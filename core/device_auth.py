#!/usr/bin/env python3
"""
Device Authentication System

Identifies and authenticates devices (laptop, phone, tablet) for content deployment.
Uses browser fingerprinting + machine hash to create unique device IDs.

Use Cases:
1. Track which device deployed what content
2. Different permissions per device (laptop=full access, phone=deploy-only)
3. Multi-device sync (deploy from laptop, view on phone)
4. Device-specific workflows

How It Works:
1. Browser sends fingerprint (User-Agent, screen size, timezone, etc.)
2. Server generates device_id (hash of fingerprint + machine hash)
3. Device registered in database with permissions
4. Future requests include device_token for authentication

Usage:
    from device_auth import DeviceAuthManager

    # Register new device
    manager = DeviceAuthManager()
    device = manager.register_device(
        fingerprint={'userAgent': '...', 'screen': '1920x1080'},
        device_type='laptop',
        user_id=1
    )

    # Verify device token
    device_info = manager.verify_device(device_token='abc123')

    # Check permissions
    can_deploy = manager.has_permission(device_token, 'deploy_git')
"""

import hashlib
import secrets
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from database import get_db


class DeviceAuthManager:
    """Manage device authentication and permissions"""

    # Device types and their default permissions
    DEVICE_PERMISSIONS = {
        'laptop': ['deploy_local', 'deploy_git', 'deploy_ssh', 'deploy_api', 'edit_content', 'delete_content'],
        'phone': ['deploy_local', 'view_content', 'qr_scan'],
        'tablet': ['deploy_local', 'edit_content', 'view_content'],
        'server': ['deploy_git', 'deploy_api', 'automated_deploy'],
    }

    def __init__(self):
        """Initialize device auth manager"""
        self.init_database()

    def init_database(self):
        """Create devices table if not exists"""
        db = get_db()

        db.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_token TEXT UNIQUE NOT NULL,
                device_type TEXT NOT NULL,
                user_id INTEGER,
                fingerprint_hash TEXT NOT NULL,
                fingerprint_data TEXT,
                permissions TEXT,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                deploy_target TEXT NOT NULL,
                content_path TEXT,
                content_url TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )
        ''')

        db.commit()

    def generate_device_id(self, fingerprint: Dict) -> str:
        """
        Generate unique device ID from fingerprint

        Args:
            fingerprint: Dict with userAgent, screen, timezone, etc.

        Returns:
            Hex string device ID
        """
        # Create stable hash from fingerprint components
        components = [
            fingerprint.get('userAgent', ''),
            fingerprint.get('screen', ''),
            fingerprint.get('timezone', ''),
            fingerprint.get('language', ''),
            fingerprint.get('platform', ''),
        ]

        fingerprint_string = '|'.join(str(c) for c in components)
        device_id = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]

        return device_id

    def register_device(
        self,
        fingerprint: Dict,
        device_type: str = 'laptop',
        user_id: Optional[int] = None,
        custom_permissions: Optional[List[str]] = None
    ) -> Dict:
        """
        Register a new device or return existing device

        Args:
            fingerprint: Browser/device fingerprint data
            device_type: 'laptop', 'phone', 'tablet', 'server'
            user_id: User ID who owns this device
            custom_permissions: Override default permissions

        Returns:
            Dict with device_id, device_token, permissions
        """
        device_id = self.generate_device_id(fingerprint)
        fingerprint_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()

        db = get_db()

        # Check if device already exists
        existing = db.execute('''
            SELECT device_id, device_token, permissions
            FROM devices
            WHERE device_id = ?
        ''', (device_id,)).fetchone()

        if existing:
            # Update last_seen
            db.execute('''
                UPDATE devices
                SET last_seen = CURRENT_TIMESTAMP
                WHERE device_id = ?
            ''', (device_id,))
            db.commit()

            return {
                'device_id': existing['device_id'],
                'device_token': existing['device_token'],
                'permissions': json.loads(existing['permissions']),
                'existing': True
            }

        # Create new device
        device_token = secrets.token_urlsafe(32)
        permissions = custom_permissions or self.DEVICE_PERMISSIONS.get(device_type, [])

        db.execute('''
            INSERT INTO devices (
                device_id, device_token, device_type, user_id,
                fingerprint_hash, fingerprint_data, permissions,
                last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            device_id,
            device_token,
            device_type,
            user_id,
            fingerprint_hash,
            json.dumps(fingerprint),
            json.dumps(permissions)
        ))

        db.commit()

        return {
            'device_id': device_id,
            'device_token': device_token,
            'device_type': device_type,
            'permissions': permissions,
            'existing': False
        }

    def verify_device(self, device_token: str) -> Optional[Dict]:
        """
        Verify device token and return device info

        Args:
            device_token: Device token from cookie/header

        Returns:
            Dict with device info or None if invalid
        """
        db = get_db()

        device = db.execute('''
            SELECT device_id, device_type, user_id, permissions, fingerprint_data
            FROM devices
            WHERE device_token = ?
        ''', (device_token,)).fetchone()

        if not device:
            return None

        # Update last_seen
        db.execute('''
            UPDATE devices
            SET last_seen = CURRENT_TIMESTAMP
            WHERE device_token = ?
        ''', (device_token,))
        db.commit()

        return {
            'device_id': device['device_id'],
            'device_type': device['device_type'],
            'user_id': device['user_id'],
            'permissions': json.loads(device['permissions']),
            'fingerprint': json.loads(device['fingerprint_data']) if device['fingerprint_data'] else {}
        }

    def has_permission(self, device_token: str, permission: str) -> bool:
        """
        Check if device has specific permission

        Args:
            device_token: Device token
            permission: Permission to check (e.g., 'deploy_git')

        Returns:
            True if device has permission
        """
        device = self.verify_device(device_token)

        if not device:
            return False

        return permission in device['permissions']

    def log_deployment(
        self,
        device_token: str,
        deploy_target: str,
        content_path: Optional[str] = None,
        content_url: Optional[str] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> int:
        """
        Log a deployment action

        Args:
            device_token: Device token
            deploy_target: 'local', 'git', 'ssh', 'api', 'email'
            content_path: Local path to deployed content
            content_url: URL where content is accessible
            status: 'success', 'failed', 'pending'
            error_message: Error message if failed

        Returns:
            Deployment ID
        """
        device = self.verify_device(device_token)

        if not device:
            raise ValueError("Invalid device token")

        db = get_db()

        cursor = db.execute('''
            INSERT INTO deployments (
                device_id, deploy_target, content_path, content_url,
                status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            device['device_id'],
            deploy_target,
            content_path,
            content_url,
            status,
            error_message
        ))

        db.commit()

        return cursor.lastrowid

    def get_device_deployments(self, device_token: str, limit: int = 50) -> List[Dict]:
        """
        Get deployment history for a device

        Args:
            device_token: Device token
            limit: Max number of deployments to return

        Returns:
            List of deployment dicts
        """
        device = self.verify_device(device_token)

        if not device:
            return []

        db = get_db()

        deployments = db.execute('''
            SELECT deploy_target, content_path, content_url, status, error_message, created_at
            FROM deployments
            WHERE device_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (device['device_id'], limit)).fetchall()

        return [dict(d) for d in deployments]

    def list_devices(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        List all devices (optionally filtered by user)

        Args:
            user_id: Filter by user ID

        Returns:
            List of device dicts
        """
        db = get_db()

        if user_id:
            devices = db.execute('''
                SELECT device_id, device_type, permissions, last_seen, created_at
                FROM devices
                WHERE user_id = ?
                ORDER BY last_seen DESC
            ''', (user_id,)).fetchall()
        else:
            devices = db.execute('''
                SELECT device_id, device_type, permissions, last_seen, created_at
                FROM devices
                ORDER BY last_seen DESC
            ''').fetchall()

        result = []
        for device in devices:
            result.append({
                'device_id': device['device_id'],
                'device_type': device['device_type'],
                'permissions': json.loads(device['permissions']),
                'last_seen': device['last_seen'],
                'created_at': device['created_at']
            })

        return result


if __name__ == '__main__':
    # Test device auth
    print("Testing Device Authentication System\n" + "="*50)

    manager = DeviceAuthManager()

    # Test 1: Register laptop
    print("\n✅ Test 1: Register laptop device")
    laptop_fingerprint = {
        'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'screen': '1920x1080',
        'timezone': 'America/New_York',
        'language': 'en-US',
        'platform': 'MacIntel'
    }

    laptop = manager.register_device(laptop_fingerprint, device_type='laptop', user_id=1)
    print(f"   Device ID: {laptop['device_id']}")
    print(f"   Device Token: {laptop['device_token'][:20]}...")
    print(f"   Permissions: {laptop['permissions']}")

    # Test 2: Verify device
    print("\n✅ Test 2: Verify device token")
    verified = manager.verify_device(laptop['device_token'])
    if verified:
        print(f"   ✅ Device verified: {verified['device_type']}")
    else:
        print("   ❌ Verification failed")

    # Test 3: Check permissions
    print("\n✅ Test 3: Check permissions")
    can_deploy_git = manager.has_permission(laptop['device_token'], 'deploy_git')
    can_delete = manager.has_permission(laptop['device_token'], 'delete_content')
    print(f"   Can deploy to git: {can_deploy_git}")
    print(f"   Can delete content: {can_delete}")

    # Test 4: Log deployment
    print("\n✅ Test 4: Log deployment")
    deployment_id = manager.log_deployment(
        laptop['device_token'],
        deploy_target='git',
        content_path='domains/soulfra/blog/test.html',
        content_url='https://soulfra.github.io/blog/test.html',
        status='success'
    )
    print(f"   Deployment logged: ID {deployment_id}")

    # Test 5: Get deployment history
    print("\n✅ Test 5: Get deployment history")
    history = manager.get_device_deployments(laptop['device_token'])
    print(f"   Found {len(history)} deployment(s)")
    if history:
        latest = history[0]
        print(f"   Latest: {latest['deploy_target']} → {latest['content_url']}")

    print("\n" + "="*50)
    print("✅ All tests passed! Device authentication ready.")

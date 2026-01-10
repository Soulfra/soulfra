#!/usr/bin/env python3
"""
Device & User Configuration - No Hardcoded Usernames!

This module manages device identity and user registration WITHOUT hardcoding
specific usernames. Works based on device ID and network registration.

The system should work like:
1. Device registers itself (MAC address, hostname, etc.)
2. User claims device via QR code / local network
3. All mentions/tags use device owner, not hardcoded names

Usage:
    from device_config import DeviceConfig

    config = DeviceConfig()
    github_user = config.get_github_user()  # Gets from device registration
    notify_user = config.get_notification_user()  # Gets registered owner
"""

import os
import socket
import uuid
import sqlite3
from pathlib import Path
from typing import Optional, Dict
import json


class DeviceConfig:
    """Manage device identity and user registration"""

    def __init__(self, db_path: str = "soulfra.db"):
        self.db_path = db_path
        self.config_file = Path(".device_config.json")
        self._ensure_device_registered()

    def _get_device_id(self) -> str:
        """Get unique device identifier"""
        # Try MAC address first
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                            for elements in range(0,2*6,2)][::-1])
            return f"device-{mac}"
        except:
            # Fallback to hostname
            return f"device-{socket.gethostname()}"

    def _get_hostname(self) -> str:
        """Get device hostname"""
        return socket.gethostname()

    def _ensure_device_registered(self):
        """Ensure device is registered in database"""
        conn = sqlite3.connect(self.db_path)

        # Create devices table if not exists
        conn.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                hostname TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                owner_github TEXT,
                owner_email TEXT,
                notification_preference TEXT DEFAULT 'local'
            )
        ''')

        device_id = self._get_device_id()
        hostname = self._get_hostname()

        # Register device if not exists
        conn.execute('''
            INSERT OR IGNORE INTO devices (id, hostname)
            VALUES (?, ?)
        ''', (device_id, hostname))

        conn.commit()
        conn.close()

    def get_github_user(self) -> Optional[str]:
        """
        Get GitHub username for this device

        Returns from:
        1. Device registration in database
        2. Local config file
        3. None (device not claimed)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        device_id = self._get_device_id()

        cursor = conn.execute('''
            SELECT owner_github FROM devices WHERE id = ?
        ''', (device_id,))

        row = cursor.fetchone()
        conn.close()

        if row and row['owner_github']:
            return row['owner_github']

        # Check local config
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('github_user')

        # Not claimed - localhost only
        return None

    def get_notification_user(self) -> Optional[str]:
        """Get user to notify (email or GitHub)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        device_id = self._get_device_id()

        cursor = conn.execute('''
            SELECT owner_email, notification_preference FROM devices WHERE id = ?
        ''', (device_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            if row['notification_preference'] == 'email' and row['owner_email']:
                return row['owner_email']

        return self.get_github_user()

    def is_localhost_only(self) -> bool:
        """Check if this device is localhost-only (not claimed)"""
        return self.get_github_user() is None

    def claim_device(self, github_user: Optional[str] = None,
                    email: Optional[str] = None,
                    notification_pref: str = 'local'):
        """
        Claim this device for a user

        Args:
            github_user: GitHub username
            email: Email address
            notification_pref: 'local', 'email', or 'github'
        """
        conn = sqlite3.connect(self.db_path)

        device_id = self._get_device_id()

        conn.execute('''
            UPDATE devices
            SET owner_github = ?,
                owner_email = ?,
                notification_preference = ?
            WHERE id = ?
        ''', (github_user, email, notification_pref, device_id))

        conn.commit()
        conn.close()

        # Also save to local config
        config = {
            'device_id': device_id,
            'github_user': github_user,
            'email': email,
            'notification_pref': notification_pref
        }

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Device {device_id} claimed")
        print(f"   GitHub: {github_user or 'None'}")
        print(f"   Email: {email or 'None'}")
        print(f"   Notifications: {notification_pref}")

    def get_device_info(self) -> Dict:
        """Get full device configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        device_id = self._get_device_id()

        cursor = conn.execute('''
            SELECT * FROM devices WHERE id = ?
        ''', (device_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)

        return {
            'id': device_id,
            'hostname': self._get_hostname(),
            'status': 'unclaimed'
        }


def main():
    """CLI for device configuration"""
    import argparse

    parser = argparse.ArgumentParser(description="Manage device configuration")
    parser.add_argument('--claim', action='store_true', help='Claim this device')
    parser.add_argument('--github', type=str, help='GitHub username')
    parser.add_argument('--email', type=str, help='Email address')
    parser.add_argument('--notify', choices=['local', 'email', 'github'], default='local',
                       help='Notification preference')
    parser.add_argument('--show', action='store_true', help='Show device info')

    args = parser.parse_args()

    config = DeviceConfig()

    if args.show:
        info = config.get_device_info()
        print("\n📱 Device Configuration")
        print(f"   ID: {info['id']}")
        print(f"   Hostname: {info.get('hostname', 'Unknown')}")
        print(f"   GitHub: {info.get('owner_github', 'None')}")
        print(f"   Email: {info.get('owner_email', 'None')}")
        print(f"   Notifications: {info.get('notification_preference', 'local')}")
        print(f"   Localhost Only: {config.is_localhost_only()}")

    elif args.claim:
        config.claim_device(
            github_user=args.github,
            email=args.email,
            notification_pref=args.notify
        )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

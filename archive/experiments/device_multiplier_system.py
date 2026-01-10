#!/usr/bin/env python3
"""
Device ID + Multiplier System - Pair domains with devices for rewards

This is the missing link you described:
"pair their domain with device id or something else where we can tie multipliers
and all other random things together"

Flow:
1. User scans QR code with device
2. System detects device fingerprint (IP + user agent + browser data)
3. Device gets paired with domain
4. Multiplier applied to all rewards (soul tokens, territory points, etc.)
5. Multipliers can increase with loyalty/activity

Example:
- New device scans ocean-dreams QR → 1.0x multiplier
- After 10 scans → 1.5x multiplier
- After 30 days paired → 2.0x multiplier
- Premium user → 3.0x multiplier

Architecture:
-----------
device_multipliers table
    ├── device_id (fingerprint hash)
    ├── domain_slug (ocean-dreams, calriven, etc.)
    ├── brand_id (optional - for brand-specific multipliers)
    ├── base_multiplier (1.0)
    ├── loyalty_bonus (0.0 - 2.0)
    ├── tier_bonus (0.0 - 5.0)
    └── total_multiplier (base + loyalty + tier)

device_activity table
    ├── device_id
    ├── last_seen
    ├── scan_count
    ├── first_paired_at
    └── days_active

Usage:
    from device_multiplier_system import (
        pair_device_with_domain,
        get_device_multiplier,
        track_device_activity,
        calculate_rewards
    )

    # When QR scanned
    device_id = get_device_fingerprint(request)
    pair_device_with_domain(device_id, 'ocean-dreams')

    # Get multiplier
    multiplier = get_device_multiplier(device_id, 'ocean-dreams')

    # Award tokens with multiplier
    base_tokens = 10
    actual_tokens = calculate_rewards(base_tokens, multiplier)
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def create_device_multiplier_tables():
    """
    Create tables for device tracking and multipliers

    Call this once to set up the schema
    """
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Device multipliers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_multipliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            domain_slug TEXT,
            brand_id INTEGER,
            base_multiplier REAL DEFAULT 1.0,
            loyalty_bonus REAL DEFAULT 0.0,
            tier_bonus REAL DEFAULT 0.0,
            total_multiplier REAL GENERATED ALWAYS AS (
                base_multiplier + loyalty_bonus + tier_bonus
            ) STORED,
            paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_id, domain_slug, brand_id),
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')

    # Device activity tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL UNIQUE,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scan_count INTEGER DEFAULT 0,
            days_active INTEGER DEFAULT 0,
            total_rewards_earned REAL DEFAULT 0.0,
            metadata TEXT
        )
    ''')

    # Device scans log (detailed tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            domain_slug TEXT,
            brand_id INTEGER,
            qr_code_id INTEGER,
            scan_location TEXT,
            ip_address TEXT,
            user_agent TEXT,
            rewards_earned REAL DEFAULT 0.0,
            multiplier_applied REAL DEFAULT 1.0,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Device multiplier tables created!")


# ==============================================================================
# DEVICE FINGERPRINTING
# ==============================================================================

def get_device_fingerprint(request_data: Dict) -> str:
    """
    Generate unique device fingerprint from request data

    Args:
        request_data: Dict with ip_address, user_agent, etc.

    Returns:
        SHA256 hash of device fingerprint

    Components:
    - IP address (can change, but usually stable)
    - User agent (browser, OS, device)
    - Accept-Language header
    - Screen resolution (from client JS)
    - Timezone (from client JS)
    """
    fingerprint_parts = [
        request_data.get('ip_address', 'unknown'),
        request_data.get('user_agent', 'unknown'),
        request_data.get('accept_language', 'en-US'),
        request_data.get('screen_resolution', '1920x1080'),
        request_data.get('timezone', 'UTC'),
    ]

    fingerprint_string = '|'.join(fingerprint_parts)
    device_id = hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()[:32]

    return device_id


# ==============================================================================
# PAIRING & MULTIPLIERS
# ==============================================================================

def pair_device_with_domain(
    device_id: str,
    domain_slug: str,
    brand_id: Optional[int] = None,
    initial_multiplier: float = 1.0
) -> Dict:
    """
    Pair a device with a domain (and optionally a brand)

    Args:
        device_id: Device fingerprint hash
        domain_slug: Domain (ocean-dreams, calriven, etc.)
        brand_id: Optional brand ID
        initial_multiplier: Starting multiplier (default: 1.0)

    Returns:
        Dict with pairing info
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if already paired
    cursor.execute('''
        SELECT * FROM device_multipliers
        WHERE device_id = ? AND domain_slug = ? AND brand_id IS ?
    ''', (device_id, domain_slug, brand_id))

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            'paired': True,
            'existing': True,
            'multiplier': existing['total_multiplier'],
            'paired_at': existing['paired_at']
        }

    # Create new pairing
    cursor.execute('''
        INSERT INTO device_multipliers (
            device_id, domain_slug, brand_id, base_multiplier
        ) VALUES (?, ?, ?, ?)
    ''', (device_id, domain_slug, brand_id, initial_multiplier))

    # Track device activity
    cursor.execute('''
        INSERT INTO device_activity (device_id)
        VALUES (?)
        ON CONFLICT(device_id) DO UPDATE SET
            last_seen = CURRENT_TIMESTAMP
    ''', (device_id,))

    conn.commit()
    conn.close()

    print(f"✅ Paired device {device_id[:8]}... with {domain_slug}")

    return {
        'paired': True,
        'existing': False,
        'multiplier': initial_multiplier,
        'paired_at': datetime.now().isoformat()
    }


def get_device_multiplier(
    device_id: str,
    domain_slug: str = None,
    brand_id: int = None
) -> float:
    """
    Get current multiplier for a device

    Args:
        device_id: Device fingerprint
        domain_slug: Optional domain filter
        brand_id: Optional brand filter

    Returns:
        Multiplier value (default: 1.0)
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if domain_slug and brand_id:
        # Specific domain + brand
        cursor.execute('''
            SELECT total_multiplier FROM device_multipliers
            WHERE device_id = ? AND domain_slug = ? AND brand_id = ?
        ''', (device_id, domain_slug, brand_id))
    elif domain_slug:
        # Domain-wide multiplier
        cursor.execute('''
            SELECT AVG(total_multiplier) as avg_multiplier
            FROM device_multipliers
            WHERE device_id = ? AND domain_slug = ?
        ''', (device_id, domain_slug))
    else:
        # Global device multiplier (across all domains)
        cursor.execute('''
            SELECT AVG(total_multiplier) as avg_multiplier
            FROM device_multipliers
            WHERE device_id = ?
        ''', (device_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return float(result[0] or result['avg_multiplier'] or 1.0)
    else:
        return 1.0


def update_loyalty_bonus(device_id: str, domain_slug: str):
    """
    Update loyalty bonus based on device activity

    Loyalty tiers:
    - 0-10 scans: 0.0x
    - 11-25 scans: +0.5x
    - 26-50 scans: +1.0x
    - 51-100 scans: +1.5x
    - 100+ scans: +2.0x

    Days active bonus:
    - 0-7 days: 0.0x
    - 8-30 days: +0.25x
    - 31-90 days: +0.5x
    - 90+ days: +1.0x
    """
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get device activity
    cursor.execute('''
        SELECT scan_count, days_active
        FROM device_activity
        WHERE device_id = ?
    ''', (device_id,))

    activity = cursor.fetchone()

    if not activity:
        conn.close()
        return

    scan_count, days_active = activity

    # Calculate scan bonus
    if scan_count >= 100:
        scan_bonus = 2.0
    elif scan_count >= 51:
        scan_bonus = 1.5
    elif scan_count >= 26:
        scan_bonus = 1.0
    elif scan_count >= 11:
        scan_bonus = 0.5
    else:
        scan_bonus = 0.0

    # Calculate days bonus
    if days_active >= 90:
        days_bonus = 1.0
    elif days_active >= 31:
        days_bonus = 0.5
    elif days_active >= 8:
        days_bonus = 0.25
    else:
        days_bonus = 0.0

    total_loyalty_bonus = scan_bonus + days_bonus

    # Update multiplier
    cursor.execute('''
        UPDATE device_multipliers
        SET loyalty_bonus = ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE device_id = ? AND domain_slug = ?
    ''', (total_loyalty_bonus, device_id, domain_slug))

    conn.commit()
    conn.close()

    print(f"✅ Updated loyalty bonus for {device_id[:8]}... → {total_loyalty_bonus}x")


# ==============================================================================
# TRACKING & REWARDS
# ==============================================================================

def track_device_scan(
    device_id: str,
    domain_slug: str = None,
    brand_id: int = None,
    qr_code_id: int = None,
    request_data: Dict = None
):
    """
    Track a device scan and update activity

    Args:
        device_id: Device fingerprint
        domain_slug: Domain scanned
        brand_id: Brand associated with scan
        qr_code_id: QR code ID from qr_faucets table
        request_data: Request metadata (IP, user agent, etc.)
    """
    if request_data is None:
        request_data = {}

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get current multiplier
    multiplier = get_device_multiplier(device_id, domain_slug, brand_id)

    # Calculate rewards (example: base 10 tokens * multiplier)
    base_rewards = 10.0
    actual_rewards = base_rewards * multiplier

    # Log scan
    cursor.execute('''
        INSERT INTO device_scans (
            device_id, domain_slug, brand_id, qr_code_id,
            ip_address, user_agent,
            rewards_earned, multiplier_applied
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        device_id,
        domain_slug,
        brand_id,
        qr_code_id,
        request_data.get('ip_address'),
        request_data.get('user_agent'),
        actual_rewards,
        multiplier
    ))

    # Update device activity
    cursor.execute('''
        UPDATE device_activity
        SET last_seen = CURRENT_TIMESTAMP,
            scan_count = scan_count + 1,
            total_rewards_earned = total_rewards_earned + ?
        WHERE device_id = ?
    ''', (actual_rewards, device_id))

    # Calculate days active
    cursor.execute('''
        UPDATE device_activity
        SET days_active = CAST(
            (julianday(CURRENT_TIMESTAMP) - julianday(first_seen)) AS INTEGER
        )
        WHERE device_id = ?
    ''', (device_id,))

    conn.commit()
    conn.close()

    # Update loyalty bonus based on new activity
    if domain_slug:
        update_loyalty_bonus(device_id, domain_slug)

    return {
        'rewards_earned': actual_rewards,
        'multiplier': multiplier,
        'base_rewards': base_rewards
    }


def calculate_rewards(base_amount: float, multiplier: float) -> float:
    """
    Calculate final rewards with multiplier

    Args:
        base_amount: Base reward amount
        multiplier: Multiplier to apply

    Returns:
        Final reward amount
    """
    return base_amount * multiplier


# ==============================================================================
# ADMIN / STATS
# ==============================================================================

def get_device_stats(device_id: str) -> Dict:
    """Get comprehensive stats for a device"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Activity
    cursor.execute('''
        SELECT * FROM device_activity WHERE device_id = ?
    ''', (device_id,))
    activity = cursor.fetchone()

    # Multipliers
    cursor.execute('''
        SELECT * FROM device_multipliers WHERE device_id = ?
    ''', (device_id,))
    multipliers = [dict(m) for m in cursor.fetchall()]

    # Recent scans
    cursor.execute('''
        SELECT * FROM device_scans
        WHERE device_id = ?
        ORDER BY scanned_at DESC
        LIMIT 10
    ''', (device_id,))
    recent_scans = [dict(s) for s in cursor.fetchall()]

    conn.close()

    return {
        'device_id': device_id,
        'activity': dict(activity) if activity else None,
        'multipliers': multipliers,
        'recent_scans': recent_scans
    }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Device Multiplier System')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--pair', nargs=2, metavar=('DEVICE_ID', 'DOMAIN'), help='Pair device with domain')
    parser.add_argument('--stats', metavar='DEVICE_ID', help='Get device stats')
    parser.add_argument('--scan', nargs=2, metavar=('DEVICE_ID', 'DOMAIN'), help='Simulate scan')

    args = parser.parse_args()

    if args.init:
        print("Initializing device multiplier system...")
        create_device_multiplier_tables()

    elif args.pair:
        device_id, domain = args.pair
        result = pair_device_with_domain(device_id, domain)
        print(json.dumps(result, indent=2))

    elif args.stats:
        stats = get_device_stats(args.stats)
        print(json.dumps(stats, indent=2, default=str))

    elif args.scan:
        device_id, domain = args.scan
        result = track_device_scan(
            device_id,
            domain_slug=domain,
            request_data={'ip_address': '127.0.0.1', 'user_agent': 'CLI Test'}
        )
        print(json.dumps(result, indent=2))

    else:
        print("Device ID + Multiplier System")
        print()
        print("Usage:")
        print("  --init                        Initialize database")
        print("  --pair DEVICE_ID DOMAIN       Pair device with domain")
        print("  --scan DEVICE_ID DOMAIN       Simulate scan")
        print("  --stats DEVICE_ID             Get device stats")
        print()
        print("Examples:")
        print("  python3 device_multiplier_system.py --init")
        print("  python3 device_multiplier_system.py --pair abc123 ocean-dreams")
        print("  python3 device_multiplier_system.py --scan abc123 ocean-dreams")

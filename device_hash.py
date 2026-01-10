#!/usr/bin/env python3
"""
Device Fingerprinting & Hashing System

Identifies which device (iPhone, Mac, Windows PC, etc.) a voice recording came from
by hashing User-Agent + IP + Device ID.

Features:
- Device fingerprint generation
- Device tracking across recordings
- Device name detection (iPhone 12, MacBook Pro, etc.)
- Database table creation and migration

Usage:
    from device_hash import capture_device_info, get_device_name

    # In Flask route:
    device_info = capture_device_info(request)
    recording_id = save_recording(...)
    link_device_to_recording(recording_id, device_info)
"""

import hashlib
import re
from datetime import datetime, timezone
from database import get_db


def create_device_tables():
    """
    Create device fingerprinting tables if they don't exist

    Tables:
    - device_fingerprints: Stores unique devices
    - recording_devices: Links recordings to devices
    """
    db = get_db()

    # Table 1: Device fingerprints
    db.execute('''
        CREATE TABLE IF NOT EXISTS device_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_hash TEXT UNIQUE NOT NULL,
            device_name TEXT,
            device_type TEXT,
            user_agent TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            recording_count INTEGER DEFAULT 0
        )
    ''')

    # Table 2: Recording-Device link
    db.execute('''
        CREATE TABLE IF NOT EXISTS recording_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            device_id INTEGER NOT NULL,
            ip_address TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
            FOREIGN KEY (device_id) REFERENCES device_fingerprints(id)
        )
    ''')

    db.commit()
    print("✅ Device fingerprinting tables created")


def generate_device_hash(user_agent, ip_address, device_id=None):
    """
    Generate a unique device fingerprint hash

    Args:
        user_agent (str): User-Agent header from request
        ip_address (str): IP address from request
        device_id (str, optional): Additional device identifier (if available)

    Returns:
        str: 64-character SHA256 hash

    Example:
        >>> generate_device_hash("Mozilla/5.0 (iPhone; CPU iPhone OS 15_0...", "192.168.1.100")
        'a3f5b8c2d1e0f9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3'
    """
    # Normalize inputs
    ua_normalized = (user_agent or "unknown").strip().lower()
    ip_normalized = (ip_address or "0.0.0.0").strip()
    device_normalized = (device_id or "").strip().lower()

    # Create composite string
    composite = f"{ua_normalized}|{ip_normalized}|{device_normalized}"

    # Hash it
    return hashlib.sha256(composite.encode('utf-8')).hexdigest()


def detect_device_type(user_agent):
    """
    Detect device type from User-Agent string

    Args:
        user_agent (str): User-Agent header

    Returns:
        str: Device type (iPhone, iPad, Mac, Windows, Linux, Android, Unknown)

    Example:
        >>> detect_device_type("Mozilla/5.0 (iPhone; CPU iPhone OS 15_0...")
        'iPhone'
    """
    if not user_agent:
        return "Unknown"

    ua = user_agent.lower()

    # Mobile devices
    if "iphone" in ua:
        return "iPhone"
    elif "ipad" in ua:
        return "iPad"
    elif "android" in ua and "mobile" in ua:
        return "Android Phone"
    elif "android" in ua:
        return "Android Tablet"

    # Desktop/Laptop
    elif "macintosh" in ua or "mac os x" in ua:
        return "Mac"
    elif "windows" in ua:
        return "Windows"
    elif "linux" in ua:
        return "Linux"
    elif "cros" in ua:
        return "Chromebook"

    # Fallback
    return "Unknown"


def extract_device_name(user_agent):
    """
    Extract specific device name from User-Agent

    Args:
        user_agent (str): User-Agent header

    Returns:
        str: Friendly device name (e.g., "iPhone 12", "MacBook Pro", "Windows PC")

    Example:
        >>> extract_device_name("Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)")
        'iPhone (iOS 15.0)'
    """
    if not user_agent:
        return "Unknown Device"

    device_type = detect_device_type(user_agent)
    ua = user_agent

    # iPhone detection
    if device_type == "iPhone":
        # Extract iOS version
        ios_match = re.search(r'CPU iPhone OS (\d+)_(\d+)', ua)
        if ios_match:
            major, minor = ios_match.groups()
            return f"iPhone (iOS {major}.{minor})"
        return "iPhone"

    # iPad detection
    elif device_type == "iPad":
        ios_match = re.search(r'CPU OS (\d+)_(\d+)', ua)
        if ios_match:
            major, minor = ios_match.groups()
            return f"iPad (iOS {major}.{minor})"
        return "iPad"

    # Mac detection
    elif device_type == "Mac":
        mac_match = re.search(r'Mac OS X (\d+)[_.](\d+)', ua)
        if mac_match:
            major, minor = mac_match.groups()
            return f"Mac (macOS {major}.{minor})"
        return "Mac"

    # Windows detection
    elif device_type == "Windows":
        # Try to get Windows version
        if "Windows NT 10.0" in ua:
            return "Windows 10/11 PC"
        elif "Windows NT 6.3" in ua:
            return "Windows 8.1 PC"
        elif "Windows NT 6.2" in ua:
            return "Windows 8 PC"
        elif "Windows NT 6.1" in ua:
            return "Windows 7 PC"
        return "Windows PC"

    # Android detection
    elif "Android" in device_type:
        android_match = re.search(r'Android (\d+(?:\.\d+)?)', ua)
        if android_match:
            version = android_match.group(1)
            return f"{device_type} (Android {version})"
        return device_type

    return device_type


def capture_device_info(request):
    """
    Capture device information from Flask request

    Args:
        request: Flask request object

    Returns:
        dict: Device information
            {
                'device_hash': '...',
                'user_agent': '...',
                'ip_address': '...',
                'device_type': '...',
                'device_name': '...'
            }

    Usage:
        @app.route('/upload')
        def upload():
            device_info = capture_device_info(request)
            # ... save recording ...
            link_device_to_recording(recording_id, device_info)
    """
    user_agent = request.headers.get('User-Agent', '')

    # Get real IP (handle proxies/load balancers)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    # Optional: Extract device ID from custom headers (if client sends it)
    device_id = request.headers.get('X-Device-ID', None)

    device_hash = generate_device_hash(user_agent, ip_address, device_id)
    device_type = detect_device_type(user_agent)
    device_name = extract_device_name(user_agent)

    return {
        'device_hash': device_hash,
        'user_agent': user_agent,
        'ip_address': ip_address,
        'device_type': device_type,
        'device_name': device_name,
        'device_id': device_id
    }


def get_or_create_device(device_info):
    """
    Get existing device or create new one

    Args:
        device_info (dict): Output from capture_device_info()

    Returns:
        int: device_id from device_fingerprints table
    """
    db = get_db()

    # Check if device already exists
    device = db.execute(
        'SELECT id FROM device_fingerprints WHERE device_hash = ?',
        (device_info['device_hash'],)
    ).fetchone()

    now = datetime.now(timezone.utc).isoformat()

    if device:
        # Update last_seen and increment count
        db.execute('''
            UPDATE device_fingerprints
            SET last_seen = ?, recording_count = recording_count + 1
            WHERE id = ?
        ''', (now, device['id']))
        db.commit()
        return device['id']
    else:
        # Create new device
        cursor = db.execute('''
            INSERT INTO device_fingerprints
            (device_hash, device_name, device_type, user_agent, first_seen, last_seen, recording_count)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (
            device_info['device_hash'],
            device_info['device_name'],
            device_info['device_type'],
            device_info['user_agent'],
            now,
            now
        ))
        db.commit()
        return cursor.lastrowid


def link_device_to_recording(recording_id, device_info):
    """
    Link a device to a voice recording

    Args:
        recording_id (int): ID from simple_voice_recordings table
        device_info (dict): Output from capture_device_info()

    Returns:
        int: ID from recording_devices table
    """
    db = get_db()

    # Get or create device
    device_id = get_or_create_device(device_info)

    # Create link
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.execute('''
        INSERT INTO recording_devices (recording_id, device_id, ip_address, created_at)
        VALUES (?, ?, ?, ?)
    ''', (recording_id, device_id, device_info['ip_address'], now))
    db.commit()

    return cursor.lastrowid


def get_recording_device(recording_id):
    """
    Get device information for a recording

    Args:
        recording_id (int): Recording ID

    Returns:
        dict: Device info or None
            {
                'device_name': 'iPhone (iOS 15.0)',
                'device_type': 'iPhone',
                'user_agent': '...',
                'ip_address': '...',
                'first_seen': '...',
                'recording_count': 5
            }
    """
    db = get_db()

    result = db.execute('''
        SELECT
            df.device_name,
            df.device_type,
            df.user_agent,
            rd.ip_address,
            df.first_seen,
            df.recording_count
        FROM recording_devices rd
        JOIN device_fingerprints df ON rd.device_id = df.id
        WHERE rd.recording_id = ?
    ''', (recording_id,)).fetchone()

    if not result:
        return None

    return dict(result)


def get_user_devices(user_id):
    """
    Get all devices used by a user

    Args:
        user_id (int): User ID

    Returns:
        list: List of device dicts
    """
    db = get_db()

    devices = db.execute('''
        SELECT DISTINCT
            df.id,
            df.device_name,
            df.device_type,
            df.first_seen,
            df.last_seen,
            df.recording_count
        FROM device_fingerprints df
        JOIN recording_devices rd ON df.id = rd.device_id
        JOIN simple_voice_recordings svr ON rd.recording_id = svr.id
        WHERE svr.user_id = ?
        ORDER BY df.last_seen DESC
    ''', (user_id,)).fetchall()

    return [dict(d) for d in devices]


def get_device_stats():
    """
    Get overall device statistics

    Returns:
        dict: Stats
            {
                'total_devices': 10,
                'device_types': {'iPhone': 5, 'Mac': 3, 'Windows': 2},
                'most_active_device': {...}
            }
    """
    db = get_db()

    total = db.execute('SELECT COUNT(*) as count FROM device_fingerprints').fetchone()['count']

    # Count by type
    types = db.execute('''
        SELECT device_type, COUNT(*) as count
        FROM device_fingerprints
        GROUP BY device_type
        ORDER BY count DESC
    ''').fetchall()

    device_types = {row['device_type']: row['count'] for row in types}

    # Most active device
    most_active = db.execute('''
        SELECT * FROM device_fingerprints
        ORDER BY recording_count DESC
        LIMIT 1
    ''').fetchone()

    return {
        'total_devices': total,
        'device_types': device_types,
        'most_active_device': dict(most_active) if most_active else None
    }


if __name__ == '__main__':
    """
    CLI for testing device fingerprinting
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 device_hash.py init              # Create tables")
        print("  python3 device_hash.py test <user-agent> # Test detection")
        print("  python3 device_hash.py stats             # Show statistics")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        create_device_tables()
        print("✅ Device tables initialized")

    elif command == "test":
        if len(sys.argv) < 3:
            print("Error: Provide User-Agent string")
            sys.exit(1)

        user_agent = sys.argv[2]
        device_type = detect_device_type(user_agent)
        device_name = extract_device_name(user_agent)
        device_hash = generate_device_hash(user_agent, "127.0.0.1")

        print(f"User-Agent: {user_agent}")
        print(f"Device Type: {device_type}")
        print(f"Device Name: {device_name}")
        print(f"Device Hash: {device_hash}")

    elif command == "stats":
        stats = get_device_stats()
        print(f"Total Devices: {stats['total_devices']}")
        print(f"\nDevice Types:")
        for dtype, count in stats['device_types'].items():
            print(f"  {dtype}: {count}")

        if stats['most_active_device']:
            most = stats['most_active_device']
            print(f"\nMost Active Device:")
            print(f"  Name: {most['device_name']}")
            print(f"  Type: {most['device_type']}")
            print(f"  Recordings: {most['recording_count']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

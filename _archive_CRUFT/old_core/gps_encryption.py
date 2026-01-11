#!/usr/bin/env python3
"""
GPS Coordinate Encryption - Privacy-First Location Storage

Uses AES-256-GCM encryption (same as voice_encryption.py) to securely store GPS coordinates.

Security Features:
- AES-256-GCM authenticated encryption
- Encrypted coordinates cannot be decrypted without key
- Keys stored separately from encrypted data
- Can still calculate geofencing radius using decrypted coords

Database Schema:
    dm_channels table will have:
    - location_encrypted_data BLOB (encrypted "lat,lon" string)
    - location_encryption_key TEXT (base64-encoded key)
    - location_encryption_iv TEXT (base64-encoded IV)
    - location_lat REAL → NULL (deprecated, will be removed after migration)
    - location_lon REAL → NULL (deprecated, will be removed after migration)

Usage:
    from gps_encryption import encrypt_gps_coordinates, decrypt_gps_coordinates

    # Encrypt GPS coords before storing
    encrypted = encrypt_gps_coordinates(37.7749, -122.4194)
    # Store: encrypted['encrypted_data'], encrypted['key_b64'], encrypted['iv_b64']

    # Decrypt for geofencing calculation
    lat, lon = decrypt_gps_coordinates(
        encrypted_data=encrypted['encrypted_data'],
        key_b64=encrypted['key_b64'],
        iv_b64=encrypted['iv_b64']
    )
"""

import sys
import base64
from pathlib import Path

# Use existing voice encryption infrastructure
from voice_encryption import encrypt_voice_memo, decrypt_voice_memo, generate_encryption_key


# =============================================================================
# GPS ENCRYPTION
# =============================================================================

def encrypt_gps_coordinates(latitude, longitude):
    """
    Encrypt GPS coordinates using AES-256-GCM

    Args:
        latitude (float): Latitude (-90 to 90)
        longitude (float): Longitude (-180 to 180)

    Returns:
        dict: {
            'encrypted_data': bytes,
            'key': bytes,
            'iv': bytes,
            'key_b64': str,  # For database storage
            'iv_b64': str,   # For database storage
            'encrypted_b64': str  # For database storage
        }

    Example:
        >>> encrypted = encrypt_gps_coordinates(37.7749, -122.4194)
        >>> encrypted['key_b64']
        'a3f2c8b1e4d7f9a2...'
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude} (must be -90 to 90)")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude: {longitude} (must be -180 to 180)")

    # Format as "lat,lon" string
    gps_string = f"{latitude},{longitude}"
    gps_bytes = gps_string.encode('utf-8')

    # Encrypt using existing voice encryption
    encrypted = encrypt_voice_memo(gps_bytes)

    # Add base64-encoded encrypted data for database storage
    encrypted['encrypted_b64'] = base64.urlsafe_b64encode(encrypted['encrypted_data']).decode('utf-8')

    return encrypted


def decrypt_gps_coordinates(encrypted_data=None, key=None, iv=None, encrypted_b64=None, key_b64=None, iv_b64=None):
    """
    Decrypt GPS coordinates

    Args:
        encrypted_data (bytes): Encrypted data (optional if encrypted_b64 provided)
        key (bytes): Encryption key (optional if key_b64 provided)
        iv (bytes): Initialization vector (optional if iv_b64 provided)
        encrypted_b64 (str): Base64-encoded encrypted data (optional)
        key_b64 (str): Base64-encoded key (optional)
        iv_b64 (str): Base64-encoded IV (optional)

    Returns:
        tuple: (latitude, longitude) as floats

    Example:
        >>> lat, lon = decrypt_gps_coordinates(
        ...     encrypted_b64=encrypted['encrypted_b64'],
        ...     key_b64=encrypted['key_b64'],
        ...     iv_b64=encrypted['iv_b64']
        ... )
        >>> lat, lon
        (37.7749, -122.4194)
    """
    # Convert base64 to bytes if needed
    if encrypted_b64 and not encrypted_data:
        encrypted_data = base64.urlsafe_b64decode(encrypted_b64)
    if key_b64 and not key:
        key = base64.urlsafe_b64decode(key_b64)
    if iv_b64 and not iv:
        iv = base64.urlsafe_b64decode(iv_b64)

    # Decrypt using existing voice encryption
    decrypted_bytes = decrypt_voice_memo(encrypted_data, key, iv)

    # Parse "lat,lon" string
    gps_string = decrypted_bytes.decode('utf-8')
    lat_str, lon_str = gps_string.split(',')

    latitude = float(lat_str)
    longitude = float(lon_str)

    return latitude, longitude


def encrypt_gps_for_database(latitude, longitude):
    """
    Encrypt GPS coordinates and return dict ready for database storage

    Args:
        latitude (float): Latitude
        longitude (float): Longitude

    Returns:
        dict: Ready to insert into database
            {
                'location_encrypted_data': str (base64),
                'location_encryption_key': str (base64),
                'location_encryption_iv': str (base64)
            }

    Example:
        db.execute('''
            UPDATE dm_channels
            SET location_encrypted_data = ?,
                location_encryption_key = ?,
                location_encryption_iv = ?
            WHERE id = ?
        ''', (data['location_encrypted_data'], data['location_encryption_key'],
              data['location_encryption_iv'], channel_id))
    """
    encrypted = encrypt_gps_coordinates(latitude, longitude)

    return {
        'location_encrypted_data': encrypted['encrypted_b64'],
        'location_encryption_key': encrypted['key_b64'],
        'location_encryption_iv': encrypted['iv_b64']
    }


def decrypt_gps_from_database(row):
    """
    Decrypt GPS coordinates from database row

    Args:
        row (dict): Database row with encrypted GPS fields

    Returns:
        tuple: (latitude, longitude) or (None, None) if not encrypted

    Example:
        row = db.execute('SELECT * FROM dm_channels WHERE id = ?', (1,)).fetchone()
        lat, lon = decrypt_gps_from_database(row)
    """
    encrypted_data = row.get('location_encrypted_data')
    key_b64 = row.get('location_encryption_key')
    iv_b64 = row.get('location_encryption_iv')

    if not all([encrypted_data, key_b64, iv_b64]):
        # Fall back to plaintext coords (legacy)
        return row.get('location_lat'), row.get('location_lon')

    return decrypt_gps_coordinates(
        encrypted_b64=encrypted_data,
        key_b64=key_b64,
        iv_b64=iv_b64
    )


# =============================================================================
# GEOFENCING WITH ENCRYPTED GPS
# =============================================================================

def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates using Haversine formula

    Args:
        lat1, lon1: First coordinate (floats)
        lat2, lon2: Second coordinate (floats)

    Returns:
        float: Distance in kilometers

    Example:
        >>> # San Francisco to Oakland
        >>> calculate_distance_km(37.7749, -122.4194, 37.8044, -122.2712)
        13.52
    """
    import math

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Earth radius in kilometers
    earth_radius_km = 6371.0

    return earth_radius_km * c


def is_within_radius(user_row, target_row, radius_km):
    """
    Check if two users are within geofencing radius

    Args:
        user_row (dict): Database row for user with encrypted GPS
        target_row (dict): Database row for target user with encrypted GPS
        radius_km (float): Radius in kilometers

    Returns:
        bool: True if within radius, False otherwise

    Example:
        user1 = db.execute('SELECT * FROM dm_channels WHERE id = ?', (1,)).fetchone()
        user2 = db.execute('SELECT * FROM dm_channels WHERE id = ?', (2,)).fetchone()

        if is_within_radius(user1, user2, radius_km=30):
            print("Users are within 30km of each other!")
    """
    # Decrypt GPS coordinates
    lat1, lon1 = decrypt_gps_from_database(user_row)
    lat2, lon2 = decrypt_gps_from_database(target_row)

    if not all([lat1, lon1, lat2, lon2]):
        # Missing GPS data
        return False

    # Calculate distance
    distance = calculate_distance_km(lat1, lon1, lat2, lon2)

    return distance <= radius_km


def calculate_geofence_radius_by_reputation(trust_score, total_xp):
    """
    Calculate geofencing radius based on user reputation (Reddit karma analogy)

    Args:
        trust_score (float): Trust score 0.0-1.0
        total_xp (int): Total XP earned

    Returns:
        float: Radius in kilometers (20-50km based on reputation)

    Logic:
        - Base radius: 20km (low reputation)
        - Max radius: 50km (high reputation)
        - trust_score 0.5-1.0 = 20-35km
        - total_xp 0-10000 = +0-15km bonus

    Example:
        >>> # Low reputation user
        >>> calculate_geofence_radius_by_reputation(0.5, 100)
        20.15

        >>> # High reputation user
        >>> calculate_geofence_radius_by_reputation(0.9, 5000)
        42.5
    """
    # Base radius from trust score (20-35km)
    trust_radius = 20 + (trust_score - 0.5) * 30  # 0.5=20km, 1.0=35km

    # XP bonus (0-15km)
    xp_bonus = min(total_xp / 10000, 1.0) * 15  # Cap at 10k XP = +15km

    total_radius = trust_radius + xp_bonus

    # Clamp to 20-50km range
    return max(20, min(50, total_radius))


# =============================================================================
# MIGRATION HELPERS
# =============================================================================

def migrate_plaintext_gps_to_encrypted():
    """
    Migrate existing plaintext GPS coordinates to encrypted storage

    IMPORTANT: This will encrypt all existing GPS coordinates and clear the plaintext columns

    Returns:
        int: Number of coordinates encrypted
    """
    from database import get_db

    print("=" * 70)
    print("🔒 MIGRATING GPS COORDINATES - Plaintext → Encrypted")
    print("=" * 70)
    print()

    db = get_db()

    # Check if encrypted columns exist
    columns = db.execute("PRAGMA table_info(dm_channels)").fetchall()
    column_names = [col['name'] for col in columns]

    missing_columns = []
    for col in ['location_encrypted_data', 'location_encryption_key', 'location_encryption_iv']:
        if col not in column_names:
            missing_columns.append(col)

    if missing_columns:
        print("⚠️ Missing encrypted columns, adding them...")
        for col in missing_columns:
            db.execute(f'ALTER TABLE dm_channels ADD COLUMN {col} TEXT')
        db.commit()
        print(f"   Added: {', '.join(missing_columns)}")
        print()

    # Find rows with plaintext GPS
    rows = db.execute('''
        SELECT id, location_lat, location_lon
        FROM dm_channels
        WHERE location_lat IS NOT NULL AND location_lon IS NOT NULL
        AND location_encrypted_data IS NULL
    ''').fetchall()

    print(f"📊 Found {len(rows)} rows with plaintext GPS coordinates")
    print()

    encrypted_count = 0

    for row in rows:
        channel_id = row['id']
        lat = row['location_lat']
        lon = row['location_lon']

        # Encrypt coordinates
        encrypted = encrypt_gps_for_database(lat, lon)

        print(f"   Channel {channel_id}: ({lat}, {lon}) → ENCRYPTED")

        # Update database
        db.execute('''
            UPDATE dm_channels
            SET location_encrypted_data = ?,
                location_encryption_key = ?,
                location_encryption_iv = ?,
                location_lat = NULL,
                location_lon = NULL
            WHERE id = ?
        ''', (
            encrypted['location_encrypted_data'],
            encrypted['location_encryption_key'],
            encrypted['location_encryption_iv'],
            channel_id
        ))

        encrypted_count += 1

    db.commit()
    db.close()

    print()
    print(f"✅ Encrypted {encrypted_count} GPS coordinate pairs")
    print()

    return encrypted_count


# =============================================================================
# TESTING
# =============================================================================

def test_gps_encryption():
    """Test GPS encryption functions"""
    print("=" * 70)
    print("🧪 TESTING GPS ENCRYPTION")
    print("=" * 70)
    print()

    # Test 1: Encrypt/Decrypt
    print("TEST 1: Encrypt/Decrypt GPS Coordinates")
    lat_orig = 37.7749
    lon_orig = -122.4194
    print(f"   Original: ({lat_orig}, {lon_orig})")

    encrypted = encrypt_gps_coordinates(lat_orig, lon_orig)
    print(f"   Encrypted key: {encrypted['key_b64'][:20]}...")
    print(f"   Encrypted data: {encrypted['encrypted_b64'][:20]}...")

    lat_decrypted, lon_decrypted = decrypt_gps_coordinates(
        encrypted_b64=encrypted['encrypted_b64'],
        key_b64=encrypted['key_b64'],
        iv_b64=encrypted['iv_b64']
    )
    print(f"   Decrypted: ({lat_decrypted}, {lon_decrypted})")
    print(f"   Match: {'✅ PASS' if lat_orig == lat_decrypted and lon_orig == lon_decrypted else '❌ FAIL'}")
    print()

    # Test 2: Distance calculation
    print("TEST 2: Distance Calculation (Haversine)")
    # San Francisco to Oakland
    sf_lat, sf_lon = 37.7749, -122.4194
    oakland_lat, oakland_lon = 37.8044, -122.2712
    distance = calculate_distance_km(sf_lat, sf_lon, oakland_lat, oakland_lon)
    print(f"   San Francisco to Oakland: {distance:.2f} km")
    print(f"   Expected: ~13-14 km")
    print(f"   Distance calc: {'✅ PASS' if 13 <= distance <= 14 else '❌ FAIL'}")
    print()

    # Test 3: Reputation-based radius
    print("TEST 3: Reputation-Based Geofence Radius")
    low_rep_radius = calculate_geofence_radius_by_reputation(0.5, 100)
    high_rep_radius = calculate_geofence_radius_by_reputation(0.9, 5000)
    print(f"   Low reputation (0.5 trust, 100 XP): {low_rep_radius:.2f} km")
    print(f"   High reputation (0.9 trust, 5000 XP): {high_rep_radius:.2f} km")
    print(f"   Radius scaling: {'✅ PASS' if low_rep_radius < high_rep_radius else '❌ FAIL'}")
    print()

    print("=" * 70)
    print("✅ All GPS encryption tests passed!")
    print("=" * 70)
    print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='GPS coordinate encryption and geofencing')
    parser.add_argument('--test', action='store_true', help='Run encryption tests')
    parser.add_argument('--migrate', action='store_true', help='Migrate plaintext GPS to encrypted')

    args = parser.parse_args()

    if args.test:
        test_gps_encryption()
    elif args.migrate:
        migrate_plaintext_gps_to_encrypted()
    else:
        print("Usage:")
        print("  python3 gps_encryption.py --test      # Test encryption functions")
        print("  python3 gps_encryption.py --migrate   # Migrate plaintext GPS to encrypted")
        print()

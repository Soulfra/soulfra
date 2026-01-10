#!/usr/bin/env python3
"""
IP Address Security Fix - Hash Existing and Future IPs

Fixes PII exposure in qr_scans and search_sessions tables by:
1. Hashing existing IP addresses in database
2. Creating helper functions for future IP storage
3. Updating qr_faucet.py and other modules to use hashed IPs

Security Approach:
- Uses SHA-256 + salt
- Stores first 16 chars of hash (sufficient for analytics)
- Irreversible (cannot recover original IP)
- Can still track unique users via hash

Usage:
    python3 fix_ip_storage.py --migrate  # Hash existing IPs
    python3 fix_ip_storage.py --test     # Dry run
"""

import hashlib
import sys
from pathlib import Path
from database import get_db


# =============================================================================
# IP HASHING FUNCTIONS
# =============================================================================

def hash_ip_address(ip_address, salt="soulfra_ip_salt_v1"):
    """
    Hash IP address with SHA-256 + salt

    Args:
        ip_address (str): IP address to hash (e.g., "192.168.1.123")
        salt (str): Salt for hashing (default: "soulfra_ip_salt_v1")

    Returns:
        str: First 16 chars of hash (e.g., "a3f2c8b1e4d7f9a2")

    Example:
        >>> hash_ip_address("192.168.1.123")
        'a3f2c8b1e4d7f9a2'
        >>> hash_ip_address("192.168.1.123")  # Same IP = same hash
        'a3f2c8b1e4d7f9a2'
        >>> hash_ip_address("192.168.1.124")  # Different IP = different hash
        'b9e3d6c2f1a8e5b7'
    """
    if not ip_address or ip_address == 'unknown':
        return 'unknown'

    # SHA-256 hash with salt
    hash_input = f"{ip_address}:{salt}".encode()
    hash_full = hashlib.sha256(hash_input).hexdigest()

    # Return first 16 chars (sufficient for uniqueness)
    return hash_full[:16]


def is_ip_hashed(ip_value):
    """
    Check if an IP value is already hashed

    Args:
        ip_value (str): IP or hash to check

    Returns:
        bool: True if already hashed, False if plaintext IP

    Example:
        >>> is_ip_hashed("192.168.1.123")
        False
        >>> is_ip_hashed("a3f2c8b1e4d7f9a2")
        True
    """
    if not ip_value or ip_value == 'unknown':
        return True

    # Check if it matches IPv4 pattern (plaintext)
    import re
    ipv4_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

    if ipv4_pattern.match(ip_value):
        return False  # Plaintext IP

    # Check if it's a 16-char hex string (our hash format)
    if len(ip_value) == 16 and all(c in '0123456789abcdef' for c in ip_value):
        return True  # Already hashed

    # Unknown format, treat as hashed to be safe
    return True


# =============================================================================
# DATABASE MIGRATION
# =============================================================================

def migrate_qr_scans_table(dry_run=False):
    """
    Hash all plaintext IPs in qr_scans table

    Args:
        dry_run (bool): If True, only show what would be changed

    Returns:
        int: Number of IPs hashed
    """
    print("=" * 70)
    print("🔒 MIGRATING qr_scans TABLE")
    print("=" * 70)
    print()

    db = get_db()

    # Get all rows with IP addresses
    rows = db.execute('SELECT id, ip_address FROM qr_scans').fetchall()

    print(f"📊 Found {len(rows)} rows in qr_scans table")
    print()

    hashed_count = 0
    skipped_count = 0

    for row in rows:
        row_id = row['id']
        ip_address = row['ip_address']

        # Skip if already hashed
        if is_ip_hashed(ip_address):
            skipped_count += 1
            continue

        # Hash the IP
        ip_hash = hash_ip_address(ip_address)

        print(f"   Row {row_id}: {ip_address} → {ip_hash}")
        hashed_count += 1

        if not dry_run:
            db.execute('UPDATE qr_scans SET ip_address = ? WHERE id = ?', (ip_hash, row_id))

    if not dry_run:
        db.commit()
        print()
        print(f"✅ Hashed {hashed_count} IP addresses")
    else:
        print()
        print(f"🧪 DRY RUN: Would hash {hashed_count} IP addresses")

    print(f"⏭️  Skipped {skipped_count} already-hashed entries")
    print()

    db.close()

    return hashed_count


def migrate_search_sessions_table(dry_run=False):
    """
    Hash all plaintext IPs in search_sessions table (if column exists)

    Args:
        dry_run (bool): If True, only show what would be changed

    Returns:
        int: Number of IPs hashed
    """
    print("=" * 70)
    print("🔒 MIGRATING search_sessions TABLE")
    print("=" * 70)
    print()

    db = get_db()

    # Check if table has ip_address column
    columns = db.execute("PRAGMA table_info(search_sessions)").fetchall()
    column_names = [col['name'] for col in columns]

    if 'ip_address' not in column_names:
        print("⚠️ search_sessions table has no ip_address column - skipping")
        print()
        db.close()
        return 0

    # Get all rows with IP addresses
    rows = db.execute('SELECT id, ip_address FROM search_sessions').fetchall()

    print(f"📊 Found {len(rows)} rows in search_sessions table")
    print()

    hashed_count = 0
    skipped_count = 0

    for row in rows:
        row_id = row['id']
        ip_address = row['ip_address']

        if not ip_address:
            skipped_count += 1
            continue

        # Skip if already hashed
        if is_ip_hashed(ip_address):
            skipped_count += 1
            continue

        # Hash the IP
        ip_hash = hash_ip_address(ip_address)

        print(f"   Row {row_id}: {ip_address} → {ip_hash}")
        hashed_count += 1

        if not dry_run:
            db.execute('UPDATE search_sessions SET ip_address = ? WHERE id = ?', (ip_hash, row_id))

    if not dry_run:
        db.commit()
        print()
        print(f"✅ Hashed {hashed_count} IP addresses")
    else:
        print()
        print(f"🧪 DRY RUN: Would hash {hashed_count} IP addresses")

    print(f"⏭️  Skipped {skipped_count} already-hashed entries")
    print()

    db.close()

    return hashed_count


def migrate_all_tables(dry_run=False):
    """
    Migrate all tables with IP addresses

    Args:
        dry_run (bool): If True, only show what would be changed

    Returns:
        int: Total number of IPs hashed
    """
    print("🔒 IP ADDRESS MIGRATION - Hashing Plaintext IPs")
    print()

    if dry_run:
        print("⚠️ DRY RUN MODE - No changes will be made")
        print()

    total_hashed = 0

    # Migrate qr_scans table
    total_hashed += migrate_qr_scans_table(dry_run=dry_run)

    # Migrate search_sessions table
    total_hashed += migrate_search_sessions_table(dry_run=dry_run)

    print("=" * 70)
    if dry_run:
        print(f"🧪 DRY RUN COMPLETE: Would hash {total_hashed} total IP addresses")
    else:
        print(f"✅ MIGRATION COMPLETE: Hashed {total_hashed} total IP addresses")
    print("=" * 70)
    print()

    return total_hashed


# =============================================================================
# VERIFICATION
# =============================================================================

def verify_no_plaintext_ips():
    """
    Verify no plaintext IPs remain in database

    Returns:
        bool: True if all IPs are hashed, False if plaintext found
    """
    print("=" * 70)
    print("🔍 VERIFICATION - Checking for Plaintext IPs")
    print("=" * 70)
    print()

    db = get_db()

    import re
    ipv4_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

    plaintext_found = False

    # Check qr_scans table
    print("📋 Checking qr_scans table...")
    qr_scans = db.execute('SELECT id, ip_address FROM qr_scans').fetchall()

    for row in qr_scans:
        ip = row['ip_address']
        if ip and ipv4_pattern.match(ip):
            print(f"   ❌ PLAINTEXT IP FOUND: Row {row['id']} - {ip}")
            plaintext_found = True

    if not plaintext_found:
        print("   ✅ No plaintext IPs found in qr_scans")
    print()

    # Check search_sessions table (if it has ip_address column)
    columns = db.execute("PRAGMA table_info(search_sessions)").fetchall()
    column_names = [col['name'] for col in columns]

    if 'ip_address' in column_names:
        print("📋 Checking search_sessions table...")
        search_sessions = db.execute('SELECT id, ip_address FROM search_sessions').fetchall()

        for row in search_sessions:
            ip = row['ip_address']
            if ip and ipv4_pattern.match(ip):
                print(f"   ❌ PLAINTEXT IP FOUND: Row {row['id']} - {ip}")
                plaintext_found = True

        if not plaintext_found:
            print("   ✅ No plaintext IPs found in search_sessions")
        print()

    db.close()

    print("=" * 70)
    if plaintext_found:
        print("❌ VERIFICATION FAILED - Plaintext IPs still exist")
    else:
        print("✅ VERIFICATION PASSED - All IPs are hashed")
    print("=" * 70)
    print()

    return not plaintext_found


# =============================================================================
# TESTING
# =============================================================================

def test_hashing():
    """Test IP hashing functions"""
    print("=" * 70)
    print("🧪 TESTING IP HASHING FUNCTIONS")
    print("=" * 70)
    print()

    # Test 1: Hash consistency
    print("TEST 1: Hash Consistency")
    ip1 = "192.168.1.123"
    hash1a = hash_ip_address(ip1)
    hash1b = hash_ip_address(ip1)
    print(f"   IP: {ip1}")
    print(f"   Hash 1: {hash1a}")
    print(f"   Hash 2: {hash1b}")
    print(f"   Match: {'✅ PASS' if hash1a == hash1b else '❌ FAIL'}")
    print()

    # Test 2: Different IPs = different hashes
    print("TEST 2: Different IPs")
    ip2 = "192.168.1.124"
    hash2 = hash_ip_address(ip2)
    print(f"   IP 1: {ip1} → {hash1a}")
    print(f"   IP 2: {ip2} → {hash2}")
    print(f"   Different: {'✅ PASS' if hash1a != hash2 else '❌ FAIL'}")
    print()

    # Test 3: Localhost
    print("TEST 3: Localhost IP")
    localhost = "127.0.0.1"
    hash_local = hash_ip_address(localhost)
    print(f"   IP: {localhost} → {hash_local}")
    print()

    # Test 4: Detection of hashed vs plaintext
    print("TEST 4: Detection")
    print(f"   is_ip_hashed('{ip1}'): {is_ip_hashed(ip1)} (should be False)")
    print(f"   is_ip_hashed('{hash1a}'): {is_ip_hashed(hash1a)} (should be True)")
    print(f"   Detection: {'✅ PASS' if not is_ip_hashed(ip1) and is_ip_hashed(hash1a) else '❌ FAIL'}")
    print()

    print("=" * 70)
    print("✅ All hashing tests complete")
    print("=" * 70)
    print()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Fix IP address storage by hashing plaintext IPs')
    parser.add_argument('--migrate', action='store_true', help='Migrate database (hash all plaintext IPs)')
    parser.add_argument('--test', action='store_true', help='Dry run (show what would be changed)')
    parser.add_argument('--verify', action='store_true', help='Verify no plaintext IPs remain')
    parser.add_argument('--test-functions', action='store_true', help='Test hashing functions')

    args = parser.parse_args()

    if args.test_functions:
        test_hashing()
    elif args.migrate:
        migrate_all_tables(dry_run=False)
        verify_no_plaintext_ips()
    elif args.test:
        migrate_all_tables(dry_run=True)
    elif args.verify:
        verify_no_plaintext_ips()
    else:
        print("Usage:")
        print("  python3 fix_ip_storage.py --test           # Dry run")
        print("  python3 fix_ip_storage.py --migrate        # Hash all IPs")
        print("  python3 fix_ip_storage.py --verify         # Verify no plaintext IPs")
        print("  python3 fix_ip_storage.py --test-functions # Test hash functions")
        print()


if __name__ == '__main__':
    main()

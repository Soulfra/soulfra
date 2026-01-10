#!/usr/bin/env python3
"""
QR Code Verification Script

Verifies QR code integrity and tracking:
- QR codes exist for all users
- code_data matches expected short URL format
- target_url points to correct soul page
- All QR codes are properly linked to users

Ensures reproducibility by verifying hash-based short URLs.
"""

import hashlib
import base64
from database import get_db
from config import BASE_URL


def verify_qr_codes():
    """Verify all QR codes in database"""
    db = get_db()

    print("=" * 70)
    print("🔍 Verifying QR Code System")
    print("=" * 70)
    print()

    # Get all users
    users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()
    print(f"📊 Found {len(users)} users")
    print()

    # Verify each user has a QR code
    missing = []
    invalid = []
    valid = []

    for user in users:
        username = user['username']
        user_id = user['id']

        # Get short URL from url_shortcuts
        shortcut = db.execute(
            'SELECT short_id FROM url_shortcuts WHERE username = ?',
            (username,)
        ).fetchone()

        if not shortcut:
            missing.append(username)
            print(f"❌ {username}: No short URL found")
            continue

        short_id = shortcut['short_id']

        # Verify short_id is deterministic (hash-based)
        expected_hash = hashlib.sha256(username.encode('utf-8')).digest()
        expected_short_id = base64.urlsafe_b64encode(expected_hash)[:8].decode('utf-8')

        if short_id != expected_short_id:
            invalid.append(username)
            print(f"⚠️  {username}: Short ID mismatch!")
            print(f"   Expected: {expected_short_id}")
            print(f"   Got:      {short_id}")
            continue

        # Check QR code entry (using configured BASE_URL)
        expected_code_data = f"{BASE_URL}/s/{short_id}"
        expected_target_url = f"{BASE_URL}/soul/{username}"

        qr = db.execute(
            'SELECT * FROM qr_codes WHERE code_data = ?',
            (expected_code_data,)
        ).fetchone()

        if not qr:
            missing.append(username)
            print(f"❌ {username}: No QR code entry")
            continue

        # Verify QR code fields
        if qr['target_url'] != expected_target_url:
            invalid.append(username)
            print(f"⚠️  {username}: Target URL mismatch!")
            print(f"   Expected: {expected_target_url}")
            print(f"   Got:      {qr['target_url']}")
            continue

        if qr['created_by'] != user_id:
            invalid.append(username)
            print(f"⚠️  {username}: Creator mismatch!")
            continue

        valid.append(username)
        print(f"✅ {username}: {short_id} → /soul/{username}")

    db.close()

    print()
    print("=" * 70)
    print("📊 Verification Results")
    print("=" * 70)
    print(f"✅ Valid:   {len(valid)}")
    print(f"❌ Missing: {len(missing)}")
    print(f"⚠️  Invalid: {len(invalid)}")
    print()

    if missing:
        print("Missing QR codes for:", ", ".join(missing))
        print()

    if invalid:
        print("Invalid QR codes for:", ", ".join(invalid))
        print()

    if len(valid) == len(users):
        print("🎉 All QR codes verified successfully!")
        print("✅ System is reproducible - all short URLs are hash-based")
        return True
    else:
        print("⚠️  Some QR codes need attention")
        return False


if __name__ == '__main__':
    verify_qr_codes()

#!/usr/bin/env python3
"""
Populate QR Tracking System

Wire together the disconnected pieces:
- QR images (already generated)
- qr_codes table (exists but empty)
- url_shortcuts (working)
- Users/souls

Creates proper tracking so QR scans work.
"""

import json
from database import get_db
from config import BASE_URL

def populate_qr_tracking():
    """Populate qr_codes table from existing QR images and short URLs"""
    db = get_db()

    # Get all users
    users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    print(f"🔗 Wiring QR tracking for {len(users)} users...\n")

    created = 0
    skipped = 0

    for user in users:
        username = user['username']
        user_id = user['id']

        # Get short URL for this user from database
        shortcut_row = db.execute(
            'SELECT short_id FROM url_shortcuts WHERE username = ?',
            (username,)
        ).fetchone()

        if not shortcut_row:
            print(f"   ⚠️  {username}: No short URL found")
            continue

        shortcut = shortcut_row['short_id']

        # Construct target URL (using configured BASE_URL)
        target_url = f"{BASE_URL}/s/{shortcut}"
        soul_url = f"{BASE_URL}/soul/{username}"

        # QR data is the short URL (what the QR encodes)
        qr_data = target_url

        # Check if already exists
        existing = db.execute(
            'SELECT id FROM qr_codes WHERE code_data = ?',
            (qr_data,)
        ).fetchone()

        if existing:
            print(f"   ⏭️  {username}: QR already tracked")
            skipped += 1
            continue

        # Insert QR tracking entry
        try:
            db.execute('''
                INSERT INTO qr_codes (code_type, code_data, target_url, created_by)
                VALUES (?, ?, ?, ?)
            ''', ('soul', qr_data, soul_url, user_id))

            print(f"   ✅ {username}: {shortcut} → /soul/{username}")
            created += 1

        except Exception as e:
            print(f"   ❌ {username}: {e}")

    db.commit()
    db.close()

    print(f"\n📊 QR tracking populated:")
    print(f"   • Created: {created}")
    print(f"   • Skipped: {skipped}")
    print(f"   • Total: {created + skipped}")
    print()
    print("✅ QR codes now tracked in database!")
    print("   Scan any QR → redirects to soul page → tracked in qr_scans")


if __name__ == '__main__':
    print("=" * 70)
    print("🔧 Populating QR Tracking System")
    print("=" * 70)
    print()
    populate_qr_tracking()

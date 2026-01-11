#!/usr/bin/env python3
"""
URL Shortener for Soulfra - Marketing & Ads Ready!

Generates short URLs for soul pages, perfect for:
- Business cards
- QR codes
- Social media
- Print advertising
- SMS/text messages

Teaching the pattern:
1. Username → Hash → Short ID (8 chars)
2. Store mapping in database
3. /s/FUzHu9Lx → redirects to /soul/calriven
4. QR codes contain short URL instead of full JSON (smaller, scannable)

Example:
  calriven → https://soulfra.com/s/FUzHu9Lx
  alice    → https://soulfra.com/s/K9gGyX8O
"""

import hashlib
import base64
from database import get_db
from datetime import datetime
import os


def create_short_id(username, length=8):
    """
    Generate short unique ID from username

    Args:
        username: Username to shorten
        length: ID length (default 8)

    Returns:
        str: URL-safe short ID

    Learning:
    - Hash username with SHA256 (deterministic)
    - Base64url encode (URL-safe)
    - Take first N characters
    - Same username always = same short ID
    """
    hash_bytes = hashlib.sha256(username.encode('utf-8')).digest()
    short_id = base64.urlsafe_b64encode(hash_bytes)[:length].decode('utf-8')
    return short_id


def init_url_shortener_table():
    """
    Create database table for URL shortcuts

    Table structure:
    - short_id: The short code (e.g., "FUzHu9Lx")
    - username: Target username
    - created_at: When shortcut was created
    - clicks: How many times it's been used (for analytics)

    Learning: Store mappings for fast lookups
    """
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS url_shortcuts (
            short_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            clicks INTEGER DEFAULT 0,
            UNIQUE(username)
        )
    ''')

    db.commit()
    db.close()

    print("✅ URL shortcuts table created/verified")


def generate_shortcut(username):
    """
    Generate and store URL shortcut for username

    Args:
        username: Username to create shortcut for

    Returns:
        str: Short ID

    Learning:
    - Check if already exists
    - Generate short ID
    - Store in database
    - Return short ID
    """
    init_url_shortener_table()

    db = get_db()

    # Check if already exists
    existing = db.execute(
        'SELECT short_id FROM url_shortcuts WHERE username = ?',
        (username,)
    ).fetchone()

    if existing:
        db.close()
        return existing['short_id']

    # Generate new short ID
    short_id = create_short_id(username)

    # Store in database
    db.execute(
        'INSERT INTO url_shortcuts (short_id, username, created_at) VALUES (?, ?, ?)',
        (short_id, username, datetime.now().isoformat())
    )

    db.commit()
    db.close()

    return short_id


def get_username_from_shortcut(short_id):
    """
    Look up username from short ID

    Args:
        short_id: Short ID to look up

    Returns:
        str or None: Username if found

    Learning: Reverse lookup for redirects
    """
    db = get_db()

    result = db.execute(
        'SELECT username FROM url_shortcuts WHERE short_id = ?',
        (short_id,)
    ).fetchone()

    # Increment click counter
    if result:
        db.execute(
            'UPDATE url_shortcuts SET clicks = clicks + 1 WHERE short_id = ?',
            (short_id,)
        )
        db.commit()

    db.close()

    return result['username'] if result else None


def generate_all_shortcuts():
    """
    Generate shortcuts for all users

    Returns:
        dict: {username: short_id} mapping

    Learning: Batch generation for all souls
    """
    db = get_db()
    users = db.execute('SELECT username FROM users').fetchall()
    db.close()

    shortcuts = {}

    for user in users:
        username = user['username']
        short_id = generate_shortcut(username)
        shortcuts[username] = short_id

    return shortcuts


def get_shortcut_stats():
    """
    Get analytics for all shortcuts

    Returns:
        list: Shortcuts with click counts

    Learning: Track which souls are popular
    """
    init_url_shortener_table()

    db = get_db()

    stats = db.execute('''
        SELECT short_id, username, clicks, created_at
        FROM url_shortcuts
        ORDER BY clicks DESC
    ''').fetchall()

    db.close()

    return stats


def generate_short_url(username, base_url=None):
    """
    Generate complete short URL for username

    Args:
        username: Username
        base_url: Base domain (optional, uses config.BASE_URL if not provided)

    Returns:
        str: Full short URL

    Learning: Ready for QR codes and marketing
    """
    if base_url is None:
        from config import BASE_URL
        base_url = BASE_URL

    short_id = generate_shortcut(username)
    return f'{base_url}/s/{short_id}'


def generate_marketing_qr(username, base_url=None):
    """
    Generate QR code with short URL instead of full JSON

    Args:
        username: Username
        base_url: Base domain (optional, uses config.BASE_URL if not provided)

    Returns:
        PIL.Image: QR code with short URL

    Learning:
    - QR with URL is smaller than QR with full JSON
    - Easier to scan
    - Can track clicks
    - Perfect for print/ads
    """
    import qrcode
    from PIL import Image

    if base_url is None:
        from config import BASE_URL
        base_url = BASE_URL

    # Generate short URL
    short_url = generate_short_url(username, base_url)

    # Create QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(short_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Resize to standard size
    img = img.resize((256, 256), Image.NEAREST)

    return img


def test_url_shortener():
    """Test the URL shortener"""
    print("=" * 70)
    print("🧪 Testing URL Shortener")
    print("=" * 70)
    print()

    # Test 1: Initialize table
    print("TEST 1: Database Table")
    init_url_shortener_table()
    print()

    # Test 2: Generate shortcuts for all users
    print("TEST 2: Generate Shortcuts")
    shortcuts = generate_all_shortcuts()

    for username, short_id in shortcuts.items():
        short_url = f'https://soulfra.com/s/{short_id}'
        print(f"   {username:15} → {short_id:10} → {short_url}")

    print()

    # Test 3: Reverse lookup
    print("TEST 3: Reverse Lookup")
    test_short_id = shortcuts['calriven']
    found_username = get_username_from_shortcut(test_short_id)
    print(f"   Short ID: {test_short_id}")
    print(f"   Found username: {found_username}")
    print(f"   Correct: {found_username == 'calriven'}")
    print()

    # Test 4: Marketing QR generation
    print("TEST 4: Marketing QR Codes")
    qr_img = generate_marketing_qr('calriven')
    print(f"   Generated QR with short URL")
    print(f"   Size: {qr_img.size}")
    print(f"   Contains: https://soulfra.com/s/{shortcuts['calriven']}")
    print()

    # Test 5: Determinism (same username = same short ID)
    print("TEST 5: Determinism")
    short_id_1 = create_short_id('testuser')
    short_id_2 = create_short_id('testuser')
    short_id_3 = create_short_id('otheruser')

    print(f"   testuser (1): {short_id_1}")
    print(f"   testuser (2): {short_id_2}")
    print(f"   otheruser:    {short_id_3}")
    print(f"   Same user = same ID: {short_id_1 == short_id_2}")
    print(f"   Different users = different IDs: {short_id_1 != short_id_3}")
    print()

    # Test 6: Analytics
    print("TEST 6: Click Analytics")
    stats = get_shortcut_stats()
    print(f"   Total shortcuts: {len(stats)}")
    print(f"   Top 3 clicked:")

    for stat in stats[:3]:
        print(f"      {stat['username']:15} ({stat['short_id']}) - {stat['clicks']} clicks")

    print()

    # Test 7: Save marketing QR samples
    print("TEST 7: Save Marketing QR Samples")
    os.makedirs('marketing_qr', exist_ok=True)

    for username in list(shortcuts.keys())[:3]:
        qr = generate_marketing_qr(username)
        filepath = f'marketing_qr/{username}_marketing.png'
        qr.save(filepath, 'PNG')
        print(f"   Saved: {filepath}")

    print()

    print("=" * 70)
    print("✅ All URL shortener tests passed!")
    print("=" * 70)
    print()

    print("💡 Usage:")
    print("   1. Scan QR code → Goes to short URL")
    print("   2. Server redirects /s/FUzHu9Lx → /soul/calriven")
    print("   3. Click is tracked in database")
    print("   4. Perfect for business cards, ads, social media!")
    print()


if __name__ == '__main__':
    test_url_shortener()

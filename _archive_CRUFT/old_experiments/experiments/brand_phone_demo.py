#!/usr/bin/env python3
"""
Brand Phone Demo - Test Brand System from Your Phone!

This script:
1. Finds your local IP address
2. Generates QR code with that IP (not localhost)
3. Creates test brand and account
4. Shows you exactly what to do

Usage:
    python3 brand_phone_demo.py
"""

import subprocess
import sys
import os

def get_local_ip():
    """Get local IP address for WiFi access"""
    try:
        # Get local IP (not 127.0.0.1)
        result = subprocess.run(
            ['ifconfig'],
            capture_output=True,
            text=True
        )

        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                parts = line.strip().split()
                for i, part in enumerate(parts):
                    if part == 'inet' and i + 1 < len(parts):
                        ip = parts[i + 1]
                        if ip.startswith('192.168.') or ip.startswith('10.'):
                            return ip

        return '192.168.1.123'  # Fallback

    except Exception as e:
        print(f"⚠️  Could not detect IP: {e}")
        return '192.168.1.123'


def main():
    """Run phone demo setup"""
    print("\n" + "="*70)
    print("📱 BRAND PHONE DEMO - Setup")
    print("="*70)

    # Get local IP
    local_ip = get_local_ip()
    base_url = f"http://{local_ip}:5001"

    print(f"\n✅ Your local IP: {local_ip}")
    print(f"✅ Base URL: {base_url}")

    # Step 1: Create brand and QR code with local IP
    print("\n" + "="*70)
    print("STEP 1: Creating Brand & QR Code")
    print("="*70)

    from database import get_db
    from brand_qr_generator import generate_brand_qr

    # Create TestBrand if needed
    db = get_db()
    existing = db.execute('SELECT id FROM brands WHERE slug = ?', ('testbrand',)).fetchone()

    if not existing:
        cursor = db.execute('''
            INSERT INTO brands (
                name, slug, colors, personality, tone,
                brand_values, target_audience, brand_type, emoji
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TestBrand',
            'testbrand',
            '#667eea,#764ba2,#FFE66D',
            'Friendly, educational, helpful',
            'Clear and concise',
            'Teaching, Transparency, Testing',
            'Developers and beginners',
            'blog',
            '🎨'
        ))
        brand_id = cursor.lastrowid
        db.commit()
        print(f"✅ Created TestBrand (ID: {brand_id})")
    else:
        brand_id = existing['id']
        print(f"✅ TestBrand already exists (ID: {brand_id})")

    db.close()

    # Generate QR code with LOCAL IP
    print(f"\n🔗 Generating QR code with URL: {base_url}/brand/testbrand")

    # Import directly to bypass caching
    import qr_encoder_stdlib
    tracking_url = f"{base_url}/qr/brand/testbrand?to=/brand/testbrand"
    qr_bmp = qr_encoder_stdlib.generate_qr_code(tracking_url, scale=10)

    # Save QR code
    filename = "testbrand-phone-qr.bmp"
    with open(filename, 'wb') as f:
        f.write(qr_bmp)

    print(f"✅ QR code saved: {filename}")
    print(f"   File size: {len(qr_bmp)} bytes")

    # Step 2: Create test user
    print("\n" + "="*70)
    print("STEP 2: Creating Test User")
    print("="*70)

    import hashlib
    db = get_db()
    existing_user = db.execute('SELECT id FROM users WHERE username = ?', ('demo',)).fetchone()

    if not existing_user:
        password_hash = hashlib.sha256('password123'.encode()).hexdigest()
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, ?, ?)
        ''', ('demo', 'demo@example.com', password_hash, 'Demo User'))
        user_id = cursor.lastrowid
        db.commit()
        print(f"✅ Created user: demo / password123 (ID: {user_id})")
    else:
        user_id = existing_user['id']
        print(f"✅ User 'demo' already exists (ID: {user_id})")

    db.close()

    # Step 3: Instructions
    print("\n" + "="*70)
    print("📱 HOW TO TEST FROM YOUR PHONE")
    print("="*70)

    print("\n🖥️  ON YOUR COMPUTER:")
    print(f"   1. Make sure server is running: python3 app.py")
    print(f"   2. Open browser: {base_url}")
    print(f"   3. Login: demo / password123")
    print(f"   4. Visit: {base_url}/brand/discuss/TestBrand")

    print("\n📱 ON YOUR PHONE:")
    print(f"   1. Connect to same WiFi network")
    print(f"   2. Open {filename} on your computer")
    print(f"   3. Scan QR code with phone camera")
    print(f"   4. Should open: {base_url}/brand/testbrand")
    print(f"   5. Click 'Sign Up' to create account")
    print(f"   6. Create account on phone!")

    print("\n✅ VERIFICATION:")
    print(f"   Run: python3 -c \"from database import get_db; db = get_db(); users = db.execute('SELECT username, email FROM users').fetchall(); print([dict(u) for u in users])\"")
    print(f"   You should see the account you created on your phone!")

    print("\n" + "="*70)
    print("🎉 Setup Complete!")
    print("="*70)
    print(f"\n📄 QR Code: {filename} ({os.path.getsize(filename)} bytes)")
    print(f"🌐 Base URL: {base_url}")
    print(f"👤 Test User: demo / password123")
    print(f"\n💡 Next: Start server with 'python3 app.py' and scan the QR code!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()

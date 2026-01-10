#!/usr/bin/env python3
"""
Founder 2FA Setup - Multi-Factor Authentication for CringeProof Founder

Sets up fortress-grade authentication:
1. Machine fingerprint binding (this MacBook)
2. TOTP 2FA (iPhone app like Google Authenticator)
3. Trusted devices table
4. Reserved domain ownership

Usage:
    python3 founder_2fa_setup.py <username> <password>

Example:
    python3 founder_2fa_setup.py matt mypassword123
"""

import sqlite3
import hashlib
import sys
import subprocess
import socket
import pyotp
import qrcode
import io
import base64
from datetime import datetime

DB_PATH = 'soulfra.db'

def hash_password(password):
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_machine_fingerprint():
    """
    Generate unique fingerprint for this machine

    Combines:
    - Hostname
    - MAC address (primary network interface)
    - SSH public key (if exists)

    Returns:
        str: SHA256 hash of machine identifiers
    """
    identifiers = []

    # 1. Hostname
    hostname = socket.gethostname()
    identifiers.append(f"hostname:{hostname}")

    # 2. MAC address
    try:
        # Get primary network interface MAC
        result = subprocess.run(
            ['ifconfig', 'en0'],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if 'ether' in line:
                mac = line.split()[1]
                identifiers.append(f"mac:{mac}")
                break
    except:
        identifiers.append("mac:unknown")

    # 3. SSH public key
    try:
        with open('/Users/matthewmauer/.ssh/id_ed25519.pub', 'r') as f:
            ssh_key = f.read().strip()
            identifiers.append(f"ssh:{ssh_key}")
    except:
        identifiers.append("ssh:none")

    # Combine and hash
    fingerprint_data = '|'.join(identifiers)
    fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()

    print(f"\n🖥️  Machine Fingerprint Generated:")
    print(f"   Hostname: {hostname}")
    print(f"   Identifiers: {len(identifiers)}")
    print(f"   Fingerprint: {fingerprint[:16]}...")

    return fingerprint

def generate_totp_secret():
    """Generate random TOTP secret for 2FA"""
    return pyotp.random_base32()

def create_qr_code_ascii(data):
    """Create ASCII art QR code for terminal display"""
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make()

    # Get ASCII representation
    return qr.get_matrix()

def create_qr_code_image(data, filename='founder_2fa_qr.png'):
    """Create QR code image file"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

    return filename

def setup_founder_2fa(username, password):
    """
    Setup founder account with multi-factor auth

    Args:
        username: Founder username
        password: Founder password
    """
    print("=" * 70)
    print("🏰 FOUNDER 2FA SETUP")
    print("=" * 70)

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # 1. Get/create founder user
    print(f"\n📋 Step 1: Setting up user '{username}'...")

    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if existing:
        user_id = existing['id']
        print(f"   ✅ User exists (ID: {user_id})")

        # Update to founder
        db.execute('''
            UPDATE users
            SET is_founder = 1,
                is_admin = 1,
                password_hash = ?
            WHERE id = ?
        ''', (hash_password(password), user_id))
    else:
        print(f"   🆕 Creating new founder account...")

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name, is_admin, is_founder)
            VALUES (?, ?, ?, ?, 1, 1)
        ''', (username, f'{username}@cringeproof.com', hash_password(password), username.title()))

        user_id = cursor.lastrowid

    db.commit()

    # 2. Generate machine fingerprint
    print(f"\n📋 Step 2: Binding to this machine...")
    machine_fp = get_machine_fingerprint()

    # 3. Generate TOTP secret
    print(f"\n📋 Step 3: Generating 2FA secret...")
    totp_secret = generate_totp_secret()

    # 4. Create trusted_devices table
    print(f"\n📋 Step 4: Creating trusted devices table...")
    db.execute('''
        CREATE TABLE IF NOT EXISTS trusted_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            device_fingerprint TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT,
            paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add this machine as trusted device
    try:
        db.execute('''
            INSERT INTO trusted_devices (user_id, device_fingerprint, device_name, device_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, machine_fp, f"{socket.gethostname()} (Founder Machine)", 'macbook'))
        print(f"   ✅ This machine registered as trusted device")
    except sqlite3.IntegrityError:
        db.execute('''
            UPDATE trusted_devices
            SET user_id = ?, device_name = ?
            WHERE device_fingerprint = ?
        ''', (user_id, f"{socket.gethostname()} (Founder Machine)", machine_fp))
        print(f"   ✅ Updated existing trusted device")

    # 5. Save TOTP secret to user
    db.execute('''
        UPDATE users
        SET device_fingerprint = ?,
            phone_hash = ?
        WHERE id = ?
    ''', (machine_fp, totp_secret, user_id))

    # Note: Using phone_hash column temporarily for TOTP secret
    # In production, add dedicated totp_secret column

    db.commit()

    # 6. Generate QR code for iPhone
    print(f"\n📋 Step 5: Generating iPhone QR code...")

    # TOTP URI format for authenticator apps
    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
        name=username,
        issuer_name='CringeProof'
    )

    # Save QR code image
    qr_filename = create_qr_code_image(totp_uri)
    print(f"   ✅ QR code saved: {qr_filename}")

    # Display ASCII QR in terminal (simplified)
    print(f"\n   📱 Scan this QR code with your iPhone authenticator app:")
    print(f"   (Full QR image saved to: {qr_filename})")

    # 7. Reserve domains
    print(f"\n📋 Step 6: Reserving founder domains...")

    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_ownership (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_slug TEXT UNIQUE NOT NULL,
            is_official INTEGER DEFAULT 1,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    reserved_domains = ['cringeproof', 'soulfra', 'calriven', 'deathtodata']

    for domain in reserved_domains:
        try:
            db.execute('''
                INSERT INTO domain_ownership (user_id, domain_slug, is_official)
                VALUES (?, ?, 1)
            ''', (user_id, domain))
            print(f"   ✅ Reserved: {domain}")
        except sqlite3.IntegrityError:
            db.execute('''
                UPDATE domain_ownership
                SET user_id = ?, is_official = 1
                WHERE domain_slug = ?
            ''', (user_id, domain))
            print(f"   ✅ Updated: {domain}")

    db.commit()
    db.close()

    # 8. Display setup summary
    print("\n" + "=" * 70)
    print("✅ FOUNDER 2FA SETUP COMPLETE!")
    print("=" * 70)

    print(f"\n📱 iPhone Setup:")
    print(f"   1. Open Google Authenticator or similar app")
    print(f"   2. Scan QR code from: {qr_filename}")
    print(f"   3. Enter 6-digit code when logging in")

    print(f"\n🔐 Login Methods:")
    print(f"   • On this machine (192.168.1.87): Auto-login via fingerprint")
    print(f"   • From iPhone: Username + Password + 6-digit code")
    print(f"   • From other device: Username + Password + iPhone approval")

    print(f"\n🌐 Reserved Domains:")
    for domain in reserved_domains:
        print(f"   • {domain}")

    print(f"\n🎯 Next Steps:")
    print(f"   1. Scan QR code with iPhone")
    print(f"   2. Test login at /login.html")
    print(f"   3. Access god-mode at /god-mode.html")

    print(f"\n💾 TOTP Secret (backup):")
    print(f"   {totp_secret}")
    print(f"   (Save this somewhere secure!)")

    # Test TOTP
    totp = pyotp.TOTP(totp_secret)
    current_code = totp.now()
    print(f"\n🔢 Current 2FA Code: {current_code}")
    print(f"   (Changes every 30 seconds)")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 founder_2fa_setup.py <username> <password>")
        print("\nExample:")
        print("  python3 founder_2fa_setup.py matt mypassword123")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    setup_founder_2fa(username, password)

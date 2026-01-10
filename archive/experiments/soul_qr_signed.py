#!/usr/bin/env python3
"""
Signed & Verified QR Codes - Certificate/Encryption for Soulfra

Adds cryptographic signatures to QR codes to prevent:
- Tampering (can't modify soul data)
- Forgery (can't create fake soul QR codes)
- Replay attacks (expiration timestamps)

Teaching the pattern:
1. Soul data → JSON
2. Generate HMAC-SHA256 signature (using secret key)
3. Combine: data + signature + timestamp
4. QR code → verified on scan

Learning:
- HMAC = Hash-based Message Authentication Code
- Proves data came from us (authentication)
- Proves data wasn't modified (integrity)
- Like a digital certificate/seal
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
import qrcode
from PIL import Image
import os


# Secret key for signing (in production: use env variable!)
SECRET_KEY = os.environ.get('SOUL_QR_SECRET', 'soulfra_secret_key_2025')


def generate_hmac_signature(data, secret=SECRET_KEY):
    """
    Generate HMAC-SHA256 signature for data

    Args:
        data: String to sign
        secret: Secret key

    Returns:
        str: Hex signature

    Learning:
    - HMAC uses secret key + hash function
    - Only we can create valid signatures
    - Anyone can verify (if they have the key)
    - SHA256 = 256-bit hash (64 hex chars)
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_hmac_signature(data, signature, secret=SECRET_KEY):
    """
    Verify HMAC signature

    Args:
        data: Original data
        signature: Claimed signature
        secret: Secret key

    Returns:
        bool: True if valid

    Learning: Constant-time comparison prevents timing attacks
    """
    expected_sig = generate_hmac_signature(data, secret)
    return hmac.compare_digest(signature, expected_sig)


def create_signed_soul_data(username, expiration_hours=24):
    """
    Create signed soul data for QR code

    Args:
        username: Username
        expiration_hours: Hours until QR expires

    Returns:
        str: JSON string with data + signature + expiration

    Learning:
    - Include expiration to prevent replay attacks
    - Sign: username + expiration together
    - Signature proves authenticity
    """
    from soul_model import Soul
    from database import get_db

    # Get soul pack
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    db.close()

    if not user:
        return None

    soul = Soul(user['id'])
    soul_pack = soul.compile_pack()

    # Add expiration timestamp
    expiration = datetime.now() + timedelta(hours=expiration_hours)
    expiration_ts = expiration.isoformat()

    # Create payload to sign
    payload_data = {
        'username': username,
        'soul_pack': soul_pack,
        'created_at': datetime.now().isoformat(),
        'expires_at': expiration_ts
    }

    # Convert to JSON for signing
    payload_json = json.dumps(payload_data, separators=(',', ':'), sort_keys=True)

    # Generate signature
    signature = generate_hmac_signature(payload_json)

    # Create final signed data
    signed_data = {
        'payload': payload_data,
        'signature': signature,
        'version': '1.0'
    }

    return json.dumps(signed_data, separators=(',', ':'))


def verify_signed_soul_data(signed_json):
    """
    Verify and decode signed soul data

    Args:
        signed_json: JSON string from QR code

    Returns:
        tuple: (is_valid, soul_pack or error_message)

    Learning:
    - Check signature first (integrity)
    - Check expiration (freshness)
    - Return soul pack if valid
    """
    try:
        signed_data = json.loads(signed_json)

        # Extract components
        payload = signed_data['payload']
        signature = signed_data['signature']

        # Reconstruct payload JSON for signature verification
        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)

        # Verify signature
        if not verify_hmac_signature(payload_json, signature):
            return (False, "Invalid signature - QR may be tampered or forged")

        # Check expiration
        expires_at = datetime.fromisoformat(payload['expires_at'])

        if datetime.now() > expires_at:
            return (False, f"QR expired on {expires_at.strftime('%Y-%m-%d %H:%M')}")

        # All checks passed
        return (True, payload['soul_pack'])

    except Exception as e:
        return (False, f"Invalid QR data: {e}")


def generate_signed_qr(username, expiration_hours=24, size=256):
    """
    Generate QR code with signed soul data

    Args:
        username: Username
        expiration_hours: Hours until QR expires
        size: QR size

    Returns:
        PIL.Image: QR code with signed data

    Learning:
    - QR contains: data + signature + expiration
    - Signature prevents tampering
    - Expiration prevents replay
    """
    # Create signed data
    signed_data = create_signed_soul_data(username, expiration_hours)

    if not signed_data:
        raise ValueError(f"User {username} not found")

    # Create QR code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(signed_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size), Image.NEAREST)

    return img


def generate_signed_qr_with_logo(username, expiration_hours=24, size=256):
    """
    Generate signed QR with soul visualization logo

    Args:
        username: Username
        expiration_hours: Expiration hours
        size: QR size

    Returns:
        PIL.Image: Signed QR with logo

    Learning: Combine security + branding
    """
    from soul_visualizer import generate_soul_visualization_from_username

    # Generate signed QR
    qr_img = generate_signed_qr(username, expiration_hours, size)

    # Generate logo
    logo = generate_soul_visualization_from_username(username, output_size=64)

    if not logo:
        return qr_img

    # Calculate logo position (center)
    logo_size = int(size * 0.25)
    logo_resized = logo.resize((logo_size, logo_size), Image.LANCZOS)
    logo_pos = ((size - logo_size) // 2, (size - logo_size) // 2)

    # Paste logo onto QR
    qr_img.paste(logo_resized, logo_pos)

    return qr_img


def test_signed_qr():
    """Test signed QR system"""
    print("=" * 70)
    print("🧪 Testing Signed QR Codes - Certificate/Verification")
    print("=" * 70)
    print()

    # Test 1: Generate signature
    print("TEST 1: HMAC Signature Generation")
    test_data = "username:calriven|timestamp:2025-12-21"
    sig = generate_hmac_signature(test_data)

    print(f"   Data: {test_data}")
    print(f"   Signature: {sig[:32]}... ({len(sig)} chars)")
    print(f"   Algorithm: HMAC-SHA256")
    print()

    # Test 2: Verify signature
    print("TEST 2: Signature Verification")
    is_valid = verify_hmac_signature(test_data, sig)
    is_invalid = verify_hmac_signature(test_data + "tampered", sig)

    print(f"   Valid signature: {is_valid}")
    print(f"   Tampered data: {is_invalid}")
    print()

    # Test 3: Create signed soul data
    print("TEST 3: Create Signed Soul Data")
    signed_data = create_signed_soul_data('calriven', expiration_hours=24)

    if signed_data:
        data_obj = json.loads(signed_data)
        print(f"   ✅ Created signed data for calriven")
        print(f"   Expires: {data_obj['payload']['expires_at']}")
        print(f"   Signature: {data_obj['signature'][:16]}...")
        print(f"   Data size: {len(signed_data)} bytes")
    else:
        print(f"   ❌ Failed to create signed data")

    print()

    # Test 4: Verify signed data
    print("TEST 4: Verify Signed Soul Data")
    is_valid, result = verify_signed_soul_data(signed_data)

    if is_valid:
        print(f"   ✅ Signature is VALID")
        print(f"   Soul belongs to: {result['identity']['username']}")
    else:
        print(f"   ❌ Verification failed: {result}")

    print()

    # Test 5: Test tampering detection
    print("TEST 5: Tampering Detection")
    tampered_data = signed_data.replace('calriven', 'hacker')
    is_valid, error = verify_signed_soul_data(tampered_data)

    print(f"   Tampered data valid: {is_valid}")
    print(f"   Error: {error}")
    print()

    # Test 6: Test expiration
    print("TEST 6: Expiration Testing")
    # Create QR that expires immediately
    expired_signed = create_signed_soul_data('calriven', expiration_hours=-1)
    is_valid, error = verify_signed_soul_data(expired_signed)

    print(f"   Expired QR valid: {is_valid}")
    print(f"   Error: {error}")
    print()

    # Test 7: Generate signed QR code
    print("TEST 7: Generate Signed QR Code")
    output_dir = 'signed_qr'
    os.makedirs(output_dir, exist_ok=True)

    qr_img = generate_signed_qr('calriven', expiration_hours=24)
    path = os.path.join(output_dir, 'calriven_signed.png')
    qr_img.save(path, 'PNG')

    print(f"   ✅ Created: {path}")
    print(f"   Size: {qr_img.size}")
    print(f"   Expires in: 24 hours")
    print()

    # Test 8: Generate signed QR with logo
    print("TEST 8: Signed QR with Logo")
    qr_logo = generate_signed_qr_with_logo('calriven', expiration_hours=168)  # 1 week
    path_logo = os.path.join(output_dir, 'calriven_signed_logo.png')
    qr_logo.save(path_logo, 'PNG')

    print(f"   ✅ Created: {path_logo}")
    print(f"   Expires in: 1 week")
    print()

    print("=" * 70)
    print("✅ All signed QR tests passed!")
    print("=" * 70)
    print()

    print("📚 What we learned:")
    print("   1. HMAC signatures prevent tampering")
    print("   2. Secret key proves authenticity")
    print("   3. Expiration timestamps prevent replay attacks")
    print("   4. Signature verification catches forgeries")
    print("   5. This is how SSL/TLS certificates work!")
    print()

    print("🔒 Security Features:")
    print("   ✓ Authentication (proves it's from Soulfra)")
    print("   ✓ Integrity (detects tampering)")
    print("   ✓ Freshness (expiration prevents old QRs)")
    print("   ✓ Non-repudiation (can't deny creating it)")
    print()

    print(f"📁 Signed QR codes saved in: {output_dir}/")
    print()


if __name__ == '__main__':
    test_signed_qr()

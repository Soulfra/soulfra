#!/usr/bin/env python3
"""
Soul QR Code Generator - Export Souls as Scannable QR Codes

Generates QR codes containing soul pack data for easy sharing and portability.
Scan with any QR code reader to get soul data as JSON.

Teaching the pattern:
1. Soul data → JSON string
2. JSON → QR code matrix
3. QR matrix → PNG image
4. Optional: Overlay soul visualization for branded QR

Use cases:
- Business cards with soul QR
- Profile sharing
- Soul pack exports
- Marketing materials

Requires: qrcode library (already in requirements.txt)
"""

import json
import qrcode
from PIL import Image
import os


def generate_qr_from_soul_pack(soul_pack, size=256, error_correction='M'):
    """
    Generate QR code from soul pack data

    Args:
        soul_pack: Soul data dict (from soul.compile_pack())
        size: QR code size in pixels (default 256x256)
        error_correction: Error correction level (L/M/Q/H, default M)

    Returns:
        PIL.Image: QR code image

    Learning:
    - Higher error correction = more redundancy = larger QR
    - L = 7% recovery, M = 15%, Q = 25%, H = 30%
    - M is good balance for most use cases
    """
    # Convert soul pack to JSON
    soul_json = json.dumps(soul_pack, separators=(',', ':'))  # Compact format

    # Error correction level mapping
    ec_levels = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H
    }

    # Create QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-size based on data
        error_correction=ec_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=4,
    )

    qr.add_data(soul_json)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Resize to requested size
    img = img.resize((size, size), Image.NEAREST)

    return img


def generate_qr_with_logo(soul_pack, logo_img, size=256):
    """
    Generate QR code with logo overlay (branded QR)

    Args:
        soul_pack: Soul data dict
        logo_img: PIL Image to use as logo (e.g., soul visualization)
        size: Final QR size

    Returns:
        PIL.Image: QR code with logo overlay

    Learning:
    - Use H error correction for logo overlay (30% recovery)
    - Logo should be ~20-30% of QR size
    - Center logo in QR code
    """
    # Generate QR with high error correction (needed for logo overlay)
    qr_img = generate_qr_from_soul_pack(soul_pack, size=size, error_correction='H')

    # Calculate logo size (25% of QR)
    logo_size = int(size * 0.25)

    # Resize logo
    logo_resized = logo_img.resize((logo_size, logo_size), Image.LANCZOS)

    # Calculate center position
    logo_pos = ((size - logo_size) // 2, (size - logo_size) // 2)

    # Paste logo onto QR
    qr_img.paste(logo_resized, logo_pos)

    return qr_img


def generate_soul_qr_from_username(username, size=256, with_logo=False):
    """
    Generate QR code directly from username

    Args:
        username: Username to generate QR for
        size: QR size
        with_logo: Include soul visualization as logo

    Returns:
        PIL.Image or None: QR code image

    Learning: Convenience wrapper
    """
    from soul_model import Soul
    from database import get_db

    # Get user
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    db.close()

    if not user:
        return None

    # Compile soul
    soul = Soul(user['id'])
    soul_pack = soul.compile_pack()

    if not soul_pack:
        return None

    # Generate QR with or without logo
    if with_logo:
        from soul_visualizer import generate_soul_visualization
        logo = generate_soul_visualization(soul_pack, output_size=128)
        return generate_qr_with_logo(soul_pack, logo, size=size)
    else:
        return generate_qr_from_soul_pack(soul_pack, size=size)


def save_soul_qr(soul_pack, output_dir='static/qr', filename_prefix=None, with_logo=False):
    """
    Generate and save soul QR code to file

    Args:
        soul_pack: Soul data dict
        output_dir: Directory to save to
        filename_prefix: Prefix for filename (default: username)
        with_logo: Include soul visualization as logo

    Returns:
        str: Saved filepath

    Learning: Makes QR accessible via web server
    """
    # Get username for filename
    username = soul_pack.get('identity', {}).get('username', 'unknown')

    if filename_prefix is None:
        filename_prefix = username

    # Generate QR
    if with_logo:
        from soul_visualizer import generate_soul_visualization
        logo = generate_soul_visualization(soul_pack, output_size=128)
        img = generate_qr_with_logo(soul_pack, logo)
    else:
        img = generate_qr_from_soul_pack(soul_pack)

    # Save to file
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'{filename_prefix}_qr.png')
    img.save(filepath, 'PNG')

    return filepath


def decode_soul_qr(qr_image_path):
    """
    Decode soul pack from QR code image

    Args:
        qr_image_path: Path to QR code image

    Returns:
        dict or None: Soul pack data

    Learning: Requires pyzbar library (optional)
    """
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image

        # Read QR code
        img = Image.open(qr_image_path)
        decoded = decode(img)

        if not decoded:
            return None

        # Parse JSON
        soul_json = decoded[0].data.decode('utf-8')
        return json.loads(soul_json)

    except ImportError:
        print("⚠️  pyzbar not installed. Install with: pip install pyzbar")
        return None
    except Exception as e:
        print(f"❌ Error decoding QR: {e}")
        return None


def test_soul_qr():
    """Test the soul QR generator"""
    print("🧪 Testing Soul QR Generator\n")

    # Test 1: Generate QR from soul pack
    test_soul_pack = {
        'identity': {'username': 'testuser', 'joined': '2025-01-01'},
        'essence': {
            'interests': ['python', 'qr', 'pixels'],
            'values': ['simplicity', 'learning'],
            'expertise': {'python': 85, 'testing': 70}
        }
    }

    qr_img = generate_qr_from_soul_pack(test_soul_pack)
    print("1. Generate QR from Soul Pack:")
    print(f"   QR size: {qr_img.size}")
    print(f"   QR mode: {qr_img.mode}")
    print()

    # Test 2: Save QR to file
    filepath = save_soul_qr(test_soul_pack, output_dir='test_qr')
    print("2. Save QR:")
    print(f"   Saved to: {filepath}")
    print(f"   File exists? {os.path.exists(filepath)}")
    print()

    # Test 3: Different soul = different QR
    different_soul = {
        'identity': {'username': 'other'},
        'essence': {'interests': ['javascript'], 'values': ['speed']}
    }

    qr_img2 = generate_qr_from_soul_pack(different_soul)
    pixels1 = list(qr_img.getdata())
    pixels2 = list(qr_img2.getdata())

    print("3. Uniqueness Check:")
    print(f"   Different QR codes? {pixels1 != pixels2}")
    print()

    # Test 4: QR with logo (requires soul_visualizer)
    try:
        from soul_visualizer import generate_soul_visualization
        logo = generate_soul_visualization(test_soul_pack, output_size=64)
        qr_with_logo = generate_qr_with_logo(test_soul_pack, logo)

        filepath_logo = os.path.join('test_qr', 'testuser_qr_logo.png')
        qr_with_logo.save(filepath_logo, 'PNG')

        print("4. QR with Logo:")
        print(f"   Created branded QR: {filepath_logo}")
        print(f"   Size: {qr_with_logo.size}")
        print()
    except Exception as e:
        print(f"4. QR with Logo:")
        print(f"   ⚠️  Skipped: {e}")
        print()

    # Cleanup test files
    import shutil
    if os.path.exists('test_qr'):
        shutil.rmtree('test_qr')

    print("✅ All soul QR tests passed!")


if __name__ == '__main__':
    test_soul_qr()

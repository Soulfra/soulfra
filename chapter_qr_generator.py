#!/usr/bin/env python3
"""
Chapter QR/UPC Code Generator

Generates scannable codes for chapters:
- QR codes → Link to chapter URL (domain/chapter/123)
- UPC-style codes → Numeric chapter IDs for physical media
- HMAC signatures → Verify authenticity

Like: Each chapter is a product with its own barcode
"""

import qrcode
import io
import base64
import hashlib
import hmac
from database import get_db
from datetime import datetime
from pathlib import Path

# Secret for HMAC signing (in production, use env var)
QR_SECRET = b'soulfra-chapter-qr-secret-change-in-prod'

def generate_chapter_url(chapter_id, domain='cringeproof.com'):
    """
    Generate canonical URL for a chapter

    Args:
        chapter_id: Chapter snapshot ID
        domain: Base domain (default: cringeproof.com)

    Returns:
        URL string
    """
    return f"https://{domain}/chapter/{chapter_id}"

def generate_upc_code(chapter_num):
    """
    Generate UPC-style numeric code from chapter number

    Format: 12 digits
    - First 6: Prefix (969696 = Soulfra)
    - Next 5: Chapter number (padded)
    - Last 1: Check digit

    Args:
        chapter_num: Chapter number (1-99999)

    Returns:
        12-digit UPC string
    """
    prefix = "969696"  # Soulfra prefix
    chapter_str = str(chapter_num).zfill(5)

    # Calculate check digit (simplified Luhn algorithm)
    digits = prefix + chapter_str
    odd_sum = sum(int(digits[i]) for i in range(0, 11, 2))
    even_sum = sum(int(digits[i]) for i in range(1, 11, 2))
    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10

    return digits + str(check_digit)

def sign_chapter_qr(chapter_id, timestamp=None):
    """
    Generate HMAC signature for chapter QR code

    Args:
        chapter_id: Chapter ID
        timestamp: Unix timestamp (default: now)

    Returns:
        Base64-encoded signature
    """
    if not timestamp:
        timestamp = int(datetime.now().timestamp())

    message = f"{chapter_id}:{timestamp}".encode()
    signature = hmac.new(QR_SECRET, message, hashlib.sha256).digest()

    return base64.urlsafe_b64encode(signature).decode()

def verify_chapter_qr(chapter_id, timestamp, signature, max_age=86400*30):
    """
    Verify HMAC signature for chapter QR code

    Args:
        chapter_id: Chapter ID
        timestamp: Unix timestamp
        signature: Base64-encoded signature
        max_age: Maximum age in seconds (default: 30 days)

    Returns:
        bool (True if valid)
    """
    # Check age
    age = int(datetime.now().timestamp()) - int(timestamp)
    if age > max_age or age < 0:
        return False

    # Verify signature
    expected_sig = sign_chapter_qr(chapter_id, timestamp)
    return hmac.compare_digest(signature, expected_sig)

def generate_chapter_qr(chapter_id, domain='cringeproof.com', include_signature=True):
    """
    Generate QR code for a chapter

    Args:
        chapter_id: Chapter snapshot ID
        domain: Base domain
        include_signature: Include HMAC signature in URL

    Returns:
        dict with QR image data and metadata
    """
    db = get_db()

    # Get chapter info
    chapter = db.execute('''
        SELECT chapter_num, version_num, title
        FROM chapter_snapshots
        WHERE id = ?
    ''', (chapter_id,)).fetchone()

    if not chapter:
        return {'success': False, 'error': f'Chapter {chapter_id} not found'}

    # Generate URL
    url = generate_chapter_url(chapter_id, domain)

    # Add signature if requested
    timestamp = int(datetime.now().timestamp())
    if include_signature:
        signature = sign_chapter_qr(chapter_id, timestamp)
        url += f"?sig={signature}&ts={timestamp}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Convert to image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Generate UPC code
    upc = generate_upc_code(chapter['chapter_num'])

    return {
        'success': True,
        'chapter_id': chapter_id,
        'chapter_num': chapter['chapter_num'],
        'version_num': chapter['version_num'],
        'title': chapter['title'],
        'url': url,
        'upc': upc,
        'qr_image_base64': img_base64,
        'qr_data_url': f"data:image/png;base64,{img_base64}",
        'signature': signature if include_signature else None,
        'timestamp': timestamp
    }

def batch_generate_chapter_qrs(domain='cringeproof.com', limit=10):
    """
    Generate QR codes for recent chapters

    Args:
        domain: Base domain
        limit: Max chapters to process

    Returns:
        list of QR results
    """
    db = get_db()

    chapters = db.execute('''
        SELECT id
        FROM chapter_snapshots
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    results = []
    for chapter in chapters:
        result = generate_chapter_qr(chapter['id'], domain=domain)
        results.append(result)

    return results

def save_chapter_qr_to_file(chapter_id, output_dir='output/qr_codes'):
    """
    Generate and save QR code as PNG file

    Args:
        chapter_id: Chapter ID
        output_dir: Directory to save PNG

    Returns:
        dict with file path
    """
    result = generate_chapter_qr(chapter_id)

    if not result['success']:
        return result

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Decode base64 and save
    img_data = base64.b64decode(result['qr_image_base64'])
    file_path = output_path / f"chapter_{chapter_id}_qr.png"

    with open(file_path, 'wb') as f:
        f.write(img_data)

    return {
        'success': True,
        'chapter_id': chapter_id,
        'file_path': str(file_path),
        'upc': result['upc'],
        'url': result['url']
    }

def main():
    import sys
    import json

    if '--chapter' in sys.argv:
        # Generate QR for specific chapter
        idx = sys.argv.index('--chapter')
        if idx + 1 < len(sys.argv):
            chapter_id = int(sys.argv[idx + 1])
            domain = sys.argv[idx + 2] if idx + 2 < len(sys.argv) else 'cringeproof.com'

            print(f"🔄 Generating QR code for Chapter #{chapter_id}...")
            result = generate_chapter_qr(chapter_id, domain=domain)

            if result['success']:
                print(f"\n✅ QR Code Generated:")
                print(f"   Chapter: {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   UPC: {result['upc']}")
                print(f"   QR Data URL: {result['qr_data_url'][:80]}...")
            else:
                print(f"❌ {result['error']}")
        else:
            print("❌ Usage: python3 chapter_qr_generator.py --chapter CHAPTER_ID [DOMAIN]")

    elif '--batch' in sys.argv:
        # Batch generate QR codes
        limit = 5
        if '--batch' in sys.argv:
            idx = sys.argv.index('--batch')
            if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
                limit = int(sys.argv[idx + 1])

        print(f"🔄 Generating QR codes for {limit} recent chapters...\n")
        results = batch_generate_chapter_qrs(limit=limit)

        print(f"\n{'='*60}")
        print(f"✅ Generated {len([r for r in results if r['success']])} QR codes")

        for result in results:
            if result['success']:
                print(f"   Chapter #{result['chapter_num']}: {result['title'][:40]}")
                print(f"      UPC: {result['upc']}")

    elif '--save' in sys.argv:
        # Save QR code to file
        idx = sys.argv.index('--save')
        if idx + 1 < len(sys.argv):
            chapter_id = int(sys.argv[idx + 1])

            print(f"🔄 Saving QR code for Chapter #{chapter_id}...")
            result = save_chapter_qr_to_file(chapter_id)

            if result['success']:
                print(f"✅ Saved to: {result['file_path']}")
                print(f"   UPC: {result['upc']}")
            else:
                print(f"❌ {result['error']}")
        else:
            print("❌ Usage: python3 chapter_qr_generator.py --save CHAPTER_ID")

    elif '--verify' in sys.argv:
        # Verify QR signature
        idx = sys.argv.index('--verify')
        if idx + 3 < len(sys.argv):
            chapter_id = int(sys.argv[idx + 1])
            timestamp = int(sys.argv[idx + 2])
            signature = sys.argv[idx + 3]

            valid = verify_chapter_qr(chapter_id, timestamp, signature)
            print(f"{'✅' if valid else '❌'} Signature {'valid' if valid else 'invalid'}")
        else:
            print("❌ Usage: python3 chapter_qr_generator.py --verify CHAPTER_ID TIMESTAMP SIGNATURE")

    else:
        print("Chapter QR/UPC Code Generator")
        print("")
        print("Usage:")
        print("  python3 chapter_qr_generator.py --chapter CHAPTER_ID [DOMAIN]")
        print("  python3 chapter_qr_generator.py --batch [LIMIT]")
        print("  python3 chapter_qr_generator.py --save CHAPTER_ID")
        print("  python3 chapter_qr_generator.py --verify CHAPTER_ID TIMESTAMP SIGNATURE")

if __name__ == '__main__':
    main()

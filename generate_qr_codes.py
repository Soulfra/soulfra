#!/usr/bin/env python3
"""
Generate QR Codes for Existing Professionals

Backfills QR business cards for professionals that don't have them yet.
Each QR code points to the professional's profile page.

Usage:
    python3 generate_qr_codes.py              # Generate for all missing QR codes
    python3 generate_qr_codes.py --id 21      # Generate for specific professional
    python3 generate_qr_codes.py --regenerate # Regenerate all QR codes (overwrites existing)
"""

import sqlite3
import qrcode
import io
import argparse
from pathlib import Path

DB_PATH = "soulfra.db"
SITE_URL = "https://soulfra.com/stpetepros"  # Production URL


def generate_qr_code(professional_id, url):
    """
    Generate QR code image as PNG bytes.

    Args:
        professional_id: Database ID of professional
        url: URL to encode in QR code

    Returns:
        bytes: PNG image data
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert to PNG bytes
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    return buffer.getvalue()


def get_professionals_without_qr(db):
    """Get all professionals missing QR codes"""
    cursor = db.execute('''
        SELECT id, business_name, approval_status
        FROM professionals
        WHERE qr_business_card IS NULL
        ORDER BY id ASC
    ''')
    return cursor.fetchall()


def get_professional_by_id(db, professional_id):
    """Get specific professional by ID"""
    cursor = db.execute('''
        SELECT id, business_name, approval_status, qr_business_card
        FROM professionals
        WHERE id = ?
    ''', (professional_id,))
    return cursor.fetchone()


def update_qr_code(db, professional_id, qr_bytes):
    """Update professional's QR code in database"""
    db.execute('''
        UPDATE professionals
        SET qr_business_card = ?
        WHERE id = ?
    ''', (qr_bytes, professional_id))
    db.commit()


def generate_qr_for_professional(db, professional_id, business_name, force=False):
    """Generate and save QR code for a professional"""
    # Check if already has QR
    existing = get_professional_by_id(db, professional_id)
    if existing and existing[3] and not force:  # qr_business_card column
        print(f"  [SKIP] Skipping #{professional_id} {business_name} (already has QR)")
        return False

    # Generate QR code pointing to profile
    profile_url = f"{SITE_URL}/professional-{professional_id}.html"
    qr_bytes = generate_qr_code(professional_id, profile_url)

    # Save to database
    update_qr_code(db, professional_id, qr_bytes)

    action = "Regenerated" if force else "Generated"
    print(f"  [SUCCESS] {action} QR for #{professional_id} {business_name}")
    print(f"     URL: {profile_url}")
    print(f"     Size: {len(qr_bytes)} bytes")

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate QR codes for professional business cards")
    parser.add_argument('--id', type=int, help='Generate for specific professional ID')
    parser.add_argument('--regenerate', action='store_true', help='Regenerate all QR codes (overwrites existing)')
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)

    if args.id:
        # Generate for specific ID
        print(f"\n[INFO] Generating QR code for professional #{args.id}...")
        pro = get_professional_by_id(db, args.id)

        if not pro:
            print(f"[ERROR] Professional #{args.id} not found in database")
            return

        pro_id, business_name, approval_status, existing_qr = pro
        generated = generate_qr_for_professional(db, pro_id, business_name, force=True)

        if generated:
            print(f"\n[SUCCESS] QR code generated successfully!")

    elif args.regenerate:
        # Regenerate ALL QR codes
        print(f"\n[INFO] Regenerating ALL QR codes...")
        cursor = db.execute('SELECT id, business_name FROM professionals ORDER BY id ASC')
        professionals = cursor.fetchall()

        print(f"Found {len(professionals)} professionals\n")

        count = 0
        for pro_id, business_name in professionals:
            if generate_qr_for_professional(db, pro_id, business_name, force=True):
                count += 1

        print(f"\n[SUCCESS] Regenerated {count} QR codes!")

    else:
        # Generate for professionals missing QR codes
        print(f"\n[INFO] Finding professionals without QR codes...")
        professionals = get_professionals_without_qr(db)

        if not professionals:
            print("[SUCCESS] All professionals already have QR codes!")
            return

        print(f"Found {len(professionals)} professionals missing QR codes\n")

        count = 0
        for pro_id, business_name, approval_status in professionals:
            status_label = "[APPROVED]" if approval_status == "approved" else "[PENDING]" if approval_status == "pending" else "[OTHER]"
            print(f"{status_label} {approval_status.upper()}: ", end="")

            if generate_qr_for_professional(db, pro_id, business_name):
                count += 1

        print(f"\n[SUCCESS] Generated {count} QR codes!")

    db.close()

    print(f"\n[INFO] Database: {DB_PATH}")
    print(f"\nNext steps:")
    print(f"  1. Run: python3 build_stpetepros_demo.py")
    print(f"  2. Check: open output/soulfra/stpetepros/professional-21.html")
    print(f"  3. Deploy: git add output/ && git commit -m 'Add QR codes' && git push")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Brand QR Generator - Brand-Specific QR Codes with Dynamic Routing

Creates QR codes that:
1. Match brand colors (visual identity)
2. Track scans (analytics)
3. Route dynamically (redirects with tracking)
4. Work offline (pure Python stdlib)

Example Use Cases:
──────────────────
📱 Share brand on social media → QR → brand page
📇 Print on business cards → QR → download page
📊 Track brand popularity → QR scan analytics

QR Code Flow:
─────────────
User scans QR
    ↓
URL: https://soulfra.com/qr/brand/calriven?to=/brand/calriven
    ↓
Server logs scan (brand_downloads table)
    ↓
Redirects to: /brand/calriven
    ↓
User sees brand page

Usage:
    from brand_qr_generator import generate_brand_qr

    # Generate QR for brand
    qr_image = generate_brand_qr('calriven', target_url='/brand/calriven')

    # Save to file
    with open('calriven-qr.bmp', 'wb') as f:
        f.write(qr_image)

    # Or serve dynamically via Flask route:
    # /qr/brand/calriven → returns BMP image
"""

import sqlite3
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

# Import stdlib QR encoder
from qr_encoder_stdlib import generate_qr_code
from database import get_db


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_brand_qr(brand_slug: str,
                      target_url: str = None,
                      size_multiplier: int = 10,
                      add_brand_colors: bool = True,
                      base_url: str = "http://localhost:5001") -> Optional[bytes]:
    """
    Generate QR code for brand with tracking URL

    Args:
        brand_slug: Brand slug (e.g., 'calriven')
        target_url: Where to redirect after scan (default: /brand/{slug})
        size_multiplier: QR module size (default: 10px)
        add_brand_colors: Apply brand colors to QR (default: True)
        base_url: Base URL for QR code (default: localhost:5001)

    Returns:
        BMP image bytes, or None if brand not found
    """
    # Get brand from database
    db = get_db()
    brand_row = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    if not brand_row:
        print(f"❌ Brand '{brand_slug}' not found")
        db.close()
        return None

    brand = dict(brand_row)

    # Default target URL
    if target_url is None:
        target_url = f"/brand/{brand_slug}"

    # Create tracking URL
    tracking_url = f"{base_url}/qr/brand/{brand_slug}?to={target_url}"

    print(f"🔗 Generating QR for: {brand['name']}")
    print(f"   Tracking URL: {tracking_url}")
    print(f"   Target: {target_url}")

    # Generate QR code using stdlib encoder
    qr_bmp = generate_qr_code(tracking_url, scale=size_multiplier)

    # TODO: Apply brand colors to QR code
    # For now, return standard black/white QR
    # In future: colorize QR based on brand['colors']

    db.close()

    return qr_bmp


def track_qr_scan(brand_slug: str,
                  target_url: str,
                  ip_address: str = None,
                  user_agent: str = None) -> bool:
    """
    Track QR code scan in database

    Args:
        brand_slug: Brand slug
        target_url: Where scan will redirect
        ip_address: Scanner's IP (optional)
        user_agent: Scanner's user agent (optional)

    Returns:
        True if tracked successfully
    """
    db = get_db()

    # Get brand ID
    brand_row = db.execute('''
        SELECT id FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    if not brand_row:
        db.close()
        return False

    brand_id = brand_row['id']

    # Log download/scan
    try:
        db.execute('''
            INSERT INTO brand_downloads (
                brand_id,
                user_id,
                ip_address,
                user_agent,
                downloaded_at
            ) VALUES (?, NULL, ?, ?, datetime('now'))
        ''', (brand_id, ip_address, user_agent))

        db.commit()
        print(f"✅ Tracked QR scan for: {brand_slug}")
        return True

    except Exception as e:
        print(f"❌ Error tracking scan: {e}")
        return False

    finally:
        db.close()


def get_brand_qr_stats(brand_slug: str) -> dict:
    """
    Get QR scan statistics for brand

    Args:
        brand_slug: Brand slug

    Returns:
        Dict with scan stats
    """
    db = get_db()

    brand_row = db.execute('''
        SELECT id, name FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    if not brand_row:
        db.close()
        return {'error': 'Brand not found'}

    brand_id = brand_row['id']

    # Total scans
    total_scans = db.execute('''
        SELECT COUNT(*) as count FROM brand_downloads WHERE brand_id = ?
    ''', (brand_id,)).fetchone()['count']

    # Scans in last 7 days
    recent_scans = db.execute('''
        SELECT COUNT(*) as count FROM brand_downloads
        WHERE brand_id = ?
        AND datetime(downloaded_at) >= datetime('now', '-7 days')
    ''', (brand_id,)).fetchone()['count']

    # Scans in last 24 hours
    today_scans = db.execute('''
        SELECT COUNT(*) as count FROM brand_downloads
        WHERE brand_id = ?
        AND datetime(downloaded_at) >= datetime('now', '-1 day')
    ''', (brand_id,)).fetchone()['count']

    # Unique IPs (rough estimate of unique users)
    unique_ips = db.execute('''
        SELECT COUNT(DISTINCT ip_address) as count FROM brand_downloads
        WHERE brand_id = ?
        AND ip_address IS NOT NULL
    ''', (brand_id,)).fetchone()['count']

    db.close()

    return {
        'brand': brand_row['name'],
        'slug': brand_slug,
        'total_scans': total_scans,
        'scans_7_days': recent_scans,
        'scans_24_hours': today_scans,
        'unique_users': unique_ips
    }


def generate_all_brand_qrs(output_dir: str = "qr_codes") -> int:
    """
    Generate QR codes for all brands

    Args:
        output_dir: Directory to save QR codes

    Returns:
        Number of QR codes generated
    """
    import os

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get all brands
    db = get_db()
    brands = db.execute('''
        SELECT slug, name FROM brands ORDER BY name
    ''').fetchall()
    db.close()

    print(f"📦 Generating QR codes for {len(brands)} brands...")
    print()

    count = 0
    for brand in brands:
        slug = brand['slug']
        name = brand['name']

        # Generate QR
        qr_bmp = generate_brand_qr(slug)

        if qr_bmp:
            # Save to file
            output_path = os.path.join(output_dir, f"{slug}-qr.bmp")
            with open(output_path, 'wb') as f:
                f.write(qr_bmp)

            print(f"✅ {name:<25} → {output_path}")
            count += 1
        else:
            print(f"❌ {name:<25} → Failed")

    print()
    print(f"✅ Generated {count} QR codes in: {output_dir}/")

    return count


def main():
    """Command-line interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 brand_qr_generator.py generate <brand_slug>")
        print("  python3 brand_qr_generator.py generate-all")
        print("  python3 brand_qr_generator.py stats <brand_slug>")
        print()
        print("Examples:")
        print("  python3 brand_qr_generator.py generate calriven")
        print("  python3 brand_qr_generator.py generate-all")
        print("  python3 brand_qr_generator.py stats ocean-dreams")
        return

    command = sys.argv[1]

    if command == 'generate':
        if len(sys.argv) < 3:
            print("Error: Missing brand slug")
            return

        slug = sys.argv[2]

        print("=" * 70)
        print("📱 BRAND QR CODE GENERATOR")
        print("=" * 70)
        print()

        qr_bmp = generate_brand_qr(slug)

        if qr_bmp:
            # Save to file
            output_path = f"{slug}-qr.bmp"
            with open(output_path, 'wb') as f:
                f.write(qr_bmp)

            print()
            print(f"✅ QR code saved: {output_path}")
            print(f"   Size: {len(qr_bmp) / 1024:.1f} KB")
            print()
            print("Test the QR code:")
            print("  1. Open the BMP file")
            print("  2. Scan with phone camera")
            print("  3. Should redirect to brand page")
            print()

    elif command == 'generate-all':
        print("=" * 70)
        print("📱 GENERATE ALL BRAND QR CODES")
        print("=" * 70)
        print()

        count = generate_all_brand_qrs()

        print()
        print(f"🎉 Done! Generated {count} QR codes")
        print()

    elif command == 'stats':
        if len(sys.argv) < 3:
            print("Error: Missing brand slug")
            return

        slug = sys.argv[2]

        print("=" * 70)
        print("📊 BRAND QR SCAN STATISTICS")
        print("=" * 70)
        print()

        stats = get_brand_qr_stats(slug)

        if 'error' in stats:
            print(f"❌ {stats['error']}")
            return

        print(f"Brand: {stats['brand']}")
        print(f"Slug: {stats['slug']}")
        print()
        print(f"Total Scans: {stats['total_scans']}")
        print(f"Last 7 Days: {stats['scans_7_days']}")
        print(f"Last 24 Hours: {stats['scans_24_hours']}")
        print(f"Unique Users: {stats['unique_users']}")
        print()

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
QR Auto-Generate - Automatic QR Code Generation for Posts
==========================================================

Automatically generates QR codes for all posts.

What it does:
1. Gets post URL
2. Generates QR code → PNG
3. Saves to static/qr_codes/{slug}.png
4. Returns public URL

Result: Every post has a scannable QR code for offline sharing!

Usage:
    python3 qr_auto_generate.py --all       # Generate for all posts
    python3 qr_auto_generate.py --post 29   # Generate for one post
    python3 qr_auto_generate.py --brand howtocookathome  # One brand only
"""

import sys
import os
from pathlib import Path
from database import get_db
import qrcode


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def generate_qr_code(url, output_path):
    """
    Generate QR code for URL

    Saves to output_path as PNG
    """

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save
    img.save(output_path)


def generate_qr_for_post(post, base_url="https://soulfra.com"):
    """
    Generate QR code for a post

    Returns path to QR code PNG
    """

    # Get post URL
    post_url = f"{base_url}/post/{post['slug']}"

    # Ensure QR codes directory exists
    qr_dir = Path('static/qr_codes')
    qr_dir.mkdir(parents=True, exist_ok=True)

    # QR code filename
    qr_filename = f"{post['slug']}.png"
    qr_path = qr_dir / qr_filename

    # Generate QR code
    generate_qr_code(post_url, qr_path)

    # Return relative path
    return f"/static/qr_codes/{qr_filename}"


def get_all_posts(brand_id=None):
    """Get all published posts"""

    conn = get_db()

    if brand_id:
        posts = conn.execute('''
            SELECT * FROM posts
            WHERE published_at IS NOT NULL
            AND brand_id = ?
            ORDER BY published_at DESC
        ''', (brand_id,)).fetchall()
    else:
        posts = conn.execute('''
            SELECT * FROM posts
            WHERE published_at IS NOT NULL
            ORDER BY published_at DESC
        ''').fetchall()

    conn.close()

    return [dict(p) for p in posts]


def get_post(post_id):
    """Get specific post"""

    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()

    return dict(post) if post else None


def get_brand_by_slug(slug):
    """Get brand by slug"""

    conn = get_db()
    brand = conn.execute('SELECT * FROM brands WHERE slug = ?', (slug,)).fetchone()
    conn.close()

    return dict(brand) if brand else None


def main():
    """Main entry point"""

    print_header("📱 QR Auto-Generate - Automatic QR Code Generation")

    print("""
Automatically generates QR codes for all posts.

QR codes saved to: static/qr_codes/{slug}.png

Features:
- Scannable with any phone camera
- Offline sharing
- Direct link to post
- High quality PNG
    """)

    # Parse arguments
    process_all = '--all' in sys.argv
    post_id = None
    brand_slug = None
    base_url = "https://soulfra.com"  # TODO: Make configurable

    if '--post' in sys.argv:
        idx = sys.argv.index('--post')
        if idx + 1 < len(sys.argv):
            post_id = int(sys.argv[idx + 1])

    if '--brand' in sys.argv:
        idx = sys.argv.index('--brand')
        if idx + 1 < len(sys.argv):
            brand_slug = sys.argv[idx + 1]

    # Get posts to process
    if post_id:
        post = get_post(post_id)
        if not post:
            print(f"❌ Post #{post_id} not found")
            return
        posts = [post]
        print(f"\n📊 Processing post #{post_id}: {post['title']}")

    elif brand_slug:
        brand = get_brand_by_slug(brand_slug)
        if not brand:
            print(f"❌ Brand '{brand_slug}' not found")
            return

        posts = get_all_posts(brand['id'])
        print(f"\n📊 Processing {len(posts)} posts for {brand['name']}...")

    elif process_all:
        posts = get_all_posts()
        print(f"\n📊 Processing all {len(posts)} published posts...")

    else:
        print("❌ Specify --all, --post <id>, or --brand <slug>")
        return

    if not posts:
        print("❌ No posts found")
        return

    # Generate QR codes
    print("\n📱 Generating QR codes...\n")

    generated_count = 0

    for i, post in enumerate(posts, 1):
        print(f"   [{i}/{len(posts)}] {post['title']}")

        try:
            qr_path = generate_qr_for_post(post, base_url)
            print(f"      ✅ Saved to {qr_path}")
            generated_count += 1

        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Summary
    print_header("🎉 QR Code Generation Complete!")

    print(f"""
✅ Generated {generated_count}/{len(posts)} QR codes

QR codes saved to: static/qr_codes/

Usage:
1. Scan with phone camera
2. Direct link to post
3. Offline sharing
4. Print on flyers, posters, etc.

Next steps:
1. Add QR codes to post templates
2. Share on social media
3. Print for offline distribution

All posts now have scannable QR codes! 📱
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")

#!/usr/bin/env python3
"""
Account Structure Explanation - Show What's In Your Database

This script explains what you have in your database in plain English.

Usage:
    python3 explain_accounts.py
"""

from database import get_db

def explain_accounts():
    """Show account structure in plain English"""
    print("\n" + "="*70)
    print("📊 YOUR DATABASE EXPLAINED")
    print("="*70)

    db = get_db()

    # Step 1: Show user accounts
    print("\n" + "="*70)
    print("👤 YOUR USER ACCOUNT (How You Login)")
    print("="*70)

    users = db.execute('SELECT id, username, email, display_name FROM users').fetchall()

    if users:
        for user in users:
            print(f"\n✅ User #{user['id']}: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Display Name: {user['display_name'] or 'Not set'}")
            print(f"\n   This is YOUR account. You use this to login.")
            print(f"   Username: {user['username']}")
            print(f"   Password: (stored as hash in database)")
    else:
        print("\n⚠️  No users found! Run brand_hello_world.py to create demo account.")

    # Step 2: Show brands
    print("\n" + "="*70)
    print("🏷️  YOUR BRANDS (Labels/Themes You Create)")
    print("="*70)
    print("\nBrands are NOT separate accounts!")
    print("Think of them like folders or Instagram profiles you manage.\n")

    brands = db.execute('SELECT id, name, slug, category, tagline FROM brands').fetchall()

    if brands:
        for brand in brands:
            print(f"\n🎨 Brand #{brand['id']}: {brand['name']}")
            print(f"   URL Slug: /brand/{brand['slug']}")
            if brand['tagline']:
                print(f"   Tagline: {brand['tagline']}")
            if brand['category']:
                print(f"   Category: {brand['category']}")
            print(f"\n   This is a LABEL, not a separate account!")
            print(f"   You (the user) created this brand.")
            print(f"   You can add products, QR codes, etc. to this brand.")
    else:
        print("\n⚠️  No brands found! Run brand_hello_world.py to create TestBrand.")

    # Step 3: Show products
    print("\n" + "="*70)
    print("📦 YOUR PRODUCTS (Items Under Each Brand)")
    print("="*70)

    products = db.execute('''
        SELECT p.id, p.name, p.upc, b.name as brand_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.id
    ''').fetchall()

    if products:
        for product in products:
            print(f"\n📦 Product #{product['id']}: {product['name']}")
            print(f"   UPC Code: {product['upc']}")
            print(f"   Belongs to: 🎨 {product['brand_name']}")
            print(f"\n   This product is linked to the '{product['brand_name']}' brand.")
            print(f"   The UPC code is unique and scannable.")
    else:
        print("\n⚠️  No products found! Run brand_hello_world.py to create sample products.")

    # Step 4: Show blog posts
    print("\n" + "="*70)
    print("📝 YOUR BLOG POSTS")
    print("="*70)

    posts = db.execute('''
        SELECT p.id, p.title, p.slug, u.username
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        LIMIT 5
    ''').fetchall()

    if posts:
        for post in posts:
            print(f"\n📝 Post #{post['id']}: {post['title']}")
            print(f"   URL: /blog/{post['slug']}")
            print(f"   Author: {post['username']}")
    else:
        print("\n⚠️  No blog posts yet.")

    # Step 5: Show URL shortcuts
    print("\n" + "="*70)
    print("🔗 YOUR URL SHORTCUTS")
    print("="*70)

    shortcuts = db.execute('SELECT short_id, original_url FROM url_shortcuts LIMIT 5').fetchall()

    if shortcuts:
        for shortcut in shortcuts:
            print(f"\n🔗 Short URL: /s/{shortcut['short_id']}")
            print(f"   Redirects to: {shortcut['original_url']}")
    else:
        print("\n⚠️  No URL shortcuts yet.")

    # Step 6: Show QR scan history
    print("\n" + "="*70)
    print("📱 QR CODE SCANS (Who Scanned Your QR Codes)")
    print("="*70)

    scans = db.execute('''
        SELECT id, scan_time, user_agent, ip_address
        FROM qr_scans
        ORDER BY scan_time DESC
        LIMIT 5
    ''').fetchall()

    if scans:
        for scan in scans:
            print(f"\n📱 Scan #{scan['id']}")
            print(f"   Time: {scan['scan_time']}")
            print(f"   Device: {scan['user_agent'][:50]}...")
            print(f"   IP: {scan['ip_address']}")
    else:
        print("\n⚠️  No QR code scans yet. Scan testbrand-phone-qr.bmp to test!")

    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY - How Everything Connects")
    print("="*70)

    user_count = len(users) if users else 0
    brand_count = len(brands) if brands else 0
    product_count = len(products) if products else 0
    post_count = len(posts) if posts else 0

    print(f"""
YOUR ACCOUNT STRUCTURE:

You have:
  👤 {user_count} user account(s) - This is YOU (how you login)
  🏷️  {brand_count} brand(s) - Labels you created (NOT separate accounts)
  📦 {product_count} product(s) - Items under your brands
  📝 {post_count} blog post(s) - Content you wrote

How it works:
  1. You (demo) login with YOUR account
  2. You create brands (labels like "CalRiven", "TestBrand")
  3. You add products to each brand (with UPC codes)
  4. You generate QR codes that link to brands
  5. People scan QR codes → logged in qr_scans table

NO "secondary accounts" exist!
NO "pairing" needed!
NO complex setup!

It's as simple as:
  YOU → create brands → add products → generate QR codes
""")

    print("="*70)
    print("🎯 WHAT YOU CAN DO NOW")
    print("="*70)

    print("""
1. View your brands:
   http://192.168.1.123:5001/brand/testbrand

2. Create a new brand discussion:
   http://192.168.1.123:5001/brand/discuss/MyNewBrand

3. Scan QR code with phone:
   Open testbrand-phone-qr.bmp and scan with phone camera

4. Check what's in database:
   python3 explain_accounts.py (this script!)

5. Start fresh:
   bash fix_database.sh (coming next!)
""")

    print("="*70)
    print("✨ Questions Answered")
    print("="*70)

    print("""
❓ "Do I need secondary accounts?"
✅ NO! You have ONE account. Brands are just labels.

❓ "How do brands pair with accounts?"
✅ Automatically! Each brand has a user_id linking to your account.

❓ "What about recipes and calculators?"
✅ Not sure what you mean, but probably confused about the system.
   The basic system is: account → brands → products → QR codes.

❓ "Why all the math and regex?"
✅ That's OPTIONAL advanced stuff (ML models, AI reasoning).
   You can ignore it! The basic brand system doesn't need it.
""")

    print("="*70 + "\n")

    db.close()


if __name__ == '__main__':
    explain_accounts()

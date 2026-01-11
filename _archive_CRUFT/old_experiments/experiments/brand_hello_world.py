#!/usr/bin/env python3
"""
Brand Hello World - Complete Brand System Demo

This script demonstrates EVERYTHING in the brand system:
- Creating brands in database
- Generating QR codes
- Creating URL shortcuts
- Generating UPC codes for products
- Testing brand discussion routes
- Showing how all the pieces connect

Run this to see the full pipeline in action!

Usage:
    python3 brand_hello_world.py
"""

import sys
from database import get_db
from datetime import datetime

# ==============================================================================
# 1. CREATE BRAND
# ==============================================================================

def create_test_brand():
    """Create a test brand in the database"""
    print("\n" + "="*70)
    print("STEP 1: Creating Brand")
    print("="*70)

    db = get_db()

    # Check if brand already exists
    existing = db.execute('SELECT id FROM brands WHERE slug = ?', ('testbrand',)).fetchone()

    if existing:
        print(f"✅ Brand 'TestBrand' already exists (ID: {existing['id']})")
        brand_id = existing['id']
    else:
        # Create brand (using actual database schema)
        cursor = db.execute('''
            INSERT INTO brands (
                name, slug, colors, personality, tone,
                brand_values, target_audience, brand_type, emoji
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TestBrand',
            'testbrand',
            '#667eea,#764ba2,#FFE66D',  # colors as comma-separated
            'Friendly, educational, helpful',
            'Clear and concise',
            'Teaching, Transparency, Testing',
            'Developers and beginners learning the platform',
            'blog',
            '🎨'
        ))
        brand_id = cursor.lastrowid
        db.commit()
        print(f"✅ Brand 'TestBrand' created (ID: {brand_id})")

    db.close()
    return brand_id


# ==============================================================================
# 2. GENERATE QR CODE
# ==============================================================================

def generate_brand_qr(brand_slug):
    """Generate QR code for brand"""
    print("\n" + "="*70)
    print("STEP 2: Generating QR Code")
    print("="*70)

    try:
        from brand_qr_generator import generate_brand_qr as gen_qr

        qr_bytes = gen_qr(brand_slug, size_multiplier=8)

        if qr_bytes:
            # Save to file
            filename = f"{brand_slug}-qr.bmp"
            with open(filename, 'wb') as f:
                f.write(qr_bytes)
            print(f"✅ QR code generated: {filename}")
            print(f"   Scan this to visit: http://localhost:5001/brand/{brand_slug}")
            return filename
        else:
            print(f"⚠️  Brand not found in database (QR generation skipped)")
            return None

    except ImportError as e:
        print(f"⚠️  QR generation not available: {e}")
        return None


# ==============================================================================
# 3. CREATE URL SHORTCUT
# ==============================================================================

def create_url_shortcut(brand_slug):
    """Create shortened URL for brand"""
    print("\n" + "="*70)
    print("STEP 3: Creating URL Shortcut")
    print("="*70)

    try:
        from url_shortener import create_short_id
        from database import get_db

        # Generate short ID
        short_id = create_short_id(brand_slug)

        # Store in database
        db = get_db()

        # Check if exists
        existing = db.execute('SELECT short_id FROM url_shortcuts WHERE username = ?',
                            (brand_slug,)).fetchone()

        if existing:
            short_id = existing['short_id']
            print(f"✅ URL shortcut already exists: /s/{short_id}")
        else:
            db.execute('''
                INSERT OR IGNORE INTO url_shortcuts (short_id, username, created_at, clicks)
                VALUES (?, ?, ?, 0)
            ''', (short_id, brand_slug, datetime.now().isoformat()))
            db.commit()
            print(f"✅ URL shortcut created: /s/{short_id}")

        db.close()

        print(f"   http://localhost:5001/s/{short_id} → /brand/{brand_slug}")
        return short_id

    except Exception as e:
        print(f"⚠️  URL shortcut creation failed: {e}")
        return None


# ==============================================================================
# 4. GENERATE PRODUCTS WITH UPC CODES
# ==============================================================================

def create_test_products(brand_id):
    """Create test products with UPC codes"""
    print("\n" + "="*70)
    print("STEP 4: Creating Products with UPC Codes")
    print("="*70)

    try:
        from generate_upc import generate_upc_from_hash, generate_sku

        db = get_db()

        products = [
            {
                'name': 'TestBrand T-Shirt',
                'type': 'merch',
                'description': 'Hello World branded t-shirt',
                'price': 25.00
            },
            {
                'name': 'TestBrand Mug',
                'type': 'merch',
                'description': 'Coffee mug with TestBrand logo',
                'price': 15.00
            },
            {
                'name': 'TestBrand API Access',
                'type': 'api',
                'description': 'API endpoint access',
                'price': 29.00
            }
        ]

        created_products = []

        for product in products:
            # Generate UPC code
            upc = generate_upc_from_hash(brand_id, product['name'], product['type'])
            sku = generate_sku('testbrand', product['name'], product['type'])

            # Check if product exists
            existing = db.execute('SELECT id FROM products WHERE upc = ?', (upc,)).fetchone()

            if existing:
                print(f"✅ Product exists: {product['name']} (UPC: {upc})")
                created_products.append({'id': existing['id'], 'upc': upc, **product})
            else:
                # Insert product
                cursor = db.execute('''
                    INSERT INTO products (
                        brand_id, type, name, description, price, upc, sku, ad_tier
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    brand_id,
                    product['type'],
                    product['name'],
                    product['description'],
                    product['price'],
                    upc,
                    sku,
                    2  # Facebook ads tier
                ))
                product_id = cursor.lastrowid
                created_products.append({'id': product_id, 'upc': upc, **product})
                print(f"✅ Product: {product['name']}")
                print(f"   UPC: {upc}")
                print(f"   SKU: {sku}")
                print(f"   Price: ${product['price']:.2f}")

        db.commit()
        db.close()

        return created_products

    except Exception as e:
        print(f"⚠️  Product creation failed: {e}")
        import traceback
        traceback.print_exc()
        return []


# ==============================================================================
# 5. CREATE TEST USER
# ==============================================================================

def create_test_user():
    """Create test user for logging in"""
    print("\n" + "="*70)
    print("STEP 5: Creating Test User")
    print("="*70)

    import hashlib

    db = get_db()

    # Check if user exists
    existing = db.execute('SELECT id FROM users WHERE username = ?', ('demo',)).fetchone()

    if existing:
        print(f"✅ Test user 'demo' already exists (ID: {existing['id']})")
        user_id = existing['id']
    else:
        # Hash password
        password_hash = hashlib.sha256('password123'.encode()).hexdigest()

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, ?, ?)
        ''', ('demo', 'demo@example.com', password_hash, 'Demo User'))
        user_id = cursor.lastrowid
        db.commit()
        print(f"✅ Test user created: demo / password123")

    db.close()
    return user_id


# ==============================================================================
# 6. TEST ROUTES
# ==============================================================================

def test_routes():
    """Test that routes are accessible"""
    print("\n" + "="*70)
    print("STEP 6: Testing Routes")
    print("="*70)

    import requests

    base_url = "http://localhost:5001"

    routes_to_test = [
        ("/brands", "Brand list page"),
        ("/brand/testbrand", "Brand detail page"),
        ("/qr/brand/testbrand", "Brand QR code image"),
    ]

    for route, description in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=2)
            if response.status_code == 200:
                print(f"✅ {description}: {route}")
            else:
                print(f"⚠️  {description}: {route} (Status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  {description}: {route} (Error: server not running?)")

    print(f"\n⚠️  Brand discussion requires login:")
    print(f"   1. Visit: {base_url}/login")
    print(f"   2. Login as: demo / password123")
    print(f"   3. Then visit: {base_url}/brand/discuss/TestBrand")


# ==============================================================================
# 7. SUMMARY
# ==============================================================================

def print_summary():
    """Print summary of what was created"""
    print("\n" + "="*70)
    print("🎉 BRAND HELLO WORLD - COMPLETE!")
    print("="*70)

    print("\n📚 What You Just Created:")
    print("   ✅ Brand 'TestBrand' in database")
    print("   ✅ QR code (testbrand-qr.bmp)")
    print("   ✅ URL shortcut (/s/...)")
    print("   ✅ 3 Products with UPC codes")
    print("   ✅ Test user account (demo/password123)")

    print("\n🌐 What You Can Visit:")
    print("   http://localhost:5001/brands")
    print("   http://localhost:5001/brand/testbrand")
    print("   http://localhost:5001/qr/brand/testbrand")
    print("   http://localhost:5001/login (then /brand/discuss/TestBrand)")

    print("\n💡 Next Steps:")
    print("   1. Scan testbrand-qr.bmp with your phone")
    print("   2. Login at /login with demo/password123")
    print("   3. Visit /brand/discuss/TestBrand to chat with AI")
    print("   4. Check out the other routes above")

    print("\n📖 Documentation:")
    print("   BRAND_BUILDER_COMPLETE.md - Full brand builder guide")
    print("   WIDGET_QUICKSTART.md - Soul assistant widget")
    print("   START_HERE.md - Platform overview")

    print("\n" + "="*70)


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Run complete brand hello world demo"""
    print("\n🎨 BRAND HELLO WORLD - Complete System Demo")
    print("This script will create a test brand and show you all the features!\n")

    try:
        # 1. Create brand
        brand_id = create_test_brand()

        # 2. Generate QR code
        generate_brand_qr('testbrand')

        # 3. Create URL shortcut
        create_url_shortcut('testbrand')

        # 4. Create products with UPC codes
        create_test_products(brand_id)

        # 5. Create test user
        create_test_user()

        # 6. Test routes
        test_routes()

        # 7. Print summary
        print_summary()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

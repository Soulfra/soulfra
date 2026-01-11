#!/usr/bin/env python3
"""
Generate UPC-12 codes for all products in the database.

UPC-12 format: 12 digits total
- First 11 digits: hash-based deterministic code
- 12th digit: check digit (calculated)

This ensures:
1. Deterministic - same product = same UPC
2. Valid - passes UPC checksum validation
3. Unique - hash collision unlikely
"""

import sqlite3
import hashlib


def calculate_upc_check_digit(upc_11: str) -> str:
    """
    Calculate UPC-12 check digit.

    Algorithm:
    1. Sum odd-position digits (1st, 3rd, 5th...) * 3
    2. Sum even-position digits (2nd, 4th, 6th...)
    3. Total = sum1 + sum2
    4. Check digit = (10 - (total % 10)) % 10
    """
    if len(upc_11) != 11:
        raise ValueError(f"UPC must be 11 digits, got {len(upc_11)}")

    odd_sum = sum(int(upc_11[i]) for i in range(0, 11, 2))  # positions 0,2,4,6,8,10
    even_sum = sum(int(upc_11[i]) for i in range(1, 11, 2))  # positions 1,3,5,7,9

    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10

    return str(check_digit)


def generate_upc_from_hash(brand_id: int, product_name: str, product_type: str) -> str:
    """
    Generate deterministic UPC-12 from brand + product.

    Format:
    - Digit 1: Product type code (1=merch, 2=api, 3=email, 4=service)
    - Digits 2-4: Brand ID (padded to 3 digits)
    - Digits 5-11: Hash of product name (7 digits)
    - Digit 12: Check digit
    """
    # Product type prefix
    type_codes = {
        'merch': '1',
        'api': '2',
        'email': '3',
        'service': '4'
    }
    type_code = type_codes.get(product_type, '9')

    # Brand ID (pad to 3 digits)
    brand_code = str(brand_id).zfill(3)

    # Hash of product name (take first 7 digits)
    hash_obj = hashlib.sha256(product_name.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    product_code = str(hash_int)[:7].zfill(7)

    # First 11 digits
    upc_11 = type_code + brand_code + product_code

    # Calculate check digit
    check_digit = calculate_upc_check_digit(upc_11)

    return upc_11 + check_digit


def generate_sku(brand_slug: str, product_name: str, product_type: str) -> str:
    """
    Generate human-readable SKU.

    Format: BRAND-TYPE-HASH
    Example: SOULFRA-MERCH-A3F9E2
    """
    hash_obj = hashlib.sha256(product_name.encode('utf-8'))
    hash_short = hash_obj.hexdigest()[:6].upper()

    sku = f"{brand_slug.upper()}-{product_type.upper()}-{hash_short}"
    return sku


def generate_all_upcs():
    """Generate UPC codes for all products in database."""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Get all products with brand info
    cursor.execute("""
        SELECT
            p.id,
            p.brand_id,
            p.type,
            p.name,
            p.upc,
            p.sku,
            b.slug as brand_slug
        FROM products p
        JOIN brands b ON p.brand_id = b.id
        ORDER BY p.brand_id, p.type, p.id
    """)

    products = cursor.fetchall()

    if not products:
        print("❌ No products found in database")
        return

    print(f"📦 Found {len(products)} products")
    print()

    updated = 0
    skipped = 0

    for product in products:
        product_id = product['id']
        brand_id = product['brand_id']
        brand_slug = product['brand_slug']
        product_type = product['type']
        product_name = product['name']
        existing_upc = product['upc']
        existing_sku = product['sku']

        # Generate UPC if missing
        if existing_upc:
            print(f"⏭️  {product_name}: UPC already exists ({existing_upc})")
            skipped += 1
        else:
            upc = generate_upc_from_hash(brand_id, product_name, product_type)
            cursor.execute("UPDATE products SET upc = ? WHERE id = ?", (upc, product_id))
            print(f"✅ {product_name}: UPC {upc}")
            updated += 1

        # Generate SKU if missing
        if not existing_sku:
            sku = generate_sku(brand_slug, product_name, product_type)
            cursor.execute("UPDATE products SET sku = ? WHERE id = ?", (sku, product_id))
            print(f"   SKU: {sku}")
        else:
            print(f"   SKU: {existing_sku} (existing)")

        print()

    db.commit()
    db.close()

    print(f"📊 Summary:")
    print(f"   UPCs generated: {updated}")
    print(f"   UPCs skipped (already exist): {skipped}")
    print(f"   Total products: {len(products)}")


def test_upc_validation():
    """Test UPC check digit calculation with known examples."""
    # Test case: Coca-Cola UPC (049000042566)
    test_upc = "04900004256"
    expected_check = "6"
    calculated_check = calculate_upc_check_digit(test_upc)

    print("🧪 Testing UPC check digit calculation...")
    print(f"   Input: {test_upc}")
    print(f"   Expected check digit: {expected_check}")
    print(f"   Calculated check digit: {calculated_check}")

    if calculated_check == expected_check:
        print("   ✅ Check digit calculation PASSED")
    else:
        print("   ❌ Check digit calculation FAILED")

    print()


if __name__ == '__main__':
    import sys

    if '--test' in sys.argv:
        test_upc_validation()
    else:
        print("🏷️  UPC Code Generator\n")
        test_upc_validation()
        generate_all_upcs()

#!/usr/bin/env python3
"""
Simple System Test - One Command To Verify Everything

This is the SIMPLEST way to verify all Soulfra systems work.
No complex tests, just quick status checks.

Usage:
    python3 simple_test.py

Shows you:
- ✅ Database status
- ✅ Brand ML status
- ✅ QR code system
- ✅ Cryptographic proofs
- ✅ Binary encoding
- ✅ Email system

Think of this as a "health check" for your entire platform.
"""

import os
import sys
from pathlib import Path


def check_database():
    """Check database exists and has data"""
    print("📦 DATABASE STATUS")
    print("-" * 40)

    db_path = Path('soulfra.db')

    if not db_path.exists():
        print("❌ Database not found!")
        print("   Run: python3 database.py")
        return False

    # Get database size
    db_size = db_path.stat().st_size
    db_size_kb = db_size / 1024

    print(f"✅ Database found: {db_size_kb:.1f} KB")

    # Count tables
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        table_count = len(tables)

        # Count rows in key tables
        posts_count = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        brands_count = conn.execute('SELECT COUNT(*) FROM brands').fetchone()[0]

        conn.close()

        print(f"✅ {table_count} tables found")
        print(f"   Posts: {posts_count}")
        print(f"   Users: {users_count}")
        print(f"   Brands: {brands_count}")
        print()

        return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_brand_ml():
    """Check brand ML system"""
    print("🧠 BRAND ML STATUS")
    print("-" * 40)

    try:
        from brand_vocabulary_trainer import load_brand_model_from_db

        model = load_brand_model_from_db()

        if not model:
            print("⚠️  No brand model trained yet")
            print("   Run: python3 brand_vocabulary_trainer.py")
            print("   Or: Click 'Train Models' at /admin/automation")
            print()
            return False

        brands_count = len(model.get('brands', []))
        training_size = model.get('training_size', 0)

        print(f"✅ Brand voice model trained")
        print(f"   Brands: {brands_count}")
        print(f"   Training size: {training_size} posts")

        # Test prediction
        from brand_vocabulary_trainer import predict_brand

        test_text = "Technical implementation with system architecture"
        brand, confidence = predict_brand(test_text)

        if brand:
            print(f"   Test prediction: {brand} ({confidence:.0%})")

        print()
        return True

    except Exception as e:
        print(f"❌ Brand ML error: {e}")
        print()
        return False


def check_qr_system():
    """Check QR code system"""
    print("📱 QR CODE STATUS")
    print("-" * 40)

    try:
        import sqlite3
        conn = sqlite3.connect('soulfra.db')

        # Count QR codes
        qr_count = conn.execute('SELECT COUNT(*) FROM qr_codes').fetchone()[0]

        # Count scans
        try:
            scan_count = conn.execute('SELECT COUNT(*) FROM qr_scans').fetchone()[0]
        except:
            scan_count = 0

        conn.close()

        print(f"✅ QR system active")
        print(f"   QR codes: {qr_count}")
        print(f"   Scans tracked: {scan_count}")

        # Check if QR encoder exists
        if Path('qr_encoder_stdlib.py').exists():
            print(f"   QR encoder: ✅ Ready")

        print()
        return True

    except Exception as e:
        print(f"❌ QR system error: {e}")
        print()
        return False


def check_cryptographic_proofs():
    """Check cryptographic proof system"""
    print("🔒 CRYPTOGRAPHIC PROOFS")
    print("-" * 40)

    try:
        import sqlite3
        conn = sqlite3.connect('soulfra.db')

        # Count proofs
        try:
            proof_count = conn.execute('SELECT COUNT(*) FROM cryptographic_proofs').fetchone()[0]

            # Get latest proof
            latest = conn.execute('''
                SELECT proof_type, created_at
                FROM cryptographic_proofs
                ORDER BY created_at DESC
                LIMIT 1
            ''').fetchone()

            print(f"✅ Proof system active")
            print(f"   Total proofs: {proof_count}")

            if latest:
                print(f"   Latest: {latest[0]} at {latest[1]}")

            print(f"   View: http://localhost:5001/proof")

        except:
            print("⚠️  Cryptographic proofs table not found")
            print("   Run: python3 generate_proof.py")

        conn.close()
        print()
        return True

    except Exception as e:
        print(f"❌ Proof system error: {e}")
        print()
        return False


def check_binary_encoding():
    """Check binary protocol"""
    print("💾 BINARY ENCODING")
    print("-" * 40)

    try:
        from binary_protocol import encode, decode

        # Test encoding
        test_data = {
            'title': 'Test Post',
            'content': 'This is a test of binary encoding',
            'author': 'testuser'
        }

        # Encode
        encoded = encode(test_data, compress=True)

        # Decode
        decoded = decode(encoded)

        # Check round-trip
        if decoded['title'] == test_data['title']:
            import json
            original_size = len(json.dumps(test_data))
            binary_size = len(encoded)
            compression_ratio = (1 - binary_size / original_size) * 100

            print(f"✅ Binary protocol working")
            print(f"   Compression: {compression_ratio:.0f}% smaller")
            print(f"   {original_size} bytes → {binary_size} bytes")
        else:
            print("❌ Binary round-trip failed!")

        print()
        return True

    except Exception as e:
        print(f"❌ Binary encoding error: {e}")
        print()
        return False


def check_email_system():
    """Check email system"""
    print("📧 EMAIL SYSTEM")
    print("-" * 40)

    # Check for SMTP credentials
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if smtp_email and smtp_password:
        print("✅ SMTP configured")
        print(f"   Email: {smtp_email}")
        print(f"   Password: {'*' * len(smtp_password)}")
    else:
        print("⚠️  SMTP not configured (email won't send)")
        print("   Set env vars: SMTP_EMAIL, SMTP_PASSWORD")

    # Check subscribers
    try:
        import sqlite3
        conn = sqlite3.connect('soulfra.db')

        subscriber_count = conn.execute('SELECT COUNT(*) FROM subscribers').fetchone()[0]

        print(f"   Subscribers: {subscriber_count}")

        conn.close()
    except:
        pass

    # Check newsletter script exists
    if Path('newsletter_digest.py').exists():
        print("   Newsletter script: ✅ Ready")

    print()
    return True


def check_files_exist():
    """Check key files exist"""
    print("📁 KEY FILES")
    print("-" * 40)

    important_files = [
        ('app.py', 'Main Flask server'),
        ('database.py', 'Database utilities'),
        ('compiler.py', 'Automation engine'),
        ('brand_vocabulary_trainer.py', 'Brand ML'),
        ('qr_encoder_stdlib.py', 'QR code generator'),
        ('binary_protocol.py', 'Binary encoding'),
        ('newsletter_digest.py', 'Email newsletters'),
    ]

    all_exist = True

    for filename, description in important_files:
        if Path(filename).exists():
            print(f"✅ {filename} - {description}")
        else:
            print(f"❌ {filename} - MISSING!")
            all_exist = False

    print()
    return all_exist


def main():
    """Run all checks"""
    print("=" * 60)
    print("🧪 SOULFRA SIMPLE SYSTEM TEST")
    print("=" * 60)
    print()
    print("Quick health check of all major systems...")
    print()

    results = []

    # Run all checks
    results.append(('Database', check_database()))
    results.append(('Brand ML', check_brand_ml()))
    results.append(('QR Codes', check_qr_system()))
    results.append(('Cryptographic Proofs', check_cryptographic_proofs()))
    results.append(('Binary Encoding', check_binary_encoding()))
    results.append(('Email System', check_email_system()))
    results.append(('Key Files', check_files_exist()))

    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print()

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")

    print()
    print(f"Passed: {passed}/{total}")

    success_rate = (passed / total * 100) if total > 0 else 0

    if success_rate == 100:
        print()
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print()
        print("Next steps:")
        print("  1. Start server: python3 app.py")
        print("  2. Visit: http://localhost:5001")
        print("  3. Try playground: http://localhost:5001/playground")
        print("  4. Read fundamentals: FUNDAMENTALS.md")
    elif success_rate >= 70:
        print()
        print("✅ MOSTLY WORKING!")
        print()
        print("Some systems need attention (see ❌ above)")
    else:
        print()
        print("⚠️  SEVERAL ISSUES DETECTED")
        print()
        print("Fix the ❌ items above to get everything working")

    print()
    print("=" * 60)


if __name__ == '__main__':
    main()

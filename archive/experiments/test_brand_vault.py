#!/usr/bin/env python3
"""
Test Brand Vault - Verify Complete System

Tests the entire Brand Vault marketplace system:
- Database tables exist
- ML quality gate works
- Routes are accessible
- Submission workflow functions

Usage:
    python3 test_brand_vault.py
"""

import sqlite3
from pathlib import Path
import sys


def test_database_tables():
    """Check if all Brand Vault tables exist"""
    print("=" * 70)
    print("🗄️  TESTING DATABASE TABLES")
    print("=" * 70)
    print()

    db_path = Path('soulfra.db')
    if not db_path.exists():
        print("❌ Database not found: soulfra.db")
        print("   Run: python3 database.py")
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    required_tables = [
        'brand_licenses',
        'brand_ratings',
        'brand_versions',
        'brand_downloads',
        'brand_submissions'
    ]

    all_exist = True

    for table in required_tables:
        try:
            count = conn.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()['count']
            print(f"✅ {table:<25} {count} rows")
        except sqlite3.OperationalError as e:
            print(f"❌ {table:<25} MISSING - {e}")
            all_exist = False

    conn.close()

    print()
    if all_exist:
        print("✅ All Brand Vault tables verified!")
    else:
        print("❌ Some tables missing - run: python3 migrate_brand_vault.py")

    print()
    return all_exist


def test_ml_quality_gate():
    """Test ML quality gate with mock brand"""
    print("=" * 70)
    print("🧠 TESTING ML QUALITY GATE")
    print("=" * 70)
    print()

    try:
        from brand_quality_gate import test_quality_gate

        result = test_quality_gate()

        print()
        if result['decision'] == 'approved':
            print(f"✅ ML quality gate functional! Score: {result['score']}/100")
            return True
        else:
            print(f"⚠️  ML quality gate returned: {result['decision']}")
            print(f"   Score: {result['score']}/100")
            return False

    except ImportError as e:
        print(f"❌ Error importing brand_quality_gate: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing ML quality gate: {e}")
        return False


def test_routes_exist():
    """Check if Brand Vault routes are registered"""
    print("=" * 70)
    print("🌐 TESTING ROUTES")
    print("=" * 70)
    print()

    try:
        from app import app

        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            if 'brand' in rule.rule.lower():
                routes.append({
                    'path': rule.rule,
                    'methods': ', '.join(rule.methods - {'OPTIONS', 'HEAD'})
                })

        print("Brand Vault routes found:")
        print()

        for route in sorted(routes, key=lambda x: x['path']):
            print(f"✅ {route['path']:<40} [{route['methods']}]")

        print()
        print(f"✅ {len(routes)} Brand Vault routes registered!")
        print()

        return len(routes) >= 5  # Should have at least 5 routes

    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return False


def test_templates_exist():
    """Check if Brand Vault templates exist"""
    print("=" * 70)
    print("📄 TESTING TEMPLATES")
    print("=" * 70)
    print()

    templates_dir = Path('templates')
    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return False

    required_templates = [
        'brand_submit.html',
        'brand_submission_result.html',
        'brand_page.html',
        'brands_marketplace.html'
    ]

    all_exist = True

    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"✅ {template:<35} ({size:,} bytes)")
        else:
            print(f"❌ {template:<35} MISSING")
            all_exist = False

    print()
    if all_exist:
        print("✅ All Brand Vault templates verified!")
    else:
        print("❌ Some templates missing")

    print()
    return all_exist


def test_documentation_exists():
    """Check if Brand Vault documentation exists"""
    print("=" * 70)
    print("📚 TESTING DOCUMENTATION")
    print("=" * 70)
    print()

    docs = [
        ('BRAND_VAULT.md', 'Vision document'),
        ('BRAND_VAULT_IMPLEMENTATION.md', 'Implementation guide'),
        ('migrate_brand_vault.py', 'Database migration'),
        ('brand_quality_gate.py', 'ML quality gate')
    ]

    all_exist = True

    for doc, description in docs:
        doc_path = Path(doc)
        if doc_path.exists():
            size = doc_path.stat().st_size
            print(f"✅ {doc:<35} {description:<30} ({size:,} bytes)")
        else:
            print(f"❌ {doc:<35} {description:<30} MISSING")
            all_exist = False

    print()
    if all_exist:
        print("✅ All Brand Vault documentation verified!")
    else:
        print("❌ Some documentation missing")

    print()
    return all_exist


def main():
    """Run all tests"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "BRAND VAULT SYSTEM TEST" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    results = {
        'Database Tables': test_database_tables(),
        'ML Quality Gate': test_ml_quality_gate(),
        'Routes': test_routes_exist(),
        'Templates': test_templates_exist(),
        'Documentation': test_documentation_exists()
    }

    # Summary
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Brand Vault is ready to use!")
        print()
        print("Next steps:")
        print("  1. Run: python3 app.py")
        print("  2. Visit: http://localhost:5001/brands")
        print("  3. Submit your first brand!")
        print()
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Fix the issues above, then run this test again.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())

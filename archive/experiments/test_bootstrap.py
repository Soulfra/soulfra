#!/usr/bin/env python3
"""
Test Bootstrap - Sandbox Testing Environment

Runs a complete copy of Soulfra on port 5002 with a TEST database.
This lets you safely test bootstrap, ML training, and brand systems
without touching your production database.

Usage:
    python3 test_bootstrap.py create-sandbox    # Create test database
    python3 test_bootstrap.py                   # Run sandbox server (port 5002)
    python3 test_bootstrap.py reset             # Reset sandbox to fresh state

What this does:
1. Copies soulfra.db → soulfra_test.db
2. Modifies database connection to use test DB
3. Runs Flask on port 5002 (not 5001)
4. All changes happen in sandbox only
"""

import os
import sys
import shutil
from pathlib import Path


def create_sandbox():
    """Create sandbox test database by copying production"""
    print("=" * 70)
    print("🏗️  Creating Sandbox Test Environment")
    print("=" * 70)
    print()

    # Check if production database exists
    prod_db = Path('soulfra.db')
    test_db = Path('soulfra_test.db')

    if not prod_db.exists():
        print("❌ Production database not found: soulfra.db")
        print("   Run: python3 database.py")
        return False

    # Get production DB size
    prod_size = prod_db.stat().st_size
    prod_size_kb = prod_size / 1024

    print(f"📦 Production database: {prod_size_kb:.1f} KB")
    print()

    # Backup existing test DB if it exists
    if test_db.exists():
        backup = Path('soulfra_test.db.backup')
        print(f"⚠️  Test database already exists")
        print(f"   Backing up to: {backup}")
        shutil.copy2(test_db, backup)
        print()

    # Copy production → test
    print("📋 Copying soulfra.db → soulfra_test.db...")
    shutil.copy2(prod_db, test_db)

    test_size = test_db.stat().st_size
    test_size_kb = test_size / 1024

    print(f"✅ Test database created: {test_size_kb:.1f} KB")
    print()

    # Verify database integrity
    print("🔍 Verifying test database...")
    import sqlite3
    try:
        conn = sqlite3.connect(test_db)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        conn.close()

        table_count = len(tables)
        print(f"✅ {table_count} tables found in test database")
        print()

    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

    print("=" * 70)
    print("✅ SANDBOX CREATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run sandbox: python3 test_bootstrap.py")
    print("  2. Open: http://localhost:5002")
    print("  3. Go to: /admin/automation")
    print("  4. Test bootstrap and ML training")
    print()

    return True


def reset_sandbox():
    """Reset sandbox to match production again"""
    print("🔄 Resetting sandbox to match production...")
    print()

    # Remove test database
    test_db = Path('soulfra_test.db')
    if test_db.exists():
        test_db.unlink()
        print("🗑️  Removed old test database")

    # Recreate from production
    return create_sandbox()


def run_sandbox_server():
    """Run Flask server on port 5002 with test database"""
    print("=" * 70)
    print("🧪 Soulfra Sandbox Test Server")
    print("=" * 70)
    print()

    # Check if test database exists
    test_db = Path('soulfra_test.db')
    if not test_db.exists():
        print("❌ Test database not found!")
        print()
        print("Create sandbox first:")
        print("  python3 test_bootstrap.py create-sandbox")
        print()
        return

    test_size_kb = test_db.stat().st_size / 1024
    print(f"📦 Using test database: {test_size_kb:.1f} KB")
    print()

    # Set environment variable to use test database
    os.environ['SOULFRA_DB'] = 'soulfra_test.db'

    print("🔧 Configuration:")
    print(f"   Database: soulfra_test.db (SANDBOX)")
    print(f"   Port: 5002 (NOT production)")
    print(f"   Production: http://localhost:5001 (unchanged)")
    print()

    print("=" * 70)
    print("🚀 Starting Sandbox Server...")
    print("=" * 70)
    print()
    print("📍 Sandbox URL: http://localhost:5002")
    print("📍 Production URL: http://localhost:5001 (still safe!)")
    print()
    print("⚠️  ALL CHANGES HAPPEN IN SANDBOX ONLY")
    print("   Production database is NOT touched")
    print()

    # Import Flask app
    from app import app

    # Run on port 5002
    app.run(debug=True, port=5002)


def show_status():
    """Show status of production vs sandbox databases"""
    print("=" * 70)
    print("📊 Database Status")
    print("=" * 70)
    print()

    prod_db = Path('soulfra.db')
    test_db = Path('soulfra_test.db')

    # Production database
    if prod_db.exists():
        prod_size_kb = prod_db.stat().st_size / 1024
        print(f"✅ Production (port 5001): soulfra.db ({prod_size_kb:.1f} KB)")

        # Count brands
        import sqlite3
        conn = sqlite3.connect(prod_db)
        prod_brands = conn.execute('SELECT COUNT(*) FROM brands').fetchone()[0]
        prod_ml_models = conn.execute('SELECT COUNT(*) FROM ml_models').fetchone()[0]
        conn.close()

        print(f"   Brands: {prod_brands}")
        print(f"   ML models: {prod_ml_models}")
    else:
        print("❌ Production database not found")

    print()

    # Test database
    if test_db.exists():
        test_size_kb = test_db.stat().st_size / 1024
        print(f"✅ Sandbox (port 5002): soulfra_test.db ({test_size_kb:.1f} KB)")

        # Count brands
        import sqlite3
        conn = sqlite3.connect(test_db)
        test_brands = conn.execute('SELECT COUNT(*) FROM brands').fetchone()[0]
        test_ml_models = conn.execute('SELECT COUNT(*) FROM ml_models').fetchone()[0]
        conn.close()

        print(f"   Brands: {test_brands}")
        print(f"   ML models: {test_ml_models}")
    else:
        print("⚠️  Sandbox database not created yet")
        print("   Run: python3 test_bootstrap.py create-sandbox")

    print()


def main():
    """CLI interface"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'create-sandbox':
            create_sandbox()
        elif command == 'reset':
            reset_sandbox()
        elif command == 'status':
            show_status()
        else:
            print(f"Unknown command: {command}")
            print()
            print("Usage:")
            print("  python3 test_bootstrap.py create-sandbox")
            print("  python3 test_bootstrap.py                # Run server")
            print("  python3 test_bootstrap.py reset")
            print("  python3 test_bootstrap.py status")
    else:
        # Default: run server
        run_sandbox_server()


if __name__ == '__main__':
    main()

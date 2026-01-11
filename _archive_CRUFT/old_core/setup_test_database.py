#!/usr/bin/env python3
"""
OPTIONAL: Create separate test database for isolated testing
Copies soulfra.db → soulfra-test.db
"""

import shutil
import os
import sqlite3

MAIN_DB = 'soulfra.db'
TEST_DB = 'soulfra-test.db'

def main():
    print("🗄️  Setting up test database...")
    print()

    if not os.path.exists(MAIN_DB):
        print(f"❌ Error: {MAIN_DB} not found")
        return

    if os.path.exists(TEST_DB):
        print(f"⚠️  {TEST_DB} already exists")
        response = input("Overwrite? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled")
            return

    # Copy database
    print(f"📋 Copying {MAIN_DB} → {TEST_DB}...")
    shutil.copy2(MAIN_DB, TEST_DB)

    # Verify copy
    main_size = os.path.getsize(MAIN_DB)
    test_size = os.path.getsize(TEST_DB)

    print(f"✅ Copy complete")
    print(f"  Main DB: {main_size / 1024 / 1024:.1f} MB")
    print(f"  Test DB: {test_size / 1024 / 1024:.1f} MB")
    print()

    # Show contents
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM brands")
    count = cursor.fetchone()[0]
    print(f"📊 Test database contains {count} domains")
    conn.close()

    print()
    print("✅ Test database ready!")
    print()
    print("🔧 To use test database:")
    print("  1. Edit app.py")
    print("  2. Find: DATABASE = 'soulfra.db'")
    print("  3. Change to: DATABASE = 'soulfra-test.db'")
    print("  4. Restart Flask server")
    print()
    print("💡 Or use this command to temporarily use test DB:")
    print("  export DATABASE=soulfra-test.db && python3 app.py")
    print()
    print("🧪 Test workflow:")
    print("  1. Import test domains to soulfra-test.db")
    print("  2. Verify everything works")
    print("  3. Run merge_test_to_main.py to copy to main DB")
    print("  4. Delete soulfra-test.db when done")

if __name__ == '__main__':
    main()

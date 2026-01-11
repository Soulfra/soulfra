#!/usr/bin/env python3
"""
OPTIONAL: Merge successful test domains from soulfra-test.db to soulfra.db
Avoids duplicates, preserves existing data
"""

import sqlite3
import os

MAIN_DB = 'soulfra.db'
TEST_DB = 'soulfra-test.db'

def main():
    print("🔄 Merging test database to main database...")
    print()

    # Verify files exist
    if not os.path.exists(MAIN_DB):
        print(f"❌ Error: {MAIN_DB} not found")
        return

    if not os.path.exists(TEST_DB):
        print(f"❌ Error: {TEST_DB} not found")
        print("💡 Run setup_test_database.py first")
        return

    # Connect to both databases
    main_conn = sqlite3.connect(MAIN_DB)
    test_conn = sqlite3.connect(TEST_DB)

    main_cursor = main_conn.cursor()
    test_cursor = test_conn.cursor()

    # Get counts before
    main_cursor.execute("SELECT COUNT(*) FROM brands")
    main_before = main_cursor.fetchone()[0]

    test_cursor.execute("SELECT COUNT(*) FROM brands")
    test_total = test_cursor.fetchone()[0]

    print("📊 Before merge:")
    print(f"  Main DB: {main_before} domains")
    print(f"  Test DB: {test_total} domains")
    print()

    # Get domains from test DB
    test_cursor.execute("""
        SELECT name, slug, domain, category, tier, emoji, brand_type, tagline,
               target_audience, purpose, created_at
        FROM brands
    """)
    test_domains = test_cursor.fetchall()

    # Get existing domains in main DB
    main_cursor.execute("SELECT domain FROM brands")
    existing_domains = {row[0] for row in main_cursor.fetchall()}

    # Filter out duplicates
    new_domains = [d for d in test_domains if d[2] not in existing_domains]

    print(f"🔍 Found {len(new_domains)} new domains to import")
    print(f"⏭️  Skipping {len(test_domains) - len(new_domains)} duplicates")
    print()

    if len(new_domains) == 0:
        print("✅ Nothing to merge!")
        main_conn.close()
        test_conn.close()
        return

    # Show sample
    print("📋 Sample domains to import:")
    for domain_data in new_domains[:5]:
        domain = domain_data[2]
        category = domain_data[3]
        emoji = domain_data[5] or '🌐'
        print(f"  {emoji} {domain} ({category})")
    if len(new_domains) > 5:
        print(f"  ... and {len(new_domains) - 5} more")
    print()

    # Confirm import
    response = input(f"Import {len(new_domains)} domains to main database? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        main_conn.close()
        test_conn.close()
        return

    print()
    print("📥 Importing domains...")

    # Import each domain
    imported = 0
    for domain_data in new_domains:
        try:
            main_cursor.execute("""
                INSERT INTO brands (name, slug, domain, category, tier, emoji, brand_type, tagline,
                                   target_audience, purpose, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, domain_data)
            imported += 1
        except sqlite3.IntegrityError as e:
            print(f"⚠️  Skipping {domain_data[2]}: {e}")

    main_conn.commit()

    print(f"✅ Imported {imported} domains")
    print()

    # Get counts after
    main_cursor.execute("SELECT COUNT(*) FROM brands")
    main_after = main_cursor.fetchone()[0]

    print("📊 After merge:")
    print(f"  Main DB: {main_after} domains (+{main_after - main_before})")
    print()

    # Clean up
    main_conn.close()
    test_conn.close()

    print("🎉 Merge complete!")
    print()
    print("💡 Next steps:")
    print("  1. Verify domains in main database:")
    print("     Visit http://localhost:5001/admin/domains")
    print()
    print("  2. Delete test database when done:")
    print(f"     rm {TEST_DB}")

if __name__ == '__main__':
    main()

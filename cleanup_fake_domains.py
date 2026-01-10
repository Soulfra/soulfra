#!/usr/bin/env python3
"""
Clean up fake test domains from database
Deletes all domains with category 'test-fake'
Runs VACUUM to reclaim disk space
"""

import sqlite3
import os

DB_FILE = 'soulfra.db'

def get_file_size(filepath):
    """Get file size in human-readable format"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"

def main():
    print("🧹 Cleaning up fake test domains...")
    print()

    if not os.path.exists(DB_FILE):
        print(f"❌ Error: {DB_FILE} not found")
        return

    # Connect to database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get current stats
    print("📊 Before cleanup:")
    size_before = get_file_size(DB_FILE)
    print(f"  Database size: {size_before}")

    cursor.execute("SELECT COUNT(*) FROM brands")
    total_before = cursor.fetchone()[0]
    print(f"  Total domains: {total_before}")

    cursor.execute("SELECT COUNT(*) FROM brands WHERE category = 'test-fake'")
    fake_count = cursor.fetchone()[0]
    print(f"  Fake domains: {fake_count}")
    print()

    if fake_count == 0:
        print("✅ No fake domains to clean up!")
        conn.close()
        return

    # Confirm deletion
    print(f"⚠️  This will delete {fake_count} fake domains")
    response = input("Continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        conn.close()
        return

    print()
    print("🗑️  Deleting fake domains...")

    # Delete fake domains
    cursor.execute("DELETE FROM brands WHERE category = 'test-fake'")
    deleted = cursor.rowcount
    conn.commit()

    print(f"✅ Deleted {deleted} fake domains")
    print()

    # Run VACUUM to reclaim space
    print("💾 Running VACUUM to reclaim disk space...")
    cursor.execute("VACUUM")
    conn.commit()
    conn.close()

    print("✅ VACUUM complete")
    print()

    # Show after stats
    print("📊 After cleanup:")
    size_after = get_file_size(DB_FILE)
    print(f"  Database size: {size_after}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM brands")
    total_after = cursor.fetchone()[0]
    print(f"  Total domains: {total_after}")
    conn.close()

    print()
    print("🎉 Cleanup complete!")
    print()
    print("💡 Your real domains are safe:")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT domain, category FROM brands LIMIT 10")
    domains = cursor.fetchall()

    if domains:
        print("  Real domains still in database:")
        for domain, category in domains:
            print(f"    - {domain} ({category})")
    conn.close()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Database Audit Script

Checks which tables in soulfra.db actually have data.
Generates report of used vs unused tables.
"""

import sqlite3
import os

def audit_database():
    """Audit all tables in soulfra.db"""

    if not os.path.exists('soulfra.db'):
        print("❌ soulfra.db not found")
        return

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get all tables
    tables = cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE 'idx_%'
        ORDER BY name
    """).fetchall()

    print(f"📊 Auditing soulfra.db...")
    print(f"Total tables: {len(tables)}")
    print("")

    used_tables = []
    empty_tables = []

    for (table_name,) in tables:
        try:
            count = cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]

            if count > 0:
                used_tables.append((table_name, count))
            else:
                empty_tables.append(table_name)

        except Exception as e:
            print(f"⚠️  Error checking {table_name}: {e}")

    # Sort by row count
    used_tables.sort(key=lambda x: x[1], reverse=True)

    print("=" * 80)
    print("TABLES WITH DATA")
    print("=" * 80)
    print(f"\nTotal: {len(used_tables)} tables\n")

    for table_name, count in used_tables:
        print(f"  {table_name:50} {count:>10} rows")

    print("\n")
    print("=" * 80)
    print("EMPTY TABLES (Candidates for Removal)")
    print("=" * 80)
    print(f"\nTotal: {len(empty_tables)} tables\n")

    # Group empty tables by prefix
    groups = {}
    for table in empty_tables:
        prefix = table.split('_')[0] if '_' in table else 'other'
        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append(table)

    for prefix in sorted(groups.keys()):
        print(f"\n{prefix.upper()} tables ({len(groups[prefix])}):")
        for table in sorted(groups[prefix]):
            print(f"  - {table}")

    print("\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tables with data:    {len(used_tables)}")
    print(f"Empty tables:        {len(empty_tables)}")
    print(f"Total tables:        {len(tables)}")
    print(f"Unused percentage:   {len(empty_tables)/len(tables)*100:.1f}%")

    # Calculate database size
    db_size = os.path.getsize('soulfra.db')
    print(f"Database size:       {db_size / 1024 / 1024:.2f} MB")

    conn.close()

    # Save report
    with open('DATABASE_AUDIT_REPORT.txt', 'w') as f:
        f.write("DATABASE AUDIT REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total tables: {len(tables)}\n")
        f.write(f"Used tables: {len(used_tables)}\n")
        f.write(f"Empty tables: {len(empty_tables)}\n\n")

        f.write("TABLES WITH DATA:\n")
        f.write("-" * 80 + "\n")
        for table_name, count in used_tables:
            f.write(f"{table_name:50} {count:>10} rows\n")

        f.write("\n\nEMPTY TABLES:\n")
        f.write("-" * 80 + "\n")
        for table in sorted(empty_tables):
            f.write(f"{table}\n")

    print("\n✅ Report saved to DATABASE_AUDIT_REPORT.txt")


if __name__ == '__main__':
    audit_database()

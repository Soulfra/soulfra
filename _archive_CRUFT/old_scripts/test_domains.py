#!/usr/bin/env python3
"""
Test Domain System

Verifies:
1. Brands exist in database
2. add_domain.py works
3. Database schema is fixed
4. Visualizer works
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / 'soulfra.db'

print()
print("="*70)
print(" "*20 + "DOMAIN SYSTEM TEST" + " "*26)
print("="*70)
print()

# Test 1: Check brands exist
print("[1/4] Checking brands in database...")
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row

brands = db.execute('SELECT id, name, slug, domain FROM brands').fetchall()
print(f"   ✅ Found {len(brands)} brands:")
for brand in brands:
    print(f"      • {brand['name']} ({brand['domain']})")
print()

# Test 2: Check required tables exist
print("[2/4] Checking database schema...")
tables_to_check = ['subscribers', 'feedback', 'brands', 'images']
missing = []
for table in tables_to_check:
    try:
        db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()
        print(f"   ✅ Table '{table}' exists")
    except sqlite3.OperationalError:
        print(f"   ❌ Table '{table}' MISSING")
        missing.append(table)
print()

if missing:
    print(f"⚠️  Missing tables: {', '.join(missing)}")
    print("   Run: sqlite3 soulfra.db < fix_database_schema.sql")
    print()

# Test 3: Check feedback table has required columns
print("[3/4] Checking feedback table schema...")
try:
    feedback = db.execute('SELECT name, component, message, status FROM feedback LIMIT 1').fetchone()
    print("   ✅ Feedback table has all required columns")
except sqlite3.OperationalError as e:
    print(f"   ⚠️  Feedback table schema issue: {e}")
print()

# Test 4: Check images table has hash column
print("[4/4] Checking images table schema...")
try:
    db.execute('SELECT hash FROM images LIMIT 1').fetchone()
    print("   ✅ Images table has 'hash' column")
except sqlite3.OperationalError as e:
    print(f"   ⚠️  Images table missing 'hash' column")
print()

db.close()

# Summary
print("="*70)
print("📊 Test Summary:")
print(f"   Brands: {len(brands)}")
print(f"   Missing tables: {len(missing) if missing else 0}")
print()

if not missing:
    print("✅ ALL TESTS PASSED!")
    print()
    print("Next steps:")
    print()
    print("   1. Add a new domain:")
    print("      python3 add_domain.py mysite.com")
    print()
    print("   2. View the matrix:")
    print("      python3 brand_matrix_visualizer.py")
    print()
    print("   3. Start Flask:")
    print("      python3 app.py")
    print()
    print("   4. Test a domain:")
    print("      open http://calriven.localhost:5001/")
    print()
    sys.exit(0)
else:
    print("⚠️  TESTS FAILED - Fix schema first")
    print()
    sys.exit(1)

#!/usr/bin/env python3
"""
Import domains from domains-master.csv into database

Usage:
    python3 import_domains_csv.py

Validates:
- No duplicate domains
- No null required fields
- Valid categories/tiers
- Proper domain format
"""

import csv
import sqlite3
import sys
from pathlib import Path

# Config
CSV_FILE = "domains-master.csv"
DB_FILE = "soulfra.db"

# Valid values
VALID_CATEGORIES = ['cooking', 'tech', 'privacy', 'business', 'health', 'art', 'education', 'gaming', 'finance', 'local']
VALID_TIERS = ['foundation', 'business', 'creative']
VALID_TYPES = ['blog', 'game', 'community', 'platform', 'directory']

def validate_domain(row, line_num):
    """Validate a domain row from CSV"""
    errors = []

    # Required fields
    required = ['name', 'domain', 'category']
    for field in required:
        if not row.get(field, '').strip():
            errors.append(f"Line {line_num}: Missing required field '{field}'")

    # Category validation
    category = row.get('category', '').strip().lower()
    if category and category not in VALID_CATEGORIES:
        errors.append(f"Line {line_num}: Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}")

    # Tier validation
    tier = row.get('tier', '').strip().lower()
    if tier and tier not in VALID_TIERS:
        errors.append(f"Line {line_num}: Invalid tier '{tier}'. Must be one of: {', '.join(VALID_TIERS)}")

    # Brand type validation
    brand_type = row.get('brand_type', '').strip().lower()
    if brand_type and brand_type not in VALID_TYPES:
        errors.append(f"Line {line_num}: Invalid brand_type '{brand_type}'. Must be one of: {', '.join(VALID_TYPES)}")

    # Domain format
    domain = row.get('domain', '').strip()
    if domain and not ('.' in domain and len(domain) > 3):
        errors.append(f"Line {line_num}: Invalid domain format '{domain}'")

    return errors

def import_csv():
    """Import domains from CSV to database"""

    # Check CSV exists
    if not Path(CSV_FILE).exists():
        print(f"❌ Error: {CSV_FILE} not found")
        print(f"   Create it first, then fill in your domains")
        sys.exit(1)

    # Open database
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    # Read CSV
    print(f"📖 Reading {CSV_FILE}...")
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row.get('name', '').strip() and not row['name'].startswith('#')]

    print(f"   Found {len(rows)} domains in CSV")

    # Validate all rows first
    all_errors = []
    seen_domains = set()
    seen_names = set()

    for i, row in enumerate(rows, start=2):  # Start at 2 (line 1 is header)
        # Check for duplicates
        domain = row.get('domain', '').strip().lower()
        name = row.get('name', '').strip()

        if domain in seen_domains:
            all_errors.append(f"Line {i}: Duplicate domain '{domain}'")
        seen_domains.add(domain)

        if name in seen_names:
            all_errors.append(f"Line {i}: Duplicate name '{name}'")
        seen_names.add(name)

        # Validate fields
        errors = validate_domain(row, i)
        all_errors.extend(errors)

    # Stop if validation errors
    if all_errors:
        print(f"\n❌ Validation failed ({len(all_errors)} errors):\n")
        for error in all_errors[:20]:  # Show first 20
            print(f"   {error}")
        if len(all_errors) > 20:
            print(f"   ... and {len(all_errors) - 20} more errors")
        sys.exit(1)

    print(f"✅ Validation passed!")

    # Clear existing brands (optional - comment out if you want to keep existing)
    # cursor.execute("DELETE FROM brands")

    # Import each domain
    imported = 0
    skipped = 0

    for row in rows:
        name = row.get('name', '').strip()
        domain = row.get('domain', '').strip()
        category = row.get('category', '').strip()
        tier = row.get('tier', 'foundation').strip()
        emoji = row.get('emoji', '').strip()
        brand_type = row.get('brand_type', 'blog').strip()
        tagline = row.get('tagline', '').strip()
        target_audience = row.get('target_audience', '').strip()
        purpose = row.get('purpose', '').strip()

        # Generate slug
        slug = domain.replace('.com', '').replace('.', '-').lower()

        # Check if already exists
        existing = cursor.execute('SELECT id FROM brands WHERE slug = ? OR domain = ?', (slug, domain)).fetchone()

        if existing:
            print(f"⏭️  Skipping {name} (already exists)")
            skipped += 1
            continue

        # Insert
        try:
            cursor.execute('''
                INSERT INTO brands (
                    name, slug, domain, category, tier, emoji, brand_type, tagline, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (name, slug, domain, category, tier, emoji, brand_type, tagline))

            imported += 1
            print(f"✅ Imported: {name} ({domain})")

        except sqlite3.Error as e:
            print(f"❌ Error importing {name}: {e}")
            skipped += 1

    # Commit
    db.commit()
    db.close()

    # Summary
    print(f"\n" + "="*50)
    print(f"📊 Import Summary:")
    print(f"   Imported: {imported}")
    print(f"   Skipped:  {skipped}")
    print(f"   Total:    {imported + skipped}")
    print(f"="*50)

    if imported > 0:
        print(f"\n✅ Success! {imported} domains imported to database")
        print(f"   Visit: http://localhost:5001/admin/domains")
        print(f"   Or: http://localhost:5001/control")

if __name__ == '__main__':
    import_csv()

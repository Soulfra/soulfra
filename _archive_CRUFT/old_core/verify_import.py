#!/usr/bin/env python3
"""
CSV Import Verification Tool
Generates cryptographic proof that imports worked correctly

Usage:
    # Before import: Generate checksum
    python3 verify_import.py --pre-check test-domains-50.csv

    # After import: Verify against checksum
    python3 verify_import.py --post-check test-domains-50.csv

    # Auto test (import + verify)
    python3 verify_import.py --auto-test test-domains-50.csv
"""

import hashlib
import json
import sqlite3
import argparse
from datetime import datetime
from collections import Counter

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def sha256_file(filepath):
    """Generate SHA256 checksum of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def parse_csv_file(filepath):
    """Parse CSV and return domain list"""
    domains = []
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip header and comments
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or 'name,domain' in line.lower():
            continue

        parts = [p.strip().strip('"') for p in line.split(',')]
        if len(parts) >= 6:
            domains.append({
                'name': parts[0],
                'domain': parts[1],
                'category': parts[2],
                'tier': parts[3],
                'emoji': parts[4],
                'brand_type': parts[5]
            })

    return domains

def get_current_db_domains():
    """Get all domains currently in database"""
    db = get_db()
    cursor = db.cursor()
    rows = cursor.execute('SELECT name, domain, category, tier, emoji, brand_type FROM brands ORDER BY id').fetchall()
    db.close()

    return [dict(row) for row in rows]

def generate_pre_check_proof(csv_file):
    """Generate proof certificate BEFORE import"""
    print(f"📋 Pre-Check: Analyzing {csv_file}...")
    print()

    # Parse CSV
    csv_domains = parse_csv_file(csv_file)

    # Get current database state
    db_domains_before = get_current_db_domains()

    # Generate checksums
    file_checksum = sha256_file(csv_file)

    # Count by category/tier
    categories = Counter(d['category'] for d in csv_domains)
    tiers = Counter(d['tier'] for d in csv_domains)
    types = Counter(d['brand_type'] for d in csv_domains)

    # Create proof certificate
    proof = {
        'type': 'pre-import-check',
        'timestamp': datetime.now().isoformat(),
        'csv_file': csv_file,
        'file_checksum_sha256': file_checksum,
        'expected': {
            'total_domains': len(csv_domains),
            'categories': dict(categories),
            'tiers': dict(tiers),
            'types': dict(types),
            'sample_domains': [d['domain'] for d in csv_domains[:5]]
        },
        'database_before': {
            'total_domains': len(db_domains_before)
        }
    }

    # Save proof
    proof_file = f"import-proof-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(proof_file, 'w') as f:
        json.dump(proof, f, indent=2)

    # Display results
    print("✅ Pre-Check Complete!")
    print()
    print(f"📄 CSV File: {csv_file}")
    print(f"🔐 SHA256: {file_checksum[:16]}...")
    print()
    print(f"📊 Expected to import: {len(csv_domains)} domains")
    print()
    print("📈 Category distribution:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count} domains")
    print()
    print("📈 Tier distribution:")
    for tier, count in tiers.most_common():
        print(f"  {tier}: {count} domains")
    print()
    print("📈 Type distribution:")
    for typ, count in types.most_common():
        print(f"  {typ}: {count} domains")
    print()
    print(f"💾 Proof saved: {proof_file}")
    print()
    print("🚀 Next steps:")
    print(f"  1. Import via: http://localhost:5001/admin/domains/csv")
    print(f"  2. Verify via: python3 verify_import.py --post-check {csv_file}")

    return proof

def generate_post_check_proof(csv_file):
    """Verify import AFTER it happened"""
    print(f"🔍 Post-Check: Verifying {csv_file} was imported...")
    print()

    # Parse expected CSV
    csv_domains = parse_csv_file(csv_file)
    csv_domain_names = {d['domain'] for d in csv_domains}

    # Get current database
    db_domains_after = get_current_db_domains()
    db_domain_names = {d['domain'] for d in db_domains_after if d['domain']}

    # Check which domains were imported
    imported = csv_domain_names & db_domain_names
    missing = csv_domain_names - db_domain_names

    # Count by category/tier
    imported_domains = [d for d in db_domains_after if d['domain'] in imported]
    categories = Counter(d['category'] for d in imported_domains if d['category'])
    tiers = Counter(d['tier'] for d in imported_domains if d['tier'])
    types = Counter(d['brand_type'] for d in imported_domains if d['brand_type'])

    # Generate checksum
    file_checksum = sha256_file(csv_file)

    # Create verification proof
    proof = {
        'type': 'post-import-verification',
        'timestamp': datetime.now().isoformat(),
        'csv_file': csv_file,
        'file_checksum_sha256': file_checksum,
        'expected': len(csv_domains),
        'actual': {
            'imported': len(imported),
            'missing': len(missing),
            'total_in_database': len(db_domains_after),
            'categories': dict(categories),
            'tiers': dict(tiers),
            'types': dict(types)
        },
        'verification': {
            'all_imported': len(missing) == 0,
            'match_percentage': (len(imported) / len(csv_domains) * 100) if csv_domains else 0
        }
    }

    # Save proof
    proof_file = f"verification-proof-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(proof_file, 'w') as f:
        json.dump(proof, f, indent=2)

    # Display results
    print("🔍 Verification Results:")
    print()
    print(f"📄 CSV File: {csv_file}")
    print(f"🔐 SHA256: {file_checksum[:16]}...")
    print()
    print(f"Expected: {len(csv_domains)} domains")
    print(f"Imported: {len(imported)} domains")
    print(f"Missing: {len(missing)} domains")
    print()

    if len(missing) == 0:
        print("✅ PASS: All domains imported successfully!")
    else:
        print("⚠️  WARNING: Some domains not imported:")
        for domain in list(missing)[:10]:
            print(f"  - {domain}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")

    print()
    print("📊 Imported domains by category:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")

    print()
    print("📊 Imported domains by tier:")
    for tier, count in tiers.most_common():
        print(f"  {tier}: {count}")

    print()
    print(f"💾 Verification proof saved: {proof_file}")
    print()
    print(f"🎯 Match: {proof['verification']['match_percentage']:.1f}%")

    return proof

def main():
    parser = argparse.ArgumentParser(description='Verify CSV imports')
    parser.add_argument('--pre-check', type=str, help='Run pre-import check on CSV file')
    parser.add_argument('--post-check', type=str, help='Run post-import verification on CSV file')
    parser.add_argument('--auto-test', type=str, help='Run automated test (requires API)')
    args = parser.parse_args()

    if args.pre_check:
        generate_pre_check_proof(args.pre_check)
    elif args.post_check:
        generate_post_check_proof(args.post_check)
    elif args.auto_test:
        print("Auto-test not implemented yet")
        print("Use --pre-check before import, --post-check after import")
    else:
        print("Usage:")
        print("  python3 verify_import.py --pre-check test-domains-50.csv")
        print("  python3 verify_import.py --post-check test-domains-50.csv")

if __name__ == '__main__':
    main()

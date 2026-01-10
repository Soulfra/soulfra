#!/usr/bin/env python3
"""
Domain Manager - CSV-based multi-domain management for Soulfra brands

Features:
- Import/export domains from CSV
- Track domain status (active, planned, parked)
- Link domains to brands
- DNS configuration tracking
- Generate CNAME/DNS records

Usage:
    python3 domain_manager.py list                # List all domains
    python3 domain_manager.py add <domain>        # Add new domain
    python3 domain_manager.py export              # Export to CSV
    python3 domain_manager.py import domains.csv  # Import from CSV
"""

import csv
import sys
from database import get_db
from datetime import datetime, timezone


def init_domains_table():
    """
    Initialize domains table in database
    """
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            brand_id INTEGER,
            status TEXT DEFAULT 'planned',
            dns_configured INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')

    db.commit()
    print("✅ Domains table initialized")


def import_domains_csv(csv_path='domains.csv'):
    """
    Import domains from CSV file to database

    Args:
        csv_path (str): Path to CSV file

    Returns:
        int: Number of domains imported
    """
    db = get_db()
    imported_count = 0

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            domain = row['domain']
            brand_id = int(row['brand_id']) if row['brand_id'] else None
            status = row['status'] or 'planned'
            dns_configured = 1 if row['dns_configured'].lower() == 'yes' else 0
            notes = row.get('notes', '')

            created_at = datetime.now(timezone.utc).isoformat()

            try:
                db.execute('''
                    INSERT INTO domains (domain, brand_id, status, dns_configured, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(domain) DO UPDATE SET
                        brand_id = excluded.brand_id,
                        status = excluded.status,
                        dns_configured = excluded.dns_configured,
                        notes = excluded.notes,
                        updated_at = ?
                ''', (domain, brand_id, status, dns_configured, notes, created_at, created_at))

                imported_count += 1
                print(f"✅ Imported: {domain} → brand_id={brand_id}, status={status}")

            except Exception as e:
                print(f"❌ Failed to import {domain}: {e}")

    db.commit()
    print(f"\n✅ Imported {imported_count} domains from {csv_path}")

    return imported_count


def export_domains_csv(csv_path='domains_export.csv'):
    """
    Export domains from database to CSV file

    Args:
        csv_path (str): Output CSV path

    Returns:
        int: Number of domains exported
    """
    db = get_db()

    domains = db.execute('''
        SELECT domain, brand_id, status, dns_configured, notes
        FROM domains
        ORDER BY brand_id, domain
    ''').fetchall()

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['domain', 'brand_id', 'status', 'dns_configured', 'notes'])

        for domain in domains:
            dns_configured = 'yes' if domain['dns_configured'] else 'no'
            writer.writerow([
                domain['domain'],
                domain['brand_id'] or '',
                domain['status'],
                dns_configured,
                domain['notes'] or ''
            ])

    print(f"✅ Exported {len(domains)} domains to {csv_path}")
    return len(domains)


def list_domains():
    """
    List all domains with their brand assignments

    Returns:
        None (prints to console)
    """
    db = get_db()

    domains = db.execute('''
        SELECT d.*, b.name as brand_name, b.slug as brand_slug
        FROM domains d
        LEFT JOIN brands b ON d.brand_id = b.id
        ORDER BY d.status, d.brand_id, d.domain
    ''').fetchall()

    if not domains:
        print("No domains found in database")
        return

    print(f"\n{'='*80}")
    print(f"{'DOMAIN':<40} {'BRAND':<20} {'STATUS':<12} {'DNS':<8}")
    print(f"{'='*80}")

    for domain in domains:
        brand_name = domain['brand_name'] or '(no brand)'
        dns_status = '✅' if domain['dns_configured'] else '❌'

        print(f"{domain['domain']:<40} {brand_name:<20} {domain['status']:<12} {dns_status:<8}")

        if domain['notes']:
            print(f"  └─ Note: {domain['notes']}")

    print(f"{'='*80}")
    print(f"Total: {len(domains)} domains\n")


def add_domain(domain, brand_id=None, status='planned', dns_configured=False, notes=''):
    """
    Add a new domain to the database

    Args:
        domain (str): Domain name (e.g., 'calriven.com')
        brand_id (int): Brand ID (optional)
        status (str): Domain status (active, planned, parked)
        dns_configured (bool): Whether DNS is configured
        notes (str): Optional notes

    Returns:
        int: Domain ID
    """
    db = get_db()

    created_at = datetime.now(timezone.utc).isoformat()

    cursor = db.execute('''
        INSERT INTO domains (domain, brand_id, status, dns_configured, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (domain, brand_id, status, 1 if dns_configured else 0, notes, created_at))

    domain_id = cursor.lastrowid
    db.commit()

    print(f"✅ Added domain: {domain} (ID: {domain_id})")
    return domain_id


def generate_dns_records():
    """
    Generate DNS configuration for all active domains

    Returns:
        None (prints to console)
    """
    db = get_db()

    domains = db.execute('''
        SELECT d.*, b.name as brand_name, b.slug as brand_slug
        FROM domains d
        JOIN brands b ON d.brand_id = b.id
        WHERE d.status = 'active'
        ORDER BY d.domain
    ''').fetchall()

    print(f"\n{'='*80}")
    print(f"DNS CONFIGURATION FOR ACTIVE DOMAINS")
    print(f"{'='*80}\n")

    for domain in domains:
        print(f"Domain: {domain['domain']}")
        print(f"Brand: {domain['brand_name']} ({domain['brand_slug']})")
        print(f"\nDNS Records:")

        if domain['domain'].endswith('.github.io'):
            # GitHub Pages subdirectory
            print(f"  Type: GitHub Pages")
            print(f"  No DNS needed - served via soulfra.github.io/{domain['brand_slug']}")
        else:
            # Custom domain
            print(f"  Type: CNAME")
            print(f"  Name: {domain['domain']}")
            print(f"  Value: soulfra.github.io")
            print(f"\n  (Add this CNAME record to your DNS provider)")

        print(f"\n{'-'*80}\n")


if __name__ == '__main__':
    """
    CLI usage
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 domain_manager.py init                    # Initialize table")
        print("  python3 domain_manager.py list                    # List all domains")
        print("  python3 domain_manager.py import domains.csv      # Import from CSV")
        print("  python3 domain_manager.py export domains_out.csv  # Export to CSV")
        print("  python3 domain_manager.py add <domain>            # Add new domain")
        print("  python3 domain_manager.py dns                     # Show DNS config")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_domains_table()

    elif command == "list":
        list_domains()

    elif command == "import":
        csv_path = sys.argv[2] if len(sys.argv) > 2 else 'domains.csv'
        import_domains_csv(csv_path)

    elif command == "export":
        csv_path = sys.argv[2] if len(sys.argv) > 2 else 'domains_export.csv'
        export_domains_csv(csv_path)

    elif command == "add":
        if len(sys.argv) < 3:
            print("Usage: python3 domain_manager.py add <domain> [brand_id] [status]")
            sys.exit(1)

        domain = sys.argv[2]
        brand_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
        status = sys.argv[4] if len(sys.argv) > 4 else 'planned'

        add_domain(domain, brand_id=brand_id, status=status)

    elif command == "dns":
        generate_dns_records()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

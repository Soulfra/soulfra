#!/usr/bin/env python3
"""
Subscriber Management System - One database, all platforms

Usage:
    python3 manage_subscribers.py migrate          # Upgrade database schema
    python3 manage_subscribers.py add --email test@example.com --brand soulfra
    python3 manage_subscribers.py add --phone +12345678901 --brand soulfra
    python3 manage_subscribers.py list             # List all subscribers
    python3 manage_subscribers.py list --brand soulfra
    python3 manage_subscribers.py export           # Export to CSV
    python3 manage_subscribers.py import subs.csv  # Import from CSV
    python3 manage_subscribers.py sync             # Sync with external platforms
"""

import sqlite3
import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'soulfra.db'


def migrate_database():
    """Upgrade subscribers table to support all platforms"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if migration is needed
    cursor.execute("PRAGMA table_info(subscribers)")
    columns = [col[1] for col in cursor.fetchall()]

    migrations = []

    if 'brand_id' not in columns:
        migrations.append("ALTER TABLE subscribers ADD COLUMN brand_id INTEGER REFERENCES brands(id)")

    if 'phone' not in columns:
        migrations.append("ALTER TABLE subscribers ADD COLUMN phone TEXT")

    if 'signal_number' not in columns:
        migrations.append("ALTER TABLE subscribers ADD COLUMN signal_number TEXT")

    if 'active' not in columns:
        migrations.append("ALTER TABLE subscribers ADD COLUMN active BOOLEAN DEFAULT 1")

    if 'platforms' not in columns:
        migrations.append("ALTER TABLE subscribers ADD COLUMN platforms TEXT DEFAULT 'email'")

    if 'metadata' not in columns:
        migrations.append("ALTER TABLE subscribers ADD COLUMN metadata TEXT")

    if migrations:
        print(f"🔄 Running {len(migrations)} migrations...")
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"  ✅ {migration[:60]}...")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' not in str(e):
                    print(f"  ⚠️  {e}")

        conn.commit()
        print("✅ Migration complete")
    else:
        print("✅ Database already up to date")

    conn.close()


def add_subscriber(email=None, phone=None, signal=None, brand=None, platforms=None):
    """Add a new subscriber"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get brand_id if brand name provided
    brand_id = None
    if brand:
        cursor.execute("SELECT id FROM brands WHERE name = ?", (brand,))
        result = cursor.fetchone()
        if result:
            brand_id = result[0]
        else:
            print(f"❌ Brand '{brand}' not found")
            conn.close()
            return False

    # Default platforms
    if not platforms:
        platforms_list = []
        if email:
            platforms_list.append('email')
        if phone:
            platforms_list.append('whatsapp')
        if signal:
            platforms_list.append('signal')
        platforms = ','.join(platforms_list)

    try:
        cursor.execute('''
            INSERT INTO subscribers (email, phone, signal_number, brand_id, platforms, active, confirmed)
            VALUES (?, ?, ?, ?, ?, 1, 1)
        ''', (email, phone, signal, brand_id, platforms))

        conn.commit()
        sub_id = cursor.lastrowid

        print(f"✅ Added subscriber #{sub_id}")
        if email:
            print(f"   Email: {email}")
        if phone:
            print(f"   Phone: {phone}")
        if signal:
            print(f"   Signal: {signal}")
        if brand:
            print(f"   Brand: {brand}")
        print(f"   Platforms: {platforms}")

        conn.close()
        return True

    except sqlite3.IntegrityError as e:
        print(f"❌ Error: {e}")
        conn.close()
        return False


def list_subscribers(brand=None, platform=None):
    """List all subscribers"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = '''
        SELECT s.*, b.name as brand_name
        FROM subscribers s
        LEFT JOIN brands b ON s.brand_id = b.id
        WHERE 1=1
    '''
    params = []

    if brand:
        query += " AND b.name = ?"
        params.append(brand)

    if platform:
        query += " AND s.platforms LIKE ?"
        params.append(f'%{platform}%')

    query += " ORDER BY s.id DESC"

    cursor.execute(query, params)
    subscribers = cursor.fetchall()

    if not subscribers:
        print("📭 No subscribers found")
        conn.close()
        return

    print(f"\n📊 {len(subscribers)} subscribers\n")
    print(f"{'ID':<6} {'Email':<30} {'Phone':<15} {'Brand':<15} {'Platforms':<20} {'Active':<8}")
    print("=" * 100)

    for sub in subscribers:
        print(f"{sub['id']:<6} {(sub['email'] or '-'):<30} {(sub['phone'] or '-'):<15} {(sub['brand_name'] or 'All'):<15} {(sub['platforms'] or '-'):<20} {'✅' if sub['active'] else '❌':<8}")

    conn.close()


def export_subscribers(output_file='subscribers.csv'):
    """Export all subscribers to CSV"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.*, b.name as brand_name
        FROM subscribers s
        LEFT JOIN brands b ON s.brand_id = b.id
        ORDER BY s.id
    ''')

    subscribers = cursor.fetchall()

    if not subscribers:
        print("📭 No subscribers to export")
        conn.close()
        return

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'email', 'phone', 'signal_number', 'brand_name', 'platforms', 'active', 'confirmed', 'subscribed_at'
        ])
        writer.writeheader()

        for sub in subscribers:
            writer.writerow({
                'id': sub['id'],
                'email': sub['email'],
                'phone': sub['phone'],
                'signal_number': sub['signal_number'],
                'brand_name': sub['brand_name'] or '',
                'platforms': sub['platforms'] or '',
                'active': sub['active'],
                'confirmed': sub['confirmed'],
                'subscribed_at': sub['subscribed_at']
            })

    print(f"✅ Exported {len(subscribers)} subscribers to {output_file}")
    conn.close()


def import_subscribers(csv_file):
    """Import subscribers from CSV"""
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    imported = 0
    skipped = 0

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Get brand_id
            brand_id = None
            if row.get('brand_name'):
                cursor.execute("SELECT id FROM brands WHERE name = ?", (row['brand_name'],))
                result = cursor.fetchone()
                if result:
                    brand_id = result[0]

            try:
                cursor.execute('''
                    INSERT INTO subscribers (email, phone, signal_number, brand_id, platforms, active, confirmed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('email'),
                    row.get('phone'),
                    row.get('signal_number'),
                    brand_id,
                    row.get('platforms', 'email'),
                    int(row.get('active', 1)),
                    int(row.get('confirmed', 1))
                ))
                imported += 1
            except sqlite3.IntegrityError:
                skipped += 1

    conn.commit()
    conn.close()

    print(f"✅ Imported {imported} subscribers")
    if skipped > 0:
        print(f"⚠️  Skipped {skipped} duplicates")


def sync_with_platforms():
    """Sync subscribers with external platforms (Substack, Medium, etc.)"""
    print("🔄 Syncing subscribers with external platforms...")

    # This would fetch subscribers from:
    # - Substack API
    # - Medium followers API
    # - Existing email lists

    print("⚠️  Platform sync not implemented yet")
    print("   Add your API integrations to pull subscriber lists")


def main():
    parser = argparse.ArgumentParser(description='Manage subscribers across all platforms')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Migrate command
    subparsers.add_parser('migrate', help='Upgrade database schema')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add new subscriber')
    add_parser.add_argument('--email', help='Email address')
    add_parser.add_argument('--phone', help='Phone number (WhatsApp)')
    add_parser.add_argument('--signal', help='Signal number')
    add_parser.add_argument('--brand', help='Brand name')
    add_parser.add_argument('--platforms', help='Comma-separated platforms (email,whatsapp,signal)')

    # List command
    list_parser = subparsers.add_parser('list', help='List subscribers')
    list_parser.add_argument('--brand', help='Filter by brand')
    list_parser.add_argument('--platform', help='Filter by platform')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export to CSV')
    export_parser.add_argument('--output', default='subscribers.csv', help='Output file')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import from CSV')
    import_parser.add_argument('file', help='CSV file to import')

    # Sync command
    subparsers.add_parser('sync', help='Sync with external platforms')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'migrate':
        migrate_database()
    elif args.command == 'add':
        if not args.email and not args.phone and not args.signal:
            print("❌ Must provide at least one contact method (--email, --phone, or --signal)")
            sys.exit(1)
        add_subscriber(
            email=args.email,
            phone=args.phone,
            signal=args.signal,
            brand=args.brand,
            platforms=args.platforms
        )
    elif args.command == 'list':
        list_subscribers(brand=args.brand, platform=args.platform)
    elif args.command == 'export':
        export_subscribers(output_file=args.output)
    elif args.command == 'import':
        import_subscribers(args.file)
    elif args.command == 'sync':
        sync_with_platforms()


if __name__ == '__main__':
    main()

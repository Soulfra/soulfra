#!/usr/bin/env python3
"""
CSV Import/Export for StPetePros

Manage professionals via CSV (like email list management, but for businesses).

Usage:
    python3 csv-manager.py export              # Export database → CSV
    python3 csv-manager.py import professionals.csv   # Import CSV → database
    python3 csv-manager.py sync professionals.csv     # Sync CSV ↔ database ↔ GitHub Pages
"""

import sqlite3
import csv
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'soulfra.db'


def export_to_csv(output_file='professionals.csv'):
    """Export professionals from database to CSV"""

    print()
    print("=" * 60)
    print("  Export Database → CSV")
    print("=" * 60)
    print()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    professionals = db.execute('''
        SELECT
            id,
            business_name,
            category,
            email,
            phone,
            bio,
            website,
            address,
            city,
            zip_code,
            approval_status,
            created_at
        FROM professionals
        ORDER BY business_name
    ''').fetchall()

    db.close()

    if not professionals:
        print("⚠️  No professionals found in database")
        print()
        return

    # Write CSV
    output_path = Path(output_file)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'id',
            'business_name',
            'category',
            'email',
            'phone',
            'bio',
            'website',
            'address',
            'city',
            'zip_code',
            'approval_status',
            'created_at'
        ])

        # Data
        for prof in professionals:
            writer.writerow([
                prof['id'],
                prof['business_name'],
                prof['category'] or '',
                prof['email'] or '',
                prof['phone'] or '',
                prof['bio'] or '',
                prof['website'] or '',
                prof['address'] or '',
                prof['city'] or '',
                prof['zip_code'] or '',
                prof['approval_status'] or 'pending',
                prof['created_at'] or ''
            ])

    print(f"✅ Exported {len(professionals)} professionals to: {output_path}")
    print()
    print("📂 Open in Excel/Numbers/Google Sheets to edit")
    print()


def import_from_csv(csv_file):
    """Import professionals from CSV to database"""

    print()
    print("=" * 60)
    print("  Import CSV → Database")
    print("=" * 60)
    print()

    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"❌ File not found: {csv_file}")
        print()
        return

    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("⚠️  CSV file is empty")
        print()
        return

    print(f"📊 Found {len(rows)} rows in CSV")
    print()

    db = sqlite3.connect(DB_PATH)

    added = 0
    updated = 0
    skipped = 0

    for row in rows:
        # Check if ID exists
        prof_id = row.get('id', '').strip()

        if prof_id:
            # Update existing
            existing = db.execute(
                'SELECT id FROM professionals WHERE id = ?',
                (prof_id,)
            ).fetchone()

            if existing:
                db.execute('''
                    UPDATE professionals
                    SET
                        business_name = ?,
                        category = ?,
                        email = ?,
                        phone = ?,
                        bio = ?,
                        website = ?,
                        address = ?,
                        city = ?,
                        zip_code = ?,
                        approval_status = ?
                    WHERE id = ?
                ''', (
                    row.get('business_name', ''),
                    row.get('category', ''),
                    row.get('email', ''),
                    row.get('phone', ''),
                    row.get('bio', ''),
                    row.get('website', ''),
                    row.get('address', ''),
                    row.get('city', ''),
                    row.get('zip_code', ''),
                    row.get('approval_status', 'pending'),
                    prof_id
                ))
                updated += 1
                print(f"   Updated: {row.get('business_name', 'Unknown')} (ID {prof_id})")
                continue

        # Insert new
        business_name = row.get('business_name', '').strip()
        if not business_name:
            skipped += 1
            print(f"   Skipped: Row missing business_name")
            continue

        try:
            db.execute('''
                INSERT INTO professionals (
                    business_name,
                    category,
                    email,
                    phone,
                    bio,
                    website,
                    address,
                    city,
                    zip_code,
                    approval_status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                business_name,
                row.get('category', ''),
                row.get('email', ''),
                row.get('phone', ''),
                row.get('bio', ''),
                row.get('website', ''),
                row.get('address', ''),
                row.get('city', ''),
                row.get('zip_code', ''),
                row.get('approval_status', 'pending'),
                row.get('created_at', datetime.now().isoformat())
            ))
            added += 1
            print(f"   Added: {business_name}")

        except sqlite3.IntegrityError as e:
            skipped += 1
            print(f"   Skipped: {business_name} (duplicate or error)")

    db.commit()
    db.close()

    print()
    print(f"✅ Import complete!")
    print(f"   Added: {added}")
    print(f"   Updated: {updated}")
    print(f"   Skipped: {skipped}")
    print()


def sync_workflow(csv_file):
    """Full sync: CSV → Database → GitHub Pages"""

    print()
    print("=" * 60)
    print("  Full Sync Workflow")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Import CSV → Database")
    print("  2. Export Database → GitHub Pages HTML")
    print("  3. (You can then git push)")
    print()

    confirm = input("Continue? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        print()
        return

    # Step 1: Import CSV
    import_from_csv(csv_file)

    # Step 2: Export to GitHub Pages
    print()
    print("=" * 60)
    print("  Exporting to GitHub Pages...")
    print("=" * 60)
    print()

    import subprocess
    export_script = Path(__file__).parent / 'export-to-github-pages.py'

    if not export_script.exists():
        print("⚠️  export-to-github-pages.py not found")
        print("   Run manually: python3 export-to-github-pages.py")
        print()
        return

    result = subprocess.run(['python3', str(export_script)])

    if result.returncode == 0:
        print()
        print("✅ Full sync complete!")
        print()
        print("Next steps:")
        print("  cd ~/Desktop/soulfra.github.io")
        print("  git add stpetepros/")
        print("  git commit -m 'Update directory from CSV'")
        print("  git push")
        print()
    else:
        print("❌ Export failed")
        print()


def main():
    if len(sys.argv) < 2:
        print()
        print("Usage:")
        print("  python3 csv-manager.py export")
        print("  python3 csv-manager.py import professionals.csv")
        print("  python3 csv-manager.py sync professionals.csv")
        print()
        return

    command = sys.argv[1]

    if command == 'export':
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'professionals.csv'
        export_to_csv(output_file)

    elif command == 'import':
        if len(sys.argv) < 3:
            print()
            print("❌ Please specify CSV file to import")
            print("   python3 csv-manager.py import professionals.csv")
            print()
            return
        import_from_csv(sys.argv[2])

    elif command == 'sync':
        if len(sys.argv) < 3:
            print()
            print("❌ Please specify CSV file to sync")
            print("   python3 csv-manager.py sync professionals.csv")
            print()
            return
        sync_workflow(sys.argv[2])

    else:
        print()
        print(f"❌ Unknown command: {command}")
        print()
        print("Valid commands: export, import, sync")
        print()


if __name__ == '__main__':
    main()

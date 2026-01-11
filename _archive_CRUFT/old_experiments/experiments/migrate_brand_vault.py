#!/usr/bin/env python3
"""
Brand Vault Migration - Add Marketplace Tables

Adds tables for Brand Vault marketplace system:
- brand_licenses: License types (public domain, CC-BY, proprietary, etc.)
- brand_ratings: Star ratings and reviews
- brand_versions: Version control for brand updates

Usage:
    python3 migrate_brand_vault.py

Safe to run multiple times - creates tables only if they don't exist.
"""

from database import get_db
from datetime import datetime


def migrate():
    """Add Brand Vault tables"""
    print("=" * 70)
    print("📦 BRAND VAULT MIGRATION")
    print("=" * 70)
    print()
    print("Adding marketplace tables...")
    print()

    db = get_db()

    # Brand Licenses Table
    print("1. Creating brand_licenses table...")
    db.execute('''
        CREATE TABLE IF NOT EXISTS brand_licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            license_type TEXT NOT NULL,
            -- Types: 'public', 'cc0', 'cc-by', 'licensed', 'proprietary'
            attribution_required BOOLEAN DEFAULT 0,
            commercial_use_allowed BOOLEAN DEFAULT 1,
            modifications_allowed BOOLEAN DEFAULT 1,
            derivative_works_allowed BOOLEAN DEFAULT 1,
            share_alike_required BOOLEAN DEFAULT 0,
            license_text TEXT,
            license_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
        )
    ''')
    print("   ✅ brand_licenses created")

    # Brand Ratings Table
    print("2. Creating brand_ratings table...")
    db.execute('''
        CREATE TABLE IF NOT EXISTS brand_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review TEXT,
            helpful_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(brand_id, user_id)  -- One rating per user per brand
        )
    ''')
    print("   ✅ brand_ratings created")

    # Brand Versions Table
    print("3. Creating brand_versions table...")
    db.execute('''
        CREATE TABLE IF NOT EXISTS brand_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            version_number TEXT NOT NULL,  -- "1.0.0", "1.1.0", etc.
            changelog TEXT,
            zip_path TEXT,  -- Path to version ZIP file
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
            UNIQUE(brand_id, version_number)
        )
    ''')
    print("   ✅ brand_versions created")

    # Brand Downloads Table (track who downloaded what)
    print("4. Creating brand_downloads table...")
    db.execute('''
        CREATE TABLE IF NOT EXISTS brand_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            user_id INTEGER,  -- NULL if anonymous
            version_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (version_id) REFERENCES brand_versions(id) ON DELETE SET NULL
        )
    ''')
    print("   ✅ brand_downloads created")

    # Brand Submissions Table (pending review)
    print("5. Creating brand_submissions table...")
    db.execute('''
        CREATE TABLE IF NOT EXISTS brand_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand_name TEXT NOT NULL,
            brand_slug TEXT NOT NULL,
            description TEXT,
            license_type TEXT NOT NULL,
            zip_path TEXT NOT NULL,  -- Path to submitted ZIP
            status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
            ml_score REAL,  -- 0.0-1.0 quality score from ML
            ml_feedback TEXT,  -- Suggestions from ML review
            admin_notes TEXT,  -- Manual review notes
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,  -- Admin user who reviewed
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    print("   ✅ brand_submissions created")

    # Indexes for performance
    print("6. Creating indexes...")
    db.execute('CREATE INDEX IF NOT EXISTS idx_brand_licenses_brand_id ON brand_licenses(brand_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_brand_ratings_brand_id ON brand_ratings(brand_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_brand_ratings_user_id ON brand_ratings(user_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_brand_versions_brand_id ON brand_versions(brand_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_brand_downloads_brand_id ON brand_downloads(brand_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_brand_submissions_status ON brand_submissions(status)')
    print("   ✅ Indexes created")

    db.commit()
    db.close()

    print()
    print("=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    print("Brand Vault tables added:")
    print("  • brand_licenses - License management")
    print("  • brand_ratings - Star ratings and reviews")
    print("  • brand_versions - Version control")
    print("  • brand_downloads - Download tracking")
    print("  • brand_submissions - Submission queue")
    print()
    print("Next steps:")
    print("  1. Add default licenses: python3 seed_brand_licenses.py")
    print("  2. Test submission: visit /brand/submit")
    print("  3. View marketplace: visit /brands")
    print()


def seed_default_licenses():
    """Add default licenses for existing brands"""
    print("=" * 70)
    print("🌱 SEEDING DEFAULT LICENSES")
    print("=" * 70)
    print()

    db = get_db()

    # Get all brands without licenses
    brands = db.execute('''
        SELECT b.id, b.slug, b.name
        FROM brands b
        LEFT JOIN brand_licenses bl ON b.id = bl.brand_id
        WHERE bl.id IS NULL
    ''').fetchall()

    if not brands:
        print("✅ All brands already have licenses!")
        db.close()
        return

    print(f"Found {len(brands)} brands without licenses")
    print()

    # Add CC0 (public domain) license to all existing brands
    for brand in brands:
        db.execute('''
            INSERT INTO brand_licenses (
                brand_id,
                license_type,
                attribution_required,
                commercial_use_allowed,
                modifications_allowed,
                derivative_works_allowed,
                license_text,
                license_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            brand['id'],
            'cc0',  # CC0 Public Domain
            0,      # No attribution required
            1,      # Commercial use allowed
            1,      # Modifications allowed
            1,      # Derivative works allowed
            'CC0 1.0 Universal - Public Domain Dedication',
            'https://creativecommons.org/publicdomain/zero/1.0/'
        ))

        print(f"✅ {brand['name']} → CC0 Public Domain")

    db.commit()
    db.close()

    print()
    print(f"✅ Added CC0 licenses to {len(brands)} brands!")
    print()


def verify_migration():
    """Verify tables were created successfully"""
    print("=" * 70)
    print("🔍 VERIFYING MIGRATION")
    print("=" * 70)
    print()

    db = get_db()

    tables = [
        'brand_licenses',
        'brand_ratings',
        'brand_versions',
        'brand_downloads',
        'brand_submissions'
    ]

    all_exist = True

    for table in tables:
        try:
            count = db.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()['count']
            print(f"✅ {table}: {count} rows")
        except Exception as e:
            print(f"❌ {table}: ERROR - {e}")
            all_exist = False

    db.close()

    print()
    if all_exist:
        print("✅ All tables verified successfully!")
    else:
        print("⚠️  Some tables missing - run migration again!")
    print()


def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'seed':
            seed_default_licenses()
        elif command == 'verify':
            verify_migration()
        else:
            print(f"Unknown command: {command}")
            print()
            print("Usage:")
            print("  python3 migrate_brand_vault.py         # Run migration")
            print("  python3 migrate_brand_vault.py seed    # Seed default licenses")
            print("  python3 migrate_brand_vault.py verify  # Verify tables exist")
    else:
        migrate()


if __name__ == '__main__':
    main()

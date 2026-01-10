#!/usr/bin/env python3
"""
Add StPetePros tables to database

Creates professional directory tables:
- professionals: Service providers and their business info
- professional_reviews: Customer reviews with QR verification
- loyalty_points: Brand-specific loyalty rewards
- skill_certifications: QR-verified certifications
"""

from database import get_db

def migrate_stpetepros():
    """Add tables for professional services platform"""
    db = get_db()

    print("🔧 Creating StPetePros database tables...")

    # Professionals/Service Providers
    db.execute('''
        CREATE TABLE IF NOT EXISTS professionals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            business_name TEXT NOT NULL,
            category TEXT,  -- 'plumbing', 'electrical', 'hvac', etc.
            subcategory TEXT,  -- More specific categorization
            bio TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            address TEXT,
            city TEXT DEFAULT 'St. Petersburg',
            state TEXT DEFAULT 'FL',
            zip_code TEXT,
            qr_business_card BLOB,  -- QR code for digital business card
            verified BOOLEAN DEFAULT 0,
            rating_avg REAL DEFAULT 0.0,
            review_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Professional Reviews
    db.execute('''
        CREATE TABLE IF NOT EXISTS professional_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professional_id INTEGER NOT NULL,
            reviewer_user_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            qr_verification_code TEXT,  -- QR code scanned to verify service
            service_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id),
            FOREIGN KEY (reviewer_user_id) REFERENCES users(id)
        )
    ''')

    # Loyalty Rewards (shared across brands)
    db.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand_slug TEXT NOT NULL,  -- 'stpetepros', 'soulfra', etc.
            points INTEGER DEFAULT 0,
            points_lifetime INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'bronze',  -- bronze, silver, gold, platinum
            last_activity TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, brand_slug)
        )
    ''')

    # Skill Certifications (QR-based)
    db.execute('''
        CREATE TABLE IF NOT EXISTS skill_certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            professional_id INTEGER,
            skill_name TEXT NOT NULL,
            skill_category TEXT,
            level TEXT,  -- 'beginner', 'intermediate', 'expert'
            qr_certificate BLOB,  -- QR code with verification
            issued_by TEXT,
            verified BOOLEAN DEFAULT 0,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')

    # Create indexes for performance
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_professionals_category
        ON professionals(category)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_professionals_city
        ON professionals(city)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_professionals_verified
        ON professionals(verified)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_professional_reviews_professional
        ON professional_reviews(professional_id)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_loyalty_points_user_brand
        ON loyalty_points(user_id, brand_slug)
    ''')

    db.commit()
    print("✅ StPetePros tables created successfully")

    # Show table counts
    tables = ['professionals', 'professional_reviews', 'loyalty_points', 'skill_certifications']
    for table in tables:
        count = db.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()['count']
        print(f"   {table}: {count} rows")

if __name__ == '__main__':
    migrate_stpetepros()
    print("\n✨ Migration complete! Ready to add professionals to the directory.")

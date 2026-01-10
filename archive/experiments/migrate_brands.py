#!/usr/bin/env python3
"""
Add Brands & Brand Integration Tables

This enables the brand-story-studio integration where brands are stored
in the database with their visual assets and can have associated posts.
"""

from database import get_db

def migrate():
    """Add brands table and brand_id to posts"""
    conn = get_db()

    # Brands table - stores brand identity information
    conn.execute('''
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            colors TEXT,             -- JSON array of hex codes
            personality TEXT,
            brand_values TEXT,       -- JSON array (renamed from 'values' to avoid SQL keyword)
            tone TEXT,
            target_audience TEXT,
            story_theme TEXT,
            config_json TEXT,        -- Complete brand config
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add brand_id column to posts if not exists
    try:
        conn.execute('ALTER TABLE posts ADD COLUMN brand_id INTEGER')
        print("✅ Added brand_id column to posts table")
    except Exception as e:
        if 'duplicate column' in str(e).lower():
            print("⏭️  brand_id column already exists in posts table")
        else:
            raise

    # Create index for brand posts
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_posts_brand_id
        ON posts(brand_id)
    ''')

    # Add is_ai_persona column to users if not exists (for brand users)
    try:
        conn.execute('ALTER TABLE users ADD COLUMN is_ai_persona INTEGER DEFAULT 0')
        print("✅ Added is_ai_persona column to users table")
    except Exception as e:
        if 'duplicate column' in str(e).lower():
            print("⏭️  is_ai_persona column already exists in users table")
        else:
            raise

    conn.commit()
    conn.close()

    print("✅ Brands table created")
    print("✅ Brand integration complete")

if __name__ == '__main__':
    migrate()

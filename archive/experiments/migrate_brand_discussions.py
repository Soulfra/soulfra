#!/usr/bin/env python3
"""
Database Migration - Add Brand Discussion Support

Modifies discussion_sessions table to support both:
- Post discussions (existing feature)
- Brand discussions (new feature for SOP generation)
"""

import sqlite3
from database import get_db

def migrate():
    """Add brand discussion support to database"""
    print("🔄 Migrating database for brand discussions...")

    db = get_db()

    try:
        # Check if brand_name column exists
        cursor = db.execute("PRAGMA table_info(discussion_sessions)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'brand_name' in columns:
            print("✅ Database already migrated (brand_name column exists)")
            db.close()
            return

        # Create new table with updated schema
        db.execute('''
            CREATE TABLE discussion_sessions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                brand_name TEXT,
                user_id INTEGER NOT NULL,
                persona_name TEXT DEFAULT 'calriven',
                status TEXT DEFAULT 'active',
                draft_comment TEXT,
                final_comment_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finalized_at TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (final_comment_id) REFERENCES comments(id),
                CHECK ((post_id IS NOT NULL AND brand_name IS NULL) OR (post_id IS NULL AND brand_name IS NOT NULL))
            )
        ''')

        # Copy existing data
        db.execute('''
            INSERT INTO discussion_sessions_new
            (id, post_id, user_id, persona_name, status, draft_comment, final_comment_id, created_at, finalized_at)
            SELECT id, post_id, user_id, persona_name, status, draft_comment, final_comment_id, created_at, finalized_at
            FROM discussion_sessions
        ''')

        # Drop old table and rename new one
        db.execute('DROP TABLE discussion_sessions')
        db.execute('ALTER TABLE discussion_sessions_new RENAME TO discussion_sessions')

        # Recreate index
        db.execute('CREATE INDEX IF NOT EXISTS idx_discussion_sessions_post_id ON discussion_sessions(post_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_discussion_sessions_brand_name ON discussion_sessions(brand_name)')

        db.commit()
        print("✅ Migration complete!")
        print("   - Made post_id nullable")
        print("   - Added brand_name column")
        print("   - Added CHECK constraint (must have post_id XOR brand_name)")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    migrate()

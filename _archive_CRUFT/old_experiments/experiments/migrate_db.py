#!/usr/bin/env python3
"""
Database Migration Script
Adds ai_processed and source_post_id columns to existing databases
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'soulfra.db')


def migrate():
    """Add new columns if they don't exist"""
    print(f"🔄 Migrating database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"⚠️  Database doesn't exist yet - will be created with new schema")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(posts)")
    columns = [row[1] for row in cursor.fetchall()]

    migrations_needed = []

    if 'ai_processed' not in columns:
        migrations_needed.append('ai_processed')

    if 'source_post_id' not in columns:
        migrations_needed.append('source_post_id')

    if not migrations_needed:
        print("✅ Database already up to date!")
        conn.close()
        return

    print(f"📝 Adding columns: {', '.join(migrations_needed)}")

    # Add columns
    if 'ai_processed' in migrations_needed:
        cursor.execute('ALTER TABLE posts ADD COLUMN ai_processed BOOLEAN DEFAULT 0')
        print("   ✓ Added ai_processed column")

    if 'source_post_id' in migrations_needed:
        cursor.execute('ALTER TABLE posts ADD COLUMN source_post_id INTEGER REFERENCES posts(id)')
        print("   ✓ Added source_post_id column")

    conn.commit()
    conn.close()

    print("✅ Migration complete!")


if __name__ == '__main__':
    migrate()

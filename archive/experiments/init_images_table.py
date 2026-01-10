#!/usr/bin/env python3
"""
Initialize images table for database-first image storage
No file hosting needed - everything in SQL
"""

from database import get_db

def init_images_table():
    """Create images table"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            data BLOB NOT NULL,
            mime_type TEXT NOT NULL,
            width INTEGER,
            height INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Index for fast hash lookups
    db.execute('CREATE INDEX IF NOT EXISTS idx_images_hash ON images(hash)')

    db.commit()
    db.close()

    print("✅ images table created")
    print("   • hash: SHA256 of image data")
    print("   • data: PNG/JPG bytes (BLOB)")
    print("   • metadata: JSON (type, username, etc.)")


if __name__ == '__main__':
    init_images_table()

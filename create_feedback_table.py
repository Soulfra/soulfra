#!/usr/bin/env python3
"""
Create feedback table for admin dashboard
"""
import sqlite3
import os

# Database path
DB_PATH = 'database.db'

def create_feedback_table():
    """Create feedback table if it doesn't exist"""

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            component TEXT,
            message TEXT NOT NULL,
            url TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new',
            admin_notes TEXT
        )
    ''')

    # Create index for admin queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_feedback_status
        ON feedback(status, created_at DESC)
    ''')

    conn.commit()

    # Verify table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
    if cursor.fetchone():
        print("✅ feedback table created successfully")

        # Show table schema
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        print("\nTable schema:")
        for col in columns:
            print(f"  {col[1]} {col[2]}")
    else:
        print("❌ Failed to create feedback table")

    conn.close()

if __name__ == '__main__':
    create_feedback_table()

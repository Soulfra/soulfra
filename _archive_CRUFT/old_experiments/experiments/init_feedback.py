#!/usr/bin/env python3
"""
Initialize Public Feedback System

Allows users to report bugs/issues WITHOUT logging in.
Admin can see feedback in dashboard.
"""

from database import get_db


def init_feedback_table():
    """Create feedback table for public bug reports"""
    db = get_db()
    
    db.execute('''
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
    
    # Index for admin queries
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_feedback_status
        ON feedback(status, created_at DESC)
    ''')
    
    db.commit()
    db.close()
    
    print("✅ Feedback table created")


if __name__ == '__main__':
    init_feedback_table()

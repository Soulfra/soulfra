#!/usr/bin/env python3
"""
Add Reputation & Contribution Tracking Tables

This enables the Perfect Bits system where contributors earn reputation
for proposals, code reviews, and implementations.
"""

from database import get_db

def migrate():
    """Add reputation and contribution_logs tables"""
    conn = get_db()

    # Reputation table - tracks user's earned bits
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reputation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            bits_earned INTEGER DEFAULT 0,
            bits_spent INTEGER DEFAULT 0,
            contribution_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Contribution logs - tracks each contribution and reward
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contribution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER,
            comment_id INTEGER,
            contribution_type TEXT NOT NULL,
            description TEXT,
            bits_awarded INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_by INTEGER,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (comment_id) REFERENCES comments(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    ''')

    # Initialize reputation for existing users
    conn.execute('''
        INSERT OR IGNORE INTO reputation (user_id, bits_earned, contribution_count)
        SELECT id, 0, 0 FROM users
    ''')

    conn.commit()
    conn.close()

    print("✅ Reputation tables created")
    print("✅ Initialized reputation for all existing users")

if __name__ == '__main__':
    migrate()

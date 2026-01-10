#!/usr/bin/env python3
"""
Kangaroo Court - Database Schema

Simple group voice chat where AI judges your submissions.

Tables:
- kangaroo_submissions - Voice memo submissions with verdicts
- kangaroo_users - User credits and stats
- kangaroo_votes - Voting on submissions
"""

import sqlite3
from datetime import datetime


def init_kangaroo_court_tables():
    """Initialize Kangaroo Court database tables"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # ==========================================================================
    # KANGAROO SUBMISSIONS - Voice memos awaiting judgment
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kangaroo_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT DEFAULT 'main',
            user_id INTEGER,
            username TEXT,
            voice_memo_id TEXT,
            transcription TEXT,
            verdict TEXT DEFAULT 'PENDING',
            severity INTEGER,
            punishment TEXT,
            reward TEXT,
            reasoning TEXT,
            credits_earned INTEGER DEFAULT 5,
            votes INTEGER DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            judged_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (voice_memo_id) REFERENCES voice_memos(id)
        )
    ''')

    # ==========================================================================
    # KANGAROO USERS - Credits and stats
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kangaroo_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            total_credits INTEGER DEFAULT 0,
            submissions_count INTEGER DEFAULT 0,
            guilty_count INTEGER DEFAULT 0,
            innocent_count INTEGER DEFAULT 0,
            total_votes_received INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_submission_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ==========================================================================
    # KANGAROO VOTES - Upvoting submissions
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kangaroo_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            voter_id INTEGER NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES kangaroo_submissions(id),
            FOREIGN KEY (voter_id) REFERENCES users(id),
            UNIQUE(submission_id, voter_id)
        )
    ''')

    # Indexes for performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kangaroo_submissions_room
        ON kangaroo_submissions(room_id, submitted_at DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kangaroo_submissions_user
        ON kangaroo_submissions(user_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kangaroo_submissions_verdict
        ON kangaroo_submissions(verdict)
    ''')

    conn.commit()
    conn.close()

    print("✅ Kangaroo Court tables created successfully")


def seed_example_submissions():
    """Seed database with example submissions for testing"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Create a test user if doesn't exist
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, username, email, password_hash, created_at)
        VALUES (999, 'test_user', 'test@kangaroo.court', 'hash', datetime('now'))
    ''')

    # Create kangaroo user
    cursor.execute('''
        INSERT OR REPLACE INTO kangaroo_users
        (user_id, username, total_credits, submissions_count)
        VALUES (999, 'test_user', 25, 3)
    ''')

    # Example submissions
    examples = [
        {
            'username': 'test_user',
            'transcription': 'I think pineapple belongs on pizza and anyone who disagrees is wrong',
            'verdict': 'INNOCENT',
            'severity': 3,
            'punishment': None,
            'reward': 'You get to choose the next pizza topping',
            'reasoning': 'Bold take, but defensible. Pineapple pizza has its place.',
            'credits_earned': 8
        },
        {
            'username': 'test_user',
            'transcription': 'I never do my dishes and I leave them in the sink for days',
            'verdict': 'GUILTY',
            'severity': 7,
            'punishment': 'Do everyone\'s dishes for a week',
            'reward': None,
            'reasoning': 'Unacceptable behavior in shared living. The court finds you GUILTY.',
            'credits_earned': 12
        },
        {
            'username': 'test_user',
            'transcription': 'Tabs are better than spaces for code indentation',
            'verdict': 'GUILTY',
            'severity': 9,
            'punishment': 'Convert all your code to spaces and explain why to a rubber duck',
            'reward': None,
            'reasoning': 'This is a hill you chose to die on. The court is not merciful.',
            'credits_earned': 14
        }
    ]

    for ex in examples:
        cursor.execute('''
            INSERT INTO kangaroo_submissions
            (user_id, username, voice_memo_id, transcription, verdict, severity,
             punishment, reward, reasoning, credits_earned, votes, judged_at)
            VALUES (999, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 0, datetime('now'))
        ''', (ex['username'], ex['transcription'], ex['verdict'], ex['severity'],
              ex['punishment'], ex['reward'], ex['reasoning'], ex['credits_earned']))

    conn.commit()
    conn.close()

    print("✅ Seeded 3 example submissions")


def get_leaderboard(limit=10):
    """Get top users by credits"""

    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    leaders = cursor.execute('''
        SELECT
            username,
            total_credits,
            submissions_count,
            guilty_count,
            innocent_count,
            total_votes_received
        FROM kangaroo_users
        ORDER BY total_credits DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    conn.close()

    return [dict(row) for row in leaders]


if __name__ == '__main__':
    print("Initializing Kangaroo Court...")
    print("")

    init_kangaroo_court_tables()
    seed_example_submissions()

    print("")
    print("🦘 Kangaroo Court ready!")
    print("")
    print("Example submissions:")
    print("  ✅ Pineapple pizza - INNOCENT")
    print("  ❌ Never do dishes - GUILTY")
    print("  ❌ Tabs > Spaces - GUILTY")
    print("")
    print("Leaderboard:")
    for i, leader in enumerate(get_leaderboard(5), 1):
        print(f"  {i}. {leader['username']}: {leader['total_credits']} credits")
    print("")
    print("Next steps:")
    print("  1. Submit voice memo")
    print("  2. AI judges it")
    print("  3. Get punishment or reward")
    print("  4. Earn credits for AI chat")

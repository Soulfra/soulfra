#!/usr/bin/env python3
"""
Fix missing domain_rotation_state and domain_contexts tables
"""

import sqlite3
from database import get_db

def create_rotation_tables():
    """Create missing rotation tables"""
    db = get_db()

    # Create domain_rotation_state table
    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_rotation_state (
            domain_slug TEXT PRIMARY KEY,
            current_question_index INTEGER DEFAULT 0,
            current_theme_index INTEGER DEFAULT 0,
            current_profile_index INTEGER DEFAULT 0,
            last_rotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rotation_interval_hours INTEGER DEFAULT 24,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create domain_contexts table
    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_slug TEXT NOT NULL,
            context_type TEXT NOT NULL,
            rotation_order INTEGER DEFAULT 0,
            content TEXT,
            metadata TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(domain_slug, context_type, rotation_order)
        )
    ''')

    # Insert default rotation state for main domains
    domains = ['soulfra', 'cringeproof', 'calriven', 'deathtodata', 'stpetepros']

    for domain in domains:
        db.execute('''
            INSERT OR IGNORE INTO domain_rotation_state
            (domain_slug, current_question_index, current_theme_index, current_profile_index)
            VALUES (?, 0, 0, 0)
        ''', (domain,))

    # Insert default questions for each domain
    default_questions = {
        'soulfra': [
            "What would you build if you had unlimited time?",
            "What's the most important problem you're solving right now?",
            "If you could automate one part of your workflow, what would it be?"
        ],
        'cringeproof': [
            "What's the cringiest moment you can laugh about now?",
            "What feedback did you ignore that you wish you'd listened to?",
            "What would your past self be most surprised about?"
        ],
        'calriven': [
            "What's the most important thing on your calendar this week?",
            "What decision are you putting off that you know you need to make?",
            "What would happen if you said 'no' to everything for 48 hours?"
        ],
        'deathtodata': [
            "What data are you collecting that you never look at?",
            "What would you delete if storage wasn't cheap?",
            "What metrics are you tracking that don't actually matter?"
        ],
        'stpetepros': [
            "What local business do you wish existed in St. Pete?",
            "What skill would make the biggest impact on your business?",
            "Who in St. Pete should everyone know about?"
        ]
    }

    for domain, questions in default_questions.items():
        for i, question in enumerate(questions):
            db.execute('''
                INSERT OR IGNORE INTO domain_contexts
                (domain_slug, context_type, rotation_order, content)
                VALUES (?, 'question', ?, ?)
            ''', (domain, i, question))

    db.commit()
    print("✅ Rotation tables created and populated")

    # Show status
    for domain in domains:
        count = db.execute('''
            SELECT COUNT(*) as count FROM domain_contexts
            WHERE domain_slug = ? AND context_type = 'question'
        ''', (domain,)).fetchone()['count']
        print(f"   {domain}: {count} questions")

if __name__ == '__main__':
    create_rotation_tables()

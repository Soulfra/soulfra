#!/usr/bin/env python3
"""
Database Migration: Add Reasoning Platform Features

Adds tables for:
- Reasoning threads (multi-step AI debates)
- Reasoning steps (individual reasoning actions)
- Categories (post organization)
- Tags (post metadata)
- Post-category and post-tag relationships
"""

import sqlite3
from database import get_db, DB_PATH

def migrate():
    print("🔄 Migrating database for reasoning platform features...")
    print(f"   Database: {DB_PATH}")

    conn = get_db()

    # Reasoning threads - Track AI debate sessions
    print("\n📊 Creating reasoning_threads table...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reasoning_threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            initiator_user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (initiator_user_id) REFERENCES users(id)
        )
    ''')

    # Reasoning steps - Individual AI reasoning actions
    print("📊 Creating reasoning_steps table...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reasoning_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            step_type TEXT NOT NULL,
            content TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            parent_step_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES reasoning_threads(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (parent_step_id) REFERENCES reasoning_steps(id) ON DELETE CASCADE
        )
    ''')

    # Categories - Post categories for organization
    print("📊 Creating categories table...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tags - Post tags for metadata
    print("📊 Creating tags table...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Post-category relationship (many-to-many)
    print("📊 Creating post_categories table...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS post_categories (
            post_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            PRIMARY KEY (post_id, category_id),
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    ''')

    # Post-tag relationship (many-to-many)
    print("📊 Creating post_tags table...")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (post_id, tag_id),
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    ''')

    # Create indexes for performance
    print("\n🔍 Creating indexes...")
    conn.execute('CREATE INDEX IF NOT EXISTS idx_reasoning_threads_post_id ON reasoning_threads(post_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_reasoning_steps_thread_id ON reasoning_steps(thread_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_reasoning_steps_user_id ON reasoning_steps(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_post_categories_post_id ON post_categories(post_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_post_categories_category_id ON post_categories(category_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id)')

    # Insert default categories
    print("\n📁 Creating default categories...")
    default_categories = [
        ('Philosophy', 'philosophy', 'Philosophical discussions and debates'),
        ('Technology', 'technology', 'Technical architecture and systems'),
        ('Privacy', 'privacy', 'Privacy and surveillance topics'),
        ('Security', 'security', 'Security and encryption'),
        ('AI', 'ai', 'Artificial intelligence and machine learning'),
        ('Web3', 'web3', 'Decentralization and blockchain')
    ]

    for name, slug, desc in default_categories:
        try:
            conn.execute('INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)', (name, slug, desc))
            print(f"   ✅ {name}")
        except sqlite3.IntegrityError:
            print(f"   ⏭  {name} (already exists)")

    # Insert default tags
    print("\n🏷  Creating default tags...")
    default_tags = [
        ('ollama', 'ollama'),
        ('reasoning', 'reasoning'),
        ('debate', 'debate'),
        ('local-ai', 'local-ai'),
        ('oss', 'oss')
    ]

    for name, slug in default_tags:
        try:
            conn.execute('INSERT INTO tags (name, slug) VALUES (?, ?)', (name, slug))
            print(f"   ✅ {name}")
        except sqlite3.IntegrityError:
            print(f"   ⏭  {name} (already exists)")

    conn.commit()
    conn.close()

    print("\n✅ Migration complete!")
    print("\nNew tables:")
    print("  • reasoning_threads - AI debate sessions")
    print("  • reasoning_steps - Individual reasoning steps")
    print("  • categories - Post categories")
    print("  • tags - Post tags")
    print("  • post_categories - Post-category relationships")
    print("  • post_tags - Post-tag relationships")

if __name__ == '__main__':
    migrate()

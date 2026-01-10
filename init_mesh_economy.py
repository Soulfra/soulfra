#!/usr/bin/env python3
"""
Mesh Network Economy - Master Initialization

Creates ALL tables needed for the voice → wordmap → domains → ownership system.

Run this ONCE to set up the database:
    python3 init_mesh_economy.py

Tables Created:
- users: User accounts
- simple_voice_recordings: Voice memos with transcriptions
- user_wordmaps: Personal vocabulary extracted from voice
- domain_contexts: The 8 mesh network domains
- domain_ownership: Ownership percentages per user per domain
- domain_wordmaps: Collective wordmap for each domain
- ownership_rewards: History of ownership earned
- content_generations: Generated content (pitch decks, blogs, etc.)
"""

import sqlite3
from datetime import datetime


def init_all_tables():
    """Initialize complete mesh network economy database"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("🚀 Initializing Mesh Network Economy Database...\n")

    # 1. Users table
    print("📝 Creating users table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Voice recordings table
    print("🎤 Creating voice recordings table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS simple_voice_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            audio_data BLOB,
            file_size INTEGER,
            transcription TEXT,
            transcription_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 3. User wordmaps table
    print("🗺️  Creating user wordmaps table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_wordmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            wordmap_json TEXT NOT NULL,
            recording_count INTEGER DEFAULT 0,
            vocabulary_size INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 4. Domain contexts table (the 8 domains)
    print("🌐 Creating domain contexts table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            tier TEXT NOT NULL,
            description TEXT,
            initial_keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Domain ownership table
    print("💎 Creating domain ownership table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_ownership (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_id INTEGER NOT NULL,
            ownership_percentage REAL DEFAULT 0.0,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (domain_id) REFERENCES domain_contexts(id),
            UNIQUE(user_id, domain_id)
        )
    ''')

    # 6. Domain wordmaps table
    print("🧠 Creating domain wordmaps table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_wordmaps (
            domain TEXT PRIMARY KEY,
            wordmap_json TEXT NOT NULL,
            contributor_count INTEGER DEFAULT 0,
            total_recordings INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Ownership rewards table
    print("🏆 Creating ownership rewards table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ownership_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            content_type TEXT NOT NULL,
            content_id INTEGER,
            alignment_score REAL NOT NULL,
            reward_pct REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 8. Content generations table
    print("📄 Creating content generations table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            content_type TEXT NOT NULL,
            recording_id INTEGER,
            content_text TEXT,
            alignment_score REAL,
            published BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id)
        )
    ''')

    conn.commit()
    print("\n✅ All tables created successfully!")

    # Show table count
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"\n📊 Total tables in database: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")

    conn.close()
    print("\n🎉 Database initialization complete!")
    print("\nNext steps:")
    print("  1. Run: python3 seed_domains.py")
    print("  2. Run: python3 test_mesh_flow.py")
    print("  3. Visit: http://localhost:5001/domains")


if __name__ == '__main__':
    init_all_tables()

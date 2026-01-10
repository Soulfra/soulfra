#!/usr/bin/env python3
"""
Initialize Messages Table - IRC/Usenet-style messaging

Creates the messages table for cross-domain messaging system
Like Usenet newsgroups or IRC channels

Tables:
- messages: Core message storage
- message_reads: Track which messages user has seen
"""

from database import get_db

def init_messages_tables():
    """Create messages and related tables"""
    db = get_db()

    # Main messages table (like Usenet articles)
    # Named 'domain_messages' to avoid conflict with existing messages table
    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user TEXT NOT NULL,                -- Email or username
            from_device_hash TEXT,                  -- Device fingerprint
            to_domain TEXT NOT NULL,                -- soulfra, cringeproof, etc.
            channel TEXT DEFAULT 'general',         -- Like IRC #channel or alt.domain.channel
            subject TEXT,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            message_type TEXT DEFAULT 'text',       -- text, voice, email, system
            parent_id INTEGER,                      -- For threading (like Usenet)
            FOREIGN KEY (parent_id) REFERENCES domain_messages(id)
        )
    ''')

    db.commit()  # Commit table creation first

    # Index for fast lookups by domain/channel
    try:
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_domain_messages_domain
            ON domain_messages(to_domain, created_at DESC)
        ''')
    except:
        pass

    try:
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_domain_messages_channel
            ON domain_messages(to_domain, channel, created_at DESC)
        ''')
    except:
        pass

    # Message reads (track who's seen what)
    db.execute('''
        CREATE TABLE IF NOT EXISTS message_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            device_hash TEXT NOT NULL,
            read_at TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES domain_messages(id),
            UNIQUE(message_id, device_hash)
        )
    ''')

    # Channels metadata (like IRC #channel list)
    db.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            is_public BOOLEAN DEFAULT 1,
            UNIQUE(domain, channel_name)
        )
    ''')

    db.commit()
    print("✅ Messages tables created")

    # Create default channels for each domain
    create_default_channels(db)


def create_default_channels(db):
    """
    Create default channels for each domain
    Like Usenet hierarchy: alt.soulfra.dev, alt.cringeproof.ideas, etc.
    """
    from datetime import datetime

    domains = [
        ('soulfra', 'general', 'General discussion'),
        ('soulfra', 'dev', 'Development discussions'),
        ('soulfra', 'voice', 'Voice memo transcripts'),

        ('cringeproof', 'ideas', 'Idea submissions'),
        ('cringeproof', 'feedback', 'User feedback'),
        ('cringeproof', 'cringe', 'Cringe reports'),

        ('deathtodata', 'privacy', 'Privacy discussions'),
        ('deathtodata', 'crypto', 'Crypto news and analysis'),
        ('deathtodata', 'leaks', 'Data breach alerts'),

        ('calriven', 'listings', 'Real estate listings'),
        ('calriven', 'market', 'Market analysis'),
        ('calriven', 'voice', 'Voice memos about properties'),

        ('stpetepros', 'jobs', 'Job postings'),
        ('stpetepros', 'events', 'Local events'),
        ('stpetepros', 'directory', 'Professional listings')
    ]

    for domain, channel, description in domains:
        try:
            db.execute('''
                INSERT OR IGNORE INTO channels (domain, channel_name, description, created_at, is_public)
                VALUES (?, ?, ?, ?, 1)
            ''', (domain, channel, description, datetime.now().isoformat()))
        except Exception as e:
            print(f"⚠️  Channel {domain}/{channel} already exists")

    db.commit()
    print(f"✅ Created {len(domains)} default channels")
    print("\n📋 Channel hierarchy (Usenet-style):")
    print("   alt.soulfra.general")
    print("   alt.soulfra.dev")
    print("   alt.soulfra.voice")
    print("   alt.cringeproof.ideas")
    print("   alt.cringeproof.feedback")
    print("   alt.deathtodata.privacy")
    print("   alt.calriven.listings")
    print("   alt.stpetepros.jobs")
    print("   ... and more")


def seed_test_messages():
    """Add some test messages for development"""
    from datetime import datetime
    from device_hash import generate_device_hash

    db = get_db()

    test_messages = [
        ('soulfra', 'general', 'Welcome!', 'Welcome to the Soulfra messaging system'),
        ('cringeproof', 'ideas', 'First idea', 'What if we could predict news article outcomes?'),
        ('deathtodata', 'privacy', 'Privacy tip', 'Always use VPN when browsing'),
        ('calriven', 'market', 'Market update', 'St. Pete real estate up 5% this quarter'),
    ]

    device_hash = generate_device_hash('TestDevice', '127.0.0.1')

    for domain, channel, subject, body in test_messages:
        db.execute('''
            INSERT INTO domain_messages (from_user, from_device_hash, to_domain, channel, subject, body, created_at, message_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'system')
        ''', ('system', device_hash, domain, channel, subject, body, datetime.now().isoformat()))

    db.commit()
    print(f"✅ Added {len(test_messages)} test messages")


if __name__ == '__main__':
    print("🔧 Initializing messages tables...")
    init_messages_tables()

    import sys
    if '--seed' in sys.argv:
        print("\n🌱 Seeding test messages...")
        seed_test_messages()

    print("\n✨ Done!")
    print("\nNext steps:")
    print("  1. Run Flask with message routes")
    print("  2. Send messages via CLI: python3 irc_client.py")
    print("  3. View in browser: /inbox.html")

#!/usr/bin/env python3
"""
Voice Memos Federation - Database Schema

Creates the voice_memos table for federated voice memo storage.

Features:
- Encrypted audio storage
- QR code access control
- Federation-ready (cross-domain sharing)
- Access tracking and expiration
- Multiple access types (QR, NFC, Bluetooth, Time-locked)
"""

import sqlite3
from datetime import datetime


def init_voice_memos_table():
    """Initialize voice_memos table for federated voice storage"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # ==========================================================================
    # VOICE MEMOS - Federated encrypted voice memo storage
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_memos (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            domain TEXT NOT NULL,
            encrypted_audio BLOB NOT NULL,
            encryption_iv TEXT NOT NULL,
            access_key_hash TEXT NOT NULL,
            duration_seconds INTEGER,
            file_size_bytes INTEGER,
            audio_format TEXT DEFAULT 'audio/webm',
            access_type TEXT DEFAULT 'qr',
            federation_shared BOOLEAN DEFAULT 1,
            trusted_domains TEXT,
            access_count INTEGER DEFAULT 0,
            last_accessed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Index for fast lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_voice_memos_domain
        ON voice_memos(domain)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_voice_memos_user
        ON voice_memos(user_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_voice_memos_created
        ON voice_memos(created_at)
    ''')

    # ==========================================================================
    # VOICE MEMO ACCESS LOG - Track who accessed which memos
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_memo_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memo_id TEXT NOT NULL,
            requesting_domain TEXT,
            requesting_ip TEXT,
            access_granted BOOLEAN,
            access_denied_reason TEXT,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (memo_id) REFERENCES voice_memos(id)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_access_log_memo
        ON voice_memo_access_log(memo_id)
    ''')

    # ==========================================================================
    # FEDERATION PEERS - Trusted domains for voice memo sharing
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS federation_peers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            display_name TEXT,
            federation_endpoint TEXT,
            public_key TEXT,
            shared_secret TEXT,
            trust_level TEXT DEFAULT 'trusted',
            voice_memos_enabled BOOLEAN DEFAULT 1,
            last_connected_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Voice memos federation tables created successfully")


def seed_federation_peers():
    """Seed database with default federation peers (your domains)"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Your domains as trusted federation peers
    peers = [
        {
            'domain': 'deathtodata.org',
            'display_name': 'DeathToData',
            'federation_endpoint': 'https://deathtodata.org/api/federation',
            'trust_level': 'owner',
            'voice_memos_enabled': 1
        },
        {
            'domain': 'calriven.com',
            'display_name': 'CalRiven',
            'federation_endpoint': 'https://calriven.com/api/federation',
            'trust_level': 'owner',
            'voice_memos_enabled': 1
        },
        {
            'domain': 'howtocookathome.com',
            'display_name': 'HowToCookAtHome',
            'federation_endpoint': 'https://howtocookathome.com/api/federation',
            'trust_level': 'owner',
            'voice_memos_enabled': 1
        },
        {
            'domain': 'soulfra.com',
            'display_name': 'Soulfra',
            'federation_endpoint': 'https://soulfra.com/api/federation',
            'trust_level': 'owner',
            'voice_memos_enabled': 1
        }
    ]

    for peer in peers:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO federation_peers
                (domain, display_name, federation_endpoint, trust_level, voice_memos_enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', (peer['domain'], peer['display_name'], peer['federation_endpoint'],
                  peer['trust_level'], peer['voice_memos_enabled']))
        except Exception as e:
            print(f"Note: {peer['domain']} already exists or error: {e}")

    conn.commit()
    conn.close()

    print("✅ Seeded 4 federation peers (your domains)")


def get_federation_peers():
    """Get list of all trusted federation peers"""

    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    peers = cursor.execute('''
        SELECT domain, display_name, trust_level, voice_memos_enabled
        FROM federation_peers
        WHERE active = 1
        ORDER BY trust_level DESC, domain ASC
    ''').fetchall()

    conn.close()

    return [dict(p) for p in peers]


def add_federation_peer(domain: str, display_name: str, trust_level: str = 'trusted'):
    """Add a new federation peer"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO federation_peers
        (domain, display_name, trust_level, voice_memos_enabled, created_at)
        VALUES (?, ?, ?, 1, datetime('now'))
    ''', (domain, display_name, trust_level))

    conn.commit()
    conn.close()

    print(f"✅ Added federation peer: {domain} ({display_name})")


if __name__ == '__main__':
    print("Initializing Voice Memos Federation System...")
    print("")

    init_voice_memos_table()
    seed_federation_peers()

    print("")
    print("📋 Federation Peers:")
    peers = get_federation_peers()
    for peer in peers:
        print(f"   - {peer['domain']} ({peer['display_name']}) - {peer['trust_level']}")

    print("")
    print("🎉 Voice Memos Federation ready!")
    print("")
    print("Features:")
    print("  ✅ AES-256-GCM encryption")
    print("  ✅ QR code access control")
    print("  ✅ Cross-domain federation")
    print("  ✅ Access logging")
    print("  ✅ Trusted peer network")
    print("")
    print("Next steps:")
    print("  1. Record voice memo on one domain")
    print("  2. Get QR code with embedded decryption key")
    print("  3. Scan QR code on another domain")
    print("  4. Federation request → encrypted audio transfer")
    print("  5. Local decryption → playback")

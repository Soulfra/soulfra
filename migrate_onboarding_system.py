#!/usr/bin/env python3
"""
Database Migration - Creative Onboarding System

Initialize all database tables for:
- GitHub OAuth + API keys
- Creative challenges
- File imports and routing
- Content pipeline

**Tables Created:**
1. api_keys - API keys from GitHub OAuth or creative challenges
2. oauth_states - OAuth state verification
3. creative_challenges - Challenge definitions
4. challenge_attempts - User challenge submissions
5. file_routes - @brand routing system
6. posts - Enhanced with route and brand fields

**Usage:**
```bash
# Run migration
python3 migrate_onboarding_system.py

# Or from Python:
from migrate_onboarding_system import run_migration
run_migration()
```

**Features:**
- Safe migrations (won't drop existing data)
- Adds columns if missing
- Creates indexes for performance
- Handles upgrades from old schemas
"""

import sqlite3
from database import get_db
from datetime import datetime


# ==============================================================================
# MIGRATION FUNCTIONS
# ==============================================================================

def run_migration():
    """
    Run complete database migration
    """
    print('\n🗄️  Starting database migration...\n')

    conn = get_db()

    try:
        # Create tables
        create_api_keys_table(conn)
        create_oauth_states_table(conn)
        create_creative_challenges_table(conn)
        create_challenge_attempts_table(conn)
        create_file_routes_table(conn)
        upgrade_posts_table(conn)
        create_voice_inputs_table(conn)
        create_voice_qr_attachments_table(conn)
        create_practice_rooms_table(conn)
        create_practice_room_participants_table(conn)
        create_practice_room_recordings_table(conn)

        # Create indexes
        create_indexes(conn)

        conn.commit()

        print('\n✅ Migration completed successfully!\n')

        # Show table summary
        show_table_summary(conn)

    except Exception as e:
        print(f'\n❌ Migration failed: {e}\n')
        conn.rollback()
        raise

    finally:
        conn.close()


# ==============================================================================
# TABLE CREATION
# ==============================================================================

def create_api_keys_table(conn: sqlite3.Connection):
    """Create api_keys table"""
    print('📋 Creating api_keys table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            source TEXT DEFAULT 'manual',
            github_username TEXT,
            github_email TEXT,
            github_repos INTEGER,
            github_followers INTEGER,
            tier INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add source column if missing (for existing tables)
    _add_column_if_missing(conn, 'api_keys', 'source', 'TEXT DEFAULT "manual"')

    print('   ✓ api_keys table ready')


def create_oauth_states_table(conn: sqlite3.Connection):
    """Create oauth_states table for CSRF protection"""
    print('📋 Creating oauth_states table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS oauth_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            state TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    print('   ✓ oauth_states table ready')


def create_creative_challenges_table(conn: sqlite3.Connection):
    """Create creative_challenges table"""
    print('📋 Creating creative_challenges table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS creative_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id TEXT UNIQUE NOT NULL,
            challenge_type TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            prompt TEXT NOT NULL,
            expected_answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    print('   ✓ creative_challenges table ready')


def create_challenge_attempts_table(conn: sqlite3.Connection):
    """Create challenge_attempts table"""
    print('📋 Creating challenge_attempts table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS challenge_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id TEXT NOT NULL,
            challenge_type TEXT NOT NULL,
            user_answer TEXT,
            ai_score REAL,
            passed BOOLEAN,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (challenge_id) REFERENCES creative_challenges(challenge_id)
        )
    ''')

    print('   ✓ challenge_attempts table ready')


def create_file_routes_table(conn: sqlite3.Connection):
    """Create file_routes table for @brand routing"""
    print('📋 Creating file_routes table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS file_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT UNIQUE NOT NULL,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            owner_user_id INTEGER NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (owner_user_id) REFERENCES users(id)
        )
    ''')

    print('   ✓ file_routes table ready')


def upgrade_posts_table(conn: sqlite3.Connection):
    """Upgrade posts table with route and brand fields"""
    print('📋 Upgrading posts table...')

    # Check if posts table exists
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='posts'
    """)

    if not cursor.fetchone():
        # Create posts table if doesn't exist
        conn.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                status TEXT DEFAULT 'draft',
                route TEXT,
                brand TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users(id)
            )
        ''')
        print('   ✓ posts table created')
    else:
        # Add columns if missing
        _add_column_if_missing(conn, 'posts', 'route', 'TEXT')
        _add_column_if_missing(conn, 'posts', 'brand', 'TEXT')
        print('   ✓ posts table upgraded')


def create_voice_inputs_table(conn: sqlite3.Connection):
    """Create voice_inputs table for voice memos"""
    print('📋 Creating voice_inputs table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS voice_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_hash TEXT,
            file_size INTEGER,
            duration_seconds REAL,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            transcription TEXT,
            transcribed_at TIMESTAMP,
            transcription_method TEXT,
            metadata TEXT
        )
    ''')

    print('   ✓ voice_inputs table ready')


def create_voice_qr_attachments_table(conn: sqlite3.Connection):
    """Create voice_qr_attachments table for QR + voice integration"""
    print('📋 Creating voice_qr_attachments table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS voice_qr_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL,
            voice_input_id INTEGER,
            audio_file_path TEXT,
            duration_seconds REAL,
            transcription TEXT,
            transcription_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transcribed_at TIMESTAMP,
            FOREIGN KEY (voice_input_id) REFERENCES voice_inputs(id)
        )
    ''')

    print('   ✓ voice_qr_attachments table ready')


def create_practice_rooms_table(conn: sqlite3.Connection):
    """Create practice_rooms table for practice room system"""
    print('📋 Creating practice_rooms table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS practice_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT UNIQUE NOT NULL,
            topic TEXT NOT NULL,
            creator_id INTEGER,
            max_participants INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            qr_code TEXT,
            qr_ascii TEXT,
            voice_enabled BOOLEAN DEFAULT 1,
            chat_enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY (creator_id) REFERENCES users(id)
        )
    ''')

    print('   ✓ practice_rooms table ready')


def create_practice_room_participants_table(conn: sqlite3.Connection):
    """Create practice_room_participants table"""
    print('📋 Creating practice_room_participants table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS practice_room_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            left_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (room_id) REFERENCES practice_rooms(room_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    print('   ✓ practice_room_participants table ready')


def create_practice_room_recordings_table(conn: sqlite3.Connection):
    """Create practice_room_recordings table"""
    print('📋 Creating practice_room_recordings table...')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS practice_room_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            audio_id INTEGER NOT NULL,
            user_id INTEGER,
            transcription TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES practice_rooms(room_id),
            FOREIGN KEY (audio_id) REFERENCES voice_inputs(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    print('   ✓ practice_room_recordings table ready')


# ==============================================================================
# INDEX CREATION
# ==============================================================================

def create_indexes(conn: sqlite3.Connection):
    """Create indexes for performance"""
    print('📋 Creating indexes...')

    indexes = [
        # api_keys indexes
        ('idx_api_keys_key', 'api_keys', 'api_key'),
        ('idx_api_keys_github', 'api_keys', 'github_username'),
        ('idx_api_keys_user', 'api_keys', 'user_id'),

        # oauth_states indexes
        ('idx_oauth_states_state', 'oauth_states', 'state'),
        ('idx_oauth_states_user', 'oauth_states', 'user_id'),

        # creative_challenges indexes
        ('idx_challenges_id', 'creative_challenges', 'challenge_id'),
        ('idx_challenges_type', 'creative_challenges', 'challenge_type'),

        # challenge_attempts indexes
        ('idx_attempts_user', 'challenge_attempts', 'user_id'),
        ('idx_attempts_challenge', 'challenge_attempts', 'challenge_id'),

        # file_routes indexes
        ('idx_file_routes_route', 'file_routes', 'route'),
        ('idx_file_routes_brand', 'file_routes', 'brand'),
        ('idx_file_routes_owner', 'file_routes', 'owner_user_id'),
        ('idx_file_routes_category', 'file_routes', 'category'),

        # posts indexes
        ('idx_posts_route', 'posts', 'route'),
        ('idx_posts_brand', 'posts', 'brand'),
        ('idx_posts_author', 'posts', 'author_id'),

        # voice_inputs indexes
        ('idx_voice_inputs_status', 'voice_inputs', 'status'),
        ('idx_voice_inputs_source', 'voice_inputs', 'source'),
        ('idx_voice_inputs_hash', 'voice_inputs', 'file_hash'),

        # voice_qr_attachments indexes
        ('idx_voice_qr_scan', 'voice_qr_attachments', 'scan_id'),
        ('idx_voice_qr_voice', 'voice_qr_attachments', 'voice_input_id'),

        # practice_rooms indexes
        ('idx_practice_rooms_room_id', 'practice_rooms', 'room_id'),
        ('idx_practice_rooms_status', 'practice_rooms', 'status'),
        ('idx_practice_rooms_creator', 'practice_rooms', 'creator_id'),

        # practice_room_participants indexes
        ('idx_practice_participants_room', 'practice_room_participants', 'room_id'),
        ('idx_practice_participants_user', 'practice_room_participants', 'user_id'),
        ('idx_practice_participants_status', 'practice_room_participants', 'status'),

        # practice_room_recordings indexes
        ('idx_practice_recordings_room', 'practice_room_recordings', 'room_id'),
        ('idx_practice_recordings_audio', 'practice_room_recordings', 'audio_id'),
        ('idx_practice_recordings_user', 'practice_room_recordings', 'user_id'),
    ]

    for index_name, table_name, column_name in indexes:
        try:
            conn.execute(f'''
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name}({column_name})
            ''')
        except:
            pass  # Index might already exist

    print('   ✓ Indexes created')


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str):
    """Add column to table if it doesn't exist"""
    # Check if column exists
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    if column not in columns:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f'   ✓ Added column {column} to {table}')
        except Exception as e:
            print(f'   ⚠ Could not add {column} to {table}: {e}')


def show_table_summary(conn: sqlite3.Connection):
    """Show summary of created tables"""
    tables = [
        'api_keys',
        'oauth_states',
        'creative_challenges',
        'challenge_attempts',
        'file_routes',
        'posts',
        'users',
        'voice_inputs',
        'voice_qr_attachments',
        'practice_rooms',
        'practice_room_participants',
        'practice_room_recordings'
    ]

    print('📊 Table Summary:\n')

    for table in tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]

            # Get table info
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            print(f'   {table}:')
            print(f'      Rows: {count}')
            print(f'      Columns: {len(columns)}')

        except Exception as e:
            print(f'   {table}: Not found or error')

    print()


# ==============================================================================
# SAMPLE DATA (OPTIONAL)
# ==============================================================================

def insert_sample_data(conn: sqlite3.Connection):
    """
    Insert sample data for testing (optional)
    """
    print('📝 Inserting sample data...')

    # Sample user (if users table exists and is empty)
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            conn.execute('''
                INSERT INTO users (username, email, password_hash, tier, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', ('demo_user', 'demo@soulfra.com', 'hashed_password', 1, datetime.now()))

            print('   ✓ Created sample user: demo_user')

    except:
        pass

    # Sample challenge
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM creative_challenges")
        if cursor.fetchone()[0] == 0:
            conn.execute('''
                INSERT INTO creative_challenges
                (challenge_id, challenge_type, difficulty, prompt, expected_answer, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('ch_sample_001', 'puzzle', 'easy', 'What is 5 + 7?', '12', datetime.now()))

            print('   ✓ Created sample challenge')

    except:
        pass

    conn.commit()
    print('   ✓ Sample data inserted\n')


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Database Migration')
    parser.add_argument('--migrate', action='store_true', help='Run migration')
    parser.add_argument('--sample-data', action='store_true', help='Insert sample data')
    parser.add_argument('--show-tables', action='store_true', help='Show table summary')

    args = parser.parse_args()

    if args.migrate or (not args.sample_data and not args.show_tables):
        # Default: run migration
        run_migration()

        if args.sample_data:
            conn = get_db()
            insert_sample_data(conn)
            conn.close()

    elif args.show_tables:
        conn = get_db()
        show_table_summary(conn)
        conn.close()

    elif args.sample_data:
        conn = get_db()
        insert_sample_data(conn)
        conn.close()

    else:
        print('Usage: python3 migrate_onboarding_system.py')
        print('       python3 migrate_onboarding_system.py --migrate')
        print('       python3 migrate_onboarding_system.py --sample-data')
        print('       python3 migrate_onboarding_system.py --show-tables')

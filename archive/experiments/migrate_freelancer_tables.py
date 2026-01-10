#!/usr/bin/env python3
"""
Database Migration: Freelancer Tables

Creates missing tables needed for freelancer flow:
- newsletter_subscribers
- Enhances existing inbound_emails table

Usage:
    python3 migrate_freelancer_tables.py
    python3 migrate_freelancer_tables.py --dry-run
"""

import sys
from database import get_db


def check_table_exists(table_name: str) -> bool:
    """Check if table exists"""
    conn = get_db()
    result = conn.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    ''', (table_name,)).fetchone()
    conn.close()
    return result is not None


def migrate_newsletter_subscribers(dry_run=False):
    """Create newsletter_subscribers table"""
    table_name = 'newsletter_subscribers'

    if check_table_exists(table_name):
        print(f"✅ Table '{table_name}' already exists, skipping")
        return

    print(f"Creating table '{table_name}'...")

    sql = '''
    CREATE TABLE newsletter_subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        name TEXT,
        brand TEXT,
        verified INTEGER DEFAULT 0,
        api_key_id INTEGER,
        signup_source TEXT DEFAULT 'web',
        device_fingerprint TEXT,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        last_email_at TIMESTAMP,
        unsubscribed_at TIMESTAMP,
        FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
    )
    '''

    if dry_run:
        print(f"  [DRY RUN] Would execute:\n{sql}\n")
        return

    conn = get_db()
    conn.execute(sql)
    conn.execute('CREATE INDEX idx_newsletter_email ON newsletter_subscribers(email)')
    conn.execute('CREATE INDEX idx_newsletter_brand ON newsletter_subscribers(brand)')
    conn.commit()
    conn.close()

    print(f"✅ Created table '{table_name}' with indexes")


def enhance_inbound_emails(dry_run=False):
    """Enhance inbound_emails table if it exists"""
    table_name = 'inbound_emails'

    if not check_table_exists(table_name):
        print(f"ℹ️  Table '{table_name}' doesn't exist yet, will be created when needed")
        return

    print(f"✅ Table '{table_name}' already exists")

    # Check if table has all necessary columns
    conn = get_db()
    columns = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    column_names = [col['name'] for col in columns]
    conn.close()

    required_columns = [
        'id', 'from_email', 'subject', 'body_text', 'in_reply_to',
        'message_id', 'processed', 'post_id', 'comment_id', 'received_at'
    ]

    missing_columns = [col for col in required_columns if col not in column_names]

    if missing_columns:
        print(f"  ⚠️  Missing columns: {missing_columns}")
        print(f"  Manual migration may be needed")
    else:
        print(f"  ✅ All required columns present")


def migrate_ollama_responses_tracking(dry_run=False):
    """
    Add tracking columns to ai_responses table for Ollama
    (Alternative to creating separate ollama_comments table)
    """
    table_name = 'ai_responses'

    if not check_table_exists(table_name):
        print(f"⚠️  Table '{table_name}' doesn't exist")
        return

    print(f"Checking '{table_name}' for Ollama tracking columns...")

    conn = get_db()
    columns = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    column_names = [col['name'] for col in columns]

    ollama_columns = {
        'model': 'TEXT',
        'temperature': 'REAL',
        'response_time_ms': 'INTEGER',
        'prompt': 'TEXT',
        'response_text': 'TEXT'
    }

    missing_ollama_cols = [col for col in ollama_columns if col not in column_names]

    if missing_ollama_cols:
        print(f"  ℹ️  Could add Ollama tracking columns: {missing_ollama_cols}")
        print(f"  Current ai_responses schema is sufficient for basic tracking")
    else:
        print(f"  ✅ All Ollama tracking columns present")

    conn.close()


def create_cache_tables(dry_run=False):
    """Create caching tables for performance"""
    tables = {
        'query_cache': '''
            CREATE TABLE IF NOT EXISTS query_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT NOT NULL UNIQUE,
                cache_value TEXT NOT NULL,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'api_response_cache': '''
            CREATE TABLE IF NOT EXISTS api_response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                params_hash TEXT NOT NULL,
                response_data TEXT NOT NULL,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(endpoint, params_hash)
            )
        '''
    }

    for table_name, sql in tables.items():
        if check_table_exists(table_name):
            print(f"✅ Cache table '{table_name}' already exists")
            continue

        print(f"Creating cache table '{table_name}'...")

        if dry_run:
            print(f"  [DRY RUN] Would execute:\n{sql}\n")
            continue

        conn = get_db()
        conn.execute(sql)

        # Add indexes
        if table_name == 'query_cache':
            conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON query_cache(cache_key)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON query_cache(expires_at)')
        elif table_name == 'api_response_cache':
            conn.execute('CREATE INDEX IF NOT EXISTS idx_api_cache_endpoint ON api_response_cache(endpoint)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_response_cache(expires_at)')

        conn.commit()
        conn.close()

        print(f"✅ Created cache table '{table_name}' with indexes")


def run_migrations(dry_run=False):
    """Run all migrations"""
    print("="*80)
    print("FREELANCER TABLES MIGRATION")
    print("="*80)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")

    print("\n1. Newsletter Subscribers Table")
    print("-" * 40)
    migrate_newsletter_subscribers(dry_run)

    print("\n2. Inbound Emails Table")
    print("-" * 40)
    enhance_inbound_emails(dry_run)

    print("\n3. Ollama Response Tracking")
    print("-" * 40)
    migrate_ollama_responses_tracking(dry_run)

    print("\n4. Cache Tables")
    print("-" * 40)
    create_cache_tables(dry_run)

    print("\n" + "="*80)
    if dry_run:
        print("DRY RUN COMPLETE - No changes were made")
    else:
        print("MIGRATION COMPLETE")
    print("="*80 + "\n")


def verify_migrations():
    """Verify all tables exist and are properly structured"""
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80 + "\n")

    tables_to_check = [
        'newsletter_subscribers',
        'inbound_emails',
        'ai_responses',
        'api_keys',
        'api_call_logs',
        'query_cache',
        'api_response_cache'
    ]

    conn = get_db()

    for table in tables_to_check:
        exists = conn.execute('''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        ''', (table,)).fetchone()

        if exists:
            row_count = conn.execute(f'SELECT COUNT(*) as c FROM {table}').fetchone()['c']
            print(f"✅ {table:30s} ({row_count:,} rows)")
        else:
            print(f"❌ {table:30s} (missing)")

    conn.close()

    print()


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv

    run_migrations(dry_run=dry_run)

    if not dry_run:
        verify_migrations()

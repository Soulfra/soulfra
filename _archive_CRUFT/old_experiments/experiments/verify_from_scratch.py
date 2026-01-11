#!/usr/bin/env python3
"""
Verify Platform is Reproducible "From Scratch"

Proves the OSS/schema-as-code principle:
1. Delete existing database
2. Rebuild ONLY from migrations
3. Verify all 22 tables exist
4. Show schema version
5. Prove reproducibility

This answers: "how do we know this was all working or whatever then
and oss or something from scratch?"

The answer: THIS SCRIPT.
"""

import os
import sys
import sqlite3
from pathlib import Path


DB_PATH = 'soulfra.db'
BACKUP_PATH = 'soulfra.db.backup_before_verify'

# Expected tables (all 22)
EXPECTED_TABLES = {
    # Core tables (migration 001)
    'users',
    'posts',
    'comments',
    'messages',
    'notifications',
    'subscribers',

    # Reasoning platform (migration 003)
    'reasoning_threads',
    'reasoning_steps',
    'categories',
    'tags',
    'post_categories',
    'post_tags',

    # QR tracking (migration 004)
    'qr_codes',
    'qr_scans',

    # Images (migration 005)
    'images',

    # Soul history (migration 006)
    'soul_history',

    # URL shortener (migration 007)
    'url_shortcuts',

    # Reputation (migration 008)
    'reputation',
    'contribution_logs',

    # ML (migration 009)
    'ml_models',
    'predictions',

    # Feedback (migration 010)
    'feedback',

    # Migration tracking
    'schema_migrations'
}


def backup_existing_db():
    """Backup existing database before test"""
    if os.path.exists(DB_PATH):
        print(f"📦 Backing up existing database to {BACKUP_PATH}")

        # Copy file
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)

        print(f"   ✅ Backup created")
        return True
    else:
        print(f"ℹ️  No existing database to backup")
        return False


def delete_database():
    """Delete database to test from-scratch build"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️  Deleted {DB_PATH}")
    else:
        print(f"ℹ️  {DB_PATH} doesn't exist")


def run_migrations():
    """Run migrations using migrate.py"""
    print("\n🔄 Running migrations from scratch...")
    print()

    # Import and run migrations
    import migrate
    migrate.run_migrations()


def verify_schema():
    """
    Verify all expected tables exist

    Returns:
        tuple: (success: bool, missing: set, extra: set)
    """
    print("\n🔍 Verifying schema...")
    print()

    conn = sqlite3.connect(DB_PATH)

    # Get all tables
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    actual_tables = {row[0] for row in cursor.fetchall()}

    conn.close()

    # Filter out SQLite internal tables
    sqlite_internal = {'sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4'}
    actual_tables = actual_tables - sqlite_internal

    # Compare
    missing = EXPECTED_TABLES - actual_tables
    extra = actual_tables - EXPECTED_TABLES

    print(f"Expected tables: {len(EXPECTED_TABLES)}")
    print(f"Actual tables: {len(actual_tables)}")
    print()

    if missing:
        print(f"❌ Missing tables ({len(missing)}):")
        for table in sorted(missing):
            print(f"   - {table}")
        print()

    if extra:
        print(f"⚠️  Extra tables ({len(extra)}):")
        for table in sorted(extra):
            print(f"   + {table}")
        print()

    if not missing and not extra:
        print("✅ All tables present and accounted for!")
        print()

        print("Tables by migration:")
        print()
        print("  001 - Core Platform:")
        print("    • users, posts, comments, messages, notifications, subscribers")
        print()
        print("  003 - Reasoning Platform:")
        print("    • reasoning_threads, reasoning_steps")
        print("    • categories, tags, post_categories, post_tags")
        print()
        print("  004 - QR Tracking:")
        print("    • qr_codes, qr_scans")
        print()
        print("  005 - Images:")
        print("    • images")
        print()
        print("  006 - Soul History:")
        print("    • soul_history")
        print()
        print("  007 - URL Shortener:")
        print("    • url_shortcuts")
        print()
        print("  008 - Reputation:")
        print("    • reputation, contribution_logs")
        print()
        print("  009 - ML:")
        print("    • ml_models, predictions")
        print()
        print("  010 - Feedback:")
        print("    • feedback")
        print()

    return (len(missing) == 0 and len(extra) == 0, missing, extra)


def get_schema_version():
    """Get current schema version from migrations"""
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(
            'SELECT version, name FROM schema_migrations ORDER BY version DESC LIMIT 1'
        )
        row = cursor.fetchone()

        if row:
            return f"{row[0]}_{row[1]}"
        else:
            return "No migrations applied"

    except sqlite3.OperationalError:
        return "schema_migrations table doesn't exist"

    finally:
        conn.close()


def verify_from_scratch():
    """
    Main verification function

    Process:
    1. Backup existing DB (if exists)
    2. Delete DB
    3. Run migrations from scratch
    4. Verify all tables exist
    5. Show schema version
    6. Report success/failure
    """
    print("=" * 70)
    print("🧪 Verify Platform Reproducibility - 'From Scratch' Test")
    print("=" * 70)
    print()
    print("This proves the platform can be built from migrations alone.")
    print("No manual schema changes, no hidden setup - just SQL files.")
    print()

    # Backup
    had_backup = backup_existing_db()
    print()

    # Delete
    delete_database()
    print()

    # Migrate
    run_migrations()

    # Verify
    success, missing, extra = verify_schema()

    # Schema version
    version = get_schema_version()

    print()
    print("=" * 70)
    print("📊 Verification Results")
    print("=" * 70)
    print()

    if success:
        print("✅ SUCCESS - Platform is reproducible from scratch!")
        print()
        print(f"Schema version: {version}")
        print(f"Total tables: {len(EXPECTED_TABLES)}")
        print()
        print("🎉 OSS Principle Validated:")
        print("   • Schema is code (migrations/*.sql)")
        print("   • Reproducible (delete DB, run migrations, everything works)")
        print("   • Versioned (schema_migrations tracks state)")
        print("   • Auditable (see exactly what changed when)")
        print()

        if had_backup:
            print(f"💾 Your data is safe in: {BACKUP_PATH}")
            print(f"   To restore: mv {BACKUP_PATH} {DB_PATH}")

        return True

    else:
        print("❌ FAILED - Missing or extra tables")
        print()
        print(f"Schema version: {version}")
        print()

        if missing:
            print(f"Missing {len(missing)} tables - migrations incomplete!")
        if extra:
            print(f"Found {len(extra)} unexpected tables - schema drift?")

        return False


def main():
    """Main entry point"""
    try:
        success = verify_from_scratch()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

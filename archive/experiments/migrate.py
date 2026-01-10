#!/usr/bin/env python3
"""
Database Migration System - "Schema is Code"

Applies SQL migrations in order, tracks which have been applied.
Like Rails/Django migrations but simpler.

Usage:
    python3 migrate.py          # Apply all pending migrations
    python3 migrate.py status   # Show migration status
    python3 migrate.py reset    # Reset database (WARNING: deletes all data!)

Teaching the pattern:
1. Migrations are numbered SQL files (001_name.sql, 002_name.sql)
2. schema_migrations table tracks which have been applied
3. Migrations run in order, skip already-applied
4. Reproducible "from scratch" - same migrations = same schema
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = 'soulfra.db'
MIGRATIONS_DIR = 'migrations'


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_migrations_table():
    """
    Create schema_migrations table to track applied migrations

    Table structure:
    - version: Migration number (001, 002, etc.)
    - name: Migration name (initial_schema, add_excerpts, etc.)
    - applied_at: When migration was applied
    """
    conn = get_db()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def get_applied_migrations():
    """
    Get list of already-applied migrations

    Returns:
        set: Set of version numbers (e.g., {'001', '002', '003'})
    """
    conn = get_db()

    try:
        rows = conn.execute('SELECT version FROM schema_migrations ORDER BY version').fetchall()
        return {row['version'] for row in rows}
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return set()
    finally:
        conn.close()


def get_migration_files():
    """
    Get all migration files from migrations/ directory

    Returns:
        list: Sorted list of (version, name, filepath) tuples

    Example:
        [('001', 'initial_schema', 'migrations/001_initial_schema.sql'), ...]
    """
    migrations = []

    migrations_path = Path(MIGRATIONS_DIR)
    if not migrations_path.exists():
        print(f"❌ Migrations directory not found: {MIGRATIONS_DIR}")
        sys.exit(1)

    for filepath in sorted(migrations_path.glob('*.sql')):
        filename = filepath.name

        # Parse filename: 001_initial_schema.sql -> ('001', 'initial_schema')
        parts = filename.replace('.sql', '').split('_', 1)

        if len(parts) != 2:
            print(f"⚠️  Skipping invalid migration filename: {filename}")
            continue

        version, name = parts
        migrations.append((version, name, str(filepath)))

    return migrations


def apply_migration(version, name, filepath):
    """
    Apply a single migration

    Args:
        version: Migration version (e.g., '001')
        name: Migration name (e.g., 'initial_schema')
        filepath: Path to SQL file

    Returns:
        bool: True if successful
    """
    print(f"  Applying {version}_{name}...")

    # Read SQL file
    try:
        with open(filepath, 'r') as f:
            sql = f.read()
    except Exception as e:
        print(f"    ❌ Failed to read migration file: {e}")
        return False

    # Execute SQL
    conn = get_db()

    try:
        # Use executescript for full SQL file execution
        # This properly handles multi-statement SQL files
        # Note: executescript commits automatically
        conn.executescript(sql)
        conn.close()

        # Record migration as applied (need fresh connection after executescript)
        conn2 = get_db()
        conn2.execute(
            'INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)',
            (version, name, datetime.now().isoformat())
        )
        conn2.commit()
        conn2.close()

        print(f"    ✅ Applied {version}_{name}")
        return True

    except Exception as e:
        print(f"    ❌ Failed to apply migration: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def run_migrations():
    """
    Run all pending migrations

    Process:
    1. Create schema_migrations table
    2. Get list of applied migrations
    3. Get list of migration files
    4. Apply migrations not yet applied
    """
    print("=" * 70)
    print("🔄 Database Migration System")
    print("=" * 70)
    print()

    # Initialize migrations table
    init_migrations_table()

    # Get applied migrations
    applied = get_applied_migrations()

    # Get migration files
    migration_files = get_migration_files()

    if not migration_files:
        print("No migration files found in migrations/")
        return

    print(f"Found {len(migration_files)} migration files")
    print(f"Already applied: {len(applied)} migrations")
    print()

    # Apply pending migrations
    pending = [(v, n, f) for v, n, f in migration_files if v not in applied]

    if not pending:
        print("✅ All migrations up to date!")
        print()
        show_status()
        return

    print(f"Applying {len(pending)} pending migrations:")
    print()

    success = 0
    failed = 0

    for version, name, filepath in pending:
        if apply_migration(version, name, filepath):
            success += 1
        else:
            failed += 1
            print(f"\n❌ Migration failed, stopping here")
            break

    print()
    print("=" * 70)
    print(f"📊 Migration Results")
    print("=" * 70)
    print(f"✅ Applied: {success}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print()
        print("✅ All migrations completed successfully!")
        print("🎉 Database schema is now up to date")

    print()
    show_status()


def show_status():
    """Show current migration status"""
    print("=" * 70)
    print("📊 Migration Status")
    print("=" * 70)
    print()

    # Get applied migrations
    conn = get_db()

    try:
        applied = conn.execute(
            'SELECT version, name, applied_at FROM schema_migrations ORDER BY version'
        ).fetchall()
    except sqlite3.OperationalError:
        print("No migrations applied yet (schema_migrations table doesn't exist)")
        conn.close()
        return

    conn.close()

    # Get all migration files
    migration_files = get_migration_files()
    applied_versions = {row['version'] for row in applied}

    print(f"Database: {DB_PATH}")
    print(f"Migrations directory: {MIGRATIONS_DIR}")
    print()

    if not applied:
        print("No migrations applied yet")
        print()
    else:
        print(f"Applied migrations ({len(applied)}):")
        print()
        for row in applied:
            print(f"  ✅ {row['version']}_{row['name']}")
            print(f"     Applied: {row['applied_at']}")
        print()

    # Show pending migrations
    pending = [(v, n) for v, n, _ in migration_files if v not in applied_versions]

    if pending:
        print(f"Pending migrations ({len(pending)}):")
        print()
        for version, name in pending:
            print(f"  ⏳ {version}_{name}")
        print()
    else:
        print("✅ All migrations up to date!")
        print()

    # Show schema version
    if applied:
        latest = applied[-1]
        print(f"Current schema version: {latest['version']}_{latest['name']}")
        print()


def reset_database():
    """
    Reset database - DELETE ALL DATA and reapply migrations

    WARNING: This deletes the entire database!
    """
    print("=" * 70)
    print("⚠️  DATABASE RESET - THIS WILL DELETE ALL DATA!")
    print("=" * 70)
    print()

    response = input("Are you sure you want to delete soulfra.db and rebuild from scratch? [yes/NO]: ")

    if response.lower() != 'yes':
        print("Cancelled")
        return

    print()
    print("Deleting database...")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ Deleted {DB_PATH}")
    else:
        print(f"ℹ️  {DB_PATH} doesn't exist")

    print()
    print("Rebuilding from migrations...")
    print()

    run_migrations()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'status':
            show_status()
        elif command == 'reset':
            reset_database()
        else:
            print(f"Unknown command: {command}")
            print()
            print("Usage:")
            print("  python3 migrate.py          # Apply pending migrations")
            print("  python3 migrate.py status   # Show migration status")
            print("  python3 migrate.py reset    # Reset database (deletes all data!)")
    else:
        run_migrations()


if __name__ == '__main__':
    main()

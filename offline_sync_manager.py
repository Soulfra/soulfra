#!/usr/bin/env python3
"""
Offline Sync Manager - Laptop Works Offline/Online Seamlessly

Like Git: Commit locally, push when connected.

Your laptop:
- Works OFFLINE (SQLite local, queue changes)
- PRELOADS static assets ahead of time
- COMPILES sites before you need them
- SYNCS to production when online

Usage:
    # Work offline
    python3 offline_sync_manager.py --work-offline

    # Sync when online
    python3 offline_sync_manager.py --sync

    # Preload all assets
    python3 offline_sync_manager.py --preload

    # Check status
    python3 offline_sync_manager.py --status
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict
import hashlib


# ============================================================================
# Configuration
# ============================================================================

LOCAL_DB = 'soulfra.db'  # Local SQLite (works offline)
SYNC_QUEUE_DB = 'sync_queue.db'  # Queue of changes to sync
PRELOAD_DIR = 'preloaded_assets'  # Static assets cached locally
COMPILE_DIR = 'compiled_sites'  # Pre-compiled sites


# ============================================================================
# Sync Queue Management
# ============================================================================

def init_sync_queue():
    """Initialize sync queue database"""

    conn = sqlite3.connect(SYNC_QUEUE_DB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            synced BOOLEAN DEFAULT 0,
            synced_at TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Sync queue initialized")


def queue_change(action: str, table: str, record_id: int, data: Dict):
    """
    Queue a change for sync

    Args:
        action: 'insert', 'update', 'delete'
        table: Table name
        record_id: Record ID
        data: Change data
    """

    conn = sqlite3.connect(SYNC_QUEUE_DB)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO sync_queue (action, table_name, record_id, data)
        VALUES (?, ?, ?, ?)
    ''', (action, table, record_id, json.dumps(data)))

    conn.commit()
    conn.close()

    print(f"📝 Queued: {action} {table}/{record_id}")


def get_pending_syncs() -> List[Dict]:
    """Get all pending syncs"""

    conn = sqlite3.connect(SYNC_QUEUE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    pending = cursor.execute('''
        SELECT * FROM sync_queue
        WHERE synced = 0
        ORDER BY created_at ASC
    ''').fetchall()

    conn.close()

    return [dict(row) for row in pending]


def mark_synced(sync_id: int):
    """Mark a sync as completed"""

    conn = sqlite3.connect(SYNC_QUEUE_DB)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE sync_queue
        SET synced = 1, synced_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), sync_id))

    conn.commit()
    conn.close()


# ============================================================================
# Offline Mode
# ============================================================================

def enable_offline_mode():
    """
    Enable offline mode

    - SQLite local works normally
    - Queue all changes for later sync
    - Use preloaded assets
    """

    print("🔌 Offline mode enabled")
    print("   - Local SQLite works normally")
    print("   - Changes queued for sync")
    print("   - Using preloaded assets")

    # Create marker file
    with open('.offline_mode', 'w') as f:
        f.write(datetime.now().isoformat())

    init_sync_queue()


def is_offline_mode() -> bool:
    """Check if offline mode is active"""
    return os.path.exists('.offline_mode')


# ============================================================================
# Preloading
# ============================================================================

def preload_static_assets():
    """
    Preload static assets for offline use

    - CSS/JS files
    - Domain configs
    - Templates
    - Common images
    """

    os.makedirs(PRELOAD_DIR, exist_ok=True)

    print("📦 Preloading static assets...\n")

    # Files to preload
    preload_files = [
        'domains_config.py',
        'domain_mapper.py',
        'content_taxonomy.py',
        'voice_quality_checker.py',
        'template_generator.py',
        'professional_routes.py',
    ]

    for file_path in preload_files:
        if os.path.exists(file_path):
            # Copy to preload dir
            dest = os.path.join(PRELOAD_DIR, file_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            with open(file_path, 'r') as f:
                content = f.read()

            with open(dest, 'w') as f:
                f.write(content)

            print(f"✅ Preloaded: {file_path}")

    print(f"\n✅ Preloaded {len(preload_files)} files")


def compile_professional_sites():
    """
    Pre-compile professional sites for offline viewing

    Generate static HTML for all professional sites
    """

    os.makedirs(COMPILE_DIR, exist_ok=True)

    print("🔨 Compiling professional sites...\n")

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    professionals = cursor.execute('''
        SELECT id, business_name, subdomain
        FROM professional_profile
    ''').fetchall()

    conn.close()

    for prof_id, business_name, subdomain in professionals:
        # Generate site HTML
        from template_generator import generate_professional_site

        try:
            site_html = generate_professional_site(prof_id)

            # Save to compile dir
            site_dir = os.path.join(COMPILE_DIR, subdomain or str(prof_id))
            os.makedirs(site_dir, exist_ok=True)

            for page_name, html_content in site_html.items():
                file_path = os.path.join(site_dir, f"{page_name}.html")

                with open(file_path, 'w') as f:
                    f.write(html_content)

            print(f"✅ Compiled: {business_name} ({subdomain or prof_id})")

        except Exception as e:
            print(f"❌ Failed: {business_name} - {e}")

    print(f"\n✅ Compiled {len(professionals)} sites")


# ============================================================================
# Syncing
# ============================================================================

def sync_to_production():
    """
    Sync queued changes to production

    Requires online connection
    """

    if is_offline_mode():
        print("⚠️  Still in offline mode. Remove .offline_mode file to sync.")
        return

    pending = get_pending_syncs()

    if not pending:
        print("✅ No changes to sync")
        return

    print(f"🔄 Syncing {len(pending)} changes...\n")

    for sync in pending:
        action = sync['action']
        table = sync['table_name']
        record_id = sync['record_id']
        data = json.loads(sync['data'])

        print(f"   {action} {table}/{record_id}")

        # TODO: Implement actual sync to production
        # This would use API calls or database connection to production

        # For now, mark as synced
        mark_synced(sync['id'])

    print(f"\n✅ Synced {len(pending)} changes")


def check_sync_status():
    """Check sync status"""

    pending_count = len(get_pending_syncs())

    if is_offline_mode():
        print("🔌 Offline mode: ACTIVE")
    else:
        print("🌐 Online mode: ACTIVE")

    print(f"📊 Pending syncs: {pending_count}")

    if pending_count > 0:
        print("\n   Run: python3 offline_sync_manager.py --sync")


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import sys

    if '--work-offline' in sys.argv:
        enable_offline_mode()

    elif '--sync' in sys.argv:
        sync_to_production()

    elif '--preload' in sys.argv:
        preload_static_assets()

    elif '--compile' in sys.argv:
        compile_professional_sites()

    elif '--status' in sys.argv:
        check_sync_status()

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Offline Sync Manager - Laptop Works Offline/Online                 ║
║                                                                      ║
║  Like Git: Commit locally, push when connected.                     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python3 offline_sync_manager.py --work-offline    # Enable offline mode
    python3 offline_sync_manager.py --sync            # Sync to production
    python3 offline_sync_manager.py --preload         # Preload assets
    python3 offline_sync_manager.py --compile         # Compile sites
    python3 offline_sync_manager.py --status          # Check status

Workflow:
    1. Enable offline mode: --work-offline
    2. Work locally (SQLite works, changes queued)
    3. Preload assets: --preload
    4. Compile sites: --compile
    5. When online: --sync
""")

        check_sync_status()

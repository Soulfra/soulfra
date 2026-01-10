#!/usr/bin/env python3
"""
Auto-Sync Daemon - Watches soulfra.db and syncs to GitHub Pages

Watches for database changes and automatically:
1. Rebuilds static sites (waitlist, domains, profiles)
2. Pushes changes to GitHub Pages
3. Logs all sync operations

Usage:
    python3 auto_sync_daemon.py                    # Run in foreground
    python3 auto_sync_daemon.py --daemon           # Run in background
    python3 auto_sync_daemon.py --once             # Sync once and exit
"""

import os
import sys
import time
import sqlite3
import subprocess
import hashlib
import json
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('auto_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = Path('./soulfra.db')
SYNC_INTERVAL = 30  # seconds
STATE_FILE = Path('./auto_sync_state.json')
GITHUB_REPO_PATH = Path('/Users/matthewmauer/Desktop/soulfra.github.io')

class AutoSyncDaemon:
    def __init__(self):
        self.db_hash = None
        self.last_sync = None
        self.sync_count = 0
        self.load_state()

    def load_state(self):
        """Load previous state from JSON"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    state = json.load(f)
                    self.db_hash = state.get('db_hash')
                    self.last_sync = state.get('last_sync')
                    self.sync_count = state.get('sync_count', 0)
                    logger.info(f"Loaded state: {self.sync_count} syncs, last: {self.last_sync}")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def save_state(self):
        """Save current state to JSON"""
        state = {
            'db_hash': self.db_hash,
            'last_sync': self.last_sync,
            'sync_count': self.sync_count
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

    def get_db_hash(self):
        """Calculate MD5 hash of database file"""
        if not DB_PATH.exists():
            return None

        md5 = hashlib.md5()
        with open(DB_PATH, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def has_db_changed(self):
        """Check if database has been modified"""
        current_hash = self.get_db_hash()
        if current_hash is None:
            logger.error(f"Database not found: {DB_PATH}")
            return False

        if self.db_hash is None:
            # First run
            self.db_hash = current_hash
            return True

        if current_hash != self.db_hash:
            logger.info(f"Database changed: {self.db_hash[:8]} → {current_hash[:8]}")
            self.db_hash = current_hash
            return True

        return False

    def get_changed_tables(self):
        """Query database to see what changed recently"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        changes = []

        # Check waitlist signups
        try:
            cursor.execute("SELECT COUNT(*) as count FROM waitlist")
            waitlist_count = cursor.fetchone()['count']
            changes.append(f"Waitlist: {waitlist_count} signups")
        except:
            pass

        # Check user profiles
        try:
            cursor.execute("SELECT COUNT(*) as count FROM user_profiles")
            profile_count = cursor.fetchone()['count']
            changes.append(f"Profiles: {profile_count} users")
        except:
            pass

        # Check recordings
        try:
            cursor.execute("SELECT COUNT(*) as count FROM simple_voice_recordings")
            recording_count = cursor.fetchone()['count']
            changes.append(f"Recordings: {recording_count} total")
        except:
            pass

        conn.close()
        return changes

    def rebuild_static_sites(self):
        """Rebuild all static sites from database"""
        logger.info("Rebuilding static sites...")

        scripts = [
            ('build_waitlist.py', 'Waitlist'),
            ('build_domains_manager.py', 'Domain Manager'),
        ]

        for script, name in scripts:
            if not Path(script).exists():
                logger.warning(f"Script not found: {script}")
                continue

            try:
                logger.info(f"Building {name}...")
                result = subprocess.run(
                    ['python3', script],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    logger.info(f"✅ {name} built successfully")
                else:
                    logger.error(f"❌ {name} build failed: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                logger.error(f"❌ {name} build timed out")
                return False
            except Exception as e:
                logger.error(f"❌ {name} build error: {e}")
                return False

        return True

    def sync_to_github(self):
        """Copy built files to GitHub repo and optionally push"""
        logger.info("Syncing to GitHub repo...")

        # Copy output to GitHub repo
        try:
            subprocess.run(
                ['rsync', '-av', './output/', str(GITHUB_REPO_PATH) + '/'],
                check=True,
                capture_output=True
            )
            logger.info("✅ Files synced to GitHub repo")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ rsync failed: {e}")
            return False

        # Check if repo has changes
        try:
            os.chdir(GITHUB_REPO_PATH)
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                logger.info("No changes to commit")
                return True

            logger.info(f"Changes detected:\n{result.stdout}")

            # NOTE: We don't auto-push to GitHub yet
            # User should manually review and push
            logger.info("⚠️  Changes ready to commit. Run manually:")
            logger.info(f"    cd {GITHUB_REPO_PATH}")
            logger.info(f"    git add .")
            logger.info(f"    git commit -m 'Auto-sync: {datetime.now().isoformat()}'")
            logger.info(f"    git push")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ git status failed: {e}")
            return False
        finally:
            os.chdir(Path(__file__).parent)

        return True

    def perform_sync(self):
        """Execute full sync workflow"""
        logger.info("="*60)
        logger.info(f"SYNC #{self.sync_count + 1} - {datetime.now().isoformat()}")

        # Get what changed
        changes = self.get_changed_tables()
        if changes:
            logger.info("Database state:")
            for change in changes:
                logger.info(f"  • {change}")

        # Rebuild static sites
        if not self.rebuild_static_sites():
            logger.error("Rebuild failed, skipping GitHub sync")
            return False

        # Sync to GitHub
        if not self.sync_to_github():
            logger.error("GitHub sync failed")
            return False

        # Update state
        self.sync_count += 1
        self.last_sync = datetime.now().isoformat()
        self.save_state()

        logger.info(f"✅ Sync complete (#{self.sync_count})")
        logger.info("="*60)
        return True

    def run_once(self):
        """Sync once and exit"""
        logger.info("Running one-time sync...")
        self.perform_sync()

    def run_daemon(self):
        """Run continuous monitoring loop"""
        logger.info("Starting auto-sync daemon...")
        logger.info(f"Watching: {DB_PATH}")
        logger.info(f"Interval: {SYNC_INTERVAL}s")
        logger.info(f"GitHub repo: {GITHUB_REPO_PATH}")

        # Initial sync
        if self.has_db_changed():
            self.perform_sync()

        # Monitoring loop
        try:
            while True:
                time.sleep(SYNC_INTERVAL)

                if self.has_db_changed():
                    logger.info("Database change detected!")
                    self.perform_sync()
                else:
                    logger.debug("No changes detected")

        except KeyboardInterrupt:
            logger.info("\nStopping daemon...")
            self.save_state()
            logger.info(f"Performed {self.sync_count} syncs")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Auto-sync database to GitHub Pages')
    parser.add_argument('--once', action='store_true', help='Sync once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon')
    args = parser.parse_args()

    daemon = AutoSyncDaemon()

    if args.once:
        daemon.run_once()
    else:
        daemon.run_daemon()

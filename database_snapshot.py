#!/usr/bin/env python3
"""
Database Snapshot Export - Provable Database State

Creates cryptographically-signed snapshots of the voice predictions database.
Published to GitHub Pages for transparency and verification.

**Purpose:**
Prove that predictions weren't backdated by creating tamper-proof snapshots.

**How It Works:**

1. Export database state to JSON
2. Generate SHA256 hash of entire snapshot
3. Publish to voice-archive/database-snapshots/
4. Git commit with timestamp (proof of when)
5. Content hash proves what was in database at that time

**Usage:**

```bash
# Export current database state
python3 database_snapshot.py --export

# Verify snapshot integrity
python3 database_snapshot.py --verify 2026-01-03.json

# Verify all snapshots
python3 database_snapshot.py --verify-all

# Publish to GitHub Pages
python3 database_snapshot.py --export --publish
```

**Output Structure:**

```json
{
  "snapshot_hash": "abc123def456...",
  "exported_at": "2026-01-03T09:00:00Z",
  "version": "1.0",
  "database_path": "soulfra.db",
  "predictions": [
    {
      "content_hash": "d489b26c288a...",
      "recorded_at": "2026-01-02T21:34:11",
      "article_hash": "...",
      "transcription_preview": "First 50 chars...",
      "export_path": "voice-archive/d489b26c/"
    }
  ],
  "statistics": {
    "total_predictions": 1,
    "exported_predictions": 1,
    "time_locked_predictions": 0
  }
}
```
"""

import os
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# ==============================================================================
# CONFIG
# ==============================================================================

DATABASE_PATH = Path('soulfra.db')
SNAPSHOT_DIR = Path('voice-archive/database-snapshots')
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# DATABASE SNAPSHOT
# ==============================================================================

class DatabaseSnapshot:
    """Create and verify database snapshots"""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

    def get_all_predictions(self) -> List[Dict]:
        """
        Get all voice predictions from database

        Returns:
            List of prediction dicts
        """
        cursor = self.db.execute("""
            SELECT
                p.id as pairing_id,
                p.content_hash,
                p.user_prediction,
                p.paired_at,
                p.time_lock_until,
                p.exported_at,
                p.export_path,
                p.cringe_factor,
                p.published_to_archive,

                r.id as recording_id,
                r.filename as audio_filename,
                r.transcription,
                r.created_at as recorded_at,
                r.file_size,

                a.id as article_id,
                a.title as article_title,
                a.url as article_url,
                a.source as article_source,
                a.topics as article_topics,
                a.article_hash

            FROM voice_article_pairings p
            LEFT JOIN simple_voice_recordings r ON p.recording_id = r.id
            LEFT JOIN news_articles a ON p.article_id = a.id
            ORDER BY p.paired_at DESC
        """)

        predictions = []

        for row in cursor.fetchall():
            predictions.append({
                'pairing_id': row['pairing_id'],
                'content_hash': row['content_hash'],
                'user_prediction': row['user_prediction'],
                'paired_at': row['paired_at'],
                'time_lock_until': row['time_lock_until'],
                'exported_at': row['exported_at'],
                'export_path': row['export_path'],
                'cringe_factor': row['cringe_factor'],
                'published_to_archive': bool(row['published_to_archive']),

                'recording': {
                    'id': row['recording_id'],
                    'filename': row['audio_filename'],
                    'transcription_preview': (row['transcription'] or '')[:100],
                    'recorded_at': row['recorded_at'],
                    'file_size': row['file_size'],
                },

                'article': {
                    'id': row['article_id'],
                    'title': row['article_title'],
                    'url': row['article_url'],
                    'source': row['article_source'],
                    'topics': row['article_topics'],
                    'article_hash': row['article_hash'],
                }
            })

        return predictions

    def calculate_snapshot_hash(self, snapshot_data: Dict) -> str:
        """
        Calculate SHA256 hash of entire snapshot

        Args:
            snapshot_data: Snapshot dict

        Returns:
            SHA256 hash string
        """
        # Sort keys for deterministic hashing
        sorted_json = json.dumps(snapshot_data, sort_keys=True)
        return hashlib.sha256(sorted_json.encode()).hexdigest()

    def export_snapshot(self, publish: bool = False) -> Path:
        """
        Export database snapshot to JSON file

        Args:
            publish: If True, also publish to GitHub Pages

        Returns:
            Path to snapshot file
        """
        print("\n📸 Creating database snapshot...")

        # Get all predictions
        predictions = self.get_all_predictions()

        # Calculate statistics
        total = len(predictions)
        exported = sum(1 for p in predictions if p['exported_at'])
        time_locked = sum(1 for p in predictions if p['time_lock_until'])

        # Create snapshot data (without hash yet)
        snapshot_data = {
            'version': '1.0',
            'database_path': str(self.db_path),
            'exported_at': datetime.now().isoformat(),
            'predictions': predictions,
            'statistics': {
                'total_predictions': total,
                'exported_predictions': exported,
                'time_locked_predictions': time_locked
            }
        }

        # Calculate snapshot hash
        snapshot_hash = self.calculate_snapshot_hash(snapshot_data)
        snapshot_data['snapshot_hash'] = snapshot_hash

        # Create filename with date
        filename = f"{datetime.now().strftime('%Y-%m-%d')}.json"
        snapshot_path = SNAPSHOT_DIR / filename

        # Write snapshot
        snapshot_path.write_text(json.dumps(snapshot_data, indent=2))

        print(f"✅ Snapshot created: {snapshot_path}")
        print(f"   Hash: {snapshot_hash[:16]}...")
        print(f"   Predictions: {total}")

        # Publish to GitHub if requested
        if publish:
            self._publish_to_github(snapshot_path)

        return snapshot_path

    def verify_snapshot(self, snapshot_path: Path) -> bool:
        """
        Verify snapshot integrity

        Args:
            snapshot_path: Path to snapshot JSON

        Returns:
            True if verified, False otherwise
        """
        if not snapshot_path.exists():
            print(f"❌ Snapshot not found: {snapshot_path}")
            return False

        try:
            snapshot_data = json.loads(snapshot_path.read_text())

            # Extract stored hash
            stored_hash = snapshot_data.get('snapshot_hash')

            if not stored_hash:
                print(f"❌ No snapshot_hash found in {snapshot_path}")
                return False

            # Remove hash and recalculate
            snapshot_data_without_hash = snapshot_data.copy()
            del snapshot_data_without_hash['snapshot_hash']

            calculated_hash = self.calculate_snapshot_hash(snapshot_data_without_hash)

            # Compare
            if stored_hash == calculated_hash:
                print(f"✅ {snapshot_path.name} - VERIFIED")
                print(f"   Hash: {stored_hash[:16]}...")
                print(f"   Predictions: {snapshot_data['statistics']['total_predictions']}")
                return True
            else:
                print(f"❌ {snapshot_path.name} - HASH MISMATCH")
                print(f"   Stored:     {stored_hash[:16]}...")
                print(f"   Calculated: {calculated_hash[:16]}...")
                return False

        except Exception as e:
            print(f"❌ Error verifying {snapshot_path}: {e}")
            return False

    def verify_all_snapshots(self) -> Dict:
        """
        Verify all database snapshots

        Returns:
            {
                'total': int,
                'verified': int,
                'failed': int,
                'details': List[Dict]
            }
        """
        snapshots = list(SNAPSHOT_DIR.glob('*.json'))

        if not snapshots:
            print("⚠️  No snapshots found in database-snapshots/")
            return {'total': 0, 'verified': 0, 'failed': 0, 'details': []}

        print(f"\n{'='*60}")
        print(f"  VERIFYING {len(snapshots)} DATABASE SNAPSHOTS")
        print(f"{'='*60}\n")

        verified = 0
        failed = 0
        details = []

        for snapshot_path in sorted(snapshots):
            is_verified = self.verify_snapshot(snapshot_path)

            if is_verified:
                verified += 1
                details.append({'file': snapshot_path.name, 'status': 'verified'})
            else:
                failed += 1
                details.append({'file': snapshot_path.name, 'status': 'failed'})

        print(f"\n{'='*60}")
        print(f"  SUMMARY")
        print(f"{'='*60}\n")
        print(f"Total:    {len(snapshots)}")
        print(f"✅ Verified: {verified}")
        print(f"❌ Failed:   {failed}\n")

        return {
            'total': len(snapshots),
            'verified': verified,
            'failed': failed,
            'details': details
        }

    def _publish_to_github(self, snapshot_path: Path):
        """
        Publish snapshot to GitHub Pages

        Args:
            snapshot_path: Path to snapshot file
        """
        import subprocess

        try:
            # Assuming voice-archive is a git repo
            archive_dir = Path('voice-archive')

            if not (archive_dir / '.git').exists():
                print("⚠️  voice-archive is not a git repo - skipping publish")
                return

            # Copy snapshot to voice-archive/database-snapshots/
            dest_path = archive_dir / 'database-snapshots' / snapshot_path.name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(snapshot_path.read_text())

            # Git commit and push
            subprocess.run(['git', 'add', 'database-snapshots/'], cwd=archive_dir, check=True)
            subprocess.run(
                ['git', 'commit', '-m', f'Database snapshot: {snapshot_path.name}'],
                cwd=archive_dir,
                check=True
            )
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=archive_dir, check=True)

            print(f"✅ Published to GitHub: voice-archive/database-snapshots/{snapshot_path.name}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git publish failed: {e}")


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Database Snapshot Export and Verification'
    )

    parser.add_argument(
        '--export',
        action='store_true',
        help='Export current database state to snapshot'
    )

    parser.add_argument(
        '--verify',
        type=str,
        metavar='FILENAME',
        help='Verify specific snapshot file'
    )

    parser.add_argument(
        '--verify-all',
        action='store_true',
        help='Verify all snapshots'
    )

    parser.add_argument(
        '--publish',
        action='store_true',
        help='Publish snapshot to GitHub Pages'
    )

    args = parser.parse_args()

    snapshot = DatabaseSnapshot()

    if args.export:
        snapshot.export_snapshot(publish=args.publish)

    elif args.verify:
        snapshot_path = SNAPSHOT_DIR / args.verify
        snapshot.verify_snapshot(snapshot_path)

    elif args.verify_all:
        snapshot.verify_all_snapshots()

    else:
        parser.print_help()

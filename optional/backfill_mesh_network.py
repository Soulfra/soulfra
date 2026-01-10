#!/usr/bin/env python3
"""
Backfill Mesh Network - Process Existing Recordings

Run the mesh network cascade on all previously transcribed recordings
that haven't been processed yet.

This is the "backward propagation" - applying the new mesh network
to old recordings so they contribute to your wordmap economy.

Usage:
======
```bash
# Process all unprocessed transcriptions
python3 backfill_mesh_network.py

# Process specific user's recordings
python3 backfill_mesh_network.py --user 1

# Dry run (show what would be processed)
python3 backfill_mesh_network.py --dry-run

# Force reprocess all recordings (even if already processed)
python3 backfill_mesh_network.py --force
```
"""

import sys
from typing import List, Dict
from database import get_db
from economy_mesh_network import on_voice_transcribed


def get_unprocessed_recordings(user_id: int = None, force: bool = False) -> List[Dict]:
    """
    Get recordings that have transcriptions but haven't been processed
    through mesh network yet.

    Args:
        user_id: Optional filter by user ID
        force: If True, return ALL transcribed recordings (reprocess)

    Returns:
        List of recording dicts with id, user_id, filename, transcription
    """
    db = get_db()

    if force:
        # Get ALL transcribed recordings
        query = '''
            SELECT id, user_id, filename, transcription, created_at
            FROM simple_voice_recordings
            WHERE transcription IS NOT NULL
        '''
        params = ()

        if user_id:
            query += ' AND user_id = ?'
            params = (user_id,)

        query += ' ORDER BY created_at ASC'

    else:
        # Get only recordings without mesh network processing
        # (We'll assume if a recording has been processed, it has economy rewards)
        # This is a heuristic - recordings with rewards have been processed
        query = '''
            SELECT DISTINCT r.id, r.user_id, r.filename, r.transcription, r.created_at
            FROM simple_voice_recordings r
            WHERE r.transcription IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM ownership_rewards rw
                WHERE rw.user_id = r.user_id
                AND rw.created_at >= r.created_at
                AND rw.created_at <= datetime(r.created_at, '+5 minutes')
            )
        '''
        params = ()

        if user_id:
            query += ' AND r.user_id = ?'
            params = (user_id,)

        query += ' ORDER BY r.created_at ASC'

    recordings = db.execute(query, params).fetchall()

    return [dict(r) for r in recordings]


def backfill_recordings(
    recordings: List[Dict],
    dry_run: bool = False
) -> Dict:
    """
    Process recordings through mesh network

    Args:
        recordings: List of recording dicts
        dry_run: If True, don't actually process, just show what would happen

    Returns:
        {
            'total': int,
            'processed': int,
            'failed': int,
            'results': [...]
        }
    """
    total = len(recordings)
    processed = 0
    failed = 0
    results = []

    print(f"\n{'='*70}")
    print(f"📦 BACKFILLING MESH NETWORK")
    print(f"{'='*70}")
    print(f"Found {total} recording(s) to process\n")

    if dry_run:
        print("🔍 DRY RUN MODE - No actual processing\n")
        for rec in recordings:
            print(f"   Would process: #{rec['id']} - {rec['filename']}")
            print(f"      User: {rec['user_id']}")
            print(f"      Transcription: {len(rec['transcription'])} chars")
            print(f"      Created: {rec['created_at']}\n")

        return {
            'total': total,
            'processed': 0,
            'failed': 0,
            'results': [],
            'dry_run': True
        }

    for i, rec in enumerate(recordings, 1):
        recording_id = rec['id']

        print(f"[{i}/{total}] Processing recording #{recording_id}...")
        print(f"   File: {rec['filename']}")
        print(f"   User: {rec['user_id']}")
        print(f"   Transcription: {len(rec['transcription'])} chars\n")

        try:
            # Trigger mesh network cascade
            result = on_voice_transcribed(recording_id)

            if result.get('success'):
                processed += 1
                results.append({
                    'recording_id': recording_id,
                    'success': True,
                    'domains_matched': len(result.get('domains_matched', [])),
                    'content_generated': len(result.get('content_generated', {})),
                    'rewards_claimed': len(result.get('rewards_claimed', {}))
                })

                print(f"✅ Success")
                print(f"   Matched: {len(result.get('domains_matched', []))} domains")
                print(f"   Generated: {len(result.get('content_generated', {}))} content pieces")
                print(f"   Rewards: {len(result.get('rewards_claimed', {}))} claimed\n")
            else:
                failed += 1
                error_msg = result.get('error', 'Unknown error')
                results.append({
                    'recording_id': recording_id,
                    'success': False,
                    'error': error_msg
                })
                print(f"❌ Failed: {error_msg}\n")

        except Exception as e:
            failed += 1
            results.append({
                'recording_id': recording_id,
                'success': False,
                'error': str(e)
            })
            print(f"❌ Error: {e}\n")

    # Summary
    print(f"{'='*70}")
    print(f"📊 BACKFILL COMPLETE")
    print(f"{'='*70}")
    print(f"Total recordings: {total}")
    print(f"Successfully processed: {processed}")
    print(f"Failed: {failed}")

    # Aggregate stats
    total_domains_matched = sum(r.get('domains_matched', 0) for r in results if r.get('success'))
    total_content_generated = sum(r.get('content_generated', 0) for r in results if r.get('success'))
    total_rewards_claimed = sum(r.get('rewards_claimed', 0) for r in results if r.get('success'))

    print(f"\n🎯 Aggregate Results:")
    print(f"   Total domain matches: {total_domains_matched}")
    print(f"   Total content generated: {total_content_generated}")
    print(f"   Total rewards claimed: {total_rewards_claimed}")
    print(f"{'='*70}\n")

    return {
        'total': total,
        'processed': processed,
        'failed': failed,
        'results': results,
        'dry_run': False
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Backfill mesh network on existing transcribed recordings'
    )
    parser.add_argument(
        '--user',
        type=int,
        help='Only process recordings for this user ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually processing'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Reprocess ALL transcribed recordings (even if already processed)'
    )

    args = parser.parse_args()

    try:
        # Get recordings to process
        recordings = get_unprocessed_recordings(
            user_id=args.user,
            force=args.force
        )

        if not recordings:
            print("\n✅ No recordings to process!")
            print("   All transcribed recordings have already been processed through mesh network.")
            print("   Use --force to reprocess all recordings.\n")
            sys.exit(0)

        # Process them
        result = backfill_recordings(
            recordings=recordings,
            dry_run=args.dry_run
        )

        # Exit with error code if any failed
        if result['failed'] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

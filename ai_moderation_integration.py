#!/usr/bin/env python3
"""
AI Moderation Integration
Connects prohibited_words_filter.py with OSP compliance system
"""

from database import get_db
from prohibited_words_filter import check_prohibited
from datetime import datetime, timezone
import json


def auto_moderate_content(content_type, content_id, text_content, domain="soulfra"):
    """
    Automatically moderate content using AI filter

    Args:
        content_type: Type of content (recording, comment, post, etc.)
        content_id: ID of the content
        text_content: Text to analyze
        domain: Domain context (soulfra, cringeproof, deathtodata)

    Returns:
        dict: Moderation result with action and confidence
    """
    db = get_db()

    # Check prohibited words
    is_prohibited, matches = check_prohibited(text_content, domain)

    if is_prohibited:
        # Calculate confidence based on number of matches
        confidence = min(0.5 + (len(matches) * 0.1), 1.0)

        # Create moderation queue entry
        reasons = ", ".join([f"{m['pattern']} ({m['category']})" for m in matches])
        analysis = json.dumps({
            'matches': matches,
            'total_violations': len(matches),
            'categories': list(set(m['category'] for m in matches)),
            'severity': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low'
        })

        now = datetime.now(timezone.utc).isoformat()

        try:
            cursor = db.execute('''
                INSERT INTO moderation_queue
                (content_type, content_id, flagged_reason, ai_confidence,
                 ai_analysis, flagged_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                content_type,
                content_id,
                f"AI flagged: {reasons}",
                confidence,
                analysis,
                now
            ))

            db.commit()

            print(f"🚫 AI Moderation: Flagged {content_type}:{content_id} (confidence: {confidence:.0%})")

            return {
                'flagged': True,
                'confidence': confidence,
                'reasons': reasons,
                'queue_id': cursor.lastrowid,
                'action': 'quarantine' if confidence > 0.8 else 'review'
            }

        except Exception as e:
            print(f"⚠️  Error creating moderation entry: {e}")
            db.rollback()
            return {
                'flagged': True,
                'confidence': confidence,
                'reasons': reasons,
                'error': str(e)
            }

    else:
        return {
            'flagged': False,
            'confidence': 0.0,
            'action': 'approve'
        }


def auto_moderate_voice_recording(recording_id):
    """
    Moderate a voice recording by its transcription

    Args:
        recording_id: ID of the voice recording

    Returns:
        dict: Moderation result
    """
    db = get_db()

    # Get recording transcription
    recording = db.execute('''
        SELECT id, transcription
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return {'error': 'Recording not found'}

    if not recording['transcription']:
        return {'flagged': False, 'reason': 'No transcription available'}

    return auto_moderate_content(
        'recording',
        recording_id,
        recording['transcription'],
        domain='soulfra'
    )


def auto_moderate_text_submission(submission_id, text):
    """
    Moderate a text submission (idea, comment, etc.)

    Args:
        submission_id: ID of the submission
        text: Text content

    Returns:
        dict: Moderation result
    """
    return auto_moderate_content(
        'text_submission',
        submission_id,
        text,
        domain='soulfra'
    )


def get_moderation_stats():
    """
    Get AI moderation statistics

    Returns:
        dict: Stats about flagged content
    """
    db = get_db()

    stats = {
        'total_flagged': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue"
        ).fetchone()['c'],

        'pending_review': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue WHERE status = 'pending'"
        ).fetchone()['c'],

        'approved': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue WHERE status = 'approved'"
        ).fetchone()['c'],

        'removed': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue WHERE status = 'removed'"
        ).fetchone()['c'],

        'avg_confidence': db.execute(
            "SELECT AVG(ai_confidence) as avg FROM moderation_queue WHERE ai_confidence IS NOT NULL"
        ).fetchone()['avg'] or 0.0
    }

    # Get top flagging reasons
    top_reasons = db.execute('''
        SELECT flagged_reason, COUNT(*) as count
        FROM moderation_queue
        GROUP BY flagged_reason
        ORDER BY count DESC
        LIMIT 5
    ''').fetchall()

    stats['top_reasons'] = [
        {'reason': r['flagged_reason'], 'count': r['count']}
        for r in top_reasons
    ]

    return stats


def bulk_moderate_pending_recordings():
    """
    Scan all unmoderated voice recordings and flag violations

    Returns:
        dict: Results of bulk moderation
    """
    db = get_db()

    # Get all recordings not yet moderated
    recordings = db.execute('''
        SELECT id, transcription
        FROM simple_voice_recordings
        WHERE transcription IS NOT NULL
        AND id NOT IN (
            SELECT content_id
            FROM moderation_queue
            WHERE content_type = 'recording'
        )
    ''').fetchall()

    results = {
        'scanned': len(recordings),
        'flagged': 0,
        'approved': 0,
        'errors': 0
    }

    for rec in recordings:
        result = auto_moderate_voice_recording(rec['id'])

        if result.get('flagged'):
            results['flagged'] += 1
        elif result.get('error'):
            results['errors'] += 1
        else:
            results['approved'] += 1

    print(f"✅ Bulk moderation complete: {results['scanned']} scanned, {results['flagged']} flagged")

    return results


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("AI Moderation Integration")
        print("\nUsage:")
        print("  python3 ai_moderation_integration.py scan")
        print("  python3 ai_moderation_integration.py stats")
        print("  python3 ai_moderation_integration.py test 'some text to test'")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scan':
        print("🔍 Scanning all unmoderated content...")
        results = bulk_moderate_pending_recordings()
        print(f"\n📊 Results:")
        print(f"   Scanned: {results['scanned']}")
        print(f"   Flagged: {results['flagged']}")
        print(f"   Approved: {results['approved']}")
        print(f"   Errors: {results['errors']}")

    elif command == 'stats':
        stats = get_moderation_stats()
        print("\n📊 AI Moderation Statistics:\n")
        print(f"  Total flagged: {stats['total_flagged']}")
        print(f"  Pending review: {stats['pending_review']}")
        print(f"  Approved: {stats['approved']}")
        print(f"  Removed: {stats['removed']}")
        print(f"  Avg confidence: {stats['avg_confidence']:.1%}")

        if stats['top_reasons']:
            print("\n  Top flagging reasons:")
            for r in stats['top_reasons']:
                print(f"    - {r['reason']}: {r['count']}")

    elif command == 'test':
        if len(sys.argv) < 3:
            print("Usage: python3 ai_moderation_integration.py test 'text to analyze'")
            sys.exit(1)

        text = sys.argv[2]
        result = auto_moderate_content('test', 0, text)

        print(f"\n🔍 Test Results for: '{text}'\n")
        print(f"  Flagged: {result['flagged']}")
        print(f"  Confidence: {result.get('confidence', 0):.1%}")
        if result['flagged']:
            print(f"  Reasons: {result.get('reasons', 'N/A')}")
            print(f"  Action: {result.get('action', 'N/A')}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

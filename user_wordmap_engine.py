#!/usr/bin/env python3
"""
User Wordmap Engine - Persistent Personal Voice

Each user has a cumulative wordmap that grows from their voice recordings.

Concept: "Pure Source"
- First recording = 100% weight (your original voice)
- Each new recording merges in with decay (recent words weighted higher)
- Result: Your authentic vocabulary that defines YOUR voice over time

This wordmap then contributes to domain wordmaps based on your ownership %.

Tables:
- user_wordmaps: user_id, wordmap_json, recording_count, last_updated, pure_source_id
"""

import json
from typing import Dict, Optional
from datetime import datetime
from collections import Counter
from database import get_db


def init_user_wordmap_table():
    """Create user_wordmaps table"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS user_wordmaps (
            user_id INTEGER PRIMARY KEY,
            wordmap_json TEXT NOT NULL,
            recording_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pure_source_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (pure_source_id) REFERENCES simple_voice_recordings(id)
        )
    ''')

    db.commit()
    print("✅ user_wordmaps table created")


def get_user_wordmap(user_id: int) -> Optional[Dict]:
    """
    Get user's current cumulative wordmap

    Returns:
        {
            'wordmap': {'word': frequency, ...},
            'recording_count': int,
            'pure_source_id': int or None,
            'last_updated': timestamp
        }
    """
    db = get_db()

    result = db.execute('''
        SELECT wordmap_json, recording_count, pure_source_id, last_updated
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if not result:
        return None

    return {
        'wordmap': json.loads(result['wordmap_json']),
        'recording_count': result['recording_count'],
        'pure_source_id': result['pure_source_id'],
        'last_updated': result['last_updated']
    }


def merge_wordmaps(
    existing_wordmap: Dict[str, int],
    new_wordmap: Dict[str, int],
    decay_factor: float = 0.95
) -> Dict[str, int]:
    """
    Merge new wordmap into existing wordmap with decay

    Args:
        existing_wordmap: Current cumulative wordmap
        new_wordmap: Wordmap from new recording
        decay_factor: Weight for existing words (0.95 = 95% of old + 100% of new)

    Returns:
        Merged wordmap
    """
    merged = {}

    # Decay existing words (minimum value of 1 to prevent zero-out)
    for word, count in existing_wordmap.items():
        decayed = int(count * decay_factor)
        merged[word] = max(1, decayed)  # Prevent words from decaying to 0

    # Add new words (full weight)
    for word, count in new_wordmap.items():
        if word in merged:
            merged[word] += count
        else:
            merged[word] = count

    # Remove words that have decayed to 1 and haven't appeared in last 10 recordings
    # (This prevents word accumulation while keeping recent vocabulary)
    # For now, just keep top 200 by frequency
    sorted_words = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_words[:200])


def update_user_wordmap(user_id: int, recording_id: int, transcript: str) -> Dict:
    """
    Update user's cumulative wordmap with new recording

    Args:
        user_id: User ID
        recording_id: Recording ID (for pure source tracking)
        transcript: New transcript to add

    Returns:
        {
            'wordmap': updated wordmap,
            'recording_count': total recordings processed,
            'is_pure_source': bool (was this the first recording?),
            'top_words': list of (word, count) tuples
        }
    """
    from wordmap_pitch_integrator import extract_wordmap_from_transcript

    db = get_db()

    # Extract wordmap from new transcript
    new_wordmap = extract_wordmap_from_transcript(transcript, top_n=100)

    # Get existing wordmap
    existing = get_user_wordmap(user_id)

    if not existing:
        # First recording = "pure source"
        db.execute('''
            INSERT INTO user_wordmaps (user_id, wordmap_json, recording_count, pure_source_id, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            json.dumps(new_wordmap),
            1,
            recording_id,
            datetime.now().isoformat()
        ))
        db.commit()

        return {
            'wordmap': new_wordmap,
            'recording_count': 1,
            'is_pure_source': True,
            'pure_source_id': recording_id,
            'top_words': list(new_wordmap.items())[:20]
        }

    # Merge with decay
    merged_wordmap = merge_wordmaps(existing['wordmap'], new_wordmap, decay_factor=0.95)

    # Update database
    db.execute('''
        UPDATE user_wordmaps
        SET wordmap_json = ?,
            recording_count = recording_count + 1,
            last_updated = ?
        WHERE user_id = ?
    ''', (
        json.dumps(merged_wordmap),
        datetime.now().isoformat(),
        user_id
    ))
    db.commit()

    return {
        'wordmap': merged_wordmap,
        'recording_count': existing['recording_count'] + 1,
        'is_pure_source': False,
        'pure_source_id': existing['pure_source_id'],
        'top_words': list(merged_wordmap.items())[:20]
    }


def get_wordmap_evolution(user_id: int) -> Dict:
    """
    Get user's wordmap evolution over time

    Returns:
        {
            'pure_source': first recording metadata,
            'current_wordmap': current state,
            'recordings_processed': count,
            'top_20_words': most frequent words,
            'rare_words': words appearing only once,
            'vocabulary_size': total unique words
        }
    """
    db = get_db()

    wordmap_data = get_user_wordmap(user_id)

    if not wordmap_data:
        return {
            'error': 'No wordmap found - user needs to record first voice memo'
        }

    wordmap = wordmap_data['wordmap']

    # Get pure source recording details
    pure_source = None
    if wordmap_data['pure_source_id']:
        pure_source_rec = db.execute('''
            SELECT id, filename, created_at, transcription
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (wordmap_data['pure_source_id'],)).fetchone()

        if pure_source_rec:
            pure_source = {
                'id': pure_source_rec['id'],
                'filename': pure_source_rec['filename'],
                'created_at': pure_source_rec['created_at'],
                'excerpt': pure_source_rec['transcription'][:200] + '...' if pure_source_rec['transcription'] else None
            }

    # Analyze wordmap
    sorted_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)
    rare_words = [word for word, count in wordmap.items() if count == 1]

    return {
        'pure_source': pure_source,
        'current_wordmap': wordmap,
        'recordings_processed': wordmap_data['recording_count'],
        'top_20_words': sorted_words[:20],
        'rare_words': rare_words[:10],
        'vocabulary_size': len(wordmap),
        'last_updated': wordmap_data['last_updated']
    }


def reset_user_wordmap(user_id: int) -> bool:
    """
    Reset user's wordmap (start fresh)

    WARNING: This deletes their cumulative voice history
    """
    db = get_db()

    db.execute('DELETE FROM user_wordmaps WHERE user_id = ?', (user_id,))
    db.commit()

    return True


def compare_user_wordmaps(user_id_1: int, user_id_2: int) -> Dict:
    """
    Compare two users' wordmaps to find similarity

    Returns:
        {
            'overlap_words': words both use,
            'user1_unique': words only user1 uses,
            'user2_unique': words only user2 uses,
            'similarity_score': 0.0-1.0
        }
    """
    wordmap1 = get_user_wordmap(user_id_1)
    wordmap2 = get_user_wordmap(user_id_2)

    if not wordmap1 or not wordmap2:
        return {'error': 'One or both users have no wordmap'}

    words1 = set(wordmap1['wordmap'].keys())
    words2 = set(wordmap2['wordmap'].keys())

    overlap = words1 & words2
    unique1 = words1 - words2
    unique2 = words2 - words1

    # Jaccard similarity
    similarity = len(overlap) / len(words1 | words2) if (words1 | words2) else 0.0

    return {
        'overlap_words': list(overlap)[:20],
        'user1_unique': list(unique1)[:20],
        'user2_unique': list(unique2)[:20],
        'similarity_score': similarity,
        'overlap_count': len(overlap),
        'total_unique_words': len(words1 | words2)
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 user_wordmap_engine.py init              # Create table")
        print("  python3 user_wordmap_engine.py show <user_id>    # Show user wordmap")
        print("  python3 user_wordmap_engine.py compare <id1> <id2> # Compare two users")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init':
        init_user_wordmap_table()

    elif command == 'show' and len(sys.argv) > 2:
        user_id = int(sys.argv[2])
        evolution = get_wordmap_evolution(user_id)
        print(json.dumps(evolution, indent=2))

    elif command == 'compare' and len(sys.argv) > 3:
        user1 = int(sys.argv[2])
        user2 = int(sys.argv[3])
        comparison = compare_user_wordmaps(user1, user2)
        print(json.dumps(comparison, indent=2))

    else:
        print("Unknown command")
        sys.exit(1)

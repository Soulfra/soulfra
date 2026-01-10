#!/usr/bin/env python3
"""
Convert Existing Voice Recordings → Suggestions

Stop building new mics. Use the data we already have.

What this does:
1. Reads from simple_voice_recordings table (7 recordings)
2. Extracts ideas from transcripts (manually defined or AI)
3. Generates SHA256 hash
4. Inserts into voice_suggestions table
5. Makes /suggestion-box show actual content TODAY

Usage:
    # Convert Recording #7
    python3 convert_recordings_to_suggestions.py --recording 7

    # Convert all recordings
    python3 convert_recordings_to_suggestions.py --all

    # Preview without inserting
    python3 convert_recordings_to_suggestions.py --recording 7 --dry-run
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from database import get_db


def extract_wordmap_from_text(text, top_n=20):
    """
    Extract word frequencies from text

    Same logic as wordmap builder but simpler
    """
    import re
    from collections import Counter

    # Clean text
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()

    # Filter stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
                 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                 'it', 'its', 'that', 'this', 'these', 'those', 'i', 'you', 'he', 'she',
                 'we', 'they', 'my', 'your', 'his', 'her', 'our', 'their', 'so', 'know',
                 'im', 'just', 'like', 'all', 'what', 'when', 'where', 'how', 'why'}

    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]

    # Count frequencies
    word_freq = Counter(filtered_words)

    return dict(word_freq.most_common(top_n))


def generate_sha256_hash(transcription, wordmap):
    """Generate SHA256 hash from transcript + wordmap"""
    content = {
        'transcription': transcription,
        'wordmap': wordmap
    }
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def extract_ideas_from_recording_7():
    """
    Manually extract ideas from Recording #7

    Transcript: "cringe on social media... authentic... genuine connection..."
    """
    return [
        {
            'title': 'Authentic social media vs performative content',
            'text': 'Everyone trying so hard to be authentic but it all feels fake. Need genuine connection and real community instead of the validation game.',
            'score': 90,
            'insight': 'Core frustration with current social media dynamics',
            'category': 'social_media'
        },
        {
            'title': 'Build trust through vulnerability and honesty',
            'text': 'People being vulnerable and honest is the only way to build trust and belonging. Spaces where people can express true identity without fear.',
            'score': 85,
            'insight': 'Values-based alternative to performative culture',
            'category': 'community'
        },
        {
            'title': 'Social acceptance shouldn\'t be based on performance',
            'text': 'The whole validation game is broken. Social acceptance should be about being real, being yourself, finding your truth.',
            'score': 80,
            'insight': 'Systemic critique of social validation mechanics',
            'category': 'identity'
        }
    ]


def convert_recording_to_suggestion(recording_id, dry_run=False):
    """
    Convert a voice recording to a suggestion

    Args:
        recording_id: ID from simple_voice_recordings table
        dry_run: Preview without inserting
    """
    db = get_db()

    # Get recording
    recording = db.execute('''
        SELECT id, filename, transcription, created_at
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        print(f"❌ Recording {recording_id} not found")
        return None

    if not recording['transcription']:
        print(f"❌ Recording {recording_id} has no transcription")
        return None

    print(f"\n{'='*70}")
    print(f"  Converting Recording #{recording_id}")
    print(f"{'='*70}\n")

    print(f"Filename: {recording['filename']}")
    print(f"Transcript: {recording['transcription'][:100]}...")
    print()

    # Extract ideas
    if recording_id == 7:
        # Use manually defined ideas for Recording #7
        ideas = extract_ideas_from_recording_7()
        print(f"✅ Extracted {len(ideas)} ideas (manually defined)")
    else:
        # For other recordings, extract simple ideas
        ideas = [{
            'title': f'Idea from Recording #{recording_id}',
            'text': recording['transcription'][:200],
            'score': 70,
            'insight': 'Auto-extracted from transcript',
            'category': 'general'
        }]
        print(f"✅ Extracted {len(ideas)} ideas (auto-generated)")

    # Show ideas
    for i, idea in enumerate(ideas, 1):
        print(f"\n  {i}. {idea['title']}")
        print(f"     Score: {idea['score']}")
        print(f"     {idea['text'][:80]}...")

    # Extract wordmap
    wordmap = extract_wordmap_from_text(recording['transcription'], top_n=20)
    print(f"\n✅ Wordmap: {len(wordmap)} words")
    print(f"   Top words: {', '.join(list(wordmap.keys())[:5])}")

    # Generate SHA256 hash
    sha256_hash = generate_sha256_hash(recording['transcription'], wordmap)
    print(f"\n✅ SHA256: {sha256_hash[:32]}...")

    # Determine brand facets based on content
    # Like "Diamond Facets" - same voice memo, different themed lens
    transcript_lower = recording['transcription'].lower()

    # @deathtodata (rebellious/critical): Anger, frustration, broken systems
    deathtodata_keywords = ['hate', 'broken', 'fake', 'cringe', 'burn', 'garbage',
                            'destroy', 'corrupt', 'bullshit', 'scam']

    # @calriven (logical/data): Analysis, metrics, proof, systematic thinking
    calriven_keywords = ['data', 'analysis', 'metrics', 'proof', 'game', 'scraped',
                        'articles', 'news', 'feeds', 'input', 'system', 'logic']

    # @soulfra (balanced/community): Trust, authentic, connection, balance
    soulfra_keywords = ['authentic', 'trust', 'community', 'genuine', 'connection',
                       'vulnerable', 'honest', 'belonging', 'real', 'truth']

    # Count keyword matches
    deathtodata_score = sum(1 for kw in deathtodata_keywords if kw in transcript_lower)
    calriven_score = sum(1 for kw in calriven_keywords if kw in transcript_lower)
    soulfra_score = sum(1 for kw in soulfra_keywords if kw in transcript_lower)

    # Route to brand with highest score
    if deathtodata_score > calriven_score and deathtodata_score > soulfra_score:
        brand_slug = 'deathtodata'
    elif calriven_score > soulfra_score:
        brand_slug = 'calriven'
    else:
        brand_slug = 'soulfra'

    print(f"✅ Brand facet: @{brand_slug}")
    print(f"   Scores: @deathtodata={deathtodata_score}, @calriven={calriven_score}, @soulfra={soulfra_score}")

    if dry_run:
        print(f"\n{'='*70}")
        print(f"  DRY RUN - Would insert into voice_suggestions")
        print(f"{'='*70}")
        return {
            'recording_id': recording_id,
            'ideas': ideas,
            'sha256_hash': sha256_hash,
            'wordmap': wordmap,
            'brand_slug': brand_slug
        }

    # Insert into voice_suggestions
    try:
        cursor = db.execute('''
            INSERT INTO voice_suggestions
            (user_id, filename, audio_path, transcription, ideas_json,
             wordmap_json, sha256_hash, brand_slug, category, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,  # user_id
            recording['filename'],
            f"recordings/{recording['filename']}",  # Assume recordings/ directory
            recording['transcription'],
            json.dumps(ideas),
            json.dumps(wordmap),
            sha256_hash,
            brand_slug,
            'social_media' if recording_id == 7 else 'general',
            'living',
            recording['created_at'] or datetime.now().isoformat()
        ))

        suggestion_id = cursor.lastrowid
        db.commit()

        print(f"\n{'='*70}")
        print(f"  ✅ INSERTED INTO voice_suggestions")
        print(f"{'='*70}")
        print(f"\nSuggestion ID: {suggestion_id}")
        print(f"View at: http://localhost:5001/suggestion-box")
        print(f"Brand view: http://localhost:5001/@{brand_slug}/suggestions")

        return {
            'suggestion_id': suggestion_id,
            'recording_id': recording_id,
            'ideas': ideas,
            'sha256_hash': sha256_hash,
            'brand_slug': brand_slug
        }

    except Exception as e:
        print(f"\n❌ Error inserting: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_all_recordings(dry_run=False):
    """Convert all recordings with transcriptions"""
    db = get_db()

    recordings = db.execute('''
        SELECT id FROM simple_voice_recordings
        WHERE transcription IS NOT NULL AND transcription != ''
        ORDER BY id
    ''').fetchall()

    print(f"\n{'='*70}")
    print(f"  Converting {len(recordings)} recordings")
    print(f"{'='*70}\n")

    results = []
    for recording in recordings:
        result = convert_recording_to_suggestion(recording['id'], dry_run=dry_run)
        if result:
            results.append(result)

    print(f"\n{'='*70}")
    print(f"  ✅ Converted {len(results)}/{len(recordings)} recordings")
    print(f"{'='*70}")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert voice recordings to suggestions'
    )

    parser.add_argument(
        '--recording',
        type=int,
        help='Convert specific recording ID'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Convert all recordings'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without inserting'
    )

    args = parser.parse_args()

    if not args.recording and not args.all:
        print("Usage:")
        print("  python3 convert_recordings_to_suggestions.py --recording 7")
        print("  python3 convert_recordings_to_suggestions.py --all")
        print("  python3 convert_recordings_to_suggestions.py --recording 7 --dry-run")
        sys.exit(1)

    if args.recording:
        result = convert_recording_to_suggestion(args.recording, dry_run=args.dry_run)
        if result and not args.dry_run:
            print(f"\n✅ Done! Visit http://localhost:5001/suggestion-box")

    elif args.all:
        results = convert_all_recordings(dry_run=args.dry_run)
        if results and not args.dry_run:
            print(f"\n✅ Done! Visit http://localhost:5001/suggestion-box")


if __name__ == '__main__':
    main()

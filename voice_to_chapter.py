#!/usr/bin/env python3
"""
Voice → Chapter Converter

Converts voice memo transcriptions into chapter snapshots:
1. Analyzes transcription content
2. Detects which domain it belongs to (from wordmap)
3. Generates markdown structure
4. Creates chapter_snapshot in database
5. Links back to original voice memo

Like: Talking to your README and it writes itself
"""

import re
import json
from database import get_db
from datetime import datetime

def detect_domain_from_transcript(transcription):
    """
    Detect which domain a voice memo belongs to based on keywords

    Args:
        transcription: Text from voice memo

    Returns:
        domain name (str) or None
    """
    text = transcription.lower()

    # Domain keyword mapping
    domain_keywords = {
        'cringeproof': ['cringe', 'anxiety', 'performance', 'voice', 'memo', 'wall'],
        'soulfra': ['soul', 'identity', 'keys', 'privacy', 'auth', 'ai'],
        'calriven': ['calendar', 'schedule', 'planning', 'cal', 'time', 'event'],
        'deathtodata': ['death', 'data', 'privacy', 'tracking', 'surveillance', 'homebrew', 'lab']
    }

    # Score each domain
    scores = {}
    for domain, keywords in domain_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        scores[domain] = score

    # Get highest scoring domain
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)

    return None  # No clear match

def transcription_to_markdown(transcription, title=None):
    """
    Convert voice transcription to structured markdown

    Heuristics:
    - First sentence = title (if not provided)
    - Paragraphs separated by long pauses (. or !)
    - Technical terms = code blocks
    - Lists detected from "first, second, third" or bullet points

    Args:
        transcription: Raw transcription text
        title: Optional title override

    Returns:
        markdown string
    """
    lines = transcription.split('\n')
    text = ' '.join(lines)

    # Extract title from first sentence if not provided
    if not title:
        first_sentence_match = re.match(r'^([^.!?]+)[.!?]', text)
        if first_sentence_match:
            title = first_sentence_match.group(1).strip()
        else:
            title = "Voice Chapter"

    # Split into paragraphs (sentences)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Build markdown
    markdown = f"# {title}\n\n"
    markdown += f"> Generated from voice memo on {datetime.now().strftime('%Y-%m-%d')}\n\n"

    # Group sentences into paragraphs (every 2-3 sentences)
    paragraphs = []
    current_para = []

    for sentence in sentences:
        current_para.append(sentence)

        # New paragraph every 2-3 sentences
        if len(current_para) >= 2:
            paragraphs.append('. '.join(current_para) + '.')
            current_para = []

    # Add remaining sentences
    if current_para:
        paragraphs.append('. '.join(current_para) + '.')

    # Write paragraphs
    for para in paragraphs:
        # Detect code/technical terms (words with underscores or camelCase)
        if re.search(r'[a-z][A-Z]|_[a-z]', para):
            # Wrap technical paragraph in code block
            markdown += f"```\n{para}\n```\n\n"
        else:
            markdown += f"{para}\n\n"

    return markdown

def create_chapter_from_voice(recording_id, user_id=None, domain=None, title=None):
    """
    Create a chapter_snapshot from a voice recording

    Args:
        recording_id: ID from simple_voice_recordings
        user_id: User who created it
        domain: Domain to assign (auto-detected if None)
        title: Chapter title (auto-generated if None)

    Returns:
        dict with chapter info or error
    """
    db = get_db()

    # Get voice recording
    recording = db.execute('''
        SELECT id, transcription, user_id, domain, created_at
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return {'success': False, 'error': f'Recording {recording_id} not found'}

    if not recording['transcription']:
        return {'success': False, 'error': 'Recording has no transcription'}

    # Detect domain if not provided
    if not domain:
        domain = detect_domain_from_transcript(recording['transcription'])
        if not domain:
            domain = recording['domain'] or 'soulfra'  # Fallback

    # Convert to markdown
    markdown = transcription_to_markdown(recording['transcription'], title=title)

    # Get next chapter number (global across all domains)
    max_chapter = db.execute('''
        SELECT MAX(chapter_num) as max_num
        FROM chapter_snapshots
    ''').fetchone()

    chapter_num = (max_chapter['max_num'] or 0) + 1

    # Create chapter snapshot
    cursor = db.execute('''
        INSERT INTO chapter_snapshots
        (chapter_num, version_num, title, content, commit_message, created_by_user_id, is_fork, fork_source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        chapter_num,
        1,  # First version
        title or f"{domain.capitalize()} - Voice Chapter {chapter_num}",
        markdown,
        f"Generated from voice recording #{recording_id}",
        user_id or recording['user_id'],
        0,  # Not a fork
        None  # No fork source
    ))

    chapter_id = cursor.lastrowid
    db.commit()

    return {
        'success': True,
        'chapter_id': chapter_id,
        'chapter_num': chapter_num,
        'domain': domain,
        'title': title or f"{domain.capitalize()} - Voice Chapter {chapter_num}",
        'recording_id': recording_id,
        'markdown_preview': markdown[:200] + '...'
    }

def batch_convert_voice_to_chapters(limit=10, domain_filter=None):
    """
    Convert recent voice memos to chapters (batch processing)

    Args:
        limit: Max number to convert
        domain_filter: Only convert specific domain

    Returns:
        list of results
    """
    db = get_db()

    # Find voice recordings not yet converted to chapters
    query = '''
        SELECT r.id, r.transcription, r.user_id, r.domain, r.created_at
        FROM simple_voice_recordings r
        WHERE r.transcription IS NOT NULL
        AND r.transcription != ''
        AND NOT EXISTS (
            SELECT 1 FROM chapter_snapshots c
            WHERE c.commit_message LIKE '%recording #' || r.id || '%'
        )
        ORDER BY r.created_at DESC
        LIMIT ?
    '''

    recordings = db.execute(query, (limit,)).fetchall()

    results = []
    for recording in recordings:
        # Skip if domain filter doesn't match
        if domain_filter and recording['domain'] != domain_filter:
            continue

        result = create_chapter_from_voice(
            recording['id'],
            user_id=recording['user_id'],
            domain=recording['domain']
        )
        results.append(result)

    return results

def main():
    import sys

    if '--batch' in sys.argv:
        # Batch convert recent voice memos
        limit = int(sys.argv[sys.argv.index('--batch') + 1]) if '--batch' in sys.argv and len(sys.argv) > sys.argv.index('--batch') + 1 else 10

        print(f"🔄 Converting up to {limit} voice memos to chapters...\n")
        results = batch_convert_voice_to_chapters(limit=limit)

        print(f"\n{'='*60}")
        print(f"✅ Converted {len([r for r in results if r['success']])} voice memos")
        print(f"❌ Failed {len([r for r in results if not r['success']])}")

        for result in results:
            if result['success']:
                print(f"   ✅ Recording #{result['recording_id']} → Chapter #{result['chapter_num']} ({result['domain']})")

    elif '--recording' in sys.argv:
        # Convert specific recording
        idx = sys.argv.index('--recording')
        if idx + 1 < len(sys.argv):
            recording_id = int(sys.argv[idx + 1])
            result = create_chapter_from_voice(recording_id)
            print(json.dumps(result, indent=2))
        else:
            print("❌ Usage: python3 voice_to_chapter.py --recording RECORDING_ID")

    else:
        print("Usage:")
        print("  python3 voice_to_chapter.py --batch [LIMIT]")
        print("  python3 voice_to_chapter.py --recording RECORDING_ID")

if __name__ == '__main__':
    main()

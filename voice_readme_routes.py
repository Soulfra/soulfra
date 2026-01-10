"""
Voice → README API Routes

Talk to your README via voice memos:
1. Record voice memo on phone
2. Auto-transcribes
3. Updates README content
4. Syncs to GitHub (via local git)

Like: Your README is a phone number you can call
"""

from flask import Blueprint, request, jsonify
from database import get_db
from voice_to_chapter import create_chapter_from_voice, detect_domain_from_transcript
from readme_chapter_sync import chapter_to_readme
from datetime import datetime

voice_readme_bp = Blueprint('voice_readme', __name__)

@voice_readme_bp.route('/api/voice-to-readme', methods=['POST'])
def voice_to_readme():
    """
    Convert voice memo directly to README update

    Body:
    {
        "recording_id": 16,
        "domain": "soulfra",  // optional, auto-detected if not provided
        "mode": "append"      // "append", "replace", or "chapter"
    }

    Returns:
    {
        "success": true,
        "domain": "soulfra",
        "chapter_id": 12,
        "readme_updated": true,
        "preview": "..."
    }
    """
    data = request.json
    recording_id = data.get('recording_id')
    domain = data.get('domain')
    mode = data.get('mode', 'chapter')  # Default: create chapter

    if not recording_id:
        return jsonify({'success': False, 'error': 'recording_id required'}), 400

    db = get_db()

    # Get recording
    recording = db.execute('''
        SELECT id, transcription, user_id, domain as recording_domain
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return jsonify({'success': False, 'error': f'Recording {recording_id} not found'}), 404

    if not recording['transcription']:
        return jsonify({'success': False, 'error': 'Recording has no transcription'}), 400

    # Detect domain if not provided
    if not domain:
        domain = detect_domain_from_transcript(recording['transcription'])
        if not domain:
            domain = recording['recording_domain'] or 'soulfra'

    # Mode 1: Create chapter (default)
    if mode == 'chapter':
        result = create_chapter_from_voice(
            recording_id,
            user_id=recording['user_id'],
            domain=domain
        )

        if not result['success']:
            return jsonify(result), 500

        return jsonify({
            'success': True,
            'mode': 'chapter',
            'domain': domain,
            'chapter_id': result['chapter_id'],
            'chapter_num': result['chapter_num'],
            'title': result['title'],
            'preview': result['markdown_preview']
        })

    # Mode 2: Append to existing README
    elif mode == 'append':
        # Get current README chapter
        readme_chapter = db.execute('''
            SELECT id, content
            FROM chapter_snapshots
            WHERE title LIKE ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (f'%{domain}%README%',)).fetchone()

        if not readme_chapter:
            return jsonify({'success': False, 'error': f'No README chapter found for {domain}'}), 404

        # Append voice content
        from voice_to_chapter import transcription_to_markdown
        voice_markdown = transcription_to_markdown(recording['transcription'])

        updated_content = readme_chapter['content'] + f"\n\n## Voice Update ({datetime.now().strftime('%Y-%m-%d')})\n\n" + voice_markdown

        # Create new version
        cursor = db.execute('''
            INSERT INTO chapter_snapshots
            (chapter_num, version_num, title, content, commit_message, created_by_user_id, is_fork, fork_source_id)
            SELECT chapter_num, version_num + 1, title, ?, ?, created_by_user_id, 0, NULL
            FROM chapter_snapshots
            WHERE id = ?
        ''', (
            updated_content,
            f"Appended voice memo #{recording_id}",
            readme_chapter['id']
        ))

        new_chapter_id = cursor.lastrowid
        db.commit()

        return jsonify({
            'success': True,
            'mode': 'append',
            'domain': domain,
            'chapter_id': new_chapter_id,
            'preview': updated_content[:300] + '...'
        })

    # Mode 3: Replace README entirely
    elif mode == 'replace':
        from voice_to_chapter import transcription_to_markdown

        voice_markdown = transcription_to_markdown(
            recording['transcription'],
            title=f"{domain.capitalize()} README"
        )

        # Get next chapter number
        max_chapter = db.execute('SELECT MAX(chapter_num) as max_num FROM chapter_snapshots').fetchone()
        chapter_num = (max_chapter['max_num'] or 0) + 1

        cursor = db.execute('''
            INSERT INTO chapter_snapshots
            (chapter_num, version_num, title, content, commit_message, created_by_user_id, is_fork, fork_source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            chapter_num,
            1,
            f"{domain.capitalize()} README",
            voice_markdown,
            f"Replaced README from voice memo #{recording_id}",
            recording['user_id'],
            0,
            None
        ))

        new_chapter_id = cursor.lastrowid
        db.commit()

        return jsonify({
            'success': True,
            'mode': 'replace',
            'domain': domain,
            'chapter_id': new_chapter_id,
            'chapter_num': chapter_num,
            'preview': voice_markdown[:300] + '...'
        })

    else:
        return jsonify({'success': False, 'error': f'Invalid mode: {mode}'}), 400


@voice_readme_bp.route('/api/readme-status/<domain>', methods=['GET'])
def readme_status(domain):
    """
    Get current README status for a domain

    Returns:
    {
        "domain": "soulfra",
        "current_chapter_id": 11,
        "version_num": 1,
        "last_updated": "2026-01-04 12:34:56",
        "word_count": 245,
        "voice_contributions": 3
    }
    """
    db = get_db()

    # Find latest README chapter (try README first, then domain name)
    readme_chapter = db.execute('''
        SELECT id, chapter_num, version_num, title, content, created_at
        FROM chapter_snapshots
        WHERE (title LIKE ? OR title LIKE ? OR title = ?)
        AND commit_message LIKE '%README%'
        ORDER BY created_at DESC
        LIMIT 1
    ''', (f'%{domain}%README%', f'%{domain.capitalize()}%', domain.capitalize())).fetchone()

    if not readme_chapter:
        return jsonify({'success': False, 'error': f'No README found for {domain}'}), 404

    # Count voice contributions
    voice_count = db.execute('''
        SELECT COUNT(*) as count
        FROM chapter_snapshots
        WHERE commit_message LIKE '%voice%'
        AND (title LIKE ? OR commit_message LIKE ?)
    ''', (f'%{domain}%', f'%{domain}%')).fetchone()

    word_count = len(readme_chapter['content'].split())

    return jsonify({
        'success': True,
        'domain': domain,
        'current_chapter_id': readme_chapter['id'],
        'chapter_num': readme_chapter['chapter_num'],
        'version_num': readme_chapter['version_num'],
        'title': readme_chapter['title'],
        'last_updated': readme_chapter['created_at'],
        'word_count': word_count,
        'voice_contributions': voice_count['count'],
        'preview': readme_chapter['content'][:200] + '...'
    })


@voice_readme_bp.route('/api/readme-history/<domain>', methods=['GET'])
def readme_history(domain):
    """
    Get version history for domain's README

    Returns list of all README versions with diffs
    """
    db = get_db()

    versions = db.execute('''
        SELECT id, chapter_num, version_num, title, created_at, commit_message,
               LENGTH(content) as content_length
        FROM chapter_snapshots
        WHERE title LIKE ? OR commit_message LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{domain}%README%', f'%{domain}%')).fetchall()

    return jsonify({
        'success': True,
        'domain': domain,
        'version_count': len(versions),
        'versions': [
            {
                'chapter_id': v['id'],
                'chapter_num': v['chapter_num'],
                'version_num': v['version_num'],
                'title': v['title'],
                'created_at': v['created_at'],
                'commit_message': v['commit_message'],
                'content_length': v['content_length']
            }
            for v in versions
        ]
    })

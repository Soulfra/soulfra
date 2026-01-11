#!/usr/bin/env python3
"""
Voice Bank Routes - Dashboard for voice recordings

Shows:
- All recordings with audio player
- Transcriptions
- Wordmaps
- Domain matches
- Ownership earned
- Storage info
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from database import get_db
import json

voice_bank_bp = Blueprint('voice_bank', __name__)


@voice_bank_bp.route('/voice-bank')
def voice_bank():
    """Voice Bank Dashboard - See all your voice recordings"""
    # Development mode: bypass login if no session exists
    if 'user_id' not in session:
        # Default to user_id=1 for development
        user_id = 1
    else:
        user_id = session['user_id']

    db = get_db()

    # Get all recordings for user
    recordings = db.execute('''
        SELECT id, filename, transcription, file_size, created_at
        FROM simple_voice_recordings
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    recordings_data = []
    for rec in recordings:
        # Get wordmap for this recording (if extracted)
        # For now, show global wordmap
        wordmap_row = db.execute('''
            SELECT wordmap_json
            FROM user_wordmaps
            WHERE user_id = ?
        ''', (user_id,)).fetchone()

        wordmap = {}
        if wordmap_row and wordmap_row['wordmap_json']:
            wordmap = json.loads(wordmap_row['wordmap_json'])

        # Count unique words
        transcript = rec['transcription'] or ''
        word_count = len(set(transcript.split()))

        recordings_data.append({
            'id': rec['id'],
            'filename': rec['filename'],
            'transcription': transcript,
            'transcript_length': len(transcript),
            'word_count': word_count,
            'file_size': rec['file_size'],
            'created_at': rec['created_at'],
            'has_transcript': bool(transcript)
        })

    # Get user's wordmap
    wordmap_row = db.execute('''
        SELECT wordmap_json, recording_count
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    wordmap_data = {}
    if wordmap_row and wordmap_row['wordmap_json']:
        wordmap = json.loads(wordmap_row['wordmap_json'])
        top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:20]
        wordmap_data = {
            'top_words': top_words,
            'total_words': len(wordmap),
            'total_recordings': wordmap_row['recording_count'] or 0
        }

    # Get domain ownership
    owned_domains = db.execute('''
        SELECT dc.domain, dc.tier, do.ownership_percentage
        FROM domain_ownership do
        JOIN domain_contexts dc ON do.domain_id = dc.id
        WHERE do.user_id = ? AND do.ownership_percentage > 0
        ORDER BY do.ownership_percentage DESC
    ''', (user_id,)).fetchall()

    # Calculate totals
    total_recordings = len(recordings)
    total_audio_bytes = sum(r['file_size'] for r in recordings_data)
    total_transcript_chars = sum(r['transcript_length'] for r in recordings_data)

    return render_template('voice_bank.html',
                         recordings=recordings_data,
                         total_recordings=total_recordings,
                         total_audio_bytes=total_audio_bytes,
                         total_transcript_chars=total_transcript_chars,
                         wordmap=wordmap_data,
                         owned_domains=[dict(d) for d in owned_domains],
                         user_id=user_id)


@voice_bank_bp.route('/voice-bank/<int:recording_id>/audio')
def get_recording_audio(recording_id):
    """Serve audio file for a recording"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    user_id = session['user_id']

    # Get recording
    rec = db.execute('''
        SELECT audio_data, filename
        FROM simple_voice_recordings
        WHERE id = ? AND user_id = ?
    ''', (recording_id, user_id)).fetchone()

    if not rec or not rec['audio_data']:
        return jsonify({'error': 'Recording not found'}), 404

    # Return audio file
    from flask import Response
    return Response(rec['audio_data'], mimetype='audio/webm')

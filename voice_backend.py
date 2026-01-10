#!/usr/bin/env python3
"""
Voice Backend API - Simple Flask API for Voice Memos

Handles:
- Save audio + transcription to database
- List all memos
- Get token count
- Playback audio

Usage:
    python3 voice_backend.py

Runs on: http://localhost:5002
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import io

app = Flask(__name__)
CORS(app)  # Allow requests from localhost:8080

DATABASE = 'soulfra.db'
AUDIO_DIR = 'voice_audio'

# Create audio directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/api/voice/save', methods=['POST'])
def save_voice_memo():
    """
    Save voice memo to database

    Expected form data:
    - audio: Audio file (webm/wav/mp3)
    - transcription: Text transcription
    - tokens: Number of tokens used

    Returns:
    {
        "success": true,
        "id": 123,
        "tokens": 2
    }
    """
    try:
        # Get form data
        audio_file = request.files.get('audio')
        transcription = request.form.get('transcription', '')
        tokens = int(request.form.get('tokens', 1))

        if not transcription:
            return jsonify({'success': False, 'error': 'No transcription provided'}), 400

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'voice_memo_{timestamp}.webm'
        filepath = os.path.join(AUDIO_DIR, filename)

        # Save audio file
        audio_blob = None
        if audio_file:
            audio_file.save(filepath)
            # Also save to database as blob
            audio_blob = audio_file.read()
            audio_file.seek(0)  # Reset for saving to file
            audio_file.save(filepath)

        # Insert into database
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO voice_memos (
                audio_filename,
                audio_blob,
                transcription,
                tokens_used,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            filename,
            audio_blob,
            transcription,
            tokens,
            datetime.now().isoformat()
        ))

        memo_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'id': memo_id,
            'tokens': tokens,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/voice/memos', methods=['GET'])
def get_voice_memos():
    """
    Get all voice memos

    Returns:
    [
        {
            "id": 1,
            "transcription": "Hello world",
            "tokens_used": 1,
            "created_at": "2026-01-11T10:30:00",
            "audio_filename": "voice_memo_20260111_103000.webm",
            "github_gist_url": "https://gist.github.com/..."
        }
    ]
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                audio_filename,
                transcription,
                github_gist_id,
                github_gist_url,
                tokens_used,
                created_at
            FROM voice_memos
            ORDER BY created_at DESC
            LIMIT 50
        """)

        memos = []
        for row in cursor.fetchall():
            memos.append({
                'id': row['id'],
                'audio_filename': row['audio_filename'],
                'transcription': row['transcription'],
                'github_gist_id': row['github_gist_id'],
                'github_gist_url': row['github_gist_url'],
                'tokens_used': row['tokens_used'],
                'created_at': row['created_at']
            })

        conn.close()

        return jsonify(memos)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/tokens', methods=['GET'])
def get_token_count():
    """
    Get total tokens used

    Returns:
    {
        "total_tokens": 42,
        "memo_count": 15
    }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COALESCE(SUM(tokens_used), 0) as total_tokens,
                COUNT(*) as memo_count
            FROM voice_memos
        """)

        row = cursor.fetchone()
        conn.close()

        return jsonify({
            'total_tokens': row['total_tokens'],
            'memo_count': row['memo_count']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/audio/<int:memo_id>', methods=['GET'])
def get_audio(memo_id):
    """
    Get audio file for a memo

    Returns:
    Binary audio file (webm)
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT audio_filename, audio_blob
            FROM voice_memos
            WHERE id = ?
        """, (memo_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Memo not found'}), 404

        # Return file from disk if exists
        if row['audio_filename']:
            filepath = os.path.join(AUDIO_DIR, row['audio_filename'])
            if os.path.exists(filepath):
                return send_file(filepath, mimetype='audio/webm')

        # Fallback to blob
        if row['audio_blob']:
            return send_file(
                io.BytesIO(row['audio_blob']),
                mimetype='audio/webm',
                as_attachment=True,
                download_name=f'memo_{memo_id}.webm'
            )

        return jsonify({'error': 'Audio not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/gist', methods=['POST'])
def update_gist_url():
    """
    Update GitHub Gist URL for a memo

    Request body:
    {
        "memo_id": 123,
        "gist_id": "abc123",
        "gist_url": "https://gist.github.com/user/abc123"
    }
    """
    try:
        data = request.json
        memo_id = data.get('memo_id')
        gist_id = data.get('gist_id')
        gist_url = data.get('gist_url')

        if not memo_id:
            return jsonify({'success': False, 'error': 'memo_id required'}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE voice_memos
            SET
                github_gist_id = ?,
                github_gist_url = ?
            WHERE id = ?
        """, (gist_id, gist_url, memo_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'database': DATABASE,
        'audio_dir': AUDIO_DIR
    })


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     VOICE BACKEND API                                        ║
║     Simple Flask API for Voice Memos                         ║
╚═══════════════════════════════════════════════════════════════╝

Database:    {database}
Audio Dir:   {audio_dir}
Port:        5002

API Endpoints:
  POST   /api/voice/save     - Save voice memo
  GET    /api/voice/memos    - List all memos
  GET    /api/voice/tokens   - Get token count
  GET    /api/voice/audio/<id> - Get audio file
  POST   /api/voice/gist     - Update gist URL
  GET    /health             - Health check

Frontend: http://localhost:8080/voice-integrated.html

Ready! Press Ctrl+C to stop.
    """.format(
        database=DATABASE,
        audio_dir=AUDIO_DIR
    ))

    app.run(
        host='0.0.0.0',
        port=5002,
        debug=True
    )

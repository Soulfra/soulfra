#!/usr/bin/env python3
"""
Voice CAPTCHA - Voice-based brand verification

Instead of "click all traffic lights", users prove they're human by:
1. Scanning a QR code (device fingerprinting)
2. Recording a challenge phrase
3. Whisper transcribes the audio
4. System verifies match and awards trust score

Features:
- Random challenge phrases (Soulfra-themed)
- Voice match verification
- Trust score bonus (+15 for voice completion)
- Works with existing QR auth system
"""

from flask import Blueprint, render_template, request, jsonify, session
from database import get_db
import secrets
import tempfile
import os
from datetime import datetime
from typing import Dict, Optional

voice_captcha_bp = Blueprint('voice_captcha', __name__)

# Soulfra-themed challenge phrases
CHALLENGE_PHRASES = [
    "soulfra is building the future",
    "authentic creativity starts here",
    "no corporate bullshit allowed",
    "voice powered collaboration",
    "real people real projects",
    "decentralized creative freedom",
    "build what matters to you",
    "your ideas your control",
    "technology meets soul",
    "fuck yeah let's create"
]


def generate_voice_challenge() -> Dict:
    """
    Generate a new voice CAPTCHA challenge

    Returns:
        {
            'challenge_id': str (unique token),
            'phrase': str (what user should say),
            'expires_at': str (ISO timestamp)
        }
    """
    import time

    challenge_id = secrets.token_urlsafe(32)
    phrase = secrets.choice(CHALLENGE_PHRASES)
    expires_at = int(time.time()) + 300  # 5 minutes

    db = get_db()
    db.execute('''
        INSERT INTO voice_captcha_challenges (challenge_id, phrase, expires_at)
        VALUES (?, ?, ?)
    ''', (challenge_id, phrase, expires_at))
    db.commit()
    db.close()

    return {
        'challenge_id': challenge_id,
        'phrase': phrase,
        'expires_at': expires_at
    }


def verify_voice_challenge(challenge_id: str, audio_data: bytes, device_fingerprint: Optional[Dict] = None) -> Dict:
    """
    Verify voice CAPTCHA by transcribing audio and comparing to expected phrase

    Args:
        challenge_id: Challenge token
        audio_data: Recorded audio (webm)
        device_fingerprint: Optional device info for trust scoring

    Returns:
        {
            'success': bool,
            'match_score': int (0-100),
            'transcription': str (what was heard),
            'expected': str (what should have been said),
            'trust_score': int (0-100),
            'verdict': str (approve/challenge/reject)
        }
    """
    db = get_db()

    # Get challenge
    challenge = db.execute('''
        SELECT phrase, expires_at, used
        FROM voice_captcha_challenges
        WHERE challenge_id = ?
    ''', (challenge_id,)).fetchone()

    if not challenge:
        db.close()
        return {
            'success': False,
            'error': 'Challenge not found',
            'trust_score': 0,
            'verdict': 'reject'
        }

    if challenge['used']:
        db.close()
        return {
            'success': False,
            'error': 'Challenge already used',
            'trust_score': 0,
            'verdict': 'reject'
        }

    import time
    if time.time() > challenge['expires_at']:
        db.close()
        return {
            'success': False,
            'error': 'Challenge expired',
            'trust_score': 0,
            'verdict': 'reject'
        }

    expected_phrase = challenge['phrase']

    # Transcribe audio with Whisper
    transcription = None
    transcription_method = None

    try:
        from whisper_transcriber import WhisperTranscriber

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        # Transcribe
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(tmp_path)

        transcription = result['text'].strip().lower()
        transcription_method = result['backend']

        # Clean up temp file
        os.unlink(tmp_path)

    except Exception as e:
        db.close()
        return {
            'success': False,
            'error': f'Transcription failed: {str(e)}',
            'trust_score': 0,
            'verdict': 'reject'
        }

    # Calculate match score using fuzzy matching
    match_score = calculate_phrase_match(expected_phrase.lower(), transcription)

    # Determine if voice matches well enough (70% threshold)
    voice_verified = match_score >= 70

    # Calculate trust score
    base_trust_score = 50  # Base score

    if voice_verified:
        base_trust_score += 15  # Voice bonus

    # Add device fingerprint bonus if provided
    if device_fingerprint:
        from archive.experiments.qr_captcha import calculate_device_trust_score
        device_trust = calculate_device_trust_score(device_fingerprint)
        base_trust_score += device_trust['score'] // 5  # Up to +20 from device

    # Cap at 100
    total_trust_score = min(100, base_trust_score)

    # Determine verdict
    if total_trust_score >= 70:
        verdict = 'approve'
    elif total_trust_score >= 40:
        verdict = 'challenge'  # Maybe ask for another verification
    else:
        verdict = 'reject'

    # Mark challenge as used
    db.execute('''
        UPDATE voice_captcha_challenges
        SET used = 1, verified_at = ?, transcription = ?, match_score = ?
        WHERE challenge_id = ?
    ''', (datetime.now().isoformat(), transcription, match_score, challenge_id))
    db.commit()
    db.close()

    return {
        'success': voice_verified,
        'match_score': match_score,
        'transcription': transcription,
        'expected': expected_phrase,
        'trust_score': total_trust_score,
        'verdict': verdict,
        'voice_verified': voice_verified
    }


def calculate_phrase_match(expected: str, actual: str) -> int:
    """
    Calculate how well the transcription matches the expected phrase

    Uses simple word-level matching (could be enhanced with fuzzy matching)

    Args:
        expected: Expected phrase
        actual: Transcribed phrase

    Returns:
        Match score 0-100
    """
    # Normalize
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())

    if not expected_words:
        return 0

    # Count matching words
    matching_words = expected_words & actual_words
    match_percentage = (len(matching_words) / len(expected_words)) * 100

    # Bonus if exact match
    if expected.lower() == actual.lower():
        return 100

    # Bonus if very close (contains all words in order)
    if expected.lower() in actual.lower() or actual.lower() in expected.lower():
        match_percentage = max(match_percentage, 90)

    return int(match_percentage)


# Flask Routes

@voice_captcha_bp.route('/captcha/voice')
def voice_captcha_page():
    """
    Voice CAPTCHA page

    Shows challenge phrase and voice recorder
    """
    # Generate new challenge
    challenge = generate_voice_challenge()

    return render_template('voice_captcha.html',
        challenge_id=challenge['challenge_id'],
        phrase=challenge['phrase'],
        expires_at=challenge['expires_at']
    )


@voice_captcha_bp.route('/api/captcha/voice/challenge', methods=['POST'])
def create_voice_challenge():
    """
    Create a new voice CAPTCHA challenge

    Returns:
    {
        "challenge_id": "...",
        "phrase": "soulfra is building the future",
        "expires_at": 1234567890
    }
    """
    challenge = generate_voice_challenge()

    return jsonify({
        'success': True,
        **challenge
    })


@voice_captcha_bp.route('/api/captcha/voice/verify', methods=['POST'])
def verify_voice_captcha():
    """
    Verify voice CAPTCHA by submitting audio

    Expects multipart form data:
    - challenge_id: str
    - audio: file (webm)
    - device_fingerprint: optional JSON

    Returns:
    {
        "success": true,
        "match_score": 95,
        "trust_score": 85,
        "verdict": "approve",
        "transcription": "soulfra is building the future",
        "voice_verified": true
    }
    """
    challenge_id = request.form.get('challenge_id')

    if not challenge_id:
        return jsonify({'error': 'Missing challenge_id'}), 400

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'error': 'Empty audio file'}), 400

    # Get device fingerprint if provided
    device_fingerprint = None
    if 'device_fingerprint' in request.form:
        import json
        try:
            device_fingerprint = json.loads(request.form['device_fingerprint'])
        except:
            pass

    # Verify
    result = verify_voice_challenge(challenge_id, audio_data, device_fingerprint)

    return jsonify(result)


@voice_captcha_bp.route('/api/captcha/voice/init-db', methods=['POST'])
def init_voice_captcha_db():
    """
    Initialize voice CAPTCHA database table

    Creates:
    - voice_captcha_challenges table
    """
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_captcha_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id TEXT UNIQUE NOT NULL,
            phrase TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP,
            transcription TEXT,
            match_score INTEGER
        )
    ''')

    db.commit()
    db.close()

    return jsonify({'success': True, 'message': 'Voice CAPTCHA table created'})


def register_voice_captcha_routes(app):
    """Register voice CAPTCHA routes"""
    app.register_blueprint(voice_captcha_bp)
    print("✅ Voice CAPTCHA routes registered:")
    print("   - /captcha/voice (Voice CAPTCHA page)")
    print("   - /api/captcha/voice/challenge (Create challenge)")
    print("   - /api/captcha/voice/verify (Verify voice)")
    print("   - /api/captcha/voice/init-db (Initialize database)")


if __name__ == '__main__':
    # CLI test
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 voice_captcha.py init  # Initialize database")
        print("  python3 voice_captcha.py challenge  # Generate challenge")
        sys.exit(1)

    if sys.argv[1] == 'init':
        # Initialize database
        import sqlite3
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_captcha_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id TEXT UNIQUE NOT NULL,
                phrase TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                transcription TEXT,
                match_score INTEGER
            )
        ''')

        conn.commit()
        conn.close()

        print("✅ Voice CAPTCHA table created")

    elif sys.argv[1] == 'challenge':
        # Generate a challenge
        challenge = generate_voice_challenge()
        print(f"\nChallenge ID: {challenge['challenge_id']}")
        print(f"Phrase: {challenge['phrase']}")
        print(f"Expires: {challenge['expires_at']}\n")

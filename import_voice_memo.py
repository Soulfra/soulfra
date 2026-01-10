#!/usr/bin/env python3
"""
Import Voice Memo - Dead Simple

Drag audio file → Auto-transcribe → Save to database

Usage:
    python3 import_voice_memo.py audio.m4a
    python3 import_voice_memo.py recording.wav
    python3 import_voice_memo.py voice-memo.webm

No server, no SSL, no networking. Just files.
"""

import sys
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

def transcribe_audio(audio_path):
    """Transcribe audio file with Whisper"""
    try:
        from whisper_transcriber import WhisperTranscriber
        from audio_enhancer import AudioEnhancer

        print(f"🎧 Enhancing audio quality...")
        enhancer = AudioEnhancer()
        enhance_result = enhancer.enhance(audio_path)

        audio_to_transcribe = enhance_result.get('output_path', audio_path) if enhance_result.get('success') else audio_path

        print(f"📝 Transcribing with Whisper...")
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(audio_to_transcribe)

        print(f"✅ Transcription complete: {result['backend']}")
        return result['text'], result['backend']

    except Exception as e:
        print(f"⚠️  Transcription failed: {e}")
        print(f"   Continuing without transcription...")
        return None, None


def calculate_sha256(file_path):
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def import_voice_memo(audio_path):
    """Import voice memo from file"""

    audio_path = Path(audio_path)

    if not audio_path.exists():
        print(f"❌ File not found: {audio_path}")
        sys.exit(1)

    print(f"📂 Importing: {audio_path.name}")
    print(f"   Size: {audio_path.stat().st_size / 1024:.1f} KB")

    # Read audio data
    with open(audio_path, 'rb') as f:
        audio_data = f.read()

    # Calculate hash
    sha256_hash = calculate_sha256(audio_path)
    print(f"🔐 SHA-256: {sha256_hash[:16]}...")

    # Transcribe
    transcription, transcription_method = transcribe_audio(str(audio_path))

    if transcription:
        print(f"📄 Transcript: {transcription[:100]}...")
    else:
        print(f"📄 No transcription available")

    # Save to database
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row

    # Check if already exists
    existing = db.execute('''
        SELECT id FROM simple_voice_recordings
        WHERE LENGTH(audio_data) = ? AND transcription = ?
    ''', (len(audio_data), transcription)).fetchone()

    if existing:
        print(f"⏭️  Already imported (ID: {existing['id']})")
        db.close()
        return existing['id']

    # Get or create user
    user = db.execute('SELECT id FROM users WHERE username = ?', ('local_import',)).fetchone()

    if not user:
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('local_import', 'import@local.voice', 'local-file-import'))
        user_id = cursor.lastrowid
        db.commit()
    else:
        user_id = user['id']

    # Insert recording
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (
            filename,
            audio_data,
            file_size,
            transcription,
            transcription_method,
            user_id,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        audio_path.name,
        audio_data,
        len(audio_data),
        transcription,
        transcription_method,
        user_id,
        datetime.now().isoformat()
    ))

    recording_id = cursor.lastrowid
    db.commit()

    print(f"✅ Saved to database (ID: {recording_id})")

    # Also save to voice_suggestions for /suggestion-box
    print(f"📤 Publishing to suggestion box...")

    # Determine brand routing
    brand_slug = None
    if transcription:
        text = transcription.lower()

        calriven_keywords = ['data', 'analysis', 'metrics', 'proof', 'game', 'scraped',
                           'articles', 'news', 'feeds', 'input', 'system', 'logic', 'cringeproof']
        calriven_score = sum(1 for kw in calriven_keywords if kw in text)

        deathtodata_keywords = ['hate', 'broken', 'fake', 'cringe', 'burn', 'garbage',
                               'destroy', 'corrupt', 'bullshit', 'scam']
        deathtodata_score = sum(1 for kw in deathtodata_keywords if kw in text)

        soulfra_keywords = ['authentic', 'trust', 'community', 'genuine', 'connection',
                          'vulnerable', 'honest', 'belonging', 'real', 'truth']
        soulfra_score = sum(1 for kw in soulfra_keywords if kw in text)

        if deathtodata_score > calriven_score and deathtodata_score > soulfra_score:
            brand_slug = 'deathtodata'
        elif calriven_score > soulfra_score:
            brand_slug = 'calriven'
        elif soulfra_score > 0:
            brand_slug = 'soulfra'

    # Save audio file
    import os
    os.makedirs('suggestion-box', exist_ok=True)
    audio_file_path = f'suggestion-box/{sha256_hash[:8]}{audio_path.suffix}'

    with open(audio_file_path, 'wb') as f:
        f.write(audio_data)

    # Insert into voice_suggestions
    db.execute('''
        INSERT INTO voice_suggestions (
            user_id,
            filename,
            audio_path,
            transcription,
            sha256_hash,
            brand_slug,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        audio_path.name,
        audio_file_path,
        transcription,
        sha256_hash,
        brand_slug,
        datetime.now().isoformat()
    ))

    db.commit()
    db.close()

    print(f"✅ Published to /suggestion-box")
    if brand_slug:
        print(f"🎯 Routed to: @{brand_slug}")
    else:
        print(f"🎯 No brand routing (add keywords to transcript)")

    print("")
    print("="*60)
    print(f"✅ Import complete!")
    print(f"   View at: http://localhost:5001/suggestion-box")
    if brand_slug:
        print(f"   Or: http://localhost:5001/@{brand_slug}/suggestions")
    print("="*60)
    print("")
    print("📤 Next: Publish to GitHub Pages:")
    print(f"   python3 publish_voice_archive.py")
    print("")

    return recording_id


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 import_voice_memo.py <audio_file>")
        print("")
        print("Examples:")
        print("  python3 import_voice_memo.py recording.m4a")
        print("  python3 import_voice_memo.py voice-memo.wav")
        print("  python3 import_voice_memo.py idea.webm")
        print("")
        print("Supported formats: .m4a, .wav, .webm, .mp3, .ogg")
        sys.exit(1)

    audio_file = sys.argv[1]
    import_voice_memo(audio_file)

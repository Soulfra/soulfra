#!/usr/bin/env python3
"""
Voice Input System - Offline-First Audio Handling

This implements an offline-first voice input system:
1. Store audio files locally
2. Queue for transcription (offline or online)
3. Manage transcription results
4. Support manual transcription
5. Export for external transcription services

WHY THIS EXISTS:
- Record ideas/notes via voice
- Works offline (store for later transcription)
- Support both auto and manual transcription
- No external dependencies for storage
- Queue-based transcription system

Note: Python stdlib doesn't include audio recording or speech recognition.
This module provides the framework and queue system. For actual recording:
- macOS: Use subprocess to call 'rec' or 'sox' if installed
- Or: Use any audio recording tool, then import files
- Or: Manually transcribe audio files

Usage:
    # Add audio file to queue
    from voice_input import add_audio, transcribe_audio

    add_audio('recording.wav', source='manual')

    # Transcribe (manual or auto when online)
    transcribe_audio(audio_id, text='Manually transcribed text')
"""

import sqlite3
import os
import hashlib
from datetime import datetime
from pathlib import Path
import json
import subprocess


def _get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def _init_database():
    """Initialize audio storage tables"""
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_hash TEXT,
            file_size INTEGER,
            duration_seconds REAL,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            transcription TEXT,
            transcribed_at TIMESTAMP,
            transcription_method TEXT,
            metadata TEXT
        )
    ''')

    conn.commit()
    conn.close()


def add_audio(file_path: str, source: str = 'manual', metadata: dict = None) -> int:
    """
    Add audio file to voice input queue

    Args:
        file_path: Path to audio file
        source: Source of recording ('manual', 'system', 'mobile', etc)
        metadata: Optional metadata dict

    Returns:
        audio_id: ID of added audio
    """
    _init_database()

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Calculate file hash
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    file_hash = hasher.hexdigest()

    # Get file size
    file_size = file_path.stat().st_size

    # Store in database
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO voice_inputs
        (filename, file_path, file_hash, file_size, source, metadata, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    ''', (
        file_path.name,
        str(file_path.absolute()),
        file_hash,
        file_size,
        source,
        json.dumps(metadata) if metadata else None
    ))

    audio_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"🎤 Added audio #{audio_id}: {file_path.name}")
    print(f"   Size: {file_size:,} bytes")
    print(f"   Hash: {file_hash[:16]}...")

    return audio_id


def transcribe_audio(audio_id: int, text: str, method: str = 'manual'):
    """
    Add transcription to audio

    Args:
        audio_id: ID of audio to transcribe
        text: Transcribed text
        method: Method used ('manual', 'whisper', 'google', etc)
    """
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE voice_inputs
        SET transcription = ?,
            transcribed_at = CURRENT_TIMESTAMP,
            transcription_method = ?,
            status = 'transcribed'
        WHERE id = ?
    ''', (text, method, audio_id))

    conn.commit()
    conn.close()

    print(f"✅ Transcribed audio #{audio_id}")
    print(f"   Method: {method}")
    print(f"   Length: {len(text)} characters")


def get_audio(audio_id: int) -> dict:
    """Get audio details"""
    conn = _get_db()
    cursor = conn.cursor()

    audio = cursor.execute(
        'SELECT * FROM voice_inputs WHERE id = ?',
        (audio_id,)
    ).fetchone()

    conn.close()

    if not audio:
        return None

    return dict(audio)


def list_audio(status: str = None, limit: int = 10) -> list:
    """List audio files"""
    _init_database()

    conn = _get_db()
    cursor = conn.cursor()

    if status:
        audios = cursor.execute('''
            SELECT id, filename, file_size, created_at, status, transcription
            FROM voice_inputs
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (status, limit)).fetchall()
    else:
        audios = cursor.execute('''
            SELECT id, filename, file_size, created_at, status, transcription
            FROM voice_inputs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    conn.close()

    return [dict(a) for a in audios]


def export_for_transcription(output_dir: str = 'audio_export'):
    """
    Export pending audio files for external transcription

    Creates a folder with all pending audio + manifest JSON

    Args:
        output_dir: Directory to export to
    """
    _init_database()

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    conn = _get_db()
    cursor = conn.cursor()

    pending = cursor.execute('''
        SELECT * FROM voice_inputs
        WHERE status = 'pending'
        ORDER BY created_at
    ''').fetchall()

    if not pending:
        print("No pending audio files to export")
        return

    manifest = []

    for audio in pending:
        # Copy audio file
        src = Path(audio['file_path'])
        dst = output_path / f"{audio['id']}_{src.name}"

        if src.exists():
            import shutil
            shutil.copy2(src, dst)

            manifest.append({
                'id': audio['id'],
                'filename': src.name,
                'export_filename': dst.name,
                'created_at': audio['created_at'],
                'file_size': audio['file_size']
            })

    # Write manifest
    manifest_path = output_path / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"📦 Exported {len(manifest)} audio files to {output_path}/")
    print(f"   Manifest: {manifest_path}")
    print()
    print("💡 Transcribe these files, then import with:")
    print(f"   python3 voice_input.py import {output_path}/transcriptions.json")


def import_transcriptions(json_path: str):
    """
    Import transcriptions from JSON file

    Expected format:
    [
        {"id": 1, "text": "Transcribed text here", "method": "whisper"},
        ...
    ]

    Args:
        json_path: Path to JSON file with transcriptions
    """
    with open(json_path, 'r') as f:
        transcriptions = json.load(f)

    for item in transcriptions:
        audio_id = item['id']
        text = item['text']
        method = item.get('method', 'imported')

        transcribe_audio(audio_id, text, method)

    print(f"✅ Imported {len(transcriptions)} transcriptions")


def stats():
    """Show voice input statistics"""
    _init_database()

    conn = _get_db()
    cursor = conn.cursor()

    total = cursor.execute('SELECT COUNT(*) FROM voice_inputs').fetchone()[0]
    pending = cursor.execute('SELECT COUNT(*) FROM voice_inputs WHERE status = "pending"').fetchone()[0]
    transcribed = cursor.execute('SELECT COUNT(*) FROM voice_inputs WHERE status = "transcribed"').fetchone()[0]

    total_size = cursor.execute('SELECT SUM(file_size) FROM voice_inputs').fetchone()[0] or 0

    conn.close()

    print("=" * 70)
    print("🎤 Voice Input Statistics")
    print("=" * 70)
    print()
    print(f"Total audio files:    {total}")
    print(f"Pending:              {pending}")
    print(f"Transcribed:          {transcribed}")
    print(f"Total size:           {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
    print()


def create_post_from_audio(audio_id: int, title: str = None):
    """
    Create a blog post from transcribed audio

    Args:
        audio_id: ID of transcribed audio
        title: Optional post title
    """
    audio = get_audio(audio_id)

    if not audio:
        print(f"❌ Audio #{audio_id} not found")
        return

    if not audio['transcription']:
        print(f"❌ Audio #{audio_id} not transcribed yet")
        return

    # Create post
    from database import get_db
    db = get_db()

    # Use first line as title if not provided
    if not title:
        first_line = audio['transcription'].split('\n')[0]
        title = first_line[:100] if len(first_line) > 100 else first_line

    slug = title.lower().replace(' ', '-')

    db.execute('''
        INSERT INTO posts (title, content, author_id, published_at, slug)
        VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?)
    ''', (title, audio['transcription'], slug))

    db.commit()
    post_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()

    print(f"✅ Created post #{post_id} from audio #{audio_id}")
    print(f"   Title: {title}")
    print(f"   URL: http://localhost:5001/post/{post_id}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            status = sys.argv[2] if len(sys.argv) > 2 else None
            audios = list_audio(status=status, limit=20)

            print("=" * 70)
            print(f"🎤 Voice Inputs{' (' + status + ')' if status else ''}")
            print("=" * 70)
            print()

            if not audios:
                print("   No audio files found")
            else:
                for audio in audios:
                    status_icon = {'pending': '⏳', 'transcribed': '✅'}.get(audio['status'], '❓')

                    print(f"{status_icon} #{audio['id']}: {audio['filename']}")
                    print(f"   Size: {audio['file_size']:,} bytes | {audio['created_at']}")

                    if audio['transcription']:
                        preview = audio['transcription'][:100]
                        print(f"   📝 {preview}...")

                    print()

        elif command == 'add':
            if len(sys.argv) < 3:
                print("Usage: python3 voice_input.py add <audio_file>")
                sys.exit(1)

            file_path = sys.argv[2]
            source = sys.argv[3] if len(sys.argv) > 3 else 'manual'

            audio_id = add_audio(file_path, source=source)
            print()
            print(f"💡 Transcribe with: python3 voice_input.py transcribe {audio_id} 'your text here'")

        elif command == 'transcribe':
            if len(sys.argv) < 4:
                print("Usage: python3 voice_input.py transcribe <audio_id> <text>")
                sys.exit(1)

            audio_id = int(sys.argv[2])
            text = sys.argv[3]
            method = sys.argv[4] if len(sys.argv) > 4 else 'manual'

            transcribe_audio(audio_id, text, method=method)

        elif command == 'export':
            output_dir = sys.argv[2] if len(sys.argv) > 2 else 'audio_export'
            export_for_transcription(output_dir)

        elif command == 'import':
            if len(sys.argv) < 3:
                print("Usage: python3 voice_input.py import <transcriptions.json>")
                sys.exit(1)

            json_path = sys.argv[2]
            import_transcriptions(json_path)

        elif command == 'stats':
            stats()

        elif command == 'post':
            if len(sys.argv) < 3:
                print("Usage: python3 voice_input.py post <audio_id> [title]")
                sys.exit(1)

            audio_id = int(sys.argv[2])
            title = sys.argv[3] if len(sys.argv) > 3 else None

            create_post_from_audio(audio_id, title)

        else:
            print(f"Unknown command: {command}")
            print()
            print("Available commands:")
            print("  python3 voice_input.py list [status]")
            print("  python3 voice_input.py add <audio_file> [source]")
            print("  python3 voice_input.py transcribe <id> <text> [method]")
            print("  python3 voice_input.py export [output_dir]")
            print("  python3 voice_input.py import <transcriptions.json>")
            print("  python3 voice_input.py stats")
            print("  python3 voice_input.py post <audio_id> [title]")
            sys.exit(1)

    else:
        print("=" * 70)
        print("🎤 Voice Input System - Offline-First Audio Management")
        print("=" * 70)
        print()
        print("Manage audio recordings and transcriptions offline.")
        print()
        print("Workflow:")
        print("  1. Record audio (external tool or device)")
        print("  2. Add to queue: python3 voice_input.py add recording.wav")
        print("  3. Transcribe manually or export for batch transcription")
        print("  4. Create posts from transcribed audio")
        print()
        print("Commands:")
        print("  list [status]           - List audio files")
        print("  add <file> [source]     - Add audio file")
        print("  transcribe <id> <text>  - Add transcription")
        print("  export [dir]            - Export for external transcription")
        print("  import <json>           - Import transcriptions")
        print("  stats                   - Show statistics")
        print("  post <id> [title]       - Create post from audio")
        print()
        print("=" * 70)

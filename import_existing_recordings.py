#!/usr/bin/env python3
"""
Import Existing Voice Recordings
Scan filesystem for .webm files, extract transcriptions, import to database
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent

def get_db():
    """Connect to database"""
    db_path = BASE_DIR / 'soulfra.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def find_all_audio_files():
    """Recursively find all .webm and .wav files"""
    audio_files = []

    search_dirs = [
        BASE_DIR / 'voice-archive',
        BASE_DIR / 'suggestion-box',
        BASE_DIR / 'voice_exports',
        BASE_DIR / 'voice_samples',  # Add voice_samples directory
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Find .webm files
        for webm_file in search_dir.rglob('*.webm'):
            audio_files.append(webm_file)

        # Find .wav files
        for wav_file in search_dir.rglob('*.wav'):
            audio_files.append(wav_file)

    return audio_files

def extract_transcription(webm_path):
    """Extract transcription from metadata.json or index.html"""
    parent_dir = webm_path.parent

    # Try metadata.json first
    metadata_file = parent_dir / 'metadata.json'
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)

        # Check if transcription is in metadata
        if 'transcription' in metadata:
            return metadata['transcription']

    # Try index.html
    index_file = parent_dir / 'index.html'
    if index_file.exists():
        with open(index_file) as f:
            html_content = f.read()

        # Look for transcription in HTML (various patterns)
        # Pattern 1: <div class="transcription">...</div>
        match = re.search(r'<div[^>]*class="transcription"[^>]*>(.*?)</div>', html_content, re.DOTALL)
        if match:
            transcription = match.group(1).strip()
            # Clean HTML tags
            transcription = re.sub(r'<[^>]+>', '', transcription)
            return transcription

        # Pattern 2: Look for paragraphs after "Transcription:" heading
        match = re.search(r'Transcription:?\s*</h[1-6]>\s*<p>(.*?)</p>', html_content, re.DOTALL)
        if match:
            transcription = match.group(1).strip()
            transcription = re.sub(r'<[^>]+>', '', transcription)
            return transcription

    # Try looking for .txt file with same name
    txt_file = webm_path.with_suffix('.txt')
    if txt_file.exists():
        with open(txt_file) as f:
            return f.read().strip()

    return None

def extract_timestamp(webm_path):
    """Extract created_at timestamp from filename or file metadata"""
    filename = webm_path.stem

    # Pattern 1: recording_20260102_150124.webm
    match = re.search(r'(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)  # 20260102
        time_str = match.group(2)  # 150124

        datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        return datetime_str

    # Pattern 2: idea_20260102_163410.webm
    match = re.search(r'(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        return datetime_str

    # Fallback: Use file modification time
    stat = webm_path.stat()
    return datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

def import_recording(db, audio_path, transcription, created_at):
    """Import recording to database"""

    filename = audio_path.name

    # Check if already imported
    existing = db.execute(
        'SELECT id FROM simple_voice_recordings WHERE filename = ? AND transcription = ?',
        (filename, transcription)
    ).fetchone()

    if existing:
        print(f"  ⏭️  Already imported: {filename}")
        return None

    # Read audio file
    with open(audio_path, 'rb') as f:
        audio_data = f.read()

    file_size = len(audio_data)

    # Insert recording
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (
            filename,
            audio_data,
            file_size,
            transcription,
            transcription_method,
            created_at,
            approval_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, file_size, transcription, 'imported', created_at, 'approved'))

    db.commit()
    return cursor.lastrowid

def main():
    print("🔍 Scanning for audio recordings (.webm, .wav)...")

    audio_files = find_all_audio_files()
    print(f"Found {len(audio_files)} audio files")

    db = get_db()
    imported = 0
    skipped = 0
    no_transcription = 0

    for audio_path in audio_files:
        print(f"\n📁 {audio_path.relative_to(BASE_DIR)}")

        # Extract transcription
        transcription = extract_transcription(audio_path)

        if not transcription:
            print(f"  ⚠️  No transcription found")
            no_transcription += 1
            continue

        print(f"  ✅ Transcription: {transcription[:50]}...")

        # Extract timestamp
        created_at = extract_timestamp(audio_path)
        print(f"  📅 Created: {created_at}")

        # Import to database
        recording_id = import_recording(db, audio_path, transcription, created_at)

        if recording_id:
            print(f"  💾 Imported as ID: {recording_id}")
            imported += 1
        else:
            skipped += 1

    db.close()

    print(f"\n{'='*60}")
    print(f"✅ Imported: {imported}")
    print(f"⏭️  Skipped (already imported): {skipped}")
    print(f"⚠️  No transcription: {no_transcription}")
    print(f"{'='*60}")

    if imported > 0:
        print(f"\n🎉 Success! Visit https://localhost:5001/daily to see your recordings")

if __name__ == '__main__':
    main()

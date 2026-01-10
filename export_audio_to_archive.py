#!/usr/bin/env python3
"""
Export Audio Files to Voice Archive

Exports audio from database to voice-archive/audio/ directory
so they can be linked from ideas hub and other pages.

Usage:
    python3 export_audio_to_archive.py
"""

import sqlite3
import os
from pathlib import Path
import json


def export_audio():
    """Export all voice recordings to voice-archive/audio/"""

    db_path = "soulfra.db"
    audio_dir = Path("voice-archive/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get all recordings with audio data
    cursor = conn.execute('''
        SELECT id, filename, audio_data, transcription, created_at
        FROM simple_voice_recordings
        WHERE audio_data IS NOT NULL
        ORDER BY id
    ''')

    recordings = cursor.fetchall()

    print(f"\n📤 Exporting {len(recordings)} audio files...")

    manifest = []
    exported_count = 0

    for rec in recordings:
        rec_id = rec['id']
        filename = rec['filename'] or f"recording_{rec_id}.webm"

        # Create directory for this recording
        rec_dir = audio_dir / str(rec_id)
        rec_dir.mkdir(exist_ok=True)

        # Determine file extension
        if filename.endswith('.wav'):
            ext = '.wav'
        elif filename.endswith('.webm'):
            ext = '.webm'
        else:
            ext = '.webm'  # default

        # Export audio file
        audio_path = rec_dir / f"recording{ext}"

        with open(audio_path, 'wb') as f:
            f.write(rec['audio_data'])

        # Create metadata JSON
        metadata = {
            'id': rec_id,
            'filename': filename,
            'has_transcription': rec['transcription'] is not None,
            'created_at': rec['created_at'],
            'audio_file': f"recording{ext}"
        }

        metadata_path = rec_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create simple HTML player
        player_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Recording #{rec_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 600px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        }}
        h1 {{
            margin-bottom: 2rem;
        }}
        audio {{
            width: 100%;
            margin: 2rem 0;
        }}
        .meta {{
            opacity: 0.8;
            margin-top: 2rem;
        }}
        a {{
            color: white;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Voice Recording #{rec_id}</h1>
        <audio controls preload="metadata">
            <source src="recording{ext}" type="audio/{'webm' if ext == '.webm' else 'wav'}">
            Your browser doesn't support audio playback.
        </audio>
        <div class="meta">
            <p>Recorded: {rec['created_at']}</p>
            <p><a href="../../ideas/">← Back to Ideas</a></p>
        </div>
    </div>
</body>
</html>'''

        player_path = rec_dir / "index.html"
        with open(player_path, 'w') as f:
            f.write(player_html)

        manifest.append({
            'id': rec_id,
            'path': f"audio/{rec_id}/",
            'filename': filename,
            'size': len(rec['audio_data'])
        })

        print(f"   ✅ Exported recording #{rec_id}: {audio_path}")
        exported_count += 1

    # Create manifest
    manifest_path = audio_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump({
            'total_recordings': len(recordings),
            'exported': exported_count,
            'recordings': manifest
        }, f, indent=2)

    conn.close()

    print(f"\n✅ Exported {exported_count} audio files to voice-archive/audio/")
    print(f"   Manifest: {manifest_path}")
    print(f"\n🔗 Audio files can now be accessed at:")
    for rec in manifest:
        print(f"   https://soulfra.github.io/voice-archive/audio/{rec['id']}/")


if __name__ == '__main__':
    export_audio()

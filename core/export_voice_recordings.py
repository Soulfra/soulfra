#!/usr/bin/env python3
"""
Export Voice Recordings - Database → Filesystem

Exports your voice recordings from the database BLOBs to actual .wav files on your PC.

Usage:
    python3 export_voice_recordings.py <username>

Example:
    python3 export_voice_recordings.py matt

This will create a folder `voice_exports/<username>/` with all your recordings.
"""

import sqlite3
import sys
import os
from pathlib import Path


def export_user_voice_recordings(username: str):
    """Export all voice recordings for a user to filesystem"""

    # Connect to database
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get user
    user = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        print(f"❌ User '{username}' not found")
        return

    user_id = user['id']

    # Get all voice recordings
    recordings = cursor.execute('''
        SELECT id, filename, audio_data, file_size, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ?
        ORDER BY created_at
    ''', (user_id,)).fetchall()

    if not recordings:
        print(f"No voice recordings found for user '{username}'")
        return

    # Create export directory
    export_dir = Path(f'voice_exports/{username}')
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Exporting {len(recordings)} voice recordings for '{username}'")
    print(f"📁 Export directory: {export_dir.absolute()}\n")

    exported_count = 0

    for recording in recordings:
        recording_id = recording['id']
        filename = recording['filename']
        audio_data = recording['audio_data']
        transcription = recording['transcription']
        created_at = recording['created_at']

        # Save audio file
        audio_path = export_dir / filename
        with open(audio_path, 'wb') as f:
            f.write(audio_data)

        # Save transcription as .txt
        transcript_path = export_dir / f"{filename}.txt"
        with open(transcript_path, 'w') as f:
            f.write(f"Recording ID: {recording_id}\n")
            f.write(f"Created: {created_at}\n")
            f.write(f"File Size: {len(audio_data)} bytes\n")
            f.write(f"\n{'='*70}\n")
            f.write(f"TRANSCRIPTION:\n")
            f.write(f"{'='*70}\n\n")
            f.write(transcription or "(No transcription)")

        print(f"✅ Exported: {filename}")
        print(f"   Audio: {audio_path}")
        print(f"   Transcript: {transcript_path}")
        print(f"   Size: {len(audio_data)} bytes\n")

        exported_count += 1

    conn.close()

    print(f"\n{'='*70}")
    print(f"🎉 Successfully exported {exported_count} recordings!")
    print(f"📁 Location: {export_dir.absolute()}")
    print(f"{'='*70}\n")

    print("Your voice recordings are now on your PC at:")
    print(f"  {export_dir.absolute()}")
    print("\nYou can:")
    print("  - Play the .wav files in any audio player")
    print("  - Read the .txt transcriptions")
    print("  - Back up to external drive / cloud storage")
    print("  - The originals remain safely in the database")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_voice_recordings.py <username>")
        print("\nExample:")
        print("  python3 export_voice_recordings.py matt")
        sys.exit(1)

    username = sys.argv[1]
    export_user_voice_recordings(username)


if __name__ == '__main__':
    main()

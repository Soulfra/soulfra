#!/usr/bin/env python3
"""
Whisper Processor - Extract webm from database and transcribe with REAL Whisper

This script processes voice recordings stored as BLOBs in the database:
1. Extracts webm audio data from database
2. Saves to temporary file
3. Runs Whisper transcription on actual audio
4. Updates database with REAL transcript (replaces fake/null)

Usage:
    python3 whisper_processor.py --all              # Process all recordings
    python3 whisper_processor.py --id 2             # Process specific recording
    python3 whisper_processor.py --nulls-only       # Only process NULL transcripts
    python3 whisper_processor.py --replace-all      # Replace ALL transcripts (even existing)
"""

import sqlite3
import argparse
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
NC = '\033[0m'


class WhisperProcessor:
    """Process voice recordings with real Whisper transcription"""

    def __init__(self, db_path='soulfra.db', model='base'):
        self.db_path = db_path
        self.model = model
        self.whisper_model = None

    def load_whisper(self):
        """Load Whisper model (lazy loading)"""
        if self.whisper_model is not None:
            return

        try:
            import whisper
            import ssl
            import urllib.request

            # Disable SSL verification for Whisper model download (macOS issue)
            ssl._create_default_https_context = ssl._create_unverified_context

            print(f"{CYAN}🔄 Loading Whisper model '{self.model}'...{NC}")
            self.whisper_model = whisper.load_model(self.model)
            print(f"{GREEN}✅ Whisper model loaded{NC}\n")
        except Exception as e:
            print(f"{RED}❌ Failed to load Whisper: {e}{NC}")
            print(f"{YELLOW}💡 Install with: pip3 install openai-whisper{NC}")
            raise

    def get_recording(self, recording_id: int) -> Optional[Dict]:
        """Fetch recording from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        recording = cursor.execute('''
            SELECT id, filename, audio_data, transcription, transcription_method, created_at
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        conn.close()

        if not recording:
            return None

        return dict(recording)

    def get_all_recordings(self, nulls_only=False) -> List[Dict]:
        """Fetch all recordings from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if nulls_only:
            query = '''
                SELECT id, filename, audio_data, transcription, transcription_method, created_at
                FROM simple_voice_recordings
                WHERE transcription IS NULL
                ORDER BY created_at DESC
            '''
        else:
            query = '''
                SELECT id, filename, audio_data, transcription, transcription_method, created_at
                FROM simple_voice_recordings
                ORDER BY created_at DESC
            '''

        recordings = cursor.execute(query).fetchall()
        conn.close()

        return [dict(r) for r in recordings]

    def transcribe_recording(self, recording_id: int, force_replace=False) -> bool:
        """Transcribe a single recording"""
        recording = self.get_recording(recording_id)

        if not recording:
            print(f"{RED}❌ Recording {recording_id} not found{NC}")
            return False

        # Check if already has transcription
        if recording['transcription'] and not force_replace:
            print(f"{YELLOW}⊘  Recording {recording_id} already has transcription (use --replace-all to override){NC}")
            return False

        print(f"\n{CYAN}━━━ Processing Recording {recording_id} ━━━{NC}")
        print(f"Filename: {recording['filename']}")
        print(f"Created: {recording['created_at']}")
        print(f"Size: {len(recording['audio_data'])} bytes")

        if recording['transcription']:
            print(f"{YELLOW}Current transcript (will be replaced): {recording['transcription'][:100]}...{NC}")

        # Extract webm to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(recording['audio_data'])
            tmp_path = tmp.name

        try:
            # Load Whisper model
            self.load_whisper()

            # Transcribe
            print(f"{CYAN}🎙️  Transcribing audio with Whisper...{NC}")
            result = self.whisper_model.transcribe(tmp_path, language='en')

            transcription = result['text'].strip()

            if not transcription:
                print(f"{RED}❌ Whisper returned empty transcription{NC}")
                os.unlink(tmp_path)
                return False

            print(f"\n{GREEN}✅ Transcription complete!{NC}")
            print(f"{CYAN}📝 Text: {transcription}{NC}\n")

            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE simple_voice_recordings
                SET transcription = ?, transcription_method = ?
                WHERE id = ?
            ''', (transcription, f'whisper_{self.model}', recording_id))

            conn.commit()
            conn.close()

            print(f"{GREEN}✅ Database updated with real transcription{NC}")

            # Clean up temp file
            os.unlink(tmp_path)

            return True

        except Exception as e:
            print(f"{RED}❌ Transcription failed: {e}{NC}")
            os.unlink(tmp_path)
            return False

    def process_all(self, nulls_only=False, force_replace=False):
        """Process all recordings"""
        recordings = self.get_all_recordings(nulls_only=nulls_only)

        if not recordings:
            if nulls_only:
                print(f"{GREEN}✅ No recordings with null transcriptions found!{NC}")
            else:
                print(f"{YELLOW}⚠️  No recordings found in database{NC}")
            return

        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}🎙️  Whisper Processor{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")
        print(f"Found {len(recordings)} recording(s) to process")
        print(f"Mode: {'NULL transcripts only' if nulls_only else 'All recordings'}")
        print(f"Replace existing: {'Yes' if force_replace else 'No'}\n")

        success_count = 0
        skip_count = 0
        fail_count = 0

        for recording in recordings:
            result = self.transcribe_recording(recording['id'], force_replace=force_replace)

            if result:
                success_count += 1
            elif recording['transcription'] and not force_replace:
                skip_count += 1
            else:
                fail_count += 1

        # Summary
        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}📊 SUMMARY{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")
        print(f"{GREEN}✅ Success:  {success_count}{NC}")
        print(f"{YELLOW}⊘  Skipped:  {skip_count}{NC}")
        print(f"{RED}❌ Failed:   {fail_count}{NC}\n")


def main():
    parser = argparse.ArgumentParser(description='Whisper Processor - Real transcription from webm files')
    parser.add_argument('--all', action='store_true', help='Process all recordings')
    parser.add_argument('--id', type=int, help='Process specific recording ID')
    parser.add_argument('--nulls-only', action='store_true', help='Only process recordings with NULL transcripts')
    parser.add_argument('--replace-all', action='store_true', help='Replace ALL transcripts (even existing)')
    parser.add_argument('--model', default='base', help='Whisper model (tiny, base, small, medium, large)')
    parser.add_argument('--db', default='soulfra.db', help='Database path')

    args = parser.parse_args()

    processor = WhisperProcessor(db_path=args.db, model=args.model)

    if args.id:
        # Process specific recording
        processor.transcribe_recording(args.id, force_replace=args.replace_all)

    elif args.all or args.nulls_only:
        # Process all or nulls only
        processor.process_all(nulls_only=args.nulls_only, force_replace=args.replace_all)

    else:
        # Default: process nulls only
        print(f"{CYAN}💡 No arguments provided. Processing NULL transcripts only.{NC}")
        print(f"{CYAN}   Use --all to process all recordings{NC}\n")
        processor.process_all(nulls_only=True, force_replace=args.replace_all)


if __name__ == '__main__':
    main()

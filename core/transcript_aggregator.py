#!/usr/bin/env python3
"""
Transcript Aggregator - Find transcripts from ALL sources

Aggregates transcripts from:
1. Database: simple_voice_recordings (voice memos)
2. Database: chat_transcripts (chat sessions)
3. Database: discussion_messages (discussion sessions)
4. File System: .txt, .md, .json files containing transcripts
5. External submissions via API

Features:
- Unified search across all sources
- Find and fix null transcriptions
- Export all transcripts
- Queue recordings for Whisper processing

Usage:
    python3 transcript_aggregator.py --search "roommate network"
    python3 transcript_aggregator.py --fix-nulls
    python3 transcript_aggregator.py --export transcripts.zip
    python3 transcript_aggregator.py --stats
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import glob

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
NC = '\033[0m'


class TranscriptAggregator:
    """Aggregate transcripts from multiple sources"""

    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path
        self.transcripts = []

    def fetch_voice_transcripts(self) -> List[Dict]:
        """Fetch transcripts from simple_voice_recordings table"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = cursor.execute('''
            SELECT id, filename, transcription, transcription_method, created_at
            FROM simple_voice_recordings
            ORDER BY created_at DESC
        ''').fetchall()

        conn.close()

        transcripts = []
        for row in results:
            transcripts.append({
                'id': row['id'],
                'source': 'voice_recording',
                'filename': row['filename'],
                'content': row['transcription'],
                'method': row['transcription_method'],
                'created_at': row['created_at'],
                'has_null': row['transcription'] is None
            })

        return transcripts

    def fetch_chat_transcripts(self) -> List[Dict]:
        """Fetch transcripts from chat_transcripts table"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if table exists
        table_check = cursor.execute('''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='chat_transcripts'
        ''').fetchone()

        if not table_check:
            conn.close()
            return []

        results = cursor.execute('''
            SELECT id, role, content, model, created_at, session_id
            FROM chat_transcripts
            ORDER BY created_at DESC
            LIMIT 1000
        ''').fetchall()

        conn.close()

        transcripts = []
        for row in results:
            transcripts.append({
                'id': row['id'],
                'source': 'chat_transcript',
                'role': row['role'],
                'content': row['content'],
                'model': row['model'],
                'session_id': row['session_id'],
                'created_at': row['created_at'],
                'has_null': False  # Chat transcripts shouldn't be null
            })

        return transcripts

    def fetch_discussion_messages(self) -> List[Dict]:
        """Fetch transcripts from discussion_messages table"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = cursor.execute('''
            SELECT id, session_id, sender, content, created_at
            FROM discussion_messages
            ORDER BY created_at DESC
            LIMIT 1000
        ''').fetchall()

        conn.close()

        transcripts = []
        for row in results:
            transcripts.append({
                'id': row['id'],
                'source': 'discussion_message',
                'sender': row['sender'],
                'content': row['content'],
                'session_id': row['session_id'],
                'created_at': row['created_at'],
                'has_null': row['content'] is None
            })

        return transcripts

    def scan_file_system(self, search_path='.') -> List[Dict]:
        """Scan file system for transcript files"""
        transcripts = []

        # File patterns to search
        patterns = [
            '**/*.transcript.txt',
            '**/*transcript*.json',
            '**/*-transcript-*.md',
            'transcripts/**/*.txt',
            'data/transcripts/**/*'
        ]

        for pattern in patterns:
            for filepath in glob.glob(pattern, recursive=True):
                # Skip hidden files and directories
                if '/.git/' in filepath or '/__pycache__/' in filepath:
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    transcripts.append({
                        'source': 'file_system',
                        'filepath': filepath,
                        'content': content,
                        'size': len(content),
                        'modified_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                        'has_null': False
                    })
                except Exception as e:
                    print(f"{YELLOW}⚠️  Could not read {filepath}: {e}{NC}")

        return transcripts

    def aggregate_all(self):
        """Fetch transcripts from all sources"""
        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}📚 Transcript Aggregator{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")

        # Voice recordings
        print(f"{CYAN}🎙️  Fetching voice recordings...{NC}")
        voice_transcripts = self.fetch_voice_transcripts()
        print(f"   Found {len(voice_transcripts)} voice recordings")
        nulls = len([t for t in voice_transcripts if t['has_null']])
        if nulls > 0:
            print(f"   {YELLOW}⚠️  {nulls} recordings have NULL transcriptions{NC}")

        # Chat transcripts
        print(f"\n{CYAN}💬 Fetching chat transcripts...{NC}")
        chat_transcripts = self.fetch_chat_transcripts()
        print(f"   Found {len(chat_transcripts)} chat messages")

        # Discussion messages
        print(f"\n{CYAN}💭 Fetching discussion messages...{NC}")
        discussion_transcripts = self.fetch_discussion_messages()
        print(f"   Found {len(discussion_transcripts)} discussion messages")

        # File system
        print(f"\n{CYAN}📁 Scanning file system...{NC}")
        file_transcripts = self.scan_file_system()
        print(f"   Found {len(file_transcripts)} transcript files")

        # Combine all
        self.transcripts = (
            voice_transcripts +
            chat_transcripts +
            discussion_transcripts +
            file_transcripts
        )

        print(f"\n{GREEN}✅ Total transcripts found: {len(self.transcripts)}{NC}\n")

        return self.transcripts

    def search(self, query: str, case_sensitive=False):
        """Search transcripts by keyword"""
        if not self.transcripts:
            self.aggregate_all()

        query_lower = query if case_sensitive else query.lower()

        results = []
        for t in self.transcripts:
            content = t.get('content', '')
            if content is None:
                continue

            content_check = content if case_sensitive else content.lower()

            if query_lower in content_check:
                results.append(t)

        return results

    def find_nulls(self):
        """Find all transcripts with null content"""
        if not self.transcripts:
            self.aggregate_all()

        nulls = [t for t in self.transcripts if t.get('has_null', False)]
        return nulls

    def fix_nulls(self, dry_run=False):
        """Fix null transcriptions by queueing for Whisper processing"""
        nulls = self.find_nulls()

        if not nulls:
            print(f"{GREEN}✅ No null transcriptions found!{NC}\n")
            return

        print(f"\n{YELLOW}⚠️  Found {len(nulls)} NULL transcriptions{NC}\n")

        for t in nulls:
            if t['source'] == 'voice_recording':
                print(f"   • Recording {t['id']}: {t['filename']}")
                print(f"     Created: {t['created_at']}")

                if not dry_run:
                    # Queue for Whisper processing
                    self._queue_for_whisper(t['id'])
                    print(f"     {GREEN}→ Queued for Whisper processing{NC}")
                else:
                    print(f"     {CYAN}→ Would queue for Whisper (dry run){NC}")
                print()

        if dry_run:
            print(f"\n{CYAN}Dry run complete. Use --fix-nulls without --dry-run to actually process.{NC}\n")
        else:
            print(f"\n{GREEN}✅ Queued {len(nulls)} recordings for Whisper processing{NC}")
            print(f"   Run whisper processing to generate transcriptions.\n")

    def _queue_for_whisper(self, recording_id: int):
        """Queue a recording for Whisper transcription"""
        # This would integrate with whisper_transcriber.py
        # For now, just mark it in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE simple_voice_recordings
            SET transcription_method = 'queued_for_whisper'
            WHERE id = ?
        ''', (recording_id,))

        conn.commit()
        conn.close()

    def export(self, output_file='transcripts_export.json'):
        """Export all transcripts to JSON file"""
        if not self.transcripts:
            self.aggregate_all()

        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_transcripts': len(self.transcripts),
            'sources': {
                'voice_recordings': len([t for t in self.transcripts if t['source'] == 'voice_recording']),
                'chat_transcripts': len([t for t in self.transcripts if t['source'] == 'chat_transcript']),
                'discussion_messages': len([t for t in self.transcripts if t['source'] == 'discussion_message']),
                'file_system': len([t for t in self.transcripts if t['source'] == 'file_system'])
            },
            'transcripts': self.transcripts
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\n{GREEN}✅ Exported {len(self.transcripts)} transcripts to {output_file}{NC}\n")

    def stats(self):
        """Print statistics about transcripts"""
        if not self.transcripts:
            self.aggregate_all()

        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}📊 Transcript Statistics{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")

        # By source
        by_source = {}
        for t in self.transcripts:
            source = t.get('source', 'unknown')
            by_source[source] = by_source.get(source, 0) + 1

        print(f"{CYAN}By Source:{NC}")
        for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source:30} {count:>6} transcripts")

        # Null count
        nulls = len([t for t in self.transcripts if t.get('has_null', False)])
        print(f"\n{CYAN}Data Quality:{NC}")
        print(f"   Total:                         {len(self.transcripts):>6} transcripts")
        print(f"   With content:                  {len(self.transcripts) - nulls:>6} transcripts")
        print(f"   {YELLOW}NULL/missing:{NC}                  {nulls:>6} transcripts")

        if nulls > 0:
            print(f"\n{YELLOW}💡 Tip: Run with --fix-nulls to queue null recordings for Whisper processing{NC}")

        print()


def main():
    parser = argparse.ArgumentParser(description='Transcript Aggregator')
    parser.add_argument('--search', type=str, help='Search transcripts by keyword')
    parser.add_argument('--fix-nulls', action='store_true', help='Fix NULL transcriptions')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t actually fix)')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--db', default='soulfra.db', help='Database path')

    args = parser.parse_args()

    aggregator = TranscriptAggregator(db_path=args.db)

    if args.search:
        print(f"\n{CYAN}🔍 Searching for: \"{args.search}\"{NC}\n")
        results = aggregator.search(args.search)

        if results:
            print(f"{GREEN}Found {len(results)} matches:{NC}\n")
            for i, result in enumerate(results[:10], 1):  # Show first 10
                print(f"{i}. {result['source']} - {result.get('filename', result.get('sender', 'N/A'))}")
                content = result.get('content', '')
                if content:
                    # Show snippet
                    snippet = content[:150].replace('\n', ' ')
                    print(f"   \"{snippet}...\"")
                print()

            if len(results) > 10:
                print(f"   ... and {len(results) - 10} more results\n")
        else:
            print(f"{YELLOW}No matches found.{NC}\n")

    elif args.fix_nulls:
        aggregator.fix_nulls(dry_run=args.dry_run)

    elif args.export:
        aggregator.export(args.export)

    elif args.stats:
        aggregator.stats()

    else:
        # Default: show stats
        aggregator.stats()


if __name__ == '__main__':
    main()

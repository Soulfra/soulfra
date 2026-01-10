#!/usr/bin/env python3
"""
Voice Memo Dissector - Extract structured ideas from voice transcriptions

Converts voice memos into structured documentation:
- Main idea/concept
- Technical requirements
- Domain tags
- Hardware specs (if mentioned)
- Pitch deck sections
- Related projects

Usage:
    # Process single recording
    python3 voice_memo_dissector.py --recording-id 7

    # Process all unprocessed recordings
    python3 voice_memo_dissector.py --process-all

    # Re-process with better prompt
    python3 voice_memo_dissector.py --recording-id 7 --reprocess
"""

import os
import sys
import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import requests


class VoiceMemoDissector:
    """Extract structured ideas from voice memo transcriptions"""

    def __init__(self, db_path: str = "soulfra.db", ollama_url: str = "http://localhost:11434"):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.docs_dir = Path("docs/voice-ideas")
        self.pitches_dir = Path("docs/pitches")
        self.hardware_dir = Path("docs/hardware")

        # Create directories
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.pitches_dir.mkdir(parents=True, exist_ok=True)
        self.hardware_dir.mkdir(parents=True, exist_ok=True)

    def dissect_recording(self, recording_id: int, reprocess: bool = False) -> Optional[Dict]:
        """
        Extract structured ideas from a voice recording

        Args:
            recording_id: ID of recording to process
            reprocess: Force reprocess even if already done

        Returns:
            Dict with extracted ideas or None if error
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get recording
        cursor = conn.execute('''
            SELECT id, filename, transcription, created_at
            FROM simple_voice_recordings
            WHERE id = ? AND transcription IS NOT NULL
        ''', (recording_id,))

        recording = cursor.fetchone()

        if not recording:
            print(f"❌ Recording {recording_id} not found or not transcribed")
            conn.close()
            return None

        # Check if already processed
        if not reprocess:
            cursor = conn.execute('''
                SELECT COUNT(*) as count FROM voice_ideas
                WHERE recording_id = ?
            ''', (recording_id,))

            if cursor.fetchone()['count'] > 0:
                print(f"⚠️  Recording {recording_id} already processed (use --reprocess to redo)")
                conn.close()
                return None

        transcription = recording['transcription']
        print(f"\n🎤 Processing Recording #{recording_id}")
        print(f"   Transcription: {transcription[:100]}...")

        # Extract structured data using Ollama
        extracted = self._extract_with_ollama(transcription)

        if not extracted:
            print(f"❌ Failed to extract ideas from recording {recording_id}")
            conn.close()
            return None

        # Save to voice_ideas table
        idea_id = self._save_to_database(conn, recording_id, extracted)

        # Generate documentation files
        self._generate_idea_doc(idea_id, recording_id, extracted)

        if extracted.get('has_pitch'):
            self._generate_pitch_deck(idea_id, recording_id, extracted)

        if extracted.get('has_hardware'):
            self._generate_hardware_spec(idea_id, recording_id, extracted)

        conn.close()

        print(f"✅ Extracted idea #{idea_id} from recording #{recording_id}")
        print(f"   Title: {extracted['title']}")
        print(f"   Tags: {', '.join(extracted['tags'])}")
        print(f"   Files: {len(extracted.get('files_created', []))} created")

        return extracted

    def _extract_with_ollama(self, transcription: str) -> Optional[Dict]:
        """Use Ollama to extract structured data from transcription"""

        prompt = f"""Analyze this voice memo transcription and extract structured information:

TRANSCRIPTION:
{transcription}

Extract and return ONLY valid JSON (no markdown, no commentary) with this structure:
{{
    "title": "Short descriptive title (5-10 words)",
    "summary": "One sentence summary of the main idea",
    "concept": "Detailed explanation of the concept (2-3 paragraphs)",
    "tags": ["tag1", "tag2", "tag3"],
    "domains": ["soulfra", "calriven", "deathtodata"],
    "technical_requirements": ["requirement1", "requirement2"],
    "has_pitch": true/false,
    "pitch_sections": {{
        "problem": "What problem this solves",
        "solution": "How this solves it",
        "market": "Who wants this",
        "traction": "What's been done so far"
    }},
    "has_hardware": true/false,
    "hardware_specs": {{
        "components": ["component1", "component2"],
        "requirements": ["req1", "req2"]
    }},
    "related_projects": ["project1", "project2"],
    "next_steps": ["step1", "step2", "step3"]
}}

Return ONLY the JSON object, nothing else."""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )

            if response.status_code != 200:
                print(f"❌ Ollama error: {response.status_code}")
                return None

            result = response.json()
            extracted_text = result.get('response', '')

            # Parse JSON response
            extracted = json.loads(extracted_text)

            return extracted

        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama connection error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"   Response: {extracted_text[:200]}")
            return None

    def _save_to_database(self, conn: sqlite3.Connection, recording_id: int, extracted: Dict) -> int:
        """Save extracted idea to voice_ideas table"""

        cursor = conn.execute('''
            INSERT INTO voice_ideas (
                recording_id, title, text, ai_insight, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            recording_id,
            extracted['title'],
            extracted['concept'],
            json.dumps(extracted),
            'living',
            datetime.now().isoformat()
        ))

        conn.commit()
        return cursor.lastrowid

    def _generate_idea_doc(self, idea_id: int, recording_id: int, extracted: Dict):
        """Generate markdown documentation for the idea"""

        # Clean title for filename
        safe_title = extracted['title'].lower().replace(' ', '-').replace('/', '-')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c == '-')

        filename = self.docs_dir / f"idea-{idea_id}-{safe_title}.md"

        content = f"""# {extracted['title']}

**Idea ID:** #{idea_id}
**Source:** Voice Recording #{recording_id}
**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** Living

## Summary

{extracted['summary']}

## Concept

{extracted['concept']}

## Tags

{', '.join(f'`{tag}`' for tag in extracted.get('tags', []))}

## Related Domains

{', '.join(f'**{domain}**' for domain in extracted.get('domains', []))}

## Technical Requirements

{chr(10).join(f'- {req}' for req in extracted.get('technical_requirements', []))}

## Related Projects

{chr(10).join(f'- {proj}' for proj in extracted.get('related_projects', []))}

## Next Steps

{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(extracted.get('next_steps', [])))}

---

**Voice Archive Link:** [Recording #{recording_id}](../../voice-archive/recordings/{recording_id}/)

**Generated:** {datetime.now().isoformat()}
"""

        with open(filename, 'w') as f:
            f.write(content)

        extracted.setdefault('files_created', []).append(str(filename))
        print(f"   📄 Created: {filename}")

    def _generate_pitch_deck(self, idea_id: int, recording_id: int, extracted: Dict):
        """Generate pitch deck markdown"""

        if not extracted.get('pitch_sections'):
            return

        safe_title = extracted['title'].lower().replace(' ', '-').replace('/', '-')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c == '-')

        filename = self.pitches_dir / f"pitch-{idea_id}-{safe_title}.md"

        pitch = extracted['pitch_sections']

        content = f"""# {extracted['title']} - Pitch Deck

**Idea ID:** #{idea_id}
**Voice Recording:** #{recording_id}

---

## 🎯 Problem

{pitch.get('problem', 'TBD')}

---

## 💡 Solution

{pitch.get('solution', 'TBD')}

---

## 📊 Market

{pitch.get('market', 'TBD')}

---

## 🚀 Traction

{pitch.get('traction', 'TBD')}

---

## 🔗 Links

- [Full Idea Doc](../voice-ideas/idea-{idea_id}-{safe_title}.md)
- [Voice Recording](../../voice-archive/recordings/{recording_id}/)

---

**Generated:** {datetime.now().isoformat()}
"""

        with open(filename, 'w') as f:
            f.write(content)

        extracted.setdefault('files_created', []).append(str(filename))
        print(f"   📊 Created: {filename}")

    def _generate_hardware_spec(self, idea_id: int, recording_id: int, extracted: Dict):
        """Generate hardware specification document"""

        if not extracted.get('hardware_specs'):
            return

        safe_title = extracted['title'].lower().replace(' ', '-').replace('/', '-')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c == '-')

        filename = self.hardware_dir / f"hardware-{idea_id}-{safe_title}.md"

        hw = extracted['hardware_specs']

        content = f"""# {extracted['title']} - Hardware Specification

**Idea ID:** #{idea_id}
**Voice Recording:** #{recording_id}

---

## Components Required

{chr(10).join(f'- {comp}' for comp in hw.get('components', []))}

---

## Requirements

{chr(10).join(f'- {req}' for req in hw.get('requirements', []))}

---

## 🔗 Links

- [Full Idea Doc](../voice-ideas/idea-{idea_id}-{safe_title}.md)
- [Voice Recording](../../voice-archive/recordings/{recording_id}/)

---

**Generated:** {datetime.now().isoformat()}
"""

        with open(filename, 'w') as f:
            f.write(content)

        extracted.setdefault('files_created', []).append(str(filename))
        print(f"   🔧 Created: {filename}")

    def process_all_unprocessed(self):
        """Process all recordings that don't have ideas extracted yet"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Find unprocessed recordings
        cursor = conn.execute('''
            SELECT r.id
            FROM simple_voice_recordings r
            LEFT JOIN voice_ideas vi ON r.id = vi.recording_id
            WHERE r.transcription IS NOT NULL
              AND vi.id IS NULL
            ORDER BY r.id
        ''')

        unprocessed = [row['id'] for row in cursor.fetchall()]
        conn.close()

        if not unprocessed:
            print("✅ No unprocessed recordings found")
            return

        print(f"\n📋 Found {len(unprocessed)} unprocessed recordings")
        print(f"   IDs: {', '.join(map(str, unprocessed))}")

        for recording_id in unprocessed:
            self.dissect_recording(recording_id)

        print(f"\n✅ Processed {len(unprocessed)} recordings")


def main():
    parser = argparse.ArgumentParser(description="Extract structured ideas from voice memos")
    parser.add_argument('--recording-id', type=int, help='Process specific recording ID')
    parser.add_argument('--process-all', action='store_true', help='Process all unprocessed recordings')
    parser.add_argument('--reprocess', action='store_true', help='Reprocess even if already done')
    parser.add_argument('--db-path', default='soulfra.db', help='Path to database')
    parser.add_argument('--ollama-url', default='http://localhost:11434', help='Ollama API URL')

    args = parser.parse_args()

    dissector = VoiceMemoDissector(db_path=args.db_path, ollama_url=args.ollama_url)

    if args.process_all:
        dissector.process_all_unprocessed()
    elif args.recording_id:
        dissector.dissect_recording(args.recording_id, reprocess=args.reprocess)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

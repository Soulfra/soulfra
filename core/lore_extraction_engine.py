#!/usr/bin/env python3
"""
Lore Extraction Engine - Reverse Engineer Personal Narrative from Voice Recordings

Takes fragmented voice memos and builds a coherent "origin story" about you:
- Aggregates all transcripts
- Extracts recurring themes, values, concepts
- Identifies worldview and communication style
- Generates narrative lore profile

Example:
    6 random voice memos about work, ideas, frustrations
    → "Matt's worldview centers on authentic connection, fighting cringe in social media,
       building genuine community. He values vulnerability and trust over performance."

Usage:
    from lore_extraction_engine import LoreExtractor

    extractor = LoreExtractor()
    lore = extractor.extract_user_lore(user_id=1)
    print(lore['origin_story'])

CLI:
    python3 lore_extraction_engine.py --user 1
    python3 lore_extraction_engine.py --user 1 --save
"""

import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db
from ollama_client import OllamaClient


class LoreExtractor:
    """Extract personal lore and narrative themes from voice recordings"""

    def __init__(self, model: str = 'soulfra-model'):
        self.client = OllamaClient()
        self.model = model

    def get_user_transcripts(self, user_id: int) -> List[Dict]:
        """Get all transcripts for a user"""
        db = get_db()

        recordings = db.execute('''
            SELECT id, filename, transcription, created_at
            FROM simple_voice_recordings
            WHERE user_id = ?
            AND transcription IS NOT NULL
            AND LENGTH(transcription) > 10
            ORDER BY created_at DESC
        ''', (user_id,)).fetchall()

        return [dict(r) for r in recordings]

    def extract_themes(self, transcripts: List[str]) -> Dict:
        """
        Extract recurring themes from multiple transcripts using Ollama

        Returns:
            {
                'themes': [str, str, ...],
                'values': [str, str, ...],
                'keywords': [str, str, ...],
                'communication_style': str
            }
        """
        # Combine all transcripts
        combined_text = '\n\n'.join([f"Recording {i+1}: {t}" for i, t in enumerate(transcripts)])

        system_prompt = """You are a narrative analyst extracting themes from voice recordings.

Analyze these voice memos and identify:
1. **Recurring themes** - What topics does this person talk about repeatedly?
2. **Core values** - What do they care about deeply?
3. **Key concepts** - What ideas/words appear often?
4. **Communication style** - How do they express themselves?

Be concise but insightful. Focus on patterns across ALL recordings.

Return valid JSON:
{
    "themes": ["theme1", "theme2", "theme3"],
    "values": ["value1", "value2", "value3"],
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "communication_style": "description of how they speak"
}"""

        prompt = f"""Analyze these voice recordings and extract patterns:

{combined_text}

What themes, values, keywords, and communication style emerge? Return valid JSON only."""

        try:
            result = self.client.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=800,
                timeout=90
            )

            if not result['success']:
                return {
                    'error': result.get('error', 'Ollama generation failed')
                }

            # Parse JSON response
            response_text = result['response'].strip()
            theme_data = self._extract_json(response_text)

            if not theme_data:
                return {
                    'error': 'Failed to parse themes JSON',
                    'raw_response': response_text[:500]
                }

            return theme_data

        except Exception as e:
            return {
                'error': str(e)
            }

    def generate_origin_story(self, transcripts: List[str], themes: Dict) -> str:
        """
        Generate narrative "origin story" from transcripts and extracted themes

        Returns:
            Origin story text (2-3 paragraphs)
        """
        combined_text = '\n'.join(transcripts[:5])  # Use first 5 recordings as samples

        system_prompt = """You are a storyteller creating personal "origin stories" from voice recordings.

Write a compelling 2-3 paragraph narrative that captures WHO this person is based on their voice memos.

Style:
- Third person or second person ("You are..." or "Matt is...")
- Insightful and authentic (no corporate bullshit)
- Focus on worldview, values, communication style
- Make it compelling like a character bio

Example:
"Matt's worldview centers on authentic connection in a sea of social media cringe. He fights against performance and validation games, seeking genuine community where people can be vulnerable and honest. His communication style is direct and passionate—he doesn't hide his frustrations or his vision for better digital spaces. Trust and belonging matter more to him than likes and followers."
"""

        prompt = f"""Based on these voice recordings and extracted themes, write a compelling origin story:

THEMES:
{json.dumps(themes, indent=2)}

SAMPLE RECORDINGS:
{combined_text}

Generate a 2-3 paragraph origin story that captures who this person is. Be authentic and insightful."""

        try:
            result = self.client.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=600,
                timeout=60
            )

            if not result['success']:
                return f"Error generating origin story: {result.get('error', 'Unknown error')}"

            return result['response'].strip()

        except Exception as e:
            return f"Error: {str(e)}"

    def extract_user_lore(self, user_id: int, save_to_db: bool = False) -> Dict:
        """
        Complete lore extraction for a user

        Args:
            user_id: User ID
            save_to_db: Save lore profile to database

        Returns:
            {
                'user_id': int,
                'recording_count': int,
                'transcripts': [str, str, ...],
                'themes': {...},
                'origin_story': str,
                'wordmap': {...},
                'generated_at': str
            }
        """
        # Get transcripts
        recordings = self.get_user_transcripts(user_id)

        if not recordings:
            return {
                'error': f'No transcripts found for user {user_id}',
                'user_id': user_id
            }

        transcripts = [r['transcription'] for r in recordings]

        # Extract themes
        themes = self.extract_themes(transcripts)

        if 'error' in themes:
            return {
                'error': themes['error'],
                'user_id': user_id,
                'recording_count': len(recordings),
                'transcripts': transcripts
            }

        # Generate origin story
        origin_story = self.generate_origin_story(transcripts, themes)

        # Get wordmap (if exists)
        db = get_db()
        wordmap_row = db.execute('''
            SELECT wordmap_json
            FROM user_wordmaps
            WHERE user_id = ?
        ''', (user_id,)).fetchone()

        wordmap = json.loads(wordmap_row['wordmap_json']) if wordmap_row and wordmap_row['wordmap_json'] else {}

        lore_profile = {
            'user_id': user_id,
            'recording_count': len(recordings),
            'total_words': sum(len(t.split()) for t in transcripts),
            'transcripts': transcripts,
            'themes': themes,
            'origin_story': origin_story,
            'wordmap': wordmap,
            'wordmap_size': len(wordmap),
            'generated_at': datetime.now().isoformat(),
            'model': self.model
        }

        # Save to database if requested
        if save_to_db:
            self._save_lore_profile(user_id, lore_profile)

        return lore_profile

    def _save_lore_profile(self, user_id: int, lore_profile: Dict):
        """Save lore profile to database"""
        db = get_db()

        # Create table if doesn't exist
        db.execute('''
            CREATE TABLE IF NOT EXISTS user_lore_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lore_json TEXT NOT NULL,
                recording_count INTEGER,
                origin_story TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Check if lore profile exists
        existing = db.execute('''
            SELECT id FROM user_lore_profiles WHERE user_id = ?
        ''', (user_id,)).fetchone()

        lore_json = json.dumps(lore_profile)

        if existing:
            # Update existing
            db.execute('''
                UPDATE user_lore_profiles
                SET lore_json = ?,
                    recording_count = ?,
                    origin_story = ?,
                    generated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (lore_json, lore_profile['recording_count'], lore_profile['origin_story'], user_id))
        else:
            # Create new
            db.execute('''
                INSERT INTO user_lore_profiles (user_id, lore_json, recording_count, origin_story)
                VALUES (?, ?, ?, ?)
            ''', (user_id, lore_json, lore_profile['recording_count'], lore_profile['origin_story']))

        db.commit()
        print(f"✅ Saved lore profile for user {user_id}")

    def get_saved_lore(self, user_id: int) -> Optional[Dict]:
        """Retrieve saved lore profile from database"""
        db = get_db()

        lore_row = db.execute('''
            SELECT lore_json, generated_at
            FROM user_lore_profiles
            WHERE user_id = ?
            ORDER BY generated_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()

        if lore_row and lore_row['lore_json']:
            lore = json.loads(lore_row['lore_json'])
            lore['last_generated'] = lore_row['generated_at']
            return lore

        return None

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from Ollama response (handles markdown code blocks)"""
        try:
            return json.loads(text)
        except:
            pass

        import re

        # Look for JSON in markdown code blocks or raw braces
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # Nested
            r'(\{[^{}]+\})'  # Simple
        ]

        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue

        return None


# =============================================================================
# CLI & Testing
# =============================================================================

if __name__ == '__main__':
    import sys

    print("="*70)
    print("🎭 LORE EXTRACTION ENGINE - Reverse Engineer Your Story")
    print("="*70)

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python3 lore_extraction_engine.py --user <user_id>")
        print("  python3 lore_extraction_engine.py --user <user_id> --save")
        print("\nExample:")
        print("  python3 lore_extraction_engine.py --user 1")
        print("  python3 lore_extraction_engine.py --user 1 --save")
        sys.exit(1)

    # Parse arguments
    user_id = None
    save_to_db = '--save' in sys.argv

    if '--user' in sys.argv:
        idx = sys.argv.index('--user')
        if idx + 1 < len(sys.argv):
            user_id = int(sys.argv[idx + 1])

    if not user_id:
        print("❌ Missing --user argument")
        sys.exit(1)

    # Extract lore
    extractor = LoreExtractor()

    print(f"\n📖 Extracting lore for user {user_id}...")
    print(f"💾 Save to database: {save_to_db}")
    print()

    lore = extractor.extract_user_lore(user_id, save_to_db=save_to_db)

    if 'error' in lore:
        print(f"❌ Error: {lore['error']}")
        sys.exit(1)

    # Display results
    print("="*70)
    print("📊 LORE PROFILE")
    print("="*70)
    print(f"User ID: {lore['user_id']}")
    print(f"Recordings analyzed: {lore['recording_count']}")
    print(f"Total words: {lore['total_words']}")
    print(f"Wordmap size: {lore['wordmap_size']} unique words")
    print(f"Generated: {lore['generated_at']}")
    print(f"Model: {lore['model']}")

    print("\n" + "="*70)
    print("🎯 EXTRACTED THEMES")
    print("="*70)

    if 'themes' in lore['themes']:
        print("\n📌 Recurring Themes:")
        for theme in lore['themes']['themes']:
            print(f"  • {theme}")

    if 'values' in lore['themes']:
        print("\n💎 Core Values:")
        for value in lore['themes']['values']:
            print(f"  • {value}")

    if 'keywords' in lore['themes']:
        print("\n🔑 Key Concepts:")
        for keyword in lore['themes']['keywords']:
            print(f"  • {keyword}")

    if 'communication_style' in lore['themes']:
        print(f"\n🗣️  Communication Style:")
        print(f"  {lore['themes']['communication_style']}")

    print("\n" + "="*70)
    print("📖 ORIGIN STORY")
    print("="*70)
    print()
    print(lore['origin_story'])
    print()

    if save_to_db:
        print("="*70)
        print("✅ Lore profile saved to database")
        print("="*70)
        print()
        print("Retrieve anytime with:")
        print(f"  extractor = LoreExtractor()")
        print(f"  lore = extractor.get_saved_lore(user_id={user_id})")

    print("\n" + "="*70)
    print("🎉 Lore extraction complete!")
    print("="*70)

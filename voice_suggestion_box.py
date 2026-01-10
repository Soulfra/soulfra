#!/usr/bin/env python3
"""
Voice Suggestion Box - Not Horrendous Questionnaires

Like old-school office suggestion box but modern:
- Voice memo instead of paper slip (30 sec recordings)
- AI extracts ideas automatically (no forms)
- SHA256 signature proves authenticity
- @Brand routing for themed presentation
- Community voice responses (not text comments)
- Living/Dead document lifecycle

Architecture: "The Diamond Facets"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

            VOICE MEMO (typescript-style immutable)
                        ↓
                  SHA256 SIGNATURE
                        ↓
            ┌───────────┼───────────┐
            ↓           ↓           ↓
       @soulfra    @deathtodata   Community
       facet       facet          suggestions
            ↓           ↓           ↓
    Same content, different angle, proven authentic

Usage:
    # Create suggestion box system
    from voice_suggestion_box import VoiceSuggestionBox

    box = VoiceSuggestionBox()

    # Submit voice suggestion
    result = box.submit_voice_suggestion(
        audio_data=audio_bytes,
        user_id=1,
        brand_slug='soulfra'
    )

    # Get suggestions for brand
    suggestions = box.get_brand_suggestions('soulfra')

    # Voice response to suggestion
    response = box.submit_voice_response(
        suggestion_id=123,
        audio_data=audio_bytes,
        user_id=2
    )

Like: Lateralus spiral - same truth, multiple interpretations
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database import get_db


# ==============================================================================
# CONFIG
# ==============================================================================

SUGGESTION_AUDIO_DIR = Path('./suggestion_audio')
SUGGESTION_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# VOICE SUGGESTION BOX
# ==============================================================================

class VoiceSuggestionBox:
    """
    Voice-first suggestion box with SHA256 authentication

    Not horrendous questionnaires - just record voice, AI does the rest.
    """

    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.db = get_db()

    def submit_voice_suggestion(
        self,
        audio_data: bytes,
        user_id: int,
        brand_slug: Optional[str] = None,
        category: str = 'general'
    ) -> Dict:
        """
        Submit voice suggestion (30 sec max, no forms)

        Flow:
        1. Save audio → Transcribe with Whisper
        2. Extract ideas with AI (Ollama)
        3. Generate SHA256 signature
        4. Store with brand context
        5. Return extracted ideas

        Args:
            audio_data: Audio bytes (WebM)
            user_id: User submitting suggestion
            brand_slug: Brand context (optional)
            category: Suggestion category

        Returns:
            {
                'suggestion_id': int,
                'ideas': List[Dict],
                'transcription': str,
                'sha256_hash': str,
                'brand_facets': List[str]  # Which brands can see this
            }
        """
        if not audio_data:
            return {'error': 'No audio data provided'}

        # Save audio
        filename = f"suggestion_{int(datetime.now().timestamp())}_{user_id}.webm"
        audio_path = SUGGESTION_AUDIO_DIR / filename
        audio_path.write_bytes(audio_data)

        # Transcribe with Whisper
        transcription = self._transcribe_audio(audio_path)

        if not transcription or transcription == "[NO TRANSCRIPTION]":
            return {'error': 'Transcription failed'}

        # Extract ideas with AI
        ideas = self._extract_ideas_from_transcript(transcription)

        # Build wordmap (for SHA256 signature)
        from wordmap_pitch_integrator import extract_wordmap_from_transcript

        wordmap = extract_wordmap_from_transcript(transcription, top_n=20)

        # Generate SHA256 hash (proves authenticity)
        content_hash = self._generate_content_hash(transcription, wordmap)

        # Store suggestion
        cursor = self.db.execute('''
            INSERT INTO voice_suggestions
            (user_id, filename, audio_path, transcription, ideas_json, wordmap_json,
             sha256_hash, brand_slug, category, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            filename,
            str(audio_path),
            transcription,
            json.dumps(ideas),
            json.dumps(wordmap),
            content_hash,
            brand_slug,
            category,
            'living',  # Start as "living" document
            datetime.now().isoformat()
        ))

        suggestion_id = cursor.lastrowid
        self.db.commit()

        # Determine which brand facets can see this
        brand_facets = self._determine_brand_facets(wordmap, brand_slug)

        return {
            'suggestion_id': suggestion_id,
            'ideas': ideas,
            'transcription': transcription,
            'sha256_hash': content_hash,
            'brand_facets': brand_facets,
            'status': 'living'
        }

    def submit_voice_response(
        self,
        suggestion_id: int,
        audio_data: bytes,
        user_id: int
    ) -> Dict:
        """
        Submit voice response to existing suggestion

        Flow:
        1. Save audio → Transcribe
        2. Extract response ideas
        3. Link to original suggestion (SHA256 chain)
        4. Store response

        Args:
            suggestion_id: Original suggestion ID
            audio_data: Response audio bytes
            user_id: User responding

        Returns:
            {
                'response_id': int,
                'ideas': List[Dict],
                'original_hash': str,
                'response_hash': str,
                'chain_verified': bool
            }
        """
        # Get original suggestion
        original = self.db.execute('''
            SELECT id, sha256_hash, transcription, wordmap_json, brand_slug
            FROM voice_suggestions
            WHERE id = ?
        ''', (suggestion_id,)).fetchone()

        if not original:
            return {'error': 'Original suggestion not found'}

        # Save response audio
        filename = f"response_{suggestion_id}_{int(datetime.now().timestamp())}_{user_id}.webm"
        audio_path = SUGGESTION_AUDIO_DIR / filename
        audio_path.write_bytes(audio_data)

        # Transcribe
        transcription = self._transcribe_audio(audio_path)

        if not transcription:
            return {'error': 'Transcription failed'}

        # Extract ideas
        ideas = self._extract_ideas_from_transcript(transcription, is_response=True)

        # Build wordmap
        from wordmap_pitch_integrator import extract_wordmap_from_transcript

        wordmap = extract_wordmap_from_transcript(transcription, top_n=20)

        # Generate response hash
        response_hash = self._generate_content_hash(transcription, wordmap)

        # Create SHA256 chain (response → original)
        chain_hash = hashlib.sha256(
            (response_hash + original['sha256_hash']).encode()
        ).hexdigest()

        # Store response
        cursor = self.db.execute('''
            INSERT INTO voice_suggestion_responses
            (suggestion_id, user_id, filename, audio_path, transcription,
             ideas_json, wordmap_json, sha256_hash, chain_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            suggestion_id,
            user_id,
            filename,
            str(audio_path),
            transcription,
            json.dumps(ideas),
            json.dumps(wordmap),
            response_hash,
            chain_hash,
            datetime.now().isoformat()
        ))

        response_id = cursor.lastrowid
        self.db.commit()

        # Verify chain
        chain_verified = self._verify_chain(original['sha256_hash'], response_hash, chain_hash)

        return {
            'response_id': response_id,
            'ideas': ideas,
            'original_hash': original['sha256_hash'],
            'response_hash': response_hash,
            'chain_hash': chain_hash,
            'chain_verified': chain_verified
        }

    def get_brand_suggestions(
        self,
        brand_slug: str,
        status: str = 'living',
        limit: int = 50
    ) -> List[Dict]:
        """
        Get suggestions visible to brand facet

        Each brand sees suggestions through their themed lens
        (same content, different presentation)

        Args:
            brand_slug: Brand to view suggestions for
            status: living/dead
            limit: Max results

        Returns:
            List of suggestion dicts
        """
        # Get suggestions for this brand
        suggestions = self.db.execute('''
            SELECT
                id, user_id, transcription, ideas_json, sha256_hash,
                brand_slug, category, status, created_at,
                (SELECT COUNT(*) FROM voice_suggestion_responses
                 WHERE suggestion_id = voice_suggestions.id) as response_count
            FROM voice_suggestions
            WHERE (brand_slug = ? OR brand_slug IS NULL)
              AND status = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (brand_slug, status, limit)).fetchall()

        results = []

        for row in suggestions:
            ideas = json.loads(row['ideas_json']) if row['ideas_json'] else []

            results.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'transcription': row['transcription'],
                'ideas': ideas,
                'sha256_hash': row['sha256_hash'],
                'brand_slug': row['brand_slug'] or 'all',
                'category': row['category'],
                'status': row['status'],
                'response_count': row['response_count'],
                'created_at': row['created_at']
            })

        return results

    def get_suggestion_with_responses(self, suggestion_id: int) -> Dict:
        """
        Get suggestion with all voice responses (full thread)

        Returns:
            {
                'original': Dict,
                'responses': List[Dict],
                'chain_verified': bool
            }
        """
        # Get original
        original = self.db.execute('''
            SELECT * FROM voice_suggestions WHERE id = ?
        ''', (suggestion_id,)).fetchone()

        if not original:
            return {'error': 'Suggestion not found'}

        # Get responses
        responses = self.db.execute('''
            SELECT * FROM voice_suggestion_responses
            WHERE suggestion_id = ?
            ORDER BY created_at ASC
        ''', (suggestion_id,)).fetchall()

        response_list = []

        for row in responses:
            ideas = json.loads(row['ideas_json']) if row['ideas_json'] else []

            response_list.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'transcription': row['transcription'],
                'ideas': ideas,
                'sha256_hash': row['sha256_hash'],
                'chain_hash': row['chain_hash'],
                'created_at': row['created_at']
            })

        return {
            'original': {
                'id': original['id'],
                'user_id': original['user_id'],
                'transcription': original['transcription'],
                'ideas': json.loads(original['ideas_json']) if original['ideas_json'] else [],
                'sha256_hash': original['sha256_hash'],
                'brand_slug': original['brand_slug'],
                'category': original['category'],
                'status': original['status'],
                'created_at': original['created_at']
            },
            'responses': response_list,
            'chain_verified': all(
                self._verify_chain(original['sha256_hash'], r['sha256_hash'], r['chain_hash'])
                for r in response_list
            ) if response_list else None
        }

    def _transcribe_audio(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio with Whisper"""
        try:
            from whisper_transcriber import WhisperTranscriber

            transcriber = WhisperTranscriber()
            result = transcriber.transcribe(str(audio_path))

            return result['text']

        except Exception as e:
            print(f"⚠️  Transcription failed: {e}")
            return "[NO TRANSCRIPTION]"

    def _extract_ideas_from_transcript(
        self,
        transcription: str,
        is_response: bool = False
    ) -> List[Dict]:
        """
        Extract ideas from transcript using AI

        Args:
            transcription: Full transcript
            is_response: Is this a response to another suggestion?

        Returns:
            List of idea dicts
        """
        if not transcription or transcription == "[NO TRANSCRIPTION]":
            return []

        try:
            import requests

            if is_response:
                prompt = f"""Analyze this voice response and extract the key points.

Response: "{transcription}"

Return JSON array with format:
[
  {{
    "title": "Short title (3-5 words)",
    "text": "Main point (1-2 sentences)",
    "score": 75,
    "insight": "Why this response matters"
  }}
]"""
            else:
                prompt = f"""Extract the TOP suggestions/ideas from this voice memo.

Voice memo: "{transcription}"

Return JSON array with format:
[
  {{
    "title": "Suggestion title (3-5 words)",
    "text": "Core suggestion (1-2 sentences)",
    "score": 85,
    "insight": "Why implement this"
  }}
]

Return 2-5 ideas maximum."""

            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )

            if response.ok:
                data = response.json()
                ai_text = data.get('response', '').strip()

                # Parse JSON
                import re

                json_match = re.search(r'\[.*\]', ai_text, re.DOTALL)

                if json_match:
                    ideas = json.loads(json_match.group())
                    return ideas

            return []

        except Exception as e:
            print(f"⚠️  AI extraction failed: {e}")
            return []

    def _generate_content_hash(self, transcription: str, wordmap: Dict) -> str:
        """Generate SHA256 hash of content"""
        # Combine transcript + wordmap for hash
        content = {
            'transcription': transcription,
            'wordmap': dict(sorted(wordmap.items()))
        }

        content_json = json.dumps(content, sort_keys=True)

        return hashlib.sha256(content_json.encode()).hexdigest()

    def _determine_brand_facets(
        self,
        wordmap: Dict,
        primary_brand: Optional[str] = None
    ) -> List[str]:
        """
        Determine which brand facets can see this suggestion

        Uses wordmap alignment to find relevant brands

        Args:
            wordmap: Suggestion wordmap
            primary_brand: Primary brand (always included)

        Returns:
            List of brand slugs
        """
        facets = []

        if primary_brand:
            facets.append(primary_brand)

        # Check alignment with other brands
        # (This would query brand wordmaps and check alignment %)
        # For now, return primary brand or 'all'

        if not facets:
            facets.append('all')

        return facets

    def _verify_chain(
        self,
        original_hash: str,
        response_hash: str,
        chain_hash: str
    ) -> bool:
        """Verify SHA256 chain integrity"""
        expected_chain = hashlib.sha256(
            (response_hash + original_hash).encode()
        ).hexdigest()

        return expected_chain == chain_hash


# ==============================================================================
# DATABASE SCHEMA (for migration)
# ==============================================================================

SUGGESTION_BOX_SCHEMA = """
-- Voice suggestions (original submissions)
CREATE TABLE IF NOT EXISTS voice_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    audio_path TEXT NOT NULL,
    transcription TEXT,
    ideas_json TEXT,  -- JSON array of extracted ideas
    wordmap_json TEXT,  -- JSON dict of word frequencies
    sha256_hash TEXT NOT NULL,  -- Content authenticity
    brand_slug TEXT,  -- Which brand facet
    category TEXT DEFAULT 'general',
    status TEXT DEFAULT 'living',  -- living/dead
    created_at TEXT NOT NULL,
    expires_at TEXT,  -- For dead documents (1 year)
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Voice responses to suggestions
CREATE TABLE IF NOT EXISTS voice_suggestion_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    audio_path TEXT NOT NULL,
    transcription TEXT,
    ideas_json TEXT,
    wordmap_json TEXT,
    sha256_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,  -- SHA256 chain (response + original)
    created_at TEXT NOT NULL,
    FOREIGN KEY (suggestion_id) REFERENCES voice_suggestions(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_voice_suggestions_brand ON voice_suggestions(brand_slug, status);
CREATE INDEX IF NOT EXISTS idx_voice_suggestions_user ON voice_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_suggestion_responses_suggestion ON voice_suggestion_responses(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_voice_suggestion_responses_user ON voice_suggestion_responses(user_id);
"""


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Voice Suggestion Box - Not Horrendous Questionnaires'
    )

    parser.add_argument(
        '--setup-db',
        action='store_true',
        help='Setup database schema'
    )

    parser.add_argument(
        '--show-suggestions',
        type=str,
        metavar='BRAND',
        help='Show suggestions for brand'
    )

    parser.add_argument(
        '--show-thread',
        type=int,
        metavar='ID',
        help='Show suggestion thread with responses'
    )

    args = parser.parse_args()

    try:
        if args.setup_db:
            print("Setting up database schema...")
            db = get_db()
            db.executescript(SUGGESTION_BOX_SCHEMA)
            db.commit()
            print("✅ Database schema created")

        elif args.show_suggestions:
            box = VoiceSuggestionBox()
            suggestions = box.get_brand_suggestions(args.show_suggestions)

            print(f"\n📬 SUGGESTIONS FOR @{args.show_suggestions}")
            print(f"{'='*70}\n")

            for s in suggestions:
                print(f"ID: {s['id']} | Responses: {s['response_count']}")
                print(f"Hash: {s['sha256_hash'][:16]}...")
                print(f"Ideas: {len(s['ideas'])}")

                for i, idea in enumerate(s['ideas'][:2], 1):
                    print(f"  {i}. {idea['title']} (score: {idea['score']})")

                print()

        elif args.show_thread:
            box = VoiceSuggestionBox()
            thread = box.get_suggestion_with_responses(args.show_thread)

            if 'error' in thread:
                print(f"❌ {thread['error']}")
                return

            print(f"\n💬 SUGGESTION THREAD #{args.show_thread}")
            print(f"{'='*70}\n")

            print(f"ORIGINAL:")
            print(f"  Hash: {thread['original']['sha256_hash'][:16]}...")
            print(f"  Ideas: {len(thread['original']['ideas'])}")
            print()

            print(f"RESPONSES ({len(thread['responses'])}):")

            for i, r in enumerate(thread['responses'], 1):
                print(f"  {i}. User {r['user_id']}")
                print(f"     Hash: {r['sha256_hash'][:16]}...")
                print(f"     Chain: {'✅ Verified' if thread['chain_verified'] else '❌ Invalid'}")
                print()

        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

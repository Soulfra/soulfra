#!/usr/bin/env python3
"""
Wordmap Transcript Generator - Build to 256 Words with AI

Generates synthetic voice memo transcripts to build your wordmap to 256 unique words.
Uses your existing recordings as "seed" to maintain your voice/style.

Why 256 words?
- SHA256 produces 256-bit hash
- 256 words = natural language hash space
- Your vocabulary fingerprint
- Deterministic identity proof

Usage:
    # Build wordmap to 256 words
    python3 wordmap_transcript_generator.py --build-to-256

    # Generate specific number of transcripts
    python3 wordmap_transcript_generator.py --generate 10

    # Save synthetic transcripts to database
    python3 wordmap_transcript_generator.py --build-to-256 --save-to-db

    # Show current wordmap state
    python3 wordmap_transcript_generator.py --show-wordmap
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db
from wordmap_pitch_integrator import extract_wordmap_from_transcript, tokenize
from user_wordmap_engine import update_user_wordmap, get_user_wordmap


# ==============================================================================
# CONFIG
# ==============================================================================

OLLAMA_URL = 'http://localhost:11434'
SYNTHETIC_TRANSCRIPTS_DIR = Path('./synthetic_transcripts')
SYNTHETIC_TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Topics to generate (expands on user's existing themes)
GENERATION_TOPICS = [
    "social media authenticity and the pressure to perform online",
    "building genuine online communities vs surface-level engagement",
    "content moderation challenges and freedom of expression",
    "privacy vs sharing personal information on platforms",
    "AI-generated content and its impact on creativity",
    "creator economy and monetization pressures",
    "platform algorithms and their effect on discourse",
    "digital identity and how we present ourselves online",
    "trust and reputation in online spaces",
    "future of social platforms and decentralization",
    "mental health impacts of constant connectivity",
    "authenticity vs curation in personal branding",
    "echo chambers and filter bubbles",
    "online harassment and toxic behavior",
    "influencer culture and parasocial relationships"
]


# ==============================================================================
# WORDMAP TRANSCRIPT GENERATOR
# ==============================================================================

class WordmapTranscriptGenerator:
    """Generate synthetic voice memo transcripts to build wordmap"""

    def __init__(
        self,
        user_id: int = 1,
        ollama_url: str = OLLAMA_URL
    ):
        self.user_id = user_id
        self.ollama_url = ollama_url.rstrip('/')
        self.db = get_db()

    def check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.ok
        except Exception:
            return False

    def get_seed_transcripts(self) -> List[str]:
        """Get user's existing transcripts as seed material"""
        recordings = self.db.execute('''
            SELECT transcription
            FROM simple_voice_recordings
            WHERE user_id = ? AND transcription IS NOT NULL
            ORDER BY LENGTH(transcription) DESC
        ''', (self.user_id,)).fetchall()

        return [r['transcription'] for r in recordings]

    def get_current_wordmap_state(self) -> Dict:
        """Get current wordmap state"""
        wordmap_data = get_user_wordmap(self.user_id)

        if not wordmap_data:
            return {
                'exists': False,
                'word_count': 0,
                'wordmap': {},
                'recording_count': 0
            }

        return {
            'exists': True,
            'word_count': len(wordmap_data['wordmap']),
            'wordmap': wordmap_data['wordmap'],
            'recording_count': wordmap_data['recording_count']
        }

    def generate_synthetic_transcript(
        self,
        topic: str,
        seed_transcripts: List[str],
        model: str = 'llama3',
        target_length: int = 250
    ) -> Optional[str]:
        """
        Generate one synthetic voice memo transcript

        Args:
            topic: Topic to discuss
            seed_transcripts: Existing transcripts for style
            model: Ollama model
            target_length: Target word count

        Returns:
            Generated transcript text
        """
        # Build prompt from seed transcripts
        seed_examples = "\n\n".join(seed_transcripts[:3]) if seed_transcripts else ""

        prompt = f"""You are generating a voice memo transcript.

Here are examples of the user's natural speaking style:

{seed_examples}

Now generate a NEW voice memo where the user talks about:
"{topic}"

Requirements:
- Sound like natural spoken words (not formal writing)
- Use "I", "you", "we" (conversational)
- Include filler words occasionally (like, you know, I think)
- Be passionate and opinionated
- Around {target_length} words
- Sound like the examples above

Generate the voice memo:"""

        print(f"\n🤖 Generating transcript about: {topic[:50]}...")

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )

            if not response.ok:
                print(f"   ❌ Ollama error: {response.status_code}")
                return None

            data = response.json()
            transcript = data.get('response', '').strip()

            # Clean up (remove quotes if Ollama wrapped it)
            if transcript.startswith('"') and transcript.endswith('"'):
                transcript = transcript[1:-1]

            word_count = len(transcript.split())
            print(f"   ✅ Generated {word_count} words")

            return transcript

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def build_to_target(
        self,
        target_words: int = 256,
        batch_size: int = 5,
        save_to_db: bool = False,
        model: str = 'llama3'
    ) -> Dict:
        """
        Generate transcripts until wordmap reaches target size

        Args:
            target_words: Target wordmap size (default: 256)
            batch_size: Transcripts per batch
            save_to_db: Save synthetic transcripts to database
            model: Ollama model to use

        Returns:
            {
                'final_wordmap': dict,
                'word_count': int,
                'transcripts_generated': int,
                'sha256_hash': str
            }
        """
        print(f"\n{'='*70}")
        print(f"  WORDMAP BUILDER - Target: {target_words} unique words")
        print(f"{'='*70}\n")

        # Get current state
        current_state = self.get_current_wordmap_state()
        current_word_count = current_state['word_count']

        print(f"📊 Current state:")
        print(f"   Wordmap size: {current_word_count} words")
        print(f"   Target: {target_words} words")
        print(f"   Gap: {target_words - current_word_count} words needed\n")

        if current_word_count >= target_words:
            print(f"✅ Already at target! ({current_word_count} words)")
            wordmap_hash = self._hash_wordmap(current_state['wordmap'])
            return {
                'final_wordmap': current_state['wordmap'],
                'word_count': current_word_count,
                'transcripts_generated': 0,
                'sha256_hash': wordmap_hash
            }

        # Get seed transcripts
        seed_transcripts = self.get_seed_transcripts()

        if not seed_transcripts:
            print("⚠️  No existing transcripts found. Using generic style.")
            seed_transcripts = []

        # Generate in batches
        batch_num = 1
        total_generated = 0
        generated_transcripts = []

        while current_word_count < target_words:
            print(f"🎙️  BATCH {batch_num} ({batch_size} transcripts)")
            print(f"{'='*70}")

            batch_transcripts = []

            for i in range(batch_size):
                topic_idx = (batch_num - 1) * batch_size + i
                topic = GENERATION_TOPICS[topic_idx % len(GENERATION_TOPICS)]

                transcript = self.generate_synthetic_transcript(
                    topic=topic,
                    seed_transcripts=seed_transcripts,
                    model=model
                )

                if transcript:
                    batch_transcripts.append(transcript)
                    generated_transcripts.append({
                        'topic': topic,
                        'transcript': transcript,
                        'batch': batch_num
                    })

                    # Update wordmap
                    if save_to_db:
                        # Save as synthetic recording
                        self._save_synthetic_recording(transcript, topic)

                    # Update user wordmap (always, to track progress)
                    update_result = update_user_wordmap(
                        self.user_id,
                        recording_id=None,  # Synthetic, no recording ID
                        transcript=transcript
                    )

                    current_word_count = len(update_result['wordmap'])
                    total_generated += 1

                    print(f"      Wordmap now: {current_word_count} words (+{current_word_count - current_state['word_count']} total)")

                    if current_word_count >= target_words:
                        print(f"\n✅ TARGET REACHED! ({current_word_count} words)")
                        break

            # Save batch
            self._save_batch(batch_num, batch_transcripts)

            batch_num += 1

            if current_word_count >= target_words:
                break

        # Get final wordmap
        final_state = self.get_current_wordmap_state()
        final_wordmap = final_state['wordmap']
        wordmap_hash = self._hash_wordmap(final_wordmap)

        print(f"\n{'='*70}")
        print(f"  🎉 WORDMAP BUILDING COMPLETE")
        print(f"{'='*70}")
        print(f"Final size: {len(final_wordmap)} unique words")
        print(f"Transcripts generated: {total_generated}")
        print(f"SHA256 hash: {wordmap_hash}")
        print(f"{'='*70}\n")

        return {
            'final_wordmap': final_wordmap,
            'word_count': len(final_wordmap),
            'transcripts_generated': total_generated,
            'generated_transcripts': generated_transcripts,
            'sha256_hash': wordmap_hash
        }

    def _hash_wordmap(self, wordmap: Dict[str, int]) -> str:
        """Generate SHA256 hash of wordmap"""
        # Sort for deterministic hashing
        sorted_wordmap = dict(sorted(wordmap.items()))
        wordmap_json = json.dumps(sorted_wordmap, sort_keys=True)
        return hashlib.sha256(wordmap_json.encode()).hexdigest()

    def _save_synthetic_recording(self, transcript: str, topic: str):
        """Save synthetic transcript as voice recording (optional)"""
        filename = f"synthetic_{int(datetime.now().timestamp())}.txt"

        self.db.execute('''
            INSERT INTO simple_voice_recordings
            (filename, audio_data, file_size, transcription, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            b'',  # No audio data for synthetic
            0,
            transcript,
            self.user_id,
            datetime.now().isoformat()
        ))
        self.db.commit()

    def _save_batch(self, batch_num: int, transcripts: List[str]):
        """Save batch of transcripts to file"""
        batch_file = SYNTHETIC_TRANSCRIPTS_DIR / f"batch_{batch_num}.json"

        data = {
            'batch': batch_num,
            'count': len(transcripts),
            'transcripts': transcripts,
            'generated_at': datetime.now().isoformat()
        }

        batch_file.write_text(json.dumps(data, indent=2))
        print(f"\n   📁 Saved batch to: {batch_file}")


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Wordmap Transcript Generator - Build to 256 Words'
    )

    parser.add_argument(
        '--build-to-256',
        action='store_true',
        help='Build wordmap to 256 unique words'
    )

    parser.add_argument(
        '--target',
        type=int,
        default=256,
        help='Target wordmap size (default: 256)'
    )

    parser.add_argument(
        '--generate',
        type=int,
        metavar='N',
        help='Generate N synthetic transcripts'
    )

    parser.add_argument(
        '--save-to-db',
        action='store_true',
        help='Save synthetic transcripts to database'
    )

    parser.add_argument(
        '--show-wordmap',
        action='store_true',
        help='Show current wordmap state'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='llama3',
        help='Ollama model to use'
    )

    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID (default: 1)'
    )

    args = parser.parse_args()

    generator = WordmapTranscriptGenerator(user_id=args.user_id)

    # Check Ollama
    if not generator.check_ollama():
        print("❌ Ollama not running!")
        print("   Start: ollama serve")
        sys.exit(1)

    try:
        if args.show_wordmap:
            # Show current wordmap
            state = generator.get_current_wordmap_state()

            print(f"\n📊 WORDMAP STATE")
            print(f"{'='*70}")
            print(f"Exists: {state['exists']}")
            print(f"Word count: {state['word_count']}")
            print(f"Recording count: {state.get('recording_count', 0)}")

            if state['wordmap']:
                print(f"\nTop 20 words:")
                sorted_words = sorted(
                    state['wordmap'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]

                for word, count in sorted_words:
                    print(f"   {word}: {count}")

                wordmap_hash = generator._hash_wordmap(state['wordmap'])
                print(f"\nSHA256: {wordmap_hash}")

            print(f"{'='*70}\n")

        elif args.build_to_256 or args.target:
            # Build to target
            result = generator.build_to_target(
                target_words=args.target,
                save_to_db=args.save_to_db,
                model=args.model
            )

            print(f"\n📋 FINAL RESULTS:")
            print(f"   Words: {result['word_count']}")
            print(f"   Generated: {result['transcripts_generated']} transcripts")
            print(f"   SHA256: {result['sha256_hash']}")
            print()

        elif args.generate:
            # Generate specific number
            print(f"Generating {args.generate} transcripts...")
            # TODO: Implement fixed-count generation

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Creative Onboarding - Alternative Ways to Join

Instead of boring forms, users can:
1. Draw something → OCR validates
2. Write a poem → Ollama judges creativity
3. Solve a puzzle → Ollama validates answer
4. Upload a file → System validates format

Each method grants access with different tiers.

**Why Creative Onboarding?**
- More engaging than forms
- Filters bots naturally
- Shows user creativity/effort
- No email verification needed
- Privacy-friendly (no external APIs)

**How It Works:**
1. User chooses challenge type
2. System generates challenge or prompt
3. User submits answer
4. AI validates (Ollama for most, OCR for drawings)
5. Score recorded in database
6. API key generated if passed

**Tiers:**
- **Tier 1**: Basic challenges → Basic access
- **Tier 2**: Advanced challenges or file upload → File imports
- **Tier 3**: Multiple challenges passed → API access
- **Tier 4**: GitHub OAuth with high activity → Brand forking

**Usage:**
```python
from creative_onboarding import CreativeOnboarding

onboarding = CreativeOnboarding()

# Generate challenge
challenge = onboarding.generate_challenge('draw')
# Returns: {'type': 'draw', 'prompt': 'Draw the word PRIVACY', 'id': 'ch_abc123'}

# Validate answer
result = onboarding.validate_challenge(challenge_id='ch_abc123', user_answer='image_data_here')
# Returns: {'passed': True, 'score': 8.5, 'api_key': 'sk_creative_abc123'}
```
"""

import os
import sqlite3
import secrets
import hashlib
import base64
import json
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from PIL import Image
import io

# Optional: pytesseract for OCR (install: pip install pytesseract)
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: pytesseract not installed. OCR challenges will be disabled.")

from database import get_db


# ==============================================================================
# CONFIG
# ==============================================================================

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama2')

# Challenge difficulty scoring
DIFFICULTY_TIERS = {
    'easy': 1,      # Basic math, simple drawings
    'medium': 2,    # Poems, puzzles
    'hard': 3,      # File uploads, complex challenges
}

# Score thresholds (0-10 scale)
PASSING_SCORES = {
    'draw': 6.0,      # OCR must recognize 60% of text
    'write': 7.0,     # Ollama must rate poem 7/10 or higher
    'puzzle': 8.0,    # Must get puzzle correct (strict)
    'upload': 5.0,    # File must be valid format
}


# ==============================================================================
# CREATIVE ONBOARDING CLASS
# ==============================================================================

class CreativeOnboarding:
    """
    Handle creative challenges for user onboarding
    """

    def __init__(self, ollama_host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.ollama_host = ollama_host
        self.model = model


    # ==========================================================================
    # CHALLENGE GENERATION
    # ==========================================================================

    def generate_challenge(self, challenge_type: str, difficulty: str = 'easy') -> Dict:
        """
        Generate a creative challenge

        Args:
            challenge_type: 'draw', 'write', 'puzzle', 'upload'
            difficulty: 'easy', 'medium', 'hard'

        Returns:
            Dict with challenge details

        Example:
            >>> onboarding = CreativeOnboarding()
            >>> challenge = onboarding.generate_challenge('draw')
            >>> print(challenge['prompt'])
            Draw the word "PRIVACY" in large letters
        """
        challenge_id = self._generate_challenge_id()

        generators = {
            'draw': self._generate_draw_challenge,
            'write': self._generate_write_challenge,
            'puzzle': self._generate_puzzle_challenge,
            'upload': self._generate_upload_challenge,
        }

        generator = generators.get(challenge_type)
        if not generator:
            raise ValueError(f"Unknown challenge type: {challenge_type}")

        challenge_data = generator(difficulty)

        # Store challenge in database
        conn = get_db()
        conn.execute('''
            INSERT INTO creative_challenges
            (challenge_id, challenge_type, difficulty, prompt, expected_answer, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            challenge_id,
            challenge_type,
            difficulty,
            challenge_data['prompt'],
            challenge_data.get('expected_answer', ''),
            datetime.now()
        ))
        conn.commit()
        conn.close()

        return {
            'id': challenge_id,
            'type': challenge_type,
            'difficulty': difficulty,
            'prompt': challenge_data['prompt'],
            'tier': DIFFICULTY_TIERS[difficulty],
            'metadata': challenge_data.get('metadata', {})
        }


    def _generate_draw_challenge(self, difficulty: str) -> Dict:
        """Generate drawing challenge"""
        if not HAS_OCR:
            return {
                'prompt': 'OCR not available. Please install pytesseract.',
                'expected_answer': ''
            }

        words = {
            'easy': ['PRIVACY', 'DATA', 'SECURE', 'FREEDOM'],
            'medium': ['ENCRYPTION', 'ANONYMOUS', 'DECENTRALIZED'],
            'hard': ['ZERO-KNOWLEDGE', 'CRYPTOGRAPHY', 'SELF-SOVEREIGN']
        }

        word = secrets.choice(words.get(difficulty, words['easy']))

        return {
            'prompt': f'Draw the word "{word}" in large, clear letters',
            'expected_answer': word.lower(),
            'metadata': {'word_length': len(word)}
        }


    def _generate_write_challenge(self, difficulty: str) -> Dict:
        """Generate creative writing challenge using Ollama"""
        prompts = {
            'easy': [
                "Write a haiku about data privacy",
                "Write a short poem about encryption",
                "Describe privacy in 3 lines"
            ],
            'medium': [
                "Write a limerick about surveillance",
                "Write a sonnet about digital freedom",
                "Write a short story about anonymous communication"
            ],
            'hard': [
                "Write a villanelle about cryptography",
                "Write an epic poem about decentralization",
                "Write a philosophical essay on digital rights in 5 sentences"
            ]
        }

        prompt = secrets.choice(prompts.get(difficulty, prompts['easy']))

        return {
            'prompt': prompt,
            'expected_answer': '',  # Will be judged by Ollama
            'metadata': {'min_words': 10 if difficulty == 'easy' else 50}
        }


    def _generate_puzzle_challenge(self, difficulty: str) -> Dict:
        """Generate logic/math puzzle"""
        if difficulty == 'easy':
            a = secrets.randbelow(20) + 1
            b = secrets.randbelow(20) + 1
            answer = a + b
            return {
                'prompt': f'What is {a} + {b}?',
                'expected_answer': str(answer)
            }

        elif difficulty == 'medium':
            num = secrets.randbelow(256)
            answer = hex(num)[2:]  # Remove '0x' prefix
            return {
                'prompt': f'What is {num} in hexadecimal? (lowercase, no prefix)',
                'expected_answer': answer
            }

        else:  # hard
            # Use Ollama to generate a logic puzzle
            puzzle = self._ask_ollama(
                "Generate a short logic puzzle with one clear answer. "
                "Format: State the puzzle, then on a new line write 'ANSWER: <answer>'"
            )

            # Parse puzzle and answer
            if 'ANSWER:' in puzzle:
                parts = puzzle.split('ANSWER:')
                return {
                    'prompt': parts[0].strip(),
                    'expected_answer': parts[1].strip().lower()
                }
            else:
                # Fallback to math
                a = secrets.randbelow(50) + 10
                b = secrets.randbelow(10) + 1
                answer = a * b
                return {
                    'prompt': f'What is {a} × {b}?',
                    'expected_answer': str(answer)
                }


    def _generate_upload_challenge(self, difficulty: str) -> Dict:
        """Generate file upload challenge"""
        formats = {
            'easy': 'txt, md',
            'medium': 'txt, md, html, json',
            'hard': 'any format (txt, md, html, doc, json, csv, yaml)'
        }

        return {
            'prompt': f'Upload a file about privacy, encryption, or digital rights. Supported formats: {formats[difficulty]}',
            'expected_answer': '',
            'metadata': {'allowed_formats': formats[difficulty]}
        }


    # ==========================================================================
    # CHALLENGE VALIDATION
    # ==========================================================================

    def validate_challenge(
        self,
        challenge_id: str,
        user_answer: str,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Validate user's answer to challenge

        Args:
            challenge_id: Challenge ID
            user_answer: User's submission
            user_id: Optional user ID (for creating account)

        Returns:
            Dict with validation results

        Example:
            >>> result = onboarding.validate_challenge('ch_123', 'privacy')
            >>> print(result['passed'])
            True
        """
        # Fetch challenge from database
        conn = get_db()
        cursor = conn.execute('''
            SELECT challenge_type, difficulty, prompt, expected_answer
            FROM creative_challenges
            WHERE challenge_id = ?
        ''', (challenge_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError('Challenge not found')

        challenge_type, difficulty, prompt, expected_answer = row

        # Validate based on type
        validators = {
            'draw': self._validate_draw,
            'write': self._validate_write,
            'puzzle': self._validate_puzzle,
            'upload': self._validate_upload,
        }

        validator = validators.get(challenge_type)
        if not validator:
            conn.close()
            raise ValueError(f"Unknown challenge type: {challenge_type}")

        # Run validation
        score, feedback = validator(user_answer, expected_answer, prompt)

        # Check if passed
        threshold = PASSING_SCORES[challenge_type]
        passed = score >= threshold

        # Record attempt in database
        conn.execute('''
            INSERT INTO challenge_attempts
            (user_id, challenge_id, challenge_type, user_answer, ai_score, passed, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            challenge_id,
            challenge_type,
            user_answer[:1000],  # Truncate long answers
            score,
            passed,
            feedback,
            datetime.now()
        ))

        # If passed, generate API key
        api_key = None
        tier = DIFFICULTY_TIERS[difficulty]

        if passed and user_id:
            api_key = self._generate_api_key(user_id, challenge_type, tier, conn)

        conn.commit()
        conn.close()

        return {
            'passed': passed,
            'score': score,
            'threshold': threshold,
            'feedback': feedback,
            'tier': tier if passed else 0,
            'api_key': api_key
        }


    def _validate_draw(self, image_data: str, expected_word: str, prompt: str) -> Tuple[float, str]:
        """
        Validate drawing using OCR

        Args:
            image_data: Base64-encoded image or file path
            expected_word: Word that should be drawn
            prompt: Original prompt

        Returns:
            (score, feedback)
        """
        if not HAS_OCR:
            return 0.0, "OCR not available"

        try:
            # Decode image
            if image_data.startswith('data:image'):
                # Base64 data URL
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Run OCR
            ocr_text = pytesseract.image_to_string(image).lower()

            # Check if expected word is in OCR text
            if expected_word.lower() in ocr_text:
                score = 10.0
                feedback = f"✓ Perfect! OCR detected '{expected_word}'"
            else:
                # Fuzzy match: check how many characters match
                matches = sum(c in ocr_text for c in expected_word.lower())
                score = (matches / len(expected_word)) * 10

                if score >= 6.0:
                    feedback = f"Good attempt! OCR found some text: {ocr_text[:50]}"
                else:
                    feedback = f"Drawing not clear enough. OCR result: {ocr_text[:50]}"

            return score, feedback

        except Exception as e:
            return 0.0, f"Error processing image: {str(e)}"


    def _validate_write(self, user_text: str, expected_answer: str, prompt: str) -> Tuple[float, str]:
        """
        Validate creative writing using Ollama

        Args:
            user_text: User's written submission
            expected_answer: Not used (Ollama judges)
            prompt: Original writing prompt

        Returns:
            (score, feedback)
        """
        # Ask Ollama to judge the writing
        judge_prompt = f"""
You are a creative writing judge. Rate this submission on a scale of 0-10.

Original prompt: {prompt}

User's submission:
{user_text}

Provide your rating as a number from 0-10, followed by brief feedback.
Format your response exactly like this:
SCORE: 8.5
FEEDBACK: This is creative and well-written...
"""

        try:
            response = self._ask_ollama(judge_prompt)

            # Parse score and feedback
            score = 0.0
            feedback = response

            if 'SCORE:' in response:
                parts = response.split('SCORE:')[1].split('\n')
                score_str = parts[0].strip()
                try:
                    score = float(score_str)
                except:
                    score = 5.0  # Default middle score

            if 'FEEDBACK:' in response:
                feedback = response.split('FEEDBACK:')[1].strip()

            return score, feedback

        except Exception as e:
            return 0.0, f"Error validating with Ollama: {str(e)}"


    def _validate_puzzle(self, user_answer: str, expected_answer: str, prompt: str) -> Tuple[float, str]:
        """
        Validate puzzle answer

        Args:
            user_answer: User's answer
            expected_answer: Correct answer
            prompt: Original puzzle

        Returns:
            (score, feedback)
        """
        user_answer_clean = user_answer.strip().lower()
        expected_answer_clean = expected_answer.strip().lower()

        # Try exact match first
        if user_answer_clean == expected_answer_clean:
            return 10.0, "✓ Correct!"

        # Try Ollama for flexible validation
        validate_prompt = f"""
Question: {prompt}
Expected answer: {expected_answer}
User's answer: {user_answer}

Is the user's answer correct or close enough? Consider variations in wording.
Respond with ONLY "yes" or "no", nothing else.
"""

        try:
            response = self._ask_ollama(validate_prompt).lower()

            if 'yes' in response:
                return 9.0, "Correct! (Validated by AI)"
            else:
                return 0.0, f"Incorrect. Expected: {expected_answer}"

        except:
            return 0.0, f"Incorrect. Expected: {expected_answer}"


    def _validate_upload(self, file_data: str, expected_answer: str, prompt: str) -> Tuple[float, str]:
        """
        Validate uploaded file

        Args:
            file_data: File content or metadata JSON
            expected_answer: Not used
            prompt: Upload requirements

        Returns:
            (score, feedback)
        """
        try:
            # Parse file metadata
            if file_data.startswith('{'):
                metadata = json.loads(file_data)
                filename = metadata.get('filename', '')
                content = metadata.get('content', '')
                file_size = metadata.get('size', 0)
            else:
                # Direct content
                filename = 'uploaded.txt'
                content = file_data
                file_size = len(file_data)

            # Check file is not empty
            if file_size == 0 or len(content) < 10:
                return 0.0, "File is too small or empty"

            # Check minimum content length
            if len(content) < 100:
                return 5.0, "File uploaded, but content is very short"

            # Ask Ollama to check if content is relevant
            relevance_prompt = f"""
Does this text relate to privacy, encryption, security, or digital rights?

Text:
{content[:500]}

Respond with a score from 0-10 and brief explanation.
Format: SCORE: 8.0
FEEDBACK: This text discusses...
"""

            response = self._ask_ollama(relevance_prompt)

            # Parse score
            score = 7.0  # Default decent score
            feedback = "File uploaded successfully"

            if 'SCORE:' in response:
                try:
                    score_str = response.split('SCORE:')[1].split('\n')[0].strip()
                    score = float(score_str)
                except:
                    pass

            if 'FEEDBACK:' in response:
                feedback = response.split('FEEDBACK:')[1].strip()

            return score, feedback

        except Exception as e:
            return 0.0, f"Error processing file: {str(e)}"


    # ==========================================================================
    # OLLAMA INTEGRATION
    # ==========================================================================

    def _ask_ollama(self, prompt: str) -> str:
        """
        Ask Ollama a question

        Args:
            prompt: Question or prompt

        Returns:
            Ollama's response
        """
        response = requests.post(
            f'{self.ollama_host}/api/generate',
            json={
                'model': self.model,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        return response.json().get('response', '').strip()


    # ==========================================================================
    # API KEY GENERATION
    # ==========================================================================

    def _generate_api_key(
        self,
        user_id: int,
        challenge_type: str,
        tier: int,
        conn: sqlite3.Connection
    ) -> str:
        """
        Generate API key for user who passed challenge

        Args:
            user_id: User ID
            challenge_type: Type of challenge passed
            tier: Access tier earned
            conn: Database connection

        Returns:
            API key string
        """
        # Check if user already has key
        existing = conn.execute('''
            SELECT api_key FROM api_keys
            WHERE user_id = ? AND source = 'creative_challenge'
        ''', (user_id,)).fetchone()

        if existing:
            return existing[0]

        # Generate new key
        random_suffix = secrets.token_hex(8)
        api_key = f'sk_creative_{challenge_type}_{random_suffix}'

        # Store in database
        conn.execute('''
            INSERT INTO api_keys
            (user_id, api_key, source, tier, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            api_key,
            'creative_challenge',
            tier,
            datetime.now(),
            True
        ))

        # Update user's tier
        conn.execute('UPDATE users SET tier = ? WHERE id = ?', (tier, user_id))

        return api_key


    def _generate_challenge_id(self) -> str:
        """Generate unique challenge ID"""
        return f'ch_{secrets.token_hex(12)}'


# ==============================================================================
# DATABASE MIGRATION
# ==============================================================================

def init_creative_tables():
    """
    Initialize database tables for creative onboarding

    Run this once to set up tables:
    >>> from creative_onboarding import init_creative_tables
    >>> init_creative_tables()
    """
    conn = get_db()

    # Creative challenges table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS creative_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id TEXT UNIQUE NOT NULL,
            challenge_type TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            prompt TEXT NOT NULL,
            expected_answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Challenge attempts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS challenge_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id TEXT NOT NULL,
            challenge_type TEXT NOT NULL,
            user_answer TEXT,
            ai_score REAL,
            passed BOOLEAN,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (challenge_id) REFERENCES creative_challenges(challenge_id)
        )
    ''')

    # Update api_keys table to support creative challenges
    # Check if 'source' column exists
    cursor = conn.execute("PRAGMA table_info(api_keys)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'source' not in columns:
        # Add source column
        conn.execute('''
            ALTER TABLE api_keys
            ADD COLUMN source TEXT DEFAULT 'manual'
        ''')

    # Indexes
    conn.execute('CREATE INDEX IF NOT EXISTS idx_challenges_id ON creative_challenges(challenge_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_attempts_user ON challenge_attempts(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_attempts_challenge ON challenge_attempts(challenge_id)')

    conn.commit()
    conn.close()

    print('✅ Creative onboarding tables created!')


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Creative Onboarding System')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--generate', type=str, choices=['draw', 'write', 'puzzle', 'upload'],
                        help='Generate a challenge')
    parser.add_argument('--validate', type=str, help='Validate challenge (challenge_id)')
    parser.add_argument('--answer', type=str, help='User answer for validation')
    parser.add_argument('--difficulty', type=str, default='easy', choices=['easy', 'medium', 'hard'],
                        help='Challenge difficulty')

    args = parser.parse_args()

    if args.init:
        init_creative_tables()

    elif args.generate:
        onboarding = CreativeOnboarding()
        challenge = onboarding.generate_challenge(args.generate, args.difficulty)
        print(f'\n🎨 Challenge Generated:\n')
        print(f'   ID: {challenge["id"]}')
        print(f'   Type: {challenge["type"]}')
        print(f'   Difficulty: {challenge["difficulty"]}')
        print(f'   Tier: {challenge["tier"]}')
        print(f'\n   Prompt: {challenge["prompt"]}\n')

    elif args.validate and args.answer:
        onboarding = CreativeOnboarding()
        result = onboarding.validate_challenge(args.validate, args.answer)

        print(f'\n{"✅" if result["passed"] else "❌"} Validation Result:\n')
        print(f'   Score: {result["score"]:.1f}/{result["threshold"]:.1f}')
        print(f'   Status: {"PASSED" if result["passed"] else "FAILED"}')
        print(f'   Feedback: {result["feedback"]}')

        if result['api_key']:
            print(f'\n   🎉 API Key: {result["api_key"]}')
            print(f'   Tier: {result["tier"]}\n')

    else:
        print('Usage: python3 creative_onboarding.py --init')
        print('       python3 creative_onboarding.py --generate draw --difficulty easy')
        print('       python3 creative_onboarding.py --validate ch_abc123 --answer "my answer"')

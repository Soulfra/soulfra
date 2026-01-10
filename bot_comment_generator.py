#!/usr/bin/env python3
"""
Bot Comment Generator - 85 IQ Wholesome Social Proof

Generates friendly, simple, wholesome comments using Ollama.
NOT trash-tier spam - genuine-feeling encouragement at accessible reading level.

Personality:
- 85 IQ reading level (8th grade, simple vocabulary)
- Wholesome and encouraging
- Short and punchy (1-2 sentences)
- No complex analysis or buzzwords
- Feels human, not robotic

Usage:
    from bot_comment_generator import BotCommentGenerator

    bot = BotCommentGenerator()
    comment = bot.generate_comment(
        content="Voice memo about launching a startup",
        content_type="voice_memo"
    )
    # Returns: "This is really cool! Hope you make it happen!"
"""

import requests
import json
import random
from datetime import datetime
from typing import Dict, Optional
from database import get_db


class BotCommentGenerator:
    """Generate 85 IQ wholesome comments using Ollama"""

    # Ollama endpoint (local server)
    OLLAMA_URL = "http://192.168.1.87:11434/api/generate"

    # Comment personality templates
    PERSONALITY_PROMPTS = [
        "You are a friendly, encouraging person who leaves short supportive comments. Use simple language (8th grade level). Be genuine and wholesome. 1-2 sentences max.",
        "You're someone who always sees the positive in things. Comment enthusiastically but simply. No complex words. Just be nice and encouraging.",
        "You're a supportive friend leaving a quick comment. Be warm and real. Simple words only. Make it feel human, not like AI.",
    ]

    # Wholesome reaction starters (for variety)
    REACTIONS = [
        "This is",
        "I like",
        "Really",
        "That's",
        "Wow",
        "Nice",
        "Cool",
        "Love",
        "Great",
        "Awesome",
    ]

    def __init__(self, ollama_url: Optional[str] = None):
        """Initialize bot comment generator"""
        if ollama_url:
            self.OLLAMA_URL = ollama_url

        self.init_database()

    def init_database(self):
        """Create table for bot comments if it doesn't exist"""
        db = get_db()

        db.execute('''
            CREATE TABLE IF NOT EXISTS bot_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                bot_personality TEXT DEFAULT 'wholesome_85',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        db.commit()

    def generate_comment(
        self,
        content: str,
        content_type: str = "voice_memo",
        max_length: int = 100
    ) -> str:
        """
        Generate wholesome comment for content

        Args:
            content: The content to comment on (transcript, post text, etc.)
            content_type: Type of content (voice_memo, post, idea, etc.)
            max_length: Max character length for comment

        Returns:
            str: Generated comment text
        """
        # Choose random personality prompt for variety
        personality = random.choice(self.PERSONALITY_PROMPTS)

        # Build Ollama prompt
        prompt = f"""{personality}

Content to comment on:
{content[:500]}

Write a short, encouraging comment (1-2 sentences, simple words):"""

        try:
            # Call Ollama
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": "llama3.2:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.9,  # Higher temp for variety
                        "top_p": 0.95,
                        "num_predict": 50,  # Short responses only
                    }
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                comment = result.get('response', '').strip()

                # Clean up comment
                comment = self._clean_comment(comment, max_length)

                return comment
            else:
                # Fallback to template if Ollama fails
                return self._generate_fallback_comment(content)

        except Exception as e:
            print(f"⚠️  Ollama error: {e}")
            return self._generate_fallback_comment(content)

    def _clean_comment(self, comment: str, max_length: int) -> str:
        """Clean up AI-generated comment"""
        # Remove quotes if AI added them
        comment = comment.strip('"\'')

        # Remove "Comment:" prefix if present
        if comment.lower().startswith('comment:'):
            comment = comment[8:].strip()

        # Truncate at sentence boundary if too long
        if len(comment) > max_length:
            # Try to cut at period
            sentences = comment.split('.')
            if len(sentences) > 1:
                comment = sentences[0] + '.'
            else:
                # Hard cut
                comment = comment[:max_length].rsplit(' ', 1)[0] + '...'

        # Ensure it ends with punctuation
        if not comment[-1] in '.!?':
            comment += '!'

        return comment

    def _generate_fallback_comment(self, content: str) -> str:
        """Generate simple template comment if Ollama unavailable"""
        templates = [
            "This is really cool!",
            "I like this idea!",
            "That's awesome, keep going!",
            "Really interesting stuff!",
            "Nice work on this!",
            "This is great!",
            "Love it, hope it works out!",
            "Wow, that's cool!",
            "Great idea here!",
            "This seems really good!",
        ]

        return random.choice(templates)

    def save_comment(
        self,
        target_type: str,
        target_id: int,
        comment_text: str
    ) -> int:
        """
        Save generated comment to database

        Returns:
            int: Comment ID
        """
        db = get_db()

        cursor = db.execute('''
            INSERT INTO bot_comments (target_type, target_id, comment_text)
            VALUES (?, ?, ?)
        ''', (target_type, target_id, comment_text))

        db.commit()

        return cursor.lastrowid

    def generate_and_save(
        self,
        content: str,
        target_type: str,
        target_id: int
    ) -> Dict:
        """
        Generate comment and save to database in one call

        Returns:
            dict: {
                'comment_id': int,
                'comment_text': str,
                'generated_at': str
            }
        """
        # Generate comment
        comment_text = self.generate_comment(content, target_type)

        # Save to database
        comment_id = self.save_comment(target_type, target_id, comment_text)

        return {
            'comment_id': comment_id,
            'comment_text': comment_text,
            'generated_at': datetime.now().isoformat()
        }

    def get_comments_for_target(
        self,
        target_type: str,
        target_id: int
    ) -> list:
        """Get all bot comments for a specific target"""
        db = get_db()
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        cursor = db.execute('''
            SELECT * FROM bot_comments
            WHERE target_type = ? AND target_id = ?
            ORDER BY generated_at DESC
        ''', (target_type, target_id))

        return cursor.fetchall()


def main():
    """CLI for testing bot comment generator"""
    import argparse

    parser = argparse.ArgumentParser(description='Bot Comment Generator')
    parser.add_argument('--test', action='store_true', help='Run test generation')
    parser.add_argument('--content', type=str, help='Content to comment on')
    parser.add_argument('--generate', type=int, help='Generate N comments for testing')

    args = parser.parse_args()

    bot = BotCommentGenerator()

    if args.test or args.content:
        test_content = args.content or "I just launched my first startup! It's a voice memo app where AI extracts insights from your random thoughts."

        print("="*70)
        print("🤖 Bot Comment Generator Test")
        print("="*70)
        print(f"\nContent:\n{test_content}\n")

        if args.generate:
            print(f"Generating {args.generate} comments:\n")
            for i in range(args.generate):
                comment = bot.generate_comment(test_content)
                print(f"{i+1}. {comment}")
        else:
            comment = bot.generate_comment(test_content)
            print(f"Generated Comment:\n{comment}")

    else:
        print("Usage: python bot_comment_generator.py --test")
        print("       python bot_comment_generator.py --content 'Your content here'")
        print("       python bot_comment_generator.py --generate 10")


if __name__ == '__main__':
    main()

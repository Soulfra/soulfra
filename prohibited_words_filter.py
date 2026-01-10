#!/usr/bin/env python3
"""
Prohibited Words Filter - Content Moderation for Voice Recordings

Filters voice transcriptions for prohibited words/patterns before storage.
Different domains can have different prohibited word lists.

Use cases:
- soulfra.com: Filter profanity, hate speech, spam
- cringeproof.com: Allow raw authentic expression (minimal filtering)
- deathtodata.com: Filter PII, phone numbers, addresses

Usage:
```python
from prohibited_words_filter import check_prohibited, filter_transcription

# Check if transcription contains prohibited words
if check_prohibited("transcription text", domain="soulfra.com"):
    print("Contains prohibited content")

# Auto-filter/redact prohibited words
filtered = filter_transcription("transcription text", domain="soulfra.com")
```
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from database import get_db


# Default prohibited patterns (used if database doesn't have domain-specific patterns)
DEFAULT_PATTERNS = {
    'hate_speech': [
        r'\b(n[i1]gg[ae]r|f[a4]gg[o0]t|tr[a4]nny)\b',
        # Add more patterns as needed
    ],
    'spam': [
        r'click here',
        r'buy now',
        r'limited time offer',
        r'act fast',
    ],
    'pii': [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone numbers
        r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',     # SSN
        r'\b\d{1,5}\s\w+\s(?:street|st|avenue|ave|road|rd|boulevard|blvd)\b',  # Addresses
    ]
}


def get_prohibited_patterns(domain: str) -> Dict[str, List[str]]:
    """
    Get prohibited word patterns for a specific domain

    Returns: Dict of category -> list of regex patterns
    """
    db = get_db()

    try:
        result = db.execute('''
            SELECT patterns_json
            FROM prohibited_words
            WHERE domain = ?
        ''', (domain,)).fetchone()

        if result and result['patterns_json']:
            return json.loads(result['patterns_json'])
        else:
            # Return default patterns if domain doesn't have custom ones
            return DEFAULT_PATTERNS

    except Exception as e:
        print(f"⚠️  Error loading prohibited patterns: {e}")
        return DEFAULT_PATTERNS
    finally:
        db.close()


def check_prohibited(text: str, domain: str = "all") -> Tuple[bool, Optional[List[Dict]]]:
    """
    Check if text contains prohibited words

    Args:
        text: Text to check
        domain: Domain to check against (e.g., "soulfra.com")

    Returns:
        (is_prohibited, matches)
        - is_prohibited: True if text contains prohibited content
        - matches: List of dicts with pattern matches and categories
    """
    patterns = get_prohibited_patterns(domain)
    matches = []

    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            regex_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in regex_matches:
                matches.append({
                    'category': category,
                    'pattern': pattern,
                    'match': match.group(),
                    'position': match.span()
                })

    is_prohibited = len(matches) > 0
    return is_prohibited, matches if is_prohibited else None


def filter_transcription(text: str, domain: str = "all", redact_char: str = "*") -> str:
    """
    Filter/redact prohibited words from transcription

    Args:
        text: Original transcription
        domain: Domain to filter for
        redact_char: Character to use for redaction

    Returns:
        Filtered transcription with prohibited words redacted
    """
    patterns = get_prohibited_patterns(domain)
    filtered_text = text

    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            # Replace matches with redacted version (same length)
            def redact_match(match):
                return redact_char * len(match.group())

            filtered_text = re.sub(pattern, redact_match, filtered_text, flags=re.IGNORECASE)

    return filtered_text


def log_prohibited_detection(recording_id: int, matches: List[Dict]):
    """
    Log prohibited word detection for moderation review

    Creates audit trail in database
    """
    db = get_db()

    try:
        for match in matches:
            db.execute('''
                INSERT INTO prohibited_word_log (recording_id, category, pattern, matched_text, detected_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                recording_id,
                match['category'],
                match['pattern'],
                match['match']
            ))

        db.commit()
        print(f"📝 Logged {len(matches)} prohibited word detections for recording #{recording_id}")

    except Exception as e:
        print(f"⚠️  Error logging prohibited words: {e}")
    finally:
        db.close()


def setup_prohibited_words_table():
    """
    Create database tables for prohibited words filtering

    Run this once to initialize the system
    """
    db = get_db()

    # Table for domain-specific prohibited patterns
    db.execute('''
        CREATE TABLE IF NOT EXISTS prohibited_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            patterns_json TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for logging prohibited word detections
    db.execute('''
        CREATE TABLE IF NOT EXISTS prohibited_word_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            pattern TEXT NOT NULL,
            matched_text TEXT NOT NULL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed BOOLEAN DEFAULT 0,
            action_taken TEXT,
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id)
        )
    ''')

    db.commit()
    print("✅ Prohibited words tables created")

    # Insert default patterns for each domain
    domains_config = [
        {
            'domain': 'soulfra.com',
            'description': 'Soulfra: Filters profanity, hate speech, spam',
            'patterns': {
                'hate_speech': DEFAULT_PATTERNS['hate_speech'],
                'spam': DEFAULT_PATTERNS['spam'],
            }
        },
        {
            'domain': 'cringeproof.com',
            'description': 'CringeProof: Minimal filtering (authentic expression)',
            'patterns': {
                'hate_speech': DEFAULT_PATTERNS['hate_speech'],  # Only block hate speech
            }
        },
        {
            'domain': 'deathtodata.com',
            'description': 'DeathToData: Filters PII, tracking IDs',
            'patterns': {
                'pii': DEFAULT_PATTERNS['pii'],
            }
        },
    ]

    for config in domains_config:
        db.execute('''
            INSERT OR REPLACE INTO prohibited_words (domain, patterns_json, description)
            VALUES (?, ?, ?)
        ''', (config['domain'], json.dumps(config['patterns']), config['description']))

    db.commit()
    db.close()

    print("✅ Default prohibited patterns inserted for all domains")


if __name__ == '__main__':
    print("🛡️  Setting up prohibited words filtering system...")
    setup_prohibited_words_table()

    # Test the filter
    test_text = "This is a test transcription with a phone number 555-123-4567 and some content"
    is_prohibited, matches = check_prohibited(test_text, domain="deathtodata.com")

    if is_prohibited:
        print(f"\n⚠️  Test text contains prohibited content:")
        for match in matches:
            print(f"  - Category: {match['category']}")
            print(f"    Matched: {match['match']}")

        filtered = filter_transcription(test_text, domain="deathtodata.com")
        print(f"\n📝 Filtered version:\n{filtered}")
    else:
        print("\n✅ Test text passed filter")

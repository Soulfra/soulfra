#!/usr/bin/env python3
"""
Seed Domain Wordmaps - Initialize domains with keyword profiles

Creates initial wordmaps for domains so voice matching actually works.
Without this, domains have no baseline to match against.

Usage:
    python3 seed_domain_wordmaps.py
"""

import json
from database import get_db
from datetime import datetime


# Domain keyword profiles
# Each domain gets a starter wordmap based on its concept
DOMAIN_SEEDS = {
    'cringeproof.com': {
        'keywords': [
            'cringe', 'proof', 'authentic', 'truth', 'genuine', 'real',
            'fake', 'validation', 'social', 'media', 'game', 'play',
            'news', 'articles', 'scraping', 'content', 'feed'
        ],
        'weights': [10, 10, 8, 8, 7, 7, 6, 5, 5, 5, 4, 4, 3, 3, 3, 2, 2]
    },

    'soulfra.com': {
        'keywords': [
            'soul', 'fragments', 'voice', 'memory', 'recording', 'capture',
            'essence', 'identity', 'preservation', 'archive', 'personal',
            'audio', 'transcription', 'words', 'thoughts'
        ],
        'weights': [10, 10, 8, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 2]
    },

    'deathtodata.com': {
        'keywords': [
            'privacy', 'data', 'surveillance', 'tracking', 'protection',
            'security', 'anonymous', 'encrypted', 'freedom', 'digital',
            'rights', 'control', 'ownership', 'personal', 'information'
        ],
        'weights': [10, 10, 8, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 2]
    },

    'calriven.com': {
        'keywords': [
            'calendar', 'driven', 'schedule', 'time', 'planning', 'events',
            'organization', 'productivity', 'automation', 'workflow',
            'tasks', 'deadlines', 'reminders', 'goals'
        ],
        'weights': [10, 10, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 2]
    },

    'hollowtown.com': {
        'keywords': [
            'empty', 'hollow', 'abandoned', 'ghost', 'town', 'forgotten',
            'lost', 'memories', 'nostalgia', 'past', 'history', 'stories',
            'community', 'place'
        ],
        'weights': [10, 10, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 2]
    },

    'howtocookathome.com': {
        'keywords': [
            'cooking', 'recipes', 'food', 'kitchen', 'home', 'meals',
            'ingredients', 'preparation', 'tutorial', 'instructions',
            'easy', 'simple', 'delicious', 'healthy'
        ],
        'weights': [10, 10, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 2]
    },

    'niceleak.com': {
        'keywords': [
            'leak', 'reveal', 'expose', 'disclosure', 'transparency',
            'secrets', 'hidden', 'information', 'truth', 'whistleblower',
            'release', 'public', 'share'
        ],
        'weights': [10, 10, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2]
    },

    'oofbox.com': {
        'keywords': [
            'mistake', 'error', 'oops', 'fail', 'learning', 'feedback',
            'improvement', 'iteration', 'testing', 'experiment', 'try',
            'attempt', 'practice'
        ],
        'weights': [10, 10, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2]
    }
}


def seed_domain_wordmap(domain: str, keywords: list, weights: list) -> bool:
    """
    Seed a domain with initial wordmap

    Args:
        domain: Domain name
        keywords: List of keywords
        weights: List of weights (same length as keywords)

    Returns:
        True if successful
    """
    db = get_db()

    # Create wordmap dict
    wordmap = {}
    for keyword, weight in zip(keywords, weights):
        wordmap[keyword] = weight

    # Check if wordmap already exists
    existing = db.execute('''
        SELECT wordmap_json FROM domain_wordmaps WHERE domain = ?
    ''', (domain,)).fetchone()

    if existing:
        print(f"   ⚠️  {domain} already has wordmap - skipping")
        return False

    # Insert new wordmap
    db.execute('''
        INSERT INTO domain_wordmaps (domain, wordmap_json, contributor_count, last_updated)
        VALUES (?, ?, ?, ?)
    ''', (
        domain,
        json.dumps(wordmap),
        0,  # No contributors yet (seeded)
        datetime.now()
    ))
    db.commit()

    print(f"   ✅ {domain} seeded with {len(keywords)} keywords")
    return True


def seed_all_domains():
    """Seed all domains with initial wordmaps"""
    print(f"\n{'='*70}")
    print(f"🌱 SEEDING DOMAIN WORDMAPS")
    print(f"{'='*70}")
    print(f"Seeding {len(DOMAIN_SEEDS)} domains...\n")

    seeded_count = 0
    skipped_count = 0

    for domain, config in DOMAIN_SEEDS.items():
        keywords = config['keywords']
        weights = config['weights']

        # Ensure weights list matches keywords length
        if len(weights) < len(keywords):
            weights = weights + [1] * (len(keywords) - len(weights))

        if seed_domain_wordmap(domain, keywords, weights):
            seeded_count += 1
        else:
            skipped_count += 1

    print(f"\n{'='*70}")
    print(f"📊 SEEDING COMPLETE")
    print(f"{'='*70}")
    print(f"Seeded: {seeded_count}")
    print(f"Skipped: {skipped_count}")
    print(f"{'='*70}\n")

    if seeded_count > 0:
        print(f"✅ Domains ready for matching!")
        print(f"\nNext steps:")
        print(f"1. Record voice memo about your project (1-2 min)")
        print(f"2. Run: python3 economy_mesh_network.py --user 1")
        print(f"3. Watch the cascade find matches and claim rewards\n")


if __name__ == '__main__':
    try:
        seed_all_domains()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

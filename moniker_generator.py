#!/usr/bin/env python3
"""
Moniker Generator - Domain-Specific Username Generator

Generates unique monikers (pseudonyms) for each domain based on user's master username.
Each domain has its own personality:
- soulfra.com: spiritual, reflective (e.g., "soul_wanderer")
- deathtodata.com: privacy-focused, anonymous (e.g., "ghost_falcon_2847")
- calriven.com: technical, professional (e.g., "dev_architect_1492")
- cringeproof.com: creative, playful (e.g., "content_wizard_5931")
"""

import hashlib
import random


# Domain-specific word banks
DOMAIN_WORDS = {
    'soulfra.com': {
        'adjectives': ['soul', 'spirit', 'cosmic', 'zen', 'mystic', 'serene', 'ethereal', 'luminous', 'sacred', 'divine'],
        'nouns': ['wanderer', 'seeker', 'dreamer', 'guide', 'pilgrim', 'sage', 'oracle', 'nomad', 'voyager', 'keeper']
    },
    'deathtodata.com': {
        'adjectives': ['ghost', 'shadow', 'phantom', 'cipher', 'stealth', 'silent', 'masked', 'void', 'dark', 'hidden'],
        'nouns': ['falcon', 'wolf', 'raven', 'lynx', 'viper', 'hawk', 'panther', 'spider', 'fox', 'owl']
    },
    'calriven.com': {
        'adjectives': ['dev', 'code', 'tech', 'system', 'data', 'cloud', 'binary', 'logic', 'cyber', 'quantum'],
        'nouns': ['architect', 'engineer', 'builder', 'wizard', 'master', 'forge', 'nexus', 'matrix', 'hub', 'core']
    },
    'cringeproof.com': {
        'adjectives': ['content', 'viral', 'meme', 'epic', 'legendary', 'based', 'fire', 'savage', 'peak', 'main'],
        'nouns': ['wizard', 'king', 'queen', 'lord', 'boss', 'chef', 'legend', 'star', 'icon', 'creator']
    },
    'howtocookathome.com': {
        'adjectives': ['home', 'kitchen', 'chef', 'fresh', 'tasty', 'spicy', 'savory', 'crispy', 'golden', 'herb'],
        'nouns': ['cook', 'baker', 'master', 'artist', 'wizard', 'pro', 'guru', 'ninja', 'expert', 'chef']
    }
}


def generate_moniker(username, domain, user_id=None):
    """
    Generate domain-specific moniker based on username

    Args:
        username: Master username (e.g., "matthew")
        domain: Target domain (e.g., "deathtodata.com")
        user_id: Optional user ID for additional uniqueness

    Returns:
        str: Domain-specific moniker (e.g., "ghost_falcon_2847")
    """

    # Get word bank for domain
    if domain not in DOMAIN_WORDS:
        domain = 'soulfra.com'  # Default fallback

    words = DOMAIN_WORDS[domain]

    # Create deterministic seed from username + domain
    seed_string = f"{username}:{domain}"
    seed_hash = hashlib.sha256(seed_string.encode()).hexdigest()

    # Use first 8 chars of hash as seed for consistent randomness
    seed = int(seed_hash[:8], 16)
    rng = random.Random(seed)

    # Pick words based on hash
    adjective = rng.choice(words['adjectives'])
    noun = rng.choice(words['nouns'])

    # Generate 4-digit suffix from hash (deterministic)
    number_seed = int(seed_hash[8:12], 16) % 10000

    # Format: adjective_noun_number
    moniker = f"{adjective}_{noun}_{number_seed:04d}"

    return moniker


def generate_all_monikers(username, user_id=None):
    """
    Generate monikers for all domains

    Args:
        username: Master username
        user_id: Optional user ID

    Returns:
        dict: {domain: moniker} mapping
    """
    domains = [
        'soulfra.com',
        'deathtodata.com',
        'calriven.com',
        'cringeproof.com',
        'howtocookathome.com'
    ]

    monikers = {}
    for domain in domains:
        monikers[domain] = generate_moniker(username, domain, user_id)

    return monikers


def preview_monikers(username):
    """
    Preview what monikers a username would generate

    Useful for debugging/testing
    """
    print(f"\n🎭 Moniker Preview for: {username}\n")
    print("=" * 60)

    monikers = generate_all_monikers(username)

    for domain, moniker in monikers.items():
        print(f"  {domain:25s} → {moniker}")

    print("=" * 60)


# CLI
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Moniker Generator")
        print("\nUsage:")
        print("  python3 moniker_generator.py <username>")
        print("\nExample:")
        print("  python3 moniker_generator.py matthew")
        sys.exit(1)

    username = sys.argv[1]
    preview_monikers(username)

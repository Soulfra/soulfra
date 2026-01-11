#!/usr/bin/env python3
"""
Seed Mesh Network Domains

Populates the 8 domains with tier levels and initial keywords.

Run after init_mesh_economy.py:
    python3 seed_domains.py
"""

import sqlite3
import json
from datetime import datetime


DOMAINS = [
    {
        'domain': 'cringeproof.com',
        'tier': 'legendary',
        'description': 'Authentic validation in social media. No cringe, just genuine connection.',
        'keywords': [
            'authentic', 'social', 'media', 'validation', 'genuine', 'connection',
            'cringe', 'real', 'honest', 'vulnerable', 'trust', 'community',
            'acceptance', 'belonging', 'expression', 'identity', 'self', 'truth'
        ]
    },
    {
        'domain': 'soulfra.com',
        'tier': 'legendary',
        'description': 'Soul infrastructure. Building systems for human flourishing.',
        'keywords': [
            'soul', 'infrastructure', 'human', 'flourishing', 'systems', 'build',
            'meaning', 'purpose', 'connection', 'growth', 'development', 'potential',
            'framework', 'foundation', 'structure', 'support', 'community', 'culture'
        ]
    },
    {
        'domain': 'deathtodata.com',
        'tier': 'epic',
        'description': 'Resist surveillance capitalism. Own your digital identity.',
        'keywords': [
            'privacy', 'data', 'surveillance', 'capitalism', 'resist', 'own',
            'digital', 'identity', 'freedom', 'control', 'security', 'encryption',
            'decentralized', 'sovereignty', 'autonomy', 'rights', 'protection', 'power'
        ]
    },
    {
        'domain': 'theworldisntreal.com',
        'tier': 'epic',
        'description': 'Question consensus reality. Explore alternative perspectives.',
        'keywords': [
            'reality', 'perception', 'truth', 'question', 'explore', 'alternative',
            'consciousness', 'awareness', 'perspective', 'simulation', 'matrix', 'awake',
            'paradigm', 'belief', 'illusion', 'understanding', 'knowledge', 'wisdom'
        ]
    },
    {
        'domain': 'seattlesucks.com',
        'tier': 'rare',
        'description': 'Honest takes on Seattle living. The rain, the tech, the truth.',
        'keywords': [
            'seattle', 'pacific', 'northwest', 'rain', 'tech', 'city',
            'honest', 'real', 'authentic', 'local', 'community', 'culture',
            'amazon', 'microsoft', 'coffee', 'grunge', 'nature', 'mountains'
        ]
    },
    {
        'domain': 'stpetepros.com',
        'tier': 'rare',
        'description': 'St. Petersburg FL professionals. Sunshine state networking.',
        'keywords': [
            'stpete', 'tampa', 'florida', 'professional', 'network', 'business',
            'sunshine', 'beach', 'community', 'local', 'growth', 'opportunity',
            'entrepreneur', 'startup', 'innovation', 'collaboration', 'success', 'hustle'
        ]
    },
    {
        'domain': 'mattisinspace.com',
        'tier': 'common',
        'description': 'Matt\'s personal universe. Projects, thoughts, experiments.',
        'keywords': [
            'matt', 'personal', 'project', 'experiment', 'thought', 'idea',
            'build', 'create', 'share', 'learn', 'grow', 'explore',
            'code', 'design', 'writing', 'content', 'creative', 'expression'
        ]
    },
    {
        'domain': 'aiclouds.com',
        'tier': 'common',
        'description': 'AI infrastructure and cloud computing. The future of intelligence.',
        'keywords': [
            'ai', 'artificial', 'intelligence', 'cloud', 'computing', 'future',
            'machine', 'learning', 'neural', 'network', 'model', 'train',
            'infrastructure', 'scale', 'distributed', 'gpu', 'compute', 'power'
        ]
    }
]


def seed_domains():
    """Seed all 8 domains into database"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("🌱 Seeding mesh network domains...\n")

    for domain_data in DOMAINS:
        domain = domain_data['domain']
        tier = domain_data['tier']
        description = domain_data['description']
        keywords_json = json.dumps(domain_data['keywords'])

        # Get domain slug (e.g., "cringeproof" from "cringeproof.com")
        domain_slug = domain.split('.')[0]

        # Insert or update domain
        cursor.execute('''
            INSERT OR REPLACE INTO domain_contexts
            (domain, domain_slug, context_type, content, tier, description, initial_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (domain, domain_slug, 'mesh_network', '', tier, description, keywords_json))

        # Create initial domain wordmap from keywords
        wordmap = {word: 10 for word in domain_data['keywords']}  # Give each word a count of 10
        wordmap_json = json.dumps(wordmap)

        cursor.execute('''
            INSERT OR REPLACE INTO domain_wordmaps
            (domain, wordmap_json, contributor_count, total_recordings, last_updated)
            VALUES (?, ?, 0, 0, ?)
        ''', (domain, wordmap_json, datetime.now().isoformat()))

        # Visual feedback
        emoji = {
            'legendary': '👑',
            'epic': '💎',
            'rare': '🌟',
            'common': '⚪'
        }.get(tier, '🔵')

        print(f"{emoji} {tier.upper():10} | {domain:25} | {len(domain_data['keywords'])} keywords")

    conn.commit()
    conn.close()

    print(f"\n✅ Successfully seeded {len(DOMAINS)} domains!")
    print("\n📊 Domain Distribution:")
    print("   👑 Legendary: 2 domains")
    print("   💎 Epic: 2 domains")
    print("   🌟 Rare: 2 domains")
    print("   ⚪ Common: 2 domains")

    print("\nNext steps:")
    print("  1. Run: python3 test_mesh_flow.py")
    print("  2. Visit: http://localhost:5001/domains")
    print("  3. Visit: http://localhost:5001/cringeproof")


if __name__ == '__main__':
    seed_domains()

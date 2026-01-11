#!/usr/bin/env python3
"""
Import remaining 9 brands from brand-profiles.js into database.

Already imported:
- Soulfra (ID 1)
- Calriven (ID 2) - Note: JS has ID 2 but we may have it as different ID
- DeathToData (ID 3)

Need to import:
- FinishThisIdea (ID 4)
- FinishThisRepo (ID 5)
- IPOMyAgent (ID 6)
- HollowTown (ID 7)
- ColdStartKit (ID 8)
- BrandAidKit (ID 9)
- DealOrDelete (ID 10)
- SaveOrSink (ID 11)
- CringeProof (ID 12)
"""

import sqlite3
import json


# Brand data from brand-profiles.js
BRANDS_TO_IMPORT = [
    {
        'name': 'FinishThisIdea',
        'slug': 'finishthisidea',
        'tagline': "47 unfinished projects? Let's fix that.",
        'category': 'Completion',
        'tier': 'business',
        'color_primary': '#4CAF50',
        'color_secondary': '#45a049',
        'color_accent': '#FFC107',
        'personality_tone': 'Motivating, supportive',
        'personality_traits': json.dumps(['encouraging', 'practical', 'action-oriented']),
        'ai_style': 'motivational coach, helps you finish what you started'
    },
    {
        'name': 'FinishThisRepo',
        'slug': 'finishthisrepo',
        'tagline': "Code's not done? We'll finish it.",
        'category': 'Code Completion',
        'tier': 'business',
        'color_primary': '#24292e',
        'color_secondary': '#0366d6',
        'color_accent': '#28a745',
        'personality_tone': 'Pragmatic, direct',
        'personality_traits': json.dumps(['code-focused', 'no-nonsense', 'ship-it']),
        'ai_style': 'direct, practical, focused on shipping code'
    },
    {
        'name': 'IPOMyAgent',
        'slug': 'ipomyagent',
        'tagline': "Your agent's an asset. Trade it like one.",
        'category': 'AI Market',
        'tier': 'business',
        'color_primary': '#9C27B0',
        'color_secondary': '#7B1FA2',
        'color_accent': '#E91E63',
        'personality_tone': 'Ambitious, market-savvy',
        'personality_traits': json.dumps(['entrepreneurial', 'visionary', 'market-minded']),
        'ai_style': 'business-focused, talks about value and markets'
    },
    {
        'name': 'HollowTown',
        'slug': 'hollowtown',
        'tagline': '8-bit > photorealism. Fight me.',
        'category': 'Virtual World',
        'tier': 'creative',
        'color_primary': '#8B4513',
        'color_secondary': '#A0522D',
        'color_accent': '#FFD700',
        'personality_tone': 'Nostalgic, playful',
        'personality_traits': json.dumps(['retro-loving', 'creative', 'whimsical']),
        'ai_style': 'playful, nostalgic for 80s/90s gaming'
    },
    {
        'name': 'ColdStartKit',
        'slug': 'coldstartkit',
        'tagline': 'Ship in hours, not months.',
        'category': 'Templates',
        'tier': 'creative',
        'color_primary': '#00BCD4',
        'color_secondary': '#0097A7',
        'color_accent': '#FF5722',
        'personality_tone': 'Practical, fast',
        'personality_traits': json.dumps(['efficient', 'starter-friendly', 'quick']),
        'ai_style': 'fast-paced, practical, gets you started quickly'
    },
    {
        'name': 'BrandAidKit',
        'slug': 'brandaidkit',
        'tagline': 'Design agency prices? Nah.',
        'category': 'Design',
        'tier': 'creative',
        'color_primary': '#FF6B6B',
        'color_secondary': '#4ECDC4',
        'color_accent': '#FFE66D',
        'personality_tone': 'Creative, accessible',
        'personality_traits': json.dumps(['design-focused', 'affordable', 'creative']),
        'ai_style': 'creative, design-minded, makes design accessible'
    },
    {
        'name': 'DealOrDelete',
        'slug': 'dealordelete',
        'tagline': 'Ship or kill. No limbo.',
        'category': 'Decisions',
        'tier': 'additional',
        'color_primary': '#FF9800',
        'color_secondary': '#F57C00',
        'color_accent': '#FFC107',
        'personality_tone': 'Decisive, clear',
        'personality_traits': json.dumps(['decisive', 'binary-thinking', 'action-focused']),
        'ai_style': 'forces decisions, no middle ground'
    },
    {
        'name': 'SaveOrSink',
        'slug': 'saveorsink',
        'tagline': '3am outage? We got you.',
        'category': 'Rescue',
        'tier': 'additional',
        'color_primary': '#2196F3',
        'color_secondary': '#1976D2',
        'color_accent': '#FFC107',
        'personality_tone': 'Calm, capable',
        'personality_traits': json.dumps(['reliable', 'emergency-ready', 'calm-under-pressure']),
        'ai_style': 'calm, reassuring, solves emergencies'
    },
    {
        'name': 'CringeProof',
        'slug': 'cringeproof',
        'tagline': "Don't post that. Seriously.",
        'category': 'Content Review',
        'tier': 'additional',
        'color_primary': '#E91E63',
        'color_secondary': '#C2185B',
        'color_accent': '#FF4081',
        'personality_tone': 'Protective, honest',
        'personality_traits': json.dumps(['brutally-honest', 'protective', 'critical']),
        'ai_style': 'brutally honest, saves you from embarrassment'
    }
]


def import_brands():
    """Import remaining brands into database."""
    db = sqlite3.connect('soulfra.db')
    cursor = db.cursor()

    print("🏷️  Brand Importer\n")

    # Check existing brands
    cursor.execute("SELECT name FROM brands ORDER BY id")
    existing_brands = [row[0] for row in cursor.fetchall()]
    print(f"📊 Currently in database: {len(existing_brands)} brands")
    for brand in existing_brands:
        print(f"   ✅ {brand}")
    print()

    imported = 0
    skipped = 0

    for brand_data in BRANDS_TO_IMPORT:
        brand_name = brand_data['name']

        # Check if brand already exists
        cursor.execute("SELECT id FROM brands WHERE name = ?", (brand_name,))
        if cursor.fetchone():
            print(f"⏭️  {brand_name}: Already exists")
            skipped += 1
            continue

        # Insert brand
        cursor.execute("""
            INSERT INTO brands (
                name, slug, tagline, category, tier,
                color_primary, color_secondary, color_accent,
                personality_tone, personality_traits, ai_style
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            brand_data['name'],
            brand_data['slug'],
            brand_data['tagline'],
            brand_data['category'],
            brand_data['tier'],
            brand_data['color_primary'],
            brand_data['color_secondary'],
            brand_data['color_accent'],
            brand_data['personality_tone'],
            brand_data['personality_traits'],
            brand_data['ai_style']
        ))

        brand_id = cursor.lastrowid
        print(f"✅ {brand_name} (ID {brand_id})")
        print(f"   Tagline: {brand_data['tagline']}")
        print(f"   Category: {brand_data['category']} ({brand_data['tier']} tier)")
        print()

        imported += 1

    db.commit()
    db.close()

    print(f"📊 Summary:")
    print(f"   Imported: {imported} brands")
    print(f"   Skipped (already exist): {skipped} brands")
    print(f"   Total in database: {len(existing_brands) + imported} brands")


if __name__ == '__main__':
    import_brands()

#!/usr/bin/env python3
"""
Seed Brands - Create brands that match neural network classifiers

Creates three competing brands:
1. CalRiven (Technical) - 💻 Code, APIs, Architecture
2. Privacy Guard (Privacy) - 🔒 Data Protection, Security
3. The Auditor (Validation) - ✅ Testing, Quality, Validation

Each brand maps to a neural network classifier, creating the competitive ecosystem.
"""

import sqlite3

def seed_brands():
    """Create the three core brands"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    brands = [
        {
            'name': 'CalRiven',
            'slug': 'calriven',
            'description': 'Master of code, APIs, and technical architecture. CalRiven thrives on clean implementations, elegant algorithms, and scalable systems.',
            'color': '#2196F3',
            'emoji': '💻'
        },
        {
            'name': 'Privacy Guard',
            'slug': 'privacy-guard',
            'description': 'Protector of personal data and digital rights. Privacy Guard champions encryption, security, and user privacy in the digital age.',
            'color': '#f44336',
            'emoji': '🔒'
        },
        {
            'name': 'The Auditor',
            'slug': 'the-auditor',
            'description': 'Quality enforcer and validation expert. The Auditor ensures everything is tested, verified, and production-ready.',
            'color': '#4CAF50',
            'emoji': '✅'
        }
    ]

    print("=" * 70)
    print("🌱 SEEDING BRANDS")
    print("=" * 70)
    print()

    for brand in brands:
        # Check if brand exists
        cursor.execute('SELECT id FROM brands WHERE slug = ?', (brand['slug'],))
        existing = cursor.fetchone()

        if existing:
            print(f"⏭️  {brand['name']} already exists (ID: {existing[0]})")
            brand_id = existing[0]
        else:
            # Insert brand
            cursor.execute('''
                INSERT INTO brands (name, slug, personality, tone)
                VALUES (?, ?, ?, ?)
            ''', (brand['name'], brand['slug'], brand['description'], 'professional'))

            brand_id = cursor.lastrowid
            print(f"✅ Created {brand['name']} (ID: {brand_id})")

        # Initialize territory
        cursor.execute('''
            INSERT OR IGNORE INTO brand_territory (brand_id, territory_score, rank)
            VALUES (?, 0.0, 0)
        ''', (brand_id,))

    conn.commit()
    conn.close()

    print()
    print("=" * 70)
    print("🎉 BRANDS SEEDED!")
    print("=" * 70)
    print()
    print("Competitive Ecosystem Ready:")
    print("  💻 CalRiven - Technical content")
    print("  🔒 Privacy Guard - Privacy & security")
    print("  ✅ The Auditor - Testing & validation")
    print()
    print("Users can now:")
    print("  → Contribute to their preferred brand")
    print("  → Earn soul tokens for on-brand contributions")
    print("  → Help brands compete for territory")
    print()


if __name__ == '__main__':
    seed_brands()

#!/usr/bin/env python3
"""
Create Diverse User Personas

Adds varied users with different backgrounds to showcase platform diversity.
Not just AI personas - real human-like users with different interests.
"""

from db_helpers import create_user
from database import get_db


PERSONAS = [
    {
        'username': 'philosopher_king',
        'email': 'philosophy@soulfra.local',
        'password': 'soulfra2025',
        'display_name': 'PhilosopherKing',
        'bio': 'Exploring ideas at the intersection of technology, ethics, and human nature. Questions everything.',
        'is_ai_persona': False
    },
    {
        'username': 'data_skeptic',
        'email': 'skeptic@soulfra.local',
        'password': 'soulfra2025',
        'display_name': 'DataSkeptic',
        'bio': 'Journalist covering surveillance capitalism, privacy rights, and digital freedom. Deeply suspicious of data collection.',
        'is_ai_persona': False
    },
    {
        'username': 'science_explorer',
        'email': 'science@soulfra.local',
        'password': 'soulfra2025',
        'display_name': 'ScienceExplorer',
        'bio': 'Research scientist fascinated by reproducibility, open science, and transparent research methods.',
        'is_ai_persona': False
    },
    {
        'username': 'culture_critic',
        'email': 'culture@soulfra.local',
        'password': 'soulfra2025',
        'display_name': 'CultureCritic',
        'bio': 'Writer examining how open source principles apply to art, culture, and creative communities.',
        'is_ai_persona': False
    },
    {
        'username': 'freedom_builder',
        'email': 'freedom@soulfra.local',
        'password': 'soulfra2025',
        'display_name': 'FreedomBuilder',
        'bio': 'Activist building tools for decentralized communities. Believes code is speech and software is politics.',
        'is_ai_persona': False
    },
]


def create_personas():
    """Create all personas"""
    print("=" * 70)
    print("👥 Creating Diverse User Personas")
    print("=" * 70)
    print()

    created = 0
    skipped = 0

    for persona in PERSONAS:
        user = create_user(
            username=persona['username'],
            email=persona['email'],
            password=persona['password'],
            display_name=persona['display_name'],
            is_ai_persona=persona.get('is_ai_persona', False)
        )

        if user:
            print(f"✅ Created: {persona['display_name']} (@{persona['username']})")
            print(f"   {persona['bio'][:80]}...")
            print()
            created += 1

            # Update bio
            db = get_db()
            db.execute('UPDATE users SET bio = ? WHERE username = ?',
                      (persona['bio'], persona['username']))
            db.commit()
            db.close()
        else:
            print(f"⏭️  Skipped: {persona['username']} (already exists)")
            skipped += 1

    print()
    print(f"📊 Created {created} new personas, skipped {skipped} existing")
    print(f"✅ Total users now: {created + skipped + 6}")  # +6 for existing users


if __name__ == '__main__':
    create_personas()

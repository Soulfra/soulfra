#!/usr/bin/env python3
"""
Brand AI Persona Generator - Auto-create AI character for every brand!

Creates an AI user account for each brand that:
1. Comments in the brand's voice (personality + tone)
2. Acts as "sounding board" for new creators
3. Provides instant engagement
4. Creates network effect through AI cross-engagement

This solves the cold start problem: New creator has 0 users → Brand AI gives
instant feedback → Feels engaged → Keeps creating!

Usage:
    python3 brand_ai_persona_generator.py generate ocean-dreams
    python3 brand_ai_persona_generator.py generate-all
    python3 brand_ai_persona_generator.py list
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional
from database import get_db
from db_helpers import create_user


def generate_system_prompt(brand_config: Dict) -> str:
    """
    Generate Ollama system prompt from brand config

    Converts personality, tone, and values into AI instructions.

    Example:
        Brand: Ocean Dreams
        Personality: "calm, deep, flowing"
        Tone: "peaceful and contemplative"
        →
        System Prompt: "You are Ocean Dreams, a calm and contemplative voice..."
    """
    name = brand_config.get('name', 'Unknown Brand')
    personality = brand_config.get('personality', 'thoughtful')
    tone = brand_config.get('tone', 'friendly')
    values = brand_config.get('values', [])

    # Build personality description
    personality_desc = f"You embody these traits: {personality}"

    # Build tone description
    tone_desc = f"Your communication style is {tone}"

    # Build values description
    values_desc = ""
    if values:
        if isinstance(values, list):
            values_str = ", ".join(values)
        else:
            values_str = str(values)
        values_desc = f"You value: {values_str}"

    prompt = f"""You are {name}, an AI persona representing the {name} brand.

{personality_desc}

{tone_desc}

{values_desc if values_desc else ''}

When commenting on posts:
- Stay true to your personality and tone
- Provide constructive feedback
- Ask thoughtful questions
- Share insights from your unique perspective
- Keep responses concise (2-3 paragraphs)
- Be supportive and encouraging
- Add value to the conversation

Remember: You're not just commenting, you're helping creators feel heard and engaged.
Be the kind of presence that makes them want to keep creating!
"""

    return prompt.strip()


def get_brand_emoji(brand_config: Dict) -> str:
    """Extract or guess brand emoji from config"""
    # Try explicit emoji field
    if 'emoji' in brand_config:
        return brand_config['emoji']

    # Try to guess from name/personality
    name_lower = brand_config.get('name', '').lower()
    personality_lower = brand_config.get('personality', '').lower()

    if 'ocean' in name_lower or 'water' in personality_lower:
        return '🌊'
    elif 'tech' in name_lower or 'code' in personality_lower:
        return '💻'
    elif 'privacy' in name_lower or 'data' in personality_lower:
        return '🔒'
    elif 'audit' in name_lower or 'test' in personality_lower:
        return '🔍'
    elif 'art' in name_lower or 'creative' in personality_lower:
        return '🎨'
    elif 'science' in name_lower:
        return '🔬'
    elif 'build' in personality_lower:
        return '🛠️'
    else:
        return '✨'  # Default


def generate_brand_ai_persona(brand_slug: str, tier: str = 'free') -> Optional[Dict]:
    """
    Generate AI persona for a brand

    Args:
        brand_slug: Brand slug (e.g., 'ocean-dreams')
        tier: Engagement tier ('free', 'pro', 'enterprise')

    Returns:
        Dict with persona config, or None if brand not found

    Creates:
        - User account in database (username = brand slug)
        - System prompt from brand personality/tone
        - AI persona config for Ollama
    """
    db = get_db()

    # Get brand
    brand_row = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    if not brand_row:
        print(f"❌ Brand '{brand_slug}' not found")
        db.close()
        return None

    brand = dict(brand_row)

    # Parse config
    try:
        brand_config = json.loads(brand['config_json']) if brand['config_json'] else {}
    except (json.JSONDecodeError, TypeError):
        brand_config = {}

    # Add brand metadata
    brand_config['name'] = brand['name']
    brand_config['personality'] = brand.get('personality', 'thoughtful')
    brand_config['tone'] = brand.get('tone', 'friendly')

    # Generate system prompt
    system_prompt = generate_system_prompt(brand_config)

    # Get or create AI user
    username = brand_slug
    email = f"{brand_slug}@soulfra.ai"
    display_name = f"{brand['name']}"

    # Check if user exists
    existing_user = db.execute('''
        SELECT id FROM users WHERE username = ?
    ''', (username,)).fetchone()

    if existing_user:
        user_id = existing_user['id']
        print(f"ℹ️  AI persona already exists: {display_name} (@{username})")
    else:
        # Create AI persona user
        db.execute('''
            INSERT INTO users (username, email, password_hash, display_name,
                              bio, is_admin, is_ai_persona, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            email,
            'NOLOGIN',  # AI personas don't need password
            display_name,
            f"AI persona for {brand['name']} brand. {brand_config.get('personality', '')}",
            0,  # Not admin
            1,  # Is AI persona
            datetime.now().isoformat()
        ))
        user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()
        print(f"✅ Created AI persona: {display_name} (@{username})")

    db.close()

    # Get emoji
    emoji = get_brand_emoji(brand_config)

    # Build persona config
    persona = {
        'user_id': user_id,
        'username': username,
        'display_name': display_name,
        'email': email,
        'brand_id': brand['id'],
        'brand_slug': brand_slug,
        'brand_name': brand['name'],
        'system_prompt': system_prompt,
        'personality': brand_config.get('personality', 'thoughtful'),
        'tone': brand_config.get('tone', 'friendly'),
        'emoji': emoji,
        'tier': tier,
        'is_ai_persona': True
    }

    return persona


def generate_all_brand_ai_personas(tier: str = 'free') -> int:
    """
    Generate AI personas for all brands

    Args:
        tier: Default engagement tier

    Returns:
        Number of personas created
    """
    db = get_db()
    brands = db.execute('''
        SELECT slug, name FROM brands ORDER BY name
    ''').fetchall()
    db.close()

    print("=" * 70)
    print("🤖 GENERATING BRAND AI PERSONAS")
    print("=" * 70)
    print()
    print(f"Found {len(brands)} brands")
    print()

    created = 0
    for brand in brands:
        slug = brand['slug']
        persona = generate_brand_ai_persona(slug, tier=tier)
        if persona:
            print(f"   {persona['emoji']} {persona['display_name']}")
            created += 1

    print()
    print(f"✅ Generated {created} AI personas")
    print()

    return created


def list_brand_ai_personas():
    """List all brand AI personas"""
    db = get_db()

    personas = db.execute('''
        SELECT
            u.username,
            u.display_name,
            u.bio,
            b.name as brand_name,
            b.slug as brand_slug
        FROM users u
        LEFT JOIN brands b ON u.username = b.slug
        WHERE u.is_ai_persona = 1
        ORDER BY u.created_at DESC
    ''').fetchall()

    db.close()

    print("=" * 70)
    print("🤖 BRAND AI PERSONAS")
    print("=" * 70)
    print()

    if not personas:
        print("No AI personas found.")
        return

    for persona in personas:
        print(f"@{persona['username']:<20} {persona['display_name']}")
        if persona['brand_name']:
            print(f"  Brand: {persona['brand_name']} ({persona['brand_slug']})")
        if persona['bio']:
            print(f"  Bio: {persona['bio'][:80]}")
        print()

    print(f"Total: {len(personas)} AI personas")
    print()


def get_brand_ai_persona_config(brand_slug: str) -> Optional[Dict]:
    """
    Get AI persona config for a brand (for use by ollama_auto_commenter)

    Args:
        brand_slug: Brand slug

    Returns:
        Persona config dict or None
    """
    db = get_db()

    # Get user and brand
    result = db.execute('''
        SELECT
            u.id as user_id,
            u.username,
            u.display_name,
            u.email,
            b.id as brand_id,
            b.slug as brand_slug,
            b.name as brand_name,
            b.personality,
            b.tone,
            b.config_json
        FROM users u
        JOIN brands b ON u.username = b.slug
        WHERE u.username = ? AND u.is_ai_persona = 1
    ''', (brand_slug,)).fetchone()

    db.close()

    if not result:
        return None

    result_dict = dict(result)

    # Parse config
    try:
        brand_config = json.loads(result_dict['config_json']) if result_dict['config_json'] else {}
    except (json.JSONDecodeError, TypeError):
        brand_config = {}

    brand_config['name'] = result_dict['brand_name']
    brand_config['personality'] = result_dict['personality']
    brand_config['tone'] = result_dict['tone']

    # Generate system prompt
    system_prompt = generate_system_prompt(brand_config)
    emoji = get_brand_emoji(brand_config)

    return {
        'user_id': result_dict['user_id'],
        'username': result_dict['username'],
        'display_name': result_dict['display_name'],
        'email': result_dict['email'],
        'brand_id': result_dict['brand_id'],
        'brand_slug': result_dict['brand_slug'],
        'brand_name': result_dict['brand_name'],
        'system_prompt': system_prompt,
        'personality': result_dict['personality'],
        'tone': result_dict['tone'],
        'emoji': emoji,
        'is_ai_persona': True
    }


def main():
    """CLI for brand AI persona generation"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 brand_ai_persona_generator.py generate <brand_slug>")
        print("  python3 brand_ai_persona_generator.py generate-all")
        print("  python3 brand_ai_persona_generator.py list")
        print()
        print("Examples:")
        print("  python3 brand_ai_persona_generator.py generate ocean-dreams")
        print("  python3 brand_ai_persona_generator.py generate-all")
        print("  python3 brand_ai_persona_generator.py list")
        return

    command = sys.argv[1]

    if command == 'generate':
        if len(sys.argv) < 3:
            print("Error: Missing brand slug")
            return

        brand_slug = sys.argv[2]
        tier = sys.argv[3] if len(sys.argv) > 3 else 'free'

        print("=" * 70)
        print(f"🤖 GENERATING AI PERSONA FOR: {brand_slug}")
        print("=" * 70)
        print()

        persona = generate_brand_ai_persona(brand_slug, tier=tier)

        if persona:
            print()
            print("✅ Persona Config:")
            print(f"   Username: @{persona['username']}")
            print(f"   Display Name: {persona['display_name']}")
            print(f"   Emoji: {persona['emoji']}")
            print(f"   Personality: {persona['personality']}")
            print(f"   Tone: {persona['tone']}")
            print(f"   Tier: {persona['tier']}")
            print()
            print("System Prompt:")
            print("-" * 70)
            print(persona['system_prompt'])
            print("-" * 70)
            print()

    elif command == 'generate-all':
        tier = sys.argv[2] if len(sys.argv) > 2 else 'free'
        generate_all_brand_ai_personas(tier=tier)

    elif command == 'list':
        list_brand_ai_personas()

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

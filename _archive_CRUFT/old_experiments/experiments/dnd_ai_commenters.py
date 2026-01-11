#!/usr/bin/env python3
"""
D&D AI Commenters - Brand AIs Comment on Quest Progress

This bridges D&D gameplay with the brand AI network:
- When player starts a quest → AIs react based on personality
- When player takes action → AIs debate the strategy
- When quest completes → AIs celebrate/analyze results

Uses neural networks to determine which AIs should comment!
"""

import sqlite3
from typing import List, Dict, Optional
import json


def get_brand_ai_personas() -> List[Dict]:
    """Get all brand AI personas that can comment"""

    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, display_name, bio, is_ai_persona
        FROM users
        WHERE is_ai_persona = 1
    ''')

    personas = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return personas


def should_ai_comment(ai_persona: Dict, event_type: str, event_data: Dict) -> bool:
    """
    Use neural networks to decide if AI should comment

    Args:
        ai_persona: AI persona info
        event_type: 'quest_start', 'action_taken', 'quest_complete'
        event_data: Quest/action details

    Returns:
        True if AI should comment
    """

    # Load neural network for this AI's personality
    try:
        from brand_voice_generator import load_neural_network

        # Get AI's network based on username
        network_map = {
            'calriven': 'calriven_technical_classifier',
            'theauditor': 'theauditor_validation_classifier',
            'deathtodata': 'deathtodata_privacy_classifier',
            'soulfra': 'soulfra_judge'
        }

        network_name = network_map.get(ai_persona['username'].lower())
        if not network_name:
            # Default: 50% chance for non-core AIs
            import random
            return random.random() > 0.5

        network = load_neural_network(network_name)
        if not network:
            return False

        # Extract features based on event type
        if event_type == 'quest_start':
            # Technical AIs like new quests, validation AIs like proof
            features = _extract_quest_features(event_data)
        elif event_type == 'action_taken':
            # Analyze the action text
            features = _extract_action_features(event_data)
        else:  # quest_complete
            # All AIs like celebrations!
            return True

        # Predict if this AI cares about this event
        import numpy as np
        prediction = network.predict(np.array([features]))[0][0]

        # Comment if prediction > 0.5
        return prediction > 0.5

    except Exception as e:
        print(f"Neural network decision failed: {e}")
        # Fallback: random chance
        import random
        return random.random() > 0.5


def _extract_quest_features(quest_data: Dict) -> List[float]:
    """Extract features from quest for neural network"""

    # Simple features: difficulty level, reward count, aging amount
    difficulty_map = {'easy': 0.25, 'medium': 0.5, 'hard': 0.75, 'legendary': 1.0}

    features = [
        difficulty_map.get(quest_data.get('difficulty', 'medium'), 0.5),
        min(len(quest_data.get('rewards', {}).get('items', [])) / 10.0, 1.0),
        min(quest_data.get('aging_years', 0) / 20.0, 1.0),
        1.0 if 'dragon' in quest_data.get('name', '').lower() else 0.0
    ]

    return features


def _extract_action_features(action_data: Dict) -> List[float]:
    """Extract features from action for neural network"""

    action_text = action_data.get('action_text', '').lower()

    features = [
        1.0 if 'attack' in action_text else 0.0,
        1.0 if 'spell' in action_text or 'magic' in action_text else 0.0,
        1.0 if 'heal' in action_text or 'potion' in action_text else 0.0,
        min(len(action_text) / 100.0, 1.0)  # Action complexity
    ]

    return features


def generate_ai_comment(ai_persona: Dict, event_type: str, event_data: Dict) -> str:
    """
    Generate comment from AI persona using Ollama

    Args:
        ai_persona: AI persona info
        event_type: Type of event
        event_data: Event details

    Returns:
        Generated comment text
    """

    try:
        import urllib.request
        import json as json_lib

        # Build prompt based on AI personality
        persona_prompts = {
            'calriven': "You are CalRiven, a technical AI who analyzes strategy and tactics. Comment on this D&D event from a technical perspective.",
            'theauditor': "You are The Auditor, who validates and verifies results. Comment on this D&D event focusing on proof and validation.",
            'deathtodata': "You are DeathToData, who values privacy and self-reliance. Comment on this D&D event from a decentralized perspective.",
            'soulfra': "You are Soulfra, a meta-judge who weighs all perspectives. Comment on this D&D event with balanced wisdom."
        }

        system_prompt = persona_prompts.get(
            ai_persona['username'].lower(),
            f"You are {ai_persona['display_name']}, an AI persona. Comment on this D&D event."
        )

        # Format event for AI
        if event_type == 'quest_start':
            event_desc = f"Player started quest: {event_data.get('quest_name')} ({event_data.get('difficulty')})"
        elif event_type == 'action_taken':
            event_desc = f"Player action: {event_data.get('action_text')} - Result: {event_data.get('verdict')}"
        else:
            event_desc = f"Player completed quest! Character aged {event_data.get('years_aged')} years, earned {len(event_data.get('items_earned', []))} items"

        prompt = f"{system_prompt}\n\n{event_desc}\n\nProvide a brief, in-character comment (2-3 sentences max):"

        # Call Ollama
        request_data = {
            'model': 'llama2',
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.8,
                'num_predict': 100
            }
        }

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=json_lib.dumps(request_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        response = urllib.request.urlopen(req, timeout=30)
        result = json_lib.loads(response.read().decode('utf-8'))
        comment = result.get('response', '').strip()

        return comment

    except Exception as e:
        print(f"Failed to generate AI comment: {e}")
        return f"*{ai_persona['display_name']} nods approvingly*"


def notify_ai_commenters(event_type: str, event_data: Dict, max_comments: int = 3):
    """
    Notify brand AI personas about D&D event and generate comments

    Args:
        event_type: 'quest_start', 'action_taken', 'quest_complete'
        event_data: Event details (quest info, action, completion results)
        max_comments: Maximum number of AI comments to generate
    """

    print(f"\n🤖 Notifying brand AIs about {event_type}...")

    # Get all AI personas
    personas = get_brand_ai_personas()

    # Determine which AIs should comment (using neural networks!)
    commenting_ais = []
    for persona in personas:
        if should_ai_comment(persona, event_type, event_data):
            commenting_ais.append(persona)
            if len(commenting_ais) >= max_comments:
                break

    print(f"   {len(commenting_ais)}/{len(personas)} AIs decided to comment")

    # Generate and save comments
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    for ai in commenting_ais:
        comment_text = generate_ai_comment(ai, event_type, event_data)

        # Save comment to a "D&D events" post (create if doesn't exist)
        post_id = _get_or_create_dnd_events_post()

        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (post_id, ai['id'], f"**[{event_type.upper()}]** {comment_text}"))

        print(f"   ✅ {ai['display_name']}: {comment_text[:50]}...")

    conn.commit()
    conn.close()


def _get_or_create_dnd_events_post() -> int:
    """Get or create the D&D events feed post where AIs comment"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if exists
    cursor.execute('''
        SELECT id FROM posts WHERE slug = 'dnd-events-feed'
    ''')

    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]

    # Create it
    cursor.execute('''
        INSERT INTO posts (title, slug, content, excerpt, author_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        '🐉 D&D Events Feed',
        'dnd-events-feed',
        '# D&D Events Feed\n\nWatch brand AIs comment on D&D quest progress in real-time!',
        'Live feed of brand AI reactions to D&D quest events',
        1,  # System post
        'published'
    ))

    post_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return post_id


if __name__ == '__main__':
    """Test AI commenting system"""

    print("=" * 70)
    print("🤖 D&D AI Commenters Test")
    print("=" * 70)

    # Test quest start event
    test_event = {
        'quest_name': 'Dragon\'s Lair',
        'difficulty': 'legendary',
        'aging_years': 10,
        'rewards': {'items': ['Dragon Scale', 'Ancient Sword']}
    }

    print("\nSimulating: Player starts 'Dragon's Lair' quest")
    notify_ai_commenters('quest_start', test_event, max_comments=3)

    print("\n" + "=" * 70)
    print("✅ Test complete! Check http://localhost:5001/post/dnd-events-feed")

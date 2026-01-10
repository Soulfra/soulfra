#!/usr/bin/env python3
"""
Profile Builder - Analyze Quiz Answers → Build Personality → Assign AI Friend

Analyzes user answers from narrative games to:
- Build personality profile
- Match to best AI persona ("first friend" like MySpace Tom)
- Calculate compatibility scores
- Generate traits and insights

Usage:
    from profile_builder import build_profile_from_quiz

    profile = build_profile_from_quiz(session_id=123, user_id=456)
    # Returns: {
    #     'matched_ai': 'soulfra',
    #     'ai_friend_id': 8,
    #     'scores': {...},
    #     'traits': [...]
    # }
"""

import json
from typing import Dict, Any, List, Tuple
from database import get_db


# AI Persona Scoring System
# Each persona has different question preferences
AI_PERSONAS = {
    'soulfra': {
        'name': 'Soulfra',
        'description': 'Dark mysteries, forbidden knowledge, philosophical depth',
        'keywords': ['mystery', 'philosophy', 'dark', 'forbidden', 'truth', 'hidden', 'secret', 'deep'],
        'question_weights': {
            # Questions with philosophical/mystery themes score higher
            'mystery_questions': 2.0,
            'philosophy_questions': 2.0,
            'introspection_questions': 1.5
        }
    },
    'calriven': {
        'name': 'CalRiven',
        'description': 'Architecture, design, technical depth, building systems',
        'keywords': ['build', 'design', 'architecture', 'technical', 'system', 'structure', 'create', 'craft'],
        'question_weights': {
            'technical_questions': 2.0,
            'design_questions': 2.0,
            'analytical_questions': 1.5
        }
    },
    'deathtodata': {
        'name': 'DeathToData',
        'description': 'Privacy, encryption, digital freedom, protecting data',
        'keywords': ['privacy', 'encrypt', 'freedom', 'protect', 'secure', 'anonymous', 'rights', 'data'],
        'question_weights': {
            'privacy_questions': 2.0,
            'freedom_questions': 2.0,
            'security_questions': 1.5
        }
    },
    'theauditor': {
        'name': 'TheAuditor',
        'description': 'Validation, proof, evidence, analytical thinking',
        'keywords': ['proof', 'evidence', 'validate', 'test', 'verify', 'analyze', 'logic', 'reason'],
        'question_weights': {
            'analytical_questions': 2.0,
            'validation_questions': 2.0,
            'logic_questions': 1.5
        }
    }
}


def get_ai_persona_id(persona_slug: str) -> int:
    """
    Get user ID for AI persona (they're stored as users with is_ai_persona=1)

    Args:
        persona_slug: Slug of persona (e.g., 'soulfra')

    Returns:
        User ID of AI persona
    """
    db = get_db()

    # Get AI persona user
    persona = db.execute('''
        SELECT id FROM users
        WHERE username = ? AND is_ai_persona = 1
    ''', (persona_slug,)).fetchone()

    db.close()

    if persona:
        return persona['id']

    # If persona doesn't exist, create it
    db = get_db()
    cursor = db.execute('''
        INSERT INTO users (username, email, password_hash, display_name, is_ai_persona)
        VALUES (?, ?, 'N/A', ?, 1)
    ''', (
        persona_slug,
        f'{persona_slug}@soulfra.ai',
        AI_PERSONAS[persona_slug]['name']
    ))
    db.commit()
    persona_id = cursor.lastrowid
    db.close()

    return persona_id


def analyze_quiz_answers(session_id: int) -> Dict[str, Any]:
    """
    Analyze quiz answers from narrative session

    Args:
        session_id: ID of narrative session

    Returns:
        Analysis dict with scores and insights
    """
    db = get_db()

    # Get session and answers
    session = db.execute('''
        SELECT game_state, brand_slug FROM narrative_sessions WHERE id = ?
    ''', (session_id,)).fetchone()

    db.close()

    if not session:
        return {'error': 'Session not found'}

    game_state = json.loads(session['game_state']) if session['game_state'] else {}
    answers = game_state.get('answers', {})

    # Calculate scores for each AI persona
    scores = {persona: 0.0 for persona in AI_PERSONAS.keys()}

    # Simple scoring: High ratings (4-5) indicate interest in that persona's themes
    # We'll score based on which brand they chose and their answer patterns

    brand_slug = session['brand_slug']

    # Brand they chose gives them a starting bonus with that AI
    if brand_slug in scores:
        scores[brand_slug] += 3.0

    # Analyze answer patterns
    total_answers = len(answers)
    if total_answers > 0:
        # Calculate average rating
        ratings = [ans.get('rating', 3) for ans in answers.values()]
        avg_rating = sum(ratings) / len(ratings)

        # High engagement (many high ratings) = deep interest
        high_ratings = sum(1 for r in ratings if r >= 4)
        engagement_ratio = high_ratings / total_answers

        # Distribute scores based on engagement and brand choice
        if brand_slug == 'soulfra':
            scores['soulfra'] += engagement_ratio * 5.0
        elif brand_slug == 'calriven':
            scores['calriven'] += engagement_ratio * 5.0
        elif brand_slug == 'deathtodata':
            scores['deathtodata'] += engagement_ratio * 5.0

        # Secondary personas get fractional scores
        for persona in scores:
            if persona != brand_slug:
                scores[persona] += (avg_rating / 5.0) * 2.0

    # Find best match
    best_match = max(scores.items(), key=lambda x: x[1])
    matched_persona = best_match[0]

    return {
        'scores': scores,
        'matched_persona': matched_persona,
        'engagement_ratio': engagement_ratio if total_answers > 0 else 0,
        'total_answers': total_answers
    }


def generate_personality_traits(analysis: Dict[str, Any]) -> List[str]:
    """
    Generate personality traits based on quiz analysis

    Args:
        analysis: Analysis dict from analyze_quiz_answers()

    Returns:
        List of personality trait strings
    """
    traits = []

    matched = analysis['matched_persona']
    engagement = analysis.get('engagement_ratio', 0)

    # Base traits from matched persona
    persona_traits = {
        'soulfra': ['curious', 'philosophical', 'introspective', 'mysterious'],
        'calriven': ['creative', 'analytical', 'systematic', 'ambitious'],
        'deathtodata': ['principled', 'protective', 'independent', 'vigilant'],
        'theauditor': ['logical', 'thorough', 'skeptical', 'precise']
    }

    traits.extend(persona_traits.get(matched, []))

    # Add engagement-based traits
    if engagement > 0.7:
        traits.append('highly engaged')
    elif engagement > 0.5:
        traits.append('thoughtful')

    # Add secondary personas as interests
    scores = analysis['scores']
    secondary = sorted([(k, v) for k, v in scores.items() if k != matched], key=lambda x: x[1], reverse=True)

    if len(secondary) > 0 and secondary[0][1] > 2.0:
        traits.append(f'interested in {secondary[0][0]}')

    return traits[:6]  # Limit to top 6 traits


def build_profile_from_quiz(session_id: int, user_id: int) -> Dict[str, Any]:
    """
    Build complete user profile from quiz answers and assign AI friend

    Args:
        session_id: ID of narrative session
        user_id: ID of user

    Returns:
        Complete profile dict
    """
    # Analyze answers
    analysis = analyze_quiz_answers(session_id)

    if 'error' in analysis:
        return analysis

    # Generate traits
    traits = generate_personality_traits(analysis)

    # Get AI friend ID
    matched_persona = analysis['matched_persona']
    ai_friend_id = get_ai_persona_id(matched_persona)

    # Build complete profile
    profile = {
        'matched_ai': matched_persona,
        'ai_friend_name': AI_PERSONAS[matched_persona]['name'],
        'ai_friend_description': AI_PERSONAS[matched_persona]['description'],
        'scores': analysis['scores'],
        'traits': traits,
        'engagement': analysis['engagement_ratio'],
        'quiz_session_id': session_id
    }

    # Save to database
    db = get_db()

    db.execute('''
        UPDATE users
        SET personality_profile = ?,
            ai_friend_id = ?
        WHERE id = ?
    ''', (json.dumps(profile), ai_friend_id, user_id))

    db.commit()
    db.close()

    print(f"✅ Built profile for user {user_id}: Matched with {AI_PERSONAS[matched_persona]['name']}")

    return profile


def get_user_profile(user_id: int) -> Dict[str, Any]:
    """
    Get user's personality profile

    Args:
        user_id: ID of user

    Returns:
        Profile dict or None
    """
    db = get_db()

    user = db.execute('''
        SELECT personality_profile, ai_friend_id FROM users WHERE id = ?
    ''', (user_id,)).fetchone()

    db.close()

    if not user or not user['personality_profile']:
        return None

    profile = json.loads(user['personality_profile'])
    profile['ai_friend_id'] = user['ai_friend_id']

    return profile


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("\n🧪 Testing Profile Builder\n")

    # Test with sample session
    print("Test: Analyzing quiz answers")

    # Create mock session
    from database import get_db
    db = get_db()

    # Insert test session
    test_game_state = json.dumps({
        'answers': {
            '1': {'rating': 5},
            '2': {'rating': 4},
            '3': {'rating': 5},
            '4': {'rating': 3},
            '5': {'rating': 4}
        }
    })

    cursor = db.execute('''
        INSERT INTO narrative_sessions (user_id, brand_slug, status, game_state)
        VALUES (1, 'soulfra', 'in_progress', ?)
    ''', (test_game_state,))

    session_id = cursor.lastrowid
    db.commit()
    db.close()

    # Build profile
    profile = build_profile_from_quiz(session_id, 1)

    print(f"\nProfile built:")
    print(f"  Matched AI: {profile['matched_ai']}")
    print(f"  AI Friend: {profile['ai_friend_name']}")
    print(f"  Traits: {', '.join(profile['traits'])}")
    print(f"  Scores: {profile['scores']}")

    print("\n✅ Profile builder tests complete!\n")

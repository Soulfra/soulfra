#!/usr/bin/env python3
"""
Brand AI Orchestrator - Manages Cast of Neural Network Characters

Intelligently decides which brand AI personas should comment on which posts to:
1. Prevent all AIs spamming every post (feels fake!)
2. Create natural, relevant engagement
3. Match brand personalities to post content
4. Build cross-brand network effect

Think of it as: "Which of our AI characters would ACTUALLY care about this post?"

Usage:
    python3 brand_ai_orchestrator.py analyze-post 42
    python3 brand_ai_orchestrator.py generate-comments 42
    python3 brand_ai_orchestrator.py stats
"""

import sqlite3
import json
from typing import List, Dict, Optional
from database import get_db
from brand_ai_persona_generator import get_brand_ai_persona_config


# ==============================================================================
# RELEVANCE SCORING
# ==============================================================================

def calculate_brand_post_relevance(brand_config: Dict, post_content: str) -> float:
    """
    Calculate how relevant a brand is to a post (0.0 - 1.0)

    Uses:
    - Brand personality/tone keywords
    - Brand wordmap (vocabulary)
    - Post content analysis

    Example:
        TechFlow (personality: "analytical, data-driven") + Post about databases
        → High relevance (0.8)

        Ocean Dreams (personality: "calm, flowing") + Post about databases
        → Low relevance (0.2)
    """
    score = 0.0
    post_lower = post_content.lower()

    # Base score for any brand
    base_score = 0.1

    # Check personality keywords (40%)
    personality = brand_config.get('personality', '').lower()
    personality_keywords = [k.strip() for k in personality.split(',')]

    personality_matches = sum(1 for keyword in personality_keywords if keyword in post_lower)
    if personality_keywords:
        personality_score = min(personality_matches / len(personality_keywords), 1.0) * 0.4
    else:
        personality_score = 0.0

    # Check tone keywords (30%)
    tone = brand_config.get('tone', '').lower()
    tone_words = tone.split()
    tone_matches = sum(1 for word in tone_words if word in post_lower)
    if tone_words:
        tone_score = min(tone_matches / len(tone_words), 1.0) * 0.3
    else:
        tone_score = 0.0

    # Check brand values (30%)
    values = brand_config.get('values', [])
    if isinstance(values, list):
        value_matches = sum(1 for value in values if value.lower() in post_lower)
        if values:
            value_score = min(value_matches / len(values), 1.0) * 0.3
        else:
            value_score = 0.0
    else:
        value_score = 0.0

    # Total score
    score = base_score + personality_score + tone_score + value_score

    return min(score, 1.0)


def select_relevant_brands_for_post(post_id: int, max_brands: int = 3, min_relevance: float = 0.3) -> List[Dict]:
    """
    Select which brand AI personas should comment on a post

    Args:
        post_id: Post ID
        max_brands: Maximum number of brands to select
        min_relevance: Minimum relevance score (0.0 - 1.0)

    Returns:
        List of persona configs sorted by relevance

    Strategy:
    1. Score all brand personas for relevance
    2. Filter by minimum relevance
    3. Sort by score
    4. Return top N
    5. Add some randomness to feel natural
    """
    db = get_db()

    # Get post
    post = db.execute('''
        SELECT * FROM posts WHERE id = ?
    ''', (post_id,)).fetchone()

    if not post:
        db.close()
        return []

    post_dict = dict(post)
    post_content = f"{post_dict['title']} {post_dict['content']}"

    # Get all brand AI personas
    personas = db.execute('''
        SELECT
            u.username,
            b.id as brand_id,
            b.name as brand_name,
            b.slug as brand_slug,
            b.personality,
            b.tone,
            b.config_json
        FROM users u
        JOIN brands b ON u.username = b.slug
        WHERE u.is_ai_persona = 1
    ''').fetchall()

    db.close()

    if not personas:
        return []

    # Score each brand
    scored_personas = []

    for persona in personas:
        persona_dict = dict(persona)

        # Parse brand config
        try:
            brand_config = json.loads(persona_dict['config_json']) if persona_dict['config_json'] else {}
        except (json.JSONDecodeError, TypeError):
            brand_config = {}

        brand_config['name'] = persona_dict['brand_name']
        brand_config['personality'] = persona_dict['personality']
        brand_config['tone'] = persona_dict['tone']

        # Calculate relevance
        relevance = calculate_brand_post_relevance(brand_config, post_content)

        if relevance >= min_relevance:
            scored_personas.append({
                'username': persona_dict['username'],
                'brand_slug': persona_dict['brand_slug'],
                'brand_name': persona_dict['brand_name'],
                'relevance': relevance,
                'config': brand_config
            })

    # Sort by relevance (descending)
    scored_personas.sort(key=lambda x: x['relevance'], reverse=True)

    # Return top N
    return scored_personas[:max_brands]


# ==============================================================================
# ENGAGEMENT TIERS
# ==============================================================================

def get_brand_engagement_tier(brand_slug: str) -> str:
    """
    Get engagement tier for brand

    Tiers:
    - free: Passive (comments only when highly relevant)
    - pro: Active (comments more frequently)
    - enterprise: Proactive (initiates conversations)

    For now, all brands are 'free' tier.
    In future, this will check a subscription table.
    """
    # TODO: Check brand_subscriptions table
    return 'free'


def should_brand_comment(brand_slug: str, relevance: float) -> bool:
    """
    Decide if brand AI should comment based on tier and relevance

    Free tier: Only comment if relevance > 0.5
    Pro tier: Comment if relevance > 0.3
    Enterprise tier: Comment if relevance > 0.1
    """
    tier = get_brand_engagement_tier(brand_slug)

    if tier == 'free':
        return relevance > 0.5
    elif tier == 'pro':
        return relevance > 0.3
    elif tier == 'enterprise':
        return relevance > 0.1
    else:
        return relevance > 0.5  # Default to free


# ==============================================================================
# ORCHESTRATION
# ==============================================================================

def orchestrate_brand_comments(post_id: int, dry_run: bool = False) -> List[Dict]:
    """
    Orchestrate which brand AIs should comment on a post

    Args:
        post_id: Post ID
        dry_run: If True, don't actually generate comments (just show plan)

    Returns:
        List of selected personas with relevance scores

    This is the "conductor" - decides who plays when!
    """
    # Get relevant brands
    relevant_brands = select_relevant_brands_for_post(post_id, max_brands=3, min_relevance=0.3)

    if not relevant_brands:
        print(f"No relevant brand AI personas found for post {post_id}")
        return []

    # Filter by tier permissions
    selected_brands = []
    for brand_info in relevant_brands:
        if should_brand_comment(brand_info['brand_slug'], brand_info['relevance']):
            selected_brands.append(brand_info)

    if dry_run:
        print()
        print(f"📋 ORCHESTRATION PLAN FOR POST {post_id}")
        print("=" * 70)
        print()
        print(f"Found {len(relevant_brands)} relevant brands:")
        for brand in relevant_brands:
            status = "✅ WILL COMMENT" if brand in selected_brands else "❌ FILTERED (tier/relevance)"
            print(f"  {status} {brand['brand_name']:<20} (relevance: {brand['relevance']:.2f})")
        print()
        print(f"Selected {len(selected_brands)} brands to comment")
        print()

    return selected_brands


# ==============================================================================
# STATS
# ==============================================================================

def get_orchestration_stats() -> Dict:
    """Get statistics about AI orchestration"""
    db = get_db()

    # Count total AI personas
    total_personas = db.execute('''
        SELECT COUNT(*) as count FROM users WHERE is_ai_persona = 1
    ''').fetchone()['count']

    # Count brand-specific personas
    brand_personas = db.execute('''
        SELECT COUNT(*) as count
        FROM users u
        JOIN brands b ON u.username = b.slug
        WHERE u.is_ai_persona = 1
    ''').fetchone()['count']

    # Count total comments by AI personas
    ai_comments = db.execute('''
        SELECT COUNT(*) as count
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE u.is_ai_persona = 1
    ''').fetchone()['count']

    # Get most active AI personas
    active_personas = db.execute('''
        SELECT
            u.username,
            u.display_name,
            COUNT(c.id) as comment_count
        FROM users u
        LEFT JOIN comments c ON u.id = c.user_id
        WHERE u.is_ai_persona = 1
        GROUP BY u.id
        ORDER BY comment_count DESC
        LIMIT 5
    ''').fetchall()

    db.close()

    return {
        'total_personas': total_personas,
        'brand_personas': brand_personas,
        'ai_comments': ai_comments,
        'active_personas': [dict(p) for p in active_personas]
    }


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """CLI for orchestration"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 brand_ai_orchestrator.py analyze-post <post_id>")
        print("  python3 brand_ai_orchestrator.py generate-comments <post_id>")
        print("  python3 brand_ai_orchestrator.py stats")
        print()
        print("Examples:")
        print("  python3 brand_ai_orchestrator.py analyze-post 42")
        print("  python3 brand_ai_orchestrator.py stats")
        return

    command = sys.argv[1]

    if command == 'analyze-post':
        if len(sys.argv) < 3:
            print("Error: Missing post ID")
            return

        post_id = int(sys.argv[2])

        # Dry run - just show plan
        orchestrate_brand_comments(post_id, dry_run=True)

    elif command == 'generate-comments':
        if len(sys.argv) < 3:
            print("Error: Missing post ID")
            return

        post_id = int(sys.argv[2])

        # Get selected brands
        selected_brands = orchestrate_brand_comments(post_id, dry_run=False)

        print()
        print(f"🤖 GENERATING COMMENTS FROM {len(selected_brands)} BRAND AIs")
        print("=" * 70)
        print()

        for brand_info in selected_brands:
            print(f"Generating comment from: {brand_info['brand_name']}")
            print(f"  Relevance: {brand_info['relevance']:.2f}")
            print()

            # TODO: Actually generate comments using ollama_auto_commenter
            # For now, just show the plan
            print(f"  → Would call ollama_auto_commenter with {brand_info['brand_slug']}")
            print()

    elif command == 'stats':
        print("=" * 70)
        print("📊 BRAND AI ORCHESTRATION STATISTICS")
        print("=" * 70)
        print()

        stats = get_orchestration_stats()

        print(f"Total AI Personas: {stats['total_personas']}")
        print(f"Brand-Specific Personas: {stats['brand_personas']}")
        print(f"Total AI Comments: {stats['ai_comments']}")
        print()

        print("Most Active AI Personas:")
        for persona in stats['active_personas']:
            print(f"  @{persona['username']:<20} {persona['comment_count']} comments")
        print()

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Progression System - Track user advancement from Anonymous → Super User

Implements 5-tier progression:
1. Anonymous - Just scanned QR / visited site
2. Registered - Created account
3. Active - Completed 1 narrative game
4. Engaged - Completed 3+ learning chapters
5. Super User - Completed all 7 chapters + unlocked everything

Each tier unlocks new features.
"""

from datetime import datetime
from typing import Dict, List, Optional
from database import get_db
import json


# Tier definitions
TIERS = {
    1: {
        'name': 'Anonymous',
        'description': 'Just arrived. Exploring the system.',
        'unlocks': [
            'Browse content',
            'View QR codes',
            'Read blogs'
        ],
        'icon': '👤'
    },
    2: {
        'name': 'Registered',
        'description': 'Created an account. Part of the community.',
        'unlocks': [
            'Post comments',
            'Create blog posts',
            'Join discussions',
            'Generate QR codes'
        ],
        'icon': '✍️'
    },
    3: {
        'name': 'Active',
        'description': 'Completed a narrative game. Engaged user.',
        'unlocks': [
            'Brand discussions',
            'AI assistant access',
            'Custom quizzes',
            'DM via QR (in-person only)'
        ],
        'icon': '🎮'
    },
    4: {
        'name': 'Engaged',
        'description': 'Deep into the learning system. Building skills.',
        'unlocks': [
            'Idea processor (AI-powered)',
            'Fork brands',
            'Chapter version control',
            'Advanced QR faucet'
        ],
        'icon': '🔥'
    },
    5: {
        'name': 'Super User',
        'description': 'Mastered the system. Full access unlocked.',
        'unlocks': [
            'API key generation',
            'Deploy forked brands',
            'Subdomain routing',
            'Full platform access'
        ],
        'icon': '🚀'
    }
}


def get_user_tier(user_id: Optional[int]) -> int:
    """
    Calculate user's current tier based on their activity

    Args:
        user_id: User ID (None for anonymous)

    Returns:
        Tier number (1-5)
    """
    if not user_id:
        return 1  # Anonymous

    db = get_db()

    # Check if registered (has user record)
    user = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        return 1

    # Tier 2: Registered
    tier = 2

    # Check for completed narrative games
    completed_games = db.execute('''
        SELECT COUNT(*) as count FROM narrative_sessions
        WHERE user_id = ? AND status = 'completed'
    ''', (user_id,)).fetchone()

    if completed_games and completed_games['count'] >= 1:
        tier = 3  # Active

    # Check for completed learning chapters
    learning_progress = db.execute('''
        SELECT chapters_completed FROM user_learning_progress
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if learning_progress:
        chapters = json.loads(learning_progress['chapters_completed'] or '[]')

        if len(chapters) >= 3:
            tier = 4  # Engaged

        if len(chapters) >= 7:
            tier = 5  # Super User

    db.close()
    return tier


def get_tier_info(tier: int) -> Dict:
    """Get tier information"""
    return TIERS.get(tier, TIERS[1])


def get_user_progress(user_id: Optional[int]) -> Dict:
    """
    Get complete user progression data

    Returns:
        Dict with tier, unlocks, next tier requirements, etc.
    """
    current_tier = get_user_tier(user_id)
    tier_info = get_tier_info(current_tier)

    # Calculate progress to next tier
    next_tier = min(current_tier + 1, 5)
    next_tier_info = get_tier_info(next_tier)

    # Get activity stats
    stats = {
        'narrative_games_completed': 0,
        'chapters_completed': 0,
        'posts_created': 0,
        'comments_made': 0,
        'brands_forked': 0,
        'qr_scans': 0,
        'has_api_key': False
    }

    if user_id:
        db = get_db()

        # Narrative games
        games = db.execute('''
            SELECT COUNT(*) as count FROM narrative_sessions
            WHERE user_id = ? AND status = 'completed'
        ''', (user_id,)).fetchone()
        stats['narrative_games_completed'] = games['count'] if games else 0

        # Learning chapters
        learning = db.execute('''
            SELECT chapters_completed FROM user_learning_progress
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        if learning:
            chapters = json.loads(learning['chapters_completed'] or '[]')
            stats['chapters_completed'] = len(chapters)

        # Posts
        posts = db.execute('''
            SELECT COUNT(*) as count FROM posts WHERE user_id = ?
        ''', (user_id,)).fetchone()
        stats['posts_created'] = posts['count'] if posts else 0

        # Comments
        comments = db.execute('''
            SELECT COUNT(*) as count FROM comments WHERE user_id = ?
        ''', (user_id,)).fetchone()
        stats['comments_made'] = comments['count'] if comments else 0

        # Brands forked
        brands = db.execute('''
            SELECT COUNT(*) as count FROM brands WHERE created_by = ? AND is_fork = 1
        ''', (user_id,)).fetchone()
        stats['brands_forked'] = brands['count'] if brands else 0

        # QR scans (via user's email)
        user_data = db.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_data:
            scans = db.execute('''
                SELECT COUNT(*) as count FROM qr_scans
                WHERE scanned_by_email = ?
            ''', (user_data['email'],)).fetchone()
            stats['qr_scans'] = scans['count'] if scans else 0

        # API key
        api_key = db.execute('''
            SELECT id FROM api_keys
            WHERE user_email = (SELECT email FROM users WHERE id = ?)
              AND is_active = 1
        ''', (user_id,)).fetchone()
        stats['has_api_key'] = bool(api_key)

        db.close()

    # Calculate completion percentage
    if current_tier < 5:
        # Requirements for next tier
        requirements = {
            2: {'needs': 'Create an account'},
            3: {'needs': 'Complete 1 narrative game'},
            4: {'needs': 'Complete 3 learning chapters'},
            5: {'needs': 'Complete all 7 learning chapters'}
        }

        progress_pct = 0
        if next_tier == 3:
            # To reach Active: need 1 narrative game
            progress_pct = min(stats['narrative_games_completed'] * 100, 100)
        elif next_tier == 4:
            # To reach Engaged: need 3 chapters
            progress_pct = min((stats['chapters_completed'] / 3) * 100, 100)
        elif next_tier == 5:
            # To reach Super User: need 7 chapters
            progress_pct = (stats['chapters_completed'] / 7) * 100
    else:
        progress_pct = 100
        requirements = {5: {'needs': "You've achieved max tier!"}}

    return {
        'current_tier': current_tier,
        'tier_name': tier_info['name'],
        'tier_description': tier_info['description'],
        'tier_icon': tier_info['icon'],
        'unlocked_features': tier_info['unlocks'],
        'next_tier': next_tier,
        'next_tier_name': next_tier_info['name'],
        'next_tier_icon': next_tier_info['icon'],
        'next_tier_unlocks': next_tier_info['unlocks'],
        'progress_to_next': progress_pct,
        'requirements': requirements.get(next_tier, {}),
        'stats': stats
    }


def get_all_tiers_overview() -> List[Dict]:
    """Get overview of all tiers for display"""
    return [
        {
            'tier': tier_num,
            **tier_info
        }
        for tier_num, tier_info in TIERS.items()
    ]


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        progress = get_user_progress(user_id)

        print(f"\n{'='*60}")
        print(f"USER #{user_id} PROGRESSION")
        print(f"{'='*60}\n")

        print(f"{progress['tier_icon']} Current Tier: {progress['tier_name']} (Tier {progress['current_tier']}/5)")
        print(f"   {progress['tier_description']}\n")

        print(f"📊 Stats:")
        for key, value in progress['stats'].items():
            print(f"   • {key}: {value}")

        print(f"\n🔓 Unlocked Features:")
        for feature in progress['unlocked_features']:
            print(f"   ✓ {feature}")

        if progress['current_tier'] < 5:
            print(f"\n🎯 Next: {progress['next_tier_icon']} {progress['next_tier_name']} ({progress['progress_to_next']:.0f}%)")
            print(f"   {progress['requirements'].get('needs', '')}")
            print(f"\n   Will unlock:")
            for feature in progress['next_tier_unlocks']:
                print(f"   → {feature}")
        else:
            print(f"\n🚀 You've reached Super User! All features unlocked.\n")
    else:
        print("Usage: python3 progression_system.py <user_id>")
        print("\nTier System:")
        for tier in get_all_tiers_overview():
            print(f"\n{tier['icon']} Tier {tier['tier']}: {tier['name']}")
            print(f"   {tier['description']}")
            print(f"   Unlocks: {', '.join(tier['unlocks'][:2])}...")

#!/usr/bin/env python3
"""
User Economy Dashboard - The Practice Room

Aggregates all wordmap economy data for a user:
- Personal wordmap (authentic voice)
- Domain ownership percentages
- Content generation rewards
- Voice recording history
- ASCII wordmap visualization
- JSON-LD export

This powers the `/me` economy dashboard.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import get_db
from text_encoder import (
    ascii_wordmap_viz,
    wordmap_to_jsonld,
    add_tier_emoji,
    ensure_utf8
)


def get_economy_data(user_id: int) -> Dict:
    """
    Get complete economy data for user's dashboard

    Args:
        user_id: User ID

    Returns:
        {
            'user': Basic user info,
            'wordmap': {
                'words': top 50 words,
                'recording_count': total recordings,
                'is_pure_source': has pure source?,
                'pure_source': first recording info,
                'vocabulary_size': total unique words
            },
            'domains': [
                {
                    'domain': 'soulfra.com',
                    'ownership_pct': 45.5,
                    'unlocked_at': timestamp
                }
            ],
            'rewards': Recent ownership rewards,
            'stats': {
                'total_rewards_earned': percentage points,
                'total_domains': count,
                'avg_alignment': average score
            },
            'quick_actions': Available actions
        }
    """
    from user_wordmap_engine import get_user_wordmap, get_wordmap_evolution
    from domain_unlock_engine import get_user_domains
    from ownership_rewards import get_user_reward_history

    db = get_db()

    # Get user profile
    user = db.execute('''
        SELECT id, username, email, display_name, created_at
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    if not user:
        return {'error': 'User not found'}

    user_dict = dict(user)

    # Get user's personal wordmap
    wordmap_data = get_wordmap_evolution(user_id)

    wordmap_info = None
    if 'error' not in wordmap_data:
        top_words = wordmap_data.get('top_20_words', [])
        full_wordmap = wordmap_data.get('current_wordmap', {})

        # Generate ASCII visualization (practice room style)
        ascii_viz = ascii_wordmap_viz(full_wordmap) if full_wordmap else None

        wordmap_info = {
            'words': top_words[:50],  # Top 50 for display
            'recording_count': wordmap_data.get('recordings_processed', 0),
            'is_pure_source': wordmap_data.get('pure_source') is not None,
            'pure_source': wordmap_data.get('pure_source'),
            'vocabulary_size': wordmap_data.get('vocabulary_size', 0),
            'last_updated': wordmap_data.get('last_updated'),
            'ascii_viz': ascii_viz  # Practice room ASCII art
        }

    # Get owned domains
    domains = get_user_domains(user_id)

    domains_list = []
    if domains and 'domains' in domains:
        # Get tier for each domain
        for d in domains['domains']:
            domain_name = d['domain']

            # Lookup tier from database
            db = get_db()
            tier_result = db.execute('''
                SELECT tier FROM domain_contexts WHERE domain = ?
            ''', (domain_name,)).fetchone()

            tier = tier_result['tier'] if tier_result else 'common'

            domains_list.append({
                'domain': domain_name,
                'domain_with_emoji': add_tier_emoji(domain_name, tier),
                'tier': tier,
                'ownership_pct': d['ownership_percentage'],
                'unlocked_at': d['unlocked_at']
            })

    # Get recent rewards
    rewards = get_user_reward_history(user_id, limit=10)

    # Calculate stats
    total_rewards = sum(r['reward_pct'] for r in rewards) if rewards else 0.0
    avg_alignment = (
        sum(r['alignment_score'] for r in rewards) / len(rewards)
        if rewards else 0.0
    )

    # Get voice recordings count
    recordings_count = db.execute('''
        SELECT COUNT(*) as count
        FROM simple_voice_recordings
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    # Quick actions
    quick_actions = [
        {
            'label': 'Record Voice Memo',
            'url': '/voice',
            'icon': 'mic',
            'primary': True
        },
        {
            'label': 'Generate Content',
            'url': '/content-generator',
            'icon': 'file-text'
        },
        {
            'label': 'View All Domains',
            'url': '/domains',
            'icon': 'globe'
        },
        {
            'label': 'Export JSON-LD',
            'url': '/me/export-jsonld',
            'icon': 'download'
        }
    ]

    return {
        'user': user_dict,
        'wordmap': wordmap_info,
        'domains': domains_list,
        'rewards': rewards,
        'stats': {
            'total_rewards_earned': total_rewards,
            'total_domains': len(domains_list),
            'avg_alignment': avg_alignment,
            'total_recordings': recordings_count['count'] if recordings_count else 0
        },
        'quick_actions': quick_actions
    }


def get_domain_economy_stats(domain: str) -> Dict:
    """
    Get economy stats for a specific domain

    Returns:
        {
            'domain': 'soulfra.com',
            'total_owners': count,
            'total_rewards_claimed': count,
            'avg_alignment': score,
            'top_contributors': [...]
        }
    """
    from ownership_rewards import get_domain_reward_stats
    from domain_wordmap_aggregator import get_domain_wordmap

    db = get_db()

    # Get domain wordmap
    domain_wordmap = get_domain_wordmap(domain)

    # Get reward stats
    reward_stats = get_domain_reward_stats(domain)

    # Get top contributors (owners with highest %)
    top_owners = db.execute('''
        SELECT u.username, u.display_name, do.ownership_percentage
        FROM domain_ownership do
        JOIN users u ON do.user_id = u.id
        WHERE do.domain = ?
        ORDER BY do.ownership_percentage DESC
        LIMIT 5
    ''', (domain,)).fetchall()

    return {
        'domain': domain,
        'wordmap': domain_wordmap,
        'total_owners': reward_stats.get('unique_claimants', 0),
        'total_rewards_claimed': reward_stats.get('total_rewards', 0),
        'avg_alignment': reward_stats.get('avg_alignment', 0.0),
        'top_contributors': [dict(row) for row in top_owners]
    }


def get_user_content_history(user_id: int, limit: int = 20) -> List[Dict]:
    """
    Get user's content generation history

    Returns list of generated content with alignment scores
    """
    db = get_db()

    # Get from ownership_rewards table (linked to content)
    content = db.execute('''
        SELECT
            domain,
            content_type,
            alignment_score,
            reward_pct,
            created_at
        FROM ownership_rewards
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    return [dict(row) for row in content]


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 user_economy.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    economy = get_economy_data(user_id)

    print(json.dumps(economy, indent=2))

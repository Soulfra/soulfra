#!/usr/bin/env python3
"""
Ownership Rewards - Earn Domain % Through Content Creation

The Economy Loop:
1. Create content (pitch deck, blog, social) from voice memo
2. Calculate wordmap alignment score (how well it matches domain voice)
3. High alignment (>0.7) = earn +0.5% domain ownership
4. Medium alignment (0.4-0.7) = earn +0.25% domain ownership
5. Low alignment (<0.4) = no reward

Caps:
- Max 100% total ownership per user per domain
- Daily reward limit: 5% max per day per domain

This creates the incentive: Use your authentic voice → build domain ownership → increase influence
"""

import json
from typing import Dict, Optional
from datetime import datetime, timedelta
from database import get_db
from wordmap_pitch_integrator import calculate_wordmap_alignment
from domain_unlock_engine import increase_ownership
from domain_wordmap_aggregator import get_domain_wordmap, recalculate_domain_wordmap


REWARD_TIERS = {
    'excellent': {'threshold': 0.7, 'reward_pct': 0.5},
    'good': {'threshold': 0.4, 'reward_pct': 0.25},
    'poor': {'threshold': 0.0, 'reward_pct': 0.0}
}

DAILY_REWARD_CAP = 5.0  # Max 5% per day
MAX_OWNERSHIP = 100.0


def init_ownership_rewards_table():
    """Track ownership rewards history"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS ownership_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            content_type TEXT NOT NULL,
            content_id INTEGER,
            alignment_score REAL NOT NULL,
            reward_pct REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    print("✅ ownership_rewards table created")


def calculate_content_reward(
    user_id: int,
    domain: str,
    content_text: str,
    content_type: str = 'pitch_deck',
    content_id: Optional[int] = None
) -> Dict:
    """
    Calculate ownership reward for generated content

    Args:
        user_id: User who created content
        domain: Domain the content is for
        content_text: Full content text (pitch deck, blog, social post)
        content_type: 'pitch_deck', 'blog_post', 'social_post'
        content_id: Optional ID of content (recording_id, etc.)

    Returns:
        {
            'alignment_score': 0.0-1.0,
            'reward_pct': percentage earned,
            'tier': 'excellent', 'good', or 'poor',
            'new_ownership': updated ownership %,
            'can_claim': bool,
            'reason': explanation
        }
    """
    db = get_db()

    # Get domain wordmap
    domain_wordmap_data = get_domain_wordmap(domain)

    if not domain_wordmap_data:
        # No domain wordmap yet - recalculate
        recalculate_domain_wordmap(domain)
        domain_wordmap_data = get_domain_wordmap(domain)

        if not domain_wordmap_data:
            return {
                'error': f'Domain {domain} has no wordmap',
                'can_claim': False,
                'reason': 'Domain needs at least one owner with a personal wordmap'
            }

    domain_wordmap = domain_wordmap_data['wordmap']

    # Calculate alignment
    alignment_score = calculate_wordmap_alignment(domain_wordmap, content_text)

    # Determine reward tier
    tier = 'poor'
    reward_pct = 0.0

    for tier_name, tier_config in sorted(REWARD_TIERS.items(), key=lambda x: x[1]['threshold'], reverse=True):
        if alignment_score >= tier_config['threshold']:
            tier = tier_name
            reward_pct = tier_config['reward_pct']
            break

    # Check daily cap
    today = datetime.now().date()
    today_rewards = db.execute('''
        SELECT SUM(reward_pct) as total
        FROM ownership_rewards
        WHERE user_id = ?
        AND domain = ?
        AND DATE(created_at) = ?
    ''', (user_id, domain, today)).fetchone()

    total_today = today_rewards['total'] or 0.0

    if total_today + reward_pct > DAILY_REWARD_CAP:
        return {
            'alignment_score': alignment_score,
            'tier': tier,
            'reward_pct': 0.0,
            'can_claim': False,
            'reason': f'Daily reward cap reached ({total_today:.2f}% of {DAILY_REWARD_CAP}%)'
        }

    # Check max ownership
    current_ownership = db.execute('''
        SELECT do.ownership_percentage
        FROM domain_ownership do
        JOIN domain_contexts dc ON do.domain_id = dc.id
        WHERE do.user_id = ? AND dc.domain = ?
    ''', (user_id, domain)).fetchone()

    current_pct = current_ownership['ownership_percentage'] if current_ownership else 0.0

    if current_pct >= MAX_OWNERSHIP:
        return {
            'alignment_score': alignment_score,
            'tier': tier,
            'reward_pct': 0.0,
            'can_claim': False,
            'reason': f'Max ownership reached (100%)'
        }

    # Cap reward to not exceed 100%
    actual_reward = min(reward_pct, MAX_OWNERSHIP - current_pct)

    return {
        'alignment_score': alignment_score,
        'tier': tier,
        'reward_pct': actual_reward,
        'can_claim': actual_reward > 0,
        'current_ownership': current_pct,
        'potential_new_ownership': current_pct + actual_reward,
        'reason': f'{tier.upper()} content ({alignment_score:.2%} alignment)'
    }


def claim_content_reward(
    user_id: int,
    domain: str,
    content_text: str,
    content_type: str = 'pitch_deck',
    content_id: Optional[int] = None
) -> Dict:
    """
    Claim ownership reward for content

    Returns:
        {
            'success': bool,
            'reward_claimed': percentage earned,
            'new_ownership': updated total,
            'transaction_id': reward record ID
        }
    """
    db = get_db()

    # Calculate reward
    reward_calc = calculate_content_reward(user_id, domain, content_text, content_type, content_id)

    if not reward_calc.get('can_claim'):
        return {
            'success': False,
            'error': reward_calc.get('reason'),
            'alignment_score': reward_calc.get('alignment_score')
        }

    reward_pct = reward_calc['reward_pct']

    # Increase ownership
    success = increase_ownership(user_id, domain, reward_pct)

    if not success:
        return {
            'success': False,
            'error': 'Failed to increase ownership'
        }

    # Record reward
    cursor = db.execute('''
        INSERT INTO ownership_rewards
        (user_id, domain, content_type, content_id, alignment_score, reward_pct)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, domain, content_type, content_id, reward_calc['alignment_score'], reward_pct))

    transaction_id = cursor.lastrowid
    db.commit()

    # Recalculate domain wordmap (ownership changed)
    recalculate_domain_wordmap(domain)

    return {
        'success': True,
        'reward_claimed': reward_pct,
        'new_ownership': reward_calc['potential_new_ownership'],
        'transaction_id': transaction_id,
        'tier': reward_calc['tier'],
        'alignment_score': reward_calc['alignment_score']
    }


def get_user_reward_history(user_id: int, limit: int = 10) -> list:
    """Get user's reward history"""
    db = get_db()

    rewards = db.execute('''
        SELECT domain, content_type, alignment_score, reward_pct, created_at
        FROM ownership_rewards
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    return [dict(row) for row in rewards]


def get_domain_reward_stats(domain: str) -> Dict:
    """Get reward statistics for a domain"""
    db = get_db()

    stats = db.execute('''
        SELECT
            COUNT(*) as total_rewards,
            SUM(reward_pct) as total_pct_awarded,
            AVG(alignment_score) as avg_alignment,
            COUNT(DISTINCT user_id) as unique_claimants
        FROM ownership_rewards
        WHERE domain = ?
    ''', (domain,)).fetchone()

    return dict(stats)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ownership_rewards.py init")
        sys.exit(1)

    if sys.argv[1] == 'init':
        init_ownership_rewards_table()

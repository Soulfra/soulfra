#!/usr/bin/env python3
"""
Ownership Ledger - Track ownership percentages per domain

Formula:
    ownership_% = base_tier_% + (stars × 0.5%) + (posts × 0.2%) + (referrals × 1%)

Max ownership per user per domain: 50%
Platform reserve: 20%

Database schema:
- domains: All available domains
- user_domains: User's unlocked domains (based on tier)
- domain_ownership: Ownership percentages per user per domain
- ownership_history: Audit trail of ownership changes
- github_profiles: Cached GitHub data for tier calculation
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from database import get_db


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_ownership_tables():
    """Initialize ownership tracking tables"""
    conn = get_db()

    # Domains table - All available domains
    conn.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_name TEXT UNIQUE NOT NULL,
            tier_requirement INTEGER NOT NULL,
            category TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # GitHub profiles - Cached GitHub data for tier calculation
    conn.execute('''
        CREATE TABLE IF NOT EXISTS github_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            github_username TEXT UNIQUE NOT NULL,
            github_id INTEGER UNIQUE NOT NULL,
            total_repos INTEGER DEFAULT 0,
            total_stars INTEGER DEFAULT 0,
            total_followers INTEGER DEFAULT 0,
            api_key TEXT,
            tier INTEGER DEFAULT 0,
            last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # User domains - Tracks which domains user has unlocked
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unlocked_via TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (domain_id) REFERENCES domains(id),
            UNIQUE(user_id, domain_id)
        )
    ''')

    # Domain ownership - Percentage ownership per user per domain
    conn.execute('''
        CREATE TABLE IF NOT EXISTS domain_ownership (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_id INTEGER NOT NULL,
            ownership_percentage REAL DEFAULT 0.0,
            base_tier_percentage REAL DEFAULT 0.0,
            stars_bonus REAL DEFAULT 0.0,
            posts_bonus REAL DEFAULT 0.0,
            referrals_bonus REAL DEFAULT 0.0,
            last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (domain_id) REFERENCES domains(id),
            UNIQUE(user_id, domain_id)
        )
    ''')

    # Ownership history - Audit trail
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ownership_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_id INTEGER NOT NULL,
            old_percentage REAL,
            new_percentage REAL,
            change_reason TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (domain_id) REFERENCES domains(id)
        )
    ''')

    # Referrals - Track who referred who
    conn.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_user_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL,
            referred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_user_id) REFERENCES users(id),
            FOREIGN KEY (referred_user_id) REFERENCES users(id),
            UNIQUE(referred_user_id)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# TIER CALCULATION
# ==============================================================================

def calculate_tier_from_github(github_username: str, github_data: Dict) -> int:
    """
    Calculate user tier from GitHub activity

    Args:
        github_username: GitHub username
        github_data: Dict with 'repos', 'stars', 'followers'

    Returns:
        Tier (0-4)
    """

    # Extract counts (filter out empty/bot repos)
    real_repos = github_data.get('repos', 0)
    real_stars = github_data.get('stars', 0)
    real_followers = github_data.get('followers', 0)

    # Tier logic (from ECONOMIC_MODEL.md)
    if real_repos >= 100 and real_followers >= 50:
        return 4  # VIP
    elif real_repos >= 50 or real_stars >= 10:
        return 3  # Creator
    elif real_stars >= 2:
        return 2  # Contributor
    elif real_stars >= 1:
        return 1  # Commenter
    else:
        return 0  # Entry


def get_base_tier_percentage(tier: int) -> float:
    """
    Get base ownership percentage for tier

    Tier 0: 0%
    Tier 1: 5%
    Tier 2: 7%
    Tier 3: 10%
    Tier 4: 25%
    """
    tier_base = {
        0: 0.0,
        1: 5.0,
        2: 7.0,
        3: 10.0,
        4: 25.0
    }
    return tier_base.get(tier, 0.0)


# ==============================================================================
# OWNERSHIP CALCULATION
# ==============================================================================

def calculate_ownership(user_id: int, domain_id: int) -> float:
    """
    Calculate user's ownership percentage for a domain

    Formula:
        ownership_% = base_tier_% + (stars × 0.5%) + (posts × 0.2%) + (referrals × 1%)

    Max ownership: 50%

    Returns:
        Ownership percentage (0.0 - 50.0)
    """

    conn = get_db()

    # Get GitHub profile for tier
    github = conn.execute(
        'SELECT tier, total_stars FROM github_profiles WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    if not github:
        return 0.0

    tier = github['tier']
    total_stars = github['total_stars']

    # Base tier percentage
    base = get_base_tier_percentage(tier)

    # Stars bonus (0.5% per star)
    stars_bonus = total_stars * 0.5

    # Posts bonus (0.2% per post for this domain)
    posts = conn.execute(
        '''
        SELECT COUNT(*) as count FROM posts
        WHERE user_id = ? AND domain_id = ?
        ''',
        (user_id, domain_id)
    ).fetchone()
    posts_count = posts['count'] if posts else 0
    posts_bonus = posts_count * 0.2

    # Referrals bonus (1% per referral)
    referrals = conn.execute(
        'SELECT COUNT(*) as count FROM referrals WHERE referrer_user_id = ?',
        (user_id,)
    ).fetchone()
    referrals_count = referrals['count'] if referrals else 0
    referrals_bonus = referrals_count * 1.0

    # Total ownership
    total = base + stars_bonus + posts_bonus + referrals_bonus

    # Cap at 50%
    ownership = min(total, 50.0)

    conn.close()

    return ownership


def update_ownership(user_id: int, domain_id: int, reason: str = "recalculation") -> float:
    """
    Recalculate and update ownership percentage for user/domain

    Args:
        user_id: User ID
        domain_id: Domain ID
        reason: Reason for update (for audit trail)

    Returns:
        New ownership percentage
    """

    conn = get_db()

    # Get current ownership
    current = conn.execute(
        'SELECT ownership_percentage FROM domain_ownership WHERE user_id = ? AND domain_id = ?',
        (user_id, domain_id)
    ).fetchone()

    old_percentage = current['ownership_percentage'] if current else 0.0

    # Calculate new ownership
    new_percentage = calculate_ownership(user_id, domain_id)

    # Get GitHub profile for breakdown
    github = conn.execute(
        'SELECT tier, total_stars FROM github_profiles WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    tier = github['tier'] if github else 0
    total_stars = github['total_stars'] if github else 0

    base = get_base_tier_percentage(tier)
    stars_bonus = total_stars * 0.5

    # Posts bonus
    posts = conn.execute(
        'SELECT COUNT(*) as count FROM posts WHERE user_id = ? AND domain_id = ?',
        (user_id, domain_id)
    ).fetchone()
    posts_count = posts['count'] if posts else 0
    posts_bonus = posts_count * 0.2

    # Referrals bonus
    referrals = conn.execute(
        'SELECT COUNT(*) as count FROM referrals WHERE referrer_user_id = ?',
        (user_id,)
    ).fetchone()
    referrals_count = referrals['count'] if referrals else 0
    referrals_bonus = referrals_count * 1.0

    # Update or insert ownership
    conn.execute('''
        INSERT INTO domain_ownership (
            user_id, domain_id, ownership_percentage,
            base_tier_percentage, stars_bonus, posts_bonus, referrals_bonus,
            last_calculated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, domain_id) DO UPDATE SET
            ownership_percentage = excluded.ownership_percentage,
            base_tier_percentage = excluded.base_tier_percentage,
            stars_bonus = excluded.stars_bonus,
            posts_bonus = excluded.posts_bonus,
            referrals_bonus = excluded.referrals_bonus,
            last_calculated = excluded.last_calculated
    ''', (
        user_id, domain_id, new_percentage,
        base, stars_bonus, posts_bonus, referrals_bonus,
        datetime.utcnow()
    ))

    # Record history
    conn.execute('''
        INSERT INTO ownership_history (
            user_id, domain_id, old_percentage, new_percentage, change_reason
        ) VALUES (?, ?, ?, ?, ?)
    ''', (user_id, domain_id, old_percentage, new_percentage, reason))

    conn.commit()
    conn.close()

    return new_percentage


# ==============================================================================
# DOMAIN UNLOCKING
# ==============================================================================

TIER_0_DOMAINS = ['soulfra.com']
TIER_1_DOMAINS = ['soulfra.com', 'deathtodata.com', 'calriven.com']
TIER_2_CREATIVE = ['howtocookathome.com', 'stpetepros.com']


def get_unlocked_domains(user_id: int) -> List[Dict]:
    """
    Get all domains unlocked for user based on tier

    Returns:
        List of domain dicts with name, tier, ownership
    """

    conn = get_db()

    # Get user's tier
    github = conn.execute(
        'SELECT tier FROM github_profiles WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    tier = github['tier'] if github else 0

    # Get unlocked domains
    domains = conn.execute('''
        SELECT
            d.id,
            d.domain_name,
            d.tier_requirement,
            d.category,
            do.ownership_percentage
        FROM domains d
        LEFT JOIN domain_ownership do ON d.id = do.domain_id AND do.user_id = ?
        WHERE d.tier_requirement <= ?
        ORDER BY d.tier_requirement, d.domain_name
    ''', (user_id, tier)).fetchall()

    conn.close()

    return [dict(d) for d in domains]


def unlock_domain_for_user(user_id: int, domain_name: str, via: str = "tier_progression") -> bool:
    """
    Unlock a domain for a user and initialize ownership

    Args:
        user_id: User ID
        domain_name: Domain to unlock
        via: How domain was unlocked (tier, choice, rotation, etc)

    Returns:
        True if unlocked successfully
    """

    conn = get_db()

    # Get domain ID
    domain = conn.execute(
        'SELECT id FROM domains WHERE domain_name = ?',
        (domain_name,)
    ).fetchone()

    if not domain:
        conn.close()
        return False

    domain_id = domain['id']

    # Check if already unlocked
    existing = conn.execute(
        'SELECT id FROM user_domains WHERE user_id = ? AND domain_id = ?',
        (user_id, domain_id)
    ).fetchone()

    if existing:
        conn.close()
        return True  # Already unlocked

    # Unlock domain
    conn.execute('''
        INSERT INTO user_domains (user_id, domain_id, unlocked_via)
        VALUES (?, ?, ?)
    ''', (user_id, domain_id, via))

    conn.commit()

    # Initialize ownership
    update_ownership(user_id, domain_id, reason=f"domain_unlocked_via_{via}")

    conn.close()

    return True


# ==============================================================================
# REVENUE DISTRIBUTION
# ==============================================================================

def get_domain_ownership_distribution(domain_id: int) -> Dict:
    """
    Get ownership distribution for a domain

    Returns:
        {
            'total_distributed': 80.0,  # 80% distributed, 20% platform reserve
            'platform_reserve': 20.0,
            'owners': [
                {
                    'user_id': 15,
                    'username': 'matthewmauer',
                    'ownership_percentage': 25.5,
                    'share_of_distributed': 31.875  # 25.5 / 80 * 100
                },
                ...
            ]
        }
    """

    conn = get_db()

    # Get all owners
    owners = conn.execute('''
        SELECT
            do.user_id,
            u.username,
            do.ownership_percentage
        FROM domain_ownership do
        JOIN users u ON do.user_id = u.id
        WHERE do.domain_id = ? AND do.ownership_percentage > 0
        ORDER BY do.ownership_percentage DESC
    ''', (domain_id,)).fetchall()

    conn.close()

    # Calculate total distributed (max 80%, 20% platform reserve)
    total_ownership = sum(o['ownership_percentage'] for o in owners)
    total_distributed = min(total_ownership, 80.0)
    platform_reserve = 100.0 - total_distributed

    # Calculate each owner's share of distributed percentage
    owner_list = []
    for owner in owners:
        share_of_distributed = (owner['ownership_percentage'] / total_distributed * 100) if total_distributed > 0 else 0

        owner_list.append({
            'user_id': owner['user_id'],
            'username': owner['username'],
            'ownership_percentage': owner['ownership_percentage'],
            'share_of_distributed': share_of_distributed
        })

    return {
        'total_distributed': total_distributed,
        'platform_reserve': platform_reserve,
        'owners': owner_list
    }


def calculate_revenue_share(domain_id: int, monthly_revenue: float) -> List[Dict]:
    """
    Calculate revenue share for all owners of a domain

    Args:
        domain_id: Domain ID
        monthly_revenue: Total revenue for the month (e.g., $10,000)

    Returns:
        List of payouts:
        [
            {
                'user_id': 15,
                'username': 'matthewmauer',
                'ownership_percentage': 25.5,
                'payout': 3187.50
            },
            ...
        ]
    """

    distribution = get_domain_ownership_distribution(domain_id)

    # Revenue available for distribution (after platform reserve)
    distributable_revenue = monthly_revenue * (distribution['total_distributed'] / 100.0)

    payouts = []
    for owner in distribution['owners']:
        # Owner's payout = revenue × (ownership / total_distributed)
        payout = monthly_revenue * (owner['ownership_percentage'] / distribution['total_distributed'])

        payouts.append({
            'user_id': owner['user_id'],
            'username': owner['username'],
            'ownership_percentage': owner['ownership_percentage'],
            'payout': round(payout, 2)
        })

    return payouts


# ==============================================================================
# ADMIN / REPORTING
# ==============================================================================

def get_user_ownership_summary(user_id: int) -> Dict:
    """
    Get complete ownership summary for a user

    Returns:
        {
            'user_id': 15,
            'tier': 3,
            'github_stars': 25,
            'total_posts': 50,
            'total_referrals': 5,
            'domains': [
                {
                    'domain_name': 'soulfra.com',
                    'ownership_percentage': 32.5,
                    'base': 10.0,
                    'stars_bonus': 12.5,
                    'posts_bonus': 10.0,
                    'referrals_bonus': 5.0
                },
                ...
            ],
            'total_ownership_value': 125.5  # Sum across all domains
        }
    """

    conn = get_db()

    # Get GitHub profile
    github = conn.execute(
        'SELECT tier, total_stars, total_repos, total_followers FROM github_profiles WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    if not github:
        return {'error': 'User not found'}

    # Get total posts
    posts = conn.execute(
        'SELECT COUNT(*) as count FROM posts WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    # Get total referrals
    referrals = conn.execute(
        'SELECT COUNT(*) as count FROM referrals WHERE referrer_user_id = ?',
        (user_id,)
    ).fetchone()

    # Get all domain ownerships
    ownerships = conn.execute('''
        SELECT
            d.domain_name,
            do.ownership_percentage,
            do.base_tier_percentage,
            do.stars_bonus,
            do.posts_bonus,
            do.referrals_bonus
        FROM domain_ownership do
        JOIN domains d ON do.domain_id = d.id
        WHERE do.user_id = ?
        ORDER BY do.ownership_percentage DESC
    ''', (user_id,)).fetchall()

    conn.close()

    domains = [dict(o) for o in ownerships]
    total_ownership = sum(d['ownership_percentage'] for d in domains)

    return {
        'user_id': user_id,
        'tier': github['tier'],
        'github_stars': github['total_stars'],
        'github_repos': github['total_repos'],
        'github_followers': github['total_followers'],
        'total_posts': posts['count'],
        'total_referrals': referrals['count'],
        'domains': domains,
        'total_ownership_value': round(total_ownership, 2)
    }


# ==============================================================================
# INITIALIZATION
# ==============================================================================

def seed_domains():
    """Seed initial domains into database"""
    conn = get_db()

    domains = [
        # Tier 0
        ('soulfra.com', 0, 'foundation'),

        # Tier 1
        ('deathtodata.com', 1, 'foundation'),
        ('calriven.com', 1, 'foundation'),

        # Tier 2
        ('howtocookathome.com', 2, 'creative'),
        ('stpetepros.com', 2, 'creative'),

        # Tier 3+ (add more as needed)
        ('example-tier3-domain.com', 3, 'rotation'),
    ]

    for domain_name, tier, category in domains:
        conn.execute('''
            INSERT OR IGNORE INTO domains (domain_name, tier_requirement, category)
            VALUES (?, ?, ?)
        ''', (domain_name, tier, category))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    print("Initializing ownership ledger...")
    init_ownership_tables()
    seed_domains()
    print("✅ Ownership ledger initialized")
    print()
    print("Tables created:")
    print("  - domains")
    print("  - github_profiles")
    print("  - user_domains")
    print("  - domain_ownership")
    print("  - ownership_history")
    print("  - referrals")

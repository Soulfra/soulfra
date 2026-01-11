#!/usr/bin/env python3
"""
Ownership Helper - Calculate and manage user ownership across brands

Functions for:
- Calculating ownership % per brand
- Awarding soul tokens
- Getting user rankings
- Calculating multipliers
"""

import sqlite3
from typing import Dict, List, Optional
from database import get_db


def award_soul_tokens(user_id: int, brand_id: int, tokens: int, reason: str = "") -> bool:
    """
    Award soul tokens to a user for a brand

    Args:
        user_id: User ID
        brand_id: Brand ID
        tokens: Number of tokens to award
        reason: Reason for awarding (e.g., "QR scan", "idea submitted")

    Returns:
        bool: True if successful
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if loyalty record exists
        existing = cursor.execute('''
            SELECT id, soul_tokens, contribution_count
            FROM user_brand_loyalty
            WHERE user_id = ? AND brand_id = ?
        ''', (user_id, brand_id)).fetchone()

        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE user_brand_loyalty
                SET soul_tokens = soul_tokens + ?,
                    contribution_count = contribution_count + 1,
                    last_contribution_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND brand_id = ?
            ''', (tokens, user_id, brand_id))
        else:
            # Create new record
            cursor.execute('''
                INSERT INTO user_brand_loyalty (
                    user_id, brand_id, soul_tokens, contribution_count,
                    last_contribution_at
                )
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', (user_id, brand_id, tokens))

        # Log the contribution (if table exists with correct schema)
        try:
            cursor.execute('''
                INSERT INTO contribution_logs (
                    user_id, action_type, tokens_earned, description
                )
                VALUES (?, ?, ?, ?)
            ''', (user_id, 'token_award', tokens, reason))
        except sqlite3.OperationalError:
            # Table might not exist or have different schema
            pass

        conn.commit()
        return True

    except Exception as e:
        print(f"Error awarding tokens: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_user_ownership(user_id: int) -> List[Dict]:
    """
    Get user's ownership across all brands

    Returns list of dicts with:
    - brand_id, brand_name, brand_slug
    - soul_tokens (user's tokens)
    - total_brand_tokens (all tokens for that brand)
    - ownership_pct (% ownership)
    - rank (user's rank among contributors)
    - contribution_count
    """
    conn = get_db()

    # Get user's loyalty records
    loyalty_records = conn.execute('''
        SELECT
            ubl.brand_id,
            b.name as brand_name,
            b.slug as brand_slug,
            ubl.soul_tokens,
            ubl.contribution_count,
            ubl.steering_power,
            ubl.last_contribution_at
        FROM user_brand_loyalty ubl
        JOIN brands b ON ubl.brand_id = b.id
        WHERE ubl.user_id = ?
        ORDER BY ubl.soul_tokens DESC
    ''', (user_id,)).fetchall()

    results = []

    for record in loyalty_records:
        brand_id = record['brand_id']

        # Get total tokens for this brand
        total_tokens_row = conn.execute('''
            SELECT COALESCE(SUM(soul_tokens), 0) as total
            FROM user_brand_loyalty
            WHERE brand_id = ?
        ''', (brand_id,)).fetchone()

        total_brand_tokens = total_tokens_row['total'] if total_tokens_row else 0

        # Calculate ownership %
        ownership_pct = 0
        if total_brand_tokens > 0:
            ownership_pct = (record['soul_tokens'] / total_brand_tokens) * 100

        # Get user's rank for this brand
        rank_row = conn.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM user_brand_loyalty
            WHERE brand_id = ? AND soul_tokens > ?
        ''', (brand_id, record['soul_tokens'])).fetchone()

        rank = rank_row['rank'] if rank_row else 1

        # Get total contributors for this brand
        total_contributors_row = conn.execute('''
            SELECT COUNT(*) as total
            FROM user_brand_loyalty
            WHERE brand_id = ?
        ''', (brand_id,)).fetchone()

        total_contributors = total_contributors_row['total'] if total_contributors_row else 0

        results.append({
            'brand_id': brand_id,
            'brand_name': record['brand_name'],
            'brand_slug': record['brand_slug'],
            'soul_tokens': record['soul_tokens'],
            'total_brand_tokens': total_brand_tokens,
            'ownership_pct': ownership_pct,
            'rank': rank,
            'total_contributors': total_contributors,
            'contribution_count': record['contribution_count'],
            'steering_power': record['steering_power'],
            'last_contribution_at': record['last_contribution_at']
        })

    conn.close()
    return results


def get_brand_leaderboard(brand_id: int, limit: int = 50) -> List[Dict]:
    """
    Get top contributors for a brand

    Returns list of dicts with:
    - user_id, username, display_name
    - soul_tokens
    - ownership_pct
    - rank
    - contribution_count
    """
    conn = get_db()

    # Get total tokens for this brand
    total_tokens_row = conn.execute('''
        SELECT COALESCE(SUM(soul_tokens), 0) as total
        FROM user_brand_loyalty
        WHERE brand_id = ?
    ''', (brand_id,)).fetchone()

    total_brand_tokens = total_tokens_row['total'] if total_tokens_row else 1  # Avoid division by zero

    # Get top contributors
    contributors = conn.execute('''
        SELECT
            ubl.user_id,
            u.username,
            u.display_name,
            ubl.soul_tokens,
            ubl.contribution_count,
            ubl.last_contribution_at,
            ROW_NUMBER() OVER (ORDER BY ubl.soul_tokens DESC) as rank
        FROM user_brand_loyalty ubl
        JOIN users u ON ubl.user_id = u.id
        WHERE ubl.brand_id = ?
        ORDER BY ubl.soul_tokens DESC
        LIMIT ?
    ''', (brand_id, limit)).fetchall()

    results = []
    for contributor in contributors:
        ownership_pct = (contributor['soul_tokens'] / total_brand_tokens) * 100

        results.append({
            'user_id': contributor['user_id'],
            'username': contributor['username'],
            'display_name': contributor['display_name'] or contributor['username'],
            'soul_tokens': contributor['soul_tokens'],
            'ownership_pct': ownership_pct,
            'rank': contributor['rank'],
            'contribution_count': contributor['contribution_count'],
            'last_contribution_at': contributor['last_contribution_at']
        })

    conn.close()
    return results


def get_user_total_tokens(user_id: int) -> int:
    """Get user's total tokens across all brands"""
    conn = get_db()
    result = conn.execute('''
        SELECT COALESCE(SUM(soul_tokens), 0) as total
        FROM user_brand_loyalty
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    conn.close()

    return result['total'] if result else 0


def get_user_contribution_history(user_id: int, limit: int = 20) -> List[Dict]:
    """
    Get user's recent contribution history

    Returns list of dicts with:
    - action_type, tokens_earned, description
    - brand_name, created_at
    """
    conn = get_db()

    # Check if contribution_logs table exists
    tables = conn.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='contribution_logs'
    ''').fetchall()

    if not tables:
        conn.close()
        return []

    contributions = conn.execute('''
        SELECT
            cl.contribution_type as action_type,
            cl.bits_awarded as tokens_earned,
            cl.description,
            cl.created_at,
            NULL as brand_name,
            NULL as brand_slug
        FROM contribution_logs cl
        WHERE cl.user_id = ?
        ORDER BY cl.created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    conn.close()

    return [dict(c) for c in contributions]


def calculate_user_multiplier(user_id: int, domain_slug: Optional[str] = None) -> float:
    """
    Calculate user's current multiplier based on:
    - Base multiplier: 1.0
    - Loyalty bonus: +0.1 per 10 contributions
    - Domain affinity: +0.2 if all contributions on same domain

    Args:
        user_id: User ID
        domain_slug: Optional domain to check affinity

    Returns:
        float: Multiplier (e.g., 2.3)
    """
    conn = get_db()

    # Get total contributions
    contributions_row = conn.execute('''
        SELECT COALESCE(SUM(contribution_count), 0) as total
        FROM user_brand_loyalty
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    total_contributions = contributions_row['total'] if contributions_row else 0

    # Base multiplier
    multiplier = 1.0

    # Loyalty bonus: +0.1 per 10 contributions
    loyalty_bonus = (total_contributions // 10) * 0.1
    multiplier += loyalty_bonus

    # Domain affinity bonus (if all contributions on same domain)
    if domain_slug:
        # Check device_multipliers table for domain affinity
        device_row = conn.execute('''
            SELECT multiplier
            FROM device_multipliers
            WHERE device_id IN (
                SELECT device_id FROM device_scans WHERE user_id = ?
            ) AND domain_slug = ?
            LIMIT 1
        ''', (user_id, domain_slug)).fetchone()

        if device_row and device_row['multiplier'] > 1.0:
            multiplier += 0.2  # Domain affinity bonus

    conn.close()

    return round(multiplier, 2)


if __name__ == '__main__':
    print("Ownership Helper - Testing")

    # Test awarding tokens
    print("\n1. Testing token award...")
    success = award_soul_tokens(
        user_id=1,
        brand_id=1,
        tokens=100,
        reason="Test award"
    )
    print(f"   Award successful: {success}")

    # Test getting ownership
    print("\n2. Getting user ownership...")
    ownership = get_user_ownership(user_id=1)
    for brand in ownership:
        print(f"   {brand['brand_name']}: {brand['soul_tokens']} tokens ({brand['ownership_pct']:.2f}% ownership)")

    # Test leaderboard
    print("\n3. Getting brand leaderboard...")
    leaderboard = get_brand_leaderboard(brand_id=1, limit=5)
    for contributor in leaderboard:
        print(f"   #{contributor['rank']} {contributor['display_name']}: {contributor['soul_tokens']} tokens ({contributor['ownership_pct']:.2f}%)")

    print("\n✅ Ownership helper tests complete!")

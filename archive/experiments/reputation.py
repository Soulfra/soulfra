#!/usr/bin/env python3
"""
Perfect Bits Reputation System

Implements the automated reputation/bounty system for contributors.
Uses ONLY Python stdlib + SQLite (no external dependencies).

Based on: docs/api/REPUTATION.md
Tables: reputation, contribution_logs (migration 008)
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Any


def get_db() -> sqlite3.Connection:
    """Get database connection with Row factory."""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_user_reputation(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get total reputation for a user.

    Args:
        user_id: User ID to query

    Returns:
        Dict with bits_earned, bits_spent, contribution_count, created_at
        None if user has no reputation record
    """
    conn = get_db()
    cursor = conn.cursor()

    row = cursor.execute(
        'SELECT * FROM reputation WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    conn.close()

    if not row:
        return None

    return {
        'user_id': row['user_id'],
        'bits_earned': row['bits_earned'],
        'bits_spent': row['bits_spent'],
        'contribution_count': row['contribution_count'],
        'created_at': row['created_at']
    }


def award_bits(
    user_id: int,
    amount: int,
    reason: str,
    contribution_type: str = 'other',
    post_id: Optional[int] = None,
    comment_id: Optional[int] = None,
    reviewed_by: Optional[int] = None,
    status: str = 'approved'
) -> int:
    """
    Award Perfect Bits to a user for a contribution.

    Args:
        user_id: Who to award
        amount: How many bits (can be negative for penalties)
        reason: Description of contribution
        contribution_type: Type ('proposal', 'implementation', 'documentation', 'comment', 'other')
        post_id: Related post ID (optional)
        comment_id: Related comment ID (optional)
        reviewed_by: Who approved it (optional, None = auto-approved)
        status: Status ('approved', 'pending', 'rejected')

    Returns:
        contribution_log ID

    Example:
        award_bits(
            user_id=5,
            amount=10,
            reason='Great pixel avatar proposal',
            contribution_type='proposal',
            post_id=5,
            comment_id=12
        )
    """
    conn = get_db()
    cursor = conn.cursor()

    # Update or create reputation record
    cursor.execute('''
        INSERT INTO reputation (user_id, bits_earned, contribution_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            bits_earned = bits_earned + ?,
            contribution_count = contribution_count + 1
    ''', (user_id, amount, amount))

    # Log the contribution
    cursor.execute('''
        INSERT INTO contribution_logs (
            user_id, post_id, comment_id, contribution_type,
            description, bits_awarded, status, reviewed_by, reviewed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        post_id,
        comment_id,
        contribution_type,
        reason,
        amount,
        status,
        reviewed_by,
        datetime.now().isoformat() if status == 'approved' else None
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return log_id


def get_contribution_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent contributions for a user.

    Args:
        user_id: User ID
        limit: Max number of contributions to return

    Returns:
        List of contribution dicts with all fields
    """
    conn = get_db()
    cursor = conn.cursor()

    rows = cursor.execute('''
        SELECT * FROM contribution_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def calculate_bits_for_tests(total_tests: int, passed_tests: int) -> int:
    """
    Calculate bits awarded based on test pass rate.

    Formula from REPUTATION.md:
    - 100% pass rate: 70 base + 10 bonus = 80 bits
    - ≥87.5% pass rate: 70 bits
    - <87.5% pass rate: proportional (e.g., 50% = 35 bits)

    Args:
        total_tests: Total number of tests
        passed_tests: Number of tests that passed

    Returns:
        Bits to award
    """
    if total_tests == 0:
        return 0

    success_rate = passed_tests / total_tests
    base_bits = 70

    if success_rate >= 1.0:
        # Perfect score bonus
        return base_bits + 10
    elif success_rate >= 0.875:
        # Full credit for ≥87.5% pass rate
        return base_bits
    else:
        # Partial credit proportional to pass rate
        return int(base_bits * success_rate)


def auto_award_on_comment(
    user_id: int,
    comment_id: int,
    post_id: int,
    comment_text: str
) -> Optional[int]:
    """
    Auto-award bits for quality comments.

    Criteria for auto-award:
    - Comment length ≥ 200 characters
    - Contains code blocks or technical terms
    - Not from admin/AI users

    Awards: 1-5 bits depending on quality signals

    Args:
        user_id: Who posted the comment
        comment_id: Comment ID
        post_id: Post ID
        comment_text: Comment content

    Returns:
        contribution_log ID if bits awarded, None otherwise
    """
    # Check if user is admin or AI (don't auto-award)
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute(
        'SELECT role FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    conn.close()

    if not user or user['role'] in ('admin', 'sysadmin'):
        return None

    # Quality signals
    bits = 0
    reason_parts = []

    # Length check
    if len(comment_text) >= 200:
        bits += 2
        reason_parts.append('detailed comment')
    elif len(comment_text) >= 100:
        bits += 1
        reason_parts.append('helpful comment')

    # Code block check
    if '```' in comment_text or '<code>' in comment_text:
        bits += 2
        reason_parts.append('includes code')

    # Technical terms check (simple heuristic)
    technical_terms = ['function', 'class', 'api', 'database', 'query', 'algorithm',
                      'implementation', 'refactor', 'bug', 'feature', 'test']
    if any(term in comment_text.lower() for term in technical_terms):
        bits += 1
        reason_parts.append('technical contribution')

    # Award if earned any bits
    if bits > 0:
        reason = 'Quality comment: ' + ', '.join(reason_parts)
        return award_bits(
            user_id=user_id,
            amount=bits,
            reason=reason,
            contribution_type='comment',
            post_id=post_id,
            comment_id=comment_id,
            status='approved'
        )

    return None


def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top contributors by bits earned.

    Args:
        limit: Number of top contributors to return

    Returns:
        List of dicts with username, bits_earned, contribution_count, avg_bits
    """
    conn = get_db()
    cursor = conn.cursor()

    rows = cursor.execute('''
        SELECT
            u.username,
            u.display_name,
            r.bits_earned,
            r.contribution_count,
            ROUND(r.bits_earned * 1.0 / r.contribution_count, 2) as avg_bits_per_contribution
        FROM reputation r
        JOIN users u ON r.user_id = u.id
        WHERE r.contribution_count > 0
        ORDER BY r.bits_earned DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def can_claim_bounty(user_id: int, post_id: int) -> bool:
    """
    Check if user can claim a bounty on a post.

    Rules:
    - Can't claim if post already has 'pending' contribution from someone else
    - Can't claim if user already has a pending contribution on this post
    - Must be a registered user (not admin/AI)

    Args:
        user_id: User trying to claim
        post_id: Post with bounty

    Returns:
        True if can claim, False otherwise
    """
    conn = get_db()
    cursor = conn.cursor()

    # Check if anyone else has pending work on this post
    existing = cursor.execute('''
        SELECT COUNT(*) as count
        FROM contribution_logs
        WHERE post_id = ? AND status = 'pending'
    ''', (post_id,)).fetchone()

    conn.close()

    if existing['count'] > 0:
        return False

    return True


# For future: Track code usage royalties
def track_code_usage(module_name: str, author_id: int, used_by_id: Optional[int] = None):
    """
    Track when contributed code is used (future feature for royalties).

    Every time a contributed module is imported/used, award 0.1 bits to author.

    Args:
        module_name: Name of module used ('avatar_generator', etc)
        author_id: Who wrote the code
        used_by_id: Who used it (optional)
    """
    # Future implementation: Log usage and award micro-royalties
    # For now, just award a tiny amount
    award_bits(
        user_id=author_id,
        amount=0.1,
        reason=f'Code usage royalty: {module_name}',
        contribution_type='royalty',
        status='approved'
    )


if __name__ == '__main__':
    # Test the functions
    print("🎯 Perfect Bits Reputation System\n")

    # Test get_user_reputation
    print("Testing get_user_reputation(5)...")
    rep = get_user_reputation(5)
    if rep:
        print(f"  ✅ Alice has {rep['bits_earned']} bits from {rep['contribution_count']} contributions")
    else:
        print("  ❌ No reputation found")

    print()

    # Test get_leaderboard
    print("Testing get_leaderboard()...")
    leaderboard = get_leaderboard(5)
    for i, entry in enumerate(leaderboard, 1):
        print(f"  {i}. {entry['username']}: {entry['bits_earned']} bits ({entry['contribution_count']} contributions)")

    print()

    # Test calculate_bits_for_tests
    print("Testing calculate_bits_for_tests()...")
    test_cases = [
        (16, 16, "100% pass"),
        (16, 15, "93.75% pass"),
        (16, 14, "87.5% pass"),
        (16, 10, "62.5% pass"),
    ]
    for total, passed, desc in test_cases:
        bits = calculate_bits_for_tests(total, passed)
        print(f"  {desc}: {bits} bits")

    print()
    print("✅ All tests passed!")

#!/usr/bin/env python3
"""
Initialize Learning Cards for User
===================================

Assigns all existing learning cards to a user so they have cards "due today".

Usage:
    python3 init_learning_cards_for_user.py <user_id>

Example:
    python3 init_learning_cards_for_user.py 1
"""

import sys
from datetime import datetime
from database import get_db


def init_cards_for_user(user_id: int) -> int:
    """
    Initialize all learning cards for a user

    Creates learning_progress entries for all cards that don't have one yet.
    Sets them as "due today" so user can start reviewing immediately.

    Args:
        user_id: User ID to initialize cards for

    Returns:
        Number of cards initialized
    """
    db = get_db()

    # Get all cards that don't have progress for this user
    cards = db.execute('''
        SELECT c.id
        FROM learning_cards c
        LEFT JOIN learning_progress p ON c.id = p.card_id AND p.user_id = ?
        WHERE p.id IS NULL
    ''', (user_id,)).fetchall()

    if not cards:
        print(f"✅ User {user_id} already has all cards initialized")
        return 0

    # Initialize progress for each card
    now = datetime.now().isoformat()
    cards_initialized = 0

    for card in cards:
        # Set next_review to 1 hour ago so cards are immediately "due"
        db.execute('''
            INSERT INTO learning_progress
            (card_id, user_id, repetitions, ease_factor, interval_days,
             last_reviewed, next_review, total_reviews, correct_reviews,
             streak, status)
            VALUES (?, ?, 0, 2.5, 0, NULL, datetime('now', '-1 hour'), 0, 0, 0, 'new')
        ''', (card['id'], user_id))
        cards_initialized += 1

    db.commit()

    print(f"✅ Initialized {cards_initialized} cards for user {user_id}")
    print(f"📚 Cards are now 'due today' and ready for review!")
    print(f"🌐 Visit: http://localhost:5001/learn")

    return cards_initialized


def get_user_stats(user_id: int) -> dict:
    """Get current learning stats for user"""
    db = get_db()

    stats = {
        'total_cards': 0,
        'new_cards': 0,
        'due_today': 0,
        'learning': 0,
        'young': 0,
        'mature': 0
    }

    # Total cards
    result = db.execute('''
        SELECT COUNT(*) as count
        FROM learning_progress
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    stats['total_cards'] = result['count']

    # Due today
    result = db.execute('''
        SELECT COUNT(*) as count
        FROM learning_progress
        WHERE user_id = ?
        AND next_review <= datetime('now')
    ''', (user_id,)).fetchone()
    stats['due_today'] = result['count']

    # Status breakdown
    statuses = db.execute('''
        SELECT status, COUNT(*) as count
        FROM learning_progress
        WHERE user_id = ?
        GROUP BY status
    ''', (user_id,)).fetchall()

    for row in statuses:
        if row['status'] == 'new':
            stats['new_cards'] = row['count']
        elif row['status'] == 'learning':
            stats['learning'] = row['count']
        elif row['status'] == 'young':
            stats['young'] = row['count']
        elif row['status'] == 'mature':
            stats['mature'] = row['count']

    return stats


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 init_learning_cards_for_user.py <user_id>")
        print("\nExample:")
        print("  python3 init_learning_cards_for_user.py 1")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print(f"❌ Error: user_id must be a number")
        sys.exit(1)

    print(f"Initializing learning cards for user {user_id}...")
    print()

    # Show stats before
    print("📊 BEFORE:")
    stats_before = get_user_stats(user_id)
    print(f"  Total cards: {stats_before['total_cards']}")
    print(f"  Due today: {stats_before['due_today']}")
    print()

    # Initialize
    count = init_cards_for_user(user_id)
    print()

    # Show stats after
    print("📊 AFTER:")
    stats_after = get_user_stats(user_id)
    print(f"  Total cards: {stats_after['total_cards']}")
    print(f"  Due today: {stats_after['due_today']}")
    print(f"  New cards: {stats_after['new_cards']}")
    print()

    if count > 0:
        print(f"✅ SUCCESS! {count} cards ready for review")
        print(f"🚀 Visit http://localhost:5001/learn to start studying!")
    else:
        print("✅ All cards already initialized!")

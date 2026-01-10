#!/usr/bin/env python3
"""
User Personal Workspace

Personal dashboard for each user - like Anki personal decks.
Shows quiz history, unlocks, stats, AI friend match, and progress.

Features:
- Personal dashboard (/me)
- Quiz history with results
- Unlocked features display
- AI friend match info
- Personal stats and achievements
- Quick actions (retake quiz, export data, etc.)

Usage:
    from user_workspace import get_workspace_data, get_quiz_history

    # Get full workspace data for dashboard
    data = get_workspace_data(user_id=42)

    # Get quiz history only
    quizzes = get_quiz_history(user_id=42)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db


def get_workspace_data(user_id: int) -> Dict:
    """
    Get complete workspace data for user dashboard

    Args:
        user_id: User ID

    Returns:
        Dict with:
        - user: Profile info
        - stats: Quiz/unlock/connection counts
        - recent_activity: Latest quizzes, unlocks
        - ai_friend: Matched AI persona
        - quick_actions: Available actions
    """
    db = get_db()

    # Get user profile
    user = db.execute('''
        SELECT id, username, email, display_name, bio, profile_pic,
               created_at, character_age, total_years_aged, personality_profile
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    if not user:
        return {'error': 'User not found'}

    user_dict = dict(user)

    # Get quiz stats
    quiz_stats = db.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
        FROM narrative_sessions
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    # Get recent quizzes
    recent_quizzes = db.execute('''
        SELECT ns.id, ns.brand_id, b.name as brand_name, b.slug as brand_slug,
               b.emoji as brand_emoji, ns.current_chapter, ns.status,
               ns.created_at, ns.completed_at
        FROM narrative_sessions ns
        LEFT JOIN brands b ON ns.brand_id = b.id
        WHERE ns.user_id = ?
        ORDER BY ns.created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    recent_quizzes_list = [dict(row) for row in recent_quizzes]

    # Get unlocked features
    unlocks = db.execute('''
        SELECT id, feature_key, unlocked_at, unlock_source
        FROM user_unlocks
        WHERE user_id = ?
          AND (expires_at IS NULL OR expires_at > datetime('now'))
        ORDER BY unlocked_at DESC
    ''', (user_id,)).fetchall()

    unlocks_list = [dict(row) for row in unlocks]

    # Get AI friend match (most recent completed quiz)
    ai_friend = None
    latest_completed = db.execute('''
        SELECT b.name, b.slug, b.emoji, b.tagline, ns.completed_at
        FROM narrative_sessions ns
        LEFT JOIN brands b ON ns.brand_id = b.id
        WHERE ns.user_id = ? AND ns.status = 'completed'
        ORDER BY ns.completed_at DESC
        LIMIT 1
    ''', (user_id,)).fetchone()

    if latest_completed:
        ai_friend = dict(latest_completed)

    # Get connection stats
    connection_stats = db.execute('''
        SELECT COUNT(*) as total
        FROM user_connections
        WHERE (user_id_1 = ? OR user_id_2 = ?)
          AND status = 'active'
    ''', (user_id, user_id)).fetchone()

    # Calculate account age
    created = datetime.fromisoformat(user_dict['created_at'])
    account_age_days = (datetime.now() - created).days

    # Build workspace data
    workspace = {
        'user': {
            'id': user_dict['id'],
            'username': user_dict['username'],
            'display_name': user_dict['display_name'] or user_dict['username'],
            'bio': user_dict['bio'],
            'profile_pic': user_dict['profile_pic'],
            'account_age_days': account_age_days
        },
        'stats': {
            'quizzes': {
                'total': quiz_stats['total'] if quiz_stats else 0,
                'completed': quiz_stats['completed'] if quiz_stats else 0,
                'active': quiz_stats['active'] if quiz_stats else 0
            },
            'unlocks': len(unlocks_list),
            'connections': connection_stats['total'] if connection_stats else 0
        },
        'recent_activity': {
            'quizzes': recent_quizzes_list,
            'latest_unlock': unlocks_list[0] if unlocks_list else None
        },
        'ai_friend': ai_friend,
        'unlocks': unlocks_list,
        'quick_actions': {
            'can_take_quiz': True,  # Always allowed
            'can_export_data': True,
            'can_delete_account': True,
            'available_brands': ['soulfra', 'calriven', 'deathtodata']
        }
    }

    return workspace


def get_quiz_history(user_id: int, brand_slug: Optional[str] = None) -> List[Dict]:
    """
    Get quiz history for user

    Args:
        user_id: User ID
        brand_slug: Filter by brand (optional)

    Returns:
        List of quiz sessions with details
    """
    db = get_db()

    if brand_slug:
        quizzes = db.execute('''
            SELECT ns.id, ns.brand_id, b.name as brand_name, b.slug as brand_slug,
                   b.emoji as brand_emoji, b.tagline, ns.current_chapter,
                   ns.game_state, ns.status, ns.created_at, ns.completed_at
            FROM narrative_sessions ns
            LEFT JOIN brands b ON ns.brand_id = b.id
            WHERE ns.user_id = ? AND b.slug = ?
            ORDER BY ns.created_at DESC
        ''', (user_id, brand_slug)).fetchall()
    else:
        quizzes = db.execute('''
            SELECT ns.id, ns.brand_id, b.name as brand_name, b.slug as brand_slug,
                   b.emoji as brand_emoji, b.tagline, ns.current_chapter,
                   ns.game_state, ns.status, ns.created_at, ns.completed_at
            FROM narrative_sessions ns
            LEFT JOIN brands b ON ns.brand_id = b.id
            WHERE ns.user_id = ?
            ORDER BY ns.created_at DESC
        ''', (user_id,)).fetchall()

    return [dict(row) for row in quizzes]


def get_unlock_history(user_id: int) -> List[Dict]:
    """
    Get unlock history for user

    Args:
        user_id: User ID

    Returns:
        List of unlocks with details
    """
    db = get_db()

    unlocks = db.execute('''
        SELECT id, feature_key, unlocked_at, expires_at, unlock_source
        FROM user_unlocks
        WHERE user_id = ?
        ORDER BY unlocked_at DESC
    ''', (user_id,)).fetchall()

    return [dict(row) for row in unlocks]


def get_ai_friend_match(user_id: int) -> Optional[Dict]:
    """
    Get user's AI friend match (from latest completed quiz)

    Args:
        user_id: User ID

    Returns:
        Dict with AI friend info or None
    """
    db = get_db()

    latest_completed = db.execute('''
        SELECT b.id, b.name, b.slug, b.emoji, b.tagline, b.description,
               ns.completed_at, ns.game_state
        FROM narrative_sessions ns
        LEFT JOIN brands b ON ns.brand_id = b.id
        WHERE ns.user_id = ? AND ns.status = 'completed'
        ORDER BY ns.completed_at DESC
        LIMIT 1
    ''', (user_id,)).fetchone()

    if not latest_completed:
        return None

    return dict(latest_completed)


def get_leaderboard_position(user_id: int) -> Dict:
    """
    Get user's position on leaderboard

    Args:
        user_id: User ID

    Returns:
        Dict with leaderboard info
    """
    db = get_db()

    # Get user's completed quiz count
    user_stats = db.execute('''
        SELECT COUNT(*) as completed_quizzes
        FROM narrative_sessions
        WHERE user_id = ? AND status = 'completed'
    ''', (user_id,)).fetchone()

    # Get rank (how many users have more completed quizzes)
    rank = db.execute('''
        SELECT COUNT(DISTINCT ns.user_id) + 1 as rank
        FROM narrative_sessions ns
        WHERE ns.status = 'completed'
        GROUP BY ns.user_id
        HAVING COUNT(*) > ?
    ''', (user_stats['completed_quizzes'] if user_stats else 0,)).fetchone()

    # Get total users
    total_users = db.execute('SELECT COUNT(*) as total FROM users').fetchone()

    return {
        'rank': rank['rank'] if rank else 1,
        'total_users': total_users['total'] if total_users else 0,
        'completed_quizzes': user_stats['completed_quizzes'] if user_stats else 0
    }


def get_available_brands(user_id: int) -> List[Dict]:
    """
    Get brands available for user to take quiz

    Args:
        user_id: User ID

    Returns:
        List of brands with metadata
    """
    db = get_db()

    brands = db.execute('''
        SELECT b.id, b.name, b.slug, b.emoji, b.tagline, b.description,
               COUNT(ns.id) as times_taken
        FROM brands b
        LEFT JOIN narrative_sessions ns ON b.id = ns.brand_id AND ns.user_id = ?
        WHERE b.active = 1
        GROUP BY b.id
        ORDER BY b.name
    ''', (user_id,)).fetchall()

    return [dict(row) for row in brands]


def update_user_profile(user_id: int, updates: Dict) -> tuple[bool, str]:
    """
    Update user profile

    Args:
        user_id: User ID
        updates: Dict with fields to update (username, display_name, bio, etc.)

    Returns:
        Tuple of (success, message)
    """
    db = get_db()

    allowed_fields = ['username', 'display_name', 'bio', 'profile_pic']
    updates_to_apply = {k: v for k, v in updates.items() if k in allowed_fields}

    if not updates_to_apply:
        return False, 'No valid fields to update'

    # Check if username is being changed and if it's taken
    if 'username' in updates_to_apply:
        existing = db.execute(
            'SELECT id FROM users WHERE username = ? AND id != ?',
            (updates_to_apply['username'], user_id)
        ).fetchone()

        if existing:
            return False, 'Username already taken'

    try:
        # Build UPDATE query
        set_clause = ', '.join([f'{field} = ?' for field in updates_to_apply.keys()])
        values = list(updates_to_apply.values()) + [user_id]

        db.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
        db.commit()

        return True, 'Profile updated successfully'

    except Exception as e:
        db.rollback()
        return False, f'Error updating profile: {str(e)}'


# CLI for testing
if __name__ == '__main__':
    import sys

    print("User Workspace\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'dashboard' and len(sys.argv) >= 3:
            # Show dashboard data
            user_id = int(sys.argv[2])
            data = get_workspace_data(user_id)

            if 'error' in data:
                print(f"❌ {data['error']}")
            else:
                print(f"Dashboard for {data['user']['display_name']} (@{data['user']['username']})")
                print(f"\nStats:")
                print(f"  Quizzes: {data['stats']['quizzes']['completed']}/{data['stats']['quizzes']['total']} completed")
                print(f"  Unlocks: {data['stats']['unlocks']}")
                print(f"  Connections: {data['stats']['connections']}")

                if data['ai_friend']:
                    print(f"\nAI Friend: {data['ai_friend']['emoji']} {data['ai_friend']['name']}")

                print(f"\nRecent Activity:")
                for quiz in data['recent_activity']['quizzes'][:3]:
                    status_icon = '✅' if quiz['status'] == 'completed' else '⏳'
                    print(f"  {status_icon} {quiz['brand_emoji']} {quiz['brand_name']} - {quiz['created_at']}")

        elif command == 'quizzes' and len(sys.argv) >= 3:
            # Show quiz history
            user_id = int(sys.argv[2])
            quizzes = get_quiz_history(user_id)

            print(f"Quiz History for User {user_id}:")
            for quiz in quizzes:
                status_icon = '✅' if quiz['status'] == 'completed' else '⏳'
                print(f"  {status_icon} {quiz['brand_emoji']} {quiz['brand_name']}")
                print(f"     Started: {quiz['created_at']}")
                if quiz['completed_at']:
                    print(f"     Completed: {quiz['completed_at']}")
                print()

        elif command == 'leaderboard' and len(sys.argv) >= 3:
            # Show leaderboard position
            user_id = int(sys.argv[2])
            position = get_leaderboard_position(user_id)

            print(f"Leaderboard Position:")
            print(f"  Rank: #{position['rank']} out of {position['total_users']} users")
            print(f"  Completed Quizzes: {position['completed_quizzes']}")

        else:
            print("Unknown command")

    else:
        print("Commands:\n")
        print("  python3 user_workspace.py dashboard <user_id>")
        print("      Show user dashboard\n")
        print("  python3 user_workspace.py quizzes <user_id>")
        print("      Show quiz history\n")
        print("  python3 user_workspace.py leaderboard <user_id>")
        print("      Show leaderboard position\n")
        print("Examples:")
        print("  python3 user_workspace.py dashboard 1")
        print("  python3 user_workspace.py quizzes 1")
        print("  python3 user_workspace.py leaderboard 1")

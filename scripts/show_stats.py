#!/usr/bin/env python3
"""
Show Stats - Display Battlenet-style leaderboard
"""

import sqlite3

DB_PATH = 'soulfra.db'

def show_stats():
    """Display current stats and leaderboard"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("=" * 60)
    print("🏆 SOULFRA LEADERBOARD")
    print("=" * 60)

    # Top contributors by XP
    top_users = conn.execute('''
        SELECT u.email, us.total_xp, us.total_scans, us.scan_streak, us.avatar_code
        FROM user_stats us
        JOIN users u ON us.user_id = u.id
        ORDER BY us.total_xp DESC
        LIMIT 10
    ''').fetchall()

    if top_users:
        print("\n📊 Top Contributors:")
        for i, user in enumerate(top_users, 1):
            print(f"  {i}. {user['email']} - {user['total_xp']} XP "
                  f"({user['total_scans']} scans, {user['scan_streak']} day streak) "
                  f"[{user['avatar_code']}]")
    else:
        print("\n  No users yet. Start scanning to climb the leaderboard!")

    # Recent achievements
    print("\n🎖️  Recent Achievements:")
    recent_achievements = conn.execute('''
        SELECT u.email, ua.achievement_name, ua.badge_emoji, ua.unlocked_at
        FROM user_achievements ua
        JOIN users u ON ua.user_id = u.id
        ORDER BY ua.unlocked_at DESC
        LIMIT 5
    ''').fetchall()

    if recent_achievements:
        for ach in recent_achievements:
            print(f"  {ach['badge_emoji']} {ach['email']} unlocked \"{ach['achievement_name']}\"")
    else:
        print("  No achievements unlocked yet")

    # System totals
    print("\n📈 System Totals:")
    totals = conn.execute('''
        SELECT
            (SELECT COUNT(*) FROM scan_history) as total_scans,
            (SELECT COUNT(*) FROM shared_responses) as total_responses,
            (SELECT SUM(view_count) FROM shared_responses) as total_views,
            (SELECT COUNT(*) FROM scan_sessions WHERE ended_at IS NOT NULL) as completed_sessions
    ''').fetchone()

    print(f"  Total Scans: {totals['total_scans']}")
    print(f"  Shared Responses: {totals['total_responses']}")
    print(f"  Total Views: {totals['total_views'] or 0}")
    print(f"  Completed Sessions: {totals['completed_sessions']}")

    print("=" * 60)

    conn.close()

if __name__ == '__main__':
    show_stats()

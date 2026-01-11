#!/usr/bin/env python3
"""
Nudge System - Facebook Poke Style Interactions

Simple social interaction system:
- Send nudges (like Facebook pokes)
- Track nudge history
- Trigger notifications
- Optionally send emails for important nudges

Usage:
```python
from nudge_system import send_nudge, get_nudge_count

# Send a nudge
send_nudge(from_user_id=1, to_user_id=2, send_email=False)

# Get nudge count between users
count = get_nudge_count(user_id_1=1, user_id_2=2)
```
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from database import get_db


def send_nudge(from_user_id: int, to_user_id: int, send_email: bool = False) -> bool:
    """
    Send a nudge from one user to another (like Facebook poke)

    Args:
        from_user_id: ID of user sending nudge
        to_user_id: ID of user receiving nudge
        send_email: Whether to send email notification (default: False, to avoid spam)

    Returns:
        True if nudge sent successfully
    """
    if from_user_id == to_user_id:
        print("❌ Cannot nudge yourself")
        return False

    db = get_db()

    # Get user info
    from_user = db.execute('SELECT username, email FROM users WHERE id = ?',
                           (from_user_id,)).fetchone()
    to_user = db.execute('SELECT username, email FROM users WHERE id = ?',
                         (to_user_id,)).fetchone()

    if not from_user or not to_user:
        db.close()
        print("❌ User not found")
        return False

    # Create notification
    try:
        from db_helpers import create_notification
        create_notification(
            user_id=to_user_id,
            type='nudge',
            content=f"{from_user['username']} nudged you!",
            link=f"/profile/{from_user['username']}"
        )
    except ImportError:
        # If db_helpers doesn't exist, create notification directly
        db.execute('''
            INSERT INTO notifications (user_id, type, content, link)
            VALUES (?, ?, ?, ?)
        ''', (to_user_id, 'nudge', f"{from_user['username']} nudged you!",
              f"/profile/{from_user['username']}"))
        db.commit()

    # Optionally send email (disabled by default to avoid spam)
    if send_email:
        try:
            from simple_emailer import send_notification_email
            send_notification_email(
                user_email=to_user['email'],
                notification_type='nudge',
                notification_content=f"{from_user['username']} nudged you!",
                link=f"/profile/{from_user['username']}"
            )
        except ImportError:
            print("⚠️  simple_emailer not found - skipping email")

    db.close()

    print(f"✅ {from_user['username']} nudged {to_user['username']}")
    return True


def get_recent_nudges(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent nudges received by a user

    Args:
        user_id: ID of user
        limit: Max number of nudges to return

    Returns:
        List of nudge dicts with sender info and timestamp
    """
    db = get_db()

    nudges = db.execute('''
        SELECT n.id, n.content, n.link, n.created_at, n.read,
               u.username as from_username, u.display_name as from_display_name
        FROM notifications n
        JOIN users u ON u.username = SUBSTR(n.link, 10)
        WHERE n.user_id = ? AND n.type = 'nudge'
        ORDER BY n.created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    db.close()

    return [dict(nudge) for nudge in nudges]


def get_nudge_count(user_id_1: int, user_id_2: int, days: int = 7) -> int:
    """
    Get count of nudges between two users in recent days

    Args:
        user_id_1: First user ID
        user_id_2: Second user ID
        days: Number of days to look back (default: 7)

    Returns:
        Count of nudges exchanged
    """
    db = get_db()

    # Get usernames
    user1 = db.execute('SELECT username FROM users WHERE id = ?', (user_id_1,)).fetchone()
    user2 = db.execute('SELECT username FROM users WHERE id = ?', (user_id_2,)).fetchone()

    if not user1 or not user2:
        db.close()
        return 0

    cutoff = datetime.now() - timedelta(days=days)

    # Count nudges in both directions
    count = db.execute('''
        SELECT COUNT(*) as count FROM notifications
        WHERE type = 'nudge'
        AND created_at > ?
        AND (
            (user_id = ? AND link = ?)
            OR
            (user_id = ? AND link = ?)
        )
    ''', (cutoff, user_id_1, f'/profile/{user2["username"]}',
          user_id_2, f'/profile/{user1["username"]}')).fetchone()['count']

    db.close()

    return count


def mark_nudge_read(notification_id: int, user_id: int) -> bool:
    """
    Mark a nudge notification as read

    Args:
        notification_id: ID of notification
        user_id: ID of user (for security check)

    Returns:
        True if marked as read
    """
    try:
        from db_helpers import mark_notification_read
        return mark_notification_read(notification_id, user_id)
    except ImportError:
        # If db_helpers doesn't exist, mark directly
        db = get_db()
        db.execute('''
            UPDATE notifications
            SET read = 1
            WHERE id = ? AND user_id = ?
        ''', (notification_id, user_id))
        db.commit()
        db.close()
        return True


def nudge_back(from_user_id: int, original_notification_id: int) -> bool:
    """
    Nudge someone back who nudged you

    Args:
        from_user_id: ID of user nudging back
        original_notification_id: ID of original nudge notification

    Returns:
        True if nudge sent
    """
    db = get_db()

    # Get original nudge
    original = db.execute('''
        SELECT user_id, link FROM notifications
        WHERE id = ? AND type = 'nudge'
    ''', (original_notification_id,)).fetchone()

    if not original or original['user_id'] != from_user_id:
        db.close()
        print("❌ Original nudge not found")
        return False

    # Extract username from link
    original_sender_username = original['link'].replace('/profile/', '')

    # Get original sender's user ID
    original_sender = db.execute(
        'SELECT id FROM users WHERE username = ?',
        (original_sender_username,)
    ).fetchone()

    db.close()

    if not original_sender:
        print("❌ Original sender not found")
        return False

    # Send nudge back
    return send_nudge(from_user_id, original_sender['id'])


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("\n🧪 Testing Nudge System\n")

    # Test 1: Send nudge
    print("Test 1: Send nudge")
    result = send_nudge(from_user_id=1, to_user_id=2, send_email=False)
    print(f"Result: {'✅ Sent' if result else '❌ Failed'}\n")

    # Test 2: Get recent nudges
    print("Test 2: Get recent nudges")
    nudges = get_recent_nudges(user_id=2, limit=5)
    print(f"Found {len(nudges)} nudges")
    for nudge in nudges[:3]:
        print(f"  - {nudge['from_username']}: {nudge['content']}")
    print()

    # Test 3: Get nudge count
    print("Test 3: Get nudge count between users")
    count = get_nudge_count(user_id_1=1, user_id_2=2, days=7)
    print(f"Nudges exchanged in last 7 days: {count}\n")

    # Test 4: Nudge back
    print("Test 4: Nudge back")
    if nudges:
        result = nudge_back(from_user_id=2, original_notification_id=nudges[0]['id'])
        print(f"Result: {'✅ Sent' if result else '❌ Failed'}\n")

    print("✅ Nudge system tests complete!\n")

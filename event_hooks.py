#!/usr/bin/env python3
"""
Event Hooks - Wire Systems Together

This module connects events across the platform to trigger:
- Notifications (in-app alerts)
- Emails (optional, configurable)
- Profile updates
- AI interactions

Events:
- Quiz completion → welcome email + profile build + AI friend assignment
- AI comment on post → notification to post author
- Post creation → notify followers (future)
- Nudge received → notification + optional email

Usage:
```python
from event_hooks import on_quiz_completed, on_ai_comment_created

# When quiz finishes
on_quiz_completed(user_id=1, session_id=5)

# When AI comments on a post
on_ai_comment_created(post_id=10, comment_id=42, post_author_id=3)
```
"""

from typing import Optional, Dict, Any
from database import get_db


def on_quiz_completed(user_id: int, session_id: int, send_email: bool = True) -> Dict[str, Any]:
    """
    Handle quiz completion event

    Actions:
    1. Build personality profile
    2. Assign AI friend
    3. Send welcome email
    4. Create notification

    Args:
        user_id: ID of user who completed quiz
        session_id: ID of narrative session
        send_email: Whether to send welcome email (default: True)

    Returns:
        Dict with profile info and status
    """
    print(f"🎉 Quiz completed: user_id={user_id}, session_id={session_id}")

    # Build profile and assign AI friend
    try:
        from profile_builder import build_profile_from_quiz, get_ai_persona_id
        profile = build_profile_from_quiz(session_id, user_id)

        if 'error' in profile:
            print(f"❌ Profile build failed: {profile['error']}")
            return profile
    except Exception as e:
        print(f"❌ Profile build error: {e}")
        return {'error': str(e)}

    # Get user info for email
    db = get_db()
    user = db.execute('SELECT username, email FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()

    if not user:
        return {'error': 'User not found'}

    # Send welcome email
    if send_email:
        try:
            from simple_emailer import send_welcome_email
            email_sent = send_welcome_email(
                user_email=user['email'],
                username=user['username'],
                ai_friend_name=profile['ai_friend_name']
            )
            print(f"📧 Welcome email: {'sent' if email_sent else 'printed to console'}")
        except Exception as e:
            print(f"⚠️  Email failed: {e}")

    # Create notification
    try:
        from db_helpers import create_notification
        create_notification(
            user_id=user_id,
            type='quiz_complete',
            content=f"Welcome! You've been matched with {profile['ai_friend_name']} as your AI friend.",
            link=f"/profile/{user['username']}"
        )
        print(f"🔔 Notification created for user {user_id}")
    except Exception as e:
        print(f"⚠️  Notification failed: {e}")

    return {
        'success': True,
        'profile': profile,
        'email_sent': send_email
    }


def on_post_created(post_id: int, trigger_ai_comments: bool = True) -> Dict[str, Any]:
    """
    Handle post creation event

    Actions:
    1. Trigger AI personas to comment (if enabled)
    2. Notify followers (future)
    3. Create reasoning thread (if applicable)

    Args:
        post_id: ID of newly created post
        trigger_ai_comments: Whether to generate AI comments (default: True)

    Returns:
        Dict with comment IDs and status
    """
    print(f"📝 Post created: post_id={post_id}")

    result = {
        'post_id': post_id,
        'ai_comments': [],
        'success': True
    }

    # Trigger AI commenting
    if trigger_ai_comments:
        try:
            from ollama_auto_commenter import generate_comments_for_post
            print(f"🤖 Triggering AI auto-commenters...")
            comment_ids = generate_comments_for_post(post_id, dry_run=False)
            result['ai_comments'] = comment_ids
            print(f"✅ Generated {len(comment_ids)} AI comment(s)")
        except Exception as e:
            print(f"⚠️  AI commenting failed: {e}")
            result['success'] = False
            result['error'] = str(e)

    return result


def on_ai_comment_created(post_id: int, comment_id: int, ai_persona_slug: str,
                          send_email: bool = False) -> bool:
    """
    Handle AI comment creation event

    Actions:
    1. Notify post author
    2. Optionally send email (disabled by default to avoid spam)

    Args:
        post_id: ID of post that was commented on
        comment_id: ID of new comment
        ai_persona_slug: Slug of AI persona (e.g., 'soulfra')
        send_email: Whether to send email notification (default: False)

    Returns:
        True if notification created
    """
    print(f"🤖 AI comment created: post_id={post_id}, comment_id={comment_id}")

    db = get_db()

    # Get post author
    post = db.execute('SELECT user_id, title, slug FROM posts WHERE id = ?',
                     (post_id,)).fetchone()

    if not post:
        db.close()
        print(f"❌ Post {post_id} not found")
        return False

    # Get post author info
    author = db.execute('SELECT username, email FROM users WHERE id = ?',
                       (post['user_id'],)).fetchone()

    # Get AI persona name
    ai_persona = db.execute('SELECT display_name FROM users WHERE username = ? AND is_ai_persona = 1',
                           (ai_persona_slug,)).fetchone()

    db.close()

    if not author:
        print(f"❌ Post author not found")
        return False

    ai_name = ai_persona['display_name'] if ai_persona else ai_persona_slug

    # Create notification
    try:
        from db_helpers import create_notification
        create_notification(
            user_id=post['user_id'],
            type='ai_comment',
            content=f"{ai_name} commented on your post: {post['title']}",
            link=f"/post/{post['slug']}#comment-{comment_id}"
        )
        print(f"🔔 Notification created for post author {author['username']}")
    except Exception as e:
        print(f"⚠️  Notification failed: {e}")
        return False

    # Optionally send email (disabled by default)
    if send_email and author:
        try:
            from simple_emailer import send_notification_email
            send_notification_email(
                user_email=author['email'],
                notification_type='ai_comment',
                notification_content=f"{ai_name} commented on your post: {post['title']}",
                link=f"/post/{post['slug']}#comment-{comment_id}"
            )
            print(f"📧 Email sent to {author['email']}")
        except Exception as e:
            print(f"⚠️  Email failed: {e}")

    return True


def on_user_registered(user_id: int, send_email: bool = True) -> bool:
    """
    Handle new user registration event

    Actions:
    1. Send welcome email
    2. Create initial notification

    Args:
        user_id: ID of newly registered user
        send_email: Whether to send welcome email (default: True)

    Returns:
        True if processed successfully
    """
    print(f"👤 User registered: user_id={user_id}")

    db = get_db()

    user = db.execute('SELECT username, email FROM users WHERE id = ?',
                     (user_id,)).fetchone()

    db.close()

    if not user:
        print(f"❌ User {user_id} not found")
        return False

    # Create welcome notification
    try:
        from db_helpers import create_notification
        create_notification(
            user_id=user_id,
            type='welcome',
            content="Welcome to Soulfra! Take the quiz to get matched with your AI friend.",
            link="/cringeproof/narrative/soulfra"
        )
        print(f"🔔 Welcome notification created")
    except Exception as e:
        print(f"⚠️  Notification failed: {e}")

    # Send welcome email
    if send_email:
        try:
            from simple_emailer import send_email
            send_email(
                to=user['email'],
                subject=f"Welcome to Soulfra, {user['username']}!",
                body=f"""Hi {user['username']},

Welcome to Soulfra! We're excited to have you here.

Get started:
1. Take the personality quiz: http://localhost:5001/cringeproof/narrative/soulfra
2. Get matched with your AI friend
3. Start chatting!

See you soon,
The Soulfra Team

---
🎮 Generated with Soulfra
"""
            )
            print(f"📧 Welcome email sent to {user['email']}")
        except Exception as e:
            print(f"⚠️  Email failed: {e}")

    return True


def on_nudge_received(from_user_id: int, to_user_id: int, send_email: bool = False) -> bool:
    """
    Handle nudge received event

    This is called by nudge_system.py - included here for completeness

    Args:
        from_user_id: ID of user who sent nudge
        to_user_id: ID of user receiving nudge
        send_email: Whether to send email notification

    Returns:
        True if processed successfully
    """
    # Nudge notifications are handled directly in nudge_system.py
    # This hook is just for logging and future extensions
    print(f"👋 Nudge: {from_user_id} → {to_user_id}")
    return True


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("\n🧪 Testing Event Hooks\n")

    # Test 1: Quiz completion
    print("Test 1: Quiz completion event")
    result = on_quiz_completed(user_id=1, session_id=1, send_email=False)
    print(f"Result: {result}\n")

    # Test 2: AI comment
    print("Test 2: AI comment event")
    result = on_ai_comment_created(
        post_id=1,
        comment_id=1,
        ai_persona_slug='soulfra',
        send_email=False
    )
    print(f"Result: {result}\n")

    # Test 3: Post creation
    print("Test 3: Post creation event")
    result = on_post_created(post_id=1, notify_followers=False)
    print(f"Result: {result}\n")

    # Test 4: User registration
    print("Test 4: User registration event")
    result = on_user_registered(user_id=1, send_email=False)
    print(f"Result: {result}\n")

    print("✅ Event hooks tests complete!\n")

#!/usr/bin/env python3
"""
Avatar Auto-Attach - Automatic Avatar Generation & Attachment
==============================================================

Automatically generates and attaches avatars to all users.

Avatar types:
- AI personas → robohash (cool robot avatars)
- Human users → gravatar with identicon fallback

What it does:
1. Checks if user has avatar
2. If not: generates based on user type
3. Stores in database (avatar_url field)
4. Attaches to all posts/comments by user

Result: Every user has a beautiful avatar automatically!

Usage:
    python3 avatar_auto_attach.py --all          # Process all users
    python3 avatar_auto_attach.py --users 1 2 3  # Specific users
    python3 avatar_auto_attach.py --post 29      # Users on this post
"""

import sys
import hashlib
from database import get_db


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def generate_avatar_url(user, size=200):
    """
    Generate avatar URL based on user type

    - AI personas → robohash (robot avatars)
    - Humans → gravatar (with identicon fallback)
    """

    username = user['username']
    email = user.get('email', f'{username}@soulfra.local')
    is_ai = user.get('is_ai_persona', 0) == 1

    if is_ai:
        # AI persona: robohash
        identifier = hashlib.md5(username.encode('utf-8')).hexdigest()
        return f"https://robohash.org/{identifier}?size={size}x{size}&set=set2"
    else:
        # Human: gravatar with identicon fallback
        email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"


def attach_avatar_to_user(user_id):
    """
    Generate and attach avatar to user

    Returns True if avatar was attached
    """

    conn = get_db()

    # Get user
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        conn.close()
        return False

    user = dict(user)

    # Check if user already has avatar_url
    if user.get('avatar_url'):
        print(f"      User already has avatar: {user['avatar_url'][:50]}...")
        conn.close()
        return False

    # Generate avatar URL
    avatar_url = generate_avatar_url(user)

    # Update database
    conn.execute('''
        UPDATE users
        SET avatar_url = ?
        WHERE id = ?
    ''', (avatar_url, user_id))

    conn.commit()
    conn.close()

    return True


def get_all_users():
    """Get all users"""
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY id').fetchall()
    conn.close()
    return [dict(u) for u in users]


def get_users_on_post(post_id):
    """Get all users who have posted/commented on a post"""

    conn = get_db()

    # Get post author
    post = conn.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,)).fetchone()

    user_ids = set()
    if post:
        user_ids.add(post['user_id'])

    # Get commenters
    comments = conn.execute('SELECT DISTINCT user_id FROM comments WHERE post_id = ?', (post_id,)).fetchall()

    for comment in comments:
        user_ids.add(comment['user_id'])

    conn.close()

    return list(user_ids)


def main():
    """Main entry point"""

    print_header("🎨 Avatar Auto-Attach - Automatic Avatar Generation")

    print("""
Automatically generates avatars for all users:

- AI personas → robohash (robot avatars)
- Humans → gravatar with identicon fallback

Avatars are stored in users.avatar_url field.
    """)

    # Parse arguments
    process_all = '--all' in sys.argv
    user_ids = []
    post_id = None

    if '--users' in sys.argv:
        idx = sys.argv.index('--users')
        # Get all args after --users until next flag
        i = idx + 1
        while i < len(sys.argv) and not sys.argv[i].startswith('--'):
            try:
                user_ids.append(int(sys.argv[i]))
            except ValueError:
                break
            i += 1

    if '--post' in sys.argv:
        idx = sys.argv.index('--post')
        if idx + 1 < len(sys.argv):
            post_id = int(sys.argv[idx + 1])

    # Get users to process
    if process_all:
        users = get_all_users()
        user_ids = [u['id'] for u in users]
        print(f"\n📊 Processing all {len(user_ids)} users...")

    elif post_id:
        user_ids = get_users_on_post(post_id)
        print(f"\n📊 Processing {len(user_ids)} users from post #{post_id}...")

    elif user_ids:
        print(f"\n📊 Processing {len(user_ids)} specific users...")

    else:
        print("❌ Specify --all, --users <ids>, or --post <id>")
        return

    if not user_ids:
        print("❌ No users found")
        return

    # Process users
    print("\n🎨 Generating avatars...\n")

    attached_count = 0
    skipped_count = 0

    for user_id in user_ids:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if not user:
            print(f"   ⚠️  User #{user_id} not found")
            continue

        user = dict(user)

        print(f"   [{user_id}] {user['username']}")

        attached = attach_avatar_to_user(user_id)

        if attached:
            attached_count += 1
            print(f"      ✅ Avatar attached")
        else:
            skipped_count += 1
            print(f"      ⏭️  Skipped (already has avatar)")

    # Summary
    print_header("🎉 Avatar Generation Complete!")

    print(f"""
✅ Processed {len(user_ids)} users:
   - Attached: {attached_count} new avatars
   - Skipped: {skipped_count} (already had avatars)

Avatar types used:
- AI personas: robohash (robot avatars)
- Humans: gravatar with identicon fallback

Next steps:
1. View avatars in user profiles
2. Avatars will now appear on posts/comments
3. Run again after adding new users

All users now have beautiful avatars! 🎨
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")

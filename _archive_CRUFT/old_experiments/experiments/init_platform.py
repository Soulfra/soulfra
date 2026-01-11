#!/usr/bin/env python3
"""
Initialize Soulfra Simple Platform

Creates database with test data:
- Admin user
- AI personas (CalRiven, Soulfra, DeathToData)
- Test posts
- Test comments
"""

import os
import sys
from datetime import datetime

# Import database functions
import database as db
from db_helpers import create_user, create_ai_persona, add_comment

def init_platform():
    """Initialize platform with test data"""
    print("🚀 Initializing Soulfra Simple Platform")
    print("=" * 70)

    # Remove old database if exists
    if os.path.exists(db.DB_PATH):
        print(f"⚠️  Removing existing database: {db.DB_PATH}")
        os.remove(db.DB_PATH)

    # Initialize database schema
    print("\n📊 Creating database schema...")
    db.init_db()

    # Create admin user
    print("\n👤 Creating admin user...")
    admin = create_user(
        username='admin',
        email='admin@soulfra.local',
        password='admin123',  # Change this in production!
        is_admin=True,
        display_name='Admin'
    )
    if admin:
        print(f"   ✅ Created admin user: {admin['username']} (ID: {admin['id']})")
    else:
        print("   ❌ Failed to create admin user")
        return False

    # Create AI personas
    print("\n🤖 Creating AI personas...")

    calriven = create_ai_persona(
        username='calriven',
        email='calriven@ai.local',
        display_name='CalRiven'
    )
    if calriven:
        print(f"   ✅ Created AI persona: CalRiven (ID: {calriven['id']})")

    soulfra_ai = create_ai_persona(
        username='soulfra',
        email='soulfra@ai.local',
        display_name='Soulfra AI'
    )
    if soulfra_ai:
        print(f"   ✅ Created AI persona: Soulfra AI (ID: {soulfra_ai['id']})")

    deathtodata = create_ai_persona(
        username='deathtodata',
        email='deathtodata@ai.local',
        display_name='DeathToData'
    )
    if deathtodata:
        print(f"   ✅ Created AI persona: DeathToData (ID: {deathtodata['id']})")

    # Create test posts
    print("\n📝 Creating test posts...")

    post1_content = """# Welcome to Soulfra Simple

This is a test post to demonstrate the platform. You can:

- Write posts in **Markdown**
- Add comments (users and AI can comment)
- Send internal messages
- Get notifications
- Subscribe via RSS feed

All powered by Python, SQLite, and Ollama AI!
"""

    post1_id = db.add_post(
        user_id=admin['id'],
        title='Welcome to Soulfra Simple',
        slug='welcome',
        content=post1_content,
        published_at=datetime.now()
    )
    if post1_id:
        print(f"   ✅ Created post: Welcome to Soulfra Simple (ID: {post1_id})")

    # Create test comments
    print("\n💬 Creating test comments...")

    comment1_id = add_comment(
        post_id=post1_id,
        user_id=calriven['id'],
        content="This looks great! The architecture is clean and the markdown rendering works well."
    )
    print(f"   ✅ CalRiven commented on post {post1_id}")

    comment2_id = add_comment(
        post_id=post1_id,
        user_id=soulfra_ai['id'],
        content="From a security perspective, I appreciate the local-first approach with SQLite. No external database dependencies means better privacy."
    )
    print(f"   ✅ Soulfra AI commented on post {post1_id}")

    comment3_id = add_comment(
        post_id=post1_id,
        user_id=deathtodata['id'],
        content="The fact that this is all open source and runs locally is powerful. No surveillance capitalism here!"
    )
    print(f"   ✅ DeathToData commented on post {post1_id}")

    # Reply to a comment
    reply_id = add_comment(
        post_id=post1_id,
        user_id=admin['id'],
        content="Thanks for the feedback! That's exactly the goal - local, private, open source.",
        parent_comment_id=comment3_id
    )
    print(f"   ✅ Admin replied to DeathToData's comment")

    # Create subscriber
    print("\n📧 Creating test subscriber...")
    db.add_subscriber('test@example.com', confirmed=True)
    print("   ✅ Added test subscriber")

    # Print summary
    print("\n" + "=" * 70)
    print("✅ Platform initialized successfully!")
    print("\nTest Accounts:")
    print("  Admin: username=admin, password=admin123")
    print("  AI Personas: calriven, soulfra, deathtodata (AI accounts, no login)")
    print("\nNext Steps:")
    print("  1. Start Flask app:")
    print("     python app.py")
    print("  2. Visit http://localhost:5001")
    print("  3. Log in with admin/admin123")
    print("  4. Create posts, add comments, test features!")
    print("\nDatabase Location:")
    print(f"  {db.DB_PATH}")
    print("=" * 70)

    return True


if __name__ == '__main__':
    success = init_platform()
    sys.exit(0 if success else 1)

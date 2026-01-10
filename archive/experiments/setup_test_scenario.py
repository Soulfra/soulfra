#!/usr/bin/env python3
"""
Setup Test Scenario for AI Reasoning Flow

Creates:
1. Test user account (Alice)
2. Test post from Alice asking for feature help
3. Assigns categories and tags
4. Ready for Cal-Riven bridge processing
"""

from datetime import datetime
from db_helpers import create_user, get_user_by_username, add_category_to_post, add_tag_to_post
from database import get_db, add_post
import markdown2

def create_test_user():
    """Create Alice test user"""
    print("📝 Creating test user: Alice...")

    user = create_user(
        username='alice',
        email='alice@example.com',
        password='testpass123',
        display_name='Alice Developer',
        is_admin=False,
        is_ai_persona=False
    )

    if user:
        print(f"   ✅ Created user: {user['username']} (ID: {user['id']})")
        return user
    else:
        # User might already exist
        user = get_user_by_username('alice')
        if user:
            print(f"   ℹ️  User already exists: {user['username']} (ID: {user['id']})")
            return user
        else:
            print("   ❌ Failed to create user")
            return None


def create_test_post(user_id):
    """Create test post from Alice"""
    print("\n📰 Creating test post from Alice...")

    title = "How can I add image upload support to Soulfra?"
    slug = "how-to-add-image-uploads"

    content_md = """I'm really impressed with Soulfra Simple and would love to contribute!

One feature I think would be amazing is image upload support for posts. Right now we can only write text content, but having images would make the platform much more engaging.

## My Questions

1. **Where should we store uploaded images?** Should we use the filesystem or a cloud service like S3?

2. **How do we handle image optimization?** Large images could slow down the site. Should we resize/compress them automatically?

3. **Security concerns?** What validation do we need to prevent malicious file uploads?

4. **Database schema changes?** Do we need a new `images` table or just add image URLs to the posts table?

## What I'm thinking

I was thinking we could:
- Add a file upload field to the post creation form
- Store images in `/static/uploads/` directory
- Use Python's Pillow library for image processing
- Add image URLs to post content as markdown

**Would this approach work? Or is there a better way?**

I'd love to hear CalRiven's thoughts on the architecture, Soulfra's perspective on security, and DeathToData's take on privacy implications of storing user images.

Looking forward to the AI reasoning on this! 🚀"""

    # Convert markdown to HTML
    content_html = markdown2.markdown(
        content_md,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )

    published_at = datetime.now()

    # Add post
    post_id = add_post(
        user_id=user_id,
        title=title,
        slug=slug,
        content=content_html,
        published_at=published_at
    )

    print(f"   ✅ Created post: '{title}' (ID: {post_id})")
    return post_id


def assign_categories_and_tags(post_id):
    """Assign categories and tags to the post"""
    print("\n🏷️  Assigning categories and tags...")

    conn = get_db()

    # Get category IDs
    technology = conn.execute('SELECT id FROM categories WHERE slug = ?', ('technology',)).fetchone()
    ai = conn.execute('SELECT id FROM categories WHERE slug = ?', ('ai',)).fetchone()

    # Get tag IDs
    reasoning = conn.execute('SELECT id FROM tags WHERE slug = ?', ('reasoning',)).fetchone()
    features = conn.execute('SELECT id FROM tags WHERE slug = ?', ('features',)).fetchone()

    # Create features tag if it doesn't exist
    if not features:
        conn.execute('INSERT INTO tags (name, slug) VALUES (?, ?)', ('Features', 'features'))
        conn.commit()
        features = conn.execute('SELECT id FROM tags WHERE slug = ?', ('features',)).fetchone()
        print("   ✅ Created new tag: Features")

    # Create media tag
    media_tag = conn.execute('SELECT id FROM tags WHERE slug = ?', ('media',)).fetchone()
    if not media_tag:
        conn.execute('INSERT INTO tags (name, slug) VALUES (?, ?)', ('Media', 'media'))
        conn.commit()
        media_tag = conn.execute('SELECT id FROM tags WHERE slug = ?', ('media',)).fetchone()
        print("   ✅ Created new tag: Media")

    conn.close()

    # Assign categories
    if technology:
        add_category_to_post(post_id, technology['id'])
        print("   ✅ Added category: Technology")

    if ai:
        add_category_to_post(post_id, ai['id'])
        print("   ✅ Added category: AI")

    # Assign tags
    if reasoning:
        add_tag_to_post(post_id, reasoning['id'])
        print("   ✅ Added tag: reasoning")

    if features:
        add_tag_to_post(post_id, features['id'])
        print("   ✅ Added tag: features")

    if media_tag:
        add_tag_to_post(post_id, media_tag['id'])
        print("   ✅ Added tag: media")


def main():
    print("=" * 70)
    print("🚀 Setting up AI Reasoning Test Scenario")
    print("=" * 70)
    print()

    # Step 1: Create test user
    user = create_test_user()
    if not user:
        print("\n❌ Failed to create test user. Exiting.")
        return

    # Step 2: Create test post
    post_id = create_test_post(user['id'])
    if not post_id:
        print("\n❌ Failed to create test post. Exiting.")
        return

    # Step 3: Assign categories and tags
    assign_categories_and_tags(post_id)

    print("\n" + "=" * 70)
    print("✅ Test scenario setup complete!")
    print("=" * 70)
    print()
    print("📋 Next Steps:")
    print()
    print(f"1. View the post at: http://localhost:5001/post/how-to-add-image-uploads")
    print(f"2. Run AI analysis: python cal_riven_bridge.py --process-id {post_id}")
    print(f"3. Verify reasoning steps appear in the UI")
    print()
    print("💡 Tip: You can also run the bridge in watch mode:")
    print("   python cal_riven_bridge.py --watch")
    print()


if __name__ == '__main__':
    main()

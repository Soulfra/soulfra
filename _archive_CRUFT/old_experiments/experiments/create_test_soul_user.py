#!/usr/bin/env python3
"""
Create Test Soul User - Quick Soul Platform Testing

Generates a realistic test user with:
- Multiple posts with varied content
- Comments showing engagement
- Calculated karma/reputation
- Interests extracted from content
- Printable URLs for testing

Run this to instantly create a test user for the Soul platform system.
"""

import sys
from datetime import datetime, timedelta
from db_helpers import create_user, add_comment
from database import get_db
from soul_model import Soul


# Sample test data
TEST_USER = {
    'username': 'soul_tester',
    'email': 'soul_tester@soulfra.test',
    'password': 'test123',
    'display_name': 'Soul Platform Tester',
    'bio': 'Testing the Soulfra multi-platform Soul system. Interests: coding, gaming, art, and building cool stuff.',
    'is_ai_persona': False
}

TEST_POSTS = [
    {
        'title': 'Building My First Game in Roblox',
        'content': '''Just started learning Lua scripting for Roblox game development!

The platform is surprisingly powerful. I'm working on a tower defense game that uses player stats to determine tower types. Each player's "soul" in the game will have unique abilities based on their interests.

```lua
function calculateTowerType(playerSoul)
    if playerSoul:HasInterest("coding") then
        return "HackerTower"
    end
end
```

Really excited about the possibilities here. The chat moderation system is also interesting - need to make sure the game enforces community rules.''',
        'published_at': datetime.now() - timedelta(days=5)
    },
    {
        'title': 'Minecraft Plugin Development Journey',
        'content': '''Started working on a Minecraft server plugin that imports player data from external sources.

The NBT format is fascinating - you can store custom data right in the player file. I'm experimenting with:
- Custom enchantments representing skills
- Items that reflect player interests (enchanted books for learning, tools for expertise)
- Automatic stat calculation based on activity

The Java API is well-documented but there's definitely a learning curve.''',
        'published_at': datetime.now() - timedelta(days=4)
    },
    {
        'title': 'Thoughts on Digital Identity Systems',
        'content': '''Been thinking a lot about how we represent ourselves across different platforms.

What if your "identity" could travel with you? Not just a username, but your actual preferences, skills, reputation, and style?

Imagine:
- Gaming platforms that adapt to your playstyle
- Social networks that understand your values
- Creative tools that match your aesthetic

The key is making it:
1. **Portable** - Works everywhere
2. **Private** - You control what's shared
3. **Evolving** - Changes as you grow

This is what I'm trying to build.''',
        'published_at': datetime.now() - timedelta(days=3)
    },
    {
        'title': 'Python for Game Development',
        'content': '''Python isn't typically the first choice for game dev, but it's great for:

- **Prototyping** - Quick iteration on mechanics
- **Data processing** - Player stats, analytics
- **Content generation** - Procedural worlds, character builders
- **Backend systems** - Matchmaking, leaderboards

I've been using Python to generate configuration files for Unity and Unreal. The transform pipeline is surprisingly smooth:

```python
soul_pack = compile_user_soul(user_id)
unity_asset = transform_to_unity(soul_pack)
save_asset_bundle(unity_asset)
```

Game engines import the JSON and boom - instant character.''',
        'published_at': datetime.now() - timedelta(days=2)
    },
    {
        'title': 'Building in Public: Platform Connector System',
        'content': '''Just shipped the first version of the platform connector system!

It transforms user identity data into platform-specific formats:
- Roblox → Lua ModuleScript
- Minecraft → NBT/JSON player data
- Unity → Asset bundle JSON
- Voice AI → Persona configuration

The cool part is it's deterministic - same input always produces same output. Your username generates a unique color scheme via SHA-256 hash.

Next steps:
- [ ] Add more platforms (Unreal, Godot)
- [ ] Create game template marketplace
- [ ] Build testing infrastructure

Check it out and let me know what you think!''',
        'published_at': datetime.now() - timedelta(days=1)
    }
]

TEST_COMMENTS = [
    {
        'post_slug': 'building-my-first-game-in-roblox',
        'content': 'Love the idea of soul-based tower types! Are you planning to add multiplayer?'
    },
    {
        'post_slug': 'minecraft-plugin-development-journey',
        'content': 'NBT format is definitely tricky at first but super flexible once you get it. Have you looked at Spigot API?'
    },
    {
        'post_slug': 'thoughts-on-digital-identity-systems',
        'content': 'This is exactly what the web needs. Tired of creating the same profile on 50 different sites.'
    },
    {
        'post_slug': 'python-for-game-development',
        'content': 'Great breakdown! I use Python for Unity editor extensions too - the integration is smoother than people think.'
    },
    {
        'post_slug': 'building-in-public-platform-connector-system',
        'content': 'This is so cool! Just downloaded the Roblox module and it works perfectly. When are you adding Steam integration?'
    }
]


def create_test_soul_user():
    """Create a complete test user with Soul data"""
    print("=" * 70)
    print("🎮 Creating Test Soul User for Platform Testing")
    print("=" * 70)
    print()

    # Check if user already exists
    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', (TEST_USER['username'],)).fetchone()

    if existing:
        print(f"⚠️  User '{TEST_USER['username']}' already exists (id: {existing['id']})")
        print("   Deleting and recreating...\n")

        # Delete existing user and their content
        user_id = existing['id']
        conn.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()

    # Create user
    print(f"👤 Creating user: {TEST_USER['username']}")
    user = create_user(
        username=TEST_USER['username'],
        email=TEST_USER['email'],
        password=TEST_USER['password'],
        display_name=TEST_USER['display_name'],
        is_ai_persona=TEST_USER['is_ai_persona']
    )

    if not user:
        print(f"   ❌ Failed to create user (username may already exist)")
        return None

    user_id = user['id']

    # Update bio manually (create_user doesn't accept bio parameter)
    conn = get_db()
    conn.execute('UPDATE users SET bio = ? WHERE id = ?', (TEST_USER['bio'], user_id))
    conn.commit()
    conn.close()

    print(f"   ✅ Created user (id: {user_id})")
    print()

    # Create posts
    print(f"📝 Creating {len(TEST_POSTS)} test posts...")
    post_ids = []
    conn = get_db()
    for post_data in TEST_POSTS:
        # Generate slug from title
        slug = post_data['title'].lower().replace(' ', '-').replace("'", '')

        cursor = conn.execute('''
            INSERT INTO posts (user_id, title, slug, content, published_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            post_data['title'],
            slug,
            post_data['content'],
            post_data['published_at']
        ))
        post_id = cursor.lastrowid
        post_ids.append(post_id)
        print(f"   ✅ {post_data['title']}")
    conn.commit()
    print()

    # Create comments (add to other users' posts for realism)
    print(f"💬 Creating {len(TEST_COMMENTS)} test comments...")

    # Get some existing posts to comment on (excluding our own)
    other_posts = conn.execute(
        'SELECT id FROM posts WHERE user_id != ? ORDER BY published_at DESC LIMIT 5',
        (user_id,)
    ).fetchall()

    comments_created = 0
    for i, comment_data in enumerate(TEST_COMMENTS):
        # Try to find the post by slug (if it's one of ours)
        target_post = conn.execute(
            'SELECT id FROM posts WHERE slug = ?',
            (comment_data['post_slug'],)
        ).fetchone()

        # If not found, use a random other post
        if not target_post and other_posts:
            target_post = other_posts[i % len(other_posts)]

        if target_post:
            add_comment(
                post_id=target_post['id'],
                user_id=user_id,
                content=comment_data['content']
            )
            comments_created += 1

    print(f"   ✅ Created {comments_created} comments")
    conn.close()
    print()

    # Compile Soul Pack
    print("🧠 Compiling Soul Pack...")
    soul = Soul(user_id)
    pack = soul.compile_pack()

    # Display Soul statistics
    essence = pack['essence']
    expression = pack['expression']

    print(f"   Identity:")
    print(f"      Username: {pack['identity']['username']}")
    print(f"      Display: {pack['identity']['display_name']}")
    print()
    print(f"   Essence:")
    print(f"      Interests: {', '.join(essence['interests'][:5])}")
    print(f"      Expertise: {', '.join(str(k) for k in list(essence['expertise'].keys())[:3])}")
    print(f"      Values: {', '.join(essence['values'][:3])}")
    print()
    print(f"   Expression:")
    print(f"      Posts: {expression.get('post_count', 0)}")
    print(f"      Comments: {expression.get('comment_count', 0)}")
    print(f"      Karma: {expression.get('karma', 0)}")
    print(f"      Activity: {expression.get('activity_level', 0)}")
    print()

    # Generate platform URLs
    print("=" * 70)
    print("🌐 TESTING URLS")
    print("=" * 70)
    print()
    print("Platform Picker:")
    print(f"   http://localhost:5001/soul/{TEST_USER['username']}/platforms")
    print()
    print("Direct Downloads:")
    print(f"   Roblox:    http://localhost:5001/api/soul/transform?user_id={user_id}&platform=roblox&download=true")
    print(f"   Minecraft: http://localhost:5001/api/soul/transform?user_id={user_id}&platform=minecraft&download=true")
    print(f"   Unity:     http://localhost:5001/api/soul/transform?user_id={user_id}&platform=unity&download=true")
    print(f"   Voice:     http://localhost:5001/api/soul/transform?user_id={user_id}&platform=voice&download=true")
    print()
    print("API Endpoints:")
    print(f"   Soul Pack: http://localhost:5001/api/soul/{TEST_USER['username']}")
    print(f"   Similar:   http://localhost:5001/soul/{TEST_USER['username']}/similar")
    print()
    print("=" * 70)
    print("✅ Test user created successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Visit the Platform Picker URL above")
    print("2. Click 'Download Module' for any platform")
    print("3. Verify the downloaded file contains correct data")
    print("4. Run: python3 test_soul_platform_e2e.py")
    print()

    return user_id


if __name__ == '__main__':
    try:
        create_test_soul_user()
    except Exception as e:
        print(f"\n❌ Error creating test user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

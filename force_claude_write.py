#!/usr/bin/env python3
"""
Force Claude to write a blog post from terminal

Usage:
    python3 force_claude_write.py --brand deathtodata --topic "privacy"
    python3 force_claude_write.py --brand calriven --topic "neural networks"
"""

import argparse
import sqlite3
from datetime import datetime
import sys

# Try to import Anthropic (optional)
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    from config_secrets import CLAUDE_API_KEY
except ImportError:
    CLAUDE_API_KEY = None

def get_brand_personality(brand_slug):
    """Get brand personality from database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name, description FROM brands WHERE slug = ?", (brand_slug,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    return {
        "name": result[0],
        "description": result[1] or "A creative content brand"
    }

def generate_with_claude(brand_slug, topic):
    """Generate post using Claude API"""

    if not CLAUDE_AVAILABLE:
        print("✗ Anthropic package not installed. Run: pip install anthropic")
        return None

    if not CLAUDE_API_KEY:
        print("✗ CLAUDE_API_KEY not found in config_secrets.py")
        return None

    brand = get_brand_personality(brand_slug)
    if not brand:
        print(f"✗ Brand '{brand_slug}' not found in database")
        return None

    client = Anthropic(api_key=CLAUDE_API_KEY)

    prompt = f"""
You are writing for the {brand['name']} brand.
Brand focus: {brand['description']}

Topic: {topic}

Write a 500-word blog post about this topic in the brand's voice.
Format as markdown with ## headers.
Make it engaging, informative, and actionable.
"""

    print(f"→ Asking Claude to write about '{topic}' for {brand['name']}...")

    try:
        message = client.messages.create(
            model="claude-sonnet-4",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        content = message.content[0].text
        print(f"✓ Claude generated {len(content)} characters")
        return content

    except Exception as e:
        print(f"✗ Claude API error: {e}")
        return None

def generate_mock_post(brand_slug, topic):
    """Generate a mock post when Claude API isn't available"""

    brand = get_brand_personality(brand_slug)
    if not brand:
        print(f"✗ Brand '{brand_slug}' not found")
        return None

    # Create simple mock post
    title = f"{topic.title()}: A {brand['name']} Perspective"

    content = f"""# {title}

## Introduction

{brand['description']}

This post explores {topic} from the {brand['name']} perspective.

## Key Points

1. **Understanding {topic}** - Breaking down the fundamentals
2. **Why it matters** - The impact on our digital lives
3. **Taking action** - Practical steps you can take today

## The Core Issue

{topic.capitalize()} is becoming increasingly important in today's digital landscape. Here's why:

- Privacy and security are fundamental rights
- Technology moves faster than regulation
- Individual action can drive systemic change

## What You Can Do

1. **Educate yourself** - Understand the technology and implications
2. **Take control** - Use tools that respect your autonomy
3. **Spread awareness** - Share knowledge with your community

## Conclusion

The future of {topic} depends on informed, engaged users. By understanding the stakes and taking action, we can build a better digital world.

---

*This post was auto-generated as a demo. Install Claude API for real content generation.*
"""

    print(f"✓ Generated mock post (Install Claude API for real content)")
    return content

def save_to_database(brand_slug, title, content):
    """Save post to database"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get brand ID
    cursor.execute("SELECT id FROM brands WHERE slug = ?", (brand_slug,))
    result = cursor.fetchone()
    if not result:
        print(f"✗ Brand '{brand_slug}' not found")
        return None

    brand_id = result[0]

    # Create slug
    slug = title.lower().replace(' ', '-').replace(',', '').replace(':', '')[:100]
    slug = f"{slug}-{int(datetime.now().timestamp())}"

    # Insert post
    try:
        cursor.execute("""
            INSERT INTO posts (user_id, title, slug, content, published_at, brand_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            14,  # Claude AI user ID (create this user if needed)
            title,
            slug,
            content,
            datetime.now().isoformat(),
            brand_id
        ))

        post_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✓ Post #{post_id} saved to database")
        print(f"  URL: http://localhost:5001/post/{slug}")

        return post_id

    except Exception as e:
        print(f"✗ Database error: {e}")
        conn.close()
        return None

def main():
    parser = argparse.ArgumentParser(description="Force Claude to write a blog post")
    parser.add_argument("--brand", required=True, help="Brand slug (e.g., deathtodata, calriven)")
    parser.add_argument("--topic", required=True, help="Post topic (e.g., 'privacy', 'neural networks')")
    parser.add_argument("--save", action="store_true", help="Save to database")
    parser.add_argument("--print", action="store_true", help="Print to console")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"FORCE CLAUDE WRITE")
    print(f"Brand: {args.brand}")
    print(f"Topic: {args.topic}")
    print(f"{'='*60}\n")

    # Generate post
    if CLAUDE_AVAILABLE and CLAUDE_API_KEY:
        content = generate_with_claude(args.brand, args.topic)
    else:
        print("⚠️  Claude API not available, using mock generator")
        content = generate_mock_post(args.brand, args.topic)

    if not content:
        print("✗ Failed to generate post")
        sys.exit(1)

    # Extract title from content
    lines = content.split('\n')
    title = lines[0].replace('#', '').strip() if lines else args.topic.title()

    # Print if requested
    if args.print:
        print(f"\n{'-'*60}")
        print(content)
        print(f"{'-'*60}\n")

    # Save if requested
    if args.save:
        save_to_database(args.brand, title, content)

    print("\n✓ Done!\n")

if __name__ == "__main__":
    main()

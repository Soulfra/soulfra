#!/usr/bin/env python3
"""
Offline Blog Post Creator - PROOF IT WORKS!
============================================

GeeksForGeeks-style: "Try it yourself" - 100% OFFLINE

This script proves you can create blog posts with:
- ✅ ZERO internet required
- ✅ Python + SQLite only
- ✅ Instant browser preview
- ✅ No Node.js, no PostgreSQL, no BS

Usage:
    python3 create_blog_post_offline.py

What it does:
    1. Connects to SQLite database (soulfra.db)
    2. Creates a new blog post with current timestamp
    3. Prints the URL to view in browser
    4. Returns post ID and slug
"""

import sqlite3
from datetime import datetime
import sys
import os

# Add current directory to path so we can import database.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import add_post, get_db


def create_offline_post(title=None, content=None, user_id=1):
    """
    Create a blog post completely offline

    Args:
        title: Post title (default: auto-generated with timestamp)
        content: Post content (default: proof of offline functionality)
        user_id: User ID (default: 1, assumes admin user exists)

    Returns:
        dict with post_id, slug, and url
    """

    # Auto-generate title if not provided
    if not title:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"Offline Post Created at {timestamp}"

    # Auto-generate slug from title
    slug = title.lower().replace(" ", "-").replace(":", "-").replace(",", "")
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')

    # Auto-generate content if not provided
    if not content:
        content = f"""# {title}

**Proof of Offline Functionality**

This blog post was created **completely offline** using:

- Python 3
- SQLite database
- Zero internet connection
- No Node.js, no PostgreSQL, no complex dependencies

## How It Works

1. **Database Connection**: Direct SQLite connection to `soulfra.db`
2. **Post Creation**: Called `add_post()` from `database.py`
3. **Timestamp**: Automatic `published_at` using `datetime.now()`
4. **Browser Preview**: Instant viewing at `http://localhost:5001/post/{slug}`

## Why This Matters

You can create content **anywhere**:

- ✅ On a plane (no WiFi)
- ✅ In a coffee shop (sketchy internet)
- ✅ At home (ISP down)
- ✅ On a train (tunnel mode)

**GeeksForGeeks-style learning**: Try it yourself! Run this script and see your post appear.

---

*Created by: `create_blog_post_offline.py`*
*Timestamp: {datetime.now().isoformat()}*
"""

    # Get current timestamp for published_at
    published_at = datetime.now().isoformat()

    print("=" * 60)
    print("OFFLINE BLOG POST CREATOR - PROOF IT WORKS!")
    print("=" * 60)
    print()
    print(f"📝 Title: {title}")
    print(f"🔗 Slug: {slug}")
    print(f"⏰ Published: {published_at}")
    print(f"👤 User ID: {user_id}")
    print()
    print("Creating post... (100% offline, no internet required)")
    print()

    try:
        # Create the post - NO INTERNET REQUIRED!
        post_id = add_post(
            user_id=user_id,
            title=title,
            slug=slug,
            content=content,
            published_at=published_at
        )

        if post_id:
            url = f"http://localhost:5001/post/{slug}"

            # Trigger AI auto-commenting
            try:
                from event_hooks import on_post_created
                on_post_created(post_id)
            except Exception as e:
                print(f"⚠️  AI auto-commenting failed: {e}")

            print("✅ SUCCESS! Post created offline!")
            print()
            print(f"📍 Post ID: {post_id}")
            print(f"🌐 View at: {url}")
            print()
            print("=" * 60)
            print("COPY-PASTE TO BROWSER:")
            print("=" * 60)
            print(url)
            print("=" * 60)
            print()
            print("🎉 PROOF: You just created a blog post with ZERO internet!")
            print()

            # Verify in database
            conn = get_db()
            post = conn.execute(
                'SELECT * FROM posts WHERE id = ?',
                (post_id,)
            ).fetchone()
            conn.close()

            if post:
                print("✅ VERIFIED: Post exists in database")
                print(f"   - ID: {post['id']}")
                print(f"   - Title: {post['title']}")
                print(f"   - Slug: {post['slug']}")
                print(f"   - Published: {post['published_at']}")
                print()

            return {
                'post_id': post_id,
                'slug': slug,
                'url': url,
                'title': title,
                'published_at': published_at
            }
        else:
            print("❌ ERROR: Post creation failed")
            return None

    except sqlite3.IntegrityError as e:
        print(f"❌ ERROR: Slug already exists - {e}")
        print()
        print("💡 TIP: Run again to create a new post with different timestamp")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_tutorial_post():
    """Create a GeeksForGeeks-style tutorial post"""

    title = "Python SQLite Tutorial - Offline Database"
    content = """# Python SQLite Tutorial - Offline Database

## Introduction

SQLite is a **zero-configuration** database that works completely offline. No server setup, no internet, no complex installation.

## Why SQLite?

✅ **Embedded Database**: Runs directly in your application
✅ **No Setup Required**: No server to configure or manage
✅ **Portable**: Single file database (`.db` file)
✅ **Fast**: Optimized for local storage
✅ **Cross-Platform**: Works on Windows, Mac, Linux

## Basic SQLite Operations

### 1. Connect to Database

```python
import sqlite3

# Connect (creates file if doesn't exist)
conn = sqlite3.connect('my_database.db')
```

### 2. Create Table

```python
conn.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        created_at TEXT
    )
''')
conn.commit()
```

### 3. Insert Data

```python
from datetime import datetime

conn.execute(
    'INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)',
    ('My First Post', 'Hello World!', datetime.now().isoformat())
)
conn.commit()
```

### 4. Query Data

```python
cursor = conn.execute('SELECT * FROM posts')
for row in cursor:
    print(row)
```

### 5. Close Connection

```python
conn.close()
```

## Real-World Example: Blog System

This exact pattern powers the blog you're reading right now!

```python
# From database.py
def add_post(user_id, title, slug, content, published_at):
    conn = get_db()
    conn.execute(
        'INSERT INTO posts (user_id, title, slug, content, published_at) VALUES (?, ?, ?, ?, ?)',
        (user_id, title, slug, content, published_at)
    )
    conn.commit()
    return conn.execute('SELECT last_insert_rowid()').fetchone()[0]
```

## Try It Yourself!

Create your own offline blog post:

```bash
python3 create_blog_post_offline.py
```

No internet required. No complex setup. Just Python + SQLite.

## Practice Questions

**Q1**: What happens if you call `sqlite3.connect('test.db')` on a file that doesn't exist?
**A**: SQLite creates the file automatically

**Q2**: Why use `?` placeholders in SQL queries instead of string formatting?
**A**: Prevents SQL injection attacks

**Q3**: What does `AUTOINCREMENT` do on a PRIMARY KEY?
**A**: Automatically generates unique IDs starting from 1

**Q4**: Can you use SQLite without an internet connection?
**A**: Yes! SQLite is completely offline

## Next Steps

- Read the SQLite documentation
- Experiment with different table schemas
- Build your own offline application
- Learn about database indexing for performance

---

**Level**: Beginner
**Time**: 10 minutes
**Prerequisites**: Python basics
**Offline Compatible**: ✅ YES
"""

    return create_offline_post(title=title, content=content)


if __name__ == '__main__':
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  OFFLINE BLOG POST CREATOR - GeeksForGeeks Style          ║")
    print("║  No internet • No Node.js • No PostgreSQL • Just Python   ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Check for command-line arguments
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--tutorial':
            # Create tutorial post
            result = create_tutorial_post()
        else:
            # Custom title from command line
            title = ' '.join(sys.argv[1:])
            result = create_offline_post(title=title)
    else:
        # Default: Create timestamped proof post
        result = create_offline_post()

    if result:
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Copy the URL above")
        print("   2. Paste in your browser")
        print("   3. See your post live!")
        print()
        print("📚 CREATE MORE POSTS:")
        print(f"   python3 {__file__} 'My Custom Title'")
        print(f"   python3 {__file__} --tutorial")
        print()
        sys.exit(0)
    else:
        sys.exit(1)

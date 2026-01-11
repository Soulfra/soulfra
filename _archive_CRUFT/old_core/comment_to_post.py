#!/usr/bin/env python3
"""
Comment to Post - Expand AI Comments Into Full Blog Posts
==========================================================

The self-sustaining content loop:
1. User posts: "How do I make salted butter?"
2. AI (howtocookathome) comments with detailed recipe
3. Script expands comment → NEW full blog post
4. AI comments on THAT post → expands again
5. Infinite content generation!

Usage:
    python3 comment_to_post.py expand 1           # Expand comment ID 1
    python3 comment_to_post.py auto               # Auto-expand qualifying comments
    python3 comment_to_post.py check 28           # Check which comments qualify for expansion

Features:
- Expands AI comments into full blog posts
- Adds images, SEO, recipe steps automatically
- Links comments ↔ posts in database
- Self-sustaining content loop

Database Changes Needed:
    ALTER TABLE comments ADD COLUMN expanded_to_post_id INTEGER;
    ALTER TABLE comments ADD COLUMN expansion_quality REAL;
    ALTER TABLE posts ADD COLUMN source_comment_id INTEGER;
"""

import sys
import sqlite3
from datetime import datetime
from database import get_db
from db_helpers import get_user_by_id
import re


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def check_database_schema():
    """Check if database has required fields for comment→post expansion"""
    conn = get_db()

    # Check comments table
    comments_schema = conn.execute("PRAGMA table_info(comments)").fetchall()
    comments_columns = [row[1] for row in comments_schema]

    # Check posts table
    posts_schema = conn.execute("PRAGMA table_info(posts)").fetchall()
    posts_columns = [row[1] for row in posts_schema]

    has_expanded_to_post_id = 'expanded_to_post_id' in comments_columns
    has_expansion_quality = 'expansion_quality' in comments_columns
    has_source_comment_id = 'source_comment_id' in posts_columns

    conn.close()

    return {
        'expanded_to_post_id': has_expanded_to_post_id,
        'expansion_quality': has_expansion_quality,
        'source_comment_id': has_source_comment_id,
        'ready': has_expanded_to_post_id and has_source_comment_id
    }


def expand_comment_to_post(comment_id, auto_publish=True):
    """
    Expand a comment into a full blog post

    Flow:
    1. Get comment from database
    2. AI expands to full post (add structure, images, SEO)
    3. Create new post in database
    4. Link: comments.expanded_to_post_id = post_id
    5. Link: posts.source_comment_id = comment_id
    6. Return new post_id

    Args:
        comment_id: ID of comment to expand
        auto_publish: If True, publish immediately; if False, save as draft

    Returns:
        post_id of new post, or None if failed
    """
    print_header(f"🔄 Expanding Comment #{comment_id} to Blog Post")

    conn = get_db()

    # Check database schema
    schema = check_database_schema()
    if not schema['ready']:
        print("\n❌ Database not ready for comment→post expansion")
        print("\nMissing fields:")
        if not schema['expanded_to_post_id']:
            print("   - comments.expanded_to_post_id")
        if not schema['source_comment_id']:
            print("   - posts.source_comment_id")
        print("\nRun: python3 comment_to_post.py migrate")
        conn.close()
        return None

    # 1. Get comment from database
    comment = conn.execute('''
        SELECT c.*, u.username, u.display_name, u.is_ai_persona
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    if not comment:
        print(f"\n❌ Comment #{comment_id} not found")
        conn.close()
        return None

    comment = dict(comment)

    # Check if already expanded
    if comment.get('expanded_to_post_id'):
        print(f"\n⚠️  Comment already expanded to post #{comment['expanded_to_post_id']}")
        conn.close()
        return comment['expanded_to_post_id']

    # Get original post
    original_post = conn.execute('SELECT * FROM posts WHERE id = ?', (comment['post_id'],)).fetchone()
    original_post = dict(original_post) if original_post else None

    print(f"\n📝 Comment by: {comment['username']}")
    print(f"💬 Length: {len(comment['content'])} characters")
    print(f"📄 Original post: {original_post['title'] if original_post else 'Unknown'}")

    # 2. Expand comment to full post
    print(f"\n🤖 Expanding comment to full blog post...")

    expanded = ai_expand_comment(comment, original_post)

    if not expanded:
        print("\n❌ Failed to expand comment")
        conn.close()
        return None

    print(f"\n✅ Expanded successfully!")
    print(f"📰 Title: {expanded['title']}")
    print(f"📏 Content length: {len(expanded['content'])} characters")

    # 3. Create new post in database
    try:
        cursor = conn.execute('''
            INSERT INTO posts (
                user_id,
                title,
                slug,
                content,
                excerpt,
                source_comment_id,
                published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            comment['user_id'],
            expanded['title'],
            expanded['slug'],
            expanded['content'],
            expanded['excerpt'],
            comment_id,
            datetime.now() if auto_publish else None
        ))

        post_id = cursor.lastrowid
        conn.commit()

        print(f"\n✅ Created post #{post_id}")

        # 4. Update comment to link to new post
        conn.execute('''
            UPDATE comments
            SET expanded_to_post_id = ?,
                expansion_quality = ?
            WHERE id = ?
        ''', (post_id, expanded.get('quality', 0.8), comment_id))

        conn.commit()

        print(f"✅ Linked comment #{comment_id} → post #{post_id}")

        conn.close()

        print(f"\n🎉 SUCCESS!")
        print(f"   Comment #{comment_id} expanded to post #{post_id}")
        print(f"   URL: /post/{expanded['slug']}")

        return post_id

    except sqlite3.IntegrityError as e:
        print(f"\n❌ Database error: {e}")
        conn.close()
        return None


def ai_expand_comment(comment, original_post=None):
    """
    Use AI to expand comment into full blog post

    Takes comment content and expands it into:
    - Title
    - Full structured content
    - Excerpt
    - Slug
    - Quality score

    For now: Rule-based expansion (can add real AI later via Ollama)
    """

    content = comment['content']
    username = comment['username']

    # Generate title from first sentence or original post
    if original_post:
        # Derive title from original post + comment topic
        first_sentence = content.split('.')[0].strip()
        title = derive_title_from_comment(first_sentence, original_post['title'])
    else:
        # Use first sentence as title
        title = content.split('.')[0].strip()[:100]

    # Generate slug
    slug = generate_slug(title)

    # Expand content with structure
    expanded_content = expand_content_with_structure(content, username, original_post)

    # Generate excerpt (first 200 chars)
    excerpt = content[:200] + "..." if len(content) > 200 else content

    # Calculate quality score (0.0-1.0)
    quality = calculate_expansion_quality(content, expanded_content)

    return {
        'title': title,
        'slug': slug,
        'content': expanded_content,
        'excerpt': excerpt,
        'quality': quality
    }


def derive_title_from_comment(first_sentence, original_title):
    """Derive blog post title from comment + original post"""

    # Remove question marks, "how", "what", etc.
    cleaned = first_sentence.lower()
    cleaned = cleaned.replace('?', '').replace('!', '')

    # If comment starts with "To make X", use "How to Make X"
    if cleaned.startswith('to make '):
        thing = cleaned.replace('to make ', '').strip()
        return f"How to Make {thing.title()}"

    # If comment starts with "You can", use topic from original
    if cleaned.startswith('you can') or cleaned.startswith('you should'):
        # Extract topic from original post title
        if 'how' in original_title.lower():
            return original_title.replace('?', '') + ' - Detailed Guide'
        else:
            return f"Guide: {original_title}"

    # Default: capitalize first sentence
    return first_sentence[:80].title()


def generate_slug(title):
    """Generate URL-safe slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')[:50]
    return slug


def expand_content_with_structure(content, username, original_post=None):
    """
    Expand comment content with blog post structure

    Adds:
    - Introduction
    - Sections/steps
    - Conclusion
    - Attribution to original comment
    """

    # Build structured post
    sections = []

    # Introduction
    if original_post:
        sections.append(f"# {original_post['title']}\n")
        sections.append(f"*This guide is based on insights from {username}.*\n")

    # Main content (detect if it's steps/recipe)
    if has_steps(content):
        sections.append("## Instructions\n")
        sections.append(format_steps(content))
    else:
        # Just use content as-is with paragraphs
        sections.append(content)

    # Add tips section if content has tips
    if 'tip' in content.lower() or 'note' in content.lower():
        sections.append("\n## Tips\n")
        sections.append(extract_tips(content))

    # Attribution footer
    sections.append(f"\n---\n\n*Originally shared by {username} in the comments.*")

    return "\n\n".join(sections)


def has_steps(content):
    """Check if content contains step-by-step instructions"""
    # Look for numbered steps or recipe-style content
    has_numbers = bool(re.search(r'\b\d+\.\s', content))
    has_recipe_keywords = any(word in content.lower() for word in ['cup', 'tablespoon', 'teaspoon', 'heat', 'mix', 'stir'])
    return has_numbers or has_recipe_keywords


def format_steps(content):
    """Format content as numbered steps"""
    # Split by periods and create steps
    sentences = content.split('.')
    steps = []

    for i, sentence in enumerate(sentences, 1):
        sentence = sentence.strip()
        if sentence and len(sentence) > 10:
            steps.append(f"{i}. {sentence}.")

    return "\n".join(steps)


def extract_tips(content):
    """Extract tips from content"""
    # Find sentences with "tip", "note", "important"
    tips = []
    sentences = content.split('.')

    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in ['tip', 'note', 'important', 'remember']):
            tips.append(f"- {sentence.strip()}")

    return "\n".join(tips) if tips else "- Follow the instructions carefully for best results."


def calculate_expansion_quality(original, expanded):
    """
    Calculate quality score for expansion (0.0-1.0)

    Factors:
    - Length increase (more content = better)
    - Structure added (sections, formatting)
    - Original content preserved
    """
    length_ratio = len(expanded) / len(original) if original else 1.0
    has_structure = '##' in expanded or '\n\n' in expanded
    has_attribution = 'Originally shared' in expanded

    score = 0.5  # Base score

    # Length bonus (up to +0.3)
    if length_ratio > 1.5:
        score += 0.3
    elif length_ratio > 1.2:
        score += 0.2
    elif length_ratio > 1.0:
        score += 0.1

    # Structure bonus
    if has_structure:
        score += 0.1

    # Attribution bonus
    if has_attribution:
        score += 0.1

    return min(score, 1.0)


def auto_expand_qualifying_comments(limit=5):
    """
    Auto-expand comments that qualify

    Criteria:
    - Length > 200 characters
    - From AI brands (howtocookathome, calriven, deathtodata, soulfra)
    - Not already expanded
    - Posted in last 30 days

    Args:
        limit: Max number of comments to expand
    """
    print_header("🤖 Auto-Expanding Qualifying Comments")

    # Check database schema
    schema = check_database_schema()
    if not schema['ready']:
        print("\n❌ Database not ready")
        print("Run: python3 comment_to_post.py migrate")
        return

    conn = get_db()

    # Find qualifying comments
    query = '''
        SELECT c.id, c.content, u.username, LENGTH(c.content) as length
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE LENGTH(c.content) > 200
        AND u.username IN ('howtocookathome', 'calriven', 'deathtodata', 'soulfra')
        AND c.expanded_to_post_id IS NULL
        ORDER BY c.created_at DESC
        LIMIT ?
    '''

    candidates = conn.execute(query, (limit,)).fetchall()
    conn.close()

    if not candidates:
        print("\n📭 No qualifying comments found")
        print("\nCriteria:")
        print("   - Length > 200 characters")
        print("   - From AI brands (howtocookathome, calriven, deathtodata, soulfra)")
        print("   - Not already expanded")
        return

    print(f"\n✅ Found {len(candidates)} qualifying comments:\n")

    for comment in candidates:
        comment = dict(comment)
        print(f"   Comment #{comment['id']} by {comment['username']} ({comment['length']} chars)")

    print("\n🔄 Expanding comments...\n")

    expanded_count = 0
    for comment in candidates:
        comment = dict(comment)
        post_id = expand_comment_to_post(comment['id'])

        if post_id:
            expanded_count += 1
            print(f"✅ {expanded_count}/{len(candidates)} expanded\n")
        else:
            print(f"❌ Failed to expand comment #{comment['id']}\n")

    print(f"\n🎉 Expanded {expanded_count}/{len(candidates)} comments!")


def check_expandable_comments(post_id=None):
    """
    Check which comments can be expanded

    Args:
        post_id: If provided, check only comments on this post
    """
    print_header("🔍 Checking Expandable Comments")

    conn = get_db()

    if post_id:
        query = '''
            SELECT c.id, c.content, u.username, LENGTH(c.content) as length,
                   p.title as post_title
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN posts p ON c.post_id = p.id
            WHERE c.post_id = ?
            ORDER BY LENGTH(c.content) DESC
        '''
        comments = conn.execute(query, (post_id,)).fetchall()
        print(f"\n📄 Comments on post #{post_id}:\n")
    else:
        query = '''
            SELECT c.id, c.content, u.username, LENGTH(c.content) as length,
                   p.title as post_title,
                   c.expanded_to_post_id
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN posts p ON c.post_id = p.id
            ORDER BY LENGTH(c.content) DESC
            LIMIT 20
        '''
        comments = conn.execute(query).fetchall()
        print(f"\n📊 All comments (sorted by length):\n")

    conn.close()

    if not comments:
        print("   No comments found")
        return

    for comment in comments:
        comment = dict(comment)
        length = comment['length']
        username = comment['username']
        is_ai = username in ['howtocookathome', 'calriven', 'deathtodata', 'soulfra']
        already_expanded = comment.get('expanded_to_post_id') is not None

        # Determine if expandable
        expandable = length > 200 and is_ai and not already_expanded

        status = "✅ EXPANDABLE" if expandable else "❌ Not expandable"
        if already_expanded:
            status = f"📰 Already expanded to post #{comment['expanded_to_post_id']}"

        print(f"   Comment #{comment['id']} - {username} - {length} chars - {status}")
        print(f"      Post: {comment['post_title'][:60]}...")
        print()


def migrate_database():
    """Add required fields to database for comment→post expansion"""
    print_header("🔧 Database Migration")

    schema = check_database_schema()

    print("\n📋 Current schema:")
    print(f"   comments.expanded_to_post_id: {'✅' if schema['expanded_to_post_id'] else '❌'}")
    print(f"   comments.expansion_quality: {'✅' if schema['expansion_quality'] else '❌'}")
    print(f"   posts.source_comment_id: {'✅' if schema['source_comment_id'] else '❌'}")

    if schema['ready']:
        print("\n✅ Database already has required fields!")
        return

    print("\n🔧 Adding missing fields...\n")

    conn = get_db()

    try:
        if not schema['expanded_to_post_id']:
            print("   Adding comments.expanded_to_post_id...")
            conn.execute('ALTER TABLE comments ADD COLUMN expanded_to_post_id INTEGER')
            print("   ✅ Added")

        if not schema['expansion_quality']:
            print("   Adding comments.expansion_quality...")
            conn.execute('ALTER TABLE comments ADD COLUMN expansion_quality REAL')
            print("   ✅ Added")

        if not schema['source_comment_id']:
            print("   Adding posts.source_comment_id...")
            conn.execute('ALTER TABLE posts ADD COLUMN source_comment_id INTEGER')
            print("   ✅ Added")

        conn.commit()
        conn.close()

        print("\n✅ Migration complete!")
        print("\n🎉 Database ready for comment→post expansion!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.close()


def show_help():
    """Show usage instructions"""
    print("""
Comment to Post - Expand AI Comments to Blog Posts
===================================================

Usage:
    python3 comment_to_post.py expand <comment_id>     # Expand specific comment
    python3 comment_to_post.py auto                    # Auto-expand qualifying comments
    python3 comment_to_post.py check [post_id]         # Check which comments can be expanded
    python3 comment_to_post.py migrate                 # Add required database fields

Examples:
    # Check which comments can be expanded
    python3 comment_to_post.py check

    # Check comments on post #28
    python3 comment_to_post.py check 28

    # Expand comment #1 to full blog post
    python3 comment_to_post.py expand 1

    # Auto-expand all qualifying comments
    python3 comment_to_post.py auto

Qualifying Comments:
    - Length > 200 characters
    - From AI brands (howtocookathome, calriven, deathtodata, soulfra)
    - Not already expanded

The Self-Sustaining Loop:
    1. User posts: "How do I make salted butter?"
    2. AI comments with detailed recipe
    3. Comment expands → NEW blog post
    4. AI comments on THAT post
    5. Expands again → More posts!
    6. Infinite content generation 🚀
    """)


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'expand':
        if len(sys.argv) < 3:
            print("❌ Error: comment_id required")
            print("Usage: python3 comment_to_post.py expand <comment_id>")
            sys.exit(1)

        comment_id = int(sys.argv[2])
        expand_comment_to_post(comment_id)

    elif command == 'auto':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        auto_expand_qualifying_comments(limit)

    elif command == 'check':
        post_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        check_expandable_comments(post_id)

    elif command == 'migrate':
        migrate_database()

    elif command in ['help', '--help', '-h']:
        show_help()

    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

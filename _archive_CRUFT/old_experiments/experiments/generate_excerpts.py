#!/usr/bin/env python3
"""
Generate Excerpts for Existing Posts

Automatically creates excerpts from post content:
- First paragraph (if short enough)
- OR first 200 characters
- Strips markdown formatting
- Adds "..." if truncated
"""

import re
from database import get_db


def strip_markdown(text):
    """Remove markdown and HTML formatting from text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove links
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def get_first_paragraph(text):
    """Get first paragraph from text"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return paragraphs[0] if paragraphs else text


def generate_excerpt(content, max_length=200):
    """
    Generate excerpt from content

    Args:
        content: Full post content (markdown)
        max_length: Maximum excerpt length

    Returns:
        str: Excerpt text
    """
    # Strip markdown
    clean_text = strip_markdown(content)

    # Get first paragraph
    first_para = get_first_paragraph(clean_text)

    # If first paragraph is short enough, use it
    if len(first_para) <= max_length:
        return first_para

    # Otherwise truncate at word boundary
    if len(clean_text) <= max_length:
        return clean_text

    # Truncate at last complete word before max_length
    truncated = clean_text[:max_length]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + "..."


def generate_all_excerpts():
    """Generate excerpts for all posts"""
    db = get_db()

    # Get all posts
    posts = db.execute('SELECT id, title, content FROM posts').fetchall()

    print(f"📝 Generating excerpts for {len(posts)} posts...\n")

    updated = 0

    for post in posts:
        post_id = post['id']
        title = post['title']
        content = post['content']

        # Generate excerpt
        excerpt = generate_excerpt(content)

        # Update database
        db.execute('UPDATE posts SET excerpt = ? WHERE id = ?', (excerpt, post_id))

        print(f"✅ {title}")
        print(f"   {excerpt[:80]}...")
        print()

        updated += 1

    db.commit()
    db.close()

    print(f"\n📊 Generated excerpts for {updated} posts")
    print("✅ Posts now have preview text for homepage!")


if __name__ == '__main__':
    print("=" * 70)
    print("🔧 Generating Post Excerpts")
    print("=" * 70)
    print()
    generate_all_excerpts()

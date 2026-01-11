#!/usr/bin/env python3
"""
Chat Compiler - Turn Homework into Blog Posts

Reads your Ollama chat conversations and compiles them into blog posts.
Your learning conversations become published content automatically!

Workflow:
1. Read messages from database
2. Group by topic/date
3. Generate blog post from conversation
4. Save as draft in posts table
5. Newsletter picks them up

Usage:
    python3 compile_chats.py                  # Compile all uncompiled chats
    python3 compile_chats.py --last-week      # Only last 7 days
    python3 compile_chats.py --topic "Neural Networks"  # Specific topic
    python3 compile_chats.py --preview        # Show what would be compiled

The "Homework → Blog" Pipeline:
- Chat about learning → Stored
- Run compiler → Draft post created
- Review/edit → Publish
- Newsletter → Shares your learning
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re


def get_conversations(days_back=None, topic=None):
    """
    Get chat conversations from database

    Args:
        days_back: Only get conversations from last N days
        topic: Filter by topic (searches message content)

    Returns:
        list: Conversations grouped by date
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    query = '''
        SELECT
            m.id,
            m.content,
            m.created_at,
            u.username,
            DATE(m.created_at) as chat_date
        FROM messages m
        JOIN users u ON m.from_user_id = u.id
        WHERE (m.from_user_id IN (SELECT id FROM users WHERE username IN ('admin', 'ollama'))
           OR m.to_user_id IN (SELECT id FROM users WHERE username IN ('admin', 'ollama')))
    '''

    params = []

    if days_back:
        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()
        query += ' AND m.created_at > ?'
        params.append(cutoff)

    if topic:
        query += ' AND m.content LIKE ?'
        params.append(f'%{topic}%')

    query += ' ORDER BY m.created_at'

    cursor.execute(query, params)
    messages = cursor.fetchall()
    conn.close()

    # Group by date
    conversations = defaultdict(list)
    for msg in messages:
        conversations[msg['chat_date']].append(dict(msg))

    return dict(conversations)


def extract_topic_from_conversation(messages):
    """
    Extract topic from conversation

    Uses first user question + keywords to determine topic

    Args:
        messages: List of message dicts

    Returns:
        str: Topic name
    """
    if not messages:
        return "General Discussion"

    # Get first user message
    first_user_msg = next((m for m in messages if m['username'] != 'ollama'), None)

    if not first_user_msg:
        return "General Discussion"

    # Simple keyword extraction
    content = first_user_msg['content'].lower()

    # Common topic patterns
    if 'neural network' in content or 'machine learning' in content or 'ml' in content:
        return "Machine Learning"
    elif 'qr code' in content or 'barcode' in content or 'upc' in content:
        return "Barcodes & QR Codes"
    elif 'ip address' in content or 'network' in content or 'dns' in content:
        return "Networking"
    elif 'gps' in content or 'location' in content or 'coordinates' in content:
        return "Location & GPS"
    elif 'database' in content or 'sql' in content or 'sqlite' in content:
        return "Database"
    elif 'newsletter' in content or 'email' in content or 'smtp' in content:
        return "Newsletters & Email"
    elif 'python' in content or 'code' in content or 'programming' in content:
        return "Programming"
    else:
        # Use first few words of question
        words = content.split()[:5]
        return ' '.join(words).title()


def format_conversation_as_post(date, messages):
    """
    Format conversation as blog post

    Args:
        date: Date string
        messages: List of message dicts

    Returns:
        dict: Post data
    """
    topic = extract_topic_from_conversation(messages)

    # Build conversation transcript
    transcript_parts = []
    for msg in messages:
        sender = "**You:**" if msg['username'] != 'ollama' else "**Ollama:**"
        transcript_parts.append(f"{sender} {msg['content']}")

    transcript = "\n\n".join(transcript_parts)

    # Extract key points (find questions)
    questions = [m['content'] for m in messages if m['username'] != 'ollama']

    # Generate post content
    content = f"""# Learning Session: {topic}

*Conversation from {date}*

---

## What I Asked

"""

    for i, q in enumerate(questions[:5], 1):
        content += f"{i}. {q}\n"

    content += f"""

---

## Full Conversation

{transcript}

---

## Key Takeaways

*(Add your notes here after reviewing)*

-
-
-

---

*This post was auto-compiled from a learning conversation with Ollama. Part of the "homework becomes blog" system.*
"""

    # Create slug
    slug_base = topic.lower().replace(' ', '-').replace('&', 'and')
    slug = f"learning-{slug_base}-{date}"

    return {
        'title': f"Learning: {topic}",
        'slug': slug,
        'content': content,
        'date': date,
        'topic': topic,
        'message_count': len(messages)
    }


def check_already_compiled(date):
    """Check if conversation from this date was already compiled"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM posts
        WHERE slug LIKE ?
    ''', (f'%{date}%',))

    count = cursor.fetchone()[0]
    conn.close()

    return count > 0


def save_post_draft(post_data, user_id):
    """Save compiled post as draft"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO posts (user_id, title, slug, content, created_at, published_at, emailed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        post_data['title'],
        post_data['slug'],
        post_data['content'],
        datetime.now().isoformat(),
        None,  # Draft - not published yet
        0
    ))

    post_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return post_id


def compile_chats(days_back=None, topic=None, preview=False):
    """
    Main compilation function

    Args:
        days_back: Only compile last N days
        topic: Filter by topic
        preview: Don't save, just show what would be compiled
    """
    print("="*70)
    print("📚 Chat Compiler - Homework → Blog Posts")
    print("="*70)
    print()

    # Get conversations
    print("STEP 1: Loading conversations...")
    conversations = get_conversations(days_back=days_back, topic=topic)

    if not conversations:
        print("❌ No conversations found")
        print()
        print("Start chatting: python3 ollama_chat.py")
        return

    print(f"✅ Found {len(conversations)} conversation sessions")
    print()

    # Compile each conversation
    print("STEP 2: Compiling into blog posts...")
    print()

    compiled_posts = []

    for date, messages in sorted(conversations.items()):
        print(f"📅 {date}:")
        print(f"   Messages: {len(messages)}")

        # Check if already compiled
        if not preview and check_already_compiled(date):
            print(f"   ⏭️  Already compiled - skipping")
            print()
            continue

        # Compile to post
        post_data = format_conversation_as_post(date, messages)

        print(f"   Topic: {post_data['topic']}")
        print(f"   Title: {post_data['title']}")
        print(f"   Slug: {post_data['slug']}")

        if preview:
            print(f"   📄 Preview:")
            print()
            print(post_data['content'][:300] + "...")
            print()
        else:
            # Save as draft
            conn = sqlite3.connect('soulfra.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            user_id = cursor.fetchone()[0]
            conn.close()

            post_id = save_post_draft(post_data, user_id)
            print(f"   ✅ Saved as draft (Post ID: {post_id})")
            print()

        compiled_posts.append(post_data)

    # Summary
    print("="*70)
    print("✅ COMPILATION COMPLETE")
    print("="*70)
    print()
    print(f"📊 Summary:")
    print(f"   Conversations: {len(conversations)}")
    print(f"   Posts compiled: {len(compiled_posts)}")
    print()

    if not preview:
        print("💡 Next steps:")
        print("  • Review draft posts at http://localhost:5001/admin")
        print("  • Publish when ready")
        print("  • Run: python3 newsletter_digest.py")
        print("    To include in weekly newsletter")
    else:
        print("This was a PREVIEW. Run without --preview to actually save.")

    print()

    return compiled_posts


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Compile chat conversations into blog posts')
    parser.add_argument('--last-week', action='store_true', help='Only compile last 7 days')
    parser.add_argument('--last-month', action='store_true', help='Only compile last 30 days')
    parser.add_argument('--topic', type=str, help='Filter by topic keyword')
    parser.add_argument('--preview', action='store_true', help='Preview without saving')

    args = parser.parse_args()

    days_back = None
    if args.last_week:
        days_back = 7
    elif args.last_month:
        days_back = 30

    compile_chats(
        days_back=days_back,
        topic=args.topic,
        preview=args.preview
    )


if __name__ == '__main__':
    main()

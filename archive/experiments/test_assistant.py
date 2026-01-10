#!/usr/bin/env python3
"""
Soul Assistant "Hello World" Demo

This script demonstrates the full AI assistant workflow:
1. Creates a discussion session on a post
2. Sends commands (/qr, /research, /neural predict)
3. Has a natural language chat conversation
4. Posts a final comment as the Soul Assistant

Pure Python stdlib - no external dependencies (except Flask/SQLite already in use)
"""

import sqlite3
import json
from datetime import datetime


def get_first_post():
    """Get the first post from the database"""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    post = db.execute('SELECT * FROM posts LIMIT 1').fetchone()
    db.close()
    return dict(post) if post else None


def demo():
    print("🤖 Soul Assistant 'Hello World' Demo")
    print("=" * 70)
    print()

    # Import the assistant
    from soulfra_assistant import SoulAssistant

    # Get a post to discuss
    post = get_first_post()
    if not post:
        print("❌ No posts found in database. Create a post first!")
        return

    print(f"📝 Discussing post: {post['title']}")
    print(f"   Post ID: {post['id']}")
    print()

    # Create assistant with post context
    assistant = SoulAssistant(
        user_id=14,  # SoulAssistant user ID
        context={
            'post_id': post['id'],
            'post': post,
            'url': f"/post/{post['slug']}"
        }
    )

    print(f"✅ Created discussion session: {assistant.session_id}")
    print()

    # Test commands
    tests = [
        ("QR Code Generation", "/qr Test QR Code"),
        ("Research", "/research platform"),
        ("Neural Network", "/neural status"),
        ("Natural Language", "What are the main topics in this post?"),
    ]

    for test_name, message in tests:
        print(f"🔹 Test: {test_name}")
        print(f"   Input: {message}")

        result = assistant.handle_message(message)

        if result.get('success'):
            print(f"   ✅ {result.get('response')[:100]}...")
        else:
            print(f"   ❌ {result.get('response')}")

        print()

    # View conversation history
    print("📜 Conversation History:")
    history = assistant.get_conversation_history()
    for i, msg in enumerate(history, 1):
        sender = msg['sender'].upper()
        content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"   {i}. [{sender}] {content}")
    print()

    # Post a final comment
    final_comment = f"""Hello! I'm the Soul Assistant, and I've been analyzing this post.

I ran several tests:
✅ QR code generation
✅ Research across the platform
✅ Neural network status check
✅ Natural language understanding

This is a demonstration of the AI assistant's ability to interact with all system capabilities through commands and conversation, then post a real comment to the blog.

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session ID: {assistant.session_id}
"""

    print("💬 Posting final comment...")
    comment_result = assistant.post_comment(final_comment)

    if comment_result.get('success'):
        comment_id = comment_result['comment_id']
        print(f"   ✅ Comment posted! ID: {comment_id}")
        print(f"   View at: http://localhost:5001/post/{post['slug']}#{comment_id}")
    else:
        print(f"   ❌ Failed: {comment_result.get('error')}")

    print()
    print("=" * 70)
    print("✅ Demo complete!")
    print()
    print("The Soul Assistant:")
    print("  - Created a persistent discussion session")
    print("  - Saved all messages to the database")
    print("  - Executed commands (QR, research, neural)")
    print("  - Posted a real comment to the blog")
    print()
    print("🔍 Check the database:")
    print(f"   SELECT * FROM discussion_sessions WHERE id = {assistant.session_id};")
    print(f"   SELECT * FROM discussion_messages WHERE session_id = {assistant.session_id};")
    print(f"   SELECT * FROM comments WHERE user_id = 14;")


if __name__ == '__main__':
    demo()

#!/usr/bin/env python3
"""
Ollama Auto-Commenter - AI Comment Generation Engine

Generates contextual comments from brand AI personas using Ollama.

This is the FINAL piece that wires everything together:
1. Brand AI Persona Generator → Creates AI users
2. Brand AI Orchestrator → Selects which AIs should comment
3. **Ollama Auto-Commenter** → Actually generates the comments! ✨

Usage:
    from ollama_auto_commenter import generate_ai_comment

    # Generate single comment
    comment_id = generate_ai_comment(
        brand_slug='ocean-dreams',
        post_id=42
    )

    # Generate comments for all selected AIs
    from brand_ai_orchestrator import orchestrate_brand_comments
    selected = orchestrate_brand_comments(post_id=42)
    for brand in selected:
        generate_ai_comment(brand['brand_slug'], post_id=42)
"""

import urllib.request
import urllib.error
import json
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db
from brand_ai_persona_generator import get_brand_ai_persona_config


# ==============================================================================
# OLLAMA API CONFIGURATION
# ==============================================================================

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"  # Fast, lightweight model for comments


# ==============================================================================
# OLLAMA API INTERFACE
# ==============================================================================

def call_ollama_api(system_prompt: str, user_prompt: str, model: str = OLLAMA_MODEL) -> Optional[str]:
    """
    Call Ollama API to generate text

    Args:
        system_prompt: System instructions (persona definition)
        user_prompt: User request (post content + instructions)
        model: Ollama model to use

    Returns:
        Generated text or None if error
    """
    # Prepare request
    request_data = {
        "model": model,
        "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}",
        "stream": False
    }

    try:
        # Make request
        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=json.dumps(request_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()

    except urllib.error.URLError as e:
        print(f"❌ Ollama API error: {e}")
        print(f"   Make sure Ollama is running: ollama serve")
        return None

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


# ==============================================================================
# COMMENT GENERATION
# ==============================================================================

def build_comment_prompt(post_title: str, post_content: str, brand_name: str) -> str:
    """
    Build the prompt for generating a comment

    Args:
        post_title: Post title
        post_content: Post content
        brand_name: AI persona brand name

    Returns:
        Formatted prompt for Ollama
    """
    prompt = f"""You are commenting on this post:

Title: {post_title}

Content:
{post_content[:500]}{"..." if len(post_content) > 500 else ""}

Generate a thoughtful comment from the perspective of {brand_name}. Your comment should:
1. Be 2-3 paragraphs (150-250 words)
2. Stay true to your personality and tone
3. Provide constructive feedback or ask thoughtful questions
4. Add value to the conversation
5. Sound natural and authentic
6. Avoid generic praise - be specific

Do not include any preamble like "Here's my comment:" - just write the comment directly.

Comment:"""

    return prompt


def generate_ai_comment(brand_slug: str, post_id: int, dry_run: bool = False) -> Optional[int]:
    """
    Generate and post an AI comment

    Args:
        brand_slug: Brand slug (e.g., 'ocean-dreams')
        post_id: Post ID to comment on
        dry_run: If True, generate comment but don't post to database

    Returns:
        Comment ID or None if failed

    Process:
    1. Load AI persona config (system prompt)
    2. Load post content
    3. Build comment prompt
    4. Call Ollama API
    5. Post-process comment
    6. Store in database
    """
    # Get AI persona config
    persona = get_brand_ai_persona_config(brand_slug)
    if not persona:
        print(f"❌ AI persona '{brand_slug}' not found")
        return None

    # Get post
    db = get_db()
    post = db.execute('''
        SELECT id, title, content FROM posts WHERE id = ?
    ''', (post_id,)).fetchone()

    if not post:
        db.close()
        print(f"❌ Post {post_id} not found")
        return None

    post_dict = dict(post)

    # Check if this AI has already commented on this post
    existing = db.execute('''
        SELECT id FROM comments
        WHERE post_id = ? AND user_id = ?
    ''', (post_id, persona['user_id'])).fetchone()

    if existing:
        db.close()
        print(f"⚠️  {persona['display_name']} has already commented on post {post_id}")
        return existing['id']

    # Build comment prompt
    user_prompt = build_comment_prompt(
        post_dict['title'],
        post_dict['content'],
        persona['brand_name']
    )

    # Generate comment using Ollama
    print(f"🤖 Generating comment from {persona['display_name']} ({persona['emoji']})...")

    generated_text = call_ollama_api(
        system_prompt=persona['system_prompt'],
        user_prompt=user_prompt
    )

    if not generated_text:
        db.close()
        print(f"❌ Failed to generate comment")
        return None

    # Post-process comment
    comment_text = generated_text.strip()

    # Remove common AI preambles if present
    preambles_to_remove = [
        "Here's my comment:",
        "Here is my comment:",
        "Comment:",
        "My comment:",
        "Here's what I think:"
    ]

    for preamble in preambles_to_remove:
        if comment_text.startswith(preamble):
            comment_text = comment_text[len(preamble):].strip()

    # Ensure reasonable length
    if len(comment_text) < 50:
        db.close()
        print(f"❌ Generated comment too short ({len(comment_text)} chars)")
        return None

    if len(comment_text) > 1000:
        # Truncate to last complete sentence before 1000 chars
        comment_text = comment_text[:1000]
        last_period = comment_text.rfind('.')
        if last_period > 500:  # Don't truncate too aggressively
            comment_text = comment_text[:last_period + 1]

    # Print preview
    preview = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
    print(f"✅ Generated comment ({len(comment_text)} chars): {preview}")

    if dry_run:
        db.close()
        print(f"🔍 DRY RUN - Comment NOT posted to database")
        print()
        print("=" * 70)
        print(f"FULL COMMENT FROM {persona['display_name']}:")
        print("=" * 70)
        print(comment_text)
        print("=" * 70)
        return None

    # Store comment in database
    db.execute('''
        INSERT INTO comments (post_id, user_id, content, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        post_id,
        persona['user_id'],
        comment_text,
        datetime.now().isoformat()
    ))

    db.commit()
    comment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    db.close()

    print(f"✅ Comment posted! ID={comment_id}")

    return comment_id


def generate_comments_for_post(post_id: int, dry_run: bool = False) -> List[int]:
    """
    Generate AI comments for a post using orchestration

    Args:
        post_id: Post ID
        dry_run: If True, generate but don't post

    Returns:
        List of comment IDs

    Process:
    1. Use orchestrator to select which AIs should comment
    2. Generate comment from each selected AI
    3. Return list of comment IDs
    """
    from brand_ai_orchestrator import orchestrate_brand_comments

    print()
    print("=" * 70)
    print(f"🎭 GENERATING AI COMMENTS FOR POST {post_id}")
    print("=" * 70)
    print()

    # Get selected brands
    selected_brands = orchestrate_brand_comments(post_id, dry_run=False)

    if not selected_brands:
        print("ℹ️  No AI personas selected for this post")
        return []

    print(f"📋 Selected {len(selected_brands)} AI persona(s):")
    for i, brand in enumerate(selected_brands, 1):
        print(f"   {i}. {brand['brand_name']} (relevance={brand['relevance']:.2f})")
    print()

    # Generate comments
    comment_ids = []

    for brand_info in selected_brands:
        comment_id = generate_ai_comment(
            brand_slug=brand_info['brand_slug'],
            post_id=post_id,
            dry_run=dry_run
        )

        if comment_id:
            comment_ids.append(comment_id)

        print()  # Spacing

    print("=" * 70)
    print(f"✅ Generated {len(comment_ids)} comment(s)")
    print("=" * 70)
    print()

    return comment_ids


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """CLI for Ollama auto-commenter"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ollama_auto_commenter.py comment <brand_slug> <post_id> [--dry-run]")
        print("  python3 ollama_auto_commenter.py auto <post_id> [--dry-run]")
        print()
        print("Examples:")
        print("  python3 ollama_auto_commenter.py comment ocean-dreams 42")
        print("  python3 ollama_auto_commenter.py auto 42")
        print("  python3 ollama_auto_commenter.py auto 42 --dry-run")
        return

    command = sys.argv[1]

    if command == 'comment':
        if len(sys.argv) < 4:
            print("Error: Missing arguments")
            print("Usage: python3 ollama_auto_commenter.py comment <brand_slug> <post_id> [--dry-run]")
            return

        brand_slug = sys.argv[2]
        post_id = int(sys.argv[3])
        dry_run = '--dry-run' in sys.argv

        comment_id = generate_ai_comment(brand_slug, post_id, dry_run=dry_run)

        if comment_id:
            print()
            print(f"✅ Success! Comment ID: {comment_id}")
        else:
            print()
            print("❌ Failed to generate comment")

    elif command == 'auto':
        if len(sys.argv) < 3:
            print("Error: Missing post ID")
            print("Usage: python3 ollama_auto_commenter.py auto <post_id> [--dry-run]")
            return

        post_id = int(sys.argv[2])
        dry_run = '--dry-run' in sys.argv

        comment_ids = generate_comments_for_post(post_id, dry_run=dry_run)

        if comment_ids:
            print()
            print(f"✅ Success! Generated {len(comment_ids)} comments")
        else:
            print()
            print("⚠️  No comments generated")

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Cal Auto-Publisher - Voice → Cal → GitHub

Simple workflow:
1. Get voice recording from database
2. Send transcript to Cal (Ollama)
3. Cal generates blog post
4. Save to calriven repo
5. Push to GitHub
6. Auto-deploys via GitHub Pages

Usage:
    python3 cal_auto_publish.py --recording-id 123
    python3 cal_auto_publish.py --prompt "Write about AI"
"""

import argparse
import requests
import json
import os
import subprocess
from datetime import datetime
from database import get_db


def get_cal_response(prompt, model="llama3.2:latest"):
    """
    Send prompt to Cal/Ollama and get response (with auto-fallback)

    Args:
        prompt: Text to send to Cal
        model: Ollama model to use

    Returns:
        str: Cal's response
    """
    # ✅ FIXED: Use smart client with auto-fallback (localhost → remote → mock)
    try:
        from ollama_smart_client import ask_ollama
        return ask_ollama(prompt, model=model, use_soul=True)
    except Exception as e:
        print(f"❌ Error getting Cal response: {e}")
        return f"Error generating content: {e}"


def create_blog_post(title, content, author="Cal"):
    """
    Create blog post file in calriven repo

    Args:
        title: Post title
        content: Post content (markdown)
        author: Author name

    Returns:
        str: Path to created file
    """
    # Generate slug from title
    slug = title.lower().replace(' ', '-').replace('/', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')

    # Create filename with date
    date = datetime.now().strftime('%Y-%m-%d')
    filename = f"{date}-{slug}.md"

    # Full path to calriven repo
    repo_path = os.path.expanduser('~/Desktop/calriven')
    posts_dir = os.path.join(repo_path, 'posts')

    # Create posts directory if it doesn't exist
    os.makedirs(posts_dir, exist_ok=True)

    # Create blog post with frontmatter
    post_content = f"""---
title: {title}
date: {datetime.now().isoformat()}
author: {author}
tags: [ai, automation, cal]
---

{content}
"""

    # Write file
    filepath = os.path.join(posts_dir, filename)
    with open(filepath, 'w') as f:
        f.write(post_content)

    return filepath


def push_to_github(filepath, commit_message="🤖 Cal auto-publish"):
    """
    Push changes to GitHub

    Args:
        filepath: Path to file to commit
        commit_message: Git commit message

    Returns:
        bool: Success status
    """
    repo_path = os.path.expanduser('~/Desktop/calriven')

    try:
        # Git add
        subprocess.run(['git', 'add', filepath], cwd=repo_path, check=True)

        # Git commit
        subprocess.run([
            'git', 'commit', '-m',
            f"{commit_message}\n\n🤖 Generated with Cal\nCo-Authored-By: Cal <cal@soulfra.com>"
        ], cwd=repo_path, check=True)

        # Git push
        subprocess.run(['git', 'push'], cwd=repo_path, check=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False


def publish_from_recording(recording_id):
    """
    Publish blog post from voice recording

    Args:
        recording_id: ID from simple_voice_recordings table
    """
    db = get_db()

    # Get recording
    recording = db.execute('''
        SELECT id, transcript, ai_analysis, created_at
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        print(f"❌ Recording {recording_id} not found")
        return

    if not recording['transcript']:
        print(f"❌ Recording {recording_id} has no transcript")
        return

    print(f"📝 Found recording: {recording['transcript'][:100]}...")

    # Generate blog post with Cal
    prompt = f"""You are Cal, an AI writing assistant. Convert this voice memo into a blog post.

Voice memo:
{recording['transcript']}

Write a complete blog post with:
1. A catchy title
2. Introduction
3. Main content (3-5 paragraphs)
4. Conclusion

Format in Markdown. Start with # Title.
"""

    print("🤖 Asking Cal to write blog post...")
    response = get_cal_response(prompt)

    # Extract title (first line starting with #)
    lines = response.split('\n')
    title = None
    content_start = 0

    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            content_start = i + 1
            break

    if not title:
        title = f"Voice Memo {recording_id}"
        content = response
    else:
        content = '\n'.join(lines[content_start:]).strip()

    print(f"✍️  Cal wrote: {title}")

    # Create blog post file
    filepath = create_blog_post(title, content)
    print(f"📄 Created: {filepath}")

    # Push to GitHub
    print("🚀 Pushing to GitHub...")
    if push_to_github(filepath, f"📝 {title}"):
        print("✅ Published to GitHub!")
        print(f"🌐 Will be live at: https://soulfra.github.io/calriven/posts/{os.path.basename(filepath).replace('.md', '.html')}")
    else:
        print("❌ Failed to push to GitHub")


def publish_from_prompt(prompt):
    """
    Publish blog post from text prompt

    Args:
        prompt: What to write about
    """
    print(f"🤖 Asking Cal to write about: {prompt}")

    cal_prompt = f"""You are Cal, an AI writing assistant. Write a blog post about: {prompt}

Write a complete blog post with:
1. A catchy title
2. Introduction
3. Main content (3-5 paragraphs)
4. Conclusion

Format in Markdown. Start with # Title.
"""

    response = get_cal_response(cal_prompt)

    # Extract title
    lines = response.split('\n')
    title = None
    content_start = 0

    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            content_start = i + 1
            break

    if not title:
        title = prompt[:50]
        content = response
    else:
        content = '\n'.join(lines[content_start:]).strip()

    print(f"✍️  Cal wrote: {title}")

    # Create blog post file
    filepath = create_blog_post(title, content)
    print(f"📄 Created: {filepath}")

    # Push to GitHub
    print("🚀 Pushing to GitHub...")
    if push_to_github(filepath, f"📝 {title}"):
        print("✅ Published to GitHub!")
        print(f"🌐 Will be live at: https://soulfra.github.io/calriven/")
    else:
        print("❌ Failed to push to GitHub")


def main():
    parser = argparse.ArgumentParser(description='Cal Auto-Publisher')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--recording-id', type=int, help='Voice recording ID')
    group.add_argument('--prompt', type=str, help='Text prompt for Cal')

    args = parser.parse_args()

    if args.recording_id:
        publish_from_recording(args.recording_id)
    elif args.prompt:
        publish_from_prompt(args.prompt)


if __name__ == '__main__':
    main()

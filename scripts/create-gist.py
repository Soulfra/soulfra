#!/usr/bin/env python3
"""
Create GitHub Gist - Automate gist creation from voice memos

This integrates with Flask backend to automatically create gists
when voice memos are uploaded from iPhone.

Usage:
    python3 create-gist.py --file voice-memo.json --description "iPhone recording"

Or from Flask:
    from scripts.create_gist import create_gist
    gist_url = create_gist(filename, content, description)
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timezone

# GitHub API configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'Soulfra')

def create_gist(filename, content, description, public=True):
    """
    Create a GitHub gist via API

    Args:
        filename (str): Name of the file in the gist
        content (str): Content of the file
        description (str): Description of the gist
        public (bool): Whether gist should be public

    Returns:
        dict: Gist response with 'html_url', 'id', etc.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    url = 'https://api.github.com/gists'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    data = {
        'description': description,
        'public': public,
        'files': {
            filename: {
                'content': content
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create gist: {response.status_code} - {response.text}")

def create_voice_memo_gist(voice_memo_data):
    """
    Create gist for voice memo metadata

    Args:
        voice_memo_data (dict): Voice memo metadata

    Returns:
        str: Gist HTML URL
    """
    # Generate filename
    timestamp = voice_memo_data.get('timestamp', datetime.now(timezone.utc).isoformat())
    filename = f"voice-memo-{timestamp[:10]}.json"

    # Format content
    content = json.dumps(voice_memo_data, indent=2)

    # Description
    title = voice_memo_data.get('title', 'Voice Memo')
    description = f"{title} - Recorded from iPhone via CringeProof"

    # Create gist
    gist = create_gist(filename, content, description, public=True)

    return gist['html_url']

def embed_gist_in_readme(gist_id, readme_path='../README.md'):
    """
    Add gist embed to README.md

    Args:
        gist_id (str): Gist ID (not full URL)
        readme_path (str): Path to README.md
    """
    embed_code = f'<script src="https://gist.github.com/{GITHUB_USERNAME}/{gist_id}.js"></script>\n'

    with open(readme_path, 'a') as f:
        f.write(f'\n## Latest Voice Memo\n\n')
        f.write(embed_code)

    print(f"✅ Added gist embed to {readme_path}")

def add_to_story_wall(gist_data, privacy_level='public', readme_path='../README.md'):
    """
    Add voice memo to story wall in README

    Privacy levels:
    - 'public': Full gist embedded (visible content)
    - 'private': Hash-only proof (content obfuscated)

    Args:
        gist_data (dict): Gist response from GitHub API
        privacy_level (str): 'public' or 'private'
        readme_path (str): Path to README.md
    """
    import hashlib
    from pathlib import Path

    gist_id = gist_data['id']
    gist_url = gist_data['html_url']
    created_at = gist_data['created_at']
    description = gist_data['description']

    # Read current README
    readme = Path(readme_path)
    content = readme.read_text() if readme.exists() else ""

    # Find or create story wall section
    story_wall_marker = "## 📱 Story Wall"

    if story_wall_marker not in content:
        # Create new story wall section
        story_wall_section = f"""
{story_wall_marker}

**Voice memos recorded from iPhone via QR pairing**

### Public Stories

<!-- Public story entries below -->

### Private Stories

<!-- Private story entries (hash-only proofs) below -->

---
"""
        # Insert before the "Get In Touch" section or at end
        if "## 📬 Get In Touch" in content:
            content = content.replace("## 📬 Get In Touch", story_wall_section + "## 📬 Get In Touch")
        else:
            content += "\n" + story_wall_section

    # Generate story entry based on privacy level
    if privacy_level == 'public':
        # Public: Full gist embedded
        story_entry = f"""
<details>
<summary>🎤 {description} - <small>{created_at[:10]}</small></summary>

<script src="https://gist.github.com/{GITHUB_USERNAME}/{gist_id}.js"></script>

[View on GitHub]({gist_url})
</details>
"""
        # Insert into Public Stories section
        public_marker = "### Public Stories\n\n<!-- Public story entries below -->"
        if public_marker in content:
            content = content.replace(
                public_marker,
                f"### Public Stories\n\n<!-- Public story entries below -->\n{story_entry}"
            )

    elif privacy_level == 'private':
        # Private: Hash-only proof
        content_hash = hashlib.sha256(json.dumps(gist_data).encode()).hexdigest()

        story_entry = f"""
- 🔒 **{description}** - `{created_at[:10]}`
  - Hash: `{content_hash[:16]}...`
  - [Verify proof]({gist_url}) (requires authentication)
"""
        # Insert into Private Stories section
        private_marker = "### Private Stories\n\n<!-- Private story entries (hash-only proofs) below -->"
        if private_marker in content:
            content = content.replace(
                private_marker,
                f"### Private Stories\n\n<!-- Private story entries (hash-only proofs) below -->\n{story_entry}"
            )

    # Write updated README
    readme.write_text(content)
    print(f"✅ Added to story wall ({privacy_level}): {description}")

    return content

def create_story_from_voice_memo(voice_memo_data, privacy_level='public'):
    """
    Complete workflow: Voice memo → Gist → Story wall

    Args:
        voice_memo_data (dict): Voice memo metadata
        privacy_level (str): 'public' or 'private'

    Returns:
        dict: Gist data with story wall info
    """
    # Create gist
    timestamp = voice_memo_data.get('timestamp', datetime.now(timezone.utc).isoformat())
    filename = f"voice-memo-{timestamp[:10]}.json"
    content = json.dumps(voice_memo_data, indent=2)
    title = voice_memo_data.get('title', 'Voice Memo')
    description = f"{title} - Recorded from iPhone"

    # Create gist (always public URL, but content may be obfuscated)
    public = (privacy_level == 'public')
    gist = create_gist(filename, content, description, public=public)

    # Add to story wall
    add_to_story_wall(gist, privacy_level=privacy_level)

    return {
        'gist': gist,
        'privacy_level': privacy_level,
        'story_wall_updated': True
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create GitHub gist')
    parser.add_argument('--file', required=True, help='File to upload')
    parser.add_argument('--description', required=True, help='Gist description')
    parser.add_argument('--public', action='store_true', default=True, help='Make gist public')
    parser.add_argument('--embed', action='store_true', help='Embed in README')

    args = parser.parse_args()

    # Read file content
    with open(args.file, 'r') as f:
        content = f.read()

    # Create gist
    gist = create_gist(
        filename=os.path.basename(args.file),
        content=content,
        description=args.description,
        public=args.public
    )

    print(f"✅ Gist created: {gist['html_url']}")
    print(f"   ID: {gist['id']}")

    # Optionally embed in README
    if args.embed:
        embed_gist_in_readme(gist['id'])

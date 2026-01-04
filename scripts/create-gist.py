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

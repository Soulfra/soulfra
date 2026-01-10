#!/usr/bin/env python3
"""
Auto Publisher - Publish debates to GitHub Pages via API

No manual git commits needed. Uses GitHub API to create commits automatically.

Usage:
    from auto_publisher import auto_publish_debate
    auto_publish_debate('debates/2026-01-03-my-debate.md')
"""

import os
import base64
import requests
from pathlib import Path
from typing import Optional


class GitHubPublisher:
    """Publish files to GitHub Pages via API"""

    def __init__(self, repo_owner='Soulfra', repo_name='soulfra.github.io'):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

        # Get GitHub token from environment
        self.token = os.environ.get('GITHUB_TOKEN')
        if not self.token:
            print("⚠️  GITHUB_TOKEN not set. Will use local git instead.")

        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        } if self.token else {}

    def get_file_sha(self, file_path: str) -> Optional[str]:
        """Get SHA of existing file (needed for updates)"""
        if not self.token:
            return None

        url = f"{self.api_base}/contents/{file_path}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json().get('sha')
        return None

    def create_or_update_file(self, file_path: str, content: str, commit_message: str) -> bool:
        """
        Create or update file via GitHub API

        Args:
            file_path: Path in repo (e.g. 'debates/2026-01-03-foo.md')
            content: File content
            commit_message: Commit message

        Returns:
            True if successful
        """
        if not self.token:
            print("❌ GitHub token not available. Using local git instead.")
            return False

        url = f"{self.api_base}/contents/{file_path}"

        # Encode content to base64
        content_bytes = content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')

        # Check if file exists
        existing_sha = self.get_file_sha(file_path)

        payload = {
            'message': commit_message,
            'content': content_b64,
            'branch': 'main'
        }

        if existing_sha:
            payload['sha'] = existing_sha

        response = requests.put(url, json=payload, headers=self.headers)

        if response.status_code in [200, 201]:
            print(f"✅ Published to GitHub: {file_path}")
            return True
        else:
            print(f"❌ GitHub API error: {response.status_code}")
            print(f"   {response.json().get('message', 'Unknown error')}")
            return False


def auto_publish_debate(debate_file_path: Path) -> Optional[str]:
    """
    Auto-publish debate to GitHub Pages

    Args:
        debate_file_path: Local path to debate markdown file

    Returns:
        GitHub Pages URL if successful
    """
    debate_path = Path(debate_file_path)

    if not debate_path.exists():
        print(f"❌ File not found: {debate_file_path}")
        return None

    # Read file content
    with open(debate_path, 'r') as f:
        content = f.read()

    # Determine repo path
    repo_path = f"debates/{debate_path.name}"

    # Try GitHub API first
    publisher = GitHubPublisher()

    if publisher.token:
        success = publisher.create_or_update_file(
            repo_path,
            content,
            f"Add debate: {debate_path.stem}"
        )

        if success:
            return f"https://soulfra.github.io/debates/{debate_path.name}"

    # Fallback to local git
    print("📦 Using local git publish instead...")
    from publish_debates import publish_debates
    publish_debates()

    return f"https://soulfra.github.io/debates/{debate_path.name}"


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 auto_publisher.py <debate-file.md>")
        sys.exit(1)

    debate_file = sys.argv[1]
    url = auto_publish_debate(debate_file)

    if url:
        print(f"\n🌐 Published: {url}")
    else:
        print("\n❌ Publishing failed")

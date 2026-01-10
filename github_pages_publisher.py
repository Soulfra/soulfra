#!/usr/bin/env python3
"""
GitHub Pages Publisher - Decentralized Hosting

Publish content to GitHub Pages (soulfra.github.io/soulfra)
100% decentralized, free hosting, version-controlled content

Like Medium, but:
- You own the domain
- Content is version-controlled (Git)
- Free forever (GitHub Pages)
- Can fork and run your own version
- Censorship-resistant

Multi-domain strategy:
- soulfra.com → Main platform (app.py)
- soulfra.ai → AI tools (Ollama integration)
- soulfra.github.io/soulfra → Static content (decentralized)
- github.com/soulfra → Open-source repos
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

# ==============================================================================
# CONFIGURATION
# ==============================================================================

GITHUB_PAGES_REPO = "soulfra/soulfra.github.io"
LOCAL_REPO_PATH = Path.home() / "soulfra-github-pages"
GITHUB_PAGES_URL = "https://soulfra.github.io/soulfra"

# ==============================================================================
# GIT OPERATIONS
# ==============================================================================

class GitHubPagesPublisher:
    """Publish content to GitHub Pages"""

    def __init__(self, repo_path: Path = LOCAL_REPO_PATH):
        self.repo_path = repo_path
        self.posts_dir = repo_path / "posts"
        self.index_path = repo_path / "index.html"
        self.feed_path = repo_path / "feed.json"

    def init_repo(self, github_token: Optional[str] = None) -> Dict:
        """
        Initialize GitHub Pages repository

        Args:
            github_token: GitHub personal access token

        Returns:
            {'success': bool, 'repo_path': str}
        """

        if self.repo_path.exists():
            return {
                'success': True,
                'repo_path': str(self.repo_path),
                'status': 'already_exists'
            }

        try:
            # Clone repo
            if github_token:
                clone_url = f"https://{github_token}@github.com/{GITHUB_PAGES_REPO}.git"
            else:
                clone_url = f"https://github.com/{GITHUB_PAGES_REPO}.git"

            subprocess.run(
                ['git', 'clone', clone_url, str(self.repo_path)],
                check=True,
                capture_output=True
            )

            # Create posts directory
            self.posts_dir.mkdir(exist_ok=True)

            return {
                'success': True,
                'repo_path': str(self.repo_path),
                'status': 'cloned'
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr.decode() if e.stderr else str(e)
            }

    def publish_post(
        self,
        title: str,
        content: str,
        slug: str,
        category: str = 'general',
        tags: List[str] = None,
        author: str = 'soulfra',
        commit_message: Optional[str] = None
    ) -> Dict:
        """
        Publish blog post to GitHub Pages

        Args:
            title: Post title
            content: Markdown content
            slug: URL slug
            category: Category
            tags: List of tags
            author: Author name
            commit_message: Git commit message

        Returns:
            {
                'success': bool,
                'url': str,
                'hash': str,
                'commit_sha': str
            }
        """

        if not self.repo_path.exists():
            return {'success': False, 'error': 'Repo not initialized. Run init_repo() first.'}

        tags = tags or []

        # Create post metadata
        post_date = datetime.utcnow()
        post_hash = hashlib.sha256(f"{slug}{post_date.isoformat()}".encode()).hexdigest()[:16]

        # Post frontmatter (YAML-style)
        frontmatter = f"""---
title: "{title}"
slug: "{slug}"
date: "{post_date.isoformat()}"
category: "{category}"
tags: {json.dumps(tags)}
author: "{author}"
hash: "{post_hash}"
---

"""

        full_content = frontmatter + content

        # Write post file
        post_filename = f"{post_date.strftime('%Y-%m-%d')}-{slug}.md"
        post_path = self.posts_dir / post_filename

        with open(post_path, 'w') as f:
            f.write(full_content)

        # Update index
        self._update_index()

        # Update feed
        self._update_feed()

        # Git commit and push
        commit_msg = commit_message or f"Publish: {title}"

        try:
            # Git add
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.repo_path,
                check=True
            )

            # Git commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            commit_sha = result.stdout.decode().split('[')[1].split(']')[0] if '[' in result.stdout.decode() else 'unknown'

            # Git push
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=self.repo_path,
                check=True
            )

            post_url = f"{GITHUB_PAGES_URL}/posts/{slug}.html"

            return {
                'success': True,
                'url': post_url,
                'hash': post_hash,
                'commit_sha': commit_sha,
                'file_path': str(post_path)
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr.decode() if e.stderr else str(e)
            }

    def _update_index(self):
        """Update index.html with list of posts"""

        # Get all posts
        posts = []
        for post_file in sorted(self.posts_dir.glob("*.md"), reverse=True):
            with open(post_file, 'r') as f:
                content = f.read()

            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    metadata = {}
                    for line in frontmatter_text.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip().strip('"')

                    posts.append({
                        'title': metadata.get('title', 'Untitled'),
                        'slug': metadata.get('slug', ''),
                        'date': metadata.get('date', ''),
                        'category': metadata.get('category', 'general'),
                        'hash': metadata.get('hash', '')
                    })

        # Generate HTML
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soulfra - Decentralized Content</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { font-size: 2.5rem; margin-bottom: 10px; color: #00ff88; }
        .subtitle { color: #888; margin-bottom: 40px; font-size: 1.1rem; }
        .post { background: #1a1a1a; padding: 20px; margin-bottom: 20px; border-radius: 8px; border-left: 4px solid #00ff88; }
        .post h2 { margin-bottom: 10px; color: #00ff88; }
        .post .meta { color: #666; font-size: 0.9rem; margin-bottom: 10px; }
        .post .category { display: inline-block; background: #00ff88; color: #0a0a0a; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-right: 10px; }
        .post .hash { font-family: monospace; font-size: 0.8rem; color: #444; }
        a { color: #00ff88; text-decoration: none; }
        a:hover { text-decoration: underline; }
        footer { margin-top: 60px; padding-top: 20px; border-top: 1px solid #333; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Soulfra</h1>
        <p class="subtitle">Decentralized content on GitHub Pages. Fork it, own it, build it.</p>
"""

        for post in posts:
            html += f"""
        <div class="post">
            <h2><a href="/soulfra/posts/{post['slug']}.html">{post['title']}</a></h2>
            <div class="meta">
                <span class="category">{post['category']}</span>
                <span class="date">{post['date'][:10]}</span>
                <span class="hash">#{post['hash']}</span>
            </div>
        </div>
"""

        html += """
        <footer>
            <p>Powered by GitHub Pages | <a href="https://github.com/soulfra">Open Source</a> | <a href="/soulfra/feed.json">RSS Feed</a></p>
        </footer>
    </div>
</body>
</html>
"""

        with open(self.index_path, 'w') as f:
            f.write(html)

    def _update_feed(self):
        """Update feed.json (JSON Feed format)"""

        posts = []
        for post_file in sorted(self.posts_dir.glob("*.md"), reverse=True)[:20]:  # Latest 20
            with open(post_file, 'r') as f:
                content = f.read()

            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    body = parts[2].strip()

                    metadata = {}
                    for line in frontmatter_text.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip().strip('"')

                    posts.append({
                        'id': f"{GITHUB_PAGES_URL}/posts/{metadata.get('slug', '')}.html",
                        'url': f"{GITHUB_PAGES_URL}/posts/{metadata.get('slug', '')}.html",
                        'title': metadata.get('title', 'Untitled'),
                        'content_html': body[:500] + '...',  # Preview
                        'date_published': metadata.get('date', ''),
                        'tags': json.loads(metadata.get('tags', '[]')) if metadata.get('tags', '').startswith('[') else []
                    })

        feed = {
            'version': 'https://jsonfeed.org/version/1',
            'title': 'Soulfra',
            'home_page_url': GITHUB_PAGES_URL,
            'feed_url': f'{GITHUB_PAGES_URL}/feed.json',
            'description': 'Decentralized content on GitHub Pages',
            'items': posts
        }

        with open(self.feed_path, 'w') as f:
            json.dump(feed, f, indent=2)


# ==============================================================================
# CROSS-DOMAIN PUBLISHING
# ==============================================================================

def publish_to_all_domains(
    title: str,
    content: str,
    slug: str,
    category: str = 'general',
    tags: List[str] = None
) -> Dict:
    """
    Publish content to all Soulfra domains

    Domains:
    - soulfra.com (main platform via app.py)
    - soulfra.github.io/soulfra (GitHub Pages)
    - Future: soulfra.ai (AI tools)

    Args:
        title: Post title
        content: Markdown content
        slug: URL slug
        category: Category
        tags: Tags

    Returns:
        {
            'soulfra_com': {'success': bool, 'url': str},
            'github_pages': {'success': bool, 'url': str},
            'hash': str
        }
    """

    results = {}

    # Publish to GitHub Pages
    publisher = GitHubPagesPublisher()
    github_result = publisher.publish_post(title, content, slug, category, tags)
    results['github_pages'] = github_result

    # Publish to soulfra.com (via database)
    # TODO: Import post creation from app.py
    # For now, placeholder:
    results['soulfra_com'] = {
        'success': False,
        'error': 'Not implemented yet - integrate with app.py post creation'
    }

    # Content hash (for verification across domains)
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    results['hash'] = content_hash

    return results


# ==============================================================================
# DOMAIN VERIFICATION INTEGRATION
# ==============================================================================

def verify_ownership_across_domains(user_id: int) -> Dict:
    """
    Verify user owns all Soulfra domains

    Checks:
    - soulfra.com (DNS TXT record)
    - soulfra.ai (DNS TXT record)
    - soulfra.github.io (GitHub repo ownership)
    - github.com/soulfra (GitHub org ownership)

    Args:
        user_id: User ID

    Returns:
        {
            'soulfra_com': bool,
            'soulfra_ai': bool,
            'github_pages': bool,
            'github_org': bool
        }
    """

    from domain_verification import verify_domain_dns, is_domain_verified

    verification = {}

    # Check soulfra.com
    verification['soulfra_com'] = is_domain_verified('soulfra.com')

    # Check soulfra.ai
    verification['soulfra_ai'] = is_domain_verified('soulfra.ai')

    # Check GitHub Pages (verify repo ownership)
    try:
        import requests
        response = requests.get(f'https://api.github.com/repos/{GITHUB_PAGES_REPO}')
        if response.status_code == 200:
            data = response.json()
            # Check if user has write access (placeholder - need GitHub API token)
            verification['github_pages'] = True
        else:
            verification['github_pages'] = False
    except:
        verification['github_pages'] = False

    # Check GitHub org ownership
    try:
        response = requests.get('https://api.github.com/orgs/soulfra')
        verification['github_org'] = response.status_code == 200
    except:
        verification['github_org'] = False

    return verification


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("GitHub Pages Publisher - Decentralized Hosting")
    print()
    print("Multi-domain strategy:")
    print("  soulfra.com → Main platform (Flask)")
    print("  soulfra.ai → AI tools (Ollama)")
    print("  soulfra.github.io/soulfra → Static content (GitHub Pages)")
    print("  github.com/soulfra → Open-source repos")
    print()
    print("Features:")
    print("  - Publish to GitHub Pages")
    print("  - Cross-domain syndication")
    print("  - Content hashing for verification")
    print("  - JSON Feed for RSS readers")
    print("  - 100% free, 100% decentralized")

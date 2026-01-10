#!/usr/bin/env python3
"""
Publisher Routes - Export content to domains and push to GitHub

Workflow:
1. User writes post in /admin/studio
2. Selects domains to publish to
3. Clicks "Export + Push to GitHub"
4. System generates static HTML for each domain
5. Copies to domains/{domain}/build/
6. Copies to docs/{domain}/ (GitHub Pages)
7. Git commits and pushes
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from domain_manager import DomainManager
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

publisher_bp = Blueprint('publisher', __name__)


@publisher_bp.route('/api/publisher/domains', methods=['GET'])
def list_domains():
    """Get all available domains for publishing"""
    manager = DomainManager()
    domains = manager.get_all()

    return jsonify({
        'success': True,
        'domains': domains,
        'count': len(domains)
    })


@publisher_bp.route('/api/publisher/export', methods=['POST'])
def export_to_domains():
    """
    Export post to selected domains and optionally push to GitHub

    POST body:
    {
        "post_id": 34,
        "domains": ["soulfra.com", "calriven.com"],
        "push_to_github": true,
        "commit_message": "Update blog posts"
    }
    """
    data = request.json

    post_id = data.get('post_id')
    selected_domains = data.get('domains', [])
    push_to_github = data.get('push_to_github', False)
    commit_message = data.get('commit_message', 'Update content from admin studio')

    if not post_id:
        return jsonify({'success': False, 'error': 'No post_id provided'}), 400

    if not selected_domains:
        return jsonify({'success': False, 'error': 'No domains selected'}), 400

    # Get post from database
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if not post:
        return jsonify({'success': False, 'error': 'Post not found'}), 404

    # Get domain manager
    manager = DomainManager()

    results = []
    errors = []

    # Export to each domain
    for domain_name in selected_domains:
        domain = manager.get_domain(domain_name)
        if not domain:
            errors.append(f"Domain {domain_name} not found")
            continue

        try:
            # Generate static HTML for this domain
            html = generate_post_html(post, domain)

            # Get GitHub repo path (if it exists)
            github_repo = domain.get('github_repo')

            if not github_repo:
                errors.append(f"{domain_name}: No GitHub repo found. Run setup_github_repos.sh first")
                continue

            # Export to GitHub repo (will be pushed to GitHub Pages)
            repo_posts_dir = Path(github_repo) / 'posts'
            repo_posts_dir.mkdir(parents=True, exist_ok=True)

            post_file = repo_posts_dir / f"{post['slug']}.html"
            with open(post_file, 'w') as f:
                f.write(html)

            # Update index.html with latest posts
            update_index_html(github_repo, post, domain)

            results.append({
                'domain': domain_name,
                'success': True,
                'github_repo': github_repo,
                'files': [str(post_file)],
                'live_url': f"https://{domain_name}/posts/{post['slug']}.html"
            })

        except Exception as e:
            errors.append(f"{domain_name}: {str(e)}")

    # If push to GitHub requested
    git_result = None
    if push_to_github and results:
        try:
            git_result = push_to_git(commit_message, selected_domains)
        except Exception as e:
            git_result = {'success': False, 'error': str(e)}

    return jsonify({
        'success': len(results) > 0,
        'results': results,
        'errors': errors,
        'git': git_result,
        'post_id': post_id,
        'domains_exported': len(results)
    })


def generate_post_html(post, domain):
    """Generate static HTML for a post on a specific domain"""
    # Basic template - you can customize this per domain
    category = domain.get('category', 'general')
    domain_name = domain['domain']

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - {domain.get('name', domain_name)}</title>
    <link rel="stylesheet" href="/theme-{domain_name.split('.')[0]}.css">
</head>
<body>
    <header>
        <h1>{domain.get('name', domain_name)}</h1>
        <p>{domain.get('tagline', '')}</p>
    </header>

    <main>
        <article>
            <h2>{post['title']}</h2>
            <div class="meta">
                <time>{post['published_at']}</time>
            </div>

            <div class="content">
                {post['content']}
            </div>
        </article>

        <footer>
            <p>Powered by <a href="https://soulfra.com">Soulfra</a></p>
        </footer>
    </main>
</body>
</html>
"""

    return html


def update_index_html(github_repo, post, domain):
    """Update index.html in GitHub repo with latest post"""
    index_path = Path(github_repo) / 'index.html'

    # If index doesn't exist, create a simple one
    if not index_path.exists():
        domain_name = domain['domain']
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain.get('name', domain_name)}</title>
</head>
<body>
    <h1>{domain.get('name', domain_name)}</h1>
    <p>{domain.get('tagline', 'AI-powered content')}</p>

    <h2>Latest Posts</h2>
    <ul id="posts">
        <li><a href="/posts/{post['slug']}.html">{post['title']}</a> - {post['published_at']}</li>
    </ul>
</body>
</html>
"""
        with open(index_path, 'w') as f:
            f.write(html)
    # else: Could parse existing index and prepend new post, but for now keep it simple


def push_to_git(commit_message, selected_domains):
    """Git add, commit, and push each domain's GitHub repo"""
    manager = DomainManager()
    results = []

    for domain_name in selected_domains:
        domain = manager.get_domain(domain_name)
        if not domain or not domain.get('github_repo'):
            continue

        github_repo = Path(domain['github_repo'])

        try:
            # Git status
            status_result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=github_repo,
                capture_output=True,
                text=True
            )

            if not status_result.stdout.strip():
                results.append({
                    'domain': domain_name,
                    'success': True,
                    'message': 'No changes to commit',
                    'pushed': False
                })
                continue

            # Git add all
            subprocess.run(
                ['git', 'add', '.'],
                cwd=github_repo,
                check=True
            )

            # Git commit
            full_message = f"""{commit_message}

Published via Soulfra Studio

🤖 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>
"""

            subprocess.run(
                ['git', 'commit', '-m', full_message],
                cwd=github_repo,
                check=True
            )

            # Git push
            push_result = subprocess.run(
                ['git', 'push'],
                cwd=github_repo,
                capture_output=True,
                text=True
            )

            if push_result.returncode == 0:
                results.append({
                    'domain': domain_name,
                    'success': True,
                    'message': f'Pushed to GitHub → https://{domain_name}',
                    'pushed': True,
                    'live_url': f'https://{domain_name}'
                })
            else:
                results.append({
                    'domain': domain_name,
                    'success': False,
                    'error': push_result.stderr,
                    'pushed': False
                })

        except subprocess.CalledProcessError as e:
            results.append({
                'domain': domain_name,
                'success': False,
                'error': str(e),
                'pushed': False
            })

    return {
        'success': any(r['pushed'] for r in results if 'pushed' in r),
        'results': results,
        'total_pushed': sum(1 for r in results if r.get('pushed'))
    }


@publisher_bp.route('/api/publisher/add-domain', methods=['POST'])
def add_domain():
    """
    Add new domain to master list (with optional Ollama suggestion)

    POST body:
    {
        "domain": "newdomain.com",
        "use_ollama": true
    }
    """
    data = request.json
    domain = data.get('domain', '').strip()

    if not domain:
        return jsonify({'success': False, 'error': 'No domain provided'}), 400

    manager = DomainManager()

    # Check if domain already exists
    if manager.get_domain(domain):
        return jsonify({'success': False, 'error': 'Domain already exists'}), 400

    # If use_ollama requested, ask Ollama to suggest category/tags
    ollama_suggestion = None
    if data.get('use_ollama', False):
        try:
            import requests
            ollama_result = requests.post('http://localhost:11434/api/generate', json={
                'model': 'llama3.2:3b',
                'prompt': f"""Analyze this domain name and suggest metadata:

Domain: {domain}

Respond with JSON only:
{{
    "category": "tech|privacy|cooking|business|health|art|education",
    "suggested_tags": ["tag1", "tag2"],
    "tagline": "Short one-line description",
    "target_audience": "Who would use this site?"
}}""",
                'stream': False
            })

            if ollama_result.status_code == 200:
                response_text = ollama_result.json().get('response', '{}')
                # Try to parse JSON from response
                try:
                    ollama_suggestion = json.loads(response_text)
                except:
                    pass

        except Exception as e:
            print(f"Ollama error: {e}")

    # Add domain to manager
    category = ollama_suggestion.get('category', 'general') if ollama_suggestion else 'general'
    manager.add_domain(
        domain=domain,
        category=category
    )

    # Save to domains-simple.txt
    manager.save_to_simple_txt()

    return jsonify({
        'success': True,
        'domain': domain,
        'category': category,
        'ollama_suggestion': ollama_suggestion
    })

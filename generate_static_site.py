#!/usr/bin/env python3
"""
STATIC SITE GENERATOR - IRC/Usenet → GitHub Pages

Converts IRC messages + voice recordings into static HTML websites
Deployable to GitHub Pages with embeddable widgets

Features:
- Multiple templates (blog, newspaper, classified)
- Embeddable widget for external sites
- RSS feed integration
- Real-time polling via JSON
- One-click GitHub Pages deploy

Usage:
    python3 generate_static_site.py --domain soulfra --template blog
    python3 generate_static_site.py --domain cringeproof --template newspaper
    python3 generate_static_site.py --all --template blog
"""

import sqlite3
import os
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from jinja2 import Template
import html


# Configuration
DB_PATH = "soulfra.db"
OUTPUT_DIR = Path("static-sites")
TEMPLATES_DIR = Path("templates/static-site")
GITHUB_PAGES_REPO = Path("/Users/matthewmauer/Desktop/soulfra.github.io")


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_domain_messages(domain, limit=100):
    """Get IRC messages for domain"""
    db = get_db()

    messages = db.execute('''
        SELECT
            id,
            from_user,
            to_domain,
            channel,
            subject,
            body,
            created_at,
            message_type,
            'irc' as source
        FROM domain_messages
        WHERE to_domain = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (domain, limit)).fetchall()

    db.close()
    return [dict(msg) for msg in messages]


def get_domain_voice_recordings(domain, limit=100):
    """Get voice recordings for domain"""
    db = get_db()

    recordings = db.execute('''
        SELECT
            svr.id,
            COALESCE(u.email, 'anonymous') as from_user,
            ? as to_domain,
            'voice' as channel,
            '' as subject,
            svr.transcription as body,
            svr.created_at,
            'voice' as message_type,
            'voice' as source
        FROM simple_voice_recordings svr
        LEFT JOIN users u ON svr.user_id = u.id
        WHERE svr.transcription IS NOT NULL
        ORDER BY svr.created_at DESC
        LIMIT ?
    ''', (domain, limit)).fetchall()

    db.close()
    return [dict(rec) for rec in recordings]


def get_merged_content(domain, limit=100):
    """Get merged IRC + voice content for domain"""
    irc_messages = get_domain_messages(domain, limit)
    voice_recordings = get_domain_voice_recordings(domain, limit)

    # Merge and sort by created_at
    all_content = irc_messages + voice_recordings
    all_content = sorted(all_content, key=lambda x: x['created_at'], reverse=True)[:limit]

    return all_content


def generate_blog_template(domain, content):
    """Generate blog-style static site"""

    print(f"\n📝 Generating blog template for {domain}")

    template_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ domain_title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f6f8fa;
            color: #24292f;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        .header {
            text-align: center;
            padding: 3rem 0;
            border-bottom: 2px solid #d0d7de;
            margin-bottom: 3rem;
        }
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .header p {
            color: #57606a;
            font-size: 1.1rem;
        }
        .post {
            background: white;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 2rem;
            margin-bottom: 2rem;
            transition: all 0.2s;
        }
        .post:hover {
            border-color: #0969da;
            box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        }
        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #d0d7de;
        }
        .post-author {
            font-weight: 600;
            color: #0969da;
        }
        .post-date {
            color: #57606a;
            font-size: 0.9rem;
        }
        .post-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .post-body {
            color: #24292f;
            line-height: 1.8;
            white-space: pre-wrap;
        }
        .post-meta {
            margin-top: 1rem;
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            color: #57606a;
        }
        .badge {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-voice {
            background: #ddf4ff;
            color: #0969da;
        }
        .badge-irc {
            background: #dafbe1;
            color: #1a7f37;
        }
        .footer {
            text-align: center;
            padding: 2rem;
            color: #57606a;
            border-top: 1px solid #d0d7de;
            margin-top: 3rem;
        }
        .rss-link {
            display: inline-block;
            margin: 1rem 0;
            padding: 0.5rem 1rem;
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            color: #0969da;
            text-decoration: none;
            font-weight: 500;
        }
        .rss-link:hover {
            background: #0969da;
            color: white;
        }
        /* Comments Section */
        .comments-section {
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 2px solid #d0d7de;
        }
        .comments-header {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .comment {
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .comment-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }
        .comment-author {
            font-weight: 600;
            color: #0969da;
        }
        .comment-date {
            color: #57606a;
        }
        .comment-body {
            color: #24292f;
            line-height: 1.6;
        }
        .comment-reply {
            margin-left: 2rem;
            margin-top: 0.5rem;
        }
        .comment-form {
            margin-top: 1.5rem;
        }
        .comment-form input,
        .comment-form textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            font-family: inherit;
            font-size: 0.9rem;
            margin-bottom: 0.75rem;
        }
        .comment-form textarea {
            min-height: 100px;
            resize: vertical;
        }
        .comment-submit {
            padding: 0.75rem 1.5rem;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }
        .comment-submit:hover {
            background: #2ea043;
        }
        .loading {
            text-align: center;
            padding: 1rem;
            color: #57606a;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ domain_title }}</h1>
            <p>{{ domain_description }}</p>
            <a href="feed.xml" class="rss-link">📡 Subscribe via RSS</a>
        </div>

        {% for post in posts %}
        <article class="post">
            <div class="post-header">
                <span class="post-author">{{ post.from_user }}</span>
                <span class="post-date">{{ post.formatted_date }}</span>
            </div>

            {% if post.subject %}
            <h2 class="post-title">{{ post.subject }}</h2>
            {% endif %}

            <div class="post-body">{{ post.body }}</div>

            <div class="post-meta">
                <span class="badge badge-{{ post.source }}">
                    {% if post.source == 'voice' %}🎤 Voice{% else %}💬 IRC{% endif %}
                </span>
                <span>alt.{{ post.to_domain }}.{{ post.channel }}</span>
                <span>ID: {{ post.id }}</span>
            </div>

            <!-- Comments Section -->
            <div class="comments-section" id="comments-{{ post.id }}">
                <div class="comments-header">💬 Comments</div>
                <div class="comments-list">
                    <div class="loading">Loading comments...</div>
                </div>

                <!-- Comment Form -->
                <div class="comment-form">
                    <input type="text" placeholder="Your name (optional)" id="name-{{ post.id }}">
                    <textarea placeholder="Add a comment..." id="comment-{{ post.id }}"></textarea>
                    <button class="comment-submit" onclick="submitComment('{{ post.to_domain }}', {{ post.id }})">Post Comment</button>
                </div>
            </div>
        </article>
        {% endfor %}

        <div class="footer">
            <p>Powered by IRC/Usenet messaging system</p>
            <p>Generated: {{ generation_time }}</p>
        </div>
    </div>

    <script>
        const API_URL = 'https://192.168.1.87:5002';

        // Load comments for all posts on page load
        document.addEventListener('DOMContentLoaded', () => {
            {% for post in posts %}
            loadComments('{{ post.to_domain }}', {{ post.id }});
            {% endfor %}
        });

        // Load comments for a specific post
        async function loadComments(domain, postId) {
            try {
                const response = await fetch(`${API_URL}/api/messages/${domain}/${postId}/comments`);
                const data = await response.json();

                const container = document.querySelector(`#comments-${postId} .comments-list`);

                if (data.comments && data.comments.length > 0) {
                    container.innerHTML = data.comments.map(comment => renderComment(comment)).join('');
                } else {
                    container.innerHTML = '<div class="loading">No comments yet. Be the first!</div>';
                }
            } catch (error) {
                console.error('Failed to load comments:', error);
                document.querySelector(`#comments-${postId} .comments-list`).innerHTML =
                    '<div class="loading">Comments unavailable (offline mode)</div>';
            }
        }

        // Render a single comment (with nested replies)
        function renderComment(comment) {
            const date = new Date(comment.created_at).toLocaleString();

            let html = `
                <div class="comment">
                    <div class="comment-header">
                        <span class="comment-author">${escapeHtml(comment.from_user)}</span>
                        <span class="comment-date">${date}</span>
                    </div>
                    <div class="comment-body">${escapeHtml(comment.body)}</div>
            `;

            // Render nested replies
            if (comment.replies && comment.replies.length > 0) {
                html += '<div class="comment-reply">';
                html += comment.replies.map(reply => renderComment(reply)).join('');
                html += '</div>';
            }

            html += '</div>';
            return html;
        }

        // Submit a new comment
        async function submitComment(domain, postId) {
            const nameInput = document.getElementById(`name-${postId}`);
            const commentInput = document.getElementById(`comment-${postId}`);

            const body = commentInput.value.trim();
            if (!body) {
                alert('Please enter a comment');
                return;
            }

            const fromUser = nameInput.value.trim() || 'anonymous';

            try {
                const response = await fetch(`${API_URL}/api/messages/${domain}/${postId}/comments`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        body: body,
                        from_user: fromUser
                    })
                });

                const data = await response.json();

                if (data.success) {
                    // Clear form
                    commentInput.value = '';
                    // Reload comments
                    await loadComments(domain, postId);
                } else {
                    alert('Failed to post comment: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Failed to post comment:', error);
                alert('Failed to post comment. Are you online?');
            }
        }

        // Escape HTML to prevent XSS
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""

    # Domain metadata
    domain_info = {
        'soulfra': {
            'title': 'Soulfra Blog',
            'description': 'Voice-first personal blog powered by IRC/Usenet'
        },
        'cringeproof': {
            'title': 'CringeProof Ideas',
            'description': 'Authentic thoughts, zero cringe'
        },
        'deathtodata': {
            'title': 'DeathToData',
            'description': 'Privacy-first messaging and ideas'
        },
        'calriven': {
            'title': 'CalRiven Blog',
            'description': 'Personal thoughts and voice memos'
        },
        'stpetepros': {
            'title': 'StPetePros News',
            'description': 'Professional services and local events'
        }
    }

    info = domain_info.get(domain, {
        'title': f'{domain.title()} Blog',
        'description': f'Messages and ideas from {domain}'
    })

    # Format posts
    posts = []
    for item in content:
        post_date = datetime.fromisoformat(item['created_at'])
        formatted_date = post_date.strftime('%B %d, %Y at %I:%M %p')

        posts.append({
            **item,
            'formatted_date': formatted_date
        })

    # Render template
    template = Template(template_html)
    html_output = template.render(
        domain_title=info['title'],
        domain_description=info['description'],
        posts=posts,
        generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    return html_output


def export_to_directory(domain, html_content, template_type):
    """Export static site to directory"""

    # Create output directory
    site_dir = OUTPUT_DIR / domain / template_type
    site_dir.mkdir(parents=True, exist_ok=True)

    # Write index.html
    index_path = site_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✅ Exported: {index_path}")

    # Copy RSS feed (will be generated by Flask RSS endpoint)
    print(f"  📡 RSS: https://192.168.1.87:5002/api/messages/{domain}/feed.xml")

    return site_dir


def deploy_to_github_pages(domain, site_dir):
    """Deploy site to GitHub Pages repo"""

    print(f"\n🚀 Deploying to GitHub Pages...")

    # Create domain directory in GitHub Pages repo
    gh_domain_dir = GITHUB_PAGES_REPO / domain
    gh_domain_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files
    for file_path in site_dir.glob('*'):
        dest_path = gh_domain_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"  ✅ Copied: {file_path.name} → {dest_path}")

    print(f"\n  🌐 GitHub Pages URL: https://soulfra.github.io/{domain}/")
    print(f"  📂 Local path: {gh_domain_dir}")

    return gh_domain_dir


def main():
    parser = argparse.ArgumentParser(description="Static Site Generator - IRC → GitHub Pages")
    parser.add_argument("--domain", help="Domain to generate site for")
    parser.add_argument("--all", action="store_true", help="Generate for all domains")
    parser.add_argument("--template", default="blog", choices=["blog", "newspaper", "classified"],
                       help="Template style (default: blog)")
    parser.add_argument("--limit", type=int, default=100, help="Max posts to include")
    parser.add_argument("--deploy", action="store_true", help="Deploy to GitHub Pages")

    args = parser.parse_args()

    # Get domains to process
    if args.all:
        # Get all domains with messages
        db = get_db()
        domains = db.execute('''
            SELECT DISTINCT to_domain FROM domain_messages
        ''').fetchall()
        domain_list = [d['to_domain'] for d in domains]
        db.close()
    elif args.domain:
        domain_list = [args.domain]
    else:
        parser.error("Must specify --domain or --all")

    print(f"\n🏗️  STATIC SITE GENERATOR")
    print("=" * 60)
    print(f"Template: {args.template}")
    print(f"Domains: {', '.join(domain_list)}")
    print("=" * 60)

    for domain in domain_list:
        print(f"\n📦 Processing {domain}...")

        # Get content
        content = get_merged_content(domain, args.limit)

        if not content:
            print(f"  ⚠️  No content found for {domain}")
            continue

        print(f"  📊 Found {len(content)} posts")

        # Generate HTML based on template
        if args.template == "blog":
            html_output = generate_blog_template(domain, content)
        elif args.template == "newspaper":
            # TODO: Implement newspaper template
            print(f"  ⚠️  Newspaper template not yet implemented, using blog")
            html_output = generate_blog_template(domain, content)
        elif args.template == "classified":
            # TODO: Implement classified template
            print(f"  ⚠️  Classified template not yet implemented, using blog")
            html_output = generate_blog_template(domain, content)

        # Export to directory
        site_dir = export_to_directory(domain, html_output, args.template)

        # Deploy to GitHub Pages if requested
        if args.deploy:
            deploy_to_github_pages(domain, site_dir)

    print(f"\n✅ DONE! Generated {len(domain_list)} static sites")
    print(f"📂 Output directory: {OUTPUT_DIR.absolute()}")

    if args.deploy:
        print(f"\n📌 Next steps:")
        print(f"   1. cd {GITHUB_PAGES_REPO}")
        print(f"   2. git add .")
        print(f"   3. git commit -m 'Update static sites'")
        print(f"   4. git push")


if __name__ == "__main__":
    main()

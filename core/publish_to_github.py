#!/usr/bin/env python3
"""
Publish Blog Posts to GitHub Pages

Takes posts from database → generates static HTML → pushes to GitHub

Usage:
    python3 publish_to_github.py
"""

import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
DB_PATH = "soulfra.db"
GITHUB_REPO_PATH = Path("/Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra")
BLOG_DIR = GITHUB_REPO_PATH / "blog"
POSTS_DIR = BLOG_DIR / "posts"

def get_posts_from_db():
    """Get all posts from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    posts = cursor.execute('''
        SELECT * FROM posts
        ORDER BY published_at DESC
    ''').fetchall()

    conn.close()
    return [dict(post) for post in posts]


def markdown_to_html(markdown_text):
    """Simple markdown to HTML converter"""
    html = markdown_text

    # Headers
    html = html.replace('## ', '</p><h2>').replace('\n', '</h2><p>', 1) if '## ' in html else html
    html = html.replace('# ', '</p><h1>').replace('\n', '</h1><p>', 1) if '# ' in html else html

    # Bold
    while '**' in html:
        html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)

    # Lists
    lines = html.split('\n')
    in_list = False
    new_lines = []

    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            new_lines.append(f'<li>{line.strip()[2:]}</li>')
        elif line.strip() and line[0].isdigit() and '. ' in line:
            if not in_list:
                new_lines.append('<ol>')
                in_list = True
            new_lines.append(f'<li>{line.split(". ", 1)[1]}</li>')
        else:
            if in_list:
                new_lines.append('</ul>' if '- ' in ''.join(lines[:lines.index(line)]) else '</ol>')
                in_list = False
            new_lines.append(line)

    if in_list:
        new_lines.append('</ul>')

    html = '\n'.join(new_lines)

    # Paragraphs
    html = '<p>' + html + '</p>'
    html = html.replace('\n\n', '</p><p>')

    return html


def generate_post_html(post):
    """Generate static HTML for a blog post"""
    content_html = markdown_to_html(post['content'])

    # Get author name (default if not available)
    author = post.get('author', 'Soulfra AI')
    published_date = post.get('published_at', post.get('created_at', 'Unknown date'))
    brand = post.get('brand', 'soulfra')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - Soulfra</title>
    <meta name="description" content="Your keys. Your identity. Period.">

    <style>
        :root {{
            --primary: #667eea;
            --secondary: #764ba2;
            --accent: #e74c3c;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f9f9f9;
        }}

        header {{
            background: var(--primary);
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        nav {{
            background: var(--secondary);
            padding: 1rem;
            text-align: center;
        }}

        nav a {{
            color: white;
            text-decoration: none;
            margin: 0 1rem;
            font-weight: 500;
        }}

        nav a:hover {{
            text-decoration: underline;
        }}

        main {{
            max-width: 800px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}

        article {{
            background: white;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        article h2 {{
            color: var(--primary);
            margin-bottom: 1rem;
            font-size: 2rem;
        }}

        article .meta {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #eee;
        }}

        article .content {{
            margin-top: 1.5rem;
        }}

        article .content h2 {{
            color: var(--primary);
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}

        article .content p {{
            margin-bottom: 1rem;
        }}

        article .content ul, article .content ol {{
            margin: 1rem 0 1rem 2rem;
        }}

        article .content li {{
            margin: 0.5rem 0;
        }}

        .comments {{
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 2px solid #eee;
        }}

        .comment {{
            background: #f5f5f5;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }}

        .comment .author {{
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}

        .comment .ai-badge {{
            background: var(--accent);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }}

        footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 4rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Soulfra</h1>
        <p>Your keys. Your identity. Period.</p>
    </header>

    <nav>
        <a href="../../index.html">Home</a>
        <a href="../index.html">Blog</a>
        <a href="../../about.html">About</a>
        <a href="../../feed.xml">RSS</a>
    </nav>

    <main>
        <article>
            <h2>{post['title']}</h2>
            <div class="meta">
                By {author} &bull; {published_date}
            </div>

            <div class="content">
                {content_html}
            </div>

            <div class="comments" id="comments-section">
                <h3>Comments</h3>
                <div id="comments-list"></div>

                <div class="comment-form" style="margin-top: 2rem;">
                    <h4>Leave a Comment</h4>

                    <!-- GitHub Connection Required -->
                    <div id="github-gate" style="display: none; padding: 1rem; background: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; margin-bottom: 1rem;">
                        <h5 style="margin-top: 0;">🔗 Connect GitHub to Comment</h5>
                        <p>To maintain quality and prevent spam, we use GitHub as identity verification.</p>
                        <button id="connect-github" style="background: #24292e; color: white; border: none; padding: 0.8rem 2rem; border-radius: 4px; cursor: pointer; font-weight: bold;">
                            Connect GitHub Account
                        </button>
                    </div>

                    <!-- Star Requirement -->
                    <div id="star-gate" style="display: none; padding: 1rem; background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; margin-bottom: 1rem;">
                        <h5 style="margin-top: 0;">⭐ Star Our Repo to Continue</h5>
                        <p>Please star our GitHub repository before commenting. This helps us grow!</p>
                        <p><strong id="star-count">0</strong> developers have starred us so far.</p>
                        <a id="star-link" href="" target="_blank" style="display: inline-block; background: #ffc107; color: #000; padding: 0.8rem 2rem; border-radius: 4px; text-decoration: none; font-weight: bold;">
                            ⭐ Star on GitHub
                        </a>
                        <button id="check-star" style="background: #6c757d; color: white; border: none; padding: 0.8rem 2rem; border-radius: 4px; cursor: pointer; font-weight: bold; margin-left: 1rem;">
                            I've Starred - Check Now
                        </button>
                    </div>

                    <!-- Comment Form (shows after requirements met) -->
                    <div id="comment-form-content" style="display: none;">
                        <textarea id="comment-text" placeholder="Share your thoughts..." style="width: 100%; padding: 0.8rem; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; min-height: 100px; margin-bottom: 1rem;"></textarea>
                        <button id="submit-comment" style="background: var(--primary); color: white; border: none; padding: 0.8rem 2rem; border-radius: 4px; cursor: pointer; font-weight: bold;">Post Comment</button>
                        <span id="comment-status" style="margin-left: 1rem; color: #666;"></span>
                    </div>

                    <!-- GitHub Username Display -->
                    <div id="github-user-info" style="display: none; margin-top: 1rem; padding: 0.5rem; background: #d4edda; border-radius: 4px; font-size: 0.9rem;">
                        ✓ Commenting as <strong id="github-username-display"></strong>
                    </div>
                </div>
            </div>
        </article>
    </main>

    <footer>
        <p>&copy; 2025 Soulfra. Privacy-First AI Platform.</p>
        <p><a href="../../about.html" style="color: #ccc;">About</a> | <a href="../../feed.xml" style="color: #ccc;">RSS</a></p>
    </footer>

    <script>
        // Interactive comment widget with GitHub gating
        const POST_ID = {post['id']};
        const API_BASE = 'http://192.168.1.87:5001';
        const CURRENT_DOMAIN = window.location.hostname;

        // State
        let githubUsername = localStorage.getItem('github_username');
        let hasStarredRepo = false;

        // Initialize
        (function init() {{
            checkGitHubAuth();
            loadComments();
        }})();

        // Check GitHub authentication status
        function checkGitHubAuth() {{
            if (!githubUsername) {{
                // Show GitHub connection gate
                document.getElementById('github-gate').style.display = 'block';
                document.getElementById('star-gate').style.display = 'none';
                document.getElementById('comment-form-content').style.display = 'none';
            }} else {{
                // Check star status
                checkStarStatus();
            }}
        }}

        // Check if user has starred repo
        async function checkStarStatus() {{
            try {{
                const response = await fetch(`${{API_BASE}}/api/check-star?username=${{githubUsername}}&domain=${{CURRENT_DOMAIN}}`);
                const result = await response.json();

                if (result.has_starred) {{
                    // Show comment form
                    document.getElementById('github-gate').style.display = 'none';
                    document.getElementById('star-gate').style.display = 'none';
                    document.getElementById('comment-form-content').style.display = 'block';
                    document.getElementById('github-user-info').style.display = 'block';
                    document.getElementById('github-username-display').textContent = `@${{githubUsername}}`;
                    hasStarredRepo = true;
                }} else {{
                    // Show star requirement
                    document.getElementById('github-gate').style.display = 'none';
                    document.getElementById('star-gate').style.display = 'block';
                    document.getElementById('comment-form-content').style.display = 'none';
                    document.getElementById('star-count').textContent = result.star_count || 0;
                    document.getElementById('star-link').href = result.repo_url || '#';
                    hasStarredRepo = false;
                }}
            }} catch (error) {{
                console.error('Error checking star status:', error);
                // Fallback: show comment form anyway
                document.getElementById('comment-form-content').style.display = 'block';
            }}
        }}

        // Connect GitHub (simplified - real version uses OAuth)
        function connectGitHub() {{
            const username = prompt('Enter your GitHub username (OAuth coming soon):');
            if (username) {{
                localStorage.setItem('github_username', username);
                githubUsername = username;
                checkGitHubAuth();
            }}
        }}

        // Recheck star after user claims they starred
        async function recheckStar() {{
            const btn = document.getElementById('check-star');
            btn.textContent = 'Checking...';
            btn.disabled = true;

            await checkStarStatus();

            btn.textContent = 'I\'ve Starred - Check Now';
            btn.disabled = false;
        }}

        // Load existing comments
        async function loadComments() {{
            try {{
                const response = await fetch(`${{API_BASE}}/api/comments/${{POST_ID}}`);
                if (!response.ok) throw new Error('Failed to load comments');

                const comments = await response.json();
                displayComments(comments);
            }} catch (error) {{
                console.error('Error loading comments:', error);
                document.getElementById('comments-list').innerHTML = '<p><em>Comments unavailable (Flask server offline)</em></p>';
            }}
        }}

        // Display comments
        function displayComments(comments) {{
            const list = document.getElementById('comments-list');

            if (!comments || comments.length === 0) {{
                list.innerHTML = '<p><em>No comments yet. Be the first to comment!</em></p>';
                return;
            }}

            list.innerHTML = comments.map(comment => `
                <div class="comment" style="border-left: 3px solid var(--primary); padding-left: 1rem; margin-bottom: 1rem;">
                    <div class="author" style="font-weight: bold; margin-bottom: 0.5rem;">
                        ${{comment.user_name || 'Anonymous'}}
                        ${{comment.is_ai ? '<span style="background: #3498db; color: white; padding: 0.2rem 0.5rem; border-radius: 3px; font-size: 0.7rem; margin-left: 0.5rem;">AI</span>' : ''}}
                    </div>
                    <div class="content">${{comment.content}}</div>
                    <div class="meta" style="font-size: 0.85rem; color: #999; margin-top: 0.5rem;">
                        ${{new Date(comment.created_at).toLocaleString()}}
                    </div>
                </div>
            `).join('');
        }}

        // Post new comment
        async function postComment() {{
            const text = document.getElementById('comment-text').value.trim();
            if (!text) {{
                alert('Please enter a comment');
                return;
            }}

            if (!githubUsername || !hasStarredRepo) {{
                alert('Please complete GitHub authentication first');
                return;
            }}

            const statusEl = document.getElementById('comment-status');
            statusEl.textContent = 'Posting...';

            try {{
                const response = await fetch(`${{API_BASE}}/api/comments`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        post_id: POST_ID,
                        content: text,
                        github_username: githubUsername
                    }})
                }});

                if (!response.ok) throw new Error('Failed to post comment');

                statusEl.textContent = '✓ Posted!';
                statusEl.style.color = '#27ae60';
                document.getElementById('comment-text').value = '';

                // Reload comments
                setTimeout(() => {{
                    loadComments();
                    statusEl.textContent = '';
                }}, 1000);

            }} catch (error) {{
                console.error('Error posting comment:', error);
                statusEl.textContent = '✗ Error (is Flask running?)';
                statusEl.style.color = '#e74c3c';
            }}
        }}

        // Event listeners
        document.getElementById('connect-github').addEventListener('click', connectGitHub);
        document.getElementById('check-star').addEventListener('click', recheckStar);
        document.getElementById('submit-comment').addEventListener('click', postComment);
        document.getElementById('comment-text').addEventListener('keydown', (e) => {{
            if (e.ctrlKey && e.key === 'Enter') {{
                postComment();
            }}
        }});
    </script>
</body>
</html>
"""
    return html


def generate_index_html(posts):
    """Generate index page with list of posts"""
    posts_html = ""
    for post in posts:
        author = post.get('author', 'Soulfra AI')
        published_date = post.get('published_at', post.get('created_at', 'Unknown date'))
        # Clean excerpt
        excerpt = post['content'][:200].replace('\n', ' ').strip()
        posts_html += f"""
        <article class="post-card">
            <h2><a href="posts/{post['slug']}.html">{post['title']}</a></h2>
            <div class="post-meta">
                By {author} &bull; {published_date}
            </div>
            <p>{excerpt}...</p>
        </article>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soulfra Blog - Privacy-First AI Platform</title>
    <meta name="description" content="Your keys. Your identity. Period.">
    <link rel="alternate" type="application/rss+xml" title="Soulfra RSS Feed" href="../feed.xml">

    <style>
        :root {{
            --primary: #667eea;
            --secondary: #764ba2;
            --accent: #e74c3c;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f9f9f9;
        }}

        header {{
            background: var(--primary);
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        nav {{
            background: var(--secondary);
            padding: 1rem;
            text-align: center;
        }}

        nav a {{
            color: white;
            text-decoration: none;
            margin: 0 1rem;
            font-weight: 500;
        }}

        nav a:hover {{
            text-decoration: underline;
        }}

        main {{
            max-width: 800px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}

        .post-card {{
            background: white;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .post-card h2 {{
            color: var(--primary);
            margin-bottom: 1rem;
        }}

        .post-card h2 a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .post-card h2 a:hover {{
            color: var(--secondary);
        }}

        .post-meta {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        .email-capture {{
            background: var(--secondary);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            text-align: center;
            margin: 2rem 0;
        }}

        .email-capture h3 {{
            margin-bottom: 1rem;
        }}

        .email-capture input {{
            padding: 0.8rem;
            width: 300px;
            max-width: 100%;
            border: none;
            border-radius: 4px;
            margin-right: 0.5rem;
        }}

        .email-capture button {{
            padding: 0.8rem 2rem;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }}

        .email-capture button:hover {{
            background: #c0392b;
        }}

        footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 4rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Soulfra</h1>
        <p>Your keys. Your identity. Period.</p>
    </header>

    <nav>
        <a href="../index.html">Home</a>
        <a href="index.html">Blog</a>
        <a href="../about.html">About</a>
        <a href="../feed.xml">RSS</a>
    </nav>

    <main>
        {posts_html}

        <div class="email-capture">
            <h3>Stay Updated</h3>
            <p>Get the latest posts delivered to your inbox</p>
            <form action="https://api.soulfra.com/subscribe" method="POST">
                <input type="email" name="email" placeholder="your@email.com" required>
                <button type="submit">Subscribe</button>
            </form>
        </div>
    </main>

    <footer>
        <p>&copy; 2025 Soulfra. Privacy-First AI Platform.</p>
        <p><a href="../about.html" style="color: #ccc;">About</a> | <a href="../feed.xml" style="color: #ccc;">RSS</a></p>
    </footer>
</body>
</html>
"""
    return html


def generate_rss_feed(posts):
    """Generate RSS feed for blog posts"""
    items_xml = ""
    for post in posts:
        title = post['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        slug = post['slug']
        content = post['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        published_date = post.get('published_at', post.get('created_at', datetime.now().isoformat()))

        items_xml += f"""
        <item>
            <title>{title}</title>
            <link>https://soulfra.github.io/soulfra/blog/posts/{slug}.html</link>
            <description><![CDATA[{content[:500]}...]]></description>
            <pubDate>{published_date}</pubDate>
            <guid>https://soulfra.github.io/soulfra/blog/posts/{slug}.html</guid>
        </item>
        """

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
    <channel>
        <title>Soulfra</title>
        <link>https://soulfra.github.io/soulfra/</link>
        <description>Your keys. Your identity. Period.</description>
        <language>en-us</language>
        <itunes:author>Soulfra</itunes:author>
        <itunes:category text="Technology"/>
        {items_xml}
    </channel>
</rss>
"""
    return rss_xml


def generate_root_index():
    """Generate root index with navigation to blog"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soulfra - Privacy-First AI Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            padding: 60px 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 600px;
        }

        h1 {
            font-size: 4em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }

        p {
            font-size: 1.3em;
            color: #666;
            margin-bottom: 40px;
        }

        .nav {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .nav a {
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .nav a:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Soulfra</h1>
        <p>Privacy-First AI Platform</p>

        <div class="nav">
            <a href="blog/">Blog</a>
            <a href="about.html">About</a>
            <a href="http://192.168.1.87:5001/chat">Chat</a>
        </div>
    </div>
</body>
</html>
"""
    return html


def publish():
    """Main publishing workflow"""
    print("=" * 70)
    print("📝 Publishing Blog Posts to GitHub Pages")
    print("=" * 70)
    print()

    # Get posts from database
    print("Step 1: Loading posts from database...")
    posts = get_posts_from_db()
    print(f"   Found {len(posts)} post(s)")
    print()

    # Create posts directory
    print("Step 2: Creating posts directory...")
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"   Directory: {POSTS_DIR}")
    print()

    # Generate HTML for each post
    print("Step 3: Generating static HTML...")
    for post in posts:
        html = generate_post_html(post)
        post_file = POSTS_DIR / f"{post['slug']}.html"

        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"   ✅ Generated: {post_file.name}")
    print()

    # Generate blog/index.html
    print("Step 4: Generating blog index...")
    blog_index_html = generate_index_html(posts)
    blog_index_file = BLOG_DIR / "index.html"

    with open(blog_index_file, 'w', encoding='utf-8') as f:
        f.write(blog_index_html)

    print(f"   ✅ Generated: blog/index.html")
    print()

    # Generate root index with link to blog
    print("Step 5: Generating root index...")
    root_index_html = generate_root_index()
    root_index_file = GITHUB_REPO_PATH / "index.html"

    with open(root_index_file, 'w', encoding='utf-8') as f:
        f.write(root_index_html)

    print(f"   ✅ Generated: index.html")
    print()

    # Generate RSS feed
    print("Step 6: Generating RSS feed...")
    rss_xml = generate_rss_feed(posts)
    rss_file = GITHUB_REPO_PATH / "feed.xml"

    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write(rss_xml)

    print(f"   ✅ Generated: feed.xml")
    print()

    # Git commands
    print("Step 7: Pushing to GitHub...")

    try:
        # Change to repo directory
        subprocess.run(['git', 'add', 'blog/', 'index.html', 'feed.xml'], cwd=GITHUB_REPO_PATH, check=True)

        commit_msg = f"Update blog: {posts[0]['title']} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=GITHUB_REPO_PATH, check=True)

        subprocess.run(['git', 'push', 'origin', 'main'], cwd=GITHUB_REPO_PATH, check=True)

        print("   ✅ Pushed to GitHub!")
        print()

        print("=" * 70)
        print("✅ SUCCESS! Blog published to GitHub Pages")
        print("=" * 70)
        print()
        print("📍 Live URLs:")
        print(f"   - Home: https://soulfra.github.io/soulfra/")
        print(f"   - Blog: https://soulfra.github.io/soulfra/blog/")
        for post in posts[:5]:  # Show first 5 posts
            print(f"   - {post['title']}: https://soulfra.github.io/soulfra/blog/posts/{post['slug']}.html")
        print()
        print("⏰ Wait ~30 seconds for GitHub Pages to build, then visit the URLs above")
        print()

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Git error: {e}")
        print()
        print("Manual steps:")
        print(f"   cd {GITHUB_REPO_PATH}")
        print("   git add posts/ index.html")
        print("   git commit -m 'Update blog'")
        print("   git push origin main")
        print()


if __name__ == '__main__':
    publish()

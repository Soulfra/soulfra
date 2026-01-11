#!/usr/bin/env python3
"""
Multi-Brand Publisher
Publishes all brands from database to their respective GitHub repos

Usage:
    python3 publish_all_brands.py              # Publish all brands
    python3 publish_all_brands.py soulfra      # Publish specific brand
"""

import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Paths
DB_PATH = "soulfra.db"
GITHUB_REPOS_BASE = Path("/Users/matthewmauer/Desktop/roommate-chat/github-repos")

# Brand → GitHub repo mapping
BRAND_REPOS = {
    'soulfra': 'soulfra',
    'calriven': 'calriven',
    'deathtodata': 'deathtodata',
    'howtocookathome': 'howtocookathome',  # Not in github-repos yet
    'stpetepros': 'stpetepros',             # Not in github-repos yet
    'hollowtown': 'hollowtown',             # Not in github-repos yet
    'oofbox': 'oofbox',                     # Not in github-repos yet
    'niceleak': 'niceleak',                 # Not in github-repos yet
    'dealordelete': 'dealordelete-site',
    'finishthisrepo': 'finishthisrepo-site',
    'mascotrooms': 'mascotrooms-site',
    'saveorsink': 'saveorsink-site',
    'sellthismvp': 'sellthismvp-site',
    'shiprekt': 'shiprekt-site',
}


def get_brand_info():
    """Get all brands from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    brands = cursor.execute('''
        SELECT id, name, slug, domain, tagline, color_primary, color_secondary, emoji
        FROM brands
        ORDER BY name
    ''').fetchall()

    conn.close()
    return [dict(brand) for brand in brands]


def get_posts_for_brand(brand_id):
    """Get all posts for a specific brand"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    posts = cursor.execute('''
        SELECT * FROM posts
        WHERE brand_id = ?
        ORDER BY published_at DESC
    ''', (brand_id,)).fetchall()

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


def generate_post_html(post, brand):
    """Generate HTML for a single post"""
    content_html = markdown_to_html(post['content'])

    author = post.get('author', brand['name'])
    published_date = post.get('published_at', post.get('created_at', 'Unknown date'))

    primary_color = brand.get('color_primary', '#667eea')
    secondary_color = brand.get('color_secondary', '#764ba2')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - {brand['name']}</title>
    <meta name="description" content="{brand.get('tagline', brand['name'])}">

    <style>
        :root {{
            --primary: {primary_color};
            --secondary: {secondary_color};
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
            font-size: 2rem;
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
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        article h1 {{
            color: var(--primary);
            margin-bottom: 1rem;
        }}

        .meta {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #eee;
        }}

        footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 4rem;
        }}

        footer a {{
            color: #ccc;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{brand['name']}</h1>
        <p>{brand.get('tagline', '')}</p>
    </header>

    <nav>
        <a href="../index.html">Home</a>
        <a href="../blog/">Blog</a>
        <a href="../about.html">About</a>
        <a href="../feed.xml">RSS</a>
    </nav>

    <main>
        <article>
            <h1>{post['title']}</h1>
            <div class="meta">
                By {author} | {published_date[:10] if published_date else 'Draft'}
            </div>
            {content_html}
        </article>
    </main>

    <footer>
        <p>&copy; 2025 {brand['name']}. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    return html


def generate_blog_index(posts, brand):
    """Generate blog index page"""
    primary_color = brand.get('color_primary', '#667eea')
    secondary_color = brand.get('color_secondary', '#764ba2')

    posts_html = ""
    for post in posts:
        posts_html += f"""
        <div class="post-card">
            <h2><a href="posts/{post['slug']}.html">{post['title']}</a></h2>
            <p class="excerpt">{post['content'][:200]}...</p>
            <p class="meta">By {post.get('author', brand['name'])} | {post.get('published_at', '')[:10] if post.get('published_at') else 'Draft'}</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog - {brand['name']}</title>

    <style>
        :root {{
            --primary: {primary_color};
            --secondary: {secondary_color};
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

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

        .post-card h2 a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .excerpt {{
            margin: 1rem 0;
        }}

        .meta {{
            color: #666;
            font-size: 0.9rem;
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
        <h1>{brand['name']}</h1>
        <p>{brand.get('tagline', '')}</p>
    </header>

    <nav>
        <a href="../index.html">Home</a>
        <a href="index.html">Blog</a>
        <a href="../about.html">About</a>
        <a href="../feed.xml">RSS</a>
    </nav>

    <main>
        <h1>All Posts</h1>
        {posts_html}
    </main>

    <footer>
        <p>&copy; 2025 {brand['name']}. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    return html


def generate_rss_feed(posts, brand):
    """Generate RSS feed"""
    base_url = f"https://{brand['domain']}" if brand.get('domain') else f"https://Soulfra.github.io/{BRAND_REPOS.get(brand['slug'], brand['slug'])}"

    items = ""
    for post in posts[:10]:  # Latest 10 posts
        pub_date = post.get('published_at', datetime.now().isoformat())
        items += f"""
        <item>
            <title>{post['title']}</title>
            <link>{base_url}/blog/posts/{post['slug']}.html</link>
            <description>{post['content'][:200]}...</description>
            <pubDate>{pub_date}</pubDate>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{brand['name']}</title>
        <link>{base_url}</link>
        <description>{brand.get('tagline', brand['name'])}</description>
        {items}
    </channel>
</rss>
"""
    return rss


def publish_brand(brand):
    """Publish a single brand to GitHub Pages"""
    brand_slug = brand['slug'].lower()
    repo_name = BRAND_REPOS.get(brand_slug)

    if not repo_name:
        print(f"⚠️  No GitHub repo mapping for {brand['name']} ({brand_slug})")
        return False

    repo_path = GITHUB_REPOS_BASE / repo_name

    if not repo_path.exists():
        print(f"❌ GitHub repo not found: {repo_path}")
        return False

    print(f"\n{'='*70}")
    print(f"📦 Publishing: {brand['name']}")
    print(f"{'='*70}")

    # Get posts
    posts = get_posts_for_brand(brand['id'])
    print(f"Found {len(posts)} posts")

    if len(posts) == 0:
        print(f"⚠️  No posts for {brand['name']}, skipping")
        return False

    # Create directories
    blog_dir = repo_path / "blog"
    posts_dir = blog_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    # Generate post HTML files
    for post in posts:
        post_html = generate_post_html(post, brand)
        post_file = posts_dir / f"{post['slug']}.html"
        post_file.write_text(post_html)
        print(f"  ✓ Generated: {post['slug']}.html")

    # Generate blog index
    blog_index_html = generate_blog_index(posts, brand)
    (blog_dir / "index.html").write_text(blog_index_html)
    print(f"  ✓ Generated: blog/index.html")

    # Generate RSS feed
    rss_feed = generate_rss_feed(posts, brand)
    (repo_path / "feed.xml").write_text(rss_feed)
    print(f"  ✓ Generated: feed.xml")

    # Create CNAME if custom domain exists
    if brand.get('domain'):
        cname_file = repo_path / "CNAME"
        cname_file.write_text(brand['domain'])
        print(f"  ✓ Generated: CNAME ({brand['domain']})")

    # Git commit and push
    try:
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        subprocess.run([
            'git', 'commit', '-m',
            f'Publish {len(posts)} posts for {brand["name"]}\n\n🤖 Generated with Multi-Brand Publisher'
        ], cwd=repo_path, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_path, check=True)
        print(f"  ✓ Pushed to GitHub")
        print(f"\n🎉 {brand['name']} published successfully!")

        if brand.get('domain'):
            print(f"🌐 Live at: https://{brand['domain']}")
        else:
            print(f"🌐 Live at: https://Soulfra.github.io/{repo_name}/")

        return True

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git error: {e}")
        return False


def main():
    """Main function"""
    print("\n🚀 Multi-Brand Publisher")
    print("="*70)

    # Get all brands
    brands = get_brand_info()
    print(f"Found {len(brands)} brands in database\n")

    # Check if specific brand requested
    if len(sys.argv) > 1:
        target_slug = sys.argv[1].lower()
        brands = [b for b in brands if b['slug'].lower() == target_slug]
        if not brands:
            print(f"❌ Brand '{target_slug}' not found")
            sys.exit(1)

    # Publish each brand
    success_count = 0
    for brand in brands:
        if publish_brand(brand):
            success_count += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 Summary: {success_count}/{len(brands)} brands published successfully")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Static Site Exporter - Export Flask to GitHub Pages

Exports each brand/domain to static HTML with embedded JavaScript
for API calls to handle dynamic features (email capture, comments, auth).

Usage:
    python3 export_static.py              # Export all brands
    python3 export_static.py --brand howtocookathome  # Export one brand
    python3 export_static.py --output-dir ./sites  # Custom output directory

Architecture:
    - Static HTML/CSS/JS → GitHub Pages (free)
    - Dynamic features → api.howtocookathome.com (central platform)
    - JavaScript calls API for: comments, email capture, auth

White-Label Mode:
    All exported sites connect back to howtocookathome.com API.
    Deploy sites to any platform (GitHub Pages, Vercel, Netlify).
"""

import os
import sys
import shutil
import re
from pathlib import Path
from database import get_db
import markdown2


def get_all_brands():
    """Get all brands from database"""
    db = get_db()
    brands = db.execute('SELECT * FROM brands ORDER BY name').fetchall()
    db.close()
    return [dict(b) for b in brands]


def get_brand_posts(brand_slug):
    """Get all posts for a brand"""
    db = get_db()

    # First get brand_id from slug
    brand = db.execute('SELECT id FROM brands WHERE slug = ?', (brand_slug,)).fetchone()
    if not brand:
        db.close()
        return []

    brand_id = brand['id']

    # Get posts for this brand
    posts = db.execute('''
        SELECT p.* FROM posts p
        WHERE p.brand_id = ?
        ORDER BY p.published_at DESC
    ''', (brand_id,)).fetchall()
    db.close()
    return [dict(p) for p in posts]


def get_post_comments(post_id):
    """Get all comments for a post"""
    db = get_db()
    comments = db.execute('''
        SELECT c.*, u.username, u.display_name, u.is_ai_persona
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.id ASC
    ''', (post_id,)).fetchall()
    db.close()
    return [dict(c) for c in comments]


def generate_html_template(brand, base_path=""):
    """Generate base HTML template for a brand

    Args:
        brand: Brand dict with name, tagline, colors, etc.
        base_path: Path prefix for links (e.g., "" for root, ".." for post/ directory)
    """
    # Add trailing slash if base_path is not empty and doesn't end with /
    if base_path and not base_path.endswith('/'):
        base_path = base_path + '/'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ title }}}} - {brand['name']}</title>
    <meta name="description" content="{brand['tagline']}">

    <!-- Brand Colors -->
    <style>
        :root {{
            --primary: {brand['color_primary']};
            --secondary: {brand['color_secondary']};
            --accent: {brand['color_accent']};
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        }}

        article .meta {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        article .content {{
            margin-top: 1.5rem;
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

        .email-capture {{
            background: var(--secondary);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            text-align: center;
            margin: 2rem 0;
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
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{brand['name']}</h1>
        <p>{brand['tagline']}</p>
    </header>

    <nav>
        <a href="{base_path}index.html">Home</a>
        <a href="{base_path}feed.xml">RSS Feed</a>
        <a href="{base_path}about.html">About</a>
    </nav>

    <main>
        {{{{ content }}}}
    </main>

    <footer>
        <p>&copy; 2024 {brand['name']} - All rights reserved</p>
        <p>Powered by Soulfra</p>
    </footer>

    <!-- API Integration -->
    <script>
        // Central API - all deployed sites call back to howtocookathome.com
        const API_BASE = 'https://api.howtocookathome.com';
        const BRAND_SLUG = '{brand['slug']}';

        // Email capture
        async function captureEmail(email) {{
            const response = await fetch(`${{API_BASE}}/api/email-capture`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ email, brand_slug: BRAND_SLUG }})
            }});
            return response.json();
        }}

        // Post comment
        async function postComment(post_id, content, author_name) {{
            const response = await fetch(`${{API_BASE}}/api/comments`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ post_id, content, author_name, brand_slug: BRAND_SLUG }})
            }});
            return response.json();
        }}
    </script>
</body>
</html>'''


def generate_index_page(brand, posts):
    """Generate index.html for a brand"""
    posts_html = []

    for post in posts[:10]:  # Show latest 10
        # Smart truncation: full sentences up to ~500 chars
        content = post['content']
        if len(content) > 500:
            # Find last period before 500 chars
            truncate_at = content.rfind('.', 0, 500)
            if truncate_at > 100:  # Make sure we got a reasonable amount
                content = content[:truncate_at + 1]
            else:
                # No period found, just truncate at word boundary
                content = content[:500].rsplit(' ', 1)[0] + '...'

        posts_html.append(f'''
        <article>
            <h2><a href="post/{post['slug']}.html">{post['title']}</a></h2>
            <div class="meta">
                Posted on {post['published_at'][:10]}
            </div>
            <div class="content">
                {markdown2.markdown(content)}
            </div>
            <p><a href="post/{post['slug']}.html">Read more →</a></p>
        </article>
        ''')

    # Email capture section
    email_section = f'''
    <div class="email-capture">
        <h2>Subscribe for Updates</h2>
        <p>Get new posts delivered to your inbox</p>
        <form id="email-form" onsubmit="handleEmailSubmit(event)">
            <input type="email" placeholder="your@email.com" required id="email-input">
            <button type="submit">Subscribe</button>
        </form>
        <p id="email-message" style="margin-top: 1rem;"></p>
    </div>

    <script>
        async function handleEmailSubmit(e) {{
            e.preventDefault();
            const email = document.getElementById('email-input').value;
            const msg = document.getElementById('email-message');

            try {{
                const result = await captureEmail(email);
                msg.textContent = result.message || 'Subscribed!';
                msg.style.color = '#4CAF50';
                document.getElementById('email-input').value = '';
            }} catch (err) {{
                msg.textContent = 'Error subscribing. Please try again.';
                msg.style.color = '#f44336';
            }}
        }}
    </script>
    '''

    content = '\n'.join(posts_html) + email_section

    # Root level page uses empty base_path (relative links like feed.xml, post/foo.html)
    template = generate_html_template(brand, base_path="")
    return template.replace('{{ title }}', 'Home').replace('{{ content }}', content)


def extract_and_save_images(content, site_dir, brand_id):
    """
    Extract /i/<hash> image references and save them as files

    Args:
        content: Markdown content with /i/<hash> refs
        site_dir: Output site directory path
        brand_id: Brand ID for filtering images

    Returns:
        Updated content with images/ paths
    """
    # Find all /i/<hash> references
    image_pattern = r'!\[([^\]]*)\]\(/i/([a-f0-9]+)\)'
    matches = re.findall(image_pattern, content)

    if not matches:
        return content

    # Create images directory
    images_dir = site_dir / 'images'
    images_dir.mkdir(exist_ok=True)

    db = get_db()
    images_saved = 0

    for alt_text, image_hash in matches:
        # Query database for image
        image = db.execute('''
            SELECT data, mime_type
            FROM images
            WHERE hash = ?
        ''', (image_hash,)).fetchone()

        if image:
            # Determine file extension from mime type
            ext = 'png'  # Default
            if image['mime_type'] == 'image/jpeg':
                ext = 'jpg'
            elif image['mime_type'] == 'image/gif':
                ext = 'gif'

            # Save image file
            image_path = images_dir / f"{image_hash}.{ext}"
            with open(image_path, 'wb') as f:
                f.write(image['data'])

            # Update content to use relative path
            old_ref = f'![{alt_text}](/i/{image_hash})'
            new_ref = f'![{alt_text}](images/{image_hash}.{ext})'
            content = content.replace(old_ref, new_ref)

            images_saved += 1

    db.close()

    if images_saved > 0:
        print(f"   📸 Extracted {images_saved} image(s) to images/")

    return content


def generate_post_page(brand, post, comments, site_dir):
    """Generate post page HTML"""
    comments_html = []

    for comment in comments:
        ai_badge = ''
        if comment.get('is_ai_persona'):
            ai_badge = '<span class="ai-badge">AI</span>'

        author = comment.get('display_name') or comment.get('username') or 'Anonymous'

        comments_html.append(f'''
        <div class="comment">
            <div class="author">{author}{ai_badge}</div>
            <div>{comment['content']}</div>
        </div>
        ''')

    comments_section = ''
    if comments_html:
        comments_section = f'''
        <div class="comments">
            <h3>Comments ({len(comments)})</h3>
            {''.join(comments_html)}
        </div>
        '''

    # Extract images from DB and update content
    processed_content = extract_and_save_images(post['content'], site_dir, brand['id'])

    content = f'''
    <article>
        <h1>{post['title']}</h1>
        <div class="meta">Posted on {post['published_at'][:10]}</div>
        <div class="content">
            {markdown2.markdown(processed_content)}
        </div>
        {comments_section}
    </article>
    '''

    # Post pages are in post/ directory, so use .. to go up one level
    template = generate_html_template(brand, base_path="..")
    return template.replace('{{ title }}', post['title']).replace('{{ content }}', content)


def generate_rss_feed(brand, posts):
    """Generate RSS feed for podcast"""
    items = []

    for post in posts[:20]:  # Latest 20
        # Use full content for RSS (readers can handle it)
        # Wrap in CDATA to prevent XML parsing issues
        description_html = markdown2.markdown(post['content'])

        items.append(f'''
        <item>
            <title>{post['title']}</title>
            <link>https://{brand['slug']}.com/post/{post['slug']}.html</link>
            <description><![CDATA[{description_html}]]></description>
            <pubDate>{post['published_at']}</pubDate>
            <guid>https://{brand['slug']}.com/post/{post['slug']}.html</guid>
        </item>
        ''')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
    <channel>
        <title>{brand['name']}</title>
        <link>https://{brand['slug']}.com</link>
        <description>{brand['tagline']}</description>
        <language>en-us</language>
        <itunes:author>{brand['name']}</itunes:author>
        <itunes:category text="{brand['category'].title()}"/>
        {''.join(items)}
    </channel>
</rss>'''


def export_brand_to_static(brand_slug, output_dir='output'):
    """
    Export a single brand to static HTML

    Args:
        brand_slug: Brand slug to export
        output_dir: Base output directory

    Returns:
        True if successful
    """
    print(f"\n📦 Exporting: {brand_slug}")

    # Get brand
    db = get_db()
    brand = db.execute('SELECT * FROM brands WHERE slug = ?', (brand_slug,)).fetchone()
    db.close()

    if not brand:
        print(f"   ❌ Brand not found: {brand_slug}")
        return False

    brand = dict(brand)

    # Create output directory
    site_dir = Path(output_dir) / brand_slug
    site_dir.mkdir(parents=True, exist_ok=True)

    # Create post directory
    post_dir = site_dir / 'post'
    post_dir.mkdir(exist_ok=True)

    # Get posts
    posts = get_brand_posts(brand_slug)
    print(f"   📄 Found {len(posts)} post(s)")

    # Generate index.html
    index_html = generate_index_page(brand, posts)
    (site_dir / 'index.html').write_text(index_html)
    print(f"   ✅ Created index.html")

    # Generate post pages
    for post in posts:
        comments = get_post_comments(post['id'])
        post_html = generate_post_page(brand, post, comments, site_dir)
        (post_dir / f"{post['slug']}.html").write_text(post_html)

    print(f"   ✅ Created {len(posts)} post page(s)")

    # Generate RSS feed
    rss_xml = generate_rss_feed(brand, posts)
    (site_dir / 'feed.xml').write_text(rss_xml)
    print(f"   ✅ Created feed.xml")

    # Create CNAME file for GitHub Pages
    (site_dir / 'CNAME').write_text(f"{brand_slug}.com")
    print(f"   ✅ Created CNAME")

    # Create README
    readme = f"""# {brand['name']}

{brand['tagline']}

**Category**: {brand['category']}

## Deployment

This site is deployed to GitHub Pages.

Domain: https://{brand_slug}.com

## Architecture

- **Static Site**: GitHub Pages (free)
- **API Server**: api.soulfra.com (shared)
- **Database**: SQLite on API server

## Build

Generated from Soulfra multi-site generator:
```bash
python3 export_static.py --brand {brand_slug}
```
"""
    (site_dir / 'README.md').write_text(readme)
    print(f"   ✅ Created README.md")

    print(f"   📁 Output: {site_dir}")
    print(f"   🌐 Ready for GitHub Pages")

    return True


def export_all_brands(output_dir='output'):
    """Export all brands to static HTML"""
    print("=" * 70)
    print("📦 STATIC SITE EXPORTER")
    print("=" * 70)
    print()

    brands = get_all_brands()

    if not brands:
        print("❌ No brands found in database")
        return 0

    print(f"📋 Found {len(brands)} brand(s)")

    exported = 0
    for brand in brands:
        try:
            if export_brand_to_static(brand['slug'], output_dir):
                exported += 1
        except Exception as e:
            print(f"   ❌ Export failed: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"✅ Exported {exported}/{len(brands)} site(s)")
    print("=" * 70)
    print()

    if exported > 0:
        print("Next steps:")
        print(f"  1. cd {output_dir}/<brand-slug>")
        print("  2. git init")
        print("  3. git add .")
        print("  4. git commit -m 'Initial commit'")
        print("  5. gh repo create <brand-slug> --public --source=. --push")
        print("  6. Enable GitHub Pages in repo settings")
        print("  7. Point domain DNS to GitHub Pages")
        print()

    return exported


def main():
    """CLI for static site exporter"""

    output_dir = 'output'
    specific_brand = None

    # Parse arguments
    if '--output-dir' in sys.argv:
        idx = sys.argv.index('--output-dir')
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]

    if '--brand' in sys.argv:
        idx = sys.argv.index('--brand')
        if idx + 1 < len(sys.argv):
            specific_brand = sys.argv[idx + 1]

    if '--help' in sys.argv:
        print(__doc__)
        return

    if specific_brand:
        export_brand_to_static(specific_brand, output_dir)
    else:
        export_all_brands(output_dir)


if __name__ == '__main__':
    main()

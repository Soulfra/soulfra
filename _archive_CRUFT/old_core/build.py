#!/usr/bin/env python3
"""
Static Site Builder - OSS Style for GitHub Pages
Converts Markdown posts + docs → HTML → GitHub Pages

Builds:
  1. Blog posts from database → /docs/post/*.html
  2. Markdown documentation → /docs/docs/*.html
  3. Documentation index → /docs/docs/index.html
  4. Embeddable widget → /docs/widget-embed.js
  5. RSS feed → /docs/feed.xml

Usage:
  python build.py              # Build entire site
  python build.py --watch      # Rebuild on file changes (TODO)
  python build.py --serve      # Serve locally on port 8000
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import markdown2
from database import get_db
import json


# Paths
POSTS_DIR = Path('posts')
TEMPLATES_DIR = Path('templates')
OUTPUT_DIR = Path('docs')  # GitHub Pages serves from /docs
STATIC_DIR = Path('static')

# Site configuration
SITE_CONFIG = {
    'title': 'Soulfra Platform',
    'description': 'Multi-brand architecture with unified accounts',
    'url': 'https://YOUR_USERNAME.github.io/YOUR_REPO',  # Update for GitHub Pages
    'brands': {
        'deathtodata': 'DeathToData - Privacy & Encryption',
        'soulfra': 'Soulfra - Account Faucet & Profiles',
        'calriven': 'CalRiven - AI Marketplace'
    }
}


def read_template(name):
    """Read HTML template"""
    template_path = TEMPLATES_DIR / f'{name}.html'
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template_name, **kwargs):
    """Simple template rendering (replace {{variables}})"""
    template = read_template(template_name)

    for key, value in kwargs.items():
        template = template.replace(f'{{{{{key}}}}}', str(value))

    return template


def parse_markdown_post(filepath):
    """
    Parse Markdown file with frontmatter

    Expected format:
    ---
    title: Post Title
    slug: post-slug
    date: 2025-12-20
    ---

    Markdown content here...
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter and content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            markdown_content = parts[2].strip()
        else:
            frontmatter = ''
            markdown_content = content
    else:
        frontmatter = ''
        markdown_content = content

    # Parse frontmatter
    metadata = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    # Convert Markdown to HTML
    html_content = markdown2.markdown(
        markdown_content,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline', 'header-ids']
    )

    return {
        'title': metadata.get('title', 'Untitled'),
        'slug': metadata.get('slug', ''),
        'date': metadata.get('date', ''),
        'content': html_content,
        'metadata': metadata
    }


def get_posts_from_db():
    """Get all published posts from database"""
    db = get_db()
    posts = db.execute('''
        SELECT id, slug, title, content, published_at
        FROM posts
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
    ''').fetchall()
    db.close()
    return [dict(p) for p in posts]


def build_index_page(posts):
    """Build homepage with recent posts"""
    print("📄 Building index.html...")

    # Generate posts HTML
    posts_html = ''
    for post in posts[:10]:  # Show 10 most recent
        # Format date
        published_at = post.get('published_at', '')
        if isinstance(published_at, str):
            date_str = published_at.split(' ')[0]  # Get date part
        else:
            date_str = published_at.strftime('%Y-%m-%d') if published_at else ''

        # Truncate content for preview
        content = post.get('content', '')
        # Strip HTML tags for preview
        import re
        content_text = re.sub(r'<[^>]+>', '', content)
        content_preview = content_text[:200] + '...' if len(content_text) > 200 else content_text

        posts_html += f"""
        <article class="post-preview">
          <h2><a href="post/{post['slug']}.html">{post['title']}</a></h2>
          <p class="date">{date_str}</p>
          <div class="excerpt">{content_preview}</div>
        </article>
        """

    # Create simple index page
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SITE_CONFIG['title']}</title>
    <meta name="description" content="{SITE_CONFIG['description']}">
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <header>
        <h1>{SITE_CONFIG['title']}</h1>
        <p>{SITE_CONFIG['description']}</p>
        <nav>
            <a href="docs/index.html">Documentation</a> |
            <a href="subscribe.html">Subscribe</a> |
            <a href="about.html">About</a>
        </nav>
    </header>

    <main>
        <h2>Recent Posts</h2>
        {posts_html if posts_html else '<p>No posts yet.</p>'}
    </main>

    <footer>
        <p>&copy; 2025 Soulfra Platform | <a href="feed.xml">RSS Feed</a></p>
    </footer>
</body>
</html>
"""

    output_path = OUTPUT_DIR / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✅ Created {output_path}")


def build_post_page(post):
    """Build individual post page"""
    slug = post['slug']
    print(f"📄 Building post/{slug}.html...")

    # Format date
    published_at = post.get('published_at', '')
    if isinstance(published_at, str):
        date_str = published_at.split(' ')[0]
    else:
        date_str = published_at.strftime('%Y-%m-%d') if published_at else ''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - {SITE_CONFIG['title']}</title>
    <link rel="stylesheet" href="../static/style.css">
</head>
<body>
    <header>
        <h1><a href="../index.html">{SITE_CONFIG['title']}</a></h1>
        <nav>
            <a href="../docs/index.html">Docs</a> |
            <a href="../index.html">Posts</a>
        </nav>
    </header>

    <main>
        <article class="post">
            <h1>{post['title']}</h1>
            <p class="date">{date_str}</p>
            <div class="content">
                {post['content']}
            </div>
        </article>
    </main>

    <footer>
        <p><a href="../index.html">← Back to posts</a></p>
    </footer>
</body>
</html>
"""

    # Create post directory
    post_dir = OUTPUT_DIR / 'post'
    post_dir.mkdir(exist_ok=True)

    output_path = post_dir / f"{slug}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✅ Created {output_path}")


def build_documentation():
    """Build all .md documentation files to /docs/docs/"""
    print("📚 Building documentation...")

    # Find all .md files in root
    md_files = list(Path('.').glob('*.md'))

    if not md_files:
        print("  ⚠️  No .md files found in root directory")
        return []

    # Create docs output directory
    docs_dir = OUTPUT_DIR / 'docs'
    docs_dir.mkdir(exist_ok=True)

    built_docs = []

    for md_file in md_files:
        filename = md_file.name
        slug = md_file.stem  # Filename without .md extension

        print(f"  📄 Building docs/{slug}.html...")

        # Read and parse markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Convert to HTML
        html_content = markdown2.markdown(
            content,
            extras=['fenced-code-blocks', 'tables', 'header-ids', 'toc']
        )

        # Extract title from first # header or use filename
        title = filename.replace('.md', '').replace('_', ' ').replace('-', ' ')
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break

        # Build doc page
        doc_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Documentation</title>
    <link rel="stylesheet" href="../static/style.css">
    <style>
        .doc-content {{
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
        }}
        .doc-content pre {{
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }}
        .doc-content code {{
            background: #f0f0f0;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: monospace;
        }}
        .doc-content pre code {{
            background: transparent;
            padding: 0;
        }}
        .doc-content table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        .doc-content th, .doc-content td {{
            border: 1px solid #ddd;
            padding: 0.5rem;
            text-align: left;
        }}
        .doc-content th {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <header>
        <h1><a href="../index.html">{SITE_CONFIG['title']}</a></h1>
        <nav>
            <a href="index.html">Docs Home</a> |
            <a href="../index.html">Posts</a>
        </nav>
    </header>

    <main class="doc-content">
        {html_content}
    </main>

    <footer>
        <p><a href="index.html">← Back to documentation</a></p>
    </footer>
</body>
</html>
"""

        output_path = docs_dir / f"{slug}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc_html)

        built_docs.append({
            'title': title,
            'slug': slug,
            'filename': filename
        })

        print(f"    ✅ Created {output_path}")

    return built_docs


def build_docs_index(docs):
    """Build documentation index page"""
    print("📚 Building docs/index.html...")

    # Group docs by category (heuristic)
    categories = {
        'Architecture': [],
        'Guides': [],
        'Setup': [],
        'Other': []
    }

    for doc in docs:
        title_lower = doc['title'].lower()
        if 'architecture' in title_lower or 'vision' in title_lower:
            categories['Architecture'].append(doc)
        elif 'guide' in title_lower or 'quickstart' in title_lower:
            categories['Guides'].append(doc)
        elif 'setup' in title_lower or 'deployment' in title_lower or 'email' in title_lower:
            categories['Setup'].append(doc)
        else:
            categories['Other'].append(doc)

    # Build category sections
    docs_html = ''
    for category, category_docs in categories.items():
        if not category_docs:
            continue

        docs_html += f'<h2>{category}</h2><ul>'
        for doc in sorted(category_docs, key=lambda d: d['title']):
            docs_html += f'<li><a href="{doc["slug"]}.html">{doc["title"]}</a></li>'
        docs_html += '</ul>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation - {SITE_CONFIG['title']}</title>
    <link rel="stylesheet" href="../static/style.css">
</head>
<body>
    <header>
        <h1><a href="../index.html">{SITE_CONFIG['title']}</a></h1>
        <nav>
            <a href="../index.html">Home</a> |
            <a href="index.html">Documentation</a>
        </nav>
    </header>

    <main style="max-width: 800px; margin: 0 auto; padding: 2rem;">
        <h1>📚 Documentation</h1>
        <p>Complete documentation for the Soulfra multi-brand platform.</p>

        {docs_html}

        <hr>
        <h2>Key Concepts</h2>
        <ul>
            <li><strong>ReadTheDocs-Style Architecture</strong>: Multi-subdomain setup (app., ref., org.) with unified accounts</li>
            <li><strong>Keyring Unlocks</strong>: RuneScape-style permanent feature access</li>
            <li><strong>Three Brands</strong>: DeathToData (privacy), Soulfra (accounts), CalRiven (AI)</li>
            <li><strong>QR Authentication</strong>: Passwordless signup via QR faucet</li>
        </ul>
    </main>

    <footer>
        <p>&copy; 2025 Soulfra Platform</p>
    </footer>
</body>
</html>
"""

    output_path = OUTPUT_DIR / 'docs' / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✅ Created {output_path}")


def build_embeddable_widget():
    """Create widget-embed.js for iframe embedding"""
    print("🔌 Building widget-embed.js...")

    widget_js = """/**
 * Soulfra Embeddable Widget
 *
 * Usage:
 *   <script src="https://YOUR_USERNAME.github.io/YOUR_REPO/widget-embed.js"></script>
 *   <div id="soulfra-widget" data-brand="deathtodata"></div>
 *
 * Options:
 *   data-brand: "deathtodata" | "soulfra" | "calriven"
 *   data-width: Width in pixels (default: "400px")
 *   data-height: Height in pixels (default: "600px")
 */

(function() {
  'use strict';

  const WIDGET_BASE_URL = 'https://YOUR_USERNAME.github.io/YOUR_REPO';

  function initSoulfraWidget() {
    const containers = document.querySelectorAll('#soulfra-widget');

    containers.forEach(container => {
      const brand = container.getAttribute('data-brand') || 'soulfra';
      const width = container.getAttribute('data-width') || '400px';
      const height = container.getAttribute('data-height') || '600px';

      // Create iframe
      const iframe = document.createElement('iframe');
      iframe.src = `${WIDGET_BASE_URL}/widget.html?brand=${brand}`;
      iframe.style.width = width;
      iframe.style.height = height;
      iframe.style.border = '1px solid #ccc';
      iframe.style.borderRadius = '8px';
      iframe.setAttribute('frameborder', '0');
      iframe.setAttribute('allowtransparency', 'true');

      // Replace container with iframe
      container.appendChild(iframe);

      console.log(`[Soulfra Widget] Loaded ${brand} widget`);
    });
  }

  // Auto-initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSoulfraWidget);
  } else {
    initSoulfraWidget();
  }

  // Expose for manual initialization
  window.SoulfraWidget = {
    init: initSoulfraWidget
  };
})();
"""

    output_path = OUTPUT_DIR / 'widget-embed.js'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(widget_js)

    print(f"  ✅ Created {output_path}")


def build_static_pages():
    """Build subscribe, about, etc. pages"""
    print("📄 Building static pages...")

    # About page
    about_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - {SITE_CONFIG['title']}</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <header>
        <h1><a href="index.html">{SITE_CONFIG['title']}</a></h1>
        <nav>
            <a href="index.html">Home</a> |
            <a href="docs/index.html">Docs</a> |
            <a href="about.html">About</a>
        </nav>
    </header>

    <main style="max-width: 800px; margin: 0 auto; padding: 2rem;">
        <h1>About Soulfra Platform</h1>
        <p>Multi-brand architecture inspired by ReadTheDocs.org</p>

        <h2>Three Brands, One Account</h2>
        <ul>
            <li><strong>DeathToData</strong>: Privacy & encryption advocacy</li>
            <li><strong>Soulfra</strong>: QR-based account faucet & personality profiles</li>
            <li><strong>CalRiven</strong>: AI agent marketplace & API access</li>
        </ul>

        <h2>Key Features</h2>
        <ul>
            <li>Unified account system across all subdomains</li>
            <li>Keyring unlocks (RuneScape-style permanent access)</li>
            <li>QR code authentication (passwordless)</li>
            <li>Cross-subdomain sessions</li>
        </ul>

        <p><a href="docs/READTHEDOCS_ARCHITECTURE.html">Read the full architecture →</a></p>
    </main>

    <footer>
        <p>&copy; 2025 Soulfra Platform</p>
    </footer>
</body>
</html>
"""

    output_path = OUTPUT_DIR / 'about.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(about_html)

    print(f"  ✅ Created {output_path}")


def copy_static_files():
    """Copy CSS, images, etc. to output directory"""
    print("📁 Copying static files...")

    if not STATIC_DIR.exists():
        print("  ⚠️  No static/ directory found, creating minimal CSS")

        # Create minimal CSS
        output_static = OUTPUT_DIR / 'static'
        output_static.mkdir(exist_ok=True)

        minimal_css = """
body {
    font-family: system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background: #f9f9f9;
}

header {
    background: white;
    padding: 2rem;
    margin-bottom: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

header h1 {
    margin: 0 0 0.5rem 0;
}

header nav {
    margin-top: 1rem;
}

header nav a {
    color: #0066cc;
    text-decoration: none;
    margin-right: 1rem;
}

main {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.post-preview {
    border-bottom: 1px solid #eee;
    padding: 1.5rem 0;
}

.post-preview:last-child {
    border-bottom: none;
}

.post-preview h2 {
    margin: 0 0 0.5rem 0;
}

.post-preview .date {
    color: #666;
    font-size: 0.9rem;
    margin: 0 0 0.5rem 0;
}

.post-preview .excerpt {
    color: #333;
}

footer {
    text-align: center;
    margin-top: 2rem;
    color: #666;
    font-size: 0.9rem;
}
"""

        with open(output_static / 'style.css', 'w') as f:
            f.write(minimal_css)

        print(f"  ✅ Created minimal CSS at {output_static / 'style.css'}")
        return

    output_static = OUTPUT_DIR / 'static'

    # Remove old static files
    if output_static.exists():
        shutil.rmtree(output_static)

    # Copy new static files
    shutil.copytree(STATIC_DIR, output_static)

    print(f"  ✅ Copied static files to {output_static}")


def generate_rss_feed(posts):
    """Generate RSS feed for subscribers"""
    print("📡 Generating RSS feed...")

    rss_items = ''
    for post in posts[:10]:  # Last 10 posts
        published_at = post.get('published_at', '')
        if isinstance(published_at, str):
            date_str = published_at
        else:
            date_str = published_at.strftime('%a, %d %b %Y %H:%M:%S +0000') if published_at else ''

        # Strip HTML for description
        import re
        content_text = re.sub(r'<[^>]+>', '', post.get('content', ''))
        description = content_text[:500] + '...' if len(content_text) > 500 else content_text

        rss_items += f"""
        <item>
          <title>{post['title']}</title>
          <link>{SITE_CONFIG['url']}/post/{post['slug']}.html</link>
          <description>{description}</description>
          <pubDate>{date_str}</pubDate>
          <guid>{SITE_CONFIG['url']}/post/{post['slug']}.html</guid>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_CONFIG['title']}</title>
    <link>{SITE_CONFIG['url']}</link>
    <description>{SITE_CONFIG['description']}</description>
    <language>en-us</language>
    {rss_items}
  </channel>
</rss>
"""

    output_path = OUTPUT_DIR / 'feed.xml'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rss)

    print(f"  ✅ Created {output_path}")


def build_site():
    """Build entire static site"""
    print("🔨 Building Soulfra Platform - OSS Style")
    print("=" * 70)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Get all posts from database
    posts = get_posts_from_db()

    # Build all components
    build_index_page(posts)

    for post in posts:
        build_post_page(post)

    docs = build_documentation()
    build_docs_index(docs)

    build_static_pages()
    build_embeddable_widget()
    copy_static_files()
    generate_rss_feed(posts)

    print("=" * 70)
    print("✅ Build complete!")
    print(f"📊 Built {len(posts)} blog posts")
    print(f"📚 Built {len(docs)} documentation pages")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    print("\nTest locally:")
    print(f"  cd {OUTPUT_DIR} && python3 -m http.server 8000")
    print("  Then visit: http://localhost:8000")
    print("\nDeploy to GitHub Pages:")
    print("  git add docs/ && git commit -m 'Update site' && git push")
    print("\nDon't forget to:")
    print("  1. Enable GitHub Pages in repo settings (deploy from /docs)")
    print(f"  2. Update SITE_CONFIG['url'] in build.py with your GitHub Pages URL")


if __name__ == '__main__':
    import sys

    if '--serve' in sys.argv:
        # Build first
        build_site()

        # Then serve
        print("\n🌐 Starting local server on http://localhost:8000...")
        print("Press Ctrl+C to stop")
        os.chdir(OUTPUT_DIR)
        os.system('python3 -m http.server 8000')

    elif '--watch' in sys.argv:
        print("👀 Watch mode not yet implemented")
        print("For now, just run `python build.py` after making changes")
        sys.exit(1)

    else:
        build_site()

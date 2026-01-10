"""
Static Site Builder
Converts Markdown posts → HTML → GitHub Pages

Usage:
  python build.py              # Build entire site
  python build.py --watch      # Rebuild on file changes
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import markdown2
from database import get_posts, get_post_by_slug, get_stats, init_db


# Paths
POSTS_DIR = Path('posts')
TEMPLATES_DIR = Path('templates')
OUTPUT_DIR = Path('docs')  # GitHub Pages serves from /docs
STATIC_DIR = Path('static')


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
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )

    return {
        'title': metadata.get('title', 'Untitled'),
        'slug': metadata.get('slug', ''),
        'date': metadata.get('date', ''),
        'content': html_content
    }


def build_index_page(posts):
    """Build homepage with recent posts"""
    print("📄 Building index.html...")

    # Generate posts HTML
    posts_html = ''
    for post in posts:
        # Format date
        published_at = post.get('published_at', '')
        if isinstance(published_at, str):
            date_str = published_at.split(' ')[0]  # Get date part
        else:
            date_str = published_at.strftime('%Y-%m-%d') if published_at else ''

        # Truncate content for preview
        content_preview = post['content'][:200] + '...'

        posts_html += f"""
        <article class="post-preview">
          <h2><a href="post/{post['slug']}.html">{post['title']}</a></h2>
          <p class="date">{date_str}</p>
          <div class="excerpt">{content_preview}</div>
        </article>
        """

    html = render_template(
        'index',
        posts=posts_html,
        stats_posts=len(posts)
    )

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

    html = render_template(
        'post',
        title=post['title'],
        date=date_str,
        content=post['content']
    )

    # Create post directory
    post_dir = OUTPUT_DIR / 'post'
    post_dir.mkdir(exist_ok=True)

    output_path = post_dir / f"{slug}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✅ Created {output_path}")


def build_static_pages():
    """Build subscribe, about, etc. pages"""
    print("📄 Building static pages...")

    pages = ['subscribe', 'about', 'unsubscribe']

    for page in pages:
        try:
            html = render_template(page)
            output_path = OUTPUT_DIR / f'{page}.html'

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"  ✅ Created {output_path}")
        except FileNotFoundError:
            print(f"  ⚠️  Template {page}.html not found, skipping")


def copy_static_files():
    """Copy CSS, images, etc. to output directory"""
    print("📁 Copying static files...")

    if not STATIC_DIR.exists():
        print("  ⚠️  No static/ directory found")
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

        rss_items += f"""
        <item>
          <title>{post['title']}</title>
          <link>https://soulfra.github.io/post/{post['slug']}.html</link>
          <description>{post['content'][:500]}...</description>
          <pubDate>{date_str}</pubDate>
          <guid>https://soulfra.github.io/post/{post['slug']}.html</guid>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Soulfra Newsletter</title>
    <link>https://soulfra.github.io</link>
    <description>AI, privacy, and the future</description>
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
    print("🔨 Building Soulfra Simple Newsletter")
    print("=" * 50)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Initialize database if needed
    if not Path('soulfra.db').exists():
        print("⚠️  Database not found, initializing...")
        init_db()

    # Get all posts from database
    posts = get_posts()

    if not posts:
        print("\n⚠️  No posts found in database!")
        print("Add posts by creating Markdown files in posts/ directory")
        print("Then run: python -c 'from database import add_post; add_post(...)'")
        print("\nBuilding site anyway with empty content...")

    # Build pages
    build_index_page(posts)

    for post in posts:
        build_post_page(post)

    build_static_pages()
    copy_static_files()
    generate_rss_feed(posts)

    print("=" * 50)
    print("✅ Build complete!")
    print(f"📊 Built {len(posts)} posts")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    print("\nDeploy:")
    print("  git add docs/ && git commit -m 'Update site' && git push")


if __name__ == '__main__':
    import sys

    if '--watch' in sys.argv:
        print("👀 Watch mode not yet implemented")
        print("For now, just run `python build.py` after making changes")
        sys.exit(1)

    build_site()

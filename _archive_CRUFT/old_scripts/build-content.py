#!/usr/bin/env python3
"""
Build Content - MD/IPYNB → HTML with Caching

Converts markdown files and Jupyter notebooks to static HTML with:
- Merkle tree caching (only rebuild changed files)
- GitHub Pages deployment
- RSS feed generation
- Sitemap generation
- Blog post indexing

This is the final piece of the voice-to-graph pipeline:
1. Record voice memo → transcribe → save as .md
2. build-content.py → converts .md to .html
3. Deploy to GitHub Pages

Usage:
    python3 build-content.py                    # Build all content
    python3 build-content.py --file post.md     # Build single file
    python3 build-content.py --deploy           # Build + deploy to GitHub Pages
"""

import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Directories
CONTENT_DIR = Path("content")  # Source markdown/ipynb
OUTPUT_DIR = Path("dist")      # Built HTML
CACHE_DIR = Path(".cache")     # Merkle tree cache
BLOG_DIR = Path("blog/posts")  # Existing blog posts

# GitHub Pages config
GITHUB_PAGES_REPO = "matthewmauer/soulfra-simple"
GITHUB_PAGES_BRANCH = "gh-pages"

def compute_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of file contents"""
    if not filepath.exists():
        return ""

    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def load_cache() -> Dict[str, str]:
    """Load Merkle tree cache from disk"""
    cache_file = CACHE_DIR / "content_hashes.json"

    if not cache_file.exists():
        return {}

    with open(cache_file) as f:
        return json.load(f)

def save_cache(cache: Dict[str, str]):
    """Save Merkle tree cache to disk"""
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    cache_file = CACHE_DIR / "content_hashes.json"

    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

def markdown_to_html(md_content: str, title: str = "") -> str:
    """
    Convert markdown to HTML

    Uses simple markdown parser (no dependencies)
    """

    # Basic markdown conversions
    html = md_content

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold/italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

    # Code blocks
    html = re.sub(r'```(\w+)?\n(.+?)\n```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Lists
    html = re.sub(r'^\- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)

    # Paragraphs
    lines = html.split('\n')
    paragraphs = []
    current = []

    for line in lines:
        if line.strip().startswith('<') or not line.strip():
            if current:
                paragraphs.append('<p>' + ' '.join(current) + '</p>')
                current = []
            if line.strip():
                paragraphs.append(line)
        else:
            current.append(line.strip())

    if current:
        paragraphs.append('<p>' + ' '.join(current) + '</p>')

    html = '\n'.join(paragraphs)

    # Wrap in HTML template
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #667eea; }}
        h2 {{ color: #764ba2; margin-top: 2rem; }}
        h3 {{ color: #495057; }}
        code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
    </style>
</head>
<body>
    {html}
    <hr>
    <p><small>Built with <a href="/voice-to-graph">Voice to Graph</a></small></p>
</body>
</html>"""

def ipynb_to_html(ipynb_path: Path) -> str:
    """
    Convert Jupyter notebook to HTML

    Extracts markdown cells and code cells with outputs
    """

    with open(ipynb_path) as f:
        notebook = json.load(f)

    html_parts = []

    for cell in notebook.get('cells', []):
        cell_type = cell.get('cell_type')
        source = ''.join(cell.get('source', []))

        if cell_type == 'markdown':
            html_parts.append(markdown_to_html(source))

        elif cell_type == 'code':
            # Code input
            html_parts.append(f'<pre><code class="python">{source}</code></pre>')

            # Code outputs
            outputs = cell.get('outputs', [])
            for output in outputs:
                if output.get('output_type') == 'stream':
                    text = ''.join(output.get('text', []))
                    html_parts.append(f'<pre><code>{text}</code></pre>')

                elif output.get('output_type') == 'execute_result':
                    data = output.get('data', {})
                    text = data.get('text/plain', '')
                    if isinstance(text, list):
                        text = ''.join(text)
                    html_parts.append(f'<pre><code>{text}</code></pre>')

    title = ipynb_path.stem.replace('-', ' ').replace('_', ' ').title()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #667eea; }}
        h2 {{ color: #764ba2; margin-top: 2rem; }}
        pre {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        code {{
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {''.join(html_parts)}
    <hr>
    <p><small>Jupyter notebook converted by <a href="/voice-to-graph">Voice to Graph</a></small></p>
</body>
</html>"""

def build_file(filepath: Path, force: bool = False) -> Optional[Path]:
    """
    Build single file (markdown or ipynb) to HTML

    Returns output path if built, None if skipped (cached)
    """

    # Check cache
    cache = load_cache()
    current_hash = compute_hash(filepath)
    cached_hash = cache.get(str(filepath), "")

    if current_hash == cached_hash and not force:
        print(f"⏭️  Skipped (cached): {filepath.name}")
        return None

    print(f"🔨 Building: {filepath.name}")

    # Determine output path
    output_path = OUTPUT_DIR / filepath.relative_to(CONTENT_DIR).with_suffix('.html')
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Convert to HTML
    if filepath.suffix == '.md':
        with open(filepath) as f:
            md_content = f.read()
        title = filepath.stem.replace('-', ' ').replace('_', ' ').title()
        html = markdown_to_html(md_content, title)

    elif filepath.suffix == '.ipynb':
        html = ipynb_to_html(filepath)

    else:
        print(f"⚠️  Unknown file type: {filepath.suffix}")
        return None

    # Write HTML
    with open(output_path, 'w') as f:
        f.write(html)

    # Update cache
    cache[str(filepath)] = current_hash
    save_cache(cache)

    print(f"✅ Built: {output_path}")
    return output_path

def build_all(force: bool = False):
    """Build all content files"""

    print("📦 Building all content...")

    # Find all markdown and notebook files
    md_files = list(CONTENT_DIR.glob("**/*.md"))
    ipynb_files = list(CONTENT_DIR.glob("**/*.ipynb"))
    all_files = md_files + ipynb_files

    print(f"   Found {len(md_files)} markdown files, {len(ipynb_files)} notebooks")

    # Build each file
    built_count = 0
    for filepath in all_files:
        result = build_file(filepath, force=force)
        if result:
            built_count += 1

    print(f"\n✅ Built {built_count} files (skipped {len(all_files) - built_count} cached)")

    # Generate index
    generate_index()

    # Generate RSS feed
    generate_rss()

    # Generate sitemap
    generate_sitemap()

def generate_index():
    """Generate index.html listing all posts"""

    print("\n📋 Generating index...")

    html_files = list(OUTPUT_DIR.glob("**/*.html"))
    posts = []

    for html_file in html_files:
        if html_file.name == 'index.html':
            continue

        # Extract title from HTML
        with open(html_file) as f:
            content = f.read()
            title_match = re.search(r'<title>(.+?)</title>', content)
            title = title_match.group(1) if title_match else html_file.stem

        # Get modified time
        modified = datetime.fromtimestamp(html_file.stat().st_mtime)

        posts.append({
            'title': title,
            'path': str(html_file.relative_to(OUTPUT_DIR)),
            'modified': modified
        })

    # Sort by modified date
    posts.sort(key=lambda p: p['modified'], reverse=True)

    # Generate index HTML
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Index</title>
    <style>
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #667eea; }}
        .post {{
            border-bottom: 1px solid #dee2e6;
            padding: 20px 0;
        }}
        .post h2 {{
            margin: 0 0 10px 0;
        }}
        .post a {{
            color: #667eea;
            text-decoration: none;
            font-size: 1.3rem;
        }}
        .post a:hover {{
            text-decoration: underline;
        }}
        .post .date {{
            color: #6c757d;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <h1>📚 Content Index</h1>
    <p><strong>{len(posts)}</strong> posts</p>
"""

    for post in posts:
        index_html += f"""
    <div class="post">
        <h2><a href="/{post['path']}">{post['title']}</a></h2>
        <p class="date">{post['modified'].strftime('%B %d, %Y')}</p>
    </div>
"""

    index_html += """
</body>
</html>"""

    with open(OUTPUT_DIR / 'index.html', 'w') as f:
        f.write(index_html)

    print(f"✅ Generated index with {len(posts)} posts")

def generate_rss():
    """Generate RSS feed"""

    print("\n📡 Generating RSS feed...")

    html_files = list(OUTPUT_DIR.glob("**/*.html"))
    posts = []

    for html_file in html_files:
        if html_file.name == 'index.html':
            continue

        with open(html_file) as f:
            content = f.read()
            title_match = re.search(r'<title>(.+?)</title>', content)
            title = title_match.group(1) if title_match else html_file.stem

        modified = datetime.fromtimestamp(html_file.stat().st_mtime)

        posts.append({
            'title': title,
            'path': str(html_file.relative_to(OUTPUT_DIR)),
            'modified': modified
        })

    posts.sort(key=lambda p: p['modified'], reverse=True)

    # Generate RSS XML
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Soulfra Blog</title>
        <link>https://soulfra.com</link>
        <description>Voice-to-graph content system</description>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
"""

    for post in posts[:20]:  # Last 20 posts
        rss += f"""
        <item>
            <title>{post['title']}</title>
            <link>https://soulfra.com/{post['path']}</link>
            <pubDate>{post['modified'].strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
        </item>
"""

    rss += """
    </channel>
</rss>"""

    with open(OUTPUT_DIR / 'feed.xml', 'w') as f:
        f.write(rss)

    print(f"✅ Generated RSS feed with {len(posts[:20])} items")

def generate_sitemap():
    """Generate sitemap.xml for SEO"""

    print("\n🗺️  Generating sitemap...")

    html_files = list(OUTPUT_DIR.glob("**/*.html"))

    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

    for html_file in html_files:
        path = str(html_file.relative_to(OUTPUT_DIR))
        modified = datetime.fromtimestamp(html_file.stat().st_mtime)

        sitemap += f"""
    <url>
        <loc>https://soulfra.com/{path}</loc>
        <lastmod>{modified.strftime('%Y-%m-%d')}</lastmod>
    </url>
"""

    sitemap += """
</urlset>"""

    with open(OUTPUT_DIR / 'sitemap.xml', 'w') as f:
        f.write(sitemap)

    print(f"✅ Generated sitemap with {len(html_files)} URLs")

def deploy_to_github_pages():
    """Deploy dist/ to GitHub Pages"""

    print("\n🚀 Deploying to GitHub Pages...")

    # Check if dist/ exists
    if not OUTPUT_DIR.exists():
        print("❌ No dist/ directory - run build first")
        return

    # Check if gh-pages branch exists
    try:
        subprocess.run(['git', 'rev-parse', '--verify', GITHUB_PAGES_BRANCH],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"Creating {GITHUB_PAGES_BRANCH} branch...")
        subprocess.run(['git', 'checkout', '--orphan', GITHUB_PAGES_BRANCH], check=True)
        subprocess.run(['git', 'rm', '-rf', '.'], check=True)

    # Copy dist/ to root
    subprocess.run(['cp', '-r', f'{OUTPUT_DIR}/*', '.'], shell=True, check=True)

    # Commit and push
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', f'Deploy {datetime.now().isoformat()}'], check=True)
    subprocess.run(['git', 'push', 'origin', GITHUB_PAGES_BRANCH], check=True)

    print("✅ Deployed to GitHub Pages!")
    print(f"   Visit: https://{GITHUB_PAGES_REPO.split('/')[0]}.github.io/{GITHUB_PAGES_REPO.split('/')[1]}/")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build content with Merkle caching")
    parser.add_argument("--file", help="Build single file")
    parser.add_argument("--force", action="store_true", help="Force rebuild (ignore cache)")
    parser.add_argument("--deploy", action="store_true", help="Deploy to GitHub Pages")

    args = parser.parse_args()

    # Create content dir if needed
    CONTENT_DIR.mkdir(exist_ok=True, parents=True)
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    if args.file:
        filepath = Path(args.file)
        build_file(filepath, force=args.force)

    else:
        build_all(force=args.force)

    if args.deploy:
        deploy_to_github_pages()

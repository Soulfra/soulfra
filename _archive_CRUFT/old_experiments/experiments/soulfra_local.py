#!/usr/bin/env python3
"""
Soulfra Local - Pure Python Desktop Platform

A single-file blog/content platform that runs from any desktop folder.
NO external dependencies - stdlib only.

Features:
- Tier system (0=private, 1=draft, 2=review, 3=public, 4=featured)
- Username-based SQLite databases
- Pure Python template engine (no Jinja2)
- Pure Python markdown parser (no markdown2)
- Git-like versioning (no git dependency)
- Local HTTP server (stdlib)
- Optional GitHub publishing (tier 3+ only)

Usage:
    python3 soulfra_local.py init --username=alice
    python3 soulfra_local.py serve
    python3 soulfra_local.py build
    python3 soulfra_local.py save "commit message"
    python3 soulfra_local.py publish --tier=3

Architecture:
- content/tier{0-4}_* folders for content organization
- {username}_soulfra.db for user data
- .versions/ for git-like snapshots
- build/ for generated HTML
"""

import sys
import os
import re
import json
import sqlite3
import hashlib
import shutil
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse


# ==============================================================================
# PURE PYTHON TEMPLATE ENGINE
# ==============================================================================

class SimpleTemplate:
    """
    Pure Python template engine using regex
    No Jinja2 dependency - just string replacement

    Syntax:
        {{ variable }} - Variable substitution
        {% for item in items %} ... {% endfor %} - Loops
        {% if condition %} ... {% endif %} - Conditionals
    """

    @staticmethod
    def render(template_string: str, **context) -> str:
        """Render template with context variables"""
        result = template_string

        # Handle for loops: {% for item in items %} ... {% endfor %}
        for_pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'

        def replace_for_loop(match):
            var_name = match.group(1)
            list_name = match.group(2)
            loop_body = match.group(3)

            if list_name not in context:
                return ''

            items = context[list_name]
            if not isinstance(items, list):
                return ''

            output = []
            for item in items:
                loop_context = {**context, var_name: item}
                rendered = loop_body
                for key, value in loop_context.items():
                    if isinstance(value, dict):
                        # Handle nested dict access: {{ item.key }}
                        for subkey, subvalue in value.items():
                            rendered = rendered.replace(f'{{{{ {var_name}.{subkey} }}}}', str(subvalue))
                    else:
                        rendered = rendered.replace(f'{{{{ {key} }}}}', str(value))
                output.append(rendered)

            return ''.join(output)

        result = re.sub(for_pattern, replace_for_loop, result, flags=re.DOTALL)

        # Handle if statements: {% if condition %} ... {% endif %}
        if_pattern = r'{%\s*if\s+(\w+)\s*%}(.*?){%\s*endif\s*%}'

        def replace_if(match):
            condition_name = match.group(1)
            if_body = match.group(2)

            if condition_name in context and context[condition_name]:
                return if_body
            return ''

        result = re.sub(if_pattern, replace_if, result, flags=re.DOTALL)

        # Handle simple variable substitution: {{ variable }}
        for key, value in context.items():
            result = result.replace(f'{{{{ {key} }}}}', str(value))

        # Clean up any remaining template syntax
        result = re.sub(r'{%.*?%}', '', result)
        result = re.sub(r'{{.*?}}', '', result)

        return result


# ==============================================================================
# PURE PYTHON MARKDOWN PARSER
# ==============================================================================

class SimpleMarkdown:
    """
    Pure Python markdown parser using regex
    No markdown2 dependency - just pattern matching

    Supports:
        # Header 1
        ## Header 2
        **bold**
        *italic*
        `code`
        [link](url)
        - list items
        > blockquotes
        ```code blocks```
    """

    @staticmethod
    def convert(markdown_text: str) -> str:
        """Convert markdown to HTML"""
        html = markdown_text

        # Code blocks: ```...```
        html = re.sub(
            r'```(.*?)```',
            r'<pre><code>\1</code></pre>',
            html,
            flags=re.DOTALL
        )

        # Headers: # H1, ## H2, ### H3
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold: **text**
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)

        # Italic: *text*
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

        # Inline code: `code`
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)

        # Links: [text](url)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)

        # Lists: - item
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)

        # Blockquotes: > text
        html = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

        # Paragraphs: wrap text blocks
        lines = html.split('\n')
        paragraphs = []
        current_p = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('<') or stripped == '':
                if current_p:
                    paragraphs.append('<p>' + ' '.join(current_p) + '</p>')
                    current_p = []
                if stripped and stripped.startswith('<'):
                    paragraphs.append(line)
            else:
                current_p.append(line)

        if current_p:
            paragraphs.append('<p>' + ' '.join(current_p) + '</p>')

        return '\n'.join(paragraphs)


# ==============================================================================
# DATABASE MANAGER
# ==============================================================================

class DatabaseManager:
    """
    Manages username-based SQLite databases
    Each user gets their own {username}_soulfra.db file
    """

    def __init__(self, username: str):
        self.username = username
        self.db_path = f"{username}_soulfra.db"
        self.conn = None

    def connect(self):
        """Connect to database, create if doesn't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()

        # Posts table - stores content with tier levels
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                tier INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
        ''')

        # Versions table - git-like snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_hash TEXT UNIQUE NOT NULL,
                message TEXT NOT NULL,
                snapshot_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Settings table - platform configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def save_post(self, title: str, slug: str, content: str, tier: int = 0):
        """Save or update post"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO posts (title, slug, content, tier)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                content = excluded.content,
                tier = excluded.tier,
                updated_at = CURRENT_TIMESTAMP
        ''', (title, slug, content, tier))
        self.conn.commit()
        return cursor.lastrowid

    def get_posts_by_tier(self, min_tier: int = 0) -> List[Dict]:
        """Get all posts at or above specified tier"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM posts
            WHERE tier >= ?
            ORDER BY created_at DESC
        ''', (min_tier,))
        return [dict(row) for row in cursor.fetchall()]

    def save_version(self, message: str, snapshot_data: Dict) -> str:
        """Save version snapshot, returns version hash"""
        # Generate hash from snapshot content
        snapshot_json = json.dumps(snapshot_data, sort_keys=True)
        version_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()[:12]

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO versions (version_hash, message, snapshot_data)
            VALUES (?, ?, ?)
        ''', (version_hash, message, snapshot_json))
        self.conn.commit()

        return version_hash

    def get_version(self, version_hash: str) -> Optional[Dict]:
        """Retrieve version snapshot"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM versions WHERE version_hash = ?', (version_hash,))
        row = cursor.fetchone()

        if not row:
            return None

        version = dict(row)
        version['snapshot_data'] = json.loads(version['snapshot_data'])
        return version

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ==============================================================================
# TIER SYSTEM MANAGER
# ==============================================================================

class TierManager:
    """
    Manages content tier system

    Tiers:
        0 = tier0_private - Never published, local only
        1 = tier1_drafts - Work in progress, not ready
        2 = tier2_review - Ready for review, not published
        3 = tier3_public - Published to website
        4 = tier4_featured - Highlighted content
    """

    TIER_NAMES = {
        0: 'tier0_private',
        1: 'tier1_drafts',
        2: 'tier2_review',
        3: 'tier3_public',
        4: 'tier4_featured'
    }

    @staticmethod
    def create_folder_structure():
        """Create tier-based content folders"""
        base_dir = Path('content')
        base_dir.mkdir(exist_ok=True)

        for tier, name in TierManager.TIER_NAMES.items():
            tier_dir = base_dir / name
            tier_dir.mkdir(exist_ok=True)

            # Create README explaining tier
            readme_path = tier_dir / 'README.md'
            if not readme_path.exists():
                readme_content = TierManager._get_tier_readme(tier, name)
                readme_path.write_text(readme_content)

    @staticmethod
    def _get_tier_readme(tier: int, name: str) -> str:
        """Generate README for tier folder"""
        descriptions = {
            0: "**Private content** - Never published. Personal notes, drafts, experiments.",
            1: "**Draft content** - Work in progress. Not ready for review or publication.",
            2: "**Review content** - Ready for review. Needs approval before publishing.",
            3: "**Public content** - Published to your website. Visible to everyone.",
            4: "**Featured content** - Highlighted on homepage. Your best work."
        }

        return f"""# {name.replace('_', ' ').title()}

{descriptions.get(tier, "Content folder")}

## Usage

Place markdown files (.md) in this folder to set their tier level to **{tier}**.

Files in this folder will be:
{"- ❌ Never published (local only)" if tier < 3 else "- ✅ Published to website"}
{"- ✅ Built into local HTML preview" if tier >= 1 else "- ⚠️  Only visible in database"}
{"- ⭐ Featured on homepage" if tier == 4 else ""}

## Publishing Rules

- Tier 0-2: Local only, never pushed to GitHub
- Tier 3-4: Published to website and GitHub Pages

Move files between tier folders to change their visibility level.
"""

    @staticmethod
    def scan_content_folders(db: DatabaseManager):
        """Scan content folders and import posts to database"""
        content_dir = Path('content')
        if not content_dir.exists():
            return

        for tier, tier_name in TierManager.TIER_NAMES.items():
            tier_dir = content_dir / tier_name
            if not tier_dir.exists():
                continue

            # Scan for markdown files
            for md_file in tier_dir.glob('*.md'):
                if md_file.name == 'README.md':
                    continue

                # Read file content
                content = md_file.read_text()

                # Extract title from filename or first line
                title = md_file.stem.replace('_', ' ').title()
                slug = md_file.stem.lower().replace(' ', '-')

                # Save to database
                db.save_post(title=title, slug=slug, content=content, tier=tier)


# ==============================================================================
# BUILD SYSTEM
# ==============================================================================

class BuildSystem:
    """
    Pure Python static site generator
    Converts markdown content to HTML
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.build_dir = Path('build')
        self.template = self._get_default_template()

    def build_site(self, min_tier: int = 1):
        """Build static HTML site from posts"""
        # Create build directory
        self.build_dir.mkdir(exist_ok=True)

        # Get posts to build
        posts = self.db.get_posts_by_tier(min_tier)

        # Build index page
        self._build_index(posts)

        # Build individual post pages
        for post in posts:
            self._build_post(post)

        print(f"✅ Built {len(posts)} posts to {self.build_dir}/")

    def _build_index(self, posts: List[Dict]):
        """Build index.html with post list"""
        post_list_html = []
        for post in posts:
            tier_label = TierManager.TIER_NAMES.get(post['tier'], 'unknown')
            post_list_html.append(f'''
                <article>
                    <h2><a href="{post['slug']}.html">{post['title']}</a></h2>
                    <span class="tier-badge tier-{post['tier']}">{tier_label}</span>
                    <time>{post['created_at']}</time>
                </article>
            ''')

        html = SimpleTemplate.render(
            self.template,
            title='Home',
            content='\n'.join(post_list_html)
        )

        (self.build_dir / 'index.html').write_text(html)

    def _build_post(self, post: Dict):
        """Build individual post HTML file"""
        # Convert markdown to HTML
        content_html = SimpleMarkdown.convert(post['content'])

        # Render with template
        html = SimpleTemplate.render(
            self.template,
            title=post['title'],
            content=content_html
        )

        # Write to file
        (self.build_dir / f"{post['slug']}.html").write_text(html)

    def _get_default_template(self) -> str:
        """Default HTML template"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Soulfra Local</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1, h2, h3 { color: #2c3e50; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        article {
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #3498db;
            background: #f8f9fa;
        }
        .tier-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .tier-0 { background: #95a5a6; color: white; }
        .tier-1 { background: #f39c12; color: white; }
        .tier-2 { background: #e67e22; color: white; }
        .tier-3 { background: #27ae60; color: white; }
        .tier-4 { background: #8e44ad; color: white; }
        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            background: #ecf0f1;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }
        pre code {
            background: none;
            padding: 0;
        }
        blockquote {
            border-left: 4px solid #bdc3c7;
            margin: 0;
            padding-left: 20px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
    </header>
    <main>
        {{ content }}
    </main>
    <footer>
        <p><a href="index.html">← Home</a> | Built with Soulfra Local</p>
    </footer>
</body>
</html>'''


# ==============================================================================
# VERSION CONTROL
# ==============================================================================

class VersionControl:
    """
    Git-like versioning without Git dependency
    Uses snapshots stored in database
    """

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_snapshot(self, message: str) -> str:
        """Create version snapshot of current state"""
        # Gather all files to snapshot
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'files': self._gather_files()
        }

        # Save to database
        version_hash = self.db.save_version(message, snapshot)

        print(f"✅ Saved snapshot: {version_hash}")
        print(f"   Message: {message}")
        print(f"   Files: {len(snapshot['files'])}")

        return version_hash

    def _gather_files(self) -> Dict[str, str]:
        """Gather all content files for snapshot"""
        files = {}
        content_dir = Path('content')

        if content_dir.exists():
            for md_file in content_dir.rglob('*.md'):
                if md_file.name == 'README.md':
                    continue
                rel_path = str(md_file.relative_to(content_dir))
                files[rel_path] = md_file.read_text()

        return files

    def restore_snapshot(self, version_hash: str):
        """Restore files from version snapshot"""
        version = self.db.get_version(version_hash)

        if not version:
            print(f"❌ Version {version_hash} not found")
            return

        snapshot_data = version['snapshot_data']
        files = snapshot_data.get('files', {})

        # Restore files
        content_dir = Path('content')
        for rel_path, content in files.items():
            file_path = content_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        print(f"✅ Restored {len(files)} files from {version_hash}")


# ==============================================================================
# HTTP SERVER
# ==============================================================================

class SoulfraHTTPHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for local serving"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='build', **kwargs)

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def serve_site(port: int = 8888):
    """Start local HTTP server"""
    build_dir = Path('build')

    if not build_dir.exists():
        print("❌ Build directory doesn't exist. Run: python3 soulfra_local.py build")
        return

    print(f"🚀 Starting server on http://localhost:{port}/")
    print(f"   Serving from: {build_dir.absolute()}")
    print(f"   Press Ctrl+C to stop")

    os.chdir('build')

    try:
        with HTTPServer(('localhost', port), SoulfraHTTPHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")


# ==============================================================================
# GITHUB PUBLISHER
# ==============================================================================

class GitHubPublisher:
    """
    Optional GitHub Pages publishing for tier 3+ content
    Uses git commands if available, otherwise provides instructions
    """

    @staticmethod
    def check_git_available() -> bool:
        """Check if git is installed"""
        return shutil.which('git') is not None

    @staticmethod
    def publish(min_tier: int = 3):
        """Publish tier 3+ content to GitHub Pages"""
        print(f"📤 Publishing tier {min_tier}+ content...")

        if not GitHubPublisher.check_git_available():
            print("\n⚠️  Git not found. Install git to enable GitHub publishing.")
            print("\nManual publishing instructions:")
            print("1. Install git: brew install git  (macOS) or apt install git (Linux)")
            print("2. Create GitHub repo: https://github.com/new")
            print("3. Run: git init && git add build/ && git commit -m 'Initial commit'")
            print("4. Run: git push origin main")
            print("5. Enable GitHub Pages in repo settings")
            return

        # Build site with tier 3+ only
        build_dir = Path('build')
        if not build_dir.exists():
            print("❌ Build directory doesn't exist. Run: python3 soulfra_local.py build")
            return

        print("\n✅ To publish to GitHub Pages:")
        print(f"   1. Commit build/ folder: git add build/ && git commit -m 'Publish tier {min_tier}+ content'")
        print("   2. Push to GitHub: git push origin main")
        print("   3. Enable GitHub Pages in repo settings (source: /build folder)")


# ==============================================================================
# CLI COMMANDS
# ==============================================================================

def cmd_init(username: str):
    """Initialize platform in current directory"""
    print(f"🚀 Initializing Soulfra Local for user: {username}")

    # Create database
    db = DatabaseManager(username)
    db.connect()

    # Create tier folders
    TierManager.create_folder_structure()

    # Create example post
    example_content = """# Welcome to Soulfra Local

This is your first post! Edit this file to customize it.

## Features

- **Pure Python** - No external dependencies
- **Tier System** - Organize content by visibility (0=private, 4=featured)
- **Version Control** - Git-like snapshots without Git
- **Local First** - Your data, your computer

## Next Steps

1. Create markdown files in `content/tier*_*/` folders
2. Run `python3 soulfra_local.py build` to generate HTML
3. Run `python3 soulfra_local.py serve` to preview locally
4. Run `python3 soulfra_local.py publish` to share tier 3+ content

Happy writing!
"""

    example_file = Path('content/tier1_drafts/welcome.md')
    example_file.write_text(example_content)

    db.close()

    print("\n✅ Platform initialized!")
    print(f"   Database: {username}_soulfra.db")
    print(f"   Content folders created in: content/")
    print(f"   Example post: {example_file}")
    print(f"\n📝 Next: Edit {example_file} and run 'python3 soulfra_local.py build'")


def cmd_build(username: str):
    """Build static HTML from markdown content"""
    print("🔨 Building site...")

    db = DatabaseManager(username)
    db.connect()

    # Scan content folders
    TierManager.scan_content_folders(db)

    # Build site
    builder = BuildSystem(db)
    builder.build_site(min_tier=1)  # Build tier 1+ (drafts and above)

    db.close()


def cmd_serve(port: int = 8888):
    """Start local HTTP server"""
    serve_site(port)


def cmd_save(username: str, message: str):
    """Save version snapshot"""
    print(f"💾 Creating snapshot: {message}")

    db = DatabaseManager(username)
    db.connect()

    vc = VersionControl(db)
    version_hash = vc.save_snapshot(message)

    db.close()


def cmd_publish(username: str, tier: int = 3):
    """Publish tier 3+ content to GitHub Pages"""
    # Rebuild with tier 3+ only
    db = DatabaseManager(username)
    db.connect()

    TierManager.scan_content_folders(db)

    builder = BuildSystem(db)
    builder.build_site(min_tier=tier)

    db.close()

    # Publish
    GitHubPublisher.publish(min_tier=tier)


def cmd_status(username: str):
    """Show platform status"""
    db = DatabaseManager(username)
    db.connect()

    print(f"📊 Soulfra Local Status\n")
    print(f"Username: {username}")
    print(f"Database: {db.db_path}")

    # Count posts by tier
    print(f"\n📝 Posts by tier:")
    for tier, tier_name in TierManager.TIER_NAMES.items():
        posts = db.get_posts_by_tier(min_tier=tier)
        posts_at_tier = [p for p in posts if p['tier'] == tier]
        print(f"   Tier {tier} ({tier_name}): {len(posts_at_tier)} posts")

    db.close()


# ==============================================================================
# MAIN CLI
# ==============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Soulfra Local - Pure Python Desktop Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 soulfra_local.py init --username=alice
  python3 soulfra_local.py build
  python3 soulfra_local.py serve
  python3 soulfra_local.py save "Updated about page"
  python3 soulfra_local.py publish --tier=3
  python3 soulfra_local.py status

Tier Levels:
  0 = tier0_private  (never published)
  1 = tier1_drafts   (work in progress)
  2 = tier2_review   (ready for review)
  3 = tier3_public   (published to web)
  4 = tier4_featured (highlighted content)
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init command
    init_parser = subparsers.add_parser('init', help='Initialize platform')
    init_parser.add_argument('--username', required=True, help='Username for database')

    # build command
    build_parser = subparsers.add_parser('build', help='Build static HTML')
    build_parser.add_argument('--username', default='default', help='Username')

    # serve command
    serve_parser = subparsers.add_parser('serve', help='Start local server')
    serve_parser.add_argument('--port', type=int, default=8888, help='Port number')

    # save command
    save_parser = subparsers.add_parser('save', help='Save version snapshot')
    save_parser.add_argument('message', help='Commit message')
    save_parser.add_argument('--username', default='default', help='Username')

    # publish command
    publish_parser = subparsers.add_parser('publish', help='Publish to GitHub Pages')
    publish_parser.add_argument('--tier', type=int, default=3, help='Minimum tier to publish')
    publish_parser.add_argument('--username', default='default', help='Username')

    # status command
    status_parser = subparsers.add_parser('status', help='Show platform status')
    status_parser.add_argument('--username', default='default', help='Username')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'init':
        cmd_init(args.username)
    elif args.command == 'build':
        cmd_build(args.username)
    elif args.command == 'serve':
        cmd_serve(args.port)
    elif args.command == 'save':
        cmd_save(args.username, args.message)
    elif args.command == 'publish':
        cmd_publish(args.username, args.tier)
    elif args.command == 'status':
        cmd_status(args.username)


if __name__ == '__main__':
    main()

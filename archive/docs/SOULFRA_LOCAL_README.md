# Soulfra Local - Pure Python Desktop Platform

**Start a blog from any desktop folder. Zero dependencies. Full control.**

## What is This?

Soulfra Local is a single-file blog platform that runs entirely in pure Python (stdlib only). No Flask. No Markdown libraries. Just Python 3.

### Key Features

- **🚀 Start from any folder** - `python3 soulfra_local.py init --username=you`
- **📊 Tier system** - Organize content by visibility (0=private, 4=featured)
- **💾 Git-like versioning** - Snapshots without Git dependency
- **🎨 Pure Python** - Regex-based template engine and markdown parser
- **🌐 Local-first** - Your data, your computer, your control
- **📤 Optional publishing** - Publish tier 3+ content to GitHub Pages

## Quick Start

### 1. Initialize Platform

```bash
# Create a new folder for your blog
mkdir my-blog
cd my-blog

# Initialize platform
python3 /path/to/soulfra_local.py init --username=alice

# What this creates:
# - alice_soulfra.db (your database)
# - content/tier{0-4}_*/ folders
# - content/tier1_drafts/welcome.md (example post)
```

### 2. Write Content

Create markdown files in tier folders:

```bash
# Private notes (never published)
echo "# My Secret Notes" > content/tier0_private/notes.md

# Draft posts (local only)
echo "# Work in Progress" > content/tier1_drafts/draft.md

# Ready for review
echo "# Almost Done" > content/tier2_review/article.md

# Public posts (publishable)
echo "# Hello World" > content/tier3_public/hello.md

# Featured content
echo "# Best Post Ever" > content/tier4_featured/featured.md
```

### 3. Build HTML

```bash
python3 /path/to/soulfra_local.py build --username=alice

# Builds tier 1+ content to build/ folder
# Creates index.html + individual post pages
```

### 4. Preview Locally

```bash
python3 /path/to/soulfra_local.py serve

# Opens http://localhost:8888/
# Ctrl+C to stop
```

### 5. Save Versions

```bash
python3 /path/to/soulfra_local.py save "Added first post" --username=alice

# Creates snapshot: ab12cd34ef56
# Stores in database with message
```

### 6. Publish (Optional)

```bash
# Build tier 3+ only (public content)
python3 /path/to/soulfra_local.py publish --tier=3 --username=alice

# Follow instructions to push to GitHub Pages
```

## Tier System Explained

| Tier | Name | Description | Built? | Published? |
|------|------|-------------|--------|------------|
| 0 | `tier0_private` | Personal notes, never shared | ❌ No | ❌ Never |
| 1 | `tier1_drafts` | Work in progress | ✅ Yes | ❌ Local only |
| 2 | `tier2_review` | Ready for review | ✅ Yes | ❌ Local only |
| 3 | `tier3_public` | Published to website | ✅ Yes | ✅ Yes |
| 4 | `tier4_featured` | Highlighted content | ✅ Yes | ✅ Yes |

### How Tiers Work

1. **Create markdown file in tier folder** - File inherits tier level
2. **Run build** - Scans folders, imports to database, generates HTML
3. **Run publish** - Only tier 3+ content gets pushed to GitHub

**Example workflow:**

```bash
# Draft phase (local only)
echo "# My Post" > content/tier1_drafts/my-post.md
python3 soulfra_local.py build --username=alice
python3 soulfra_local.py serve  # Preview locally

# Ready to publish
mv content/tier1_drafts/my-post.md content/tier3_public/
python3 soulfra_local.py build --username=alice
python3 soulfra_local.py publish --username=alice
```

## CLI Commands

### `init` - Initialize platform

```bash
python3 soulfra_local.py init --username=NAME

# Creates:
# - NAME_soulfra.db database
# - content/ folder structure
# - Example welcome.md post
```

### `build` - Generate HTML

```bash
python3 soulfra_local.py build --username=NAME

# Scans content/ folders
# Imports markdown to database
# Generates HTML in build/
# Default: builds tier 1+ (all except private)
```

### `serve` - Start local server

```bash
python3 soulfra_local.py serve
python3 soulfra_local.py serve --port=9000

# Serves build/ folder
# Opens http://localhost:8888/
# Press Ctrl+C to stop
```

### `save` - Create version snapshot

```bash
python3 soulfra_local.py save "Commit message" --username=NAME

# Creates SHA256 snapshot hash
# Stores all content files in database
# Like: git commit -m "message"
```

### `publish` - Publish to GitHub

```bash
python3 soulfra_local.py publish --tier=3 --username=NAME

# Rebuilds with only tier 3+ content
# Provides GitHub Pages instructions
# Requires git installed (or manual upload)
```

### `status` - Show platform info

```bash
python3 soulfra_local.py status --username=NAME

# Shows:
# - Username and database path
# - Post counts by tier
```

## Pure Python Implementation

### Template Engine (No Jinja2)

Uses regex for template rendering:

```python
class SimpleTemplate:
    @staticmethod
    def render(template_string, **context):
        # {{ variable }} → value
        # {% for item in items %} ... {% endfor %} → loop
        # {% if condition %} ... {% endif %} → conditional
        return result
```

### Markdown Parser (No markdown2)

Regex patterns for markdown syntax:

```python
class SimpleMarkdown:
    @staticmethod
    def convert(markdown_text):
        # # Header → <h1>Header</h1>
        # **bold** → <strong>bold</strong>
        # `code` → <code>code</code>
        # [text](url) → <a href="url">text</a>
        return html
```

### Version Control (No Git)

Snapshot-based versioning:

```python
class VersionControl:
    def save_snapshot(self, message):
        # Gather all content files
        # Generate SHA256 hash
        # Store in database
        return version_hash
```

## Architecture

### File Structure

```
my-blog/
├── alice_soulfra.db          # SQLite database
├── content/                  # Markdown content
│   ├── tier0_private/        # Never published
│   ├── tier1_drafts/         # Local only
│   ├── tier2_review/         # Ready for review
│   ├── tier3_public/         # Published
│   └── tier4_featured/       # Highlighted
└── build/                    # Generated HTML
    ├── index.html
    └── *.html
```

### Database Schema

```sql
-- Posts table
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    tier INTEGER DEFAULT 0,  -- 0-4 visibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Versions table (git-like snapshots)
CREATE TABLE versions (
    id INTEGER PRIMARY KEY,
    version_hash TEXT UNIQUE NOT NULL,  -- SHA256 hash
    message TEXT NOT NULL,
    snapshot_data TEXT NOT NULL,  -- JSON with all files
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Content Flow

```
1. Write markdown → content/tier*_*/post.md
2. Run build → Scans folders → Imports to database → Generates HTML
3. Run serve → Preview locally at http://localhost:8888/
4. Move to tier 3+ → Run publish → Push to GitHub Pages
```

## Publishing to GitHub Pages

### Option 1: With Git Installed

```bash
# Initialize git repo
git init
git add build/
git commit -m "Initial publish"

# Create GitHub repo at https://github.com/new
git remote add origin https://github.com/username/repo.git
git push -u origin main

# Enable GitHub Pages
# Settings → Pages → Source: /build folder
```

### Option 2: Manual Upload

```bash
# Build tier 3+ content
python3 soulfra_local.py publish --tier=3 --username=alice

# Upload build/ folder contents to:
# - GitHub Pages
# - Netlify Drop
# - Vercel
# - Any static host
```

## Advanced Usage

### Multiple Users

Different users can use same folder with different databases:

```bash
# Alice's blog
python3 soulfra_local.py init --username=alice
python3 soulfra_local.py build --username=alice

# Bob's blog (same folder)
python3 soulfra_local.py init --username=bob
python3 soulfra_local.py build --username=bob
```

### Custom Port

```bash
python3 soulfra_local.py serve --port=9000
# Opens http://localhost:9000/
```

### Build Specific Tier

```bash
# Build only tier 3+ (skip drafts)
python3 soulfra_local.py publish --tier=3 --username=alice
```

### Version Snapshots

```bash
# Save snapshot
python3 soulfra_local.py save "Before major refactor" --username=alice
# → Saved snapshot: ab12cd34ef56

# Later: restore from database using hash
# (Feature: manual restore via SQL query)
SELECT snapshot_data FROM versions WHERE version_hash = 'ab12cd34ef56';
```

## Markdown Syntax Supported

```markdown
# Header 1
## Header 2
### Header 3

**bold text**
*italic text*
`inline code`

[link text](https://example.com)

- List item 1
- List item 2

> Blockquote

\```
Code block
Multiple lines
\```
```

## Template Customization

Edit the `_get_default_template()` method in `soulfra_local.py`:

```python
def _get_default_template(self) -> str:
    return '''<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        /* Your custom CSS */
    </style>
</head>
<body>
    {{ content }}
</body>
</html>'''
```

## Why Pure Python?

**Problem:** Flask + Markdown libraries = dependencies

**Solution:** Pure Python stdlib only

**Benefits:**
- ✅ Works on any Python 3 installation
- ✅ No pip install needed
- ✅ No virtual environment required
- ✅ Copy file to any folder and run
- ✅ Easier to understand (regex vs black box)
- ✅ Faster startup (no import overhead)

**Trade-offs:**
- ⚠️ Simpler markdown support (no tables, footnotes, etc.)
- ⚠️ Basic template syntax (no complex filters)
- ⚠️ Manual restore from snapshots (no full git interface)

## Comparison to Other Systems

| Feature | Soulfra Local | Jekyll | Hugo | Flask Blog |
|---------|---------------|--------|------|------------|
| Dependencies | None (stdlib) | Ruby, gems | None (binary) | Flask, MD, etc. |
| Setup time | 1 command | Install Ruby | Download binary | pip install |
| File size | 1 file (~30KB) | Many files | ~80MB binary | Many files |
| Tier system | ✅ Built-in | ❌ Manual | ❌ Manual | ❌ Manual |
| Version control | ✅ Built-in | Git required | Git required | Git required |
| Local-first | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Server-based |

## Troubleshooting

### "No such file or directory: soulfra_local.py"

Use absolute path or copy to working directory:

```bash
cp /path/to/soulfra_local.py .
python3 soulfra_local.py init --username=alice
```

### "Built 0 posts"

Check that markdown files exist in content/ folders:

```bash
ls -la content/tier1_drafts/
# Should see .md files (not just README.md)
```

### "Can't open file"

Make sure you're in the same directory where you ran `init`:

```bash
# Must be in same folder as {username}_soulfra.db
ls -la *.db
python3 soulfra_local.py build --username=alice
```

### Serve port already in use

Use different port:

```bash
python3 soulfra_local.py serve --port=9000
```

## Examples

### Personal Blog

```bash
mkdir my-blog && cd my-blog
python3 ../soulfra_local.py init --username=alice

# Write posts
echo "# About Me" > content/tier3_public/about.md
echo "# My Projects" > content/tier3_public/projects.md
echo "# Private Notes" > content/tier0_private/notes.md

# Build and preview
python3 ../soulfra_local.py build --username=alice
python3 ../soulfra_local.py serve

# Publish
python3 ../soulfra_local.py publish --tier=3 --username=alice
```

### Multiple Tier Workflow

```bash
# Start with draft
echo "# New Idea" > content/tier1_drafts/idea.md
python3 soulfra_local.py build --username=alice
python3 soulfra_local.py save "Draft: New idea post" --username=alice

# Move to review
mv content/tier1_drafts/idea.md content/tier2_review/
python3 soulfra_local.py build --username=alice
python3 soulfra_local.py save "Review: New idea post" --username=alice

# Publish
mv content/tier2_review/idea.md content/tier3_public/
python3 soulfra_local.py publish --tier=3 --username=alice
```

## License

Same as main project (MIT) - see LICENSE file.

## Philosophy

**"Start from any folder. Write in markdown. Publish what you want."**

Local-first blogging with:
- Zero setup friction
- Full content control
- Tier-based visibility
- No framework lock-in
- Pure Python simplicity

Built with stdlib only. No dependencies. No surprises.

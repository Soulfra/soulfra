# Self-Hosting Guide: Soulfra Multi-Brand Blogging Platform

**Turn any URL into a complete multimedia blog with procedurally generated images**

This guide shows you how to self-host Soulfra and give others access to create their own branded static sites with zero external dependencies.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Complete Workflow](#complete-workflow)
6. [Admin UI](#admin-ui)
7. [Multi-User Access with Ollama](#multi-user-access-with-ollama)
8. [Architecture](#architecture)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What is this?

A complete blogging platform that:
- ✅ Converts any URL to a blog post with procedural images
- ✅ Generates images locally using Python + Pillow (no external APIs)
- ✅ Stores everything in SQLite (posts, images, brands)
- ✅ Exports to static HTML sites for GitHub Pages
- ✅ Supports unlimited brands/domains
- ✅ Self-hostable with Ollama for multi-user access

### The Magic Pipeline

```
Paste URL → Scrape Content → Generate Images → Save to DB → Export Static Site → Deploy
```

All in **one command**:
```bash
python3 url_to_blog.py --url https://example.com --brand mybrand
```

---

## Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url> soulfra
cd soulfra
pip3 install -r requirements.txt
```

### 2. Create Your First Brand

**Via Web UI:**
```bash
python3 app.py  # Start Flask server
# Visit http://localhost:5000/admin/brand/new
```

**Via Command Line:**
```bash
# Add to domains.txt
echo "mybrand.com | tech | My awesome tech blog" >> domains.txt

# Initialize database
python3 init_brands.py
```

### 3. Import Content from URL

```bash
python3 url_to_blog.py --url https://example.com/article --brand mybrand
```

This will:
1. Scrape the URL
2. Generate procedural hero + section images
3. Create blog post in database
4. Auto-export static site to `output/mybrand/`

### 4. View Your Site

```bash
open output/mybrand/index.html
```

### 5. Deploy to GitHub Pages

```bash
cd output/mybrand
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/mybrand.git
git push -u origin main

# Enable GitHub Pages in repo settings
```

---

## System Requirements

### Minimum
- Python 3.8+
- 500MB disk space
- 2GB RAM

### Recommended
- Python 3.10+
- 2GB disk space (for multiple brands)
- 4GB RAM
- Ollama installed (for AI features)

### Dependencies

```bash
# Core
Flask==3.0.0
Pillow==10.1.0
BeautifulSoup4==4.12.2
requests==2.31.0
markdown2==2.4.10

# Optional (for AI features)
ollama  # Install via: curl https://ollama.ai/install.sh | sh
```

---

## Installation

### Step 1: Install System Dependencies

**macOS:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Install Python Dependencies

```bash
pip3 install Flask Pillow BeautifulSoup4 requests markdown2
```

### Step 3: Initialize Database

```bash
python3 -c "from database import init_db; init_db()"
```

### Step 4: Create Admin User

```bash
sqlite3 soulfra.db
INSERT INTO users (username, email, is_admin) VALUES ('admin', 'admin@localhost', 1);
.quit
```

### Step 5: Start Flask Server

```bash
python3 app.py
```

Visit: http://localhost:5000

---

## Complete Workflow

### Workflow 1: URL to Blog Post (Command Line)

```bash
# Import URL as blog post with auto-export
python3 url_to_blog.py \
  --url https://example.com/article \
  --brand howtocookathome

# Output:
# ✅ Scraped URL
# ✅ Generated 3 images
# ✅ Created post ID 42
# ✅ Exported to output/howtocookathome/
```

### Workflow 2: URL to Blog Post (Web UI)

1. Start server: `python3 app.py`
2. Visit: http://localhost:5000/admin/import-url
3. Paste URL + select brand
4. Click "Import & Generate"
5. Done! Static site exported automatically

### Workflow 3: Create Brand + Import Content

```bash
# 1. Create brand via web UI
open http://localhost:5000/admin/brand/new

# 2. Import content
python3 url_to_blog.py --url https://example.com --brand newbrand

# 3. Deploy
cd output/newbrand
git init && git add . && git commit -m "Initial"
git push
```

---

## Admin UI

### Admin Routes

| Route | Purpose |
|-------|---------|
| `/admin/login` | Login to admin panel |
| `/admin/dashboard` | Admin dashboard |
| `/admin/brand/new` | Create new brand |
| `/admin/import-url` | Import URL as blog post |
| `/admin/post/new` | Create post manually |

### Creating a New Brand

**Via Web UI:**

1. Visit: http://localhost:5000/admin/brand/new
2. Fill in:
   - Name: `My Cooking Blog`
   - Slug: `mycookingblog` (auto-generated)
   - Tagline: `Simple recipes for home cooks`
   - Domain: `mycookingblog.com` (optional)
   - Category: `cooking`
   - Colors: Pick primary, secondary, accent
   - Emoji: `🍳` (optional)
3. Click "Create Brand"

**What you get:**
- Database entry for brand
- Ready to import content
- Ready to export static site

### Importing Content

**Via Web UI:**

1. Visit: http://localhost:5000/admin/import-url
2. Paste URL: `https://www.seriouseats.com/perfect-scrambled-eggs`
3. Select brand: `mycookingblog`
4. Click "Import & Generate"

**What happens:**
1. URL is scraped (title, content, metadata)
2. Keywords extracted from content
3. Hero image generated (1200x600px)
4. Section images generated for each heading
5. Images stored in database as BLOBs
6. Post created in database
7. **Auto-export**: Static site updated in `output/mycookingblog/`

---

## Multi-User Access with Ollama

### Why Ollama?

Ollama allows you to run AI models locally, enabling:
- AI-generated comments on posts
- Content classification
- Automated feedback
- Multi-user access via web UI

### Installing Ollama

```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai
```

### Starting Ollama

```bash
ollama serve

# Pull models
ollama pull llama2
ollama pull mistral
```

### Configuring Soulfra

The Flask app automatically detects Ollama on `http://localhost:11434`

### Multi-User Workflow

**Scenario:** You want to give friends access to create their own blogs

1. **Host Soulfra on your network:**
   ```bash
   python3 app.py --host 0.0.0.0 --port 5000
   ```

2. **Share the URL:**
   ```
   Your IP: http://192.168.1.100:5000
   ```

3. **Users can:**
   - Visit `/admin/brand/new` to create their brand
   - Visit `/admin/import-url` to import content
   - Download their static site from `output/theirbrand/`
   - Deploy to GitHub Pages

4. **Each user gets:**
   - Their own brand/domain
   - Their own static site
   - Procedural images with their brand colors
   - Complete independence (no shared data)

---

## Architecture

### File Structure

```
soulfra/
├── app.py                   # Flask web server
├── url_to_blog.py           # CLI: URL → Blog post
├── url_to_content.py        # Scraper
├── procedural_media.py      # Image generator
├── enrich_content.py        # Content enrichment
├── export_static.py         # Static site exporter
├── database.py              # SQLite helpers
├── soulfra.db               # SQLite database
├── templates/               # HTML templates
│   ├── admin_brand_new.html
│   ├── admin_import_url.html
│   └── ...
├── output/                  # Generated static sites
│   ├── howtocookathome/
│   │   ├── index.html
│   │   ├── post/
│   │   ├── images/          # ← Extracted from DB
│   │   ├── feed.xml
│   │   └── CNAME
│   └── mybrand/
└── domains.txt              # Brand configuration
```

### Database Schema

**brands**
- id, name, slug, tagline, domain, category
- color_primary, color_secondary, color_accent
- emoji, created_at

**posts**
- id, user_id, brand_id, title, slug, content
- excerpt, published_at, ai_processed

**images**
- id, post_id, brand_id, hash, data (BLOB)
- mime_type, width, height, created_at

**users**
- id, username, email, is_admin

### How Images Work

1. **Generation:**
   ```python
   from procedural_media import ProceduralMediaGenerator

   generator = ProceduralMediaGenerator()
   img_bytes = generator.generate_hero_image(
       keywords=['recipe', 'cooking', 'eggs'],
       brand_colors=['#FF6B35', '#F7931E', '#C1272D']
   )
   ```

2. **Storage:**
   ```python
   # Saved to database as BLOB
   hash = hashlib.sha256(img_bytes).hexdigest()
   db.execute('INSERT INTO images (hash, data, mime_type) VALUES (?, ?, ?)',
              (hash, img_bytes, 'image/png'))
   ```

3. **Reference in Content:**
   ```markdown
   ![Recipe](</i/461219f3fa9fe6e571bef3195b5f67e5dca47ea12ee3efdcafd882b7ca172d3e>)
   ```

4. **Export to Static:**
   ```python
   # extract_and_save_images() in export_static.py
   # Queries DB for /i/<hash> refs
   # Writes to output/brand/images/<hash>.png
   # Updates markdown to images/<hash>.png
   ```

### Image Generation Styles

**Gradient:**
```python
generator.generate_hero_image(keywords, colors, style='gradient')
```

**Pixel Art:**
```python
generator.generate_hero_image(keywords, colors, style='pixel')
```

**Geometric:**
```python
generator.generate_hero_image(keywords, colors, style='geometric')
```

All are **deterministic** - same keywords = same image every time.

---

## Troubleshooting

### Import fails with "ModuleNotFoundError: pixel_utils"

**Fix:**
```bash
cp archive/experiments/pixel_utils.py .
```

### Images not showing in exported site

**Check:**
1. Images extracted? `ls output/yourbrand/images/`
2. HTML references? `grep 'images/' output/yourbrand/post/*.html`

**Fix:**
```bash
# Re-export with image extraction
python3 export_static.py --brand yourbrand
```

### Brand not found

**Fix:**
```bash
# Add to domains.txt
echo "yourbrand.com | category | Your tagline" >> domains.txt

# Re-initialize
python3 init_brands.py
```

### Permission denied on app.py

**Fix:**
```bash
chmod +x app.py
```

### Port 5000 already in use

**Fix:**
```bash
# Use different port
python3 app.py --port 5001
```

### Database locked

**Fix:**
```bash
# Close all connections
pkill -f "python3 app.py"

# Restart
python3 app.py
```

---

## Advanced Usage

### Custom Image Sizes

```python
from procedural_media import ProceduralMediaGenerator

generator = ProceduralMediaGenerator()
img = generator.generate_hero_image(
    keywords=['tech', 'coding'],
    brand_colors=['#FF6B35', '#F7931E'],
    size=(1920, 1080),  # Custom size
    style='pixel'
)
```

### Batch Import

```bash
# Import multiple URLs
for url in $(cat urls.txt); do
  python3 url_to_blog.py --url "$url" --brand mybrand
done
```

### Export All Brands

```bash
# Get all brand slugs
sqlite3 soulfra.db "SELECT slug FROM brands" | while read slug; do
  python3 export_static.py --brand "$slug"
done
```

### Custom Export Directory

```python
# In export_static.py
output_dir = Path('custom_output') / brand_slug
```

---

## What's Next?

1. ✅ **You now have:** A complete self-hosted blogging platform
2. ✅ **You can:** Turn any URL into a blog post with images
3. ✅ **You can:** Create unlimited brands with custom domains
4. ✅ **You can:** Export to static sites for free hosting

### Ideas for Extension

- **Multi-language support:** Translate scraped content
- **More image styles:** Add wave, noise, mandala generators
- **Video thumbnails:** Generate procedural video thumbnails
- **RSS automation:** Auto-import from RSS feeds
- **Email newsletters:** Convert posts to email templates
- **Analytics:** Track static site views with simple JS

---

## Support

- **Issues:** Create issue on GitHub
- **Docs:** See `README.md` for more details
- **Architecture:** See `SYSTEM_MAP.md`
- **Deployment:** See `DEPLOYMENT_PROOF.md`

---

**Built with love, Python, and zero external dependencies.**

🚀 Happy blogging!

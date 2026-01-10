# Self-Hosted OSS Stack: Complete Control

**Created**: 2025-12-27
**Philosophy**: Own your infrastructure, export to platforms (don't depend on them)

This is the real deployment guide - no Anchor.fm, no third-party lock-in, 100% self-hosted with automated exports.

---

## The Problem With Platform Dependence

### What Happened to Anchor.fm?
- 2019: Anchor.fm = free podcast hosting
- 2021: Spotify acquires Anchor
- 2024: Anchor redirects to creators.spotify.com
- Result: Your tools/links break, features change, you have zero control

### The Pattern:
```
Platform is free → Get users hooked → Get acquired → Change everything → Lock you in
```

**Examples**:
- Anchor.fm → Spotify (changed)
- Parse.com → Facebook (shutdown)
- Google Reader → Google (shutdown)
- Twitter API → Elonmusk lockdown

### The Self-Hosted Answer:
```
You host everything → Export RSS/APIs → Platforms pull from YOU → If they change, switch platforms
```

---

## Full Self-Hosted Stack (What You Own)

```
┌─────────────────────────────────────────────┐
│  YOUR SERVER (DigitalOcean $5/month)        │
│                                             │
│  ├── Soulfra (Blog + AI)                   │
│  ├── Podcast files (MP3s in /static/)      │
│  ├── RSS feed (auto-generated)             │
│  ├── Widget (embeddable chat)              │
│  ├── Database (SQLite)                     │
│  └── Automation scripts (export.py)        │
└─────────────────────────────────────────────┘
                   ↓ (YOU control, they pull)
    ┌──────────────┼──────────────┐
    ↓              ↓               ↓
Spotify      Apple Podcasts    YouTube
(reads RSS)  (reads RSS)       (via API)
```

**Key Difference**: Platforms read from YOUR server. If Spotify changes, you just point another platform to your RSS feed.

---

## Stack Components (All Open Source)

### 1. Core Web App: Soulfra (Flask + SQLite)
**What It Does**:
- Blog/CMS for posts
- AI auto-commenting (Ollama)
- Widget for chat
- Tutorial/quiz generation

**Files**:
- `app.py` - Flask web server
- `soulfra.db` - SQLite database
- `static/` - CSS, JS, MP3 files
- `templates/` - HTML templates

**Deploy**: DigitalOcean droplet or self-hosted server

---

### 2. Podcast Hosting: Self-Hosted MP3s
**What It Does**:
- Host MP3 files on YOUR server
- Generate RSS feed automatically
- Serve via nginx (fast CDN-like delivery)

**File Structure**:
```
static/
├── podcast/
│   ├── episodes/
│   │   ├── 001-salted-butter.mp3
│   │   ├── 002-knife-skills.mp3
│   │   └── 003-pasta-dough.mp3
│   └── cover-art.jpg
```

**nginx config** (serves MP3s fast):
```nginx
location /static/podcast/ {
    alias /var/www/soulfra-simple/static/podcast/;
    add_header Cache-Control "public, max-age=31536000";
    add_header X-Content-Type-Options "nosniff";
}
```

**Cost**: $0 (up to ~10GB free on droplet) or $0.005/GB on BackBlaze B2

---

### 3. RSS Feed Generator: podcast_rss.py (NEW)
**What It Does**:
- Auto-generates podcast RSS feed from your MP3 files
- Updates when you add new episodes
- Platforms (Spotify, Apple) pull from YOUR feed

**Create this file**:
```python
#!/usr/bin/env python3
"""
Podcast RSS Feed Generator

Generates RSS 2.0 + iTunes podcast feed from MP3 files.
Platforms pull from this feed (YOU control it).

Usage:
    python3 podcast_rss.py generate
"""

import os
import glob
from datetime import datetime
from mutagen.mp3 import MP3  # pip install mutagen
from mutagen.id3 import ID3

# Podcast metadata
PODCAST_TITLE = "How To Cook At Home"
PODCAST_DESCRIPTION = "Simple recipes and cooking techniques for home cooks"
PODCAST_AUTHOR = "How To Cook At Home Team"
PODCAST_EMAIL = "podcast@howtocookathome.com"
PODCAST_COVER_URL = "https://howtocookathome.com/static/podcast/cover-art.jpg"
PODCAST_LANGUAGE = "en-us"
PODCAST_CATEGORY = "Leisure > Food"
PODCAST_EXPLICIT = "no"
BASE_URL = "https://howtocookathome.com"

def get_mp3_metadata(filepath):
    """Extract metadata from MP3 file"""
    audio = MP3(filepath)
    try:
        tags = ID3(filepath)
        title = str(tags.get('TIT2', os.path.basename(filepath)))
        artist = str(tags.get('TPE1', PODCAST_AUTHOR))
        description = str(tags.get('COMM', ''))
    except:
        title = os.path.basename(filepath)
        artist = PODCAST_AUTHOR
        description = ""

    duration = int(audio.info.length)
    filesize = os.path.getsize(filepath)

    return {
        'title': title,
        'artist': artist,
        'description': description,
        'duration': duration,
        'filesize': filesize,
        'filename': os.path.basename(filepath)
    }

def generate_rss_feed():
    """Generate RSS feed from MP3 files"""
    # Find all MP3 files
    mp3_files = sorted(glob.glob('static/podcast/episodes/*.mp3'), reverse=True)

    if not mp3_files:
        print("❌ No MP3 files found in static/podcast/episodes/")
        return None

    # Build RSS feed
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{PODCAST_TITLE}</title>
    <link>{BASE_URL}</link>
    <description>{PODCAST_DESCRIPTION}</description>
    <language>{PODCAST_LANGUAGE}</language>
    <itunes:author>{PODCAST_AUTHOR}</itunes:author>
    <itunes:email>{PODCAST_EMAIL}</itunes:email>
    <itunes:image href="{PODCAST_COVER_URL}"/>
    <itunes:category text="{PODCAST_CATEGORY}"/>
    <itunes:explicit>{PODCAST_EXPLICIT}</itunes:explicit>
    <atom:link href="{BASE_URL}/podcast.xml" rel="self" type="application/rss+xml"/>
'''

    # Add episodes
    for i, mp3_file in enumerate(mp3_files, 1):
        meta = get_mp3_metadata(mp3_file)
        pub_date = datetime.fromtimestamp(os.path.getmtime(mp3_file)).strftime('%a, %d %b %Y %H:%M:%S %z')
        episode_url = f"{BASE_URL}/static/podcast/episodes/{meta['filename']}"

        rss += f'''
    <item>
        <title>{meta['title']}</title>
        <description>{meta['description'] or PODCAST_DESCRIPTION}</description>
        <pubDate>{pub_date}</pubDate>
        <enclosure url="{episode_url}" length="{meta['filesize']}" type="audio/mpeg"/>
        <guid isPermaLink="false">{meta['filename']}</guid>
        <itunes:author>{meta['artist']}</itunes:author>
        <itunes:duration>{meta['duration']}</itunes:duration>
        <itunes:episodeType>full</itunes:episodeType>
    </item>
'''

    rss += '''
</channel>
</rss>
'''

    # Write to file
    with open('static/podcast.xml', 'w') as f:
        f.write(rss)

    print(f"✅ Generated RSS feed: static/podcast.xml")
    print(f"   Episodes: {len(mp3_files)}")
    print(f"   Feed URL: {BASE_URL}/static/podcast.xml")

    return rss

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'generate':
        generate_rss_feed()
    else:
        print("Usage: python3 podcast_rss.py generate")
```

**How to use**:
```bash
# Add MP3 files
cp my-episode.mp3 static/podcast/episodes/001-salted-butter.mp3

# Generate RSS feed
python3 podcast_rss.py generate

# Result: static/podcast.xml (platforms read this)
```

**Submit to platforms**:
```
Spotify: https://podcasters.spotify.com/pod/submit
Apple Podcasts: https://podcastsconnect.apple.com
Google Podcasts: https://podcastsmanager.google.com

Feed URL: https://howtocookathome.com/static/podcast.xml
```

**If platform changes**: Just submit your RSS URL to a different platform. YOU control the feed.

---

### 4. Static Site Export: build_static.py (NEW)
**What It Does**:
- Exports your Soulfra blog to static HTML
- Deploy to GitHub Pages (free) or Netlify (free)
- Fast CDN delivery, no Flask needed for public pages

**Create this file**:
```python
#!/usr/bin/env python3
"""
Static Site Builder

Exports Soulfra blog to static HTML files.
Deploy to GitHub Pages, Netlify, or DigitalOcean.

Usage:
    python3 build_static.py
"""

import os
import shutil
from database import get_db
from app import app
from flask import url_for

OUTPUT_DIR = 'static_export'

def export_static_site():
    """Export all blog posts + index to static HTML"""
    # Clean output directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # Copy static assets
    shutil.copytree('static', f'{OUTPUT_DIR}/static')

    # Get all posts
    db = get_db()
    posts = db.execute('SELECT * FROM posts ORDER BY published_at DESC').fetchall()

    # Export index page
    with app.test_client() as client:
        response = client.get('/')
        with open(f'{OUTPUT_DIR}/index.html', 'wb') as f:
            f.write(response.data)

    # Export each post
    for post in posts:
        slug = post['slug']
        with app.test_client() as client:
            response = client.get(f'/post/{slug}')
            os.makedirs(f'{OUTPUT_DIR}/post', exist_ok=True)
            with open(f'{OUTPUT_DIR}/post/{slug}.html', 'wb') as f:
                f.write(response.data)

    db.close()

    print(f"✅ Exported {len(posts)} posts to {OUTPUT_DIR}/")
    print(f"   Deploy: cd {OUTPUT_DIR} && python3 -m http.server 8000")
    print(f"   Or push to GitHub Pages:")
    print(f"   cd {OUTPUT_DIR} && git init && git add . && git commit -m 'Deploy' && git push")

if __name__ == '__main__':
    export_static_site()
```

**Deploy to GitHub Pages**:
```bash
# Build static site
python3 build_static.py

# Push to GitHub
cd static_export
git init
git remote add origin https://github.com/yourusername/blog.git
git add .
git commit -m "Deploy static site"
git push -u origin gh-pages

# Result: https://yourusername.github.io/blog
```

**Cost**: $0 (GitHub Pages is free)

---

### 5. Automation Scripts: Auto-Export to Platforms

**Create `automation/export_to_platforms.py`**:
```python
#!/usr/bin/env python3
"""
Platform Export Automation

Automatically exports content to:
- YouTube (podcast audio as video)
- Twitter (new post announcements)
- RSS aggregators

Run via cron: 0 * * * * /usr/bin/python3 export_to_platforms.py
"""

import subprocess
import os
from database import get_db

def export_latest_episode_to_youtube():
    """
    Convert latest podcast MP3 to video + upload to YouTube

    Requires:
        - ffmpeg (audio → video conversion)
        - youtube-upload (https://github.com/tokland/youtube-upload)
    """
    # Find latest MP3
    import glob
    mp3_files = sorted(glob.glob('static/podcast/episodes/*.mp3'), reverse=True)

    if not mp3_files:
        return

    latest_mp3 = mp3_files[0]
    episode_title = os.path.basename(latest_mp3).replace('.mp3', '')

    # Convert MP3 → Video (with static image)
    output_video = f'/tmp/{episode_title}.mp4'
    cover_image = 'static/podcast/cover-art.jpg'

    # ffmpeg: combine audio + image into video
    subprocess.run([
        'ffmpeg', '-loop', '1', '-i', cover_image,
        '-i', latest_mp3,
        '-c:v', 'libx264', '-tune', 'stillimage',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p', '-shortest',
        output_video
    ])

    # Upload to YouTube
    subprocess.run([
        'youtube-upload',
        '--title', f'How To Cook At Home: {episode_title}',
        '--description', 'Full podcast episode. Subscribe for more!',
        '--category', '22',  # People & Blogs
        '--tags', 'cooking,recipes,podcast',
        output_video
    ])

    print(f"✅ Uploaded {episode_title} to YouTube")

def post_new_blog_to_twitter():
    """
    Auto-tweet new blog posts

    Requires: python-twitter or tweepy
    """
    # Get latest post
    db = get_db()
    latest_post = db.execute('''
        SELECT * FROM posts
        WHERE published_at > datetime('now', '-1 day')
        ORDER BY published_at DESC
        LIMIT 1
    ''').fetchone()

    if not latest_post:
        return

    # Tweet it (using Twitter API)
    import tweepy

    client = tweepy.Client(
        consumer_key=os.getenv('TWITTER_API_KEY'),
        consumer_secret=os.getenv('TWITTER_API_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_SECRET')
    )

    tweet_text = f"New recipe: {latest_post['title']}\n\nhttps://howtocookathome.com/post/{latest_post['slug']}"

    client.create_tweet(text=tweet_text)

    print(f"✅ Tweeted: {latest_post['title']}")

if __name__ == '__main__':
    export_latest_episode_to_youtube()
    post_new_blog_to_twitter()
```

**Setup cron job** (runs hourly):
```bash
crontab -e

# Add this line:
0 * * * * cd /var/www/soulfra-simple && /usr/bin/python3 automation/export_to_platforms.py
```

---

## Full Deployment Guide (DigitalOcean)

### Step 1: Create Droplet ($5/month)
```bash
# 1. Create droplet at digitalocean.com
# Choose: Ubuntu 22.04, Basic plan ($5/mo), San Francisco datacenter

# 2. SSH into droplet
ssh root@your-droplet-ip

# 3. Install dependencies
apt update && apt upgrade -y
apt install python3 python3-pip git nginx certbot python3-certbot-nginx ffmpeg -y

# 4. Install Ollama (local AI)
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2:3b
```

### Step 2: Clone & Setup Soulfra
```bash
# Clone repo
cd /var/www
git clone https://github.com/yourusername/soulfra-simple.git
cd soulfra-simple

# Install Python deps
pip3 install flask mutagen tweepy youtube-upload

# Initialize database
python3 database.py
python3 brand_ai_persona_generator.py generate howtocookathome
```

### Step 3: Configure nginx
```bash
# Create nginx config
cat > /etc/nginx/sites-available/howtocookathome << 'EOF'
server {
    listen 80;
    server_name howtocookathome.com www.howtocookathome.com;

    # Flask app
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (fast serving)
    location /static {
        alias /var/www/soulfra-simple/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Podcast RSS feed
    location /podcast.xml {
        alias /var/www/soulfra-simple/static/podcast.xml;
        add_header Content-Type "application/rss+xml";
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/howtocookathome /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Step 4: Add SSL (Free)
```bash
certbot --nginx -d howtocookathome.com -d www.howtocookathome.com
```

### Step 5: Run Flask as Service
```bash
# Create systemd service
cat > /etc/systemd/system/soulfra.service << 'EOF'
[Unit]
Description=Soulfra Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/soulfra-simple
ExecStart=/usr/bin/python3 /var/www/soulfra-simple/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl start soulfra
systemctl enable soulfra
```

### Step 6: Point Domain
```
# In your domain registrar (Namecheap, etc.)
A Record: howtocookathome.com → your-droplet-ip
A Record: www.howtocookathome.com → your-droplet-ip

Wait 5-10 minutes for DNS propagation
```

**Result**: Your site is live at https://howtocookathome.com

---

## Podcast Workflow (Self-Hosted)

### 1. Record Episode
```bash
# Record locally (use Audacity, GarageBand, etc.)
# Save as: 001-salted-butter.mp3
```

### 2. Upload to Server
```bash
# SCP to your server
scp 001-salted-butter.mp3 root@howtocookathome.com:/var/www/soulfra-simple/static/podcast/episodes/

# Or use FileZilla, rsync, etc.
```

### 3. Generate RSS Feed
```bash
# SSH to server
ssh root@howtocookathome.com

# Regenerate feed
cd /var/www/soulfra-simple
python3 podcast_rss.py generate

# Result: static/podcast.xml updated
```

### 4. Auto-Export to Platforms
```bash
# Manual (first time):
python3 automation/export_to_platforms.py

# Automated (cron runs hourly):
# Already setup in cron job above
```

**Platforms pull from YOUR RSS**:
- Spotify: Reads https://howtocookathome.com/podcast.xml
- Apple Podcasts: Reads https://howtocookathome.com/podcast.xml
- Google Podcasts: Reads https://howtocookathome.com/podcast.xml

**If platform changes**: Submit RSS URL to new platform. Done.

---

## Cost Breakdown (Full Stack)

| Component | Service | Cost | Alternative |
|-----------|---------|------|-------------|
| **Server** | DigitalOcean Droplet | $5/month | Self-host Pi ($0) |
| **Domain** | Namecheap | $10/year | Free: .tk domain |
| **SSL** | Let's Encrypt | $0 | - |
| **Podcast Storage** | Included (10GB) | $0 | BackBlaze B2 ($0.005/GB) |
| **Static Hosting** | GitHub Pages | $0 | Netlify ($0) |
| **AI** | Ollama (local) | $0 | - |
| **Database** | SQLite (file) | $0 | - |
| **CDN** | nginx | $0 | Cloudflare ($0) |

**Total**: **$5-7/month** for full control vs. $50-200/month for SaaS platforms

---

## Export, Don't Depend

### Platforms You Export TO (They Pull From You):
1. **Spotify for Podcasters** - Reads your RSS feed
2. **Apple Podcasts** - Reads your RSS feed
3. **Google Podcasts** - Reads your RSS feed
4. **YouTube** - Auto-upload via API (ffmpeg converts MP3 → video)
5. **Twitter/X** - Auto-post new episodes via API
6. **Instagram** - Share episode links (manual or via API)

### What YOU Control:
- Your server (DigitalOcean or self-hosted)
- Your domain (howtocookathome.com)
- Your database (SQLite file - portable)
- Your content (MP3 files + blog posts)
- Your RSS feed (platforms read this)
- Your automation (cron jobs export to platforms)

**If a platform changes**:
- Anchor.fm → Spotify? No problem, you still have your MP3s + RSS
- Twitter API lock-down? Switch to Mastodon, post to your blog
- YouTube changes rules? Host video on your own site

---

## GitHub + Automation Strategy

### Repository Structure:
```
howtocookathome/
├── README.md
├── app.py
├── database.py
├── soulfra.db (gitignored)
├── podcast_rss.py (NEW)
├── build_static.py (NEW)
├── automation/
│   └── export_to_platforms.py (NEW)
├── static/
│   ├── podcast/
│   │   ├── episodes/ (gitignored - too large)
│   │   └── cover-art.jpg
│   └── style.css
└── templates/
    └── *.html
```

### Deploy via Git:
```bash
# On your server
cd /var/www/soulfra-simple

# Pull latest changes
git pull origin main

# Restart Flask
systemctl restart soulfra

# Rebuild RSS if new episodes
python3 podcast_rss.py generate

# Rebuild static site
python3 build_static.py
```

### Continuous Deployment (GitHub Actions):
```yaml
# .github/workflows/deploy.yml
name: Deploy to DigitalOcean

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DROPLET_IP }}
          username: root
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /var/www/soulfra-simple
            git pull origin main
            systemctl restart soulfra
            python3 podcast_rss.py generate
```

**Result**: Push to GitHub → Auto-deploys to your server

---

## Summary: Why Self-Hosting Wins

### Platform Dependence (What You Had):
```
You → Anchor.fm → Spotify acquires → Redirects to creators.spotify.com → Your links break
```

### Self-Hosted (What You Get):
```
You → YOUR server → RSS feed → Platforms pull from you → Platform changes? Switch to different platform
```

### What You Control:
1. ✅ All your content (MP3s, posts, database)
2. ✅ All your infrastructure (server, domain, code)
3. ✅ All your automation (exports run on YOUR schedule)
4. ✅ All your data (portable SQLite file)
5. ✅ All your AI (Ollama runs locally)

### What Platforms Get:
1. Your RSS feed (they pull from YOU)
2. API exports (you push when YOU want)
3. Nothing else - you own everything

---

## Next Steps

1. **Test Flask restart**: Visit http://localhost:5001/post/how-do-i-make-salted-butter
2. **Create podcast_rss.py**: Copy script above
3. **Add first MP3**: Upload to static/podcast/episodes/
4. **Generate RSS**: `python3 podcast_rss.py generate`
5. **Deploy to DigitalOcean**: Follow deployment guide
6. **Submit RSS to platforms**: Use YOUR feed URL

**The shift**: From "how do I use platforms" → "how do platforms read from ME"

You own the stack. Platforms are just distribution channels.

---

**Status**: Flask restarted. Comment should show. Self-hosted strategy defined. Ready to deploy.

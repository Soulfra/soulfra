#!/usr/bin/env python3
"""
Export Database → Git-Based Media Library
==========================================

Takes soulfra.db (fragmented across 100+ tables) and exports to unified
Git-based format where every piece of content is:
- Clipable (has URL, timestamp)
- Shareable (QR code, embed code)
- Targetable (references specific articles/videos)
- Reactable (comments, reactions in JSON)

Like TikTok/YouTube Shorts but Git-backed!
"""

import sqlite3
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Paths
DB_PATH = 'soulfra.db'
OUTPUT_DIR = Path('voice-archive/media')

def generate_short_id(content):
    """Generate short ID for URLs"""
    hash_obj = hashlib.sha256(content.encode())
    return hash_obj.hexdigest()[:8]

def export_posts():
    """Export all posts with metadata"""
    print("📝 Exporting posts...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, title, content, created_at, user_id, soul_score
            FROM posts
            LIMIT 100
        """)

        posts_dir = OUTPUT_DIR / 'posts'
        posts_dir.mkdir(parents=True, exist_ok=True)

        for row in cursor.fetchall():
            post_id, title, content, created_at, user_id, soul_score = row

            short_id = generate_short_id(f"post-{post_id}")
            post_dir = posts_dir / short_id
            post_dir.mkdir(exist_ok=True)

            # Metadata
            metadata = {
                "id": post_id,
                "type": "post",
                "short_id": short_id,
                "title": title,
                "created_at": created_at,
                "user_id": user_id,
                "soul_score": soul_score,
                "url": f"https://cringeproof.com/post/{short_id}",
                "qr_code": f"/qr/{short_id}.png",
                "embed_code": f'<iframe src="https://cringeproof.com/embed/post/{short_id}"></iframe>'
            }

            # Save files
            with open(post_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)

            with open(post_dir / 'content.md', 'w') as f:
                f.write(f"# {title}\n\n{content}")

            # Reactions file (empty initially)
            with open(post_dir / 'reactions.json', 'w') as f:
                json.dump({
                    "likes": 0,
                    "comments": [],
                    "shares": 0
                }, f, indent=2)

        count = cursor.rowcount
        print(f"  ✅ Exported {count} posts")

    except sqlite3.OperationalError as e:
        print(f"  ⚠️  No posts table: {e}")

    conn.close()

def export_news_articles():
    """Export news articles with voice reactions"""
    print("📰 Exporting news articles...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, title, url, summary, source, published_at
            FROM news_articles
            LIMIT 50
        """)

        news_dir = OUTPUT_DIR / 'news'
        news_dir.mkdir(parents=True, exist_ok=True)

        for row in cursor.fetchall():
            article_id, title, url, summary, source, published_at = row

            short_id = generate_short_id(f"news-{article_id}")
            article_dir = news_dir / short_id
            article_dir.mkdir(exist_ok=True)

            metadata = {
                "id": article_id,
                "type": "news_article",
                "short_id": short_id,
                "title": title,
                "source": source,
                "original_url": url,
                "published_at": published_at,
                "summary": summary,
                "clipable_url": f"https://cringeproof.com/clip/{short_id}",
                "voice_reactions": []  # Will be populated later
            }

            with open(article_dir / 'article.json', 'w') as f:
                json.dump(metadata, f, indent=2)

            # Markdown version for reading
            with open(article_dir / 'article.md', 'w') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**Source:** {source}\n")
                f.write(f"**URL:** {url}\n\n")
                f.write(f"{summary}\n")

        count = cursor.rowcount
        print(f"  ✅ Exported {count} news articles")

    except sqlite3.OperationalError as e:
        print(f"  ⚠️  No news_articles table: {e}")

    conn.close()

def copy_existing_audio():
    """Copy existing audio files from voice-archive/audio/"""
    print("🎙️ Copying existing voice recordings...")

    voice_dir = OUTPUT_DIR / 'voice'
    voice_dir.mkdir(parents=True, exist_ok=True)

    source_audio_dir = Path('voice-archive/audio')

    if not source_audio_dir.exists():
        print("  ⚠️  No existing audio directory")
        return

    count = 0
    for audio_folder in source_audio_dir.glob('*/'):
        if audio_folder.name == 'manifest.json':
            continue

        try:
            # Load existing metadata
            meta_path = audio_folder / 'metadata.json'
            if meta_path.exists():
                with open(meta_path) as f:
                    old_meta = json.load(f)

                # Generate short ID
                short_id = generate_short_id(f"voice-{audio_folder.name}")
                new_dir = voice_dir / short_id
                new_dir.mkdir(exist_ok=True)

                # Find audio file
                audio_file = None
                for ext in ['*.webm', '*.wav', '*.mp3']:
                    matches = list(audio_folder.glob(ext))
                    if matches:
                        audio_file = matches[0]
                        break

                if audio_file:
                    # Copy audio
                    shutil.copy(audio_file, new_dir / audio_file.name)

                    # Create enhanced metadata
                    metadata = {
                        "id": int(audio_folder.name),
                        "type": "voice_memo",
                        "short_id": short_id,
                        "filename": old_meta.get('filename', audio_file.name),
                        "created_at": old_meta.get('created_at', ''),
                        "has_transcription": old_meta.get('has_transcription', False),
                        "audio_file": audio_file.name,
                        "duration": None,  # TODO: extract from file
                        "url": f"https://cringeproof.com/voice/{short_id}",
                        "embed_code": f'<audio src="https://cringeproof.com/media/voice/{short_id}/{audio_file.name}" controls></audio>',
                        "timestamp_links": {
                            "0:00": f"https://cringeproof.com/voice/{short_id}#t=0",
                            # Can add more timestamp markers
                        }
                    }

                    with open(new_dir / 'metadata.json', 'w') as f:
                        json.dump(metadata, f, indent=2)

                    # Reactions file
                    with open(new_dir / 'reactions.json', 'w') as f:
                        json.dump({"plays": 0, "likes": 0, "comments": []}, f, indent=2)

                    count += 1

        except Exception as e:
            print(f"  ⚠️  Failed to copy {audio_folder.name}: {e}")

    print(f"  ✅ Copied {count} voice recordings")

def create_manifest():
    """Create master manifest of all media"""
    print("📋 Creating media manifest...")

    manifest = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "media_types": {
            "voice": {},
            "posts": {},
            "news": {},
            "clips": {}
        },
        "total_items": 0
    }

    # Scan all media directories
    for media_type in ['voice', 'posts', 'news']:
        media_dir = OUTPUT_DIR / media_type
        if not media_dir.exists():
            continue

        items = []
        for item_dir in media_dir.glob('*/'):
            meta_path = item_dir / 'metadata.json'
            if meta_path.exists():
                with open(meta_path) as f:
                    metadata = json.load(f)
                    items.append({
                        "short_id": metadata['short_id'],
                        "type": metadata['type'],
                        "url": metadata['url'],
                        "created_at": metadata.get('created_at', '')
                    })

        manifest['media_types'][media_type] = {
            "count": len(items),
            "items": items
        }
        manifest['total_items'] += len(items)

    # Save manifest
    with open(OUTPUT_DIR / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"  ✅ Manifest created with {manifest['total_items']} items")

def create_index_html():
    """Create simple index to browse all media"""
    print("🌐 Creating media index page...")

    html = """<!DOCTYPE html>
<html>
<head>
    <title>CringeProof Media Library</title>
    <style>
        body {
            font-family: sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #000;
            color: #fff;
        }
        .media-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .media-card {
            background: #1a1a1a;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid #333;
        }
        .media-card:hover {
            border-color: #ff006e;
        }
        .media-type {
            display: inline-block;
            background: #ff006e;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        audio {
            width: 100%;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <h1>🎬 CringeProof Media Library</h1>
    <p>All content exported from database → Git-backed, clipable, shareable</p>

    <div class="media-grid" id="mediaGrid">
        Loading...
    </div>

    <script>
        fetch('/media/manifest.json')
            .then(r => r.json())
            .then(manifest => {
                const grid = document.getElementById('mediaGrid');
                grid.innerHTML = '';

                // Render voice memos
                manifest.media_types.voice.items.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'media-card';
                    card.innerHTML = `
                        <div class="media-type">VOICE</div>
                        <strong>${item.short_id}</strong><br>
                        <small>${item.created_at}</small><br>
                        <a href="${item.url}" target="_blank">View →</a>
                    `;
                    grid.appendChild(card);
                });

                // Render posts
                manifest.media_types.posts.items.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'media-card';
                    card.innerHTML = `
                        <div class="media-type">POST</div>
                        <strong>${item.short_id}</strong><br>
                        <small>${item.created_at}</small><br>
                        <a href="${item.url}" target="_blank">View →</a>
                    `;
                    grid.appendChild(card);
                });
            });
    </script>
</body>
</html>
"""

    with open(OUTPUT_DIR / 'index.html', 'w') as f:
        f.write(html)

    print("  ✅ Index page created at /media/index.html")

def main():
    print("🚀 Starting database export to Git-based media library\n")

    # Create output structure
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Export different content types
    copy_existing_audio()
    export_posts()
    export_news_articles()

    # Create navigation files
    create_manifest()
    create_index_html()

    print("\n✅ Export complete!")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Browse: file://{OUTPUT_DIR.absolute()}/index.html")
    print("\nNext steps:")
    print("1. Commit to Git: git add voice-archive/media && git commit")
    print("2. Push to GitHub: git push")
    print("3. Access at: https://cringeproof.com/media/")

if __name__ == '__main__':
    main()

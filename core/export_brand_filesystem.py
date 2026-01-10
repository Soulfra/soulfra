#!/usr/bin/env python3
"""
Export Brand to Filesystem

Creates Linux-style directory structure from database:

brands/
├── deathtodata/
│   ├── config.json (brand personality, colors, emoji)
│   ├── posts/
│   │   ├── encryption-basics-123.md
│   │   └── privacy-guide-456.md
│   ├── neural_network.pkl (trained classifier)
│   └── subscribers.csv
├── calriven/
└── soulfra/

Usage:
    python3 export_brand_filesystem.py --brand deathtodata
    python3 export_brand_filesystem.py --brand calriven --zip
    python3 export_brand_filesystem.py --all
"""

import argparse
import sqlite3
import json
import os
import shutil
import pickle
from datetime import datetime
from pathlib import Path

def export_brand_to_filesystem(brand_slug, create_zip=False):
    """Export brand from database to filesystem structure"""

    print(f"\n{'='*60}")
    print(f"EXPORTING BRAND: {brand_slug}")
    print(f"{'='*60}\n")

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get brand info
    cursor.execute("""
        SELECT id, name, slug, tagline, emoji,
               color_primary, color_secondary, color_accent,
               personality_tone, personality_traits, ai_style,
               category, tier, domain
        FROM brands WHERE slug = ?
    """, (brand_slug,))

    brand_row = cursor.fetchone()
    if not brand_row:
        print(f"✗ Brand '{brand_slug}' not found")
        conn.close()
        return None

    brand_id = brand_row[0]
    brand_data = {
        "name": brand_row[1],
        "slug": brand_row[2],
        "tagline": brand_row[3],
        "emoji": brand_row[4],
        "colors": {
            "primary": brand_row[5],
            "secondary": brand_row[6],
            "accent": brand_row[7]
        },
        "personality": {
            "tone": brand_row[8],
            "traits": brand_row[9],
            "ai_style": brand_row[10]
        },
        "category": brand_row[11],
        "tier": brand_row[12],
        "domain": brand_row[13],
        "exported_at": datetime.now().isoformat()
    }

    # Create brand directory
    brand_dir = Path(f"brands/{brand_slug}")
    brand_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {brand_dir}")

    # 1. Export config.json
    config_path = brand_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(brand_data, f, indent=2)
    print(f"✓ Exported config: {config_path}")

    # 2. Export posts
    posts_dir = brand_dir / "posts"
    posts_dir.mkdir(exist_ok=True)

    cursor.execute("""
        SELECT id, title, slug, content, published_at
        FROM posts
        WHERE brand_id = ?
        ORDER BY published_at DESC
    """, (brand_id,))

    posts = cursor.fetchall()
    post_count = 0

    for post in posts:
        post_id, title, slug, content, published_at = post

        # Create markdown file
        post_filename = f"{slug}.md"
        post_path = posts_dir / post_filename

        # Format post with frontmatter
        post_markdown = f"""---
title: {title}
slug: {slug}
published: {published_at}
brand: {brand_slug}
---

{content}
"""

        with open(post_path, 'w') as f:
            f.write(post_markdown)

        post_count += 1

    print(f"✓ Exported {post_count} posts to {posts_dir}")

    # 3. Export neural network (if exists)
    nn_dir = Path('neural_networks')
    if nn_dir.exists():
        # Look for brand-specific classifiers
        for nn_file in nn_dir.glob(f"{brand_slug}*.pkl"):
            dest = brand_dir / nn_file.name
            shutil.copy(nn_file, dest)
            print(f"✓ Exported neural network: {nn_file.name}")

    # 4. Export subscribers (global - not brand-specific yet)
    cursor.execute("""
        SELECT email, confirmed, subscribed_at
        FROM subscribers
        WHERE confirmed = 1 AND unsubscribed_at IS NULL
        ORDER BY subscribed_at DESC
    """)

    subscribers = cursor.fetchall()

    if subscribers:
        subscribers_path = brand_dir / "subscribers.csv"
        with open(subscribers_path, 'w') as f:
            f.write("email,confirmed,subscribed_at\n")
            for email, confirmed, subscribed_at in subscribers:
                f.write(f"{email},{confirmed},{subscribed_at}\n")
        print(f"✓ Exported {len(subscribers)} subscribers to {subscribers_path}")

    # 5. Create README
    readme_path = brand_dir / "README.md"
    personality = brand_data.get('personality', {})
    readme_content = f"""# {brand_data['name']} {brand_data.get('emoji', '')}

**Tagline:** {brand_data.get('tagline', 'N/A')}

## Personality

- **Tone:** {personality.get('tone', 'N/A')}
- **Traits:** {personality.get('traits', 'N/A')}
- **AI Style:** {personality.get('ai_style', 'N/A')}

## Stats

- **Posts:** {post_count}
- **Subscribers:** {len(subscribers)}
- **Category:** {brand_data.get('category', 'N/A')}
- **Tier:** {brand_data.get('tier', 'N/A')}
- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Brand Colors

- Primary: `{brand_data['colors']['primary']}`
- Secondary: `{brand_data['colors']['secondary']}`
- Accent: `{brand_data['colors']['accent']}`

## Directory Structure

```
{brand_slug}/
├── config.json          # Brand configuration
├── posts/               # All blog posts as markdown
├── subscribers.csv      # Subscriber list
├── *_classifier.pkl     # Trained neural network
└── README.md           # This file
```

## Import

To import this brand into another Soulfra instance:

```bash
python3 import_brand_filesystem.py --brand {brand_slug}
```
"""

    with open(readme_path, 'w') as f:
        f.write(readme_content)
    print(f"✓ Created README: {readme_path}")

    conn.close()

    # 6. Create ZIP if requested
    if create_zip:
        zip_name = f"{brand_slug}_export_{int(datetime.now().timestamp())}"
        shutil.make_archive(zip_name, 'zip', 'brands', brand_slug)
        print(f"✓ Created ZIP: {zip_name}.zip")
        return f"{zip_name}.zip"

    print(f"\n✓ Export complete: {brand_dir}")
    return str(brand_dir)

def export_all_brands(create_zip=False):
    """Export all brands to filesystem"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT slug FROM brands")
    brands = cursor.fetchall()
    conn.close()

    exported = []
    for (brand_slug,) in brands:
        result = export_brand_to_filesystem(brand_slug, create_zip)
        if result:
            exported.append(result)

    print(f"\n{'='*60}")
    print(f"EXPORTED {len(exported)} BRANDS")
    print(f"{'='*60}\n")

    for path in exported:
        print(f"  → {path}")

    return exported

def main():
    parser = argparse.ArgumentParser(description="Export brands to filesystem")
    parser.add_argument("--brand", help="Brand slug to export")
    parser.add_argument("--all", action="store_true", help="Export all brands")
    parser.add_argument("--zip", action="store_true", help="Create ZIP archive")

    args = parser.parse_args()

    if args.all:
        export_all_brands(create_zip=args.zip)
    elif args.brand:
        export_brand_to_filesystem(args.brand, create_zip=args.zip)
    else:
        print("Usage:")
        print("  python3 export_brand_filesystem.py --brand deathtodata")
        print("  python3 export_brand_filesystem.py --all --zip")

if __name__ == "__main__":
    main()

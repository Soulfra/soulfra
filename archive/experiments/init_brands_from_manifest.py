#!/usr/bin/env python3
"""
Initialize Brands from Manifest - Pure Python Stdlib

Syncs theme definitions from themes/manifest.yaml into the brands database table.
This is the bootstrap script that populates the database with theme data.

Self-healing: Can be called automatically if no brands exist.

Usage:
    python3 init_brands_from_manifest.py

Or programmatically:
    from init_brands_from_manifest import sync_brands_from_manifest
    sync_brands_from_manifest()
"""

import yaml
import json
import os
from datetime import datetime
from database import get_db


def load_manifest():
    """
    Load and parse themes/manifest.yaml

    Returns:
        dict: Manifest data with themes
    """
    manifest_path = os.path.join(os.path.dirname(__file__), 'themes', 'manifest.yaml')

    if not os.path.exists(manifest_path):
        print(f"❌ Manifest not found: {manifest_path}")
        return None

    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)

    return manifest


def sync_brands_from_manifest():
    """
    Sync theme definitions from manifest into brands table

    Returns:
        dict: {
            'added': int,
            'updated': int,
            'skipped': int,
            'total': int
        }
    """
    print("=" * 60)
    print("🎨 Syncing Brands from Manifest")
    print("=" * 60)
    print()

    # Load manifest
    manifest = load_manifest()

    if not manifest or 'themes' not in manifest:
        print("❌ No themes found in manifest.yaml")
        return {'added': 0, 'updated': 0, 'skipped': 0, 'total': 0}

    themes = manifest['themes']
    print(f"📚 Found {len(themes)} themes in manifest")
    print()

    db = get_db()

    # Get existing brands
    existing_brands = {}
    for row in db.execute('SELECT id, slug FROM brands').fetchall():
        existing_brands[row['slug']] = row['id']

    print(f"💾 Current brands in database: {len(existing_brands)}")
    print()

    stats = {
        'added': 0,
        'updated': 0,
        'skipped': 0,
        'total': 0
    }

    # Sync each theme
    for theme_slug, theme_data in themes.items():
        stats['total'] += 1

        # Skip if no name
        if not theme_data.get('name'):
            print(f"  ⏭️  Skipped {theme_slug}: No name defined")
            stats['skipped'] += 1
            continue

        # Extract theme data
        name = theme_data['name']
        emoji = theme_data.get('emoji', '')
        personality = theme_data.get('personality', '')
        tone = theme_data.get('tone', '')
        ship_class = theme_data.get('class', 'dinghy')
        tier = theme_data.get('tier', 'free')

        # Build colors JSON
        colors_data = theme_data.get('colors', {})
        colors_json = json.dumps(colors_data) if colors_data else None

        # Build full config JSON (for exports/imports)
        config_json = json.dumps({
            'emoji': emoji,
            'class': ship_class,
            'tier': tier,
            'colors': colors_data,
            'personality': personality,
            'tone': tone,
            'animation': theme_data.get('animation'),
            'extends': theme_data.get('extends'),
            'features': theme_data.get('features', [])
        })

        # Check if brand exists
        if theme_slug in existing_brands:
            # Update existing brand
            db.execute('''
                UPDATE brands
                SET name = ?,
                    colors = ?,
                    personality = ?,
                    tone = ?,
                    config_json = ?
                WHERE slug = ?
            ''', (name, colors_json, personality, tone, config_json, theme_slug))

            print(f"  ✏️  Updated: {emoji} {name} ({theme_slug})")
            stats['updated'] += 1

        else:
            # Insert new brand
            cursor = db.execute('''
                INSERT INTO brands (name, slug, colors, personality, tone, config_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, theme_slug, colors_json, personality, tone, config_json, datetime.now().isoformat()))

            brand_id = cursor.lastrowid

            print(f"  ✅ Added: {emoji} {name} ({theme_slug}) - ID {brand_id}")
            stats['added'] += 1

    db.commit()
    db.close()

    # Print summary
    print()
    print("=" * 60)
    print("✅ Sync Complete!")
    print("=" * 60)
    print(f"Total themes: {stats['total']}")
    print(f"  Added: {stats['added']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  Skipped: {stats['skipped']}")
    print()

    return stats


def verify_brand_associations():
    """
    Check if all brand_posts associations point to valid brands

    Returns:
        dict: {
            'total_associations': int,
            'valid': int,
            'orphaned': int,
            'orphaned_brand_ids': [list of invalid IDs]
        }
    """
    print("🔍 Verifying brand-post associations...")

    db = get_db()

    # Get all brand IDs from brand_posts
    associations = db.execute('SELECT DISTINCT brand_id FROM brand_posts').fetchall()

    # Get all valid brand IDs
    valid_brands = set()
    for row in db.execute('SELECT id FROM brands').fetchall():
        valid_brands.add(row['id'])

    db.close()

    # Check which are orphaned
    orphaned_brand_ids = []
    valid_count = 0

    for assoc in associations:
        brand_id = assoc['brand_id']
        if brand_id in valid_brands:
            valid_count += 1
        else:
            orphaned_brand_ids.append(brand_id)

    total = len(associations)

    print(f"  Total unique brand IDs in associations: {total}")
    print(f"  Valid: {valid_count}")
    print(f"  Orphaned (invalid): {len(orphaned_brand_ids)}")

    if orphaned_brand_ids:
        print(f"  ⚠️  Orphaned brand IDs: {orphaned_brand_ids}")
        print(f"     These associations point to deleted brands!")

    print()

    return {
        'total_associations': total,
        'valid': valid_count,
        'orphaned': len(orphaned_brand_ids),
        'orphaned_brand_ids': orphaned_brand_ids
    }


def main():
    """CLI interface"""
    # Sync brands
    stats = sync_brands_from_manifest()

    # Verify associations
    verification = verify_brand_associations()

    # Final report
    print("📊 System Status:")
    print(f"  Brands in database: {stats['total']}")
    print(f"  Brand-post associations: {verification['total_associations']}")

    if verification['orphaned'] > 0:
        print()
        print("⚠️  Warning: Some brand-post associations are orphaned!")
        print("   Run cleanup_orphaned_associations.py to fix")


if __name__ == '__main__':
    main()

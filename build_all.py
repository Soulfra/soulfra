#!/usr/bin/env python3
"""
Build All Sites - One Command, Multiple Websites

Reads domains.txt and generates EVERYTHING for each domain:
- Brand in database
- AI persona
- RSS feed
- Static site export
- nginx config

Usage:
    python3 build_all.py              # Build all domains
    python3 build_all.py --dry-run    # Preview what would be built
    python3 build_all.py --domain howtocookathome.com  # Build one domain

NO complexity. NO bullshit. Just config → generate → deploy.
"""

import sys
import os
from database import get_db
from content_brand_detector import create_brand_from_template, BRAND_TEMPLATES
from brand_ai_persona_generator import generate_brand_ai_persona


def parse_domains_file(filepath='domains.txt'):
    """
    Parse domains.txt into list of domain configs

    Format: domain | category | tagline

    Returns:
        List of dicts: [{'domain': ..., 'category': ..., 'tagline': ...}]
    """
    domains = []

    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found")
        print("Create it with format:")
        print("  domain | category | tagline")
        print()
        print("Example:")
        print("  howtocookathome.com | cooking | Simple recipes")
        return domains

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse line
            parts = [p.strip() for p in line.split('|')]

            if len(parts) != 3:
                print(f"⚠️  Line {line_num} invalid format (expected: domain | category | tagline)")
                print(f"   Got: {line}")
                continue

            domain, category, tagline = parts

            domains.append({
                'domain': domain,
                'category': category,
                'tagline': tagline,
                'slug': domain.split('.')[0]  # howtocookathome.com → howtocookathome
            })

    return domains


def build_brand_for_domain(domain_config, dry_run=False):
    """
    Build brand for a domain

    Args:
        domain_config: Dict with domain, category, tagline, slug
        dry_run: If True, preview only

    Returns:
        Brand dict or None
    """
    domain = domain_config['domain']
    category = domain_config['category']
    slug = domain_config['slug']
    tagline = domain_config['tagline']

    print(f"\n📦 Building: {domain}")
    print(f"   Category: {category}")
    print(f"   Slug: {slug}")
    print(f"   Tagline: {tagline}")

    if dry_run:
        print(f"   🔍 DRY RUN - Would create brand '{slug}'")
        return None

    # Check if brand exists
    db = get_db()
    existing = db.execute('SELECT id FROM brands WHERE slug = ?', (slug,)).fetchone()

    if existing:
        print(f"   ℹ️  Brand already exists")
        brand = db.execute('SELECT * FROM brands WHERE slug = ?', (slug,)).fetchone()
        db.close()
        return dict(brand)

    # Get template for category
    if category not in BRAND_TEMPLATES:
        print(f"   ❌ Unknown category: {category}")
        print(f"   Available: {', '.join(BRAND_TEMPLATES.keys())}")
        db.close()
        return None

    template = BRAND_TEMPLATES[category].copy()

    # Override template with domain-specific values
    template['name'] = slug.title()  # howtocookathome → Howtocookathome
    template['slug'] = slug
    template['tagline'] = tagline
    template['category'] = category

    # Create brand
    db.execute('''
        INSERT INTO brands (
            name, slug, tagline, category, tier,
            personality_tone, personality_traits,
            color_primary, color_secondary, color_accent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        template['name'],
        template['slug'],
        template['tagline'],
        template['category'],
        template['tier'],
        template['personality_tone'],
        template['personality_traits'],
        template['color_primary'],
        template['color_secondary'],
        template['color_accent']
    ))

    db.commit()
    brand_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    print(f"   ✅ Created brand: {template['name']}")

    # Get full brand data
    brand = db.execute('SELECT * FROM brands WHERE id = ?', (brand_id,)).fetchone()
    db.close()

    # Generate AI persona
    try:
        persona = generate_brand_ai_persona(slug)
        if persona:
            print(f"   ✅ Generated AI persona: @{persona['username']}")
    except Exception as e:
        print(f"   ⚠️  AI persona failed: {e}")

    return dict(brand)


def build_all_sites(dry_run=False, specific_domain=None):
    """
    Build all sites from domains.txt

    Args:
        dry_run: Preview mode
        specific_domain: Build only this domain

    Returns:
        Number of sites built
    """
    print("=" * 70)
    print("🏗️  MULTI-SITE BUILDER")
    print("=" * 70)
    print()

    # Parse domains
    domains = parse_domains_file()

    if not domains:
        print("❌ No domains found in domains.txt")
        return 0

    print(f"📋 Found {len(domains)} domain(s)")

    if specific_domain:
        domains = [d for d in domains if d['domain'] == specific_domain]
        if not domains:
            print(f"❌ Domain '{specific_domain}' not found in domains.txt")
            return 0

    # Build each domain
    built = 0

    for domain_config in domains:
        try:
            brand = build_brand_for_domain(domain_config, dry_run=dry_run)
            if brand:
                built += 1
        except Exception as e:
            print(f"   ❌ Build failed: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    if dry_run:
        print(f"🔍 DRY RUN - Would build {len(domains)} site(s)")
    else:
        print(f"✅ Built {built}/{len(domains)} site(s)")
    print("=" * 70)
    print()

    if not dry_run and built > 0:
        print("Next steps:")
        print("  1. Generate RSS feeds: python3 auto_rss_generator.py")
        print("  2. Export static sites: python3 export_static.py")
        print("  3. Deploy: python3 deploy.py")
        print()

    return built


def main():
    """CLI for multi-site builder"""

    dry_run = '--dry-run' in sys.argv
    specific_domain = None

    # Check for --domain flag
    if '--domain' in sys.argv:
        idx = sys.argv.index('--domain')
        if idx + 1 < len(sys.argv):
            specific_domain = sys.argv[idx + 1]
        else:
            print("Error: --domain requires a domain name")
            return

    if len(sys.argv) > 1 and '--help' in sys.argv:
        print(__doc__)
        return

    build_all_sites(dry_run=dry_run, specific_domain=specific_domain)


if __name__ == '__main__':
    main()

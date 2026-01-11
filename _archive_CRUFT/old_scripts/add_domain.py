#!/usr/bin/env python3
"""
Ultra-Simple Domain Builder

Usage:
    python3 add_domain.py mysite.com
    python3 add_domain.py mysite.org tech
    python3 add_domain.py mysite.net cooking "Best Recipes"

No text files. No Ollama. No confusion.
Just: domain → database.
"""

import sys
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'soulfra.db'

# Smart defaults by TLD
TLD_DEFAULTS = {
    '.com': {'category': 'business', 'emoji': '🏢', 'tier': 'foundation'},
    '.org': {'category': 'tech', 'emoji': '🌐', 'tier': 'foundation'},
    '.net': {'category': 'tech', 'emoji': '💻', 'tier': 'foundation'},
    '.io': {'category': 'tech', 'emoji': '⚡', 'tier': 'foundation'},
    '.ai': {'category': 'tech', 'emoji': '🤖', 'tier': 'creative'},
    '.app': {'category': 'tech', 'emoji': '📱', 'tier': 'creative'},
}

# Category emoji mapping
CATEGORY_EMOJI = {
    'cooking': '🍳',
    'tech': '💻',
    'privacy': '🔐',
    'business': '🏢',
    'health': '💊',
    'art': '🎨',
    'education': '📚',
    'gaming': '🎮',
    'finance': '💰',
    'local': '📍',
}

# Color schemes by category
CATEGORY_COLORS = {
    'cooking': {'primary': '#4CAF50', 'secondary': '#8BC34A', 'accent': '#FFC107'},
    'tech': {'primary': '#FF5722', 'secondary': '#FF9800', 'accent': '#FFC107'},
    'privacy': {'primary': '#1a1a1a', 'secondary': '#2d2d2d', 'accent': '#ff0000'},
    'business': {'primary': '#2196F3', 'secondary': '#03A9F4', 'accent': '#00BCD4'},
    'health': {'primary': '#E91E63', 'secondary': '#F06292', 'accent': '#EC407A'},
    'art': {'primary': '#9C27B0', 'secondary': '#E91E63', 'accent': '#FF5722'},
    'education': {'primary': '#3F51B5', 'secondary': '#5C6BC0', 'accent': '#7986CB'},
    'gaming': {'primary': '#673AB7', 'secondary': '#9575CD', 'accent': '#B39DDB'},
    'finance': {'primary': '#4CAF50', 'secondary': '#66BB6A', 'accent': '#81C784'},
    'local': {'primary': '#FF9800', 'secondary': '#FFB74D', 'accent': '#FFCC80'},
}


def get_tld(domain):
    """Extract TLD from domain"""
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.' + parts[-1]
    return '.com'


def get_defaults(domain, category=None):
    """Get smart defaults for domain"""
    tld = get_tld(domain)
    defaults = TLD_DEFAULTS.get(tld, TLD_DEFAULTS['.com'])

    # Override category if provided
    if category:
        defaults['category'] = category
        defaults['emoji'] = CATEGORY_EMOJI.get(category, '🌐')

    # Get colors for category
    colors = CATEGORY_COLORS.get(defaults['category'], CATEGORY_COLORS['tech'])
    defaults.update(colors)

    return defaults


def create_brand_name(domain):
    """Convert domain to readable name"""
    # Remove TLD
    name = domain.split('.')[0]

    # Handle hyphens
    if '-' in name:
        # howtocookathome → How To Cook At Home
        # death-to-data → Death To Data
        parts = name.split('-')
        return ' '.join(word.capitalize() for word in parts)

    # CamelCase detection
    if any(c.isupper() for c in name):
        return name  # Keep as-is if has capitals

    # Simple capitalization
    return name.capitalize()


def create_slug(domain):
    """Convert domain to slug"""
    name = domain.split('.')[0]
    return name.replace('-', '').lower()


def add_domain(domain, category=None, tagline=None):
    """Add domain to database"""

    # Validation
    if '.' not in domain:
        print(f"❌ Invalid domain: {domain}")
        print("   Domains must have a TLD (e.g., mysite.com)")
        return False

    domain = domain.lower().strip()

    # Connect to database
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Check if exists
    slug = create_slug(domain)
    existing = db.execute(
        'SELECT id, name FROM brands WHERE slug = ? OR domain = ?',
        (slug, domain)
    ).fetchone()

    if existing:
        print(f"⚠️  Domain already exists: {existing['name']} ({domain})")
        print(f"   ID: {existing['id']}")
        return False

    # Get defaults
    defaults = get_defaults(domain, category)
    name = create_brand_name(domain)

    # Generate tagline if not provided
    if not tagline:
        category_name = defaults['category'].replace('_', ' ')
        tagline = f"Your {category_name} resource"

    # Create brand
    try:
        db.execute('''
            INSERT INTO brands (
                name, slug, domain, tier, category, emoji, brand_type, tagline,
                color_primary, color_secondary, color_accent,
                personality, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            name,
            slug,
            domain,
            defaults['tier'],
            defaults['category'],
            defaults['emoji'],
            'member',  # spoke in the network
            tagline,
            defaults['primary'],
            defaults['secondary'],
            defaults['accent'],
            f"{defaults['category'].capitalize()} focused brand",
        ))

        brand_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        # Success!
        print()
        print("✅ Domain added to database!")
        print()
        print(f"   {defaults['emoji']} {name}")
        print(f"   Domain: {domain}")
        print(f"   Category: {defaults['category']}")
        print(f"   Tier: {defaults['tier']}")
        print(f"   Colors: {defaults['primary']}, {defaults['secondary']}, {defaults['accent']}")
        print(f"   Tagline: {tagline}")
        print()
        print("🌐 Test it:")
        print(f"   Local: http://{slug}.localhost:5001/")
        print(f"   Production: https://{domain}/")
        print()

        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False

    finally:
        db.close()


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print()
        print("📝 Ultra-Simple Domain Builder")
        print()
        print("Usage:")
        print("   python3 add_domain.py mysite.com")
        print("   python3 add_domain.py mysite.org tech")
        print("   python3 add_domain.py mysite.net cooking \"Best Recipes\"")
        print()
        print("Categories:")
        for cat, emoji in CATEGORY_EMOJI.items():
            print(f"   {emoji} {cat}")
        print()
        print("TLDs with auto-detection:")
        for tld, defaults in TLD_DEFAULTS.items():
            print(f"   {tld} → {defaults['category']} ({defaults['emoji']})")
        print()
        sys.exit(1)

    # Parse arguments
    domain = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else None
    tagline = sys.argv[3] if len(sys.argv) > 3 else None

    # Validate category
    if category and category not in CATEGORY_EMOJI:
        print(f"❌ Invalid category: {category}")
        print(f"   Valid categories: {', '.join(CATEGORY_EMOJI.keys())}")
        sys.exit(1)

    # Add domain
    success = add_domain(domain, category, tagline)

    if success:
        print("Next steps:")
        print()
        print("   1. View in matrix:")
        print("      python3 brand_matrix_visualizer.py")
        print()
        print("   2. Start Flask:")
        print("      python3 app.py")
        print()
        print("   3. Visit domain:")
        print(f"      open http://{create_slug(domain)}.localhost:5001/")
        print()
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

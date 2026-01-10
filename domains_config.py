#!/usr/bin/env python3
"""
Domains Config - Single Source of Truth for All Your Domains

Replaces/consolidates:
- domains.txt (4 domains, pipe-delimited)
- domains.json (9 domains, JSON)
- my-real-domains.csv (9 domains, CSV)
- domains-simple.txt, domains-master.csv, etc.

ONE config file. ONE format. No more "domains.txt is all fucking off".

Usage:
    from domains_config import DOMAINS, get_domain, get_all_domains

    # Get single domain
    domain = get_domain('stpetepros.com')

    # Get all domains
    all_domains = get_all_domains()

    # Export to different formats
    export_to_json('domains.json')
    export_to_csv('domains.csv')
"""

import json
import csv
from typing import Dict, List, Optional
from datetime import datetime


# ============================================================================
# THE ONE TRUE DOMAIN CONFIG
# ============================================================================

DOMAINS = {
    'soulfra.com': {
        'slug': 'soulfra',
        'name': 'Soulfra',
        'tagline': 'Your keys. Your identity. Period.',
        'category': 'Identity & Security',
        'type': 'platform_hub',
        'verified': True,  # You own this

        # Professional system config
        'professional_system_enabled': True,
        'supports_verticals': ['developer', 'tech_blogger', 'tech_podcaster', 'software_consultant'],

        # Theme
        'theme': {
            'primary': '#3498db',
            'secondary': '#2ecc71',
            'accent': '#e74c3c'
        },

        # Network role
        'network_role': 'hub',
        'is_main_platform': True,

        # Status
        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'cringeproof.com': {
        'slug': 'cringeproof',
        'name': 'CringeProof',
        'tagline': 'Zero Performance Anxiety',
        'category': 'social',
        'type': 'community',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['podcast', 'youtube', 'blog', 'creator', 'influencer'],

        'theme': {
            'primary': '#ff006e',
            'secondary': '#bdb2ff',
            'accent': '#000'
        },

        'network_role': 'member',
        'is_educational_platform': True,

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'stpetepros.com': {
        'slug': 'stpetepros',
        'name': 'St Pete Pros',
        'tagline': 'Tampa Bay Area, Florida: Leverage Local SEO and Online Directories',
        'category': 'Home Services',
        'type': 'professional_directory',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['plumber', 'electrician', 'hvac', 'contractor', 'handyman',
                              'landscaper', 'roofer', 'painter'],

        'theme': {
            'primary': '#0066CC',
            'secondary': '#FF6600',
            'accent': '#003366'
        },

        # Geographic targeting
        'geographic_scope': 'regional',
        'target_region': 'Tampa Bay, FL',
        'target_cities': ['Tampa', 'St. Petersburg', 'Clearwater', 'Brandon'],

        'network_role': 'member',
        'is_local_directory': True,

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'howtocookathome.com': {
        'slug': 'howtocookathome',
        'name': 'How To Cook At Home',
        'tagline': 'Simple recipes for home cooks 🍳',
        'category': 'cooking',
        'type': 'blog',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['chef', 'restaurant', 'cooking_instructor', 'food_blogger',
                              'nutritionist', 'meal_prep', 'catering'],

        'theme': {
            'primary': '#FF6B35',
            'secondary': '#F7931E',
            'accent': '#C1272D'
        },

        'network_role': 'member',

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'deathtodata.com': {
        'slug': 'deathtodata',
        'name': 'DeathToData',
        'tagline': 'Search without surveillance. Deal with it, Google.',
        'category': 'Privacy Search',
        'type': 'blog',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['security_consultant', 'privacy_advocate', 'cybersecurity_professional'],

        'theme': {
            'primary': '#e74c3c',
            'secondary': '#c0392b',
            'accent': '#f39c12'
        },

        'network_role': 'member',

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'calriven.com': {
        'slug': 'calriven',
        'name': 'Calriven',
        'tagline': 'Best AI for the job. Every time.',
        'category': 'AI Platform',
        'type': 'blog',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['ai_consultant', 'ml_engineer', 'ai_researcher', 'ai_podcaster'],

        'theme': {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#61dafb'
        },

        'network_role': 'member',

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'hollowtown.com': {
        'slug': 'hollowtown',
        'name': 'Hollowtown',
        'tagline': 'Where gaming mysteries unfold',
        'category': 'gaming',
        'type': 'blog',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['gaming_streamer', 'esports_player', 'gaming_youtuber',
                              'gaming_podcaster', 'game_reviewer'],

        'theme': {
            'primary': '#2c1810',
            'secondary': '#8b4513',
            'accent': '#ff6b35'
        },

        'network_role': 'member',

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'oofbox.com': {
        'slug': 'oofbox',
        'name': 'Oofbox',
        'tagline': 'Gaming content and community',
        'category': 'gaming',
        'type': 'blog',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['gaming_streamer', 'gaming_youtuber', 'gaming_podcaster'],

        'theme': {
            'primary': '#2c1810',
            'secondary': '#8b4513',
            'accent': '#ff6b35'
        },

        'network_role': 'member',

        'status': 'active',
        'last_updated': '2026-01-09'
    },

    'niceleak.com': {
        'slug': 'niceleak',
        'name': 'Niceleak',
        'tagline': 'Experience the thrill of the unknown, one game at a time',
        'category': 'gaming',
        'type': 'blog',
        'verified': True,

        'professional_system_enabled': True,
        'supports_verticals': ['gaming_journalist', 'gaming_insider', 'gaming_youtuber'],

        'theme': {
            'primary': '#1a1d23',
            'secondary': '#343a40',
            'accent': '#ff69b4'
        },

        'network_role': 'member',

        'status': 'active',
        'last_updated': '2026-01-09'
    },
}


# ============================================================================
# Lookup Functions
# ============================================================================

def get_domain(domain_name: str) -> Optional[Dict]:
    """
    Get domain config by name

    Args:
        domain_name: Full domain (e.g., 'stpetepros.com')

    Returns:
        Domain config dict or None
    """
    return DOMAINS.get(domain_name)


def get_domain_by_slug(slug: str) -> Optional[Dict]:
    """
    Get domain config by slug

    Args:
        slug: Domain slug (e.g., 'stpetepros')

    Returns:
        Domain config dict (with 'domain' key added) or None
    """
    for domain_name, config in DOMAINS.items():
        if config['slug'] == slug:
            return {**config, 'domain': domain_name}
    return None


def get_all_domains() -> Dict[str, Dict]:
    """Get all domain configs"""
    return DOMAINS


def get_active_domains() -> Dict[str, Dict]:
    """Get only active domains"""
    return {name: config for name, config in DOMAINS.items()
            if config.get('status') == 'active'}


def get_professional_domains() -> Dict[str, Dict]:
    """Get domains with professional system enabled"""
    return {name: config for name, config in DOMAINS.items()
            if config.get('professional_system_enabled')}


def get_domains_by_category(category: str) -> Dict[str, Dict]:
    """Get domains in a specific category"""
    return {name: config for name, config in DOMAINS.items()
            if config.get('category') == category}


# ============================================================================
# Export Functions
# ============================================================================

def export_to_json(output_file: str = 'domains.json'):
    """
    Export to JSON format (for old systems that need it)

    Args:
        output_file: Output filename
    """

    export_data = {
        'generated_at': datetime.now().isoformat(),
        'total_domains': len(DOMAINS),
        'domains': []
    }

    for domain_name, config in DOMAINS.items():
        export_data['domains'].append({
            'domain': domain_name,
            **config
        })

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"✅ Exported to {output_file}")


def export_to_csv(output_file: str = 'domains.csv'):
    """
    Export to CSV format

    Args:
        output_file: Output filename
    """

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(['domain', 'slug', 'name', 'tagline', 'category', 'type',
                        'verified', 'status', 'professional_enabled'])

        # Rows
        for domain_name, config in DOMAINS.items():
            writer.writerow([
                domain_name,
                config['slug'],
                config['name'],
                config['tagline'],
                config['category'],
                config['type'],
                config['verified'],
                config['status'],
                config.get('professional_system_enabled', False)
            ])

    print(f"✅ Exported to {output_file}")


def export_to_txt(output_file: str = 'domains.txt'):
    """
    Export to simple TXT format (pipe-delimited)

    Args:
        output_file: Output filename
    """

    with open(output_file, 'w') as f:
        f.write("# Domain Configuration - One Codebase, Multiple Sites\n")
        f.write("# Format: domain | category | tagline\n\n")

        for domain_name, config in DOMAINS.items():
            f.write(f"{domain_name} | {config['category']} | {config['tagline']}\n")

    print(f"✅ Exported to {output_file}")


def sync_all_formats():
    """Export to all formats (JSON, CSV, TXT)"""
    print("📦 Syncing all domain formats...\n")

    export_to_json('domains.json')
    export_to_json('my-real-domains.csv')  # Actually JSON despite name
    export_to_csv('domains.csv')
    export_to_csv('domains-master.csv')
    export_to_txt('domains.txt')
    export_to_txt('domains-simple.txt')

    print("\n✅ All formats synced!")


# ============================================================================
# Validation
# ============================================================================

def validate_domains():
    """Validate domain configuration"""

    print("✅ Validating domain configuration...\n")

    issues = []

    for domain_name, config in DOMAINS.items():
        # Required fields
        required = ['slug', 'name', 'tagline', 'category', 'type', 'verified', 'status']

        for field in required:
            if field not in config:
                issues.append(f"❌ {domain_name}: Missing required field '{field}'")

        # Check theme
        if 'theme' in config:
            theme_required = ['primary', 'secondary', 'accent']
            for field in theme_required:
                if field not in config['theme']:
                    issues.append(f"⚠️  {domain_name}: Missing theme.{field}")

        # Check professional system
        if config.get('professional_system_enabled'):
            if 'supports_verticals' not in config or not config['supports_verticals']:
                issues.append(f"⚠️  {domain_name}: Professional system enabled but no verticals defined")

    if issues:
        print("\n".join(issues))
        print(f"\n❌ Found {len(issues)} issues")
    else:
        print("✅ All domains valid!")

    return len(issues) == 0


# ============================================================================
# Stats
# ============================================================================

def show_stats():
    """Show domain statistics"""

    total = len(DOMAINS)
    active = len(get_active_domains())
    professional_enabled = len(get_professional_domains())

    print(f"📊 Domain Statistics\n")
    print(f"   Total domains: {total}")
    print(f"   Active: {active}")
    print(f"   Professional system enabled: {professional_enabled}")

    # By category
    print(f"\n   By category:")
    categories = {}
    for domain_name, config in DOMAINS.items():
        cat = config['category']
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"      {cat}: {count}")

    # By type
    print(f"\n   By type:")
    types = {}
    for domain_name, config in DOMAINS.items():
        typ = config['type']
        types[typ] = types.get(typ, 0) + 1

    for typ, count in sorted(types.items()):
        print(f"      {typ}: {count}")


def list_domains():
    """List all domains with key info"""

    print("🌐 Your Domains\n")

    for domain_name, config in DOMAINS.items():
        status_emoji = '✅' if config['verified'] else '⚠️'
        pro_emoji = '💼' if config.get('professional_system_enabled') else '📝'

        print(f"{status_emoji} {pro_emoji} {domain_name:25} | {config['name']:20} | {config['category']}")

    print()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import sys

    if '--export-json' in sys.argv:
        export_to_json()

    elif '--export-csv' in sys.argv:
        export_to_csv()

    elif '--export-txt' in sys.argv:
        export_to_txt()

    elif '--sync-all' in sys.argv:
        sync_all_formats()

    elif '--validate' in sys.argv:
        validate_domains()

    elif '--stats' in sys.argv:
        show_stats()

    elif '--list' in sys.argv:
        list_domains()

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Domains Config - Single Source of Truth                            ║
║                                                                      ║
║  Replaces all your messy domain files with ONE clean config:        ║
║  - domains.txt (4 domains, pipe-delimited)                          ║
║  - domains.json (9 domains, JSON)                                   ║
║  - my-real-domains.csv (9 domains, CSV)                            ║
║  - domains-simple.txt, domains-master.csv, etc.                     ║
║                                                                      ║
║  ONE file. ONE format. No more "domains.txt is all fucking off".   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python3 domains_config.py --list           # List all domains
    python3 domains_config.py --stats          # Show statistics
    python3 domains_config.py --validate       # Validate config
    python3 domains_config.py --export-json    # Export to JSON
    python3 domains_config.py --export-csv     # Export to CSV
    python3 domains_config.py --export-txt     # Export to TXT
    python3 domains_config.py --sync-all       # Sync all formats

Examples:
    python3 domains_config.py --list
    python3 domains_config.py --sync-all
""")

        list_domains()
        print()
        show_stats()

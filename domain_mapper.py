#!/usr/bin/env python3
"""
Domain Mapper - Map Your Real Domains to Professional System

Instead of fake subdomains (joesplumbing.cringeproof.com), use your ACTUAL domains:
- stpetepros.com → Tampa Bay professionals
- cringeproof.com → Platform hub / creators
- howtocookathome.com → Restaurant/chef professionals
- hollowtown.com → Gaming content creators
- etc.

Each domain = its own professional vertical/niche.

Usage:
    from domain_mapper import get_domain_config, route_professional_to_domain

    # Get config for domain
    config = get_domain_config('stpetepros.com')

    # Route professional to correct domain
    domain = route_professional_to_domain(professional_id=123)
"""

import sqlite3
from typing import Dict, Optional, List
import json


# ============================================================================
# Your Actual Domain Configuration
# ============================================================================

DOMAIN_MAPPING = {
    # Core Platform
    'cringeproof.com': {
        'slug': 'cringeproof',
        'name': 'CringeProof',
        'tagline': 'Zero Performance Anxiety',
        'purpose': 'platform_hub',
        'description': 'Main platform hub for all professional accounts',

        # Professional verticals on this domain
        'verticals': ['podcast', 'youtube', 'blog', 'creator', 'influencer'],

        # Theme
        'primary_color': '#ff006e',
        'secondary_color': '#bdb2ff',
        'accent_color': '#000',

        # Geographic scope
        'geographic_scope': 'national',  # Not location-specific
        'target_cities': [],
    },

    # Trade Professionals - Tampa Bay
    'stpetepros.com': {
        'slug': 'stpetepros',
        'name': 'St Pete Pros',
        'tagline': 'Tampa Bay Area Professionals',
        'purpose': 'trade_professionals',
        'description': 'Licensed professionals serving Tampa Bay area',

        # Professional verticals
        'verticals': ['plumber', 'electrician', 'hvac', 'contractor', 'handyman',
                     'landscaper', 'roofer', 'painter'],

        # Theme
        'primary_color': '#0066CC',
        'secondary_color': '#FF6600',
        'accent_color': '#003366',

        # Geographic scope
        'geographic_scope': 'regional',
        'target_cities': ['Tampa', 'St. Petersburg', 'Clearwater', 'Brandon',
                         'Riverview', 'Wesley Chapel', 'Land O Lakes'],
        'service_radius_miles': 35,
    },

    # Food/Restaurant Professionals
    'howtocookathome.com': {
        'slug': 'howtocookathome',
        'name': 'How To Cook At Home',
        'tagline': 'Simple recipes for home cooks',
        'purpose': 'food_professionals',
        'description': 'Chefs, restaurants, cooking instructors',

        # Professional verticals
        'verticals': ['chef', 'restaurant', 'cooking_instructor', 'food_blogger',
                     'nutritionist', 'meal_prep', 'catering'],

        # Theme
        'primary_color': '#FF6B35',
        'secondary_color': '#F7931E',
        'accent_color': '#C1272D',

        # Geographic scope
        'geographic_scope': 'national',
        'target_cities': [],
    },

    # Gaming Content Creators
    'hollowtown.com': {
        'slug': 'hollowtown',
        'name': 'Hollowtown',
        'tagline': 'Where gaming mysteries unfold',
        'purpose': 'gaming_professionals',
        'description': 'Gaming content creators, streamers, esports pros',

        # Professional verticals
        'verticals': ['gaming_streamer', 'esports_player', 'gaming_youtuber',
                     'gaming_podcaster', 'game_reviewer'],

        # Theme
        'primary_color': '#2c1810',
        'secondary_color': '#8b4513',
        'accent_color': '#ff6b35',

        # Geographic scope
        'geographic_scope': 'national',
        'target_cities': [],
    },

    # Gaming Platform #2
    'oofbox.com': {
        'slug': 'oofbox',
        'name': 'Oofbox',
        'tagline': 'Gaming content and community',
        'purpose': 'gaming_professionals',
        'description': 'Alternative gaming community platform',

        'verticals': ['gaming_streamer', 'gaming_youtuber', 'gaming_podcaster'],

        'primary_color': '#2c1810',
        'secondary_color': '#8b4513',
        'accent_color': '#ff6b35',

        'geographic_scope': 'national',
        'target_cities': [],
    },

    # Gaming Platform #3
    'niceleak.com': {
        'slug': 'niceleak',
        'name': 'Niceleak',
        'tagline': 'Gaming news and leaks',
        'purpose': 'gaming_professionals',
        'description': 'Gaming news, leaks, and insider content',

        'verticals': ['gaming_journalist', 'gaming_insider', 'gaming_youtuber'],

        'primary_color': '#1a1d23',
        'secondary_color': '#343a40',
        'accent_color': '#ff69b4',

        'geographic_scope': 'national',
        'target_cities': [],
    },

    # Tech Platform - Hub
    'soulfra.com': {
        'slug': 'soulfra',
        'name': 'Soulfra',
        'tagline': 'Your keys. Your identity. Period.',
        'purpose': 'tech_hub',
        'description': 'Technical platform and developer hub',

        'verticals': ['developer', 'tech_blogger', 'tech_podcaster', 'software_consultant'],

        'primary_color': '#3498db',
        'secondary_color': '#2ecc71',
        'accent_color': '#e74c3c',

        'geographic_scope': 'national',
        'target_cities': [],
    },

    # Privacy/Security Platform
    'deathtodata.com': {
        'slug': 'deathtodata',
        'name': 'DeathToData',
        'tagline': 'Search without surveillance',
        'purpose': 'privacy_professionals',
        'description': 'Privacy advocates, security professionals, consultants',

        'verticals': ['security_consultant', 'privacy_advocate', 'cybersecurity_professional'],

        'primary_color': '#e74c3c',
        'secondary_color': '#c0392b',
        'accent_color': '#f39c12',

        'geographic_scope': 'national',
        'target_cities': [],
    },

    # AI Platform
    'calriven.com': {
        'slug': 'calriven',
        'name': 'Calriven',
        'tagline': 'Best AI for the job. Every time.',
        'purpose': 'ai_professionals',
        'description': 'AI consultants, ML engineers, AI-focused content creators',

        'verticals': ['ai_consultant', 'ml_engineer', 'ai_researcher', 'ai_podcaster'],

        'primary_color': '#667eea',
        'secondary_color': '#764ba2',
        'accent_color': '#61dafb',

        'geographic_scope': 'national',
        'target_cities': [],
    },
}


# ============================================================================
# Domain Lookup Functions
# ============================================================================

def get_domain_config(domain: str) -> Optional[Dict]:
    """
    Get configuration for a domain

    Args:
        domain: Domain name (e.g., 'stpetepros.com')

    Returns:
        Domain config dict or None
    """
    return DOMAIN_MAPPING.get(domain)


def get_all_domains() -> List[str]:
    """Get list of all configured domains"""
    return list(DOMAIN_MAPPING.keys())


def get_domain_by_slug(slug: str) -> Optional[str]:
    """
    Get domain name by slug

    Args:
        slug: Domain slug (e.g., 'stpetepros')

    Returns:
        Full domain name or None
    """
    for domain, config in DOMAIN_MAPPING.items():
        if config['slug'] == slug:
            return domain
    return None


def get_domains_for_vertical(vertical: str) -> List[str]:
    """
    Get all domains that support a vertical

    Args:
        vertical: Vertical name (e.g., 'plumber', 'podcast')

    Returns:
        List of domain names
    """
    matching_domains = []

    for domain, config in DOMAIN_MAPPING.items():
        if vertical in config['verticals']:
            matching_domains.append(domain)

    return matching_domains


# ============================================================================
# Professional → Domain Routing
# ============================================================================

def route_professional_to_domain(
    trade_category: str,
    address_city: Optional[str] = None,
    address_state: Optional[str] = None
) -> str:
    """
    Route a professional to the correct domain based on their profile

    Logic:
    1. If trade matches regional domain's verticals AND city matches → Use regional domain
    2. If trade matches national domain's verticals → Use national domain
    3. Fallback to cringeproof.com

    Args:
        trade_category: Professional's trade ('plumber', 'podcast', etc.)
        address_city: Professional's city (optional)
        address_state: Professional's state (optional)

    Returns:
        Domain name to use

    Examples:
        >>> route_professional_to_domain('plumber', 'Tampa', 'FL')
        'stpetepros.com'

        >>> route_professional_to_domain('podcast')
        'cringeproof.com'

        >>> route_professional_to_domain('chef')
        'howtocookathome.com'
    """

    # Check regional domains first (if city/state provided)
    if address_city:
        for domain, config in DOMAIN_MAPPING.items():
            if config['geographic_scope'] == 'regional':
                # Check if trade matches
                if trade_category in config['verticals']:
                    # Check if city is in target area
                    if address_city in config.get('target_cities', []):
                        return domain

    # Check national domains by vertical
    for domain, config in DOMAIN_MAPPING.items():
        if config['geographic_scope'] == 'national':
            if trade_category in config['verticals']:
                return domain

    # Fallback to cringeproof.com (platform hub)
    return 'cringeproof.com'


def get_professional_domain(professional_id: int) -> str:
    """
    Get domain for existing professional from database

    Args:
        professional_id: Professional's database ID

    Returns:
        Domain name
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    prof = cursor.execute('''
        SELECT trade_category, address_city, address_state
        FROM professional_profile
        WHERE id = ?
    ''', (professional_id,)).fetchone()

    conn.close()

    if not prof:
        return 'cringeproof.com'

    trade_category, address_city, address_state = prof

    return route_professional_to_domain(trade_category, address_city, address_state)


def get_professional_url(professional_id: int, subdomain: Optional[str] = None) -> str:
    """
    Get full URL for professional's site

    Args:
        professional_id: Professional's database ID
        subdomain: Optional subdomain (uses ID if not provided)

    Returns:
        Full URL

    Examples:
        >>> get_professional_url(123, 'joesplumbing')
        'https://stpetepros.com/pro/joesplumbing'

        >>> get_professional_url(456)
        'https://cringeproof.com/pro/456'
    """

    domain = get_professional_domain(professional_id)

    if subdomain:
        return f"https://{domain}/pro/{subdomain}"
    else:
        return f"https://{domain}/pro/{professional_id}"


# ============================================================================
# Domain Statistics
# ============================================================================

def get_domain_stats():
    """
    Get statistics for all domains

    Returns:
        Dict with counts per domain
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    stats = {}

    for domain in get_all_domains():
        config = get_domain_config(domain)

        # Count professionals in each vertical for this domain
        verticals = config['verticals']

        count = cursor.execute('''
            SELECT COUNT(*)
            FROM professional_profile
            WHERE trade_category IN ({})
        '''.format(','.join('?' * len(verticals))), verticals).fetchone()[0]

        stats[domain] = {
            'professional_count': count,
            'verticals': verticals,
            'purpose': config['purpose'],
            'geographic_scope': config['geographic_scope']
        }

    conn.close()

    return stats


def show_domain_mapping():
    """Display current domain mapping"""

    print("🗺️  Your Domain Mapping\n")

    for domain, config in DOMAIN_MAPPING.items():
        print(f"🌐 {domain}")
        print(f"   Name: {config['name']}")
        print(f"   Purpose: {config['purpose']}")
        print(f"   Scope: {config['geographic_scope']}")
        print(f"   Verticals: {', '.join(config['verticals'][:3])}{'...' if len(config['verticals']) > 3 else ''}")

        if config['target_cities']:
            print(f"   Cities: {', '.join(config['target_cities'][:3])}...")

        print()


def validate_domain_mapping():
    """
    Validate domain mapping against database

    Check:
    - All professionals have a matching domain
    - No orphaned trades
    - Geographic coverage
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("✅ Validating domain mapping...\n")

    # Get all distinct trade categories
    trades = cursor.execute('''
        SELECT DISTINCT trade_category, COUNT(*) as count
        FROM professional_profile
        GROUP BY trade_category
    ''').fetchall()

    unmapped_trades = []

    for trade, count in trades:
        # Check if this trade is covered by any domain
        domains = get_domains_for_vertical(trade)

        if not domains:
            unmapped_trades.append((trade, count))
        else:
            print(f"✅ {trade:20} → {', '.join(domains)} ({count} pros)")

    if unmapped_trades:
        print("\n⚠️  Unmapped trades (add to DOMAIN_MAPPING):")
        for trade, count in unmapped_trades:
            print(f"   ❌ {trade:20} ({count} pros)")

    conn.close()


# ============================================================================
# Migration Helpers
# ============================================================================

def migrate_professionals_to_domains():
    """
    Add domain field to existing professionals

    Updates professional_profile table with correct domain
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if domain column exists
    try:
        cursor.execute('ALTER TABLE professional_profile ADD COLUMN assigned_domain TEXT')
        conn.commit()
        print("✅ Added assigned_domain column")
    except:
        print("ℹ️  assigned_domain column already exists")

    # Get all professionals
    professionals = cursor.execute('''
        SELECT id, trade_category, address_city, address_state
        FROM professional_profile
    ''').fetchall()

    print(f"\n🔄 Migrating {len(professionals)} professionals to domains...\n")

    for prof_id, trade, city, state in professionals:
        domain = route_professional_to_domain(trade, city, state)

        cursor.execute('''
            UPDATE professional_profile
            SET assigned_domain = ?
            WHERE id = ?
        ''', (domain, prof_id))

        print(f"   {prof_id:3} | {trade:15} | {city or 'N/A':15} → {domain}")

    conn.commit()
    conn.close()

    print(f"\n✅ Migration complete!")


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import sys

    if '--show' in sys.argv:
        show_domain_mapping()

    elif '--stats' in sys.argv:
        stats = get_domain_stats()
        print("📊 Domain Statistics\n")
        for domain, data in stats.items():
            print(f"{domain}:")
            print(f"   Professionals: {data['professional_count']}")
            print(f"   Purpose: {data['purpose']}")
            print(f"   Scope: {data['geographic_scope']}")
            print()

    elif '--validate' in sys.argv:
        validate_domain_mapping()

    elif '--migrate' in sys.argv:
        migrate_professionals_to_domains()

    elif '--route' in sys.argv:
        if len(sys.argv) < 3:
            print("Usage: python3 domain_mapper.py --route <trade> [city]")
            sys.exit(1)

        trade = sys.argv[2]
        city = sys.argv[3] if len(sys.argv) > 3 else None

        domain = route_professional_to_domain(trade, city)
        config = get_domain_config(domain)

        print(f"🎯 Routing: {trade}" + (f" in {city}" if city else ""))
        print(f"   → {domain}")
        print(f"   Purpose: {config['purpose']}")
        print(f"   Scope: {config['geographic_scope']}")

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Domain Mapper - Map Your Real Domains to Professional System       ║
║                                                                      ║
║  Your 9 domains mapped to professional verticals:                   ║
║  - stpetepros.com → Tampa Bay trade professionals                  ║
║  - cringeproof.com → Platform hub / creators                        ║
║  - howtocookathome.com → Food professionals                         ║
║  - hollowtown.com/oofbox.com/niceleak.com → Gaming                 ║
║  - soulfra.com/deathtodata.com/calriven.com → Tech                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python3 domain_mapper.py --show        # Show domain mapping
    python3 domain_mapper.py --stats       # Show statistics
    python3 domain_mapper.py --validate    # Validate mapping
    python3 domain_mapper.py --migrate     # Migrate existing pros
    python3 domain_mapper.py --route <trade> [city]  # Test routing

Examples:
    python3 domain_mapper.py --route plumber Tampa
    python3 domain_mapper.py --route podcast
    python3 domain_mapper.py --route chef Miami
""")

        show_domain_mapping()

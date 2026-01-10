#!/usr/bin/env python3
"""
Subdomain Router - Multi-Brand Domain Routing System

Routes HTTP requests to brand-specific themes based on domain name.

🏢 ARCHITECTURE: 1 Brand = 1 Domain = 1 Website
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Each row in the `brands` table represents:
- One unique domain name (e.g., soulfra.com, deathtodata.com)
- One complete website with its own theme, colors, personality
- One brand identity in the network

The `brands.domain` column stores the production domain (e.g., "soulfra.com").
The `brands.slug` column stores URL-friendly identifier (e.g., "soulfra").

🎚️ TIER SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brands are organized into tiers:

- foundation: Core network infrastructure (Soulfra, DeathToData, Calriven)
- creative: Creative-focused brands (HowToCookAtHome)
- null: Untiered brands (testing, development, misc)

Network roles:
- hub: Central brand (Soulfra) - aggregator and network center
- member: Spoke brands - specialized content/services

🌐 DNS SETUP FOR PRODUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
To make a brand domain live in production:

1. A Record (Root Domain):
   soulfra.com → A → <server-ip-address>

2. CNAME Record (www subdomain):
   www.soulfra.com → CNAME → soulfra.com

3. Repeat for each brand domain:
   - deathtodata.com → A → <server-ip-address>
   - calriven.com → A → <server-ip-address>
   - etc.

🔧 ROUTING STRATEGIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This router uses 3 detection strategies (in order):

1. Exact domain match:
   soulfra.com → matches brands.domain = 'soulfra.com'

2. www prefix removal:
   www.soulfra.com → strips 'www.' → matches soulfra.com

3. Subdomain slug match:
   ocean-dreams.localhost → extracts 'ocean-dreams' → matches brands.slug

🧪 LOCAL DEVELOPMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- localhost:5001 → Defaults to stpetepros brand (test mode)
- 192.168.1.87:5001 → Same as localhost (no subdomain)
- <slug>.localhost:5001 → Routes to brand with matching slug

Examples:
    - soulfra.com → Soulfra brand (production)
    - www.soulfra.com → Soulfra brand (strips www)
    - localhost:5001 → StPetePros brand (default)
    - ocean-dreams.localhost:5001 → Would match if brand existed

Usage:
    from subdomain_router import setup_subdomain_routing

    # In app.py
    app = Flask(__name__)
    setup_subdomain_routing(app)
"""

from flask import request, g
from database import get_db
import json
from rotation_helpers import inject_rotation_context
from typing import Optional, Dict


def detect_brand_from_subdomain():
    """
    Detect brand from full domain OR subdomain in request.host

    Database-driven routing - queries brands table for matching domain.

    Examples:
        - soulfra.com → Soulfra brand
        - stpetepros.com → StPetePros brand
        - ocean-dreams.soulfra.com → Ocean Dreams brand (subdomain)
        - localhost:5001 → Default (no brand)

    Returns:
        Brand dict if domain/subdomain matches, None otherwise
    """
    host = request.host  # e.g., "soulfra.com" or "ocean-dreams.localhost:5001"

    # Remove port
    host_without_port = host.split(':')[0]  # "soulfra.com" or "ocean-dreams.localhost"

    db = get_db()

    # Strategy 1: Try exact domain match first (e.g., "soulfra.com")
    brand_row = db.execute('''
        SELECT * FROM brands WHERE domain = ?
    ''', (host_without_port,)).fetchone()

    if brand_row:
        brand = dict(brand_row)
        brand = _enrich_brand_data(brand, db)
        return brand

    # Strategy 2: Try with www prefix (www.soulfra.com → soulfra.com)
    if host_without_port.startswith('www.'):
        clean_domain = host_without_port[4:]  # Remove "www."
        brand_row = db.execute('''
            SELECT * FROM brands WHERE domain = ?
        ''', (clean_domain,)).fetchone()

        if brand_row:
            brand = dict(brand_row)
            brand = _enrich_brand_data(brand, db)
            return brand

    # Strategy 3: Try subdomain routing (ocean-dreams.localhost → slug='ocean-dreams')
    parts = host_without_port.split('.')
    if len(parts) >= 2:
        subdomain = parts[0]

        # Check if subdomain matches brand slug
        brand_row = db.execute('''
            SELECT * FROM brands WHERE slug = ?
        ''', (subdomain,)).fetchone()

        if brand_row:
            brand = dict(brand_row)
            brand = _enrich_brand_data(brand, db)
            return brand

    # TEMPORARY: Default localhost to stpetepros for testing
    if 'localhost' in host_without_port or '127.0.0.1' in host_without_port:
        brand_row = db.execute('''
            SELECT * FROM brands WHERE slug = 'stpetepros'
        ''').fetchone()

        if brand_row:
            brand = dict(brand_row)
            brand = _enrich_brand_data(brand, db)
            print(f"🧪 TEST MODE: Showing stpetepros on localhost")
            return brand

    # No brand detected
    return None


def _enrich_brand_data(brand: dict, db) -> dict:
    """
    Add computed fields to brand dict

    Args:
        brand: Raw brand row from database
        db: Database connection

    Returns:
        Enriched brand dict with colors_list, thumbnail_url, etc.
    """
    # Build colors list from individual color columns
    colors = []
    if brand.get('color_primary'):
        colors.append(brand['color_primary'])
    if brand.get('color_secondary'):
        colors.append(brand['color_secondary'])
    if brand.get('color_accent'):
        colors.append(brand['color_accent'])

    brand['colors_list'] = colors

    # Legacy: also parse JSON if it exists
    if brand.get('colors'):
        try:
            brand['colors_list'] = json.loads(brand['colors'])
        except:
            pass

    # Parse brand values if JSON
    if brand.get('brand_values'):
        try:
            brand['values_list'] = json.loads(brand['brand_values'])
        except:
            brand['values_list'] = []
    else:
        brand['values_list'] = []

    # Get brand thumbnail
    thumbnail = db.execute('''
        SELECT hash FROM images
        WHERE json_extract(metadata, '$.brand_id') = ?
        AND json_extract(metadata, '$.type') = 'thumbnail'
        LIMIT 1
    ''', (brand['id'],)).fetchone()

    brand['thumbnail_url'] = f"/i/{thumbnail['hash']}" if thumbnail else None

    return brand


def apply_brand_theming(brand):
    """
    Generate CSS overrides for brand theming

    Args:
        brand: Brand dict

    Returns:
        CSS string with brand-specific styles
    """
    colors = brand.get('colors_list', [])

    if not colors:
        return ""

    primary_color = colors[0]
    secondary_color = colors[1] if len(colors) > 1 else primary_color
    accent_color = colors[2] if len(colors) > 2 else secondary_color

    css = f"""
    <style id="brand-theme">
        /* Brand Theme: {brand['name']} */

        /* Primary color overrides */
        header {{
            background: {primary_color} !important;
        }}

        .logo {{
            color: {secondary_color} !important;
        }}

        a {{
            color: {primary_color};
        }}

        a:hover {{
            color: {secondary_color};
        }}

        .btn-primary {{
            background: {primary_color} !important;
            border-color: {primary_color} !important;
        }}

        .btn-primary:hover {{
            background: {secondary_color} !important;
            border-color: {secondary_color} !important;
        }}

        .category-badge {{
            background: {accent_color} !important;
            color: white !important;
        }}

        .tag-badge {{
            border-color: {primary_color} !important;
            color: {primary_color} !important;
        }}

        /* Brand banner */
        body::before {{
            content: '🎨 {brand["name"]} Theme';
            display: block;
            background: {primary_color};
            color: white;
            text-align: center;
            padding: 8px;
            font-size: 14px;
            font-weight: 500;
        }}
    </style>
    """

    return css


def setup_subdomain_routing(app):
    """
    Setup subdomain routing for Flask app

    Args:
        app: Flask application instance
    """

    @app.before_request
    def detect_subdomain_brand():
        """Detect and apply brand theming from subdomain"""
        brand = detect_brand_from_subdomain()

        if brand:
            # Store brand in Flask g object (available in templates)
            g.active_brand = brand

            # Generate CSS overrides
            g.brand_css = apply_brand_theming(brand)

            print(f"🎨 Subdomain routing: {brand['name']} theme active")
        else:
            g.active_brand = None
            g.brand_css = ""

    @app.context_processor
    def inject_brand():
        """Make brand and rotation context available in all templates"""
        brand = g.get('active_brand', None)

        # Get rotation context for current domain
        rotation_ctx = inject_rotation_context(brand)

        return {
            'active_brand': brand,
            'brand_css': g.get('brand_css', ''),
            **rotation_ctx  # Merge rotation context (domain_question, theme_primary, etc.)
        }


def get_branded_posts_filter():
    """
    Get SQL filter for brand-specific post filtering

    Returns:
        SQL WHERE clause string
    """
    if hasattr(g, 'active_brand') and g.active_brand:
        # If brand is active, only show brand posts
        return f"brand_id = {g.active_brand['id']}"
    else:
        # Default: show all posts
        return "1=1"


# =============================================================================
# GITHUB INTEGRATION
# =============================================================================

# Domain → GitHub Repo Mapping (for star verification)
DOMAIN_GITHUB_REPOS = {
    'soulfra.com': {'owner': 'soulfra', 'repo': 'soulfra'},
    'deathtodata.com': {'owner': 'soulfra', 'repo': 'deathtodata'},
    'calriven.com': {'owner': 'soulfra', 'repo': 'calriven'},
    'howtocookathome.com': {'owner': 'soulfra', 'repo': 'howtocookathome'},
    'stpetepros.com': {'owner': 'soulfra', 'repo': 'stpetepros'},

    # GitHub Pages URLs
    'soulfra.github.io': {'owner': 'soulfra', 'repo': 'soulfra'},

    # Localhost (default)
    'localhost': {'owner': 'soulfra', 'repo': 'soulfra'},
    '127.0.0.1': {'owner': 'soulfra', 'repo': 'soulfra'},
    '192.168.1.87': {'owner': 'soulfra', 'repo': 'soulfra'},
}


def get_github_repo_for_domain(domain=None):
    """
    Get GitHub repo info for current domain

    Args:
        domain: Domain name (defaults to current request domain)

    Returns:
        Dict with 'owner' and 'repo', or None if not mapped

    Example:
        >>> repo = get_github_repo_for_domain('soulfra.com')
        >>> print(repo)
        {'owner': 'soulfra', 'repo': 'soulfra'}
    """
    if domain is None:
        from flask import request
        domain = request.host

    # Remove port
    domain_clean = domain.split(':')[0]

    # Remove www prefix
    if domain_clean.startswith('www.'):
        domain_clean = domain_clean[4:]

    return DOMAIN_GITHUB_REPOS.get(domain_clean)


# =============================================================================
# TIER-BASED ACCESS CONTROL
# =============================================================================

def check_domain_access(domain: str, user_id: Optional[int] = None,
                       github_username: Optional[str] = None) -> Dict:
    """
    Check if user has access to a domain based on tier

    Args:
        domain: Domain to check access for
        user_id: User ID (optional)
        github_username: GitHub username (optional)

    Returns:
        Dict with allowed, tier, message

    Tier Access:
        - Tier 0: soulfra.com only
        - Tier 1: soulfra.com + deathtodata.com + calriven.com
        - Tier 2: Tier 1 + howtocookathome.com + stpetepros.com
        - Tier 3+: All domains

    Example:
        >>> result = check_domain_access('deathtodata.com', github_username='octocat')
        >>> if not result['allowed']:
        ...     print(result['unlock_instructions'])
    """
    from tier_progression_engine import TierProgression

    # soulfra.com is always accessible (Tier 0)
    if domain in ['soulfra.com', 'soulfra.local', 'localhost', '127.0.0.1', '192.168.1.87']:
        return {
            'allowed': True,
            'tier': 0,
            'message': 'Entry domain - always accessible'
        }

    # If no user provided, deny access
    if not user_id and not github_username:
        return {
            'allowed': False,
            'tier': 0,
            'message': 'Please connect GitHub to access this domain',
            'unlock_instructions': 'Connect your GitHub account and star our repos to unlock'
        }

    # Check user's tier
    tier_engine = TierProgression(user_id=user_id, github_username=github_username)
    tier_data = tier_engine.get_current_tier()

    # Check if domain is unlocked
    unlocked = domain in tier_data['domains']

    if unlocked:
        return {
            'allowed': True,
            'tier': tier_data['tier'],
            'ownership': tier_data['ownership'].get(domain, 0.0),
            'message': f"Access granted (Tier {tier_data['tier']})"
        }
    else:
        return {
            'allowed': False,
            'tier': tier_data['tier'],
            'message': f"Domain locked - requires Tier {tier_data['next_tier']['next_tier']}",
            'unlock_instructions': tier_data['next_tier']['needed'],
            'next_tier': tier_data['next_tier']
        }


def inject_tier_context():
    """
    Inject tier information into Flask g object for use in templates

    Called automatically in before_request
    """
    from flask import session

    # Get user from session
    user_id = session.get('user_id')
    github_username = session.get('github_username')

    if not user_id and not github_username:
        g.user_tier = 0
        g.unlocked_domains = ['soulfra.com']
        g.domain_locked = False
        return

    # Get user tier
    from tier_progression_engine import TierProgression
    tier_engine = TierProgression(user_id=user_id, github_username=github_username)
    tier_data = tier_engine.get_current_tier()

    # Store in g object
    g.user_tier = tier_data['tier']
    g.unlocked_domains = tier_data['domains']
    g.tier_ownership = tier_data['ownership']

    # Check if current domain is locked
    current_domain = request.host.split(':')[0]
    if current_domain.startswith('www.'):
        current_domain = current_domain[4:]

    g.domain_locked = current_domain not in tier_data['domains']


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    from flask import Flask
    from database import get_db

    print("\n🧪 Testing Subdomain Router\n")

    # Test brand detection
    print("Test 1: Subdomain Detection")
    test_hosts = [
        "ocean-dreams.localhost:5001",
        "localhost:5001",
        "unknown-brand.localhost:5001",
        "soulfra.com"
    ]

    for host in test_hosts:
        print(f"\n  Host: {host}")

        # Mock request.host
        class MockRequest:
            def __init__(self, host):
                self.host = host

        # Temporarily replace request
        import flask
        original_request = flask.request
        flask.request = MockRequest(host)

        brand = detect_brand_from_subdomain()

        if brand:
            print(f"  ✅ Brand detected: {brand['name']}")
            print(f"     Slug: {brand['slug']}")
            print(f"     Colors: {brand['colors_list']}")

            # Test CSS generation
            css = apply_brand_theming(brand)
            print(f"     CSS generated: {len(css)} chars")
        else:
            print(f"  ⏭️  No brand (default theme)")

        # Restore request
        flask.request = original_request

    print("\n✅ Subdomain router tests complete!\n")

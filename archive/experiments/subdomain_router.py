#!/usr/bin/env python3
"""
Subdomain Router

Multi-tenant subdomain routing and brand theming.
Routes requests based on subdomain and applies brand-specific theming.

Examples:
    - ocean-dreams.localhost:5001 → Ocean Dreams theme
    - localhost:5001 → Default theme (no brand)
    - my-brand.soulfra.com → My Brand theme (production)

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


def detect_brand_from_subdomain():
    """
    Detect brand from subdomain in request.host

    Returns:
        Brand dict if subdomain matches a brand, None otherwise
    """
    host = request.host  # e.g., "ocean-dreams.localhost:5001"

    # Remove port
    host_without_port = host.split(':')[0]  # "ocean-dreams.localhost"

    # Get subdomain (everything before first dot)
    parts = host_without_port.split('.')

    if len(parts) < 2:
        # No subdomain (just "localhost" or "soulfra")
        return None

    subdomain = parts[0]

    # Check if subdomain is a brand slug
    db = get_db()
    brand_row = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (subdomain,)).fetchone()

    if not brand_row:
        return None

    brand = dict(brand_row)

    # Parse JSON fields
    brand['colors_list'] = json.loads(brand['colors']) if brand['colors'] else []
    brand['values_list'] = json.loads(brand['brand_values']) if brand['brand_values'] else []

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

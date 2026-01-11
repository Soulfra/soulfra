#!/usr/bin/env python3
"""
Brand CSS Generator - Dynamic Styling from Brand Config

Makes brands VISUALLY different, not just different data!

Each brand has colors, personality, tone → This generates CSS that makes
the UI actually look different for each brand.

Example:
────────
CalRiven (Technical, Blue):
  Primary: #2196f3 (blue)
  Secondary: #1976d2 (darker blue)
  → UI has blue gradients, technical feel

Ocean Dreams (Calm, Aqua):
  Primary: #00bcd4 (cyan)
  Secondary: #0097a7 (teal)
  → UI has aqua gradients, calm feel

DeathToData (Privacy, Dark):
  Primary: #424242 (dark gray)
  Secondary: #212121 (black)
  → UI has dark theme, privacy-focused feel

Usage:
    from brand_css_generator import generate_brand_css

    # Generate CSS for brand
    css = generate_brand_css(brand_config)

    # Inject into template
    return render_template('brand_page.html', brand_css=css)

Components Styled:
- Headers/Banners
- Buttons
- Cards
- Links
- Gradients
- Shadows
"""

import json
from typing import Dict, Any


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def adjust_lightness(hex_color: str, factor: float) -> str:
    """
    Adjust color lightness

    Args:
        hex_color: Hex color (#RRGGBB)
        factor: 1.0 = same, >1.0 = lighter, <1.0 = darker

    Returns:
        Adjusted hex color
    """
    r, g, b = hex_to_rgb(hex_color)

    # Adjust each component
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))

    return f'#{r:02x}{g:02x}{b:02x}'


def generate_brand_css(brand_config: Dict[str, Any], include_style_tag: bool = True) -> str:
    """
    Generate CSS from brand configuration

    Args:
        brand_config: Brand config dict with 'colors', 'personality', etc.
        include_style_tag: Whether to wrap in <style> tags

    Returns:
        CSS string (with or without <style> tags)
    """
    colors = brand_config.get('colors', {})

    # Default colors if not provided
    primary = colors.get('primary', '#667eea')
    secondary = colors.get('secondary', '#764ba2')
    accent = colors.get('accent', '#f093fb')

    # Generate variations
    primary_light = adjust_lightness(primary, 1.2)
    primary_dark = adjust_lightness(primary, 0.8)
    secondary_light = adjust_lightness(secondary, 1.2)
    secondary_dark = adjust_lightness(secondary, 0.8)

    # Convert to RGB for alpha variants
    primary_rgb = hex_to_rgb(primary)
    secondary_rgb = hex_to_rgb(secondary)

    css = f"""
/* ═══════════════════════════════════════════════════════════════
   Brand CSS: {brand_config.get('name', 'Unknown Brand')}
   Generated from brand configuration
   ═══════════════════════════════════════════════════════════════ */

:root {{
    /* Brand Colors */
    --brand-primary: {primary};
    --brand-primary-light: {primary_light};
    --brand-primary-dark: {primary_dark};
    --brand-primary-rgb: {primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]};

    --brand-secondary: {secondary};
    --brand-secondary-light: {secondary_light};
    --brand-secondary-dark: {secondary_dark};
    --brand-secondary-rgb: {secondary_rgb[0]}, {secondary_rgb[1]}, {secondary_rgb[2]};

    --brand-accent: {accent};

    /* Gradients */
    --brand-gradient: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
    --brand-gradient-radial: radial-gradient(circle, var(--brand-primary) 0%, var(--brand-secondary) 100%);
}}

/* ═══════════════════════════════════════════════════════════════
   Headers & Banners
   ═══════════════════════════════════════════════════════════════ */

.brand-header,
.brand-banner {{
    background: var(--brand-gradient);
    color: white;
}}

.brand-header h1,
.brand-banner h1 {{
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}}

/* ═══════════════════════════════════════════════════════════════
   Buttons
   ═══════════════════════════════════════════════════════════════ */

.btn-brand,
.btn-download,
.btn-submit-brand {{
    background: var(--brand-gradient);
    border: none;
    color: white;
    box-shadow: 0 4px 15px rgba(var(--brand-primary-rgb), 0.4);
    transition: all 0.3s ease;
}}

.btn-brand:hover,
.btn-download:hover,
.btn-submit-brand:hover {{
    box-shadow: 0 6px 20px rgba(var(--brand-primary-rgb), 0.6);
    transform: translateY(-2px);
}}

.btn-brand:active {{
    transform: translateY(0);
}}

/* Secondary buttons */
.btn-brand-secondary {{
    background: white;
    border: 2px solid var(--brand-primary);
    color: var(--brand-primary);
}}

.btn-brand-secondary:hover {{
    background: var(--brand-primary);
    color: white;
}}

/* ═══════════════════════════════════════════════════════════════
   Links
   ═══════════════════════════════════════════════════════════════ */

.brand-link,
a.brand-link {{
    color: var(--brand-primary);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s;
}}

.brand-link:hover,
a.brand-link:hover {{
    border-bottom-color: var(--brand-primary);
}}

/* ═══════════════════════════════════════════════════════════════
   Cards
   ═══════════════════════════════════════════════════════════════ */

.brand-card {{
    border-top: 4px solid var(--brand-primary);
    box-shadow: 0 2px 10px rgba(var(--brand-primary-rgb), 0.1);
    transition: box-shadow 0.3s, transform 0.3s;
}}

.brand-card:hover {{
    box-shadow: 0 4px 20px rgba(var(--brand-primary-rgb), 0.2);
    transform: translateY(-4px);
}}

.brand-card-header {{
    background: var(--brand-gradient);
    color: white;
    padding: 1rem;
    border-radius: 8px 8px 0 0;
}}

/* ═══════════════════════════════════════════════════════════════
   Badges & Labels
   ═══════════════════════════════════════════════════════════════ */

.brand-badge {{
    background: var(--brand-primary);
    color: white;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: 600;
}}

.brand-tag {{
    background: rgba(var(--brand-primary-rgb), 0.1);
    color: var(--brand-primary);
    padding: 4px 10px;
    border-radius: 16px;
    border: 1px solid rgba(var(--brand-primary-rgb), 0.3);
}}

/* ═══════════════════════════════════════════════════════════════
   Forms & Inputs
   ═══════════════════════════════════════════════════════════════ */

.brand-input:focus,
.brand-textarea:focus,
.brand-select:focus {{
    outline: none;
    border-color: var(--brand-primary);
    box-shadow: 0 0 0 3px rgba(var(--brand-primary-rgb), 0.1);
}}

.brand-checkbox:checked {{
    background-color: var(--brand-primary);
    border-color: var(--brand-primary);
}}

/* ═══════════════════════════════════════════════════════════════
   Progress & Loading
   ═══════════════════════════════════════════════════════════════ */

.brand-progress-bar {{
    background: var(--brand-gradient);
    height: 8px;
    border-radius: 4px;
}}

.brand-spinner {{
    border: 3px solid rgba(var(--brand-primary-rgb), 0.1);
    border-top-color: var(--brand-primary);
    border-radius: 50%;
    animation: brand-spin 0.8s linear infinite;
}}

@keyframes brand-spin {{
    to {{ transform: rotate(360deg); }}
}}

/* ═══════════════════════════════════════════════════════════════
   Alerts & Messages
   ═══════════════════════════════════════════════════════════════ */

.brand-alert-success {{
    background: rgba(var(--brand-primary-rgb), 0.1);
    border-left: 4px solid var(--brand-primary);
    color: var(--brand-primary-dark);
}}

.brand-alert-info {{
    background: rgba(var(--brand-secondary-rgb), 0.1);
    border-left: 4px solid var(--brand-secondary);
    color: var(--brand-secondary-dark);
}}

/* ═══════════════════════════════════════════════════════════════
   Navigation
   ═══════════════════════════════════════════════════════════════ */

.brand-nav-item.active {{
    color: var(--brand-primary);
    border-bottom: 2px solid var(--brand-primary);
}}

.brand-nav-item:hover {{
    color: var(--brand-primary);
}}

/* ═══════════════════════════════════════════════════════════════
   Highlights & Accents
   ═══════════════════════════════════════════════════════════════ */

.brand-highlight {{
    background: linear-gradient(120deg,
        rgba(var(--brand-primary-rgb), 0.1) 0%,
        rgba(var(--brand-secondary-rgb), 0.1) 100%);
    border-left: 4px solid var(--brand-primary);
    padding: 1rem;
    border-radius: 4px;
}}

.brand-divider {{
    height: 2px;
    background: var(--brand-gradient);
    border: none;
}}

/* ═══════════════════════════════════════════════════════════════
   Shadows
   ═══════════════════════════════════════════════════════════════ */

.brand-shadow-sm {{
    box-shadow: 0 2px 8px rgba(var(--brand-primary-rgb), 0.15);
}}

.brand-shadow-md {{
    box-shadow: 0 4px 16px rgba(var(--brand-primary-rgb), 0.2);
}}

.brand-shadow-lg {{
    box-shadow: 0 8px 24px rgba(var(--brand-primary-rgb), 0.25);
}}

/* ═══════════════════════════════════════════════════════════════
   QR Codes (Brand-Specific)
   ═══════════════════════════════════════════════════════════════ */

.brand-qr-container {{
    border: 4px solid var(--brand-primary);
    padding: 1rem;
    border-radius: 12px;
    background: white;
    box-shadow: 0 4px 20px rgba(var(--brand-primary-rgb), 0.3);
}}

.brand-qr-label {{
    background: var(--brand-gradient);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    text-align: center;
    font-weight: 600;
}}
"""

    if include_style_tag:
        return f"<style>\n{css}\n</style>"
    else:
        return css


def generate_inline_brand_style(brand_config: Dict[str, Any]) -> str:
    """
    Generate inline style attribute for single element

    Args:
        brand_config: Brand config dict

    Returns:
        String for use in style="" attribute
    """
    colors = brand_config.get('colors', {})
    primary = colors.get('primary', '#667eea')
    secondary = colors.get('secondary', '#764ba2')

    return f"background: linear-gradient(135deg, {primary} 0%, {secondary} 100%); color: white;"


def main():
    """Test CSS generation"""
    # Test brands
    test_brands = [
        {
            'name': 'CalRiven',
            'colors': {
                'primary': '#2196f3',
                'secondary': '#1976d2',
                'accent': '#64b5f6'
            }
        },
        {
            'name': 'Ocean Dreams',
            'colors': {
                'primary': '#00bcd4',
                'secondary': '#0097a7',
                'accent': '#4dd0e1'
            }
        },
        {
            'name': 'DeathToData',
            'colors': {
                'primary': '#424242',
                'secondary': '#212121',
                'accent': '#616161'
            }
        }
    ]

    for brand in test_brands:
        print("=" * 70)
        print(f"Brand: {brand['name']}")
        print("=" * 70)
        print()
        css = generate_brand_css(brand, include_style_tag=False)
        print(css[:500] + "...")  # First 500 chars
        print()
        print(f"Inline style: {generate_inline_brand_style(brand)}")
        print()


if __name__ == '__main__':
    main()

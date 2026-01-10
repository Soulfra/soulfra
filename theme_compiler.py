#!/usr/bin/env python3
"""
Universal Theme Compiler

Reads brand configuration files (brand/{domain}-complete.json)
and generates CSS theme files with variables.

This creates a SINGLE SOURCE OF TRUTH for theming across:
- Domain manager UI
- Production blogs
- Newsletters
- Faucets
- Marketing pages

Usage:
    python theme_compiler.py --domain soulfra
    python theme_compiler.py --all

    # Or in code:
    from theme_compiler import ThemeCompiler
    compiler = ThemeCompiler()
    compiler.compile_theme('soulfra')
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
import colorsys


class ThemeCompiler:
    """Compiles brand configs into universal CSS themes"""

    def __init__(self, domains_dir='../domains', output_dir=None):
        self.domains_dir = Path(domains_dir)
        self.output_dir = Path(output_dir) if output_dir else self.domains_dir

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_rgba(self, rgb: Tuple[int, int, int], alpha: float) -> str:
        """Convert RGB to RGBA string"""
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"

    def darken(self, hex_color: str, factor: float = 0.3) -> str:
        """Darken a hex color by factor (0-1)"""
        rgb = self.hex_to_rgb(hex_color)
        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        # Darken by reducing value
        v = max(0, v * (1 - factor))
        # Convert back to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        # Convert to hex
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def lighten(self, hex_color: str, factor: float = 0.3) -> str:
        """Lighten a hex color by factor (0-1)"""
        rgb = self.hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        v = min(1, v + (1 - v) * factor)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def read_brand_config(self, domain: str) -> Optional[Dict]:
        """Read brand configuration JSON file"""
        # Try multiple possible paths
        possible_paths = [
            self.domains_dir / domain / 'brand' / f'{domain}-complete.json',
            self.domains_dir / domain / 'brand' / f'{domain}.json',
            self.domains_dir / domain / f'{domain}-complete.json'
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)

        print(f"❌ Brand config not found for {domain}")
        print(f"   Searched: {[str(p) for p in possible_paths]}")
        return None

    def extract_colors(self, brand_config: Dict) -> Dict[str, str]:
        """Extract colors from brand config"""
        colors = {}

        # Try to find primary color in styling section
        styling = brand_config.get('concepts', {}).get('styling', [])
        if styling and len(styling) > 0:
            metadata = styling[0].get('metadata', {})
            if 'primaryColor' in metadata:
                colors['primary'] = metadata['primaryColor']

        # Fallback to a default if not found
        if 'primary' not in colors:
            print(f"⚠️  No primaryColor found in brand config, using default")
            colors['primary'] = '#3b82f6'  # Default blue

        # Generate derived colors
        primary = colors['primary']
        colors['primary_dark'] = self.darken(primary, 0.3)
        colors['primary_darker'] = self.darken(primary, 0.5)
        colors['primary_light'] = self.lighten(primary, 0.3)
        colors['primary_lighter'] = self.lighten(primary, 0.5)

        return colors

    def generate_css(self, domain: str, colors: Dict[str, str]) -> str:
        """Generate CSS with theme variables"""

        primary_rgb = self.hex_to_rgb(colors['primary'])

        css = f"""/**
 * Universal Theme for {domain}
 * Auto-generated from brand config
 *
 * DO NOT EDIT MANUALLY - Changes will be overwritten
 * Edit the brand config and recompile instead:
 *   python theme_compiler.py --domain {domain}
 */

:root {{
    /* ========================================
       BRAND COLORS (from brand config)
    ======================================== */
    --brand-primary: {colors['primary']};
    --brand-primary-rgb: {primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]};
    --brand-primary-dark: {colors['primary_dark']};
    --brand-primary-darker: {colors['primary_darker']};
    --brand-primary-light: {colors['primary_light']};
    --brand-primary-lighter: {colors['primary_lighter']};

    /* ========================================
       TARGETING COLORS (for domain manager)
    ======================================== */
    --target-0-primary: {colors['primary']};
    --target-0-bg: rgba(var(--brand-primary-rgb), 0.2);
    --target-0-shadow: rgba(var(--brand-primary-rgb), 0.4);

    --target-1-primary: {colors['primary_light']};
    --target-1-bg: rgba(var(--brand-primary-rgb), 0.15);
    --target-1-shadow: rgba(var(--brand-primary-rgb), 0.3);

    --target-2-primary: {colors['primary_dark']};
    --target-2-bg: rgba(var(--brand-primary-rgb), 0.25);
    --target-2-shadow: rgba(var(--brand-primary-rgb), 0.5);

    --target-3-primary: {colors['primary_lighter']};
    --target-3-bg: rgba(var(--brand-primary-rgb), 0.1);
    --target-3-shadow: rgba(var(--brand-primary-rgb), 0.2);

    --target-4-primary: {colors['primary_darker']};
    --target-4-bg: rgba(var(--brand-primary-rgb), 0.3);
    --target-4-shadow: rgba(var(--brand-primary-rgb), 0.6);

    /* More targets use variations of primary */
    --target-5-primary: {colors['primary']};
    --target-5-bg: rgba(var(--brand-primary-rgb), 0.18);
    --target-5-shadow: rgba(var(--brand-primary-rgb), 0.35);

    --target-6-primary: {colors['primary_light']};
    --target-6-bg: rgba(var(--brand-primary-rgb), 0.12);
    --target-6-shadow: rgba(var(--brand-primary-rgb), 0.25);

    --target-7-primary: {colors['primary_dark']};
    --target-7-bg: rgba(var(--brand-primary-rgb), 0.22);
    --target-7-shadow: rgba(var(--brand-primary-rgb), 0.45);

    /* ========================================
       BLOG STYLES
    ======================================== */
    --blog-bg-start: {colors['primary_darker']};
    --blog-bg-end: {colors['primary_dark']};
    --blog-bg: linear-gradient(135deg, var(--blog-bg-start) 0%, var(--blog-bg-end) 100%);
    --blog-text-primary: #e0e0e0;
    --blog-text-secondary: #a0aec0;
    --blog-accent: {colors['primary']};
    --blog-link: {colors['primary_light']};
    --blog-link-hover: {colors['primary_lighter']};

    /* ========================================
       NEWSLETTER STYLES
    ======================================== */
    --newsletter-accent: {colors['primary']};
    --newsletter-header-bg: {colors['primary']};
    --newsletter-header-text: #ffffff;
    --newsletter-cta-bg: {colors['primary']};
    --newsletter-cta-text: #ffffff;
    --newsletter-link: {colors['primary_light']};

    /* ========================================
       UI COMPONENTS
    ======================================== */
    --button-primary-bg: {colors['primary']};
    --button-primary-hover: {colors['primary_light']};
    --button-primary-text: #ffffff;

    --badge-primary-bg: {colors['primary']};
    --badge-primary-text: #ffffff;

    --link-color: {colors['primary_light']};
    --link-hover: {colors['primary_lighter']};

    /* ========================================
       STATUS COLORS (brand-aware)
    ======================================== */
    --status-success: {colors['primary']};
    --status-warning: #f59e0b;
    --status-error: #ef4444;
    --status-info: {colors['primary_light']};
}}

/* ========================================
   UTILITY CLASSES (brand-aware)
======================================== */

.text-brand {{
    color: var(--brand-primary);
}}

.bg-brand {{
    background-color: var(--brand-primary);
}}

.border-brand {{
    border-color: var(--brand-primary);
}}

.btn-brand {{
    background: var(--button-primary-bg);
    color: var(--button-primary-text);
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
}}

.btn-brand:hover {{
    background: var(--button-primary-hover);
}}

.link-brand {{
    color: var(--link-color);
    text-decoration: none;
}}

.link-brand:hover {{
    color: var(--link-hover);
}}
"""
        return css

    def compile_theme(self, domain: str) -> Optional[Path]:
        """Compile theme for a single domain"""
        print(f"\n🎨 Compiling theme for {domain}...")

        # Read brand config
        brand_config = self.read_brand_config(domain)
        if not brand_config:
            return None

        # Extract colors
        colors = self.extract_colors(brand_config)
        print(f"   Primary color: {colors['primary']}")

        # Generate CSS
        css = self.generate_css(domain, colors)

        # Save to domain directory
        output_path = self.output_dir / domain / f'theme-{domain}.css'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(css)

        print(f"   ✅ Generated: {output_path}")
        print(f"   Size: {len(css)} bytes")

        return output_path

    def compile_all_themes(self) -> Dict[str, Optional[Path]]:
        """Compile themes for all domains with brand configs"""
        print("🎨 Compiling themes for all domains...\n")

        results = {}

        # Find all domain directories
        if not self.domains_dir.exists():
            print(f"❌ Domains directory not found: {self.domains_dir}")
            return results

        for domain_dir in self.domains_dir.iterdir():
            if not domain_dir.is_dir():
                continue

            domain = domain_dir.name

            # Skip special directories
            if domain.startswith('.') or domain.startswith('--'):
                continue

            # Check if brand config exists
            brand_dir = domain_dir / 'brand'
            if not brand_dir.exists():
                continue

            # Compile theme
            theme_path = self.compile_theme(domain)
            results[domain] = theme_path

        print(f"\n✅ Compiled {len([p for p in results.values() if p])} themes")
        return results


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='Compile brand configs into universal CSS themes'
    )
    parser.add_argument(
        '--domain',
        help='Compile theme for specific domain (e.g., soulfra)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Compile themes for all domains'
    )
    parser.add_argument(
        '--domains-dir',
        default='../domains',
        help='Path to domains directory'
    )

    args = parser.parse_args()

    compiler = ThemeCompiler(domains_dir=args.domains_dir)

    if args.all:
        compiler.compile_all_themes()
    elif args.domain:
        compiler.compile_theme(args.domain)
    else:
        print("Please specify --domain or --all")
        parser.print_help()


if __name__ == '__main__':
    main()

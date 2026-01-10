#!/usr/bin/env python3
"""
Shipwright - Theme Builder CLI

Build, upgrade, and manage Soulfra themes across ship classes.

Usage:
    ./shipwright.py build --class schooner --base ocean-dreams --name "Ocean Dreams Schooner"
    ./shipwright.py upgrade ocean-dreams --to schooner
    ./shipwright.py validate ocean-dreams-frigate
    ./shipwright.py list --class frigate
    ./shipwright.py stats

Examples:
    # Build new Schooner class theme based on Dinghy
    ./shipwright.py build --class schooner --base calriven --name "CalRiven Enhanced"

    # Upgrade existing theme to next class
    ./shipwright.py upgrade deathtodata --to frigate

    # Validate theme meets class requirements
    ./shipwright.py validate ocean-dreams-schooner

    # List all themes in a class
    ./shipwright.py list --class dinghy
"""

import argparse
import yaml
import os
from pathlib import Path
import sys

class Shipwright:
    """Theme builder and manager"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.themes_dir = self.project_root / 'themes'
        self.manifest_path = self.themes_dir / 'manifest.yaml'

        # Load manifest
        with open(self.manifest_path, 'r') as f:
            self.manifest = yaml.safe_load(f)

        self.ship_classes = self.manifest['ship_classes']
        self.themes = self.manifest['themes']

    def build_theme(self, ship_class: str, base_theme: str, name: str):
        """Build new theme from base theme"""
        print(f"\n🔨 Building {ship_class} class theme: {name}")
        print(f"   Base: {base_theme}")

        if base_theme not in self.themes:
            print(f"❌ Base theme '{base_theme}' not found!")
            return

        base = self.themes[base_theme]
        class_info = self.ship_classes[ship_class]

        # Generate slug from name
        slug = name.lower().replace(' ', '-')

        # Read base theme CSS
        base_css_path = self.themes_dir / f"{base_theme}.css"
        if not base_css_path.exists():
            print(f"❌ Base theme CSS not found: {base_css_path}")
            return

        with open(base_css_path, 'r') as f:
            base_css = f.read()

        # Generate enhanced CSS based on ship class
        if ship_class == 'schooner':
            enhanced_css = self._enhance_to_schooner(base_css, base, name)
        elif ship_class == 'frigate':
            enhanced_css = self._enhance_to_frigate(base_css, base, name)
        elif ship_class == 'galleon':
            enhanced_css = self._enhance_to_galleon(base_css, base, name)
        else:
            print(f"❌ Unknown ship class: {ship_class}")
            return

        # Write new theme CSS
        output_path = self.themes_dir / f"{slug}.css"
        with open(output_path, 'w') as f:
            f.write(enhanced_css)

        print(f"✅ Created: {output_path}")
        print(f"   Lines: {len(enhanced_css.splitlines())}")
        print(f"\n📝 Add to manifest.yaml manually:")
        print(f"""
  {slug}:
    name: "{name}"
    emoji: "{base['emoji']}⛵"
    class: {ship_class}
    tier: free
    extends: {base_theme}
    colors:
      primary: "{base['colors']['primary']}"
      background: "{base['colors']['background']}"
      text: "{base['colors']['text']}"
""")

    def _enhance_to_schooner(self, base_css: str, base_theme: dict, name: str) -> str:
        """Enhance Dinghy to Schooner class"""
        colors = base_theme['colors']
        emoji = base_theme['emoji']

        template = f'''/* {name} - Schooner Class {emoji}⛵ */
/* Enhanced: Typography + Spacing + Components */

/* Layer 1: Emoji brand */
.logo::before {{ content: "{emoji} "; }}

/* Layer 2: Background */
body {{
  background: linear-gradient(120deg, {colors['background']} 0%, {colors['background']} 100%);
  background-size: 200% 200%;
  animation: flow 60s ease-in-out infinite;
}}

@keyframes flow {{
  0%, 100% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
}}

/* Layer 3: Typography system */
body {{
  color: {colors['text']};
  font-size: 16px;
  line-height: 1.65;
  letter-spacing: 0.01em;
}}

h1, h2, h3 {{
  color: {colors['text']};
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 0.75em;
}}

h1 {{ font-size: 2.5em; letter-spacing: -0.02em; }}
h2 {{ font-size: 1.75em; letter-spacing: -0.01em; }}
h3 {{ font-size: 1.25em; }}

p {{ margin-bottom: 1em; }}

/* Layer 4: Links & Interaction */
a {{
  color: {colors['primary']};
  text-decoration: underline;
  text-decoration-color: rgba(0, 0, 0, 0.3);
  transition: all 200ms ease;
}}

a:hover {{
  opacity: 0.7;
}}

/* Layer 5: Spacing system */
.hero {{ margin: 3em 0; }}
.post-card {{ margin-bottom: 2em; padding: 1.5em; }}
section {{ margin: 2.5em 0; }}

/* Layer 6: Component styling */
.post-card {{
  background: rgba(255, 255, 255, 0.8);
  border-left: 4px solid {colors['primary']};
  border-radius: 6px;
  transition: transform 200ms ease, box-shadow 200ms ease;
}}

.post-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}}

.cta-button {{
  background: {colors['primary']};
  color: white;
  padding: 0.75em 1.5em;
  border: 2px solid {colors['text']};
  border-radius: 6px;
  text-decoration: none;
  transition: all 200ms ease;
}}

.cta-button:hover {{
  opacity: 0.8;
  transform: translateY(-1px);
}}
'''
        return template

    def _enhance_to_frigate(self, base_css: str, base_theme: dict, name: str) -> str:
        """Enhance to Frigate class (placeholder - use existing frigate theme as template)"""
        print("⚠️  Frigate enhancement not fully implemented - use existing frigate themes as templates")
        return base_css

    def _enhance_to_galleon(self, base_css: str, base_theme: dict, name: str) -> str:
        """Enhance to Galleon class (placeholder)"""
        print("⚠️  Galleon class not yet implemented")
        return base_css

    def validate_theme(self, theme_slug: str):
        """Validate theme meets class requirements"""
        print(f"\n🔍 Validating: {theme_slug}")

        if theme_slug not in self.themes:
            print(f"❌ Theme not in manifest: {theme_slug}")
            return False

        theme = self.themes[theme_slug]
        theme_class = theme.get('class', 'dinghy')
        class_info = self.ship_classes[theme_class]

        # Check CSS file exists
        css_path = self.themes_dir / f"{theme_slug}.css"
        if not css_path.exists():
            print(f"❌ CSS file not found: {css_path}")
            return False

        # Check line count
        with open(css_path, 'r') as f:
            lines = len(f.readlines())

        print(f"✅ CSS file found: {css_path}")
        print(f"   Lines: {lines}")
        print(f"   Class: {theme_class} ({class_info['lines']})")

        # Validate line count matches class
        if theme_class == 'dinghy' and lines > 40:
            print(f"⚠️  Dinghy themes should be ~26 lines, got {lines}")
        elif theme_class == 'schooner' and (lines < 50 or lines > 100):
            print(f"⚠️  Schooner themes should be 50-80 lines, got {lines}")
        elif theme_class == 'frigate' and (lines < 120 or lines > 200):
            print(f"⚠️  Frigate themes should be 120-180 lines, got {lines}")

        print(f"✅ Theme '{theme_slug}' validated!")
        return True

    def list_themes(self, ship_class: str = None):
        """List all themes, optionally filtered by class"""
        if ship_class:
            print(f"\n🚢 {ship_class.title()} Class Themes:")
            filtered = {k: v for k, v in self.themes.items() if v.get('class') == ship_class}
        else:
            print(f"\n🚢 All Themes:")
            filtered = self.themes

        for slug, theme in filtered.items():
            emoji = theme.get('emoji', '📄')
            name = theme.get('name', slug)
            theme_class = theme.get('class', 'dinghy')
            tier = theme.get('tier', 'free')
            print(f"   {emoji} {name} ({theme_class} | {tier})")

    def stats(self):
        """Show shipyard statistics"""
        metadata = self.manifest['metadata']

        print("\n📊 Shipyard Statistics")
        print("=" * 50)
        print(f"Total Themes: {metadata['total_themes']}")
        print(f"Ship Classes: {metadata['total_classes']}")
        print(f"  - Dinghy: {metadata['dinghy_count']}")
        print(f"  - Schooner: {metadata['schooner_count']}")
        print(f"  - Frigate: {metadata['frigate_count']}")
        print(f"  - Galleon: {metadata['galleon_count']}")
        print(f"\nVersion: {metadata['version']}")
        print(f"Updated: {metadata['updated']}")


def main():
    parser = argparse.ArgumentParser(description='Shipwright - Theme Builder CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build new theme')
    build_parser.add_argument('--class', dest='ship_class', required=True,
                             choices=['schooner', 'frigate', 'galleon'],
                             help='Ship class to build')
    build_parser.add_argument('--base', required=True, help='Base theme to extend')
    build_parser.add_argument('--name', required=True, help='Name of new theme')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate theme')
    validate_parser.add_argument('theme', help='Theme slug to validate')

    # List command
    list_parser = subparsers.add_parser('list', help='List themes')
    list_parser.add_argument('--class', dest='ship_class', help='Filter by ship class')

    # Stats command
    subparsers.add_parser('stats', help='Show shipyard statistics')

    args = parser.parse_args()

    shipwright = Shipwright()

    if args.command == 'build':
        shipwright.build_theme(args.ship_class, args.base, args.name)
    elif args.command == 'validate':
        shipwright.validate_theme(args.theme)
    elif args.command == 'list':
        shipwright.list_themes(args.ship_class)
    elif args.command == 'stats':
        shipwright.stats()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

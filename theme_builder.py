#!/usr/bin/env python3
"""
Theme Builder - Customer Theme System for Building Blogs from Scratch

Allows customers to:
- Choose from pre-built themes
- Customize colors, fonts, layouts
- Build their own theme from scratch
- Export/import themes (reproducible)
- Preview themes before applying

Usage:
    from theme_builder import ThemeBuilder

    # Create builder
    builder = ThemeBuilder()

    # List available themes
    themes = builder.list_themes()

    # Apply theme
    builder.apply_theme('minimal-dark')

    # Customize theme
    builder.customize_theme('minimal-dark', {
        'primary_color': '#3b82f6',
        'font_family': 'Inter, sans-serif'
    })

    # Export theme
    theme_config = builder.export_theme('my-custom-theme')

    # Import theme
    builder.import_theme(theme_config)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil


@dataclass
class ThemeColors:
    """Theme color scheme"""
    # Primary colors
    primary: str = '#3b82f6'
    secondary: str = '#8b5cf6'
    accent: str = '#10b981'

    # Background colors
    bg_primary: str = '#ffffff'
    bg_secondary: str = '#f3f4f6'
    bg_tertiary: str = '#e5e7eb'

    # Text colors
    text_primary: str = '#111827'
    text_secondary: str = '#6b7280'
    text_tertiary: str = '#9ca3af'

    # Status colors
    success: str = '#10b981'
    warning: str = '#f59e0b'
    error: str = '#ef4444'
    info: str = '#3b82f6'

    # Border colors
    border: str = '#e5e7eb'
    border_focus: str = '#3b82f6'


@dataclass
class ThemeTypography:
    """Theme typography settings"""
    # Font families
    font_family: str = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    font_family_mono: str = 'Monaco, Courier, monospace'

    # Font sizes
    font_size_xs: str = '0.75rem'
    font_size_sm: str = '0.875rem'
    font_size_base: str = '1rem'
    font_size_lg: str = '1.125rem'
    font_size_xl: str = '1.25rem'
    font_size_2xl: str = '1.5rem'
    font_size_3xl: str = '1.875rem'
    font_size_4xl: str = '2.25rem'

    # Line heights
    line_height_tight: str = '1.25'
    line_height_normal: str = '1.5'
    line_height_relaxed: str = '1.75'


@dataclass
class ThemeSpacing:
    """Theme spacing settings"""
    xs: str = '0.25rem'
    sm: str = '0.5rem'
    md: str = '1rem'
    lg: str = '1.5rem'
    xl: str = '2rem'
    xxl: str = '3rem'


@dataclass
class ThemeLayout:
    """Theme layout settings"""
    max_width: str = '1200px'
    sidebar_width: str = '250px'
    header_height: str = '60px'
    footer_height: str = '80px'
    border_radius: str = '0.375rem'
    border_width: str = '1px'


@dataclass
class Theme:
    """Complete theme configuration"""
    name: str
    display_name: str
    description: str
    author: str = 'Soulfra'
    version: str = '1.0.0'
    created_at: str = None

    # Theme components
    colors: ThemeColors = None
    typography: ThemeTypography = None
    spacing: ThemeSpacing = None
    layout: ThemeLayout = None

    # Additional settings
    dark_mode: bool = False
    custom_css: str = ''

    def __post_init__(self):
        if self.colors is None:
            self.colors = ThemeColors()
        if self.typography is None:
            self.typography = ThemeTypography()
        if self.spacing is None:
            self.spacing = ThemeSpacing()
        if self.layout is None:
            self.layout = ThemeLayout()
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ThemeBuilder:
    """Build and manage themes"""

    def __init__(self, themes_dir: str = 'themes'):
        """
        Initialize theme builder

        Args:
            themes_dir: Directory to store themes
        """
        self.themes_dir = Path(themes_dir)
        self.themes_dir.mkdir(exist_ok=True)

        # Ensure built-in themes exist
        self._create_builtin_themes()

    def _create_builtin_themes(self):
        """Create built-in themes if they don't exist"""
        builtin_themes = [
            self._create_minimal_light_theme(),
            self._create_minimal_dark_theme(),
            self._create_professional_theme(),
            self._create_creative_theme(),
            self._create_technical_theme()
        ]

        for theme in builtin_themes:
            theme_path = self.themes_dir / f"{theme.name}.json"
            if not theme_path.exists():
                self.save_theme(theme)

    def _create_minimal_light_theme(self) -> Theme:
        """Create minimal light theme"""
        return Theme(
            name='minimal-light',
            display_name='Minimal Light',
            description='Clean and minimal light theme',
            dark_mode=False,
            colors=ThemeColors(
                primary='#000000',
                secondary='#666666',
                accent='#0066cc',
                bg_primary='#ffffff',
                bg_secondary='#f9fafb',
                text_primary='#000000',
                text_secondary='#666666'
            ),
            typography=ThemeTypography(
                font_family='"Inter", -apple-system, sans-serif',
                font_size_base='16px',
                line_height_normal='1.6'
            )
        )

    def _create_minimal_dark_theme(self) -> Theme:
        """Create minimal dark theme"""
        return Theme(
            name='minimal-dark',
            display_name='Minimal Dark',
            description='Clean and minimal dark theme',
            dark_mode=True,
            colors=ThemeColors(
                primary='#ffffff',
                secondary='#a0aec0',
                accent='#60a5fa',
                bg_primary='#1a202c',
                bg_secondary='#2d3748',
                bg_tertiary='#4a5568',
                text_primary='#ffffff',
                text_secondary='#cbd5e0',
                text_tertiary='#a0aec0',
                border='#4a5568'
            ),
            typography=ThemeTypography(
                font_family='"JetBrains Mono", monospace'
            )
        )

    def _create_professional_theme(self) -> Theme:
        """Create professional business theme"""
        return Theme(
            name='professional',
            display_name='Professional',
            description='Professional business theme with blue accents',
            dark_mode=False,
            colors=ThemeColors(
                primary='#1e40af',
                secondary='#64748b',
                accent='#0ea5e9',
                bg_primary='#ffffff',
                bg_secondary='#f8fafc',
                text_primary='#0f172a',
                text_secondary='#475569'
            ),
            typography=ThemeTypography(
                font_family='"Helvetica Neue", Arial, sans-serif',
                font_size_base='15px'
            ),
            layout=ThemeLayout(
                max_width='1400px',
                border_radius='0.25rem'
            )
        )

    def _create_creative_theme(self) -> Theme:
        """Create creative/artistic theme"""
        return Theme(
            name='creative',
            display_name='Creative',
            description='Colorful creative theme for artists and designers',
            dark_mode=False,
            colors=ThemeColors(
                primary='#ec4899',
                secondary='#8b5cf6',
                accent='#f59e0b',
                bg_primary='#fefce8',
                bg_secondary='#fef3c7',
                text_primary='#78350f',
                text_secondary='#92400e'
            ),
            typography=ThemeTypography(
                font_family='"Comic Sans MS", "Marker Felt", sans-serif',
                font_size_base='17px',
                line_height_normal='1.7'
            ),
            layout=ThemeLayout(
                border_radius='1rem'
            )
        )

    def _create_technical_theme(self) -> Theme:
        """Create technical/developer theme"""
        return Theme(
            name='technical',
            display_name='Technical',
            description='Developer-focused theme with monospace fonts',
            dark_mode=True,
            colors=ThemeColors(
                primary='#22c55e',
                secondary='#a3e635',
                accent='#84cc16',
                bg_primary='#0c0c0c',
                bg_secondary='#1c1c1c',
                bg_tertiary='#2c2c2c',
                text_primary='#d4d4d4',
                text_secondary='#a1a1a1',
                border='#333333'
            ),
            typography=ThemeTypography(
                font_family='"Fira Code", "JetBrains Mono", monospace',
                font_family_mono='"Fira Code", monospace',
                font_size_base='14px',
                line_height_normal='1.5'
            ),
            layout=ThemeLayout(
                max_width='1600px',
                border_radius='0'
            )
        )

    def list_themes(self) -> List[Dict]:
        """
        List all available themes

        Returns:
            List of theme metadata dicts
        """
        themes = []

        for theme_file in self.themes_dir.glob('*.json'):
            with open(theme_file, 'r') as f:
                theme_data = json.load(f)
                themes.append({
                    'name': theme_data['name'],
                    'display_name': theme_data['display_name'],
                    'description': theme_data['description'],
                    'author': theme_data.get('author', 'Unknown'),
                    'dark_mode': theme_data.get('dark_mode', False)
                })

        return themes

    def get_theme(self, theme_name: str) -> Optional[Theme]:
        """
        Load theme by name

        Args:
            theme_name: Name of theme to load

        Returns:
            Theme object or None if not found
        """
        theme_path = self.themes_dir / f"{theme_name}.json"

        if not theme_path.exists():
            return None

        with open(theme_path, 'r') as f:
            theme_data = json.load(f)

        # Reconstruct theme object
        theme = Theme(
            name=theme_data['name'],
            display_name=theme_data['display_name'],
            description=theme_data['description'],
            author=theme_data.get('author', 'Soulfra'),
            version=theme_data.get('version', '1.0.0'),
            created_at=theme_data.get('created_at'),
            dark_mode=theme_data.get('dark_mode', False),
            custom_css=theme_data.get('custom_css', ''),
            colors=ThemeColors(**theme_data['colors']),
            typography=ThemeTypography(**theme_data['typography']),
            spacing=ThemeSpacing(**theme_data['spacing']),
            layout=ThemeLayout(**theme_data['layout'])
        )

        return theme

    def save_theme(self, theme: Theme) -> Path:
        """
        Save theme to disk

        Args:
            theme: Theme object to save

        Returns:
            Path to saved theme file
        """
        theme_path = self.themes_dir / f"{theme.name}.json"

        # Convert to dict
        theme_dict = {
            'name': theme.name,
            'display_name': theme.display_name,
            'description': theme.description,
            'author': theme.author,
            'version': theme.version,
            'created_at': theme.created_at,
            'dark_mode': theme.dark_mode,
            'custom_css': theme.custom_css,
            'colors': asdict(theme.colors),
            'typography': asdict(theme.typography),
            'spacing': asdict(theme.spacing),
            'layout': asdict(theme.layout)
        }

        with open(theme_path, 'w') as f:
            json.dump(theme_dict, f, indent=2)

        return theme_path

    def customize_theme(self, base_theme_name: str, new_theme_name: str,
                       customizations: Dict[str, Any]) -> Theme:
        """
        Create customized theme from base theme

        Args:
            base_theme_name: Name of base theme
            new_theme_name: Name for new theme
            customizations: Dict of customizations to apply

        Returns:
            New customized Theme object
        """
        # Load base theme
        base_theme = self.get_theme(base_theme_name)
        if not base_theme:
            raise ValueError(f"Base theme '{base_theme_name}' not found")

        # Create new theme
        new_theme = Theme(
            name=new_theme_name,
            display_name=customizations.get('display_name', new_theme_name.title()),
            description=customizations.get('description', f'Custom theme based on {base_theme.display_name}'),
            author=customizations.get('author', 'Custom'),
            dark_mode=customizations.get('dark_mode', base_theme.dark_mode),
            custom_css=customizations.get('custom_css', base_theme.custom_css),
            colors=base_theme.colors,
            typography=base_theme.typography,
            spacing=base_theme.spacing,
            layout=base_theme.layout
        )

        # Apply customizations
        if 'colors' in customizations:
            for key, value in customizations['colors'].items():
                setattr(new_theme.colors, key, value)

        if 'typography' in customizations:
            for key, value in customizations['typography'].items():
                setattr(new_theme.typography, key, value)

        if 'spacing' in customizations:
            for key, value in customizations['spacing'].items():
                setattr(new_theme.spacing, key, value)

        if 'layout' in customizations:
            for key, value in customizations['layout'].items():
                setattr(new_theme.layout, key, value)

        # Save new theme
        self.save_theme(new_theme)

        return new_theme

    def export_theme(self, theme_name: str) -> Dict:
        """
        Export theme as JSON

        Args:
            theme_name: Name of theme to export

        Returns:
            Theme configuration dict
        """
        theme = self.get_theme(theme_name)
        if not theme:
            raise ValueError(f"Theme '{theme_name}' not found")

        return {
            'name': theme.name,
            'display_name': theme.display_name,
            'description': theme.description,
            'author': theme.author,
            'version': theme.version,
            'dark_mode': theme.dark_mode,
            'custom_css': theme.custom_css,
            'colors': asdict(theme.colors),
            'typography': asdict(theme.typography),
            'spacing': asdict(theme.spacing),
            'layout': asdict(theme.layout)
        }

    def import_theme(self, theme_config: Dict) -> Theme:
        """
        Import theme from JSON

        Args:
            theme_config: Theme configuration dict

        Returns:
            Imported Theme object
        """
        theme = Theme(
            name=theme_config['name'],
            display_name=theme_config['display_name'],
            description=theme_config['description'],
            author=theme_config.get('author', 'Imported'),
            version=theme_config.get('version', '1.0.0'),
            dark_mode=theme_config.get('dark_mode', False),
            custom_css=theme_config.get('custom_css', ''),
            colors=ThemeColors(**theme_config['colors']),
            typography=ThemeTypography(**theme_config['typography']),
            spacing=ThemeSpacing(**theme_config['spacing']),
            layout=ThemeLayout(**theme_config['layout'])
        )

        self.save_theme(theme)
        return theme

    def generate_css(self, theme: Theme) -> str:
        """
        Generate CSS from theme

        Args:
            theme: Theme to generate CSS for

        Returns:
            CSS string
        """
        css = f"""/* Theme: {theme.display_name} */
/* Generated by Soulfra Theme Builder */

:root {{
    /* Colors */
    --color-primary: {theme.colors.primary};
    --color-secondary: {theme.colors.secondary};
    --color-accent: {theme.colors.accent};

    --color-bg-primary: {theme.colors.bg_primary};
    --color-bg-secondary: {theme.colors.bg_secondary};
    --color-bg-tertiary: {theme.colors.bg_tertiary};

    --color-text-primary: {theme.colors.text_primary};
    --color-text-secondary: {theme.colors.text_secondary};
    --color-text-tertiary: {theme.colors.text_tertiary};

    --color-success: {theme.colors.success};
    --color-warning: {theme.colors.warning};
    --color-error: {theme.colors.error};
    --color-info: {theme.colors.info};

    --color-border: {theme.colors.border};
    --color-border-focus: {theme.colors.border_focus};

    /* Typography */
    --font-family: {theme.typography.font_family};
    --font-family-mono: {theme.typography.font_family_mono};

    --font-size-xs: {theme.typography.font_size_xs};
    --font-size-sm: {theme.typography.font_size_sm};
    --font-size-base: {theme.typography.font_size_base};
    --font-size-lg: {theme.typography.font_size_lg};
    --font-size-xl: {theme.typography.font_size_xl};
    --font-size-2xl: {theme.typography.font_size_2xl};
    --font-size-3xl: {theme.typography.font_size_3xl};
    --font-size-4xl: {theme.typography.font_size_4xl};

    --line-height-tight: {theme.typography.line_height_tight};
    --line-height-normal: {theme.typography.line_height_normal};
    --line-height-relaxed: {theme.typography.line_height_relaxed};

    /* Spacing */
    --spacing-xs: {theme.spacing.xs};
    --spacing-sm: {theme.spacing.sm};
    --spacing-md: {theme.spacing.md};
    --spacing-lg: {theme.spacing.lg};
    --spacing-xl: {theme.spacing.xl};
    --spacing-xxl: {theme.spacing.xxl};

    /* Layout */
    --max-width: {theme.layout.max_width};
    --sidebar-width: {theme.layout.sidebar_width};
    --header-height: {theme.layout.header_height};
    --footer-height: {theme.layout.footer_height};
    --border-radius: {theme.layout.border_radius};
    --border-width: {theme.layout.border_width};
}}

body {{
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height-normal);
    color: var(--color-text-primary);
    background-color: var(--color-bg-primary);
}}

/* Custom CSS */
{theme.custom_css}
"""

        return css

    def apply_theme(self, theme_name: str, output_path: str = 'static/css/theme.css') -> Path:
        """
        Apply theme by generating CSS file

        Args:
            theme_name: Name of theme to apply
            output_path: Path to write CSS file

        Returns:
            Path to generated CSS file
        """
        theme = self.get_theme(theme_name)
        if not theme:
            raise ValueError(f"Theme '{theme_name}' not found")

        css = self.generate_css(theme)

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write CSS
        with open(output_file, 'w') as f:
            f.write(css)

        return output_file

    def delete_theme(self, theme_name: str) -> bool:
        """
        Delete theme

        Args:
            theme_name: Name of theme to delete

        Returns:
            True if deleted, False if not found
        """
        theme_path = self.themes_dir / f"{theme_name}.json"

        if not theme_path.exists():
            return False

        theme_path.unlink()
        return True


# CLI for testing
if __name__ == '__main__':
    import sys

    builder = ThemeBuilder()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            print("Available Themes:\n")
            for theme in builder.list_themes():
                dark_indicator = '🌙' if theme['dark_mode'] else '☀️'
                print(f"{dark_indicator} {theme['display_name']}")
                print(f"   Name: {theme['name']}")
                print(f"   Description: {theme['description']}")
                print(f"   Author: {theme['author']}")
                print()

        elif command == 'apply' and len(sys.argv) > 2:
            theme_name = sys.argv[2]
            output = builder.apply_theme(theme_name)
            print(f"✓ Applied theme '{theme_name}'")
            print(f"  CSS written to: {output}")

        elif command == 'export' and len(sys.argv) > 2:
            theme_name = sys.argv[2]
            theme_config = builder.export_theme(theme_name)
            print(json.dumps(theme_config, indent=2))

        elif command == 'customize' and len(sys.argv) > 3:
            base_theme = sys.argv[2]
            new_theme = sys.argv[3]

            # Example customization
            customizations = {
                'display_name': new_theme.replace('-', ' ').title(),
                'colors': {
                    'primary': '#ff00ff',
                    'accent': '#00ffff'
                }
            }

            theme = builder.customize_theme(base_theme, new_theme, customizations)
            print(f"✓ Created custom theme '{new_theme}' based on '{base_theme}'")

        else:
            print("Unknown command")

    else:
        print("Theme Builder\n")
        print("Usage:")
        print("  python3 theme_builder.py list                           # List themes")
        print("  python3 theme_builder.py apply <theme-name>             # Apply theme")
        print("  python3 theme_builder.py export <theme-name>            # Export theme")
        print("  python3 theme_builder.py customize <base> <new-name>    # Customize theme")

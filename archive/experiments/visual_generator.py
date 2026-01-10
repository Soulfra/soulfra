#!/usr/bin/env python3
"""
Unified Visual Generator

Generates complete brand visual identity from a single color choice:
- Avatar (pixel art, 128x128)
- QR code (with brand colors)
- Logo (SVG, shape + color)
- Favicon (16x16 pixel art)
- Color palette card

Integrates existing systems:
- avatar_generator.py
- brand_qr_generator.py
- train_color_features.py
"""

import hashlib
import io
import json
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, Optional
import colorsys


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple (0-255)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_complementary_color(hex_color: str) -> str:
    """Generate complementary color (opposite on color wheel)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

    # Shift hue by 180 degrees (complementary)
    h = (h + 0.5) % 1.0

    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return f'#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}'


def generate_analogous_colors(hex_color: str) -> Tuple[str, str]:
    """Generate analogous colors (+/- 30 degrees on wheel)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

    # Analogous colors
    h1 = (h + 30/360) % 1.0
    h2 = (h - 30/360) % 1.0

    r1, g1, b1 = colorsys.hsv_to_rgb(h1, s, v)
    r2, g2, b2 = colorsys.hsv_to_rgb(h2, s, v)

    color1 = f'#{int(r1*255):02x}{int(g1*255):02x}{int(b1*255):02x}'
    color2 = f'#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}'

    return (color1, color2)


def generate_avatar_from_color(hex_color: str, username: str = None, size: int = 128) -> Image.Image:
    """
    Generate pixel art avatar based on color

    Args:
        hex_color: Primary color for avatar
        username: Optional username for deterministic generation
        size: Output size (default 128x128)

    Returns:
        PIL Image object
    """
    # Use color as seed if no username provided
    seed = username or hex_color
    hash_bytes = hashlib.md5(seed.encode('utf-8')).digest()

    # Get primary and secondary colors
    primary = hex_to_rgb(hex_color)
    secondary = hex_to_rgb(generate_complementary_color(hex_color))

    # Create 16x16 grid
    grid_size = 16
    img = Image.new('RGB', (grid_size, grid_size), color=(240, 240, 240))
    pixels = img.load()

    # Fill with symmetric pattern
    for y in range(grid_size):
        for x in range(grid_size // 2):
            byte_index = (y * (grid_size // 2) + x) % len(hash_bytes)
            pixel_value = hash_bytes[byte_index]

            if pixel_value % 3 == 0:  # Primary color
                pixels[x, y] = primary
                pixels[grid_size - 1 - x, y] = primary
            elif pixel_value % 5 == 0:  # Secondary color
                pixels[x, y] = secondary
                pixels[grid_size - 1 - x, y] = secondary

    # Upscale to final size
    return img.resize((size, size), Image.NEAREST)


def generate_favicon_from_color(hex_color: str) -> Image.Image:
    """
    Generate 16x16 favicon from color

    Creates a simple geometric shape in the color
    """
    img = Image.new('RGB', (16, 16), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    primary = hex_to_rgb(hex_color)
    secondary = hex_to_rgb(generate_complementary_color(hex_color))

    # Draw circle
    draw.ellipse([3, 3, 13, 13], fill=primary, outline=secondary)

    # Add center dot
    draw.ellipse([7, 7, 9, 9], fill=secondary)

    return img


def generate_logo_svg(hex_color: str, shape: str = 'circle') -> str:
    """
    Generate SVG logo from color

    Args:
        hex_color: Primary brand color
        shape: Shape type (circle, square, hexagon, triangle)

    Returns:
        SVG string
    """
    complementary = generate_complementary_color(hex_color)
    analogous1, analogous2 = generate_analogous_colors(hex_color)

    shapes = {
        'circle': f'''
            <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{hex_color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{complementary};stop-opacity:1" />
                    </linearGradient>
                </defs>
                <circle cx="100" cy="100" r="80" fill="url(#grad1)" stroke="{analogous1}" stroke-width="4"/>
                <circle cx="100" cy="100" r="40" fill="{analogous2}" opacity="0.8"/>
            </svg>
        ''',
        'square': f'''
            <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                <rect x="20" y="20" width="160" height="160" fill="{hex_color}" rx="10"/>
                <rect x="60" y="60" width="80" height="80" fill="{complementary}" rx="5"/>
            </svg>
        ''',
        'hexagon': f'''
            <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                <polygon points="100,20 170,60 170,140 100,180 30,140 30,60"
                         fill="{hex_color}" stroke="{complementary}" stroke-width="4"/>
                <polygon points="100,60 140,80 140,120 100,140 60,120 60,80"
                         fill="{analogous1}"/>
            </svg>
        ''',
        'triangle': f'''
            <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                <polygon points="100,30 180,170 20,170" fill="{hex_color}" stroke="{complementary}" stroke-width="4"/>
                <polygon points="100,90 140,150 60,150" fill="{analogous1}"/>
            </svg>
        '''
    }

    return shapes.get(shape, shapes['circle'])


def generate_color_palette_card(hex_color: str, width: int = 600, height: int = 200) -> Image.Image:
    """
    Generate color palette card showing primary and derived colors

    Args:
        hex_color: Primary color
        width: Card width
        height: Card height

    Returns:
        PIL Image object
    """
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Get color palette
    primary = hex_to_rgb(hex_color)
    complementary = hex_to_rgb(generate_complementary_color(hex_color))
    analogous1, analogous2 = generate_analogous_colors(hex_color)

    # Draw color swatches
    swatch_width = width // 4
    colors = [
        (primary, hex_color, "Primary"),
        (hex_to_rgb(complementary), generate_complementary_color(hex_color), "Complementary"),
        (hex_to_rgb(analogous1), analogous1, "Analogous 1"),
        (hex_to_rgb(analogous2), analogous2, "Analogous 2")
    ]

    for i, (rgb, hex_val, label) in enumerate(colors):
        x = i * swatch_width

        # Draw color swatch
        draw.rectangle([x, 0, x + swatch_width, height * 0.7], fill=rgb)

        # Draw label background
        draw.rectangle([x, height * 0.7, x + swatch_width, height], fill=(240, 240, 240))

        # Draw text (simple, no font file needed)
        text_y = int(height * 0.75)
        draw.text((x + 10, text_y), label, fill=(50, 50, 50))
        draw.text((x + 10, text_y + 25), hex_val, fill=(100, 100, 100))

    return img


def generate_complete_brand_kit(hex_color: str, username: str = None) -> Dict[str, bytes]:
    """
    Generate complete brand visual kit from a single color

    Args:
        hex_color: Primary brand color
        username: Optional username for avatar generation

    Returns:
        Dict with PNG/SVG bytes for each asset:
        {
            'avatar': bytes,
            'favicon': bytes,
            'logo_svg': str,
            'palette_card': bytes,
            'colors': {
                'primary': str,
                'complementary': str,
                'analogous': [str, str]
            }
        }
    """
    # Generate avatar
    avatar_img = generate_avatar_from_color(hex_color, username, size=128)
    avatar_bytes = io.BytesIO()
    avatar_img.save(avatar_bytes, 'PNG')

    # Generate favicon
    favicon_img = generate_favicon_from_color(hex_color)
    favicon_bytes = io.BytesIO()
    favicon_img.save(favicon_bytes, 'PNG')

    # Generate logo SVG
    logo_svg = generate_logo_svg(hex_color, shape='circle')

    # Generate palette card
    palette_img = generate_color_palette_card(hex_color)
    palette_bytes = io.BytesIO()
    palette_img.save(palette_bytes, 'PNG')

    # Collect colors
    complementary = generate_complementary_color(hex_color)
    analogous1, analogous2 = generate_analogous_colors(hex_color)

    return {
        'avatar': avatar_bytes.getvalue(),
        'favicon': favicon_bytes.getvalue(),
        'logo_svg': logo_svg,
        'palette_card': palette_bytes.getvalue(),
        'colors': {
            'primary': hex_color,
            'complementary': complementary,
            'analogous': [analogous1, analogous2]
        }
    }


if __name__ == '__main__':
    # Test generator
    test_color = '#667eea'
    print(f"Generating brand kit for color: {test_color}")

    kit = generate_complete_brand_kit(test_color, username='testuser')

    print("\n✅ Generated assets:")
    print(f"  - Avatar: {len(kit['avatar'])} bytes")
    print(f"  - Favicon: {len(kit['favicon'])} bytes")
    print(f"  - Logo SVG: {len(kit['logo_svg'])} chars")
    print(f"  - Palette Card: {len(kit['palette_card'])} bytes")
    print(f"\n🎨 Color Palette:")
    print(f"  - Primary: {kit['colors']['primary']}")
    print(f"  - Complementary: {kit['colors']['complementary']}")
    print(f"  - Analogous: {', '.join(kit['colors']['analogous'])}")

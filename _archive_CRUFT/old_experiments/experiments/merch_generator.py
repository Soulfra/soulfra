#!/usr/bin/env python3
"""
Merch Design Generator - Create Actual SVG/PNG Files

Generates print-ready merch designs using:
- Brand colors from database
- Slogans from slogan_generator.py
- Simple SVG templates (no external libraries needed)

Output: SVG files in output/merch/ directory
"""

import sqlite3
import os
from typing import Dict, Any, List
from slogan_generator import generate_all_slogans, get_all_brands


def get_db() -> sqlite3.Connection:
    """Get database connection with Row factory."""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def create_tshirt_svg(brand: Dict[str, Any], slogan: str, output_path: str):
    """
    Create a simple t-shirt design SVG.

    Design: Brand color background + slogan text + brand name

    Args:
        brand: Brand dict with colors
        slogan: Slogan text
        output_path: Where to save SVG file
    """
    primary = brand['color_primary']
    secondary = brand['color_secondary']
    brand_name = brand['name']

    # Simple text wrapping - split slogan into lines if too long
    words = slogan.split()
    lines = []
    current_line = []
    max_chars = 30

    for word in words:
        if sum(len(w) for w in current_line) + len(word) + len(current_line) <= max_chars:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    # Generate SVG
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="500" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="400" height="500" fill="{primary}"/>

  <!-- Brand name at top -->
  <text x="200" y="50" font-family="Arial, sans-serif" font-size="24"
        font-weight="bold" fill="white" text-anchor="middle">
    {brand_name}
  </text>

  <!-- Slogan (multi-line if needed) -->
'''

    # Add each line of slogan
    y_pos = 200
    for i, line in enumerate(lines):
        svg += f'''  <text x="200" y="{y_pos + (i * 40)}" font-family="Arial, sans-serif"
        font-size="18" fill="white" text-anchor="middle">{line}</text>\n'''

    # Add accent bar at bottom
    svg += f'''
  <!-- Accent bar -->
  <rect x="0" y="460" width="400" height="40" fill="{secondary}"/>
</svg>'''

    # Write to file
    with open(output_path, 'w') as f:
        f.write(svg)


def create_sticker_svg(brand: Dict[str, Any], keyword: str, output_path: str):
    """
    Create a simple sticker design SVG.

    Design: Circular logo with brand name + keyword

    Args:
        brand: Brand dict with colors
        keyword: Trending keyword
        output_path: Where to save SVG file
    """
    primary = brand['color_primary']
    accent = brand['color_accent']
    brand_name = brand['name']

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <!-- Circle background -->
  <circle cx="100" cy="100" r="95" fill="{primary}" stroke="{accent}" stroke-width="5"/>

  <!-- Brand name -->
  <text x="100" y="90" font-family="Arial, sans-serif" font-size="20"
        font-weight="bold" fill="white" text-anchor="middle">
    {brand_name}
  </text>

  <!-- Keyword -->
  <text x="100" y="120" font-family="Arial, sans-serif" font-size="16"
        fill="white" text-anchor="middle">
    {keyword.title()}
  </text>
</svg>'''

    with open(output_path, 'w') as f:
        f.write(svg)


def create_poster_svg(brand: Dict[str, Any], slogan: str, output_path: str):
    """
    Create a simple poster design SVG.

    Design: Large text poster with brand colors

    Args:
        brand: Brand dict with colors
        slogan: Slogan text
        output_path: Where to save SVG file
    """
    primary = brand['color_primary']
    secondary = brand['color_secondary']
    accent = brand['color_accent']
    brand_name = brand['name']

    # Split slogan for poster
    words = slogan.split()
    lines = []
    current_line = []

    for word in words:
        if len(' '.join(current_line + [word])) <= 25:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="600" height="800" xmlns="http://www.w3.org/2000/svg">
  <!-- Background gradient -->
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{primary};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{secondary};stop-opacity:1" />
    </linearGradient>
  </defs>

  <rect width="600" height="800" fill="url(#bg)"/>

  <!-- Accent stripe -->
  <rect x="0" y="350" width="600" height="100" fill="{accent}" opacity="0.3"/>

  <!-- Brand name header -->
  <text x="300" y="100" font-family="Arial, sans-serif" font-size="36"
        font-weight="bold" fill="white" text-anchor="middle">
    {brand_name}
  </text>

  <!-- Slogan (large, multi-line) -->
'''

    y_pos = 300
    for i, line in enumerate(lines):
        font_size = 32 if len(line) < 20 else 24
        svg += f'''  <text x="300" y="{y_pos + (i * 60)}" font-family="Arial, sans-serif"
        font-size="{font_size}" font-weight="bold" fill="white" text-anchor="middle">{line}</text>\n'''

    svg += '</svg>'

    with open(output_path, 'w') as f:
        f.write(svg)


def generate_merch_for_brand(brand: Dict[str, Any], slogans: List[str], output_dir: str):
    """
    Generate all merch types for a brand.

    Creates:
    - T-shirt designs (first 3 slogans)
    - Sticker designs (brand name + trending keywords)
    - Poster designs (best slogan)

    Args:
        brand: Brand dict
        slogans: List of slogans for this brand
        output_dir: Directory to save files
    """
    brand_name = brand['name']
    brand_slug = brand['slug']

    # Create brand directory
    brand_dir = os.path.join(output_dir, brand_slug)
    os.makedirs(brand_dir, exist_ok=True)

    files_created = []

    # Generate t-shirts (top 3 slogans)
    for i, slogan in enumerate(slogans[:3], 1):
        filename = f"tshirt_{brand_slug}_{i}.svg"
        filepath = os.path.join(brand_dir, filename)
        create_tshirt_svg(brand, slogan, filepath)
        files_created.append(filepath)

    # Generate stickers (simple brand name designs)
    keywords = ['OSS', 'Privacy', 'AI', 'Tech']  # Generic keywords for stickers
    for i, keyword in enumerate(keywords[:2], 1):
        filename = f"sticker_{brand_slug}_{i}.svg"
        filepath = os.path.join(brand_dir, filename)
        create_sticker_svg(brand, keyword, filepath)
        files_created.append(filepath)

    # Generate poster (best slogan)
    if slogans:
        filename = f"poster_{brand_slug}.svg"
        filepath = os.path.join(brand_dir, filename)
        create_poster_svg(brand, slogans[0], filepath)
        files_created.append(filepath)

    return files_created


def generate_all_merch(output_dir: str = 'output/merch'):
    """
    Generate merch designs for all brands.

    Creates SVG files organized by brand in output/merch/ directory.

    Args:
        output_dir: Base directory for output files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get brands and slogans
    brands = get_all_brands()
    all_slogans = generate_all_slogans()

    total_files = 0

    print("🎨 Merch Design Generator\n")
    print(f"Output directory: {output_dir}\n")

    for brand in brands:
        brand_name = brand['name']
        slogans = all_slogans.get(brand_name, [])

        if not slogans:
            print(f"⏭️  {brand_name}: No slogans (skipping)")
            continue

        print(f"🎨 {brand_name}:")
        files = generate_merch_for_brand(brand, slogans, output_dir)
        print(f"   Created {len(files)} files")
        total_files += len(files)

        # Show first file path
        if files:
            print(f"   Example: {files[0]}")

        print()

    print(f"✅ Generated {total_files} merch design files across {len(brands)} brands")
    print(f"📁 Files saved to: {output_dir}/")

    return total_files


def preview_designs():
    """Print preview of what will be generated."""
    brands = get_all_brands()
    all_slogans = generate_all_slogans()

    print("🔍 Merch Design Preview\n")

    for brand in brands[:5]:  # Preview first 5 brands
        brand_name = brand['name']
        slogans = all_slogans.get(brand_name, [])

        if not slogans:
            continue

        print(f"{brand_name} ({brand['color_primary']}):")
        print(f"  T-Shirt 1: \"{slogans[0][:50]}...\"")
        if len(slogans) > 1:
            print(f"  T-Shirt 2: \"{slogans[1][:50]}...\"")
        print(f"  Sticker: Circle logo with brand name")
        print(f"  Poster: Large text poster")
        print()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        # Just preview what would be generated
        preview_designs()
    else:
        # Actually generate the files
        generate_all_merch()

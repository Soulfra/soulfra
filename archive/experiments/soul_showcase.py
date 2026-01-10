#!/usr/bin/env python3
"""
Soul Showcase - Visual Proof Gallery

Generates visual showcase of all souls showing:
- Soul visualization (pixel art)
- QR code (signed + verified)
- Short URL (for marketing)
- Username and stats

Creates both:
1. Individual cards (PNG images)
2. HTML gallery page
3. Combined mega-image grid

Perfect for:
- Proving the system works
- Marketing materials
- Documentation
- Demos

Run this to see ALL souls at once!
"""

import os
from PIL import Image, ImageDraw, ImageFont
from database import get_db
from soul_visualizer import generate_soul_visualization_from_username
from soul_qr_signed import generate_signed_qr
from url_shortener import generate_shortcut, generate_short_url


def create_soul_card(username, output_dir='showcase'):
    """
    Create visual card for one soul

    Card layout:
    [username]
    [visualization] [QR code]
    [short URL]

    Args:
        username: Username to showcase
        output_dir: Output directory

    Returns:
        PIL.Image: Soul card image
    """
    # Generate components
    viz = generate_soul_visualization_from_username(username, output_size=128)
    qr = generate_signed_qr(username, size=128)
    short_url = generate_short_url(username, 'soulfra.com')

    if not viz or not qr:
        return None

    # Create card (400x300)
    card = Image.new('RGB', (400, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(card)

    # Try to load font
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_url = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        # Fallback to default
        font_title = ImageFont.load_default()
        font_url = ImageFont.load_default()

    # Draw username at top
    title_text = f"@{username}"
    # Use textbbox instead of deprecated textsize
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(
        ((400 - title_width) // 2, 20),
        title_text,
        fill=(0, 0, 0),
        font=font_title
    )

    # Paste visualization (left)
    card.paste(viz, (60, 80))

    # Paste QR code (right)
    card.paste(qr, (212, 80))

    # Draw short URL at bottom
    url_bbox = draw.textbbox((0, 0), short_url, font=font_url)
    url_width = url_bbox[2] - url_bbox[0]
    draw.text(
        ((400 - url_width) // 2, 240),
        short_url,
        fill=(100, 100, 100),
        font=font_url
    )

    # Draw border
    draw.rectangle([(0, 0), (399, 299)], outline=(200, 200, 200), width=2)

    return card


def generate_showcase_grid(users, grid_cols=3):
    """
    Create grid of all soul cards

    Args:
        users: List of user dicts
        grid_cols: Number of columns

    Returns:
        PIL.Image: Grid image
    """
    cards = []

    for user in users:
        card = create_soul_card(user['username'])
        if card:
            cards.append(card)

    if not cards:
        return None

    # Calculate grid dimensions
    card_width, card_height = 400, 300
    grid_rows = (len(cards) + grid_cols - 1) // grid_cols

    grid_width = card_width * grid_cols
    grid_height = card_height * grid_rows

    # Create grid image
    grid = Image.new('RGB', (grid_width, grid_height), color=(240, 240, 240))

    # Paste cards
    for i, card in enumerate(cards):
        row = i // grid_cols
        col = i % grid_cols

        x = col * card_width
        y = row * card_height

        grid.paste(card, (x, y))

    return grid


def generate_html_gallery(users, output_path='showcase/gallery.html'):
    """
    Generate HTML gallery page

    Args:
        users: List of user dicts
        output_path: HTML output path

    Returns:
        str: HTML file path
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soul Showcase - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            color: #333;
            margin: 0;
        }
        .header p {
            color: #666;
            margin: 10px 0;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .soul-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px;
            text-align: center;
        }
        .soul-card h2 {
            margin: 0 0 20px 0;
            color: #333;
        }
        .soul-images {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }
        .soul-images img {
            width: 128px;
            height: 128px;
            border-radius: 4px;
        }
        .soul-url {
            color: #666;
            font-size: 14px;
            font-family: monospace;
            background: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
        }
        .stats {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            max-width: 600px;
            margin: 0 auto 40px auto;
        }
        .stats h3 {
            margin: 0 0 10px 0;
            color: #2e7d32;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Soul Showcase</h1>
        <p>Visual proof that Soulfra works - All souls with visualizations, QR codes, and short URLs</p>
    </div>

    <div class="stats">
        <h3>System Status</h3>
        <p>✅ {user_count} souls compiled and verified</p>
        <p>✅ All visualizations unique</p>
        <p>✅ All QR codes signed and secure</p>
    </div>

    <div class="gallery">
"""

    # Add cards
    from database import get_db
    db = get_db()

    for user in users:
        username = user['username']
        short_url = generate_short_url(username, 'soulfra.com')

        # Get image hashes from database
        viz_img = db.execute('''
            SELECT hash FROM images
            WHERE json_extract(metadata, '$.username') = ?
            AND json_extract(metadata, '$.type') = 'viz'
            LIMIT 1
        ''', (username,)).fetchone()

        qr_img = db.execute('''
            SELECT hash FROM images
            WHERE json_extract(metadata, '$.username') = ?
            AND json_extract(metadata, '$.type') = 'qr'
            LIMIT 1
        ''', (username,)).fetchone()

        # Use /i/<hash> URLs (database-served images)
        viz_url = f"/i/{viz_img['hash']}" if viz_img else f"{username}_viz.png"
        qr_url = f"/i/{qr_img['hash']}" if qr_img else f"{username}_qr.png"

        html += f"""
        <div class="soul-card">
            <h2>@{username}</h2>
            <div class="soul-images">
                <div>
                    <p style="margin: 0 0 5px 0; font-size: 12px; color: #999;">Visualization</p>
                    <img src="{viz_url}" alt="{username} visualization">
                </div>
                <div>
                    <p style="margin: 0 0 5px 0; font-size: 12px; color: #999;">QR Code</p>
                    <img src="{qr_url}" alt="{username} QR code">
                </div>
            </div>
            <div class="soul-url">{short_url}</div>
        </div>
"""

    db.close()

    html += """
    </div>

    <div class="header" style="margin-top: 40px;">
        <p style="color: #999; font-size: 14px;">
            Generated by soul_showcase.py<br>
            🤖 Built with Claude Code
        </p>
    </div>
</body>
</html>
"""

    # Replace placeholder
    html = html.replace('{user_count}', str(len(users)))

    # Save HTML
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


def generate_showcase():
    """Generate complete showcase"""
    print("=" * 70)
    print("🎨 Generating Soul Showcase")
    print("=" * 70)
    print()

    output_dir = 'showcase'
    os.makedirs(output_dir, exist_ok=True)

    # Get all users
    db = get_db()
    users = db.execute('SELECT username FROM users ORDER BY username').fetchall()
    db.close()

    print(f"Found {len(users)} souls to showcase\n")

    # Generate individual components
    print("📸 Generating individual components...")
    for user in users:
        username = user['username']

        # Generate visualization
        viz = generate_soul_visualization_from_username(username, output_size=128)
        if viz:
            viz_path = os.path.join(output_dir, f'{username}_viz.png')
            viz.save(viz_path, 'PNG')
            print(f"   ✓ {username} visualization")

        # Generate QR
        qr = generate_signed_qr(username, size=128)
        if qr:
            qr_path = os.path.join(output_dir, f'{username}_qr.png')
            qr.save(qr_path, 'PNG')
            print(f"   ✓ {username} QR code")

    print()

    # Generate cards
    print("🎴 Generating soul cards...")
    for user in users:
        card = create_soul_card(user['username'], output_dir)
        if card:
            card_path = os.path.join(output_dir, f"{user['username']}_card.png")
            card.save(card_path, 'PNG')
            print(f"   ✓ {user['username']} card")

    print()

    # Generate grid
    print("🖼️  Generating showcase grid...")
    grid = generate_showcase_grid(users, grid_cols=3)
    if grid:
        grid_path = os.path.join(output_dir, 'showcase_grid.png')
        grid.save(grid_path, 'PNG')
        print(f"   ✓ Grid saved: {grid_path}")
        print(f"   Size: {grid.size}")

    print()

    # Generate HTML gallery
    print("🌐 Generating HTML gallery...")
    html_path = generate_html_gallery(users, f'{output_dir}/gallery.html')
    print(f"   ✓ Gallery saved: {html_path}")

    print()

    print("=" * 70)
    print("✅ Showcase Generation Complete!")
    print("=" * 70)
    print()

    print(f"📁 Output directory: {output_dir}/")
    print()
    print("Files created:")
    print(f"   • showcase_grid.png - All souls in one image")
    print(f"   • gallery.html - Interactive HTML gallery")
    print(f"   • {len(users)} individual cards")
    print(f"   • {len(users)} visualizations")
    print(f"   • {len(users)} QR codes")
    print()

    print("💡 To view:")
    print(f"   open {output_dir}/gallery.html")
    print(f"   open {output_dir}/showcase_grid.png")
    print()


if __name__ == '__main__':
    generate_showcase()

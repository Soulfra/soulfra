#!/usr/bin/env python3
"""
Pixel Art Avatar Generator for Soulfra

Generates deterministic, symmetric 16x16 pixel art avatars based on username.
No external dependencies except Pillow for PNG generation.

Created by: Alice Developer
Contribution: 100 Perfect Bits
"""

import hashlib
import os
from PIL import Image


def generate_pixel_avatar(username, size=16, output_size=128):
    """
    Generate a deterministic pixel art avatar

    Args:
        username: String to generate avatar from
        size: Grid size (16x16 by default)
        output_size: Final PNG size (upscaled from grid, default 128x128)

    Returns:
        PIL Image object
    """
    # Create deterministic seed from username
    hash_bytes = hashlib.md5(username.encode('utf-8')).digest()

    # Extract colors from hash
    r = hash_bytes[0]
    g = hash_bytes[1]
    b = hash_bytes[2]

    # Secondary color (inverted)
    r2 = 255 - r
    g2 = 255 - g
    b2 = 255 - b

    # Create small grid image
    img = Image.new('RGB', (size, size), color=(240, 240, 240))  # Light gray background
    pixels = img.load()

    # Fill left half deterministically, mirror to right half for symmetry
    for y in range(size):
        for x in range(size // 2):
            # Use hash bytes to determine if pixel should be filled
            byte_index = (y * (size // 2) + x) % len(hash_bytes)
            pixel_value = hash_bytes[byte_index]

            # Create pattern with some logic
            if pixel_value % 3 == 0:  # ~33% fill rate with primary color
                pixels[x, y] = (r, g, b)
                pixels[size - 1 - x, y] = (r, g, b)  # Mirror to right
            elif pixel_value % 5 == 0:  # ~20% fill rate with secondary color
                pixels[x, y] = (r2, g2, b2)
                pixels[size - 1 - x, y] = (r2, g2, b2)  # Mirror to right

    # Upscale to desired output size (with nearest neighbor for pixel art look)
    img_large = img.resize((output_size, output_size), Image.NEAREST)

    return img_large


def save_avatar(username, output_dir='static/avatars/generated'):
    """
    Generate and save avatar for a username

    Args:
        username: Username to generate avatar for
        output_dir: Directory to save PNG files

    Returns:
        Path to saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate avatar
    avatar = generate_pixel_avatar(username)

    # Save as PNG
    output_path = os.path.join(output_dir, f'{username}.png')
    avatar.save(output_path, 'PNG')

    return output_path


def get_avatar_path(username, output_dir='static/avatars/generated'):
    """
    Get path to avatar file, generate if it doesn't exist

    Args:
        username: Username
        output_dir: Directory where avatars are stored

    Returns:
        Relative path to avatar file (for use in URLs)
    """
    avatar_file = f'{username}.png'
    full_path = os.path.join(output_dir, avatar_file)

    # Generate if doesn't exist
    if not os.path.exists(full_path):
        save_avatar(username, output_dir)

    # Return web-accessible path
    return f'/{output_dir}/{avatar_file}'


def get_avatar_url(username):
    """
    Get database URL for avatar (database-first approach)

    Args:
        username: Username

    Returns:
        URL to avatar image from database (/i/<hash>)
    """
    from database import get_db
    import hashlib

    db = get_db()

    # Try to get from database first
    avatar = db.execute('''
        SELECT hash FROM images
        WHERE json_extract(metadata, '$.username') = ?
        AND json_extract(metadata, '$.type') = 'avatar'
        LIMIT 1
    ''', (username,)).fetchone()

    if avatar:
        db.close()
        return f"/i/{avatar['hash']}"

    # If not in database, generate and store it
    avatar_img = generate_pixel_avatar(username)

    # Convert to bytes
    import io
    img_bytes = io.BytesIO()
    avatar_img.save(img_bytes, 'PNG')
    image_data = img_bytes.getvalue()

    # Calculate hash
    image_hash = hashlib.sha256(image_data).hexdigest()

    # Store in database
    import json
    metadata = json.dumps({
        'filename': f'{username}.png',
        'type': 'avatar',
        'username': username,
        'source': 'avatar_generator'
    })

    try:
        db.execute('''
            INSERT INTO images (hash, data, mime_type, width, height, metadata)
            VALUES (?, ?, 'image/png', 128, 128, ?)
        ''', (image_hash, image_data, metadata))
        db.commit()
    except:
        pass  # Already exists

    db.close()

    return f"/i/{image_hash}"


def main():
    """Test the generator with Soulfra users"""
    test_users = ['calriven', 'soulfra', 'deathtodata', 'alice', 'admin']

    print("🎨 Generating pixel art avatars...")
    print()

    for username in test_users:
        path = save_avatar(username)
        file_size = os.path.getsize(path)
        print(f"✅ {username:15} → {path:50} ({file_size:,} bytes)")

    print()
    print(f"✅ Generated {len(test_users)} avatars")
    print("📁 View them in: static/avatars/generated/")


if __name__ == '__main__':
    main()

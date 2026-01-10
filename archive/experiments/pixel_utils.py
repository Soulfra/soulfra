#!/usr/bin/env python3
"""
Pixel Art Utilities for Soulfra

Shared utilities for generating deterministic pixel art from hash data.
Used by both avatar_generator and soul_visualizer.

Teaching the pattern:
1. Data (username, keywords) → Hash (MD5, SHA256)
2. Hash → Colors (extract RGB from bytes)
3. Hash → Pattern (which pixels to fill)
4. Pattern → Image (PIL pixel manipulation)

No external deps except Pillow (already installed).
"""

import hashlib
from PIL import Image


def string_to_hash(text):
    """
    Convert string to hash bytes

    Args:
        text: String to hash

    Returns:
        bytes: MD5 hash (16 bytes)

    Learning: This is how we make deterministic colors from text
    """
    return hashlib.md5(text.encode('utf-8')).digest()


def hash_to_colors(hash_bytes):
    """
    Extract primary and secondary colors from hash

    Args:
        hash_bytes: Hash digest bytes

    Returns:
        tuple: ((r, g, b), (r2, g2, b2)) - primary and secondary colors

    Learning: First 3 bytes = RGB, invert for secondary color
    """
    # Extract RGB from first 3 bytes
    r = hash_bytes[0]
    g = hash_bytes[1]
    b = hash_bytes[2]

    # Secondary color (inverted for contrast)
    r2 = 255 - r
    g2 = 255 - g
    b2 = 255 - b

    return ((r, g, b), (r2, g2, b2))


def generate_symmetric_pattern(hash_bytes, size=16):
    """
    Generate symmetric pixel pattern from hash

    Args:
        hash_bytes: Hash digest bytes
        size: Grid size (default 16x16)

    Returns:
        PIL.Image: Small pixel grid (size x size)

    Learning:
    - Mirror left half to right (symmetry)
    - Use hash bytes to determine which pixels to fill
    - Modulo operator for fill patterns (% 3, % 5)
    """
    primary, secondary = hash_to_colors(hash_bytes)

    # Create grid with light gray background
    img = Image.new('RGB', (size, size), color=(240, 240, 240))
    pixels = img.load()

    # Fill left half, mirror to right for symmetry
    for y in range(size):
        for x in range(size // 2):
            # Use hash bytes to determine pixel fill
            byte_index = (y * (size // 2) + x) % len(hash_bytes)
            pixel_value = hash_bytes[byte_index]

            # Pattern logic: % 3 = 33% fill, % 5 = 20% fill
            if pixel_value % 3 == 0:
                pixels[x, y] = primary
                pixels[size - 1 - x, y] = primary  # Mirror
            elif pixel_value % 5 == 0:
                pixels[x, y] = secondary
                pixels[size - 1 - x, y] = secondary  # Mirror

    return img


def generate_pattern_from_keywords(keywords, size=16):
    """
    Generate pixel pattern from list of keywords

    Args:
        keywords: List of strings (interests, values, etc.)
        size: Grid size

    Returns:
        PIL.Image: Small pixel grid

    Learning: Combine multiple keywords into single hash
    """
    # Join keywords with separator
    combined = '|'.join(sorted(keywords))  # Sort for determinism
    hash_bytes = string_to_hash(combined)

    return generate_symmetric_pattern(hash_bytes, size)


def upscale_pixel_art(img, output_size=128):
    """
    Upscale pixel art with nearest neighbor (no blur)

    Args:
        img: Small PIL Image
        output_size: Target size (width and height)

    Returns:
        PIL.Image: Upscaled image

    Learning: NEAREST filter preserves pixel art aesthetic
    """
    return img.resize((output_size, output_size), Image.NEAREST)


def save_pixel_art(img, filepath):
    """
    Save pixel art as PNG

    Args:
        img: PIL Image
        filepath: Output path

    Returns:
        str: Saved filepath

    Learning: PNG is lossless, perfect for pixel art
    """
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath, 'PNG')
    return filepath


def test_pixel_utils():
    """Test the pixel utilities"""
    print("🧪 Testing Pixel Utilities\n")

    # Test 1: String to hash
    hash1 = string_to_hash("alice")
    hash2 = string_to_hash("alice")
    hash3 = string_to_hash("bob")

    print("1. Hash Determinism:")
    print(f"   alice hash 1: {hash1[:4].hex()}...")
    print(f"   alice hash 2: {hash2[:4].hex()}... (same? {hash1 == hash2})")
    print(f"   bob hash:     {hash3[:4].hex()}... (different? {hash1 != hash3})")
    print()

    # Test 2: Hash to colors
    colors = hash_to_colors(hash1)
    print("2. Hash to Colors:")
    print(f"   Primary:   RGB{colors[0]}")
    print(f"   Secondary: RGB{colors[1]}")
    print()

    # Test 3: Generate pattern
    img = generate_symmetric_pattern(hash1)
    print("3. Generate Pattern:")
    print(f"   Created {img.size[0]}x{img.size[1]} pixel grid")
    print()

    # Test 4: Keyword pattern
    keywords = ['python', 'testing', 'pixels']
    img2 = generate_pattern_from_keywords(keywords)
    print("4. Pattern from Keywords:")
    print(f"   Keywords: {keywords}")
    print(f"   Created {img2.size[0]}x{img2.size[1]} pixel grid")
    print()

    # Test 5: Upscale
    img_large = upscale_pixel_art(img, 128)
    print("5. Upscale:")
    print(f"   {img.size} → {img_large.size}")
    print()

    print("✅ All pixel utility tests passed!")


if __name__ == '__main__':
    test_pixel_utils()

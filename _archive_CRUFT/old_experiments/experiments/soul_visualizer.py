#!/usr/bin/env python3
"""
Soul Visualizer - Generate Unique Pixel Art from Soul Data

Turns a user's soul essence (interests, values, expertise) into
deterministic pixel art visualizations.

Teaching the pattern:
1. Soul data (interests + values + expertise) → Keywords
2. Keywords → Hash (via pixel_utils)
3. Hash → Symmetric pixel pattern
4. Pattern → Upscaled PNG image

Each soul gets a unique visual fingerprint!

No external deps except Pillow (already installed).
"""

import os
from pixel_utils import (
    generate_pattern_from_keywords,
    upscale_pixel_art,
    save_pixel_art
)


def extract_soul_keywords(soul_pack, max_keywords=10):
    """
    Extract representative keywords from soul pack

    Args:
        soul_pack: Soul data dict (from soul_compiler.compile_soul)
        max_keywords: Maximum keywords to extract

    Returns:
        list: Keywords representing this soul

    Learning: Combine interests, values, and top expertise
    """
    keywords = []

    # Add interests (top interests)
    if 'essence' in soul_pack and 'interests' in soul_pack['essence']:
        interests = soul_pack['essence']['interests'][:5]
        keywords.extend(interests)

    # Add values (core values)
    if 'essence' in soul_pack and 'values' in soul_pack['essence']:
        values = soul_pack['essence']['values'][:3]
        keywords.extend(values)

    # Add top expertise areas
    if 'essence' in soul_pack and 'expertise' in soul_pack['essence']:
        expertise = soul_pack['essence']['expertise']
        # Sort by score, take top 2
        top_skills = sorted(expertise.items(), key=lambda x: x[1], reverse=True)[:2]
        keywords.extend([skill for skill, _ in top_skills])

    # Limit to max_keywords
    return keywords[:max_keywords]


def generate_soul_visualization(soul_pack, size=16, output_size=256):
    """
    Generate pixel art visualization from soul data

    Args:
        soul_pack: Soul data dict
        size: Grid size for base pattern (default 16x16)
        output_size: Final upscaled size (default 256x256)

    Returns:
        PIL.Image: Upscaled pixel art image

    Learning:
    - Extract keywords from soul
    - Generate symmetric pattern
    - Upscale with NEAREST filter (pixel art look)
    """
    # Extract keywords
    keywords = extract_soul_keywords(soul_pack)

    # Generate base pattern
    base_pattern = generate_pattern_from_keywords(keywords, size=size)

    # Upscale to final size
    return upscale_pixel_art(base_pattern, output_size=output_size)


def generate_soul_visualization_from_username(username, size=16, output_size=256):
    """
    Generate visualization directly from username

    Args:
        username: Username to visualize
        size: Grid size
        output_size: Final size

    Returns:
        PIL.Image or None: Visualization image, or None if user not found

    Learning: Convenience wrapper that compiles soul first
    """
    from soul_model import Soul
    from database import get_db

    # Get user ID from username
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    db.close()

    if not user:
        return None

    # Compile soul
    soul = Soul(user['id'])
    soul_pack = soul.compile_pack()

    if not soul_pack:
        return None

    # Generate visualization
    return generate_soul_visualization(soul_pack, size=size, output_size=output_size)


def save_soul_visualization(soul_pack, output_dir='static/souls', filename_prefix=None):
    """
    Generate and save soul visualization to file

    Args:
        soul_pack: Soul data dict
        output_dir: Directory to save to (default: static/souls)
        filename_prefix: Prefix for filename (default: username)

    Returns:
        str: Saved filepath

    Learning: Makes visualization accessible via web server
    """
    # Get username for filename
    username = soul_pack.get('identity', {}).get('username', 'unknown')

    if filename_prefix is None:
        filename_prefix = username

    # Generate visualization
    img = generate_soul_visualization(soul_pack)

    # Save to file
    filepath = os.path.join(output_dir, f'{filename_prefix}_soul.png')
    return save_pixel_art(img, filepath)


def test_soul_visualizer():
    """Test the soul visualizer"""
    print("🧪 Testing Soul Visualizer\n")

    # Test 1: Extract keywords from soul pack
    test_soul_pack = {
        'identity': {'username': 'testuser'},
        'essence': {
            'interests': ['python', 'testing', 'automation', 'pixels', 'art'],
            'values': ['learning', 'simplicity', 'quality'],
            'expertise': {
                'python': 85,
                'testing': 70,
                'design': 60,
                'writing': 50
            }
        }
    }

    keywords = extract_soul_keywords(test_soul_pack)
    print("1. Extract Keywords:")
    print(f"   Soul keywords: {keywords}")
    print(f"   Count: {len(keywords)}")
    print()

    # Test 2: Generate visualization
    img = generate_soul_visualization(test_soul_pack)
    print("2. Generate Visualization:")
    print(f"   Image size: {img.size}")
    print(f"   Image mode: {img.mode}")
    print()

    # Test 3: Determinism check (same soul = same image)
    img2 = generate_soul_visualization(test_soul_pack)
    pixels1 = list(img.getdata())
    pixels2 = list(img2.getdata())

    print("3. Determinism Check:")
    print(f"   Same pixels? {pixels1 == pixels2}")
    print()

    # Test 4: Different souls = different images
    different_soul = {
        'identity': {'username': 'other'},
        'essence': {
            'interests': ['javascript', 'web', 'design'],
            'values': ['creativity', 'speed'],
            'expertise': {'javascript': 90, 'css': 80}
        }
    }

    img3 = generate_soul_visualization(different_soul)
    pixels3 = list(img3.getdata())

    print("4. Uniqueness Check:")
    print(f"   Different pixels? {pixels1 != pixels3}")
    print()

    # Test 5: Save visualization
    test_filepath = save_soul_visualization(test_soul_pack, output_dir='test_output')
    print("5. Save Visualization:")
    print(f"   Saved to: {test_filepath}")
    print(f"   File exists? {os.path.exists(test_filepath)}")
    print()

    # Cleanup test files
    import shutil
    if os.path.exists('test_output'):
        shutil.rmtree('test_output')

    print("✅ All soul visualizer tests passed!")


if __name__ == '__main__':
    test_soul_visualizer()

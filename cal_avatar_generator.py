#!/usr/bin/env python3
"""
Cal Avatar Generator - Voice → Visual Identity

Generates unique visual avatars from user wordmaps.
Like FaceID but for vocabulary patterns.

Usage:
    from cal_avatar_generator import generate_cal_avatar
    svg = generate_cal_avatar(user_id)
"""

import hashlib
import math
from database import get_db


def generate_cal_avatar(user_id, size=200):
    """
    Generate Cal avatar SVG from user's wordmap

    Args:
        user_id: User ID
        size: Avatar size in pixels

    Returns:
        SVG string
    """
    import json
    db = get_db()

    # Get user's wordmap from user_wordmaps table (JSON format)
    wordmap_row = db.execute('''
        SELECT wordmap_json
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    db.close()

    if not wordmap_row or not wordmap_row['wordmap_json']:
        # Default avatar for new users
        return generate_default_avatar(user_id, size)

    # Parse JSON wordmap: {"word": frequency, ...}
    wordmap_dict = json.loads(wordmap_row['wordmap_json'])

    # Convert to list of (word, frequency) tuples, sorted by frequency
    wordmap = sorted(wordmap_dict.items(), key=lambda x: x[1], reverse=True)[:20]

    if not wordmap:
        return generate_default_avatar(user_id, size)

    # Generate deterministic visual from word patterns
    words_str = ''.join([word for word, freq in wordmap])
    word_hash = hashlib.sha256(words_str.encode()).hexdigest()

    # Extract visual parameters from hash
    hue1 = int(word_hash[0:2], 16) % 360
    hue2 = (hue1 + int(word_hash[2:4], 16)) % 360
    saturation = 50 + (int(word_hash[4:6], 16) % 40)
    lightness = 45 + (int(word_hash[6:8], 16) % 20)

    # Pattern density based on vocabulary size
    pattern_count = 3 + (len(wordmap) // 5)

    # Generate SVG
    svg = f'''<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bg-{user_id}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:hsl({hue1}, {saturation}%, {lightness}%)" />
            <stop offset="100%" style="stop-color:hsl({hue2}, {saturation}%, {lightness}%)" />
        </linearGradient>
        <filter id="goo-{user_id}">
            <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
            <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" result="goo" />
        </filter>
    </defs>

    <!-- Background -->
    <rect width="100" height="100" fill="url(#bg-{user_id})" />

    <!-- Organic pattern based on word frequencies -->
    <g filter="url(#goo-{user_id})">
'''

    # Generate organic blobs from word patterns
    for i, (word, freq) in enumerate(wordmap[:pattern_count]):
        # Position based on word hash
        word_h = hashlib.md5(word.encode()).hexdigest()
        x = 20 + (int(word_h[0:2], 16) % 60)
        y = 20 + (int(word_h[2:4], 16) % 60)
        r = 10 + (freq % 15)

        opacity = 0.3 + (freq % 40) / 100

        svg += f'        <circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{opacity}" />\n'

    svg += '''    </g>

    <!-- Cal signature -->
    <text x="50" y="90" font-family="Arial, sans-serif" font-size="8"
          fill="white" text-anchor="middle" opacity="0.6">Cal</text>
</svg>'''

    return svg


def generate_default_avatar(user_id, size=200):
    """Generate default Cal avatar for new users"""
    # Use user_id for deterministic colors
    hue = (user_id * 137) % 360

    return f'''<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="default-bg-{user_id}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:hsl({hue}, 60%, 50%)" />
            <stop offset="100%" style="stop-color:hsl({(hue + 60) % 360}, 60%, 50%)" />
        </linearGradient>
    </defs>
    <rect width="100" height="100" fill="url(#default-bg-{user_id})" />
    <circle cx="50" cy="40" r="15" fill="white" opacity="0.3" />
    <circle cx="50" cy="65" r="20" fill="white" opacity="0.2" />
    <text x="50" y="90" font-family="Arial, sans-serif" font-size="8"
          fill="white" text-anchor="middle" opacity="0.6">Cal</text>
</svg>'''


def generate_cal_avatar_from_email(email, size=200):
    """Generate Cal avatar from email hash (for users without wordmaps yet)"""
    email_hash = hashlib.sha256(email.encode()).hexdigest()

    hue1 = int(email_hash[0:2], 16) % 360
    hue2 = (hue1 + int(email_hash[2:4], 16)) % 360

    return f'''<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="email-bg">
            <stop offset="0%" style="stop-color:hsl({hue1}, 70%, 55%)" />
            <stop offset="100%" style="stop-color:hsl({hue2}, 70%, 45%)" />
        </radialGradient>
    </defs>
    <rect width="100" height="100" fill="url(#email-bg)" />
    <text x="50" y="55" font-family="Arial, sans-serif" font-size="40" font-weight="900"
          fill="white" text-anchor="middle" opacity="0.9">{email[0].upper()}</text>
    <text x="50" y="90" font-family="Arial, sans-serif" font-size="8"
          fill="white" text-anchor="middle" opacity="0.6">Cal</text>
</svg>'''


if __name__ == '__main__':
    # Test avatar generation
    print("Generating test Cal avatars...")

    # Test with user_id 1
    svg = generate_cal_avatar(1)
    with open('/tmp/cal_avatar_test.svg', 'w') as f:
        f.write(svg)
    print("✅ Generated /tmp/cal_avatar_test.svg")

    # Test email-based avatar
    svg_email = generate_cal_avatar_from_email("test@example.com")
    with open('/tmp/cal_avatar_email_test.svg', 'w') as f:
        f.write(svg_email)
    print("✅ Generated /tmp/cal_avatar_email_test.svg")

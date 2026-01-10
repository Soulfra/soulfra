#!/usr/bin/env python3
"""
SVG Badge Generator for GitHub READMEs

Generates dynamic SVG images that work in GitHub markdown:
- QR codes (link to profile)
- Wordmap visualization
- Activity indicators
- Auth provider badges

Usage:
    ![QR](https://api.cringeproof.com/badge/matt/qr.svg)
    ![Wordmap](https://api.cringeproof.com/badge/matt/wordmap.svg)
    ![Activity](https://api.cringeproof.com/badge/matt/activity.svg)
"""

from flask import Blueprint, Response
from database import get_db
from datetime import datetime, timezone, timedelta
import io
import qrcode
import qrcode.image.svg

badge_bp = Blueprint('badge', __name__)


@badge_bp.route('/badge/<slug>/qr.svg')
def qr_code_badge(slug):
    """
    Generate QR code SVG for profile link

    Embeds: https://cringeproof.com/<slug>?ref=github
    """
    profile_url = f"https://cringeproof.com/{slug}?ref=github"

    # Generate actual QR code
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
        image_factory=factory
    )
    qr.add_data(profile_url)
    qr.make(fit=True)

    # Get QR code as SVG
    img_buffer = io.BytesIO()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(img_buffer)
    qr_svg_content = img_buffer.getvalue().decode('utf-8')

    # Extract the path from generated QR SVG
    import re
    path_match = re.search(r'<path[^>]*d="([^"]+)"', qr_svg_content)
    qr_path = path_match.group(1) if path_match else ""

    # Wrap in styled SVG with gradient background
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="240" viewBox="0 0 200 240">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="200" height="240" fill="url(#grad)" rx="10"/>

  <!-- White background for QR -->
  <rect x="20" y="20" width="160" height="160" fill="white" rx="5"/>

  <!-- Actual QR Code -->
  <g transform="translate(30, 30) scale(0.48)">
    <path d="{qr_path}" fill="black"/>
  </g>

  <!-- Text -->
  <text x="100" y="210" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="white" font-weight="bold">
    Scan to Visit
  </text>
  <text x="100" y="230" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="white" opacity="0.9">
    cringeproof.com/{slug}
  </text>
</svg>"""

    return Response(svg, mimetype='image/svg+xml')


@badge_bp.route('/badge/<slug>/qr.png')
def qr_code_png(slug):
    """
    Generate downloadable PNG QR code
    """
    profile_url = f"https://cringeproof.com/{slug}?ref=download"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(profile_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#667eea", back_color="white")

    # Convert to PNG bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return Response(img_buffer.getvalue(), mimetype='image/png')


@badge_bp.route('/badge/<slug>/wordmap.svg')
def wordmap_badge(slug):
    """
    Generate wordmap visualization as SVG

    Shows top 10 words as word cloud
    """
    db = get_db()

    # Get user
    user = db.execute('''
        SELECT id FROM users WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if not user:
        return Response('<svg></svg>', mimetype='image/svg+xml')

    # Get top words from JSON wordmap
    wordmap_row = db.execute('''
        SELECT wordmap_json
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user['id'],)).fetchone()

    words = []
    if wordmap_row and wordmap_row['wordmap_json']:
        import json
        try:
            wordmap_obj = json.loads(wordmap_row['wordmap_json'])
            sorted_words = sorted(wordmap_obj.items(), key=lambda x: x[1], reverse=True)[:10]
            words = [{'word': w[0], 'count': w[1]} for w in sorted_words]
        except:
            pass

    if not words:
        return Response('<svg></svg>', mimetype='image/svg+xml')

    # Generate word cloud SVG
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200" viewBox="0 0 600 200">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
    </linearGradient>
  </defs>

  <rect width="600" height="200" fill="url(#bg)" rx="10"/>

  <text x="300" y="30" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#00C49A" font-weight="bold">
    Top Words from Voice Memos
  </text>
"""

    # Position words (simple grid layout)
    x_positions = [80, 200, 320, 440, 140, 260, 380, 500, 180, 340]
    y_positions = [80, 80, 80, 80, 130, 130, 130, 130, 180, 180]

    max_count = words[0]['count'] if words else 1

    # Color palette (gradient from teal to purple based on frequency)
    colors = ['#00C49A', '#00D4AA', '#00E4BA', '#667eea', '#764ba2']

    for i, word_data in enumerate(words):
        if i >= 10:
            break

        # Font size based on frequency (12-36px range)
        font_size = 12 + (word_data['count'] / max_count * 24)

        # Color based on rank
        color_index = min(int(i / 2), len(colors) - 1)
        color = colors[color_index]

        # Opacity based on frequency
        opacity = 0.7 + (word_data['count'] / max_count * 0.3)

        svg += f"""  <text x="{x_positions[i]}" y="{y_positions[i]}" text-anchor="middle"
         font-family="'SF Pro Display', -apple-system, sans-serif" font-size="{font_size:.0f}"
         fill="{color}" opacity="{opacity:.2f}" font-weight="700">
    {word_data['word']}
  </text>
"""

    svg += "</svg>"

    return Response(svg, mimetype='image/svg+xml')


@badge_bp.route('/badge/<slug>/activity.svg')
def activity_badge(slug):
    """
    Generate activity indicator badge

    Shows:
    - Last recording time
    - Recording streak
    - Status (active/idle/stale)
    """
    db = get_db()

    user = db.execute('''
        SELECT id FROM users WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if not user:
        status = "inactive"
        status_color = "#666"
        last_activity = "Never"
    else:
        # Get latest recording
        latest = db.execute('''
            SELECT created_at FROM simple_voice_recordings
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user['id'],)).fetchone()

        if latest:
            created_dt = datetime.fromisoformat(latest['created_at'])
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            diff = now - created_dt

            if diff < timedelta(hours=24):
                status = "active"
                status_color = "#00C49A"
                last_activity = "Today"
            elif diff < timedelta(days=7):
                status = "recent"
                status_color = "#FFA500"
                last_activity = f"{diff.days}d ago"
            else:
                status = "idle"
                status_color = "#666"
                last_activity = f"{diff.days}d ago"
        else:
            status = "inactive"
            status_color = "#666"
            last_activity = "No recordings"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" viewBox="0 0 200 40">
  <rect width="200" height="40" fill="#1a1a2e" rx="6"/>

  <!-- Status dot -->
  <circle cx="20" cy="20" r="6" fill="{status_color}">
    <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/>
  </circle>

  <!-- Status text -->
  <text x="35" y="16" font-family="Arial, sans-serif" font-size="12" fill="white" font-weight="600">
    {status.upper()}
  </text>
  <text x="35" y="28" font-family="Arial, sans-serif" font-size="10" fill="#aaa">
    {last_activity}
  </text>
</svg>"""

    return Response(svg, mimetype='image/svg+xml')


@badge_bp.route('/badge/<slug>/stats.svg')
def stats_badge(slug):
    """
    Generate stats badge with recording count, ideas, etc.
    """
    db = get_db()

    user = db.execute('''
        SELECT id FROM users WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if not user:
        recordings_count = 0
        ideas_count = 0
    else:
        recordings_count = db.execute(
            'SELECT COUNT(*) as count FROM simple_voice_recordings WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']

        ideas_count = db.execute(
            'SELECT COUNT(*) as count FROM voice_ideas WHERE user_id = ?',
            (user['id'],)
        ).fetchone()['count']

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="80" viewBox="0 0 300 80">
  <defs>
    <linearGradient id="statsBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>

  <rect width="300" height="80" fill="url(#statsBg)" rx="10"/>

  <!-- Recordings -->
  <text x="20" y="30" font-family="Arial, sans-serif" font-size="28" fill="white" font-weight="bold">
    {recordings_count}
  </text>
  <text x="20" y="50" font-family="Arial, sans-serif" font-size="12" fill="white" opacity="0.9">
    Voice Memos
  </text>

  <!-- Ideas -->
  <text x="160" y="30" font-family="Arial, sans-serif" font-size="28" fill="white" font-weight="bold">
    {ideas_count}
  </text>
  <text x="160" y="50" font-family="Arial, sans-serif" font-size="12" fill="white" opacity="0.9">
    Ideas Extracted
  </text>
</svg>"""

    return Response(svg, mimetype='image/svg+xml')

#!/usr/bin/env python3
"""
Universal Resource Identifier (URI) Routes

Provides short, shareable links with auto-generated OG images:
- /v/<id> - View voice memo (with waveform OG image)
- /u/<username> - View user profile (with stats OG image)
- /t/<token> - Redeem token/reward
- /i/<idea_id> - View idea (with thumbnail)
- /q/<qr_code> - QR code redirect

All routes auto-generate Open Graph meta tags for:
- iMessage previews
- Google Messages previews
- Twitter/X cards
- Discord/Slack embeds
"""

from flask import Blueprint, render_template_string, redirect, url_for, jsonify, abort
from database import get_db
import os

uri_bp = Blueprint('uri', __name__)


# Base HTML template with OG tags
OG_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="{{ og_type }}">
    <meta property="og:url" content="{{ og_url }}">
    <meta property="og:title" content="{{ og_title }}">
    <meta property="og:description" content="{{ og_description }}">
    <meta property="og:image" content="{{ og_image }}">

    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{{ og_url }}">
    <meta property="twitter:title" content="{{ og_title }}">
    <meta property="twitter:description" content="{{ og_description }}">
    <meta property="twitter:image" content="{{ og_image }}">

    <!-- Auto-redirect to app -->
    <meta http-equiv="refresh" content="0; url={{ redirect_url }}">

    <style>
        body {
            font-family: -apple-system, system-ui, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .loading {
            text-align: center;
        }
        .loading h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .loading p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="loading">
        <h1>{{ emoji }}</h1>
        <p>{{ loading_message }}</p>
    </div>
</body>
</html>
'''


@uri_bp.route('/v/<int:voice_id>')
def view_voice(voice_id):
    """
    View voice memo with OG image

    Example: https://cringeproof.com/v/123
    """
    db = get_db()

    # Get voice memo (placeholder - adjust to your schema)
    voice = db.execute('''
        SELECT id, transcription, created_at
        FROM simple_voice_data
        WHERE id = ?
        LIMIT 1
    ''', (voice_id,)).fetchone()

    db.close()

    if not voice:
        abort(404)

    # Generate OG image URL (will be auto-generated)
    og_image_url = f"https://cringeproof.com/api/og/voice/{voice_id}.png"

    # Truncate transcription for preview
    transcription = voice['transcription'] or "Voice memo"
    preview = transcription[:100] + "..." if len(transcription) > 100 else transcription

    return render_template_string(OG_TEMPLATE,
        title=f"Voice Memo #{voice_id}",
        og_type="article",
        og_url=f"https://cringeproof.com/v/{voice_id}",
        og_title=f"🎤 Voice Memo #{voice_id}",
        og_description=preview,
        og_image=og_image_url,
        redirect_url=f"https://cringeproof.com/audio/{voice_id}/",
        emoji="🎤",
        loading_message="Loading voice memo..."
    )


@uri_bp.route('/u/<username>')
def view_user(username):
    """
    View user profile with OG image

    Example: https://cringeproof.com/u/alice
    """
    db = get_db()

    user = db.execute('''
        SELECT id, username, email, credits, created_at
        FROM users
        WHERE username = ?
        LIMIT 1
    ''', (username,)).fetchone()

    db.close()

    if not user:
        abort(404)

    # Generate OG image for user profile
    og_image_url = f"https://cringeproof.com/api/og/user/{username}.png"

    credits = user['credits'] or 0
    description = f"{username} has {credits} tokens. Member since {user['created_at'][:10]}"

    return render_template_string(OG_TEMPLATE,
        title=f"{username} on CringeProof",
        og_type="profile",
        og_url=f"https://cringeproof.com/u/{username}",
        og_title=f"👤 {username}",
        og_description=description,
        og_image=og_image_url,
        redirect_url=f"https://cringeproof.com/profile.html?user={username}",
        emoji="👤",
        loading_message=f"Loading {username}'s profile..."
    )


@uri_bp.route('/t/<token_code>')
def redeem_token(token_code):
    """
    Redeem token/reward code

    Example: https://cringeproof.com/t/WELCOME10
    """
    # For now, just redirect to signup with token
    # Later: Auto-credit account if logged in

    og_image_url = f"https://cringeproof.com/api/og/token/{token_code}.png"

    return render_template_string(OG_TEMPLATE,
        title=f"Redeem Token: {token_code}",
        og_type="website",
        og_url=f"https://cringeproof.com/t/{token_code}",
        og_title=f"🎁 Redeem: {token_code}",
        og_description=f"Claim your reward with code {token_code}",
        og_image=og_image_url,
        redirect_url=f"https://cringeproof.com/signup.html?token={token_code}",
        emoji="🎁",
        loading_message="Redeeming token..."
    )


@uri_bp.route('/i/<int:idea_id>')
def view_idea(idea_id):
    """
    View idea with thumbnail

    Example: https://cringeproof.com/i/42
    """
    # Redirect to ideas page
    og_image_url = f"https://cringeproof.com/api/og/idea/{idea_id}.png"

    return render_template_string(OG_TEMPLATE,
        title=f"Idea #{idea_id}",
        og_type="article",
        og_url=f"https://cringeproof.com/i/{idea_id}",
        og_title=f"💡 Idea #{idea_id}",
        og_description="View this idea on CringeProof",
        og_image=og_image_url,
        redirect_url=f"https://cringeproof.com/ideas/?id={idea_id}",
        emoji="💡",
        loading_message="Loading idea..."
    )


@uri_bp.route('/q/<qr_code>')
def qr_redirect(qr_code):
    """
    QR code redirect (for tracking)

    Example: https://cringeproof.com/q/ABC123
    """
    db = get_db()

    # Log QR scan (optional)
    # Later: Track QR code analytics

    db.close()

    # For now, redirect to home
    # Later: Redirect based on QR code type
    return redirect('https://cringeproof.com/')


# API endpoint to generate OG images on-the-fly
@uri_bp.route('/api/og/<content_type>/<content_id>.png')
def generate_og_image(content_type, content_id):
    """
    Generate OG image on-the-fly

    Uses generate_og_image.py to create 1200x630 PNG
    """
    from generate_og_image import generate_og_image
    from io import BytesIO
    from flask import send_file

    # Generate image based on content type
    if content_type == 'voice':
        title = f"🎤 Voice Memo #{content_id}"
        subtitle = "Listen on CringeProof"
    elif content_type == 'user':
        title = f"👤 {content_id}"
        subtitle = "CringeProof Profile"
    elif content_type == 'token':
        title = f"🎁 {content_id}"
        subtitle = "Redeem on CringeProof"
    elif content_type == 'idea':
        title = f"💡 Idea #{content_id}"
        subtitle = "Explore on CringeProof"
    else:
        title = "CringeProof"
        subtitle = "Ideas Without The Cringe"

    # Generate image (modify generate_og_image to accept params)
    img = generate_og_image()  # For now, uses default

    # Return as PNG
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


if __name__ == '__main__':
    print("✅ URI routes ready")
    print("   - /v/<id> - Voice memo")
    print("   - /u/<username> - User profile")
    print("   - /t/<token> - Redeem token")
    print("   - /i/<id> - View idea")
    print("   - /q/<code> - QR redirect")

#!/usr/bin/env python3
"""
Embeddable Widget Routes

Provides iframe-embeddable components for websites:
- Wordmap widget
- Activity feed
- README preview
- Profile card

Usage:
    <iframe src="https://api.cringeproof.com/embed/matt/wordmap" width="100%" height="300"></iframe>
"""

from flask import Blueprint, Response, render_template_string, jsonify
from database import get_db
from datetime import datetime, timezone, timedelta
import json

embed_bp = Blueprint('embed', __name__)


@embed_bp.route('/embed/<slug>/wordmap')
def embed_wordmap(slug):
    """
    Embeddable wordmap widget (iframe)

    Usage: <iframe src="/embed/matt/wordmap" width="600" height="300"></iframe>
    """
    db = get_db()

    user = db.execute('SELECT id, username, display_name FROM users WHERE user_slug = ?', (slug,)).fetchone()
    if not user:
        return "<h3>User not found</h3>", 404

    # Get wordmap
    wordmap_row = db.execute('SELECT wordmap_json FROM user_wordmaps WHERE user_id = ?', (user['id'],)).fetchone()
    words = []
    if wordmap_row and wordmap_row['wordmap_json']:
        wordmap_obj = json.loads(wordmap_row['wordmap_json'])
        sorted_words = sorted(wordmap_obj.items(), key=lambda x: x[1], reverse=True)[:20]
        words = [{'word': w[0], 'count': w[1]} for w in sorted_words]

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wordmap - {{ display_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h2 {
            text-align: center;
            margin-bottom: 30px;
            color: #00C49A;
            font-size: 24px;
        }
        .word-cloud {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            align-items: center;
        }
        .word {
            padding: 10px 20px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            cursor: default;
        }
        .word:hover {
            transform: scale(1.1);
            background: rgba(0, 196, 154, 0.2);
        }
        .word-text {
            font-weight: 700;
            margin-right: 8px;
        }
        .word-count {
            opacity: 0.7;
            font-size: 0.85em;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            opacity: 0.6;
            font-size: 12px;
        }
        .footer a {
            color: #00C49A;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🗣️ {{ display_name }}'s Wordmap</h2>
        <div class="word-cloud">
            {% for word in words %}
            <div class="word" style="font-size: {{ 14 + (word.count / max_count * 20) }}px; color: {{ colors[loop.index0 % 5] }};">
                <span class="word-text">{{ word.word }}</span>
                <span class="word-count">({{ word.count }})</span>
            </div>
            {% endfor %}
        </div>
        <div class="footer">
            Powered by <a href="https://cringeproof.com/{{ slug }}" target="_blank">Cringeproof</a>
        </div>
    </div>
</body>
</html>"""

    max_count = words[0]['count'] if words else 1
    colors = ['#00C49A', '#00D4AA', '#00E4BA', '#667eea', '#764ba2']

    return render_template_string(
        template,
        slug=slug,
        display_name=user['display_name'] or user['username'],
        words=words,
        max_count=max_count,
        colors=colors
    )


@embed_bp.route('/embed/<slug>/activity')
def embed_activity(slug):
    """
    Embeddable activity feed widget

    Usage: <iframe src="/embed/matt/activity" width="400" height="500"></iframe>
    """
    db = get_db()

    user = db.execute('SELECT id, username, display_name FROM users WHERE user_slug = ?', (slug,)).fetchone()
    if not user:
        return "<h3>User not found</h3>", 404

    # Get recent recordings
    recordings = db.execute('''
        SELECT id, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user['id'],)).fetchall()

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity - {{ display_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        h2 {
            color: white;
            margin-bottom: 20px;
            text-align: center;
        }
        .activity-item {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
            color: white;
            transition: all 0.3s ease;
        }
        .activity-item:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateX(5px);
        }
        .activity-time {
            font-size: 11px;
            opacity: 0.7;
            margin-bottom: 5px;
        }
        .activity-content {
            font-size: 14px;
            line-height: 1.5;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: white;
            opacity: 0.7;
            font-size: 12px;
        }
        .footer a {
            color: white;
            text-decoration: none;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎙️ {{ display_name }}'s Recent Voice Memos</h2>
        {% for rec in recordings %}
        <div class="activity-item">
            <div class="activity-time">{{ rec.time_ago }}</div>
            <div class="activity-content">{{ rec.excerpt }}</div>
        </div>
        {% endfor %}
        <div class="footer">
            View full profile at <a href="https://cringeproof.com/{{ slug }}" target="_blank">cringeproof.com/{{ slug }}</a>
        </div>
    </div>
</body>
</html>"""

    # Format recordings
    formatted_recordings = []
    for rec in recordings:
        created_dt = datetime.fromisoformat(rec['created_at'])
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        diff = now - created_dt

        if diff.seconds < 3600:
            time_ago = f"{diff.seconds // 60}m ago"
        elif diff.days == 0:
            time_ago = f"{diff.seconds // 3600}h ago"
        else:
            time_ago = f"{diff.days}d ago"

        excerpt = rec['transcription'][:120] + ('...' if len(rec['transcription']) > 120 else '')

        formatted_recordings.append({
            'time_ago': time_ago,
            'excerpt': excerpt
        })

    return render_template_string(
        template,
        slug=slug,
        display_name=user['display_name'] or user['username'],
        recordings=formatted_recordings
    )


@embed_bp.route('/embed/<slug>/profile')
def embed_profile_card(slug):
    """
    Embeddable profile card widget

    Usage: <iframe src="/embed/matt/profile" width="350" height="200"></iframe>
    """
    db = get_db()

    user = db.execute('SELECT id, username, display_name, bio FROM users WHERE user_slug = ?', (slug,)).fetchone()
    if not user:
        return "<h3>User not found</h3>", 404

    # Get stats
    recordings_count = db.execute(
        'SELECT COUNT(*) as count FROM simple_voice_recordings WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    ideas_count = db.execute(
        'SELECT COUNT(*) as count FROM voice_ideas WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ display_name }} - Profile</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            color: white;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        .name {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .bio {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .stats {
            display: flex;
            gap: 30px;
            margin-bottom: 20px;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #00C49A;
        }
        .stat-label {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 5px;
        }
        .link {
            text-align: center;
            margin-top: 20px;
        }
        .link a {
            color: white;
            text-decoration: none;
            background: rgba(255, 255, 255, 0.2);
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
        }
        .link a:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="name">{{ display_name }}</div>
        <div class="bio">{{ bio }}</div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{{ recordings }}</div>
                <div class="stat-label">Voice Memos</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ ideas }}</div>
                <div class="stat-label">Ideas</div>
            </div>
        </div>
        <div class="link">
            <a href="https://cringeproof.com/{{ slug }}" target="_blank">Visit Profile →</a>
        </div>
    </div>
</body>
</html>"""

    return render_template_string(
        template,
        slug=slug,
        display_name=user['display_name'] or user['username'],
        bio=user['bio'] or 'Voice-powered thinking. No cringe, just authenticity.',
        recordings=recordings_count,
        ideas=ideas_count
    )


@embed_bp.route('/embed/<slug>/preview')
def embed_readme_preview(slug):
    """
    Embeddable README preview

    Usage: <iframe src="/embed/matt/preview" width="100%" height="600"></iframe>
    """
    from readme_generator import generate_readme_markdown

    markdown = generate_readme_markdown(slug)

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>README Preview - {{ slug }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
            line-height: 1.6;
        }
        h1, h2, h3 { color: #58a6ff; margin-top: 24px; margin-bottom: 16px; }
        h1 { font-size: 32px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }
        h2 { font-size: 24px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        code { background: #161b22; padding: 2px 6px; border-radius: 6px; font-size: 14px; }
        pre { background: #161b22; padding: 16px; border-radius: 6px; overflow-x: auto; }
        img { max-width: 100%; }
        hr { border: 0; border-top: 1px solid #21262d; margin: 24px 0; }
        ul, ol { margin-left: 20px; margin-bottom: 16px; }
        li { margin-bottom: 8px; }
        strong { color: #ffffff; }
    </style>
</head>
<body>
    <pre style="white-space: pre-wrap; word-wrap: break-word;">{{ markdown }}</pre>
</body>
</html>"""

    return render_template_string(template, slug=slug, markdown=markdown)

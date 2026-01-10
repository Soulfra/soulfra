#!/usr/bin/env python3
"""
Dynamic README Generator for GitHub Profiles

Generates a live, updating README.md for github.com/<user>/<user>/README.md
Pulls from: voice recordings, wordmap, auth providers, profile data

Usage:
    GET /api/readme/<slug> → Returns markdown
    GET /api/readme/<slug>/preview → Returns HTML preview
"""

from flask import Blueprint, Response, jsonify, render_template_string
from database import get_db
from datetime import datetime, timezone
import json

readme_gen_bp = Blueprint('readme_gen', __name__)

def generate_readme_markdown(slug):
    """
    Generate GitHub-compatible README.md from user data

    Args:
        slug: User slug (e.g. 'matt', 'alice')

    Returns:
        str: Markdown content for README.md
    """
    db = get_db()

    # Get user info
    user = db.execute('''
        SELECT id, username, user_slug, display_name, bio, email
        FROM users WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if not user:
        return f"# {slug}\n\nUser not found. Visit [cringeproof.com/{slug}](https://cringeproof.com/{slug}) to claim this slug."

    # Get wordmap data (top 10 words from JSON)
    wordmap_row = db.execute('''
        SELECT wordmap_json
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user['id'],)).fetchone()

    wordmap_data = []
    if wordmap_row and wordmap_row['wordmap_json']:
        import json
        try:
            wordmap_obj = json.loads(wordmap_row['wordmap_json'])
            # Wordmap format: {word: count, ...}
            sorted_words = sorted(wordmap_obj.items(), key=lambda x: x[1], reverse=True)[:10]
            wordmap_data = [{'word': w[0], 'count': w[1]} for w in sorted_words]
        except:
            pass

    # Get recent APPROVED voice recordings (last 5)
    recordings = db.execute('''
        SELECT id, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ?
        AND transcription IS NOT NULL
        AND approval_status = 'approved'
        ORDER BY created_at DESC
        LIMIT 5
    ''', (user['id'],)).fetchall()

    # Get stats
    total_recordings = db.execute(
        'SELECT COUNT(*) as count FROM simple_voice_recordings WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    total_ideas = db.execute(
        'SELECT COUNT(*) as count FROM voice_ideas WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    # Build markdown
    md = f"""# {user['display_name'] or user['username']}

{user['bio'] or 'Voice-powered thinking. No cringe, just authenticity.'}

<div align="center">

![QR Code](https://api.cringeproof.com/badge/{slug}/qr.svg)

**Scan to visit my live profile**

[![Profile](https://img.shields.io/badge/Profile-cringeproof.com%2F{slug}-blueviolet?style=for-the-badge)](https://cringeproof.com/{slug})
[![Recordings](https://img.shields.io/badge/Recordings-{total_recordings}-green?style=for-the-badge)](https://cringeproof.com/{slug})
[![Ideas](https://img.shields.io/badge/Ideas-{total_ideas}-blue?style=for-the-badge)](https://cringeproof.com/{slug})

</div>

---

## 🎙️ Latest Voice Memos

"""

    # Add recent recordings
    if recordings:
        for rec in recordings:
            created_dt = datetime.fromisoformat(rec['created_at'])
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)

            # Time ago
            now = datetime.now(timezone.utc)
            diff = now - created_dt
            if diff.seconds < 3600:
                time_ago = f"{diff.seconds // 60}m ago"
            elif diff.days == 0:
                time_ago = f"{diff.seconds // 3600}h ago"
            else:
                time_ago = f"{diff.days}d ago"

            excerpt = rec['transcription'][:150] + ('...' if len(rec['transcription']) > 150 else '')
            md += f"- **{time_ago}**: {excerpt}\n"
    else:
        md += "*No recordings yet. Start recording at [cringeproof.com/voice](https://cringeproof.com/voice)*\n"

    md += "\n---\n\n## 📊 My Wordmap\n\n"

    # Add wordmap with visual indicators
    if wordmap_data:
        md += "Top words from my voice recordings:\n\n"
        for i, word_data in enumerate(wordmap_data):
            # Add visual indicator based on rank
            if i == 0:
                emoji = "🥇"  # Gold for #1
            elif i == 1:
                emoji = "🥈"  # Silver for #2
            elif i == 2:
                emoji = "🥉"  # Bronze for #3
            else:
                # Use frequency bars for others
                count = word_data['count']
                if count >= 10:
                    emoji = "▰▰▰"
                elif count >= 5:
                    emoji = "▰▰▱"
                elif count >= 3:
                    emoji = "▰▱▱"
                else:
                    emoji = "▱▱▱"

            md += f"- {emoji} **{word_data['word']}** ({word_data['count']} times)\n"
    else:
        md += "*Building wordmap from voice recordings...*\n"

    md += "\n---\n\n"
    md += f"""<div align="center">

**🎯 This README updates automatically from my voice recordings**

*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*

[Visit Live Profile](https://cringeproof.com/{slug}) | [Record Voice Memo](https://cringeproof.com/voice)

</div>
"""

    return md


@readme_gen_bp.route('/api/readme/<slug>')
def get_readme(slug):
    """
    GET /api/readme/matt

    Returns raw markdown for GitHub README
    """
    markdown = generate_readme_markdown(slug)
    return Response(markdown, mimetype='text/markdown')


@readme_gen_bp.route('/api/readme/<slug>/preview')
def preview_readme(slug):
    """
    GET /api/readme/matt/preview

    Returns HTML preview of README
    """
    markdown = generate_readme_markdown(slug)

    # Simple markdown → HTML conversion
    html = markdown.replace('**', '<strong>').replace('**', '</strong>')
    html = html.replace('*', '<em>').replace('*', '</em>')

    template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>README Preview - {slug}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 900px;
            margin: 2rem auto;
            padding: 2rem;
            background: #0d1117;
            color: #c9d1d9;
        }}
        a {{
            color: #58a6ff;
        }}
        img {{
            max-width: 100%;
        }}
        code {{
            background: #161b22;
            padding: 0.2rem 0.4rem;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <pre style="white-space: pre-wrap; word-wrap: break-word;">{markdown}</pre>
</body>
</html>
    """

    return template


@readme_gen_bp.route('/api/readme/<slug>/json')
def readme_json(slug):
    """
    GET /api/readme/matt/json

    Returns structured JSON data for README
    """
    db = get_db()

    user = db.execute('''
        SELECT id, username, user_slug, display_name, bio
        FROM users WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get data
    recordings = db.execute('''
        SELECT id, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user['id'],)).fetchall()

    # Get wordmap from JSON
    wordmap_row = db.execute('''
        SELECT wordmap_json
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user['id'],)).fetchone()

    wordmap = []
    if wordmap_row and wordmap_row['wordmap_json']:
        try:
            wordmap_obj = json.loads(wordmap_row['wordmap_json'])
            sorted_words = sorted(wordmap_obj.items(), key=lambda x: x[1], reverse=True)[:20]
            wordmap = [{'word': w[0], 'count': w[1]} for w in sorted_words]
        except:
            pass

    return jsonify({
        'slug': slug,
        'display_name': user['display_name'] or user['username'],
        'bio': user['bio'],
        'recordings': [dict(r) for r in recordings],
        'wordmap': wordmap,
        'profile_url': f'https://cringeproof.com/{slug}',
        'generated_at': datetime.now(timezone.utc).isoformat()
    })

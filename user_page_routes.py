"""
User Page Routes - Serve personalized pages at /<slug>
"""
from flask import Blueprint, render_template_string, jsonify
from database import get_db
from wordmap_css_generator import generate_css_from_wordmap, get_wordmap_metadata

user_page_bp = Blueprint('user_page', __name__)

USER_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ username }} - CringeProof</title>
<meta name="description" content="{{ username }}'s personalized wordmap page">
<link rel="stylesheet" href="/css/soulfra.css">
<style>
{{ custom_css }}
</style>
</head>
<body>

<nav class="soulfra-nav">
    <div class="soulfra-nav-container">
        <a href="/" class="soulfra-logo">🚫 CringeProof</a>
        <div class="soulfra-links">
            <a href="/">🏠 Home</a>
            <a href="/wall.html">🎯 Wall</a>
            <a href="/record-v2.html" class="soulfra-record-btn">🎙️ Record</a>
        </div>
    </div>
</nav>

<div class="container" style="padding-top: 100px;">
    <header class="header">
        <h1>{{ username }}</h1>
        <p>{{ bio or "Voice-powered wordmap enthusiast" }}</p>
        <p style="font-size: 1rem; opacity: 0.7; margin-top: 1rem;">
            🔗 cringeproof.com/{{ slug }}
        </p>
    </header>

    <!-- Wordmap Visualization -->
    <div class="wordmap-section" style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 16px; margin-bottom: 3rem;">
        <h2 style="text-align: center; margin-bottom: 2rem;">📊 My Wordmap</h2>

        <div class="wordmap-stats" style="display: flex; justify-content: center; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap;">
            <div class="stat" style="text-align: center;">
                <div style="font-size: 2rem; font-weight: 900; color: var(--primary-color);">{{ wordmap.total_words }}</div>
                <div style="font-size: 0.9rem; opacity: 0.7;">Total Words</div>
            </div>
            <div class="stat" style="text-align: center;">
                <div style="font-size: 2rem; font-weight: 900; color: var(--secondary-color);">{{ wordmap.unique_words }}</div>
                <div style="font-size: 0.9rem; opacity: 0.7;">Unique Words</div>
            </div>
            <div class="stat" style="text-align: center;">
                <div style="font-size: 2rem; font-weight: 900; color: var(--accent-color);">{{ recordings_count }}</div>
                <div style="font-size: 0.9rem; opacity: 0.7;">Voice Memos</div>
            </div>
        </div>

        <div class="top-words" style="display: flex; flex-direction: column; gap: 1rem;">
            {% for item in wordmap.top_words[:10] %}
            <div class="word-bar" style="display: flex; align-items: center; gap: 1rem;">
                <div class="word-color" style="width: 24px; height: 24px; background: {{ item.color }}; border-radius: 4px;"></div>
                <div class="word-name" style="flex: 0 0 150px; font-weight: 700;">{{ item.word }}</div>
                <div class="bar-container" style="flex: 1; background: rgba(0,0,0,0.3); height: 24px; border-radius: 12px; overflow: hidden;">
                    <div class="bar-fill" style="height: 100%; background: {{ item.color }}; width: {{ (item.count / wordmap.top_words[0].count * 100)|int }}%;"></div>
                </div>
                <div class="word-count" style="flex: 0 0 50px; text-align: right; font-weight: 600; color: var(--secondary-color);">{{ item.count }}</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Recent Voice Memos -->
    <div class="memos-section" style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 16px;">
        <h2 style="text-align: center; margin-bottom: 2rem;">🎙️ Recent Voice Memos</h2>

        {% if recent_memos %}
        <div class="memos-list" style="display: flex; flex-direction: column; gap: 1rem;">
            {% for memo in recent_memos %}
            <div class="memo-card" style="background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 12px; border-left: 4px solid var(--primary-color);">
                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 0.85rem; opacity: 0.7;">{{ memo.created_at }}</span>
                </div>
                <p style="line-height: 1.6;">{{ memo.excerpt }}</p>
                {% if memo.audio_url %}
                <audio controls style="width: 100%; margin-top: 1rem;">
                    <source src="{{ memo.audio_url }}" type="audio/webm">
                </audio>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p style="text-align: center; opacity: 0.7;">No voice memos yet. Start recording to build your wordmap!</p>
        {% endif %}
    </div>

    <!-- Cross-Pollination Info -->
    {% if parent_domain %}
    <div class="lineage" style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 12px; margin-top: 2rem; text-align: center;">
        <p style="opacity: 0.7; font-size: 0.9rem;">
            🌸 Descended from <strong>{{ parent_domain }}</strong> · Cross-pollinated branding
        </p>
    </div>
    {% endif %}
</div>

</body>
</html>
"""

@user_page_bp.route('/<slug>')
def user_page(slug):
    """
    Serve personalized user page at /<slug>

    Example: /alice → Alice's page with her wordmap CSS

    Skip if slug contains file extensions (let static file handler catch it)
    """
    import os
    from flask import send_from_directory

    # Don't intercept static files - serve them from voice-archive folder
    if '.' in slug:
        try:
            return send_from_directory('voice-archive', slug)
        except:
            from flask import abort
            abort(404)

    db = get_db()

    # First check if this is a README profile
    profile = db.execute('''
        SELECT * FROM user_profiles WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if profile:
        # Serve the new profile dashboard
        return send_from_directory('voice-archive', 'profile-dashboard.html')

    # Find user by slug (legacy wordmap profiles)
    user = db.execute('''
        SELECT id, username, user_slug, display_name, bio
        FROM users WHERE user_slug = ?
    ''', (slug,)).fetchone()

    if not user:
        return jsonify({'error': f'User slug "{slug}" not found'}), 404

    # Generate CSS from wordmap
    custom_css = generate_css_from_wordmap(user['id'], parent_domain='cringeproof')

    # Get wordmap metadata
    wordmap = get_wordmap_metadata(user['id'])

    # Get recent voice memos
    recent_memos = db.execute('''
        SELECT
            transcription,
            created_at
        FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 5
    ''', (user['id'],)).fetchall()

    # Format memos for display
    memos = []
    for memo in recent_memos:
        excerpt = memo['transcription'][:200] + ('...' if len(memo['transcription']) > 200 else '')
        memos.append({
            'excerpt': excerpt,
            'created_at': memo['created_at'],
            'audio_url': None  # Audio playback not available yet
        })

    # Count total recordings
    recordings_count = db.execute(
        'SELECT COUNT(*) as count FROM simple_voice_recordings WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    return render_template_string(
        USER_PAGE_TEMPLATE,
        username=user['display_name'] or user['username'],
        slug=user['user_slug'],
        bio=user['bio'],
        custom_css=custom_css,
        wordmap=wordmap,
        recent_memos=memos,
        recordings_count=recordings_count,
        parent_domain='cringeproof'  # For cross-pollination display
    )

@user_page_bp.route('/api/user/<slug>/css')
def get_user_css(slug):
    """
    Get just the CSS for a user (API endpoint)

    GET /api/user/alice/css
    Returns raw CSS
    """
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE user_slug = ?', (slug,)).fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    css = generate_css_from_wordmap(user['id'], parent_domain='cringeproof')

    return css, 200, {'Content-Type': 'text/css'}

@user_page_bp.route('/api/user/<slug>/wordmap')
def get_user_wordmap_api(slug):
    """
    Get user's wordmap metadata (API endpoint)

    GET /api/user/alice/wordmap
    Returns JSON
    """
    db = get_db()
    user = db.execute('SELECT id, username FROM users WHERE user_slug = ?', (slug,)).fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    wordmap = get_wordmap_metadata(user['id'])

    return jsonify({
        'success': True,
        'username': user['username'],
        'slug': slug,
        'wordmap': wordmap
    })

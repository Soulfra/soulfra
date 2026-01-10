#!/usr/bin/env python3
"""
Widget Carousel - Embeddable Rotating Experience System

Like Habbo Hotel rooms but better - embeddable mini-games/experiences that:
- Rotate automatically (Universe → Arena → Marketplace)
- Run on safe ports (managed by UNFUCKABLE_PORT_MANAGER)
- Log all interactions to training_contributions
- Work across domains (better than Supermemory)

Usage:
    <iframe src="https://cringeproof.com/widget/carousel"></iframe>

Features:
- No installation required
- Cross-domain messaging (postMessage API)
- Persistent user state
- Gamification (cringe_score, rewards, districts)
"""

from flask import Blueprint, render_template, request, jsonify
from database import get_db
import json
from datetime import datetime
import hashlib

widget_carousel_bp = Blueprint('widget_carousel', __name__)

# Port configuration (from UNFUCKABLE_PORT_MANAGER)
WIDGET_PORTS = {
    'universe': 8888,
    'arena': 4444,
    'marketplace': 7777,
    'immersion': 5555,
    'automation': 9090
}

def get_live_carousel_widgets():
    """
    Generate widget carousel content from live CringeProof data

    Each widget shows:
    - Latest question from narrative sessions (Exploration)
    - Top multiplayer room (Combat)
    - Trending prediction from feed (Commerce)
    - Popular voice idea (Creativity)
    """
    db = get_db()
    widgets = []

    # Widget 1: Exploration - Latest Narrative Question
    try:
        cursor = db.execute('''
            SELECT current_chapter, brand_slug, created_at
            FROM narrative_sessions
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        session = cursor.fetchone()

        if session:
            chapter_num = session['current_chapter'] or 1
            description = f"Chapter {chapter_num} • Latest Question of the Hour"
        else:
            description = "Navigate the multi-dimensional universe"

        widgets.append({
            'id': 'universe',
            'name': 'Soulfra Universe',
            'port': 8888,
            'district': 'Exploration',
            'description': description,
            'color': '#8B5CF6',
            'action_url': '/cringeproof/narrative/soulfra'
        })
    except Exception as e:
        print(f"Error loading universe widget: {e}")
        widgets.append({
            'id': 'universe',
            'name': 'Soulfra Universe',
            'port': 8888,
            'district': 'Exploration',
            'description': 'Navigate the multi-dimensional universe',
            'color': '#8B5CF6',
            'action_url': '/cringeproof/narrative/soulfra'
        })

    # Widget 2: Combat - Multiplayer Arena Stats
    try:
        cursor = db.execute('''
            SELECT COUNT(*) as players
            FROM training_contributions
            WHERE district = 'Combat'
            AND created_at > datetime('now', '-1 hour')
        ''')
        row = cursor.fetchone()
        players = row['players'] if row else 0

        description = f"{players} players in last hour" if players > 0 else "Team-based combat and challenges"

        widgets.append({
            'id': 'arena',
            'name': 'Multiplayer Arena',
            'port': 4444,
            'district': 'Combat',
            'description': description,
            'color': '#EF4444',
            'action_url': '/cringeproof/create-room'
        })
    except Exception as e:
        print(f"Error loading arena widget: {e}")
        widgets.append({
            'id': 'arena',
            'name': 'Multiplayer Arena',
            'port': 4444,
            'district': 'Combat',
            'description': 'Team-based combat and challenges',
            'color': '#EF4444',
            'action_url': '/cringeproof/create-room'
        })

    # Widget 3: Commerce - Top Voice Prediction
    try:
        cursor = db.execute('''
            SELECT title, score
            FROM voice_ideas
            WHERE status = 'active'
            ORDER BY score DESC
            LIMIT 1
        ''')
        idea = cursor.fetchone()

        if idea and idea['title']:
            description = f"💡 {idea['title'][:40]}..."
        else:
            description = "Trade ideas and collaborate"

        widgets.append({
            'id': 'marketplace',
            'name': 'Idea Marketplace',
            'port': 7777,
            'district': 'Commerce',
            'description': description,
            'color': '#10B981',
            'action_url': '/feed'
        })
    except Exception as e:
        print(f"Error loading marketplace widget: {e}")
        widgets.append({
            'id': 'marketplace',
            'name': 'Idea Marketplace',
            'port': 7777,
            'district': 'Commerce',
            'description': 'Trade ideas and collaborate',
            'color': '#10B981',
            'action_url': '/feed'
        })

    # Widget 4: Creativity - Popular Voice Contributions
    try:
        cursor = db.execute('''
            SELECT COUNT(*) as total
            FROM simple_voice_recordings
            WHERE transcription IS NOT NULL
            AND created_at > datetime('now', '-24 hours')
        ''')
        row = cursor.fetchone()
        total = row['total'] if row else 0

        description = f"{total} voice ideas today" if total > 0 else "Build and create together"

        widgets.append({
            'id': 'immersion',
            'name': 'Immersive Experience',
            'port': 5555,
            'district': 'Creativity',
            'description': description,
            'color': '#F59E0B',
            'action_url': '/voice'
        })
    except Exception as e:
        print(f"Error loading immersion widget: {e}")
        widgets.append({
            'id': 'immersion',
            'name': 'Immersive Experience',
            'port': 5555,
            'district': 'Creativity',
            'description': 'Build and create together',
            'color': '#F59E0B',
            'action_url': '/voice'
        })

    return widgets


# Static fallback for non-CringeProof contexts
CAROUSEL_WIDGETS_STATIC = [
    {
        'id': 'universe',
        'name': 'Soulfra Universe',
        'port': 8888,
        'district': 'Exploration',
        'description': 'Navigate the multi-dimensional universe',
        'color': '#8B5CF6',
        'action_url': '/cringeproof/narrative/soulfra'
    },
    {
        'id': 'arena',
        'name': 'Multiplayer Arena',
        'port': 4444,
        'district': 'Combat',
        'description': 'Team-based combat and challenges',
        'color': '#EF4444',
        'action_url': '/cringeproof/create-room'
    },
    {
        'id': 'marketplace',
        'name': 'Idea Marketplace',
        'port': 7777,
        'district': 'Commerce',
        'description': 'Trade ideas and collaborate',
        'color': '#10B981',
        'action_url': '/feed'
    },
    {
        'id': 'immersion',
        'name': 'Immersive Experience',
        'port': 5555,
        'district': 'Creativity',
        'description': 'Build and create together',
        'color': '#F59E0B',
        'action_url': '/voice'
    }
]


def log_widget_interaction(widget_id, user_id, action_type, action_data):
    """
    Log widget interactions to training_contributions

    Args:
        widget_id: Which widget (universe, arena, etc.)
        user_id: User ID (or None for anonymous)
        action_type: Type of action (click, voice, text, movement, etc.)
        action_data: JSON data about the action
    """
    try:
        db = get_db()

        # Create extracted text from action
        extracted_text = f"[{widget_id}] {action_type}: {json.dumps(action_data)}"

        # Generate content hash
        content_hash = hashlib.sha256(extracted_text.encode()).hexdigest()

        # Get widget district
        widget = next((w for w in CAROUSEL_WIDGETS if w['id'] == widget_id), None)
        district = widget['district'] if widget else 'General'

        # Determine zone from user agent or IP
        user_agent = request.headers.get('User-Agent', '')
        if 'Mobile' in user_agent:
            zone = 'Mobile'
        else:
            zone = 'Desktop'

        # Calculate cringe_score (0.0-1.0 based on action authenticity)
        # Higher score = more authentic interaction
        cringe_score = 0.5  # Default
        if action_type == 'voice':
            cringe_score = 0.8  # Voice is more authentic
        elif action_type == 'text':
            cringe_score = 0.6  # Text is moderately authentic
        elif action_type == 'click':
            cringe_score = 0.4  # Clicks are less authentic

        # Determine reward tier
        reward_tier = 'free'  # Default for now

        # Store in training_contributions
        cursor = db.execute('''
            INSERT INTO training_contributions (
                user_id, modality, extracted_text, content_hash,
                district, zone, cringe_score, reward_tier,
                file_size, processing_method, source_table, source_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            'widget_interaction',
            extracted_text,
            content_hash,
            district,
            zone,
            cringe_score,
            reward_tier,
            len(extracted_text.encode()),
            'widget_carousel',
            'widget_interactions',
            None
        ))

        db.commit()

        return {
            'success': True,
            'contribution_id': cursor.lastrowid,
            'cringe_score': cringe_score,
            'district': district
        }

    except Exception as e:
        print(f"Error logging widget interaction: {e}")
        return {'success': False, 'error': str(e)}


@widget_carousel_bp.route('/widget/carousel')
def widget_carousel():
    """
    Main embeddable carousel widget

    GET /widget/carousel?start_widget=arena&auto_rotate=true&live=true

    Returns HTML that can be embedded in iframe
    """
    start_widget = request.args.get('start_widget', 'universe')
    auto_rotate = request.args.get('auto_rotate', 'true').lower() == 'true'
    rotation_interval = int(request.args.get('rotation_interval', 30000))  # 30 seconds
    use_live = request.args.get('live', 'true').lower() == 'true'

    # Use live CringeProof data or static fallback
    widgets = get_live_carousel_widgets() if use_live else CAROUSEL_WIDGETS_STATIC

    return render_template('widgets/carousel.html',
                         widgets=widgets,
                         start_widget=start_widget,
                         auto_rotate=auto_rotate,
                         rotation_interval=rotation_interval)


@widget_carousel_bp.route('/api/widget/log-interaction', methods=['POST'])
def api_widget_log_interaction():
    """
    Log widget interaction

    POST /api/widget/log-interaction
    Body: {
        "widget_id": "arena",
        "user_id": 1,
        "action_type": "click",
        "action_data": {"button": "join_team", "x": 123, "y": 456}
    }

    Returns:
        {
            "success": true,
            "contribution_id": 123,
            "cringe_score": 0.4,
            "district": "Combat"
        }
    """
    try:
        data = request.get_json()

        widget_id = data.get('widget_id')
        user_id = data.get('user_id')
        action_type = data.get('action_type')
        action_data = data.get('action_data', {})

        if not widget_id or not action_type:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: widget_id, action_type'
            }), 400

        result = log_widget_interaction(widget_id, user_id, action_type, action_data)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@widget_carousel_bp.route('/api/widget/get-stats', methods=['GET'])
def api_widget_get_stats():
    """
    Get widget interaction statistics

    GET /api/widget/get-stats?widget_id=arena&limit=100

    Returns:
        {
            "total_interactions": 1234,
            "by_action_type": {"click": 800, "voice": 234, "text": 200},
            "avg_cringe_score": 0.65,
            "top_district": "Combat"
        }
    """
    try:
        widget_id = request.args.get('widget_id')
        limit = int(request.args.get('limit', 100))

        db = get_db()

        # Base query
        where_clause = "WHERE modality = 'widget_interaction'"
        params = []

        if widget_id:
            where_clause += " AND district = ?"
            widget = next((w for w in CAROUSEL_WIDGETS if w['id'] == widget_id), None)
            if widget:
                params.append(widget['district'])

        # Get total count
        cursor = db.execute(f'''
            SELECT COUNT(*) as total FROM training_contributions
            {where_clause}
        ''', params)
        total = cursor.fetchone()['total']

        # Get average cringe score
        cursor = db.execute(f'''
            SELECT AVG(cringe_score) as avg_score FROM training_contributions
            {where_clause}
        ''', params)
        avg_score = cursor.fetchone()['avg_score'] or 0

        # Get interactions by district
        cursor = db.execute(f'''
            SELECT district, COUNT(*) as count
            FROM training_contributions
            {where_clause}
            GROUP BY district
            ORDER BY count DESC
        ''', params)
        by_district = {row['district']: row['count'] for row in cursor.fetchall()}

        # Get recent interactions
        cursor = db.execute(f'''
            SELECT extracted_text, district, cringe_score, created_at
            FROM training_contributions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        ''', params + [limit])
        recent = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'total_interactions': total,
            'avg_cringe_score': round(avg_score, 3),
            'by_district': by_district,
            'recent_interactions': recent
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@widget_carousel_bp.route('/widget/embed-code')
def widget_embed_code():
    """
    Generate embeddable iframe code

    GET /widget/embed-code?widget=arena&width=800&height=600

    Returns HTML page with copy-paste embed code
    """
    widget_id = request.args.get('widget', 'universe')
    width = request.args.get('width', '100%')
    height = request.args.get('height', '600px')
    auto_rotate = request.args.get('auto_rotate', 'true')

    # Generate iframe code
    iframe_src = f"/widget/carousel?start_widget={widget_id}&auto_rotate={auto_rotate}"
    iframe_code = f'<iframe src="{request.host_url.rstrip("/")}{iframe_src}" width="{width}" height="{height}" frameborder="0" allow="microphone; camera; autoplay"></iframe>'

    return render_template('widgets/embed_code.html',
                         iframe_code=iframe_code,
                         widget_id=widget_id,
                         widgets=CAROUSEL_WIDGETS)


def register_widget_carousel_routes(app):
    """Register widget carousel routes"""
    app.register_blueprint(widget_carousel_bp)
    print("🎠 Widget Carousel routes registered:")
    print("   Carousel: GET /widget/carousel")
    print("   Log: POST /api/widget/log-interaction")
    print("   Stats: GET /api/widget/get-stats")
    print("   Embed Code: GET /widget/embed-code")

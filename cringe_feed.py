#!/usr/bin/env python3
"""
CringeProof Feed - Decentralized TikTok with Git + Pixel Rendering

Like TikTok but:
- Content stored on GitHub Pages (decentralized)
- Videos rendered real-time from layers (no storage)
- Recommendations via "cringe wordmaps" (transparent algo)
- Federation via Git (follow repos like RSS)
"""

from flask import Blueprint, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import json

cringe_feed_bp = Blueprint('cringe_feed', __name__)


def get_db():
    """Get database connection"""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    return db


@cringe_feed_bp.route('/feed')
def cringe_feed():
    """
    Vertical scrolling feed of CringeProof content

    Like TikTok:
    - Vertical scroll (1080x1920)
    - Auto-play voice
    - Vote buttons
    - Skip to next

    Unlike TikTok:
    - No video files (rendered real-time)
    - Decentralized (Git repos)
    - Transparent algorithm (wordmaps)
    """
    return render_template('cringe_feed.html')


@cringe_feed_bp.route('/api/feed/items')
def get_feed_items():
    """
    Get feed items for user

    Query params:
      - offset: Start index (for infinite scroll)
      - limit: Number of items (default 10)
      - user_id: For personalized recommendations (optional)

    Response:
      {
        "items": [
          {
            "id": 42,
            "recording_id": 7,
            "article": {...},
            "prediction": "GPT-5 is vaporware",
            "audio_url": "/voice_recordings/...",
            "cringeproof_score": 0.0,
            "votes_cringe": 0,
            "votes_based": 0,
            "time_locked_until": null,
            "unlocked": true
          }
        ],
        "has_more": true
      }
    """
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))
    user_id = request.args.get('user_id')  # For personalized feed

    db = get_db()

    # Get unlocked pairings (time-lock expired)
    # TODO: Add personalization based on user_id
    query = """
        SELECT
            p.id,
            p.recording_id,
            p.article_id,
            p.user_prediction,
            p.time_lock_until,
            p.cringe_factor as cringeproof_score,
            r.filename as audio_url,
            r.transcription,
            r.created_at as recorded_at,
            a.title as article_title,
            a.url as article_url,
            a.source as article_source,
            a.summary as article_summary,
            a.topics as article_topics,
            (SELECT COUNT(*) FROM cringe_votes WHERE pairing_id = p.id AND vote_type = 'cringe') as votes_cringe,
            (SELECT COUNT(*) FROM cringe_votes WHERE pairing_id = p.id AND vote_type = 'based') as votes_based
        FROM voice_article_pairings p
        JOIN simple_voice_recordings r ON p.recording_id = r.id
        LEFT JOIN news_articles a ON p.article_id = a.id
        WHERE p.time_lock_until IS NULL OR p.time_lock_until < datetime('now')
        ORDER BY p.paired_at DESC
        LIMIT ? OFFSET ?
    """

    items = db.execute(query, (limit, offset)).fetchall()

    # Check if there are more items
    count_query = """
        SELECT COUNT(*) as total
        FROM voice_article_pairings p
        WHERE p.time_lock_until IS NULL OR p.time_lock_until < datetime('now')
    """
    total = db.execute(count_query).fetchone()['total']
    has_more = (offset + limit) < total

    # Format for JSON
    feed_items = []
    for item in items:
        feed_items.append({
            'id': item['id'],
            'recording_id': item['recording_id'],
            'article': {
                'id': item['article_id'],
                'title': item['article_title'],
                'url': item['article_url'],
                'source': item['article_source'],
                'summary': item['article_summary'],
                'topics': item['article_topics']
            },
            'prediction': item['user_prediction'],
            'audio_url': item['audio_url'],
            'transcription': item['transcription'],
            'recorded_at': item['recorded_at'],
            'cringeproof_score': item['cringeproof_score'] or 0.0,
            'votes_cringe': item['votes_cringe'],
            'votes_based': item['votes_based'],
            'time_locked_until': item['time_lock_until'],
            'unlocked': True  # Already filtered by WHERE clause
        })

    db.close()

    return jsonify({
        'items': feed_items,
        'has_more': has_more,
        'offset': offset,
        'limit': limit
    })


@cringe_feed_bp.route('/api/feed/vote', methods=['POST'])
def vote_on_item():
    """
    Vote on a CringeProof item

    Request:
      {
        "pairing_id": 42,
        "vote_type": "cringe|based",
        "user_id": "optional"
      }

    Response:
      {
        "success": true,
        "new_score": 0.23,
        "votes_cringe": 5,
        "votes_based": 17
      }
    """
    data = request.json
    pairing_id = data.get('pairing_id')
    vote_type = data.get('vote_type')  # 'cringe' or 'based'
    user_id = data.get('user_id', 'anonymous')

    if not pairing_id or vote_type not in ['cringe', 'based']:
        return jsonify({'success': False, 'error': 'Invalid vote'}), 400

    db = get_db()

    # Record vote
    db.execute("""
        INSERT OR REPLACE INTO cringe_votes (pairing_id, user_id, vote_type, voted_at)
        VALUES (?, ?, ?, datetime('now'))
    """, (pairing_id, user_id, vote_type))

    # Update CringeProof score
    votes = db.execute("""
        SELECT
            SUM(CASE WHEN vote_type = 'cringe' THEN 1 ELSE 0 END) as cringe,
            SUM(CASE WHEN vote_type = 'based' THEN 1 ELSE 0 END) as based
        FROM cringe_votes
        WHERE pairing_id = ?
    """, (pairing_id,)).fetchone()

    cringe_count = votes['cringe']
    based_count = votes['based']
    total = cringe_count + based_count

    # Score: 0.0 = all based, 1.0 = all cringe
    cringeproof_score = cringe_count / total if total > 0 else 0.0

    db.execute("""
        UPDATE voice_article_pairings
        SET cringe_factor = ?
        WHERE id = ?
    """, (cringeproof_score, pairing_id))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'new_score': cringeproof_score,
        'votes_cringe': cringe_count,
        'votes_based': based_count
    })


@cringe_feed_bp.route('/api/feed/render/<int:pairing_id>')
def render_feed_item(pairing_id):
    """
    Render a feed item as pixel-composed "video"

    Returns JSON with layer data for client-side rendering:
      {
        "layers": [
          {"type": "gradient", "colors": ["#667eea", "#764ba2"]},
          {"type": "text", "content": "Article Title", "y": 300},
          {"type": "waveform", "audio_url": "...", "y": 600},
          {"type": "prediction", "text": "...", "y": 1200},
          {"type": "score_badge", "score": 0.23, "x": 50, "y": 50},
          {"type": "crt_filter", "mode": "rainbow"}
        ],
        "duration": 45.2
      }
    """
    db = get_db()

    item = db.execute("""
        SELECT
            p.*,
            r.filename as audio_url,
            r.transcription,
            a.title as article_title,
            a.topics as article_topics,
            p.user_prediction
        FROM voice_article_pairings p
        JOIN simple_voice_recordings r ON p.recording_id = r.id
        LEFT JOIN news_articles a ON p.article_id = a.id
        WHERE p.id = ?
    """, (pairing_id,)).fetchone()

    db.close()

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Determine background color from topic
    topic_colors = {
        'ai': ['#667eea', '#764ba2'],
        'crypto': ['#f093fb', '#f5576c'],
        'tech': ['#4facfe', '#00f2fe'],
        'default': ['#43e97b', '#38f9d7']
    }

    topic = item['article_topics'] or 'default'
    colors = topic_colors.get(topic, topic_colors['default'])

    # Build layer stack for rendering
    layers = [
        {
            'type': 'gradient',
            'colors': colors,
            'width': 1080,
            'height': 1920
        },
        {
            'type': 'text',
            'content': item['article_title'],
            'y': 300,
            'font_size': 48,
            'font_weight': 'bold',
            'color': '#ffffff',
            'shadow': True
        },
        {
            'type': 'waveform',
            'audio_url': item['audio_url'],
            'y': 600,
            'height': 200,
            'color': '#00ff00'
        },
        {
            'type': 'prediction',
            'text': item['user_prediction'],
            'y': 1200,
            'font_size': 32,
            'color': '#ffffff',
            'max_width': 900
        },
        {
            'type': 'score_badge',
            'score': item['cringe_factor'] or 0.0,
            'x': 50,
            'y': 50,
            'size': 100
        },
        {
            'type': 'crt_filter',
            'mode': 'rainbow',
            'scanlines': True
        }
    ]

    # Estimate duration from audio (TODO: get actual duration)
    duration = 45.0  # Default 45 seconds

    return jsonify({
        'layers': layers,
        'duration': duration,
        'audio_url': item['audio_url']
    })


@cringe_feed_bp.route('/api/feed/recommend')
def get_recommendations():
    """
    Get recommended items based on user's voting history

    Algorithm:
    - If user voted "cringe", show "based" content in same topic
    - If user voted "based", show "cringe" content in opposite topic
    - Use wordmap clustering for similarity

    Query params:
      - user_id: User ID
      - limit: Number of recommendations (default 5)

    Response:
      {
        "recommendations": [...]
      }
    """
    user_id = request.args.get('user_id', 'anonymous')
    limit = int(request.args.get('limit', 5))

    db = get_db()

    # Get user's last vote
    last_vote = db.execute("""
        SELECT cv.vote_type, a.topics
        FROM cringe_votes cv
        JOIN voice_article_pairings p ON cv.pairing_id = p.id
        LEFT JOIN news_articles a ON p.article_id = a.id
        WHERE cv.user_id = ?
        ORDER BY cv.voted_at DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    if not last_vote:
        # No voting history - return popular items
        items = db.execute("""
            SELECT p.id, p.cringe_factor as cringeproof_score,
                   COUNT(cv.id) as vote_count
            FROM voice_article_pairings p
            LEFT JOIN cringe_votes cv ON p.id = cv.pairing_id
            WHERE p.time_lock_until IS NULL OR p.time_lock_until < datetime('now')
            GROUP BY p.id
            ORDER BY vote_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
    else:
        # Recommend opposite of what they voted
        if last_vote['vote_type'] == 'cringe':
            # Show "based" content (low score)
            score_filter = '< 0.3'
        else:
            # Show "cringe" content (high score)
            score_filter = '> 0.7'

        topic = last_vote['topics']

        items = db.execute(f"""
            SELECT p.id, p.cringe_factor as cringeproof_score
            FROM voice_article_pairings p
            LEFT JOIN news_articles a ON p.article_id = a.id
            WHERE p.time_lock_until IS NULL OR p.time_lock_until < datetime('now')
              AND p.cringe_factor {score_filter}
              AND a.topics = ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (topic, limit)).fetchall()

    db.close()

    recommendations = [{'id': item['id'], 'score': item['cringeproof_score']} for item in items]

    return jsonify({'recommendations': recommendations})


def register_cringe_feed_routes(app):
    """Register CringeProof feed routes"""
    app.register_blueprint(cringe_feed_bp)
    print('🎬 CringeProof Feed routes registered')
    print('   Feed: /feed')
    print('   API: /api/feed/items')
    print('   API: /api/feed/vote')
    print('   API: /api/feed/render/<id>')


# Testing
if __name__ == '__main__':
    print('🎬 CringeProof Feed - Decentralized TikTok')
    print('Routes:')
    print('  /feed - Vertical scrolling feed')
    print('  /api/feed/items - Get feed items')
    print('  /api/feed/vote - Vote on item')
    print('  /api/feed/render/<id> - Get layer data for rendering')

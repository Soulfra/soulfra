#!/usr/bin/env python3
"""
Suggestion Box Routes - Voice-First Community Input

Flask routes for voice suggestion box:
- Submit voice suggestions (no forms, just 30 sec audio)
- View suggestions by brand facet
- Voice responses to suggestions
- SHA256 chain verification

URL Structure:
    /suggestion-box - Main interface
    /@brand/suggestions - Brand-specific view
    /api/suggest-voice - Submit voice suggestion
    /api/respond-voice/<id> - Voice response to suggestion

Like: Old office suggestion box meets voice recording meets @brand routing
"""

from flask import Blueprint, render_template, request, jsonify, session, g, abort
from database import get_db
from voice_suggestion_box import VoiceSuggestionBox, SUGGESTION_BOX_SCHEMA
from datetime import datetime
import json

suggestion_box_bp = Blueprint('suggestion_box', __name__)


# ==============================================================================
# PAGE ROUTES
# ==============================================================================

@suggestion_box_bp.route('/suggestion-box')
def suggestion_box_page():
    """
    Main suggestion box interface

    Shows:
    - Voice recorder (30 sec max)
    - Recent suggestions
    - Community responses
    - SHA256 verification
    """
    user_id = session.get('user_id', 1)
    brand_slug = g.get('brand', {}).get('slug', 'soulfra')

    # Get recent suggestions for this brand
    box = VoiceSuggestionBox(user_id=user_id)
    suggestions = box.get_brand_suggestions(brand_slug, limit=20)

    return render_template(
        'suggestion_box.html',
        suggestions=suggestions,
        brand_slug=brand_slug,
        user_id=user_id
    )


@suggestion_box_bp.route('/@<brand_slug>/suggestions')
def brand_suggestions(brand_slug):
    """
    Brand-specific suggestions view

    Same suggestions, different themed presentation
    (the "facet" concept)

    Args:
        brand_slug: Brand to view suggestions for
    """
    user_id = session.get('user_id', 1)

    # Get suggestions for this brand facet
    box = VoiceSuggestionBox(user_id=user_id)
    suggestions = box.get_brand_suggestions(brand_slug, limit=50)

    # Get brand info for theming
    db = get_db()
    brand = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    if not brand:
        return "Brand not found", 404

    return render_template(
        'brand_suggestions.html',
        suggestions=suggestions,
        brand=brand,
        brand_slug=brand_slug,
        user_id=user_id
    )


@suggestion_box_bp.route('/suggestion/<int:suggestion_id>')
def suggestion_thread(suggestion_id):
    """
    View suggestion thread (original + responses)

    Shows:
    - Original voice suggestion
    - All voice responses
    - SHA256 chain verification
    - Brand facets that can see this
    """
    user_id = session.get('user_id', 1)

    box = VoiceSuggestionBox(user_id=user_id)
    thread = box.get_suggestion_with_responses(suggestion_id)

    if 'error' in thread:
        return thread['error'], 404

    return render_template(
        'suggestion_thread.html',
        thread=thread,
        suggestion_id=suggestion_id,
        user_id=user_id
    )


# ==============================================================================
# API ROUTES
# ==============================================================================

@suggestion_box_bp.route('/api/suggest-voice', methods=['POST'])
def submit_voice_suggestion():
    """
    Submit voice suggestion (no forms, just audio)

    Request:
        - audio: WebM file (30 sec max)
        - brand_slug: Optional brand context
        - category: Optional category

    Response:
        {
            'success': true,
            'suggestion_id': 123,
            'ideas': [...],
            'sha256_hash': '...',
            'brand_facets': ['soulfra', 'deathtodata']
        }

    Flow:
    1. Save audio
    2. Transcribe with Whisper
    3. Extract ideas with AI
    4. Generate SHA256 signature
    5. Return results (no horrendous questionnaires!)
    """
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'success': False, 'error': 'Empty audio'}), 400

    user_id = session.get('user_id', 1)
    brand_slug = request.form.get('brand_slug')
    category = request.form.get('category', 'general')

    # Submit suggestion
    box = VoiceSuggestionBox(user_id=user_id)

    result = box.submit_voice_suggestion(
        audio_data=audio_data,
        user_id=user_id,
        brand_slug=brand_slug,
        category=category
    )

    if 'error' in result:
        return jsonify({'success': False, 'error': result['error']}), 400

    return jsonify({
        'success': True,
        'suggestion_id': result['suggestion_id'],
        'ideas': result['ideas'],
        'transcription': result['transcription'],
        'sha256_hash': result['sha256_hash'],
        'brand_facets': result['brand_facets']
    })


@suggestion_box_bp.route('/api/respond-voice/<int:suggestion_id>', methods=['POST'])
def submit_voice_response(suggestion_id):
    """
    Submit voice response to suggestion

    Request:
        - audio: WebM file (30 sec max)

    Response:
        {
            'success': true,
            'response_id': 456,
            'ideas': [...],
            'original_hash': '...',
            'response_hash': '...',
            'chain_hash': '...',
            'chain_verified': true
        }

    Flow:
    1. Save response audio
    2. Transcribe
    3. Extract response ideas
    4. Create SHA256 chain (response → original)
    5. Verify chain integrity
    """
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'success': False, 'error': 'Empty audio'}), 400

    user_id = session.get('user_id', 1)

    # Submit response
    box = VoiceSuggestionBox(user_id=user_id)

    result = box.submit_voice_response(
        suggestion_id=suggestion_id,
        audio_data=audio_data,
        user_id=user_id
    )

    if 'error' in result:
        return jsonify({'success': False, 'error': result['error']}), 400

    return jsonify({
        'success': True,
        'response_id': result['response_id'],
        'ideas': result['ideas'],
        'original_hash': result['original_hash'],
        'response_hash': result['response_hash'],
        'chain_hash': result['chain_hash'],
        'chain_verified': result['chain_verified']
    })


@suggestion_box_bp.route('/api/suggestions/<brand_slug>')
def get_brand_suggestions_api(brand_slug):
    """
    Get suggestions for brand facet (API)

    Query params:
        - status: living/dead
        - limit: Max results

    Response:
        {
            'success': true,
            'brand_slug': 'soulfra',
            'suggestions': [...]
        }
    """
    status = request.args.get('status', 'living')
    limit = int(request.args.get('limit', 50))

    user_id = session.get('user_id', 1)

    box = VoiceSuggestionBox(user_id=user_id)
    suggestions = box.get_brand_suggestions(brand_slug, status=status, limit=limit)

    return jsonify({
        'success': True,
        'brand_slug': brand_slug,
        'suggestions': suggestions,
        'count': len(suggestions)
    })


@suggestion_box_bp.route('/api/suggestion/<int:suggestion_id>/thread')
def get_suggestion_thread_api(suggestion_id):
    """
    Get suggestion thread (original + responses) (API)

    Response:
        {
            'success': true,
            'original': {...},
            'responses': [...],
            'chain_verified': true
        }
    """
    user_id = session.get('user_id', 1)

    box = VoiceSuggestionBox(user_id=user_id)
    thread = box.get_suggestion_with_responses(suggestion_id)

    if 'error' in thread:
        return jsonify({'success': False, 'error': thread['error']}), 404

    return jsonify({
        'success': True,
        'original': thread['original'],
        'responses': thread['responses'],
        'chain_verified': thread['chain_verified']
    })


@suggestion_box_bp.route('/api/suggestion/<int:suggestion_id>/verify-chain')
def verify_suggestion_chain(suggestion_id):
    """
    Verify SHA256 chain for suggestion thread

    Returns:
        {
            'success': true,
            'suggestion_id': 123,
            'chain_verified': true,
            'original_hash': '...',
            'response_hashes': [...],
            'chain_hashes': [...]
        }
    """
    user_id = session.get('user_id', 1)

    box = VoiceSuggestionBox(user_id=user_id)
    thread = box.get_suggestion_with_responses(suggestion_id)

    if 'error' in thread:
        return jsonify({'success': False, 'error': thread['error']}), 404

    return jsonify({
        'success': True,
        'suggestion_id': suggestion_id,
        'chain_verified': thread['chain_verified'],
        'original_hash': thread['original']['sha256_hash'],
        'response_hashes': [r['sha256_hash'] for r in thread['responses']],
        'chain_hashes': [r['chain_hash'] for r in thread['responses']]
    })


# ==============================================================================
# ADMIN ROUTES
# ==============================================================================

@suggestion_box_bp.route('/api/admin/setup-suggestion-box', methods=['POST'])
def setup_suggestion_box_database():
    """
    Setup suggestion box database schema

    Admin only - creates tables if they don't exist
    """
    # Check if user is admin (simple check for now)
    user_id = session.get('user_id')

    if user_id != 1:
        return jsonify({'success': False, 'error': 'Admin only'}), 403

    try:
        db = get_db()
        db.executescript(SUGGESTION_BOX_SCHEMA)
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Suggestion box database schema created'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@suggestion_box_bp.route('/api/vote/<int:suggestion_id>', methods=['POST'])
def vote_on_suggestion(suggestion_id):
    """
    Vote on a suggestion (CringeProof voting)

    Request:
        {
            'vote_type': 'upvote' | 'downvote' | 'cringe' | 'authentic'
        }

    Response:
        {
            'success': true,
            'votes': {
                'upvotes': 10,
                'downvotes': 2,
                'cringe_votes': 1,
                'authentic_votes': 15,
                'cringeproof_score': 85.2
            }
        }
    """
    user_id = session.get('user_id', 1)

    data = request.get_json()
    vote_type = data.get('vote_type')

    if vote_type not in ['upvote', 'downvote', 'cringe', 'authentic']:
        return jsonify({'success': False, 'error': 'Invalid vote type'}), 400

    db = get_db()

    # Check if user already voted
    existing_vote = db.execute('''
        SELECT vote_type FROM suggestion_votes
        WHERE suggestion_id = ? AND user_id = ?
    ''', (suggestion_id, user_id)).fetchone()

    if existing_vote:
        # Update existing vote
        db.execute('''
            UPDATE suggestion_votes
            SET vote_type = ?, created_at = datetime('now')
            WHERE suggestion_id = ? AND user_id = ?
        ''', (vote_type, suggestion_id, user_id))
    else:
        # Insert new vote
        db.execute('''
            INSERT INTO suggestion_votes (suggestion_id, user_id, vote_type)
            VALUES (?, ?, ?)
        ''', (suggestion_id, user_id, vote_type))

    db.commit()

    # Calculate CringeProof score
    votes = calculate_cringeproof_score(suggestion_id)

    return jsonify({
        'success': True,
        'votes': votes
    })


@suggestion_box_bp.route('/api/votes/<int:suggestion_id>')
def get_suggestion_votes(suggestion_id):
    """
    Get vote counts for a suggestion

    Response:
        {
            'success': true,
            'votes': {...},
            'user_vote': 'upvote' | null
        }
    """
    user_id = session.get('user_id', 1)

    votes = calculate_cringeproof_score(suggestion_id)

    # Check user's vote
    db = get_db()
    user_vote = db.execute('''
        SELECT vote_type FROM suggestion_votes
        WHERE suggestion_id = ? AND user_id = ?
    ''', (suggestion_id, user_id)).fetchone()

    return jsonify({
        'success': True,
        'votes': votes,
        'user_vote': user_vote['vote_type'] if user_vote else None
    })


def calculate_cringeproof_score(suggestion_id):
    """
    Calculate CringeProof score for a suggestion

    Formula:
    - Authentic votes add to score
    - Cringe votes subtract from score
    - Upvotes add slightly
    - Downvotes subtract slightly
    - Base score: 50
    - Range: 0-100

    Returns:
        {
            'upvotes': int,
            'downvotes': int,
            'cringe_votes': int,
            'authentic_votes': int,
            'cringeproof_score': float
        }
    """
    db = get_db()

    # Get vote counts
    upvotes = db.execute('''
        SELECT COUNT(*) as count FROM suggestion_votes
        WHERE suggestion_id = ? AND vote_type = 'upvote'
    ''', (suggestion_id,)).fetchone()['count']

    downvotes = db.execute('''
        SELECT COUNT(*) as count FROM suggestion_votes
        WHERE suggestion_id = ? AND vote_type = 'downvote'
    ''', (suggestion_id,)).fetchone()['count']

    cringe_votes = db.execute('''
        SELECT COUNT(*) as count FROM suggestion_votes
        WHERE suggestion_id = ? AND vote_type = 'cringe'
    ''', (suggestion_id,)).fetchone()['count']

    authentic_votes = db.execute('''
        SELECT COUNT(*) as count FROM suggestion_votes
        WHERE suggestion_id = ? AND vote_type = 'authentic'
    ''', (suggestion_id,)).fetchone()['count']

    # Calculate CringeProof score
    # Base: 50
    # Authentic: +10 each
    # Cringe: -15 each
    # Upvote: +2 each
    # Downvote: -2 each
    score = 50.0
    score += authentic_votes * 10
    score -= cringe_votes * 15
    score += upvotes * 2
    score -= downvotes * 2

    # Clamp to 0-100
    score = max(0, min(100, score))

    # Update cringeproof_scores table
    db.execute('''
        INSERT OR REPLACE INTO cringeproof_scores
        (suggestion_id, upvotes, downvotes, cringe_votes, authentic_votes, cringeproof_score, last_calculated)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (suggestion_id, upvotes, downvotes, cringe_votes, authentic_votes, score))

    db.commit()

    return {
        'upvotes': upvotes,
        'downvotes': downvotes,
        'cringe_votes': cringe_votes,
        'authentic_votes': authentic_votes,
        'cringeproof_score': score
    }


@suggestion_box_bp.route('/api/admin/suggestion-stats')
def suggestion_box_stats():
    """
    Get suggestion box statistics

    Returns:
        {
            'total_suggestions': 123,
            'total_responses': 456,
            'living_suggestions': 100,
            'dead_suggestions': 23,
            'suggestions_by_brand': {...}
        }
    """
    user_id = session.get('user_id')

    if user_id != 1:
        return jsonify({'success': False, 'error': 'Admin only'}), 403

    db = get_db()

    # Total suggestions
    total = db.execute('SELECT COUNT(*) as count FROM voice_suggestions').fetchone()

    # Total responses
    responses = db.execute('SELECT COUNT(*) as count FROM voice_suggestion_responses').fetchone()

    # By status
    living = db.execute(
        "SELECT COUNT(*) as count FROM voice_suggestions WHERE status = 'living'"
    ).fetchone()

    dead = db.execute(
        "SELECT COUNT(*) as count FROM voice_suggestions WHERE status = 'dead'"
    ).fetchone()

    # By brand
    by_brand = db.execute('''
        SELECT brand_slug, COUNT(*) as count
        FROM voice_suggestions
        GROUP BY brand_slug
    ''').fetchall()

    brands = {row['brand_slug']: row['count'] for row in by_brand}

    return jsonify({
        'success': True,
        'total_suggestions': total['count'] if total else 0,
        'total_responses': responses['count'] if responses else 0,
        'living_suggestions': living['count'] if living else 0,
        'dead_suggestions': dead['count'] if dead else 0,
        'suggestions_by_brand': brands
    })


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def init_suggestion_box(app):
    """
    Initialize suggestion box system

    Call this from app.py:
        from suggestion_box_routes import init_suggestion_box
        init_suggestion_box(app)
    """
    app.register_blueprint(suggestion_box_bp)

    # Setup database on first run
    with app.app_context():
        try:
            db = get_db()
            db.executescript(SUGGESTION_BOX_SCHEMA)
            db.commit()
            print("✅ Suggestion box database initialized")
        except Exception as e:
            print(f"⚠️  Suggestion box database error: {e}")

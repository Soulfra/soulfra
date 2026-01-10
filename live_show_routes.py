"""
Live Show Routes - Flask API for call-in show system

Endpoints for creating shows, submitting call-ins, managing queue, pairing sponsors
"""

from flask import Blueprint, request, jsonify, render_template, session
from live_call_in_show import LiveCallInShow
from database import get_db
import json

live_show_bp = Blueprint('live_show', __name__)


@live_show_bp.route('/live-show-host/<int:show_id>')
def host_dashboard(show_id):
    """Host dashboard for managing live show"""
    return render_template('live_show_host.html', show_id=show_id)


@live_show_bp.route('/call-in/<int:show_id>')
def call_in_page(show_id):
    """Public page for calling into show"""
    db = get_db()
    show = db.execute('''
        SELECT title, article_text, article_url, article_source, status
        FROM live_shows
        WHERE id = ?
    ''', (show_id,)).fetchone()

    if not show:
        return "Show not found", 404

    return render_template('call_in.html',
                         show_id=show_id,
                         show=dict(show))


@live_show_bp.route('/api/live-show/create', methods=['POST'])
def create_show():
    """
    Create new live show

    Request:
        {
            "title": "AI Regulation News",
            "article_text": "Full article text...",
            "article_url": "https://...",
            "article_source": "NY Times"
        }

    Response:
        {
            "success": true,
            "show_id": 1,
            "call_in_url": "http://192.168.1.87:5001/call-in/1",
            "host_dashboard": "http://192.168.1.87:5001/live-show-host/1"
        }
    """
    data = request.get_json()

    if not data.get('title') or not data.get('article_text'):
        return jsonify({'error': 'Title and article_text required'}), 400

    host_user_id = session.get('user_id', 1)  # Default to user 1 if not logged in

    show_system = LiveCallInShow()
    result = show_system.create_show(
        title=data['title'],
        article_text=data['article_text'],
        host_user_id=host_user_id,
        article_url=data.get('article_url'),
        article_source=data.get('article_source')
    )

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/<int:show_id>/call-in', methods=['POST'])
def submit_call_in(show_id):
    """
    Submit voice call-in to show

    Request:
        {
            "recording_id": 42,
            "caller_name": "John from Tampa",
            "reaction_type": "comment"
        }

    Response:
        {
            "success": true,
            "reaction_id": 5,
            "status": "pending"
        }
    """
    data = request.get_json()

    if not data.get('recording_id'):
        return jsonify({'error': 'recording_id required'}), 400

    user_id = session.get('user_id')

    show_system = LiveCallInShow()
    result = show_system.submit_call_in(
        show_id=show_id,
        recording_id=data['recording_id'],
        caller_name=data.get('caller_name'),
        user_id=user_id,
        reaction_type=data.get('reaction_type', 'comment')
    )

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/<int:show_id>/queue', methods=['GET'])
def get_queue(show_id):
    """
    Get call-in queue for show

    Query params:
        ?status=pending (optional)

    Response:
        {
            "show_id": 1,
            "reactions": [
                {
                    "id": 5,
                    "caller_name": "John from Tampa",
                    "transcription": "...",
                    "approval_status": "pending",
                    "sponsor_name": null
                }
            ]
        }
    """
    status = request.args.get('status')

    show_system = LiveCallInShow()
    reactions = show_system.get_show_queue(show_id, status)

    return jsonify({
        'show_id': show_id,
        'reactions': reactions
    })


@live_show_bp.route('/api/live-show/reaction/<int:reaction_id>/approve', methods=['POST'])
def approve_reaction(reaction_id):
    """
    Approve call-in reaction

    Request:
        {
            "timestamp_in_show": 120  // Optional: seconds into show
        }

    Response:
        {
            "success": true,
            "reaction_id": 5,
            "status": "approved"
        }
    """
    data = request.get_json() or {}
    approved_by = session.get('user_id', 1)

    show_system = LiveCallInShow()
    result = show_system.approve_reaction(
        reaction_id=reaction_id,
        approved_by=approved_by,
        timestamp_in_show=data.get('timestamp_in_show')
    )

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/reaction/<int:reaction_id>/reject', methods=['POST'])
def reject_reaction(reaction_id):
    """Reject call-in reaction"""
    db = get_db()
    db.execute('''
        UPDATE show_reactions
        SET approval_status = 'rejected'
        WHERE id = ?
    ''', (reaction_id,))
    db.commit()

    return jsonify({
        'success': True,
        'reaction_id': reaction_id,
        'status': 'rejected'
    })


@live_show_bp.route('/api/live-show/<int:show_id>/sponsor', methods=['POST'])
def add_sponsor(show_id):
    """
    Add sponsor to show

    Request:
        {
            "sponsor_name": "PrivacyTools.io",
            "sponsor_type": "affiliate",
            "sponsor_url": "https://privacytools.io",
            "ad_script": "Check out PrivacyTools for...",
            "keywords": ["privacy", "security", "encryption"]
        }

    Response:
        {
            "success": true,
            "sponsor_id": 2,
            "sponsor_name": "PrivacyTools.io"
        }
    """
    data = request.get_json()

    if not data.get('sponsor_name'):
        return jsonify({'error': 'sponsor_name required'}), 400

    show_system = LiveCallInShow()
    result = show_system.add_sponsor(
        show_id=show_id,
        sponsor_name=data['sponsor_name'],
        sponsor_type=data.get('sponsor_type', 'product'),
        sponsor_url=data.get('sponsor_url'),
        ad_script=data.get('ad_script'),
        keywords=data.get('keywords')
    )

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/reaction/<int:reaction_id>/pair-sponsor', methods=['POST'])
def pair_sponsor(reaction_id):
    """
    Pair reaction with sponsor

    Request:
        {
            "sponsor_id": 2,
            "placement_style": "before"  // before, after, split
        }

    Response:
        {
            "success": true,
            "pairing_score": 75.0,
            "pairing_reason": "Matched 3 keywords"
        }
    """
    data = request.get_json()

    if not data.get('sponsor_id'):
        return jsonify({'error': 'sponsor_id required'}), 400

    show_system = LiveCallInShow()
    result = show_system.pair_reaction_with_sponsor(
        reaction_id=reaction_id,
        sponsor_id=data['sponsor_id'],
        placement_style=data.get('placement_style', 'before')
    )

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/<int:show_id>/auto-pair', methods=['POST'])
def auto_pair_sponsors(show_id):
    """
    Auto-pair all approved reactions with sponsors using keyword matching

    Response:
        {
            "success": true,
            "pairings_created": 5,
            "pairings": [...]
        }
    """
    show_system = LiveCallInShow()
    pairings = show_system.auto_pair_sponsors(show_id)

    return jsonify({
        'success': True,
        'pairings_created': len(pairings),
        'pairings': pairings
    })


@live_show_bp.route('/api/live-show/<int:show_id>/bookend', methods=['POST'])
def generate_bookend(show_id):
    """
    Generate intro or outro bookend

    Request:
        {
            "type": "intro"  // intro or outro
        }

    Response:
        {
            "success": true,
            "bookend_id": 1,
            "type": "intro",
            "script": "Welcome to the show...",
            "sponsors": ["PrivacyTools.io", "VPN Provider"]
        }
    """
    data = request.get_json()
    bookend_type = data.get('type', 'intro')

    if bookend_type not in ['intro', 'outro']:
        return jsonify({'error': 'type must be intro or outro'}), 400

    show_system = LiveCallInShow()
    result = show_system.generate_bookend(show_id, bookend_type)

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/<int:show_id>/export', methods=['GET'])
def export_show(show_id):
    """
    Export complete show data

    Response:
        {
            "show_id": 1,
            "title": "AI Regulation News",
            "article": {...},
            "intro": {...},
            "reactions": [...],
            "outro": {...},
            "stats": {...}
        }
    """
    show_system = LiveCallInShow()
    show = show_system.export_show(show_id)

    return jsonify(show)


@live_show_bp.route('/api/live-show/<int:show_id>/close', methods=['POST'])
def close_show(show_id):
    """Close show to new call-ins"""
    show_system = LiveCallInShow()
    result = show_system.close_show(show_id)

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/<int:show_id>/publish', methods=['POST'])
def publish_show(show_id):
    """Publish show (mark as aired)"""
    show_system = LiveCallInShow()
    result = show_system.publish_show(show_id)

    return jsonify({
        'success': True,
        **result
    })


@live_show_bp.route('/api/live-show/<int:show_id>/info', methods=['GET'])
def get_show_info(show_id):
    """Get show metadata"""
    db = get_db()
    show = db.execute('''
        SELECT * FROM live_shows WHERE id = ?
    ''', (show_id,)).fetchone()

    if not show:
        return jsonify({'error': 'Show not found'}), 404

    # Get sponsors
    sponsors = db.execute('''
        SELECT * FROM show_sponsors WHERE show_id = ?
    ''', (show_id,)).fetchall()

    return jsonify({
        'show': dict(show),
        'sponsors': [dict(s) for s in sponsors]
    })

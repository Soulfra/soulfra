"""
Ollama Connector Routes - Flask API for multi-Ollama integration

Endpoints for users to connect their local Ollama instances to your show server
"""

from flask import Blueprint, request, jsonify
from database import get_db
import json
import secrets
from datetime import datetime

ollama_connector_bp = Blueprint('ollama_connector', __name__)

# In-memory session storage (could be moved to database)
ollama_sessions = {}


@ollama_connector_bp.route('/api/ollama/connect', methods=['POST'])
def connect_ollama():
    """
    Connect user's local Ollama to show server

    Request:
        {
            "model": "llama3",
            "ollama_url": "http://localhost:11434"
        }

    Response:
        {
            "success": true,
            "session_id": "abc123...",
            "message": "Connected successfully"
        }
    """
    data = request.get_json()

    model = data.get('model', 'llama3')
    ollama_url = data.get('ollama_url', 'http://localhost:11434')

    # Generate session ID
    session_id = secrets.token_urlsafe(16)

    # Store session
    ollama_sessions[session_id] = {
        'model': model,
        'ollama_url': ollama_url,
        'connected_at': datetime.now().isoformat(),
        'last_check': None
    }

    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': f'Connected with model: {model}'
    })


@ollama_connector_bp.route('/api/ollama/check-new', methods=['GET'])
def check_new_content():
    """
    Check for new content (voice-ins, emails, subscriptions)

    Query params:
        ?session_id=abc123

    Response:
        {
            "new_voice_reactions": 5,
            "new_email_subscriptions": 2,
            "new_sponsor_updates": 1,
            "active_shows": 1
        }
    """
    session_id = request.args.get('session_id')

    if not session_id or session_id not in ollama_sessions:
        return jsonify({'error': 'Invalid session'}), 401

    # Update last check time
    ollama_sessions[session_id]['last_check'] = datetime.now().isoformat()

    db = get_db()

    # Count new voice reactions (pending)
    voice_reactions = db.execute('''
        SELECT COUNT(*) as count FROM show_reactions
        WHERE approval_status = 'pending'
    ''').fetchone()

    # Count email subscriptions (unread - placeholder)
    email_subscriptions = 0  # TODO: implement email tracking

    # Count sponsor updates (placeholder)
    sponsor_updates = 0

    # Count active shows
    active_shows = db.execute('''
        SELECT COUNT(*) as count FROM live_shows
        WHERE status = 'accepting_calls'
    ''').fetchone()

    return jsonify({
        'new_voice_reactions': voice_reactions['count'] if voice_reactions else 0,
        'new_email_subscriptions': email_subscriptions,
        'new_sponsor_updates': sponsor_updates,
        'active_shows': active_shows['count'] if active_shows else 0
    })


@ollama_connector_bp.route('/api/ollama/shows', methods=['GET'])
def get_shows_for_ollama():
    """
    Get list of shows for Ollama client

    Response:
        {
            "shows": [
                {
                    "id": 1,
                    "title": "AI Regulation Discussion",
                    "status": "accepting_calls",
                    "total_reactions": 10,
                    "approved_reactions": 5
                }
            ]
        }
    """
    db = get_db()

    shows = db.execute('''
        SELECT id, title, status, total_reactions, approved_reactions, created_at
        FROM live_shows
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()

    return jsonify({
        'shows': [dict(s) for s in shows]
    })


@ollama_connector_bp.route('/api/ollama/subscriptions', methods=['GET'])
def get_subscriptions_for_ollama():
    """
    Get email subscriptions

    Query params:
        ?unread=true

    Response:
        {
            "subscriptions": [
                {
                    "id": 1,
                    "email": "user@example.com",
                    "subscribed_at": "2026-01-02 10:00:00"
                }
            ]
        }
    """
    unread_only = request.args.get('unread', 'true').lower() == 'true'

    db = get_db()

    # Get recent subscribers
    subscribers = db.execute('''
        SELECT id, email, created_at as subscribed_at
        FROM subscribers
        ORDER BY created_at DESC
        LIMIT 50
    ''').fetchall()

    return jsonify({
        'subscriptions': [dict(s) for s in subscribers]
    })


@ollama_connector_bp.route('/api/ollama/active', methods=['GET'])
def get_active_shows():
    """
    Get currently active shows accepting call-ins

    Response:
        {
            "shows": [...]
        }
    """
    db = get_db()

    shows = db.execute('''
        SELECT * FROM live_shows
        WHERE status = 'accepting_calls'
        ORDER BY created_at DESC
    ''').fetchall()

    return jsonify({
        'shows': [dict(s) for s in shows]
    })


@ollama_connector_bp.route('/api/ollama/stats', methods=['GET'])
def get_ollama_stats():
    """
    Get system stats for Ollama client dashboard

    Response:
        {
            "total_shows": 10,
            "total_reactions": 100,
            "pending_reactions": 25,
            "active_sessions": 5
        }
    """
    db = get_db()

    total_shows = db.execute('SELECT COUNT(*) as count FROM live_shows').fetchone()
    total_reactions = db.execute('SELECT COUNT(*) as count FROM show_reactions').fetchone()
    pending_reactions = db.execute('''
        SELECT COUNT(*) as count FROM show_reactions WHERE approval_status = 'pending'
    ''').fetchone()

    return jsonify({
        'total_shows': total_shows['count'] if total_shows else 0,
        'total_reactions': total_reactions['count'] if total_reactions else 0,
        'pending_reactions': pending_reactions['count'] if pending_reactions else 0,
        'active_sessions': len(ollama_sessions)
    })


@ollama_connector_bp.route('/api/ollama/disconnect', methods=['POST'])
def disconnect_ollama():
    """
    Disconnect Ollama session

    Request:
        {
            "session_id": "abc123"
        }

    Response:
        {
            "success": true,
            "message": "Disconnected"
        }
    """
    data = request.get_json()
    session_id = data.get('session_id')

    if session_id and session_id in ollama_sessions:
        del ollama_sessions[session_id]

    return jsonify({
        'success': True,
        'message': 'Disconnected'
    })

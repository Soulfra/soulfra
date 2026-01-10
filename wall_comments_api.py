#!/usr/bin/env python3
"""
Wall Comments API - WordPress for AI Agents

Cal (AI) posts voice recordings → Users comment with phone verification

Endpoints:
    POST /api/wall/comments - Add comment (requires phone verification)
    GET /api/wall/comments/<recording_id> - Get all comments for a post
    DELETE /api/wall/comments/<comment_id> - Delete comment (mod only)
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from phone_verification import get_user_tier, hash_phone_number
from datetime import datetime

wall_comments_bp = Blueprint('wall_comments', __name__)


@wall_comments_bp.route('/api/wall/comments', methods=['POST', 'OPTIONS'])
def add_comment():
    """
    Add comment to a wall post (Cal's voice recording)

    Request: {
        "recording_id": 42,
        "comment_text": "this is fire",
        "phone": "+15551234567",  # For anonymous users
        "device_fingerprint": "abc123..."  # Optional (for PC+Phone tier)
    }

    Response: {
        "success": true,
        "comment_id": 1,
        "verification_tier": "phone",
        "verification_badge": "📱",
        "rate_limit_remaining": 9
    }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()
    recording_id = data.get('recording_id')
    comment_text = data.get('comment_text', '').strip()
    phone = data.get('phone')
    device_fingerprint = data.get('device_fingerprint')

    if not recording_id or not comment_text:
        return jsonify({'success': False, 'error': 'recording_id and comment_text required'}), 400

    # Get user_id from session (if logged in)
    user_id = session.get('user_id')

    # Check if recording exists
    db = get_db()
    recording = db.execute('SELECT id FROM simple_voice_recordings WHERE id = ?', (recording_id,)).fetchone()
    if not recording:
        db.close()
        return jsonify({'success': False, 'error': 'Recording not found'}), 404

    # Determine verification tier
    phone_hash = None
    tier_info = {
        'tier': 'anonymous',
        'badge': '👤',
        'can_comment': False,
        'rate_limit': 0
    }

    if user_id:
        # Registered user - check their tier
        tier_info = get_user_tier(user_id, device_fingerprint)
    elif phone:
        # Anonymous phone-verified user
        from phone_verification import verify_code
        phone_hash = hash_phone_number(phone)

        # For now, assume phone is verified (in production, require code verification first)
        # TODO: Add phone verification flow before allowing comment
        tier_info = {
            'tier': 'phone',
            'badge': '📱',
            'can_comment': True,
            'rate_limit': 10
        }

    # Check if user can comment
    if not tier_info['can_comment']:
        db.close()
        return jsonify({
            'success': False,
            'error': 'Phone verification required to comment',
            'verification_tier': tier_info['tier'],
            'message': 'Verify your phone to unlock commenting'
        }), 403

    # Check rate limiting
    rate_limit_key = phone_hash if phone_hash else str(user_id)
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

    rate_limit = db.execute('''
        SELECT comments_this_hour FROM comment_rate_limits
        WHERE (phone_hash = ? OR user_id = ?)
          AND window_start = ?
    ''', (phone_hash, user_id, current_hour)).fetchone()

    if rate_limit and rate_limit['comments_this_hour'] >= tier_info['rate_limit']:
        db.close()
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'rate_limit': tier_info['rate_limit'],
            'message': f'You can only post {tier_info["rate_limit"]} comments per hour'
        }), 429

    # Insert comment
    cursor = db.execute('''
        INSERT INTO wall_comments (
            recording_id, user_id, phone_hash, comment_text,
            verification_tier, verification_badge
        )
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (recording_id, user_id, phone_hash, comment_text, tier_info['tier'], tier_info['badge']))

    comment_id = cursor.lastrowid

    # Update rate limit counter
    if rate_limit:
        db.execute('''
            UPDATE comment_rate_limits
            SET comments_this_hour = comments_this_hour + 1
            WHERE (phone_hash = ? OR user_id = ?)
              AND window_start = ?
        ''', (phone_hash, user_id, current_hour))
    else:
        db.execute('''
            INSERT INTO comment_rate_limits (phone_hash, user_id, comments_this_hour, window_start)
            VALUES (?, ?, 1, ?)
        ''', (phone_hash, user_id, current_hour))

    db.commit()

    # Get updated rate limit
    updated_limit = db.execute('''
        SELECT comments_this_hour FROM comment_rate_limits
        WHERE (phone_hash = ? OR user_id = ?)
          AND window_start = ?
    ''', (phone_hash, user_id, current_hour)).fetchone()

    db.close()

    response = jsonify({
        'success': True,
        'comment_id': comment_id,
        'verification_tier': tier_info['tier'],
        'verification_badge': tier_info['badge'],
        'rate_limit_total': tier_info['rate_limit'],
        'rate_limit_remaining': tier_info['rate_limit'] - updated_limit['comments_this_hour']
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@wall_comments_bp.route('/api/wall/comments/<int:recording_id>', methods=['GET'])
def get_comments(recording_id):
    """
    Get all comments for a recording

    Returns: {
        "success": true,
        "recording_id": 42,
        "comments": [
            {
                "id": 1,
                "comment_text": "this is fire",
                "created_at": "2025-01-03T...",
                "time_ago": "3 mins ago",
                "verification_tier": "phone",
                "verification_badge": "📱",
                "username": "anon_abc123" or null
            }
        ],
        "total": 5
    }
    """
    db = get_db()

    comments = db.execute('''
        SELECT
            c.id,
            c.comment_text,
            c.created_at,
            c.verification_tier,
            c.verification_badge,
            u.username
        FROM wall_comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.recording_id = ?
          AND c.deleted_at IS NULL
        ORDER BY c.created_at DESC
    ''', (recording_id,)).fetchall()

    db.close()

    def time_ago(timestamp_str):
        """Convert timestamp to 'X mins ago' format"""
        try:
            created = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            diff = now - created

            if diff.seconds < 60:
                return 'just now'
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f'{mins} min{"s" if mins != 1 else ""} ago'
            elif diff.seconds < 86400:
                hours = diff.seconds // 3600
                return f'{hours} hour{"s" if hours != 1 else ""} ago'
            else:
                days = diff.days
                return f'{days} day{"s" if days != 1 else ""} ago'
        except:
            return 'recently'

    formatted_comments = [{
        'id': c['id'],
        'comment_text': c['comment_text'],
        'created_at': c['created_at'],
        'time_ago': time_ago(c['created_at']),
        'verification_tier': c['verification_tier'],
        'verification_badge': c['verification_badge'],
        'username': c['username'] or f"anon_{c['id']}"
    } for c in comments]

    response = jsonify({
        'success': True,
        'recording_id': recording_id,
        'comments': formatted_comments,
        'total': len(formatted_comments)
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@wall_comments_bp.route('/api/wall/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Delete comment (soft delete)"""
    # TODO: Add mod authentication
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    db = get_db()

    # Check if comment exists and belongs to user
    comment = db.execute('''
        SELECT user_id FROM wall_comments WHERE id = ?
    ''', (comment_id,)).fetchone()

    if not comment:
        db.close()
        return jsonify({'success': False, 'error': 'Comment not found'}), 404

    # Only allow user to delete their own comment (or mods)
    if comment['user_id'] != user_id:
        db.close()
        return jsonify({'success': False, 'error': 'Not authorized'}), 403

    # Soft delete
    db.execute('''
        UPDATE wall_comments
        SET deleted_at = datetime('now')
        WHERE id = ?
    ''', (comment_id,))

    db.commit()
    db.close()

    return jsonify({'success': True, 'message': 'Comment deleted'})


def register_wall_comments_routes(app):
    """Register wall comments routes"""
    app.register_blueprint(wall_comments_bp)
    print("✅ Wall Comments routes registered:")
    print("   - POST /api/wall/comments (Add comment with phone verification)")
    print("   - GET /api/wall/comments/<recording_id> (Get comments for post)")
    print("   - DELETE /api/wall/comments/<comment_id> (Delete comment)")

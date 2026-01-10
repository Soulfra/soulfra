"""
Public Comments API - No authentication required
For use with static GitHub Pages
"""

from flask import Blueprint, request, jsonify
from database import get_db
from flask_cors import cross_origin

public_comments = Blueprint('public_comments', __name__)


@public_comments.route('/api/comments/<int:post_id>', methods=['GET'])
@cross_origin(origins=['https://soulfra.github.io', 'http://localhost:*'])
def get_comments(post_id):
    """Get all comments for a post (public, no auth required)"""
    db = get_db()

    comments = db.execute('''
        SELECT
            c.id,
            c.content,
            c.created_at,
            c.parent_comment_id,
            u.username as user_name,
            0 as is_ai
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()

    db.close()

    return jsonify([dict(comment) for comment in comments])


@public_comments.route('/api/comments', methods=['POST'])
@cross_origin(origins=['https://soulfra.github.io', 'http://localhost:*'])
def post_comment():
    """Post a comment (public, no auth - uses anonymous user)"""
    data = request.get_json()

    post_id = data.get('post_id')
    content = data.get('content', '').strip()

    if not post_id or not content:
        return jsonify({'error': 'post_id and content required'}), 400

    db = get_db()

    # Use anonymous user (ID 1) for public comments
    # In production, you'd create a captcha or rate limiting here
    cursor = db.execute('''
        INSERT INTO comments (post_id, user_id, content)
        VALUES (?, 1, ?)
    ''', (post_id, content))

    comment_id = cursor.lastrowid
    db.commit()

    # Return the new comment
    comment = db.execute('''
        SELECT
            c.id,
            c.content,
            c.created_at,
            c.parent_comment_id,
            'Anonymous' as user_name,
            0 as is_ai
        FROM comments c
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    db.close()

    return jsonify(dict(comment)), 201

#!/usr/bin/env python3
"""
Generator Routes - Chat Interface for Unified Content Generation

This is the web interface for the unified_generator.py system.

Routes:
- GET /generate - Main chat interface for content generation
- POST /api/generate/hello - Generate hello world in any language
- POST /api/generate/post - Generate custom blog post
- GET /api/generate/library - View all generated content
- GET /api/generate/verify/<hash> - Verify content by hash
- GET /generate/view/<unified_id> - View generated content with all codes
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from unified_generator import UnifiedContentGenerator
from database import get_db
import json

generator_bp = Blueprint('generator', __name__)

# Initialize unified generator
unified_gen = None  # Will be initialized in register function


def register_generator_routes(app):
    """Register generator blueprint with Flask app"""
    global unified_gen

    # Initialize generator
    unified_gen = UnifiedContentGenerator(brand_slug='soulfra')

    # Register blueprint
    app.register_blueprint(generator_bp)
    print("✅ Registered unified generator routes")


# Need to update all route functions to use the global unified_gen


@generator_bp.route('/generate')
def generate_interface():
    """
    Main chat interface for content generation

    Users can ask to:
    - Generate hello worlds in different languages
    - Generate 0-2 blog posts
    - View all generated content
    - Verify content
    """
    user_id = session.get('user_id')

    # Get recent generated content
    recent_content = unified_gen.get_all_content(limit=10)

    return render_template('generate.html',
        user_id=user_id,
        recent_content=recent_content,
        languages=['python', 'javascript', 'rust', 'go', 'java', 'c', 'ruby', 'php']
    )


@generator_bp.route('/api/generate/hello', methods=['POST'])
def generate_hello_world():
    """
    Generate hello world in specified language

    POST body:
    {
        "language": "python"
    }

    Returns:
    {
        "success": true,
        "data": {
            "unified_id": 1,
            "title": "Hello World in Python",
            "code": "print('Hello, World!')",
            "content_hash": "abc123...",
            "upc_code": "123456789012",
            "qr_url": "https://soulfra.com/v/abc123",
            "affiliate_url": "https://soulfra.com/aff/AFF-abc123",
            "verifiable": true
        }
    }
    """
    user_id = session.get('user_id')

    data = request.get_json()
    language = data.get('language', '').strip().lower()

    if not language:
        return jsonify({'success': False, 'error': 'Language required'}), 400

    # Valid languages
    valid_languages = ['python', 'javascript', 'rust', 'go', 'java', 'c', 'ruby', 'php', 'swift', 'kotlin']

    if language not in valid_languages:
        return jsonify({'success': False, 'error': f'Language "{language}" not supported'}), 400

    try:
        # Generate hello world
        result = unified_gen.generate_hello_world(language, user_id=user_id)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"Error generating hello world: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@generator_bp.route('/api/generate/post', methods=['POST'])
def generate_post():
    """
    Generate custom blog post

    POST body:
    {
        "title": "My Post Title",
        "content": "Post content here..."
    }

    Returns same structure as /api/generate/hello
    """
    user_id = session.get('user_id')

    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title or not content:
        return jsonify({'success': False, 'error': 'Title and content required'}), 400

    try:
        # Generate post
        result = unified_gen.generate_post(title, content, user_id=user_id)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"Error generating post: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@generator_bp.route('/api/generate/library')
def get_library():
    """
    Get all generated content

    Query params:
    - limit: Number of items to return (default 20)

    Returns:
    {
        "success": true,
        "data": [
            {
                "unified_id": 1,
                "title": "Hello World in Python",
                "content_type": "hello_world",
                "content_hash": "abc123...",
                "upc_code": "123456789012",
                "qr_url": "https://soulfra.com/v/abc123",
                "affiliate_code": "AFF-abc123",
                "created_at": "2025-12-28T12:00:00"
            },
            ...
        ]
    }
    """
    limit = request.args.get('limit', 20, type=int)

    try:
        content = unified_gen.get_all_content(limit=limit)

        return jsonify({
            'success': True,
            'data': content
        })

    except Exception as e:
        print(f"Error fetching library: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@generator_bp.route('/api/generate/verify/<content_hash>')
def verify_content(content_hash):
    """
    Verify content by hash

    This is the "100% verifiable" feature - checks that all codes match

    Returns:
    {
        "success": true,
        "verified": true,
        "hash_matches": true,
        "upc_valid": true,
        "upc_matches_hash": true,
        "data": { ... all content data ... }
    }
    """
    try:
        verification = unified_gen.verify_content(content_hash)

        if not verification.get('verified', False) and 'error' in verification:
            return jsonify({
                'success': False,
                'error': verification['error']
            }), 404

        return jsonify({
            'success': True,
            **verification
        })

    except Exception as e:
        print(f"Error verifying content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@generator_bp.route('/generate/view/<int:unified_id>')
def view_generated_content(unified_id):
    """
    View generated content with all codes displayed

    Shows:
    - Content
    - SHA-256 hash
    - UPC-12 barcode
    - QR code
    - Affiliate link
    - Verification status
    """
    # Fetch content from database
    conn = get_db()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    content = conn.execute('''
        SELECT * FROM unified_content WHERE id = ?
    ''', (unified_id,)).fetchone()

    conn.close()

    if not content:
        return "Content not found", 404

    # Verify content
    verification = unified_gen.verify_content(content['content_hash'])

    # Parse metadata
    metadata = json.loads(content['metadata']) if content['metadata'] else {}

    return render_template('generate_view.html',
        content=content,
        metadata=metadata,
        verification=verification,
        verified=verification.get('verified', False)
    )


@generator_bp.route('/api/generate/stats')
def get_stats():
    """
    Get generation statistics

    Returns:
    {
        "total_content": 42,
        "by_type": {
            "hello_world": 10,
            "post": 32
        },
        "by_language": {
            "python": 5,
            "javascript": 3,
            ...
        }
    }
    """
    try:
        conn = get_db()

        # Total content
        total = conn.execute('SELECT COUNT(*) as count FROM unified_content').fetchone()[0]

        # By type
        by_type_rows = conn.execute('''
            SELECT content_type, COUNT(*) as count
            FROM unified_content
            GROUP BY content_type
        ''').fetchall()
        by_type = {row[0]: row[1] for row in by_type_rows}

        # By language (for hello_world type)
        by_language_rows = conn.execute('''
            SELECT language, COUNT(*) as count
            FROM unified_content
            WHERE language IS NOT NULL
            GROUP BY language
        ''').fetchall()
        by_language = {row[0]: row[1] for row in by_language_rows}

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_content': total,
                'by_type': by_type,
                'by_language': by_language
            }
        })

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Vanity URL Redirect (for QR codes and short links)
# =============================================================================

@generator_bp.route('/v/<short_code>')
def vanity_redirect(short_code):
    """
    Redirect from vanity short code to actual content

    This is what QR codes point to
    """
    conn = get_db()

    # Look up short code in vanity_qr_codes table
    qr_data = conn.execute('''
        SELECT full_url FROM vanity_qr_codes WHERE short_code = ?
    ''', (short_code,)).fetchone()

    # Track click
    if qr_data:
        conn.execute('''
            UPDATE vanity_qr_codes
            SET clicks = clicks + 1, last_clicked_at = CURRENT_TIMESTAMP
            WHERE short_code = ?
        ''', (short_code,))
        conn.commit()

    conn.close()

    if qr_data:
        return redirect(qr_data[0])
    else:
        return "Short code not found", 404


@generator_bp.route('/aff/<affiliate_code>')
def affiliate_redirect(affiliate_code):
    """
    Redirect from affiliate code to content

    Tracks affiliate clicks
    """
    from unified_generator import track_affiliate_click

    # Track click
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    referrer = request.referrer

    track_affiliate_click(affiliate_code, ip_address, user_agent, referrer)

    # Get content hash from affiliate code
    conn = get_db()
    affiliate_data = conn.execute('''
        SELECT content_hash FROM affiliate_codes WHERE code = ?
    ''', (affiliate_code,)).fetchone()

    if not affiliate_data:
        conn.close()
        return "Affiliate code not found", 404

    content_hash = affiliate_data[0]

    # Find unified content
    content = conn.execute('''
        SELECT id FROM unified_content WHERE content_hash = ?
    ''', (content_hash,)).fetchone()

    conn.close()

    if content:
        return redirect(url_for('generator.view_generated_content', unified_id=content[0]))
    else:
        return "Content not found", 404

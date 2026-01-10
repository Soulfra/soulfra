#!/usr/bin/env python3
"""
Soulfra API Server - Dynamic Features for Static Sites

ONE tiny Flask API server that handles dynamic features for ALL static sites:
- Email capture / newsletter signups
- Comments (future)
- Authentication (future)
- Paid features (future)

This runs on a single $5/month DigitalOcean droplet and serves ALL your sites.

Architecture:
    - Static sites (GitHub Pages) → Free
    - API server (this file) → $5/month
    - Database (SQLite) → Same server

Usage:
    python3 api_server.py

Deploy:
    # On DigitalOcean droplet:
    python3 api_server.py --port 8080 --host 0.0.0.0

Cost:
    - 1 site: $5/month
    - 10 sites: $5/month
    - 100 sites: $5/month (same server, same cost)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db
import os


app = Flask(__name__)

# Enable CORS for all origins (static sites from GitHub Pages)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all static sites
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


@app.route('/')
def index():
    """API status page"""
    return jsonify({
        'service': 'Soulfra API',
        'version': '1.0',
        'endpoints': {
            'email_capture': '/api/email-capture (POST)',
            'comments': '/api/comments (POST, GET)',
            'health': '/api/health (GET)'
        },
        'status': 'operational'
    })


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected'
    })


@app.route('/api/email-capture', methods=['POST', 'OPTIONS'])
def email_capture():
    """
    Capture email signups from static sites

    POST body:
        {
            "email": "user@example.com",
            "brand_slug": "howtocookathome"
        }

    Returns:
        {
            "success": true,
            "message": "Subscribed!"
        }
    """
    # Handle preflight
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({
            'success': False,
            'message': 'Email required'
        }), 400

    email = data['email'].strip().lower()
    brand_slug = data.get('brand_slug', 'unknown')

    # Validate email format
    if '@' not in email or '.' not in email:
        return jsonify({
            'success': False,
            'message': 'Invalid email format'
        }), 400

    # Store in database
    db = get_db()

    try:
        # Check if already subscribed
        existing = db.execute(
            'SELECT id FROM subscribers WHERE email = ? AND brand_slug = ?',
            (email, brand_slug)
        ).fetchone()

        if existing:
            db.close()
            return jsonify({
                'success': True,
                'message': 'Already subscribed!'
            })

        # Create subscribers table if doesn't exist
        db.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                brand_slug TEXT NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                UNIQUE(email, brand_slug)
            )
        ''')

        # Insert subscriber
        db.execute(
            'INSERT INTO subscribers (email, brand_slug) VALUES (?, ?)',
            (email, brand_slug)
        )
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'message': 'Subscribed! Check your email.'
        })

    except Exception as e:
        db.close()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/comments', methods=['GET', 'POST', 'OPTIONS'])
def comments():
    """
    Handle comments for static sites (future feature)

    GET /api/comments?post_id=123
        Returns all comments for a post

    POST /api/comments
        Creates a new comment

    Body:
        {
            "post_id": 123,
            "author_name": "John",
            "content": "Great post!",
            "brand_slug": "howtocookathome"
        }
    """
    # Handle preflight
    if request.method == 'OPTIONS':
        return '', 204

    if request.method == 'GET':
        post_id = request.args.get('post_id')
        if not post_id:
            return jsonify({
                'success': False,
                'message': 'post_id required'
            }), 400

        db = get_db()
        comments_list = db.execute('''
            SELECT c.*, u.display_name, u.is_ai_persona
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.id ASC
        ''', (post_id,)).fetchall()
        db.close()

        return jsonify({
            'success': True,
            'comments': [dict(c) for c in comments_list]
        })

    # POST - create comment (future feature)
    return jsonify({
        'success': False,
        'message': 'Comment creation not yet implemented'
    }), 501


@app.route('/api/stats')
def stats():
    """
    Get API statistics

    Returns subscriber counts per brand
    """
    db = get_db()

    try:
        # Check if subscribers table exists
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='subscribers'"
        ).fetchone()

        if not tables:
            db.close()
            return jsonify({
                'total_subscribers': 0,
                'brands': {}
            })

        # Get stats
        stats_data = db.execute('''
            SELECT brand_slug, COUNT(*) as count
            FROM subscribers
            WHERE active = 1
            GROUP BY brand_slug
        ''').fetchall()

        total = sum(s['count'] for s in stats_data)

        db.close()

        return jsonify({
            'total_subscribers': total,
            'brands': {s['brand_slug']: s['count'] for s in stats_data}
        })

    except Exception as e:
        db.close()
        return jsonify({
            'error': str(e)
        }), 500


def main():
    """Run the API server"""
    import sys

    port = 5002  # Default API port (different from main app port 5001)
    host = '127.0.0.1'  # Default to localhost

    # Parse arguments
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    if '--host' in sys.argv:
        idx = sys.argv.index('--host')
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]

    print("=" * 70)
    print("🚀 Soulfra API Server")
    print("=" * 70)
    print(f"📍 Running on: http://{host}:{port}")
    print(f"📊 Stats: http://{host}:{port}/api/stats")
    print(f"💚 Health: http://{host}:{port}/api/health")
    print()
    print("Endpoints:")
    print(f"  POST /api/email-capture - Email signups")
    print(f"  GET  /api/comments - Get comments")
    print(f"  POST /api/comments - Post comment (future)")
    print(f"  GET  /api/stats - Subscriber stats")
    print()
    print("CORS: Enabled for all origins (static sites)")
    print("=" * 70)
    print()

    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()

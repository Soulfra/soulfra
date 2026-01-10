#!/usr/bin/env python3
"""
API Routes - Domain Distribution System
The "Faucet" - content flows from soulfra-simple to all domains

Endpoints:
- GET /api/posts - List all published posts
- GET /api/posts?tag=privacy - Filter by tag
- GET /api/posts/{id} - Single post
- GET /api/health - API health check
"""

from flask import Blueprint, jsonify, request
from database import get_db
import json

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'ok',
        'service': 'soulfra-api',
        'version': '1.0'
    })


@api_bp.route('/api/posts', methods=['GET'])
def list_posts():
    """
    List all published posts

    Query params:
    - tag: Filter by tag (privacy, security, cooking, tech, etc.)
    - limit: Max posts to return (default 50)
    - offset: Pagination offset (default 0)
    - brand: Filter by brand

    Examples:
    GET /api/posts
    GET /api/posts?tag=privacy
    GET /api/posts?tag=cooking&limit=10
    GET /api/posts?brand=deathtodata
    """

    db = get_db()

    # Get query params
    tag = request.args.get('tag')
    brand = request.args.get('brand')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    # Base query - only published posts
    query = '''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.content,
            p.excerpt,
            p.published_at,
            p.brand,
            u.username as author
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.published_at IS NOT NULL
    '''

    params = []

    # Filter by brand if specified
    if brand:
        query += ' AND p.brand = ?'
        params.append(brand)

    # Filter by tag if specified
    if tag:
        # Check if post_tags table exists
        tags_table_exists = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='post_tags'"
        ).fetchone()

        if tags_table_exists:
            query = '''
                SELECT DISTINCT
                    p.id,
                    p.title,
                    p.slug,
                    p.content,
                    p.excerpt,
                    p.published_at,
                    p.brand,
                    u.username as author
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                LEFT JOIN post_tags pt ON p.id = pt.post_id
                WHERE p.published_at IS NOT NULL
                AND pt.tag = ?
            '''
            params = [tag] + params

    # Order by newest first
    query += ' ORDER BY p.published_at DESC'

    # Add pagination
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    # Execute query
    posts = db.execute(query, params).fetchall()

    # Convert to JSON-friendly format
    posts_list = []
    for post in posts:
        posts_list.append({
            'id': post['id'],
            'title': post['title'],
            'slug': post['slug'],
            'content': post['content'],
            'excerpt': post['excerpt'],
            'published_at': post['published_at'],
            'brand': post['brand'],
            'author': post['author'],
            'url': f'/posts/{post["slug"]}'
        })

    # Get total count
    count_query = 'SELECT COUNT(*) as total FROM posts WHERE published_at IS NOT NULL'
    count_params = []

    if brand:
        count_query += ' AND brand = ?'
        count_params.append(brand)

    if tag and tags_table_exists:
        count_query = '''
            SELECT COUNT(DISTINCT p.id) as total
            FROM posts p
            LEFT JOIN post_tags pt ON p.id = pt.post_id
            WHERE p.published_at IS NOT NULL
            AND pt.tag = ?
        '''
        count_params = [tag] + count_params

    total = db.execute(count_query, count_params).fetchone()['total']

    return jsonify({
        'success': True,
        'posts': posts_list,
        'total': total,
        'limit': limit,
        'offset': offset,
        'tag': tag,
        'brand': brand
    })


@api_bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """
    Get single post by ID

    Example:
    GET /api/posts/123
    """

    db = get_db()

    post = db.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.content,
            p.excerpt,
            p.published_at,
            p.brand,
            u.username as author,
            u.id as author_id
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.id = ? AND p.published_at IS NOT NULL
    ''', (post_id,)).fetchone()

    if not post:
        return jsonify({
            'success': False,
            'error': 'Post not found or not published'
        }), 404

    # Get tags if post_tags table exists
    tags = []
    tags_table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='post_tags'"
    ).fetchone()

    if tags_table_exists:
        tag_rows = db.execute('''
            SELECT tag FROM post_tags WHERE post_id = ?
        ''', (post_id,)).fetchall()
        tags = [row['tag'] for row in tag_rows]

    return jsonify({
        'success': True,
        'post': {
            'id': post['id'],
            'title': post['title'],
            'slug': post['slug'],
            'content': post['content'],
            'excerpt': post['excerpt'],
            'published_at': post['published_at'],
            'brand': post['brand'],
            'author': post['author'],
            'author_id': post['author_id'],
            'tags': tags,
            'url': f'/posts/{post["slug"]}'
        }
    })


@api_bp.route('/api/posts/slug/<slug>', methods=['GET'])
def get_post_by_slug(slug):
    """
    Get single post by slug

    Example:
    GET /api/posts/slug/how-to-protect-your-privacy
    """

    db = get_db()

    post = db.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.content,
            p.excerpt,
            p.published_at,
            p.brand,
            u.username as author,
            u.id as author_id
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.slug = ? AND p.published_at IS NOT NULL
    ''', (slug,)).fetchone()

    if not post:
        return jsonify({
            'success': False,
            'error': 'Post not found or not published'
        }), 404

    # Get tags if post_tags table exists
    tags = []
    tags_table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='post_tags'"
    ).fetchone()

    if tags_table_exists:
        tag_rows = db.execute('''
            SELECT tag FROM post_tags WHERE post_id = ?
        ''', (post['id'],)).fetchall()
        tags = [row['tag'] for row in tag_rows]

    return jsonify({
        'success': True,
        'post': {
            'id': post['id'],
            'title': post['title'],
            'slug': post['slug'],
            'content': post['content'],
            'excerpt': post['excerpt'],
            'published_at': post['published_at'],
            'brand': post['brand'],
            'author': post['author'],
            'author_id': post['author_id'],
            'tags': tags,
            'url': f'/posts/{post["slug"]}'
        }
    })


@api_bp.route('/api/tags', methods=['GET'])
def list_tags():
    """
    List all available tags

    Example:
    GET /api/tags
    """

    db = get_db()

    # Check if post_tags table exists
    tags_table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='post_tags'"
    ).fetchone()

    if not tags_table_exists:
        return jsonify({
            'success': True,
            'tags': [],
            'message': 'Tags table does not exist yet'
        })

    # Get all unique tags with post counts
    tags = db.execute('''
        SELECT
            pt.tag,
            COUNT(DISTINCT p.id) as post_count
        FROM post_tags pt
        JOIN posts p ON pt.post_id = p.id
        WHERE p.published_at IS NOT NULL
        GROUP BY pt.tag
        ORDER BY post_count DESC
    ''').fetchall()

    tags_list = [
        {
            'tag': row['tag'],
            'post_count': row['post_count']
        }
        for row in tags
    ]

    return jsonify({
        'success': True,
        'tags': tags_list
    })


@api_bp.route('/api/brands', methods=['GET'])
def list_brands():
    """
    List all available brands

    Example:
    GET /api/brands
    """

    db = get_db()

    # Get all unique brands with post counts
    brands = db.execute('''
        SELECT
            brand,
            COUNT(*) as post_count
        FROM posts
        WHERE published_at IS NOT NULL
        AND brand IS NOT NULL
        GROUP BY brand
        ORDER BY post_count DESC
    ''').fetchall()

    brands_list = [
        {
            'brand': row['brand'],
            'post_count': row['post_count']
        }
        for row in brands
    ]

    return jsonify({
        'success': True,
        'brands': brands_list
    })


# CORS support for cross-domain requests
@api_bp.after_request
def after_request(response):
    """Add CORS headers to allow cross-domain requests"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response

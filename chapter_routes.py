"""
Chapter API Routes

Endpoints for chapter card UI and chapter management
"""

from flask import Blueprint, request, jsonify, send_file
from database import get_db
from chapter_qr_generator import generate_chapter_qr

chapter_bp = Blueprint('chapters', __name__)

@chapter_bp.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    """
    Get chapter details

    Returns:
    {
        "success": true,
        "id": 11,
        "chapter_num": 11,
        "version_num": 1,
        "title": "Soulfra",
        "content": "# Soulfra\n\nYour keys...",
        "created_at": "2026-01-04 12:34:56",
        "created_by_user_id": 1,
        "commit_message": "Synced from soulfra README"
    }
    """
    db = get_db()

    chapter = db.execute('''
        SELECT id, chapter_num, version_num, title, content,
               created_at, created_by_user_id, commit_message
        FROM chapter_snapshots
        WHERE id = ?
    ''', (chapter_id,)).fetchone()

    if not chapter:
        return jsonify({'success': False, 'error': f'Chapter {chapter_id} not found'}), 404

    return jsonify({
        'success': True,
        'id': chapter['id'],
        'chapter_num': chapter['chapter_num'],
        'version_num': chapter['version_num'],
        'title': chapter['title'],
        'content': chapter['content'],
        'created_at': chapter['created_at'],
        'created_by_user_id': chapter['created_by_user_id'],
        'commit_message': chapter['commit_message']
    })


@chapter_bp.route('/api/chapter-qr/<int:chapter_id>', methods=['GET'])
def get_chapter_qr(chapter_id):
    """
    Get QR code for chapter

    Returns:
    {
        "success": true,
        "chapter_id": 11,
        "url": "https://cringeproof.com/chapter/11",
        "upc": "969696000117",
        "qr_data_url": "data:image/png;base64,...",
        "signature": "..."
    }
    """
    domain = request.args.get('domain', 'cringeproof.com')
    result = generate_chapter_qr(chapter_id, domain=domain)

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@chapter_bp.route('/api/chapters/list', methods=['GET'])
def list_chapters():
    """
    List all chapters with pagination

    Query params:
    - limit: Max chapters (default: 20)
    - offset: Skip N chapters (default: 0)
    - domain: Filter by domain name

    Returns:
    {
        "success": true,
        "chapters": [...],
        "total": 12,
        "limit": 20,
        "offset": 0
    }
    """
    db = get_db()

    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    domain = request.args.get('domain')

    # Build query
    if domain:
        query = '''
            SELECT id, chapter_num, version_num, title, created_at,
                   LENGTH(content) as content_length
            FROM chapter_snapshots
            WHERE (title LIKE ? OR commit_message LIKE ?)
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        params = (f'%{domain}%', f'%{domain}%', limit, offset)

        count_query = '''
            SELECT COUNT(*) as count
            FROM chapter_snapshots
            WHERE (title LIKE ? OR commit_message LIKE ?)
        '''
        count_params = (f'%{domain}%', f'%{domain}%')
    else:
        query = '''
            SELECT id, chapter_num, version_num, title, created_at,
                   LENGTH(content) as content_length
            FROM chapter_snapshots
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        params = (limit, offset)

        count_query = 'SELECT COUNT(*) as count FROM chapter_snapshots'
        count_params = ()

    chapters = db.execute(query, params).fetchall()
    total = db.execute(count_query, count_params).fetchone()['count']

    return jsonify({
        'success': True,
        'chapters': [
            {
                'id': c['id'],
                'chapter_num': c['chapter_num'],
                'version_num': c['version_num'],
                'title': c['title'],
                'created_at': c['created_at'],
                'content_length': c['content_length']
            }
            for c in chapters
        ],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@chapter_bp.route('/chapter/<int:chapter_id>', methods=['GET'])
def chapter_page(chapter_id):
    """
    Render chapter page (redirects to chapter card)
    """
    from flask import redirect
    return redirect(f'/chapter-card.html?id={chapter_id}')


@chapter_bp.route('/chapter-card.html', methods=['GET'])
def chapter_card():
    """
    Serve chapter card HTML
    """
    from flask import send_from_directory
    return send_from_directory('.', 'chapter_card.html')

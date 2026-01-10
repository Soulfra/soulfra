#!/usr/bin/env python3
"""
Share Routes - Shareable AI Responses with QR Codes and SHA-256 Verification

Features:
- Create shareable response URLs with unique IDs
- QR code generation for easy sharing
- SHA-256 content hashing for tamper detection
- View tracking and analytics
- QR/UPC scanner validation
- Time-series metrics

Routes:
- GET /adaptive → Adaptive interface (device detection)
- GET /scanner → QR/UPC scanner
- GET /share/<response_id> → Shareable response page
- POST /api/share/create → Create new shareable response
- GET /api/share/<response_id> → Get response data (JSON)
- POST /api/share/validate → Validate QR/UPC scan
- GET /api/share/metrics/<response_id> → Get time-series metrics
"""

from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, Response
from database import get_db
import hashlib
import secrets
from datetime import datetime
import qrcode
import io

share_bp = Blueprint('share', __name__)


def generate_response_id():
    """Generate unique URL-safe ID (11 chars like YouTube)"""
    return secrets.token_urlsafe(8)[:11]


def calculate_sha256(text):
    """Calculate SHA-256 hash of text content"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def track_metric(response_id, metric_type, request_obj=None):
    """Track metric with timestamp for analytics"""
    db = get_db()

    user_agent = request_obj.headers.get('User-Agent', '') if request_obj else ''
    ip_address = request_obj.remote_addr if request_obj else ''

    db.execute('''
        INSERT INTO response_metrics (response_id, metric_type, user_agent, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (response_id, metric_type, user_agent, ip_address))

    db.commit()
    db.close()


# ===== Frontend Pages =====

@share_bp.route('/adaptive')
def adaptive_page():
    """Adaptive interface with device detection"""
    return send_from_directory('voice-archive', 'adaptive.html')


@share_bp.route('/scanner')
def scanner_page():
    """QR/UPC scanner interface"""
    return send_from_directory('voice-archive', 'scanner.html')


@share_bp.route('/share/<response_id>')
def share_page(response_id):
    """Shareable response page with QR code and verification"""
    # Track view
    try:
        track_metric(response_id, 'view', request)

        # Increment view count
        db = get_db()
        db.execute('''
            UPDATE shared_responses
            SET view_count = view_count + 1
            WHERE id = ?
        ''', (response_id,))
        db.commit()
        db.close()
    except:
        pass  # Don't fail if response doesn't exist yet

    return send_from_directory('voice-archive', 'share-response.html')


# ===== API Endpoints =====

@share_bp.route('/api/share/create', methods=['POST'])
def create_shared_response():
    """
    Create new shareable AI response

    POST data:
    {
        "source_type": "screenshot" | "voice" | "text",
        "source_id": 123,  // Optional FK to voice recording etc
        "response_text": "AI analysis text...",
        "crazy_level": 7,  // 1-10 slider value
        "agent_name": "soulfra"  // Which AI agent analyzed
    }

    Returns:
    {
        "success": true,
        "response_id": "abc123xyz",
        "share_url": "https://soulfra.com/share/abc123xyz",
        "content_hash": "sha256...",
        "qr_url": "https://soulfra.com/share/abc123xyz/qr.svg"
    }
    """
    data = request.get_json()

    if not data or 'response_text' not in data:
        return jsonify({'success': False, 'error': 'No response_text provided'}), 400

    # Generate unique ID
    response_id = generate_response_id()

    # Calculate content hash
    content_hash = calculate_sha256(data['response_text'])

    # Get user_id from session
    user_id = session.get('user_id')

    # Save to database
    db = get_db()

    db.execute('''
        INSERT INTO shared_responses (
            id, source_type, source_id, response_text, crazy_level,
            content_hash, user_id, agent_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        response_id,
        data.get('source_type', 'text'),
        data.get('source_id'),
        data['response_text'],
        data.get('crazy_level', 5),
        content_hash,
        user_id,
        data.get('agent_name', 'soulfra')
    ))

    db.commit()
    db.close()

    # Track creation metric
    track_metric(response_id, 'create', request)

    # Build response
    base_url = request.url_root.rstrip('/')
    share_url = f"{base_url}/share/{response_id}"

    return jsonify({
        'success': True,
        'response_id': response_id,
        'share_url': share_url,
        'content_hash': content_hash,
        'qr_url': f"{share_url}/qr.svg"
    })


@share_bp.route('/api/share/<response_id>', methods=['GET'])
def get_shared_response(response_id):
    """
    Get shareable response data (JSON)

    Returns:
    {
        "success": true,
        "id": "abc123xyz",
        "text": "AI analysis...",
        "source": "screenshot",
        "crazy_level": 7,
        "timestamp": "2025-01-05T...",
        "hash": "sha256...",
        "verified": true,
        "view_count": 42,
        "agent_name": "soulfra"
    }
    """
    db = get_db()

    response = db.execute('''
        SELECT * FROM shared_responses WHERE id = ?
    ''', (response_id,)).fetchone()

    if not response:
        db.close()
        return jsonify({'success': False, 'error': 'Response not found'}), 404

    # Verify hash integrity
    current_hash = calculate_sha256(response['response_text'])
    verified = (current_hash == response['content_hash'])

    # Build response
    result = {
        'success': True,
        'id': response['id'],
        'text': response['response_text'],
        'source': response['source_type'],
        'crazy_level': response['crazy_level'],
        'timestamp': response['created_at'],
        'hash': response['content_hash'],
        'verified': verified,
        'view_count': response['view_count'],
        'agent_name': response['agent_name']
    }

    db.close()

    return jsonify(result)


@share_bp.route('/api/share/<response_id>/metadata', methods=['GET'])
def get_response_metadata(response_id):
    """
    Get full metadata for scanner debug panel

    Returns:
    {
        "success": true,
        "response": {...},          # Full response data
        "metrics": {...},           # View/scan counts
        "recent_activity": [...],   # Last 10 views/scans
        "verification": {           # SHA-256 status
            "verified": true,
            "current_hash": "...",
            "stored_hash": "..."
        }
    }
    """
    db = get_db()

    # Get response data
    response = db.execute('''
        SELECT * FROM shared_responses WHERE id = ?
    ''', (response_id,)).fetchone()

    if not response:
        db.close()
        return jsonify({'success': False, 'error': 'Response not found'}), 404

    # Verify hash
    current_hash = calculate_sha256(response['response_text'])
    verified = (current_hash == response['content_hash'])

    # Get metrics counts
    metrics_raw = db.execute('''
        SELECT metric_type, COUNT(*) as count
        FROM response_metrics
        WHERE response_id = ?
        GROUP BY metric_type
    ''', (response_id,)).fetchall()

    metrics = {row['metric_type']: row['count'] for row in metrics_raw}

    # Get recent activity (last 10 events)
    recent_activity_raw = db.execute('''
        SELECT metric_type, timestamp, user_agent, ip_address
        FROM response_metrics
        WHERE response_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (response_id,)).fetchall()

    recent_activity = [
        {
            'type': row['metric_type'],
            'timestamp': row['timestamp'],
            'user_agent': row['user_agent'][:50] if row['user_agent'] else 'unknown',
            'ip': row['ip_address'] or 'unknown'
        }
        for row in recent_activity_raw
    ]

    db.close()

    return jsonify({
        'success': True,
        'response': {
            'id': response['id'],
            'text': response['response_text'],
            'source': response['source_type'],
            'crazy_level': response['crazy_level'],
            'timestamp': response['created_at'],
            'view_count': response['view_count'],
            'agent_name': response['agent_name']
        },
        'metrics': {
            'views': metrics.get('view', 0),
            'scans': metrics.get('scan', 0),
            'shares': metrics.get('share', 0),
            'copies': metrics.get('copy', 0)
        },
        'verification': {
            'verified': verified,
            'current_hash': current_hash,
            'stored_hash': response['content_hash'],
            'algorithm': 'SHA-256'
        },
        'recent_activity': recent_activity
    })


@share_bp.route('/api/share/validate', methods=['POST'])
def validate_scan():
    """
    Validate QR/UPC scan

    POST data:
    {
        "code_type": "QR Code" | "UPC" | "EAN-13",
        "code_value": "https://soulfra.com/share/abc123"
    }

    Returns:
    {
        "success": true,
        "validated": true,
        "scan_id": 123,
        "message": "Code validated successfully"
    }
    """
    data = request.get_json()

    if not data or 'code_value' not in data:
        return jsonify({'success': False, 'error': 'No code_value provided'}), 400

    code_type = data.get('code_type', 'QR Code')
    code_value = data['code_value']

    # Validation logic
    validated = False

    if code_type == 'QR Code' and '/share/' in code_value:
        # Valid share URL
        validated = True
    elif code_type in ['UPC', 'EAN-13'] and code_value.isdigit():
        # Valid barcode
        validated = True

    # Save to database
    user_id = session.get('user_id')
    session_id = data.get('session_id', 'anonymous')

    db = get_db()

    cursor = db.execute('''
        INSERT INTO scan_history (code_type, code_value, validated, user_id, session_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (code_type, code_value, validated, user_id, session_id))

    scan_id = cursor.lastrowid
    db.commit()
    db.close()

    # Track metric
    if '/share/' in code_value:
        # Extract response_id from URL
        try:
            response_id = code_value.split('/share/')[-1].split('?')[0]
            track_metric(response_id, 'scan', request)
        except:
            pass

    message = 'Code validated successfully' if validated else 'Invalid code format'

    return jsonify({
        'success': True,
        'validated': validated,
        'scan_id': scan_id,
        'message': message
    })


@share_bp.route('/api/share/metrics/<response_id>', methods=['GET'])
def get_response_metrics(response_id):
    """
    Get time-series metrics for response

    Query params:
    - timeframe: 'hour' | 'day' | 'week' | 'month' (default: 'day')

    Returns:
    {
        "success": true,
        "response_id": "abc123",
        "metrics": {
            "views": 42,
            "scans": 7,
            "shares": 3,
            "copies": 12
        },
        "timeline": [
            {"timestamp": "2025-01-05T10:00:00", "views": 5},
            {"timestamp": "2025-01-05T11:00:00", "views": 8},
            ...
        ]
    }
    """
    timeframe = request.args.get('timeframe', 'day')

    # Map timeframe to SQL interval
    intervals = {
        'hour': "datetime('now', '-1 hour')",
        'day': "datetime('now', '-1 day')",
        'week': "datetime('now', '-7 days')",
        'month': "datetime('now', '-30 days')"
    }

    since = intervals.get(timeframe, intervals['day'])

    db = get_db()

    # Get total counts by type
    metrics_raw = db.execute(f'''
        SELECT metric_type, COUNT(*) as count
        FROM response_metrics
        WHERE response_id = ?
        AND timestamp >= {since}
        GROUP BY metric_type
    ''', (response_id,)).fetchall()

    metrics = {row['metric_type']: row['count'] for row in metrics_raw}

    # Get timeline (hourly buckets)
    timeline_raw = db.execute(f'''
        SELECT
            strftime('%Y-%m-%dT%H:00:00', timestamp) as hour,
            COUNT(*) as views
        FROM response_metrics
        WHERE response_id = ?
        AND metric_type = 'view'
        AND timestamp >= {since}
        GROUP BY hour
        ORDER BY hour
    ''', (response_id,)).fetchall()

    timeline = [{'timestamp': row['hour'], 'views': row['views']} for row in timeline_raw]

    db.close()

    return jsonify({
        'success': True,
        'response_id': response_id,
        'metrics': {
            'views': metrics.get('view', 0),
            'scans': metrics.get('scan', 0),
            'shares': metrics.get('share', 0),
            'copies': metrics.get('copy', 0)
        },
        'timeline': timeline
    })


@share_bp.route('/share/<response_id>/qr.png')
def get_qr_code(response_id):
    """
    Generate real scannable QR code as PNG

    Returns PNG image that encodes the share URL
    """
    # Build full share URL
    base_url = request.url_root.rstrip('/')
    share_url = f"{base_url}/share/{response_id}"

    # Generate QR code with high error correction
    qr = qrcode.QRCode(
        version=1,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% error correction
        box_size=10,
        border=4,
    )
    qr.add_data(share_url)
    qr.make(fit=True)

    # Create image with brand colors
    img = qr.make_image(fill_color="#667eea", back_color="white")

    # Convert to PNG bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return Response(img_buffer.getvalue(), mimetype='image/png')


@share_bp.route('/api/share/feed', methods=['GET'])
def get_unified_feed():
    """
    Unified feed - All AI responses from all sources (UNION query)

    Query params:
    - limit: Number of results (default: 20)
    - offset: Pagination offset (default: 0)
    - source_type: Filter by 'screenshot' | 'voice' | 'text' (optional)

    Returns:
    {
        "success": true,
        "responses": [
            {
                "id": "abc123",
                "source": "voice",
                "excerpt": "First 100 chars...",
                "crazy_level": 7,
                "timestamp": "2025-01-05T...",
                "views": 42,
                "agent_name": "soulfra"
            },
            ...
        ],
        "total": 150
    }
    """
    limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
    offset = int(request.args.get('offset', 0))
    source_type = request.args.get('source_type')

    db = get_db()

    # Base query
    where_clause = ''
    params = []

    if source_type:
        where_clause = 'WHERE source_type = ?'
        params.append(source_type)

    # Get responses
    query = f'''
        SELECT
            id,
            source_type,
            substr(response_text, 1, 100) as excerpt,
            crazy_level,
            created_at,
            view_count,
            agent_name
        FROM shared_responses
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    '''

    params.extend([limit, offset])
    responses_raw = db.execute(query, params).fetchall()

    # Get total count
    count_query = f'SELECT COUNT(*) as total FROM shared_responses {where_clause}'
    count_params = [source_type] if source_type else []
    total = db.execute(count_query, count_params).fetchone()['total']

    db.close()

    # Build response
    responses = [
        {
            'id': row['id'],
            'source': row['source_type'],
            'excerpt': row['excerpt'] + ('...' if len(row['excerpt']) == 100 else ''),
            'crazy_level': row['crazy_level'],
            'timestamp': row['created_at'],
            'views': row['view_count'],
            'agent_name': row['agent_name']
        }
        for row in responses_raw
    ]

    return jsonify({
        'success': True,
        'responses': responses,
        'total': total
    })


@share_bp.route('/api/share/voice-readme-join', methods=['GET'])
def voice_readme_join():
    """
    NATURAL JOIN example - Connect voice recordings with shared responses

    Shows which voice memos became README entries

    Returns:
    {
        "success": true,
        "joined_data": [
            {
                "voice_id": 123,
                "transcription": "Build adaptive interface...",
                "response_id": "abc123",
                "response_excerpt": "Analysis of adaptive UI...",
                "agent_name": "soulfra",
                "timestamp": "2025-01-05T..."
            },
            ...
        ]
    }
    """
    db = get_db()

    # INNER JOIN - Only voice recordings that became shared responses
    joined = db.execute('''
        SELECT
            v.id as voice_id,
            substr(v.transcription, 1, 100) as transcription,
            s.id as response_id,
            substr(s.response_text, 1, 100) as response_excerpt,
            s.agent_name,
            s.created_at
        FROM simple_voice_recordings v
        INNER JOIN shared_responses s ON v.id = s.source_id
        WHERE s.source_type = 'voice'
        ORDER BY s.created_at DESC
        LIMIT 50
    ''').fetchall()

    db.close()

    # Build response
    joined_data = [
        {
            'voice_id': row['voice_id'],
            'transcription': row['transcription'],
            'response_id': row['response_id'],
            'response_excerpt': row['response_excerpt'],
            'agent_name': row['agent_name'],
            'timestamp': row['created_at']
        }
        for row in joined
    ]

    return jsonify({
        'success': True,
        'joined_data': joined_data
    })

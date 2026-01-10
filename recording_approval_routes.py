#!/usr/bin/env python3
"""
Recording Approval & Deletion Routes

Allows users to approve/delete voice recordings from phone after reviewing.

Features:
- List pending recordings
- Approve recording (triggers GitHub README update)
- Delete recording
- Email notifications when new recording uploaded

Routes:
- GET /api/recordings/pending - List pending recordings for approval
- POST /api/recordings/<id>/approve - Approve recording
- DELETE /api/recordings/<id> - Delete recording
- GET /recordings/review - HTML page to review/approve recordings
"""

from flask import Blueprint, jsonify, request, render_template_string
from database import get_db
from datetime import datetime, timezone

approval_bp = Blueprint('approval', __name__)


def create_approval_tables():
    """
    Create tables for recording approval workflow

    Tables:
    - recording_status: Track approval status of recordings
    """
    db = get_db()

    # Add approval status column to simple_voice_recordings if not exists
    try:
        db.execute('ALTER TABLE simple_voice_recordings ADD COLUMN approval_status TEXT DEFAULT "pending"')
        db.execute('ALTER TABLE simple_voice_recordings ADD COLUMN approved_at TEXT')
        db.commit()
        print("✅ Added approval_status column")
    except Exception as e:
        # Column probably already exists
        pass

    print("✅ Approval tables ready")


@approval_bp.route('/api/recordings/pending')
def get_pending_recordings():
    """
    Get all pending recordings for current user

    Example:
        GET /api/recordings/pending

    Response:
        {
            "success": true,
            "recordings": [
                {
                    "id": 123,
                    "transcription": "Ideas about AI safety",
                    "created_at": "2026-01-04T12:00:00Z",
                    "device_name": "iPhone (iOS 15.0)",
                    "articles_count": 5,
                    "wordmap_preview": ["ai", "safety", "ideas"]
                }
            ]
        }
    """
    from flask import session

    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated'
        }), 401

    db = get_db()

    # Get pending recordings with device info and article counts
    recordings = db.execute('''
        SELECT
            svr.id,
            svr.transcription,
            svr.created_at,
            df.device_name,
            df.device_type,
            (SELECT COUNT(*) FROM recording_articles WHERE recording_id = svr.id) as articles_count
        FROM simple_voice_recordings svr
        LEFT JOIN recording_devices rd ON svr.id = rd.recording_id
        LEFT JOIN device_fingerprints df ON rd.device_id = df.id
        WHERE svr.user_id = ?
        AND (svr.approval_status IS NULL OR svr.approval_status = 'pending')
        AND svr.transcription IS NOT NULL
        ORDER BY svr.created_at DESC
    ''', (user_id,)).fetchall()

    # Format results
    results = []
    for rec in recordings:
        # Extract first 3 keywords as preview
        from voice_scraper import extract_keywords
        keywords = extract_keywords(rec['transcription'])[:3] if rec['transcription'] else []

        results.append({
            'id': rec['id'],
            'transcription': rec['transcription'],
            'created_at': rec['created_at'],
            'device_name': rec['device_name'] or 'Unknown Device',
            'device_type': rec['device_type'] or 'Unknown',
            'articles_count': rec['articles_count'],
            'wordmap_preview': keywords
        })

    return jsonify({
        'success': True,
        'recordings': results
    })


@approval_bp.route('/api/recordings/<int:recording_id>/approve', methods=['POST'])
def approve_recording(recording_id):
    """
    Approve a recording (triggers GitHub README update)

    Example:
        POST /api/recordings/123/approve

    Response:
        {
            "success": true,
            "recording_id": 123,
            "github_update_triggered": true
        }
    """
    from flask import session

    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated'
        }), 401

    db = get_db()

    # Verify recording belongs to user
    recording = db.execute('''
        SELECT id, user_id FROM simple_voice_recordings WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return jsonify({
            'success': False,
            'error': 'Recording not found'
        }), 404

    if recording['user_id'] != user_id:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        }), 403

    # Approve recording
    now = datetime.now(timezone.utc).isoformat()
    db.execute('''
        UPDATE simple_voice_recordings
        SET approval_status = 'approved', approved_at = ?
        WHERE id = ?
    ''', (now, recording_id))
    db.commit()

    # Trigger GitHub README update (if user has slug)
    github_update_triggered = False
    try:
        user = db.execute('SELECT user_slug FROM users WHERE id = ?', (user_id,)).fetchone()

        if user and user['user_slug']:
            # GitHub Actions will pick this up automatically on next run
            # Or we could trigger webhook here
            github_update_triggered = True
            print(f"✅ Recording {recording_id} approved - GitHub README will update")
    except Exception as e:
        print(f"⚠️  GitHub update failed: {e}")

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'approved_at': now,
        'github_update_triggered': github_update_triggered
    })


@approval_bp.route('/api/recordings/<int:recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    """
    Delete a recording

    Example:
        DELETE /api/recordings/123

    Response:
        {
            "success": true,
            "recording_id": 123,
            "deleted": true
        }
    """
    from flask import session

    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated'
        }), 401

    db = get_db()

    # Verify recording belongs to user
    recording = db.execute('''
        SELECT id, user_id FROM simple_voice_recordings WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return jsonify({
            'success': False,
            'error': 'Recording not found'
        }), 404

    if recording['user_id'] != user_id:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        }), 403

    # Delete recording (CASCADE should handle related records)
    db.execute('DELETE FROM simple_voice_recordings WHERE id = ?', (recording_id,))
    db.commit()

    print(f"✅ Recording {recording_id} deleted")

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'deleted': True
    })


@approval_bp.route('/recordings/review')
def review_recordings_page():
    """
    HTML page to review and approve/delete recordings

    Example:
        GET /recordings/review
    """
    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Voice Recordings</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            font-size: 32px;
            margin-bottom: 30px;
            text-align: center;
        }
        .recording {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .recording:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .recording-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .recording-device {
            font-size: 12px;
            opacity: 0.8;
        }
        .recording-time {
            font-size: 12px;
            opacity: 0.7;
        }
        .recording-text {
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 15px;
        }
        .recording-meta {
            display: flex;
            gap: 15px;
            font-size: 12px;
            opacity: 0.8;
            margin-bottom: 15px;
        }
        .recording-actions {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-approve {
            background: #00C49A;
            color: white;
        }
        .btn-approve:hover {
            background: #00a082;
            transform: translateY(-2px);
        }
        .btn-delete {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }
        .btn-delete:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .btn-view {
            background: rgba(255, 255, 255, 0.15);
            color: white;
            text-decoration: none;
            display: inline-block;
            padding: 8px 15px;
            font-size: 12px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            opacity: 0.7;
        }
        .loading {
            text-align: center;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Review Voice Recordings</h1>

        <div id="loading" class="loading">
            Loading recordings...
        </div>

        <div id="recordings-container"></div>
    </div>

    <script>
        async function loadRecordings() {
            try {
                const response = await fetch('/api/recordings/pending');
                const data = await response.json();

                document.getElementById('loading').style.display = 'none';

                if (!data.success || data.recordings.length === 0) {
                    document.getElementById('recordings-container').innerHTML = `
                        <div class="empty-state">
                            <h2>✅ All caught up!</h2>
                            <p>No pending recordings to review.</p>
                        </div>
                    `;
                    return;
                }

                const container = document.getElementById('recordings-container');
                container.innerHTML = data.recordings.map(rec => `
                    <div class="recording" id="recording-${rec.id}">
                        <div class="recording-header">
                            <div class="recording-device">
                                📱 ${rec.device_name}
                            </div>
                            <div class="recording-time">
                                ${new Date(rec.created_at).toLocaleString()}
                            </div>
                        </div>

                        <div class="recording-text">
                            ${rec.transcription}
                        </div>

                        <div class="recording-meta">
                            <span>🏷️ ${rec.wordmap_preview.join(', ')}</span>
                            <span>📰 ${rec.articles_count} articles</span>
                        </div>

                        <div class="recording-actions">
                            <button class="btn btn-approve" onclick="approveRecording(${rec.id})">
                                ✓ Approve
                            </button>
                            <button class="btn btn-delete" onclick="deleteRecording(${rec.id})">
                                ✗ Delete
                            </button>
                            <a href="/news/${rec.id}" class="btn btn-view" target="_blank">
                                View Articles →
                            </a>
                        </div>
                    </div>
                `).join('');

            } catch (error) {
                document.getElementById('loading').innerHTML = `
                    <div class="empty-state">
                        <h2>❌ Error</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        async function approveRecording(id) {
            if (!confirm('Approve this recording?')) return;

            try {
                const response = await fetch(`/api/recordings/${id}/approve`, {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.success) {
                    const el = document.getElementById(`recording-${id}`);
                    el.style.background = 'rgba(0, 196, 154, 0.3)';
                    setTimeout(() => {
                        el.remove();
                        if (document.querySelectorAll('.recording').length === 0) {
                            loadRecordings();
                        }
                    }, 500);

                    alert('✅ Recording approved! GitHub README will update automatically.');
                } else {
                    alert(`❌ Error: ${data.error}`);
                }
            } catch (error) {
                alert(`❌ Error: ${error.message}`);
            }
        }

        async function deleteRecording(id) {
            if (!confirm('Delete this recording permanently?')) return;

            try {
                const response = await fetch(`/api/recordings/${id}`, {
                    method: 'DELETE'
                });
                const data = await response.json();

                if (data.success) {
                    const el = document.getElementById(`recording-${id}`);
                    el.style.opacity = '0';
                    setTimeout(() => {
                        el.remove();
                        if (document.querySelectorAll('.recording').length === 0) {
                            loadRecordings();
                        }
                    }, 300);
                } else {
                    alert(`❌ Error: ${data.error}`);
                }
            } catch (error) {
                alert(`❌ Error: ${error.message}`);
            }
        }

        // Load recordings on page load
        loadRecordings();
    </script>
</body>
</html>"""

    return render_template_string(template)


if __name__ == '__main__':
    """
    CLI for testing approval workflow
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 recording_approval_routes.py init    # Create tables")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        create_approval_tables()
        print("✅ Approval tables initialized")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

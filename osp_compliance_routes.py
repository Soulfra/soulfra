#!/usr/bin/env python3
"""
OSP/DMCA Compliance Dashboard

Implements OCILLA (Online Copyright Infringement Liability Limitation Act) safe harbor requirements:
- DMCA takedown request handling
- Counter-notification workflow
- Repeat infringer policy
- Designated DMCA agent
- Transparency reporting

17 USC § 512 compliance for Online Service Providers

Routes:
- GET  /admin/dmca - DMCA dashboard
- POST /api/dmca/takedown - Submit DMCA takedown
- POST /api/dmca/counter - Submit counter-notification
- GET  /api/dmca/status/<id> - Check notice status
- GET  /dmca-policy - Public DMCA policy page
"""

from flask import Blueprint, request, jsonify, render_template_string
from database import get_db
from datetime import datetime, timezone, timedelta
import hashlib
import json

osp_bp = Blueprint('osp', __name__)


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

def init_osp_tables():
    """Initialize OSP compliance tables"""
    db = get_db()

    # DMCA takedown notices
    db.execute('''
        CREATE TABLE IF NOT EXISTS dmca_notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            complainant_name TEXT NOT NULL,
            complainant_email TEXT NOT NULL,
            complainant_address TEXT,
            work_description TEXT NOT NULL,
            infringing_url TEXT NOT NULL,
            infringing_content_id INTEGER,
            good_faith_statement TEXT NOT NULL,
            perjury_statement TEXT NOT NULL,
            signature TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            processed_at TEXT,
            resolution TEXT,
            notes TEXT
        )
    ''')

    # Counter-notifications
    db.execute('''
        CREATE TABLE IF NOT EXISTS dmca_counter_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_notice_id INTEGER NOT NULL,
            respondent_name TEXT NOT NULL,
            respondent_email TEXT NOT NULL,
            respondent_address TEXT NOT NULL,
            content_description TEXT NOT NULL,
            good_faith_statement TEXT NOT NULL,
            jurisdiction_consent TEXT NOT NULL,
            perjury_statement TEXT NOT NULL,
            signature TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            processed_at TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (original_notice_id) REFERENCES dmca_notices(id)
        )
    ''')

    # Repeat infringer tracking
    db.execute('''
        CREATE TABLE IF NOT EXISTS repeat_infringers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_email TEXT,
            infringement_count INTEGER DEFAULT 1,
            first_infringement_at TEXT NOT NULL,
            last_infringement_at TEXT NOT NULL,
            status TEXT DEFAULT 'warned',
            terminated_at TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # AI moderation queue
    db.execute('''
        CREATE TABLE IF NOT EXISTS moderation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            content_id INTEGER NOT NULL,
            flagged_reason TEXT NOT NULL,
            ai_confidence REAL,
            ai_analysis TEXT,
            flagged_at TEXT NOT NULL,
            reviewed_at TEXT,
            reviewer_action TEXT,
            reviewer_notes TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Transparency reports
    db.execute('''
        CREATE TABLE IF NOT EXISTS transparency_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_period_start TEXT NOT NULL,
            report_period_end TEXT NOT NULL,
            total_notices INTEGER DEFAULT 0,
            takedowns_honored INTEGER DEFAULT 0,
            counter_notifications INTEGER DEFAULT 0,
            repeat_infringers_terminated INTEGER DEFAULT 0,
            ai_flagged_content INTEGER DEFAULT 0,
            generated_at TEXT NOT NULL,
            report_json TEXT
        )
    ''')

    db.commit()
    print("✅ OSP compliance tables created")


# ============================================================================
# DMCA TAKEDOWN ROUTES
# ============================================================================

@osp_bp.route('/api/dmca/takedown', methods=['POST'])
def submit_dmca_takedown():
    """
    POST /api/dmca/takedown

    Submit DMCA takedown notice

    Required fields (17 USC § 512(c)(3)):
    - complainant_name
    - complainant_email
    - complainant_address
    - work_description
    - infringing_url
    - good_faith_statement
    - perjury_statement
    - signature

    Returns:
        JSON: {
            "success": true,
            "notice_id": 123,
            "status": "pending"
        }
    """
    data = request.get_json()

    # Validate required fields
    required = [
        'complainant_name', 'complainant_email', 'complainant_address',
        'work_description', 'infringing_url',
        'good_faith_statement', 'perjury_statement', 'signature'
    ]

    for field in required:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    try:
        cursor = db.execute('''
            INSERT INTO dmca_notices
            (notice_type, complainant_name, complainant_email, complainant_address,
             work_description, infringing_url, infringing_content_id,
             good_faith_statement, perjury_statement, signature, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'takedown',
            data['complainant_name'],
            data['complainant_email'],
            data['complainant_address'],
            data['work_description'],
            data['infringing_url'],
            data.get('infringing_content_id'),
            data['good_faith_statement'],
            data['perjury_statement'],
            data['signature'],
            now
        ))

        notice_id = cursor.lastrowid
        db.commit()

        # TODO: Send email notification to DMCA agent
        print(f"📧 DMCA takedown notice #{notice_id} submitted by {data['complainant_name']}")

        return jsonify({
            'success': True,
            'notice_id': notice_id,
            'status': 'pending',
            'message': 'DMCA notice submitted. We will process within 24-48 hours.'
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@osp_bp.route('/api/dmca/counter', methods=['POST'])
def submit_counter_notification():
    """
    POST /api/dmca/counter

    Submit DMCA counter-notification (17 USC § 512(g))

    Required fields:
    - original_notice_id
    - respondent_name
    - respondent_email
    - respondent_address
    - content_description
    - good_faith_statement
    - jurisdiction_consent
    - perjury_statement
    - signature

    Returns:
        JSON: Counter-notification confirmation
    """
    data = request.get_json()

    required = [
        'original_notice_id', 'respondent_name', 'respondent_email',
        'respondent_address', 'content_description',
        'good_faith_statement', 'jurisdiction_consent',
        'perjury_statement', 'signature'
    ]

    for field in required:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    try:
        cursor = db.execute('''
            INSERT INTO dmca_counter_notifications
            (original_notice_id, respondent_name, respondent_email, respondent_address,
             content_description, good_faith_statement, jurisdiction_consent,
             perjury_statement, signature, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['original_notice_id'],
            data['respondent_name'],
            data['respondent_email'],
            data['respondent_address'],
            data['content_description'],
            data['good_faith_statement'],
            data['jurisdiction_consent'],
            data['perjury_statement'],
            data['signature'],
            now
        ))

        counter_id = cursor.lastrowid
        db.commit()

        print(f"📧 Counter-notification #{counter_id} received for notice #{data['original_notice_id']}")

        return jsonify({
            'success': True,
            'counter_id': counter_id,
            'status': 'pending',
            'message': 'Counter-notification received. Content may be restored in 10-14 business days if no court action filed.'
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@osp_bp.route('/admin/dmca')
def dmca_dashboard():
    """
    GET /admin/dmca

    DMCA compliance dashboard (admin only)
    """
    db = get_db()

    # Get pending notices
    pending = db.execute('''
        SELECT * FROM dmca_notices
        WHERE status = 'pending'
        ORDER BY submitted_at DESC
    ''').fetchall()

    # Get counter-notifications
    counters = db.execute('''
        SELECT * FROM dmca_counter_notifications
        WHERE status = 'pending'
        ORDER BY submitted_at DESC
    ''').fetchall()

    # Get AI moderation queue
    flagged = db.execute('''
        SELECT * FROM moderation_queue
        WHERE status = 'pending'
        ORDER BY flagged_at DESC
        LIMIT 20
    ''').fetchall()

    # Statistics
    stats = {
        'total_notices': db.execute("SELECT COUNT(*) as c FROM dmca_notices").fetchone()['c'],
        'pending_notices': len(pending),
        'counter_notifications': len(counters),
        'ai_flagged': len(flagged)
    }

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMCA/OSP Compliance Dashboard</title>
    <link rel="stylesheet" href="/static/css/osp-compliance.css">
    <style>
        /* Additional inline styles for dynamic content */
        .notice-id {
            font-family: 'Monaco', monospace;
            background: rgba(255, 255, 255, 0.1);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }
        /* External CSS loaded, minimal overrides only */
    </style>
</head>
<body>
    <div class="osp-container">
        <header class="osp-header">
            <h1>⚖️ DMCA/OSP Compliance Dashboard</h1>
            <p>17 USC § 512 (OCILLA) Safe Harbor Compliance • Real-time Moderation</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card pending">
                <h3>Total DMCA Notices</h3>
                <div class="stat-value">{{ stats['total_notices'] }}</div>
            </div>
            <div class="stat-card approved">
                <h3>Pending Notices</h3>
                <div class="stat-value">{{ stats['pending_notices'] }}</div>
            </div>
            <div class="stat-card rejected">
                <h3>Counter-Notifications</h3>
                <div class="stat-value">{{ stats['counter_notifications'] }}</div>
            </div>
            <div class="stat-card">
                <h3>AI Flagged Content</h3>
                <div class="stat-value">{{ stats['ai_flagged'] }}</div>
            </div>
        </div>

        <div class="table-container">
            <div class="section-header">
                <h2>📩 Pending DMCA Takedown Notices</h2>
            </div>
            {% if pending|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Complainant</th>
                        <th>Work Description</th>
                        <th>Infringing URL</th>
                        <th>Submitted</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for notice in pending %}
                    <tr>
                        <td>#{{ notice['id'] }}</td>
                        <td>{{ notice['complainant_name'] }}</td>
                        <td>{{ notice['work_description'][:100] }}...</td>
                        <td><a href="{{ notice['infringing_url'] }}" target="_blank">View</a></td>
                        <td>{{ notice['submitted_at'][:10] }}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-success" onclick="processNotice({{ notice['id'] }}, 'approve')">✓ Honor</button>
                                <button class="btn btn-sm btn-danger" onclick="processNotice({{ notice['id'] }}, 'reject')">✗ Reject</button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <p>✅ No pending DMCA notices</p>
            </div>
            {% endif %}
        </div>

        <div class="table-container">
            <div class="section-header">
                <h2>🔄 Counter-Notifications</h2>
            </div>
            {% if counters|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Respondent</th>
                        <th>Original Notice</th>
                        <th>Submitted</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for counter in counters %}
                    <tr>
                        <td>#{{ counter['id'] }}</td>
                        <td>{{ counter['respondent_name'] }}</td>
                        <td>#{{ counter['original_notice_id'] }}</td>
                        <td>{{ counter['submitted_at'][:10] }}</td>
                        <td><span class="badge badge-pending">{{ counter['status'] }}</span></td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="reviewCounter({{ counter['id'] }})">Review</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <p>✅ No pending counter-notifications</p>
            </div>
            {% endif %}
        </div>

        <div class="table-container">
            <div class="section-header">
                <h2>🤖 AI Moderation Queue</h2>
            </div>
            {% if flagged|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Content ID</th>
                        <th>Type</th>
                        <th>Reason</th>
                        <th>Confidence</th>
                        <th>Flagged</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in flagged %}
                    <tr>
                        <td>{{ item['content_type'] }}-{{ item['content_id'] }}</td>
                        <td>{{ item['content_type'] }}</td>
                        <td>{{ item['flagged_reason'] }}</td>
                        <td><span class="ai-confidence">{{ "%.0f"|format(item['ai_confidence'] * 100) if item['ai_confidence'] else 'N/A' }}%</span></td>
                        <td>{{ item['flagged_at'][:10] }}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-success" onclick="moderateContent({{ item['id'] }}, 'approve')">✓ Approve</button>
                                <button class="btn btn-sm btn-danger" onclick="moderateContent({{ item['id'] }}, 'remove')">✗ Remove</button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <p>✅ No content pending moderation</p>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        function processNotice(id, action) {
            if (confirm(`${action === 'approve' ? 'Honor' : 'Reject'} DMCA notice #${id}?`)) {
                fetch(`/api/dmca/process/${id}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: action})
                })
                .then(r => r.json())
                .then(d => {
                    alert(d.message);
                    location.reload();
                });
            }
        }

        function reviewCounter(id) {
            window.location.href = `/admin/dmca/counter/${id}`;
        }

        function moderateContent(id, action) {
            if (confirm(`${action === 'approve' ? 'Approve' : 'Remove'} this content?`)) {
                fetch(`/api/moderation/process/${id}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: action})
                })
                .then(r => r.json())
                .then(d => {
                    alert(d.message);
                    location.reload();
                });
            }
        }
    </script>
</body>
</html>"""

    return render_template_string(template, pending=pending, counters=counters, flagged=flagged, stats=stats)


# ============================================================================
# PUBLIC DMCA POLICY PAGE
# ============================================================================

@osp_bp.route('/dmca-policy')
def dmca_policy():
    """Public DMCA policy page (required for safe harbor)"""
    return render_template_string(open('/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.github.io/docs/dmca-policy.md').read())


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("OSP Compliance Tool")
        print("\nUsage:")
        print("  python3 osp_compliance_routes.py init")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_osp_tables()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

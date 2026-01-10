#!/usr/bin/env python3
"""
Gallery Routes - Flask routes for QR galleries and DM scanning

Adds missing routes to app.py for serving QR galleries and handling
QR scan analytics (lineage tracking, device detection, location).

Routes:
- /gallery/<slug> - Serve QR gallery page
- /gallery/<slug>/track - Track gallery view + analytics
- /dm/scan - Handle DM QR code scan
- /qr/track/<qr_id> - Track any QR code scan

Analytics captured:
- Device type (iOS, Android, Desktop)
- User agent
- IP address
- Location (city, country) via IP geolocation
- Referrer
- Lineage (previous_scan_id) for viral tracking

Usage:
    # Import into app.py:
    from gallery_routes import register_gallery_routes
    register_gallery_routes(app)

    # Or run standalone server:
    python3 gallery_routes.py
"""

from flask import Flask, render_template_string, request, jsonify, redirect, abort
from pathlib import Path
from database import get_db
from datetime import datetime
import hashlib
import json


# =============================================================================
# DM Chat Template
# =============================================================================

DM_CHAT_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DM Chat - Soulfra</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 1.3rem; color: #333; margin-bottom: 0.5rem; }
        .header p { color: #666; font-size: 0.9rem; }
        .chat-container {
            flex: 1;
            padding: 1rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .message {
            max-width: 80%;
            padding: 0.8rem 1.2rem;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user {
            background: #007AFF;
            color: white;
            align-self: flex-end;
            margin-left: auto;
        }
        .message.ai {
            background: white;
            color: #333;
            align-self: flex-start;
        }
        .input-container {
            background: white;
            padding: 1rem;
            display: flex;
            gap: 0.5rem;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }
        #messageInput {
            flex: 1;
            padding: 0.8rem 1rem;
            border: 2px solid #ddd;
            border-radius: 24px;
            font-size: 1rem;
            outline: none;
        }
        #messageInput:focus { border-color: #007AFF; }
        #sendBtn {
            padding: 0.8rem 1.5rem;
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 24px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }
        #sendBtn:disabled { background: #ccc; cursor: not-allowed; }
        .error { text-align: center; color: white; padding: 1rem; background: rgba(255, 59, 48, 0.9); margin: 1rem; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>💬 DM with {{ author_name }}</h1>
        <p>Scan #{{ scan_id }} • {{ time_left }}s remaining</p>
    </div>

    <div class="chat-container" id="chatContainer">
        <div class="message ai">
            Hi! I'm connected via DM QR code. How can I help you?
        </div>
    </div>

    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type a message..." />
        <button id="sendBtn">Send</button>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const token = '{{ token }}';

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message to UI
            const userMsg = document.createElement('div');
            userMsg.className = 'message user';
            userMsg.textContent = message;
            chatContainer.appendChild(userMsg);
            messageInput.value = '';
            sendBtn.disabled = true;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                // Call AI (using same chat API endpoint, but with token for DM tracking)
                const response = await fetch('/api/dm/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token, question: message })
                });

                const data = await response.json();

                if (data.success) {
                    const aiMsg = document.createElement('div');
                    aiMsg.className = 'message ai';
                    aiMsg.textContent = data.answer;
                    chatContainer.appendChild(aiMsg);
                } else {
                    throw new Error(data.error || 'Failed to get response');
                }
            } catch (error) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error';
                errorMsg.textContent = 'Error: ' + error.message;
                chatContainer.appendChild(errorMsg);
            }

            sendBtn.disabled = false;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>'''

# =============================================================================
# Device Detection
# =============================================================================

def detect_device_type(user_agent):
    """
    Detect device type from User-Agent header

    Args:
        user_agent: User-Agent string

    Returns:
        str: 'iOS', 'Android', 'Desktop', or 'Unknown'
    """
    ua = user_agent.lower()

    if 'iphone' in ua or 'ipad' in ua:
        return 'iOS'
    elif 'android' in ua:
        return 'Android'
    elif 'mobile' in ua:
        return 'Mobile'
    elif 'windows' in ua or 'mac' in ua or 'linux' in ua:
        return 'Desktop'
    else:
        return 'Unknown'


def get_ip_location(ip_address):
    """
    Get location from IP address

    Args:
        ip_address: IP address string

    Returns:
        dict with city, country, or None
    """
    # For MVP, return None (would integrate with ip-api.com or ipinfo.io in production)
    # Free tier: http://ip-api.com/json/{ip}
    return {
        'city': None,
        'country': None
    }


# =============================================================================
# QR Scan Tracking
# =============================================================================

def track_qr_scan(qr_code_id, qr_type='gallery', entity_id=None, previous_scan_id=None):
    """
    Track QR code scan with analytics

    Args:
        qr_code_id: ID of QR code in qr_codes table
        qr_type: Type of QR (gallery, dm, post, etc.)
        entity_id: ID of related entity (post_id, etc.)
        previous_scan_id: ID of previous scan (for lineage tracking)

    Returns:
        dict with scan_id and analytics
    """
    # Get request data
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    referrer = request.headers.get('Referer', '')

    # Detect device
    device_type = detect_device_type(user_agent)

    # Get location (stub for MVP)
    location = get_ip_location(ip_address)

    # Insert scan record
    db = get_db()

    # Check if qr_code exists, if not create it
    qr_code = db.execute('SELECT id FROM qr_codes WHERE code_type = ? AND code_data = ?',
                         (qr_type, str(entity_id) if entity_id else '')).fetchone()

    if not qr_code:
        # Create QR code entry (let database handle id, created_at, total_scans defaults)
        target_url = request.url
        db.execute('''
            INSERT INTO qr_codes (code_type, code_data, target_url)
            VALUES (?, ?, ?)
        ''', (qr_type, str(entity_id) if entity_id else '', target_url))
        db.commit()

        # Get the auto-generated ID
        qr_code = db.execute('SELECT id FROM qr_codes WHERE code_type = ? AND code_data = ?',
                             (qr_type, str(entity_id) if entity_id else '')).fetchone()
        qr_code_id = qr_code['id']
    else:
        qr_code_id = qr_code['id']

    # Insert scan
    db.execute('''
        INSERT INTO qr_scans
        (qr_code_id, scanned_at, ip_address, location_city, location_country,
         device_type, user_agent, referrer, previous_scan_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (qr_code_id, datetime.now(), ip_address, location.get('city'), location.get('country'),
          device_type, user_agent, referrer, previous_scan_id))

    scan_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Update QR code total_scans
    db.execute('''
        UPDATE qr_codes
        SET total_scans = total_scans + 1, last_scanned_at = ?
        WHERE id = ?
    ''', (datetime.now(), qr_code_id))

    # Update qr_galleries view_count if gallery
    if qr_type == 'gallery' and entity_id:
        db.execute('''
            UPDATE qr_galleries
            SET view_count = view_count + 1
            WHERE post_id = ?
        ''', (entity_id,))

    db.commit()
    db.close()

    return {
        'scan_id': scan_id,
        'device_type': device_type,
        'ip_address': ip_address,
        'location': location,
        'previous_scan_id': previous_scan_id
    }


# =============================================================================
# Gallery Routes
# =============================================================================

def gallery_view(slug):
    """
    Serve QR gallery page

    Args:
        slug: Post slug

    Returns:
        HTML page or 404
    """
    # Get post
    db = get_db()
    post = db.execute('SELECT id FROM posts WHERE slug = ?', (slug,)).fetchone()

    if not post:
        db.close()
        abort(404, "Gallery not found")

    post_id = post['id']

    # Check if gallery HTML exists
    gallery_path = Path(f"output/galleries/{slug}.html")

    if not gallery_path.exists():
        db.close()
        abort(404, f"Gallery not generated yet. Run: python3 qr_gallery_system.py --post {post_id}")

    # Get or create QR code ID for tracking
    qr_gallery = db.execute('SELECT id FROM qr_galleries WHERE post_id = ?', (post_id,)).fetchone()

    if qr_gallery:
        qr_code_id = qr_gallery['id']
    else:
        # Create QR gallery entry
        db.execute('''
            INSERT INTO qr_galleries (post_id, gallery_slug, view_count, created_at)
            VALUES (?, ?, 0, ?)
        ''', (post_id, slug, datetime.now()))
        db.commit()
        qr_code_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    db.close()

    # Track scan (check for previous_scan_id in URL params)
    previous_scan_id = request.args.get('ref')  # ?ref=<previous_scan_id>
    scan_data = track_qr_scan(qr_code_id, 'gallery', post_id, previous_scan_id)

    # Read gallery HTML
    html_content = gallery_path.read_text()

    # Inject scan_id into HTML for sharing (add to share buttons)
    scan_id = scan_data['scan_id']
    share_url = f"{request.host_url}gallery/{slug}?ref={scan_id}"

    # Replace share URL in HTML (simple injection)
    html_content = html_content.replace(
        f'https://soulfra.com/gallery/{slug}',
        share_url
    )

    return html_content


def dm_scan_view():
    """
    Handle DM QR code scan

    Query params:
        token: DM token from dm_via_qr.py

    Returns:
        HTML chat interface
    """
    token = request.args.get('token')

    if not token:
        return render_template_string('''
        <!DOCTYPE html>
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error</title></head><body style="font-family: sans-serif; padding: 2rem; text-align: center;">
        <h1>❌ No Token</h1><p>Invalid DM QR code</p></body></html>
        '''), 400

    # Track scan
    qr_code_id = hashlib.sha256(token.encode()).hexdigest()[:16]
    scan_data = track_qr_scan(qr_code_id, 'dm', entity_id=None)

    # Verify token (use dm_via_qr.py function)
    from dm_via_qr import verify_dm_token

    verification = verify_dm_token(token)

    if not verification or not verification.get('valid', False):
        error_msg = verification.get('error', 'Invalid token format') if verification else 'Invalid token format'
        return render_template_string('''
        <!DOCTYPE html>
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Token Expired</title></head><body style="font-family: sans-serif; padding: 2rem; text-align: center;">
        <h1>⏰ Token Expired</h1>
        <p>This DM QR code has expired. Please request a new one.</p>
        <p style="color: #666;">{{ error }}</p>
        </body></html>
        ''', error=error_msg), 403

    # Get author info
    db = get_db()
    author = db.execute('SELECT username, email FROM users WHERE id = ?',
                       (verification['user_id'],)).fetchone()
    db.close()

    author_name = author['username'] if author else f"User #{verification['user_id']}"
    time_left = verification['time_remaining']

    # Return HTML chat interface
    return render_template_string(DM_CHAT_TEMPLATE,
                                 author_name=author_name,
                                 time_left=time_left,
                                 token=token,
                                 scan_id=scan_data['scan_id'])


def track_qr_view(qr_id):
    """
    Generic QR code tracking endpoint

    Args:
        qr_id: QR code ID

    Returns:
        JSON with tracking info
    """
    previous_scan_id = request.args.get('ref')
    scan_data = track_qr_scan(qr_id, 'generic', entity_id=None, previous_scan_id=previous_scan_id)

    return jsonify({
        'success': True,
        'scan_id': scan_data['scan_id'],
        'device': scan_data['device_type'],
        'share_url': f"{request.host_url}qr/track/{qr_id}?ref={scan_data['scan_id']}"
    })


def galleries_index_view():
    """
    List all QR galleries

    Returns:
        HTML page with all galleries
    """
    db = get_db()

    # Get all galleries with post info
    galleries = db.execute('''
        SELECT
            g.id,
            g.gallery_slug,
            g.view_count,
            g.created_at,
            p.title,
            p.slug as post_slug
        FROM qr_galleries g
        JOIN posts p ON g.post_id = p.id
        ORDER BY g.created_at DESC
    ''').fetchall()

    db.close()

    # Generate HTML
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Galleries - Soulfra</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
        }
        .gallery-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }
        .gallery-card:hover {
            transform: translateY(-5px);
        }
        .gallery-card h2 {
            margin-bottom: 1rem;
            color: #333;
            font-size: 1.3rem;
        }
        .gallery-meta {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .gallery-link {
            display: inline-block;
            background: #4a90e2;
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: opacity 0.3s;
        }
        .gallery-link:hover {
            opacity: 0.9;
        }
        .nav-link {
            color: white;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="nav-link">← Back to Home</a>
        <h1>🖼️ QR Galleries</h1>
        <div class="gallery-grid">
'''

    for gallery in galleries:
        html += f'''
            <div class="gallery-card">
                <h2>{gallery['title']}</h2>
                <div class="gallery-meta">
                    📊 {gallery['view_count']} views<br>
                    🗓️ Created: {gallery['created_at'][:10]}
                </div>
                <a href="/gallery/{gallery['gallery_slug']}" class="gallery-link">
                    View Gallery →
                </a>
            </div>
'''

    html += '''
        </div>
    </div>
</body>
</html>
'''

    return html


# =============================================================================
# Flask Route Registration
# =============================================================================

def register_gallery_routes(app):
    """
    Register gallery routes with Flask app

    Args:
        app: Flask app instance
    """
    @app.route('/galleries')
    def galleries_index():
        return galleries_index_view()

    @app.route('/gallery/<slug>')
    def gallery(slug):
        return gallery_view(slug)

    @app.route('/dm/scan')
    def dm_scan():
        return dm_scan_view()

    @app.route('/qr/track/<qr_id>')
    def qr_track(qr_id):
        return track_qr_view(qr_id)

    print("✅ Gallery routes registered:")
    print("   - /galleries")
    print("   - /gallery/<slug>")
    print("   - /dm/scan")
    print("   - /qr/track/<qr_id>")


# =============================================================================
# Standalone Server (for testing)
# =============================================================================

if __name__ == '__main__':
    app = Flask(__name__)
    register_gallery_routes(app)

    print("\n" + "=" * 70)
    print("🖼️  GALLERY ROUTES SERVER")
    print("=" * 70)
    print("\nTest routes:")
    print("  http://localhost:5002/gallery/i-love-that-youre-considering-sharing-a-recipe-for")
    print("  http://localhost:5002/dm/scan?token=<token>")
    print("  http://localhost:5002/qr/track/12345")
    print()

    app.run(host='0.0.0.0', port=5002, debug=True)

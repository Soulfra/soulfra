#!/usr/bin/env python3
"""
Cross-Device Session Synchronization
Allows sessions to be synced between laptop <-> phone via QR codes

User workflow:
1. Laptop generates QR code with session token
2. Phone scans QR -> inherits session (user_id, domains, voice memos, progress)
3. Phone can generate QR -> laptop scans to pull session back
"""

from flask import Blueprint, request, jsonify, session, render_template_string
from database import get_db
import secrets
import time
from typing import Dict, Optional
import qrcode
import io
import base64

session_sync_bp = Blueprint('session_sync', __name__)


class SessionSyncManager:
    """Manage cross-device session synchronization"""

    def __init__(self):
        self.token_expiry_seconds = 300  # 5 minutes

    def generate_sync_token(self, user_id: int, session_data: Dict) -> str:
        """
        Generate a session sync token

        Args:
            user_id: User ID to sync
            session_data: Dict of session data (domains, progress, etc.)

        Returns:
            Token string (32 chars)
        """
        token = secrets.token_urlsafe(32)
        db = get_db()

        # Store token in database
        db.execute('''
            INSERT INTO session_sync_tokens (
                token, user_id, session_data,
                created_at, expires_at, is_used
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            token,
            user_id,
            str(session_data),  # Store as JSON string
            int(time.time()),
            int(time.time()) + self.token_expiry_seconds,
            0
        ))
        db.commit()

        return token

    def verify_sync_token(self, token: str) -> Optional[Dict]:
        """
        Verify and consume a sync token

        Returns:
            Dict with user_id and session_data if valid, None otherwise
        """
        db = get_db()

        token_record = db.execute('''
            SELECT user_id, session_data, expires_at, is_used
            FROM session_sync_tokens
            WHERE token = ?
        ''', (token,)).fetchone()

        if not token_record:
            return None

        # Check if expired
        if int(time.time()) > token_record['expires_at']:
            return None

        # Check if already used
        if token_record['is_used'] == 1:
            return None

        # Mark as used
        db.execute('UPDATE session_sync_tokens SET is_used = 1 WHERE token = ?', (token,))
        db.commit()

        # Parse session data
        import ast
        session_data = ast.literal_eval(token_record['session_data'])

        return {
            'user_id': token_record['user_id'],
            'session_data': session_data
        }

    def generate_qr_code(self, token: str, base_url: str) -> str:
        """
        Generate QR code image for session sync token

        Returns:
            Base64-encoded PNG image
        """
        sync_url = f"{base_url}/api/session/sync/{token}"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(sync_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()

        return f"data:image/png;base64,{img_base64}"

    def get_session_snapshot(self, user_id: int) -> Dict:
        """
        Get current session snapshot for a user

        Returns:
            Dict with user progress, domains, voice memos, etc.
        """
        db = get_db()

        # Get user info
        user = db.execute('SELECT id, email, username FROM users WHERE id = ?', (user_id,)).fetchone()

        # Get domains
        from domain_unlock_engine import get_user_domains, get_user_handle, get_primary_domain
        domains = get_user_domains(user_id)
        handle = get_user_handle(user_id)
        primary_domain = get_primary_domain(user_id)

        # Get voice recordings count
        voice_count = db.execute(
            'SELECT COUNT(*) as count FROM simple_voice_recordings WHERE user_id = ?',
            (user_id,)
        ).fetchone()['count']

        # Get ideas count
        ideas_count = db.execute(
            'SELECT COUNT(*) as count FROM ideas WHERE user_id = ?',
            (user_id,)
        ).fetchone()['count']

        return {
            'user_id': user_id,
            'email': user.get('email'),
            'username': user.get('username'),
            'handle': handle,
            'primary_domain': primary_domain['domain'] if primary_domain else None,
            'domains_count': len(domains),
            'voice_recordings': voice_count,
            'ideas_count': ideas_count,
            'timestamp': int(time.time())
        }


# Initialize manager
sync_manager = SessionSyncManager()


@session_sync_bp.route('/api/session/generate-qr', methods=['GET'])
def generate_qr():
    """
    Generate QR code for current session

    Laptop workflow:
    1. User visits /voice on laptop
    2. Clicks "Sync to Phone"
    3. QR code appears
    4. Phone scans -> inherits session
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated. Please log in first.'
        }), 401

    # Get session snapshot
    session_snapshot = sync_manager.get_session_snapshot(user_id)

    # Generate token
    token = sync_manager.generate_sync_token(user_id, session_snapshot)

    # Generate QR code
    base_url = request.url_root.rstrip('/')
    qr_image = sync_manager.generate_qr_code(token, base_url)

    return jsonify({
        'success': True,
        'token': token,
        'qr_code': qr_image,
        'expires_in': 300,  # 5 minutes
        'session_snapshot': session_snapshot,
        'sync_url': f"{base_url}/api/session/sync/{token}"
    })


@session_sync_bp.route('/api/session/sync/<token>', methods=['GET', 'POST'])
def sync_session(token: str):
    """
    Sync session from token

    Phone workflow:
    1. Scan QR code
    2. Browser opens this URL
    3. Session is created/synced
    4. Redirect to /voice
    """
    # Verify token
    token_data = sync_manager.verify_sync_token(token)

    if not token_data:
        return jsonify({
            'success': False,
            'error': 'Invalid or expired token. QR codes expire after 5 minutes.'
        }), 400

    # Set session
    session['user_id'] = token_data['user_id']
    session['synced_from_qr'] = True
    session['synced_at'] = int(time.time())

    # Add session snapshot to session
    for key, value in token_data['session_data'].items():
        session[f'snapshot_{key}'] = value

    # If GET request (from QR scan), redirect to voice page
    if request.method == 'GET':
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Session Synced!</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                    color: #66ff66;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    text-align: center;
                }}
                .sync-success {{
                    background: #1a1a1a;
                    padding: 40px;
                    border-radius: 20px;
                    border: 2px solid #66ff66;
                    max-width: 400px;
                }}
                h1 {{
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                .snapshot {{
                    background: #0a0a0a;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .snapshot-item {{
                    margin: 10px 0;
                    font-size: 14px;
                }}
                .redirect {{
                    color: #888;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="sync-success">
                <h1>✅ Synced!</h1>
                <p>Your session has been synchronized to this device.</p>

                <div class="snapshot">
                    <div class="snapshot-item">👤 Handle: {token_data['session_data'].get('handle', 'N/A')}</div>
                    <div class="snapshot-item">💎 Domains: {token_data['session_data'].get('domains_count', 0)}</div>
                    <div class="snapshot-item">🎙️ Recordings: {token_data['session_data'].get('voice_recordings', 0)}</div>
                    <div class="snapshot-item">💡 Ideas: {token_data['session_data'].get('ideas_count', 0)}</div>
                </div>

                <p class="redirect">Redirecting to voice page in 2 seconds...</p>
            </div>

            <script>
                setTimeout(() => {{
                    window.location.href = '/voice';
                }}, 2000);
            </script>
        </body>
        </html>
        """

    # If POST request (API call), return JSON
    return jsonify({
        'success': True,
        'message': 'Session synced successfully',
        'user_id': token_data['user_id'],
        'session_data': token_data['session_data']
    })


@session_sync_bp.route('/api/session/status', methods=['GET'])
def session_status():
    """
    Get current session status

    Returns:
        - authenticated: bool
        - user_id: int
        - synced_from_qr: bool
        - session_data: dict
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'success': True,
            'authenticated': False
        })

    # Get current session snapshot
    snapshot = sync_manager.get_session_snapshot(user_id)

    return jsonify({
        'success': True,
        'authenticated': True,
        'user_id': user_id,
        'synced_from_qr': session.get('synced_from_qr', False),
        'synced_at': session.get('synced_at'),
        'session_data': snapshot
    })


# Initialize session_sync_tokens table
def init_session_sync_db():
    """Create session_sync_tokens table if it doesn't exist"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS session_sync_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            session_data TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            is_used INTEGER DEFAULT 0,
            device_fingerprint TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create index for fast token lookup
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_session_tokens_token
        ON session_sync_tokens(token)
    ''')

    db.commit()
    print("✅ Session sync database initialized")


if __name__ == '__main__':
    # Test token generation
    print("Testing Session Sync Manager...")

    manager = SessionSyncManager()

    # Test token
    test_data = {
        'handle': '@soulfra',
        'domains_count': 3,
        'voice_recordings': 5
    }

    token = manager.generate_sync_token(1, test_data)
    print(f"✅ Generated token: {token}")

    # Verify token
    verified = manager.verify_sync_token(token)
    print(f"✅ Verified: {verified}")

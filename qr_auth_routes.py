"""
QR Authentication Routes - Passwordless device-based login via QR codes

Routes:
- GET /api/qr/generate - Generate QR code for current user
- GET /qr/auth/<token> - Authenticate via QR code scan
- POST /api/qr/verify - Verify QR auth token
- GET /api/qr/device-auth - Get or create anonymous device auth

Usage in app.py:
    from qr_auth_routes import register_qr_auth_routes
    register_qr_auth_routes(app)
"""

from flask import jsonify, request, redirect, session, render_template_string
from qr_auth import (
    generate_auth_token,
    verify_auth_token,
    authenticate_with_qr,
    init_qr_auth_tables,
    save_qr_auth_code,
    get_user_by_username,
    increment_qr_usage
)
from database import get_db
import secrets


def register_qr_auth_routes(app):
    """Register QR authentication routes with Flask app"""

    # Initialize QR auth tables
    init_qr_auth_tables()

    @app.route('/api/qr/generate', methods=['POST'])
    def api_generate_qr():
        """
        Generate QR auth code for user

        POST body:
        {
            "username": "alice",  # Optional if logged in
            "ttl_seconds": 3600,  # Optional, default 1 hour
            "one_time": false     # Optional, default false
        }

        Returns:
        {
            "success": true,
            "token": "...",
            "qr_url": "http://localhost:5001/qr/auth/...",
            "expires_at": 1234567890
        }
        """
        data = request.json or {}

        # Get username from session or request
        username = data.get('username') or session.get('username')

        if not username:
            return jsonify({
                'success': False,
                'error': 'No username provided and user not logged in'
            }), 401

        ttl_seconds = data.get('ttl_seconds', 3600)
        one_time = data.get('one_time', False)

        # Get user
        user = get_user_by_username(username)

        if not user:
            return jsonify({
                'success': False,
                'error': f'User {username} not found'
            }), 404

        try:
            # Generate token
            token = generate_auth_token(
                user_id=user['id'],
                ttl_seconds=ttl_seconds,
                one_time=one_time
            )

            # Build QR URL
            qr_url = f"{request.host_url}qr/auth/{token}"

            # Decode token to get expiration
            token_data = verify_auth_token(token)

            # Save to database
            save_qr_auth_code(
                user_id=user['id'],
                token=token,
                expires_at=token_data['expires_at'],
                one_time=one_time
            )

            return jsonify({
                'success': True,
                'token': token,
                'qr_url': qr_url,
                'expires_at': token_data['expires_at']
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/qr/auth/<token>')
    def qr_auth_handler(token):
        """
        QR code authentication handler
        User scans QR → This endpoint → Auto-login

        Returns HTML page confirming login
        """
        # Verify and authenticate
        user = authenticate_with_qr(token)

        if not user:
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>QR Auth Failed</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="font-family: monospace; padding: 2rem; background: #ff006e; color: #fff; text-align: center;">
                    <h1>❌ Invalid QR Code</h1>
                    <p>This QR code is invalid, expired, or already used.</p>
                    <a href="/" style="color: #fff;">Go Home</a>
                </body>
                </html>
            '''), 401

        # Log user in
        session['user_id'] = user['id']
        session['username'] = user['username']

        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>QR Login Success</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="refresh" content="2;url=/">
            </head>
            <body style="font-family: monospace; padding: 2rem; background: #00C49A; color: #fff; text-align: center;">
                <h1>✅ Logged In</h1>
                <p>Welcome, {{ username }}!</p>
                <p>Redirecting to homepage...</p>
            </body>
            </html>
        ''', username=user['username'])

    @app.route('/api/qr/verify', methods=['POST'])
    def api_verify_qr():
        """
        Verify QR auth token without logging in

        POST body:
        {
            "token": "..."
        }

        Returns:
        {
            "success": true,
            "valid": true,
            "user_id": 42,
            "expires_at": 1234567890
        }
        """
        data = request.json
        token = data.get('token')

        if not token:
            return jsonify({
                'success': False,
                'error': 'Token required'
            }), 400

        token_data = verify_auth_token(token)

        if not token_data:
            return jsonify({
                'success': True,
                'valid': False
            })

        return jsonify({
            'success': True,
            'valid': True,
            'user_id': token_data['user_id'],
            'expires_at': token_data['expires_at']
        })

    @app.route('/api/qr/device-auth', methods=['POST'])
    def api_device_auth():
        """
        Get or create anonymous device authentication

        POST body:
        {
            "device_fingerprint": "..."  # Browser fingerprint
        }

        Returns:
        {
            "success": true,
            "device_id": "abc123",
            "device_token": "...",
            "qr_url": "..."
        }

        If device exists, returns existing token.
        If new device, creates anonymous user and returns new token.
        """
        data = request.json
        device_fingerprint = data.get('device_fingerprint')

        if not device_fingerprint:
            return jsonify({
                'success': False,
                'error': 'device_fingerprint required'
            }), 400

        db = get_db()
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        # Check if device exists
        cursor = db.execute('''
            SELECT * FROM devices
            WHERE fingerprint_hash = ?
        ''', (device_fingerprint,))

        device = cursor.fetchone()

        if device:
            # Existing device - return token
            return jsonify({
                'success': True,
                'device_id': device['device_id'],
                'device_token': device['device_token'],
                'user_id': device['user_id']
            })

        # New device - create anonymous user
        device_id = secrets.token_urlsafe(16)
        device_token = secrets.token_urlsafe(32)

        # Create anonymous user
        username = f"device_{device_id[:8]}"
        email = f"{username}@device.local"

        db.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_ai_persona)
            VALUES (?, ?, ?, 0, 0)
        ''', (username, email, 'device_auth'))

        user_id = db.lastrowid

        # Create device entry
        db.execute('''
            INSERT INTO devices (
                device_id, device_token, device_type, user_id,
                fingerprint_hash, fingerprint_data, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (device_id, device_token, 'web', user_id, device_fingerprint, '{}'))

        db.commit()

        # Generate QR auth token for device
        token = generate_auth_token(user_id=user_id, ttl_seconds=86400)  # 24 hours
        qr_url = f"{request.host_url}qr/auth/{token}"

        # Save QR code
        token_data = verify_auth_token(token)
        save_qr_auth_code(
            user_id=user_id,
            token=token,
            expires_at=token_data['expires_at'],
            one_time=False
        )

        return jsonify({
            'success': True,
            'device_id': device_id,
            'device_token': device_token,
            'user_id': user_id,
            'username': username,
            'qr_url': qr_url
        })

    print("✅ QR Authentication routes registered:")
    print("   - POST /api/qr/generate (Generate QR for user)")
    print("   - GET /qr/auth/<token> (Scan to login)")
    print("   - POST /api/qr/verify (Verify token)")
    print("   - POST /api/qr/device-auth (Anonymous device auth)")

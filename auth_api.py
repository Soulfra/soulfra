#!/usr/bin/env python3
"""
JSON API endpoints for authentication

Routes:
- POST /api/auth/login - Login with username/password, returns JWT token
- POST /api/auth/register - Create new account
- POST /api/auth/logout - Logout (invalidate token)
- POST /api/auth/forgot-password - Send password reset email
- GET /api/auth/me - Get current user info
"""

from flask import Blueprint, jsonify, request, session
from database import get_db
import hashlib
import secrets
import time

auth_api_bp = Blueprint('auth_api', __name__)


def hash_password(password):
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(user, password):
    """Verify password against hashed password"""
    return user['password_hash'] == hash_password(password)


def generate_token():
    """Generate random auth token"""
    return secrets.token_urlsafe(32)


@auth_api_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """
    Login API endpoint

    Request JSON:
        {
            "username": "admin",
            "password": "password123"
        }

    Response:
        {
            "success": true,
            "token": "abc123...",
            "user": {
                "id": 1,
                "username": "admin",
                "display_name": "Admin User"
            }
        }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Username and password are required'
        }), 400

    db = get_db()

    # Get user
    user = db.execute('''
        SELECT id, username, display_name, password_hash, is_admin
        FROM users
        WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        return jsonify({
            'success': False,
            'error': 'Invalid username or password'
        }), 401

    # Verify password
    if not verify_password(user, password):
        return jsonify({
            'success': False,
            'error': 'Invalid username or password'
        }), 401

    # Generate auth token
    token = generate_token()

    # Store session in database (simple token-based auth)
    db.execute('''
        INSERT INTO auth_tokens (user_id, token, created_at, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (user['id'], token, int(time.time()), int(time.time()) + 86400 * 30))  # 30 days
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'is_admin': user['is_admin']
        }
    })


@auth_api_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """
    Register new user

    Request JSON:
        {
            "username": "newuser",
            "password": "password123",
            "display_name": "New User"
        }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    display_name = data.get('display_name', '').strip() or username

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Username and password are required'
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }), 400

    db = get_db()

    # Check if username exists
    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        db.close()
        return jsonify({
            'success': False,
            'error': 'Username already exists'
        }), 400

    # Create user
    password_hash = hash_password(password)
    db.execute('''
        INSERT INTO users (username, email, display_name, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, email, display_name, password_hash, int(time.time())))
    db.commit()

    # Get new user
    user = db.execute('SELECT id, username, display_name FROM users WHERE username = ?', (username,)).fetchone()

    # Generate token
    token = generate_token()
    db.execute('''
        INSERT INTO auth_tokens (user_id, token, created_at, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (user['id'], token, int(time.time()), int(time.time()) + 86400 * 30))
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name']
        }
    })


@auth_api_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout - invalidate token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({'success': False, 'error': 'No token provided'}), 401

    db = get_db()
    db.execute('DELETE FROM auth_tokens WHERE token = ?', (token,))
    db.commit()
    db.close()

    return jsonify({'success': True})


@auth_api_bp.route('/api/auth/me', methods=['GET'])
def api_me():
    """Get current user info from token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    db = get_db()

    # Get user from token
    result = db.execute('''
        SELECT u.id, u.username, u.display_name, u.is_admin, u.email,
               t.expires_at
        FROM auth_tokens t
        JOIN users u ON u.id = t.user_id
        WHERE t.token = ?
    ''', (token,)).fetchone()

    if not result:
        db.close()
        return jsonify({'success': False, 'error': 'Invalid token'}), 401

    # Check if expired
    if result['expires_at'] < int(time.time()):
        db.execute('DELETE FROM auth_tokens WHERE token = ?', (token,))
        db.commit()
        db.close()
        return jsonify({'success': False, 'error': 'Token expired'}), 401

    db.close()

    return jsonify({
        'success': True,
        'user': {
            'id': result['id'],
            'username': result['username'],
            'display_name': result['display_name'],
            'is_admin': result['is_admin'],
            'email': result['email']
        }
    })


@auth_api_bp.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """Send password reset email (placeholder)"""
    data = request.get_json()
    username = data.get('username', '').strip()

    if not username:
        return jsonify({'success': False, 'error': 'Username required'}), 400

    # TODO: Implement actual password reset
    # For now, just return success
    return jsonify({
        'success': True,
        'message': 'If the username exists, a password reset link will be sent (feature not implemented yet)'
    })


def register_auth_api_routes(app):
    """Register auth API routes with Flask app"""
    app.register_blueprint(auth_api_bp)

    # Create auth_tokens table if it doesn't exist
    from database import get_db
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id)')
    db.commit()
    db.close()

    print("✅ Auth API routes registered:")
    print("   - POST /api/auth/login")
    print("   - POST /api/auth/register")
    print("   - POST /api/auth/logout")
    print("   - GET /api/auth/me")
    print("   - POST /api/auth/forgot-password")

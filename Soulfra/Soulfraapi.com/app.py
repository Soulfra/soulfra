#!/usr/bin/env python3
"""
Soulfraapi.com - Account Creation & Session Management API

Endpoints:
- GET  /qr-signup              → Create account from QR scan, redirect to soulfra.ai
- POST /validate-session       → Validate session token
- GET  /account/<user_id>      → Get account info
- GET  /health                 → Health check

Database:
- users table (id, username, email, created_at, ref_source)
- sessions table (id, user_id, token, created_at, expires_at)

Flow:
1. iPhone scans QR → /qr-signup
2. Create account + session token
3. Redirect to soulfra.ai/?session=TOKEN
"""

import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow soulfra.ai to call this API

# Config
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'soulfraapi.db')
SOULFRA_AI_URL = os.getenv('SOULFRA_AI_URL', 'http://localhost:5003')
SESSION_EXPIRY_HOURS = int(os.getenv('SESSION_EXPIRY_HOURS', '24'))

# ==============================================================================
# DATABASE
# ==============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables"""
    conn = get_db()

    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ref_source TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Sessions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            device_fingerprint TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Database initialized at", DATABASE_PATH)


# ==============================================================================
# HELPERS
# ==============================================================================

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)


def generate_username():
    """Generate random username"""
    adjectives = ['Cool', 'Swift', 'Bright', 'Bold', 'Calm', 'Deep', 'True', 'Wise', 'Pure', 'Rare']
    nouns = ['Soul', 'Mind', 'Wave', 'Star', 'Fire', 'Wind', 'Light', 'Code', 'Path', 'Flow']

    import random
    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    number = random.randint(100, 999)

    return f"{adj}{noun}{number}"


def create_user(ref_source='landing'):
    """Create new user account"""
    conn = get_db()

    # Generate unique username
    username = generate_username()

    # Check if username exists (unlikely but possible)
    while conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        username = generate_username()

    # Insert user
    cursor = conn.execute('''
        INSERT INTO users (username, ref_source)
        VALUES (?, ?)
    ''', (username, ref_source))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return user_id, username


def create_session(user_id):
    """Create session token for user"""
    conn = get_db()

    token = generate_session_token()
    expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)

    conn.execute('''
        INSERT INTO sessions (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, token, expires_at))

    conn.commit()
    conn.close()

    return token


def validate_session_token(token):
    """Validate session token and return user info"""
    conn = get_db()

    row = conn.execute('''
        SELECT s.*, u.username, u.email, u.created_at as user_created_at
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > ?
    ''', (token, datetime.now())).fetchone()

    conn.close()

    if row:
        return {
            'valid': True,
            'user_id': row['user_id'],
            'username': row['username'],
            'email': row['email'],
            'created_at': row['user_created_at']
        }
    else:
        return {'valid': False, 'error': 'Invalid or expired token'}


# ==============================================================================
# ROUTES
# ==============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'soulfraapi.com',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/qr-signup', methods=['GET'])
def qr_signup():
    """
    Create account from QR scan

    Query params:
        ref (optional): Referral source (landing, qr, etc.)

    Response:
        Redirects to soulfra.ai/?session=TOKEN
    """
    ref_source = request.args.get('ref', 'qr')

    # Create user account
    user_id, username = create_user(ref_source)

    # Create session
    token = create_session(user_id)

    # Log
    print(f"✅ Created account: {username} (user_id={user_id}, ref={ref_source})")
    print(f"   Session token: {token}")

    # Redirect to soulfra.ai with session token
    redirect_url = f"{SOULFRA_AI_URL}/?session={token}"

    return redirect(redirect_url)


@app.route('/validate-session', methods=['POST'])
def validate_session():
    """
    Validate session token

    Body:
        {
            "token": "SESSION_TOKEN"
        }

    Response:
        {
            "valid": true,
            "user_id": 123,
            "username": "CoolSoul456"
        }
    """
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({'valid': False, 'error': 'Missing token'}), 400

    result = validate_session_token(token)

    return jsonify(result)


@app.route('/account/<int:user_id>', methods=['GET'])
def get_account(user_id):
    """Get account info by user ID"""
    conn = get_db()

    row = conn.execute('''
        SELECT id, username, email, created_at, ref_source, is_active
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    conn.close()

    if not row:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(dict(row))


@app.route('/stats', methods=['GET'])
def stats():
    """Get API statistics"""
    conn = get_db()

    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    active_sessions = conn.execute('SELECT COUNT(*) FROM sessions WHERE expires_at > ?', (datetime.now(),)).fetchone()[0]

    # Users by ref source
    ref_sources = conn.execute('''
        SELECT ref_source, COUNT(*) as count
        FROM users
        GROUP BY ref_source
    ''').fetchall()

    conn.close()

    return jsonify({
        'total_users': total_users,
        'active_sessions': active_sessions,
        'ref_sources': {row['ref_source']: row['count'] for row in ref_sources}
    })


# ==============================================================================
# TRIBUNAL - EXECUTIVE BRANCH
# ==============================================================================

@app.route('/api/tribunal/execute', methods=['POST'])
def tribunal_execute():
    """
    Executive Branch - Execute token purchase

    Body:
        {
            "package": "pro",
            "user_id": 1,
            "session_id": "tribunal_XXX",
            "proof_chain": ["hash1", "hash2"]
        }

    Response:
        {
            "status": "executed",
            "branch": "executive",
            "method": "stripe_checkout" or "local_simulation",
            "checkout_url": "...",
            "data": {...}
        }
    """
    import hashlib
    import json

    data = request.get_json()

    package = data.get('package')
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    proof_chain = data.get('proof_chain', [])

    if not package or not user_id or not session_id:
        return jsonify({
            'status': 'failed',
            'error': 'Missing required fields'
        }), 400

    # Package pricing
    PACKAGES = {
        'starter': {'tokens': 100, 'price': 10.00},
        'pro': {'tokens': 500, 'price': 40.00},
        'premium': {'tokens': 1000, 'price': 70.00}
    }

    if package not in PACKAGES:
        return jsonify({
            'status': 'failed',
            'error': f'Invalid package: {package}'
        }), 400

    pkg_info = PACKAGES[package]

    # In production, would create Stripe Checkout session
    # For now, simulate execution
    STRIPE_ENABLED = os.getenv('STRIPE_ENABLED', 'false').lower() == 'true'

    if STRIPE_ENABLED:
        # Real Stripe integration (not implemented yet)
        result = {
            'status': 'executed',
            'branch': 'executive',
            'method': 'stripe_checkout',
            'checkout_url': 'https://checkout.stripe.com/...',
            'data': {
                'package': package,
                'tokens': pkg_info['tokens'],
                'price': pkg_info['price'],
                'user_id': user_id
            }
        }
    else:
        # Simulate local execution
        result = {
            'status': 'executed',
            'branch': 'executive',
            'method': 'local_simulation',
            'data': {
                'package': package,
                'tokens': pkg_info['tokens'],
                'price': pkg_info['price'],
                'user_id': user_id,
                'simulated': True
            }
        }

    print(f"⚖️  Executive: Executed {package} purchase for user {user_id}")
    print(f"   Method: {result['method']}")

    return jsonify(result)


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    # Initialize database
    init_database()

    # Run server
    port = int(os.getenv('PORT', '5002'))

    print("\n" + "="*70)
    print("🚀 Soulfraapi.com - Account Creation API")
    print("="*70)
    print(f"Running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"QR signup: http://localhost:{port}/qr-signup")
    print(f"Stats: http://localhost:{port}/stats")
    print(f"\nRedirects to: {SOULFRA_AI_URL}")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=True)

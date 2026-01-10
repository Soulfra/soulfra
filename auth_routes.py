#!/usr/bin/env python3
"""
Authentication Routes - User Signup, Login, Session Management

Simple email/password auth for CringeProof/Soulfra accounts.
First user is auto-assigned admin role.
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/signup', methods=['POST', 'OPTIONS'])
def signup():
    """
    Create new user account

    POST body: {'email': '...', 'password': '...', 'username': '...', 'domain': '...'}
    Returns: {'success': True, 'user_id': int, 'is_admin': bool}
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    username = data.get('username', data.get('name', '')).strip()
    domain = data.get('domain', request.headers.get('Origin', 'soulfra.com')).lower().strip()

    # Extract domain from Origin header if provided (e.g., "https://example.com" → "example.com")
    if domain.startswith('http'):
        domain = domain.split('://')[1].split('/')[0]

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    if len(password) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400

    if not username:
        username = email.split('@')[0]  # Default username from email

    db = get_db()

    # Check if email exists FOR THIS DOMAIN (per-domain isolation)
    existing = db.execute(
        'SELECT id FROM users WHERE email = ? AND (display_name = ? OR display_name IS NULL)',
        (email, domain)
    ).fetchone()
    if existing:
        return jsonify({'success': False, 'error': 'Email already registered on this domain'}), 400

    # Check if this is the first user FOR THIS DOMAIN (each domain gets its own admin)
    user_count = db.execute(
        'SELECT COUNT(*) FROM users WHERE display_name = ?',
        (domain,)
    ).fetchone()[0]
    is_first_user = user_count == 0
    is_admin = 1 if is_first_user else 0

    # Hash password using werkzeug (matches existing schema)
    password_hash = generate_password_hash(password, method='scrypt')

    # Create user - use display_name to store domain for isolation
    # FAUCET: Give new users 10 free tokens to start
    cursor = db.execute('''
        INSERT INTO users (username, email, password_hash, is_admin, display_name, credits, created_at)
        VALUES (?, ?, ?, ?, ?, 10.0, CURRENT_TIMESTAMP)
    ''', (username, email, password_hash, is_admin, domain))

    user_id = cursor.lastrowid

    # Log faucet transaction
    db.execute('''
        INSERT INTO credit_transactions (
            user_id, amount, transaction_type, note, created_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, 10.0, 'faucet', 'Welcome bonus: 10 free tokens'))

    db.commit()
    db.close()

    print(f"🎁 Faucet: Gave {email} 10 free tokens")

    # Log them in WITH DOMAIN CONTEXT
    session['user_id'] = user_id
    session['email'] = email
    session['username'] = username
    session['is_admin'] = is_admin
    session['domain'] = domain

    role = 'admin' if is_admin else 'user'
    print(f"✅ New user created: {email} on {domain} (ID: {user_id}, Admin: {is_admin})")

    return jsonify({
        'success': True,
        'user_id': user_id,
        'email': email,
        'username': username,
        'domain': domain,
        'is_admin': bool(is_admin),
        'credits': 10.0,
        'faucet_bonus': True,
        'message': 'Account created successfully' + (f' - You are the {domain} admin!' if is_first_user else '')
    })


@auth_bp.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Login to existing account

    POST body: {'email': '...', 'password': '...', 'domain': '...'}
    Returns: {'success': True, 'user_id': int, 'is_admin': bool}
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    domain = data.get('domain', request.headers.get('Origin', 'soulfra.com')).lower().strip()

    # Extract domain from Origin header if provided
    if domain.startswith('http'):
        domain = domain.split('://')[1].split('/')[0]

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    db = get_db()

    # Find user FOR THIS DOMAIN ONLY (per-domain isolation)
    user = db.execute('''
        SELECT id, email, username, password_hash, is_admin, display_name
        FROM users
        WHERE email = ? AND (display_name = ? OR display_name IS NULL)
    ''', (email, domain)).fetchone()

    db.close()

    if not user:
        return jsonify({'success': False, 'error': 'Invalid email or password (or wrong domain)'}), 401

    # Verify password (werkzeug scrypt format)
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    # Log them in WITH DOMAIN CONTEXT
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['username'] = user['username']
    session['is_admin'] = user['is_admin']
    session['domain'] = user['display_name'] or domain

    print(f"✅ User logged in: {email} on {domain} (Admin: {user['is_admin']})")

    return jsonify({
        'success': True,
        'user_id': user['id'],
        'email': user['email'],
        'username': user['username'],
        'domain': session['domain'],
        'is_admin': bool(user['is_admin'])
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout current user"""
    email = session.get('email', 'Unknown')
    session.clear()

    print(f"👋 User logged out: {email}")

    return jsonify({'success': True, 'message': 'Logged out successfully'})


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """
    Get current logged-in user info

    Returns: {'user_id': int, 'email': str, 'domain': str, 'is_admin': bool} or 401 if not logged in
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    return jsonify({
        'success': True,
        'user_id': user_id,
        'email': session.get('email'),
        'username': session.get('username'),
        'domain': session.get('domain', 'soulfra.com'),
        'is_admin': bool(session.get('is_admin'))
    })


@auth_bp.route('/api/auth/check-admin', methods=['GET'])
def check_admin():
    """Check if current user is admin"""
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')

    if not user_id:
        return jsonify({'success': False, 'is_admin': False, 'error': 'Not logged in'}), 401

    return jsonify({
        'success': True,
        'is_admin': bool(is_admin)
    })


def create_users_table():
    """
    No-op - users table already exists in database

    Keeping for backwards compatibility with app.py import
    """
    print("✅ Users table already exists (using existing schema)")

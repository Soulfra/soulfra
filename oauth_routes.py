#!/usr/bin/env python3
"""
OAuth Authentication - Brain-Dead Simple

Supports:
- Google OAuth (everyone has Gmail)
- GitHub OAuth (for devs)
- Apple Sign In (for iPhone users)

NO email/password complexity. NO password reset. NO verification emails.
Just: Click button → Log in → Get tokens.

Account Linking Bonuses:
- Link Google → +10 tokens
- Link GitHub → +10 tokens
- Link Apple → +10 tokens
"""

from flask import Blueprint, request, redirect, session, jsonify, url_for
from database import get_db
import requests
import secrets
import os

oauth_bp = Blueprint('oauth', __name__)

# OAuth Configuration (set via environment variables)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET')

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', 'YOUR_GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', 'YOUR_GITHUB_CLIENT_SECRET')

APPLE_CLIENT_ID = os.getenv('APPLE_CLIENT_ID', 'YOUR_APPLE_CLIENT_ID')
APPLE_CLIENT_SECRET = os.getenv('APPLE_CLIENT_SECRET', 'YOUR_APPLE_CLIENT_SECRET')

# Redirect URIs (update these for production)
BASE_URL = os.getenv('BASE_URL', 'https://localhost:5001')
GOOGLE_REDIRECT_URI = f'{BASE_URL}/auth/google/callback'
GITHUB_REDIRECT_URI = f'{BASE_URL}/auth/github/callback'
APPLE_REDIRECT_URI = f'{BASE_URL}/auth/apple/callback'


# ============================================================================
# GOOGLE OAUTH
# ============================================================================

@oauth_bp.route('/auth/google')
def google_login():
    """Redirect to Google OAuth"""
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Google OAuth URL
    google_auth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={GOOGLE_CLIENT_ID}&'
        f'redirect_uri={GOOGLE_REDIRECT_URI}&'
        'response_type=code&'
        'scope=openid email profile&'
        f'state={state}'
    )

    return redirect(google_auth_url)


@oauth_bp.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    # Verify state (CSRF protection)
    if request.args.get('state') != session.get('oauth_state'):
        return jsonify({'error': 'Invalid state'}), 400

    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No code provided'}), 400

    # Exchange code for token
    token_response = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    })

    if not token_response.ok:
        return jsonify({'error': 'Failed to get access token'}), 400

    access_token = token_response.json().get('access_token')

    # Get user info
    user_info = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={
        'Authorization': f'Bearer {access_token}'
    }).json()

    email = user_info.get('email')
    name = user_info.get('name')
    google_id = user_info.get('id')

    # Create or login user
    user = find_or_create_oauth_user(email, name, 'google', google_id)

    # Set session
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['username'] = user['username']
    session['is_admin'] = user['is_admin']

    # Redirect to home
    return redirect('https://cringeproof.com/?login=success')


# ============================================================================
# GITHUB OAUTH
# ============================================================================

@oauth_bp.route('/auth/github')
def github_login():
    """Redirect to GitHub OAuth"""
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    github_auth_url = (
        'https://github.com/login/oauth/authorize?'
        f'client_id={GITHUB_CLIENT_ID}&'
        f'redirect_uri={GITHUB_REDIRECT_URI}&'
        'scope=user:email&'
        f'state={state}'
    )

    return redirect(github_auth_url)


@oauth_bp.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    if request.args.get('state') != session.get('oauth_state'):
        return jsonify({'error': 'Invalid state'}), 400

    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No code provided'}), 400

    # Exchange code for token
    token_response = requests.post('https://github.com/login/oauth/access_token', data={
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': GITHUB_REDIRECT_URI
    }, headers={'Accept': 'application/json'})

    if not token_response.ok:
        return jsonify({'error': 'Failed to get access token'}), 400

    access_token = token_response.json().get('access_token')

    # Get user info
    user_info = requests.get('https://api.github.com/user', headers={
        'Authorization': f'Bearer {access_token}'
    }).json()

    # Get email (might be in separate endpoint)
    emails = requests.get('https://api.github.com/user/emails', headers={
        'Authorization': f'Bearer {access_token}'
    }).json()

    primary_email = next((e['email'] for e in emails if e['primary']), emails[0]['email'] if emails else None)

    github_id = str(user_info.get('id'))
    name = user_info.get('name') or user_info.get('login')
    email = primary_email or f"{github_id}@github.users.noreply.github.com"

    # Create or login user
    user = find_or_create_oauth_user(email, name, 'github', github_id)

    # Set session
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['username'] = user['username']
    session['is_admin'] = user['is_admin']

    return redirect('https://cringeproof.com/?login=success')


# ============================================================================
# APPLE SIGN IN (Placeholder - requires more setup)
# ============================================================================

@oauth_bp.route('/auth/apple')
def apple_login():
    """Redirect to Apple Sign In"""
    # Apple Sign In requires more complex setup
    # For now, return placeholder
    return jsonify({
        'error': 'Apple Sign In not yet configured',
        'message': 'Coming soon! Use Google or GitHub for now.'
    }), 501


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_or_create_oauth_user(email, name, provider, provider_id):
    """
    Find existing user or create new one from OAuth

    Returns user dict with bonus applied if new link
    """
    db = get_db()

    # Check if this OAuth account already linked
    linked = db.execute('''
        SELECT user_id FROM linked_accounts
        WHERE provider = ? AND provider_id = ?
    ''', (provider, provider_id)).fetchone()

    if linked:
        # Existing OAuth link - just log in
        user = db.execute('SELECT * FROM users WHERE id = ?', (linked['user_id'],)).fetchone()
        db.close()
        return dict(user)

    # Check if email already exists (link to existing account)
    existing_user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if existing_user:
        # Link OAuth to existing account + give bonus
        db.execute('''
            INSERT INTO linked_accounts (user_id, provider, provider_id, email, linked_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (existing_user['id'], provider, provider_id, email))

        # Give linking bonus
        bonus = 10.0
        db.execute('UPDATE users SET credits = credits + ? WHERE id = ?', (bonus, existing_user['id']))

        # Log bonus
        db.execute('''
            INSERT INTO credit_transactions (
                user_id, amount, transaction_type, note, created_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (existing_user['id'], bonus, 'oauth_link_bonus', f'Linked {provider} account'))

        db.commit()
        db.close()

        print(f"🔗 Linked {provider} to existing user {email} (+{bonus} tokens)")

        return dict(existing_user)

    # New user - create account with faucet bonus
    username = name.split()[0].lower() if name else email.split('@')[0]

    cursor = db.execute('''
        INSERT INTO users (username, email, password_hash, credits, created_at)
        VALUES (?, ?, ?, 10.0, CURRENT_TIMESTAMP)
    ''', (username, email, 'oauth_no_password'))

    user_id = cursor.lastrowid

    # Link OAuth account
    db.execute('''
        INSERT INTO linked_accounts (user_id, provider, provider_id, email, linked_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, provider, provider_id, email))

    # Log faucet bonus
    db.execute('''
        INSERT INTO credit_transactions (
            user_id, amount, transaction_type, note, created_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, 10.0, 'faucet', f'Welcome bonus via {provider} OAuth'))

    db.commit()

    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()

    print(f"✅ Created new user via {provider}: {email} (+10 tokens)")

    return dict(user)


def init_oauth_tables():
    """Create OAuth-related tables"""
    db = get_db()

    # Linked accounts table
    db.execute('''
        CREATE TABLE IF NOT EXISTS linked_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            email TEXT,
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, provider_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ OAuth tables ready")


if __name__ == '__main__':
    print("🔐 Creating OAuth tables...")
    init_oauth_tables()
    print("✅ OAuth system ready!")
    print()
    print("Setup instructions:")
    print("1. Get Google OAuth credentials: https://console.cloud.google.com")
    print("2. Get GitHub OAuth credentials: https://github.com/settings/developers")
    print("3. Set environment variables:")
    print("   export GOOGLE_CLIENT_ID='...'")
    print("   export GOOGLE_CLIENT_SECRET='...'")
    print("   export GITHUB_CLIENT_ID='...'")
    print("   export GITHUB_CLIENT_SECRET='...'")

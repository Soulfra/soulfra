#!/usr/bin/env python3
"""
Simple Authentication Routes for Cringeproof.com

Provides basic login, signup, and recovery for friends to access the system.

Features:
- Username/password login
- Simple signup (username → auto-create account)
- Email-based recovery OR QR rescan
- Session management (stores in Flask session)
- Works with existing QR auth system

Routes:
- GET /login - HTML login page
- POST /login - Handle login submission
- GET /signup - HTML signup page
- POST /signup - Create new user account
- GET /recover - HTML recovery page
- POST /recover - Send recovery token
- GET /logout - Clear session

Database:
Uses existing `users` table from soulfra.db
"""

from flask import Blueprint, request, render_template_string, redirect, url_for, session, jsonify
from database import get_db
from datetime import datetime, timezone
import hashlib
import secrets
import re

auth_bp = Blueprint('simple_auth', __name__)


def init_auth_tables():
    """
    Initialize authentication tables and columns

    Adds password_hash column to users table if it doesn't exist
    """
    from database import get_db
    db = get_db()

    # Add password_hash column if it doesn't exist
    try:
        db.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
        db.commit()
        print("✅ Added password_hash column to users table")
    except Exception as e:
        # Column probably already exists
        pass

    print("✅ Authentication tables ready")


def hash_password(password):
    """
    Hash password with SHA256

    Args:
        password (str): Plain text password

    Returns:
        str: SHA256 hash
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def generate_slug(username):
    """
    Generate URL-friendly slug from username

    Args:
        username (str): Username

    Returns:
        str: Lowercase alphanumeric slug
    """
    # Remove non-alphanumeric, convert to lowercase
    slug = re.sub(r'[^a-z0-9]', '', username.lower())
    return slug


def verify_password(password, password_hash):
    """
    Verify password against hash

    Args:
        password (str): Plain text password
        password_hash (str): Stored hash

    Returns:
        bool: True if match
    """
    return hash_password(password) == password_hash


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """
    GET /login

    Display login page with username/password form
    Also shows QR login option (links to existing /qr/auth system)
    """
    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Cringeproof</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 40px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            opacity: 0.8;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 16px;
        }
        input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: #00C49A;
            color: white;
            margin-bottom: 10px;
        }
        .btn-primary:hover {
            background: #00a082;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .divider {
            text-align: center;
            margin: 20px 0;
            opacity: 0.6;
        }
        .links {
            text-align: center;
            margin-top: 20px;
        }
        .links a {
            color: #fff;
            text-decoration: none;
            opacity: 0.8;
            font-size: 14px;
        }
        .links a:hover {
            opacity: 1;
            text-decoration: underline;
        }
        .error {
            background: rgba(255, 100, 100, 0.3);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Cringeproof</h1>
        <p class="subtitle">Voice-powered intelligence</p>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" placeholder="Enter your username" required autofocus>
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter your password" required>
            </div>

            <button type="submit" class="btn btn-primary">Login</button>
        </form>

        <div class="divider">OR</div>

        <a href="/api/qr/generate" class="btn btn-secondary" style="display: block; text-align: center; text-decoration: none;">
            📱 Login with QR Code
        </a>

        <div class="links">
            <a href="/signup">Create Account</a> •
            <a href="/recover">Forgot Password?</a>
        </div>
    </div>
</body>
</html>"""

    error = request.args.get('error')
    return render_template_string(template, error=error)


@auth_bp.route('/login', methods=['POST'])
def login_submit():
    """
    POST /login

    Handle login form submission

    Form Data:
        username (str): Username
        password (str): Password

    Returns:
        Redirect to /voice on success
        Redirect to /login?error=... on failure
    """
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        return redirect('/login?error=Please enter both username and password')

    db = get_db()

    # Find user by username
    user = db.execute('''
        SELECT id, username, password_hash, user_slug, display_name
        FROM users
        WHERE username = ? OR user_slug = ?
    ''', (username, username)).fetchone()

    if not user:
        return redirect('/login?error=Invalid username or password')

    # Verify password
    if not user['password_hash']:
        # No password set - maybe created via QR auth
        return redirect('/login?error=Please use QR login or set a password')

    if not verify_password(password, user['password_hash']):
        return redirect('/login?error=Invalid username or password')

    # Success - create session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['user_slug'] = user['user_slug']
    session['display_name'] = user['display_name']

    print(f"✅ User logged in: {user['username']} (ID: {user['id']})")

    return redirect('/voice')


@auth_bp.route('/signup', methods=['GET'])
def signup_page():
    """
    GET /signup

    Display signup page
    """
    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Up - Cringeproof</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 40px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            opacity: 0.8;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input[type="text"],
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 16px;
        }
        input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: #00C49A;
            color: white;
        }
        .btn-primary:hover {
            background: #00a082;
            transform: translateY(-2px);
        }
        .links {
            text-align: center;
            margin-top: 20px;
        }
        .links a {
            color: #fff;
            text-decoration: none;
            opacity: 0.8;
            font-size: 14px;
        }
        .links a:hover {
            opacity: 1;
            text-decoration: underline;
        }
        .error {
            background: rgba(255, 100, 100, 0.3);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .success {
            background: rgba(0, 196, 154, 0.3);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .hint {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Create Account</h1>
        <p class="subtitle">Join the voice-powered revolution</p>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST" action="/signup">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" placeholder="Choose a username" required autofocus pattern="[a-zA-Z0-9_-]+" minlength="3" maxlength="20">
                <p class="hint">Letters, numbers, underscore, dash only</p>
            </div>

            <div class="form-group">
                <label for="email">Email (optional)</label>
                <input type="email" id="email" name="email" placeholder="your@email.com">
                <p class="hint">For password recovery</p>
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Choose a strong password" required minlength="8">
                <p class="hint">At least 8 characters</p>
            </div>

            <div class="form-group">
                <label for="password_confirm">Confirm Password</label>
                <input type="password" id="password_confirm" name="password_confirm" placeholder="Re-enter your password" required>
            </div>

            <div class="form-group" style="margin-top: 20px;">
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="gdpr_consent" name="gdpr_consent" required style="width: auto; margin-right: 10px; cursor: pointer;">
                    <span style="font-size: 14px;">
                        I agree to the <a href="/terms" target="_blank" style="color: #06FFA5; text-decoration: underline;">Terms of Service & Privacy Policy</a> (GDPR compliant)
                    </span>
                </label>
            </div>

            <button type="submit" class="btn btn-primary">Create Account</button>
        </form>

        <div class="links">
            <a href="/login">Already have an account? Login</a>
        </div>
    </div>

    <script>
        // Client-side password validation
        document.querySelector('form').addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            const confirm = document.getElementById('password_confirm').value;

            if (password !== confirm) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    </script>
</body>
</html>"""

    error = request.args.get('error')
    return render_template_string(template, error=error)


@auth_bp.route('/signup', methods=['POST'])
def signup_submit():
    """
    POST /signup

    Create new user account

    Form Data:
        username (str): Username (required)
        email (str): Email (optional, for recovery)
        password (str): Password (required)
        password_confirm (str): Password confirmation (required)

    Returns:
        Redirect to /login on success
        Redirect to /signup?error=... on failure
    """
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    password_confirm = request.form.get('password_confirm', '')
    gdpr_consent = request.form.get('gdpr_consent')

    # Validation
    if not username or not password:
        return redirect('/signup?error=Username and password are required')

    if not gdpr_consent:
        return redirect('/signup?error=You must agree to the Terms of Service and Privacy Policy')

    if password != password_confirm:
        return redirect('/signup?error=Passwords do not match')

    if len(password) < 8:
        return redirect('/signup?error=Password must be at least 8 characters')

    # Validate username format
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return redirect('/signup?error=Username can only contain letters, numbers, underscore, and dash')

    if len(username) < 3 or len(username) > 20:
        return redirect('/signup?error=Username must be between 3 and 20 characters')

    db = get_db()

    # Check if username already exists
    existing_user = db.execute('''
        SELECT id FROM users WHERE username = ? OR user_slug = ?
    ''', (username, generate_slug(username))).fetchone()

    if existing_user:
        return redirect('/signup?error=Username already taken')

    # Create user
    user_slug = generate_slug(username)
    password_hash = hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()
    gdpr_consent_at = created_at  # Store timestamp of GDPR consent
    terms_accepted_at = created_at  # Store timestamp of Terms acceptance

    try:
        cursor = db.execute('''
            INSERT INTO users (username, user_slug, password_hash, email, created_at, display_name, gdpr_consent_at, terms_accepted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_slug, password_hash, email or None, created_at, username, gdpr_consent_at, terms_accepted_at))

        user_id = cursor.lastrowid
        db.commit()

        print(f"✅ New user created: {username} (ID: {user_id}, slug: {user_slug})")

        # Auto-login after signup
        session['user_id'] = user_id
        session['username'] = username
        session['user_slug'] = user_slug
        session['display_name'] = username

        return redirect('/voice')

    except Exception as e:
        db.rollback()
        print(f"❌ Signup error: {e}")
        return redirect('/signup?error=Account creation failed. Please try again.')


@auth_bp.route('/recover', methods=['GET'])
def recover_page():
    """
    GET /recover

    Display password recovery page
    """
    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recover Password - Cringeproof</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 40px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            opacity: 0.8;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input[type="email"] {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 16px;
        }
        input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: block;
            text-align: center;
        }
        .btn-primary {
            background: #00C49A;
            color: white;
            margin-bottom: 10px;
        }
        .btn-primary:hover {
            background: #00a082;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .divider {
            text-align: center;
            margin: 20px 0;
            opacity: 0.6;
        }
        .links {
            text-align: center;
            margin-top: 20px;
        }
        .links a {
            color: #fff;
            text-decoration: none;
            opacity: 0.8;
            font-size: 14px;
        }
        .links a:hover {
            opacity: 1;
            text-decoration: underline;
        }
        .error {
            background: rgba(255, 100, 100, 0.3);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .success {
            background: rgba(0, 196, 154, 0.3);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔑 Recover Password</h1>
        <p class="subtitle">We'll send you a recovery link</p>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}

        <form method="POST" action="/recover">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" placeholder="your@email.com" required autofocus>
            </div>

            <button type="submit" class="btn btn-primary">Send Recovery Link</button>
        </form>

        <div class="divider">OR</div>

        <a href="/api/qr/generate" class="btn btn-secondary">
            📱 Reset via QR Code
        </a>

        <div class="links">
            <a href="/login">Back to Login</a>
        </div>
    </div>
</body>
</html>"""

    error = request.args.get('error')
    success = request.args.get('success')
    return render_template_string(template, error=error, success=success)


@auth_bp.route('/recover', methods=['POST'])
def recover_submit():
    """
    POST /recover

    Send recovery email (placeholder - email not wired up yet)

    Form Data:
        email (str): Email address

    Returns:
        Redirect to /recover?success=... with instructions
    """
    email = request.form.get('email', '').strip()

    if not email:
        return redirect('/recover?error=Please enter your email address')

    db = get_db()

    # Find user by email
    user = db.execute('''
        SELECT id, username, email FROM users WHERE email = ?
    ''', (email,)).fetchone()

    if not user:
        # Don't reveal if email exists or not (security)
        return redirect('/recover?success=If that email is registered, you will receive a recovery link shortly.')

    # TODO: Wire up email sending
    # For now, just generate recovery token and show message
    recovery_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc).isoformat()

    # Store recovery token (would need recovery_tokens table)
    print(f"🔑 Recovery token for {user['username']}: {recovery_token}")
    print(f"   Email would be sent to: {email}")

    return redirect('/recover?success=Recovery link sent! Check your email. (Email not wired up yet - contact admin)')


@auth_bp.route('/logout')
def logout():
    """
    GET /logout

    Clear session and redirect to login
    """
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"✅ User logged out: {username}")

    return redirect('/login')


@auth_bp.route('/api/auth/status')
def auth_status():
    """
    GET /api/auth/status

    Check if user is logged in (for AJAX)

    Returns:
        JSON: {
            "authenticated": true/false,
            "user": {
                "id": 123,
                "username": "matt",
                "slug": "matt"
            }
        }
    """
    user_id = session.get('user_id')

    if user_id:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user_id,
                'username': session.get('username'),
                'slug': session.get('user_slug'),
                'display_name': session.get('display_name')
            }
        })
    else:
        return jsonify({
            'authenticated': False,
            'user': None
        })


@auth_bp.route('/api/gdpr/export', methods=['GET'])
def gdpr_export_data():
    """
    GET /api/gdpr/export

    Export all user data (GDPR Right to Access)

    Returns:
        JSON: All user data (posts, subscriptions, account info)
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    db = get_db()

    # Get user account info
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    # Get user's posts
    posts = db.execute('''
        SELECT p.*, b.name as brand_name
        FROM posts p
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.user_id = ?
        ORDER BY p.published_at DESC
    ''', (user_id,)).fetchall()

    # Get newsletter subscriptions
    subscriptions = db.execute('''
        SELECT ns.*, b.name as brand_name
        FROM newsletter_subscriptions ns
        JOIN brands b ON ns.brand_id = b.id
        WHERE ns.user_id = ?
    ''', (user_id,)).fetchall()

    # Compile all data
    export_data = {
        'export_date': datetime.now(timezone.utc).isoformat(),
        'user': dict(user),
        'posts': [dict(p) for p in posts],
        'newsletter_subscriptions': [dict(s) for s in subscriptions],
        'gdpr_notice': 'This is all personal data Soulfra has stored about you. You have the right to request deletion at any time.'
    }

    print(f"✅ User {user['username']} exported their data (GDPR compliance)")

    return jsonify(export_data)


@auth_bp.route('/api/gdpr/delete', methods=['POST'])
def gdpr_delete_account():
    """
    POST /api/gdpr/delete

    Delete user account and all data (GDPR Right to Erasure)

    JSON Body:
        confirm (str): Must be "DELETE MY ACCOUNT" to confirm

    Returns:
        JSON: {
            "success": true,
            "message": "Account deleted"
        }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    confirm = data.get('confirm', '')

    if confirm != "DELETE MY ACCOUNT":
        return jsonify({
            'success': False,
            'error': 'Must confirm with "DELETE MY ACCOUNT"'
        }), 400

    db = get_db()

    # Get username before deletion
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    username = user['username'] if user else 'Unknown'

    # Delete all user data (cascade)
    db.execute('DELETE FROM newsletter_subscriptions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))

    db.commit()

    # Clear session
    session.clear()

    print(f"✅ User {username} deleted their account (GDPR Right to Erasure)")

    return jsonify({
        'success': True,
        'message': 'Your account and all associated data have been permanently deleted. Goodbye!'
    })


if __name__ == '__main__':
    """
    CLI for testing authentication
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 simple_auth_routes.py create <username> <password>  # Create test user")
        print("  python3 simple_auth_routes.py verify <username> <password>  # Verify login")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: python3 simple_auth_routes.py create <username> <password>")
            sys.exit(1)

        username = sys.argv[2]
        password = sys.argv[3]

        from database import get_db
        db = get_db()

        user_slug = generate_slug(username)
        password_hash = hash_password(password)
        created_at = datetime.now(timezone.utc).isoformat()

        cursor = db.execute('''
            INSERT INTO users (username, user_slug, password_hash, created_at, display_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, user_slug, password_hash, created_at, username))

        db.commit()
        print(f"✅ User created: {username} (slug: {user_slug})")

    elif command == "verify":
        if len(sys.argv) < 4:
            print("Usage: python3 simple_auth_routes.py verify <username> <password>")
            sys.exit(1)

        username = sys.argv[2]
        password = sys.argv[3]

        from database import get_db
        db = get_db()

        user = db.execute('''
            SELECT id, username, password_hash FROM users WHERE username = ?
        ''', (username,)).fetchone()

        if not user:
            print(f"❌ User not found: {username}")
            sys.exit(1)

        if verify_password(password, user['password_hash']):
            print(f"✅ Password verified for: {username}")
        else:
            print(f"❌ Invalid password for: {username}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

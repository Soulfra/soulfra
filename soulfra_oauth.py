#!/usr/bin/env python3
"""
Soulfra OAuth Provider - Your Own Authentication Platform

This is YOUR OAuth provider. Other sites can add "Login with Soulfra" button.

Standard OAuth 2.0 Flow:
1. User visits CringeProof.com, clicks "Login with Soulfra"
2. CringeProof redirects to: soulfra.com/oauth/authorize?client_id=...&redirect_uri=...
3. User logs in via QR code (using qr_auth.py)
4. Soulfra redirects back: cringeproof.com/callback?code=ABC123
5. CringeProof exchanges code for access token
6. CringeProof uses token to get user info

Routes:
- GET  /oauth/signup          - Create Soulfra account
- GET  /oauth/login           - QR code login page
- GET  /oauth/authorize       - OAuth authorization (other sites redirect here)
- POST /oauth/token           - Exchange code for access token
- GET  /oauth/user            - Get user info from access token
- POST /oauth/register-client - Register new OAuth client (CringeProof, etc.)
"""

from flask import Blueprint, request, session, jsonify, render_template_string, redirect, url_for
import secrets
import hashlib
import time
import json
from datetime import datetime, timedelta
from database import get_db
from qr_auth import generate_auth_token, verify_auth_token
from device_hash import capture_device_info, get_or_create_device
import qrcode
import io
import base64

soulfra_oauth_bp = Blueprint('soulfra_oauth', __name__)


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_oauth_tables():
    """Create OAuth tables"""
    db = get_db()

    # OAuth clients (sites that use Soulfra login)
    db.execute('''
        CREATE TABLE IF NOT EXISTS oauth_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE NOT NULL,
            client_secret TEXT NOT NULL,
            client_name TEXT NOT NULL,
            redirect_uris TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Authorization codes (temporary codes exchanged for tokens)
    db.execute('''
        CREATE TABLE IF NOT EXISTS oauth_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            client_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            redirect_uri TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES oauth_clients(client_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Access tokens (long-lived tokens for API access)
    db.execute('''
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT UNIQUE NOT NULL,
            client_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES oauth_clients(client_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Transaction ledger (complete audit log)
    db.execute('''
        CREATE TABLE IF NOT EXISTS auth_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            client_id TEXT,
            device_hash TEXT,
            ip_address TEXT,
            user_agent TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Users table (if not exists)
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            display_name TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    db.commit()
    print("✅ Soulfra OAuth tables initialized")


# =============================================================================
# TRANSACTION LOGGING (Your Ledger)
# =============================================================================

def log_transaction(event_type, user_id=None, client_id=None, device_info=None, metadata=None):
    """
    Log all authentication events to transaction ledger

    This is your "blockchain" - complete audit trail of all auth activity
    """
    db = get_db()

    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent', '') if request else None
    device_hash = device_info.get('device_hash') if device_info else None

    db.execute('''
        INSERT INTO auth_transactions (
            event_type, user_id, client_id, device_hash,
            ip_address, user_agent, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        event_type,
        user_id,
        client_id,
        device_hash,
        ip_address,
        user_agent,
        json.dumps(metadata) if metadata else None
    ))

    db.commit()


# =============================================================================
# USER SIGNUP & LOGIN
# =============================================================================

@soulfra_oauth_bp.route('/oauth/signup', methods=['GET', 'POST'])
def signup():
    """Create Soulfra account"""
    if request.method == 'GET':
        return render_template_string(SIGNUP_TEMPLATE)

    # POST - create account
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password required'}), 400

    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    db = get_db()

    try:
        # Create user
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, username))

        user_id = cursor.lastrowid
        db.commit()

        # Capture device info
        device_info = capture_device_info(request)

        # Log transaction
        log_transaction('signup', user_id=user_id, device_info=device_info, metadata={
            'username': username,
            'email': email
        })

        # Set session
        session['user_id'] = user_id
        session['username'] = username

        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': username
        })

    except Exception as e:
        return jsonify({'error': f'Signup failed: {str(e)}'}), 400


@soulfra_oauth_bp.route('/oauth/login', methods=['GET', 'POST'])
def login():
    """QR code login"""
    if request.method == 'GET':
        # Show QR code login page

        # Get user_id from query (if coming from authorize flow)
        requested_user = request.args.get('username', '')

        return render_template_string(LOGIN_TEMPLATE, username=requested_user)

    # POST - generate QR code for login
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Verify credentials
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    db = get_db()
    user = db.execute('''
        SELECT id, username, email, display_name
        FROM users
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash)).fetchone()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate QR auth token
    auth_token = generate_auth_token(user['id'], ttl_seconds=300, one_time=True)

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(f"soulfra_login:{auth_token}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Log transaction
    device_info = capture_device_info(request)
    log_transaction('login_qr_generated', user_id=user['id'], device_info=device_info)

    return jsonify({
        'success': True,
        'auth_token': auth_token,
        'qr_code': qr_base64,
        'user_id': user['id']
    })


@soulfra_oauth_bp.route('/oauth/verify-qr', methods=['POST'])
def verify_qr():
    """Verify QR code scan and establish session"""
    data = request.get_json()
    auth_token = data.get('auth_token', '')

    # Verify token
    token_data = verify_auth_token(auth_token)

    if not token_data:
        return jsonify({'error': 'Invalid or expired token'}), 401

    user_id = token_data['user_id']

    # Get user
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']

    # Update last login
    db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    db.commit()

    # Log transaction
    device_info = capture_device_info(request)
    log_transaction('login_success', user_id=user_id, device_info=device_info)

    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'display_name': user['display_name']
        }
    })


# =============================================================================
# OAUTH AUTHORIZATION FLOW
# =============================================================================

@soulfra_oauth_bp.route('/oauth/authorize')
def authorize():
    """
    OAuth authorization endpoint

    Other sites redirect here: /oauth/authorize?client_id=...&redirect_uri=...&state=...

    User logs in, then we redirect back with authorization code
    """
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    state = request.args.get('state', '')

    if not client_id or not redirect_uri:
        return "Missing client_id or redirect_uri", 400

    # Verify client exists
    db = get_db()
    client = db.execute('''
        SELECT client_name, redirect_uris FROM oauth_clients WHERE client_id = ?
    ''', (client_id,)).fetchone()

    if not client:
        return "Invalid client_id", 400

    # Verify redirect_uri matches registered URIs
    allowed_uris = json.loads(client['redirect_uris'])
    if redirect_uri not in allowed_uris:
        return "Invalid redirect_uri", 400

    # Check if user already logged in
    user_id = session.get('user_id')

    if user_id:
        # User already logged in - generate auth code and redirect
        return _generate_auth_code_and_redirect(user_id, client_id, redirect_uri, state)

    # User not logged in - show login page
    session['oauth_client_id'] = client_id
    session['oauth_redirect_uri'] = redirect_uri
    session['oauth_state'] = state

    return render_template_string(AUTHORIZE_TEMPLATE, client_name=client['client_name'])


def _generate_auth_code_and_redirect(user_id, client_id, redirect_uri, state):
    """Generate authorization code and redirect back to client"""
    db = get_db()

    # Generate auth code
    auth_code = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

    db.execute('''
        INSERT INTO oauth_codes (code, client_id, user_id, redirect_uri, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (auth_code, client_id, user_id, redirect_uri, expires_at))

    db.commit()

    # Log transaction
    device_info = capture_device_info(request)
    log_transaction('oauth_code_generated', user_id=user_id, client_id=client_id, device_info=device_info)

    # Build redirect URL
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"

    return redirect(redirect_url)


@soulfra_oauth_bp.route('/oauth/authorize/complete', methods=['POST'])
def authorize_complete():
    """
    Complete authorization after user logs in

    Called from authorize page after QR login
    """
    # Get OAuth params from session
    client_id = session.get('oauth_client_id')
    redirect_uri = session.get('oauth_redirect_uri')
    state = session.get('oauth_state', '')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    if not client_id or not redirect_uri:
        return jsonify({'error': 'Missing OAuth parameters'}), 400

    # Clear OAuth session data
    session.pop('oauth_client_id', None)
    session.pop('oauth_redirect_uri', None)
    session.pop('oauth_state', None)

    # Generate auth code and get redirect URL
    db = get_db()
    auth_code = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

    db.execute('''
        INSERT INTO oauth_codes (code, client_id, user_id, redirect_uri, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (auth_code, client_id, user_id, redirect_uri, expires_at))

    db.commit()

    # Log transaction
    device_info = capture_device_info(request)
    log_transaction('oauth_authorized', user_id=user_id, client_id=client_id, device_info=device_info)

    # Return redirect URL
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"

    return jsonify({
        'success': True,
        'redirect_url': redirect_url
    })


@soulfra_oauth_bp.route('/oauth/token', methods=['POST'])
def token():
    """
    Exchange authorization code for access token

    POST body:
    {
        "grant_type": "authorization_code",
        "code": "...",
        "client_id": "...",
        "client_secret": "...",
        "redirect_uri": "..."
    }
    """
    data = request.get_json() or request.form

    grant_type = data.get('grant_type')
    code = data.get('code')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    redirect_uri = data.get('redirect_uri')

    if grant_type != 'authorization_code':
        return jsonify({'error': 'unsupported_grant_type'}), 400

    if not code or not client_id or not client_secret:
        return jsonify({'error': 'invalid_request'}), 400

    db = get_db()

    # Verify client credentials
    client = db.execute('''
        SELECT client_id FROM oauth_clients
        WHERE client_id = ? AND client_secret = ?
    ''', (client_id, client_secret)).fetchone()

    if not client:
        return jsonify({'error': 'invalid_client'}), 401

    # Verify authorization code
    auth_code = db.execute('''
        SELECT user_id, redirect_uri, expires_at, used
        FROM oauth_codes
        WHERE code = ? AND client_id = ?
    ''', (code, client_id)).fetchone()

    if not auth_code:
        return jsonify({'error': 'invalid_grant'}), 400

    if auth_code['used']:
        return jsonify({'error': 'invalid_grant', 'error_description': 'Code already used'}), 400

    # Check expiration
    if datetime.fromisoformat(auth_code['expires_at']) < datetime.now():
        return jsonify({'error': 'invalid_grant', 'error_description': 'Code expired'}), 400

    # Check redirect_uri matches
    if redirect_uri and redirect_uri != auth_code['redirect_uri']:
        return jsonify({'error': 'invalid_grant', 'error_description': 'Redirect URI mismatch'}), 400

    # Mark code as used
    db.execute('UPDATE oauth_codes SET used = 1 WHERE code = ?', (code,))

    # Generate access token
    access_token = secrets.token_urlsafe(32)
    user_id = auth_code['user_id']

    db.execute('''
        INSERT INTO oauth_tokens (access_token, client_id, user_id)
        VALUES (?, ?, ?)
    ''', (access_token, client_id, user_id))

    db.commit()

    # Log transaction
    log_transaction('token_issued', user_id=user_id, client_id=client_id)

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'scope': 'user:email user:profile'
    })


@soulfra_oauth_bp.route('/oauth/user')
def get_user():
    """
    Get user info from access token

    Authorization: Bearer <access_token>
    """
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'invalid_token'}), 401

    access_token = auth_header.replace('Bearer ', '')

    db = get_db()

    # Verify token
    token_data = db.execute('''
        SELECT user_id FROM oauth_tokens WHERE access_token = ?
    ''', (access_token,)).fetchone()

    if not token_data:
        return jsonify({'error': 'invalid_token'}), 401

    # Get user
    user = db.execute('''
        SELECT id, username, email, display_name, avatar_url, created_at
        FROM users WHERE id = ?
    ''', (token_data['user_id'],)).fetchone()

    if not user:
        return jsonify({'error': 'user_not_found'}), 404

    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'display_name': user['display_name'],
        'avatar_url': user['avatar_url'],
        'created_at': user['created_at']
    })


# =============================================================================
# CLIENT REGISTRATION
# =============================================================================

@soulfra_oauth_bp.route('/oauth/register-client', methods=['POST'])
def register_client():
    """
    Register new OAuth client (e.g., CringeProof)

    POST body:
    {
        "client_name": "CringeProof",
        "redirect_uris": ["https://cringeproof.com/auth/callback"]
    }
    """
    data = request.get_json()
    client_name = data.get('client_name', '').strip()
    redirect_uris = data.get('redirect_uris', [])

    if not client_name or not redirect_uris:
        return jsonify({'error': 'client_name and redirect_uris required'}), 400

    # Generate client credentials
    client_id = f"soulfra_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)

    db = get_db()

    db.execute('''
        INSERT INTO oauth_clients (client_id, client_secret, client_name, redirect_uris)
        VALUES (?, ?, ?, ?)
    ''', (client_id, client_secret, client_name, json.dumps(redirect_uris)))

    db.commit()

    # Log transaction
    log_transaction('client_registered', metadata={
        'client_id': client_id,
        'client_name': client_name
    })

    return jsonify({
        'success': True,
        'client_id': client_id,
        'client_secret': client_secret,
        'client_name': client_name,
        'redirect_uris': redirect_uris
    })


# =============================================================================
# HTML TEMPLATES
# =============================================================================

SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Soulfra - Create Account</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 50px; }
        .container { max-width: 400px; margin: 0 auto; background: #161b22; padding: 40px; border-radius: 12px; }
        h1 { margin-top: 0; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #238636; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
        button:hover { background: #2ea043; }
        .error { color: #f85149; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Create Soulfra Account</h1>
        <div id="error" class="error"></div>
        <input type="text" id="username" placeholder="Username" />
        <input type="email" id="email" placeholder="Email" />
        <input type="password" id="password" placeholder="Password" />
        <button onclick="signup()">Create Account</button>
    </div>
    <script>
        async function signup() {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const res = await fetch('/oauth/signup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, email, password})
            });

            const data = await res.json();

            if (data.error) {
                document.getElementById('error').textContent = data.error;
            } else {
                window.location.href = '/';
            }
        }
    </script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Soulfra - Login</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 50px; }
        .container { max-width: 400px; margin: 0 auto; background: #161b22; padding: 40px; border-radius: 12px; text-align: center; }
        h1 { margin-top: 0; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #238636; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; margin: 10px 0; }
        button:hover { background: #2ea043; }
        .qr-code { background: white; padding: 20px; border-radius: 8px; display: inline-block; margin: 20px 0; }
        .error { color: #f85149; margin: 10px 0; }
        #qr-section { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Login to Soulfra</h1>

        <div id="login-form">
            <div id="error" class="error"></div>
            <input type="text" id="username" placeholder="Username" value="{{ username }}" />
            <input type="password" id="password" placeholder="Password" />
            <button onclick="login()">Login</button>
        </div>

        <div id="qr-section">
            <p>Scan QR code to complete login:</p>
            <div class="qr-code">
                <img id="qr-img" />
            </div>
            <button onclick="verifyQR()">I've Scanned - Verify</button>
        </div>
    </div>
    <script>
        let authToken = '';

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const res = await fetch('/oauth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });

            const data = await res.json();

            if (data.error) {
                document.getElementById('error').textContent = data.error;
            } else {
                authToken = data.auth_token;
                document.getElementById('qr-img').src = 'data:image/png;base64,' + data.qr_code;
                document.getElementById('login-form').style.display = 'none';
                document.getElementById('qr-section').style.display = 'block';
            }
        }

        async function verifyQR() {
            const res = await fetch('/oauth/verify-qr', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({auth_token: authToken})
            });

            const data = await res.json();

            if (data.success) {
                window.location.href = '/';
            } else {
                alert('QR verification failed: ' + data.error);
            }
        }
    </script>
</body>
</html>
'''

AUTHORIZE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Authorize {{ client_name }}</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 50px; }
        .container { max-width: 400px; margin: 0 auto; background: #161b22; padding: 40px; border-radius: 12px; text-align: center; }
        h1 { margin-top: 0; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #238636; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; margin: 10px 0; }
        button:hover { background: #2ea043; }
        .qr-code { background: white; padding: 20px; border-radius: 8px; display: inline-block; margin: 20px 0; }
        #qr-section { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ client_name }} wants to access your Soulfra account</h1>

        <div id="login-form">
            <p>Login to authorize:</p>
            <input type="text" id="username" placeholder="Username" />
            <input type="password" id="password" placeholder="Password" />
            <button onclick="login()">Login & Authorize</button>
        </div>

        <div id="qr-section">
            <p>Scan QR code to authorize:</p>
            <div class="qr-code">
                <img id="qr-img" />
            </div>
            <button onclick="completeAuth()">Complete Authorization</button>
        </div>
    </div>
    <script>
        let authToken = '';

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const res = await fetch('/oauth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });

            const data = await res.json();

            if (data.error) {
                alert(data.error);
            } else {
                authToken = data.auth_token;
                document.getElementById('qr-img').src = 'data:image/png;base64,' + data.qr_code;
                document.getElementById('login-form').style.display = 'none';
                document.getElementById('qr-section').style.display = 'block';
            }
        }

        async function completeAuth() {
            // First verify QR
            const verifyRes = await fetch('/oauth/verify-qr', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({auth_token: authToken})
            });

            const verifyData = await verifyRes.json();

            if (!verifyData.success) {
                alert('QR verification failed: ' + verifyData.error);
                return;
            }

            // Complete OAuth authorization
            const authRes = await fetch('/oauth/authorize/complete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });

            const authData = await authRes.json();

            if (authData.success) {
                window.location.href = authData.redirect_url;
            } else {
                alert('Authorization failed: ' + authData.error);
            }
        }
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    init_oauth_tables()

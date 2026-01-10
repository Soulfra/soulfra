#!/usr/bin/env python3
"""
GitHub Device Flow OAuth - No Callback Needed!

Perfect for self-hosted apps:
- No public URL required
- Works on LAN (192.168.1.87)
- User scans QR → Authorizes on GitHub
- Your app polls for success

Flow:
1. Request device code from GitHub
2. Show QR code + 8-digit code to user
3. User scans QR or goes to github.com/device
4. User enters code, authorizes
5. Your app polls GitHub every 5 seconds
6. Get access token when user authorizes
7. Create user account in YOUR database
"""

from flask import Blueprint, request, session, jsonify, render_template_string
import requests
import time
import qrcode
import io
import base64
import os
from database import get_db
from moniker_generator import generate_all_monikers

device_flow_bp = Blueprint('device_flow', __name__)

# GitHub Device Flow Configuration
# NO CLIENT_SECRET NEEDED!
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', 'YOUR_CLIENT_ID')


@device_flow_bp.route('/auth/device/login')
def device_login():
    """
    Start device flow - show QR code for user to scan
    """

    # Step 1: Request device code from GitHub
    response = requests.post(
        'https://github.com/login/device/code',
        headers={'Accept': 'application/json'},
        data={'client_id': GITHUB_CLIENT_ID}
    )

    if response.status_code != 200:
        return jsonify({'error': 'Failed to get device code'}), 500

    data = response.json()

    device_code = data['device_code']
    user_code = data['user_code']
    verification_uri = data['verification_uri']
    expires_in = data['expires_in']
    interval = data.get('interval', 5)  # Poll every 5 seconds

    # Store device_code in session for polling
    session['device_code'] = device_code
    session['poll_interval'] = interval
    session['expires_at'] = time.time() + expires_in

    # Generate QR code for easy mobile scanning
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(verification_uri)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR to base64 for embedding in HTML
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Render login page with QR code
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login with GitHub</title>
        <style>
            body {{
                font-family: -apple-system, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                text-align: center;
                background: #0d1117;
                color: #c9d1d9;
            }}
            .container {{
                background: #161b22;
                padding: 40px;
                border-radius: 12px;
                border: 1px solid #30363d;
            }}
            .qr-code {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                display: inline-block;
                margin: 20px 0;
            }}
            .user-code {{
                font-size: 48px;
                font-weight: bold;
                letter-spacing: 8px;
                color: #58a6ff;
                margin: 20px 0;
                font-family: monospace;
            }}
            .instructions {{
                color: #8b949e;
                margin: 20px 0;
                line-height: 1.6;
            }}
            .status {{
                margin-top: 30px;
                padding: 15px;
                background: #21262d;
                border-radius: 6px;
                font-size: 14px;
            }}
            .spinner {{
                border: 3px solid #30363d;
                border-top: 3px solid #58a6ff;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Login with GitHub</h1>

            <div class="qr-code">
                <img src="data:image/png;base64,{qr_base64}" alt="QR Code">
            </div>

            <p class="instructions">
                <strong>Option 1 (Mobile):</strong> Scan QR code with your phone
            </p>

            <p class="instructions">
                <strong>Option 2 (Desktop):</strong> Go to <a href="{verification_uri}" target="_blank">{verification_uri}</a>
            </p>

            <div class="user-code">{user_code}</div>

            <p class="instructions">
                Enter the code above to authorize this app
            </p>

            <div class="status">
                <div class="spinner"></div>
                <p>Waiting for authorization...</p>
                <p style="font-size: 12px; color: #8b949e;">This page will automatically redirect when you authorize</p>
            </div>
        </div>

        <script>
            // Poll for authorization
            const pollInterval = {interval * 1000};  // Convert to milliseconds
            const expiresAt = {int(time.time() + expires_in) * 1000};

            function checkAuthorization() {{
                if (Date.now() > expiresAt) {{
                    document.querySelector('.status').innerHTML = '<p style="color: #f85149;">❌ Code expired. Please refresh to try again.</p>';
                    return;
                }}

                fetch('/auth/device/poll')
                    .then(res => res.json())
                    .then(data => {{
                        if (data.status === 'authorized') {{
                            document.querySelector('.status').innerHTML = '<p style="color: #3fb950;">✅ Authorized! Redirecting...</p>';
                            setTimeout(() => {{
                                window.location.href = data.redirect_url || '/';
                            }}, 1000);
                        }} else if (data.status === 'pending') {{
                            // Keep polling
                            setTimeout(checkAuthorization, pollInterval);
                        }} else {{
                            document.querySelector('.status').innerHTML = `<p style="color: #f85149;">❌ ${{data.error}}</p>`;
                        }}
                    }})
                    .catch(err => {{
                        console.error('Poll error:', err);
                        setTimeout(checkAuthorization, pollInterval);
                    }});
            }}

            // Start polling
            setTimeout(checkAuthorization, pollInterval);
        </script>
    </body>
    </html>
    '''

    return html


@device_flow_bp.route('/auth/device/poll')
def device_poll():
    """
    JavaScript frontend calls this to check if user authorized
    """
    device_code = session.get('device_code')

    if not device_code:
        return jsonify({'status': 'error', 'error': 'No device code in session'}), 400

    # Check if code expired
    if time.time() > session.get('expires_at', 0):
        return jsonify({'status': 'expired', 'error': 'Code expired'})

    # Poll GitHub for authorization
    response = requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': GITHUB_CLIENT_ID,
            'device_code': device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }
    )

    if response.status_code != 200:
        return jsonify({'status': 'error', 'error': 'GitHub API error'})

    data = response.json()

    # Check response
    if 'error' in data:
        error = data['error']

        if error == 'authorization_pending':
            # User hasn't authorized yet - keep polling
            return jsonify({'status': 'pending'})
        elif error == 'slow_down':
            # Polling too fast
            return jsonify({'status': 'slow_down'})
        elif error == 'expired_token':
            return jsonify({'status': 'expired', 'error': 'Code expired'})
        elif error == 'access_denied':
            return jsonify({'status': 'denied', 'error': 'User denied access'})
        else:
            return jsonify({'status': 'error', 'error': error})

    # SUCCESS! Got access token
    access_token = data.get('access_token')

    if not access_token:
        return jsonify({'status': 'error', 'error': 'No access token received'})

    # Get user info from GitHub
    user_response = requests.get(
        'https://api.github.com/user',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    )

    if user_response.status_code != 200:
        return jsonify({'status': 'error', 'error': 'Failed to get user info'})

    user_data = user_response.json()

    github_id = user_data['id']
    github_username = user_data['login']
    email = user_data.get('email', f'{github_username}@github.local')
    avatar_url = user_data.get('avatar_url')

    # Create or update user in database
    db = get_db()

    # Check if master user exists (GitHub OAuth integration)
    existing_master = db.execute(
        'SELECT id FROM soulfra_master_users WHERE github_id = ?',
        (github_id,)
    ).fetchone()

    if existing_master:
        # Update existing master user
        master_user_id = existing_master['id']
        db.execute('''
            UPDATE soulfra_master_users
            SET github_username = ?, avatar_url = ?, last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (github_username, avatar_url, master_user_id))
        db.commit()

        # Get username
        master_user = db.execute(
            'SELECT master_username FROM soulfra_master_users WHERE id = ?',
            (master_user_id,)
        ).fetchone()
        username = master_user['master_username']

    else:
        # Create new master user with GitHub OAuth
        # Generate monikers
        monikers = generate_all_monikers(github_username)

        cursor = db.execute('''
            INSERT INTO soulfra_master_users (
                email,
                password_hash,
                master_username,
                github_id,
                github_username,
                avatar_url,
                soulfra_moniker,
                deathtodata_moniker,
                calriven_moniker,
                cringeproof_moniker,
                howtocookathome_moniker
            ) VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email,
            github_username,
            github_id,
            github_username,
            avatar_url,
            monikers.get('soulfra.com'),
            monikers.get('deathtodata.com'),
            monikers.get('calriven.com'),
            monikers.get('cringeproof.com'),
            monikers.get('howtocookathome.com')
        ))

        master_user_id = cursor.lastrowid
        username = github_username

        # Mirror accounts to domain-specific users tables
        for domain, moniker in monikers.items():
            try:
                db.execute('''
                    INSERT INTO users (username, email, password_hash, display_name, github_id, github_username, avatar_url, created_at)
                    VALUES (?, ?, '', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (moniker, email, domain, github_id, github_username, avatar_url))
            except Exception as e:
                print(f"⚠️  Failed to create {domain} account: {e}")

        db.commit()

    # Set session (master auth + legacy compatibility)
    session['master_user_id'] = master_user_id
    session['master_username'] = username
    session['user_id'] = master_user_id  # Legacy compatibility
    session['github_username'] = github_username
    session['logged_in'] = True

    # Clear device flow data
    session.pop('device_code', None)
    session.pop('expires_at', None)

    return jsonify({
        'status': 'authorized',
        'redirect_url': '/',
        'user': {
            'id': master_user_id,
            'master_user_id': master_user_id,
            'username': username,
            'github_username': github_username,
            'email': email
        }
    })


@device_flow_bp.route('/auth/logout')
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'status': 'logged_out'})


@device_flow_bp.route('/auth/me')
def auth_me():
    """Get current logged-in user"""
    if not session.get('logged_in'):
        return jsonify({'logged_in': False}), 401

    return jsonify({
        'logged_in': True,
        'user_id': session.get('user_id'),
        'username': session.get('github_username')
    })


def init_device_flow_tables():
    """Create users table if it doesn't exist"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            github_id INTEGER UNIQUE,
            github_username TEXT,
            email TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    print("✅ Device flow auth tables ready")


if __name__ == '__main__':
    init_device_flow_tables()

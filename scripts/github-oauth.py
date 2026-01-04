#!/usr/bin/env python3
"""
GitHub OAuth Pairing - Like Discord's QR Login

Enables iPhone to pair with GitHub account for gist creation and README updates.

OAuth Flow:
1. User scans QR → lands on mobile-pair.html
2. Clicks "Connect GitHub"
3. Redirects to GitHub OAuth authorize
4. User approves permissions
5. GitHub redirects back with code
6. Exchange code for access token
7. Store token in session → paired!

Usage (Flask Integration):
    from scripts.github_oauth import init_oauth_routes
    init_oauth_routes(app)

Environment Variables:
    GITHUB_CLIENT_ID=your_client_id
    GITHUB_CLIENT_SECRET=your_client_secret
    GITHUB_REDIRECT_URI=https://cringeproof.com/oauth/callback
"""

import os
import secrets
import requests
from flask import request, redirect, session, jsonify, url_for
from datetime import datetime, timezone, timedelta

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'https://cringeproof.com/oauth/callback')

# OAuth scopes needed
SCOPES = 'gist,repo'  # gist = create gists, repo = update README

# Token storage (in production, use database)
active_sessions = {}

def init_oauth_routes(app):
    """Initialize OAuth routes in Flask app"""

    @app.route('/pair')
    def pair():
        """Landing page after scanning QR code"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Pair iPhone with GitHub</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }

        .card {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #333;
        }

        p {
            color: #666;
            margin-bottom: 2rem;
            line-height: 1.6;
        }

        .btn-connect {
            background: #24292e;
            color: white;
            border: none;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: background 0.2s;
        }

        .btn-connect:active {
            background: #1a1f23;
        }

        .icon {
            font-size: 1.5rem;
        }

        .features {
            margin-top: 2rem;
            text-align: left;
        }

        .feature {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            color: #555;
        }

        .feature-icon {
            background: #f0f0f0;
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>📱 Pair Your iPhone</h1>
        <p>Connect your GitHub account to start recording voice memos that automatically update your profile</p>

        <button class="btn-connect" onclick="connectGitHub()">
            <span class="icon">⚡</span>
            Connect GitHub Account
        </button>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">🎤</div>
                <div>Record voice memos from your iPhone</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🔒</div>
                <div>Secure GitHub OAuth (like Discord)</div>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <div>Auto-creates gists and updates README</div>
            </div>
        </div>
    </div>

    <script>
        function connectGitHub() {
            // Redirect to GitHub OAuth
            window.location.href = '/oauth/authorize';
        }
    </script>
</body>
</html>
"""

    @app.route('/oauth/authorize')
    def oauth_authorize():
        """Redirect to GitHub OAuth authorization"""

        if not GITHUB_CLIENT_ID:
            return jsonify({'error': 'GITHUB_CLIENT_ID not configured'}), 500

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state

        # Build authorization URL
        auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_REDIRECT_URI}&scope={SCOPES}&state={state}"

        return redirect(auth_url)

    @app.route('/oauth/callback')
    def oauth_callback():
        """Handle GitHub OAuth callback"""

        # Verify state to prevent CSRF
        state = request.args.get('state')
        if state != session.get('oauth_state'):
            return jsonify({'error': 'Invalid state parameter'}), 400

        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No code provided'}), 400

        # Exchange code for access token
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': GITHUB_REDIRECT_URI
            }
        )

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        if not access_token:
            return jsonify({'error': 'Failed to get access token', 'details': token_data}), 400

        # Get user info
        user_response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {access_token}'}
        )

        user_data = user_response.json()
        username = user_data.get('login')

        # Store session
        session_token = secrets.token_urlsafe(32)
        session['github_token'] = access_token
        session['github_username'] = username
        session['paired_at'] = datetime.now(timezone.utc).isoformat()

        # Store in active sessions
        active_sessions[session_token] = {
            'access_token': access_token,
            'username': username,
            'paired_at': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc) + timedelta(days=30)
        }

        # Redirect to success page
        return redirect(f'/pair/success?username={username}')

    @app.route('/pair/success')
    def pair_success():
        """Success page after pairing"""

        username = request.args.get('username', 'user')

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Paired Successfully!</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }}

        .card {{
            background: white;
            border-radius: 20px;
            padding: 2rem;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .success-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}

        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #333;
        }}

        p {{
            color: #666;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }}

        .username {{
            background: #f0f0f0;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            color: #24292e;
            margin-bottom: 2rem;
        }}

        .btn-record {{
            background: #667eea;
            color: white;
            border: none;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            font-weight: 600;
            transition: background 0.2s;
        }}

        .btn-record:active {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon">✅</div>
        <h1>Paired Successfully!</h1>
        <p>Your iPhone is now connected to GitHub</p>

        <div class="username">@{username}</div>

        <p>You can now record voice memos that will automatically create gists and update your profile README!</p>

        <button class="btn-record" onclick="startRecording()">
            🎤 Start Recording
        </button>
    </div>

    <script>
        function startRecording() {{
            // Redirect to CringeProof mobile interface
            window.location.href = 'https://cringeproof.com/mobile.html';
        }}

        // Auto-redirect after 3 seconds
        setTimeout(() => {{
            window.location.href = 'https://cringeproof.com/mobile.html';
        }}, 3000);
    </script>
</body>
</html>
"""

    @app.route('/api/pair/status')
    def pair_status():
        """Check if user is paired"""

        if 'github_token' in session:
            return jsonify({
                'paired': True,
                'username': session.get('github_username'),
                'paired_at': session.get('paired_at')
            })
        else:
            return jsonify({'paired': False})

def get_user_token():
    """Get GitHub access token for current user"""
    return session.get('github_token')

def is_paired():
    """Check if user has paired GitHub account"""
    return 'github_token' in session

def create_gist_for_user(filename, content, description, public=True):
    """Create gist using user's GitHub token"""

    token = get_user_token()
    if not token:
        raise ValueError("User not paired with GitHub")

    url = 'https://api.github.com/gists'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    data = {
        'description': description,
        'public': public,
        'files': {
            filename: {'content': content}
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create gist: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("GitHub OAuth Pairing - Configuration")
    print("=" * 60)
    print("\n1. Create GitHub OAuth App:")
    print("   https://github.com/settings/developers")
    print("\n2. Set environment variables:")
    print("   export GITHUB_CLIENT_ID=your_client_id")
    print("   export GITHUB_CLIENT_SECRET=your_client_secret")
    print("   export GITHUB_REDIRECT_URI=https://cringeproof.com/oauth/callback")
    print("\n3. Add routes to Flask app:")
    print("   from scripts.github_oauth import init_oauth_routes")
    print("   init_oauth_routes(app)")
    print("\n4. Test pairing flow:")
    print("   https://cringeproof.com/pair")
    print("\n" + "=" * 60)

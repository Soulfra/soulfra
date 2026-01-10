#!/usr/bin/env python3
"""
GitHub OAuth Routes for CringeProof

Integrates github_faucet.py with Flask to provide:
- GitHub login
- User sessions
- API key generation
- GitHub star validation

Routes:
- /github/login - Initiate OAuth
- /github/callback - OAuth callback
- /github/logout - Clear session
- /github/status - Check auth status

Usage in app.py:
```python
from github_auth_routes import github_auth_bp
app.register_blueprint(github_auth_bp)
```
"""

from flask import Blueprint, redirect, request, session, jsonify, url_for
from github_faucet import GitHubFaucet
from github_star_validator import GitHubStarValidator
from database import get_db
from datetime import datetime
import os
import json

# Create blueprint
github_auth_bp = Blueprint('github_auth', __name__, url_prefix='/github')

# Initialize GitHub services
faucet = GitHubFaucet()
star_validator = GitHubStarValidator()

# ==============================================================================
# ROUTES
# ==============================================================================

@github_auth_bp.route('/login')
def github_login():
    """
    Initiate GitHub OAuth flow

    Query params:
        redirect_to: URL to redirect after auth (default: /wall.html)

    Example:
        /github/login?redirect_to=/record-simple.html
    """
    # Store where to redirect after auth
    redirect_to = request.args.get('redirect_to', '/wall.html')
    session['auth_redirect_to'] = redirect_to

    # Generate OAuth URL (uses random state for security)
    auth_url = faucet.get_auth_url()

    return redirect(auth_url)


@github_auth_bp.route('/callback')
def github_callback():
    """
    GitHub OAuth callback

    Called by GitHub after user authorizes.
    Exchanges code for access token, fetches user info, creates session.
    """
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return jsonify({
            'success': False,
            'error': 'No authorization code received'
        }), 400

    try:
        # Exchange code for API key + user info
        result = faucet.process_callback(code=code)

        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'GitHub auth failed')
            }), 400

        # Store user info in session
        session['github_authenticated'] = True
        session['github_username'] = result['github_username']
        session['github_email'] = result.get('github_email')
        session['api_key'] = result['api_key']
        session['tier'] = result['tier']
        session['github_stats'] = {
            'repos': result.get('repos', 0),
            'commits': result.get('commits', 0),
            'followers': result.get('followers', 0)
        }

        # Set admin flag for owner or tier 4 users
        if result['github_username'].lower() == 'soulfra' or result['tier'] >= 4:
            session['is_admin'] = True
        else:
            session['is_admin'] = False

        # Check if user starred cringeproof repo
        has_starred = star_validator.check_star(
            github_username=result['github_username'],
            repo_owner='soulfra',
            repo_name='voice-archive'  # or 'cringeproof' if that's the repo name
        )
        session['has_starred_repo'] = has_starred

        # Store GitHub as auth provider in database
        db = get_db()

        # Check if this GitHub account is already linked to a user
        existing_provider = db.execute('''
            SELECT user_id FROM auth_providers
            WHERE provider = 'github' AND provider_username = ?
        ''', (result['github_username'],)).fetchone()

        if existing_provider:
            # Existing user - update last login
            user_id = existing_provider['user_id']
            db.execute('''
                UPDATE auth_providers
                SET last_login_at = ?, metadata = ?
                WHERE provider = 'github' AND provider_username = ?
            ''', (datetime.now(), json.dumps(result.get('github_stats', {})), result['github_username']))
            db.commit()

            # Load user info
            user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            session['user_id'] = user_id
            session['user_slug'] = user['user_slug']
        else:
            # New GitHub auth - create shadow account or prompt to claim
            session['pending_github_claim'] = True
            session['github_claim_data'] = {
                'username': result['github_username'],
                'email': result.get('github_email'),
                'stats': result.get('github_stats', {})
            }

        db.close()

        # Redirect to dashboard by default (user can override with redirect_to param)
        default_redirect = '/dashboard' if session.get('auth_redirect_to') is None else session.get('auth_redirect_to')
        redirect_to = session.pop('auth_redirect_to', default_redirect)

        return redirect(redirect_to)

    except Exception as e:
        print(f"GitHub callback error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@github_auth_bp.route('/logout')
def github_logout():
    """
    Clear GitHub session
    """
    session.pop('github_authenticated', None)
    session.pop('github_username', None)
    session.pop('github_email', None)
    session.pop('api_key', None)
    session.pop('tier', None)
    session.pop('github_stats', None)
    session.pop('has_starred_repo', None)

    redirect_to = request.args.get('redirect_to', '/')
    return redirect(redirect_to)


@github_auth_bp.route('/status')
def github_status():
    """
    Check GitHub authentication status

    Returns JSON with user info if authenticated

    Example response:
    {
        "authenticated": true,
        "username": "octocat",
        "email": "octocat@github.com",
        "tier": 2,
        "stats": {
            "repos": 15,
            "commits": 523,
            "followers": 42
        },
        "has_starred_repo": true
    }
    """
    if not session.get('github_authenticated'):
        return jsonify({
            'authenticated': False
        })

    return jsonify({
        'authenticated': True,
        'username': session.get('github_username'),
        'email': session.get('github_email'),
        'tier': session.get('tier', 1),
        'stats': session.get('github_stats', {}),
        'has_starred_repo': session.get('has_starred_repo', False)
    })


@github_auth_bp.route('/require-star')
def require_star():
    """
    Middleware-style endpoint to check if user has starred repo

    Used before allowing comments/reviews.
    Redirects to GitHub star page if not starred.
    """
    if not session.get('github_authenticated'):
        return redirect(url_for('github_auth.github_login',
                              redirect_to=request.referrer or '/'))

    if session.get('has_starred_repo'):
        # Already starred - allow action
        return jsonify({'success': True, 'has_starred': True})

    # Not starred - redirect to star page
    return jsonify({
        'success': False,
        'has_starred': False,
        'star_url': 'https://github.com/soulfra/voice-archive',
        'message': 'Please star the repo to access this feature'
    }), 403


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def require_github_auth(f):
    """
    Decorator to require GitHub authentication

    Usage:
    @app.route('/protected')
    @require_github_auth
    def protected_route():
        username = session['github_username']
        return f"Hello {username}"
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('github_authenticated'):
            return redirect(url_for('github_auth.github_login',
                                  redirect_to=request.url))
        return f(*args, **kwargs)

    return decorated_function


def get_current_github_user():
    """
    Get current authenticated GitHub user

    Returns:
        dict: User info or None if not authenticated
    """
    if not session.get('github_authenticated'):
        return None

    return {
        'username': session.get('github_username'),
        'email': session.get('github_email'),
        'tier': session.get('tier', 1),
        'api_key': session.get('api_key'),
        'stats': session.get('github_stats', {}),
        'has_starred_repo': session.get('has_starred_repo', False)
    }

#!/usr/bin/env python3
"""
Auth Bridge - Soulfra Master Auth Integration

Middleware that enforces Soulfra Master Auth on protected routes.
Any domain that requires_auth will redirect to Soulfra login if not authenticated.

Usage in app.py:
    from auth_bridge import AuthBridge

    auth_bridge = AuthBridge(app)

    # Protect a route
    @app.route('/protected')
    @auth_bridge.require_auth
    def protected_route():
        return "You are logged in!"

    # Or check auth status manually
    if auth_bridge.is_authenticated():
        user_id = auth_bridge.get_master_user_id()
"""

from flask import session, request, redirect, url_for, g, jsonify
from functools import wraps
import jwt
from typing import Optional, Dict
from domain_config.domain_loader import get_domain_config, get_domain_by_hostname


class AuthBridge:
    """
    Authentication bridge for Soulfra Master Auth

    Integrates with:
    - config/domains.yaml (domain auth requirements)
    - soulfra_master_auth.py (master auth system)
    - Session tokens and JWT validation
    """

    def __init__(self, app=None):
        """
        Initialize auth bridge

        Args:
            app: Flask app instance (optional)
        """
        self.app = app
        self.domain_config = get_domain_config()
        self.jwt_secret = None
        self.jwt_algorithm = 'HS256'

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize with Flask app

        Args:
            app: Flask app instance
        """
        self.app = app

        # Load JWT secret from app config or env
        import os
        self.jwt_secret = app.config.get('JWT_SECRET') or os.getenv('JWT_SECRET', 'soulfra-2026-device-flow-secret')

        # Register before_request handler
        app.before_request(self._check_auth_requirements)

        print("✅ Auth bridge initialized (Soulfra Master Auth)")

    def _check_auth_requirements(self):
        """
        Check authentication requirements before each request

        Called automatically via Flask before_request
        """
        # Skip for static files and API endpoints
        if request.path.startswith('/static') or request.path.startswith('/api'):
            return

        # Detect current domain
        hostname = request.headers.get('Host', '').lower()
        domain_config = get_domain_by_hostname(hostname)

        if not domain_config:
            # Unknown domain, use dev mode default
            dev_config = self.domain_config.get_dev_mode_config()
            if dev_config.get('enabled'):
                domain_slug = dev_config.get('default_domain', 'stpetepros')
                domain_config = self.domain_config.get_domain(domain_slug)

        # Store in request context
        g.domain_config = domain_config
        g.domain_slug = domain_config.get('slug') if domain_config else 'soulfra'

        # Check if this domain requires auth
        if domain_config and domain_config.get('requires_auth'):
            # Check if user is authenticated
            if not self.is_authenticated():
                # Exempt certain routes from auth requirement
                exempt_paths = ['/login', '/signup', '/api/master/login', '/api/master/signup', '/api/master/verify', '/']
                if request.path not in exempt_paths and not request.path.startswith('/signup/'):
                    # Redirect to login page
                    return redirect(url_for('auth_bridge_login', next=request.url))

    def is_authenticated(self) -> bool:
        """
        Check if current user is authenticated

        Returns:
            True if authenticated, False otherwise
        """
        # Check session for master_user_id
        if session.get('logged_in') and session.get('master_user_id'):
            return True

        # Check for JWT token in header or cookie
        token = self._get_token_from_request()
        if token:
            return self._validate_jwt_token(token) is not None

        return False

    def get_master_user_id(self) -> Optional[int]:
        """
        Get the authenticated user's master user ID

        Returns:
            Master user ID or None if not authenticated
        """
        # Check session first
        if session.get('master_user_id'):
            return session.get('master_user_id')

        # Check JWT token
        token = self._get_token_from_request()
        if token:
            payload = self._validate_jwt_token(token)
            if payload:
                return payload.get('master_user_id')

        return None

    def get_user_info(self) -> Optional[Dict]:
        """
        Get authenticated user information

        Returns:
            Dict with user info or None if not authenticated
        """
        if not self.is_authenticated():
            return None

        master_user_id = self.get_master_user_id()

        from database import get_db
        db = get_db()

        user = db.execute(
            'SELECT * FROM soulfra_master_users WHERE id = ?',
            (master_user_id,)
        ).fetchone()

        if not user:
            return None

        # Get domain-specific moniker
        domain_slug = g.get('domain_slug', 'soulfra')
        moniker_field = f"{domain_slug}_moniker"
        domain_moniker = user.get(moniker_field, user.get('master_username'))

        return {
            'master_user_id': user['id'],
            'email': user['email'],
            'username': user['master_username'],
            'display_name': user.get('display_name'),
            'domain_moniker': domain_moniker,
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login')
        }

    def _get_token_from_request(self) -> Optional[str]:
        """
        Extract JWT token from request

        Checks:
        1. Authorization header (Bearer token)
        2. Cookie (soulfra_token)
        3. Query parameter (?token=)

        Returns:
            JWT token string or None
        """
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove "Bearer " prefix

        # Check cookie
        token = request.cookies.get('soulfra_token')
        if token:
            return token

        # Check query parameter (for email links, QR codes, etc.)
        token = request.args.get('token')
        if token:
            return token

        return None

    def _validate_jwt_token(self, token: str) -> Optional[Dict]:
        """
        Validate JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict or None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            print("⚠️  JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"⚠️  Invalid JWT token: {e}")
            return None

    def require_auth(self, f):
        """
        Decorator to require authentication on a route

        Usage:
            @app.route('/protected')
            @auth_bridge.require_auth
            def protected_route():
                return "You are logged in!"
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.is_authenticated():
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth_bridge_login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def optional_auth(self, f):
        """
        Decorator for optional authentication (loads user if available)

        Usage:
            @app.route('/public')
            @auth_bridge.optional_auth
            def public_route():
                if g.user:
                    return f"Hello {g.user['username']}"
                return "Hello guest"
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            g.user = self.get_user_info()
            return f(*args, **kwargs)
        return decorated_function


# Global instance (initialized in app.py)
auth_bridge = None


def get_auth_bridge() -> Optional[AuthBridge]:
    """Get the global auth bridge instance"""
    return auth_bridge


def init_auth_bridge(app):
    """
    Initialize global auth bridge

    Args:
        app: Flask app instance
    """
    global auth_bridge
    auth_bridge = AuthBridge(app)
    return auth_bridge


# Flask routes for login/signup redirects
def register_auth_bridge_routes(app):
    """
    Register auth bridge routes

    Args:
        app: Flask app instance
    """
    @app.route('/login')
    def auth_bridge_login():
        """Login page (redirects to Soulfra master auth)"""
        next_url = request.args.get('next', '/')

        # If already logged in, redirect to next
        if session.get('logged_in'):
            return redirect(next_url)

        # Detect if this is Soulfra domain (provides auth)
        hostname = request.headers.get('Host', '').lower()
        domain_config = get_domain_by_hostname(hostname)

        if domain_config and domain_config.get('provides_auth'):
            # Render Soulfra login page
            from flask import render_template
            return render_template('auth/login.html', next=next_url)
        else:
            # Redirect to Soulfra master auth
            auth_config = get_domain_config().get_auth_flow_config()
            master_domain = auth_config.get('signup_redirect_domain', 'soulfra.com')

            # In dev mode, use localhost or local network IP
            if 'localhost' in hostname or '127.0.0.1' in hostname or '192.168.' in hostname:
                # Determine protocol (HTTPS if on network, HTTP if localhost)
                protocol = 'https' if '192.168.' in hostname else 'http'
                redirect_url = f"{protocol}://{hostname}/login?next={next_url}"
            else:
                redirect_url = f"https://{master_domain}/login?next={next_url}"

            return redirect(redirect_url)

    @app.route('/signup-soulfra')
    def auth_bridge_signup():
        """Signup page (creates Soulfra master account)"""
        next_url = request.args.get('next', '/signup/professional')

        # If already logged in, redirect to next
        if session.get('logged_in'):
            return redirect(next_url)

        # Render signup page
        from flask import render_template
        return render_template('auth/signup.html', next=next_url)

    @app.route('/api/auth/set-session', methods=['POST'])
    def set_session_from_token():
        """
        Convert JWT token to Flask session

        Called by login/signup forms after API returns token.
        Converts JWT auth → Flask session so server-side routes work.
        """
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Get user info from API response
        master_user_id = data.get('master_user_id')
        email = data.get('email')
        username = data.get('username')

        if not master_user_id or not email:
            return jsonify({'error': 'Missing required fields'}), 400

        # Set Flask session (required for /signup/professional and other routes)
        session['logged_in'] = True
        session['master_user_id'] = master_user_id
        session['email'] = email
        session['master_username'] = username

        return jsonify({'success': True})

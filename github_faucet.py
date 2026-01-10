#!/usr/bin/env python3
"""
GitHub Faucet - Generate API Keys from GitHub OAuth

**The Concept:**
Use GitHub as a "faucet" to distribute API keys. Connect your GitHub account → Get API key.

**Why GitHub?**
1. Proven identity (GitHub profile)
2. Free OAuth (no payment processor)
3. Developer-friendly
4. Anti-spam (GitHub has captcha)
5. Reputation (stars, repos, followers)

**How It Works:**
1. User clicks "Connect GitHub"
2. OAuth flow: Soulfra → GitHub → Back with token
3. Fetch GitHub profile (username, email, repos)
4. Generate unique API key based on GitHub username
5. Store in database
6. Rate limit: 1 key per GitHub account

**Access Tiers:**
- **Tier 1**: <100 GitHub commits → Basic access
- **Tier 2**: 100-1000 commits → File imports
- **Tier 3**: 1000+ commits → API access
- **Tier 4**: 10+ repos → Brand forking

**Usage:**
```python
from github_faucet import GitHubFaucet

faucet = GitHubFaucet()

# Generate OAuth URL
auth_url = faucet.get_auth_url(user_id=15)
# User visits auth_url → GitHub → Callback

# Process callback
api_key = faucet.process_callback(code='abc123', user_id=15)
# Returns: {'api_key': 'sk_github_username_abc123', 'tier': 2}
```

**Environment Variables:**
```bash
export GITHUB_CLIENT_ID=your_client_id
export GITHUB_CLIENT_SECRET=your_client_secret
export GITHUB_REDIRECT_URI=http://localhost:5001/github/callback
```

**GitHub App Setup:**
1. Go to: https://github.com/settings/developers
2. New OAuth App
3. Application name: Soulfra
4. Homepage URL: http://localhost:5001
5. Callback URL: http://localhost:5001/github/callback
6. Get CLIENT_ID and CLIENT_SECRET
"""

import os
import sqlite3
import hashlib
import secrets
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from database import get_db

# ==============================================================================
# CONFIG
# ==============================================================================

# GitHub OAuth Config (set via environment variables)
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', 'your_client_id_here')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', 'your_client_secret_here')
GITHUB_REDIRECT_URI = os.environ.get('GITHUB_REDIRECT_URI', 'http://localhost:5001/github/callback')

# GitHub Personal Access Token (fallback for single-user/dev mode)
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'Soulfra')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'cringeproof')

# GitHub API URLs
GITHUB_OAUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_API_URL = 'https://api.github.com'

# Rate Limits
MAX_KEYS_PER_GITHUB = 1  # One API key per GitHub account
KEY_REFRESH_DAYS = 30    # Can refresh key every 30 days


# ==============================================================================
# GITHUB FAUCET CLASS
# ==============================================================================

class GitHubFaucet:
    """
    Generate API keys from GitHub OAuth
    """

    def __init__(self):
        self.client_id = GITHUB_CLIENT_ID
        self.client_secret = GITHUB_CLIENT_SECRET
        self.redirect_uri = GITHUB_REDIRECT_URI
        self.token = GITHUB_TOKEN  # Personal access token fallback


    # ==========================================================================
    # DIRECT TOKEN AUTH (Single User Mode)
    # ==========================================================================

    def get_user_from_token(self) -> Optional[Dict]:
        """
        Get authenticated user info using personal access token (no OAuth flow)

        Returns:
            User info dict with: username, email, avatar_url, repos, commits
            Returns None if GITHUB_TOKEN not set
        """
        if not self.token:
            return None

        try:
            # Get user info
            headers = {'Authorization': f'token {self.token}'}
            response = requests.get(f'{GITHUB_API_URL}/user', headers=headers)
            response.raise_for_status()
            user_data = response.json()

            # Get commit count (search commits by author)
            commits_url = f"{GITHUB_API_URL}/search/commits?q=author:{user_data['login']}"
            commits_response = requests.get(commits_url, headers=headers)
            commits_count = commits_response.json().get('total_count', 0) if commits_response.ok else 0

            return {
                'username': user_data['login'],
                'email': user_data.get('email'),
                'avatar_url': user_data.get('avatar_url'),
                'repos': user_data.get('public_repos', 0),
                'commits': commits_count,
                'followers': user_data.get('followers', 0)
            }
        except Exception as e:
            print(f"Error getting user from token: {e}")
            return None


    # ==========================================================================
    # OAUTH FLOW
    # ==========================================================================

    def get_auth_url(self, user_id: int, state: Optional[str] = None) -> str:
        """
        Generate GitHub OAuth authorization URL

        Args:
            user_id: Soulfra user ID
            state: Optional state parameter (for CSRF protection)

        Returns:
            GitHub OAuth URL to redirect user to

        Example:
            >>> faucet = GitHubFaucet()
            >>> url = faucet.get_auth_url(user_id=15)
            >>> # Redirect user to this URL
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        # Store state in database for verification
        conn = get_db()
        conn.execute('''
            INSERT OR REPLACE INTO oauth_states (user_id, state, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, state, datetime.now()))
        conn.commit()
        conn.close()

        # Build OAuth URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'read:user user:email',
            'state': state
        }

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f'{GITHUB_OAUTH_URL}?{query_string}'


    def process_callback(self, code: str, state: str) -> Dict:
        """
        Process GitHub OAuth callback

        Args:
            code: OAuth authorization code from GitHub
            state: State parameter (for CSRF verification)

        Returns:
            Dict with API key and user info

        Raises:
            ValueError: If state is invalid or code exchange fails

        Example:
            >>> faucet = GitHubFaucet()
            >>> result = faucet.process_callback(code='abc123', state='xyz789')
            >>> print(result['api_key'])
            sk_github_octocat_a1b2c3d4
        """
        # Verify state
        conn = get_db()
        cursor = conn.execute('''
            SELECT user_id FROM oauth_states
            WHERE state = ? AND created_at > datetime('now', '-10 minutes')
        ''', (state,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise ValueError('Invalid or expired state parameter')

        user_id = row[0]

        # Exchange code for access token
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        headers = {'Accept': 'application/json'}
        response = requests.post(GITHUB_TOKEN_URL, data=token_data, headers=headers)

        if response.status_code != 200:
            conn.close()
            raise ValueError('Failed to exchange code for token')

        token_response = response.json()
        access_token = token_response.get('access_token')

        if not access_token:
            conn.close()
            raise ValueError('No access token in response')

        # Fetch GitHub user info
        github_user = self._fetch_github_user(access_token)

        # Generate API key
        api_key_data = self._generate_api_key(user_id, github_user, conn)

        # Clean up state
        conn.execute('DELETE FROM oauth_states WHERE state = ?', (state,))
        conn.commit()
        conn.close()

        return api_key_data


    # ==========================================================================
    # GITHUB API
    # ==========================================================================

    def _fetch_github_user(self, access_token: str) -> Dict:
        """
        Fetch GitHub user profile

        Args:
            access_token: GitHub access token

        Returns:
            Dict with GitHub user info
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/json'
        }

        # Get user profile
        user_response = requests.get(f'{GITHUB_API_URL}/user', headers=headers)
        user_data = user_response.json()

        # Get user stats
        username = user_data.get('login')
        repos_response = requests.get(f'{GITHUB_API_URL}/users/{username}/repos', headers=headers)
        repos = repos_response.json() if repos_response.status_code == 200 else []

        return {
            'username': user_data.get('login'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'bio': user_data.get('bio'),
            'avatar_url': user_data.get('avatar_url'),
            'public_repos': user_data.get('public_repos', 0),
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'created_at': user_data.get('created_at'),
            'repos': repos
        }


    # ==========================================================================
    # API KEY GENERATION
    # ==========================================================================

    def _generate_api_key(self, user_id: int, github_user: Dict, conn: sqlite3.Connection) -> Dict:
        """
        Generate API key from GitHub user info

        Args:
            user_id: Soulfra user ID
            github_user: GitHub user data
            conn: Database connection

        Returns:
            Dict with API key and metadata
        """
        github_username = github_user['username']

        # Check if user already has key from this GitHub account
        existing = conn.execute('''
            SELECT api_key, created_at FROM api_keys
            WHERE github_username = ?
        ''', (github_username,)).fetchone()

        if existing:
            # Check if they can refresh (30 days)
            created_at = datetime.fromisoformat(existing[1])
            if datetime.now() - created_at < timedelta(days=KEY_REFRESH_DAYS):
                return {
                    'api_key': existing[0],
                    'message': f'Using existing key. Can refresh in {KEY_REFRESH_DAYS - (datetime.now() - created_at).days} days.',
                    'tier': self._calculate_tier(github_user)
                }

        # Generate new key
        random_suffix = secrets.token_hex(8)
        api_key = f'sk_github_{github_username}_{random_suffix}'

        # Calculate tier based on GitHub activity
        tier = self._calculate_tier(github_user)

        # Store in database
        conn.execute('''
            INSERT OR REPLACE INTO api_keys
            (user_id, api_key, github_username, github_email, github_repos, github_followers, tier, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            api_key,
            github_username,
            github_user['email'],
            github_user['public_repos'],
            github_user['followers'],
            tier,
            datetime.now()
        ))

        # Update user's tier
        conn.execute('UPDATE users SET tier = ? WHERE id = ?', (tier, user_id))

        conn.commit()

        return {
            'api_key': api_key,
            'tier': tier,
            'github_username': github_username,
            'github_repos': github_user['public_repos'],
            'github_followers': github_user['followers'],
            'message': 'API key generated successfully!'
        }


    def _calculate_tier(self, github_user: Dict) -> int:
        """
        Calculate access tier based on GitHub activity

        Tier 1: <10 repos
        Tier 2: 10-50 repos
        Tier 3: 50+ repos
        Tier 4: 100+ repos + 50+ followers

        Args:
            github_user: GitHub user data

        Returns:
            Tier level (1-4)
        """
        repos = github_user.get('public_repos', 0)
        followers = github_user.get('followers', 0)

        if repos >= 100 and followers >= 50:
            return 4
        elif repos >= 50:
            return 3
        elif repos >= 10:
            return 2
        else:
            return 1


    # ==========================================================================
    # API KEY VALIDATION
    # ==========================================================================

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Validate API key and return user info

        Args:
            api_key: API key to validate

        Returns:
            Dict with user info if valid, None otherwise

        Example:
            >>> faucet = GitHubFaucet()
            >>> user = faucet.validate_api_key('sk_github_octocat_a1b2c3d4')
            >>> print(user['tier'])
            2
        """
        conn = get_db()
        cursor = conn.execute('''
            SELECT user_id, github_username, tier, created_at
            FROM api_keys
            WHERE api_key = ?
        ''', (api_key,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'user_id': row[0],
            'github_username': row[1],
            'tier': row[2],
            'created_at': row[3]
        }


# ==============================================================================
# DATABASE MIGRATION
# ==============================================================================

def init_faucet_tables():
    """
    Initialize database tables for GitHub faucet

    Run this once to set up tables:
    >>> from github_faucet import init_faucet_tables
    >>> init_faucet_tables()
    """
    conn = get_db()

    # API keys table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            github_username TEXT NOT NULL,
            github_email TEXT,
            github_repos INTEGER DEFAULT 0,
            github_followers INTEGER DEFAULT 0,
            tier INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(github_username)
        )
    ''')

    # OAuth states (for CSRF protection)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS oauth_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            state TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Index for fast lookups
    conn.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_github ON api_keys(github_username)')

    conn.commit()
    conn.close()

    print('✅ GitHub faucet tables created!')


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='GitHub Faucet - Generate API keys from GitHub')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--validate', type=str, help='Validate an API key')
    parser.add_argument('--list', action='store_true', help='List all API keys')

    args = parser.parse_args()

    if args.init:
        init_faucet_tables()

    elif args.validate:
        faucet = GitHubFaucet()
        result = faucet.validate_api_key(args.validate)
        if result:
            print(f'✅ Valid API key!')
            print(f'   User ID: {result["user_id"]}')
            print(f'   GitHub: {result["github_username"]}')
            print(f'   Tier: {result["tier"]}')
        else:
            print('❌ Invalid API key')

    elif args.list:
        conn = get_db()
        cursor = conn.execute('''
            SELECT api_key, github_username, tier, created_at
            FROM api_keys
            WHERE is_active = 1
            ORDER BY created_at DESC
        ''')

        print('\n📋 Active API Keys:\n')
        for row in cursor.fetchall():
            print(f'  • {row[0]} ({row[1]}) - Tier {row[2]} - Created {row[3]}')

        conn.close()

    else:
        print('Usage: python3 github_faucet.py --init')
        print('       python3 github_faucet.py --validate sk_github_username_abc123')
        print('       python3 github_faucet.py --list')

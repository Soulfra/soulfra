#!/usr/bin/env python3
"""
GitHub Star Validator

Validates that a GitHub user has starred a specific repository.

**Use Case:**
Before allowing user to leave comment/review, verify they've starred the repo.
This creates organic GitHub engagement similar to Airbnb's review gating.

**Flow:**
1. User connects GitHub (via github_faucet.py)
2. User attempts to comment on soulfra.com post
3. System checks: Has @username starred soulfra/soulfra repo?
4. If yes → Allow comment
5. If no → Redirect to GitHub with star prompt

**Domain → Repo Mapping:**
- soulfra.com → soulfra/soulfra
- deathtodata.com → soulfra/deathtodata
- calriven.com → soulfra/calriven

**Usage:**
```python
from github_star_validator import GitHubStarValidator

validator = GitHubStarValidator()

# Check if user starred repo
has_starred = validator.check_star(
    github_username='octocat',
    repo_owner='soulfra',
    repo_name='soulfra'
)

if has_starred:
    # Allow comment
else:
    # Show "Please star repo to comment" prompt
```

**API Endpoints:**
- GET /api/check-star?username=octocat&domain=soulfra.com
- POST /api/require-star (middleware for comment endpoints)

**Environment:**
Uses GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET from github_faucet.py
"""

import os
import requests
from typing import Dict, Optional
from datetime import datetime
from database import get_db

# GitHub API Config
GITHUB_API_URL = 'https://api.github.com'
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', 'your_client_id_here')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', 'your_client_secret_here')

# Domain → GitHub Repo Mapping
DOMAIN_REPO_MAP = {
    'soulfra.com': {'owner': 'soulfra', 'repo': 'soulfra'},
    'deathtodata.com': {'owner': 'soulfra', 'repo': 'deathtodata'},
    'calriven.com': {'owner': 'soulfra', 'repo': 'calriven'},

    # GitHub Pages URLs (development)
    'soulfra.github.io': {'owner': 'soulfra', 'repo': 'soulfra'},

    # Localhost (default to soulfra for testing)
    'localhost': {'owner': 'soulfra', 'repo': 'soulfra'},
    '127.0.0.1': {'owner': 'soulfra', 'repo': 'soulfra'},
    '192.168.1.87': {'owner': 'soulfra', 'repo': 'soulfra'},
}


class GitHubStarValidator:
    """
    Validate GitHub repository stars for engagement gating
    """

    def __init__(self):
        self.client_id = GITHUB_CLIENT_ID
        self.client_secret = GITHUB_CLIENT_SECRET


    # ==========================================================================
    # STAR VALIDATION
    # ==========================================================================

    def check_star(self, github_username: str, repo_owner: str, repo_name: str,
                   access_token: Optional[str] = None) -> Dict:
        """
        Check if a GitHub user has starred a repository

        Args:
            github_username: GitHub username to check
            repo_owner: Repository owner (e.g., 'soulfra')
            repo_name: Repository name (e.g., 'soulfra')
            access_token: Optional GitHub access token (for auth'd requests)

        Returns:
            Dict with:
                - has_starred (bool): True if user starred repo
                - starred_at (str): Timestamp when starred (if available)
                - star_count (int): Total stars on repo

        Example:
            >>> validator = GitHubStarValidator()
            >>> result = validator.check_star('octocat', 'soulfra', 'soulfra')
            >>> print(result['has_starred'])
            True
        """
        # Build API URL
        url = f'{GITHUB_API_URL}/users/{github_username}/starred/{repo_owner}/{repo_name}'

        # Headers
        headers = {'Accept': 'application/vnd.github.v3+json'}

        if access_token:
            headers['Authorization'] = f'token {access_token}'

        # Check if user starred repo
        # GitHub returns 204 if starred, 404 if not
        response = requests.get(url, headers=headers)

        has_starred = response.status_code == 204

        # Get repo info (star count)
        repo_url = f'{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}'
        repo_response = requests.get(repo_url, headers=headers)

        star_count = 0
        if repo_response.status_code == 200:
            repo_data = repo_response.json()
            star_count = repo_data.get('stargazers_count', 0)

        return {
            'has_starred': has_starred,
            'starred_at': datetime.now().isoformat() if has_starred else None,
            'star_count': star_count,
            'repo_owner': repo_owner,
            'repo_name': repo_name,
            'github_username': github_username
        }


    def check_star_for_domain(self, github_username: str, domain: str,
                              access_token: Optional[str] = None) -> Dict:
        """
        Check if user starred repo associated with domain

        Args:
            github_username: GitHub username
            domain: Domain name (e.g., 'soulfra.com')
            access_token: Optional GitHub access token

        Returns:
            Dict with star validation result + repo info

        Example:
            >>> validator = GitHubStarValidator()
            >>> result = validator.check_star_for_domain('octocat', 'soulfra.com')
            >>> if not result['has_starred']:
            ...     print(f"Please star {result['repo_url']}")
        """
        # Get repo for domain
        repo_info = self.get_repo_for_domain(domain)

        if not repo_info:
            return {
                'has_starred': False,
                'error': f'No GitHub repo mapped for domain: {domain}',
                'repo_owner': None,
                'repo_name': None
            }

        # Check star
        result = self.check_star(
            github_username=github_username,
            repo_owner=repo_info['owner'],
            repo_name=repo_info['repo'],
            access_token=access_token
        )

        # Add repo URL
        result['repo_url'] = f'https://github.com/{repo_info["owner"]}/{repo_info["repo"]}'
        result['domain'] = domain

        return result


    # ==========================================================================
    # DOMAIN MAPPING
    # ==========================================================================

    def get_repo_for_domain(self, domain: str) -> Optional[Dict]:
        """
        Get GitHub repo info for a domain

        Args:
            domain: Domain name (e.g., 'soulfra.com')

        Returns:
            Dict with 'owner' and 'repo', or None if not mapped

        Example:
            >>> validator = GitHubStarValidator()
            >>> repo = validator.get_repo_for_domain('soulfra.com')
            >>> print(repo)
            {'owner': 'soulfra', 'repo': 'soulfra'}
        """
        # Remove port if present
        domain_clean = domain.split(':')[0]

        # Remove www prefix
        if domain_clean.startswith('www.'):
            domain_clean = domain_clean[4:]

        return DOMAIN_REPO_MAP.get(domain_clean)


    # ==========================================================================
    # TIER-BASED STAR CHECKING
    # ==========================================================================

    def check_user_tier_from_stars(self, github_username: str) -> Dict:
        """
        Calculate user's tier based on how many network repos they've starred

        Args:
            github_username: GitHub username

        Returns:
            Dict with tier level, stars given, unlocked domains

        Tier Requirements:
            - Tier 0: 0 stars (entry, soulfra.com only)
            - Tier 1: 1 star (foundation domains)
            - Tier 2: 2+ stars (creative domains)
            - Tier 3: 10+ stars OR 50+ repos
            - Tier 4: 20+ stars + 100+ repos + 50+ followers

        Example:
            >>> validator = GitHubStarValidator()
            >>> tier = validator.check_user_tier_from_stars('octocat')
            >>> print(f"Tier {tier['tier']}: {tier['stars_given']} stars")
            Tier 2: 3 stars
        """
        # List of all network repos to check
        network_repos = [
            {'owner': 'soulfra', 'repo': 'soulfra', 'domain': 'soulfra.com'},
            {'owner': 'soulfra', 'repo': 'deathtodata', 'domain': 'deathtodata.com'},
            {'owner': 'soulfra', 'repo': 'calriven', 'domain': 'calriven.com'},
            {'owner': 'soulfra', 'repo': 'howtocookathome', 'domain': 'howtocookathome.com'},
            {'owner': 'soulfra', 'repo': 'stpetepros', 'domain': 'stpetepros.com'},
        ]

        starred_repos = []
        stars_given = 0

        # Check each network repo
        for repo in network_repos:
            result = self.check_star(github_username, repo['owner'], repo['repo'])

            if result['has_starred']:
                stars_given += 1
                starred_repos.append({
                    'repo': f"{repo['owner']}/{repo['repo']}",
                    'domain': repo['domain'],
                    'starred_at': result.get('starred_at')
                })

        # Get GitHub profile stats (for Tier 3/4 calculation)
        try:
            profile_url = f'{GITHUB_API_URL}/users/{github_username}'
            profile_response = requests.get(profile_url, timeout=5)

            if profile_response.status_code == 200:
                profile = profile_response.json()
                repos_count = profile.get('public_repos', 0)
                followers_count = profile.get('followers', 0)
            else:
                repos_count = 0
                followers_count = 0
        except:
            repos_count = 0
            followers_count = 0

        # Calculate tier
        tier = 0
        if stars_given >= 20 and repos_count >= 100 and followers_count >= 50:
            tier = 4
        elif stars_given >= 10 or repos_count >= 50:
            tier = 3
        elif stars_given >= 2:
            tier = 2
        elif stars_given >= 1:
            tier = 1

        # Determine unlocked domains based on tier
        if tier == 0:
            unlocked_domains = ['soulfra.com']
        elif tier == 1:
            unlocked_domains = ['soulfra.com', 'deathtodata.com', 'calriven.com']
        elif tier == 2:
            unlocked_domains = ['soulfra.com', 'deathtodata.com', 'calriven.com',
                              'howtocookathome.com', 'stpetepros.com']
        elif tier >= 3:
            unlocked_domains = [r['domain'] for r in network_repos]

        return {
            'tier': tier,
            'stars_given': stars_given,
            'starred_repos': starred_repos,
            'unlocked_domains': unlocked_domains,
            'github_stats': {
                'repos': repos_count,
                'followers': followers_count
            }
        }


    def get_stars_needed_for_next_tier(self, github_username: str) -> Dict:
        """
        Get number of stars needed for next tier

        Args:
            github_username: GitHub username

        Returns:
            Dict with current tier, next tier, stars needed

        Example:
            >>> validator = GitHubStarValidator()
            >>> needed = validator.get_stars_needed_for_next_tier('octocat')
            >>> print(f"Need {needed['stars_needed']} more stars for Tier {needed['next_tier']}")
            Need 1 more stars for Tier 2
        """
        current = self.check_user_tier_from_stars(github_username)
        current_tier = current['tier']
        stars_given = current['stars_given']

        if current_tier >= 4:
            return {
                'current_tier': current_tier,
                'next_tier': None,
                'stars_needed': 0,
                'message': 'Max tier reached!'
            }

        # Stars required for each tier
        tier_requirements = {
            1: 1,
            2: 2,
            3: 10,
            4: 20
        }

        next_tier = current_tier + 1
        required_stars = tier_requirements[next_tier]
        stars_needed = max(0, required_stars - stars_given)

        return {
            'current_tier': current_tier,
            'next_tier': next_tier,
            'stars_given': stars_given,
            'stars_needed': stars_needed,
            'message': f'Star {stars_needed} more repo(s) to reach Tier {next_tier}'
        }


    # ==========================================================================
    # DATABASE TRACKING
    # ==========================================================================

    def record_star_verification(self, github_username: str, domain: str,
                                 has_starred: bool) -> None:
        """
        Record star verification in database

        Args:
            github_username: GitHub username
            domain: Domain checked
            has_starred: Result of star check

        Creates record in api_keys table (or new star_verifications table)
        """
        db = get_db()

        # Update api_keys table with star info
        db.execute('''
            UPDATE api_keys
            SET github_starred_repo = ?,
                last_used_at = ?
            WHERE github_username = ?
        ''', (f"{domain}:{'starred' if has_starred else 'not_starred'}",
              datetime.now(), github_username))

        db.commit()
        db.close()


    def get_user_github_token(self, user_id: int) -> Optional[str]:
        """
        Get GitHub access token for user (from previous OAuth)

        Args:
            user_id: Soulfra user ID

        Returns:
            GitHub access token or None

        Note: This requires storing access tokens in database.
        Currently github_faucet.py doesn't store tokens, only API keys.

        For MVP, we'll use unauthenticated API (lower rate limit but works).
        """
        # TODO: Store GitHub access tokens in database
        # For now, return None (will use unauthenticated API)
        return None


# ==============================================================================
# FLASK BLUEPRINT
# ==============================================================================

from flask import Blueprint, request, jsonify, g

github_star_bp = Blueprint('github_star', __name__)


@github_star_bp.route('/api/check-star', methods=['GET'])
def check_star_endpoint():
    """
    Check if GitHub user has starred repo for current domain

    Query params:
        - username: GitHub username
        - domain: Optional domain (uses request.host if not provided)

    Returns:
        JSON with star validation result

    Example:
        GET /api/check-star?username=octocat&domain=soulfra.com

        Response:
        {
            "has_starred": true,
            "repo_url": "https://github.com/soulfra/soulfra",
            "star_count": 42,
            "starred_at": "2025-01-02T10:30:00"
        }
    """
    github_username = request.args.get('username')
    domain = request.args.get('domain', request.host)

    if not github_username:
        return jsonify({'error': 'username parameter required'}), 400

    validator = GitHubStarValidator()
    result = validator.check_star_for_domain(github_username, domain)

    return jsonify(result)


@github_star_bp.route('/api/require-star', methods=['POST'])
def require_star_middleware():
    """
    Middleware endpoint to gate actions behind GitHub star

    POST body:
        {
            "github_username": "octocat",
            "action": "comment",
            "domain": "soulfra.com"
        }

    Returns:
        - 200 if user has starred
        - 403 with star_url if user hasn't starred

    Example:
        POST /api/require-star
        {
            "github_username": "octocat",
            "action": "comment"
        }

        Response (if not starred):
        {
            "error": "GitHub star required",
            "message": "Please star our repo to comment",
            "repo_url": "https://github.com/soulfra/soulfra",
            "action_allowed": false
        }
    """
    data = request.get_json()

    github_username = data.get('github_username')
    action = data.get('action', 'comment')
    domain = data.get('domain', request.host)

    if not github_username:
        return jsonify({'error': 'github_username required'}), 400

    validator = GitHubStarValidator()
    result = validator.check_star_for_domain(github_username, domain)

    # Record verification
    validator.record_star_verification(github_username, domain, result['has_starred'])

    if result['has_starred']:
        return jsonify({
            'action_allowed': True,
            'message': f'Thank you for starring {result["repo_url"]}!',
            'star_count': result['star_count']
        }), 200
    else:
        return jsonify({
            'error': 'GitHub star required',
            'message': f'Please star our repo to {action}',
            'repo_url': result['repo_url'],
            'action_allowed': False,
            'help': f'Click the ⭐ button at {result["repo_url"]} then refresh this page'
        }), 403


@github_star_bp.route('/api/tier/from-stars/<github_username>', methods=['GET'])
def get_tier_from_stars_endpoint(github_username):
    """
    Get user's tier based on GitHub stars

    Returns:
        Tier level, stars given, unlocked domains

    Example:
        GET /api/tier/from-stars/octocat

        Response:
        {
            "tier": 2,
            "stars_given": 3,
            "starred_repos": [...],
            "unlocked_domains": ["soulfra.com", "deathtodata.com", ...],
            "github_stats": {"repos": 100, "followers": 20}
        }
    """
    validator = GitHubStarValidator()
    result = validator.check_user_tier_from_stars(github_username)

    return jsonify(result)


@github_star_bp.route('/api/tier/next-tier/<github_username>', methods=['GET'])
def get_next_tier_endpoint(github_username):
    """
    Get stars needed for next tier

    Returns:
        Current tier, next tier, stars needed

    Example:
        GET /api/tier/next-tier/octocat

        Response:
        {
            "current_tier": 1,
            "next_tier": 2,
            "stars_given": 1,
            "stars_needed": 1,
            "message": "Star 1 more repo(s) to reach Tier 2"
        }
    """
    validator = GitHubStarValidator()
    result = validator.get_stars_needed_for_next_tier(github_username)

    return jsonify(result)


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='GitHub Star Validator')
    parser.add_argument('--check', type=str, help='Check if username starred repo')
    parser.add_argument('--repo', type=str, default='soulfra/soulfra',
                       help='Repo in format owner/repo (default: soulfra/soulfra)')
    parser.add_argument('--domain', type=str, help='Check for domain (e.g., soulfra.com)')

    args = parser.parse_args()

    validator = GitHubStarValidator()

    if args.check and args.domain:
        # Check for domain
        result = validator.check_star_for_domain(args.check, args.domain)

        print(f'\n🔍 Checking {args.check} for {args.domain}...\n')

        if result.get('error'):
            print(f'❌ {result["error"]}')
        elif result['has_starred']:
            print(f'✅ @{args.check} HAS starred {result["repo_url"]}')
            print(f'   Total stars: {result["star_count"]}')
            print(f'   Starred at: {result["starred_at"]}')
        else:
            print(f'⭐ @{args.check} has NOT starred {result["repo_url"]}')
            print(f'   Please visit: {result["repo_url"]}')
            print(f'   Current stars: {result["star_count"]}')

    elif args.check:
        # Check for specific repo
        owner, repo = args.repo.split('/')
        result = validator.check_star(args.check, owner, repo)

        print(f'\n🔍 Checking {args.check} for {owner}/{repo}...\n')

        if result['has_starred']:
            print(f'✅ @{args.check} HAS starred {owner}/{repo}')
            print(f'   Total stars: {result["star_count"]}')
        else:
            print(f'⭐ @{args.check} has NOT starred {owner}/{repo}')
            print(f'   Please visit: https://github.com/{owner}/{repo}')
            print(f'   Current stars: {result["star_count"]}')

    else:
        print('Usage:')
        print('  python3 github_star_validator.py --check octocat --domain soulfra.com')
        print('  python3 github_star_validator.py --check octocat --repo soulfra/soulfra')

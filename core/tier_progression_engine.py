#!/usr/bin/env python3
"""
Tier Progression Engine - Amazon Affiliate-Style Tiered Domain Unlocking

Integrates with existing domain_unlock_engine.py and github_faucet.py to create
a unified 5-tier progression system where domains unlock based on GitHub stars
and engagement.

🎯 TIER SYSTEM (Amazon Affiliate Model)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier 0: Entry (FREE)
  - Domain: soulfra.com (entry point, always accessible)
  - Actions: Browse, read content, view comments
  - Ownership: 0%
  - Requirements: None

Tier 1: Commenter (1 GitHub Star)
  - Unlocks: soulfra.com commenting + 2 foundation domains
  - Domains: soulfra.com, deathtodata.com, calriven.com
  - Actions: Comment, leave reviews, submit ideas
  - Ownership: 5% soulfra + 2% each additional domain
  - Requirements: Star 1 GitHub repo

Tier 2: Contributor (2+ GitHub Stars)
  - Unlocks: All foundation domains + 1 creative domain
  - Domains: foundation (3) + howtocookathome.com OR stpetepros.com
  - Actions: Post content, create threads, voice memos
  - Ownership: 7% soulfra + 5% per additional domain
  - Requirements: Star 2+ repos, 5+ comments posted

Tier 3: Creator (10+ Stars OR 50+ Repos)
  - Unlocks: Random domain from daily rotation
  - Domains: All foundation + creative + 1 random from rotation
  - Actions: Create posts, moderate comments, admin features
  - Ownership: 10% soulfra + 10% per unlocked domain
  - Requirements: Star 10+ repos OR have 50+ public repos

Tier 4: VIP (100+ Repos + 50+ Followers)
  - Unlocks: All domains + ability to choose premium domains
  - Domains: Complete network access
  - Actions: Full admin, revenue sharing, domain selection
  - Ownership: 25% soulfra + 25% per domain + revenue share
  - Requirements: 100+ public repos + 50+ followers

📊 OWNERSHIP CALCULATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ownership % increases with:
- GitHub stars given to network repos
- Content posted (ideas, comments, reviews)
- Voice memos uploaded
- High-quality contributions (score 80+)
- Referrals (affiliate links)

Formula:
  ownership_% = base_tier_% + (stars × 0.5%) + (posts × 0.2%) + (referrals × 1%)

Max ownership per domain: 50%
Total network ownership: Sum across all domains

🔗 INTEGRATION POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Existing Systems:
  - domain_unlock_engine.py: unlock_domain(), check_unlock_eligibility()
  - github_faucet.py: _calculate_tier(), link_github_account()
  - github_star_validator.py: check_star_for_domain()
  - subdomain_router.py: detect_brand_from_subdomain()

New Functionality:
  - Unified tier calculation across all systems
  - Automatic domain unlocking on tier progression
  - Ownership percentage tracking
  - Tier-based feature gating

Usage:
    from tier_progression_engine import TierProgression

    tier = TierProgression(user_id=123)

    # Check user's current tier
    current = tier.get_current_tier()
    print(f"Tier {current['tier']}: {current['tier_name']}")

    # Check what's needed for next tier
    next_tier = tier.get_next_tier_requirements()
    print(f"Need {next_tier['stars_needed']} more stars")

    # Update tier after GitHub star
    tier.update_tier_from_github(github_username='octocat')
"""

from flask import Blueprint, request, jsonify, g
from database import get_db
from github_faucet import GitHubFaucet
from github_star_validator import GitHubStarValidator
from typing import Dict, List, Optional
import json
from datetime import datetime

tier_progression_bp = Blueprint('tier_progression', __name__)


# =============================================================================
# TIER CONFIGURATION
# =============================================================================

TIER_CONFIG = {
    0: {
        'name': 'Entry',
        'domains': ['soulfra.com'],
        'ownership_base': 0.0,
        'requirements': {
            'stars': 0,
            'repos': 0,
            'followers': 0,
            'comments': 0,
            'posts': 0
        },
        'features': ['browse', 'read_content', 'view_comments'],
        'description': 'Free entry - browse and read content'
    },
    1: {
        'name': 'Commenter',
        'domains': ['soulfra.com', 'deathtodata.com', 'calriven.com'],
        'ownership_base': 5.0,  # 5% soulfra + 2% each additional
        'ownership_per_additional': 2.0,
        'requirements': {
            'stars': 1,
            'repos': 0,
            'followers': 0,
            'comments': 0,
            'posts': 0
        },
        'features': ['browse', 'read_content', 'view_comments', 'post_comments', 'leave_reviews'],
        'description': 'Star 1 repo to unlock commenting + 2 foundation domains'
    },
    2: {
        'name': 'Contributor',
        'domains': ['soulfra.com', 'deathtodata.com', 'calriven.com', 'howtocookathome.com', 'stpetepros.com'],
        'ownership_base': 7.0,  # 7% soulfra + 5% per additional
        'ownership_per_additional': 5.0,
        'requirements': {
            'stars': 2,
            'repos': 0,
            'followers': 0,
            'comments': 5,
            'posts': 0
        },
        'features': ['all_tier1', 'post_content', 'create_threads', 'voice_memos'],
        'description': 'Star 2+ repos + 5 comments to unlock creative domains'
    },
    3: {
        'name': 'Creator',
        'domains': ['*'],  # All foundation + creative + 1 random rotation
        'ownership_base': 10.0,
        'ownership_per_additional': 10.0,
        'requirements': {
            'stars': 10,
            'repos_or': 50,  # 10 stars OR 50 repos
            'followers': 0,
            'comments': 10,
            'posts': 5
        },
        'features': ['all_tier2', 'create_posts', 'moderate_comments', 'admin_features'],
        'description': 'Star 10+ repos OR have 50+ repos to unlock rotation domains'
    },
    4: {
        'name': 'VIP',
        'domains': ['**'],  # All domains + premium selection
        'ownership_base': 25.0,
        'ownership_per_additional': 25.0,
        'requirements': {
            'stars': 20,
            'repos': 100,
            'followers': 50,
            'comments': 50,
            'posts': 20
        },
        'features': ['all_tier3', 'full_admin', 'revenue_share', 'domain_selection', 'custom_domains'],
        'description': 'VIP access - 100+ repos + 50+ followers unlocks everything'
    }
}


# =============================================================================
# TIER PROGRESSION ENGINE
# =============================================================================

class TierProgression:
    """
    Unified tier progression system integrating GitHub stars, engagement, and ownership
    """

    def __init__(self, user_id: Optional[int] = None, github_username: Optional[str] = None):
        """
        Initialize tier progression for a user

        Args:
            user_id: User ID in database
            github_username: GitHub username (alternative to user_id)
        """
        self.user_id = user_id
        self.github_username = github_username
        self.github_faucet = GitHubFaucet()
        self.star_validator = GitHubStarValidator()

        # If github_username provided, get user_id
        if github_username and not user_id:
            self.user_id = self._get_user_id_from_github(github_username)


    def _get_user_id_from_github(self, github_username: str) -> Optional[int]:
        """Get user_id from api_keys table"""
        db = get_db()
        row = db.execute('''
            SELECT user_id FROM api_keys WHERE github_username = ?
        ''', (github_username,)).fetchone()
        db.close()

        return row[0] if row else None


    # ==========================================================================
    # TIER CALCULATION
    # ==========================================================================

    def get_current_tier(self) -> Dict:
        """
        Calculate user's current tier

        Returns:
            Dict with:
                - tier (int): Tier number (0-4)
                - tier_name (str): Tier name
                - domains (list): Unlocked domains
                - ownership (dict): Ownership % per domain
                - features (list): Enabled features
                - next_tier (dict): Requirements for next tier
        """
        db = get_db()

        # Get user stats
        stats = self._get_user_stats(db)

        # Calculate tier from stats
        tier_level = self._calculate_tier_from_stats(stats)

        tier_config = TIER_CONFIG[tier_level]

        # Get unlocked domains
        unlocked_domains = self._get_unlocked_domains(db, tier_level)

        # Calculate ownership
        ownership = self._calculate_ownership(db, tier_level, stats)

        # Get next tier requirements
        next_tier = self._get_next_tier_requirements(tier_level, stats)

        db.close()

        return {
            'tier': tier_level,
            'tier_name': tier_config['name'],
            'description': tier_config['description'],
            'domains': unlocked_domains,
            'ownership': ownership,
            'features': tier_config['features'],
            'stats': stats,
            'next_tier': next_tier
        }


    def _get_user_stats(self, db) -> Dict:
        """
        Get comprehensive user statistics

        Returns:
            Dict with stars, repos, followers, comments, posts, etc.
        """
        if not self.user_id:
            return {
                'stars': 0,
                'repos': 0,
                'followers': 0,
                'comments': 0,
                'posts': 0,
                'reviews': 0,
                'voice_memos': 0,
                'ideas': 0
            }

        # Get GitHub stats from api_keys
        github_row = db.execute('''
            SELECT github_username, metadata FROM api_keys WHERE user_id = ?
        ''', (self.user_id,)).fetchone()

        github_stats = {}
        if github_row and github_row[1]:
            try:
                metadata = json.loads(github_row[1])
                github_stats = metadata.get('github_profile', {})
            except:
                pass

        # Count stars given to network repos
        stars_given = self._count_stars_given(github_row[0] if github_row else None)

        # Count comments
        comments_count = db.execute('''
            SELECT COUNT(*) FROM comments WHERE user_id = ?
        ''', (self.user_id,)).fetchone()[0]

        # Count posts (ideas)
        posts_count = db.execute('''
            SELECT COUNT(*) FROM ideas WHERE user_id = ?
        ''', (self.user_id,)).fetchone()[0]

        # Count reviews
        reviews_count = db.execute('''
            SELECT COUNT(*) FROM game_reviews WHERE github_username = ?
        ''', (github_row[0] if github_row else '',)).fetchone()[0]

        # Count voice memos
        voice_count = db.execute('''
            SELECT COUNT(*) FROM voice_memos WHERE user_id = ?
        ''', (self.user_id,)).fetchone()[0]

        return {
            'stars': stars_given,
            'repos': github_stats.get('public_repos', 0),
            'followers': github_stats.get('followers', 0),
            'comments': comments_count,
            'posts': posts_count,
            'reviews': reviews_count,
            'voice_memos': voice_count,
            'ideas': posts_count
        }


    def _count_stars_given(self, github_username: Optional[str]) -> int:
        """
        Count how many Soulfra network repos user has starred

        Args:
            github_username: GitHub username

        Returns:
            Number of network repos starred
        """
        if not github_username:
            return 0

        # List of Soulfra network repos
        network_repos = [
            {'owner': 'soulfra', 'repo': 'soulfra'},
            {'owner': 'soulfra', 'repo': 'deathtodata'},
            {'owner': 'soulfra', 'repo': 'calriven'},
            {'owner': 'soulfra', 'repo': 'howtocookathome'},
            {'owner': 'soulfra', 'repo': 'stpetepros'},
        ]

        stars_count = 0

        for repo in network_repos:
            result = self.star_validator.check_star(
                github_username,
                repo['owner'],
                repo['repo']
            )
            if result['has_starred']:
                stars_count += 1

        return stars_count


    def _calculate_tier_from_stats(self, stats: Dict) -> int:
        """
        Calculate tier level from user stats

        Args:
            stats: User statistics dict

        Returns:
            Tier level (0-4)
        """
        # Check tiers from highest to lowest
        for tier_level in [4, 3, 2, 1]:
            requirements = TIER_CONFIG[tier_level]['requirements']

            # Check all requirements
            meets_requirements = True

            if 'stars' in requirements and stats['stars'] < requirements['stars']:
                meets_requirements = False

            if 'repos' in requirements and stats['repos'] < requirements['repos']:
                meets_requirements = False

            if 'repos_or' in requirements:
                # Special: either stars OR repos
                if not (stats['stars'] >= requirements.get('stars', 0) or
                       stats['repos'] >= requirements['repos_or']):
                    meets_requirements = False

            if 'followers' in requirements and stats['followers'] < requirements['followers']:
                meets_requirements = False

            if 'comments' in requirements and stats['comments'] < requirements['comments']:
                meets_requirements = False

            if 'posts' in requirements and stats['posts'] < requirements['posts']:
                meets_requirements = False

            if meets_requirements:
                return tier_level

        # Default: Tier 0
        return 0


    def _get_unlocked_domains(self, db, tier_level: int) -> List[str]:
        """
        Get list of unlocked domains for tier

        Args:
            db: Database connection
            tier_level: User's tier level

        Returns:
            List of domain names
        """
        tier_config = TIER_CONFIG[tier_level]
        domain_list = tier_config['domains']

        # Special handling for '*' (all foundation + creative)
        if domain_list == ['*']:
            # Get all foundation + creative tier brands
            rows = db.execute('''
                SELECT domain FROM brands
                WHERE tier IN ('foundation', 'creative')
                AND domain IS NOT NULL
            ''').fetchall()
            return [row[0] for row in rows]

        # Special handling for '**' (all domains)
        elif domain_list == ['**']:
            rows = db.execute('''
                SELECT domain FROM brands WHERE domain IS NOT NULL
            ''').fetchall()
            return [row[0] for row in rows]

        # Regular domain list
        else:
            return domain_list


    def _calculate_ownership(self, db, tier_level: int, stats: Dict) -> Dict:
        """
        Calculate ownership percentages for unlocked domains

        Formula:
            base_% + (stars × 0.5%) + (posts × 0.2%) + (comments × 0.1%)

        Args:
            db: Database connection
            tier_level: User's tier level
            stats: User statistics

        Returns:
            Dict mapping domain → ownership %
        """
        tier_config = TIER_CONFIG[tier_level]
        base_ownership = tier_config['ownership_base']
        additional_ownership = tier_config.get('ownership_per_additional', 0.0)

        ownership = {}

        # Get unlocked domains
        domains = self._get_unlocked_domains(db, tier_level)

        for i, domain in enumerate(domains):
            if i == 0:
                # First domain (soulfra.com) gets base ownership
                domain_ownership = base_ownership
            else:
                # Additional domains get lower ownership
                domain_ownership = additional_ownership

            # Add bonuses
            domain_ownership += stats['stars'] * 0.5
            domain_ownership += stats['posts'] * 0.2
            domain_ownership += stats['comments'] * 0.1

            # Cap at 50%
            domain_ownership = min(domain_ownership, 50.0)

            ownership[domain] = round(domain_ownership, 2)

        return ownership


    def _get_next_tier_requirements(self, current_tier: int, stats: Dict) -> Dict:
        """
        Get requirements for next tier

        Args:
            current_tier: Current tier level
            stats: Current user statistics

        Returns:
            Dict with what's needed for next tier
        """
        if current_tier >= 4:
            return {
                'tier': 4,
                'message': 'Max tier reached!',
                'rewards': 'Full network access + revenue sharing'
            }

        next_tier = current_tier + 1
        requirements = TIER_CONFIG[next_tier]['requirements']

        needed = {}

        for key, required_value in requirements.items():
            if key == 'repos_or':
                # Special case: stars OR repos
                stars_needed = max(0, requirements.get('stars', 0) - stats['stars'])
                repos_needed = max(0, required_value - stats['repos'])
                needed['stars_or_repos'] = f"{stars_needed} stars OR {repos_needed} repos"
            else:
                current_value = stats.get(key, 0)
                if current_value < required_value:
                    needed[key] = required_value - current_value

        return {
            'next_tier': next_tier,
            'tier_name': TIER_CONFIG[next_tier]['name'],
            'needed': needed,
            'rewards': TIER_CONFIG[next_tier]['description']
        }


    # ==========================================================================
    # TIER UPDATES
    # ==========================================================================

    def update_tier_from_github(self, github_username: Optional[str] = None) -> Dict:
        """
        Update user tier based on latest GitHub activity

        Args:
            github_username: GitHub username (optional if already set)

        Returns:
            Dict with old_tier, new_tier, newly_unlocked_domains
        """
        if github_username:
            self.github_username = github_username
            self.user_id = self._get_user_id_from_github(github_username)

        if not self.user_id:
            return {
                'error': 'User not found',
                'message': 'GitHub account not linked'
            }

        # Get current tier
        old_tier_data = self.get_current_tier()
        old_tier = old_tier_data['tier']
        old_domains = set(old_tier_data['domains'])

        # Refresh GitHub stats via github_faucet
        # (This will update api_keys.metadata with latest GitHub profile)
        self.github_faucet.link_github_account(self.github_username, self.user_id)

        # Recalculate tier
        new_tier_data = self.get_current_tier()
        new_tier = new_tier_data['tier']
        new_domains = set(new_tier_data['domains'])

        # Find newly unlocked domains
        newly_unlocked = list(new_domains - old_domains)

        # Update domain_ownership table
        if newly_unlocked:
            self._unlock_domains(newly_unlocked, new_tier_data['ownership'])

        return {
            'old_tier': old_tier,
            'new_tier': new_tier,
            'tier_changed': old_tier != new_tier,
            'newly_unlocked_domains': newly_unlocked,
            'ownership': new_tier_data['ownership'],
            'next_tier': new_tier_data['next_tier']
        }


    def _unlock_domains(self, domains: List[str], ownership: Dict):
        """
        Unlock domains in domain_ownership table

        Args:
            domains: List of domain names to unlock
            ownership: Dict of domain → ownership %
        """
        db = get_db()

        for domain in domains:
            # Get brand_id for domain
            brand_row = db.execute('''
                SELECT id FROM brands WHERE domain = ?
            ''', (domain,)).fetchone()

            if not brand_row:
                continue

            brand_id = brand_row[0]
            ownership_pct = ownership.get(domain, 0.0)

            # Check if already unlocked
            existing = db.execute('''
                SELECT id FROM domain_ownership
                WHERE user_id = ? AND domain_id = ?
            ''', (self.user_id, brand_id)).fetchone()

            if existing:
                # Update ownership
                db.execute('''
                    UPDATE domain_ownership
                    SET ownership_percentage = ?
                    WHERE user_id = ? AND domain_id = ?
                ''', (ownership_pct, self.user_id, brand_id))
            else:
                # Create new ownership
                db.execute('''
                    INSERT INTO domain_ownership
                    (user_id, domain_id, ownership_percentage, unlock_source, unlocked_at)
                    VALUES (?, ?, ?, 'tier_progression', datetime('now'))
                ''', (self.user_id, brand_id, ownership_pct))

        db.commit()
        db.close()


    # ==========================================================================
    # DOMAIN ACCESS CHECK
    # ==========================================================================

    def can_access_domain(self, domain: str) -> Dict:
        """
        Check if user can access a specific domain

        Args:
            domain: Domain name to check

        Returns:
            Dict with allowed, tier, reason
        """
        tier_data = self.get_current_tier()

        allowed = domain in tier_data['domains']

        if allowed:
            return {
                'allowed': True,
                'tier': tier_data['tier'],
                'ownership': tier_data['ownership'].get(domain, 0.0),
                'message': f"Access granted (Tier {tier_data['tier']})"
            }
        else:
            return {
                'allowed': False,
                'tier': tier_data['tier'],
                'message': f"Domain locked - upgrade to {tier_data['next_tier']['tier_name']}",
                'next_tier': tier_data['next_tier']
            }


# ==============================================================================
# FLASK ENDPOINTS
# ==============================================================================

@tier_progression_bp.route('/api/tier/current', methods=['GET'])
def get_current_tier_endpoint():
    """
    Get current tier for user

    Query params:
        - user_id: User ID
        - github_username: GitHub username (alternative)

    Returns:
        Tier data with domains, ownership, features
    """
    user_id = request.args.get('user_id', type=int)
    github_username = request.args.get('github_username')

    if not user_id and not github_username:
        return jsonify({'error': 'user_id or github_username required'}), 400

    tier = TierProgression(user_id=user_id, github_username=github_username)
    result = tier.get_current_tier()

    return jsonify(result)


@tier_progression_bp.route('/api/tier/update', methods=['POST'])
def update_tier_endpoint():
    """
    Update tier from latest GitHub activity

    POST body:
    {
        "github_username": "octocat"
    }

    Returns:
        Tier progression data
    """
    data = request.get_json()
    github_username = data.get('github_username')

    if not github_username:
        return jsonify({'error': 'github_username required'}), 400

    tier = TierProgression(github_username=github_username)
    result = tier.update_tier_from_github()

    return jsonify(result)


@tier_progression_bp.route('/api/tier/check-access/<domain>', methods=['GET'])
def check_domain_access_endpoint(domain):
    """
    Check if user can access domain

    Query params:
        - user_id: User ID
        - github_username: GitHub username (alternative)

    Returns:
        Access permission data
    """
    user_id = request.args.get('user_id', type=int)
    github_username = request.args.get('github_username')

    if not user_id and not github_username:
        return jsonify({'error': 'user_id or github_username required'}), 400

    tier = TierProgression(user_id=user_id, github_username=github_username)
    result = tier.can_access_domain(domain)

    return jsonify(result)


# ==============================================================================
# CLI TESTING
# ==============================================================================

if __name__ == '__main__':
    print('\n🎯 Tier Progression Engine Test\n')

    # Test tier calculation
    print('Test 1: Get current tier for test user\n')

    tier = TierProgression(user_id=1)
    result = tier.get_current_tier()

    print(f"Tier: {result['tier']} - {result['tier_name']}")
    print(f"Description: {result['description']}")
    print(f"Unlocked domains: {len(result['domains'])}")
    for domain in result['domains']:
        ownership = result['ownership'].get(domain, 0.0)
        print(f"  • {domain}: {ownership}% ownership")

    print(f"\nUser stats:")
    for key, value in result['stats'].items():
        print(f"  {key}: {value}")

    print(f"\nNext tier: {result['next_tier']['tier_name']}")
    print(f"Needed:")
    for key, value in result['next_tier']['needed'].items():
        print(f"  {key}: {value}")

    print('\n✅ Tier progression tests complete!\n')

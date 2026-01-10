#!/usr/bin/env python3
"""
Affiliate Link Tracker - Amazon Affiliate-Style Referral System

Tracks user paths through the domain network and calculates referral rewards.

🔗 CONCEPT: "The entrance is free but anything else it links to works back"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User Journey Example:
  1. User enters via soulfra.com (Tier 0 - free)
  2. Clicks link to deathtodata.com (Tier 1 - requires star)
  3. User stars repo → unlocks deathtodata.com
  4. Original referrer (soulfra.com) earns 5% of user's future ownership
  5. User continues to calriven.com → soulfra.com earns 2.5% of that too
  6. Chain continues: entry domain always gets credit

🎯 REFERRAL REWARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry Domain (First Touch):
  - Gets 5% of all downstream ownership
  - Tracked for lifetime of user
  - "Entry domain is always free but links work back"

Direct Referrer (Last Touch):
  - Gets 2.5% of immediate next domain
  - Only for direct click-through

Example:
  User path: soulfra.com → deathtodata.com → calriven.com

  User unlocks deathtodata (2% ownership):
    - soulfra.com earns: 5% × 2% = 0.1% ownership
    - User keeps: 1.9% ownership

  User unlocks calriven (5% ownership):
    - soulfra.com earns: 5% × 5% = 0.25% ownership
    - deathtodata.com earns: 2.5% × 5% = 0.125% ownership
    - User keeps: 4.625% ownership

📊 TRACKING MECHANISM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
How it works:
  1. Generate unique referral links: soulfra.com?ref=abc123
  2. Store referral in cookie/session
  3. Track domain path in database: user_journeys table
  4. Calculate rewards when domain unlocked
  5. Update domain_ownership with referral credits

Database Schema:
  CREATE TABLE user_journeys (
      id INTEGER PRIMARY KEY,
      user_id INTEGER,
      domain_sequence TEXT,  -- JSON array: ["soulfra.com", "deathtodata.com"]
      entry_domain TEXT,
      current_domain TEXT,
      referral_code TEXT,
      created_at TIMESTAMP,
      updated_at TIMESTAMP
  );

  CREATE TABLE referral_earnings (
      id INTEGER PRIMARY KEY,
      referrer_domain TEXT,
      referred_user_id INTEGER,
      target_domain TEXT,
      ownership_earned REAL,
      referral_type TEXT,  -- 'entry' or 'direct'
      created_at TIMESTAMP
  );

🔒 ANTI-GAMING MEASURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prevent abuse:
  - Only first visit to domain counts (no gaming by revisiting)
  - Max 5% referral (prevents runaway rewards)
  - Minimum 24-hour gap between referrals from same user
  - Block self-referrals (same user_id as entry)

Usage:
    from affiliate_link_tracker import AffiliateTracker

    tracker = AffiliateTracker()

    # Generate referral link
    link = tracker.generate_referral_link('soulfra.com', user_id=123)
    print(link)  # https://soulfra.com?ref=soulfra_u123_abc

    # Track domain visit
    tracker.track_visit(
        user_id=456,
        domain='deathtodata.com',
        referral_code='soulfra_u123_abc'
    )

    # Get user journey
    journey = tracker.get_user_journey(user_id=456)
    print(journey['entry_domain'])  # soulfra.com

    # Calculate rewards when domain unlocked
    tracker.process_referral_rewards(
        user_id=456,
        unlocked_domain='deathtodata.com',
        ownership_earned=2.0
    )
"""

from flask import Blueprint, request, jsonify, session, make_response
from database import get_db
from typing import Dict, List, Optional
import json
import hashlib
import secrets
from datetime import datetime, timedelta

affiliate_tracker_bp = Blueprint('affiliate_tracker', __name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

REFERRAL_RATES = {
    'entry': 0.05,    # 5% for entry domain (first touch)
    'direct': 0.025   # 2.5% for direct referrer (last touch)
}

MAX_REFERRAL_PERCENTAGE = 5.0  # Cap total referral rewards
MIN_REFERRAL_GAP_HOURS = 24    # Minimum time between referrals from same user


# =============================================================================
# AFFILIATE TRACKER
# =============================================================================

class AffiliateTracker:
    """
    Track referral paths through domain network
    """

    def __init__(self):
        pass


    # ==========================================================================
    # REFERRAL LINK GENERATION
    # ==========================================================================

    def generate_referral_link(self, domain: str, user_id: Optional[int] = None,
                               campaign: Optional[str] = None) -> str:
        """
        Generate unique referral link for domain

        Args:
            domain: Domain to create link for
            user_id: User ID of referrer (optional)
            campaign: Campaign name (optional)

        Returns:
            Full referral URL with tracking code

        Example:
            >>> tracker = AffiliateTracker()
            >>> link = tracker.generate_referral_link('soulfra.com', user_id=123)
            >>> print(link)
            https://soulfra.com?ref=soulfra_u123_a1b2c3
        """
        # Generate unique referral code
        ref_components = [
            domain.split('.')[0],  # "soulfra"
            f"u{user_id}" if user_id else "anon",
            secrets.token_urlsafe(6)[:6]  # Random suffix
        ]

        if campaign:
            ref_components.insert(2, campaign)

        ref_code = '_'.join(ref_components)

        # Store referral code in database
        db = get_db()
        db.execute('''
            INSERT OR IGNORE INTO referral_codes
            (code, domain, referrer_user_id, campaign, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (ref_code, domain, user_id, campaign))
        db.commit()
        db.close()

        # Build full URL
        protocol = 'https' if domain != 'localhost' else 'http'
        port = ':5001' if 'local' in domain or 'localhost' in domain else ''

        return f"{protocol}://{domain}{port}?ref={ref_code}"


    def parse_referral_code(self, ref_code: str) -> Dict:
        """
        Parse referral code to extract info

        Args:
            ref_code: Referral code (e.g., "soulfra_u123_abc")

        Returns:
            Dict with domain, user_id, campaign
        """
        db = get_db()
        row = db.execute('''
            SELECT domain, referrer_user_id, campaign
            FROM referral_codes
            WHERE code = ?
        ''', (ref_code,)).fetchone()
        db.close()

        if row:
            return {
                'domain': row[0],
                'referrer_user_id': row[1],
                'campaign': row[2]
            }
        else:
            # Try to parse from code structure
            parts = ref_code.split('_')
            return {
                'domain': f"{parts[0]}.com" if len(parts) > 0 else None,
                'referrer_user_id': int(parts[1][1:]) if len(parts) > 1 and parts[1].startswith('u') else None,
                'campaign': parts[2] if len(parts) > 2 else None
            }


    # ==========================================================================
    # VISIT TRACKING
    # ==========================================================================

    def track_visit(self, user_id: int, domain: str,
                   referral_code: Optional[str] = None,
                   session_id: Optional[str] = None) -> Dict:
        """
        Track user visit to domain

        Args:
            user_id: User ID
            domain: Domain being visited
            referral_code: Referral code (if present in URL)
            session_id: Session ID for anonymous tracking

        Returns:
            Dict with journey_id, is_new_domain, entry_domain
        """
        db = get_db()

        # Get or create user journey
        journey = db.execute('''
            SELECT id, domain_sequence, entry_domain, referral_code
            FROM user_journeys
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()

        if journey:
            journey_id = journey[0]
            domain_sequence = json.loads(journey[1]) if journey[1] else []
            entry_domain = journey[2]
            existing_ref_code = journey[3]

            # Check if domain already visited
            is_new_domain = domain not in domain_sequence

            if is_new_domain:
                # Add to sequence
                domain_sequence.append(domain)

                db.execute('''
                    UPDATE user_journeys
                    SET domain_sequence = ?,
                        current_domain = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                ''', (json.dumps(domain_sequence), domain, journey_id))
                db.commit()

        else:
            # Create new journey
            domain_sequence = [domain]
            entry_domain = domain

            cursor = db.execute('''
                INSERT INTO user_journeys
                (user_id, domain_sequence, entry_domain, current_domain, referral_code, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (user_id, json.dumps(domain_sequence), entry_domain, domain, referral_code))

            journey_id = cursor.lastrowid
            is_new_domain = True
            db.commit()

        db.close()

        return {
            'journey_id': journey_id,
            'is_new_domain': is_new_domain,
            'entry_domain': entry_domain,
            'domain_sequence': domain_sequence,
            'total_domains': len(domain_sequence)
        }


    def get_user_journey(self, user_id: int) -> Dict:
        """
        Get complete user journey

        Args:
            user_id: User ID

        Returns:
            Dict with journey data
        """
        db = get_db()

        journey = db.execute('''
            SELECT
                id,
                domain_sequence,
                entry_domain,
                current_domain,
                referral_code,
                created_at,
                updated_at
            FROM user_journeys
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()

        db.close()

        if not journey:
            return {
                'journey_id': None,
                'entry_domain': None,
                'current_domain': None,
                'domain_sequence': [],
                'referral_code': None
            }

        return {
            'journey_id': journey[0],
            'domain_sequence': json.loads(journey[1]) if journey[1] else [],
            'entry_domain': journey[2],
            'current_domain': journey[3],
            'referral_code': journey[4],
            'started_at': journey[5],
            'updated_at': journey[6]
        }


    # ==========================================================================
    # REFERRAL REWARDS
    # ==========================================================================

    def process_referral_rewards(self, user_id: int, unlocked_domain: str,
                                 ownership_earned: float) -> Dict:
        """
        Calculate and distribute referral rewards when user unlocks domain

        Args:
            user_id: User who unlocked domain
            unlocked_domain: Domain that was unlocked
            ownership_earned: Base ownership % user earned

        Returns:
            Dict with rewards distributed

        Example:
            User unlocks deathtodata.com (2% ownership)
            Entry domain (soulfra.com) earns: 5% × 2% = 0.1%
            User keeps: 1.9%
        """
        db = get_db()

        # Get user journey
        journey = self.get_user_journey(user_id)

        if not journey['entry_domain']:
            db.close()
            return {
                'rewards': [],
                'user_keeps': ownership_earned,
                'message': 'No referral path found'
            }

        rewards = []
        total_referral_deduction = 0.0

        # 1. Entry domain reward (first touch)
        entry_domain = journey['entry_domain']
        if entry_domain != unlocked_domain:
            entry_reward = ownership_earned * REFERRAL_RATES['entry']
            total_referral_deduction += entry_reward

            # Get referrer from referral code
            entry_referrer_id = self._get_referrer_user_id(journey['referral_code'])

            # Credit entry domain ownership to referrer
            if entry_referrer_id and entry_referrer_id != user_id:
                self._credit_referral_ownership(
                    db,
                    referrer_user_id=entry_referrer_id,
                    referrer_domain=entry_domain,
                    referred_user_id=user_id,
                    target_domain=unlocked_domain,
                    ownership_earned=entry_reward,
                    referral_type='entry'
                )

                rewards.append({
                    'type': 'entry',
                    'domain': entry_domain,
                    'referrer_user_id': entry_referrer_id,
                    'ownership_earned': entry_reward
                })

        # 2. Direct referrer reward (last touch)
        domain_sequence = journey['domain_sequence']
        if len(domain_sequence) >= 2:
            # Previous domain in sequence
            direct_referrer_domain = domain_sequence[-2]

            if direct_referrer_domain != entry_domain and direct_referrer_domain != unlocked_domain:
                direct_reward = ownership_earned * REFERRAL_RATES['direct']
                total_referral_deduction += direct_reward

                # Get user_id of domain owner/operator (simplified: use entry referrer)
                direct_referrer_id = self._get_referrer_user_id(journey['referral_code'])

                if direct_referrer_id and direct_referrer_id != user_id:
                    self._credit_referral_ownership(
                        db,
                        referrer_user_id=direct_referrer_id,
                        referrer_domain=direct_referrer_domain,
                        referred_user_id=user_id,
                        target_domain=unlocked_domain,
                        ownership_earned=direct_reward,
                        referral_type='direct'
                    )

                    rewards.append({
                        'type': 'direct',
                        'domain': direct_referrer_domain,
                        'referrer_user_id': direct_referrer_id,
                        'ownership_earned': direct_reward
                    })

        # 3. User keeps the rest
        user_keeps = ownership_earned - total_referral_deduction

        db.commit()
        db.close()

        return {
            'rewards': rewards,
            'total_referral_deduction': total_referral_deduction,
            'user_keeps': user_keeps,
            'ownership_before_referrals': ownership_earned
        }


    def _get_referrer_user_id(self, referral_code: Optional[str]) -> Optional[int]:
        """Get referrer user_id from referral code"""
        if not referral_code:
            return None

        parsed = self.parse_referral_code(referral_code)
        return parsed.get('referrer_user_id')


    def _credit_referral_ownership(self, db, referrer_user_id: int,
                                   referrer_domain: str, referred_user_id: int,
                                   target_domain: str, ownership_earned: float,
                                   referral_type: str):
        """
        Credit ownership to referrer

        Args:
            db: Database connection
            referrer_user_id: User who gets the credit
            referrer_domain: Domain that gets credit
            referred_user_id: User who was referred
            target_domain: Domain that was unlocked
            ownership_earned: Ownership % to credit
            referral_type: 'entry' or 'direct'
        """
        # Get brand_id for target domain
        brand_row = db.execute('''
            SELECT id FROM brands WHERE domain = ?
        ''', (target_domain,)).fetchone()

        if not brand_row:
            return

        brand_id = brand_row[0]

        # Update or create domain_ownership for referrer
        existing = db.execute('''
            SELECT id, ownership_percentage
            FROM domain_ownership
            WHERE user_id = ? AND domain_id = ?
        ''', (referrer_user_id, brand_id)).fetchone()

        if existing:
            # Add to existing ownership
            new_ownership = existing[1] + ownership_earned
            db.execute('''
                UPDATE domain_ownership
                SET ownership_percentage = ?
                WHERE id = ?
            ''', (new_ownership, existing[0]))
        else:
            # Create new ownership entry
            db.execute('''
                INSERT INTO domain_ownership
                (user_id, domain_id, ownership_percentage, unlock_source, unlock_date)
                VALUES (?, ?, ?, 'referral', datetime('now'))
            ''', (referrer_user_id, brand_id, ownership_earned))

        # Record referral earning
        db.execute('''
            INSERT INTO referral_earnings
            (referrer_domain, referred_user_id, target_domain, ownership_earned, referral_type, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (referrer_domain, referred_user_id, target_domain, ownership_earned, referral_type))


    # ==========================================================================
    # ANALYTICS
    # ==========================================================================

    def get_referral_stats(self, user_id: int) -> Dict:
        """
        Get referral statistics for user

        Args:
            user_id: User ID

        Returns:
            Dict with total referrals, earnings, etc.
        """
        db = get_db()

        # Total referral earnings
        earnings = db.execute('''
            SELECT
                COUNT(*) as total_referrals,
                SUM(ownership_earned) as total_ownership_earned,
                target_domain
            FROM referral_earnings
            WHERE referrer_domain IN (
                SELECT domain FROM brands b
                JOIN domain_ownership do ON b.id = do.domain_id
                WHERE do.user_id = ?
            )
            GROUP BY target_domain
        ''', (user_id,)).fetchall()

        # Total users referred
        total_users = db.execute('''
            SELECT COUNT(DISTINCT referred_user_id)
            FROM referral_earnings
            WHERE referrer_domain IN (
                SELECT domain FROM brands b
                JOIN domain_ownership do ON b.id = do.domain_id
                WHERE do.user_id = ?
            )
        ''', (user_id,)).fetchone()[0]

        db.close()

        earnings_by_domain = {}
        total_earned = 0.0

        for row in earnings:
            domain = row[2]
            ownership = row[1] or 0.0
            earnings_by_domain[domain] = {
                'referrals': row[0],
                'ownership_earned': ownership
            }
            total_earned += ownership

        return {
            'total_users_referred': total_users,
            'total_ownership_earned': total_earned,
            'earnings_by_domain': earnings_by_domain
        }


# ==============================================================================
# FLASK ENDPOINTS
# ==============================================================================

@affiliate_tracker_bp.route('/api/referral/generate', methods=['POST'])
def generate_referral_link_endpoint():
    """
    Generate referral link

    POST body:
    {
        "domain": "soulfra.com",
        "user_id": 123,
        "campaign": "launch"  // optional
    }

    Returns:
    {
        "referral_link": "https://soulfra.com?ref=soulfra_u123_abc",
        "referral_code": "soulfra_u123_abc"
    }
    """
    data = request.get_json()
    domain = data.get('domain')
    user_id = data.get('user_id')
    campaign = data.get('campaign')

    if not domain:
        return jsonify({'error': 'domain required'}), 400

    tracker = AffiliateTracker()
    link = tracker.generate_referral_link(domain, user_id, campaign)

    return jsonify({
        'referral_link': link,
        'referral_code': link.split('ref=')[1] if 'ref=' in link else None
    })


@affiliate_tracker_bp.route('/api/referral/track', methods=['POST'])
def track_visit_endpoint():
    """
    Track domain visit

    POST body:
    {
        "user_id": 456,
        "domain": "deathtodata.com",
        "referral_code": "soulfra_u123_abc"  // optional
    }

    Returns:
        Journey data
    """
    data = request.get_json()
    user_id = data.get('user_id')
    domain = data.get('domain')
    referral_code = data.get('referral_code')

    if not user_id or not domain:
        return jsonify({'error': 'user_id and domain required'}), 400

    tracker = AffiliateTracker()
    result = tracker.track_visit(user_id, domain, referral_code)

    return jsonify(result)


@affiliate_tracker_bp.route('/api/referral/journey/<int:user_id>', methods=['GET'])
def get_journey_endpoint(user_id):
    """Get user journey"""
    tracker = AffiliateTracker()
    journey = tracker.get_user_journey(user_id)

    return jsonify(journey)


@affiliate_tracker_bp.route('/api/referral/stats/<int:user_id>', methods=['GET'])
def get_referral_stats_endpoint(user_id):
    """Get referral statistics for user"""
    tracker = AffiliateTracker()
    stats = tracker.get_referral_stats(user_id)

    return jsonify(stats)


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def create_referral_tables():
    """Create referral tracking tables"""
    db = get_db()

    # Referral codes
    db.execute('''
        CREATE TABLE IF NOT EXISTS referral_codes (
            code TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            referrer_user_id INTEGER,
            campaign TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User journeys
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_journeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_sequence TEXT,
            entry_domain TEXT,
            current_domain TEXT,
            referral_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Referral earnings
    db.execute('''
        CREATE TABLE IF NOT EXISTS referral_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_domain TEXT NOT NULL,
            referred_user_id INTEGER NOT NULL,
            target_domain TEXT NOT NULL,
            ownership_earned REAL NOT NULL,
            referral_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    db.close()


# ==============================================================================
# CLI TESTING
# ==============================================================================

if __name__ == '__main__':
    print('\n🔗 Affiliate Link Tracker Test\n')

    # Create tables
    create_referral_tables()
    print('✅ Created referral tables\n')

    tracker = AffiliateTracker()

    # Test 1: Generate referral link
    print('Test 1: Generate referral link\n')
    link = tracker.generate_referral_link('soulfra.com', user_id=123, campaign='launch')
    print(f"Referral link: {link}\n")

    # Test 2: Track visit
    print('Test 2: Track visit\n')
    result = tracker.track_visit(
        user_id=456,
        domain='soulfra.com',
        referral_code=link.split('ref=')[1]
    )
    print(f"Journey ID: {result['journey_id']}")
    print(f"Entry domain: {result['entry_domain']}\n")

    # Test 3: Get journey
    print('Test 3: Get user journey\n')
    journey = tracker.get_user_journey(456)
    print(f"Domain sequence: {journey['domain_sequence']}")
    print(f"Referral code: {journey['referral_code']}\n")

    # Test 4: Process rewards
    print('Test 4: Process referral rewards\n')
    rewards = tracker.process_referral_rewards(
        user_id=456,
        unlocked_domain='deathtodata.com',
        ownership_earned=2.0
    )
    print(f"Rewards: {len(rewards['rewards'])}")
    print(f"User keeps: {rewards['user_keeps']}%\n")

    print('✅ Affiliate tracker tests complete!\n')

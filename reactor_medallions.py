#!/usr/bin/env python3
"""
Reactor Medallion System - NYC Taxi Medallion Model for Voice Authors

Like taxi medallions but for publishing voice reactions:
- Limited supply of medallions (scarce credibility)
- Buy medallion = earn right to publish reactions
- Medallion holders earn from payouts
- Medallions tradeable (secondary market)
- Bad actors lose medallions (crash-and-burn penalty)

Medallion Types:
1. **Founding Member** - $1 stake, lifetime access, grandfathered in
2. **Standard Medallion** - Market rate ($10-$1000+), tradeable
3. **Earned Medallion** - Free, earned through accuracy/engagement

Staking Model:
- Stake USD → Get medallion → Publish reactions → Earn revenue share
- Lose medallion if crash-and-burn rate > 70%
- Trade medallions on secondary market

Usage:
    # Mint new medallion (admin only)
    python3 reactor_medallions.py mint --user-id 1 --type standard --price 50.00

    # Buy medallion
    python3 reactor_medallions.py buy --user-id 2 --medallion-id 5

    # Stake for medallion
    python3 reactor_medallions.py stake --user-id 3 --amount 100.00

    # Revoke medallion (crash-and-burn penalty)
    python3 reactor_medallions.py revoke --medallion-id 8 --reason "70% crash rate"

    # Market prices
    python3 reactor_medallions.py market-prices
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db


class ReactorMedallionSystem:
    """NYC Taxi Medallion-style system for voice reactor credibility"""

    # Medallion supply limits
    MAX_FOUNDING_MEMBERS = 100
    MAX_STANDARD_MEDALLIONS = 1000
    UNLIMITED_EARNED_MEDALLIONS = True

    # Pricing
    FOUNDING_MEMBER_PRICE = 1.00
    BASE_STANDARD_PRICE = 50.00

    # Revocation thresholds
    CRASH_BURN_THRESHOLD = 70.0  # % crash rate = medallion revoked

    def __init__(self):
        self.db = get_db()
        self._ensure_tables()

    def _ensure_tables(self):
        """Create medallion tables"""

        # Medallion registry
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS reactor_medallions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medallion_type TEXT NOT NULL,  -- founding_member, standard, earned
                owner_user_id INTEGER REFERENCES users(id),
                original_price REAL,
                current_market_value REAL,
                minted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acquired_at TIMESTAMP,
                revoked_at TIMESTAMP,
                revocation_reason TEXT,
                is_active BOOLEAN DEFAULT 1,
                total_earned REAL DEFAULT 0.0,
                UNIQUE(medallion_type, owner_user_id) ON CONFLICT REPLACE
            )
        ''')

        # Medallion marketplace (secondary market)
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS medallion_marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medallion_id INTEGER REFERENCES reactor_medallions(id),
                seller_user_id INTEGER REFERENCES users(id),
                asking_price REAL NOT NULL,
                listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sold_at TIMESTAMP,
                buyer_user_id INTEGER REFERENCES users(id),
                sale_price REAL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # Medallion staking (escrow for medallion purchase)
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS medallion_stakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                amount REAL NOT NULL,
                staked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                medallion_id INTEGER REFERENCES reactor_medallions(id),
                withdrawn_at TIMESTAMP,
                withdrawn_amount REAL
            )
        ''')

        self.db.commit()

    def get_medallion_counts(self) -> Dict:
        """Get current medallion counts by type"""
        counts = {}

        for mtype in ['founding_member', 'standard', 'earned']:
            count = self.db.execute('''
                SELECT COUNT(*) as count
                FROM reactor_medallions
                WHERE medallion_type = ?
                  AND is_active = 1
                  AND revoked_at IS NULL
            ''', (mtype,)).fetchone()

            counts[mtype] = count['count'] if count else 0

        return counts

    def can_mint_medallion(self, medallion_type: str) -> bool:
        """Check if new medallion can be minted"""
        counts = self.get_medallion_counts()

        if medallion_type == 'founding_member':
            return counts['founding_member'] < self.MAX_FOUNDING_MEMBERS
        elif medallion_type == 'standard':
            return counts['standard'] < self.MAX_STANDARD_MEDALLIONS
        elif medallion_type == 'earned':
            return True  # No limit on earned medallions
        else:
            return False

    def calculate_market_price(self, medallion_type: str) -> float:
        """
        Calculate current market price for medallion

        Price increases as supply decreases (Dutch auction style)
        """
        if medallion_type == 'founding_member':
            return self.FOUNDING_MEMBER_PRICE

        counts = self.get_medallion_counts()
        remaining = self.MAX_STANDARD_MEDALLIONS - counts['standard']

        # Price increases as medallions sell out
        # 1000 remaining = $50
        # 500 remaining = $100
        # 100 remaining = $500
        # 10 remaining = $1000
        scarcity_multiplier = 1 + (1 - remaining / self.MAX_STANDARD_MEDALLIONS) * 19
        market_price = self.BASE_STANDARD_PRICE * scarcity_multiplier

        return round(market_price, 2)

    def mint_medallion(
        self,
        user_id: int,
        medallion_type: str,
        price: Optional[float] = None
    ) -> Dict:
        """
        Mint new medallion and assign to user

        Args:
            user_id: User to receive medallion
            medallion_type: founding_member, standard, earned
            price: Override price (None = use market price)

        Returns:
            Medallion info dict
        """
        if not self.can_mint_medallion(medallion_type):
            return {'success': False, 'error': f'Cannot mint {medallion_type} - limit reached'}

        # Calculate price
        if price is None:
            if medallion_type == 'earned':
                price = 0.0
            else:
                price = self.calculate_market_price(medallion_type)

        # Check if user already has this medallion type
        existing = self.db.execute('''
            SELECT id FROM reactor_medallions
            WHERE owner_user_id = ?
              AND medallion_type = ?
              AND is_active = 1
        ''', (user_id, medallion_type)).fetchone()

        if existing:
            return {'success': False, 'error': f'User already has {medallion_type} medallion'}

        # Mint medallion
        cursor = self.db.execute('''
            INSERT INTO reactor_medallions
            (medallion_type, owner_user_id, original_price, current_market_value, acquired_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (medallion_type, user_id, price, price))

        medallion_id = cursor.lastrowid
        self.db.commit()

        return {
            'success': True,
            'medallion_id': medallion_id,
            'medallion_type': medallion_type,
            'user_id': user_id,
            'price': price
        }

    def stake_for_medallion(self, user_id: int, amount: float) -> Dict:
        """
        Stake USD for medallion purchase

        User stakes amount → If enough for medallion, auto-mint

        Returns:
            Stake/medallion info
        """
        # Record stake
        cursor = self.db.execute('''
            INSERT INTO medallion_stakes
            (user_id, amount)
            VALUES (?, ?)
        ''', (user_id, amount))

        stake_id = cursor.lastrowid

        # Check total staked amount
        total_staked = self.db.execute('''
            SELECT SUM(amount) as total
            FROM medallion_stakes
            WHERE user_id = ?
              AND withdrawn_at IS NULL
        ''', (user_id,)).fetchone()

        total = total_staked['total'] if total_staked else 0

        # Check if enough for founding member
        if total >= self.FOUNDING_MEMBER_PRICE and total < self.BASE_STANDARD_PRICE:
            medallion_type = 'founding_member'
        elif total >= self.calculate_market_price('standard'):
            medallion_type = 'standard'
        else:
            self.db.commit()
            return {
                'success': True,
                'stake_id': stake_id,
                'amount_staked': amount,
                'total_staked': total,
                'medallion_minted': False,
                'needed_for_medallion': self.calculate_market_price('standard') - total
            }

        # Mint medallion
        medallion = self.mint_medallion(user_id, medallion_type)

        if medallion['success']:
            # Link stake to medallion
            self.db.execute('''
                UPDATE medallion_stakes
                SET medallion_id = ?
                WHERE user_id = ?
                  AND withdrawn_at IS NULL
            ''', (medallion['medallion_id'], user_id))

            self.db.commit()

            return {
                'success': True,
                'stake_id': stake_id,
                'amount_staked': amount,
                'total_staked': total,
                'medallion_minted': True,
                'medallion_id': medallion['medallion_id'],
                'medallion_type': medallion_type
            }
        else:
            self.db.commit()
            return medallion

    def check_revocation_eligibility(self, user_id: int) -> Dict:
        """
        Check if user's medallion should be revoked due to poor performance

        Revoke if crash-and-burn rate > 70%

        Returns:
            Revocation eligibility info
        """
        from reactor_payouts import ReactorPayoutSystem

        # Get reactor weights
        weights = self.db.execute('''
            SELECT crash_burn_count, accurate_count
            FROM reactor_weights
            WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if not weights:
            return {'should_revoke': False, 'reason': 'No prediction history'}

        total_predictions = weights['crash_burn_count'] + weights['accurate_count']

        if total_predictions < 10:
            return {'should_revoke': False, 'reason': 'Not enough predictions (need 10+)'}

        crash_rate = (weights['crash_burn_count'] / total_predictions) * 100

        if crash_rate > self.CRASH_BURN_THRESHOLD:
            return {
                'should_revoke': True,
                'crash_rate': crash_rate,
                'reason': f'{crash_rate:.1f}% crash rate (threshold: {self.CRASH_BURN_THRESHOLD}%)'
            }

        return {'should_revoke': False, 'crash_rate': crash_rate}

    def revoke_medallion(self, medallion_id: int, reason: str) -> Dict:
        """
        Revoke medallion (bad actor penalty)

        Returns:
            Revocation result
        """
        medallion = self.db.execute('''
            SELECT * FROM reactor_medallions WHERE id = ?
        ''', (medallion_id,)).fetchone()

        if not medallion:
            return {'success': False, 'error': 'Medallion not found'}

        if medallion['revoked_at']:
            return {'success': False, 'error': 'Medallion already revoked'}

        # Revoke medallion
        self.db.execute('''
            UPDATE reactor_medallions
            SET is_active = 0,
                revoked_at = CURRENT_TIMESTAMP,
                revocation_reason = ?
            WHERE id = ?
        ''', (reason, medallion_id))

        self.db.commit()

        return {
            'success': True,
            'medallion_id': medallion_id,
            'user_id': medallion['owner_user_id'],
            'reason': reason
        }

    def list_on_marketplace(self, medallion_id: int, asking_price: float) -> Dict:
        """
        List medallion for sale on secondary market

        Returns:
            Listing info
        """
        medallion = self.db.execute('''
            SELECT * FROM reactor_medallions WHERE id = ?
        ''', (medallion_id,)).fetchone()

        if not medallion or not medallion['is_active']:
            return {'success': False, 'error': 'Medallion not active'}

        # Create listing
        cursor = self.db.execute('''
            INSERT INTO medallion_marketplace
            (medallion_id, seller_user_id, asking_price)
            VALUES (?, ?, ?)
        ''', (medallion_id, medallion['owner_user_id'], asking_price))

        self.db.commit()

        return {
            'success': True,
            'listing_id': cursor.lastrowid,
            'medallion_id': medallion_id,
            'asking_price': asking_price
        }

    def buy_from_marketplace(self, listing_id: int, buyer_user_id: int) -> Dict:
        """
        Buy medallion from secondary market

        Returns:
            Purchase result
        """
        listing = self.db.execute('''
            SELECT * FROM medallion_marketplace WHERE id = ?
        ''', (listing_id,)).fetchone()

        if not listing or not listing['is_active']:
            return {'success': False, 'error': 'Listing not active'}

        # Transfer medallion
        self.db.execute('''
            UPDATE reactor_medallions
            SET owner_user_id = ?,
                acquired_at = CURRENT_TIMESTAMP,
                current_market_value = ?
            WHERE id = ?
        ''', (buyer_user_id, listing['asking_price'], listing['medallion_id']))

        # Mark listing as sold
        self.db.execute('''
            UPDATE medallion_marketplace
            SET is_active = 0,
                sold_at = CURRENT_TIMESTAMP,
                buyer_user_id = ?,
                sale_price = ?
            WHERE id = ?
        ''', (buyer_user_id, listing['asking_price'], listing_id))

        self.db.commit()

        return {
            'success': True,
            'medallion_id': listing['medallion_id'],
            'buyer_user_id': buyer_user_id,
            'seller_user_id': listing['seller_user_id'],
            'sale_price': listing['asking_price']
        }

    def get_marketplace_listings(self) -> List[Dict]:
        """Get active marketplace listings"""
        return [dict(l) for l in self.db.execute('''
            SELECT
                mm.*,
                rm.medallion_type,
                rm.total_earned,
                u.username as seller_username
            FROM medallion_marketplace mm
            JOIN reactor_medallions rm ON mm.medallion_id = rm.id
            JOIN users u ON mm.seller_user_id = u.id
            WHERE mm.is_active = 1
            ORDER BY mm.asking_price ASC
        ''').fetchall()]


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Reactor Medallion System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Mint medallion
    mint_parser = subparsers.add_parser('mint', help='Mint new medallion')
    mint_parser.add_argument('--user-id', type=int, required=True)
    mint_parser.add_argument('--type', required=True, choices=['founding_member', 'standard', 'earned'])
    mint_parser.add_argument('--price', type=float)

    # Stake for medallion
    stake_parser = subparsers.add_parser('stake', help='Stake USD for medallion')
    stake_parser.add_argument('--user-id', type=int, required=True)
    stake_parser.add_argument('--amount', type=float, required=True)

    # Revoke medallion
    revoke_parser = subparsers.add_parser('revoke', help='Revoke medallion')
    revoke_parser.add_parser('--medallion-id', type=int, required=True)
    revoke_parser.add_argument('--reason', required=True)

    # Market prices
    prices_parser = subparsers.add_parser('market-prices', help='Show current medallion prices')

    # Marketplace listings
    market_parser = subparsers.add_parser('marketplace', help='View marketplace listings')

    args = parser.parse_args()

    medallion_system = ReactorMedallionSystem()

    if args.command == 'mint':
        result = medallion_system.mint_medallion(args.user_id, args.type, args.price)
        if result['success']:
            print(f"\n✅ Minted {result['medallion_type']} medallion #{result['medallion_id']}")
            print(f"   User: #{result['user_id']}")
            print(f"   Price: ${result['price']:.2f}\n")
        else:
            print(f"\n❌ Error: {result['error']}\n")

    elif args.command == 'stake':
        result = medallion_system.stake_for_medallion(args.user_id, args.amount)
        print(f"\n💰 Staked ${args.amount:.2f} for User #{args.user_id}")
        print(f"   Total Staked: ${result['total_staked']:.2f}")
        if result['medallion_minted']:
            print(f"   ✅ Medallion minted! Type: {result['medallion_type']} (#{result['medallion_id']})")
        else:
            print(f"   Need ${result['needed_for_medallion']:.2f} more for medallion\n")

    elif args.command == 'revoke':
        result = medallion_system.revoke_medallion(args.medallion_id, args.reason)
        if result['success']:
            print(f"\n❌ Revoked medallion #{result['medallion_id']}")
            print(f"   Reason: {result['reason']}\n")
        else:
            print(f"\n❌ Error: {result['error']}\n")

    elif args.command == 'market-prices':
        counts = medallion_system.get_medallion_counts()
        founding_price = medallion_system.FOUNDING_MEMBER_PRICE
        standard_price = medallion_system.calculate_market_price('standard')

        print("\n💎 Current Medallion Prices\n")
        print(f"Founding Member: ${founding_price:.2f} ({counts['founding_member']}/{medallion_system.MAX_FOUNDING_MEMBERS} minted)")
        print(f"Standard: ${standard_price:.2f} ({counts['standard']}/{medallion_system.MAX_STANDARD_MEDALLIONS} minted)")
        print(f"Earned: FREE ({counts['earned']} issued)\n")

    elif args.command == 'marketplace':
        listings = medallion_system.get_marketplace_listings()
        print(f"\n🏪 Medallion Marketplace ({len(listings)} listings)\n")
        for listing in listings:
            print(f"#{listing['id']} - {listing['medallion_type']} by {listing['seller_username']}")
            print(f"   Price: ${listing['asking_price']:.2f} | Earned: ${listing['total_earned']:.2f}\n")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

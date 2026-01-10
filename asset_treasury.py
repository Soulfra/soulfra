#!/usr/bin/env python3
"""
Asset Treasury - USDT/USDC Model but Backed by Real Assets

Instead of T-Bills, treasury holds:
- Commercial property (rental income)
- Premium domains (traffic revenue, sales)
- Metaverse land (Sandbox, Decentraland - appreciation + rentals)
- Crypto positions (staking yields)

Treasury Model:
1. Medallion stakes → Pool capital
2. Buy real assets with capital
3. Assets generate yield (rent, traffic, staking)
4. Yield distributed to medallion holders via payouts
5. Asset appreciation = increased treasury value = higher medallion prices

Usage:
    # Add asset to treasury
    python3 asset_treasury.py add-asset --type property --name "123 Main St Office" --price 500000 --yield 2500

    # Calculate treasury value
    python3 asset_treasury.py treasury-value

    # Distribute yield to medallion holders
    python3 asset_treasury.py distribute-yield

    # Buy asset with pooled stakes
    python3 asset_treasury.py buy-asset --type domain --name "ai-news.com" --price 10000
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import get_db


class AssetTreasury:
    """USDT/USDC-style treasury backed by real assets instead of T-Bills"""

    # Asset allocation targets (%)
    TARGET_PROPERTY = 40
    TARGET_DOMAINS = 30
    TARGET_METAVERSE = 20
    TARGET_CRYPTO = 10

    def __init__(self):
        self.db = get_db()

    def add_asset(
        self,
        asset_type: str,
        asset_name: str,
        purchase_price: float,
        monthly_yield: float = 0.0,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Add asset to treasury

        Args:
            asset_type: property, domain, metaverse_land, crypto
            asset_name: Asset identifier (address, domain name, plot ID, ticker)
            purchase_price: Purchase price in USD
            monthly_yield: Monthly income (rent, traffic revenue, staking yield)
            notes: Additional details

        Returns:
            Asset info dict
        """
        cursor = self.db.execute('''
            INSERT INTO asset_treasury
            (asset_type, asset_name, purchase_price, current_value, monthly_yield, purchase_date, notes)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (asset_type, asset_name, purchase_price, purchase_price, monthly_yield, notes))

        asset_id = cursor.lastrowid
        self.db.commit()

        return {
            'success': True,
            'asset_id': asset_id,
            'asset_type': asset_type,
            'asset_name': asset_name,
            'purchase_price': purchase_price,
            'monthly_yield': monthly_yield
        }

    def update_asset_value(self, asset_id: int, new_value: float) -> Dict:
        """
        Update asset valuation (mark-to-market)

        Args:
            asset_id: Asset to update
            new_value: Current market value

        Returns:
            Updated asset info
        """
        asset = self.db.execute('''
            SELECT * FROM asset_treasury WHERE id = ?
        ''', (asset_id,)).fetchone()

        if not asset:
            return {'success': False, 'error': 'Asset not found'}

        appreciation = new_value - asset['purchase_price']
        appreciation_pct = (appreciation / asset['purchase_price']) * 100

        self.db.execute('''
            UPDATE asset_treasury
            SET current_value = ?,
                last_valuation = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_value, asset_id))

        self.db.commit()

        return {
            'success': True,
            'asset_id': asset_id,
            'asset_name': asset['asset_name'],
            'purchase_price': asset['purchase_price'],
            'current_value': new_value,
            'appreciation': appreciation,
            'appreciation_pct': round(appreciation_pct, 2)
        }

    def calculate_treasury_value(self) -> Dict:
        """
        Calculate total treasury value and breakdown

        Returns:
            Treasury valuation dict
        """
        # Total value by asset type
        breakdown = self.db.execute('''
            SELECT
                asset_type,
                COUNT(*) as count,
                SUM(purchase_price) as total_cost,
                SUM(current_value) as total_value,
                SUM(monthly_yield) as total_monthly_yield
            FROM asset_treasury
            GROUP BY asset_type
        ''').fetchall()

        # Overall totals
        totals = self.db.execute('''
            SELECT
                COUNT(*) as total_assets,
                SUM(purchase_price) as total_cost,
                SUM(current_value) as total_value,
                SUM(monthly_yield) as total_monthly_yield
            FROM asset_treasury
        ''').fetchone()

        treasury = {
            'total_assets': totals['total_assets'],
            'total_cost': totals['total_cost'],
            'total_value': totals['total_value'],
            'total_appreciation': totals['total_value'] - totals['total_cost'],
            'total_monthly_yield': totals['total_monthly_yield'],
            'annual_yield': totals['total_monthly_yield'] * 12,
            'yield_percentage': round((totals['total_monthly_yield'] * 12 / totals['total_value']) * 100, 2) if totals['total_value'] else 0,
            'breakdown': {}
        }

        for asset in breakdown:
            treasury['breakdown'][asset['asset_type']] = {
                'count': asset['count'],
                'total_cost': asset['total_cost'],
                'total_value': asset['total_value'],
                'monthly_yield': asset['total_monthly_yield'],
                'percentage_of_treasury': round((asset['total_value'] / totals['total_value']) * 100, 2) if totals['total_value'] else 0
            }

        return treasury

    def distribute_monthly_yield(self) -> Dict:
        """
        Distribute monthly treasury yield to medallion holders

        Yield distribution based on medallion type:
        - Founding members: 2x weight
        - Standard: 1x weight
        - Earned: 0.5x weight

        Returns:
            Distribution results
        """
        from reactor_payouts import ReactorPayoutSystem

        # Calculate total monthly yield
        treasury = self.calculate_treasury_value()
        total_yield = treasury['total_monthly_yield']

        if total_yield <= 0:
            return {'success': False, 'error': 'No yield to distribute'}

        # Get all active medallion holders
        medallions = self.db.execute('''
            SELECT
                owner_user_id,
                medallion_type,
                CASE
                    WHEN medallion_type = 'founding_member' THEN 2.0
                    WHEN medallion_type = 'standard' THEN 1.0
                    WHEN medallion_type = 'earned' THEN 0.5
                END as weight
            FROM reactor_medallions
            WHERE is_active = 1
              AND revoked_at IS NULL
        ''').fetchall()

        if not medallions:
            return {'success': False, 'error': 'No active medallions'}

        # Calculate total weight
        total_weight = sum(m['weight'] for m in medallions)

        # Distribute yield proportionally
        payout_system = ReactorPayoutSystem()
        distributions = []

        for medallion in medallions:
            share = (medallion['weight'] / total_weight) * total_yield

            # Record payout
            self.db.execute('''
                INSERT INTO payout_history
                (user_id, amount, payout_type, reactor_weight, notes)
                VALUES (?, ?, 'treasury_yield', ?, 'Monthly treasury yield distribution')
            ''', (medallion['owner_user_id'], share, medallion['weight']))

            # Update medallion total earned
            self.db.execute('''
                UPDATE reactor_medallions
                SET total_earned = total_earned + ?
                WHERE owner_user_id = ?
                  AND medallion_type = ?
            ''', (share, medallion['owner_user_id'], medallion['medal lion_type']))

            distributions.append({
                'user_id': medallion['owner_user_id'],
                'medallion_type': medallion['medallion_type'],
                'weight': medallion['weight'],
                'share': round(share, 2)
            })

        self.db.commit()

        return {
            'success': True,
            'total_yield_distributed': total_yield,
            'recipient_count': len(distributions),
            'distributions': distributions
        }

    def get_asset_allocation(self) -> Dict:
        """
        Get current asset allocation vs targets

        Returns:
            Allocation breakdown
        """
        treasury = self.calculate_treasury_value()
        total_value = treasury['total_value']

        allocation = {}

        for asset_type in ['property', 'domain', 'metaverse_land', 'crypto']:
            current_value = treasury['breakdown'].get(asset_type, {}).get('total_value', 0)
            current_pct = (current_value / total_value * 100) if total_value else 0

            if asset_type == 'property':
                target_pct = self.TARGET_PROPERTY
            elif asset_type == 'domain':
                target_pct = self.TARGET_DOMAINS
            elif asset_type == 'metaverse_land':
                target_pct = self.TARGET_METAVERSE
            else:
                target_pct = self.TARGET_CRYPTO

            allocation[asset_type] = {
                'current_value': current_value,
                'current_percentage': round(current_pct, 2),
                'target_percentage': target_pct,
                'delta': round(current_pct - target_pct, 2),
                'needed_to_rebalance': round((target_pct / 100 * total_value) - current_value, 2)
            }

        return allocation

    def get_available_capital(self) -> float:
        """
        Calculate available capital from medallion stakes

        Returns:
            USD available for asset purchases
        """
        # Sum of all stakes not yet used for medallions or withdrawals
        available = self.db.execute('''
            SELECT SUM(amount) as total
            FROM medallion_stakes
            WHERE medallion_id IS NULL
              AND withdrawn_at IS NULL
        ''').fetchone()

        return available['total'] if available and available['total'] else 0.0

    def suggest_asset_purchases(self, budget: Optional[float] = None) -> List[Dict]:
        """
        Suggest asset purchases to rebalance treasury

        Args:
            budget: Available capital (None = use available stakes)

        Returns:
            List of suggested purchases
        """
        if budget is None:
            budget = self.get_available_capital()

        allocation = self.get_asset_allocation()

        # Sort by delta (most underweight first)
        sorted_types = sorted(
            allocation.items(),
            key=lambda x: x[1]['delta'],
            reverse=False  # Most negative (underweight) first
        )

        suggestions = []

        for asset_type, data in sorted_types:
            if data['delta'] < 0 and data['needed_to_rebalance'] > 0:
                # Calculate suggested purchase amount
                purchase_amount = min(budget, data['needed_to_rebalance'])

                if purchase_amount > 100:  # Minimum $100 purchase
                    suggestions.append({
                        'asset_type': asset_type,
                        'suggested_amount': round(purchase_amount, 2),
                        'current_percentage': data['current_percentage'],
                        'target_percentage': data['target_percentage'],
                        'underweight_by': abs(data['delta'])
                    })

                    budget -= purchase_amount

        return suggestions


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Asset Treasury Management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add asset
    add_parser = subparsers.add_parser('add-asset', help='Add asset to treasury')
    add_parser.add_argument('--type', required=True, choices=['property', 'domain', 'metaverse_land', 'crypto'])
    add_parser.add_argument('--name', required=True, help='Asset identifier')
    add_parser.add_argument('--price', type=float, required=True)
    add_parser.add_argument('--yield', type=float, default=0.0, help='Monthly yield (USD)')
    add_parser.add_argument('--notes', help='Additional notes')

    # Update value
    update_parser = subparsers.add_parser('update-value', help='Update asset valuation')
    update_parser.add_argument('--asset-id', type=int, required=True)
    update_parser.add_argument('--value', type=float, required=True)

    # Treasury value
    value_parser = subparsers.add_parser('treasury-value', help='Calculate treasury value')

    # Distribute yield
    distribute_parser = subparsers.add_parser('distribute-yield', help='Distribute monthly yield')

    # Asset allocation
    allocation_parser = subparsers.add_parser('allocation', help='Show asset allocation')

    # Suggest purchases
    suggest_parser = subparsers.add_parser('suggest-purchases', help='Suggest asset purchases')
    suggest_parser.add_argument('--budget', type=float, help='Available budget (default: use stakes)')

    args = parser.parse_args()

    treasury = AssetTreasury()

    if args.command == 'add-asset':
        result = treasury.add_asset(
            args.type,
            args.name,
            args.price,
            args.yield if hasattr(args, 'yield') else 0.0,
            args.notes
        )
        if result['success']:
            print(f"\n✅ Added {result['asset_type']} to treasury")
            print(f"   Name: {result['asset_name']}")
            print(f"   Price: ${result['purchase_price']:,.2f}")
            print(f"   Monthly Yield: ${result['monthly_yield']:,.2f}\n")

    elif args.command == 'update-value':
        result = treasury.update_asset_value(args.asset_id, args.value)
        if result['success']:
            print(f"\n📈 Updated {result['asset_name']} valuation")
            print(f"   Purchase Price: ${result['purchase_price']:,.2f}")
            print(f"   Current Value: ${result['current_value']:,.2f}")
            print(f"   Appreciation: ${result['appreciation']:,.2f} ({result['appreciation_pct']}%)\n")

    elif args.command == 'treasury-value':
        value = treasury.calculate_treasury_value()
        print(f"\n💎 Treasury Valuation\n")
        print(f"Total Assets: {value['total_assets']}")
        print(f"Total Cost: ${value['total_cost']:,.2f}")
        print(f"Total Value: ${value['total_value']:,.2f}")
        print(f"Appreciation: ${value['total_appreciation']:,.2f}")
        print(f"Monthly Yield: ${value['total_monthly_yield']:,.2f}")
        print(f"Annual Yield: ${value['annual_yield']:,.2f} ({value['yield_percentage']}%)\n")

        print("Breakdown by Asset Type:\n")
        for asset_type, data in value['breakdown'].items():
            print(f"{asset_type.upper()}: ${data['total_value']:,.2f} ({data['percentage_of_treasury']}%)")
            print(f"  Count: {data['count']} | Monthly Yield: ${data['monthly_yield']:,.2f}\n")

    elif args.command == 'distribute-yield':
        result = treasury.distribute_monthly_yield()
        if result['success']:
            print(f"\n💰 Distributed ${result['total_yield_distributed']:,.2f} to {result['recipient_count']} medallion holders\n")
            for dist in result['distributions'][:10]:
                print(f"User #{dist['user_id']} ({dist['medallion_type']}): ${dist['share']:,.2f}")
        else:
            print(f"\n❌ Error: {result['error']}\n")

    elif args.command == 'allocation':
        allocation = treasury.get_asset_allocation()
        print(f"\n📊 Asset Allocation\n")
        for asset_type, data in allocation.items():
            status = "✅" if abs(data['delta']) < 5 else "⚠️"
            print(f"{status} {asset_type.upper()}: {data['current_percentage']:.1f}% (target: {data['target_percentage']}%)")
            print(f"   Value: ${data['current_value']:,.2f} | Rebalance: ${data['needed_to_rebalance']:,.2f}\n")

    elif args.command == 'suggest-purchases':
        suggestions = treasury.suggest_asset_purchases(args.budget if hasattr(args, 'budget') else None)
        available = treasury.get_available_capital()

        print(f"\n💡 Suggested Asset Purchases (Available Capital: ${available:,.2f})\n")
        for suggestion in suggestions:
            print(f"Buy {suggestion['asset_type']}: ${suggestion['suggested_amount']:,.2f}")
            print(f"   Current: {suggestion['current_percentage']:.1f}% | Target: {suggestion['target_percentage']}% | Underweight by: {suggestion['underweight_by']:.1f}%\n")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

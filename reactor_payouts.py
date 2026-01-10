#!/usr/bin/env python3
"""
Reactor Payout System - ElevenLabs-style payouts for voice reactions

Like USDT/USDC but backed by REAL ASSETS instead of T-Bills:
- Commercial property rental income
- Metaverse land (Sandbox, Decentraland)
- Premium domains
- Other digital/physical assets

Treasury generates yield → Distributed to reactors based on performance weights

Flow:
1. Reactors submit voice reactions to news articles
2. System calculates performance weights (accuracy, engagement, consistency)
3. Sponsor revenue + treasury yield → Split based on weights
4. Top performers earn more, crash-and-burn reactors earn less
5. Open source - others can fork and run their own treasury

Usage:
    # Calculate reactor weights
    python3 reactor_payouts.py calculate-weights

    # Distribute payouts
    python3 reactor_payouts.py distribute --total-revenue 1000.00

    # Show leaderboard
    python3 reactor_payouts.py leaderboard

    # Export crash-and-burn report
    python3 reactor_payouts.py crash-burn-report
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import get_db


class ReactorPayoutSystem:
    """Calculate performance weights and distribute payouts to voice reactors"""

    def __init__(self):
        self.db = get_db()
        self._ensure_tables()

    def _ensure_tables(self):
        """Create tables for reactor weights and payouts"""

        # Reactor performance weights
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS reactor_weights (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                accuracy_score REAL DEFAULT 0.0,      -- Prediction accuracy (0-100)
                engagement_score REAL DEFAULT 0.0,    -- Views/listens (0-100)
                sponsor_score REAL DEFAULT 0.0,       -- Sponsor keyword matching (0-100)
                consistency_score REAL DEFAULT 0.0,   -- Activity frequency (0-100)
                total_weight REAL DEFAULT 0.0,        -- Weighted average (0-100)
                total_earned REAL DEFAULT 0.0,        -- Lifetime earnings (USD)
                crash_burn_count INTEGER DEFAULT 0,   -- Failed predictions
                accurate_count INTEGER DEFAULT 0,     -- Successful predictions
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Payout history
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS payout_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                amount REAL NOT NULL,
                payout_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payout_type TEXT,  -- sponsor, treasury_yield, bonus
                reactor_weight REAL,
                notes TEXT
            )
        ''')

        # Asset treasury (backing for payouts)
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS asset_treasury (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_type TEXT NOT NULL,  -- property, domain, metaverse_land, crypto
                asset_name TEXT NOT NULL,
                purchase_price REAL,
                current_value REAL,
                monthly_yield REAL,
                purchase_date TIMESTAMP,
                last_valuation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')

        # Revenue pools
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS revenue_pools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_date DATE UNIQUE,
                sponsor_revenue REAL DEFAULT 0.0,
                treasury_yield REAL DEFAULT 0.0,
                total_distributed REAL DEFAULT 0.0,
                distribution_date TIMESTAMP
            )
        ''')

        self.db.commit()

    def calculate_accuracy_score(self, user_id: int) -> float:
        """
        Calculate prediction accuracy score

        Checks voice_article_pairings where time-lock expired:
        - Compare user prediction vs actual outcome
        - Use Ollama to analyze if prediction was accurate

        Returns:
            Score from 0-100 (100 = perfect predictions)
        """
        # Get all time-unlocked pairings for user
        pairings = self.db.execute('''
            SELECT
                vap.user_prediction,
                vap.cringe_factor,
                na.cringe_score,
                na.relevance_score
            FROM voice_article_pairings vap
            JOIN news_articles na ON vap.article_id = na.id
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE svr.user_id = ?
              AND vap.time_lock_until < datetime('now')
              AND vap.published_to_archive = 1
        ''', (user_id,)).fetchall()

        if not pairings:
            return 50.0  # Neutral score for new users

        # Simple scoring: inverse of average cringe_score
        # Lower cringe = better predictions
        avg_cringe = sum(p['cringe_score'] or 50 for p in pairings) / len(pairings)
        accuracy_score = 100 - avg_cringe

        return max(0, min(100, accuracy_score))

    def calculate_engagement_score(self, user_id: int) -> float:
        """
        Calculate engagement score based on views/reactions to user's content

        For now, uses reaction count as proxy for engagement
        Later: Track actual views via raw GitHub URL analytics

        Returns:
            Score from 0-100
        """
        # Count total reactions by this user
        reactions = self.db.execute('''
            SELECT COUNT(*) as count
            FROM voice_article_pairings vap
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE svr.user_id = ?
              AND vap.published_to_archive = 1
        ''', (user_id,)).fetchone()

        reaction_count = reactions['count'] if reactions else 0

        # Simple formula: log scale (1-10 reactions = 10-50, 11+ = 50-100)
        if reaction_count == 0:
            return 0
        elif reaction_count <= 10:
            return reaction_count * 5  # 1 = 5, 10 = 50
        else:
            return min(100, 50 + (reaction_count - 10) * 2)  # 11 = 52, 25 = 80, 35+ = 100

    def calculate_sponsor_score(self, user_id: int) -> float:
        """
        Calculate sponsor relevance score

        Measures how well user's reactions match sponsor keywords
        Better matching = more valuable to sponsors = higher score

        Returns:
            Score from 0-100
        """
        # Get reactions with sponsor pairings
        matched = self.db.execute('''
            SELECT COUNT(*) as count
            FROM voice_article_pairings vap
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE svr.user_id = ?
              AND vap.live_show_id IS NOT NULL
        ''', (user_id,)).fetchone()

        total = self.db.execute('''
            SELECT COUNT(*) as count
            FROM voice_article_pairings vap
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE svr.user_id = ?
        ''', (user_id,)).fetchone()

        if total['count'] == 0:
            return 50.0  # Neutral for new users

        # Percentage of reactions that got matched with sponsors
        match_rate = (matched['count'] / total['count']) * 100

        return match_rate

    def calculate_consistency_score(self, user_id: int, days_lookback: int = 30) -> float:
        """
        Calculate consistency score based on activity frequency

        Rewards regular contributors over one-hit wonders

        Returns:
            Score from 0-100
        """
        cutoff_date = (datetime.now() - timedelta(days=days_lookback)).isoformat()

        recent_reactions = self.db.execute('''
            SELECT COUNT(*) as count
            FROM voice_article_pairings vap
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE svr.user_id = ?
              AND vap.paired_at >= ?
        ''', (user_id, cutoff_date)).fetchone()

        reaction_count = recent_reactions['count'] if recent_reactions else 0

        # Score based on frequency:
        # 0 reactions = 0
        # 1-4 reactions/month = 25
        # 5-9 = 50
        # 10-19 = 75
        # 20+ = 100
        if reaction_count == 0:
            return 0
        elif reaction_count <= 4:
            return 25
        elif reaction_count <= 9:
            return 50
        elif reaction_count <= 19:
            return 75
        else:
            return 100

    def calculate_total_weight(
        self,
        accuracy: float,
        engagement: float,
        sponsor: float,
        consistency: float
    ) -> float:
        """
        Calculate weighted average of all scores

        Weights:
        - Accuracy: 40% (most important - were they right?)
        - Engagement: 30% (do people listen to them?)
        - Sponsor relevance: 20% (are they valuable to sponsors?)
        - Consistency: 10% (are they active?)
        """
        total_weight = (
            accuracy * 0.40 +
            engagement * 0.30 +
            sponsor * 0.20 +
            consistency * 0.10
        )

        return round(total_weight, 2)

    def update_reactor_weights(self, user_id: int) -> Dict:
        """
        Recalculate and update all weights for a reactor

        Returns:
            Updated weight data
        """
        # Calculate individual scores
        accuracy = self.calculate_accuracy_score(user_id)
        engagement = self.calculate_engagement_score(user_id)
        sponsor = self.calculate_sponsor_score(user_id)
        consistency = self.calculate_consistency_score(user_id)

        # Calculate total weight
        total_weight = self.calculate_total_weight(accuracy, engagement, sponsor, consistency)

        # Count crash-and-burn vs accurate predictions
        stats = self.db.execute('''
            SELECT
                COUNT(CASE WHEN na.cringe_score > 70 THEN 1 END) as crash_burn,
                COUNT(CASE WHEN na.cringe_score < 30 THEN 1 END) as accurate
            FROM voice_article_pairings vap
            JOIN news_articles na ON vap.article_id = na.id
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE svr.user_id = ?
              AND vap.time_lock_until < datetime('now')
        ''', (user_id,)).fetchone()

        crash_burn_count = stats['crash_burn'] if stats else 0
        accurate_count = stats['accurate'] if stats else 0

        # Upsert reactor weights
        self.db.execute('''
            INSERT INTO reactor_weights
            (user_id, accuracy_score, engagement_score, sponsor_score,
             consistency_score, total_weight, crash_burn_count, accurate_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                accuracy_score = excluded.accuracy_score,
                engagement_score = excluded.engagement_score,
                sponsor_score = excluded.sponsor_score,
                consistency_score = excluded.consistency_score,
                total_weight = excluded.total_weight,
                crash_burn_count = excluded.crash_burn_count,
                accurate_count = excluded.accurate_count,
                last_updated = CURRENT_TIMESTAMP
        ''', (user_id, accuracy, engagement, sponsor, consistency, total_weight,
              crash_burn_count, accurate_count))

        self.db.commit()

        return {
            'user_id': user_id,
            'accuracy_score': accuracy,
            'engagement_score': engagement,
            'sponsor_score': sponsor,
            'consistency_score': consistency,
            'total_weight': total_weight,
            'crash_burn_count': crash_burn_count,
            'accurate_count': accurate_count
        }

    def calculate_all_weights(self) -> List[Dict]:
        """Calculate weights for all reactors"""
        users = self.db.execute('''
            SELECT DISTINCT user_id
            FROM simple_voice_recordings
            WHERE user_id IS NOT NULL
        ''').fetchall()

        results = []
        for user in users:
            weights = self.update_reactor_weights(user['user_id'])
            results.append(weights)

        return results

    def distribute_payouts(self, total_revenue: float, payout_type: str = 'sponsor') -> List[Dict]:
        """
        Distribute revenue to reactors based on weights

        Args:
            total_revenue: Total amount to distribute (USD)
            payout_type: sponsor, treasury_yield, bonus

        Returns:
            List of payout records
        """
        # Get all reactor weights
        reactors = self.db.execute('''
            SELECT user_id, total_weight
            FROM reactor_weights
            WHERE total_weight > 0
            ORDER BY total_weight DESC
        ''').fetchall()

        if not reactors:
            return []

        # Calculate total weight pool
        total_weight_sum = sum(r['total_weight'] for r in reactors)

        payouts = []

        for reactor in reactors:
            # Proportional share based on weight
            weight_ratio = reactor['total_weight'] / total_weight_sum
            payout_amount = total_revenue * weight_ratio

            # Record payout
            self.db.execute('''
                INSERT INTO payout_history
                (user_id, amount, payout_type, reactor_weight)
                VALUES (?, ?, ?, ?)
            ''', (reactor['user_id'], payout_amount, payout_type, reactor['total_weight']))

            # Update total earned
            self.db.execute('''
                UPDATE reactor_weights
                SET total_earned = total_earned + ?
                WHERE user_id = ?
            ''', (payout_amount, reactor['user_id']))

            payouts.append({
                'user_id': reactor['user_id'],
                'amount': round(payout_amount, 2),
                'weight': reactor['total_weight'],
                'share_percentage': round(weight_ratio * 100, 2)
            })

        self.db.commit()

        return payouts

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top reactors by total weight"""
        return [dict(r) for r in self.db.execute('''
            SELECT
                rw.*,
                u.username
            FROM reactor_weights rw
            JOIN users u ON rw.user_id = u.id
            ORDER BY rw.total_weight DESC
            LIMIT ?
        ''', (limit,)).fetchall()]

    def get_crash_burn_report(self) -> List[Dict]:
        """Get reactors with most failed predictions"""
        return [dict(r) for r in self.db.execute('''
            SELECT
                rw.user_id,
                u.username,
                rw.crash_burn_count,
                rw.accurate_count,
                rw.accuracy_score,
                CASE
                    WHEN (rw.crash_burn_count + rw.accurate_count) > 0
                    THEN ROUND(rw.crash_burn_count * 100.0 / (rw.crash_burn_count + rw.accurate_count), 2)
                    ELSE 0
                END as crash_burn_percentage
            FROM reactor_weights rw
            JOIN users u ON rw.user_id = u.id
            ORDER BY crash_burn_percentage DESC
        ''').fetchall()]


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Reactor Payout System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Calculate weights
    weights_parser = subparsers.add_parser('calculate-weights', help='Calculate reactor weights')

    # Distribute payouts
    distribute_parser = subparsers.add_parser('distribute', help='Distribute payouts')
    distribute_parser.add_argument('--total-revenue', type=float, required=True)
    distribute_parser.add_argument('--type', default='sponsor', choices=['sponsor', 'treasury_yield', 'bonus'])

    # Leaderboard
    leaderboard_parser = subparsers.add_parser('leaderboard', help='Show top reactors')
    leaderboard_parser.add_argument('--limit', type=int, default=10)

    # Crash & burn report
    crash_parser = subparsers.add_parser('crash-burn-report', help='Show failed predictions')

    args = parser.parse_args()

    payout_system = ReactorPayoutSystem()

    if args.command == 'calculate-weights':
        results = payout_system.calculate_all_weights()
        print(f"\n✅ Calculated weights for {len(results)} reactors\n")
        for r in results[:5]:
            print(f"User #{r['user_id']}: Weight {r['total_weight']:.2f} (Accuracy: {r['accuracy_score']:.1f}, Engagement: {r['engagement_score']:.1f})")

    elif args.command == 'distribute':
        payouts = payout_system.distribute_payouts(args.total_revenue, args.type)
        print(f"\n💰 Distributed ${args.total_revenue:.2f} to {len(payouts)} reactors\n")
        for p in payouts:
            print(f"User #{p['user_id']}: ${p['amount']:.2f} ({p['share_percentage']:.2f}% share, weight: {p['weight']:.2f})")

    elif args.command == 'leaderboard':
        leaders = payout_system.get_leaderboard(args.limit)
        print(f"\n🏆 Top {args.limit} Reactors\n")
        for i, leader in enumerate(leaders, 1):
            print(f"{i}. {leader['username']} - Weight: {leader['total_weight']:.2f} | Earned: ${leader['total_earned']:.2f}")
            print(f"   Accuracy: {leader['accuracy_score']:.1f} | Engagement: {leader['engagement_score']:.1f} | Predictions: {leader['accurate_count']} ✅ / {leader['crash_burn_count']} ❌\n")

    elif args.command == 'crash-burn-report':
        report = payout_system.get_crash_burn_report()
        print(f"\n🔥 Crash & Burn Report\n")
        for r in report:
            print(f"{r['username']} - {r['crash_burn_percentage']:.1f}% crash rate ({r['crash_burn_count']} fails / {r['accurate_count']} accurate)")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

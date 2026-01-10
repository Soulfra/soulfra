#!/usr/bin/env python3
"""
Story Betting Market - Bet on AI Prediction Accuracy

Integrates with:
- story_predictor.py for AI predictions
- reverse_wpm.py for storyteller reputation
- VIBE token economy (from soulfra.github.io/misc/VIBE_TOKEN_ECONOMY.py)

Bet Types:
- "AI Correct": Bet that AI will predict correctly (< 30% unpredictability)
- "AI Wrong": Bet that storyteller will surprise AI (>= 70% unpredictability)
- "Plot Twist": Bet on specific surprise elements
- "Streak Breaker": Bet that current streak will break
- "Genre Switch": Bet that story will switch genres
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
from decimal import Decimal


DATABASE_PATH = Path(__file__).parent / 'soulfra.db'


class StoryBettingMarket:
    """
    Betting market for story predictions

    Based on betting-shell.js from soulfra.github.io/misc/
    """

    def __init__(self):
        self.db = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.init_tables()

        # Betting configuration
        self.config = {
            'min_bet': 10,  # 10 VIBE minimum bet
            'max_bet': 1000,  # 1000 VIBE maximum bet
            'platform_fee': 0.025,  # 2.5% platform fee
            'odds_update_threshold': 100,  # Update odds every 100 VIBE bet

            # Odds calculation
            'ai_correct_base_odds': 1.5,  # Base odds for AI being correct
            'ai_wrong_base_odds': 2.5,  # Base odds for AI being wrong
            'plot_twist_odds': 3.5,  # Odds for plot twist
            'streak_break_odds': 2.0,  # Odds for streak breaking

            # Special multipliers
            'confidence_multiplier': 1.2,  # Higher AI confidence = lower payout
            'reputation_multiplier': 1.3,  # Higher storyteller reputation = higher payout for surprise
        }

    def init_tables(self):
        """Create betting market tables"""
        cursor = self.db.cursor()

        # Active betting pools
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_bet_pools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                segment_number INTEGER NOT NULL,
                ai_confidence REAL,
                storyteller_reputation REAL,

                -- Pool stats
                total_bets_ai_correct INTEGER DEFAULT 0,
                total_bets_ai_wrong INTEGER DEFAULT 0,
                total_vibe_ai_correct INTEGER DEFAULT 0,
                total_vibe_ai_wrong INTEGER DEFAULT 0,

                -- Current odds
                odds_ai_correct REAL,
                odds_ai_wrong REAL,

                -- Status
                status TEXT DEFAULT 'open',  -- open, closed, resolved
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME,
                resolved_at DATETIME,

                -- Result
                actual_unpredictability REAL,
                winning_side TEXT,  -- 'ai_correct', 'ai_wrong', 'push'

                FOREIGN KEY (session_id) REFERENCES story_sessions(id),
                UNIQUE(session_id, segment_number)
            )
        ''')

        # Individual bets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                bet_type TEXT NOT NULL,  -- 'ai_correct', 'ai_wrong', 'plot_twist', etc.
                amount INTEGER NOT NULL,
                odds REAL NOT NULL,
                potential_payout INTEGER,

                -- Result
                status TEXT DEFAULT 'pending',  -- pending, won, lost, refunded
                actual_payout INTEGER DEFAULT 0,

                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (pool_id) REFERENCES story_bet_pools(id)
            )
        ''')

        # Special bets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_special_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id INTEGER NOT NULL,
                bet_type TEXT NOT NULL,  -- 'plot_twist', 'streak_break', 'genre_switch'
                description TEXT,
                odds REAL NOT NULL,
                total_bets INTEGER DEFAULT 0,
                total_vibe INTEGER DEFAULT 0,
                status TEXT DEFAULT 'open',

                FOREIGN KEY (pool_id) REFERENCES story_bet_pools(id)
            )
        ''')

        # Player VIBE balances (simple version - full economy in VIBE_TOKEN_ECONOMY.py)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vibe_balances (
                player_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 1000,  -- Start with 1000 VIBE
                total_wagered INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                total_lost INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_bet DATETIME
            )
        ''')

        # Betting history for analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS betting_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_pool_size INTEGER,
                odds_ai_correct REAL,
                odds_ai_wrong REAL,
                bet_ratio REAL,  -- ai_correct / ai_wrong

                FOREIGN KEY (pool_id) REFERENCES story_bet_pools(id)
            )
        ''')

        self.db.commit()
        print("✅ Story betting market tables initialized")

    def create_betting_pool(
        self,
        session_id: int,
        segment_number: int,
        ai_confidence: float,
        storyteller_reputation: float
    ) -> int:
        """
        Create a new betting pool for a story segment

        Args:
            session_id: Active story session
            segment_number: Segment number (1, 2, 3...)
            ai_confidence: AI's confidence in prediction (0-1)
            storyteller_reputation: Storyteller's reverse WPM score

        Returns:
            pool_id
        """
        cursor = self.db.cursor()

        # Calculate initial odds
        odds_ai_correct = self._calculate_odds(
            base_odds=self.config['ai_correct_base_odds'],
            ai_confidence=ai_confidence,
            storyteller_reputation=storyteller_reputation,
            favor_ai=True
        )

        odds_ai_wrong = self._calculate_odds(
            base_odds=self.config['ai_wrong_base_odds'],
            ai_confidence=ai_confidence,
            storyteller_reputation=storyteller_reputation,
            favor_ai=False
        )

        # Create pool
        cursor.execute('''
            INSERT INTO story_bet_pools (
                session_id, segment_number, ai_confidence, storyteller_reputation,
                odds_ai_correct, odds_ai_wrong
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, segment_number, ai_confidence, storyteller_reputation,
              odds_ai_correct, odds_ai_wrong))

        pool_id = cursor.lastrowid

        # Create special bet options
        self._create_special_bets(pool_id)

        self.db.commit()

        print(f"🎲 Created betting pool #{pool_id} for session {session_id}, segment {segment_number}")
        print(f"   Odds - AI Correct: {odds_ai_correct:.2f}x | AI Wrong: {odds_ai_wrong:.2f}x")

        return pool_id

    def _calculate_odds(
        self,
        base_odds: float,
        ai_confidence: float,
        storyteller_reputation: float,
        favor_ai: bool
    ) -> float:
        """
        Calculate odds based on AI confidence and storyteller reputation

        Args:
            base_odds: Starting odds
            ai_confidence: 0-1 how confident AI is
            storyteller_reputation: Storyteller's reverse WPM
            favor_ai: True = adjust for AI being correct, False = for AI being wrong

        Returns:
            Calculated odds
        """
        if favor_ai:
            # High AI confidence = lower payout for betting on AI
            confidence_factor = 1.0 - (ai_confidence * 0.3)
            # High storyteller reputation = even lower payout (more likely to surprise)
            reputation_factor = 1.0 - min(storyteller_reputation / 20.0, 0.3)
        else:
            # High AI confidence = higher payout for betting against AI
            confidence_factor = 1.0 + (ai_confidence * 0.3)
            # High storyteller reputation = lower payout (more likely to surprise anyway)
            reputation_factor = 1.0 + min(storyteller_reputation / 20.0, 0.5)

        odds = base_odds * confidence_factor * reputation_factor
        return max(round(odds, 2), 1.05)  # Minimum 1.05x odds

    def _create_special_bets(self, pool_id: int):
        """Create special betting options for a pool"""
        cursor = self.db.cursor()

        special_bets = [
            ('plot_twist', 'Story takes unexpected turn', self.config['plot_twist_odds']),
            ('streak_break', 'Storyteller\'s streak will break', self.config['streak_break_odds']),
            ('dialogue_heavy', 'Next segment will be >50% dialogue', 2.2),
            ('character_intro', 'New character will be introduced', 2.8),
        ]

        for bet_type, description, odds in special_bets:
            cursor.execute('''
                INSERT INTO story_special_bets (pool_id, bet_type, description, odds)
                VALUES (?, ?, ?, ?)
            ''', (pool_id, bet_type, description, odds))

        self.db.commit()

    def place_bet(
        self,
        player_id: int,
        pool_id: int,
        bet_type: str,
        amount: int
    ) -> Dict:
        """
        Place a bet on a story prediction

        Args:
            player_id: Player ID
            pool_id: Betting pool ID
            bet_type: 'ai_correct', 'ai_wrong', or special bet type
            amount: VIBE amount to bet

        Returns:
            {
                'success': bool,
                'bet_id': int,
                'odds': float,
                'potential_payout': int,
                'new_balance': int
            }
        """
        cursor = self.db.cursor()

        # Validate bet amount
        if amount < self.config['min_bet']:
            return {'success': False, 'error': f"Minimum bet is {self.config['min_bet']} VIBE"}
        if amount > self.config['max_bet']:
            return {'success': False, 'error': f"Maximum bet is {self.config['max_bet']} VIBE"}

        # Check pool status
        cursor.execute('SELECT status, odds_ai_correct, odds_ai_wrong FROM story_bet_pools WHERE id = ?', (pool_id,))
        result = cursor.fetchone()
        if not result:
            return {'success': False, 'error': 'Pool not found'}

        status, odds_ai_correct, odds_ai_wrong = result
        if status != 'open':
            return {'success': False, 'error': 'Betting is closed'}

        # Get or create player balance
        cursor.execute('INSERT OR IGNORE INTO vibe_balances (player_id) VALUES (?)', (player_id,))
        cursor.execute('SELECT balance FROM vibe_balances WHERE player_id = ?', (player_id,))
        balance = cursor.fetchone()[0]

        if balance < amount:
            return {'success': False, 'error': f'Insufficient balance ({balance} VIBE)'}

        # Determine odds
        if bet_type == 'ai_correct':
            odds = odds_ai_correct
        elif bet_type == 'ai_wrong':
            odds = odds_ai_wrong
        else:
            # Special bet
            cursor.execute('SELECT odds FROM story_special_bets WHERE pool_id = ? AND bet_type = ?',
                          (pool_id, bet_type))
            special_bet = cursor.fetchone()
            if not special_bet:
                return {'success': False, 'error': 'Invalid bet type'}
            odds = special_bet[0]

        # Calculate potential payout (after platform fee)
        gross_payout = int(amount * odds)
        platform_fee = int(gross_payout * self.config['platform_fee'])
        potential_payout = gross_payout - platform_fee

        # Deduct balance
        cursor.execute('''
            UPDATE vibe_balances
            SET balance = balance - ?,
                total_wagered = total_wagered + ?,
                last_bet = CURRENT_TIMESTAMP
            WHERE player_id = ?
        ''', (amount, amount, player_id))

        # Place bet
        cursor.execute('''
            INSERT INTO story_bets (pool_id, player_id, bet_type, amount, odds, potential_payout)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (pool_id, player_id, bet_type, amount, odds, potential_payout))

        bet_id = cursor.lastrowid

        # Update pool stats
        if bet_type == 'ai_correct':
            cursor.execute('''
                UPDATE story_bet_pools
                SET total_bets_ai_correct = total_bets_ai_correct + 1,
                    total_vibe_ai_correct = total_vibe_ai_correct + ?
                WHERE id = ?
            ''', (amount, pool_id))
        elif bet_type == 'ai_wrong':
            cursor.execute('''
                UPDATE story_bet_pools
                SET total_bets_ai_wrong = total_bets_ai_wrong + 1,
                    total_vibe_ai_wrong = total_vibe_ai_wrong + ?
                WHERE id = ?
            ''', (amount, pool_id))
        else:
            # Special bet
            cursor.execute('''
                UPDATE story_special_bets
                SET total_bets = total_bets + 1,
                    total_vibe = total_vibe + ?
                WHERE pool_id = ? AND bet_type = ?
            ''', (amount, pool_id, bet_type))

        # Check if we should update odds
        total_vibe = cursor.execute('SELECT total_vibe_ai_correct + total_vibe_ai_wrong FROM story_bet_pools WHERE id = ?', (pool_id,)).fetchone()[0]
        if total_vibe % self.config['odds_update_threshold'] < amount:
            self._update_pool_odds(pool_id)

        self.db.commit()

        new_balance = balance - amount

        print(f"💰 Bet placed: Player {player_id} bet {amount} VIBE on '{bet_type}' @ {odds:.2f}x")
        print(f"   Potential payout: {potential_payout} VIBE")
        print(f"   New balance: {new_balance} VIBE")

        return {
            'success': True,
            'bet_id': bet_id,
            'odds': odds,
            'potential_payout': potential_payout,
            'new_balance': new_balance
        }

    def _update_pool_odds(self, pool_id: int):
        """Update odds based on betting volume (move odds toward underdogs)"""
        cursor = self.db.cursor()

        cursor.execute('''
            SELECT total_vibe_ai_correct, total_vibe_ai_wrong, odds_ai_correct, odds_ai_wrong
            FROM story_bet_pools
            WHERE id = ?
        ''', (pool_id,))

        ai_correct_vibe, ai_wrong_vibe, current_ai_correct_odds, current_ai_wrong_odds = cursor.fetchone()

        total_vibe = ai_correct_vibe + ai_wrong_vibe
        if total_vibe == 0:
            return

        # Calculate betting ratio
        ai_correct_ratio = ai_correct_vibe / total_vibe
        ai_wrong_ratio = ai_wrong_vibe / total_vibe

        # Adjust odds (popular side gets worse odds, underdog gets better odds)
        adjustment_factor = 0.1  # 10% max adjustment

        new_ai_correct_odds = current_ai_correct_odds * (1.0 + (0.5 - ai_correct_ratio) * adjustment_factor)
        new_ai_wrong_odds = current_ai_wrong_odds * (1.0 + (0.5 - ai_wrong_ratio) * adjustment_factor)

        # Ensure minimum odds
        new_ai_correct_odds = max(round(new_ai_correct_odds, 2), 1.05)
        new_ai_wrong_odds = max(round(new_ai_wrong_odds, 2), 1.05)

        cursor.execute('''
            UPDATE story_bet_pools
            SET odds_ai_correct = ?,
                odds_ai_wrong = ?
            WHERE id = ?
        ''', (new_ai_correct_odds, new_ai_wrong_odds, pool_id))

        # Log analytics
        cursor.execute('''
            INSERT INTO betting_analytics (pool_id, total_pool_size, odds_ai_correct, odds_ai_wrong, bet_ratio)
            VALUES (?, ?, ?, ?, ?)
        ''', (pool_id, total_vibe, new_ai_correct_odds, new_ai_wrong_odds, ai_correct_ratio / max(ai_wrong_ratio, 0.01)))

        self.db.commit()

        print(f"📊 Updated odds for pool #{pool_id}: AI Correct {new_ai_correct_odds:.2f}x | AI Wrong {new_ai_wrong_odds:.2f}x")

    def close_betting(self, pool_id: int):
        """Close betting before segment is revealed"""
        cursor = self.db.cursor()

        cursor.execute('''
            UPDATE story_bet_pools
            SET status = 'closed',
                closed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (pool_id,))

        cursor.execute('''
            UPDATE story_special_bets
            SET status = 'closed'
            WHERE pool_id = ?
        ''', (pool_id,))

        self.db.commit()

        print(f"🔒 Closed betting for pool #{pool_id}")

    def resolve_bets(
        self,
        pool_id: int,
        actual_unpredictability: float,
        special_results: Dict[str, bool] = None
    ) -> Dict:
        """
        Resolve bets after segment is revealed

        Args:
            pool_id: Betting pool ID
            actual_unpredictability: 0-1 unpredictability score
            special_results: Dict of {bet_type: won} for special bets

        Returns:
            {
                'total_paid_out': int,
                'winners_count': int,
                'losers_count': int
            }
        """
        cursor = self.db.cursor()

        # Determine winning side
        # AI is "correct" if unpredictability < 30%, "wrong" if >= 70%, "push" if in between
        if actual_unpredictability < 0.3:
            winning_side = 'ai_correct'
        elif actual_unpredictability >= 0.7:
            winning_side = 'ai_wrong'
        else:
            winning_side = 'push'

        # Update pool
        cursor.execute('''
            UPDATE story_bet_pools
            SET status = 'resolved',
                resolved_at = CURRENT_TIMESTAMP,
                actual_unpredictability = ?,
                winning_side = ?
            WHERE id = ?
        ''', (actual_unpredictability, winning_side, pool_id))

        # Get all bets
        cursor.execute('''
            SELECT id, player_id, bet_type, amount, potential_payout
            FROM story_bets
            WHERE pool_id = ?
        ''', (pool_id,))

        bets = cursor.fetchall()

        total_paid_out = 0
        winners_count = 0
        losers_count = 0

        for bet_id, player_id, bet_type, amount, potential_payout in bets:
            won = False
            payout = 0

            if winning_side == 'push':
                # Refund
                won = True
                payout = amount
                status = 'refunded'
            elif bet_type == winning_side:
                # Won!
                won = True
                payout = potential_payout
                status = 'won'
            elif bet_type in (special_results or {}):
                # Special bet
                if special_results[bet_type]:
                    won = True
                    payout = potential_payout
                    status = 'won'
                else:
                    status = 'lost'
            else:
                # Lost
                status = 'lost'

            # Update bet
            cursor.execute('''
                UPDATE story_bets
                SET status = ?,
                    actual_payout = ?
                WHERE id = ?
            ''', (status, payout, bet_id))

            # Update player balance
            if payout > 0:
                cursor.execute('''
                    UPDATE vibe_balances
                    SET balance = balance + ?,
                        total_won = total_won + ?
                    WHERE player_id = ?
                ''', (payout, payout - amount if won else amount, player_id))

                winners_count += 1
                total_paid_out += payout
            else:
                cursor.execute('''
                    UPDATE vibe_balances
                    SET total_lost = total_lost + ?
                    WHERE player_id = ?
                ''', (amount, player_id))

                losers_count += 1

        self.db.commit()

        print(f"\n💸 Resolved pool #{pool_id}: {winning_side.upper()}")
        print(f"   Total paid out: {total_paid_out} VIBE")
        print(f"   Winners: {winners_count} | Losers: {losers_count}")

        return {
            'total_paid_out': total_paid_out,
            'winners_count': winners_count,
            'losers_count': losers_count,
            'winning_side': winning_side
        }

    def get_pool_info(self, pool_id: int) -> Optional[Dict]:
        """Get betting pool information"""
        cursor = self.db.cursor()

        cursor.execute('''
            SELECT
                session_id, segment_number, ai_confidence, storyteller_reputation,
                total_bets_ai_correct, total_bets_ai_wrong,
                total_vibe_ai_correct, total_vibe_ai_wrong,
                odds_ai_correct, odds_ai_wrong, status
            FROM story_bet_pools
            WHERE id = ?
        ''', (pool_id,))

        result = cursor.fetchone()
        if not result:
            return None

        return {
            'pool_id': pool_id,
            'session_id': result[0],
            'segment_number': result[1],
            'ai_confidence': result[2],
            'storyteller_reputation': result[3],
            'total_bets_ai_correct': result[4],
            'total_bets_ai_wrong': result[5],
            'total_vibe_ai_correct': result[6],
            'total_vibe_ai_wrong': result[7],
            'odds_ai_correct': result[8],
            'odds_ai_wrong': result[9],
            'status': result[10],
            'total_pool_size': result[6] + result[7]
        }

    def get_player_balance(self, player_id: int) -> Dict:
        """Get player's VIBE balance and stats"""
        cursor = self.db.cursor()

        cursor.execute('INSERT OR IGNORE INTO vibe_balances (player_id) VALUES (?)', (player_id,))
        cursor.execute('''
            SELECT balance, total_wagered, total_won, total_lost
            FROM vibe_balances
            WHERE player_id = ?
        ''', (player_id,))

        balance, total_wagered, total_won, total_lost = cursor.fetchone()

        return {
            'balance': balance,
            'total_wagered': total_wagered,
            'total_won': total_won,
            'total_lost': total_lost,
            'net_profit': total_won - total_lost
        }


def main():
    """Demo story betting market"""
    market = StoryBettingMarket()

    print("=" * 60)
    print("🎲 STORY BETTING MARKET DEMO")
    print("=" * 60)

    # Create a betting pool
    pool_id = market.create_betting_pool(
        session_id=1,
        segment_number=1,
        ai_confidence=0.8,
        storyteller_reputation=25.5
    )

    # Place some bets
    player1_result = market.place_bet(player_id=1, pool_id=pool_id, bet_type='ai_wrong', amount=100)
    print()

    player2_result = market.place_bet(player_id=2, pool_id=pool_id, bet_type='ai_correct', amount=200)
    print()

    player3_result = market.place_bet(player_id=3, pool_id=pool_id, bet_type='plot_twist', amount=50)
    print()

    # Close betting
    market.close_betting(pool_id)
    print()

    # Resolve (storyteller surprised AI!)
    results = market.resolve_bets(
        pool_id=pool_id,
        actual_unpredictability=0.85,
        special_results={'plot_twist': True}
    )

    # Check balances
    print("\n📊 Final Balances:")
    for player_id in [1, 2, 3]:
        balance = market.get_player_balance(player_id)
        print(f"   Player {player_id}: {balance['balance']} VIBE (Net: {balance['net_profit']:+d} VIBE)")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Session-to-Soul Compiler - THE MISSING LINK

Compiles game session data back into user Soul Packs.

This is the FEEDBACK LOOP that makes Souls evolve from gameplay:
    Play chess → Actions logged → Soul expertise['chess']++

Before this: Game actions were logged but never affected Souls
After this: Everything you do in games shapes your digital identity

Architecture:
    game_actions table → Aggregate by user/game_type → Update Soul expertise
"""

import sqlite3
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict


class SessionToSoulCompiler:
    """
    Compiles game session data into Soul Pack updates

    Think of this like a "character sheet compiler" in D&D -
    your actions determine your stats.
    """

    def __init__(self):
        self.db_path = 'soulfra.db'

    def compile_user_soul(self, user_id: int) -> Dict[str, Any]:
        """
        Compile Soul Pack from ALL sources:
        - Posts/comments (existing soul_model.py logic)
        - Game sessions (NEW - this function)

        Returns: Updated Soul Pack with game expertise included
        """

        # Get base Soul from existing system
        from soul_model import Soul
        base_soul = Soul(user_id)
        soul_pack = base_soul.compile_pack()

        # Add game expertise
        game_expertise = self._compile_game_expertise(user_id)
        game_stats = self._compile_game_stats(user_id)

        # Merge into Soul Pack
        soul_pack['essence']['expertise'].update(game_expertise)
        soul_pack['expression']['games_played'] = game_stats['total_games']
        soul_pack['expression']['games_won'] = game_stats['wins']
        soul_pack['expression']['favorite_game'] = game_stats['favorite']

        return soul_pack

    def _compile_game_expertise(self, user_id: int) -> Dict[str, int]:
        """
        Calculate game expertise from game_actions

        Returns: {'2plus2': 5, 'chess': 12, 'monte_carlo': 3}
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all game actions for this user
        cursor.execute('''
            SELECT gs.game_type, COUNT(*) as action_count
            FROM game_actions ga
            JOIN game_sessions gs ON ga.game_id = gs.game_id
            WHERE ga.player_user_id = ?
            GROUP BY gs.game_type
        ''', (user_id,))

        results = cursor.fetchall()
        conn.close()

        # Build expertise dict
        expertise = {}
        for game_type, count in results:
            expertise[game_type] = count

        return expertise

    def _compile_game_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Calculate overall game statistics

        Returns: total games, wins, favorite game, etc.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count total games played
        cursor.execute('''
            SELECT COUNT(DISTINCT ga.game_id)
            FROM game_actions ga
            WHERE ga.player_user_id = ?
        ''', (user_id,))

        total_games = cursor.fetchone()[0]

        # Count wins (where AI verdict was 'success')
        cursor.execute('''
            SELECT COUNT(*)
            FROM game_actions
            WHERE player_user_id = ? AND ai_verdict = 'success'
        ''', (user_id,))

        wins = cursor.fetchone()[0]

        # Find most-played game type
        cursor.execute('''
            SELECT gs.game_type, COUNT(*) as count
            FROM game_actions ga
            JOIN game_sessions gs ON ga.game_id = gs.game_id
            WHERE ga.player_user_id = ?
            GROUP BY gs.game_type
            ORDER BY count DESC
            LIMIT 1
        ''', (user_id,))

        favorite_row = cursor.fetchone()
        favorite = favorite_row[0] if favorite_row else 'none'

        conn.close()

        return {
            'total_games': total_games,
            'wins': wins,
            'favorite': favorite
        }

    def get_game_actions_summary(self, user_id: int) -> Dict[str, List[Dict]]:
        """
        Get detailed summary of all game actions by type

        Useful for debugging and analytics
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all actions grouped by game type
        cursor.execute('''
            SELECT
                gs.game_type,
                ga.action_type,
                ga.ai_verdict,
                ga.submitted_at,
                ga.action_data
            FROM game_actions ga
            JOIN game_sessions gs ON ga.game_id = gs.game_id
            WHERE ga.player_user_id = ?
            ORDER BY ga.submitted_at DESC
        ''', (user_id,))

        actions = cursor.fetchall()
        conn.close()

        # Group by game type
        by_game = defaultdict(list)
        for game_type, action_type, verdict, timestamp, action_data in actions:
            by_game[game_type].append({
                'action': action_type,
                'verdict': verdict,
                'time': timestamp,
                'data': action_data
            })

        return dict(by_game)


def compile_soul_with_games(user_id: int) -> Dict[str, Any]:
    """
    MAIN FUNCTION: Compile complete Soul Pack including game data

    This is what should replace the old Soul.compile_pack() everywhere.

    Returns: Full Soul Pack with both post data AND game expertise
    """
    compiler = SessionToSoulCompiler()
    return compiler.compile_user_soul(user_id)


def show_soul_evolution(user_id: int):
    """
    Visual display of how games have shaped a Soul

    Shows before/after comparison
    """

    print()
    print("=" * 70)
    print("🧬 SOUL EVOLUTION FROM GAMES")
    print("=" * 70)
    print()

    # Get user info
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        print(f"❌ User {user_id} not found")
        return

    username = user[0]
    print(f"User: {username} (ID: {user_id})")
    print()

    # Compile Soul
    compiler = SessionToSoulCompiler()
    soul_pack = compiler.compile_user_soul(user_id)

    # Show expertise (both posts AND games)
    print("🎯 EXPERTISE (from posts + games):")
    print()

    for skill, score in sorted(soul_pack['essence']['expertise'].items(),
                                key=lambda x: x[1], reverse=True):
        # Check if this is a game expertise
        is_game = skill in ['2plus2', 'chess', 'tic_tac_toe', 'monte_carlo',
                            'dnd', 'math', 'strategy']

        icon = "🎮" if is_game else "📝"
        source = "games" if is_game else "posts"

        print(f"   {icon} {skill}: {score} ({source})")

    # Show game stats
    print()
    print("📊 GAME STATISTICS:")
    print()
    print(f"   Total games played: {soul_pack['expression'].get('games_played', 0)}")
    print(f"   Games won: {soul_pack['expression'].get('games_won', 0)}")
    print(f"   Favorite game: {soul_pack['expression'].get('favorite_game', 'none')}")

    # Show recent actions
    print()
    print("🕐 RECENT GAME ACTIONS:")
    print()

    summary = compiler.get_game_actions_summary(user_id)
    for game_type, actions in summary.items():
        print(f"   {game_type.upper()}:")
        for action in actions[:3]:  # Show last 3
            verdict_icon = "✅" if action['verdict'] == 'success' else "⚡" if action['verdict'] == 'partial' else "❌"
            print(f"      {verdict_icon} {action['action']} - {action['time']}")

    print()
    print("=" * 70)
    print("💡 YOUR SOUL EVOLVES WITH EVERY GAME YOU PLAY")
    print("=" * 70)
    print()


if __name__ == '__main__':
    """Test the compiler"""

    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 session_to_soul.py <user_id>")
        print()
        print("Example: python3 session_to_soul.py 2")
        sys.exit(1)

    user_id = int(sys.argv[1])

    # Show Soul evolution
    show_soul_evolution(user_id)

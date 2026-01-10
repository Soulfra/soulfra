#!/usr/bin/env python3
"""
2+2 Math Game - The SIMPLEST possible game

Proves the game orchestrator can handle ANY turn-based game,
even one as trivial as a single math question.

This is the "Hello World" of the game system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_orchestrator import GameOrchestrator
import sqlite3


class TwoPlusTwo:
    """
    The simplest possible game: 2+2=?

    One question. One answer. Either right or wrong.
    """

    def __init__(self, game_id: int, user_id: int):
        self.game_id = game_id
        self.user_id = user_id
        self.question = "What is 2 + 2?"
        self.correct_answer = 4

    def ask(self):
        """Ask the question"""
        print()
        print("=" * 50)
        print("🧮 2+2 MATH GAME")
        print("=" * 50)
        print()
        print(f"Question: {self.question}")
        print()

        # Get answer
        answer = input("Your answer: ").strip()

        try:
            answer_num = int(answer)
        except ValueError:
            print("❌ That's not a number!")
            return False

        # Check if correct
        is_correct = (answer_num == self.correct_answer)

        if is_correct:
            print()
            print("✅ CORRECT!")
            print(f"Yes, 2 + 2 = {self.correct_answer}")
        else:
            print()
            print(f"❌ WRONG!")
            print(f"You said {answer_num}, but 2 + 2 = {self.correct_answer}")

        print()

        return is_correct

    def submit_result(self, is_correct: bool):
        """Submit result to game orchestrator"""

        # Use the game orchestrator to log this action
        orch = GameOrchestrator(self.game_id)

        result = orch.process_action(
            user_id=self.user_id,
            platform='terminal',  # Playing via command line
            action_type='answer_question',
            action_data={
                'question': self.question,
                'answer': self.correct_answer if is_correct else 'wrong',
                'is_correct': is_correct,
                'game_type': '2plus2'
            }
        )

        return result


def create_2plus2_game(user_id: int) -> int:
    """Create a new 2+2 game session"""

    import json
    import hashlib

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Create game session
    cursor.execute('''
        INSERT INTO game_sessions (
            session_name, game_type, creator_user_id,
            max_players, dungeon_master_ai, enable_ai_judging
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        '2+2 Math Quiz',
        '2plus2',  # Game type
        user_id,
        1,  # Single player
        'none',  # No DM needed for math
        0  # No AI judging needed
    ))

    game_id = cursor.lastrowid

    # Create initial game state (required by orchestrator)
    initial_state = {
        'questions_asked': 0,
        'questions_correct': 0,
        'current_question': '2 + 2'
    }

    state_json = json.dumps(initial_state, sort_keys=True)
    state_hash = hashlib.sha256(state_json.encode()).hexdigest()

    cursor.execute('''
        INSERT INTO game_state (
            game_id, turn_number, board_state, player_positions,
            active_effects, state_hash, verified_by_network, is_current
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (game_id, 1, state_json, '{}', '[]', state_hash, 'math_validator', 1))

    conn.commit()
    conn.close()

    return game_id


def play_2plus2(user_id: int = None):
    """
    Play the 2+2 game

    Args:
        user_id: Optional user ID, defaults to first user in DB
    """

    # Get user
    if user_id is None:
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users LIMIT 1')
        user = cursor.fetchone()
        conn.close()

        if not user:
            print("❌ No users found. Run init_game_tables.py first.")
            return

        user_id = user[0]
        username = user[1]
    else:
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            print(f"❌ User {user_id} not found")
            return

        username = user[0]

    print(f"🎮 Player: {username} (ID: {user_id})")

    # Create game
    game_id = create_2plus2_game(user_id)
    print(f"📝 Game created (ID: {game_id})")

    # Play
    game = TwoPlusTwo(game_id, user_id)
    is_correct = game.ask()

    # Submit to orchestrator
    result = game.submit_result(is_correct)

    # Show result
    print("=" * 50)
    print("📊 GAME RESULT")
    print("=" * 50)
    print()
    print(f"Your answer: {'✅ CORRECT' if is_correct else '❌ WRONG'}")
    print(f"AI Verdict: {result.get('ai_verdict', 'N/A')}")
    print(f"Success: {result.get('success', False)}")
    print()

    if is_correct:
        print("🎉 You know basic math! Your Soul has been updated.")
        print("   expertise['math'] increased")
    else:
        print("📚 Study up on addition! Your attempt was recorded.")

    print()
    print("=" * 50)
    print()

    return game_id, is_correct


if __name__ == '__main__':
    """Run the game"""

    # Parse optional user_id argument
    user_id = None
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python3 {sys.argv[0]} [user_id]")
            sys.exit(1)

    play_2plus2(user_id)

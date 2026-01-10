#!/usr/bin/env python3
"""
Debug Quest Economy - Two-Way Debugging Marketplace

Pay for fast fixes OR earn by completing learning quests.

Two modes:
1. **Fast Fix** - User pays VIBE → AI + human debug → 10min guarantee
2. **Learning Quest** - Platform posts challenge → You solve → Earn VIBE

Philosophy:
- Debugging is valuable (people will pay)
- Learning is valuable (we'll pay you)
- Open source everything → GitHub network effects
- Fast local inference (Ollama, no API costs)
- Solutions become API docs

Integration:
- Uses debug_lab.py for AI error explanation
- Uses mvp_payments.py for VIBE tokens
- Uses payment_routes.py for payouts
- Uses ollama_client.py for fast inference
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from database import get_db
from ollama_client import OllamaClient


# ==============================================================================
# PRICING
# ==============================================================================

FAST_FIX_PRICING = {
    'simple': {
        'vibe': 5,      # $0.50 (syntax error, import issue)
        'time_limit': 5  # minutes
    },
    'medium': {
        'vibe': 10,     # $1.00 (logic bug, API error)
        'time_limit': 10
    },
    'complex': {
        'vibe': 25,     # $2.50 (architectural issue, performance)
        'time_limit': 20
    },
    'expert': {
        'vibe': 50,     # $5.00 (security, scaling, distributed systems)
        'time_limit': 30
    }
}

LEARNING_QUEST_REWARDS = {
    'beginner': 3,      # $0.30
    'intermediate': 10,  # $1.00
    'advanced': 25,     # $2.50
    'expert': 50        # $5.00
}


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_quest_tables():
    """Initialize debug quest tables"""
    conn = get_db()

    # Fast fix requests (users paying for help)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fast_fix_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            error_text TEXT NOT NULL,
            error_context TEXT,
            complexity TEXT DEFAULT 'medium',
            budget_vibe INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            ai_solution TEXT,
            human_solution TEXT,
            solver_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            solved_at TIMESTAMP,
            refunded BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (solver_id) REFERENCES users(id)
        )
    ''')

    # Learning quests (platform paying for solutions)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            error_example TEXT,
            difficulty TEXT DEFAULT 'intermediate',
            reward_vibe INTEGER NOT NULL,
            status TEXT DEFAULT 'open',
            category TEXT,
            tags TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            github_issue_url TEXT,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # Quest submissions
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quest_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            solution_text TEXT NOT NULL,
            solution_code TEXT,
            test_results TEXT,
            ai_review_score REAL,
            human_review_score REAL,
            status TEXT DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (quest_id) REFERENCES learning_quests(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Contributor reputation
    conn.execute('''
        CREATE TABLE IF NOT EXISTS debug_reputation (
            user_id INTEGER PRIMARY KEY,
            total_quests_solved INTEGER DEFAULT 0,
            total_vibe_earned INTEGER DEFAULT 0,
            avg_review_score REAL DEFAULT 0.0,
            fastest_solve_time INTEGER,
            specialty_tags TEXT,
            github_username TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Quest solutions as API docs
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quest_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_id INTEGER NOT NULL,
            submission_id INTEGER,
            doc_title TEXT NOT NULL,
            doc_content TEXT NOT NULL,
            doc_url TEXT,
            published BOOLEAN DEFAULT 0,
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quest_id) REFERENCES learning_quests(id),
            FOREIGN KEY (submission_id) REFERENCES quest_submissions(id)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# FAST FIX REQUESTS (PAY FOR HELP)
# ==============================================================================

class FastFixMarketplace:
    """Marketplace for users to pay for fast debugging help"""

    def __init__(self):
        self.ollama = OllamaClient()

    def create_fast_fix_request(
        self,
        user_id: int,
        error_text: str,
        error_context: Optional[str] = None,
        complexity: str = 'medium'
    ) -> Dict:
        """
        User creates fast fix request

        Args:
            user_id: User requesting help
            error_text: Error message/stack trace
            error_context: Optional context (file, code snippet)
            complexity: 'simple', 'medium', 'complex', 'expert'

        Returns:
            {
                'request_id': int,
                'cost_vibe': int,
                'time_limit': int (minutes),
                'ai_solution': str (instant AI attempt)
            }
        """

        if complexity not in FAST_FIX_PRICING:
            complexity = 'medium'

        pricing = FAST_FIX_PRICING[complexity]
        cost_vibe = pricing['vibe']
        time_limit = pricing['time_limit']

        # Check user balance
        if not self._has_sufficient_balance(user_id, cost_vibe):
            return {
                'success': False,
                'error': f'Insufficient VIBE balance. Need {cost_vibe} VIBE.'
            }

        # Deduct VIBE (held in escrow until solved or refunded)
        self._deduct_vibe(user_id, cost_vibe, 'fast_fix_request')

        # Get instant AI solution
        ai_solution = self._get_ai_solution(error_text, error_context, complexity)

        # Create request
        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO fast_fix_requests (
                user_id, error_text, error_context, complexity,
                budget_vibe, ai_solution
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, error_text, error_context, complexity, cost_vibe, ai_solution))

        request_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            'success': True,
            'request_id': request_id,
            'cost_vibe': cost_vibe,
            'time_limit': time_limit,
            'ai_solution': ai_solution,
            'message': f'AI solution generated instantly. Human review available for {time_limit} minutes.'
        }

    def solve_fast_fix(
        self,
        request_id: int,
        solver_id: int,
        solution_text: str
    ) -> Dict:
        """
        Solver (human or AI) provides solution

        Args:
            request_id: Fast fix request ID
            solver_id: User ID of solver
            solution_text: Debugging solution

        Returns:
            {
                'success': bool,
                'earned_vibe': int,
                'bonus_vibe': int (if solved quickly)
            }
        """

        conn = get_db()

        # Get request
        request = conn.execute('''
            SELECT * FROM fast_fix_requests WHERE id = ?
        ''', (request_id,)).fetchone()

        if not request:
            return {'success': False, 'error': 'Request not found'}

        if request['status'] != 'pending':
            return {'success': False, 'error': 'Request already solved or expired'}

        # Calculate time elapsed
        created_at = datetime.fromisoformat(request['created_at'])
        time_elapsed = (datetime.now() - created_at).seconds / 60  # minutes
        time_limit = FAST_FIX_PRICING[request['complexity']]['time_limit']

        # Check if within time limit
        if time_elapsed > time_limit:
            # Auto-refund user
            self._refund_vibe(request['user_id'], request['budget_vibe'])
            conn.execute('''
                UPDATE fast_fix_requests
                SET status = 'expired', refunded = 1
                WHERE id = ?
            ''', (request_id,))
            conn.commit()
            conn.close()
            return {'success': False, 'error': 'Request expired, user refunded'}

        # Mark as solved
        conn.execute('''
            UPDATE fast_fix_requests
            SET status = 'solved',
                human_solution = ?,
                solver_id = ?,
                solved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (solution_text, solver_id, request_id))

        # Calculate payout (80% to solver, 20% platform fee)
        base_payout = int(request['budget_vibe'] * 0.8)

        # Bonus for fast solve (within 50% of time limit)
        bonus = 0
        if time_elapsed < (time_limit * 0.5):
            bonus = int(base_payout * 0.2)  # 20% bonus

        total_payout = base_payout + bonus

        # Pay solver
        self._credit_vibe(solver_id, total_payout, 'fast_fix_solved')

        # Update reputation
        self._update_reputation(solver_id, 1, total_payout, time_elapsed)

        conn.commit()
        conn.close()

        return {
            'success': True,
            'earned_vibe': total_payout,
            'base_payout': base_payout,
            'bonus_vibe': bonus,
            'solve_time_minutes': round(time_elapsed, 1)
        }

    def _get_ai_solution(
        self,
        error_text: str,
        context: Optional[str],
        complexity: str
    ) -> str:
        """Get instant AI debugging solution"""

        prompt = f"""You are a debugging expert. Analyze this error and provide a solution.

Error:
{error_text}

Context:
{context if context else 'No additional context provided'}

Complexity: {complexity}

Provide:
1. **What happened** - Root cause
2. **How to fix** - Step-by-step solution
3. **Debug commands** - Commands to investigate
4. **Prevention** - How to avoid this in the future

Be concise and actionable."""

        result = self.ollama.generate(
            prompt=prompt,
            model='llama3.2',
            system_prompt='You are a helpful debugging assistant. Provide clear, actionable solutions.',
            temperature=0.3,
            max_tokens=800
        )

        return result.get('response', 'AI solution generation failed')

    def _has_sufficient_balance(self, user_id: int, amount: int) -> bool:
        """Check if user has enough VIBE"""
        conn = get_db()
        balance = conn.execute('''
            SELECT balance FROM vibe_balances WHERE soul_id = ?
        ''', (str(user_id),)).fetchone()
        conn.close()

        if not balance:
            return False

        return balance['balance'] >= amount

    def _deduct_vibe(self, user_id: int, amount: int, reason: str):
        """Deduct VIBE from user balance"""
        conn = get_db()
        conn.execute('''
            INSERT OR IGNORE INTO vibe_balances (soul_id, soul_type)
            VALUES (?, 'user')
        ''', (str(user_id),))

        conn.execute('''
            UPDATE vibe_balances
            SET balance = balance - ?,
                spent_total = spent_total + ?
            WHERE soul_id = ?
        ''', (amount, amount, str(user_id)))
        conn.commit()
        conn.close()

    def _credit_vibe(self, user_id: int, amount: int, reason: str):
        """Credit VIBE to user balance"""
        conn = get_db()
        conn.execute('''
            INSERT OR IGNORE INTO vibe_balances (soul_id, soul_type)
            VALUES (?, 'user')
        ''', (str(user_id),))

        conn.execute('''
            UPDATE vibe_balances
            SET balance = balance + ?,
                earned_total = earned_total + ?
            WHERE soul_id = ?
        ''', (amount, amount, str(user_id)))
        conn.commit()
        conn.close()

    def _refund_vibe(self, user_id: int, amount: int):
        """Refund VIBE to user"""
        self._credit_vibe(user_id, amount, 'refund')

    def _update_reputation(
        self,
        user_id: int,
        quests_solved: int,
        vibe_earned: int,
        solve_time: float
    ):
        """Update solver reputation"""
        conn = get_db()

        # Get current stats
        stats = conn.execute('''
            SELECT * FROM debug_reputation WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if stats:
            # Update existing
            new_total_quests = stats['total_quests_solved'] + quests_solved
            new_total_vibe = stats['total_vibe_earned'] + vibe_earned
            new_fastest = min(stats['fastest_solve_time'] or 999, int(solve_time))

            conn.execute('''
                UPDATE debug_reputation
                SET total_quests_solved = ?,
                    total_vibe_earned = ?,
                    fastest_solve_time = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_total_quests, new_total_vibe, new_fastest, user_id))
        else:
            # Create new
            conn.execute('''
                INSERT INTO debug_reputation (
                    user_id, total_quests_solved, total_vibe_earned, fastest_solve_time
                ) VALUES (?, ?, ?, ?)
            ''', (user_id, quests_solved, vibe_earned, int(solve_time)))

        conn.commit()
        conn.close()


# ==============================================================================
# LEARNING QUESTS (EARN BY SOLVING)
# ==============================================================================

class LearningQuestMarketplace:
    """Marketplace for learning by solving debugging challenges"""

    def __init__(self):
        self.ollama = OllamaClient()

    def create_quest(
        self,
        title: str,
        description: str,
        error_example: str,
        difficulty: str = 'intermediate',
        category: str = 'general',
        tags: List[str] = None,
        created_by: int = None
    ) -> Dict:
        """
        Create a new learning quest

        Args:
            title: Quest title
            description: Quest description
            error_example: Example error to debug
            difficulty: 'beginner', 'intermediate', 'advanced', 'expert'
            category: 'python', 'javascript', 'database', 'api', etc.
            tags: List of tags
            created_by: User ID of creator (admin or AI)

        Returns:
            {
                'quest_id': int,
                'reward_vibe': int,
                'difficulty': str
            }
        """

        if difficulty not in LEARNING_QUEST_REWARDS:
            difficulty = 'intermediate'

        reward_vibe = LEARNING_QUEST_REWARDS[difficulty]

        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO learning_quests (
                title, description, error_example, difficulty,
                reward_vibe, category, tags, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, description, error_example, difficulty,
            reward_vibe, category, json.dumps(tags or []), created_by
        ))

        quest_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            'success': True,
            'quest_id': quest_id,
            'reward_vibe': reward_vibe,
            'difficulty': difficulty,
            'message': f'Quest created! Reward: {reward_vibe} VIBE'
        }

    def submit_solution(
        self,
        quest_id: int,
        user_id: int,
        solution_text: str,
        solution_code: Optional[str] = None
    ) -> Dict:
        """
        Submit solution to a quest

        Args:
            quest_id: Quest ID
            user_id: Solver user ID
            solution_text: Explanation of solution
            solution_code: Code solution (optional)

        Returns:
            {
                'submission_id': int,
                'ai_review_score': float,
                'status': str
            }
        """

        conn = get_db()

        # Get quest
        quest = conn.execute('''
            SELECT * FROM learning_quests WHERE id = ?
        ''', (quest_id,)).fetchone()

        if not quest:
            return {'success': False, 'error': 'Quest not found'}

        if quest['status'] != 'open':
            return {'success': False, 'error': 'Quest is closed'}

        # Get AI review
        ai_review_score = self._ai_review_solution(
            quest['error_example'],
            solution_text,
            solution_code
        )

        # Create submission
        cursor = conn.execute('''
            INSERT INTO quest_submissions (
                quest_id, user_id, solution_text, solution_code, ai_review_score
            ) VALUES (?, ?, ?, ?, ?)
        ''', (quest_id, user_id, solution_text, solution_code, ai_review_score))

        submission_id = cursor.lastrowid

        # Auto-approve if AI score > 0.7
        if ai_review_score >= 0.7:
            self._approve_submission(quest_id, submission_id, user_id, quest['reward_vibe'])
            status = 'approved'
        else:
            status = 'pending_review'

        conn.commit()
        conn.close()

        return {
            'success': True,
            'submission_id': submission_id,
            'ai_review_score': ai_review_score,
            'status': status,
            'message': f'Submission received. AI score: {ai_review_score:.0%}'
        }

    def _ai_review_solution(
        self,
        error_example: str,
        solution_text: str,
        solution_code: Optional[str]
    ) -> float:
        """AI reviews solution and returns score 0-1"""

        prompt = f"""Review this debugging solution. Score from 0.0 to 1.0.

Error:
{error_example}

Solution:
{solution_text}

Code:
{solution_code if solution_code else 'No code provided'}

Criteria:
- Correct root cause identified? (40%)
- Solution actually fixes the problem? (40%)
- Clear explanation? (20%)

Output ONLY a decimal score (e.g., 0.85)"""

        result = self.ollama.generate(
            prompt=prompt,
            model='llama3.2',
            temperature=0.1,
            max_tokens=10
        )

        try:
            score = float(result.get('response', '0').strip())
            return max(0.0, min(1.0, score))
        except:
            return 0.5  # Default if AI fails

    def _approve_submission(
        self,
        quest_id: int,
        submission_id: int,
        user_id: int,
        reward_vibe: int
    ):
        """Approve submission and pay reward"""

        conn = get_db()

        # Mark quest as completed
        conn.execute('''
            UPDATE learning_quests
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (quest_id,))

        # Mark submission as approved
        conn.execute('''
            UPDATE quest_submissions
            SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (submission_id,))

        # Pay reward
        conn.execute('''
            INSERT OR IGNORE INTO vibe_balances (soul_id, soul_type)
            VALUES (?, 'user')
        ''', (str(user_id),))

        conn.execute('''
            UPDATE vibe_balances
            SET balance = balance + ?,
                earned_total = earned_total + ?
            WHERE soul_id = ?
        ''', (reward_vibe, reward_vibe, str(user_id)))

        # Update reputation
        conn.execute('''
            INSERT OR IGNORE INTO debug_reputation (user_id)
            VALUES (?)
        ''', (user_id,))

        conn.execute('''
            UPDATE debug_reputation
            SET total_quests_solved = total_quests_solved + 1,
                total_vibe_earned = total_vibe_earned + ?
            WHERE user_id = ?
        ''', (reward_vibe, user_id))

        conn.commit()
        conn.close()


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing Debug Quest Economy...")
    init_quest_tables()
    print("✅ Quest tables initialized")
    print()
    print("Fast Fix Pricing:")
    for complexity, pricing in FAST_FIX_PRICING.items():
        print(f"  {complexity}: {pricing['vibe']} VIBE (${pricing['vibe'] * 0.10:.2f}) - {pricing['time_limit']}min guarantee")
    print()
    print("Learning Quest Rewards:")
    for difficulty, reward in LEARNING_QUEST_REWARDS.items():
        print(f"  {difficulty}: {reward} VIBE (${reward * 0.10:.2f})")
    print()
    print("Ready to launch marketplace!")

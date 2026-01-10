#!/usr/bin/env python3
"""
Rate Limiter for Question/Reward System

Prevents spam by limiting how many questions a user can answer per hour.

Features:
- Configurable limit (default: 5 questions/hour)
- Per-user tracking
- Automatic reset after time window
- Returns remaining questions and time until reset

Usage:
    from rate_limiter import can_answer_question, record_question_answer

    if can_answer_question(user_id):
        # Allow answer
        record_question_answer(user_id, question_id)
    else:
        # Show error: "You've answered 5/5 questions. Next in 42 minutes."
"""

from database import get_db
from datetime import datetime, timedelta
from typing import Tuple, Optional


# Configuration
DEFAULT_QUESTIONS_PER_HOUR = 5
RATE_LIMIT_WINDOW_MINUTES = 60


def can_answer_question(user_id: int, limit: int = DEFAULT_QUESTIONS_PER_HOUR) -> Tuple[bool, int, Optional[int]]:
    """
    Check if user can answer another question

    Args:
        user_id: User ID
        limit: Max questions per hour

    Returns:
        Tuple of (can_answer, remaining_questions, seconds_until_reset)
    """
    db = get_db()

    # Get questions answered in last hour
    cutoff_time = datetime.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)

    answered = db.execute('''
        SELECT COUNT(*) as count, MIN(answered_at) as first_answer
        FROM user_question_answers
        WHERE user_id = ?
        AND answered_at > ?
    ''', (user_id, cutoff_time.isoformat())).fetchone()

    count = answered['count'] if answered else 0
    first_answer = answered['first_answer'] if answered else None

    # Calculate remaining
    remaining = max(0, limit - count)
    can_answer = remaining > 0

    # Calculate time until reset
    seconds_until_reset = None
    if count >= limit and first_answer:
        first_dt = datetime.fromisoformat(first_answer)
        reset_time = first_dt + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
        seconds_until_reset = max(0, int((reset_time - datetime.now()).total_seconds()))

    db.close()

    return (can_answer, remaining, seconds_until_reset)


def record_question_answer(user_id: int, question_id: int, xp_earned: int = 10) -> bool:
    """
    Record that user answered a question

    Args:
        user_id: User ID
        question_id: Question ID
        xp_earned: XP to award (default: 10)

    Returns:
        True if recorded successfully
    """
    db = get_db()

    try:
        # Record answer
        db.execute('''
            INSERT INTO user_question_answers (user_id, question_id, answered_at, xp_earned)
            VALUES (?, ?, ?, ?)
        ''', (user_id, question_id, datetime.now().isoformat(), xp_earned))

        # Award XP to loyalty points
        db.execute('''
            INSERT INTO loyalty_points (user_id, points, reason, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                points = points + ?,
                updated_at = ?
        ''', (user_id, xp_earned, f'Answered question {question_id}', datetime.now().isoformat(),
              xp_earned, datetime.now().isoformat()))

        db.commit()
        return True

    except Exception as e:
        print(f"Error recording question answer: {e}")
        db.rollback()
        return False

    finally:
        db.close()


def get_user_stats(user_id: int) -> dict:
    """
    Get user's question answering stats

    Args:
        user_id: User ID

    Returns:
        Dict with total_answered, total_xp, level
    """
    db = get_db()

    stats = db.execute('''
        SELECT
            COUNT(*) as total_answered,
            SUM(xp_earned) as total_xp
        FROM user_question_answers
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    # Get current XP from loyalty_points
    points_row = db.execute('''
        SELECT points FROM loyalty_points WHERE user_id = ?
    ''', (user_id,)).fetchone()

    total_xp = points_row['points'] if points_row else 0

    # Calculate level (every 100 XP = 1 level)
    level = total_xp // 100

    db.close()

    return {
        'total_answered': stats['total_answered'] if stats else 0,
        'total_xp': total_xp,
        'level': level,
        'xp_to_next_level': 100 - (total_xp % 100)
    }


def format_time_remaining(seconds: int) -> str:
    """
    Format seconds into human-readable time

    Args:
        seconds: Seconds remaining

    Returns:
        Formatted string like "42 minutes" or "1 hour 15 minutes"
    """
    if seconds < 60:
        return f"{seconds} seconds"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"


# Initialize database tables if they don't exist
def init_rate_limit_tables():
    """Create tables for rate limiting (call on app startup)"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS user_question_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answered_at TEXT NOT NULL,
            xp_earned INTEGER DEFAULT 10,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create index for fast lookups
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_question_answers_time
        ON user_question_answers(user_id, answered_at)
    ''')

    db.commit()
    db.close()


if __name__ == '__main__':
    # Test rate limiter
    print("🧪 Testing Rate Limiter\n")

    # Initialize tables
    init_rate_limit_tables()
    print("✅ Initialized rate limit tables")

    # Test with user_id 1
    user_id = 1

    print(f"\n📊 Testing user {user_id}:")

    # Check if can answer
    can_answer, remaining, seconds = can_answer_question(user_id, limit=5)
    print(f"   Can answer: {can_answer}")
    print(f"   Remaining: {remaining}/5")
    if seconds:
        print(f"   Reset in: {format_time_remaining(seconds)}")

    # Get stats
    stats = get_user_stats(user_id)
    print(f"\n📈 User Stats:")
    print(f"   Level: {stats['level']}")
    print(f"   Total XP: {stats['total_xp']}")
    print(f"   Questions answered: {stats['total_answered']}")
    print(f"   XP to next level: {stats['xp_to_next_level']}")

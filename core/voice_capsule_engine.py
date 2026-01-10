#!/usr/bin/env python3
"""
Voice Capsule Engine - Question Rotation Logic

Handles:
- Getting next question for a user based on domain and signup date
- Scheduling questions throughout the year
- Tracking which questions have been answered
- Determining rotation position based on signup timing
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List


def _get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_next_question_for_user(user_id: int, domain: str) -> Optional[Dict]:
    """
    Get the next unanswered question for a user in a specific domain

    Args:
        user_id: User ID
        domain: Domain name (calriven, deathtodata, howtocookathome, soulfra)

    Returns:
        Dictionary with question data, or None if all answered
    """
    db = _get_db()

    # Get user's signup date for this domain (or use account creation date)
    user_data = db.execute('''
        SELECT created_at FROM users WHERE id = ?
    ''', (user_id,)).fetchone()

    if not user_data:
        db.close()
        return None

    signup_date = datetime.fromisoformat(user_data['created_at'].replace(' ', 'T'))

    # Get domain's rotation period
    domain_info = db.execute('''
        SELECT rotation_period FROM voice_questions
        WHERE domain = ?
        LIMIT 1
    ''', (domain,)).fetchone()

    if not domain_info:
        db.close()
        return None

    rotation_period = domain_info['rotation_period']

    # Calculate which question position user should be at now
    current_position = _calculate_current_position(signup_date, rotation_period)

    # Get all questions for this domain in rotation order
    all_questions = db.execute('''
        SELECT id, question_text, category, vibe, expected_duration_seconds, rotation_order
        FROM voice_questions
        WHERE domain = ? AND active = 1
        ORDER BY rotation_order ASC
    ''', (domain,)).fetchall()

    if not all_questions:
        db.close()
        return None

    # Get questions user has already answered
    answered_ids = db.execute('''
        SELECT question_id FROM voice_responses
        WHERE user_id = ?
    ''', (user_id,)).fetchall()

    answered_set = {row['question_id'] for row in answered_ids}

    # Find next unanswered question starting from current position
    total_questions = len(all_questions)

    for offset in range(total_questions):
        idx = (current_position + offset) % total_questions
        question = all_questions[idx]

        if question['id'] not in answered_set:
            db.close()
            return {
                'id': question['id'],
                'question_text': question['question_text'],
                'category': question['category'],
                'vibe': question['vibe'],
                'expected_duration_seconds': question['expected_duration_seconds'],
                'rotation_order': question['rotation_order'],
                'domain': domain
            }

    # All questions answered
    db.close()
    return None


def _calculate_current_position(signup_date: datetime, rotation_period: str) -> int:
    """
    Calculate which question position user should be at based on time since signup

    Args:
        signup_date: When user signed up
        rotation_period: 'weekly' or 'monthly'

    Returns:
        Question position (0-indexed)
    """
    now = datetime.now()
    delta = now - signup_date

    if rotation_period == 'weekly':
        # One question per week
        weeks_since_signup = delta.days // 7
        return weeks_since_signup

    elif rotation_period == 'monthly':
        # One question per month
        months_since_signup = (now.year - signup_date.year) * 12 + (now.month - signup_date.month)
        return months_since_signup

    else:
        # Default to monthly
        months_since_signup = (now.year - signup_date.year) * 12 + (now.month - signup_date.month)
        return months_since_signup


def schedule_next_question_date(user_id: int, domain: str) -> Optional[datetime]:
    """
    Get the date when user's next question will be available

    Args:
        user_id: User ID
        domain: Domain name

    Returns:
        DateTime of next question, or None
    """
    db = _get_db()

    # Get user signup date
    user_data = db.execute('SELECT created_at FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user_data:
        db.close()
        return None

    signup_date = datetime.fromisoformat(user_data['created_at'].replace(' ', 'T'))

    # Get rotation period
    domain_info = db.execute('''
        SELECT rotation_period FROM voice_questions
        WHERE domain = ?
        LIMIT 1
    ''', (domain,)).fetchone()

    if not domain_info:
        db.close()
        return None

    rotation_period = domain_info['rotation_period']

    # Count how many questions user has answered
    answered_count = db.execute('''
        SELECT COUNT(*) as count FROM voice_responses
        WHERE user_id = ?
    ''', (user_id,)).fetchone()['count']

    db.close()

    # Calculate next question date
    if rotation_period == 'weekly':
        next_date = signup_date + timedelta(weeks=answered_count + 1)
    else:  # monthly
        # Add months (approximate with 30 days)
        next_date = signup_date + timedelta(days=30 * (answered_count + 1))

    return next_date


def mark_question_answered(user_id: int, question_id: int, transcription: str,
                          sentiment: float = 0.0, key_themes: str = '',
                          duration_seconds: int = 0) -> int:
    """
    Mark a question as answered and store the response

    Args:
        user_id: User ID
        question_id: Question ID
        transcription: Transcribed text of answer
        sentiment: Sentiment score (-1 to +1)
        key_themes: Comma-separated themes
        duration_seconds: Length of recording

    Returns:
        Response ID
    """
    db = _get_db()

    now = datetime.now()
    word_count = len(transcription.split())

    cursor = db.execute('''
        INSERT INTO voice_responses
        (user_id, question_id, transcription, sentiment, key_themes,
         word_count, duration_seconds, answered_at, year, month)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, question_id, transcription, sentiment, key_themes,
          word_count, duration_seconds, now, now.year, now.month))

    response_id = cursor.lastrowid

    db.commit()
    db.close()

    return response_id


def get_user_progress(user_id: int, domain: str) -> Dict:
    """
    Get user's progress in a domain

    Args:
        user_id: User ID
        domain: Domain name

    Returns:
        Dictionary with progress stats
    """
    db = _get_db()

    # Count total questions in domain
    total_questions = db.execute('''
        SELECT COUNT(*) as count FROM voice_questions
        WHERE domain = ? AND active = 1
    ''', (domain,)).fetchone()['count']

    # Count answered questions
    answered_questions = db.execute('''
        SELECT COUNT(*) as count
        FROM voice_responses vr
        JOIN voice_questions vq ON vr.question_id = vq.id
        WHERE vr.user_id = ? AND vq.domain = ?
    ''', (user_id, domain)).fetchone()['count']

    # Get average sentiment
    avg_sentiment = db.execute('''
        SELECT AVG(sentiment) as avg
        FROM voice_responses vr
        JOIN voice_questions vq ON vr.question_id = vq.id
        WHERE vr.user_id = ? AND vq.domain = ?
    ''', (user_id, domain)).fetchone()['avg'] or 0.0

    db.close()

    percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0

    return {
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'remaining_questions': total_questions - answered_questions,
        'progress_percentage': round(percentage, 1),
        'average_sentiment': round(avg_sentiment, 2)
    }


def get_all_user_responses(user_id: int, domain: str, year: Optional[int] = None) -> List[Dict]:
    """
    Get all responses from a user in a domain

    Args:
        user_id: User ID
        domain: Domain name
        year: Optional year filter

    Returns:
        List of response dictionaries
    """
    db = _get_db()

    query = '''
        SELECT
            vr.id,
            vr.transcription,
            vr.sentiment,
            vr.key_themes,
            vr.word_count,
            vr.duration_seconds,
            vr.answered_at,
            vq.question_text,
            vq.category,
            vq.vibe
        FROM voice_responses vr
        JOIN voice_questions vq ON vr.question_id = vq.id
        WHERE vr.user_id = ? AND vq.domain = ?
    '''

    params = [user_id, domain]

    if year:
        query += ' AND vr.year = ?'
        params.append(year)

    query += ' ORDER BY vr.answered_at ASC'

    responses = db.execute(query, params).fetchall()
    db.close()

    return [dict(row) for row in responses]


if __name__ == '__main__':
    # Test the engine
    print("Voice Capsule Engine Test")
    print("")

    # Example: Get next question for user 1 in calriven domain
    next_q = get_next_question_for_user(1, 'calriven')

    if next_q:
        print(f"Next question for user 1 (CalRiven): {next_q['question_text']}")
        print(f"Category: {next_q['category']}")
        print(f"Vibe: {next_q['vibe']}")
    else:
        print("No questions available or all answered")

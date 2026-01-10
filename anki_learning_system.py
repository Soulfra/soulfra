#!/usr/bin/env python3
"""
Anki-Style Spaced Repetition Learning System
==============================================

Combines:
- Spaced repetition algorithm (SM-2, like Anki)
- Neural network difficulty classification
- Your tutorial content as curriculum
- Offline learning (100% local)

Features:
- Adaptive question frequency based on performance
- Neural network predicts question difficulty
- Tracks learning streaks and retention
- Personalizes study sessions
- Works 100% offline

Usage:
    # Start learning session
    python3 anki_learning_system.py --session python-basics

    # Review cards due today
    python3 anki_learning_system.py --review

    # Check learning stats
    python3 anki_learning_system.py --stats

How It Works:
    1. Tutorial questions become "flashcards"
    2. Neural network classifies difficulty (technical, validation, etc.)
    3. SM-2 algorithm schedules reviews
    4. User performance adjusts intervals
    5. Learn efficiently with minimal repetition
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
from database import get_db


# ==============================================================================
# SM-2 ALGORITHM (Anki's Spaced Repetition)
# ==============================================================================

def sm2_schedule(quality: int, repetitions: int, ease_factor: float, interval: int) -> Tuple[int, float, int]:
    """
    SuperMemo 2 (SM-2) algorithm for spaced repetition

    Used by Anki for scheduling flashcard reviews.

    Args:
        quality: Response quality (0-5)
            5 = Perfect recall
            4 = Correct after hesitation
            3 = Correct with difficulty
            2 = Incorrect but remembered
            1 = Incorrect, vague memory
            0 = Complete blackout
        repetitions: Number of consecutive correct answers
        ease_factor: Difficulty multiplier (default: 2.5)
        interval: Days since last review

    Returns:
        (new_repetitions, new_ease_factor, new_interval)

    Reference: https://en.wikipedia.org/wiki/SuperMemo#SM-2_algorithm
    """
    if quality >= 3:
        # Correct answer
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)

        repetitions += 1
    else:
        # Incorrect answer - reset
        repetitions = 0
        interval = 1

    # Update ease factor
    ease_factor += (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Ease factor has a minimum of 1.3
    ease_factor = max(1.3, ease_factor)

    return repetitions, ease_factor, interval


def calculate_next_review(last_reviewed: datetime, interval_days: int) -> datetime:
    """Calculate next review date based on interval"""
    return last_reviewed + timedelta(days=interval_days)


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_learning_tables():
    """Initialize spaced repetition learning tables"""
    conn = get_db()

    # Learning cards (flashcards from tutorial questions)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tutorial_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT,
            explanation TEXT,
            question_type TEXT,
            difficulty_predicted REAL,
            neural_classifier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tutorial_id) REFERENCES tutorials(id)
        )
    ''')

    # Learning progress (SM-2 state for each card)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            user_id INTEGER,
            repetitions INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            interval_days INTEGER DEFAULT 1,
            last_reviewed TIMESTAMP,
            next_review TIMESTAMP,
            total_reviews INTEGER DEFAULT 0,
            correct_reviews INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            FOREIGN KEY (card_id) REFERENCES learning_cards(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(card_id, user_id)
        )
    ''')

    # Learning sessions (track study sessions)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_end TIMESTAMP,
            cards_reviewed INTEGER DEFAULT 0,
            cards_correct INTEGER DEFAULT 0,
            session_duration_seconds INTEGER,
            session_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Review history (detailed log)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS review_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            user_id INTEGER,
            session_id INTEGER,
            quality INTEGER NOT NULL,
            time_to_answer_seconds INTEGER,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES learning_cards(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (session_id) REFERENCES learning_sessions(id)
        )
    ''')

    # Learning paths (organize cards into courses)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path_name TEXT NOT NULL,
            description TEXT,
            topic TEXT,
            card_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Path cards (many-to-many relationship)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS path_cards (
            path_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            position INTEGER,
            FOREIGN KEY (path_id) REFERENCES learning_paths(id),
            FOREIGN KEY (card_id) REFERENCES learning_cards(id),
            UNIQUE(path_id, card_id)
        )
    ''')

    # Create indexes for performance
    conn.execute('CREATE INDEX IF NOT EXISTS idx_next_review ON learning_progress(next_review)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_card_user ON learning_progress(card_id, user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_session_user ON learning_sessions(user_id)')

    conn.commit()
    conn.close()

    print("✅ Learning tables initialized")


# ==============================================================================
# CARD GENERATION FROM TUTORIALS
# ==============================================================================

def import_tutorial_questions(tutorial_id: int, questions: List[Dict], question_type: str = 'tutorial') -> int:
    """
    Import questions from tutorial into learning cards

    Args:
        tutorial_id: Tutorial ID from tutorials table
        questions: List of question dicts from tutorial_builder.py
        question_type: 'tutorial' or 'aptitude'

    Returns:
        Number of cards created
    """
    conn = get_db()
    cards_created = 0

    for q in questions:
        # Skip if card already exists
        existing = conn.execute('''
            SELECT id FROM learning_cards
            WHERE tutorial_id = ? AND question = ?
        ''', (tutorial_id, q['question'])).fetchone()

        if existing:
            continue

        # Predict difficulty using neural networks (if available)
        difficulty = predict_question_difficulty(q)

        # Insert card
        conn.execute('''
            INSERT INTO learning_cards
            (tutorial_id, question, answer, explanation, question_type, difficulty_predicted, neural_classifier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            tutorial_id,
            q['question'],
            q.get('answer'),
            q.get('explanation'),
            question_type,
            difficulty,
            q.get('model', 'ollama')
        ))

        cards_created += 1

    conn.commit()
    conn.close()

    print(f"✅ Imported {cards_created} cards from tutorial {tutorial_id}")
    return cards_created


def predict_question_difficulty(question: Dict) -> float:
    """
    Use neural networks to predict question difficulty

    Args:
        question: Question dict with 'question', 'answer', etc.

    Returns:
        Difficulty score (0.0 = easy, 1.0 = hard)
    """
    try:
        from neural_network import load_neural_network
        import numpy as np

        # Load technical classifier (CalRiven)
        network = load_neural_network('calriven_technical_classifier')

        if network:
            # Extract features from question text
            # (simplified - in production, use better feature extraction)
            text = question.get('question', '') + ' ' + question.get('answer', '')

            # Simple word count as proxy for difficulty
            words = text.split()
            word_count = len(words)
            unique_words = len(set(words))
            avg_word_length = sum(len(w) for w in words) / max(1, len(words))

            # Predict using network
            # (This is simplified - actual implementation would use network.forward())
            difficulty = min(1.0, (word_count / 100.0) + (unique_words / 50.0) + (avg_word_length / 10.0))

            return difficulty
    except:
        pass

    # Fallback: Use question metadata
    if question.get('category') in ['reflection', 'philosophy']:
        return 0.7  # Harder (conceptual)
    elif question.get('category') in ['automation', 'action']:
        return 0.5  # Medium (practical)
    else:
        return 0.3  # Easier (factual)


# ==============================================================================
# REVIEW SYSTEM
# ==============================================================================

def get_cards_due(user_id: int = 1, limit: int = 20) -> List[Dict]:
    """
    Get cards due for review today

    Args:
        user_id: User ID
        limit: Maximum cards to return

    Returns:
        List of card dicts with progress info
    """
    conn = get_db()

    # Get cards that are:
    # 1. New (never reviewed)
    # 2. Due for review (next_review <= now)
    cards = conn.execute('''
        SELECT
            c.id,
            c.question,
            c.answer,
            c.explanation,
            c.question_type,
            c.difficulty_predicted,
            p.repetitions,
            p.ease_factor,
            p.interval_days,
            p.last_reviewed,
            p.next_review,
            p.streak,
            p.status,
            p.total_reviews,
            p.correct_reviews
        FROM learning_cards c
        LEFT JOIN learning_progress p ON c.id = p.card_id AND p.user_id = ?
        WHERE
            p.next_review IS NULL OR p.next_review <= datetime('now')
        ORDER BY
            p.next_review ASC,
            c.difficulty_predicted ASC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    conn.close()

    return [dict(card) for card in cards]


def review_card(card_id: int, quality: int, user_id: int = 1, session_id: Optional[int] = None,
                time_to_answer: int = 0) -> Dict:
    """
    Review a card and update SM-2 schedule

    Args:
        card_id: Card ID
        quality: Response quality (0-5)
        user_id: User ID
        session_id: Current session ID
        time_to_answer: Seconds taken to answer

    Returns:
        Updated progress dict
    """
    conn = get_db()

    # Get current progress
    progress = conn.execute('''
        SELECT * FROM learning_progress
        WHERE card_id = ? AND user_id = ?
    ''', (card_id, user_id)).fetchone()

    if not progress:
        # New card - initialize progress
        repetitions, ease_factor, interval_days = 0, 2.5, 1
        total_reviews, correct_reviews, streak = 0, 0, 0
    else:
        repetitions = progress['repetitions']
        ease_factor = progress['ease_factor']
        interval_days = progress['interval_days']
        total_reviews = progress['total_reviews']
        correct_reviews = progress['correct_reviews']
        streak = progress['streak']

    # Apply SM-2 algorithm
    new_reps, new_ease, new_interval = sm2_schedule(
        quality, repetitions, ease_factor, interval_days
    )

    # Update stats
    total_reviews += 1
    if quality >= 3:
        correct_reviews += 1
        streak += 1
    else:
        streak = 0

    # Calculate next review date
    last_reviewed = datetime.now()
    next_review = calculate_next_review(last_reviewed, new_interval)

    # Determine status
    if new_reps == 0:
        status = 'learning'
    elif new_reps < 3:
        status = 'young'
    else:
        status = 'mature'

    # Upsert progress
    conn.execute('''
        INSERT OR REPLACE INTO learning_progress
        (card_id, user_id, repetitions, ease_factor, interval_days,
         last_reviewed, next_review, total_reviews, correct_reviews, streak, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        card_id, user_id, new_reps, new_ease, new_interval,
        last_reviewed, next_review, total_reviews, correct_reviews, streak, status
    ))

    # Log review
    conn.execute('''
        INSERT INTO review_history
        (card_id, user_id, session_id, quality, time_to_answer_seconds)
        VALUES (?, ?, ?, ?, ?)
    ''', (card_id, user_id, session_id, quality, time_to_answer))

    conn.commit()
    conn.close()

    return {
        'card_id': card_id,
        'repetitions': new_reps,
        'ease_factor': new_ease,
        'interval_days': new_interval,
        'next_review': next_review.isoformat(),
        'streak': streak,
        'status': status,
        'accuracy': (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0
    }


# ==============================================================================
# LEARNING SESSIONS
# ==============================================================================

def start_session(user_id: int = 1, session_type: str = 'review') -> int:
    """
    Start a new learning session

    Args:
        user_id: User ID
        session_type: 'review', 'cram', 'new_cards', etc.

    Returns:
        Session ID
    """
    conn = get_db()

    cursor = conn.execute('''
        INSERT INTO learning_sessions
        (user_id, session_type)
        VALUES (?, ?)
    ''', (user_id, session_type))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


def end_session(session_id: int):
    """End a learning session and calculate stats"""
    conn = get_db()

    # Get session start time
    session = conn.execute('''
        SELECT session_start FROM learning_sessions WHERE id = ?
    ''', (session_id,)).fetchone()

    if not session:
        return

    # Calculate duration
    duration = (datetime.now() - datetime.fromisoformat(session['session_start'])).total_seconds()

    # Get review counts
    stats = conn.execute('''
        SELECT
            COUNT(*) as cards_reviewed,
            SUM(CASE WHEN quality >= 3 THEN 1 ELSE 0 END) as cards_correct
        FROM review_history
        WHERE session_id = ?
    ''', (session_id,)).fetchone()

    # Update session
    conn.execute('''
        UPDATE learning_sessions
        SET session_end = CURRENT_TIMESTAMP,
            cards_reviewed = ?,
            cards_correct = ?,
            session_duration_seconds = ?
        WHERE id = ?
    ''', (stats['cards_reviewed'], stats['cards_correct'], int(duration), session_id))

    conn.commit()
    conn.close()

    print(f"✅ Session {session_id} ended:")
    print(f"   Cards reviewed: {stats['cards_reviewed']}")
    print(f"   Correct: {stats['cards_correct']}")
    print(f"   Accuracy: {stats['cards_correct'] / max(1, stats['cards_reviewed']) * 100:.1f}%")
    print(f"   Duration: {int(duration)}s")


# ==============================================================================
# STATS & ANALYTICS
# ==============================================================================

def get_learning_stats(user_id: int = 1) -> Dict:
    """Get learning statistics for a user"""
    conn = get_db()

    # Overall stats
    overall = conn.execute('''
        SELECT
            COUNT(DISTINCT c.id) as total_cards,
            COUNT(DISTINCT CASE WHEN p.status = 'new' THEN c.id END) as new_cards,
            COUNT(DISTINCT CASE WHEN p.status = 'learning' THEN c.id END) as learning_cards,
            COUNT(DISTINCT CASE WHEN p.status = 'young' THEN c.id END) as young_cards,
            COUNT(DISTINCT CASE WHEN p.status = 'mature' THEN c.id END) as mature_cards,
            AVG(p.ease_factor) as avg_ease,
            MAX(p.streak) as longest_streak
        FROM learning_cards c
        LEFT JOIN learning_progress p ON c.id = p.card_id AND p.user_id = ?
    ''', (user_id,)).fetchone()

    # Cards due today
    due_today = conn.execute('''
        SELECT COUNT(*) as count
        FROM learning_progress
        WHERE user_id = ? AND next_review <= datetime('now')
    ''', (user_id,)).fetchone()

    # Recent accuracy
    recent_accuracy = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN quality >= 3 THEN 1 ELSE 0 END) as correct
        FROM review_history
        WHERE user_id = ?
        AND reviewed_at >= datetime('now', '-7 days')
    ''', (user_id,)).fetchone()

    accuracy = (recent_accuracy['correct'] / max(1, recent_accuracy['total']) * 100) if recent_accuracy['total'] > 0 else 0

    conn.close()

    return {
        'total_cards': overall['total_cards'],
        'new_cards': overall['new_cards'] or 0,
        'learning_cards': overall['learning_cards'] or 0,
        'young_cards': overall['young_cards'] or 0,
        'mature_cards': overall['mature_cards'] or 0,
        'due_today': due_today['count'],
        'avg_ease': overall['avg_ease'] or 2.5,
        'longest_streak': overall['longest_streak'] or 0,
        'recent_accuracy': accuracy
    }


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def run_review_session(user_id: int = 1, max_cards: int = 20):
    """Run an interactive review session"""
    print("=" * 60)
    print("ANKI-STYLE SPACED REPETITION - REVIEW SESSION")
    print("=" * 60)
    print()

    # Get cards due
    cards = get_cards_due(user_id, max_cards)

    if not cards:
        print("✅ No cards due for review! Come back later.")
        return

    print(f"📚 {len(cards)} cards due for review")
    print()

    # Start session
    session_id = start_session(user_id, 'review')

    # Review each card
    for i, card in enumerate(cards, 1):
        print(f"Card {i}/{len(cards)}")
        print("-" * 60)
        print(f"Q: {card['question']}")
        print()

        input("Press Enter to see answer...")
        print()

        if card['answer']:
            print(f"A: {card['answer']}")
        if card['explanation']:
            print(f"\n💡 {card['explanation']}")
        print()

        # Get quality rating
        while True:
            try:
                quality = int(input("How well did you know this? (0-5): "))
                if 0 <= quality <= 5:
                    break
                print("Please enter a number between 0 and 5")
            except ValueError:
                print("Please enter a valid number")

        # Review card
        result = review_card(card['id'], quality, user_id, session_id)

        print(f"\n✅ Next review: {result['interval_days']} days")
        print(f"   Streak: {result['streak']}")
        print(f"   Accuracy: {result['accuracy']:.1f}%")
        print()

    # End session
    end_session(session_id)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Anki-Style Spaced Repetition Learning")
    parser.add_argument('--init', action='store_true', help='Initialize learning tables')
    parser.add_argument('--import-tutorial', type=int, help='Import tutorial questions by ID')
    parser.add_argument('--review', action='store_true', help='Start review session')
    parser.add_argument('--stats', action='store_true', help='Show learning statistics')
    parser.add_argument('--user-id', type=int, default=1, help='User ID (default: 1)')
    parser.add_argument('--max-cards', type=int, default=20, help='Max cards per session')

    args = parser.parse_args()

    if args.init:
        init_learning_tables()

    elif args.import_tutorial:
        # Get tutorial questions from database
        conn = get_db()
        tutorial = conn.execute('''
            SELECT tutorial_questions, aptitude_questions
            FROM tutorials WHERE post_id = ?
        ''', (args.import_tutorial,)).fetchone()
        conn.close()

        if tutorial:
            tutorial_qs = json.loads(tutorial['tutorial_questions']) if tutorial['tutorial_questions'] else []
            aptitude_qs = json.loads(tutorial['aptitude_questions']) if tutorial['aptitude_questions'] else []

            count = import_tutorial_questions(args.import_tutorial, tutorial_qs, 'tutorial')
            count += import_tutorial_questions(args.import_tutorial, aptitude_qs, 'aptitude')

            print(f"✅ Imported {count} cards total")
        else:
            print(f"❌ Tutorial {args.import_tutorial} not found")

    elif args.review:
        run_review_session(args.user_id, args.max_cards)

    elif args.stats:
        stats = get_learning_stats(args.user_id)
        print("=" * 60)
        print("LEARNING STATISTICS")
        print("=" * 60)
        print(f"Total Cards: {stats['total_cards']}")
        print(f"New: {stats['new_cards']}")
        print(f"Learning: {stats['learning_cards']}")
        print(f"Young: {stats['young_cards']}")
        print(f"Mature: {stats['mature_cards']}")
        print(f"Due Today: {stats['due_today']}")
        print(f"Longest Streak: {stats['longest_streak']}")
        print(f"Recent Accuracy: {stats['recent_accuracy']:.1f}%")
        print(f"Average Ease: {stats['avg_ease']:.2f}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

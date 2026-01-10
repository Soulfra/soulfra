#!/usr/bin/env python3
"""
Idea Backpropagation System - Neural Network Learning Applied to Human Thinking

Revolutionary Concept:
--------------------
Apply backpropagation (neural network training) to idea evolution:
- Track ideas over time (forward pass = submit idea)
- Validate correctness months/years later (compare prediction vs reality)
- Backpropagate success/failure through user's idea history (update weights = reputation)
- Generate personalized questions based on patterns (gradient descent = refinement direction)

The Analogy:
-----------
Neural Network → Human Thinking
- Forward pass → Submit idea
- Prediction → Your claim about the future
- Loss function → How wrong you were
- Backpropagation → Update your reputation based on accuracy
- Gradient descent → Questions that push you toward better ideas
- Training data → Time capsule of past ideas
- Model weights → User's accuracy score + reputation

User Experience:
---------------
1. Submit idea: "I think privacy-first analytics will be huge in 2025"
2. Time passes... (6 months)
3. Validation event: Privacy-first analytics raises $50M
4. Backpropagate: User was RIGHT! Accuracy ↑, Reputation ↑
5. Time capsule shows: "You predicted this 196 days early!"
6. New question generated: "What else will explode in privacy tech?"

Better Than Reddit:
------------------
Reddit: Popularity-based (groupthink wins)
Soulfra: Accuracy-based (correctness wins)

- Early bird bonus: Reward being ahead of the curve
- Confidence calibration: Penalty for overconfidence
- Idea lineage: Track refinements (vague → specific → technical)
- Reskinning: Same idea, different brand voice

Philosophy:
----------
"The best ideas are often unpopular at first.
We reward you for being RIGHT, not for being LIKED."

Tables:
-------
idea_lineage: Links parent → child ideas (refinement chains)
idea_outcomes: Validation results (was the idea correct?)
user_accuracy: Reputation scores (how often are you right?)

Usage:
------
from idea_backpropagation import (
    link_ideas,              # Connect parent → child
    record_outcome,          # Mark idea as validated
    calculate_accuracy,      # Get user's accuracy score
    backpropagate_success,   # Update reputation based on validation
    get_time_capsule,        # Show idea evolution timeline
    generate_next_question   # Coach mode
)

# When user improves an idea
link_ideas(
    parent_tracking_id="IDEA-ABC123",
    child_tracking_id="IDEA-XYZ789",
    refinement_type="technical_depth",
    question="How would you implement this?"
)

# When idea is validated months later
record_outcome(
    tracking_id="IDEA-ABC123",
    outcome_result=1.0,  # 1.0 = completely right, 0.0 = completely wrong
    validation_source="TechCrunch article",
    validation_url="https://..."
)

# Update user's reputation
backpropagate_success(tracking_id="IDEA-ABC123")
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_db


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def create_backpropagation_tables():
    """
    Create tables for idea backpropagation system

    Tables:
    - idea_lineage: Parent → child idea relationships
    - idea_outcomes: Validation results (right/wrong over time)
    - user_accuracy: Reputation tracking (accuracy scores)
    """
    conn = get_db()

    # Idea Lineage - Track refinement chains
    conn.execute('''
        CREATE TABLE IF NOT EXISTS idea_lineage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_submission_id INTEGER NOT NULL,
            child_submission_id INTEGER NOT NULL,
            refinement_type TEXT NOT NULL,
            question_that_led_here TEXT,
            depth_increase REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_submission_id) REFERENCES idea_submissions(id),
            FOREIGN KEY (child_submission_id) REFERENCES idea_submissions(id),
            UNIQUE(parent_submission_id, child_submission_id)
        )
    ''')

    # Idea Outcomes - Validation over time
    conn.execute('''
        CREATE TABLE IF NOT EXISTS idea_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            outcome_result REAL NOT NULL,
            confidence_at_submission REAL DEFAULT 0.5,
            days_until_validation INTEGER,
            early_bird_multiplier REAL DEFAULT 1.0,
            calibration_penalty REAL DEFAULT 0.0,
            accuracy_score REAL NOT NULL,
            validation_source TEXT,
            validation_url TEXT,
            validation_notes TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES idea_submissions(id)
        )
    ''')

    # User Accuracy - Reputation tracking
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_accuracy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            total_submissions INTEGER DEFAULT 0,
            total_validations INTEGER DEFAULT 0,
            accuracy_rate REAL DEFAULT 0.0,
            average_days_early REAL DEFAULT 0.0,
            calibration_score REAL DEFAULT 0.0,
            reputation_score REAL DEFAULT 0.0,
            depth_level REAL DEFAULT 0.0,
            last_submission_at TIMESTAMP,
            last_validation_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_email)
        )
    ''')

    # Indexes for performance
    conn.execute('CREATE INDEX IF NOT EXISTS idx_lineage_parent ON idea_lineage(parent_submission_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_lineage_child ON idea_lineage(child_submission_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_outcomes_submission ON idea_outcomes(submission_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_accuracy_email ON user_accuracy(user_email)')

    conn.commit()
    conn.close()

    print("✅ Idea backpropagation tables created!")


# ==============================================================================
# IDEA LINEAGE - Link Parent → Child Ideas
# ==============================================================================

def link_ideas(
    parent_tracking_id: str,
    child_tracking_id: str,
    refinement_type: str,
    question: Optional[str] = None,
    depth_increase: float = 0.1
) -> bool:
    """
    Link two ideas in parent → child relationship

    Refinement types:
    - 'clarification': Made the idea clearer
    - 'technical_depth': Added implementation details
    - 'expansion': Broadened the scope
    - 'pivot': Changed direction based on insight
    - 'validation': Added evidence/research

    Args:
        parent_tracking_id: Original idea (e.g., IDEA-ABC123)
        child_tracking_id: Refined idea (e.g., IDEA-XYZ789)
        refinement_type: Type of refinement
        question: Question that led to refinement
        depth_increase: How much deeper this idea is (0.0-1.0)

    Returns:
        True if linked successfully
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get submission IDs
    cursor.execute('SELECT id FROM idea_submissions WHERE tracking_id = ?', (parent_tracking_id,))
    parent = cursor.fetchone()

    cursor.execute('SELECT id FROM idea_submissions WHERE tracking_id = ?', (child_tracking_id,))
    child = cursor.fetchone()

    if not parent or not child:
        conn.close()
        return False

    parent_id = parent['id']
    child_id = child['id']

    try:
        cursor.execute('''
            INSERT INTO idea_lineage (
                parent_submission_id,
                child_submission_id,
                refinement_type,
                question_that_led_here,
                depth_increase
            ) VALUES (?, ?, ?, ?, ?)
        ''', (parent_id, child_id, refinement_type, question, depth_increase))

        conn.commit()
        print(f"✅ Linked {parent_tracking_id} → {child_tracking_id} ({refinement_type})")
        return True

    except sqlite3.IntegrityError:
        print(f"⚠️  Link already exists: {parent_tracking_id} → {child_tracking_id}")
        return False

    finally:
        conn.close()


def get_idea_children(tracking_id: str) -> List[Dict]:
    """Get all ideas that refined this one"""
    conn = get_db()

    children = conn.execute('''
        SELECT
            s.tracking_id,
            s.idea_text,
            s.created_at,
            l.refinement_type,
            l.question_that_led_here,
            l.depth_increase
        FROM idea_lineage l
        JOIN idea_submissions s ON l.child_submission_id = s.id
        JOIN idea_submissions p ON l.parent_submission_id = p.id
        WHERE p.tracking_id = ?
        ORDER BY s.created_at ASC
    ''', (tracking_id,)).fetchall()

    conn.close()

    return [dict(c) for c in children]


def get_idea_parents(tracking_id: str) -> List[Dict]:
    """Get all ideas that this one refined"""
    conn = get_db()

    parents = conn.execute('''
        SELECT
            s.tracking_id,
            s.idea_text,
            s.created_at,
            l.refinement_type,
            l.question_that_led_here,
            l.depth_increase
        FROM idea_lineage l
        JOIN idea_submissions s ON l.parent_submission_id = s.id
        JOIN idea_submissions p ON l.child_submission_id = p.id
        WHERE p.tracking_id = ?
        ORDER BY s.created_at DESC
    ''', (tracking_id,)).fetchall()

    conn.close()

    return [dict(p) for p in parents]


def get_idea_lineage_tree(tracking_id: str) -> Dict:
    """
    Get full lineage tree for an idea

    Returns:
        {
            'root': original_idea,
            'children': [...],
            'parents': [...],
            'depth': total_depth_from_root
        }
    """
    conn = get_db()

    # Get the idea itself
    idea = conn.execute('''
        SELECT * FROM idea_submissions WHERE tracking_id = ?
    ''', (tracking_id,)).fetchone()

    if not idea:
        conn.close()
        return None

    conn.close()

    return {
        'idea': dict(idea),
        'parents': get_idea_parents(tracking_id),
        'children': get_idea_children(tracking_id),
        'tracking_id': tracking_id
    }


# ==============================================================================
# IDEA OUTCOMES - Validation Over Time
# ==============================================================================

def record_outcome(
    tracking_id: str,
    outcome_result: float,
    validation_source: str = None,
    validation_url: str = None,
    validation_notes: str = None,
    confidence_at_submission: float = 0.5
) -> bool:
    """
    Record validation outcome for an idea

    Args:
        tracking_id: Idea to validate (e.g., IDEA-ABC123)
        outcome_result: 0.0 (completely wrong) to 1.0 (completely right)
        validation_source: Where validation came from
        validation_url: Link to evidence
        validation_notes: Additional context
        confidence_at_submission: User's original confidence (0.0-1.0)

    Returns:
        True if recorded successfully
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get submission
    cursor.execute('''
        SELECT id, created_at FROM idea_submissions WHERE tracking_id = ?
    ''', (tracking_id,))

    submission = cursor.fetchone()

    if not submission:
        conn.close()
        return False

    submission_id = submission['id']
    created_at = datetime.fromisoformat(submission['created_at'])

    # Calculate time to validation
    days_until_validation = (datetime.now() - created_at).days

    # Early bird multiplier: +1x per year early (max 5x)
    years_early = days_until_validation / 365.0
    early_bird_multiplier = min(1.0 + years_early, 5.0)

    # Calibration penalty: penalize overconfidence
    # If you were 90% confident but only 50% right → penalty
    # If you were 50% confident and 50% right → no penalty
    confidence_error = abs(confidence_at_submission - outcome_result)
    calibration_penalty = confidence_error * 0.5  # Max 0.5 penalty

    # Accuracy score formula
    accuracy_score = (outcome_result * early_bird_multiplier) - calibration_penalty
    accuracy_score = max(0.0, accuracy_score)  # Can't be negative

    # Record outcome
    cursor.execute('''
        INSERT INTO idea_outcomes (
            submission_id,
            outcome_result,
            confidence_at_submission,
            days_until_validation,
            early_bird_multiplier,
            calibration_penalty,
            accuracy_score,
            validation_source,
            validation_url,
            validation_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        submission_id,
        outcome_result,
        confidence_at_submission,
        days_until_validation,
        early_bird_multiplier,
        calibration_penalty,
        accuracy_score,
        validation_source,
        validation_url,
        validation_notes
    ))

    conn.commit()
    conn.close()

    print(f"✅ Recorded outcome for {tracking_id}:")
    print(f"   Result: {outcome_result:.2f}")
    print(f"   Days early: {days_until_validation}")
    print(f"   Early bird multiplier: {early_bird_multiplier:.2f}x")
    print(f"   Accuracy score: {accuracy_score:.2f}")

    return True


def get_idea_outcome(tracking_id: str) -> Optional[Dict]:
    """Get validation outcome for an idea"""
    conn = get_db()

    outcome = conn.execute('''
        SELECT o.*, s.tracking_id, s.idea_text, s.created_at as submission_date
        FROM idea_outcomes o
        JOIN idea_submissions s ON o.submission_id = s.id
        WHERE s.tracking_id = ?
    ''', (tracking_id,)).fetchone()

    conn.close()

    return dict(outcome) if outcome else None


# ==============================================================================
# USER ACCURACY - Reputation Tracking
# ==============================================================================

def calculate_user_accuracy(email: str) -> Dict:
    """
    Calculate accuracy metrics for a user

    Returns:
        {
            'total_submissions': int,
            'total_validations': int,
            'accuracy_rate': float (0.0-1.0),
            'average_days_early': float,
            'calibration_score': float,
            'reputation_score': float,
            'depth_level': float (0.0-1.0)
        }
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get all submissions for user
    cursor.execute('''
        SELECT COUNT(*) as count FROM idea_submissions WHERE user_email = ?
    ''', (email,))
    total_submissions = cursor.fetchone()['count']

    # Get all validated outcomes
    cursor.execute('''
        SELECT o.*
        FROM idea_outcomes o
        JOIN idea_submissions s ON o.submission_id = s.id
        WHERE s.user_email = ?
    ''', (email,))
    outcomes = cursor.fetchall()

    total_validations = len(outcomes)

    if total_validations == 0:
        conn.close()
        return {
            'total_submissions': total_submissions,
            'total_validations': 0,
            'accuracy_rate': 0.0,
            'average_days_early': 0.0,
            'calibration_score': 0.0,
            'reputation_score': 0.0,
            'depth_level': 0.0
        }

    # Calculate metrics
    accuracy_scores = [o['accuracy_score'] for o in outcomes]
    outcome_results = [o['outcome_result'] for o in outcomes]
    days_early = [o['days_until_validation'] for o in outcomes]
    calibration_penalties = [o['calibration_penalty'] for o in outcomes]

    accuracy_rate = sum(outcome_results) / len(outcome_results)
    average_days_early = sum(days_early) / len(days_early)
    average_calibration = sum(calibration_penalties) / len(calibration_penalties)
    calibration_score = 1.0 - average_calibration  # Higher = better calibrated

    # Reputation score: weighted combination
    reputation_score = (
        accuracy_rate * 0.4 +           # 40% from accuracy
        calibration_score * 0.3 +       # 30% from calibration
        min(average_days_early / 365, 1.0) * 0.3  # 30% from being early
    )

    # Depth level: measure idea sophistication
    # (Would calculate from idea lineage depth in production)
    depth_level = min(total_submissions / 50.0, 1.0)  # Simple approximation

    conn.close()

    return {
        'total_submissions': total_submissions,
        'total_validations': total_validations,
        'accuracy_rate': accuracy_rate,
        'average_days_early': average_days_early,
        'calibration_score': calibration_score,
        'reputation_score': reputation_score,
        'depth_level': depth_level
    }


def update_user_accuracy(email: str) -> bool:
    """
    Update user_accuracy table with latest metrics
    Called after recording new outcome
    """
    metrics = calculate_user_accuracy(email)

    conn = get_db()
    cursor = conn.cursor()

    # Upsert user accuracy
    cursor.execute('''
        INSERT INTO user_accuracy (
            user_email,
            total_submissions,
            total_validations,
            accuracy_rate,
            average_days_early,
            calibration_score,
            reputation_score,
            depth_level,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_email) DO UPDATE SET
            total_submissions = excluded.total_submissions,
            total_validations = excluded.total_validations,
            accuracy_rate = excluded.accuracy_rate,
            average_days_early = excluded.average_days_early,
            calibration_score = excluded.calibration_score,
            reputation_score = excluded.reputation_score,
            depth_level = excluded.depth_level,
            updated_at = CURRENT_TIMESTAMP
    ''', (
        email,
        metrics['total_submissions'],
        metrics['total_validations'],
        metrics['accuracy_rate'],
        metrics['average_days_early'],
        metrics['calibration_score'],
        metrics['reputation_score'],
        metrics['depth_level']
    ))

    conn.commit()
    conn.close()

    print(f"✅ Updated accuracy for {email}:")
    print(f"   Accuracy: {metrics['accuracy_rate']:.1%}")
    print(f"   Reputation: {metrics['reputation_score']:.2f}")

    return True


def backpropagate_success(tracking_id: str) -> bool:
    """
    Backpropagate success through idea lineage

    When an idea is validated:
    1. Update user's accuracy metrics
    2. Propagate partial credit to parent ideas
    3. Generate new personalized question

    This is the core "backpropagation" logic!
    """
    conn = get_db()

    # Get submission
    submission = conn.execute('''
        SELECT * FROM idea_submissions WHERE tracking_id = ?
    ''', (tracking_id,)).fetchone()

    if not submission or not submission['user_email']:
        conn.close()
        return False

    email = submission['user_email']

    # Get outcome
    outcome = get_idea_outcome(tracking_id)

    if not outcome:
        conn.close()
        return False

    conn.close()

    # Update user's accuracy (main backprop step)
    update_user_accuracy(email)

    # Get parent ideas and give them partial credit
    parents = get_idea_parents(tracking_id)

    for parent in parents:
        # Parent gets 50% credit for child's success
        partial_result = outcome['outcome_result'] * 0.5

        # Record outcome for parent (if not already validated)
        existing = get_idea_outcome(parent['tracking_id'])
        if not existing:
            record_outcome(
                tracking_id=parent['tracking_id'],
                outcome_result=partial_result,
                validation_source=f"Derived from child idea {tracking_id}",
                validation_notes=f"Refinement led to validated idea"
            )

    print(f"✅ Backpropagated success from {tracking_id}")
    print(f"   Updated {email}'s reputation")
    print(f"   Credited {len(parents)} parent ideas")

    return True


# ==============================================================================
# TIME CAPSULE - Show Idea Evolution
# ==============================================================================

def get_time_capsule(email: str, days_back: int = 365) -> Dict:
    """
    Get user's idea time capsule

    Shows:
    - Ideas submitted in the past
    - Which ones were validated
    - Evolution chains (parent → child)
    - Accuracy over time

    Returns:
        {
            'ideas': [...],
            'validated': [...],
            'chains': [...],
            'accuracy_over_time': [...]
        }
    """
    conn = get_db()

    cutoff_date = datetime.now() - timedelta(days=days_back)

    # Get all ideas from this user
    ideas = conn.execute('''
        SELECT * FROM idea_submissions
        WHERE user_email = ? AND created_at >= ?
        ORDER BY created_at DESC
    ''', (email, cutoff_date)).fetchall()

    ideas_list = [dict(i) for i in ideas]

    # Get validated ideas
    validated = conn.execute('''
        SELECT s.tracking_id, s.idea_text, s.created_at, o.*
        FROM idea_outcomes o
        JOIN idea_submissions s ON o.submission_id = s.id
        WHERE s.user_email = ? AND s.created_at >= ?
        ORDER BY o.validated_at DESC
    ''', (email, cutoff_date)).fetchall()

    validated_list = [dict(v) for v in validated]

    conn.close()

    # Build evolution chains
    chains = []
    for idea in ideas_list:
        lineage = get_idea_lineage_tree(idea['tracking_id'])
        if lineage and (lineage['parents'] or lineage['children']):
            chains.append(lineage)

    return {
        'ideas': ideas_list,
        'validated': validated_list,
        'chains': chains,
        'days_back': days_back,
        'user_email': email
    }


# ==============================================================================
# GENERATE NEXT QUESTION - Coach Mode
# ==============================================================================

def generate_next_question(email: str) -> str:
    """
    Generate personalized next question based on user's pattern

    Analyzes:
    - User's depth level (surface vs deep thinking)
    - Recent idea topics
    - Validation history
    - Refinement patterns

    Returns:
        Personalized question to push thinking forward
    """
    metrics = calculate_user_accuracy(email)
    depth_level = metrics['depth_level']

    conn = get_db()

    # Get recent ideas
    recent = conn.execute('''
        SELECT * FROM idea_submissions
        WHERE user_email = ?
        ORDER BY created_at DESC
        LIMIT 5
    ''', (email,)).fetchall()

    conn.close()

    if not recent:
        return "What problem are you most curious about right now?"

    # Analyze depth progression
    if depth_level < 0.3:
        # Surface level - push for specifics
        questions = [
            "You've shared some interesting thoughts. How would you implement one of them?",
            "What specific problem does your latest idea solve?",
            "Can you describe the technical details of your idea?",
            "What would the first prototype look like?"
        ]
    elif depth_level < 0.6:
        # Medium depth - push for broader implications
        questions = [
            "What are the second-order effects of your idea?",
            "Who would be threatened by this working?",
            "What needs to be true for this to succeed at scale?",
            "What would the world look like if this became mainstream?"
        ]
    else:
        # Deep thinker - push for novel connections
        questions = [
            "What seemingly unrelated field could inform this idea?",
            "What would be the contrarian take on your approach?",
            "How would you prove this wrong?",
            "What's the most radical version of this idea?"
        ]

    import random
    return random.choice(questions)


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Idea Backpropagation System')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--link', nargs=3, metavar=('PARENT', 'CHILD', 'TYPE'), help='Link ideas')
    parser.add_argument('--validate', nargs=2, metavar=('TRACKING_ID', 'RESULT'), help='Record validation')
    parser.add_argument('--backprop', metavar='TRACKING_ID', help='Backpropagate success')
    parser.add_argument('--capsule', metavar='EMAIL', help='Show time capsule')
    parser.add_argument('--accuracy', metavar='EMAIL', help='Show accuracy metrics')

    args = parser.parse_args()

    if args.init:
        create_backpropagation_tables()

    elif args.link:
        parent, child, refinement_type = args.link
        link_ideas(parent, child, refinement_type)

    elif args.validate:
        tracking_id, result = args.validate
        record_outcome(tracking_id, float(result))

    elif args.backprop:
        backpropagate_success(args.backprop)

    elif args.capsule:
        capsule = get_time_capsule(args.capsule)
        print(json.dumps(capsule, indent=2, default=str))

    elif args.accuracy:
        metrics = calculate_user_accuracy(args.accuracy)
        print(json.dumps(metrics, indent=2))

    else:
        print("Idea Backpropagation System")
        print()
        print("Usage:")
        print("  --init                          Initialize database")
        print("  --link PARENT CHILD TYPE        Link two ideas")
        print("  --validate ID RESULT            Record validation (0.0-1.0)")
        print("  --backprop ID                   Backpropagate success")
        print("  --capsule EMAIL                 Show time capsule")
        print("  --accuracy EMAIL                Show accuracy metrics")

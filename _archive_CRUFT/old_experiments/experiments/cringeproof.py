#!/usr/bin/env python3
"""
Cringeproof - Self-Awareness Game

A game that helps you understand your level of self-awareness and social anxiety.
Answer 7 questions honestly and get AI-powered insights.

Questions cover:
- Self-monitoring behavior
- Social media anxiety
- Conversation rehearsal
- Message overthinking
- Past embarrassment
- Self-analysis patterns
- Validation seeking

Scoring:
- 7-14: Low self-awareness / Very relaxed
- 15-21: Moderate self-awareness
- 22-28: High self-awareness / Some anxiety
- 29-35: Very high self-awareness / Significant anxiety
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
import json


# =============================================================================
# QUESTION BANK
# =============================================================================

CRINGEPROOF_QUESTIONS = [
    {
        'id': 1,
        'text': 'I triple-check my texts before sending them',
        'category': 'communication_anxiety',
        'weight': 1.0
    },
    {
        'id': 2,
        'text': 'I worry about what people think of my social media posts',
        'category': 'social_anxiety',
        'weight': 1.0
    },
    {
        'id': 3,
        'text': 'I rehearse conversations in my head before having them',
        'category': 'preparation_anxiety',
        'weight': 1.0
    },
    {
        'id': 4,
        'text': 'I delete and rewrite messages multiple times',
        'category': 'communication_anxiety',
        'weight': 1.2  # Weighted higher - strong indicator
    },
    {
        'id': 5,
        'text': 'I feel embarrassed thinking about past interactions',
        'category': 'retrospective_anxiety',
        'weight': 1.0
    },
    {
        'id': 6,
        'text': 'I analyze my own behavior constantly',
        'category': 'self_monitoring',
        'weight': 1.1
    },
    {
        'id': 7,
        'text': 'I seek validation from others frequently',
        'category': 'validation_seeking',
        'weight': 1.0
    }
]


# =============================================================================
# SCORING & ANALYSIS
# =============================================================================

def calculate_score(responses: Dict[int, int]) -> Dict[str, Any]:
    """
    Calculate cringeproof score and provide analysis

    Args:
        responses: Dict mapping question_id → rating (1-5)

    Returns:
        Dict with score, analysis, and recommendations
    """
    # Calculate weighted score
    total_score = 0
    max_score = 0

    for question in CRINGEPROOF_QUESTIONS:
        qid = question['id']
        weight = question['weight']

        if qid in responses:
            total_score += responses[qid] * weight
            max_score += 5 * weight

    # Normalize to percentage
    percentage = (total_score / max_score * 100) if max_score > 0 else 0

    # Determine level
    if total_score <= 14:
        level = "Low Self-Awareness"
        description = "You're pretty relaxed about social interactions!"
        color = "#4ECDC4"  # Teal
    elif total_score <= 21:
        level = "Moderate Self-Awareness"
        description = "You have a healthy balance of self-awareness."
        color = "#FFE66D"  # Yellow
    elif total_score <= 28:
        level = "High Self-Awareness"
        description = "You're very conscious of how you come across."
        color = "#FFA07A"  # Light orange
    else:
        level = "Very High Self-Awareness"
        description = "You might be overthinking social interactions."
        color = "#FF6B6B"  # Red

    # Category breakdown
    category_scores = {}
    for category in ['communication_anxiety', 'social_anxiety', 'preparation_anxiety',
                     'retrospective_anxiety', 'self_monitoring', 'validation_seeking']:
        questions_in_category = [q for q in CRINGEPROOF_QUESTIONS if q['category'] == category]
        if questions_in_category:
            category_total = sum(responses.get(q['id'], 0) for q in questions_in_category)
            category_max = len(questions_in_category) * 5
            category_scores[category] = (category_total / category_max * 100) if category_max > 0 else 0

    return {
        'total_score': round(total_score, 1),
        'max_score': round(max_score, 1),
        'percentage': round(percentage, 1),
        'level': level,
        'description': description,
        'color': color,
        'category_scores': category_scores,
        'responses': responses
    }


def generate_insights(score_data: Dict[str, Any]) -> List[str]:
    """Generate personalized insights based on score"""
    insights = []

    percentage = score_data['percentage']
    category_scores = score_data['category_scores']

    # Overall insights
    if percentage >= 80:
        insights.append("💭 You're highly self-aware, which is great! But make sure you're not overthinking every interaction.")
    elif percentage >= 60:
        insights.append("✨ You have good self-awareness. You notice social cues without obsessing over them.")
    elif percentage >= 40:
        insights.append("🌟 You're pretty relaxed in social situations. This can be a superpower!")
    else:
        insights.append("😎 You're very confident and don't worry much about social perceptions. Rock on!")

    # Category-specific insights
    if category_scores.get('communication_anxiety', 0) > 70:
        insights.append("📱 You might be overthinking your messages. Try the 'send it and forget it' approach sometimes!")

    if category_scores.get('social_anxiety', 0) > 70:
        insights.append("📸 Social media anxiety detected. Remember: most people are too busy worrying about themselves to judge you!")

    if category_scores.get('preparation_anxiety', 0) > 70:
        insights.append("🎭 You rehearse conversations a lot. Sometimes spontaneity leads to the best interactions!")

    if category_scores.get('retrospective_anxiety', 0) > 70:
        insights.append("⏰ You dwell on past interactions. Everyone has awkward moments - they're part of being human!")

    if category_scores.get('validation_seeking', 0) > 70:
        insights.append("💖 You seek external validation often. Try building confidence from within!")

    # Add positive reinforcement
    if percentage < 50:
        insights.append("✅ Your low anxiety about social interactions is a strength. People probably find you easy to talk to!")

    return insights


def generate_recommendations(score_data: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations"""
    recommendations = []

    percentage = score_data['percentage']

    if percentage >= 75:
        recommendations.extend([
            "Practice 'good enough' instead of perfect in your communications",
            "Set a time limit for crafting messages (30 seconds max!)",
            "Try one spontaneous conversation per day without rehearsing"
        ])
    elif percentage >= 50:
        recommendations.extend([
            "Notice when you're overthinking and consciously let it go",
            "Celebrate your self-awareness as a positive trait",
            "Balance reflection with action"
        ])
    else:
        recommendations.extend([
            "Your relaxed approach is great! Maintain that confidence",
            "Use your ease in social situations to help others feel comfortable",
            "Stay authentic - it's working for you"
        ])

    return recommendations


# =============================================================================
# GAME DATA MANAGEMENT
# =============================================================================

def save_game_result(user_id: int, score_data: Dict[str, Any]) -> int:
    """
    Save game result to database

    Args:
        user_id: User ID (or None for anonymous)
        score_data: Score calculation result

    Returns:
        Game result ID
    """
    from database import get_db

    db = get_db()

    # Create game_results table if it doesn't exist
    db.execute('''
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_type TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL NOT NULL,
            percentage REAL NOT NULL,
            level TEXT NOT NULL,
            result_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor = db.execute('''
        INSERT INTO game_results (user_id, game_type, score, max_score, percentage, level, result_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        'cringeproof',
        score_data['total_score'],
        score_data['max_score'],
        score_data['percentage'],
        score_data['level'],
        json.dumps(score_data)
    ))

    db.commit()
    return cursor.lastrowid


def get_game_result(result_id: int) -> Dict[str, Any]:
    """Get game result by ID"""
    from database import get_db

    db = get_db()
    row = db.execute('SELECT * FROM game_results WHERE id = ?', (result_id,)).fetchone()

    if not row:
        return None

    result = dict(row)
    result['result_data'] = json.loads(result['result_data'])
    return result


def get_user_history(user_id: int, game_type: str = 'cringeproof', limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's game history"""
    from database import get_db

    db = get_db()
    rows = db.execute('''
        SELECT * FROM game_results
        WHERE user_id = ? AND game_type = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, game_type, limit)).fetchall()

    results = []
    for row in rows:
        result = dict(row)
        result['result_data'] = json.loads(result['result_data'])
        results.append(result)

    return results


# =============================================================================
# STATISTICS
# =============================================================================

def get_global_stats(game_type: str = 'cringeproof') -> Dict[str, Any]:
    """Get global statistics for the game"""
    from database import get_db

    db = get_db()

    # Total games played
    total = db.execute(
        'SELECT COUNT(*) FROM game_results WHERE game_type = ?',
        (game_type,)
    ).fetchone()[0]

    if total == 0:
        return {'total_games': 0}

    # Average score
    avg_score = db.execute(
        'SELECT AVG(percentage) FROM game_results WHERE game_type = ?',
        (game_type,)
    ).fetchone()[0]

    # Distribution by level
    distribution = db.execute('''
        SELECT level, COUNT(*) as count
        FROM game_results
        WHERE game_type = ?
        GROUP BY level
        ORDER BY count DESC
    ''', (game_type,)).fetchall()

    level_distribution = {row[0]: row[1] for row in distribution}

    return {
        'total_games': total,
        'average_score': round(avg_score, 1) if avg_score else 0,
        'level_distribution': level_distribution
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    print("🎮 Cringeproof Game - Self-Awareness Quiz\n")

    print("=" * 70)
    print("QUESTIONS")
    print("=" * 70)
    for q in CRINGEPROOF_QUESTIONS:
        print(f"{q['id']}. {q['text']}")
        print(f"   Category: {q['category']}, Weight: {q['weight']}")
        print()

    print("=" * 70)
    print("TEST RUN")
    print("=" * 70)

    # Simulate high self-awareness responses
    test_responses = {
        1: 5,  # Triple-check texts
        2: 4,  # Social media worry
        3: 5,  # Rehearse conversations
        4: 5,  # Delete/rewrite messages
        5: 3,  # Past embarrassment
        6: 4,  # Self-analysis
        7: 4   # Validation seeking
    }

    print("Test responses (high self-awareness):")
    print(test_responses)
    print()

    score_data = calculate_score(test_responses)
    print(f"Score: {score_data['total_score']}/{score_data['max_score']} ({score_data['percentage']}%)")
    print(f"Level: {score_data['level']}")
    print(f"Description: {score_data['description']}")
    print()

    print("Category Breakdown:")
    for category, score in score_data['category_scores'].items():
        print(f"  {category}: {score:.0f}%")
    print()

    print("Insights:")
    for insight in generate_insights(score_data):
        print(f"  • {insight}")
    print()

    print("Recommendations:")
    for rec in generate_recommendations(score_data):
        print(f"  ✓ {rec}")

    print("\n✅ Cringeproof game logic working!")

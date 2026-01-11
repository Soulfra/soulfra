#!/usr/bin/env python3
"""
Game Sharing & Peer Review System

Connects:
- Games (cringeproof, color challenges, etc.)
- Peer reviews (friends give feedback)
- Neural networks (AI analyzes feedback)
- Templates (generate reports/emails)
- Neural hub (route results to channels)

Philosophy:
----------
External services charge for analytics and insights.
We generate them ourselves using:
- Peer feedback from friends/colleagues
- Neural network analysis
- Automated report generation
- Multi-channel distribution

Usage:
    # Share a game
    from game_sharing import create_game_share
    share_id, code = create_game_share(
        game_type='cringeproof',
        game_data={'answers': [...], 'score': 75},
        sender_email='user@example.com',
        recipient_email='friend@example.com',
        message='Can you review my answers?'
    )

    # Submit a review
    from game_sharing import submit_game_review
    review_id = submit_game_review(
        share_code='abc123',
        reviewer_email='friend@example.com',
        review_data={'ratings': {...}, 'comments': '...'}
    )

    # Get AI analysis
    from game_sharing import analyze_game_review
    analysis = analyze_game_review(review_id)
"""

import sqlite3
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any


# ==============================================================================
# DATABASE CONNECTION
# ==============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# GAME SHARING
# ==============================================================================

def generate_share_code() -> str:
    """Generate unique share code"""
    return secrets.token_urlsafe(8)  # e.g., 'abc123XY'


def create_game_share(
    game_type: str,
    game_data: Dict[str, Any],
    recipient_email: str,
    sender_user_id: Optional[int] = None,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    message: Optional[str] = None,
    expires_in_days: int = 30
) -> Tuple[int, str]:
    """
    Create a shareable game link

    Args:
        game_type: Type of game ('cringeproof', 'color_challenge', etc.)
        game_data: JSON-serializable game data (answers, scores, etc.)
        recipient_email: Who to send it to
        sender_user_id: Sender's user ID (if logged in)
        sender_name: Sender's name (if not logged in)
        sender_email: Sender's email (if not logged in)
        message: Personal message to recipient
        expires_in_days: Days until link expires

    Returns:
        Tuple of (share_id, share_code)
    """
    conn = get_db()
    cursor = conn.cursor()

    share_code = generate_share_code()
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    cursor.execute('''
        INSERT INTO game_shares
        (sender_user_id, sender_name, sender_email, recipient_email,
         game_type, game_data, share_code, message, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        sender_user_id,
        sender_name,
        sender_email,
        recipient_email,
        game_type,
        json.dumps(game_data),
        share_code,
        message,
        expires_at.isoformat()
    ))

    share_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return share_id, share_code


def get_game_share(share_code: str) -> Optional[Dict]:
    """
    Get game share by code

    Returns:
        Game share dict or None if not found/expired
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM game_shares
        WHERE share_code = ?
    ''', (share_code,))

    share = cursor.fetchone()

    if not share:
        conn.close()
        return None

    share_dict = dict(share)

    # Check if expired
    if share_dict.get('expires_at'):
        expires_at = datetime.fromisoformat(share_dict['expires_at'])
        if expires_at < datetime.now(timezone.utc):
            share_dict['status'] = 'expired'

    # Increment view count
    cursor.execute('''
        UPDATE game_shares
        SET view_count = view_count + 1
        WHERE id = ?
    ''', (share_dict['id'],))

    conn.commit()
    conn.close()

    # Parse JSON fields
    share_dict['game_data'] = json.loads(share_dict['game_data'])

    return share_dict


# ==============================================================================
# GAME REVIEWS
# ==============================================================================

def submit_game_review(
    share_code: str,
    review_data: Dict[str, Any],
    reviewer_email: str,
    reviewer_user_id: Optional[int] = None,
    reviewer_name: Optional[str] = None,
    review_type: str = 'peer',
    is_anonymous: bool = False,
    overall_rating: Optional[int] = None
) -> Optional[int]:
    """
    Submit a review for a shared game

    Args:
        share_code: Unique share code
        review_data: JSON-serializable review data (ratings, comments, etc.)
        reviewer_email: Reviewer's email
        reviewer_user_id: Reviewer's user ID (if logged in)
        reviewer_name: Reviewer's name (if not logged in)
        review_type: 'peer', 'reference', 'mentor', or 'self'
        is_anonymous: Hide reviewer identity from sender
        overall_rating: 1-5 rating

    Returns:
        review_id or None if share not found
    """
    # Get the share
    share = get_game_share(share_code)
    if not share:
        return None

    # Check if expired
    if share['status'] == 'expired':
        return None

    conn = get_db()
    cursor = conn.cursor()

    # Create review
    cursor.execute('''
        INSERT INTO game_reviews
        (game_share_id, reviewer_user_id, reviewer_name, reviewer_email,
         review_data, review_type, is_anonymous, overall_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        share['id'],
        reviewer_user_id,
        reviewer_name,
        reviewer_email,
        json.dumps(review_data),
        review_type,
        is_anonymous,
        overall_rating
    ))

    review_id = cursor.lastrowid

    # Update share status and counts
    cursor.execute('''
        UPDATE game_shares
        SET status = 'reviewed',
            review_count = review_count + 1,
            reviewed_at = ?
        WHERE id = ?
    ''', (datetime.now(timezone.utc).isoformat(), share['id']))

    conn.commit()
    conn.close()

    return review_id


def get_review(review_id: int) -> Optional[Dict]:
    """Get review by ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM game_reviews WHERE id = ?', (review_id,))
    review = cursor.fetchone()
    conn.close()

    if not review:
        return None

    review_dict = dict(review)
    review_dict['review_data'] = json.loads(review_dict['review_data'])
    if review_dict.get('neural_classification'):
        review_dict['neural_classification'] = json.loads(review_dict['neural_classification'])

    return review_dict


def get_reviews_for_share(share_id: int) -> List[Dict]:
    """Get all reviews for a game share"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM game_reviews
        WHERE game_share_id = ?
        ORDER BY created_at DESC
    ''', (share_id,))

    reviews = []
    for row in cursor.fetchall():
        review_dict = dict(row)
        review_dict['review_data'] = json.loads(review_dict['review_data'])
        if review_dict.get('neural_classification'):
            review_dict['neural_classification'] = json.loads(review_dict['neural_classification'])
        reviews.append(review_dict)

    conn.close()
    return reviews


# ==============================================================================
# NEURAL NETWORK ANALYSIS
# ==============================================================================

def analyze_game_review(review_id: int) -> Dict[str, Any]:
    """
    Analyze a game review using neural networks

    Uses:
    - CalRiven: Technical feedback quality
    - TheAuditor: Validation thoroughness
    - Soulfra: Overall helpfulness

    Returns:
        Dict with classifications, insights, and action items
    """
    from neural_hub import classify_message
    from neural_network import load_neural_network

    # Get the review
    review = get_review(review_id)
    if not review:
        return {'error': 'Review not found'}

    # Get the original game share
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM game_shares WHERE id = ?', (review['game_share_id'],))
    share = dict(cursor.fetchone())
    share['game_data'] = json.loads(share['game_data'])
    conn.close()

    # Prepare content for classification
    review_text = f"Game: {share['game_type']}\n"
    review_text += f"Review type: {review['review_type']}\n"
    review_text += f"Overall rating: {review['overall_rating']}/5\n"
    review_text += f"Review data: {json.dumps(review['review_data'])}"

    # Classify using neural networks
    classifications = classify_message(review_text)

    # Calculate helpfulness score
    helpfulness_score = 0.0
    if classifications:
        # Average confidence scores
        helpfulness_score = sum(c.confidence for c in classifications) / len(classifications)

    # Update review with neural classification
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE game_reviews
        SET neural_classification = ?,
            helpfulness_score = ?
        WHERE id = ?
    ''', (
        json.dumps([{
            'network_name': c.network_name,
            'score': c.score,
            'label': c.label,
            'confidence': c.confidence
        } for c in classifications]),
        helpfulness_score,
        review_id
    ))
    conn.commit()
    conn.close()

    # Generate insights
    insights = {
        'classifications': classifications,
        'helpfulness_score': helpfulness_score,
        'analysis_type': 'peer_review',
        'recommendations': []
    }

    # Add recommendations based on classifications
    for classification in classifications:
        if classification.network_name == 'calriven_technical_classifier' and classification.confidence > 0.7:
            if classification.label == 'technical':
                insights['recommendations'].append('Technical feedback detected - share in dev channels')

        if classification.network_name == 'theauditor_validation_classifier' and classification.confidence > 0.7:
            if classification.label == 'validated':
                insights['recommendations'].append('Thorough validation - consider featuring this review')

    return insights


# ==============================================================================
# ANALYTICS
# ==============================================================================

def get_share_stats() -> Dict[str, Any]:
    """Get game sharing statistics"""
    conn = get_db()
    cursor = conn.cursor()

    # Total shares
    cursor.execute('SELECT COUNT(*) FROM game_shares')
    total_shares = cursor.fetchone()[0]

    # By game type
    cursor.execute('''
        SELECT game_type, COUNT(*) as count
        FROM game_shares
        GROUP BY game_type
        ORDER BY count DESC
    ''')
    by_game_type = {row[0]: row[1] for row in cursor.fetchall()}

    # Completion rate
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) as reviewed
        FROM game_shares
    ''')
    row = cursor.fetchone()
    completion_rate = (row[1] / row[0] * 100) if row[0] > 0 else 0

    # Average review helpfulness
    cursor.execute('SELECT AVG(helpfulness_score) FROM game_reviews WHERE helpfulness_score IS NOT NULL')
    avg_helpfulness = cursor.fetchone()[0] or 0.0

    conn.close()

    return {
        'total_shares': total_shares,
        'by_game_type': by_game_type,
        'completion_rate': completion_rate,
        'avg_helpfulness': avg_helpfulness
    }


# ==============================================================================
# INTEGRATION WITH NEURAL HUB
# ==============================================================================

def route_review_to_hub(review_id: int):
    """
    Route completed review through neural hub

    This sends the review to appropriate channels based on
    neural network classification
    """
    from neural_hub import process_message

    review = get_review(review_id)
    if not review:
        return

    # Get share info
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM game_shares WHERE id = ?', (review['game_share_id'],))
    share = dict(cursor.fetchone())
    conn.close()

    # Prepare message
    content = f"Peer review completed for {share['game_type']} game"
    if review.get('overall_rating'):
        content += f" - Rating: {review['overall_rating']}/5"

    metadata = {
        'game_share_id': share['id'],
        'review_id': review_id,
        'game_type': share['game_type'],
        'helpfulness_score': review.get('helpfulness_score'),
        'reviewer_email': review['reviewer_email']
    }

    # Route through hub
    result = process_message(
        content=content,
        source='game_review',
        metadata=metadata
    )

    return result


# ==============================================================================
# CLI & TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🎮 Game Sharing System\n")

    # Create a test share
    print("Creating test game share...")
    share_id, code = create_game_share(
        game_type='cringeproof',
        game_data={'answers': [1, 2, 3], 'score': 75},
        sender_email='test@example.com',
        sender_name='Test User',
        recipient_email='friend@example.com',
        message='Can you review my cringeproof answers?'
    )

    print(f"✅ Created share #{share_id} with code: {code}")
    print(f"Share link: https://cringeproof.com/review/{code}")

    # Get the share
    share = get_game_share(code)
    print(f"\n📋 Share details:")
    print(f"  Game type: {share['game_type']}")
    print(f"  Status: {share['status']}")
    print(f"  Views: {share['view_count']}")

    # Submit a test review
    print("\nSubmitting test review...")
    review_id = submit_game_review(
        share_code=code,
        review_data={
            'ratings': {'self_awareness': 4, 'honesty': 5},
            'comments': 'Great self-reflection!'
        },
        reviewer_email='friend@example.com',
        reviewer_name='Friend',
        overall_rating=4
    )

    print(f"✅ Review submitted with ID: {review_id}")

    # Analyze the review
    print("\nAnalyzing review with neural networks...")
    analysis = analyze_game_review(review_id)
    print(f"Helpfulness score: {analysis['helpfulness_score']:.2f}")
    print(f"Classifications: {len(analysis['classifications'])}")
    print(f"Recommendations: {analysis['recommendations']}")

    # Get stats
    print("\n📊 Statistics:")
    stats = get_share_stats()
    print(f"Total shares: {stats['total_shares']}")
    print(f"Completion rate: {stats['completion_rate']:.1f}%")
    print(f"Avg helpfulness: {stats['avg_helpfulness']:.2f}")

    print("\n✅ Game sharing system working!")

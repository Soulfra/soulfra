#!/usr/bin/env python3
"""
Bidirectional Review Engine - Airbnb-Style Mutual Reviews

Implements 2-sided review system where both parties must review each other
before either review is published.

**The Airbnb Model:**
1. Guest leaves review of Host → Hidden until Host reviews Guest
2. Host leaves review of Guest → Hidden until Guest reviews Host
3. After both submit (or 14-day deadline) → Both reviews published simultaneously
4. Prevents gaming: Can't see what other person wrote before submitting yours

**Applied to Comment Chains:**
1. User A posts comment with voice/text (chain_hash created)
2. User B wants to reply → Must:
   a. Connect GitHub
   b. Star repo (github_star_validator.py)
   c. Leave review of User A's comment
3. User A gets notification → Must review User B's interaction
4. After both reviews submitted → Both published + User B can post reply

**Database:**
Uses existing game_reviews table with new columns:
- requires_reciprocal BOOLEAN
- reciprocal_review_id INTEGER (links to partner review)
- comment_id INTEGER (links to comment being reviewed)
- chain_hash TEXT (links to comment chain)

**Flow Example:**
```
User A posts: "Check out this idea!"
  ↓ (creates comment_id=123, chain_hash=abc)

User B clicks reply:
  ↓ Redirect to GitHub OAuth
  ↓ Verify starred repo
  ↓ Show review form for User A's comment

User B submits review:
  {
    "comment_id": 123,
    "rating": 5,
    "feedback": "Great idea!",
    "reviewer": "@octocat"
  }
  ↓ Creates review_id=1 (status=pending_reciprocal)

User A gets notification:
  "Please review @octocat's interaction to see their feedback"

User A submits review:
  {
    "review_id": 1,  // User B's review
    "rating": 4,
    "feedback": "Thoughtful response"
  }
  ↓ Creates review_id=2 (reciprocal_review_id=1)
  ↓ Updates review_id=1 (reciprocal_review_id=2)
  ↓ PUBLISH BOTH REVIEWS

Both users see:
  ✅ User B's review of User A
  ✅ User A's review of User B
  ✅ User B can now post reply comment
```

**Usage:**
```python
from bidirectional_review_engine import BidirectionalReviews

engine = BidirectionalReviews()

# User B submits review
review = engine.create_review(
    comment_id=123,
    reviewer_github='octocat',
    rating=5,
    feedback='Great post!'
)
# Returns: {'review_id': 1, 'status': 'pending_reciprocal'}

# User A submits reciprocal
reciprocal = engine.create_reciprocal_review(
    original_review_id=1,
    rating=4,
    feedback='Thanks!'
)
# Returns: {'both_published': True, 'can_reply': True}
```

**API Endpoints:**
- POST /api/review/create
- POST /api/review/reciprocal
- GET /api/review/pending
- GET /api/review/status/<review_id>
"""

from flask import Blueprint, request, jsonify, g
from database import get_db
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

bidirectional_review_bp = Blueprint('bidirectional_review', __name__)


class BidirectionalReviews:
    """
    Manage Airbnb-style bidirectional review system
    """

    REVIEW_DEADLINE_DAYS = 14  # Days before auto-publishing unpaired review


    # ==========================================================================
    # CREATE REVIEWS
    # ==========================================================================

    def create_review(self, comment_id: int, reviewer_github: str,
                     rating: int, feedback: str, review_data: Optional[Dict] = None) -> Dict:
        """
        Create initial review (triggers reciprocal requirement)

        Args:
            comment_id: Comment being reviewed
            reviewer_github: GitHub username of reviewer
            rating: 1-5 star rating
            feedback: Text feedback
            review_data: Optional additional data (JSON)

        Returns:
            Dict with review_id and status

        Example:
            >>> engine = BidirectionalReviews()
            >>> review = engine.create_review(
            ...     comment_id=123,
            ...     reviewer_github='octocat',
            ...     rating=5,
            ...     feedback='Great post!'
            ... )
            >>> print(review['status'])
            pending_reciprocal
        """
        db = get_db()

        # Get comment details
        comment = db.execute('''
            SELECT id, user_id, chain_hash FROM comments WHERE id = ?
        ''', (comment_id,)).fetchone()

        if not comment:
            db.close()
            raise ValueError(f'Comment {comment_id} not found')

        # Get reviewer user_id from api_keys table
        reviewer_row = db.execute('''
            SELECT user_id FROM api_keys WHERE github_username = ?
        ''', (reviewer_github,)).fetchone()

        reviewer_user_id = reviewer_row[0] if reviewer_row else None

        # Prepare review data
        if review_data is None:
            review_data = {}

        review_data.update({
            'rating': rating,
            'feedback': feedback,
            'review_type': 'peer'
        })

        # Create review (hidden until reciprocal)
        cursor = db.execute('''
            INSERT INTO game_reviews (
                game_share_id,
                reviewer_user_id,
                reviewer_name,
                review_data,
                review_type,
                overall_rating,
                comment_id,
                chain_hash,
                github_username,
                requires_reciprocal,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            0,  # game_share_id (not used for comments)
            reviewer_user_id,
            reviewer_github,
            json.dumps(review_data),
            'peer',
            rating,
            comment_id,
            comment['chain_hash'],
            reviewer_github,
            1,  # requires_reciprocal=True
            datetime.now()
        ))

        review_id = cursor.lastrowid
        db.commit()

        # Notify comment author
        self._notify_reciprocal_required(
            comment_author_id=comment['user_id'],
            reviewer_github=reviewer_github,
            review_id=review_id
        )

        db.close()

        return {
            'review_id': review_id,
            'status': 'pending_reciprocal',
            'message': f'Review submitted! Waiting for @{reviewer_github} to be reviewed by comment author.',
            'deadline': (datetime.now() + timedelta(days=self.REVIEW_DEADLINE_DAYS)).isoformat()
        }


    def create_reciprocal_review(self, original_review_id: int,
                                 rating: int, feedback: str,
                                 review_data: Optional[Dict] = None) -> Dict:
        """
        Create reciprocal review (completes the pair, publishes both)

        Args:
            original_review_id: Review being reciprocated
            rating: 1-5 star rating
            feedback: Text feedback
            review_data: Optional additional data

        Returns:
            Dict with both_published status

        Example:
            >>> engine = BidirectionalReviews()
            >>> result = engine.create_reciprocal_review(
            ...     original_review_id=1,
            ...     rating=4,
            ...     feedback='Thanks for the review!'
            ... )
            >>> print(result['both_published'])
            True
        """
        db = get_db()

        # Get original review
        original = db.execute('''
            SELECT id, comment_id, reviewer_user_id, reviewer_name, github_username, chain_hash
            FROM game_reviews WHERE id = ?
        ''', (original_review_id,)).fetchone()

        if not original:
            db.close()
            raise ValueError(f'Review {original_review_id} not found')

        # Get comment author (person writing reciprocal)
        comment = db.execute('''
            SELECT user_id FROM comments WHERE id = ?
        ''', (original['comment_id'],)).fetchone()

        if not comment:
            db.close()
            raise ValueError(f'Comment {original["comment_id"]} not found')

        comment_author_id = comment['user_id']

        # Get comment author's GitHub username
        author_github_row = db.execute('''
            SELECT github_username FROM api_keys WHERE user_id = ?
        ''', (comment_author_id,)).fetchone()

        author_github = author_github_row[0] if author_github_row else f'user_{comment_author_id}'

        # Prepare review data
        if review_data is None:
            review_data = {}

        review_data.update({
            'rating': rating,
            'feedback': feedback,
            'review_type': 'reciprocal'
        })

        # Create reciprocal review
        cursor = db.execute('''
            INSERT INTO game_reviews (
                game_share_id,
                reviewer_user_id,
                reviewer_name,
                review_data,
                review_type,
                overall_rating,
                comment_id,
                chain_hash,
                github_username,
                requires_reciprocal,
                reciprocal_review_id,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            0,
            comment_author_id,
            author_github,
            json.dumps(review_data),
            'reciprocal',
            rating,
            original['comment_id'],
            original['chain_hash'],
            author_github,
            0,  # requires_reciprocal=False (this completes the pair)
            original_review_id,
            datetime.now()
        ))

        reciprocal_review_id = cursor.lastrowid

        # Link original review to reciprocal
        db.execute('''
            UPDATE game_reviews
            SET reciprocal_review_id = ?,
                requires_reciprocal = 0
            WHERE id = ?
        ''', (reciprocal_review_id, original_review_id))

        db.commit()

        # Notify both parties
        self._notify_both_published(original_review_id, reciprocal_review_id)

        db.close()

        return {
            'reciprocal_review_id': reciprocal_review_id,
            'original_review_id': original_review_id,
            'both_published': True,
            'message': 'Both reviews published!',
            'can_reply': True  # Reviewer can now post comment reply
        }


    # ==========================================================================
    # QUERY REVIEWS
    # ==========================================================================

    def get_pending_reciprocals(self, user_id: int) -> List[Dict]:
        """
        Get reviews waiting for this user to reciprocate

        Args:
            user_id: User ID to check

        Returns:
            List of reviews waiting for reciprocal

        Example:
            >>> engine = BidirectionalReviews()
            >>> pending = engine.get_pending_reciprocals(user_id=15)
            >>> for review in pending:
            ...     print(f"Review from @{review['reviewer_name']}")
        """
        db = get_db()

        # Get comments authored by this user
        user_comment_ids = db.execute('''
            SELECT id FROM comments WHERE user_id = ?
        ''', (user_id,)).fetchall()

        comment_ids = [row[0] for row in user_comment_ids]

        if not comment_ids:
            db.close()
            return []

        # Get reviews on those comments that need reciprocal
        placeholders = ','.join('?' * len(comment_ids))
        pending_reviews = db.execute(f'''
            SELECT
                r.id,
                r.comment_id,
                r.reviewer_name,
                r.github_username,
                r.overall_rating,
                r.created_at,
                c.content as comment_content
            FROM game_reviews r
            JOIN comments c ON r.comment_id = c.id
            WHERE r.comment_id IN ({placeholders})
              AND r.requires_reciprocal = 1
              AND r.reciprocal_review_id IS NULL
            ORDER BY r.created_at DESC
        ''', comment_ids).fetchall()

        db.close()

        return [dict(row) for row in pending_reviews]


    def get_review_status(self, review_id: int) -> Dict:
        """
        Get status of a review (pending, published, expired)

        Args:
            review_id: Review ID

        Returns:
            Dict with review status and details

        Example:
            >>> engine = BidirectionalReviews()
            >>> status = engine.get_review_status(review_id=1)
            >>> print(status['status'])
            pending_reciprocal
        """
        db = get_db()

        review = db.execute('''
            SELECT
                id,
                comment_id,
                reviewer_name,
                github_username,
                overall_rating,
                requires_reciprocal,
                reciprocal_review_id,
                created_at
            FROM game_reviews
            WHERE id = ?
        ''', (review_id,)).fetchone()

        if not review:
            db.close()
            return {'error': 'Review not found'}

        review_dict = dict(review)

        # Determine status
        if review_dict['reciprocal_review_id']:
            status = 'published'
            message = 'Both reviews published'
        elif review_dict['requires_reciprocal']:
            created_at = datetime.fromisoformat(review_dict['created_at'])
            deadline = created_at + timedelta(days=self.REVIEW_DEADLINE_DAYS)

            if datetime.now() > deadline:
                status = 'expired'
                message = 'Reciprocal deadline passed, auto-published'
            else:
                status = 'pending_reciprocal'
                days_left = (deadline - datetime.now()).days
                message = f'Waiting for reciprocal review ({days_left} days left)'
        else:
            status = 'published'
            message = 'Review published'

        db.close()

        return {
            'review_id': review_id,
            'status': status,
            'message': message,
            **review_dict
        }


    # ==========================================================================
    # NOTIFICATIONS
    # ==========================================================================

    def _notify_reciprocal_required(self, comment_author_id: int,
                                   reviewer_github: str, review_id: int) -> None:
        """
        Notify comment author they need to review the reviewer

        Args:
            comment_author_id: User ID of comment author
            reviewer_github: GitHub username who left review
            review_id: Review ID

        In production, this would send email/push notification.
        For now, just log to console.
        """
        print(f'📧 NOTIFICATION → User {comment_author_id}:')
        print(f'   @{reviewer_github} reviewed your comment!')
        print(f'   Please review their interaction to see their feedback.')
        print(f'   Review ID: {review_id}')


    def _notify_both_published(self, original_review_id: int,
                               reciprocal_review_id: int) -> None:
        """
        Notify both parties that reviews are published

        Args:
            original_review_id: Original review ID
            reciprocal_review_id: Reciprocal review ID

        In production, send notifications to both users.
        """
        print(f'🎉 PUBLISHED:')
        print(f'   Review {original_review_id} ↔️ Review {reciprocal_review_id}')
        print(f'   Both parties can now see feedback!')


# ==============================================================================
# FLASK ENDPOINTS
# ==============================================================================

@bidirectional_review_bp.route('/api/review/create', methods=['POST'])
def create_review_endpoint():
    """
    Create review (triggers reciprocal requirement)

    POST body:
    {
        "comment_id": 123,
        "github_username": "octocat",
        "rating": 5,
        "feedback": "Great post!",
        "review_data": {}  // optional
    }

    Returns:
    {
        "review_id": 1,
        "status": "pending_reciprocal",
        "deadline": "2025-01-16T10:30:00"
    }
    """
    data = request.get_json()

    comment_id = data.get('comment_id')
    github_username = data.get('github_username')
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    review_data = data.get('review_data', {})

    if not all([comment_id, github_username, rating]):
        return jsonify({'error': 'comment_id, github_username, and rating required'}), 400

    if not (1 <= rating <= 5):
        return jsonify({'error': 'rating must be 1-5'}), 400

    engine = BidirectionalReviews()

    try:
        result = engine.create_review(
            comment_id=comment_id,
            reviewer_github=github_username,
            rating=rating,
            feedback=feedback,
            review_data=review_data
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bidirectional_review_bp.route('/api/review/reciprocal', methods=['POST'])
def create_reciprocal_endpoint():
    """
    Create reciprocal review (completes pair, publishes both)

    POST body:
    {
        "original_review_id": 1,
        "rating": 4,
        "feedback": "Thanks!",
        "review_data": {}  // optional
    }

    Returns:
    {
        "reciprocal_review_id": 2,
        "original_review_id": 1,
        "both_published": true,
        "can_reply": true
    }
    """
    data = request.get_json()

    original_review_id = data.get('original_review_id')
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    review_data = data.get('review_data', {})

    if not all([original_review_id, rating]):
        return jsonify({'error': 'original_review_id and rating required'}), 400

    if not (1 <= rating <= 5):
        return jsonify({'error': 'rating must be 1-5'}), 400

    engine = BidirectionalReviews()

    try:
        result = engine.create_reciprocal_review(
            original_review_id=original_review_id,
            rating=rating,
            feedback=feedback,
            review_data=review_data
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bidirectional_review_bp.route('/api/review/pending', methods=['GET'])
def get_pending_reviews():
    """
    Get reviews waiting for reciprocal

    Query params:
        - user_id: User ID (defaults to session user)

    Returns:
    [
        {
            "id": 1,
            "comment_id": 123,
            "reviewer_name": "octocat",
            "overall_rating": 5,
            "created_at": "2025-01-02T10:30:00"
        }
    ]
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        # Try to get from session
        user_id = g.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    engine = BidirectionalReviews()
    pending = engine.get_pending_reciprocals(user_id)

    return jsonify(pending)


@bidirectional_review_bp.route('/api/review/status/<int:review_id>', methods=['GET'])
def get_review_status_endpoint(review_id):
    """
    Get review status

    Returns:
    {
        "review_id": 1,
        "status": "pending_reciprocal",
        "message": "Waiting for reciprocal review (12 days left)"
    }
    """
    engine = BidirectionalReviews()
    status = engine.get_review_status(review_id)

    return jsonify(status)


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    print('\n🔄 Bidirectional Review Engine - Airbnb Style\n')

    engine = BidirectionalReviews()

    # Test: Create initial review
    print('Test 1: Create review (triggers reciprocal)\n')

    review = engine.create_review(
        comment_id=1,  # Assuming comment exists
        reviewer_github='testuser',
        rating=5,
        feedback='Great comment!'
    )

    print(f'✅ Review created: {review["review_id"]}')
    print(f'   Status: {review["status"]}')
    print(f'   Deadline: {review["deadline"]}\n')

    # Test: Check pending
    print('Test 2: Check pending reciprocals\n')

    pending = engine.get_pending_reciprocals(user_id=1)
    print(f'📋 Pending reviews: {len(pending)}\n')

    # Test: Create reciprocal (if pending exists)
    if pending:
        print('Test 3: Create reciprocal review\n')

        reciprocal = engine.create_reciprocal_review(
            original_review_id=pending[0]['id'],
            rating=4,
            feedback='Thanks for the review!'
        )

        print(f'✅ Reciprocal created: {reciprocal["reciprocal_review_id"]}')
        print(f'   Both published: {reciprocal["both_published"]}')
        print(f'   Can reply: {reciprocal["can_reply"]}\n')

    print('✅ Tests complete!\n')

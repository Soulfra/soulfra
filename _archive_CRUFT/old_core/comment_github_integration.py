#!/usr/bin/env python3
"""
Comment-GitHub Integration

Connects the complete flow:
Comment Chain → GitHub Star → Bidirectional Review → Reply Permission

**Complete Flow:**
1. User A posts comment → creates chain_hash
2. User B clicks "Reply" button
3. System checks: Is User B authenticated with GitHub?
   - No → Redirect to GitHub OAuth
   - Yes → Continue
4. System checks: Has User B starred the repo?
   - No → Show "Star to continue" prompt
   - Yes → Continue
5. Show review form: "Review User A's comment"
6. User B submits review → creates review (pending_reciprocal)
7. Notify User A: "Please review User B to see their feedback"
8. User A reviews User B → publishes both reviews
9. User B can now post reply comment

**Integration Points:**
- comment_voice_chain.py: Comment chain creation
- github_faucet.py: GitHub OAuth
- github_star_validator.py: Star verification
- bidirectional_review_engine.py: Airbnb-style reviews

**Database:**
All integrated via foreign keys:
- comments.id → game_reviews.comment_id
- comments.chain_hash → game_reviews.chain_hash
- api_keys.github_username → game_reviews.github_username

**Usage:**
```python
from comment_github_integration import CommentGitHubFlow

flow = CommentGitHubFlow()

# Check if user can reply
can_reply = flow.check_reply_permission(
    comment_id=123,
    github_username='octocat',
    domain='soulfra.com'
)

if can_reply['allowed']:
    # Show reply form
else:
    # Show: can_reply['next_step']
    # e.g., "Connect GitHub", "Star repo", "Review comment"
```

**API Endpoints:**
- GET /api/comment/can-reply/<comment_id>?github_username=octocat
- POST /api/comment/reply-with-review
- GET /api/comment/reviews/<comment_id>
"""

from flask import Blueprint, request, jsonify, g
from database import get_db
from github_faucet import GitHubFaucet
from github_star_validator import GitHubStarValidator
from bidirectional_review_engine import BidirectionalReviews
from typing import Dict, Optional
import json

comment_github_bp = Blueprint('comment_github', __name__)


class CommentGitHubFlow:
    """
    Orchestrate complete comment → GitHub → review → reply flow
    """

    def __init__(self):
        self.github_faucet = GitHubFaucet()
        self.star_validator = GitHubStarValidator()
        self.review_engine = BidirectionalReviews()


    # ==========================================================================
    # REPLY PERMISSION CHECK
    # ==========================================================================

    def check_reply_permission(self, comment_id: int, github_username: str,
                               domain: str) -> Dict:
        """
        Check if user has permission to reply to comment

        Args:
            comment_id: Comment to reply to
            github_username: GitHub username attempting reply
            domain: Current domain (for repo mapping)

        Returns:
            Dict with:
                - allowed (bool): Can user reply?
                - next_step (str): What user needs to do next
                - details (dict): Additional info

        Steps checked:
        1. GitHub connected? (has API key)
        2. Repo starred?
        3. Review submitted?
        4. Reciprocal review completed?

        Example:
            >>> flow = CommentGitHubFlow()
            >>> result = flow.check_reply_permission(123, 'octocat', 'soulfra.com')
            >>> if result['allowed']:
            ...     # Show reply form
            ... else:
            ...     print(result['next_step'])
        """
        db = get_db()

        # Get comment
        comment = db.execute('''
            SELECT id, user_id, chain_hash, content FROM comments WHERE id = ?
        ''', (comment_id,)).fetchone()

        if not comment:
            db.close()
            return {
                'allowed': False,
                'next_step': 'error',
                'error': f'Comment {comment_id} not found'
            }

        # Step 1: Check GitHub connection
        api_key_row = db.execute('''
            SELECT api_key, user_id FROM api_keys WHERE github_username = ?
        ''', (github_username,)).fetchone()

        if not api_key_row:
            db.close()
            return {
                'allowed': False,
                'next_step': 'connect_github',
                'message': 'Please connect your GitHub account',
                'oauth_url': '/api/github/connect'  # Would generate via github_faucet
            }

        user_id = api_key_row[1]

        # Step 2: Check repo star
        star_result = self.star_validator.check_star_for_domain(github_username, domain)

        if not star_result['has_starred']:
            db.close()
            return {
                'allowed': False,
                'next_step': 'star_repo',
                'message': f'Please star our repo to reply',
                'repo_url': star_result['repo_url'],
                'star_count': star_result['star_count']
            }

        # Step 3: Check if review exists
        existing_review = db.execute('''
            SELECT id, reciprocal_review_id, requires_reciprocal
            FROM game_reviews
            WHERE comment_id = ? AND github_username = ?
        ''', (comment_id, github_username)).fetchone()

        if not existing_review:
            db.close()
            return {
                'allowed': False,
                'next_step': 'submit_review',
                'message': 'Please review this comment before replying',
                'comment_id': comment_id,
                'comment_preview': comment['content'][:100]
            }

        # Step 4: Check if reciprocal completed
        if existing_review['requires_reciprocal'] and not existing_review['reciprocal_review_id']:
            db.close()
            return {
                'allowed': False,
                'next_step': 'wait_reciprocal',
                'message': 'Waiting for comment author to review your interaction',
                'review_id': existing_review['id'],
                'status': 'pending_reciprocal'
            }

        # All checks passed!
        db.close()
        return {
            'allowed': True,
            'next_step': 'reply',
            'message': 'You can reply to this comment',
            'user_id': user_id,
            'review_id': existing_review['id']
        }


    # ==========================================================================
    # REPLY WITH REVIEW
    # ==========================================================================

    def submit_reply_with_review(self, comment_id: int, github_username: str,
                                 domain: str, rating: int, feedback: str,
                                 reply_content: Optional[str] = None) -> Dict:
        """
        Submit review and optionally post reply

        Args:
            comment_id: Comment being replied to
            github_username: GitHub username
            domain: Current domain
            rating: 1-5 star rating
            feedback: Review feedback
            reply_content: Optional reply comment text

        Returns:
            Dict with review_id and next steps

        Example:
            >>> flow = CommentGitHubFlow()
            >>> result = flow.submit_reply_with_review(
            ...     comment_id=123,
            ...     github_username='octocat',
            ...     domain='soulfra.com',
            ...     rating=5,
            ...     feedback='Great idea!',
            ...     reply_content='I agree, let me add...'
            ... )
            >>> print(result['status'])
            pending_reciprocal
        """
        # Check permissions first
        permission = self.check_reply_permission(comment_id, github_username, domain)

        if permission['next_step'] == 'submit_review':
            # Create review
            review_result = self.review_engine.create_review(
                comment_id=comment_id,
                reviewer_github=github_username,
                rating=rating,
                feedback=feedback,
                review_data={
                    'domain': domain,
                    'starred_repo': permission.get('repo_url', ''),
                    'reply_content_preview': reply_content[:100] if reply_content else None
                }
            )

            return {
                'review_id': review_result['review_id'],
                'status': 'pending_reciprocal',
                'message': review_result['message'],
                'can_post_reply': False,
                'next_step': 'wait_reciprocal'
            }

        elif permission['allowed']:
            # User already reviewed, can post reply directly
            if reply_content:
                reply_id = self._post_reply_comment(
                    parent_comment_id=comment_id,
                    user_github=github_username,
                    content=reply_content
                )

                return {
                    'review_id': permission.get('review_id'),
                    'reply_id': reply_id,
                    'status': 'posted',
                    'message': 'Reply posted!',
                    'can_post_reply': True
                }
            else:
                return {
                    'review_id': permission.get('review_id'),
                    'status': 'ready',
                    'message': 'Ready to post reply',
                    'can_post_reply': True
                }

        else:
            # Permission denied for some reason
            return {
                'error': 'Permission denied',
                'next_step': permission['next_step'],
                'message': permission['message'],
                'can_post_reply': False
            }


    def _post_reply_comment(self, parent_comment_id: int, user_github: str,
                           content: str) -> int:
        """
        Post reply comment to comment chain

        Args:
            parent_comment_id: Parent comment ID
            user_github: GitHub username
            content: Reply content

        Returns:
            New comment ID
        """
        db = get_db()

        # Get user_id from api_keys
        user_row = db.execute('''
            SELECT user_id FROM api_keys WHERE github_username = ?
        ''', (user_github,)).fetchone()

        user_id = user_row[0] if user_row else 1  # Default to anonymous

        # Get parent comment for post_id
        parent = db.execute('''
            SELECT post_id, chain_hash FROM comments WHERE id = ?
        ''', (parent_comment_id,)).fetchone()

        if not parent:
            db.close()
            raise ValueError(f'Parent comment {parent_comment_id} not found')

        # Create reply comment (will use comment_voice_chain.py logic)
        cursor = db.execute('''
            INSERT INTO comments (post_id, user_id, content, parent_comment_id)
            VALUES (?, ?, ?, ?)
        ''', (parent['post_id'], user_id, content, parent_comment_id))

        reply_id = cursor.lastrowid

        # Generate chain hash (simplified - full version in comment_voice_chain.py)
        import hashlib
        chain_hash = hashlib.sha256(
            f"{reply_id}:none:{parent['chain_hash']}".encode()
        ).hexdigest()[:16]

        db.execute('''
            UPDATE comments SET chain_hash = ? WHERE id = ?
        ''', (chain_hash, reply_id))

        db.commit()
        db.close()

        return reply_id


    # ==========================================================================
    # GET COMMENT REVIEWS
    # ==========================================================================

    def get_comment_reviews(self, comment_id: int,
                           include_pending: bool = False) -> Dict:
        """
        Get all reviews for a comment

        Args:
            comment_id: Comment ID
            include_pending: Include pending reciprocal reviews?

        Returns:
            Dict with published and pending reviews

        Example:
            >>> flow = CommentGitHubFlow()
            >>> reviews = flow.get_comment_reviews(comment_id=123)
            >>> print(f"Published: {len(reviews['published'])}")
            >>> print(f"Pending: {len(reviews['pending'])}")
        """
        db = get_db()

        # Get published reviews (have reciprocal)
        published = db.execute('''
            SELECT
                r.id,
                r.reviewer_name,
                r.github_username,
                r.overall_rating,
                r.review_data,
                r.created_at,
                r.reciprocal_review_id
            FROM game_reviews r
            WHERE r.comment_id = ?
              AND r.reciprocal_review_id IS NOT NULL
            ORDER BY r.created_at DESC
        ''', (comment_id,)).fetchall()

        published_list = [dict(row) for row in published]

        # Get pending reviews (if requested)
        pending_list = []
        if include_pending:
            pending = db.execute('''
                SELECT
                    r.id,
                    r.reviewer_name,
                    r.github_username,
                    r.overall_rating,
                    r.created_at,
                    r.requires_reciprocal
                FROM game_reviews r
                WHERE r.comment_id = ?
                  AND r.requires_reciprocal = 1
                  AND r.reciprocal_review_id IS NULL
                ORDER BY r.created_at DESC
            ''', (comment_id,)).fetchall()

            pending_list = [dict(row) for row in pending]

        db.close()

        return {
            'comment_id': comment_id,
            'published': published_list,
            'pending': pending_list,
            'total_published': len(published_list),
            'total_pending': len(pending_list)
        }


# ==============================================================================
# FLASK ENDPOINTS
# ==============================================================================

@comment_github_bp.route('/api/comment/can-reply/<int:comment_id>', methods=['GET'])
def can_reply_endpoint(comment_id):
    """
    Check if user can reply to comment

    Query params:
        - github_username: GitHub username

    Returns:
    {
        "allowed": false,
        "next_step": "star_repo",
        "message": "Please star our repo to reply",
        "repo_url": "https://github.com/soulfra/soulfra"
    }
    """
    github_username = request.args.get('github_username')

    if not github_username:
        return jsonify({'error': 'github_username required'}), 400

    domain = request.host
    flow = CommentGitHubFlow()

    result = flow.check_reply_permission(comment_id, github_username, domain)

    return jsonify(result)


@comment_github_bp.route('/api/comment/reply-with-review', methods=['POST'])
def reply_with_review_endpoint():
    """
    Submit review and optional reply

    POST body:
    {
        "comment_id": 123,
        "github_username": "octocat",
        "rating": 5,
        "feedback": "Great post!",
        "reply_content": "I agree, let me add..."  // optional
    }

    Returns:
    {
        "review_id": 1,
        "status": "pending_reciprocal",
        "message": "Review submitted! Waiting for reciprocal..."
    }
    """
    data = request.get_json()

    comment_id = data.get('comment_id')
    github_username = data.get('github_username')
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    reply_content = data.get('reply_content')

    if not all([comment_id, github_username, rating]):
        return jsonify({'error': 'comment_id, github_username, rating required'}), 400

    domain = request.host
    flow = CommentGitHubFlow()

    try:
        result = flow.submit_reply_with_review(
            comment_id=comment_id,
            github_username=github_username,
            domain=domain,
            rating=rating,
            feedback=feedback,
            reply_content=reply_content
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@comment_github_bp.route('/api/comment/reviews/<int:comment_id>', methods=['GET'])
def get_reviews_endpoint(comment_id):
    """
    Get reviews for comment

    Query params:
        - include_pending: Include pending reviews (default: false)

    Returns:
    {
        "comment_id": 123,
        "published": [...],
        "pending": [...],
        "total_published": 5,
        "total_pending": 2
    }
    """
    include_pending = request.args.get('include_pending', 'false').lower() == 'true'

    flow = CommentGitHubFlow()
    reviews = flow.get_comment_reviews(comment_id, include_pending)

    return jsonify(reviews)


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    print('\n🔗 Comment-GitHub Integration Flow\n')

    flow = CommentGitHubFlow()

    # Test: Check reply permission
    print('Test 1: Check reply permission\n')

    result = flow.check_reply_permission(
        comment_id=1,
        github_username='testuser',
        domain='soulfra.com'
    )

    print(f'Can reply: {result["allowed"]}')
    print(f'Next step: {result["next_step"]}')
    print(f'Message: {result.get("message", "")}\n')

    # Test: Get comment reviews
    print('Test 2: Get comment reviews\n')

    reviews = flow.get_comment_reviews(comment_id=1, include_pending=True)

    print(f'Published: {reviews["total_published"]}')
    print(f'Pending: {reviews["total_pending"]}\n')

    print('✅ Integration tests complete!\n')

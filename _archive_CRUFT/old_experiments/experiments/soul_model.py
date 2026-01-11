#!/usr/bin/env python3
"""
Soul Model for Soulfra
Based on research in Post #10: "What IS a Soul?"

A soul is:
- Essence: The fundamental nature of a being
- Identity: What makes you YOU
- Expression: How you manifest (posts, comments, contributions)
- Connections: Who you interact with
- Evolution: How you change over time

This model enables:
- User profiles based on essence (not just username)
- Soul packs for marketing/products
- Soul similarity search
- Soul-based avatars
"""

from datetime import datetime
from collections import Counter
from database import get_db
from db_helpers import get_user_by_id, get_comments_for_post
from reasoning_engine import ReasoningEngine


class Soul:
    """
    Represents a user's soul in Soulfra

    Layers:
    1. Identity - immutable (username, user_id)
    2. Essence - evolves slowly (interests, values, expertise)
    3. Expression - changes frequently (posts, comments, contributions)
    4. Connections - network (who you interact with)
    5. Evolution - time-series (how you change)
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.engine = ReasoningEngine()

        # Load user data
        conn = get_db()
        self.user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not self.user:
            raise ValueError(f"User {user_id} not found")

        self.user = dict(self.user)

        # Load posts
        self.posts = conn.execute(
            'SELECT * FROM posts WHERE user_id = ? ORDER BY published_at DESC',
            (user_id,)
        ).fetchall()
        self.posts = [dict(p) for p in self.posts]

        # Load comments
        self.comments = conn.execute(
            'SELECT * FROM comments WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        self.comments = [dict(c) for c in self.comments]

        conn.close()

    # ==================== IDENTITY LAYER (Immutable) ====================

    def get_identity(self):
        """Core identity - who you are"""
        return {
            'user_id': self.user_id,
            'username': self.user['username'],
            'display_name': self.user['display_name'],
            'is_ai_persona': self.user['is_ai_persona'],
            'created_at': self.user['created_at']
        }

    # ==================== ESSENCE LAYER (Evolves Slowly) ====================

    def extract_interests(self, top_n=10):
        """Extract interests from posts/comments"""
        all_text = ""

        # Combine all post content
        for post in self.posts:
            all_text += " " + post['title'] + " " + post['content']

        # Combine all comment content
        for comment in self.comments:
            all_text += " " + comment['content']

        # Extract keywords
        keywords = self.engine.extract_keywords(all_text, top_n=top_n)

        return [kw for kw, _ in keywords]

    def extract_expertise(self):
        """Calculate expertise areas based on keyword frequency"""
        interests = self.extract_interests(top_n=20)

        # Calculate frequency scores
        expertise = {}
        for kw, freq in self.engine.extract_keywords(
            " ".join([p['content'] for p in self.posts]),
            top_n=20
        ):
            # Normalize to 0-1 scale
            expertise[kw] = min(freq / 10.0, 1.0)

        return expertise

    def detect_values(self):
        """Detect values from post patterns"""
        # Simple heuristic: look for value-indicating words
        value_words = {
            'privacy', 'security', 'transparency', 'community',
            'open-source', 'collaboration', 'freedom', 'trust',
            'quality', 'simplicity', 'honesty', 'respect'
        }

        all_text = " ".join([p['content'] for p in self.posts]).lower()

        detected = []
        for value in value_words:
            if value in all_text:
                detected.append(value)

        return detected

    # ==================== EXPRESSION LAYER (Changes Frequently) ====================

    def get_expression(self):
        """How soul expresses itself"""
        return {
            'post_count': len(self.posts),
            'comment_count': len(self.comments),
            'avg_post_length': sum(len(p['content']) for p in self.posts) / max(len(self.posts), 1),
            'recent_topics': [p['title'] for p in self.posts[:5]],
            'has_code': any('```' in p['content'] for p in self.posts)
        }

    # ==================== CONNECTION LAYER (Network) ====================

    def get_connections(self):
        """Who this soul interacts with"""
        conn = get_db()

        # Find users this soul comments on
        interacts_with = conn.execute('''
            SELECT DISTINCT p.user_id, u.username
            FROM comments c
            JOIN posts p ON c.post_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE c.user_id = ?
            LIMIT 10
        ''', (self.user_id,)).fetchall()

        conn.close()

        return [dict(u) for u in interacts_with]

    # ==================== EVOLUTION LAYER (Time-Series) ====================

    def get_evolution(self):
        """How soul has changed over time"""
        if not self.posts:
            return {'first_post': None, 'latest_post': None, 'growth': 0}

        first_post = self.posts[-1]
        latest_post = self.posts[0]

        # Calculate activity growth
        first_keywords = self.engine.extract_keywords(first_post['content'], top_n=5)
        latest_keywords = self.engine.extract_keywords(latest_post['content'], top_n=5)

        return {
            'first_post': first_post['title'],
            'latest_post': latest_post['title'],
            'first_keywords': [kw for kw, _ in first_keywords],
            'latest_keywords': [kw for kw, _ in latest_keywords],
            'total_posts': len(self.posts)
        }

    # ==================== SOUL COMPILATION ====================

    def compile_pack(self):
        """
        Compile soul into exportable package

        Like Go compiler, but for souls.
        Output: JSON/YAML-ready dict for marketing, matching, export
        """
        return {
            'version': '1.0',
            'compiled_at': datetime.now().isoformat(),

            # Identity
            'identity': self.get_identity(),

            # Essence
            'essence': {
                'interests': self.extract_interests(),
                'expertise': self.extract_expertise(),
                'values': self.detect_values()
            },

            # Expression
            'expression': self.get_expression(),

            # Connections
            'connections': self.get_connections(),

            # Evolution
            'evolution': self.get_evolution(),

            # Fingerprint (for similarity matching)
            'fingerprint': self.calculate_fingerprint()
        }

    def calculate_fingerprint(self):
        """
        Calculate unique soul fingerprint for similarity matching

        Returns vector of essence dimensions for cosine similarity
        """
        interests = self.extract_interests(top_n=10)
        expertise = self.extract_expertise()

        # Create fingerprint from top keywords
        return {
            'interests_vector': interests,
            'expertise_scores': expertise,
            'value_flags': self.detect_values(),
            'activity_level': len(self.posts) + len(self.comments),
            'expression_style': 'technical' if any('```' in p['content'] for p in self.posts) else 'narrative'
        }

    def similarity_to(self, other_soul):
        """Calculate similarity to another soul (0-1)"""
        my_interests = set(self.extract_interests())
        other_interests = set(other_soul.extract_interests())

        if not my_interests or not other_interests:
            return 0.0

        # Jaccard similarity
        intersection = len(my_interests & other_interests)
        union = len(my_interests | other_interests)

        return intersection / union if union > 0 else 0.0


def test_soul_model():
    """Test the soul model"""
    print("🧠 Testing Soul Model\n")

    # Get a user
    conn = get_db()
    user = conn.execute('SELECT id, username FROM users WHERE is_ai_persona = 0 LIMIT 1').fetchone()
    conn.close()

    if not user:
        print("❌ No real users found")
        return

    user_id = user['id']
    username = user['username']

    print(f"Compiling soul for: {username}\n")

    # Create soul
    soul = Soul(user_id)

    # Compile pack
    pack = soul.compile_pack()

    print("Identity:", pack['identity'])
    print("\nEssence:")
    print("  Interests:", pack['essence']['interests'][:5])
    print("  Values:", pack['essence']['values'])
    print("\nExpression:")
    print("  Posts:", pack['expression']['post_count'])
    print("  Comments:", pack['expression']['comment_count'])
    print("\nFingerprint:")
    print("  Activity:", pack['fingerprint']['activity_level'])
    print("  Style:", pack['fingerprint']['expression_style'])


if __name__ == '__main__':
    test_soul_model()

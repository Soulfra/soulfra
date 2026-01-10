"""
Gamification API - Quiz, Ratings, Achievements, Progress Tracking

Scholastic Book Fair + Goodreads-style content discovery system.
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime
import random

gamification_bp = Blueprint('gamification', __name__)

def get_db_connection():
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_gamification_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Quiz questions & attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            blog_post_id INTEGER,
            score INTEGER,
            total_questions INTEGER,
            passed INTEGER,
            tokens_earned INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')

    # Ratings & reviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content_type TEXT,
            content_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            tokens_earned INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')

    # Reading progress
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain TEXT,
            blog_post_id INTEGER,
            completed INTEGER DEFAULT 0,
            time_spent_seconds INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')

    # Achievements/badges
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_type TEXT,
            achievement_name TEXT,
            domain TEXT,
            earned_at TEXT,
            tokens_awarded INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

@gamification_bp.route('/api/quiz/generate/<int:blog_post_id>', methods=['GET'])
def generate_quiz(blog_post_id):
    """Auto-generate quiz questions from blog post keywords"""
    try:
        init_gamification_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM blog_posts WHERE id = ?', (blog_post_id,))
        post = cursor.fetchone()

        if not post:
            return jsonify({'success': False, 'error': 'Blog post not found'}), 404

        # Get ideas that were used in this blog
        cursor.execute('''
            SELECT * FROM ideas
            WHERE blog_post_id = ?
        ''', (blog_post_id,))
        ideas = cursor.fetchall()
        conn.close()

        if not ideas:
            return jsonify({'success': False, 'error': 'No ideas found for this post'}), 404

        # Generate questions from keywords
        questions = []
        for idea in ideas[:3]:  # Max 3 questions
            keywords = json.loads(idea['keywords']) if idea['keywords'] else []
            if not keywords:
                continue

            # Simple fill-in-the-blank style question
            question_text = f"This post discusses concepts related to: ____"
            correct_answer = keywords[0]
            wrong_answers = [kw for kw in keywords[1:4]]  # Use other keywords as distractors

            questions.append({
                'question': question_text,
                'correct_answer': correct_answer,
                'options': random.sample([correct_answer] + wrong_answers, min(4, len([correct_answer] + wrong_answers)))
            })

        return jsonify({
            'success': True,
            'blog_post_id': blog_post_id,
            'title': post['title'],
            'questions': questions
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gamification_bp.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    """Submit quiz answers and earn tokens"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        blog_post_id = data.get('blog_post_id')
        answers = data.get('answers', [])

        init_gamification_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate score
        score = sum(1 for answer in answers if answer.get('correct'))
        total = len(answers)
        passed = score >= (total * 0.6)  # 60% to pass

        tokens_earned = 10 if passed else 0

        # Record attempt
        cursor.execute('''
            INSERT INTO quiz_attempts (user_id, blog_post_id, score, total_questions, passed, tokens_earned, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, blog_post_id, score, total, int(passed), tokens_earned, datetime.utcnow().isoformat()))

        # Award tokens if passed
        if passed and user_id:
            try:
                from token_economy_api import earn_tokens
                # TODO: Call earn_tokens endpoint
            except:
                pass

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'score': score,
            'total': total,
            'passed': passed,
            'tokens_earned': tokens_earned,
            'message': '🎉 Passed! +10 tokens' if passed else 'Try again to earn tokens'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gamification_bp.route('/api/rating/submit', methods=['POST'])
def submit_rating():
    """Submit rating/review for content"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        content_type = data.get('content_type', 'blog_post')
        content_id = data.get('content_id')
        rating = data.get('rating')
        review_text = data.get('review_text', '')

        if not rating or rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be 1-5 stars'}), 400

        init_gamification_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        tokens_earned = 5 if review_text else 2  # More tokens for written reviews

        cursor.execute('''
            INSERT INTO content_ratings (user_id, content_type, content_id, rating, review_text, tokens_earned, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, content_type, content_id, rating, review_text, tokens_earned, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'tokens_earned': tokens_earned,
            'message': f'Thanks for the review! +{tokens_earned} tokens'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gamification_bp.route('/api/progress/mark-read', methods=['POST'])
def mark_as_read():
    """Track reading progress"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        blog_post_id = data.get('blog_post_id')
        domain = data.get('domain')
        time_spent = data.get('time_spent_seconds', 0)

        init_gamification_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO reading_progress (user_id, domain, blog_post_id, completed, time_spent_seconds, created_at)
            VALUES (?, ?, ?, 1, ?, ?)
        ''', (user_id, domain, blog_post_id, time_spent, datetime.utcnow().isoformat()))

        # Check for achievements
        cursor.execute('''
            SELECT COUNT(*) as count FROM reading_progress
            WHERE user_id = ? AND domain = ? AND completed = 1
        ''', (user_id, domain))
        domain_count = cursor.fetchone()['count']

        # Award badge at milestones
        achievement = None
        if domain_count == 5:
            achievement = f"{domain.capitalize()} Explorer"
        elif domain_count == 10:
            achievement = f"{domain.capitalize()} Expert"
        elif domain_count == 25:
            achievement = f"{domain.capitalize()} Master"

        if achievement:
            cursor.execute('''
                INSERT INTO user_achievements (user_id, achievement_type, achievement_name, domain, earned_at, tokens_awarded)
                VALUES (?, 'reading', ?, ?, ?, 20)
            ''', (user_id, achievement, domain, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'domain_progress': domain_count,
            'achievement_unlocked': achievement,
            'tokens_earned': 20 if achievement else 0
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gamification_bp.route('/api/achievements/<int:user_id>', methods=['GET'])
def get_achievements(user_id):
    """Get user's achievements/badges"""
    try:
        init_gamification_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM user_achievements
            WHERE user_id = ?
            ORDER BY earned_at DESC
        ''', (user_id,))
        achievements = cursor.fetchall()

        # Get reading progress per domain
        cursor.execute('''
            SELECT domain, COUNT(*) as count
            FROM reading_progress
            WHERE user_id = ? AND completed = 1
            GROUP BY domain
        ''', (user_id,))
        progress = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'achievements': [{
                'name': a['achievement_name'],
                'type': a['achievement_type'],
                'domain': a['domain'],
                'earned_at': a['earned_at']
            } for a in achievements],
            'reading_progress': {p['domain']: p['count'] for p in progress}
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gamification_bp.route('/api/ratings/<content_type>/<int:content_id>', methods=['GET'])
def get_ratings(content_type, content_id):
    """Get ratings for a piece of content"""
    try:
        init_gamification_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings
            FROM content_ratings
            WHERE content_type = ? AND content_id = ?
        ''', (content_type, content_id))
        stats = cursor.fetchone()

        cursor.execute('''
            SELECT u.username, cr.rating, cr.review_text, cr.created_at
            FROM content_ratings cr
            LEFT JOIN users u ON cr.user_id = u.id
            WHERE cr.content_type = ? AND cr.content_id = ?
            ORDER BY cr.created_at DESC
            LIMIT 10
        ''', (content_type, content_id))
        reviews = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'average_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
            'total_ratings': stats['total_ratings'],
            'reviews': [{
                'username': r['username'],
                'rating': r['rating'],
                'review': r['review_text'],
                'created_at': r['created_at']
            } for r in reviews]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

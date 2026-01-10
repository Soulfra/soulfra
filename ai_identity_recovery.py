#!/usr/bin/env python3
"""
AI Identity Recovery System

When users lose access (forgot password, new device), they must prove identity by:
1. AI generates questions from their previous recordings/ideas/work
2. User recreates or answers questions about their content
3. Ollama analyzes semantic similarity of answers
4. If verified → restore access on new device

Flow:
- User: "I lost access, my display name was Matthew Mauer"
- AI: Retrieves recordings attributed to that display name
- AI: Generates 3-5 questions about their past work/ideas
- User: Answers questions (voice or text)
- AI: Compares semantic similarity using Ollama embeddings
- If similarity > 70% → Restore access
"""

from flask import Blueprint, request, jsonify
from database import get_db
import requests
import json
from typing import List, Dict, Tuple
import random

recovery_bp = Blueprint('recovery', __name__)

OLLAMA_URL = 'http://localhost:11434'

def init_recovery_tables():
    """Create identity recovery tables"""
    db = get_db()

    # Recovery attempts table
    db.execute('''
        CREATE TABLE IF NOT EXISTS identity_recovery_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            device_fingerprint TEXT NOT NULL,
            questions_json TEXT,  -- JSON array of questions
            answers_json TEXT,  -- JSON array of user answers
            similarity_score REAL,
            status TEXT DEFAULT 'pending',  -- 'pending', 'verified', 'failed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP
        )
    ''')

    db.commit()
    print("✅ AI Identity Recovery tables created")


def generate_recovery_questions(display_name: str, first_name: str, last_name: str) -> List[Dict]:
    """
    Generate recovery questions from user's past recordings

    Args:
        display_name: User's display name
        first_name: First name (LIGHT path)
        last_name: Last name (SHADOW path)

    Returns:
        List of questions with context
    """
    db = get_db()

    # Get user's past recordings
    recordings = db.execute('''
        SELECT transcription, category, created_at
        FROM simple_voice_recordings
        WHERE transcription LIKE ?
           OR transcription LIKE ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (f'%{first_name}%', f'%{last_name}%')).fetchall()

    if not recordings:
        # Fallback to generic questions
        return [
            {
                'question': 'What type of work or projects do you typically record about?',
                'expected_keywords': ['work', 'project', 'idea', 'code', 'business'],
                'context': None
            },
            {
                'question': 'What are your main interests or goals?',
                'expected_keywords': ['goal', 'learn', 'build', 'create', 'improve'],
                'context': None
            },
            {
                'question': 'Describe one of your recent ideas or thoughts you recorded.',
                'expected_keywords': ['idea', 'thought', 'concept', 'vision'],
                'context': None
            }
        ]

    # Generate questions from actual recordings
    questions = []

    # Question 1: About WORK (LIGHT path - first name)
    work_recordings = [r for r in recordings if dict(r).get('category') == 'work']
    if work_recordings:
        rec = dict(work_recordings[0])
        snippet = rec['transcription'][:100]
        questions.append({
            'question': f'You recorded something about work. What was it about?',
            'expected_content': rec['transcription'],
            'context': 'work'
        })

    # Question 2: About IDEAS (SHADOW path - last name)
    ideas_recordings = [r for r in recordings if dict(r).get('category') == 'ideas']
    if ideas_recordings:
        rec = dict(ideas_recordings[0])
        questions.append({
            'question': f'You recorded an idea. What was the main concept?',
            'expected_content': rec['transcription'],
            'context': 'ideas'
        })

    # Question 3: General recordings
    if len(recordings) > 2:
        rec = dict(recordings[2])
        questions.append({
            'question': f'What topics do you typically discuss in your recordings?',
            'expected_content': rec['transcription'],
            'context': 'general'
        })

    return questions[:3]  # Return 3 questions


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity using Ollama embeddings

    Args:
        text1: First text (expected answer)
        text2: Second text (user's answer)

    Returns:
        float: Similarity score (0.0 to 1.0)
    """
    try:
        # Get embeddings from Ollama
        response1 = requests.post(
            f'{OLLAMA_URL}/api/embeddings',
            json={'model': 'llama3.2:1b', 'prompt': text1},
            timeout=10
        )
        response2 = requests.post(
            f'{OLLAMA_URL}/api/embeddings',
            json={'model': 'llama3.2:1b', 'prompt': text2},
            timeout=10
        )

        if response1.status_code != 200 or response2.status_code != 200:
            # Fallback to keyword matching
            return _keyword_similarity(text1, text2)

        embedding1 = response1.json().get('embedding', [])
        embedding2 = response2.json().get('embedding', [])

        # Calculate cosine similarity
        similarity = _cosine_similarity(embedding1, embedding2)
        return similarity

    except Exception as e:
        print(f"⚠️  Ollama embedding failed: {e}")
        # Fallback to keyword matching
        return _keyword_similarity(text1, text2)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def _keyword_similarity(text1: str, text2: str) -> float:
    """Fallback keyword-based similarity"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


@recovery_bp.route('/api/recovery/request', methods=['POST'])
def request_recovery():
    """
    Start identity recovery process

    POST /api/recovery/request
    {
        "display_name": "Matthew Mauer",
        "email": "user@example.com"  // optional for verification
    }

    Returns: Recovery questions
    """
    data = request.json
    display_name = data.get('display_name')
    email = data.get('email')

    if not display_name:
        return jsonify({'error': 'display_name required'}), 400

    db = get_db()

    # Check if user exists
    query = 'SELECT id, display_name, first_name, last_name, device_fingerprint FROM soulfra_master_users WHERE display_name = ?'
    params = [display_name]

    if email:
        query += ' AND email = ?'
        params.append(email)

    user = db.execute(query, params).fetchone()

    if not user:
        return jsonify({'error': 'No account found with that display name'}), 404

    user_dict = dict(user)

    # Generate device fingerprint for current device
    user_agent = request.headers.get('User-Agent', 'unknown')
    ip_address = request.remote_addr or 'unknown'
    from dual_persona_generator import generate_device_fingerprint
    current_device = generate_device_fingerprint(user_agent, ip_address)

    # Generate recovery questions
    questions = generate_recovery_questions(
        user_dict['display_name'],
        user_dict['first_name'],
        user_dict['last_name']
    )

    # Store recovery attempt
    cursor = db.execute('''
        INSERT INTO identity_recovery_attempts (
            display_name,
            device_fingerprint,
            questions_json,
            status
        ) VALUES (?, ?, ?, ?)
    ''', (
        display_name,
        current_device,
        json.dumps(questions),
        'pending'
    ))

    recovery_id = cursor.lastrowid
    db.commit()

    # Return questions (without expected answers)
    return jsonify({
        'recovery_id': recovery_id,
        'display_name': display_name,
        'questions': [q['question'] for q in questions],
        'instructions': 'Answer these questions about your previous recordings to verify your identity.'
    })


@recovery_bp.route('/api/recovery/verify', methods=['POST'])
def verify_recovery():
    """
    Verify identity recovery answers

    POST /api/recovery/verify
    {
        "recovery_id": 1,
        "answers": ["answer1", "answer2", "answer3"]
    }

    Returns: Verification result + new JWT if successful
    """
    data = request.json
    recovery_id = data.get('recovery_id')
    answers = data.get('answers', [])

    if not recovery_id or not answers:
        return jsonify({'error': 'recovery_id and answers required'}), 400

    db = get_db()

    # Get recovery attempt
    attempt = db.execute('''
        SELECT * FROM identity_recovery_attempts WHERE id = ?
    ''', (recovery_id,)).fetchone()

    if not attempt:
        return jsonify({'error': 'Recovery attempt not found'}), 404

    attempt_dict = dict(attempt)

    if attempt_dict['status'] != 'pending':
        return jsonify({'error': f'Recovery already {attempt_dict["status"]}'}), 400

    # Load questions
    questions = json.loads(attempt_dict['questions_json'])

    if len(answers) != len(questions):
        return jsonify({'error': f'Expected {len(questions)} answers, got {len(answers)}'}), 400

    # Calculate similarity for each answer
    similarities = []
    for i, (question, answer) in enumerate(zip(questions, answers)):
        expected = question.get('expected_content', question.get('question', ''))
        similarity = calculate_semantic_similarity(expected, answer)
        similarities.append(similarity)

    # Average similarity score
    avg_similarity = sum(similarities) / len(similarities)

    # Threshold: 70% similarity required
    SIMILARITY_THRESHOLD = 0.70
    verified = avg_similarity >= SIMILARITY_THRESHOLD

    # Update recovery attempt
    db.execute('''
        UPDATE identity_recovery_attempts
        SET answers_json = ?,
            similarity_score = ?,
            status = ?,
            verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        json.dumps(answers),
        avg_similarity,
        'verified' if verified else 'failed',
        recovery_id
    ))

    db.commit()

    if not verified:
        return jsonify({
            'verified': False,
            'similarity_score': avg_similarity,
            'message': f'Verification failed. Similarity: {avg_similarity:.1%}, Required: {SIMILARITY_THRESHOLD:.0%}'
        }), 403

    # SUCCESS - Restore access
    # Get user account
    user = db.execute('''
        SELECT id, master_username, email, display_name
        FROM soulfra_master_users
        WHERE display_name = ?
    ''', (attempt_dict['display_name'],)).fetchone()

    user_dict = dict(user)

    # Update device fingerprint to new device
    new_device = attempt_dict['device_fingerprint']
    db.execute('''
        UPDATE soulfra_master_users
        SET device_fingerprint = ?
        WHERE id = ?
    ''', (new_device, user_dict['id']))

    db.commit()

    # Generate new JWT token
    from soulfra_master_auth import _generate_jwt_token
    token = _generate_jwt_token(user_dict['id'], user_dict['master_username'], user_dict['email'])

    return jsonify({
        'verified': True,
        'similarity_score': avg_similarity,
        'message': 'Identity verified! Access restored.',
        'token': token,
        'user': {
            'id': user_dict['id'],
            'display_name': user_dict['display_name'],
            'email': user_dict['email']
        }
    })


if __name__ == '__main__':
    init_recovery_tables()
    print("\n🔐 AI Identity Recovery System")
    print("=" * 60)
    print("When users lose access:")
    print("1. Request recovery with display name")
    print("2. Answer questions about past recordings")
    print("3. AI verifies semantic similarity")
    print("4. If verified → restore access on new device")
    print("=" * 60)

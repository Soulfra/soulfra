#!/usr/bin/env python3
"""
Kangaroo Court Routes - Simple Group Voice Chat with AI Judge

Routes:
- GET /kangaroo-court - Main room interface
- POST /kangaroo-court/submit - Submit voice memo for judgment
- GET /kangaroo-court/judge/<id> - AI judges a submission
- POST /kangaroo-court/vote/<id> - Vote on submission
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from database import get_db
from ollama_client import OllamaClient
import json
from datetime import datetime

kangaroo_bp = Blueprint('kangaroo_court', __name__)


@kangaroo_bp.route('/kangaroo-court')
def kangaroo_court():
    """Main Kangaroo Court room"""
    db = get_db()

    # Get recent submissions (last 20)
    submissions = db.execute('''
        SELECT * FROM kangaroo_submissions
        WHERE room_id = 'main'
        ORDER BY submitted_at DESC
        LIMIT 20
    ''').fetchall()

    # Get current user (or create guest)
    user_id = session.get('user_id', 1)
    user = db.execute('''
        SELECT * FROM kangaroo_users WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if not user:
        # Create guest user
        db.execute('''
            INSERT INTO kangaroo_users (user_id, username, total_credits)
            VALUES (?, ?, 0)
        ''', (user_id, f'Guest{user_id}'))
        db.commit()
        user = {'user_id': user_id, 'username': f'Guest{user_id}', 'total_credits': 0}

    # Get leaderboard
    leaderboard = db.execute('''
        SELECT username, total_credits, guilty_count, innocent_count
        FROM kangaroo_users
        ORDER BY total_credits DESC
        LIMIT 10
    ''').fetchall()

    return render_template('kangaroo_court.html',
                         submissions=submissions,
                         user=user,
                         leaderboard=leaderboard)


@kangaroo_bp.route('/kangaroo-court/submit', methods=['POST'])
def submit_to_court():
    """Submit voice memo to kangaroo court"""
    voice_memo_id = request.form.get('voice_memo_id')
    transcription = request.form.get('transcription', '')
    user_id = session.get('user_id', 1)

    db = get_db()

    # Get username
    user = db.execute('SELECT username FROM kangaroo_users WHERE user_id = ?', (user_id,)).fetchone()
    username = user['username'] if user else f'Guest{user_id}'

    # Create submission
    cursor = db.execute('''
        INSERT INTO kangaroo_submissions
        (user_id, username, voice_memo_id, transcription, room_id)
        VALUES (?, ?, ?, ?, 'main')
    ''', (user_id, username, voice_memo_id, transcription))

    submission_id = cursor.lastrowid

    # Update user stats
    db.execute('''
        UPDATE kangaroo_users
        SET submissions_count = submissions_count + 1,
            last_submission_at = datetime('now')
        WHERE user_id = ?
    ''', (user_id,))

    db.commit()

    # Trigger AI judgment
    judge_submission(submission_id)

    return redirect(url_for('kangaroo_court.kangaroo_court'))


@kangaroo_bp.route('/kangaroo-court/judge/<int:submission_id>')
def judge_submission_route(submission_id):
    """Manually trigger judgment (or re-judge)"""
    judge_submission(submission_id)
    return redirect(url_for('kangaroo_court.kangaroo_court'))


@kangaroo_bp.route('/kangaroo-court/vote/<int:submission_id>', methods=['POST'])
def vote_on_submission(submission_id):
    """Vote on a submission"""
    user_id = session.get('user_id', 1)
    db = get_db()

    try:
        # Add vote
        db.execute('''
            INSERT INTO kangaroo_votes (submission_id, voter_id)
            VALUES (?, ?)
        ''', (submission_id, user_id))

        # Update vote count
        db.execute('''
            UPDATE kangaroo_submissions
            SET votes = votes + 1
            WHERE id = ?
        ''', (submission_id,))

        # Award bonus credits to submission author
        db.execute('''
            UPDATE kangaroo_users
            SET total_credits = total_credits + 2,
                total_votes_received = total_votes_received + 1
            WHERE user_id = (SELECT user_id FROM kangaroo_submissions WHERE id = ?)
        ''', (submission_id,))

        db.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def judge_submission(submission_id):
    """Have Ollama judge a submission"""
    db = get_db()

    # Get submission
    sub = db.execute('''
        SELECT * FROM kangaroo_submissions WHERE id = ?
    ''', (submission_id,)).fetchone()

    if not sub or not sub['transcription']:
        return

    # Call Ollama
    ollama = OllamaClient()
    result = ollama.generate(
        prompt=f'''You are the judge in Kangaroo Court - a fun group chat game. Someone said:

"{sub['transcription']}"

Judge their submission. Decide if they're GUILTY or INNOCENT, and give a funny punishment or reward.

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "verdict": "GUILTY" or "INNOCENT",
  "severity": 1-10,
  "punishment": "funny punishment" or null,
  "reward": "fun reward" or null,
  "reasoning": "brief explanation"
}}''',
        model='llama3.2',
        temperature=0.9,
        max_tokens=300
    )

    # Parse response
    try:
        response_text = result['response'].strip()
        # Remove markdown code blocks if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()

        judgment = json.loads(response_text)

        # Calculate credits
        credits = 5  # Base
        if judgment.get('verdict') == 'GUILTY':
            credits += min(judgment.get('severity', 5), 10)  # More guilty = more credits

        # Update submission
        db.execute('''
            UPDATE kangaroo_submissions
            SET verdict = ?, severity = ?, punishment = ?, reward = ?,
                reasoning = ?, credits_earned = ?, judged_at = datetime('now')
            WHERE id = ?
        ''', (judgment.get('verdict', 'PENDING'),
              judgment.get('severity', 5),
              judgment.get('punishment'),
              judgment.get('reward'),
              judgment.get('reasoning', 'No reasoning provided'),
              credits,
              submission_id))

        # Update user stats and credits
        verdict_col = 'guilty_count' if judgment.get('verdict') == 'GUILTY' else 'innocent_count'
        db.execute(f'''
            UPDATE kangaroo_users
            SET total_credits = total_credits + ?,
                {verdict_col} = {verdict_col} + 1
            WHERE user_id = ?
        ''', (credits, sub['user_id']))

        db.commit()

    except json.JSONDecodeError as e:
        # Failed to parse - mark as error
        db.execute('''
            UPDATE kangaroo_submissions
            SET verdict = 'ERROR', reasoning = ?
            WHERE id = ?
        ''', (f'AI response parsing failed: {str(e)}', submission_id))
        db.commit()


def register_kangaroo_court_routes(app):
    """Register kangaroo court routes"""
    app.register_blueprint(kangaroo_bp)
    print("✅ Kangaroo Court routes registered")


if __name__ == '__main__':
    print("Kangaroo Court Routes")
    print("")
    print("Routes:")
    print("  GET  /kangaroo-court - Main room")
    print("  POST /kangaroo-court/submit - Submit voice memo")
    print("  GET  /kangaroo-court/judge/<id> - AI judgment")
    print("  POST /kangaroo-court/vote/<id> - Vote")

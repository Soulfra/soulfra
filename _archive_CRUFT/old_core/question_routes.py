#!/usr/bin/env python3
"""
Question/Reward Routes - Themed Question Rotation System

Users answer rotating questions to earn XP and rewards.
Rate limited to prevent spam (5 questions/hour default).

Routes:
- /questions - Browse questions by theme
- /questions/answer/<id> - Answer a specific question
- /api/questions/submit - Submit answer (POST)
- /api/questions/stats - Get user stats

Features:
- Themed question rotation (Water, Privacy, Tech, etc.)
- Rate limiting (5 questions/hour)
- XP rewards (+10 per answer)
- Level progression
- QR authentication required
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import get_db
from rate_limiter import can_answer_question, record_question_answer, get_user_stats, format_time_remaining
from rotation_helpers import get_rotation_context
from datetime import datetime

question_bp = Blueprint('questions', __name__)


@question_bp.route('/questions')
def question_browser():
    """
    Browse available questions by theme

    Requires QR authentication
    Shows rate limit status and themed questions
    """
    # Check if user has valid QR auth session
    search_token = session.get('search_token')

    if not search_token:
        return redirect(url_for('login_qr') + '?redirect=/questions')

    # Validate session token
    db = get_db()
    session_data = db.execute('''
        SELECT * FROM search_sessions
        WHERE session_token = ?
        AND expires_at > datetime('now')
    ''', (search_token,)).fetchone()

    if not session_data:
        db.close()
        session.pop('search_token', None)
        return redirect(url_for('login_qr') + '?redirect=/questions')

    # Get or create user_id
    user_id = session.get('user_id')

    if not user_id:
        import secrets

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (f'qr_user_{secrets.token_hex(4)}', f'qr_{secrets.token_hex(4)}@temp.com', 'qr-authenticated'))

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()

    # Check rate limit
    can_answer, remaining, seconds_until_reset = can_answer_question(user_id)

    # Get user stats
    stats = get_user_stats(user_id)

    # Get all available question themes
    themes = db.execute('''
        SELECT DISTINCT theme FROM voice_questions
        WHERE active = 1
        ORDER BY theme
    ''').fetchall()

    # Get questions grouped by theme
    questions_by_theme = {}

    for theme_row in themes:
        theme = theme_row['theme']

        questions = db.execute('''
            SELECT id, question_text, theme, difficulty, xp_reward
            FROM voice_questions
            WHERE theme = ? AND active = 1
            ORDER BY difficulty, id
            LIMIT 10
        ''', (theme,)).fetchall()

        questions_by_theme[theme] = [dict(q) for q in questions]

    db.close()

    # Format time remaining
    time_remaining_str = None
    if seconds_until_reset:
        time_remaining_str = format_time_remaining(seconds_until_reset)

    return render_template('questions.html',
        can_answer=can_answer,
        remaining=remaining,
        seconds_until_reset=seconds_until_reset,
        time_remaining_str=time_remaining_str,
        stats=stats,
        themes=themes,
        questions_by_theme=questions_by_theme,
        session_expires=session_data['expires_at']
    )


@question_bp.route('/questions/answer/<int:question_id>')
def answer_question(question_id):
    """
    Answer a specific question

    Args:
        question_id: Question ID

    Requires QR auth and rate limit check
    """
    # Check if user has valid QR auth session
    search_token = session.get('search_token')

    if not search_token:
        return redirect(url_for('login_qr') + '?redirect=/questions')

    # Validate session token
    db = get_db()
    session_data = db.execute('''
        SELECT * FROM search_sessions
        WHERE session_token = ?
        AND expires_at > datetime('now')
    ''', (search_token,)).fetchone()

    if not session_data:
        db.close()
        session.pop('search_token', None)
        return redirect(url_for('login_qr') + '?redirect=/questions')

    user_id = session.get('user_id')

    if not user_id:
        db.close()
        return redirect('/questions')

    # Check rate limit
    can_answer, remaining, seconds_until_reset = can_answer_question(user_id)

    if not can_answer:
        db.close()
        time_str = format_time_remaining(seconds_until_reset) if seconds_until_reset else "soon"
        return render_template('error.html',
            error='Rate limit reached',
            message=f"You've answered your limit of questions. Try again in {time_str}."
        )

    # Get question details
    question = db.execute('''
        SELECT id, question_text, theme, difficulty, xp_reward
        FROM voice_questions
        WHERE id = ? AND active = 1
    ''', (question_id,)).fetchone()

    if not question:
        db.close()
        return render_template('error.html',
            error='Question not found',
            message='This question does not exist or is no longer available.'
        )

    # Check if already answered
    already_answered = db.execute('''
        SELECT id FROM user_question_answers
        WHERE user_id = ? AND question_id = ?
    ''', (user_id, question_id)).fetchone()

    db.close()

    # Get user stats
    stats = get_user_stats(user_id)

    return render_template('question_answer.html',
        question=dict(question),
        already_answered=already_answered is not None,
        remaining=remaining,
        stats=stats
    )


@question_bp.route('/api/questions/submit', methods=['POST'])
def submit_answer():
    """
    Submit answer to a question

    POST body:
    {
        "question_id": 123,
        "answer_text": "user's answer"
    }

    Returns:
    {
        "success": true,
        "xp_earned": 10,
        "new_level": 3,
        "remaining": 4,
        "stats": {...}
    }
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    question_id = data.get('question_id')
    answer_text = data.get('answer_text', '').strip()

    if not question_id or not answer_text:
        return jsonify({'error': 'Missing question_id or answer_text'}), 400

    # Check rate limit
    can_answer, remaining, seconds_until_reset = can_answer_question(user_id)

    if not can_answer:
        time_str = format_time_remaining(seconds_until_reset) if seconds_until_reset else "soon"
        return jsonify({
            'error': 'Rate limit reached',
            'message': f'Try again in {time_str}',
            'remaining': 0,
            'seconds_until_reset': seconds_until_reset
        }), 429

    # Get question to determine XP reward
    db = get_db()
    question = db.execute('''
        SELECT xp_reward FROM voice_questions WHERE id = ? AND active = 1
    ''', (question_id,)).fetchone()

    if not question:
        db.close()
        return jsonify({'error': 'Question not found'}), 404

    xp_reward = question['xp_reward'] or 10

    # Store answer in database
    db.execute('''
        INSERT INTO voice_answers (user_id, question_id, answer_text, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, question_id, answer_text, datetime.now().isoformat()))
    db.commit()
    db.close()

    # Record answer and award XP
    success = record_question_answer(user_id, question_id, xp_reward)

    if not success:
        return jsonify({'error': 'Failed to record answer'}), 500

    # Get updated stats
    stats = get_user_stats(user_id)

    # Check remaining after this answer
    can_answer_more, remaining_after, _ = can_answer_question(user_id)

    return jsonify({
        'success': True,
        'xp_earned': xp_reward,
        'new_level': stats['level'],
        'total_xp': stats['total_xp'],
        'remaining': remaining_after,
        'stats': stats
    })


@question_bp.route('/api/questions/stats')
def get_stats_api():
    """
    Get user's question stats

    Returns:
    {
        "level": 3,
        "total_xp": 320,
        "total_answered": 32,
        "xp_to_next_level": 80,
        "can_answer": true,
        "remaining": 3
    }
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    stats = get_user_stats(user_id)
    can_answer, remaining, seconds_until_reset = can_answer_question(user_id)

    return jsonify({
        **stats,
        'can_answer': can_answer,
        'remaining': remaining,
        'seconds_until_reset': seconds_until_reset
    })


@question_bp.route('/questions/voice/<int:question_id>')
def answer_question_voice(question_id):
    """
    Answer a question with voice recording

    Args:
        question_id: Question ID

    Shows voice recorder interface for answering question
    Requires QR auth and rate limit check
    """
    # Check if user has valid QR auth session
    search_token = session.get('search_token')

    if not search_token:
        return redirect(url_for('login_qr') + '?redirect=/questions')

    # Validate session token
    db = get_db()
    session_data = db.execute('''
        SELECT * FROM search_sessions
        WHERE session_token = ?
        AND expires_at > datetime('now')
    ''', (search_token,)).fetchone()

    if not session_data:
        db.close()
        session.pop('search_token', None)
        return redirect(url_for('login_qr') + '?redirect=/questions')

    user_id = session.get('user_id')

    if not user_id:
        db.close()
        return redirect('/questions')

    # Check rate limit
    can_answer, remaining, seconds_until_reset = can_answer_question(user_id)

    if not can_answer:
        db.close()
        time_str = format_time_remaining(seconds_until_reset) if seconds_until_reset else "soon"
        return render_template('error.html',
            error='Rate limit reached',
            message=f"You've answered your limit of questions. Try again in {time_str}."
        )

    # Get question details
    question = db.execute('''
        SELECT id, question_text, theme, difficulty, xp_reward
        FROM voice_questions
        WHERE id = ? AND active = 1
    ''', (question_id,)).fetchone()

    if not question:
        db.close()
        return render_template('error.html',
            error='Question not found',
            message='This question does not exist or is no longer available.'
        )

    # Check if already answered
    already_answered = db.execute('''
        SELECT id FROM user_question_answers
        WHERE user_id = ? AND question_id = ?
    ''', (user_id, question_id)).fetchone()

    db.close()

    # Get user stats
    stats = get_user_stats(user_id)

    return render_template('question_voice.html',
        question=dict(question),
        already_answered=already_answered is not None,
        remaining=remaining,
        stats=stats,
        user_id=user_id
    )


@question_bp.route('/api/questions/submit-voice', methods=['POST'])
def submit_voice_answer():
    """
    Submit voice answer to a question

    Expects multipart form data:
    - question_id: int
    - audio: file (webm)

    Flow:
    1. Save audio to database
    2. Transcribe with Whisper
    3. Analyze quality with Ollama
    4. Award XP (base + quality bonus)
    5. Return results

    Returns:
    {
        "success": true,
        "recording_id": 123,
        "transcription": "...",
        "quality_score": 85,
        "xp_earned": 25,
        "xp_breakdown": {
            "base": 10,
            "quality_bonus": 15
        },
        "new_level": 3,
        "stats": {...}
    }
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    question_id = request.form.get('question_id')

    if not question_id:
        return jsonify({'error': 'Missing question_id'}), 400

    try:
        question_id = int(question_id)
    except:
        return jsonify({'error': 'Invalid question_id'}), 400

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'error': 'Empty audio file'}), 400

    # Check rate limit
    can_answer, remaining, seconds_until_reset = can_answer_question(user_id)

    if not can_answer:
        time_str = format_time_remaining(seconds_until_reset) if seconds_until_reset else "soon"
        return jsonify({
            'error': 'Rate limit reached',
            'message': f'Try again in {time_str}',
            'remaining': 0,
            'seconds_until_reset': seconds_until_reset
        }), 429

    # Get question to determine base XP reward
    db = get_db()
    question = db.execute('''
        SELECT xp_reward FROM voice_questions WHERE id = ? AND active = 1
    ''', (question_id,)).fetchone()

    if not question:
        db.close()
        return jsonify({'error': 'Question not found'}), 404

    base_xp = question['xp_reward'] or 10

    # Save voice recording
    import tempfile
    from datetime import datetime

    filename = f"question_{question_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

    # Try to transcribe with Whisper
    transcription = None
    transcription_method = None

    try:
        from whisper_transcriber import WhisperTranscriber

        # Save audio to temp file for transcription
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        # Transcribe
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(tmp_path)

        transcription = result['text']
        transcription_method = result['backend']

        # Clean up temp file
        import os
        os.unlink(tmp_path)

    except Exception as e:
        print(f"⚠️  Transcription failed: {e}")
        # Continue without transcription

    # Save to database
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, len(audio_data), transcription, transcription_method, user_id))

    recording_id = cursor.lastrowid
    db.commit()

    # Analyze answer quality with Ollama if we have transcription
    quality_score = 50  # Default
    quality_bonus_xp = 0

    if transcription:
        try:
            from voice_ollama_processor import VoiceOllamaProcessor

            processor = VoiceOllamaProcessor()
            analysis = processor.analyze_recording(recording_id)

            if 'quality_score' in analysis and 'error' not in analysis:
                quality_score = analysis['quality_score']

                # Award bonus XP based on quality (0-15 bonus)
                # 80+ score = +15 XP
                # 60-79 score = +10 XP
                # 40-59 score = +5 XP
                # <40 score = +0 XP
                if quality_score >= 80:
                    quality_bonus_xp = 15
                elif quality_score >= 60:
                    quality_bonus_xp = 10
                elif quality_score >= 40:
                    quality_bonus_xp = 5

        except Exception as e:
            print(f"⚠️  Quality analysis failed: {e}")

    total_xp = base_xp + quality_bonus_xp

    # Store answer in database
    db.execute('''
        INSERT INTO voice_answers (user_id, question_id, answer_text, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, question_id, transcription or '[Voice answer - no transcription]', datetime.now().isoformat()))
    db.commit()
    db.close()

    # Record answer and award XP
    success = record_question_answer(user_id, question_id, total_xp)

    if not success:
        return jsonify({'error': 'Failed to record answer'}), 500

    # Get updated stats
    stats = get_user_stats(user_id)

    # Check remaining after this answer
    can_answer_more, remaining_after, _ = can_answer_question(user_id)

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'transcription': transcription,
        'quality_score': quality_score,
        'xp_earned': total_xp,
        'xp_breakdown': {
            'base': base_xp,
            'quality_bonus': quality_bonus_xp
        },
        'new_level': stats['level'],
        'total_xp': stats['total_xp'],
        'remaining': remaining_after,
        'stats': stats
    })


def register_question_routes(app):
    """Register question blueprint with Flask app"""
    app.register_blueprint(question_bp)
    print("✅ Registered question routes:")
    print("   - /questions (Browse themed questions)")
    print("   - /questions/answer/<id> (Answer question with text)")
    print("   - /questions/voice/<id> (Answer question with voice)")
    print("   - /api/questions/submit (Submit text answer)")
    print("   - /api/questions/submit-voice (Submit voice answer + AI analysis)")
    print("   - /api/questions/stats (Get user stats)")

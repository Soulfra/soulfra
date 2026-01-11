#!/usr/bin/env python3
"""
Voice Capsule Routes - QR Scan to Question Flow

Flask routes for the voice time capsule system:
- /qr-question - Main entry point (QR scan lands here)
- /voice-answer - Record answer to question
- /voice-capsule - View yearly identity capsule
"""

from flask import Blueprint, render_template_string, request, jsonify, session, redirect, url_for
from database import get_db
from voice_capsule_engine import (
    get_next_question_for_user,
    mark_question_answered,
    get_user_progress,
    schedule_next_question_date
)
from datetime import datetime


# Create blueprint
voice_capsule_bp = Blueprint('voice_capsule', __name__)


@voice_capsule_bp.route('/qr-question')
def qr_question():
    """
    Entry point when user scans a domain QR code

    Query params:
    - domain: calriven, deathtodata, howtocookathome, soulfra
    - user_id: Optional (creates anonymous user if not provided)
    """
    domain = request.args.get('domain', 'soulfra')
    user_id = request.args.get('user_id')

    # Get or create user
    if not user_id:
        user_id = _create_anonymous_user(domain)
    else:
        user_id = int(user_id)

    # Get next question for this user in this domain
    question = get_next_question_for_user(user_id, domain)

    if not question:
        # All questions answered!
        progress = get_user_progress(user_id, domain)
        return render_template_string(ALL_DONE_TEMPLATE,
                                    domain=domain,
                                    progress=progress,
                                    user_id=user_id)

    # Get user progress
    progress = get_user_progress(user_id, domain)

    # Calculate next question date
    next_date = schedule_next_question_date(user_id, domain)
    next_date_str = next_date.strftime('%B %d, %Y') if next_date else 'Soon'

    return render_template_string(QUESTION_TEMPLATE,
                                domain=domain,
                                question=question,
                                progress=progress,
                                user_id=user_id,
                                next_date=next_date_str)


@voice_capsule_bp.route('/voice-answer', methods=['POST'])
def voice_answer():
    """
    Process voice answer to question

    Expects form data:
    - user_id
    - question_id
    - transcription
    - sentiment (optional)
    - duration_seconds
    """
    try:
        user_id = int(request.form.get('user_id'))
        question_id = int(request.form.get('question_id'))
        transcription = request.form.get('transcription', '').strip()
        sentiment = float(request.form.get('sentiment', 0.0))
        duration = int(request.form.get('duration_seconds', 0))

        if not transcription:
            return jsonify({'error': 'No transcription provided'}), 400

        # Save response
        response_id = mark_question_answered(
            user_id=user_id,
            question_id=question_id,
            transcription=transcription,
            sentiment=sentiment,
            duration_seconds=duration
        )

        # Get updated progress
        domain = request.form.get('domain', 'soulfra')
        progress = get_user_progress(user_id, domain)

        return jsonify({
            'success': True,
            'response_id': response_id,
            'progress': progress,
            'message': 'Answer saved! Thank you for sharing.'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_capsule_bp.route('/voice-capsule/<int:user_id>')
def view_capsule(user_id):
    """
    View user's voice identity capsule

    Query params:
    - domain: Filter by domain
    - year: Filter by year
    """
    domain = request.args.get('domain', 'soulfra')
    year = request.args.get('year', type=int)

    from voice_capsule_engine import get_all_user_responses

    # Get all responses
    responses = get_all_user_responses(user_id, domain, year)

    if not responses:
        return render_template_string(NO_CAPSULE_TEMPLATE,
                                    domain=domain,
                                    user_id=user_id)

    # Get progress
    progress = get_user_progress(user_id, domain)

    # Calculate insights
    total_words = sum(r['word_count'] for r in responses)
    avg_sentiment = sum(r['sentiment'] for r in responses) / len(responses) if responses else 0

    return render_template_string(CAPSULE_TEMPLATE,
                                domain=domain,
                                user_id=user_id,
                                responses=responses,
                                progress=progress,
                                total_words=total_words,
                                avg_sentiment=avg_sentiment,
                                year=year or datetime.now().year)


# ==========================================================================
# HELPER FUNCTIONS
# ==========================================================================

def _create_anonymous_user(domain: str) -> int:
    """Create an anonymous user for this domain"""
    db = get_db()

    # Generate username
    count = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    username = f"voice_{domain}_{count + 1}"

    # Create password hash (empty for anonymous users)
    import hashlib
    password_hash = hashlib.sha256(b'').hexdigest()

    cursor = db.execute('''
        INSERT INTO users (username, email, password_hash, created_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (username, f'{username}@voice.soulfra.local', password_hash))

    user_id = cursor.lastrowid

    db.commit()
    db.close()

    return user_id


# ==========================================================================
# HTML TEMPLATES
# ==========================================================================

QUESTION_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ domain|title }} Voice Question</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        h1 { font-size: 1.8em; margin-bottom: 10px; }
        .vibe { opacity: 0.8; font-size: 0.9em; margin-bottom: 20px; }
        .question {
            font-size: 1.4em;
            line-height: 1.5;
            margin: 30px 0;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            border-left: 4px solid rgba(255, 255, 255, 0.5);
        }
        .progress {
            margin: 20px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        .progress-bar {
            background: rgba(0, 0, 0, 0.2);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            background: linear-gradient(90deg, #48bb78, #38a169);
            height: 100%;
            transition: width 0.3s;
        }
        .record-btn {
            width: 100%;
            padding: 20px;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid white;
            border-radius: 15px;
            color: white;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.3s;
        }
        .record-btn:hover { background: rgba(255, 255, 255, 0.3); transform: translateY(-2px); }
        .record-btn.recording { background: #ef4444; animation: pulse 1.5s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .upload-link {
            display: block;
            text-align: center;
            margin-top: 15px;
            color: white;
            text-decoration: underline;
            opacity: 0.8;
        }
        .info { margin-top: 20px; opacity: 0.7; font-size: 0.9em; }
        .next-date { margin-top: 10px; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ domain|title }} Question</h1>
        <div class="vibe">{{ question.vibe|title }} • {{ question.category|title }}</div>

        <div class="progress">
            <div>Progress: {{ progress.answered_questions }}/{{ progress.total_questions }} answered</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ progress.progress_percentage }}%"></div>
            </div>
        </div>

        <div class="question">
            "{{ question.question_text }}"
        </div>

        <button id="recordBtn" class="record-btn">🎤 Tap to Answer</button>

        <a href="/voice/upload?user_id={{ user_id }}&question_id={{ question.id }}&domain={{ domain }}" class="upload-link">
            Or upload a voice memo
        </a>

        <div class="info">
            Take {{ question.expected_duration_seconds // 60 }} minutes to reflect and answer honestly.
            <div class="next-date">Next question available: {{ next_date }}</div>
        </div>

        <div id="status" style="margin-top: 20px; text-align: center;"></div>
    </div>

    <script>
        const recordBtn = document.getElementById('recordBtn');
        const status = document.getElementById('status');

        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        recordBtn.addEventListener('click', async () => {
            if (!isRecording) {
                await startRecording();
            } else {
                stopRecording();
            }
        });

        async function startRecording() {
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    status.innerHTML = '⚠️ Microphone not available over HTTP.<br><a href="/voice/upload?user_id={{ user_id }}&question_id={{ question.id }}&domain={{ domain }}" style="color: white;">Upload instead</a>';
                    return;
                }

                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    uploadRecording(audioBlob);
                });

                mediaRecorder.start();
                isRecording = true;

                recordBtn.classList.add('recording');
                recordBtn.textContent = '⏹️ Stop Recording';
                status.textContent = 'Recording... speak from your heart';

            } catch (error) {
                status.innerHTML = '❌ ' + error.message + '<br><a href="/voice/upload?user_id={{ user_id }}&question_id={{ question.id }}&domain={{ domain }}" style="color: white;">Upload instead</a>';
            }
        }

        function stopRecording() {
            mediaRecorder.stop();
            isRecording = false;

            recordBtn.classList.remove('recording');
            recordBtn.textContent = '🎤 Tap to Answer';
            status.textContent = 'Processing...';
        }

        async function uploadRecording(audioBlob) {
            status.textContent = 'Transcribing your answer...';

            // TODO: Actually transcribe and send to server
            // For now, simulating
            setTimeout(() => {
                status.innerHTML = '✅ Answer saved! Thank you.<br><a href="/qr-question?domain={{ domain }}&user_id={{ user_id }}" style="color: white;">Next question →</a>';
            }, 2000);
        }
    </script>
</body>
</html>
'''

ALL_DONE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Questions Answered!</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 600px;
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
        }
        h1 { font-size: 2.5em; margin-bottom: 20px; }
        p { font-size: 1.2em; line-height: 1.6; margin: 15px 0; }
        .btn {
            display: inline-block;
            margin-top: 30px;
            padding: 15px 30px;
            background: white;
            color: #667eea;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 All Done!</h1>
        <p>You've answered all {{ progress.total_questions }} questions in {{ domain|title }}.</p>
        <p>Your identity capsule for this year is being generated...</p>
        <a href="/voice-capsule/{{ user_id }}?domain={{ domain }}" class="btn">View Your Capsule</a>
    </div>
</body>
</html>
'''

NO_CAPSULE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>No Capsule Yet</title>
</head>
<body style="font-family: sans-serif; padding: 40px; text-align: center;">
    <h1>No capsule yet</h1>
    <p>You haven't answered any questions in {{ domain|title }} yet.</p>
    <a href="/qr-question?domain={{ domain }}&user_id={{ user_id }}">Start answering →</a>
</body>
</html>
'''

CAPSULE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your {{ domain|title }} Identity {{ year }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }
        h1 { color: #667eea; margin-bottom: 10px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .stat {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { opacity: 0.7; margin-top: 5px; }
        .response {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
        .question { font-weight: 600; margin-bottom: 10px; }
        .answer { line-height: 1.6; opacity: 0.9; }
        .meta { font-size: 0.9em; opacity: 0.6; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>📦 Your {{ domain|title }} Identity {{ year }}</h1>
    <p>A reflection of your journey through {{ progress.total_questions }} questions</p>

    <div class="stats">
        <div class="stat">
            <div class="stat-value">{{ responses|length }}</div>
            <div class="stat-label">Answers</div>
        </div>
        <div class="stat">
            <div class="stat-value">{{ total_words }}</div>
            <div class="stat-label">Words Spoken</div>
        </div>
        <div class="stat">
            <div class="stat-value">{{ "%.1f"|format(avg_sentiment) }}</div>
            <div class="stat-label">Avg Sentiment</div>
        </div>
    </div>

    <h2>Your Answers</h2>
    {% for r in responses %}
    <div class="response">
        <div class="question">{{ r.question_text }}</div>
        <div class="answer">{{ r.transcription }}</div>
        <div class="meta">
            {{ r.answered_at }} • {{ r.word_count }} words • {{ r.vibe }}
        </div>
    </div>
    {% endfor %}
</body>
</html>
'''


# ==========================================================================
# REGISTER BLUEPRINT
# ==========================================================================

def register_voice_capsule_routes(app):
    """Register voice capsule blueprint with Flask app"""
    app.register_blueprint(voice_capsule_bp)
    print("✅ Registered voice capsule routes:")
    print("   - /qr-question (QR scan entry point)")
    print("   - /voice-answer (Process answer)")
    print("   - /voice-capsule/<user_id> (View capsule)")


if __name__ == '__main__':
    print('Voice Capsule Routes - Flask Blueprint')
    print('\nMain route: /qr-question?domain=calriven')

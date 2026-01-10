#!/usr/bin/env python3
"""
Public Voice Submission - No Login Required

Anyone can submit voice memos for AI processing:
- Record voice memo via browser (WebRTC)
- AI processes (Whisper transcription + Ollama extraction)
- Returns shareable link
- Optional encryption (QR code for privacy)
- Spam protection via rate limiting

Use cases:
- AI complaint hotline (people send voice complaints)
- Voice feedback form
- Anonymous voice suggestions
- Community voice discussions
"""

from flask import Blueprint, request, jsonify, render_template_string
from database import get_db
from voice_encryption import encrypt_voice_memo, hash_access_key, create_qr_access_data
import secrets
import json
from datetime import datetime, timedelta
from config import BASE_URL
import hashlib
import time

public_voice_bp = Blueprint('public_voice', __name__)

# Rate limiting (simple in-memory store)
_rate_limit_store = {}
MAX_SUBMISSIONS_PER_HOUR = 10
MAX_SUBMISSIONS_PER_DAY = 50


def _get_client_id():
    """Get unique identifier for rate limiting (IP + User-Agent hash)"""
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    return hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()[:16]


def _check_rate_limit(client_id: str) -> tuple[bool, str]:
    """
    Check if client has exceeded rate limits

    Returns:
        (allowed: bool, reason: str)
    """
    now = time.time()

    # Clean up old entries
    cutoff_day = now - 86400  # 24 hours
    cutoff_hour = now - 3600  # 1 hour

    if client_id not in _rate_limit_store:
        _rate_limit_store[client_id] = []

    # Filter out old submissions
    _rate_limit_store[client_id] = [
        ts for ts in _rate_limit_store[client_id]
        if ts > cutoff_day
    ]

    # Check hourly limit
    hour_count = sum(1 for ts in _rate_limit_store[client_id] if ts > cutoff_hour)
    if hour_count >= MAX_SUBMISSIONS_PER_HOUR:
        return False, f"Rate limit exceeded: {MAX_SUBMISSIONS_PER_HOUR} submissions per hour"

    # Check daily limit
    day_count = len(_rate_limit_store[client_id])
    if day_count >= MAX_SUBMISSIONS_PER_DAY:
        return False, f"Rate limit exceeded: {MAX_SUBMISSIONS_PER_DAY} submissions per day"

    return True, ""


@public_voice_bp.route('/submit', methods=['GET'])
def submit_page():
    """Public voice submission page"""
    return render_template_string(SUBMIT_TEMPLATE)


@public_voice_bp.route('/api/submit-voice', methods=['POST'])
def submit_voice():
    """
    Public endpoint for voice memo submission

    POST /api/submit-voice
    - audio: File (WebM, MP3, etc.)
    - encrypt: Boolean (optional, default false)
    - category: String (optional: "complaint", "feedback", "idea", "other")
    - anonymous: Boolean (optional, default true)
    """
    # Rate limiting
    client_id = _get_client_id()
    allowed, reason = _check_rate_limit(client_id)
    if not allowed:
        return jsonify({
            'success': False,
            'error': reason,
            'retry_after': 3600  # seconds
        }), 429

    # Validate audio upload
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'Empty file'}), 400

    # Options
    encrypt = request.form.get('encrypt', 'false').lower() == 'true'
    category = request.form.get('category', 'other')
    anonymous = request.form.get('anonymous', 'true').lower() == 'true'

    # Read audio
    audio_data = audio_file.read()

    # Validate size (max 10MB)
    if len(audio_data) > 10 * 1024 * 1024:
        return jsonify({'success': False, 'error': 'File too large (max 10MB)'}), 400

    # Generate memo ID
    memo_id = secrets.token_urlsafe(16)

    try:
        db = get_db()

        if encrypt:
            # Encrypted submission (private, needs QR code)
            result = encrypt_voice_memo(audio_data)
            key_hash = hash_access_key(result['key'])

            # Create QR access data
            domain = BASE_URL.replace('http://', '').replace('https://', '').split(':')[0]
            qr_data = create_qr_access_data(memo_id, result['key_b64'], domain)

            # Store encrypted
            metadata = {
                'source': 'public_submission',
                'category': category,
                'anonymous': anonymous,
                'encrypted': True,
                'qr_access': qr_data,
                'client_id': client_id if not anonymous else None,
                'submitted_at': datetime.now().isoformat()
            }

            db.execute('''
                INSERT INTO voice_memos (
                    id, user_id, domain, encrypted_audio, encryption_iv, access_key_hash,
                    file_size_bytes, audio_format, access_type, federation_shared, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memo_id,
                None,  # Public submission (no user)
                domain,
                result['encrypted_data'],
                result['iv_b64'],
                key_hash,
                len(audio_data),
                'audio/webm',
                'qr',
                1,  # Federation enabled
                json.dumps(metadata)
            ))

            db.commit()

            # Record rate limit
            _rate_limit_store[client_id].append(time.time())

            return jsonify({
                'success': True,
                'memo_id': memo_id,
                'encrypted': True,
                'qr_access': qr_data,
                'share_url': f"{BASE_URL}/voice/{memo_id}",
                'message': 'Voice memo submitted! Save the QR code to access it.'
            })

        else:
            # Public submission (not encrypted, anyone can listen)
            # Save audio as-is
            audio_filename = f"public_{memo_id}.webm"
            audio_path = f"voice_recordings/{audio_filename}"

            # Write to disk
            with open(audio_path, 'wb') as f:
                f.write(audio_data)

            # Store in simple_voice_recordings table
            metadata = {
                'source': 'public_submission',
                'category': category,
                'anonymous': anonymous,
                'encrypted': False,
                'client_id': client_id if not anonymous else None,
                'submitted_at': datetime.now().isoformat()
            }

            db.execute('''
                INSERT INTO simple_voice_recordings (
                    filename, transcription, transcription_method, metadata, created_at
                ) VALUES (?, ?, ?, ?, datetime('now'))
            ''', (
                audio_path,
                None,  # Will be transcribed by Whisper
                'pending_whisper',
                json.dumps(metadata)
            ))

            recording_id = db.lastrowid
            db.commit()

            # Record rate limit
            _rate_limit_store[client_id].append(time.time())

            return jsonify({
                'success': True,
                'recording_id': recording_id,
                'memo_id': memo_id,
                'encrypted': False,
                'share_url': f"{BASE_URL}/voice/public/{recording_id}",
                'message': 'Voice memo submitted! AI will process it shortly.',
                'processing': True
            })

    except Exception as e:
        print(f"❌ Error submitting voice memo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@public_voice_bp.route('/voice/public/<int:recording_id>', methods=['GET'])
def view_public_voice(recording_id):
    """View public (non-encrypted) voice submission with AI processing"""
    db = get_db()

    recording = db.execute('''
        SELECT * FROM simple_voice_recordings WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return "Voice memo not found", 404

    metadata = json.loads(recording['metadata']) if recording['metadata'] else {}

    # Check if this is a public submission
    if metadata.get('source') != 'public_submission':
        return "Not a public submission", 403

    # Render page with audio player + AI results
    return render_template_string(PUBLIC_VOICE_VIEW_TEMPLATE, recording=recording, metadata=metadata)


# HTML Templates

SUBMIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit Voice Memo - AI Processing</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .container {
            background: white;
            border-radius: 20px;
            padding: 3rem;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #333;
        }

        .subtitle {
            color: #666;
            margin-bottom: 2rem;
            font-size: 1rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }

        select, input[type="checkbox"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .checkbox-group input[type="checkbox"] {
            width: auto;
        }

        .record-btn {
            width: 100%;
            padding: 1.5rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 1rem;
        }

        .record-btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .record-btn:active {
            transform: translateY(0);
        }

        .record-btn.recording {
            background: #ef4444;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .status {
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            display: none;
        }

        .status.success {
            background: #d1fae5;
            color: #065f46;
            display: block;
        }

        .status.error {
            background: #fee2e2;
            color: #991b1b;
            display: block;
        }

        .status.info {
            background: #dbeafe;
            color: #1e40af;
            display: block;
        }

        .share-link {
            margin-top: 1rem;
            padding: 1rem;
            background: #f3f4f6;
            border-radius: 8px;
            word-break: break-all;
        }

        .share-link a {
            color: #667eea;
            font-weight: 600;
        }

        .timer {
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            color: #ef4444;
            margin: 1rem 0;
            display: none;
        }

        .info-box {
            background: #f9fafb;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin-top: 2rem;
            font-size: 0.9rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Submit Voice Memo</h1>
        <p class="subtitle">AI will transcribe and extract insights from your recording</p>

        <div class="form-group">
            <label for="category">Category</label>
            <select id="category">
                <option value="complaint">💢 Complaint</option>
                <option value="feedback">💭 Feedback</option>
                <option value="idea">💡 Idea</option>
                <option value="other">📝 Other</option>
            </select>
        </div>

        <div class="form-group checkbox-group">
            <input type="checkbox" id="encrypt">
            <label for="encrypt">🔒 Encrypt (requires QR code to access)</label>
        </div>

        <div class="form-group checkbox-group">
            <input type="checkbox" id="anonymous" checked>
            <label for="anonymous">🕵️ Submit anonymously</label>
        </div>

        <button id="recordBtn" class="record-btn">🎙️ Start Recording</button>

        <div id="timer" class="timer">00:00</div>

        <div id="status" class="status"></div>

        <div class="info-box">
            <strong>How it works:</strong><br>
            1. Click "Start Recording" and speak your message<br>
            2. Click "Stop Recording" when done<br>
            3. AI transcribes with Whisper and extracts ideas with Ollama<br>
            4. Get a shareable link to the processed recording
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let startTime;
        let timerInterval;

        const recordBtn = document.getElementById('recordBtn');
        const statusDiv = document.getElementById('status');
        const timerDiv = document.getElementById('timer');
        const categorySelect = document.getElementById('category');
        const encryptCheckbox = document.getElementById('encrypt');
        const anonymousCheckbox = document.getElementById('anonymous');

        function updateTimer() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            timerDiv.textContent = `${minutes}:${seconds}`;
        }

        function showStatus(message, type = 'info') {
            statusDiv.className = `status ${type}`;
            statusDiv.innerHTML = message;
        }

        recordBtn.addEventListener('click', async () => {
            if (!isRecording) {
                // Start recording
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        await submitVoice(audioBlob);
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    startTime = Date.now();
                    timerInterval = setInterval(updateTimer, 100);
                    timerDiv.style.display = 'block';
                    recordBtn.textContent = '⏹️ Stop Recording';
                    recordBtn.classList.add('recording');
                    showStatus('Recording... Speak now!', 'info');

                } catch (err) {
                    showStatus('❌ Microphone access denied. Please allow microphone access.', 'error');
                    console.error('Microphone error:', err);
                }

            } else {
                // Stop recording
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                isRecording = false;
                clearInterval(timerInterval);
                timerDiv.style.display = 'none';
                recordBtn.textContent = '🎙️ Start Recording';
                recordBtn.classList.remove('recording');
                showStatus('⏳ Processing...', 'info');
            }
        });

        async function submitVoice(audioBlob) {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice-memo.webm');
            formData.append('category', categorySelect.value);
            formData.append('encrypt', encryptCheckbox.checked);
            formData.append('anonymous', anonymousCheckbox.checked);

            try {
                const response = await fetch('/api/submit-voice', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    let message = `✅ ${data.message}<div class="share-link">Share: <a href="${data.share_url}" target="_blank">${data.share_url}</a></div>`;

                    if (data.encrypted && data.qr_access) {
                        message += `<div class="share-link">🔑 QR Access: ${data.qr_access}</div>`;
                    }

                    showStatus(message, 'success');
                } else {
                    showStatus(`❌ ${data.error}`, 'error');
                }

            } catch (err) {
                showStatus('❌ Upload failed. Please try again.', 'error');
                console.error('Upload error:', err);
            }
        }
    </script>
</body>
</html>
'''

PUBLIC_VOICE_VIEW_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Memo - AI Processed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 1rem;
            color: #333;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #667eea;
            color: white;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }

        .audio-player {
            margin: 2rem 0;
            width: 100%;
        }

        .section {
            margin: 2rem 0;
            padding: 1.5rem;
            background: #f9fafb;
            border-radius: 12px;
        }

        .section h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #333;
        }

        .processing {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .meta {
            color: #666;
            font-size: 0.875rem;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Voice Memo</h1>

        <div>
            <span class="badge">{{ metadata.get('category', 'other').title() }}</span>
            {% if metadata.get('anonymous') %}
            <span class="badge">Anonymous</span>
            {% endif %}
        </div>

        <div class="audio-player">
            <audio controls style="width: 100%;">
                <source src="/{{ recording['filename'] }}" type="audio/webm">
                Your browser does not support the audio element.
            </audio>
        </div>

        {% if recording['transcription'] %}
        <div class="section">
            <h2>📝 Transcription</h2>
            <p>{{ recording['transcription'] }}</p>
        </div>
        {% else %}
        <div class="section">
            <div class="processing">
                ⏳ AI transcription in progress...<br>
                <small>Refresh in a few seconds</small>
            </div>
        </div>
        {% endif %}

        <div class="meta">
            Submitted: {{ recording['created_at'] }}
        </div>
    </div>
</body>
</html>
'''


def register_public_voice_routes(app):
    """Register public voice submission routes"""
    app.register_blueprint(public_voice_bp)
    print('🌐 Public voice submission routes registered')
    print('   Submit: /submit')
    print('   API: /api/submit-voice')
    print('   View: /voice/public/<id>')

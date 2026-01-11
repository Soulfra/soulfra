#!/usr/bin/env python3
"""
Voice Federation Routes - Federated Voice Memo System

Flask routes for federated encrypted voice memos:
- /voice/record - Record and encrypt voice memo
- /voice/{memo_id} - Play voice memo (decrypts with QR key)
- /api/federation/voice/store - Store encrypted voice memo
- /api/federation/voice/fetch - Federation endpoint to fetch encrypted memo
- /api/federation/voice/qr - Generate QR code for voice memo
"""

from flask import Blueprint, request, jsonify, render_template_string, send_file, Response
from database import get_db
from voice_encryption import (
    encrypt_voice_memo,
    decrypt_voice_memo,
    key_from_base64,
    iv_from_base64,
    create_qr_access_data,
    parse_qr_access_data,
    hash_access_key,
    verify_access_key
)
import qrcode
from io import BytesIO
import base64
import secrets
from datetime import datetime, timedelta
from config import BASE_URL
import json


# Create blueprint
voice_federation_bp = Blueprint('voice_federation', __name__)


def _get_current_domain():
    """Get current domain from BASE_URL"""
    domain = BASE_URL.replace('http://', '').replace('https://', '')
    # Remove port if present
    domain = domain.split(':')[0]
    return domain


def _log_access(memo_id: str, requesting_domain: str, granted: bool, reason: str = None):
    """Log voice memo access attempt"""
    db = get_db()
    db.execute('''
        INSERT INTO voice_memo_access_log
        (memo_id, requesting_domain, requesting_ip, access_granted, access_denied_reason)
        VALUES (?, ?, ?, ?, ?)
    ''', (memo_id, requesting_domain, request.remote_addr, granted, reason))
    db.commit()


@voice_federation_bp.route('/voice/record', methods=['GET', 'POST'])
def record_voice_memo():
    """
    Record a voice memo and encrypt it

    GET: Show recording interface
    POST: Store encrypted voice memo
    """
    if request.method == 'GET':
        return render_template_string(RECORD_TEMPLATE)

    # POST: Store voice memo
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    user_id = request.form.get('user_id', 1)  # TODO: Get from session
    access_type = request.form.get('access_type', 'qr')
    expires_hours = int(request.form.get('expires_hours', 0))

    # Read audio data
    audio_data = audio_file.read()

    # Encrypt audio
    result = encrypt_voice_memo(audio_data)

    # Generate unique memo ID
    memo_id = secrets.token_urlsafe(16)

    # Calculate expiration
    expires_at = None
    if expires_hours > 0:
        expires_at = datetime.now() + timedelta(hours=expires_hours)

    # Hash the access key (don't store the key itself!)
    key_hash = hash_access_key(result['key'])

    # Store in database
    db = get_db()
    db.execute('''
        INSERT INTO voice_memos
        (id, user_id, domain, encrypted_audio, encryption_iv, access_key_hash,
         duration_seconds, file_size_bytes, audio_format, access_type,
         federation_shared, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        memo_id,
        user_id,
        _get_current_domain(),
        result['encrypted_data'],
        result['iv_b64'],
        key_hash,
        0,  # TODO: Calculate duration from audio
        len(audio_data),
        audio_file.content_type or 'audio/webm',
        access_type,
        1,  # federation_shared
        expires_at
    ))
    db.commit()

    # Create QR code data
    qr_data = create_qr_access_data(memo_id, result['key_b64'], _get_current_domain())

    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        'success': True,
        'memo_id': memo_id,
        'qr_data': qr_data,
        'qr_code_image': f'data:image/png;base64,{qr_code_base64}',
        'play_url': f"{BASE_URL}/voice/{memo_id}?key={result['key_b64']}"
    })


@voice_federation_bp.route('/voice/<memo_id>')
def play_voice_memo(memo_id):
    """
    Play a voice memo (requires key in URL or QR scan data)

    URL: /voice/{memo_id}?key={base64_key}
    """
    key_b64 = request.args.get('key')

    if not key_b64:
        return jsonify({'error': 'Access key required'}), 403

    # Get memo from database
    db = get_db()
    memo = db.execute('''
        SELECT id, domain, encrypted_audio, encryption_iv, access_key_hash,
               audio_format, expires_at, access_count
        FROM voice_memos
        WHERE id = ?
    ''', (memo_id,)).fetchone()

    if not memo:
        _log_access(memo_id, _get_current_domain(), False, 'Memo not found')
        return jsonify({'error': 'Voice memo not found'}), 404

    # Check expiration
    if memo['expires_at']:
        expires = datetime.fromisoformat(memo['expires_at'])
        if datetime.now() > expires:
            _log_access(memo_id, _get_current_domain(), False, 'Memo expired')
            return jsonify({'error': 'Voice memo has expired'}), 410

    # Verify access key
    try:
        key = key_from_base64(key_b64)
    except Exception:
        _log_access(memo_id, _get_current_domain(), False, 'Invalid key format')
        return jsonify({'error': 'Invalid access key format'}), 400

    if not verify_access_key(key, memo['access_key_hash']):
        _log_access(memo_id, _get_current_domain(), False, 'Invalid key')
        return jsonify({'error': 'Invalid access key'}), 403

    # Decrypt audio
    try:
        iv = iv_from_base64(memo['encryption_iv'])
        decrypted_audio = decrypt_voice_memo(memo['encrypted_audio'], key, iv)
    except Exception as e:
        _log_access(memo_id, _get_current_domain(), False, f'Decryption failed: {str(e)}')
        return jsonify({'error': 'Failed to decrypt audio'}), 500

    # Update access count
    db.execute('''
        UPDATE voice_memos
        SET access_count = access_count + 1,
            last_accessed_at = datetime('now')
        WHERE id = ?
    ''', (memo_id,))
    db.commit()

    # Log successful access
    _log_access(memo_id, _get_current_domain(), True)

    # Return audio file
    return Response(
        decrypted_audio,
        mimetype=memo['audio_format'] or 'audio/webm',
        headers={
            'Content-Disposition': f'inline; filename="voice_memo_{memo_id}.webm"',
            'Cache-Control': 'no-cache'
        }
    )


@voice_federation_bp.route('/api/federation/voice/fetch', methods=['POST'])
def federation_fetch_voice_memo():
    """
    Federation endpoint: Fetch encrypted voice memo from another domain

    Request JSON:
    {
        "memo_id": "abc123",
        "access_key": "base64_key",
        "requesting_domain": "calriven.com"
    }

    Returns encrypted audio + IV for local decryption
    """
    data = request.get_json()

    memo_id = data.get('memo_id')
    access_key_b64 = data.get('access_key')
    requesting_domain = data.get('requesting_domain', 'unknown')

    if not memo_id or not access_key_b64:
        return jsonify({'error': 'memo_id and access_key required'}), 400

    # Get memo from database
    db = get_db()
    memo = db.execute('''
        SELECT id, domain, encrypted_audio, encryption_iv, access_key_hash,
               audio_format, expires_at, federation_shared, trusted_domains
        FROM voice_memos
        WHERE id = ?
    ''', (memo_id,)).fetchone()

    if not memo:
        _log_access(memo_id, requesting_domain, False, 'Memo not found')
        return jsonify({'error': 'Voice memo not found'}), 404

    # Check if federation is allowed
    if not memo['federation_shared']:
        _log_access(memo_id, requesting_domain, False, 'Federation not allowed')
        return jsonify({'error': 'This memo is not available for federation'}), 403

    # Check if requesting domain is trusted
    if memo['trusted_domains']:
        trusted = json.loads(memo['trusted_domains'])
        if requesting_domain not in trusted:
            _log_access(memo_id, requesting_domain, False, 'Domain not trusted')
            return jsonify({'error': 'Requesting domain not trusted'}), 403

    # Check expiration
    if memo['expires_at']:
        expires = datetime.fromisoformat(memo['expires_at'])
        if datetime.now() > expires:
            _log_access(memo_id, requesting_domain, False, 'Memo expired')
            return jsonify({'error': 'Voice memo has expired'}), 410

    # Verify access key
    try:
        key = key_from_base64(access_key_b64)
    except Exception:
        _log_access(memo_id, requesting_domain, False, 'Invalid key format')
        return jsonify({'error': 'Invalid access key format'}), 400

    if not verify_access_key(key, memo['access_key_hash']):
        _log_access(memo_id, requesting_domain, False, 'Invalid key')
        return jsonify({'error': 'Invalid access key'}), 403

    # Log successful federation access
    _log_access(memo_id, requesting_domain, True)

    # Return encrypted audio (caller will decrypt locally)
    return jsonify({
        'success': True,
        'memo_id': memo_id,
        'encrypted_audio_b64': base64.b64encode(memo['encrypted_audio']).decode(),
        'encryption_iv': memo['encryption_iv'],
        'audio_format': memo['audio_format']
    })


@voice_federation_bp.route('/api/federation/voice/verify', methods=['POST'])
def federation_verify_access():
    """
    Verify if an access key is valid for a memo (without fetching audio)

    Request JSON:
    {
        "memo_id": "abc123",
        "access_key": "base64_key"
    }
    """
    data = request.get_json()

    memo_id = data.get('memo_id')
    access_key_b64 = data.get('access_key')

    if not memo_id or not access_key_b64:
        return jsonify({'error': 'memo_id and access_key required'}), 400

    db = get_db()
    memo = db.execute('''
        SELECT access_key_hash, expires_at
        FROM voice_memos
        WHERE id = ?
    ''', (memo_id,)).fetchone()

    if not memo:
        return jsonify({'valid': False, 'reason': 'Memo not found'})

    # Check expiration
    if memo['expires_at']:
        expires = datetime.fromisoformat(memo['expires_at'])
        if datetime.now() > expires:
            return jsonify({'valid': False, 'reason': 'Memo expired'})

    # Verify key
    try:
        key = key_from_base64(access_key_b64)
    except Exception:
        return jsonify({'valid': False, 'reason': 'Invalid key format'})

    valid = verify_access_key(key, memo['access_key_hash'])

    return jsonify({
        'valid': valid,
        'reason': None if valid else 'Invalid access key'
    })


@voice_federation_bp.route('/voice/upload', methods=['GET', 'POST'])
def upload_voice_memo():
    """
    Upload a voice memo file (no microphone access needed, works over HTTP)

    GET: Show upload form
    POST: Process uploaded file
    """
    if request.method == 'GET':
        return render_template_string(UPLOAD_TEMPLATE)

    # POST: Process uploaded file
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    user_id = request.form.get('user_id', 1)  # TODO: Get from session
    access_type = request.form.get('access_type', 'qr')
    expires_hours = int(request.form.get('expires_hours', 0))

    # Read audio data
    audio_data = audio_file.read()

    # Encrypt audio
    result = encrypt_voice_memo(audio_data)

    # Generate unique memo ID
    memo_id = secrets.token_urlsafe(16)

    # Calculate expiration
    expires_at = None
    if expires_hours > 0:
        expires_at = datetime.now() + timedelta(hours=expires_hours)

    # Hash the access key
    key_hash = hash_access_key(result['key'])

    # Store in database
    db = get_db()
    db.execute('''
        INSERT INTO voice_memos
        (id, user_id, domain, encrypted_audio, encryption_iv, access_key_hash,
         duration_seconds, file_size_bytes, audio_format, access_type,
         federation_shared, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        memo_id,
        user_id,
        _get_current_domain(),
        result['encrypted_data'],
        result['iv_b64'],
        key_hash,
        0,
        len(audio_data),
        audio_file.content_type or 'audio/m4a',
        access_type,
        1,
        expires_at
    ))
    db.commit()

    # Create QR code data
    qr_data = create_qr_access_data(memo_id, result['key_b64'], _get_current_domain())

    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        'success': True,
        'memo_id': memo_id,
        'qr_data': qr_data,
        'qr_code_image': f'data:image/png;base64,{qr_code_base64}',
        'play_url': f"{BASE_URL}/voice/{memo_id}?key={result['key_b64']}"
    })


@voice_federation_bp.route('/voice/qr/<memo_id>')
def get_voice_memo_qr(memo_id):
    """
    Generate QR code for a voice memo (requires owner verification)

    Returns QR code image
    """
    # TODO: Verify user owns this memo

    db = get_db()
    memo = db.execute('''
        SELECT id FROM voice_memos WHERE id = ?
    ''', (memo_id,)).fetchone()

    if not memo:
        return jsonify({'error': 'Voice memo not found'}), 404

    # Note: This endpoint doesn't include the key!
    # The key should only be returned when the memo is first created
    # QR codes should be generated client-side with the key

    return jsonify({
        'error': 'QR codes must be generated at creation time with the encryption key'
    }), 400


def register_voice_federation_routes(app):
    """Register voice federation routes with Flask app"""
    app.register_blueprint(voice_federation_bp)
    print("✅ Voice Federation routes registered")


# HTML Template for voice upload (works without HTTPS!)
UPLOAD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload Voice Memo - Federated</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        h1 { color: #667eea; margin-bottom: 20px; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
        }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        input[type="file"] {
            padding: 12px;
            border: 2px dashed #667eea;
            border-radius: 8px;
            width: 100%;
            margin-bottom: 15px;
        }
        .status { padding: 15px; border-radius: 8px; margin: 15px 0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .qr-code { text-align: center; margin: 20px 0; }
        .qr-code img { max-width: 300px; border: 4px solid #667eea; border-radius: 12px; }
        #resultSection { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>📤 Upload Voice Memo</h1>

            <div class="info">
                <strong>📱 iPhone Instructions:</strong><br>
                1. Open Voice Memos app<br>
                2. Record your message<br>
                3. Tap share → Save to Files<br>
                4. Come back here and upload the file
            </div>

            <div id="uploadSection">
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" id="audioFile" name="audio" accept="audio/*" required>
                    <button type="submit">🔐 Encrypt & Generate QR Code</button>
                </form>
                <div id="status"></div>
            </div>

            <div id="resultSection">
                <h2>✅ Voice Memo Created!</h2>
                <div class="qr-code">
                    <img id="qrImage" src="" alt="QR Code">
                </div>
                <p id="playUrl" style="word-break: break-all; margin: 20px 0;"></p>
                <button onclick="location.reload()">Upload Another</button>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById('audioFile');
            const file = fileInput.files[0];

            if (!file) {
                document.getElementById('status').innerHTML = '<div class="status error">Please select a file</div>';
                return;
            }

            document.getElementById('status').innerHTML = '<div class="status">⏳ Encrypting and generating QR code...</div>';

            const formData = new FormData();
            formData.append('audio', file);

            try {
                const response = await fetch('/voice/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    document.getElementById('uploadSection').style.display = 'none';
                    document.getElementById('resultSection').style.display = 'block';
                    document.getElementById('qrImage').src = data.qr_code_image;
                    document.getElementById('playUrl').innerHTML =
                        '<strong>Play URL:</strong><br>' + data.play_url +
                        '<br><br><strong>QR Data:</strong><br>' + data.qr_data;
                } else {
                    document.getElementById('status').innerHTML = '<div class="status error">Error: ' + data.error + '</div>';
                }
            } catch (error) {
                document.getElementById('status').innerHTML = '<div class="status error">Upload error: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
'''

# HTML Template for voice recording (requires HTTPS/localhost)
RECORD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Record Voice Memo - Federated</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        h1 { color: #667eea; margin-bottom: 20px; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            margin: 10px 5px;
        }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .status { padding: 15px; border-radius: 8px; margin: 15px 0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .qr-code { text-align: center; margin: 20px 0; }
        .qr-code img { max-width: 300px; border: 4px solid #667eea; border-radius: 12px; }
        #resultSection { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🎙️ Record Federated Voice Memo</h1>
            <p style="margin-bottom: 20px;">Record a voice memo that can be shared across all domains with encryption.</p>

            <div class="info" style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <strong>⚠️ Microphone recording requires HTTPS or localhost.</strong><br>
                If you're on iPhone over network: <a href="/voice/upload" style="color: #667eea; text-decoration: underline;">Use Upload Instead</a>
            </div>

            <div id="recordSection">
                <button id="recordBtn" onclick="startRecording()">🔴 Start Recording</button>
                <button id="stopBtn" onclick="stopRecording()" disabled>⏹️ Stop Recording</button>
                <div id="status"></div>
            </div>

            <div id="resultSection">
                <h2>✅ Voice Memo Created!</h2>
                <div class="qr-code">
                    <img id="qrImage" src="" alt="QR Code">
                </div>
                <p id="playUrl" style="word-break: break-all; margin: 20px 0;"></p>
                <button onclick="location.reload()">Record Another</button>
            </div>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = uploadRecording;

                mediaRecorder.start();

                document.getElementById('recordBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').innerHTML = '<div class="status success">🎙️ Recording...</div>';
            } catch (error) {
                document.getElementById('status').innerHTML = '<div class="status error">Error: ' + error.message + '</div>';
            }
        }

        function stopRecording() {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());

            document.getElementById('recordBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('status').innerHTML = '<div class="status success">⏳ Processing...</div>';
        }

        async function uploadRecording() {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            audioChunks = [];

            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice_memo.webm');

            try {
                const response = await fetch('/voice/record', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    document.getElementById('recordSection').style.display = 'none';
                    document.getElementById('resultSection').style.display = 'block';
                    document.getElementById('qrImage').src = data.qr_code_image;
                    document.getElementById('playUrl').innerHTML =
                        '<strong>Play URL:</strong><br>' + data.play_url +
                        '<br><br><strong>QR Data:</strong><br>' + data.qr_data;
                } else {
                    document.getElementById('status').innerHTML = '<div class="status error">Error: ' + data.error + '</div>';
                }
            } catch (error) {
                document.getElementById('status').innerHTML = '<div class="status error">Upload error: ' + error.message + '</div>';
            }
        }
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print("Voice Federation Routes")
    print("")
    print("Routes:")
    print("  GET/POST /voice/record - Record and encrypt voice memo")
    print("  GET      /voice/{memo_id} - Play voice memo (requires key)")
    print("  POST     /api/federation/voice/fetch - Federation fetch endpoint")
    print("  POST     /api/federation/voice/verify - Verify access key")

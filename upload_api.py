#!/usr/bin/env python3
"""
Voice Upload API - Direct Upload from Phone Browser

Endpoint: POST /api/upload-voice
- Accepts .webm files from browser recording
- Auto-transcribes with Whisper
- Auto-debates with Ollama
- Auto-publishes to GitHub Pages
- Returns GitHub Pages link

Usage:
    python3 upload_api.py
    # Server runs on http://localhost:5002
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
import tempfile
import os

# Import existing modules
from whisper_transcriber import WhisperTranscriber
from voice_to_ollama import debate_with_models, publish_debate
from publish_debates import publish_debates as publish_to_github

# Import brand router
try:
    from brand_router import detect_brand_from_prediction, get_brand_config
    BRAND_ROUTER_AVAILABLE = True
except ImportError:
    BRAND_ROUTER_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from soulfra.github.io

DATABASE_PATH = Path(__file__).parent / 'soulfra.db'


def get_or_create_device(fingerprint_data: dict) -> int:
    """
    Get or create device ID based on browser fingerprint

    Args:
        fingerprint_data: {
            'user_agent': 'Mozilla/5.0...',
            'screen_resolution': '1920x1080',
            'timezone': 'America/New_York',
            'local_storage_id': 'uuid-from-browser'
        }

    Returns:
        device_id from database
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create fingerprint hash
    fingerprint_str = f"{fingerprint_data.get('user_agent', '')}-{fingerprint_data.get('screen_resolution', '')}-{fingerprint_data.get('timezone', '')}-{fingerprint_data.get('local_storage_id', '')}"
    fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

    # Check if device exists
    cursor.execute(
        "SELECT id FROM devices WHERE fingerprint_hash = ?",
        (fingerprint_hash,)
    )
    result = cursor.fetchone()

    if result:
        device_id = result[0]
        # Update last_seen
        cursor.execute(
            "UPDATE devices SET last_seen = ? WHERE id = ?",
            (datetime.now(), device_id)
        )
    else:
        # Create new device
        device_token = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        cursor.execute("""
            INSERT INTO devices (device_id, device_token, device_type, fingerprint_hash, fingerprint_data, last_seen, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"web-{fingerprint_hash}",
            device_token,
            'web_browser',
            fingerprint_hash,
            str(fingerprint_data),
            datetime.now(),
            datetime.now()
        ))
        device_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return device_id


@app.route('/api/upload-voice', methods=['GET', 'POST'])
def upload_voice():
    """
    Upload voice recording from browser

    Request:
        - file: .webm audio file
        - fingerprint: JSON with device fingerprint

    Response:
        {
            "success": true,
            "debate_url": "https://soulfra.github.io/debates/2026-01-03-...",
            "device_id": 4729,
            "transcription": "Bitcoin will hit 100k..."
        }
    """

    # Handle GET request - show API docs
    if request.method == 'GET':
        return jsonify({
            'service': 'Soulfra Voice Upload API',
            'status': 'running',
            'version': '1.0.0',
            'endpoints': {
                'POST /api/upload-voice': 'Upload voice recording for debate',
                'GET /api/health': 'Health check',
                'GET /api/device/<id>': 'Get device info'
            },
            'usage': {
                'method': 'POST',
                'content_type': 'multipart/form-data',
                'fields': {
                    'file': '.webm audio file',
                    'fingerprint': 'JSON device fingerprint'
                }
            },
            'example_curl': "curl -X POST http://localhost:5002/api/upload-voice -F 'file=@recording.webm' -F 'fingerprint={}'",
            'recording_page': 'https://soulfra.github.io/record'
        })

    # Handle POST request - process upload
    try:
        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        audio_file = request.files['file']
        if not audio_file.filename:
            return jsonify({'error': 'Empty filename'}), 400

        # Get device fingerprint
        fingerprint_data = request.form.get('fingerprint', '{}')
        try:
            import json
            fingerprint = json.loads(fingerprint_data)
        except:
            fingerprint = {}

        # Get or create device
        device_id = get_or_create_device(fingerprint)

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        print(f"📥 Uploaded from device #{device_id}")
        print(f"🎧 Transcribing...")

        # Transcribe
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(tmp_path)
        transcription = result.get('text', '')

        if not transcription:
            os.unlink(tmp_path)
            return jsonify({'error': 'Transcription failed'}), 500

        print(f"✅ Transcription: {transcription[:100]}...")

        # Detect brand from transcription
        brand_slug = None
        brand_name = "Soulfra"  # Default
        if BRAND_ROUTER_AVAILABLE:
            brand_slug = detect_brand_from_prediction(transcription)
            brand_config = get_brand_config(brand_slug)
            brand_name = brand_config['name']
            print(f"🏷️  Routed to: {brand_name} ({brand_slug})")

        # Debate with AI (with brand routing)
        print(f"🤖 Debating with AI models...")
        responses = debate_with_models(transcription, brand_slug=brand_slug)

        if not responses:
            os.unlink(tmp_path)
            return jsonify({'error': 'AI debate failed'}), 500

        # Publish debate to markdown (with brand routing)
        print(f"📝 Publishing debate...")
        debate_file = publish_debate(transcription, responses, brand_slug=brand_slug)

        # Publish to GitHub Pages
        print(f"🚀 Publishing to GitHub Pages...")
        publish_to_github()

        # Calculate debate URL
        debate_filename = Path(debate_file).name
        debate_url = f"https://soulfra.github.io/debates/{debate_filename}"

        # Clean up temp file
        os.unlink(tmp_path)

        print(f"✅ Complete! {debate_url}")

        return jsonify({
            'success': True,
            'debate_url': debate_url,
            'brand': brand_name,
            'brand_slug': brand_slug or 'soulfra',
            'device_id': device_id,
            'transcription': transcription,
            'models_count': len(responses),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'soulfra-upload-api'
    })


@app.route('/api/device/<device_id>', methods=['GET'])
def get_device_info(device_id):
    """Get device information"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, device_type, created_at, last_seen
        FROM devices
        WHERE id = ?
    """, (device_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'Device not found'}), 404

    return jsonify({
        'device_id': result[0],
        'device_type': result[1],
        'created_at': result[2],
        'last_seen': result[3]
    })


if __name__ == '__main__':
    print("🚀 Starting Voice Upload API")
    print("📡 Endpoint: http://localhost:5002/api/upload-voice")
    print("🔧 CORS enabled for soulfra.github.io")
    print()
    app.run(host='0.0.0.0', port=5002, debug=True)

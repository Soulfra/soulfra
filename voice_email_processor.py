#!/usr/bin/env python3
"""
Voice Email Processor - Email → GitHub Pages Pipeline

Receives voice memo emails and triggers GitHub Actions workflow to:
1. Extract audio attachment
2. Transcribe with Whisper
3. Generate content hash
4. Export to voice-archive/
5. Commit and push to GitHub Pages

**Email Flow:**
```
User sends email with audio attachment
  ↓
SendGrid Inbound Parse → Webhook
  ↓
This script (Flask endpoint)
  ↓
Trigger GitHub Actions workflow
  ↓
Voice archive updated on GitHub Pages
```

**Setup:**

1. **SendGrid Inbound Parse:**
   - Go to: https://app.sendgrid.com/settings/parse
   - Create new parse webhook
   - Hostname: voice@soulfra.com
   - Destination URL: https://your-server.com/webhook/voice-email
   - POST raw MIME data

2. **GitHub Personal Access Token:**
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   export GITHUB_REPO=Soulfra/voice-archive
   ```

3. **Start server:**
   ```bash
   python3 voice_email_processor.py
   ```

**Usage:**

Send email to: `voice@soulfra.com`
- Subject: Your prediction text
- Attachment: audio.webm or audio.mp3
- Body: Optional article URL or context

**Example email:**
```
To: voice@soulfra.com
Subject: GPT-5 will be delayed until 2026
Attachment: my-prediction.webm

This is my reaction to the OpenAI announcement.
Article: https://techcrunch.com/openai-gpt5
```
"""

import os
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, Optional

# ==============================================================================
# CONFIG
# ==============================================================================

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', 'your_github_token_here')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'Soulfra/voice-archive')
GITHUB_API_URL = 'https://api.github.com'

# Webhook secret for verification
WEBHOOK_SECRET = os.environ.get('VOICE_EMAIL_SECRET', 'change-me-in-production')

# Temp storage for email attachments
TEMP_DIR = Path('./temp_voice_emails')
TEMP_DIR.mkdir(exist_ok=True)

app = Flask(__name__)


# ==============================================================================
# EMAIL PROCESSING
# ==============================================================================

def extract_audio_from_email(email_data: Dict) -> Optional[Dict]:
    """
    Extract audio attachment from SendGrid email webhook

    Args:
        email_data: Raw email data from SendGrid

    Returns:
        {
            'filename': 'audio.webm',
            'content_type': 'audio/webm',
            'data': b'...binary data...',
            'from_email': 'user@example.com',
            'subject': 'My prediction',
            'body': 'Article context...'
        }
    """
    # SendGrid Inbound Parse format
    from_email = email_data.get('from', 'unknown@example.com')
    subject = email_data.get('subject', 'Voice prediction')
    body = email_data.get('text', '')

    # Extract attachments
    attachments = email_data.get('attachments', [])

    for attachment in attachments:
        filename = attachment.get('filename', '')
        content_type = attachment.get('type', '')

        # Check if audio file
        if content_type.startswith('audio/') or filename.endswith(('.webm', '.mp3', '.wav', '.m4a')):
            return {
                'filename': filename,
                'content_type': content_type,
                'data': attachment.get('content'),  # Base64 encoded
                'from_email': from_email,
                'subject': subject,
                'body': body
            }

    return None


def save_audio_attachment(audio_data: Dict) -> Path:
    """
    Save audio attachment to temp directory

    Returns:
        Path to saved audio file
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f'{timestamp}-{audio_data["filename"]}'
    file_path = TEMP_DIR / filename

    # Decode base64 if needed
    import base64
    content = base64.b64decode(audio_data['data'])

    file_path.write_bytes(content)

    return file_path


def trigger_github_workflow(audio_url: str, subject: str, from_email: str) -> Dict:
    """
    Trigger GitHub Actions workflow via repository_dispatch

    Args:
        audio_url: URL to audio file
        subject: Email subject (prediction text)
        from_email: Sender email

    Returns:
        {'success': bool, 'workflow_id': str}
    """
    url = f'{GITHUB_API_URL}/repos/{GITHUB_REPO}/dispatches'

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    payload = {
        'event_type': 'voice-email-received',
        'client_payload': {
            'attachment_url': audio_url,
            'subject': subject,
            'from_email': from_email,
            'timestamp': datetime.now().isoformat()
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 204:
        return {'success': True, 'workflow_id': 'triggered'}
    else:
        return {'success': False, 'error': response.text}


# ==============================================================================
# WEBHOOK ENDPOINTS
# ==============================================================================

@app.route('/webhook/voice-email', methods=['POST'])
def handle_voice_email():
    """
    Receive voice email from SendGrid Inbound Parse

    Expected payload:
    {
        "from": "user@example.com",
        "subject": "My prediction text",
        "text": "Email body with context",
        "attachments": [
            {
                "filename": "audio.webm",
                "type": "audio/webm",
                "content": "base64_encoded_data"
            }
        ]
    }
    """
    try:
        # Verify webhook secret
        secret_header = request.headers.get('X-Soulfra-Secret', '')
        if secret_header != WEBHOOK_SECRET:
            return jsonify({'error': 'Invalid webhook secret'}), 401

        # Parse email data
        email_data = request.json or request.form.to_dict()

        # Extract audio attachment
        audio_data = extract_audio_from_email(email_data)

        if not audio_data:
            return jsonify({'error': 'No audio attachment found'}), 400

        # Save audio to temp storage
        audio_path = save_audio_attachment(audio_data)

        # Upload to temporary URL (or use Flask server as temporary host)
        audio_url = f"{request.url_root}temp/audio/{audio_path.name}"

        # Trigger GitHub workflow
        result = trigger_github_workflow(
            audio_url=audio_url,
            subject=audio_data['subject'],
            from_email=audio_data['from_email']
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Voice memo processing started',
                'workflow_id': result['workflow_id'],
                'audio_file': str(audio_path)
            }), 202
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/temp/audio/<filename>', methods=['GET'])
def serve_temp_audio(filename: str):
    """
    Serve temporary audio files for GitHub Actions to download
    """
    file_path = TEMP_DIR / filename

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    from flask import send_file
    return send_file(file_path)


@app.route('/webhook/voice-email/test', methods=['POST'])
def test_voice_email():
    """
    Test endpoint to simulate email webhook

    Usage:
    curl -X POST http://localhost:5001/webhook/voice-email/test \
      -H "Content-Type: application/json" \
      -H "X-Soulfra-Secret: your-secret" \
      -d '{
        "from": "test@example.com",
        "subject": "Test prediction",
        "text": "Testing voice email workflow",
        "attachment_url": "https://example.com/audio.webm"
      }'
    """
    try:
        secret_header = request.headers.get('X-Soulfra-Secret', '')
        if secret_header != WEBHOOK_SECRET:
            return jsonify({'error': 'Invalid webhook secret'}), 401

        data = request.json

        result = trigger_github_workflow(
            audio_url=data.get('attachment_url', ''),
            subject=data.get('subject', 'Test'),
            from_email=data.get('from', 'test@example.com')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'voice-email-processor',
        'github_repo': GITHUB_REPO
    })


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Voice Email Processor')
    parser.add_argument('--port', type=int, default=5001, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Debug mode')

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  Voice Email Processor - Running on port {args.port}
║
║  Webhook URL: http://{args.host}:{args.port}/webhook/voice-email
║  Test URL:    http://{args.host}:{args.port}/webhook/voice-email/test
║  Health:      http://{args.host}:{args.port}/health
║
║  GitHub Repo: {GITHUB_REPO}
╚══════════════════════════════════════════════════════════╝
    """)

    app.run(host=args.host, port=args.port, debug=args.debug)

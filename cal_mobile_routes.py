#!/usr/bin/env python3
"""
Cal Mobile Interface - QR Code → Voice/Text → Cal → GitHub

Simple workflow:
1. Generate QR code on laptop
2. Scan with phone
3. Record voice OR type text
4. Cal generates content
5. Auto-publishes to GitHub

Routes:
- GET  /cal/qr - Show QR code (scan this with phone)
- GET  /cal/mobile - Mobile interface (voice + text input)
- POST /cal/submit - Submit voice/text → Cal → GitHub
"""

from flask import Blueprint, render_template_string, request, jsonify
import qrcode
import io
import base64
import os
import subprocess
from cal_auto_publish import get_cal_response
from database import get_db
from datetime import datetime

cal_mobile_bp = Blueprint('cal_mobile', __name__)


@cal_mobile_bp.route('/cal/qr')
def show_qr():
    """
    Show QR code to scan with phone

    This page stays open on your laptop.
    Scan the QR code with your phone to open the mobile interface.
    """
    # Generate URL for mobile interface
    mobile_url = f"{request.host_url}cal/mobile"

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(mobile_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template_string(QR_PAGE_TEMPLATE,
        qr_code=qr_base64,
        mobile_url=mobile_url
    )


@cal_mobile_bp.route('/cal/mobile')
def mobile_interface():
    """
    Mobile interface - opens after scanning QR code

    Shows:
    - Voice recorder
    - Text input
    - Submit button
    """
    return render_template_string(MOBILE_INTERFACE_TEMPLATE)


@cal_mobile_bp.route('/cal/submit', methods=['POST'])
def submit_to_cal():
    """
    Submit voice or text → Cal generates content → GitHub

    POST body:
    {
        "type": "voice" or "text",
        "content": "..." (text) or base64 audio data,
        "prompt": "Write a blog post about..."
    }

    Returns:
    {
        "success": true,
        "title": "Blog post title",
        "github_url": "https://github.com/Soulfra/calriven/...",
        "live_url": "https://soulfra.github.io/calriven/"
    }
    """
    data = request.get_json()

    content_type = data.get('type')
    content = data.get('content')
    prompt = data.get('prompt', '')

    if not content_type or not content:
        return jsonify({'error': 'Missing type or content'}), 400

    try:
        # Process based on type
        if content_type == 'text':
            # User typed text directly
            user_input = content

        elif content_type == 'voice':
            # Voice recording (would need transcription)
            # For now, just use the prompt
            user_input = prompt if prompt else "Write a blog post about this voice recording"

        else:
            return jsonify({'error': f'Unknown type: {content_type}'}), 400

        # Generate blog post with Cal
        cal_prompt = f"""You are Cal, an AI writing assistant. Convert this into a blog post.

User input:
{user_input}

Write a complete blog post with:
1. A catchy title
2. Introduction
3. Main content (3-5 paragraphs)
4. Conclusion

Format in Markdown. Start with # Title.
"""

        print(f"🤖 Asking Cal to write about: {user_input[:100]}...")
        response = get_cal_response(cal_prompt)

        # Extract title
        lines = response.split('\n')
        title = None
        content_start = 0

        for i, line in enumerate(lines):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                content_start = i + 1
                break

        if not title:
            title = user_input[:50]
            blog_content = response
        else:
            blog_content = '\n'.join(lines[content_start:]).strip()

        print(f"✍️  Cal wrote: {title}")

        # Generate slug from title
        slug = title.lower().replace(' ', '-').replace('/', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        # Insert into database
        from database import get_db
        db = get_db()

        # Cal's user_id is 4, calriven brand_id is 3
        cursor = db.execute('''
            INSERT INTO posts (user_id, title, slug, content, published_at, brand_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (4, title, slug, blog_content, datetime.now().isoformat(), 3))
        post_id = cursor.lastrowid
        db.commit()
        db.close()

        print(f"💾 Saved to database: post_id={post_id}")

        # Rebuild static site
        print("🔨 Rebuilding static site...")
        soulfra_path = os.path.expanduser('~/Desktop/roommate-chat/soulfra-simple')
        rebuild_result = subprocess.run([
            'python3', 'export_static.py', '--brand', 'calriven'
        ], cwd=soulfra_path, capture_output=True, text=True)

        if rebuild_result.returncode != 0:
            print(f"⚠️  Rebuild warning: {rebuild_result.stderr}")
        else:
            print("✅ Static site rebuilt!")

        # Copy generated files to GitHub Pages repo
        import shutil
        output_path = os.path.join(soulfra_path, 'output', 'calriven')
        calriven_repo = os.path.expanduser('~/Desktop/calriven')

        # Copy all files except .git
        for item in os.listdir(output_path):
            if item == '.git' or item == '.DS_Store':
                continue
            src = os.path.join(output_path, item)
            dst = os.path.join(calriven_repo, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        print("📋 Copied to GitHub repo")

        # Commit and push ALL changes to GitHub (markdown + HTML)
        print("🚀 Pushing to GitHub...")
        repo_path = os.path.expanduser('~/Desktop/calriven')

        try:
            # Git add all changes
            subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)

            # Git commit
            subprocess.run([
                'git', 'commit', '-m',
                f"📝 {title}\n\n🤖 Generated with Cal\nCo-Authored-By: Cal <cal@soulfra.com>"
            ], cwd=repo_path, check=True)

            # Git push
            subprocess.run(['git', 'push'], cwd=repo_path, check=True)

            print("✅ Published to GitHub!")

            return jsonify({
                'success': True,
                'title': title,
                'post_id': post_id,
                'github_url': 'https://github.com/Soulfra/calriven',
                'live_url': 'https://soulfra.github.io/calriven/',
                'post_url': f'https://soulfra.github.io/calriven/post/{slug}.html'
            })
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Git error: {e}'}), 500

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# HTML TEMPLATES
# =============================================================================

QR_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cal Mobile - Scan QR Code</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            margin: 0;
            padding: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            text-align: center;
            max-width: 600px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        .qr-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            display: inline-block;
            margin: 30px 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .qr-code {
            max-width: 400px;
            width: 100%;
            height: auto;
        }
        .instructions {
            font-size: 1.2em;
            line-height: 1.6;
            color: #8b949e;
            margin: 20px 0;
        }
        .url {
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.9em;
            color: #58a6ff;
            margin: 20px 0;
            word-break: break-all;
        }
        .status {
            background: #238636;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            display: inline-block;
            margin-top: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Cal Mobile Interface</h1>

        <p class="instructions">
            Scan this QR code with your phone to open the mobile interface
        </p>

        <div class="qr-container">
            <img src="data:image/png;base64,{{ qr_code }}" class="qr-code" alt="QR Code">
        </div>

        <p class="instructions">
            Or visit this URL on your phone:
        </p>

        <div class="url">{{ mobile_url }}</div>

        <div class="status">
            ✅ Ready to scan
        </div>

        <p class="instructions" style="margin-top: 40px; font-size: 0.9em;">
            After scanning:
            <br>• Record voice OR type text
            <br>• Cal generates blog post
            <br>• Auto-publishes to GitHub
        </p>
    </div>
</body>
</html>
'''

MOBILE_INTERFACE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cal Mobile - Create Content</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #8b949e;
            margin-bottom: 30px;
        }
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab-button {
            flex: 1;
            padding: 15px;
            background: #161b22;
            border: 2px solid #30363d;
            color: #c9d1d9;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab-button.active {
            background: #238636;
            border-color: #238636;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        textarea {
            width: 100%;
            min-height: 200px;
            padding: 15px;
            background: #161b22;
            border: 2px solid #30363d;
            color: #c9d1d9;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
        }
        .record-button {
            width: 100%;
            padding: 20px;
            background: #da3633;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            margin: 10px 0;
        }
        .record-button.recording {
            background: #f85149;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .submit-button {
            width: 100%;
            padding: 20px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            margin: 10px 0;
        }
        .submit-button:disabled {
            background: #30363d;
            cursor: not-allowed;
        }
        .status {
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            display: none;
        }
        .status.show {
            display: block;
        }
        .status.success {
            background: #238636;
        }
        .status.error {
            background: #da3633;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Cal Mobile</h1>
        <p class="subtitle">Create content → Cal writes → Auto-publishes to GitHub</p>

        <div class="tab-buttons">
            <button class="tab-button active" onclick="switchTab('text')">✍️ Type</button>
            <button class="tab-button" onclick="switchTab('voice')">🎤 Voice</button>
        </div>

        <div id="text-tab" class="tab-content active">
            <textarea id="text-input" placeholder="Type what you want Cal to write about...

Examples:
• Write a blog post about AI automation
• Explain how to build a self-hosted platform
• Create a guide for voice-to-blog workflow"></textarea>
        </div>

        <div id="voice-tab" class="tab-content">
            <button id="record-button" class="record-button" onclick="toggleRecording()">
                🎤 Tap to Record
            </button>
            <div id="audio-status"></div>
        </div>

        <button id="submit-button" class="submit-button" onclick="submit()">
            🚀 Send to Cal → Publish to GitHub
        </button>

        <div id="status" class="status"></div>
    </div>

    <script>
        let currentTab = 'text';
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];

        function switchTab(tab) {
            currentTab = tab;

            // Update buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');

            // Update content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tab + '-tab').classList.add('active');
        }

        async function toggleRecording() {
            if (!isRecording) {
                // Start recording
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.start();
                    isRecording = true;

                    document.getElementById('record-button').textContent = '⏹️ Tap to Stop';
                    document.getElementById('record-button').classList.add('recording');
                    document.getElementById('audio-status').textContent = '🔴 Recording...';
                } catch (err) {
                    alert('Microphone access denied: ' + err.message);
                }
            } else {
                // Stop recording
                mediaRecorder.stop();
                isRecording = false;

                document.getElementById('record-button').textContent = '🎤 Tap to Record';
                document.getElementById('record-button').classList.remove('recording');
                document.getElementById('audio-status').textContent = '✅ Recording saved';
            }
        }

        async function submit() {
            const statusEl = document.getElementById('status');
            const submitBtn = document.getElementById('submit-button');

            statusEl.className = 'status show';
            statusEl.textContent = '⏳ Sending to Cal...';
            submitBtn.disabled = true;

            let payload;

            if (currentTab === 'text') {
                const text = document.getElementById('text-input').value.trim();
                if (!text) {
                    statusEl.className = 'status show error';
                    statusEl.textContent = '❌ Please type something first';
                    submitBtn.disabled = false;
                    return;
                }

                payload = {
                    type: 'text',
                    content: text,
                    prompt: text
                };
            } else {
                // Voice recording
                if (audioChunks.length === 0) {
                    statusEl.className = 'status show error';
                    statusEl.textContent = '❌ Please record audio first';
                    submitBtn.disabled = false;
                    return;
                }

                // For now, just use text prompt for voice
                // TODO: Add transcription
                payload = {
                    type: 'voice',
                    content: 'voice recording',
                    prompt: 'Write a blog post from this voice recording'
                };
            }

            try {
                const response = await fetch('/cal/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (result.success) {
                    statusEl.className = 'status show success';
                    statusEl.innerHTML = `
                        ✅ Published!<br>
                        <strong>${result.title}</strong><br>
                        <a href="${result.live_url}" style="color: white; text-decoration: underline;" target="_blank">
                            View on GitHub →
                        </a>
                    `;

                    // Reset form
                    document.getElementById('text-input').value = '';
                    audioChunks = [];
                    document.getElementById('audio-status').textContent = '';
                } else {
                    statusEl.className = 'status show error';
                    statusEl.textContent = '❌ Error: ' + result.error;
                }
            } catch (err) {
                statusEl.className = 'status show error';
                statusEl.textContent = '❌ Network error: ' + err.message;
            } finally {
                submitBtn.disabled = false;
            }
        }
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print("Cal Mobile Routes")
    print("=================")
    print()
    print("Add to app.py:")
    print("  from cal_mobile_routes import cal_mobile_bp")
    print("  app.register_blueprint(cal_mobile_bp)")
    print()
    print("Then visit:")
    print("  http://192.168.1.87:5001/cal/qr")

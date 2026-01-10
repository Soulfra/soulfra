#!/usr/bin/env python3
"""
Voice Routes - Flask Blueprint for Voice Recording

Web interface for voice memo recording and processing:
- Browser-based recording (Web Audio API)
- Upload pre-recorded audio
- Transcribe existing voice memos
- Import to @routes
- QR + voice integration

**Routes:**
- GET  /voice - Voice memo dashboard
- GET  /voice/record - Recording interface
- POST /voice/upload - Upload audio file
- POST /voice/record/save - Save browser recording
- POST /voice/transcribe/<id> - Transcribe voice memo
- POST /voice/import/<id> - Import to @routes
- GET  /voice/list - List all voice memos
- GET  /voice/<id> - Get voice memo details

**Usage in app.py:**
```python
from voice_routes import create_voice_blueprint

app.register_blueprint(create_voice_blueprint())
```

**iPhone/Android Recording:**
Open browser on phone → http://YOUR_IP:5001/voice/record → Record → Auto-process
"""

from flask import Blueprint, request, jsonify, session, render_template_string, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import os

from voice_input import add_audio, get_audio, list_audio, transcribe_audio
from whisper_transcriber import transcribe_voice_input, process_transcription_queue
from voice_pipeline import VoicePipeline
from qr_voice_integration import attach_voice_to_scan


# ==============================================================================
# CONFIG
# ==============================================================================

UPLOAD_FOLDER = Path(os.environ.get('VOICE_UPLOAD_FOLDER', './uploads/voice'))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'ogg', 'flac', 'webm'}

DEFAULT_BRAND = os.environ.get('VOICE_BRAND', 'me')
DEFAULT_CATEGORY = os.environ.get('VOICE_CATEGORY', 'voice')


# ==============================================================================
# BLUEPRINT CREATION
# ==============================================================================

def create_voice_blueprint():
    """
    Create Flask blueprint for voice routes
    """
    bp = Blueprint('voice', __name__, url_prefix='/voice')

    # Initialize pipeline
    pipeline = VoicePipeline()


    # ==========================================================================
    # HELPER FUNCTIONS
    # ==========================================================================

    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


    # ==========================================================================
    # DASHBOARD
    # ==========================================================================

    @bp.route('/')
    def dashboard():
        """Voice memo dashboard"""
        # Get stats
        all_memos = list_audio()
        pending_count = len([m for m in all_memos if m['status'] == 'pending'])
        transcribed_count = len([m for m in all_memos if m['status'] == 'transcribed'])

        return render_template_string(DASHBOARD_TEMPLATE,
                                       total=len(all_memos),
                                       pending=pending_count,
                                       transcribed=transcribed_count)


    # ==========================================================================
    # RECORDING INTERFACE
    # ==========================================================================

    @bp.route('/record')
    def record_page():
        """Browser-based recording interface"""
        return render_template_string(RECORD_TEMPLATE)


    @bp.route('/record/save', methods=['POST'])
    def save_recording():
        """Save browser recording"""
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400

        file = request.files['audio']

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        # Save file
        filename = secure_filename(f'recording-{int(os.time() * 1000)}.webm')
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))

        # Get parameters
        brand = request.form.get('brand', DEFAULT_BRAND)
        category = request.form.get('category', DEFAULT_CATEGORY)
        user_id = session.get('user_id', 1)
        auto_import = request.form.get('auto_import', 'true') == 'true'

        # Store in database
        audio_id = add_audio(
            file_path=str(filepath),
            source='web_recording',
            metadata={
                'brand': brand,
                'category': category,
                'user_id': user_id
            }
        )

        # Auto-process if requested
        if auto_import:
            try:
                result = pipeline.process_voice_memo(
                    audio_path=filepath,
                    brand=brand,
                    category=category,
                    user_id=user_id,
                    auto_transcribe=True,
                    use_full_pipeline=True
                )

                return jsonify({
                    'success': True,
                    'audio_id': audio_id,
                    'route': result['route'],
                    'url': result.get('url'),
                    'transcription': result.get('transcription')
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'audio_id': audio_id,
                    'error': str(e)
                }), 500

        return jsonify({
            'success': True,
            'audio_id': audio_id,
            'message': 'Recording saved (transcription pending)'
        })


    # ==========================================================================
    # UPLOAD
    # ==========================================================================

    @bp.route('/upload', methods=['GET', 'POST'])
    def upload():
        """Upload pre-recorded audio file"""
        if request.method == 'GET':
            return render_template_string(UPLOAD_TEMPLATE)

        # POST: Handle upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Use: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Save file
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))

        # Get parameters
        brand = request.form.get('brand', DEFAULT_BRAND)
        category = request.form.get('category', DEFAULT_CATEGORY)
        user_id = session.get('user_id', 1)
        auto_import = request.form.get('auto_import', 'true') == 'true'
        title = request.form.get('title')

        # Store in database
        audio_id = add_audio(
            file_path=str(filepath),
            source='upload',
            metadata={
                'brand': brand,
                'category': category,
                'user_id': user_id,
                'original_filename': filename
            }
        )

        # Auto-process if requested
        if auto_import:
            try:
                result = pipeline.process_voice_memo(
                    audio_path=filepath,
                    brand=brand,
                    category=category,
                    user_id=user_id,
                    title=title,
                    auto_transcribe=True,
                    use_full_pipeline=True
                )

                return jsonify({
                    'success': True,
                    'audio_id': audio_id,
                    'route': result['route'],
                    'url': result.get('url'),
                    'transcription': result.get('transcription'),
                    'qr_code': result.get('qr_code')
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'audio_id': audio_id,
                    'error': str(e)
                }), 500

        return jsonify({
            'success': True,
            'audio_id': audio_id,
            'message': 'File uploaded (transcription pending)'
        })


    # ==========================================================================
    # TRANSCRIPTION
    # ==========================================================================

    @bp.route('/transcribe/<int:audio_id>', methods=['POST'])
    def transcribe(audio_id):
        """Transcribe specific voice memo"""
        try:
            result = transcribe_voice_input(audio_id)

            return jsonify({
                'success': True,
                'audio_id': audio_id,
                'transcription': result['text'],
                'language': result.get('language'),
                'backend': result.get('backend')
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    @bp.route('/transcribe/queue', methods=['POST'])
    def transcribe_queue():
        """Process transcription queue"""
        limit = request.json.get('limit', 10) if request.json else 10

        try:
            results = process_transcription_queue(limit=limit)

            return jsonify({
                'success': True,
                'processed': len(results),
                'results': results
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    # ==========================================================================
    # IMPORT TO @ROUTES
    # ==========================================================================

    @bp.route('/import/<int:audio_id>', methods=['POST'])
    def import_voice(audio_id):
        """Import voice memo to @routes"""
        data = request.json or {}

        brand = data.get('brand', DEFAULT_BRAND)
        category = data.get('category', DEFAULT_CATEGORY)
        user_id = session.get('user_id', 1)
        title = data.get('title')

        # Get audio record
        audio = get_audio(audio_id)

        if not audio:
            return jsonify({'error': f'Audio {audio_id} not found'}), 404

        try:
            result = pipeline.process_voice_memo(
                audio_path=audio['file_path'],
                brand=brand,
                category=category,
                user_id=user_id,
                title=title,
                auto_transcribe=audio['status'] != 'transcribed',
                use_full_pipeline=True
            )

            return jsonify({
                'success': True,
                'audio_id': audio_id,
                'route': result['route'],
                'url': result.get('url'),
                'qr_code': result.get('qr_code')
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    # ==========================================================================
    # LIST & GET
    # ==========================================================================

    @bp.route('/list')
    def list_memos():
        """List all voice memos"""
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)

        memos = list_audio(status=status, limit=limit)

        return jsonify({
            'success': True,
            'memos': memos,
            'count': len(memos)
        })


    @bp.route('/<int:audio_id>')
    def get_memo(audio_id):
        """Get voice memo details"""
        audio = get_audio(audio_id)

        if not audio:
            return jsonify({'error': f'Audio {audio_id} not found'}), 404

        return jsonify({
            'success': True,
            'memo': audio
        })


    # ==========================================================================
    # QR INTEGRATION
    # ==========================================================================

    @bp.route('/attach-to-scan', methods=['POST'])
    def attach_to_scan_route():
        """Attach voice memo to QR scan"""
        data = request.json or {}

        audio_id = data.get('audio_id')
        scan_id = data.get('scan_id')

        if not audio_id or not scan_id:
            return jsonify({'error': 'audio_id and scan_id required'}), 400

        # Get audio
        audio = get_audio(audio_id)

        if not audio:
            return jsonify({'error': f'Audio {audio_id} not found'}), 404

        try:
            attach_voice_to_scan(
                scan_id=scan_id,
                audio_file=audio['file_path'],
                transcription=audio.get('transcription')
            )

            return jsonify({
                'success': True,
                'message': f'Voice memo {audio_id} attached to scan {scan_id}'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    return bp


# ==============================================================================
# HTML TEMPLATES
# ==============================================================================

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Memos - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 10px;
        }
        .actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .action {
            background: #667eea;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            text-decoration: none;
            transition: all 0.3s;
        }
        .action:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        .action-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎤 Voice Memos</h1>
        <p>Speak your thoughts, we'll handle the rest</p>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="stat-number">{{ total }}</div>
            <div class="stat-label">Total Memos</div>
        </div>
        <div class="stat">
            <div class="stat-number">{{ pending }}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat">
            <div class="stat-number">{{ transcribed }}</div>
            <div class="stat-label">Transcribed</div>
        </div>
    </div>

    <div class="actions">
        <a href="/voice/record" class="action">
            <div class="action-icon">🎙️</div>
            <div>Record Now</div>
        </a>
        <a href="/voice/upload" class="action">
            <div class="action-icon">📤</div>
            <div>Upload Audio</div>
        </a>
        <a href="/voice/list" class="action">
            <div class="action-icon">📋</div>
            <div>View All</div>
        </a>
    </div>
</body>
</html>
'''


RECORD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Record Voice Memo - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        #recordButton {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            border: none;
            background: #667eea;
            color: white;
            font-size: 3em;
            cursor: pointer;
            transition: all 0.3s;
            margin: 40px auto;
        }
        #recordButton:hover {
            background: #5568d3;
            transform: scale(1.05);
        }
        #recordButton.recording {
            background: #ef4444;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .status {
            font-size: 1.2em;
            margin: 20px 0;
            min-height: 30px;
        }
        .result {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            text-align: left;
            display: none;
        }
        .form-group {
            margin: 20px 0;
            text-align: left;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
    </style>
</head>
<body>
    <h1>🎙️ Record Voice Memo</h1>

    <div class="form-group">
        <label for="brand">Brand:</label>
        <input type="text" id="brand" value="me">
    </div>

    <div class="form-group">
        <label for="category">Category:</label>
        <input type="text" id="category" value="voice">
    </div>

    <button id="recordButton">🎤</button>

    <div class="status" id="status">Click to start recording</div>

    <div class="result" id="result"></div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        const recordButton = document.getElementById('recordButton');
        const status = document.getElementById('status');
        const result = document.getElementById('result');

        recordButton.addEventListener('click', async () => {
            if (!isRecording) {
                await startRecording();
            } else {
                stopRecording();
            }
        });

        async function startRecording() {
            try {
                // Check if getUserMedia is available
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    status.innerHTML = '⚠️ Microphone recording requires HTTPS or localhost.<br>Please use the <a href="/voice/upload" style="color: white; text-decoration: underline;">Upload</a> option instead, or access from laptop.';
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

                recordButton.classList.add('recording');
                recordButton.textContent = '⏹️';
                status.textContent = 'Recording... (click to stop)';

            } catch (error) {
                if (error.name === 'NotAllowedError') {
                    status.innerHTML = '🚫 Microphone access denied.<br>Please allow microphone in browser settings, or use <a href="/voice/upload" style="color: white; text-decoration: underline;">Upload</a> instead.';
                } else {
                    status.innerHTML = '❌ Error: ' + error.message + '<br><a href="/voice/upload" style="color: white; text-decoration: underline;">Try uploading instead</a>';
                }
            }
        }

        function stopRecording() {
            mediaRecorder.stop();
            isRecording = false;

            recordButton.classList.remove('recording');
            recordButton.textContent = '🎤';
            status.textContent = 'Processing...';
        }

        async function uploadRecording(audioBlob) {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('brand', document.getElementById('brand').value);
            formData.append('category', document.getElementById('category').value);
            formData.append('auto_import', 'true');

            try {
                const response = await fetch('/voice/record/save', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    result.style.display = 'block';
                    result.innerHTML = `
                        <h3>✅ Recording Processed!</h3>
                        <p><strong>Route:</strong> ${data.route}</p>
                        <p><strong>Transcription:</strong> ${data.transcription}</p>
                        ${data.url ? `<p><a href="${data.url}" target="_blank">View →</a></p>` : ''}
                    `;
                    status.textContent = 'Ready to record again';
                } else {
                    status.textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                status.textContent = 'Upload failed: ' + error.message;
            }
        }
    </script>
</body>
</html>
'''


UPLOAD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Voice Memo - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            background: #f3f4f6;
        }
        .upload-area.drag-over {
            background: #e0e7ff;
            border-color: #4f46e5;
        }
        input[type="file"] {
            display: none;
        }
        .form-group {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
        }
        button:hover {
            background: #5568d3;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f3f4f6;
            border-radius: 10px;
            display: none;
        }
    </style>
</head>
<body>
    <h1>📤 Upload Voice Memo</h1>

    <div class="upload-area" id="uploadArea">
        <div style="font-size: 3em; margin-bottom: 20px;">📁</div>
        <p>Click or drag audio file here</p>
        <p style="color: #666; font-size: 0.9em;">Supported: WAV, MP3, M4A, OGG, FLAC</p>
    </div>

    <input type="file" id="fileInput" accept="audio/*">

    <div class="form-group">
        <label for="brand">Brand:</label>
        <input type="text" id="brand" value="me">
    </div>

    <div class="form-group">
        <label for="category">Category:</label>
        <input type="text" id="category" value="voice">
    </div>

    <div class="form-group">
        <label for="title">Title (optional):</label>
        <input type="text" id="title" placeholder="Auto-generated from transcription">
    </div>

    <button id="uploadButton" style="display: none;">Upload & Process</button>

    <div class="result" id="result"></div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadButton = document.getElementById('uploadButton');
        const result = document.getElementById('result');

        let selectedFile = null;

        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');

            const file = e.dataTransfer.files[0];
            handleFile(file);
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            handleFile(file);
        });

        function handleFile(file) {
            if (!file) return;

            selectedFile = file;
            uploadArea.innerHTML = `
                <div style="font-size: 3em; margin-bottom: 20px;">✅</div>
                <p><strong>${file.name}</strong></p>
                <p style="color: #666;">${(file.size / 1024 / 1024).toFixed(2)} MB</p>
            `;
            uploadButton.style.display = 'block';
        }

        uploadButton.addEventListener('click', async () => {
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('brand', document.getElementById('brand').value);
            formData.append('category', document.getElementById('category').value);
            formData.append('title', document.getElementById('title').value);
            formData.append('auto_import', 'true');

            uploadButton.textContent = 'Processing...';
            uploadButton.disabled = true;

            try {
                const response = await fetch('/voice/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    result.style.display = 'block';
                    result.innerHTML = `
                        <h3>✅ Upload Successful!</h3>
                        <p><strong>Route:</strong> ${data.route}</p>
                        <p><strong>Transcription:</strong> ${data.transcription || 'Processing...'}</p>
                        ${data.url ? `<p><a href="${data.url}" target="_blank">View →</a></p>` : ''}
                        ${data.qr_code ? `<p><img src="${data.qr_code}" alt="QR Code" style="max-width: 200px;"></p>` : ''}
                    `;
                } else {
                    result.style.display = 'block';
                    result.innerHTML = `<h3>❌ Error:</h3><p>${data.error}</p>`;
                }
            } catch (error) {
                result.style.display = 'block';
                result.innerHTML = `<h3>❌ Upload Failed:</h3><p>${error.message}</p>`;
            } finally {
                uploadButton.textContent = 'Upload & Process';
                uploadButton.disabled = false;
            }
        });
    </script>
</body>
</html>
'''


# ==============================================================================
# EXPORT
# ==============================================================================

if __name__ == '__main__':
    print('Voice Routes - Flask Blueprint')
    print('\nUsage in app.py:')
    print('  from voice_routes import create_voice_blueprint')
    print('  app.register_blueprint(create_voice_blueprint())')
    print('\nRoutes:')
    print('  GET  /voice - Dashboard')
    print('  GET  /voice/record - Recording interface')
    print('  POST /voice/upload - Upload audio')
    print('  POST /voice/transcribe/<id> - Transcribe')
    print('  POST /voice/import/<id> - Import to @routes')

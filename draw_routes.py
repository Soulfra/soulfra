"""
Draw Routes - Mobile-friendly drawing interface with OCR learning

Features:
- Simple canvas for drawing
- Text input for labeling
- OCR verification of drawings
- Learn from labeled drawings
"""

from flask import Blueprint, render_template_string, request, jsonify, session
from ocr_extractor import OCRExtractor
from database import get_db
import base64
import io
from PIL import Image
import hashlib
from datetime import datetime

draw_bp = Blueprint('draw', __name__)
ocr = OCRExtractor()


# Mobile-optimized drawing interface template
DRAW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Draw & Learn</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
            overflow-x: hidden;
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            font-size: 2em;
            margin-bottom: 10px;
        }

        .subtitle {
            text-align: center;
            opacity: 0.9;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .canvas-container {
            background: white;
            border-radius: 15px;
            padding: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }

        #drawCanvas {
            width: 100%;
            height: 400px;
            border: 2px solid #ddd;
            border-radius: 10px;
            cursor: crosshair;
            touch-action: none;
        }

        .controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .btn {
            flex: 1;
            min-width: 100px;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-clear {
            background: #ff6b6b;
            color: white;
        }

        .btn-clear:active {
            background: #ee5a52;
        }

        .btn-submit {
            background: #51cf66;
            color: white;
        }

        .btn-submit:active {
            background: #40c057;
        }

        .label-section {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .label-section h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
        }

        #labelInput {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: none;
            border-radius: 10px;
            margin-bottom: 15px;
        }

        .hint {
            font-size: 0.9em;
            opacity: 0.8;
            font-style: italic;
        }

        .result-section {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
        }

        .result-section.show {
            display: block;
        }

        .result-section h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
        }

        .result-item {
            background: rgba(0, 0, 0, 0.2);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .result-label {
            font-weight: 600;
            margin-bottom: 5px;
        }

        .result-value {
            font-size: 1.1em;
        }

        .match-indicator {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: 600;
            margin-left: 10px;
        }

        .match-yes {
            background: #51cf66;
            color: white;
        }

        .match-no {
            background: #ff6b6b;
            color: white;
        }

        .loading {
            text-align: center;
            padding: 20px;
            font-size: 1.2em;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>✏️ Draw & Learn</h1>
        <p class="subtitle">Draw something, label it, train the AI</p>

        <div class="canvas-container">
            <canvas id="drawCanvas"></canvas>
            <div class="controls">
                <button class="btn btn-clear" onclick="clearCanvas()">Clear</button>
                <button class="btn btn-submit" onclick="submitDrawing()">Verify with OCR</button>
            </div>
        </div>

        <div class="label-section">
            <h2>What did you draw?</h2>
            <input type="text" id="labelInput" placeholder="e.g., cat, house, tree..." />
            <p class="hint">Type what you drew - OCR will verify what it sees</p>
        </div>

        <div class="result-section" id="resultSection">
            <h2>Verification Results</h2>
            <div class="result-item">
                <div class="result-label">You labeled it as:</div>
                <div class="result-value" id="userLabel"></div>
            </div>
            <div class="result-item">
                <div class="result-label">OCR detected:</div>
                <div class="result-value" id="ocrResult"></div>
            </div>
            <div class="result-item">
                <div class="result-label">Match:</div>
                <div class="result-value">
                    <span id="matchIndicator"></span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('drawCanvas');
        const ctx = canvas.getContext('2d');

        // Set canvas size
        function resizeCanvas() {
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * 2;
            canvas.height = rect.height * 2;
            ctx.scale(2, 2);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.lineWidth = 3;
        }

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Drawing state
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;

        function getPos(e) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width / 2;
            const scaleY = canvas.height / rect.height / 2;

            if (e.touches) {
                return {
                    x: (e.touches[0].clientX - rect.left) * scaleX,
                    y: (e.touches[0].clientY - rect.top) * scaleY
                };
            }
            return {
                x: (e.clientX - rect.left) * scaleX,
                y: (e.clientY - rect.top) * scaleY
            };
        }

        function startDrawing(e) {
            e.preventDefault();
            isDrawing = true;
            const pos = getPos(e);
            lastX = pos.x;
            lastY = pos.y;
        }

        function draw(e) {
            if (!isDrawing) return;
            e.preventDefault();

            const pos = getPos(e);

            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(pos.x, pos.y);
            ctx.stroke();

            lastX = pos.x;
            lastY = pos.y;
        }

        function stopDrawing(e) {
            if (!isDrawing) return;
            e.preventDefault();
            isDrawing = false;
        }

        // Mouse events
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);

        // Touch events
        canvas.addEventListener('touchstart', startDrawing);
        canvas.addEventListener('touchmove', draw);
        canvas.addEventListener('touchend', stopDrawing);

        function clearCanvas() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            document.getElementById('resultSection').classList.remove('show');
        }

        async function submitDrawing() {
            const label = document.getElementById('labelInput').value.trim();

            if (!label) {
                alert('Please enter a label for your drawing');
                return;
            }

            // Show loading
            const resultSection = document.getElementById('resultSection');
            resultSection.innerHTML = '<div class="loading"><div class="spinner"></div> Analyzing drawing...</div>';
            resultSection.classList.add('show');

            // Convert canvas to base64
            const imageData = canvas.toDataURL('image/png');

            try {
                const response = await fetch('/api/draw/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        image: imageData,
                        label: label
                    })
                });

                const result = await response.json();

                // Show results
                resultSection.innerHTML = `
                    <h2>Verification Results</h2>
                    <div class="result-item">
                        <div class="result-label">You labeled it as:</div>
                        <div class="result-value">${result.user_label}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">OCR detected:</div>
                        <div class="result-value">${result.ocr_text || 'No text detected'}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Match:</div>
                        <div class="result-value">
                            <span class="match-indicator ${result.is_match ? 'match-yes' : 'match-no'}">
                                ${result.is_match ? '✓ Match' : '✗ No Match'}
                            </span>
                        </div>
                    </div>
                    ${result.similarity ? `
                    <div class="result-item">
                        <div class="result-label">Similarity:</div>
                        <div class="result-value">${(result.similarity * 100).toFixed(1)}%</div>
                    </div>
                    ` : ''}
                `;
            } catch (error) {
                resultSection.innerHTML = `
                    <div class="loading" style="color: #ff6b6b;">
                        Error: ${error.message}
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
"""


@draw_bp.route('/draw')
def draw_page():
    """Mobile-friendly drawing interface"""
    return render_template_string(DRAW_TEMPLATE)


@draw_bp.route('/api/draw/verify', methods=['POST'])
def verify_drawing():
    """
    Verify drawing with OCR

    Request:
        {
            "image": "data:image/png;base64,...",
            "label": "what user thinks they drew"
        }

    Response:
        {
            "user_label": "cat",
            "ocr_text": "cat",
            "is_match": true,
            "similarity": 0.95,
            "drawing_id": 123
        }
    """
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        user_label = data.get('label', '').strip().lower()

        if not image_data or not user_label:
            return jsonify({'error': 'Missing image or label'}), 400

        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)

        # Save temporarily for OCR
        temp_path = f'/tmp/drawing_{hashlib.md5(image_bytes).hexdigest()}.png'
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)

        # Run OCR
        ocr_text = ocr.extract_text(temp_path, detail=0).strip().lower()

        # Calculate similarity (simple fuzzy match)
        is_match = False
        similarity = 0.0

        if ocr_text:
            # Check if user label is in OCR text or vice versa
            if user_label in ocr_text or ocr_text in user_label:
                is_match = True
                similarity = 1.0
            else:
                # Calculate simple Levenshtein-like similarity
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, user_label, ocr_text).ratio()
                is_match = similarity > 0.7

        # Save to database for learning
        db = get_db()
        user_id = session.get('user_id')

        cursor = db.execute('''
            INSERT INTO drawings (
                user_id,
                image_data,
                user_label,
                ocr_result,
                is_match,
                similarity,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            image_bytes,
            user_label,
            ocr_text,
            1 if is_match else 0,
            similarity,
            datetime.now()
        ))

        drawing_id = cursor.lastrowid
        db.commit()
        db.close()

        return jsonify({
            'user_label': user_label,
            'ocr_text': ocr_text if ocr_text else None,
            'is_match': is_match,
            'similarity': similarity,
            'drawing_id': drawing_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_draw_routes(app):
    """Register draw blueprint with Flask app"""
    app.register_blueprint(draw_bp)
    print("✅ Registered drawing routes:")
    print("   - /draw (Mobile drawing interface)")
    print("   - /api/draw/verify (OCR verification)")

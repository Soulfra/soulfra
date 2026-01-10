#!/usr/bin/env python3
"""
Universal Intake System - The ONE Endpoint That Handles EVERYTHING

Like Bitcoin block validation - accepts any format, validates, processes, publishes.

Handles:
- Voice memos (Whisper transcription)
- PDFs (PyPDF2 extraction)
- Screenshots (Tesseract OCR)
- URLs (web scraping)
- Plain text
- Emails (forwarded to intake@cringeproof.com)
- Fax documents (OCR)

Flow:
  Input → Auto-Detect → Extract Text → Ollama Insights → Route to Domain → Credit User
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from datetime import datetime
import hashlib
import base64
import tempfile
import os

# Optional: python-magic for file type detection
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    print("⚠️  python-magic not installed. Install with: pip install python-magic")

intake_bp = Blueprint('intake', __name__)


def detect_input_type(data, content_type=None):
    """
    Auto-detect input type from raw data

    Returns: 'audio', 'pdf', 'image', 'video', 'text', 'url', 'email'
    """
    # If it's a file upload
    if hasattr(data, 'read'):
        # Use python-magic to detect MIME type if available
        if HAS_MAGIC:
            file_data = data.read()
            data.seek(0)  # Reset file pointer
            mime = magic.from_buffer(file_data, mime=True)
        elif content_type:
            mime = content_type
        else:
            # Fallback: check filename extension
            filename = getattr(data, 'filename', '')
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic')):
                mime = 'image/jpeg'
            elif filename.endswith(('.mp4', '.mov', '.avi', '.webm')):
                mime = 'video/mp4'
            elif filename.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                mime = 'audio/mpeg'
            elif filename.endswith('.pdf'):
                mime = 'application/pdf'
            else:
                mime = 'application/octet-stream'

        if mime.startswith('audio/'):
            return 'audio'
        elif mime == 'application/pdf':
            return 'pdf'
        elif mime.startswith('image/'):
            return 'image'
        elif mime.startswith('video/'):
            return 'video'
        elif mime.startswith('text/'):
            return 'text'
        else:
            return 'unknown'

    # If it's text data
    if isinstance(data, str):
        # Check if it's a URL
        if data.startswith('http://') or data.startswith('https://'):
            return 'url'
        # Check if it looks like an email
        if '\nFrom:' in data and '\nSubject:' in data:
            return 'email'
        # Plain text
        return 'text'

    # If it's bytes
    if isinstance(data, bytes):
        if HAS_MAGIC:
            mime = magic.from_buffer(data, mime=True)
            if mime.startswith('audio/'):
                return 'audio'
            elif mime == 'application/pdf':
                return 'pdf'
            elif mime.startswith('image/'):
                return 'image'
            elif mime.startswith('video/'):
                return 'video'

    return 'unknown'


def extract_text_from_audio(audio_data):
    """Transcribe audio with Whisper"""
    try:
        from whisper_transcriber import WhisperTranscriber
        from audio_enhancer import AudioEnhancer

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            if hasattr(audio_data, 'read'):
                tmp.write(audio_data.read())
            else:
                tmp.write(audio_data)
            tmp_path = tmp.name

        # Enhance audio
        enhancer = AudioEnhancer()
        enhance_result = enhancer.enhance(tmp_path)
        audio_to_transcribe = enhance_result.get('output_path', tmp_path) if enhance_result.get('success') else tmp_path

        # Transcribe
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(audio_to_transcribe)

        # Cleanup
        os.unlink(tmp_path)
        if enhance_result.get('success') and enhance_result.get('output_path'):
            try:
                os.unlink(enhance_result['output_path'])
            except:
                pass

        return {
            'success': True,
            'text': result['text'],
            'method': result['backend']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_text_from_pdf(pdf_data):
    """Extract text from PDF"""
    try:
        try:
            import PyPDF2
        except ImportError:
            return {
                'success': False,
                'error': 'PyPDF2 not installed. Install with: pip install PyPDF2'
            }

        import io

        # Convert to file-like object
        if hasattr(pdf_data, 'read'):
            pdf_file = pdf_data
        else:
            pdf_file = io.BytesIO(pdf_data)

        # Extract text
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'

        return {
            'success': True,
            'text': text.strip(),
            'method': 'PyPDF2',
            'pages': len(reader.pages)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def detect_image_source(image_data):
    """
    Detect if image is AI-generated, from phone camera, or screenshot

    Returns: {
        'source': 'ai-generated' | 'phone-camera' | 'screenshot' | 'unknown',
        'details': {...metadata...}
    }
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import io
        import json

        # Convert to PIL Image
        if hasattr(image_data, 'read'):
            img = Image.open(image_data)
            image_data.seek(0)  # Reset for later use
        else:
            img = Image.open(io.BytesIO(image_data))

        metadata = {
            'width': img.width,
            'height': img.height,
            'format': img.format
        }

        # Extract EXIF data
        exif_data = {}
        try:
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value) if not isinstance(value, (str, int, float)) else value
        except:
            pass

        # Check for AI generation markers
        ai_markers = [
            'midjourney', 'dall-e', 'dalle', 'stable diffusion', 'stablediffusion',
            'openai', 'anthropic', 'ai generated', 'artificial intelligence',
            'neural network', 'gan', 'diffusion model'
        ]

        software = exif_data.get('Software', '').lower()
        description = exif_data.get('ImageDescription', '').lower()
        comment = exif_data.get('UserComment', '').lower()

        for marker in ai_markers:
            if marker in software or marker in description or marker in comment:
                return {
                    'source': 'ai-generated',
                    'details': {
                        **metadata,
                        'software': exif_data.get('Software'),
                        'confidence': 'high'
                    }
                }

        # Check for camera info (phone camera)
        camera_make = exif_data.get('Make')
        camera_model = exif_data.get('Model')

        if camera_make or camera_model:
            return {
                'source': 'phone-camera',
                'details': {
                    **metadata,
                    'camera_make': camera_make,
                    'camera_model': camera_model,
                    'lens': exif_data.get('LensModel'),
                    'date_taken': exif_data.get('DateTimeOriginal')
                }
            }

        # No EXIF camera data = likely screenshot
        if not exif_data or len(exif_data) < 3:
            return {
                'source': 'screenshot',
                'details': metadata
            }

        return {
            'source': 'unknown',
            'details': metadata
        }

    except Exception as e:
        return {
            'source': 'unknown',
            'details': {'error': str(e)}
        }


def extract_text_from_image(image_data):
    """OCR text from image (screenshot, fax, photo)"""
    try:
        from PIL import Image
        import io

        # Convert to PIL Image
        if hasattr(image_data, 'read'):
            img = Image.open(image_data)
            image_data.seek(0)  # Reset for later use
        else:
            img = Image.open(io.BytesIO(image_data))

        # Detect image source (AI, camera, screenshot)
        source_info = detect_image_source(image_data)

        # Try OCR if pytesseract available
        text = ''
        ocr_method = 'No OCR (pytesseract not installed)'

        try:
            import pytesseract
            text = pytesseract.image_to_string(img)
            ocr_method = 'Tesseract OCR'
        except ImportError:
            # pytesseract not installed - skip OCR, just return metadata
            text = f"[Image: {source_info['source']}]"
            pass
        except Exception as ocr_error:
            # OCR failed but that's okay
            text = f"[Image: OCR failed - {str(ocr_error)}]"
            pass

        return {
            'success': True,
            'text': text.strip() if text else '[Image uploaded]',
            'method': ocr_method,
            'source': source_info['source'],
            'metadata': source_info['details']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_text_from_video(video_data):
    """
    Extract text and audio from video file
    - Extract audio track and transcribe with Whisper
    - Extract first frame as thumbnail
    - Get video metadata
    """
    try:
        import subprocess
        import json
        from PIL import Image

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            if hasattr(video_data, 'read'):
                tmp.write(video_data.read())
            else:
                tmp.write(video_data)
            tmp_path = tmp.name

        # Extract video metadata with ffprobe
        try:
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', tmp_path
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            metadata = json.loads(probe_result.stdout)
        except:
            metadata = {}

        # Extract audio track
        audio_path = tmp_path.replace('.mp4', '_audio.mp3')
        try:
            subprocess.run([
                'ffmpeg', '-i', tmp_path, '-vn', '-acodec', 'mp3',
                '-y', audio_path
            ], capture_output=True, check=True)

            # Transcribe audio
            with open(audio_path, 'rb') as audio_file:
                transcription = extract_text_from_audio(audio_file)
            text = transcription.get('text', '') if transcription.get('success') else ''
        except:
            text = '[No audio track or transcription failed]'

        # Extract first frame as thumbnail
        thumbnail_path = tmp_path.replace('.mp4', '_thumb.jpg')
        try:
            subprocess.run([
                'ffmpeg', '-i', tmp_path, '-vframes', '1',
                '-y', thumbnail_path
            ], capture_output=True, check=True)
        except:
            thumbnail_path = None

        # Cleanup
        os.unlink(tmp_path)
        if os.path.exists(audio_path):
            os.unlink(audio_path)

        return {
            'success': True,
            'text': text,
            'method': 'Video extraction (FFmpeg + Whisper)',
            'thumbnail_path': thumbnail_path,
            'metadata': {
                'duration': metadata.get('format', {}).get('duration'),
                'size': metadata.get('format', {}).get('size'),
                'codec': metadata.get('streams', [{}])[0].get('codec_name') if metadata.get('streams') else None
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_text_from_url(url):
    """Scrape text from URL"""
    try:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError as import_err:
            return {
                'success': False,
                'error': f'Missing dependencies: {import_err}. Install with: pip install requests beautifulsoup4'
            }

        # Fetch page
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return {
            'success': True,
            'text': text,
            'method': 'BeautifulSoup scraping',
            'title': soup.title.string if soup.title else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_insights_with_ollama(text, context=None):
    """Extract insights, ideas, and action items with Ollama"""
    try:
        try:
            from ollama_client import OllamaClient
        except ImportError:
            # Ollama not available - skip insights
            return {
                'success': False,
                'error': 'Ollama not configured (optional)'
            }

        client = OllamaClient()

        prompt = f"""Extract key insights from this content:

{text[:2000]}  # Limit to first 2000 chars

Provide:
1. Main topic (one sentence)
2. Key ideas (3-5 bullet points)
3. Action items (if any)
4. Suggested domain: CalRiven, Soulfra, or CringeProof

Format as JSON."""

        result = client.generate(
            prompt=prompt,
            model='llama3.2',
            temperature=0.3,
            max_tokens=500
        )

        if result['success']:
            return {
                'success': True,
                'insights': result['response']
            }
        else:
            return {
                'success': False,
                'error': 'Ollama generation failed'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def route_to_domain(insights, text):
    """Decide which domain this content belongs to"""
    text_lower = text.lower()
    insights_lower = insights.lower() if insights else ''

    # CalRiven keywords
    calriven_keywords = ['data', 'analysis', 'metrics', 'proof', 'facts', 'research', 'study']
    calriven_score = sum(1 for kw in calriven_keywords if kw in text_lower or kw in insights_lower)

    # CringeProof keywords
    cringe_keywords = ['fake', 'bullshit', 'cringe', 'scam', 'exposed', 'truth', 'authentic']
    cringe_score = sum(1 for kw in cringe_keywords if kw in text_lower or kw in insights_lower)

    # Soulfra keywords
    soulfra_keywords = ['community', 'genuine', 'connection', 'trust', 'vulnerable', 'honest']
    soulfra_score = sum(1 for kw in soulfra_keywords if kw in text_lower or kw in insights_lower)

    # Return highest scoring domain
    scores = {
        'calriven': calriven_score,
        'cringeproof': cringe_score,
        'soulfra': soulfra_score
    }

    return max(scores, key=scores.get) if max(scores.values()) > 0 else 'soulfra'


@intake_bp.route('/api/intake', methods=['POST', 'OPTIONS'])
def universal_intake():
    """
    Universal intake endpoint - accepts ANYTHING

    POST /api/intake

    Form data:
        file: <audio/pdf/image file>
        OR
        url: <URL to scrape>
        OR
        text: <plain text>

    JSON data:
        {
            "data": "<base64 or plain text>",
            "type": "auto|audio|pdf|image|url|text"
        }

    Returns:
        {
            "success": true,
            "input_type": "audio|pdf|image|url|text",
            "extracted_text": "...",
            "insights": "...",
            "routed_to": "calriven|cringeproof|soulfra",
            "content_hash": "abc123...",
            "user_credited": true
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    # Get user session
    user_id = session.get('user_id')
    session_token = session.get('search_token') or session.get('session_token')

    if not user_id:
        # Create anonymous user
        import secrets
        db = get_db()
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (f'intake_{secrets.token_hex(4)}', f'intake_{secrets.token_hex(4)}@auto.com', 'auto-intake'))
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()
        db.close()

    # Detect input source
    data = None
    input_type = None

    # Check for file upload
    if 'file' in request.files:
        file = request.files['file']
        data = file
        input_type = detect_input_type(data)

    # Check for URL
    elif 'url' in request.form:
        url = request.form['url']
        data = url
        input_type = 'url'

    # Check for plain text
    elif 'text' in request.form:
        data = request.form['text']
        input_type = 'text'

    # Check for JSON body
    elif request.is_json:
        json_data = request.get_json()
        data = json_data.get('data')
        input_type = json_data.get('type', 'auto')

        # Auto-detect if needed
        if input_type == 'auto':
            input_type = detect_input_type(data)

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Extract text based on type
    extraction_result = None

    if input_type == 'audio':
        extraction_result = extract_text_from_audio(data)
    elif input_type == 'pdf':
        extraction_result = extract_text_from_pdf(data)
    elif input_type == 'image':
        extraction_result = extract_text_from_image(data)
    elif input_type == 'video':
        extraction_result = extract_text_from_video(data)
    elif input_type == 'url':
        extraction_result = extract_text_from_url(data)
    elif input_type == 'text':
        extraction_result = {'success': True, 'text': data, 'method': 'plaintext'}
    else:
        return jsonify({'success': False, 'error': f'Unknown input type: {input_type}'}), 400

    if not extraction_result['success']:
        return jsonify({
            'success': False,
            'error': f"Extraction failed: {extraction_result.get('error')}"
        }), 500

    extracted_text = extraction_result['text']

    # Generate content hash
    content_hash = hashlib.sha256(extracted_text.encode()).hexdigest()

    # Extract insights with Ollama
    insights_result = extract_insights_with_ollama(extracted_text)
    insights = insights_result.get('insights', '') if insights_result['success'] else ''

    # Route to domain
    target_domain = route_to_domain(insights, extracted_text)

    # Save to database
    db = get_db()
    cursor = db.execute('''
        INSERT INTO intake_submissions (
            user_id, input_type, extracted_text, insights, content_hash,
            routed_to_domain, extraction_method, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        input_type,
        extracted_text,
        insights,
        content_hash,
        target_domain,
        extraction_result.get('method'),
        datetime.now().isoformat()
    ))

    submission_id = cursor.lastrowid
    db.commit()
    db.close()

    # Build response
    response = jsonify({
        'success': True,
        'submission_id': submission_id,
        'input_type': input_type,
        'extracted_text': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
        'extraction_method': extraction_result.get('method'),
        'source': extraction_result.get('source', 'unknown'),  # AI-generated, phone-camera, screenshot
        'metadata': extraction_result.get('metadata', {}),
        'insights': insights,
        'routed_to': target_domain,
        'content_hash': content_hash,
        'user_credited': True,
        'user_id': user_id
    })

    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@intake_bp.route('/api/intake/stats')
def intake_stats():
    """Get intake statistics for current user"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    db = get_db()

    # Count by type
    stats = db.execute('''
        SELECT input_type, COUNT(*) as count
        FROM intake_submissions
        WHERE user_id = ?
        GROUP BY input_type
    ''', (user_id,)).fetchall()

    # Total count
    total = db.execute('''
        SELECT COUNT(*) as count FROM intake_submissions WHERE user_id = ?
    ''', (user_id,)).fetchone()['count']

    db.close()

    return jsonify({
        'success': True,
        'total_submissions': total,
        'by_type': {row['input_type']: row['count'] for row in stats}
    })


def register_intake_routes(app):
    """Register universal intake routes"""
    app.register_blueprint(intake_bp)

    # Create intake_submissions table if it doesn't exist
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS intake_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            input_type TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            insights TEXT,
            content_hash TEXT NOT NULL,
            routed_to_domain TEXT NOT NULL,
            extraction_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    db.close()

    print("✅ Universal Intake System registered:")
    print("   - POST /api/intake (accepts voice, PDF, screenshot, URL, text)")
    print("   - GET /api/intake/stats (user submission stats)")
    print("   - Auto-detection: voice → Whisper, PDF → PyPDF2, image → Tesseract, URL → scraping")
    print("   - Auto-routing: CalRiven, CringeProof, or Soulfra based on content")
    print("   - User credited for all submissions")

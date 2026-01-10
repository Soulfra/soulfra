#!/usr/bin/env python3
"""
Simple Voice Routes - RECORD, SAVE, AND TRANSCRIBE

Features:
- Record audio
- Save to database
- Auto-transcribe with Whisper (if available)
- Download recordings
"""

from flask import Blueprint, render_template, request, jsonify, send_file, session, redirect, url_for
from database import get_db
import os
import tempfile
from datetime import datetime
from pathlib import Path

simple_voice_bp = Blueprint('simple_voice', __name__)


@simple_voice_bp.route('/voice')
def voice_page():
    """
    Voice recorder page with QR authentication

    Requires:
    - Valid QR auth session (search_token)
    - If not authenticated, redirects to QR login
    """
    from dev_config import DEV_MODE

    # In production, require QR authentication
    if not DEV_MODE:
        search_token = session.get('search_token')

        if not search_token:
            # Not authenticated - redirect to QR login
            return redirect('/login/qr?redirect=/voice')

        # Verify session token is valid
        db = get_db()
        session_data = db.execute('''
            SELECT * FROM search_sessions
            WHERE session_token = ?
            AND expires_at > datetime('now')
        ''', (search_token,)).fetchone()

        if not session_data:
            db.close()
            session.pop('search_token', None)
            return redirect('/login/qr?redirect=/voice')

        db.close()

    # Get or create user_id for session
    user_id = session.get('user_id')

    if not user_id:
        # Create temporary user for QR-authenticated sessions
        import secrets
        db = get_db()

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (f'qr_user_{secrets.token_hex(4)}', f'qr_{secrets.token_hex(4)}@temp.com', 'qr-authenticated'))

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()
        db.close()

    return render_template('cringeproof_voice.html', user_id=user_id)


@simple_voice_bp.route('/cringeproof')
def cringeproof_voice():
    """
    CringeProof - Single-page voice-only experience

    No login, no friction, just speak your truth.
    Like 9gag + proximity portals + collective wordmap
    """
    from dev_config import DEV_MODE

    # Auto-create anonymous user for this session
    user_id = session.get('user_id')

    if not user_id:
        import secrets
        db = get_db()

        anon_username = f'voice_{secrets.token_hex(4)}'
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (anon_username, f'{anon_username}@cringeproof.com', 'anonymous'))

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()
        db.close()

    return render_template('cringeproof_voice.html', user_id=user_id)


@simple_voice_bp.route('/api/simple-voice/save', methods=['POST', 'OPTIONS'])
def save_voice():
    """Save recorded audio to database with optional transcription (CORS enabled for GitHub Pages)"""
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    if 'audio' not in request.files:
        response = jsonify({'success': False, 'error': 'No audio file'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'success': False, 'error': 'Empty audio'}), 400

    # Get or create user_id from session
    user_id = session.get('user_id')

    if not user_id:
        # Auto-create anonymous user account for this recording
        import secrets
        db = get_db()

        anonymous_username = f'voice_user_{secrets.token_hex(4)}'
        anonymous_email = f'{anonymous_username}@cringeproof.com'

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (anonymous_username, anonymous_email, 'voice-recording-account'))

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()
        db.close()

        print(f"✅ Auto-created user account: {anonymous_username} (ID: {user_id})")

    filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

    # Try to transcribe with Whisper (optional - don't fail if unavailable)
    transcription = None
    transcription_method = None

    try:
        from whisper_transcriber import WhisperTranscriber
        from audio_enhancer import AudioEnhancer

        # Save audio to temp file for transcription
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        # Enhance audio before transcription (remove noise, isolate voice)
        enhancer = AudioEnhancer()
        enhance_result = enhancer.enhance(tmp_path)

        # Use enhanced audio for transcription if available
        audio_to_transcribe = enhance_result.get('output_path', tmp_path) if enhance_result.get('success') else tmp_path

        # Transcribe
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(audio_to_transcribe)

        transcription = result['text']
        transcription_method = result['backend']

        # Clean up temp files
        os.unlink(tmp_path)
        if enhance_result.get('success') and enhance_result.get('output_path'):
            try:
                os.unlink(enhance_result['output_path'])
            except:
                pass

        print(f"✅ Transcribed: {transcription[:100]}...")

    except Exception as e:
        print(f"⚠️  Transcription failed (continuing without it): {e}")
        # Don't fail the whole request if transcription fails

    # Get domain and prompt from form data (optional - for domain studio)
    domain = request.form.get('domain')
    prompt_question = request.form.get('prompt')

    # Get session_id from form data (for anonymous users)
    session_id = request.form.get('session_id')

    db = get_db()

    # Save to database with transcription, user_id, session_id, and optional domain/prompt
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id, domain, prompt_question, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, len(audio_data), transcription, transcription_method, user_id, domain, prompt_question, session_id))

    file_id = cursor.lastrowid
    db.commit()
    db.close()

    # Capture device fingerprint
    try:
        from device_hash import capture_device_info, link_device_to_recording
        device_info = capture_device_info(request)
        link_device_to_recording(file_id, device_info)
        print(f"✅ Device tracked: {device_info['device_name']} ({device_info['device_hash'][:8]}...)")
    except Exception as e:
        print(f"⚠️  Device tracking failed (non-critical): {e}")

    # Auto-scrape news articles based on transcription
    scrape_result = None
    if transcription:
        try:
            from voice_scraper import scrape_for_recording
            scrape_result = scrape_for_recording(file_id)
            print(f"🔍 Scraped {scrape_result.get('articles_found', 0)} articles for keywords: {scrape_result.get('keywords', [])}")
        except Exception as e:
            print(f"⚠️  Auto-scraping failed (non-critical): {e}")

    # Update user's wordmap with this recording
    wordmap_update = None
    if transcription:
        try:
            from user_wordmap_engine import update_user_wordmap
            from domain_unlock_engine import get_primary_domain
            from domain_wordmap_aggregator import recalculate_domain_wordmap

            # Update user's cumulative wordmap
            wordmap_update = update_user_wordmap(user_id, file_id, transcription)

            # Recalculate domain wordmap (user's voice now influences domain)
            primary_domain = get_primary_domain(user_id)
            if primary_domain:
                recalculate_domain_wordmap(primary_domain['domain'])

        except Exception as e:
            print(f"⚠️  Wordmap update failed (non-critical): {e}")

    # Update user profile with personality/topic dissection
    profile_update = None
    if transcription:
        try:
            from profile_dissector import dissect_and_update_profile

            # Dissect profile from all transcriptions
            profile_update = dissect_and_update_profile(user_id)
            print(f"✅ Profile updated: {profile_update.get('traits', [])} | {profile_update.get('topics', [])}")

        except Exception as e:
            print(f"⚠️  Profile dissection failed (non-critical): {e}")

    # Auto-post to IRC/Usenet channel (optional - if post_to_channel param is set)
    message_posted = None
    post_to_channel = request.form.get('post_to_channel', '').lower() in ('true', '1', 'yes')

    if post_to_channel and transcription:
        try:
            from brand_router import detect_brand_from_prediction
            from device_hash import capture_device_info

            # Detect which domain/channel based on transcription content
            detected_domain = detect_brand_from_prediction(transcription)

            # Default channel based on domain
            channel_map = {
                'cringeproof': 'ideas',
                'soulfra': 'voice',
                'deathtodata': 'privacy',
                'calriven': 'voice',
                'stpetepros': 'events'
            }
            channel = channel_map.get(detected_domain, 'general')

            # Get device info for from_device_hash
            device_info = capture_device_info(request)

            # Post to IRC channel
            db = get_db()

            # Get user email or username for from_user
            user_row = db.execute('SELECT username, email FROM users WHERE id = ?', (user_id,)).fetchone()
            from_user = user_row['email'] if user_row and user_row['email'] else (user_row['username'] if user_row else 'anonymous')

            cursor = db.execute('''
                INSERT INTO domain_messages
                (from_user, from_device_hash, to_domain, channel, subject, body, created_at, message_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'voice')
            ''', (
                from_user,
                device_info['device_hash'],
                detected_domain,
                channel,
                'Voice Memo Transcription',
                transcription,
                datetime.now().isoformat()
            ))

            message_id = cursor.lastrowid
            db.commit()
            db.close()

            # Export to JSON for GitHub Pages
            from message_routes import export_messages_to_json
            export_messages_to_json(detected_domain)

            message_posted = {
                'message_id': message_id,
                'channel': f'alt.{detected_domain}.{channel}',
                'domain': detected_domain
            }

            print(f"📨 Auto-posted to alt.{detected_domain}.{channel} (message #{message_id})")

        except Exception as e:
            print(f"⚠️  Failed to post to IRC channel (non-critical): {e}")

    # Get username for response
    db = get_db()
    user_info = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()

    response = jsonify({
        'success': True,
        'recording_id': file_id,
        'file_id': file_id,
        'filename': filename,
        'size': len(audio_data),
        'transcription': transcription,
        'transcription_method': transcription_method,
        'user_id': user_id,
        'username': user_info['username'] if user_info else None,
        'account_created': user_id and session.get('user_id') == user_id,
        'wordmap_update': {
            'recording_count': wordmap_update['recording_count'] if wordmap_update else None,
            'is_pure_source': wordmap_update.get('is_pure_source', False) if wordmap_update else False,
            'top_words': wordmap_update.get('top_words', [])[:5] if wordmap_update else []
        } if wordmap_update else None,
        'profile_update': {
            'bio': profile_update.get('bio') if profile_update and profile_update.get('has_data') else None,
            'traits': profile_update.get('traits', []) if profile_update and profile_update.get('has_data') else [],
            'topics': profile_update.get('topics', []) if profile_update and profile_update.get('has_data') else [],
            'top_keywords': [(k[0], k[1]) for k in profile_update.get('keywords', [])[:5]] if profile_update and profile_update.get('has_data') else []
        } if profile_update else None,
        'message_posted': message_posted
    })

    # Add CORS headers for GitHub Pages
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@simple_voice_bp.route('/api/screenshot-text/save', methods=['POST', 'OPTIONS'])
def save_screenshot_text():
    """Save OCR text from screenshot and extract insights with Ollama (CORS enabled)"""
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()
    text = data.get('text')

    if not text:
        response = jsonify({'success': False, 'error': 'No text provided'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400

    # Get user_id from session
    user_id = session.get('user_id')

    # Save text as "transcription" - reuse existing voice recording flow
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    db = get_db()

    # Save to database (text instead of audio_data)
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, None, len(text.encode('utf-8')), text, 'screenshot-ocr', user_id))

    recording_id = cursor.lastrowid
    db.commit()

    # Capture device fingerprint
    try:
        from device_hash import capture_device_info, link_device_to_recording
        device_info = capture_device_info(request)
        link_device_to_recording(recording_id, device_info)
        print(f"✅ Device tracked (screenshot): {device_info['device_name']}")
    except Exception as e:
        print(f"⚠️  Device tracking failed (non-critical): {e}")

    # Try to extract insights with Ollama (optional - don't fail if unavailable)
    insight = None
    try:
        # Import Ollama integration
        from ollama_idea_extractor import extract_idea_from_text

        insight = extract_idea_from_text(text, recording_id=recording_id)

    except Exception as e:
        print(f"⚠️  Ollama extraction failed (non-critical): {e}")

    db.close()

    response = jsonify({
        'success': True,
        'recording_id': recording_id,
        'text_length': len(text),
        'insight': insight,
        'idea_id': insight.get('id') if insight else None
    })

    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@simple_voice_bp.route('/api/simple-voice/list')
def list_voices():
    """Get list of all saved recordings with transcriptions"""
    db = get_db()

    files = db.execute('''
        SELECT id, filename, file_size, transcription, transcription_method, created_at
        FROM simple_voice_recordings
        ORDER BY created_at DESC
        LIMIT 50
    ''').fetchall()

    db.close()

    return jsonify({
        'success': True,
        'files': [
            {
                'id': f['id'],
                'filename': f['filename'],
                'size': f['file_size'],
                'transcription': f['transcription'],
                'transcription_method': f['transcription_method'],
                'created_at': f['created_at']
            }
            for f in files
        ]
    })


def detect_audio_mime_type(audio_data):
    """Detect MIME type from audio file magic bytes"""
    if not audio_data or len(audio_data) < 12:
        return 'audio/webm'  # Default fallback

    # Check magic bytes
    header = audio_data[:12]

    # WebM: starts with 0x1A 0x45 0xDF 0xA3
    if header[0:4] == b'\x1a\x45\xdf\xa3':
        return 'audio/webm'

    # MP4/M4A: ftyp box at offset 4
    if header[4:8] == b'ftyp':
        return 'audio/mp4'

    # MP3: ID3 tag or MPEG frame sync
    if header[0:3] == b'ID3' or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        return 'audio/mpeg'

    # OGG: "OggS"
    if header[0:4] == b'OggS':
        return 'audio/ogg'

    # WAV/RIFF: "RIFF....WAVE"
    if header[0:4] == b'RIFF' and header[8:12] == b'WAVE':
        return 'audio/wav'

    # Default to webm if unknown
    return 'audio/webm'


@simple_voice_bp.route('/api/simple-voice/play/<int:file_id>')
def play_voice(file_id):
    """Play a saved recording"""
    db = get_db()

    recording = db.execute('''
        SELECT audio_data FROM simple_voice_recordings WHERE id = ?
    ''', (file_id,)).fetchone()

    db.close()

    if not recording:
        return jsonify({'error': 'Recording not found'}), 404

    # Detect correct MIME type
    mime_type = detect_audio_mime_type(recording['audio_data'])

    # Send directly from memory using BytesIO
    import io
    audio_io = io.BytesIO(recording['audio_data'])
    audio_io.seek(0)

    return send_file(audio_io, mimetype=mime_type)


@simple_voice_bp.route('/api/simple-voice/download/<int:file_id>')
def download_voice(file_id):
    """Download a saved recording"""
    db = get_db()

    recording = db.execute('''
        SELECT filename, audio_data FROM simple_voice_recordings WHERE id = ?
    ''', (file_id,)).fetchone()

    db.close()

    if not recording:
        return jsonify({'error': 'Recording not found'}), 404

    # Detect correct MIME type
    mime_type = detect_audio_mime_type(recording['audio_data'])

    # Send directly from memory
    import io
    audio_io = io.BytesIO(recording['audio_data'])
    audio_io.seek(0)

    return send_file(
        audio_io,
        mimetype=mime_type,
        as_attachment=True,
        download_name=recording['filename']
    )


@simple_voice_bp.route('/api/voice/analyze/<int:recording_id>')
def analyze_voice(recording_id):
    """
    Analyze voice recording with Ollama AI

    Returns:
        - sentiment: happy/sad/angry/neutral/excited
        - key_topics: extracted topics
        - brand_voice: reformatted transcript
        - follow_up_questions: suggested questions
        - quality_score: 0-100
    """
    from voice_ollama_processor import VoiceOllamaProcessor

    try:
        processor = VoiceOllamaProcessor()
        analysis = processor.analyze_recording(recording_id)

        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 404 if 'not found' in analysis['error'] else 500

        return jsonify({
            'success': True,
            **analysis
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@simple_voice_bp.route('/api/voice/sentiment-summary/<int:user_id>')
def get_sentiment_summary(user_id):
    """
    Get sentiment summary for user's recent recordings

    Returns:
        - total_recordings: count
        - sentiment_breakdown: {'happy': 3, 'neutral': 2, ...}
        - average_quality: float
        - common_topics: list of strings
        - recent_analyses: list of dicts
    """
    from voice_ollama_processor import VoiceOllamaProcessor

    try:
        processor = VoiceOllamaProcessor()
        summary = processor.get_sentiment_summary(user_id, limit=10)

        return jsonify({
            'success': True,
            **summary
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@simple_voice_bp.route('/api/voice-to-chat', methods=['POST'])
def voice_to_chat():
    """
    Create chat session from voice recording

    Request: {"recording_id": 1}
    Response: {"success": true, "chat_url": "/chat?mode=voice&context_id=1"}
    """
    data = request.get_json()
    recording_id = data.get('recording_id')

    if not recording_id:
        return jsonify({'success': False, 'error': 'recording_id is required'}), 400

    # Fetch recording with transcription
    db = get_db()
    recording = db.execute('''
        SELECT id, filename, transcription, created_at
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        db.close()
        return jsonify({'success': False, 'error': 'Recording not found'}), 404

    if not recording['transcription']:
        db.close()
        return jsonify({
            'success': False,
            'error': 'Recording has no transcription. Install Whisper: pip install openai-whisper'
        }), 400

    # Get or create user_id
    user_id = session.get('user_id', 1)
    session['user_id'] = user_id

    # Create chat session for this voice recording
    cursor = db.execute('''
        INSERT INTO discussion_sessions (post_id, user_id, persona_name, status)
        VALUES (?, ?, ?, ?)
    ''', (recording_id, user_id, 'soulassistant', 'active'))

    session_id = cursor.lastrowid

    # Add initial system message with voice context
    db.execute('''
        INSERT INTO discussion_messages (session_id, sender, content)
        VALUES (?, ?, ?)
    ''', (session_id, 'system', f"Voice recording from {recording['created_at']}: {recording['transcription']}"))

    db.commit()
    db.close()

    # Build chat URL
    chat_url = f"/chat?mode=voice&context_id={recording_id}&session_id={session_id}"

    return jsonify({
        'success': True,
        'chat_url': chat_url,
        'session_id': session_id,
        'transcription': recording['transcription']
    })


@simple_voice_bp.route('/api/domains/list')
def list_domains():
    """Get all available domains"""
    from domain_manager import DomainManager
    dm = DomainManager()
    domains = dm.get_all()

    return jsonify({
        'success': True,
        'domains': [{'domain': d['domain'], 'name': d.get('name', d['domain'])} for d in domains]
    })


@simple_voice_bp.route('/api/ideas/save', methods=['POST'])
def save_idea():
    """Save text idea (no voice required)"""
    data = request.get_json()
    text = data.get('text', '').strip()
    domain = data.get('domain')  # Optional domain selection

    if not text:
        return jsonify({'success': False, 'error': 'Text required'}), 400

    user_id = session.get('user_id', 1)

    db = get_db()
    title = ' '.join(text.split()[:5])

    # Get domain_id if domain provided
    domain_id = None
    if domain:
        domain_row = db.execute('SELECT id FROM domain_contexts WHERE domain = ?', (domain,)).fetchone()
        if domain_row:
            domain_id = domain_row['id']
        else:
            # Create domain context if doesn't exist
            cursor = db.execute('INSERT INTO domain_contexts (domain, name) VALUES (?, ?)',
                              (domain, domain.split('.')[0].capitalize()))
            domain_id = cursor.lastrowid

    cursor = db.execute('''
        INSERT INTO voice_ideas (user_id, title, text, score, status, created_at, domain_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, title, text, 50, 'living', datetime.now().isoformat(), domain_id))

    db.commit()
    db.close()

    return jsonify({'success': True, 'idea_id': cursor.lastrowid})


@simple_voice_bp.route('/api/ideas/extract', methods=['POST'])
def extract_ideas():
    """Extract ideas from transcription"""
    data = request.get_json()
    transcription = data.get('transcription', '').strip()
    recording_id = data.get('recording_id')

    if not transcription:
        return jsonify({'success': False, 'error': 'Transcription required'}), 400

    user_id = session.get('user_id', 1)
    from voice_idea_board_routes import extract_ideas_from_transcript

    ideas = extract_ideas_from_transcript(transcription, recording_id, user_id)

    return jsonify({'success': True, 'ideas_count': len(ideas)})


@simple_voice_bp.route('/api/ideas/list')
def list_ideas():
    """Get all ideas (multi-user) with optional domain filtering"""
    domain_filter = request.args.get('domain')  # Optional domain filter

    db = get_db()

    if domain_filter:
        # Filter by specific domain
        ideas = db.execute('''
            SELECT v.id, v.title, v.text, v.score, v.ai_insight, v.status,
                   v.created_at, v.merged_count, u.username, d.domain, d.domain_slug as domain_name
            FROM voice_ideas v
            LEFT JOIN users u ON v.user_id = u.id
            LEFT JOIN domain_contexts d ON v.domain_id = d.id
            WHERE v.status IN ('living', 'expanded')
              AND d.domain = ?
            ORDER BY v.score DESC, v.created_at DESC
            LIMIT 10
        ''', (domain_filter,)).fetchall()
    else:
        # Get all ideas
        ideas = db.execute('''
            SELECT v.id, v.title, v.text, v.score, v.ai_insight, v.status,
                   v.created_at, v.merged_count, u.username, d.domain, d.domain_slug as domain_name
            FROM voice_ideas v
            LEFT JOIN users u ON v.user_id = u.id
            LEFT JOIN domain_contexts d ON v.domain_id = d.id
            WHERE v.status IN ('living', 'expanded')
            ORDER BY v.score DESC, v.created_at DESC
            LIMIT 10
        ''').fetchall()

    db.close()

    return jsonify({'success': True, 'ideas': [dict(i) for i in ideas]})


@simple_voice_bp.route('/api/ideas/expand', methods=['POST'])
def expand_idea():
    """Expand idea with AI"""
    data = request.get_json()
    idea_id = data.get('idea_id')

    if not idea_id:
        return jsonify({'success': False, 'error': 'idea_id required'}), 400

    db = get_db()
    idea = db.execute('SELECT * FROM voice_ideas WHERE id = ?', (idea_id,)).fetchone()

    if not idea:
        db.close()
        return jsonify({'success': False, 'error': 'Not found'}), 404

    try:
        from ollama_client import OllamaClient
        client = OllamaClient()

        result = client.generate(
            prompt=f"Expand this idea with 3 actionable steps:\n\n{idea['title']}: {idea['text']}",
            model='llama3.2',
            temperature=0.7,
            max_tokens=300
        )

        if result['success']:
            db.execute('''
                UPDATE voice_ideas
                SET ai_insight = ?, score = score + 5, status = 'expanded'
                WHERE id = ?
            ''', (result['response'], idea_id))
            db.commit()
            db.close()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Expand failed: {e}")

    db.close()
    return jsonify({'success': False, 'error': 'AI failed'}), 500


@simple_voice_bp.route('/api/ideas/merge', methods=['POST'])
def merge_ideas():
    """Merge similar ideas"""
    data = request.get_json()
    idea_id = data.get('idea_id')

    if not idea_id:
        return jsonify({'success': False, 'error': 'idea_id required'}), 400

    db = get_db()
    idea = db.execute('SELECT * FROM voice_ideas WHERE id = ?', (idea_id,)).fetchone()

    if not idea:
        db.close()
        return jsonify({'success': False, 'error': 'Not found'}), 404

    keywords = set(idea['text'].lower().split())
    similar = db.execute('SELECT id, text FROM voice_ideas WHERE id != ? AND status = "living"', (idea_id,)).fetchall()

    merged_count = 0
    for s in similar:
        if len(keywords & set(s['text'].lower().split())) >= 3:
            db.execute('UPDATE voice_ideas SET status = ? WHERE id = ?', (f'merged_into_{idea_id}', s['id']))
            merged_count += 1

    if merged_count > 0:
        db.execute('UPDATE voice_ideas SET score = score + ?, merged_count = merged_count + ? WHERE id = ?',
                   (merged_count * 10, merged_count, idea_id))

    db.commit()
    db.close()

    return jsonify({'success': merged_count > 0, 'merged_count': merged_count})


@simple_voice_bp.route('/api/ideas/update', methods=['POST'])
def update_idea():
    """Update idea title/text"""
    data = request.get_json()
    idea_id = data.get('idea_id')
    title = data.get('title', '').strip()
    text = data.get('text', '').strip()

    if not idea_id or not title or not text:
        return jsonify({'success': False, 'error': 'Missing fields'}), 400

    db = get_db()
    db.execute('UPDATE voice_ideas SET title = ?, text = ? WHERE id = ?', (title, text, idea_id))
    db.commit()
    db.close()

    return jsonify({'success': True})


@simple_voice_bp.route('/api/ideas/export')
def export_ideas():
    """Export ideas as JSON"""
    db = get_db()
    ideas = db.execute('''
        SELECT id, title, text, score, ai_insight, status, created_at
        FROM voice_ideas WHERE status IN ('living', 'expanded')
        ORDER BY score DESC
    ''').fetchall()
    db.close()

    return jsonify({'ideas': [dict(i) for i in ideas]})


# ============================================================================
# CONTENT GENERATION ENDPOINTS - Generate pitch decks, blogs, social posts
# ============================================================================

@simple_voice_bp.route('/api/voice/generate-content/<int:recording_id>')
def generate_content_all(recording_id):
    """
    Generate ALL content types from a voice recording

    Returns:
        - pitch_deck (slides with bullets)
        - blog_post (intro, sections, conclusion)
        - social_posts (Twitter, LinkedIn, Instagram)
    """
    from voice_content_generator import VoiceContentGenerator

    generator = VoiceContentGenerator()
    result = generator.generate_all_content(recording_id)

    return jsonify(result)


@simple_voice_bp.route('/api/voice/generate-pitch/<int:recording_id>')
def generate_pitch_deck(recording_id):
    """Generate pitch deck from voice recording"""
    from voice_content_generator import VoiceContentGenerator
    from domain_unlock_engine import get_primary_domain

    db = get_db()
    rec = db.execute('''
        SELECT transcription, user_id
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not rec:
        return jsonify({'error': 'Recording not found'}), 404

    if not rec['transcription']:
        return jsonify({'error': 'No transcription available'}), 400

    # Get user's primary domain
    primary_domain = get_primary_domain(rec['user_id'])
    domain = primary_domain['domain'] if primary_domain else 'your-domain.com'

    generator = VoiceContentGenerator()
    result = generator.generate_pitch_deck(rec['transcription'], domain, recording_id)

    return jsonify(result)


@simple_voice_bp.route('/api/voice/generate-blog/<int:recording_id>')
def generate_blog_post(recording_id):
    """Generate blog post from voice recording"""
    from voice_content_generator import VoiceContentGenerator
    from domain_unlock_engine import get_primary_domain

    db = get_db()
    rec = db.execute('''
        SELECT transcription, user_id
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not rec:
        return jsonify({'error': 'Recording not found'}), 404

    if not rec['transcription']:
        return jsonify({'error': 'No transcription available'}), 400

    primary_domain = get_primary_domain(rec['user_id'])
    domain = primary_domain['domain'] if primary_domain else 'your-domain.com'

    generator = VoiceContentGenerator()
    result = generator.generate_blog_post(rec['transcription'], domain, recording_id)

    return jsonify(result)


@simple_voice_bp.route('/api/voice/generate-social/<int:recording_id>')
def generate_social_posts(recording_id):
    """Generate social media posts from voice recording"""
    from voice_content_generator import VoiceContentGenerator
    from domain_unlock_engine import get_primary_domain

    db = get_db()
    rec = db.execute('''
        SELECT transcription, user_id
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not rec:
        return jsonify({'error': 'Recording not found'}), 404

    if not rec['transcription']:
        return jsonify({'error': 'No transcription available'}), 400

    primary_domain = get_primary_domain(rec['user_id'])
    domain = primary_domain['domain'] if primary_domain else 'your-domain.com'

    generator = VoiceContentGenerator()
    result = generator.generate_social_posts(rec['transcription'], domain, recording_id)

    return jsonify(result)


@simple_voice_bp.route('/api/voice/batch-generate/<int:user_id>')
def batch_generate_content(user_id):
    """
    Batch generate content for user's recent voice memos

    Query params:
        - content_type: 'pitch_deck', 'blog_post', 'social_posts', or 'all' (default)
        - limit: Number of recordings to process (default 5)
    """
    from voice_content_generator import VoiceContentGenerator

    content_type = request.args.get('content_type', 'all')
    limit = int(request.args.get('limit', 5))

    generator = VoiceContentGenerator()
    results = generator.batch_generate(user_id, content_type, limit)

    return jsonify({
        'success': True,
        'content_type': content_type,
        'results': results,
        'count': len(results)
    })


@simple_voice_bp.route('/api/voice/wordmap-pitch/<int:recording_id>')
def api_voice_wordmap_pitch(recording_id):
    """
    Generate brand-aware pitch deck using wordmap analysis

    Query params:
        brand: Optional brand slug (defaults to user's primary domain)

    Returns:
        {
            'pitch_deck': {...},
            'wordmap': {'word': count, ...},
            'alignment_score': float (0.0-1.0),
            'alignment_quality': str (🟢 Excellent, 🟡 Good, etc.)
        }
    """
    from wordmap_pitch_integrator import generate_brand_aware_pitch_deck

    brand = request.args.get('brand')

    result = generate_brand_aware_pitch_deck(recording_id, brand=brand)

    return jsonify(result)


def register_simple_voice_routes(app):
    """Register simple voice routes"""
    app.register_blueprint(simple_voice_bp)
    print("✅ Simple Voice routes registered:")
    print("   - /voice (Simple recorder with QR auth)")
    print("   - /api/simple-voice/save (Save recording + auto-transcribe)")
    print("   - /api/simple-voice/list (List recordings with transcriptions)")
    print("   - /api/simple-voice/play/<id> (Play recording)")
    print("   - /api/simple-voice/download/<id> (Download recording)")
    print("   - /api/voice/analyze/<id> (AI analysis with Ollama)")
    print("   - /api/voice/sentiment-summary/<user_id> (User sentiment summary)")
    print("   - /api/voice-to-chat (Create chat from voice recording)")
    print("   - /api/voice/wordmap-pitch/<id> (Wordmap-guided pitch deck)")
    print("   - /api/ideas/save (Type idea - no voice needed)")
    print("   - /api/ideas/extract (Extract ideas from transcript)")
    print("   - /api/ideas/list (All ideas - multi-user)")
    print("   - /api/ideas/expand (AI expand)")
    print("   - /api/ideas/update (Edit idea)")
    print("   - /api/ideas/merge (Merge similar)")
    print("   - /api/ideas/export (JSON export)")


@simple_voice_bp.route('/api/domains/my-domains')
def get_my_domains():
    """
    Get current user's owned domains with ownership info

    Returns:
        {
            'success': true,
            'user_id': 1,
            'handle': '@soulfra',
            'primary_domain': {...},
            'domains': [{domain, ownership_percentage, tier, ...}],
            'unlock_status': {can_unlock, unlocks_available, ...}
        }
    """
    from domain_unlock_engine import get_user_domains, get_user_handle, get_primary_domain, check_unlock_eligibility

    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        # Get domains
        domains = get_user_domains(user_id)

        # Get handle
        handle = get_user_handle(user_id)

        # Get primary domain
        primary = get_primary_domain(user_id)

        # Get unlock eligibility
        unlock_status = check_unlock_eligibility(user_id)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'handle': handle,
            'primary_domain': primary,
            'domains': domains,
            'unlock_status': unlock_status
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@simple_voice_bp.route('/api/domains/set-primary', methods=['POST'])
def set_primary():
    """
    Set user's primary domain (handle)

    Request: {"domain": "calriven.com"}
    Response: {"success": true, "handle": "@calriven"}
    """
    from domain_unlock_engine import set_primary_domain, get_user_handle

    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json()
    domain = data.get('domain')

    if not domain:
        return jsonify({'success': False, 'error': 'Missing domain'}), 400

    try:
        success = set_primary_domain(user_id, domain)

        if success:
            new_handle = get_user_handle(user_id)
            return jsonify({
                'success': True,
                'handle': new_handle,
                'domain': domain
            })
        else:
            return jsonify({'success': False, 'error': 'Domain not owned or not found'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# VOICE QUERY & FAUCET INTEGRATION - The Google/Siri/Ollama Hybrid
# ============================================================================

@simple_voice_bp.route('/api/voice/query', methods=['POST'])
def process_voice_query():
    """
    Process voice transcription as search query + faucet unlock

    Like Google Voice Search + Siri + ChatGPT combined

    Request: {
        "recording_id": 42,
        "transcription": "show me privacy articles",  # Optional (will fetch from recording)
        "user_id": 1  # Optional (will use session)
    }

    Response: {
        "success": true,
        "query_result": {
            "intent": "search",
            "enhanced_query": "privacy articles",
            "keywords": ["privacy", "articles"],
            "results": [...],  # Search results
            "ai_response": "I found 5 articles about privacy..."
        },
        "faucet_result": {
            "domains_unlocked": ["privacy.com"],
            "faucet_keys_generated": [...],
            "ownership_progress": {"privacy.com": {"percentage": 12.5, ...}}
        }
    }
    """
    from voice_query_processor import process_voice_query as process_query
    from voice_faucet_integration import process_voice_for_faucet

    data = request.get_json()
    recording_id = data.get('recording_id')
    transcription = data.get('transcription')
    user_id = data.get('user_id') or session.get('user_id')

    if not transcription:
        if not recording_id:
            return jsonify({'success': False, 'error': 'transcription or recording_id required'}), 400

        # Fetch transcription from recording
        db = get_db()
        rec = db.execute('''
            SELECT transcription, user_id FROM simple_voice_recordings WHERE id = ?
        ''', (recording_id,)).fetchone()
        db.close()

        if not rec:
            return jsonify({'success': False, 'error': 'Recording not found'}), 404

        if not rec['transcription']:
            return jsonify({'success': False, 'error': 'Recording has no transcription'}), 400

        transcription = rec['transcription']
        if not user_id:
            user_id = rec['user_id']

    try:
        # Step 1: Process as search query with Ollama
        query_result = process_query(transcription, user_id)

        # Step 2: Process for faucet unlock
        faucet_result = process_voice_for_faucet(user_id, transcription, recording_id)

        return jsonify({
            'success': True,
            'transcription': transcription,
            'query_result': query_result,
            'faucet_result': faucet_result
        })

    except Exception as e:
        import traceback
        print(f"Voice query processing failed: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@simple_voice_bp.route('/api/voice/query/batch', methods=['POST'])
def batch_process_voice_queries():
    """
    Batch process multiple recordings as voice queries

    Request: {
        "recording_ids": [1, 2, 3],
        "user_id": 1  # Optional
    }

    Response: {
        "success": true,
        "results": [
            {"recording_id": 1, "query_result": {...}, "faucet_result": {...}},
            ...
        ],
        "summary": {
            "total_processed": 3,
            "total_domains_unlocked": 2,
            "total_keywords": 15
        }
    }
    """
    from voice_query_processor import process_voice_query as process_query
    from voice_faucet_integration import process_voice_for_faucet

    data = request.get_json()
    recording_ids = data.get('recording_ids', [])
    user_id = data.get('user_id') or session.get('user_id')

    if not recording_ids:
        return jsonify({'success': False, 'error': 'recording_ids required'}), 400

    db = get_db()
    results = []
    all_domains_unlocked = set()
    all_keywords = set()

    for rec_id in recording_ids:
        rec = db.execute('''
            SELECT id, transcription, user_id FROM simple_voice_recordings WHERE id = ?
        ''', (rec_id,)).fetchone()

        if not rec or not rec['transcription']:
            continue

        try:
            query_result = process_query(rec['transcription'], user_id or rec['user_id'])
            faucet_result = process_voice_for_faucet(user_id or rec['user_id'], rec['transcription'], rec_id)

            results.append({
                'recording_id': rec_id,
                'query_result': query_result,
                'faucet_result': faucet_result
            })

            # Track summary
            all_domains_unlocked.update(faucet_result['domains_unlocked'])
            all_keywords.update(query_result['keywords'])

        except Exception as e:
            print(f"Failed to process recording {rec_id}: {e}")

    db.close()

    return jsonify({
        'success': True,
        'results': results,
        'summary': {
            'total_processed': len(results),
            'total_domains_unlocked': len(all_domains_unlocked),
            'total_keywords': len(all_keywords),
            'domains_unlocked': list(all_domains_unlocked),
            'top_keywords': list(all_keywords)[:20]
        }
    })


@simple_voice_bp.route('/api/upload-voice', methods=['POST'])
def upload_voice_file():
    """
    Upload voice file from iPhone Shortcuts or Voice Memos app

    This endpoint accepts file uploads from:
    - iOS Shortcuts app
    - Direct file uploads from Voice Memos
    - Any HTTP client sending audio files

    Works with HTTP (no HTTPS requirement) - perfect for local network
    """
    if 'file' not in request.files and 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file. Send as "file" or "audio" field'}), 400

    audio_file = request.files.get('file') or request.files.get('audio')
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'success': False, 'error': 'Empty audio file'}), 400

    # Get user_id from session or create temp user
    user_id = session.get('user_id')

    if not user_id:
        import secrets
        db = get_db()
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (f'iphone_user_{secrets.token_hex(4)}', f'iphone_{secrets.token_hex(4)}@upload.com', 'iphone-upload'))

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()
        db.close()

    filename = audio_file.filename or f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m4a"

    # Try to transcribe with Whisper
    transcription = None
    transcription_method = None

    try:
        from whisper_transcriber import WhisperTranscriber
        from audio_enhancer import AudioEnhancer

        # Save audio to temp file for transcription
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        # Enhance audio before transcription
        enhancer = AudioEnhancer()
        enhance_result = enhancer.enhance(tmp_path)

        # Use enhanced audio for transcription if available
        audio_to_transcribe = enhance_result.get('output_path', tmp_path) if enhance_result.get('success') else tmp_path

        # Transcribe
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(audio_to_transcribe)

        transcription = result['text']
        transcription_method = result['backend']

        # Clean up temp files
        os.unlink(tmp_path)
        if enhance_result.get('success') and enhance_result.get('output_path'):
            try:
                os.unlink(enhance_result['output_path'])
            except:
                pass

        print(f"✅ Transcribed upload: {transcription[:100]}...")

    except Exception as e:
        print(f"⚠️  Transcription failed (continuing without it): {e}")

    db = get_db()

    # Save to database
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, len(audio_data), transcription, transcription_method, user_id))

    file_id = cursor.lastrowid
    db.commit()
    db.close()

    # Capture device fingerprint
    try:
        from device_hash import capture_device_info, link_device_to_recording
        device_info = capture_device_info(request)
        link_device_to_recording(file_id, device_info)
        print(f"✅ Device tracked (upload): {device_info['device_name']}")
    except Exception as e:
        print(f"⚠️  Device tracking failed (non-critical): {e}")

    return jsonify({
        'success': True,
        'id': file_id,
        'filename': filename,
        'size': len(audio_data),
        'transcription': transcription,
        'method': transcription_method,
        'message': 'Voice uploaded successfully from iPhone!'
    })


@simple_voice_bp.route('/voices')
def voices_dashboard():
    """
    Dashboard to view ALL voice recordings

    Shows:
    - All recordings from simple_voice_recordings table
    - Filter by brand (CalRiven, DeathToData, Soulfra)
    - Play/download/delete buttons
    - Transcriptions displayed
    - Stats summary

    Like running: ls -la ~/voice-memos/
    """
    db = get_db()

    # Get all recordings with brand routing info
    recordings = db.execute('''
        SELECT
            svr.id,
            svr.filename,
            svr.transcription,
            svr.created_at,
            svr.file_size,
            svr.transcription_method,
            NULL as brand
        FROM simple_voice_recordings svr
        ORDER BY svr.created_at DESC
    ''').fetchall()

    # Calculate brand routing for each recording based on transcription
    recordings_with_brands = []
    for rec in recordings:
        brand = None
        if rec['transcription']:
            text = rec['transcription'].lower()

            # CalRiven keywords
            calriven_keywords = ['data', 'analysis', 'metrics', 'proof', 'game', 'scraped',
                               'articles', 'news', 'feeds', 'input', 'system', 'logic', 'cringeproof']
            calriven_score = sum(1 for kw in calriven_keywords if kw in text)

            # DeathToData keywords
            deathtodata_keywords = ['hate', 'broken', 'fake', 'cringe', 'burn', 'garbage',
                                   'destroy', 'corrupt', 'bullshit', 'scam']
            deathtodata_score = sum(1 for kw in deathtodata_keywords if kw in text)

            # Soulfra keywords
            soulfra_keywords = ['authentic', 'trust', 'community', 'genuine', 'connection',
                              'vulnerable', 'honest', 'belonging', 'real', 'truth']
            soulfra_score = sum(1 for kw in soulfra_keywords if kw in text)

            # Assign brand based on highest score
            if deathtodata_score > calriven_score and deathtodata_score > soulfra_score:
                brand = 'deathtodata'
            elif calriven_score > soulfra_score:
                brand = 'calriven'
            elif soulfra_score > 0:
                brand = 'soulfra'

        recordings_with_brands.append({
            'id': rec['id'],
            'filename': rec['filename'],
            'transcription': rec['transcription'],
            'created_at': rec['created_at'],
            'file_size': rec['file_size'],
            'transcription_method': rec['transcription_method'],
            'brand': brand
        })

    # Calculate stats
    total_count = len(recordings_with_brands)
    calriven_count = sum(1 for r in recordings_with_brands if r['brand'] == 'calriven')
    deathtodata_count = sum(1 for r in recordings_with_brands if r['brand'] == 'deathtodata')
    soulfra_count = sum(1 for r in recordings_with_brands if r['brand'] == 'soulfra')

    db.close()

    return render_template(
        'voices_dashboard.html',
        recordings=recordings_with_brands,
        total_count=total_count,
        calriven_count=calriven_count,
        deathtodata_count=deathtodata_count,
        soulfra_count=soulfra_count
    )


@simple_voice_bp.route('/api/simple-voice/delete/<int:file_id>', methods=['DELETE'])
def delete_voice(file_id):
    """Delete a voice recording"""
    db = get_db()

    # Check if exists
    recording = db.execute('SELECT id FROM simple_voice_recordings WHERE id = ?', (file_id,)).fetchone()

    if not recording:
        db.close()
        return jsonify({'success': False, 'error': 'Recording not found'}), 404

    # Delete it
    db.execute('DELETE FROM simple_voice_recordings WHERE id = ?', (file_id,))
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': f'Recording {file_id} deleted'})


@simple_voice_bp.route('/api/wordmap/<int:user_id>')
def get_user_wordmap(user_id):
    """Get user's wordmap for visualization"""
    db = get_db()

    # Get user's wordmap from database
    wordmap_data = db.execute('''
        SELECT wordmap_json, recording_count, last_updated, pure_source_id
        FROM user_wordmaps
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if not wordmap_data:
        db.close()
        return jsonify({
            'success': True,
            'wordmap': {},
            'recording_count': 0,
            'last_updated': None,
            'pure_source_id': None
        })

    # Parse JSON wordmap
    import json
    wordmap = json.loads(wordmap_data['wordmap_json']) if wordmap_data['wordmap_json'] else {}

    db.close()

    return jsonify({
        'success': True,
        'wordmap': wordmap,
        'recording_count': wordmap_data['recording_count'],
        'last_updated': wordmap_data['last_updated'],
        'pure_source_id': wordmap_data['pure_source_id']
    })


@simple_voice_bp.route('/api/wordmap/domain/<domain>')
def get_domain_wordmap(domain):
    """Get domain's collective wordmap"""
    db = get_db()

    # Get domain wordmap
    wordmap_data = db.execute('''
        SELECT wordmap_json, contributor_count, last_updated
        FROM domain_wordmaps
        WHERE domain = ?
    ''', (domain,)).fetchone()

    if not wordmap_data:
        db.close()
        return jsonify({
            'success': True,
            'wordmap': {},
            'contributor_count': 0,
            'last_updated': None
        })

    # Parse JSON wordmap
    import json
    wordmap = json.loads(wordmap_data['wordmap_json']) if wordmap_data['wordmap_json'] else {}

    db.close()

    return jsonify({
        'success': True,
        'wordmap': wordmap,
        'contributor_count': wordmap_data['contributor_count'],
        'last_updated': wordmap_data['last_updated']
    })


@simple_voice_bp.route('/recordings')
def recordings_gallery():
    """Gallery page showing all audio recordings"""
    db = get_db()

    # Get all recordings with user info
    recordings = db.execute('''
        SELECT
            r.id,
            r.filename,
            r.file_size,
            r.transcription,
            r.created_at,
            r.user_id,
            u.username
        FROM simple_voice_recordings r
        LEFT JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        LIMIT 100
    ''').fetchall()

    db.close()

    return render_template('recordings_gallery.html', recordings=recordings)


@simple_voice_bp.route('/api/recordings')
def api_get_recordings():
    """API endpoint to get all recordings as JSON (CORS enabled)"""
    db = get_db()

    recordings = db.execute('''
        SELECT
            id,
            filename,
            file_size,
            transcription,
            created_at,
            user_id
        FROM simple_voice_recordings
        ORDER BY created_at DESC
        LIMIT 100
    ''').fetchall()

    db.close()

    result = [{
        'id': r['id'],
        'filename': r['filename'],
        'size': r['file_size'],
        'transcription': r['transcription'],
        'created_at': r['created_at'],
        'user_id': r['user_id'],
        'audio_url': f'/api/simple-voice/download/{r["id"]}'
    } for r in recordings]

    response = jsonify({'success': True, 'recordings': result})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@simple_voice_bp.route('/api/simple-voice/stream/<int:recording_id>')
def stream_recording(recording_id):
    """Stream audio file by ID (CORS enabled, for <audio> playback)"""
    db = get_db()

    recording = db.execute('''
        SELECT audio_data, filename FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    db.close()

    if not recording:
        return jsonify({'error': 'Recording not found'}), 404

    # Detect correct MIME type
    mime_type = detect_audio_mime_type(recording['audio_data'])

    import io
    audio_io = io.BytesIO(recording['audio_data'])
    audio_io.seek(0)

    response = send_file(
        audio_io,
        mimetype=mime_type,
        as_attachment=False,
        download_name=recording['filename']
    )
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@simple_voice_bp.route('/api/ipfs/publish/<int:recording_id>', methods=['POST'])
def publish_to_ipfs(recording_id):
    """
    Publish audio recording to IPFS with cryptographic signature
    Like Bitcoin transactions - decentralized, verifiable, permanent
    """
    db = get_db()

    recording = db.execute('''
        SELECT id, audio_data, filename, user_id, transcription, created_at
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    db.close()

    if not recording:
        return jsonify({'error': 'Recording not found'}), 404

    try:
        from audio_crypto_signer import AudioSigner

        signer = AudioSigner()
        user_id = recording['user_id'] if recording['user_id'] else 'anonymous'

        # Sign the audio (Bitcoin-style)
        signature = signer.sign_audio(
            recording['audio_data'],
            user_id=str(user_id),
            metadata={
                'recording_id': recording['id'],
                'filename': recording['filename'],
                'transcription': recording['transcription'],
                'created_at': recording['created_at']
            }
        )

        # Publish to IPFS
        ipfs_hash = signer.publish_to_ipfs(recording['audio_data'], signature)

        if not ipfs_hash:
            return jsonify({'success': False, 'error': 'IPFS publish failed'}), 500

        # Save IPFS hash to database
        db = get_db()
        db.execute('''
            UPDATE simple_voice_recordings
            SET ipfs_hash = ?, crypto_signature = ?
            WHERE id = ?
        ''', (ipfs_hash, jsonify(signature).data.decode(), recording_id))
        db.commit()
        db.close()

        # Get URLs
        urls = signer.get_ipfs_url(ipfs_hash)

        response = jsonify({
            'success': True,
            'recording_id': recording_id,
            'ipfs_hash': ipfs_hash,
            'signature': signature,
            'urls': urls,
            'message': 'Audio published to IPFS with cryptographic signature'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@simple_voice_bp.route('/api/ipfs/verify/<int:recording_id>')
def verify_ipfs_signature(recording_id):
    """Verify cryptographic signature of IPFS-published audio"""
    db = get_db()

    recording = db.execute('''
        SELECT audio_data, crypto_signature FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    db.close()

    if not recording or not recording['crypto_signature']:
        return jsonify({'error': 'No signature found'}), 404

    try:
        from audio_crypto_signer import AudioSigner
        import json

        signer = AudioSigner()
        signature = json.loads(recording['crypto_signature'])

        is_valid = signer.verify_audio(recording['audio_data'], signature)

        response = jsonify({
            'valid': is_valid,
            'signature': signature,
            'message': 'Signature is valid' if is_valid else 'Signature is INVALID'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@simple_voice_bp.route('/api/wall/feed')
def get_wall_feed():
    """
    Get anonymous voice memo wall feed with live wordmap

    Like 9gag + Bitcoin - decentralized voice memos competing on collective wordmap

    Query params:
        domain: Domain to show (default: cringeproof.com)
        limit: Number of recent memos (default: 20)

    Returns:
        {
            'success': true,
            'domain': 'cringeproof.com',
            'memos': [
                {
                    'id': recording_id,
                    'transcription': text,
                    'created_at': timestamp,
                    'time_ago': '3 mins ago',
                    'audio_url': '/api/simple-voice/download/...',
                    'top_words': ['word1', 'word2', ...]
                }
            ],
            'wordmap': {
                'top_words': [['word', count], ...],
                'total_words': count,
                'contributor_count': num_users,
                'last_updated': timestamp
            }
        }
    """
    from domain_wordmap_aggregator import get_domain_wordmap
    from wordmap_pitch_integrator import extract_wordmap_from_transcript

    domain = request.args.get('domain', 'cringeproof.com')
    limit = int(request.args.get('limit', 20))

    db = get_db()

    # Get recent voice memos (anonymous)
    memos = db.execute('''
        SELECT
            r.id,
            r.transcription,
            r.created_at,
            r.file_size
        FROM simple_voice_recordings r
        WHERE r.transcription IS NOT NULL
        ORDER BY r.created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    # Format memos with time_ago
    from datetime import datetime, timezone

    def time_ago(timestamp_str):
        """Convert timestamp to 'X mins ago' format"""
        try:
            created = datetime.fromisoformat(timestamp_str)
            # Make created datetime timezone-aware (assume UTC from DB)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            # Use UTC for comparison since DB timestamps are in UTC
            now = datetime.now(timezone.utc)
            diff = now - created

            if diff.seconds < 60:
                return 'just now'
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f'{mins} min{"s" if mins != 1 else ""} ago'
            elif diff.seconds < 86400:
                hours = diff.seconds // 3600
                return f'{hours} hour{"s" if hours != 1 else ""} ago'
            else:
                days = diff.days
                return f'{days} day{"s" if days != 1 else ""} ago'
        except:
            return 'recently'

    formatted_memos = []
    for memo in memos:
        # Extract top words from this memo
        memo_wordmap = extract_wordmap_from_transcript(memo['transcription'], top_n=5)
        top_words = list(memo_wordmap.keys())[:5]

        formatted_memos.append({
            'id': memo['id'],
            'transcription': memo['transcription'],
            'created_at': memo['created_at'],
            'time_ago': time_ago(memo['created_at']),
            'audio_url': f'/api/simple-voice/stream/{memo["id"]}',
            'top_words': top_words,
            'excerpt': memo['transcription'][:200] + '...' if len(memo['transcription']) > 200 else memo['transcription']
        })

    # Get domain wordmap (collective voice)
    domain_wordmap_data = get_domain_wordmap(domain)

    wordmap_info = {
        'top_words': [],
        'total_words': 0,
        'contributor_count': 0,
        'last_updated': None
    }

    if domain_wordmap_data:
        wordmap = domain_wordmap_data['wordmap']
        sorted_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)

        wordmap_info = {
            'top_words': sorted_words[:20],  # Top 20 for visualization
            'total_words': len(wordmap),
            'contributor_count': domain_wordmap_data['contributor_count'],
            'last_updated': domain_wordmap_data['last_updated']
        }

    db.close()

    response = jsonify({
        'success': True,
        'domain': domain,
        'memos': formatted_memos,
        'wordmap': wordmap_info,
        'total_memos': len(formatted_memos)
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
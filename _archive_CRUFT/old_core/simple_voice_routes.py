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

    return render_template('simple_voice.html', user_id=user_id)


@simple_voice_bp.route('/api/simple-voice/save', methods=['POST'])
def save_voice():
    """Save recorded audio to database with optional transcription"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'success': False, 'error': 'Empty audio'}), 400

    # Get user_id from session
    user_id = session.get('user_id')

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

    db = get_db()

    # Save to database with transcription and user_id
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, len(audio_data), transcription, transcription_method, user_id))

    file_id = cursor.lastrowid
    db.commit()
    db.close()

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

    return jsonify({
        'success': True,
        'file_id': file_id,
        'filename': filename,
        'size': len(audio_data),
        'transcription': transcription,
        'transcription_method': transcription_method,
        'user_id': user_id,
        'wordmap_update': {
            'recording_count': wordmap_update['recording_count'] if wordmap_update else None,
            'is_pure_source': wordmap_update.get('is_pure_source', False) if wordmap_update else False,
            'top_words': wordmap_update.get('top_words', [])[:5] if wordmap_update else []
        } if wordmap_update else None
    })


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

    # Write to temp file and send
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        tmp.write(recording['audio_data'])
        tmp_path = tmp.name

    return send_file(tmp_path, mimetype='audio/webm')


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

    # Write to temp file and send with download header
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        tmp.write(recording['audio_data'])
        tmp_path = tmp.name

    return send_file(
        tmp_path,
        mimetype='audio/webm',
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
                   v.created_at, v.merged_count, u.username, d.domain, d.name as domain_name
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
                   v.created_at, v.merged_count, u.username, d.domain, d.name as domain_name
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
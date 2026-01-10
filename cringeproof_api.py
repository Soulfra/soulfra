#!/usr/bin/env python3
"""
CringeProof API - Isolated Voice/Screenshot Intake Microservice

Separate from main Soulfra app for:
- Independent scaling (heavy Whisper/Ollama processing)
- Isolation (debugging tool stays up when Soulfra crashes)
- Clean API for Calriven/DeathToData to access insights

Endpoints:
- POST /api/simple-voice/save - Voice recording upload
- POST /api/screenshot-text/save - Screenshot OCR text upload
- GET /api/ideas/list - List all extracted ideas
- GET /api/ideas/<id> - Get specific idea

Port: 5002 (separate from main Soulfra app on 5001)
Database: Shared soulfra.db (microservices, same data)
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from database import get_db, init_db
import os
import tempfile
import requests
from datetime import datetime, timedelta
from pathlib import Path
import secrets
import hashlib

app = Flask(__name__, static_folder='voice-archive', static_url_path='')
CORS(app, origins=[
    'https://cringeproof.com',
    'https://soulfra.github.io',  # Projects dashboard
    'http://localhost:*',
    'http://192.168.1.87:*'
], supports_credentials=True)
app.secret_key = os.environ.get('SECRET_KEY', 'cringeproof-dev-key-change-in-prod')

# Initialize database tables on startup
init_db()
print("✅ Database tables initialized (including shared_responses, scan_history, response_metrics)")

# Import auth routes
try:
    from auth_routes import auth_bp, create_users_table
    app.register_blueprint(auth_bp)
    # Initialize users table on startup
    try:
        create_users_table()
    except:
        pass  # Table might already exist
    print("✅ Auth system loaded (web routes)")
except ImportError as e:
    print(f"⚠️  Auth routes not available: {e}")

# Import auth API routes (JSON endpoints)
try:
    from auth_api import auth_api_bp
    app.register_blueprint(auth_api_bp)
    print("✅ Auth API loaded (/api/auth/login, /api/auth/me, etc.)")
except ImportError as e:
    print(f"⚠️  Auth API not available: {e}")

# Import slug claiming system
try:
    from slug_routes import slug_bp
    app.register_blueprint(slug_bp)
    print("✅ Slug system loaded (/api/claim-slug, /api/check-slug)")
except ImportError as e:
    print(f"⚠️  Slug routes not available: {e}")

# Import user page routes (/<slug> wildcard routing)
try:
    from user_page_routes import user_page_bp
    app.register_blueprint(user_page_bp)
    print("✅ User pages loaded (/<slug> with wordmap CSS)")
except ImportError as e:
    print(f"⚠️  User page routes not available: {e}")

# Import voice → README routes
try:
    from voice_readme_routes import voice_readme_bp
    app.register_blueprint(voice_readme_bp)
    print("✅ Voice → README routes loaded (/api/voice-to-readme, /api/readme-status)")
except ImportError as e:
    print(f"⚠️  Voice README routes not available: {e}")

# Import chapter routes (chapter cards, QR codes)
try:
    from chapter_routes import chapter_bp
    app.register_blueprint(chapter_bp)
    print("✅ Chapter routes loaded (/api/chapters, /chapter-card.html)")
except ImportError as e:
    print(f"⚠️  Chapter routes not available: {e}")

# Import traffic blackhole routes (THE GAME)
try:
    from traffic_blackhole import blackhole_bp
    app.register_blueprint(blackhole_bp)
    print("✅ Traffic Blackhole loaded (/void, /void-leaderboard)")
except ImportError as e:
    print(f"⚠️  Traffic Blackhole not available: {e}")

# Import collaboration minesweeper (INTERVIEW GAME)
try:
    from collaboration_minesweeper import collab_bp
    app.register_blueprint(collab_bp)
    print("✅ Collaboration Minesweeper loaded (/api/collaboration/*)")
except ImportError as e:
    print(f"⚠️  Collaboration Minesweeper not available: {e}")

# Import README-as-Profile system (NO IMAGE UPLOADS)
try:
    from readme_profile_system import profile_bp
    app.register_blueprint(profile_bp)
    print("✅ README Profile System loaded (/api/profile/*)")
except ImportError as e:
    print(f"⚠️  README Profile System not available: {e}")

# Import Voice Q&A Profile Builder
try:
    from voice_qa_profile import qa_profile_bp
    app.register_blueprint(qa_profile_bp)
    print("✅ Voice Q&A Profile Builder loaded (/api/voice-qa/*)")
    print("   - /build-profile-voice.html (Voice Q&A interface)")
    print("   - /api/voice-qa/answer (Process voice answers)")
    print("   - /api/voice-qa/results/<session_id> (Get analysis)")
    print("   - /api/voice-qa/claim-github (Claim with GitHub OAuth)")
except ImportError as e:
    print(f"⚠️  Voice Q&A Profile Builder not available: {e}")

# Import Soul Document System
try:
    from soul_document_routes import soul_bp
    app.register_blueprint(soul_bp)
    print("✅ Soul Document System loaded (/api/soul/*)")
    print("   - /soul (Soul dashboard)")
    print("   - /api/soul/current (Get active soul document)")
    print("   - /api/soul/vote (Rate AI response vibe)")
    print("   - /api/soul/stats (System statistics)")
    print("   - Community-votable AI personality")
except ImportError as e:
    print(f"⚠️  Soul Document System not available: {e}")

# Import Soul Leaderboard (Reddit-style ranking for AI agents)
try:
    from soul_leaderboard_routes import soul_leaderboard_bp
    app.register_blueprint(soul_leaderboard_bp)
    print("✅ Soul Leaderboard loaded (/api/soul/agents, /api/soul/vote-agent)")
    print("   - /soul/leaderboard (Ranked AI agents)")
    print("   - /soul/feed-page (Live cheering feed)")
    print("   - Reddit hot score ranking")
except ImportError as e:
    print(f"⚠️  Soul Leaderboard not available: {e}")

# Import Share Routes (Shareable AI responses with QR codes)
try:
    from share_routes import share_bp
    app.register_blueprint(share_bp)
    print("✅ Share Routes loaded (/adaptive, /scanner, /share/<id>)")
    print("   - /adaptive (Device-responsive interface)")
    print("   - /scanner (QR/UPC scanner)")
    print("   - /share/<id> (Shareable responses)")
    print("   - /api/share/create (Create shareable response)")
    print("   - /api/share/validate (Validate QR scan)")
    print("   - /api/share/feed (Unified content feed)")
    print("   - SHA-256 verification + time-series metrics")
except ImportError as e:
    print(f"⚠️  Share Routes not available: {e}")

# Import Debug Routes (Local dashboard to see everything)
try:
    from debug_routes import debug_bp
    app.register_blueprint(debug_bp)
    print("✅ Debug Dashboard loaded (/debug)")
    print("   - /debug (Visual database + component browser)")
    print("   - /api/debug/database (All tables + counts)")
    print("   - /api/debug/qr-codes (All QR codes with previews)")
    print("   - /api/debug/components (All HTML files)")
    print("   - /api/debug/routes (All Flask routes)")
except ImportError as e:
    print(f"⚠️  Debug Dashboard not available: {e}")

# Import Message Routes (IRC/Usenet-style messaging)
try:
    from message_routes import message_bp
    app.register_blueprint(message_bp)
    print("✅ Message System loaded (/api/send-message, /api/messages/*)")
    print("   - /api/send-message (Send to domain/channel)")
    print("   - /api/messages/<domain>.json (Get all messages)")
    print("   - /api/messages/<domain>/<channel> (Channel messages)")
    print("   - /api/channels (List all channels)")
    print("   - IRC/Usenet architecture for 2045 Email System")
except ImportError as e:
    print(f"⚠️  Message System not available: {e}")

# GitHub webhook configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO_OWNER = 'Soulfra'
GITHUB_REPO_NAME = 'voice-archive'

# Import Whisper/Ollama modules
try:
    from whisper_transcriber import WhisperTranscriber
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️  Whisper not available")

try:
    from ollama_client import OllamaClient
    from voice_idea_board_routes import extract_ideas_from_transcript
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️  Ollama not available")

try:
    from classify_idea import classify_idea, classify_and_store
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False
    print("⚠️  Classifier not available")

try:
    from prohibited_words_filter import check_prohibited, log_prohibited_detection
    PROHIBITED_FILTER_AVAILABLE = True
except ImportError:
    PROHIBITED_FILTER_AVAILABLE = False
    print("⚠️  Prohibited words filter not available")


def generate_public_hash():
    """Generate short, URL-safe hash for public sharing"""
    # Use 8 random bytes = 16 hex chars (like YouTube video IDs)
    return secrets.token_urlsafe(8)[:11]  # 11 chars, URL-safe

def calculate_expiry(user_id):
    """Calculate expiry time based on user tier"""
    if not user_id:
        # Anonymous: 24 hours
        return datetime.now() + timedelta(hours=24), 'anonymous'

    # TODO: Check user's actual tier from database
    # For now: logged-in users get 7 days
    return datetime.now() + timedelta(days=7), 'free'

def trigger_site_rebuild():
    """
    Trigger GitHub Actions workflow to rebuild voice-archive static site

    Sends repository_dispatch event to voice-archive repo
    """
    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set - skipping site rebuild trigger")
        return False

    url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/dispatches'
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    data = {
        'event_type': 'new-voice-recording',
        'client_payload': {
            'timestamp': datetime.now().isoformat(),
            'source': 'cringeproof-api'
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 204:
            print(f"✅ Site rebuild triggered successfully")
            return True
        else:
            print(f"⚠️  Site rebuild trigger failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Site rebuild trigger error: {e}")
        return False


@app.route('/')
def root():
    """Unified Ecosystem Dashboard"""
    db = get_db()

    # Voice System Stats
    try:
        idea_count = db.execute('SELECT COUNT(*) FROM voice_ideas').fetchone()[0]
    except:
        idea_count = 0

    try:
        recording_count = db.execute('SELECT COUNT(*) FROM simple_voice_recordings').fetchone()[0]
    except:
        recording_count = 0

    # User System Stats
    try:
        user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    except:
        user_count = 0

    try:
        slug_count = db.execute('SELECT COUNT(DISTINCT user_slug) FROM users WHERE user_slug IS NOT NULL').fetchone()[0]
    except:
        slug_count = 0

    # Chapter System Stats
    try:
        chapter_count = db.execute('SELECT COUNT(*) FROM chapter_snapshots').fetchone()[0]
    except:
        chapter_count = 0

    # Domain System Stats
    try:
        domain_count = db.execute('SELECT COUNT(*) FROM domain_wordmaps').fetchone()[0]
    except:
        domain_count = 0

    db.close()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CringeProof API</title>
        <style>
            body {{ font-family: monospace; max-width: 1000px; margin: 50px auto; padding: 20px; background: #000; color: #0f0; }}
            h1 {{ color: #ff006e; }}
            h4 {{ color: #8338ec; margin-top: 15px; margin-bottom: 8px; }}
            .status {{ background: #111; padding: 20px; border: 2px solid #0f0; margin: 20px 0; }}
            .stat-section {{ margin: 15px 0; padding: 10px; border-left: 3px solid #8338ec; }}
            .endpoint {{ background: #111; padding: 15px; margin: 10px 0; border-left: 4px solid #0f0; }}
            .method {{ color: #ff006e; font-weight: bold; }}
            .quick-links {{ background: #111; padding: 20px; border: 2px solid #0ff; margin: 20px 0; }}
            .quick-links a {{ display: inline-block; margin: 5px 10px; padding: 8px 15px; background: #222; border-radius: 4px; text-decoration: none; }}
            .quick-links a:hover {{ background: #333; }}
            a {{ color: #0ff; }}
            .available {{ color: #0f0; }}
            .unavailable {{ color: #f00; }}
        </style>
    </head>
    <body>
        <h1>🚫 CringeProof API - Isolated Microservice</h1>

        <div class="status">
            <h3>📊 Ecosystem Stats</h3>

            <div class="stat-section">
                <h4>🎤 Voice System</h4>
                <p><strong>Recordings Saved:</strong> {recording_count}</p>
                <p><strong>Ideas Extracted:</strong> {idea_count}</p>
            </div>

            <div class="stat-section">
                <h4>👤 User System</h4>
                <p><strong>Total Users:</strong> {user_count}</p>
                <p><strong>Claimed Slugs:</strong> {slug_count}</p>
            </div>

            <div class="stat-section">
                <h4>📖 Chapter System</h4>
                <p><strong>Total Chapters:</strong> {chapter_count}</p>
            </div>

            <div class="stat-section">
                <h4>🌐 Domain System</h4>
                <p><strong>Domains Synced:</strong> {domain_count}</p>
            </div>

            <div class="stat-section">
                <h4>⚙️ Services</h4>
                <p><strong>Whisper:</strong> <span class="{'available' if WHISPER_AVAILABLE else 'unavailable'}">{'✅' if WHISPER_AVAILABLE else '❌'}</span></p>
                <p><strong>Ollama:</strong> <span class="{'available' if OLLAMA_AVAILABLE else 'unavailable'}">{'✅' if OLLAMA_AVAILABLE else '❌'}</span></p>
                <p><strong>Database:</strong> <span class="available">✅</span></p>
            </div>
        </div>

        <div class="quick-links">
            <h3>🔗 Quick Links</h3>
            <div>
                <a href="/matt">👤 Example User Page (matt)</a>
                <a href="/chapter-card.html?id=11">📖 Example Chapter Card</a>
                <a href="/api/chapters/list">📚 Browse Chapters (JSON)</a>
                <a href="/record-v2.html">🎤 Voice Recorder</a>
                <a href="/wall.html">🧱 Voice Wall</a>
                <a href="/api/readme-status/soulfra">📄 README Status</a>
            </div>
        </div>

        <h3>🎯 API Endpoints</h3>

        <div class="endpoint">
            <p><span class="method">GET</span> <a href="/health">/health</a></p>
            <p>Health check for PM2 monitoring</p>
        </div>

        <div class="endpoint">
            <p><span class="method">POST</span> /api/simple-voice/save</p>
            <p>Upload voice recording → Whisper transcription → Ollama idea extraction</p>
        </div>

        <div class="endpoint">
            <p><span class="method">POST</span> /api/screenshot-text/save</p>
            <p>Upload OCR text from screenshot → Ollama idea extraction</p>
        </div>

        <div class="endpoint">
            <p><span class="method">GET</span> <a href="/api/ideas/list">/api/ideas/list</a></p>
            <p>List all extracted ideas (for debugging)</p>
        </div>

        <div class="endpoint">
            <p><span class="method">GET</span> /api/ideas/&lt;id&gt;</p>
            <p>Get specific idea by ID</p>
        </div>

        <hr>
        <p>🔒 <strong>CORS Enabled:</strong> cringeproof.com</p>
        <p>📊 <strong>Database:</strong> Shared soulfra.db (microservices)</p>
        <p>🎯 <strong>Purpose:</strong> Isolated intake for CringeProof/Calriven/DeathToData</p>
        <p>🌐 <strong>Frontend:</strong> <a href="https://cringeproof.com">cringeproof.com</a></p>
    </body>
    </html>
    """

    return html


@app.route('/favicon.ico')
def favicon():
    """Favicon (prevents 404 spam in logs)"""
    return '', 204


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for PM2 monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'cringeproof-api',
        'whisper': WHISPER_AVAILABLE,
        'ollama': OLLAMA_AVAILABLE,
        'classifier': CLASSIFIER_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/simple-voice/save', methods=['POST', 'OPTIONS'])
def save_voice_recording():
    """
    Save voice recording, transcribe with Whisper, extract ideas with Ollama

    Accepts: multipart/form-data with 'audio' file
    Returns: {'success': True, 'recording_id': int, 'idea_id': int}
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']

    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
    audio_file.save(temp_file.name)
    temp_file.close()

    # Get user_id from session (optional)
    user_id = session.get('user_id')

    # Read audio data
    with open(temp_file.name, 'rb') as f:
        audio_data = f.read()

    file_size = len(audio_data)
    filename = audio_file.filename or f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

    # Save to database
    db = get_db()
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, user_id)
        VALUES (?, ?, ?, ?)
    ''', (filename, audio_data, file_size, user_id))

    recording_id = cursor.lastrowid
    db.commit()

    # Transcribe with Whisper (if available)
    transcription = None
    prohibited_content_detected = False
    if WHISPER_AVAILABLE:
        try:
            transcriber = WhisperTranscriber()
            transcription_result = transcriber.transcribe(temp_file.name)
            transcription = transcription_result.get('text', '') if isinstance(transcription_result, dict) else transcription_result
            print(f"🎤 Transcription result: {transcription}")

            # Check for prohibited words BEFORE storing
            if PROHIBITED_FILTER_AVAILABLE and transcription:
                is_prohibited, matches = check_prohibited(transcription, domain="all")
                if is_prohibited:
                    prohibited_content_detected = True
                    log_prohibited_detection(recording_id, matches)
                    print(f"⚠️  Prohibited content detected in recording #{recording_id}: {len(matches)} matches")

                    # Option 1: Reject recording entirely
                    # db.execute('DELETE FROM simple_voice_recordings WHERE id = ?', (recording_id,))
                    # db.commit()
                    # return jsonify({'success': False, 'error': 'Prohibited content detected'}), 400

                    # Option 2: Store but flag for review (chosen approach)
                    # Continue processing but mark as flagged

            print(f"💾 Saving transcription to DB for recording #{recording_id}: {transcription[:50]}...")
            db.execute('''
                UPDATE simple_voice_recordings
                SET transcription = ?, transcription_method = 'whisper'
                WHERE id = ?
            ''', (transcription, recording_id))
            db.commit()
            print(f"✅ Transcription saved to database for recording #{recording_id}")
        except Exception as e:
            print(f"⚠️  Whisper transcription failed: {e}")

    # Extract ideas with Ollama (if available and transcribed)
    idea_id = None
    domain_matches = None
    if OLLAMA_AVAILABLE and transcription:
        try:
            user_id = user_id or 1  # Default user if not logged in
            ideas = extract_ideas_from_transcript(transcription, recording_id, user_id)
            idea_id = ideas[0]['id'] if ideas else None

            # Classify idea to domain (if classifier available)
            if CLASSIFIER_AVAILABLE and idea_id and transcription:
                try:
                    domain_matches = classify_idea(transcription)
                    # Store best match in database
                    if domain_matches and domain_matches[0]['score'] > 0:
                        classify_and_store(idea_id, transcription)
                        print(f"🎯 Idea #{idea_id} classified to: {domain_matches[0]['domain']} ({domain_matches[0]['score']:.0%})")
                except Exception as e:
                    print(f"⚠️  Domain classification failed: {e}")

        except Exception as e:
            print(f"⚠️  Ollama extraction failed: {e}")

    # Generate public hash and expiry for INSTANT SHARING
    public_hash = generate_public_hash()
    expiry_time, tier = calculate_expiry(user_id)

    # Update voice_ideas with hash and expiry
    if idea_id:
        db.execute('''
            UPDATE voice_ideas
            SET public_hash = ?, expiry_timestamp = ?, tier = ?
            WHERE id = ?
        ''', (public_hash, expiry_time, tier, idea_id))
        db.commit()
        print(f"🔗 Public share link created: /i/{public_hash} (expires: {expiry_time}, tier: {tier})")

        # Generate OG image for instant sharing
        try:
            from image_composer import ImageComposer

            # Get idea title from database
            idea_data = db.execute('SELECT title, text FROM voice_ideas WHERE id = ?', (idea_id,)).fetchone()
            idea_title = idea_data['title'] if idea_data else "Voice Idea"
            idea_text = idea_data['text'] if idea_data else ""

            # Truncate title if too long
            if len(idea_title) > 50:
                idea_title = idea_title[:47] + "..."

            # Create share URL
            share_url = f"https://cringeproof.com/i/{public_hash}"

            # Compose OG image (1200x630 for social media)
            composer = ImageComposer(size=(1200, 630))

            # Gradient background
            composer.add_layer('gradient', colors=['#ff006e', '#000'], angle=135)

            # Title text
            composer.add_layer('text',
                content=idea_title,
                font='impact',
                size=72,
                color='#fff',
                position='center',
                shadow={'offset': (4, 4), 'blur': 8, 'color': '#000'}
            )

            # QR code in bottom right
            composer.add_layer('qr', url=share_url, position='bottom-right', size=150)

            # Render to bytes
            image_bytes = composer.render()

            # Ensure directory exists
            share_dir = f"voice-archive/i/{public_hash}"
            os.makedirs(share_dir, exist_ok=True)

            # Save OG image
            og_image_path = f"{share_dir}/og.png"
            with open(og_image_path, 'wb') as f:
                f.write(image_bytes)

            print(f"🎨 OG image generated: {og_image_path}")

        except Exception as e:
            print(f"⚠️  OG image generation failed: {e}")
            # Don't fail the entire request if image generation fails

    # Clean up temp file
    os.unlink(temp_file.name)

    db.close()

    # Trigger site rebuild (async, don't wait for response)
    if idea_id:
        trigger_site_rebuild()

    # Build public URL (use request.host for dynamic domain)
    public_url = f"{request.scheme}://{request.host}/i/{public_hash}" if idea_id else None

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'transcription': transcription,
        'idea_id': idea_id,
        'domain_matches': domain_matches[:3] if domain_matches else None,  # Top 3 matches
        'message': 'Recording saved and processed',
        # INSTANT SHARING FEATURE
        'public_url': public_url,
        'public_hash': public_hash if idea_id else None,
        'expires_at': expiry_time.isoformat() if idea_id else None,
        'tier': tier
    })


@app.route('/api/screenshot-text/save', methods=['POST', 'OPTIONS'])
def save_screenshot_text():
    """
    Save OCR text from screenshot and extract insights with Ollama

    Accepts: JSON {'text': 'extracted OCR text'}
    Returns: {'success': True, 'recording_id': int, 'idea_id': int}
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    # Get user_id from session
    user_id = session.get('user_id')

    # Save text as "transcription" - reuse voice recording table
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    db = get_db()

    # Save to database (no audio_data for screenshots)
    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, None, len(text.encode('utf-8')), text, 'screenshot-ocr', user_id))

    recording_id = cursor.lastrowid
    db.commit()

    # Extract ideas with Ollama (if available)
    idea_id = None
    if OLLAMA_AVAILABLE:
        try:
            user_id = user_id or 1  # Default user if not logged in
            ideas = extract_ideas_from_transcript(text, recording_id, user_id)
            idea_id = ideas[0]['id'] if ideas else None
        except Exception as e:
            print(f"⚠️  Ollama extraction failed: {e}")

    db.close()

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'text_length': len(text),
        'idea_id': idea_id,
        'message': 'Screenshot text saved and processed'
    })


@app.route('/api/ideas/list', methods=['GET'])
def list_ideas():
    """List all extracted ideas (for debugging by Calriven/DeathToData)"""
    db = get_db()

    # Try to get ideas from database (table name may vary)
    try:
        ideas = db.execute('''
            SELECT id, title, description, created_at, recording_id
            FROM ideas
            ORDER BY created_at DESC
            LIMIT 100
        ''').fetchall()
    except:
        # Fallback: show recordings with transcriptions
        ideas = db.execute('''
            SELECT id, filename as title, transcription as description,
                   created_at, id as recording_id
            FROM simple_voice_recordings
            WHERE transcription IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 100
        ''').fetchall()

    db.close()

    return jsonify({
        'ideas': [dict(row) for row in ideas],
        'count': len(ideas)
    })


@app.route('/api/ideas/<int:idea_id>', methods=['GET'])
def get_idea(idea_id):
    """Get specific idea details"""
    db = get_db()

    try:
        idea = db.execute('SELECT * FROM ideas WHERE id = ?', (idea_id,)).fetchone()
    except:
        idea = db.execute('SELECT * FROM simple_voice_recordings WHERE id = ?', (idea_id,)).fetchone()

    db.close()

    if not idea:
        return jsonify({'error': 'Idea not found'}), 404

    return jsonify(dict(idea))


@app.route('/api/ideas/suggest/<word>', methods=['GET'])
def suggest_ideas_by_word(word):
    """
    Suggest ideas containing a specific word from wordmap

    Returns recordings/ideas where transcription contains the word
    """
    db = get_db()

    # Search in simple_voice_recordings transcriptions
    search_pattern = f'%{word}%'

    try:
        recordings = db.execute('''
            SELECT id, filename, transcription, created_at
            FROM simple_voice_recordings
            WHERE transcription LIKE ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (search_pattern,)).fetchall()

        results = []
        for rec in recordings:
            results.append({
                'id': rec['id'],
                'filename': rec['filename'],
                'transcription': rec['transcription'][:200] if rec['transcription'] else None,
                'created_at': rec['created_at'],
                'type': 'recording'
            })

        db.close()

        return jsonify({
            'word': word,
            'count': len(results),
            'ideas': results
        })

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/classify', methods=['POST', 'OPTIONS'])
def classify_text():
    """
    Classify text to domains (CringeProof filter endpoint)

    POST body: {'text': 'your idea or transcription'}

    Returns:
        {
            'domains': [
                {'domain': 'cringeproof.com', 'score': 0.87, 'matches': ['social', 'cringe']},
                ...
            ]
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    if not CLASSIFIER_AVAILABLE:
        return jsonify({'error': 'Classifier not available'}), 503

    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing "text" field'}), 400

    text = data['text']

    if not text or len(text.strip()) == 0:
        return jsonify({'error': 'Empty text'}), 400

    try:
        domain_matches = classify_idea(text)

        return jsonify({
            'text': text[:100],  # Echo first 100 chars
            'domains': domain_matches[:5],  # Top 5 matches
            'best_match': domain_matches[0] if domain_matches else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Import and register activity routes
try:
    from recent_activity_api import register_activity_routes
    register_activity_routes(app)
    print("✅ Activity API routes loaded")
except ImportError as e:
    print(f"⚠️  Activity routes not available: {e}")

# Import Cal avatar generator
try:
    from cal_avatar_generator import generate_cal_avatar, generate_cal_avatar_from_email
    CAL_AVATAR_AVAILABLE = True
    print("✅ Cal avatar generator loaded")
except ImportError as e:
    CAL_AVATAR_AVAILABLE = False
    print(f"⚠️  Cal avatar generator not available: {e}")

@app.route('/api/encyclopedia/word-of-year', methods=['GET'])
def get_word_of_year():
    """Get Word of the Year (top word across all recordings)"""
    from encyclopedia_engine import EncyclopediaEngine
    engine = EncyclopediaEngine()
    result = engine.get_word_of_period('year')
    return jsonify(result if result else {'word': 'N/A', 'count': 0, 'total_recordings': 0})

@app.route('/api/encyclopedia/progression', methods=['GET'])
def get_progression():
    """Get user progression and unlocked features"""
    from encyclopedia_engine import EncyclopediaEngine
    user_id = request.args.get('user_id', 1, type=int)
    engine = EncyclopediaEngine()
    result = engine.check_feature_unlock(user_id)
    return jsonify(result)

@app.route('/api/encyclopedia/year-in-review', methods=['GET'])
def get_year_in_review():
    """Generate Year in Review report"""
    from encyclopedia_engine import EncyclopediaEngine
    from datetime import datetime
    year = request.args.get('year', datetime.now().year, type=int)
    user_id = request.args.get('user_id', type=int)
    engine = EncyclopediaEngine()
    result = engine.generate_year_in_review(year, user_id)
    return jsonify(result if result else {'error': 'No data for this year'})

@app.route('/api/squad/match', methods=['GET'])
def find_squad():
    """
    Find squad members based on wordmap similarity

    Returns users with similar vocabulary/interests
    """
    from user_wordmap_engine import get_user_wordmap, compare_user_wordmaps

    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    # Get user's wordmap
    user_wordmap = get_user_wordmap(user_id)

    if not user_wordmap:
        return jsonify({'error': 'No wordmap found - record a voice memo first'}), 404

    # Get all other users with wordmaps
    db = get_db()
    other_users = db.execute('''
        SELECT DISTINCT u.id, u.display_name as email, uw.wordmap_json, uw.recording_count
        FROM users u
        JOIN user_wordmaps uw ON u.id = uw.user_id
        WHERE u.id != ?
    ''', (user_id,)).fetchall()

    squad = []

    for other_user in other_users:
        # Compare wordmaps
        comparison = compare_user_wordmaps(user_id, other_user['id'])

        if 'error' not in comparison and comparison['similarity_score'] > 0.1:  # 10% similarity threshold
            squad.append({
                'user_id': other_user['id'],
                'email': other_user['email'],
                'similarity': comparison['similarity_score'],
                'shared_words': comparison['overlap_words'][:10],
                'recording_count': other_user['recording_count'],
                'unique_words': comparison['overlap_count']
            })

    # Sort by similarity (highest first)
    squad.sort(key=lambda x: x['similarity'], reverse=True)

    return jsonify({
        'user_id': user_id,
        'squad': squad[:10],  # Top 10 matches
        'total_matches': len(squad)
    })

# Import wall comments routes
try:
    from wall_comments_api import register_wall_comments_routes
    register_wall_comments_routes(app)
except ImportError as e:
    print(f"⚠️  Wall comments routes not available: {e}")

# Import simple voice routes (includes /api/wall/feed)
try:
    from simple_voice_routes import simple_voice_bp
    app.register_blueprint(simple_voice_bp)
    print("✅ Simple voice routes loaded (includes /api/wall/feed)")
except ImportError as e:
    print(f"⚠️  Simple voice routes not available: {e}")

# Domain Studio - Random question prompt from domains.json
@app.route('/api/domain-studio/question', methods=['GET'])
def get_random_domain_question():
    """
    Returns a random domain and random question from that domain's prompts

    Response: {
        "domain": "cringeproof",
        "domain_info": {...},
        "question": "What's the cringiest thing you see on social media?"
    }
    """
    import json
    import random

    try:
        with open('domains.json', 'r') as f:
            domains_data = json.load(f)

        # Filter domains that have prompts
        domains_with_prompts = {
            name: info for name, info in domains_data['domains'].items()
            if 'prompts' in info and info['prompts']
        }

        if not domains_with_prompts:
            return jsonify({'error': 'No domains with prompts configured'}), 500

        # Pick random domain
        domain_name = random.choice(list(domains_with_prompts.keys()))
        domain_info = domains_with_prompts[domain_name]

        # Pick random question from that domain
        question = random.choice(domain_info['prompts'])

        return jsonify({
            'domain': domain_name,
            'domain_info': {
                'description': domain_info.get('description'),
                'theme': domain_info.get('theme'),
                'color': domain_info.get('color'),
                'url': domain_info.get('url')
            },
            'question': question
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load question: {str(e)}'}), 500

# Domain Question of the Day (deterministic based on date)
@app.route('/api/domain/<domain_name>/question-of-day', methods=['GET'])
def get_domain_question_of_day(domain_name):
    """Returns the same question for this domain all day (changes at midnight)"""
    import json
    import random

    # Hardcoded prompts as fallback (TODO: move to database or separate config)
    DEFAULT_PROMPTS = {
        'cringeproof': [
            "What's the cringiest thing you see on social media right now?",
            "How would you explain CringeProof to someone in 30 seconds?",
            "What feature would make people record their first voice memo?",
            "Why would someone choose voice over text?",
            "What's one word that should never appear on the wordmap?"
        ],
        'soulfra': [
            "Why don't people trust AI companies with their data?",
            "What makes Soulfra different from OpenAI or Anthropic?",
            "How would you route a prompt to the best AI model?",
            "What's the core problem with using multiple AI providers?",
            "Who would pay for AI routing infrastructure?"
        ],
        'calriven': [
            "What's broken about Substack or Medium?",
            "Why would a creator want federated publishing?",
            "How do you monetize without ads or paywalls?",
            "What's the first feature you'd ship?",
            "Who owns the content on Calriven?"
        ],
        'deathtodata': [
            "What if Google paid you for your search data?",
            "How do you value someone's search history?",
            "What's the 'vibes economy'?",
            "Would you sell your browsing data for $5/month?",
            "How is this different from Brave Browser?"
        ]
    }

    try:
        # Use today's date as seed for deterministic "random" question
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        seed_value = hash(domain_name + today)
        random.seed(seed_value)

        prompts = DEFAULT_PROMPTS.get(domain_name, ["What's your thought on " + domain_name + "?"])
        question = random.choice(prompts)

        # Try to load domain info from domains.json
        domain_info = {'color': '#00C49A', 'description': domain_name}
        try:
            with open('domains.json', 'r') as f:
                domains_data = json.load(f)

            # Handle new array format
            if isinstance(domains_data.get('domains'), list):
                for d in domains_data['domains']:
                    if d.get('slug') == domain_name:
                        domain_info = {
                            'color': d.get('theme', {}).get('primary', '#00C49A'),
                            'description': d.get('tagline', d.get('name')),
                            'theme': d.get('category'),
                            'url': f"https://{d.get('domain')}"
                        }
                        break
            # Handle old object format
            elif domain_name in domains_data.get('domains', {}):
                d = domains_data['domains'][domain_name]
                domain_info = {
                    'color': d.get('color', '#00C49A'),
                    'description': d.get('description'),
                    'theme': d.get('theme'),
                    'url': d.get('url')
                }
        except:
            pass  # Use defaults if file can't be loaded

        return jsonify({
            'domain': domain_name,
            'question': question,
            'domain_info': domain_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Recent answers for a domain
@app.route('/api/domain/<domain_name>/recent-answers', methods=['GET'])
def get_domain_recent_answers(domain_name):
    """Get recent voice recordings for this domain"""
    try:
        limit = request.args.get('limit', 5, type=int)

        db = get_db()
        recordings = db.execute('''
            SELECT id, filename, created_at, transcription, prompt_question, LENGTH(audio_data) as audio_size
            FROM simple_voice_recordings
            WHERE domain = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (domain_name, limit)).fetchall()
        db.close()

        answers = []
        for rec in recordings:
            # Calculate time ago
            from datetime import datetime
            try:
                created = datetime.fromisoformat(rec['created_at'].replace('T', ' '))
                now = datetime.now()
                delta = now - created

                if delta.seconds < 60:
                    time_ago = f"{delta.seconds}s ago"
                elif delta.seconds < 3600:
                    time_ago = f"{delta.seconds // 60}m ago"
                elif delta.total_seconds() < 86400:
                    time_ago = f"{int(delta.total_seconds() // 3600)}h ago"
                else:
                    time_ago = f"{delta.days}d ago"
            except:
                time_ago = "recently"

            answers.append({
                'id': rec['id'],
                'audio_url': f'/api/simple-voice/download/{rec["id"]}',
                'duration': rec['audio_size'] // 16000 if rec['audio_size'] else 0,  # Rough estimate
                'time_ago': time_ago,
                'excerpt': rec['transcription'][:100] if rec['transcription'] else None,
                'question': rec['prompt_question']
            })

        return jsonify({
            'domain': domain_name,
            'answers': answers,
            'total': len(answers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve HTML pages from voice-archive folder
@app.route('/')
def index():
    return send_from_directory('voice-archive', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve any HTML/CSS/JS from voice-archive folder"""
    return send_from_directory('voice-archive', path)

if __name__ == '__main__':
    # Check for SSL certs (in project root)
    cert_file = 'cert.pem'
    key_file = 'key.pem'

    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        # Fallback to mkcert certs
        cert_file = 'localhost+4.pem'
        key_file = 'localhost+4-key.pem'

    if os.path.exists(cert_file) and os.path.exists(key_file):
        ssl_context = (cert_file, key_file)
        print("🔒 HTTPS enabled")
        print(f"   Access: https://192.168.1.87:5002")
    else:
        ssl_context = None
        print("⚠️  HTTP only (no SSL certs)")
        print(f"   Access: http://192.168.1.87:5002")

    print("🚀 CringeProof API - Isolated Microservice")
    print("=" * 60)
    print("📍 Endpoint: https://192.168.1.87:5002")
    print("🎤 Voice Upload: POST /api/simple-voice/save")
    print("📸 Screenshot OCR: POST /api/screenshot-text/save")
    print("💡 List Ideas: GET /api/ideas/list")
    print("📡 Recent Activity: GET /api/recent-activity")
    print("🏆 Top Contributors: GET /api/top-contributors")
    print("🔍 Health Check: GET /health")
    print("=" * 60)
    print("🔒 CORS enabled for cringeproof.com")
    print("📊 Shared database: soulfra.db")
    print("=" * 60)
    print()
    app.run(host='0.0.0.0', port=5002, debug=True, ssl_context=ssl_context)

# PUBLIC SHARING ROUTES - bore.pub style instant links

@app.route('/i/<hash>', methods=['GET'])
def public_idea(hash):
    """
    PUBLIC view of voice idea - works like bore.pub
    
    No auth required - anyone with the link can view
    Checks expiry timestamp
    """
    db = get_db()
    
    idea = db.execute('''
        SELECT v.id, v.title, v.text, v.score, v.ai_insight, v.status,
               v.created_at, v.public_hash, v.expiry_timestamp, v.tier,
               u.username
        FROM voice_ideas v
        LEFT JOIN users u ON v.user_id = u.id
        WHERE v.public_hash = ?
    ''', (hash,)).fetchone()
    
    db.close()
    
    if not idea:
        return jsonify({'error': 'Idea not found or link expired'}), 404
    
    # Check if expired
    if idea['expiry_timestamp']:
        expiry = datetime.fromisoformat(idea['expiry_timestamp'])
        if datetime.now() > expiry:
            return jsonify({
                'error': 'Link expired',
                'expired_at': idea['expiry_timestamp'],
                'tier': idea['tier'],
                'message': 'Sign up to keep your ideas forever!'
            }), 410  # 410 Gone
    
    # Return public view
    return jsonify({
        'id': idea['id'],
        'title': idea['title'],
        'text': idea['text'],
        'score': idea['score'],
        'insight': idea['ai_insight'],
        'created_at': idea['created_at'],
        'author': idea['username'] or 'Anonymous',
        'tier': idea['tier'],
        'expires_at': idea['expiry_timestamp'],
        'share_url': f"{request.scheme}://{request.host}/i/{hash}"
    })


# CAL AVATAR ROUTES

@app.route('/api/cal-avatar/<int:user_id>.svg', methods=['GET'])
def cal_avatar_svg(user_id):
    """
    Generate Cal avatar SVG from user's wordmap

    GET /api/cal-avatar/123.svg
    Returns: SVG image
    """
    if not CAL_AVATAR_AVAILABLE:
        return jsonify({'error': 'Cal avatar generator not available'}), 503

    try:
        svg = generate_cal_avatar(user_id)
        return svg, 200, {'Content-Type': 'image/svg+xml'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cal-avatar/email/<email_hash>.svg', methods=['GET'])
def cal_avatar_email_svg(email_hash):
    """
    Generate Cal avatar from email hash (for users without wordmaps)

    GET /api/cal-avatar/email/abc123.svg
    Returns: SVG image
    """
    if not CAL_AVATAR_AVAILABLE:
        return jsonify({'error': 'Cal avatar generator not available'}), 503

    try:
        # Generate avatar from email hash
        svg = generate_cal_avatar_from_email(email_hash)
        return svg, 200, {'Content-Type': 'image/svg+xml'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500


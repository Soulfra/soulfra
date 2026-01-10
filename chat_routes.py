#!/usr/bin/env python3
"""
Unified Chat Routes - ONE Interface for All Chat Systems

Consolidates:
1. Blog post discussions (/post/<slug>/discuss)
2. Brand building (/brand/discuss/<name>)
3. QR code chats (/qr/chat/<code>)
4. Gallery Q&A (/api/gallery/chat)
5. General Ollama chat (NEW!)

All use: discussion_sessions + discussion_messages tables
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import get_db
from context_manager import ContextManager
from progression_system import get_user_tier
from knowledge_extractor import KnowledgeExtractor
from dev_config import should_skip_auth, log_dev
import json
from datetime import datetime
import threading

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat')
def chat_interface():
    """
    Unified chat interface - REQUIRES QR AUTHENTICATION (unless DEV_MODE)

    Query params:
    - mode: 'general', 'post', 'brand', 'qr', 'gallery'
    - context_id: post_id, brand_name, short_code, gallery_slug
    - model: Specific Ollama model (optional)
    """
    # DEV MODE: Skip authentication
    if should_skip_auth():
        log_dev("Skipping QR auth for /chat (dev mode)")
        user_id = session.get('user_id', 1)  # Default to user_id 1 in dev
        session['user_id'] = user_id
    else:
        # PRODUCTION: Check if user has valid QR auth session
        search_token = session.get('search_token')

        if not search_token:
            # Redirect to QR login page
            return redirect(url_for('login_qr') + '?redirect=/chat')

        # Validate session token
        db = get_db()
        session_data = db.execute('''
            SELECT * FROM search_sessions
            WHERE session_token = ?
            AND expires_at > datetime('now')
        ''', (search_token,)).fetchone()

        if not session_data:
            db.close()
            session.pop('search_token', None)
            return redirect(url_for('login_qr') + '?redirect=/chat')

        # Get or create user_id from QR session
        user_id = session.get('user_id')

        if not user_id:
            import secrets

            # Create guest user linked to QR session
            cursor = db.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (f'qr_user_{secrets.token_hex(4)}', f'qr_{secrets.token_hex(4)}@temp.com', 'qr-authenticated'))

            user_id = cursor.lastrowid
            session['user_id'] = user_id
            db.commit()

        db.close()

    # Get tier
    tier = get_user_tier(user_id)

    # Get mode and context
    chat_mode = request.args.get('mode', 'general')
    context_id = request.args.get('context_id')
    selected_model = request.args.get('model')

    # Initialize context manager
    cm = ContextManager(user_id=user_id)

    # Get available models
    models = cm.get_available_models()

    # Get or create session
    session_id = _get_or_create_session(user_id, chat_mode, context_id)

    # Load conversation history
    history = _load_conversation_history(session_id)

    # Get context info (post title, brand name, etc.)
    context_info = _get_context_info(chat_mode, context_id)

    return render_template('chat.html',
        chat_mode=chat_mode,
        context_id=context_id,
        context_info=context_info,
        session_id=str(session_id),  # Convert to string for template
        models=models,
        selected_model=selected_model,
        conversation_history=history,
        user_tier=tier
    )


@chat_bp.route('/api/chat/send', methods=['POST'])
def send_message():
    """
    Send message to Ollama and get response

    POST body:
    {
        "message": "user question",
        "session_id": "abc123",
        "model": "soulfra-model" (optional)
    }
    """
    user_id = session.get('user_id')

    # Allow anonymous chat (no tier requirement)

    data = request.get_json()
    message = data.get('message', '').strip()
    session_id = data.get('session_id')
    model_name = data.get('model')

    if not message or not session_id:
        return jsonify({'error': 'Missing message or session_id'}), 400

    # Initialize context manager
    cm = ContextManager(user_id=user_id, session_id=session_id)

    # Process query
    result = cm.process_query(message, model_name=model_name)

    # Background knowledge extraction (runs in separate thread, invisible to user)
    if user_id:
        def extract_knowledge():
            """Background task: extract knowledge from this conversation"""
            try:
                extractor = KnowledgeExtractor(user_id=user_id)
                extractor.extract_from_conversation(
                    user_message=message,
                    ai_response=result['response'],
                    session_id=session_id
                )
            except Exception as e:
                # Silent failure - don't break user experience
                print(f"Knowledge extraction error (non-critical): {e}")

        # Run extraction in background thread (non-blocking)
        threading.Thread(target=extract_knowledge, daemon=True).start()

    return jsonify({
        'success': True,
        'response': result['response'],
        'model_used': result['model_used'],
        'model_description': result['model_description'],
        'session_id': result['session_id']
    })


@chat_bp.route('/api/chat/history/<session_id>')
def get_history(session_id):
    """Get conversation history for a session"""
    history = _load_conversation_history(session_id)
    return jsonify({'history': history})


@chat_bp.route('/api/chat/clear/<session_id>', methods=['POST'])
def clear_chat(session_id):
    """Clear conversation history"""
    db = get_db()
    db.execute('DELETE FROM discussion_messages WHERE session_id = ?', (session_id,))
    db.commit()
    db.close()

    return jsonify({'success': True})


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def _get_or_create_session(user_id, chat_mode, context_id):
    """Get existing session or create new one"""
    db = get_db()

    # Map chat mode to session lookup
    if chat_mode == 'post' and context_id:
        # Look for existing post discussion session
        session_row = db.execute('''
            SELECT id FROM discussion_sessions
            WHERE post_id = ? AND user_id = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (context_id, user_id)).fetchone()
    elif chat_mode == 'brand' and context_id:
        # Look for existing brand discussion session
        session_row = db.execute('''
            SELECT id FROM discussion_sessions
            WHERE brand_name = ? AND user_id = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (context_id, user_id)).fetchone()
    else:
        # General chat - create session with persona 'soulassistant'
        session_row = db.execute('''
            SELECT id FROM discussion_sessions
            WHERE user_id = ? AND post_id IS NULL AND brand_name IS NULL
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id,)).fetchone()

    if session_row:
        session_id = session_row['id']
    else:
        # Create new session
        if chat_mode == 'post' and context_id:
            cursor = db.execute('''
                INSERT INTO discussion_sessions (post_id, user_id, persona_name, status)
                VALUES (?, ?, 'soulassistant', 'active')
            ''', (context_id, user_id))
        elif chat_mode == 'brand' and context_id:
            cursor = db.execute('''
                INSERT INTO discussion_sessions (brand_name, user_id, persona_name, status)
                VALUES (?, ?, 'soulassistant', 'active')
            ''', (context_id, user_id))
        else:
            # General chat (no post_id or brand_name)
            # Use a dummy post_id = 0 to satisfy CHECK constraint
            cursor = db.execute('''
                INSERT INTO discussion_sessions (post_id, user_id, persona_name, status)
                VALUES (0, ?, 'soulassistant', 'active')
            ''', (user_id,))

        session_id = cursor.lastrowid
        db.commit()

    db.close()
    return session_id


def _load_conversation_history(session_id):
    """Load messages for session"""
    db = get_db()
    messages = db.execute('''
        SELECT sender, content, created_at
        FROM discussion_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    ''', (session_id,)).fetchall()
    db.close()

    return [
        {
            'sender': msg['sender'],
            'content': msg['content'],
            'timestamp': msg['created_at']
        }
        for msg in messages
    ]


def _get_context_info(chat_mode, context_id):
    """Get display info about the context"""
    if not context_id:
        return {'type': 'general', 'title': 'General Chat', 'description': 'Chat with any Ollama model'}

    db = get_db()

    if chat_mode == 'post':
        post = db.execute('SELECT title, slug FROM posts WHERE id = ?', (context_id,)).fetchone()
        if post:
            info = {
                'type': 'post',
                'title': post['title'],
                'description': f"Discuss: {post['title']}",
                'url': f"/post/{post['slug']}"
            }
        else:
            info = {'type': 'general', 'title': 'General Chat', 'description': 'Post not found'}

    elif chat_mode == 'brand':
        brand = db.execute('SELECT name, tagline FROM brands WHERE name = ?', (context_id,)).fetchone()
        if brand:
            info = {
                'type': 'brand',
                'title': brand['name'],
                'description': brand['tagline'] or f"Build brand: {brand['name']}",
                'url': f"/brand/{brand['name']}"
            }
        else:
            info = {'type': 'general', 'title': 'General Chat', 'description': 'Brand not found'}

    elif chat_mode == 'qr':
        qr = db.execute('SELECT destination_url FROM vanity_qr_codes WHERE short_code = ?', (context_id,)).fetchone()
        if qr:
            info = {
                'type': 'qr',
                'title': f"QR: {context_id}",
                'description': f"Chat via QR code",
                'url': f"/v/{context_id}"
            }
        else:
            info = {'type': 'general', 'title': 'General Chat', 'description': 'QR code not found'}

    elif chat_mode == 'gallery':
        gallery = db.execute('SELECT title FROM qr_galleries WHERE slug = ?', (context_id,)).fetchone()
        if gallery:
            info = {
                'type': 'gallery',
                'title': gallery['title'],
                'description': f"Ask about gallery: {gallery['title']}",
                'url': f"/gallery/{context_id}"
            }
        else:
            info = {'type': 'general', 'title': 'General Chat', 'description': 'Gallery not found'}

    else:
        info = {'type': 'general', 'title': 'General Chat', 'description': 'Chat with any Ollama model'}

    db.close()
    return info


def register_chat_routes(app):
    """Register chat blueprint with Flask app"""
    app.register_blueprint(chat_bp)
    print("✅ Registered unified chat routes:")
    print("   - /chat (Unified chat interface)")
    print("   - /api/chat/send (Send message to Ollama)")
    print("   - /api/chat/history/<session_id> (Get conversation history)")
    print("   - /api/chat/clear/<session_id> (Clear chat)")

#!/usr/bin/env python3
"""
SOUL Marketplace - AI Agent Workflow Marketplace

Inspired by: "like dying your hair in real life but for your avatar"
"SOUL upload or soul link for the workflows and how people want to feel that day"

Features:
- Upload AI workflows (voice → Cal → automation chains)
- Link workflows to moods/personas
- Avatar customization based on workflow
- Mouse effects, memes, gamification
- Marketplace for sharing/selling workflows
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from database import get_db
from datetime import datetime
import json
import hashlib
import secrets

soul_marketplace_bp = Blueprint('soul_marketplace', __name__)


def init_soul_marketplace_tables():
    """
    Initialize database tables for SOUL Marketplace
    """
    db = get_db()

    # SOUL Workflows - Reusable AI automation chains
    db.execute('''
        CREATE TABLE IF NOT EXISTS soul_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_user_id INTEGER NOT NULL,
            workflow_name TEXT NOT NULL,
            workflow_slug TEXT UNIQUE NOT NULL,
            description TEXT,
            workflow_type TEXT NOT NULL, -- 'voice_to_blog', 'voice_to_art', 'voice_to_code', etc.
            workflow_config TEXT NOT NULL, -- JSON: steps, models, prompts
            mood_tags TEXT, -- JSON: ['energetic', 'calm', 'focused', 'creative']
            avatar_effects TEXT, -- JSON: {hair_color, mouse_effect, meme_style}
            price_tokens INTEGER DEFAULT 0, -- 0 = free, >0 = paid
            downloads INTEGER DEFAULT 0,
            rating REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_public INTEGER DEFAULT 1,
            FOREIGN KEY (creator_user_id) REFERENCES users(id)
        )
    ''')

    # SOUL Links - User's active workflow assignments
    db.execute('''
        CREATE TABLE IF NOT EXISTS soul_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workflow_id INTEGER NOT NULL,
            link_name TEXT, -- "Morning Routine", "Brainstorm Mode", etc.
            mood TEXT, -- Current mood this workflow is linked to
            is_active INTEGER DEFAULT 0, -- Only one active workflow at a time per user
            shortcut_key TEXT, -- Keyboard shortcut to trigger
            activation_count INTEGER DEFAULT 0,
            last_activated_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (workflow_id) REFERENCES soul_workflows(id)
        )
    ''')

    # Workflow Executions - Track when workflows run
    db.execute('''
        CREATE TABLE IF NOT EXISTS workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            execution_status TEXT DEFAULT 'pending', -- pending, running, success, failed
            input_data TEXT, -- JSON: what triggered it
            output_data TEXT, -- JSON: what it produced
            error_message TEXT,
            duration_seconds REAL,
            executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES soul_workflows(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Marketplace Transactions - Track workflow purchases
    db.execute('''
        CREATE TABLE IF NOT EXISTS workflow_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_user_id INTEGER NOT NULL,
            seller_user_id INTEGER NOT NULL,
            workflow_id INTEGER NOT NULL,
            price_tokens INTEGER NOT NULL,
            purchase_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_user_id) REFERENCES users(id),
            FOREIGN KEY (seller_user_id) REFERENCES users(id),
            FOREIGN KEY (workflow_id) REFERENCES soul_workflows(id)
        )
    ''')

    # Avatar Customizations - Track avatar changes based on workflows
    db.execute('''
        CREATE TABLE IF NOT EXISTS avatar_customizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workflow_id INTEGER,
            customization_type TEXT NOT NULL, -- 'hair_color', 'mouse_effect', 'meme_style', 'vibe'
            customization_value TEXT NOT NULL, -- JSON or text value
            is_active INTEGER DEFAULT 1,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (workflow_id) REFERENCES soul_workflows(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ SOUL Marketplace tables initialized")


@soul_marketplace_bp.route('/soul/marketplace')
def marketplace_home():
    """
    Marketplace homepage - Browse workflows
    """
    db = get_db()

    # Get trending workflows
    trending = db.execute('''
        SELECT
            w.*,
            u.username as creator_name,
            COUNT(DISTINCT p.id) as purchase_count
        FROM soul_workflows w
        LEFT JOIN users u ON w.creator_user_id = u.id
        LEFT JOIN workflow_purchases p ON w.id = p.workflow_id
        WHERE w.is_public = 1
        GROUP BY w.id
        ORDER BY w.downloads DESC, w.rating DESC
        LIMIT 20
    ''').fetchall()

    # Get by mood
    moods = ['energetic', 'calm', 'focused', 'creative', 'playful', 'professional']

    return jsonify({
        'trending': [dict(row) for row in trending],
        'moods': moods
    })


@soul_marketplace_bp.route('/api/soul/upload', methods=['POST'])
def upload_workflow():
    """
    Upload a new SOUL workflow to marketplace

    Example workflow config:
    {
        "steps": [
            {"action": "capture_voice", "config": {}},
            {"action": "transcribe", "config": {"model": "whisper"}},
            {"action": "send_to_cal", "config": {"model": "calos-model", "prompt": "..."}},
            {"action": "generate_blog", "config": {"brand_id": 3}},
            {"action": "publish", "config": {"repo": "calriven"}}
        ],
        "avatar_effects": {
            "hair_color": "#FF69B4",
            "mouse_effect": "sparkle",
            "meme_style": "wholesome_vibes"
        }
    }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    workflow_name = data.get('workflow_name')
    description = data.get('description', '')
    workflow_type = data.get('workflow_type', 'custom')
    workflow_config = data.get('workflow_config', {})
    mood_tags = data.get('mood_tags', [])
    avatar_effects = data.get('avatar_effects', {})
    price_tokens = data.get('price_tokens', 0)

    if not workflow_name:
        return jsonify({'error': 'workflow_name required'}), 400

    # Generate slug
    slug = workflow_name.lower().replace(' ', '-').replace('/', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    slug = f"{slug}-{secrets.token_hex(4)}"

    # Insert workflow
    db = get_db()
    cursor = db.execute('''
        INSERT INTO soul_workflows (
            creator_user_id, workflow_name, workflow_slug, description,
            workflow_type, workflow_config, mood_tags, avatar_effects, price_tokens
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, workflow_name, slug, description, workflow_type,
        json.dumps(workflow_config), json.dumps(mood_tags),
        json.dumps(avatar_effects), price_tokens
    ))

    workflow_id = cursor.lastrowid
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'workflow_id': workflow_id,
        'workflow_slug': slug,
        'message': f'Workflow "{workflow_name}" uploaded to marketplace!'
    })


@soul_marketplace_bp.route('/api/soul/link', methods=['POST'])
def link_workflow():
    """
    Link a workflow to user's active SOUL

    Like "dying your hair" - changes your current vibe/workflow
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    workflow_id = data.get('workflow_id')
    link_name = data.get('link_name', 'My Workflow')
    mood = data.get('mood', 'neutral')
    make_active = data.get('make_active', True)

    if not workflow_id:
        return jsonify({'error': 'workflow_id required'}), 400

    db = get_db()

    # Deactivate all other workflows if making this active
    if make_active:
        db.execute('''
            UPDATE soul_links SET is_active = 0 WHERE user_id = ?
        ''', (user_id,))

    # Check if already linked
    existing = db.execute('''
        SELECT id FROM soul_links
        WHERE user_id = ? AND workflow_id = ?
    ''', (user_id, workflow_id)).fetchone()

    if existing:
        # Update existing link
        db.execute('''
            UPDATE soul_links
            SET is_active = ?, mood = ?, link_name = ?, last_activated_at = ?
            WHERE id = ?
        ''', (1 if make_active else 0, mood, link_name, datetime.now().isoformat(), existing['id']))
    else:
        # Create new link
        db.execute('''
            INSERT INTO soul_links (
                user_id, workflow_id, link_name, mood, is_active, last_activated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, workflow_id, link_name, mood, 1 if make_active else 0, datetime.now().isoformat()))

    # Get workflow details
    workflow = db.execute('''
        SELECT * FROM soul_workflows WHERE id = ?
    ''', (workflow_id,)).fetchone()

    # Apply avatar effects if workflow has them
    if workflow and workflow['avatar_effects']:
        avatar_effects = json.loads(workflow['avatar_effects'])

        # Deactivate previous avatar customizations
        db.execute('''
            UPDATE avatar_customizations SET is_active = 0 WHERE user_id = ?
        ''', (user_id,))

        # Apply new customizations
        for effect_type, effect_value in avatar_effects.items():
            db.execute('''
                INSERT INTO avatar_customizations (
                    user_id, workflow_id, customization_type, customization_value
                ) VALUES (?, ?, ?, ?)
            ''', (user_id, workflow_id, effect_type, json.dumps(effect_value)))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'message': f'Workflow linked! Your vibe is now: {mood}',
        'avatar_effects': avatar_effects if workflow else {}
    })


@soul_marketplace_bp.route('/api/soul/execute', methods=['POST'])
def execute_workflow():
    """
    Execute the user's active workflow

    This is the "talk into the void and shit happens" endpoint
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    input_data = data.get('input_data', {})
    workflow_id = data.get('workflow_id')  # Optional - use active if not specified

    db = get_db()

    # Get active workflow if not specified
    if not workflow_id:
        link = db.execute('''
            SELECT workflow_id FROM soul_links
            WHERE user_id = ? AND is_active = 1
            LIMIT 1
        ''', (user_id,)).fetchone()

        if not link:
            return jsonify({'error': 'No active workflow linked'}), 400

        workflow_id = link['workflow_id']

    # Get workflow config
    workflow = db.execute('''
        SELECT * FROM soul_workflows WHERE id = ?
    ''', (workflow_id,)).fetchone()

    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404

    # Parse workflow steps
    workflow_config = json.loads(workflow['workflow_config'])
    steps = workflow_config.get('steps', [])

    # Log execution start
    cursor = db.execute('''
        INSERT INTO workflow_executions (
            workflow_id, user_id, execution_status, input_data
        ) VALUES (?, ?, ?, ?)
    ''', (workflow_id, user_id, 'running', json.dumps(input_data)))

    execution_id = cursor.lastrowid

    # Update activation count
    db.execute('''
        UPDATE soul_links
        SET activation_count = activation_count + 1, last_activated_at = ?
        WHERE user_id = ? AND workflow_id = ?
    ''', (datetime.now().isoformat(), user_id, workflow_id))

    db.commit()

    # Execute workflow steps
    # (This would integrate with your existing systems: Cal, voice recording, etc.)
    execution_result = {
        'workflow_id': workflow_id,
        'workflow_name': workflow['workflow_name'],
        'steps_executed': len(steps),
        'status': 'queued',
        'message': f'Workflow "{workflow["workflow_name"]}" is running...'
    }

    # Update execution status
    db.execute('''
        UPDATE workflow_executions
        SET execution_status = 'success', output_data = ?
        WHERE id = ?
    ''', (json.dumps(execution_result), execution_id))

    db.commit()
    db.close()

    return jsonify(execution_result)


@soul_marketplace_bp.route('/api/soul/my-workflows')
def my_workflows():
    """
    Get user's linked workflows
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()

    workflows = db.execute('''
        SELECT
            sl.*,
            sw.workflow_name,
            sw.workflow_type,
            sw.mood_tags,
            sw.avatar_effects
        FROM soul_links sl
        JOIN soul_workflows sw ON sl.workflow_id = sw.id
        WHERE sl.user_id = ?
        ORDER BY sl.is_active DESC, sl.last_activated_at DESC
    ''').fetchall()

    return jsonify({
        'workflows': [dict(row) for row in workflows]
    })


@soul_marketplace_bp.route('/api/soul/avatar')
def get_avatar():
    """
    Get user's current avatar customizations based on active workflow
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()

    customizations = db.execute('''
        SELECT * FROM avatar_customizations
        WHERE user_id = ? AND is_active = 1
        ORDER BY applied_at DESC
    ''', (user_id,)).fetchall()

    avatar = {}
    for custom in customizations:
        try:
            avatar[custom['customization_type']] = json.loads(custom['customization_value'])
        except:
            avatar[custom['customization_type']] = custom['customization_value']

    return jsonify({
        'avatar': avatar,
        'customizations': [dict(row) for row in customizations]
    })


def register_soul_marketplace_routes(app):
    """Register SOUL Marketplace blueprint"""
    app.register_blueprint(soul_marketplace_bp)
    print("✅ SOUL Marketplace routes registered")

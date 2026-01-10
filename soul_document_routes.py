"""
Soul Document Routes - Community-votable AI personality system
Inspired by Claude's soul document + Airbnb reviews + Wikipedia governance
"""
from flask import Blueprint, request, jsonify, render_template_string, send_from_directory
import os
import json
import hashlib
from datetime import datetime
from database import get_db

soul_bp = Blueprint('soul', __name__)

# Initialize database tables
def init_soul_tables():
    """Create tables for soul document versioning and vibe ratings"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS soul_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by_user_id INTEGER,
            is_active BOOLEAN DEFAULT 0,
            total_votes INTEGER DEFAULT 0,
            avg_vibe_score REAL DEFAULT 0.0,
            change_summary TEXT
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS vibe_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_response_text TEXT NOT NULL,
            user_prompt TEXT NOT NULL,
            vibe_score INTEGER NOT NULL,  -- 1-5 (terrible to fire)
            vibe_emoji TEXT,  -- "fire", "good", "mid", "cringe", "terrible"
            soul_document_version TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            FOREIGN KEY (soul_document_version) REFERENCES soul_documents(version)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS soul_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soul_document_version TEXT NOT NULL,
            user_id INTEGER,
            vote INTEGER NOT NULL,  -- 1 = upvote, -1 = downvote
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (soul_document_version) REFERENCES soul_documents(version)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS cringe_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vibe_rating_id INTEGER NOT NULL,
            flag_reason TEXT,  -- "corporate_speak", "fake_empathy", etc.
            flagged_by_user_id INTEGER,
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            FOREIGN KEY (vibe_rating_id) REFERENCES vibe_ratings(id)
        )
    ''')

    db.commit()

    # Load initial soul document from file
    soul_doc_path = 'SOULFRA_SOUL.md'
    if os.path.exists(soul_doc_path):
        with open(soul_doc_path, 'r') as f:
            content = f.read()

        # Check if version 1.0 already exists
        existing = db.execute(
            'SELECT id FROM soul_documents WHERE version = ?',
            ('1.0',)
        ).fetchone()

        if not existing:
            db.execute('''
                INSERT INTO soul_documents (
                    version, content, is_active, change_summary
                ) VALUES (?, ?, ?, ?)
            ''', ('1.0', content, 1, 'Initial soul document'))
            db.commit()

    print("✅ Soul document tables initialized")

init_soul_tables()

@soul_bp.route('/api/soul/current')
def get_current_soul():
    """
    Get the currently active soul document

    GET /api/soul/current
    Returns: soul document content + metadata
    """
    db = get_db()

    soul = db.execute('''
        SELECT * FROM soul_documents
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
    ''').fetchone()

    if not soul:
        return jsonify({'error': 'No active soul document'}), 404

    return jsonify({
        'success': True,
        'version': soul['version'],
        'content': soul['content'],
        'created_at': soul['created_at'],
        'total_votes': soul['total_votes'],
        'avg_vibe_score': soul['avg_vibe_score']
    })

@soul_bp.route('/api/soul/versions')
def list_soul_versions():
    """
    List all soul document versions

    GET /api/soul/versions
    Returns: array of all versions with stats
    """
    db = get_db()

    versions = db.execute('''
        SELECT
            version,
            created_at,
            is_active,
            total_votes,
            avg_vibe_score,
            change_summary
        FROM soul_documents
        ORDER BY created_at DESC
    ''').fetchall()

    return jsonify({
        'success': True,
        'versions': [dict(v) for v in versions]
    })

@soul_bp.route('/api/soul/vote', methods=['POST'])
def rate_ai_vibe():
    """
    Rate the vibe of an AI response

    POST /api/soul/vote
    Body: {
        "ai_response": "...",
        "user_prompt": "...",
        "vibe_score": 1-5,
        "vibe_emoji": "fire|good|mid|cringe|terrible",
        "session_id": "..."
    }
    """
    data = request.json

    ai_response = data.get('ai_response')
    user_prompt = data.get('user_prompt')
    vibe_score = data.get('vibe_score')
    vibe_emoji = data.get('vibe_emoji')
    session_id = data.get('session_id')

    if not all([ai_response, user_prompt, vibe_score]):
        return jsonify({'error': 'Missing required fields'}), 400

    if vibe_score not in [1, 2, 3, 4, 5]:
        return jsonify({'error': 'vibe_score must be 1-5'}), 400

    db = get_db()

    # Get current soul document version
    soul = db.execute(
        'SELECT version FROM soul_documents WHERE is_active = 1 LIMIT 1'
    ).fetchone()

    if not soul:
        return jsonify({'error': 'No active soul document'}), 500

    # Store vibe rating
    db.execute('''
        INSERT INTO vibe_ratings (
            ai_response_text, user_prompt, vibe_score, vibe_emoji,
            soul_document_version, session_id
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        ai_response, user_prompt, vibe_score, vibe_emoji,
        soul['version'], session_id
    ))
    db.commit()

    rating_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Update soul document avg vibe score
    avg_score = db.execute('''
        SELECT AVG(vibe_score) as avg
        FROM vibe_ratings
        WHERE soul_document_version = ?
    ''', (soul['version'],)).fetchone()['avg']

    db.execute('''
        UPDATE soul_documents
        SET avg_vibe_score = ?
        WHERE version = ?
    ''', (avg_score, soul['version']))
    db.commit()

    # Check if response should be flagged as cringe
    if vibe_emoji in ['cringe', 'terrible']:
        # Count recent cringe ratings for this soul version
        cringe_count = db.execute('''
            SELECT COUNT(*) as count
            FROM vibe_ratings
            WHERE soul_document_version = ?
            AND vibe_emoji IN ('cringe', 'terrible')
            AND created_at > datetime('now', '-1 hour')
        ''', (soul['version'],)).fetchone()['count']

        # If 3+ cringe ratings in last hour, flag for review
        if cringe_count >= 3:
            db.execute('''
                INSERT INTO cringe_flags (
                    vibe_rating_id, flag_reason
                ) VALUES (?, ?)
            ''', (rating_id, 'high_cringe_rate'))
            db.commit()

            return jsonify({
                'success': True,
                'rating_id': rating_id,
                'cringe_alert': True,
                'message': 'Response flagged for cringe. Soul document may need update.'
            })

    return jsonify({
        'success': True,
        'rating_id': rating_id,
        'avg_vibe_score': round(avg_score, 2)
    })

@soul_bp.route('/api/soul/update', methods=['POST'])
def propose_soul_update():
    """
    Propose an update to the soul document

    POST /api/soul/update
    Body: {
        "content": "...",  # New soul document content
        "change_summary": "..."  # Summary of changes
    }
    """
    data = request.json

    content = data.get('content')
    change_summary = data.get('change_summary')

    if not all([content, change_summary]):
        return jsonify({'error': 'Missing content or change_summary'}), 400

    db = get_db()

    # Get current version
    current = db.execute(
        'SELECT version FROM soul_documents WHERE is_active = 1 LIMIT 1'
    ).fetchone()

    if not current:
        new_version = '1.0'
    else:
        # Increment version
        major, minor = map(int, current['version'].split('.'))
        new_version = f'{major}.{minor + 1}'

    # Create new version (not active yet - requires voting)
    db.execute('''
        INSERT INTO soul_documents (
            version, content, is_active, change_summary
        ) VALUES (?, ?, 0, ?)
    ''', (new_version, content, change_summary))
    db.commit()

    return jsonify({
        'success': True,
        'new_version': new_version,
        'message': 'Soul document update proposed. Community voting required to activate.'
    })

@soul_bp.route('/api/soul/vote-version', methods=['POST'])
def vote_on_soul_version():
    """
    Vote on a proposed soul document version

    POST /api/soul/vote-version
    Body: {
        "version": "1.1",
        "vote": 1 or -1  # upvote or downvote
    }
    """
    data = request.json

    version = data.get('version')
    vote = data.get('vote')

    if not all([version, vote]):
        return jsonify({'error': 'Missing version or vote'}), 400

    if vote not in [1, -1]:
        return jsonify({'error': 'vote must be 1 or -1'}), 400

    db = get_db()

    # Record vote
    db.execute('''
        INSERT INTO soul_votes (soul_document_version, vote)
        VALUES (?, ?)
    ''', (version, vote))
    db.commit()

    # Count total votes for this version
    vote_count = db.execute('''
        SELECT SUM(vote) as total
        FROM soul_votes
        WHERE soul_document_version = ?
    ''', (version,)).fetchone()['total']

    # Update vote count
    db.execute('''
        UPDATE soul_documents
        SET total_votes = ?
        WHERE version = ?
    ''', (vote_count, version))
    db.commit()

    # If 100+ votes and positive score, activate
    if vote_count >= 100:
        # Deactivate old version
        db.execute('UPDATE soul_documents SET is_active = 0')

        # Activate new version
        db.execute('''
            UPDATE soul_documents
            SET is_active = 1
            WHERE version = ?
        ''', (version,))
        db.commit()

        return jsonify({
            'success': True,
            'activated': True,
            'message': f'Soul document v{version} activated!'
        })

    return jsonify({
        'success': True,
        'total_votes': vote_count,
        'votes_needed': max(0, 100 - vote_count)
    })

@soul_bp.route('/api/soul/leaderboard')
def soul_leaderboard():
    """
    Get top-rated soul document versions

    GET /api/soul/leaderboard
    Returns: versions ranked by avg vibe score
    """
    db = get_db()

    versions = db.execute('''
        SELECT
            version,
            avg_vibe_score,
            total_votes,
            is_active,
            created_at
        FROM soul_documents
        ORDER BY avg_vibe_score DESC, total_votes DESC
        LIMIT 10
    ''').fetchall()

    return jsonify({
        'success': True,
        'leaderboard': [dict(v) for v in versions]
    })

@soul_bp.route('/api/soul/stats')
def soul_stats():
    """
    Get overall soul document statistics

    GET /api/soul/stats
    Returns: aggregate stats
    """
    db = get_db()

    total_ratings = db.execute('SELECT COUNT(*) as count FROM vibe_ratings').fetchone()['count']

    vibe_distribution = db.execute('''
        SELECT vibe_emoji, COUNT(*) as count
        FROM vibe_ratings
        GROUP BY vibe_emoji
    ''').fetchall()

    cringe_flags = db.execute('''
        SELECT COUNT(*) as count
        FROM cringe_flags
        WHERE resolved = 0
    ''').fetchone()['count']

    current_soul = db.execute('''
        SELECT version, avg_vibe_score, total_votes
        FROM soul_documents
        WHERE is_active = 1
        LIMIT 1
    ''').fetchone()

    return jsonify({
        'success': True,
        'total_ratings': total_ratings,
        'vibe_distribution': {v['vibe_emoji']: v['count'] for v in vibe_distribution},
        'pending_cringe_flags': cringe_flags,
        'current_version': dict(current_soul) if current_soul else None
    })

@soul_bp.route('/soul')
def soul_dashboard():
    """Serve soul document dashboard"""
    return send_from_directory('voice-archive', 'soul-dashboard.html')

def load_soul_document_for_ollama():
    """
    Load current soul document to use in Ollama system prompt

    Returns: string of soul document content
    """
    db = get_db()

    soul = db.execute('''
        SELECT content FROM soul_documents
        WHERE is_active = 1
        LIMIT 1
    ''').fetchone()

    if not soul:
        return ""

    return soul['content']

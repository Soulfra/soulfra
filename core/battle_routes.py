#!/usr/bin/env python3
"""
AI Battle Arena - Competitive AI Content Generation

Roommates submit prompts → Multiple AI models compete → Users vote for winner

Features:
- AI vs AI battles (2-4 models compete simultaneously)
- User voting system (upvote/downvote responses)
- Leaderboard tracking (which AI wins most often)
- Topic categories (code, creative writing, explanations, debates)
- Real-time results

Routes:
- GET /battle - Main battle arena interface
- POST /api/battle/create - Create new battle with prompt
- POST /api/battle/vote - Vote for AI response
- GET /api/battle/results/<battle_id> - Get battle results
- GET /battle/leaderboard - AI leaderboard page

Database Tables:
- battle_sessions: Individual battles
- battle_responses: AI-generated responses
- battle_votes: User votes
- battle_stats: AI win/loss tracking
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import get_db
from context_manager import ContextManager
from unified_logger import log_integration_event
import json
from datetime import datetime
import threading

battle_bp = Blueprint('battle', __name__)


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_battle_tables():
    """Initialize battle arena database tables"""
    db = get_db()

    # Battle sessions table
    db.execute('''
        CREATE TABLE IF NOT EXISTS battle_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            creator_user_id INTEGER,
            models TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')

    # Battle responses table (AI-generated content)
    db.execute('''
        CREATE TABLE IF NOT EXISTS battle_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            response_text TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (battle_id) REFERENCES battle_sessions(id)
        )
    ''')

    # Battle votes table
    db.execute('''
        CREATE TABLE IF NOT EXISTS battle_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id INTEGER NOT NULL,
            response_id INTEGER NOT NULL,
            voter_user_id INTEGER,
            vote_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (battle_id) REFERENCES battle_sessions(id),
            FOREIGN KEY (response_id) REFERENCES battle_responses(id),
            UNIQUE(battle_id, voter_user_id, response_id)
        )
    ''')

    # Battle stats table (AI leaderboard)
    db.execute('''
        CREATE TABLE IF NOT EXISTS battle_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT UNIQUE NOT NULL,
            total_battles INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            total_votes INTEGER DEFAULT 0,
            avg_votes_per_battle REAL DEFAULT 0.0,
            last_battle_at TIMESTAMP
        )
    ''')

    # Indexes
    db.execute('CREATE INDEX IF NOT EXISTS idx_battle_sessions_status ON battle_sessions(status)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_battle_responses_battle ON battle_responses(battle_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_battle_votes_battle ON battle_votes(battle_id)')

    db.commit()
    db.close()

    print("✅ Battle arena tables initialized")


# =============================================================================
# MAIN ROUTES
# =============================================================================

@battle_bp.route('/battle')
def battle_arena():
    """
    Main battle arena interface

    Users can:
    - View active battles
    - Create new battles
    - Vote on AI responses
    - See leaderboard
    """
    # Check QR authentication
    search_token = session.get('search_token')

    if not search_token:
        return redirect(url_for('login_qr') + '?redirect=/battle')

    # Validate session
    db = get_db()
    session_data = db.execute('''
        SELECT * FROM search_sessions
        WHERE session_token = ?
        AND expires_at > datetime('now')
    ''', (search_token,)).fetchone()

    if not session_data:
        db.close()
        session.pop('search_token', None)
        return redirect(url_for('login_qr') + '?redirect=/battle')

    # Get or create user_id
    user_id = session.get('user_id')

    if not user_id:
        import secrets

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (f'battle_user_{secrets.token_hex(4)}', f'battle_{secrets.token_hex(4)}@temp.com', 'qr-authenticated'))

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        db.commit()

    # Get active battles
    active_battles = db.execute('''
        SELECT id, prompt, category, models, created_at
        FROM battle_sessions
        WHERE status = 'active'
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()

    # Get available AI models
    cm = ContextManager(user_id=user_id)
    available_models = cm.get_available_models()

    db.close()

    return render_template('battle.html',
        user_id=user_id,
        active_battles=[dict(b) for b in active_battles],
        available_models=available_models,
        battle_categories=['general', 'code', 'creative', 'explanation', 'debate', 'horoscope']
    )


@battle_bp.route('/api/battle/create', methods=['POST'])
def create_battle():
    """
    Create new AI battle

    POST body:
    {
        "prompt": "Write a haiku about encryption",
        "category": "creative",
        "models": ["soulfra-model", "deathtodata-model", "drseuss-model"]
    }

    Returns:
    {
        "success": true,
        "battle_id": 42,
        "status": "generating",
        "models": ["soulfra-model", "deathtodata-model", "drseuss-model"]
    }
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    category = data.get('category', 'general')
    models = data.get('models', [])

    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400

    if len(models) < 2:
        return jsonify({'error': 'At least 2 models required for battle'}), 400

    if len(models) > 4:
        return jsonify({'error': 'Maximum 4 models per battle'}), 400

    # Create battle session
    db = get_db()

    cursor = db.execute('''
        INSERT INTO battle_sessions (prompt, category, creator_user_id, models, status)
        VALUES (?, ?, ?, ?, 'generating')
    ''', (prompt, category, user_id, json.dumps(models)))

    battle_id = cursor.lastrowid
    db.commit()
    db.close()

    # Generate responses from all models in background
    def generate_responses():
        """Background task: Generate AI responses"""
        cm = ContextManager(user_id=user_id)
        db = get_db()

        for model_name in models:
            try:
                # Generate response from this AI model
                result = cm.process_query(prompt, model_name=model_name)

                # Store response
                db.execute('''
                    INSERT INTO battle_responses (battle_id, model_name, response_text)
                    VALUES (?, ?, ?)
                ''', (battle_id, model_name, result['response']))

                db.commit()

                # Update battle stats
                _update_battle_stats(model_name, battles_delta=1)

            except Exception as e:
                print(f"Error generating response from {model_name}: {e}")

        # Mark battle as active
        db.execute('''
            UPDATE battle_sessions SET status = 'active' WHERE id = ?
        ''', (battle_id,))
        db.commit()
        db.close()

        # Log event
        log_integration_event(
            platform='battle',
            event_type='battle_created',
            description=f'Battle #{battle_id}: {len(models)} AI models competing',
            metadata={'battle_id': battle_id, 'prompt': prompt, 'models': models},
            user_id=user_id
        )

    # Start background generation
    threading.Thread(target=generate_responses, daemon=True).start()

    return jsonify({
        'success': True,
        'battle_id': battle_id,
        'status': 'generating',
        'models': models,
        'message': 'Battle started! AI models are generating responses...'
    })


@battle_bp.route('/api/battle/vote', methods=['POST'])
def vote_on_response():
    """
    Vote for AI response

    POST body:
    {
        "battle_id": 42,
        "response_id": 123,
        "vote_type": "upvote"
    }

    Returns:
    {
        "success": true,
        "new_vote_count": 7
    }
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    battle_id = data.get('battle_id')
    response_id = data.get('response_id')
    vote_type = data.get('vote_type', 'upvote')

    if not all([battle_id, response_id]):
        return jsonify({'error': 'Missing battle_id or response_id'}), 400

    if vote_type not in ['upvote', 'downvote']:
        return jsonify({'error': 'Invalid vote_type'}), 400

    db = get_db()

    # Check if user already voted on this response
    existing_vote = db.execute('''
        SELECT id, vote_type FROM battle_votes
        WHERE battle_id = ? AND voter_user_id = ? AND response_id = ?
    ''', (battle_id, user_id, response_id)).fetchone()

    if existing_vote:
        # Update existing vote
        db.execute('''
            UPDATE battle_votes
            SET vote_type = ?, created_at = ?
            WHERE id = ?
        ''', (vote_type, datetime.now().isoformat(), existing_vote['id']))
    else:
        # Insert new vote
        db.execute('''
            INSERT INTO battle_votes (battle_id, response_id, voter_user_id, vote_type)
            VALUES (?, ?, ?, ?)
        ''', (battle_id, response_id, user_id, vote_type))

    db.commit()

    # Get updated vote count
    vote_count = db.execute('''
        SELECT
            COUNT(CASE WHEN vote_type = 'upvote' THEN 1 END) as upvotes,
            COUNT(CASE WHEN vote_type = 'downvote' THEN 1 END) as downvotes
        FROM battle_votes
        WHERE response_id = ?
    ''', (response_id,)).fetchone()

    # Update stats for this model
    model_name = db.execute('SELECT model_name FROM battle_responses WHERE id = ?', (response_id,)).fetchone()['model_name']
    _update_battle_stats(model_name, votes_delta=1)

    db.close()

    return jsonify({
        'success': True,
        'upvotes': vote_count['upvotes'],
        'downvotes': vote_count['downvotes'],
        'net_votes': vote_count['upvotes'] - vote_count['downvotes']
    })


@battle_bp.route('/api/battle/results/<int:battle_id>')
def get_battle_results(battle_id):
    """
    Get battle results with all AI responses and votes

    Returns:
    {
        "battle": {...},
        "responses": [
            {
                "model_name": "soulfra-model",
                "response_text": "...",
                "upvotes": 5,
                "downvotes": 1,
                "rank": 1
            },
            ...
        ]
    }
    """
    db = get_db()

    # Get battle info
    battle = db.execute('''
        SELECT id, prompt, category, models, status, created_at
        FROM battle_sessions
        WHERE id = ?
    ''', (battle_id,)).fetchone()

    if not battle:
        db.close()
        return jsonify({'error': 'Battle not found'}), 404

    # Get all responses with vote counts
    responses = db.execute('''
        SELECT
            br.id,
            br.model_name,
            br.response_text,
            br.generated_at,
            COUNT(CASE WHEN bv.vote_type = 'upvote' THEN 1 END) as upvotes,
            COUNT(CASE WHEN bv.vote_type = 'downvote' THEN 1 END) as downvotes
        FROM battle_responses br
        LEFT JOIN battle_votes bv ON br.id = bv.response_id
        WHERE br.battle_id = ?
        GROUP BY br.id
        ORDER BY (COUNT(CASE WHEN bv.vote_type = 'upvote' THEN 1 END) -
                  COUNT(CASE WHEN bv.vote_type = 'downvote' THEN 1 END)) DESC
    ''', (battle_id,)).fetchall()

    db.close()

    # Format responses
    responses_list = []
    for idx, resp in enumerate(responses):
        responses_list.append({
            'id': resp['id'],
            'model_name': resp['model_name'],
            'response_text': resp['response_text'],
            'generated_at': resp['generated_at'],
            'upvotes': resp['upvotes'],
            'downvotes': resp['downvotes'],
            'net_votes': resp['upvotes'] - resp['downvotes'],
            'rank': idx + 1
        })

    return jsonify({
        'battle': dict(battle),
        'responses': responses_list,
        'winner': responses_list[0] if responses_list else None
    })


@battle_bp.route('/battle/leaderboard')
def leaderboard():
    """AI leaderboard page showing win/loss records"""
    db = get_db()

    # Get leaderboard stats
    stats = db.execute('''
        SELECT
            model_name,
            total_battles,
            wins,
            losses,
            total_votes,
            avg_votes_per_battle,
            last_battle_at,
            CASE
                WHEN total_battles > 0 THEN CAST(wins AS REAL) / total_battles * 100
                ELSE 0
            END as win_rate
        FROM battle_stats
        ORDER BY wins DESC, win_rate DESC
        LIMIT 20
    ''').fetchall()

    db.close()

    return render_template('battle_leaderboard.html',
        stats=[dict(s) for s in stats]
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _update_battle_stats(model_name, battles_delta=0, wins_delta=0, losses_delta=0, votes_delta=0):
    """Update battle stats for a model"""
    db = get_db()

    # Check if model exists in stats
    existing = db.execute('SELECT id FROM battle_stats WHERE model_name = ?', (model_name,)).fetchone()

    if not existing:
        # Create new stats entry
        db.execute('''
            INSERT INTO battle_stats (model_name, total_battles, wins, losses, total_votes, last_battle_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (model_name, battles_delta, wins_delta, losses_delta, votes_delta, datetime.now().isoformat()))
    else:
        # Update existing stats
        db.execute('''
            UPDATE battle_stats
            SET total_battles = total_battles + ?,
                wins = wins + ?,
                losses = losses + ?,
                total_votes = total_votes + ?,
                last_battle_at = ?
            WHERE model_name = ?
        ''', (battles_delta, wins_delta, losses_delta, votes_delta, datetime.now().isoformat(), model_name))

    # Recalculate average votes per battle
    db.execute('''
        UPDATE battle_stats
        SET avg_votes_per_battle = CAST(total_votes AS REAL) / total_battles
        WHERE model_name = ? AND total_battles > 0
    ''', (model_name,))

    db.commit()
    db.close()


def calculate_battle_winners():
    """
    Calculate winners for completed battles

    Runs periodically to determine which AI won each battle
    and update stats
    """
    db = get_db()

    # Get active battles with responses
    battles = db.execute('''
        SELECT DISTINCT bs.id
        FROM battle_sessions bs
        JOIN battle_responses br ON bs.id = br.battle_id
        WHERE bs.status = 'active'
    ''').fetchall()

    for battle in battles:
        battle_id = battle['id']

        # Get responses ranked by votes
        responses = db.execute('''
            SELECT
                br.model_name,
                COUNT(CASE WHEN bv.vote_type = 'upvote' THEN 1 END) -
                COUNT(CASE WHEN bv.vote_type = 'downvote' THEN 1 END) as net_votes
            FROM battle_responses br
            LEFT JOIN battle_votes bv ON br.id = bv.response_id
            WHERE br.battle_id = ?
            GROUP BY br.model_name
            ORDER BY net_votes DESC
        ''', (battle_id,)).fetchall()

        if not responses:
            continue

        # Winner is model with most net votes
        winner = responses[0]['model_name']

        # Update stats
        for idx, resp in enumerate(responses):
            if idx == 0:
                # Winner
                _update_battle_stats(resp['model_name'], wins_delta=1)
            else:
                # Loser
                _update_battle_stats(resp['model_name'], losses_delta=1)

    db.close()


# =============================================================================
# REGISTRATION
# =============================================================================

def register_battle_routes(app):
    """Register battle blueprint with Flask app"""
    # Initialize tables
    init_battle_tables()

    # Register blueprint
    app.register_blueprint(battle_bp)

    print("✅ Registered AI Battle Arena routes:")
    print("   - /battle (Main battle arena)")
    print("   - /api/battle/create (Create new battle)")
    print("   - /api/battle/vote (Vote for AI response)")
    print("   - /api/battle/results/<id> (Get battle results)")
    print("   - /battle/leaderboard (AI leaderboard)")

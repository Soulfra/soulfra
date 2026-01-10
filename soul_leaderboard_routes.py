"""
Soul Leaderboard Routes - Reddit-style ranking for AI personalities

Like Product Hunt daily rankings but for AI souls.
Community votes on which AI personalities are fire vs cringe.
"""
from flask import Blueprint, request, jsonify, send_from_directory
import math
from datetime import datetime, timedelta
from database import get_db

soul_leaderboard_bp = Blueprint('soul_leaderboard', __name__)

# Initialize AI agents table
def init_ai_agents_table():
    """Create table for AI agent registry + voting"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS ai_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT UNIQUE NOT NULL,
            soul_document_version TEXT,
            profile_slug TEXT,
            description TEXT,
            votes_up INTEGER DEFAULT 0,
            votes_down INTEGER DEFAULT 0,
            avg_vibe_score REAL DEFAULT 0.0,
            hot_score REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_vote_at TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS agent_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            user_id INTEGER,
            vote INTEGER NOT NULL,  -- 1 or -1
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            FOREIGN KEY (agent_name) REFERENCES ai_agents(agent_name)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS agent_cheers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            user_id INTEGER,
            cheer_message TEXT,
            cheered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_name) REFERENCES ai_agents(agent_name)
        )
    ''')

    db.commit()

    # Pre-populate with Soulfra AI agents (real domains only)
    agents = [
        {
            'name': 'soulfra',
            'soul_version': '1.0',
            'slug': 'soulfra',
            'description': 'Community-voted AI personality. No corporate speak, no fake empathy.',
            'website': 'https://soulfra.com'
        },
        {
            'name': 'cringeproof',
            'soul_version': '1.0',
            'slug': 'cringeproof',
            'description': 'Voice idea capture with brutal honesty. No BS allowed.',
            'website': 'https://cringeproof.com'
        },
        {
            'name': 'calriven',
            'soul_version': '1.0',
            'slug': 'calriven',
            'description': 'Real estate intelligence. Market analysis without hype.',
            'website': 'https://calriven.com'
        },
        {
            'name': 'deathtodata',
            'soul_version': '1.0',
            'slug': 'deathtodata',
            'description': 'Privacy guardian. Exposes tracking, surveillance, data harvesting.',
            'website': 'https://deathtodata.com'
        },
        {
            'name': 'stpetepros',
            'soul_version': '1.0',
            'slug': 'stpetepros',
            'description': 'Tampa Bay professional network. Real skills, real people.',
            'website': 'https://stpetepros.com'
        }
    ]

    for agent in agents:
        existing = db.execute(
            'SELECT id FROM ai_agents WHERE agent_name = ?',
            (agent['name'],)
        ).fetchone()

        if not existing:
            db.execute('''
                INSERT INTO ai_agents (
                    agent_name, soul_document_version, profile_slug, description
                ) VALUES (?, ?, ?, ?)
            ''', (
                agent['name'],
                agent['soul_version'],
                agent['slug'],
                agent['description']
            ))
            db.commit()

    print("✅ AI agents table initialized with 5 real domain agents")

init_ai_agents_table()

def calculate_hot_score(votes_up, votes_down, timestamp):
    """
    Reddit hot score algorithm

    Balances popularity (net votes) with recency (time decay)
    """
    net_votes = votes_up - votes_down
    hours_old = (datetime.now() - timestamp).total_seconds() / 3600

    # Prevent log(0)
    order = math.log(max(abs(net_votes), 1), 10)
    sign = 1 if net_votes > 0 else -1 if net_votes < 0 else 0
    seconds_old = hours_old * 3600

    # Reddit formula: sign * log(votes) + time_decay
    return sign * order + seconds_old / 45000

@soul_leaderboard_bp.route('/api/soul/agents')
def list_agents():
    """
    Get all AI agents

    GET /api/soul/agents
    Returns: list of agents with stats
    """
    db = get_db()

    agents = db.execute('''
        SELECT
            agent_name,
            soul_document_version,
            profile_slug,
            description,
            votes_up,
            votes_down,
            votes_up - votes_down as net_votes,
            avg_vibe_score,
            hot_score,
            created_at
        FROM ai_agents
        ORDER BY hot_score DESC
    ''').fetchall()

    return jsonify({
        'success': True,
        'agents': [dict(a) for a in agents]
    })

@soul_leaderboard_bp.route('/api/soul/vote-agent', methods=['POST'])
def vote_on_agent():
    """
    Vote on AI agent

    POST /api/soul/vote-agent
    Body: {
        "agent_name": "soulfra",
        "vote": 1 or -1
    }
    """
    data = request.json

    agent_name = data.get('agent_name')
    vote = data.get('vote')
    session_id = data.get('session_id')

    if not all([agent_name, vote]):
        return jsonify({'error': 'agent_name and vote required'}), 400

    if vote not in [1, -1]:
        return jsonify({'error': 'vote must be 1 or -1'}), 400

    db = get_db()

    # Check agent exists
    agent = db.execute(
        'SELECT * FROM ai_agents WHERE agent_name = ?',
        (agent_name,)
    ).fetchone()

    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    # Record vote
    db.execute('''
        INSERT INTO agent_votes (agent_name, vote, session_id)
        VALUES (?, ?, ?)
    ''', (agent_name, vote, session_id))
    db.commit()

    # Update agent vote counts
    if vote == 1:
        db.execute('''
            UPDATE ai_agents
            SET votes_up = votes_up + 1, last_vote_at = ?
            WHERE agent_name = ?
        ''', (datetime.now(), agent_name))
    else:
        db.execute('''
            UPDATE ai_agents
            SET votes_down = votes_down + 1, last_vote_at = ?
            WHERE agent_name = ?
        ''', (datetime.now(), agent_name))
    db.commit()

    # Recalculate hot score
    updated_agent = db.execute(
        'SELECT votes_up, votes_down, created_at FROM ai_agents WHERE agent_name = ?',
        (agent_name,)
    ).fetchone()

    new_hot_score = calculate_hot_score(
        updated_agent['votes_up'],
        updated_agent['votes_down'],
        datetime.fromisoformat(updated_agent['created_at'])
    )

    db.execute('''
        UPDATE ai_agents SET hot_score = ? WHERE agent_name = ?
    ''', (new_hot_score, agent_name))
    db.commit()

    return jsonify({
        'success': True,
        'agent_name': agent_name,
        'vote': vote,
        'new_hot_score': round(new_hot_score, 2)
    })

@soul_leaderboard_bp.route('/api/soul/leaderboard-rotating')
def rotating_leaderboard():
    """
    Get rotating soul leaderboard (top 10)

    GET /api/soul/leaderboard-rotating
    Returns: top souls ranked by hot score
    """
    db = get_db()

    # Top 10 by hot score
    leaderboard = db.execute('''
        SELECT
            agent_name,
            description,
            votes_up - votes_down as net_votes,
            avg_vibe_score,
            hot_score,
            soul_document_version
        FROM ai_agents
        ORDER BY hot_score DESC
        LIMIT 10
    ''').fetchall()

    # Add ranks
    ranked = []
    for i, agent in enumerate(leaderboard):
        entry = dict(agent)
        entry['rank'] = i + 1

        # Medal emojis
        if i == 0:
            entry['medal'] = '🥇'
        elif i == 1:
            entry['medal'] = '🥈'
        elif i == 2:
            entry['medal'] = '🥉'
        else:
            entry['medal'] = ''

        ranked.append(entry)

    return jsonify({
        'success': True,
        'leaderboard': ranked,
        'updated_at': datetime.now().isoformat()
    })

@soul_leaderboard_bp.route('/api/soul/cheer', methods=['POST'])
def cheer_for_agent():
    """
    Cheer for an AI agent (like Twitch cheering)

    POST /api/soul/cheer
    Body: {
        "agent_name": "soulfra",
        "message": "Soulfra is fire!"
    }
    """
    data = request.json

    agent_name = data.get('agent_name')
    message = data.get('message', '')

    if not agent_name:
        return jsonify({'error': 'agent_name required'}), 400

    db = get_db()

    # Record cheer
    db.execute('''
        INSERT INTO agent_cheers (agent_name, cheer_message)
        VALUES (?, ?)
    ''', (agent_name, message))
    db.commit()

    # Auto-upvote when cheering
    db.execute('''
        UPDATE ai_agents
        SET votes_up = votes_up + 1
        WHERE agent_name = ?
    ''', (agent_name,))
    db.commit()

    return jsonify({
        'success': True,
        'message': f'Cheered for {agent_name}!'
    })

@soul_leaderboard_bp.route('/api/soul/feed')
def cheering_feed():
    """
    Get recent cheers/votes (live feed)

    GET /api/soul/feed
    Returns: last 50 cheers + votes
    """
    db = get_db()

    # Get recent cheers
    cheers = db.execute('''
        SELECT
            agent_name,
            cheer_message,
            cheered_at
        FROM agent_cheers
        ORDER BY cheered_at DESC
        LIMIT 25
    ''').fetchall()

    # Get recent votes
    votes = db.execute('''
        SELECT
            agent_name,
            vote,
            voted_at
        FROM agent_votes
        ORDER BY voted_at DESC
        LIMIT 25
    ''').fetchall()

    # Combine and sort
    feed = []

    for cheer in cheers:
        feed.append({
            'type': 'cheer',
            'agent_name': cheer['agent_name'],
            'message': cheer['cheer_message'],
            'timestamp': cheer['cheered_at']
        })

    for vote in votes:
        emoji = '👍' if vote['vote'] == 1 else '👎'
        feed.append({
            'type': 'vote',
            'agent_name': vote['agent_name'],
            'message': f'{emoji} {"Upvoted" if vote["vote"] == 1 else "Downvoted"}',
            'timestamp': vote['voted_at']
        })

    # Sort by timestamp
    feed = sorted(feed, key=lambda x: x['timestamp'], reverse=True)[:50]

    return jsonify({
        'success': True,
        'feed': feed
    })

@soul_leaderboard_bp.route('/soul/leaderboard')
def leaderboard_page():
    """Serve soul leaderboard page"""
    return send_from_directory('voice-archive', 'soul-leaderboard.html')

@soul_leaderboard_bp.route('/soul/feed-page')
def feed_page():
    """Serve cheering feed page"""
    return send_from_directory('voice-archive', 'soul-feed.html')

# Update hot scores periodically (call from cron or scheduler)
def recalculate_all_hot_scores():
    """
    Recalculate hot scores for all agents
    Should be called every hour
    """
    db = get_db()

    agents = db.execute('SELECT * FROM ai_agents').fetchall()

    for agent in agents:
        hot_score = calculate_hot_score(
            agent['votes_up'],
            agent['votes_down'],
            datetime.fromisoformat(agent['created_at'])
        )

        db.execute('''
            UPDATE ai_agents SET hot_score = ? WHERE id = ?
        ''', (hot_score, agent['id']))

    db.commit()
    print(f"✅ Recalculated hot scores for {len(agents)} agents")

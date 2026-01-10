#!/usr/bin/env python3
"""
Debug Quest Routes - Flask API for Debug Quest Economy

Endpoints for:
- Fast fix requests (pay for debugging help)
- Learning quests (earn by solving challenges)
- Quest browsing/submission
- Leaderboards
"""

from flask import Blueprint, request, jsonify, render_template, session
from database import get_db
from debug_quest_economy import (
    FastFixMarketplace,
    LearningQuestMarketplace,
    FAST_FIX_PRICING,
    LEARNING_QUEST_REWARDS
)
from datetime import datetime
import json


# ==============================================================================
# BLUEPRINT SETUP
# ==============================================================================

debug_quests = Blueprint('debug_quests', __name__, url_prefix='/debug-quests')


# ==============================================================================
# FAST FIX REQUESTS (PAY FOR HELP)
# ==============================================================================

@debug_quests.route('/fast-fix/request', methods=['POST'])
def request_fast_fix():
    """
    Create fast fix request

    Request body:
        {
            'error_text': str,
            'error_context': str (optional),
            'complexity': str ('simple', 'medium', 'complex', 'expert')
        }

    Returns:
        {
            'success': bool,
            'request_id': int,
            'cost_vibe': int,
            'time_limit': int,
            'ai_solution': str
        }
    """

    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    error_text = data.get('error_text', '')
    error_context = data.get('error_context')
    complexity = data.get('complexity', 'medium')

    if not error_text:
        return jsonify({'error': 'No error text provided'}), 400

    marketplace = FastFixMarketplace()
    result = marketplace.create_fast_fix_request(
        user_id=session['user_id'],
        error_text=error_text,
        error_context=error_context,
        complexity=complexity
    )

    return jsonify(result)


@debug_quests.route('/fast-fix/solve/<int:request_id>', methods=['POST'])
def solve_fast_fix(request_id: int):
    """
    Solve a fast fix request (for human helpers)

    Request body:
        {
            'solution_text': str
        }

    Returns:
        {
            'success': bool,
            'earned_vibe': int,
            'bonus_vibe': int
        }
    """

    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    solution_text = data.get('solution_text', '')

    if not solution_text:
        return jsonify({'error': 'No solution provided'}), 400

    marketplace = FastFixMarketplace()
    result = marketplace.solve_fast_fix(
        request_id=request_id,
        solver_id=session['user_id'],
        solution_text=solution_text
    )

    return jsonify(result)


@debug_quests.route('/fast-fix/list', methods=['GET'])
def list_fast_fix_requests():
    """
    List open fast fix requests (for helpers)

    Query params:
        complexity: Filter by complexity
        limit: Max results (default 20)

    Returns:
        {
            'requests': [...]
        }
    """

    complexity = request.args.get('complexity')
    limit = int(request.args.get('limit', 20))

    conn = get_db()

    query = '''
        SELECT
            id, error_text, complexity, budget_vibe,
            created_at, ai_solution
        FROM fast_fix_requests
        WHERE status = 'pending'
    '''

    params = []

    if complexity:
        query += ' AND complexity = ?'
        params.append(complexity)

    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)

    requests_list = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        'requests': [dict(r) for r in requests_list],
        'count': len(requests_list)
    })


@debug_quests.route('/fast-fix/my-requests', methods=['GET'])
def my_fast_fix_requests():
    """
    Get user's fast fix requests

    Returns:
        {
            'requests': [...]
        }
    """

    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()

    requests_list = conn.execute('''
        SELECT
            id, error_text, complexity, budget_vibe,
            status, ai_solution, human_solution,
            created_at, solved_at
        FROM fast_fix_requests
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return jsonify({
        'requests': [dict(r) for r in requests_list],
        'count': len(requests_list)
    })


# ==============================================================================
# LEARNING QUESTS (EARN BY SOLVING)
# ==============================================================================

@debug_quests.route('/quests/list', methods=['GET'])
def list_learning_quests():
    """
    List available learning quests

    Query params:
        difficulty: Filter by difficulty
        category: Filter by category
        limit: Max results (default 50)

    Returns:
        {
            'quests': [...]
        }
    """

    difficulty = request.args.get('difficulty')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 50))

    conn = get_db()

    query = '''
        SELECT
            id, title, description, error_example,
            difficulty, reward_vibe, category, tags,
            created_at, github_issue_url
        FROM learning_quests
        WHERE status = 'open'
    '''

    params = []

    if difficulty:
        query += ' AND difficulty = ?'
        params.append(difficulty)

    if category:
        query += ' AND category = ?'
        params.append(category)

    query += ' ORDER BY reward_vibe DESC, created_at DESC LIMIT ?'
    params.append(limit)

    quests = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        'quests': [dict(q) for q in quests],
        'count': len(quests)
    })


@debug_quests.route('/quests/create', methods=['POST'])
def create_learning_quest():
    """
    Create a learning quest (admin only)

    Request body:
        {
            'title': str,
            'description': str,
            'error_example': str,
            'difficulty': str,
            'category': str,
            'tags': [str]
        }

    Returns:
        {
            'success': bool,
            'quest_id': int
        }
    """

    if not session.get('is_admin'):
        return jsonify({'error': 'Admin only'}), 403

    data = request.get_json()

    marketplace = LearningQuestMarketplace()
    result = marketplace.create_quest(
        title=data.get('title', ''),
        description=data.get('description', ''),
        error_example=data.get('error_example', ''),
        difficulty=data.get('difficulty', 'intermediate'),
        category=data.get('category', 'general'),
        tags=data.get('tags', []),
        created_by=session.get('user_id')
    )

    return jsonify(result)


@debug_quests.route('/quests/submit/<int:quest_id>', methods=['POST'])
def submit_quest_solution(quest_id: int):
    """
    Submit solution to a quest

    Request body:
        {
            'solution_text': str,
            'solution_code': str (optional)
        }

    Returns:
        {
            'success': bool,
            'submission_id': int,
            'ai_review_score': float,
            'status': str
        }
    """

    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    solution_text = data.get('solution_text', '')
    solution_code = data.get('solution_code')

    if not solution_text:
        return jsonify({'error': 'No solution provided'}), 400

    marketplace = LearningQuestMarketplace()
    result = marketplace.submit_solution(
        quest_id=quest_id,
        user_id=session['user_id'],
        solution_text=solution_text,
        solution_code=solution_code
    )

    return jsonify(result)


@debug_quests.route('/quests/my-submissions', methods=['GET'])
def my_quest_submissions():
    """
    Get user's quest submissions

    Returns:
        {
            'submissions': [...]
        }
    """

    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()

    submissions = conn.execute('''
        SELECT
            qs.id, qs.quest_id, qs.solution_text,
            qs.ai_review_score, qs.status,
            qs.submitted_at, qs.reviewed_at,
            lq.title as quest_title,
            lq.reward_vibe
        FROM quest_submissions qs
        JOIN learning_quests lq ON qs.quest_id = lq.id
        WHERE qs.user_id = ?
        ORDER BY qs.submitted_at DESC
        LIMIT 50
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return jsonify({
        'submissions': [dict(s) for s in submissions],
        'count': len(submissions)
    })


# ==============================================================================
# LEADERBOARDS & REPUTATION
# ==============================================================================

@debug_quests.route('/leaderboard', methods=['GET'])
def leaderboard():
    """
    Get top contributors leaderboard

    Query params:
        metric: 'quests' or 'vibe' (default 'vibe')
        limit: Max results (default 50)

    Returns:
        {
            'leaderboard': [...]
        }
    """

    metric = request.args.get('metric', 'vibe')
    limit = int(request.args.get('limit', 50))

    conn = get_db()

    if metric == 'quests':
        order_by = 'total_quests_solved DESC'
    else:
        order_by = 'total_vibe_earned DESC'

    leaders = conn.execute(f'''
        SELECT
            dr.user_id,
            u.username,
            dr.total_quests_solved,
            dr.total_vibe_earned,
            dr.avg_review_score,
            dr.fastest_solve_time,
            dr.github_username
        FROM debug_reputation dr
        LEFT JOIN users u ON dr.user_id = u.id
        ORDER BY {order_by}
        LIMIT ?
    ''', (limit,)).fetchall()

    conn.close()

    return jsonify({
        'leaderboard': [dict(l) for l in leaders],
        'count': len(leaders)
    })


@debug_quests.route('/reputation/<int:user_id>', methods=['GET'])
def user_reputation(user_id: int):
    """
    Get user's debugging reputation

    Returns:
        {
            'user_id': int,
            'username': str,
            'stats': {...}
        }
    """

    conn = get_db()

    user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    stats = conn.execute('SELECT * FROM debug_reputation WHERE user_id = ?', (user_id,)).fetchone()

    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user_id': user_id,
        'username': user['username'],
        'stats': dict(stats) if stats else {
            'total_quests_solved': 0,
            'total_vibe_earned': 0,
            'avg_review_score': 0.0,
            'fastest_solve_time': None
        }
    })


# ==============================================================================
# INFO ENDPOINTS
# ==============================================================================

@debug_quests.route('/pricing', methods=['GET'])
def pricing_info():
    """
    Get pricing for fast fixes and quest rewards

    Returns:
        {
            'fast_fix_pricing': {...},
            'learning_quest_rewards': {...}
        }
    """

    return jsonify({
        'fast_fix_pricing': FAST_FIX_PRICING,
        'learning_quest_rewards': LEARNING_QUEST_REWARDS
    })


@debug_quests.route('/stats', methods=['GET'])
def marketplace_stats():
    """
    Get marketplace statistics

    Returns:
        {
            'total_quests': int,
            'open_quests': int,
            'total_fast_fixes': int,
            'pending_fast_fixes': int,
            'total_vibe_paid': int
        }
    """

    conn = get_db()

    total_quests = conn.execute('SELECT COUNT(*) FROM learning_quests').fetchone()[0]
    open_quests = conn.execute("SELECT COUNT(*) FROM learning_quests WHERE status = 'open'").fetchone()[0]
    total_fast_fixes = conn.execute('SELECT COUNT(*) FROM fast_fix_requests').fetchone()[0]
    pending_fast_fixes = conn.execute("SELECT COUNT(*) FROM fast_fix_requests WHERE status = 'pending'").fetchone()[0]

    total_vibe = conn.execute('''
        SELECT SUM(budget_vibe) FROM fast_fix_requests WHERE status = 'solved'
    ''').fetchone()[0] or 0

    conn.close()

    return jsonify({
        'total_quests': total_quests,
        'open_quests': open_quests,
        'total_fast_fixes': total_fast_fixes,
        'pending_fast_fixes': pending_fast_fixes,
        'total_vibe_paid': total_vibe
    })


# ==============================================================================
# UI ROUTES
# ==============================================================================

@debug_quests.route('/', methods=['GET'])
def quest_marketplace_ui():
    """Debug Quest Marketplace homepage"""
    return render_template('debug_quests.html')


@debug_quests.route('/fast-fix', methods=['GET'])
def fast_fix_ui():
    """Fast Fix request form"""
    return render_template('fast_fix_request.html')


# ==============================================================================
# REGISTRATION
# ==============================================================================

def register_debug_quest_routes(app):
    """
    Register Debug Quest blueprint with Flask app

    Args:
        app: Flask application

    Returns:
        Blueprint instance
    """
    app.register_blueprint(debug_quests)

    print("✅ Debug Quest routes registered at /debug-quests/*")

    return debug_quests


if __name__ == '__main__':
    print("Debug Quest API Routes:")
    print()
    print("Fast Fix (Pay for Help):")
    print("  POST /debug-quests/fast-fix/request")
    print("  POST /debug-quests/fast-fix/solve/<id>")
    print("  GET  /debug-quests/fast-fix/list")
    print("  GET  /debug-quests/fast-fix/my-requests")
    print()
    print("Learning Quests (Earn by Solving):")
    print("  GET  /debug-quests/quests/list")
    print("  POST /debug-quests/quests/create (admin)")
    print("  POST /debug-quests/quests/submit/<id>")
    print("  GET  /debug-quests/quests/my-submissions")
    print()
    print("Leaderboards:")
    print("  GET  /debug-quests/leaderboard")
    print("  GET  /debug-quests/reputation/<user_id>")
    print()
    print("Info:")
    print("  GET  /debug-quests/pricing")
    print("  GET  /debug-quests/stats")

"""
Token Economy API

Manages time tokens/coins that users earn and spend to extend draft timers.
Part of the "Chat → Yap → Ideate → Lock In" pipeline.
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timedelta

token_economy_bp = Blueprint('token_economy', __name__)

# Token earning rates (in minutes)
TOKEN_RATES = {
    'voice_memo_recorded': 5,
    'comment_on_idea': 2,
    'blog_post_published': 10,
    'idea_used_in_blog': 3,
    'domain_contribution': 5
}

# Token spending costs (in minutes)
TOKEN_COSTS = {
    'extend_draft_timer': 1,  # 1 token = 1 minute extension
    'freeze_draft': 60,  # Freeze draft indefinitely
    'priority_publish': 30  # Skip timer and publish immediately
}

def get_db_connection():
    """Get database connection with Row factory"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_token_tables():
    """Initialize token economy tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # User tokens balance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_balance INTEGER DEFAULT 0,
            lifetime_earned INTEGER DEFAULT 0,
            lifetime_spent INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Token transaction history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

@token_economy_bp.route('/api/tokens/balance/<int:user_id>', methods=['GET'])
def get_token_balance(user_id):
    """Get user's current token balance"""
    try:
        init_token_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM user_tokens
            WHERE user_id = ?
        ''', (user_id,))

        balance_row = cursor.fetchone()

        if not balance_row:
            # Initialize balance for new user
            cursor.execute('''
                INSERT INTO user_tokens (user_id, token_balance, lifetime_earned, lifetime_spent, last_updated)
                VALUES (?, 15, 15, 0, ?)
            ''', (user_id, datetime.utcnow().isoformat()))
            conn.commit()

            return jsonify({
                'success': True,
                'user_id': user_id,
                'token_balance': 15,  # Starting balance
                'lifetime_earned': 15,
                'lifetime_spent': 0
            })

        conn.close()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'token_balance': balance_row['token_balance'],
            'lifetime_earned': balance_row['lifetime_earned'],
            'lifetime_spent': balance_row['lifetime_spent']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@token_economy_bp.route('/api/tokens/earn', methods=['POST'])
def earn_tokens():
    """Earn tokens for an action"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        action = data.get('action')

        if not user_id or not action:
            return jsonify({'success': False, 'error': 'Missing user_id or action'}), 400

        if action not in TOKEN_RATES:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400

        tokens_earned = TOKEN_RATES[action]

        init_token_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get or create user balance
        cursor.execute('SELECT * FROM user_tokens WHERE user_id = ?', (user_id,))
        balance_row = cursor.fetchone()

        if not balance_row:
            cursor.execute('''
                INSERT INTO user_tokens (user_id, token_balance, lifetime_earned, lifetime_spent, last_updated)
                VALUES (?, ?, ?, 0, ?)
            ''', (user_id, tokens_earned, tokens_earned, datetime.utcnow().isoformat()))
        else:
            new_balance = balance_row['token_balance'] + tokens_earned
            new_lifetime = balance_row['lifetime_earned'] + tokens_earned

            cursor.execute('''
                UPDATE user_tokens
                SET token_balance = ?, lifetime_earned = ?, last_updated = ?
                WHERE user_id = ?
            ''', (new_balance, new_lifetime, datetime.utcnow().isoformat(), user_id))

        # Log transaction
        cursor.execute('''
            INSERT INTO token_transactions (user_id, transaction_type, amount, reason, created_at)
            VALUES (?, 'earn', ?, ?, ?)
        ''', (user_id, tokens_earned, action, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'action': action,
            'tokens_earned': tokens_earned,
            'new_balance': balance_row['token_balance'] + tokens_earned if balance_row else tokens_earned
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@token_economy_bp.route('/api/tokens/spend', methods=['POST'])
def spend_tokens():
    """Spend tokens on an action"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        action = data.get('action')
        amount = data.get('amount')  # Optional: specify custom amount

        if not user_id or not action:
            return jsonify({'success': False, 'error': 'Missing user_id or action'}), 400

        # Determine cost
        if amount:
            tokens_cost = amount
        elif action in TOKEN_COSTS:
            tokens_cost = TOKEN_COSTS[action]
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400

        init_token_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user balance
        cursor.execute('SELECT * FROM user_tokens WHERE user_id = ?', (user_id,))
        balance_row = cursor.fetchone()

        if not balance_row or balance_row['token_balance'] < tokens_cost:
            return jsonify({
                'success': False,
                'error': 'Insufficient tokens',
                'required': tokens_cost,
                'available': balance_row['token_balance'] if balance_row else 0
            }), 400

        # Deduct tokens
        new_balance = balance_row['token_balance'] - tokens_cost
        new_spent = balance_row['lifetime_spent'] + tokens_cost

        cursor.execute('''
            UPDATE user_tokens
            SET token_balance = ?, lifetime_spent = ?, last_updated = ?
            WHERE user_id = ?
        ''', (new_balance, new_spent, datetime.utcnow().isoformat(), user_id))

        # Log transaction
        cursor.execute('''
            INSERT INTO token_transactions (user_id, transaction_type, amount, reason, created_at)
            VALUES (?, 'spend', ?, ?, ?)
        ''', (user_id, -tokens_cost, action, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'action': action,
            'tokens_spent': tokens_cost,
            'new_balance': new_balance
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@token_economy_bp.route('/api/tokens/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    """Get user's token transaction history"""
    try:
        init_token_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        limit = request.args.get('limit', 50, type=int)

        cursor.execute('''
            SELECT * FROM token_transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))

        transactions = cursor.fetchall()
        conn.close()

        return jsonify({
            'success': True,
            'transactions': [{
                'id': t['id'],
                'type': t['transaction_type'],
                'amount': t['amount'],
                'reason': t['reason'],
                'created_at': t['created_at']
            } for t in transactions]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@token_economy_bp.route('/api/tokens/leaderboard', methods=['GET'])
def token_leaderboard():
    """Get top token earners"""
    try:
        init_token_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT u.username, ut.token_balance, ut.lifetime_earned
            FROM user_tokens ut
            JOIN users u ON ut.user_id = u.id
            ORDER BY ut.lifetime_earned DESC
            LIMIT 10
        ''')

        leaderboard = cursor.fetchall()
        conn.close()

        return jsonify({
            'success': True,
            'leaderboard': [{
                'username': row['username'],
                'current_balance': row['token_balance'],
                'lifetime_earned': row['lifetime_earned']
            } for row in leaderboard]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

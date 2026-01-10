#!/usr/bin/env python3
"""
Prepaid Credits System - Simple Manual Payment Processing

For $1 payments, skip payment processors entirely:
1. User Zelles you $10 via Mercury
2. You run: /api/admin/credits/add with their email
3. They spend $1 at a time from balance
4. Zero fees, zero complexity

No Stripe, no BTCPay, no Lightning needed for MVP.
Add those later for automation.
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from functools import wraps
import sqlite3

credits_bp = Blueprint('credits', __name__)


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@credits_bp.route('/api/credits/balance', methods=['GET'])
def get_balance():
    """
    Get current user's credit balance

    Returns: {'balance': 10.00, 'email': 'user@example.com'}
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    user = db.execute('''
        SELECT email, credits, display_name as domain
        FROM users
        WHERE id = ?
    ''', (session['user_id'],)).fetchone()
    db.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'balance': user['credits'] or 0.00,
        'email': user['email'],
        'domain': user['domain']
    })


@credits_bp.route('/api/admin/credits/add', methods=['POST'])
@admin_required
def add_credits():
    """
    Add credits to a user's account (admin only)

    POST body: {
        'email': 'user@example.com',
        'amount': 10.00,
        'note': 'Zelle payment received'
    }

    Returns: {'success': true, 'new_balance': 10.00}
    """
    data = request.get_json()

    email = data.get('email')
    amount = data.get('amount')
    note = data.get('note', '')

    if not email or not amount:
        return jsonify({'error': 'Missing email or amount'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400

    db = get_db()

    # Find user
    user = db.execute('SELECT id, credits FROM users WHERE email = ?', (email,)).fetchone()

    if not user:
        db.close()
        return jsonify({'error': f'User not found: {email}'}), 404

    # Add credits
    current_balance = user['credits'] or 0.00
    new_balance = current_balance + amount

    db.execute('''
        UPDATE users
        SET credits = ?
        WHERE id = ?
    ''', (new_balance, user['id']))

    # Log transaction
    db.execute('''
        INSERT INTO credit_transactions (
            user_id, amount, transaction_type, note, admin_id, created_at
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user['id'], amount, 'add', note, session.get('user_id')))

    db.commit()
    db.close()

    print(f"✅ Added ${amount} credits to {email} (new balance: ${new_balance})")

    return jsonify({
        'success': True,
        'email': email,
        'amount_added': amount,
        'new_balance': new_balance,
        'note': note
    })


@credits_bp.route('/api/credits/spend', methods=['POST'])
def spend_credits():
    """
    Spend credits (e.g., for $1 checkout)

    POST body: {
        'amount': 1.00,
        'product': 'voice_checkout',
        'metadata': {...}
    }

    Returns: {'success': true, 'new_balance': 9.00}
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()

    amount = data.get('amount', 1.00)
    product = data.get('product', 'unknown')
    metadata = data.get('metadata', {})

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400

    db = get_db()

    # Get current balance
    user = db.execute('''
        SELECT id, email, credits
        FROM users
        WHERE id = ?
    ''', (session['user_id'],)).fetchone()

    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404

    current_balance = user['credits'] or 0.00

    # Check sufficient balance
    if current_balance < amount:
        db.close()
        return jsonify({
            'error': f'Insufficient credits. Balance: ${current_balance:.2f}, Required: ${amount:.2f}',
            'balance': current_balance,
            'required': amount
        }), 400

    # Deduct credits
    new_balance = current_balance - amount

    db.execute('''
        UPDATE users
        SET credits = ?
        WHERE id = ?
    ''', (new_balance, user['id']))

    # Log transaction
    import json
    db.execute('''
        INSERT INTO credit_transactions (
            user_id, amount, transaction_type, note, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        user['id'],
        -amount,  # Negative for spending
        'spend',
        f'Purchase: {product}',
        json.dumps(metadata)
    ))

    db.commit()
    db.close()

    print(f"✅ {user['email']} spent ${amount} on {product} (new balance: ${new_balance})")

    return jsonify({
        'success': True,
        'amount_spent': amount,
        'new_balance': new_balance,
        'product': product
    })


@credits_bp.route('/api/admin/credits/transactions', methods=['GET'])
@admin_required
def get_transactions():
    """
    Get all credit transactions (admin only)

    Query params:
    - user_id: Filter by user
    - limit: Number of results (default 100)

    Returns: {'transactions': [...]}
    """
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 100))

    db = get_db()

    if user_id:
        transactions = db.execute('''
            SELECT
                t.*,
                u.email as user_email
            FROM credit_transactions t
            JOIN users u ON t.user_id = u.id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()
    else:
        transactions = db.execute('''
            SELECT
                t.*,
                u.email as user_email
            FROM credit_transactions t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    db.close()

    return jsonify({
        'transactions': [dict(t) for t in transactions]
    })


def init_credits_tables():
    """Create credits-related tables"""
    db = get_db()

    # Add credits column to users table if it doesn't exist
    try:
        db.execute('SELECT credits FROM users LIMIT 1')
    except sqlite3.OperationalError:
        print("Adding credits column to users table...")
        db.execute('ALTER TABLE users ADD COLUMN credits REAL DEFAULT 0.0')
        print("✅ Credits column added")

    # Create credit_transactions table
    db.execute('''
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            note TEXT,
            metadata TEXT,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (admin_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Credits tables ready")


if __name__ == '__main__':
    print("🔐 Creating credits tables...")
    init_credits_tables()
    print("✅ Credits system ready!")
    print()
    print("Usage:")
    print("  1. User Zelles you $10")
    print("  2. You run: POST /api/admin/credits/add {'email': 'them@email.com', 'amount': 10}")
    print("  3. They spend: POST /api/credits/spend {'amount': 1.00}")
    print("  4. Check balance: GET /api/credits/balance")

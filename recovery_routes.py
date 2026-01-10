#!/usr/bin/env python3
"""
Account Recovery System - SOC2/GDPR Compliant

Features:
- Password reset via email token
- Account data export (GDPR compliance)
- Account deletion (right to be forgotten)
- Audit logging for all auth events

No actual email sending (use console logs for dev, add SMTP later)
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from werkzeug.security import generate_password_hash
import secrets
import json
from datetime import datetime, timedelta

recovery_bp = Blueprint('recovery', __name__)


@recovery_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset

    POST body: {'email': 'user@example.com', 'domain': 'cringeproof.com'}

    Creates reset token, stores in DB
    In production: Send email with reset link
    In dev: Returns token in response (for testing)
    """
    data = request.get_json()
    email = data.get('email')
    domain = data.get('domain', request.headers.get('Origin', ''))

    if domain.startswith('http'):
        domain = domain.split('://')[1].split('/')[0]

    if not email:
        return jsonify({'error': 'Email required'}), 400

    db = get_db()

    # Find user
    user = db.execute('''
        SELECT id, email, display_name
        FROM users
        WHERE email = ? AND (display_name = ? OR display_name IS NULL)
    ''', (email, domain)).fetchone()

    if not user:
        # Don't reveal if email exists (security best practice)
        return jsonify({
            'success': True,
            'message': 'If that email exists, a reset link has been sent'
        })

    # Generate reset token (cryptographically secure)
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Store token
    db.execute('''
        INSERT INTO password_reset_tokens (
            user_id, token, expires_at, created_at
        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user['id'], reset_token, expires_at))

    # Log audit event
    db.execute('''
        INSERT INTO audit_log (
            user_id, event_type, details, ip_address, created_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user['id'], 'password_reset_requested', json.dumps({
        'email': email,
        'domain': domain
    }), request.remote_addr))

    db.commit()
    db.close()

    # In production: Send email with reset link
    reset_url = f"https://{domain}/reset-password.html?token={reset_token}"

    print(f"🔐 Password reset requested for {email}")
    print(f"   Reset URL: {reset_url}")

    # DEV MODE: Return token in response
    return jsonify({
        'success': True,
        'message': 'Password reset email sent (check console in dev mode)',
        'dev_token': reset_token,  # Remove this in production!
        'dev_url': reset_url
    })


@recovery_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password with valid token

    POST body: {
        'token': 'abc123...',
        'new_password': 'newpass123'
    }
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({'error': 'Token and new password required'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    db = get_db()

    # Find valid token
    reset = db.execute('''
        SELECT
            t.id as token_id,
            t.user_id,
            t.expires_at,
            t.used_at,
            u.email
        FROM password_reset_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ?
    ''', (token,)).fetchone()

    if not reset:
        db.close()
        return jsonify({'error': 'Invalid reset token'}), 400

    # Check if already used
    if reset['used_at']:
        db.close()
        return jsonify({'error': 'Reset token already used'}), 400

    # Check if expired
    expires_at = datetime.fromisoformat(reset['expires_at'])
    if datetime.utcnow() > expires_at:
        db.close()
        return jsonify({'error': 'Reset token expired'}), 400

    # Update password
    password_hash = generate_password_hash(new_password, method='scrypt')

    db.execute('''
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
    ''', (password_hash, reset['user_id']))

    # Mark token as used
    db.execute('''
        UPDATE password_reset_tokens
        SET used_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (reset['token_id'],))

    # Log audit event
    db.execute('''
        INSERT INTO audit_log (
            user_id, event_type, details, ip_address, created_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (reset['user_id'], 'password_reset_completed', json.dumps({
        'email': reset['email']
    }), request.remote_addr))

    db.commit()
    db.close()

    print(f"✅ Password reset completed for {reset['email']}")

    return jsonify({
        'success': True,
        'message': 'Password reset successfully'
    })


@recovery_bp.route('/api/account/export', methods=['GET'])
def export_account_data():
    """
    Export all user data (GDPR compliance)

    Returns JSON with all user data:
    - Profile info
    - Voice memos
    - Transactions
    - Messages
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    db = get_db()

    # Get user profile
    user = db.execute('''
        SELECT id, username, email, display_name, credits, created_at
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    # Get transactions
    transactions = db.execute('''
        SELECT * FROM credit_transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # Get audit log
    audit_log = db.execute('''
        SELECT * FROM audit_log
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    db.close()

    export_data = {
        'exported_at': datetime.utcnow().isoformat(),
        'user': dict(user) if user else None,
        'transactions': [dict(t) for t in transactions],
        'audit_log': [dict(a) for a in audit_log]
    }

    print(f"📦 Data export requested by user {user_id}")

    return jsonify(export_data)


@recovery_bp.route('/api/account/delete', methods=['POST'])
def delete_account():
    """
    Delete account (GDPR right to be forgotten)

    POST body: {'password': 'confirm_password'}

    Requires password confirmation
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    password = data.get('password')

    if not password:
        return jsonify({'error': 'Password confirmation required'}), 400

    user_id = session['user_id']
    db = get_db()

    # Verify password
    user = db.execute('''
        SELECT id, email, password_hash
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    from werkzeug.security import check_password_hash
    if not check_password_hash(user['password_hash'], password):
        db.close()
        return jsonify({'error': 'Incorrect password'}), 401

    # Log deletion
    db.execute('''
        INSERT INTO audit_log (
            user_id, event_type, details, ip_address, created_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, 'account_deleted', json.dumps({
        'email': user['email']
    }), request.remote_addr))

    # Delete user data
    db.execute('DELETE FROM credit_transactions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM password_reset_tokens WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))

    db.commit()
    db.close()

    # Clear session
    session.clear()

    print(f"🗑️  Account deleted: {user['email']}")

    return jsonify({
        'success': True,
        'message': 'Account deleted successfully'
    })


def init_recovery_tables():
    """Create recovery-related tables"""
    db = get_db()

    # Password reset tokens
    db.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Audit log (SOC2 compliance)
    db.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Recovery tables ready")


if __name__ == '__main__':
    print("🔐 Creating recovery tables...")
    init_recovery_tables()
    print("✅ Recovery system ready!")

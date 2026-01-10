#!/usr/bin/env python3
"""
Account Claiming System - Link anonymous sessions to real accounts

Allows users to:
- Use app anonymously (scan QR → instant access)
- Claim their session later (keep all recordings/ideas)
- Link multiple auth providers (GitHub, phone, email, wallet)
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect
from database import get_db
from datetime import datetime, timedelta
import secrets
import hashlib

auth_claim_bp = Blueprint('auth_claim', __name__)


@auth_claim_bp.route('/claim')
def claim_page():
    """
    Account claiming page - Shows user what they've done anonymously
    """
    session_token = session.get('search_token') or session.get('session_token')

    if not session_token:
        return redirect('/login/qr?redirect=/claim')

    db = get_db()

    # Get anonymous session info
    anon_session = db.execute('''
        SELECT * FROM anonymous_sessions WHERE session_token = ?
    ''', (session_token,)).fetchone()

    if not anon_session:
        db.close()
        return redirect('/login/qr?redirect=/claim')

    # Get stats for this anonymous session
    # Count recordings from this device fingerprint
    recordings_count = db.execute('''
        SELECT COUNT(*) as count FROM simple_voice_recordings
        WHERE user_id IN (
            SELECT id FROM users
            WHERE device_fingerprint = ?
        )
    ''', (anon_session['device_fingerprint'],)).fetchone()['count']

    # Count ideas
    ideas_count = db.execute('''
        SELECT COUNT(*) as count FROM voice_ideas
        WHERE user_id IN (
            SELECT id FROM users
            WHERE device_fingerprint = ?
        )
    ''', (anon_session['device_fingerprint'],)).fetchone()['count']

    # Days active
    created_at = datetime.fromisoformat(anon_session['created_at'])
    days_active = (datetime.now() - created_at).days

    db.close()

    return render_template('claim_account.html',
                          recordings_count=recordings_count,
                          ideas_count=ideas_count,
                          days_active=days_active,
                          session_token=session_token,
                          already_claimed=anon_session['claimed_by_user_id'] is not None)


@auth_claim_bp.route('/api/claim/github')
def claim_github():
    """
    Start GitHub OAuth flow to claim anonymous account
    """
    from github_oauth import get_github_auth_url

    # Store original session token so we can claim it after OAuth
    session_token = session.get('search_token') or session.get('session_token')
    session['claiming_session_token'] = session_token

    # Redirect to GitHub OAuth
    auth_url = get_github_auth_url(redirect_uri='/api/claim/github/callback')
    return redirect(auth_url)


@auth_claim_bp.route('/api/claim/github/callback')
def claim_github_callback():
    """
    GitHub OAuth callback - Link GitHub account to anonymous session
    """
    code = request.args.get('code')

    if not code:
        return jsonify({'success': False, 'error': 'No code provided'}), 400

    from github_oauth import get_github_access_token, get_github_user

    # Get GitHub access token
    access_token = get_github_access_token(code, redirect_uri='/api/claim/github/callback')

    if not access_token:
        return jsonify({'success': False, 'error': 'Failed to get access token'}), 400

    # Get GitHub user info
    github_user = get_github_user(access_token)

    if not github_user:
        return jsonify({'success': False, 'error': 'Failed to get user info'}), 400

    # Get the anonymous session we're claiming
    claiming_token = session.get('claiming_session_token')

    if not claiming_token:
        return jsonify({'success': False, 'error': 'No session to claim'}), 400

    db = get_db()

    # Check if GitHub account already exists
    existing_user = db.execute('''
        SELECT * FROM users WHERE email = ?
    ''', (github_user['email'],)).fetchone()

    if existing_user:
        # Merge anonymous session into existing account
        user_id = existing_user['id']
    else:
        # Create new account from GitHub
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, ?, ?)
        ''', (
            github_user['login'],
            github_user['email'],
            'github-oauth',  # No password for OAuth users
            github_user['name'] or github_user['login']
        ))
        user_id = cursor.lastrowid

    # Claim the anonymous session
    db.execute('''
        UPDATE anonymous_sessions
        SET claimed_by_user_id = ?, claimed_at = ?
        WHERE session_token = ?
    ''', (user_id, datetime.now().isoformat(), claiming_token))

    # Transfer all anonymous data to claimed user
    # Get device fingerprint from anonymous session
    anon_session = db.execute('''
        SELECT device_fingerprint FROM anonymous_sessions WHERE session_token = ?
    ''', (claiming_token,)).fetchone()

    if anon_session:
        # Update all recordings from anonymous users with same device fingerprint
        db.execute('''
            UPDATE simple_voice_recordings
            SET user_id = ?
            WHERE user_id IN (
                SELECT id FROM users WHERE device_fingerprint = ?
            )
        ''', (user_id, anon_session['device_fingerprint']))

        # Update all ideas
        db.execute('''
            UPDATE voice_ideas
            SET user_id = ?
            WHERE user_id IN (
                SELECT id FROM users WHERE device_fingerprint = ?
            )
        ''', (user_id, anon_session['device_fingerprint']))

    db.commit()
    db.close()

    # Set user session
    session['user_id'] = user_id
    session.pop('claiming_session_token', None)

    return redirect('/claim/success')


@auth_claim_bp.route('/claim/success')
def claim_success():
    """Success page after claiming account"""
    return render_template('claim_success.html')


@auth_claim_bp.route('/api/claim/phone', methods=['POST'])
def claim_phone():
    """
    Claim account via phone number (SMS verification)

    Request: {"phone": "+15551234567"}
    Response: {"success": true, "verification_code_sent": true}
    """
    data = request.get_json()
    phone = data.get('phone', '').strip()

    if not phone:
        return jsonify({'success': False, 'error': 'Phone number required'}), 400

    # Hash phone number (never store plaintext)
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()

    # Generate 6-digit verification code
    verification_code = str(secrets.randbelow(1000000)).zfill(6)

    # Store verification code (expires in 10 minutes)
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS phone_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_hash TEXT NOT NULL,
            verification_code TEXT NOT NULL,
            session_token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            verified BOOLEAN DEFAULT 0
        )
    ''')

    session_token = session.get('search_token') or session.get('session_token')

    db.execute('''
        INSERT INTO phone_verifications (phone_hash, verification_code, session_token, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (
        phone_hash,
        verification_code,
        session_token,
        (datetime.now() + timedelta(minutes=10)).isoformat()
    ))
    db.commit()
    db.close()

    # TODO: Send SMS via Twilio
    # For now, just return the code (development only!)
    return jsonify({
        'success': True,
        'verification_code_sent': True,
        'verification_code': verification_code  # Remove in production!
    })


@auth_claim_bp.route('/api/claim/phone/verify', methods=['POST'])
def verify_phone():
    """
    Verify phone number and claim account

    Request: {"phone": "+15551234567", "code": "123456"}
    Response: {"success": true, "user_id": 1}
    """
    data = request.get_json()
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()

    if not phone or not code:
        return jsonify({'success': False, 'error': 'Phone and code required'}), 400

    phone_hash = hashlib.sha256(phone.encode()).hexdigest()
    session_token = session.get('search_token') or session.get('session_token')

    db = get_db()

    # Check verification code
    verification = db.execute('''
        SELECT * FROM phone_verifications
        WHERE phone_hash = ?
        AND session_token = ?
        AND verification_code = ?
        AND expires_at > ?
        AND verified = 0
    ''', (
        phone_hash,
        session_token,
        code,
        datetime.now().isoformat()
    )).fetchone()

    if not verification:
        db.close()
        return jsonify({'success': False, 'error': 'Invalid or expired code'}), 400

    # Mark as verified
    db.execute('''
        UPDATE phone_verifications SET verified = 1 WHERE id = ?
    ''', (verification['id'],))

    # Check if phone already has account
    existing_user = db.execute('''
        SELECT * FROM users WHERE phone_hash = ?
    ''', (phone_hash,)).fetchone()

    if existing_user:
        user_id = existing_user['id']
    else:
        # Create new account
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, phone_hash, phone_verified, phone_verified_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            f'phone_{secrets.token_hex(4)}',
            f'phone_{secrets.token_hex(4)}@cringeproof.com',
            'phone-verified',
            phone_hash,
            1,
            datetime.now().isoformat()
        ))
        user_id = cursor.lastrowid

    # Claim anonymous session
    db.execute('''
        UPDATE anonymous_sessions
        SET claimed_by_user_id = ?, claimed_at = ?
        WHERE session_token = ?
    ''', (user_id, datetime.now().isoformat(), session_token))

    # Transfer anonymous data
    anon_session = db.execute('''
        SELECT device_fingerprint FROM anonymous_sessions WHERE session_token = ?
    ''', (session_token,)).fetchone()

    if anon_session:
        db.execute('''
            UPDATE simple_voice_recordings SET user_id = ?
            WHERE user_id IN (SELECT id FROM users WHERE device_fingerprint = ?)
        ''', (user_id, anon_session['device_fingerprint']))

        db.execute('''
            UPDATE voice_ideas SET user_id = ?
            WHERE user_id IN (SELECT id FROM users WHERE device_fingerprint = ?)
        ''', (user_id, anon_session['device_fingerprint']))

    db.commit()
    db.close()

    # Set user session
    session['user_id'] = user_id

    return jsonify({'success': True, 'user_id': user_id})


def register_claim_routes(app):
    """Register account claiming routes"""
    app.register_blueprint(auth_claim_bp)
    print("✅ Account claiming routes registered:")
    print("   - /claim (Claim page)")
    print("   - /api/claim/github (GitHub OAuth claim)")
    print("   - /api/claim/phone (Phone verification claim)")
    print("   - /api/claim/phone/verify (Verify phone code)")

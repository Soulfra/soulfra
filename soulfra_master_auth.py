#!/usr/bin/env python3
"""
Soulfra Master Authentication System

Central authentication hub for all domains (soulfra.com, deathtodata.com, calriven.com, etc.)

Features:
- Single signup → mirrored accounts across ALL domains
- Domain-specific monikers (usernames)
- Cross-domain session validation
- Central calendar/timer tracking
- User signup counter

Flow:
1. User signs up on soulfra.com with email/password
2. Master account created in soulfra_master_users table
3. Monikers auto-generated for each domain
4. Mirror accounts created in domain-specific users tables
5. Single JWT token validates across all domains
"""

from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import jwt
import datetime
import os
from moniker_generator import generate_all_monikers
from dual_persona_generator import generate_display_name_personas, generate_device_fingerprint

master_auth_bp = Blueprint('master_auth', __name__)

# JWT Secret for cross-domain tokens
JWT_SECRET = os.getenv('JWT_SECRET', 'soulfra-2026-device-flow-secret')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 168  # 7 days


def init_master_auth_tables():
    """Create master authentication tables"""
    db = get_db()

    # Master users table - single source of truth
    db.execute('''
        CREATE TABLE IF NOT EXISTS soulfra_master_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            master_username TEXT UNIQUE NOT NULL,

            -- Display Name + Device Binding
            display_name TEXT,
            first_name TEXT,
            last_name TEXT,
            device_fingerprint TEXT,

            -- Domain monikers (auto-generated)
            soulfra_moniker TEXT,
            deathtodata_moniker TEXT,
            calriven_moniker TEXT,
            cringeproof_moniker TEXT,
            howtocookathome_moniker TEXT,

            -- Domain-specific user IDs (foreign keys)
            soulfra_user_id INTEGER,
            deathtodata_user_id INTEGER,
            calriven_user_id INTEGER,
            cringeproof_user_id INTEGER,
            howtocookathome_user_id INTEGER,

            -- Tracking
            signup_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- GitHub OAuth (optional)
            github_id INTEGER,
            github_username TEXT,
            avatar_url TEXT
        )
    ''')

    # Calendar/timer events table
    db.execute('''
        CREATE TABLE IF NOT EXISTS soulfra_pulse_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_user_id INTEGER REFERENCES soulfra_master_users(id),
            event_type TEXT NOT NULL,  -- 'timer', 'calendar', 'daily_question', 'goal'
            event_data TEXT,  -- JSON data
            source_domain TEXT,  -- Which domain triggered this
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')

    # Cross-domain session tokens
    db.execute('''
        CREATE TABLE IF NOT EXISTS soulfra_session_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_user_id INTEGER REFERENCES soulfra_master_users(id),
            token TEXT UNIQUE NOT NULL,
            current_domain TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    print("✅ Soulfra Master Auth tables created")


@master_auth_bp.route('/api/master/signup', methods=['POST'])
def master_signup():
    """
    Master signup - creates accounts across ALL domains with device binding

    POST /api/master/signup
    {
        "email": "user@example.com",
        "password": "password123",
        "display_name": "Matthew Mauer"  // User's chosen display name
    }

    Returns: JWT token + domain monikers + dual personas
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')
    display_name = data.get('display_name') or data.get('username')  # Backward compat

    if not email or not password or not display_name:
        return jsonify({'error': 'Email, password, and display_name required'}), 400

    db = get_db()

    # Check if email already exists
    existing = db.execute(
        'SELECT id FROM soulfra_master_users WHERE email = ?',
        (email,)
    ).fetchone()

    if existing:
        return jsonify({'error': 'Email already registered'}), 400

    # Generate device fingerprint from request
    user_agent = request.headers.get('User-Agent', 'unknown')
    ip_address = request.remote_addr or 'unknown'
    device_fingerprint = generate_device_fingerprint(user_agent, ip_address)

    # Check if device already registered
    existing_device = db.execute(
        'SELECT id, display_name FROM soulfra_master_users WHERE device_fingerprint = ?',
        (device_fingerprint,)
    ).fetchone()

    if existing_device:
        return jsonify({
            'error': f'Device already registered to account: {existing_device["display_name"]}'
        }), 400

    # Generate dual personas from display name
    persona_data = generate_display_name_personas(display_name, device_fingerprint)
    first_name = persona_data['first_name']
    last_name = persona_data['last_name']
    personas = persona_data['personas']

    # Extract monikers for storage
    monikers = {
        'soulfra.com': personas['neutral'].get('soulfra.com'),
        'deathtodata.com': personas['light'].get('deathtodata.com'),
        'calriven.com': personas['light'].get('calriven.com'),
        'cringeproof.com': personas['shadow'].get('cringeproof.com'),
        'howtocookathome.com': personas['shadow'].get('howtocookathome.com')
    }

    # Use display_name as master_username (unique constraint)
    username = display_name.replace(' ', '_').lower()

    # Hash password
    password_hash = generate_password_hash(password)

    # Create master user with dual persona data
    cursor = db.execute('''
        INSERT INTO soulfra_master_users (
            email,
            password_hash,
            master_username,
            display_name,
            first_name,
            last_name,
            device_fingerprint,
            soulfra_moniker,
            deathtodata_moniker,
            calriven_moniker,
            cringeproof_moniker,
            howtocookathome_moniker
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        email,
        password_hash,
        username,
        display_name,
        first_name,
        last_name,
        device_fingerprint,
        monikers.get('soulfra.com'),
        monikers.get('deathtodata.com'),
        monikers.get('calriven.com'),
        monikers.get('cringeproof.com'),
        monikers.get('howtocookathome.com')
    ))

    master_user_id = cursor.lastrowid

    # Mirror accounts to domain-specific users tables
    domain_user_ids = _mirror_accounts_to_domains(db, master_user_id, email, monikers)

    # Update master user with domain user IDs
    db.execute('''
        UPDATE soulfra_master_users
        SET soulfra_user_id = ?,
            deathtodata_user_id = ?,
            calriven_user_id = ?,
            cringeproof_user_id = ?,
            howtocookathome_user_id = ?
        WHERE id = ?
    ''', (
        domain_user_ids.get('soulfra.com'),
        domain_user_ids.get('deathtodata.com'),
        domain_user_ids.get('calriven.com'),
        domain_user_ids.get('cringeproof.com'),
        domain_user_ids.get('howtocookathome.com'),
        master_user_id
    ))

    db.commit()

    # Generate JWT token
    token = _generate_jwt_token(master_user_id, username, email)

    # Store session token
    _store_session_token(db, master_user_id, token, 'soulfra.com')

    # Set Flask session
    session['master_user_id'] = master_user_id
    session['master_username'] = username
    session['logged_in'] = True

    return jsonify({
        'success': True,
        'token': token,
        'master_user_id': master_user_id,
        'username': username,
        'display_name': display_name,
        'first_name': first_name,
        'last_name': last_name,
        'device_fingerprint': device_fingerprint,
        'email': email,
        'personas': personas,  # Full dual persona data
        'monikers': monikers,
        'domain_accounts': domain_user_ids
    }), 201


@master_auth_bp.route('/api/master/login', methods=['POST'])
def master_login():
    """
    Master login - works across all domains

    POST /api/master/login
    {
        "email": "user@example.com",
        "password": "password123",
        "domain": "soulfra.com"  // optional
    }

    Returns: JWT token
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')
    domain = data.get('domain', 'soulfra.com')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    db = get_db()

    # Get master user
    user = db.execute(
        'SELECT * FROM soulfra_master_users WHERE email = ?',
        (email,)
    ).fetchone()

    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    # Check password
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    master_user_id = user['id']
    username = user['master_username']

    # Update last login
    db.execute(
        'UPDATE soulfra_master_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
        (master_user_id,)
    )
    db.commit()

    # Generate JWT token
    token = _generate_jwt_token(master_user_id, username, email)

    # Store session token
    _store_session_token(db, master_user_id, token, domain)

    # Set Flask session
    session['master_user_id'] = master_user_id
    session['master_username'] = username
    session['current_domain'] = domain
    session['logged_in'] = True

    # Get domain moniker
    moniker_field = domain.replace('.com', '_moniker')
    domain_moniker = dict(user).get(moniker_field, username)

    return jsonify({
        'success': True,
        'token': token,
        'master_user_id': master_user_id,
        'username': username,
        'email': email,
        'current_domain': domain,
        'domain_moniker': domain_moniker
    })


@master_auth_bp.route('/api/master/verify', methods=['POST'])
def verify_token():
    """
    Verify JWT token - called by other domains

    POST /api/master/verify
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "domain": "cringeproof.com"
    }

    Returns: User info if valid
    """
    data = request.json
    token = data.get('token')
    domain = data.get('domain', 'soulfra.com')

    if not token:
        return jsonify({'error': 'Token required'}), 400

    try:
        # Decode JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        master_user_id = payload.get('master_user_id')
        username = payload.get('username')
        email = payload.get('email')

        # Update session last_used
        db = get_db()
        db.execute(
            'UPDATE soulfra_session_tokens SET last_used = CURRENT_TIMESTAMP WHERE token = ?',
            (token,)
        )
        db.commit()

        # Get domain moniker
        user = db.execute(
            'SELECT * FROM soulfra_master_users WHERE id = ?',
            (master_user_id,)
        ).fetchone()

        moniker_field = domain.replace('.com', '_moniker')
        domain_moniker = user.get(moniker_field, username)

        return jsonify({
            'valid': True,
            'master_user_id': master_user_id,
            'username': username,
            'email': email,
            'domain': domain,
            'domain_moniker': domain_moniker
        })

    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401


@master_auth_bp.route('/api/master/me')
def get_master_user():
    """Get current logged-in master user"""
    if not session.get('logged_in'):
        return jsonify({'logged_in': False}), 401

    master_user_id = session.get('master_user_id')

    db = get_db()
    user = db.execute(
        'SELECT * FROM soulfra_master_users WHERE id = ?',
        (master_user_id,)
    ).fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'logged_in': True,
        'master_user_id': user['id'],
        'username': user['master_username'],
        'email': user['email'],
        'monikers': {
            'soulfra.com': user['soulfra_moniker'],
            'deathtodata.com': user['deathtodata_moniker'],
            'calriven.com': user['calriven_moniker'],
            'cringeproof.com': user['cringeproof_moniker'],
            'howtocookathome.com': user['howtocookathome_moniker']
        },
        'created_at': user['created_at'],
        'last_login': user['last_login']
    })


@master_auth_bp.route('/api/master/logout', methods=['POST'])
def master_logout():
    """Logout from all domains"""
    master_user_id = session.get('master_user_id')

    if master_user_id:
        # Expire all session tokens
        db = get_db()
        db.execute(
            'UPDATE soulfra_session_tokens SET expires_at = CURRENT_TIMESTAMP WHERE master_user_id = ?',
            (master_user_id,)
        )
        db.commit()

    session.clear()
    return jsonify({'success': True})


# Helper functions

def _mirror_accounts_to_domains(db, master_user_id, email, monikers):
    """
    Create accounts in domain-specific users tables

    Returns: {domain: user_id} mapping
    """
    domain_user_ids = {}

    # For each domain, insert into users table
    # NOTE: This assumes users table has username, email, password_hash columns
    # and allows NULL password_hash (since master auth handles passwords)

    for domain, moniker in monikers.items():
        try:
            cursor = db.execute('''
                INSERT INTO users (username, email, password_hash, display_name, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (moniker, email, '', domain))

            domain_user_ids[domain] = cursor.lastrowid

        except Exception as e:
            print(f"⚠️  Failed to create {domain} account: {e}")
            domain_user_ids[domain] = None

    return domain_user_ids


def _generate_jwt_token(master_user_id, username, email):
    """Generate JWT token for cross-domain authentication"""
    payload = {
        'master_user_id': master_user_id,
        'username': username,
        'email': email,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def _store_session_token(db, master_user_id, token, domain):
    """Store session token in database"""
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS)

    db.execute('''
        INSERT INTO soulfra_session_tokens (master_user_id, token, current_domain, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (master_user_id, token, domain, expires_at))

    db.commit()


if __name__ == '__main__':
    init_master_auth_tables()
    print("✅ Master auth system initialized")

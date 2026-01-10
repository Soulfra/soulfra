#!/usr/bin/env python3
"""
QR Code Authentication - Passwordless Login System

Scan a QR code → instant login. No password required.

Features:
- Generate secure QR codes for user authentication
- Scan QR code → decode → auto-login
- Expiring tokens (configurable TTL)
- One-time use codes (optional)
- QR code tracking in database

Usage:
    # Generate auth QR code for user
    python3 qr_auth.py --generate --user alice

    # List all auth QR codes
    python3 qr_auth.py --list

    # Verify/decode QR code
    python3 qr_auth.py --verify QR_CODE_DATA

How it works:
1. User requests QR code
2. Generate secure token: user_id + timestamp + random bytes + HMAC signature
3. Encode token in QR code (using stdlib encoder)
4. User scans QR code on another device
5. Decode token → verify HMAC → check expiration → auto-login

Security:
- HMAC signature prevents tampering
- Timestamp prevents replay attacks (TTL)
- Random bytes provide entropy
- One-time use option for extra security
"""

import sqlite3
import hashlib
import secrets
import time
import json
from datetime import datetime, timedelta
import hmac
import base64


# ==============================================================================
# CONFIG
# ==============================================================================

# Secret key for HMAC (in production, store in environment variable)
SECRET_KEY = b"soulfra-qr-auth-secret-key-2025"  # Change this!

# Default token TTL (time to live)
DEFAULT_TTL_SECONDS = 3600  # 1 hour


# ==============================================================================
# TOKEN GENERATION & VERIFICATION
# ==============================================================================

def generate_auth_token(user_id, ttl_seconds=DEFAULT_TTL_SECONDS, one_time=False):
    """
    Generate secure authentication token

    Token format (base64 encoded JSON):
    {
        "user_id": 42,
        "expires_at": 1766425182,
        "nonce": "random_bytes_hex",
        "one_time": true/false,
        "hmac": "signature"
    }

    Args:
        user_id: User ID to authenticate
        ttl_seconds: Token expiration time in seconds
        one_time: If True, token can only be used once

    Returns:
        str: Base64-encoded token
    """
    # Generate token data
    token_data = {
        'user_id': user_id,
        'expires_at': int(time.time()) + ttl_seconds,
        'nonce': secrets.token_hex(16),
        'one_time': one_time
    }

    # Create HMAC signature
    message = json.dumps(token_data, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    token_data['hmac'] = signature

    # Encode as base64
    token_json = json.dumps(token_data, separators=(',', ':'))
    token = base64.urlsafe_b64encode(token_json.encode('utf-8')).decode('utf-8')

    return token


def verify_auth_token(token):
    """
    Verify and decode authentication token

    Args:
        token: Base64-encoded token string

    Returns:
        dict: Decoded token data if valid, None if invalid

    Checks:
    1. Valid base64
    2. Valid JSON
    3. HMAC signature valid
    4. Not expired
    5. Not already used (if one-time)
    """
    try:
        # Decode base64
        token_json = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
        token_data = json.loads(token_json)

        # Extract HMAC
        provided_hmac = token_data.pop('hmac', None)

        if not provided_hmac:
            print("❌ Token missing HMAC signature")
            return None

        # Verify HMAC
        message = json.dumps(token_data, separators=(',', ':')).encode('utf-8')
        expected_hmac = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(provided_hmac, expected_hmac):
            print("❌ Invalid HMAC signature")
            return None

        # Check expiration
        if time.time() > token_data['expires_at']:
            print(f"❌ Token expired at {datetime.fromtimestamp(token_data['expires_at'])}")
            return None

        # Check if already used (one-time tokens)
        if token_data.get('one_time') and token_already_used(token_data['nonce']):
            print("❌ One-time token already used")
            return None

        # Token is valid!
        return token_data

    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        return None


def token_already_used(nonce):
    """Check if one-time token has already been used"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM qr_auth_log
        WHERE nonce = ? AND used = 1
    ''', (nonce,))

    count = cursor.fetchone()[0]
    conn.close()

    return count > 0


def mark_token_used(nonce, user_id):
    """Mark one-time token as used"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO qr_auth_log (nonce, user_id, used_at, used)
        VALUES (?, ?, ?, 1)
    ''', (nonce, user_id, datetime.now().isoformat()))

    conn.commit()
    conn.close()


# ==============================================================================
# DATABASE FUNCTIONS
# ==============================================================================

def init_qr_auth_tables():
    """Create tables for QR authentication if they don't exist"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # QR auth log (tracks token usage)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_auth_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nonce TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            used_at TIMESTAMP,
            used BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # QR auth codes (generated codes for users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_auth_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            one_time BOOLEAN DEFAULT 0,
            times_used INTEGER DEFAULT 0,
            last_used_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ QR auth tables initialized")


def save_qr_auth_code(user_id, token, expires_at, one_time=False):
    """Save generated QR code to database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO qr_auth_codes (user_id, token, created_at, expires_at, one_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        user_id,
        token,
        datetime.now().isoformat(),
        datetime.fromtimestamp(expires_at).isoformat(),
        one_time
    ))

    code_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return code_id


def get_user_qr_codes(user_id):
    """Get all QR codes for user"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM qr_auth_codes
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))

    codes = cursor.fetchall()
    conn.close()

    return [dict(c) for c in codes]


def get_user_by_username(username):
    """Get user by username"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    conn.close()
    return dict(user) if user else None


def increment_qr_usage(token):
    """Increment usage counter for QR code"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE qr_auth_codes
        SET times_used = times_used + 1,
            last_used_at = ?
        WHERE token = ?
    ''', (datetime.now().isoformat(), token))

    conn.commit()
    conn.close()


# ==============================================================================
# QR CODE GENERATION
# ==============================================================================

def generate_qr_for_user(username, ttl_seconds=DEFAULT_TTL_SECONDS, one_time=False, output_file=None):
    """
    Generate QR code for user authentication

    Args:
        username: Username to generate code for
        ttl_seconds: Token expiration in seconds
        one_time: One-time use token
        output_file: Optional file path to save QR image

    Returns:
        dict: {
            'token': token string,
            'qr_url': URL to scan,
            'expires_at': expiration timestamp,
            'qr_image': BMP data (if output_file specified)
        }
    """
    # Get user
    user = get_user_by_username(username)

    if not user:
        print(f"❌ User '{username}' not found")
        return None

    # Generate token
    token = generate_auth_token(user['id'], ttl_seconds=ttl_seconds, one_time=one_time)

    # Build authentication URL
    qr_url = f"http://localhost:5001/qr/auth/{token}"

    # Generate QR code image (using stdlib encoder)
    if output_file:
        from qr_encoder_stdlib import generate_data_matrix

        qr_image = generate_data_matrix(qr_url, size=24, scale=10)

        with open(output_file, 'wb') as f:
            f.write(qr_image)

        print(f"✅ QR code saved to {output_file}")
    else:
        qr_image = None

    # Save to database
    token_data = verify_auth_token(token)  # Decode to get expiration
    code_id = save_qr_auth_code(
        user_id=user['id'],
        token=token,
        expires_at=token_data['expires_at'],
        one_time=one_time
    )

    print(f"✅ Generated QR auth code for {username} (ID: {code_id})")
    print(f"   Token: {token[:50]}...")
    print(f"   URL: {qr_url}")
    print(f"   Expires: {datetime.fromtimestamp(token_data['expires_at'])}")
    print(f"   One-time: {one_time}")

    return {
        'token': token,
        'qr_url': qr_url,
        'expires_at': token_data['expires_at'],
        'qr_image': qr_image,
        'code_id': code_id
    }


def authenticate_with_qr(token):
    """
    Authenticate user with QR code token

    Returns:
        dict: User data if valid, None if invalid
    """
    # Verify token
    token_data = verify_auth_token(token)

    if not token_data:
        return None

    # Get user
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (token_data['user_id'],))
    user = cursor.fetchone()

    conn.close()

    if not user:
        print(f"❌ User {token_data['user_id']} not found")
        return None

    # Mark as used if one-time
    if token_data.get('one_time'):
        mark_token_used(token_data['nonce'], token_data['user_id'])

    # Increment usage counter
    increment_qr_usage(token)

    print(f"✅ Authenticated user: {user['username']}")

    return dict(user)


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='QR Code Authentication System')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--generate', action='store_true', help='Generate QR auth code')
    parser.add_argument('--user', type=str, help='Username for generation')
    parser.add_argument('--ttl', type=int, default=3600, help='Token TTL in seconds')
    parser.add_argument('--one-time', action='store_true', help='One-time use token')
    parser.add_argument('--output', type=str, help='Output file for QR image')
    parser.add_argument('--verify', type=str, help='Verify/decode token')
    parser.add_argument('--list', action='store_true', help='List all QR codes for user')

    args = parser.parse_args()

    # Initialize tables
    if args.init:
        init_qr_auth_tables()
        return

    # Generate QR code
    if args.generate:
        if not args.user:
            print("❌ --user required for generation")
            return

        result = generate_qr_for_user(
            username=args.user,
            ttl_seconds=args.ttl,
            one_time=args.one_time,
            output_file=args.output
        )

        if result:
            print()
            print("="*70)
            print("✅ QR CODE GENERATED")
            print("="*70)
            print(f"User can scan this QR code to login instantly!")
            print(f"Valid for {args.ttl} seconds")

    # Verify token
    elif args.verify:
        print("="*70)
        print("🔍 Verifying QR Token")
        print("="*70)
        print()

        user = authenticate_with_qr(args.verify)

        if user:
            print()
            print("✅ TOKEN VALID")
            print(f"   User: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Display Name: {user['display_name']}")
        else:
            print()
            print("❌ INVALID TOKEN")

    # List codes
    elif args.list:
        if not args.user:
            print("❌ --user required for listing")
            return

        user = get_user_by_username(args.user)

        if not user:
            print(f"❌ User '{args.user}' not found")
            return

        codes = get_user_qr_codes(user['id'])

        print("="*70)
        print(f"QR Auth Codes for {args.user}")
        print("="*70)
        print()

        if not codes:
            print("No QR codes generated yet")
        else:
            for code in codes:
                print(f"ID: {code['id']}")
                print(f"   Created: {code['created_at']}")
                print(f"   Expires: {code['expires_at']}")
                print(f"   Used: {code['times_used']} times")
                print(f"   One-time: {code['one_time']}")
                print()


if __name__ == '__main__':
    main()

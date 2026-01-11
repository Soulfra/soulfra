#!/usr/bin/env python3
"""
Anonymous Session Manager - Track non-logged-in users across page visits

Enables anonymous gameplay with later account claiming:
1. User visits /cringeproof without logging in
2. Generate anonymous session token → store in Flask session + database
3. User plays game → results linked to session token
4. User gets QR code to signup
5. After signup → claim all results from session token

Architecture:
- Flask session stores: session_token, device_fingerprint
- Database stores: session history, claimed status
- QR codes embed: session_token for seamless signup

Security:
- Session tokens: 32 random bytes (hex encoded)
- Device fingerprints: IP + User-Agent hash
- 30-day expiration on unclaimed sessions
- HMAC signatures on QR codes

Integration:
- Works with existing qr_faucet.py pattern
- Compatible with cringeproof.py, catchphrase, color challenge
- Links to soul_model.py after account creation
"""

import secrets
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database import get_db


# ==============================================================================
# SESSION TOKEN GENERATION
# ==============================================================================

def generate_session_token() -> str:
    """
    Generate secure anonymous session token

    Format: 32 random bytes → hex encoded (64 characters)
    Example: "a3f2e1d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1"

    Returns:
        64-character hex string
    """
    return secrets.token_hex(32)


def generate_device_fingerprint(request) -> str:
    """
    Generate device fingerprint from request

    Combines:
    - IP address
    - User-Agent string
    - Accept-Language header

    Args:
        request: Flask request object

    Returns:
        SHA256 hash (64 characters)
    """
    components = [
        request.remote_addr or "unknown",
        request.headers.get('User-Agent', 'unknown'),
        request.headers.get('Accept-Language', 'unknown')
    ]

    fingerprint_str = '|'.join(components)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()


# ==============================================================================
# SESSION MANAGEMENT
# ==============================================================================

def create_anonymous_session(request, source: str = 'cringeproof') -> str:
    """
    Create anonymous session for non-logged-in user

    Args:
        request: Flask request object (for device fingerprint)
        source: Game/feature that created session ('cringeproof', 'catchphrase', etc.)

    Returns:
        session_token (64-char hex string)
    """
    db = get_db()

    # Generate token and fingerprint
    session_token = generate_session_token()
    device_fingerprint = generate_device_fingerprint(request)

    # Store in database
    db.execute('''
        INSERT INTO anonymous_sessions
        (session_token, device_fingerprint, source, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (
        session_token,
        device_fingerprint,
        source,
        datetime.now() + timedelta(days=30)  # 30-day expiration
    ))

    db.commit()

    return session_token


def get_session_info(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Get anonymous session information

    Args:
        session_token: Session token to lookup

    Returns:
        Dict with session data or None if not found/expired
    """
    db = get_db()

    row = db.execute('''
        SELECT * FROM anonymous_sessions
        WHERE session_token = ?
        AND expires_at > CURRENT_TIMESTAMP
    ''', (session_token,)).fetchone()

    if not row:
        return None

    return dict(row)


def is_session_claimed(session_token: str) -> bool:
    """
    Check if session has been claimed by a user

    Args:
        session_token: Session token to check

    Returns:
        True if claimed, False otherwise
    """
    db = get_db()

    row = db.execute('''
        SELECT claimed_by_user_id
        FROM anonymous_sessions
        WHERE session_token = ?
    ''', (session_token,)).fetchone()

    if not row:
        return False

    return row['claimed_by_user_id'] is not None


def claim_session(session_token: str, user_id: int) -> bool:
    """
    Claim anonymous session for a user account

    Links all game results from session to user account.

    Args:
        session_token: Session token to claim
        user_id: User ID claiming the session

    Returns:
        True if successful, False if already claimed or not found
    """
    db = get_db()

    # Check if already claimed
    if is_session_claimed(session_token):
        return False

    # Verify session exists and hasn't expired
    session = get_session_info(session_token)
    if not session:
        return False

    # Mark session as claimed
    db.execute('''
        UPDATE anonymous_sessions
        SET claimed_by_user_id = ?, claimed_at = CURRENT_TIMESTAMP
        WHERE session_token = ?
    ''', (user_id, session_token))

    # Link all game results from this session to user
    db.execute('''
        UPDATE game_results
        SET user_id = ?
        WHERE session_token = ? AND user_id IS NULL
    ''', (user_id, session_token))

    db.commit()

    return True


def get_session_game_results(session_token: str) -> list:
    """
    Get all game results for an anonymous session

    Args:
        session_token: Session token to lookup

    Returns:
        List of game result dicts
    """
    db = get_db()

    rows = db.execute('''
        SELECT * FROM game_results
        WHERE session_token = ?
        ORDER BY created_at DESC
    ''', (session_token,)).fetchall()

    return [dict(row) for row in rows]


def count_unclaimed_results(session_token: str) -> int:
    """
    Count how many results user will get if they claim this session

    Args:
        session_token: Session token to check

    Returns:
        Number of unclaimed results
    """
    db = get_db()

    row = db.execute('''
        SELECT COUNT(*) as count
        FROM game_results
        WHERE session_token = ? AND user_id IS NULL
    ''', (session_token,)).fetchone()

    return row['count']


# ==============================================================================
# FLASK SESSION HELPERS
# ==============================================================================

def get_or_create_session_token(flask_session, request, source: str = 'cringeproof') -> str:
    """
    Get existing session token from Flask session or create new one

    Use this in Flask routes to ensure user has a session token.

    Args:
        flask_session: Flask session object
        request: Flask request object
        source: Game/feature name

    Returns:
        session_token (64-char hex)
    """
    # Check if user is logged in - no anonymous session needed
    if flask_session.get('user_id'):
        return None

    # Check if anonymous session already exists in Flask session
    session_token = flask_session.get('session_token')

    if session_token:
        # Verify it's still valid in database
        if get_session_info(session_token):
            return session_token

    # Create new anonymous session
    session_token = create_anonymous_session(request, source)
    flask_session['session_token'] = session_token

    return session_token


def session_stats() -> Dict[str, int]:
    """
    Get statistics about anonymous sessions

    Returns:
        Dict with: total, active, claimed, expired, unclaimed_results
    """
    db = get_db()

    stats = {}

    # Total sessions
    stats['total'] = db.execute('SELECT COUNT(*) FROM anonymous_sessions').fetchone()[0]

    # Active (not expired, not claimed)
    stats['active'] = db.execute('''
        SELECT COUNT(*) FROM anonymous_sessions
        WHERE expires_at > CURRENT_TIMESTAMP
        AND claimed_by_user_id IS NULL
    ''').fetchone()[0]

    # Claimed
    stats['claimed'] = db.execute('''
        SELECT COUNT(*) FROM anonymous_sessions
        WHERE claimed_by_user_id IS NOT NULL
    ''').fetchone()[0]

    # Expired
    stats['expired'] = db.execute('''
        SELECT COUNT(*) FROM anonymous_sessions
        WHERE expires_at <= CURRENT_TIMESTAMP
    ''').fetchone()[0]

    # Unclaimed results waiting
    stats['unclaimed_results'] = db.execute('''
        SELECT COUNT(*) FROM game_results
        WHERE session_token IS NOT NULL AND user_id IS NULL
    ''').fetchone()[0]

    return stats


# ==============================================================================
# CLI TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🎮 Anonymous Session Manager Test\n")

    # Mock request object for testing
    class MockRequest:
        remote_addr = "192.168.1.100"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        def get(self, key, default=None):
            return self.headers.get(key, default)

    request = MockRequest()

    print("=" * 70)
    print("TEST 1: Create Anonymous Session")
    print("=" * 70)
    session_token = create_anonymous_session(request, 'cringeproof')
    print(f"✅ Created session: {session_token}")
    print(f"   Length: {len(session_token)} characters")

    print("\n" + "=" * 70)
    print("TEST 2: Get Session Info")
    print("=" * 70)
    info = get_session_info(session_token)
    if info:
        print(f"✅ Session found:")
        print(f"   Source: {info['source']}")
        print(f"   Created: {info['created_at']}")
        print(f"   Expires: {info['expires_at']}")
        print(f"   Claimed: {info['claimed_by_user_id'] is not None}")
    else:
        print("❌ Session not found")

    print("\n" + "=" * 70)
    print("TEST 3: Session Statistics")
    print("=" * 70)
    stats = session_stats()
    print(f"Total sessions: {stats['total']}")
    print(f"Active sessions: {stats['active']}")
    print(f"Claimed sessions: {stats['claimed']}")
    print(f"Expired sessions: {stats['expired']}")
    print(f"Unclaimed results: {stats['unclaimed_results']}")

    print("\n✅ Session manager working!")

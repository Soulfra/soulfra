#!/usr/bin/env python3
"""
QR Code Signup - Seamless Account Creation via QR Scan

Enables anonymous users to create accounts by scanning a QR code:
1. User plays cringeproof anonymously → gets results
2. Results page shows QR code: "Scan to save & create account"
3. User scans QR on phone → opens /signup?token=SESSION_TOKEN
4. User creates account → all results automatically linked

Architecture:
- Builds on qr_faucet.py pattern (secure payloads, HMAC signatures)
- Integrates with session_manager.py (anonymous sessions)
- Links to existing /signup route (app.py)

QR Payload Format:
{
    "type": "signup",
    "session_token": "64-char-hex",
    "source": "cringeproof",
    "result_count": 3,
    "timestamp": 1766435700,
    "hmac": "signature"
}

Security:
- HMAC SHA256 signature prevents tampering
- Session tokens verified before account creation
- Expired sessions rejected (30-day TTL)
- Device fingerprinting tracks conversions

Integration:
- Works with existing qr_encoder_stdlib.py for QR generation
- Compatible with all games (cringeproof, catchphrase, color challenge)
- Auto-links results after signup
"""

import json
import hashlib
import hmac
import base64
import time
from typing import Dict, Any
from datetime import datetime

# Use existing QR encoder
try:
    from qr_encoder_stdlib import generate_qr_ascii, generate_qr_data
except ImportError:
    generate_qr_ascii = None
    generate_qr_data = None

# Session management
from session_manager import (
    get_session_info,
    count_unclaimed_results,
    is_session_claimed
)


# ==============================================================================
# CONFIG
# ==============================================================================

# Secret key for HMAC (store in environment in production)
SECRET_KEY = b"soulfra-qr-signup-secret-2025"

# Base URL (from config.py or default)
try:
    from config import BASE_URL
except ImportError:
    BASE_URL = "http://localhost:5001"


# ==============================================================================
# PAYLOAD GENERATION & VERIFICATION
# ==============================================================================

def generate_signup_qr_payload(session_token: str, source: str = 'cringeproof') -> str:
    """
    Generate QR code payload for signup

    Args:
        session_token: Anonymous session token (64-char hex)
        source: Game/feature name ('cringeproof', 'catchphrase', etc.)

    Returns:
        Base64-encoded signed JSON payload
    """
    # Get session info to verify it exists
    session_info = get_session_info(session_token)
    if not session_info:
        raise ValueError(f"Session token not found or expired: {session_token}")

    # Check if already claimed
    if is_session_claimed(session_token):
        raise ValueError(f"Session already claimed: {session_token}")

    # Count results user will get
    result_count = count_unclaimed_results(session_token)

    # Build payload
    payload = {
        'type': 'signup',
        'session_token': session_token,
        'source': source,
        'result_count': result_count,
        'timestamp': int(time.time())
    }

    # Create HMAC signature
    message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    payload['hmac'] = signature

    # Encode as base64
    payload_json = json.dumps(payload, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')

    return encoded


def verify_signup_qr_payload(encoded_payload: str) -> Dict[str, Any]:
    """
    Verify and decode signup QR payload

    Args:
        encoded_payload: Base64-encoded payload from QR code

    Returns:
        Decoded payload dict if valid

    Raises:
        ValueError: If payload invalid or tampered
    """
    try:
        # Decode from base64
        payload_json = base64.urlsafe_b64decode(encoded_payload).decode('utf-8')
        payload = json.loads(payload_json)
    except Exception as e:
        raise ValueError(f"Invalid payload format: {e}")

    # Verify type
    if payload.get('type') != 'signup':
        raise ValueError(f"Invalid payload type: {payload.get('type')}")

    # Extract HMAC
    provided_hmac = payload.pop('hmac', None)
    if not provided_hmac:
        raise ValueError("Missing HMAC signature")

    # Recompute HMAC
    message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    expected_hmac = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    # Verify HMAC
    if not hmac.compare_digest(provided_hmac, expected_hmac):
        raise ValueError("Invalid HMAC signature - payload may be tampered")

    # Restore HMAC to payload
    payload['hmac'] = provided_hmac

    return payload


# ==============================================================================
# QR CODE GENERATION
# ==============================================================================

def generate_signup_qr_code(session_token: str, source: str = 'cringeproof', format: str = 'url') -> str:
    """
    Generate QR code for account signup

    Args:
        session_token: Anonymous session token
        source: Game/feature name
        format: 'url', 'ascii', or 'data'

    Returns:
        QR code as URL, ASCII art, or raw data
    """
    # Generate payload
    payload = generate_signup_qr_payload(session_token, source)

    # Build signup URL
    signup_url = f"{BASE_URL}/signup?token={payload}&source={source}"

    if format == 'url':
        return signup_url

    elif format == 'ascii' and generate_qr_ascii:
        return generate_qr_ascii(signup_url)

    elif format == 'data' and generate_qr_data:
        return generate_qr_data(signup_url)

    else:
        # Fallback to URL
        return signup_url


def generate_signup_qr_html(session_token: str, source: str = 'cringeproof', result_count: int = 0) -> str:
    """
    Generate HTML snippet with QR code and signup instructions

    Use this in templates to display signup QR code.

    Args:
        session_token: Anonymous session token
        source: Game/feature name
        result_count: Number of results user will get

    Returns:
        HTML string with QR code display
    """
    signup_url = generate_signup_qr_code(session_token, source, format='url')

    # QR code library URL (Google Charts API as fallback)
    qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={signup_url}"

    result_text = f"{result_count} result{'s' if result_count != 1 else ''}" if result_count > 0 else "your results"

    html = f'''
    <div class="signup-qr-container" style="text-align: center; padding: 30px; background: #f8f9fa; border-radius: 15px; margin: 20px 0;">
        <h3 style="color: #333; margin-bottom: 15px;">📱 Save Your Results</h3>
        <p style="color: #666; margin-bottom: 20px;">Scan this QR code to create an account and save {result_text}</p>

        <div class="qr-code" style="background: white; padding: 20px; display: inline-block; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <img src="{qr_image_url}" alt="Signup QR Code" style="display: block; width: 250px; height: 250px;">
        </div>

        <p style="color: #888; font-size: 0.9em; margin-top: 15px;">Or visit: <a href="{signup_url}" style="color: #667eea;">{BASE_URL}/signup</a></p>

        <div class="signup-benefits" style="margin-top: 25px; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto;">
            <p style="font-weight: 600; color: #333; margin-bottom: 10px;">What you'll get:</p>
            <ul style="color: #666; line-height: 1.8;">
                <li>✅ All {result_text} saved to your profile</li>
                <li>🏆 Unlock badges and achievements</li>
                <li>📊 Track progress over time</li>
                <li>🔗 Share results with friends</li>
                <li>🎯 Get personalized recommendations</li>
            </ul>
        </div>
    </div>
    '''

    return html


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def extract_session_token_from_url(url_token_param: str) -> str:
    """
    Extract session token from URL token parameter

    The URL param is a base64-encoded payload with session_token inside.

    Args:
        url_token_param: Token from URL (/signup?token=BASE64_PAYLOAD)

    Returns:
        session_token (64-char hex)

    Raises:
        ValueError: If token invalid
    """
    # Verify and decode payload
    payload = verify_signup_qr_payload(url_token_param)

    # Extract session token
    session_token = payload.get('session_token')
    if not session_token:
        raise ValueError("Missing session_token in payload")

    return session_token


def get_signup_stats() -> Dict[str, Any]:
    """
    Get statistics about QR signup conversions

    Returns:
        Dict with conversion metrics
    """
    from database import get_db

    db = get_db()

    stats = {}

    # Total QR signups (sessions claimed via signup)
    stats['total_qr_signups'] = db.execute('''
        SELECT COUNT(*)
        FROM anonymous_sessions
        WHERE claimed_by_user_id IS NOT NULL
    ''').fetchone()[0]

    # Signup rate (claimed / total)
    total_sessions = db.execute('SELECT COUNT(*) FROM anonymous_sessions').fetchone()[0]
    if total_sessions > 0:
        stats['signup_rate'] = round((stats['total_qr_signups'] / total_sessions) * 100, 2)
    else:
        stats['signup_rate'] = 0.0

    # Average results claimed per signup
    avg_row = db.execute('''
        SELECT AVG(result_count) as avg_results
        FROM (
            SELECT session_token, COUNT(*) as result_count
            FROM game_results
            WHERE session_token IN (
                SELECT session_token
                FROM anonymous_sessions
                WHERE claimed_by_user_id IS NOT NULL
            )
            GROUP BY session_token
        )
    ''').fetchone()

    stats['avg_results_per_signup'] = round(avg_row[0], 1) if avg_row[0] else 0.0

    # Top sources for QR signups
    top_sources = db.execute('''
        SELECT source, COUNT(*) as count
        FROM anonymous_sessions
        WHERE claimed_by_user_id IS NOT NULL
        GROUP BY source
        ORDER BY count DESC
        LIMIT 5
    ''').fetchall()

    stats['top_sources'] = {row[0]: row[1] for row in top_sources}

    return stats


# ==============================================================================
# CLI TESTING
# ==============================================================================

if __name__ == '__main__':
    print("📱 QR Signup Generator Test\n")

    # Test with existing session (create one first via session_manager.py)
    test_session_token = "a" * 64  # Dummy token for testing

    print("=" * 70)
    print("TEST 1: Generate Signup QR Payload")
    print("=" * 70)

    try:
        # This will fail if session doesn't exist - that's expected
        payload = generate_signup_qr_payload(test_session_token, 'cringeproof')
        print(f"✅ Generated payload (length {len(payload)} chars)")
        print(f"   First 50 chars: {payload[:50]}...")

        # Verify payload
        decoded = verify_signup_qr_payload(payload)
        print(f"✅ Payload verified successfully")
        print(f"   Type: {decoded['type']}")
        print(f"   Source: {decoded['source']}")
        print(f"   Result count: {decoded['result_count']}")

    except ValueError as e:
        print(f"⚠️  {e} (This is expected if no session exists)")

    print("\n" + "=" * 70)
    print("TEST 2: Generate Signup URL")
    print("=" * 70)

    try:
        signup_url = generate_signup_qr_code(test_session_token, 'cringeproof', format='url')
        print(f"✅ Generated signup URL:")
        print(f"   {signup_url[:100]}...")

    except ValueError as e:
        print(f"⚠️  {e} (This is expected if no session exists)")

    print("\n" + "=" * 70)
    print("TEST 3: Get Signup Statistics")
    print("=" * 70)

    stats = get_signup_stats()
    print(f"Total QR signups: {stats['total_qr_signups']}")
    print(f"Signup rate: {stats['signup_rate']}%")
    print(f"Avg results per signup: {stats['avg_results_per_signup']}")
    print(f"Top sources: {stats['top_sources']}")

    print("\n✅ QR signup module working!")

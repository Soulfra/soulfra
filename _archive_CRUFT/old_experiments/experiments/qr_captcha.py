#!/usr/bin/env python3
"""
QR CAPTCHA - Device Fingerprint Authentication (Zero Dependencies)

Revolutionary CAPTCHA: Scan QR = Prove You're Real

Instead of clicking traffic lights or typing distorted text:
1. Scan QR code with your device
2. Device fingerprint captured (IP + User Agent + Device Type + Scan History)
3. Instant verification - no clicking required!

Philosophy:
----------
Traditional CAPTCHAs are annoying and fail accessibility.
QR-based CAPTCHA is:
- Fast (just scan)
- Accessible (works with any device camera)
- Secure (device fingerprinting harder to fake than cookies)
- Trackable (scan chains prove authenticity)

How It Works:
------------
1. User requests access
2. Generate QR code with challenge
3. User scans QR with their device
4. System captures: IP, user agent, device type, location, previous scans
5. Verify device is unique (not a bot farm)
6. Grant access based on device trust score

Device Trust Score:
------------------
- New device: 0 (require additional verification)
- Seen before: +10 (same IP/user agent previously)
- Scan chain: +5 per previous scan
- Different location: -5 (suspicious)
- Bot-like user agent: -20
- Score > 50: Auto-approve
- Score 20-50: Challenge (require 2nd scan or email)
- Score < 20: Reject (likely bot)

Usage:
    # Generate CAPTCHA QR
    python3 qr_captcha.py --generate --challenge "Prove you're human"

    # Verify scan
    python3 qr_captcha.py --verify SCAN_DATA

    # Check device trust
    python3 qr_captcha.py --trust-score DEVICE_ID
"""

import sqlite3
import json
import hashlib
import secrets
import time
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, List


# ==============================================================================
# CONFIG
# ==============================================================================

SECRET_KEY = b"soulfra-qr-captcha-secret-2025"

# Trust score thresholds
TRUST_SCORE_AUTO_APPROVE = 50
TRUST_SCORE_CHALLENGE = 20
TRUST_SCORE_REJECT = 0

# Device fingerprint blacklist (known bot user agents)
BOT_USER_AGENTS = [
    'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
    'python-requests', 'http', 'headless'
]


# ==============================================================================
# DEVICE FINGERPRINTING
# ==============================================================================

def generate_device_id(ip_address: str, user_agent: str, device_type: str = None) -> str:
    """
    Generate unique device ID from fingerprint

    Args:
        ip_address: IP address
        user_agent: User agent string
        device_type: Device type (mobile, desktop, tablet)

    Returns:
        SHA256 hash of fingerprint
    """
    fingerprint = f"{ip_address}|{user_agent}|{device_type or 'unknown'}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]


def is_bot_user_agent(user_agent: str) -> bool:
    """Check if user agent looks like a bot"""
    if not user_agent:
        return True

    user_agent_lower = user_agent.lower()
    return any(bot in user_agent_lower for bot in BOT_USER_AGENTS)


def calculate_device_trust_score(device_fingerprint: Dict) -> Dict:
    """
    Calculate trust score for device

    Returns:
        {
            "score": 0-100,
            "factors": {
                "previous_scans": +X,
                "bot_user_agent": -X,
                "location_change": -X,
                ...
            },
            "verdict": "approve" | "challenge" | "reject"
        }
    """
    score = 0
    factors = {}

    device_id = generate_device_id(
        device_fingerprint.get('ip_address', ''),
        device_fingerprint.get('user_agent', ''),
        device_fingerprint.get('device_type')
    )

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Factor 1: Previous scans from this device
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM qr_scans
            WHERE ip_address = ? AND user_agent = ?
        ''', (device_fingerprint.get('ip_address'), device_fingerprint.get('user_agent')))

        previous_scans = cursor.fetchone()[0]
        scan_bonus = min(previous_scans * 5, 30)  # Max +30
        score += scan_bonus
        factors['previous_scans'] = f"+{scan_bonus} ({previous_scans} scans)"
    except:
        factors['previous_scans'] = "+0 (no history)"

    # Factor 2: Bot user agent check
    if is_bot_user_agent(device_fingerprint.get('user_agent', '')):
        score -= 20
        factors['bot_user_agent'] = "-20 (suspicious UA)"
    else:
        score += 10
        factors['bot_user_agent'] = "+10 (human-like UA)"

    # Factor 3: Device type known
    if device_fingerprint.get('device_type') in ['mobile', 'desktop', 'tablet']:
        score += 10
        factors['device_type'] = "+10 (known type)"
    else:
        factors['device_type'] = "+0 (unknown type)"

    # Factor 4: Has referrer (came from somewhere legit)
    if device_fingerprint.get('referrer'):
        score += 5
        factors['referrer'] = "+5 (has referrer)"
    else:
        factors['referrer'] = "+0 (no referrer)"

    # Factor 5: Location consistency
    # TODO: Check if location matches previous scans
    # For now, assume consistent
    factors['location'] = "+0 (not checked)"

    conn.close()

    # Determine verdict
    if score >= TRUST_SCORE_AUTO_APPROVE:
        verdict = "approve"
    elif score >= TRUST_SCORE_CHALLENGE:
        verdict = "challenge"
    else:
        verdict = "reject"

    return {
        'score': max(0, min(100, score)),  # Clamp 0-100
        'factors': factors,
        'verdict': verdict,
        'device_id': device_id
    }


# ==============================================================================
# CAPTCHA GENERATION & VERIFICATION
# ==============================================================================

def generate_captcha_qr(challenge_text: str = "Prove you're human", ttl_seconds: int = 300) -> Dict:
    """
    Generate CAPTCHA QR code

    Args:
        challenge_text: Challenge message
        ttl_seconds: Time to live (shorter than auth tokens)

    Returns:
        {
            "challenge_id": ...,
            "qr_data": "...",
            "qr_url": "...",
            "expires_at": ...
        }
    """
    # Generate challenge
    challenge = {
        'challenge_id': secrets.token_hex(16),
        'challenge_text': challenge_text,
        'timestamp': int(time.time()),
        'expires_at': int(time.time()) + ttl_seconds,
        'nonce': secrets.token_hex(8)
    }

    # Sign with HMAC
    message = json.dumps(challenge, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    challenge['hmac'] = signature

    # Encode
    qr_data = base64.urlsafe_b64encode(
        json.dumps(challenge, separators=(',', ':')).encode('utf-8')
    ).decode('utf-8')

    # Save to database
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_captcha_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id TEXT UNIQUE NOT NULL,
            challenge_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            solved_by_device_id TEXT,
            solved_at TIMESTAMP
        )
    ''')

    cursor.execute('''
        INSERT INTO qr_captcha_challenges (challenge_id, challenge_text, expires_at)
        VALUES (?, ?, ?)
    ''', (
        challenge['challenge_id'],
        challenge_text,
        datetime.fromtimestamp(challenge['expires_at']).isoformat()
    ))

    conn.commit()
    conn.close()

    try:
        from config import BASE_URL
    except ImportError:
        BASE_URL = "http://localhost:5001"

    qr_url = f"{BASE_URL}/qr/captcha/{qr_data}"

    print(f"✅ Generated CAPTCHA QR")
    print(f"   Challenge: {challenge_text}")
    print(f"   Expires: {datetime.fromtimestamp(challenge['expires_at'])}")
    print(f"   URL: {qr_url}")

    return {
        'challenge_id': challenge['challenge_id'],
        'qr_data': qr_data,
        'qr_url': qr_url,
        'expires_at': challenge['expires_at']
    }


def verify_captcha_scan(qr_data: str, device_fingerprint: Dict) -> Dict:
    """
    Verify CAPTCHA scan

    Args:
        qr_data: QR code data (base64-encoded challenge)
        device_fingerprint: Device info from scan

    Returns:
        {
            "success": bool,
            "trust_score": {...},
            "verdict": "approve" | "challenge" | "reject",
            "session_token": "..." (if approved)
        }
    """
    try:
        # Decode challenge
        challenge_json = base64.urlsafe_b64decode(qr_data.encode('utf-8')).decode('utf-8')
        challenge = json.loads(challenge_json)

        # Verify HMAC
        provided_hmac = challenge.pop('hmac', None)
        message = json.dumps(challenge, separators=(',', ':')).encode('utf-8')
        expected_hmac = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(provided_hmac or '', expected_hmac):
            print("❌ Invalid HMAC signature")
            return {'success': False, 'error': 'Invalid challenge'}

        # Check expiration
        if time.time() > challenge['expires_at']:
            print("❌ Challenge expired")
            return {'success': False, 'error': 'Challenge expired'}

        # Calculate trust score
        trust_result = calculate_device_trust_score(device_fingerprint)

        print(f"✅ CAPTCHA scanned")
        print(f"   Device trust score: {trust_result['score']}")
        print(f"   Verdict: {trust_result['verdict']}")

        # Mark challenge as solved
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE qr_captcha_challenges
            SET solved_by_device_id = ?,
                solved_at = ?
            WHERE challenge_id = ?
        ''', (
            trust_result['device_id'],
            datetime.now().isoformat(),
            challenge['challenge_id']
        ))

        conn.commit()
        conn.close()

        # Generate session token if approved
        session_token = None
        if trust_result['verdict'] == 'approve':
            session_token = secrets.token_urlsafe(32)

            # Save session
            conn = sqlite3.connect('soulfra.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qr_captcha_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_token TEXT UNIQUE NOT NULL,
                    device_id TEXT NOT NULL,
                    trust_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')

            cursor.execute('''
                INSERT INTO qr_captcha_sessions (session_token, device_id, trust_score, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (
                session_token,
                trust_result['device_id'],
                trust_result['score'],
                (datetime.now() + timedelta(hours=24)).isoformat()
            ))

            conn.commit()
            conn.close()

        return {
            'success': True,
            'trust_score': trust_result,
            'verdict': trust_result['verdict'],
            'session_token': session_token
        }

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return {'success': False, 'error': str(e)}


def check_device_trust(device_fingerprint: Dict) -> Dict:
    """
    Check device trust without challenge

    Args:
        device_fingerprint: Device info

    Returns:
        Trust score result
    """
    return calculate_device_trust_score(device_fingerprint)


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='QR CAPTCHA - Device Fingerprint Auth')
    parser.add_argument('--generate', action='store_true', help='Generate CAPTCHA QR')
    parser.add_argument('--challenge', type=str, default="Prove you're human", help='Challenge text')
    parser.add_argument('--ttl', type=int, default=300, help='Time to live (seconds)')
    parser.add_argument('--verify', type=str, help='Verify CAPTCHA scan')
    parser.add_argument('--trust-score', action='store_true', help='Check device trust')
    parser.add_argument('--ip', type=str, help='IP address for trust check')
    parser.add_argument('--user-agent', type=str, help='User agent for trust check')

    args = parser.parse_args()

    if args.generate:
        result = generate_captcha_qr(args.challenge, args.ttl)

        print()
        print("=" * 70)
        print("✅ CAPTCHA QR GENERATED")
        print("=" * 70)
        print()
        print("Scan this URL to prove you're human:")
        print(result['qr_url'])
        print()
        print("Challenge will expire in", args.ttl, "seconds")

    elif args.verify:
        device_fp = {
            'ip_address': args.ip or '127.0.0.1',
            'user_agent': args.user_agent or 'Test Browser',
            'device_type': 'desktop',
            'referrer': None
        }

        result = verify_captcha_scan(args.verify, device_fp)

        print()
        print("=" * 70)
        print("🔍 CAPTCHA VERIFICATION")
        print("=" * 70)
        print()

        if result['success']:
            print(f"✅ Verdict: {result['verdict'].upper()}")
            print(f"   Trust Score: {result['trust_score']['score']}")
            print()
            print("Factors:")
            for factor, value in result['trust_score']['factors'].items():
                print(f"   • {factor}: {value}")

            if result['session_token']:
                print()
                print(f"✅ Session Token: {result['session_token']}")
        else:
            print(f"❌ Error: {result['error']}")

    elif args.trust_score:
        if not args.ip or not args.user_agent:
            print("❌ --ip and --user-agent required for trust check")
            exit(1)

        device_fp = {
            'ip_address': args.ip,
            'user_agent': args.user_agent,
            'device_type': 'desktop'
        }

        result = check_device_trust(device_fp)

        print("=" * 70)
        print("🔍 DEVICE TRUST SCORE")
        print("=" * 70)
        print()
        print(f"Device ID: {result['device_id']}")
        print(f"Trust Score: {result['score']}")
        print(f"Verdict: {result['verdict'].upper()}")
        print()
        print("Factors:")
        for factor, value in result['factors'].items():
            print(f"   • {factor}: {value}")

    else:
        print("QR CAPTCHA - Device Fingerprint Authentication")
        print()
        print("Usage:")
        print("  --generate --challenge 'Prove you are human'")
        print("  --verify QR_DATA --ip 1.2.3.4 --user-agent 'Mozilla/5.0...'")
        print("  --trust-score --ip 1.2.3.4 --user-agent 'Mozilla/5.0...'")

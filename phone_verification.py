#!/usr/bin/env python3
"""
Phone Verification System - Anti-bot protection for comments

Verification Tiers:
1. Anonymous - No verification (can browse, can't comment)
2. Phone-only - SMS verified (can comment with rate limits)
3. PC + Phone - Device fingerprint + SMS (higher rate limits)
4. Premium - Paid verification ($5/month for permanent badge)

Usage:
    from phone_verification import send_verification_code, verify_code, get_user_tier

Environment Variables:
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_PHONE_NUMBER
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from database import get_db

# Twilio configuration (optional - can use mock for testing)
TWILIO_AVAILABLE = False
try:
    from twilio.rest import Client
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        TWILIO_AVAILABLE = True
except ImportError:
    pass


def hash_phone_number(phone: str) -> str:
    """
    Hash phone number for privacy

    We store hash, not actual number:
    - Can verify same phone again
    - Can't reverse to get actual number
    - Prevents phone number leaks
    """
    # Normalize phone number (remove all non-digits)
    normalized = ''.join(c for c in phone if c.isdigit())

    # Hash with salt
    salt = os.getenv('PHONE_HASH_SALT', 'soulfra-phone-salt-change-in-prod')
    return hashlib.sha256(f"{salt}:{normalized}".encode()).hexdigest()


def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return f"{secrets.randbelow(1000000):06d}"


def send_verification_code(phone: str, user_id: int = None) -> dict:
    """
    Send SMS verification code to phone number

    Returns:
        {
            'success': True/False,
            'code_id': int (for verification),
            'expires_at': timestamp,
            'message': str
        }
    """
    phone_hash = hash_phone_number(phone)
    code = generate_verification_code()
    expires_at = datetime.now() + timedelta(minutes=10)

    db = get_db()

    # Check rate limiting (max 3 codes per hour per phone)
    recent_codes = db.execute('''
        SELECT COUNT(*) as count
        FROM phone_verifications
        WHERE phone_hash = ?
          AND created_at > datetime('now', '-1 hour')
    ''', (phone_hash,)).fetchone()

    if recent_codes['count'] >= 3:
        db.close()
        return {
            'success': False,
            'message': 'Too many verification attempts. Try again in 1 hour.'
        }

    # Store verification code
    cursor = db.execute('''
        INSERT INTO phone_verifications (phone_hash, code, user_id, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (phone_hash, code, user_id, expires_at))

    code_id = cursor.lastrowid
    db.commit()
    db.close()

    # Send SMS (if Twilio available)
    if TWILIO_AVAILABLE:
        try:
            message = twilio_client.messages.create(
                body=f"Your CringeProof verification code: {code}\n\nExpires in 10 minutes.",
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )

            return {
                'success': True,
                'code_id': code_id,
                'expires_at': expires_at.isoformat(),
                'message': 'Verification code sent via SMS',
                'twilio_sid': message.sid
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'SMS failed: {str(e)}'
            }
    else:
        # Mock mode (for testing without Twilio)
        print(f"📱 [MOCK SMS] Code: {code} → {phone}")
        return {
            'success': True,
            'code_id': code_id,
            'expires_at': expires_at.isoformat(),
            'message': 'Verification code generated (mock mode)',
            'mock_code': code  # Only returned in dev mode
        }


def verify_code(phone: str, code: str) -> dict:
    """
    Verify SMS code

    Returns:
        {
            'success': True/False,
            'user_id': int (if exists),
            'phone_hash': str,
            'message': str
        }
    """
    phone_hash = hash_phone_number(phone)

    db = get_db()

    verification = db.execute('''
        SELECT id, user_id, code, expires_at, verified_at
        FROM phone_verifications
        WHERE phone_hash = ?
          AND code = ?
          AND verified_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    ''', (phone_hash, code)).fetchone()

    if not verification:
        db.close()
        return {
            'success': False,
            'message': 'Invalid verification code'
        }

    # Check expiry
    expires_at = datetime.fromisoformat(verification['expires_at'])
    if datetime.now() > expires_at:
        db.close()
        return {
            'success': False,
            'message': 'Verification code expired'
        }

    # Mark as verified
    db.execute('''
        UPDATE phone_verifications
        SET verified_at = datetime('now')
        WHERE id = ?
    ''', (verification['id'],))

    # Update user verification status
    if verification['user_id']:
        db.execute('''
            UPDATE users
            SET phone_verified = 1,
                phone_hash = ?,
                phone_verified_at = datetime('now')
            WHERE id = ?
        ''', (phone_hash, verification['user_id']))

    db.commit()
    db.close()

    return {
        'success': True,
        'user_id': verification['user_id'],
        'phone_hash': phone_hash,
        'message': 'Phone verified successfully'
    }


def get_user_tier(user_id: int, device_fingerprint: str = None) -> dict:
    """
    Get user's verification tier

    Tiers:
    - anonymous: No verification
    - phone: Phone verified
    - pc_phone: Phone + PC fingerprint verified (GOATED)
    - premium: Paid tier

    Returns:
        {
            'tier': str,
            'badge': str (emoji),
            'can_comment': bool,
            'rate_limit': int (comments per hour)
        }
    """
    db = get_db()

    user = db.execute('''
        SELECT phone_verified, device_fingerprint, premium_until
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    db.close()

    if not user:
        return {
            'tier': 'anonymous',
            'badge': '👤',
            'can_comment': False,
            'rate_limit': 0
        }

    # Check premium tier (paid)
    if user['premium_until']:
        premium_until = datetime.fromisoformat(user['premium_until'])
        if datetime.now() < premium_until:
            return {
                'tier': 'premium',
                'badge': '⭐',
                'can_comment': True,
                'rate_limit': 100  # 100 comments/hour
            }

    # Check PC + Phone tier (GOATED)
    if user['phone_verified'] and user['device_fingerprint'] == device_fingerprint:
        return {
            'tier': 'pc_phone',
            'badge': '💻📱',
            'can_comment': True,
            'rate_limit': 50  # 50 comments/hour
        }

    # Check phone-only tier
    if user['phone_verified']:
        return {
            'tier': 'phone',
            'badge': '📱',
            'can_comment': True,
            'rate_limit': 10  # 10 comments/hour
        }

    # Anonymous (default)
    return {
        'tier': 'anonymous',
        'badge': '👤',
        'can_comment': False,
        'rate_limit': 0
    }


def init_phone_verification_tables():
    """Initialize phone verification tables"""
    db = get_db()

    # Phone verifications table
    db.execute('''
        CREATE TABLE IF NOT EXISTS phone_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_hash TEXT NOT NULL,
            code TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            verified_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add phone verification columns to users table (if not exists)
    try:
        db.execute('''
            ALTER TABLE users ADD COLUMN phone_verified INTEGER DEFAULT 0
        ''')
    except:
        pass  # Column already exists

    try:
        db.execute('''
            ALTER TABLE users ADD COLUMN phone_hash TEXT
        ''')
    except:
        pass

    try:
        db.execute('''
            ALTER TABLE users ADD COLUMN phone_verified_at TIMESTAMP
        ''')
    except:
        pass

    try:
        db.execute('''
            ALTER TABLE users ADD COLUMN device_fingerprint TEXT
        ''')
    except:
        pass

    try:
        db.execute('''
            ALTER TABLE users ADD COLUMN premium_until TIMESTAMP
        ''')
    except:
        pass

    db.commit()
    db.close()

    print("✅ Phone verification tables initialized")


if __name__ == '__main__':
    # Initialize tables
    init_phone_verification_tables()

    # Test phone verification flow
    print("\n📱 Testing Phone Verification System...")

    test_phone = "+15551234567"

    # Send code
    result = send_verification_code(test_phone)
    print(f"\n1. Send Code: {result}")

    if result['success'] and 'mock_code' in result:
        # Verify code (mock mode)
        verify_result = verify_code(test_phone, result['mock_code'])
        print(f"\n2. Verify Code: {verify_result}")

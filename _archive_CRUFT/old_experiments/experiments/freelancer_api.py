#!/usr/bin/env python3
"""
Freelancer API - API Key Management for Brand AI Access

Enables freelancers to:
1. Get API keys to access brand AI personas
2. Generate AI comments programmatically
3. Classify text using neural networks
4. Access idea backpropagation system

Tiers:
- Free: 100 calls/day, 1 brand
- Pro: 1000 calls/day, all brands
- Enterprise: Unlimited calls, custom models

Usage:
    # Generate API key
    from freelancer_api import generate_api_key
    api_key = generate_api_key(
        email="freelancer@example.com",
        tier="free",
        brand_slug="calriven"
    )

    # Validate API key
    from freelancer_api import validate_api_key
    is_valid = validate_api_key("ABC-123-XYZ")

    # Track API call (rate limiting)
    from freelancer_api import track_api_call
    allowed = track_api_call("ABC-123-XYZ")
"""

import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from database import get_db


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def create_api_key_tables():
    """Create tables for API key management"""
    conn = get_db()

    # API Keys table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'free',
            brand_slug TEXT,
            rate_limit INTEGER DEFAULT 100,
            calls_today INTEGER DEFAULT 0,
            calls_total INTEGER DEFAULT 0,
            last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_call_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            revoked BOOLEAN DEFAULT 0,
            revoked_at TIMESTAMP,
            revoked_reason TEXT
        )
    ''')

    # API Call Logs table (for analytics)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            brand_slug TEXT,
            request_params TEXT,
            response_status INTEGER,
            response_time_ms INTEGER,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        )
    ''')

    # Indexes
    conn.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_email ON api_keys(user_email)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_api_call_logs_key ON api_call_logs(api_key_id)')

    conn.commit()
    conn.close()

    print("✅ API key tables created!")


# ==============================================================================
# API KEY GENERATION
# ==============================================================================

def generate_random_key() -> str:
    """
    Generate cryptographically secure API key

    Format: SK-XXXXXXXXXXXX (24 characters)

    Returns:
        str: API key
    """
    # Generate 18 random bytes (144 bits)
    random_bytes = secrets.token_bytes(18)

    # Convert to base64-like string (alphanumeric + dash)
    key_part = secrets.token_urlsafe(18)[:24]

    return f"SK-{key_part}"


def generate_api_key(
    email: str,
    tier: str = 'free',
    brand_slug: Optional[str] = None,
    expires_days: Optional[int] = None
) -> Dict:
    """
    Generate API key for a user

    Args:
        email: User's email
        tier: 'free', 'pro', 'enterprise'
        brand_slug: Brand to assign (free tier only)
        expires_days: Days until expiration (None = never)

    Returns:
        {
            'api_key': 'SK-...',
            'tier': 'free',
            'brand_slug': 'calriven',
            'rate_limit': 100,
            'expires_at': '2025-12-31'
        }
    """
    # Set rate limit based on tier
    rate_limits = {
        'free': 100,
        'pro': 1000,
        'enterprise': 999999
    }
    rate_limit = rate_limits.get(tier, 100)

    # Free tier must have brand assigned
    if tier == 'free' and not brand_slug:
        return {
            'success': False,
            'error': 'Free tier requires brand_slug to be specified'
        }

    # Generate unique API key
    api_key = generate_random_key()

    # Calculate expiration
    expires_at = None
    if expires_days:
        expires_at = datetime.now() + timedelta(days=expires_days)

    conn = get_db()

    try:
        conn.execute('''
            INSERT INTO api_keys (
                user_email,
                api_key,
                tier,
                brand_slug,
                rate_limit,
                expires_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, api_key, tier, brand_slug, rate_limit, expires_at))

        conn.commit()

        print(f"✅ Generated API key for {email} ({tier})")

        return {
            'success': True,
            'api_key': api_key,
            'tier': tier,
            'brand_slug': brand_slug,
            'rate_limit': rate_limit,
            'expires_at': expires_at.isoformat() if expires_at else None
        }

    except sqlite3.IntegrityError as e:
        conn.rollback()
        return {
            'success': False,
            'error': f'API key generation failed: {e}'
        }

    finally:
        conn.close()


# ==============================================================================
# API KEY VALIDATION
# ==============================================================================

def validate_api_key(api_key: str) -> Optional[Dict]:
    """
    Validate API key and return key info

    Args:
        api_key: API key to validate

    Returns:
        Dict with key info if valid, None if invalid:
        {
            'id': 1,
            'email': 'user@example.com',
            'tier': 'free',
            'brand_slug': 'calriven',
            'rate_limit': 100,
            'calls_today': 45
        }
    """
    conn = get_db()

    key_info = conn.execute('''
        SELECT * FROM api_keys
        WHERE api_key = ? AND revoked = 0
    ''', (api_key,)).fetchone()

    conn.close()

    if not key_info:
        return None

    key_dict = dict(key_info)

    # Check expiration
    if key_dict['expires_at']:
        expires_at = datetime.fromisoformat(key_dict['expires_at'])
        if datetime.now() > expires_at:
            return None  # Expired

    return key_dict


def check_rate_limit(api_key: str) -> bool:
    """
    Check if API key is within rate limit

    Args:
        api_key: API key to check

    Returns:
        True if within limit, False if exceeded
    """
    key_info = validate_api_key(api_key)

    if not key_info:
        return False

    # Check if we need to reset daily counter
    last_reset = datetime.fromisoformat(key_info['last_reset_at'])
    now = datetime.now()

    # Reset if last reset was yesterday or earlier
    if now.date() > last_reset.date():
        conn = get_db()
        conn.execute('''
            UPDATE api_keys
            SET calls_today = 0, last_reset_at = CURRENT_TIMESTAMP
            WHERE api_key = ?
        ''', (api_key,))
        conn.commit()
        conn.close()
        return True  # Reset, so definitely within limit

    # Check current count
    return key_info['calls_today'] < key_info['rate_limit']


def track_api_call(
    api_key: str,
    endpoint: str,
    brand_slug: Optional[str] = None,
    response_status: int = 200,
    response_time_ms: Optional[int] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Track API call for rate limiting and analytics

    Args:
        api_key: API key making the call
        endpoint: Endpoint called (e.g., '/api/v1/calriven/comment')
        brand_slug: Brand accessed
        response_status: HTTP status code
        response_time_ms: Response time in milliseconds
        error_message: Error message if failed

    Returns:
        True if call was allowed, False if rate limited
    """
    # Check rate limit first
    if not check_rate_limit(api_key):
        return False

    conn = get_db()

    # Get API key ID
    key_row = conn.execute('''
        SELECT id FROM api_keys WHERE api_key = ?
    ''', (api_key,)).fetchone()

    if not key_row:
        conn.close()
        return False

    api_key_id = key_row['id']

    # Increment call count
    conn.execute('''
        UPDATE api_keys
        SET calls_today = calls_today + 1,
            calls_total = calls_total + 1,
            last_call_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (api_key_id,))

    # Log the call
    conn.execute('''
        INSERT INTO api_call_logs (
            api_key_id,
            endpoint,
            brand_slug,
            response_status,
            response_time_ms,
            error_message
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (api_key_id, endpoint, brand_slug, response_status, response_time_ms, error_message))

    conn.commit()
    conn.close()

    return True


# ==============================================================================
# API KEY MANAGEMENT
# ==============================================================================

def revoke_api_key(api_key: str, reason: str = None) -> bool:
    """
    Revoke an API key

    Args:
        api_key: API key to revoke
        reason: Reason for revocation

    Returns:
        True if revoked successfully
    """
    conn = get_db()

    conn.execute('''
        UPDATE api_keys
        SET revoked = 1,
            revoked_at = CURRENT_TIMESTAMP,
            revoked_reason = ?
        WHERE api_key = ?
    ''', (reason, api_key))

    conn.commit()
    rows_affected = conn.total_changes
    conn.close()

    return rows_affected > 0


def get_user_api_keys(email: str) -> List[Dict]:
    """
    Get all API keys for a user

    Args:
        email: User's email

    Returns:
        List of API key info dicts
    """
    conn = get_db()

    keys = conn.execute('''
        SELECT * FROM api_keys
        WHERE user_email = ?
        ORDER BY created_at DESC
    ''', (email,)).fetchall()

    conn.close()

    return [dict(k) for k in keys]


def get_api_stats() -> Dict:
    """
    Get API usage statistics

    Returns:
        {
            'total_keys': 42,
            'active_keys': 35,
            'calls_today': 1234,
            'calls_total': 56789,
            'by_tier': {'free': 30, 'pro': 5}
        }
    """
    conn = get_db()

    # Total keys
    total_keys = conn.execute('''
        SELECT COUNT(*) as count FROM api_keys
    ''').fetchone()['count']

    # Active keys (not revoked, not expired)
    active_keys = conn.execute('''
        SELECT COUNT(*) as count FROM api_keys
        WHERE revoked = 0 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
    ''').fetchone()['count']

    # Calls today
    calls_today = conn.execute('''
        SELECT SUM(calls_today) as total FROM api_keys
    ''').fetchone()['total'] or 0

    # Calls total
    calls_total = conn.execute('''
        SELECT SUM(calls_total) as total FROM api_keys
    ''').fetchone()['total'] or 0

    # By tier
    by_tier = {}
    tier_counts = conn.execute('''
        SELECT tier, COUNT(*) as count FROM api_keys
        WHERE revoked = 0
        GROUP BY tier
    ''').fetchall()

    for row in tier_counts:
        by_tier[row['tier']] = row['count']

    conn.close()

    return {
        'total_keys': total_keys,
        'active_keys': active_keys,
        'calls_today': calls_today,
        'calls_total': calls_total,
        'by_tier': by_tier
    }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Freelancer API Key Management')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--generate', nargs=3, metavar=('EMAIL', 'TIER', 'BRAND'), help='Generate API key')
    parser.add_argument('--validate', metavar='KEY', help='Validate API key')
    parser.add_argument('--revoke', nargs=2, metavar=('KEY', 'REASON'), help='Revoke API key')
    parser.add_argument('--user', metavar='EMAIL', help='List user API keys')
    parser.add_argument('--stats', action='store_true', help='Show API statistics')

    args = parser.parse_args()

    if args.init:
        create_api_key_tables()

    elif args.generate:
        email, tier, brand = args.generate
        result = generate_api_key(email, tier, brand)
        if result['success']:
            print(f"\n✅ API Key Generated:")
            print(f"   Key: {result['api_key']}")
            print(f"   Tier: {result['tier']}")
            print(f"   Brand: {result['brand_slug']}")
            print(f"   Rate Limit: {result['rate_limit']} calls/day")
        else:
            print(f"\n❌ Error: {result['error']}")

    elif args.validate:
        key_info = validate_api_key(args.validate)
        if key_info:
            print(f"\n✅ Valid API Key:")
            print(f"   Email: {key_info['user_email']}")
            print(f"   Tier: {key_info['tier']}")
            print(f"   Brand: {key_info['brand_slug']}")
            print(f"   Calls Today: {key_info['calls_today']}/{key_info['rate_limit']}")
        else:
            print("\n❌ Invalid or expired API key")

    elif args.revoke:
        key, reason = args.revoke
        success = revoke_api_key(key, reason)
        if success:
            print(f"\n✅ API key revoked: {reason}")
        else:
            print("\n❌ API key not found")

    elif args.user:
        keys = get_user_api_keys(args.user)
        print(f"\n📋 API Keys for {args.user}:")
        for key in keys:
            status = "❌ Revoked" if key['revoked'] else "✅ Active"
            print(f"   {status} {key['api_key']} ({key['tier']}) - {key['calls_today']}/{key['rate_limit']} calls")

    elif args.stats:
        stats = get_api_stats()
        print("\n📊 API Statistics:")
        print(f"   Total Keys: {stats['total_keys']}")
        print(f"   Active Keys: {stats['active_keys']}")
        print(f"   Calls Today: {stats['calls_today']:,}")
        print(f"   Calls Total: {stats['calls_total']:,}")
        print(f"   By Tier: {stats['by_tier']}")

    else:
        print("Freelancer API Key Management")
        print()
        print("Usage:")
        print("  --init                           Initialize database")
        print("  --generate EMAIL TIER BRAND      Generate API key")
        print("  --validate KEY                   Validate API key")
        print("  --revoke KEY REASON              Revoke API key")
        print("  --user EMAIL                     List user's API keys")
        print("  --stats                          Show statistics")
        print()
        print("Example:")
        print("  python3 freelancer_api.py --generate freelancer@example.com free calriven")

#!/usr/bin/env python3
"""
Soulfra License & API Key Manager

Handles:
- License generation (Free/Pro/Enterprise tiers)
- API key generation and validation
- Rate limiting based on tier
- Usage tracking

Usage:
    # Generate license for user
    python3 license_manager.py --generate-license --email user@example.com --tier pro

    # Generate API key for existing license
    python3 license_manager.py --generate-api-key --license LICENSE-UUID

    # Validate API key
    python3 license_manager.py --validate-key sk-abc123...

    # Check usage
    python3 license_manager.py --usage --email user@example.com
"""

import argparse
import sqlite3
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import json

# Tier definitions (from soulfra.json)
TIERS = {
    'free': {
        'posts_per_month': 100,
        'brands': 1,
        'api_calls_per_day': 100,
        'neural_networks': 1,
        'subscribers': 100
    },
    'pro': {
        'posts_per_month': -1,  # unlimited
        'brands': 5,
        'api_calls_per_day': 10000,
        'neural_networks': 10,
        'subscribers': 10000
    },
    'enterprise': {
        'posts_per_month': -1,
        'brands': -1,
        'api_calls_per_day': -1,
        'neural_networks': -1,
        'subscribers': -1
    }
}

def init_license_tables():
    """Initialize license and API key tables in database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Licenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            tier TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            metadata TEXT
        )
    """)

    # API keys table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            license_id INTEGER NOT NULL,
            name TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            FOREIGN KEY (license_id) REFERENCES licenses(id)
        )
    """)

    # API usage tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            request_data TEXT,
            response_code INTEGER,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_email ON licenses(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)")

    conn.commit()
    conn.close()

    print("✓ License tables initialized")

def generate_license_key() -> str:
    """Generate UUID-based license key"""
    return str(uuid.uuid4())

def generate_api_key() -> str:
    """Generate secure API key with 'sk-' prefix (like Anthropic/OpenAI)"""
    random_part = secrets.token_urlsafe(48)  # 64 characters base64
    return f"sk-{random_part}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage (security best practice)"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def create_license(email: str, tier: str = 'free', duration_days: int = 365) -> Tuple[str, int]:
    """
    Create a new license for a user

    Args:
        email: User's email address
        tier: License tier (free/pro/enterprise)
        duration_days: License duration in days (365 = 1 year)

    Returns:
        (license_key, license_id)
    """
    if tier not in TIERS:
        raise ValueError(f"Invalid tier: {tier}. Must be one of: {list(TIERS.keys())}")

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if user already has active license
    cursor.execute("""
        SELECT license_key, tier FROM licenses
        WHERE email = ? AND status = 'active'
    """, (email,))
    existing = cursor.fetchone()

    if existing:
        print(f"⚠️  User {email} already has active {existing[1]} license: {existing[0]}")
        conn.close()
        return existing[0], None

    # Generate license
    license_key = generate_license_key()
    expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat()

    metadata = {
        'limits': TIERS[tier],
        'features': get_tier_features(tier)
    }

    cursor.execute("""
        INSERT INTO licenses (license_key, email, tier, expires_at, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, (license_key, email, tier, expires_at, json.dumps(metadata)))

    license_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"✓ License created")
    print(f"  Email: {email}")
    print(f"  Tier: {tier}")
    print(f"  License Key: {license_key}")
    print(f"  Expires: {expires_at[:10]}")

    return license_key, license_id

def create_api_key(license_key: str, name: str = None) -> str:
    """
    Generate API key for a license

    Args:
        license_key: License UUID
        name: Optional name for the API key (e.g., "Production", "Testing")

    Returns:
        api_key (plaintext - only shown once!)
    """
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Verify license exists and is active
    cursor.execute("""
        SELECT id, email, tier, status, expires_at FROM licenses
        WHERE license_key = ?
    """, (license_key,))
    license = cursor.fetchone()

    if not license:
        conn.close()
        raise ValueError(f"License not found: {license_key}")

    license_id, email, tier, status, expires_at = license

    if status != 'active':
        conn.close()
        raise ValueError(f"License is not active: {status}")

    # Check if expired
    if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
        conn.close()
        raise ValueError(f"License expired: {expires_at}")

    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    cursor.execute("""
        INSERT INTO api_keys (api_key, license_id, name)
        VALUES (?, ?, ?)
    """, (api_key_hash, license_id, name or f"API Key {datetime.now().strftime('%Y-%m-%d')}"))

    conn.commit()
    conn.close()

    print(f"✓ API key created for {email} ({tier})")
    print(f"  Key: {api_key}")
    print(f"  Name: {name or 'Default'}")
    print(f"\n⚠️  Save this key - it won't be shown again!")

    return api_key

def validate_api_key(api_key: str) -> Optional[Dict]:
    """
    Validate API key and return license info

    Args:
        api_key: API key to validate

    Returns:
        Dict with license info if valid, None otherwise
    """
    if not api_key.startswith('sk-'):
        return None

    api_key_hash = hash_api_key(api_key)

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            l.license_key,
            l.email,
            l.tier,
            l.status,
            l.expires_at,
            l.metadata,
            k.id as api_key_id,
            k.name as api_key_name
        FROM api_keys k
        JOIN licenses l ON k.license_id = l.id
        WHERE k.api_key = ? AND k.status = 'active'
    """, (api_key_hash,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    license_key, email, tier, status, expires_at, metadata, api_key_id, api_key_name = result

    # Check license status
    if status != 'active':
        conn.close()
        return None

    # Check expiration
    if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
        conn.close()
        return None

    # Update last_used_at
    cursor.execute("""
        UPDATE api_keys
        SET last_used_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (api_key_id,))
    conn.commit()
    conn.close()

    return {
        'valid': True,
        'license_key': license_key,
        'email': email,
        'tier': tier,
        'api_key_id': api_key_id,
        'api_key_name': api_key_name,
        'limits': json.loads(metadata)['limits'] if metadata else TIERS[tier]
    }

def check_rate_limit(api_key_id: int, endpoint: str) -> Tuple[bool, int, int]:
    """
    Check if API key has exceeded rate limit

    Args:
        api_key_id: API key ID from database
        endpoint: API endpoint being called

    Returns:
        (allowed, current_count, limit)
    """
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get tier limits
    cursor.execute("""
        SELECT l.tier, l.metadata
        FROM api_keys k
        JOIN licenses l ON k.license_id = l.id
        WHERE k.id = ?
    """, (api_key_id,))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return False, 0, 0

    tier, metadata = result
    limits = json.loads(metadata)['limits'] if metadata else TIERS[tier]
    daily_limit = limits['api_calls_per_day']

    # Unlimited for enterprise
    if daily_limit == -1:
        conn.close()
        return True, 0, -1

    # Count calls in last 24 hours
    cursor.execute("""
        SELECT COUNT(*) FROM api_usage
        WHERE api_key_id = ?
        AND timestamp >= datetime('now', '-1 day')
    """, (api_key_id,))

    current_count = cursor.fetchone()[0]
    conn.close()

    allowed = current_count < daily_limit

    return allowed, current_count, daily_limit

def log_api_usage(api_key_id: int, endpoint: str, request_data: str = None, response_code: int = 200):
    """Log API usage for analytics and billing"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO api_usage (api_key_id, endpoint, request_data, response_code)
        VALUES (?, ?, ?, ?)
    """, (api_key_id, endpoint, request_data, response_code))

    conn.commit()
    conn.close()

def get_usage_stats(email: str) -> Dict:
    """Get usage statistics for a user"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get license info
    cursor.execute("""
        SELECT l.id, l.license_key, l.tier, l.created_at, l.expires_at
        FROM licenses l
        WHERE l.email = ? AND l.status = 'active'
    """, (email,))

    license = cursor.fetchone()
    if not license:
        conn.close()
        return None

    license_id, license_key, tier, created_at, expires_at = license

    # Get API usage stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_calls,
            COUNT(CASE WHEN timestamp >= datetime('now', '-1 day') THEN 1 END) as calls_today,
            COUNT(CASE WHEN timestamp >= datetime('now', '-1 month') THEN 1 END) as calls_this_month
        FROM api_usage u
        JOIN api_keys k ON u.api_key_id = k.id
        WHERE k.license_id = ?
    """, (license_id,))

    usage = cursor.fetchone()
    total_calls, calls_today, calls_this_month = usage

    conn.close()

    return {
        'email': email,
        'tier': tier,
        'license_key': license_key,
        'created_at': created_at,
        'expires_at': expires_at,
        'usage': {
            'total_calls': total_calls,
            'calls_today': calls_today,
            'calls_this_month': calls_this_month
        },
        'limits': TIERS[tier]
    }

def get_tier_features(tier: str) -> list:
    """Get features included in a tier"""
    features_map = {
        'free': ['basic_blogging', 'single_brand', 'manual_posts'],
        'pro': ['unlimited_posts', 'multi_brand', 'claude_generation', 'batch_import', 'email_newsletters', 'custom_domain', 'api_access'],
        'enterprise': ['everything_in_pro', 'white_label', 'priority_support', 'custom_integrations', 'dedicated_hosting', 'sla_guarantee']
    }
    return features_map.get(tier, [])

def main():
    parser = argparse.ArgumentParser(description="Soulfra License & API Key Manager")
    parser.add_argument('--init', action='store_true', help='Initialize license tables')
    parser.add_argument('--generate-license', action='store_true', help='Generate new license')
    parser.add_argument('--generate-api-key', action='store_true', help='Generate API key for license')
    parser.add_argument('--validate-key', help='Validate an API key')
    parser.add_argument('--usage', action='store_true', help='Show usage statistics')
    parser.add_argument('--email', help='User email')
    parser.add_argument('--tier', default='free', choices=['free', 'pro', 'enterprise'], help='License tier')
    parser.add_argument('--license', help='License key')
    parser.add_argument('--name', help='API key name')

    args = parser.parse_args()

    if args.init:
        init_license_tables()

    elif args.generate_license:
        if not args.email:
            print("❌ --email required")
            return 1
        create_license(args.email, args.tier)

    elif args.generate_api_key:
        if not args.license:
            print("❌ --license required")
            return 1
        create_api_key(args.license, args.name)

    elif args.validate_key:
        result = validate_api_key(args.validate_key)
        if result:
            print("✓ Valid API key")
            print(f"  Email: {result['email']}")
            print(f"  Tier: {result['tier']}")
            print(f"  Limits: {result['limits']}")
        else:
            print("❌ Invalid API key")

    elif args.usage:
        if not args.email:
            print("❌ --email required")
            return 1
        stats = get_usage_stats(args.email)
        if stats:
            print(f"\nUsage Statistics for {stats['email']}")
            print(f"{'='*60}")
            print(f"Tier: {stats['tier']}")
            print(f"License Key: {stats['license_key']}")
            print(f"Created: {stats['created_at'][:10]}")
            print(f"Expires: {stats['expires_at'][:10] if stats['expires_at'] else 'Never'}")
            print(f"\nAPI Usage:")
            print(f"  Today: {stats['usage']['calls_today']} / {stats['limits']['api_calls_per_day']}")
            print(f"  This Month: {stats['usage']['calls_this_month']}")
            print(f"  All Time: {stats['usage']['total_calls']}")
        else:
            print(f"❌ No active license found for {args.email}")

    else:
        parser.print_help()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

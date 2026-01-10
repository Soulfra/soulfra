#!/usr/bin/env python3
"""
Keyring Unlock System - Runescape-Style Permanent Feature Unlocks

Like the Runescape keyring: once you unlock a feature, it stays unlocked permanently.
Similar to Stripe subscriptions but with permanent feature access.

Features can be unlocked by:
- Completing quizzes
- Achievements
- One-time payments
- Admin grants

Usage:
    from keyring_unlocks import unlock_feature, has_unlocked, get_user_unlocks

    # Unlock a feature
    unlock_feature(user_id=1, feature_key='premium_tier')

    # Check if unlocked
    if has_unlocked(user_id=1, feature_key='calriven_api'):
        # User has access to CalRiven API

    # Get all unlocks
    unlocks = get_user_unlocks(user_id=1)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import get_db


# =============================================================================
# Feature Keys (What Can Be Unlocked)
# =============================================================================

FEATURES = {
    # Tier unlocks
    'premium_tier': {
        'name': 'Premium Tier',
        'description': 'Access to premium features',
        'category': 'tier'
    },
    'pro_tier': {
        'name': 'Pro Tier',
        'description': 'Access to all features',
        'category': 'tier'
    },

    # AI/Brand access
    'calriven_api': {
        'name': 'CalRiven AI API',
        'description': 'Access to CalRiven AI marketplace',
        'category': 'ai'
    },
    'soulfra_ai': {
        'name': 'Soulfra AI Friend',
        'description': 'Your AI companion from quiz completion',
        'category': 'ai'
    },
    'deathtodata_encryption': {
        'name': 'DeathToData Encryption',
        'description': 'End-to-end encryption features',
        'category': 'encryption'
    },

    # Quiz/Personality
    'personality_profile': {
        'name': 'Personality Profile',
        'description': 'Completed personality quiz',
        'category': 'profile'
    },

    # Email/Communication
    'custom_email': {
        'name': 'Custom Email Address',
        'description': 'yourname@soulfra.com email alias',
        'category': 'communication'
    },

    # Developer features
    'api_access': {
        'name': 'API Access',
        'description': 'REST API access with API key',
        'category': 'developer'
    },
    'webhook_integration': {
        'name': 'Webhook Integration',
        'description': 'Custom webhook callbacks',
        'category': 'developer'
    },
}


# =============================================================================
# Database Schema
# =============================================================================

def init_keyring_table():
    """Create user_unlocks table (Runescape keyring style)"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS user_unlocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feature_key TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL,
            unlock_source TEXT,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, feature_key)
        )
    ''')

    # Index for fast lookups
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_unlocks_user
        ON user_unlocks(user_id)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_unlocks_feature
        ON user_unlocks(feature_key)
    ''')

    db.commit()
    db.close()
    print("✅ Keyring unlocks table initialized")


# =============================================================================
# Core Functions
# =============================================================================

def unlock_feature(user_id: int, feature_key: str, source: str = 'manual',
                  expires_at: Optional[datetime] = None, metadata: Optional[str] = None) -> bool:
    """
    Unlock a feature for a user (Runescape keyring style)

    Args:
        user_id: User ID
        feature_key: Feature to unlock (e.g., 'premium_tier')
        source: How it was unlocked ('quiz', 'payment', 'admin', 'achievement')
        expires_at: Optional expiration (None = permanent)
        metadata: Optional JSON metadata

    Returns:
        True if unlocked, False if already unlocked
    """
    if feature_key not in FEATURES:
        print(f"⚠️  Unknown feature: {feature_key}")
        return False

    db = get_db()

    try:
        db.execute('''
            INSERT OR IGNORE INTO user_unlocks
            (user_id, feature_key, unlocked_at, expires_at, unlock_source, metadata)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
        ''', (user_id, feature_key, expires_at, source, metadata))

        db.commit()

        if db.total_changes > 0:
            print(f"🔓 Unlocked '{feature_key}' for user {user_id} (source: {source})")
            return True
        else:
            print(f"ℹ️  User {user_id} already has '{feature_key}' unlocked")
            return False

    except Exception as e:
        print(f"❌ Error unlocking feature: {e}")
        return False
    finally:
        db.close()


def has_unlocked(user_id: int, feature_key: str) -> bool:
    """
    Check if user has unlocked a feature

    Args:
        user_id: User ID
        feature_key: Feature to check

    Returns:
        True if unlocked and not expired
    """
    db = get_db()

    unlock = db.execute('''
        SELECT id, expires_at FROM user_unlocks
        WHERE user_id = ? AND feature_key = ?
    ''', (user_id, feature_key)).fetchone()

    db.close()

    if not unlock:
        return False

    # Check if expired (if expires_at is set)
    if unlock['expires_at']:
        expires = datetime.fromisoformat(unlock['expires_at'])
        if datetime.now() > expires:
            return False

    return True


def get_user_unlocks(user_id: int, include_expired: bool = False) -> List[Dict]:
    """
    Get all features unlocked by a user

    Args:
        user_id: User ID
        include_expired: Include expired unlocks

    Returns:
        List of unlock dicts with feature info
    """
    db = get_db()

    unlocks = db.execute('''
        SELECT feature_key, unlocked_at, expires_at, unlock_source, metadata
        FROM user_unlocks
        WHERE user_id = ?
        ORDER BY unlocked_at DESC
    ''', (user_id,)).fetchall()

    db.close()

    result = []
    for unlock in unlocks:
        feature_key = unlock['feature_key']

        # Check if expired
        is_expired = False
        if unlock['expires_at']:
            expires = datetime.fromisoformat(unlock['expires_at'])
            if datetime.now() > expires:
                is_expired = True

        if is_expired and not include_expired:
            continue

        feature_info = FEATURES.get(feature_key, {
            'name': feature_key,
            'description': 'Unknown feature',
            'category': 'unknown'
        })

        result.append({
            'feature_key': feature_key,
            'name': feature_info['name'],
            'description': feature_info['description'],
            'category': feature_info['category'],
            'unlocked_at': unlock['unlocked_at'],
            'expires_at': unlock['expires_at'],
            'unlock_source': unlock['unlock_source'],
            'is_expired': is_expired,
            'is_permanent': unlock['expires_at'] is None
        })

    return result


def revoke_unlock(user_id: int, feature_key: str) -> bool:
    """
    Revoke an unlock (admin only)

    Args:
        user_id: User ID
        feature_key: Feature to revoke

    Returns:
        True if revoked
    """
    db = get_db()

    db.execute('''
        DELETE FROM user_unlocks
        WHERE user_id = ? AND feature_key = ?
    ''', (user_id, feature_key))

    db.commit()
    success = db.total_changes > 0
    db.close()

    if success:
        print(f"🔒 Revoked '{feature_key}' from user {user_id}")

    return success


# =============================================================================
# Helper Functions
# =============================================================================

def unlock_quiz_completion(user_id: int, ai_friend_slug: str):
    """Unlock features when user completes personality quiz"""
    unlock_feature(user_id, 'personality_profile', source='quiz')
    unlock_feature(user_id, 'soulfra_ai', source='quiz',
                  metadata=f'{{"ai_friend": "{ai_friend_slug}"}}')
    print(f"🎯 Quiz completion unlocks granted to user {user_id}")


def unlock_tier_upgrade(user_id: int, tier: str, payment_id: str = None):
    """Unlock features when user upgrades tier"""
    if tier == 'premium':
        unlock_feature(user_id, 'premium_tier', source='payment',
                      metadata=f'{{"payment_id": "{payment_id}"}}' if payment_id else None)
        unlock_feature(user_id, 'custom_email', source='payment')
        unlock_feature(user_id, 'api_access', source='payment')

    elif tier == 'pro':
        unlock_feature(user_id, 'pro_tier', source='payment',
                      metadata=f'{{"payment_id": "{payment_id}"}}' if payment_id else None)
        unlock_feature(user_id, 'custom_email', source='payment')
        unlock_feature(user_id, 'api_access', source='payment')
        unlock_feature(user_id, 'webhook_integration', source='payment')
        unlock_feature(user_id, 'calriven_api', source='payment')
        unlock_feature(user_id, 'deathtodata_encryption', source='payment')

    print(f"💎 Tier '{tier}' unlocks granted to user {user_id}")


# =============================================================================
# Testing
# =============================================================================

if __name__ == '__main__':
    print("\n🔐 Keyring Unlock System - Runescape Style\n")
    print("=" * 70)

    # Initialize table
    init_keyring_table()

    # Test unlocks
    print("\n🧪 Testing unlocks...\n")

    user_id = 1

    # Unlock quiz completion
    unlock_quiz_completion(user_id, 'soulfra')

    # Unlock premium tier
    unlock_tier_upgrade(user_id, 'premium', payment_id='test_123')

    # Check unlocks
    print(f"\n📋 User {user_id} unlocks:")
    unlocks = get_user_unlocks(user_id)

    for unlock in unlocks:
        permanent = "🔒 PERMANENT" if unlock['is_permanent'] else f"⏰ Expires: {unlock['expires_at']}"
        print(f"  ✅ {unlock['name']} ({unlock['category']}) - {permanent}")
        print(f"     Source: {unlock['unlock_source']}")

    # Check specific feature
    print(f"\n🔍 Checking specific features:")
    print(f"  Has 'premium_tier': {has_unlocked(user_id, 'premium_tier')}")
    print(f"  Has 'pro_tier': {has_unlocked(user_id, 'pro_tier')}")
    print(f"  Has 'calriven_api': {has_unlocked(user_id, 'calriven_api')}")

    print("\n" + "=" * 70)
    print("✅ Keyring system working!\n")

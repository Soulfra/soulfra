#!/usr/bin/env python3
"""
Stripe Membership System

Handles Stripe subscriptions for D&D campaign access.
NO crypto/blockchain - just standard Stripe payments.

Membership Tiers:
- Free: 10 item inventory limit, 1 trade/day
- Premium ($5/mo): Unlimited inventory, 10 trades/day
- Pro ($10/mo): Everything + exclusive quests + priority support

Usage:
    from stripe_membership import (
        get_membership_tier,
        create_checkout_session,
        handle_webhook
    )
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

# Stripe will be imported when needed (not required for dev/testing)
STRIPE_ENABLED = os.environ.get('STRIPE_ENABLED', 'false').lower() == 'true'
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

if STRIPE_ENABLED:
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
    except ImportError:
        print("⚠️  Stripe not installed. Run: pip install stripe")
        STRIPE_ENABLED = False


# Membership tier configuration
TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'inventory_limit': 10,
        'trades_per_day': 1,
        'quests_available': 'basic',
        'features': [
            '✅ Play D&D campaign',
            '✅ Earn items through gameplay',
            '✅ Up to 10 items in inventory',
            '✅ 1 trade per day'
        ]
    },
    'premium': {
        'name': 'Premium',
        'price': 5.00,  # USD per month
        'stripe_price_id': 'price_premium_monthly',  # Set in Stripe dashboard
        'inventory_limit': None,  # Unlimited
        'trades_per_day': 10,
        'quests_available': 'all',
        'features': [
            '✅ Everything in Free',
            '✅ Unlimited inventory',
            '✅ 10 trades per day',
            '✅ Access to all quests',
            '✅ Exclusive items'
        ]
    },
    'pro': {
        'name': 'Pro',
        'price': 10.00,  # USD per month
        'stripe_price_id': 'price_pro_monthly',  # Set in Stripe dashboard
        'inventory_limit': None,  # Unlimited
        'trades_per_day': None,  # Unlimited
        'quests_available': 'all_plus_exclusive',
        'features': [
            '✅ Everything in Premium',
            '✅ Unlimited trades',
            '✅ Exclusive Pro quests',
            '✅ Priority support',
            '✅ Special cosmetics',
            '✅ Early access to new content'
        ]
    }
}


def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_membership(user_id: int) -> Dict:
    """
    Get user's membership details

    Returns:
        Dict with tier, status, features, limits
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM memberships WHERE user_id = ?
    ''', (user_id,))

    membership = cursor.fetchone()
    conn.close()

    if not membership:
        # Create free membership if doesn't exist
        return create_free_membership(user_id)

    # Convert to dict
    membership_dict = dict(membership)
    tier = membership_dict['tier']

    # Add tier config
    tier_config = TIERS.get(tier, TIERS['free'])
    membership_dict['config'] = tier_config

    # Check if expired
    if membership_dict['status'] == 'active' and membership_dict['current_period_end']:
        period_end = datetime.fromisoformat(membership_dict['current_period_end'])
        if datetime.now() > period_end:
            # Subscription expired
            downgrade_to_free(user_id)
            membership_dict['tier'] = 'free'
            membership_dict['status'] = 'expired'
            membership_dict['config'] = TIERS['free']

    return membership_dict


def create_free_membership(user_id: int) -> Dict:
    """Create free tier membership for user"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO memberships (user_id, tier, status)
        VALUES (?, 'free', 'active')
    ''', (user_id,))

    conn.commit()
    conn.close()

    return {
        'user_id': user_id,
        'tier': 'free',
        'status': 'active',
        'config': TIERS['free']
    }


def can_trade_today(user_id: int) -> bool:
    """Check if user can trade today (based on tier limits)"""
    membership = get_membership(user_id)
    trades_per_day = membership['config']['trades_per_day']

    if trades_per_day is None:
        return True  # Unlimited

    # Check trade count today
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT trades_today, last_trade_date FROM trade_limits
        WHERE user_id = ?
    ''', (user_id,))

    limits = cursor.fetchone()

    if not limits:
        # First trade ever
        cursor.execute('''
            INSERT INTO trade_limits (user_id, trades_today, last_trade_date)
            VALUES (?, 0, DATE('now'))
        ''', (user_id,))
        conn.commit()
        conn.close()
        return True

    trades_today = limits['trades_today']
    last_trade_date = limits['last_trade_date']

    # Reset if new day
    if last_trade_date != datetime.now().strftime('%Y-%m-%d'):
        cursor.execute('''
            UPDATE trade_limits
            SET trades_today = 0, last_trade_date = DATE('now')
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        trades_today = 0

    conn.close()
    return trades_today < trades_per_day


def increment_trade_count(user_id: int):
    """Increment user's trade count for today"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO trade_limits (user_id, trades_today, last_trade_date)
        VALUES (?, 1, DATE('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            trades_today = trades_today + 1,
            last_trade_date = DATE('now')
    ''', (user_id,))

    conn.commit()
    conn.close()


def can_hold_more_items(user_id: int) -> bool:
    """Check if user can hold more items (inventory limit)"""
    membership = get_membership(user_id)
    inventory_limit = membership['config']['inventory_limit']

    if inventory_limit is None:
        return True  # Unlimited

    # Count current items
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT SUM(quantity) as total FROM inventory
        WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    total_items = result['total'] if result['total'] else 0
    return total_items < inventory_limit


def create_checkout_session(user_id: int, tier: str, success_url: str, cancel_url: str) -> Optional[str]:
    """
    Create Stripe checkout session for membership upgrade

    Returns:
        Checkout session URL or None if Stripe disabled
    """
    if not STRIPE_ENABLED:
        print("⚠️  Stripe not enabled. Set STRIPE_ENABLED=true in environment.")
        return None

    if tier not in ['premium', 'pro']:
        return None

    tier_config = TIERS[tier]
    price_id = tier_config['stripe_price_id']

    # Get or create Stripe customer
    customer_id = get_or_create_stripe_customer(user_id)

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': user_id,
                'tier': tier
            }
        )

        return session.url

    except Exception as e:
        print(f"❌ Stripe checkout error: {e}")
        return None


def get_or_create_stripe_customer(user_id: int) -> Optional[str]:
    """Get existing Stripe customer ID or create new one"""
    if not STRIPE_ENABLED:
        return None

    conn = get_db()
    cursor = conn.cursor()

    # Check if customer already exists
    cursor.execute('''
        SELECT stripe_customer_id FROM memberships WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()

    if result and result['stripe_customer_id']:
        conn.close()
        return result['stripe_customer_id']

    # Create new Stripe customer
    cursor.execute('''
        SELECT email, username FROM users WHERE id = ?
    ''', (user_id,))

    user = cursor.fetchone()

    if not user:
        conn.close()
        return None

    try:
        customer = stripe.Customer.create(
            email=user['email'],
            name=user['username'],
            metadata={'user_id': user_id}
        )

        # Save customer ID
        cursor.execute('''
            UPDATE memberships
            SET stripe_customer_id = ?
            WHERE user_id = ?
        ''', (customer.id, user_id))

        conn.commit()
        conn.close()

        return customer.id

    except Exception as e:
        print(f"❌ Stripe customer creation error: {e}")
        conn.close()
        return None


def handle_webhook(payload: bytes, sig_header: str) -> Dict:
    """
    Handle Stripe webhook events

    Events handled:
    - checkout.session.completed: Upgrade membership
    - customer.subscription.updated: Update subscription status
    - customer.subscription.deleted: Downgrade to free
    """
    if not STRIPE_ENABLED or not STRIPE_WEBHOOK_SECRET:
        return {'success': False, 'error': 'Stripe webhooks not configured'}

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return {'success': False, 'error': 'Invalid payload'}
    except stripe.error.SignatureVerificationError:
        return {'success': False, 'error': 'Invalid signature'}

    # Handle event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)

    return {'success': True}


def handle_checkout_completed(session):
    """Upgrade user's membership after successful checkout"""
    user_id = int(session['metadata']['user_id'])
    tier = session['metadata']['tier']
    subscription_id = session['subscription']

    conn = get_db()
    cursor = conn.cursor()

    # Get subscription details from Stripe
    if STRIPE_ENABLED:
        subscription = stripe.Subscription.retrieve(subscription_id)
        current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
    else:
        current_period_end = datetime.now() + timedelta(days=30)

    cursor.execute('''
        UPDATE memberships
        SET tier = ?,
            status = 'active',
            stripe_subscription_id = ?,
            current_period_end = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (tier, subscription_id, current_period_end.isoformat(), user_id))

    conn.commit()
    conn.close()

    print(f"✅ User {user_id} upgraded to {tier}")


def handle_subscription_updated(subscription):
    """Handle subscription updates (renewal, changes)"""
    customer_id = subscription['customer']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id FROM memberships WHERE stripe_customer_id = ?
    ''', (customer_id,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return

    user_id = result['user_id']
    current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
    status = subscription['status']  # active, past_due, canceled, etc.

    cursor.execute('''
        UPDATE memberships
        SET current_period_end = ?,
            status = ?,
            cancel_at_period_end = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (current_period_end.isoformat(), status, subscription['cancel_at_period_end'], user_id))

    conn.commit()
    conn.close()


def handle_subscription_cancelled(subscription):
    """Downgrade user to free tier when subscription cancelled"""
    customer_id = subscription['customer']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id FROM memberships WHERE stripe_customer_id = ?
    ''', (customer_id,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return

    user_id = result['user_id']
    downgrade_to_free(user_id)


def downgrade_to_free(user_id: int):
    """Downgrade user to free tier"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE memberships
        SET tier = 'free',
            status = 'cancelled',
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))

    conn.commit()
    conn.close()

    print(f"⬇️  User {user_id} downgraded to free tier")


# ==================== TESTING HELPERS ====================

def simulate_upgrade(user_id: int, tier: str):
    """
    Simulate membership upgrade for testing (NO Stripe required)

    Use this in development to test premium features without Stripe
    """
    conn = get_db()
    cursor = conn.cursor()

    current_period_end = datetime.now() + timedelta(days=30)

    cursor.execute('''
        UPDATE memberships
        SET tier = ?,
            status = 'active',
            current_period_end = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (tier, current_period_end.isoformat(), user_id))

    conn.commit()
    conn.close()

    print(f"🧪 SIMULATED: User {user_id} upgraded to {tier} (expires {current_period_end.date()})")


if __name__ == '__main__':
    """Test the membership system"""
    print("=" * 70)
    print("🧪 STRIPE MEMBERSHIP SYSTEM TEST")
    print("=" * 70)
    print()

    # Test with user ID 1
    user_id = 1

    print("📊 Current Membership:")
    membership = get_membership(user_id)
    print(f"   Tier: {membership['tier']}")
    print(f"   Status: {membership['status']}")
    print(f"   Inventory Limit: {membership['config']['inventory_limit'] or 'Unlimited'}")
    print(f"   Trades/Day: {membership['config']['trades_per_day'] or 'Unlimited'}")
    print()

    print("✅ Can trade today:", can_trade_today(user_id))
    print("✅ Can hold more items:", can_hold_more_items(user_id))
    print()

    # Simulate upgrade to premium
    print("🧪 Simulating upgrade to Premium...")
    simulate_upgrade(user_id, 'premium')
    print()

    print("📊 Updated Membership:")
    membership = get_membership(user_id)
    print(f"   Tier: {membership['tier']}")
    print(f"   Status: {membership['status']}")
    print(f"   Features:")
    for feature in membership['config']['features']:
        print(f"      {feature}")
    print()

    print("=" * 70)
    print("✅ Membership system working!")
    print()
    print("💡 To enable Stripe:")
    print("   export STRIPE_ENABLED=true")
    print("   export STRIPE_SECRET_KEY=sk_test_...")
    print("   export STRIPE_PUBLISHABLE_KEY=pk_test_...")
    print("   export STRIPE_WEBHOOK_SECRET=whsec_...")
    print("=" * 70)

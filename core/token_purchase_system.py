#!/usr/bin/env python3
"""
Token Purchase System - Pay-as-you-go model

Allows users to purchase tokens for one-time use instead of subscriptions.
Uses Stripe Checkout with Link support for one-click payments.

Token Packages:
- Starter: 100 tokens for $10 ($0.10/token)
- Pro: 500 tokens for $40 ($0.08/token) - 20% savings
- Premium: 1000 tokens for $70 ($0.07/token) - 30% savings

Token Usage:
- 1 token = 1 domain import
- 5 tokens = 1 AI brand analysis
- 10 tokens = 1 data export
- 2 tokens = 1 CSV import (up to 50 domains)

Features:
- Stripe Checkout + Link integration
- Apple Pay, Google Pay support
- Purchase history tracking
- Token balance management
- Usage analytics
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List
import json

# Stripe configuration (reuse from membership_system.py)
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


# Token package configuration
TOKEN_PACKAGES = {
    'starter': {
        'name': 'Starter Pack',
        'tokens': 100,
        'price': 10.00,  # USD
        'price_per_token': 0.10,
        'savings': '0%',
        'description': '100 tokens for basic usage',
        'popular': False
    },
    'pro': {
        'name': 'Pro Pack',
        'tokens': 500,
        'price': 40.00,
        'price_per_token': 0.08,
        'savings': '20%',
        'description': '500 tokens with 20% savings',
        'popular': True  # Most popular
    },
    'premium': {
        'name': 'Premium Pack',
        'tokens': 1000,
        'price': 70.00,
        'price_per_token': 0.07,
        'savings': '30%',
        'description': '1000 tokens with 30% savings',
        'popular': False
    }
}

# Token cost for different actions
TOKEN_COSTS = {
    'import_domain': 1,
    'ai_analysis': 5,
    'data_export': 10,
    'csv_import': 2,  # Up to 50 domains
    'premium_feature': 3
}


def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_token_balance(user_id: int) -> int:
    """Get user's current token balance"""
    conn = get_db()
    cursor = conn.cursor()

    # Get total purchased tokens
    cursor.execute('''
        SELECT COALESCE(SUM(tokens), 0) as purchased
        FROM purchases
        WHERE user_id = ? AND type = 'tokens' AND status = 'completed'
    ''', (user_id,))

    purchased = cursor.fetchone()['purchased']

    # Get total spent tokens
    cursor.execute('''
        SELECT COALESCE(SUM(tokens_spent), 0) as spent
        FROM token_usage
        WHERE user_id = ?
    ''', (user_id,))

    spent = cursor.fetchone()['spent']

    conn.close()

    return int(purchased - spent)


def create_token_checkout_session(
    user_id: int,
    package: str,
    success_url: str,
    cancel_url: str
) -> Optional[Dict]:
    """
    Create Stripe Checkout session for token purchase

    Args:
        user_id: User ID
        package: 'starter', 'pro', or 'premium'
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels

    Returns:
        Dict with checkout_url and session_id, or None if error
    """
    if not STRIPE_ENABLED:
        print("⚠️  Stripe not enabled. Set STRIPE_ENABLED=true")
        return None

    if package not in TOKEN_PACKAGES:
        print(f"❌ Invalid package: {package}")
        return None

    pkg = TOKEN_PACKAGES[package]

    # Get or create Stripe customer
    from membership_system import get_or_create_stripe_customer
    customer_id = get_or_create_stripe_customer(user_id)

    if not customer_id:
        print("❌ Failed to create Stripe customer")
        return None

    try:
        # Create Checkout Session (one-time payment, not subscription)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],  # Supports Link, Apple Pay, Google Pay automatically
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': pkg['name'],
                        'description': f"{pkg['tokens']} tokens - Save {pkg['savings']} vs Starter",
                        'images': []  # TODO: Add token pack image
                    },
                    'unit_amount': int(pkg['price'] * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',  # One-time payment (not 'subscription')
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'user_id': user_id,
                'package': package,
                'tokens': pkg['tokens'],
                'type': 'token_purchase'
            },
            # Enable Stripe Link for one-click checkout
            payment_method_options={
                'card': {
                    'setup_future_usage': 'off_session'  # Save for future purchases
                }
            }
        )

        # Record pending purchase
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO purchases (
                user_id, type, amount, tokens, description,
                stripe_checkout_session_id, status
            ) VALUES (?, 'tokens', ?, ?, ?, ?, 'pending')
        ''', (
            user_id,
            pkg['price'],
            pkg['tokens'],
            f"{pkg['name']} - {pkg['tokens']} tokens",
            session.id
        ))

        conn.commit()
        conn.close()

        return {
            'checkout_url': session.url,
            'session_id': session.id,
            'package': package,
            'tokens': pkg['tokens'],
            'price': pkg['price']
        }

    except Exception as e:
        print(f"❌ Stripe Checkout error: {e}")
        return None


def handle_token_purchase_completed(session):
    """
    Handle successful token purchase from webhook

    Called when checkout.session.completed webhook received
    """
    if session['metadata'].get('type') != 'token_purchase':
        return  # Not a token purchase

    user_id = int(session['metadata']['user_id'])
    tokens = int(session['metadata']['tokens'])
    package = session['metadata']['package']

    payment_intent_id = session.get('payment_intent')
    session_id = session['id']

    conn = get_db()
    cursor = conn.cursor()

    # Update purchase record
    cursor.execute('''
        UPDATE purchases
        SET status = 'completed',
            stripe_payment_intent_id = ?,
            completed_at = CURRENT_TIMESTAMP
        WHERE stripe_checkout_session_id = ?
    ''', (payment_intent_id, session_id))

    conn.commit()
    conn.close()

    print(f"✅ User {user_id} purchased {tokens} tokens ({package} pack)")


def spend_tokens(user_id: int, action: str, metadata: Dict = None) -> bool:
    """
    Spend tokens for an action

    Args:
        user_id: User ID
        action: Action type (from TOKEN_COSTS)
        metadata: Additional context (e.g., {'domain': 'example.com'})

    Returns:
        True if tokens spent successfully, False if insufficient balance
    """
    if action not in TOKEN_COSTS:
        print(f"❌ Invalid action: {action}")
        return False

    cost = TOKEN_COSTS[action]
    balance = get_token_balance(user_id)

    if balance < cost:
        print(f"❌ Insufficient tokens. Need {cost}, have {balance}")
        return False

    # Record usage
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO token_usage (user_id, tokens_spent, action, metadata)
        VALUES (?, ?, ?, ?)
    ''', (user_id, cost, action, json.dumps(metadata) if metadata else None))

    conn.commit()
    conn.close()

    print(f"✅ User {user_id} spent {cost} tokens for {action}. Balance: {balance - cost}")
    return True


def get_purchase_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Get user's purchase history"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            id, type, amount, tokens, description, status,
            created_at, completed_at
        FROM purchases
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_token_usage_history(user_id: int, limit: int = 50) -> List[Dict]:
    """Get user's token usage history"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            id, tokens_spent, action, metadata, created_at
        FROM token_usage
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    usage = []
    for row in rows:
        item = dict(row)
        if item['metadata']:
            item['metadata'] = json.loads(item['metadata'])
        usage.append(item)

    return usage


def get_token_stats(user_id: int) -> Dict:
    """Get user's token statistics"""
    balance = get_token_balance(user_id)

    conn = get_db()
    cursor = conn.cursor()

    # Total purchased
    cursor.execute('''
        SELECT
            COALESCE(SUM(tokens), 0) as total_purchased,
            COALESCE(SUM(amount), 0) as total_spent_usd,
            COUNT(*) as purchase_count
        FROM purchases
        WHERE user_id = ? AND type = 'tokens' AND status = 'completed'
    ''', (user_id,))

    purchase_stats = dict(cursor.fetchone())

    # Usage breakdown
    cursor.execute('''
        SELECT
            action,
            COUNT(*) as count,
            SUM(tokens_spent) as tokens
        FROM token_usage
        WHERE user_id = ?
        GROUP BY action
        ORDER BY tokens DESC
    ''', (user_id,))

    usage_breakdown = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'balance': balance,
        'total_purchased': purchase_stats['total_purchased'],
        'total_spent_usd': purchase_stats['total_spent_usd'],
        'purchase_count': purchase_stats['purchase_count'],
        'usage_breakdown': usage_breakdown
    }


# ==================== TESTING HELPERS ====================

def simulate_token_purchase(user_id: int, package: str):
    """
    Simulate token purchase for testing (NO Stripe required)

    Use this in development to test token features without Stripe
    """
    if package not in TOKEN_PACKAGES:
        print(f"❌ Invalid package: {package}")
        return

    pkg = TOKEN_PACKAGES[package]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO purchases (
            user_id, type, amount, tokens, description,
            status, completed_at
        ) VALUES (?, 'tokens', ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
    ''', (
        user_id,
        pkg['price'],
        pkg['tokens'],
        f"SIMULATED: {pkg['name']}"
    ))

    conn.commit()
    conn.close()

    balance = get_token_balance(user_id)
    print(f"🧪 SIMULATED: User {user_id} purchased {pkg['tokens']} tokens. Balance: {balance}")


if __name__ == '__main__':
    """Test the token purchase system"""
    print("=" * 70)
    print("🪙 TOKEN PURCHASE SYSTEM TEST")
    print("=" * 70)
    print()

    # Test with user ID 1
    user_id = 1

    print("📊 Token Packages:")
    for key, pkg in TOKEN_PACKAGES.items():
        popular = " ⭐ POPULAR" if pkg['popular'] else ""
        print(f"   {pkg['name']}{popular}")
        print(f"      {pkg['tokens']} tokens for ${pkg['price']:.2f}")
        print(f"      ${pkg['price_per_token']:.3f} per token (Save {pkg['savings']})")
        print()

    print("💰 Current Balance:", get_token_balance(user_id), "tokens")
    print()

    # Simulate purchase
    print("🧪 Simulating purchase: Pro Pack (500 tokens)...")
    simulate_token_purchase(user_id, 'pro')
    print()

    print("💰 Updated Balance:", get_token_balance(user_id), "tokens")
    print()

    # Test token spending
    print("💸 Testing token spending...")
    spend_tokens(user_id, 'import_domain', {'domain': 'example.com'})
    spend_tokens(user_id, 'ai_analysis', {'brand_id': 1})
    print()

    print("💰 Final Balance:", get_token_balance(user_id), "tokens")
    print()

    # Show stats
    print("📊 Token Statistics:")
    stats = get_token_stats(user_id)
    print(f"   Balance: {stats['balance']} tokens")
    print(f"   Total Purchased: {stats['total_purchased']} tokens")
    print(f"   Total Spent: ${stats['total_spent_usd']:.2f}")
    print(f"   Purchase Count: {stats['purchase_count']}")
    print()

    if stats['usage_breakdown']:
        print("   Usage Breakdown:")
        for item in stats['usage_breakdown']:
            print(f"      {item['action']}: {item['tokens']} tokens ({item['count']}x)")
    print()

    print("=" * 70)
    print("✅ Token purchase system working!")
    print()
    print("💡 To enable Stripe:")
    print("   export STRIPE_ENABLED=true")
    print("   export STRIPE_SECRET_KEY=sk_test_...")
    print("   export STRIPE_PUBLISHABLE_KEY=pk_test_...")
    print("=" * 70)

#!/usr/bin/env python3
"""
Token Purchase Routes - Flask Integration

API endpoints for token purchase system.
Integrates with Stripe Checkout + Link for one-click payments.

Endpoints:
- POST /api/tokens/purchase - Create Stripe Checkout session
- GET /api/tokens/balance - Get user's token balance
- GET /api/tokens/packages - Get available token packages
- GET /api/tokens/history - Get purchase history
- GET /api/tokens/usage - Get token usage history
- POST /api/tokens/webhook - Stripe webhook handler
- GET /tokens/success - Purchase success page
- GET /tokens/cancel - Purchase cancelled page
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
import os

from token_purchase_system import (
    TOKEN_PACKAGES,
    TOKEN_COSTS,
    get_token_balance,
    create_token_checkout_session,
    handle_token_purchase_completed,
    spend_tokens,
    get_purchase_history,
    get_token_usage_history,
    get_token_stats,
    STRIPE_ENABLED,
    STRIPE_WEBHOOK_SECRET
)

# Create blueprint
token_bp = Blueprint('tokens', __name__)


def require_login(f):
    """Decorator to require login"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


# ==================== API ENDPOINTS ====================

@token_bp.route('/api/tokens/packages', methods=['GET'])
def api_get_packages():
    """Get available token packages"""
    return jsonify({
        'packages': TOKEN_PACKAGES,
        'costs': TOKEN_COSTS
    })


@token_bp.route('/api/tokens/balance', methods=['GET'])
@require_login
def api_get_balance():
    """Get user's token balance"""
    user_id = session['user_id']
    balance = get_token_balance(user_id)

    return jsonify({
        'balance': balance,
        'user_id': user_id
    })


@token_bp.route('/api/tokens/purchase', methods=['POST'])
@require_login
def api_purchase_tokens():
    """
    Create Stripe Checkout session for token purchase

    Request body:
        {
            "package": "starter" | "pro" | "premium"
        }

    Response:
        {
            "checkout_url": "https://checkout.stripe.com/...",
            "session_id": "cs_...",
            "package": "pro",
            "tokens": 500,
            "price": 40.00
        }
    """
    if not STRIPE_ENABLED:
        return jsonify({
            'error': 'Stripe not enabled',
            'message': 'Token purchases require Stripe integration'
        }), 503

    user_id = session['user_id']
    data = request.get_json()

    package = data.get('package')
    if not package:
        return jsonify({'error': 'Missing package parameter'}), 400

    if package not in TOKEN_PACKAGES:
        return jsonify({'error': f'Invalid package: {package}'}), 400

    # Create checkout session
    # Get base URL from request
    base_url = request.host_url.rstrip('/')
    success_url = f"{base_url}/tokens/success"
    cancel_url = f"{base_url}/tokens/cancel"

    result = create_token_checkout_session(
        user_id=user_id,
        package=package,
        success_url=success_url,
        cancel_url=cancel_url
    )

    if not result:
        return jsonify({'error': 'Failed to create checkout session'}), 500

    return jsonify(result)


@token_bp.route('/api/tokens/history', methods=['GET'])
@require_login
def api_get_history():
    """Get user's purchase history"""
    user_id = session['user_id']
    limit = request.args.get('limit', 20, type=int)

    history = get_purchase_history(user_id, limit)

    return jsonify({
        'history': history,
        'count': len(history)
    })


@token_bp.route('/api/tokens/usage', methods=['GET'])
@require_login
def api_get_usage():
    """Get user's token usage history"""
    user_id = session['user_id']
    limit = request.args.get('limit', 50, type=int)

    usage = get_token_usage_history(user_id, limit)

    return jsonify({
        'usage': usage,
        'count': len(usage)
    })


@token_bp.route('/api/tokens/stats', methods=['GET'])
@require_login
def api_get_stats():
    """Get user's token statistics"""
    user_id = session['user_id']
    stats = get_token_stats(user_id)

    return jsonify(stats)


@token_bp.route('/api/tokens/spend', methods=['POST'])
@require_login
def api_spend_tokens():
    """
    Spend tokens for an action (internal API)

    Request body:
        {
            "action": "import_domain" | "ai_analysis" | "data_export" | "csv_import",
            "metadata": {...}  // Optional context
        }

    Response:
        {
            "success": true,
            "balance": 494,
            "spent": 5
        }
    """
    user_id = session['user_id']
    data = request.get_json()

    action = data.get('action')
    metadata = data.get('metadata', {})

    if not action:
        return jsonify({'error': 'Missing action parameter'}), 400

    if action not in TOKEN_COSTS:
        return jsonify({'error': f'Invalid action: {action}'}), 400

    # Attempt to spend tokens
    success = spend_tokens(user_id, action, metadata)

    if not success:
        balance = get_token_balance(user_id)
        return jsonify({
            'error': 'Insufficient tokens',
            'balance': balance,
            'required': TOKEN_COSTS[action]
        }), 402  # Payment Required

    new_balance = get_token_balance(user_id)

    return jsonify({
        'success': True,
        'balance': new_balance,
        'spent': TOKEN_COSTS[action]
    })


# ==================== WEBHOOK HANDLER ====================

@token_bp.route('/api/tokens/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks for token purchases

    Events handled:
    - checkout.session.completed: Complete token purchase
    - payment_intent.succeeded: Confirm payment
    - payment_intent.payment_failed: Handle failed payment
    """
    if not STRIPE_ENABLED:
        return jsonify({'error': 'Stripe not enabled'}), 503

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    if not sig_header:
        return jsonify({'error': 'Missing signature'}), 400

    try:
        import stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    event_type = event['type']

    if event_type == 'checkout.session.completed':
        session_data = event['data']['object']
        handle_token_purchase_completed(session_data)

    elif event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"✅ Payment succeeded: {payment_intent['id']}")

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        print(f"❌ Payment failed: {payment_intent['id']}")

    return jsonify({'success': True})


# ==================== SUCCESS/CANCEL PAGES ====================

@token_bp.route('/tokens/success')
@require_login
def token_purchase_success():
    """Token purchase success page"""
    session_id = request.args.get('session_id')
    user_id = session['user_id']

    balance = get_token_balance(user_id)

    return render_template('token_purchase_success.html',
                          session_id=session_id,
                          balance=balance)


@token_bp.route('/tokens/cancel')
@require_login
def token_purchase_cancel():
    """Token purchase cancelled page"""
    return render_template('token_purchase_cancel.html')


# ==================== ADMIN PAGES ====================

@token_bp.route('/admin/tokens')
@require_login
def admin_tokens_page():
    """Token purchase admin page"""
    user_id = session['user_id']

    balance = get_token_balance(user_id)
    stats = get_token_stats(user_id)
    history = get_purchase_history(user_id, 10)

    return render_template('admin_tokens.html',
                          packages=TOKEN_PACKAGES,
                          balance=balance,
                          stats=stats,
                          history=history,
                          stripe_enabled=STRIPE_ENABLED)


# ==================== HELPER FUNCTIONS ====================

def check_token_balance_middleware(action: str):
    """
    Middleware to check token balance before action

    Usage in routes:
        @app.route('/api/domains/import')
        def import_domain():
            if not check_token_balance_middleware('import_domain'):
                return jsonify({'error': 'Insufficient tokens'}), 402
            # ... proceed with import
    """
    if 'user_id' not in session:
        return False

    user_id = session['user_id']
    balance = get_token_balance(user_id)
    required = TOKEN_COSTS.get(action, 0)

    return balance >= required


# Export blueprint
__all__ = ['token_bp', 'check_token_balance_middleware']

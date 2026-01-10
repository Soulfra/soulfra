#!/usr/bin/env python3
"""
OSS Checkout Routes - Lightning Network + BTCPay Server Integration

Replaces Stripe with open source, self-hosted payment processing:
- Lightning Network: Instant, <$0.01 fee
- BTCPay Server: Self-hosted, $0 fee
- Coinbase Commerce: Crypto fallback, 1% fee

Philosophy: $1 is cheap enough to host yourself. No payment processors needed.
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from mvp_payments import (
    create_lightning_invoice,
    create_btcpay_invoice,
    create_coinbase_charge,
    verify_lightning_payment,
    verify_btcpay_payment,
    verify_coinbase_payment,
    record_payment,
    init_mvp_payment_tables
)
import json
from datetime import datetime

oss_checkout_bp = Blueprint('oss_checkout', __name__)


@oss_checkout_bp.route('/api/oss-checkout/create', methods=['POST'])
def create_oss_checkout():
    """
    Create OSS payment checkout with voice-dictated address

    POST body: {
        'street': '123 Main St',
        'unit': 'Apt 4B',
        'city': 'New York',
        'state': 'NY',
        'zip': '10001',
        'email': 'user@example.com',
        'payment_method': 'lightning' | 'btcpay' | 'coinbase'
    }

    Returns:
    - Lightning: {'invoice': 'lnbc...', 'payment_hash': '...'}
    - BTCPay: {'checkout_url': 'https://btcpay.../...'}
    - Coinbase: {'checkout_url': 'https://commerce.coinbase.com/...'}
    """
    data = request.get_json()

    # Extract address
    address = {
        'street': data.get('street', ''),
        'unit': data.get('unit', ''),
        'city': data.get('city', ''),
        'state': data.get('state', ''),
        'zip': data.get('zip', ''),
    }

    email = data.get('email', session.get('email', ''))
    user_id = session.get('user_id')
    payment_method = data.get('payment_method', 'lightning')  # Default to Lightning

    # Validation
    if not address['street'] or not address['city'] or not address['state'] or not address['zip']:
        return jsonify({
            'success': False,
            'error': 'Missing required address fields'
        }), 400

    # Store address in session for later
    session['checkout_address'] = address

    # Create payment based on method
    if payment_method == 'lightning':
        result = create_lightning_invoice(email, user_id)

        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

        # Store payment session in database
        db = get_db()
        db.execute('''
            INSERT INTO mvp_payment_sessions (
                session_id, user_id, email, payment_method, amount, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (result['payment_hash'], user_id, email, 'lightning', 1.00, 'created'))
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'payment_method': 'lightning',
            'invoice': result['invoice'],
            'payment_hash': result['payment_hash'],
            'note': result.get('note', '')
        })

    elif payment_method == 'btcpay':
        result = create_btcpay_invoice(email, user_id)

        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

        return jsonify({
            'success': True,
            'payment_method': 'btcpay',
            'checkout_url': result['checkout_url'],
            'invoice_id': result['invoice_id']
        })

    elif payment_method == 'coinbase':
        result = create_coinbase_charge(email, user_id)

        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

        return jsonify({
            'success': True,
            'payment_method': 'coinbase',
            'checkout_url': result['checkout_url'],
            'charge_id': result['charge_id']
        })

    else:
        return jsonify({
            'success': False,
            'error': f'Unknown payment method: {payment_method}'
        }), 400


@oss_checkout_bp.route('/api/oss-checkout/verify', methods=['POST'])
def verify_oss_payment():
    """
    Verify OSS payment completion

    POST body: {
        'payment_method': 'lightning' | 'btcpay' | 'coinbase',
        'session_id': 'payment_hash' | 'invoice_id' | 'charge_id'
    }

    Returns: {
        'success': bool,
        'paid': bool,
        'transaction_id': str
    }
    """
    data = request.get_json()

    payment_method = data.get('payment_method')
    session_id = data.get('session_id')

    if not payment_method or not session_id:
        return jsonify({
            'success': False,
            'error': 'Missing payment_method or session_id'
        }), 400

    # Verify based on method
    if payment_method == 'lightning':
        result = verify_lightning_payment(session_id)
    elif payment_method == 'btcpay':
        result = verify_btcpay_payment(session_id)
    elif payment_method == 'coinbase':
        result = verify_coinbase_payment(session_id)
    else:
        return jsonify({
            'success': False,
            'error': f'Unknown payment method: {payment_method}'
        }), 400

    if result.get('success'):
        # Record payment in database
        result['payment_method'] = payment_method
        payment_id = record_payment(result)

        # Update session status
        db = get_db()
        db.execute('''
            UPDATE mvp_payment_sessions
            SET status = 'completed'
            WHERE session_id = ?
        ''', (session_id,))
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'paid': True,
            'transaction_id': result['transaction_id'],
            'payment_id': payment_id
        })
    else:
        return jsonify({
            'success': True,
            'paid': False,
            'error': result.get('error', 'Payment not yet completed')
        })


@oss_checkout_bp.route('/api/oss-checkout/status/<session_id>', methods=['GET'])
def get_oss_checkout_status(session_id):
    """
    Check status of checkout session

    GET /api/oss-checkout/status/<session_id>
    Returns: {'status': 'created' | 'completed', 'payment_method': str}
    """
    db = get_db()
    checkout = db.execute('''
        SELECT status, payment_method, amount, created_at
        FROM mvp_payment_sessions
        WHERE session_id = ?
    ''', (session_id,)).fetchone()
    db.close()

    if not checkout:
        return jsonify({'success': False, 'error': 'Checkout not found'}), 404

    return jsonify({
        'success': True,
        'status': checkout['status'],
        'payment_method': checkout['payment_method'],
        'amount': checkout['amount'],
        'created_at': checkout['created_at']
    })


@oss_checkout_bp.route('/api/oss-checkout/methods', methods=['GET'])
def get_payment_methods():
    """
    Get available payment methods and their fees

    Returns: {
        'methods': [
            {'id': 'lightning', 'name': 'Lightning Network', 'fee': 0.001, ...},
            {'id': 'btcpay', 'name': 'BTCPay (Bitcoin/Cards)', 'fee': 0, ...},
            {'id': 'coinbase', 'name': 'Coinbase (Crypto)', 'fee': 0.01, ...}
        ]
    }
    """
    from mvp_payments import get_payment_fees

    methods = []

    for method_id in ['lightning', 'btcpay', 'coinbase']:
        fee_info = get_payment_fees(method_id, 1.00)
        methods.append({
            'id': method_id,
            'name': {
                'lightning': 'Lightning Network',
                'btcpay': 'BTCPay Server',
                'coinbase': 'Coinbase Commerce'
            }[method_id],
            'fee': fee_info['fee'],
            'net': fee_info['net'],
            'description': fee_info['description'],
            'fee_percentage': fee_info['fee_percentage']
        })

    return jsonify({
        'success': True,
        'methods': methods
    })


if __name__ == '__main__':
    print("🔐 Creating OSS payment tables...")
    init_mvp_payment_tables()
    print("✅ OSS checkout system ready!")
    print()
    print("Available payment methods:")
    print("  - Lightning Network (instant, <$0.01 fee)")
    print("  - BTCPay Server (self-hosted, $0 fee)")
    print("  - Coinbase Commerce (crypto, 1% fee)")

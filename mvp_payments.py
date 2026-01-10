#!/usr/bin/env python3
"""
MVP Payments - Decentralized $1 Checkout with Multiple Gateways

Accepts payments via:
- Stripe (credit cards, 33% fees)
- Coinbase Commerce (crypto, 1% fee, non-refundable)
- Lightning Network (instant, <$0.01 fee)
- BTCPay Server (self-hosted, $0 fee)

Philosophy: $1 is cheap enough to accept ANY payment method.
User chooses what works for them.

All payments are NON-REFUNDABLE by design.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from database import get_db

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Stripe
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_placeholder')

# Coinbase Commerce
COINBASE_API_KEY = os.environ.get('COINBASE_COMMERCE_API_KEY', 'placeholder')

# Lightning Network (LND)
LND_MACAROON_PATH = os.environ.get('LND_MACAROON_PATH', '/path/to/admin.macaroon')
LND_CERT_PATH = os.environ.get('LND_CERT_PATH', '/path/to/tls.cert')
LND_GRPC_HOST = os.environ.get('LND_GRPC_HOST', 'localhost:10009')

# BTCPay Server
BTCPAY_SERVER_URL = os.environ.get('BTCPAY_SERVER_URL', 'https://your-btcpay.com')
BTCPAY_API_KEY = os.environ.get('BTCPAY_API_KEY', 'placeholder')
BTCPAY_STORE_ID = os.environ.get('BTCPAY_STORE_ID', 'placeholder')

# Pricing
MVP_BASE_PRICE = 1.00
MVP_OWNERSHIP_PERCENTAGE = 0.1


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_mvp_payment_tables():
    """Initialize MVP payment tables"""
    conn = get_db()

    # MVP payments
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mvp_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            payment_method TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            transaction_id TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            refundable BOOLEAN DEFAULT 0,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')

    # Payment sessions (for tracking checkout sessions)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mvp_payment_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            email TEXT,
            payment_method TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'created',
            payment_url TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# STRIPE INTEGRATION
# ==============================================================================

def create_stripe_checkout(email: str, user_id: Optional[int] = None) -> Dict:
    """
    Create Stripe checkout session for $1 payment

    Args:
        email: User email
        user_id: Optional user ID (if logged in)

    Returns:
        {
            'session_id': str,
            'checkout_url': str,
            'payment_method': 'stripe'
        }
    """

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=email,
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Soulfra MVP Founding Member',
                        'description': '0.1% ownership + digital booklet',
                    },
                    'unit_amount': int(MVP_BASE_PRICE * 100),  # $1.00 in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://soulfra.com/mvp/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://soulfra.com/mvp',
            metadata={
                'user_id': str(user_id) if user_id else '',
                'email': email,
                'product': 'mvp_founding_member'
            }
        )

        # Store session
        conn = get_db()
        conn.execute('''
            INSERT INTO mvp_payment_sessions (
                session_id, user_id, email, payment_method, amount, payment_url
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (session.id, user_id, email, 'stripe', MVP_BASE_PRICE, session.url))
        conn.commit()
        conn.close()

        return {
            'session_id': session.id,
            'checkout_url': session.url,
            'payment_method': 'stripe'
        }

    except Exception as e:
        return {'error': str(e)}


def verify_stripe_payment(session_id: str) -> Dict:
    """
    Verify Stripe payment was completed

    Args:
        session_id: Stripe checkout session ID

    Returns:
        {
            'success': bool,
            'transaction_id': str,
            'email': str,
            'user_id': int or None
        }
    """

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            return {
                'success': True,
                'transaction_id': session.payment_intent,
                'email': session.customer_email,
                'user_id': session.metadata.get('user_id') if session.metadata.get('user_id') else None,
                'amount': session.amount_total / 100.0  # Convert cents to dollars
            }
        else:
            return {'success': False, 'error': 'Payment not completed'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# ==============================================================================
# COINBASE COMMERCE INTEGRATION
# ==============================================================================

def create_coinbase_charge(email: str, user_id: Optional[int] = None) -> Dict:
    """
    Create Coinbase Commerce charge for $1 crypto payment

    Args:
        email: User email
        user_id: Optional user ID

    Returns:
        {
            'charge_id': str,
            'checkout_url': str,
            'payment_method': 'coinbase'
        }
    """

    try:
        url = 'https://api.commerce.coinbase.com/charges'

        headers = {
            'X-CC-Api-Key': COINBASE_API_KEY,
            'X-CC-Version': '2018-03-22',
            'Content-Type': 'application/json'
        }

        data = {
            'name': 'Soulfra MVP Founding Member',
            'description': '0.1% ownership + digital booklet',
            'pricing_type': 'fixed_price',
            'local_price': {
                'amount': str(MVP_BASE_PRICE),
                'currency': 'USD'
            },
            'metadata': {
                'user_id': str(user_id) if user_id else '',
                'email': email,
                'product': 'mvp_founding_member'
            },
            'redirect_url': 'https://soulfra.com/mvp/success',
            'cancel_url': 'https://soulfra.com/mvp'
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        charge = response.json()['data']

        # Store session
        conn = get_db()
        conn.execute('''
            INSERT INTO mvp_payment_sessions (
                session_id, user_id, email, payment_method, amount, payment_url
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (charge['id'], user_id, email, 'coinbase', MVP_BASE_PRICE, charge['hosted_url']))
        conn.commit()
        conn.close()

        return {
            'charge_id': charge['id'],
            'checkout_url': charge['hosted_url'],
            'payment_method': 'coinbase'
        }

    except Exception as e:
        return {'error': str(e)}


def verify_coinbase_payment(charge_id: str) -> Dict:
    """
    Verify Coinbase Commerce payment was completed

    Args:
        charge_id: Coinbase charge ID

    Returns:
        {
            'success': bool,
            'transaction_id': str,
            'email': str,
            'user_id': int or None
        }
    """

    try:
        url = f'https://api.commerce.coinbase.com/charges/{charge_id}'

        headers = {
            'X-CC-Api-Key': COINBASE_API_KEY,
            'X-CC-Version': '2018-03-22'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        charge = response.json()['data']

        if charge['timeline'][-1]['status'] == 'COMPLETED':
            return {
                'success': True,
                'transaction_id': charge['id'],
                'email': charge['metadata'].get('email', ''),
                'user_id': charge['metadata'].get('user_id'),
                'amount': float(charge['pricing']['local']['amount']),
                'currency': charge['pricing']['local']['currency']
            }
        else:
            return {'success': False, 'error': 'Payment not completed'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# ==============================================================================
# LIGHTNING NETWORK INTEGRATION (Placeholder)
# ==============================================================================

def create_lightning_invoice(email: str, user_id: Optional[int] = None) -> Dict:
    """
    Create Lightning Network invoice for instant $1 payment

    Args:
        email: User email
        user_id: Optional user ID

    Returns:
        {
            'invoice': str (BOLT11 payment request),
            'payment_hash': str,
            'payment_method': 'lightning'
        }
    """

    # In production, use lnd_grpc or similar:
    # from lnd_grpc import Client
    # lnd = Client(
    #     macaroon_filepath=LND_MACAROON_PATH,
    #     cert_filepath=LND_CERT_PATH,
    #     grpc_host=LND_GRPC_HOST
    # )
    #
    # # Get current BTC price to convert $1 to satoshis
    # btc_price = get_btc_price()
    # satoshis = int((MVP_BASE_PRICE / btc_price) * 100_000_000)
    #
    # invoice = lnd.add_invoice(
    #     value=satoshis,
    #     memo=f'Soulfra MVP - {email}',
    #     expiry=3600  # 1 hour
    # )
    #
    # return {
    #     'invoice': invoice.payment_request,
    #     'payment_hash': invoice.r_hash.hex(),
    #     'payment_method': 'lightning'
    # }

    # Placeholder for now
    return {
        'invoice': 'lnbc1000n1...',  # BOLT11 invoice
        'payment_hash': 'placeholder_hash',
        'payment_method': 'lightning',
        'note': 'Lightning Network integration requires LND node setup'
    }


def verify_lightning_payment(payment_hash: str) -> Dict:
    """
    Verify Lightning payment was received

    Args:
        payment_hash: Lightning payment hash

    Returns:
        {
            'success': bool,
            'transaction_id': str,
            'amount': float
        }
    """

    # In production:
    # invoice = lnd.lookup_invoice(r_hash_str=payment_hash)
    # if invoice.state == lnd_grpc.lnrpc.Invoice.SETTLED:
    #     return {
    #         'success': True,
    #         'transaction_id': payment_hash,
    #         'amount': invoice.value / 100_000_000 * btc_price
    #     }

    # Placeholder
    return {'success': False, 'error': 'Lightning integration not yet configured'}


# ==============================================================================
# BTCPAY SERVER INTEGRATION
# ==============================================================================

def create_btcpay_invoice(email: str, user_id: Optional[int] = None) -> Dict:
    """
    Create BTCPay Server invoice for $1 payment

    Args:
        email: User email
        user_id: Optional user ID

    Returns:
        {
            'invoice_id': str,
            'checkout_url': str,
            'payment_method': 'btcpay'
        }
    """

    try:
        url = f'{BTCPAY_SERVER_URL}/api/v1/stores/{BTCPAY_STORE_ID}/invoices'

        headers = {
            'Authorization': f'token {BTCPAY_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            'amount': str(MVP_BASE_PRICE),
            'currency': 'USD',
            'metadata': {
                'orderId': f'mvp_{user_id}_{int(datetime.utcnow().timestamp())}',
                'buyerEmail': email,
                'user_id': str(user_id) if user_id else ''
            },
            'checkout': {
                'redirectURL': 'https://soulfra.com/mvp/success',
                'redirectAutomatically': True
            }
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        invoice = response.json()

        # Store session
        conn = get_db()
        conn.execute('''
            INSERT INTO mvp_payment_sessions (
                session_id, user_id, email, payment_method, amount, payment_url
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (invoice['id'], user_id, email, 'btcpay', MVP_BASE_PRICE, invoice['checkoutLink']))
        conn.commit()
        conn.close()

        return {
            'invoice_id': invoice['id'],
            'checkout_url': invoice['checkoutLink'],
            'payment_method': 'btcpay'
        }

    except Exception as e:
        return {'error': str(e)}


def verify_btcpay_payment(invoice_id: str) -> Dict:
    """
    Verify BTCPay Server payment was completed

    Args:
        invoice_id: BTCPay invoice ID

    Returns:
        {
            'success': bool,
            'transaction_id': str,
            'amount': float
        }
    """

    try:
        url = f'{BTCPAY_SERVER_URL}/api/v1/stores/{BTCPAY_STORE_ID}/invoices/{invoice_id}'

        headers = {
            'Authorization': f'token {BTCPAY_API_KEY}'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        invoice = response.json()

        if invoice['status'] in ['settled', 'complete']:
            return {
                'success': True,
                'transaction_id': invoice_id,
                'amount': float(invoice['amount']),
                'currency': invoice['currency']
            }
        else:
            return {'success': False, 'error': f"Invoice status: {invoice['status']}"}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# ==============================================================================
# UNIFIED PAYMENT INTERFACE
# ==============================================================================

def create_payment_checkout(email: str, payment_method: str, user_id: Optional[int] = None) -> Dict:
    """
    Create payment checkout for any method

    Args:
        email: User email
        payment_method: 'stripe', 'coinbase', 'lightning', 'btcpay'
        user_id: Optional user ID

    Returns:
        {
            'checkout_url': str or 'invoice': str (for Lightning),
            'session_id': str,
            'payment_method': str
        }
    """

    if payment_method == 'stripe':
        return create_stripe_checkout(email, user_id)

    elif payment_method == 'coinbase':
        return create_coinbase_charge(email, user_id)

    elif payment_method == 'lightning':
        return create_lightning_invoice(email, user_id)

    elif payment_method == 'btcpay':
        return create_btcpay_invoice(email, user_id)

    else:
        return {'error': f'Unknown payment method: {payment_method}'}


def verify_payment(payment_method: str, session_id: str) -> Dict:
    """
    Verify payment for any method

    Args:
        payment_method: 'stripe', 'coinbase', 'lightning', 'btcpay'
        session_id: Session/charge/invoice ID

    Returns:
        {
            'success': bool,
            'transaction_id': str,
            'email': str,
            'user_id': int or None,
            'amount': float
        }
    """

    if payment_method == 'stripe':
        return verify_stripe_payment(session_id)

    elif payment_method == 'coinbase':
        return verify_coinbase_payment(session_id)

    elif payment_method == 'lightning':
        return verify_lightning_payment(session_id)

    elif payment_method == 'btcpay':
        return verify_btcpay_payment(session_id)

    else:
        return {'success': False, 'error': f'Unknown payment method: {payment_method}'}


def record_payment(payment_data: Dict) -> int:
    """
    Record successful payment in database

    Args:
        payment_data: Dict from verify_payment()

    Returns:
        payment_id
    """

    conn = get_db()

    cursor = conn.execute('''
        INSERT INTO mvp_payments (
            user_id, email, payment_method, amount,
            transaction_id, status, refundable, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        payment_data.get('user_id'),
        payment_data.get('email'),
        payment_data.get('payment_method', 'unknown'),
        payment_data.get('amount', MVP_BASE_PRICE),
        payment_data.get('transaction_id'),
        'completed',
        False,  # NON-REFUNDABLE
        datetime.utcnow()
    ))

    payment_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return payment_id


# ==============================================================================
# PAYMENT FEES COMPARISON
# ==============================================================================

def get_payment_fees(payment_method: str, amount: float = 1.00) -> Dict:
    """
    Calculate fees for each payment method

    Returns:
        {
            'method': str,
            'gross': float,
            'fee': float,
            'net': float,
            'fee_percentage': float
        }
    """

    fees = {
        'stripe': {
            'method': 'stripe',
            'gross': amount,
            'fee': 0.30 + (amount * 0.029),  # $0.30 + 2.9%
            'description': 'Credit cards accepted, highest fees'
        },
        'coinbase': {
            'method': 'coinbase',
            'gross': amount,
            'fee': amount * 0.01,  # 1%
            'description': 'Crypto only, non-refundable by design'
        },
        'lightning': {
            'method': 'lightning',
            'gross': amount,
            'fee': 0.001,  # <$0.01
            'description': 'Instant settlement, lowest fees'
        },
        'btcpay': {
            'method': 'btcpay',
            'gross': amount,
            'fee': 0.00,  # Self-hosted
            'description': 'Self-hosted, zero fees, full control'
        }
    }

    if payment_method not in fees:
        return {'error': 'Unknown payment method'}

    fee_data = fees[payment_method]
    fee_data['net'] = fee_data['gross'] - fee_data['fee']
    fee_data['fee_percentage'] = (fee_data['fee'] / fee_data['gross']) * 100

    return fee_data


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing MVP payment tables...")
    init_mvp_payment_tables()
    print("✅ MVP payment tables initialized")
    print()
    print("Supported payment methods:")
    print("  - Stripe (credit cards)")
    print("  - Coinbase Commerce (crypto)")
    print("  - Lightning Network (instant BTC)")
    print("  - BTCPay Server (self-hosted)")
    print()
    print("Fee comparison for $1.00 payment:")
    for method in ['stripe', 'coinbase', 'lightning', 'btcpay']:
        fees = get_payment_fees(method, 1.00)
        print(f"  {method.upper()}:")
        print(f"    Fee: ${fees['fee']:.4f} ({fees['fee_percentage']:.1f}%)")
        print(f"    Net: ${fees['net']:.2f}")
        print(f"    {fees['description']}")
        print()

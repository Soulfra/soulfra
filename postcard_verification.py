#!/usr/bin/env python3
"""
$1 Postcard Verification System

Each domain onboarding collects shipping address + $1 payment.
Postcard sent with verification code.
User enters code → verified + payment method on file.
"""

import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from database import get_db


def init_postcard_tables():
    """Create tables for postcard verification"""
    db = get_db()

    # Shipping addresses table
    db.execute('''
        CREATE TABLE IF NOT EXISTS shipping_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            full_name TEXT NOT NULL,
            address_line1 TEXT NOT NULL,
            address_line2 TEXT,
            city TEXT NOT NULL,
            state_province TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            country TEXT NOT NULL DEFAULT 'US',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Verification codes table
    db.execute('''
        CREATE TABLE IF NOT EXISTS postcard_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            verification_code TEXT NOT NULL UNIQUE,
            address_id INTEGER NOT NULL,
            payment_status TEXT DEFAULT 'pending',  -- pending, paid, sent, verified
            payment_method TEXT,  -- lightning, btcpay, stripe
            payment_txid TEXT,  -- Transaction ID
            sent_date TIMESTAMP,
            verified_date TIMESTAMP,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (address_id) REFERENCES shipping_addresses(id)
        )
    ''')

    db.commit()
    print("✅ Postcard verification tables created")


def generate_verification_code(length=6):
    """Generate random alphanumeric code (no confusing chars)"""
    # Exclude 0, O, I, 1, l to avoid confusion
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def save_shipping_address(user_id, domain, address_data):
    """
    Save shipping address for user
    
    Args:
        user_id: User ID
        domain: Domain (cringeproof.com, calriven.com, etc.)
        address_data: dict with keys:
            full_name, address_line1, address_line2, city, state_province, postal_code, country
    
    Returns:
        address_id
    """
    db = get_db()

    cursor = db.execute('''
        INSERT INTO shipping_addresses 
        (user_id, domain, full_name, address_line1, address_line2, city, state_province, postal_code, country)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        domain,
        address_data['full_name'],
        address_data['address_line1'],
        address_data.get('address_line2', ''),
        address_data['city'],
        address_data['state_province'],
        address_data['postal_code'],
        address_data.get('country', 'US')
    ))

    db.commit()
    return cursor.lastrowid


def create_postcard_verification(user_id, address_id):
    """
    Create postcard verification request
    
    Returns:
        {
            'verification_code': 'ABC123',
            'expires_at': datetime,
            'payment_required': True
        }
    """
    db = get_db()

    code = generate_verification_code()
    expires_at = datetime.now() + timedelta(days=30)  # Code valid for 30 days

    db.execute('''
        INSERT INTO postcard_verifications 
        (user_id, verification_code, address_id, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, code, address_id, expires_at.isoformat()))

    db.commit()

    return {
        'verification_code': code,
        'expires_at': expires_at.isoformat(),
        'payment_required': True,
        'amount': 1.00,  # $1 USD
        'currency': 'USD'
    }


def mark_payment_received(verification_code, payment_method, txid):
    """
    Mark payment as received for postcard
    
    Returns:
        {
            'success': bool,
            'ready_to_send': bool
        }
    """
    db = get_db()

    db.execute('''
        UPDATE postcard_verifications
        SET payment_status = 'paid',
            payment_method = ?,
            payment_txid = ?
        WHERE verification_code = ?
    ''', (payment_method, txid, verification_code))

    db.commit()

    return {
        'success': True,
        'ready_to_send': True,
        'message': 'Payment received. Postcard will be sent within 2-3 business days.'
    }


def mark_postcard_sent(verification_code):
    """Mark postcard as sent"""
    db = get_db()

    db.execute('''
        UPDATE postcard_verifications
        SET payment_status = 'sent',
            sent_date = ?
        WHERE verification_code = ?
    ''', (datetime.now().isoformat(), verification_code))

    db.commit()


def verify_code(entered_code, user_id):
    """
    Verify postcard code entered by user
    
    Returns:
        {
            'verified': bool,
            'error': str or None
        }
    """
    db = get_db()

    # Check code exists and matches user
    result = db.execute('''
        SELECT id, payment_status, verified_date, expires_at
        FROM postcard_verifications
        WHERE verification_code = ? AND user_id = ?
    ''', (entered_code.upper(), user_id)).fetchone()

    if not result:
        return {'verified': False, 'error': 'Invalid code'}

    if result['verified_date']:
        return {'verified': False, 'error': 'Code already used'}

    # Check expiration
    expires_at = datetime.fromisoformat(result['expires_at'])
    if datetime.now() > expires_at:
        return {'verified': False, 'error': 'Code expired'}

    # Verify
    db.execute('''
        UPDATE postcard_verifications
        SET payment_status = 'verified',
            verified_date = ?
        WHERE verification_code = ?
    ''', (datetime.now().isoformat(), entered_code.upper()))

    db.commit()

    return {
        'verified': True,
        'message': '✅ Address verified! You can now receive physical rewards.'
    }


def get_pending_postcards():
    """
    Get list of postcards ready to send
    
    Returns:
        List of addresses + codes to print
    """
    db = get_db()

    results = db.execute('''
        SELECT 
            pv.verification_code,
            pv.payment_method,
            sa.full_name,
            sa.address_line1,
            sa.address_line2,
            sa.city,
            sa.state_province,
            sa.postal_code,
            sa.country,
            pv.created_at
        FROM postcard_verifications pv
        JOIN shipping_addresses sa ON pv.address_id = sa.id
        WHERE pv.payment_status = 'paid'
        ORDER BY pv.created_at ASC
    ''').fetchall()

    return [{
        'code': row['verification_code'],
        'name': row['full_name'],
        'address': {
            'line1': row['address_line1'],
            'line2': row['address_line2'],
            'city': row['city'],
            'state': row['state_province'],
            'postal_code': row['postal_code'],
            'country': row['country']
        },
        'payment_method': row['payment_method']
    } for row in results]


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 postcard_verification.py init              # Create tables")
        print("  python3 postcard_verification.py pending           # Get pending postcards")
        print("  python3 postcard_verification.py verify <code>     # Test verification")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init':
        init_postcard_tables()

    elif command == 'pending':
        postcards = get_pending_postcards()
        print(f"📬 {len(postcards)} postcards ready to send:")
        for p in postcards:
            print(f"\nCode: {p['code']}")
            print(f"Name: {p['name']}")
            print(f"Address: {p['address']['line1']}, {p['address']['city']}, {p['address']['state']} {p['address']['postal_code']}")

    elif command == 'verify' and len(sys.argv) > 2:
        code = sys.argv[2]
        result = verify_code(code, user_id=1)  # Test with user 1
        print(result)

    else:
        print("Unknown command")
        sys.exit(1)

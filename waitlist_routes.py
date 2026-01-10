#!/usr/bin/env python3
"""
Waitlist Routes - Gamified domain launch waitlist

API Endpoints:
    POST /api/waitlist/signup - Join waitlist for a domain
    GET /api/waitlist/stats - Get all domain stats
    GET /api/waitlist/leaderboard - Get competitive leaderboard
    GET /api/waitlist/domain/<domain> - Get specific domain stats
    POST /api/waitlist/launch/<domain> - Mark domain as launched (admin)

Database Tables:
    - waitlist: Email signups with letter codes
    - domain_launches: Domain launch config and status
"""

from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime, timezone
import hashlib
import secrets
from launch_calculator import (
    calculate_launch_date,
    get_leaderboard,
    get_letter_allocation,
    assign_letter_to_signup,
    mark_domain_launched
)

waitlist_bp = Blueprint('waitlist', __name__)


def generate_referral_code(email, domain_name):
    """
    Generate unique referral code for a user

    Args:
        email (str): User email
        domain_name (str): Domain name

    Returns:
        str: 8-character referral code
    """
    # Hash email + domain + random salt
    salt = secrets.token_hex(8)
    hash_input = f"{email}{domain_name}{salt}".encode('utf-8')
    hash_hex = hashlib.sha256(hash_input).hexdigest()

    # Take first 8 characters
    return hash_hex[:8].upper()


@waitlist_bp.route('/api/waitlist/signup', methods=['POST'])
def waitlist_signup():
    """
    Join waitlist for a domain

    POST /api/waitlist/signup
    {
        "email": "user@example.com",
        "domain_name": "soulfra",
        "referred_by_code": "ABC12345"  // Optional
    }

    Returns:
        {
            "success": true,
            "letter_code": "A",
            "referral_code": "XYZ98765",
            "domain": {...launch info...}
        }
    """
    data = request.get_json()

    email = data.get('email', '').strip().lower()
    domain_name = data.get('domain_name', '').strip().lower()
    referred_by_code = data.get('referred_by_code', '').strip().upper()

    # Validate
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400

    valid_domains = ['soulfra', 'calriven', 'deathtodata', 'cringeproof']
    if domain_name not in valid_domains:
        return jsonify({'error': f'Invalid domain. Choose: {", ".join(valid_domains)}'}), 400

    db = get_db()

    # Check if already signed up
    existing = db.execute('''
        SELECT * FROM waitlist WHERE email = ? AND domain_name = ?
    ''', (email, domain_name)).fetchone()

    if existing:
        return jsonify({
            'error': 'Already signed up for this domain',
            'letter_code': existing['letter_code'],
            'referral_code': existing['referral_code']
        }), 400

    # Check if domain is full (26 letters)
    allocation = get_letter_allocation(domain_name)
    if allocation['is_full']:
        return jsonify({
            'error': f'{domain_name} waitlist is FULL (26/26 slots taken)',
            'is_full': True
        }), 400

    # Find referrer (if code provided)
    referred_by_id = None
    if referred_by_code:
        referrer = db.execute('''
            SELECT id FROM waitlist WHERE referral_code = ?
        ''', (referred_by_code,)).fetchone()

        if referrer:
            referred_by_id = referrer['id']

    # Generate referral code for this user
    referral_code = generate_referral_code(email, domain_name)

    # Create signup
    signup_at = datetime.now(timezone.utc).isoformat()

    cursor = db.execute('''
        INSERT INTO waitlist (email, domain_name, signup_at, referral_code, referred_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, domain_name, signup_at, referral_code, referred_by_id))

    waitlist_id = cursor.lastrowid
    db.commit()

    # Assign letter code
    letter_code = assign_letter_to_signup(waitlist_id)

    # Get updated launch info
    launch_info = calculate_launch_date(domain_name)

    # Check if domain should launch
    if launch_info and launch_info['days_until'] == 0 and not launch_info['is_launched']:
        mark_domain_launched(domain_name)
        launch_info['is_launched'] = True

    return jsonify({
        'success': True,
        'message': f'Signed up for {domain_name} waitlist!',
        'letter_code': letter_code,
        'referral_code': referral_code,
        'position': waitlist_id,
        'domain': launch_info,
        'slots_remaining': allocation['remaining_slots'] - 1  # -1 for this signup
    }), 201


@waitlist_bp.route('/api/waitlist/stats', methods=['GET'])
def waitlist_stats():
    """
    Get stats for all domains

    GET /api/waitlist/stats

    Returns:
        {
            "domains": [
                {...launch info for soulfra...},
                {...launch info for calriven...},
                ...
            ],
            "total_signups": 156
        }
    """
    leaderboard = get_leaderboard()

    db = get_db()
    total_signups = db.execute('SELECT COUNT(*) as count FROM waitlist').fetchone()['count']

    return jsonify({
        'domains': leaderboard,
        'total_signups': total_signups,
        'updated_at': datetime.now(timezone.utc).isoformat()
    })


@waitlist_bp.route('/api/waitlist/leaderboard', methods=['GET'])
def waitlist_leaderboard():
    """
    Get competitive leaderboard

    GET /api/waitlist/leaderboard

    Returns:
        [
            {
                "rank": 1,
                "domain_name": "soulfra",
                "signups": 234,
                "days_until": 67,
                "progress_pct": 26.0
            },
            ...
        ]
    """
    leaderboard = get_leaderboard()

    # Add rank
    for rank, domain in enumerate(leaderboard, 1):
        domain['rank'] = rank

    return jsonify(leaderboard)


@waitlist_bp.route('/api/waitlist/domain/<domain_name>', methods=['GET'])
def get_domain_waitlist(domain_name):
    """
    Get waitlist info for specific domain

    GET /api/waitlist/domain/soulfra

    Returns:
        {
            "domain_name": "soulfra",
            "signups": 123,
            "days_until": 78,
            "launch_date": "2026-03-25T...",
            "is_launched": false,
            "letter_allocation": {
                "allocated": ["A", "B", "C"],
                "available": ["D", "E", ...],
                "remaining_slots": 23
            }
        }
    """
    launch_info = calculate_launch_date(domain_name)

    if not launch_info:
        return jsonify({'error': 'Domain not found'}), 404

    allocation = get_letter_allocation(domain_name)

    return jsonify({
        **launch_info,
        'letter_allocation': allocation
    })


@waitlist_bp.route('/api/waitlist/launch/<domain_name>', methods=['POST'])
def launch_domain(domain_name):
    """
    Mark domain as launched (admin only)

    POST /api/waitlist/launch/soulfra

    Returns:
        {
            "success": true,
            "domain_name": "soulfra",
            "launched_at": "2026-01-06T..."
        }
    """
    # TODO: Add admin authentication

    success = mark_domain_launched(domain_name)

    if success:
        return jsonify({
            'success': True,
            'domain_name': domain_name,
            'launched_at': datetime.now(timezone.utc).isoformat()
        })
    else:
        return jsonify({'error': 'Failed to launch domain'}), 500


@waitlist_bp.route('/api/waitlist/verify/<referral_code>', methods=['GET'])
def verify_referral_code(referral_code):
    """
    Verify if a referral code exists

    GET /api/waitlist/verify/ABC12345

    Returns:
        {
            "valid": true,
            "domain_name": "soulfra",
            "letter_code": "A"
        }
    """
    db = get_db()

    entry = db.execute('''
        SELECT domain_name, letter_code FROM waitlist WHERE referral_code = ?
    ''', (referral_code.upper(),)).fetchone()

    if entry:
        return jsonify({
            'valid': True,
            'domain_name': entry['domain_name'],
            'letter_code': entry['letter_code']
        })
    else:
        return jsonify({'valid': False}), 404


# CLI initialization
if __name__ == '__main__':
    print("Waitlist Routes - API Endpoints:")
    print("  POST /api/waitlist/signup")
    print("  GET /api/waitlist/stats")
    print("  GET /api/waitlist/leaderboard")
    print("  GET /api/waitlist/domain/<domain>")
    print("  POST /api/waitlist/launch/<domain>")
    print("  GET /api/waitlist/verify/<code>")

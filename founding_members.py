#!/usr/bin/env python3
"""
Founding Members - $1 MVP Pre-Sale System

Pay $1 → Get 0.1% ownership + digital booklet
Non-refundable by design
Timestamped proof of purchase

Philosophy: Early supporters get equity stake for life.
Their $1 could be worth $1000+ if platform succeeds.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
from database import get_db
from ownership_ledger import update_ownership, get_domain_ownership_distribution
from mvp_payments import record_payment, MVP_BASE_PRICE, MVP_OWNERSHIP_PERCENTAGE

# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_founding_members_tables():
    """Initialize founding members tables"""
    conn = get_db()

    # Founding members
    conn.execute('''
        CREATE TABLE IF NOT EXISTS founding_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT NOT NULL,
            payment_id INTEGER NOT NULL,
            ownership_percentage REAL NOT NULL,
            domain_id INTEGER DEFAULT 1,
            paid_amount REAL NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            booklet_downloaded BOOLEAN DEFAULT 0,
            proof_nft_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (payment_id) REFERENCES mvp_payments(id),
            FOREIGN KEY (domain_id) REFERENCES domains(id)
        )
    ''')

    # Booklet downloads (track when users download)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS founding_member_booklets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            founding_member_id INTEGER NOT NULL,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (founding_member_id) REFERENCES founding_members(id)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# FOUNDING MEMBER CREATION
# ==============================================================================

def create_founding_member(email: str, payment_data: Dict, user_id: Optional[int] = None) -> Dict:
    """
    Create founding member after successful payment

    Args:
        email: User email
        payment_data: Dict from mvp_payments.verify_payment()
        user_id: Optional user ID (if logged in)

    Returns:
        {
            'success': bool,
            'founding_member_id': int,
            'ownership_percentage': float,
            'proof_token': str (for verification)
        }
    """

    conn = get_db()

    try:
        # Record payment
        payment_id = record_payment(payment_data)

        # Create founding member record
        cursor = conn.execute('''
            INSERT INTO founding_members (
                user_id, email, payment_id,
                ownership_percentage, domain_id, paid_amount
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            email,
            payment_id,
            MVP_OWNERSHIP_PERCENTAGE,
            1,  # soulfra.com
            payment_data.get('amount', MVP_BASE_PRICE)
        ))

        founding_member_id = cursor.lastrowid

        # Grant ownership in domain_ownership table
        if user_id:
            # Add to their existing ownership
            conn.execute('''
                INSERT INTO domain_ownership (
                    user_id, domain_id, ownership_percentage,
                    base_tier_percentage, stars_bonus, posts_bonus, referrals_bonus
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, domain_id) DO UPDATE SET
                    ownership_percentage = ownership_percentage + ?,
                    last_calculated = CURRENT_TIMESTAMP
            ''', (
                user_id, 1, MVP_OWNERSHIP_PERCENTAGE,
                MVP_OWNERSHIP_PERCENTAGE, 0.0, 0.0, 0.0,
                MVP_OWNERSHIP_PERCENTAGE  # Add to existing
            ))

            # Record ownership history
            conn.execute('''
                INSERT INTO ownership_history (
                    user_id, domain_id, old_percentage, new_percentage, change_reason
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, 1, 0.0, MVP_OWNERSHIP_PERCENTAGE, 'founding_member_purchase'
            ))

        conn.commit()

        # Generate proof token (for booklet download verification)
        import hashlib
        proof_token = hashlib.sha256(
            f"{founding_member_id}{email}{payment_id}".encode()
        ).hexdigest()[:16]

        conn.close()

        return {
            'success': True,
            'founding_member_id': founding_member_id,
            'ownership_percentage': MVP_OWNERSHIP_PERCENTAGE,
            'proof_token': proof_token,
            'paid_amount': payment_data.get('amount', MVP_BASE_PRICE),
            'purchase_date': datetime.utcnow().isoformat()
        }

    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}


# ==============================================================================
# BOOKLET GENERATION & DOWNLOAD
# ==============================================================================

def generate_booklet_pdf(founding_member_id: int) -> Optional[bytes]:
    """
    Generate digital booklet PDF from ECONOMIC_MODEL.md

    Args:
        founding_member_id: Founding member ID

    Returns:
        PDF bytes or None
    """

    # In production, use reportlab or weasyprint:
    # from reportlab.lib.pagesizes import letter
    # from reportlab.pdfgen import canvas
    # from reportlab.lib.utils import simpleSplit
    #
    # # Read ECONOMIC_MODEL.md
    # with open('ECONOMIC_MODEL.md', 'r') as f:
    #     markdown_content = f.read()
    #
    # # Convert markdown to PDF
    # ...

    # For now, placeholder
    return b'%PDF-1.4\n...placeholder...'


def record_booklet_download(founding_member_id: int, ip_address: str = None, user_agent: str = None):
    """
    Record booklet download

    Args:
        founding_member_id: Founding member ID
        ip_address: User's IP
        user_agent: User's browser
    """

    conn = get_db()

    conn.execute('''
        INSERT INTO founding_member_booklets (
            founding_member_id, ip_address, user_agent
        ) VALUES (?, ?, ?)
    ''', (founding_member_id, ip_address, user_agent))

    # Mark as downloaded
    conn.execute('''
        UPDATE founding_members
        SET booklet_downloaded = 1
        WHERE id = ?
    ''', (founding_member_id,))

    conn.commit()
    conn.close()


# ==============================================================================
# FOUNDING MEMBER STATS
# ==============================================================================

def get_founding_member_stats() -> Dict:
    """
    Get overall founding member statistics

    Returns:
        {
            'total_members': int,
            'total_raised': float,
            'total_ownership_distributed': float,
            'average_stake_value': float
        }
    """

    conn = get_db()

    stats = conn.execute('''
        SELECT
            COUNT(*) as total_members,
            SUM(paid_amount) as total_raised,
            SUM(ownership_percentage) as total_ownership_distributed
        FROM founding_members
    ''').fetchone()

    conn.close()

    # Calculate average stake value (based on platform valuation)
    # Placeholder: $50k valuation
    platform_valuation = 50000.0
    avg_ownership = stats['total_ownership_distributed'] / stats['total_members'] if stats['total_members'] > 0 else 0
    avg_stake_value = platform_valuation * (avg_ownership / 100.0) if avg_ownership > 0 else 0

    return {
        'total_members': stats['total_members'],
        'total_raised': stats['total_raised'] or 0.0,
        'total_ownership_distributed': stats['total_ownership_distributed'] or 0.0,
        'average_stake_value': avg_stake_value,
        'platform_valuation': platform_valuation
    }


def get_founding_member_info(email: str = None, user_id: int = None, founding_member_id: int = None) -> Optional[Dict]:
    """
    Get founding member information

    Args:
        email: Lookup by email
        user_id: Lookup by user ID
        founding_member_id: Lookup by ID

    Returns:
        {
            'founding_member_id': int,
            'email': str,
            'ownership_percentage': float,
            'paid_amount': float,
            'purchase_date': str,
            'current_stake_value': float,
            'roi': float
        }
    """

    conn = get_db()

    if founding_member_id:
        member = conn.execute(
            'SELECT * FROM founding_members WHERE id = ?',
            (founding_member_id,)
        ).fetchone()
    elif user_id:
        member = conn.execute(
            'SELECT * FROM founding_members WHERE user_id = ? ORDER BY purchase_date ASC LIMIT 1',
            (user_id,)
        ).fetchone()
    elif email:
        member = conn.execute(
            'SELECT * FROM founding_members WHERE email = ? ORDER BY purchase_date ASC LIMIT 1',
            (email,)
        ).fetchone()
    else:
        conn.close()
        return None

    if not member:
        conn.close()
        return None

    # Calculate current stake value
    # Placeholder: $50k valuation
    platform_valuation = 50000.0
    stake_value = platform_valuation * (member['ownership_percentage'] / 100.0)
    roi = ((stake_value - member['paid_amount']) / member['paid_amount']) * 100

    conn.close()

    return {
        'founding_member_id': member['id'],
        'email': member['email'],
        'user_id': member['user_id'],
        'ownership_percentage': member['ownership_percentage'],
        'paid_amount': member['paid_amount'],
        'purchase_date': member['purchase_date'],
        'current_stake_value': round(stake_value, 2),
        'roi': round(roi, 2),
        'roi_multiple': round(stake_value / member['paid_amount'], 2)
    }


# ==============================================================================
# LEADERBOARD
# ==============================================================================

def get_founding_members_leaderboard(limit: int = 100) -> list:
    """
    Get founding members leaderboard (earliest members first)

    Args:
        limit: Number of members to return

    Returns:
        List of founding members sorted by purchase date
    """

    conn = get_db()

    members = conn.execute('''
        SELECT
            id,
            email,
            ownership_percentage,
            paid_amount,
            purchase_date
        FROM founding_members
        ORDER BY purchase_date ASC
        LIMIT ?
    ''', (limit,)).fetchall()

    conn.close()

    # Calculate stake values
    platform_valuation = 50000.0  # Placeholder

    leaderboard = []
    for i, member in enumerate(members, 1):
        stake_value = platform_valuation * (member['ownership_percentage'] / 100.0)
        roi = ((stake_value - member['paid_amount']) / member['paid_amount']) * 100

        leaderboard.append({
            'rank': i,
            'email': member['email'][:3] + '***@' + member['email'].split('@')[1] if '@' in member['email'] else 'anonymous',  # Privacy
            'ownership_percentage': member['ownership_percentage'],
            'paid_amount': member['paid_amount'],
            'purchase_date': member['purchase_date'],
            'current_stake_value': round(stake_value, 2),
            'roi': round(roi, 2)
        })

    return leaderboard


# ==============================================================================
# PROOF OF PURCHASE (NFT-STYLE)
# ==============================================================================

def generate_proof_of_purchase(founding_member_id: int) -> Dict:
    """
    Generate timestamped proof of purchase (like an NFT receipt)

    Args:
        founding_member_id: Founding member ID

    Returns:
        {
            'proof_id': str,
            'ownership_percentage': float,
            'timestamp': str,
            'transaction_hash': str,
            'verification_url': str
        }
    """

    conn = get_db()

    member = conn.execute(
        '''
        SELECT
            fm.*,
            p.transaction_id,
            p.payment_method
        FROM founding_members fm
        JOIN mvp_payments p ON fm.payment_id = p.id
        WHERE fm.id = ?
        ''',
        (founding_member_id,)
    ).fetchone()

    conn.close()

    if not member:
        return {'error': 'Founding member not found'}

    import hashlib

    # Generate proof hash
    proof_data = f"{member['id']}{member['email']}{member['purchase_date']}{member['transaction_id']}"
    proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

    # In production, could mint an actual NFT on blockchain
    # For now, generate verifiable proof

    return {
        'proof_id': proof_hash[:16],
        'founding_member_id': member['id'],
        'ownership_percentage': member['ownership_percentage'],
        'domain': 'soulfra.com',
        'timestamp': member['purchase_date'],
        'transaction_hash': member['transaction_id'],
        'payment_method': member['payment_method'],
        'verification_url': f'https://soulfra.com/mvp/verify/{proof_hash[:16]}',
        'proof_hash': proof_hash
    }


def verify_proof_of_purchase(proof_id: str) -> Optional[Dict]:
    """
    Verify proof of purchase

    Args:
        proof_id: Proof hash (first 16 chars)

    Returns:
        Founding member info if valid, None otherwise
    """

    conn = get_db()

    # Search for matching proof
    members = conn.execute('SELECT * FROM founding_members').fetchall()

    for member in members:
        # Regenerate hash
        payment = conn.execute(
            'SELECT transaction_id, payment_method FROM mvp_payments WHERE id = ?',
            (member['payment_id'],)
        ).fetchone()

        import hashlib
        proof_data = f"{member['id']}{member['email']}{member['purchase_date']}{payment['transaction_id']}"
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

        if proof_hash[:16] == proof_id:
            conn.close()
            return {
                'valid': True,
                'founding_member_id': member['id'],
                'email': member['email'],
                'ownership_percentage': member['ownership_percentage'],
                'purchase_date': member['purchase_date'],
                'proof_verified_at': datetime.utcnow().isoformat()
            }

    conn.close()
    return None


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing founding members tables...")
    init_founding_members_tables()
    print("✅ Founding members tables initialized")
    print()
    print("Features:")
    print("  - $1 payment → 0.1% ownership grant")
    print("  - Non-refundable by design")
    print("  - Timestamped proof of purchase")
    print("  - Digital booklet delivery")
    print("  - Leaderboard (earliest members first)")
    print("  - NFT-style proof verification")

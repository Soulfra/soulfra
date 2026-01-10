#!/usr/bin/env python3
"""
Idea Submission System - QR → Email Confirmation → Device Tracking

Complete user flow:
1. User scans QR code → lands on /submit-idea?theme=ocean-dreams
2. Fills out form (idea + email/phone)
3. System captures device fingerprint
4. Neural networks classify idea → route to brand
5. Pair device with domain → assign multiplier
6. Generate tracking ID
7. Send email/SMS confirmation
8. User can check status at /track/<id>

Connects:
- device_multiplier_system.py (device tracking + multipliers)
- neural_proxy.py (idea classification)
- emails.py (email confirmations)
- qr_faucet.py (QR code generation)

Philosophy:
----------
Make contributing FRICTIONLESS:
- Scan QR → 30 seconds to submit idea
- Email confirmation → feel heard
- Track progress → see impact
- Multipliers → reward loyalty
- No account required → lower barrier

The Loop:
---------
Submit idea → Get confirmation → Check progress →
See rewards → Submit more ideas → Multiplier increases → LOOP

Architecture:
------------
idea_submissions table
    ├── tracking_id (unique, shareable)
    ├── idea_text
    ├── user_email / user_phone
    ├── device_id (fingerprint)
    ├── theme / domain_slug
    ├── classified_as (technical/privacy/validation)
    ├── matched_brand_id
    ├── status (pending/reviewing/accepted/rejected)
    ├── multiplier_at_submission
    └── potential_rewards

Usage:
    from idea_submission_system import (
        submit_idea,
        get_submission_status,
        generate_idea_qr,
        send_confirmation_email
    )

    # When form submitted
    result = submit_idea(
        idea_text="Build privacy-first analytics",
        email="user@example.com",
        device_fingerprint=device_id,
        theme="ocean-dreams"
    )

    # Returns tracking_id → send email → show confirmation page
"""

import sqlite3
import secrets
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import hashlib

# Import existing systems
from device_multiplier_system import (
    get_device_fingerprint,
    pair_device_with_domain,
    get_device_multiplier,
    track_device_scan
)
from neural_proxy import classify_with_neural_network


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def create_idea_submission_tables():
    """Create tables for idea submissions"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idea_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE NOT NULL,
            idea_text TEXT NOT NULL,
            user_email TEXT,
            user_phone TEXT,
            device_id TEXT NOT NULL,
            device_fingerprint_data TEXT,
            theme TEXT,
            domain_slug TEXT,
            classified_as TEXT,
            classification_confidence REAL,
            matched_brand_id INTEGER,
            status TEXT DEFAULT 'pending',
            multiplier_at_submission REAL DEFAULT 1.0,
            potential_rewards REAL DEFAULT 0.0,
            actual_rewards REAL DEFAULT 0.0,
            ip_address TEXT,
            user_agent TEXT,
            confirmation_sent BOOLEAN DEFAULT 0,
            confirmation_sent_at TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewer_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (matched_brand_id) REFERENCES brands(id)
        )
    ''')

    # Idea comments/feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idea_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            feedback_type TEXT NOT NULL,
            feedback_text TEXT,
            given_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES idea_submissions(id)
        )
    ''')

    # Idea status history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idea_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_by TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES idea_submissions(id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Idea submission tables created!")


# ==============================================================================
# TRACKING ID GENERATION
# ==============================================================================

def generate_tracking_id() -> str:
    """
    Generate unique tracking ID for idea submission

    Format: IDEA-XXXXXX (6 random alphanumeric characters)

    Examples: IDEA-A3B9F2, IDEA-7K2P4L
    """
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Remove ambiguous: 0,O,1,I
    random_part = ''.join(secrets.choice(chars) for _ in range(6))
    return f"IDEA-{random_part}"


def ensure_unique_tracking_id() -> str:
    """Generate tracking ID and ensure it's unique in database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    max_attempts = 10
    for _ in range(max_attempts):
        tracking_id = generate_tracking_id()

        cursor.execute('''
            SELECT id FROM idea_submissions WHERE tracking_id = ?
        ''', (tracking_id,))

        if not cursor.fetchone():
            conn.close()
            return tracking_id

    conn.close()
    raise RuntimeError("Could not generate unique tracking ID after 10 attempts")


# ==============================================================================
# IDEA SUBMISSION
# ==============================================================================

def submit_idea(
    idea_text: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    device_fingerprint_data: Dict = None,
    theme: str = None,
    domain_slug: str = None
) -> Dict:
    """
    Submit an idea and create tracking record

    Args:
        idea_text: The idea description
        email: User's email for confirmation
        phone: User's phone for SMS confirmation
        device_fingerprint_data: Device info (IP, user agent, etc.)
        theme: Theme/category of idea
        domain_slug: Domain context (ocean-dreams, calriven, etc.)

    Returns:
        Dict with submission info and tracking_id
    """
    if not idea_text or len(idea_text.strip()) < 10:
        return {
            'success': False,
            'error': 'Idea must be at least 10 characters'
        }

    if not email and not phone:
        return {
            'success': False,
            'error': 'Email or phone required for confirmation'
        }

    # Generate device fingerprint
    device_id = get_device_fingerprint(device_fingerprint_data or {})

    # Pair device with domain (if specified)
    if domain_slug:
        pair_device_with_domain(device_id, domain_slug)

    # Get current multiplier
    multiplier = get_device_multiplier(device_id, domain_slug)

    # Classify idea with neural networks
    classification = classify_with_neural_network(idea_text)

    # Match to brand based on classification
    brand_mapping = {
        'technical': 4,      # CalRiven
        'privacy': 5,        # Privacy Guard
        'validation': 6,     # The Auditor
    }
    matched_brand_id = brand_mapping.get(classification['classification'], None)

    # Generate unique tracking ID
    tracking_id = ensure_unique_tracking_id()

    # Calculate potential rewards
    base_rewards = 50.0  # Base tokens for idea submission
    potential_rewards = base_rewards * multiplier

    # Save to database
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO idea_submissions (
            tracking_id, idea_text, user_email, user_phone,
            device_id, device_fingerprint_data,
            theme, domain_slug,
            classified_as, classification_confidence, matched_brand_id,
            multiplier_at_submission, potential_rewards,
            ip_address, user_agent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tracking_id,
        idea_text,
        email,
        phone,
        device_id,
        json.dumps(device_fingerprint_data) if device_fingerprint_data else None,
        theme,
        domain_slug,
        classification['classification'],
        classification['confidence'],
        matched_brand_id,
        multiplier,
        potential_rewards,
        device_fingerprint_data.get('ip_address') if device_fingerprint_data else None,
        device_fingerprint_data.get('user_agent') if device_fingerprint_data else None
    ))

    submission_id = cursor.lastrowid

    # Log status history
    cursor.execute('''
        INSERT INTO idea_status_history (submission_id, new_status, reason)
        VALUES (?, 'pending', 'Idea submitted')
    ''', (submission_id,))

    conn.commit()
    conn.close()

    # Track device scan
    if domain_slug:
        track_device_scan(
            device_id,
            domain_slug=domain_slug,
            brand_id=matched_brand_id,
            request_data=device_fingerprint_data or {}
        )

    print(f"✅ Idea submitted: {tracking_id}")

    return {
        'success': True,
        'tracking_id': tracking_id,
        'submission_id': submission_id,
        'classified_as': classification['classification'],
        'confidence': classification['confidence'],
        'matched_brand': matched_brand_id,
        'multiplier': multiplier,
        'potential_rewards': potential_rewards,
        'email': email,
        'phone': phone
    }


# ==============================================================================
# STATUS TRACKING
# ==============================================================================

def get_submission_status(tracking_id: str) -> Optional[Dict]:
    """
    Get status of idea submission

    Args:
        tracking_id: Tracking ID (e.g., IDEA-A3B9F2)

    Returns:
        Dict with submission info and status
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.*, b.name as brand_name, b.slug as brand_slug
        FROM idea_submissions s
        LEFT JOIN brands b ON s.matched_brand_id = b.id
        WHERE s.tracking_id = ?
    ''', (tracking_id,))

    submission = cursor.fetchone()

    if not submission:
        conn.close()
        return None

    submission_dict = dict(submission)

    # Get status history
    cursor.execute('''
        SELECT * FROM idea_status_history
        WHERE submission_id = ?
        ORDER BY created_at DESC
    ''', (submission_dict['id'],))

    history = [dict(h) for h in cursor.fetchall()]

    # Get feedback
    cursor.execute('''
        SELECT * FROM idea_feedback
        WHERE submission_id = ?
        ORDER BY created_at DESC
    ''', (submission_dict['id'],))

    feedback = [dict(f) for f in cursor.fetchall()]

    conn.close()

    submission_dict['history'] = history
    submission_dict['feedback'] = feedback

    return submission_dict


def update_submission_status(
    tracking_id: str,
    new_status: str,
    changed_by: str = 'system',
    reason: str = None,
    rewards: float = None
) -> bool:
    """
    Update status of idea submission

    Args:
        tracking_id: Tracking ID
        new_status: New status (pending/reviewing/accepted/rejected)
        changed_by: Who changed it
        reason: Reason for change
        rewards: Actual rewards if accepted

    Returns:
        True if updated successfully
    """
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get current status
    cursor.execute('''
        SELECT id, status FROM idea_submissions
        WHERE tracking_id = ?
    ''', (tracking_id,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return False

    submission_id, old_status = result

    # Update submission
    update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
    update_values = [new_status]

    if rewards is not None:
        update_fields.append('actual_rewards = ?')
        update_values.append(rewards)

    if new_status == 'accepted':
        update_fields.append('reviewed_at = CURRENT_TIMESTAMP')

    update_sql = f'''
        UPDATE idea_submissions
        SET {', '.join(update_fields)}
        WHERE id = ?
    '''
    update_values.append(submission_id)

    cursor.execute(update_sql, update_values)

    # Log status change
    cursor.execute('''
        INSERT INTO idea_status_history (
            submission_id, old_status, new_status, changed_by, reason
        ) VALUES (?, ?, ?, ?, ?)
    ''', (submission_id, old_status, new_status, changed_by, reason))

    conn.commit()
    conn.close()

    print(f"✅ Updated {tracking_id}: {old_status} → {new_status}")

    return True


def add_feedback(
    tracking_id: str,
    feedback_type: str,
    feedback_text: str,
    given_by: str = 'system'
) -> bool:
    """Add feedback to idea submission"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM idea_submissions WHERE tracking_id = ?
    ''', (tracking_id,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return False

    submission_id = result[0]

    cursor.execute('''
        INSERT INTO idea_feedback (
            submission_id, feedback_type, feedback_text, given_by
        ) VALUES (?, ?, ?, ?)
    ''', (submission_id, feedback_type, feedback_text, given_by))

    conn.commit()
    conn.close()

    return True


# ==============================================================================
# STATISTICS
# ==============================================================================

def get_submission_stats() -> Dict:
    """Get overall submission statistics"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    stats = {}

    # Total submissions
    cursor.execute('SELECT COUNT(*) FROM idea_submissions')
    stats['total_submissions'] = cursor.fetchone()[0]

    # By status
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM idea_submissions
        GROUP BY status
    ''')
    stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

    # By classification
    cursor.execute('''
        SELECT classified_as, COUNT(*) as count
        FROM idea_submissions
        GROUP BY classified_as
    ''')
    stats['by_classification'] = {row[0]: row[1] for row in cursor.fetchall()}

    # By brand
    cursor.execute('''
        SELECT b.name, COUNT(*) as count
        FROM idea_submissions s
        JOIN brands b ON s.matched_brand_id = b.id
        GROUP BY b.id
    ''')
    stats['by_brand'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Total potential rewards
    cursor.execute('SELECT SUM(potential_rewards) FROM idea_submissions')
    stats['total_potential_rewards'] = cursor.fetchone()[0] or 0.0

    # Total actual rewards
    cursor.execute('SELECT SUM(actual_rewards) FROM idea_submissions WHERE status = "accepted"')
    stats['total_actual_rewards'] = cursor.fetchone()[0] or 0.0

    conn.close()

    return stats


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Idea Submission System')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--submit', nargs=3, metavar=('TEXT', 'EMAIL', 'THEME'), help='Submit idea')
    parser.add_argument('--status', metavar='TRACKING_ID', help='Check status')
    parser.add_argument('--stats', action='store_true', help='Show statistics')

    args = parser.parse_args()

    if args.init:
        create_idea_submission_tables()

    elif args.submit:
        text, email, theme = args.submit
        result = submit_idea(
            idea_text=text,
            email=email,
            theme=theme,
            device_fingerprint_data={'ip_address': '127.0.0.1', 'user_agent': 'CLI Test'}
        )
        print(json.dumps(result, indent=2))

    elif args.status:
        status = get_submission_status(args.status)
        if status:
            print(json.dumps(status, indent=2, default=str))
        else:
            print(f"Tracking ID {args.status} not found")

    elif args.stats:
        stats = get_submission_stats()
        print(json.dumps(stats, indent=2))

    else:
        print("Idea Submission System")
        print()
        print("Usage:")
        print("  --init                                 Initialize database")
        print('  --submit "idea text" email@x.com theme Submit idea')
        print("  --status IDEA-ABC123                   Check status")
        print("  --stats                                Show statistics")
        print()
        print("Examples:")
        print("  python3 idea_submission_system.py --init")
        print('  python3 idea_submission_system.py --submit "Privacy-first analytics" user@example.com privacy')
        print("  python3 idea_submission_system.py --status IDEA-ABC123")

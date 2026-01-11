#!/usr/bin/env python3
"""
Email Outbox System - Internal Mailbox for StPetePros

Instead of sending emails immediately, save them to database first.
This allows:
1. Review emails before sending (like Resend's test system)
2. Prove emails work without spamming
3. Token-gated actual sending
4. View all emails in dashboard

Usage:
    from email_outbox import save_to_outbox, send_from_outbox

    # Save email (doesn't send)
    email_id = save_to_outbox(
        to="professional@example.com",
        subject="Welcome!",
        body_html="<h1>Hello</h1>",
        recovery_code="clearwater-plumber-trusted-4821",
        professional_id=18
    )

    # Later: Send email (costs tokens)
    send_from_outbox(email_id, user_id=1)
"""

import sqlite3
import json
import base64
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent / 'soulfra.db'


def save_to_outbox(to, subject, body_html, body_text=None, from_address=None,
                   recovery_code=None, professional_id=None, qr_bytes=None):
    """
    Save email to outbox (doesn't send yet).

    Returns:
        int: Email ID in outbox table
    """

    if not from_address:
        from_address = 'StPetePros <noreply@soulfra.com>'

    # Prepare attachments if QR code provided
    attachments_json = None
    if qr_bytes:
        attachments = [{
            'filename': 'qr-code.png',
            'content': base64.b64encode(qr_bytes).decode(),
            'mime_type': 'image/png'
        }]
        attachments_json = json.dumps(attachments)

    # Save to database
    db = sqlite3.connect(DB_PATH)
    cursor = db.execute('''
        INSERT INTO email_outbox (
            to_address, from_address, subject,
            body_html, body_text, attachments,
            professional_id, recovery_code,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queued', CURRENT_TIMESTAMP)
    ''', (
        to, from_address, subject,
        body_html, body_text, attachments_json,
        professional_id, recovery_code
    ))

    email_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"📧 Email saved to outbox (ID: {email_id})")
    print(f"   To: {to}")
    print(f"   Subject: {subject}")
    print(f"   View at: http://localhost:5001/dashboard/outbox/{email_id}")

    return email_id


def send_from_outbox(email_id, user_id=None):
    """
    Actually send an email from outbox.

    Args:
        email_id: ID in email_outbox table
        user_id: User sending email (for token deduction)

    Returns:
        bool: True if sent successfully
    """

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Get email from outbox
    email = db.execute('''
        SELECT * FROM email_outbox WHERE id = ?
    ''', (email_id,)).fetchone()

    if not email:
        print(f"❌ Email {email_id} not found in outbox")
        db.close()
        return False

    if email['status'] == 'sent':
        print(f"⚠️  Email {email_id} already sent at {email['sent_at']}")
        db.close()
        return True

    # Check user has tokens (if user_id provided)
    if user_id:
        user = db.execute('SELECT token_balance FROM users WHERE id = ?', (user_id,)).fetchone()
        if user and user['token_balance'] < email['token_cost']:
            print(f"❌ Insufficient tokens. Need {email['token_cost']}, have {user['token_balance']}")
            db.close()
            return False

    # Mark as sending
    db.execute('''
        UPDATE email_outbox
        SET status = 'sending'
        WHERE id = ?
    ''', (email_id,))
    db.commit()

    try:
        # Import email sender
        from email_sender import send_via_sendmail, send_via_resend
        import os

        # Parse attachments
        qr_bytes = None
        if email['attachments']:
            attachments = json.loads(email['attachments'])
            for att in attachments:
                if att['filename'] == 'qr-code.png':
                    qr_bytes = base64.b64decode(att['content'])

        # Try sending
        if os.environ.get('RESEND_API_KEY'):
            success = send_via_resend(
                email['to_address'],
                email['subject'],
                email['body_html'],
                email['body_text'],
                qr_bytes
            )
        else:
            success = send_via_sendmail(
                email['to_address'],
                email['subject'],
                email['body_html'],
                email['body_text'],
                qr_bytes
            )

        if success:
            # Mark as sent
            db.execute('''
                UPDATE email_outbox
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (email_id,))

            # Deduct tokens if user_id provided
            if user_id:
                db.execute('''
                    UPDATE users
                    SET token_balance = token_balance - ?
                    WHERE id = ?
                ''', (email['token_cost'], user_id))

                db.execute('''
                    UPDATE email_outbox
                    SET sent_by_user_id = ?
                    WHERE id = ?
                ''', (user_id, email_id))

                # Log token transaction
                db.execute('''
                    INSERT INTO token_transactions (user_id, amount, transaction_type, description)
                    VALUES (?, ?, 'debit', ?)
                ''', (user_id, -email['token_cost'], f'Sent email to {email["to_address"]}'))

            db.commit()
            print(f"✅ Email sent successfully!")
            print(f"   To: {email['to_address']}")
            print(f"   Tokens deducted: {email['token_cost']}")
            db.close()
            return True

        else:
            raise Exception("Email send failed")

    except Exception as e:
        print(f"❌ Error sending email: {e}")

        # Mark as failed
        db.execute('''
            UPDATE email_outbox
            SET status = 'failed', error_message = ?
            WHERE id = ?
        ''', (str(e), email_id))
        db.commit()
        db.close()
        return False


def get_outbox_emails(status=None, limit=50):
    """
    Get emails from outbox.

    Args:
        status: Filter by status ('draft', 'queued', 'sent', 'failed')
        limit: Max number of emails to return

    Returns:
        list: Email dictionaries
    """

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    if status:
        emails = db.execute('''
            SELECT * FROM email_outbox
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (status, limit)).fetchall()
    else:
        emails = db.execute('''
            SELECT * FROM email_outbox
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    db.close()

    return [dict(email) for email in emails]


def delete_from_outbox(email_id):
    """Delete email from outbox"""

    db = sqlite3.connect(DB_PATH)
    db.execute('DELETE FROM email_outbox WHERE id = ?', (email_id,))
    db.commit()
    db.close()

    print(f"🗑️  Email {email_id} deleted from outbox")


if __name__ == "__main__":
    # Test saving to outbox
    print("Testing Email Outbox System...\n")

    # Create test email
    email_id = save_to_outbox(
        to="test@example.com",
        subject="Test Email",
        body_html="<h1>Test</h1><p>This is a test email in outbox.</p>",
        body_text="Test - This is a test email in outbox.",
        recovery_code="test-code-1234",
        professional_id=999
    )

    print(f"\n✅ Email saved with ID: {email_id}")
    print("\nView outbox emails:")
    print(f"  GET /dashboard/outbox")
    print(f"  GET /api/outbox")

    print("\nTo send this email:")
    print(f"  send_from_outbox({email_id}, user_id=1)")

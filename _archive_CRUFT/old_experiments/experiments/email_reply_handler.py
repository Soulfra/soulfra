#!/usr/bin/env python3
"""
Email Reply Handler - Convert Newsletter Email Replies to Comments

Automatically converts email replies from freelancers into comments on posts.

Flow:
1. User receives newsletter with post digest
2. User replies to email (email contains In-Reply-To header with post ID)
3. Email is received by system (via webhook or IMAP polling)
4. System parses email, extracts content
5. Creates comment on original post
6. Sends confirmation email to user

Usage:
    # Process incoming email
    from email_reply_handler import process_inbound_email

    process_inbound_email(
        from_email="freelancer@example.com",
        subject="Re: [CalRiven] New Post: Building Privacy Tools",
        body="Great idea! I'd love to contribute...",
        in_reply_to="post-42@soulfra.com",
        received_at="2025-12-24 12:00:00"
    )
"""

import sqlite3
import re
from datetime import datetime
from typing import Dict, Optional, List
from database import get_db
from db_helpers import add_comment, get_user_by_email


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def create_inbound_email_tables():
    """Create tables for email reply handling"""
    conn = get_db()

    # Inbound Emails table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inbound_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_email TEXT NOT NULL,
            to_email TEXT,
            subject TEXT,
            body_text TEXT,
            body_html TEXT,
            in_reply_to TEXT,
            message_id TEXT UNIQUE,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT 0,
            processed_at TIMESTAMP,
            post_id INTEGER,
            comment_id INTEGER,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Indexes
    conn.execute('CREATE INDEX IF NOT EXISTS idx_inbound_emails_from ON inbound_emails(from_email)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_inbound_emails_processed ON inbound_emails(processed)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_inbound_emails_post ON inbound_emails(post_id)')

    conn.commit()
    conn.close()

    print("✅ Inbound email tables created!")


# ==============================================================================
# EMAIL PARSING
# ==============================================================================

def extract_post_id_from_reference(reference: str) -> Optional[int]:
    """
    Extract post ID from email reference header

    Supports formats:
    - post-42@soulfra.com → 42
    - <post-123@soulfra.com> → 123
    - post-456 → 456

    Args:
        reference: In-Reply-To or References header value

    Returns:
        Post ID as integer or None
    """
    if not reference:
        return None

    # Remove angle brackets
    reference = reference.strip('<>')

    # Match post-123 pattern
    match = re.search(r'post-(\d+)', reference, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def clean_email_body(body: str, strip_quoted: bool = True) -> str:
    """
    Clean email body for use as comment

    - Removes email signatures
    - Removes quoted text (lines starting with >)
    - Removes excessive whitespace
    - Removes "On DATE, PERSON wrote:" headers

    Args:
        body: Raw email body text
        strip_quoted: Remove quoted text from replies

    Returns:
        Cleaned comment text
    """
    if not body:
        return ""

    lines = body.split('\n')
    cleaned_lines = []

    signature_markers = [
        '-- ',
        '---',
        'Sent from my',
        'Get Outlook for',
        'Sent from ',
        '________________________________'
    ]

    in_signature = False

    for line in lines:
        # Skip signature
        if any(line.strip().startswith(marker) for marker in signature_markers):
            in_signature = True
            continue

        if in_signature:
            continue

        # Skip quoted text
        if strip_quoted and line.strip().startswith('>'):
            continue

        # Skip "On DATE, PERSON wrote:" headers
        if re.match(r'^On .+wrote:$', line.strip()):
            continue

        cleaned_lines.append(line)

    # Join and clean whitespace
    cleaned = '\n'.join(cleaned_lines).strip()

    # Remove excessive blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned


# ==============================================================================
# EMAIL PROCESSING
# ==============================================================================

def process_inbound_email(
    from_email: str,
    subject: str,
    body_text: str,
    in_reply_to: Optional[str] = None,
    message_id: Optional[str] = None,
    to_email: Optional[str] = None,
    body_html: Optional[str] = None,
    received_at: Optional[str] = None
) -> Dict:
    """
    Process inbound email and convert to comment

    Args:
        from_email: Sender email address
        subject: Email subject
        body_text: Plain text email body
        in_reply_to: In-Reply-To header (contains post ID reference)
        message_id: Unique message ID
        to_email: Recipient email
        body_html: HTML email body
        received_at: Timestamp email was received

    Returns:
        {
            'success': True,
            'comment_id': 123,
            'post_id': 42,
            'email_id': 1
        }
    """
    conn = get_db()

    # Extract post ID from reference
    post_id = extract_post_id_from_reference(in_reply_to)

    if not post_id:
        # Try extracting from subject (e.g., "Re: Post #42 - Title")
        match = re.search(r'#(\d+)', subject)
        if match:
            post_id = int(match.group(1))

    # Clean email body
    comment_text = clean_email_body(body_text)

    if not comment_text:
        error = "Email body is empty after cleaning"
        conn.execute('''
            INSERT INTO inbound_emails (
                from_email, to_email, subject, body_text, body_html,
                in_reply_to, message_id, received_at, processed, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        ''', (from_email, to_email, subject, body_text, body_html, in_reply_to, message_id, received_at, error))
        conn.commit()
        conn.close()

        return {
            'success': False,
            'error': error
        }

    # Get user by email
    user = get_user_by_email(from_email)

    if not user:
        error = f"User not found for email: {from_email}"
        conn.execute('''
            INSERT INTO inbound_emails (
                from_email, to_email, subject, body_text, body_html,
                in_reply_to, message_id, received_at, processed, error_message, post_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        ''', (from_email, to_email, subject, body_text, body_html, in_reply_to, message_id, received_at, error, post_id))
        conn.commit()
        conn.close()

        return {
            'success': False,
            'error': error,
            'post_id': post_id
        }

    user_id = user['id']

    # Create comment
    try:
        comment_id = add_comment(
            post_id=post_id,
            user_id=user_id,
            content=comment_text
        )

        # Log email as processed
        conn.execute('''
            INSERT INTO inbound_emails (
                from_email, to_email, subject, body_text, body_html,
                in_reply_to, message_id, received_at, processed, processed_at,
                post_id, comment_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
        ''', (from_email, to_email, subject, body_text, body_html, in_reply_to, message_id, received_at, post_id, comment_id))

        conn.commit()
        email_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        print(f"✅ Email converted to comment! ID={comment_id}, Post={post_id}, Email={email_id}")

        # Send confirmation email (optional)
        send_comment_confirmation_email(from_email, post_id, comment_id)

        return {
            'success': True,
            'comment_id': comment_id,
            'post_id': post_id,
            'email_id': email_id
        }

    except Exception as e:
        error = f"Failed to create comment: {str(e)}"
        conn.execute('''
            INSERT INTO inbound_emails (
                from_email, to_email, subject, body_text, body_html,
                in_reply_to, message_id, received_at, processed, error_message, post_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        ''', (from_email, to_email, subject, body_text, body_html, in_reply_to, message_id, received_at, error, post_id))
        conn.commit()
        conn.close()

        return {
            'success': False,
            'error': error,
            'post_id': post_id
        }


def send_comment_confirmation_email(email: str, post_id: int, comment_id: int):
    """
    Send confirmation email that comment was posted

    Args:
        email: User's email address
        post_id: Post ID
        comment_id: Comment ID
    """
    from email_server import queue_email

    subject = f"✅ Your comment was posted!"

    body = f"""
Hi there!

Your email reply was successfully converted to a comment!

📝 Post: #{post_id}
💬 Comment ID: {comment_id}

View your comment: http://localhost:5001/post/{post_id}#comment-{comment_id}

Thanks for engaging with the community!

---
Soulfra Platform
    """.strip()

    queue_email(
        to_email=email,
        subject=subject,
        body=body
    )


# ==============================================================================
# EMAIL MONITORING & STATS
# ==============================================================================

def get_inbound_email_stats() -> Dict:
    """
    Get statistics on inbound emails

    Returns:
        {
            'total_emails': 42,
            'processed': 35,
            'pending': 7,
            'success_rate': 0.83,
            'comments_created': 35,
            'top_senders': [...]
        }
    """
    conn = get_db()

    # Total emails
    total = conn.execute('SELECT COUNT(*) as count FROM inbound_emails').fetchone()['count']

    # Processed vs pending
    processed = conn.execute('SELECT COUNT(*) as count FROM inbound_emails WHERE processed = 1').fetchone()['count']
    pending = total - processed

    # Comments created
    comments = conn.execute('SELECT COUNT(*) as count FROM inbound_emails WHERE comment_id IS NOT NULL').fetchone()['count']

    # Success rate
    success_rate = comments / total if total > 0 else 0

    # Top senders
    top_senders = conn.execute('''
        SELECT from_email, COUNT(*) as count
        FROM inbound_emails
        WHERE comment_id IS NOT NULL
        GROUP BY from_email
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()

    conn.close()

    return {
        'total_emails': total,
        'processed': processed,
        'pending': pending,
        'comments_created': comments,
        'success_rate': success_rate,
        'top_senders': [dict(s) for s in top_senders]
    }


def get_unprocessed_emails() -> List[Dict]:
    """
    Get list of unprocessed emails

    Returns:
        List of email dicts
    """
    conn = get_db()

    emails = conn.execute('''
        SELECT * FROM inbound_emails
        WHERE processed = 0
        ORDER BY received_at DESC
        LIMIT 100
    ''').fetchall()

    conn.close()

    return [dict(e) for e in emails]


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Email Reply Handler')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--test', action='store_true', help='Test email processing')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--pending', action='store_true', help='Show pending emails')

    args = parser.parse_args()

    if args.init:
        create_inbound_email_tables()

    elif args.test:
        print("\n🧪 Testing email processing...\n")

        result = process_inbound_email(
            from_email="test@example.com",
            subject="Re: [CalRiven] Post #1 - Building Privacy Tools",
            body_text="""
This is a great idea! I'd love to contribute to this project.

Let me know how I can help.

Best,
Test User

--
Sent from my iPhone
            """,
            in_reply_to="<post-1@soulfra.com>",
            message_id="test-message-123@gmail.com"
        )

        if result['success']:
            print(f"✅ Success!")
            print(f"   Comment ID: {result['comment_id']}")
            print(f"   Post ID: {result['post_id']}")
            print(f"   Email ID: {result['email_id']}")
        else:
            print(f"❌ Failed: {result['error']}")

    elif args.stats:
        stats = get_inbound_email_stats()
        print("\n📊 Email Reply Statistics:")
        print(f"   Total Emails: {stats['total_emails']}")
        print(f"   Processed: {stats['processed']}")
        print(f"   Pending: {stats['pending']}")
        print(f"   Comments Created: {stats['comments_created']}")
        print(f"   Success Rate: {stats['success_rate']:.1%}")

        if stats['top_senders']:
            print("\n   Top Senders:")
            for sender in stats['top_senders']:
                print(f"      {sender['from_email']}: {sender['count']} comments")

    elif args.pending:
        emails = get_unprocessed_emails()
        print(f"\n📥 Pending Emails ({len(emails)}):\n")

        for email in emails:
            print(f"   From: {email['from_email']}")
            print(f"   Subject: {email['subject']}")
            print(f"   Received: {email['received_at']}")
            print(f"   Error: {email['error_message'] or 'None'}")
            print()

    else:
        print("Email Reply Handler")
        print()
        print("Usage:")
        print("  --init     Initialize database tables")
        print("  --test     Test email processing")
        print("  --stats    Show statistics")
        print("  --pending  Show pending emails")
        print()
        print("Example:")
        print("  python3 email_reply_handler.py --init")

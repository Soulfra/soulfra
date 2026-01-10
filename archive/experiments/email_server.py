#!/usr/bin/env python3
"""
Built-in Email Queue - Offline-First Email System

This implements a local email queue that:
1. Stores emails locally (database + .eml files)
2. Queues for later sending when online
3. Provides email preview/viewing
4. No SMTP server needed - direct API

WHY THIS EXISTS:
- Work completely offline
- Preview emails before sending
- Queue emails to send later
- No external SMTP dependencies
- All emails are auditable locally

Usage:
    # Queue an email
    from email_server import queue_email
    queue_email(
        from_addr='noreply@soulfra.local',
        to_addrs=['user@example.com'],
        subject='Test Email',
        body='Hello world',
        html_body='<p>Hello world</p>'
    )

    # View queued emails
    python3 email_server.py list

    # Send queued emails
    python3 email_server.py send --dry-run
"""

import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
from pathlib import Path


def _get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def _init_database():
    """Initialize email storage tables"""
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outbound_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_addr TEXT NOT NULL,
            to_addrs TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            html_body TEXT,
            raw_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'queued',
            send_attempts INTEGER DEFAULT 0,
            last_error TEXT,
            sent_at TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def queue_email(from_addr, to_addrs, subject, body, html_body=None):
    """
    Queue an email for sending

    Args:
        from_addr: Sender email address
        to_addrs: List of recipient email addresses
        subject: Email subject
        body: Plain text body
        html_body: HTML body (optional)

    Returns:
        email_id: ID of queued email
    """
    _init_database()

    # Create email message
    if html_body:
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
    else:
        msg = MIMEText(body, 'plain')

    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs) if isinstance(to_addrs, list) else to_addrs

    raw_email = msg.as_string()

    # Ensure to_addrs is list
    if isinstance(to_addrs, str):
        to_addrs = [to_addrs]

    # Store in database
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO outbound_emails
        (from_addr, to_addrs, subject, body, html_body, raw_email, status)
        VALUES (?, ?, ?, ?, ?, ?, 'queued')
    ''', (
        from_addr,
        json.dumps(to_addrs),
        subject,
        body,
        html_body,
        raw_email
    ))

    email_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Save .eml file
    email_dir = Path('emails')
    email_dir.mkdir(exist_ok=True)

    eml_path = email_dir / f"{email_id}.eml"
    with open(eml_path, 'w') as f:
        f.write(raw_email)

    # Save JSON representation
    json_path = email_dir / f"{email_id}.json"
    email_json = {
        'id': email_id,
        'from': from_addr,
        'to': to_addrs,
        'subject': subject,
        'body': body,
        'html_body': html_body,
        'created_at': datetime.now().isoformat(),
        'status': 'queued'
    }

    with open(json_path, 'w') as f:
        json.dump(email_json, f, indent=2)

    print(f"📧 Queued email #{email_id}: {subject}")

    return email_id


def send_queued_emails(dry_run=True, smtp_config=None):
    """
    Send queued emails to real SMTP server

    Args:
        dry_run: If True, just preview what would be sent
        smtp_config: Dict with SMTP settings {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'user@gmail.com',
            'password': 'app_password'
        }
    """
    import smtplib

    conn = _get_db()
    cursor = conn.cursor()

    # Get queued emails
    queued = cursor.execute('''
        SELECT * FROM outbound_emails
        WHERE status = 'queued'
        ORDER BY created_at
    ''').fetchall()

    print("=" * 70)
    print(f"📬 Queued Emails: {len(queued)}")
    print("=" * 70)
    print()

    if not queued:
        print("   No emails in queue")
        conn.close()
        return

    if dry_run:
        print("   DRY RUN MODE - Not actually sending")
        print()

        for email_row in queued:
            print(f"   Email #{email_row['id']}")
            print(f"   From: {email_row['from_addr']}")
            print(f"   To: {', '.join(json.loads(email_row['to_addrs']))}")
            print(f"   Subject: {email_row['subject']}")
            print(f"   Body: {email_row['body'][:100]}...")
            print()
    else:
        if not smtp_config:
            print("   ❌ SMTP config required for real sending")
            print("   Configure SMTP settings or use --dry-run")
            conn.close()
            return

        print(f"   Connecting to {smtp_config['host']}:{smtp_config['port']}...")

        try:
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])

            sent_count = 0
            failed_count = 0

            for email_row in queued:
                try:
                    to_addrs = json.loads(email_row['to_addrs'])
                    server.sendmail(
                        email_row['from_addr'],
                        to_addrs,
                        email_row['raw_email']
                    )

                    # Mark as sent
                    cursor.execute('''
                        UPDATE outbound_emails
                        SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (email_row['id'],))

                    print(f"   ✅ Sent #{email_row['id']}: {email_row['subject']}")
                    sent_count += 1

                except Exception as e:
                    # Mark as failed
                    cursor.execute('''
                        UPDATE outbound_emails
                        SET status = 'failed',
                            send_attempts = send_attempts + 1,
                            last_error = ?
                        WHERE id = ?
                    ''', (str(e), email_row['id']))

                    print(f"   ❌ Failed #{email_row['id']}: {e}")
                    failed_count += 1

            server.quit()
            conn.commit()

            print()
            print(f"   📊 Results: {sent_count} sent, {failed_count} failed")

        except Exception as e:
            print(f"   ❌ SMTP Error: {e}")

    conn.close()


def view_email(email_id):
    """View a specific email by ID"""
    conn = _get_db()
    cursor = conn.cursor()

    email_row = cursor.execute(
        'SELECT * FROM outbound_emails WHERE id = ?',
        (email_id,)
    ).fetchone()

    conn.close()

    if not email_row:
        print(f"❌ Email #{email_id} not found")
        return

    print("=" * 70)
    print(f"📧 Email #{email_id}")
    print("=" * 70)
    print()
    print(f"From:    {email_row['from_addr']}")
    print(f"To:      {', '.join(json.loads(email_row['to_addrs']))}")
    print(f"Subject: {email_row['subject']}")
    print(f"Created: {email_row['created_at']}")
    print(f"Status:  {email_row['status']}")

    if email_row['sent_at']:
        print(f"Sent:    {email_row['sent_at']}")

    if email_row['last_error']:
        print(f"Error:   {email_row['last_error']}")

    print()
    print("=" * 70)
    print("BODY:")
    print("=" * 70)
    print(email_row['body'])
    print("=" * 70)


def list_emails(status=None, limit=10):
    """List recent emails"""
    _init_database()

    conn = _get_db()
    cursor = conn.cursor()

    if status:
        emails = cursor.execute('''
            SELECT id, from_addr, subject, created_at, status
            FROM outbound_emails
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (status, limit)).fetchall()
    else:
        emails = cursor.execute('''
            SELECT id, from_addr, subject, created_at, status
            FROM outbound_emails
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    conn.close()

    print("=" * 70)
    print(f"📬 Recent Emails (limit {limit})")
    print("=" * 70)
    print()

    if not emails:
        print("   No emails found")
        return

    for email_row in emails:
        status_icon = {
            'queued': '📥',
            'sent': '✅',
            'failed': '❌'
        }.get(email_row['status'], '❓')

        print(f"{status_icon} #{email_row['id']}: {email_row['subject'][:50]}")
        print(f"   From: {email_row['from_addr']}")
        print(f"   {email_row['created_at']} | {email_row['status']}")
        print()


def test_queue():
    """Test the email queue by creating a test email"""
    print("=" * 70)
    print("📧 Testing Email Queue")
    print("=" * 70)
    print()

    email_id = queue_email(
        from_addr='noreply@soulfra.local',
        to_addrs=['test@example.com', 'admin@example.com'],
        subject='Test Email from Soulfra',
        body='This is a test email from the offline-first email system.',
        html_body='<h1>Test Email</h1><p>This is a test email from the <strong>offline-first</strong> email system.</p>'
    )

    print()
    print(f"✅ Email #{email_id} queued successfully")
    print()
    print("📁 Files created:")
    print(f"   emails/{email_id}.eml")
    print(f"   emails/{email_id}.json")
    print()
    print("💡 View with: python3 email_server.py view {email_id}")
    print("💡 List all: python3 email_server.py list")
    print()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            status = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            list_emails(status, limit)

        elif command == 'view':
            if len(sys.argv) < 3:
                print("Usage: python3 email_server.py view <email_id>")
                sys.exit(1)
            email_id = int(sys.argv[2])
            view_email(email_id)

        elif command == 'send':
            dry_run = '--dry-run' in sys.argv or len(sys.argv) == 2
            send_queued_emails(dry_run=dry_run)

        elif command == 'test':
            test_queue()

        else:
            print(f"Unknown command: {command}")
            print()
            print("Available commands:")
            print("  python3 email_server.py test              # Queue a test email")
            print("  python3 email_server.py list [status] [limit]")
            print("  python3 email_server.py view <id>")
            print("  python3 email_server.py send [--dry-run]")
            sys.exit(1)
    else:
        print("=" * 70)
        print("📧 Offline-First Email Queue")
        print("=" * 70)
        print()
        print("This is a simple email queue for offline-first development.")
        print("Emails are stored locally and can be sent when online.")
        print()
        print("Commands:")
        print("  python3 email_server.py test              # Queue a test email")
        print("  python3 email_server.py list [status]     # List emails")
        print("  python3 email_server.py view <id>         # View email")
        print("  python3 email_server.py send [--dry-run]  # Send queued emails")
        print()
        print("Usage in code:")
        print("  from email_server import queue_email")
        print("  queue_email(from_addr, to_addrs, subject, body, html_body)")
        print()
        print("=" * 70)

#!/usr/bin/env python3
"""
Newsletter Routes - Email newsletter system for Soulfra

Features:
- Subscribe/unsubscribe to brand newsletters
- Send email digests of blog posts
- Scrape Calriven feed → generate emails
- GDPR-compliant (opt-in only, easy unsubscribe)

Routes:
- POST /api/newsletter/subscribe - Subscribe to brand newsletter
- POST /api/newsletter/unsubscribe - Unsubscribe from newsletter
- POST /api/newsletter/send - Send newsletter to subscribers (admin only)
- GET /api/newsletter/subscriptions - Get user's subscriptions

Database Tables:
- newsletters - Sent newsletters (subject, content, sent_at)
- newsletter_subscriptions - User subscriptions (user_id, brand_id)
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from datetime import datetime, timezone, timedelta
from simple_emailer import send_email
import markdown2

newsletter_bp = Blueprint('newsletter', __name__)


def init_newsletter_tables():
    """
    Initialize newsletter database tables
    """
    db = get_db()

    # Table: newsletters (sent newsletter history)
    db.execute('''
        CREATE TABLE IF NOT EXISTS newsletters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            html_content TEXT,
            sent_at TEXT NOT NULL,
            recipient_count INTEGER DEFAULT 0,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')

    # Table: newsletter_subscriptions (user newsletter subscriptions)
    db.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand_id INTEGER NOT NULL,
            subscribed_at TEXT NOT NULL,
            unsubscribed_at TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (brand_id) REFERENCES brands(id),
            UNIQUE(user_id, brand_id)
        )
    ''')

    db.commit()
    print("✅ Newsletter tables initialized")


@newsletter_bp.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe():
    """
    POST /api/newsletter/subscribe

    Subscribe user to brand newsletter

    JSON Body:
        brand_id (int): Brand to subscribe to (e.g., 3 for Calriven)

    Returns:
        JSON: {
            "success": true,
            "message": "Subscribed to Calriven newsletter"
        }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    brand_id = data.get('brand_id')

    if not brand_id:
        return jsonify({'success': False, 'error': 'brand_id required'}), 400

    db = get_db()

    # Get brand name
    brand = db.execute('SELECT name FROM brands WHERE id = ?', (brand_id,)).fetchone()
    if not brand:
        return jsonify({'success': False, 'error': 'Brand not found'}), 404

    # Check if already subscribed
    existing = db.execute('''
        SELECT id, is_active FROM newsletter_subscriptions
        WHERE user_id = ? AND brand_id = ?
    ''', (user_id, brand_id)).fetchone()

    if existing and existing['is_active']:
        return jsonify({
            'success': False,
            'error': f'Already subscribed to {brand["name"]} newsletter'
        }), 400

    subscribed_at = datetime.now(timezone.utc).isoformat()

    if existing:
        # Reactivate old subscription
        db.execute('''
            UPDATE newsletter_subscriptions
            SET is_active = 1, unsubscribed_at = NULL, subscribed_at = ?
            WHERE id = ?
        ''', (subscribed_at, existing['id']))
    else:
        # Create new subscription
        db.execute('''
            INSERT INTO newsletter_subscriptions (user_id, brand_id, subscribed_at, is_active)
            VALUES (?, ?, ?, 1)
        ''', (user_id, brand_id, subscribed_at))

    db.commit()

    print(f"✅ User {user_id} subscribed to {brand['name']} newsletter")

    return jsonify({
        'success': True,
        'message': f'Subscribed to {brand["name"]} newsletter! You\'ll receive email digests of new posts.'
    })


@newsletter_bp.route('/api/newsletter/unsubscribe', methods=['POST'])
def unsubscribe():
    """
    POST /api/newsletter/unsubscribe

    Unsubscribe user from brand newsletter

    JSON Body:
        brand_id (int): Brand to unsubscribe from

    Returns:
        JSON: {
            "success": true,
            "message": "Unsubscribed from Calriven newsletter"
        }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    brand_id = data.get('brand_id')

    if not brand_id:
        return jsonify({'success': False, 'error': 'brand_id required'}), 400

    db = get_db()

    # Get brand name
    brand = db.execute('SELECT name FROM brands WHERE id = ?', (brand_id,)).fetchone()
    if not brand:
        return jsonify({'success': False, 'error': 'Brand not found'}), 404

    unsubscribed_at = datetime.now(timezone.utc).isoformat()

    db.execute('''
        UPDATE newsletter_subscriptions
        SET is_active = 0, unsubscribed_at = ?
        WHERE user_id = ? AND brand_id = ?
    ''', (unsubscribed_at, user_id, brand_id))

    db.commit()

    print(f"✅ User {user_id} unsubscribed from {brand['name']} newsletter")

    return jsonify({
        'success': True,
        'message': f'Unsubscribed from {brand["name"]} newsletter'
    })


@newsletter_bp.route('/api/newsletter/subscriptions', methods=['GET'])
def get_subscriptions():
    """
    GET /api/newsletter/subscriptions

    Get user's active newsletter subscriptions

    Returns:
        JSON: {
            "subscriptions": [
                {
                    "brand_id": 3,
                    "brand_name": "Calriven",
                    "subscribed_at": "2026-01-06T..."
                }
            ]
        }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    db = get_db()

    subscriptions = db.execute('''
        SELECT
            ns.brand_id,
            b.name as brand_name,
            b.slug as brand_slug,
            ns.subscribed_at
        FROM newsletter_subscriptions ns
        JOIN brands b ON ns.brand_id = b.id
        WHERE ns.user_id = ? AND ns.is_active = 1
        ORDER BY ns.subscribed_at DESC
    ''', (user_id,)).fetchall()

    return jsonify({
        'success': True,
        'subscriptions': [dict(row) for row in subscriptions]
    })


@newsletter_bp.route('/api/newsletter/send', methods=['POST'])
def send_newsletter():
    """
    POST /api/newsletter/send

    Send newsletter to all subscribers of a brand

    JSON Body:
        brand_id (int): Brand to send newsletter for (e.g., 3 for Calriven)
        days_back (int): How many days of posts to include (default: 7)
        subject (str): Optional custom subject line

    Returns:
        JSON: {
            "success": true,
            "recipients": 5,
            "posts_included": 3
        }
    """
    # TODO: Add admin authentication
    # For now, anyone can send (will add auth later)

    data = request.get_json()
    brand_id = data.get('brand_id')
    days_back = data.get('days_back', 7)
    custom_subject = data.get('subject')

    if not brand_id:
        return jsonify({'success': False, 'error': 'brand_id required'}), 400

    db = get_db()

    # Get brand
    brand = db.execute('SELECT * FROM brands WHERE id = ?', (brand_id,)).fetchone()
    if not brand:
        return jsonify({'success': False, 'error': 'Brand not found'}), 404

    # Get subscribers
    subscribers = db.execute('''
        SELECT u.email, u.username
        FROM newsletter_subscriptions ns
        JOIN users u ON ns.user_id = u.id
        WHERE ns.brand_id = ? AND ns.is_active = 1 AND u.email IS NOT NULL
    ''', (brand_id,)).fetchall()

    if not subscribers:
        return jsonify({
            'success': False,
            'error': 'No subscribers with email addresses found'
        }), 400

    # Get recent posts
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    posts = db.execute('''
        SELECT p.*, u.username as author
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.brand_id = ? AND p.published_at >= ?
        ORDER BY p.published_at DESC
    ''', (brand_id, cutoff_date)).fetchall()

    if not posts:
        return jsonify({
            'success': False,
            'error': f'No posts in the last {days_back} days'
        }), 400

    # Generate email content
    subject = custom_subject or f"{brand['name']} Newsletter - {len(posts)} New Posts"

    html_content = generate_newsletter_html(brand, posts, days_back)
    text_content = generate_newsletter_text(brand, posts, days_back)

    # Send to all subscribers
    sent_count = 0
    for subscriber in subscribers:
        success = send_email(
            to=subscriber['email'],
            subject=subject,
            body=html_content,
            from_name=brand['name'],
            html=True
        )
        if success:
            sent_count += 1

    # Save newsletter to database
    sent_at = datetime.now(timezone.utc).isoformat()
    db.execute('''
        INSERT INTO newsletters (brand_id, subject, content, html_content, sent_at, recipient_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (brand_id, subject, text_content, html_content, sent_at, sent_count))
    db.commit()

    print(f"✅ Newsletter sent to {sent_count} subscribers for {brand['name']}")

    return jsonify({
        'success': True,
        'recipients': sent_count,
        'posts_included': len(posts),
        'subject': subject
    })


def generate_newsletter_html(brand, posts, days_back):
    """
    Generate HTML email content for newsletter

    Args:
        brand: Brand dict
        posts: List of post dicts
        days_back: Number of days covered

    Returns:
        HTML string
    """
    primary = brand['color_primary'] or '#667eea'

    posts_html = ""
    for post in posts:
        # Convert markdown to HTML (first 300 chars)
        excerpt = post['content'][:300] + "..." if len(post['content']) > 300 else post['content']
        excerpt_html = markdown2.markdown(excerpt)

        post_url = f"https://soulfra.github.io/{brand['slug']}/post/{post['slug']}.html"

        posts_html += f"""
        <div style="margin: 30px 0; padding: 20px; background: #f9f9f9; border-radius: 8px;">
            <h2 style="color: {primary}; margin-top: 0;">
                <a href="{post_url}" style="color: {primary}; text-decoration: none;">{post['title']}</a>
            </h2>
            <p style="color: #666; font-size: 14px; margin-bottom: 15px;">
                By {post['author']} • {post['published_at'][:10]}
            </p>
            <div style="color: #333; line-height: 1.6;">
                {excerpt_html}
            </div>
            <a href="{post_url}" style="display: inline-block; margin-top: 15px; padding: 10px 20px; background: {primary}; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                Read Full Post →
            </a>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background: {primary}; color: white; padding: 40px 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 32px;">{brand['name']} Newsletter</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">
                    {len(posts)} new posts in the last {days_back} days
                </p>
            </div>

            <!-- Content -->
            <div style="padding: 30px;">
                {posts_html}
            </div>

            <!-- Footer -->
            <div style="background: #f5f5f5; padding: 30px; text-align: center; color: #666; font-size: 14px;">
                <p style="margin: 0 0 10px 0;">
                    You're receiving this because you subscribed to {brand['name']} newsletters.
                </p>
                <p style="margin: 0;">
                    <a href="https://soulfra.github.io/{brand['slug']}" style="color: {primary}; text-decoration: none;">Visit {brand['name']}</a> •
                    <a href="http://localhost:5001/profile" style="color: {primary}; text-decoration: none;">Manage Subscriptions</a>
                </p>
                <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.7;">
                    Powered by Soulfra - Voice-Powered Publishing
                </p>
            </div>

        </div>
    </body>
    </html>
    """

    return html


def generate_newsletter_text(brand, posts, days_back):
    """
    Generate plain text email content for newsletter

    Args:
        brand: Brand dict
        posts: List of post dicts
        days_back: Number of days covered

    Returns:
        Plain text string
    """
    text = f"{brand['name']} Newsletter\n"
    text += f"{len(posts)} new posts in the last {days_back} days\n"
    text += "=" * 60 + "\n\n"

    for post in posts:
        text += f"{post['title']}\n"
        text += f"By {post['author']} • {post['published_at'][:10]}\n\n"
        excerpt = post['content'][:300] + "..." if len(post['content']) > 300 else post['content']
        text += excerpt + "\n\n"
        text += f"Read more: https://soulfra.github.io/{brand['slug']}/post/{post['slug']}.html\n\n"
        text += "-" * 60 + "\n\n"

    text += f"Visit {brand['name']}: https://soulfra.github.io/{brand['slug']}\n"
    text += "Manage subscriptions: http://localhost:5001/profile\n\n"
    text += "Powered by Soulfra - Voice-Powered Publishing\n"

    return text


@newsletter_bp.route('/api/newsletter/send-irc-message', methods=['POST'])
def send_irc_newsletter():
    """
    POST /api/newsletter/send-irc-message

    Send IRC message as newsletter to subscribers

    JSON Body:
        domain (str): Domain slug (e.g., 'stpetepros')
        message_id (int): IRC message ID to send as newsletter

    Returns:
        JSON: {
            "success": true,
            "recipients": 5,
            "subject": "..."
        }
    """
    data = request.get_json()
    domain_slug = data.get('domain')
    message_id = data.get('message_id')

    if not domain_slug or not message_id:
        return jsonify({'success': False, 'error': 'domain and message_id required'}), 400

    db = get_db()

    # Get IRC message
    message = db.execute('''
        SELECT * FROM domain_messages
        WHERE id = ? AND to_domain = ?
    ''', (message_id, domain_slug)).fetchone()

    if not message:
        return jsonify({'success': False, 'error': 'Message not found'}), 404

    # Get brand
    brand = db.execute('SELECT * FROM brands WHERE slug = ?', (domain_slug,)).fetchone()
    if not brand:
        return jsonify({'success': False, 'error': 'Brand not found'}), 404

    # Get subscribers
    subscribers = db.execute('''
        SELECT u.email, u.username
        FROM newsletter_subscriptions ns
        JOIN users u ON ns.user_id = u.id
        WHERE ns.brand_id = ? AND ns.is_active = 1 AND u.email IS NOT NULL
    ''', (brand['id'],)).fetchall()

    if not subscribers:
        return jsonify({'success': False, 'error': 'No subscribers found'}), 400

    # Send email to each subscriber
    subject = message['subject'] or f"New message from {brand['name']}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: -apple-system, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px;">
            <h2 style="color: {brand['color_primary'] or '#667eea'};">{message['subject']}</h2>
            <p style="color: #666; margin-bottom: 20px;">From: {message['from_user']}</p>
            <div style="line-height: 1.6; color: #333;">{message['body']}</div>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 14px;">
                Posted to alt.{message['to_domain']}.{message['channel']}<br>
                <a href="https://soulfra.github.io/inbox.html?domain={domain_slug}">View in Inbox</a>
            </p>
        </div>
    </body>
    </html>
    """

    sent_count = 0
    for subscriber in subscribers:
        success = send_email(
            to=subscriber['email'],
            subject=subject,
            body=html_content,
            from_name=brand['name'],
            html=True
        )
        if success:
            sent_count += 1

    # Save newsletter record
    sent_at = datetime.now(timezone.utc).isoformat()
    db.execute('''
        INSERT INTO newsletters (brand_id, subject, content, html_content, sent_at, recipient_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (brand['id'], subject, message['body'], html_content, sent_at, sent_count))
    db.commit()

    print(f"📧 Sent IRC message #{message_id} as newsletter to {sent_count} subscribers")

    return jsonify({
        'success': True,
        'recipients': sent_count,
        'subject': subject
    })


def watch_irc_for_newsletters():
    """
    Background daemon: Watch IRC messages for message_type='newsletter'
    Auto-send as email to subscribers

    Run with: python3 newsletter_routes.py watch
    """
    import time

    print("👀 Watching IRC channels for newsletter messages...")

    last_checked_id = 0

    while True:
        try:
            db = get_db()

            # Get new newsletter messages
            messages = db.execute('''
                SELECT * FROM domain_messages
                WHERE id > ? AND message_type = 'newsletter'
                ORDER BY id ASC
            ''', (last_checked_id,)).fetchall()

            for msg in messages:
                print(f"📨 Found newsletter message #{msg['id']} in alt.{msg['to_domain']}.{msg['channel']}")

                # Get brand
                brand = db.execute('SELECT * FROM brands WHERE slug = ?', (msg['to_domain'],)).fetchone()

                if brand:
                    # Trigger newsletter send (would need to call send_irc_newsletter via HTTP)
                    print(f"   → Would send to {brand['name']} subscribers")

                last_checked_id = msg['id']

            time.sleep(10)  # Check every 10 seconds

        except KeyboardInterrupt:
            print("\n✅ Stopped watching IRC")
            break
        except Exception as e:
            print(f"❌ Error watching IRC: {e}")
            time.sleep(10)


if __name__ == '__main__':
    """
    CLI for testing newsletter system
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 newsletter_routes.py init             # Initialize tables")
        print("  python3 newsletter_routes.py send <brand_id>  # Send test newsletter")
        print("  python3 newsletter_routes.py watch            # Watch IRC for newsletters")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_newsletter_tables()
        print("✅ Newsletter tables initialized")

    elif command == "watch":
        watch_irc_for_newsletters()

    elif command == "send":
        if len(sys.argv) < 3:
            print("Usage: python3 newsletter_routes.py send <brand_id>")
            sys.exit(1)

        brand_id = int(sys.argv[2])

        # Simulate sending newsletter
        print(f"📧 Sending newsletter for brand_id={brand_id}...")

        from database import get_db
        db = get_db()

        brand = db.execute('SELECT * FROM brands WHERE id = ?', (brand_id,)).fetchone()
        if not brand:
            print(f"❌ Brand {brand_id} not found")
            sys.exit(1)

        print(f"✅ Would send newsletter for: {brand['name']}")
        print("   (Run via API endpoint to actually send)")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

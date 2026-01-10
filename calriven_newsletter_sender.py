#!/usr/bin/env python3
"""
Calriven Newsletter Sender - Automated email newsletter for Calriven blog

Usage:
    python3 calriven_newsletter_sender.py

What it does:
1. Scrapes Calriven posts from database (last 7 days)
2. Generates beautiful HTML email newsletter
3. Sends to all Calriven newsletter subscribers
4. Logs newsletter to database

Can be run:
- Manually (python3 calriven_newsletter_sender.py)
- Cron job (weekly digest)
- API endpoint (POST /api/newsletter/send with brand_id=3)
"""

import sys
from database import get_db
from newsletter_routes import send_newsletter
from datetime import datetime, timezone


def send_calriven_newsletter(days_back=7, dry_run=False):
    """
    Send Calriven newsletter to all subscribers

    Args:
        days_back (int): How many days of posts to include (default: 7)
        dry_run (bool): If True, don't actually send emails (just preview)

    Returns:
        dict: {
            "success": bool,
            "recipients": int,
            "posts_included": int,
            "subject": str
        }
    """
    db = get_db()

    # Get Calriven brand (brand_id = 3)
    calriven = db.execute("SELECT * FROM brands WHERE slug = 'calriven'").fetchone()

    if not calriven:
        print("❌ Calriven brand not found in database")
        return {"success": False, "error": "Calriven not found"}

    brand_id = calriven['id']

    # Get subscriber count
    subscriber_count = db.execute('''
        SELECT COUNT(*) as count
        FROM newsletter_subscriptions ns
        JOIN users u ON ns.user_id = u.id
        WHERE ns.brand_id = ? AND ns.is_active = 1 AND u.email IS NOT NULL
    ''', (brand_id,)).fetchone()['count']

    # Get post count
    from datetime import timedelta
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    post_count = db.execute('''
        SELECT COUNT(*) as count FROM posts
        WHERE brand_id = ? AND published_at >= ?
    ''', (brand_id, cutoff_date)).fetchone()['count']

    print(f"\n{'='*60}")
    print(f"📧 Calriven Newsletter")
    print(f"{'='*60}")
    print(f"Posts in last {days_back} days: {post_count}")
    print(f"Subscribers with email: {subscriber_count}")
    print(f"Dry run: {dry_run}")
    print(f"{'='*60}\n")

    if post_count == 0:
        print("❌ No posts in the last {days_back} days - skipping newsletter")
        return {"success": False, "error": f"No posts in last {days_back} days"}

    if subscriber_count == 0:
        print("❌ No subscribers with email addresses - skipping newsletter")
        return {"success": False, "error": "No subscribers"}

    if dry_run:
        print("✅ Dry run complete - would send newsletter to {subscriber_count} subscribers")
        return {
            "success": True,
            "dry_run": True,
            "recipients": subscriber_count,
            "posts_included": post_count
        }

    # Actually send newsletter
    print("📧 Sending newsletter...")

    # Import Flask request context (needed for send_newsletter to work)
    # For CLI usage, we simulate the request
    from flask import Flask
    app = Flask(__name__)

    with app.test_request_context(
        json={
            'brand_id': brand_id,
            'days_back': days_back
        }
    ):
        from newsletter_routes import send_newsletter
        result = send_newsletter()

        # Flask returns a tuple (response, status_code)
        if isinstance(result, tuple):
            response_data = result[0].get_json()
        else:
            response_data = result.get_json()

        if response_data.get('success'):
            print(f"✅ Newsletter sent to {response_data['recipients']} recipients!")
            print(f"   Subject: {response_data['subject']}")
            print(f"   Posts included: {response_data['posts_included']}")
        else:
            print(f"❌ Newsletter failed: {response_data.get('error')}")

        return response_data


def preview_newsletter(days_back=7):
    """
    Preview newsletter content without sending

    Args:
        days_back (int): How many days of posts to include

    Returns:
        None (prints preview to console)
    """
    from datetime import timedelta
    from newsletter_routes import generate_newsletter_html, generate_newsletter_text

    db = get_db()

    # Get Calriven brand
    calriven = db.execute("SELECT * FROM brands WHERE slug = 'calriven'").fetchone()
    if not calriven:
        print("❌ Calriven not found")
        return

    # Get posts
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    posts = db.execute('''
        SELECT p.*, u.username as author
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.brand_id = ? AND p.published_at >= ?
        ORDER BY p.published_at DESC
    ''', (calriven['id'], cutoff_date)).fetchall()

    if not posts:
        print(f"❌ No posts in last {days_back} days")
        return

    print(f"\n{'='*60}")
    print(f"📧 Calriven Newsletter Preview")
    print(f"{'='*60}")
    print(f"Posts: {len(posts)}")
    print(f"Days back: {days_back}")
    print(f"{'='*60}\n")

    # Generate text version
    text_content = generate_newsletter_text(dict(calriven), [dict(p) for p in posts], days_back)
    print(text_content)

    print(f"\n{'='*60}")
    print("✅ Preview complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    """
    CLI usage
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 calriven_newsletter_sender.py send        # Send newsletter")
        print("  python3 calriven_newsletter_sender.py preview     # Preview without sending")
        print("  python3 calriven_newsletter_sender.py dry-run     # Test without sending")
        print("\nOptions:")
        print("  --days=7    # Number of days back to include (default: 7)")
        sys.exit(1)

    command = sys.argv[1]

    # Parse optional --days argument
    days_back = 7
    for arg in sys.argv[2:]:
        if arg.startswith('--days='):
            days_back = int(arg.split('=')[1])

    if command == "send":
        result = send_calriven_newsletter(days_back=days_back, dry_run=False)
        if not result.get('success'):
            sys.exit(1)

    elif command == "preview":
        preview_newsletter(days_back=days_back)

    elif command == "dry-run":
        result = send_calriven_newsletter(days_back=days_back, dry_run=True)
        if not result.get('success'):
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Use: send, preview, or dry-run")
        sys.exit(1)

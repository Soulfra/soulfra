#!/usr/bin/env python3
"""
Send Post as Email - Test email generation

Send an existing blog post as a beautiful HTML email

Usage:
    python3 send_post_email.py --post-id 30 --send-to your@email.com
"""

import sys
import argparse
from simple_emailer import send_email
from database import get_db
import markdown2


def generate_email_html(post, brand, full_url):
    """
    Generate beautiful HTML email from blog post

    Args:
        post: Post dict from database
        brand: Brand dict from database
        full_url: Full URL to read online

    Returns:
        HTML string
    """
    # Convert markdown to HTML
    content_html = markdown2.markdown(post['content'])

    # Brand colors
    primary = brand['color_primary'] if brand['color_primary'] else '#FF6B35'
    secondary = brand['color_secondary'] if brand['color_secondary'] else '#F7931E'
    accent = brand['color_accent'] if brand['color_accent'] else '#C1272D'

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: {primary};
            color: white;
            padding: 30px;
            text-align: center;
            margin: -30px -30px 30px -30px;
            border-radius: 8px 8px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .tagline {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            margin: 20px 0;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .content h1, .content h2, .content h3 {{
            color: {primary};
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .read-online {{
            background: {secondary};
            color: white;
            text-align: center;
            padding: 20px;
            margin: 30px -30px -30px -30px;
            border-radius: 0 0 8px 8px;
        }}
        .read-online a {{
            color: white;
            text-decoration: none;
            font-weight: bold;
            padding: 12px 30px;
            background: {accent};
            border-radius: 4px;
            display: inline-block;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{brand['name']}</h1>
            <p class="tagline">{brand['tagline'] if brand['tagline'] else ''}</p>
        </div>

        <div class="content">
            <h1>{post['title']}</h1>
            {content_html}
        </div>

        <div class="read-online">
            <p style="margin: 0 0 15px 0;">Read this post online</p>
            <a href="{full_url}">View in Browser →</a>
        </div>
    </div>

    <div class="footer">
        <p>You're receiving this because you subscribed to {brand['name']}</p>
        <p>Powered by Soulfra | Generated with procedural images</p>
    </div>
</body>
</html>
"""
    return html


def send_post_email(post_id, send_to, host='localhost', port=5000):
    """
    Send existing blog post as email

    Args:
        post_id: Post ID
        send_to: Email address
        host: Host for full URL
        port: Port for full URL

    Returns:
        True if successful
    """
    db = get_db()

    post = db.execute('''
        SELECT p.*, b.slug as brand_slug
        FROM posts p
        JOIN brands b ON p.brand_id = b.id
        WHERE p.id = ?
    ''', (post_id,)).fetchone()

    if not post:
        print(f"❌ Post {post_id} not found")
        db.close()
        return False

    brand = db.execute('''
        SELECT * FROM brands WHERE id = ?
    ''', (post['brand_id'],)).fetchone()

    # Build full URL
    full_url = f"http://{host}:{port}/brand/{post['brand_slug']}/post/{post['slug']}"

    # Generate email HTML
    email_html = generate_email_html(post, brand, full_url)

    # Send email
    subject = f"📰 {post['title']} - {brand['name']}"

    success = send_email(
        to=send_to,
        subject=subject,
        body=email_html,
        from_name=brand['name'],
        html=True
    )

    db.close()

    if success:
        print(f"\n✅ Email sent to {send_to}")
        print(f"📧 Subject: {subject}")
        print(f"🔗 URL: {full_url}")
    else:
        print(f"\n⚠️  Email printed to console (not configured)")

    return success


def main():
    parser = argparse.ArgumentParser(
        description='Send existing blog post as email newsletter'
    )

    parser.add_argument(
        '--post-id',
        type=int,
        required=True,
        help='Post ID to send'
    )

    parser.add_argument(
        '--send-to',
        required=True,
        help='Email address to send to'
    )

    parser.add_argument(
        '--host',
        default='localhost',
        help='Host for full URL (default: localhost)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port for full URL (default: 5000)'
    )

    args = parser.parse_args()

    send_post_email(
        post_id=args.post_id,
        send_to=args.send_to,
        host=args.host,
        port=args.port
    )


if __name__ == '__main__':
    main()

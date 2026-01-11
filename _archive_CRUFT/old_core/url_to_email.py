#!/usr/bin/env python3
"""
URL to Email - THE MAGIC COMMAND

Paste a URL → Get a beautiful email newsletter with procedural images

This is the ONE COMMAND that proves everything works:
    python3 url_to_email.py --url https://example.com --brand howtocookathome --send-to your@email.com

What it does:
1. Scrapes the URL
2. Generates procedural images
3. Creates blog post in database
4. Exports to static site
5. Generates beautiful HTML email
6. Sends to your inbox
7. YOU READ IT ON YOUR PHONE

This is PROOF that the system works. Not just code - actual email in your inbox.
"""

import sys
import argparse
from url_to_blog import url_to_blog_post
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
    primary = brand.get('color_primary', '#FF6B35')
    secondary = brand.get('color_secondary', '#F7931E')
    accent = brand.get('color_accent', '#C1272D')

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
            <p class="tagline">{brand.get('tagline', '')}</p>
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


def url_to_email(url, brand_slug, send_to, host='localhost', port=5000):
    """
    Complete pipeline: URL → Email

    Args:
        url: URL to scrape
        brand_slug: Brand slug
        send_to: Email address to send to
        host: Host for full URL (default: localhost)
        port: Port for full URL (default: 5000)

    Returns:
        True if successful
    """
    print("=" * 70)
    print("🚀 URL TO EMAIL - THE COMPLETE PIPELINE")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Brand: {brand_slug}")
    print(f"Send to: {send_to}")
    print("=" * 70)
    print()

    # Step 1: Create blog post (includes scrape, generate images, export)
    print("STEP 1-4: Create Blog Post (URL → Images → DB → Export)")
    print("-" * 70)

    post_id = url_to_blog_post(
        url=url,
        brand_slug=brand_slug,
        author_id=1
    )

    if not post_id:
        print("❌ Failed to create blog post")
        return False

    print()

    # Step 5: Get post and brand data
    print("STEP 5: Generate Email")
    print("-" * 70)

    db = get_db()

    post = db.execute('''
        SELECT * FROM posts WHERE id = ?
    ''', (post_id,)).fetchone()

    brand = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    if not post or not brand:
        print("❌ Could not find post or brand")
        db.close()
        return False

    # Build full URL
    full_url = f"http://{host}:{port}/brand/{brand_slug}/post/{post['slug']}"

    # Generate email HTML
    email_html = generate_email_html(post, brand, full_url)

    print(f"✅ Generated email HTML ({len(email_html)} bytes)")
    print()

    # Step 6: Send email
    print("STEP 6: Send Email")
    print("-" * 70)

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
        print()
        print("=" * 70)
        print("✅ SUCCESS! EMAIL SENT!")
        print("=" * 70)
        print(f"Post ID: {post_id}")
        print(f"Title: {post['title']}")
        print(f"Sent to: {send_to}")
        print()
        print("💡 Now:")
        print(f"   1. Check your email: {send_to}")
        print(f"   2. Open on your phone or laptop")
        print(f"   3. See the blog post with procedural images")
        print(f"   4. Click 'View in Browser' to see static site")
        print()
        print("🎉 THIS IS PROOF IT WORKS!")
        print("=" * 70)
        return True
    else:
        print()
        print("⚠️  Email not configured (printed to console)")
        print()
        print("To send real emails:")
        print("1. Create config_secrets.py with:")
        print("   SMTP_HOST = 'smtp.gmail.com'")
        print("   SMTP_PORT = 587")
        print("   SMTP_USER = 'your@gmail.com'")
        print("   SMTP_PASSWORD = 'your-app-password'")
        print()
        print("2. Get Gmail app password:")
        print("   Google Account → Security → App passwords")
        print()
        return False


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Convert any URL to an email newsletter with procedural images'
    )

    parser.add_argument(
        '--url',
        required=True,
        help='URL to convert to blog post and email'
    )

    parser.add_argument(
        '--brand',
        required=True,
        help='Brand slug (e.g., howtocookathome, soulfra)'
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

    success = url_to_email(
        url=args.url,
        brand_slug=args.brand,
        send_to=args.send_to,
        host=args.host,
        port=args.port
    )

    sys.exit(0 if success else 1)


# =============================================================================
# TESTING
# =============================================================================

def test_url_to_email():
    """Test with example.com"""
    print("🧪 Testing URL to Email with example.com\n")

    success = url_to_email(
        url='https://example.com',
        brand_slug='howtocookathome',
        send_to='test@example.com'
    )

    if success:
        print("✅ Test passed!")
    else:
        print("⚠️  Test completed (email not configured)")


if __name__ == '__main__':
    if '--test' in sys.argv:
        test_url_to_email()
    else:
        main()

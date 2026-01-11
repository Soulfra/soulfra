"""
Email Sender - SMTP (Gmail)
Send newsletter emails to subscribers

Setup:
1. Enable 2FA in Gmail
2. Create App Password: https://myaccount.google.com/apppasswords
3. Set environment variables:
   export SMTP_EMAIL="your-email@gmail.com"
   export SMTP_PASSWORD="your-app-password"
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from database import get_subscribers, mark_post_emailed


def send_post_email(post, dry_run=False):
    """
    Send post to all subscribers

    Args:
        post: Post dict from database
        dry_run: If True, don't actually send emails (for testing)

    Returns:
        Number of emails sent
    """
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if not smtp_email or not smtp_password:
        print("⚠️  SMTP credentials not set!")
        print("Set SMTP_EMAIL and SMTP_PASSWORD environment variables")
        return 0

    subscribers = get_subscribers()

    if not subscribers:
        print("📭 No subscribers yet")
        return 0

    # Extract just the emails from subscriber dicts
    subscriber_emails = [sub['email'] for sub in subscribers if sub['active']]

    if not subscriber_emails:
        print("📭 No active subscribers")
        return 0

    print(f"📧 Sending '{post['title']}' to {len(subscriber_emails)} subscribers...")

    if dry_run:
        print("🔍 DRY RUN - Not actually sending")
        for email in subscriber_emails:
            print(f"  Would send to: {email}")
        return 0

    # Create email content
    subject = post['title']

    # HTML email body
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #333;">{post['title']}</h1>
        <div style="color: #666; margin-bottom: 30px; line-height: 1.6;">
          {post['content']}
        </div>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
          <a href="https://soulfra.github.io/post/{post['slug']}" style="color: #666;">View online</a>
          | <a href="https://soulfra.github.io/unsubscribe?email={{email}}" style="color: #666;">Unsubscribe</a>
        </p>
      </body>
    </html>
    """

    # Plain text fallback
    text_content = f"""
{post['title']}

{post['content']}

---
View online: https://soulfra.github.io/post/{post['slug']}
Unsubscribe: https://soulfra.github.io/unsubscribe?email={{email}}
    """

    sent_count = 0
    failed = []

    # Send to each subscriber
    for email in subscriber_emails:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_email
            msg['To'] = email

            # Attach both plain text and HTML
            msg.attach(MIMEText(text_content.replace('{{email}}', email), 'plain'))
            msg.attach(MIMEText(html_content.replace('{{email}}', email), 'html'))

            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(smtp_email, smtp_password)
                server.send_message(msg)

            sent_count += 1
            print(f"  ✅ Sent to {email}")

        except Exception as e:
            print(f"  ❌ Failed to send to {email}: {e}")
            failed.append(email)

    # Mark post as emailed
    if sent_count > 0:
        mark_post_emailed(post['slug'])

    print(f"\n📊 Results: {sent_count} sent, {len(failed)} failed")

    if failed:
        print("\nFailed addresses:")
        for email in failed:
            print(f"  - {email}")

    return sent_count


def send_welcome_email(email, dry_run=False):
    """
    Send welcome email to new subscriber

    Args:
        email: Subscriber email address
        dry_run: If True, don't actually send

    Returns:
        True if sent successfully
    """
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if not smtp_email or not smtp_password:
        print("⚠️  SMTP credentials not set!")
        return False

    if dry_run:
        print(f"🔍 DRY RUN - Would send welcome email to {email}")
        return True

    subject = "Welcome to Soulfra Newsletter!"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #333;">Welcome to Soulfra!</h1>
        <p style="color: #666; line-height: 1.6;">
          Thanks for subscribing. You'll receive updates whenever we publish new posts.
        </p>
        <p style="color: #666; line-height: 1.6;">
          You can <a href="https://soulfra.github.io/unsubscribe?email={email}" style="color: #666;">unsubscribe</a> anytime.
        </p>
      </body>
    </html>
    """

    text_content = f"""
Welcome to Soulfra!

Thanks for subscribing. You'll receive updates whenever we publish new posts.

Unsubscribe: https://soulfra.github.io/unsubscribe?email={email}
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = email

        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)

        print(f"✅ Welcome email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send welcome email to {email}: {e}")
        return False


def send_game_share_email(recipient_email, share_code, game_type, sender_name=None, message=None, theme_primary='#667eea', theme_secondary='#764ba2'):
    """
    Send game share invitation email

    Args:
        recipient_email: Friend's email address
        share_code: Unique share code for the link
        game_type: Type of game (e.g., 'cringeproof')
        sender_name: Name of person sending (optional)
        message: Personal message (optional)
        theme_primary: Brand primary color
        theme_secondary: Brand secondary color

    Returns:
        True if sent successfully
    """
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if not smtp_email or not smtp_password:
        print("⚠️  SMTP credentials not set - skipping email")
        return False

    # Build review URL
    review_url = f"https://soulfra.github.io/review/{share_code}"

    # Build subject
    sender_text = sender_name if sender_name else "Someone"
    subject = f"{sender_text} wants your honest feedback on their {game_type} results"

    # Build HTML email
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f8f9fa;">
        <div style="background: linear-gradient(135deg, {theme_primary} 0%, {theme_secondary} 100%); color: white; padding: 40px; border-radius: 16px 16px 0 0; text-align: center;">
          <h1 style="margin: 0; font-size: 32px;">💌 You've Been Asked for Feedback!</h1>
        </div>

        <div style="background: white; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
          <p style="font-size: 18px; color: #333; line-height: 1.6;">
            <strong>{sender_text}</strong> shared their {game_type} results with you and would love your honest feedback.
          </p>

          {f'<div style="background: #f8f9fa; padding: 20px; border-left: 4px solid {theme_primary}; margin: 20px 0;"><p style="margin: 0; color: #666; font-style: italic;">"{message}"</p></div>' if message else ''}

          <p style="color: #666; line-height: 1.6;">
            Click the button below to review their results. Your feedback will be analyzed by AI to provide helpful insights.
          </p>

          <div style="text-align: center; margin: 30px 0;">
            <a href="{review_url}" style="display: inline-block; background: {theme_primary}; color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
              Review Now
            </a>
          </div>

          <p style="color: #999; font-size: 14px; margin-top: 30px;">
            Or copy this link: <br>
            <a href="{review_url}" style="color: {theme_primary}; word-break: break-all;">{review_url}</a>
          </p>
        </div>
      </body>
    </html>
    """

    # Plain text version
    text_content = f"""
{sender_text} wants your honest feedback!

{sender_text} shared their {game_type} results with you and would love your honest feedback.

{f'Personal message: "{message}"' if message else ''}

Click here to review: {review_url}

Your feedback will be analyzed by AI to provide helpful insights.
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = recipient_email

        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)

        print(f"✅ Game share email sent to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send game share email to {recipient_email}: {e}")
        return False


def send_review_received_email(sender_email, share_code, game_type, reviewer_name=None, overall_rating=None, theme_primary='#667eea', theme_secondary='#764ba2'):
    """
    Send notification to game sender that review was completed

    Args:
        sender_email: Original sender's email
        share_code: Share code for viewing analysis
        game_type: Type of game
        reviewer_name: Name of reviewer (if not anonymous)
        overall_rating: Overall star rating (1-5)
        theme_primary: Brand primary color
        theme_secondary: Brand secondary color

    Returns:
        True if sent successfully
    """
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if not smtp_email or not smtp_password:
        print("⚠️  SMTP credentials not set - skipping email")
        return False

    # Build analysis URL
    analysis_url = f"https://soulfra.github.io/share/{share_code}/analysis"

    # Build reviewer text
    reviewer_text = reviewer_name if reviewer_name else "Someone"
    rating_text = f"gave you {overall_rating}/5 stars" if overall_rating else "completed their review"

    subject = f"🎯 {reviewer_text} {rating_text} on your {game_type}!"

    # Build HTML email
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f8f9fa;">
        <div style="background: linear-gradient(135deg, {theme_primary} 0%, {theme_secondary} 100%); color: white; padding: 40px; border-radius: 16px 16px 0 0; text-align: center;">
          <h1 style="margin: 0; font-size: 32px;">🎉 Your Review is Ready!</h1>
        </div>

        <div style="background: white; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
          <p style="font-size: 18px; color: #333; line-height: 1.6;">
            <strong>{reviewer_text}</strong> just {rating_text}!
          </p>

          {f'<div style="text-align: center; margin: 30px 0;"><div style="font-size: 48px; color: #FFD700;">{"★" * overall_rating}{"☆" * (5 - overall_rating)}</div></div>' if overall_rating else ''}

          <p style="color: #666; line-height: 1.6;">
            Our AI has analyzed the feedback and generated insights for you. Click below to see:
          </p>

          <ul style="color: #666; line-height: 1.8;">
            <li>Neural network classifications</li>
            <li>Review quality score</li>
            <li>Key insights and recommendations</li>
            <li>Detailed peer feedback</li>
          </ul>

          <div style="text-align: center; margin: 30px 0;">
            <a href="{analysis_url}" style="display: inline-block; background: {theme_primary}; color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
              View AI Analysis
            </a>
          </div>

          <p style="color: #999; font-size: 14px; margin-top: 30px;">
            Or copy this link: <br>
            <a href="{analysis_url}" style="color: {theme_primary}; word-break: break-all;">{analysis_url}</a>
          </p>
        </div>
      </body>
    </html>
    """

    # Plain text version
    text_content = f"""
Your Review is Ready!

{reviewer_text} just {rating_text}!

{f'Rating: {"★" * overall_rating}{"☆" * (5 - overall_rating)} ({overall_rating}/5)' if overall_rating else ''}

Our AI has analyzed the feedback and generated insights for you including:
- Neural network classifications
- Review quality score
- Key insights and recommendations
- Detailed peer feedback

View your AI analysis here: {analysis_url}
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = sender_email

        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)

        print(f"✅ Review notification email sent to {sender_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send review notification to {sender_email}: {e}")
        return False


if __name__ == '__main__':
    import sys
    from database import get_posts

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python emails.py send-latest           # Send latest post")
        print("  python emails.py send-latest --dry-run # Test without sending")
        print("  python emails.py welcome test@example.com")
        sys.exit(1)

    command = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if command == 'send-latest':
        posts = get_posts(limit=1)
        if not posts:
            print("❌ No posts found")
            sys.exit(1)

        post = posts[0]
        send_post_email(post, dry_run=dry_run)

    elif command == 'welcome' and len(sys.argv) >= 3:
        email = sys.argv[2]
        send_welcome_email(email, dry_run=dry_run)

    else:
        print("❌ Unknown command")
        sys.exit(1)

#!/usr/bin/env python3
"""
Simple Emailer - Send emails without complexity

Just a thin wrapper around SMTP. Uses config_secrets.py for credentials.
If config not found, prints to console instead of crashing.

Setup:
1. Create config_secrets.py (git-ignored):
```python
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-16-char-app-password'  # Get from Google Account → Security → App passwords
```

Usage:
```python
from simple_emailer import send_email

send_email(
    to='user@example.com',
    subject='Welcome!',
    body='You got matched with Soulfra as your AI friend!'
)
```
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Try to import config, fallback to console if not found
try:
    from config_secrets import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    EMAIL_CONFIGURED = True
except ImportError:
    EMAIL_CONFIGURED = False
    print("⚠️  config_secrets.py not found - emails will print to console")
    print("   Create config_secrets.py with SMTP credentials to enable real emails")


def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: str = 'Soulfra',
    html: bool = False
) -> bool:
    """
    Send email via SMTP (or print to console if not configured)

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (text or HTML)
        from_email: Sender email (defaults to SMTP_USER)
        from_name: Sender display name
        html: Whether body is HTML (default: False = plain text)

    Returns:
        True if sent successfully, False otherwise
    """
    if not EMAIL_CONFIGURED:
        # Print to console instead of crashing
        print("\n" + "="*60)
        print("📧 EMAIL (would send if configured):")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("="*60 + "\n")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email or SMTP_USER}>"
        msg['To'] = to

        # Attach body
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Send via SMTP
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email sent to {to}: {subject}")
        return True

    except Exception as e:
        print(f"❌ Email send failed to {to}: {e}")
        return False


def send_welcome_email(user_email: str, username: str, ai_friend_name: str) -> bool:
    """
    Send welcome email after quiz completion

    Args:
        user_email: User's email address
        username: User's username
        ai_friend_name: Name of matched AI friend

    Returns:
        True if sent successfully
    """
    subject = f"Welcome to Soulfra, {username}!"

    body = f"""
Hi {username},

Welcome to Soulfra! You've completed the personality quiz and we've matched you with **{ai_friend_name}** as your AI companion.

Your AI friend is ready to chat anytime via the widget on any page. Just click the purple chat bubble in the corner!

**What's next:**
- Explore the wiki: http://localhost:5001/wiki
- View your profile: http://localhost:5001/profile/{username}
- Read the latest posts: http://localhost:5001/
- Chat with your AI friend anytime!

---

🎮 Generated with Soulfra
"""

    return send_email(user_email, subject, body)


def send_notification_email(user_email: str, notification_type: str, notification_content: str, link: Optional[str] = None) -> bool:
    """
    Send notification email (for important notifications only, not spam)

    Args:
        user_email: User's email
        notification_type: Type of notification
        notification_content: Notification message
        link: Optional link to relevant page

    Returns:
        True if sent successfully
    """
    subject_map = {
        'nudge': 'You got nudged!',
        'ai_comment': 'AI commented on your post',
        'quiz_complete': 'Your Soulfra profile is ready',
        'new_friend': 'You have a new friend request'
    }

    subject = subject_map.get(notification_type, 'New notification')

    body = f"""
{notification_content}

"""

    if link:
        body += f"View here: http://localhost:5001{link}\n\n"

    body += "---\n🎮 Soulfra Notifications"

    return send_email(user_email, subject, body)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("\n🧪 Testing Simple Emailer\n")

    # Test 1: Send simple email
    print("Test 1: Send test email")
    result = send_email(
        to='test@example.com',
        subject='Test Email',
        body='This is a test from simple_emailer.py'
    )
    print(f"Result: {'✅ Sent' if result else '⚠️  Printed to console'}\n")

    # Test 2: Send welcome email
    print("Test 2: Send welcome email")
    result = send_welcome_email(
        user_email='newuser@example.com',
        username='testuser',
        ai_friend_name='Soulfra'
    )
    print(f"Result: {'✅ Sent' if result else '⚠️  Printed to console'}\n")

    # Test 3: Send notification email
    print("Test 3: Send notification email")
    result = send_notification_email(
        user_email='user@example.com',
        notification_type='nudge',
        notification_content='Bob nudged you!',
        link='/profile/bob'
    )
    print(f"Result: {'✅ Sent' if result else '⚠️  Printed to console'}\n")

    print("✅ Email tests complete!\n")

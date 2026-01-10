#!/usr/bin/env python3
"""
Waitlist Emailer - Send confirmation and update emails to waitlist users

Email types:
1. Confirmation - When user joins waitlist
2. Launch Alert - When domain launches
3. Position Update - When they move up in line
4. Referral Success - When someone uses their code

Usage:
    python3 waitlist_emailer.py confirm user@example.com soulfra A
    python3 waitlist_emailer.py launch soulfra
    python3 waitlist_emailer.py referral user@example.com ABC12345
"""

from database import get_db
from datetime import datetime, timezone
import sys

# Try to import SMTP config, fallback to console output
try:
    from config_secrets import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    USE_SMTP = True
except ImportError:
    USE_SMTP = False
    print("⚠️  No SMTP credentials found (config_secrets.py)")
    print("📧 Emails will be printed to console instead\n")

if USE_SMTP:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart


def send_email(to_email, subject, html_content):
    """
    Send email via SMTP or print to console

    Args:
        to_email (str): Recipient email
        subject (str): Email subject
        html_content (str): HTML email body

    Returns:
        bool: Success
    """
    if USE_SMTP:
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            print(f"✅ Email sent to {to_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    else:
        # Console fallback
        print(f"\n{'='*60}")
        print(f"📧 EMAIL (Console Mode)")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"\n{html_content}\n")
        print(f"{'='*60}\n")
        return True


def send_confirmation_email(email, domain_name, letter_code, referral_code):
    """
    Send waitlist confirmation email

    Args:
        email (str): User email
        domain_name (str): Domain they signed up for
        letter_code (str): Their letter slot (A-Z)
        referral_code (str): Their referral code

    Returns:
        bool: Success
    """
    from launch_calculator import calculate_launch_date

    launch_info = calculate_launch_date(domain_name)

    subject = f"🚀 You're on the {domain_name.upper()} Waitlist!"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       color: white; padding: 30px; text-align: center; border-radius: 10px; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin-top: 20px; }}
            .badge {{ background: #ffd700; color: #333; padding: 10px 20px;
                      border-radius: 30px; font-weight: bold; font-size: 1.2em; }}
            .code {{ background: #333; color: #ffd700; padding: 5px 15px;
                     border-radius: 5px; font-family: monospace; font-size: 1.1em; }}
            .footer {{ text-align: center; margin-top: 30px; opacity: 0.7; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Welcome to the Waitlist!</h1>
                <p style="font-size: 1.2em;">You're in line for <strong>{domain_name.upper()}</strong></p>
            </div>

            <div class="content">
                <h2>Your Letter Slot:</h2>
                <p style="text-align: center;">
                    <span class="badge">{letter_code}</span>
                </p>

                <h2>Launch Info:</h2>
                <ul>
                    <li><strong>Current Signups:</strong> {launch_info['signups']}</li>
                    <li><strong>Days Until Launch:</strong> {launch_info['days_until']}</li>
                    <li><strong>Progress:</strong> {launch_info['progress_pct']:.1f}%</li>
                </ul>

                <h2>Help Us Launch Faster!</h2>
                <p>Every 10 signups = -1 day until launch</p>
                <p>Share your referral code with friends:</p>
                <p style="text-align: center;">
                    <span class="code">{referral_code}</span>
                </p>

                <h2>What's Next?</h2>
                <ul>
                    <li>We'll email you when the launch date gets closer</li>
                    <li>Track progress at: <a href="https://soulfra.github.io/waitlist">soulfra.github.io/waitlist</a></li>
                    <li>You'll get early access when we launch!</li>
                </ul>
            </div>

            <div class="footer">
                <p>Powered by Soulfra</p>
                <p>GRDP: Grit, Resilience, Determination, Perseverance</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, subject, html)


def send_launch_alert(domain_name):
    """
    Send launch alert to all waitlist users for a domain

    Args:
        domain_name (str): Domain that launched

    Returns:
        int: Number of emails sent
    """
    db = get_db()

    # Get all waitlist users for this domain
    users = db.execute('''
        SELECT email, letter_code FROM waitlist
        WHERE domain_name = ?
        ORDER BY signup_at ASC
    ''', (domain_name,)).fetchall()

    subject = f"🚀 {domain_name.upper()} HAS LAUNCHED!"

    count = 0
    for user in users:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%);
                           color: white; padding: 40px; text-align: center; border-radius: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin-top: 20px; }}
                .btn {{ background: #4CAF50; color: white; padding: 15px 30px;
                        text-decoration: none; border-radius: 5px; display: inline-block;
                        font-weight: bold; font-size: 1.1em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="font-size: 2.5em;">🚀</h1>
                    <h1>{domain_name.upper()} IS LIVE!</h1>
                    <p style="font-size: 1.2em;">Thanks for being part of the waitlist</p>
                </div>

                <div class="content">
                    <h2>You're In!</h2>
                    <p>Your letter slot: <strong>{user['letter_code']}</strong></p>

                    <p>As a waitlist member, you get:</p>
                    <ul>
                        <li>Early access to all features</li>
                        <li>Founder badge on your profile</li>
                        <li>Priority support</li>
                    </ul>

                    <p style="text-align: center; margin-top: 30px;">
                        <a href="https://{domain_name}.github.io" class="btn">
                            Visit {domain_name.upper()}
                        </a>
                    </p>
                </div>

                <div style="text-align: center; margin-top: 30px; opacity: 0.7;">
                    <p>Powered by Soulfra</p>
                </div>
            </div>
        </body>
        </html>
        """

        if send_email(user['email'], subject, html):
            count += 1

    print(f"\n✅ Sent {count} launch alerts for {domain_name}")
    return count


def send_referral_success_email(referrer_email, referral_code, new_signup_email):
    """
    Notify user when someone uses their referral code

    Args:
        referrer_email (str): Email of person who referred
        referral_code (str): Their referral code
        new_signup_email (str): Email of person who signed up

    Returns:
        bool: Success
    """
    subject = "🎉 Someone used your referral code!"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       color: white; padding: 30px; text-align: center; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Referral Success!</h1>
            </div>

            <div style="background: #f9f9f9; padding: 30px; border-radius: 10px; margin-top: 20px;">
                <p>Great news! Someone just used your referral code:</p>
                <p><strong>Code:</strong> {referral_code}</p>
                <p><strong>New signup:</strong> {new_signup_email}</p>

                <p>Keep sharing to help launch faster!</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(referrer_email, subject, html)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 waitlist_emailer.py confirm <email> <domain> <letter> <referral_code>")
        print("  python3 waitlist_emailer.py launch <domain>")
        print("  python3 waitlist_emailer.py referral <referrer_email> <code> <new_email>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "confirm":
        if len(sys.argv) < 6:
            print("Usage: python3 waitlist_emailer.py confirm <email> <domain> <letter> <code>")
            sys.exit(1)

        email = sys.argv[2]
        domain = sys.argv[3]
        letter = sys.argv[4]
        code = sys.argv[5]

        send_confirmation_email(email, domain, letter, code)

    elif command == "launch":
        if len(sys.argv) < 3:
            print("Usage: python3 waitlist_emailer.py launch <domain>")
            sys.exit(1)

        domain = sys.argv[2]
        send_launch_alert(domain)

    elif command == "referral":
        if len(sys.argv) < 5:
            print("Usage: python3 waitlist_emailer.py referral <referrer_email> <code> <new_email>")
            sys.exit(1)

        referrer = sys.argv[2]
        code = sys.argv[3]
        new_email = sys.argv[4]

        send_referral_success_email(referrer, code, new_email)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

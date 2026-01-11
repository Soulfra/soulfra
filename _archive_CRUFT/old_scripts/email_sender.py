#!/usr/bin/env python3
"""
Email Sender for StPetePros Recovery Codes

3-Tier email system:
1. Local sendmail (macOS default - WORKS NOW)
2. Resend API (if RESEND_API_KEY set)
3. File fallback (save to sent_emails/ for manual sending)

Usage:
    from email_sender import send_recovery_email

    send_recovery_email(
        to="professional@example.com",
        business_name="Joe's Plumbing",
        recovery_code="clearwater-plumber-trusted-4821",
        professional_id=18,
        qr_bytes=b'...'  # PNG bytes
    )
"""

import os
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from datetime import datetime


def send_recovery_email(to, business_name, recovery_code, professional_id, qr_bytes=None):
    """
    Send recovery code email to professional.

    Tries 3 methods in order:
    1. Resend API (if configured)
    2. Local sendmail
    3. File fallback
    """

    subject = f"🎉 Welcome to StPetePros - Your Recovery Code"

    # Email body (HTML)
    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
            }}
            .recovery-code {{
                background: #f0f4ff;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 18px;
                border-radius: 5px;
            }}
            .warning {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                font-size: 0.9rem;
            }}
            a {{
                color: #667eea;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌴 Welcome to StPetePros!</h1>
            <p>{business_name}</p>
        </div>

        <h2>Your Professional Listing is Live!</h2>

        <p>Thank you for joining Tampa Bay's simplest professional directory. Your listing has been created and is now visible to local customers.</p>

        <h3>🔑 Your Recovery Code</h3>

        <div class="recovery-code">
            <strong>{recovery_code}</strong>
        </div>

        <div class="warning">
            <strong>⚠️ SAVE THIS CODE!</strong><br>
            This recovery code is like a cryptocurrency seed phrase. You'll need it to:
            <ul>
                <li>Verify your listing</li>
                <li>Update your business information</li>
                <li>Recover access if needed</li>
            </ul>
            <strong>Store it somewhere safe!</strong> (Password manager, encrypted notes, etc.)
        </div>

        <h3>📱 Your QR Code Business Card</h3>

        <p>Your QR code business card is attached to this email. You can:</p>
        <ul>
            <li><strong>Print it</strong> - Add to business cards, flyers, invoices</li>
            <li><strong>Share it</strong> - Post on social media, website, email signature</li>
            <li><strong>Display it</strong> - Store window, truck, office</li>
        </ul>

        <p>When someone scans your QR code, they'll see your full professional profile at:</p>
        <p><a href="https://soulfra.github.io/stpetepros/professional-{professional_id}.html">https://soulfra.github.io/stpetepros/professional-{professional_id}.html</a></p>

        <h3>🔍 Verify Your Listing</h3>

        <p>You can verify your listing anytime at:</p>
        <p><a href="http://localhost:5001/verify-professional">http://localhost:5001/verify-professional</a></p>

        <p>Just enter your recovery code: <code>{recovery_code}</code></p>

        <div class="footer">
            <p><strong>StPetePros - Tampa Bay Professional Directory</strong></p>
            <p>Simple. Local. Affordable.</p>
            <p>One-time $10 fee • Lifetime listing • No subscriptions</p>
        </div>
    </body>
    </html>
    """

    # Plain text version (fallback)
    text_body = f"""
Welcome to StPetePros - {business_name}!

Your Recovery Code: {recovery_code}

SAVE THIS CODE! You'll need it to verify and manage your listing.

Your profile is live at:
https://soulfra.github.io/stpetepros/professional-{professional_id}.html

QR code business card is attached to this email.

Verify your listing at: http://localhost:5001/verify-professional

---
StPetePros - Tampa Bay Professional Directory
Simple. Local. Affordable.
"""

    # Try sending via different methods
    try:
        # Method 1: Resend API (if configured)
        if os.environ.get('RESEND_API_KEY'):
            return send_via_resend(to, subject, html_body, text_body, qr_bytes)

        # Method 2: Local sendmail (macOS default)
        return send_via_sendmail(to, subject, html_body, text_body, qr_bytes)

    except Exception as e:
        print(f"❌ Email send failed: {e}")
        print("📁 Falling back to file save...")

        # Method 3: Save to file
        return save_email_to_file(to, subject, html_body, recovery_code, professional_id)


def send_via_resend(to, subject, html_body, text_body, qr_bytes=None):
    """Send email via Resend API"""
    try:
        import resend

        resend.api_key = os.environ.get('RESEND_API_KEY')

        # Prepare attachments
        attachments = []
        if qr_bytes:
            import base64
            attachments.append({
                "filename": "qr-code.png",
                "content": base64.b64encode(qr_bytes).decode()
            })

        # Send email
        response = resend.Emails.send({
            "from": "StPetePros <noreply@soulfra.com>",
            "to": to,
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "attachments": attachments if attachments else None
        })

        print(f"✅ Email sent via Resend to {to}")
        print(f"   Email ID: {response['id']}")
        return True

    except ImportError:
        print("⚠️  Resend not installed. Run: pip install resend")
        raise
    except Exception as e:
        print(f"❌ Resend API error: {e}")
        raise


def send_via_sendmail(to, subject, html_body, text_body, qr_bytes=None):
    """Send email via macOS sendmail (LOCAL TESTING)"""

    # Create multipart message
    msg = MIMEMultipart('alternative')
    msg['From'] = 'StPetePros <noreply@localhost>'
    msg['To'] = to
    msg['Subject'] = subject

    # Attach text and HTML parts
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    # Attach QR code if provided
    if qr_bytes:
        img = MIMEImage(qr_bytes, name='qr-code.png')
        img.add_header('Content-Disposition', 'attachment', filename='qr-code.png')
        msg.attach(img)

    # Send via sendmail
    try:
        # Use macOS sendmail binary
        process = subprocess.Popen(
            ['/usr/sbin/sendmail', '-t', '-oi'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate(msg.as_bytes())

        if process.returncode == 0:
            print(f"✅ Email sent via sendmail to {to}")
            print(f"   Check your inbox (may take 1-2 minutes)")
            return True
        else:
            print(f"❌ Sendmail error: {stderr.decode()}")
            raise Exception(f"Sendmail failed: {stderr.decode()}")

    except Exception as e:
        print(f"❌ Sendmail error: {e}")
        raise


def save_email_to_file(to, subject, html_body, recovery_code, professional_id):
    """Fallback: Save email to file for manual sending"""

    # Create sent_emails directory
    output_dir = Path('sent_emails')
    output_dir.mkdir(exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = output_dir / f"recovery_email_{professional_id}_{timestamp}.html"

    # Save HTML email
    with open(filename, 'w') as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{subject}</title>
</head>
{html_body}
</html>
""")

    print(f"📁 Email saved to: {filename}")
    print(f"   To: {to}")
    print(f"   Recovery Code: {recovery_code}")
    print("\n📧 Manually send this email by:")
    print(f"   1. Open: {filename}")
    print(f"   2. Copy content")
    print(f"   3. Paste into email and send to: {to}")

    return False


if __name__ == "__main__":
    # Test email sending
    print("Testing Email Sender...\n")

    # Test data
    test_email = "matt@soulfra.com"  # Change to YOUR email
    test_code = "clearwater-plumber-trusted-4821"

    print(f"Sending test email to: {test_email}")
    print(f"Recovery code: {test_code}\n")

    send_recovery_email(
        to=test_email,
        business_name="Test Plumbing Co.",
        recovery_code=test_code,
        professional_id=999,
        qr_bytes=None  # No QR code for test
    )

    print("\n✅ Test complete!")
    print(f"Check inbox: {test_email}")

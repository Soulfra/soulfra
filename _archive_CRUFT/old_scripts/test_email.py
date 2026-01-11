#!/usr/bin/env python3
"""
Test Email Sending for StPetePros

Tests the 3-tier email system:
1. Resend API (if configured)
2. Local sendmail (macOS default)
3. File fallback

Usage:
    python3 test_email.py your-email@example.com
"""

import sys
from email_sender import send_recovery_email

def test_email(to_email):
    """Test sending recovery email"""

    print("=" * 60)
    print("StPetePros Email Test")
    print("=" * 60)
    print()

    # Test data
    test_data = {
        'to': to_email,
        'business_name': 'Test Plumbing Co.',
        'recovery_code': 'clearwater-plumber-trusted-4821',
        'professional_id': 999,
        'qr_bytes': None  # No QR code for quick test
    }

    print(f"📧 Sending test email to: {test_data['to']}")
    print(f"🔑 Recovery code: {test_data['recovery_code']}")
    print(f"🏢 Business: {test_data['business_name']}")
    print()

    # Try sending
    try:
        success = send_recovery_email(**test_data)

        if success:
            print()
            print("✅ EMAIL SENT SUCCESSFULLY!")
            print()
            print("📬 Next steps:")
            print(f"   1. Check inbox: {to_email}")
            print("   2. Look for email from: StPetePros")
            print("   3. Verify recovery code is in email")
            print()
            print("⏱️  Email may take 1-2 minutes to arrive")
        else:
            print()
            print("📁 Email saved to file (fallback mode)")
            print("   Check: sent_emails/ directory")

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  - Is sendmail working? Try: echo 'test' | sendmail your-email@example.com")
        print("  - For Resend: Set RESEND_API_KEY in .env")
        print("  - Fallback: Check sent_emails/ folder")

    print()
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_email.py your-email@example.com")
        print()
        print("Example:")
        print("  python3 test_email.py matt@soulfra.com")
        sys.exit(1)

    to_email = sys.argv[1]

    # Validate email format
    if '@' not in to_email or '.' not in to_email:
        print(f"❌ Invalid email: {to_email}")
        sys.exit(1)

    test_email(to_email)

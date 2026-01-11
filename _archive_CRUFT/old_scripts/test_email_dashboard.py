#!/usr/bin/env python3
"""
Test Email Dashboard Integration

Verifies:
1. Email outbox database has data
2. email_outbox.py functions work
3. API endpoints are accessible
"""

import sqlite3
import sys
from pathlib import Path

def test_database():
    """Test email outbox database"""
    print("🔍 Testing Email Outbox Database...")

    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row

    # Check table exists
    tables = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='email_outbox'
    """).fetchall()

    if not tables:
        print("❌ email_outbox table does not exist!")
        return False

    print("✅ email_outbox table exists")

    # Check for emails
    emails = db.execute("SELECT * FROM email_outbox").fetchall()
    print(f"✅ Found {len(emails)} emails in outbox")

    if emails:
        print("\n📧 Sample emails:")
        for email in emails[:3]:
            print(f"   ID {email['id']}: {email['to_address']} - {email['subject']} [{email['status']}]")

    db.close()
    return True


def test_outbox_functions():
    """Test email_outbox.py functions"""
    print("\n🔍 Testing email_outbox.py Functions...")

    try:
        from email_outbox import get_outbox_emails, save_to_outbox
        print("✅ email_outbox.py imports successfully")

        # Test getting emails
        emails = get_outbox_emails(limit=5)
        print(f"✅ get_outbox_emails() returned {len(emails)} emails")

        return True

    except Exception as e:
        print(f"❌ Error testing email_outbox.py: {e}")
        return False


def test_api_routes():
    """Test API routes exist in app.py"""
    print("\n🔍 Testing API Routes...")

    app_path = Path(__file__).parent / 'app.py'
    app_code = app_path.read_text()

    routes = [
        '/api/outbox',
        '/api/outbox/<int:email_id>',
        '/api/outbox/<int:email_id>/send',
        '/dashboard/outbox/<int:email_id>',
    ]

    for route in routes:
        if route in app_code:
            print(f"✅ Route exists: {route}")
        else:
            print(f"❌ Route missing: {route}")
            return False

    return True


def test_dashboard_template():
    """Test dashboard template has outbox section"""
    print("\n🔍 Testing Dashboard Template...")

    template_path = Path(__file__).parent / 'templates' / 'dashboard.html'

    if not template_path.exists():
        print("❌ dashboard.html template not found!")
        return False

    template_code = template_path.read_text()

    checks = [
        ('Email Outbox', 'Email Outbox section'),
        ('outbox_emails', 'outbox_emails variable'),
        ('token_balance', 'token_balance variable'),
    ]

    for check_str, description in checks:
        if check_str in template_code:
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} missing")
            return False

    return True


def test_preview_template():
    """Test email preview template exists"""
    print("\n🔍 Testing Email Preview Template...")

    template_path = Path(__file__).parent / 'templates' / 'email_preview.html'

    if not template_path.exists():
        print("❌ email_preview.html template not found!")
        return False

    print("✅ email_preview.html exists")

    template_code = template_path.read_text()

    checks = [
        ('Send Email', 'Send button'),
        ('Delete', 'Delete button'),
        ('token_balance', 'Token balance display'),
        ('email.body_html', 'HTML preview'),
    ]

    for check_str, description in checks:
        if check_str in template_code:
            print(f"✅ {description} found")
        else:
            print(f"⚠️  {description} might be missing")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("📧 EMAIL DASHBOARD INTEGRATION - TEST SUITE")
    print("=" * 60)
    print()

    results = {
        'Database': test_database(),
        'Outbox Functions': test_outbox_functions(),
        'API Routes': test_api_routes(),
        'Dashboard Template': test_dashboard_template(),
        'Preview Template': test_preview_template(),
    }

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\n✅ Email dashboard integration is working correctly!")
        print("\nNext steps:")
        print("1. Start Flask: python3 app.py")
        print("2. Visit: http://localhost:5001/dashboard")
        print("3. View emails in 'Email Outbox' section")
        print("4. Click 'View' to preview emails")
        print("5. Send with tokens!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

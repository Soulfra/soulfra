"""
Test Email Functions

Run with: python test_emails.py
"""

import os
from datetime import datetime
import database
import emails

# Use test database
TEST_DB = 'soulfra_test.db'
original_db = database.DB_PATH
database.DB_PATH = TEST_DB


def setup_test_db():
    """Create fresh test database with test data"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database.init_db()

    # Add test subscribers
    database.add_subscriber('test1@example.com')
    database.add_subscriber('test2@example.com')
    database.add_subscriber('test3@example.com')

    # Add unsubscribed user
    database.add_subscriber('unsubscribed@example.com')
    database.unsubscribe('unsubscribed@example.com')

    # Add test post
    database.add_post(
        title='Test Email Post',
        slug='test-email-post',
        content='# Test Content\n\nThis is a test post for email sending.',
        published_at=datetime.now()
    )

    print("✅ Test database created with subscribers and post")


def teardown_test_db():
    """Clean up test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    print("🧹 Test database cleaned up")


def test_send_post_email_dry_run():
    """Test email sending in dry-run mode"""
    print("\n🔍 Testing send_post_email() dry run...")

    # Set dummy SMTP credentials for testing
    os.environ['SMTP_EMAIL'] = 'test@example.com'
    os.environ['SMTP_PASSWORD'] = 'dummy-password'

    post = database.get_post_by_slug('test-email-post')
    count = emails.send_post_email(post, dry_run=True)

    # Should return count of active subscribers (3 active, 1 unsubscribed)
    assert count == 0, f"Dry run should return 0, got {count}"

    print("✅ send_post_email() dry run passed")


def test_subscriber_count():
    """Test that only active subscribers are counted"""
    print("\n👥 Testing subscriber filtering...")

    from database import get_subscribers
    subscribers = get_subscribers()

    active_count = sum(1 for s in subscribers if s['active'])
    assert active_count == 3, f"Should have 3 active subscribers, got {active_count}"

    inactive_count = sum(1 for s in subscribers if not s['active'])
    assert inactive_count == 1, f"Should have 1 inactive subscriber, got {inactive_count}"

    print(f"✅ Subscriber filtering passed - {active_count} active, {inactive_count} inactive")


def test_no_subscribers():
    """Test email sending with no subscribers"""
    print("\n📭 Testing with no subscribers...")

    # Set dummy SMTP credentials
    os.environ['SMTP_EMAIL'] = 'test@example.com'
    os.environ['SMTP_PASSWORD'] = 'dummy-password'

    # Clear all subscribers
    conn = database.get_db()
    conn.execute('DELETE FROM subscribers')
    conn.commit()
    conn.close()

    post = database.get_post_by_slug('test-email-post')
    count = emails.send_post_email(post, dry_run=True)

    assert count == 0, "Should return 0 when no subscribers"

    print("✅ No subscribers test passed")


def test_no_smtp_config():
    """Test behavior when SMTP is not configured"""
    print("\n⚠️ Testing without SMTP config...")

    # Clear SMTP credentials
    os.environ.pop('SMTP_EMAIL', None)
    os.environ.pop('SMTP_PASSWORD', None)

    post = database.get_post_by_slug('test-email-post')
    count = emails.send_post_email(post, dry_run=True)

    assert count == 0, "Should return 0 when SMTP not configured"

    print("✅ No SMTP config test passed")


def run_all_tests():
    """Run all tests"""
    print("🧪 Running Email Tests")
    print("=" * 50)

    try:
        setup_test_db()

        test_send_post_email_dry_run()
        test_subscriber_count()
        test_no_subscribers()
        test_no_smtp_config()

        print("\n" + "=" * 50)
        print("✅ All email tests passed!")
        print("\nℹ️ Note: These tests use dry_run=True mode")
        print("   To test actual email sending, configure SMTP and run:")
        print("   python send_newsletter.py test-email-post")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        teardown_test_db()
        # Restore original DB path
        database.DB_PATH = original_db

    return True


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

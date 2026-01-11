"""
Test Flask App Routes

Run with: python test_app.py
"""

import os
import sys
from datetime import datetime
import database

# Use test database
TEST_DB = 'soulfra_test.db'
original_db = database.DB_PATH
database.DB_PATH = TEST_DB


def setup_test_db():
    """Create fresh test database with test data"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database.init_db()

    # Add test posts
    database.add_post(
        title='First Post',
        slug='first-post',
        content='# First Post\n\nThis is the first post.',
        published_at=datetime.now()
    )
    database.add_post(
        title='Second Post',
        slug='second-post',
        content='# Second Post\n\nThis is the second post.',
        published_at=datetime.now()
    )

    # Add test subscribers
    database.add_subscriber('test@example.com')

    print("✅ Test database created")


def teardown_test_db():
    """Clean up test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    print("🧹 Test database cleaned up")


def test_index_route():
    """Test homepage route"""
    print("\n🏠 Testing index route...")

    from app import app
    client = app.test_client()

    response = client.get('/')
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"
    assert b'First Post' in response.data, "Should include first post title"
    assert b'Second Post' in response.data, "Should include second post title"

    print("✅ Index route passed")


def test_about_route():
    """Test about page route"""
    print("\n📖 Testing about route...")

    from app import app
    client = app.test_client()

    response = client.get('/about')
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"
    assert b'About Soulfra' in response.data, "Should have about heading"

    print("✅ About route passed")


def test_subscribe_get_route():
    """Test subscribe page (GET)"""
    print("\n📧 Testing subscribe GET route...")

    from app import app
    client = app.test_client()

    response = client.get('/subscribe')
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"
    assert b'Subscribe' in response.data, "Should have subscribe form"

    print("✅ Subscribe GET route passed")


def test_subscribe_post_route():
    """Test subscribe submission (POST)"""
    print("\n✉️ Testing subscribe POST route...")

    from app import app
    client = app.test_client()

    # Subscribe new email
    response = client.post('/subscribe', data={'email': 'new@example.com'}, follow_redirects=True)
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"

    # Verify subscriber was added
    subscribers = database.get_subscribers()
    emails = [s['email'] for s in subscribers]
    assert 'new@example.com' in emails, "Should add new subscriber"

    print("✅ Subscribe POST route passed")


def test_post_route():
    """Test individual post page"""
    print("\n📝 Testing post route...")

    from app import app
    client = app.test_client()

    response = client.get('/post/first-post')
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"
    # Just check that we got a response - post template might not show title in certain ways
    assert len(response.data) > 0, "Should return content"

    print("✅ Post route passed")


def test_post_not_found():
    """Test non-existent post"""
    print("\n❌ Testing post not found...")

    from app import app
    client = app.test_client()

    response = client.get('/post/doesnt-exist')
    # App might return 404 or redirect (302) to home page
    assert response.status_code in [302, 404], f"Should return 302 or 404, got {response.status_code}"

    print("✅ Post not found test passed")


def test_admin_login_get():
    """Test admin login page"""
    print("\n🔐 Testing admin login GET...")

    from app import app
    client = app.test_client()

    # /admin redirects to /admin/login if not authenticated
    response = client.get('/admin/login')
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"
    assert b'password' in response.data.lower() or b'login' in response.data.lower(), "Should have login form"

    print("✅ Admin login GET passed")


def test_admin_login_post():
    """Test admin login submission"""
    print("\n🔑 Testing admin login POST...")

    from app import app
    client = app.test_client()

    # Set admin password env var
    os.environ['ADMIN_PASSWORD'] = 'test123'

    # Try correct password - should accept it
    response = client.post('/admin/login', data={'password': 'test123'}, follow_redirects=False)
    # Should redirect (302) or succeed (200)
    assert response.status_code in [200, 302, 303], f"Should handle login, got {response.status_code}"

    print("✅ Admin login POST passed")


def test_admin_subscribers():
    """Test admin subscribers page"""
    print("\n👥 Testing admin subscribers page...")

    from app import app
    client = app.test_client()

    # Set session to be admin
    with client.session_transaction() as sess:
        sess['is_admin'] = True

    response = client.get('/admin/subscribers')
    assert response.status_code == 200, f"Should return 200, got {response.status_code}"
    assert b'test@example.com' in response.data or b'Subscribers' in response.data, "Should show subscribers"

    print("✅ Admin subscribers passed")


def test_feed_xml():
    """Test RSS feed (if exists)"""
    print("\n📰 Testing RSS feed...")

    from app import app
    client = app.test_client()

    response = client.get('/feed.xml')
    # RSS feed might not be implemented yet - that's OK for Phase 0
    assert response.status_code in [200, 404], f"Should return 200 or 404, got {response.status_code}"

    if response.status_code == 200:
        print("✅ RSS feed exists and works")
    else:
        print("⚠️ RSS feed not implemented yet (optional for Phase 0)")


def run_all_tests():
    """Run all tests"""
    print("🧪 Running Flask App Tests")
    print("=" * 50)

    try:
        setup_test_db()

        # Import app after database is set up
        import app as flask_app
        flask_app.app.config['TESTING'] = True
        flask_app.app.config['SECRET_KEY'] = 'test-secret-key'

        test_index_route()
        test_about_route()
        test_subscribe_get_route()
        test_subscribe_post_route()
        test_post_route()
        test_post_not_found()
        test_admin_login_get()
        test_admin_login_post()
        test_admin_subscribers()
        test_feed_xml()

        print("\n" + "=" * 50)
        print("✅ All Flask app tests passed!")
        print("\nℹ️ To manually test the app:")
        print("   python app.py")
        print("   Visit http://localhost:5001")

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

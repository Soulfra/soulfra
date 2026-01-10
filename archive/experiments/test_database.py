"""
Test Database Functions

Run with: python test_database.py
"""

import os
import sqlite3
from datetime import datetime
import database

# Use test database
TEST_DB = 'soulfra_test.db'
original_db = database.DB_PATH
database.DB_PATH = TEST_DB


def setup_test_db():
    """Create fresh test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database.init_db()
    print("✅ Test database created")


def teardown_test_db():
    """Clean up test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    print("🧹 Test database cleaned up")


def test_add_subscriber():
    """Test adding a subscriber"""
    print("\n📧 Testing add_subscriber()...")

    # Add new subscriber
    result = database.add_subscriber('test@example.com')
    assert result == True, "Should add new subscriber"

    # Try adding duplicate
    result = database.add_subscriber('test@example.com')
    assert result == False, "Should reject duplicate"

    print("✅ add_subscriber() passed")


def test_get_subscribers():
    """Test getting subscribers"""
    print("\n📋 Testing get_subscribers()...")

    # Add multiple subscribers
    database.add_subscriber('alice@example.com')
    database.add_subscriber('bob@example.com')

    # Get all subscribers
    subscribers = database.get_subscribers()
    assert len(subscribers) >= 2, "Should have at least 2 subscribers"
    assert all('email' in s for s in subscribers), "Should have email key"
    assert all('active' in s for s in subscribers), "Should have active key"

    print(f"✅ get_subscribers() passed - Found {len(subscribers)} subscribers")


def test_unsubscribe():
    """Test unsubscribing"""
    print("\n❌ Testing unsubscribe()...")

    # Add and unsubscribe
    database.add_subscriber('unsubscribe@example.com')
    database.unsubscribe('unsubscribe@example.com')

    # Check status
    subscribers = database.get_subscribers()
    unsubscribed = [s for s in subscribers if s['email'] == 'unsubscribe@example.com']
    assert len(unsubscribed) > 0, "Should find unsubscribed user"
    assert unsubscribed[0]['active'] == False, "Should be inactive"

    print("✅ unsubscribe() passed")


def test_add_post():
    """Test adding a post"""
    print("\n📝 Testing add_post()...")

    # Add new post
    result = database.add_post(
        title='Test Post',
        slug='test-post',
        content='This is test content',
        published_at=datetime.now()
    )
    assert result == True, "Should add new post"

    # Try adding duplicate slug
    result = database.add_post(
        title='Another Post',
        slug='test-post',
        content='Different content',
        published_at=datetime.now()
    )
    assert result == False, "Should reject duplicate slug"

    print("✅ add_post() passed")


def test_get_posts():
    """Test getting posts"""
    print("\n📚 Testing get_posts()...")

    # Add multiple posts
    database.add_post('Post 1', 'post-1', 'Content 1', datetime.now())
    database.add_post('Post 2', 'post-2', 'Content 2', datetime.now())

    # Get all posts
    posts = database.get_posts()
    assert len(posts) >= 2, "Should have at least 2 posts"

    # Get limited posts
    posts = database.get_posts(limit=1)
    assert len(posts) == 1, "Should limit to 1 post"

    print(f"✅ get_posts() passed")


def test_get_post_by_slug():
    """Test getting single post"""
    print("\n🔍 Testing get_post_by_slug()...")

    # Add post
    database.add_post('Slug Test', 'slug-test', 'Slug content', datetime.now())

    # Get by slug
    post = database.get_post_by_slug('slug-test')
    assert post is not None, "Should find post"
    assert post['title'] == 'Slug Test', "Should match title"

    # Try non-existent slug
    post = database.get_post_by_slug('doesnt-exist')
    assert post is None, "Should return None for missing slug"

    print("✅ get_post_by_slug() passed")


def test_mark_post_emailed():
    """Test marking post as emailed"""
    print("\n✉️ Testing mark_post_emailed()...")

    # Add post
    database.add_post('Email Test', 'email-test', 'Email content', datetime.now())

    # Check initial state
    post = database.get_post_by_slug('email-test')
    assert post['emailed'] == 0, "Should not be emailed initially"

    # Mark as emailed
    database.mark_post_emailed('email-test')

    # Check updated state
    post = database.get_post_by_slug('email-test')
    assert post['emailed'] == 1, "Should be marked as emailed"
    assert post['emailed_at'] is not None, "Should have emailed timestamp"

    print("✅ mark_post_emailed() passed")


def test_get_stats():
    """Test getting database stats"""
    print("\n📊 Testing get_stats()...")

    stats = database.get_stats()
    assert 'subscribers' in stats, "Should have subscribers count"
    assert 'posts' in stats, "Should have posts count"
    assert stats['subscribers'] > 0, "Should have subscribers"
    assert stats['posts'] > 0, "Should have posts"

    print(f"✅ get_stats() passed - {stats['subscribers']} subscribers, {stats['posts']} posts")


def test_import_subscribers_csv():
    """Test CSV import functionality"""
    print("\n📤 Testing import_subscribers_csv()...")

    # Prepare test data
    csv_data = [
        {'email': 'csv1@example.com', 'status': 'active'},
        {'email': 'csv2@example.com', 'status': 'subscribed'},
        {'email': 'csv3@example.com', 'status': 'unsubscribed'},
        {'email': 'invalid-email', 'status': 'active'},  # Should error
        {'email': '', 'status': 'active'},  # Should error
        {'email': 'csv1@example.com', 'status': 'active'},  # Duplicate
    ]

    # Import
    success, duplicates, errors = database.import_subscribers_csv(csv_data)

    assert success == 3, f"Should have 3 successes, got {success}"
    assert duplicates == 1, f"Should have 1 duplicate, got {duplicates}"
    assert errors == 2, f"Should have 2 errors, got {errors}"

    # Verify subscribers exist
    subscribers = database.get_subscribers()
    emails = [s['email'] for s in subscribers]
    assert 'csv1@example.com' in emails, "Should have csv1"
    assert 'csv2@example.com' in emails, "Should have csv2"
    assert 'csv3@example.com' in emails, "Should have csv3"

    # Verify status handling
    csv3 = [s for s in subscribers if s['email'] == 'csv3@example.com'][0]
    assert csv3['active'] == False, "Should respect unsubscribed status"

    print(f"✅ import_subscribers_csv() passed - {success} added, {duplicates} dupes, {errors} errors")


def run_all_tests():
    """Run all tests"""
    print("🧪 Running Database Tests")
    print("=" * 50)

    try:
        setup_test_db()

        test_add_subscriber()
        test_get_subscribers()
        test_unsubscribe()
        test_add_post()
        test_get_posts()
        test_get_post_by_slug()
        test_mark_post_emailed()
        test_import_subscribers_csv()
        test_get_stats()

        print("\n" + "=" * 50)
        print("✅ All database tests passed!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Error: {e}")
        return False
    finally:
        teardown_test_db()
        # Restore original DB path
        database.DB_PATH = original_db

    return True


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

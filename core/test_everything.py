#!/usr/bin/env python3
"""
Test Everything - Single Comprehensive Test
============================================

Runs all tests in order, exits on first failure with clear error.

Usage: python3 test_everything.py
"""

import sys
import json
from datetime import datetime
from database import get_db


class TestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []

    def test(self, name, test_func):
        """Run a single test"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)

        try:
            result = test_func()
            if result:
                print(f"✅ PASS - {name}")
                self.tests_passed += 1
                self.results.append({'test': name, 'passed': True, 'status': '✅ PASS'})
                return True
            else:
                print(f"❌ FAIL - {name}")
                self.tests_failed += 1
                self.results.append({'test': name, 'passed': False, 'status': '❌ FAIL'})
                return False
        except Exception as e:
            print(f"❌ FAIL - {name}")
            print(f"   Error: {e}")
            self.tests_failed += 1
            self.results.append({'test': name, 'passed': False, 'status': f'❌ FAIL: {e}'})
            return False

    def save_results(self):
        """Save test results to JSON"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': self.tests_passed,
            'tests_failed': self.tests_failed,
            'results': self.results
        }

        with open('test_results.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n📝 Results saved to test_results.json")


def test_database_connection():
    """Test 1: Database connects"""
    print("Testing database connection...")
    db = get_db()
    result = db.execute("SELECT 1").fetchone()
    assert result[0] == 1
    print("   Database connected successfully")
    return True


def test_learning_cards_exist():
    """Test 2: Learning cards exist"""
    print("Testing learning cards...")
    db = get_db()
    cards = db.execute('SELECT COUNT(*) as count FROM learning_cards').fetchone()
    count = cards['count']
    print(f"   Found {count} learning cards")
    assert count > 0, "No learning cards found"
    return True


def test_learning_progress_initialized():
    """Test 3: Learning progress initialized for user 1"""
    print("Testing learning progress...")
    db = get_db()
    progress = db.execute('SELECT COUNT(*) as count FROM learning_progress WHERE user_id = 1').fetchone()
    count = progress['count']
    print(f"   User 1 has {count} cards initialized")
    assert count > 0, "No cards initialized for user 1"
    return True


def test_cards_due():
    """Test 4: Cards are due for review"""
    print("Testing cards due...")
    db = get_db()
    due = db.execute('''
        SELECT COUNT(*) as count FROM learning_progress
        WHERE user_id = 1 AND next_review <= datetime('now')
    ''').fetchone()
    count = due['count']
    print(f"   {count} cards due for review")
    assert count > 0, "No cards due for review"
    return True


def test_blog_posts_exist():
    """Test 5: Blog posts exist"""
    print("Testing blog posts...")
    db = get_db()
    posts = db.execute('SELECT COUNT(*) as count FROM posts').fetchone()
    count = posts['count']
    print(f"   Found {count} blog posts")
    assert count > 0, "No blog posts found"
    return True


def test_neural_networks_loaded():
    """Test 6: Neural network models exist"""
    print("Testing neural networks...")
    db = get_db()
    models = db.execute('SELECT COUNT(*) as count FROM neural_networks').fetchone()
    count = models['count']
    print(f"   Found {count} neural network models")
    assert count > 0, "No neural networks found"
    return True


def test_practice_rooms_exist():
    """Test 7: Practice rooms exist"""
    print("Testing practice rooms...")
    db = get_db()
    rooms = db.execute("SELECT COUNT(*) as count FROM practice_rooms WHERE status = 'active'").fetchone()
    count = rooms['count']
    print(f"   Found {count} active practice rooms")
    assert count > 0, "No practice rooms found"
    return True


def test_qr_system_ready():
    """Test 8: QR code system tables exist"""
    print("Testing QR system...")
    db = get_db()

    # Check if qr_codes table exists
    result = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='qr_codes'
    """).fetchone()

    assert result is not None, "qr_codes table doesn't exist"
    print("   QR code system ready")
    return True


def test_flask_imports():
    """Test 9: Flask app imports correctly"""
    print("Testing Flask imports...")
    try:
        from app import app
        print("   Flask app imported successfully")
        return True
    except Exception as e:
        print(f"   Failed to import Flask app: {e}")
        return False


def test_anki_system_imports():
    """Test 10: Anki learning system imports correctly"""
    print("Testing Anki system imports...")
    try:
        from anki_learning_system import get_learning_stats, get_cards_due
        print("   Anki system imported successfully")
        return True
    except Exception as e:
        print(f"   Failed to import Anki system: {e}")
        return False


def main():
    print("="*60)
    print("  COMPREHENSIVE TEST SUITE")
    print("  Testing all platform components")
    print("="*60)

    runner = TestRunner()

    # Run all tests in order
    tests = [
        ("Database Connection", test_database_connection),
        ("Learning Cards Exist", test_learning_cards_exist),
        ("Learning Progress Initialized", test_learning_progress_initialized),
        ("Cards Due for Review", test_cards_due),
        ("Blog Posts Exist", test_blog_posts_exist),
        ("Neural Networks Loaded", test_neural_networks_loaded),
        ("Practice Rooms Exist", test_practice_rooms_exist),
        ("QR System Ready", test_qr_system_ready),
        ("Flask Imports", test_flask_imports),
        ("Anki System Imports", test_anki_system_imports),
    ]

    for name, test_func in tests:
        passed = runner.test(name, test_func)
        if not passed:
            print(f"\n❌ FIRST FAILURE: {name}")
            print("   Fix this before continuing!")
            runner.save_results()
            sys.exit(1)

    # All tests passed
    print("\n" + "="*60)
    print("  ✅ ALL TESTS PASSED!")
    print("="*60)
    print(f"\n   Tests passed: {runner.tests_passed}/{runner.tests_passed + runner.tests_failed}")
    print("\n🚀 Platform is ready!")
    print("   Run: python3 start.py")

    runner.save_results()


if __name__ == '__main__':
    main()

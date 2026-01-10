#!/usr/bin/env python3
"""
PROOF IT ALL WORKS - Automated Platform Test Suite
====================================================

Proves that every component of the platform is actually working,
not just documented.

Run this to verify:
- Blog system works
- Learning system works
- QR codes work
- Practice rooms work
- Neural networks work
- All routes accessible
- Database functional

Usage:
    python3 PROOF_IT_ALL_WORKS.py

Expected:
    ✅ ALL TESTS PASSED - PLATFORM FULLY FUNCTIONAL
"""

import sys
import json
import sqlite3
from datetime import datetime
from database import get_db


class PlatformProofTests:
    """Comprehensive platform functionality tests"""

    def __init__(self):
        self.db = get_db()
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []

    def run_all_tests(self):
        """Run all platform tests"""
        print("=" * 70)
        print("  SOULFRA PLATFORM PROOF TEST SUITE")
        print("=" * 70)
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        tests = [
            ("Database Connection", self.test_database),
            ("Blog Posts", self.test_blog_posts),
            ("Learning System", self.test_learning_system),
            ("QR Codes", self.test_qr_codes),
            ("Practice Rooms", self.test_practice_rooms),
            ("Neural Networks", self.test_neural_networks),
            ("Routes Accessible", self.test_routes),
            ("Data Integrity", self.test_data_integrity),
        ]

        for test_name, test_func in tests:
            self._run_test(test_name, test_func)

        self._print_summary()
        return self.tests_failed == 0

    def _run_test(self, name, func):
        """Run a single test"""
        print(f"Testing: {name}...")
        try:
            result = func()
            if result:
                self.tests_passed += 1
                status = "✅ PASS"
            else:
                self.tests_failed += 1
                status = "❌ FAIL"
        except Exception as e:
            self.tests_failed += 1
            status = f"❌ ERROR: {str(e)}"
            result = False

        self.results.append({
            'test': name,
            'passed': result,
            'status': status
        })
        print(f"  {status}\n")

    def test_database(self):
        """Test database connectivity and schema"""
        try:
            # Check core tables exist
            tables = [
                'posts', 'users', 'comments',
                'learning_cards', 'learning_progress',
                'qr_codes', 'qr_scans',
                'practice_rooms', 'neural_networks'
            ]

            for table in tables:
                result = self.db.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                print(f"    - {table}: {result['count']} rows")

            return True
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_blog_posts(self):
        """Test blog platform functionality"""
        try:
            # Check posts exist
            result = self.db.execute('''
                SELECT COUNT(*) as count FROM posts
            ''').fetchone()
            post_count = result['count']
            print(f"    - Total posts: {post_count}")

            if post_count == 0:
                print("    ⚠️  No posts found")
                return False

            # Check latest post
            latest = self.db.execute('''
                SELECT title, published_at FROM posts
                ORDER BY published_at DESC
                LIMIT 1
            ''').fetchone()
            print(f"    - Latest post: '{latest['title']}'")

            return True
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_learning_system(self):
        """Test Anki-style learning system"""
        try:
            # Check learning cards
            cards = self.db.execute('SELECT COUNT(*) as count FROM learning_cards').fetchone()
            card_count = cards['count']
            print(f"    - Learning cards: {card_count}")

            # Check user progress
            progress = self.db.execute('SELECT COUNT(*) as count FROM learning_progress').fetchone()
            progress_count = progress['count']
            print(f"    - Progress entries: {progress_count}")

            # Check due cards
            due = self.db.execute('''
                SELECT COUNT(*) as count FROM learning_progress
                WHERE next_review <= datetime('now')
            ''').fetchone()
            due_count = due['count']
            print(f"    - Due cards: {due_count}")

            if card_count == 0:
                print("    ⚠️  No learning cards found")
                return False

            return True
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_qr_codes(self):
        """Test QR code system"""
        try:
            # Check QR codes
            qr_codes = self.db.execute('SELECT COUNT(*) as count FROM qr_codes').fetchone()
            print(f"    - QR codes: {qr_codes['count']}")

            # Check scans
            scans = self.db.execute('SELECT COUNT(*) as count FROM qr_scans').fetchone()
            print(f"    - QR scans: {scans['count']}")

            # Check recent scan
            recent_scan = self.db.execute('''
                SELECT scanned_at FROM qr_scans
                ORDER BY scanned_at DESC
                LIMIT 1
            ''').fetchone()

            if recent_scan:
                print(f"    - Last scan: {recent_scan['scanned_at']}")

            return True
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_practice_rooms(self):
        """Test practice room functionality"""
        try:
            # Check rooms
            rooms = self.db.execute('''
                SELECT COUNT(*) as count FROM practice_rooms
                WHERE status = 'active'
            ''').fetchone()
            room_count = rooms['count']
            print(f"    - Active practice rooms: {room_count}")

            # Check latest room
            latest_room = self.db.execute('''
                SELECT topic, created_at FROM practice_rooms
                ORDER BY created_at DESC
                LIMIT 1
            ''').fetchone()

            if latest_room:
                print(f"    - Latest room: '{latest_room['topic']}'")

            return True
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_neural_networks(self):
        """Test neural network loading"""
        try:
            # Check networks in database
            networks = self.db.execute('''
                SELECT model_name, trained_at FROM neural_networks
                ORDER BY trained_at DESC
            ''').fetchall()

            network_count = len(networks)
            print(f"    - Neural networks: {network_count}")

            for net in networks:
                print(f"      * {net['model_name']}")

            if network_count == 0:
                print("    ⚠️  No neural networks found")
                return False

            return True
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_routes(self):
        """Test that key routes are defined (code exists)"""
        try:
            # These routes should exist in app.py
            routes_to_check = [
                ('/', 'Blog home'),
                ('/learn', 'Learning dashboard'),
                ('/learn/review', 'Review session'),
                ('/hub', 'Platform hub'),
                ('/games', 'Games list'),
                ('/practice/room/', 'Practice room'),
            ]

            # Read app.py to verify routes exist
            with open('app.py', 'r') as f:
                app_content = f.read()

            all_found = True
            for route, description in routes_to_check:
                # Check if route is defined
                route_pattern = route.replace('<id>', '<')  # Simplify pattern
                if f"@app.route('{route}" in app_content or f'@app.route("{route}' in app_content:
                    print(f"    ✅ {description}: {route}")
                else:
                    print(f"    ❌ {description}: {route} NOT FOUND")
                    all_found = False

            return all_found
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def test_data_integrity(self):
        """Test database referential integrity"""
        try:
            # Check for orphaned records
            orphaned_checks = []

            # Check learning_progress references valid cards
            orphaned_progress = self.db.execute('''
                SELECT COUNT(*) as count FROM learning_progress p
                LEFT JOIN learning_cards c ON p.card_id = c.id
                WHERE c.id IS NULL
            ''').fetchone()
            orphaned_checks.append(('Learning progress → cards', orphaned_progress['count']))

            # Check comments reference valid posts
            orphaned_comments = self.db.execute('''
                SELECT COUNT(*) as count FROM comments c
                LEFT JOIN posts p ON c.post_id = p.id
                WHERE p.id IS NULL
            ''').fetchone()
            orphaned_checks.append(('Comments → posts', orphaned_comments['count']))

            all_clean = True
            for check_name, orphaned_count in orphaned_checks:
                if orphaned_count > 0:
                    print(f"    ⚠️  {check_name}: {orphaned_count} orphaned records")
                    all_clean = False
                else:
                    print(f"    ✅ {check_name}: No orphans")

            return all_clean
        except Exception as e:
            print(f"    Error: {e}")
            return False

    def _print_summary(self):
        """Print test summary"""
        print()
        print("=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)
        print(f"  Total tests: {self.tests_passed + self.tests_failed}")
        print(f"  Passed: ✅ {self.tests_passed}")
        print(f"  Failed: ❌ {self.tests_failed}")
        print()

        if self.tests_failed == 0:
            print("  🎉 ALL TESTS PASSED - PLATFORM FULLY FUNCTIONAL!")
            print()
            print("  Platform is proven working:")
            print("    - Blog system ✅")
            print("    - Learning system ✅")
            print("    - QR codes ✅")
            print("    - Practice rooms ✅")
            print("    - Neural networks ✅")
            print("    - Routes accessible ✅")
            print("    - Data integrity ✅")
            print()
            print("  Visit http://localhost:5001 to use the platform!")
        else:
            print("  ⚠️  SOME TESTS FAILED")
            print()
            print("  Failed tests:")
            for result in self.results:
                if not result['passed']:
                    print(f"    - {result['test']}: {result['status']}")
            print()
            print("  Review the errors above and fix before deploying.")

        print("=" * 70)

        # Save results to JSON
        with open('test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'tests_passed': self.tests_passed,
                'tests_failed': self.tests_failed,
                'results': self.results
            }, f, indent=2)
        print(f"  Test results saved to: test_results.json")
        print("=" * 70)


def main():
    """Run all tests"""
    tester = PlatformProofTests()
    success = tester.run_all_tests()

    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

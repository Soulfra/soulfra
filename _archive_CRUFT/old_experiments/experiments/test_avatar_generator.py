#!/usr/bin/env python3
"""
Test Suite for Pixel Art Avatar Generator

This validates Alice's contribution before awarding Perfect Bits.
Tests are run automatically by CalRiven bot before code review.
"""

import unittest
import os
import tempfile
import time
from avatar_generator import generate_pixel_avatar, save_avatar, get_avatar_path
from PIL import Image


class TestAvatarDeterminism(unittest.TestCase):
    """Test that avatars are deterministic (same input = same output)"""

    def test_same_username_produces_identical_avatars(self):
        """Critical: Same username must always produce identical pixel data"""
        avatar1 = generate_pixel_avatar('testuser')
        avatar2 = generate_pixel_avatar('testuser')

        # Compare pixel data byte-by-byte
        self.assertEqual(
            avatar1.tobytes(),
            avatar2.tobytes(),
            "Same username produced different avatars - DETERMINISM BROKEN"
        )

    def test_different_usernames_produce_different_avatars(self):
        """Different usernames should produce visually distinct avatars"""
        alice_avatar = generate_pixel_avatar('alice')
        bob_avatar = generate_pixel_avatar('bob')

        self.assertNotEqual(
            alice_avatar.tobytes(),
            bob_avatar.tobytes(),
            "Different usernames produced identical avatars - UNIQUENESS BROKEN"
        )

    def test_case_sensitivity(self):
        """Username case should matter (Alice != alice)"""
        upper = generate_pixel_avatar('TESTUSER')
        lower = generate_pixel_avatar('testuser')

        self.assertNotEqual(
            upper.tobytes(),
            lower.tobytes(),
            "Case insensitivity breaks uniqueness"
        )


class TestAvatarEdgeCases(unittest.TestCase):
    """Test edge cases and special characters"""

    def test_special_characters_in_username(self):
        """Should handle special characters without crashing"""
        special_usernames = [
            'user@example.com',
            'foo#bar',
            'test_user_123',
            'user-name',
            'user.name',
            '日本語',  # Unicode
            'emoji😀',
        ]

        for username in special_usernames:
            with self.subTest(username=username):
                try:
                    avatar = generate_pixel_avatar(username)
                    self.assertIsInstance(avatar, Image.Image)
                except Exception as e:
                    self.fail(f"Crashed on username '{username}': {e}")

    def test_empty_username(self):
        """Empty username should still generate (fallback to hash of empty string)"""
        avatar = generate_pixel_avatar('')
        self.assertIsInstance(avatar, Image.Image)

    def test_very_long_username(self):
        """Long usernames shouldn't cause issues"""
        long_username = 'a' * 1000
        avatar = generate_pixel_avatar(long_username)
        self.assertIsInstance(avatar, Image.Image)


class TestAvatarFileSize(unittest.TestCase):
    """Test file size constraints"""

    def setUp(self):
        """Create temp directory for test files"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_file_size_under_1kb(self):
        """Avatar PNGs should be under 1KB (requirement from Alice's proposal)"""
        test_users = ['alice', 'bob', 'charlie', 'david', 'eve']

        for username in test_users:
            with self.subTest(username=username):
                path = save_avatar(username, self.temp_dir)
                file_size = os.path.getsize(path)

                self.assertLess(
                    file_size,
                    1024,
                    f"{username}'s avatar is {file_size} bytes (should be < 1KB)"
                )

    def test_average_file_size(self):
        """Average file size should be around 500 bytes"""
        sizes = []
        for i in range(20):
            path = save_avatar(f'testuser{i}', self.temp_dir)
            sizes.append(os.path.getsize(path))

        avg_size = sum(sizes) / len(sizes)
        self.assertLess(avg_size, 600, f"Average file size {avg_size:.0f} bytes is too large")
        self.assertGreater(avg_size, 400, f"Average file size {avg_size:.0f} bytes seems suspiciously small")


class TestAvatarImageProperties(unittest.TestCase):
    """Test image properties (size, format, etc)"""

    def test_output_size_is_128x128(self):
        """Default output should be 128x128 pixels"""
        avatar = generate_pixel_avatar('testuser')
        self.assertEqual(avatar.size, (128, 128))

    def test_custom_size(self):
        """Should support custom sizes"""
        avatar = generate_pixel_avatar('testuser', size=16, output_size=64)
        self.assertEqual(avatar.size, (64, 64))

    def test_image_mode_is_rgb(self):
        """Image should be RGB mode"""
        avatar = generate_pixel_avatar('testuser')
        self.assertEqual(avatar.mode, 'RGB')

    def test_symmetry(self):
        """Avatar should be left-right symmetric (Alice's design choice)"""
        avatar = generate_pixel_avatar('testuser')
        pixels = avatar.load()

        width, height = avatar.size

        # Check a sample of rows for symmetry
        for y in range(0, height, 10):
            for x in range(width // 2):
                left_pixel = pixels[x, y]
                right_pixel = pixels[width - 1 - x, y]

                self.assertEqual(
                    left_pixel,
                    right_pixel,
                    f"Asymmetry detected at row {y}: {left_pixel} != {right_pixel}"
                )


class TestAvatarPerformance(unittest.TestCase):
    """Performance benchmarks"""

    def test_generation_speed(self):
        """Single avatar should generate in under 100ms"""
        start = time.time()
        generate_pixel_avatar('testuser')
        elapsed = time.time() - start

        self.assertLess(
            elapsed,
            0.1,
            f"Avatar generation took {elapsed*1000:.1f}ms (should be < 100ms)"
        )

    def test_batch_generation_100_users(self):
        """Should generate 100 avatars in under 5 seconds"""
        start = time.time()

        for i in range(100):
            generate_pixel_avatar(f'user{i}')

        elapsed = time.time() - start
        avg_time = elapsed / 100 * 1000  # ms per avatar

        self.assertLess(
            elapsed,
            5.0,
            f"100 avatars took {elapsed:.2f}s (should be < 5s)"
        )

        print(f"\n  ⚡ Performance: {avg_time:.1f}ms per avatar")


class TestAvatarIntegration(unittest.TestCase):
    """Integration tests with the full system"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_avatar_path_creates_if_missing(self):
        """get_avatar_path should auto-generate if avatar doesn't exist"""
        path = get_avatar_path('newuser', self.temp_dir)

        # Should return a path
        self.assertIsInstance(path, str)

        # File should now exist
        full_path = path.lstrip('/')
        self.assertTrue(os.path.exists(full_path))

    def test_get_avatar_path_returns_existing(self):
        """get_avatar_path should return existing avatar without regenerating"""
        # Generate once
        path1 = get_avatar_path('testuser', self.temp_dir)
        mtime1 = os.path.getmtime(path1.lstrip('/'))

        time.sleep(0.01)  # Small delay

        # Get again
        path2 = get_avatar_path('testuser', self.temp_dir)
        mtime2 = os.path.getmtime(path2.lstrip('/'))

        # Should be same file (not regenerated)
        self.assertEqual(path1, path2)
        self.assertEqual(mtime1, mtime2, "File was regenerated unnecessarily")


def run_tests_and_generate_report():
    """Run all tests and generate markdown report for CalRiven bot to post"""

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate report
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    report = f"""## 🤖 Automated Test Results

**Test Suite:** `test_avatar_generator.py`
**Total Tests:** {total_tests}
**Passed:** {passed} ✅
**Failed:** {failures} ❌
**Errors:** {errors} 🚨
**Success Rate:** {success_rate:.1f}%

"""

    if result.wasSuccessful():
        report += "### ✅ ALL TESTS PASSED\n\n"
        report += "Alice's avatar generator meets all requirements:\n"
        report += "- ✅ Deterministic (same username → same avatar)\n"
        report += "- ✅ Handles edge cases (special chars, unicode)\n"
        report += "- ✅ File size < 1KB\n"
        report += "- ✅ Symmetric design\n"
        report += "- ✅ Performance < 100ms per avatar\n"
        report += "- ✅ Integration with existing system\n\n"
        report += "**Recommendation:** APPROVE for merge + award 100 Perfect Bits\n"
    else:
        report += "### ❌ TESTS FAILED\n\n"
        report += "Issues found:\n"
        for failure in result.failures:
            test_name = failure[0]
            report += f"- ❌ {test_name}\n"
        for error in result.errors:
            test_name = error[0]
            report += f"- 🚨 {test_name}\n"
        report += "\n**Recommendation:** Request fixes before awarding bits\n"

    return report, result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("🧪 Running Avatar Generator Test Suite")
    print("=" * 70)
    print()

    report, success = run_tests_and_generate_report()

    print()
    print("=" * 70)
    print("📊 TEST REPORT (for CalRiven bot to post)")
    print("=" * 70)
    print()
    print(report)

    # Save report to file
    with open('test_report_avatar.md', 'w') as f:
        f.write(report)

    print("✅ Report saved to: test_report_avatar.md")

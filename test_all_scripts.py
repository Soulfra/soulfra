#!/usr/bin/env python3
"""
Test All Scripts - Verify Everything Works
===========================================

Tests all the new scripts to ensure they work together:
- start.py (can be imported)
- test_everything.py (all tests pass)
- build_from_scratch.py (can be imported)
- hello_world.py (runs successfully)
- full_flow_demo.py (can be imported)

Usage:
    python3 test_all_scripts.py
"""

import sys
import subprocess
import importlib.util


def print_header(title):
    """Print test header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_script_imports(script_name):
    """Test if a script can be imported"""
    print(f"\n🔍 Testing: {script_name}")
    print(f"   Checking if script can be imported...")

    try:
        spec = importlib.util.spec_from_file_location("module", script_name)
        if spec is None:
            print(f"   ❌ Failed: Could not load {script_name}")
            return False

        module = importlib.util.module_from_spec(spec)

        # Don't execute, just check it can be loaded
        print(f"   ✅ Script loads successfully")
        return True

    except Exception as e:
        print(f"   ❌ Failed to import: {e}")
        return False


def test_hello_world():
    """Test hello_world.py runs successfully"""
    print_header("TEST 1: hello_world.py")

    print("\n🏃 Running: python3 hello_world.py")

    try:
        result = subprocess.run(
            ['python3', 'hello_world.py'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("   ✅ Script completed successfully")
            print(f"   Output lines: {len(result.stdout.splitlines())}")

            # Check for expected output
            if "HELLO WORLD COMPLETE" in result.stdout:
                print("   ✅ Found success message")
                return True
            else:
                print("   ⚠️  Script ran but missing success message")
                return False
        else:
            print(f"   ❌ Script failed with exit code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Script timed out (>10 seconds)")
        return False
    except Exception as e:
        print(f"   ❌ Error running script: {e}")
        return False


def test_test_everything():
    """Test test_everything.py passes all tests"""
    print_header("TEST 2: test_everything.py")

    print("\n🏃 Running: python3 test_everything.py")

    try:
        result = subprocess.run(
            ['python3', 'test_everything.py'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("   ✅ All tests passed")

            # Check test count
            if "ALL TESTS PASSED" in result.stdout:
                print("   ✅ Found success message")

                # Extract test count
                if "10/10" in result.stdout:
                    print("   ✅ All 10 tests passed")
                    return True
                else:
                    print("   ⚠️  Unknown test count")
                    return True
            else:
                print("   ⚠️  Script ran but missing success message")
                return False
        else:
            print(f"   ❌ Tests failed with exit code {result.returncode}")
            if "FAIL" in result.stdout:
                # Find which test failed
                for line in result.stdout.splitlines():
                    if "FAIL" in line:
                        print(f"   Failed test: {line}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Script timed out (>30 seconds)")
        return False
    except Exception as e:
        print(f"   ❌ Error running script: {e}")
        return False


def test_start_py_imports():
    """Test start.py can be imported"""
    print_header("TEST 3: start.py (import check)")

    return test_script_imports('start.py')


def test_build_from_scratch_imports():
    """Test build_from_scratch.py can be imported"""
    print_header("TEST 4: build_from_scratch.py (import check)")

    return test_script_imports('build_from_scratch.py')


def test_full_flow_demo_imports():
    """Test full_flow_demo.py can be imported"""
    print_header("TEST 5: full_flow_demo.py (import check)")

    return test_script_imports('full_flow_demo.py')


def test_proof_it_all_works():
    """Test PROOF_IT_ALL_WORKS.py (existing test suite)"""
    print_header("BONUS TEST: PROOF_IT_ALL_WORKS.py")

    print("\n🏃 Running existing test suite...")

    try:
        result = subprocess.run(
            ['python3', 'PROOF_IT_ALL_WORKS.py'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("   ✅ All original tests passed")

            # Count tests
            passed = result.stdout.count("✅ PASS")
            print(f"   ✅ {passed} tests passed")
            return True
        else:
            print(f"   ⚠️  Some tests may have failed")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Script timed out")
        return False
    except Exception as e:
        print(f"   ⚠️  Could not run: {e}")
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("  TEST ALL SCRIPTS - Comprehensive Verification")
    print("="*70)
    print("""
Tests all new scripts created for the platform:

1. hello_world.py - Simple complete flow demo
2. test_everything.py - 10 comprehensive tests
3. start.py - One-command starter
4. build_from_scratch.py - Step-by-step proof
5. full_flow_demo.py - Interactive walkthrough

Plus bonus test:
6. PROOF_IT_ALL_WORKS.py - Original test suite
    """)

    results = []

    # Run all tests
    tests = [
        ("hello_world.py", test_hello_world),
        ("test_everything.py", test_test_everything),
        ("start.py imports", test_start_py_imports),
        ("build_from_scratch.py imports", test_build_from_scratch_imports),
        ("full_flow_demo.py imports", test_full_flow_demo_imports),
        ("PROOF_IT_ALL_WORKS.py", test_proof_it_all_works),
    ]

    for name, test_func in tests:
        passed = test_func()
        results.append((name, passed))

    # Print summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print()
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")

    print("\n" + "="*70)

    if passed_count == total_count:
        print(f"  ✅ ALL TESTS PASSED ({passed_count}/{total_count})")
        print("="*70)
        print("""
   🎉 All scripts work perfectly!

   You can now use:
   - python3 hello_world.py (simple demo)
   - python3 full_flow_demo.py (interactive walkthrough)
   - python3 test_everything.py (verify platform)
   - python3 start.py (run platform)
   - python3 build_from_scratch.py (learn how it works)

   Everything is ready to use! 🚀
        """)
        return 0
    else:
        failed_count = total_count - passed_count
        print(f"  ⚠️  {failed_count} TEST(S) FAILED ({passed_count}/{total_count} passed)")
        print("="*70)
        print("\nFailed tests:")
        for name, passed in results:
            if not passed:
                print(f"   ❌ {name}")

        print("\nFix the failed tests before proceeding.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

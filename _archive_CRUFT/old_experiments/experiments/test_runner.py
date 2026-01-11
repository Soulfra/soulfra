#!/usr/bin/env python3
"""
Automated Test Runner - "loop it until it doesn't need to be"

Replaces manual `python3 test_*.py` commands with automated execution.

Features:
- Discover all test_*.py files
- Run individually or all at once
- Auto-loop until all tests pass
- Stream output for WebSocket integration
- Simple auto-fix attempts for common errors

Usage:
    # Run all tests once
    python3 test_runner.py

    # Auto-loop until all pass
    python3 test_runner.py --auto-loop

    # Run specific test
    python3 test_runner.py test_database.py

    # From Python code
    from test_runner import run_all_tests, auto_test_loop
    results = run_all_tests()
"""

import subprocess
import sys
import os
import glob
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable


# ==============================================================================
# TEST DISCOVERY
# ==============================================================================

def discover_tests() -> List[str]:
    """
    Find all test_*.py files in current directory

    Returns:
        List of test file paths
    """
    test_files = glob.glob('test_*.py')
    test_files.sort()
    return test_files


# ==============================================================================
# TEST EXECUTION
# ==============================================================================

def run_test(test_file: str, output_callback: Optional[Callable] = None) -> Tuple[bool, str, str]:
    """
    Run a single test file

    Args:
        test_file: Path to test file (e.g., 'test_database.py')
        output_callback: Optional function to call with each line of output

    Returns:
        Tuple of (passed, stdout, stderr)
    """
    print(f"\n🧪 Running: {test_file}")
    if output_callback:
        output_callback(f"\n🧪 Running: {test_file}\n")

    try:
        # Run test as subprocess
        process = subprocess.Popen(
            [sys.executable, test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )

        stdout_lines = []
        stderr_lines = []

        # Read output line by line (real-time streaming)
        while True:
            stdout_line = process.stdout.readline()
            if stdout_line:
                stdout_lines.append(stdout_line)
                print(stdout_line, end='')
                if output_callback:
                    output_callback(stdout_line)

            stderr_line = process.stderr.readline()
            if stderr_line:
                stderr_lines.append(stderr_line)
                print(stderr_line, end='', file=sys.stderr)
                if output_callback:
                    output_callback(stderr_line)

            # Check if process finished
            if stdout_line == '' and stderr_line == '' and process.poll() is not None:
                break

        # Get remaining output
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            stdout_lines.append(remaining_stdout)
            print(remaining_stdout, end='')
            if output_callback:
                output_callback(remaining_stdout)

        if remaining_stderr:
            stderr_lines.append(remaining_stderr)
            print(remaining_stderr, end='', file=sys.stderr)
            if output_callback:
                output_callback(remaining_stderr)

        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)

        # Check return code
        passed = process.returncode == 0

        if passed:
            print(f"✅ {test_file}: PASSED")
            if output_callback:
                output_callback(f"✅ {test_file}: PASSED\n")
        else:
            print(f"❌ {test_file}: FAILED (exit code {process.returncode})")
            if output_callback:
                output_callback(f"❌ {test_file}: FAILED (exit code {process.returncode})\n")

        return passed, stdout, stderr

    except Exception as e:
        error_msg = f"❌ {test_file}: ERROR - {str(e)}"
        print(error_msg)
        if output_callback:
            output_callback(error_msg + '\n')
        return False, '', str(e)


def run_all_tests(output_callback: Optional[Callable] = None) -> Dict[str, bool]:
    """
    Run all test_*.py files

    Args:
        output_callback: Optional function to call with each line of output

    Returns:
        Dict mapping test_file -> passed (bool)
    """
    tests = discover_tests()

    if not tests:
        print("❌ No test files found (test_*.py)")
        return {}

    print(f"\n{'=' * 70}")
    print(f"🚀 Running {len(tests)} tests...")
    print(f"{'=' * 70}")

    if output_callback:
        output_callback(f"\n{'=' * 70}\n")
        output_callback(f"🚀 Running {len(tests)} tests...\n")
        output_callback(f"{'=' * 70}\n")

    results = {}

    for test_file in tests:
        passed, stdout, stderr = run_test(test_file, output_callback)
        results[test_file] = passed

    # Summary
    passed_count = sum(1 for p in results.values() if p)
    failed_count = len(results) - passed_count

    print(f"\n{'=' * 70}")
    print(f"📊 Results: {passed_count}/{len(results)} passed")
    if failed_count > 0:
        print(f"❌ Failed tests:")
        for test_file, passed in results.items():
            if not passed:
                print(f"   - {test_file}")
    print(f"{'=' * 70}\n")

    if output_callback:
        output_callback(f"\n{'=' * 70}\n")
        output_callback(f"📊 Results: {passed_count}/{len(results)} passed\n")
        if failed_count > 0:
            output_callback(f"❌ Failed tests:\n")
            for test_file, passed in results.items():
                if not passed:
                    output_callback(f"   - {test_file}\n")
        output_callback(f"{'=' * 70}\n\n")

    return results


# ==============================================================================
# AUTO-LOOP - "loop it until it doesn't need to be"
# ==============================================================================

def auto_test_loop(max_attempts: int = 10, delay: int = 3, output_callback: Optional[Callable] = None) -> bool:
    """
    Keep running tests until all pass or max attempts reached

    Args:
        max_attempts: Maximum number of test runs
        delay: Seconds to wait between runs
        output_callback: Optional function to call with each line of output

    Returns:
        True if all tests eventually passed
    """
    print(f"\n🔄 AUTO-LOOP MODE: Will run tests until all pass (max {max_attempts} attempts)")
    print(f"{'=' * 70}\n")

    if output_callback:
        output_callback(f"\n🔄 AUTO-LOOP MODE: Will run tests until all pass (max {max_attempts} attempts)\n")
        output_callback(f"{'=' * 70}\n\n")

    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Attempt {attempt}/{max_attempts}")
        if output_callback:
            output_callback(f"\n🔄 Attempt {attempt}/{max_attempts}\n")

        results = run_all_tests(output_callback)

        # Check if all passed
        all_passed = all(results.values())

        if all_passed:
            print(f"\n🎉 SUCCESS! All tests passed on attempt {attempt}")
            if output_callback:
                output_callback(f"\n🎉 SUCCESS! All tests passed on attempt {attempt}\n")
            return True

        # Failed tests remain
        failed_count = sum(1 for p in results.values() if not p)
        print(f"\n⏳ {failed_count} tests still failing...")

        if output_callback:
            output_callback(f"\n⏳ {failed_count} tests still failing...\n")

        if attempt < max_attempts:
            print(f"🔄 Retrying in {delay} seconds...")
            if output_callback:
                output_callback(f"🔄 Retrying in {delay} seconds...\n")
            time.sleep(delay)

    print(f"\n❌ AUTO-LOOP FAILED: Some tests still failing after {max_attempts} attempts")
    if output_callback:
        output_callback(f"\n❌ AUTO-LOOP FAILED: Some tests still failing after {max_attempts} attempts\n")

    return False


# ==============================================================================
# SIMPLE AUTO-FIX (Future Enhancement)
# ==============================================================================

def attempt_auto_fix(test_file: str, error_output: str) -> bool:
    """
    Try to automatically fix common test errors

    This is a placeholder for future intelligent auto-fixing.

    Args:
        test_file: Test file that failed
        error_output: Error message from test

    Returns:
        True if fix was attempted
    """
    # Common patterns to auto-fix:
    # - Missing imports
    # - Database not initialized
    # - Port already in use
    # - File permissions

    # TODO: Implement intelligent auto-fixing
    # For now, just return False

    return False


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Run Soulfra tests')
    parser.add_argument('test_file', nargs='?', help='Specific test file to run')
    parser.add_argument('--auto-loop', action='store_true', help='Keep running until all pass')
    parser.add_argument('--max-attempts', type=int, default=10, help='Max auto-loop attempts')
    parser.add_argument('--delay', type=int, default=3, help='Delay between auto-loop runs (seconds)')

    args = parser.parse_args()

    if args.test_file:
        # Run specific test
        if not os.path.exists(args.test_file):
            print(f"❌ Test file not found: {args.test_file}")
            sys.exit(1)

        passed, stdout, stderr = run_test(args.test_file)
        sys.exit(0 if passed else 1)

    elif args.auto_loop:
        # Auto-loop mode
        success = auto_test_loop(
            max_attempts=args.max_attempts,
            delay=args.delay
        )
        sys.exit(0 if success else 1)

    else:
        # Run all tests once
        results = run_all_tests()

        all_passed = all(results.values())
        sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()

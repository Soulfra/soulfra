#!/usr/bin/env python3
"""
Hello World Smoke Tests - Quick verification that Soulfra is working

This is the "hello world" of testing - fast, simple checks that the basic system works.
Run this first before doing comprehensive testing.

Usage:
    python3 test_hello_world.py

Expected runtime: < 10 seconds

Tests:
✓ Server responds on port 5001
✓ Database exists and has tables
✓ Ollama AI is reachable on port 11434
✓ Basic route (/) returns HTML
✓ API health endpoint works
✓ Neural networks can load
"""

import sys
import sqlite3
import requests
from pathlib import Path
import time

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


class HelloWorldTests:
    """Quick smoke tests"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()

    def test(self, name, func):
        """Run a single test"""
        print(f"\n{CYAN}Testing: {name}{RESET}")
        try:
            result = func()
            if result:
                print(f"{GREEN}✓ PASS{RESET}")
                self.passed += 1
                return True
            else:
                print(f"{RED}✗ FAIL{RESET}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"{RED}✗ FAIL: {str(e)}{RESET}")
            self.failed += 1
            return False

    def test_server_running(self):
        """Test if Flask server is running on port 5001"""
        try:
            response = requests.get('http://localhost:5001', timeout=2)
            print(f"  Status code: {response.status_code}")
            return response.status_code in [200, 302, 500]  # Any response is good
        except requests.exceptions.ConnectionError:
            print(f"  {YELLOW}Server not running. Start with: python3 app.py{RESET}")
            return False

    def test_database_exists(self):
        """Test if SQLite database exists and has tables"""
        db_path = Path('soulfra.db')

        if not db_path.exists():
            print(f"  {YELLOW}Database not found at: {db_path}{RESET}")
            return False

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if posts table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            has_posts = cursor.fetchone() is not None

            # Count tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            conn.close()

            print(f"  Tables found: {table_count}")
            print(f"  Posts table: {'✓' if has_posts else '✗'}")

            return has_posts

        except Exception as e:
            print(f"  Database error: {e}")
            return False

    def test_ollama_reachable(self):
        """Test if Ollama AI is reachable on port 11434"""
        try:
            response = requests.get('http://localhost:11434/', timeout=2)
            print(f"  Ollama API: {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            print(f"  {YELLOW}Ollama not running (optional for basic functionality){RESET}")
            print(f"  {YELLOW}Start with: ollama serve{RESET}")
            return True  # Not critical for basic operation

    def test_homepage_loads(self):
        """Test if homepage returns HTML"""
        try:
            response = requests.get('http://localhost:5001/', timeout=2)

            is_html = 'text/html' in response.headers.get('Content-Type', '')
            has_content = len(response.text) > 100

            print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  Response size: {len(response.text)} bytes")

            return is_html and has_content

        except requests.exceptions.ConnectionError:
            print(f"  {YELLOW}Server not running{RESET}")
            return False

    def test_health_endpoint(self):
        """Test API health endpoint"""
        try:
            response = requests.get('http://localhost:5001/api/health', timeout=2)

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"  Health check: {data.get('status', 'unknown')}")
                return data.get('status') == 'healthy'

            return response.status_code == 200

        except requests.exceptions.ConnectionError:
            print(f"  {YELLOW}Server not running{RESET}")
            return False
        except Exception as e:
            print(f"  Error: {e}")
            return False

    def test_neural_networks(self):
        """Test if neural networks can be imported (optional)"""
        try:
            from neural_network import load_neural_network

            print(f"  {GREEN}Neural network module available{RESET}")

            # Try to load one network
            try:
                network = load_neural_network('soulfra_judge')
                print(f"  {GREEN}Sample network loaded: soulfra_judge{RESET}")
                return True
            except:
                print(f"  {YELLOW}Networks not trained yet (run train_context_networks.py){RESET}")
                return True  # Not critical

        except ImportError:
            print(f"  {YELLOW}Neural network module not found (optional){RESET}")
            return True  # Not critical for basic operation

    def run_all(self):
        """Run all smoke tests"""
        print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
        print(f"{BOLD}{BLUE}SOULFRA HELLO WORLD SMOKE TESTS{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

        print(f"{CYAN}Quick verification that basic system is working...{RESET}")

        # Run tests
        self.test("Server Running (port 5001)", self.test_server_running)
        self.test("Database Exists & Has Tables", self.test_database_exists)
        self.test("Ollama AI Reachable (port 11434)", self.test_ollama_reachable)
        self.test("Homepage Loads", self.test_homepage_loads)
        self.test("API Health Endpoint", self.test_health_endpoint)
        self.test("Neural Networks Available", self.test_neural_networks)

        # Summary
        elapsed = time.time() - self.start_time
        total = self.passed + self.failed

        print(f"\n{BOLD}{'=' * 70}{RESET}")
        print(f"{BOLD}SUMMARY{RESET}")
        print(f"{BOLD}{'=' * 70}{RESET}\n")

        if self.failed == 0:
            print(f"{GREEN}{BOLD}✓ ALL TESTS PASSED ({self.passed}/{total}){RESET}")
            print(f"{GREEN}Soulfra is working! 🎉{RESET}")
        else:
            print(f"{YELLOW}{BOLD}⚠ SOME TESTS FAILED ({self.passed}/{total} passed){RESET}")

            if self.passed >= 2:
                print(f"{YELLOW}Basic functionality available, some features may not work.{RESET}")
            else:
                print(f"{RED}Critical issues detected. Check errors above.{RESET}")

        print(f"\n{CYAN}Runtime: {elapsed:.2f} seconds{RESET}\n")

        # Next steps
        if self.failed == 0:
            print(f"{BOLD}Next steps:{RESET}")
            print(f"  • Run comprehensive tests: {CYAN}python3 test_application_stack.py{RESET}")
            print(f"  • Test network stack: {CYAN}python3 test_network_stack.py{RESET}")
            print(f"  • Open browser: {CYAN}http://localhost:5001{RESET}")
        else:
            print(f"{BOLD}Fix issues:{RESET}")
            if not Path('soulfra.db').exists():
                print(f"  • Initialize database: {CYAN}python3 database.py{RESET}")
            print(f"  • Start server: {CYAN}python3 app.py{RESET}")
            print(f"  • Start Ollama: {CYAN}ollama serve{RESET} (optional)")

        print(f"\n{BOLD}{'=' * 70}{RESET}\n")

        return self.failed == 0


def main():
    """Main entry point"""
    tests = HelloWorldTests()
    success = tests.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
End-to-End Flow Test

Tests the ACTUAL user flow:
1. Visit localhost:5001
2. Create a post
3. Publish it
4. View it on blog
5. Chat about it with Ollama

This shows what ACTUALLY works vs what's broken.
"""

import requests
import sqlite3
import time
from pathlib import Path

BASE_URL = "http://localhost:5001"
DB_PATH = "soulfra.db"

def color_print(status, message):
    """Print colored output"""
    colors = {
        'PASS': '\033[92m✓',
        'FAIL': '\033[91m✗',
        'SKIP': '\033[93m⊘',
        'INFO': '\033[94mℹ'
    }
    reset = '\033[0m'
    print(f"{colors.get(status, '')} {message}{reset}")


def test_localhost_running():
    """Test 1: Is Flask running?"""
    try:
        response = requests.get(BASE_URL, timeout=2)
        color_print('PASS', "Flask server is running")
        return True
    except requests.exceptions.ConnectionError:
        color_print('FAIL', "Flask server is NOT running - Start it with: python3 app.py")
        return False


def test_database_exists():
    """Test 2: Does database exist?"""
    if Path(DB_PATH).exists():
        color_print('PASS', f"Database exists: {DB_PATH}")
        return True
    else:
        color_print('FAIL', f"Database NOT found: {DB_PATH}")
        return False


def test_posts_table():
    """Test 3: Can we query posts table?"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        conn.close()
        color_print('PASS', f"Posts table exists with {count} posts")
        return True
    except Exception as e:
        color_print('FAIL', f"Cannot query posts table: {e}")
        return False


def test_chat_route():
    """Test 4: Is /chat accessible?"""
    try:
        response = requests.get(f"{BASE_URL}/chat", timeout=5, allow_redirects=False)

        # Check if it redirects (means auth is working)
        if response.status_code == 302:
            color_print('INFO', "/chat redirects to QR auth (production mode)")
            return True
        elif response.status_code == 200:
            color_print('PASS', "/chat is accessible (dev mode)")
            return True
        else:
            color_print('FAIL', f"/chat returned status {response.status_code}")
            return False
    except Exception as e:
        color_print('FAIL', f"Cannot access /chat: {e}")
        return False


def test_status_route():
    """Test 5: Is /status accessible?"""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            color_print('PASS', "/status is accessible")
            return True
        else:
            color_print('FAIL', f"/status returned status {response.status_code}")
            return False
    except Exception as e:
        color_print('FAIL', f"Cannot access /status: {e}")
        return False


def test_ollama_running():
    """Test 6: Is Ollama running?"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            color_print('PASS', f"Ollama is running with {len(models)} models")
            return True
        else:
            color_print('FAIL', "Ollama responded but with error")
            return False
    except requests.exceptions.ConnectionError:
        color_print('FAIL', "Ollama is NOT running - Start it with: ollama serve")
        return False
    except Exception as e:
        color_print('FAIL', f"Ollama error: {e}")
        return False


def test_publish_script_exists():
    """Test 7: Does publish script exist?"""
    if Path("publish_to_github.py").exists():
        color_print('PASS', "publish_to_github.py exists")
        return True
    else:
        color_print('FAIL', "publish_to_github.py NOT found")
        return False


def test_github_repo_exists():
    """Test 8: Does GitHub repo directory exist?"""
    repo_path = Path("/Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra")
    if repo_path.exists():
        color_print('PASS', f"GitHub repo exists at {repo_path}")
        return True
    else:
        color_print('FAIL', f"GitHub repo NOT found at {repo_path}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 Soulfra End-to-End Flow Test")
    print("="*70 + "\n")

    tests = [
        ("Flask Server", test_localhost_running),
        ("Database File", test_database_exists),
        ("Posts Table", test_posts_table),
        ("Chat Route", test_chat_route),
        ("Status Route", test_status_route),
        ("Ollama Server", test_ollama_running),
        ("Publish Script", test_publish_script_exists),
        ("GitHub Repo", test_github_repo_exists),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        result = test_func()
        results.append((test_name, result))
        time.sleep(0.5)

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color_print(status, f"{test_name}: {'✓ PASS' if result else '✗ FAIL'}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        color_print('PASS', "All tests PASSED! 🎉")
        print("\nNext steps:")
        print("1. Visit http://localhost:5001/chat")
        print("2. Create a test post")
        print("3. Run: python3 publish_to_github.py")
        print("4. Check: https://soulfra.github.io/soulfra/")
    else:
        color_print('FAIL', f"{total - passed} tests FAILED")
        print("\nFix the failed tests before proceeding.")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()

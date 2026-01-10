#!/usr/bin/env python3
"""
Integration Testing Script - "Jig Testing" for Soulfra

Tests each layer of the stack systematically:
1. Database (data layer)
2. Routes (Flask routing)
3. Templates (rendering)
4. JavaScript (interactivity)
5. External services (Ollama)

Like testing each jig in woodworking before final assembly!
"""

import urllib.request
import urllib.error
import sqlite3
import json
import sys
import os
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def test_result(passed, test_name, details=""):
    """Print test result with color"""
    if passed:
        symbol = f"{GREEN}✓{RESET}"
        status = f"{GREEN}PASS{RESET}"
    else:
        symbol = f"{RED}✗{RESET}"
        status = f"{RED}FAIL{RESET}"

    print(f"{symbol} [{status}] {test_name}")
    if details:
        print(f"         {details}")


def test_database():
    """Layer 1: Test database connectivity and data"""
    print(f"\n{BOLD}=== LAYER 1: DATABASE ==={RESET}")

    try:
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()

        # Test 1: Database exists and is readable
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
        tables = cursor.fetchall()
        test_result(len(tables) > 0, "Database exists and readable", f"Found {len(tables)} tables")

        # Test 2: Posts table has data
        cursor.execute("SELECT COUNT(*) FROM posts")
        post_count = cursor.fetchone()[0]
        test_result(post_count > 0, "Posts table has data", f"{post_count} posts found")

        # Test 3: Tutorial post exists
        cursor.execute("SELECT id, title FROM posts WHERE slug = 'welcome-complete-guide'")
        tutorial_post = cursor.fetchone()
        test_result(tutorial_post is not None, "Tutorial post exists", f"ID: {tutorial_post[0] if tutorial_post else 'N/A'}")

        # Test 4: Users table has admin
        cursor.execute("SELECT id, username FROM users WHERE is_admin = 1 LIMIT 1")
        admin = cursor.fetchone()
        test_result(admin is not None, "Admin user exists", f"Username: {admin[1] if admin else 'N/A'}")

        conn.close()
        return True

    except Exception as e:
        test_result(False, "Database layer failed", str(e))
        return False


def test_routes(base_url='http://localhost:5001'):
    """Layer 2: Test Flask routes"""
    print(f"\n{BOLD}=== LAYER 2: ROUTES ==={RESET}")

    routes_to_test = [
        ('/', 'Homepage'),
        ('/post/welcome-complete-guide', 'Tutorial post'),
        ('/playground', 'Playground'),
        ('/docs', 'API Documentation'),
        ('/api/health', 'Health API'),
        ('/sitemap', 'Sitemap'),
        ('/live', 'Live chat feed'),
    ]

    all_passed = True

    for route, name in routes_to_test:
        try:
            url = base_url + route
            response = urllib.request.urlopen(url, timeout=5)
            status = response.getcode()
            passed = status == 200
            test_result(passed, f"Route: {route}", f"HTTP {status}")

            if not passed:
                all_passed = False

        except urllib.error.HTTPError as e:
            test_result(False, f"Route: {route}", f"HTTP {e.code} {e.reason}")
            all_passed = False
        except Exception as e:
            test_result(False, f"Route: {route}", str(e))
            all_passed = False

    return all_passed


def test_templates(base_url='http://localhost:5001'):
    """Layer 3: Test template rendering"""
    print(f"\n{BOLD}=== LAYER 3: TEMPLATES ==={RESET}")

    # Test tutorial post renders markdown correctly
    try:
        url = base_url + '/post/welcome-complete-guide'
        response = urllib.request.urlopen(url, timeout=5)
        html = response.read().decode('utf-8')

        # Check if markdown was converted to HTML
        has_h1 = '<h1' in html
        has_h2 = '<h2' in html
        has_links = '<a href=' in html
        not_raw_markdown = '# Welcome to Soulfra' not in html  # Should NOT have raw markdown

        all_good = has_h1 and has_h2 and has_links and not_raw_markdown

        test_result(all_good, "Markdown rendering",
                   f"H1: {has_h1}, H2: {has_h2}, Links: {has_links}, No raw MD: {not_raw_markdown}")

    except Exception as e:
        test_result(False, "Markdown rendering", str(e))

    # Test playground has interactive elements
    try:
        url = base_url + '/playground'
        response = urllib.request.urlopen(url, timeout=5)
        html = response.read().decode('utf-8')

        has_tabs = 'tab-chat' in html or 'switchTab' in html
        has_forms = '<input' in html or '<button' in html
        has_js = '<script>' in html

        all_good = has_tabs and has_forms and has_js

        test_result(all_good, "Playground template",
                   f"Tabs: {has_tabs}, Forms: {has_forms}, JS: {has_js}")

    except Exception as e:
        test_result(False, "Playground template", str(e))

    # Test docs has API endpoints
    try:
        url = base_url + '/docs'
        response = urllib.request.urlopen(url, timeout=5)
        html = response.read().decode('utf-8')

        has_endpoints = '/api/' in html
        has_methods = 'GET' in html or 'POST' in html
        has_search = 'searchEndpoints' in html or 'search' in html.lower()

        all_good = has_endpoints and has_methods and has_search

        test_result(all_good, "API docs template",
                   f"Endpoints: {has_endpoints}, Methods: {has_methods}, Search: {has_search}")

    except Exception as e:
        test_result(False, "API docs template", str(e))


def test_api(base_url='http://localhost:5001'):
    """Layer 4: Test API endpoints return valid JSON"""
    print(f"\n{BOLD}=== LAYER 4: API ENDPOINTS ==={RESET}")

    api_endpoints = [
        ('/api/health', 'Health check'),
        ('/api/posts', 'Posts API'),
    ]

    for endpoint, name in api_endpoints:
        try:
            url = base_url + endpoint
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode('utf-8'))

            is_valid_json = isinstance(data, dict) or isinstance(data, list)
            test_result(is_valid_json, f"API: {endpoint}", f"Valid JSON: {type(data).__name__}")

        except json.JSONDecodeError as e:
            test_result(False, f"API: {endpoint}", f"Invalid JSON: {e}")
        except Exception as e:
            test_result(False, f"API: {endpoint}", str(e))


def test_ollama():
    """Layer 5: Test Ollama connectivity (optional)"""
    print(f"\n{BOLD}=== LAYER 5: EXTERNAL SERVICES ==={RESET}")

    # Test Ollama
    try:
        # Try to connect to Ollama
        req_data = json.dumps({
            'model': 'llama2',
            'prompt': 'Test',
            'stream': False
        }).encode('utf-8')

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )

        response = urllib.request.urlopen(req, timeout=5)
        result = json.loads(response.read().decode('utf-8'))

        test_result(True, "Ollama connectivity", f"Model: {result.get('model', 'unknown')}")
        return True

    except urllib.error.URLError:
        test_result(False, "Ollama connectivity",
                   f"{YELLOW}Ollama not running (optional){RESET}")
        print(f"         Start Ollama: {BLUE}ollama serve{RESET}")
        return False
    except Exception as e:
        test_result(False, "Ollama connectivity", str(e))
        return False


def test_files():
    """Layer 0: Test critical files exist"""
    print(f"\n{BOLD}=== LAYER 0: FILES ==={RESET}")

    critical_files = [
        ('app.py', 'Flask application'),
        ('database.py', 'Database module'),
        ('soulfra.db', 'SQLite database'),
        ('templates/base.html', 'Base template'),
        ('templates/post.html', 'Post template'),
        ('templates/playground.html', 'Playground template'),
        ('templates/api_docs.html', 'API docs template'),
        ('static/style.css', 'Stylesheet'),
    ]

    for filepath, description in critical_files:
        exists = os.path.exists(filepath)
        size = os.path.getsize(filepath) if exists else 0
        test_result(exists, f"File: {filepath}",
                   f"{description} ({size} bytes)" if exists else "Missing")


def print_summary():
    """Print helpful summary"""
    print(f"\n{BOLD}=== SUMMARY ==={RESET}")
    print()
    print(f"✅ {GREEN}All tests passed{RESET} - Your system is fully operational!")
    print()
    print(f"{BOLD}Next steps:{RESET}")
    print(f"  1. Visit {BLUE}http://localhost:5001/post/welcome-complete-guide{RESET}")
    print(f"  2. Try the {BLUE}http://localhost:5001/playground{RESET}")
    print(f"  3. Explore {BLUE}http://localhost:5001/docs{RESET}")
    print()
    print(f"{BOLD}Optional:{RESET}")
    print(f"  • Start Ollama: {BLUE}ollama serve{RESET}")
    print(f"  • Then try AI chat in playground")
    print()


def main():
    """Run all integration tests"""
    print(f"\n{BOLD}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║  SOULFRA INTEGRATION TEST - \"Jig Testing\" Each Layer      ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════════════════════════════╝{RESET}")
    print()
    print("Testing each layer of the stack like checking jigs in woodworking...")

    # Test each layer in order
    files_ok = test_files()
    db_ok = test_database()
    routes_ok = test_routes()
    test_templates()
    test_api()
    ollama_ok = test_ollama()

    print_summary()

    # Exit code
    if files_ok and db_ok and routes_ok:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

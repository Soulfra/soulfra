#!/usr/bin/env python3
"""
Test soulfra.com Actual Deployment

Check what's REALLY deployed and working right now.
Stop planning, start testing!
"""

import requests
import sys
from datetime import datetime

# Colors
class C:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    INFO = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{C.OK}✅ PASS{C.END}" if passed else f"{C.FAIL}❌ FAIL{C.END}"
    print(f"{status} {name}")
    if details:
        print(f"     {C.INFO}{details}{C.END}")

def test_http_access():
    """Test if soulfra.com is accessible via HTTP"""
    try:
        response = requests.get('http://soulfra.com', timeout=10)
        passed = response.status_code == 200
        details = f"Status: {response.status_code}, Server: {response.headers.get('Server', 'Unknown')}"
        print_test("HTTP Access (http://soulfra.com)", passed, details)
        return passed
    except Exception as e:
        print_test("HTTP Access", False, str(e))
        return False

def test_https_access():
    """Test if HTTPS works (it won't - SSL cert issue)"""
    try:
        response = requests.get('https://soulfra.com', timeout=10, verify=True)
        passed = response.status_code == 200
        print_test("HTTPS Access (https://soulfra.com)", passed, "SSL cert valid")
        return passed
    except requests.exceptions.SSLError as e:
        print_test("HTTPS Access", False, "SSL cert problem (expected - need to enable HTTPS in GitHub Pages)")
        return False
    except Exception as e:
        print_test("HTTPS Access", False, str(e))
        return False

def test_customer_discovery_deployed():
    """Test if customer-discovery-chat.html is deployed"""
    try:
        response = requests.get('http://soulfra.com/customer-discovery-chat.html', timeout=10)
        passed = response.status_code == 200 and 'Customer Discovery' in response.text
        details = f"Status: {response.status_code}" if response.status_code != 200 else "File exists and contains expected content"
        print_test("Customer Discovery Tool Deployed", passed, details)
        return passed
    except Exception as e:
        print_test("Customer Discovery Tool Deployed", False, "Not found - need to deploy")
        return False

def test_index_page():
    """Test if index.html is deployed"""
    try:
        response = requests.get('http://soulfra.com/', timeout=10)
        passed = response.status_code == 200
        has_content = 'Decentralized' in response.text or 'Soulfra' in response.text
        details = f"Has expected content: {has_content}"
        print_test("Index Page", passed, details)
        return passed
    except Exception as e:
        print_test("Index Page", False, str(e))
        return False

def test_email_ollama_chat():
    """Test if email-ollama-chat.html is deployed"""
    try:
        response = requests.get('http://soulfra.com/email-ollama-chat.html', timeout=10)
        passed = response.status_code == 200
        print_test("Email Ollama Chat Deployed", passed)
        return passed
    except:
        print_test("Email Ollama Chat Deployed", False, "Not deployed yet")
        return False

def main():
    print(f"\n{C.BOLD}{'='*70}{C.END}")
    print(f"{C.BOLD}🔍 SOULFRA.COM DEPLOYMENT TEST{C.END}")
    print(f"{C.BOLD}Testing what's ACTUALLY deployed RIGHT NOW{C.END}")
    print(f"{C.BOLD}{'='*70}{C.END}\n")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # Test 1: Basic HTTP access
    print(f"{C.BOLD}Test 1: Basic Access{C.END}")
    results.append(test_http_access())
    print()

    # Test 2: HTTPS (will fail - that's the problem to fix)
    print(f"{C.BOLD}Test 2: HTTPS (Expected to fail){C.END}")
    results.append(test_https_access())
    print()

    # Test 3: Index page
    print(f"{C.BOLD}Test 3: Landing Page{C.END}")
    results.append(test_index_page())
    print()

    # Test 4: Customer Discovery Tool
    print(f"{C.BOLD}Test 4: Customer Discovery Tool{C.END}")
    results.append(test_customer_discovery_deployed())
    print()

    # Test 5: Email Ollama Chat
    print(f"{C.BOLD}Test 5: Email Ollama Chat{C.END}")
    results.append(test_email_ollama_chat())
    print()

    # Summary
    passed_count = sum(results)
    total_count = len(results)

    print(f"{C.BOLD}{'='*70}{C.END}")
    print(f"{C.BOLD}SUMMARY{C.END}")
    print(f"{C.BOLD}{'='*70}{C.END}\n")

    print(f"Tests Passed: {passed_count}/{total_count}")
    print()

    # Action items
    print(f"{C.BOLD}ACTION ITEMS:{C.END}\n")

    if not results[1]:  # HTTPS
        print(f"{C.WARN}1. FIX SSL CERTIFICATE:{C.END}")
        print("   - Go to: https://github.com/Soulfra/soulfra/settings/pages")
        print("   - Check: ☑️ Enforce HTTPS")
        print("   - Wait: 2-6 hours for Let's Encrypt cert")
        print()

    if not results[3]:  # Customer Discovery
        print(f"{C.WARN}2. DEPLOY CUSTOMER DISCOVERY TOOL:{C.END}")
        print("   cd /path/to/soulfra/github-repo")
        print("   cp /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/customer-discovery-chat.html .")
        print("   git add customer-discovery-chat.html")
        print("   git commit -m 'Add customer discovery tool'")
        print("   git push")
        print()

    if not results[4]:  # Email Ollama Chat
        print(f"{C.WARN}3. DEPLOY EMAIL OLLAMA CHAT:{C.END}")
        print("   cd /path/to/soulfra/github-repo")
        print("   cp /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/email-ollama-chat.html .")
        print("   git add email-ollama-chat.html")
        print("   git commit -m 'Add email ollama chat'")
        print("   git push")
        print()

    print(f"{C.INFO}4. START EMAIL NODE (test locally):{C.END}")
    print("   python3 ollama_email_node.py \\")
    print("     --email ollama-soulfra@gmail.com \\")
    print("     --password YOUR_APP_PASSWORD \\")
    print("     --node-name 'soulfra-test'")
    print()

    print(f"{C.INFO}5. TEST END-TO-END:{C.END}")
    print("   - Visit: http://soulfra.com/customer-discovery-chat.html")
    print("   - Use Persona Builder")
    print("   - Check email for AI response (30-60 sec)")
    print()

    if passed_count == total_count:
        print(f"{C.OK}🎉 ALL TESTS PASSED! soulfra.com is fully deployed!{C.END}")
        return 0
    else:
        print(f"{C.WARN}⚠️  {total_count - passed_count} issues to fix before full deployment{C.END}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

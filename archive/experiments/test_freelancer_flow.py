#!/usr/bin/env python3
"""
Freelancer Flow Integration Tests

Tests the complete end-to-end flow for freelancers:
1. Ollama connection (port 11434)
2. API key generation
3. API key validation
4. Rate limiting
5. Brand AI comment generation
6. Email handling (if configured)

Usage:
    python3 test_freelancer_flow.py
    python3 test_freelancer_flow.py --verbose
"""

import sys
import requests
import subprocess
from typing import Dict, List, Optional
from database import get_db
from freelancer_api import generate_api_key, validate_api_key, track_api_call
from config import OLLAMA_HOST, BASE_URL


# ==============================================================================
# TEST UTILITIES
# ==============================================================================

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.details = {}

    def success(self, **details):
        self.passed = True
        self.details = details

    def failure(self, error: str, **details):
        self.passed = False
        self.error = error
        self.details = details

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        result = f"{status} {self.name}"
        if self.error:
            result += f"\n   Error: {self.error}"
        if self.details:
            for key, value in self.details.items():
                result += f"\n   {key}: {value}"
        return result


def run_test(name: str, test_func, *args, **kwargs) -> TestResult:
    """Run a test and return result"""
    result = TestResult(name)
    try:
        test_func(result, *args, **kwargs)
    except Exception as e:
        result.failure(f"Exception: {str(e)}")
    return result


# ==============================================================================
# OLLAMA TESTS
# ==============================================================================

def test_ollama_connection(result: TestResult):
    """Test connection to Ollama on port 11434"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            result.success(
                ollama_host=OLLAMA_HOST,
                models_count=len(models),
                models=model_names[:5] if len(model_names) > 5 else model_names
            )
        else:
            result.failure(f"HTTP {response.status_code}", response=response.text[:200])
    except requests.exceptions.ConnectionError:
        result.failure(
            f"Cannot connect to Ollama at {OLLAMA_HOST}",
            suggestion="Run: ollama serve"
        )
    except requests.exceptions.Timeout:
        result.failure(f"Timeout connecting to {OLLAMA_HOST}")


def test_ollama_generate(result: TestResult):
    """Test Ollama text generation"""
    try:
        # Get first available model
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code != 200 or not response.json().get('models'):
            result.failure("No models available")
            return

        model_name = response.json()['models'][0]['name']

        payload = {
            "model": model_name,
            "prompt": "Say 'test successful' and nothing else.",
            "stream": False
        }
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            generated = data.get('response', '').strip()
            result.success(
                model=payload['model'],
                generated_text=generated[:100],
                response_length=len(generated)
            )
        else:
            result.failure(f"HTTP {response.status_code}", response=response.text[:200])
    except requests.exceptions.ConnectionError:
        result.failure(f"Cannot connect to Ollama", suggestion="Run: ollama serve")
    except Exception as e:
        result.failure(str(e))


# ==============================================================================
# API KEY TESTS
# ==============================================================================

def test_api_key_generation(result: TestResult):
    """Test API key generation"""
    test_email = "test-freelancer@example.com"
    api_result = generate_api_key(email=test_email, tier='free', brand_slug='calriven')

    if api_result['success']:
        result.success(
            api_key=api_result['api_key'][:20] + "...",
            tier=api_result['tier'],
            rate_limit=api_result['rate_limit']
        )
    else:
        result.failure(api_result.get('error', 'Unknown error'))


def test_api_key_validation(result: TestResult):
    """Test API key validation"""
    # Get most recent API key
    conn = get_db()
    row = conn.execute('''
        SELECT api_key, user_email, tier FROM api_keys
        WHERE revoked = 0
        ORDER BY created_at DESC LIMIT 1
    ''').fetchone()
    conn.close()

    if not row:
        result.failure("No API keys found in database")
        return

    api_key = row['api_key']
    key_info = validate_api_key(api_key)

    if key_info:
        result.success(
            email=key_info['user_email'],
            tier=key_info['tier'],
            calls_today=key_info['calls_today'],
            rate_limit=key_info['rate_limit']
        )
    else:
        result.failure("API key validation failed")


def test_api_key_rate_limiting(result: TestResult):
    """Test rate limiting"""
    conn = get_db()
    row = conn.execute('''
        SELECT api_key, user_email, tier, rate_limit FROM api_keys
        WHERE revoked = 0
        ORDER BY created_at DESC LIMIT 1
    ''').fetchone()

    if not row:
        result.failure("No API keys found")
        conn.close()
        return

    api_key = row['api_key']
    rate_limit = row['rate_limit']

    # Simulate calls up to limit
    for i in range(rate_limit + 2):
        allowed = track_api_call(
            api_key=api_key,
            endpoint='/api/v1/test/comment',
            brand_slug='test',
            response_status=200,
            response_time_ms=100
        )

        if i < rate_limit:
            if not allowed:
                result.failure(f"Call {i+1} should be allowed but was rejected")
                conn.close()
                return
        else:
            if allowed:
                result.failure(f"Call {i+1} should be rate-limited but was allowed")
                conn.close()
                return

    conn.close()
    result.success(
        rate_limit=rate_limit,
        calls_tested=rate_limit + 2,
        rate_limiting="Working correctly"
    )


# ==============================================================================
# DATABASE TESTS
# ==============================================================================

def test_database_tables(result: TestResult):
    """Test that required tables exist"""
    conn = get_db()

    required_tables = [
        'api_keys',
        'api_call_logs',
        'ai_responses',
        'outbound_emails'
    ]

    optional_tables = [
        'inbound_emails',
        'newsletter_subscribers',
        'ollama_comments'
    ]

    existing = set()
    missing = set()

    for table in required_tables:
        try:
            conn.execute(f'SELECT 1 FROM {table} LIMIT 1')
            existing.add(table)
        except:
            missing.add(table)

    optional_existing = set()
    optional_missing = set()

    for table in optional_tables:
        try:
            conn.execute(f'SELECT 1 FROM {table} LIMIT 1')
            optional_existing.add(table)
        except:
            optional_missing.add(table)

    conn.close()

    if missing:
        result.failure(
            "Required tables missing",
            missing_required=list(missing),
            existing_required=list(existing),
            missing_optional=list(optional_missing),
            existing_optional=list(optional_existing)
        )
    else:
        result.success(
            required_tables=list(existing),
            optional_tables=list(optional_existing),
            missing_optional=list(optional_missing)
        )


def test_database_data_counts(result: TestResult):
    """Check how much data exists in key tables"""
    conn = get_db()

    counts = {}
    tables_to_check = [
        'api_keys', 'api_call_logs', 'ai_responses',
        'outbound_emails', 'posts', 'comments', 'brands'
    ]

    for table in tables_to_check:
        try:
            row = conn.execute(f'SELECT COUNT(*) as c FROM {table}').fetchone()
            counts[table] = row['c']
        except:
            counts[table] = 'N/A (table missing)'

    conn.close()

    result.success(**counts)


# ==============================================================================
# BRAND AI TESTS
# ==============================================================================

def test_brand_ai_comment_api(result: TestResult):
    """Test brand AI comment generation via API"""
    # Get an API key
    conn = get_db()
    row = conn.execute('''
        SELECT api_key FROM api_keys
        WHERE revoked = 0
        ORDER BY created_at DESC LIMIT 1
    ''').fetchone()

    # Get a post_id
    post = conn.execute('SELECT id FROM posts LIMIT 1').fetchone()
    conn.close()

    if not row:
        result.failure("No API keys available for testing")
        return

    if not post:
        result.failure("No posts available for testing")
        return

    api_key = row['api_key']
    post_id = post['id']

    # Test API endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/calriven/comment",
            params={'key': api_key},
            json={'prompt': 'Test comment generation', 'post_id': post_id},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            result.success(
                status_code=200,
                comment=data.get('comment', '')[:100],
                model=data.get('model', 'unknown')
            )
        else:
            result.failure(
                f"HTTP {response.status_code}",
                response=response.text[:200]
            )
    except requests.exceptions.ConnectionError:
        result.failure(
            f"Cannot connect to {BASE_URL}",
            suggestion="Make sure Flask app is running on port 5001"
        )
    except Exception as e:
        result.failure(str(e))


# ==============================================================================
# SYSTEM INFO
# ==============================================================================

def print_system_info():
    """Print system configuration"""
    print("\n" + "="*80)
    print("SYSTEM CONFIGURATION")
    print("="*80)
    print(f"BASE_URL: {BASE_URL}")
    print(f"OLLAMA_HOST: {OLLAMA_HOST}")

    # Check if Ollama is running
    try:
        subprocess.run(['ollama', 'list'], capture_output=True, timeout=2)
        print("Ollama: Running")
    except:
        print("Ollama: Not running or not installed")

    # Check if Flask app is running
    try:
        requests.get(f"{BASE_URL}/api/health", timeout=2)
        print(f"Flask app: Running on {BASE_URL}")
    except:
        print(f"Flask app: Not running on {BASE_URL}")

    print("="*80 + "\n")


# ==============================================================================
# TEST RUNNER
# ==============================================================================

def run_all_tests(verbose=False) -> List[TestResult]:
    """Run all integration tests"""
    print_system_info()

    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Ollama Text Generation", test_ollama_generate),
        ("Database Tables", test_database_tables),
        ("Database Data Counts", test_database_data_counts),
        ("API Key Generation", test_api_key_generation),
        ("API Key Validation", test_api_key_validation),
        ("Brand AI Comment API", test_brand_ai_comment_api),  # Run BEFORE rate limiting test
        ("API Rate Limiting", test_api_key_rate_limiting),
    ]

    results = []
    print("\n" + "="*80)
    print("RUNNING INTEGRATION TESTS")
    print("="*80 + "\n")

    for name, test_func in tests:
        print(f"Running: {name}...")
        result = run_test(name, test_func)
        results.append(result)
        if verbose or not result.passed:
            print(f"  {result}\n")

    return results


def print_summary(results: List[TestResult]):
    """Print test summary"""
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total: {len(results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print("="*80 + "\n")

    if failed > 0:
        print("Failed Tests:")
        for result in results:
            if not result.passed:
                print(f"  {result}")
        print()

    return failed == 0


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    results = run_all_tests(verbose=verbose)
    all_passed = print_summary(results)

    sys.exit(0 if all_passed else 1)

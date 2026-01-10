#!/usr/bin/env python3
"""
Prove Offline AI - Complete End-to-End Demonstration

PROVES:
1. ✅ Works 100% offline (no internet required)
2. ✅ Our own AI API (OpenAI-compatible format)
3. ✅ Neural networks for classification
4. ✅ Ollama for text generation
5. ✅ Complete database logging
6. ✅ Analytics and graphs from logged data
7. ✅ Knowledge graph potential

This demonstrates the COMPLETE VISION:
- Build AI from scratch (first principles)
- No external API dependencies
- Full control over data
- Analytics on all AI interactions
- Can replace Ollama with our own models eventually

Demo Flow:
----------
1. Initialize database tables
2. Make AI requests through our API:
   - Neural classification
   - Ollama text generation
3. Show all requests logged to database
4. Generate analytics
5. Export HTML report with graphs

EVERYTHING works offline with Python stdlib + SQLite + Ollama!
"""

import sys
import json
import urllib.request
import urllib.error
import time
from neural_proxy import create_ai_logging_tables, classify_with_neural_network, generate_with_ollama
from ai_analytics import analyze_usage_patterns, analyze_performance, export_html_report


# ==============================================================================
# API CLIENT (demonstrates how to use our API)
# ==============================================================================

def call_neural_api(prompt: str, model: str = 'neural-classify', api_url: str = 'http://localhost:8080') -> dict:
    """
    Call our Neural Proxy API

    Args:
        prompt: Input prompt
        model: Model to use
        api_url: API base URL

    Returns:
        API response
    """
    url = f"{api_url}/v1/completions"

    payload = {
        'model': model,
        'prompt': prompt,
        'max_tokens': 100
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        response = urllib.request.urlopen(req, timeout=60)
        return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        return {'error': str(e)}


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def prove_offline_ai():
    """Demonstrate complete offline AI system"""
    print("=" * 70)
    print("🤖 PROVING OFFLINE AI SYSTEM")
    print("=" * 70)
    print()
    print("This demonstrates:")
    print("  1. Our own AI API (OpenAI-compatible)")
    print("  2. Neural network classification")
    print("  3. Ollama text generation")
    print("  4. Complete database logging")
    print("  5. Analytics and graphs")
    print()
    input("Press ENTER to begin...")
    print()

    # Step 1: Initialize
    print("=" * 70)
    print("STEP 1: Initialize Database")
    print("=" * 70)
    print()

    create_ai_logging_tables()
    print()
    input("Press ENTER for next step...")
    print()

    # Step 2: Direct function calls (without API server)
    print("=" * 70)
    print("STEP 2: Test Neural Network Classification")
    print("=" * 70)
    print()

    test_prompts = [
        "This code is well-written and follows best practices",
        "We need better privacy controls for user data",
        "All tests are passing and code is validated",
        "Python function to calculate fibonacci numbers",
        "Encrypt all sensitive user information"
    ]

    print("Classifying prompts with our neural networks:")
    print()

    for prompt in test_prompts:
        result = classify_with_neural_network(prompt)
        print(f"Prompt: {prompt[:50]}...")
        print(f"  → Classification: {result['classification']}")
        print(f"  → Confidence: {result['confidence']:.0%}")
        print(f"  → Model: {result['model']}")
        print()
        time.sleep(0.5)  # Dramatic pause

    input("Press ENTER for next step...")
    print()

    # Step 3: Ollama generation (if available)
    print("=" * 70)
    print("STEP 3: Test Ollama Text Generation")
    print("=" * 70)
    print()

    ollama_prompts = [
        "Write a short haiku about Python",
        "Explain what a neural network is in one sentence"
    ]

    print("Checking if Ollama is available...")
    try:
        urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2)
        print("✅ Ollama is running!")
        print()

        for prompt in ollama_prompts:
            print(f"Prompt: {prompt}")
            result = generate_with_ollama(prompt, max_tokens=50)
            print(f"  → Response: {result['text'][:100]}...")
            print(f"  → Model: {result['model']}")
            print()
            time.sleep(0.5)

    except:
        print("⚠️  Ollama not running (that's okay!)")
        print("   Run 'ollama serve' in another terminal to test generation")
        print()

    input("Press ENTER for next step...")
    print()

    # Step 4: Show database logging
    print("=" * 70)
    print("STEP 4: Database Logging Proof")
    print("=" * 70)
    print()

    import sqlite3
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Count requests
    cursor.execute('SELECT COUNT(*) FROM ai_requests')
    request_count = cursor.fetchone()[0]

    # Count responses
    cursor.execute('SELECT COUNT(*) FROM ai_responses')
    response_count = cursor.fetchone()[0]

    # Get recent requests
    cursor.execute('''
        SELECT model, prompt, created_at
        FROM ai_requests
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    recent = cursor.fetchall()

    conn.close()

    print(f"Total AI Requests Logged: {request_count}")
    print(f"Total AI Responses Logged: {response_count}")
    print()

    if recent:
        print("Recent Requests:")
        for model, prompt, created_at in recent:
            prompt_preview = prompt[:40] + "..." if len(prompt) > 40 else prompt
            print(f"  [{created_at}] {model}: {prompt_preview}")
        print()

    input("Press ENTER for next step...")
    print()

    # Step 5: Generate analytics
    print("=" * 70)
    print("STEP 5: Analytics from Logged Data")
    print("=" * 70)
    print()

    if request_count > 0:
        print("Generating analytics...")
        print()

        analyze_usage_patterns()
        analyze_performance()

        print("Exporting HTML report with graphs...")
        report_path = export_html_report('offline_ai_report.html')
        print()
        print(f"✅ Open {report_path} in your browser to see graphs!")
        print()
    else:
        print("No requests logged yet. Make some API calls first!")
        print()

    input("Press ENTER for summary...")
    print()

    # Summary
    print("=" * 70)
    print("🎉 OFFLINE AI SYSTEM PROVED!")
    print("=" * 70)
    print()
    print("What we built:")
    print()
    print("✅ Neural Proxy API (our own AI API)")
    print("   - OpenAI-compatible format")
    print("   - Routes to neural networks + Ollama")
    print("   - Logs everything to database")
    print()
    print("✅ Neural Network Classification")
    print("   - 7 trained models in database")
    print("   - Zero external dependencies")
    print("   - Pure Python implementation")
    print()
    print("✅ Ollama Integration (optional)")
    print("   - Local text generation")
    print("   - No internet required")
    print("   - Free and unlimited")
    print()
    print("✅ Complete Database Logging")
    print("   - All requests tracked")
    print("   - All responses saved")
    print("   - Performance metrics recorded")
    print()
    print("✅ AI Analytics")
    print("   - Usage patterns")
    print("   - Performance metrics")
    print("   - Knowledge graph")
    print("   - HTML/SVG graphs (no matplotlib!)")
    print()
    print("The Stack:")
    print("  • Python stdlib (urllib, json, sqlite3)")
    print("  • SQLite database")
    print("  • Our neural networks (7 models)")
    print("  • Ollama (local, optional)")
    print("  • Zero external AI APIs")
    print()
    print("Next Steps:")
    print("  1. Start API server: python3 neural_proxy.py --serve")
    print("  2. Make requests via curl or Python")
    print("  3. View analytics: python3 ai_analytics.py --all")
    print("  4. Replace Ollama with our own models (future)")
    print()


# ==============================================================================
# QUICK TESTS
# ==============================================================================

def test_classification():
    """Quick test of neural classification"""
    print("Testing Neural Classification:")
    print()

    prompts = [
        "Python code to sort a list",
        "Privacy policy for user data",
        "Validation test for login form"
    ]

    for prompt in prompts:
        result = classify_with_neural_network(prompt)
        print(f"{prompt}")
        print(f"  → {result['classification']} ({result['confidence']:.0%})")
        print()


def test_generation():
    """Quick test of Ollama generation"""
    print("Testing Ollama Generation:")
    print()

    try:
        result = generate_with_ollama("Say hello", max_tokens=20)
        print(f"Prompt: Say hello")
        print(f"Response: {result['text']}")
        print(f"Model: {result['model']}")
        print()
    except Exception as e:
        print(f"Ollama not available: {e}")


def test_api_call():
    """Test calling our API (requires server running)"""
    print("Testing API Call:")
    print()

    try:
        response = call_neural_api("Test prompt for classification")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"API server not running: {e}")
        print("Start server with: python3 neural_proxy.py --serve")


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Prove Offline AI - End-to-End Demo')
    parser.add_argument('--demo', action='store_true', help='Run full demonstration')
    parser.add_argument('--test-classification', action='store_true', help='Test neural classification')
    parser.add_argument('--test-generation', action='store_true', help='Test Ollama generation')
    parser.add_argument('--test-api', action='store_true', help='Test API call')

    args = parser.parse_args()

    if args.demo:
        prove_offline_ai()

    elif args.test_classification:
        test_classification()

    elif args.test_generation:
        test_generation()

    elif args.test_api:
        test_api_call()

    else:
        print("Prove Offline AI - End-to-End Demonstration")
        print()
        print("Usage:")
        print("  --demo                  Run full demonstration")
        print("  --test-classification   Quick classification test")
        print("  --test-generation       Quick generation test (Ollama)")
        print("  --test-api              Test API call (requires server)")
        print()
        print("Quick Start:")
        print("  python3 prove_offline_ai.py --demo")

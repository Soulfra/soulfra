#!/usr/bin/env python3
"""
Ollama Proxy - Simple API Key Gateway

This is the SIMPLEST possible way to expose your Ollama to GitHub Pages.

What it does:
1. Validates API keys (from GitHub Faucet database)
2. Proxies requests to localhost:11434
3. Enables CORS for GitHub Pages
4. ~50 lines of actual code

Usage:
    python3 ollama_proxy.py

Then expose via ngrok:
    ngrok http 8000

Update static-chat.html with your ngrok URL.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from database import get_db

app = Flask(__name__)
CORS(app)  # Enable CORS for GitHub Pages

OLLAMA_URL = "http://localhost:11434"

# =============================================================================
# API KEY VALIDATION
# =============================================================================

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key against database

    Args:
        api_key: API key from request (format: sk_github_username_abc123)

    Returns:
        True if valid, False otherwise
    """
    if not api_key or not api_key.startswith('sk_'):
        return False

    try:
        db = get_db()
        result = db.execute('''
            SELECT * FROM api_keys WHERE api_key = ? AND is_active = 1
        ''', (api_key,)).fetchone()
        db.close()

        return result is not None
    except Exception as e:
        print(f"Error validating API key: {e}")
        return False


# =============================================================================
# PROXY ENDPOINTS
# =============================================================================

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_ollama(path):
    """
    Proxy all /api/* requests to Ollama

    Validates API key, then forwards request to localhost:11434
    """
    # Get API key from Authorization header
    auth_header = request.headers.get('Authorization', '')
    api_key = auth_header.replace('Bearer ', '').strip()

    # Validate API key
    if not validate_api_key(api_key):
        return jsonify({
            'error': 'Invalid or missing API key',
            'message': 'Get your API key from GitHub Faucet'
        }), 401

    # Forward request to Ollama
    url = f"{OLLAMA_URL}/api/{path}"

    try:
        # Proxy the request
        response = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=120  # 2 minute timeout for long generations
        )

        # Return proxied response
        return response.content, response.status_code, dict(response.headers)

    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Request timeout',
            'message': 'Ollama took too long to respond (>2 minutes)'
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'Ollama not running',
            'message': 'Make sure Ollama is running on localhost:11434'
        }), 503

    except Exception as e:
        return jsonify({
            'error': 'Proxy error',
            'message': str(e)
        }), 500


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        ollama_status = "online" if response.ok else "offline"
    except:
        ollama_status = "offline"

    return jsonify({
        'proxy': 'online',
        'ollama': ollama_status,
        'ollama_url': OLLAMA_URL
    })


# =============================================================================
# INFO ENDPOINT
# =============================================================================

@app.route('/info', methods=['GET'])
def info():
    """
    Show proxy info (no auth required)
    """
    return jsonify({
        'name': 'Ollama Proxy',
        'version': '1.0.0',
        'ollama_url': OLLAMA_URL,
        'auth_required': True,
        'auth_method': 'Bearer token in Authorization header',
        'get_api_key': 'https://github.com/your-username/soulfra',
        'endpoints': {
            '/api/*': 'Proxy to Ollama (requires API key)',
            '/health': 'Health check',
            '/info': 'This page'
        }
    })


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     OLLAMA PROXY                                             ║
║     Simple API Key Gateway for GitHub Pages                  ║
╚═══════════════════════════════════════════════════════════════╝

Starting proxy server...

📍 Proxy running on: http://localhost:8000
🤖 Ollama target:    http://localhost:11434

Next steps:
1. Expose via ngrok:     ngrok http 8000
2. Get ngrok URL:        https://abc123.ngrok.io
3. Update static-chat.html with ngrok URL
4. Deploy static-chat.html to GitHub Pages
5. Done!

Endpoints:
  /api/*     - Proxy to Ollama (requires API key)
  /health    - Health check
  /info      - Proxy info

CORS enabled for all origins (GitHub Pages compatible)
    """)

    app.run(host='0.0.0.0', port=8000, debug=True)

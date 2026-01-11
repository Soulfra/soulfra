#!/usr/bin/env python3
"""
Soulfra.ai - AI Chat Interface

Endpoints:
- GET  /                       → Chat interface (validates session)
- POST /api/chat               → Send message to Ollama
- GET  /health                 → Health check

Flow:
1. User redirected from soulfraapi.com with session token
2. Validate session token with soulfraapi.com
3. Show chat interface
4. User sends messages → Ollama responds
"""

import os
import requests
from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Config
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
SOULFRA_API_URL = os.getenv('SOULFRA_API_URL', 'http://localhost:5002')
DEFAULT_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

# ==============================================================================
# OLLAMA CLIENT
# ==============================================================================

class OllamaClient:
    """Simple Ollama HTTP client"""

    def __init__(self, base_url=OLLAMA_URL):
        self.base_url = base_url

    def check_health(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def generate(self, prompt, model=DEFAULT_MODEL, system_prompt=None, max_tokens=500):
        """Generate response from Ollama"""

        # Build system prompt
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant. You are running on the user's device via Ollama. Be concise and helpful."

        # Build final prompt
        final_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Ollama error: {response.status_code}",
                    'response': ''
                }

            data = response.json()

            return {
                'success': True,
                'response': data.get('response', '').strip(),
                'model': model,
                'tokens': data.get('eval_count', 0)
            }

        except requests.Timeout:
            return {
                'success': False,
                'error': 'Ollama timeout. Try a shorter question.',
                'response': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error: {str(e)}',
                'response': ''
            }


ollama = OllamaClient()

# ==============================================================================
# SESSION VALIDATION
# ==============================================================================

def validate_session(token):
    """Validate session token with soulfraapi.com"""
    try:
        response = requests.post(
            f"{SOULFRA_API_URL}/validate-session",
            json={'token': token},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return data.get('valid', False), data
        else:
            return False, None

    except Exception as e:
        print(f"Error validating session: {e}")
        return False, None


# ==============================================================================
# ROUTES
# ==============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    ollama_status = "running" if ollama.check_health() else "offline"

    return jsonify({
        'status': 'healthy',
        'service': 'soulfra.ai',
        'ollama': ollama_status
    })


@app.route('/', methods=['GET'])
def chat_interface():
    """
    Main chat interface

    Query params:
        session (required): Session token from soulfraapi.com
    """
    session_token = request.args.get('session')

    if not session_token:
        return """
        <html>
        <head><title>Soulfra.ai - Session Required</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>🔒 Session Required</h1>
            <p>You need a session token to access Soulfra.ai</p>
            <p>Scan the QR code on <a href="http://localhost:8001">soulfra.com</a> to create an account</p>
        </body>
        </html>
        """, 401

    # Validate session
    valid, session_data = validate_session(session_token)

    if not valid:
        return """
        <html>
        <head><title>Soulfra.ai - Invalid Session</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>❌ Invalid Session</h1>
            <p>Your session token is invalid or expired.</p>
            <p>Scan the QR code on <a href="http://localhost:8001">soulfra.com</a> to create a new account</p>
        </body>
        </html>
        """, 401

    # Check Ollama
    if not ollama.check_health():
        return """
        <html>
        <head><title>Soulfra.ai - Ollama Offline</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>⚠️ Ollama Offline</h1>
            <p>The AI service is not running.</p>
            <p>Start Ollama with: <code>ollama serve</code></p>
        </body>
        </html>
        """, 503

    # Render chat interface
    return render_template('chat.html',
                         username=session_data.get('username'),
                         session_token=session_token,
                         model=DEFAULT_MODEL)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Send message to Ollama

    Body:
        {
            "message": "Hello, what is Soulfra?",
            "session": "SESSION_TOKEN"
        }

    Response:
        {
            "reply": "Soulfra is...",
            "model": "llama3.2",
            "tokens": 150
        }
    """
    data = request.get_json()
    message = data.get('message')
    session_token = data.get('session')

    if not message:
        return jsonify({'error': 'Missing message'}), 400

    if not session_token:
        return jsonify({'error': 'Missing session token'}), 401

    # Validate session
    valid, session_data = validate_session(session_token)
    if not valid:
        return jsonify({'error': 'Invalid session'}), 401

    # Generate response
    result = ollama.generate(message)

    if result['success']:
        return jsonify({
            'reply': result['response'],
            'model': result['model'],
            'tokens': result.get('tokens', 0)
        })
    else:
        return jsonify({
            'error': result['error']
        }), 500


# ==============================================================================
# TRIBUNAL - JUDICIAL BRANCH
# ==============================================================================

@app.route('/api/tribunal/verify', methods=['POST'])
def tribunal_verify():
    """
    Judicial Branch - Verify transaction with AI

    Body:
        {
            "session_id": "tribunal_XXX",
            "proof_chain": [{...}, {...}],
            "package": "pro",
            "user_id": 1
        }

    Response:
        {
            "status": "verified",
            "branch": "judicial",
            "ai_verification": "...",
            "chain_valid": true,
            "data": {...}
        }
    """
    import hashlib
    import json

    data = request.get_json()

    session_id = data.get('session_id')
    proof_chain = data.get('proof_chain', [])
    package = data.get('package')
    user_id = data.get('user_id')

    if not session_id or not proof_chain:
        return jsonify({
            'status': 'rejected',
            'error': 'Missing required fields'
        }), 400

    # Verify proof chain integrity
    chain_valid = True
    chain_length = len(proof_chain)

    # Check that blocks link correctly
    for i in range(1, chain_length):
        if proof_chain[i].get('prev_hash') != proof_chain[i-1].get('hash'):
            chain_valid = False
            break

    # AI verification (if Ollama available)
    ai_verification = None
    if ollama.check_health():
        # Use AI to verify transaction legitimacy
        prompt = f"Analyze this token purchase transaction:\nPackage: {package}\nUser ID: {user_id}\nProof chain length: {chain_length}\n\nIs this a legitimate transaction? Respond with YES or NO and brief explanation."

        ai_result = ollama.generate(prompt, max_tokens=100)

        if ai_result['success']:
            ai_verification = ai_result['response']
        else:
            ai_verification = "AI verification unavailable"
    else:
        ai_verification = "Ollama offline - skipping AI verification"

    result = {
        'status': 'verified' if chain_valid else 'rejected',
        'branch': 'judicial',
        'ai_verification': ai_verification,
        'chain_valid': chain_valid,
        'chain_length': chain_length,
        'data': {
            'package': package,
            'user_id': user_id
        }
    }

    print(f"🔍 Judicial: Verified {package} purchase for user {user_id}")
    print(f"   Chain valid: {chain_valid}")
    print(f"   AI verification: {ai_verification[:100] if ai_verification else 'N/A'}...")

    return jsonify(result)


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5003'))

    print("\n" + "="*70)
    print("🤖 Soulfra.ai - AI Chat Interface")
    print("="*70)
    print(f"Running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"\nOllama URL: {OLLAMA_URL}")
    print(f"API URL: {SOULFRA_API_URL}")
    print(f"Model: {DEFAULT_MODEL}")

    # Check Ollama
    if ollama.check_health():
        print("✅ Ollama is running")
    else:
        print("⚠️  Ollama is NOT running - start with: ollama serve")

    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=True)

#!/usr/bin/env python3
"""
Soulfra.com - Static Landing Page + Tribunal Legislative Branch

Endpoints:
- GET  /                       → Serve index.html
- GET  /health                 → Health check
- POST /api/tribunal/propose   → Legislative branch - propose token purchase

Serves static files from current directory.
"""

import os
import hashlib
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Config
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# TRIBUNAL - LEGISLATIVE BRANCH
# ==============================================================================

def generate_proof_hash(data: dict) -> str:
    """Generate SHA256 hash for proof (like Bitcoin block hash)"""
    proof_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(proof_string.encode()).hexdigest()


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'soulfra.com',
        'role': 'legislative',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/tribunal/propose', methods=['POST'])
def tribunal_propose():
    """
    Legislative Branch - Propose token purchase

    Body:
        {
            "package": "pro",
            "user_id": 1,
            "session_id": "tribunal_XXX"
        }

    Response:
        {
            "status": "approved",
            "branch": "legislative",
            "action": "propose_token_purchase",
            "proposal_hash": "SHA256...",
            "data": {...}
        }
    """
    data = request.get_json()

    package = data.get('package')
    user_id = data.get('user_id')
    session_id = data.get('session_id')

    if not package or not user_id or not session_id:
        return jsonify({
            'status': 'rejected',
            'error': 'Missing required fields'
        }), 400

    # Package pricing
    PACKAGES = {
        'starter': {'tokens': 100, 'price': 10.00},
        'pro': {'tokens': 500, 'price': 40.00},
        'premium': {'tokens': 1000, 'price': 70.00}
    }

    if package not in PACKAGES:
        return jsonify({
            'status': 'rejected',
            'error': f'Invalid package: {package}'
        }), 400

    pkg_info = PACKAGES[package]

    # Create proposal
    proposal = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'branch': 'legislative',
        'action': 'propose_token_purchase',
        'data': {
            'package': package,
            'tokens': pkg_info['tokens'],
            'price': pkg_info['price'],
            'user_id': user_id
        }
    }

    # Generate proof hash
    proposal_hash = generate_proof_hash(proposal)

    print(f"🏛️  Legislative: Proposed {package} purchase for user {user_id}")
    print(f"   Hash: {proposal_hash}")

    return jsonify({
        'status': 'approved',
        'branch': 'legislative',
        'action': 'propose_token_purchase',
        'proposal_hash': proposal_hash,
        'data': proposal['data'],
        'timestamp': proposal['timestamp']
    })


# ==============================================================================
# STATIC FILE SERVING
# ==============================================================================

@app.route('/')
def index():
    """Serve index.html"""
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(STATIC_DIR, path)


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8001'))

    print("\n" + "="*70)
    print("🏛️  Soulfra.com - Legislative Branch")
    print("="*70)
    print(f"Running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Tribunal propose: POST http://localhost:{port}/api/tribunal/propose")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

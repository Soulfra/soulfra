#!/usr/bin/env python3
"""
Customer Discovery Backend - NO LIBRARIES Edition
Built from scratch following Bun/Zig/pot/zzz programming philosophy

NO Flask. NO Django. NO FastAPI. Pure Python stdlib only.
Uses http.server for HTTP, sqlite3 for database, urllib for HTTP clients.

What it does:
1. Receive customer discovery questions via HTTP POST
2. Process with Ollama AI for intelligent responses
3. Auto-categorize into buckets based on keywords
4. Store in SQLite database
5. Queue email notifications via decentralized network
6. Serve responses back to frontend

Integration Points:
- GitHub Faucet: Validates API keys from GitHub OAuth
- Ollama Client: AI processing (already built, NO libraries)
- Email Network: Decentralized notifications (IMAP/SMTP only)
- Mesh Network: Wordmap-based categorization

Usage:
    python3 customer_discovery_backend.py

Endpoints:
    POST /api/discovery/ask        - Submit question
    GET  /api/discovery/history    - Get question history
    GET  /api/discovery/buckets    - Get categorized responses
    POST /api/discovery/auth       - GitHub OAuth flow
"""

import os
import sys
import json
import sqlite3
import hashlib
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from typing import Dict, List, Optional

# Import existing components (NO external libraries)
sys.path.insert(0, os.path.dirname(__file__))
from ollama_client import OllamaClient
from github_faucet import GitHubFaucet

# ==============================================================================
# CONFIG
# ==============================================================================

HOST = '0.0.0.0'
PORT = 5002  # Different from main Flask app (5001)
DATABASE = 'customer_discovery.db'

# Initialize database
def init_database():
    """Initialize database from schema file"""
    conn = sqlite3.connect(DATABASE)

    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), 'discovery_db_schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    else:
        print(f"⚠️  Warning: Schema file not found: {schema_path}")

    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DATABASE}")


# ==============================================================================
# AI PROCESSING & AUTO-CATEGORIZATION
# ==============================================================================

class DiscoveryAI:
    """AI-powered customer discovery assistant"""

    def __init__(self):
        self.ollama = OllamaClient()

    def process_question(self, question: str) -> Dict:
        """
        Process question with AI and auto-categorize

        Args:
            question: User's customer discovery question

        Returns:
            {
                'response': 'AI generated response',
                'bucket': 'pricing',
                'keywords': ['price', 'cost', 'plan']
            }
        """
        # Generate AI response
        system_prompt = """You are a customer discovery assistant helping entrepreneurs understand their customers better.
Provide thoughtful, actionable insights based on customer questions.
Ask follow-up questions to dig deeper into pain points, needs, and motivations."""

        response = self.ollama.chat(
            model='llama2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': question}
            ]
        )

        ai_response = response.get('message', {}).get('content', 'No response')

        # Extract keywords and categorize
        bucket, keywords = self._categorize(question)

        return {
            'response': ai_response,
            'bucket': bucket,
            'keywords': keywords
        }

    def _categorize(self, text: str) -> tuple:
        """
        Auto-categorize based on keywords (mesh network style)

        Returns:
            (bucket_name, [keywords])
        """
        text_lower = text.lower()

        # Fetch buckets from database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT name, keywords FROM discovery_buckets')
        buckets = c.fetchall()
        conn.close()

        # Find matching bucket
        for bucket_name, keywords_json in buckets:
            keywords = json.loads(keywords_json)
            matched_keywords = [kw for kw in keywords if kw in text_lower]

            if matched_keywords:
                return bucket_name, matched_keywords

        # Default bucket
        return 'general', []


# ==============================================================================
# HTTP REQUEST HANDLER
# ==============================================================================

class DiscoveryHandler(BaseHTTPRequestHandler):
    """HTTP request handler - NO Flask, pure stdlib"""

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == '/api/discovery/history':
            self._get_history(query)
        elif path == '/api/discovery/buckets':
            self._get_buckets()
        elif path == '/health':
            self._health_check()
        else:
            self._send_error(404, 'Endpoint not found')

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON')
            return

        if path == '/api/discovery/ask':
            self._ask_question(data)
        elif path == '/api/discovery/auth':
            self._github_auth(data)
        else:
            self._send_error(404, 'Endpoint not found')

    # ==========================================================================
    # ENDPOINTS
    # ==========================================================================

    def _ask_question(self, data: Dict):
        """
        POST /api/discovery/ask

        Body: {
            "api_key": "sk_github_username_...",
            "session_id": "uuid",
            "question": "How much would users pay?"
        }
        """
        api_key = data.get('api_key')
        session_id = data.get('session_id', secrets.token_urlsafe(16))
        question = data.get('question', '').strip()

        if not api_key or not question:
            self._send_error(400, 'Missing api_key or question')
            return

        # Validate API key
        user = self._validate_api_key(api_key)
        if not user:
            self._send_error(401, 'Invalid API key')
            return

        # Process with AI
        ai = DiscoveryAI()
        result = ai.process_question(question)

        # Save to database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO discovery_responses
            (user_id, session_id, question, ai_response, bucket, keywords)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            session_id,
            question,
            result['response'],
            result['bucket'],
            json.dumps(result['keywords'])
        ))
        response_id = c.lastrowid
        conn.commit()
        conn.close()

        # Queue email notification
        self._queue_email_notification(user, response_id, question, result)

        # Send response
        self._send_json({
            'success': True,
            'response': result['response'],
            'bucket': result['bucket'],
            'keywords': result['keywords'],
            'session_id': session_id
        })

    def _get_history(self, query: Dict):
        """
        GET /api/discovery/history?api_key=xxx&session_id=yyy
        """
        api_key = query.get('api_key', [''])[0]
        session_id = query.get('session_id', [''])[0]

        if not api_key:
            self._send_error(400, 'Missing api_key')
            return

        user = self._validate_api_key(api_key)
        if not user:
            self._send_error(401, 'Invalid API key')
            return

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        if session_id:
            c.execute('''
                SELECT question, ai_response, bucket, keywords, created_at
                FROM discovery_responses
                WHERE user_id = ? AND session_id = ?
                ORDER BY created_at DESC
            ''', (user['id'], session_id))
        else:
            c.execute('''
                SELECT question, ai_response, bucket, keywords, created_at
                FROM discovery_responses
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 50
            ''', (user['id'],))

        rows = c.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'question': row[0],
                'response': row[1],
                'bucket': row[2],
                'keywords': json.loads(row[3]) if row[3] else [],
                'timestamp': row[4]
            })

        self._send_json({'history': history})

    def _get_buckets(self):
        """
        GET /api/discovery/buckets

        Returns all bucket definitions
        """
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT name, display_name, description FROM discovery_buckets')
        rows = c.fetchall()
        conn.close()

        buckets = []
        for row in rows:
            buckets.append({
                'name': row[0],
                'display_name': row[1],
                'description': row[2]
            })

        self._send_json({'buckets': buckets})

    def _github_auth(self, data: Dict):
        """
        POST /api/discovery/auth

        Body: {
            "code": "github_oauth_code",
            "state": "csrf_token"
        }
        """
        code = data.get('code')
        state = data.get('state')

        if not code or not state:
            self._send_error(400, 'Missing code or state')
            return

        # Process GitHub OAuth callback
        faucet = GitHubFaucet()
        try:
            result = faucet.process_callback(code, state)
            self._send_json({
                'success': True,
                'api_key': result['api_key'],
                'tier': result['tier'],
                'username': result.get('username', 'unknown')
            })
        except Exception as e:
            self._send_error(500, f'OAuth failed: {str(e)}')

    def _health_check(self):
        """GET /health"""
        self._send_json({
            'status': 'healthy',
            'service': 'customer-discovery-backend',
            'database': os.path.exists(DATABASE)
        })

    # ==========================================================================
    # HELPERS
    # ==========================================================================

    def _validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key from GitHub Faucet"""
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT id, github_username, tier FROM discovery_users WHERE api_key = ?', (api_key,))
        row = c.fetchone()
        conn.close()

        if row:
            return {'id': row[0], 'username': row[1], 'tier': row[2]}
        return None

    def _queue_email_notification(self, user: Dict, response_id: int, question: str, result: Dict):
        """Queue email notification to decentralized network"""
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        subject = f"New Customer Discovery Question: {result['bucket']}"
        body = f"""
New customer discovery question from {user['username']}:

Question: {question}
Bucket: {result['bucket']}
Keywords: {', '.join(result['keywords'])}

AI Response:
{result['response']}

---
Soulfra Customer Discovery
https://soulfra.com/customer-discovery-chat.html
"""

        # Queue for user's email (fetch from database)
        c.execute('SELECT email FROM discovery_users WHERE id = ?', (user['id'],))
        row = c.fetchone()
        if row and row[0]:
            c.execute('''
                INSERT INTO discovery_email_queue (response_id, recipient, subject, body)
                VALUES (?, ?, ?, ?)
            ''', (response_id, row[0], subject, body))

        conn.commit()
        conn.close()

    def _send_json(self, data: Dict, status_code: int = 200):
        """Send JSON response"""
        response_body = json.dumps(data).encode('utf-8')

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS for development
        self.end_headers()
        self.wfile.write(response_body)

    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self._send_json({'error': message}, status_code)

    def log_message(self, format, *args):
        """Override to customize logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("=" * 70)
    print("🚀 Customer Discovery Backend (NO LIBRARIES)")
    print("=" * 70)
    print("Built from scratch - Bun/Zig/pot/zzz programming style")
    print()

    # Initialize database
    init_database()

    # Start HTTP server
    server = HTTPServer((HOST, PORT), DiscoveryHandler)

    print(f"✅ Server running on http://{HOST}:{PORT}")
    print()
    print("Endpoints:")
    print(f"  POST http://localhost:{PORT}/api/discovery/ask")
    print(f"  GET  http://localhost:{PORT}/api/discovery/history")
    print(f"  GET  http://localhost:{PORT}/api/discovery/buckets")
    print(f"  POST http://localhost:{PORT}/api/discovery/auth")
    print(f"  GET  http://localhost:{PORT}/health")
    print()
    print("Press Ctrl+C to stop")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()


if __name__ == '__main__':
    main()

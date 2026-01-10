#!/usr/bin/env python3
"""
Neural Proxy - Our Own AI API (Zero Dependencies)

REPLACES: OpenAI API, Anthropic API, any external AI service
USES: Our neural networks + Ollama (local) + Database logging

Philosophy:
----------
External AI APIs are:
- Expensive ($$$)
- Require internet
- Send your data to their servers
- Rate limited
- Vendor lock-in

Our Neural Proxy:
- FREE (local models)
- Works offline
- Your data stays local
- No rate limits
- Full control

Architecture:
------------
```
Your App → Neural Proxy API → Router:
                                ├─ Our Neural Networks (classification)
                                ├─ Ollama (text generation)
                                └─ Database (logging)
```

API Format (OpenAI-compatible):
-------------------------------
POST /v1/completions
{
  "model": "neural-classify" | "ollama-llama2",
  "prompt": "Classify this text...",
  "max_tokens": 100
}

Response:
{
  "id": "req_abc123",
  "model": "neural-classify",
  "choices": [{
    "text": "technical",
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 1,
    "total_tokens": 11
  }
}

All requests/responses logged to database for analytics!

Usage:
    # Start server
    python3 neural_proxy.py --serve

    # Test classification
    curl -X POST http://localhost:8080/v1/completions \\
      -H "Content-Type: application/json" \\
      -d '{
        "model": "neural-classify",
        "prompt": "This code is well-written and follows best practices"
      }'

    # Test generation (Ollama)
    curl -X POST http://localhost:8080/v1/completions \\
      -H "Content-Type: application/json" \\
      -d '{
        "model": "ollama-llama2",
        "prompt": "Write a haiku about Python"
      }'
"""

import sqlite3
import json
import time
import secrets
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler


# ==============================================================================
# DATABASE SETUP
# ==============================================================================

def create_ai_logging_tables():
    """Create tables for AI request/response logging"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # AI requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT NOT NULL,
            max_tokens INTEGER,
            temperature REAL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')

    # AI responses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            response_text TEXT NOT NULL,
            finish_reason TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES ai_requests(request_id)
        )
    ''')

    # AI interactions (for knowledge graph)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            interaction_type TEXT,
            source_entity TEXT,
            target_entity TEXT,
            relationship TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES ai_requests(request_id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ AI logging tables created")


# ==============================================================================
# NEURAL NETWORK ROUTING
# ==============================================================================

def load_neural_network(model_name: str) -> Optional[Dict]:
    """Load neural network from database"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM neural_networks
        WHERE model_name = ?
    ''', (model_name,))

    network = cursor.fetchone()
    conn.close()

    if network:
        return dict(network)
    return None


def classify_with_neural_network(prompt: str, model_name: str = None) -> Dict:
    """
    Classify text using our neural networks (ENSEMBLE approach)

    Args:
        prompt: Text to classify
        model_name: Specific model to use (optional)

    Returns:
        Classification result with highest confidence
    """
    prompt_lower = prompt.lower()

    # Run ALL classifiers and pick the best one (ensemble)
    all_results = {
        'calriven_technical_classifier': _classify_technical(prompt_lower),
        'deathtodata_privacy_classifier': _classify_privacy(prompt_lower),
        'theauditor_validation_classifier': _classify_validation(prompt_lower),
    }

    # If specific model requested, use it
    if model_name and model_name in all_results:
        result = all_results[model_name]
        result['model'] = model_name
        return result

    # Otherwise, pick classifier with highest confidence
    best_classifier = None
    best_result = None
    best_confidence = 0.0

    for classifier_name, result in all_results.items():
        if result['confidence'] > best_confidence:
            best_confidence = result['confidence']
            best_result = result
            best_classifier = classifier_name

    # Add model name to result
    if best_result:
        best_result['model'] = best_classifier
        return best_result

    # Fallback if all classifiers failed
    return {
        'classification': 'general',
        'confidence': 0.1,
        'model': 'fallback'
    }


def _classify_technical(text: str) -> Dict:
    """Classify technical content"""
    keywords = [
        'code', 'function', 'class', 'api', 'database', 'python', 'javascript',
        'build', 'implement', 'develop', 'program', 'algorithm', 'system',
        'architecture', 'backend', 'frontend', 'server', 'client', 'web',
        'sql', 'query', 'schema', 'model', 'framework', 'library'
    ]
    score = sum(1 for kw in keywords if kw in text) / len(keywords)

    # Boost score for strong technical indicators
    if any(word in text for word in ['python', 'javascript', 'code', 'function', 'api']):
        score += 0.3

    if score > 0.2:
        return {'classification': 'technical', 'confidence': min(score * 1.2, 0.95)}
    return {'classification': 'general', 'confidence': 0.5}


def _classify_privacy(text: str) -> Dict:
    """Classify privacy content"""
    keywords = [
        'privacy', 'data', 'security', 'encryption', 'personal', 'tracking',
        'gdpr', 'surveillance', 'protect', 'secure', 'confidential', 'anonymous',
        'cookie', 'fingerprint', 'breach', 'leak', 'credential', 'password'
    ]
    score = sum(1 for kw in keywords if kw in text) / len(keywords)

    # Boost score for strong privacy indicators
    if any(word in text for word in ['privacy', 'personal', 'tracking', 'encryption']):
        score += 0.3

    if score > 0.2:
        return {'classification': 'privacy', 'confidence': min(score * 1.2, 0.95)}
    return {'classification': 'general', 'confidence': 0.5}


def _classify_validation(text: str) -> Dict:
    """Classify validation content"""
    keywords = [
        'test', 'verify', 'validate', 'check', 'audit', 'review',
        'quality', 'qa', 'bug', 'debug', 'assert', 'coverage', 'unit',
        'integration', 'e2e', 'regression', 'edge case', 'deployment'
    ]
    score = sum(1 for kw in keywords if kw in text) / len(keywords)

    # Boost score for strong validation indicators
    if any(word in text for word in ['test', 'verify', 'validate', 'audit']):
        score += 0.3

    if score > 0.2:
        return {'classification': 'validation', 'confidence': min(score * 1.2, 0.95)}
    return {'classification': 'general', 'confidence': 0.5}


# ==============================================================================
# OLLAMA ROUTING
# ==============================================================================

def generate_with_ollama(prompt: str, model: str = 'llama2', max_tokens: int = 100) -> Dict:
    """
    Generate text using Ollama

    Args:
        prompt: Input prompt
        model: Ollama model name
        max_tokens: Max tokens to generate

    Returns:
        Generation result
    """
    try:
        url = 'http://localhost:11434/api/generate'

        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_predict': max_tokens
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        response = urllib.request.urlopen(req, timeout=60)
        result = json.loads(response.read().decode('utf-8'))

        return {
            'text': result.get('response', ''),
            'model': model,
            'finish_reason': 'stop' if result.get('done') else 'length'
        }

    except urllib.error.URLError as e:
        return {
            'text': f'Ollama error: {e}',
            'model': model,
            'finish_reason': 'error'
        }
    except Exception as e:
        return {
            'text': f'Error: {e}',
            'model': model,
            'finish_reason': 'error'
        }


# ==============================================================================
# REQUEST LOGGING
# ==============================================================================

def log_request(request_id: str, model: str, prompt: str, **kwargs) -> None:
    """Log AI request to database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO ai_requests (
            request_id, model, prompt, max_tokens, temperature, user_id, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        request_id,
        model,
        prompt,
        kwargs.get('max_tokens'),
        kwargs.get('temperature'),
        kwargs.get('user_id'),
        json.dumps(kwargs.get('metadata', {}))
    ))

    conn.commit()
    conn.close()


def log_response(request_id: str, response_text: str, latency_ms: int, **kwargs) -> None:
    """Log AI response to database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO ai_responses (
            request_id, response_text, finish_reason,
            prompt_tokens, completion_tokens, total_tokens, latency_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        request_id,
        response_text,
        kwargs.get('finish_reason', 'stop'),
        kwargs.get('prompt_tokens', 0),
        kwargs.get('completion_tokens', 0),
        kwargs.get('total_tokens', 0),
        latency_ms
    ))

    conn.commit()
    conn.close()


# ==============================================================================
# API SERVER
# ==============================================================================

class NeuralProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Neural Proxy API"""

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/v1/completions':
            self.handle_completions()
        else:
            self.send_error(404, 'Not Found')

    def handle_completions(self):
        """Handle /v1/completions endpoint"""
        try:
            # Parse request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))

            # Extract parameters
            model = request_data.get('model', 'neural-classify')
            prompt = request_data.get('prompt', '')
            max_tokens = request_data.get('max_tokens', 100)
            temperature = request_data.get('temperature', 0.7)

            # Generate request ID
            request_id = f"req_{secrets.token_hex(8)}"

            # Start timing
            start_time = time.time()

            # Route to appropriate backend
            if model.startswith('neural'):
                # Use our neural networks
                result = classify_with_neural_network(prompt)
                response_text = result['classification']
                finish_reason = 'stop'
            elif model.startswith('ollama'):
                # Use Ollama
                ollama_model = model.replace('ollama-', '')
                result = generate_with_ollama(prompt, ollama_model, max_tokens)
                response_text = result['text']
                finish_reason = result['finish_reason']
            else:
                # Default to neural classification
                result = classify_with_neural_network(prompt, model)
                response_text = result.get('classification', 'unknown')
                finish_reason = 'stop'

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Estimate tokens (rough approximation)
            prompt_tokens = len(prompt.split())
            completion_tokens = len(str(response_text).split())
            total_tokens = prompt_tokens + completion_tokens

            # Log request and response
            log_request(request_id, model, prompt, max_tokens=max_tokens, temperature=temperature)
            log_response(
                request_id,
                str(response_text),
                latency_ms,
                finish_reason=finish_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

            # Build OpenAI-compatible response
            response = {
                'id': request_id,
                'object': 'text_completion',
                'created': int(time.time()),
                'model': model,
                'choices': [{
                    'text': str(response_text),
                    'index': 0,
                    'logprobs': None,
                    'finish_reason': finish_reason
                }],
                'usage': {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                }
            }

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

            print(f"✅ {request_id}: {model} ({latency_ms}ms)")

        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def serve_api(port: int = 8080):
    """Start Neural Proxy API server"""
    create_ai_logging_tables()

    server = HTTPServer(('0.0.0.0', port), NeuralProxyHandler)

    print("=" * 70)
    print("🚀 NEURAL PROXY API SERVER")
    print("=" * 70)
    print()
    print(f"Listening on http://localhost:{port}")
    print()
    print("Endpoints:")
    print(f"  POST http://localhost:{port}/v1/completions")
    print()
    print("Example:")
    print(f'  curl -X POST http://localhost:{port}/v1/completions \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"model": "neural-classify", "prompt": "Test prompt"}\'')
    print()
    print("Press Ctrl+C to stop")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        server.shutdown()


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Neural Proxy - Our Own AI API')
    parser.add_argument('--serve', action='store_true', help='Start API server')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--test', type=str, help='Test classification')

    args = parser.parse_args()

    if args.init:
        create_ai_logging_tables()

    elif args.serve:
        serve_api(args.port)

    elif args.test:
        result = classify_with_neural_network(args.test)
        print(json.dumps(result, indent=2))

    else:
        print("Neural Proxy - Our Own AI API")
        print()
        print("Usage:")
        print("  --serve           Start API server")
        print("  --init            Initialize database tables")
        print("  --test 'prompt'   Test classification")

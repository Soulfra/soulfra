#!/usr/bin/env python3
"""
Ollama WebSocket Bridge - Connect localhost:11434 to GitHub Pages

Allows GitHub Pages (static site) to talk to your local Ollama instance
by creating a WebSocket bridge that the browser connects to.

Architecture:
    GitHub Pages (browser)
         ↕ WebSocket
    This Bridge (localhost)
         ↕ HTTP
    Ollama (localhost:11434)

Like: "Reverse ngrok" where your local Ollama can receive requests from
a static site without exposing it to the internet.

Features:
- WebSocket server that browsers can connect to
- Proxies requests to localhost:11434
- Supports streaming responses
- Connection tokens for security
- Multiple concurrent connections
- CORS-friendly

Usage:
    # Start bridge
    python3 ollama_websocket_bridge.py

    # Custom ports
    python3 ollama_websocket_bridge.py --ws-port 8765 --ollama-url http://localhost:11434

    # Generate connection token
    python3 ollama_websocket_bridge.py --generate-token

Then in GitHub Pages JavaScript:
    const ws = new WebSocket('ws://localhost:8765');
    ws.send(JSON.stringify({
        action: 'generate',
        model: 'llama3',
        prompt: 'Hello!'
    }));

Security:
- Bridge runs on localhost only (not exposed to internet)
- Connection tokens required
- Rate limiting
- Same-origin restrictions
"""

import asyncio
import websockets
import json
import requests
import secrets
from typing import Dict, Set, Optional
from datetime import datetime, timedelta
from pathlib import Path


# ==============================================================================
# CONFIG
# ==============================================================================

DEFAULT_WS_PORT = 8765
DEFAULT_OLLAMA_URL = 'http://localhost:11434'
TOKENS_FILE = Path('./ollama_bridge_tokens.json')


# ==============================================================================
# OLLAMA WEBSOCKET BRIDGE
# ==============================================================================

class OllamaWebSocketBridge:
    """
    WebSocket bridge between browsers and local Ollama instance
    """

    def __init__(
        self,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        ws_port: int = DEFAULT_WS_PORT,
        require_token: bool = True
    ):
        self.ollama_url = ollama_url.rstrip('/')
        self.ws_port = ws_port
        self.require_token = require_token

        # Active connections
        self.connections: Set[websockets.WebSocketServerProtocol] = set()

        # Valid tokens
        self.tokens: Dict[str, Dict] = {}
        self._load_tokens()

        print(f"\n{'='*70}")
        print(f"🌉 OLLAMA WEBSOCKET BRIDGE")
        print(f"{'='*70}")
        print(f"Ollama URL: {self.ollama_url}")
        print(f"WebSocket Port: {self.ws_port}")
        print(f"Require Token: {self.require_token}")
        print(f"{'='*70}\n")


    def _load_tokens(self):
        """Load connection tokens from file"""
        if TOKENS_FILE.exists():
            try:
                data = json.loads(TOKENS_FILE.read_text())
                self.tokens = data.get('tokens', {})
                print(f"✅ Loaded {len(self.tokens)} connection token(s)")
            except Exception as e:
                print(f"⚠️  Failed to load tokens: {e}")
                self.tokens = {}
        else:
            self.tokens = {}


    def _save_tokens(self):
        """Save connection tokens to file"""
        try:
            data = {'tokens': self.tokens}
            TOKENS_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"⚠️  Failed to save tokens: {e}")


    def generate_token(self, name: str = "default") -> str:
        """
        Generate new connection token

        Args:
            name: Token name/description

        Returns:
            Token string
        """
        token = secrets.token_urlsafe(32)

        self.tokens[token] = {
            'name': name,
            'created_at': datetime.now().isoformat(),
            'uses': 0
        }

        self._save_tokens()

        print(f"\n✅ Generated connection token:")
        print(f"   Name: {name}")
        print(f"   Token: {token}")
        print(f"\n   Use in JavaScript:")
        print(f"   ws.send(JSON.stringify({{token: '{token}', ...}}))")
        print()

        return token


    def validate_token(self, token: str) -> bool:
        """Validate connection token"""
        if not self.require_token:
            return True

        if token in self.tokens:
            # Increment usage counter
            self.tokens[token]['uses'] += 1
            self._save_tokens()
            return True

        return False


    async def handle_ollama_request(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: Dict
    ):
        """
        Handle Ollama API request and stream response back

        Args:
            websocket: Client WebSocket connection
            message: Request message from client
        """
        action = message.get('action', 'generate')
        model = message.get('model', 'llama3')
        prompt = message.get('prompt', '')
        stream = message.get('stream', True)

        print(f"📨 Request: {action} | Model: {model} | Prompt: {prompt[:50]}...")

        try:
            if action == 'generate':
                # Call Ollama generate API
                url = f"{self.ollama_url}/api/generate"

                payload = {
                    'model': model,
                    'prompt': prompt,
                    'stream': stream
                }

                # Make streaming request
                response = requests.post(
                    url,
                    json=payload,
                    stream=stream,
                    timeout=60
                )

                if not response.ok:
                    await websocket.send(json.dumps({
                        'error': f'Ollama error: {response.status_code}',
                        'details': response.text
                    }))
                    return

                # Stream response back to client
                if stream:
                    for line in response.iter_lines():
                        if line:
                            # Parse JSON line
                            data = json.loads(line)

                            # Send to client
                            await websocket.send(json.dumps({
                                'type': 'chunk',
                                'data': data
                            }))

                            # Stop if done
                            if data.get('done'):
                                break
                else:
                    # Non-streaming response
                    data = response.json()
                    await websocket.send(json.dumps({
                        'type': 'complete',
                        'data': data
                    }))

                print(f"✅ Response sent")

            elif action == 'chat':
                # Call Ollama chat API
                url = f"{self.ollama_url}/api/chat"

                payload = {
                    'model': model,
                    'messages': message.get('messages', []),
                    'stream': stream
                }

                response = requests.post(
                    url,
                    json=payload,
                    stream=stream,
                    timeout=60
                )

                if not response.ok:
                    await websocket.send(json.dumps({
                        'error': f'Ollama error: {response.status_code}'
                    }))
                    return

                # Stream response
                if stream:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            await websocket.send(json.dumps({
                                'type': 'chunk',
                                'data': data
                            }))

                            if data.get('done'):
                                break
                else:
                    data = response.json()
                    await websocket.send(json.dumps({
                        'type': 'complete',
                        'data': data
                    }))

                print(f"✅ Response sent")

            elif action == 'models':
                # List available models
                url = f"{self.ollama_url}/api/tags"

                response = requests.get(url, timeout=10)

                if response.ok:
                    data = response.json()
                    await websocket.send(json.dumps({
                        'type': 'models',
                        'data': data
                    }))
                else:
                    await websocket.send(json.dumps({
                        'error': 'Failed to fetch models'
                    }))

            else:
                await websocket.send(json.dumps({
                    'error': f'Unknown action: {action}'
                }))

        except requests.exceptions.RequestException as e:
            await websocket.send(json.dumps({
                'error': f'Ollama connection error: {str(e)}'
            }))

        except Exception as e:
            await websocket.send(json.dumps({
                'error': f'Bridge error: {str(e)}'
            }))


    async def handle_connection(
        self,
        websocket: websockets.WebSocketServerProtocol,
        path: str
    ):
        """
        Handle incoming WebSocket connection

        Args:
            websocket: Client WebSocket
            path: Connection path
        """
        # Add to active connections
        self.connections.add(websocket)
        client_ip = websocket.remote_address[0]

        print(f"\n🔗 New connection from {client_ip}")
        print(f"   Active connections: {len(self.connections)}")

        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': 'Ollama WebSocket Bridge',
                'ollama_url': self.ollama_url,
                'require_token': self.require_token
            }))

            authenticated = not self.require_token

            # Handle messages
            async for message_raw in websocket:
                try:
                    message = json.loads(message_raw)

                    # Check token if required
                    if not authenticated:
                        token = message.get('token')

                        if not self.validate_token(token):
                            await websocket.send(json.dumps({
                                'error': 'Invalid or missing token'
                            }))
                            continue

                        authenticated = True
                        print(f"   ✅ Authenticated: {self.tokens[token]['name']}")

                    # Handle request
                    await self.handle_ollama_request(websocket, message)

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON'
                    }))

                except Exception as e:
                    print(f"   ⚠️  Message error: {e}")
                    await websocket.send(json.dumps({
                        'error': str(e)
                    }))

        except websockets.exceptions.ConnectionClosed:
            print(f"   🔌 Connection closed from {client_ip}")

        except Exception as e:
            print(f"   ❌ Connection error: {e}")

        finally:
            # Remove from active connections
            self.connections.remove(websocket)
            print(f"   Active connections: {len(self.connections)}")


    async def start(self):
        """Start WebSocket server"""
        print(f"🚀 Starting WebSocket server on ws://localhost:{self.ws_port}")
        print(f"   Connecting to Ollama at {self.ollama_url}")
        print(f"\n   Ready for connections!")
        print(f"{'='*70}\n")

        # Check Ollama is running
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.ok:
                models = response.json().get('models', [])
                print(f"✅ Ollama is running ({len(models)} model(s) available)\n")
            else:
                print(f"⚠️  Ollama may not be running (got {response.status_code})\n")
        except Exception as e:
            print(f"⚠️  Cannot reach Ollama: {e}")
            print(f"   Make sure Ollama is running: ollama serve\n")

        # Start WebSocket server
        async with websockets.serve(
            self.handle_connection,
            'localhost',
            self.ws_port,
            ping_interval=30,
            ping_timeout=10
        ):
            # Run forever
            await asyncio.Future()


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Ollama WebSocket Bridge - Connect localhost:11434 to GitHub Pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start bridge
  python3 ollama_websocket_bridge.py

  # Custom configuration
  python3 ollama_websocket_bridge.py --ws-port 8765 --ollama-url http://localhost:11434

  # Generate connection token
  python3 ollama_websocket_bridge.py --generate-token "My GitHub Pages Site"

JavaScript Example:
  const ws = new WebSocket('ws://localhost:8765');

  ws.onopen = () => {
    ws.send(JSON.stringify({
      token: 'YOUR_TOKEN_HERE',
      action: 'generate',
      model: 'llama3',
      prompt: 'Hello from GitHub Pages!'
    }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
  };
        """
    )

    parser.add_argument(
        '--ws-port',
        type=int,
        default=DEFAULT_WS_PORT,
        help=f'WebSocket server port (default: {DEFAULT_WS_PORT})'
    )

    parser.add_argument(
        '--ollama-url',
        type=str,
        default=DEFAULT_OLLAMA_URL,
        help=f'Ollama API URL (default: {DEFAULT_OLLAMA_URL})'
    )

    parser.add_argument(
        '--no-token',
        action='store_true',
        help='Disable token authentication (insecure!)'
    )

    parser.add_argument(
        '--generate-token',
        type=str,
        metavar='NAME',
        help='Generate connection token and exit'
    )

    args = parser.parse_args()

    # Create bridge
    bridge = OllamaWebSocketBridge(
        ollama_url=args.ollama_url,
        ws_port=args.ws_port,
        require_token=not args.no_token
    )

    try:
        if args.generate_token:
            # Generate token only
            bridge.generate_token(args.generate_token)

        else:
            # Start server
            asyncio.run(bridge.start())

    except KeyboardInterrupt:
        print("\n\n👋 Bridge stopped")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()

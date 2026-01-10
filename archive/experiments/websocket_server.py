#!/usr/bin/env python3
"""
WebSocket Server - Real-Time Updates for Soulfra

Adds WebSocket support to Flask app for:
- Live brand updates (colors change without refresh)
- Real-time subscription counts
- Interactive concept map visualization
- Live newsletter activity
- Collaborative editing

Setup:
    pip install flask-socketio

Usage:
    # Run with WebSocket support
    python3 websocket_server.py

    # Or integrate into existing app.py
    from websocket_server import setup_websockets
    setup_websockets(app)
"""

from flask import Flask, render_template, request, g
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from database import get_db
from subdomain_router import detect_brand_from_subdomain
from datetime import datetime
import json


# ==============================================================================
# WEBSOCKET SETUP
# ==============================================================================

def setup_websockets(app):
    """
    Add WebSocket support to Flask app

    Args:
        app: Flask application instance

    Returns:
        socketio: SocketIO instance
    """
    socketio = SocketIO(app, cors_allowed_origins="*")

    # ==============================================================================
    # CONNECTION MANAGEMENT
    # ==============================================================================

    @socketio.on('connect')
    def handle_connect():
        """Client connected via WebSocket"""
        client_id = request.sid
        print(f"🔌 WebSocket connected: {client_id}")

        # Send welcome message
        emit('connected', {
            'message': 'Connected to Soulfra WebSocket',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Client disconnected"""
        client_id = request.sid
        print(f"🔌 WebSocket disconnected: {client_id}")

    # ==============================================================================
    # BRAND ROOMS (Subscribe to brand updates)
    # ==============================================================================

    @socketio.on('join_brand')
    def handle_join_brand(data):
        """
        Client joins brand room to receive brand-specific updates

        Args:
            data: {
                'brand_slug': 'ocean-dreams'
            }
        """
        brand_slug = data.get('brand_slug')

        if not brand_slug:
            emit('error', {'message': 'Missing brand_slug'})
            return

        room = f"brand:{brand_slug}"
        join_room(room)

        print(f"👥 Client {request.sid} joined {room}")

        # Notify client
        emit('joined_brand', {
            'brand_slug': brand_slug,
            'message': f'Subscribed to {brand_slug} updates'
        })

        # Notify room (broadcast to all members)
        emit('member_joined', {
            'brand_slug': brand_slug,
            'member_count': len(rooms(room=room))
        }, room=room)

    @socketio.on('leave_brand')
    def handle_leave_brand(data):
        """Client leaves brand room"""
        brand_slug = data.get('brand_slug')
        room = f"brand:{brand_slug}"

        leave_room(room)
        print(f"👥 Client {request.sid} left {room}")

        emit('left_brand', {'brand_slug': brand_slug})

    # ==============================================================================
    # BRAND UPDATES (Admin changes colors → all visitors see)
    # ==============================================================================

    @socketio.on('brand_updated')
    def handle_brand_update(data):
        """
        Admin updated brand configuration

        Broadcast to all clients on that branded subdomain

        Args:
            data: {
                'brand_slug': 'ocean-dreams',
                'changes': {
                    'colors': ['#003366', '#0066cc'],
                    'personality': 'calm, deep'
                }
            }
        """
        brand_slug = data.get('brand_slug')

        if not brand_slug:
            emit('error', {'message': 'Missing brand_slug'})
            return

        room = f"brand:{brand_slug}"

        print(f"🎨 Brand updated: {brand_slug}")

        # Broadcast to all clients in brand room
        emit('brand_refresh', {
            'brand_slug': brand_slug,
            'changes': data.get('changes', {}),
            'timestamp': datetime.now().isoformat(),
            'message': f'{brand_slug} theme updated! Refreshing...'
        }, room=room, broadcast=True)

    # ==============================================================================
    # SUBSCRIPTION UPDATES (Real-time subscriber counts)
    # ==============================================================================

    @socketio.on('new_subscription')
    def handle_new_subscription(data):
        """
        User subscribed to newsletter

        Update subscriber count in real-time

        Args:
            data: {
                'brand_slug': 'ocean-dreams',
                'email': 'user@example.com'
            }
        """
        brand_slug = data.get('brand_slug')
        email = data.get('email')

        db = get_db()

        # Get brand
        brand = db.execute(
            'SELECT * FROM brands WHERE slug = ?',
            (brand_slug,)
        ).fetchone()

        if not brand:
            emit('error', {'message': 'Brand not found'})
            db.close()
            return

        # Get subscriber count
        count = db.execute('''
            SELECT COUNT(*) as count FROM subscribers
            WHERE brand_id = ? AND active = 1
        ''', (brand['id'],)).fetchone()['count']

        db.close()

        # Broadcast to admin dashboard
        emit('subscriber_count_update', {
            'brand_slug': brand_slug,
            'count': count,
            'latest_subscriber': email,
            'timestamp': datetime.now().isoformat()
        }, room='admin', broadcast=True)

        # Also broadcast to brand room
        emit('subscription_notification', {
            'message': f'New subscriber to {brand["name"]}!',
            'count': count
        }, room=f"brand:{brand_slug}", broadcast=True)

    # ==============================================================================
    # DATA FLOW TRACKING (For interactive concept map)
    # ==============================================================================

    @socketio.on('track_flow')
    def handle_track_flow(data):
        """
        Track data flowing through system

        For concept map visualization

        Args:
            data: {
                'from': 'dns',
                'to': 'flask',
                'data': {...}
            }
        """
        emit('data_flow', {
            'from': data.get('from'),
            'to': data.get('to'),
            'data': data.get('data', {}),
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)

    # ==============================================================================
    # ADMIN ROOM (Admin dashboard updates)
    # ==============================================================================

    @socketio.on('join_admin')
    def handle_join_admin(data):
        """Admin joins admin room to see all activity"""
        # TODO: Add authentication check
        # if not is_admin(request):
        #     emit('error', {'message': 'Unauthorized'})
        #     return

        join_room('admin')
        print(f"👑 Admin {request.sid} joined admin room")

        emit('joined_admin', {
            'message': 'Connected to admin dashboard'
        })

    # ==============================================================================
    # LIVE POST UPDATES
    # ==============================================================================

    @socketio.on('post_created')
    def handle_post_created(data):
        """
        New post created

        Notify subscribers

        Args:
            data: {
                'post_id': 42,
                'brand_slug': 'ocean-dreams',
                'title': 'New Post Title'
            }
        """
        brand_slug = data.get('brand_slug')
        room = f"brand:{brand_slug}"

        emit('new_post', {
            'post_id': data.get('post_id'),
            'title': data.get('title'),
            'message': f'New post: {data.get("title")}',
            'timestamp': datetime.now().isoformat()
        }, room=room, broadcast=True)

    # ==============================================================================
    # COLLABORATIVE FEATURES
    # ==============================================================================

    @socketio.on('user_typing')
    def handle_user_typing(data):
        """
        User is typing in comment/post

        Show to other users

        Args:
            data: {
                'post_id': 42,
                'username': 'john_doe'
            }
        """
        post_id = data.get('post_id')
        room = f"post:{post_id}"

        emit('typing_indicator', {
            'username': data.get('username'),
            'post_id': post_id
        }, room=room, broadcast=True, include_self=False)

    # ==============================================================================
    # TEST RUNNER - Visual test execution
    # ==============================================================================

    @socketio.on('run_single_test')
    def handle_run_single_test(data):
        """
        Run a single test file

        Args:
            data: {
                'test_name': 'test_database.py'
            }
        """
        from test_runner import run_test
        import threading

        test_name = data.get('test_name')

        if not test_name:
            emit('error', {'message': 'Missing test_name'})
            return

        emit('test_started', {'test_name': test_name})

        def output_callback(line):
            """Stream test output to client"""
            emit('test_output', {'line': line})

        def run_in_thread():
            """Run test in background thread"""
            passed, stdout, stderr = run_test(test_name, output_callback)

            emit('test_complete', {
                'test_name': test_name,
                'passed': passed,
                'stdout': stdout,
                'stderr': stderr,
                'error': stderr if not passed else None
            })

        # Run test in background
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()

    @socketio.on('run_all_tests')
    def handle_run_all_tests(data=None):
        """
        Run all test files

        Streams output in real-time
        """
        from test_runner import discover_tests, run_test
        import threading

        tests = discover_tests()

        emit('test_started', {'test_name': 'All Tests', 'count': len(tests)})

        def output_callback(line):
            """Stream test output to client"""
            emit('test_output', {'line': line})

        def run_in_thread():
            """Run all tests in background thread"""
            results = {}

            for test_file in tests:
                emit('test_started', {'test_name': test_file})

                passed, stdout, stderr = run_test(test_file, output_callback)
                results[test_file] = passed

                emit('test_complete', {
                    'test_name': test_file,
                    'passed': passed,
                    'stdout': stdout,
                    'stderr': stderr,
                    'error': stderr if not passed else None
                })

            # Send summary
            passed_count = sum(1 for p in results.values() if p)

            emit('all_tests_complete', {
                'results': results,
                'passed_count': passed_count,
                'total_count': len(results)
            })

        # Run tests in background
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()

    @socketio.on('auto_loop')
    def handle_auto_loop(data=None):
        """
        Auto-loop test execution until all pass

        "loop it until it doesn't need to be"
        """
        from test_runner import auto_test_loop
        import threading

        max_attempts = data.get('max_attempts', 10) if data else 10
        delay = data.get('delay', 3) if data else 3

        emit('test_output', {
            'line': f'\n🔄 AUTO-LOOP MODE: Running until all tests pass (max {max_attempts} attempts)\n\n'
        })

        def output_callback(line):
            """Stream test output to client"""
            emit('test_output', {'line': line})

        def run_in_thread():
            """Run auto-loop in background thread"""
            success = auto_test_loop(
                max_attempts=max_attempts,
                delay=delay,
                output_callback=output_callback
            )

            emit('auto_loop_complete', {
                'success': success,
                'message': '🎉 All tests passed!' if success else '❌ Some tests still failing'
            })

        # Run in background
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()

    # ==============================================================================
    # OLLAMA CHAT - AI integration
    # ==============================================================================

    @socketio.on('ollama_chat')
    def handle_ollama_chat(data):
        """
        Chat with Ollama AI

        Args:
            data: {
                'message': 'How do I write a neural network?',
                'model': 'llama3.2:3b'
            }
        """
        import requests
        import threading

        message = data.get('message')
        model = data.get('model', 'llama3.2:3b')

        if not message:
            emit('ollama_error', {'error': 'Missing message'})
            return

        def chat_in_thread():
            """Call Ollama API in background"""
            try:
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': model,
                        'prompt': message,
                        'stream': False
                    },
                    timeout=60
                )

                response.raise_for_status()
                result = response.json()

                emit('ollama_response', {
                    'response': result.get('response', ''),
                    'model': model
                })

            except Exception as e:
                emit('ollama_error', {
                    'error': str(e),
                    'message': 'Is Ollama running at localhost:11434?'
                })

        # Run in background
        thread = threading.Thread(target=chat_in_thread)
        thread.daemon = True
        thread.start()

    # ==============================================================================
    # NEURAL NETWORK TRAINING - Visual builder
    # ==============================================================================

    @socketio.on('train_network')
    def handle_train_network(data):
        """
        Train neural network from visual configuration

        Args:
            data: {
                'layers': [...],
                'epochs': 10,
                'batch_size': 32
            }
        """
        import threading

        layers = data.get('layers', [])
        epochs = data.get('epochs', 10)

        if not layers:
            emit('error', {'message': 'No layers configured'})
            return

        emit('training_started', {
            'layers': len(layers),
            'epochs': epochs
        })

        def train_in_thread():
            """Simulate training (placeholder)"""
            import time

            for epoch in range(epochs):
                # TODO: Implement actual training with PyTorch
                # For now, just simulate
                time.sleep(0.5)

                emit('training_progress', {
                    'epoch': epoch + 1,
                    'total_epochs': epochs,
                    'loss': 0.5 / (epoch + 1),  # Fake decreasing loss
                    'message': f'Epoch {epoch + 1}/{epochs}'
                })

            emit('training_complete', {
                'message': 'Training complete!',
                'final_loss': 0.05
            })

        # Run in background
        thread = threading.Thread(target=train_in_thread)
        thread.daemon = True
        thread.start()

    # ==============================================================================
    # CRINGEPROOF MULTIPLAYER ROOMS
    # ==============================================================================

    @socketio.on('join_cringeproof_room')
    def handle_join_cringeproof_room(data):
        """
        Player joins a cringeproof multiplayer room

        Args:
            data: {
                'room_code': 'GAME-ABC123',
                'username': 'player_name'
            }
        """
        room_code = data.get('room_code')
        username = data.get('username', 'Anonymous')

        if not room_code:
            emit('error', {'message': 'Missing room_code'})
            return

        # Join the room
        join_room(room_code)

        print(f"🎮 {username} joined cringeproof room: {room_code}")

        # Notify the user who joined
        emit('joined_room', {
            'room_code': room_code,
            'message': f'You joined room {room_code}'
        })

        # Notify all other players in the room
        emit('player_joined', {
            'username': username,
            'room_code': room_code,
            'timestamp': datetime.now().isoformat()
        }, room=room_code, include_self=False)

    @socketio.on('leave_cringeproof_room')
    def handle_leave_cringeproof_room(data):
        """
        Player leaves a cringeproof room

        Args:
            data: {
                'room_code': 'GAME-ABC123',
                'username': 'player_name'
            }
        """
        room_code = data.get('room_code')
        username = data.get('username', 'Anonymous')

        if not room_code:
            return

        # Leave the room
        leave_room(room_code)

        print(f"🎮 {username} left cringeproof room: {room_code}")

        # Notify all players in the room
        emit('player_left', {
            'username': username,
            'room_code': room_code,
            'timestamp': datetime.now().isoformat()
        }, room=room_code)

    @socketio.on('send_room_message')
    def handle_send_room_message(data):
        """
        Send chat message to cringeproof room

        Args:
            data: {
                'room_code': 'GAME-ABC123',
                'username': 'player_name',
                'message': 'Hello everyone!'
            }
        """
        room_code = data.get('room_code')
        username = data.get('username', 'Anonymous')
        message = data.get('message', '')

        if not room_code or not message:
            emit('error', {'message': 'Missing room_code or message'})
            return

        print(f"💬 {username} in {room_code}: {message}")

        # Broadcast message to all players in room
        emit('room_message', {
            'username': username,
            'message': message,
            'room_code': room_code,
            'timestamp': datetime.now().isoformat()
        }, room=room_code, broadcast=True)

    @socketio.on('share_game_result')
    def handle_share_game_result(data):
        """
        Player shares their cringeproof game result with the room

        Args:
            data: {
                'room_code': 'GAME-ABC123',
                'username': 'player_name',
                'score': 75,
                'archetype': 'Imposter Syndrome'
            }
        """
        room_code = data.get('room_code')
        username = data.get('username', 'Anonymous')
        score = data.get('score', 0)
        archetype = data.get('archetype')

        if not room_code:
            emit('error', {'message': 'Missing room_code'})
            return

        print(f"📊 {username} shared result in {room_code}: {score}% ({archetype})")

        # Broadcast result to all players in room
        emit('game_result_shared', {
            'username': username,
            'score': score,
            'archetype': archetype,
            'room_code': room_code,
            'timestamp': datetime.now().isoformat()
        }, room=room_code, broadcast=True)

    return socketio


# ==============================================================================
# EXAMPLE FLASK APP
# ==============================================================================

def create_app():
    """Create example Flask app with WebSockets"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'

    # Setup subdomain routing (existing code)
    from subdomain_router import setup_subdomain_routing
    setup_subdomain_routing(app)

    # Add WebSocket support
    socketio = setup_websockets(app)

    # ==============================================================================
    # ROUTES
    # ==============================================================================

    @app.route('/')
    def index():
        """Homepage with WebSocket demo"""
        return render_template('index_websocket.html',
                             active_brand=g.get('active_brand'),
                             brand_css=g.get('brand_css', ''))

    @app.route('/concept-map')
    def concept_map():
        """Interactive concept map"""
        return render_template('concept_map.html')

    @app.route('/admin/dashboard')
    def admin_dashboard():
        """Admin dashboard with live updates"""
        return render_template('admin_dashboard_live.html')

    return app, socketio


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def broadcast_brand_update(brand_slug, changes):
    """
    Helper to broadcast brand updates from anywhere in code

    Usage:
        from websocket_server import broadcast_brand_update

        # After updating brand in database
        broadcast_brand_update('ocean-dreams', {
            'colors': ['#003366', '#0066cc']
        })
    """
    from flask_socketio import SocketIO
    socketio = SocketIO()

    socketio.emit('brand_refresh', {
        'brand_slug': brand_slug,
        'changes': changes,
        'timestamp': datetime.now().isoformat()
    }, room=f"brand:{brand_slug}", namespace='/')


def broadcast_subscription(brand_slug, email):
    """Helper to broadcast new subscription"""
    from flask_socketio import SocketIO
    socketio = SocketIO()

    db = get_db()
    count = db.execute('''
        SELECT COUNT(*) as count FROM subscribers
        WHERE brand_id = (SELECT id FROM brands WHERE slug = ?)
        AND active = 1
    ''', (brand_slug,)).fetchone()['count']
    db.close()

    socketio.emit('subscriber_count_update', {
        'brand_slug': brand_slug,
        'count': count,
        'latest_subscriber': email
    }, room='admin', namespace='/')


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import sys

    print()
    print("=" * 70)
    print("  🚀 Soulfra WebSocket Server")
    print("=" * 70)
    print()
    print("Starting Flask app with WebSocket support...")
    print()
    print("Features:")
    print("  • Live brand updates (colors change without refresh)")
    print("  • Real-time subscription counts")
    print("  • Interactive concept map")
    print("  • Collaborative editing indicators")
    print()
    print("Connect from browser:")
    print("  <script src=\"https://cdn.socket.io/4.0.0/socket.io.min.js\"></script>")
    print("  <script>")
    print("    const socket = io();")
    print("    socket.on('connected', (data) => console.log(data));")
    print("  </script>")
    print()
    print("=" * 70)
    print()

    app, socketio = create_app()

    # Run with WebSocket support
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True  # For development only!
    )

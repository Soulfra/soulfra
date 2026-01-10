#!/usr/bin/env python3
"""
Soulfra Dev Mode v2 - Smart Solo Development
NO libraries - Pure Python stdlib only (Bun/Zig/pot philosophy)

Problem: Email network is for multiplayer, but you're doing SOLO development
Solution: Minimal startup with just Ollama + SQLite + Flask + Auto-auth

What this does:
- Starts Flask server on port 5001
- Uses Ollama for AI processing
- SQLite for database
- Auto-authenticates your terminal (no login needed)
- Shows what's ACTUALLY loaded from 18,843-line app.py
- NO email network
- NO mesh network
- NO blamechain

New in v2:
- Terminal auto-auth (~/.soulfra_dev_token)
- Live stats on active routes/templates
- Port conflict detection
- Nested folder warnings

Usage:
    python3 dev_mode.py

Features available in dev mode:
- Customer discovery chat (Ollama AI)
- Content generation (Ollama)
- Database storage (SQLite)
- GitHub OAuth / API keys
- All 367 Flask routes
- 138 active templates

Features NOT available (multiplayer only):
- Email notifications
- Mesh network sync
- Blamechain tracking
- Multi-user collaboration
"""

import os
import sys
import json
import secrets
import socket
from pathlib import Path

# ==============================================================================
# AUTO-AUTH TOKEN MANAGEMENT
# ==============================================================================

def get_or_create_dev_token():
    """Get or create terminal auto-auth token"""
    token_file = Path.home() / '.soulfra_dev_token'

    if token_file.exists():
        with open(token_file, 'r') as f:
            data = json.load(f)
            return data['token']

    # Create new token
    token = secrets.token_urlsafe(32)

    with open(token_file, 'w') as f:
        json.dump({
            'token': token,
            'created_at': str(Path.ctime(Path(__file__))),
            'machine': socket.gethostname()
        }, f, indent=2)

    # Secure the file
    token_file.chmod(0o600)

    return token


# ==============================================================================
# PORT CONFLICT DETECTION
# ==============================================================================

def check_port_available(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except OSError:
        return False


# ==============================================================================
# STARTUP DIAGNOSTICS
# ==============================================================================

def show_startup_diagnostics():
    """Show what's actually loaded"""

    print("=" * 70)
    print("🔧 SOULFRA DEV MODE v2 (Smart Solo Development)")
    print("=" * 70)
    print()

    # Auto-auth
    token = get_or_create_dev_token()
    print(f"🔐 Auto-auth: ~/.soulfra_dev_token")
    print(f"   Token: {token[:16]}...")
    print()

    # Port check
    port = 5001
    if not check_port_available(port):
        print(f"⚠️  WARNING: Port {port} already in use!")
        print(f"   Kill existing process: lsof -ti:{port} | xargs kill -9")
        print()

    # Load analysis data
    try:
        with open('active_routes.json', 'r') as f:
            routes = json.load(f)
        with open('active_templates.json', 'r') as f:
            templates = json.load(f)
        with open('active_imports.json', 'r') as f:
            imports = json.load(f)

        print("📊 Active Components:")
        print(f"   Routes: {len(routes)}")
        print(f"   Templates: {len(templates)}")
        print(f"   Imported modules: {len(imports)}")
        print()

    except FileNotFoundError:
        print("⚠️  Analysis data not found - run: python3 analyze_app_structure.py")
        print()

    # Features
    print("✅ Enabled:")
    print("   - Ollama AI")
    print("   - SQLite Database")
    print("   - Flask Server (367 routes)")
    print("   - GitHub OAuth")
    print("   - Terminal Auto-Auth")
    print()

    print("❌ Disabled (multiplayer only):")
    print("   - Email Network")
    print("   - Mesh Network")
    print("   - Blamechain")
    print()

    # Nested folder warning
    if os.path.exists('Soulfra'):
        print("⚠️  NESTED FOLDERS DETECTED:")
        print("   Soulfra/ folder exists (triple-domain system)")
        print("   This is SEPARATE from main app.py")
        print("   Main app: port 5001")
        print("   Nested Soulfra: ports 8001/5002/5003")
        print()

    print("=" * 70)
    print()


# ==============================================================================
# MAIN
# ==============================================================================

# Set environment variables
os.environ['SOULFRA_DEV_MODE'] = '1'
os.environ['SKIP_EMAIL'] = '1'
os.environ['SOULFRA_DEV_TOKEN'] = get_or_create_dev_token()

show_startup_diagnostics()

# Check if app.py exists
if not os.path.exists('app.py'):
    print("❌ ERROR: app.py not found")
    print("   Make sure you're in the soulfra-simple directory")
    sys.exit(1)

# Import and start Flask app
try:
    print("🚀 Starting Flask server...")
    print("   http://localhost:5001")
    print()

    # Import main app
    from app import app

    # Run in dev mode
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False  # Prevent double startup
    )

except ImportError as e:
    print(f"❌ Import error: {e}")
    print()
    print("This might be because some modules expect the old structure.")
    print("Try running the original app.py instead:")
    print("   python3 app.py")
    sys.exit(1)

except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

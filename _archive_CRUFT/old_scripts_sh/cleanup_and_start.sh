#!/usr/bin/env bash
# Nuclear cleanup and fresh start for Flask server
# Kills ALL Python processes, clears port 5001, starts single instance

set -e

echo "🧹 NUCLEAR CLEANUP - Killing everything related to Flask/Python on port 5001"
echo ""

# Step 1: Kill ALL Python processes running app.py or preview_server.py
echo "🔪 Step 1: Killing all Python app.py processes..."
pkill -9 -f "python3 app.py" 2>/dev/null || true
pkill -9 -f "python3 preview_server.py" 2>/dev/null || true
sleep 1

# Step 2: Kill anything on port 5001 (belt and suspenders)
echo "🔪 Step 2: Killing anything on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 1

# Step 3: Triple-check port is free
echo "🔍 Step 3: Verifying port 5001 is free..."
PORT_CHECK=$(lsof -i :5001 2>/dev/null | grep LISTEN || echo "")
if [ -n "$PORT_CHECK" ]; then
    echo "❌ ERROR: Port 5001 still in use!"
    echo "$PORT_CHECK"
    echo ""
    echo "Manual cleanup needed: sudo lsof -ti:5001 | xargs sudo kill -9"
    exit 1
fi
echo "✅ Port 5001 is free"
echo ""

# Step 4: Wait for OS to fully release port
echo "⏳ Waiting 3 seconds for OS to release port..."
sleep 3

# Step 5: Start Flask with timeout (2 hours = 7200 seconds)
echo "🚀 Starting Flask server (2 hour timeout)..."
echo ""
echo "URLs:"
echo "  📍 Customer Discovery: http://localhost:5001/customer-discovery-chat.html"
echo "  📍 Email Chat:         http://localhost:5001/email-ollama-chat.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Use timeout command (macOS has gtimeout via brew install coreutils, fallback to no timeout)
if command -v gtimeout &> /dev/null; then
    gtimeout 7200 python3 app.py
else
    echo "⚠️  Note: 'gtimeout' not found, running without timeout (install with: brew install coreutils)"
    python3 app.py
fi

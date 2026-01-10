#!/bin/bash
# CringeProof Startup Script
# Starts all required services without port conflicts

echo "🚀 Starting CringeProof Services..."

# Kill any existing processes on ports
echo "🧹 Cleaning up existing processes..."
lsof -ti :5001 | xargs kill -9 2>/dev/null || true
lsof -ti :8888 | xargs kill -9 2>/dev/null || true
sleep 2

# Start IPFS daemon (if not running)
if ! lsof -i :5002 > /dev/null 2>&1; then
    echo "📡 Starting IPFS daemon..."
    ipfs daemon > /tmp/ipfs.log 2>&1 &
    sleep 3
else
    echo "✅ IPFS already running"
fi

# Start Flask app
echo "🐍 Starting Flask (CringeProof API)..."
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py > /tmp/flask.log 2>&1 &
sleep 5

# Start Mesh Router
echo "🔀 Starting Mesh Router..."
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.github.io/Founder-Bootstrap/Blank-Kernel/SOULFRA-CONSOLIDATED-2025/misc
node mesh-router.js > /tmp/mesh-router.log 2>&1 &
sleep 2

# Verify services
echo ""
echo "🔍 Verifying services..."
lsof -i :5001 > /dev/null 2>&1 && echo "✅ Flask running on port 5001" || echo "❌ Flask NOT running"
lsof -i :8888 > /dev/null 2>&1 && echo "✅ Mesh Router running on port 8888" || echo "❌ Mesh Router NOT running"
lsof -i :5002 > /dev/null 2>&1 && echo "✅ IPFS running on port 5002" || echo "❌ IPFS NOT running"

echo ""
echo "📍 Service URLs:"
echo "   Mesh Entry: http://localhost:8888/mesh-entry.html"
echo "   Voice Wall (via mesh): http://localhost:8888/vault"
echo "   Voice Wall (direct): https://localhost:5001/wall.html"
echo "   GitHub OAuth Status: http://localhost:5001/github/status"
echo "   IPFS Gateway: http://localhost:8080"
echo ""
echo "✅ CringeProof is running!"

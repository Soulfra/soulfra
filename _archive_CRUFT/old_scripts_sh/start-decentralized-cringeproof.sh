#!/bin/bash

#################################################################
# 🚫 CringeProof Decentralized Startup Script
#
# Starts the complete P2P mesh network stack:
# - Flask (port 5001) - Voice recording + Wall API
# - IPFS daemon (port 5002 API, 8080 Gateway)
# - Mesh Router (port 8888) - P2P routing with QR auth
# - Mesh-Flask Bridge - Database sync to mesh network
#
# NO CLOUDFLARE. NO CENTRALIZED BULLSHIT.
# Just peer-to-peer audio, Bitcoin-style.
#################################################################

set -e

WORKING_DIR="/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple"
MESH_DIR="$WORKING_DIR/soulfra.github.io/Founder-Bootstrap/Blank-Kernel/SOULFRA-CONSOLIDATED-2025/misc"

cd "$WORKING_DIR"

# Run preflight check first (like game launchers)
echo "🎮 Running pre-flight dependency check..."
if ! ./preflight-check.sh; then
    echo ""
    echo "❌ Pre-flight check failed - cannot start"
    echo "   Fix errors above and try again"
    exit 1
fi

echo ""
echo "🚫 Starting CringeProof Decentralized Stack"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill existing processes
echo ""
echo "🧹 Cleaning up old processes..."
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "ipfs daemon" 2>/dev/null || true
pkill -f "mesh-router.js" 2>/dev/null || true
pkill -f "mesh_flask_bridge.py" 2>/dev/null || true
sleep 2

# Start IPFS daemon (port 5002 API, 8080 Gateway)
echo ""
echo "📡 Starting IPFS daemon..."
echo "   API: http://localhost:5002"
echo "   Gateway: http://localhost:8080"
ipfs daemon > /tmp/ipfs-daemon.log 2>&1 &
IPFS_PID=$!
sleep 3

# Verify IPFS started
if curl -s -X POST http://localhost:5002/api/v0/id > /dev/null 2>&1; then
    echo "   ✅ IPFS daemon running (PID: $IPFS_PID)"
else
    echo "   ❌ IPFS daemon failed to start"
    exit 1
fi

# Start Flask (port 5001 HTTPS)
echo ""
echo "🎤 Starting Flask voice server..."
echo "   URL: https://192.168.1.87:5001"
echo "   Pages:"
echo "     - https://192.168.1.87:5001/           (Homepage)"
echo "     - https://192.168.1.87:5001/wall.html  (Voice Wall)"
echo "     - https://192.168.1.87:5001/record-simple.html"
python3 app.py > /tmp/flask.log 2>&1 &
FLASK_PID=$!
sleep 3

# Verify Flask started
if curl -k -s https://localhost:5001/api/wall/feed?domain=cringeproof.com > /dev/null 2>&1; then
    echo "   ✅ Flask running (PID: $FLASK_PID)"
else
    echo "   ❌ Flask failed to start"
    exit 1
fi

# Start Mesh Router (port 8888)
echo ""
echo "🔮 Starting Mesh Router..."
echo "   URL: http://localhost:8888"
echo "   Interface: http://localhost:8888/mesh-entry.html"
cd "$MESH_DIR"
node mesh-router.js > /tmp/mesh-router.log 2>&1 &
MESH_PID=$!
cd "$WORKING_DIR"
sleep 2

# Verify Mesh Router started
if curl -s http://localhost:8888/mesh-entry.html > /dev/null 2>&1; then
    echo "   ✅ Mesh Router running (PID: $MESH_PID)"
else
    echo "   ⚠️  Mesh Router may not be ready yet"
fi

# Start Mesh-Flask Bridge
echo ""
echo "🌉 Starting Mesh-Flask Bridge..."
echo "   Syncs database to P2P network every 10s"
python3 mesh_flask_bridge.py heartbeat > /tmp/mesh-bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 1

if ps -p $BRIDGE_PID > /dev/null; then
    echo "   ✅ Mesh Bridge running (PID: $BRIDGE_PID)"
else
    echo "   ⚠️  Mesh Bridge may have issues"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CringeProof Decentralized Stack Running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Process IDs:"
echo "   IPFS:        $IPFS_PID"
echo "   Flask:       $FLASK_PID"
echo "   Mesh Router: $MESH_PID"
echo "   Mesh Bridge: $BRIDGE_PID"
echo ""
echo "🌐 Access Points:"
echo ""
echo "   LOCAL:"
echo "   - Voice Archive: https://localhost:5001/"
echo "   - Voice Wall:    https://localhost:5001/wall.html"
echo "   - Record:        https://localhost:5001/record-simple.html"
echo "   - Mesh Entry:    http://localhost:8888/mesh-entry.html"
echo ""
echo "   LAN (Share with friends on WiFi):"
echo "   - Voice Archive: https://192.168.1.87:5001/"
echo "   - Voice Wall:    https://192.168.1.87:5001/wall.html"
echo "   - Record:        https://192.168.1.87:5001/record-simple.html"
echo ""
echo "   IPFS Gateway:"
echo "   - Local:  http://localhost:8080/ipfs/<hash>"
echo "   - Public: https://ipfs.io/ipfs/<hash>"
echo ""
echo "📋 Logs:"
echo "   tail -f /tmp/flask.log"
echo "   tail -f /tmp/ipfs-daemon.log"
echo "   tail -f /tmp/mesh-router.log"
echo "   tail -f /tmp/mesh-bridge.log"
echo ""
echo "🛑 To stop all:"
echo "   pkill -f 'python3 app.py'"
echo "   pkill -f 'ipfs daemon'"
echo "   pkill -f 'mesh-router.js'"
echo "   pkill -f 'mesh_flask_bridge.py'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎂 Built on Bitcoin's Birthday 2026"
echo "   In the spirit of decentralization."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

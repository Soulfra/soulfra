#!/bin/bash

echo "========================================================================"
echo "🔄 Restarting Flask Server"
echo "========================================================================"
echo ""

# Kill existing Flask processes
echo "Stopping existing Flask processes..."
pkill -9 -f "python3 app.py" 2>/dev/null || echo "No existing processes"
sleep 2

# Navigate to directory
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Start Flask
echo "Starting Flask on port 5001..."
python3 app.py > flask-server.log 2>&1 &
FLASK_PID=$!

echo "Flask started (PID: $FLASK_PID)"
echo "Logs: flask-server.log"
echo ""

# Wait for startup
echo "Waiting for server to start..."
sleep 5

# Test
echo "Testing dashboard..."
curl -I http://localhost:5001/dashboard 2>&1 | head -5

echo ""
echo "========================================================================"
echo "✅ Flask Server Running"
echo "========================================================================"
echo ""
echo "Access from iPhone:"
echo "  http://192.168.1.87:5001/dashboard"
echo ""
echo "Access from laptop:"
echo "  http://localhost:5001/dashboard"
echo ""
echo "View logs:"
echo "  tail -f flask-server.log"
echo ""
echo "========================================================================"

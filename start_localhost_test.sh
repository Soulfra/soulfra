#!/usr/bin/env bash
# Start localhost test server for customer discovery tool

echo "🚀 Starting localhost test server for Customer Discovery Tool"
echo ""
echo "This will:"
echo "  1. Start Flask on port 5001"
echo "  2. Serve customer-discovery-chat.html locally"
echo "  3. Allow you to test IMMEDIATELY while waiting for soulfra.com cache to clear"
echo ""
echo "URLs:"
echo "  📍 Customer Discovery: http://localhost:5001/customer-discovery-chat.html"
echo "  📍 Email Chat:         http://localhost:5001/email-ollama-chat.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Kill any existing Flask processes on port 5001
echo "🔪 Killing existing processes on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Wait a moment for port to free up
sleep 2

# Start Flask
echo "🔧 Starting Flask server..."
python3 app.py

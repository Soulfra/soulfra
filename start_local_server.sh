#!/bin/bash
# Simple HTTP Server - No Flask Dependencies
# Usage: ./start_local_server.sh

PORT=8080

echo "🚀 Starting local HTTP server..."
echo "📍 URL: http://localhost:$PORT"
echo "🎤 Voice input: http://localhost:$PORT/voice-input.html"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Use Python's built-in HTTP server
python3 -m http.server $PORT

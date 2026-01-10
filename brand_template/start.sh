#!/bin/bash
#
# Start Brand - Launch your branded Ollama chat with LAN access
#
# This script starts a simple HTTP server for your brand folder
# and makes it accessible from other devices on your network.
#
# Usage:
#   chmod +x start.sh
#   ./start.sh
#

echo "=================================================="
echo "🚀 Starting Your Brand Chat"
echo "=================================================="
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  WARNING: Ollama is not running!"
    echo ""
    echo "Please start Ollama in another terminal:"
    echo "  ollama serve"
    echo ""
    echo "Or run with LAN access:"
    echo "  OLLAMA_HOST=0.0.0.0:11434 ollama serve"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Get local IP address
if command -v ipconfig &> /dev/null; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
elif command -v hostname &> /dev/null; then
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}' || echo "localhost")
else
    LOCAL_IP="localhost"
fi

PORT=8080

echo "📍 Your local IP: $LOCAL_IP"
echo ""
echo "Your brand will be accessible at:"
echo "  - http://localhost:$PORT (from this computer)"
echo "  - http://$LOCAL_IP:$PORT (from phone/other devices)"
echo ""
echo "Make sure your phone is on the SAME WiFi network!"
echo ""
echo "Starting server..."
echo ""

# Start simple HTTP server
if command -v python3 &> /dev/null; then
    # Python 3
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    # Python 2
    python -m SimpleHTTPServer $PORT
else
    echo "❌ ERROR: Python not found!"
    echo ""
    echo "Install Python or use a different web server."
    echo ""
    echo "Alternative: Just double-click index.html (localhost only)"
    exit 1
fi

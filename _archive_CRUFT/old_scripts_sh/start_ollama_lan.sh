#!/bin/bash
#
# Start Ollama LAN - Make Ollama accessible from phone/other devices
#
# This script starts Ollama bound to all network interfaces (0.0.0.0),
# making it accessible from other devices on the same WiFi network.
#
# Usage:
#   chmod +x start_ollama_lan.sh
#   ./start_ollama_lan.sh
#

echo "=================================================="
echo "🚀 Starting Ollama for LAN Access"
echo "=================================================="
echo ""

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

echo "📍 Your local IP: $LOCAL_IP"
echo ""
echo "Ollama will be accessible at:"
echo "  - http://localhost:11434 (from this computer)"
echo "  - http://$LOCAL_IP:11434 (from phone/other devices)"
echo ""
echo "⚠️  Make sure your firewall allows connections on port 11434"
echo ""
echo "Starting Ollama..."
echo ""

# Set environment variable to bind to all interfaces
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama server
ollama serve

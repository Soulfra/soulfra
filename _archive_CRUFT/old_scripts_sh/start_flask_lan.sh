#!/bin/bash
#
# Start Flask LAN - Make Flask app accessible from phone with Ollama integration
#
# This script starts Flask with the correct environment variables
# so it can communicate with Ollama on the LAN.
#
# IMPORTANT: Run ./start_ollama_lan.sh FIRST in a separate terminal!
#
# Usage:
#   chmod +x start_flask_lan.sh
#   ./start_flask_lan.sh
#

echo "=================================================="
echo "🚀 Starting Flask for LAN Access"
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
echo "Flask will be accessible at:"
echo "  - http://localhost:5001 (from this computer)"
echo "  - http://$LOCAL_IP:5001 (from phone/other devices)"
echo ""
echo "Chat will connect to Ollama at:"
echo "  - http://$LOCAL_IP:11434"
echo ""
echo "⚠️  Make sure you ran ./start_ollama_lan.sh FIRST!"
echo "⚠️  Make sure your firewall allows connections on ports 5001 and 11434"
echo ""

# Export Ollama host for phone access
export OLLAMA_HOST=http://$LOCAL_IP:11434

# Start Flask
echo "Starting Flask..."
echo ""
python3 app.py

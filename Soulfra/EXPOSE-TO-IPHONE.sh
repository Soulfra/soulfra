#!/bin/bash

# EXPOSE-TO-IPHONE.sh - Get URLs for iPhone testing
# Usage: bash EXPOSE-TO-IPHONE.sh

echo "========================================================================"
echo "📱 Expose Soulfra to iPhone"
echo "========================================================================"
echo ""

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$LOCAL_IP" ]; then
    echo "❌ Could not detect local IP address"
    echo "   Find it manually with: ifconfig | grep 'inet '"
    exit 1
fi

echo "Local IP: $LOCAL_IP"
echo ""
echo "========================================================================"
echo "Option 1: Same WiFi Network (Simplest)"
echo "========================================================================"
echo ""
echo "Make sure your laptop and iPhone are on the same WiFi network."
echo ""
echo "URLs for iPhone:"
echo "  soulfra.com:    http://$LOCAL_IP:8001"
echo "  soulfraapi.com: http://$LOCAL_IP:5002"
echo "  soulfra.ai:     http://$LOCAL_IP:5003"
echo ""
echo "QR code on landing page will point to:"
echo "  http://$LOCAL_IP:5002/qr-signup"
echo ""
echo "To update QR code with local IP:"
echo "  1. Edit generate-qr.py"
echo "  2. Change LOCALHOST_URL to: http://$LOCAL_IP:5002/qr-signup?ref=landing"
echo "  3. Run: python3 generate-qr.py"
echo ""
echo "========================================================================"
echo "Option 2: ngrok (Works from Anywhere)"
echo "========================================================================"
echo ""
echo "ngrok creates public URLs that work from any network."
echo ""
echo "Install ngrok:"
echo "  brew install ngrok"
echo ""
echo "Expose soulfraapi.com:"
echo "  ngrok http 5002"
echo "  # Gives you: https://abc123.ngrok.io"
echo ""
echo "Update QR code:"
echo "  1. Copy the ngrok URL"
echo "  2. Edit generate-qr.py"
echo "  3. Change LOCALHOST_URL to: https://abc123.ngrok.io/qr-signup?ref=landing"
echo "  4. Run: python3 generate-qr.py"
echo ""
echo "Then expose soulfra.ai (in another terminal):"
echo "  ngrok http 5003"
echo "  # Gives you: https://xyz789.ngrok.io"
echo ""
echo "Update soulfraapi.com redirect:"
echo "  export SOULFRA_AI_URL=https://xyz789.ngrok.io"
echo "  python3 Soulfraapi.com/app.py"
echo ""
echo "========================================================================"
echo "Current Service Status"
echo "========================================================================"
echo ""

# Check if services are running
if curl -s http://localhost:8001 > /dev/null; then
    echo "✅ soulfra.com is running"
else
    echo "❌ soulfra.com is NOT running"
fi

if curl -s http://localhost:5002/health > /dev/null; then
    echo "✅ soulfraapi.com is running"
else
    echo "❌ soulfraapi.com is NOT running"
fi

if curl -s http://localhost:5003/health > /dev/null; then
    echo "✅ soulfra.ai is running"
else
    echo "❌ soulfra.ai is NOT running"
fi

echo ""
echo "If services are not running: bash START-ALL.sh"
echo "========================================================================"

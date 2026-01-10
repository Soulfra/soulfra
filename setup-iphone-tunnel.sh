#!/bin/bash
# Setup Tailscale Funnel for iPhone deployment
# Run this once to get a permanent URL for your Flask backend

echo "🚀 Setting up Tailscale Funnel for iPhone deployment..."
echo ""

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo "📦 Installing Tailscale..."
    brew install tailscale
fi

# Start Tailscale
echo "🔗 Connecting to Tailscale..."
sudo tailscale up

# Get your machine name
MACHINE_NAME=$(tailscale status --json | grep -o '"HostName":"[^"]*' | cut -d'"' -f4)

# Start funnel
echo "🌐 Starting Tailscale Funnel..."
tailscale funnel --bg --https=443 https://localhost:5001

# Get your URL
YOUR_URL="https://${MACHINE_NAME}.tailscale-funnel.com"

echo ""
echo "✅ Tailscale Funnel is running!"
echo ""
echo "Your permanent URL:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$YOUR_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Open this URL on your iPhone to test mobile.html"
echo ""
echo "Next steps:"
echo "1. Make sure Flask is running (python app.py)"
echo "2. Open $YOUR_URL/mobile.html on iPhone"
echo "3. Test voice recording and shadow account"
echo ""

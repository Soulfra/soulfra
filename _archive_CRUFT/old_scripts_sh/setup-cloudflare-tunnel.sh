#!/bin/bash
# Cloudflare Tunnel Setup Script
# Connects soulfra.com to local Flask server (localhost:5001)

set -e  # Exit on error

echo "🌐 Cloudflare Tunnel Setup for soulfra.com"
echo "=========================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found"
    echo "Install with: brew install cloudflared"
    exit 1
fi

echo "✅ cloudflared found: $(which cloudflared)"
echo ""

# Check if Flask server is running
echo "🔍 Checking if Flask server is running on localhost:5001..."
if curl -k -s https://localhost:5001/status > /dev/null 2>&1; then
    echo "✅ Flask server is running"
elif curl -k -s https://localhost:5001 > /dev/null 2>&1; then
    echo "✅ Flask server is running"
else
    echo "⚠️  Flask server doesn't appear to be running"
    echo "   Start it with: python3 app.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📋 Next Steps (Manual):"
echo "======================"
echo ""
echo "1️⃣  Login to Cloudflare:"
echo "   cloudflared tunnel login"
echo ""
echo "2️⃣  Create tunnel:"
echo "   cloudflared tunnel create soulfra"
echo ""
echo "3️⃣  Copy the Tunnel ID from the output above, then create config:"
echo "   mkdir -p ~/.cloudflared"
echo "   nano ~/.cloudflared/config.yml"
echo ""
echo "   Paste this (replace TUNNEL_ID with your actual ID):"
echo ""
cat << 'EOF'
tunnel: YOUR_TUNNEL_ID_HERE
credentials-file: /Users/matthewmauer/.cloudflared/YOUR_TUNNEL_ID_HERE.json

ingress:
  - hostname: soulfra.com
    service: https://localhost:5001
    originRequest:
      noTLSVerify: true
  - hostname: www.soulfra.com
    service: https://localhost:5001
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF
echo ""
echo "4️⃣  Route DNS:"
echo "   cloudflared tunnel route dns soulfra soulfra.com"
echo "   cloudflared tunnel route dns soulfra www.soulfra.com"
echo ""
echo "5️⃣  Start tunnel:"
echo "   cloudflared tunnel run soulfra"
echo ""
echo "6️⃣  Test:"
echo "   Open https://soulfra.com in your browser"
echo "   Should load your Flask app!"
echo ""
echo "📖 Full guide: CLOUDFLARE_TUNNEL_SETUP.md"
echo ""

# Offer to open documentation
read -p "Open full setup guide? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open CLOUDFLARE_TUNNEL_SETUP.md
    else
        echo "📄 See: CLOUDFLARE_TUNNEL_SETUP.md"
    fi
fi

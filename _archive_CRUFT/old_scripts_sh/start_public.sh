#!/bin/bash
#
# Soulfra Public Startup Script
# Exposes Flask app to the internet via ngrok
#

echo "🚀 Starting Soulfra Public Access..."
echo ""

# Check if Flask is running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Flask is already running on port 5001"
else
    echo "⚠️  Flask is NOT running. Starting it now..."
    python3 app.py > /tmp/flask.log 2>&1 &
    sleep 3
    echo "✅ Flask started"
fi

echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null ; then
    echo "❌ ngrok is not installed"
    echo ""
    echo "Install with: brew install ngrok"
    echo "Then run this script again"
    exit 1
fi

# Kill any existing ngrok
pkill -9 ngrok 2>/dev/null
sleep 1

echo "🌐 Starting ngrok tunnel..."
ngrok http 5001 > /tmp/ngrok.log 2>&1 &

# Wait for ngrok to start
sleep 5

# Get public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('tunnels'):
        print(data['tunnels'][0]['public_url'])
    else:
        print('ERROR')
except:
    print('ERROR')
" 2>/dev/null)

if [ "$PUBLIC_URL" = "ERROR" ] || [ -z "$PUBLIC_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    echo ""
    echo "Manually run: ngrok http 5001"
    echo "Then visit http://localhost:4040 to see the URL"
    exit 1
fi

echo ""
echo "✅ Soulfra is now PUBLIC!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Access from anywhere:"
echo "   $PUBLIC_URL"
echo ""
echo "🎯 Try these URLs:"
echo "   $PUBLIC_URL/voice"
echo "   $PUBLIC_URL/debug-quests"
echo "   $PUBLIC_URL/domains"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 ngrok dashboard: http://localhost:4040"
echo "📊 Flask logs: tail -f /tmp/flask.log"
echo ""
echo "⚠️  NOTE: Free ngrok URL changes each restart!"
echo "    Upgrade to ngrok paid for static domain."
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Keep script running
tail -f /tmp/ngrok.log

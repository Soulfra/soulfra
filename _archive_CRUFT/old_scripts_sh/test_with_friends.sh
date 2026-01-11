#!/bin/bash
# Test with Friends - One-Command Launcher
#
# Starts everything needed for localhost/LAN testing:
# - Flask app on LAN IP
# - Ollama local AI
# - Generates test QR codes
# - Shows shareable URLs
# - Monitors database scans

set -e

echo "🚀 Starting Soulfra - Friends & Family Testing"
echo "=" echo "="================================================================

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

if [ -z "$LOCAL_IP" ]; then
    echo "❌ Could not detect local IP address"
    echo "Please check your network connection"
    exit 1
fi

echo "✅ Local IP detected: $LOCAL_IP"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not installed (AI features won't work)"
    echo "Install: https://ollama.ai/download"
    echo ""
    echo "Continue without Ollama? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
    OLLAMA_RUNNING=false
else
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama already running"
        OLLAMA_RUNNING=true
    else
        echo "🤖 Starting Ollama..."
        ollama serve > /tmp/ollama.log 2>&1 &
        OLLAMA_PID=$!
        echo "   PID: $OLLAMA_PID"

        # Wait for Ollama to start
        echo "   Waiting for Ollama to start..."
        for i in {1..10}; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                echo "   ✅ Ollama started"
                OLLAMA_RUNNING=true
                break
            fi
            sleep 1
        done

        if [ "$OLLAMA_RUNNING" != "true" ]; then
            echo "   ⚠️  Ollama failed to start (check /tmp/ollama.log)"
            OLLAMA_RUNNING=false
        fi
    fi
fi

# Check if Flask is already running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Flask already running on port 5001"
    echo "Stop existing Flask? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        pkill -f "python3 app.py" || true
        sleep 2
    else
        echo "Continuing with existing Flask instance..."
    fi
fi

# Start Flask in background
echo "🌐 Starting Flask on $LOCAL_IP:5001..."
python3 app.py > /tmp/flask.log 2>&1 &
FLASK_PID=$!
echo "   PID: $FLASK_PID"

# Wait for Flask to start
echo "   Waiting for Flask to start..."
for i in {1..10}; do
    if curl -s http://localhost:5001 > /dev/null 2>&1; then
        echo "   ✅ Flask started"
        break
    fi
    sleep 1
done

echo ""
echo "================================================================"
echo "✅ ALL SYSTEMS RUNNING"
echo "================================================================"
echo ""

# Generate test QR codes
echo "🔐 Generating test QR codes..."
echo ""

# Auth QR
AUTH_QR=$(python3 qr_faucet.py --generate --type auth --data '{"level": "basic"}' --ttl 7200 2>&1 | grep "URL:" | awk '{print $2}')
if [ -n "$AUTH_QR" ]; then
    echo "✅ Auth QR: $AUTH_QR"
else
    echo "⚠️  Failed to generate auth QR"
fi

# Blog QR
BLOG_QR=$(python3 qr_faucet.py --generate --type blog --data '{"topic": "testing"}' --ttl 7200 2>&1 | grep "URL:" | awk '{print $2}')
if [ -n "$BLOG_QR" ]; then
    echo "✅ Blog QR: $BLOG_QR"
else
    echo "⚠️  Failed to generate blog QR"
fi

echo ""
echo "================================================================"
echo "📱 SHARE THESE URLs WITH FRIENDS"
echo "================================================================"
echo ""

echo "🏠 Homepage:"
echo "   http://$LOCAL_IP:5001"
echo ""

echo "🎯 Cringeproof Quiz (Best for testing):"
echo "   http://$LOCAL_IP:5001/cringeproof"
echo ""

echo "🌟 Start Page (3 brand cards):"
echo "   http://$LOCAL_IP:5001/start"
echo ""

if [ -n "$AUTH_QR" ]; then
    echo "🔐 Auth QR (Signup/Login):"
    echo "   $AUTH_QR"
    echo ""
fi

echo "================================================================"
echo "📊 MONITORING"
echo "================================================================"
echo ""

echo "Watch database scans:"
echo "   watch -n 1 'sqlite3 soulfra.db \"SELECT COUNT(*) FROM qr_faucet_scans\"'"
echo ""

echo "Watch latest scan:"
echo "   watch -n 1 'sqlite3 soulfra.db \"SELECT ip_address, device_type, scanned_at FROM qr_faucet_scans ORDER BY scanned_at DESC LIMIT 1\"'"
echo ""

echo "Flask logs:"
echo "   tail -f /tmp/flask.log"
echo ""

if [ "$OLLAMA_RUNNING" = "true" ]; then
    echo "Ollama logs:"
    echo "   tail -f /tmp/ollama.log"
    echo ""
fi

echo "================================================================"
echo "🛑 TO STOP"
echo "================================================================"
echo ""

if [ -n "$FLASK_PID" ]; then
    echo "Flask: kill $FLASK_PID"
fi

if [ -n "$OLLAMA_PID" ]; then
    echo "Ollama: kill $OLLAMA_PID"
fi

echo "Or run: pkill -f 'python3 app.py' && pkill ollama"
echo ""

# Offer to watch scans live
echo "================================================================"
echo "👀 WATCH SCANS LIVE? (optional)"
echo "================================================================"
echo ""
echo "Watch database for incoming scans? (y/n)"
read -r response

if [ "$response" = "y" ]; then
    echo ""
    echo "Watching for scans... (Ctrl+C to stop)"
    echo ""

    # Display header
    echo "TIME                 | IP ADDRESS      | DEVICE  | FAUCET ID"
    echo "-----------------------------------------------------------------"

    # Watch database
    while true; do
        sqlite3 soulfra.db "SELECT
            datetime(scanned_at, 'localtime') as time,
            ip_address,
            device_type,
            faucet_id
        FROM qr_faucet_scans
        ORDER BY scanned_at DESC
        LIMIT 1" | awk -F'|' '{printf "%-20s | %-15s | %-7s | %s\n", $1, $2, $3, $4}'

        sleep 1
    done
else
    echo ""
    echo "✅ All systems running!"
    echo "Press Ctrl+C to stop monitoring, or close terminal to stop all services"
    echo ""

    # Keep script running
    wait
fi

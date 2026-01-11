#!/bin/bash
# Restart Flask - Kill duplicates and start fresh

echo "🔧 Cleaning up Flask processes..."

# Kill all python3 app.py processes
pkill -9 -f "python3 app.py" 2>/dev/null || true

# Wait for processes to die
sleep 2

# Check if port 5001 is free
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5001 still in use, forcing kill..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo "✅ Cleanup complete"
echo ""

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

echo "🚀 Starting Flask..."
python3 app.py &
FLASK_PID=$!

echo "   PID: $FLASK_PID"
echo "   Waiting for Flask to start..."

# Wait for Flask to start
for i in {1..10}; do
    if curl -s http://localhost:5001 > /dev/null 2>&1; then
        echo "   ✅ Flask started successfully"
        break
    fi
    sleep 1
done

echo ""
echo "================================================================"
echo "✅ Flask Running"
echo "================================================================"
echo ""
echo "🌐 URLs:"
echo "   Localhost: http://localhost:5001"
if [ "$LOCAL_IP" != "localhost" ]; then
    echo "   LAN:       http://$LOCAL_IP:5001"
    echo "   Friends:   http://$LOCAL_IP:5001/start"
fi
echo ""
echo "🎯 Test routes:"
echo "   /start                       - Entry page"
echo "   /cringeproof                 - Quiz (now works!)"
echo "   /cringeproof/narrative/soulfra - Direct quiz link"
echo "   /dashboard                   - Dashboard"
echo ""
echo "🛑 To stop:"
echo "   kill $FLASK_PID"
echo "   or run: pkill -f 'python3 app.py'"
echo ""

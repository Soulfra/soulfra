#!/usr/bin/env bash
# Check status of Flask server and port 5001
# Use this to debug what's running

echo "🔍 Flask Server Status Check"
echo "=============================="
echo ""

# Check if anything is listening on port 5001
echo "📡 Port 5001 Status:"
PORT_STATUS=$(lsof -i :5001 2>/dev/null | grep LISTEN || echo "")
if [ -n "$PORT_STATUS" ]; then
    echo "✅ Port 5001 is IN USE:"
    echo "$PORT_STATUS"
else
    echo "❌ Port 5001 is FREE (no server running)"
fi
echo ""

# Check all Python processes running app.py
echo "🐍 Python app.py Processes:"
APP_PROCESSES=$(ps aux | grep "python3 app.py" | grep -v grep || echo "")
if [ -n "$APP_PROCESSES" ]; then
    echo "$APP_PROCESSES"
    PROCESS_COUNT=$(echo "$APP_PROCESSES" | wc -l | tr -d ' ')
    echo ""
    if [ "$PROCESS_COUNT" -gt 1 ]; then
        echo "⚠️  WARNING: $PROCESS_COUNT processes found! Should only be 1."
    else
        echo "✅ Exactly 1 process (correct)"
    fi
else
    echo "❌ No app.py processes running"
fi
echo ""

# Check preview_server.py too
echo "🐍 Python preview_server.py Processes:"
PREVIEW_PROCESSES=$(ps aux | grep "python3 preview_server.py" | grep -v grep || echo "")
if [ -n "$PREVIEW_PROCESSES" ]; then
    echo "$PREVIEW_PROCESSES"
else
    echo "❌ No preview_server.py processes running"
fi
echo ""

# Test if localhost:5001 responds
echo "🌐 HTTP Test:"
HTTP_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/ 2>/dev/null || echo "FAIL")
if [ "$HTTP_TEST" = "200" ]; then
    echo "✅ http://localhost:5001/ returns HTTP 200"
elif [ "$HTTP_TEST" = "FAIL" ]; then
    echo "❌ http://localhost:5001/ is NOT reachable"
else
    echo "⚠️  http://localhost:5001/ returns HTTP $HTTP_TEST"
fi
echo ""

# Test customer discovery page
echo "🎯 Customer Discovery Page:"
CUSTOMER_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/customer-discovery-chat.html 2>/dev/null || echo "FAIL")
if [ "$CUSTOMER_TEST" = "200" ]; then
    echo "✅ http://localhost:5001/customer-discovery-chat.html returns HTTP 200"
elif [ "$CUSTOMER_TEST" = "FAIL" ]; then
    echo "❌ http://localhost:5001/customer-discovery-chat.html is NOT reachable"
else
    echo "⚠️  http://localhost:5001/customer-discovery-chat.html returns HTTP $CUSTOMER_TEST"
fi
echo ""

echo "=============================="
echo "Status check complete"

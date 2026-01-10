#!/bin/bash
# CLEAN-RESTART.sh - Clean Flask server restart script
# Kills all Flask instances and starts a fresh one with logging

echo "🔴 Stopping all Flask servers on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null && echo "✅ Killed all Flask processes" || echo "ℹ️  No Flask processes found"

echo "⏳ Waiting 2 seconds for cleanup..."
sleep 2

echo "🚀 Starting Flask server..."
echo "📝 Logs: flask.log (viewable in Ghost Mode)"
echo "🌐 Server: http://localhost:5001"
echo ""

# Start Flask in background with output to both terminal and log file
python3 app.py 2>&1 | tee -a flask.log &

FLASK_PID=$!
echo "✅ Flask server started (PID: $FLASK_PID)"
echo "📊 Ghost Mode: http://localhost:5001/ghost"
echo "📝 LOGS tab: Click 📝 LOGS in Ghost Mode to view server output"
echo ""
echo "To stop: kill $FLASK_PID"
echo "Or: lsof -ti:5001 | xargs kill -9"

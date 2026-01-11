#!/bin/bash

# Kill all Flask instances cleanly
echo "🛑 Killing all Flask instances..."
pkill -9 -f "python3 app.py"
pkill -9 -f "python app.py"

# Wait a moment
sleep 2

# Verify port 5001 is free
echo "🔍 Checking if port 5001 is free..."
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠️  Port 5001 still in use, force killing..."
    kill -9 $(lsof -ti:5001) 2>/dev/null
    sleep 1
fi

# Navigate to directory
cd "$(dirname "$0")"

# Start Flask cleanly
echo "🚀 Starting Flask on port 5001..."
python3 app.py

# Note: This runs in foreground so you can see logs
# Press Ctrl+C to stop

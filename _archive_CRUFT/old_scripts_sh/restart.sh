#!/bin/bash
# Simple restart script for Soulfra server
# Usage: bash restart.sh

echo "🔄 Restarting Soulfra server..."
echo "   Killing old processes on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
sleep 1
echo "   Starting fresh server..."
python3 app.py

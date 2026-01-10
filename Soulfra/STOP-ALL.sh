#!/bin/bash

# STOP-ALL.sh - Stop all Soulfra services
# Usage: bash STOP-ALL.sh

echo "========================================================================"
echo "🛑 Stopping Soulfra Triple Domain System"
echo "========================================================================"
echo ""

# Check if .pids file exists
if [ ! -f .pids ]; then
    echo "❌ No .pids file found"
    echo "   Services may not be running, or were started manually"
    echo ""
    echo "To stop manually, find processes:"
    echo "   ps aux | grep 'python3.*app.py'"
    echo "   ps aux | grep 'http.server'"
    exit 1
fi

# Read PIDs
PIDS=$(cat .pids)

# Kill each process
for PID in $PIDS; do
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping PID: $PID"
        kill $PID
    else
        echo "PID $PID not running (already stopped)"
    fi
done

# Remove .pids file
rm .pids

echo ""
echo "✅ All services stopped"
echo "========================================================================"

#!/bin/bash
#
# Start StPetePros Backend with Public URL
#
# This makes your laptop accept payments from the internet.
# Forms on soulfra.github.io → submit to YOUR laptop → saved to YOUR database
#
# Usage:
#   ./start-public-backend.sh
#
# Stop with: Ctrl+C

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  StPetePros Public Backend"
echo "=========================================="
echo ""

# Check if Flask is already running
if pgrep -f "python3.*app.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Flask is already running${NC}"
    echo ""
    echo "Kill it first with:"
    echo "  pkill -f 'python3.*app.py'"
    echo ""
    exit 1
fi

# Start Flask in background
echo -e "${BLUE}🚀 Starting Flask backend...${NC}"
python3 app.py > flask.log 2>&1 &
FLASK_PID=$!

# Wait for Flask to start
echo -e "${BLUE}⏳ Waiting for Flask to start...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:5001/health > /dev/null 2>&1 || curl -s http://localhost:5001 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Flask running on localhost:5001${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${YELLOW}⚠️  Flask may not be ready yet (continuing anyway)${NC}"
    fi
    sleep 1
done

# Start ngrok tunnel
echo ""
echo -e "${BLUE}🌐 Creating public tunnel...${NC}"
echo ""

# Check if ngrok is authenticated
if ! ngrok config check > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  ngrok may not be authenticated${NC}"
    echo ""
    echo "Sign up at: https://dashboard.ngrok.com/signup"
    echo "Then run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    echo "Continuing anyway (may work on free tier)..."
    echo ""
fi

# Start ngrok
ngrok http 5001 \
    --log=stdout \
    --log-level=info \
    --log-format=term

# Cleanup on exit
trap "echo ''; echo 'Stopping Flask...'; kill $FLASK_PID 2>/dev/null; echo 'Done.'; exit 0" EXIT INT TERM

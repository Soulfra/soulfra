#!/bin/bash

# START-ALL.sh - Start all three Soulfra services
# Usage: bash START-ALL.sh

echo "========================================================================"
echo "🚀 Starting Soulfra Triple Domain System"
echo "========================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory FIRST (before trying to write to it)
mkdir -p logs

# Check Ollama
echo -e "${BLUE}[1/4] Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is NOT running${NC}"
    echo "   Start with: ollama serve"
    echo "   Pull model: ollama pull llama3.2"
    echo ""
fi

# Start soulfra.com (Flask app with tribunal endpoints)
echo -e "${BLUE}[2/4] Starting soulfra.com (port 8001)...${NC}"
cd Soulfra.com
python3 app.py > ../logs/static.log 2>&1 &
STATIC_PID=$!
echo -e "${GREEN}✅ soulfra.com running (PID: $STATIC_PID)${NC}"
echo "   URL: http://localhost:8001"
echo "   Logs: logs/static.log"
cd ..

# Start soulfraapi.com (API)
echo -e "${BLUE}[3/4] Starting soulfraapi.com (port 5002)...${NC}"
cd Soulfraapi.com
python3 app.py > ../logs/api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✅ soulfraapi.com running (PID: $API_PID)${NC}"
echo "   URL: http://localhost:5002"
echo "   Logs: logs/api.log"
cd ..

# Wait for API to start
sleep 2

# Start soulfra.ai (chat)
echo -e "${BLUE}[4/4] Starting soulfra.ai (port 5003)...${NC}"
cd Soulfra.ai
python3 app.py > ../logs/ai.log 2>&1 &
AI_PID=$!
echo -e "${GREEN}✅ soulfra.ai running (PID: $AI_PID)${NC}"
echo "   URL: http://localhost:5003"
echo "   Logs: logs/ai.log"
cd ..

echo ""
echo "========================================================================"
echo "✅ All services started!"
echo "========================================================================"
echo ""
echo "Testing the flow:"
echo "  1. Visit: http://localhost:8001 (soulfra.com)"
echo "  2. See QR code on landing page"
echo "  3. Test signup: curl -L http://localhost:5002/qr-signup?ref=test"
echo "  4. Should redirect to: http://localhost:5003/?session=TOKEN"
echo ""
echo "Process IDs:"
echo "  soulfra.com     (PID: $STATIC_PID)"
echo "  soulfraapi.com  (PID: $API_PID)"
echo "  soulfra.ai      (PID: $AI_PID)"
echo ""
echo "To stop all services:"
echo "  kill $STATIC_PID $API_PID $AI_PID"
echo ""
echo "Or use: bash STOP-ALL.sh"
echo "========================================================================"
echo ""

# Save PIDs to file for easy cleanup
echo "$STATIC_PID" > .pids
echo "$API_PID" >> .pids
echo "$AI_PID" >> .pids

# Create logs directory
mkdir -p logs

echo "Logs will be written to logs/ directory"
echo "Press Ctrl+C to stop (or run: bash STOP-ALL.sh)"

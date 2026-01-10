#!/bin/bash

# TEST-FLOW.sh - Test the triple QR authentication flow
# Usage: bash TEST-FLOW.sh

echo "========================================================================"
echo "🧪 Testing Soulfra Triple QR Flow"
echo "========================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Check soulfra.com (static site)
echo -e "${YELLOW}[1/7] Testing soulfra.com (port 8001)...${NC}"
if curl -s http://localhost:8001 > /dev/null; then
    echo -e "${GREEN}✅ soulfra.com is running${NC}"
else
    echo -e "${RED}❌ soulfra.com is NOT running${NC}"
    echo "   Start with: bash START-ALL.sh"
    exit 1
fi

# Test 2: Check soulfraapi.com health
echo -e "${YELLOW}[2/7] Testing soulfraapi.com (port 5002)...${NC}"
API_HEALTH=$(curl -s http://localhost:5002/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ soulfraapi.com is running${NC}"
    echo "   $API_HEALTH"
else
    echo -e "${RED}❌ soulfraapi.com is NOT running${NC}"
    exit 1
fi

# Test 3: Check soulfra.ai health
echo -e "${YELLOW}[3/7] Testing soulfra.ai (port 5003)...${NC}"
AI_HEALTH=$(curl -s http://localhost:5003/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ soulfra.ai is running${NC}"
    echo "   $AI_HEALTH"
else
    echo -e "${RED}❌ soulfra.ai is NOT running${NC}"
    exit 1
fi

# Test 4: Check Ollama
echo -e "${YELLOW}[4/7] Testing Ollama (port 11434)...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${RED}❌ Ollama is NOT running${NC}"
    echo "   Start with: ollama serve"
    echo "   This is optional for testing the flow"
fi

# Test 5: Simulate QR scan (account creation)
echo -e "${YELLOW}[5/7] Simulating QR scan (creating account)...${NC}"
REDIRECT_URL=$(curl -s -L -w "%{url_effective}" -o /dev/null http://localhost:5002/qr-signup?ref=test)
echo "   Redirect URL: $REDIRECT_URL"

if [[ $REDIRECT_URL == *"localhost:5003"* ]]; then
    echo -e "${GREEN}✅ Account created, redirected to soulfra.ai${NC}"

    # Extract session token
    SESSION_TOKEN=$(echo $REDIRECT_URL | sed -n 's/.*session=\([^&]*\).*/\1/p')
    echo "   Session token: ${SESSION_TOKEN:0:20}..."
else
    echo -e "${RED}❌ QR signup failed${NC}"
    exit 1
fi

# Test 6: Validate session
echo -e "${YELLOW}[6/7] Validating session token...${NC}"
VALIDATE_RESULT=$(curl -s -X POST http://localhost:5002/validate-session \
    -H "Content-Type: application/json" \
    -d "{\"token\":\"$SESSION_TOKEN\"}")

if [[ $VALIDATE_RESULT == *"\"valid\":true"* ]]; then
    echo -e "${GREEN}✅ Session token is valid${NC}"
    USERNAME=$(echo $VALIDATE_RESULT | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "   Username: $USERNAME"
else
    echo -e "${RED}❌ Session validation failed${NC}"
    echo "   Response: $VALIDATE_RESULT"
    exit 1
fi

# Test 7: Check API stats
echo -e "${YELLOW}[7/7] Checking API statistics...${NC}"
STATS=$(curl -s http://localhost:5002/stats)
echo "   $STATS"

echo ""
echo "========================================================================"
echo -e "${GREEN}✅ Triple QR Flow Test PASSED!${NC}"
echo "========================================================================"
echo ""
echo "Full flow working:"
echo "  1. ✅ soulfra.com serving landing page"
echo "  2. ✅ QR scan creates account in soulfraapi.com"
echo "  3. ✅ Redirects to soulfra.ai with session token"
echo "  4. ✅ Session token validates successfully"
echo ""
echo "Next steps:"
echo "  1. Visit http://localhost:8001 to see landing page"
echo "  2. Test chat: http://localhost:5003/?session=$SESSION_TOKEN"
echo "  3. Test on iPhone: bash EXPOSE-TO-IPHONE.sh"
echo ""
echo "========================================================================"

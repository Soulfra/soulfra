#!/bin/bash

# Publish a test post to verify the complete Magic Publish pipeline works

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;91m'
NC='\033[0m'

echo ""
echo "========================================================================"
echo "  🧪 TESTING MAGIC PUBLISH PIPELINE"
echo "========================================================================"
echo ""

# Check if Flask is running
if ! lsof -i :5001 > /dev/null 2>&1; then
    echo -e "${RED}❌ Flask app not running on port 5001${NC}"
    echo "   Start with: python3 app.py"
    exit 1
fi

# Check if Ollama is running
if ! curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Ollama not running - Magic Publish will fail${NC}"
    echo "   Start with: ollama serve"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"
echo "   • Flask running on port 5001"
echo "   • Ollama running on port 11434"
echo ""

# Create test content
TITLE="Test Post - $(date '+%Y-%m-%d %H:%M:%S')"
CONTENT="This is an automated test post to verify the Magic Publish pipeline works correctly.

**Features tested:**
- Ollama transformation for all 9 domains
- Database insertion
- HTML file export to GitHub repos
- Git commit and push

If you're reading this on soulfra.com, the entire pipeline worked! 🎉"

echo -e "${BLUE}Publishing test post...${NC}"
echo "   Title: $TITLE"
echo ""

# Call Magic Publish API
RESPONSE=$(curl -s -X POST http://localhost:5001/api/studio/magic-publish \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"$TITLE\",
    \"content\": \"$CONTENT\",
    \"push_to_github\": true
  }")

# Check response
if echo "$RESPONSE" | grep -q '"success"' 2>/dev/null; then
    echo -e "${GREEN}✅ Magic Publish succeeded!${NC}"
    echo ""

    # Parse response for details
    DOMAINS_PUBLISHED=$(echo "$RESPONSE" | grep -o '"published_domains":\[[^]]*\]' | grep -o '","' | wc -l | tr -d ' ')
    echo "   Published to: $DOMAINS_PUBLISHED domains"
    echo ""

    # Check database
    POST_COUNT=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM posts;" 2>/dev/null)
    echo "   Total posts in database: $POST_COUNT"
    echo ""

    # Check GitHub repos
    echo -e "${BLUE}Checking GitHub repos...${NC}"
    cd /Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra 2>/dev/null
    if [ $? -eq 0 ]; then
        LAST_COMMIT=$(git log -1 --format="%s" 2>/dev/null)
        echo "   Latest commit: $LAST_COMMIT"

        HTML_COUNT=$(ls post/*.html 2>/dev/null | wc -l | tr -d ' ')
        echo "   HTML files: $HTML_COUNT"
    fi
    echo ""

    echo -e "${GREEN}✅ TEST PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "   1. Wait 5-10 minutes for GitHub Pages to deploy"
    echo "   2. Check: http://soulfra.com"
    echo "   3. Verify your test post appears"
    echo ""
else
    echo -e "${RED}❌ Magic Publish failed${NC}"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | head -20
    echo ""
    echo "Troubleshooting:"
    echo "   • Check Ollama is running: curl http://localhost:11434/api/tags"
    echo "   • Check Flask logs for errors"
    echo "   • Verify database is writable: ls -la soulfra.db"
    echo ""
    exit 1
fi

echo "========================================================================"
echo ""

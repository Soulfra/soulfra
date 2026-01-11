#!/bin/bash

# SOULFRA CONTROL PANEL
# Master script to understand and control ALL Soulfra services

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;91m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "========================================================================"
echo "  🎯 SOULFRA MASTER CONTROL PANEL"
echo "========================================================================"
echo ""

# Function to check if port is in use
check_port() {
    lsof -i :$1 2>/dev/null | grep LISTEN | head -1
}

# Function to get process name from port
get_process() {
    lsof -i :$1 2>/dev/null | grep LISTEN | awk '{print $1}' | head -1
}

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SYSTEM A: BLOG PUBLISHING (Magic Publish)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check localhost:5001
if [ -n "$(check_port 5001)" ]; then
    echo -e "${GREEN}✅ Port 5001${NC} - Flask App (Magic Publish)"
    echo "   Status: RUNNING"
    echo "   URL:    http://localhost:5001/studio"
    echo "   Purpose: Write content → Magic Publish → 9 domains"
    echo "   Database: /soulfra-simple/soulfra.db (36 posts)"
else
    echo -e "${RED}❌ Port 5001${NC} - Flask App (Magic Publish)"
    echo "   Status: NOT RUNNING"
    echo "   Start:  cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple && python3 app.py"
fi
echo ""

# Check if soulfra.com is live
if curl -s --max-time 2 http://soulfra.com > /dev/null 2>&1; then
    echo -e "${GREEN}✅ soulfra.com${NC} - LIVE"
    echo "   URL: http://soulfra.com"
    echo "   SSL: ⚠️  HTTPS not working yet (needs 24-48hr for cert)"
else
    echo -e "${YELLOW}⚠️  soulfra.com${NC} - May be slow or rate-limited"
fi
echo ""

echo -e "${CYAN}Key Files:${NC}"
echo "  • Database: /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db"
echo "  • GitHub Repos: /Users/matthewmauer/Desktop/roommate-chat/github-repos/"
echo "  • Studio UI: http://localhost:5001/studio"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SYSTEM B: QR CODE FLOW (Triple Domain System)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check ports for QR system
PORT_8001=$(check_port 8001)
PORT_5002=$(check_port 5002)
PORT_5003=$(check_port 5003)

if [ -n "$PORT_8001" ]; then
    echo -e "${GREEN}✅ Port 8001${NC} - Soulfra.com (Landing Page)"
    echo "   Status: RUNNING"
    echo "   URL:    http://localhost:8001"
else
    echo -e "${RED}❌ Port 8001${NC} - Soulfra.com (Landing Page)"
    echo "   Status: NOT RUNNING"
fi
echo ""

if [ -n "$PORT_5002" ]; then
    echo -e "${GREEN}✅ Port 5002${NC} - Soulfraapi.com (API Backend)"
    echo "   Status: RUNNING"
    echo "   URL:    http://localhost:5002"
else
    echo -e "${RED}❌ Port 5002${NC} - Soulfraapi.com (API Backend)"
    echo "   Status: NOT RUNNING"
fi
echo ""

if [ -n "$PORT_5003" ]; then
    echo -e "${GREEN}✅ Port 5003${NC} - Soulfra.ai (Chat Interface)"
    echo "   Status: RUNNING"
    echo "   URL:    http://localhost:5003"
else
    echo -e "${RED}❌ Port 5003${NC} - Soulfra.ai (Chat Interface)"
    echo "   Status: NOT RUNNING"
fi
echo ""

# Check if START-ALL.sh exists
if [ -f "Soulfra/START-ALL.sh" ]; then
    echo -e "${CYAN}Start QR System:${NC} bash Soulfra/START-ALL.sh"
    echo -e "${CYAN}Stop QR System:${NC}  bash Soulfra/STOP-ALL.sh"
else
    echo -e "${YELLOW}⚠️  QR System scripts not found in current directory${NC}"
    echo "   Expected: Soulfra/START-ALL.sh"
fi
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  OLLAMA STATUS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Ollama
if curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama${NC} - RUNNING"
    echo "   Port: 11434"
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name"' | wc -l | tr -d ' ')
    echo "   Models loaded: $MODEL_COUNT"
    echo "   List models: ollama list"
else
    echo -e "${RED}❌ Ollama${NC} - NOT RUNNING"
    echo "   Start: ollama serve"
    echo "   Note: Magic Publish needs Ollama for content transformation"
fi
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  DATABASE STATUS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check main database
MAIN_DB="/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db"
if [ -f "$MAIN_DB" ]; then
    POST_COUNT=$(sqlite3 "$MAIN_DB" "SELECT COUNT(*) FROM posts;" 2>/dev/null || echo "0")
    BRAND_COUNT=$(sqlite3 "$MAIN_DB" "SELECT COUNT(*) FROM brands;" 2>/dev/null || echo "0")
    USER_COUNT=$(sqlite3 "$MAIN_DB" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

    echo -e "${GREEN}✅ Main Database${NC} (soulfra-simple/soulfra.db)"
    echo "   Posts:  $POST_COUNT"
    echo "   Brands: $BRAND_COUNT"
    echo "   Users:  $USER_COUNT"
else
    echo -e "${RED}❌ Main Database${NC} NOT FOUND"
fi
echo ""

# Count all databases
DB_COUNT=$(find /Users/matthewmauer/Desktop/roommate-chat -name "soulfra.db" -type f 2>/dev/null | wc -l | tr -d ' ')
echo -e "${YELLOW}⚠️  Found $DB_COUNT total 'soulfra.db' files${NC}"
echo "   (Backups, old versions, test databases)"
echo "   Master database: $MAIN_DB"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  GITHUB REPOS STATUS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

REPOS_DIR="/Users/matthewmauer/Desktop/roommate-chat/github-repos"
if [ -d "$REPOS_DIR" ]; then
    REPO_COUNT=$(ls -1 "$REPOS_DIR" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}✅ GitHub Repos Directory${NC}"
    echo "   Location: $REPOS_DIR"
    echo "   Repos: $REPO_COUNT"
    echo ""
    echo "   Repos:"
    ls -1 "$REPOS_DIR" 2>/dev/null | while read repo; do
        if [ -d "$REPOS_DIR/$repo/.git" ]; then
            echo "     • $repo (git connected)"
        fi
    done
else
    echo -e "${RED}❌ GitHub Repos Directory${NC} NOT FOUND"
fi
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  QUICK ACTIONS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo "📝 Publish Blog Post (System A):"
echo "   1. Open: http://localhost:5001/studio"
echo "   2. Write content and click 'Magic Publish'"
echo "   3. Wait 10 min, check: http://soulfra.com"
echo ""

echo "🧪 Test QR Flow (System B):"
echo "   1. Start: bash Soulfra/START-ALL.sh"
echo "   2. Visit: http://localhost:8001"
echo "   3. Scan QR code or test API"
echo ""

echo "🔍 Check System Status:"
echo "   bash SOULFRA-CONTROL.sh (this script)"
echo ""

echo "📊 View Documentation:"
echo "   cat SYSTEM-STATUS.md           # Full system overview"
echo "   cat DEPLOYMENT-CHECKLIST.md    # How to publish"
echo "   cat SSL-FIX-GUIDE.md            # Fix HTTPS"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  TROUBLESHOOTING${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -z "$(check_port 5001)" ]; then
    echo -e "${YELLOW}⚠️  Flask not running on port 5001${NC}"
    echo "   Fix: cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple && python3 app.py"
    echo ""
fi

if ! curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Ollama not running${NC}"
    echo "   Fix: ollama serve"
    echo "   Note: Magic Publish won't work without Ollama"
    echo ""
fi

if [ ! -f "$MAIN_DB" ]; then
    echo -e "${RED}❌ Main database missing${NC}"
    echo "   Expected: $MAIN_DB"
    echo ""
fi

echo "========================================================================"
echo ""

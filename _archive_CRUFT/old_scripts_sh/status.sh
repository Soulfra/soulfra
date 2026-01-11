#!/bin/bash
#
# StPetePros Status - Quick Overview
#

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=============================================="
echo "  StPetePros Status"
echo "=============================================="
echo ""

# Count professionals
PROF_COUNT=$(sqlite3 ~/Desktop/roommate-chat/soulfra-simple/soulfra.db "SELECT COUNT(*) FROM professionals WHERE approval_status = 'approved'" 2>/dev/null || echo "0")
echo -e "${BLUE}📊 Database:${NC} $PROF_COUNT professionals"

# Check what's running
DROPBOX_RUNNING=$(ps aux | grep -c "[p]ython3.*dropbox-watcher.py")
AUTODEPLOY_RUNNING=$(ps aux | grep -c "[p]ython3.*auto-deploy.py")
OLLAMA_RUNNING=$(ps aux | grep -c "[o]llama serve")

echo ""
echo -e "${BLUE}🔄 Services:${NC}"
if [ "$DROPBOX_RUNNING" -gt 0 ]; then
    echo -e "  ${GREEN}✅${NC} Drop Box Watcher (watching AirDrops)"
else
    echo -e "  ⚪ Drop Box Watcher (not running)"
fi

if [ "$AUTODEPLOY_RUNNING" -gt 0 ]; then
    echo -e "  ${GREEN}✅${NC} Auto-Deploy (watching GitHub Pages)"
else
    echo -e "  ⚪ Auto-Deploy (not running)"
fi

if [ "$OLLAMA_RUNNING" -gt 0 ]; then
    echo -e "  ${GREEN}✅${NC} Ollama (ready to generate content)"
else
    echo -e "  ⚪ Ollama (not running)"
fi

echo ""
echo -e "${BLUE}🌐 URLs:${NC}"
echo "  GitHub Pages: https://soulfra.github.io/stpetepros/"
echo "  Custom Domain: https://soulfra.com/stpetepros/"
echo ""

# Quick tips
if [ "$DROPBOX_RUNNING" -eq 0 ] && [ "$AUTODEPLOY_RUNNING" -eq 0 ]; then
    echo -e "${YELLOW}💡 Start automation:${NC} ./stpetepros-simple.sh"
    echo ""
fi

echo "=============================================="
echo ""

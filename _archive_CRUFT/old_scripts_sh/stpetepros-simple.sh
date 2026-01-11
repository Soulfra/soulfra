#!/bin/bash
#
# StPetePros Simple - ONE Script to Run Everything
#
# This starts ALL automation:
# - Drop Box watcher (process AirDrops from phone)
# - Auto-deploy (watch GitHub Pages folder, auto-push)
# - Ready to generate content with Ollama
#
# Usage:
#   ./stpetepros-simple.sh
#
# Stop all: Ctrl+C (stops everything)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Directories
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GITHUB_PAGES_DIR="$HOME/Desktop/soulfra.github.io"

echo ""
echo "=============================================="
echo "  StPetePros Simple"
echo "=============================================="
echo ""
echo "Starting automation..."
echo ""

# Array to track background processes
PIDS=()

# Function to kill all background processes on exit
cleanup() {
    echo ""
    echo ""
    echo -e "${YELLOW}Stopping all processes...${NC}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    echo -e "${GREEN}Stopped.${NC}"
    echo ""
    exit 0
}

trap cleanup INT TERM

# 1. Start Drop Box watcher
echo -e "${BLUE}1️⃣  Starting Drop Box watcher...${NC}"
echo "   📂 Watching: ~/Public/Drop Box/"
echo "   💡 AirDrop files to auto-process"
echo ""

cd "$SELF_DIR"
python3 dropbox-watcher.py &
PIDS+=($!)

sleep 1

# 2. Start Auto-Deploy (GitHub Pages)
echo -e "${BLUE}2️⃣  Starting Auto-Deploy...${NC}"
echo "   📂 Watching: ~/Desktop/soulfra.github.io/stpetepros/"
echo "   💡 Edits auto-push to GitHub"
echo ""

cd "$GITHUB_PAGES_DIR"
python3 auto-deploy.py &
PIDS+=($!)

sleep 1

# 3. Check Ollama
echo -e "${BLUE}3️⃣  Checking Ollama...${NC}"
if ps aux | grep -q "[o]llama serve"; then
    echo -e "   ${GREEN}✅ Ollama is running (localhost:11434)${NC}"
    echo "   💡 Generate content: python3 ollama-content-generator.py batch-bios"
else
    echo -e "   ${YELLOW}⚠️  Ollama not running${NC}"
    echo "   💡 Start with: ollama serve"
fi
echo ""

# Summary
echo "=============================================="
echo ""
echo -e "${GREEN}✅ StPetePros Simple is running!${NC}"
echo ""
echo "📦 What's automated:"
echo ""
echo "  1. AirDrop workflow:"
echo "     • AirDrop professionals.csv from phone"
echo "     • Auto-imports to database"
echo "     • Auto-exports to GitHub Pages"
echo "     • Auto-deploys (live in 30s)"
echo ""
echo "  2. Manual edits:"
echo "     • Edit files in ~/Desktop/soulfra.github.io/stpetepros/"
echo "     • Auto-commits and pushes"
echo "     • Live in 30s"
echo ""
echo "  3. Content generation:"
echo "     • python3 $SELF_DIR/ollama-content-generator.py batch-bios"
echo "     • python3 $SELF_DIR/export-to-github-pages.py"
echo ""
echo "🌐 Live website: https://soulfra.github.io/stpetepros/"
echo ""
echo "=============================================="
echo ""
echo -e "${YELLOW}Stop all automation: Press Ctrl+C${NC}"
echo ""

# Wait for Ctrl+C
wait

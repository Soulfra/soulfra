#!/bin/bash
# Soulfra Automated Test Runner
# Runs all tests including screenshot/visual tests

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "🧪 Soulfra Automated Test Suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is running
echo "${BLUE}Checking if test server is running...${NC}"
if curl -s http://localhost:5001 > /dev/null; then
    echo "${GREEN}✓${NC} Server is running on http://localhost:5001"
else
    echo "${RED}✗${NC} Server not running. Please start it with: python3 app.py"
    exit 1
fi

echo ""

# Run database tests
echo "${BLUE}1. Running Database Tests...${NC}"
python3 test_database.py
echo ""

# Run app/route tests
echo "${BLUE}2. Running App Route Tests...${NC}"
python3 test_app.py
echo ""

# Run avatar generator tests
echo "${BLUE}3. Running Avatar Tests...${NC}"
python3 test_avatar_generator.py
echo ""

# Run DIY visual tests (no playwright needed!)
echo "${BLUE}4. Running DIY Visual Tests...${NC}"
python3 test_visual_diy.py

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "${GREEN}✅ All Tests Complete!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Test Summary:"
echo "  - Database Tests: ✓"
echo "  - Route Tests: ✓"
echo "  - Avatar Tests: ✓"
echo "  - DIY Visual Tests: ✓ (built from scratch!)"
echo ""
echo "📸 Baselines saved in: baselines/"
echo ""

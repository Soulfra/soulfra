#!/bin/bash

# Test all GitHub Pages URLs to verify everything is live

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;91m'
NC='\033[0m'

echo ""
echo "========================================================================"
echo "  🧪 TESTING GITHUB PAGES URLS"
echo "========================================================================"
echo ""

# Function to test URL
test_url() {
    URL=$1
    NAME=$2

    echo -n "Testing $NAME... "

    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$URL" 2>/dev/null)

    if [ "$STATUS" = "200" ] || [ "$STATUS" = "301" ] || [ "$STATUS" = "302" ]; then
        echo -e "${GREEN}✅ $STATUS${NC}"
        return 0
    else
        echo -e "${RED}❌ $STATUS${NC}"
        return 1
    fi
}

PASS=0
FAIL=0

echo -e "${BLUE}Testing GitHub Pages URLs:${NC}"
echo ""

# Test user site
if test_url "https://soulfra.github.io/" "soulfra.github.io (landing page)"; then
    ((PASS++))
else
    ((FAIL++))
fi

# Test project sites
if test_url "https://soulfra.github.io/soulfra/" "soulfra.github.io/soulfra (blog)"; then
    ((PASS++))
else
    ((FAIL++))
fi

if test_url "https://soulfra.github.io/calriven/" "soulfra.github.io/calriven"; then
    ((PASS++))
else
    ((FAIL++))
fi

if test_url "https://soulfra.github.io/deathtodata/" "soulfra.github.io/deathtodata"; then
    ((PASS++))
else
    ((FAIL++))
fi

echo ""
echo -e "${BLUE}Testing Custom Domains:${NC}"
echo ""

# Test custom domain (HTTP)
if test_url "http://soulfra.com" "soulfra.com (HTTP)"; then
    ((PASS++))
else
    ((FAIL++))
fi

# Test custom domain (HTTPS)
echo -n "Testing soulfra.com (HTTPS)... "
if curl -s --max-time 5 https://soulfra.com > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 200${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  SSL cert pending${NC}"
    echo "   (This is normal - takes 24-48hrs after enabling HTTPS)"
    ((FAIL++))
fi

echo ""
echo "========================================================================"
echo -e "${GREEN}Passed: $PASS${NC} | ${RED}Failed: $FAIL${NC}"
echo "========================================================================"
echo ""

if [ $PASS -ge 4 ]; then
    echo -e "${GREEN}✅ SUCCESS! Your GitHub Pages sites are LIVE!${NC}"
    echo ""
    echo "View your sites:"
    echo "  Landing Page: https://soulfra.github.io/"
    echo "  Blog:         https://soulfra.github.io/soulfra/"
    echo "  Custom:       http://soulfra.com"
    echo ""
else
    echo -e "${RED}⚠️  Some URLs are not working${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check GitHub Pages is enabled for each repo"
    echo "  2. Check repos are public (not private)"
    echo "  3. Wait a few minutes after pushing commits"
    echo ""
fi

echo "========================================================================"
echo ""

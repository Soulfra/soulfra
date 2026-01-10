#!/bin/bash

###############################################################################
# 🎮 CringeProof Pre-Flight Dependency Check
#
# Like Taco Bell app or RuneScape launcher - checks all dependencies
# before allowing connection. Blocks startup if anything is missing.
#
# Validates:
# - Required binaries (python3, node, ipfs, curl)
# - Python packages (flask, requests, whisper, etc)
# - Node modules (express, crypto)
# - System permissions
# - Port availability
# - File structure integrity
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎮 CringeProof Pre-Flight Dependency Check${NC}"
echo -e "${BLUE}   Like RuneScape launcher - check EVERYTHING${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

###############################################################################
# 1. BINARIES
###############################################################################
echo -e "${BLUE}[1/7] Checking Required Binaries...${NC}"

check_binary() {
    local bin=$1
    local required=$2

    if command -v $bin &> /dev/null; then
        local version=$(command $bin --version 2>&1 | head -1)
        echo -e "${GREEN}  ✅ $bin${NC} - $version"
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}  ❌ $bin NOT FOUND${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${YELLOW}  ⚠️  $bin not found (optional)${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

check_binary "python3" "true"
check_binary "node" "true"
check_binary "ipfs" "true"
check_binary "curl" "true"
check_binary "jq" "false"  # Optional for JSON parsing
check_binary "sqlite3" "true"

###############################################################################
# 2. PYTHON PACKAGES
###############################################################################
echo ""
echo -e "${BLUE}[2/7] Checking Python Packages...${NC}"

check_python_package() {
    local package=$1

    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}  ✅ $package${NC}"
    else
        echo -e "${RED}  ❌ $package NOT INSTALLED${NC}"
        echo -e "     Install: pip3 install $package"
        ERRORS=$((ERRORS + 1))
    fi
}

check_python_package "flask"
check_python_package "requests"
check_python_package "sqlite3"

# Check whisper (optional - for transcription)
if python3 -c "import whisper" 2>/dev/null; then
    echo -e "${GREEN}  ✅ whisper (transcription enabled)${NC}"
else
    echo -e "${YELLOW}  ⚠️  whisper not found (transcription disabled)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

###############################################################################
# 3. NODE MODULES
###############################################################################
echo ""
echo -e "${BLUE}[3/7] Checking Node Modules...${NC}"

MESH_DIR="soulfra.github.io/Founder-Bootstrap/Blank-Kernel/SOULFRA-CONSOLIDATED-2025/misc"

if [ -d "$MESH_DIR/node_modules" ]; then
    echo -e "${GREEN}  ✅ node_modules exists${NC}"

    # Check critical modules
    if [ -d "$MESH_DIR/node_modules/express" ]; then
        echo -e "${GREEN}  ✅ express${NC}"
    else
        echo -e "${RED}  ❌ express missing${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}  ⚠️  node_modules not found in mesh directory${NC}"
    echo -e "     Run: cd $MESH_DIR && npm install"
    WARNINGS=$((WARNINGS + 1))
fi

###############################################################################
# 4. PORT AVAILABILITY
###############################################################################
echo ""
echo -e "${BLUE}[4/7] Checking Port Availability...${NC}"

check_port() {
    local port=$1
    local service=$2

    if lsof -i :$port >/dev/null 2>&1; then
        local process=$(lsof -i :$port | tail -1 | awk '{print $1}')
        echo -e "${YELLOW}  ⚠️  Port $port ($service) in use by $process${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}  ✅ Port $port ($service) available${NC}"
    fi
}

check_port "5001" "Flask HTTPS"
check_port "5002" "IPFS API"
check_port "8080" "IPFS Gateway"
check_port "8888" "Mesh Router"
check_port "4001" "IPFS Swarm"

###############################################################################
# 5. FILE STRUCTURE
###############################################################################
echo ""
echo -e "${BLUE}[5/7] Checking File Structure...${NC}"

check_file() {
    local file=$1
    local critical=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        if [ "$critical" = "true" ]; then
            echo -e "${RED}  ❌ $file MISSING${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${YELLOW}  ⚠️  $file missing (optional)${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

check_file "app.py" "true"
check_file "simple_voice_routes.py" "true"
check_file "mesh_flask_bridge.py" "true"
check_file "soulfra.db" "true"
check_file "voice-archive/wall.html" "true"
check_file "voice-archive/record-simple.html" "true"
check_file "$MESH_DIR/mesh-router.js" "true"
check_file "$MESH_DIR/mesh-config.json" "true"

###############################################################################
# 6. IPFS CONFIGURATION
###############################################################################
echo ""
echo -e "${BLUE}[6/7] Checking IPFS Configuration...${NC}"

if [ -d ~/.ipfs ]; then
    echo -e "${GREEN}  ✅ IPFS repo initialized${NC}"

    # Check IPFS API port
    API_PORT=$(ipfs config Addresses.API 2>/dev/null | grep -oE '[0-9]+$' || echo "NOT SET")
    if [ "$API_PORT" = "5002" ]; then
        echo -e "${GREEN}  ✅ IPFS API on port 5002${NC}"
    else
        echo -e "${YELLOW}  ⚠️  IPFS API on port $API_PORT (expected 5002)${NC}"
        echo -e "     Fix: ipfs config Addresses.API /ip4/127.0.0.1/tcp/5002"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}  ❌ IPFS not initialized${NC}"
    echo -e "     Run: ipfs init"
    ERRORS=$((ERRORS + 1))
fi

###############################################################################
# 7. SYSTEM PERMISSIONS
###############################################################################
echo ""
echo -e "${BLUE}[7/7] Checking System Permissions...${NC}"

# Check write access to logs directory
if [ -w /tmp ]; then
    echo -e "${GREEN}  ✅ Can write to /tmp (for logs)${NC}"
else
    echo -e "${RED}  ❌ Cannot write to /tmp${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check database write access
if [ -w soulfra.db ]; then
    echo -e "${GREEN}  ✅ Can write to soulfra.db${NC}"
else
    echo -e "${RED}  ❌ Cannot write to soulfra.db${NC}"
    ERRORS=$((ERRORS + 1))
fi

###############################################################################
# SUMMARY
###############################################################################
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Pre-Flight Check Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo -e "${GREEN}   Ready to start CringeProof mesh network${NC}"
    echo ""
    echo -e "${BLUE}Run: ./start-decentralized-cringeproof.sh${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS WARNING(S)${NC}"
    echo -e "${YELLOW}   System will start but some features may be limited${NC}"
    echo ""
    echo -e "${BLUE}Run: ./start-decentralized-cringeproof.sh${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS CRITICAL ERROR(S)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS WARNING(S)${NC}"
    fi
    echo ""
    echo -e "${RED}CANNOT START - Fix errors above first${NC}"
    exit 1
fi

#!/bin/bash
# Setup HTTPS Voice Recording System
# Configures SSL, Flask CORS, and tests complete flow

set -e  # Exit on error

echo "🎤 =================================================="
echo "   HTTPS VOICE RECORDING SETUP"
echo "   =================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get local IP
LOCAL_IP=$(ipconfig getifaddr en0 || echo "192.168.1.87")

echo -e "${BLUE}Detected local IP: ${LOCAL_IP}${NC}"
echo ""

# Step 1: Check dependencies
echo -e "${BLUE}1️⃣  Checking dependencies...${NC}"

if ! command -v openssl &> /dev/null; then
    echo -e "${RED}❌ OpenSSL not found${NC}"
    echo "   Install: brew install openssl"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  ffmpeg not found (optional for video)${NC}"
    echo "   Install: brew install ffmpeg"
fi

echo -e "${GREEN}✅ Dependencies OK${NC}"
echo ""

# Step 2: Generate SSL certificate
echo -e "${BLUE}2️⃣  Generating SSL certificate...${NC}"

if [ -f "ssl_certs/cert.pem" ]; then
    echo -e "${YELLOW}⚠️  Certificate already exists${NC}"
    read -p "   Regenerate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 ssl_local_server.py --generate --ip $LOCAL_IP
    else
        echo "   Using existing certificate"
    fi
else
    python3 ssl_local_server.py --generate --ip $LOCAL_IP
fi

echo ""

# Step 3: Check Flask CORS
echo -e "${BLUE}3️⃣  Checking Flask CORS setup...${NC}"

if grep -q "flask_cors" app.py 2>/dev/null; then
    echo -e "${GREEN}✅ CORS already configured${NC}"
else
    echo -e "${YELLOW}⚠️  CORS not found in app.py${NC}"
    echo ""
    echo "Add this to app.py:"
    echo ""
    echo -e "${YELLOW}from flask_cors import CORS${NC}"
    echo -e "${YELLOW}CORS(app, origins=['*'])${NC}"
    echo ""
    echo "Or install: pip install flask-cors"
fi

echo ""

# Step 4: Test Ollama
echo -e "${BLUE}4️⃣  Checking Ollama...${NC}"

if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('models', [])))" 2>/dev/null || echo "?")
    echo "   Models: $MODEL_COUNT"
else
    echo -e "${YELLOW}⚠️  Ollama not running${NC}"
    echo "   Start: ollama serve"
fi

echo ""

# Step 5: Summary
echo -e "${BLUE}📋 SETUP SUMMARY${NC}"
echo "   =================================================="
echo ""

echo -e "${GREEN}Option A: Self-Signed SSL (Quick Test)${NC}"
echo "   1. Start HTTPS Flask:"
echo "      python3 ssl_local_server.py --serve"
echo ""
echo "   2. On iPhone, visit:"
echo "      https://${LOCAL_IP}:5001/voice"
echo ""
echo "   3. Accept security warning"
echo "   4. Microphone will work!"
echo ""
echo "   =================================================="
echo ""

echo -e "${GREEN}Option B: GitHub Pages (Production)${NC}"
echo "   1. Deploy github_voice_recorder/ to GitHub Pages"
echo "   2. Visit: https://YOUR_USERNAME.github.io/voice-recorder/"
echo "   3. Enter local server: https://${LOCAL_IP}:5001"
echo "   4. Record and upload to local server"
echo ""
echo "   =================================================="
echo ""

echo -e "${GREEN}Option C: Ollama WebSocket Bridge${NC}"
echo "   1. Start WebSocket bridge:"
echo "      python3 ollama_websocket_bridge.py"
echo ""
echo "   2. Connect from GitHub Pages JavaScript:"
echo "      const ws = new WebSocket('ws://localhost:8765');"
echo ""
echo "   3. Send prompts to local Ollama from static site!"
echo ""
echo "   =================================================="
echo ""

# Step 6: Quick start options
echo -e "${BLUE}🚀 QUICK START${NC}"
echo ""

PS3="Choose an option (1-4): "
options=("Start HTTPS Flask now" "Test video to ASCII" "Generate Ollama bridge token" "Exit")

select opt in "${options[@]}"
do
    case $opt in
        "Start HTTPS Flask now")
            echo ""
            echo -e "${GREEN}Starting Flask with HTTPS...${NC}"
            echo "   Visit: https://${LOCAL_IP}:5001/voice"
            echo ""
            python3 ssl_local_server.py --serve
            break
            ;;
        "Test video to ASCII")
            echo ""
            echo -e "${GREEN}Converting recording #5 to ASCII...${NC}"
            python3 video_to_ascii.py --from-db 5
            break
            ;;
        "Generate Ollama bridge token")
            echo ""
            read -p "Token name: " TOKEN_NAME
            python3 ollama_websocket_bridge.py --generate-token "$TOKEN_NAME"
            echo ""
            echo "Start bridge with: python3 ollama_websocket_bridge.py"
            break
            ;;
        "Exit")
            echo ""
            echo -e "${GREEN}✅ Setup complete!${NC}"
            echo ""
            echo "Next steps:"
            echo "  • python3 ssl_local_server.py --serve"
            echo "  • python3 video_to_ascii.py --from-db 5"
            echo "  • python3 ollama_websocket_bridge.py"
            echo ""
            break
            ;;
        *) echo "Invalid option";;
    esac
done

echo ""
echo "🎤 =================================================="

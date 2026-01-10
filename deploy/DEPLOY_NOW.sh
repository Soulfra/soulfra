#!/bin/bash
# DEPLOY_NOW.sh - One command deployment for Soulfra Voice + CringeProof
# Like cursor.directory: simple, fast, works

set -e  # Exit on error

echo "🚀 Soulfra Simple Deployment"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status tracking
STATUS_MAP=()

function check_status() {
    local name=$1
    local command=$2

    echo -n "Checking ${name}... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        STATUS_MAP+=("${name}:✅")
        return 0
    else
        echo -e "${RED}❌${NC}"
        STATUS_MAP+=("${name}:❌")
        return 1
    fi
}

function install_if_missing() {
    local name=$1
    local check_cmd=$2
    local install_cmd=$3

    if ! eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "${YELLOW}Installing ${name}...${NC}"
        eval "$install_cmd"
    fi
}

echo "📋 System Check"
echo "==============="

# Check Python
check_status "Python 3" "python3 --version"

# Check pip
check_status "pip" "pip3 --version"

# Check if in correct directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Error: app.py not found. Run this from soulfra-simple directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ In correct directory${NC}"

# Install Python dependencies
echo ""
echo "📦 Installing Dependencies"
echo "=========================="
pip3 install -q -r requirements.txt
echo -e "${GREEN}✅ Python packages installed${NC}"

# Check database
echo ""
echo "🗄️  Database Check"
echo "=================="
if [ -f "soulfra.db" ]; then
    DB_SIZE=$(du -h soulfra.db | cut -f1)
    echo -e "${GREEN}✅ Database found (${DB_SIZE})${NC}"
    STATUS_MAP+=("Database:✅")
else
    echo -e "${YELLOW}⚠️  Database not found, will create on first run${NC}"
    STATUS_MAP+=("Database:🔧")
fi

# Check voice recordings
if [ -d "voice_recordings" ]; then
    RECORDING_COUNT=$(ls -1 voice_recordings/*.webm 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}✅ Voice recordings folder (${RECORDING_COUNT} files)${NC}"
else
    mkdir -p voice_recordings
    echo -e "${YELLOW}✅ Created voice_recordings folder${NC}"
fi

# Check static files
if [ -d "static" ]; then
    echo -e "${GREEN}✅ Static files found${NC}"
else
    echo -e "${RED}❌ Static folder missing${NC}"
fi

# Check templates
if [ -d "templates" ]; then
    echo -e "${GREEN}✅ Templates found${NC}"
else
    echo -e "${RED}❌ Templates folder missing${NC}"
fi

echo ""
echo "🌐 Deployment Mode"
echo "=================="
echo "Choose deployment:"
echo "  1) Local (http://localhost:5001)"
echo "  2) Production (with Nginx + Gunicorn + SSL)"
echo ""
read -p "Enter choice [1]: " DEPLOY_MODE
DEPLOY_MODE=${DEPLOY_MODE:-1}

if [ "$DEPLOY_MODE" = "1" ]; then
    echo ""
    echo "🎯 Starting Local Server"
    echo "========================"
    echo -e "${BLUE}Mode: Development${NC}"
    echo -e "${BLUE}URL: http://localhost:5001${NC}"
    echo ""

    # Kill existing Flask processes
    pkill -f "python3 app.py" 2>/dev/null || true
    sleep 1

    # Start Flask
    echo "Starting Flask server..."
    python3 app.py &
    FLASK_PID=$!

    sleep 3

    # Check if server is running
    if curl -s http://localhost:5001/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server running (PID: ${FLASK_PID})${NC}"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}🎉 DEPLOYMENT SUCCESS${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📍 Access Points:"
        echo "   Main: http://localhost:5001/"
        echo "   Voice Box: http://localhost:5001/suggestion-box"
        echo "   Status Map: http://localhost:5001/status-map"
        echo ""
        echo "🎤 Voice Recording Routes:"
        echo "   /voice - Voice recorder"
        echo "   /suggestion-box - Community suggestions"
        echo "   /suggestion/<id> - View suggestion details"
        echo "   /@deathtodata/suggestions - Brand-specific view"
        echo ""
        echo "🔧 Controls:"
        echo "   Stop server: kill ${FLASK_PID}"
        echo "   View logs: tail -f /tmp/flask.log"
        echo "   Status map: http://localhost:5001/status-map"
        echo ""

        # Save PID for later
        echo $FLASK_PID > /tmp/soulfra.pid

        # Open browser (macOS)
        if command -v open > /dev/null 2>&1; then
            echo "Opening browser..."
            sleep 1
            open http://localhost:5001/status-map
        fi

    else
        echo -e "${RED}❌ Server failed to start${NC}"
        echo "Check logs with: python3 app.py"
        exit 1
    fi

elif [ "$DEPLOY_MODE" = "2" ]; then
    echo ""
    echo "🚀 Production Deployment"
    echo "========================"

    # Check for domain
    read -p "Enter your domain (e.g., soulfra.com): " DOMAIN

    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}❌ Domain required for production deployment${NC}"
        exit 1
    fi

    echo ""
    echo "Domain: ${DOMAIN}"
    echo ""

    # Check DNS
    echo "Checking DNS..."
    if host $DOMAIN > /dev/null 2>&1; then
        IP=$(host $DOMAIN | grep "has address" | awk '{print $4}' | head -1)
        echo -e "${GREEN}✅ DNS configured (${IP})${NC}"
    else
        echo -e "${RED}❌ DNS not configured${NC}"
        echo ""
        echo "Configure DNS with these records:"
        echo "  Type: A"
        echo "  Name: @"
        echo "  Value: [Your server IP]"
        echo ""
        read -p "Continue anyway? [y/N]: " CONTINUE
        if [ "$CONTINUE" != "y" ]; then
            exit 1
        fi
    fi

    # Check Nginx
    if command -v nginx > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Nginx installed${NC}"
    else
        echo -e "${YELLOW}Installing Nginx...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install nginx
        else
            sudo apt-get update && sudo apt-get install -y nginx
        fi
    fi

    # Check Certbot (SSL)
    if command -v certbot > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Certbot installed${NC}"
    else
        echo -e "${YELLOW}Installing Certbot...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install certbot
        else
            sudo apt-get install -y certbot python3-certbot-nginx
        fi
    fi

    # Generate Nginx config
    echo ""
    echo "Generating Nginx config..."
    cat > /tmp/soulfra-nginx.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};

    # SSL certificates (will be configured by Certbot)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Max upload size (for voice recordings)
    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias $(pwd)/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Voice recordings
    location /voice_recordings/ {
        alias $(pwd)/voice_recordings/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Proxy to Flask
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support (for future real-time features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

    echo -e "${GREEN}✅ Nginx config generated${NC}"
    echo "Config saved to: /tmp/soulfra-nginx.conf"
    echo ""
    echo "Next steps:"
    echo "1. Copy config: sudo cp /tmp/soulfra-nginx.conf /etc/nginx/sites-available/soulfra"
    echo "2. Enable site: sudo ln -s /etc/nginx/sites-available/soulfra /etc/nginx/sites-enabled/"
    echo "3. Get SSL cert: sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
    echo "4. Start Gunicorn: gunicorn -w 4 -b 127.0.0.1:5001 app:app"
    echo "5. Restart Nginx: sudo nginx -s reload"
    echo ""

    read -p "Auto-configure now? (requires sudo) [y/N]: " AUTO_CONFIG

    if [ "$AUTO_CONFIG" = "y" ]; then
        echo ""
        echo "Starting production deployment..."

        # Copy Nginx config
        sudo cp /tmp/soulfra-nginx.conf /etc/nginx/sites-available/soulfra
        sudo ln -sf /etc/nginx/sites-available/soulfra /etc/nginx/sites-enabled/

        # Test Nginx config
        if sudo nginx -t; then
            echo -e "${GREEN}✅ Nginx config valid${NC}"
        else
            echo -e "${RED}❌ Nginx config invalid${NC}"
            exit 1
        fi

        # Start Gunicorn
        echo "Starting Gunicorn..."
        pkill -f gunicorn 2>/dev/null || true
        gunicorn -w 4 -b 127.0.0.1:5001 --daemon app:app
        echo -e "${GREEN}✅ Gunicorn started${NC}"

        # Reload Nginx
        sudo nginx -s reload
        echo -e "${GREEN}✅ Nginx reloaded${NC}"

        # Get SSL certificate
        echo ""
        echo "Getting SSL certificate..."
        sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}🎉 PRODUCTION DEPLOYMENT SUCCESS${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "🌐 Your site is live:"
        echo "   https://${DOMAIN}"
        echo "   https://${DOMAIN}/suggestion-box"
        echo "   https://${DOMAIN}/status-map"
        echo ""
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Deployment complete! View status map for details."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

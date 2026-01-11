#!/usr/bin/env bash
"""
Router Port Forwarding Setup Script

Helps you expose Flask API (localhost:5001) to api.cringeproof.com
WITHOUT needing Cloudflare Tunnel or ngrok!

Usage:
    ./setup_port_forward.sh
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                            ║${NC}"
    echo -e "${CYAN}║    ${GREEN}Port Forwarding Setup for api.cringeproof.com${CYAN}       ║${NC}"
    echo -e "${CYAN}║                                                            ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_network_diagram() {
    echo -e "${BLUE}Your Network Setup:${NC}"
    echo ""
    echo "┌──────────────────────────────────────────────────────────────────┐"
    echo "│                        INTERNET                                  │"
    echo "│                  (Your Public IP: $PUBLIC_IP)                     │"
    echo "└────────────────────────┬─────────────────────────────────────────┘"
    echo "                         │"
    echo "                         │ (Port 5001 forwarded)"
    echo "                         ▼"
    echo "┌──────────────────────────────────────────────────────────────────┐"
    echo "│                    YOUR ROUTER                                   │"
    echo "│              Gateway: $GATEWAY_IP                               │"
    echo "│                                                                  │"
    echo "│   Port Forward Rule:                                             │"
    echo "│   External Port: 5001 → Internal IP: $LOCAL_IP:5001             │"
    echo "└────────────────────────┬─────────────────────────────────────────┘"
    echo "                         │"
    echo "                         │ (Local Network)"
    echo "                         ▼"
    echo "┌──────────────────────────────────────────────────────────────────┐"
    echo "│              YOUR COMPUTER                                       │"
    echo "│              IP: $LOCAL_IP                                      │"
    echo "│                                                                  │"
    echo "│              Flask App running on:                               │"
    echo "│              http://localhost:5001                               │"
    echo "└──────────────────────────────────────────────────────────────────┘"
    echo ""
}

print_dns_diagram() {
    echo -e "${BLUE}DNS Configuration:${NC}"
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│                Domain Registrar (Namecheap/GoDaddy)         │"
    echo "│                                                             │"
    echo "│   A Record:                                                 │"
    echo "│   Name: api                                                 │"
    echo "│   Type: A                                                   │"
    echo "│   Value: $PUBLIC_IP                                         │"
    echo "│   TTL: 3600                                                 │"
    echo "│                                                             │"
    echo "│   Result: api.cringeproof.com → $PUBLIC_IP                  │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
}

# Step 1: Detect network info
echo -e "${GREEN}Step 1: Detecting your network configuration...${NC}"

# Get local IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
    GATEWAY_IP=$(netstat -rn | grep default | awk '{print $2}' | head -1)
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    GATEWAY_IP=$(ip route | grep default | awk '{print $3}')
fi

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com)

echo -e "  ${CYAN}✓${NC} Local IP: $LOCAL_IP"
echo -e "  ${CYAN}✓${NC} Router IP: $GATEWAY_IP"
echo -e "  ${CYAN}✓${NC} Public IP: $PUBLIC_IP"
echo ""

# Step 2: Display network diagram
print_network_diagram

# Step 3: Check if Flask is running
echo -e "${GREEN}Step 2: Checking if Flask app is running on port 5001...${NC}"

if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "  ${CYAN}✓${NC} Flask app is running on localhost:5001"
else
    echo -e "  ${RED}✗${NC} Flask app is NOT running on port 5001"
    echo ""
    echo -e "${YELLOW}Start your Flask app first:${NC}"
    echo "  python3 app.py"
    echo ""
    exit 1
fi

# Step 4: Detect router model (best effort)
echo ""
echo -e "${GREEN}Step 3: Detecting router model...${NC}"

# Try to detect router
ROUTER_PAGE=$(curl -s --connect-timeout 3 http://$GATEWAY_IP 2>/dev/null || echo "")

if echo "$ROUTER_PAGE" | grep -qi "netgear"; then
    ROUTER_TYPE="Netgear"
elif echo "$ROUTER_PAGE" | grep -qi "linksys"; then
    ROUTER_TYPE="Linksys"
elif echo "$ROUTER_PAGE" | grep -qi "tp-link"; then
    ROUTER_TYPE="TP-Link"
elif echo "$ROUTER_PAGE" | grep -qi "asus"; then
    ROUTER_TYPE="ASUS"
elif echo "$ROUTER_PAGE" | grep -qi "comcast"; then
    ROUTER_TYPE="Comcast/Xfinity"
else
    ROUTER_TYPE="Unknown"
fi

echo -e "  ${CYAN}Detected:${NC} $ROUTER_TYPE router"
echo -e "  ${CYAN}Router Admin:${NC} http://$GATEWAY_IP"
echo ""

# Step 5: Port forwarding instructions
echo -e "${GREEN}Step 4: Configure Port Forwarding${NC}"
echo ""
echo -e "${YELLOW}1. Open your router admin panel:${NC}"
echo "   http://$GATEWAY_IP"
echo ""
echo -e "${YELLOW}2. Find 'Port Forwarding' (or 'Virtual Server' / 'NAT'):${NC}"

case $ROUTER_TYPE in
    "Netgear")
        echo "   - Go to: Advanced → Advanced Setup → Port Forwarding"
        ;;
    "Linksys")
        echo "   - Go to: Security → Apps and Gaming → Single Port Forwarding"
        ;;
    "TP-Link")
        echo "   - Go to: Advanced → NAT Forwarding → Virtual Servers"
        ;;
    "ASUS")
        echo "   - Go to: WAN → Virtual Server / Port Forwarding"
        ;;
    "Comcast/Xfinity")
        echo "   - Go to: Advanced → Port Forwarding"
        ;;
    *)
        echo "   - Look for: Port Forwarding / NAT / Virtual Server in settings"
        ;;
esac

echo ""
echo -e "${YELLOW}3. Add this port forwarding rule:${NC}"
echo ""
echo "   ┌─────────────────────────────────────────┐"
echo "   │  External Port:    5001                 │"
echo "   │  Internal IP:      $LOCAL_IP           │"
echo "   │  Internal Port:    5001                 │"
echo "   │  Protocol:         TCP                  │"
echo "   │  Description:      Flask API            │"
echo "   └─────────────────────────────────────────┘"
echo ""

# Step 6: DNS configuration
print_dns_diagram

echo -e "${YELLOW}4. Configure DNS at your domain registrar:${NC}"
echo ""
echo "   Go to your domain registrar (Namecheap, GoDaddy, etc.) and add:"
echo ""
echo "   ┌─────────────────────────────────────────┐"
echo "   │  Type:    A                             │"
echo "   │  Name:    api                           │"
echo "   │  Value:   $PUBLIC_IP                    │"
echo "   │  TTL:     3600 (1 hour)                 │"
echo "   └─────────────────────────────────────────┘"
echo ""
echo -e "   This will make ${GREEN}api.cringeproof.com${NC} point to your IP"
echo ""

# Step 7: Testing
echo -e "${GREEN}Step 5: Testing (after DNS propagates - takes 5-60 minutes)${NC}"
echo ""
echo -e "${YELLOW}Test from external network:${NC}"
echo "   curl http://$PUBLIC_IP:5001/api/health"
echo ""
echo -e "${YELLOW}Test with domain (after DNS):${NC}"
echo "   curl http://api.cringeproof.com/api/health"
echo ""

# Step 8: Optional HTTPS with Let's Encrypt
echo -e "${GREEN}Step 6 (Optional): Enable HTTPS${NC}"
echo ""
echo "For HTTPS (https://api.cringeproof.com):"
echo ""
echo "1. Install certbot:"
echo "   sudo apt install certbot python3-certbot-nginx  # Linux"
echo "   brew install certbot  # Mac"
echo ""
echo "2. Get certificate:"
echo "   sudo certbot certonly --standalone -d api.cringeproof.com"
echo ""
echo "3. Update Flask to use SSL (or use nginx reverse proxy)"
echo ""

# Step 9: Dynamic IP warning
echo -e "${RED}⚠️  IMPORTANT: Dynamic IP Warning${NC}"
echo ""
echo "Most home internet has a DYNAMIC IP that changes occasionally."
echo "Your current IP: $PUBLIC_IP"
echo ""
echo "Options:"
echo "  1. Set up Dynamic DNS (DDNS) - see ddns_updater.py"
echo "  2. Use No-IP or DuckDNS (free DDNS services)"
echo "  3. Upgrade to business internet (static IP)"
echo ""

# Step 10: Security notes
echo -e "${YELLOW}🔒 Security Recommendations:${NC}"
echo ""
echo "  • Use HTTPS (not HTTP) in production"
echo "  • Add authentication to API endpoints"
echo "  • Enable firewall on your computer"
echo "  • Monitor access logs for suspicious activity"
echo "  • Consider rate limiting (flask-limiter)"
echo ""

# Step 11: Quick reference card
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     QUICK REFERENCE                        ║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC} Router Admin:    http://$GATEWAY_IP                      ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} Your Local IP:   $LOCAL_IP                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} Your Public IP:  $PUBLIC_IP                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} Flask Port:      5001                                    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} Domain:          api.cringeproof.com                     ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Save to file for reference
cat > port_forward_config.txt <<EOF
Router Port Forwarding Configuration
Generated: $(date)

Network Information:
  Local IP:     $LOCAL_IP
  Router IP:    $GATEWAY_IP
  Public IP:    $PUBLIC_IP
  Router Type:  $ROUTER_TYPE

Port Forward Rule:
  External Port:  5001
  Internal IP:    $LOCAL_IP
  Internal Port:  5001
  Protocol:       TCP

DNS Configuration:
  Type:   A
  Name:   api
  Value:  $PUBLIC_IP
  TTL:    3600

Router Admin:
  URL: http://$GATEWAY_IP

Testing Commands:
  curl http://$PUBLIC_IP:5001/api/health
  curl http://api.cringeproof.com/api/health
EOF

echo -e "${GREEN}✓ Configuration saved to port_forward_config.txt${NC}"
echo ""
echo -e "${CYAN}Done! Follow the steps above to expose your Flask API.${NC}"
echo ""

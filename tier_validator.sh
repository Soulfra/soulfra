#!/bin/bash
# Soulfra Tier Validator - Interactive validation of all network tiers
#
# This script walks you through testing each network tier:
# TIER 1: Localhost (127.0.0.1)
# TIER 2: LAN (192.168.x.x)
# TIER 3: Public IP
# TIER 4: Domain
#
# Usage:
#   chmod +x tier_validator.sh
#   ./tier_validator.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
BOLD='\033[1m'
RESET='\033[0m'

# Port
PORT=5001

# Progress tracking
TIER1_PASS=false
TIER2_PASS=false
TIER3_PASS=false
TIER4_PASS=false

# Helper functions
print_header() {
    echo ""
    echo -e "${BOLD}================================================================================${RESET}"
    echo -e "${BOLD}${BLUE}$1${RESET}"
    echo -e "${BOLD}================================================================================${RESET}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BOLD}${CYAN}▶ $1${RESET}"
    echo -e "${GRAY}────────────────────────────────────────────────────────────────────────────────${RESET}"
}

print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

print_error() {
    echo -e "${RED}✗ $1${RESET}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${RESET}"
}

print_info() {
    echo -e "${CYAN}→ $1${RESET}"
}

wait_for_user() {
    echo ""
    echo -e "${GRAY}Press Enter to continue...${RESET}"
    read
}

# Get local IP
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
    else
        # Linux
        LOCAL_IP=$(hostname -I | awk '{print $1}')
    fi

    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="Unable to detect"
    fi

    echo "$LOCAL_IP"
}

# Get public IP
get_public_ip() {
    PUBLIC_IP=$(curl -s https://api.ipify.org 2>/dev/null)

    if [ -z "$PUBLIC_IP" ]; then
        PUBLIC_IP="Unable to detect"
    fi

    echo "$PUBLIC_IP"
}

# Check if server is running
check_server() {
    local url=$1

    if curl -s -o /dev/null -w "%{http_code}" "$url" --connect-timeout 5 | grep -q "200\|302\|500"; then
        return 0  # Success
    else
        return 1  # Fail
    fi
}

# Main script
clear

print_header "SOULFRA TIER VALIDATOR"

echo -e "${GRAY}This interactive tool will help you validate each network tier step-by-step.${RESET}"
echo -e "${GRAY}We'll test in order: localhost → LAN → public IP → domain${RESET}"

wait_for_user

# ====================
# TIER 1: LOCALHOST
# ====================

print_header "TIER 1: LOCALHOST ACCESS"

print_section "Testing localhost (127.0.0.1:$PORT)"

echo -e "${CYAN}What this tests:${RESET}"
echo "  • Python is running"
echo "  • Flask is serving requests"
echo "  • Port $PORT is open"
echo "  • Basic application works"
echo ""

print_info "Testing http://localhost:$PORT ..."

if check_server "http://localhost:$PORT"; then
    print_success "Server is running on localhost!"
    TIER1_PASS=true

    echo ""
    print_info "Opening browser to localhost..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:$PORT" 2>/dev/null
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:$PORT" 2>/dev/null
    fi

    echo ""
    echo -e "${GREEN}${BOLD}✓ TIER 1 PASSED${RESET}"
    echo -e "${GRAY}Connection Point: app.py:app.run() → localhost:$PORT${RESET}"
else
    print_error "Server is not running on localhost!"

    echo ""
    echo -e "${YELLOW}How to fix:${RESET}"
    echo "  1. Start the server:   python3 app.py"
    echo "  2. Or use launcher:    ./start_soulfra.sh"
    echo "  3. Or use GUI:         python3 launcher.py"

    echo ""
    echo -e "${RED}${BOLD}✗ TIER 1 FAILED${RESET}"
    echo -e "${YELLOW}Fix localhost access before proceeding to next tier.${RESET}"

    wait_for_user
    exit 1
fi

wait_for_user

# ====================
# TIER 2: LAN ACCESS
# ====================

print_header "TIER 2: LAN ACCESS (Local Network)"

LOCAL_IP=$(get_local_ip)

print_section "Testing LAN IP ($LOCAL_IP:$PORT)"

echo -e "${CYAN}What this tests:${RESET}"
echo "  • Server bound to 0.0.0.0 (all interfaces)"
echo "  • LAN devices can access server"
echo "  • Network configuration correct"
echo "  • Firewall allows local connections"
echo ""

if [ "$LOCAL_IP" == "Unable to detect" ]; then
    print_warning "Could not detect local IP address"
    echo ""
    echo -e "${YELLOW}Skipping LAN test.${RESET}"
else
    print_info "Your LAN IP: $LOCAL_IP"
    print_info "Testing http://$LOCAL_IP:$PORT ..."

    if check_server "http://$LOCAL_IP:$PORT"; then
        print_success "Server is accessible on LAN!"
        TIER2_PASS=true

        echo ""
        echo -e "${GREEN}${BOLD}✓ TIER 2 PASSED${RESET}"
        echo -e "${GRAY}Connection Point: app.run(host='0.0.0.0') → LAN interface${RESET}"

        echo ""
        print_info "Test from another device on your network:"
        echo ""
        echo -e "${BOLD}  http://$LOCAL_IP:$PORT${RESET}"
        echo ""
        echo "  • Open this URL on your phone/tablet/other computer"
        echo "  • Make sure they're on the same WiFi network"
        echo "  • You should see the Soulfra interface"

    else
        print_error "Server is NOT accessible on LAN!"

        echo ""
        echo -e "${YELLOW}How to fix:${RESET}"
        echo "  1. Check app.py has:   app.run(host='0.0.0.0', port=$PORT)"
        echo "  2. Restart server after changing host setting"
        echo "  3. Check firewall allows port $PORT"

        echo ""
        echo -e "${YELLOW}${BOLD}⚠ TIER 2 FAILED${RESET}"
        echo -e "${GRAY}Localhost works but LAN access blocked.${RESET}"
    fi
fi

wait_for_user

# ====================
# TIER 3: PUBLIC IP
# ====================

print_header "TIER 3: PUBLIC IP ACCESS"

PUBLIC_IP=$(get_public_ip)

print_section "Testing Public IP ($PUBLIC_IP:$PORT)"

echo -e "${CYAN}What this tests:${RESET}"
echo "  • Router port forwarding configured"
echo "  • Public internet can reach your server"
echo "  • Firewall allows external connections"
echo "  • ISP doesn't block port $PORT"
echo ""

if [ "$PUBLIC_IP" == "Unable to detect" ]; then
    print_warning "Could not detect public IP address"
    echo ""
    echo -e "${YELLOW}Skipping public IP test.${RESET}"
else
    print_info "Your Public IP: $PUBLIC_IP"

    echo ""
    echo -e "${YELLOW}${BOLD}IMPORTANT:${RESET} ${YELLOW}This test requires router configuration!${RESET}"
    echo ""
    echo "To enable public IP access, configure port forwarding on your router:"
    echo ""
    echo -e "  ${CYAN}External Port:${RESET}  $PORT"
    echo -e "  ${CYAN}Internal IP:${RESET}    $LOCAL_IP"
    echo -e "  ${CYAN}Internal Port:${RESET}  $PORT"
    echo -e "  ${CYAN}Protocol:${RESET}       TCP"
    echo ""

    echo -e "${GRAY}Have you configured port forwarding? (y/n)${RESET}"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Testing http://$PUBLIC_IP:$PORT ..."

        # This test is tricky - we can't test from inside the network
        # We need external testing

        echo ""
        print_warning "Cannot reliably test from inside your network (NAT loopback)"
        echo ""
        echo "Please test from an external device:"
        echo ""
        echo -e "${BOLD}  1. Use your phone's cellular data (not WiFi)${RESET}"
        echo -e "${BOLD}  2. Visit: http://$PUBLIC_IP:$PORT${RESET}"
        echo ""
        echo "Or use an online port checker:"
        echo ""
        echo -e "${CYAN}  https://www.yougetsignal.com/tools/open-ports/${RESET}"
        echo -e "${GRAY}  Enter IP: $PUBLIC_IP, Port: $PORT${RESET}"
        echo ""

        echo -e "${GRAY}Did the external test work? (y/n)${RESET}"
        read -r external_test

        if [[ "$external_test" =~ ^[Yy]$ ]]; then
            print_success "Public IP access confirmed!"
            TIER3_PASS=true

            echo ""
            echo -e "${GREEN}${BOLD}✓ TIER 3 PASSED${RESET}"
            echo -e "${GRAY}Connection Point: Public IP → Router → LAN IP → Server${RESET}"
        else
            print_error "Public IP access not working"

            echo ""
            echo -e "${YELLOW}Common issues:${RESET}"
            echo "  1. Port forwarding not configured correctly"
            echo "  2. ISP blocks port $PORT (try a different port)"
            echo "  3. Router firewall blocking connections"
            echo "  4. Server not running or crashed"

            echo ""
            echo -e "${YELLOW}${BOLD}⚠ TIER 3 FAILED${RESET}"
        fi
    else
        print_warning "Skipping public IP test (port forwarding not configured)"
        echo ""
        echo -e "${YELLOW}To configure port forwarding:${RESET}"
        echo "  1. Access your router admin panel (usually 192.168.1.1)"
        echo "  2. Find 'Port Forwarding' or 'Virtual Server' settings"
        echo "  3. Add rule: External $PORT → $LOCAL_IP:$PORT"
        echo "  4. Save and restart router if needed"
    fi
fi

wait_for_user

# ====================
# TIER 4: DOMAIN
# ====================

print_header "TIER 4: DOMAIN ACCESS"

print_section "Testing Domain Name"

# Check if domain configured
if [ -f ".env" ]; then
    DOMAIN=$(grep "^DOMAIN=" .env | cut -d'=' -f2)
    BASE_URL=$(grep "^BASE_URL=" .env | cut -d'=' -f2)

    if [ -z "$DOMAIN" ] || [ "$DOMAIN" == "localhost" ]; then
        DOMAIN=""
    fi
else
    DOMAIN=""
fi

echo -e "${CYAN}What this tests:${RESET}"
echo "  • DNS records configured correctly"
echo "  • Domain resolves to your public IP"
echo "  • Full chain working: Domain → DNS → IP → Router → Server"
echo ""

if [ -z "$DOMAIN" ]; then
    print_warning "No domain configured in .env"

    echo ""
    echo -e "${YELLOW}To configure a domain:${RESET}"
    echo "  1. Register a domain (GoDaddy, Namecheap, etc.)"
    echo "  2. Add DNS A record:   yourdomain.com → $PUBLIC_IP"
    echo "  3. Add to .env:        DOMAIN=yourdomain.com"
    echo "  4. Add to .env:        BASE_URL=http://yourdomain.com"
    echo ""
    echo -e "${GRAY}Run: python3 dns_setup_guide.py for detailed instructions${RESET}"

    echo ""
    echo -e "${YELLOW}${BOLD}⊘ TIER 4 SKIPPED${RESET}"
else
    print_info "Configured domain: $DOMAIN"

    # Test DNS resolution
    print_info "Testing DNS resolution..."

    RESOLVED_IP=$(host "$DOMAIN" 2>/dev/null | grep "has address" | awk '{print $4}' | head -1)

    if [ -z "$RESOLVED_IP" ]; then
        print_error "Domain does not resolve to an IP!"

        echo ""
        echo -e "${YELLOW}How to fix:${RESET}"
        echo "  1. Add DNS A record at your registrar:"
        echo "     $DOMAIN → $PUBLIC_IP"
        echo "  2. Wait 5-60 minutes for DNS propagation"
        echo "  3. Verify: host $DOMAIN"

        echo ""
        echo -e "${RED}${BOLD}✗ TIER 4 FAILED (DNS)${RESET}"
    else
        print_success "Domain resolves to: $RESOLVED_IP"

        if [ "$RESOLVED_IP" == "$PUBLIC_IP" ]; then
            print_success "DNS points to your public IP!"
        else
            print_warning "DNS points to $RESOLVED_IP but your public IP is $PUBLIC_IP"
            echo ""
            echo -e "${YELLOW}Update your DNS A record to: $DOMAIN → $PUBLIC_IP${RESET}"
        fi

        # Test domain access
        print_info "Testing http://$DOMAIN ..."

        if check_server "http://$DOMAIN"; then
            print_success "Domain is accessible!"
            TIER4_PASS=true

            echo ""
            echo -e "${GREEN}${BOLD}✓ TIER 4 PASSED${RESET}"
            echo -e "${GRAY}Connection Point: $DOMAIN → DNS → $RESOLVED_IP → Server${RESET}"

            echo ""
            print_info "Opening browser to your domain..."

            if [[ "$OSTYPE" == "darwin"* ]]; then
                open "http://$DOMAIN" 2>/dev/null
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                xdg-open "http://$DOMAIN" 2>/dev/null
            fi

            echo ""
            echo -e "${GREEN}${BOLD}🎉 ALL TIERS COMPLETE!${RESET}"
            echo ""
            echo -e "${CYAN}Next steps:${RESET}"
            echo "  • Add SSL certificate for HTTPS"
            echo "  • Configure nginx for better performance"
            echo "  • Set up systemd service for auto-start"
        else
            print_error "Domain resolves but not accessible"

            echo ""
            echo -e "${YELLOW}Possible issues:${RESET}"
            echo "  1. Port forwarding not working (Tier 3 failed?)"
            echo "  2. Server not running"
            echo "  3. Firewall blocking connections"

            echo ""
            echo -e "${RED}${BOLD}✗ TIER 4 FAILED (Connection)${RESET}"
        fi
    fi
fi

wait_for_user

# ====================
# FINAL SUMMARY
# ====================

print_header "VALIDATION SUMMARY"

echo -e "${BOLD}Results:${RESET}"
echo ""

if $TIER1_PASS; then
    echo -e "  ${GREEN}✓ TIER 1: Localhost${RESET}         http://localhost:$PORT"
else
    echo -e "  ${RED}✗ TIER 1: Localhost${RESET}         http://localhost:$PORT"
fi

if $TIER2_PASS; then
    echo -e "  ${GREEN}✓ TIER 2: LAN${RESET}               http://$LOCAL_IP:$PORT"
else
    echo -e "  ${GRAY}✗ TIER 2: LAN${RESET}               http://$LOCAL_IP:$PORT"
fi

if $TIER3_PASS; then
    echo -e "  ${GREEN}✓ TIER 3: Public IP${RESET}         http://$PUBLIC_IP:$PORT"
else
    echo -e "  ${GRAY}✗ TIER 3: Public IP${RESET}         http://$PUBLIC_IP:$PORT"
fi

if $TIER4_PASS; then
    echo -e "  ${GREEN}✓ TIER 4: Domain${RESET}            http://$DOMAIN"
else
    echo -e "  ${GRAY}✗ TIER 4: Domain${RESET}            ${GRAY}(not configured)${RESET}"
fi

echo ""

# Current tier
if $TIER4_PASS; then
    echo -e "${GREEN}${BOLD}Current Status: TIER 4 - Production Ready!${RESET}"
elif $TIER3_PASS; then
    echo -e "${YELLOW}${BOLD}Current Status: TIER 3 - Public IP Working${RESET}"
    echo -e "${GRAY}Next: Configure DNS for domain access${RESET}"
elif $TIER2_PASS; then
    echo -e "${YELLOW}${BOLD}Current Status: TIER 2 - LAN Working${RESET}"
    echo -e "${GRAY}Next: Configure router port forwarding${RESET}"
elif $TIER1_PASS; then
    echo -e "${YELLOW}${BOLD}Current Status: TIER 1 - Localhost Only${RESET}"
    echo -e "${GRAY}Next: Change host to 0.0.0.0 for LAN access${RESET}"
else
    echo -e "${RED}${BOLD}Current Status: Not Working${RESET}"
    echo -e "${GRAY}Next: Start the server: python3 app.py${RESET}"
fi

echo ""
echo -e "${BOLD}================================================================================${RESET}"
echo ""

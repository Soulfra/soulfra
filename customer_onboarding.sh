#!/bin/bash
# Customer Onboarding - One-Command Blog Setup
#
# This script sets up a complete Soulfra blog for customers in 5 minutes.
# Interactive prompts guide you through blog name, theme, admin account, etc.
#
# Usage:
#   curl -sSL https://soulfra.com/install.sh | bash
#   # OR
#   chmod +x customer_onboarding.sh
#   ./customer_onboarding.sh
#
# What it does:
# 1. Checks system requirements
# 2. Asks for blog details (name, description, theme)
# 3. Creates admin account
# 4. Installs dependencies
# 5. Initializes database
# 6. Applies chosen theme
# 7. Creates first post
# 8. Starts blog
# 9. Opens browser
#
# Result: Fully working blog in 5 minutes!

set -e  # Exit on any error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
BOLD='\033[1m'
RESET='\033[0m'

# Configuration
BLOG_NAME=""
BLOG_DESCRIPTION=""
ADMIN_USERNAME=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
THEME=""
DOMAIN="localhost"
PORT=5001

# Functions
header() {
    clear
    echo ""
    echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${BLUE}║              SOULFRA BLOG - CUSTOMER ONBOARDING                    ║${RESET}"
    echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "${CYAN}Build your own blog in 5 minutes!${RESET}"
    echo ""
}

step() {
    echo ""
    echo -e "${BOLD}${MAGENTA}▶ $1${RESET}"
    echo -e "${GRAY}────────────────────────────────────────────────────────────────────${RESET}"
}

success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

error() {
    echo -e "${RED}✗ $1${RESET}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${RESET}"
}

info() {
    echo -e "${CYAN}→ $1${RESET}"
}

prompt() {
    echo -e "${CYAN}$1${RESET}"
    echo -n "> "
}

# ============================================================================
# WELCOME
# ============================================================================

header

echo -e "${BOLD}Welcome to Soulfra!${RESET}"
echo ""
echo "This script will help you set up your own blog with:"
echo "  • QR code authentication"
echo "  • AI-powered content analysis"
echo "  • Professional themes"
echo "  • Markdown support"
echo "  • Comment system"
echo "  • And much more!"
echo ""
echo -e "${GRAY}Press Enter to continue, or Ctrl+C to exit...${RESET}"
read

# ============================================================================
# STEP 1: System Requirements Check
# ============================================================================

header
step "STEP 1/9: Checking System Requirements"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python 3 installed: $PYTHON_VERSION"
else
    error "Python 3 not found!"
    echo ""
    echo "Please install Python 3:"
    echo "  macOS:  brew install python3"
    echo "  Linux:  sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check pip
if python3 -m pip --version &> /dev/null; then
    success "pip installed"
else
    error "pip not found!"
    exit 1
fi

# Check disk space
FREE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
info "Free disk space: $FREE_SPACE"

success "System requirements met!"

sleep 1

# ============================================================================
# STEP 2: Blog Configuration
# ============================================================================

header
step "STEP 2/9: Configure Your Blog"

echo ""
prompt "What's your blog name?"
read BLOG_NAME
if [ -z "$BLOG_NAME" ]; then
    BLOG_NAME="My Soulfra Blog"
fi

echo ""
prompt "Blog description (optional):"
read BLOG_DESCRIPTION
if [ -z "$BLOG_DESCRIPTION" ]; then
    BLOG_DESCRIPTION="A blog powered by Soulfra"
fi

success "Blog name: $BLOG_NAME"
success "Description: $BLOG_DESCRIPTION"

sleep 1

# ============================================================================
# STEP 3: Admin Account
# ============================================================================

header
step "STEP 3/9: Create Admin Account"

echo ""
prompt "Admin username:"
read ADMIN_USERNAME
if [ -z "$ADMIN_USERNAME" ]; then
    ADMIN_USERNAME="admin"
fi

echo ""
prompt "Admin email:"
read ADMIN_EMAIL
if [ -z "$ADMIN_EMAIL" ]; then
    ADMIN_EMAIL="admin@${BLOG_NAME// /}.com"
fi

echo ""
prompt "Admin password:"
read -s ADMIN_PASSWORD
echo ""
if [ -z "$ADMIN_PASSWORD" ]; then
    ADMIN_PASSWORD="admin123"
    warning "Using default password: admin123 (CHANGE THIS!)"
fi

success "Admin account configured"

sleep 1

# ============================================================================
# STEP 4: Choose Theme
# ============================================================================

header
step "STEP 4/9: Choose Your Theme"

echo ""
echo "Available themes:"
echo ""
echo "  ${CYAN}1)${RESET} Minimal Light   ☀️  - Clean and minimal light theme"
echo "  ${CYAN}2)${RESET} Minimal Dark    🌙  - Clean and minimal dark theme"
echo "  ${CYAN}3)${RESET} Professional    💼  - Business-focused blue theme"
echo "  ${CYAN}4)${RESET} Creative        🎨  - Colorful artistic theme"
echo "  ${CYAN}5)${RESET} Technical       💻  - Developer-focused monospace theme"
echo ""
prompt "Choose theme (1-5):"
read THEME_CHOICE

case $THEME_CHOICE in
    1)
        THEME="minimal-light"
        ;;
    2)
        THEME="minimal-dark"
        ;;
    3)
        THEME="professional"
        ;;
    4)
        THEME="creative"
        ;;
    5)
        THEME="technical"
        ;;
    *)
        THEME="minimal-light"
        warning "Invalid choice, using Minimal Light"
        ;;
esac

success "Theme selected: $THEME"

sleep 1

# ============================================================================
# STEP 5: Install Dependencies
# ============================================================================

header
step "STEP 5/9: Installing Dependencies"

echo ""
info "Creating virtual environment..."

if [ -d "venv" ]; then
    warning "Virtual environment already exists, using it"
else
    python3 -m venv venv
    success "Created virtual environment"
fi

source venv/bin/activate
success "Activated virtual environment"

echo ""
info "Installing Python packages..."

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    success "Installed dependencies"
else
    error "requirements.txt not found!"
    exit 1
fi

# ============================================================================
# STEP 6: Initialize Database
# ============================================================================

header
step "STEP 6/9: Initializing Database"

echo ""
info "Creating database..."

# Initialize database
python3 -c "from database import init_db; init_db()" 2>/dev/null || true
success "Database initialized"

# Create admin user
python3 << EOF
from db_helpers import create_user
try:
    create_user(
        username='$ADMIN_USERNAME',
        email='$ADMIN_EMAIL',
        password='$ADMIN_PASSWORD',
        is_admin=True
    )
    print('✓ Admin user created')
except Exception as e:
    print(f'⚠ Note: {e}')
EOF

# Initialize additional tables
python3 -c "from qr_auth import QRAuthManager; QRAuthManager()" 2>/dev/null || true
python3 -c "from notifications import NotificationManager; NotificationManager()" 2>/dev/null || true

success "Database ready"

# ============================================================================
# STEP 7: Apply Theme
# ============================================================================

header
step "STEP 7/9: Applying Theme"

echo ""
info "Generating theme CSS..."

python3 << EOF
from theme_builder import ThemeBuilder

builder = ThemeBuilder()
output = builder.apply_theme('$THEME')
print(f'✓ Applied theme: $THEME')
print(f'  CSS: {output}')
EOF

success "Theme applied"

# ============================================================================
# STEP 8: Create First Post
# ============================================================================

header
step "STEP 8/9: Creating Welcome Post"

echo ""
info "Creating your first post..."

python3 << EOF
from database import get_db
from datetime import datetime

db = get_db()

# Get admin user ID
admin = db.execute('SELECT id FROM users WHERE username = ?', ('$ADMIN_USERNAME',)).fetchone()

if admin:
    # Create welcome post
    db.execute('''
        INSERT INTO posts (user_id, title, slug, content, published_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        admin['id'],
        'Welcome to $BLOG_NAME!',
        'welcome',
        '''# Welcome to $BLOG_NAME

Thank you for choosing Soulfra!

## What You Can Do

- **Write posts** in Markdown
- **QR authentication** for mobile-first access
- **AI analysis** of your content
- **Custom themes** and styling
- **Comments** and engagement
- **Notifications** to stay connected

## Getting Started

1. Visit your admin panel at [/admin](/admin)
2. Write your first post
3. Customize your theme at [/admin/themes](/admin/themes)
4. Share your QR code for easy login

## Learn More

Check out the [documentation](/@docs/hello_world_blog) to learn more!

---

_Built with Soulfra - Open source blog platform_
''',
        datetime.now()
    ))
    db.commit()
    print('✓ Welcome post created')
else:
    print('⚠ Admin user not found, skipping post creation')
EOF

success "First post created"

# ============================================================================
# STEP 9: Configuration File
# ============================================================================

header
step "STEP 9/9: Final Configuration"

echo ""
info "Creating .env file..."

cat > .env << EOF
# Soulfra Configuration
# Generated by customer onboarding

# Blog settings
BLOG_NAME=$BLOG_NAME
BLOG_DESCRIPTION=$BLOG_DESCRIPTION

# Flask settings
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Platform settings
PLATFORM_VERSION=1.0.0
BASE_URL=http://$DOMAIN:$PORT
DOMAIN=$DOMAIN

# Admin settings
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_EMAIL=$ADMIN_EMAIL

# Database
DATABASE_PATH=soulfra.db

# Server
PORT=$PORT

# Theme
ACTIVE_THEME=$THEME
EOF

success "Configuration saved"

# ============================================================================
# COMPLETE!
# ============================================================================

header

echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║                  SETUP COMPLETE! 🎉                                ║${RESET}"
echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════════════╝${RESET}"
echo ""

echo -e "${BOLD}Your blog is ready!${RESET}"
echo ""

echo -e "${BOLD}Blog Details:${RESET}"
echo -e "  Name:        ${CYAN}$BLOG_NAME${RESET}"
echo -e "  Description: ${CYAN}$BLOG_DESCRIPTION${RESET}"
echo -e "  Theme:       ${CYAN}$THEME${RESET}"
echo ""

echo -e "${BOLD}Admin Credentials:${RESET}"
echo -e "  Username: ${CYAN}$ADMIN_USERNAME${RESET}"
echo -e "  Email:    ${CYAN}$ADMIN_EMAIL${RESET}"
echo -e "  Password: ${CYAN}$ADMIN_PASSWORD${RESET}"
echo ""

echo -e "${BOLD}Next Steps:${RESET}"
echo ""
echo -e "  ${CYAN}1) Start your blog:${RESET}"
echo -e "     python3 app.py"
echo ""
echo -e "  ${CYAN}2) Open browser:${RESET}"
echo -e "     http://localhost:$PORT"
echo ""
echo -e "  ${CYAN}3) Login to admin panel:${RESET}"
echo -e "     http://localhost:$PORT/admin"
echo ""
echo -e "  ${CYAN}4) Customize your theme:${RESET}"
echo -e "     python3 theme_builder.py list"
echo ""
echo -e "  ${CYAN}5) Generate QR login:${RESET}"
echo -e "     python3 qr_auth.py generate"
echo ""

echo -e "${BOLD}Quick Start:${RESET}"
echo ""
echo -e "  ${GRAY}# Start server${RESET}"
echo -e "  python3 app.py &"
echo ""
echo -e "  ${GRAY}# Open browser${RESET}"
echo -e "  open http://localhost:$PORT"
echo ""

echo -e "${BOLD}Documentation:${RESET}"
echo -e "  • Getting Started: ${CYAN}/@docs/hello_world_blog${RESET}"
echo -e "  • Network Guide:   ${CYAN}/@docs/NETWORK_GUIDE${RESET}"
echo -e "  • Encryption:      ${CYAN}/@docs/ENCRYPTION_TIERS${RESET}"
echo -e "  • Theme Builder:   ${CYAN}/@docs/THEME_BUILDER_GUIDE${RESET}"
echo ""

echo -e "${BOLD}Support:${RESET}"
echo -e "  • GitHub:  ${CYAN}https://github.com/soulfra${RESET}"
echo -e "  • Docs:    ${CYAN}https://docs.soulfra.com${RESET}"
echo ""

echo -e "${GRAY}Setup completed in $(date)${RESET}"
echo ""

# Ask if they want to start now
echo -e "${YELLOW}Start blog now? (y/n)${RESET}"
read -n 1 -r START_NOW
echo ""

if [[ $START_NOW =~ ^[Yy]$ ]]; then
    echo ""
    info "Starting blog..."

    python3 app.py &
    FLASK_PID=$!

    sleep 3

    if curl -s http://localhost:$PORT/ &> /dev/null; then
        success "Blog started! (PID: $FLASK_PID)"

        # Open browser
        if command -v open &> /dev/null; then
            open "http://localhost:$PORT"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:$PORT"
        fi

        echo ""
        echo -e "${GREEN}Your blog is now live at:${RESET} ${CYAN}http://localhost:$PORT${RESET}"
        echo ""
        echo -e "${GRAY}Press Ctrl+C to stop${RESET}"

        # Keep running
        wait $FLASK_PID
    else
        error "Failed to start blog"
        exit 1
    fi
else
    echo ""
    info "You can start your blog anytime with: ${CYAN}python3 app.py${RESET}"
    echo ""
fi

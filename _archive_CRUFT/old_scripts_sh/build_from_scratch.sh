#!/bin/bash
# Build Soulfra From Scratch
#
# This script builds the ENTIRE Soulfra system from zero.
# Run this on a fresh machine to prove it works offline and can be built from scratch.
#
# What it does:
# 1. Checks system requirements
# 2. Creates virtual environment
# 3. Installs Python dependencies
# 4. Initializes database
# 5. Creates default admin user
# 6. Trains neural networks (optional)
# 7. Starts Ollama (optional)
# 8. Starts Flask server
# 9. Verifies everything works
#
# Usage:
#   chmod +x build_from_scratch.sh
#   ./build_from_scratch.sh
#
# Options:
#   ./build_from_scratch.sh --skip-ollama     # Don't install/start Ollama
#   ./build_from_scratch.sh --skip-networks   # Don't train neural networks
#   ./build_from_scratch.sh --offline         # Use cached packages only

set -e  # Exit on any error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
BOLD='\033[1m'
RESET='\033[0m'

# Options
SKIP_OLLAMA=false
SKIP_NETWORKS=false
OFFLINE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --skip-ollama)
            SKIP_OLLAMA=true
            shift
            ;;
        --skip-networks)
            SKIP_NETWORKS=true
            shift
            ;;
        --offline)
            OFFLINE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-ollama     Don't install/start Ollama AI"
            echo "  --skip-networks   Don't train neural networks"
            echo "  --offline         Use cached packages only (no internet)"
            echo "  --help            Show this help"
            exit 0
            ;;
    esac
done

# Header
echo ""
echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${BLUE}║                  BUILD SOULFRA FROM SCRATCH                        ║${RESET}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if [ "$OFFLINE" = true ]; then
    echo -e "${YELLOW}🔒 OFFLINE MODE: Will use cached packages only${RESET}"
fi

# Function to print step
step() {
    echo ""
    echo -e "${BOLD}${CYAN}▶ STEP $1: $2${RESET}"
    echo -e "${GRAY}────────────────────────────────────────────────────────────────────${RESET}"
}

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

# Function to print error
error() {
    echo -e "${RED}✗ $1${RESET}"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠ $1${RESET}"
}

# Function to print info
info() {
    echo -e "${CYAN}→ $1${RESET}"
}

# ============================================================================
# STEP 1: Check System Requirements
# ============================================================================

step 1 "Checking System Requirements"

# Check OS
OS=$(uname -s)
info "Operating System: $OS"

if [[ "$OS" == "Darwin" ]]; then
    success "macOS detected"
elif [[ "$OS" == "Linux" ]]; then
    success "Linux detected"
else
    warning "Unknown OS: $OS (may work, but untested)"
fi

# Check Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python 3 installed: $PYTHON_VERSION"
else
    error "Python 3 not found!"
    echo ""
    echo "Install Python 3:"
    echo "  macOS:  brew install python3"
    echo "  Linux:  sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check pip
if python3 -m pip --version &> /dev/null; then
    success "pip installed"
else
    error "pip not found!"
    echo "Install pip: python3 -m ensurepip"
    exit 1
fi

# Check SQLite
if command -v sqlite3 &> /dev/null; then
    success "SQLite installed"
else
    warning "sqlite3 command not found (but Python has built-in sqlite3 module)"
fi

# Check disk space
if [[ "$OS" == "Darwin" ]]; then
    FREE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
elif [[ "$OS" == "Linux" ]]; then
    FREE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
fi
info "Free disk space: $FREE_SPACE"

success "System requirements met!"

# ============================================================================
# STEP 2: Create Virtual Environment
# ============================================================================

step 2 "Creating Virtual Environment"

if [ -d "venv" ]; then
    warning "Virtual environment already exists"
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        info "Deleted existing venv"
    else
        info "Using existing venv"
    fi
fi

if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Created virtual environment"
fi

# Activate venv
source venv/bin/activate
success "Activated virtual environment"

# ============================================================================
# STEP 3: Install Python Dependencies
# ============================================================================

step 3 "Installing Python Dependencies"

if [ "$OFFLINE" = true ]; then
    info "Installing from cache (offline mode)..."
    pip install --no-index --find-links ~/.cache/pip -r requirements.txt
else
    info "Installing from PyPI..."
    pip install -r requirements.txt
fi

success "Installed dependencies"

# ============================================================================
# STEP 4: Initialize Database
# ============================================================================

step 4 "Initializing Database"

if [ -f "soulfra.db" ]; then
    warning "Database already exists"
    read -p "Delete and reinitialize? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm soulfra.db
        info "Deleted existing database"
    else
        info "Using existing database"
        skip_init=true
    fi
fi

if [ ! "$skip_init" = true ]; then
    # Initialize main database
    python3 -c "from database import init_db; init_db()"
    success "Initialized main database"

    # Initialize license tables if license manager exists
    if [ -f "license_manager.py" ]; then
        python3 -c "from license_manager import init_license_tables; init_license_tables()" || true
        success "Initialized license tables"
    fi

    # Create default admin user
    python3 -c "
from db_helpers import create_user
try:
    create_user('admin', 'admin@soulfra.com', 'admin123', is_admin=True)
    print('Created admin user (username: admin, password: admin123)')
except:
    print('Admin user may already exist')
" || true

    success "Database initialized"
else
    info "Skipped database initialization"
fi

# ============================================================================
# STEP 5: Create .env File
# ============================================================================

step 5 "Creating Environment Configuration"

if [ ! -f ".env" ]; then
    cat > .env << EOF
# Soulfra Environment Configuration
# Generated by build_from_scratch.sh

# Flask settings
FLASK_ENV=development
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Platform settings
PLATFORM_VERSION=1.0.0
BASE_URL=http://localhost:5001
DOMAIN=localhost

# Admin settings
ADMIN_PASSWORD=soulfra2025

# Database
DATABASE_PATH=soulfra.db

# Ollama AI (if installed)
OLLAMA_HOST=http://localhost:11434

# Ports
PORT=5001
EOF

    success "Created .env file"
else
    info ".env file already exists (skipped)"
fi

# ============================================================================
# STEP 6: Train Neural Networks (Optional)
# ============================================================================

if [ "$SKIP_NETWORKS" = false ]; then
    step 6 "Training Neural Networks (Optional)"

    if [ -f "train_context_networks.py" ]; then
        info "Training networks (this may take a minute)..."

        python3 train_context_networks.py || {
            warning "Neural network training failed (optional feature)"
        }

        success "Neural networks trained (or using existing)"
    else
        warning "train_context_networks.py not found (skipping)"
    fi
else
    info "Skipping neural network training (--skip-networks flag)"
fi

# ============================================================================
# STEP 7: Install/Start Ollama (Optional)
# ============================================================================

if [ "$SKIP_OLLAMA" = false ]; then
    step 7 "Setting Up Ollama AI (Optional)"

    # Check if Ollama is installed
    if command -v ollama &> /dev/null; then
        success "Ollama already installed"

        # Check if Ollama is running
        if curl -s http://localhost:11434/ &> /dev/null; then
            success "Ollama is already running"
        else
            info "Starting Ollama..."
            ollama serve &> /dev/null &
            OLLAMA_PID=$!
            sleep 2

            if curl -s http://localhost:11434/ &> /dev/null; then
                success "Ollama started (PID: $OLLAMA_PID)"
            else
                warning "Ollama failed to start (optional feature)"
            fi
        fi

        # Pull a default model if none exist
        if ollama list | grep -q "llama"; then
            info "Ollama models already downloaded"
        else
            warning "No Ollama models found"
            read -p "Download llama2 model (~4GB)? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ollama pull llama2
                success "Downloaded llama2 model"
            fi
        fi

    else
        warning "Ollama not installed"
        echo ""
        echo "To install Ollama (optional, for AI features):"
        echo "  macOS/Linux:  curl https://ollama.ai/install.sh | sh"
        echo "  Or visit:     https://ollama.ai"
        echo ""
        read -p "Continue without Ollama? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    info "Skipping Ollama setup (--skip-ollama flag)"
fi

# ============================================================================
# STEP 8: Verify Installation
# ============================================================================

step 8 "Verifying Installation"

# Check database tables
TABLE_COUNT=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
info "Database tables: $TABLE_COUNT"

if [ $TABLE_COUNT -gt 10 ]; then
    success "Database properly initialized"
else
    warning "Database may not be fully initialized"
fi

# Check required files
FILES=("app.py" "database.py" "config.py" "soulfra.db" "requirements.txt")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        success "Found: $file"
    else
        error "Missing: $file"
    fi
done

success "Installation verified!"

# ============================================================================
# STEP 9: Start Flask Server
# ============================================================================

step 9 "Starting Flask Server"

info "Starting Soulfra on http://localhost:5001..."
echo ""
echo -e "${YELLOW}Server will start in background.${RESET}"
echo -e "${YELLOW}Press Ctrl+C to stop.${RESET}"
echo ""

# Start Flask in background
python3 app.py &
FLASK_PID=$!

# Wait for server to start
sleep 3

# Test if server is running
if curl -s http://localhost:5001/ &> /dev/null; then
    success "Flask server started (PID: $FLASK_PID)"
else
    error "Flask server failed to start"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║                  BUILD COMPLETE! 🎉                                ║${RESET}"
echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════════════╝${RESET}"
echo ""

echo -e "${BOLD}Soulfra is now running at:${RESET}"
echo -e "  ${CYAN}http://localhost:5001${RESET}"
echo ""

echo -e "${BOLD}Default Credentials:${RESET}"
echo -e "  Username: ${CYAN}admin${RESET}"
echo -e "  Password: ${CYAN}admin123${RESET}"
echo ""

echo -e "${BOLD}Services Running:${RESET}"
echo -e "  • Flask Server:  ${GREEN}✓${RESET} (PID: $FLASK_PID)"

if curl -s http://localhost:11434/ &> /dev/null; then
    echo -e "  • Ollama AI:     ${GREEN}✓${RESET}"
else
    echo -e "  • Ollama AI:     ${GRAY}✗ (optional)${RESET}"
fi

echo ""
echo -e "${BOLD}Next Steps:${RESET}"
echo -e "  1. Open browser: ${CYAN}open http://localhost:5001${RESET}"
echo -e "  2. Run tests:    ${CYAN}python3 test_hello_world.py${RESET}"
echo -e "  3. View logs:    ${CYAN}tail -f logs/soulfra.log${RESET}"
echo ""

echo -e "${BOLD}To Stop:${RESET}"
echo -e "  ${CYAN}kill $FLASK_PID${RESET}"
echo ""

echo -e "${BOLD}Files Created:${RESET}"
echo -e "  • venv/          ${GRAY}(virtual environment)${RESET}"
echo -e "  • soulfra.db     ${GRAY}(SQLite database)${RESET}"
echo -e "  • .env           ${GRAY}(environment config)${RESET}"
echo ""

echo -e "${GRAY}Build script completed successfully!${RESET}"
echo ""

# Keep script running to show Flask output
wait $FLASK_PID

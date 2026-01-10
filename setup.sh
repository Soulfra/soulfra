#!/bin/bash
# Setup Script - First-Time Installation

echo ""
echo "🚀 Soulfra Setup - Creative Onboarding + File Import System"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# DEPENDENCIES
# ==============================================================================

echo "📦 Checking dependencies..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "   ✓ Python 3 found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip"
    exit 1
fi

echo "   ✓ pip3 found"

# ==============================================================================
# INSTALL PYTHON PACKAGES
# ==============================================================================

echo ""
echo "📥 Installing Python packages..."
echo ""

# Core packages (required)
pip3 install flask requests pyyaml &> /dev/null
echo "   ✓ Core packages installed (flask, requests, pyyaml)"

# Optional packages
echo ""
echo "Installing optional packages..."

# Document parsing
pip3 install python-docx beautifulsoup4 markdown2 &> /dev/null
echo "   ✓ Document parsers (python-docx, beautifulsoup4, markdown2)"

# QR codes
pip3 install qrcode pillow &> /dev/null
echo "   ✓ QR code generator (qrcode, pillow)"

# Folder watching
pip3 install watchdog &> /dev/null
echo "   ✓ Folder watcher (watchdog)"

# OCR (optional - for draw challenges)
if command -v tesseract &> /dev/null; then
    pip3 install pytesseract &> /dev/null
    echo "   ✓ OCR support (pytesseract)"
else
    echo "   ⚠ Tesseract not found - OCR challenges disabled"
    echo "     Install: brew install tesseract (macOS) or apt install tesseract-ocr (Linux)"
fi

# ==============================================================================
# CREATE DIRECTORIES
# ==============================================================================

echo ""
echo "📁 Creating directories..."
echo ""

mkdir -p brands
mkdir -p uploads
mkdir -p output
mkdir -p static/qr
mkdir -p logs

echo "   ✓ brands/    - Imported files"
echo "   ✓ uploads/   - Temporary uploads"
echo "   ✓ output/    - Static exports"
echo "   ✓ static/qr/ - QR codes"
echo "   ✓ logs/      - Application logs"

# ==============================================================================
# DATABASE SETUP
# ==============================================================================

echo ""
echo "🗄️  Setting up database..."
echo ""

python3 migrate_onboarding_system.py

# ==============================================================================
# OPTIONAL: GITHUB OAUTH
# ==============================================================================

echo ""
echo "🔐 GitHub OAuth Setup (Optional)"
echo "=================================="
echo ""
echo "Do you want to set up GitHub OAuth? (y/n)"
echo "(Only needed for public sites with user authentication)"
read -r setup_github

if [ "$setup_github" = "y" ]; then
    echo ""
    echo "📝 You'll need to create a GitHub OAuth app:"
    echo "   1. Go to: https://github.com/settings/developers"
    echo "   2. Click 'New OAuth App'"
    echo "   3. Fill in:"
    echo "      - Application name: Your Brand Name"
    echo "      - Homepage URL: http://localhost:5001"
    echo "      - Callback URL: http://localhost:5001/github/callback"
    echo ""
    echo "Enter your GitHub Client ID (or press Enter to skip):"
    read -r client_id

    if [ -n "$client_id" ]; then
        echo "Enter your GitHub Client Secret:"
        read -r client_secret

        # Create .env file
        cat > .env << EOF
# GitHub OAuth Configuration
export GITHUB_CLIENT_ID=$client_id
export GITHUB_CLIENT_SECRET=$client_secret
export GITHUB_REDIRECT_URI=http://localhost:5001/github/callback
EOF

        echo ""
        echo "   ✓ GitHub OAuth configured"
        echo "   ✓ Settings saved to .env"
        echo ""
        echo "To activate: source .env"
    fi
else
    echo "   ⚠ Skipping GitHub OAuth (you can set up later)"
fi

# ==============================================================================
# CREATE SAMPLE FILE
# ==============================================================================

echo ""
echo "📝 Creating sample file..."
echo ""

cat > sample-note.md << 'EOF'
---
title: Sample Note
author: You
tags: sample, demo, test
---

# Welcome to Your Personal File System

This is a sample note. Import it with:

```bash
python3 file_importer.py --import sample-note.md --brand me --category notes
```

Then access it at:
- Local: http://localhost:5001/@me/notes/sample-note
- Phone: http://YOUR_IP:5001/@me/notes/sample-note

## Features

- Import any file format (txt, md, html, doc, json, etc.)
- Organize with @brand/category/file routing
- Access from phone via LAN
- Optional: Make it public with GitHub OAuth

## Next Steps

1. Import your own files
2. Access via localhost or LAN
3. Organize with @brand syntax
EOF

echo "   ✓ Created sample-note.md"

# ==============================================================================
# SUMMARY
# ==============================================================================

echo ""
echo "=========================================================="
echo "✅ Setup Complete!"
echo "=========================================================="
echo ""
echo "🎯 What You Can Do Now:"
echo ""
echo "1️⃣  Try the sample file:"
echo "   python3 file_importer.py --import sample-note.md --brand me --category notes"
echo ""
echo "2️⃣  Start the server:"
echo "   python3 app.py"
echo ""
echo "3️⃣  Access your files:"
echo "   http://localhost:5001/@me/notes/sample-note"
echo ""
echo "4️⃣  Access from phone (same WiFi):"
echo "   Find your IP: ifconfig | grep 'inet ' | grep -v 127.0.0.1"
echo "   Open: http://YOUR_IP:5001"
echo ""
echo "📚 For more help, see:"
echo "   - QUICK_START.md - Usage guide"
echo "   - CREATIVE_ONBOARDING_FLOW.md - Complete documentation"
echo ""
echo "🔧 Optional Tools:"
echo ""
echo "   Watch folder (auto-import):"
echo "   python3 watch_folder.py ~/Desktop/sync/"
echo ""
echo "   Process through pipeline (with AI enrichment):"
echo "   python3 content_pipeline.py --process file.md --brand me --category notes"
echo ""
echo "=========================================================="
echo ""

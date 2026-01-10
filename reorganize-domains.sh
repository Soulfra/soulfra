#!/bin/bash

# Reorganize Soulfra domains on Desktop
# Creates one folder per domain, each as a GitHub repo

DESKTOP="/Users/matthewmauer/Desktop"
SOURCE="/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple"

echo "🔧 Reorganizing domains on Desktop..."
echo ""

# Get list of domains from database
DOMAINS=$(sqlite3 "$SOURCE/soulfra.db" "SELECT slug FROM brands WHERE domain IS NOT NULL ORDER BY id;")

# Create each domain folder on Desktop
for domain in $DOMAINS; do
    DOMAIN_DIR="$DESKTOP/${domain}.com"

    echo "📁 Setting up $domain.com..."

    # Create domain directory if it doesn't exist
    if [ ! -d "$DOMAIN_DIR" ]; then
        mkdir -p "$DOMAIN_DIR"
    fi

    # Copy voice-archive template as base
    if [ ! -f "$DOMAIN_DIR/index.html" ]; then
        cp "$SOURCE/voice-archive/index.html" "$DOMAIN_DIR/"
        cp -r "$SOURCE/voice-archive/static" "$DOMAIN_DIR/" 2>/dev/null || true
        cp -r "$SOURCE/voice-archive/css" "$DOMAIN_DIR/" 2>/dev/null || true
        cp "$SOURCE/voice-archive/soulfra-fingerprint.js" "$DOMAIN_DIR/" 2>/dev/null || true
        cp "$SOURCE/voice-archive/_footer.html" "$DOMAIN_DIR/" 2>/dev/null || true
        cp -r "$SOURCE/voice-archive/_includes" "$DOMAIN_DIR/" 2>/dev/null || true
    fi

    # Create CNAME file
    echo "${domain}.com" > "$DOMAIN_DIR/CNAME"

    # Initialize git if not already
    if [ ! -d "$DOMAIN_DIR/.git" ]; then
        cd "$DOMAIN_DIR"
        git init
        git add .
        git commit -m "Initial commit for ${domain}.com"
        echo "✅ Git initialized"
    fi

    echo "   CNAME: ${domain}.com"
    echo "   Path: $DOMAIN_DIR"
    echo ""
done

echo "✨ Done! Created domain folders on Desktop:"
echo ""
ls -d "$DESKTOP"/*.com 2>/dev/null || echo "No .com folders found"
echo ""
echo "Next steps:"
echo "1. cd ~/Desktop/{domain}.com"
echo "2. gh repo create {domain}.com --public --source=. --remote=origin --push"
echo "3. Enable GitHub Pages on each repo"

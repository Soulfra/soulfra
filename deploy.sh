#!/bin/bash
# Deploy Script - Push Local Changes to GitHub Pages
# Usage: ./deploy.sh "commit message"

set -e  # Exit on error

COMMIT_MSG="${1:-Update site}"
GITHUB_REPO="https://github.com/Soulfra/soulfra.git"
DEPLOY_DIR="output/soulfra"

echo "🚀 Soulfra Deployment Script"
echo "======================================"
echo ""

# Check if deploy directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ Deploy directory not found: $DEPLOY_DIR"
    echo "Creating it now..."
    mkdir -p "$DEPLOY_DIR"
fi

# Check if it's a git repo
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    echo "📦 Initializing git repository..."
    cd "$DEPLOY_DIR"
    git init
    git remote add origin "$GITHUB_REPO"
    git branch -M main
    cd ../..
else
    echo "✅ Git repository exists"
fi

# Copy files to deploy directory
echo ""
echo "📋 Copying files to deploy directory..."

# Copy main HTML files
cp -v *.html "$DEPLOY_DIR/" 2>/dev/null || echo "  (No HTML files to copy)"

# Copy CSS files
if [ -d "css" ]; then
    cp -rv css "$DEPLOY_DIR/" 2>/dev/null || true
fi

# Copy JS files
if [ -d "js" ]; then
    cp -rv js "$DEPLOY_DIR/" 2>/dev/null || true
fi

# Copy keyboard shortcuts
cp -v keyboard-shortcuts.js "$DEPLOY_DIR/" 2>/dev/null || true

# Copy CNAME for custom domain
if [ -f "CNAME" ]; then
    cp -v CNAME "$DEPLOY_DIR/"
else
    echo "soulfra.com" > "$DEPLOY_DIR/CNAME"
    echo "  Created CNAME file"
fi

# Navigate to deploy directory
cd "$DEPLOY_DIR"

# Check git status
echo ""
echo "📊 Git status:"
git status --short

# Add all changes
echo ""
echo "➕ Adding changes..."
git add .

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo ""
    echo "⚠️  No changes to deploy"
    cd ../..
    exit 0
fi

# Commit changes
echo ""
echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git push -u origin main

cd ../..

echo ""
echo "======================================"
echo "✅ Deployment successful!"
echo ""
echo "🌐 Your site will be live at:"
echo "   https://soulfra.com"
echo ""
echo "⏱️  GitHub Pages typically updates in 2-5 minutes"
echo ""
echo "🔍 Check deployment status:"
echo "   https://github.com/Soulfra/soulfra/actions"
echo "======================================"

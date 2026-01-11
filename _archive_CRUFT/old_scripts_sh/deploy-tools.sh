#!/bin/bash
#
# Deploy Tools to Live Site (soulfra.com)
#
# Runs all generators and deploys reports to GitHub Pages
#
# Usage:
#     ./deploy-tools.sh               # Deploy all
#     ./deploy-tools.sh --debug-only  # Debug only
#     ./deploy-tools.sh --brand-only  # Brand only
#     ./deploy-tools.sh --ccna-only   # CCNA only
#

set -e  # Exit on error

echo "🚀 Deploy Tools to soulfra.com"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Run this from the soulfra-simple root directory"
    exit 1
fi

# Create tools directory structure
echo "📁 Creating tools directory structure..."
mkdir -p output/soulfra/tools/debug
mkdir -p output/soulfra/tools/brand
mkdir -p output/soulfra/tools/ccna
mkdir -p output/soulfra/blog

# Parse arguments
DEBUG_ONLY=false
BRAND_ONLY=false
CCNA_ONLY=false

if [ "$1" == "--debug-only" ]; then
    DEBUG_ONLY=true
elif [ "$1" == "--brand-only" ]; then
    BRAND_ONLY=true
elif [ "$1" == "--ccna-only" ]; then
    CCNA_ONLY=true
fi

# 1. Generate System Debug Reports
if [ "$DEBUG_ONLY" == "true" ] || [ "$BRAND_ONLY" == "false" ] && [ "$CCNA_ONLY" == "false" ]; then
    echo ""
    echo "🔍 Generating system debug reports..."
    python3 debug_system.py --routes

    # Copy to deployment directory
    if [ -f "data/system_debug/routes.html" ]; then
        echo "   ✅ Copying system debug reports..."
        cp data/system_debug/*.html output/soulfra/tools/debug/ 2>/dev/null || true
        cp data/system_debug/*.md output/soulfra/tools/debug/ 2>/dev/null || true
        cp data/system_debug/*.json output/soulfra/tools/debug/ 2>/dev/null || true
    else
        echo "   ⚠️  System debug reports not found"
    fi
fi

# 2. Generate Brand Analysis
if [ "$BRAND_ONLY" == "true" ] || [ "$DEBUG_ONLY" == "false" ] && [ "$CCNA_ONLY" == "false" ]; then
    echo ""
    echo "📊 Generating brand analysis..."
    python3 brand_mapper.py

    # Copy to deployment directory
    if [ -f "data/brand_analysis/brand_comparison.html" ]; then
        echo "   ✅ Copying brand analysis reports..."
        cp data/brand_analysis/*.html output/soulfra/tools/brand/ 2>/dev/null || true
        cp data/brand_analysis/*.md output/soulfra/tools/brand/ 2>/dev/null || true
        cp data/brand_analysis/*.csv output/soulfra/tools/brand/ 2>/dev/null || true
        cp data/brand_analysis/*.json output/soulfra/tools/brand/ 2>/dev/null || true
    else
        echo "   ⚠️  Brand analysis reports not found"
    fi
fi

# 3. Generate CCNA Study Graphs
if [ "$CCNA_ONLY" == "true" ] || [ "$DEBUG_ONLY" == "false" ] && [ "$BRAND_ONLY" == "false" ]; then
    echo ""
    echo "🌐 Generating CCNA study graphs..."
    python3 ccna_study.py

    # Copy to deployment directory
    if [ -f "data/ccna_study/ccna_concept_graph.html" ]; then
        echo "   ✅ Copying CCNA study reports..."
        cp data/ccna_study/*.html output/soulfra/tools/ccna/ 2>/dev/null || true
        cp data/ccna_study/*.md output/soulfra/tools/ccna/ 2>/dev/null || true
        cp data/ccna_study/*.json output/soulfra/tools/ccna/ 2>/dev/null || true
    else
        echo "   ⚠️  CCNA study reports not found"
    fi
fi

# 4. Build Content (Blog Posts)
if [ "$DEBUG_ONLY" == "false" ] && [ "$BRAND_ONLY" == "false" ] && [ "$CCNA_ONLY" == "false" ]; then
    echo ""
    echo "🏗️  Building content..."
    python3 build-content.py

    # Copy to deployment directory
    if [ -f "dist/index.html" ]; then
        echo "   ✅ Copying blog content..."
        cp -r dist/* output/soulfra/blog/ 2>/dev/null || true
    else
        echo "   ⚠️  Blog content not found"
    fi
fi

# 5. Copy debug.html if it doesn't exist
if [ ! -f "output/soulfra/debug.html" ]; then
    echo ""
    echo "📝 Creating debug.html..."
    # It should already exist, but this is a safety check
    if [ -f "output/soulfra/debug.html" ]; then
        echo "   ✅ debug.html exists"
    else
        echo "   ⚠️  debug.html not found - run this script from project root"
    fi
fi

# 6. Update index.html in output/soulfra if needed
if [ -f "index.html" ]; then
    echo ""
    echo "📋 Updating index.html..."
    cp index.html output/soulfra/index.html
    echo "   ✅ index.html copied"
fi

# 7. Commit and push to trigger GitHub Pages deployment
echo ""
echo "📤 Deploying to GitHub Pages..."
cd output/soulfra

# Check if git repo
if [ ! -d ".git" ]; then
    echo "   ⚠️  Not a git repository - initializing..."
    git init
    git remote add origin https://github.com/matthewmauer/soulfra-simple.git
fi

# Stage all changes
git add .

# Commit
if git diff-index --quiet HEAD --; then
    echo "   ℹ️  No changes to commit"
else
    git commit -m "Deploy tools: $(date +'%Y-%m-%d %H:%M:%S')"
    echo "   ✅ Changes committed"

    # Pull and push
    echo "   Syncing with remote..."
    if git pull --rebase origin main; then
        echo "   ✅ Synced with remote"
    else
        echo "   ⚠️  Rebase failed - resolve conflicts manually"
        exit 1
    fi

    echo "   Pushing to GitHub..."
    if git push origin main; then
        echo "   ✅ Pushed to GitHub"
    else
        echo "   ⚠️  Push failed - check remote"
        exit 1
    fi
fi

cd ../..

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Live URLs:"
echo "   soulfra.com/debug.html          - Debug dashboard"
echo "   soulfra.com/tools/debug/        - System reports"
echo "   soulfra.com/tools/brand/        - Brand analysis"
echo "   soulfra.com/tools/ccna/         - CCNA graphs"
echo "   soulfra.com/blog/               - Blog posts"
echo ""
echo "⏱️  GitHub Pages deploy takes ~30 seconds"
echo "📱 Mobile friendly - works on iPhone!"
echo ""

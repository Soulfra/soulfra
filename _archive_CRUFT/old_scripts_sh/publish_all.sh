#!/bin/bash
# Publish Everywhere - Master Script
# Usage: ./publish_all.sh [brand]

set -e  # Exit on error

BRAND=${1:-Soulfra}
DRY_RUN=${2:-false}

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         SOULFRA MASTER PUBLISHER                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Publishing brand: $BRAND"
echo "🔧 Dry run: $DRY_RUN"
echo ""

# Step 1: Export to static HTML
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Step 1: Export to Static HTML"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 export_static.py --brand $BRAND || {
    echo "❌ Export failed!"
    exit 1
}
echo "✅ Export complete"
echo ""

# Step 2: Publish to IPFS (if installed)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Step 2: Publish to IPFS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v ipfs &> /dev/null; then
    if [ "$DRY_RUN" = "true" ]; then
        python3 publish_ipfs.py --brand $BRAND --dry-run || {
            echo "⚠️  IPFS publish failed (continuing...)"
        }
    else
        python3 publish_ipfs.py --brand $BRAND || {
            echo "⚠️  IPFS publish failed (continuing...)"
        }
    fi
    echo "✅ IPFS publish complete"
else
    echo "⚠️  IPFS not installed (skipping)"
    echo "   Install with: brew install ipfs"
fi
echo ""

# Step 3: Cross-post to all platforms
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 Step 3: Cross-Post to All Platforms"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$DRY_RUN" = "true" ]; then
    python3 publish_everywhere.py --latest --brand $BRAND --dry-run || {
        echo "⚠️  Cross-posting failed (continuing...)"
    }
else
    python3 publish_everywhere.py --latest --brand $BRAND || {
        echo "⚠️  Cross-posting failed (continuing...)"
    }
fi
echo "✅ Cross-posting complete"
echo ""

# Step 4: Git commit + push (optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Step 4: Git Backup (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
OUTPUT_DIR="output/$BRAND"

if [ -d "$OUTPUT_DIR/.git" ]; then
    cd "$OUTPUT_DIR"

    # Check if there are changes
    if [ -n "$(git status --porcelain)" ]; then
        if [ "$DRY_RUN" = "true" ]; then
            echo "🔍 Would commit and push changes (dry run)"
            git status --short
        else
            git add .
            git commit -m "Update $BRAND content

🤖 Auto-published via publish_all.sh
$(date '+%Y-%m-%d %H:%M:%S')

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>" || {
                echo "⚠️  Nothing to commit"
            }

            git push || {
                echo "⚠️  Git push failed (continuing...)"
            }
            echo "✅ Git backup complete"
        fi
    else
        echo "✅ No changes to commit"
    fi

    cd - > /dev/null
else
    echo "⚠️  Not a git repository (skipping)"
fi
echo ""

# Step 5: Syncthing status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Step 5: Syncthing Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -s http://localhost:8384/rest/system/status > /dev/null 2>&1; then
    echo "✅ Syncthing is running"
    echo "📡 Syncing to phones (~30 seconds)..."
    echo "   Dashboard: http://localhost:8384"
else
    echo "⚠️  Syncthing not running"
    echo "   Start with: syncthing &"
fi
echo ""

# Summary
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    PUBLISH COMPLETE                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "   ✅ Static HTML exported"
echo "   🌐 IPFS published (if installed)"
echo "   📤 Cross-posted to platforms (if configured)"
echo "   📦 Git backup (if configured)"
echo "   🔄 Syncthing syncing to phones"
echo ""
echo "🌍 Your content is now live on:"
echo "   - Local: http://localhost:5001/local-site/$BRAND/"
echo "   - IPFS: https://ipfs.io/ipfs/[your-hash]"
echo "   - Phone 1: http://[phone-ip]:8000"
echo "   - Phone 2: http://[phone-ip]:8000"
if [ "$BRAND" = "Soulfra" ]; then
    echo "   - Domain: https://soulfra.com (if DNS configured)"
fi
echo ""
if [ "$DRY_RUN" = "true" ]; then
    echo "⚠️  DRY RUN - No actual publishing occurred"
    echo "   Run without --dry-run to publish for real"
fi

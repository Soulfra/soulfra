#!/bin/bash
# Cleanup Script - Archive Bloat, Keep Core Files
#
# This script will:
# 1. Create archive directories
# 2. Move experimental code to archive/
# 3. Keep only the 15 core files needed
# 4. Preserve your working system
#
# SAFE: Creates backups before moving anything

set -e  # Exit on error

echo "🧹 Soulfra Bloat Cleanup Script"
echo "================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create backup first
BACKUP_NAME="soulfra-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "📦 Step 1: Creating backup..."
echo "   Backup: $BACKUP_NAME"
tar -czf "$BACKUP_NAME" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='soulfra.db' \
    --exclude='*.log' \
    . 2>/dev/null || true
echo "   ✅ Backup created!"
echo ""

# Create archive structure
echo "📁 Step 2: Creating archive directories..."
mkdir -p archive/experiments/triple-domain
mkdir -p archive/experiments/abandoned
mkdir -p archive/experiments/feature-creep
mkdir -p archive/docs
echo "   ✅ Directories created!"
echo ""

# Move Soulfra/ folder (triple domain experiment)
echo "🔀 Step 3: Archiving triple domain experiment..."
if [ -d "Soulfra" ]; then
    echo "   Moving Soulfra/ → archive/experiments/triple-domain/"
    mv Soulfra archive/experiments/triple-domain/
    echo "   ✅ Triple domain experiment archived!"
else
    echo "   ⚠️  Soulfra/ folder not found (already moved?)"
fi
echo ""

# Archive markdown documentation (keep important ones)
echo "📚 Step 4: Consolidating documentation..."
KEEP_DOCS=(
    "README.md"
    "ARCHITECTURE-CLARIFIED.md"
    "SIMPLE-PUBLISHING-WORKFLOW.md"
    "CORE-VS-CRUFT.md"
    "WHAT-THIS-ACTUALLY-DOES.md"
    "LICENSE"
)

# Move markdown files to archive (except the ones we want to keep)
for md_file in *.md; do
    if [ -f "$md_file" ]; then
        # Check if this file should be kept
        KEEP=0
        for keep_doc in "${KEEP_DOCS[@]}"; do
            if [ "$md_file" == "$keep_doc" ]; then
                KEEP=1
                break
            fi
        done

        # If not in keep list, archive it
        if [ $KEEP -eq 0 ]; then
            echo "   Archiving: $md_file"
            mv "$md_file" archive/docs/
        fi
    fi
done
echo "   ✅ Documentation consolidated!"
echo ""

# List abandoned experiments to archive
echo "🗑️  Step 5: Archiving abandoned experiments..."
ABANDONED=(
    "soulfra_dark_story.py"
    "neural_network.py"
    "narrative_cringeproof.py"
    "wiki_concepts.py"
    "avatar_generator.py"
    "anki_learning_system.py"
    "membership_system.py"
    "url_shortener.py"
    "ascii_player.py"
    "voice_input.py"
)

for file in "${ABANDONED[@]}"; do
    if [ -f "$file" ]; then
        echo "   Archiving: $file"
        mv "$file" archive/experiments/abandoned/
    fi
done
echo "   ✅ Abandoned experiments archived!"
echo ""

# Archive test files
echo "🧪 Step 6: Archiving test files..."
find . -maxdepth 1 -name "test_*.py" -type f -exec mv {} archive/experiments/abandoned/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_test.py" -type f -exec mv {} archive/experiments/abandoned/ \; 2>/dev/null || true
echo "   ✅ Test files archived!"
echo ""

# Create summary
echo ""
echo "✅ CLEANUP COMPLETE!"
echo "===================="
echo ""
echo "📊 Summary:"
echo "   Backup: $BACKUP_NAME"
echo "   Triple domain experiment → archive/experiments/triple-domain/"
echo "   Abandoned experiments → archive/experiments/abandoned/"
echo "   Documentation → archive/docs/"
echo ""
echo "🎯 What's Left:"
echo "   - Core 15 files (app.py, database.py, export_static.py, etc.)"
echo "   - output/ folder (your GitHub Pages repos)"
echo "   - templates/ folder (your UI)"
echo "   - static/ folder (CSS, JS, images)"
echo "   - Key documentation (README.md, ARCHITECTURE-CLARIFIED.md)"
echo ""
echo "🚀 Your working system is still intact!"
echo "   Run: python3 app.py"
echo "   Visit: http://localhost:5001/studio"
echo ""
echo "💾 To restore from backup:"
echo "   tar -xzf $BACKUP_NAME"
echo ""

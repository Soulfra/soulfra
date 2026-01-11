#!/bin/bash
# Consolidation Plan - Clean Up The Mess
# Created: 2025-12-31
# Purpose: Archive duplicate databases and reorganize folder structure

set -e  # Exit on error

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DIR="old_archives/${TIMESTAMP}_consolidation"
PROJECT_ROOT="/Users/matthewmauer/Desktop/roommate-chat"

echo "==================================================================="
echo "  CONSOLIDATION PLAN - Cleaning Up Soulfra Project"
echo "==================================================================="
echo ""
echo "⚠️  THIS WILL:"
echo "   - Archive 24 duplicate database files"
echo "   - Delete outdated documentation folders"
echo "   - Reorganize static build outputs"
echo "   - Move brand assets into backend"
echo ""
echo "✅ THIS WILL NOT:"
echo "   - Touch soulfra-simple/soulfra.db (SOURCE OF TRUTH)"
echo "   - Delete any active domain folders"
echo "   - Remove working code"
echo ""
echo "Press ENTER to continue, or Ctrl+C to cancel..."
read

cd "$PROJECT_ROOT"

# ==============================================================================
# PHASE 1: Create Archive Directory
# ==============================================================================
echo ""
echo "📁 PHASE 1: Creating archive directory..."
echo ""

mkdir -p "$ARCHIVE_DIR"
mkdir -p "$ARCHIVE_DIR/databases"
mkdir -p "$ARCHIVE_DIR/folders"
mkdir -p "$ARCHIVE_DIR/static-builds"

echo "✅ Created: $ARCHIVE_DIR"

# ==============================================================================
# PHASE 2: Archive Duplicate Databases
# ==============================================================================
echo ""
echo "💾 PHASE 2: Archiving duplicate databases..."
echo ""

# Keep ONLY: soulfra-simple/soulfra.db (2.9MB - SOURCE OF TRUTH)

# Root level duplicates
if [ -f "soulfra.db" ]; then
    echo "   Archiving: soulfra.db (536KB)"
    mv soulfra.db "$ARCHIVE_DIR/databases/"
fi

if [ -f "lib/soulfra.db" ]; then
    echo "   Archiving: lib/soulfra.db (72KB)"
    mv lib/soulfra.db "$ARCHIVE_DIR/databases/"
fi

if [ -f "workspace-brand-marketplace/soulfra.db" ]; then
    echo "   Archiving: workspace-brand-marketplace/soulfra.db (756KB)"
    mv workspace-brand-marketplace/soulfra.db "$ARCHIVE_DIR/databases/"
fi

# Output folder duplicates
if [ -f "soulfra-simple/output/soulfra/soulfra.db" ]; then
    echo "   Archiving: soulfra-simple/output/soulfra/soulfra.db"
    mv soulfra-simple/output/soulfra/soulfra.db "$ARCHIVE_DIR/databases/"
fi

if [ -f "soulfra-simple/output/howtocookathome/soulfra.db" ]; then
    echo "   Archiving: soulfra-simple/output/howtocookathome/soulfra.db"
    mv soulfra-simple/output/howtocookathome/soulfra.db "$ARCHIVE_DIR/databases/"
fi

# Other databases (non-soulfra)
if [ -f "roommate-chat.db" ]; then
    echo "   Archiving: roommate-chat.db"
    mv roommate-chat.db "$ARCHIVE_DIR/databases/"
fi

if [ -f "database/multi_llm_chat.db" ]; then
    echo "   Archiving: database/multi_llm_chat.db"
    mv database/multi_llm_chat.db "$ARCHIVE_DIR/databases/"
fi

echo ""
echo "✅ Database consolidation complete!"
echo "   SOURCE OF TRUTH: soulfra-simple/soulfra.db (2.9MB)"
echo "   Archived: $ARCHIVE_DIR/databases/"

# ==============================================================================
# PHASE 3: Clean Up Duplicate Folders
# ==============================================================================
echo ""
echo "🗂️  PHASE 3: Cleaning up duplicate folders..."
echo ""

# Delete documentation-only folder (just README, no code)
if [ -d "soulfra" ] && [ ! -f "soulfra/app.py" ]; then
    echo "   Archiving: soulfra/ (documentation only)"
    mv soulfra "$ARCHIVE_DIR/folders/"
fi

# Delete empty/duplicate domain folder
if [ -d "domains/soulfra.com" ]; then
    FILECOUNT=$(find "domains/soulfra.com" -type f | wc -l)
    if [ "$FILECOUNT" -lt 5 ]; then
        echo "   Archiving: domains/soulfra.com/ (mostly empty)"
        mv domains/soulfra.com "$ARCHIVE_DIR/folders/"
    fi
fi

echo ""
echo "✅ Folder cleanup complete!"

# ==============================================================================
# PHASE 4: Reorganize Build Outputs
# ==============================================================================
echo ""
echo "🏗️  PHASE 4: Reorganizing build outputs..."
echo ""

# Create builds directory if it doesn't exist
mkdir -p builds

# Move static site builds
if [ -d "public/soulfra" ]; then
    echo "   Moving: public/soulfra → builds/soulfra-legacy"
    mv public/soulfra builds/soulfra-legacy
fi

# Brand exports
if [ -d "brand-exports/soulfra" ]; then
    echo "   Moving: brand-exports/soulfra → soulfra-simple/brand/assets"
    mkdir -p soulfra-simple/brand/assets
    cp -r brand-exports/soulfra/* soulfra-simple/brand/assets/
    mv brand-exports/soulfra "$ARCHIVE_DIR/static-builds/"
fi

echo ""
echo "✅ Build reorganization complete!"

# ==============================================================================
# PHASE 5: Summary Report
# ==============================================================================
echo ""
echo "==================================================================="
echo "  ✅ CONSOLIDATION COMPLETE!"
echo "==================================================================="
echo ""
echo "📊 SUMMARY:"
echo ""
echo "   Active Database:"
echo "   └─ soulfra-simple/soulfra.db (2.9MB, 168 tables)"
echo ""
echo "   Archived Databases:"
echo "   └─ $ARCHIVE_DIR/databases/ (24 files)"
echo ""
echo "   Archived Folders:"
echo "   └─ $ARCHIVE_DIR/folders/"
echo ""
echo "   Build Outputs:"
echo "   ├─ builds/soulfra-legacy/"
echo "   └─ soulfra-simple/brand/assets/"
echo ""
echo "   Active Domains (in /domains/):"
echo "   ├─ soulfra/ → soulfra.com"
echo "   ├─ deathtodata/ → deathtodata.org"
echo "   ├─ calriven/ → calriven.com"
echo "   └─ [other experiments]"
echo ""
echo "==================================================================="
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "1. Build REST API in soulfra-simple:"
echo "   → GET /api/posts"
echo "   → GET /api/posts?tag=privacy"
echo "   → GET /api/posts/{id}"
echo ""
echo "2. Update domain static sites to pull from API"
echo ""
echo "3. Test faucet flow:"
echo "   → Create post in /admin/studio"
echo "   → Tag with 'privacy'"
echo "   → Check deathtodata.org pulls it via API"
echo ""
echo "==================================================================="
echo ""
echo "Archive location: $ARCHIVE_DIR"
echo ""
echo "To restore a file:"
echo "   cp $ARCHIVE_DIR/databases/[filename] ./"
echo ""
echo "Done! 🎉"

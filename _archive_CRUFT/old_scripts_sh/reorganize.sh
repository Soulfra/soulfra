#!/bin/bash
# Reorganize Project - Achieve Max Depth 3 Structure
#
# This script reorganizes the project to follow the "max depth 3" convention:
# Root → Category → Subcategory → File (STOP!)
#
# Usage:
#   ./reorganize.sh --dry-run    # Preview changes
#   ./reorganize.sh              # Actually move files

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
DRY_RUN=false

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if dry-run flag is set
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}DRY RUN MODE - No files will be moved${NC}\n"
fi

# Helper function to move files
move_file() {
    local src="$1"
    local dest="$2"

    if [ ! -e "$src" ]; then
        return 0  # File doesn't exist, skip
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "   ${YELLOW}WOULD MOVE:${NC} $src → $dest"
    else
        # Create destination directory if needed
        mkdir -p "$(dirname "$dest")"
        mv "$src" "$dest"
        echo -e "   ${GREEN}✅ MOVED:${NC} $src → $dest"
    fi
}

echo "======================================================================"
echo "                    PROJECT REORGANIZATION"
echo "======================================================================"
echo ""

# Step 1: Create missing directories
echo "[1/5] Creating standard directories..."
echo ""

DIRS_TO_CREATE=(
    "tests"
    "local"
    "docs/notebooks"
    "docs/guides"
)

for dir in "${DIRS_TO_CREATE[@]}"; do
    if [ "$DRY_RUN" = true ]; then
        if [ ! -d "$PROJECT_ROOT/$dir" ]; then
            echo -e "   ${YELLOW}WOULD CREATE:${NC} $dir/"
        fi
    else
        mkdir -p "$PROJECT_ROOT/$dir"
        echo -e "   ${GREEN}✅ CREATED:${NC} $dir/"
    fi
done

# Step 2: Move test files to tests/
echo ""
echo "[2/5] Moving test files to tests/..."
echo ""

# Find all test files (not in tests/ already)
while IFS= read -r file; do
    if [[ "$file" != *"/tests/"* ]]; then
        filename=$(basename "$file")
        move_file "$file" "$PROJECT_ROOT/tests/$filename"
    fi
done < <(find "$PROJECT_ROOT" -maxdepth 2 -name "*test*.py" 2>/dev/null || true)

# Step 3: Move local development files to local/
echo ""
echo "[3/5] Moving local development files to local/..."
echo ""

LOCAL_FILES=(
    "localhost*.pem"
    "localhost*.sh"
    "setup*.sh"
    "start_localhost*.sh"
    "local_domain_tester.py"
    "cert.pem"
    "key.pem"
)

for pattern in "${LOCAL_FILES[@]}"; do
    while IFS= read -r file; do
        filename=$(basename "$file")
        move_file "$file" "$PROJECT_ROOT/local/$filename"
    done < <(find "$PROJECT_ROOT" -maxdepth 1 -name "$pattern" 2>/dev/null || true)
done

# Step 4: Move documentation to docs/
echo ""
echo "[4/5] Moving documentation to docs/..."
echo ""

# Move markdown files (except README.md and specific guides)
while IFS= read -r file; do
    filename=$(basename "$file")

    # Keep README.md in root
    if [[ "$filename" == "README.md" ]]; then
        continue
    fi

    # Skip if already in docs/
    if [[ "$file" == *"/docs/"* ]]; then
        continue
    fi

    # Determine subdirectory
    if [[ "$filename" == *"GUIDE"* ]] || [[ "$filename" == *"COMPLETE"* ]]; then
        move_file "$file" "$PROJECT_ROOT/docs/guides/$filename"
    else
        move_file "$file" "$PROJECT_ROOT/docs/$filename"
    fi
done < <(find "$PROJECT_ROOT" -maxdepth 1 -name "*.md" 2>/dev/null || true)

# Move Jupyter notebooks to docs/notebooks/
while IFS= read -r file; do
    filename=$(basename "$file")

    # Skip if already in docs/
    if [[ "$file" == *"/docs/"* ]]; then
        continue
    fi

    move_file "$file" "$PROJECT_ROOT/docs/notebooks/$filename"
done < <(find "$PROJECT_ROOT" -maxdepth 1 -name "*.ipynb" 2>/dev/null || true)

# Step 5: Verify max depth 3
echo ""
echo "[5/5] Checking directory depth..."
echo ""

echo "Directories exceeding depth 3:"
DEPTH_VIOLATIONS=0

while IFS= read -r dir; do
    # Count depth (root = 0)
    depth=$(echo "$dir" | tr -cd '/' | wc -c)
    depth=$((depth - $(echo "$PROJECT_ROOT" | tr -cd '/' | wc -c)))

    if [ "$depth" -gt 3 ]; then
        rel_path="${dir#$PROJECT_ROOT/}"
        echo -e "   ${RED}⚠️  DEPTH $depth:${NC} $rel_path"
        DEPTH_VIOLATIONS=$((DEPTH_VIOLATIONS + 1))
    fi
done < <(find "$PROJECT_ROOT" -type d -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*" 2>/dev/null || true)

if [ "$DEPTH_VIOLATIONS" -eq 0 ]; then
    echo -e "   ${GREEN}✅ All directories at max depth 3 or less!${NC}"
else
    echo -e "   ${YELLOW}Found $DEPTH_VIOLATIONS directories exceeding depth 3${NC}"
fi

# Summary
echo ""
echo "======================================================================"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN COMPLETE - No files were moved${NC}"
    echo ""
    echo "To actually reorganize, run:"
    echo "   ./reorganize.sh"
else
    echo -e "${GREEN}REORGANIZATION COMPLETE!${NC}"
fi
echo "======================================================================"
echo ""

# Show new structure
echo "Expected structure:"
echo ""
echo "soulfra-simple/"
echo "├── app.py"
echo "├── database.py"
echo "├── soulfra.db"
echo "├── core/                  ← Core functionality"
echo "├── templates/             ← HTML templates"
echo "├── static/                ← CSS/JS/images"
echo "├── tests/                 ← All test files"
echo "├── local/                 ← Local dev scripts"
echo "├── docs/                  ← Documentation"
echo "│   ├── guides/            ← How-to guides"
echo "│   └── notebooks/         ← Jupyter notebooks"
echo "├── archive/               ← Old code"
echo "└── data/                  ← Data files"
echo ""

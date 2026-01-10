#!/bin/bash
# GitHub Setup Script for Soulfra Multi-Domain Network
# This script initializes the GitHub repository and pushes all code

set -e  # Exit on error

echo "🚀 Soulfra GitHub Setup"
echo "======================="
echo

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository. Run 'git init' first."
    exit 1
fi

# Check if remote origin exists
if git remote | grep -q "^origin$"; then
    echo "✅ Remote 'origin' already exists:"
    git remote get-url origin
    echo
    read -p "Do you want to remove and re-add it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
        echo "✅ Removed existing remote 'origin'"
    else
        echo "ℹ️  Keeping existing remote. Skipping remote setup."
        SKIP_REMOTE=true
    fi
fi

# Add remote origin (if not skipped)
if [ "$SKIP_REMOTE" != "true" ]; then
    echo
    echo "📝 Enter your GitHub repository URL:"
    echo "   Format: git@github.com:username/soulfra-simple.git"
    echo "   or: https://github.com/username/soulfra-simple.git"
    read -p "Repository URL: " REPO_URL

    if [ -z "$REPO_URL" ]; then
        echo "❌ Error: Repository URL cannot be empty"
        exit 1
    fi

    git remote add origin "$REPO_URL"
    echo "✅ Added remote 'origin': $REPO_URL"
fi

echo
echo "📦 Checking git status..."
git status --short

echo
read -p "Do you want to stage all files? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    git add .
    echo "✅ Staged all files"
fi

echo
echo "📋 Current staged files:"
git diff --cached --name-only | head -20
TOTAL_FILES=$(git diff --cached --name-only | wc -l)
echo "   ... and $(($TOTAL_FILES - 20)) more files (total: $TOTAL_FILES)"

echo
echo "📝 Creating commit..."
read -p "Enter commit message (or press Enter for default): " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Initial commit: Soulfra Multi-Domain Network

- Unified domain config (9 domains)
- Soulfra Master Auth (cross-domain login)
- StPetePros professional directory with categories
- Professional inbox & messaging
- Voice memo system with encryption
- Production-ready deployment docs

🤖 Generated with Claude Code"
fi

git commit -m "$COMMIT_MSG"
echo "✅ Created commit"

echo
echo "🌍 Pushing to GitHub..."
read -p "Push to main branch? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # Check if main branch exists locally
    if git show-ref --verify --quiet refs/heads/main; then
        BRANCH="main"
    elif git show-ref --verify --quiet refs/heads/master; then
        BRANCH="master"
    else
        BRANCH=$(git rev-parse --abbrev-ref HEAD)
    fi

    echo "ℹ️  Pushing branch: $BRANCH"
    git push -u origin "$BRANCH"
    echo "✅ Pushed to origin/$BRANCH"
fi

echo
echo "✅ GitHub setup complete!"
echo
echo "Next steps:"
echo "  1. Set up GitHub secrets (run: bash scripts/setup_github_secrets.sh)"
echo "  2. Configure DNS for your 9 domains"
echo "  3. Deploy to production server"
echo
echo "Repository: $(git remote get-url origin 2>/dev/null || echo 'No remote set')"

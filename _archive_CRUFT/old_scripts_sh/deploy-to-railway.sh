#!/bin/bash

# CringeProof API Deployment to Railway
# Run this script to deploy the voice pipeline backend

set -e  # Exit on error

echo "🚀 CringeProof Voice Pipeline - Railway Deployment"
echo "=================================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @railway/cli"
    echo ""
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Not logged in to Railway. Logging in..."
    railway login
else
    echo "✅ Already logged in to Railway"
fi

echo ""
echo "📋 Setting environment variables..."

# Generate SECRET_KEY if not exists
if ! railway variables get SECRET_KEY &> /dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    railway variables set SECRET_KEY="$SECRET_KEY"
    echo "  ✅ SECRET_KEY generated"
else
    echo "  ⏭️  SECRET_KEY already set"
fi

# Set other variables
railway variables set FLASK_ENV=production
railway variables set PYTHONUNBUFFERED=1
railway variables set WHISPER_MODEL=base

echo "  ✅ Environment variables configured"
echo ""

# Prompt for GitHub token
echo "🔑 GitHub Token Setup"
echo "-------------------"
echo "You need a GitHub Personal Access Token to trigger site rebuilds."
echo ""
echo "Create one at: https://github.com/settings/tokens/new"
echo "Required scopes: repo, workflow"
echo ""
read -p "Enter your GitHub token (ghp_...): " GITHUB_TOKEN

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  No GitHub token provided. Site auto-rebuild will be disabled."
else
    railway variables set GITHUB_TOKEN="$GITHUB_TOKEN"
    echo "  ✅ GitHub token configured"
fi

echo ""
echo "📦 Deploying to Railway..."
echo ""

railway up

echo ""
echo "✅ Deployment complete!"
echo ""

# Get deployment URL
RAILWAY_URL=$(railway domain 2>/dev/null | tail -1)

echo "🌐 Your API is now live at:"
echo "   $RAILWAY_URL"
echo ""

echo "📝 Next Steps:"
echo ""
echo "1. Update voice-archive/record.html with your Railway URL:"
echo "   value=\"$RAILWAY_URL\""
echo ""
echo "2. Initialize prohibited words database:"
echo "   railway run python3 prohibited_words_filter.py"
echo ""
echo "3. Test the health endpoint:"
echo "   curl https://$RAILWAY_URL/health"
echo ""
echo "4. Visit cringeproof.com/record.html to test voice recording"
echo ""
echo "📊 Monitor logs:"
echo "   railway logs --tail 100"
echo ""
echo "🎉 Your CringeProof voice pipeline is online!"

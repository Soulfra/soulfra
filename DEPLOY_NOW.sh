#!/bin/bash
set -e

echo "🚀 DEPLOYING TO RAILWAY - NO BULLSHIT"
echo ""

# Check Railway login
if ! railway whoami &>/dev/null; then
    echo "❌ Not logged into Railway"
    echo "Run: railway login"
    exit 1
fi

# Check git
if [ ! -d .git ]; then
    echo "📦 Initializing git..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
fi

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

# Get deployment URL
RAILWAY_URL=$(railway status | grep "https://" | awk '{print $NF}')

if [ -z "$RAILWAY_URL" ]; then
    echo "❌ Could not get Railway URL"
    echo "Check: railway status"
    exit 1
fi

echo ""
echo "✅ DEPLOYED!"
echo "📍 Backend URL: $RAILWAY_URL"
echo ""
echo "Next: Update voice-archive/config.js with this URL"
echo "      API_BACKEND_URL: '$RAILWAY_URL'"

#!/bin/bash
# Production Startup Script with OAuth Environment Variables
# Use this for local testing with OAuth before deploying to Railway

cd "$(dirname "$0")"

echo "============================================"
echo "🚀 Starting Soulfra Production Mode"
echo "============================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating template..."
    cat > .env << 'ENVEOF'
# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here_change_this
FLASK_ENV=production
FLASK_DEBUG=0

# Database
SOULFRA_DB=soulfra.db

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Apple OAuth (optional)
APPLE_CLIENT_ID=your_apple_client_id_here
APPLE_CLIENT_SECRET=your_apple_client_secret_here

# Base URL (for OAuth redirects)
BASE_URL=http://localhost:5001
ENVEOF
    echo "✅ Created .env template. Please edit .env with your OAuth credentials."
    echo ""
    echo "Get credentials from:"
    echo "  Google: https://console.cloud.google.com/apis/credentials"
    echo "  GitHub: https://github.com/settings/developers"
    echo "  Apple: https://developer.apple.com/account/resources/identifiers/list"
    echo ""
    exit 1
fi

# Load environment variables from .env
echo "📋 Loading environment variables from .env..."
export $(cat .env | grep -v '^#' | xargs)

# Verify required variables
REQUIRED_VARS=("FLASK_SECRET_KEY" "GOOGLE_CLIENT_ID" "GITHUB_CLIENT_ID")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please edit .env file and add your OAuth credentials."
    exit 1
fi

echo "✅ All required environment variables set"
echo ""

# Display configuration
echo "📊 Configuration:"
echo "   Database: $SOULFRA_DB"
echo "   Base URL: $BASE_URL"
echo "   Google OAuth: ${GOOGLE_CLIENT_ID:0:10}..."
echo "   GitHub OAuth: ${GITHUB_CLIENT_ID:0:10}..."
echo ""

# Database stats
if [ -f "$SOULFRA_DB" ]; then
    USER_COUNT=$(sqlite3 $SOULFRA_DB "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    echo "📊 Database Status:"
    echo "   Users: $USER_COUNT"
else
    echo "⚠️  Database not found. Will be created on first run."
fi
echo ""

# Start Flask
echo "🌐 Starting Flask server..."
echo ""
echo "📍 Access URLs:"
echo "   Local: http://localhost:5001"
echo "   Login: http://localhost:5001/login.html"
echo "   Customer Dashboard: http://localhost:5001/customers/dashboard"
echo "   Database Admin: http://localhost:5001/admin/database"
echo ""
echo "🔐 OAuth Endpoints:"
echo "   Google: http://localhost:5001/auth/google"
echo "   GitHub: http://localhost:5001/auth/github"
echo "   Apple: http://localhost:5001/auth/apple"
echo ""
echo "============================================"
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask with production settings
python3 app.py

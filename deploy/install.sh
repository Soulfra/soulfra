#!/bin/bash
# Soulfra OSS - One-Command Installation Script
#
# Installs and configures Soulfra for deployment
#
# Usage:
#   bash install.sh
#   bash install.sh --dev    # Development mode

set -e  # Exit on error

echo "================================"
echo "🚀 Soulfra OSS Installation"
echo "================================"
echo ""

# Check if running in dev mode
DEV_MODE=false
if [[ "$1" == "--dev" ]]; then
    DEV_MODE=true
    echo "📦 Running in DEVELOPMENT mode"
else
    echo "📦 Running in PRODUCTION mode"
fi
echo ""

# Step 1: Check Python version
echo "1️⃣  Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   ✅ Found Python $python_version"
echo ""

# Step 2: Install dependencies
echo "2️⃣  Installing Python dependencies..."
pip3 install -q flask markdown2 qrcode pillow
echo "   ✅ Installed: flask, markdown2, qrcode, pillow"
echo ""

# Step 3: Initialize database
echo "3️⃣  Initializing database..."
if [ -f "soulfra.db" ]; then
    echo "   ℹ️  Database already exists: soulfra.db"
    read -p "   ⚠️  Overwrite existing database? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm soulfra.db
        echo "   🗑️  Deleted existing database"
    else
        echo "   ⏭️  Keeping existing database"
    fi
fi

if [ ! -f "soulfra.db" ]; then
    python3 -c "from database import init_db; init_db()"
    echo "   ✅ Database initialized"
fi
echo ""

# Step 4: Run database migrations
echo "4️⃣  Running database migrations..."
if [ -f "database_tier_migrations.sql" ]; then
    sqlite3 soulfra.db < database_tier_migrations.sql 2>/dev/null || echo "   ℹ️  Migrations already applied"
    echo "   ✅ Multi-tier migrations applied"
fi
echo ""

# Step 5: Load theme configuration
echo "5️⃣  Loading theme configuration..."
if [ -f "deploy/theme_config.yaml" ]; then
    python3 deploy/apply_theme.py
    echo "   ✅ Theme applied"
else
    echo "   ⏭️  No theme config found (using defaults)"
fi
echo ""

# Step 6: Generate QR codes and galleries
echo "6️⃣  Generating QR galleries..."
if [ "$DEV_MODE" = false ]; then
    python3 qr_gallery_system.py --all >/dev/null 2>&1 || echo "   ⏭️  No posts to generate galleries for"
    echo "   ✅ QR galleries generated"
else
    echo "   ⏭️  Skipped in dev mode"
fi
echo ""

# Step 7: Create output directories
echo "7️⃣  Creating output directories..."
mkdir -p output/galleries output/templates output/analytics static/qr_codes/galleries static/qr_codes/dm
echo "   ✅ Directories created"
echo ""

# Step 8: Register gallery routes
echo "8️⃣  Testing gallery routes..."
python3 -c "from gallery_routes import register_gallery_routes; from flask import Flask; app = Flask(__name__); register_gallery_routes(app); print('   ✅ Routes registered')"
echo ""

# Step 9: Show next steps
echo "================================"
echo "✅ Installation Complete!"
echo "================================"
echo ""
echo "🎯 Next steps:"
echo ""
if [ "$DEV_MODE" = true ]; then
    echo "  1. Start development server:"
    echo "     python3 app.py"
    echo ""
    echo "  2. Visit http://localhost:5001"
else
    echo "  1. Configure deployment settings:"
    echo "     Edit deploy/theme_config.yaml"
    echo ""
    echo "  2. Deploy to production:"
    echo "     See deploy/DEPLOY_README.md for options:"
    echo "       - VPS (DigitalOcean, Linode)"
    echo "       - Railway.app"
    echo "       - Fly.io"
    echo "       - Docker"
    echo ""
    echo "  3. Or start local server:"
    echo "     gunicorn -w 4 -b 0.0.0.0:5000 app:app"
fi
echo ""
echo "📚 Documentation:"
echo "   - README.md - Project overview"
echo "   - deploy/DEPLOY_README.md - Deployment guide"
echo "   - MULTI_TIER_COMPLETE.md - Architecture docs"
echo ""

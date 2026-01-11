#!/bin/bash
#
# Quick Start - Fast Deployment Script for Soulfra
#
# Usage:
#   ./quick_start.sh         # Start server with existing content
#   ./quick_start.sh --seed  # Start server and seed content
#   ./quick_start.sh --clean # Clean everything and start fresh
#

set -e  # Exit on error

echo ""
echo "========================================================================"
echo "🚀 Soulfra Quick Start"
echo "========================================================================"
echo ""

# Parse arguments
SEED_CONTENT=false
CLEAN_START=false

for arg in "$@"; do
    case $arg in
        --seed)
            SEED_CONTENT=true
            shift
            ;;
        --clean)
            CLEAN_START=true
            SEED_CONTENT=true  # Clean implies seed
            shift
            ;;
    esac
done

# Step 1: Kill existing servers
echo "🧹 Step 1: Cleaning existing processes..."
pkill -9 -f "python3 app.py" 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 1
echo "✅ All Flask processes killed"
echo ""

# Step 2: Clean database if requested
if [ "$CLEAN_START" = true ]; then
    echo "🗑️  Step 2: Cleaning database..."
    echo "   Removing soulfra.db..."
    rm -f soulfra.db
    echo "✅ Database cleaned"
    echo ""

    echo "🔧 Step 3: Running migrations..."
    python3 migrate.py
    echo "✅ Migrations complete"
    echo ""
fi

# Step 3: Seed content if requested
if [ "$SEED_CONTENT" = true ]; then
    echo "🌱 Step 4: Seeding blog posts..."
    python3 quick_seed_posts.py
    echo "✅ Content seeded"
    echo ""
fi

# Step 4: Start server
echo "🚀 Step 5: Starting Flask server..."
python3 app.py > /tmp/flask.log 2>&1 &
SERVER_PID=$!
echo "✅ Server started (PID: $SERVER_PID)"
echo ""

# Step 5: Wait for server to be ready
echo "⏳ Step 6: Waiting for server..."
for i in {1..10}; do
    if curl -s http://localhost:5001/ > /dev/null 2>&1; then
        echo "✅ Server ready!"
        break
    fi
    sleep 1
    echo "   Waiting... ($i/10)"
done
echo ""

# Step 6: Get local IP
echo "📍 Step 7: Network information..."
LOCAL_IP=$(ifconfig | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="192.168.1.123"
fi
echo "   Local IP: $LOCAL_IP"
echo ""

# Step 7: Display status
echo "========================================================================"
echo "✅ Soulfra is Ready!"
echo "========================================================================"
echo ""
echo "📍 Access Points:"
echo "   Local:        http://localhost:5001/"
echo "   Network:      http://$LOCAL_IP:5001/"
echo ""
echo "🎯 Key Routes:"
echo "   Homepage:          http://localhost:5001/"
echo "   Brand Discuss:     http://localhost:5001/brand/discuss/deathtodata"
echo "   Cringeproof Game:  http://localhost:5001/cringeproof"
echo "   Admin Studio:      http://localhost:5001/admin/studio"
echo ""
echo "📊 Content:"
posts_count=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM posts;" 2>/dev/null || echo "0")
echo "   Blog posts: $posts_count"
echo ""
echo "🔧 Commands:"
echo "   View logs:      tail -f /tmp/flask.log"
echo "   Stop server:    pkill -f 'python3 app.py'"
echo "   Restart:        ./quick_start.sh"
echo "   Clean restart:  ./quick_start.sh --clean"
echo ""
echo "========================================================================"
echo "🎮 Test Cringeproof with grandparents:"
echo "========================================================================"
echo ""
echo "1. You:        Visit http://localhost:5001/cringeproof"
echo "2. Grandma:    Visit http://$LOCAL_IP:5001/cringeproof (same WiFi)"
echo "3. Grandpa:    Visit http://$LOCAL_IP:5001/cringeproof (same WiFi)"
echo ""
echo "========================================================================"
echo ""

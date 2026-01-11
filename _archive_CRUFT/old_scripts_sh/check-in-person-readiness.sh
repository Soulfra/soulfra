#!/bin/bash
# Check if system is ready for in-person professional signups

set -e

echo "🔍 Checking In-Person Signup Readiness"
echo "======================================"
echo ""

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "📍 Your local IP: $LOCAL_IP"
echo "   Share this URL with signups: http://$LOCAL_IP:5001"
echo ""

# Test 1: Flask server running
echo "1️⃣  Checking Flask server..."
if curl -k -s https://localhost:5001/status > /dev/null 2>&1; then
    echo "   ✅ Flask is running on https://localhost:5001"
elif curl -k -s https://localhost:5001 > /dev/null 2>&1; then
    echo "   ✅ Flask is running on https://localhost:5001"
else
    echo "   ❌ Flask server is NOT running"
    echo "      Start with: python3 app.py"
    exit 1
fi

# Test 2: Database exists
echo ""
echo "2️⃣  Checking database..."
if [ -f "soulfra.db" ]; then
    echo "   ✅ Database exists (soulfra.db)"

    # Check table counts
    PROS=$(python3 -c "from database import get_db; print(get_db().execute('SELECT COUNT(*) FROM professionals').fetchone()[0])" 2>&1)
    MSGS=$(python3 -c "from database import get_db; print(get_db().execute('SELECT COUNT(*) FROM messages').fetchone()[0])" 2>&1)

    echo "   📊 Current stats:"
    echo "      Professionals: $PROS"
    echo "      Messages: $MSGS"
else
    echo "   ❌ Database not found"
    echo "      Initialize with: python3 database.py"
    exit 1
fi

# Test 3: Signup page works
echo ""
echo "3️⃣  Checking signup page..."
SIGNUP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:5001/signup/professional 2>&1)
if [ "$SIGNUP_CODE" == "200" ]; then
    echo "   ✅ Signup page works"
    echo "      URL: https://localhost:5001/signup/professional"
else
    echo "   ⚠️  Signup returned HTTP $SIGNUP_CODE"
fi

# Test 4: Admin dashboard works
echo ""
echo "4️⃣  Checking admin dashboard..."
ADMIN_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:5001/admin/stpetepros 2>&1)
if [ "$ADMIN_CODE" == "200" ]; then
    echo "   ✅ Admin dashboard works"
    echo "      URL: https://localhost:5001/admin/stpetepros"
else
    echo "   ⚠️  Admin dashboard returned HTTP $ADMIN_CODE"
fi

# Test 5: QR code generation
echo ""
echo "5️⃣  Checking QR code generation..."
if [ $PROS -gt 0 ]; then
    echo "   ✅ You have $PROS professionals"
    echo "      QR codes at: https://localhost:5001/professional/{ID}/qr"
else
    echo "   ℹ️  No professionals yet"
    echo "      Sign up your first one to test QR codes!"
fi

# Test 6: AI moderation
echo ""
echo "6️⃣  Checking AI moderation system..."
if [ -f "ai_moderation_integration.py" ]; then
    echo "   ✅ AI moderation ready"
    echo "      Dashboard: https://localhost:5001/admin/stpetepros/moderation"
else
    echo "   ⚠️  AI moderation file not found"
fi

echo ""
echo "======================================"
echo "Summary:"
echo ""

if [ "$SIGNUP_CODE" == "200" ] && [ "$ADMIN_CODE" == "200" ]; then
    echo "✅ System is READY for in-person signups!"
    echo ""
    echo "📱 Next steps:"
    echo "   1. Open on your phone: http://$LOCAL_IP:5001/signup/professional"
    echo "   2. Sign up a test professional"
    echo "   3. Download their QR code"
    echo "   4. AirDrop it to their phone"
    echo ""
    echo "📖 Full guide: IN_PERSON_SIGNUP_GUIDE.md"
else
    echo "⚠️  Some components need attention"
    echo "   Fix the issues above and try again"
fi

echo ""

# Offer to open guide
read -p "Open the in-person signup guide? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open IN_PERSON_SIGNUP_GUIDE.md 2>/dev/null || cat IN_PERSON_SIGNUP_GUIDE.md
    else
        cat IN_PERSON_SIGNUP_GUIDE.md
    fi
fi

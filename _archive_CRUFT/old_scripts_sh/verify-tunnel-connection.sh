#!/bin/bash
# Verify Cloudflare Tunnel is working correctly

set -e

echo "🔍 Verifying Cloudflare Tunnel Connection"
echo "=========================================="
echo ""

# Test 1: Check DNS
echo "1️⃣  Checking DNS for soulfra.com..."
DNS_RESULT=$(dig +short soulfra.com CNAME 2>&1 || echo "")

if [[ $DNS_RESULT == *"cfargotunnel.com"* ]]; then
    echo "   ✅ DNS: Points to Cloudflare Tunnel"
    echo "      $DNS_RESULT"
elif [[ $DNS_RESULT == *"185.199"* ]]; then
    echo "   ⚠️  DNS: Still points to GitHub Pages"
    echo "      $DNS_RESULT"
    echo "      This means tunnel DNS routing hasn't propagated yet"
    echo "      Wait a few minutes and try again"
else
    echo "   ℹ️  DNS: $DNS_RESULT"
fi

echo ""

# Test 2: Check if local Flask is running
echo "2️⃣  Checking local Flask server (localhost:5001)..."
if curl -k -s https://localhost:5001 > /dev/null 2>&1; then
    echo "   ✅ Flask server is running locally"
else
    echo "   ❌ Flask server is NOT running"
    echo "      Start with: python3 app.py"
    exit 1
fi

echo ""

# Test 3: Check if soulfra.com loads
echo "3️⃣  Checking if soulfra.com loads..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://soulfra.com 2>&1)

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "302" ]; then
    echo "   ✅ soulfra.com loads (HTTP $HTTP_CODE)"
else
    echo "   ⚠️  soulfra.com returned HTTP $HTTP_CODE"
fi

echo ""

# Test 4: Check if it's the Flask app (not GitHub Pages)
echo "4️⃣  Checking if soulfra.com serves Flask app..."
CONTENT=$(curl -s https://soulfra.com 2>&1)

if [[ $CONTENT == *"Soulfra Flask app"* ]] || [[ $CONTENT == *"flask"* ]]; then
    echo "   ✅ Serving Flask app (not GitHub Pages)"
elif [[ $CONTENT == *"GitHub.com"* ]] || [[ $CONTENT == *"github.io"* ]]; then
    echo "   ⚠️  Still serving GitHub Pages"
    echo "      DNS hasn't propagated yet, or tunnel isn't running"
else
    echo "   ℹ️  Unknown content - check manually"
fi

echo ""

# Test 5: Check specific routes
echo "5️⃣  Testing specific Flask routes..."

# Test moderation dashboard
MODERATION_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://192.168.1.87:5001/admin/stpetepros/moderation 2>&1)
if [ "$MODERATION_CODE" == "200" ]; then
    echo "   ✅ Moderation dashboard works locally"
else
    echo "   ⚠️  Moderation dashboard: HTTP $MODERATION_CODE"
fi

# Test if database exists
if python3 -c "from database import get_db; get_db()" 2>&1 > /dev/null; then
    echo "   ✅ Database is accessible"

    # Count records
    PROF_COUNT=$(python3 -c "from database import get_db; print(get_db().execute('SELECT COUNT(*) FROM professionals').fetchone()[0])" 2>&1)
    MSG_COUNT=$(python3 -c "from database import get_db; print(get_db().execute('SELECT COUNT(*) FROM messages').fetchone()[0])" 2>&1)

    echo "      📊 Database stats:"
    echo "         Professionals: $PROF_COUNT"
    echo "         Messages: $MSG_COUNT"
else
    echo "   ⚠️  Database not accessible"
fi

echo ""
echo "=========================================="
echo "Summary:"
echo ""

if [[ $DNS_RESULT == *"cfargotunnel.com"* ]] && [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Tunnel is working! soulfra.com → Your laptop"
    echo ""
    echo "Next: Create a test account at https://soulfra.com/signup/professional"
    echo "It will write to your local database!"
elif [[ $DNS_RESULT == *"185.199"* ]]; then
    echo "⚠️  DNS still points to GitHub Pages"
    echo ""
    echo "Wait 5-10 minutes for DNS propagation, then try again"
    echo "Or manually check: dig soulfra.com"
else
    echo "⚠️  Some tests failed - check tunnel setup"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Is tunnel running? cloudflared tunnel run soulfra"
    echo "  2. Is Flask running? python3 app.py"
    echo "  3. DNS configured? cloudflared tunnel route dns soulfra soulfra.com"
fi

echo ""

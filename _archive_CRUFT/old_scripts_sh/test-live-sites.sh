#!/bin/bash
# Test what's actually working vs broken

echo "🌐 Testing Live Sites"
echo "===================="
echo ""

# Test 1: GitHub Pages StPetePros
echo "1️⃣  Testing GitHub Pages StPetePros..."
CODE1=$(curl -s -o /dev/null -w "%{http_code}" https://soulfra.github.io/stpetepros/index.html 2>&1)
if [ "$CODE1" == "200" ]; then
    echo "   ✅ https://soulfra.github.io/stpetepros/ - WORKING"
else
    echo "   ❌ GitHub Pages returned HTTP $CODE1"
fi

# Test 2: Individual professional page
echo ""
echo "2️⃣  Testing individual professional page..."
CODE2=$(curl -s -o /dev/null -w "%{http_code}" https://soulfra.github.io/stpetepros/professional-21.html 2>&1)
if [ "$CODE2" == "200" ]; then
    echo "   ✅ https://soulfra.github.io/stpetepros/professional-21.html - WORKING"

    # Check if it has QR code
    CONTENT=$(curl -s https://soulfra.github.io/stpetepros/professional-21.html 2>&1)
    if [[ $CONTENT == *"data:image/png;base64"* ]]; then
        echo "      ✅ QR code embedded in page"
    else
        echo "      ⚠️  No QR code found"
    fi
else
    echo "   ❌ Professional page returned HTTP $CODE2"
fi

# Test 3: soulfra.com
echo ""
echo "3️⃣  Testing soulfra.com..."
CODE3=$(curl -s -o /dev/null -w "%{http_code}" https://soulfra.com 2>&1)
if [ "$CODE3" == "200" ]; then
    echo "   ✅ https://soulfra.com - WORKING"
else
    echo "   ❌ soulfra.com returned HTTP $CODE3"
fi

# Test 4: soulfra.com/stpetepros
echo ""
echo "4️⃣  Testing soulfra.com/stpetepros..."
CODE4=$(curl -s -o /dev/null -w "%{http_code}" https://soulfra.com/stpetepros/ 2>&1)
if [ "$CODE4" == "200" ]; then
    echo "   ✅ https://soulfra.com/stpetepros/ - WORKING"
elif [ "$CODE4" == "404" ]; then
    echo "   ❌ https://soulfra.com/stpetepros/ - 404 Not Found"
    echo "      Fix: Wait for DNS propagation or use soulfra.github.io/stpetepros instead"
else
    echo "   ⚠️  soulfra.com/stpetepros returned HTTP $CODE4"
fi

# Test 5: Local Flask
echo ""
echo "5️⃣  Testing local Flask server..."
if curl -k -s https://localhost:5001 > /dev/null 2>&1; then
    echo "   ℹ️  Local Flask is running (but has errors)"

    # Test signup page
    SIGNUP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:5001/signup/professional 2>&1)
    if [ "$SIGNUP_CODE" == "200" ]; then
        echo "      ✅ Signup page works"
    else
        echo "      ❌ Signup returns HTTP $SIGNUP_CODE (missing images table)"
    fi
else
    echo "   ⚠️  Local Flask is NOT running"
    echo "      (You don't need it - GitHub Pages works)"
fi

echo ""
echo "===================="
echo "Summary:"
echo ""

if [ "$CODE1" == "200" ] && [ "$CODE2" == "200" ]; then
    echo "✅ YOUR SITES ARE LIVE!"
    echo ""
    echo "📱 Share this URL:"
    echo "   https://soulfra.github.io/stpetepros/"
    echo ""
    echo "🎯 Individual profiles:"
    echo "   https://soulfra.github.io/stpetepros/professional-[1-25].html"
    echo ""

    if [ "$CODE4" == "404" ]; then
        echo "ℹ️  soulfra.com/stpetepros is 404 but GitHub Pages works"
        echo "   Use soulfra.github.io/stpetepros for now"
    fi
else
    echo "⚠️  Something is wrong with GitHub Pages deployment"
fi

echo ""
echo "📖 Full details: WHATS_ACTUALLY_WORKING.md"
echo ""

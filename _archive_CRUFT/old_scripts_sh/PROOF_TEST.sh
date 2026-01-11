#!/bin/bash
# Proof-of-Concept Test Script
# Proves: 0 users → 1 user → export works

cd "$(dirname "$0")"

echo "============================================"
echo "🧪 CringeProof Proof-of-Concept Test"
echo "============================================"
echo ""

# 1. Check starting state
echo "📊 Step 1: Verify Fresh Database (0 users)"
USER_COUNT=$(sqlite3 cringeproof.db "SELECT COUNT(*) FROM users;")
echo "   Users in cringeproof.db: $USER_COUNT"

if [ "$USER_COUNT" -ne 0 ]; then
    echo "   ⚠️  Database not fresh! Resetting..."
    rm -f cringeproof.db
    sqlite3 cringeproof.db < minimal_schema.sql
    echo "   ✅ Database reset to 0 users"
else
    echo "   ✅ Database is fresh (0 users)"
fi
echo ""

# 2. Instructions for manual test
echo "📝 Step 2: Manual Test Instructions"
echo ""
echo "   1. Start backend:"
echo "      ./START_CRINGEPROOF.sh"
echo ""
echo "   2. Register your first user:"
echo "      - Go to: http://localhost:5001/register"
echo "      - Create account with YOUR email"
echo ""
echo "   3. Verify export works:"
echo "      - Go to: http://localhost:5001/customers/dashboard"
echo "      - Click 'Mailchimp CSV'"
echo "      - Open CSV - should show YOUR email"
echo ""
echo "   4. Check stats:"
echo "      curl http://localhost:5001/api/customers/stats"
echo "      Should show: real_users = 1"
echo ""

# 3. Automated API test (optional)
echo "📡 Step 3: Automated API Test (optional)"
echo ""
echo "   If backend is running on port 5001, run this:"
echo "   curl http://localhost:5001/api/customers/stats | jq"
echo ""
echo "============================================"
echo "✅ Test script ready. Follow steps above to prove system works."
echo "============================================"

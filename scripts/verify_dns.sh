#!/bin/bash
# Verify all 9 Soulfra domains resolve correctly
# This script checks DNS resolution and HTTPS availability for all domains

DOMAINS=(
    "soulfra.com"
    "stpetepros.com"
    "cringeproof.com"
    "calriven.com"
    "deathtodata.com"
    "howtocookathome.com"
    "hollowtown.com"
    "oofbox.com"
    "niceleak.com"
)

echo "🌍 Verifying DNS for all Soulfra domains..."
echo "==========================================="
echo

SUCCESS_COUNT=0
FAIL_COUNT=0

for domain in "${DOMAINS[@]}"; do
    echo "🔍 Checking $domain..."

    # Get IP address (use Google DNS to avoid caching)
    IP=$(dig +short "$domain" @8.8.8.8 | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | tail -1)

    if [ -n "$IP" ]; then
        echo "   ✅ DNS: $domain → $IP"

        # Test HTTPS (with timeout)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://$domain" 2>/dev/null)

        if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ] || [ "$HTTP_CODE" -eq 301 ]; then
            echo "   ✅ HTTPS: Working (HTTP $HTTP_CODE)"
            ((SUCCESS_COUNT++))
        elif [ "$HTTP_CODE" -eq 000 ]; then
            echo "   ⚠️  HTTPS: Timeout (server may be down)"
            ((FAIL_COUNT++))
        else
            echo "   ⚠️  HTTPS: Failed (HTTP $HTTP_CODE)"
            ((FAIL_COUNT++))
        fi

        # Check SSL certificate
        SSL_INFO=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

        if [ -n "$SSL_INFO" ]; then
            EXPIRY=$(echo "$SSL_INFO" | grep "notAfter" | cut -d'=' -f2)
            echo "   ✅ SSL: Valid (expires $EXPIRY)"
        else
            echo "   ⚠️  SSL: Not configured or invalid"
        fi

    else
        echo "   ❌ DNS: NOT RESOLVED"
        echo "   ⚠️  HTTPS: Cannot test (DNS not resolved)"
        ((FAIL_COUNT++))
    fi

    echo
done

echo "==========================================="
echo "Summary:"
echo "  ✅ Success: $SUCCESS_COUNT/9 domains"
echo "  ❌ Failed:  $FAIL_COUNT/9 domains"
echo

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 All domains configured correctly!"
    exit 0
else
    echo "⚠️  Some domains need attention"
    exit 1
fi

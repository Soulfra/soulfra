#!/bin/bash

# Setup local domain testing for StPetePros
# Run this ONCE to add local domain entries

echo "🔧 Setting up local domain testing..."
echo ""
echo "This will add the following entries to /etc/hosts:"
echo "  127.0.0.1 stpetepros.local"
echo "  127.0.0.1 soulfra.local"
echo "  127.0.0.1 cringeproof.local"
echo ""
echo "You'll need to enter your password for sudo access."
echo ""

# Check if entries already exist
if grep -q "stpetepros.local" /etc/hosts; then
    echo "✅ Local domains already configured!"
    echo ""
    echo "Test URLs:"
    echo "  - http://stpetepros.local:5001"
    echo "  - http://soulfra.local:5001"
    echo "  - http://cringeproof.local:5001"
    echo ""
    echo "Make sure Flask is running: python3 app.py"
    exit 0
fi

# Add entries
sudo bash -c "cat >> /etc/hosts" << 'EOF'

# StPetePros local testing (added by setup-local-domains.sh)
127.0.0.1 stpetepros.local
127.0.0.1 soulfra.local
127.0.0.1 cringeproof.local
EOF

echo "✅ Local domains configured!"
echo ""
echo "Test URLs:"
echo "  - http://stpetepros.local:5001"
echo "  - http://soulfra.local:5001"
echo "  - http://cringeproof.local:5001"
echo ""
echo "Next steps:"
echo "  1. Start Flask: python3 app.py"
echo "  2. Open http://stpetepros.local:5001 in your browser"
echo "  3. Test keyboard shortcuts (press ? for help)"
echo "  4. Test login (press L)"
echo ""

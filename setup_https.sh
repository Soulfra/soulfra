#!/bin/bash
"""
HTTPS Setup for Voice Memo Recording on iPhone

Generates self-signed SSL certificate for local HTTPS server.
Allows getUserMedia (microphone access) on iPhone over local network.

Usage:
    bash setup_https.sh

Then start Flask with:
    python3 app.py --https
"""

echo "🔐 Setting up HTTPS for Local Voice Recording"
echo "=============================================="
echo ""

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL not found. Install with: brew install openssl"
    exit 1
fi

# Check if certificates already exist
if [ -f "key.pem" ] && [ -f "cert.pem" ]; then
    echo "⚠️  Certificates already exist:"
    echo "   - key.pem"
    echo "   - cert.pem"
    echo ""
    read -p "Regenerate? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Using existing certificates"
        exit 0
    fi
    rm -f key.pem cert.pem
fi

# Generate self-signed certificate
echo "📝 Generating self-signed SSL certificate..."
echo ""

openssl req -x509 \
    -newkey rsa:4096 \
    -keyout key.pem \
    -out cert.pem \
    -days 365 \
    -nodes \
    -subj "/C=US/ST=California/L=SF/O=Soulfra/CN=192.168.1.87"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate generated successfully!"
    echo ""
    echo "Files created:"
    echo "  - key.pem  (private key)"
    echo "  - cert.pem (certificate)"
    echo ""
    echo "📱 iPhone Setup:"
    echo "  1. Visit https://192.168.1.87:5001 on iPhone"
    echo "  2. Click 'Advanced' → 'Proceed to 192.168.1.87'"
    echo "  3. Accept the certificate warning (one-time)"
    echo "  4. Microphone access will now work!"
    echo ""
    echo "🚀 Start HTTPS server:"
    echo "  python3 -c \"from app import app; app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'))\""
    echo ""
    echo "Or add to app.py:"
    echo "  if __name__ == '__main__':"
    echo "      import sys"
    echo "      if '--https' in sys.argv:"
    echo "          app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'), debug=True)"
    echo "      else:"
    echo "          app.run(host='0.0.0.0', port=5001, debug=True)"
else
    echo "❌ Failed to generate SSL certificate"
    exit 1
fi

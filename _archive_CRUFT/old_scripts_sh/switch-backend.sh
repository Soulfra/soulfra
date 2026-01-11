#!/bin/bash
# Switch API backend between local and production

echo "🔄 Backend Switcher - Choose your deployment"
echo ""
echo "1) Local testing (192.168.1.87:5002)"
echo "2) Production VPS (api.cringeproof.com)"
echo "3) Localhost dev (https://localhost:5002)"
echo ""
read -p "Choose [1-3]: " choice

case $choice in
    1)
        BACKEND="https://192.168.1.87:5002"
        ENV="Local Testing"
        ;;
    2)
        BACKEND="https://api.cringeproof.com"
        ENV="Production VPS"
        ;;
    3)
        BACKEND="https://localhost:5002"
        ENV="Localhost Dev"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Switching to: $ENV ($BACKEND)"
echo ""

# Update voice-archive/config.js
sed -i.bak "s|API_BACKEND_URL: '.*'|API_BACKEND_URL: '$BACKEND'|" voice-archive/config.js
echo "✅ Updated voice-archive/config.js"

# Update output/soulfra/config.js
sed -i.bak "s|API_BACKEND_URL: '.*'|API_BACKEND_URL: '$BACKEND'|" output/soulfra/config.js
echo "✅ Updated output/soulfra/config.js"

# Remove backup files
rm -f voice-archive/config.js.bak
rm -f output/soulfra/config.js.bak

echo ""
echo "🎉 Done! Backend switched to: $ENV"
echo ""
echo "Next steps:"
echo "  - Test locally: python3 -m http.server 8000"
echo "  - Deploy: git add . && git commit -m 'Update backend config' && git push"

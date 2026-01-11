#!/bin/bash
# Deploy mobile.html to GitHub Pages (cringeproof.com)

echo "📱 Deploying mobile.html to GitHub Pages..."
echo ""

# Clone or update cringeproof repo
if [ ! -d "/tmp/cringeproof-deploy" ]; then
    echo "📥 Cloning cringeproof GitHub Pages repo..."
    git clone https://github.com/CringeProof/cringeproof.github.io /tmp/cringeproof-deploy
else
    echo "🔄 Updating existing repo..."
    cd /tmp/cringeproof-deploy && git pull
fi

cd /tmp/cringeproof-deploy

# Copy mobile files
echo "📋 Copying mobile.html and dependencies..."
cp ~/Desktop/roommate-chat/soulfra-simple/voice-archive/mobile.html .
cp ~/Desktop/roommate-chat/soulfra-simple/voice-archive/mobile.js .
cp ~/Desktop/roommate-chat/soulfra-simple/voice-archive/router-config.js .
cp ~/Desktop/roommate-chat/soulfra-simple/voice-archive/shadow-account.js .
cp ~/Desktop/roommate-chat/soulfra-simple/voice-archive/queue-manager.js .
cp ~/Desktop/roommate-chat/soulfra-simple/voice-archive/connection-monitor.js .

# Commit and push
echo "📤 Pushing to GitHub..."
git add mobile.html mobile.js router-config.js shadow-account.js queue-manager.js connection-monitor.js
git commit -m "Add mobile.html - Touch-optimized voice recording

🎤 Generated with Claude Code
"
git push

echo ""
echo "✅ Deployed!"
echo ""
echo "📱 Your mobile app is now live at:"
echo "   https://cringeproof.com/mobile.html"
echo ""
echo "⏱️  GitHub Pages may take 1-2 minutes to update."
echo ""

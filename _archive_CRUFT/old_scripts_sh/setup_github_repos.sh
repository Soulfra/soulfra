#!/bin/bash
# Clone all Soulfra GitHub repos for publishing

REPOS_DIR="/Users/matthewmauer/Desktop/roommate-chat/github-repos"

echo "📦 Setting up GitHub repos for publishing..."

# Create repos directory
mkdir -p "$REPOS_DIR"
cd "$REPOS_DIR"

# Main domains
repos=(
    "soulfra"
    "calriven"
    "deathtodata"
    "mascotrooms-site"
    "dealordelete-site"
    "shiprekt-site"
    "sellthismvp-site"
    "saveorsink-site"
    "finishthisrepo-site"
)

for repo in "${repos[@]}"; do
    echo "---"
    echo "🔄 Processing $repo..."

    if [ -d "$repo" ]; then
        echo "✅ Already exists, pulling latest..."
        cd "$repo"
        git pull
        cd ..
    else
        echo "📥 Cloning from GitHub..."
        git clone "https://github.com/Soulfra/$repo.git"
    fi
done

echo ""
echo "✅ All repos ready!"
echo ""
echo "📂 Repos location: $REPOS_DIR"
echo ""
echo "Next step: Update publisher_routes.py to use these repos"

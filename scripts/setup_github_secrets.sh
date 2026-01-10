#!/bin/bash
# GitHub Secrets Setup Guide
# This script generates the GitHub secrets needed for CI/CD workflows

set -e

echo "🔐 GitHub Secrets Setup"
echo "======================="
echo
echo "This script will help you set up GitHub secrets for deployment workflows."
echo
echo "You need to add these secrets to your GitHub repository:"
echo "  Settings → Secrets and variables → Actions → New repository secret"
echo

# Generate JWT secret if not exists
if [ ! -f "domain_config/secrets.env" ]; then
    echo "⚠️  domain_config/secrets.env not found"
    echo "   Creating from template..."
    cp domain_config/secrets.env.example domain_config/secrets.env
fi

echo "📋 Required GitHub Secrets:"
echo

# 1. JWT_SECRET
echo "1. JWT_SECRET"
echo "   Purpose: Sign authentication tokens"
if grep -q "JWT_SECRET=" domain_config/secrets.env 2>/dev/null; then
    JWT_SECRET=$(grep "JWT_SECRET=" domain_config/secrets.env | cut -d'=' -f2)
    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your-256-bit-random-secret-here" ]; then
        JWT_SECRET=$(openssl rand -hex 32)
        echo "   Generated: $JWT_SECRET"
    else
        echo "   Found in secrets.env: $JWT_SECRET"
    fi
else
    JWT_SECRET=$(openssl rand -hex 32)
    echo "   Generated: $JWT_SECRET"
fi
echo

# 2. SERVER_HOST
echo "2. SERVER_HOST"
echo "   Purpose: Production server IP or hostname"
read -p "   Enter server IP/hostname (e.g., 123.45.67.89): " SERVER_HOST
echo

# 3. SERVER_USER
echo "3. SERVER_USER"
echo "   Purpose: SSH user for deployment"
read -p "   Enter SSH username (default: www-data): " SERVER_USER
SERVER_USER=${SERVER_USER:-www-data}
echo

# 4. SERVER_SSH_KEY
echo "4. SERVER_SSH_KEY"
echo "   Purpose: Private SSH key for deployment"
echo "   To generate a new SSH key:"
echo "     ssh-keygen -t ed25519 -C 'github-deploy' -f ~/.ssh/github_deploy"
echo "     cat ~/.ssh/github_deploy  # This is your private key"
echo "     cat ~/.ssh/github_deploy.pub  # Add this to server's ~/.ssh/authorized_keys"
echo
read -p "   Press Enter when you have your SSH private key ready..."
echo

# 5. DEPLOY_PATH
echo "5. DEPLOY_PATH"
echo "   Purpose: Path to code directory on server"
read -p "   Enter deploy path (default: /var/www/soulfra-simple): " DEPLOY_PATH
DEPLOY_PATH=${DEPLOY_PATH:-/var/www/soulfra-simple}
echo

# 6. DATABASE_PATH
echo "6. DATABASE_PATH"
echo "   Purpose: Path to SQLite database on server"
read -p "   Enter database path (default: $DEPLOY_PATH/soulfra.db): " DATABASE_PATH
DATABASE_PATH=${DATABASE_PATH:-$DEPLOY_PATH/soulfra.db}
echo

# Summary
echo "================================"
echo "📝 Summary of GitHub Secrets"
echo "================================"
echo
echo "Add these to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo
echo "Secret Name         | Value"
echo "-------------------|-----------------------------------------"
echo "JWT_SECRET         | $JWT_SECRET"
echo "SERVER_HOST        | $SERVER_HOST"
echo "SERVER_USER        | $SERVER_USER"
echo "SERVER_SSH_KEY     | [Your SSH private key]"
echo "DEPLOY_PATH        | $DEPLOY_PATH"
echo "DATABASE_PATH      | $DATABASE_PATH"
echo

# Save to local env file
echo "💾 Saving to domain_config/secrets.env..."
cat > domain_config/secrets.env << EOF
# Soulfra Multi-Domain Network - Production Secrets
# Generated: $(date)

# JWT Secret (for authentication tokens)
JWT_SECRET=$JWT_SECRET

# Database
DATABASE_URL=sqlite:///soulfra.db

# Email (optional but recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@soulfra.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soulfra.com

# Geolocation for StPetePros (optional)
IPAPI_KEY=your-ipapi-key  # Free at https://ipapi.co/

# Production mode
FLASK_ENV=production
FLASK_DEBUG=False

# Server deployment (for reference only - NOT used by Flask)
# These values should be added to GitHub Secrets
# SERVER_HOST=$SERVER_HOST
# SERVER_USER=$SERVER_USER
# DATABASE_PATH=$DATABASE_PATH
EOF

echo "✅ Saved to domain_config/secrets.env"
echo
echo "⚠️  IMPORTANT: Never commit domain_config/secrets.env to git!"
echo "   It's already in .gitignore"
echo

# Check if .gitignore exists
if [ -f ".gitignore" ]; then
    if ! grep -q "secrets.env" .gitignore; then
        echo "secrets.env" >> .gitignore
        echo "⚠️  Added secrets.env to .gitignore"
    fi
fi

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "  1. Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo "  2. Click 'New repository secret'"
echo "  3. Add each secret from the summary above"
echo "  4. Test deployment workflow"

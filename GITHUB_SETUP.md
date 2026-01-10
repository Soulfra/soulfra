# GitHub Setup Guide
**Soulfra Multi-Domain Network - Version Control & CI/CD**

This guide walks you through connecting your local Soulfra codebase to GitHub and setting up automated deployments.

---

## Overview

Once connected to GitHub, you'll have:
- ✅ Version control for all 9 domains
- ✅ Automated deployments via GitHub Actions
- ✅ Voice memo → GitHub issue workflow
- ✅ Encrypted secrets management
- ✅ Production deployment automation

---

## Quick Start

```bash
# 1. Create GitHub repository (do this first on GitHub.com)
# Go to: https://github.com/new
# Repository name: soulfra-simple
# Description: Multi-domain network with unified auth
# Visibility: Private (recommended)

# 2. Run the setup script
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
bash scripts/github_setup.sh

# 3. Configure GitHub secrets
bash scripts/setup_github_secrets.sh

# 4. Verify workflows
git push origin main  # Triggers deployment workflow
```

---

## Step-by-Step Setup

### Step 1: Create GitHub Repository

1. **Go to GitHub**: https://github.com/new

2. **Fill in details:**
   - Repository name: `soulfra-simple`
   - Description: `Soulfra Multi-Domain Network - Unified auth, professional directories, voice workflows`
   - Visibility: **Private** (recommended - contains sensitive config)
   - ❌ **Do NOT** initialize with README, .gitignore, or license (we already have these)

3. **Click "Create repository"**

4. **Copy the repository URL:**
   - SSH: `git@github.com:YOUR_USERNAME/soulfra-simple.git`
   - HTTPS: `https://github.com/YOUR_USERNAME/soulfra-simple.git`

### Step 2: Initialize Git (if not already done)

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Check if git is initialized
git status

# If not initialized:
git init
git branch -M main
```

### Step 3: Run GitHub Setup Script

```bash
bash scripts/github_setup.sh
```

This script will:
1. Check if remote origin exists
2. Add remote origin (your GitHub repo URL)
3. Stage all files
4. Create initial commit
5. Push to GitHub

**What gets committed:**
- ✅ All Python code (app.py, auth_bridge.py, etc.)
- ✅ Configuration (domain_config/, config.py)
- ✅ Templates (templates/)
- ✅ Workflows (.github/workflows/)
- ✅ Documentation (*.md files)
- ❌ Secrets (domain_config/secrets.env) - excluded via .gitignore
- ❌ Database (soulfra.db) - excluded via .gitignore
- ❌ Virtual environment (venv/) - excluded via .gitignore

### Step 4: Configure GitHub Secrets

```bash
bash scripts/setup_github_secrets.sh
```

This script generates secrets and shows you what to add to GitHub.

**GitHub Secrets Location:**
```
https://github.com/YOUR_USERNAME/soulfra-simple/settings/secrets/actions
```

**Required Secrets:**

| Secret Name | Purpose | Example Value |
|------------|---------|---------------|
| `JWT_SECRET` | Sign authentication tokens | `a1b2c3d4e5f6...` (64 chars) |
| `SERVER_HOST` | Production server IP | `123.45.67.89` |
| `SERVER_USER` | SSH user for deployment | `www-data` |
| `SERVER_SSH_KEY` | Private SSH key | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DEPLOY_PATH` | Code directory on server | `/var/www/soulfra-simple` |
| `DATABASE_PATH` | Path to SQLite DB on server | `/var/www/soulfra-simple/soulfra.db` |

**How to add secrets:**

1. Go to: `https://github.com/YOUR_USERNAME/soulfra-simple/settings/secrets/actions`
2. Click **"New repository secret"**
3. Enter **Name** and **Secret value**
4. Click **"Add secret"**
5. Repeat for all 5 secrets

### Step 5: Set Up SSH Key for Deployment

If you don't have an SSH key for GitHub deployments:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "github-deploy-soulfra" -f ~/.ssh/github_deploy_soulfra

# View private key (add this to GitHub secret SERVER_SSH_KEY)
cat ~/.ssh/github_deploy_soulfra

# View public key (add this to server's ~/.ssh/authorized_keys)
cat ~/.ssh/github_deploy_soulfra.pub
```

**On your production server:**

```bash
# Login to server
ssh your-user@YOUR_SERVER_IP

# Add public key to authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## GitHub Workflows

Your repository includes 3 automated workflows:

### 1. Deployment Workflow (`.github/workflows/deploy.yml`)

**Triggers:**
- Push to `main` branch
- Manual trigger via GitHub UI

**What it does:**
1. SSHs into production server
2. Pulls latest code from GitHub
3. Runs database migrations
4. Restarts Flask service
5. Clears cache

**Manual trigger:**
```
https://github.com/YOUR_USERNAME/soulfra-simple/actions/workflows/deploy.yml
→ Click "Run workflow"
```

### 2. Voice Email Processor (`.github/workflows/voice-email-processor.yml`)

**Triggers:**
- Scheduled (checks for new voice emails)
- Manual trigger

**What it does:**
1. Fetches voice memos from email
2. Decrypts and transcribes
3. Extracts ideas using Ollama
4. Creates GitHub issues

### 3. Tests Workflow (`.github/workflows/tests.yml`) *(if you create it)*

Run automated tests on every push.

---

## Updating Domain Config Path

The deployment workflow references `/var/www/soulfra-simple`. If your code is elsewhere:

**Option 1: Move code to /var/www/soulfra-simple**

```bash
# On server
sudo mkdir -p /var/www
sudo mv ~/Desktop/roommate-chat/soulfra-simple /var/www/soulfra-simple
sudo chown -R www-data:www-data /var/www/soulfra-simple
```

**Option 2: Update workflow paths**

Edit `.github/workflows/deploy.yml`:

```yaml
# Change all instances of:
/var/www/soulfra-simple

# To your actual path:
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
```

---

## Voice Memo → GitHub Workflow

See `VOICE_GITHUB_WORKFLOW.md` for full integration guide.

**How it works:**

1. **Record voice memo** on iPhone/Siri Shortcuts
2. **Email sent** to your inbox with encrypted audio
3. **GitHub Action** checks email every hour
4. **Voice processed**:
   - Decrypted with AES-256-GCM
   - Transcribed with Whisper
   - Ideas extracted with Ollama
5. **GitHub issue created** with structured ideas
6. **Deployment triggered** (optional)

---

## Verifying Setup

### Check Git Status

```bash
git status
git remote -v
```

Expected output:
```
origin  git@github.com:YOUR_USERNAME/soulfra-simple.git (fetch)
origin  git@github.com:YOUR_USERNAME/soulfra-simple.git (push)
```

### Check GitHub Secrets

Go to: `https://github.com/YOUR_USERNAME/soulfra-simple/settings/secrets/actions`

You should see 6 secrets:
- JWT_SECRET
- SERVER_HOST
- SERVER_USER
- SERVER_SSH_KEY
- DEPLOY_PATH
- DATABASE_PATH

### Test Deployment Workflow

```bash
# Make a small change
echo "# Test deployment" >> README.md

# Commit and push
git add README.md
git commit -m "Test deployment workflow"
git push origin main
```

Go to: `https://github.com/YOUR_USERNAME/soulfra-simple/actions`

You should see a workflow run triggered by your push.

---

## Common Issues

### Issue: "Permission denied (publickey)"

**Cause:** SSH key not added to server or GitHub

**Solution:**
1. Verify public key is in server's `~/.ssh/authorized_keys`
2. Verify private key is in GitHub secret `SERVER_SSH_KEY`
3. Test SSH: `ssh -i ~/.ssh/github_deploy_soulfra your-user@YOUR_SERVER_IP`

### Issue: "Workflow failed: Cannot connect to server"

**Cause:** Server IP or user incorrect

**Solution:**
1. Verify `SERVER_HOST` in GitHub secrets matches server IP
2. Verify `SERVER_USER` has SSH access
3. Check server firewall allows SSH (port 22)

### Issue: "Database migration failed"

**Cause:** Database path incorrect or permissions issue

**Solution:**
1. Verify `DATABASE_PATH` in GitHub secrets
2. Check file exists: `ssh user@server "ls -la /var/www/soulfra-simple/soulfra.db"`
3. Check permissions: `chown www-data:www-data soulfra.db`

---

## Next Steps

After GitHub setup:

1. **Configure DNS** - Point all 9 domains to server (see `DNS_SETUP.md`)
2. **Enable encryption** - Encrypt sensitive database columns (see `DATABASE_ENCRYPTION.md`)
3. **Test voice workflows** - Record and process voice memo (see `VOICE_GITHUB_WORKFLOW.md`)
4. **Monitor deployments** - Watch GitHub Actions for automated deployments

---

## Security Checklist

- [ ] Repository is **private** (or secrets.env is in .gitignore)
- [ ] GitHub secrets are set (JWT_SECRET, SERVER_SSH_KEY, etc.)
- [ ] SSH keys are unique per deployment (don't reuse personal keys)
- [ ] Server firewall restricts SSH to known IPs (optional but recommended)
- [ ] Database backups enabled (see `PRODUCTION_DEPLOYMENT.md`)
- [ ] SSL certificates configured for all 9 domains

---

## Support

**Documentation:**
- GitHub Actions: https://docs.github.com/en/actions
- SSH Keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

**Soulfra Docs:**
- Production Deployment: `PRODUCTION_DEPLOYMENT.md`
- Voice Workflows: `VOICE_GITHUB_WORKFLOW.md`
- DNS Setup: `DNS_SETUP.md` (to be created)

---

**You're now connected to GitHub!** 🎉

Your multi-domain network is version-controlled and ready for automated deployments.

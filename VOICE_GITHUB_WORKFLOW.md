# Voice → GitHub Workflow
**Soulfra Multi-Domain Network - Voice-Driven Development**

Transform voice memos into GitHub issues and trigger automated deployments.

---

## Overview

The Voice → GitHub workflow lets you:

1. **Record voice memo** on iPhone (via Siri Shortcuts or app)
2. **Voice memo emailed** to your inbox with encryption
3. **GitHub Action triggered** - checks email for new voice memos
4. **Voice processed**:
   - Decrypted with AES-256-GCM
   - Transcribed with Whisper
   - Ideas extracted with Ollama
5. **GitHub issue created** with structured markdown
6. **Optional: Deploy triggered** based on issue labels

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  iPhone                                                 │
│  - Record voice memo (Siri Shortcuts)                  │
│  - Encrypt with AES-256-GCM                            │
│  - Email to voice@soulfra.com                          │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│  Email Inbox (voice@soulfra.com)                       │
│  - Encrypted .m4a attachment                            │
│  - Encryption key in email body or QR code             │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│  GitHub Action: voice-email-processor.yml              │
│  - Triggered hourly or manually                        │
│  - Fetches emails via IMAP                             │
│  - Downloads encrypted voice attachments               │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│  voice_memo_dissector.py                               │
│  - Decrypts audio with encryption key                  │
│  - Transcribes with Whisper                            │
│  - Extracts structured ideas with Ollama               │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│  voice_to_github.py (new)                              │
│  - Formats ideas as GitHub issue                       │
│  - Tags with labels (feature, bug, idea, etc.)         │
│  - Creates issue via GitHub API                        │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│  GitHub Repository                                      │
│  - New issue created with voice transcript             │
│  - Assignees, labels, projects auto-assigned           │
│  - Optional: Trigger deployment workflow               │
└────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Set up email credentials in GitHub Secrets
# EMAIL_USERNAME=voice@soulfra.com
# EMAIL_PASSWORD=your-app-password

# 2. Generate GitHub personal access token
# Settings → Developer settings → Personal access tokens → Generate new token
# Scopes: repo (full control)

# 3. Add to GitHub Secrets
# GITHUB_TOKEN_FOR_ISSUES=ghp_xxx...

# 4. Test voice-to-issue conversion locally
python3 voice_to_github.py test.m4a

# 5. Trigger workflow manually
# Go to: https://github.com/YOUR_USERNAME/soulfra-simple/actions/workflows/voice-email-processor.yml
# Click "Run workflow"
```

---

## Step-by-Step Setup

### Step 1: Configure Email for Voice Memos

**Option A: Gmail**

1. Enable 2FA: https://myaccount.google.com/security
2. Generate app password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "Soulfra Voice Memos"
   - Copy 16-character password

3. Add to GitHub Secrets:
   - `EMAIL_USERNAME` = `voice@soulfra.com`
   - `EMAIL_PASSWORD` = `abcd efgh ijkl mnop` (app password)
   - `EMAIL_IMAP_SERVER` = `imap.gmail.com`
   - `EMAIL_IMAP_PORT` = `993`

**Option B: Custom Email Server**

1. Get IMAP credentials from your email provider
2. Add to GitHub Secrets as above

### Step 2: Generate GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `Soulfra Voice Issue Creator`
4. Expiration: **No expiration** (or 1 year)
5. Scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
6. Click **"Generate token"**
7. Copy token (e.g., `ghp_1234567890abcdef...`)

**Add to GitHub Secrets:**

- Secret name: `GITHUB_TOKEN_FOR_ISSUES`
- Secret value: `ghp_1234567890abcdef...`

### Step 3: Create Voice-to-GitHub Integration

The integration already exists in `.github/workflows/voice-email-processor.yml`, but it needs the new `voice_to_github.py` script.

Create `voice_to_github.py`:

```bash
# This file will be created in the next section
```

### Step 4: Test Voice Processing Locally

```bash
# Test voice dissection (already working)
python3 voice_memo_dissector.py /path/to/voice_memo.m4a

# Test GitHub issue creation
python3 voice_to_github.py /path/to/voice_memo.m4a
```

---

## voice_to_github.py Script

This script converts voice transcripts to GitHub issues.

**Location:** `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice_to_github.py`

**Features:**
- Extracts ideas from voice transcripts
- Formats as structured GitHub issue (markdown)
- Auto-assigns labels based on keywords
- Creates issue via GitHub API
- Links related issues

**Usage:**
```bash
# Process voice memo and create GitHub issue
python3 voice_to_github.py recording.m4a

# Process with custom labels
python3 voice_to_github.py recording.m4a --labels feature,ui

# Dry run (don't create issue)
python3 voice_to_github.py recording.m4a --dry-run
```

---

## GitHub Workflow Integration

### Existing Workflow: `.github/workflows/voice-email-processor.yml`

This workflow already exists and needs to be connected to `voice_to_github.py`.

**Triggers:**
- **Schedule**: Runs every hour (`cron: '0 * * * *'`)
- **Manual**: Via GitHub Actions UI

**What it does:**
1. Connects to email via IMAP
2. Searches for unread emails with voice attachments
3. Downloads encrypted .m4a files
4. Passes to voice dissector
5. **(NEW)** Creates GitHub issues from extracted ideas
6. Marks emails as read

### New Workflow: `.github/workflows/voice-to-deployment.yml`

Create this workflow to auto-deploy when voice issues are labeled "deploy":

```yaml
name: Voice-Triggered Deployment

on:
  issues:
    types: [labeled]

jobs:
  deploy-on-voice-request:
    if: github.event.label.name == 'deploy-now'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Trigger deployment
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          event-type: voice-deploy
          client-payload: '{"issue": "${{ github.event.issue.number }}", "title": "${{ github.event.issue.title }}"}'

      - name: Comment on issue
        uses: peter-evans/create-or-update-comment@v3
        with:
          issue-number: ${{ github.event.issue.number }}
          body: |
            🚀 **Deployment triggered** by voice memo!

            Deploying to production...
            Track progress: https://github.com/${{ github.repository }}/actions

            Initiated by: @${{ github.actor }}
```

---

## Voice Memo Format

### Recording Best Practices

**Start with action keyword:**
- "Feature: ..." → Creates issue with `feature` label
- "Bug: ..." → Creates issue with `bug` label
- "Idea: ..." → Creates issue with `idea` label
- "Deploy: ..." → Creates issue with `deploy-now` label (triggers deployment)

**Example voice memo:**

> "Feature for StPetePros: Add a review reply system so professionals can respond to customer reviews directly from their inbox. This should have a text editor with formatting options and send email notifications to customers when the professional replies. Also add a dashboard showing average response time."

**Generated GitHub issue:**

```markdown
# Feature: Review Reply System for StPetePros

**Source:** Voice Memo (2026-01-09 19:45)
**Domain:** stpetepros.com
**Category:** Professional Inbox

## Description

Add a review reply system so professionals can respond to customer reviews directly from their inbox.

## Requirements

- [ ] Text editor with formatting options
- [ ] Email notifications to customers when professional replies
- [ ] Dashboard showing average response time

## Transcript

[Full voice transcript here...]

## Implementation Notes

*Ideas extracted by Ollama from voice memo*

---

🎤 Generated from voice memo by Soulfra Voice Workflow
```

---

## Labels and Automation

### Auto-Assigned Labels

| Keyword in Voice Memo | GitHub Label | Priority | Auto-Actions |
|-----------------------|--------------|----------|--------------|
| "feature", "add" | `feature` | Medium | Assign to roadmap project |
| "bug", "fix", "broken" | `bug` | High | Assign to @you, notify team |
| "idea", "maybe" | `idea` | Low | Archive for future review |
| "urgent", "asap" | `priority-high` | Critical | Send notification immediately |
| "deploy", "push live" | `deploy-now` | Critical | Trigger deployment workflow |
| "stpetepros" | `stpetepros` | - | Assign to StPetePros project |
| "cringeproof" | `cringeproof` | - | Assign to CringeProof project |

### GitHub Projects Integration

Auto-add issues to projects based on domain:

```python
# In voice_to_github.py
DOMAIN_TO_PROJECT = {
    'stpetepros': 'StPetePros Roadmap',
    'cringeproof': 'CringeProof Features',
    'soulfra': 'Core Platform',
}
```

---

## Security

### Voice Memo Encryption

All voice memos are encrypted before being emailed:

1. **iPhone records** → .m4a audio file
2. **Siri Shortcut encrypts** with AES-256-GCM
3. **Encryption key** included in email body or QR code
4. **GitHub Action decrypts** using `voice_encryption.py`

### GitHub Secrets

Required secrets:

| Secret Name | Purpose | Example |
|-------------|---------|---------|
| `EMAIL_USERNAME` | IMAP username | `voice@soulfra.com` |
| `EMAIL_PASSWORD` | IMAP app password | `abcd efgh ijkl mnop` |
| `EMAIL_IMAP_SERVER` | IMAP server | `imap.gmail.com` |
| `EMAIL_IMAP_PORT` | IMAP port | `993` |
| `GITHUB_TOKEN_FOR_ISSUES` | GitHub API token | `ghp_xxx...` |
| `DB_ENCRYPTION_KEY` | Database encryption key | `xxx...` (base64) |

---

## Monitoring

### Check Workflow Runs

Go to: `https://github.com/YOUR_USERNAME/soulfra-simple/actions/workflows/voice-email-processor.yml`

You'll see:
- ✅ Successful runs (issue created)
- ⚠️ No voice memos found
- ❌ Failed (check logs)

### Email Logs

Voice email processor logs to GitHub Actions:

```
📧 Connecting to imap.gmail.com:993...
✅ Connected
📬 Checking inbox for voice memos...
✅ Found 2 unread emails with attachments
🎤 Processing: voice_memo_2026-01-09.m4a
🔓 Decrypting with key: xxx...
📝 Transcribing with Whisper...
🧠 Extracting ideas with Ollama...
✅ Created GitHub issue #42: "Feature: Review Reply System"
```

---

## Troubleshooting

### Issue: "Failed to connect to email"

**Cause:** Wrong IMAP credentials

**Solution:**
1. Verify `EMAIL_USERNAME` and `EMAIL_PASSWORD` in GitHub Secrets
2. Check IMAP is enabled in email settings
3. Try manual IMAP connection:
   ```bash
   openssl s_client -connect imap.gmail.com:993
   a login voice@soulfra.com "app-password"
   a list "" "*"
   ```

### Issue: "GitHub API error: 401 Unauthorized"

**Cause:** Invalid or expired GitHub token

**Solution:**
1. Regenerate token: https://github.com/settings/tokens
2. Update `GITHUB_TOKEN_FOR_ISSUES` in GitHub Secrets
3. Ensure token has `repo` scope

### Issue: "Decryption failed"

**Cause:** Encryption key missing or incorrect

**Solution:**
1. Verify encryption key is in email body
2. Check `voice_encryption.py` is using correct key format
3. Re-encrypt voice memo with correct key

---

## Next Steps

After voice workflow is set up:

1. **Test end-to-end** - Record voice memo → Check GitHub issues
2. **Set up Siri Shortcuts** - Quick voice recording on iPhone
3. **Configure notifications** - Alert when new issue created
4. **Customize labels** - Add domain-specific labels
5. **Integrate with projects** - Auto-add to GitHub Projects

---

## Support

**Documentation:**
- Voice Encryption: `voice_encryption.py`
- Voice Dissector: `voice_memo_dissector.py`
- GitHub API: https://docs.github.com/en/rest/issues

**Workflows:**
- Email Processor: `.github/workflows/voice-email-processor.yml`
- Deployment: `.github/workflows/voice-to-deployment.yml`

---

**Your voice memos now create GitHub issues automatically!** 🎤→📋

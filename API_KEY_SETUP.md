# 🔐 CringeProof API Key Authentication

## Why Add Auth?

Currently anyone on your WiFi can:
- POST fake recordings
- Spam your database
- Read all your ideas

Adding an API key prevents this.

---

## Quick Setup (10 Minutes)

### Step 1: Generate API Key

```bash
# On your Mac terminal
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output (example: `kJ8xYz3mN9qWpL2vR5tBh7sC4fG1nM6jK0dX8eU`)

### Step 2: Set Environment Variable

```bash
# Add to ~/.zshrc or ~/.bashrc
export CRINGEPROOF_API_KEY="YOUR_KEY_HERE"

# Reload shell
source ~/.zshrc
```

### Step 3: Restart PM2

```bash
pm2 restart cringeproof-api
```

### Step 4: Update iOS Shortcut

In your shortcut:
1. Tap **"Get Contents of URL"** action
2. Tap **Headers** → **Add new field**
3. Key: `X-API-Key`
4. Value: `YOUR_KEY_HERE` (paste the key)
5. Done!

---

## For Multiple Users

### Option 1: Shared Key (Simple)

Everyone uses same API key (less secure but easy).

### Option 2: Per-User Keys (Better)

Create user table:
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_name TEXT,
    api_key TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO api_keys (user_name, api_key) VALUES
    ('Matt', 'key-for-matt-abc123'),
    ('Friend', 'key-for-friend-xyz789');
```

Backend checks key → identifies user → saves recordings with user_id.

---

## Alternative: No Auth (Current)

**Keep it simple if:**
- Only you use it
- Only works on your WiFi
- Laptop password-protected
- Low risk of abuse

**Your call!**

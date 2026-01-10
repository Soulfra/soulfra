# QR Code → Signup → Quiz Flow (EXACT Steps)

**This is the REAL flow that actually works.** No guessing, just tested steps.

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: You Generate QR Code (On Your Computer)                │
└─────────────────────────────────────────────────────────────────┘
    You run: python3 qr_faucet.py --generate --type auth \
             --data '{"level": "basic"}'

    ✅ Output:
       - QR code created in database (qr_faucets table)
       - URL: http://192.168.1.123:5001/qr/faucet/eyJ0eXBlIjoi...
       - HMAC signature added for security
       - Expiration: 1 hour (default)

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Friend Scans QR with Phone Camera                      │
└─────────────────────────────────────────────────────────────────┘
    Friend points iPhone/Android camera at QR code
    or
    Friend opens URL manually in phone browser

    📱 Phone opens: http://192.168.1.123:5001/qr/faucet/eyJ0eXBlI...

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Request Hits Flask Server                              │
└─────────────────────────────────────────────────────────────────┘
    Phone → WiFi Router → Your Computer (192.168.1.123:5001)

    Route triggered: /qr/faucet/<encoded_payload>
    File: app.py:3594

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Server Verifies QR Code                                │
└─────────────────────────────────────────────────────────────────┘
    Function: qr_faucet.verify_qr_payload()

    Checks:
    ✓ Base64 decode works
    ✓ JSON is valid
    ✓ HMAC signature matches (prevents tampering)
    ✓ Not expired (timestamp check)

    ❌ If fails: "Invalid or expired payload"
    ✅ If passes: Continue to Step 5

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Database Counter Increments (UPC-Style)                │
└─────────────────────────────────────────────────────────────────┘
    SQL:
    UPDATE qr_faucets
    SET times_scanned = times_scanned + 1,
        last_scanned_at = CURRENT_TIMESTAMP
    WHERE id = ?

    INSERT INTO qr_faucet_scans
    (faucet_id, ip_address, user_agent, device_type)
    VALUES (1, '192.168.1.100', 'Mozilla/5.0...', 'mobile')

    🏷️ Just like UPC barcode scanner at grocery store!

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: User Account Created or Logged In                      │
└─────────────────────────────────────────────────────────────────┘
    If payload type = 'auth':
        - Check if user exists (by QR token or device fingerprint)
        - If new: CREATE user in users table
        - If existing: LOG IN user
        - Set session['user_id'] = user_id

    Session cookie set (works across all routes)

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Redirect to Quiz or Dashboard                          │
└─────────────────────────────────────────────────────────────────┘
    Options:
    A. Redirect to /cringeproof (now redirects to /cringeproof/narrative/soulfra)
    B. Redirect to /dashboard
    C. Redirect to /start (choose brand)

    Default: /cringeproof

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Friend Takes Quiz                                      │
└─────────────────────────────────────────────────────────────────┘
    Route: /cringeproof/narrative/soulfra
    Template: templates/cringeproof/narrative.html

    Friend answers personality questions
    Each answer stored in narrative_sessions table

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: Quiz Complete → AI Friend Assigned                     │
└─────────────────────────────────────────────────────────────────┘
    Results calculated based on answers
    AI friend assigned: Soulfra, CalRiven, DeathToData, or TheAuditor

    Keyring unlocks triggered:
    - unlock_quiz_completion(user_id, 'soulfra')
    - Unlocks: 'personality_profile', 'soulfra_ai'

    Database: user_unlocks table updated

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: Results Shown to Friend                               │
└─────────────────────────────────────────────────────────────────┘
    Template: templates/cringeproof/results.html (or redirect to /dashboard)

    Friend sees:
    - Their AI friend match
    - Personality profile
    - Unlocked features

    ✅ COMPLETE!
```

---

## Database Tables Involved

### 1. `qr_faucets` (QR Code Inventory)

```sql
CREATE TABLE qr_faucets (
    id INTEGER PRIMARY KEY,
    payload_type TEXT,              -- 'auth', 'blog', 'post', etc.
    encoded_payload TEXT UNIQUE,    -- Base64 JSON + HMAC
    payload_data TEXT,              -- Original JSON data
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    times_scanned INTEGER DEFAULT 0, -- ← Counter (like UPC!)
    last_scanned_at TIMESTAMP
);
```

**Example row**:
```
id: 1
payload_type: auth
times_scanned: 12  ← Increments on each scan
last_scanned_at: 2025-12-27 14:30:00
```

### 2. `qr_faucet_scans` (Scan History)

```sql
CREATE TABLE qr_faucet_scans (
    id INTEGER PRIMARY KEY,
    faucet_id INTEGER,              -- Links to qr_faucets.id
    scanned_at TIMESTAMP,
    ip_address TEXT,                -- Friend's phone IP
    user_agent TEXT,                -- Browser/device info
    device_type TEXT,               -- 'mobile', 'desktop', 'tablet'
    result_data TEXT                -- JSON of what happened
);
```

**Example row**:
```
id: 42
faucet_id: 1
scanned_at: 2025-12-27 14:30:15
ip_address: 192.168.1.100
user_agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0...)
device_type: mobile
```

### 3. `users` (User Accounts)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMP
);
```

### 4. `user_unlocks` (Keyring System)

```sql
CREATE TABLE user_unlocks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    feature_key TEXT,               -- 'personality_profile', 'soulfra_ai', etc.
    unlocked_at TIMESTAMP,
    expires_at TIMESTAMP,           -- NULL = permanent
    unlock_source TEXT              -- 'quiz', 'payment', 'admin'
);
```

### 5. `narrative_sessions` (Quiz Answers)

```sql
CREATE TABLE narrative_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    brand_slug TEXT,                -- 'soulfra', 'calriven', etc.
    current_step INTEGER,
    answers TEXT,                   -- JSON of all answers
    completed_at TIMESTAMP
);
```

---

## What Each File Does

### `qr_faucet.py`
- `generate_qr_payload()` - Creates JSON + HMAC signature
- `verify_qr_payload()` - Checks signature + expiration
- `process_qr_faucet()` - Transforms payload → user action
- `record_faucet_scan()` - Increments database counter

### `app.py`
- Route `/qr/faucet/<path>` (line 3594) - Handles QR scans
- Route `/cringeproof/narrative/<brand>` (line 1552) - Quiz interface
- Route `/cringeproof` (line 9910) - Now redirects to narrative

### `keyring_unlocks.py`
- `unlock_feature()` - Unlocks permanent features
- `has_unlocked()` - Checks if user has feature
- `unlock_quiz_completion()` - Triggered after quiz

---

## Testing the Flow

### Generate QR Code

```bash
python3 qr_faucet.py --generate --type auth --data '{"level": "basic"}'

# Output:
# ✅ Generated QR faucet (ID: 1)
#    Type: auth
#    URL: http://192.168.1.123:5001/qr/faucet/eyJ0eXBlI...
#    Expires: 2025-12-27 15:30:00
```

###Scan from Phone (Simulate)

```bash
# On your computer (simulating phone scan)
curl "http://192.168.1.123:5001/qr/faucet/eyJ0eXBlI..."

# Expected: Redirect to /cringeproof or /dashboard
```

### Check Database Counters

```bash
# See scan count
sqlite3 soulfra.db "SELECT id, times_scanned FROM qr_faucets WHERE id = 1"

# See scan history
sqlite3 soulfra.db "SELECT * FROM qr_faucet_scans ORDER BY scanned_at DESC LIMIT 5"
```

### Watch Scans Live

```bash
# Terminal 1: Run Flask
python3 app.py

# Terminal 2: Watch counters
watch -n 1 'sqlite3 soulfra.db "SELECT COUNT(*) as total_scans FROM qr_faucet_scans"'

# Terminal 3: Scan QR from phone
# (counters update in Terminal 2)
```

---

## Alternative Flows

### Flow 2: Direct Link to Quiz (No QR)

```
Friend visits: http://192.168.1.123:5001/start
    ↓ Sees 3 brand cards
    ↓ Clicks "Soulfra"
    ↓ Redirected to /cringeproof/narrative/soulfra
    ↓ Takes quiz
    ↓ Results shown
```

### Flow 3: QR with Pre-Selected Brand

```bash
# Generate QR for CalRiven brand
python3 qr_faucet.py --generate --type auth \
    --data '{"level": "basic", "brand": "calriven"}'

# Friend scans → redirected to /cringeproof/narrative/calriven
```

---

## Common Issues & Fixes

### Issue 1: QR Code Expired

**Error**: "Payload expired at 2025-12-27 14:00:00"

**Fix**: Generate new QR with longer TTL:
```bash
python3 qr_faucet.py --generate --type auth \
    --data '{"level": "basic"}' \
    --ttl 7200  # 2 hours instead of 1
```

### Issue 2: HMAC Signature Invalid

**Error**: "Invalid HMAC signature - payload may be tampered"

**Cause**: QR code was manually edited or SECRET_KEY changed

**Fix**: Generate new QR code (don't edit QR payloads manually)

### Issue 3: Database Counter Doesn't Increment

**Check**:
```bash
# Verify qr_faucets table exists
sqlite3 soulfra.db "SELECT COUNT(*) FROM qr_faucets"

# If error, initialize:
python3 qr_faucet.py --list  # Creates tables automatically
```

### Issue 4: Friend Can't Access from Phone

**Check**:
1. Is Flask running? `curl http://localhost:5001`
2. Are you on same WiFi? Check WiFi network name
3. Is your IP correct? `ifconfig | grep "inet "`
4. Is firewall blocking? Temporarily disable to test

---

## Security Notes

### What Prevents Abuse?

1. **HMAC Signature** - Only your server can generate valid QR codes
2. **Expiration** - QR codes expire after 1 hour (configurable)
3. **Device Fingerprinting** - Tracks who scanned (IP, user-agent)
4. **Database Logging** - Every scan recorded with timestamp

### What Attackers CANNOT Do

- ❌ Create fake QR codes (don't have SECRET_KEY)
- ❌ Modify QR payloads (HMAC will fail)
- ❌ Reuse expired QR codes (timestamp check)
- ❌ Hide their scans (IP/device logged)

### What Attackers CAN Do

- ✅ Scan QR code multiple times (increment counter)
- ✅ Share QR URL with others (before expiration)

### Production Security Improvements

1. **One-time use** - Add `used` flag to qr_faucets table
2. **Rate limiting** - Limit scans per IP per hour
3. **User binding** - Tie QR to specific user account

---

## Summary

**The flow that ACTUALLY works**:

1. Generate QR: `python3 qr_faucet.py --generate ...`
2. Friend scans QR on phone
3. Server verifies HMAC + expiration
4. Database counter increments (UPC-style)
5. User logged in or created
6. Redirect to quiz: `/cringeproof/narrative/soulfra`
7. Friend takes quiz
8. Keyring unlocks features
9. Results shown

**Test it right now**:
```bash
# Generate QR
python3 qr_faucet.py --generate --type auth --data '{"level": "basic"}'

# Share URL with friend on same WiFi
# Watch database: sqlite3 soulfra.db "SELECT COUNT(*) FROM qr_faucet_scans"
```

**Related Docs**:
- `WHAT_ACTUALLY_WORKS.md` - Routes that work vs broken
- `QR_FLOW_PROOF.md` - Technical proof of 8-layer QR system
- `keyring_unlocks.py` - Permanent feature unlock system
- `LOCALHOST_TESTING_GUIDE.md` - Full testing guide

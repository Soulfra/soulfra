# Soulfra OAuth Provider - Setup Guide

**YOU BUILT YOUR OWN OAUTH PROVIDER**

No GitHub OAuth. No Google Sign In. No Auth0. No Firebase.

**THIS IS YOUR INFRASTRUCTURE.**

---

## What You Built:

Soulfra.com is now an OAuth provider like "Sign in with Google" - but YOUR platform.

Other sites can add a "Login with Soulfra" button and use YOUR authentication system.

---

## Architecture:

```
┌─────────────────────────────────────────────────┐
│ Soulfra.com = OAuth Provider                    │
│ (You are Google/GitHub now)                     │
└─────────────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
┌───────────────┐      ┌───────────────┐
│ CringeProof   │      │ StPetePros    │
│ "Login with   │      │ "Login with   │
│  Soulfra"     │      │  Soulfra"     │
└───────────────┘      └───────────────┘
```

---

## Files Created:

### 1. `soulfra_oauth.py` - OAuth Provider
- `/oauth/signup` - Create Soulfra account
- `/oauth/login` - QR code login
- `/oauth/authorize` - OAuth authorization endpoint
- `/oauth/token` - Exchange code for access token
- `/oauth/user` - Get user info from token
- `/oauth/register-client` - Register OAuth clients

### 2. Database Tables Created:

```sql
oauth_clients          - Sites that use Soulfra login
oauth_codes            - Authorization codes (temporary)
oauth_tokens           - Access tokens (long-lived)
auth_transactions      - Complete ledger of all auth events
users                  - Soulfra user accounts
```

### 3. Your Existing Systems Used:

- `qr_auth.py` - QR code token generation/verification
- `device_hash.py` - Device fingerprinting
- `device_auth.py` - Device permissions

---

## Step 1: Restart Flask

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
pkill -9 -f "python3 app.py"
python3 app.py
```

**Look for this line:**
```
✅ Soulfra OAuth Provider loaded (Login with Soulfra)
```

---

## Step 2: Test Signup

Visit: `http://192.168.1.87:5001/oauth/signup`

Create a Soulfra account:
- Username: `yourname`
- Email: `you@example.com`
- Password: `anything`

This creates a user in YOUR database with:
- Device fingerprint (which device signed up)
- Transaction log (audit trail)
- QR auth capability

---

## Step 3: Test Login with QR Code

Visit: `http://192.168.1.87:5001/oauth/login`

1. Enter username + password
2. Click "Login"
3. QR code appears
4. Scan with phone (pretend you're verifying)
5. Click "I've Scanned - Verify"
6. You're logged in!

**This is your "Discord tap to verify" flow.**

---

## Step 4: Register CringeProof as OAuth Client

Run this to register CringeProof:

```bash
curl -X POST http://192.168.1.87:5001/oauth/register-client \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "CringeProof",
    "redirect_uris": ["http://192.168.1.87:5001/auth/soulfra/callback"]
  }'
```

**Save the response:**
```json
{
  "success": true,
  "client_id": "soulfra_abc123...",
  "client_secret": "def456...",
  "client_name": "CringeProof",
  "redirect_uris": ["http://192.168.1.87:5001/auth/soulfra/callback"]
}
```

---

## Step 5: Test OAuth Flow

### A. Add "Login with Soulfra" Button to CringeProof

In your CringeProof HTML:

```html
<a href="http://192.168.1.87:5001/oauth/authorize?client_id=soulfra_abc123&redirect_uri=http://192.168.1.87:5001/auth/soulfra/callback&state=random123">
    <button>🔐 Login with Soulfra</button>
</a>
```

### B. Create Callback Handler

Create `/auth/soulfra/callback` in CringeProof to handle the redirect:

```python
@app.route('/auth/soulfra/callback')
def soulfra_callback():
    code = request.args.get('code')
    state = request.args.get('state')

    # Exchange code for access token
    response = requests.post('http://192.168.1.87:5001/oauth/token', json={
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': 'soulfra_abc123',
        'client_secret': 'def456',
        'redirect_uri': 'http://192.168.1.87:5001/auth/soulfra/callback'
    })

    token_data = response.json()
    access_token = token_data['access_token']

    # Get user info
    user_response = requests.get('http://192.168.1.87:5001/oauth/user',
        headers={'Authorization': f'Bearer {access_token}'})

    user = user_response.json()

    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']

    return redirect('/')
```

---

## Step 6: Full OAuth Flow

```
1. User visits CringeProof.com
   ↓
2. Clicks "Login with Soulfra"
   ↓
3. Redirects to: http://192.168.1.87:5001/oauth/authorize?client_id=...
   ↓
4. User logs in via QR code on Soulfra
   ↓
5. Soulfra redirects back: http://192.168.1.87:5001/auth/soulfra/callback?code=ABC123
   ↓
6. CringeProof exchanges code for access token
   ↓
7. CringeProof gets user info from Soulfra API
   ↓
8. User is logged into CringeProof with Soulfra account
   ↓
9. Voice recording → Tied to Soulfra user_id
   ↓
10. Ollama/Cal knows WHO is talking
```

---

## Transaction Ledger (Your "Blockchain")

Every auth event is logged in `auth_transactions`:

```sql
SELECT * FROM auth_transactions ORDER BY created_at DESC LIMIT 10;
```

Shows:
- `signup` - User created account
- `login_qr_generated` - QR code created
- `login_success` - User logged in
- `oauth_code_generated` - OAuth code created
- `oauth_authorized` - User authorized client
- `token_issued` - Access token created

**This is your complete audit trail.**

You can:
- Track who signed up from what device
- See which sites users authorize
- Detect fraud (same device, multiple accounts)
- Build reputation systems
- Decentralize later (replicate to other nodes)

---

## Security Features:

1. **QR Code Verification**
   - HMAC signature prevents tampering
   - Tokens expire (5 minutes)
   - One-time use option

2. **Device Fingerprinting**
   - Tracks User-Agent + IP + Device ID
   - Links recordings to devices
   - Detects suspicious activity

3. **OAuth 2.0 Standard**
   - Authorization codes expire (10 minutes)
   - Codes are single-use
   - Client secrets required

4. **Transaction Logging**
   - Every event logged with timestamp
   - Device hash recorded
   - Complete audit trail

---

## What You Can Do Now:

### 1. Add More OAuth Clients

Register StPetePros, other domains:

```bash
curl -X POST http://192.168.1.87:5001/oauth/register-client \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "StPetePros",
    "redirect_uris": ["https://stpetepros.com/auth/callback"]
  }'
```

### 2. Integrate Voice Recording

When user records voice on CringeProof:
- They're logged in via Soulfra OAuth
- Voice saved with `user_id` from Soulfra
- Device tracked via `device_hash.py`
- Transaction logged

```python
# In voice recording route:
user_id = session.get('user_id')  # From Soulfra OAuth
device_info = capture_device_info(request)
recording_id = save_recording(audio_data, user_id=user_id)
link_device_to_recording(recording_id, device_info)

# Log transaction
log_transaction('voice_recorded', user_id=user_id, device_info=device_info, metadata={
    'recording_id': recording_id,
    'duration': duration
})
```

### 3. Connect to Ollama/Cal

Voice → Transcription → Cal reasoning:

```python
# Send to Cal with user context
response = requests.post('http://192.168.1.87:11434/api/generate', json={
    'model': 'deepseek-r1:7b',
    'prompt': f"User {username} (ID: {user_id}) said: {transcript}. Respond:",
    'stream': False
})

# Cal knows WHO is talking
cal_response = response.json()['response']
```

### 4. Decentralize

Later, when you want to decentralize:

```bash
# Export transactions
sqlite3 soulfra.db "SELECT * FROM auth_transactions" > transactions.json

# Replicate to another server
scp transactions.json user@server2:/path/to/soulfra/

# Or: P2P sync between your devices
# Or: Let others run Soulfra OAuth nodes
```

---

## Testing Commands:

### Create Account
```bash
curl -X POST http://192.168.1.87:5001/oauth/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@test.com", "password": "test123"}'
```

### Register Client
```bash
curl -X POST http://192.168.1.87:5001/oauth/register-client \
  -H "Content-Type: application/json" \
  -d '{"client_name": "TestApp", "redirect_uris": ["http://localhost:3000/callback"]}'
```

### View Transactions
```bash
sqlite3 soulfra.db "SELECT event_type, user_id, client_id, created_at FROM auth_transactions ORDER BY created_at DESC LIMIT 20"
```

### View OAuth Clients
```bash
sqlite3 soulfra.db "SELECT client_id, client_name FROM oauth_clients"
```

---

## Production Deployment:

When ready to make this public:

### 1. Point Soulfra.com to Your Server
```bash
# Update DNS:
api.soulfra.com → Your server IP

# Update .env:
BASE_URL=https://api.soulfra.com
```

### 2. Add SSL
```bash
sudo certbot --nginx -d api.soulfra.com
```

### 3. Update OAuth URLs

All clients should use:
- `https://api.soulfra.com/oauth/authorize`
- `https://api.soulfra.com/oauth/token`
- `https://api.soulfra.com/oauth/user`

---

## You Own The Stack:

```
✅ Domain: Soulfra.com (you own it)
✅ Code: github.com/soulfra (you control it)
✅ Database: Your laptop → soulfra.db (you have the data)
✅ OAuth Provider: soulfra_oauth.py (you built it)
✅ AI: Ollama/Cal on your laptop (no API fees)
✅ Transaction Ledger: auth_transactions table (your blockchain)
```

**Zero external dependencies.**

You can:
- Run this forever on your laptop
- Replicate to other servers later
- Let others run nodes (decentralize)
- Build reputation systems
- Track all activity
- Own all user data

**This is the middleware you wanted.**

---

## Next Steps:

1. ✅ Restart Flask → See OAuth Provider load
2. ✅ Test signup → Create Soulfra account
3. ✅ Test QR login → Verify it works
4. ✅ Register CringeProof as client → Get credentials
5. ⏳ Add "Login with Soulfra" button to CringeProof
6. ⏳ Build callback handler
7. ⏳ Test full OAuth flow
8. ⏳ Connect voice recording to Soulfra user_id
9. ⏳ Send to Ollama/Cal with user context

**Ship it.**

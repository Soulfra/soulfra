# Twilio VoIP Integration - Setup Guide (ENCRYPTED)

**Get a real phone number for encrypted voice memos and SMS notes**

People can call or text your number → **AES-256-GCM encrypted** → saved to federated voice system → QR code access → transcribed with Whisper → ideas extracted with Ollama.

🔐 **ENCRYPTED BY DEFAULT** - Uses your federated voice memo encryption system

---

## 📞 What This Does

**Before**:
- Users must visit `/voice` page manually
- Requires QR auth + browser microphone
- Desktop/mobile only

**After**:
- Call **555-YOUR-NUMBER** from ANY phone
- Leave voicemail → **AES-256-GCM encrypted** → saved to federated voice_memos table
- QR code generated for access (key embedded in QR, never stored)
- Text ideas → saved as encrypted notes
- Works from flip phones, landlines, payphones
- **Privacy-first**: Uses your existing federated encryption system

---

## 💰 Pricing

**Twilio Costs** (pay-as-you-go):
- Phone number: **$1.00/month**
- Incoming call: **$0.0085/minute** (~1 cent per minute)
- Incoming SMS: **$0.0075/message** (~3/4 cent per text)
- Recording storage: **$0.0001/minute/month** (negligible)

**Example monthly cost**:
- 100 voicemails × 2 minutes = $1.70
- 50 text messages = $0.38
- **Total: ~$3/month**

---

## 🚀 Quick Setup (15 minutes)

### Step 1: Create Twilio Account

1. Go to [twilio.com/try-twilio](https://twilio.com/try-twilio)
2. Sign up (free trial includes $15 credit)
3. Verify your personal phone number
4. Skip the "product tour" prompts

### Step 2: Buy Phone Number (OR Use Your Existing Number!)

**Option A: Use Your Existing Verizon/AT&T/T-Mobile Number (RECOMMENDED)**

You DON'T need a new number! Use conditional call forwarding from your existing cell phone:

1. Buy a Twilio number ($1/month) - this is just a "voicemail inbox"
2. From your Verizon phone, dial: `*71` + your Twilio number
   - Example: `*71-555-123-4567` (your Twilio number)
3. Wait for confirmation tone
4. Done! Now when you don't answer, calls forward to Twilio → encrypted voicemail

**To disable forwarding:** Dial `*73`

**iPhone Users:** Turn off "Live Voicemail" in Settings → Phone, or *71 won't work

**Option B: Buy a New Twilio Number (if you want a separate business line)**

1. In Twilio Console, go to **Phone Numbers** → **Buy a number**
2. Select country (US numbers are cheapest)
3. Search for available numbers
4. Click **Buy** (~$1/month)
5. Copy your new phone number: `+1 (555) 123-4567`

### Step 3: Get API Credentials

1. In Twilio Console, go to **Account** → **API keys & tokens**
2. Copy:
   - **Account SID**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Auth Token**: (click "Show" to reveal)

### Step 4: Configure Environment

Add to `.env` file:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
```

### Step 5: Install Twilio Python SDK

```bash
pip install twilio
```

### Step 6: Configure Webhooks

**Option A: Using ngrok (for testing)**

```bash
# Start Flask
python3 app.py

# In another terminal, start ngrok
ngrok http 5001

# Copy ngrok URL: https://abc123.ngrok-free.app
```

**Option B: Using your VPS/domain**

If you have a deployed server:
```bash
# Your webhook base URL
https://soulfra.com
```

**Configure Twilio phone number**:

1. Go to **Phone Numbers** → **Manage** → **Active numbers**
2. Click your phone number
3. Under **Voice & Fax**, set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-domain.com/twilio/voice`
   - **Method**: HTTP POST
4. Under **Messaging**, set:
   - **A MESSAGE COMES IN**: Webhook
   - **URL**: `https://your-domain.com/twilio/sms`
   - **Method**: HTTP POST
5. Click **Save**

### Step 7: Test Integration

Visit: `http://localhost:5001/twilio/test`

You should see:
```json
{
  "passed": 4,
  "failed": 0,
  "tests": [
    {"test": "Database", "status": "pass"},
    {"test": "File Permissions", "status": "pass"},
    {"test": "Configuration", "status": "pass"},
    {"test": "Dependencies", "status": "pass"}
  ]
}
```

### Step 8: Make Test Call

1. Call your Twilio number from your phone
2. You should hear: "Welcome to Soulfra voice memo system..."
3. Leave a message after the beep
4. Press `#` when done
5. You should hear: "Thank you! Your message has been saved..."

### Step 9: Verify Voicemail Saved

Check database:
```bash
python3 -c "from database import get_db; db = get_db(); recordings = db.execute('SELECT id, filename, created_at FROM simple_voice_recordings ORDER BY created_at DESC LIMIT 5').fetchall(); print([dict(r) for r in recordings])"
```

Or visit: `http://localhost:5001/voice`

You should see your voicemail in the list!

---

## 📱 How It Works (ENCRYPTED)

### Incoming Call Flow

```
1. Someone calls your Twilio number
   ↓
2. Twilio hits: https://your-domain.com/twilio/voice
   ↓
3. Flask returns TwiML:
   <Response>
     <Say>Welcome to Soulfra...</Say>
     <Record action="/twilio/voicemail" />
   </Response>
   ↓
4. Caller hears greeting, leaves message
   ↓
5. Twilio hits: https://your-domain.com/twilio/voicemail
   ↓
6. Flask downloads recording from Twilio
   ↓
7. 🔐 ENCRYPTS with AES-256-GCM (random 256-bit key)
   ↓
8. Generates QR code with embedded decryption key
   ↓
9. Saves ENCRYPTED audio to voice_memos table (federated system)
   ↓
10. Stores SHA-256 hash of key (NOT the key itself!)
   ↓
11. QR code contains: domain/voice/{memo_id}#{base64_key}
   ↓
12. Whisper transcribes (if configured)
   ↓
13. Ollama extracts ideas (if configured)

🔐 **Privacy**: Encryption key is ONLY in the QR code, never stored on server
🔑 **Access**: Must have QR code to decrypt and play voicemail
🌐 **Federation**: Can share QR code across CalRiven, DeathToData, Soulfra
```

### Incoming SMS Flow

```
1. Someone texts your Twilio number
   ↓
2. Twilio hits: https://your-domain.com/twilio/sms
   ↓
3. Flask saves message to database
   ↓
4. Sends confirmation reply:
   "Thanks! Your note has been saved (ID: 42)"
   ↓
5. User can reply "IDEAS" to extract ideas
```

---

## 🔧 Webhook Routes

All routes are registered at `/twilio/*`:

| Route | Method | Purpose |
|-------|--------|---------|
| `/twilio/voice` | POST | Incoming call handler |
| `/twilio/voicemail` | POST | Save recording after call |
| `/twilio/sms` | POST | Incoming SMS handler |
| `/twilio/status` | POST | Recording status updates |
| `/twilio/config` | GET | Show configuration & setup |
| `/twilio/test` | GET | Test integration |

---

## 🐛 Troubleshooting

### Problem: "Webhook validation failed"

**Cause**: Twilio can't reach your webhook URL

**Solutions**:
1. Make sure Flask is running: `python3 app.py`
2. If using ngrok, make sure it's running: `ngrok http 5001`
3. Check ngrok URL hasn't changed (free tier changes URL on restart)
4. Test webhook manually: `curl https://your-domain.com/twilio/voice`

### Problem: "Missing TWILIO_ACCOUNT_SID"

**Cause**: Environment variables not loaded

**Solutions**:
1. Check `.env` file exists
2. Check `.env` has correct values:
   ```bash
   cat .env | grep TWILIO
   ```
3. Restart Flask to reload env vars

### Problem: "Recording not saving"

**Cause**: File permissions or database issue

**Solutions**:
1. Check `voice_recordings/` directory exists and is writable:
   ```bash
   ls -la voice_recordings/
   ```
2. Check database table exists:
   ```bash
   sqlite3 soulfra.db "SELECT COUNT(*) FROM simple_voice_recordings"
   ```
3. Check Flask logs:
   ```bash
   tail -f flask.log
   ```

### Problem: "Calls work but transcription doesn't"

**Cause**: Whisper not configured

**Solutions**:
1. Voicemails save with `transcription_method='pending_whisper'`
2. Run Whisper transcription manually (if you have Whisper installed)
3. Or leave as-is - you can still listen to audio files

---

## 💡 Advanced Usage

### Custom Greeting

Edit `twilio_integration.py:incoming_call()`:

```python
response.say(
    "Hey! Leave a voice memo for Matt. Beep!",
    voice='alice'
)
```

### Add Caller ID Display

Voicemails include caller phone number in metadata:

```python
# In simple_voice_routes.py
metadata = json.loads(recording['metadata'])
caller = metadata.get('from', 'Unknown')
print(f"Voicemail from: {caller}")
```

### SMS Auto-Reply with Ideas

When someone texts, extract ideas and reply:

```python
# In twilio_integration.py:incoming_sms()
from idea_extractor import extract_ideas

ideas = extract_ideas(message_body)
response.message(f"Ideas: {ideas}")
```

### Forward to Another Number

If voicemail box is full, forward to your cell:

```python
response.dial('+15551234567')  # Your personal number
```

---

## 🌐 Production Deployment

### Option 1: ngrok Paid ($10/month)

**Pros**: Easy, static subdomain
**Cons**: Costs more than Twilio number itself

```bash
ngrok http 5001 --subdomain=soulfra
# Webhook: https://soulfra.ngrok.io/twilio/voice
```

### Option 2: VPS ($5/month)

**Pros**: Cheaper, full control
**Cons**: Requires server setup

```bash
# Deploy Flask to VPS
# Point domain to VPS IP
# Configure SSL (required for webhooks)
# Webhook: https://soulfra.com/twilio/voice
```

### Option 3: Railway/Heroku (Free tier)

**Pros**: Free hosting
**Cons**: May sleep after inactivity

```bash
railway up
# Webhook: https://your-app.railway.app/twilio/voice
```

---

## 📊 Monitoring

### View Configuration

Visit: `http://localhost:5001/twilio/config`

```json
{
  "account_sid_configured": true,
  "auth_token_configured": true,
  "voice_webhook": "https://soulfra.com/twilio/voice",
  "sms_webhook": "https://soulfra.com/twilio/sms",
  "recordings_dir": "/path/to/voice_recordings"
}
```

### View Recent Calls

```bash
# In Twilio Console: Monitor → Logs → Calls
# Shows all incoming calls, status, errors
```

### View Recordings in Database

```bash
sqlite3 soulfra.db "SELECT id, filename, created_at, metadata FROM simple_voice_recordings WHERE filename LIKE '%twilio%' ORDER BY created_at DESC LIMIT 10"
```

---

## 🔐 Privacy & Legal

### What Data is Stored

- Caller phone number (in metadata)
- Call duration
- Recording audio file
- Transcription (if Whisper enabled)
- Timestamp

### GDPR Compliance

If you're in EU or have EU callers:

1. Add privacy notice when greeting:
   ```python
   response.say("This call will be recorded. By continuing, you consent to recording.")
   ```

2. Allow deletion requests:
   ```bash
   # Delete recording by ID
   python3 -c "from database import get_db; db = get_db(); db.execute('DELETE FROM simple_voice_recordings WHERE id = ?', (42,)); db.commit()"
   ```

3. Update privacy policy to mention phone recordings

### Business vs Personal Use

**This guide assumes business use**: customers/partners leaving voicemails on your business line.

**Not for**: harvesting personal contacts, robocalling, spam

---

## 🎯 Next Steps

1. ✅ Set up Twilio account
2. ✅ Buy phone number
3. ✅ Configure webhooks
4. ✅ Test with real call
5. 📧 Add phone number to soulfra.com footer
6. 📧 Update business cards
7. 📧 Share number with beta users
8. 🤖 Set up auto-transcription (Whisper)
9. 🤖 Set up idea extraction (Ollama)
10. 📊 Monitor usage in Twilio Console

---

## 📞 Your Twilio Dashboard

After setup, you'll have:

- **Phone Number**: `+1 (555) 123-4567`
- **Webhook URL**: `https://soulfra.com/twilio/voice`
- **Monthly Cost**: ~$3 (number + ~100 calls)
- **Voicemails**: Saved to `/voice` page automatically

---

**Questions?** Visit `/twilio/config` for configuration status or `/twilio/test` to verify setup.

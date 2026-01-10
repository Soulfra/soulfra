# 🎙️ CringeProof + Siri Integration Guide

## Quick Setup (5 Minutes)

### Option 1: iOS Shortcut (Recommended)

**Step 1: Create the Shortcut**

1. Open **Shortcuts** app on iPhone
2. Tap **+** (top right)
3. Tap **Add Action**
4. Search **"Dictate Text"** → Add it
5. Tap **+** below → Search **"Text"** → Add it
6. In Text action, type your server URL:
   ```
   https://192.168.1.87:5002/api/simple-voice/save
   ```
7. Tap **+** → Search **"Get Contents of URL"** → Add it
8. Configure it:
   - **URL:** Tap and select "Text" (from step 6)
   - **Method:** POST
   - **Request Body:** JSON
   - Tap **Add new field** → **Text**
   - Key: `text`
   - Value: Tap and select **"Dictated Text"**

9. Tap **+** → Search **"Show Result"** → Add it
10. Tap value → Select **"Contents of URL"**

11. Tap **Done** (top right)
12. Name it: **"Log CringeProof Idea"**

**Step 2: Test It**

1. Tap the shortcut
2. Speak: *"Testing Siri integration with CringeProof"*
3. Tap **Done**
4. Should see: `{"success": true, "recording_id": 8, ...}`

**Step 3: Add to Siri**

1. Tap **⋯** on your shortcut
2. Tap **ℹ️** (info icon)
3. **Add to Siri**
4. Say phrase: *"Log my idea"*
5. Tap **Done**

**Now you can say:**
- *"Hey Siri, log my idea"*
- *"Hey Siri, log CringeProof idea"*
- *"Hey Siri, run log my idea"*

---

### Option 2: Add to Home Screen (Web App)

**Step 1: Trust SSL Certificate**

1. Safari → `https://192.168.1.87:5002/`
2. Tap **Show Details**
3. Tap **visit this website**
4. Tap **Visit Website**

**Step 2: Save to Home Screen**

1. Safari → `https://cringeproof.com/record.html`
2. Tap **Share** button
3. Tap **Add to Home Screen**
4. Name it: **CringeProof**
5. Tap **Add**

**Step 3: Use It**

1. Tap CringeProof icon on home screen
2. Opens like native app (no Safari UI)
3. Record voice ideas instantly

---

## Troubleshooting

### "Failed to fetch" Error

**Cause:** SSL certificate not trusted

**Fix:**
1. Safari → `https://192.168.1.87:5002/`
2. Accept certificate warning
3. Try shortcut again

### "No audio" in Recording

**Cause:** Microphone permission not granted

**Fix:**
1. Settings → Safari → Microphone
2. Enable for cringeproof.com

### Shortcut Doesn't Work

**Check:**
1. Mac is on (Flask server running)
2. iPhone on same WiFi
3. Server URL is correct (check `pm2 logs cringeproof-api`)

---

## Advanced: Automation

### Auto-Log Daily Reflection

1. Create shortcut (as above)
2. Shortcuts → **Automation** tab
3. **Create Personal Automation**
4. **Time of Day** → 9:00 PM
5. **Add Action** → **Run Shortcut** → Select your shortcut
6. **Ask Before Running:** OFF (for auto-run)

Now every day at 9 PM, Siri asks you to record a reflection!

---

## Security Note

Currently **NO authentication** - anyone on your WiFi can POST to the API.

To add security, see `API_KEY_SETUP.md` (coming next).

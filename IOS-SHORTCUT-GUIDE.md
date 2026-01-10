# iOS Shortcuts for Soulfra Voice Recording

## Quick Setup (3 minutes)

This creates a Siri shortcut so you can say: **"Hey Siri, record to Soulfra"**

---

## Method 1: Import Shortcut (Easiest)

**Coming soon**: One-tap install link

For now, use Method 2 (manual setup)

---

## Method 2: Manual Setup

### Create "Record to Soulfra" Shortcut

1. Open **Shortcuts** app on iPhone
2. Tap **+** (top right) to create new shortcut
3. Add these actions in order:

#### Action 1: Record Audio
```
Search: "Record Audio"
Tap: "Record Audio"
Settings:
  - Quality: Normal
  - Start Recording: On Tap
  - Finish Recording: On Tap
```

#### Action 2: Set Variable
```
Search: "Set Variable"
Tap: "Set Variable"
Settings:
  - Variable Name: "AudioFile"
  - Value: (leave as "Recorded Audio")
```

#### Action 3: Get Contents of URL
```
Search: "Get Contents of URL"
Tap: "Get Contents of URL"
Settings:
  - URL: https://soulfra.local:5001/api/upload-voice
  - Method: POST
  - Headers:
      Content-Type: multipart/form-data
  - Request Body: Form
  - Form Fields:
      file: AudioFile (select variable)
```

#### Action 4: Show Notification
```
Search: "Show Notification"
Tap: "Show Notification"
Settings:
  - Title: "Uploaded to Soulfra"
  - Body: "Voice memo saved!"
```

4. Tap shortcut name at top
5. Rename to: **"Record to Soulfra"**
6. Tap **Add to Home Screen** (optional)
7. Tap **Done**

---

## Add to Siri

1. Open shortcut you just created
2. Tap **⋯** (three dots)
3. Tap **ℹ️** (info icon)
4. Tap **Add to Siri**
5. Record phrase: **"Record to Soulfra"**
6. Tap **Done**

**Now you can:**
- Say "Hey Siri, record to Soulfra"
- Siri opens recorder
- Tap to start/stop recording
- Auto-uploads to your Mac

---

## Alternative: Text-to-Soulfra

If you want to type ideas instead of recording:

### Create "Text to Soulfra" Shortcut

1. Open **Shortcuts** app
2. Tap **+** to create new shortcut
3. Add these actions:

#### Action 1: Ask for Input
```
Search: "Ask for Input"
Tap: "Ask for Input"
Settings:
  - Prompt: "What's your idea?"
  - Input Type: Text
```

#### Action 2: Set Variable
```
Search: "Set Variable"
Variable Name: "IdeaText"
Value: Provided Input
```

#### Action 3: Get Contents of URL
```
URL: https://soulfra.local:5001/api/ideas/save
Method: POST
Headers:
  Content-Type: application/json
Request Body: JSON
JSON:
{
  "text": IdeaText
}
```

#### Action 4: Show Notification
```
Title: "Saved to Soulfra"
Body: Provided Input
```

**Add to Siri:** "Save idea to Soulfra"

---

## Troubleshooting

### "Cannot Connect to Server"

**Check 1: Same WiFi?**
- iPhone WiFi must match Mac WiFi
- Settings → Wi-Fi → Check network name

**Check 2: Mac Flask running?**
- Terminal on Mac should show: `* Running on https://192.168.1.87:5001`

**Check 3: Certificate trusted?**
- Follow steps in `IPHONE-SSL-SETUP.md` first
- Must AirDrop and install CA certificate

**Check 4: Bonjour working?**
- Try changing URL from `soulfra.local` to your Mac's IP:
- On Mac: `ipconfig getifaddr en0` → example: `192.168.1.87`
- Update Shortcut URL to: `https://192.168.1.87:5001/api/upload-voice`

---

### "SSL Error" / "Not Secure"

You need to install the mkcert root certificate on your iPhone.

See: `IPHONE-SSL-SETUP.md`

**Quick fix:**
1. On Mac: Open Finder
2. Navigate to project: `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/`
3. Find file: `mkcert-root-CA.pem`
4. AirDrop to iPhone
5. iPhone Settings → Profile Downloaded → Install
6. Settings → General → About → Certificate Trust Settings → Enable

---

### "File Upload Failed"

**Change form field name:**
- In shortcut, under "Form Fields"
- Change from `file` to `audio`
- Or keep as `file` (either works)

**Check file format:**
- Shortcuts records as `.m4a` (works fine)
- WebM from browser also works

---

### Shortcut runs but nothing appears in `/suggestion-box`

**Check on Mac:**
```bash
# View recent uploads
curl https://localhost:5001/api/simple-voice/list | python3 -m json.tool

# Or open in browser
https://localhost:5001/suggestion-box
```

**If you see your recording:**
- Transcription might be processing
- Refresh page after 10-15 seconds
- Check terminal for Whisper output

**If you don't see it:**
- Check Flask terminal for errors
- Try uploading again
- Verify endpoint: `/api/upload-voice`

---

## Advanced: Auto-Find Mac on Network

Want the shortcut to find your Mac automatically (even if IP changes)?

### Add Network Discovery

1. Edit your shortcut
2. **Before** "Get Contents of URL", add:

#### Action: Get Contents of URL (Discovery)
```
URL: http://soulfra.local:5001/ping
Method: GET
```

This verifies soulfra.local is reachable before uploading.

If it fails, shortcut will show error instead of hanging.

---

## Using Voice Memos App Directly

Don't want to create a shortcut? Just use Voice Memos:

1. Record in **Voice Memos** app (built-in)
2. Tap recording → Share → Save to Files
3. Open **Safari**
4. Go to: `https://soulfra.local:5001/voice`
5. Tap **Upload** button
6. Select file from Files app

**Pros:**
- No shortcut needed
- Better audio quality
- Can edit before uploading

**Cons:**
- Extra steps
- Can't use Siri

---

## Next Steps

Once shortcuts are working:

### Create More Shortcuts

**Morning Review:**
```
Say: "Hey Siri, morning review"
→ Opens https://soulfra.local:5001/suggestion-box
→ Shows your voice ideas from yesterday
```

**CalRiven Ideas:**
```
Say: "Hey Siri, show CalRiven"
→ Opens https://soulfra.local:5001/@calriven/suggestions
→ Filtered view of data/analysis ideas
```

**Quick Voice Note:**
```
Say: "Hey Siri, quick note"
→ Records voice immediately (no confirmation)
→ Auto-uploads
→ Silent notification
```

---

## Comparison: Shortcuts vs Web Browser

| Feature | iOS Shortcut | Safari Browser |
|---------|-------------|----------------|
| Works offline | ❌ (needs WiFi) | ❌ (needs WiFi) |
| Siri integration | ✅ | ❌ |
| Background upload | ✅ | ❌ |
| Better recorder | ✅ (Voice Memos) | ❌ (MediaRecorder API) |
| Easier setup | ❌ (manual) | ✅ (just visit URL) |
| Auto IP discovery | ✅ (Bonjour) | ✅ (soulfra.local) |

**Recommendation:** Use Safari browser for testing, then create shortcut for daily use.

---

## Files Created

- ✅ `IPHONE-SSL-SETUP.md` - Certificate trust setup
- ✅ `IOS-SHORTCUT-GUIDE.md` - This file
- ⏳ `soulfra-shortcut.shortcut` - One-tap install (coming soon)

---

**Last Updated:** 2026-01-03

**Questions?** Check Flask terminal for errors, or verify:
- Same WiFi network
- Certificate installed
- Flask running with HTTPS
- URL matches: `https://soulfra.local:5001` or `https://192.168.1.87:5001`

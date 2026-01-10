# ✅ CringeProof Testing Checklist

## Pre-Test Setup

- [ ] Mac on WiFi
- [ ] iPhone on same WiFi network
- [ ] PM2 services running (`pm2 status`)
- [ ] Check server IP: `ifconfig en0 | grep "inet "`

## Test 1: API Health Check

**From Mac browser:**
```
https://192.168.1.87:5002/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "cringeproof-api",
  "whisper": true,
  "ollama": true,
  "timestamp": "..."
}
```

- [ ] All services show `true`
- [ ] Status is `"healthy"`

## Test 2: SSL Certificate Trust (iPhone)

**Safari on iPhone:**
```
https://192.168.1.87:5002/
```

- [ ] Certificate warning appears
- [ ] Tap "Show Details"
- [ ] Tap "visit this website"
- [ ] See green CringeProof API page
- [ ] Shows idea count and recording count

## Test 3: Web Recording (iPhone)

**Safari:**
```
https://cringeproof.com/record.html
```

- [ ] Page loads (CringeProof branding)
- [ ] Default server URL shows: `https://192.168.1.87:5002`
- [ ] Tap "Start Recording"
- [ ] Microphone permission prompt (accept)
- [ ] See "🔴 Recording..." status
- [ ] Waveform animation visible
- [ ] Speak: "This is a test recording for CringeProof"
- [ ] Tap "Stop Recording"
- [ ] Status: "⏳ Processing..."
- [ ] **SUCCESS:** "✅ Recording saved! ID: X"
- [ ] Auto-redirects to /ideas/ after 3 seconds

## Test 4: Database Verification

**On Mac:**
```bash
sqlite3 soulfra.db "SELECT id, title, score FROM voice_ideas ORDER BY id DESC LIMIT 1"
```

- [ ] New idea appears
- [ ] Title extracted from recording
- [ ] Score between 0-100

## Test 5: iOS Shortcut (Optional)

- [ ] Created shortcut following `SIRI_SHORTCUT_GUIDE.md`
- [ ] Tap shortcut manually → works
- [ ] Added to Siri with phrase
- [ ] "Hey Siri, log my idea" → works
- [ ] Check database → new entry

## Troubleshooting

### ❌ "Failed to fetch"

**Cause:** SSL cert not trusted (or expired)

**Fix:**
1. Repeat Test 2 (trust cert again)
2. Server may have restarted (new cert)

### ❌ "No microphone access"

**Fix:**
1. Settings → Safari → Microphone → Allow for cringeproof.com

### ❌ Recording uploads but no idea extracted

**Check Ollama:**
```bash
ollama list  # Should show models
curl http://localhost:11434/api/tags  # Should return JSON
```

**Check logs:**
```bash
pm2 logs cringeproof-api --lines 50
```

Look for: "⚠️ Ollama extraction failed"

---

## All Green? 🎉

You're ready to use CringeProof!

**Next steps:**
- [ ] Add to Home Screen (Test 2, Option 2)
- [ ] Set up daily automation
- [ ] Add API key (optional, see `API_KEY_SETUP.md`)
- [ ] Share with friends (they need cert trust too)

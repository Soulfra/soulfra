# 🎤 Voice Integrated System - Complete Guide

## What You Just Built

A **complete voice memo system** that connects:
- 🎙️ Voice-to-text transcription (Web Speech API)
- 💾 Audio recording (saves .webm files)
- 🗄️ Database storage (SQLite)
- 📤 GitHub Gist backup (optional)
- 🪙 Token tracking (game-like credits)

---

## Quick Start

### 1. Start Both Servers

```bash
# Terminal 1: HTTP server (frontend)
./start_local_server.sh

# Terminal 2: Voice API (backend)
python3 voice_backend.py
```

### 2. Open Voice Interface

**Visit:** http://localhost:8080/voice-integrated.html

---

## How It Works

### The Flow

```
1. Click "Start Recording"
   ↓
2. Speak into microphone
   ↓ (Real-time transcription appears)
3. Click "Stop Recording"
   ↓
4. Click "Save to Database"
   ↓ (Saves audio + transcript + tokens)
5. Optional: "Save to Gist"
   ↓ (Backs up to GitHub)
6. View in "My Memos" tab
```

---

## Features

### Tab 1: Record

**🎙️ Voice Recording**
- Real-time speech-to-text
- Audio file saved as .webm
- Keyboard shortcut: `Ctrl+Space`

**💾 Save to Database**
- Stores both audio and transcript
- Calculates tokens automatically
- Keyboard shortcut: `Ctrl+S`

**📤 Save to Gist**
- Backs up transcript to GitHub
- Requires personal access token
- Returns shareable URL

**🗑️ Clear**
- Reset for new recording
- Keyboard shortcut: `Ctrl+K`

### Tab 2: My Memos

**📝 View All Memos**
- Shows all saved voice memos
- Displays transcription
- Links to GitHub Gist (if saved)
- Play audio button

**Features:**
- Sorted by date (newest first)
- Shows token count per memo
- Click to play audio
- Direct link to Gist

### Tab 3: Tokens

**🪙 Token Tracking**
- Total tokens used across all memos
- Like game credits
- Future: marketplace, rewards, star economy

**Token Calculation:**
- 0-30 seconds: 1 token
- 30-60 seconds: 2 tokens
- 60+ seconds: 3 tokens

---

## Database Schema

### voice_memos Table

```sql
CREATE TABLE voice_memos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_filename TEXT,           -- e.g., "voice_memo_20260111_103000.webm"
    audio_blob BLOB,               -- Binary audio data (backup)
    transcription TEXT,            -- Speech-to-text result
    github_gist_id TEXT,           -- Gist ID (e.g., "abc123")
    github_gist_url TEXT,          -- Full URL to gist
    tokens_used INTEGER DEFAULT 0, -- Credits spent
    created_at TIMESTAMP           -- Auto-generated
);
```

### Storage

**Audio files:** `voice_audio/voice_memo_YYYYMMDD_HHMMSS.webm`

**Database:** `soulfra.db`

---

## API Endpoints

### Backend API (port 5002)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/voice/save` | POST | Save voice memo |
| `/api/voice/memos` | GET | List all memos |
| `/api/voice/tokens` | GET | Get token count |
| `/api/voice/audio/<id>` | GET | Get audio file |
| `/api/voice/gist` | POST | Update gist URL |
| `/health` | GET | Health check |

### Example: Save Voice Memo

```javascript
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.webm');
formData.append('transcription', 'Hello world');
formData.append('tokens', 1);

fetch('http://localhost:5002/api/voice/save', {
    method: 'POST',
    body: formData
});
```

**Response:**
```json
{
    "success": true,
    "id": 123,
    "tokens": 1,
    "filename": "voice_memo_20260111_103000.webm"
}
```

---

## GitHub Gist Integration

### Setup

1. **Get GitHub Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scope: ✅ `gist`
   - Copy the token

2. **Save to Gist:**
   - Record and transcribe voice
   - Click "Save to Gist"
   - Paste token when prompted
   - Get shareable Gist URL

### Example Gist

```markdown
Voice memo - 1/11/2026, 10:30:00 AM

This is my voice memo transcription.
The text appears here exactly as transcribed.
```

**Public:** No (private by default)

**Shareable:** Yes (via URL)

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Space` | Start/Stop recording |
| `Ctrl+S` | Save to database |
| `Ctrl+K` | Clear text |
| `Ctrl+/` | Show all shortcuts |

---

## Use Cases

### 1. Voice Notes (Basic)

```
Record → Save to DB → Done
```

**Result:** Searchable voice notes with transcription

### 2. Voice Journal (with Backup)

```
Record → Save to DB → Save to Gist
```

**Result:** Local storage + cloud backup

### 3. Voice Tokens (Game Economy)

```
Record many memos → Accumulate tokens → Use in marketplace
```

**Result:** Track usage, unlock features (future)

### 4. Integration with Ollama Email

```
Record → Save → Email transcript to ollama@domain.com
```

**Result:** Voice → AI response

---

## Connection to Other Systems

### Ollama Email Inbox

**Currently:** Two separate systems
- `voice-integrated.html` → Records + saves voice
- `email-ollama-chat.html` → Sends questions via email

**Integration Path:**
1. Record voice memo
2. Save transcription
3. Auto-send to `ollama@yourdomain.com`
4. Get AI response via email
5. Save response as new memo

**To Connect:**
```javascript
// In voice-integrated.html, after saving:
const emailBody = transcription;
const mailtoLink = `mailto:ollama@yourdomain.com?subject=[OLLAMA_REQUEST] your_api_key&body=${emailBody}`;
window.location.href = mailtoLink;
```

### Voice → Database → Tables

**Database Structure:**
```
soulfra.db
├── brands (6 domains)
├── subscribers (emails)
├── feedback (messages)
└── voice_memos (recordings)  ← NEW!
```

**All tables connected:**
- Voice memos can reference brands
- Voice can trigger email subscriptions
- Transcriptions saved for search

### GitHub Gist → Notes

**Workflow:**
```
Voice → Transcribe → Gist → Share Link
```

**Use for:**
- Meeting notes
- Ideas
- Quick thoughts
- Shareable snippets

---

## Troubleshooting

### "Microphone access denied"

**Fix:** Use Chrome or Edge (Safari doesn't support Web Speech API)

**Allow permissions:**
1. Click lock icon in address bar
2. Camera/Microphone → Allow
3. Refresh page

---

### "Failed to save: Connection refused"

**Check backend is running:**
```bash
curl http://localhost:5002/health
```

**Expected:**
```json
{
    "status": "ok",
    "database": "soulfra.db",
    "audio_dir": "voice_audio"
}
```

**If not running:**
```bash
python3 voice_backend.py
```

---

### "No memos showing up"

**Check database:**
```bash
sqlite3 soulfra.db "SELECT COUNT(*) FROM voice_memos"
```

**If 0:** Record a memo and save it first

**If > 0:** Check browser console for errors

---

### "Gist creation failed"

**Common issues:**
1. Invalid GitHub token
2. Token doesn't have `gist` scope
3. Network error

**Test token:**
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/gists
```

---

## Next Steps

### Integration Ideas

1. **Voice → Ollama:**
   - Auto-send transcription to email network
   - Get AI response
   - Save as new memo

2. **Voice → Star Economy:**
   - Earn stars for recording memos
   - Spend tokens to unlock features
   - Marketplace integration

3. **Voice → QR Codes:**
   - Generate QR from memo
   - Scan to play audio
   - CringeProof verification

4. **Voice → Domains:**
   - Brand-specific voice memos
   - CalRiven: code explanations
   - HowToCookAtHome: recipe narration
   - StPetePros: business reviews

---

## File Structure

```
soulfra-simple/
├── voice-integrated.html     ← Frontend interface
├── voice_backend.py          ← Flask API (port 5002)
├── keyboard-shortcuts.js     ← Global shortcuts
├── soulfra.db                ← SQLite database
├── voice_audio/              ← Audio files directory
│   └── voice_memo_*.webm
└── VOICE_INTEGRATED_GUIDE.md ← This file
```

---

## Summary

**What you have:**
- ✅ Voice recording (audio + transcript)
- ✅ Database storage (SQLite)
- ✅ GitHub Gist backup (optional)
- ✅ Token tracking (game credits)
- ✅ Local playback
- ✅ Keyboard shortcuts

**What's different from before:**
- ❌ Old: Voice input → nothing saved
- ✅ New: Voice input → database → gist → tokens

**What this connects to:**
- Email inbox (ollama_email_node.py)
- Database tables (brands, subscribers, feedback)
- GitHub (gist backup)
- Star economy (tokens = credits)

---

**Status:** ✅ Fully functional

**Test it:** http://localhost:8080/voice-integrated.html

**Like:** Voice memos meets SQLite meets GitHub meets game tokens

# 🎤 Voice Memo Workflow - Complete Guide

## What Is This?

A complete **accessibility-first** voice memo system that lets you:
- **Talk instead of type** (perfect for carpal tunnel/wrist issues)
- Record on iPhone → auto-transcribe → instant @routes
- Access from phone or laptop
- Local AI transcription (privacy-focused, no cloud)
- Integrates with QR codes, file imports, and content pipeline

---

## Why Voice Memos?

**Accessibility**: Voice input reduces strain on wrists and hands
**Speed**: Speak 3x faster than typing
**Convenience**: Record anywhere, transcribe automatically
**Privacy**: All processing happens locally (Whisper.cpp)

---

## The Complete Flow

```
iPhone Voice Memo
       ↓
[AirDrop / Bluetooth / Web Upload / Watched Folder]
       ↓
voice_input.py → Store audio + metadata
       ↓
whisper_transcriber.py → Local AI transcription (Whisper)
       ↓
voice_pipeline.py → Process transcript
       ↓
file_importer.py → Convert to markdown
       ↓
folder_router.py → Route as @me/voice/title
       ↓
content_pipeline.py → Generate QR codes, pSEO pages
       ↓
Access: http://localhost:5001/@me/voice/title
```

---

## Quick Start - 3 Methods

### Method 1: Web Recording (Easiest)

Perfect for: Recording directly from phone browser

```bash
# 1. Start server on MacBook
python3 app.py

# 2. On iPhone, open browser:
http://192.168.1.74:5001/voice/record

# 3. Click microphone, speak, click stop
# Auto-transcribes and creates @route
```

**Access your memo**:
- http://localhost:5001/@me/voice/your-memo
- http://192.168.1.74:5001/@me/voice/your-memo (from phone)

---

### Method 2: AirDrop + Auto-Process

Perfect for: Using iPhone Voice Memos app

```bash
# 1. On MacBook: Watch Downloads folder
python3 voice_pipeline.py --watch ~/Downloads/ --brand me --category voice

# 2. On iPhone:
# - Record voice memo in Voice Memos app
# - AirDrop to MacBook
# - File lands in ~/Downloads/
# - Auto-processes immediately

# Access at: http://localhost:5001/@me/voice/memo-title
```

---

### Method 3: Upload via Web

Perfect for: Uploading pre-recorded audio

```bash
# 1. Start server
python3 app.py

# 2. Open browser
http://localhost:5001/voice/upload

# 3. Drag and drop audio file
# Supports: WAV, MP3, M4A, OGG, FLAC
```

---

## Installation & Setup

### 1. Install Dependencies

```bash
# Core packages (required)
pip install flask requests pyyaml python-docx beautifulsoup4 markdown2 qrcode pillow watchdog

# Whisper for transcription (choose one):

# Option A: Python Whisper (easiest)
pip install openai-whisper

# Option B: whisper.cpp (faster, lower memory)
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
./models/download-ggml-model.sh base.en
```

### 2. Initialize Database

```bash
python3 migrate_onboarding_system.py
```

This creates:
- `voice_inputs` table (audio storage)
- `voice_qr_attachments` table (QR + voice)
- Indexes for performance

### 3. Test Voice Recording

```bash
# Record a test memo
echo "Testing voice memo system" | say -o test.wav

# Process it
python3 voice_pipeline.py test.wav --brand me --category test

# You should see:
# ✅ Voice memo processed!
#    Route: @me/test/testing-voice-memo-system
#    URL: http://localhost:5001/@me/test/testing-voice-memo-system
```

---

## iPhone + MacBook Setup

### Find Your MacBook's IP Address

```bash
# On MacBook
ifconfig | grep "inet " | grep -v 127.0.0.1

# Example output:
# inet 192.168.1.74
```

### Connect iPhone to MacBook (Same WiFi)

1. **MacBook**: Start server
   ```bash
   python3 app.py
   ```

2. **iPhone**: Open Safari
   ```
   http://192.168.1.74:5001/voice
   ```

3. **Record**: Tap microphone, speak, tap stop

4. **Access**: Memo appears at http://192.168.1.74:5001/@me/voice/...

---

## Advanced Workflows

### Workflow 1: QR Code + Voice Memo

Record a voice memo and attach it to a QR scan:

```bash
# 1. Record voice memo
python3 voice_pipeline.py memo.wav --attach-to-scan 123

# Now QR scan #123 has voice memo attached
```

**Use case**: Scan product QR → record voice feedback → attached to scan

---

### Workflow 2: Batch Process Queue

Process all pending transcriptions:

```bash
# Process up to 10 pending memos
python3 whisper_transcriber.py --process-queue --limit 10

# Or process entire queue
python3 voice_pipeline.py --process-queue
```

---

### Workflow 3: Custom Brand/Category

Organize voice memos by topic:

```bash
# Work notes
python3 voice_pipeline.py meeting.wav --brand work --category meetings

# Personal journal
python3 voice_pipeline.py journal.wav --brand me --category journal

# Project ideas
python3 voice_pipeline.py idea.wav --brand projects --category ideas
```

Access:
- `@work/meetings/meeting-title`
- `@me/journal/journal-entry`
- `@projects/ideas/idea-name`

---

## File System Organization

After processing, files are organized like:

```
brands/
  @me/
    voice/
      first-voice-memo.md
      second-voice-memo.md
    journal/
      2025-12-28-entry.md
  @work/
    meetings/
      team-standup.md
      client-call.md

uploads/
  voice/
    recording-12345.webm
    memo-67890.wav

temp_voice/
  (temporary markdown files)
```

---

## Database Schema

### voice_inputs Table

```sql
CREATE TABLE voice_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT,
    file_size INTEGER,
    duration_seconds REAL,
    source TEXT DEFAULT 'manual',          -- manual, web_recording, upload
    status TEXT DEFAULT 'pending',         -- pending, transcribed
    transcription TEXT,
    transcribed_at TIMESTAMP,
    transcription_method TEXT,             -- whisper, manual
    metadata TEXT,                         -- JSON: {brand, category, user_id}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### voice_qr_attachments Table

```sql
CREATE TABLE voice_qr_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    voice_input_id INTEGER,
    audio_file_path TEXT,
    duration_seconds REAL,
    transcription TEXT,
    transcription_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transcribed_at TIMESTAMP,
    FOREIGN KEY (voice_input_id) REFERENCES voice_inputs(id)
);
```

---

## API Routes

### Web Interface

- **GET** `/voice` - Dashboard (stats, recent memos)
- **GET** `/voice/record` - Browser-based recording interface
- **GET** `/voice/upload` - Upload pre-recorded audio
- **GET** `/voice/list` - List all voice memos

### Processing

- **POST** `/voice/record/save` - Save browser recording
- **POST** `/voice/upload` - Upload audio file
- **POST** `/voice/transcribe/<id>` - Transcribe specific memo
- **POST** `/voice/transcribe/queue` - Process transcription queue
- **POST** `/voice/import/<id>` - Import to @routes

### Integration

- **POST** `/voice/attach-to-scan` - Attach voice to QR scan
- **GET** `/voice/<id>` - Get voice memo details

---

## CLI Commands

### Basic Usage

```bash
# Process single voice memo
python3 voice_pipeline.py audio.wav

# With custom routing
python3 voice_pipeline.py audio.wav --brand me --category notes

# With custom title
python3 voice_pipeline.py audio.wav --title "My Important Note"
```

### Transcription Only

```bash
# Transcribe without importing
python3 whisper_transcriber.py audio.wav

# Transcribe with timestamps
python3 whisper_transcriber.py audio.wav --timestamps

# Save transcription to file
python3 whisper_transcriber.py audio.wav --output transcript.txt
```

### Batch Processing

```bash
# Process queue
python3 whisper_transcriber.py --process-queue

# Process specific audio_id from database
python3 whisper_transcriber.py --audio-id 123
```

### Folder Watching

```bash
# Watch folder for new audio files
python3 voice_pipeline.py --watch ~/Desktop/voice-memos/

# Watch with custom brand/category
python3 voice_pipeline.py --watch ~/Downloads/ --brand me --category voice
```

---

## Environment Variables

Configure voice system with environment variables:

```bash
# Whisper config
export WHISPER_MODEL=base              # tiny, base, small, medium, large
export WHISPER_CPP_PATH=/path/to/whisper.cpp
export WHISPER_LANGUAGE=en             # en, es, fr, de, etc.

# Voice pipeline defaults
export VOICE_BRAND=me
export VOICE_CATEGORY=voice
export VOICE_USER_ID=1
export VOICE_UPLOAD_FOLDER=./uploads/voice
```

---

## Troubleshooting

### Issue: "No Whisper backend found"

**Solution**: Install Whisper

```bash
# Python Whisper (easiest)
pip install openai-whisper

# Or whisper.cpp (faster)
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
./models/download-ggml-model.sh base.en
export WHISPER_CPP_PATH=/path/to/whisper.cpp
```

### Issue: "Cannot connect from iPhone"

**Solution**: Check network and firewall

```bash
# 1. Verify same WiFi network
# 2. Find MacBook IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 3. Test connectivity from iPhone
# Open Safari: http://YOUR_IP:5001/voice

# 4. Check firewall (macOS)
# System Preferences → Security & Privacy → Firewall
# Allow: python3
```

### Issue: "Transcription too slow"

**Solution**: Use smaller Whisper model or whisper.cpp

```bash
# Smaller model (faster but less accurate)
export WHISPER_MODEL=tiny

# Or use whisper.cpp (much faster)
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
./models/download-ggml-model.sh tiny.en
export WHISPER_CPP_PATH=$(pwd)
```

### Issue: "Web recording not working"

**Solution**: Enable microphone permissions

1. **macOS**: System Preferences → Security & Privacy → Microphone → Enable for Browser
2. **iOS/Safari**: Settings → Safari → Microphone → Allow
3. **HTTPS Required**: Some browsers require HTTPS for microphone. Use localhost or LAN IP (not internet domain)

---

## Performance Tips

### Speed Up Transcription

1. **Use smaller model**:
   ```bash
   export WHISPER_MODEL=tiny  # Fastest, ~1x realtime
   # vs
   export WHISPER_MODEL=base  # Balanced, ~2x realtime
   ```

2. **Use whisper.cpp** (2-3x faster than Python):
   ```bash
   git clone https://github.com/ggerganov/whisper.cpp
   cd whisper.cpp && make
   ./models/download-ggml-model.sh base.en
   export WHISPER_CPP_PATH=$(pwd)
   ```

3. **Process queue during downtime**:
   ```bash
   # Auto-process queue every 5 minutes
   while true; do
     python3 whisper_transcriber.py --process-queue
     sleep 300
   done
   ```

### Optimize Storage

```bash
# Compress old audio files
find uploads/voice -name "*.wav" -mtime +30 -exec gzip {} \;

# Archive processed files
python3 -c "from voice_input import archive_old_files; archive_old_files(days=90)"
```

---

## File Summary

| File | Purpose | Lines |
|------|---------|-------|
| `whisper_transcriber.py` | Local AI transcription (Whisper) | ~500 |
| `voice_pipeline.py` | Voice → transcript → @route | ~450 |
| `voice_routes.py` | Flask web interface | ~400 |
| `voice_input.py` | Audio storage & metadata | ~500 |
| `qr_voice_integration.py` | QR + voice attachment | ~400 |
| `migrate_onboarding_system.py` | Database setup (includes voice tables) | ~450 |

**Total**: ~2,700 lines of voice memo infrastructure

---

## Next Steps

### For Accessibility

1. **Record a voice memo** from iPhone:
   ```bash
   # MacBook: Watch folder
   python3 voice_pipeline.py --watch ~/Downloads/

   # iPhone: Voice Memos app → AirDrop to Mac
   ```

2. **Access from phone**:
   ```
   http://YOUR_IP:5001/@me/voice/memo-title
   ```

3. **Reduce typing**: Use voice for quick notes, journal entries, ideas

### For Development

1. **Add voice to app.py**:
   ```python
   from voice_routes import create_voice_blueprint
   app.register_blueprint(create_voice_blueprint())
   ```

2. **Customize transcription**:
   - Edit `whisper_transcriber.py` to change models
   - Adjust language settings
   - Add custom post-processing

3. **Integrate with existing features**:
   - Attach voice to blog posts
   - Voice annotations on files
   - Voice-based search

---

## Summary

You now have:
- ✅ Local AI transcription (Whisper)
- ✅ iPhone → MacBook voice recording
- ✅ Web-based recording interface
- ✅ Auto-import to @routes
- ✅ QR code integration
- ✅ Privacy-focused (all local)
- ✅ Accessibility-first design

**Speak your thoughts, we'll handle the rest.**

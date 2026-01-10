# Voice → Chapter System

Complete voice memo to interactive chapter conversion system.

## What We Built

### 1. Voice to Chapter Converter (`voice_to_chapter.py`)

Converts voice memos into structured markdown chapters:

```bash
# Convert specific recording
python3 voice_to_chapter.py --recording 16

# Batch convert recent memos
python3 voice_to_chapter.py --batch 10
```

**Features:**
- Auto-detects domain from transcription keywords
- Extracts title from first sentence
- Groups sentences into paragraphs
- Detects technical terms and wraps in code blocks
- Links back to original recording
- Global chapter numbering system

**Domain Detection:**
- `cringeproof` → Keywords: cringe, anxiety, performance, voice
- `soulfra` → Keywords: soul, identity, keys, privacy, ai
- `calriven` → Keywords: calendar, schedule, planning, time
- `deathtodata` → Keywords: death, data, privacy, homebrew, lab

### 2. README ↔ Chapter Sync (`readme_chapter_sync.py`)

Bi-directional sync between GitHub READMEs and chapter snapshots:

```bash
# README → Chapter
python3 readme_chapter_sync.py --readme-to-chapter soulfra local

# Chapter → README (preview)
python3 readme_chapter_sync.py --chapter-to-readme 11 soulfra preview

# Chapter → README (write to file)
python3 readme_chapter_sync.py --chapter-to-readme 11 soulfra write

# Batch sync all local READMEs
python3 readme_chapter_sync.py --batch

# List chapters for domain
python3 readme_chapter_sync.py --list soulfra
```

**Sources:**
- `local` → Reads from `output/{domain}/README.md`
- `github` → Fetches from GitHub API

### 3. Voice → README API (`voice_readme_routes.py`)

Talk to your README via voice memos:

**Endpoints:**

#### POST `/api/voice-to-readme`
Convert voice memo to README update

```json
{
  "recording_id": 16,
  "domain": "soulfra",
  "mode": "chapter"  // or "append" or "replace"
}
```

**Modes:**
- `chapter` → Creates standalone chapter (default)
- `append` → Adds to existing README as new section
- `replace` → Replaces entire README with voice content

#### GET `/api/readme-status/{domain}`
Get current README status

Returns:
```json
{
  "success": true,
  "domain": "soulfra",
  "current_chapter_id": 11,
  "chapter_num": 11,
  "version_num": 1,
  "word_count": 54,
  "voice_contributions": 3,
  "last_updated": "2026-01-04 18:35:18"
}
```

#### GET `/api/readme-history/{domain}`
Get version history for README

### 4. Chapter QR/UPC Generator (`chapter_qr_generator.py`)

Generate scannable codes for chapters:

```bash
# Generate QR for specific chapter
python3 chapter_qr_generator.py --chapter 11 cringeproof.com

# Batch generate QR codes
python3 chapter_qr_generator.py --batch 10

# Save QR to PNG file
python3 chapter_qr_generator.py --save 11

# Verify QR signature
python3 chapter_qr_generator.py --verify 11 1767551953 FOioHp32R5uXnj2Qr7ez8P...
```

**Features:**
- QR codes with HMAC signatures (30-day expiry)
- UPC-style barcodes (12 digits: `969696000117`)
- Base64-encoded images for embedding
- Verification system for authenticity

**UPC Format:**
```
969696 00011 7
  │      │    └─ Check digit
  │      └────── Chapter number (padded to 5 digits)
  └───────────── Soulfra prefix
```

### 5. Chapter Card UI (`chapter_card.html`)

Embeddable card component for displaying chapters:

**Usage:**
```html
<!-- Embed via iframe -->
<iframe
  src="https://cringeproof.com/chapter-card.html?id=11"
  width="600"
  height="800"
></iframe>

<!-- Or link directly -->
<a href="https://cringeproof.com/chapter/11">View Chapter #11</a>
```

**Features:**
- Markdown rendering with syntax highlighting
- QR code display (scannable from screen)
- UPC barcode display
- Wordmap-based color theming
- Voice memo button (add update to chapter)
- Fork/share buttons
- Responsive design

**API Endpoints:**

#### GET `/api/chapters/{id}`
Get chapter details

#### GET `/api/chapter-qr/{id}`
Get QR code for chapter

#### GET `/api/chapters/list`
List all chapters with pagination

Query params:
- `limit` → Max chapters (default: 20)
- `offset` → Skip N chapters (default: 0)
- `domain` → Filter by domain

### 6. Chapter Routes (`chapter_routes.py`)

Flask blueprint with chapter management endpoints:

- `GET /api/chapters/{id}` → Get chapter
- `GET /api/chapter-qr/{id}` → Get QR code
- `GET /api/chapters/list` → List chapters
- `GET /chapter/{id}` → Redirect to card
- `GET /chapter-card.html` → Serve card UI

## Data Flow

### Voice Memo → Chapter

```
1. User records voice memo on phone
   └─> Uploads to /api/simple-voice/save
       └─> Whisper transcription
           └─> Stored in simple_voice_recordings table

2. Call /api/voice-to-readme or python3 voice_to_chapter.py
   └─> Detects domain from keywords
       └─> Converts to markdown
           └─> Creates chapter_snapshot
               └─> Links to original recording via commit_message

3. Chapter now accessible via:
   - /api/chapters/{id}
   - /chapter/{id}
   - /chapter-card.html?id={id}
   - QR code scan
```

### README → Chapter → QR Code

```
1. Local README file (output/soulfra/README.md)
   └─> python3 readme_chapter_sync.py --readme-to-chapter soulfra
       └─> Creates chapter_snapshot
           └─> chapter_num assigned globally

2. Generate QR code
   └─> python3 chapter_qr_generator.py --chapter 11
       └─> Returns QR image + UPC barcode
           └─> HMAC-signed URL for verification

3. Scan QR code
   └─> Opens https://cringeproof.com/chapter/11?sig=...&ts=...
       └─> Verifies signature
           └─> Displays chapter card
```

## Database Schema

### `chapter_snapshots`

```sql
CREATE TABLE chapter_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_num INTEGER NOT NULL,           -- Global chapter number
    version_num INTEGER NOT NULL DEFAULT 1, -- Version within chapter
    title TEXT NOT NULL,
    content TEXT NOT NULL,                  -- Markdown content
    commit_message TEXT,                    -- Links to source (e.g., "from recording #16")
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    is_fork BOOLEAN DEFAULT 0,
    fork_source_id INTEGER,
    UNIQUE(chapter_num, version_num)
);
```

### `simple_voice_recordings`

```sql
CREATE TABLE simple_voice_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcription TEXT,
    user_id INTEGER,
    domain TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### `domain_wordmaps`

```sql
CREATE TABLE domain_wordmaps (
    domain TEXT PRIMARY KEY,
    wordmap_json TEXT,                      -- JSON: {"word": count, ...}
    contributor_count INTEGER DEFAULT 0,
    total_recordings INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Testing Results

### ✅ Voice to Chapter Conversion
```
🔄 Converting up to 3 voice memos to chapters...
============================================================
✅ Converted 3 voice memos
❌ Failed 0
   ✅ Recording #16 → Chapter #8 (soulfra)
   ✅ Recording #15 → Chapter #9 (soulfra)
   ✅ Recording #14 → Chapter #10 (cringeproof)
```

### ✅ README to Chapter Sync
```
🔄 Converting soulfra README → Chapter (source: local)...
{
  "success": true,
  "chapter_id": 11,
  "chapter_num": 11,
  "domain": "soulfra",
  "title": "Soulfra",
  "source": "local"
}
```

### ✅ Voice to README API
```bash
curl -X POST https://192.168.1.87:5002/api/voice-to-readme \
  -d '{"recording_id": 16, "mode": "chapter"}'

# Response:
{
  "success": true,
  "chapter_id": 12,
  "chapter_num": 12,
  "domain": "soulfra",
  "mode": "chapter",
  "title": "Soulfra - Voice Chapter 12"
}
```

### ✅ QR Code Generation
```
🔄 Generating QR code for Chapter #11...
✅ QR Code Generated:
   Chapter: Soulfra
   URL: https://cringeproof.com/chapter/11?sig=FOioHp32R5uXnj2Qr7ez8P...
   UPC: 969696000117
```

### ✅ Chapter API Endpoints
```bash
# Get chapter
curl https://192.168.1.87:5002/api/chapters/11
# → Returns full chapter content

# List chapters
curl https://192.168.1.87:5002/api/chapters/list?limit=5
# → Returns 12 total chapters, showing 5

# Get QR code
curl https://192.168.1.87:5002/api/chapter-qr/11
# → Returns base64 QR image + UPC
```

## Use Cases

### 1. Talk to Your README
```
Record voice memo on phone describing new feature
   → Auto-transcribes
      → Detects it's about "soulfra" (mentions "identity", "keys")
         → Creates chapter
            → Optional: Append to README
               → Git commit + push
```

### 2. Share Chapter via QR Code
```
Generate QR code for chapter
   → Print on sticker/card
      → Someone scans it
         → Opens chapter card on their phone
            → They can fork it to their own domain
```

### 3. Voice-Driven Documentation
```
Weekly voice updates about project progress
   → Each becomes a chapter
      → Chapters auto-organize by domain
         → Export to PDF/ebook via UPC codes
```

### 4. Cross-Site Components
```
Write chapter on cringeproof.com
   → Embed card on soulfra.com via iframe
      → Users on calriven.com can fork it
         → All domains share same chapter database
```

## Next Steps

1. **GitHub Integration**
   - Webhook to sync README on git push
   - Auto-create chapters from commits
   - Push chapter content back to README

2. **Advanced Voice Features**
   - Voice commands ("append this to chapter 11")
   - Multi-language transcription
   - Speaker identification for multi-author chapters

3. **Chapter Interactions**
   - Comments on chapters
   - Ratings/reactions
   - Completion tracking
   - Learning paths

4. **QR Advanced Features**
   - Rotating QR codes (change every 24 hours)
   - NFC tags for physical chapter "cards"
   - Print-ready PDF generation with UPC barcodes

5. **Deployment**
   - Deploy chapter-card.html to GitHub Pages
   - Point domains to production backend
   - CDN for QR code images
   - Webhook for auto-sync

## Files Created

```
voice_to_chapter.py          → Voice memo → Chapter converter
readme_chapter_sync.py       → README ↔ Chapter bi-directional sync
voice_readme_routes.py       → API for voice → README updates
chapter_qr_generator.py      → QR/UPC code generator
chapter_card.html            → Embeddable chapter UI component
chapter_routes.py            → Chapter API endpoints
VOICE_CHAPTER_SYSTEM.md      → This documentation
```

## Integration with Existing Systems

### Slug System (`slug_routes.py`)
- Users claim slugs like `alice.cringeproof.com`
- Each user can create chapters
- Chapters inherit user's wordmap colors

### Wordmap CSS Generator (`wordmap_css_generator.py`)
- Chapter cards auto-themed from content
- Top 5 words → Color palette
- Consistent styling across all sites

### Domain Sync (`sync_local_domains.py`)
- Local domain repos in `output/`
- Each domain has README
- README becomes chapter on sync

### Auth System (`auth_routes.py`)
- Login required to create chapters
- 5-tier user system
- Phone verification for domain ownership

### Wall/Feed (`simple_voice_routes.py`)
- Voice memos appear on wall
- Can convert wall posts to chapters
- Chapters appear in feed

## Example Workflow

**Your Daily Flow:**

1. **Morning** → Record voice memo on phone while making coffee
   - "Idea for Soulfra: Add QR code login instead of passwords"

2. **Auto-processing** → Voice uploads to API
   - Whisper transcribes
   - Detects domain: "soulfra" (keywords: "qr", "login", "password")
   - Creates Chapter #13

3. **Lunch** → Check chapter on laptop
   - Visit https://cringeproof.com/chapter/13
   - Card shows transcription as markdown
   - QR code displayed (UPC: 969696000130)

4. **Afternoon** → Generate QR sticker
   - `python3 chapter_qr_generator.py --save 13`
   - Print QR code on label maker
   - Stick on notebook

5. **Evening** → Friend scans QR code
   - Opens chapter card on their phone
   - Reads your idea
   - Forks chapter to their domain
   - Adds voice comment

6. **Later** → Your README auto-updates
   - Chapter syncs back to `output/soulfra/README.md`
   - Git commit: "Added QR login chapter from voice memo #23"
   - GitHub Pages rebuilds
   - Soulfra.com shows new content

**Like magic, but with SQLite and QR codes.**

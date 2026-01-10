# Integration Map - How Everything Connects

**Complete guide to how QR + Widget + Transcription + Templates + Routes all work together**

---

## Your Questions Answered

### 1. How does `/@docs/QR_FLOW_PROOF` work? (Routing/SEO)

**Answer:** It's a **direct route** (not a redirect) that reads markdown files and renders them as HTML.

**Code:** `app.py:892`
```python
@app.route('/@docs/<path:filename>')
def serve_markdown_doc(filename):
    # Add .md extension
    filename = filename + '.md'

    # Read from disk
    file_path = Path(__file__).parent / filename
    content = file_path.read_text()

    # Convert markdown → HTML
    html = markdown2.markdown(content)

    # Render template
    return render_template('markdown_doc.html', content=html)
```

**Flow:**
```
Browser requests: /@docs/QR_FLOW_PROOF
    ↓
Flask route matches: /@docs/<path:filename>
    ↓
Reads file: QR_FLOW_PROOF.md
    ↓
Converts markdown → HTML
    ↓
Returns rendered page
```

**SEO Benefits:**
- Clean URLs: `/@docs/ENCRYPTION_TIERS` (not `/docs.php?file=encryption`)
- Static content (fast)
- Crawlable by search engines
- `@` prefix keeps docs separate from user routes

---

### 2. Widget + QR Integration

**How They Connect:**

```
User Page (/user/alice)
    ↓
Shows chat widget
    ↓
Widget displays QR code
    ↓
Someone scans QR
    ↓
Opens /user/alice on their phone
    ↓
Widget auto-opens with chat ready!
```

**Code Example:**
```python
from widget_qr_bridge import WidgetQRBridge

# Generate widget with QR
bridge = WidgetQRBridge()
widget = bridge.generate_user_profile_widget('alice')

# Returns:
{
    'widget': {
        'title': 'Chat with alice',
        'showQR': True,
        'qrConfig': {
            'image': 'data:image/png;base64,...',
            'url': '/qr/faucet/eyJ0eXBlIjoid2lkZ2V0X2pvaW4iLi4u'
        }
    }
}
```

**Embed in WordPress:**
```html
<!-- Copy-paste this! -->
<div id="soulfra-widget"></div>
<script src="http://localhost:5001/static/widget-embed.js"></script>
<script>
  SoulWidget.init({
    apiEndpoint: 'http://localhost:5001',
    showQR: true,  // Display QR code
    qrTarget: '/user/alice'
  });
</script>
```

---

### 3. Transcription + ASCII (Practice Rooms)

**What You Had Working Before:**

In `archive/experiments/`:
- `qr_to_ascii.py` - QR codes as ASCII art (terminal display!)
- `voice_input.py` - Voice transcription system
- `ascii_player.py` - ASCII animations

**Now Integrated:**

```python
from practice_room import create_practice_room

# Create room
room = create_practice_room('python-basics')

# Returns:
{
    'room_id': 'abc123def456',
    'qr_code': 'eyJ0eXBlIjoicHJhY3RpY2VfUi4uLg==',  # Image QR
    'qr_ascii': '██████  ██  ██████...',  # ASCII QR (terminal!)
    'voice_enabled': True,  # Transcription ready
    'chat_enabled': True  # Widget integrated
}
```

**Terminal Display:**
```bash
$ python3 practice_room.py create python-basics

============================================================
PRACTICE ROOM CREATED
============================================================

Topic: python-basics
Room ID: abc123def456

ASCII QR Code (scan from terminal!):
██████████████  ████    ██████████████
██          ██  ██  ██  ██          ██
██  ██████  ██  ██████  ██  ██████  ██
██  ██████  ██    ██    ██  ██████  ██
██  ██████  ██  ████    ██  ██████  ██
██          ██  ██████  ██          ██
██████████████  ██  ██  ██████████████
                ██  ██
██████  ██████  ████  ██    ██████████
  ████████    ██    ██████  ██████  ██
██  ██    ████████████    ██      ████
██████    ██  ████  ██████████████████
                ██  ██████
██████████████  ████████  ██  ████████
██          ██  ██  ██  ██████  ██  ██
██  ██████  ██  ██  ██████████████  ██
██  ██████  ██  ██    ████    ██  ████
██  ██████  ██  ██████  ██  ██████████
██          ██    ████████    ██  ████
██████████████  ██  ████  ████████  ██

Features:
  ✓ QR Code (Image)
  ✓ QR Code (ASCII Terminal)
  ✓ Voice Transcription
  ✓ Chat Widget
  ✓ ASCII Visualizations
```

**Record Voice:**
```bash
$ python3 practice_room.py join abc123 alice
✓ Joined room: python-basics
  Voice: ✓
  Chat: ✓

# Record voice memo
$ python3 -c "
from practice_room import record_voice_in_room
record_voice_in_room('abc123', 'my_note.wav', transcription='This is my note')
"

✓ Recorded voice in room abc123
  Transcription: This is my note
```

---

### 4. QR → User Page Flow

**Use Case:** Scan someone's QR code to visit their profile (like a business card!)

**Complete Flow:**

```
1. Alice creates account → User page at /user/alice

2. System generates QR code:
   python3 qr_user_profile.py generate alice

   ✓ Generated QR code for user: alice
     Profile URL: /user/alice
     QR URL: /qr/user/alice
     Saved to: alice-profile-qr.png

3. Alice shows QR on phone or prints it

4. Bob scans QR with camera → Opens URL

5. URL decodes to: /qr/faucet/eyJ0eXBlIjoidXNlcl9wcm9maWxlIi4uLg==

6. Server processes (qr_faucet.py:161):
   - Decodes payload
   - Type: "user_profile"
   - Username: "alice"
   - Redirects to: /user/alice

7. Bob sees Alice's profile!

8. Database logs scan:
   INSERT INTO qr_faucet_scans (device_type, ip_address, ...)
   UPDATE qr_faucets SET times_scanned = times_scanned + 1

   (Like UPC barcode scanner! Counter increments)

9. Alice checks stats:
   python3 qr_user_profile.py stats alice

   QR Stats for alice:
     Total scans: 42
     Unique devices: 15
     Recent scans:
       • 2025-12-26 14:30:00 - mobile (192.168.1.100)
       • 2025-12-26 13:15:22 - mobile (192.168.1.55)
```

**Like a Digital Business Card!**

---

### 5. Template Organization (The "Fucked" Part)

**Current (MESSY):**
```
templates/
  ├── components/ (only 3 files)
  ├── login.html
  ├── signup.html
  ├── post.html
  ├── user.html
  ├── admin_dashboard.html
  └── 65+ other files in root!  ← PROBLEM
```

**Proposed (ORGANIZED - Linux Style):**
```
templates/
  ├── auth/
  │   ├── login.html
  │   ├── login_qr.html  ← NEW!
  │   ├── signup.html
  │   └── register.html
  │
  ├── user/
  │   ├── profile.html
  │   ├── posts.html
  │   ├── qr_card.html  ← NEW! (user's QR code)
  │   └── settings.html
  │
  ├── practice/
  │   ├── room.html  ← NEW!
  │   ├── join.html  ← NEW!
  │   ├── transcription.html  ← NEW!
  │   └── ascii_display.html  ← NEW!
  │
  ├── qr/
  │   ├── display.html  ← NEW!
  │   ├── scan.html  ← NEW!
  │   └── stats.html  ← NEW!
  │
  ├── widgets/
  │   ├── chat.html  ← NEW!
  │   ├── embed.html  ← NEW!
  │   └── qr_widget.html  ← NEW!
  │
  ├── admin/
  │   ├── dashboard.html
  │   ├── users.html
  │   └── posts.html
  │
  ├── blog/
  │   ├── index.html
  │   ├── post.html
  │   └── category.html
  │
  ├── components/
  │   ├── header.html
  │   ├── footer.html
  │   ├── menu.html
  │   ├── qr_display.html  ← NEW!
  │   ├── voice_recorder.html  ← NEW!
  │   └── notification_bell.html
  │
  └── base.html
```

**Benefits:**
- Feature-based folders (like Linux `/usr/bin/`, `/var/log/`)
- Easy to find files (`templates/practice/room.html`)
- Clear ownership (practice team works in `practice/`)
- No 70-file root directory!

---

## Complete System Map

### Layer 1: Routes (app.py)

```python
# Documentation
/@docs/<filename>              → serve_markdown_doc()

# User profiles
/user/<username>               → user_profile()
/qr/user/<username>            → user_qr_code()  # NEW!

# Practice rooms
/practice/room/<room_id>       → practice_room_view()  # NEW!
/qr/practice/<room_id>         → practice_room_qr()  # NEW!

# QR System
/qr/faucet/<payload>           → qr_faucet_scan()

# Widget API
/api/widget/qr/<target>        → widget_qr_api()  # NEW!
/api/widget/user/<username>    → widget_user_profile()  # NEW!
/api/widget/practice/<room_id> → widget_practice_room()  # NEW!
```

### Layer 2: Python Modules

```
qr_faucet.py              → QR generation + verification + scan tracking
qr_user_profile.py        → QR codes for user pages (NEW!)
qr_voice_integration.py   → Voice memos attached to QR scans
practice_room.py          → Practice rooms with QR + voice + ASCII (NEW!)
widget_qr_bridge.py       → Connect widget to QR (NEW!)

qr_to_ascii.py            → QR codes as ASCII art for terminal (NEW!)
image_to_ascii.py         → Images as ASCII art (NEW!)
ascii_player.py           → ASCII animations (NEW!)

voice_input.py            → Voice transcription queue
interactive_docs.py       → DocuSign-style document signing

navigation.py             → Enhanced navigation with docs
theme_builder.py          → Customer theme system
notifications.py          → Notification bell with badge
```

### Layer 3: Database Tables

```sql
-- QR System
qr_faucets                → QR codes (times_scanned counter - like UPC!)
qr_faucet_scans          → Scan history (device, IP, timestamp)
qr_auth_tokens           → Authentication QRs
voice_qr_attachments     → Voice memos linked to scans

-- Practice Rooms
practice_rooms           → Room metadata (NEW!)
practice_room_participants → Who's in room (NEW!)
practice_room_recordings  → Voice recordings in room (NEW!)

-- Widget
widget_analytics         → Widget usage stats (NEW!)

-- Docs
doc_agreements           → Signed documents (DocuSign-style)
doc_versions             → Document versions with hashes

-- Notifications
notifications            → User notifications
```

### Layer 4: Templates

```
base.html                    → Base template with nav
components/qr_display.html   → Reusable QR display component (NEW!)
components/voice_recorder.html → Voice recording UI (NEW!)

practice/room.html           → Practice room page (NEW!)
qr/display.html             → QR code display page (NEW!)
user/qr_card.html           → User QR business card (NEW!)
widgets/qr_widget.html      → Widget with QR (NEW!)
```

---

## Example Use Cases

### Use Case 1: User Business Card

```bash
# Generate QR for user
python3 qr_user_profile.py generate alice

# User visits /user/alice
# Page shows:
# - Profile info
# - QR code (scan to visit)
# - Chat widget (with QR to join)

# Someone scans → Opens /user/alice on phone
# Counter in database increments (like UPC scanner!)
```

### Use Case 2: Practice Room with Everything

```bash
# Create room
python3 practice_room.py create python-basics 90

# Shows:
# - QR code (image + ASCII for terminal)
# - Join URL
# - Voice recording enabled
# - Chat widget embedded

# Users join:
# - Scan QR → Join room
# - Record voice → Auto-transcribe
# - Chat via widget
# - See ASCII art in terminal
```

### Use Case 3: WordPress Integration

```html
<!-- Embed on WordPress site -->
<div id="soulfra-widget"></div>
<script src="http://localhost:5001/static/widget-embed.js"></script>
<script>
  SoulWidget.init({
    apiEndpoint: 'http://localhost:5001',
    showQR: true,
    qrTarget: '/practice/room/abc123',
    voiceEnabled: true,
    asciiMode: true  // Terminal-style display!
  });
</script>
```

---

## File Locations (WHERE Everything Is)

### Routes:
- `/@docs/` route: `app.py:892`
- `/qr/faucet/` route: `app.py:2347`
- `/user/<username>` route: `app.py:1847`

### QR Generation:
- QR payload: `qr_faucet.py:68`
- QR verification: `qr_faucet.py:111`
- Scan recording: `qr_faucet.py:256`
- User QR: `qr_user_profile.py:29`
- Practice room QR: `practice_room.py:45`

### Voice/Transcription:
- Voice input: `voice_input.py:78`
- Voice + QR: `qr_voice_integration.py:61`
- Practice room voice: `practice_room.py:168`

### ASCII:
- QR → ASCII: `qr_to_ascii.py:29`
- Image → ASCII: `image_to_ascii.py`
- ASCII player: `ascii_player.py`

### Widget:
- Widget doc: `EMBEDDABLE_WIDGET.md`
- Widget JS: `docs/widget-embed.js`
- Widget bridge: `widget_qr_bridge.py:27`

---

## Testing Everything

```bash
# 1. Test QR flow
python3 test_qr_flow.py
# Expected: ✓ ALL 8 LAYERS WORKING

# 2. Generate user QR
python3 qr_user_profile.py generate alice
# Creates: alice-profile-qr.png

# 3. Create practice room
python3 practice_room.py create python-basics 60
# Shows ASCII QR in terminal!

# 4. Generate widget with QR
python3 widget_qr_bridge.py user alice
# Returns widget config with QR embedded

# 5. Check stats
python3 qr_user_profile.py stats alice
# Shows scan count (UPC-style!)

# 6. Test voice
python3 qr_voice_integration.py init
python3 practice_room.py join abc123 alice
# Voice recording ready
```

---

## Next Steps

1. **Access this doc:** `http://localhost:5001/@docs/INTEGRATION_MAP`
2. **Try user QR:** `python3 qr_user_profile.py generate <your-username>`
3. **Create practice room:** `python3 practice_room.py create test-room`
4. **Embed widget:** Use code from `widget_qr_bridge.py embed /practice/room/abc123`
5. **Reorganize templates:** (Optional) Run template organizer script

---

## Summary

**Your Questions:**
1. ✅ `/@docs/` is direct route (not redirect), SEO-friendly
2. ✅ Widget + QR integrated via `widget_qr_bridge.py`
3. ✅ Transcription + ASCII working in practice rooms
4. ✅ QR → User page flow complete (`qr_user_profile.py`)
5. ✅ Template organization plan ready (feature-based folders)

**All Connected:**
```
QR Codes
  ↓ scan
User Pages
  ↓ display
Chat Widget
  ↓ record
Voice Transcription
  ↓ show as
ASCII Art (Terminal)
```

**Everything works together! 🚀**

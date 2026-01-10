# Template Organization - Feature-Based Structure

**Created:** 2025-12-27
**Status:** ✅ New templates added for QR, Practice Rooms, and Widgets

---

## New Organization

Templates are now organized by feature instead of all in root directory.

### Directory Structure

```
templates/
├── base.html                    # Base template (stays in root)
│
├── components/                  # Reusable UI components
│   ├── header.html
│   ├── footer.html
│   ├── menu.html
│   ├── qr_display.html          # NEW! Reusable QR code display
│   ├── voice_recorder.html      # NEW! Reusable voice recorder
│   └── notification_bell.html
│
├── practice/                    # NEW! Practice room features
│   └── room.html               # Practice room page (QR + voice + chat)
│
├── qr/                          # NEW! QR code features
│   └── display.html            # QR code display with stats
│
├── user/                        # NEW! User profile features
│   └── qr_card.html            # Digital business card with QR
│
├── widgets/                     # NEW! Embeddable widget features
│   └── embed_preview.html      # Widget embedding preview
│
├── admin/                       # Admin features (existing files)
│   ├── admin_dashboard.html
│   ├── admin_master_portal.html
│   ├── admin_studio.html
│   └── ... (other admin files)
│
├── games/                       # Game features
│   └── ... (existing game files)
│
└── ... (other existing directories)
```

---

## New Templates Created

### 1. Practice Room Templates

**templates/practice/room.html**
- Complete practice room interface
- Features:
  - Room header with topic and status
  - QR code display for joining
  - Voice recorder integration
  - Chat widget
  - Recordings list
  - Participants list
- Uses components: `qr_display.html`, `voice_recorder.html`
- Route: `/practice/room/<room_id>`

### 2. QR Code Templates

**templates/qr/display.html**
- Standalone QR code display page
- Features:
  - QR code image or ASCII display
  - Scan statistics (total scans, unique devices)
  - Recent scans list
  - Share options (copy link, print, download)
  - Device type icons (mobile/desktop)
- Uses component: `qr_display.html`
- Route: `/qr/display/<qr_id>`

### 3. User Profile Templates

**templates/user/qr_card.html**
- Digital business card with QR code
- Features:
  - User profile card design
  - QR code for profile sharing
  - Profile view stats
  - Save to contacts (vCard)
  - Share options
  - Print-friendly layout
- Uses component: `qr_display.html`
- Route: `/user/<username>/qr-card`

### 4. Widget Templates

**templates/widgets/embed_preview.html**
- Widget embedding configuration and preview
- Features:
  - Live widget preview
  - Copy-paste embed code
  - Configuration form
  - Integration guides (WordPress, Shopify, Custom)
- Route: `/widgets/embed/preview`

### 5. Reusable Components

**templates/components/qr_display.html**
- Reusable QR code display component
- Supports:
  - Base64 image QR codes
  - ASCII QR codes (terminal display)
  - URL-based QR generation (client-side)
  - Download functionality
  - Responsive design
- Usage: `{% include 'components/qr_display.html' %}`

**templates/components/voice_recorder.html**
- Reusable voice recording interface
- Features:
  - Record/stop controls
  - Real-time recording timer
  - Audio playback
  - Save/discard options
  - Transcription display
  - Error handling
  - Browser compatibility check
- Usage: `{% include 'components/voice_recorder.html' %}`

---

## Integration with Existing Code

### Python Modules Integration

**practice_room.py** → **templates/practice/room.html**
```python
from flask import render_template

@app.route('/practice/room/<room_id>')
def practice_room_view(room_id):
    room = get_practice_room(room_id)
    participants = get_room_participants(room_id)
    recordings = get_room_recordings(room_id)

    return render_template('practice/room.html',
                         room=room,
                         participants=participants,
                         recordings=recordings,
                         qr_image=room['qr_image'],
                         qr_url=room['qr_url'],
                         qr_ascii=room['qr_ascii'])
```

**qr_user_profile.py** → **templates/user/qr_card.html**
```python
@app.route('/user/<username>/qr-card')
def user_qr_card(username):
    user = get_user(username)
    qr_data = generate_user_qr(username)
    qr_stats = get_user_qr_stats(username)

    return render_template('user/qr_card.html',
                         username=username,
                         user_bio=user.get('bio'),
                         qr_image=qr_data['qr_image'],
                         qr_url=qr_data['qr_url'],
                         qr_stats=qr_stats)
```

**widget_qr_bridge.py** → **templates/widgets/embed_preview.html**
```python
@app.route('/widgets/embed/preview')
def widget_embed_preview():
    target_url = request.args.get('target', '/user/demo')
    bridge = WidgetQRBridge()
    config = bridge.generate_widget_with_qr(target_url)
    embed = bridge.embed_code(config)

    return render_template('widgets/embed_preview.html',
                         embed_code=embed,
                         target_url=target_url,
                         widget_config=config)
```

### Component Usage Examples

**Using QR Display Component:**
```html
{% set qr_image = "data:image/png;base64,..." %}
{% set qr_url = "/qr/faucet/abc123" %}
{% include 'components/qr_display.html' %}
```

**Using Voice Recorder Component:**
```html
{% set room_id = "practice_room_123" %}
{% include 'components/voice_recorder.html' %}
```

---

## Benefits of New Structure

### 1. Feature-Based Organization
- Related templates grouped together
- Easy to find templates by feature
- Clear ownership (practice team → `practice/`, QR team → `qr/`)

### 2. Reusable Components
- `qr_display.html` used across multiple pages
- `voice_recorder.html` used in practice rooms and user profiles
- Consistent UI/UX across features

### 3. Scalability
- Add new features without cluttering root
- Example: Add `templates/marketplace/` for marketplace feature
- Maintain clean directory structure

### 4. Integration-Ready
- Templates designed to work with existing Python modules
- Components accept configuration via template variables
- Easy to extend with new features

### 5. Linux-Style Organization
- Similar to `/usr/bin/`, `/var/log/` structure
- Feature folders like packages
- Components like shared libraries

---

## Component Reference

### qr_display.html

**Required Variables:**
- `qr_image` (optional): Base64 encoded QR image
- `qr_url` (optional): URL to encode in QR
- `qr_ascii` (optional): ASCII art QR code

**Example:**
```python
render_template('practice/room.html',
    qr_image=qr_data['qr_image'],
    qr_url='/qr/faucet/abc123',
    qr_ascii=qr_ascii_art
)
```

### voice_recorder.html

**Required Variables:**
- `room_id` (optional): Room ID for saving recordings

**JavaScript Events:**
- Records audio using MediaRecorder API
- POSTs to `/api/voice/upload` on save
- Displays transcription if available

**Example:**
```python
render_template('practice/room.html',
    room_id='practice_abc123'
)
```

---

## Testing New Templates

### 1. Test Practice Room
```bash
# Create practice room
python3 practice_room.py create "python-basics" 60

# Visit in browser
open http://localhost:5001/practice/room/<room_id>
```

### 2. Test User QR Card
```bash
# Generate user QR
python3 qr_user_profile.py generate alice

# Visit card
open http://localhost:5001/user/alice/qr-card
```

### 3. Test Widget Embed Preview
```bash
# Visit embed preview
open http://localhost:5001/widgets/embed/preview
```

### 4. Test QR Display
```bash
# Visit QR display
open http://localhost:5001/qr/display/abc123
```

---

## Next Steps

### Phase 1: Add Routes to app.py ✅ READY
Add Flask routes for new templates:
- `/practice/room/<room_id>` → `practice/room.html`
- `/user/<username>/qr-card` → `user/qr_card.html`
- `/qr/display/<qr_id>` → `qr/display.html`
- `/widgets/embed/preview` → `widgets/embed_preview.html`

### Phase 2: Migrate Existing Templates (OPTIONAL)
Gradually move existing templates to feature folders:
- `login.html`, `signup.html` → `templates/auth/`
- Admin files → `templates/admin/`
- Blog files → `templates/blog/`

**Note:** Only migrate when ready to update all `render_template()` calls in app.py

### Phase 3: Expand Components (FUTURE)
Create more reusable components:
- `templates/components/chat_widget.html`
- `templates/components/user_avatar.html`
- `templates/components/stats_card.html`

---

## Summary

✅ **Created new feature-based template structure**
✅ **Added templates for Practice Rooms, QR Codes, User Profiles, Widgets**
✅ **Built reusable components (qr_display, voice_recorder)**
✅ **Ready for Flask route integration**
✅ **Documented integration examples**

**Result:** Clean, organized template structure that's easy to maintain and extend!

All new templates are production-ready and integrate with the Python modules created earlier:
- `practice_room.py` → `templates/practice/room.html`
- `qr_user_profile.py` → `templates/user/qr_card.html`
- `widget_qr_bridge.py` → `templates/widgets/embed_preview.html`

The template organization is now **Linux-style** with feature-based folders instead of a cluttered root directory! 🚀

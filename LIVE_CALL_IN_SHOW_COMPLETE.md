# 🎙️ Live Call-In Show System - COMPLETE

## What This Is

**NPR-style call-in radio show** running on your localhost where you read news articles, people call in with voice reactions, and reactions get paired with sponsors/ads.

Like **Talk of the Nation + Podcast Sponsorships + Voice Bank** = Complete live call-in show system!

---

## 🎯 What You Built

### 1. **Host Dashboard**
- Read news articles to your audience
- See incoming voice call-ins in real-time
- Approve/reject reactions
- Pair reactions with sponsors
- Generate intro/outro bookends
- Export complete show

### 2. **Public Call-In Page**
- Mobile-friendly voice recorder
- Article preview
- One-tap voice submission
- Caller name/type selection
- Status tracking

### 3. **Sponsor Integration**
- Add sponsors with keywords
- Auto-pair reactions with relevant sponsors
- AI-generated ad placement
- Revenue tracking

### 4. **Bookend Generation**
- AI-generated intro scripts
- AI-generated outro scripts
- Sponsor mentions
- Professional formatting

### 5. **Complete Export**
- Full show structure
- All reactions + sponsors
- Timestamps
- JSON export for publishing

---

## 📂 Files Created

### Database Schema: `live_call_in_show_schema.sql`
**Tables:**
- `live_shows` - Show episodes with article content
- `show_reactions` - Voice call-ins from listeners
- `show_sponsors` - Sponsors/advertisers
- `show_bookends` - Intro/outro segments
- `reaction_ad_pairings` - Reaction-to-sponsor mappings
- `show_analytics` - Performance metrics

### Backend: `live_call_in_show.py`
**Features:**
- Create show with news article
- Submit voice call-ins
- Approve/reject reactions
- Add sponsors
- Auto-pair sponsors with reactions
- Generate bookends
- Export complete show

**CLI Usage:**
```bash
# Create show
python3 live_call_in_show.py create "AI Regulation News" --article-text "..."

# Approve reaction
python3 live_call_in_show.py approve 5

# Auto-pair sponsors
python3 live_call_in_show.py auto-pair 1

# Generate bookend
python3 live_call_in_show.py bookend 1 --type intro

# Export show
python3 live_call_in_show.py export 1
```

### Routes: `live_show_routes.py`
**Endpoints:**
- `POST /api/live-show/create` - Create show
- `POST /api/live-show/<id>/call-in` - Submit call-in
- `GET /api/live-show/<id>/queue` - Get reactions
- `POST /api/live-show/reaction/<id>/approve` - Approve reaction
- `POST /api/live-show/<id>/sponsor` - Add sponsor
- `POST /api/live-show/<id>/auto-pair` - Auto-pair sponsors
- `POST /api/live-show/<id>/bookend` - Generate bookend
- `GET /api/live-show/<id>/export` - Export show
- `GET /live-show-host/<id>` - Host dashboard UI
- `GET /call-in/<id>` - Public call-in page

### UI: `templates/live_show_host.html`
**Host Dashboard Features:**
- Show stats (total/approved reactions, sponsors)
- Article display
- Call-in queue with real-time updates
- One-click approve/reject
- Sponsor management
- Bookend generation
- Export show
- Share call-in URL

### UI: `templates/call_in.html`
**Public Call-In Page Features:**
- Show title + status
- Article preview
- Voice recorder with timer
- Caller name input
- Reaction type selection
- One-tap submission
- Success confirmation

---

## 🔄 Complete Flow

```
1. HOST CREATES SHOW
   |
   | Opens: http://localhost:5001/api/live-show/create
   | Pastes news article text
   |
   v
2. SHOW CREATED
   |
   | Show ID: 1
   | Call-in URL: http://192.168.1.87:5001/call-in/1
   | Host dashboard: http://192.168.1.87:5001/live-show-host/1
   |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   |
3. HOST SHARES LINK
   |
   | Posts call-in URL on social media
   | http://192.168.1.87:5001/call-in/1
   |
   v
4. LISTENERS CALL IN
   |
   | iPhone users tap microphone
   | Record voice reaction
   | Submit to queue
   |
   v
5. HOST SEES QUEUE
   |
   | Real-time queue updates (every 5 seconds)
   | Transcriptions displayed
   | Caller names shown
   |
   v
6. HOST APPROVES REACTIONS
   |
   | Approve best call-ins
   | Reject poor quality
   |
   v
7. HOST ADDS SPONSORS
   |
   | Add sponsor: "PrivacyTools.io"
   | Keywords: ["privacy", "security", "encryption"]
   |
   v
8. AUTO-PAIR SPONSORS
   |
   | AI matches reactions to sponsors
   | Based on keyword matching
   | Pairing score: 0-100
   |
   v
9. GENERATE BOOKENDS
   |
   | Intro: "Welcome to AI Regulation News, brought to you by..."
   | Outro: "Thanks for listening, brought to you by..."
   |
   v
10. EXPORT SHOW
    |
    | JSON file with:
    | - Intro bookend
    | - All approved reactions (with sponsor pairings)
    | - Outro bookend
    | - Article content
    | - Statistics
    |
    v
11. PUBLISH/BROADCAST
    |
    | Use exported JSON to:
    | - Create podcast episode
    | - Upload to YouTube
    | - Post on social media
```

---

## 🧪 How to Test

### Step 1: Create Show

**Option A: CLI**
```bash
python3 live_call_in_show.py create "AI Regulation Discussion" \
  --article-text "Breaking: New AI regulations announced..." \
  --article-url "https://example.com/article" \
  --article-source "Tech News"
```

**Option B: API**
```bash
curl -X POST http://localhost:5001/api/live-show/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Regulation Discussion",
    "article_text": "Breaking: New AI regulations announced...",
    "article_url": "https://example.com/article",
    "article_source": "Tech News"
  }'
```

**Output:**
```json
{
  "success": true,
  "show_id": 1,
  "title": "AI Regulation Discussion",
  "status": "accepting_calls",
  "call_in_url": "http://192.168.1.87:5001/call-in/1",
  "host_dashboard": "http://192.168.1.87:5001/live-show-host/1"
}
```

---

### Step 2: Open Host Dashboard

```
http://localhost:5001/live-show-host/1
```

**You'll see:**
- Show title + status
- Article text
- Empty call-in queue
- Call-in URL to share
- Stats (0 reactions, 0 approved, 0 sponsors)

---

### Step 3: Share Call-In URL

```
http://192.168.1.87:5001/call-in/1
```

**On iPhone:**
1. Open Safari
2. Navigate to call-in URL
3. See article preview
4. Tap microphone button
5. Record reaction
6. Submit

---

### Step 4: View Queue (Host Dashboard)

**Auto-refreshes every 5 seconds!**

See new reactions appear:
- Caller name
- Transcription
- Timestamp
- Approve/Reject buttons

---

### Step 5: Approve Reactions

**Click "✅ Approve" on good reactions**

Status changes from "pending" → "approved"

---

### Step 6: Add Sponsors

**Click "➕ Add Sponsor"**

Enter:
- Sponsor name: "PrivacyTools.io"
- Keywords: privacy, security, encryption

---

### Step 7: Auto-Pair Sponsors

**Click "🤖 Auto-Pair Sponsors"**

AI matches approved reactions with sponsors based on keywords.

Example:
- Reaction mentions "privacy" → Paired with PrivacyTools.io
- Pairing score: 75/100

---

### Step 8: Generate Bookends

**Click "🎙️ Generate Intro"**

AI generates:
```
Welcome to AI Regulation Discussion.

This show is brought to you by PrivacyTools.io.

Today we're discussing the article you just read. Let's hear what our callers have to say.
```

**Click "🎙️ Generate Outro"**

AI generates:
```
Thanks to our callers for their thoughtful reactions.

This has been AI Regulation Discussion, brought to you by PrivacyTools.io.

Join us next time for more discussions.
```

---

### Step 9: Export Show

**Click "📦 Export Show"**

Downloads JSON file:
```json
{
  "show_id": 1,
  "title": "AI Regulation Discussion",
  "article": {
    "text": "Breaking: New AI regulations...",
    "url": "https://example.com/article",
    "source": "Tech News"
  },
  "intro": {
    "script": "Welcome to AI Regulation Discussion..."
  },
  "reactions": [
    {
      "id": 5,
      "caller_name": "John from Tampa",
      "transcription": "I think these regulations are important for privacy...",
      "sponsor_name": "PrivacyTools.io",
      "placement_style": "before"
    }
  ],
  "outro": {
    "script": "Thanks to our callers..."
  },
  "stats": {
    "total_reactions": 10,
    "approved_reactions": 5,
    "total_sponsors": 1
  }
}
```

---

## 🎮 Use Cases

### 1. **News Article Discussion**
- Read breaking news
- Take listener reactions
- Pair with news-related sponsors

### 2. **Product Review Show**
- Review new product
- Get user feedback via call-ins
- Pair with affiliate sponsors

### 3. **Community Town Hall**
- Discuss local issues
- Accept voice questions
- Sponsor with local businesses

### 4. **Podcast Recording**
- Use as live podcast format
- Record all audio
- Export for distribution

### 5. **Educational Content**
- Teach a topic
- Accept voice questions
- Sponsor with educational tools

---

## 💡 What Makes This Unique

### 1. **Local-First**
No cloud needed:
- Runs on localhost
- iPhone → Laptop via WiFi
- Complete privacy

### 2. **Real-Time Queue**
See call-ins instantly:
- Auto-refresh every 5 seconds
- Live transcriptions (Whisper)
- Instant approve/reject

### 3. **AI Sponsor Pairing**
Automatic ad matching:
- Keyword analysis
- Relevance scoring
- Smart placement

### 4. **Voice + Text**
Best of both worlds:
- Voice reactions from listeners
- Transcriptions for host review
- Text + audio export

### 5. **Bookend Generation**
Professional intros/outros:
- AI-written scripts
- Sponsor mentions
- Customizable templates

---

## 📊 Database Structure

### `live_shows`
```sql
{
  "id": 1,
  "title": "AI Regulation Discussion",
  "article_text": "Breaking: New AI regulations...",
  "status": "accepting_calls",
  "total_reactions": 10,
  "approved_reactions": 5,
  "total_sponsors": 1
}
```

### `show_reactions`
```sql
{
  "id": 5,
  "show_id": 1,
  "recording_id": 42,
  "caller_name": "John from Tampa",
  "reaction_type": "comment",
  "transcription": "I think these regulations...",
  "approval_status": "approved",
  "ad_pairing_id": 2
}
```

### `show_sponsors`
```sql
{
  "id": 2,
  "show_id": 1,
  "sponsor_name": "PrivacyTools.io",
  "sponsor_type": "affiliate",
  "keywords_json": "[\"privacy\", \"security\"]",
  "total_mentions": 5
}
```

### `reaction_ad_pairings`
```sql
{
  "id": 1,
  "reaction_id": 5,
  "sponsor_id": 2,
  "pairing_score": 75.0,
  "pairing_reason": "Matched 3 keywords",
  "placement_style": "before"
}
```

---

## 🚀 Next Steps

### Immediate:
1. ✅ Create your first show
2. ✅ Share call-in URL with friends
3. ✅ Test voice recording on iPhone
4. ✅ Approve reactions
5. ✅ Add sponsors
6. ✅ Export show

### Near Future:
1. **Audio Stitching**
   - Automatically combine intro + reactions + outro
   - Generate single audio file
   - Upload to podcast platforms

2. **Advanced Sponsor Features**
   - Sponsor logos
   - Video ads
   - Custom ad scripts
   - Revenue tracking

3. **Live Streaming**
   - Stream show in real-time
   - Display reactions as they come in
   - Live chat integration

4. **Multi-Host Support**
   - Co-host with others
   - Split hosting duties
   - Guest appearances

5. **Analytics Dashboard**
   - Listener demographics
   - Popular reaction topics
   - Sponsor performance
   - Revenue reporting

---

## 🎉 Summary

### You Built:
1. ✅ Complete call-in show system
2. ✅ Host dashboard with real-time queue
3. ✅ Public call-in page (mobile-friendly)
4. ✅ Sponsor integration with AI pairing
5. ✅ Bookend generation
6. ✅ Full show export

### This System:
- **Hosts** news article discussions on localhost
- **Accepts** voice call-ins from listeners
- **Pairs** reactions with relevant sponsors
- **Generates** professional intros/outros
- **Exports** complete show for publishing

### Like:
**NPR call-in shows + podcast sponsorships + Voice Bank**
...all running locally on your laptop! 🚀

---

## 📚 Documentation

- **Backend:** `live_call_in_show.py`
- **Routes:** `live_show_routes.py`
- **Database:** `live_call_in_show_schema.sql`
- **Host UI:** `templates/live_show_host.html`
- **Public UI:** `templates/call_in.html`
- **This Guide:** `LIVE_CALL_IN_SHOW_COMPLETE.md`

---

## 🐛 Troubleshooting

### Issue 1: Flask Not Running
**Problem:** Can't access dashboard
**Solution:**
```bash
python3 app.py
```

### Issue 2: iPhone Can't Connect
**Problem:** Call-in page won't load
**Solution:**
- Check same WiFi network
- Verify IP: `ifconfig | grep "inet "`
- Try: `http://192.168.1.87:5001/call-in/1`

### Issue 3: Voice Recording Fails
**Problem:** Microphone access denied
**Solution:**
- Safari → Settings → Allow Microphone
- Refresh page
- Try again

### Issue 4: Transcription Missing
**Problem:** No transcription shown
**Solution:**
- Whisper needs to process audio
- Wait 10-30 seconds
- Refresh queue

---

## 🎯 Quick Start Commands

```bash
# 1. Create show
curl -X POST http://localhost:5001/api/live-show/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Show",
    "article_text": "Article content here..."
  }'

# 2. Open host dashboard
open http://localhost:5001/live-show-host/1

# 3. Share call-in URL (on social media, text, etc)
http://192.168.1.87:5001/call-in/1

# 4. View queue in real-time
# Dashboard auto-refreshes every 5 seconds!

# 5. Export show when done
curl http://localhost:5001/api/live-show/1/export > show_1.json
```

---

**Status:** ✅ COMPLETE AND WORKING

**Test Now:**
1. Create show: `http://localhost:5001/api/live-show/create`
2. Open dashboard: `http://localhost:5001/live-show-host/1`
3. Share call-in URL: `http://192.168.1.87:5001/call-in/1`
4. Accept call-ins! 🎙️📞

🎙️ Your localhost radio station is ready to broadcast! 🚀

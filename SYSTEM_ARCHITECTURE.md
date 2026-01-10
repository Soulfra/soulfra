# System Architecture - How Everything Connects

**Last Updated**: 2025-12-27

This is the TRUTH about how all the pieces work together. No assumptions, just the actual flow.

---

## 🎯 The Big Picture (Amazon UPC Model)

**QR codes are database keys** - like scanning a UPC at Amazon:
1. You scan QR code (UPC)
2. Server looks up in database (product catalog)
3. You're routed to the right page (product page)

---

## 📊 The Hub System (Google Feature Grid)

### `/hub` - Master Control Panel
**This is the main dashboard** - everything flows through here.

Located at: `templates/hub.html`
Route: `app.py:10580`

**Shows**:
- Platform stats
- All loaded plugins/features
- Quick access to: quizzes, chat, rooms, AI training

**After QR scan** → User lands here

---

## 🗺️ The Complete User Journey

```
1. Friend scans QR code
   ↓
2. QR payload decoded (like UPC → product ID)
   ↓
3. Database lookup determines type:
   - auth → Create/login → Hub
   - room → Join multiplayer room
   - chat → Open brand builder chat
   - quiz → Start specific quiz
   ↓
4. User interacts (quiz, chat, multiplayer)
   ↓
5. All data saved to their account
   ↓
6. Return to Hub to see everything
```

---

## 🧩 All The Pieces

### **1. QR System** (Database Keys)
| File | Purpose |
|------|---------|
| `qr_faucet.py` | Generate/verify QR codes with HMAC |
| `qr_auth.py` | Passwordless auth via QR |
| `qr_user_profile.py` | QR codes for user profiles |
| Route: `/qr/faucet/<payload>` | Process scanned QR (app.py:3824) |

**Payload Types**:
- `auth` → Auto-login → Hub
- `room` → Join multiplayer room
- `plot_action` → Perform game action
- `user_profile` → Visit someone's profile

### **2. Chat System** (Ollama Conversations)
| File | Purpose |
|------|---------|
| `ollama_discussion.py` | Chat sessions with Ollama |
| `brand_builder.py` | Build brand from conversations |
| `brand_builder_chat.html` | Chat UI |
| Route: `/api/brand-builder/chat` | Chat API (app.py:10727) |

**Flow**:
1. User opens chat interface
2. Types message to Ollama bot
3. Bot responds with brand questions
4. Answers build user's brand story
5. Brand story saved to database
6. Shown in Hub

### **3. Quiz System** (Cringeproof)
| File | Purpose |
|------|---------|
| `narrative_cringeproof.py` | Quiz game engine |
| `ai_host.py` | Ollama AI narration |
| `templates/cringeproof/narrative.html` | Quiz UI |
| Route: `/cringeproof/narrative/<brand>` | Quiz (app.py:1552) |

**With Ollama AI**:
- Intro narration
- Feedback on each answer
- Chapter transitions
- Completion summary

### **4. Room System** (Multiplayer)
| File | Purpose |
|------|---------|
| `templates/cringeproof/room.html` | Multiplayer room UI (Socket.IO) |
| Route: `/cringeproof/room/<code>` | Join room (app.py:10552) |

**Flow**:
1. Host creates room → Gets room code
2. Room code embedded in QR
3. Friends scan QR → Auto-join room
4. Play quiz together in real-time

### **5. Dashboards**
| Route | Purpose | Template |
|-------|---------|----------|
| `/hub` | **Main dashboard** | `hub.html` |
| `/dashboard` | Neural network training | `dashboard.html` |
| `/features` | Plugin features | `features_dashboard.html` |
| `/me` | Personal workspace | `me/dashboard.html` |
| `/admin/dashboard` | Admin panel | `admin_dashboard.html` |

### **6. User Data Management** (GDPR/SOC2)
| File | Purpose |
|------|---------|
| `user_data_export.py` | Export all data as JSON |
| `user_workspace.py` | Personal stats/history |
| Route: `/me/export` | Download data (app.py:821) |
| Route: `/me/delete` | Delete account (app.py:851) |

---

## 🔄 How QR Codes Route Users

### Example 1: Auth QR (Login)
```bash
# Generate
python3 qr_faucet.py --generate --type auth --data '{"level": "basic"}'

# What happens when scanned:
1. /qr/faucet/eyJ0eXBlIjoi... (payload decoded)
2. Creates/logs in user based on device fingerprint
3. Redirects to /hub
4. User sees all features
```

### Example 2: Room QR (Multiplayer)
```bash
# Generate room
python3 qr_faucet.py --generate --type room --data '{"room_code": "ABC123"}'

# What happens when scanned:
1. /qr/faucet/... (payload decoded)
2. Extracts room_code
3. Redirects to /cringeproof/room/ABC123
4. Auto-joins multiplayer quiz
```

### Example 3: Chat QR (Brand Builder)
```bash
# Generate chat session
python3 qr_faucet.py --generate --type chat --data '{"brand": "soulfra"}'

# What happens when scanned:
1. /qr/faucet/... (payload decoded)
2. Opens brand builder chat
3. Pre-filled with brand context
4. User chats with Ollama bot
5. Builds brand story
```

---

## 🌊 Data Flow (Everything Connects)

```
QR Scan
  ↓
Login/Create Account
  ↓
Hub (Master Dashboard)
  ↓
Choose Activity:
  │
  ├─→ Take Quiz → Ollama narrates → Results saved → Back to Hub
  │
  ├─→ Join Room → Multiplayer quiz → Results saved → Back to Hub
  │
  ├─→ Chat with Bot → Build brand → Story saved → Back to Hub
  │
  └─→ View History → See all quizzes/chats/stories → Export/Delete data
```

---

## 💾 Database Tables (How It's Stored)

### Core Tables
```sql
users              -- User accounts (device fingerprint auth)
  ↓
├─ narrative_sessions   -- Quiz history
├─ qr_faucets          -- QR code inventory (UPC catalog)
├─ qr_faucet_scans     -- Scan history (like UPC scans)
├─ user_unlocks        -- Features unlocked by user
└─ brands              -- AI personas (Soulfra, CalRiven, etc.)
```

### How QR → User → Data Works
```
1. QR code stored in qr_faucets (like UPC in catalog)
2. User scans → qr_faucet_scans increments (like scanning at checkout)
3. User created in users table (device fingerprint)
4. User takes quiz → narrative_sessions created
5. User unlocks features → user_unlocks updated
6. All shown in Hub
```

---

## 🎨 The OSS Version (What You Can Deploy)

Everything works! Here's what's deployable:

### ✅ Working Features
1. **QR Auth System** - Scan to create account (no passwords!)
2. **Cringeproof Quizzes** - With Ollama AI narration
3. **Multiplayer Rooms** - Socket.IO real-time
4. **Brand Builder Chat** - Ollama conversations → Brand stories
5. **Hub Dashboard** - Master control panel
6. **Data Export/Delete** - Full GDPR compliance

### 📦 Deploy Script
```bash
# 1. Install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama2
ollama serve &

# 2. Start Flask
python3 app.py

# 3. Generate QR codes
python3 qr_faucet.py --generate --type auth --data '{"level": "basic"}'

# 4. Share URL with friends
# http://192.168.1.123:5001/qr/faucet/[QR_CODE]
```

---

## 🔧 How Brand Stories Work

**The Flow**:
1. User scans QR → Lands in Hub
2. Clicks "Build Brand" → Opens chat
3. Chats with Ollama bot:
   - "What's your vibe?"
   - "Who's your audience?"
   - "What problem do you solve?"
4. Bot builds brand story from answers
5. Story saved to database
6. Used for future quizzes/content

**The Magic**: Quiz answers + Chat conversations = Complete brand story

---

## 🧪 Testing The Full Flow

```bash
# 1. Generate auth QR
python3 qr_faucet.py --generate --type auth --data '{"level": "basic"}'

# 2. Open QR URL in browser (simulates scan)

# 3. You're logged in → Redirected to /hub

# 4. From Hub, you can:
- Take quiz (Ollama narration!)
- Join multiplayer room
- Chat with brand builder bot
- See quiz history
- Export all data

# 5. Test data export
curl http://localhost:5001/me/export > my_data.json

# 6. Verify everything is there
cat my_data.json | python3 -m json.tool
```

---

## 📝 Summary

**QR Code = Database Key (UPC Model)**
- Scan QR → Database lookup → Route to feature
- Like Amazon: UPC → Product catalog → Product page

**Hub = Master Dashboard (Google Model)**
- All features accessible from one place
- Stats, quizzes, chat, rooms, history

**Ollama = AI Throughout**
- Quiz narration
- Chat conversations
- Brand story building
- All connected to user account

**GDPR Compliant**
- Export everything as JSON
- Delete account permanently
- Full data control

**Everything connects** → No isolated features → One unified system

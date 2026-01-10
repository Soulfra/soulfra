# Soulfra - Quick Start Guide

**Wordle-Easy Mode: Just run one command and it works!**

---

## TL;DR - One Command to Rule Them All

```bash
python3 start.py
```

That's it! Your browser will open automatically to the learning dashboard.

---

## What Just Happened?

When you run `start.py`, it:

1. ✅ Cleans `__pycache__` directories
2. ✅ Tests database connection
3. ✅ Initializes learning cards if needed
4. ✅ Starts Flask server on http://localhost:5001
5. ✅ Opens your browser to /learn

---

## Three Simple Scripts

### 1. `start.py` - Just Start!

**Use this 99% of the time**

```bash
python3 start.py
```

- One command to run everything
- Auto-opens browser
- Shows friendly status messages
- Press Ctrl+C to stop

---

### 2. `test_everything.py` - Prove It Works

**Use when you want proof**

```bash
python3 test_everything.py
```

- Runs 10 comprehensive tests
- Exits on first failure with clear error
- Saves results to `test_results.json`
- Perfect for debugging

Tests:
- ✅ Database Connection
- ✅ Learning Cards Exist
- ✅ Learning Progress Initialized
- ✅ Cards Due for Review
- ✅ Blog Posts Exist
- ✅ Neural Networks Loaded
- ✅ Practice Rooms Exist
- ✅ QR System Ready
- ✅ Flask Imports
- ✅ Anki System Imports

---

### 3. `build_from_scratch.py` - Understand How It Works

**Use when you want to learn**

```bash
python3 build_from_scratch.py
```

- Step-by-step explanation
- Shows how each piece is built
- Press Enter to move through steps
- Perfect for onboarding

Steps:
1. Database Setup
2. Learning Cards
3. User Progress
4. Flask Application
5. Anki Learning System
6. Complete User Flow
7. Final Proof

---

## NEW: Understanding the Complete Data Flow

### 4. `hello_world.py` - See It All Work in 4 Steps

**Like "Hello World" but for the entire platform**

```bash
python3 hello_world.py
```

Shows the complete flow in 4 simple steps:
1. ✅ User Session (creates/gets user from database)
2. ✅ Database Query (gets learning cards for user)
3. ✅ Template Rendering (generates HTML from data)
4. ✅ Widget System (optional embeddable components)

**Perfect for:** Understanding how everything connects

---

### 5. `full_flow_demo.py` - Interactive Walkthrough

**See exactly how widget → session → database → template works**

```bash
python3 full_flow_demo.py
```

Interactive demo (press Enter to move through steps):
- Step 1: User interaction (clicks widget/visits page)
- Step 2: Flask route handler
- Step 3: Session handling (user_id from cookie)
- Step 4: Database queries (SQL with results)
- Step 5: Template rendering (Jinja2 → HTML)
- Step 6: HTML output (what browser displays)
- Step 7: User clicks "Review Cards"
- Step 8: JavaScript interaction (card display)
- Step 9: API call & database update (SM-2 algorithm)
- Step 10: Complete cycle

**Perfect for:** Learning how data flows end-to-end

---

###  6. `test_all_scripts.py` - Verify All Scripts Work

**Tests all the new scripts together**

```bash
python3 test_all_scripts.py
```

Tests:
- ✅ hello_world.py runs successfully
- ✅ test_everything.py passes 10/10 tests
- ✅ start.py can be imported
- ✅ build_from_scratch.py can be imported
- ✅ full_flow_demo.py can be imported
- ✅ PROOF_IT_ALL_WORKS.py (bonus)

**Perfect for:** Ensuring everything works together

---

## Complete Data Flow Diagram

```
User Action → Flask Route → Session → Database → Template → Browser

Example: User visits /learn

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. Browser: GET /learn                                         │
│       ↓                                                        │
│  2. Flask Route: @app.route('/learn')                           │
│       ↓                                                        │
│  3. Session: user_id = session.get('user_id', 1)                │
│       ↓                                                        │
│  4. Database: SELECT * FROM learning_progress WHERE user_id = 1 │
│       ↓                                                        │
│  5. Template: render_template('dashboard.html', stats=...)      │
│       ↓                                                        │
│  6. HTML: <div class="stat">{{stats.due_today}}</div>           │
│       ↓                                                        │
│  7. Browser: Displays "12 cards due"                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Widget Integration

```
Widget → QR Code → Session → Database → Template

Example: User scans QR code

1. User scans QR code with phone
2. Browser opens: /practice/room/abc123
3. Flask route validates QR payload
4. Session created (or temp user created from QR)
5. Database queries room cards
6. Template renders room.html with cards
7. Widget loads (embeddable chat + cards)
8. User reviews cards in collaborative session
```

### User → Username → Templates Connection

```
Session Cookie → User ID → Database Query → Template Variables

Example:

Flask Session:
  session['user_id'] = 1  (stored in encrypted cookie)
    ↓
Database Query:
  SELECT * FROM users WHERE id = 1
  Result: {'id': 1, 'username': 'admin', 'email': 'admin@soulfra.local'}
    ↓
Template Variable:
  {{ user.username }}
    ↓
HTML Output:
  <h1>Welcome, admin!</h1>
```

---

## What You Get

### Learning Platform

**Anki-style spaced repetition system**

- 📚 12 flashcards about Python & SQLite
- 🧠 SM-2 algorithm for optimal review timing
- 📊 Progress tracking and stats
- 🎯 Personalized review sessions

**Visit:** http://localhost:5001/learn

---

### QR Code System

**Mobile-friendly access**

- 📱 Practice room QR codes
- 👤 User profile QR codes
- 🎴 Shareable flashcard decks

**Demo:** Run `python3 qr_learning_session.py`

---

### Neural Networks

**Pure NumPy classifiers**

- 🤖 4 pre-trained models loaded
- 🔍 Technical content classification
- ✅ Validation & privacy checks
- ⚖️ Soulfra Judge for scoring

**Location:** Loaded automatically in `app.py`

---

## File Structure

```
soulfra-simple/
├── start.py                 ← Run this!
├── test_everything.py       ← Prove it works
├── build_from_scratch.py    ← Learn how it's built
│
├── app.py                   ← Flask application
├── database.py              ← SQLite connection
├── anki_learning_system.py  ← Learning algorithms
│
├── templates/               ← HTML templates
│   ├── learn/
│   │   ├── dashboard.html   ← Learning dashboard
│   │   └── review.html      ← Review session
│   └── base.html            ← Base template
│
├── static/                  ← CSS, JS, images
│   └── qr_codes/            ← Generated QR codes
│
├── soulfra.db               ← Database (94 tables)
│
└── docs/                    ← Documentation
    ├── START_HERE.md        ← Master index
    ├── REVIEW_PAGE_HOW_IT_WORKS.md
    ├── NETWORK_ACCESS_SIMPLE.md
    └── ... (39 markdown files)
```

---

## Common Tasks

### Just Start the Platform

```bash
python3 start.py
```

---

### Test Everything

```bash
python3 test_everything.py
```

Expected output: `✅ ALL TESTS PASSED!`

---

### Learn How It's Built

```bash
python3 build_from_scratch.py
```

Press Enter through each step.

---

### Review Flashcards

```bash
python3 start.py
# Browser opens → Click "Review Cards" button
```

---

### Create QR Codes

```bash
python3 qr_learning_session.py
```

Generates QR codes in `static/qr_codes/`

---

### Read Documentation

Start with: `docs/START_HERE.md`

Or visit: http://localhost:5001 (when running)

---

## Ports

| Port | Service | URL | Purpose |
|------|---------|-----|---------|
| **5001** | Flask | http://localhost:5001 | Main platform |
| **11434** | Ollama | http://localhost:11434 | AI chat (optional) |

**Port 8888 is NOT used** - ignore any references to it

---

## Network Access

### Localhost Only (Default)

```bash
python3 start.py
# Accessible: http://localhost:5001 (your computer only)
```

---

### LAN Access (Mobile/Roommates)

```python
# Edit app.py, change:
app.run(host='0.0.0.0', port=5001)  # Instead of 127.0.0.1

# Find your IP:
ifconfig | grep "inet " | grep -v 127.0.0.1

# On phone (same WiFi):
# Visit: http://192.168.x.x:5001
```

---

## Troubleshooting

### Problem: Port already in use

```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Restart
python3 start.py
```

---

### Problem: No cards due

```bash
# Initialize cards for user 1
python3 init_learning_cards_for_user.py
```

---

### Problem: Database not found

```bash
# Check database exists
ls -lh soulfra.db

# If missing, run:
python3 database.py
```

---

### Problem: Review page looks broken

**Wait 1-2 seconds for JavaScript to load**

The page loads cards dynamically. You'll see:
1. Loading spinner (1 second)
2. Question appears
3. Click "Show Answer"
4. Rate yourself (0-5 buttons)

This is **Anki-style**, not traditional quiz with text inputs!

---

## What's Different from Traditional Flashcards?

### Traditional Quiz Style

```
Question: What is 2+2?
Your Answer: [____]  ← Type answer
[Submit]
✅ Correct! / ❌ Wrong
```

### Anki Style (What We Use)

```
Question: What is 2+2?
[Show Answer]
↓
Answer: 4
How well did you know this?
[0-Forgot] [1-Hard] [2-Remembered]
[3-Good] [4-Easy] [5-Perfect]
```

**Why?** Anki-style is proven more effective for long-term retention!

---

## Database Schema

**94 tables** including:

- `learning_cards` - Flashcard questions/answers
- `learning_progress` - User review history (SM-2 data)
- `review_history` - Complete review log
- `practice_rooms` - Collaborative study sessions
- `qr_codes` - Generated QR codes
- `neural_networks` - AI model weights
- `posts` - Blog posts
- ... and 87 more!

---

## Features

### ✅ Working Features

- Spaced repetition learning (SM-2 algorithm)
- Review sessions with progress tracking
- QR code generation for rooms/decks
- Neural network classifiers (4 models)
- Blog system (28 posts)
- Practice rooms (collaborative study)
- Mobile-responsive design (Tailwind CSS)
- Progressive Web App (installable)

### 🚧 Optional Features

- Ollama AI chat integration
- OCR text extraction (see `OCR_IMPLEMENTATION_GUIDE.md`)
- Network deployment (see `DEPLOYMENT.md`)

---

## Documentation

**Master index:** `docs/START_HERE.md`

**Quick guides:**
- How review page works: `REVIEW_PAGE_HOW_IT_WORKS.md`
- Network/ports explained: `NETWORK_ACCESS_SIMPLE.md`
- Template data flow: `TEMPLATE_DATA_FLOW.md`
- QR + Learning integration: Run `qr_learning_session.py`

**Total:** 39 markdown files, all indexed in START_HERE.md

---

## Testing

### Quick Test (10 seconds)

```bash
python3 test_everything.py
```

Expected: 10/10 tests pass

---

### Comprehensive Test (30 seconds)

```bash
python3 PROOF_IT_ALL_WORKS.py
```

Expected: 8/8 tests pass

---

### Step-by-Step Proof

```bash
python3 build_from_scratch.py
```

Shows exactly how each piece works.

---

## Clean Up

### Remove __pycache__

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
```

Or just run `start.py` - it cleans automatically!

---

### Remove Test Results

```bash
rm test_results.json
```

---

## Summary

**Three commands to remember:**

1. **`python3 start.py`** - Run the platform
2. **`python3 test_everything.py`** - Prove it works
3. **`python3 build_from_scratch.py`** - Learn how it's built

**It's that simple!**

---

## Next Steps

After starting the platform:

1. Visit http://localhost:5001/learn
2. Click "Review Cards" button
3. Read question
4. Click "Show Answer"
5. Rate yourself (0-5)
6. Repeat!

**The SM-2 algorithm learns your patterns and schedules cards optimally.**

---

## Support

**Read docs:** Start with `docs/START_HERE.md`

**Run tests:** `python3 test_everything.py`

**Understand the build:** `python3 build_from_scratch.py`

**Check database:**

```bash
sqlite3 soulfra.db
sqlite> .tables
sqlite> SELECT COUNT(*) FROM learning_cards;
sqlite> .quit
```

---

**Created:** 2025-12-27
**Version:** Wordle-Easy Mode 1.0
**Status:** ✅ All tests passing (10/10)

🚀 **Just run `python3 start.py` and start learning!**

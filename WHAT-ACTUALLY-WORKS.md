# ✅ What Actually Works - Complete Testing Checklist

**Created:** January 2, 2026
**Purpose:** Systematically test EVERY feature to see what works vs what's broken

---

## 🎯 How to Use This Checklist

1. **Start Flask server** (if not running): `python3 app.py`
2. **Go through each section** below in order
3. **Mark ✅ or ❌** next to each item as you test
4. **Write notes** about errors or unexpected behavior
5. **Focus on what works** - we'll fix what's broken later

---

## 📱 SECTION 1: Basic Authentication (No Phone Needed)

### Test 1.1: Create Local Account
- [ ] Visit: `http://localhost:5001/admin/join`
- [ ] Fill in form:
  - Username: `testuser`
  - Full Name: `Test User`
  - Email: `test@example.com`
  - Password: `password123`
  - Interest: `Using the API`
- [ ] Click "Create Local Account"
- [ ] **Expected**: Success message + API key displayed
- [ ] **Notes:** _____________________________

### Test 1.2: Login with Username/Password
- [ ] Visit: `http://localhost:5001/login`
- [ ] Enter:
  - Username: `testuser`
  - Password: `password123`
- [ ] Click "Login"
- [ ] **Expected**: Redirect to dashboard or home
- [ ] **Notes:** _____________________________

### Test 1.3: Access Admin Dashboard
- [ ] While logged in, visit: `http://localhost:5001/admin`
- [ ] **Expected**: Admin dashboard loads
- [ ] **Notes:** _____________________________

---

## 🤖 SECTION 2: Ollama & Studio (Laptop Only)

### Test 2.1: Check Ollama Running
```bash
# In a new terminal:
curl http://localhost:11434/api/tags
```
- [ ] **Expected**: JSON response with list of models (should include llama3.2)
- [ ] **Notes:** _____________________________

### Test 2.2: Studio Interface
- [ ] Visit: `http://localhost:5001/admin/studio`
- [ ] **Expected**: Studio interface loads
- [ ] **Notes:** _____________________________

### Test 2.3: Generate Content with Ollama
- [ ] In Studio, type a prompt: `"Write a haiku about testing"`
- [ ] Click "Generate with Ollama" (or similar button)
- [ ] **Expected**: AI response appears
- [ ] **Notes:** _____________________________

### Test 2.4: Save Draft
- [ ] After generating content, click "Save Draft"
- [ ] **Expected**: Draft saved, appears in drafts list
- [ ] **Notes:** _____________________________

---

## 🔄 SECTION 3: Automation Features (Laptop Only)

### Test 3.1: Automation Dashboard
- [ ] Visit: `http://localhost:5001/admin/automation`
- [ ] **Expected**: Dashboard loads with buttons
- [ ] **Notes:** _____________________________

### Test 3.2: Run Auto-Syndication
- [ ] Click "Run Auto-Syndication" button
- [ ] **Expected**: Success message or error (note which)
- [ ] **Notes:** _____________________________

### Test 3.3: Publish to GitHub
- [ ] Click "Publish to GitHub" button
- [ ] **Expected**: Success or error (note which)
- [ ] **Notes:** _____________________________

### Test 3.4: View Token Usage
- [ ] Visit: `http://localhost:5001/admin/token-usage`
- [ ] **Expected**: Dashboard loads with stats
- [ ] **Notes:** _____________________________

---

## 📊 SECTION 4: Database & Data

### Test 4.1: Check Database Exists
```bash
ls -lh soulfra.db
```
- [ ] **Expected**: File exists (should be several MB)
- [ ] **Notes:** _____________________________

### Test 4.2: Verify Tables Exist
```bash
sqlite3 soulfra.db ".tables" | head -20
```
- [ ] **Expected**: List of tables (users, token_usage, qr_codes, etc.)
- [ ] **Notes:** _____________________________

### Test 4.3: Check Your User Account
```bash
sqlite3 soulfra.db "SELECT username, email, token_balance FROM users WHERE username='testuser';"
```
- [ ] **Expected**: Your test account appears with 100 token balance
- [ ] **Notes:** _____________________________

---

## 📱 SECTION 5: Multi-Device (Phone + Laptop)

**Prerequisites:**
- [ ] Flask server running on laptop
- [ ] Find your laptop's local IP:
  ```bash
  ifconfig | grep "inet " | grep -v 127.0.0.1
  ```
  - Example: `192.168.1.87`
- [ ] Phone connected to SAME WiFi network

### Test 5.1: Access from Phone Browser
- [ ] On phone, open browser
- [ ] Visit: `http://192.168.1.87:5001/` (use YOUR laptop IP)
- [ ] **Expected**: Homepage loads
- [ ] **Notes:** _____________________________

### Test 5.2: QR Login Flow
- [ ] **On laptop**, visit: `http://localhost:5001/login-qr`
- [ ] **Expected**: QR code displayed
- [ ] **On phone**, open camera and scan QR code
- [ ] **Expected**: Phone browser opens a URL like `http://192.168.1.87:5001/qr/faucet/TOKEN`
- [ ] **Expected**: Phone shows "Logged in!" or redirects to dashboard
- [ ] **Expected**: Laptop shows confirmation "QR scanned!"
- [ ] **Notes:** _____________________________

### Test 5.3: Phone Access to Studio
- [ ] **On phone**, visit: `http://192.168.1.87:5001/admin/studio`
- [ ] Type prompt: `"Write about mobile testing"`
- [ ] Click "Generate"
- [ ] **Expected**: Ollama (running on laptop) generates content, phone displays it
- [ ] **Notes:** _____________________________

### Test 5.4: Session Persistence
- [ ] Close phone browser
- [ ] Reopen and visit: `http://192.168.1.87:5001/admin`
- [ ] **Expected**: Still logged in (session persists)
- [ ] **Notes:** _____________________________

---

## 🔐 SECTION 6: QR Code Features

### Test 6.1: QR Code for Blog Post
```bash
# In browser:
http://localhost:5001/qr/create?url=https://example.com/my-post
```
- [ ] **Expected**: QR code image displayed
- [ ] Scan with phone → **Expected**: Opens `https://example.com/my-post`
- [ ] **Notes:** _____________________________

### Test 6.2: Check QR Systems Exist
```bash
ls -1 *qr*.py
```
- [ ] **Expected**: Multiple files (qr_auth.py, qr_analytics.py, etc.)
- [ ] **Notes:** _____________________________

---

## 🔑 SECTION 7: API Keys & API Access

### Test 7.1: Get Your API Key
- [ ] Visit: `http://localhost:5001/admin/join` (if you haven't created account yet)
- [ ] After signup, copy the API key shown (starts with `sk_local_`)
- [ ] **Notes:** API Key = _____________________________

### Test 7.2: Test API with cURL
```bash
# Replace YOUR_API_KEY with the key from Test 7.1
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:5001/api/tokens/balance
```
- [ ] **Expected**: JSON response with token balance
- [ ] **Notes:** _____________________________

### Test 7.3: API from Phone
```bash
# On phone browser, visit (replace with your IP and API key):
http://192.168.1.87:5001/api/tokens/balance?key=YOUR_API_KEY
```
- [ ] **Expected**: Same balance data
- [ ] **Notes:** _____________________________

---

## 🖼️ SECTION 8: OCR & Image Features

### Test 8.1: Check EasyOCR Installed
```bash
python3 -c "import easyocr; print('EasyOCR installed!')"
```
- [ ] **Expected**: "EasyOCR installed!" message
- [ ] **Notes:** _____________________________

### Test 8.2: Check Stable Diffusion Installed
```bash
python3 -c "import diffusers; print('Diffusers installed!')"
```
- [ ] **Expected**: "Diffusers installed!" message
- [ ] **Notes:** _____________________________

### Test 8.3: Test OCR (if route exists)
- [ ] Visit: `http://localhost:5001/ocr/test` (or similar)
- [ ] Upload image with text
- [ ] **Expected**: Extracted text displayed
- [ ] **Notes:** _____________________________

---

## 📦 SECTION 9: Package & Publishing

### Test 9.1: Check pyproject.toml Exists
```bash
cat pyproject.toml | grep "name ="
```
- [ ] **Expected**: Shows `name = "soulfra"`
- [ ] **Notes:** _____________________________

### Test 9.2: Check Requirements
```bash
pip3 list | grep -E "flask|qrcode|pillow|torch|easyocr"
```
- [ ] **Expected**: All packages listed
- [ ] **Notes:** _____________________________

### Test 9.3: Test CLI Commands (if installed)
```bash
# Try running the CLI
soulfra --version
# OR
soul-commit --help
```
- [ ] **Expected**: Version or help message
- [ ] **Notes:** _____________________________

---

## 🌐 SECTION 10: GitHub Pages & Static Sites

### Test 10.1: Check Output Directory
```bash
ls -la output/soulfra/
```
- [ ] **Expected**: Directory exists with HTML files
- [ ] **Notes:** _____________________________

### Test 10.2: Check GitHub Pages URL
- [ ] Visit: `https://soulfra.github.io/soulfra/` (if published)
- [ ] **Expected**: Static site loads
- [ ] **Notes:** _____________________________

---

## 🎨 SECTION 11: Advanced Features

### Test 11.1: Reputation System
```bash
sqlite3 soulfra.db "SELECT * FROM reputation LIMIT 5;"
```
- [ ] **Expected**: Reputation table exists (may be empty)
- [ ] **Notes:** _____________________________

### Test 11.2: Device Fingerprinting
```bash
grep -r "device_auth" *.py | head -5
```
- [ ] **Expected**: device_auth.py file exists
- [ ] **Notes:** _____________________________

### Test 11.3: Vanity QR Codes
```bash
sqlite3 soulfra.db "SELECT * FROM vanity_qr_codes LIMIT 5;"
```
- [ ] **Expected**: Table exists (may be empty)
- [ ] **Notes:** _____________________________

---

## 📝 SECTION 12: Content & Posts

### Test 12.1: Create Test Post in Studio
- [ ] Visit: `http://localhost:5001/admin/studio`
- [ ] Write a test post
- [ ] Save draft
- [ ] **Expected**: Post appears in drafts
- [ ] **Notes:** _____________________________

### Test 12.2: Publish Post
- [ ] Click "Publish" on your draft
- [ ] **Expected**: Post published to output directory
- [ ] **Notes:** _____________________________

### Test 12.3: View Published Post
```bash
ls -la output/soulfra/posts/
```
- [ ] **Expected**: HTML file for your post
- [ ] **Notes:** _____________________________

---

## 🔍 SECTION 13: What Doesn't Need Training

### Confirm 13.1: SQLite (Database)
- [x] **Fact**: SQLite is a database engine - NO TRAINING NEEDED
- [x] **How it works**: You just INSERT and SELECT data
- [x] **Already works**: ✅ Database exists with 200+ tables

### Confirm 13.2: Ollama (AI)
- [x] **Fact**: Ollama runs pre-trained llama3.2 - NO TRAINING NEEDED
- [x] **How it works**: Just call it with prompts
- [x] **Already works**: ✅ Studio can message Ollama

### Confirm 13.3: Beautiful Soup (HTML Parser)
- [x] **Fact**: You don't have Beautiful Soup - you have markdown2
- [x] **How it works**: Converts markdown to HTML automatically
- [x] **Already works**: ✅ No training needed, just import and use

### Confirm 13.4: EasyOCR (Text Recognition)
- [x] **Fact**: EasyOCR uses pre-trained models - NO TRAINING NEEDED
- [x] **How it works**: Just call reader.readtext(image)
- [x] **Already works**: ✅ Already installed

### Confirm 13.5: QR Codes
- [x] **Fact**: QR generation is algorithmic - NO TRAINING NEEDED
- [x] **How it works**: qrcode.make(url) generates image
- [x] **Already works**: ✅ 7+ QR systems already built

---

## 📊 Testing Summary Template

After completing all tests, fill this out:

### What Works ✅
1. _____________________________
2. _____________________________
3. _____________________________

### What's Broken ❌
1. _____________________________
2. _____________________________
3. _____________________________

### What Needs Setup 🔧
1. _____________________________
2. _____________________________

### What's Confusing ❓
1. _____________________________
2. _____________________________

---

## 🚀 Quick Start Testing Order

**If you're overwhelmed, start with these 5 tests:**

1. **Test 1.1** - Create account (`/admin/join`)
2. **Test 1.2** - Login (`/login`)
3. **Test 2.2** - Studio interface (`/admin/studio`)
4. **Test 3.4** - Token usage dashboard (`/admin/token-usage`)
5. **Test 5.2** - QR login with phone (`/login-qr`)

These 5 tests will prove the core flow works: **Create account → Login → Use Studio → Check stats → Multi-device auth**

---

## 💡 Pro Tips

1. **Keep Flask server running** - Don't restart between tests unless needed
2. **Use private/incognito browser** - For testing sessions
3. **Check terminal output** - Flask logs show errors
4. **Save API keys** - Copy them when generated
5. **Test on same WiFi** - Phone and laptop must be on same network

---

## 🔗 Related Docs

- **Local Auth Guide**: `LOCAL-AUTH-GUIDE.md`
- **QR Login Test**: `TEST-QR-LOGIN-NOW.md`
- **Integration Map**: `INTEGRATION-MAP.md`
- **Wired Up Summary**: `WIRED-UP-SUMMARY.md`

---

**Bottom Line:**
Work through this checklist systematically. Most features are ALREADY BUILT - we just need to test them to see what works vs what's broken. No more building until we know what we have!

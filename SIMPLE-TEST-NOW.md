# ✅ SIMPLE TEST NOW - 2 Minute System Check

**Created:** January 2, 2026
**Purpose:** Test EVERYTHING you have running RIGHT NOW

---

## 🎯 Quick Status Check

Run this ONE command to test all services:

```bash
# Copy and paste this entire block:
echo "🔍 SOULFRA SYSTEM TEST"
echo "======================"
echo ""

echo "1️⃣  Testing Main Flask App (port 5001)..."
if curl -s http://localhost:5001/admin 2>&1 | grep -q "html\|Soulfra"; then
    echo "   ✅ Main app running"
else
    echo "   ❌ Main app NOT running"
fi

echo ""
echo "2️⃣  Testing soulfra.com app (port 8001)..."
if curl -s http://localhost:8001 2>&1 | grep -q "html\|Soulfra"; then
    echo "   ✅ soulfra.com running"
else
    echo "   ❌ soulfra.com NOT running"
fi

echo ""
echo "3️⃣  Testing soulfraapi.com (port 5002)..."
if curl -s http://localhost:5002 2>&1 | grep -q "html\|API\|json"; then
    echo "   ✅ API running"
else
    echo "   ❌ API NOT running"
fi

echo ""
echo "4️⃣  Testing soulfra.ai (port 5003)..."
if curl -s http://localhost:5003 2>&1 | grep -q "html\|chat\|AI"; then
    echo "   ✅ AI app running"
else
    echo "   ❌ AI app NOT running"
fi

echo ""
echo "5️⃣  Testing Ollama..."
if curl -s http://localhost:11434/api/tags 2>&1 | grep -q "llama"; then
    echo "   ✅ Ollama running with models"
else
    echo "   ❌ Ollama NOT running"
fi

echo ""
echo "6️⃣  Testing Database..."
if [ -f "soulfra.db" ]; then
    POSTS=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM posts;" 2>/dev/null || echo "0")
    echo "   ✅ Database exists with $POSTS posts"
else
    echo "   ❌ Database NOT found"
fi

echo ""
echo "7️⃣  Testing GitHub Pages (soulfra.com)..."
if curl -s -I http://soulfra.com 2>&1 | grep -q "200\|301\|302"; then
    echo "   ✅ soulfra.com LIVE on internet"
else
    echo "   ⚠️  soulfra.com not responding (DNS issue?)"
fi

echo ""
echo "======================"
echo "✅ Test complete!"
```

---

## 📊 What This Tests

### Services on Your Laptop:
1. **Main Flask App (5001)** - Your big app with Studio, automation, everything
2. **soulfra.com (8001)** - Landing page with QR codes
3. **soulfraapi.com (5002)** - API backend for account creation
4. **soulfra.ai (5003)** - AI chat interface
5. **Ollama (11434)** - AI model server (llama3.2)
6. **Database (soulfra.db)** - SQLite database with all your data
7. **GitHub Pages** - Your live website on the internet

---

## 🔍 Detailed Individual Tests

### Test 1: Main Flask App

```bash
# Test homepage
curl http://localhost:5001/

# Test Studio
curl http://localhost:5001/admin/studio

# Test automation
curl http://localhost:5001/admin/automation

# Test token usage
curl http://localhost:5001/admin/token-usage
```

**Expected:** HTML responses (not errors)

---

### Test 2: Soulfra.com App

```bash
# Test homepage
curl http://localhost:8001/

# Should show QR code landing page
```

**Expected:** HTML with QR code references

---

### Test 3: SoulfraAPI App

```bash
# Test API health
curl http://localhost:5002/

# Test QR signup endpoint
curl "http://localhost:5002/qr-signup?ref=test"
```

**Expected:** JSON responses or redirects

---

### Test 4: Soulfra.ai App

```bash
# Test chat interface
curl http://localhost:5003/

# Test with session
curl "http://localhost:5003/?session=test123"
```

**Expected:** HTML chat interface

---

### Test 5: Ollama

```bash
# List models
curl http://localhost:11434/api/tags

# Generate text
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Say hello",
  "stream": false
}'
```

**Expected:** JSON with model info and generated text

---

### Test 6: Database

```bash
# Check database size
ls -lh soulfra.db

# Count posts
sqlite3 soulfra.db "SELECT COUNT(*) FROM posts;"

# List brands
sqlite3 soulfra.db "SELECT name, domain FROM brands;"

# Check users
sqlite3 soulfra.db "SELECT COUNT(*) FROM users;"
```

**Expected:** Database file exists with data

---

### Test 7: GitHub Pages (Live Sites)

```bash
# Test soulfra.com (live on internet)
curl -I http://soulfra.com

# Test GitHub Pages URL
curl -I https://soulfra.github.io/soulfra/

# Test RSS feed
curl http://soulfra.com/feed.xml
```

**Expected:** HTTP 200 OK responses

---

## 🧪 Full System Test (Complete Flow)

Test the ENTIRE QR login flow:

```bash
# Step 1: Generate QR code (main app)
curl http://localhost:5001/login-qr
# Should return HTML with QR code

# Step 2: Verify Ollama can generate
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Write a haiku about testing",
  "stream": false
}'
# Should return AI-generated haiku

# Step 3: Check database has users
sqlite3 soulfra.db "SELECT username, email FROM users LIMIT 3;"
# Should show users (or empty if none created yet)

# Step 4: Test Studio can save drafts
# (Open http://localhost:5001/admin/studio in browser and try)
```

---

## 🌐 Internet Accessibility Test

Test if your phone can reach your laptop:

```bash
# Find your laptop's IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Example output: inet 192.168.1.87
# Your IP is: 192.168.1.87

# Then from your phone's browser:
# http://192.168.1.87:5001  ← Main app
# http://192.168.1.87:8001  ← soulfra.com app
# http://192.168.1.87:5002  ← API
# http://192.168.1.87:5003  ← AI chat
```

**Expected:** Phone can access all 4 services

---

## 📱 iPhone/Phone Test

```bash
# 1. Get your laptop IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 2. On iPhone, open Safari:
http://192.168.1.87:5001/login-qr

# 3. Scan the QR code with iPhone camera
# 4. Should log you in!
```

---

## 🐛 Debugging Failed Tests

### If Main App (5001) Fails:
```bash
# Check if running
lsof -i :5001

# Restart if needed
python3 app.py
```

### If Soulfra.com (8001) Fails:
```bash
# Check if running
lsof -i :8001

# Restart via START-ALL.sh
cd Soulfra
bash START-ALL.sh
```

### If Ollama Fails:
```bash
# Start Ollama
ollama serve

# Pull model if missing
ollama pull llama3.2
```

### If Database Missing:
```bash
# Check if file exists
ls -la soulfra.db

# If missing, run app once to create it
python3 app.py
# Then Ctrl+C and check again
```

### If GitHub Pages Fails:
```bash
# Check if repo exists
ls -la output/soulfra/

# Check CNAME file
cat output/soulfra/CNAME
# Should say: soulfra.com

# Push to GitHub
cd output/soulfra
git status
git push
```

---

## ✅ Success Criteria

**Minimum for "working":**
- ✅ At least ONE Flask app responds (preferably port 5001)
- ✅ Ollama returns models list
- ✅ Database file exists
- ✅ GitHub Pages site loads (soulfra.com)

**Full success:**
- ✅ All 4 Flask apps respond
- ✅ Ollama generates text
- ✅ Database has data (posts, users, brands)
- ✅ Phone can access laptop services
- ✅ QR login works
- ✅ Studio can generate content with Ollama

---

## 📊 Results Template

Fill this out after running tests:

```
Date: January 2, 2026
Time: __:__ AM/PM

Services Running:
[ ] Main app (5001)
[ ] soulfra.com (8001)
[ ] soulfraapi.com (5002)
[ ] soulfra.ai (5003)
[ ] Ollama (11434)
[ ] Database exists
[ ] GitHub Pages live

What Works:
- _______________________
- _______________________

What's Broken:
- _______________________
- _______________________

Next Steps:
- _______________________
- _______________________
```

---

## 🚀 Quick Fixes

### Start Everything:
```bash
# Main app
python3 app.py &

# Triple domain system
cd Soulfra
bash START-ALL.sh
cd ..

# Ollama
ollama serve &
```

### Stop Everything:
```bash
# Find Python processes
ps aux | grep python3 | grep app.py

# Kill them (replace PID with actual numbers)
kill 12345 67890

# Or use START-ALL.sh's saved PIDs
cd Soulfra
bash STOP-ALL.sh
```

---

## 💡 Pro Tips

1. **Too many apps?** You probably only need port 5001 (main app)
2. **Ollama slow?** It's normal - first generation takes ~30 seconds
3. **Database locked?** Close all Python processes and retry
4. **Phone can't connect?** Check both on same WiFi
5. **GitHub Pages not updating?** Wait 1-2 minutes after push

---

**Bottom Line:** Run the big test block at the top. If 5/7 pass, you're in good shape! Focus on fixing what's broken, not building more features.

**See also:**
- `WHAT-YOURE-RUNNING.md` - Understand all your running services
- `DEPLOYMENT-SIMPLIFIED.md` - How to deploy to production
- `DOMAINS-EXPLAINED.md` - Domain configuration details

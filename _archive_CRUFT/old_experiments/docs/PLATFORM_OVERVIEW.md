# Soulfra Platform Overview

**Complete visibility into what's working at localhost:5001**

---

## 🎯 Quick Access

| What | URL | Status |
|------|-----|--------|
| **Homepage** | http://localhost:5001/ | ✅ 12 posts |
| **Status Dashboard** | http://localhost:5001/status | ✅ Live health check |
| **Reasoning Dashboard** | http://localhost:5001/reasoning | ✅ 8 threads |
| **ML Dashboard** | http://localhost:5001/ml | ✅ Python stdlib ML |
| **Admin Panel** | http://localhost:5001/admin | ✅ Create posts |
| **Automation Panel** | http://localhost:5001/admin/automation | ✅ Run tasks from web |
| **API Health** | http://localhost:5001/api/health | ✅ JSON endpoint |
| **Code Browser** | http://localhost:5001/code | ✅ View source |
| **Souls** | http://localhost:5001/souls | ✅ 6 souls |
| **Feedback** | http://localhost:5001/feedback | ✅ Public form |

---

## 📡 Working API Endpoints

All endpoints return JSON:

```bash
# Health check
curl http://localhost:5001/api/health

# List posts
curl http://localhost:5001/api/posts

# Get specific post
curl http://localhost:5001/api/posts/12

# List reasoning threads
curl http://localhost:5001/api/reasoning/threads

# Get thread with steps
curl http://localhost:5001/api/reasoning/threads/10

# Submit feedback
curl -X POST http://localhost:5001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "message": "Works!"}'
```

---

## 🧭 Navigation

**Main Nav:**
- Posts
- Souls
- **Reasoning** (NEW!)
- About
- Feedback
- Login/Signup

**Footer:**
- Subscribe
- **Status** (NEW!)
- **Code** (NEW!)
- Admin

---

## 📊 Platform Stats (Live)

- **Posts:** 12
- **Comments:** 32
- **Users:** 6
- **Reasoning Threads:** 8
- **Reasoning Steps:** (varies per thread)
- **Feedback:** 1+
- **Database Tables:** 19

---

## 🔍 What Each Dashboard Shows

### 1. Status Dashboard (/status)
- **Database Health:** Connected/Error status
- **Platform Stats:** Posts, comments, users, threads counts
- **Routes Inventory:** All routes with working/pending status
- **API Endpoints:** All 6 API routes with status
- **Recent Activity:** Last 5 posts, comments, feedback
- **Database Tables:** All 19 tables with row counts

### 2. Reasoning Dashboard (/reasoning)
- **Thread List:** All 8 AI reasoning threads
- **Stats:** Total threads, steps, active threads
- **Post Links:** Jump to post for each thread
- **API Links:** View thread JSON via API
- **How It Works:** Explanation of 4 AI personas

### 3. Automation Panel (/admin/automation)
- **Public Builder:** Run feedback → posts → reasoning
- **Newsletter Digest:** Generate weekly digest
- **Send Digest:** Email to subscribers
- **QR Stats:** View QR scan statistics
- **Reasoning Engine:** Link to reasoning dashboard

### 4. Admin Dashboard (/admin)
- **Create Posts:** Write and publish posts
- **Stats:** Posts, subscribers, feedback counts
- **Recent Feedback:** Last 10 feedback items
- **Publish Destinations:** Static site, email newsletter

---

## 🤖 AI Reasoning System

**4 AI Personas analyze every post:**

1. **CalRiven** - Technical architecture & synthesis
2. **TheAuditor** - Validation & integrity
3. **Soulfra** - Platform perspective & security
4. **DeathToData** - Privacy & critical questions

**How to view:**
- On any post page → Collapsible "AI Reasoning Process" section
- Reasoning dashboard → View all threads
- API → `/api/reasoning/threads` for JSON

---

## 🔧 Build-in-Public Automation

### Public Builder (public_builder.py)
**What it does:**
1. Checks feedback for high-priority items
2. CalRiven auto-creates posts
3. Reasoning engine analyzes
4. Updates feedback status

**Run it:**
- From web: `/admin/automation` → "Run Now"
- From CLI: `python3 public_builder.py`
- Via cron: `0 * * * * cd /path && python3 public_builder.py`

### Newsletter Digest (newsletter_digest.py)
**What it does:**
1. Groups feedback by theme
2. Analyzes AI consensus/disagreement
3. Generates decision questions
4. Creates HTML email digest

**Run it:**
- From web: `/admin/automation` → "Generate Preview"
- From CLI: `python3 newsletter_digest.py`
- Via cron: `0 20 * * 0 cd /path && python3 newsletter_digest.py`

---

## 🗄️ Database

**19 Tables:**
- Core: users, posts, comments
- AI: reasoning_threads, reasoning_steps
- Build-in-Public: feedback, qr_codes, qr_scans
- Souls: soul_history
- Newsletter: subscribers
- Content: categories, tags, post_categories, post_tags
- Other: messages, notifications, reputation, contribution_logs, url_shortcuts

**All tables viewable at:** http://localhost:5001/status (scroll to "Database Tables")

---

## 🎯 Common Tasks

### View a Post with AI Reasoning
```
1. Go to http://localhost:5001/
2. Click any post title
3. Scroll to "AI Reasoning Process"
4. Click "Show Reasoning Steps"
```

### Submit Public Feedback
```
1. Go to http://localhost:5001/feedback
2. Fill out form (no login required)
3. Submit
4. View in /admin dashboard
```

### Run Build-in-Public Automation
```
1. Go to http://localhost:5001/admin/automation
2. Login as admin
3. Click "Run Now" on Public Builder
4. See flash message with results
```

### Test API Endpoints
```bash
# Get all reasoning threads
curl http://localhost:5001/api/reasoning/threads | python3 -m json.tool

# Get specific post with comments & reasoning
curl http://localhost:5001/api/posts/12 | python3 -m json.tool
```

---

## ✅ What's Actually Working

**Unlike STATUS.md which lists features, here's what you can do RIGHT NOW:**

1. ✅ View 12 posts on homepage
2. ✅ Click any post to see full content
3. ✅ See 32 comments on posts
4. ✅ View AI reasoning on posts (collapsible)
5. ✅ Browse 6 souls at /souls
6. ✅ Submit feedback without login
7. ✅ Login as admin (username: admin, password: admin123)
8. ✅ Create new posts from admin panel
9. ✅ Run automation from web UI
10. ✅ View live platform stats at /status
11. ✅ Browse all reasoning threads at /reasoning
12. ✅ Access 6 API endpoints for JSON data
13. ✅ Browse source code at /code
14. ✅ Train ML models at /ml (Python stdlib only, no external ML libs)
15. ✅ Make predictions with Naive Bayes, KNN, Decision Tree classifiers

---

## 🧪 Quick Tests

### Test 1: Homepage Loads
```
Visit: http://localhost:5001/
Expected: List of 12 posts with titles
```

### Test 2: Reasoning Works
```
Visit: http://localhost:5001/post/feature-request-reasoning-engine
Scroll down, click "Show Reasoning Steps"
Expected: 4 AI analysis steps visible
```

### Test 3: Status Dashboard
```
Visit: http://localhost:5001/status
Expected: Green "Connected" database status, 19 tables listed
```

### Test 4: API Endpoints
```bash
curl http://localhost:5001/api/health
Expected: {"status": "healthy", "database": "connected"}
```

### Test 5: Automation Panel
```
Visit: http://localhost:5001/admin/automation
Login as admin
Expected: See "Public Builder", "Newsletter Digest" panels
```

---

## 📝 Key Documentation

- **STATUS.md** - Current state of all features
- **OSS_WORKFLOW.md** - Build-in-public workflow
- **AUTOMATION.md** - Cron job setup guide
- **ADMIN_AUTOMATION.md** - Web-based automation guide
- **VISION.md** - Platform philosophy
- **PLATFORM_OVERVIEW.md** - This file

---

## 🎬 Next Steps

1. **Set up SMTP** for email sending
2. **Generate QR codes** for posts
3. **Test automation** end-to-end
4. **Add more feedback** to test workflow
5. **Explore API** endpoints for integrations

---

## 💡 Philosophy

**Before:** Confusion about what's working, separate scripts, no visibility

**After:** Full transparency via dashboards, web-based automation, API access, clear documentation

**Result:** Platform that builds itself in public, with complete visibility into every component

---

**Platform URL:** http://localhost:5001

**Status Dashboard:** http://localhost:5001/status ← **Start here for live overview**

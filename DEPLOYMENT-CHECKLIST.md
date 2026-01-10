# ✅ Simple Deployment Checklist
**How to Publish a Blog Post to 9 Domains in 10 Minutes**

---

## 🚀 QUICK START (3 Steps)

### Step 1: Write Your Content (2 minutes)

```bash
# Open Studio in browser
open http://localhost:5001/studio
```

**Or manually:**
1. Open browser
2. Go to `localhost:5001/studio`
3. Write your title and content
4. Don't worry about formatting for different brands - Ollama handles that!

---

### Step 2: Click "✨ Magic Publish" (30 seconds)

1. Click the big purple button: **✨ Magic Publish**
2. Wait for confirmation message
3. You should see: "✅ Published to 9 domains!"

**Behind the scenes (automatic):**
- Ollama transforms content for each brand
- Saves to database
- Exports to HTML files
- Commits to GitHub
- Pushes to all 9 repos

---

### Step 3: Wait for GitHub Pages (5-10 minutes)

GitHub Pages automatically rebuilds your sites. Check progress:

```bash
# Check if published
curl http://soulfra.com | grep "YOUR_TITLE"
```

**Live URLs to check:**
- http://soulfra.com
- http://soulfra.github.io/calriven/
- http://soulfra.github.io/deathtodata/
- (Others once DNS configured)

---

## 🎯 THAT'S IT!

**Total Time:** ~10 minutes (2 min writing + 30 sec publish + 7 min deploy)

Your content is now live on 9 different domains with 9 different brand voices!

---

## 📊 DETAILED WORKFLOW

For those who want to understand what's happening:

### 1. Content Creation Phase

**Input:**
- Title: "How to Secure Your Digital Identity"
- Content: Your article (markdown supported)

**Location:** Studio UI at `localhost:5001/studio`

---

### 2. Transformation Phase (Automatic)

Ollama creates 9 brand-specific versions:

| Domain | Brand Voice | Example Transformation |
|--------|-------------|----------------------|
| soulfra.com | Tech thought leader | "Digital sovereignty is your fundamental right" |
| calriven.com | Sysadmin practical | "Here's how to lock down your SSH keys" |
| deathtodata.com | Privacy advocate | "Corporations are harvesting your identity data" |
| mascotrooms.com | Business casual | "Protect your brand's digital presence" |
| dealordelete.com | Entrepreneurial | "Security is a dealbreaker for investors" |
| shiprekt.com | Gaming community | "Don't get rekt - secure your game accounts" |
| sellthismvp.com | Startup hustle | "Security sells: why investors care about identity" |
| saveorsink.com | Business triage | "Is your identity security sinking your business?" |
| finishthisrepo.com | Developer | "Git security: protecting your identity in code" |

**Time:** ~30 seconds (Ollama processing)

---

### 3. Database Save Phase (Automatic)

```sql
INSERT INTO posts (user_id, title, slug, content, brand_id, published_at)
VALUES (1, 'transformed_title', 'slug', 'transformed_content', brand_id, NOW());
```

**Result:** 9 new rows in `posts` table

---

### 4. HTML Export Phase (Automatic)

For each brand:
```bash
/github-repos/soulfra/post/how-to-secure-your-digital-identity.html
/github-repos/calriven/post/how-to-secure-your-digital-identity.html
... (9 files total)
```

**Also updates:**
- `index.html` (homepage with latest post)
- `feed.xml` (RSS feed)
- `about.html` (if needed)

---

### 5. Git Commit Phase (Automatic)

```bash
cd /github-repos/soulfra
git add .
git commit -m "Magic Publish: How to Secure Your Digital Identity"
git push origin main
```

**Repeats for all 9 repos**

---

### 6. GitHub Pages Deploy Phase (Automatic)

GitHub Pages detects the push and rebuilds the site:

```
GitHub Actions:
  - Detects commit
  - Builds static site
  - Deploys to CDN
  - Updates soulfra.com

Time: 5-10 minutes
```

---

## 🧪 VERIFICATION CHECKLIST

After publishing, verify it worked:

### ✅ Check 1: Database Updated

```bash
sqlite3 soulfra.db "SELECT title, brand_id FROM posts ORDER BY id DESC LIMIT 9;"
```

**Should show:** 9 new rows with your title

---

### ✅ Check 2: HTML Files Created

```bash
ls -la /Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra/post/
```

**Should show:** New `.html` file with your slug

---

### ✅ Check 3: Git Committed

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra
git log -1
```

**Should show:** Latest commit with "Magic Publish: YOUR_TITLE"

---

### ✅ Check 4: Live on Website

```bash
curl http://soulfra.com | grep -i "YOUR_TITLE"
```

**Should show:** Your title in HTML

**Or visit in browser:** http://soulfra.com

---

## 🚨 TROUBLESHOOTING

### Issue 1: "Ollama not running"

**Error:** `Connection refused to localhost:11434`

**Fix:**
```bash
# Start Ollama
ollama serve

# Or install if not present
brew install ollama
ollama pull soulfra-model
```

---

### Issue 2: "Database locked"

**Error:** `database is locked`

**Fix:**
```bash
# Kill any processes using the database
lsof soulfra.db
kill -9 PID_FROM_ABOVE

# Restart Flask app
python3 app.py
```

---

### Issue 3: "Git push failed"

**Error:** `Permission denied (publickey)`

**Fix:**
```bash
# Check GitHub authentication
cd /Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra
git remote -v

# Should show: https://github.com/Soulfra/soulfra.git
# If SSH (git@github.com), you need SSH keys

# Switch to HTTPS:
git remote set-url origin https://github.com/Soulfra/soulfra.git
```

---

### Issue 4: "GitHub Pages not updating"

**Cause:** Build failed or still in progress

**Fix:**

1. **Check GitHub Actions:**
   - Go to: https://github.com/Soulfra/soulfra/actions
   - Look for latest workflow run
   - If failed, click for error details

2. **Force rebuild:**
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra
   git commit --allow-empty -m "Trigger rebuild"
   git push
   ```

3. **Wait longer:**
   - GitHub Pages can take up to 10-15 minutes
   - Check again in 5 minutes

---

### Issue 5: "Content not transforming correctly"

**Problem:** All domains showing same content

**Possible Causes:**
- Ollama models not loaded
- ContentTransformer not configured

**Fix:**
```bash
# Check Ollama models
ollama list

# Should show:
# soulfra-model:latest
# calriven-model:latest
# (etc for all 9 brands)

# If missing, pull them:
ollama pull soulfra-model
ollama pull calriven-model
# ... etc
```

---

## 📅 PUBLISHING SCHEDULE RECOMMENDATIONS

### Daily Publishing
- **Best for:** Building SEO, growing audience
- **Time:** 30 minutes per day
- **Result:** 30+ posts per month across 9 domains (270 total pieces of content!)

### Weekly Publishing
- **Best for:** Maintaining presence, less time commitment
- **Time:** 2 hours per week
- **Result:** 4 posts per month across 9 domains (36 total pieces)

### Batch Publishing
- **Best for:** Content sprints
- **Strategy:** Write 10 posts in one day, schedule throughout month
- **Tools:** Could add scheduled publishing feature

---

## 🎯 OPTIMIZATION TIPS

### Tip 1: Write Once, Reach 9 Audiences

Don't write 9 different posts - write ONE good post and let Ollama adapt it for each brand.

**Example:**
- **Your Input:** "5 Security Tips for Online Privacy"
- **Soulfra Output:** "Your Digital Identity: 5 Essential Security Principles"
- **CalRiven Output:** "Sysadmin Checklist: 5 Security Configs You're Probably Missing"
- **DeathToData Output:** "5 Ways Corporations Track You (And How to Stop Them)"

---

### Tip 2: Use Markdown for Rich Formatting

```markdown
# Heading 1
## Heading 2

**Bold text**
*Italic text*

- Bullet point
- Another point

[Link](https://example.com)

`code snippet`
```

Ollama preserves formatting across all transformations.

---

### Tip 3: Include Images (Future Feature)

Currently text-only, but you can add:
```html
<img src="/images/my-diagram.png" alt="Security diagram">
```

**Roadmap:** Drag-and-drop image upload coming soon

---

### Tip 4: SEO-Friendly Titles

Good titles:
- "How to Secure Your SSH Keys in 2026"
- "Why Digital Identity Matters for Startups"
- "5 Privacy Tools Every Developer Should Use"

Bad titles:
- "Thoughts"
- "Untitled"
- "Test Post #47"

---

## 📈 CONTENT ANALYTICS (Future)

**Coming Soon:** Track performance across all domains

- Page views per domain
- Top-performing content
- Best-converting brand voices
- Audience demographics

**For now:** Use GitHub Pages built-in analytics (if enabled)

---

## ✅ PRE-PUBLISH CHECKLIST

Before hitting "Magic Publish":

- [ ] Title is clear and SEO-friendly
- [ ] Content is proofread (spell check)
- [ ] Links work (if any)
- [ ] Code examples tested (if applicable)
- [ ] Ollama is running (`ollama list`)
- [ ] Flask app is running (`lsof -i :5001`)
- [ ] You're ready for it to go LIVE (no drafts mode yet)

---

## 📞 QUICK REFERENCE

### Essential Commands

```bash
# Start Flask app
python3 app.py

# Check if running
curl http://localhost:5001/studio

# Start Ollama
ollama serve

# Check database
sqlite3 soulfra.db "SELECT COUNT(*) FROM posts;"

# Check live site
curl http://soulfra.com
```

### Essential URLs

- **Studio:** http://localhost:5001/studio
- **Admin:** http://localhost:5001/admin
- **API:** http://localhost:5001/api/domains/list
- **Live Site:** http://soulfra.com

### Essential Files

- **Database:** `soulfra.db`
- **Config:** `app.py`
- **Transformer:** `content_transformer.py`
- **Domains:** `domains-master.csv`

---

## 🎓 LEARNING PATH

### Week 1: Basic Publishing
- Publish 1-2 test posts
- Verify they appear on soulfra.com
- Get comfortable with Studio UI

### Week 2: Multi-Domain
- Configure DNS for other domains
- Test publishing to all 9
- Compare brand voice transformations

### Week 3: Advanced Features
- Schedule posts (if feature added)
- Add images (if feature added)
- Integrate analytics

---

## 🚀 READY TO PUBLISH?

**Your 30-second workflow:**

1. Open http://localhost:5001/studio
2. Write title + content
3. Click "✨ Magic Publish"
4. Wait 10 minutes
5. Check http://soulfra.com

**That's it!** You're publishing to 9 domains with 9 different brand voices.

---

**Generated:** 2026-01-02
**System Status:** ✅ Ready to publish
**Next Post Publishes To:** 9 domains automatically

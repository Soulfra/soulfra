# 📁 Folder Structure Explained

> **Your Confusion**: "when i generated a post earlier on the soulfra.com folder not the soulfra folder"

**NEWS FLASH: There is NO "soulfra.com" folder!**

Let me explain exactly what exists and where everything goes.

---

## 🎯 The Actual Folder Structure

```
soulfra-simple/
├── brands/
│   ├── soulfra/         ← Brand configuration (colors, tagline)
│   ├── calriven/
│   └── deathtodata/
│
├── output/
│   ├── soulfra/         ← Static HTML for GitHub Pages ⭐
│   │   ├── .git/        ← Git repo (Soulfra/soulfra)
│   │   ├── index.html   ← Homepage
│   │   ├── post/        ← Blog posts
│   │   ├── feed.xml     ← RSS feed
│   │   ├── CNAME        ← Contains "soulfra.com" (just text!)
│   │   └── README.md
│   ├── calriven/        ← Static HTML for calriven
│   ├── deathtodata/     ← Static HTML for deathtodata
│   └── howtocookathome/
│
├── app.py               ← Flask server (localhost:5001)
├── soulfra.db           ← Database (posts, brands, users)
├── domains.txt          ← List of your domains
└── brand_domains.json   ← Domain mappings
```

---

##❌ What DOESN'T Exist

```
❌ No "soulfra.com" folder
❌ No "soulfra.com" directory
❌ No "soulfra.com" anything
```

**The domain name "soulfra.com" only exists as:**
1. Text inside `output/soulfra/CNAME` file
2. Text in `brand_domains.json`
3. DNS records at your domain registrar

---

## 🔄 The Complete Flow (Where Posts Actually Go)

### Step 1: Create Post in Database

```
You: Click "Create Post" in Template Browser
     ↓
Flask app (localhost:5001)
     ↓
SQLite database (soulfra.db)
     ├── brands table (id, name, slug, colors)
     └── posts table (id, title, slug, content, brand_id)
```

**Location**: `soulfra.db` (the database file)
**NOT in any "folder"** - it's in the database!

---

### Step 2: Export to Static Files

```bash
# You run this command:
python3 export_static.py --brand soulfra

# What it does:
1. Reads posts from soulfra.db
2. Renders HTML templates
3. Writes files to output/soulfra/

# Result:
output/soulfra/
├── index.html        ← Generated from database posts
├── post/
│   ├── my-post-1735678900.html
│   └── another-post-1735678901.html
├── feed.xml
└── CNAME             ← Contains "soulfra.com"
```

**Location**: `output/soulfra/` (static HTML files)
**NOT "soulfra.com"** - it's `output/soulfra/`!

---

### Step 3: Deploy to GitHub

```bash
# You run this command:
python3 deploy_github.py --brand soulfra

# What it does:
cd output/soulfra/
git add .
git commit -m "Update"
git push

# Pushes to GitHub repo:
github.com/Soulfra/soulfra

# GitHub Pages serves it at:
soulfra.github.io/soulfra/
```

**Location**: GitHub repo `Soulfra/soulfra`
**Then**: GitHub Pages hosts it
**URL**: `https://soulfra.github.io/soulfra/`

---

### Step 4: Custom Domain (After DNS)

```
# After you configure DNS:
DNS: soulfra.com → 185.199.108.153 (GitHub Pages IP)

# GitHub reads CNAME file:
output/soulfra/CNAME contains "soulfra.com"

# GitHub serves site at both URLs:
✅ soulfra.github.io/soulfra/  (always works)
✅ soulfra.com                  (after DNS configured)
```

**The domain "soulfra.com" is just a DNS record pointing to GitHub Pages.**

It's NOT a folder. It's NOT a directory. It's just text in the CNAME file!

---

## 📂 Why the Confusion?

### What You Probably Saw:

```
# When creating a post, you might have seen:
"Saving to brand: soulfra"

# And thought it was saving to:
"soulfra.com" folder  ← WRONG!

# But it's actually saving to:
Database → soulfra.db
Then later exported to → output/soulfra/
```

### The Truth:

```
Database (soulfra.db)
├── Brand: soulfra (brand_id=1)
├── Post 1: "My Post" (brand_id=1, slug="my-post-1735678900")
└── Post 2: "Another" (brand_id=1, slug="another-post-1735678901")

When exported:
output/soulfra/
├── post/my-post-1735678900.html
└── post/another-post-1735678901.html
```

---

## 🎨 Where Each Brand Lives

### Brand Configuration
```
brands/soulfra/
├── ai_persona.txt     ← AI personality
├── colors.json        ← Brand colors
└── config.json        ← Settings
```

**This is just config files. NOT where posts go!**

---

### Brand Posts (Database)
```sql
SELECT * FROM posts WHERE brand_id = 1;
-- Returns all soulfra posts

SELECT * FROM posts WHERE brand_id = 2;
-- Returns all calriven posts
```

**Posts live in the database, tagged with brand_id.**

---

### Brand Static Site (After Export)
```
output/soulfra/        ← Soulfra static site
├── index.html
├── post/
└── CNAME (soulfra.com)

output/calriven/       ← Calriven static site
├── index.html
├── post/
└── CNAME (calriven.com)

output/deathtodata/    ← DeathToData static site
├── index.html
├── post/
└── CNAME (deathtodata.com)
```

**Each brand gets its own output folder.**

---

## 🤔 Common Questions

### Q: "Where did my post go?"
**A**: Check in order:
1. Database: `sqlite3 soulfra.db "SELECT title FROM posts WHERE brand_id=1;"`
2. Static files: `ls output/soulfra/post/`
3. GitHub repo: `https://github.com/Soulfra/soulfra`
4. Live site: `https://soulfra.github.io/soulfra/`

### Q: "I created a post but don't see it on the site"
**A**: You need to export it first!
```bash
python3 export_static.py --brand soulfra
python3 deploy_github.py --brand soulfra
```

### Q: "Where is the soulfra.com folder?"
**A**: **IT DOESN'T EXIST!** The folder is `output/soulfra/`. The CNAME file inside it contains the text "soulfra.com".

### Q: "How do I edit soulfra.com content?"
**A**:
```bash
# Option 1: Edit in database
1. Edit post in Flask app (localhost:5001)
2. Export: python3 export_static.py --brand soulfra
3. Deploy: python3 deploy_github.py --brand soulfra

# Option 2: Edit static files directly (not recommended)
1. Edit files in output/soulfra/
2. Git commit & push
```

---

## ✅ The Simple Truth

```
Database (soulfra.db)
     ↓ (export_static.py)
Static Files (output/soulfra/)
     ↓ (deploy_github.py)
GitHub Repo (Soulfra/soulfra)
     ↓ (GitHub Pages)
Live Site (soulfra.github.io/soulfra/)
     ↓ (DNS + CNAME)
Custom Domain (soulfra.com)
```

**There is NO "soulfra.com" folder anywhere in this chain!**

The domain is just:
- Text in a CNAME file
- A DNS record at your registrar

---

## 📊 Visual Map

```
YOUR COMPUTER
├── soulfra-simple/
│   ├── app.py (Flask app)
│   ├── soulfra.db (Database)
│   │   └── posts for all brands
│   ├── brands/soulfra/ (Config)
│   └── output/soulfra/ (Static HTML)
│       └── CNAME → "soulfra.com" (just text!)
│
GITHUB
├── Soulfra/soulfra repo
│   ├── index.html
│   ├── post/*.html
│   └── CNAME (soulfra.com)
│
GITHUB PAGES
├── soulfra.github.io/soulfra/ (hosted site)
│
DNS REGISTRAR
├── soulfra.com → 185.199.108.153
│   └── Points to GitHub Pages
│
INTERNET
└── Users visit soulfra.com
    └── GitHub serves content from github.io
```

---

## 🎯 Summary

**Your question**: "when i generated a post earlier on the soulfra.com folder"

**Answer**:
1. There is NO "soulfra.com" folder
2. You generated a post to the **database** (soulfra.db)
3. It will be exported to `output/soulfra/` when you run `export_static.py`
4. It will be deployed to GitHub repo `Soulfra/soulfra`
5. It will be live at `soulfra.github.io/soulfra/`
6. It will ALSO be accessible at `soulfra.com` (after DNS is configured)

**"soulfra.com" is a domain name, not a folder!**

---

**Read this until it clicks. The confusion ends here!** 🎉

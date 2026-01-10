# CSV Import - Quick Start Guide

**Created:** December 31, 2024
**Status:** ✅ WORKING NOW!

---

## 🎯 What This Is

**Problem:** You have 50-200 domains in a CSV file or spreadsheet. Ollama import takes 1-3 hours.

**Solution:** CSV import = **30 seconds** to import all domains using your existing templates!

---

## 🚀 Try It Right Now

### Step 1: Visit CSV Import Page

```
Studio → Domains → Click "📄 Import from CSV"
```

OR directly:
```
http://localhost:5001/admin/domains/csv
```

---

### Step 2: Prepare Your CSV

Your `domains-master.csv` is already formatted correctly!

**CSV Format:**
```csv
name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed
MyCookingBlog,mycookingblog.com,cooking,creative,🍳,blog,"Quick recipes",Home cooks,"Share recipes",false,false
TechStartup,techstartup.io,tech,business,💻,platform,"Startup tools",Entrepreneurs,"Business solutions",false,false
```

**Columns:**
1. **name** - Brand name (e.g., "My Cooking Blog")
2. **domain** - Full domain (e.g., "mycookingblog.com")
3. **category** - cooking, tech, privacy, business, health, art, education, gaming, finance, local
4. **tier** - foundation, business, creative
5. **emoji** - One emoji (🍳, 💻, 🔒, etc.)
6. **brand_type** - blog, game, community, platform, directory
7. **tagline** - Short description
8. **target_audience** - Who visits this site?
9. **purpose** - What does this site do?
10. **ssl_enabled** - true/false
11. **deployed** - true/false

---

### Step 3: Paste CSV Data

1. Open your CSV file (domains-master.csv)
2. Copy ALL contents (including header row)
3. Paste into the text area
4. Click **"📋 Parse & Preview"**

You'll see a table showing all your domains parsed and ready to import!

---

### Step 4: Review & Import

**Preview shows:**
- ✅ Emoji column
- ✅ Name, domain, category
- ✅ Tier (foundation/business/creative)
- ✅ Brand type and tagline

**Click:** "✅ Import All Domains"

**Done!** All domains imported in seconds.

---

## ✨ Example: Import 50 Cooking Domains

### Your CSV:
```csv
name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed
PastaRecipes,pastarecipes.com,cooking,creative,🍝,blog,"Perfect pasta every time",Home cooks,"Pasta tutorials",false,false
QuickMeals,quickmeals.net,cooking,creative,⚡,blog,"30-minute meals",Busy parents,"Fast recipes",false,false
BakingTips,bakingtips.io,cooking,creative,🍰,blog,"Baking made easy",Home bakers,"Baking tutorials",false,false
... (47 more)
```

### Steps:
1. Copy all 50 lines
2. Visit: `http://localhost:5001/admin/domains/csv`
3. Paste → Parse → Review
4. Click Import
5. **50 domains imported in 30 seconds!**

---

## 🎯 CSV vs Ollama Import

| Feature | CSV Import | Ollama Import |
|---------|-----------|---------------|
| **Speed** | 30 seconds | 1-3 hours |
| **Data Source** | Your CSV | AI analysis |
| **Accuracy** | Uses your data | AI suggestions |
| **Best For** | 50-200 domains | 1-10 domains |
| **Requirements** | CSV file ready | Just domain names |

**Recommendation:**
- **Have CSV?** → Use CSV import
- **Need AI help?** → Use Ollama import

---

## 📊 Your Current Setup

**You have:**
- `domains-master.csv` with template
- 4 example domains already formatted
- All columns defined

**Next step:**
1. Add your 200 domains to domains-master.csv
2. Copy file contents
3. Import!

---

## 💡 Tips

### Batch Import (50 at a time)

**Why?** Test in batches to catch errors early.

**How:**
1. Copy first 50 lines from CSV
2. Import → verify in /admin/domains
3. Copy next 50 lines
4. Repeat

### Missing Data?

If CSV row is incomplete:
- **No name?** → Uses domain name (e.g., "mycookingblog.com" → "Mycookingblog")
- **No category?** → Defaults to "tech"
- **No emoji?** → Defaults to 🌐
- **No tier?** → Defaults to "creative"

Still imports successfully!

### Duplicate Domains?

If domain already exists:
- Slug gets number appended
- First: `mycookingblog`
- Duplicate: `mycookingblog-1`

---

## 🔧 Advanced: Template Matching (Coming Next!)

**Future enhancement:**

When you import domains without full data, system will:
1. Look at domain name
2. Match to existing templates
3. Auto-fill category, emoji, tier

**Example:**
```
Input: "quickcooking.com" (just domain, no category)
Match: "howtocookathome.com" (existing cooking domain)
Auto-fill: category=cooking, emoji=🍳, tier=creative
```

**For now:** Fill out your CSV completely to get best results!

---

## ❓ FAQ

### Q: Can I import without header row?
**A:** Yes! System detects if first line is header and skips it.

### Q: Can I use Excel/Google Sheets?
**A:** Yes! Export as CSV, then paste contents into form.

### Q: What if I only have domain names?
**A:** Use "Import with Ollama" instead - it analyzes each domain.

### Q: Can I edit after import?
**A:** Yes! Go to /admin/domains, click "Edit" on any domain.

### Q: How do I add more fields?
**A:** Edit domains after import, or update your CSV and re-import.

---

## 📄 Files

**Input:**
- `domains-master.csv` - Your domain list

**Output:**
- Database: `soulfra.db` (brands table)
- View: `http://localhost:5001/admin/domains`

**Templates:**
- `templates/csv_import.html` - CSV import form
- `/api/domains/import-csv` - Backend endpoint

---

## 🎉 Bottom Line

**Before:** Manually add 200 domains one-by-one, or wait 3 hours for Ollama

**After:** Paste CSV → Import → **Done in 30 seconds!**

---

## 🚀 Try It Now!

```bash
# 1. Visit CSV import page
open http://localhost:5001/admin/domains/csv

# 2. Open your CSV
open domains-master.csv

# 3. Copy all contents, paste into form

# 4. Click Parse → Review → Import

# 5. Check results
open http://localhost:5001/admin/domains
```

**That's it! Simple and fast!**

---

## 📋 CSV Template

Save this as your starting point:

```csv
name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed
Soulfra,soulfra.com,tech,foundation,🌟,platform,"AI-powered development platform","Developers, tech enthusiasts","Central control hub for managing 200+ domains",true,true
HowToCookAtHome,howtocookathome.com,cooking,creative,👨‍🍳,blog,"Simple recipes for home cooks","Parents age 25-45","Quick 30-minute meal recipes",false,false
DeathToData,deathtodata.com,privacy,foundation,💀,blog,"Privacy-first data protection","Privacy advocates, tech users","Anti-tracking and data minimization",false,false
Calriven,calriven.com,tech,foundation,🔧,blog,"Technical excellence and code quality","Software engineers","System architecture and best practices",false,false
```

Add your domains below these examples!

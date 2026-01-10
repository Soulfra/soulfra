# Domain Files - What They Are and What to Delete

## TL;DR - The Mess

You had **3 different file formats** for domains, plus **250 fake test domains** that were never imported. This caused massive confusion about which file was "master".

## What Just Got Fixed

✅ Deleted `test-domains-200.csv` (200 fake domains)
✅ Deleted `test-domains-50.csv` (50 fake domains)
✅ Database is now source of truth (not CSV files)

## Your Real Domains (9 Total)

**All stored in:** `soulfra.db` → `brands` table

1. **soulfra.com** - Hub (Identity & Security) - Blue/Green/Red
2. **cringeproof.com** - Community (Zero Performance Anxiety) - Pink/Purple/Black
3. **deathtodata.com** - Privacy Search - Red/Orange
4. **calriven.com** - AI Platform - Purple/Blue
5. **howtocookathome.com** - Cooking - Orange/Red
6. **stpetepros.com** - Home Services (Tampa Bay) - No colors set
7. **hollowtown.com** - Gaming - Brown/Orange
8. **oofbox.com** - Gaming - Brown/Orange
9. **niceleak.com** - Gaming - Dark/Pink

## Files You Have Now

### ✅ Keep These

**1. soulfra.db** - Master database (source of truth)
- Contains all 9 domains
- Has full metadata (colors, taglines, categories)
- Updated via web UI at `localhost:5001/admin/domains`

**2. my-real-domains.csv** - Clean export (just created)
- Backup of your 9 real domains
- Auto-generated from database
- JSON format with all metadata

**3. domains.json** - Public manifest (auto-generated)
- Same as my-real-domains.csv
- Used by deployment system
- Safe to delete (regenerates automatically)

**4. deployed-domains/** - Output folder
- Contains deployed sites
- `cringeproof/` - ✅ Already deployed (41 files)
- 8 more domains ready to deploy

### ❌ Old Files (Can Delete)

**test-domains-200.csv** - ✅ DELETED (200 fake domains)
**test-domains-50.csv** - ✅ DELETED (50 fake domains)

**domains-master.csv** - Template with 4 examples (DELETE if you want)
**domains-simple.txt** - Old format (7 domains) (KEEP if you want simple import)
**domains.txt** - Old pipe-separated format (DELETE)
**domains-example.csv** - Example file (DELETE)

## Workflow Going Forward

### Add New Domain

**Option 1: Web UI (Recommended)**
```
1. Go to http://localhost:5001/admin/domains
2. Enter domain in "Quick Add" form
3. Ollama suggests category/tagline/colors
4. Click Save → Stored in database
```

**Option 2: Simple Text File**
```
1. Add domain to domains-simple.txt (just the domain name)
2. Import via web UI
3. Ollama fills in the rest
```

**Option 3: Full CSV Import**
```
1. Create CSV with format:
   name,domain,category,tier,emoji,brand_type,tagline
2. Upload via web UI CSV import
```

### Deploy Domain

**After adding to database:**
```bash
python3 domain_deployer.py <slug>
```

Or use web UI:
```
1. Go to http://localhost:5001/admin/domains
2. Click "🚀 Deploy" button
```

### Export Backup

**Any time:**
```bash
python3 domain-manager.py export my-domains-backup.json
```

## Why This Was Confusing

**Before:**
- ❌ 3 different CSV formats (domains.txt, domains-simple.txt, domains-master.csv)
- ❌ 250 test domains mixed with 9 real ones
- ❌ Unclear which file was "source of truth"
- ❌ Manual CSV editing required

**Now:**
- ✅ Database is master (soulfra.db)
- ✅ Web UI for all changes
- ✅ CSV export for backups only
- ✅ No test data pollution

## Database Schema

Your `brands` table has 20+ columns but you only need to care about:

**Essential:**
- name, slug, domain, category
- color_primary, color_secondary, color_accent
- tagline, emoji, brand_type

**Optional:**
- tier (foundation/business/creative)
- network_role (hub/member)
- verified (0 or 1)
- target_audience, purpose

**Auto-generated:**
- id, created_at, verification_token

## File Formats Explained

### Format 1: domains-master.csv (11 columns)
```csv
name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed
Soulfra,soulfra.com,tech,foundation,🌟,platform,"AI platform","Developers","Control hub",true,true
```

### Format 2: domains-simple.txt (1 column)
```
soulfra.com
cringeproof.com
deathtodata.com
```

### Format 3: domains.txt (pipe-separated)
```
soulfra.com | tech | AI-powered platform
cringeproof.com | social | Zero Performance Anxiety
```

### Format 4: Database Export (JSON)
```json
{
  "domains": [{
    "slug": "soulfra",
    "name": "Soulfra",
    "domain": "soulfra.com",
    "theme": {"primary": "#3498db"}
  }]
}
```

## Recommendation

**Delete these old files:**
```bash
rm domains.txt
rm domains-example.csv
rm domains-master.csv  # Unless you want the template
```

**Keep only:**
- `soulfra.db` - Master database
- `my-real-domains.csv` - Your current backup
- `domains-simple.txt` - For quick bulk adds (optional)

**Use this workflow:**
1. Add domains via web UI
2. Database stores everything
3. Export to JSON when you need backups
4. Deploy via CLI or web UI

No more CSV confusion!

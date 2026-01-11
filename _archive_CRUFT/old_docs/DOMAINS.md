# Domain Confusion (soulfra.com vs soulfra.github.io)

**You saw duplicates on soulfra.com/stpetepros/ but we're updating soulfra.github.io/stpetepros/**

Here's what's happening:

---

## The Two Domains

### soulfra.github.io (What We're Updating)
- **What:** GitHub Pages (free hosting)
- **Content:** Fresh export from database (16 professionals, no duplicates)
- **Updated:** Just now (we removed duplicates + re-exported)
- **URL:** https://soulfra.github.io/stpetepros/

### soulfra.com (Your Custom Domain)
- **What:** Custom domain pointing somewhere else
- **Content:** OLD version (may have duplicates, old data)
- **Updated:** Unknown (not connected to what we're doing)
- **URL:** https://soulfra.com/stpetepros/

---

## Why They're Different

**GitHub Pages (soulfra.github.io):**
- Auto-deploys when you `git push`
- We just updated this (removed duplicates)
- Fresh, clean, 16 professionals

**Custom Domain (soulfra.com):**
- Points to Flask server or old deployment
- NOT updated by our tools
- May show old data

---

## How to Fix

### Option 1: Point soulfra.com to GitHub Pages

**Make soulfra.com show the SAME content as soulfra.github.io:**

1. Add CNAME file to GitHub Pages:
```bash
echo "soulfra.com" > ~/Desktop/soulfra.github.io/CNAME
git add CNAME
git commit -m "Point custom domain to GitHub Pages"
git push
```

2. Update DNS (at your domain registrar):
```
Type: CNAME
Name: www
Value: soulfra.github.io
```

**Then soulfra.com/stpetepros/ = soulfra.github.io/stpetepros/ (same content)**

### Option 2: Use Only GitHub Pages

**Just use soulfra.github.io/stpetepros/ and ignore soulfra.com/stpetepros/**

Simpler. No DNS config needed.

---

## Current Status

**Working NOW:**
- ✅ https://soulfra.github.io/stpetepros/ (16 professionals, no duplicates)

**May have old data:**
- ⚠️  https://soulfra.com/stpetepros/ (might show duplicates)

---

## Recommendation

**Use GitHub Pages URL for now:**
https://soulfra.github.io/stpetepros/

**Fix custom domain later** (after you get first customers and prove the model).

---

## What Just Got Fixed

1. ✅ Removed duplicates from database (25 → 16)
2. ✅ Re-exported to clean HTML
3. ✅ Fixed bash script (no more file listing spam)
4. ✅ Created simple status command

**GitHub Pages is clean now. Custom domain may still show old stuff.**

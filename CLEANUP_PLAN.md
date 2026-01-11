# 🔥 Nuclear Cleanup Plan

**Status:** READY TO EXECUTE
**Time:** ~10 minutes
**Reversible:** Yes (everything goes to `_archive_CRUFT/`)

---

## What's Happening:

### Before:
```
51 folders
34 Python files in root
218 files related to QR codes
100+ markdown files
```

### After:
```
4 folders (soulfra-simple, output, templates, _archive_CRUFT)
3 Python files in root (app.py, database.py, payment.py)
1 QR payment system
Clean, focused, deployable
```

---

## Files To KEEP:

### Root Python Files (Keep Only 3):
- ✅ `app.py` - Flask server
- ✅ `database.py` - SQLite helpers
- ✅ `stpetepros_simple_payment.py` → Rename to `payment.py`

### Folders (Keep Only 3):
- ✅ `output/soulfra/` - Deployed site (GitHub Pages)
- ✅ `templates/` - HTML templates
- ✅ `venv/` - Python environment

### Everything Else (Move to Archive):
- 🗑️ All other *.py files → `_archive_CRUFT/old_scripts/`
- 🗑️ `_archive/` folder → `_archive_CRUFT/old_archive/`
- 🗑️ `archive/` folder → `_archive_CRUFT/old_experiments/`
- 🗑️ `core/` folder → `_archive_CRUFT/old_core/`
- 🗑️ `api-backend/` folder → `_archive_CRUFT/old_api/`
- 🗑️ All *.md files (except README.md) → `_archive_CRUFT/old_docs/`

---

## Execution Order:

1. ✅ Create `_archive_CRUFT/` folder
2. Move Python files (keep 3)
3. Move duplicate folders
4. Move markdown files
5. Rename `stpetepros_simple_payment.py` → `payment.py`
6. Verify `output/soulfra/` untouched
7. Test Flask server still works

---

## Safety Net:

**Everything is recoverable!** All files go to `_archive_CRUFT/` - nothing is deleted.

**To undo:**
```bash
# If something breaks, restore everything:
mv _archive_CRUFT/old_scripts/*.py .
mv _archive_CRUFT/old_core core
# etc.
```

---

## New Structure:

```
soulfra-simple/
├── app.py                     # Flask server (ONLY ONE!)
├── database.py                # SQLite helpers
├── payment.py                 # Stripe integration
├── qr-pay.py                  # NEW: QR → payment flow
├── .github/
│   └── workflows/
│       └── auto-deploy.yml    # NEW: Auto-deploy from phone
├── output/
│   └── soulfra/               # Deployed site (untouched)
├── templates/                 # HTML templates (untouched)
├── venv/                      # Python env (untouched)
└── _archive_CRUFT/            # Everything else
    ├── old_scripts/           # 31 old Python files
    ├── old_archive/           # Old _archive folder
    ├── old_experiments/       # Old archive folder
    ├── old_core/              # Old core folder
    ├── old_api/               # Old api-backend folder
    └── old_docs/              # 100+ old markdown files
```

---

## Next Steps After Cleanup:

1. Create `qr-pay.py` - Simple QR → payment system
2. Create GitHub Actions auto-deploy
3. Test on soulfra.com
4. Deploy from iPhone

---

**Ready?** Run the cleanup scripts below.

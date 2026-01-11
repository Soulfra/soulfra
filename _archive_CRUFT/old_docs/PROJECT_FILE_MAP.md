# 📁 Project File Map - Where Everything Goes

## The Problem

You have **50+ top-level directories**. This is confusing!

**Your question:** "what's on which portion or folder or depth chart or whatever else? like everyone does max depth 3"

**This guide shows you EXACTLY where everything is and where it SHOULD go.**

## Max Depth 3 Rule

Most well-organized projects use **max depth 3**:

```
project/               ← Root (depth 0)
├── core/              ← Depth 1
│   ├── routing/       ← Depth 2
│   │   └── utils.py   ← Depth 3 (STOP HERE!)
```

**Why depth 3?**
- Easy to navigate
- Easy to find files
- Not too nested
- Clear organization

## Current Structure (BEFORE Cleanup)

```
soulfra-simple/
├── 50+ DIRECTORIES AT ROOT (TOO MANY!)
├── Scattered test files everywhere
├── Local dev scripts mixed with production code
└── Hard to find anything
```

## Proposed Structure (AFTER Cleanup)

```
soulfra-simple/                    ← Root
│
├── app.py                         ← Main Flask app
├── database.py                    ← Database utilities
├── soulfra.db                     ← SQLite database
│
├── core/                          ← Core functionality (depth 1)
│   ├── subdomain_router.py        ← Domain routing
│   ├── tier_progression_engine.py ← Unlock system
│   ├── email_sender.py            ← Email utilities
│   └── [other core modules]
│
├── templates/                     ← HTML templates (depth 1)
│   ├── index.html
│   ├── admin/                     ← Depth 2
│   │   ├── dashboard.html
│   │   └── admin_base.html
│   └── blog/                      ← Depth 2
│       └── post.html
│
├── static/                        ← Static files (depth 1)
│   ├── css/                       ← Depth 2
│   ├── js/                        ← Depth 2
│   └── images/                    ← Depth 2
│
├── tests/                         ← ALL test files go here (depth 1)
│   ├── test_domains.py
│   ├── test_email.py
│   └── test_routing.py
│
├── local/                         ← Local dev scripts (depth 1)
│   ├── setup_local_domains.sh
│   ├── start_localhost_test.sh
│   └── local_domain_tester.py
│
├── docs/                          ← Documentation (depth 1)
│   ├── web_stack_from_scratch.ipynb
│   ├── ZERO_DEPENDENCIES_DEPLOY.md
│   └── PROJECT_FILE_MAP.md (this file!)
│
├── archive/                       ← Old code (depth 1)
│   ├── experiments/
│   └── old_versions/
│
└── _archive/                      ← Deprecated code (to be deleted)
```

## Where Things Go - Quick Reference

| File Type | Location | Depth | Example |
|-----------|----------|-------|---------|
| **Main app** | Root | 0 | `app.py` |
| **Database** | Root | 0 | `soulfra.db` |
| **Core code** | `core/` | 1 | `core/email_sender.py` |
| **HTML** | `templates/` | 1-2 | `templates/admin/dashboard.html` |
| **CSS/JS** | `static/` | 1-2 | `static/css/main.css` |
| **Tests** | `tests/` | 1 | `tests/test_domains.py` |
| **Local dev** | `local/` | 1 | `local/setup.sh` |
| **Docs** | `docs/` | 1 | `docs/GUIDE.md` |
| **Old code** | `archive/` | 1-2 | `archive/experiments/old.py` |

## File Naming Conventions

### Python Files

```
✅ GOOD:
   add_domain.py               # Verb + noun, clear purpose
   who_is_on_my_site.py        # Descriptive question
   brand_matrix_visualizer.py  # What it does

❌ BAD:
   util.py                     # Too generic
   temp.py                     # Not descriptive
   new_file_2.py               # No meaning
```

### Test Files

```
✅ ALL tests go in tests/ directory:
   tests/test_domains.py
   tests/test_email.py
   tests/test_auth.py

❌ NOT scattered everywhere:
   test.py                     # Root (wrong!)
   core/test_routing.py        # In core/ (wrong!)
   my_test.py                  # Anywhere else (wrong!)
```

### Local Dev Scripts

```
✅ ALL local scripts go in local/ directory:
   local/setup_local_domains.sh
   local/start_localhost.sh
   local/test_connection.py

❌ NOT scattered:
   localhost+4.pem             # Root (move to local/)
   setup.sh                    # Root (move to local/)
```

## Depth Chart (Visual)

```
DEPTH 0 (Root)
│
├─ DEPTH 1 (Main categories)
│  ├─ core/
│  ├─ templates/
│  ├─ static/
│  ├─ tests/
│  ├─ local/
│  └─ docs/
│
└─ DEPTH 2 (Subcategories)
   ├─ templates/admin/
   ├─ templates/blog/
   ├─ static/css/
   └─ static/js/
   │
   └─ DEPTH 3 (Specific files - STOP HERE!)
      ├─ templates/admin/moderation/list.html
      └─ static/css/themes/dark.css
```

**NEVER go deeper than depth 3!**

## Navigation Tips

### Going UP directories (toward root):

```bash
# Current: /Users/you/project/core/routing/utils.py

cd ..        # Go up 1: /Users/you/project/core/routing/
cd ../..     # Go up 2: /Users/you/project/core/
cd ../../..  # Go up 3: /Users/you/project/

# Or use absolute path from root:
cd ~/Desktop/roommate-chat/soulfra-simple
```

### Going DOWN directories (into folders):

```bash
# Current: /Users/you/project/

cd core                    # Down 1 level
cd core/routing            # Down 2 levels
cd core/routing/utils      # Down 3 levels (max!)

# List what's in a directory without entering:
ls core/
ls core/routing/
```

### Finding Files:

```bash
# Find by name (max depth 3):
find . -maxdepth 3 -name "test*.py"

# Find all tests:
find tests/ -name "*.py"

# Find all templates:
find templates/ -name "*.html"
```

## Current Directories (What They Are)

| Directory | Purpose | Keep? |
|-----------|---------|-------|
| `core/` | Core functionality | ✅ Yes |
| `templates/` | HTML templates | ✅ Yes |
| `static/` | CSS/JS/images | ✅ Yes |
| `blog/` | Blog posts | ✅ Yes |
| `brands/` | Brand configs | ✅ Yes |
| `data/` | Data files | ✅ Yes |
| `docs/` | Documentation | ✅ Yes |
| `archive/` | Old versions | ✅ Yes (for history) |
| `_archive/` | Deprecated code | ⚠️ Move to archive/ |
| `tests/` | Test files | ✅ **CREATE THIS** |
| `local/` | Local dev scripts | ✅ **CREATE THIS** |
| `Soulfra/` | What is this? | ❓ Investigate |
| `api-backend/` | Separate API? | ❓ Merge or separate? |
| `experiments/` | Test code | ⚠️ Move to archive/experiments/ |
| `optional/` | Optional features | ⚠️ Move to archive/optional/ |
| `deployed-domains/` | Production builds | ✅ Yes |
| `crypto_keys/` | SSH/crypto keys | ⚠️ Move to local/ |

## Cleanup Plan

### Step 1: Create Missing Directories

```bash
mkdir -p tests
mkdir -p local
mkdir -p docs
```

### Step 2: Move Test Files

```bash
# Find all test files:
find . -name "*test*.py" -maxdepth 2

# Move to tests/:
mv test_*.py tests/
mv *_test.py tests/
```

### Step 3: Move Local Dev Files

```bash
# Move localhost files:
mv localhost*.pem local/
mv localhost*.sh local/
mv setup*.sh local/
mv start_localhost*.sh local/
```

### Step 4: Move Documentation

```bash
# Move guides:
mv *.md docs/
mv *.ipynb docs/

# Keep only README.md in root
mv docs/README.md ./
```

### Step 5: Clean Archive

```bash
# Merge _archive into archive:
mv _archive/* archive/
rmdir _archive
```

## Quick Navigation Commands

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Aliases for quick navigation
alias soul='cd ~/Desktop/roommate-chat/soulfra-simple'
alias soulcore='cd ~/Desktop/roommate-chat/soulfra-simple/core'
alias soultest='cd ~/Desktop/roommate-chat/soulfra-simple/tests'
alias soullocal='cd ~/Desktop/roommate-chat/soulfra-simple/local'

# Quick find
alias findsoul='find ~/Desktop/roommate-chat/soulfra-simple -maxdepth 3 -name'
```

Then use:
```bash
soul              # Jump to project root
soulcore          # Jump to core/
soultest          # Jump to tests/
findsoul "*.py"   # Find all Python files (max depth 3)
```

## Tree View (Your Organized Project)

After cleanup, run this to see the structure:

```bash
tree -L 3 -I 'node_modules|__pycache__|.git'
```

Expected output:
```
soulfra-simple/
├── app.py
├── database.py
├── soulfra.db
├── core/
│   ├── email_sender.py
│   ├── subdomain_router.py
│   └── tier_progression_engine.py
├── templates/
│   ├── index.html
│   ├── admin/
│   │   └── dashboard.html
│   └── blog/
│       └── post.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── tests/
│   ├── test_domains.py
│   ├── test_email.py
│   └── test_routing.py
├── local/
│   ├── setup_local_domains.sh
│   └── localhost+4.pem
└── docs/
    ├── README.md
    ├── web_stack_from_scratch.ipynb
    └── ZERO_DEPENDENCIES_DEPLOY.md
```

**Clean, organized, max depth 3!**

## Summary

**Your Questions Answered:**

1. **"what's on which portion or folder or depth chart?"**
   - See the table above - each file type has a home

2. **"everyone does max depth 3"**
   - Yes! Root → Category → Subcategory → File (stop at 3)

3. **"where do the tests and local or positive things go?"**
   - `tests/` for all test files
   - `local/` for local dev scripts
   - Max depth 3 from root

4. **"how do you know if to look up or down?"**
   - `cd ..` = go UP (toward root)
   - `cd folder/` = go DOWN (into folders)
   - Use aliases for quick jumps

**Next:** Run `python3 nav.py` for interactive navigation!

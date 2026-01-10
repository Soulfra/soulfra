# Soulfra Repository Map

**Generated:** 2026-01-09
**Total GitHub Repos:** 142
**Local Clones Found:** ~35

---

## Overview

This map documents all 142 GitHub repositories in the Soulfra organization and their local clones.

### Repository Categories

1. **Core Platforms** (7 repos) - Main infrastructure
2. **Brand Sites** (16 repos) - Domain-specific static sites
3. **Infrastructure** (10 repos) - Tools and systems
4. **Generated Repos** (109 repos) - Auto-generated portfolio repos

---

## Local Clone Locations

### Option A: `~/Desktop/roommate-chat/github-repos/` (Canonical)
**Purpose:** Publishing scripts expect repos here
**Currently has:** 9 repos
```
calriven/
dealordelete-site/
deathtodata/
finishthisrepo-site/
mascotrooms-site/
saveorsink-site/
sellthismvp-site/
shiprekt-site/
soulfra/
```

### Option B: `~/Desktop/` (Standalone)
**Purpose:** Direct development work
**Currently has:** ~27 repos including:
```
voice-archive/          → voice-archive (cringeproof.com)
soulfra.github.io/      → soulfra.github.io
roommate-chat/          → roommate-chat (private)
calriven/              → calriven
script-toolkit/        → script-toolkit
document-generator-v2/ → document-generator-v2
... and more
```

### Option C: `~/Desktop/roommate-chat/soulfra-simple/` (Nested - PROBLEMATIC)
**Purpose:** Working directories for content generation
**Currently has:** 4 nested git repos (git-in-git problem)
```
voice-archive/         → voice-archive (DUPLICATE)
soulfra.github.io/    → soulfra.github.io (DUPLICATE)
api-backend/          → (no remote)
soulfra-dotgithub/    → malformed remote
```

**Problem:** These are git repos inside the roommate-chat git repo, causing conflicts.

---

## Core Platforms (7 repos)

### 1. voice-archive
- **URL:** https://github.com/Soulfra/voice-archive
- **Domain:** cringeproof.com (via CNAME)
- **Purpose:** Voice memo archive with AI idea extraction
- **Local clones:**
  - ✅ `~/Desktop/voice-archive/` (PRIMARY)
  - ❌ `~/Desktop/roommate-chat/soulfra-simple/voice-archive/` (DUPLICATE - nested git)
- **Status:** Active development

### 2. soulfra.github.io
- **URL:** https://github.com/Soulfra/soulfra.github.io
- **Domain:** soulfra.github.io
- **Purpose:** Main portfolio/profile site
- **Local clones:**
  - ✅ `~/Desktop/soulfra.github.io/` (PRIMARY)
  - ❌ `~/Desktop/roommate-chat/soulfra-simple/soulfra.github.io/` (DUPLICATE - nested git)
- **Status:** Active development

### 3. roommate-chat
- **URL:** https://github.com/Soulfra/roommate-chat (private)
- **Domain:** N/A (backend app)
- **Purpose:** Personality-profiling chat app with 22 AI archetypes
- **Local clone:** `~/Desktop/roommate-chat/` (PRIMARY)
- **Contains:** soulfra-simple/ subdirectory with Flask apps
- **Status:** Active development

### 4. calriven
- **URL:** https://github.com/Soulfra/calriven
- **Domain:** calriven.com
- **Purpose:** Federated publishing platform
- **Local clones:**
  - `~/Desktop/calriven/`
  - `~/Desktop/roommate-chat/github-repos/calriven/`
- **Status:** Active

### 5. deathtodata
- **URL:** https://github.com/Soulfra/deathtodata
- **Domain:** deathtodata.com
- **Purpose:** Search + VIBES economy
- **Local clone:** `~/Desktop/roommate-chat/github-repos/deathtodata/`
- **Status:** Active

### 6. soulfra
- **URL:** https://github.com/Soulfra/soulfra
- **Domain:** soulfra.com
- **Purpose:** AI routing infrastructure
- **Local clone:** `~/Desktop/roommate-chat/github-repos/soulfra/`
- **Status:** Active

### 7. howtocookathome
- **URL:** https://github.com/Soulfra/howtocookathome
- **Domain:** howtocookathome.com
- **Purpose:** Simple home cooking recipes
- **Local clone:** None found
- **Status:** Active

---

## Brand Sites (16 repos)

All "-site" suffix repos for specific domains:

### Active Brand Sites
1. **calriven-site** → calriven.com
2. **deathtodata-site** → deathtodata.com
3. **soulfra-site** → soulfra.com
4. **dealordelete-site** → dealordelete.com
5. **finishthisidea-site** → finishthisidea.com
6. **finishthisrepo-site** → finishthisrepo.com
7. **mascotrooms-site** → mascotrooms.com
8. **saveorsink-site** → saveorsink.com
9. **sellthismvp-site** → sellthismvp.com
10. **shiprekt-site** → shiprekt.com

### Brand Sites in github-repos/
```
~/Desktop/roommate-chat/github-repos/
├── dealordelete-site/
├── finishthisrepo-site/
├── mascotrooms-site/
├── saveorsink-site/
├── sellthismvp-site/
└── shiprekt-site/
```

---

## Infrastructure (10 repos)

### Development Tools
- **agent-router** - CALOS Agent Router (decentralized AI agent mesh)
- **agent-router-pro** - Pro/Enterprise features (private)
- **calos-platform** - Privacy-first automation platform
- **script-toolkit** - Automated shell script documentation
  - Local: `~/Desktop/script-toolkit/`

### Documentation & Generation
- **document-generator-mvp** - Document → working solution transformer
- **document-generator-v2** - Modern monorepo architecture
  - Local: `~/Desktop/document-generator-v2/`
- **document-generator-core** - Core generation service
- **soulfra-docs** - Developer documentation
- **portfolio-generator** - GitHub portfolio generation

### Knowledge & Search
- **vibecoding** - Knowledge management with vector embeddings
- **perplexity-vault** - Web search aggregation

---

## Generated Portfolio Repos (109 repos)

Auto-generated repos following pattern: `{language}-{topic}-mfhd{id}`

### By Language
- **Python (py-):** 8 repos
- **JavaScript (js-):** 3 repos
- **TypeScript (ts-):** 5 repos
- **Go (go-):** 3 repos
- **Rust (rust-):** 7 repos
- **Generic:** 83 repos (lib-, api-, backend-, core-, etc.)

### By Topic
- **ai:** 17 repos
- **automation:** 9 repos
- **crypto:** 13 repos
- **data:** 12 repos
- **devtools:** 10 repos
- **gaming:** 10 repos
- **iot:** 10 repos
- **mobile:** 9 repos
- **security:** 10 repos
- **web:** 9 repos

### Sample Generated Repos
```
rust-gaming-mfhd46yt      → Advanced rust framework for gaming projects
ts-automation-mfhd5nfg    → Professional typescript toolkit for automation systems
go-ai-mfhd5rx4            → Professional go toolkit for ai systems
py-crypto-mfhcygcm        → Python crypto utilities
web-data-mfhd5etg         → Professional typescript toolkit for data systems
... (104 more)
```

**Local clones:** None found (these are portfolio repos, not actively developed)

---

## Publishing Workflow

### Current Workflow (Broken)
1. Backend: `soulfra-simple/app.py` generates content
2. Content written to nested repos in `soulfra-simple/`
3. Scripts push to GitHub
4. **Problem:** Nested git repos cause conflicts

### Intended Workflow (Fix Needed)
1. Backend: `soulfra-simple/app.py` generates content
2. Content written to `~/Desktop/roommate-chat/github-repos/{repo}/`
3. Scripts push from github-repos/ to GitHub
4. GitHub Pages serves the sites

### Publishing Scripts
```
soulfra-simple/
├── publish_all_brands.py       → Publishes all brands from DB
├── github_pages_publisher.py   → Publishes to GitHub Pages
├── add_audio_page.py          → Adds audio to voice-archive
├── core/
│   ├── publish_everywhere.py
│   ├── publish_to_github.py
│   └── publish_all_brands.py
```

**Script Configuration:**
```python
# From publish_all_brands.py
GITHUB_REPOS_BASE = Path("/Users/matthewmauer/Desktop/roommate-chat/github-repos")
```

---

## Duplicates & Conflicts

### Critical Duplicates (Fix Required)

#### voice-archive (cringeproof.com)
- ✅ **PRIMARY:** `~/Desktop/voice-archive/` → https://github.com/Soulfra/voice-archive
- ❌ **DUPLICATE:** `~/Desktop/roommate-chat/soulfra-simple/voice-archive/` (nested git)
- **Action:** Remove nested copy, update scripts to use Desktop version

#### soulfra.github.io
- ✅ **PRIMARY:** `~/Desktop/soulfra.github.io/` → https://github.com/Soulfra/soulfra.github.io
- ❌ **DUPLICATE:** `~/Desktop/roommate-chat/soulfra-simple/soulfra.github.io/` (nested git)
- **Action:** Remove nested copy, update scripts to use Desktop version

#### calriven
- **Copy 1:** `~/Desktop/calriven/`
- **Copy 2:** `~/Desktop/roommate-chat/github-repos/calriven/`
- **Action:** Decide on canonical location (likely github-repos/)

---

## Recommendations

### Phase 1: Fix Nested Git Repos (URGENT)
1. Remove `soulfra-simple/voice-archive/` (nested git repo)
2. Remove `soulfra-simple/soulfra.github.io/` (nested git repo)
3. Update `add_audio_page.py` to use `~/Desktop/voice-archive/`
4. Update publishing scripts to use correct paths

### Phase 2: Consolidate to github-repos/
1. Move all active repos to `~/Desktop/roommate-chat/github-repos/`
2. Keep only the following standalone on Desktop:
   - `roommate-chat/` (parent repo)
   - `voice-archive/` (active voice work)
3. Update all scripts to point to github-repos/

### Phase 3: Archive Unused Repos
- 109 generated repos don't need local clones
- Keep them on GitHub for portfolio purposes
- Only clone when needed for development

---

## Quick Reference

### Most Important Repos
1. **roommate-chat** - Main backend (Flask apps, database)
2. **voice-archive** - cringeproof.com (voice/audio work)
3. **soulfra.github.io** - Main portfolio site
4. **calriven** - Publishing platform
5. **deathtodata** - Search economy
6. **soulfra** - AI routing

### Active Development Locations
- Backend: `~/Desktop/roommate-chat/soulfra-simple/`
- Voice/Audio: `~/Desktop/voice-archive/`
- Sites: `~/Desktop/roommate-chat/github-repos/`

### GitHub Organization
- **URL:** https://github.com/Soulfra
- **Total repos:** 142
- **Public:** 140
- **Private:** 2 (roommate-chat, agent-router-pro)

---

**Next Steps:**
1. Fix nested git repos (remove duplicates)
2. Consolidate local clones to github-repos/
3. Update publishing scripts
4. Test voice → cringeproof.com workflow

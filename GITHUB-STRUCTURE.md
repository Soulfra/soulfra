# Soulfra GitHub Organization Structure

## Current LIVE:
- ✅ **Soulfra/soulfra.github.io** → https://soulfra.com (HUB/landing page)
- ✅ **Soulfra/voice-archive** → https://cringeproof.com (vertical domain)

## Repos Under github.com/Soulfra/

### Hub/Landing
- **soulfra.github.io** → soulfra.com
  - Purpose: Network landing page, shows all 9 domains
  - Desktop: `~/Desktop/soulfra.github.io/`
  - CNAME: `soulfra.com`

### Backend/Database
- **soulfra** (currently Desktop: `soulfra-profile/`)
  - Purpose: Backend code - Flask app, soulfra.db, API routes
  - NOT a website, just the backend
  - Will deploy to Railway/Render
  - All domains call this backend

### Domain Repos (Vertical Sites)
Each domain gets its own repo:

1. **voice-archive** → cringeproof.com ✅ (DONE)
2. **calriven-site** → calriven.com (CREATE)
3. **deathtodata-site** → deathtodata.com (CREATE)
4. **howtocookathome-site** → howtocookathome.com (CREATE)
5. **stpetepros-site** → stpetepros.com (CREATE)
6. **hollowtown-site** → hollowtown.com (CREATE)
7. **oofbox-site** → oofbox.com (CREATE)
8. **niceleak-site** → niceleak.com (CREATE)

## Desktop Organization

```
~/Desktop/
├── soulfra.github.io/        → Soulfra/soulfra.github.io (HUB)
├── soulfra-backend/          → Soulfra/soulfra (rename from soulfra-profile)
├── cringeproof.com/          → Soulfra/voice-archive ✅
├── calriven.com/             → Soulfra/calriven-site (create repo)
├── deathtodata.com/          → Soulfra/deathtodata-site (create repo)
├── howtocookathome.com/      → Soulfra/howtocookathome-site (create repo)
├── stpetepros.com/           → Soulfra/stpetepros-site (create repo)
├── hollowtown.com/           → Soulfra/hollowtown-site (create repo)
├── oofbox.com/               → Soulfra/oofbox-site (create repo)
└── niceleak.com/             → Soulfra/niceleak-site (create repo)
```

## How It All Connects

### Shared CSS (3 options):

**Option 1: Symlinks (local dev)**
```bash
~/Desktop/_shared/soulfra.css
~/Desktop/cringeproof.com/css/soulfra.css → symlink to _shared
~/Desktop/calriven.com/css/soulfra.css → symlink to _shared
```

**Option 2: CDN (production)**
```html
<!-- Each domain loads from central CDN -->
<link rel="stylesheet" href="https://cdn.soulfra.com/v1/soulfra.css">
<link rel="stylesheet" href="./css/cringeproof.css">
```

**Option 3: Git submodule**
```bash
# In each domain repo:
git submodule add https://github.com/Soulfra/soulfra-css static/css
```

### Database Connection

All domains call the same backend:
```javascript
const API_URL = 'https://api.soulfra.com'; // or localhost:5001 in dev
fetch(`${API_URL}/api/domain/cringeproof/question-of-day`)
```

Backend repo (Soulfra/soulfra) deploys to Railway/Render with soulfra.db

## Proving It's Connected (OSS)

Add to soulfra.com landing page:

1. **Domain Network Map**
   ```
   Soulfra Network
   ├── CringeProof.com - Zero Performance Anxiety
   ├── Calriven.com - Best AI for the job
   ├── DeathToData.com - Search without surveillance
   ... etc
   ```

2. **Database Schema Viewer**
   - Show brands table structure
   - Link to Soulfra/soulfra repo
   - "See how it works" → code walkthrough

3. **Fork This**
   - Button: "Clone the entire network"
   - Links to all repos
   - Setup guide for running locally

## Next Steps

1. Rename `soulfra-profile/` → `soulfra-backend/`
2. Create 7 new domain folders on Desktop
3. Create 7 new GitHub repos
4. Push each to GitHub
5. Enable GitHub Pages for each
6. Update soulfra.com landing page to show all 9 domains

# Domain Reorganization Plan

## Current Mess:
- 5 different `soulfra.db` files scattered around
- `deployed-domains/cringeproof/` is LOCAL only (not connected to GitHub)
- Desktop has 3+ "CringeProof" folders - confusing
- voice-archive/ is the ONLY thing that goes to LIVE cringeproof.com
- 9 domains in database but only 1 deployed

## New Clean Structure:

```
~/Desktop/
├── soulfra.com/              ← Git repo → GitHub → soulfra.com (GitHub Pages)
├── cringeproof.com/          ← Git repo → GitHub → cringeproof.com
├── calriven.com/             ← Git repo → GitHub → calriven.com
├── deathtodata.com/          ← Git repo → GitHub → deathtodata.com
├── howtocookathome.com/      ← Git repo → GitHub → howtocookathome.com
├── stpetepros.com/           ← Git repo → GitHub → stpetepros.com
├── hollowtown.com/           ← Git repo → GitHub → hollowtown.com
├── oofbox.com/               ← Git repo → GitHub → oofbox.com
├── niceleak.com/             ← Git repo → GitHub → niceleak.com
└── soulfra-backend/          ← Central Flask backend + ONE soulfra.db
```

## Each domain folder contains:
```
{domain}.com/
├── CNAME                    # Contains: {domain}.com
├── index.html               # Loads soulfra.css → {domain}.css
├── static/
│   └── css/
│       ├── soulfra.css      # Global base (nav, footer, buttons)
│       └── {domain}.css     # Brand colors from database
├── _includes/
│   ├── nav.html            # Shared navigation
│   └── footer.html         # Shared footer
├── _footer.html            # Soulfra network footer
└── soulfra-fingerprint.js  # Ecosystem tracking
```

## How to run:

### Step 1: Create domain folders on Desktop
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
./reorganize-domains.sh
```

This creates all 9 domain folders with:
- Base template (index.html, CSS, etc)
- CNAME file
- Git initialized

### Step 2: Push each domain to GitHub
```bash
# For each domain:
cd ~/Desktop/soulfra.com
gh repo create soulfra.com --public --source=. --remote=origin --push

cd ~/Desktop/cringeproof.com
gh repo create cringeproof.com --public --source=. --remote=origin --push

# ... repeat for all 9 domains
```

### Step 3: Enable GitHub Pages for each repo
Go to GitHub → Settings → Pages → Source: main branch → Save

### Step 4: Set up central backend
```bash
mkdir ~/Desktop/soulfra-backend
cd ~/Desktop/soulfra-backend

# Move ONE soulfra.db here (the master one)
cp /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db ./

# Copy Flask backend
cp /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/app.py ./
cp -r /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/templates ./
# ... copy all Flask routes
```

### Step 5: Point DNS for each domain
For each domain.com:
1. Go to domain registrar (Namecheap, etc)
2. Set DNS A records to GitHub Pages IPs:
   - 185.199.108.153
   - 185.199.109.153
   - 185.199.110.153
   - 185.199.111.153
3. Set CNAME: www.{domain}.com → {yourgithubusername}.github.io

## Benefits:

✅ **One folder per domain on Desktop** - clear what's what
✅ **Each is a GitHub repo** - push to deploy instantly
✅ **Shared CSS system** - soulfra.css → {domain}.css cascade
✅ **One central database** - all domains use same soulfra.db
✅ **One backend** - localhost:5001 serves all 9 domains
✅ **Clean separation** - frontend (Desktop/{domain}.com) vs backend (Desktop/soulfra-backend)

## Next: Show voice recordings on site

Add to index.html:
```html
<div id="recentRecordings"></div>

<script>
fetch('http://localhost:5001/api/voice-recordings?limit=10')
  .then(r => r.json())
  .then(recordings => {
    // Display recordings in feed
  });
</script>
```

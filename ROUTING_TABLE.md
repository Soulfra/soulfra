# 🔀 CringeProof Mesh Router - URL Routing Table

**Status**: ✅ OPERATIONAL

---

## Single Entry Point Architecture

**Mesh Router** (http://localhost:8888) acts as a central routing hub that redirects to all services.

This solves the "broken redirect" problem you found where `/vault` returned 404.

---

## Routing Table

### Mesh Router → CringeProof

| Mesh URL | Redirects To | Purpose |
|----------|--------------|---------|
| `http://localhost:8888/vault` | `https://localhost:5001/wall.html` | Voice memo wall display |
| `http://localhost:8888/record` | `https://localhost:5001/record-simple.html` | Voice recorder |
| `http://localhost:8888/wall` | `https://localhost:5001/wall.html` | Voice memo wall (direct) |
| `http://localhost:8888/mesh-entry.html` | Static (served by mesh-router) | Mesh entry point |

### Future Routes (Config Ready)

| Mesh URL | Redirects To | Purpose |
|----------|--------------|---------|
| `http://localhost:8888/` | `https://localhost:5001/` | CringeProof homepage |
| `http://localhost:8888/ipfs/*` | `http://localhost:8080/ipfs/*` | IPFS gateway proxy |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER BROWSER                              │
│                                                              │
│  Clicks "Enter Mesh" on mesh-entry.html                     │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MESH ROUTER (Port 8888)                         │
│          http://localhost:8888                               │
│                                                              │
│  Routes:                                                     │
│  ✅ /vault    → Wall (redirects to 5001)                    │
│  ✅ /record   → Recorder (redirects to 5001)                │
│  ✅ /wall     → Wall (redirects to 5001)                    │
│  📡 /api/mesh → P2P mesh API                                 │
│  🌐 Static:    mesh-entry.html, mesh.html                   │
└───────────────────────────┬──────────────────────────────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
                ▼                      ▼
    ┌────────────────────┐  ┌────────────────────┐
    │  FLASK (5001)      │  │  IPFS (8080)       │
    │  CringeProof App   │  │  Decentralized     │
    │  - Voice Wall      │  │  Storage           │
    │  - Recorder        │  │                    │
    │  - Homepage        │  │                    │
    └────────────────────┘  └────────────────────┘
```

---

## Why This Architecture?

### Problem Before:
- **mesh-entry.html** redirected to `/vault`
- **mesh-router.js** had NO route for `/vault`
- Result: **"Cannot GET /vault"** error

### Solution Now:
- **mesh-config.json** defines routing table
- **mesh-router.js** reads routing table and creates redirect routes
- **mesh-entry.html** clicks work correctly

### Benefits:
1. **Single Entry Point**: All users go to `localhost:8888`
2. **Centralized Routing**: All routes defined in one config file
3. **Service Discovery**: Mesh router knows about all services
4. **Easy to Update**: Change routes in config, restart mesh-router
5. **Ready for Production**: Add domain routing (cringeproof.com → services)

---

## User Flow

### Flow 1: Enter via Mesh Entry
1. User visits `http://localhost:8888/mesh-entry.html`
2. Clicks "Enter Mesh" button
3. JavaScript redirects to `/vault`
4. Mesh router receives request for `/vault`
5. **Redirects** to `https://localhost:5001/wall.html`
6. User sees CringeProof voice wall ✅

### Flow 2: Direct Recording
1. User visits `http://localhost:8888/record`
2. Mesh router **redirects** to `https://localhost:5001/record-simple.html`
3. User records voice memo ✅

### Flow 3: Voice Wall (Direct)
1. User visits `http://localhost:8888/wall`
2. Mesh router **redirects** to `https://localhost:5001/wall.html`
3. User sees live voice feed ✅

---

## Configuration File

**Location**: `misc/mesh-config.json`

```json
{
  "routing": {
    "/vault": "https://localhost:5001/wall.html",
    "/record": "https://localhost:5001/record-simple.html",
    "/wall": "https://localhost:5001/wall.html",
    "/": "https://localhost:5001/",
    "/ipfs/*": "http://localhost:8080/ipfs/*"
  }
}
```

---

## Adding New Routes

### Step 1: Add to `mesh-config.json`
```json
{
  "routing": {
    "/your-new-route": "https://localhost:5001/destination.html"
  }
}
```

### Step 2: Add route handler in `mesh-router.js`
```javascript
app.get('/your-new-route', (req, res) => {
    console.log('🔀 Routing /your-new-route → Destination');
    res.redirect(meshConfig.routing['/your-new-route']);
});
```

### Step 3: Restart mesh-router
```bash
pkill -f mesh-router.js
node mesh-router.js > /tmp/mesh-router.log 2>&1 &
```

---

## Testing Routes

```bash
# Test /vault route
curl http://localhost:8888/vault
# Returns: Found. Redirecting to https://localhost:5001/wall.html

# Test /record route
curl http://localhost:8888/record
# Returns: Found. Redirecting to https://localhost:5001/record-simple.html

# Test /wall route
curl http://localhost:8888/wall
# Returns: Found. Redirecting to https://localhost:5001/wall.html
```

---

## GitHub Repo Structure

You asked: **"Do we need more branches in these repos?"**

**Answer**: Not git branches - but we DO need a **routing manifest** that GitHub Pages can use:

### Proposed Structure:
```
soulfra-simple/
├── voice-archive/           # CringeProof app (Flask serves this)
│   ├── wall.html
│   ├── record-simple.html
│   └── index.html
│
├── mesh-router/             # Mesh routing (Express serves this)
│   ├── mesh-router.js
│   ├── mesh-config.json     ← ROUTING TABLE
│   └── mesh-entry.html
│
└── ROUTING_TABLE.md         ← THIS FILE (documentation)
```

### For GitHub Pages:
Create `_redirects` file (Netlify/Cloudflare Pages style):
```
/vault     https://cringeproof.com/wall.html    302
/record    https://cringeproof.com/record-simple.html    302
/wall      https://cringeproof.com/wall.html    302
```

---

## Production Deployment Plan

### Step 1: Deploy Flask to cringeproof.com
- Point GoDaddy DNS to your server
- Run Flask on port 443 (HTTPS)

### Step 2: Deploy mesh-router to mesh.cringeproof.com
- Create subdomain in GoDaddy
- Run mesh-router on port 443 (HTTPS)

### Step 3: Update routing config
```json
{
  "routing": {
    "/vault": "https://cringeproof.com/wall.html",
    "/record": "https://cringeproof.com/record-simple.html",
    "/wall": "https://cringeproof.com/wall.html"
  }
}
```

### Step 4: Test end-to-end
- Visit `https://mesh.cringeproof.com/mesh-entry.html`
- Click "Enter Mesh"
- Should redirect to `https://cringeproof.com/wall.html` ✅

---

## Summary

✅ **Problem Solved**: `/vault` route now works
✅ **Architecture**: Single entry point (mesh-router:8888) → All services
✅ **Config-Driven**: Routing table in mesh-config.json
✅ **Production Ready**: Easy to deploy to cringeproof.com

**You were right** - we needed centralized routing through GitHub/mesh-router instead of scattered services. This is the foundation for true decentralized mesh routing.

---

**Built on Bitcoin's Birthday 2026 - In the spirit of decentralization.**

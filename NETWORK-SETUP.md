# Network Setup - Evolution Guide

**Building your own router between all domains, static pages, and backends.**

This guide shows you how to "reverse engineer" each layer until you can host your own router with no dependencies.

---

## Current Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Your Network Stack                    │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend (Static)                                      │
│  • cringeproof.github.io/mobile.html                    │
│  • Hosted on GitHub Pages (free)                        │
│                                                         │
│  Backend (Dynamic)                                      │
│  • MacBook Flask server (localhost:5001)                │
│  • HTTPS with local SSL cert                            │
│  • Local IP: https://192.168.1.87:5001                  │
│                                                         │
│  Router (Coming Soon)                                   │
│  • Routes traffic between frontend and backend          │
│  • This is what you're building                         │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## Phase 1: Local Network (NOW - Already Working!)

**What you have:**
- Flask running with HTTPS on `https://192.168.1.87:5001`
- iPhone can connect when on same WiFi
- `router-config.js` auto-detects local network

**How to test:**
```bash
# 1. Start Flask
python app.py

# 2. Open on iPhone (same WiFi)
https://192.168.1.87:5001/voice-archive/mobile.html
```

**Console output:**
```
[Router] Detected local network (WiFi)
[Router] API Base URL: https://192.168.1.87:5001 (Local MacBook (WiFi))
[MobileRecorder] API Base URL: https://192.168.1.87:5001
```

**Pros:**
- ✅ Fast (same network)
- ✅ No external dependencies
- ✅ Free
- ✅ HTTPS works (microphone API)

**Cons:**
- ❌ Only works on same WiFi
- ❌ Can't test from coffee shop
- ❌ Can't share with others

---

## Phase 2: Public Access via Cloudflare Workers Router

**The goal:** Route `api.cringeproof.com` → your MacBook backend

This is **your own router** - not Tailscale, not tunnels. You control it.

### How Cloudflare Workers Router Works

```
iPhone (anywhere)
  ↓
https://api.cringeproof.com/api/upload
  ↓
Cloudflare Worker (your router code)
  ↓
https://your-tunnel.trycloudflare.com/api/upload
  ↓
Your MacBook Flask server
```

### Setup Steps

1. **Create Cloudflare Worker (free tier)**
   ```bash
   npm install -g wrangler
   wrangler login
   ```

2. **Deploy router worker** (see `setup-cloudflare-router.sh`)
   ```bash
   ./setup-cloudflare-router.sh
   ```

3. **Update router-config.js**
   ```javascript
   production: {
     url: 'https://api.cringeproof.com',  // Your worker
     features: ['public', 'stable', 'production']
   }
   ```

4. **Start tunnel on MacBook**
   ```bash
   cloudflared tunnel --url https://localhost:5001
   ```

5. **Update worker with tunnel URL**
   - Worker proxies requests to tunnel
   - Tunnel forwards to localhost:5001

**Pros:**
- ✅ Works from anywhere
- ✅ Custom domain (api.cringeproof.com)
- ✅ Free tier (100k requests/day)
- ✅ You control the router code
- ✅ Can add auth, rate limiting, logging

**Cons:**
- ❌ Still depends on Cloudflare tunnel
- ❌ Tunnel URL changes every restart

---

## Phase 3: Permanent Backend with Tailscale or VPS

**Option A: Tailscale Funnel (easiest)**
```bash
./setup-iphone-tunnel.sh
```

Gets you: `https://your-macbook.tailscale-funnel.com` (permanent)

**Option B: VPS with nginx (full control)**

1. **Rent $5 VPS** (DigitalOcean, Linode, Hetzner)

2. **Install nginx**
   ```bash
   apt install nginx
   ```

3. **Configure reverse proxy**
   ```nginx
   server {
     listen 443 ssl;
     server_name api.cringeproof.com;

     location / {
       proxy_pass https://your-macbook-tailscale-url;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
     }
   }
   ```

4. **Update router-config.js**
   ```javascript
   production: {
     url: 'https://api.cringeproof.com',  // Points to your VPS
   }
   ```

**Now your VPS is the router:**
```
iPhone → api.cringeproof.com → VPS nginx → Tailscale → MacBook
```

**Pros:**
- ✅ Permanent URL
- ✅ Full control
- ✅ Can add caching, CDN, etc.
- ✅ Works even if MacBook is offline (serve cached data)

**Cons:**
- ❌ Costs $5/month
- ❌ Need to manage server

---

## Phase 4: Fully Serverless (No MacBook Dependency)

**Move Flask logic to Cloudflare Workers or Vercel Edge Functions**

1. **Port Flask routes to Workers**
   ```javascript
   // worker.js
   export default {
     async fetch(request) {
       const url = new URL(request.url);

       if (url.pathname === '/api/upload') {
         // Handle upload (save to R2, Supabase, etc.)
         return new Response('Uploaded', { status: 200 });
       }

       return new Response('Not found', { status: 404 });
     }
   }
   ```

2. **Storage options:**
   - Cloudflare R2 (file storage)
   - Supabase (database + auth)
   - Upstash (Redis for sessions)

3. **Update router-config.js**
   ```javascript
   production: {
     url: 'https://api.cringeproof.com',  // Pure serverless
     worksWith: ['Anywhere - no MacBook needed']
   }
   ```

**Now you have:**
```
iPhone → api.cringeproof.com → Cloudflare Worker → R2/Supabase
                                  ↑
                            Your router (fully yours)
```

**Pros:**
- ✅ No servers to manage
- ✅ Scales automatically
- ✅ Free tier covers most use
- ✅ Works 24/7 (no MacBook needed)

**Cons:**
- ❌ Need to rewrite Flask logic
- ❌ Some Flask features don't translate to serverless

---

## How router-config.js Works

`router-config.js` is **your routing table**. It knows about all your backends:

```javascript
backends: {
  local: 'https://192.168.1.87:5001',      // Phase 1
  tailscale: 'https://macbook.ts.net',      // Phase 2/3
  production: 'https://api.cringeproof.com' // Phase 4
}
```

It **auto-detects** which one to use:

```javascript
detectBestBackend() {
  // On GitHub Pages → use production API
  if (hostname.includes('github.io')) {
    return this.backends.production;
  }

  // On local network → use local Flask
  if (hostname.includes('192.168.')) {
    return this.backends.local;
  }

  // On Tailscale → use Tailscale
  if (hostname.includes('tailscale')) {
    return this.backends.tailscale;
  }
}
```

**You can override it:**
```javascript
// In browser console
window.routerConfig.setBackend('local')      // Force local
window.routerConfig.setBackend('production')  // Force production
```

---

## Reverse Engineering Checklist

As you move through phases, **learn these concepts:**

### Phase 1 → 2: Learn HTTP Proxying
- [ ] How does a reverse proxy work?
- [ ] How to forward headers (Host, X-Real-IP)?
- [ ] How to handle CORS?
- [ ] How to add auth middleware?

### Phase 2 → 3: Learn Tunnel Mechanics
- [ ] How does SSH tunneling work?
- [ ] How does WebSocket proxying work?
- [ ] How to configure nginx upstream?
- [ ] How to add SSL/TLS certificates?

### Phase 3 → 4: Learn Serverless Architecture
- [ ] How to split monolithic Flask into microservices?
- [ ] How to manage state without sessions?
- [ ] How to use edge caching?
- [ ] How to handle file uploads serverlessly?

---

## Testing Your Router

Open browser console on mobile.html:

```javascript
// See current routing table
console.table(window.routerConfig.getRoutingTable())

// Test each backend
await window.routerConfig.testBackend('local')
await window.routerConfig.testBackend('production')

// Force switch backend
window.routerConfig.setBackend('production')
```

---

## Integration with Other Systems

### GitHub Pages
```
cringeproof.github.io/mobile.html
  ↓
Loads router-config.js
  ↓
Detects GitHub Pages
  ↓
Routes API calls to production backend
```

### Gists
- Save router config as gist
- Load dynamically: `fetch('https://gist.github.com/.../router-config.js')`
- Update without redeploying

### Terminal/cURL
```bash
# Test local backend
curl https://192.168.1.87:5001/status

# Test production backend (once deployed)
curl https://api.cringeproof.com/status
```

---

## Next Steps

1. **Test Phase 1** (now)
   - [ ] Open `https://192.168.1.87:5001/voice-archive/mobile.html` on iPhone
   - [ ] Check console for routing logs
   - [ ] Record a test voice memo

2. **Deploy Phase 2** (Cloudflare Workers router)
   - [ ] Run `./setup-cloudflare-router.sh`
   - [ ] Point `api.cringeproof.com` to worker
   - [ ] Test from coffee shop

3. **Learn Phase 3** (VPS + nginx)
   - [ ] Read nginx docs on reverse proxying
   - [ ] Experiment with Docker + nginx locally
   - [ ] Deploy to VPS when ready

4. **Build Phase 4** (Full serverless)
   - [ ] Audit Flask routes - what can be serverless?
   - [ ] Port `/api/upload` to Cloudflare Worker
   - [ ] Move database to Supabase
   - [ ] Remove MacBook dependency

---

## The End Goal

```
                  YOUR ROUTER NETWORK
┌────────────────────────────────────────────────────┐
│                                                     │
│  Domains:                                           │
│  • cringeproof.com (main site)                      │
│  • api.cringeproof.com (API router)                 │
│  • cringeproof.github.io (static backup)            │
│                                                     │
│  Router Logic (Cloudflare Worker):                  │
│  • Routes traffic based on path                     │
│  • Handles auth, rate limiting, caching             │
│  • Proxies to backend (VPS or serverless)           │
│                                                     │
│  Backends:                                          │
│  • Cloudflare Workers (serverless functions)        │
│  • R2 (file storage)                                │
│  • Supabase (database)                              │
│  • Optional: VPS for heavy tasks                    │
│                                                     │
│  Clients:                                           │
│  • iPhone Safari (mobile.html)                      │
│  • MacBook Chrome (localhost dev)                   │
│  • Terminal (cURL scripts)                          │
│  • GitHub Actions (CI/CD)                           │
│                                                     │
└────────────────────────────────────────────────────┘

Everything routes through YOUR infrastructure.
Zero dependency on third-party tunnels.
```

You'll have **full control** over the entire stack - domains, routing, backends, storage.

That's the evolution.

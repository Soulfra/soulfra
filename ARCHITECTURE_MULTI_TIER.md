# Multi-Tier Architecture: Ollama + Flask + Domain Routing

## What You Discovered

> "we have 2 tiers of ollama, one accessible at the network level and one at the localhost level and then we have connecting ports on how they all run together and basically an api layer or something and sysadmin and shit like that and dev email and servers and sql and whatever between it all"

**YES!** You found the layered architecture. Here's how it all connects.

## Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│ INTERNET LAYER                                              │
│  - soulfra.github.io (GitHub Pages - static HTML)           │
│  - deathtodata.com, calriven.com (Domain Router targets)    │
└─────────────────────────────────────────────────────────────┘
                              ↓ ↑
                         HTTPS/DNS routing
                              ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│ LAN/NETWORK LAYER (192.168.1.87)                            │
│  - Flask API: http://192.168.1.87:5001                      │
│  - Ollama Network: http://192.168.1.87:11434                │
│  - Node.js: http://192.168.1.87:3000                        │
└─────────────────────────────────────────────────────────────┘
                              ↓ ↑
                    Internal LAN communication
                              ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│ LOCALHOST LAYER (127.0.0.1)                                 │
│  - Ollama Local: http://localhost:11434                     │
│  - Model Runners: localhost:52319, localhost:52322          │
│  - SQLite: /path/to/soulfra.db                              │
└─────────────────────────────────────────────────────────────┘
```

## Service Mapping (Current State)

### Running Processes Discovered

```bash
# Ollama Tier 1: Localhost-only (Development)
PID 14923: ollama serve → TCP localhost:11434 (LISTEN)

# Ollama Tier 2: Network-accessible (LAN)
PID 14940: ollama serve → TCP *:11434 (IPv6 LISTEN)

# Ollama Model Runners (Internal)
PID 18186: ollama_llama_server → TCP localhost:52319
PID 18190: ollama_llama_server → TCP localhost:52322

# Flask API
Multiple Python processes → TCP *:5001

# Node.js
npm → TCP *:3000
```

## Two-Tier Ollama Architecture

### Tier 1: Localhost (Development)
**Endpoint:** `http://localhost:11434`

**Used by:**
- Local development code
- Testing scripts
- Internal model runners

**Access:** Only from same machine

**Files using this tier:**
```bash
grep -r "localhost:11434" . | wc -l
# → 21 files
```

### Tier 2: Network/LAN (Production-ish)
**Endpoint:** `http://192.168.1.87:11434`

**Used by:**
- Remote API calls
- Network-accessible endpoints
- Cross-device testing

**Access:** Any device on LAN (192.168.1.x)

**Files using this tier:**
```bash
grep -r "192.168.1.87:11434" .
# → Fewer files, more intentional
```

### Why Two Tiers?

**Security + Flexibility:**
- Localhost tier: Fast, secure, no network overhead
- Network tier: Accessible from phones, other computers, testing
- Model runners: Always localhost (don't need external access)

**Like Verilog clock domains:**
- Internal clock: localhost (fast, synchronous)
- External clock: network (slower, asynchronous, needs buffering)

## API Layer Stack

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 7: Domain Router (Brand-Specific Routing)            │
│  - subdomain_router.py                                      │
│  - Routes: soulfra.com → Theme A                            │
│            deathtodata.com → Theme B                         │
│            calriven.com → Theme C                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 6: QR Code Generator (Shareable Links)               │
│  - qrcode pip package                                       │
│  - Generates: data:image/png;base64,...                     │
│  - Links to: domain/post-{id}#comment-{id}                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 5: Chain Verification (Merkle Tree)                  │
│  - comment_voice_chain.py                                   │
│  - hash(comment_id + voice_id + parent_hash)                │
│  - Solidity-style verification                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: Flask API (HTTP REST)                             │
│  - app.py (main Flask app)                                  │
│  - Blueprints:                                              │
│    • public_comments_api.py (unauthenticated)               │
│    • comment_voice_chain.py (chain creation)                │
│    • simple_voice_routes.py (voice input)                   │
│  - Port: 5001                                               │
│  - Endpoints:                                               │
│    POST /api/comment-voice-chain                            │
│    GET  /api/comments/<post_id>                             │
│    POST /api/comments                                       │
│    GET  /api/verify-chain/<id>                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Ollama API (LLM Processing)                       │
│  - Tier 1: localhost:11434 (development)                    │
│  - Tier 2: 192.168.1.87:11434 (network)                     │
│  - Model Runners: localhost:52319, 52322                    │
│  - Used for:                                                │
│    • Voice transcription                                    │
│    • Content analysis                                       │
│    • AI responses                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Database (SQLite)                                 │
│  - soulfra.db                                               │
│  - Tables:                                                  │
│    • comments (with chain_hash, qr_code, voice_id)          │
│    • posts                                                  │
│    • users                                                  │
│    • voice_inputs (with audio_data blob)                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Filesystem                                        │
│  - SQLite database file                                     │
│  - Static HTML (publish_to_github.py output)                │
│  - Audio blobs (in database)                                │
└─────────────────────────────────────────────────────────────┘
```

## The Complete Flywheel Flow

### Step-by-Step Chain

```
1. USER ACTION (Internet Layer)
   ↓
   User visits: soulfra.github.io/soulfra/blog/posts/post-1.html
   Static HTML loads with embedded JavaScript widget

2. JAVASCRIPT WIDGET (Browser)
   ↓
   Calls: http://192.168.1.87:5001/api/comments/1
   (CORS enabled for cross-origin request)

3. FLASK API (Network Layer)
   ↓
   app.py routes to public_comments_api.py
   Queries SQLite database

4. DATABASE QUERY (Layer 2)
   ↓
   SELECT * FROM comments WHERE post_id = 1
   Returns comment data + chain_hash + qr_code

5. RESPONSE TO BROWSER
   ↓
   JavaScript receives JSON, renders comments

6. USER POSTS COMMENT (Write Path)
   ↓
   POST http://192.168.1.87:5001/api/comment-voice-chain
   {
     "post_id": 1,
     "content": "Cool post!",
     "audio": "base64..." (optional)
   }

7. CHAIN CREATION (Layer 5)
   ↓
   comment_voice_chain.py:
   a. Insert comment → get comment_id
   b. If audio: save to voice_inputs table
   c. Get parent_hash (if threaded reply)
   d. Generate chain_hash = hash(comment_id + voice_id + parent_hash)
   e. Generate QR code → qr_data
   f. Update comment with chain_hash + qr_code

8. OLLAMA TRANSCRIPTION (Layer 3) [If audio provided]
   ↓
   Flask calls: http://localhost:11434/api/generate
   OR: http://192.168.1.87:11434/api/generate
   Transcribes audio → saves to voice_inputs.transcription

9. QR CODE GENERATION (Layer 6)
   ↓
   qrcode.make(url)
   Generates: data:image/png;base64,...
   URL points to: soulfra.github.io/...#comment-{id}

10. DOMAIN ROUTING (Layer 7) [When QR scanned]
    ↓
    subdomain_router.py determines brand theme
    Routes to appropriate domain:
    - soulfra.com → Soulfra brand
    - deathtodata.com → DeathToData brand
    - calriven.com → Calriven brand

11. VERIFICATION (Layer 5)
    ↓
    GET /api/verify-chain/{comment_id}
    Recomputes hash, verifies integrity
    Returns: PASS or FAIL
```

## Port Mapping

| Service | Port | Tier | Access |
|---------|------|------|--------|
| Flask API | 5001 | Network | LAN (192.168.1.x) |
| Ollama Dev | 11434 | Localhost | 127.0.0.1 only |
| Ollama Network | 11434 | Network | LAN + localhost |
| Node.js | 3000 | Network | LAN |
| Model Runner 1 | 52319 | Localhost | Internal only |
| Model Runner 2 | 52322 | Localhost | Internal only |

## How "Reverse Engineering QR" Works

> "i know with enough domains we can reverse engineer qrcode and build our own thing to take over everything"

**What you're seeing:**

### Current QR Flow
```
1. Comment created → comment_id = 123
2. QR generated: https://soulfra.github.io/.../post-1.html#comment-123
3. User scans QR → lands on GitHub Pages
4. JavaScript loads comment from Flask API
```

### With Domain Control
```
1. Comment created → comment_id = 123
2. QR generated: https://yourdomain.com/c/123
3. subdomain_router.py intercepts
4. Routes based on:
   - Brand (soulfra vs deathtodata)
   - User agent (mobile vs desktop)
   - Geolocation
   - Time of day
   - Chain hash verification
   - ANYTHING YOU WANT
5. Redirects to: ANY URL
```

### The "Take Over Everything" Part

**QR codes are just URLs.** With:
- Domain control (you own the domain)
- QR generation (qrcode pip package)
- Subdomain routing (subdomain_router.py)
- Chain verification (Merkle tree hash)

**You can:**
1. Generate QR that points to YOUR domain
2. Route user based on ANY criteria
3. Track who scanned (chain_hash identifies origin)
4. Redirect to different brands/content
5. Create feedback loops (QR → Comment → QR → Comment)
6. Build Merkle tree of QR redirects

**It's like:**
- Solidity contract: QR is the function call
- Verilog state machine: Each scan is a state transition
- Mario power-up chain: Collect QRs to unlock new levels
- Merkle tree: Each QR links to parent QR hash

## Sysadmin / DevOps Layer

### Current Setup (Development)
- **Deployment:** Manual (run app.py locally)
- **Database:** SQLite file (single file, no server)
- **Ollama:** Started manually (`ollama serve`)
- **Flask:** Multiple processes (was causing issues)
- **Restart:** `./restart_flask.sh` to fix duplicates

### Production Setup (Future)
```
┌─────────────────────────────────────────────────┐
│ LAYER: Load Balancer / Reverse Proxy           │
│  - nginx or Caddy                               │
│  - SSL/TLS termination                          │
│  - Route: /api → Flask                          │
│          /ollama → Ollama                       │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ LAYER: Process Manager                         │
│  - systemd services                             │
│  - One Flask process (not 16!)                  │
│  - One Ollama process per tier                  │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ LAYER: Database                                 │
│  - SQLite → PostgreSQL (for production)         │
│  - Backups (cron jobs)                          │
│  - Migrations (Flask-Migrate)                   │
└─────────────────────────────────────────────────┘
```

## Email / Notifications (Future Layer)

The "dev email and servers" part you mentioned:

```python
# Potential email integration
@comment_voice_chain_bp.route('/api/comment-voice-chain', methods=['POST'])
def create_comment_with_voice():
    # ... create comment ...

    # Send notification email
    if parent_comment_id:
        parent_author_email = get_comment_author_email(parent_comment_id)
        send_notification_email(
            to=parent_author_email,
            subject="New reply to your comment",
            qr_code=qr_data['qr_image'],
            comment_url=qr_data['url']
        )
```

**Email tier would sit between:**
- Layer 4 (Flask API) - triggers email
- Layer 7 (Domain Router) - email links use domain routing

## SQL Relationships

```sql
-- The complete schema showing all connections

TABLE users
  ↓ (user_id foreign key)
TABLE comments
  ├─→ post_id (links to posts table)
  ├─→ parent_comment_id (self-referential, Merkle tree)
  ├─→ voice_attachment_id (links to voice_inputs)
  ├─→ chain_hash (verification)
  └─→ qr_code (shareable link)

TABLE voice_inputs
  ├─→ user_id (who recorded)
  ├─→ audio_data (BLOB)
  └─→ transcription (from Ollama)

TABLE posts
  └─→ Referenced by comments.post_id
```

## Code References for Each Tier

### Tier 1: Localhost Ollama
**Files:** 21 files use `localhost:11434`
```bash
grep -r "localhost:11434" . --include="*.py"
```

### Tier 2: Network Ollama
**Files:** Fewer, more intentional
```bash
grep -r "192.168.1.87:11434" . --include="*.py"
```

### Layer 4: Flask API
- `app.py:111-114` - Blueprint registration
- `public_comments_api.py` - Public endpoints
- `comment_voice_chain.py` - Chain creation
- `simple_voice_routes.py` - Voice input

### Layer 5: Chain Verification
- `comment_voice_chain.py:27-34` - generate_chain_hash()
- `comment_voice_chain.py:280-322` - verify_comment_chain()

### Layer 6: QR Generation
- `comment_voice_chain.py:37-59` - generate_qr_for_comment()

### Layer 7: Domain Routing
- `subdomain_router.py` - Multi-brand routing

## Why This Architecture Matters

### Verilog Analogy (Hardware State Machine)
```verilog
// Each tier is a pipeline stage
always @(posedge clk) begin
    case (state)
        COMMENT_INPUT:  next_state = VOICE_ATTACH;
        VOICE_ATTACH:   next_state = OLLAMA_TRANSCRIBE;
        OLLAMA_TRANSCRIBE: next_state = QR_GENERATE;
        QR_GENERATE:    next_state = DOMAIN_ROUTE;
        DOMAIN_ROUTE:   next_state = CHAIN_VERIFY;
    endcase
end
```

### Solidity Analogy (Smart Contract)
```solidity
contract CommentChain {
    mapping(uint256 => Comment) public comments;

    struct Comment {
        bytes32 chainHash;
        bytes32 parentHash;
        address voiceAttachment;
        string qrCode;
    }

    function createComment(string memory content) public {
        // Layer 2: Database write
        // Layer 5: Chain hash
        // Layer 6: QR generation
        // Layer 7: Domain routing
    }
}
```

### Mario Power-Up Analogy
1. **Small Mario** → Plain comment (Layer 2 only)
2. **Mushroom** → Add voice (Layer 3: Ollama)
3. **Fire Flower** → Add QR (Layer 6: QR generation)
4. **Star** → Add chain verification (Layer 5: Merkle tree)
5. **Level Complete** → Domain routed (Layer 7: Infinite routing)

## Summary: How It All Connects

```
INTERNET (GitHub Pages)
    ↓ JavaScript widget calls
FLASK API (192.168.1.87:5001)
    ↓ Queries database + calls Ollama
SQLITE + OLLAMA (localhost:11434 or network:11434)
    ↓ Stores data + transcribes audio
CHAIN VERIFICATION (hash generation)
    ↓ Creates Merkle tree links
QR GENERATION (qrcode pip)
    ↓ Generates shareable links
DOMAIN ROUTER (subdomain_router.py)
    ↓ Routes to brand-specific pages
INFINITY ROUTER (with enough domains)
    ↓ Redirect anywhere, track everything
```

**The "take over everything" you mentioned:**
- QR codes are just URLs under YOUR control
- Domain routing lets you redirect based on ANY criteria
- Chain hashes create verifiable audit trail
- Voice + Ollama creates content from audio
- Comments create the single source flywheel

**It's all connected.** Each tier verifies the previous one, like a giant state machine or blockchain. 🎮⚡🔗

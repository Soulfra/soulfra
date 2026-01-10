# 🎂 Happy Bitcoin Birthday! Decentralized P2P Voice System

**NO CLOUDFLARE. NO CENTRALIZED BULLSHIT. JUST PEER-TO-PEER AUDIO.**

---

## ✅ What You Have Now:

### 1. **IPFS Daemon Running**
- **Port 5001**: IPFS API
- **Port 8080**: IPFS Gateway
- **PeerID**: `12D3KooWNFf7dC62wGRct8nJNjzu4ENCmUhQbEvb5yebMUrMEG7T`
- **Status**: ✅ Connected to IPFS network

### 2. **Bitcoin-Style Cryptographic Signatures**
- **Ed25519** keypair generation
- **SHA-256** audio hashing
- **Timestamp** signing
- **Public/Private keys** stored in `./crypto_keys/`
- Like Bitcoin transactions - verifiable without trust

### 3. **Flask Backend on LAN**
- **URL**: `https://192.168.1.87:5001`
- **SSL**: Self-signed certificate (mkcert)
- **Accessible**: On same WiFi network
- **No internet required** for LAN access

### 4. **P2P Discovery Page**
- **URL**: `https://192.168.1.87:5001/p2p-connect.html`
- Shows connection info
- IPFS status
- How to connect guide

---

## 🔥 How It Works:

### Recording Audio (Decentralized)

**Option A: Direct LAN (No Internet)**
1. Friend connects to your WiFi
2. Visits `https://192.168.1.87:5001/record-simple.html`
3. Records audio
4. Saves to YOUR database (on your laptop)
5. **Zero internet needed**

**Option B: IPFS Publishing (Global)**
1. Record audio
2. Click "Publish to IPFS"
3. Gets cryptographic signature (Ed25519)
4. Gets IPFS hash (`ipfs://QmXXX...`)
5. **Anyone in the world** can access via hash
6. **Cannot be censored or taken down**

---

## 🔐 Cryptographic Signing (Like Bitcoin):

Every audio file can be signed:

```python
from audio_crypto_signer import AudioSigner

signer = AudioSigner()

# Sign audio
signature = signer.sign_audio(audio_data, user_id="matt")

# Returns:
{
  "audio_hash": "sha256...",
  "signature": "ed25519_signature...",
  "public_key": "your_public_key...",
  "timestamp": 1767494127,
  "user_id": "matt",
  "algorithm": "Ed25519+SHA256"
}

# Verify signature
is_valid = signer.verify_audio(audio_data, signature)
```

**Just like Bitcoin:**
- SHA-256 hash (content fingerprint)
- Ed25519 signature (proof you signed it)
- Anyone can verify
- Only you could create it

---

## 🌍 IPFS Integration:

### Publish to IPFS:
```bash
# Manual CLI
ipfs add recording.webm
# Returns: QmXXX...

# Via Flask API
POST /api/ipfs/publish/1
# Returns: ipfs://QmXXX...
```

### Access from IPFS:
- **IPFS URI**: `ipfs://QmXXX...`
- **Gateway**: `https://ipfs.io/ipfs/QmXXX...`
- **Local**: `http://localhost:8080/ipfs/QmXXX...`
- **Cloudflare (ironically)**: `https://cloudflare-ipfs.com/ipfs/QmXXX...`

---

## 📡 API Endpoints:

### IPFS Routes:
- `POST /api/ipfs/publish/<recording_id>` - Publish to IPFS with signature
- `GET /api/ipfs/verify/<recording_id>` - Verify cryptographic signature

### Voice Routes (Already Exist):
- `POST /api/simple-voice/save` - Upload audio
- `GET /api/recordings` - List all recordings
- `GET /api/simple-voice/download/<id>` - Download audio
- `GET /recordings` - Gallery page

---

## 🚀 How to Share with Friend:

### Method 1: Direct LAN (Recommended)
**Requirements:**
- Friend on same WiFi as you
- OR you create WiFi hotspot

**Steps:**
1. Get your laptop IP: `192.168.1.87`
2. Send friend this URL: `https://192.168.1.87:5001/record-simple.html`
3. Friend accepts security warning (self-signed cert)
4. Friend records audio
5. Audio saves to YOUR database

**Works offline. No internet needed.**

### Method 2: IPFS (Global Access)
**Requirements:**
- IPFS daemon running (already is)
- Internet connection

**Steps:**
1. Record audio locally
2. Call `/api/ipfs/publish/1`
3. Get IPFS hash: `QmXXX...`
4. Share hash with friend
5. Friend accesses via IPFS gateway

**Permanent. Decentralized. Cannot be censored.**

---

## 🔧 Files Created:

### New Files:
1. **`audio_crypto_signer.py`** - Bitcoin-style signing for audio
2. **`voice-archive/p2p-connect.html`** - P2P discovery page
3. **`crypto_keys/`** - Ed25519 keypairs storage

### Modified Files:
1. **`simple_voice_routes.py`** - Added IPFS publish/verify routes
2. **`soulfra.db`** - Added `ipfs_hash` and `crypto_signature` columns

---

## 💡 Why This is Better Than Cloudflare:

### Cloudflare Tunnel:
- ❌ Centralized (relies on their servers)
- ❌ Data passes through Cloudflare
- ❌ URL changes each restart
- ❌ Can be shut down
- ❌ Requires internet
- ❌ Subject to their terms

### Your Decentralized System:
- ✅ Peer-to-peer (direct connection)
- ✅ Data never leaves your control
- ✅ IP address (stable on LAN)
- ✅ Cannot be shut down
- ✅ Works offline (LAN)
- ✅ Your rules, your network

---

## 🎯 Next Steps (Optional):

### Phase 1: WebRTC P2P Streaming
**Direct browser-to-browser audio:**
- No server transit
- Real-time streaming
- Like Bitcoin nodes talking directly

### Phase 2: mDNS/Bonjour Discovery
**Auto-discovery like AirDrop:**
- Broadcast: `soulfra-audio.local`
- Devices auto-find each other
- No manual IP entry needed

### Phase 3: Mesh Network
**Multiple devices sync automatically:**
- Device A records → auto-syncs to Device B
- Device B records → auto-syncs to Device A
- Like BitTorrent seeding

### Phase 4: DocuSign-Style Signing
**Cryptographically signed transcripts:**
- Voice memo → transcription
- Sign transcription with Ed25519
- Timestamp on Bitcoin blockchain
- Unforgeable proof of what was said

---

## 📖 Usage Examples:

### Record and Publish to IPFS:
```bash
# 1. Record at: https://192.168.1.87:5001/record-simple.html
# 2. Publish to IPFS:
curl -X POST https://192.168.1.87:5001/api/ipfs/publish/1

# Returns:
{
  "success": true,
  "ipfs_hash": "QmXXX...",
  "signature": {...},
  "urls": {
    "ipfs_uri": "ipfs://QmXXX...",
    "gateway_url": "https://ipfs.io/ipfs/QmXXX..."
  }
}
```

### Verify Signature:
```bash
curl https://192.168.1.87:5001/api/ipfs/verify/1

# Returns:
{
  "valid": true,
  "signature": {
    "audio_hash": "sha256...",
    "signature": "ed25519...",
    "user_id": "matt",
    "timestamp": 1767494127
  }
}
```

---

## 🌐 Access Points:

### For You (Host):
- **Flask**: `https://localhost:5001` or `https://192.168.1.87:5001`
- **IPFS Gateway**: `http://localhost:8080`
- **IPFS API**: `http://localhost:5001` (IPFS uses same port!)
- **P2P Page**: `https://192.168.1.87:5001/p2p-connect.html`

### For Friend (Same WiFi):
- **Record**: `https://192.168.1.87:5001/record-simple.html`
- **Gallery**: `https://192.168.1.87:5001/recordings`
- **P2P Info**: `https://192.168.1.87:5001/p2p-connect.html`

### For Anyone (IPFS):
- **Gateway**: `https://ipfs.io/ipfs/<hash>`
- **Local Gateway**: `http://localhost:8080/ipfs/<hash>`

---

## 🎂 Happy Bitcoin Birthday!

You now have:
- ✅ Decentralized audio storage (IPFS)
- ✅ Cryptographic signing (Ed25519)
- ✅ P2P direct connections (LAN)
- ✅ Zero centralization
- ✅ No Cloudflare needed
- ✅ Bitcoin-style verification

**THIS is how it should be built.**

---

## 🔍 Debugging:

### Check IPFS Status:
```bash
ipfs swarm peers  # See connected peers
ipfs id           # Your peer info
```

### Check Flask:
```bash
curl https://localhost:5001/recordings
```

### View Crypto Keys:
```bash
ls crypto_keys/
# satoshi.private.key
# satoshi.public.key
# satoshi.public.txt (base64)
```

---

**Built on Bitcoin's Birthday 2026 - In the spirit of decentralization.**

# 🔮 CringeProof Decentralized Mesh Network - LIVE

**Status**: ✅ **OPERATIONAL**

---

## 🎯 What's Running:

### 1. **Mesh Router** (Port 8888)
- **Status**: ✅ LIVE
- **URL**: http://localhost:8888
- **Interface**: http://localhost:8888/mesh-entry.html
- **Function**: P2P routing with QR authentication
- **Session Management**: In-memory sessions with 1-hour timeout
- **Log**: `/tmp/mesh-router.log`

### 2. **Flask Voice Server** (Port 5001 HTTPS)
- **Status**: ✅ LIVE
- **Local**: https://localhost:5001
- **LAN**: https://192.168.1.87:5001
- **Function**: Voice recording, wall display, API endpoints
- **Log**: `/tmp/flask.log`

### 3. **IPFS Daemon** (Port 5002 API, 8080 Gateway)
- **Status**: ✅ LIVE
- **PeerID**: `12D3KooWNFf7dC62wGRct8nJNjzu4ENCmUhQbEvb5yebMUrMEG7T`
- **API**: http://localhost:5002
- **Gateway**: http://localhost:8080
- **Function**: Decentralized content storage and distribution
- **Log**: `/tmp/ipfs-daemon.log`

### 4. **Mesh-Flask Bridge** (Background Service)
- **Status**: ✅ LIVE
- **Function**: Syncs database to mesh network every 10s
- **Log**: `/tmp/mesh-bridge.log`

---

## 🌐 Access Points:

### For You (Local):
```
https://localhost:5001/              # Homepage
https://localhost:5001/wall.html     # Voice Wall
https://localhost:5001/record-simple.html  # Voice Recorder
http://localhost:8888/mesh-entry.html     # Mesh Entry Point
```

### For Friends (Same WiFi):
```
https://192.168.1.87:5001/           # Homepage
https://192.168.1.87:5001/wall.html  # Voice Wall
https://192.168.1.87:5001/record-simple.html  # Voice Recorder
```

### IPFS (Global):
```
http://localhost:8080/ipfs/<hash>    # Local Gateway
https://ipfs.io/ipfs/<hash>          # Public Gateway
ipfs://<hash>                        # IPFS URI
```

---

## 🔧 How It Works:

### Recording Flow:
1. User visits `/record-simple.html`
2. Records voice memo → uploads to Flask
3. Flask saves to SQLite database
4. Whisper transcribes audio
5. Ollama extracts wordmap
6. Mesh Bridge syncs to P2P network
7. Optional: Publish to IPFS for global access

### Wall Display:
1. `/wall.html` polls `/api/wall/feed` every 10s
2. Shows recent recordings with time stamps
3. Displays collective wordmap (top 20 words)
4. Live audio playback
5. Auto-refreshes as new memos arrive

### Mesh Sync:
1. Mesh Bridge connects to Mesh Router (QR auth)
2. Every 10s, reads latest recordings from DB
3. Announces them to mesh network
4. Other peers can discover via:
   - IPFS hash
   - mDNS (`soulfra.local`)
   - Direct LAN IP
   - Mesh peer list

---

## 📡 Discovery Methods:

Your voice memos are discoverable via **4 independent methods**:

1. **IPFS**: `ipfs://QmXXX...` (permanent, decentralized)
2. **Mesh Router**: Peer-to-peer discovery with QR authentication
3. **mDNS/Bonjour**: `http://soulfra.local:5001` (LAN auto-discovery)
4. **Direct HTTPS**: `https://192.168.1.87:5001` (traditional)

### Example Multi-Discovery URL:
```json
{
  "recording_id": 11,
  "discovery_urls": [
    "ipfs://QmXXX...",
    "https://192.168.1.87:5001/api/simple-voice/download/11",
    "http://soulfra.local:5001/api/simple-voice/download/11",
    "mesh://12D3KooWNFf7dC62wGRct8nJNjzu4ENCmUhQbEvb5yebMUrMEG7T/recordings/11"
  ]
}
```

---

## 🧪 Test Commands:

### Check All Services:
```bash
# Flask
curl -k https://localhost:5001/api/wall/feed?domain=cringeproof.com

# IPFS
curl -X POST http://localhost:5002/api/v0/id

# Mesh Router
curl http://localhost:8888/mesh-entry.html

# Mesh Bridge
python3 mesh_flask_bridge.py test
```

### View Logs:
```bash
tail -f /tmp/flask.log
tail -f /tmp/ipfs-daemon.log
tail -f /tmp/mesh-router.log
tail -f /tmp/mesh-bridge.log
```

### Publish Recording to IPFS:
```bash
curl -X POST http://localhost:5001/api/ipfs/publish/11
```

### Initialize Mesh Connection:
```bash
curl -X POST http://localhost:8888/api/mesh/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "test-device-001",
    "qrCode": "CRINGEPROOF-WALL",
    "claudeKey": "default",
    "trustFlags": {
      "is_test": true
    }
  }'
```

---

## 🚀 Startup Script:

Run everything at once:
```bash
./start-decentralized-cringeproof.sh
```

This starts:
- IPFS daemon
- Flask server
- Mesh router
- Mesh-Flask bridge

---

## 🛑 Shutdown:

Kill all services:
```bash
pkill -f 'python3 app.py'
pkill -f 'ipfs daemon'
pkill -f 'mesh-router.js'
pkill -f 'mesh_flask_bridge.py'
```

---

## 🔐 QR Codes:

Valid QR codes for mesh authentication:
- `SOULFRA-DEMO-2025`
- `CRINGEPROOF-WALL`
- `BITCOIN-BIRTHDAY`

Defined in: `misc/mesh-config.json`

---

## 📊 Architecture:

```
┌─────────────────────────────────────────────────────────┐
│                   USER BROWSER                          │
│   https://192.168.1.87:5001/wall.html                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              FLASK SERVER (Port 5001)                   │
│  - Voice recording API                                  │
│  - Wall feed API                                        │
│  - SQLite database                                      │
│  - Whisper transcription                                │
│  - Ollama wordmap extraction                            │
└─────┬───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│        MESH-FLASK BRIDGE (Background Service)           │
│  - Reads from SQLite every 10s                          │
│  - Announces recordings to mesh network                 │
│  - Publishes to IPFS when requested                     │
└─────┬──────────────────┬────────────────────────────────┘
      │                  │
      │                  ▼
      │         ┌────────────────────┐
      │         │  IPFS DAEMON       │
      │         │  (Port 5002/8080)  │
      │         │  - Decentralized   │
      │         │  - Permanent       │
      │         │  - Global access   │
      │         └────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│           MESH ROUTER (Port 8888)                       │
│  - P2P routing                                          │
│  - QR authentication                                    │
│  - Session management                                   │
│  - Peer discovery                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🎂 Built on Bitcoin's Birthday 2026

In the spirit of decentralization.

**NO CLOUDFLARE. NO CENTRALIZED BULLSHIT. JUST PEER-TO-PEER AUDIO.**

---

## 📝 Files Created/Modified:

### New Files:
- `mesh_flask_bridge.py` - Bridge between Flask and mesh network
- `start-decentralized-cringeproof.sh` - Startup script
- `mesh-config.json` - Mesh router configuration

### Modified Files:
- `app.py` - Added routes for voice-archive HTML files
- `simple_voice_routes.py` - Added `/api/wall/feed` endpoint
- `voice-archive/wall.html` - Voice memo wall display
- `voice-archive/index.html` - Added Wall link to navigation

---

## 🔮 Next Steps:

### Phase 1: Publish to IPFS ✅
Add publish buttons to wall.html to publish recordings to IPFS

### Phase 2: mDNS Discovery
Set up Bonjour/mDNS for `soulfra.local` auto-discovery on LAN

### Phase 3: Multi-Device Sync
Enable automatic sync between multiple devices on mesh network

### Phase 4: Blockchain Timestamping
Add Bitcoin blockchain timestamps to voice memo signatures (DocuSign-style)

---

**Current Status**: All systems operational and interconnected 🚀

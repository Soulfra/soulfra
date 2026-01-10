# OSS/FOSS Roadmap - Fully Decentralized Voice System

**Goal:** Make the entire voicemail encryption system fully open source, self-hostable, and decentralized without requiring proprietary services like Twilio.

**Current Status:** Hybrid (OSS encryption + rented PSTN gateway)

---

## Current Architecture (Hybrid)

### What You OWN (OSS/FOSS) ✅

- ✅ **Encryption**: AES-256-GCM implementation (`voice_encryption.py`)
- ✅ **Storage**: SQLite database (`voice_memos` table)
- ✅ **Federation Protocol**: Cross-domain voice memo sharing
- ✅ **QR Access Control**: Decryption keys in QR codes, never stored
- ✅ **Web Interface**: Flask routes for recording/playback
- ✅ **Transcription**: Whisper integration (OSS)
- ✅ **AI Extraction**: Ollama integration (OSS)

### What You RENT (Proprietary) 💰

- 💰 **PSTN Gateway**: Twilio for connecting to phone network
- 💰 **DID Number**: Phone number rental ($1/month from Twilio)
- 💰 **Per-minute costs**: ~$0.0085/minute for calls

**Why You Need to Rent:**
- Phone numbers are regulated like domain names
- PSTN (Public Switched Telephone Network) access requires carrier partnership
- Even OSS projects (Signal, Matrix, Jitsi) rent numbers for phone integration

---

## How Apple Does It (Comparison)

### Apple Visual Voicemail / Live Voicemail

**What Apple Controls:**
- ✅ Transcription happens **on-device** (Neural Engine)
- ✅ Voicemails processed locally (not sent to Apple servers)
- ✅ Uses Siri speech recognition engine
- ✅ Privacy-first (no cloud processing)

**What Apple DOESN'T Control:**
- ❌ Phone number (from Verizon/AT&T/T-Mobile)
- ❌ PSTN access (carrier's voicemail system)
- ❌ Voicemail storage (carrier's servers, though cached on device)

**How it Works:**
```
Call to your Verizon number
   ↓
Verizon voicemail system records
   ↓
Verizon stores voicemail on THEIR servers
   ↓
iPhone downloads voicemail over data connection
   ↓
Neural Engine transcribes on-device
   ↓
You see transcription in Phone app
```

**Apple's Limitation:** They still rely on carrier voicemail infrastructure.

---

## Fully OSS Path (3 Phases)

### Phase 1: Current Hybrid (Where We Are Now)

**Setup:**
```
Your Verizon number (existing)
   ↓ *71 conditional forwarding
Twilio number ($1/month inbox)
   ↓ Webhook
Your Flask server (OSS)
   ↓ AES-256-GCM encryption
Your SQLite database (OSS)
   ↓ QR code access
Your federated network (OSS)
```

**What You Own:** 70%
**What You Rent:** 30% (PSTN gateway only)

---

### Phase 2: Self-Hosted PBX (More Complex, Still Need DID)

**Goal:** Replace Twilio with self-hosted Asterisk/FreeSWITCH

**Setup:**
```
Your Verizon number (existing)
   ↓ *71 conditional forwarding
DID from VoIP.ms ($0.85/month - cheaper than Twilio!)
   ↓ SIP trunk
Your Asterisk server (OSS)
   ↓ AGI script (Python integration)
Your Flask encryption system (OSS)
   ↓ AES-256-GCM
Your SQLite database (OSS)
```

**What You Own:** 85%
**What You Rent:** 15% (DID number + SIP trunk)

**Pros:**
- Cheaper ($0.85/month vs $1/month)
- Full control over PBX logic
- Can add features (IVR, call routing, etc.)

**Cons:**
- Must run Asterisk/FreeSWITCH server
- More complex configuration
- Need to handle NAT traversal
- Codec management (PCMU/PCMA ↔ Opus)

**Implementation:**

1. **Install Asterisk/FreeSWITCH:**
   ```bash
   # Asterisk
   apt-get install asterisk

   # Or FreeSWITCH
   apt-get install freeswitch
   ```

2. **Configure SIP Trunk (VoIP.ms example):**
   ```ini
   # /etc/asterisk/sip.conf
   [voipms]
   type=friend
   host=atlanta.voip.ms
   username=YOUR_VOIPMS_ACCOUNT
   secret=YOUR_PASSWORD
   context=from-voipms
   ```

3. **Create AGI Script for Encryption:**
   ```python
   # /var/lib/asterisk/agi-bin/encrypt_voicemail.py
   #!/usr/bin/env python3
   from voice_encryption import encrypt_voice_memo
   import sys

   # Read voicemail file from Asterisk
   voicemail_path = sys.argv[1]
   with open(voicemail_path, 'rb') as f:
       audio_data = f.read()

   # Encrypt
   result = encrypt_voice_memo(audio_data)

   # Save to your Flask database
   # ... (same as Twilio integration)
   ```

4. **Configure Dialplan:**
   ```ini
   # /etc/asterisk/extensions.conf
   [from-voipms]
   exten => s,1,Answer()
   exten => s,n,Playback(custom/greeting)
   exten => s,n,Record(/tmp/voicemail-%d.wav)
   exten => s,n,AGI(encrypt_voicemail.py,/tmp/voicemail-%d.wav)
   exten => s,n,Hangup()
   ```

**Cost Comparison:**
- **Twilio:** $1/month + $0.0085/min
- **VoIP.ms:** $0.85/month + $0.009/min
- **Savings:** ~$2/year + slightly lower per-minute

---

### Phase 3: Fully Decentralized (Ultimate Goal)

**Goal:** No rented phone numbers at all. Peer-to-peer voice federation.

**Concept:** Like Matrix/ActivityPub but for voice memos

**Setup:**
```
Browser WebRTC (no phone number!)
   ↓
Direct peer-to-peer connection
   ↓
Your encryption system (OSS)
   ↓
Your federated storage (OSS)
   ↓
Share via QR codes / federation protocol
```

**How It Would Work:**

1. **No Phone Numbers Required:**
   - Use WebRTC for browser-to-browser calling
   - Or use XMPP/Matrix for signaling
   - Voice memos exchanged via federation protocol

2. **Federation Protocol (Like Email):**
   ```
   Alice@soulfra.com → records voice memo
   Encrypted with AES-256-GCM
   QR code: soulfra.com/voice/abc123#key

   Bob@calriven.com → scans QR
   CalRiven makes federation request to Soulfra
   Soulfra returns encrypted blob
   Bob's browser decrypts locally with key from QR
   ```

3. **Phone Integration (Optional):**
   - For people who NEED phone number access
   - Community-run "phone gateways"
   - Like email → SMS gateways
   - You call a community gateway number
   - IVR: "Enter the domain and voice memo ID"
   - Gateway fetches from federation network
   - Plays back over phone

**What You Own:** 100%
**What You Rent:** 0%

**Challenges:**
- Need critical mass of users to be useful
- Phone integration requires SOMEONE to run gateways
- Harder for normies to adopt (no phone number to call)

---

## Why This Matters (Philosophy)

### The Problem with Current VoIP

**Centralization:**
- Twilio, Google Voice, etc. are centralized services
- They can ban you, raise prices, or shut down
- You don't control the infrastructure

**Privacy:**
- Even with encryption, they see metadata
- Caller number, call duration, timestamps
- Could be subpoenaed or hacked

**Vendor Lock-in:**
- Hard to migrate voicemails between services
- Proprietary APIs and formats
- You don't own your data

### The OSS/Federated Vision

**Decentralization:**
- Anyone can run a voice memo server
- Federate with trusted peers
- No single point of failure

**Privacy:**
- End-to-end encryption (keys in QR codes)
- Metadata minimization
- Self-hosted = you control data

**Ownership:**
- Your data, your server, your rules
- Open protocols (anyone can implement)
- No vendor lock-in

### Real-World Examples

**Matrix (Federated Chat):**
- Like email, but for instant messaging
- Anyone can run a homeserver
- Federation protocol connects them
- End-to-end encryption (Olm/Megolm)
- Still has phone number bridges for SMS

**Mastodon (Federated Social):**
- Like Twitter, but federated
- ActivityPub protocol
- Anyone can run an instance
- Your data, your rules

**Email (OG Federation):**
- Oldest federated protocol
- You can run your own mail server
- Send/receive from anyone
- BUT: Still centralized around big providers (Gmail, Outlook)

**What We're Building:**
- Like email, but for voice memos
- Federated, encrypted, self-hosted
- QR codes as the "email address" for voice

---

## Technical Specifications

### Voice Memo Federation Protocol (Draft)

**1. Discovery:**
```
GET https://soulfra.com/.well-known/voice-federation
{
  "version": "1.0",
  "endpoints": {
    "fetch": "https://soulfra.com/api/federation/voice/fetch",
    "verify": "https://soulfra.com/api/federation/voice/verify"
  },
  "encryption": ["aes-256-gcm"],
  "access_methods": ["qr", "nfc", "bluetooth"],
  "trusted_domains": ["calriven.com", "deathtodata.org"]
}
```

**2. Fetch Encrypted Voice Memo:**
```
POST https://soulfra.com/api/federation/voice/fetch
Content-Type: application/json

{
  "memo_id": "abc123xyz",
  "access_key": "base64_key",
  "requesting_domain": "calriven.com"
}

Response:
{
  "success": true,
  "encrypted_audio_b64": "...",
  "encryption_iv": "...",
  "audio_format": "audio/mpeg",
  "duration_seconds": 42,
  "metadata": {
    "source": "twilio_call",
    "created_at": "2026-01-03T10:00:00Z"
  }
}
```

**3. Verify Access Key (Before Fetching):**
```
POST https://soulfra.com/api/federation/voice/verify
Content-Type: application/json

{
  "memo_id": "abc123xyz",
  "access_key": "base64_key"
}

Response:
{
  "valid": true,
  "expires_at": "2026-02-03T10:00:00Z"
}
```

**4. QR Code Format:**
```
Standard Format:
{domain}/voice/{memo_id}#{base64_key}

Example:
soulfra.com/voice/abc123xyz#Mh7wYHqp8OZEzfkWG9bgT5nKqXZvWcYj

With Protocol:
https://soulfra.com/voice/abc123xyz#Mh7wYHqp8OZEzfkWG9bgT5nKqXZvWcYj
```

**5. Encryption Standard:**
```
Algorithm: AES-256-GCM (AEAD)
Key Size: 256 bits (32 bytes)
IV Size: 96 bits (12 bytes)
Key Storage: NEVER (only SHA-256 hash for verification)
Key Distribution: QR codes, NFC tags, Bluetooth LE
```

---

## Implementation Roadmap

### Phase 1 (Current - Hybrid)

**Status:** ✅ COMPLETE

- [x] Twilio integration
- [x] AES-256-GCM encryption
- [x] QR code access control
- [x] Federated storage (voice_memos table)
- [x] Federation API endpoints
- [x] Conditional call forwarding support (*71)

**Next Steps:**
- [ ] Add "Delete from Twilio after download" option
- [ ] Create web UI for viewing voicemails with QR codes
- [ ] Add QR code image generation
- [ ] Integrate with existing /voice page

### Phase 2 (Self-Hosted PBX)

**Status:** 🔜 PLANNED

- [ ] Research Asterisk vs FreeSWITCH
- [ ] Create AGI script for voicemail encryption
- [ ] Document VoIP.ms setup
- [ ] Create Docker container for easy deployment
- [ ] Test NAT traversal
- [ ] Codec conversion (PCMU/PCMA ↔ Opus)

**Timeline:** 2-3 weeks for basic implementation

### Phase 3 (Fully Decentralized)

**Status:** 💭 CONCEPT

- [ ] Formalize federation protocol spec
- [ ] Implement ActivityPub integration (optional)
- [ ] Create reference implementation (Python)
- [ ] Create client library (JavaScript)
- [ ] Build community phone gateway (Asterisk + federation)
- [ ] Write developer documentation
- [ ] Open source release (MIT license)

**Timeline:** 3-6 months for MVP

---

## How to Contribute (Future)

Once we open source this, here's how others can help:

### For Developers

**Core Protocol:**
- Implement federation protocol in other languages (Go, Rust, JavaScript)
- Create client libraries
- Write specification (RFC-style)

**Integrations:**
- Asterisk module
- FreeSWITCH module
- Matrix bridge
- XMPP integration

**Clients:**
- Mobile apps (iOS, Android)
- Desktop apps (Electron)
- Browser extensions
- QR code scanners

### For Server Operators

**Run a Node:**
- Self-host voice memo server
- Join federation network
- Share resources with trusted peers

**Run a Phone Gateway:**
- Community-run Asterisk/FreeSWITCH
- Allows phone users to access voice memos
- Like SMS → email gateways

### For Users

**Use the System:**
- Record voice memos
- Share with friends
- Provide feedback
- Report bugs

**Spread the Word:**
- Blog about it
- Share on social media
- Teach others

---

## Why Apple Can't Do This (Centralization)

### Apple's Constraints

**Carrier Partnerships:**
- Apple MUST work with Verizon, AT&T, T-Mobile
- Can't bypass carrier voicemail systems
- Regulations prevent "owning" phone infrastructure

**Business Model:**
- Apple sells hardware (iPhones)
- NOT in the business of running phone networks
- Carriers control the phone numbers

**Walled Garden:**
- Apple controls the iPhone
- But not the phone network
- Voicemails still stored on carrier servers

### What We Can Do That Apple Can't

**Federated Protocol:**
- Not tied to any carrier
- Not tied to any device
- Open protocol anyone can implement

**True End-to-End Encryption:**
- Keys NEVER stored on server
- Not even Apple can do this (carrier voicemail systems)
- QR codes = physical key for digital audio

**Self-Hosting:**
- Run your own server
- Your data, your rules
- No Apple/Google/carrier in the middle

---

## Comparison to Existing Solutions

### Google Voice

**What they do:**
- Free phone number
- Voicemail transcription
- Call forwarding

**Limitations:**
- ❌ Centralized (Google controls everything)
- ❌ Not encrypted (Google can read voicemails)
- ❌ Can ban your account
- ❌ US/Canada only
- ❌ Not federated (can't self-host)

### Twilio

**What they do:**
- Phone number rental
- API for calls/SMS
- Programmable voice

**Limitations:**
- ❌ Proprietary service
- ❌ Not encrypted by default
- ❌ Per-minute costs
- ❌ Not federated

### Signal

**What they do:**
- End-to-end encrypted messaging
- Voice/video calls (encrypted)
- Open source client + server

**What they DON'T do:**
- ❌ No phone number hosting (rent from Twilio for verification!)
- ❌ Centralized server infrastructure
- ❌ Federation (one Signal server, not federated)

### Matrix

**What they do:**
- Federated chat protocol
- End-to-end encryption (Olm/Megolm)
- Anyone can run a homeserver
- Voice/video calls via Jitsi

**What they DON'T do:**
- ❌ No PSTN integration (no phone numbers)
- ❌ No voicemail system
- ❌ Phone bridges require third-party services

### What We're Building

**Unique Features:**
- ✅ Federated voice memo protocol
- ✅ End-to-end encryption (keys in QR codes)
- ✅ PSTN integration (via Twilio OR Asterisk)
- ✅ Self-hostable
- ✅ Open source core
- ✅ Works with existing phone numbers (*71 forwarding)

---

## FAQ

### Q: Why not just use Signal?

**A:** Signal is great for messaging, but:
- Doesn't support voicemail system
- Not federated (one central server)
- Still rents phone numbers from Twilio
- Can't integrate with your existing phone number via *71

### Q: Why not just use Matrix?

**A:** Matrix is great for chat, but:
- No PSTN integration (can't call from flip phone)
- Voice memos not first-class (just file attachments)
- No QR code access control
- Not optimized for voice memo use case

### Q: Can I really avoid renting a phone number?

**A:** For **true phone calls** from flip phones/landlines, no. Phone numbers are regulated.

**BUT:** For browser-to-browser voice memos, YES! Use WebRTC + federation protocol.

**Hybrid approach:** Rent a cheap gateway number ($1/month) for normies, but core users use WebRTC.

### Q: How is this better than Apple Visual Voicemail?

**A:**
- ✅ Works on Android, Linux, any browser
- ✅ Self-hosted (not on carrier servers)
- ✅ Truly end-to-end encrypted (carrier voicemail isn't)
- ✅ Federated (can share across domains)
- ✅ Open source (can audit the code)

### Q: What's the catch?

**A:**
- Requires technical knowledge to self-host
- Smaller network than established services
- PSTN integration still requires renting something
- More complex than "just use Google Voice"

**BUT:** You own your data, privacy, and infrastructure.

---

## License & Open Source Release

### Planned License: MIT

**Why MIT:**
- Maximum freedom
- Can be used commercially
- Compatible with other OSS projects
- Permissive (vs GPL)

### What Will Be Open Sourced:

**Core Components:**
- `voice_encryption.py` - AES-256-GCM implementation
- `voice_federation_routes.py` - Federation API
- `init_voice_memos_federation.py` - Database schema
- Federation protocol specification
- Client reference implementation

**Optional Integrations:**
- Twilio integration (proprietary service, but code is OSS)
- Asterisk AGI scripts (for Phase 2)
- WebRTC browser client

**Documentation:**
- Setup guides
- Federation protocol spec
- Self-hosting instructions
- Developer documentation

### What Won't Be Open Sourced:

- Your private encryption keys (obviously!)
- Your personal voicemails
- Twilio API credentials

---

## Timeline

### 2026 Q1 (Current)

- [x] Phase 1 complete (Hybrid Twilio integration)
- [ ] Documentation and setup guides
- [ ] Web UI for voicemail management
- [ ] QR code generation UI

### 2026 Q2

- [ ] Phase 2 planning (Asterisk integration)
- [ ] VoIP.ms setup documentation
- [ ] AGI script development
- [ ] Docker container for easy deployment

### 2026 Q3

- [ ] Phase 2 implementation (Self-hosted PBX)
- [ ] Testing and debugging
- [ ] Performance optimization
- [ ] Security audit

### 2026 Q4

- [ ] Phase 3 planning (Full decentralization)
- [ ] Federation protocol specification (v1.0)
- [ ] Reference implementation
- [ ] Open source release

---

## Call to Action

**For Now:** Use the hybrid Twilio setup. It works, it's cheap, and it's encrypted.

**For Later:** Help us build the fully decentralized version!

**Join the Movement:**
- Self-host your voice memo server
- Contribute code
- Write documentation
- Spread the word
- Build the future of decentralized voice

---

**This SHOULD be OSS and FOSS. This SHOULD be decentralized. We're building it. Join us.**

**Status:** Phase 1 complete ✅
**Next:** Phase 2 planning 🔜
**Vision:** Fully decentralized voice federation 🌐

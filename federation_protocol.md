# Federation Protocol - Brand-to-Brand Communication

Like email servers, each brand instance can communicate with other brand instances. This creates a decentralized network of AI-powered brands.

## 🎯 Overview

**Federation** means different brand instances can:
- Send messages to each other
- Share knowledge and context
- Forward queries to specialized brands
- Build trust networks

Like email: `alice@gmail.com` ↔ `bob@protonmail.com`

With brands: `user@soulfra.com` ↔ `user@deathtodata.org`

## 🏗️ Architecture

### Simple Federation (HTTP-based)

```
Brand A (soulfra.com)          Brand B (deathtodata.org)
    ↓                                  ↓
Ollama Instance                    Ollama Instance
    ↓                                  ↓
Web Server (Port 8080)             Web Server (Port 8081)
    ↓                                  ↓
    └─────── HTTP POST ──────────────→┘
            (federation message)
```

### Components

1. **Brand Identity**
   - Domain name (e.g., `soulfra.com`)
   - Public key for verification
   - Federation endpoint (e.g., `/api/federation/receive`)

2. **Message Format**
   - JSON-based messages
   - Signed with sender's private key
   - Encrypted for recipient's public key (optional)

3. **Discovery**
   - DNS TXT records for federation info
   - Well-known URLs (`/.well-known/federation`)
   - Manual peer configuration

4. **Trust**
   - Peer whitelist (trust specific domains)
   - Public key verification
   - Rate limiting and abuse prevention

## 📋 Protocol Specification

### Message Format

```json
{
  "version": "1.0",
  "from": {
    "domain": "soulfra.com",
    "brand": "Soulfra",
    "user_id": "user123"
  },
  "to": {
    "domain": "deathtodata.org",
    "brand": "DeathToData",
    "context": "privacy_query"
  },
  "message": {
    "type": "chat",
    "content": "How can I encrypt my data?",
    "context": {
      "conversation_id": "abc123",
      "previous_messages": []
    }
  },
  "metadata": {
    "timestamp": "2025-12-28T12:34:56Z",
    "signature": "BASE64_SIGNATURE",
    "public_key": "BASE64_PUBLIC_KEY"
  }
}
```

### API Endpoints

#### 1. **Receive Federation Message**

```http
POST /api/federation/receive
Content-Type: application/json
Authorization: Bearer FEDERATION_TOKEN

{
  "version": "1.0",
  "from": {...},
  "to": {...},
  "message": {...}
}
```

**Response**:
```json
{
  "status": "received",
  "message_id": "msg_xyz789",
  "response": {
    "content": "AI-generated response from receiving brand"
  }
}
```

#### 2. **Send Federation Message**

```http
POST /api/federation/send
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "target_domain": "deathtodata.org",
  "message": "How do I protect my privacy?"
}
```

**Response**:
```json
{
  "status": "sent",
  "remote_response": {
    "content": "Response from DeathToData's Ollama"
  }
}
```

#### 3. **Discover Federation Peers**

```http
GET /.well-known/federation
```

**Response**:
```json
{
  "brand": "Soulfra",
  "domain": "soulfra.com",
  "version": "1.0",
  "endpoints": {
    "receive": "https://soulfra.com/api/federation/receive",
    "send": "https://soulfra.com/api/federation/send"
  },
  "capabilities": ["chat", "knowledge_share", "context_forward"],
  "public_key": "BASE64_PUBLIC_KEY",
  "trusted_peers": [
    "deathtodata.org",
    "calriven.com"
  ]
}
```

## 🔐 Security

### Authentication Methods

**Option 1: Shared Secret (Simple)**
```json
{
  "federation": {
    "enabled": true,
    "auth_type": "shared_secret",
    "trusted_peers": {
      "deathtodata.org": "SECRET_TOKEN_123"
    }
  }
}
```

**Option 2: Public Key Cryptography (Secure)**
```json
{
  "federation": {
    "enabled": true,
    "auth_type": "public_key",
    "private_key_path": "./keys/soulfra_private.pem",
    "public_key": "BASE64_PUBLIC_KEY",
    "trusted_peers": {
      "deathtodata.org": "BASE64_THEIR_PUBLIC_KEY"
    }
  }
}
```

**Option 3: OAuth 2.0 (Enterprise)**
```json
{
  "federation": {
    "enabled": true,
    "auth_type": "oauth2",
    "client_id": "soulfra_client",
    "client_secret": "SECRET",
    "token_endpoint": "https://auth.soulfra.com/oauth/token"
  }
}
```

### Message Signing

**Sign outgoing messages**:
```python
import json
import hmac
import hashlib
import base64

def sign_message(message, private_key):
    message_json = json.dumps(message, sort_keys=True)
    signature = hmac.new(
        private_key.encode(),
        message_json.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()
```

**Verify incoming messages**:
```python
def verify_message(message, signature, public_key):
    expected_signature = sign_message(message, public_key)
    return hmac.compare_digest(expected_signature, signature)
```

## 🚀 Implementation Example

### Python Flask Backend

```python
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Load federation config
with open('brand.json', 'r') as f:
    config = json.load(f)

TRUSTED_PEERS = config['federation']['trusted_peers']

@app.route('/api/federation/receive', methods=['POST'])
def receive_federation_message():
    """Receive message from another brand"""
    data = request.json

    # Verify sender is trusted
    sender_domain = data['from']['domain']
    if sender_domain not in TRUSTED_PEERS:
        return jsonify({'error': 'Untrusted peer'}), 403

    # Verify signature (if using public key auth)
    # verify_message(data, data['metadata']['signature'], TRUSTED_PEERS[sender_domain])

    # Process message with local Ollama
    user_message = data['message']['content']
    ollama_response = call_ollama(user_message)

    return jsonify({
        'status': 'received',
        'response': {
            'content': ollama_response,
            'brand': config['name']
        }
    })

@app.route('/api/federation/send', methods=['POST'])
def send_federation_message():
    """Send message to another brand"""
    data = request.json
    target_domain = data['target_domain']

    if target_domain not in TRUSTED_PEERS:
        return jsonify({'error': 'Untrusted peer'}), 403

    # Build federation message
    message = {
        'version': '1.0',
        'from': {
            'domain': config['federation']['domain'],
            'brand': config['name']
        },
        'to': {
            'domain': target_domain
        },
        'message': {
            'type': 'chat',
            'content': data['message']
        }
    }

    # Send to peer
    peer_url = f"https://{target_domain}/api/federation/receive"
    response = requests.post(peer_url, json=message)

    return jsonify(response.json())

def call_ollama(prompt):
    """Call local Ollama instance"""
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': config['ollama']['default_model'],
            'prompt': prompt,
            'stream': False
        }
    )
    return response.json()['response']

if __name__ == '__main__':
    app.run(port=8080)
```

### JavaScript Frontend (Static HTML)

```javascript
// Send message to federated brand
async function sendFederatedMessage(targetDomain, message) {
    const response = await fetch('/api/federation/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            target_domain: targetDomain,
            message: message
        })
    });

    const data = await response.json();
    return data.response.content;
}

// Example usage
async function askDeathToData(question) {
    const answer = await sendFederatedMessage('deathtodata.org', question);
    console.log('DeathToData says:', answer);
}

// In chat interface
if (message.startsWith('@deathtodata')) {
    const question = message.replace('@deathtodata', '').trim();
    const answer = await askDeathToData(question);
    addMessage('assistant', `DeathToData: ${answer}`);
}
```

## 🌐 Use Cases

### 1. **Specialized Routing**

Route questions to expert brands:
```javascript
// User asks about privacy
if (query.includes('privacy') || query.includes('encrypt')) {
    // Forward to DeathToData (privacy expert)
    response = await sendFederatedMessage('deathtodata.org', query);
}

// User asks about architecture
if (query.includes('architecture') || query.includes('system design')) {
    // Forward to CalRiven (architecture expert)
    response = await sendFederatedMessage('calriven.com', query);
}
```

### 2. **Knowledge Sharing**

Brands share knowledge:
```javascript
// Soulfra learns from DeathToData
const privacyKnowledge = await sendFederatedMessage(
    'deathtodata.org',
    'What are the latest privacy best practices?'
);

// Soulfra incorporates this into context
context.push({
    role: 'system',
    content: `Privacy best practices from DeathToData: ${privacyKnowledge}`
});
```

### 3. **Consensus Building**

Multiple brands collaborate:
```javascript
// Ask all trusted peers
const responses = await Promise.all([
    sendFederatedMessage('deathtodata.org', question),
    sendFederatedMessage('calriven.com', question),
    sendFederatedMessage('theauditor.io', question)
]);

// Synthesize consensus
const consensus = await callOllama(`
    These are responses from different experts:
    - DeathToData: ${responses[0]}
    - CalRiven: ${responses[1]}
    - TheAuditor: ${responses[2]}

    Synthesize a consensus answer.
`);
```

### 4. **Decentralized Network**

Build a network like Mastodon:
```
soulfra.com ←→ deathtodata.org
     ↕              ↕
calriven.com ←→ theauditor.io
     ↕              ↕
yourbrand.com ←→ anotherbrand.com
```

Each brand is independent but can communicate.

## 📝 Setup Instructions

### 1. Enable Federation in `brand.json`

```json
{
  "federation": {
    "enabled": true,
    "domain": "yourbrand.com",
    "port": 8080,
    "trusted_peers": [
      "soulfra.com",
      "deathtodata.org"
    ],
    "auth_type": "shared_secret",
    "secrets": {
      "soulfra.com": "SECRET_TOKEN_1",
      "deathtodata.org": "SECRET_TOKEN_2"
    }
  }
}
```

### 2. Add Federation Endpoints

Create `federation_server.py`:
```python
# See Python Flask example above
```

### 3. Start Federation Server

```bash
python3 federation_server.py
```

### 4. Test Federation

```bash
# Send test message
curl -X POST http://localhost:8080/api/federation/send \
  -H "Content-Type: application/json" \
  -d '{
    "target_domain": "soulfra.com",
    "message": "Hello from my brand!"
  }'
```

### 5. Deploy with HTTPS

Federation requires HTTPS for security.

**Option 1: nginx + Let's Encrypt**
```nginx
server {
    listen 443 ssl;
    server_name yourbrand.com;

    ssl_certificate /etc/letsencrypt/live/yourbrand.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourbrand.com/privkey.pem;

    location /api/federation/ {
        proxy_pass http://localhost:8080;
    }
}
```

**Option 2: Cloudflare Tunnel**
```bash
cloudflared tunnel --url localhost:8080
```

## 🔒 Best Practices

1. **Always use HTTPS** for federation endpoints
2. **Verify signatures** on incoming messages
3. **Rate limit** federation requests (prevent abuse)
4. **Whitelist** trusted peers only
5. **Log** all federation activity for audit
6. **Timeout** long-running requests
7. **Validate** message format before processing
8. **Encrypt** sensitive data in messages

## 🆚 vs. Centralized Services

| Feature | Federation | Centralized |
|---------|------------|-------------|
| **Control** | You own your data | Company owns data |
| **Privacy** | Messages between peers | All data on central server |
| **Downtime** | One brand down ≠ all down | Central server down = all down |
| **Censorship** | Resistant | Vulnerable |
| **Scaling** | Distributed load | Central bottleneck |
| **Costs** | Each brand pays their own | Central company pays all |

## 📚 Examples

### Example 1: Privacy Query Routing

```javascript
// User: "How do I encrypt my files?"
// Soulfra recognizes this is a privacy question
// Soulfra forwards to DeathToData

const response = await sendFederatedMessage(
    'deathtodata.org',
    'How do I encrypt my files?'
);

// DeathToData's Ollama responds with privacy-focused answer
// Soulfra returns this to the user
```

### Example 2: Multi-Brand Consensus

```javascript
// User: "What's the best architecture for a chat app?"
// Soulfra asks multiple expert brands

const responses = await Promise.all([
    sendFederatedMessage('calriven.com', question),  // Architecture expert
    sendFederatedMessage('theauditor.io', question), // Testing expert
    sendFederatedMessage('soulfra.com', question)    // Security expert
]);

// Soulfra synthesizes answers
const final = await callOllama(`Synthesize: ${responses.join('\n')}`);
```

## 🌟 Future Extensions

1. **ActivityPub Integration** - Federate with Mastodon, PeerTube
2. **Matrix Bridge** - Connect to Matrix chat networks
3. **IPFS Storage** - Store messages on IPFS
4. **Blockchain Trust** - On-chain reputation system
5. **P2P Discovery** - No DNS, pure P2P with libp2p

---

**Generated 2025-12-28 by Soulfra**

# Soulfra Platform Documentation

**Building Your Own Privacy-First AI Platform**

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Customization Guide](#customization-guide)
4. [AI Model Training](#ai-model-training)
5. [Multi-Brand Setup](#multi-brand-setup)
6. [Deployment Strategies](#deployment-strategies)
7. [Advanced Features](#advanced-features)

---

## Platform Overview

### What Makes Soulfra Different?

**Traditional Platforms (WordPress, Medium, etc.):**
```
Your Content → Their Servers → Their AI → Their Data Mining
```

**Soulfra:**
```
Your Content → Your Machine → Your AI → Your Privacy
```

### Core Principles

1. **Privacy First**
   - All AI processing happens locally (Ollama)
   - No external API calls
   - No data collection
   - Your keys, your identity, period

2. **Static + Dynamic Hybrid**
   - Blog = Static HTML (GitHub Pages, free)
   - Chat = Local Flask server (private)
   - Best of both worlds

3. **Fork-Friendly OSS**
   - One codebase, infinite brands
   - Customize everything
   - Train AI on your content
   - Own your platform

---

## Architecture Deep Dive

### System Components

```
┌──────────────────────────────────────────────────────┐
│                 SOULFRA PLATFORM                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐        ┌─────────────┐            │
│  │   PUBLIC    │        │   PRIVATE   │            │
│  │   (Static)  │        │  (Dynamic)  │            │
│  └─────────────┘        └─────────────┘            │
│         │                      │                    │
│         ▼                      ▼                    │
│  ┌─────────────┐        ┌─────────────┐            │
│  │ GitHub      │        │ Flask App   │            │
│  │ Pages       │        │ (localhost) │            │
│  └─────────────┘        └─────────────┘            │
│         │                      │                    │
│         │                      ▼                    │
│         │               ┌─────────────┐            │
│         │               │ SQLite DB   │            │
│         │               └─────────────┘            │
│         │                      │                    │
│         │                      ▼                    │
│         │               ┌─────────────┐            │
│         │               │ Ollama AI   │            │
│         │               └─────────────┘            │
│         │                                           │
│         └──────── Generated From ───────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data Flow

#### Publishing Workflow

```
1. Write Post (Flask UI or SQL)
        │
        ▼
2. Save to SQLite
        │
        ▼
3. Run publish_to_github.py
        │
        ├─► Generate HTML
        ├─► Generate RSS Feed
        ├─► Create Index
        │
        ▼
4. Push to GitHub
        │
        ▼
5. GitHub Pages Deploys
        │
        ▼
6. Public Blog Live!
```

#### Chat Workflow

```
1. User visits /chat
        │
        ▼
2. Flask authenticates (QR or Dev Mode)
        │
        ▼
3. User sends message
        │
        ▼
4. Context Manager loads relevant posts
        │
        ▼
5. Ollama processes query (LOCAL!)
        │
        ▼
6. Response returned to user
        │
        ▼
7. Knowledge Extractor learns from conversation
        │
        ▼
8. AI gets smarter (based on YOUR content)
```

---

## Customization Guide

### 1. Brand Identity

Edit `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/dev_config.py`:

```python
# Your Brand Settings
BRAND_NAME = "YourBrand"
BRAND_TAGLINE = "Your unique tagline"

# Color Scheme
BRAND_COLORS = {
    'primary': '#667eea',      # Main brand color
    'secondary': '#764ba2',    # Secondary accent
    'accent': '#e74c3c'        # Call-to-action color
}

# Development Settings
DEV_MODE = True                # Set to False for production
SKIP_QR_AUTH = True            # Skip QR auth in dev mode
LOCALHOST_ONLY = True          # Only accept localhost connections
VERBOSE_LOGGING = True         # Detailed logs
```

**Example: Nature Blog**

```python
BRAND_NAME = "WildThoughts"
BRAND_TAGLINE = "Connecting with nature, one thought at a time"

BRAND_COLORS = {
    'primary': '#2ecc71',      # Forest green
    'secondary': '#27ae60',    # Dark green
    'accent': '#f39c12'        # Sunset orange
}
```

### 2. Custom Domain

#### Step 1: Update `publish_to_github.py`

Find this line:

```python
BASE_URL = "https://soulfra.github.io/soulfra/"
```

Change to:

```python
BASE_URL = "https://yourdomain.com/"
```

#### Step 2: Create CNAME File

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/github-repos/soulfra

echo "yourdomain.com" > CNAME

git add CNAME
git commit -m "Add custom domain"
git push origin main
```

#### Step 3: Configure DNS

At your domain registrar (Namecheap, GoDaddy, etc.):

```
Type: CNAME
Name: @ (or www)
Value: yourusername.github.io
TTL: 3600
```

Wait 5-60 minutes for DNS propagation.

#### Step 4: Enable HTTPS in GitHub

1. Go to repo Settings → Pages
2. Check "Enforce HTTPS"
3. Done!

Your site is now at `https://yourdomain.com`

### 3. AI Personality

The AI learns from your blog posts automatically, but you can customize the base personality.

Edit `context_manager.py`:

```python
SYSTEM_PROMPTS = {
    'soulfra-model': """
        You are a privacy-focused AI assistant.
        You believe in: [YOUR VALUES HERE]
        You write in: [YOUR STYLE HERE]
    """,

    'custom-model': """
        You are [YOUR CUSTOM PERSONA].
        Your expertise: [YOUR EXPERTISE].
        Your tone: [YOUR TONE].
    """
}
```

**Example: Tech Teacher Persona**

```python
'tech-teacher': """
    You are a patient, friendly tech educator.
    You explain complex topics simply.
    You use analogies and real-world examples.
    You encourage questions and curiosity.
    Your tone is warm, clear, and encouraging.
"""
```

### 4. Email Capture Integration

The blog includes an email capture form. Connect it to your backend:

In `publish_to_github.py`, find:

```html
<form action="https://api.soulfra.com/subscribe" method="POST">
```

Change to your endpoint:

```html
<form action="https://yourdomain.com/api/subscribe" method="POST">
```

**Option 1: Mailchimp**

```html
<form action="https://youraudience.us1.list-manage.com/subscribe/post?u=XXX&id=YYY" method="POST">
```

**Option 2: ConvertKit**

```html
<form action="https://app.convertkit.com/forms/YOUR_FORM_ID/subscriptions" method="POST">
```

**Option 3: Custom Flask Endpoint**

Create `/api/subscribe` route in `app.py`:

```python
@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')

    # Save to database
    db = get_db()
    db.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
    db.commit()

    return jsonify({'success': True})
```

---

## AI Model Training

### How Training Works

Soulfra uses **context-aware retrieval** + **knowledge extraction** to train AI on your content.

#### Phase 1: Content Indexing

When you publish posts, they're stored in SQLite:

```sql
posts
├── id
├── title
├── slug
├── content          ← AI reads this
├── author
└── published_at
```

#### Phase 2: Context Retrieval

When a user asks a question:

```python
# context_manager.py
def get_relevant_context(query):
    """Find posts related to user's question"""

    # Search posts for keywords
    results = db.execute("""
        SELECT content FROM posts
        WHERE content LIKE ? OR title LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    # Return top 3 matches
    return results[:3]
```

#### Phase 3: Ollama Processing

```python
# Build prompt with your content
prompt = f"""
Based on these posts from the blog:

{context_from_your_posts}

Answer this question:
{user_question}
"""

# Send to Ollama (LOCAL!)
response = ollama.chat(model='llama2', messages=[
    {'role': 'system', 'content': 'You are the blog author'},
    {'role': 'user', 'content': prompt}
])
```

#### Phase 4: Knowledge Extraction

After conversations, the system learns:

```python
# knowledge_extractor.py
def extract_from_conversation(user_msg, ai_response):
    """Learn from chat interactions"""

    # Identify key topics
    topics = extract_topics(user_msg, ai_response)

    # Store for future context
    db.execute("""
        INSERT INTO knowledge_base (topic, insight)
        VALUES (?, ?)
    """, (topics, ai_response))
```

### Training Your AI

#### Method 1: Write More Posts

The more you write, the smarter your AI becomes.

```bash
# Write posts about your expertise
python3 app.py
# Visit http://localhost:5001/admin

# Publish to database
# AI automatically indexes content
```

#### Method 2: Import Existing Content

```python
# import_content.py
import sqlite3

db = sqlite3.connect('soulfra.db')

# Import from your old blog
posts = [
    {'title': 'Old Post 1', 'content': '...'},
    {'title': 'Old Post 2', 'content': '...'},
]

for post in posts:
    db.execute("""
        INSERT INTO posts (title, slug, content, author, published_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (post['title'], slugify(post['title']), post['content'], 'You'))

db.commit()
```

#### Method 3: Fine-Tune Ollama Models

```bash
# Create Modelfile with your content
cat > Modelfile <<EOF
FROM llama2

SYSTEM You are a privacy-focused AI expert.

# Add your knowledge
PARAMETER context_window 4096
PARAMETER temperature 0.7
EOF

# Build custom model
ollama create my-custom-model -f Modelfile
```

---

## Multi-Brand Setup

Run multiple brands from one codebase.

### Architecture

```
soulfra/
├── brands/
│   ├── soulfra/
│   │   ├── config.py       # Soulfra settings
│   │   ├── posts.db        # Soulfra content
│   │   └── static/         # Soulfra assets
│   │
│   ├── deathtodata/
│   │   ├── config.py       # DeathToData settings
│   │   ├── posts.db        # DeathToData content
│   │   └── static/         # DeathToData assets
│   │
│   └── yourbrand/
│       ├── config.py
│       ├── posts.db
│       └── static/
│
├── app.py                  # Shared Flask app
└── publish_to_github.py    # Multi-brand publisher
```

### Implementation

#### 1. Create Brand Config

```python
# brands/yourbrand/config.py

BRAND_CONFIG = {
    'name': 'YourBrand',
    'tagline': 'Your tagline',
    'domain': 'yourbrand.com',
    'colors': {
        'primary': '#FF6B6B',
        'secondary': '#4ECDC4',
        'accent': '#FFE66D'
    },
    'ai_persona': 'yourbrand-assistant',
    'models': ['llama2', 'mistral'],
}
```

#### 2. Update `app.py` for Multi-Brand

```python
import os

# Detect brand from environment or subdomain
CURRENT_BRAND = os.environ.get('BRAND', 'soulfra')

# Load brand config
if CURRENT_BRAND == 'soulfra':
    from brands.soulfra.config import BRAND_CONFIG
elif CURRENT_BRAND == 'yourbrand':
    from brands.yourbrand.config import BRAND_CONFIG

# Use brand-specific database
DB_PATH = f'brands/{CURRENT_BRAND}/posts.db'
```

#### 3. Run Multiple Brands

```bash
# Terminal 1: Run Soulfra
export BRAND=soulfra
export PORT=5001
python3 app.py

# Terminal 2: Run YourBrand
export BRAND=yourbrand
export PORT=5002
python3 app.py
```

#### 4. Publish Multiple Brands

```bash
# Publish Soulfra
python3 publish_to_github.py --brand soulfra

# Publish YourBrand
python3 publish_to_github.py --brand yourbrand
```

---

## Deployment Strategies

### Strategy 1: GitHub Pages Only (Free)

**Best for:** Static blog, no chat

```bash
# Generate static site
python3 publish_to_github.py

# Push to GitHub
git push origin main

# Enable Pages in Settings
```

**Cost:** $0/month
**Speed:** Fast (CDN)
**Limitations:** No dynamic chat

### Strategy 2: Hybrid (Static + Local Chat)

**Best for:** Personal use, privacy

```bash
# Public blog on GitHub Pages
python3 publish_to_github.py
git push

# Private chat on localhost
python3 app.py
# Access at http://localhost:5001/chat
```

**Cost:** $0/month
**Speed:** Blog = Fast, Chat = Local
**Privacy:** Maximum (AI never leaves your machine)

### Strategy 3: Full Self-Host

**Best for:** Teams, custom domains, full control

```bash
# VPS (DigitalOcean, Linode, etc.)
ssh user@your-server.com

# Install dependencies
sudo apt install python3-pip nginx
pip3 install -r requirements.txt

# Install Ollama
curl https://ollama.ai/install.sh | sh

# Run Flask with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# Configure Nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5001;
    }
}
```

**Cost:** $5-20/month (VPS)
**Speed:** Depends on VPS
**Control:** Complete

### Strategy 4: Hybrid Cloud (Static + Cloud API)

**Best for:** Public chat, scaling

```bash
# Blog on GitHub Pages (free)
python3 publish_to_github.py

# Chat API on cloud (Railway, Render, Fly.io)
# Dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python3", "app.py"]
```

**Cost:** $5-15/month (cloud API)
**Speed:** Fast everywhere
**Scalability:** High

---

## Advanced Features

### 1. Voice Memos

Record voice notes that get transcribed and added to blog:

```python
# voice_routes.py (already exists)
@app.route('/voice')
def voice_recorder():
    return render_template('voice_recorder.html')

@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe():
    audio = request.files['audio']

    # Use Whisper (local) for transcription
    text = whisper.transcribe(audio)

    # Save as draft post
    db.execute("""
        INSERT INTO posts (title, content, status)
        VALUES (?, ?, 'draft')
    """, ('Voice Note', text))
```

### 2. QR Code Authentication

Secure access without passwords:

```python
# qr_routes.py (already exists)
import qrcode

@app.route('/login_qr')
def login_qr():
    # Generate unique token
    token = secrets.token_urlsafe(32)

    # Create QR code
    qr_url = f"https://yourdomain.com/auth?token={token}"
    qr = qrcode.make(qr_url)

    # Store session
    db.execute('INSERT INTO search_sessions (session_token) VALUES (?)', (token,))

    return render_template('qr_login.html', qr_code=qr)
```

### 3. Encrypted Cross-Domain Messaging

Send encrypted DMs between Soulfra instances:

```python
# messaging.py
from cryptography.fernet import Fernet

def send_encrypted_message(recipient_domain, message):
    # Encrypt with recipient's public key
    encrypted = encrypt(message, recipient_public_key)

    # Send to their domain
    requests.post(f'https://{recipient_domain}/api/receive', {
        'message': encrypted
    })
```

### 4. Client Onboarding

Auto-setup for new users:

```bash
# Clone your template
git clone https://github.com/yourusername/soulfra-template.git myblog

cd myblog

# Run setup wizard
python3 setup_wizard.py

# Wizard asks:
# - Brand name?
# - Tagline?
# - Colors?
# - Domain?

# Generates:
# - Custom config.py
# - Initial database
# - First blog post

# Deploy
python3 publish_to_github.py
```

---

## Next Steps

1. **Fork this repo** - Make it yours
2. **Customize branding** - Colors, name, tagline
3. **Write your first post** - Train your AI
4. **Deploy to GitHub Pages** - Free hosting
5. **Share with the world** - Or keep it private

**Questions? Issues?**

- Open an issue: https://github.com/soulfra/soulfra/issues
- Read the code: It's all open source
- Fork and customize: That's the point!

---

**Remember:**

- Your keys
- Your identity
- Your platform
- Period.

**Built with ❤️ for privacy-conscious creators who want to own their AI**

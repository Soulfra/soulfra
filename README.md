# Soulfra

**Privacy-First AI Platform**

> Your keys. Your identity. Period.

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://soulfra.github.io/soulfra/)
[![RSS Feed](https://img.shields.io/badge/RSS-Feed-orange)](https://soulfra.github.io/soulfra/feed.xml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🚀 What is Soulfra?

Soulfra is an **open-source, privacy-first AI platform** that combines:

- 📝 **Static Blog Publishing** (like WordPress, but better)
- 🤖 **Local AI Models** (powered by Ollama)
- 🔐 **Zero-Knowledge Architecture** (your data never leaves your machine)
- 🎨 **Multi-Brand Support** (one codebase, infinite identities)
- 📡 **RSS Feeds** (built-in syndication)

Unlike traditional platforms, Soulfra:
- ✅ Runs AI models **locally** (no API keys, no data mining)
- ✅ Generates **static sites** (fast, secure, free hosting via GitHub Pages)
- ✅ Trains AI on **your content** (build your own reasoning model from scratch)
- ✅ Supports **custom domains** (bring your own brand)

---

## 🎯 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed locally
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/soulfra/soulfra.git
cd soulfra
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python3 init_db.py
```

### 4. Pull Ollama Models

```bash
ollama pull llama2
ollama pull mistral
```

### 5. Run Development Server

```bash
python3 app.py
```

Visit: `http://localhost:5001/chat`

### 6. Publish Your Blog

```bash
python3 publish_to_github.py
```

This generates static HTML in `blog/` and pushes to GitHub Pages.

---

## 📖 How It Works

### Architecture

```
┌─────────────────┐
│   Your Browser  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Flask Server   │◄────►│  SQLite DB   │
│  (localhost)    │      │  (posts,     │
└────────┬────────┘      │   sessions)  │
         │               └──────────────┘
         ▼
┌─────────────────┐
│  Ollama Models  │
│  (local AI)     │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Static HTML    │──►  GitHub Pages
│  (blog/)        │     (public site)
└─────────────────┘
```

### Three Modes

1. **Development Mode** (`DEV_MODE=true`)
   - Localhost only
   - No QR authentication
   - Verbose logging
   - Perfect for testing

2. **Production Mode** (`DEV_MODE=false`)
   - QR code authentication
   - Multi-user sessions
   - Privacy-first auth

3. **Static Mode** (GitHub Pages)
   - Pure HTML/CSS
   - No server required
   - Fast, secure, free

---

## 🛠️ Customization

### Change Your Brand

Edit `dev_config.py`:

```python
BRAND_NAME = "YourBrand"
BRAND_TAGLINE = "Your tagline here"
BRAND_COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'accent': '#e74c3c'
}
```

### Add Your Domain

1. Update `publish_to_github.py`:

```python
BASE_URL = "https://yourdomain.com"
```

2. Create `CNAME` file:

```bash
echo "yourdomain.com" > CNAME
git add CNAME
git commit -m "Add custom domain"
git push
```

3. Configure DNS:

```
Type: CNAME
Name: @
Value: yourusername.github.io
```

### Train AI on Your Content

The platform automatically trains AI models on your blog posts:

1. Write posts in the admin panel
2. Publish to database
3. Ollama indexes content
4. AI learns your writing style

**Example:**

```bash
# Visit chat interface
http://localhost:5001/chat

# Ask: "What's my perspective on privacy?"
# AI responds based on YOUR blog posts
```

---

## 📝 Publishing Workflow

### 1. Write a Post

Via admin panel or directly in database:

```sql
INSERT INTO posts (title, slug, content, author, published_at)
VALUES (
    'My First Post',
    'my-first-post',
    'Hello world! This is my content...',
    'Your Name',
    datetime('now')
);
```

### 2. Generate Static Site

```bash
python3 publish_to_github.py
```

**What happens:**
- ✅ Loads posts from SQLite
- ✅ Generates HTML for each post
- ✅ Creates blog index with navigation
- ✅ Generates RSS feed
- ✅ Pushes to GitHub

### 3. Deploy to GitHub Pages

```bash
# One-time setup
# Go to: Settings → Pages → Source: /docs (or root)
# Or push blog/ directory

git push origin main
```

Your blog is now live at:
- `https://yourusername.github.io/yourrepo/`
- `https://yourdomain.com` (if custom domain configured)

---

## 🎨 Features

### Blog Publishing

- ✅ Markdown support
- ✅ Author attribution
- ✅ Published dates
- ✅ RSS feed generation
- ✅ Email capture form
- ✅ Responsive design

### AI Chat

- ✅ Multiple Ollama models
- ✅ Context-aware conversations
- ✅ Session persistence
- ✅ Knowledge extraction from chats
- ✅ Privacy-first (local processing)

### Multi-Brand

- ✅ One codebase, many brands
- ✅ Custom colors per brand
- ✅ Custom taglines
- ✅ Separate AI personalities

### Privacy

- ✅ Zero external API calls
- ✅ Local AI processing
- ✅ No data collection
- ✅ QR code authentication (optional)
- ✅ Session-based access

---

## 🔧 Development

### Project Structure

```
soulfra/
├── app.py                    # Main Flask server
├── chat_routes.py            # Chat interface
├── publish_to_github.py      # Static site generator
├── dev_config.py             # Development settings
├── database.py               # SQLite helpers
├── context_manager.py        # Ollama integration
├── templates/
│   ├── chat.html
│   └── ...
├── blog/                     # Generated static files
│   ├── index.html
│   ├── posts/
│   └── ...
└── feed.xml                  # RSS feed
```

### Key Files

- **`publish_to_github.py`** - Generates static HTML from database posts
- **`chat_routes.py`** - Chat interface with Ollama integration
- **`dev_config.py`** - Development mode settings (skip auth, verbose logs)
- **`context_manager.py`** - Handles Ollama model selection and context
- **`knowledge_extractor.py`** - Extracts insights from conversations

### Running Tests

```bash
# Test development config
python3 dev_config.py

# Test static generation
python3 publish_to_github.py

# Test chat interface
curl http://localhost:5001/chat
```

---

## 🌐 Deployment Options

### Option 1: GitHub Pages (Recommended)

**Pros:**
- Free
- Fast CDN
- SSL included
- Custom domains supported

**Setup:**
1. Push blog/ directory to GitHub
2. Enable Pages in Settings
3. Done!

### Option 2: Self-Host (Flask)

**Pros:**
- Full control
- Dynamic features
- Private network option

**Setup:**
```bash
# Production mode
export DEV_MODE=false
python3 app.py
```

### Option 3: Hybrid (Static + API)

**Pros:**
- Static site for blog (fast)
- Flask API for chat (dynamic)

**Setup:**
1. GitHub Pages for blog
2. Self-host Flask for `/chat`
3. CORS configuration

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repo
2. Create feature branch (`git checkout -b feature/awesome`)
3. Commit changes (`git commit -m 'Add awesome feature'`)
4. Push to branch (`git push origin feature/awesome`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🔗 Links

- **Live Demo:** https://soulfra.github.io/soulfra/
- **RSS Feed:** https://soulfra.github.io/soulfra/feed.xml
- **Documentation:** See [PLATFORM.md](PLATFORM.md)
- **Issues:** https://github.com/soulfra/soulfra/issues

---

## 💡 Philosophy

Soulfra is built on three principles:

1. **Privacy First**
   - Your data stays on your machine
   - No tracking, no analytics, no external APIs
   - You own your keys, your identity, your content

2. **Open Source**
   - Transparent code
   - Community-driven
   - Fork-friendly architecture

3. **AI for Good**
   - Local models (no data mining)
   - Train on YOUR content
   - Build reasoning models from scratch

---

**Built with ❤️ for privacy-conscious creators**

Want to build your own AI platform? Fork this repo and make it yours.

Questions? Open an issue or PR.

#!/usr/bin/env python3
"""
Create Tutorial Blog Post

Creates a comprehensive "Hello World" tutorial post demonstrating all Soulfra features
"""

import sqlite3
from datetime import datetime

# Tutorial content
TUTORIAL_CONTENT = """# Welcome to Soulfra: Your Complete Guide

**Hello! 👋** You've just discovered a powerful, zero-dependency blogging and AI platform. This tutorial will walk you through everything Soulfra can do.

---

## 🎮 Interactive Playground

The fastest way to explore Soulfra is through the **[Playground](/playground)** - a hands-on interface where you can try every feature right in your browser.

### What You Can Do:

1. **💬 Chat with AI** - Have real-time conversations with Ollama
2. **🧠 Train Neural Networks** - Build and test ML models
3. **📚 Explore Brand Wordmaps** - Visualize vocabulary and voice
4. **🔌 Test APIs** - Call any endpoint and see JSON responses
5. **🎯 Train Predictive Models** - Create smart content classifiers

**[→ Try the Playground Now](/playground)**

---

## 🚀 Quick Start: Creating Your First Post

### From the Browser:

1. Visit `/admin/post/new`
2. Write your title and content (Markdown supported!)
3. Click "Publish Post"
4. Done! Your post is live

### From the Terminal:

```python
python3 -c "from database import add_post; from datetime import datetime; \\
add_post(1, 'My First Post', 'my-first-post', '<p>Hello World!</p>', datetime.now())"
```

---

## 🤖 AI Features

### Get AI Feedback on Posts

Every post has a "Get AI Feedback" button (admin only). Click it to get comments from 4 AI personas:

- **CalRiven** - Technical architecture expert
- **DeathToData** - Privacy and security advocate
- **TheAuditor** - Validation and testing specialist
- **Soulfra** - Encryption and safety expert

**Requires:** `ollama serve` running on localhost:11434

### Chat-to-Blog Workflow

The "homework becomes blog" system:

```bash
# 1. Chat with Ollama about what you're learning
python3 ollama_chat.py --topic "Neural Networks"

# 2. Compile conversations into blog posts
python3 compile_chats.py

# 3. Your learning is now published content!
```

---

## 📚 Brand Wordmaps

Explore how different brands use language. Each brand has a unique "voice" defined by:

- **Vocabulary** - Words they commonly use
- **Tone** - How they communicate
- **Emoji patterns** - Visual language
- **Consistency** - How predictable their voice is

### Try It:

1. Visit `/brands` to see all available brands
2. Click any brand to see their wordmap
3. Use `/api/brand/wordmap/<slug>` to get JSON data

---

## 🔌 API Reference

Soulfra has **20+ API endpoints** for everything from content management to AI predictions.

### Most Popular Endpoints:

**Health Check:**
```bash
curl http://localhost:5001/api/health
# → {{"status": "ok", "database": "connected"}}
```

**Get All Posts:**
```bash
curl http://localhost:5001/api/posts
# → {{"posts": [...]}}
```

**AI Feedback:**
```bash
curl -X POST http://localhost:5001/api/ollama/comment \\
  -H "Content-Type: application/json" \\
  -d '{{"post_id": 1, "auto_post": false}}'
# → {{"success": true, "comments": [...]}}
```

**[→ Full API Documentation](/docs)**

---

## 🧠 Neural Networks

Soulfra includes a **pure Python neural network** implementation (no TensorFlow/PyTorch). You can:

### Train Models:

```bash
python3 neural_network.py
```

### Use Cases:

1. **XOR Problem** - Classic ML test (learn non-linear patterns)
2. **Website Classification** - Predict site type from URLs
3. **Brand Voice Detection** - Identify author from writing style
4. **Content Prediction** - Suggest categories/tags

### Try It Live:

Visit `/playground` → Neural Network tab → Train XOR network

---

## 🎯 ML Training Interface

The `/train` route provides a visual interface for training content classifiers:

1. Upload training data
2. Set hyperparameters
3. Train model
4. Test predictions
5. Export trained model

**[→ Try ML Training](/train)**

---

## 📊 Live Features

### Live Comment Feed

Watch all comments across all posts in real-time (like Twitch chat):

**[→ Visit /live](/live)**

- Auto-refreshes every 5 seconds
- Shows AI and human comments
- Links to original posts

### Real-time Dashboard

See AI predictions as they happen:

**[→ Visit /dashboard](/dashboard)**

---

## 🎮 Developer Tools

### API Explorer Game

A terminal game for exploring routes (like Zelda for APIs!):

```bash
python3 api_game.py
```

Controls:
- ↑↓ Navigate routes
- Enter: View details
- T: Test route (makes real HTTP request)
- Q: Quit

### Health Check

Verify your entire system:

```bash
python3 health_check.py
```

Checks:
- Database (37 tables)
- Flask routes (70+ routes)
- Templates (35 files)
- Timestamp consistency

---

## 🗺️ System Architecture

```
┌─────────────────────────────────────────┐
│         Flask Web Server (port 5001)    │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │  Templates  │    │   Database   │  │
│  │  (35 files) │◄───┤  (SQLite)    │  │
│  └─────────────┘    └──────────────┘  │
│         ▲                   ▲          │
│         │                   │          │
│  ┌──────┴───────┐    ┌──────┴──────┐  │
│  │   Routes     │    │  Models     │  │
│  │  (70+ APIs)  │    │  (Neural)   │  │
│  └──────────────┘    └─────────────┘  │
│                                         │
└─────────────────────────────────────────┘
           │
           │ Ollama API
           ▼
    ┌──────────────┐
    │   Ollama     │
    │ (localhost)  │
    └──────────────┘
```

---

## 🔐 Offline-First Philosophy

**Soulfra works completely offline.** No internet required for core features:

✅ SQLite database (local)
✅ Flask server (local)
✅ Zero external dependencies
✅ Email queue (send later)

**Only optional:** Ollama (for AI features)

[Read more about why this matters →](/legitimacy)

---

## 📖 Next Steps

### 1. Explore Interactively

**[→ Open Playground](/playground)** - Try everything in one place

### 2. Read the Docs

**[→ API Documentation](/docs)** - Complete endpoint reference

### 3. See All Routes

**[→ Visual Sitemap](/sitemap)** - Interactive route map

### 4. Check System Status

```bash
python3 health_check.py --verbose
```

### 5. Build Something!

Use the APIs, train models, create content. Soulfra is your playground.

---

## 💡 Pro Tips

### Tip 1: Keyboard Shortcuts

- Press `/` on any page to focus search
- `Esc` to close modals
- `Ctrl+K` to open command palette (coming soon!)

### Tip 2: JSON Everywhere

Add `?format=json` to any route to get JSON:

```bash
/post/hello-world?format=json
# → {{"post": {{...}}, "comments": [...]}}
```

### Tip 3: Batch Operations

Use Python scripts for bulk operations:

```bash
# Import 1000 subscribers from CSV
python3 import_subscribers.py data.csv

# Generate 100 AI comments
python3 ollama_auto_commenter.py --batch 100
```

### Tip 4: API Game Achievements

Complete all API tests in `api_game.py` to unlock the "API Master" achievement!

---

## 🆘 Need Help?

### Documentation

- **[START_HERE.md](/)** - Getting started guide
- **[API Docs](/docs)** - Endpoint reference
- **[Playground](/playground)** - Interactive tutorials

### Common Questions

**Q: Ollama not working?**
A: Run `ollama serve` in a separate terminal

**Q: Database errors?**
A: Run `python3 database.py` to rebuild

**Q: Port already in use?**
A: Kill existing process: `lsof -ti :5001 | xargs kill -9`

---

## 🎉 You're Ready!

You now know how to:

✅ Create posts from browser and terminal
✅ Get AI feedback with Ollama
✅ Use the interactive playground
✅ Call APIs and get JSON responses
✅ Train neural networks
✅ Explore brand wordmaps
✅ Debug with health checks

**Welcome to Soulfra. Now go build something awesome.** 🚀

---

*This post was auto-generated as part of the tutorial system.*
*Last updated: {timestamp}*
"""

def create_tutorial_post():
    """Insert tutorial post into database"""
    # Connect to database
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if tutorial already exists
    cursor.execute("SELECT id FROM posts WHERE slug = 'welcome-complete-guide'")
    existing = cursor.fetchone()

    if existing:
        print("⚠️  Tutorial post already exists (ID: {})".format(existing[0]))
        print("Delete it first if you want to recreate it:")
        print("  sqlite3 soulfra.db \"DELETE FROM posts WHERE slug = 'welcome-complete-guide'\"")
        conn.close()
        return

    # Format content with current timestamp
    content = TUTORIAL_CONTENT.format(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # Get admin user ID
    cursor.execute("SELECT id FROM users WHERE username = 'admin' OR is_admin = 1 LIMIT 1")
    admin_row = cursor.fetchone()

    if not admin_row:
        print("❌ No admin user found. Creating one...")
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, display_name, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@soulfra.local', 'NOLOGIN', 'Admin', 1, datetime.now().isoformat()))
        admin_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Created admin user (ID: {admin_id})")
    else:
        admin_id = admin_row[0]

    # Insert tutorial post
    cursor.execute('''
        INSERT INTO posts (user_id, title, slug, content, published_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        admin_id,
        'Welcome to Soulfra: Your Complete Guide',
        'welcome-complete-guide',
        content,
        datetime.now().isoformat()
    ))

    post_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print()
    print("=" * 70)
    print("✅ TUTORIAL POST CREATED!")
    print("=" * 70)
    print()
    print(f"📝 Post ID: {post_id}")
    print(f"👤 Author: admin (ID: {admin_id})")
    print(f"🔗 Slug: welcome-complete-guide")
    print()
    print("🌐 View it at: http://localhost:5001/post/welcome-complete-guide")
    print()
    print("This comprehensive tutorial covers:")
    print("  • Interactive Playground")
    print("  • Creating Posts")
    print("  • AI Features & Ollama")
    print("  • Brand Wordmaps")
    print("  • API Reference")
    print("  • Neural Networks")
    print("  • Live Features")
    print("  • Developer Tools")
    print()


if __name__ == '__main__':
    create_tutorial_post()

# Brand Template - Deploy Your Own Ollama Chat

This folder contains everything you need to create and deploy your own AI-powered brand chat interface.

## 🎯 What is This?

A **self-contained, deployable folder** that gives you:
- ✅ **Static HTML chat** - No server needed, just open index.html
- ✅ **Direct Ollama integration** - Connects straight to Ollama API
- ✅ **Customizable branding** - Colors, name, icon, personality
- ✅ **Optional CAPTCHA** - Ollama-powered challenges (no Google tracking)
- ✅ **Federation ready** - Communicate with other brand instances

## 📦 What's Inside

```
brand_template/
├── index.html          # Main chat interface (just open in browser!)
├── brand.json          # Your brand configuration
├── README.md           # This file
└── start.sh            # Optional: Launch script for LAN access
```

## 🚀 Quick Start

### Option 1: Just Open It (Localhost Only)

1. **Make sure Ollama is running**:
   ```bash
   ollama serve
   ```

2. **Double-click `index.html`** or open it in your browser
3. **Start chatting!**

That's it. No installation, no setup, no server.

---

### Option 2: Deploy to Static Hosting

Upload this folder to **any** static host:

**GitHub Pages** (Free):
```bash
# 1. Create new repo
git init
git add .
git commit -m "Deploy my brand"
git branch -M main
git remote add origin https://github.com/yourusername/yourbrand.git
git push -u origin main

# 2. Enable GitHub Pages in repo settings
# 3. Your brand is live at: https://yourusername.github.io/yourbrand/
```

**Netlify** (Free):
```bash
# 1. Drag and drop this folder to netlify.com/drop
# 2. Done. Your brand is live.
```

**Vercel** (Free):
```bash
npm i -g vercel
vercel
# Follow prompts. Your brand is live.
```

**AWS S3** (Paid, ~$0.50/month):
```bash
aws s3 sync . s3://yourbrand.com --acl public-read
```

---

## 🎨 Customize Your Brand

### 1. Edit `brand.json`

```json
{
  "name": "MyBrand",
  "display_name": "My Awesome Brand",
  "icon": "🚀",
  "colors": {
    "primary": "#667eea",
    "secondary": "#764ba2"
  },
  "ollama": {
    "host": "http://localhost:11434",
    "default_model": "llama2"
  }
}
```

### 2. Update the Title in `index.html`

Replace line 6:
```html
<title>Your Brand Name - AI Chat</title>
```

### 3. Change Colors (Optional)

Edit CSS in `index.html` around line 16:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

---

## 🔐 Add Custom CAPTCHA

Protect your chat with Ollama-powered challenges (no Google tracking).

**Edit `brand.json`**:
```json
{
  "captcha": {
    "enabled": true,
    "prompts": [
      "What is 2+2 in hexadecimal?",
      "Name a primary color in lowercase",
      "What day comes after Monday?"
    ]
  }
}
```

Then add CAPTCHA logic to `index.html` before chat loads.

---

## 🌐 Enable Federation (Brand-to-Brand Communication)

Make your brand talk to other brand instances like email servers.

**Edit `brand.json`**:
```json
{
  "federation": {
    "enabled": true,
    "domain": "mybrand.com",
    "port": 8080,
    "trusted_peers": [
      "https://otherbrand.com",
      "https://friendbrand.io"
    ]
  }
}
```

See `federation_protocol.md` in parent directory for full setup.

---

## 📱 Access from Phone (LAN)

Want to access from your phone on the same WiFi?

**Run `start.sh`**:
```bash
chmod +x start.sh
./start.sh
```

This will:
1. Start Ollama on all network interfaces
2. Show you the URL to access from phone (e.g., `http://192.168.1.74:8080`)
3. You can now open that URL on your phone

---

## 🎯 Use Cases

### Personal Brand
- Create your own AI assistant with custom personality
- Deploy on GitHub Pages for free
- Access from anywhere

### Business Brand
- Customer support chatbot
- Internal knowledge base
- Product Q&A assistant

### Community Brand
- Forum companion
- Discord bot backend
- Subreddit assistant

### Federated Network
- Multiple brands that talk to each other
- Decentralized AI network
- Privacy-focused alternative to centralized services

---

## 🔧 How It Works

### Architecture
```
Browser (Your Phone/Computer)
    ↓
index.html (Pure JavaScript)
    ↓
Ollama API (http://localhost:11434)
    ↓
AI Model (llama2, mistral, etc.)
```

**No Python. No Flask. No database.**

### Conversation Memory
- **localStorage** saves chat history in your browser
- **YOU** send conversation history to Ollama with each request
- **Ollama** is stateless - it doesn't remember anything
- This is how it maintains context across messages

### Why This Works
- Ollama has a REST API at `http://localhost:11434/api/generate`
- JavaScript can call REST APIs with `fetch()`
- Browser localStorage persists data without a database
- Therefore: **Static HTML can chat with Ollama**

---

## 🆚 vs. Server-Based Chat

| Feature | This (Static) | Server-Based |
|---------|---------------|--------------|
| **Setup** | Double-click HTML | Install Python, Flask, dependencies |
| **Hosting** | Free (GitHub Pages) | Paid ($5-20/month VPS) |
| **Database** | Browser localStorage | PostgreSQL, SQLite, etc. |
| **Users** | One per browser | Shared, multi-user |
| **Privacy** | Data never leaves device | Data on server |
| **Scaling** | Infinite (static CDN) | Limited by server |

---

## 🌟 Examples

### Create "Soulfra" Brand
```bash
cp -r brand_template/ soulfra/
cd soulfra/
# Edit brand.json:
# - name: "soulfra"
# - icon: "🌙"
# - colors: Purple/blue gradient
# Deploy to soulfra.com
```

### Create "DeathToData" Brand
```bash
cp -r brand_template/ deathtodata/
cd deathtodata/
# Edit brand.json:
# - name: "deathtodata"
# - icon: "🔒"
# - colors: Dark/red gradient
# - personality: Privacy-focused
# Deploy to deathtodata.org
```

### Create Personal Brand
```bash
cp -r brand_template/ mybrand/
cd mybrand/
# Edit brand.json with your info
# Double-click index.html
# Done. Your personal AI assistant.
```

---

## 🐛 Troubleshooting

### "Ollama Offline" Error

**Problem**: Browser can't connect to Ollama

**Solutions**:
1. Make sure Ollama is running: `ollama serve`
2. Check Ollama is at `http://localhost:11434`:
   ```bash
   curl http://localhost:11434/api/tags
   ```
3. If using phone, update `brand.json`:
   ```json
   "ollama": {
     "host": "http://192.168.1.74:11434"
   }
   ```

### "No Models Found" Error

**Problem**: Ollama has no models installed

**Solutions**:
1. Pull a model:
   ```bash
   ollama pull llama2
   ```
2. List installed models:
   ```bash
   ollama list
   ```
3. Update `brand.json` with model name

### Chat Doesn't Remember Previous Messages

**Problem**: localStorage not saving

**Solutions**:
1. Check browser settings allow localStorage
2. Try incognito mode (some browsers block localStorage)
3. Clear browser cache and reload

### Phone Can't Access

**Problem**: URL doesn't work from phone

**Solutions**:
1. Make sure phone and computer on **same WiFi**
2. Check firewall allows port 11434 and 8080
3. Use IP address, not `localhost`
4. Run `./start.sh` to get correct IP

---

## 📚 Learn More

- **Ollama Docs**: https://ollama.ai/docs
- **Static Site Hosting**: https://pages.github.com
- **localStorage API**: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
- **Federation Protocol**: See `federation_protocol.md` in parent folder

---

## 🤝 Contributing

This is a template. Fork it, customize it, deploy it.

Share your brand with the community!

---

**Generated 2025-12-28 by Soulfra**

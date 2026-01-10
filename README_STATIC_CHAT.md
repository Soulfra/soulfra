# 🚀 Static HTML Ollama Chat - Complete System

**"Ollama is already turned on, why can't I just get a fucking HTML document?"**

This is that HTML document.

## 🎯 What You Get

1. **`static_chat.html`** - Open in browser, chat with Ollama immediately
2. **`brand_template/`** - Copy/paste folder to deploy your own brand
3. **`federation_protocol.md`** - Make brands talk to each other (like email)
4. **`custom_captcha.js`** - Ollama-powered CAPTCHA (no Google tracking)

**No Flask. No database. No Python. Just HTML → Ollama.**

---

## ⚡ Quick Start (5 Seconds)

### Option 1: Just Open It

```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Double-click static_chat.html
# Or: Open in browser
open static_chat.html
```

Done. You're chatting with Ollama.

---

### Option 2: Deploy Your Brand

```bash
# 1. Copy template
cp -r brand_template/ mybrand/

# 2. Edit brand.json
{
  "name": "mybrand",
  "display_name": "My Awesome Brand",
  "icon": "🚀"
}

# 3. Deploy to GitHub Pages, Netlify, Vercel, S3, anywhere
```

Your brand is live.

---

## 📁 What's Included

```
.
├── static_chat.html           # Open this! Pure HTML/JS chat
├── custom_captcha.js          # Ollama CAPTCHA (no Google)
├── federation_protocol.md     # Brand-to-brand communication spec
├── brand_template/            # Copy this to create brands
│   ├── index.html            # Same as static_chat.html
│   ├── brand.json            # Brand configuration
│   ├── start.sh              # Launch script for LAN access
│   └── README.md             # Full setup instructions
└── README_STATIC_CHAT.md     # This file
```

---

## 🔥 Features

### Static Chat (`static_chat.html`)

✅ **Zero dependencies** - Just open in browser
✅ **Direct Ollama API** - No middleware, no server
✅ **localStorage** - Saves conversation history
✅ **Model selector** - Switch between Ollama models
✅ **Context management** - Sends conversation history
✅ **Mobile-friendly** - Works on phone
✅ **Beautiful UI** - Purple/blue gradient, glassmorphism
✅ **Real-time status** - Shows Ollama connection

### Brand Template

✅ **Fully self-contained** - Copy folder, deploy anywhere
✅ **Customizable** - Colors, name, icon, personality
✅ **Static hosting** - GitHub Pages, Netlify, Vercel, S3
✅ **LAN access** - Access from phone with `./start.sh`
✅ **Federation ready** - Can communicate with other brands

### Custom CAPTCHA

✅ **Ollama-powered** - Uses AI to generate challenges
✅ **No tracking** - No Google, no external services
✅ **Customizable** - Math, text, logic, or custom prompts
✅ **Smart validation** - Flexible answer checking
✅ **Beautiful UI** - Matches static chat style

### Federation Protocol

✅ **Decentralized** - Like email, each brand independent
✅ **Brand-to-brand** - Soulfra ↔ DeathToData ↔ CalRiven
✅ **Knowledge sharing** - Brands share expertise
✅ **Consensus building** - Ask multiple brands, synthesize
✅ **Privacy-focused** - P2P, no central authority

---

## 🏗️ How It Works

### Architecture

```
Browser
  ↓ (JavaScript fetch)
Ollama API (localhost:11434)
  ↓
AI Model (llama2, mistral, etc.)
```

**No server. No Python. No database.**

### Conversation Memory

**Problem**: Ollama is stateless (doesn't remember previous messages)

**Solution**: YOU send conversation history with each request

```javascript
// Each request includes full conversation
fetch('http://localhost:11434/api/generate', {
  method: 'POST',
  body: JSON.stringify({
    model: 'llama2',
    prompt: buildPromptWithHistory(), // Includes all previous messages
    stream: false
  })
})
```

**Storage**: Browser `localStorage` persists history

### Why This Works

1. **Ollama has REST API** - `http://localhost:11434/api/generate`
2. **JavaScript can call REST APIs** - `fetch()`
3. **localStorage persists data** - No database needed
4. **Static HTML can be deployed anywhere** - GitHub Pages, S3, etc.

Therefore: **Static HTML can chat with Ollama**

---

## 🎨 Customization

### Change Colors

Edit CSS in `static_chat.html` line 16:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change Brand Name

Edit `brand_template/brand.json`:
```json
{
  "name": "yourbrand",
  "display_name": "Your Brand Name",
  "icon": "🌙"
}
```

### Add Custom CAPTCHA Prompts

Edit `brand_template/brand.json`:
```json
{
  "captcha": {
    "prompts": [
      "What is 2+2 in hexadecimal?",
      "Name a primary color",
      "What day comes after Monday?"
    ]
  }
}
```

### Change Ollama Model

Edit `brand_template/brand.json`:
```json
{
  "ollama": {
    "default_model": "mistral"
  }
}
```

---

## 📱 Phone Access (LAN)

### From Computer

```bash
cd brand_template/
./start.sh
```

Output:
```
📍 Your local IP: 192.168.1.74

Your brand will be accessible at:
  - http://localhost:8080 (from this computer)
  - http://192.168.1.74:8080 (from phone)

Starting server...
```

### From Phone

1. **Connect to same WiFi** as computer
2. **Open browser** on phone
3. **Go to** `http://192.168.1.74:8080`
4. **Start chatting!**

---

## 🌐 Deployment Options

### GitHub Pages (Free, Easy)

```bash
# 1. Create repo
git init
git add .
git commit -m "Deploy my brand"
git remote add origin https://github.com/yourusername/yourbrand.git
git push -u origin main

# 2. Enable GitHub Pages
# Settings → Pages → Source: main branch

# 3. Your brand is live
https://yourusername.github.io/yourbrand/
```

### Netlify (Free, Drag & Drop)

1. Go to https://netlify.com/drop
2. Drag `brand_template/` folder
3. Done. Your brand is live.

### Vercel (Free, CLI)

```bash
npm i -g vercel
cd brand_template/
vercel
```

### AWS S3 (Paid, ~$0.50/month)

```bash
aws s3 sync brand_template/ s3://yourbrand.com --acl public-read
```

### Your Own VPS

```bash
# Copy to server
scp -r brand_template/ user@yourserver.com:/var/www/yourbrand/

# Serve with nginx
server {
    listen 80;
    server_name yourbrand.com;
    root /var/www/yourbrand;
    index index.html;
}
```

---

## 🔐 Add CAPTCHA to Your Brand

### 1. Include Script

Edit `brand_template/index.html`:
```html
<head>
    <!-- Add before </head> -->
    <script src="../custom_captcha.js"></script>
</head>
```

### 2. Add Container

```html
<body>
    <!-- Add before chat input -->
    <div id="brand-captcha"></div>
</body>
```

### 3. Initialize

```html
<script>
    // Load brand config
    fetch('brand.json')
        .then(r => r.json())
        .then(config => {
            // Create CAPTCHA
            const captcha = new OllamaCaptcha('brand-captcha', {
                ollamaHost: config.ollama.host,
                model: config.ollama.default_model,
                customPrompts: config.captcha.prompts
            });

            // Listen for validation
            document.getElementById('brand-captcha').addEventListener('captcha-validated', () => {
                // Enable chat
                document.getElementById('sendBtn').disabled = false;
            });
        });
</script>
```

---

## 🌍 Enable Federation (Brand-to-Brand)

### 1. Configure Your Brand

Edit `brand_template/brand.json`:
```json
{
  "federation": {
    "enabled": true,
    "domain": "yourbrand.com",
    "trusted_peers": [
      "soulfra.com",
      "deathtodata.org"
    ]
  }
}
```

### 2. Create Federation Server

See `federation_protocol.md` for complete Python Flask implementation.

### 3. Send Messages to Other Brands

```javascript
// In your chat interface
if (message.startsWith('@soulfra')) {
    const question = message.replace('@soulfra', '').trim();
    const response = await sendFederatedMessage('soulfra.com', question);
    addMessage('assistant', `Soulfra: ${response}`);
}
```

---

## 🆚 vs. Traditional Setup

| Feature | Static HTML | Flask/Server |
|---------|-------------|--------------|
| **Setup Time** | 0 seconds | 30+ minutes |
| **Dependencies** | None | Python, Flask, DB, etc. |
| **Hosting Cost** | Free | $5-20/month |
| **Complexity** | 1 file | 10+ files |
| **Privacy** | Data stays local | Data on server |
| **Scaling** | Infinite (CDN) | Limited by server |
| **Deployment** | Drag & drop | DevOps required |

---

## 🧪 Testing

### Test Ollama Connection

```bash
curl http://localhost:11434/api/tags
```

Expected: JSON list of models

### Test Static Chat

```bash
# 1. Open static_chat.html in browser
# 2. Check status bar shows "Ollama Connected"
# 3. Select a model
# 4. Type message
# 5. Click Send
```

Expected: Ollama responds

### Test CAPTCHA

```bash
# 1. Open browser console
# 2. Run:
const captcha = new OllamaCaptcha('test-captcha', {
    ollamaHost: 'http://localhost:11434',
    model: 'llama2'
});

# 3. Watch challenge appear
# 4. Answer it
```

Expected: Validation succeeds

---

## 🐛 Troubleshooting

### "Ollama Offline" Error

**Problem**: Can't connect to Ollama

**Solutions**:
1. Run `ollama serve`
2. Check `http://localhost:11434/api/tags`
3. Update OLLAMA_HOST in browser console:
   ```javascript
   OLLAMA_API = 'http://192.168.1.74:11434'
   ```

### "No Models Found"

**Problem**: Ollama has no models

**Solutions**:
1. Pull a model: `ollama pull llama2`
2. List models: `ollama list`
3. Refresh page

### Chat Doesn't Remember

**Problem**: localStorage disabled

**Solutions**:
1. Enable localStorage in browser settings
2. Try incognito mode
3. Check browser console for errors

### Phone Can't Access

**Problem**: LAN blocking

**Solutions**:
1. Check phone on **same WiFi** as computer
2. Check firewall allows port 11434 and 8080
3. Use IP address, not `localhost`
4. Run `./start.sh` to get correct IP

---

## 💡 Use Cases

### Personal AI Assistant

```bash
cp -r brand_template/ my-assistant/
# Edit brand.json with your preferences
# Deploy to GitHub Pages
# Access from anywhere
```

### Customer Support Bot

```bash
cp -r brand_template/ support-bot/
# Add custom CAPTCHA
# Deploy to Netlify
# Share URL with customers
```

### Federated AI Network

```bash
# Create multiple brands
cp -r brand_template/ soulfra/
cp -r brand_template/ deathtodata/
cp -r brand_template/ calriven/

# Configure federation
# Each brand talks to others
# Decentralized AI network
```

---

## 🎓 Understanding Context Windows

**User asked**: "how that necessarily works until it hits context windows"

### What is a Context Window?

The **context window** is how much text Ollama can "see" at once.

Example:
- **llama2**: 4096 tokens (~3000 words)
- **mistral**: 8192 tokens (~6000 words)
- **codellama**: 16384 tokens (~12000 words)

### How We Handle It

**Each request** to Ollama includes:
1. System prompt (instructions)
2. Previous messages (conversation history)
3. New message from user

```javascript
function buildPromptWithContext(newMessage) {
    let prompt = '';

    // Include last 10 messages (adjustable)
    const recentHistory = conversationHistory.slice(-10);

    recentHistory.forEach(msg => {
        if (msg.role === 'user') {
            prompt += `User: ${msg.content}\n\n`;
        } else {
            prompt += `Assistant: ${msg.content}\n\n`;
        }
    });

    prompt += `User: ${newMessage}\n\nAssistant:`;
    return prompt;
}
```

**We only send last 10 messages** to stay within context window.

### If Context Gets Too Long

**Option 1**: Summarize old messages with Ollama
```javascript
const summary = await askOllama(`Summarize this conversation: ${oldMessages}`);
context = [summary, ...recentMessages];
```

**Option 2**: Use larger model
```javascript
// Switch to codellama (16K context)
model = 'codellama'
```

**Option 3**: Split conversation into sessions
```javascript
if (messageCount > 50) {
    // Start new session
    conversationHistory = [];
}
```

---

## 🚀 Next Steps

1. ✅ **Try `static_chat.html`** - Open it, chat with Ollama
2. ✅ **Create your brand** - Copy `brand_template/`, customize
3. ✅ **Deploy it** - GitHub Pages, Netlify, Vercel, S3
4. ✅ **Add CAPTCHA** - Replace Google reCAPTCHA
5. ✅ **Enable federation** - Connect with other brands

---

## 🤝 Decentralization Vision

**Your question**: "do with ollama or apis and stuff what gmail did to emails and decentralize it"

**YES! That's exactly what federation does.**

### Like Email Servers

```
Gmail (Google)          ProtonMail (Proton)
    ↕                         ↕
alice@gmail.com ←→ bob@protonmail.com
```

Each email provider is independent, but they can send to each other.

### Like Brand Instances

```
Soulfra (soulfra.com)   DeathToData (deathtodata.org)
    ↕                            ↕
user@soulfra.com  ←→  user@deathtodata.org
```

Each brand is independent, but they can message each other.

### Benefits

1. **No central authority** - You control your brand
2. **Privacy** - Data doesn't go to Google/OpenAI
3. **Resilience** - One brand down ≠ all brands down
4. **Customization** - Each brand has own personality
5. **Specialization** - Route questions to expert brands

### Example Network

```
         Soulfra (Security Expert)
              ↕
         DeathToData (Privacy Expert)
              ↕
         CalRiven (Architecture Expert)
              ↕
         TheAuditor (Testing Expert)
              ↕
         YourBrand (Your Specialty)
```

User asks privacy question → Routes to DeathToData
User asks architecture question → Routes to CalRiven
User asks security question → Routes to Soulfra

**All using Ollama. All decentralized. All private.**

---

## 📚 Learn More

- **Ollama Docs**: https://ollama.ai/docs
- **Federation Protocol**: See `federation_protocol.md`
- **CAPTCHA Implementation**: See `custom_captcha.js`
- **Brand Template**: See `brand_template/README.md`
- **LAN Access**: See `README_LAN.md`

---

**Generated 2025-12-28 by Soulfra**

*"Ollama is already turned on. Here's your HTML document."*

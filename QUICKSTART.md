# Soulfra Quick Start Guide

**Get your AI-powered ghost writing platform running in 5 minutes**

---

## What is Soulfra?

Soulfra is an **AI-powered ghost writing platform** for blogs, businesses, and personal brands. It combines:

- 🤖 **AI Content Generation** - Auto-generate posts with Claude API or local Ollama
- 🧠 **Neural Networks** - Topic classification and content recommendations
- 📊 **Batch Import** - Upload 1000 posts from Excel/CSV in one command
- 🔐 **License System** - API keys and rate limiting for agents/customers
- 🌐 **Multi-Brand** - Manage multiple blogs with different personalities
- 📧 **Email Newsletters** - Automated subscriber management

---

## Option 1: Docker (Recommended)

**Fastest way to get started - One command deployment**

```bash
# 1. Clone repository
git clone https://github.com/calriven/soulfra
cd soulfra

# 2. Create .env file (optional - has sensible defaults)
cat > .env << EOF
BASE_URL=http://localhost:5001
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
EOF

# 3. Start with Docker Compose
docker-compose up -d

# 4. Visit your blog
open http://localhost:5001
```

**Done!** Your ghost writing platform is running.

### What Docker Compose Includes

- ✅ Soulfra web app (port 5001)
- ✅ Ollama AI (port 11434)
- ✅ SQLite database
- ✅ Persistent storage for content
- ✅ Auto-restart on failure

---

## Option 2: Manual Installation

**For development or custom deployments**

### Step 1: Install

```bash
# Clone repository
git clone https://github.com/calriven/soulfra
cd soulfra

# Run installation wizard
python3 install.py

# Follow the prompts:
#   📧 Email: admin@myblog.com
#   🌐 Domain: (optional) myblog.com
#   💳 Tier: Pro ($15/year) or Free
```

The wizard will:
1. ✅ Install Python dependencies
2. ✅ Initialize database
3. ✅ Create admin account
4. ✅ Generate license & API keys
5. ✅ Create `.env` configuration

### Step 2: Start Server

```bash
# Development mode
python3 app.py

# Production mode (with gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Step 3: Visit Your Blog

```
http://localhost:5001
```

---

## Quick Tasks

### Import Existing Posts from CSV

Have 100 posts in an Excel sheet? Import them all at once:

```bash
# Create CSV file:
# title, content, brand_slug, tags, published_date
# "Privacy 101", "Your guide to...", "mybrand", "privacy,encryption", "2025-01-15"

# Preview before importing
python3 batch_import_posts.py --file posts.csv --preview

# Import all posts
python3 batch_import_posts.py --file posts.csv --import --brand mybrand
```

### Auto-Generate Posts with AI

```bash
# Generate post about a topic
python3 force_claude_write.py --brand mybrand --topic "neural networks" --save

# Bulk generate 10 posts
for topic in "AI" "ML" "Python" "Data" "Privacy"; do
  python3 force_claude_write.py --brand mybrand --topic "$topic" --save
done
```

### Set Up Custom Domain

```bash
# 1. Generate DNS records
python3 dns_setup_guide.py --domain myblog.com --ip 123.45.67.89

# 2. Add records to your domain registrar (Namecheap, GoDaddy, etc.)

# 3. Generate nginx config
python3 dns_setup_guide.py --domain myblog.com --nginx-config

# 4. Set up SSL
sudo certbot --nginx -d myblog.com -d www.myblog.com
```

### Generate API Key for Automation

```bash
# 1. Generate license (or use existing from install.py)
python3 license_manager.py --generate-license --email you@example.com --tier pro

# 2. Generate API key
python3 license_manager.py --generate-api-key \
  --license YOUR-LICENSE-UUID \
  --name "Production API"

# 3. Use API key in requests
curl -X POST http://localhost:5001/api/v1/mybrand/generate \
  -H "X-API-Key: sk-abc123..." \
  -H "Content-Type: application/json" \
  -d '{"topic": "blockchain", "auto_publish": true}'
```

---

## Common Use Cases

### Use Case 1: Personal Blog

**Scenario**: You want to start a blog about AI/ML

```bash
# 1. Install
docker-compose up -d

# 2. Create your brand
# Visit http://localhost:5001/admin
# Create brand: "Tech Insights" with slug "techinsights"

# 3. Import old posts
python3 batch_import_posts.py --file old_posts.csv --import --brand techinsights

# 4. Auto-generate new posts
python3 force_claude_write.py --brand techinsights --topic "transformers" --save
python3 force_claude_write.py --brand techinsights --topic "GPT-4" --save

# 5. Train neural network on your content
python3 train_topic_networks.py --topics AI,ML,transformers --train

# 6. Set up custom domain
python3 dns_setup_guide.py --domain techinsights.com --ip YOUR_IP
```

### Use Case 2: Multi-Client Ghost Writing Agency

**Scenario**: You manage blogs for 5 different clients

```bash
# 1. Create brands for each client
# Client A: Healthcare blog
# Client B: Finance blog
# Client C: Tech blog
# ... etc

# 2. Import their existing content
python3 batch_import_posts.py --file client_a_posts.csv --import --brand healthcare
python3 batch_import_posts.py --file client_b_posts.csv --import --brand finance

# 3. Generate API keys for each client
python3 license_manager.py --generate-license --email clienta@example.com --tier pro
python3 license_manager.py --generate-api-key --license UUID-A --name "Client A"

# 4. Train brand-specific neural networks
python3 train_context_networks.py

# 5. Auto-generate weekly posts for all clients
python3 force_claude_write.py --brand healthcare --topic "telemedicine trends" --save
python3 force_claude_write.py --brand finance --topic "crypto regulations" --save
```

### Use Case 3: Business Documentation Platform

**Scenario**: Internal knowledge base + external blog for a company

```bash
# 1. Create two brands:
#    - "internal" (employee docs)
#    - "external" (public blog)

# 2. Import company docs from Excel
python3 batch_import_posts.py --file company_docs.xlsx --import --brand internal

# 3. Auto-generate weekly blog posts
crontab -e
# Add: 0 9 * * 1 cd /path/to/soulfra && python3 force_claude_write.py --brand external --topic "industry news" --save

# 4. Set up email newsletters
# Configure SMTP in .env
# Subscribers will get weekly emails automatically
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         SOULFRA                             │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Flask     │  │   SQLite     │  │   Ollama     │      │
│  │   Web App   │──│   Database   │──│   AI Engine  │      │
│  │  (Port 5001)│  │ (soulfra.db) │  │ (Port 11434) │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
│         │                                                   │
│         ├── Templates (Jinja2 HTML)                        │
│         ├── Static Files (CSS/JS)                          │
│         ├── Neural Networks (scikit-learn)                 │
│         └── Brands (Multi-tenant content)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
     Web Browser         API Clients         Batch Imports
     (localhost:5001)    (Python/JS)         (CSV/Excel)
```

---

## API Examples

### Python Client

```python
import requests

API_KEY = "sk-abc123..."
BASE_URL = "http://localhost:5001"

# Generate post
response = requests.post(
    f"{BASE_URL}/api/v1/mybrand/generate",
    headers={"X-API-Key": API_KEY},
    json={"topic": "neural networks", "auto_publish": True}
)

post = response.json()
print(f"Created post: {post['url']}")

# Get all posts
response = requests.get(
    f"{BASE_URL}/api/v1/mybrand/posts",
    headers={"X-API-Key": API_KEY}
)

posts = response.json()
print(f"Total posts: {len(posts)}")
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'http://localhost:5001/api/v1',
  headers: {
    'X-API-Key': 'sk-abc123...'
  }
});

// Generate post
async function generatePost(brand, topic) {
  const response = await client.post(`/${brand}/generate`, {
    topic: topic,
    auto_publish: true
  });

  console.log(`Created: ${response.data.url}`);
}

generatePost('mybrand', 'blockchain');
```

---

## File Structure

```
soulfra-simple/
├── app.py                      # Main Flask application
├── soulfra.db                  # SQLite database
├── .env                        # Environment config (secrets)
│
├── install.py                  # Installation wizard
├── license_manager.py          # API keys & licensing
├── batch_import_posts.py       # CSV/Excel import
├── dns_setup_guide.py          # Domain setup helper
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── components/            # Reusable components
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── menu.html
│   └── ...
│
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   │   ├── theme.css          # Global theme
│   │   ├── deathtodata.css    # Brand-specific CSS
│   │   └── ...
│   ├── qr/                    # Generated QR codes
│   └── generated/             # AI-generated images
│
├── brands/                     # Exported brand data
│   ├── mybrand/
│   │   ├── config.json        # Brand config
│   │   ├── posts/             # Markdown posts
│   │   └── README.md
│   └── ...
│
├── neural_networks/            # Trained ML models
│   ├── mybrand_classifier.pkl
│   └── topic_classifier.pkl
│
├── docker-compose.yml          # Docker deployment
├── Dockerfile                  # Container image
└── README.md                   # Full documentation
```

---

## Troubleshooting

### Port 5001 already in use

```bash
# Find process using port 5001
lsof -i :5001

# Kill it
kill -9 PID

# Or use different port
export PORT=8000
python3 app.py
```

### Database locked

```bash
# Stop all instances
docker-compose down
pkill -f "python3 app.py"

# Restart
docker-compose up -d
```

### Can't generate posts with Claude

```bash
# Make sure API key is set
echo "CLAUDE_API_KEY=sk-ant-api03-..." >> .env

# Test it
python3 force_claude_write.py --brand mybrand --topic "test" --print
```

### DNS not working

```bash
# Test DNS propagation
python3 dns_setup_guide.py --domain myblog.com --test

# Wait 5-30 minutes for DNS to propagate
# Check with: dig myblog.com
```

---

## Next Steps

1. ✅ **Read ARCHITECTURE_EXPLAINED.md** - Understand how it all works
2. ✅ **Read DEPLOYMENT.md** - Production deployment guide
3. ✅ **Read PITCH_DECK.md** - Business model & roadmap
4. ✅ **Join Discord** - https://discord.gg/soulfra
5. ✅ **Star on GitHub** - https://github.com/calriven/soulfra

---

## Getting Help

- **Documentation**: https://docs.soulfra.com
- **Issues**: https://github.com/calriven/soulfra/issues
- **Email**: support@soulfra.com
- **Discord**: https://discord.gg/soulfra

---

## License

MIT License - See LICENSE.md

**Built with**: Python, Flask, SQLite, scikit-learn, Anthropic Claude API

**Happy writing!** 🚀

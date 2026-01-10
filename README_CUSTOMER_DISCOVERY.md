# Customer Discovery AI - Decentralized Network

**Help your users find their ideal customers - powered by email and hardware you control.**

No cloud. No subscriptions. No vendor lock-in.

---

## 🎯 What Is This?

A **marketing-focused AI tool** that helps businesses:
- Build detailed customer personas
- A/B test marketing messages (Red vs Blue)
- Discover adjacent marketing opportunities
- Save and export customer profiles

Powered by a **truly decentralized network** using email as the transport layer.

---

## 🚀 Quick Start

### For Users (No Setup Required)

1. **Get an API key** from the GitHub Faucet
2. **Visit the tool:** `https://YOUR_SITE.github.io/`
3. **Enter your email and API key**
4. **Ask questions about your target market**
5. **Receive AI insights via email** (30-60 seconds)

### For Node Operators

```bash
# 1. Create dedicated email (Gmail with app password works)
# 2. Install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama3

# 3. Install dependencies
pip install requests

# 4. Run a node
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD \
  --node-name "my-mac"

# That's it! The node checks inbox every 30 seconds
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   GitHub Pages (Free Forever)      │
│   - index.html (landing page)       │
│   - customer-discovery-chat.html    │
│   - email-ollama-chat.html          │
└──────────────┬──────────────────────┘
               │
               │ User sends email via mailto:
               │
               ▼
┌─────────────────────────────────────┐
│   Email Network                      │
│   - Shared inbox (Gmail, etc.)       │
│   - IMAP/SMTP protocol               │
└──────────────┬──────────────────────┘
               │
     ┌─────────┼─────────┐
     │         │         │
     ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│  Mac   │ │  Pi    │ │iPhone  │
│ Ollama │ │ Ollama │ │ Relay  │
└────────┘ └────────┘ └────────┘

Whoever is online processes it!
```

**Key Points:**
- Frontend: Static HTML on GitHub Pages ($0 hosting)
- Transport: Email (universally available, free)
- Processing: Your devices running Ollama
- Redundancy: Multiple nodes = resilience

---

## 📁 Files Overview

### Frontend (Deploy to GitHub Pages)

| File | Purpose |
|------|---------|
| `index.html` | Landing page with links to tools |
| `customer-discovery-chat.html` | Marketing-focused interface with personas, A/B testing, adjacent marketing |
| `email-ollama-chat.html` | Simple chat interface for general questions |

### Backend (Run on your devices)

| File | Purpose |
|------|---------|
| `ollama_email_node.py` | Node script - checks email, processes with Ollama, sends responses |
| `database.py` | API key validation (from GitHub Faucet) |

### Documentation

| File | Purpose |
|------|---------|
| `README_CUSTOMER_DISCOVERY.md` | This file - overview and quick start |
| `CUSTOMER-DISCOVERY-DEPLOYMENT.md` | Complete deployment guide for GitHub Pages |
| `DECENTRALIZED-EMAIL-NETWORK.md` | Technical deep dive on email-based architecture |
| `STATIC-GITHUB-PAGES-GUIDE.md` | Alternative ngrok-based setup |

---

## 💡 Features

### Customer Discovery Tool

**👤 Persona Builder**
- Pre-built templates for customer research
- "Who are they?" - Demographics and psychographics
- "What pain points?" - Problems and frustrations
- "Where are they?" - Channels and communities
- "How do they decide?" - Buyer's journey mapping
- "What do they value?" - Priorities and motivations
- "Who else wants them?" - Competitive analysis

**🔴🔵 A/B Testing**
- Generate two versions (Red vs Blue)
- Test headlines, CTAs, email subjects, ad copy
- Pick winner and iterate
- Save winning versions to profiles

**🔗 Adjacent Marketing**
- Find complementary products for cross-promotion
- Discover partnership opportunities
- Identify adjacent markets to expand into
- Get bundle and upsell ideas

**💾 Profile Management**
- Save customer personas to browser storage
- Export as JSON for sharing
- Build a library of target customer insights

### Simple Chat Tool

- Clean, minimal interface
- General AI questions
- Same email-based network
- No distractions

---

## 🎨 Use Cases

### 1. Marketing Agencies

**Problem:** Clients don't know who their target customer is.

**Solution:**
- Give them free access to Customer Discovery tool
- They explore their target market using AI
- You see their questions and insights
- Sales call is now about implementation, not discovery
- Higher close rate, faster sales cycle

**Implementation:**
```html
<!-- Add to your agency website -->
<a href="https://your-agency.github.io/customer-discovery">
  Free Tool: Find Your Ideal Customer
</a>
```

### 2. SaaS Companies

**Problem:** Need to qualify leads better.

**Solution:**
- Link to tool from homepage as "Free Marketing Audit"
- Prospects self-qualify by using persona builder
- Track which templates they use (indicates pain points)
- Follow up with relevant case studies
- Convert more trials to paid

**Benefits:**
- Free lead magnet that provides real value
- Learn about prospects before sales call
- Position as helpful expert, not just vendor

### 3. Local Business Directories

**Problem:** Businesses on platform don't collaborate.

**Solution:**
- Give each business an API key
- They use Adjacent Marketing to find complementary businesses
- You facilitate introductions and partnerships
- Businesses stay on platform longer
- Increased lifetime value

**Revenue Model:**
- Basic: Free tool access
- Pro: Introductions to partners ($99/month)
- Enterprise: White label for franchise owners ($499/month)

### 4. Content Marketers

**Problem:** Need lead magnets that convert.

**Solution:**
- Blog post: "Not Sure Who Your Customer Is? We Built a Free AI Tool"
- Readers use tool, get immediate value
- Email capture for "Save your results"
- Nurture sequence based on which templates they used
- Upsell consulting or implementation services

**Why It Works:**
- Demonstrates value before asking for money
- Self-qualifying (only serious prospects use it)
- Insights into their specific challenges

---

## 🔧 Configuration

### Update Node Email

Edit `customer-discovery-chat.html` and `email-ollama-chat.html`:

```javascript
// Line ~689 in customer-discovery-chat.html
// Line ~291 in email-ollama-chat.html
const NODE_EMAIL = 'ollama@yourdomain.com'; // Your actual node email
```

### Customize Branding

```html
<!-- Change header -->
<h1>🎯 [Your Brand] Customer Discovery</h1>

<!-- Change tagline -->
<div class="tagline">Your custom tagline here</div>

<!-- Change colors -->
<style>
body {
    background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
}
</style>
```

### Add Analytics

```html
<!-- Before </head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>
```

---

## 📊 Scaling

### Email Account Limits

**Gmail:** 500 emails/day
- Each request = 2 emails (request + response)
- Limit: ~250 AI requests per day per email account

**Solution:** Multiple node emails
```bash
# Pool 1
python3 ollama_email_node.py --email ollama1@domain.com ...

# Pool 2
python3 ollama_email_node.py --email ollama2@domain.com ...

# Pool 3
python3 ollama_email_node.py --email ollama3@domain.com ...
```

Update frontend to randomly assign users to pools.

### Response Time Optimization

**Hardware:**
- M1/M2 Mac: 10-20 seconds
- Desktop GPU: 5-15 seconds
- Raspberry Pi 5: 30-60 seconds

**Models:**
```bash
ollama pull llama3:8b   # Balanced (recommended)
ollama pull phi3        # Fast, smaller
ollama pull mistral     # Alternative, good quality
```

**Multiple Nodes:**
- First available node processes
- Load distributed automatically
- Geographic distribution possible

---

## 💰 Monetization Ideas

### 1. Freemium API Keys

- **Free Tier:** 5 requests/month
- **Pro Tier:** Unlimited requests ($10/month)
- **Enterprise:** White label + support ($100/month)

Enforce via API key tier system in database.

### 2. Lead Qualification as Service

- Give tool away free
- Aggregate anonymized insights
- "What are businesses asking about their customers?"
- Sell trend reports to VCs/researchers ($500/report)

### 3. White Label for Agencies

- Customize branding per agency
- They deploy for their clients
- You run the node infrastructure
- Monthly fee per agency ($50-200/month)

### 4. Consulting Upsell

- Free tool attracts prospects
- They get value from AI insights
- Upsell: "Want help implementing these insights?"
- Convert 5-10% to consulting ($2k-10k projects)

### 5. Partnership Facilitation

- Users discover adjacent opportunities via tool
- You facilitate introductions
- Commission on partnerships formed (5-10%)

---

## 🔒 Security & Privacy

### API Key Validation

Keys validated against local database:
```python
# ollama_email_node.py validates each request
def validate_api_key(api_key):
    db = get_db()
    result = db.execute(
        'SELECT * FROM api_keys WHERE api_key = ? AND is_active = 1',
        (api_key,)
    ).fetchone()
    return result is not None
```

### Data Privacy

- **User emails:** Only stored in browser localStorage
- **Prompts:** Sent via email, processed on your nodes
- **Responses:** Delivered via email, not logged
- **Profiles:** Saved in user's browser only (localStorage)

No central database of user data.

### HTTPS via GitHub Pages

GitHub Pages serves over HTTPS automatically.

---

## 🐛 Troubleshooting

### Responses Not Arriving

**Check:**
```bash
# Is node running?
ps aux | grep ollama_email_node

# Is Ollama available?
curl http://localhost:11434/api/tags

# Check node logs
python3 ollama_email_node.py ... # Look for errors
```

### mailto: Links Not Working

**Issue:** Browser blocking mailto: links

**Solutions:**
1. Set default email client (Mail, Gmail, Outlook)
2. Manually copy email details shown on page

### API Keys Not Working

**Check database:**
```bash
python3 -c "
from database import get_db
db = get_db()
keys = db.execute('SELECT api_key, is_active FROM api_keys').fetchall()
for k in keys:
    print(f'{k[0]} - Active: {k[1]}')
"
```

---

## 🤝 Contributing

### Add More Persona Templates

Edit `customer-discovery-chat.html`:

```javascript
const PERSONA_TEMPLATES = {
    your_template: `Your prompt here...

Use {context} as placeholder for user's product description.`,
    // Add more...
};
```

### Add More Adjacent Marketing Types

```javascript
const ADJACENT_TEMPLATES = {
    your_type: `Your prompt here...

Use {product} and {market} as placeholders.`,
    // Add more...
};
```

### Improve Response Parsing

The A/B testing expects this format from AI:
```
RED: [red option]
BLUE: [blue option]
```

Improve parsing in `displayABResults()` function if needed.

---

## 📚 Documentation

- **Quick Start:** This README
- **Deployment:** `CUSTOMER-DISCOVERY-DEPLOYMENT.md`
- **Architecture:** `DECENTRALIZED-EMAIL-NETWORK.md`
- **Alternative Setup:** `STATIC-GITHUB-PAGES-GUIDE.md`

---

## 🌟 Why This Matters

### The Traditional Way:
1. Pay for cloud AI API ($$$)
2. Vendor lock-in
3. Privacy concerns
4. Usage limits
5. Service can shut down anytime

### The Decentralized Way:
1. Run on hardware you own ($0 ongoing)
2. No vendor lock-in (it's just email!)
3. Complete privacy (your infrastructure)
4. No artificial limits (just your hardware)
5. Resilient (distributed across devices)

**This is how the internet was meant to work.**

---

## 🚢 Deployment Checklist

- [ ] Update `NODE_EMAIL` in HTML files
- [ ] Customize branding (header, colors, tagline)
- [ ] Set up node email account (Gmail with app password)
- [ ] Install Ollama and pull model
- [ ] Run at least one node
- [ ] Test full flow (send request, receive response)
- [ ] Push to GitHub and enable Pages
- [ ] Link from main website
- [ ] Set up analytics (optional)
- [ ] Configure GitHub Faucet for API keys (or create manually)
- [ ] Create usage documentation for users
- [ ] Monitor node logs for first few days

---

## 📈 Success Metrics

Track these to measure impact:

**User Engagement:**
- API keys issued
- Requests per day
- Most popular templates
- Conversion rate (visitor → tool user)

**Business Value:**
- Leads generated
- Qualification rate improvement
- Time to close deals
- Customer insights gained

**Technical Health:**
- Node uptime
- Average response time
- Error rate
- Email queue length

---

## 🎉 What You Built

A **truly decentralized customer discovery platform** that:

✅ Helps businesses find their ideal customers
✅ Costs $0 to run (using hardware you already own)
✅ Works on any device (Mac, Pi, old iPhone, router)
✅ Gives you full control (no cloud dependencies)
✅ Scales horizontally (add more nodes anytime)
✅ Provides real value to users (not just a gimmick)
✅ Positions you as helpful expert
✅ Generates qualified leads
✅ Reduces marketing costs through better targeting

---

## 🔗 Links

- **GitHub:** [Your repo URL]
- **Live Demo:** [Your GitHub Pages URL]
- **Documentation:** See files in repo
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

## 📜 License

[Choose your license - MIT recommended for open source]

---

**Built with ❤️ using email and hardware we control.**

No cloud subscriptions. No vendor lock-in. Just decentralized AI that works.

Welcome to the future. 🌐

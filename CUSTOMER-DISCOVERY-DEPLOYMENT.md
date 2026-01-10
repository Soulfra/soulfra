# Customer Discovery AI - GitHub Pages Deployment Guide

**Deploy your decentralized customer discovery tool in 10 minutes**

Give your users a frontend to dial in their ideal customer target, reduce marketing costs, and discover adjacent opportunities.

---

## What You're Deploying

A **marketing-focused AI interface** that helps users:
- 👤 Build ideal customer personas
- 🔴🔵 A/B test marketing messages
- 🔗 Find adjacent marketing opportunities
- 💾 Save and export customer profiles

All powered by your decentralized email-based Ollama network!

---

## Quick Deploy (5 Minutes)

### Step 1: Configure Node Email

Edit `customer-discovery-chat.html` line 689:

```javascript
const NODE_EMAIL = 'ollama@yourdomain.com'; // Replace with YOUR node email
```

Replace with the email address your nodes are monitoring.

### Step 2: Push to GitHub

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Add files
git add customer-discovery-chat.html
git add index.html  # We'll create this next
git commit -m "Add customer discovery AI tool"

# Push to your repo
git push origin main
```

### Step 3: Enable GitHub Pages

1. Go to your repo on GitHub
2. Settings → Pages
3. Source: `main` branch
4. Folder: `/` (root)
5. Save

**Your site will be live at:**
`https://YOUR_USERNAME.github.io/YOUR_REPO/`

---

## Setup Your Node Network

Make sure at least one node is running to process requests:

### Option A: Mac Node

```bash
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD \
  --node-name "mac-primary"
```

### Option B: Multiple Nodes for Redundancy

```bash
# Terminal 1: Mac
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD \
  --node-name "mac-node"

# Terminal 2: Raspberry Pi
ssh pi@raspberrypi.local
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD \
  --node-name "pi-backup"

# Terminal 3: Old iPhone (via Termux)
python ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD \
  --node-name "iphone-relay" \
  --ollama-url "http://YOUR_MAC_IP:11434"
```

---

## Link from Your Website

Add these links to your main site to direct users to the tool:

```html
<!-- Simple text link -->
<a href="https://YOUR_USERNAME.github.io/YOUR_REPO/customer-discovery-chat.html">
    Try Our Customer Discovery AI
</a>

<!-- Button style -->
<a href="https://YOUR_USERNAME.github.io/YOUR_REPO/customer-discovery-chat.html"
   style="background: #00d4ff; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none;">
    🎯 Find Your Ideal Customer
</a>

<!-- With description -->
<div>
    <h3>Need Help Finding Your Target Market?</h3>
    <p>Use our free AI-powered customer discovery tool to:</p>
    <ul>
        <li>Build detailed customer personas</li>
        <li>Test marketing messages with A/B comparisons</li>
        <li>Discover adjacent marketing opportunities</li>
        <li>Reduce marketing costs with better targeting</li>
    </ul>
    <a href="https://YOUR_USERNAME.github.io/YOUR_REPO/customer-discovery-chat.html">
        Get Started Free →
    </a>
</div>
```

---

## Integration with GitHub Faucet

Users need API keys to use the tool. Two options:

### Option A: Use Existing GitHub Faucet

If you have the GitHub Faucet running:

1. Update link in `customer-discovery-chat.html` (line ~670):
   ```javascript
   Get one from the <a href="https://YOUR_FAUCET_URL/github/connect">GitHub Faucet</a>
   ```

2. Users connect GitHub account → get API key → use tool

### Option B: Manual API Key Distribution

Create keys manually:

```bash
python3 -c "
from database import get_db
import secrets

db = get_db()

# Create API key for user
username = 'customer_name'
api_key = f'sk_github_{username}_{secrets.token_hex(8)}'

db.execute('''
    INSERT INTO api_keys (user_id, api_key, is_active, created_at)
    VALUES (1, ?, 1, datetime('now'))
''', (api_key,))

db.commit()
db.close()

print(f'API Key: {api_key}')
"
```

Then email the API key to your customer.

---

## Use Cases

### 1. Help Customers Find Their Target Market

**Scenario:** You offer marketing services and want to help prospects define their ideal customer.

**Implementation:**
- Link to customer-discovery-chat.html from your website
- "Before we can help with marketing, let's find your ideal customer"
- They use the tool, get insights, share results with you
- You now know their target market before first call

**Benefit:** Better qualified leads, faster sales cycle

---

### 2. Adjacent Marketing Discovery

**Scenario:** You run a local business directory and want to suggest cross-promotions.

**Implementation:**
- Give each business owner an API key
- They describe their business in the "Adjacent Marketing" tab
- AI suggests complementary businesses for partnerships
- You facilitate connections between businesses

**Benefit:** Increased value, businesses stay on platform longer

---

### 3. Marketing Message Testing

**Scenario:** You're a copywriter offering A/B testing services.

**Implementation:**
- Give prospects free access to A/B test generator
- They test headlines/CTAs and see value immediately
- Upgrade to your full service for implementation
- They're already convinced A/B testing works

**Benefit:** Free trial that demonstrates value, higher conversions

---

### 4. Content Marketing for Agencies

**Scenario:** You want to attract businesses who need help with targeting.

**Implementation:**
- Blog post: "Not sure who your ideal customer is? Try our free AI tool"
- Readers use tool, get value
- Email follow-up: "Want help implementing these insights?"
- Convert readers to customers

**Benefit:** Lead magnet that provides actual value

---

## Customization Ideas

### Add Your Branding

Edit `customer-discovery-chat.html`:

```html
<!-- Line 33: Change header -->
<h1>🎯 [Your Brand] Customer Discovery AI</h1>

<!-- Line 34: Change tagline -->
<div class="tagline">Find Your Perfect Customer - Powered by [Your Company]</div>

<!-- Colors (lines 15-16) -->
background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
```

### Add Analytics

Before `</head>` tag, add:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Capture Leads

Add to persona/AB/adjacent request functions:

```javascript
// Before sending to network, log to your CRM
fetch('https://your-api.com/leads', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: userEmail,
        action: 'customer_discovery_request',
        timestamp: new Date().toISOString()
    })
});
```

---

## Advanced: Multi-Domain Deployment

Deploy the same tool across multiple domains for different niches:

### Setup

1. Create separate node emails per niche:
   - `ollama-fitness@yourdomain.com`
   - `ollama-saas@yourdomain.com`
   - `ollama-ecommerce@yourdomain.com`

2. Customize `customer-discovery-chat.html` for each:
   - Different NODE_EMAIL
   - Niche-specific branding
   - Industry-specific templates

3. Deploy to separate repos/pages:
   - `fitness.yourdomain.com`
   - `saas.yourdomain.com`
   - `ecommerce.yourdomain.com`

4. Run nodes monitoring different inboxes:
   ```bash
   # Different nodes for different niches
   python3 ollama_email_node.py --email ollama-fitness@domain.com ...
   python3 ollama_email_node.py --email ollama-saas@domain.com ...
   ```

**Result:** Separate customer discovery tools for each vertical you serve!

---

## Monetization Strategies

### 1. Freemium Model

- Free: 5 AI requests per month (enforced via API key tier)
- Paid: Unlimited requests + saved profiles + priority processing

### 2. Lead Qualification Tool

- Give it away free to qualify leads
- Upsell consulting after they see results
- You know their exact pain points from their questions

### 3. White Label for Agencies

- Sell customized versions to marketing agencies
- They deploy for their clients
- You provide the node infrastructure
- Monthly fee per agency

### 4. Data Insights

- Aggregate anonymized trends from questions
- "What are businesses asking about their customers?"
- Sell trend reports to investors/market researchers

---

## Troubleshooting

### Users Not Receiving Responses

**Check:**
```bash
# Is your node running?
ps aux | grep ollama_email_node

# Is Ollama available?
curl http://localhost:11434/api/tags

# Check node logs for errors
python3 ollama_email_node.py --email ... --password ...
# Look for error messages
```

### Email Client Doesn't Open

**Issue:** Browser blocking `mailto:` links

**Fix:** Users need to:
1. Set default email client (Mail, Gmail, Outlook)
2. Or manually compose email with pre-filled info shown on page

### API Keys Not Working

**Check database:**
```bash
python3 -c "
from database import get_db
db = get_db()
keys = db.execute('SELECT api_key, is_active FROM api_keys').fetchall()
for key in keys:
    print(f'{key[0]} - Active: {key[1]}')
db.close()
"
```

---

## Performance Optimization

### Faster Response Times

1. **Run Ollama on fast hardware**
   - M1/M2 Mac = ~10-20 seconds
   - Desktop GPU = ~5-15 seconds
   - Raspberry Pi 5 = ~30-60 seconds

2. **Multiple nodes for load balancing**
   - First available node processes request
   - Distribute load across devices

3. **Smaller models for speed**
   ```bash
   ollama pull llama3:8b  # Faster
   ollama pull phi3       # Even faster
   ```

### Scale to Many Users

1. **Email account limits**
   - Gmail: 500 emails/day (250 requests/day since 2 emails per request)
   - Solution: Multiple node emails, round-robin

2. **Multiple node pools**
   ```bash
   # Pool 1
   --email ollama1@domain.com

   # Pool 2
   --email ollama2@domain.com

   # Pool 3
   --email ollama3@domain.com
   ```

3. **Frontend load balancing**
   - Randomly assign users to pools
   - Or tier-based (free users → pool1, paid → pool2)

---

## Analytics & Insights

### Track Usage

Add to each request function:

```javascript
function trackUsage(action) {
    localStorage.setItem(`usage_${action}`,
        (parseInt(localStorage.getItem(`usage_${action}`) || '0') + 1).toString()
    );
}

// Call when sending requests
trackUsage('persona_request');
trackUsage('ab_test');
trackUsage('adjacent_marketing');
```

### Aggregate Stats

```javascript
function showStats() {
    const stats = {
        persona: localStorage.getItem('usage_persona_request') || 0,
        ab: localStorage.getItem('usage_ab_test') || 0,
        adjacent: localStorage.getItem('usage_adjacent_marketing') || 0
    };

    console.log('User behavior:', stats);
    // Send to your analytics
}
```

---

## Next Steps

### Immediate

1. ✅ Deploy `customer-discovery-chat.html` to GitHub Pages
2. ✅ Start at least one node to process requests
3. ✅ Link from your main website
4. ✅ Test the full flow

### Short Term

1. Customize branding and colors
2. Add analytics tracking
3. Create onboarding documentation for users
4. Set up automated email with "Here's your API key"

### Long Term

1. Build API key tier system (free/paid)
2. Add more persona templates for specific industries
3. Create video tutorials
4. Partner with complementary services
5. Launch affiliate program for referrals

---

## Files You Created

1. **`customer-discovery-chat.html`** - The main customer discovery interface
2. **`ollama_email_node.py`** - Node script (runs on any device)
3. **`CUSTOMER-DISCOVERY-DEPLOYMENT.md`** - This guide
4. **`DECENTRALIZED-EMAIL-NETWORK.md`** - Technical details of email network

---

## Support

**Documentation:**
- Email network guide: `DECENTRALIZED-EMAIL-NETWORK.md`
- Node setup: See `ollama_email_node.py` header comments

**Community:**
- GitHub Issues for bugs
- Discussions for feature requests

---

## Summary

**What you deployed:**
- Marketing-focused customer discovery tool
- 100% static (GitHub Pages compatible)
- Powered by decentralized email network
- Uses your own hardware (Macs, Pis, old phones)

**Cost:** $0 (or cost of hardware you already own)

**Deployment:** 10 minutes

**Maintenance:** Start nodes when devices restart

**Value:** Help users find their ideal customers, test marketing, discover opportunities

---

**Ready to help your users dial in their ideal customer target! 🎯**

No cloud subscriptions. No vendor lock-in. Just email and hardware you control.

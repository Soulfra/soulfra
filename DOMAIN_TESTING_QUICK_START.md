# Domain Testing Quick Start - Customer Discovery + Unlock System

**Test the complete customer discovery tool across all 7 domains with unlock progression**

---

## 🎯 Your 7 Domains

From `domains-simple.txt`:

| Domain | Category | Tier | Unlock Requirement |
|--------|----------|------|-------------------|
| **soulfra.com** | Home/General | 0 | Always free (entry point) |
| **deathtodata.com** | Privacy | 1 | 5 customer discovery queries |
| **calriven.com** | Tech/Creative | 1 | 5 customer discovery queries |
| **howtocookathome.com** | Cooking | 2 | 10 queries OR 2+ domains owned |
| **hollowtown.com** | Dark/Gothic | 2 | 10 queries OR 2+ domains owned |
| **oofbox.com** | Quirky/Weird | 3 | 15 queries OR high-quality profiles |
| **niceleak.com** | Security/Privacy | 3 | 15 queries OR high-quality profiles |

---

## 🚀 Quick Test Flow (10 Minutes)

### Step 1: Setup Local Domains

```bash
# Add domains to /etc/hosts for local testing
sudo python3 local_domain_tester.py --setup

# Verify Flask is running
curl http://localhost:5001/api/health
```

### Step 2: Test Each Domain

```bash
# Test soulfra.com (Tier 0 - should work)
open http://soulfra.local:5001

# Test customer discovery tool
open http://soulfra.local:5001/customer-discovery-chat.html

# Test deathtodata.com (Tier 1 - locked until 5 queries)
open http://deathtodata.local:5001
```

### Step 3: Simulate Unlock Progression

```python
# Run this to simulate user completing queries
python3 -c "
from domain_unlock_engine import *
from database import get_db

user_id = 1

# Simulate 5 customer discovery queries
db = get_db()
for i in range(5):
    db.execute('''
        INSERT INTO user_question_answers (user_id, question_id, answer)
        VALUES (?, 1, 'test answer')
    ''', (user_id,))
db.commit()
db.close()

# Check if can unlock
eligibility = check_unlock_eligibility(user_id)
print(f'Can unlock: {eligibility[\"can_unlock\"]}')
print(f'Unlocks available: {eligibility[\"unlocks_available\"]}')

# Auto-unlock next domain
next_domain = auto_unlock_next_domain(user_id, 'customer_discovery')
print(f'Unlocked: {next_domain}')
"
```

### Step 4: Test Domain-Specific Email Nodes

```bash
# Terminal 1: Soulfra node
python3 ollama_email_node.py \
  --email ollama-soulfra@yourdomain.com \
  --password YOUR_PASSWORD \
  --node-name "soulfra-node"

# Terminal 2: DeathToData node (privacy-focused responses)
python3 ollama_email_node.py \
  --email ollama-deathtodata@yourdomain.com \
  --password YOUR_PASSWORD \
  --node-name "deathtodata-node"

# Terminal 3: HowToCookAtHome node (food-focused)
python3 ollama_email_node.py \
  --email ollama-cooking@yourdomain.com \
  --password YOUR_PASSWORD \
  --node-name "cooking-node"
```

---

## 📝 What to Test

### Test 1: Domain Access Control
- [ ] Visit soulfra.local:5001 → Works (Tier 0)
- [ ] Visit deathtodata.local:5001 → Shows "Unlock Required" (Tier 1)
- [ ] Complete 5 customer discovery queries on soulfra
- [ ] Visit deathtodata.local:5001 → Now accessible
- [ ] Check ownership: `python3 domain_unlock_engine.py 1`

### Test 2: Customer Discovery Tool
- [ ] Open customer-discovery-chat.html on soulfra.local
- [ ] Test Persona Builder → sends email to ollama-soulfra@
- [ ] Test A/B Testing → generates red/blue options
- [ ] Test Adjacent Marketing → finds opportunities
- [ ] Save profile → counts as contribution

### Test 3: Domain-Specific Branding
- [ ] soulfra → General marketing templates
- [ ] deathtodata → Privacy-focused templates
- [ ] howtocookathome → Food business templates
- [ ] calriven → Tech/creative templates

### Test 4: Unlock Progression
- [ ] Start with soulfra (owned by default)
- [ ] Use customer discovery 5 times → unlock Tier 1 domain
- [ ] Use 10 times total → unlock Tier 2 domain
- [ ] Save 3 high-quality profiles → bonus unlock
- [ ] Check progression: `python3 domain_unlock_engine.py 1`

### Test 5: Email Network Routing
- [ ] Send query from soulfra → ollama-soulfra@ processes
- [ ] Send query from deathtodata → ollama-deathtodata@ processes
- [ ] Response email shows which node processed it
- [ ] Verify 30-60 second response time

---

## 🔧 Manual Integration Steps

Since we're in plan mode, here are the manual changes needed:

### Update `customer-discovery-chat.html`

Add domain detection and unlock UI:

```html
<!-- Add after line 682 (before </body>) -->
<script>
// Detect current domain
function getCurrentDomain() {
    const hostname = window.location.hostname;
    // Remove .local for testing, keep actual domain
    return hostname.replace('.local', '.com');
}

// Get domain-specific node email
function getNodeEmail() {
    const domain = getCurrentDomain();
    const domainSlug = domain.split('.')[0];
    return `ollama-${domainSlug}@yourdomain.com`;
}

// Update NODE_EMAIL dynamically
const DETECTED_DOMAIN = getCurrentDomain();
const NODE_EMAIL = getNodeEmail();

console.log(`Domain detected: ${DETECTED_DOMAIN}`);
console.log(`Node email: ${NODE_EMAIL}`);

// Load domain-specific templates
function loadDomainTemplates() {
    const domain = getCurrentDomain();

    // Domain-specific customization
    const domainConfig = {
        'soulfra.com': {
            color: '#6366f1',
            tagline: 'Find Your Ideal Customer',
            focus: 'General marketing and business'
        },
        'deathtodata.com': {
            color: '#dc2626',
            tagline: 'Privacy-First Customer Discovery',
            focus: 'Privacy-conscious customers'
        },
        'howtocookathome.com': {
            color: '#f59e0b',
            tagline: 'Food Business Customer Insights',
            focus: 'Home cooks and food enthusiasts'
        },
        'calriven.com': {
            color: '#10b981',
            tagline: 'Creative & Tech Customer Discovery',
            focus: 'Creative professionals and developers'
        }
    };

    const config = domainConfig[domain] || domainConfig['soulfra.com'];

    // Apply branding
    document.querySelector('.tagline').textContent = config.tagline;
    document.documentElement.style.setProperty('--primary-color', config.color);
}

// Run on load
window.addEventListener('load', loadDomainTemplates);
</script>
```

### Update `domain_unlock_engine.py`

Add customer discovery tracking (after line 57):

```python
UNLOCK_THRESHOLDS = {
    'questions_answered': 10,
    'ideas_posted': 5,
    'voice_memos': 3,
    'high_score_idea': 80,
    'customer_discovery_queries': 5  # NEW: Track customer discovery usage
}
```

Update `check_unlock_eligibility()` function (after line 213):

```python
# Count customer discovery queries (add after line 206)
discovery_queries = db.execute('''
    SELECT COUNT(*) as count FROM customer_discovery_queries
    WHERE user_id = ?
''', (user_id,)).fetchone()
discovery_count = discovery_queries['count'] if discovery_queries else 0

# Add to unlock calculation (after line 235)
if discovery_count >= UNLOCK_THRESHOLDS['customer_discovery_queries']:
    unlocks_available += discovery_count // UNLOCK_THRESHOLDS['customer_discovery_queries']
    unlock_reasons.append(f"customer discovery ({discovery_count}/{UNLOCK_THRESHOLDS['customer_discovery_queries']})")
```

### Create Database Table

```sql
-- Run this in your database
CREATE TABLE IF NOT EXISTS customer_discovery_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    domain TEXT NOT NULL,
    query_type TEXT NOT NULL, -- 'persona', 'ab_test', 'adjacent', 'custom'
    query_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX idx_customer_discovery_user ON customer_discovery_queries(user_id);
CREATE INDEX idx_customer_discovery_domain ON customer_discovery_queries(domain);
```

---

## 🎮 Testing Scenarios

### Scenario 1: New User Journey

```bash
# 1. User visits soulfra.com (first time)
open http://soulfra.local:5001

# 2. Clicks "Customer Discovery Tool"
# 3. Sees: "You own 1 domain: soulfra.com"
# 4. Sees: "Unlock more domains by using this tool!"

# 5. Uses Persona Builder 5 times
# For each query, log to database:
INSERT INTO customer_discovery_queries (user_id, domain, query_type)
VALUES (1, 'soulfra.com', 'persona');

# 6. After 5th query → UNLOCK NOTIFICATION
# "🎉 You unlocked deathtodata.com! +2% ownership"

# 7. Visit deathtodata.local:5001 → Now accessible
# 8. See privacy-focused templates
# 9. Continue progression...
```

### Scenario 2: Power User (Unlock All 7)

```python
# Simulate power user unlocking all domains
user_id = 1

# Complete 20 customer discovery queries
for i in range(20):
    db.execute('''
        INSERT INTO customer_discovery_queries (user_id, domain, query_type)
        VALUES (?, 'soulfra.com', 'persona')
    ''', (user_id,))

# Save 5 high-quality profiles
for i in range(5):
    db.execute('''
        INSERT INTO user_question_answers (user_id, question_id, answer)
        VALUES (?, 1, 'high quality answer with 90 score')
    ''', (user_id,))

# Check eligibility
eligibility = check_unlock_eligibility(user_id)
print(f"Can unlock {eligibility['unlocks_available']} domains")

# Auto-unlock all available
while eligibility['can_unlock']:
    domain = auto_unlock_next_domain(user_id, 'customer_discovery')
    print(f"Unlocked: {domain}")
    eligibility = check_unlock_eligibility(user_id)

# Show owned domains
domains = get_user_domains(user_id)
for d in domains:
    print(f"✅ {d['domain']}: {d['ownership_percentage']}%")
```

### Scenario 3: Domain-Specific Email Routing

```bash
# User on deathtodata.com sends privacy persona query
# Email goes to: ollama-deathtodata@yourdomain.com
# Node processes with privacy-focused prompt
# Response includes: "Processed by: deathtodata-node"

# User on howtocookathome.com sends food business query
# Email goes to: ollama-cooking@yourdomain.com
# Node uses food industry context
# Response tailored to cooking businesses
```

---

## 📊 Monitoring & Verification

### Check User Progress

```python
python3 domain_unlock_engine.py 1

# Output:
# ============================================================
# DOMAIN OWNERSHIP - User #1
# ============================================================
#
# 📊 Stats:
#    • questions: 0
#    • ideas: 0
#    • recordings: 0
#    • high_score: 0
#    • customer_discovery: 12
#
# 🏆 Ownership:
#    Domains owned: 3
#    Can unlock: 1 more
#
#    Earned through: customer discovery (12/5)
#
# 💎 Your Domains:
#    • soulfra.com: 5.0% (unlocked: 2026-01-02)
#    • deathtodata.com: 2.0% (unlocked: 2026-01-02)
#    • calriven.com: 2.0% (unlocked: 2026-01-02)
```

### Check Email Node Status

```bash
# Check if nodes are processing
tail -f ollama_email_node.log

# Should see:
# [2026-01-02 10:30:15] 📧 New request from user@example.com
# [2026-01-02 10:30:16] 🤖 Processing with Ollama...
# [2026-01-02 10:30:45] ✅ Request processed and response sent
```

---

## 🐛 Troubleshooting

### "Domain not unlocking after 5 queries"

```bash
# Check customer_discovery_queries table
python3 -c "
from database import get_db
db = get_db()
count = db.execute('SELECT COUNT(*) FROM customer_discovery_queries WHERE user_id = 1').fetchone()[0]
print(f'Queries logged: {count}')
db.close()
"

# If count is 0, queries aren't being logged
# Need to add logging to customer-discovery-chat.html
```

### "Email node not receiving requests"

```bash
# Test email connectivity
python3 -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('ollama-soulfra@domain.com', 'password')
mail.select('INBOX')
status, messages = mail.search(None, 'UNSEEN')
print(f'Unread emails: {len(messages[0].split())}')
mail.close()
"
```

### "Unlock UI not showing"

```javascript
// Check browser console
console.log('Current domain:', getCurrentDomain());
console.log('Node email:', getNodeEmail());
console.log('Owned domains:', /* fetch from API */);
```

---

## 🎯 Success Metrics

Track these to validate the unlock system:

- ✅ Users can access soulfra.com immediately (Tier 0)
- ✅ Tier 1 domains locked initially
- ✅ After 5 queries, Tier 1 unlocks
- ✅ Each domain shows custom branding
- ✅ Email routes to domain-specific nodes
- ✅ Ownership % increases with usage
- ✅ All 7 domains unlockable through progression

---

## 📚 Next Steps

1. **Test manually** using this guide
2. **Verify unlock progression** works
3. **Check email routing** per domain
4. **Validate branding** changes per domain
5. **Monitor database** for query logging
6. **Deploy to GitHub Pages** when ready

---

**You now have a complete gamified customer discovery platform with domain unlock progression! 🚀**

Test locally using `.local` domains, then deploy each domain's customized version to GitHub Pages.

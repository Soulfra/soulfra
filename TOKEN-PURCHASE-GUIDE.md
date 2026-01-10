# 💰 Token Purchase System - Complete Guide

**Created:** December 31, 2024
**Purpose:** Pay-as-you-go alternative to subscriptions

---

## 🎯 What You Asked For

**Question:** "how do we prove this with tokens and people buy tokens or something with stripe or oss checkouts and link or plaid"

**Answer:** ✅ Built complete token purchase system with:
- Stripe Checkout integration (supports Link, Apple Pay, Google Pay)
- Pay-as-you-go model (alternative to subscriptions)
- Token balance tracking
- Usage analytics
- Purchase history

---

## 🆚 Two Payment Models

### Model 1: Subscriptions (Already Exists)
**File:** `membership_system.py`

- **Free:** $0/mo - 10 domains
- **Pro:** $5/mo - 50 domains
- **Premium:** $10/mo - Unlimited domains

### Model 2: Tokens (NEW - Just Built!)
**File:** `token_purchase_system.py`

- **Starter Pack:** 100 tokens for $10 ($0.10/token)
- **Pro Pack:** 500 tokens for $40 ($0.08/token) - 20% savings
- **Premium Pack:** 1000 tokens for $70 ($0.07/token) - 30% savings

**Users can choose:** Monthly subscription OR buy tokens as needed!

---

## 🪙 What Can You Do With Tokens?

| Action | Token Cost |
|--------|-----------|
| Import a domain | 1 token |
| AI brand analysis | 5 tokens |
| CSV import (up to 50 domains) | 2 tokens |
| Data export | 10 tokens |

**Example:**
- Buy Pro Pack (500 tokens) for $40
- Import 100 domains = 100 tokens
- Run 50 AI analyses = 250 tokens
- Export data 5 times = 50 tokens
- **Total:** 400 tokens used, 100 remaining

---

## 🏗️ System Architecture

### Database Tables (NEW)

**purchases table:**
```sql
CREATE TABLE purchases (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  type TEXT,  -- 'subscription' or 'tokens'
  amount REAL,  -- dollars (e.g., 10.00)
  tokens INTEGER,  -- token count if type='tokens'
  description TEXT,
  stripe_payment_intent_id TEXT,
  stripe_checkout_session_id TEXT,
  status TEXT,  -- 'pending', 'completed', 'failed', 'refunded'
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);
```

**token_usage table:**
```sql
CREATE TABLE token_usage (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  tokens_spent INTEGER,
  action TEXT,  -- 'import_domain', 'ai_analysis', etc.
  metadata TEXT,  -- JSON with context
  created_at TIMESTAMP
);
```

**brands table (UPDATED):**
```sql
-- Added new column:
ALTER TABLE brands ADD COLUMN is_test BOOLEAN DEFAULT 0;
```

### Core Files

**1. token_purchase_system.py** - Backend logic
- Token packages configuration
- Stripe Checkout integration
- Balance tracking
- Usage tracking
- Statistics

**2. token_routes.py** - Flask API
- `/api/tokens/packages` - Get available packages
- `/api/tokens/balance` - Get user balance
- `/api/tokens/purchase` - Create Stripe Checkout
- `/api/tokens/history` - Purchase history
- `/api/tokens/usage` - Usage history
- `/api/tokens/webhook` - Stripe webhook handler

**3. Templates:**
- `admin_tokens.html` - Main token purchase page
- `token_purchase_success.html` - Success page
- `token_purchase_cancel.html` - Cancel page

**4. Database Migration:**
- `migrations/add_purchases_table.sql` - Run once to setup

---

## 🚀 How to Use

### For Users

**1. Visit Token Purchase Page:**
```
http://localhost:5001/admin/tokens
```

**2. View Your Balance:**
- Current balance shown prominently
- See purchase history
- View usage breakdown

**3. Buy Tokens:**
- Click "Purchase Now" on any package
- Redirects to Stripe Checkout
- Pay with:
  - Stripe Link (one-click if saved)
  - Credit/debit card
  - Apple Pay
  - Google Pay

**4. Use Tokens:**
- Import domains (1 token each)
- Run AI analysis (5 tokens)
- Export data (10 tokens)
- CSV imports (2 tokens)

### For Developers

**1. Run Database Migration:**
```bash
sqlite3 soulfra.db < migrations/add_purchases_table.sql
```

**2. Test Token System (Without Stripe):**
```bash
python3 token_purchase_system.py
```

Output:
```
🪙 TOKEN PURCHASE SYSTEM TEST
📊 Token Packages:
   Starter Pack: 100 tokens for $10.00
   Pro Pack ⭐ POPULAR: 500 tokens for $40.00
   Premium Pack: 1000 tokens for $70.00

💰 Current Balance: 0 tokens
🧪 Simulating purchase: Pro Pack (500 tokens)...
✅ User 1 spent 1 tokens for import_domain. Balance: 499
```

**3. Enable Stripe (Production):**
```bash
export STRIPE_ENABLED=true
export STRIPE_SECRET_KEY=sk_live_...
export STRIPE_PUBLISHABLE_KEY=pk_live_...
export STRIPE_WEBHOOK_SECRET=whsec_...
```

**4. Check Token Balance in Code:**
```python
from token_purchase_system import get_token_balance, spend_tokens

# Check balance
balance = get_token_balance(user_id=1)
print(f"Balance: {balance} tokens")

# Spend tokens
success = spend_tokens(
    user_id=1,
    action='import_domain',
    metadata={'domain': 'example.com'}
)

if success:
    print("✅ Tokens spent successfully")
else:
    print("❌ Insufficient tokens")
```

---

## 🔄 How It Connects to Everything

### Integration 1: With Domain Import

**Before (required subscription):**
```python
# Check membership tier
membership = get_membership(user_id)
if membership['tier'] == 'free' and domain_count >= 10:
    return "Upgrade to Pro for more domains"
```

**Now (subscription OR tokens):**
```python
from token_purchase_system import get_token_balance, spend_tokens

# Check if user has tokens OR valid subscription
balance = get_token_balance(user_id)
membership = get_membership(user_id)

if balance >= 1:
    # Use token
    spend_tokens(user_id, 'import_domain', {'domain': domain})
    import_domain(domain)
elif membership['tier'] in ['pro', 'premium']:
    # Use subscription
    import_domain(domain)
else:
    return "Buy tokens or upgrade subscription"
```

### Integration 2: With AI Analysis

**File:** Any route that uses AI

```python
@app.route('/api/domains/<id>/analyze')
def analyze_domain(id):
    balance = get_token_balance(session['user_id'])

    if balance < 5:
        return jsonify({
            'error': 'Insufficient tokens',
            'required': 5,
            'balance': balance
        }), 402  # Payment Required

    # Spend tokens
    spend_tokens(session['user_id'], 'ai_analysis', {'brand_id': id})

    # Run AI analysis
    result = run_ai_analysis(id)
    return jsonify(result)
```

### Integration 3: With Query System

**Combine with `query_by_tier.py`:**

```bash
# Export foundation domains (costs 10 tokens)
python3 query_by_tier.py --tier foundation --export json

# In code:
from token_purchase_system import spend_tokens
from query_by_tier import get_domains_by_tier, export_domains

# Check tokens
if get_token_balance(user_id) < 10:
    print("❌ Need 10 tokens for export")
else:
    # Spend tokens
    spend_tokens(user_id, 'data_export', {'tier': 'foundation'})

    # Export
    domains = get_domains_by_tier('foundation')
    json_export = export_domains(domains, 'json')
    print(json_export)
```

### Integration 4: With Verification System

**Combine with `verify_import.py`:**

```python
# Before CSV import, check tokens
from token_purchase_system import get_token_balance, spend_tokens
from verify_import import generate_pre_check_proof

# Pre-check
proof = generate_pre_check_proof('test-domains-50.csv')
expected_domains = proof['expected']['total_domains']

# Check if user has tokens for CSV import
balance = get_token_balance(user_id)
if balance < 2:
    print(f"❌ Need 2 tokens for CSV import (importing {expected_domains} domains)")
else:
    # Spend tokens
    spend_tokens(user_id, 'csv_import', {'csv_file': 'test-domains-50.csv', 'count': expected_domains})

    # Import via UI
    print("✅ Tokens spent. Proceed with import at http://localhost:5001/admin/domains/csv")
```

---

## 📊 API Endpoints

### Get Token Balance
```bash
curl http://localhost:5001/api/tokens/balance
```

Response:
```json
{
  "balance": 494,
  "user_id": 1
}
```

### Get Packages
```bash
curl http://localhost:5001/api/tokens/packages
```

Response:
```json
{
  "packages": {
    "starter": {
      "name": "Starter Pack",
      "tokens": 100,
      "price": 10.00,
      "savings": "0%"
    },
    "pro": {
      "name": "Pro Pack",
      "tokens": 500,
      "price": 40.00,
      "savings": "20%",
      "popular": true
    }
  },
  "costs": {
    "import_domain": 1,
    "ai_analysis": 5,
    "csv_import": 2,
    "data_export": 10
  }
}
```

### Purchase Tokens
```bash
curl -X POST http://localhost:5001/api/tokens/purchase \
  -H "Content-Type: application/json" \
  -d '{"package": "pro"}'
```

Response:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_...",
  "session_id": "cs_...",
  "package": "pro",
  "tokens": 500,
  "price": 40.00
}
```

### Get Statistics
```bash
curl http://localhost:5001/api/tokens/stats
```

Response:
```json
{
  "balance": 494,
  "total_purchased": 500,
  "total_spent_usd": 40.00,
  "purchase_count": 1,
  "usage_breakdown": [
    {
      "action": "ai_analysis",
      "tokens": 5,
      "count": 1
    },
    {
      "action": "import_domain",
      "tokens": 1,
      "count": 1
    }
  ]
}
```

---

## 🔐 Stripe Checkout Flow

### Step 1: User Clicks "Purchase Now"

**JavaScript (in `admin_tokens.html`):**
```javascript
async function purchaseTokens(package) {
  const response = await fetch('/api/tokens/purchase', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ package: package })
  });

  const data = await response.json();

  if (data.checkout_url) {
    // Redirect to Stripe Checkout
    window.location.href = data.checkout_url;
  }
}
```

### Step 2: Backend Creates Checkout Session

**Python (in `token_purchase_system.py`):**
```python
session = stripe.checkout.Session.create(
    customer=customer_id,
    payment_method_types=['card'],  # Supports Link, Apple Pay, Google Pay
    line_items=[{
        'price_data': {
            'currency': 'usd',
            'product_data': {
                'name': 'Pro Pack',
                'description': '500 tokens - Save 20%'
            },
            'unit_amount': 4000  # $40.00 in cents
        },
        'quantity': 1
    }],
    mode='payment',  # One-time payment (not subscription)
    success_url='http://localhost:5001/tokens/success',
    cancel_url='http://localhost:5001/tokens/cancel'
)
```

### Step 3: User Completes Payment

- Redirected to Stripe Checkout page
- Can use:
  - Stripe Link (one-click if saved)
  - Credit/debit card
  - Apple Pay
  - Google Pay

### Step 4: Webhook Confirms Payment

**Stripe sends webhook to `/api/tokens/webhook`:**

```python
@token_bp.route('/api/tokens/webhook', methods=['POST'])
def stripe_webhook():
    event = stripe.Webhook.construct_event(
        request.data,
        request.headers.get('Stripe-Signature'),
        STRIPE_WEBHOOK_SECRET
    )

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        handle_token_purchase_completed(session_data)

        # Updates purchase record:
        # - Set status = 'completed'
        # - Add payment_intent_id
        # - Set completed_at timestamp
```

### Step 5: User Redirected to Success Page

```
http://localhost:5001/tokens/success?session_id=cs_...
```

Shows:
- ✅ Purchase successful
- Current token balance
- Links to use tokens

---

## 🎯 Real-World Usage Example

**Scenario:** User wants to import 100 test domains and analyze 10 of them

**Step 1: Check Cost**
- Import 100 domains = 100 tokens
- Analyze 10 domains = 50 tokens
- **Total needed:** 150 tokens

**Step 2: Buy Tokens**
- Visit `http://localhost:5001/admin/tokens`
- Buy "Pro Pack" (500 tokens for $40)
- Complete Stripe Checkout
- Balance: 500 tokens

**Step 3: Import Domains**
```bash
# Run pre-check
python3 verify_import.py --pre-check test-domains-100.csv

# Import via UI (costs 2 tokens for CSV import)
# Each domain costs 1 token
# Total: 2 + 100 = 102 tokens spent

# Balance: 398 tokens remaining
```

**Step 4: Analyze Domains**
```bash
# Run AI analysis on 10 domains
# Each analysis costs 5 tokens
# Total: 50 tokens spent

# Balance: 348 tokens remaining
```

**Step 5: Export Results**
```bash
# Export foundation domains
python3 query_by_tier.py --tier foundation --export json
# Costs 10 tokens

# Final balance: 338 tokens remaining
```

---

## 💡 Why Two Models?

**Subscriptions (membership_system.py):**
- ✅ Predictable monthly cost
- ✅ Unlimited usage within tier limits
- ✅ Good for regular users
- ❌ Wasteful if you don't use much

**Tokens (token_purchase_system.py):**
- ✅ Pay only for what you use
- ✅ No recurring charges
- ✅ Good for occasional users
- ✅ Tokens never expire
- ❌ Can run out mid-task

**Best of both worlds:** Let users choose!

---

## 🔧 Commands You Can Run Now

### Test the System
```bash
# Test token system without Stripe
python3 token_purchase_system.py

# Run database migration
sqlite3 soulfra.db < migrations/add_purchases_table.sql

# Check your token balance
sqlite3 soulfra.db "SELECT * FROM purchases WHERE user_id = 1"
sqlite3 soulfra.db "SELECT * FROM token_usage WHERE user_id = 1"
```

### Visit the UI
```bash
# Open token purchase page
open http://localhost:5001/admin/tokens

# Check balance via API
curl http://localhost:5001/api/tokens/balance

# Get packages
curl http://localhost:5001/api/tokens/packages
```

### Simulate Purchase (Dev/Testing)
```python
from token_purchase_system import simulate_token_purchase

# Give user 500 tokens for testing
simulate_token_purchase(user_id=1, package='pro')
# Output: 🧪 SIMULATED: User 1 purchased 500 tokens. Balance: 500
```

---

## 🎓 Bottom Line

**Before:** Only subscription model (pay monthly even if not using)

**Now:**
- ✅ Token purchase system with Stripe Checkout
- ✅ Stripe Link integration (one-click payments)
- ✅ Pay-as-you-go alternative to subscriptions
- ✅ Purchase history tracking
- ✅ Usage analytics
- ✅ Balance management
- ✅ Support for Apple Pay, Google Pay, cards
- ✅ Webhook integration for payment confirmation
- ✅ Full UI with beautiful package cards
- ✅ Success/cancel pages

**Try it now:**
```bash
# Visit token purchase page
open http://localhost:5001/admin/tokens
```

**Next Steps:**
1. Enable Stripe in production (set environment variables)
2. Configure webhook endpoint in Stripe Dashboard
3. Test real purchases with Stripe test cards
4. Add token balance widget to Studio/Domains pages
5. Integrate token spending into domain import flow

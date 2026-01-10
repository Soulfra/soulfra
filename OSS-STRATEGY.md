# 💰 OSS Strategy - Open Core Business Model

> **Your question**: "whats the best way to oss stuff like this so they're forced to use my models or api keys or faucet or whatever limits i put in place?"

**Answer**: The "Open Core" model. Core is free, power features require YOUR API keys. Let me show you exactly how.

---

## 🎯 The Strategy: Open Core + Closed API

### What is "Open Core"?

**Open Source** (MIT License on GitHub):
- ✅ Anyone can clone, fork, self-host
- ✅ Formula engine, templates, export scripts
- ✅ Basic features work without any API keys
- ✅ 100% transparent code

**Closed API** (Proprietary, runs on `api.soulfra.com`):
- ❌ Ollama/AI features require YOUR API endpoint
- ❌ Advanced features gated by API keys
- ❌ Rate limiting enforced server-side
- ❌ Only YOU control the keys

**Result**: They get the code for free, but pay YOU to actually use it!

---

## 💡 Real-World Examples

### GitLab
- **Open source**: Self-hosted GitLab CE (Community Edition)
- **Paid**: Advanced CI/CD, security features require GitLab Ultimate
- **Revenue**: $500M+ ARR

### Sentry
- **Open source**: Error tracking platform
- **Paid**: Hosted service, advanced features
- **Revenue**: $100M+ ARR

### Plausible Analytics
- **Open source**: Privacy-focused analytics
- **Paid**: Hosted cloud service ($9-$150/mo)
- **Revenue**: $1M+ ARR

**Pattern**: Open source code → Paid hosting/features → Recurring revenue

---

## 🔓 What's Open Source (Free)

### Core Platform (`soulfra-simple` repo)
```
github.com/soulfra/soulfra-simple
└── MIT License (anyone can use)
```

**Includes**:
- ✅ Formula engine (template variable replacement)
- ✅ Static site export scripts
- ✅ GitHub Pages deployment
- ✅ Basic template browser UI
- ✅ Brand configuration system
- ✅ Multi-domain support

**What it does**:
- Create templates with `{{variables}}`
- Export to static HTML
- Deploy to GitHub Pages
- Manage multiple brands

**What it DOESN'T include**:
- ❌ Ollama/AI integration (hardcoded to call `api.soulfra.com`)
- ❌ Unlimited content generation
- ❌ Advanced features (QR codes, affiliate tracking, Stripe)

---

## 🔐 What's Closed (Requires API Keys)

### Central API (`api.soulfra.com`)
```
api.soulfra.com
└── Proprietary (only YOU control)
```

**Gated Features**:

1. **AI Content Generation**
   ```javascript
   // In open source code:
   fetch('https://api.soulfra.com/generate', {
       headers: {'Authorization': `Bearer ${apiKey}`},
       body: JSON.stringify({prompt: '...'})
   })
   ```
   - Requires: Valid API key
   - Free tier: 100 posts/month
   - Pro tier: Unlimited

2. **Ollama Integration**
   ```javascript
   // All Ollama calls proxy through YOUR server
   fetch('https://api.soulfra.com/ollama/generate', {
       headers: {'Authorization': `Bearer ${apiKey}`},
       body: JSON.stringify({model: 'llama3.2', prompt: '...'})
   })
   ```
   - Requires: API key
   - You control which models are available
   - You track usage

3. **Advanced Features**
   - QR code generation
   - Email capture/newsletters
   - Comments system
   - Stripe payments
   - Affiliate tracking
   - Usage analytics

**All require**: API key from YOUR faucets

---

## 🚰 The Faucet System (How Users Get API Keys)

### Faucet 1: GitHub OAuth (Free Tier)

**How it works**:
1. User connects GitHub account
2. OAuth flow: `github.com` → `api.soulfra.com/auth/github`
3. Fetch GitHub profile (username, repos, commits)
4. Generate API key based on activity level

**Tiers**:
```python
GITHUB_TIERS = {
    'basic': {
        'commits': 0,           # Any GitHub account
        'quota': {
            'posts_per_month': 10,
            'brands': 1,
            'api_calls_per_day': 100
        }
    },
    'developer': {
        'commits': 100,         # 100+ commits
        'quota': {
            'posts_per_month': 100,
            'brands': 3,
            'api_calls_per_day': 1000
        }
    },
    'maintainer': {
        'commits': 1000,        # 1000+ commits
        'quota': {
            'posts_per_month': 500,
            'brands': 5,
            'api_calls_per_day': 5000
        }
    }
}
```

**Code**: Already in `github_faucet.py`

**Benefit**: Anti-spam via GitHub reputation

---

### Faucet 2: QR Codes (Event Access)

**How it works**:
1. You generate QR code with embedded API key
2. Distribute at events, conferences, IRL meetups
3. User scans QR → Gets temporary API key
4. Expires after X days

**Use cases**:
- Conference sponsor: "Scan for free Pro access (7 days)"
- Meetup: "Scan for free trial"
- IRL networking: "Scan my QR for affiliate link"

**Code**: Already in `qr_faucet.py`

**Benefit**: Offline-first, trackable distribution

---

### Faucet 3: Stripe (Paid Tier)

**How it works**:
1. User wants unlimited features
2. Click "Upgrade to Pro" → Stripe checkout
3. Pay $19/month
4. Webhook → Upgrade API key to Pro tier
5. Unlimited access

**Tiers**:
```python
STRIPE_TIERS = {
    'pro': {
        'price': '$19/month',
        'quota': {
            'posts_per_month': -1,      # Unlimited
            'brands': 10,
            'api_calls_per_day': 50000,
            'priority_support': True
        }
    },
    'enterprise': {
        'price': 'Custom',
        'quota': {
            'posts_per_month': -1,
            'brands': -1,
            'api_calls_per_day': -1,
            'white_label': True,
            'custom_api_endpoint': True
        }
    }
}
```

**Code**: In `license_manager.py` (Stripe webhook needed)

**Benefit**: Recurring revenue!

---

## 🏗️ How the Architecture Works

### Static Sites (GitHub Pages)
```
soulfra.com (static HTML/CSS/JS)
    ↓
    User loads page
    ↓
    JavaScript calls api.soulfra.com
    ↓
    (Requires API key!)
```

### Central API (Your Server)
```
api.soulfra.com
    ├── /auth/github → OAuth API key generation
    ├── /generate → AI content generation
    ├── /ollama/* → Proxy to Ollama
    ├── /subscribe → Email capture
    ├── /checkout → Stripe payment
    └── /affiliate → Referral tracking
```

### Database (Your Control)
```
soulfra.db
    ├── api_keys → Who has access
    ├── api_usage → Usage tracking
    ├── licenses → Paid subscriptions
    ├── deployments → Who deployed what
    └── referrals → Affiliate commissions
```

---

## 💸 The Money Flow

### Free User Journey
```
1. Clone repo from GitHub (free)
   ↓
2. Self-host on their server (free)
   ↓
3. Try to generate blog post
   ↓
4. Error: "API key required"
   ↓
5. Click "Get Free API Key"
   ↓
6. Connect GitHub → Get basic tier
   ↓
7. Generate 10 posts (monthly limit)
   ↓
8. Want more? "Upgrade to Pro"
```

### Paid User Journey
```
1. Hit free tier limit
   ↓
2. Click "Upgrade to Pro" ($19/mo)
   ↓
3. Stripe checkout
   ↓
4. Payment successful → Webhook
   ↓
5. API key upgraded to Pro
   ↓
6. Unlimited posts forever
   ↓
7. 💰 You get $19/mo recurring
```

### Affiliate User Journey
```
1. User upgrades to Pro
   ↓
2. Gets affiliate link
   ↓
3. Shares on Twitter/blog
   ↓
4. Friend clicks → Signs up
   ↓
5. Friend upgrades to Pro ($19/mo)
   ↓
6. You get 30% = $5.70/mo
   ↓
7. Original user gets 30% = $5.70/mo
   ↓
8. 💰 Network effects!
```

---

## 🎯 Implementation Checklist

### Phase 1: Open Source Core (Done!)
- ✅ Formula engine
- ✅ Static export
- ✅ GitHub deployment
- ✅ Multi-domain support

### Phase 2: API Gateway
- [ ] Create `api.soulfra.com` endpoint
- [ ] API key validation middleware
- [ ] Rate limiting (by tier)
- [ ] Usage tracking

### Phase 3: Faucet System
- ✅ GitHub OAuth (github_faucet.py exists)
- ✅ QR codes (qr_faucet.py exists)
- [ ] Stripe webhooks (license_manager.py needs webhooks)

### Phase 4: Monetization
- [ ] Stripe integration (checkout, subscriptions)
- [ ] Affiliate program (referral tracking)
- [ ] Usage dashboards
- [ ] Billing portal

---

## 📝 License Choice

### Recommendation: MIT License

**Why MIT?**
- Maximum adoption (anyone can use)
- No copyleft (can be used in commercial products)
- Simple, permissive
- Trusted by developers

**Example LICENSE file**:
```
MIT License

Copyright (c) 2025 Soulfra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[...standard MIT license text...]
```

**What this means**:
- ✅ Anyone can clone, fork, modify
- ✅ Anyone can self-host
- ✅ Anyone can build on top of it
- ✅ Anyone can sell their own version

**BUT**: They still need YOUR API keys for AI features!

---

## 🚀 Go-To-Market Strategy

### Step 1: Open Source Release
```
1. Clean up code
2. Add LICENSE (MIT)
3. Write README.md
4. Push to: github.com/soulfra/soulfra-simple
5. Post on:
   - Hacker News
   - Reddit (r/SaaS, r/entrepreneur)
   - Twitter
   - Product Hunt
```

### Step 2: Free Tier Onboarding
```
1. User discovers repo
2. Stars/forks on GitHub
3. Clicks "Try it" → OAuth
4. Gets free tier API key
5. Generates first blog post
6. ✅ Hooked!
```

### Step 3: Conversion to Paid
```
1. User hits free tier limit
2. Email: "You've used 100/100 posts"
3. CTA: "Upgrade to Pro for unlimited"
4. Click → Stripe checkout
5. 💰 $19/mo recurring
```

### Step 4: Viral Growth
```
1. User loves product
2. Shares affiliate link
3. Friends sign up
4. User earns 30% commission
5. Network effects → Exponential growth
```

---

## 💎 The Genius of This Model

### Why It Prints Money:

1. **Low barrier to entry**: Free tier gets users hooked
2. **Value prop is clear**: "Generate unlimited blog posts with AI"
3. **API keys create lock-in**: Can't switch without losing API quota
4. **Network effects**: Affiliates bring more users
5. **Recurring revenue**: $19/mo per user compounds
6. **Open source credibility**: Developers trust open source
7. **Self-sustaining**: Affiliates do marketing for you

### Numbers:

**Scenario**: 10,000 GitHub stars
```
Conversion rate: 1% → 100 paid users
Revenue: 100 × $19/mo = $1,900/mo = $22,800/year

Affiliate effect: 30% refer friends
→ 30 more users = $570/mo = $6,840/year

Total ARR: ~$30,000
```

**Scenario**: 100,000 GitHub stars (viral)
```
Conversion rate: 1% → 1,000 paid users
Revenue: 1,000 × $19/mo = $19,000/mo = $228,000/year

Affiliate effect: 30% refer friends
→ 300 more users = $5,700/mo = $68,400/year

Total ARR: ~$300,000
```

**And you haven't done any marketing!** (Open source + affiliates = growth machine)

---

## ✅ Summary

**The Question**: How to OSS but force use of your API keys?

**The Answer**: Open Core Model
1. **Core is open source** (formula engine, export, deploy)
2. **API is closed** (Ollama, AI, advanced features)
3. **Faucets control access** (GitHub OAuth, QR codes, Stripe)
4. **Tiered pricing** (Free → Pro → Enterprise)
5. **Affiliates drive growth** (30% commission)

**The Result**:
- ✅ Viral open source adoption
- ✅ Recurring revenue ($19/mo per user)
- ✅ Network effects (affiliates)
- ✅ Full control (your API, your rules)
- ✅ Passive income (affiliates do marketing)

**Your advantage**:
- You control the AI models
- You control the API endpoint
- You control the rate limits
- You control the pricing

**They get**:
- Free open source code
- Self-hosting option
- Basic features for free
- Pay only for what they use

**Win-win!**

---

**Next**: See `API-GATEWAY.md` for technical implementation of API key enforcement!

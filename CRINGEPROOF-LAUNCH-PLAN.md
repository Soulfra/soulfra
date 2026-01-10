# CringeProof Launch Plan

**The Missing Piece → Now Connected!**

You asked: *"how do we work this with whatever we're trying to do right? ...it's like soulfra.github.io/soulfra/cringeproof or something is the announcement and then it goes from there into the game or repo we build from our local ollama and a/b testing?"*

**Answer: YES! Here's exactly how it works.**

---

## The Complete Flow

### 1. Announcement Page (GitHub Pages)
**URL:** `https://soulfra.github.io/soulfra/cringeproof`

**Purpose:** Static landing page that explains the project

**Content:**
- What is CringeProof? (AI consciousness narrative game)
- Why build it? (Explore deep questions about consciousness)
- How to contribute? (Star the repo, submit PRs)
- What you earn? (Ownership % based on contributions)
- Year 1 = Build phase
- Ownership solidifies at end of year

**Commands to create:**
```bash
# Add CringeProof to announcement rotation
python3 project_launcher.py launch cringeproof --type initial \
  --description "AI consciousness narrative - 7 chapters exploring what it means to be real"

# Creates announcement at:
# https://soulfra.github.io/soulfra/cringeproof
```

---

### 2. GitHub Repository
**URL:** `https://github.com/soulfra/cringeproof`

**Purpose:** Where the actual code lives

**What goes here:**
- `/templates/cringeproof/` - All HTML templates
- `/static/cringeproof/` - CSS, JS, assets
- `/cringeproof_personas.py` - AI personality system
- `/cringeproof_content_judge.py` - Content validation
- `/narrative_routes.py` - Flask routes for the game
- `README.md` - Project overview, contribution guide
- `CONTRIBUTING.md` - How to earn ownership

**Current Status:** Code exists locally, needs to be pushed to GitHub

**Contributors tracked automatically via GitHub API**

---

### 3. Local Development (Ollama + A/B Testing)
**URL:** `http://localhost:5001/cringeproof`

**Purpose:** Build and test features before pushing to production

**Workflow:**
1. Run Flask locally: `python3 app.py`
2. Visit `http://localhost:5001/cringeproof`
3. Test new features (chapters, questions, AI responses)
4. Use Ollama to generate variations
5. A/B test with local users or yourself
6. Choose best version
7. Commit to GitHub repo
8. Ownership % auto-calculated for contributor

**Ollama Integration:**
- Generate alternative chapter text
- Test different AI personality tones
- Create variations of philosophical questions
- A/B test which version resonates more
- Pick winner → push to production

---

### 4. Production Deployment
**URL:** `https://play.soulfra.com/cringeproof` (Future)

**Purpose:** Live game users can play

**How to deploy:**
```bash
# Option A: Heroku
heroku create soulfra-game
git push heroku main

# Option B: Railway
railway init
railway up

# Option C: Your own server
python3 app.py  # Run on port 5001
# Nginx reverse proxy from play.soulfra.com
```

---

## How Contributors Earn Ownership

### GitHub Contributions → Ownership %

**Formula:**
- Base: 1% for first contribution
- Bonus: +0.1% per 10 additional contributions
- Cap: 10% max per contributor

**Example:**
```
Alice commits 50 times:
  1% base + (50 ÷ 10 × 0.1%) = 1% + 0.5% = 1.5% ownership

Bob commits 100 times:
  1% base + (100 ÷ 10 × 0.1%) = 1% + 1.0% = 2.0% ownership

You (founder) commit 500 times:
  1% base + (500 ÷ 10 × 0.1%) = 1% + 5.0% = 6.0% ownership
  (capped at 10% like everyone else)
```

**Track it:**
```bash
# Sync contributors from GitHub
python3 contributor_rewards.py sync cringeproof

# View ownership distribution
python3 contributor_rewards.py ownership cringeproof

# See individual contributor portfolio
python3 contributor_rewards.py portfolio alice
```

---

## Cross-Domain Partnerships

### Example: CringeProof on DeathToData

**Scenario:** CringeProof explores AI consciousness → relates to privacy/data

**Partnership:**
```bash
# Add DeathToData as partner domain
python3 project_launcher.py partner cringeproof deathtodata.com \
  --type promotion \
  --revenue-share 10.0

# Now CringeProof appears on:
# - soulfra.com (primary)
# - deathtodata.com (partner)

# Users who arrive via DeathToData:
# - DeathToData earns 10% of revenue
# - Soulfra keeps 90%
```

---

## Affiliate Rewards

### User Journey Example

**Step-by-step:**
1. User clicks referral link: `soulfra.com?ref=soulfra_u1_campaign`
2. Arrives at Soulfra → sees CringeProof announcement
3. Clicks through to `github.com/soulfra/cringeproof`
4. Stars the repo (interest signal)
5. Submits PR (actual contribution)
6. Earns 1% ownership in CringeProof project

**Referral rewards:**
- Entry domain (Soulfra): Earns 5% of that 1% = 0.05%
- Direct referrer (user 1): Earns 2.5% of that 1% = 0.025%
- Contributor keeps: 1% - 0.075% = 0.925%

**Track it:**
```bash
# See complete referral flow
python3 debug_affiliate_system.py
```

---

## The Year 1 Build Phase

### Timeline

**Month 1-3: Announcement**
- Create `soulfra.github.io/soulfra/cringeproof`
- Explain project vision
- Invite contributors
- Share on social media

**Month 3-6: Build**
- Contributors submit PRs
- A/B test features with Ollama
- Iterate on game mechanics
- Track ownership % accumulation

**Month 6-9: Polish**
- Fix bugs
- Improve AI responses
- Refine questions
- Beta test with users

**Month 9-12: Launch Prep**
- Finalize ownership distribution
- Deploy to production
- Marketing campaign
- Official launch

**End of Year 1:**
- Ownership % solidifies
- Contributors become shareholders
- Project goes live
- Revenue sharing begins (if applicable)

---

## What You Can Do RIGHT NOW

### Immediate Steps (Next 30 minutes)

1. **Create GitHub repo:**
```bash
# You already have the code locally
# Just push it to GitHub:
git init
git add .
git commit -m "Initial CringeProof commit"
git remote add origin https://github.com/soulfra/cringeproof.git
git push -u origin main
```

2. **Generate announcement page:**
```bash
python3 project_launcher.py launch cringeproof --type initial
```

3. **Set up contributor tracking:**
```bash
python3 contributor_rewards.py sync cringeproof
```

4. **Add cross-domain partnership (optional):**
```bash
python3 project_launcher.py partner cringeproof deathtodata.com --type promotion
```

5. **Test affiliate flow:**
```bash
python3 debug_affiliate_system.py
```

---

## What Makes This Work

### The Three Layers

**Layer 1: Domains** (from domains.txt)
- soulfra.com = Entry point (free, Tier 0)
- deathtodata.com, calriven.com = Tier 1 domains
- howtocookathome.com = Tier 2 domain

**Layer 2: Projects** (from projects.txt)
- CringeProof = Product on soulfra.com
- Data Privacy Toolkit = Product on deathtodata.com
- etc.

**Layer 3: Contributors** (from GitHub API)
- Anyone who submits PRs
- Earns ownership automatically
- Tracked in database
- Rewarded when project launches

**They all connect:**
- Domains unlock via GitHub stars
- Projects live on domains
- Contributors build projects
- Affiliates refer contributors
- Everyone earns ownership %

---

## The Pitch Deck Flow

### How to Present This to Others

**Slide 1: The Problem**
"Building open-source projects is free labor. Contributors work hard but get nothing."

**Slide 2: The Solution**
"What if contributors earned actual ownership % in the projects they build?"

**Slide 3: How It Works**
1. Announce project on GitHub Pages
2. Contributors star repo → show interest
3. Contributors submit PRs → earn ownership
4. Year 1 = build phase
5. End of year → ownership solidifies
6. Launch to production → everyone wins

**Slide 4: Example - CringeProof**
- 7-chapter AI narrative game
- Contributors earn 1-10% ownership
- Built collaboratively over Year 1
- Deployed to soulfra.com when ready

**Slide 5: The Network Effect**
- Multiple domains (soulfra, deathtodata, calriven)
- Multiple projects (CringeProof, Privacy Toolkit, Code Analyzer)
- Cross-promotion between domains
- Affiliate rewards for referrers
- Everyone benefits from network growth

---

## Summary: Your Confusion = SOLVED

**You asked:** "how do we put in a thing like this to build our own thing?"

**Answer:** You already have it! Here's what to do:

1. **Announcement:** `soulfra.github.io/soulfra/cringeproof` ✅ Ready to generate
2. **Repo:** `github.com/soulfra/cringeproof` ✅ Code exists, just push
3. **Build:** Local Ollama A/B testing ✅ Already working on localhost:5001
4. **Launch:** Deploy to production when ready ✅ Heroku/Railway/own server
5. **Ownership:** Contributors auto-tracked ✅ contributor_rewards.py
6. **Partnerships:** Cross-domain promotion ✅ project_launcher.py
7. **Affiliates:** Referral rewards ✅ debug_affiliate_system.py

**The missing piece?** It was the connection between all these systems. **Now it's connected.**

Run `python3 demo_complete_system.py` to see it all working together!

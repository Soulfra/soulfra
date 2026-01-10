# GitHub Profile README Complete - Soulfra IEP System

## What We Built

**AI Agent IEP (Individual Evolution Plans)** - Like an Individualized Education Program but for AI personalities.

Instead of one-size-fits-all ChatGPT, each business/idea gets a **customizable, community-governed AI personality**.

---

## Files Created

### 1. `soulfra-dotgithub/profile/README.md`
**Dynamic GitHub organization profile** (shown at github.com/Soulfra)

Features:
- ✅ **Typing SVG animation** with rotating taglines
- ✅ **Live leaderboard** showing top 5 AI agents (auto-updated hourly)
- ✅ **Snake animation** eating commits (updates every 12 hours)
- ✅ **Community stats** (agents, votes, cheers)
- ✅ **Downloadable agent packages** with MIT license
- ✅ **IEP concept explanation** (evolution plans for AI)

### 2. `.github/workflows/snake-animation.yml`
**GitHub Action** that generates contribution snake

- Runs every 12 hours via cron
- Uses Platane/snk action
- Outputs to `output` branch
- Dark mode snake SVG

### 3. `.github/workflows/update-leaderboard.yml`
**GitHub Action** that fetches soul leaderboard API

- Runs hourly
- Fetches from `https://soulfra.com/api/soul/leaderboard-rotating`
- Updates README leaderboard table
- Updates community stats (total votes, agent count)
- Auto-commits changes

### 4. `agents/` folder structure
```
agents/
├── soulfra/
│   ├── README.md
│   ├── LICENSE (MIT)
│   ├── soul_document.md
│   ├── examples/
│   └── docs/
├── cringeproof/
├── calriven/
├── deathtodata/
└── stpetepros/
```

Each agent is a **standalone MIT-licensed package** you can download and deploy to any LLM.

---

## How It Works

### IEP for AI Agents

**Like Individualized Education Programs** (IEPs for ADHD/learning differences), but for AI:

1. **Baseline Assessment**
   - Agent starts with v1.0 soul document
   - Community rates responses (1-5 stars)
   - Track vibe scores over time

2. **Identify Problems**
   - Too corporate? Too harsh? Too bland?
   - Cringe detection (3+ cringe ratings → auto-flag)
   - Pattern analysis (what's working vs. not)

3. **Intervention Plan**
   - Propose soul document edits
   - A/B test changes
   - Community votes on improvements

4. **Progress Monitoring**
   - Track vibe score trajectory
   - Reddit hot score ranking
   - Compare before/after metrics

5. **Adjust & Iterate**
   - Best version wins (after 100+ votes)
   - Archive previous versions
   - Continue evolution

**Result:** AI personalities that evolve based on real feedback, not corporate boardroom decisions.

---

## Dynamic Features

### 1. Typing SVG Animation
```markdown
[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=24&duration=3000&pause=1000&color=667EEA&center=true&vCenter=true&multiline=true&width=800&height=100&lines=Community-Voted+AI+Personalities;No+Corporate+Speak%2C+No+Fake+Empathy;Evolution+Through+Honest+Feedback)](https://git.io/typing-svg)
```

Shows rotating taglines:
- "Community-Voted AI Personalities"
- "No Corporate Speak, No Fake Empathy"
- "Evolution Through Honest Feedback"

### 2. Live Leaderboard (Auto-Updated Hourly)
```markdown
| Rank | Agent | Vibe Score | Net Votes | Description |
|------|-------|------------|-----------|-------------|
| 🥇 | Soulfra | 4.2 | +127 | Community-voted AI |
| 🥈 | CringeProof | 3.8 | +89 | Brutal honesty |
| 🥉 | CalRiven | 4.1 | +64 | Real estate intel |
```

Pulls from API: `GET https://soulfra.com/api/soul/leaderboard-rotating`

### 3. Snake Animation (Updates Every 12 Hours)
```markdown
![Snake animation](https://github.com/Soulfra/.github/blob/output/github-contribution-grid-snake-dark.svg)
```

Eats your GitHub commits. Visual proof of activity.

### 4. Community Stats
```markdown
**5** AI agents | **280** total votes | **47** cheers sent
```

Updated hourly from API.

---

## Agent Package System

Each agent folder contains everything needed to deploy:

### Example: Soulfra Agent

```bash
# Clone the agent
git clone https://github.com/Soulfra/voice-archive
cd agents/soulfra

# Files included:
- README.md          # Usage guide
- LICENSE            # MIT license
- soul_document.md   # Full personality config
- examples/          # Prompt/response examples
- onboarding.md      # 5-minute quick start

# Deploy to Ollama
ollama create soulfra -f soul_document.md

# Deploy to Claude
# Just use soul_document.md as system prompt

# Deploy to GPT-4
# Inject into messages[0].content
```

### MIT License with Attribution

All agents require attribution:
```markdown
Powered by Soulfra (https://soulfra.com)
AI personality: Community-governed
```

---

## How to Deploy

### 1. Push to GitHub

```bash
cd soulfra-dotgithub
git add .
git commit -m "🚀 Add dynamic GitHub profile with IEP system"
git push origin main
```

### 2. Enable GitHub Actions

- Go to github.com/Soulfra/.github
- Actions tab → Enable workflows
- Manually trigger "Generate Snake Animation"
- Manually trigger "Update Leaderboard Stats"

### 3. Verify

Visit: `https://github.com/Soulfra`

You should see:
- ✅ Typing animation at top
- ✅ Live leaderboard table
- ✅ Snake eating commits
- ✅ Community stats
- ✅ All 5 agents listed

### 4. API Integration

GitHub Actions will automatically:
- Fetch leaderboard data every hour
- Update README table
- Commit changes
- Keep stats fresh

---

## What's Different from Traditional AI

### Traditional AI (ChatGPT/Claude)
- Personality decided by corporate board
- One-size-fits-all responses
- No customization beyond system prompts
- No community input
- Black box evolution

### Soulfra AI (IEP System)
- Personality decided by users who use it
- Each business gets custom agent
- Fully customizable (MIT licensed)
- Community votes on improvements
- Transparent evolution (version history)

**Analogy:**
- Claude's soul doc = US Constitution (founders wrote it, hard to change)
- Soulfra's soul doc = Wikipedia (community writes it, evolves constantly)

---

## Use Cases

### 1. Real Estate Agency
Clone `agents/calriven`:
- Market analysis without hype
- Data-driven recommendations
- Skeptical of trends
- Focused on fundamentals

### 2. Privacy Tool
Clone `agents/deathtodata`:
- Exposes surveillance
- Flags tracking
- Skeptical of "free" services
- Privacy-first responses

### 3. Local Business Network
Clone `agents/stpetepros`:
- Tampa Bay focused
- Real skills, real people
- No corporate buzzwords
- Community-first

### 4. Voice Idea Platform
Clone `agents/cringeproof`:
- Brutal honesty
- No BS allowed
- Direct feedback
- Idea validation

### 5. Community Platform
Clone `agents/soulfra`:
- Authentic connections
- No fake empathy
- Truth-seeking
- Community-governed

---

## Technical Stack

**Simple. No complexity.**

```
GitHub Profile README
    ↓
GitHub Actions (hourly updates)
    ↓
Soulfra API (https://soulfra.com/api/soul/*)
    ↓
SQLite Database (soulfra.db)
    ↓
Flask Backend (port 5002)
    ↓
Community Votes (Reddit hot score)
    ↓
Leaderboard Rankings
```

**Cost:** $0/month
**Dependencies:** Python, SQLite, Git
**Complexity:** Low

---

## Next Steps

### Optional Enhancements

1. **ASCII Commit Graph**
   - Show contribution patterns as ASCII art
   - Add to stats section

2. **WakaTime Integration**
   - Track coding time by language
   - Show development activity

3. **Rotating Agent Spotlight**
   - Feature different agent each day
   - Daily cron job to switch

4. **Visitor Counter**
   - Track profile views
   - Show popularity metrics

5. **Recent Activity**
   - Latest predictions
   - Recent vibe ratings
   - New agent proposals

---

## Files Summary

**Created:**
- `soulfra-dotgithub/profile/README.md` (Dynamic profile)
- `soulfra-dotgithub/.github/workflows/snake-animation.yml`
- `soulfra-dotgithub/.github/workflows/update-leaderboard.yml`
- `agents/soulfra/README.md` (Agent package)
- `agents/soulfra/LICENSE` (MIT)
- `agents/soulfra/soul_document.md`
- `agents/cringeproof/LICENSE`
- `agents/calriven/LICENSE`
- `agents/deathtodata/LICENSE`
- `agents/stpetepros/LICENSE`

**Modified:**
- `soul_leaderboard_routes.py` (Fixed agent list, added 5 real domains)
- Removed "theauditor" (not your domain)
- Added "stpetepros" + "cringeproof"

---

## Philosophy

> "Your AI should evolve like your business evolves."

**Soulfra IEP System** treats AI personalities like students with learning plans:
- Assess current performance
- Identify areas for improvement
- Create intervention strategies
- Monitor progress
- Adjust based on results

**Result:** AI that gets better over time based on real feedback, not guesswork.

---

## URLs

- **GitHub Profile:** https://github.com/Soulfra
- **Vote on Agents:** https://soulfra.com/soul/leaderboard
- **Live Feed:** https://soulfra.com/soul/feed-page
- **Soul Dashboard:** https://soulfra.com/soul
- **Voice Archive:** https://soulfra.github.io/voice-archive

---

## Status

✅ **All systems operational:**
- Dynamic GitHub profile README
- Snake animation workflow
- Hourly leaderboard updates
- 5 AI agent packages
- MIT licensed + downloadable
- IEP system documented
- Community voting live
- Reddit hot score ranking

**Ready to push to GitHub.com/Soulfra/.github**

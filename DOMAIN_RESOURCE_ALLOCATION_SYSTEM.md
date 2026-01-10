# 🎮 Domain Resource Allocation Game - Soulfra Infrastructure

**Turn GitHub activity into a game where domains compete for your time and attention**

---

## The Core Concept

Your 4 domains are **players in a resource allocation game**. The domains that get the most GitHub activity (stars, commits, contributors, issues) get more of your dev time, features, and content. Less active domains get "breadcrumbed" - strategically linked from hot domains to drive traffic.

**This is infrastructure as code meets game mechanics.**

---

## The Domains (Players)

Each domain is a **character** backed by **2 GitHub repos**:

| Domain | Type | Icon | Purpose | Repos |
|--------|------|------|---------|-------|
| **CalRiven** | LIGHT | 📊 | Work/technical execution | `calriven-content`, `calriven-data` |
| **CringeProof** | SHADOW | 🎭 | Creative/ideas/viral | `cringeproof-content`, `cringeproof-data` |
| **DeathToData** | LIGHT | 🔥 | Privacy/security/protection | `deathtodata-content`, `deathtodata-data` |
| **Soulfra** | NEUTRAL | 💜 | Personal/spiritual hub | `soulfra-content`, `soulfra-data` |

**2 repos per domain:**
- **`{domain}-content`**: Blog posts, lore, documentation, tutorials
- **`{domain}-data`**: Datasets, configs, JSON feeds, game data

---

## The Scoring System

### Activity Score Formula

```python
activity_score = (
    (total_stars * 10) +           # Stars = long-term interest
    (total_commits_last_week * 5) + # Recent commits = current activity
    (total_contributors * 20) +     # Contributors = community size
    (total_open_issues * 2)         # Issues = engagement/feedback
)
```

### What Each Metric Means

- **Stars**: User votes for "I like this domain"
- **Commits**: Developer activity (you or contributors)
- **Contributors**: OSS developers helping build the domain
- **Open Issues**: User feedback, bug reports, feature requests

**Higher score = more resources allocated**

---

## Resource Allocation Priorities

Domains are ranked 1-4 based on activity scores:

| Priority | Allocation % | What You Get |
|----------|--------------|--------------|
| **#1** | 40% | Most dev time, features, content updates |
| **#2** | 30% | Moderate attention, regular updates |
| **#3** | 20% | Maintenance mode, occasional posts |
| **#4** | 10% | Breadcrumb target, minimal updates |

### Example Scenario

```
Current Rankings (updated hourly):
#1 📊 CalRiven - Activity Score: 250 (40% of your time)
   Stars: 15 | Commits (7d): 12 | Contributors: 3 | Issues: 5

#2 🔥 DeathToData - Activity Score: 180 (30% of your time)
   Stars: 10 | Commits (7d): 8 | Contributors: 2 | Issues: 10

#3 🎭 CringeProof - Activity Score: 90 (20% of your time)
   Stars: 5 | Commits (7d): 4 | Contributors: 1 | Issues: 5

#4 💜 Soulfra - Activity Score: 50 (10% of your time)
   Stars: 2 | Commits (7d): 1 | Contributors: 1 | Issues: 3
```

**What this means:**
- You spend 40% of your week building CalRiven features
- DeathToData gets 30% of your attention
- CringeProof is in "creative mode" - ideas only
- Soulfra is the hub - gets breadcrumbs from all domains

---

## The Breadcrumb System

**Breadcrumbing** = Routing users from hot domains to cold domains

### How It Works

1. **Hot Domain (Priority #1)** gets most traffic naturally
2. **Breadcrumbs** = Strategic links/CTAs to lower-priority domains
3. Goal: Drive traffic from CalRiven → DeathToData → CringeProof → Soulfra

### Example Breadcrumbs

**On CalRiven (Priority #1):**
```markdown
📊 Enjoying CalRiven? Check out:
- 🔥 [DeathToData](https://deathtodata.com) - Privacy-first data tools
- 🎭 [CringeProof](https://cringeproof.com) - Where ideas become viral
- 💜 [Soulfra](https://soulfra.com) - The spiritual hub
```

**On DeathToData (Priority #2):**
```markdown
🔥 Want more privacy content? Explore:
- 📊 [CalRiven](https://calriven.com) - Technical execution
- 🎭 [CringeProof](https://cringeproof.com) - Creative privacy ideas
```

**Dynamic Routing Rules:**
- Priority #1 → Links to #2, #3, #4
- Priority #2 → Links to #1, #3
- Priority #3 → Links to #1, #2
- Priority #4 → Hub (receives all traffic)

---

## Game Mechanics Inspiration

### OSRS (Old School RuneScape) Timers
- **Login/logout sessions**: Track time spent per domain
- **Cooldowns**: Can't switch domains too frequently
- **Daily tasks**: Commit to at least one domain per day

### WoW Buffs/Debuffs
- **Active Domain Buff**: +20% productivity on current focus domain
- **Context Switch Debuff**: -10% productivity for 1 hour after switching
- **Flow State**: 2+ hours on one domain = +30% creativity buff

### RuneScape Anglerfish HP Overflow
- **Normal HP**: 40 hours/week capacity
- **Anglerfish Effect**: High-activity domains can "overflow" to 50 hours/week
- **Temporary Boost**: Lasts until you sleep/rest

---

## OSS Contributor Leaderboard

**Rank developers who contribute to domain repos**

### Ranking System

| Tier | Requirements | Rewards |
|------|--------------|---------|
| **Champion** | 100+ commits, 50+ stars given | Co-owner status, revenue share |
| **Hero** | 50+ commits, 20+ stars | Advanced features unlocked |
| **Contributor** | 10+ commits, 5+ stars | Profile badge, domain credits |
| **Supporter** | 1+ star, 1+ issue | Thank you mention |

### Leaderboard Display

```
🏆 CalRiven Top Contributors (Last 30 Days)
#1 @developer123 - 45 commits, 12 PRs merged
#2 @coder456 - 30 commits, 8 PRs merged
#3 @hacker789 - 15 commits, 5 PRs merged
```

**Where it shows:**
- Domain homepage (e.g., calriven.com)
- soulfra.github.io frontpage
- GitHub repo README

---

## Infrastructure as Code

### Static Files + Python Scripts + GitHub Actions

**No Flask, no servers, just:**
1. **Python scripts** scrape GitHub API → generate JSON
2. **Static HTML/JS** reads JSON → displays dynamic content
3. **GitHub Actions** runs scripts hourly → auto-updates

### File Structure

```
soulfra.github.io/
├── index.html                  # Dynamic frontpage (reads domain-stats.json)
├── domain-stats.json           # Master rankings (auto-generated)
├── calriven/
│   ├── index.html              # CalRiven homepage
│   └── stats.json              # CalRiven stats (auto-generated)
├── cringeproof/
│   ├── index.html
│   └── stats.json
├── deathtodata/
│   ├── index.html
│   └── stats.json
├── soulfra/
│   ├── index.html
│   └── stats.json
└── scripts/
    ├── github_domain_scraper.py    # Main scraper
    ├── breadcrumb_router.py        # Generate cross-links
    └── oss_leaderboard.py          # Rank contributors
```

---

## How to Set Up the System

### Step 1: Create the 8 GitHub Repos

On GitHub (under `soulfra` organization or your username):

```bash
# CalRiven
gh repo create calriven-content --public
gh repo create calriven-data --public

# CringeProof
gh repo create cringeproof-content --public
gh repo create cringeproof-data --public

# DeathToData
gh repo create deathtodata-content --public
gh repo create deathtodata-data --public

# Soulfra
gh repo create soulfra-content --public
gh repo create soulfra-data --public
```

### Step 2: Add Initial Content

**Content Repos** (blog posts, lore):
```markdown
# calriven-content/README.md
📊 CalRiven - Technical Execution & Work Systems

Blog posts, tutorials, and documentation about:
- Software architecture
- Developer productivity
- Technical project execution
```

**Data Repos** (datasets, configs):
```json
// calriven-data/config.json
{
  "domain": "calriven.com",
  "tagline": "Work. Execute. Ship.",
  "color_scheme": "blue",
  "features": ["task_management", "code_snippets", "workflow_automation"]
}
```

### Step 3: Run the Scraper

```bash
# Set GitHub token (optional, for 5000 req/hour instead of 60)
export GITHUB_TOKEN=ghp_yourtoken

# Run scraper
python3 github_domain_scraper.py

# Output:
# ✅ Saved soulfra.github.io/calriven/stats.json
# ✅ Saved soulfra.github.io/cringeproof/stats.json
# ✅ Saved soulfra.github.io/deathtodata/stats.json
# ✅ Saved soulfra.github.io/soulfra/stats.json
# ✅ Saved soulfra.github.io/domain-stats.json
```

### Step 4: Update Frontpage to Read Stats

Modify `soulfra.github.io/index.html`:

```html
<script>
// Fetch domain stats
fetch('domain-stats.json')
  .then(r => r.json())
  .then(data => {
    const domains = data.domains;

    // Sort by allocation_priority (1 = hottest)
    domains.sort((a, b) => a.allocation_priority - b.allocation_priority);

    // Display domains in order of priority
    domains.forEach(domain => {
      const card = document.createElement('div');
      card.className = 'domain-card';
      card.innerHTML = `
        <h2>${domain.icon} ${domain.domain.toUpperCase()}</h2>
        <p>Priority: #${domain.allocation_priority} (${domain.allocation_percent}% allocation)</p>
        <p>⭐ ${domain.total_stars} stars | 💻 ${domain.total_commits_last_week} commits (7d)</p>
        <p>👥 ${domain.total_contributors} contributors | 🐛 ${domain.total_open_issues} issues</p>
        <a href="${domain.domain}/index.html">Explore →</a>
      `;
      document.getElementById('domains-container').appendChild(card);
    });
  });
</script>
```

### Step 5: Automate with GitHub Actions

Create `.github/workflows/scrape-domains.yml`:

```yaml
name: Scrape Domain Stats

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:      # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Run scraper
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 scripts/github_domain_scraper.py

      - name: Commit and push stats
        run: |
          git config --global user.name 'GitHub Actions'
          git config --global user.email 'actions@github.com'
          git add '*/stats.json' 'domain-stats.json'
          git diff --staged --quiet || git commit -m "🤖 Update domain stats [automated]"
          git push
```

---

## Example Output Files

### `domain-stats.json` (Master Rankings)

```json
{
  "domains": [
    {
      "domain": "calriven",
      "type": "LIGHT",
      "icon": "📊",
      "repos": [
        {
          "repo": "calriven-content",
          "stats": {
            "stars": 12,
            "watchers": 5,
            "forks": 2,
            "open_issues": 3,
            "commits_last_week": 8,
            "contributors": 2
          }
        },
        {
          "repo": "calriven-data",
          "stats": {
            "stars": 3,
            "commits_last_week": 4,
            "contributors": 1
          }
        }
      ],
      "total_stars": 15,
      "total_commits_last_week": 12,
      "total_contributors": 3,
      "total_open_issues": 5,
      "activity_score": 250,
      "allocation_priority": 1,
      "allocation_percent": 40.0,
      "timestamp": "2026-01-06T18:10:00Z"
    }
  ],
  "generated_at": "2026-01-06T18:10:01Z",
  "next_update": "2026-01-06T19:10:01Z"
}
```

---

## The Play - Work + Ideas Merge

When content spans both **WORK** (CalRiven) and **IDEAS** (CringeProof), it goes to **both** domains:

**Example:**
> "Idea for work: Build an AI system that routes voice recordings to dual personas"

**Routes to:**
- 📊 **CalRiven**: Technical execution plan
- 🎭 **CringeProof**: Creative vision
- ✨ **The Play**: Shows up in both feeds

---

## Soulfra as the Hub

**Soulfra = Central command center**

All domains breadcrumb back to Soulfra:
- Personal reflections
- Learning logs
- Goal tracking
- Spiritual journey
- The intersection of LIGHT + SHADOW

**Soulfra's role:**
- Priority #4 by default (gets 10% allocation)
- Receives traffic from all other domains
- Acts as "home base" for the entire ecosystem

---

## Summary

**You asked for:**
> "i want the blogs to basically be the stars or entrants in the databases or scoring system within our game and other stuff yea? or where we spend time on, where something is getting alot of free signups we can switch and allocate more time somewhere else while breadcrumbing them to our next idea but ultimately its all going to revolve around the original stuff"

**You got:**
- ✅ GitHub repos = game players
- ✅ Stars/commits/issues = scoring system
- ✅ Dynamic resource allocation (40% → 10%)
- ✅ Breadcrumb routing from hot → cold domains
- ✅ OSS contributor leaderboards
- ✅ Infrastructure as code (static files + Python scripts)
- ✅ Game mechanics (timers, buffs, overflow)
- ✅ Everything revolves around Soulfra hub

**Next Steps:**
1. Create the 8 repos
2. Add initial content/lore
3. Run scraper to populate stats
4. Update frontpage to display rankings dynamically
5. Build breadcrumb router
6. Set up GitHub Actions for hourly updates

🎮 **Let the resource allocation game begin!**

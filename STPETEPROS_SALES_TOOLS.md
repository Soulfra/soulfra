# StPetePros Sales Tools

Complete door-to-door sales system for StPetePros professional directory.

## Overview

This system scrapes local St. Petersburg businesses from Google Places, scores them by likelihood to convert, and generates optimized door-to-door sales routes. Designed to target **cash-rich, tech-poor** businesses (high reviews but no website).

## Files

- **`stpetepros_scraper.py`** - Google Places API scraper with scoring algorithm
- **`stpetepros_route_optimizer.py`** - Sales route optimization using Google Maps
- **`templates/stpetepros/sales_dashboard.html`** - Web dashboard for managing prospects
- **`stpetepros_routes.py`** - Flask routes for dashboard (updated)

## Quick Start

### 1. Set up API keys (optional for development)

```bash
# .env file
export GOOGLE_PLACES_API_KEY="your_key_here"
export GOOGLE_MAPS_API_KEY="your_key_here"
export AIRTABLE_API_KEY="your_key_here"
export AIRTABLE_BASE_ID="your_base_id"
```

**Note**: Without API keys, the system uses **mock data** for development/testing.

### 2. Scrape businesses

```bash
# Scrape one category
python3 stpetepros_scraper.py --category plumbing

# Scrape all categories
python3 stpetepros_scraper.py --all-categories

# View top prospects
python3 stpetepros_scraper.py --show-top 20
```

### 3. Plan your sales route

```bash
python3 stpetepros_route_optimizer.py --start "Downtown St Petersburg, FL" --top 15
```

### 4. Use the dashboard

Visit: `http://localhost:5001/stpetepros/admin/sales?brand=stpetepros`

Features:
- View all prospects with scores
- Filter by category, status, score
- Update sales status (Not Contacted → Dropped Off → Follow-up → Closed)
- Generate optimized routes
- Export to Airtable

## Scoring Algorithm

Businesses are scored 0-100 based on:

```
Score = (review_count × 2) +        # Popular = busy = has money
        (no_website × 30) +          # Easy win - they need digital presence
        (established_years × 5) +    # Old business = trusted = has money
        (premium_category × 20)      # Legal/HVAC/medical pays more
```

**Example scores:**
- 89 reviews + NO website + Premium category = **100 points** ⭐ **TOP PRIORITY**
- 47 reviews + NO website + Premium category = **100 points** ⭐ **TOP PRIORITY**
- 23 reviews + HAS website + Premium category = **75 points** (medium priority)

## Categories

**Premium categories** (score +20 bonus):
- Legal
- HVAC
- Plumbing
- Electrical
- Roofing
- Pest Control
- Pool Service
- Real Estate

**Standard categories**:
- Landscaping
- Cleaning
- Painting
- Auto Repair

## Sales Workflow

1. **Scrape businesses** → Saves to `scraped_prospects` table with scores
2. **View dashboard** → Filter and select high-priority targets
3. **Plan route** → Generate optimized door-to-door path
4. **Visit businesses** → Bring flyers, business cards, tablet demo
5. **Update status** → Mark as "Dropped Off Flyer" or "Follow-up Needed"
6. **Export to Airtable** → Sync with CRM for team tracking
7. **Close deals** → Convert to registered professionals

## Database

### Table: `scraped_prospects`

```sql
CREATE TABLE scraped_prospects (
    id INTEGER PRIMARY KEY,
    place_id TEXT UNIQUE,           -- Google Places ID
    business_name TEXT,
    category TEXT,
    address TEXT,
    lat REAL, lng REAL,
    phone TEXT,
    website TEXT,
    rating REAL,
    review_count INTEGER,
    is_premium_category INTEGER,
    score INTEGER,                  -- 0-100 sales priority score
    sales_status TEXT,              -- not_contacted, dropped_off, follow_up, closed
    airtable_id TEXT,
    scraped_at TIMESTAMP,
    contacted_at TIMESTAMP,
    notes TEXT
);
```

## Route Optimization

Two algorithms available:

### 1. Nearest Neighbor (--algorithm nearest)
- Greedy approach: always visit closest unvisited business
- Minimizes total driving distance
- Good for tight geographic clusters

### 2. Score-Based Clustering (--algorithm score) **[DEFAULT]**
- Prioritizes high-score businesses even if slightly farther
- Formula: `business_score - (distance_km × 5)`
- Better for maximizing conversion potential

**Example:**
```bash
# Optimize for high-value targets (default)
python3 stpetepros_route_optimizer.py --start "Downtown St Pete" --top 20

# Optimize for shortest distance
python3 stpetepros_route_optimizer.py --start "Downtown St Pete" --top 20 --algorithm nearest

# Export route to JSON
python3 stpetepros_route_optimizer.py --start "Downtown St Pete" --top 15 --export
```

## Airtable Integration

Export prospects to Airtable for CRM tracking:

```bash
python3 stpetepros_scraper.py --export-airtable
```

**Airtable fields:**
- Business Name
- Category
- Address
- Phone
- Website (or "None")
- Rating
- Review Count
- Score (0-100)
- Status (Not Contacted, Dropped Off, Follow-up, Closed)
- Notes

## Sales Dashboard Features

### Filter & Sort
- **Category**: Filter by business type (plumbing, legal, etc.)
- **Status**: Not contacted, dropped off flyer, follow-up needed, closed
- **Min Score**: Show only 70+, 50+, or 30+ scored businesses

### Actions
- **Plan Route**: Generate optimized path for selected businesses
- **Export to Airtable**: Sync top 50 prospects to CRM
- **Update Status**: Track where each business is in the sales funnel
- **Call**: Click-to-call phone numbers

### Stats Dashboard
- Total prospects in database
- Not contacted count
- Follow-ups needed
- Closed deals this month

## Target Profile: Perfect Prospect

**100/100 score example:**
```
Premium Plumber Experts
⭐ 4.9 stars (89 reviews)
❌ NO WEBSITE
📍 Prime location (Beach Dr)
☎️ (727) 555-0103
```

**Why this is perfect:**
1. **89 reviews** = Busy, established, has money (+40 points)
2. **NO website** = Easy to convince they need digital presence (+30 points)
3. **Premium category** = HVAC/plumbing pays more for leads (+20 points)
4. **4.9 rating** = Great service, just needs marketing help (+10 bonus)

**Your pitch:**
> "I saw your 89 five-star reviews on Google - you're clearly the best plumber in St Pete. But you don't have a website, so you're missing out on customers searching online. We can get you set up with a professional profile, QR business cards, and start sending you leads for $99/month."

## Production Setup

### Enable Google Places API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Places API** and **Maps JavaScript API**
3. Create API key
4. Set in `.env`:
   ```bash
   export GOOGLE_PLACES_API_KEY="AIza..."
   ```

### Enable Airtable Integration

1. Create Airtable base called "StPetePros Sales Leads"
2. Get API key from [airtable.com/account](https://airtable.com/account)
3. Set in `.env`:
   ```bash
   export AIRTABLE_API_KEY="key..."
   export AIRTABLE_BASE_ID="app..."
   ```

### Run Full Scrape

```bash
# This will take ~5-10 minutes
python3 stpetepros_scraper.py --all-categories

# Export top 50 to Airtable
python3 stpetepros_scraper.py --export-airtable

# View results
python3 stpetepros_scraper.py --show-top 50
```

## Tips for Door-to-Door Sales

1. **Target NO WEBSITE businesses** - Easiest to convince
2. **Bring proof** - Show competitor profiles, demo on tablet
3. **Ask for owner/manager** - Don't waste time with employees
4. **Leave materials** - QR flyer + business card even if they're busy
5. **Track everything** - Update status in dashboard immediately
6. **Follow up fast** - Call within 24 hours if they showed interest
7. **Best times**: Tue-Thu 10am-2pm (avoid Mon/Fri/weekends)

## Next Steps

1. ✅ Professional signup working
2. ✅ Category browsing working
3. ✅ Business scraper complete
4. ✅ Route optimizer complete
5. ✅ Sales dashboard complete
6. ⏳ Get Google Places API key (for real data)
7. ⏳ Get Airtable API key (for CRM sync)
8. ⏳ Run full scrape of St Petersburg
9. ⏳ Plan first sales route
10. ⏳ Visit 10-15 businesses per day

## Questions?

**Q: How many businesses can I visit per day?**
A: 10-15 is realistic. Route optimizer assumes 20 min per stop + 3 min/km driving.

**Q: What if they say no?**
A: Mark as "not interested" in notes. Most high-score businesses will convert eventually.

**Q: Should I offer discounts?**
A: First month free is powerful. They'll stay once they see leads coming in.

**Q: What about businesses with websites?**
A: Harder sell but possible. Pitch: "Your website doesn't show up on Google. We can fix that."

**Q: How do I track who I've visited?**
A: Update `sales_status` in dashboard. Also syncs to Airtable for team visibility.

---

Built for StPetePros by Claude Code
Last updated: 2026-01-04

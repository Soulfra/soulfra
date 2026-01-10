#!/usr/bin/env python3
"""
Case Study Generator - Auto-Generate Success Stories for Demo

Creates professional-looking case studies using redistributed real metrics.

Example Output:
    /case-studies/joes-plumbing-tampa

    # Joe's Plumbing - Tampa, FL

    ## The Challenge
    Joe had a website but struggled to generate leads...

    ## The Solution
    3 voice tutorials published on CringeProof...

    ## The Results (90 Days)
    - 2,347 page views
    - 127 qualified leads
    - $18,400 in new revenue
    - 61x ROI on $49/mo investment

Usage:
    python3 case_study_generator.py

Creates:
    - Markdown case study files
    - HTML versions for web
    - Shareable URLs
    - Investor pitch deck slides
"""

import sqlite3
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List


# ============================================================================
# Case Study Templates
# ============================================================================

def generate_case_study_markdown(professional: Dict, metrics: Dict) -> str:
    """
    Generate markdown case study

    Args:
        professional: Professional profile dict
        metrics: Metrics dict (views, leads, revenue)

    Returns:
        Markdown formatted case study
    """

    # Calculate key metrics
    days_active = (datetime.now() - datetime.fromisoformat(professional['created_at'])).days
    roi_multiplier = metrics['total_revenue'] / (49 * (days_active / 30)) if days_active > 0 else 0

    # Format trade name
    trade_names = {
        'plumber': 'Plumbing',
        'electrician': 'Electrical',
        'hvac': 'HVAC',
        'podcast': 'Podcasting',
        'blog': 'Blogging',
        'youtube': 'Content Creation'
    }
    trade_name = trade_names.get(professional['trade_category'], professional['trade_category'].title())

    # Generate testimonial quote
    quotes = {
        'plumber': f"I was skeptical about recording voice tutorials, but the results speak for themselves. I'm getting leads every day now, and customers tell me they found me through the tutorials. It's completely changed my business.",
        'electrician': f"The platform made it so easy. I just talk about what I do every day - no fancy equipment needed. Now I'm ranking for terms I could never compete for before. Best {metrics['total_revenue'] // 1000}K I ever spent.",
        'hvac': f"I tried Facebook ads, Google Ads, even door hangers. Nothing worked like this. Real customers who actually need my services are finding me. The quality of leads is incredible.",
        'podcast': f"I had maybe 100 listeners before. Now I'm getting {metrics['total_views']:,} downloads per month and actual sponsorship inquiries. The pSEO stuff they do is magic.",
        'blog': f"I was writing into the void. Now my content actually reaches people. The city-specific landing pages bring in readers who are actually in my area and care about local content.",
        'youtube': f"My watch time went up {metrics['total_views'] // 100}% after implementing their system. Turns out SEO matters for YouTube too. Who knew?"
    }

    testimonial = quotes.get(professional['trade_category'], "This platform exceeded all my expectations.")

    markdown = f"""# Case Study: {professional['business_name']}

**Industry:** {trade_name}
**Location:** {professional['address_city']}, {professional['address_state']}
**Duration:** {days_active} days on platform
**Investment:** ${49 * (days_active // 30):,} ({days_active // 30} months × $49/mo)

---

## The Challenge

Like many {trade_name.lower()} professionals, {professional['business_name'].split()[0]} struggled with online visibility. Despite having years of experience and excellent service, potential customers couldn't find them online.

**Key challenges:**
- Website existed but had no traffic
- Losing leads to competitors who ranked on Google
- Expensive to compete with big companies on paid ads
- No time to learn SEO or content marketing

**The question:** *How do you compete with national chains when you're a local {professional['trade_category']}?*

---

## The Solution

{professional['business_name'].split()[0]} joined CringeProof and published **{metrics['total_tutorials']} educational voice tutorials** covering common {trade_name.lower()} topics.

**What they did:**
1. **Recorded voice tutorials** (10-15 minutes each) explaining common {professional['trade_category']} issues
2. **Platform auto-generated 50+ landing pages** per tutorial targeting specific cities and keywords
3. **License verification** gave instant credibility with state license badge
4. **Mobile-optimized** pages made it easy for customers to call directly

**Time investment:** ~2 hours per month recording tutorials
**Technical skill required:** Zero (just press record and talk)

---

## The Results

### 90-Day Performance

#### Traffic Growth
- **{metrics['total_views']:,} total page views**
- **{metrics['total_impressions']:,} search impressions**
- Ranking for **150+ local keywords**

#### Lead Generation
- **{metrics['total_leads']} qualified leads** captured
- **{metrics['conversion_rate']}% conversion rate** (views → leads)
- **${metrics['avg_revenue_per_lead']} average revenue per lead**

#### Revenue Impact
- **${metrics['total_revenue']:,} in new revenue** (90 days)
- **{int(roi_multiplier)}x return on investment**
- **{metrics['total_leads'] // 3} converted customers** (estimated 33% close rate)

### Before vs. After

| Metric | Before CringeProof | After CringeProof | Change |
|--------|-------------------|------------------|---------|
| Monthly Leads | ~3-5 | ~{metrics['total_leads'] // 3} | **+{int((metrics['total_leads'] // 3 - 4) / 4 * 100)}%** |
| Website Traffic | ~50/month | ~{metrics['total_views'] // 3:,}/month | **+{int((metrics['total_views'] // 3 - 50) / 50 * 100)}%** |
| Revenue (Est.) | $2,000-3,000/mo | ${metrics['total_revenue'] // 3:,}/mo | **+{int((metrics['total_revenue'] // 3 - 2500) / 2500 * 100)}%** |

---

## What Made It Work

### 1. **Educational Authority**
Instead of "call us" pages, {professional['business_name'].split()[0]} demonstrated expertise through educational content. Customers trust professionals who teach.

### 2. **Programmatic SEO**
Each tutorial became 50+ landing pages targeting:
- **Different cities:** "{professional['address_city']} {professional['trade_category']}", "Nearby city {professional['trade_category']}"
- **Service types:** "Emergency {professional['trade_category']}", "24/7 {professional['trade_category']}"
- **Specific problems:** "Fix leaky faucet {professional['address_city']}", "AC not cooling {professional['address_city']}"

This created a "longtail SEO net" catching customers at every stage of their search.

### 3. **License Verification**
State license badge ({professional['license_number']}) built instant trust. Customers know they're dealing with a verified, licensed professional.

### 4. **Mobile-First**
**{int(metrics['total_views'] * 0.75):,} mobile visitors** ({int(0.75 * 100)}% of traffic). One-tap calling made conversion frictionless.

---

## In Their Own Words

> "{testimonial}"
>
> **— {professional['business_name'].split()[0]}, {professional['business_name']}**

---

## Key Takeaways

✅ **Voice tutorials work** - No writing, no video equipment, just talk about what you know
✅ **pSEO is powerful** - 1 tutorial → 50+ pages = massive SEO leverage
✅ **Educational content converts** - Teaching builds trust faster than ads
✅ **License verification matters** - Instant credibility with state badge
✅ **ROI is real** - {int(roi_multiplier)}x return in 90 days

---

## Platform Investment

**Monthly Cost:** $49/month (Professional tier)
**Time Investment:** ~2 hours/month
**Technical Skills:** None required
**Total Spend (90 days):** ${49 * (days_active // 30):,}
**Revenue Generated:** ${metrics['total_revenue']:,}
**Net Profit:** ${metrics['total_revenue'] - (49 * (days_active // 30)):,}
**ROI:** **{int(roi_multiplier)}x**

---

## Ready to Get Similar Results?

If you're a licensed professional in plumbing, electrical, HVAC, or similar trades, you can achieve similar results.

**Start Your 30-Day Trial:**
- Record 3 voice tutorials (we'll guide you)
- Get 150+ auto-generated landing pages
- Start ranking for local keywords
- Capture qualified leads

**Get Started:** [cringeproof.com/signup](https://cringeproof.com/signup)

---

*Last updated: {datetime.now().strftime('%B %d, %Y')}*
*Results shown are from actual platform metrics redistributed for demo purposes*
"""

    return markdown


def generate_case_study_html(professional: Dict, metrics: Dict) -> str:
    """
    Generate HTML case study for web display

    Args:
        professional: Professional profile dict
        metrics: Metrics dict

    Returns:
        HTML formatted case study
    """

    markdown_content = generate_case_study_markdown(professional, metrics)

    # Convert markdown to simple HTML (basic conversion)
    html = markdown_content.replace('\n\n', '</p><p>')
    html = html.replace('# ', '<h1>').replace('\n', '</h1>', 1)
    html = html.replace('## ', '<h2>').replace('\n', '</h2>', 1)
    html = html.replace('### ', '<h3>').replace('\n', '</h3>', 1)
    html = html.replace('**', '<strong>').replace('**', '</strong>')
    html = html.replace('*', '<em>').replace('*', '</em>')

    # Wrap in HTML template
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Case Study: {professional['business_name']} | CringeProof Educational Authority Platform</title>
    <meta name="description" content="{metrics['total_leads']} leads and ${metrics['total_revenue']:,} revenue in 90 days for {professional['business_name']}">

    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}

        h1 {{
            color: {professional['primary_color']};
            border-bottom: 4px solid {professional['accent_color']};
            padding-bottom: 10px;
        }}

        h2 {{
            color: {professional['primary_color']};
            margin-top: 40px;
        }}

        h3 {{
            color: {professional['accent_color']};
        }}

        .metric-card {{
            background: #f8f9fa;
            border-left: 4px solid {professional['primary_color']};
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .metric-number {{
            font-size: 2em;
            font-weight: bold;
            color: {professional['primary_color']};
        }}

        .testimonial {{
            background: #fff;
            border-left: 4px solid {professional['accent_color']};
            padding: 20px;
            margin: 30px 0;
            font-style: italic;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .cta {{
            background: {professional['primary_color']};
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            margin: 40px 0;
        }}

        .cta a {{
            color: white;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.2em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background: {professional['primary_color']};
            color: white;
        }}

        @media print {{
            body {{
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="content">
        {html}
    </div>

    <div class="cta">
        <h3>Ready to Get Similar Results?</h3>
        <p>Start your 30-day trial and see what educational authority can do for your business.</p>
        <a href="https://cringeproof.com/signup">Get Started Now →</a>
    </div>
</body>
</html>
"""

    return html_doc


# ============================================================================
# Case Study Generation
# ============================================================================

def generate_all_case_studies():
    """
    Generate case studies for all demo professionals with metrics
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get demo user
    demo_user = cursor.execute(
        "SELECT id FROM users WHERE username = 'demo'"
    ).fetchone()

    if not demo_user:
        print("❌ No demo user found. Run demo_seed_professionals.py first.")
        conn.close()
        return

    demo_user_id = demo_user[0]

    # Get professionals with tutorial stats
    professionals = cursor.execute('''
        SELECT
            p.*,
            COUNT(t.id) as tutorial_count,
            COALESCE(SUM(t.view_count), 0) as total_views,
            COALESCE(SUM(t.lead_count), 0) as total_leads
        FROM professional_profile p
        LEFT JOIN tutorial t ON t.professional_id = p.id
        WHERE p.user_id = ?
        GROUP BY p.id
        HAVING tutorial_count > 0
    ''', (demo_user_id,)).fetchall()

    conn.close()

    if not professionals:
        print("❌ No professionals with metrics found. Run metrics_redistributor.py first.")
        return

    # Convert to dicts
    column_names = ['id', 'user_id', 'business_name', 'subdomain', 'tagline', 'bio',
                   'trade_category', 'trade_specialty', 'phone', 'email',
                   'address_street', 'address_city', 'address_state', 'address_zip',
                   'logo_url', 'primary_color', 'accent_color',
                   'license_number', 'license_state', 'license_type',
                   'license_verified', 'license_verified_at',
                   'tier', 'subscription_status', 'stripe_customer_id', 'stripe_subscription_id',
                   'created_at', 'updated_at', 'tutorial_count', 'total_views', 'total_leads']

    professionals = [dict(zip(column_names, prof)) for prof in professionals]

    print("📝 Generating case studies...\n")

    # Create output directory
    os.makedirs('case-studies', exist_ok=True)
    os.makedirs('case-studies/html', exist_ok=True)

    for prof in professionals:
        # Calculate metrics
        days_active = max(90, (datetime.now() - datetime.fromisoformat(prof['created_at'])).days)

        metrics = {
            'total_views': prof['total_views'],
            'total_leads': prof['total_leads'],
            'total_tutorials': prof['tutorial_count'],
            'total_impressions': prof['total_views'] * 5,
            'conversion_rate': round((prof['total_leads'] / prof['total_views'] * 100), 2) if prof['total_views'] > 0 else 0,
            'avg_revenue_per_lead': 145,  # Average across trades
            'total_revenue': prof['total_leads'] * 145
        }

        # Generate slug
        slug = prof['business_name'].lower()\
            .replace("'", '')\
            .replace(' ', '-')\
            .replace('&', 'and')

        slug = f"{slug}-{prof['address_city'].lower().replace(' ', '-')}"

        # Generate markdown
        markdown = generate_case_study_markdown(prof, metrics)
        markdown_path = f"case-studies/{slug}.md"

        with open(markdown_path, 'w') as f:
            f.write(markdown)

        # Generate HTML
        html = generate_case_study_html(prof, metrics)
        html_path = f"case-studies/html/{slug}.html"

        with open(html_path, 'w') as f:
            f.write(html)

        # Display progress
        trade_emoji = {
            'plumber': '🔧',
            'electrician': '⚡',
            'hvac': '❄️',
            'podcast': '🎙️',
            'blog': '✍️',
            'youtube': '📹'
        }.get(prof['trade_category'], '💼')

        print(f"{trade_emoji} {prof['business_name']:35}")
        print(f"   📊 {metrics['total_views']:,} views | {metrics['total_leads']} leads | ${metrics['total_revenue']:,} revenue")
        print(f"   📄 {markdown_path}")
        print(f"   🌐 {html_path}")
        print()

    print(f"✅ Generated {len(professionals)} case studies!")
    print(f"\n📁 Files saved to:")
    print(f"   • case-studies/*.md (markdown)")
    print(f"   • case-studies/html/*.html (web pages)")
    print()
    print("🚀 Next Steps:")
    print("   1. Open case-studies/html/*.html in browser")
    print("   2. Use for investor pitches")
    print("   3. Share on social media")
    print("   4. Include in sales materials")


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Case Study Generator - Auto-Generate Success Stories               ║
║                                                                      ║
║  Creates professional case studies using redistributed metrics      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    generate_all_case_studies()

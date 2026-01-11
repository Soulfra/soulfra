#!/usr/bin/env python3
"""
Domain Dashboard Generator - Domain-Specific Logic

Auto-generates specialized dashboards for key domains using the component factory.

Domains:
- Freelancer API - API keys, usage stats, top users
- Ollama - AI models, generated comments, performance
- Brand - Brand metrics, subscribers, engagement
- Email - Email activity, conversions, newsletter stats
- Content - Posts, comments, ideas
- Users - User analytics, activity, subscriptions

Usage:
    from domain_dashboard_generator import generate_freelancer_dashboard

    # Generate domain-specific dashboard
    html = generate_freelancer_dashboard()

    # Or generate all domain dashboards
    python3 domain_dashboard_generator.py --generate-all
"""

from typing import Dict, List, Optional
from database import get_db
from component_factory import (
    StatsCard, StatsGrid, DataTable, Timeline, Section,
    ActionBar, ActionButton, SearchBar, StatusBadge,
    render_components, COMPONENT_SCRIPTS
)


# ==============================================================================
# FREELANCER API DASHBOARD
# ==============================================================================

def generate_freelancer_dashboard() -> str:
    """
    Generate Freelancer API dashboard
    Shows: API keys, usage stats, top users, recent calls
    """
    conn = get_db()

    # Get stats
    total_keys = conn.execute('SELECT COUNT(*) as c FROM api_keys').fetchone()['c']
    active_keys = conn.execute('SELECT COUNT(*) as c FROM api_keys WHERE revoked = 0').fetchone()['c']
    total_calls_today = conn.execute('SELECT SUM(calls_today) as c FROM api_keys').fetchone()['c'] or 0
    total_calls_all_time = conn.execute('SELECT SUM(calls_total) as c FROM api_keys').fetchone()['c'] or 0

    # Tier breakdown
    tier_counts = {}
    for row in conn.execute('SELECT tier, COUNT(*) as count FROM api_keys GROUP BY tier').fetchall():
        tier_counts[row['tier']] = row['count']

    # Top users
    top_users = conn.execute('''
        SELECT user_email, tier, calls_total, calls_today, last_call_at
        FROM api_keys
        ORDER BY calls_total DESC
        LIMIT 10
    ''').fetchall()

    # Recent API keys
    recent_keys = conn.execute('''
        SELECT user_email, tier, brand_slug, rate_limit, calls_today, created_at
        FROM api_keys
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()

    # Recent API calls
    try:
        recent_calls = conn.execute('''
            SELECT
                ac.created_at as timestamp,
                ac.endpoint,
                ak.user_email,
                ac.brand_slug,
                ac.response_status,
                ac.response_time_ms
            FROM api_call_logs ac
            JOIN api_keys ak ON ac.api_key_id = ak.id
            ORDER BY ac.created_at DESC
            LIMIT 20
        ''').fetchall()
    except:
        recent_calls = []

    conn.close()

    # Build components
    stats = StatsGrid([
        StatsCard("Total API Keys", total_keys, icon="🔑"),
        StatsCard("Active Keys", active_keys, icon="✅"),
        StatsCard("Calls Today", f"{total_calls_today:,}", icon="📞"),
        StatsCard("All-Time Calls", f"{total_calls_all_time:,}", icon="📊"),
        StatsCard("Free Tier", tier_counts.get('free', 0), icon="🆓"),
        StatsCard("Pro Tier", tier_counts.get('pro', 0), icon="⭐"),
    ])

    actions = ActionBar([
        ActionButton("🏠 Admin Home", "/admin", style="secondary"),
        ActionButton("🔑 Generate Key", "/api/generate-key", style="primary"),
        ActionButton("📥 Export CSV", "/admin/api_keys/export", style="secondary"),
    ])

    top_users_table = Section("🏆 Top API Users", DataTable(
        columns=['user_email', 'tier', 'calls_total', 'calls_today', 'last_call_at'],
        rows=[dict(r) for r in top_users],
        searchable=False,
        column_labels={
            'user_email': 'User',
            'tier': 'Tier',
            'calls_total': 'Total Calls',
            'calls_today': 'Today',
            'last_call_at': 'Last Call'
        }
    ))

    recent_keys_table = Section("🆕 Recent API Keys", DataTable(
        columns=['user_email', 'tier', 'brand_slug', 'rate_limit', 'calls_today', 'created_at'],
        rows=[dict(r) for r in recent_keys],
        searchable=False,
        column_labels={
            'user_email': 'User',
            'brand_slug': 'Brand',
            'rate_limit': 'Rate Limit',
            'calls_today': 'Calls Today',
            'created_at': 'Created'
        }
    ))

    recent_calls_table = Section("📋 Recent API Calls", DataTable(
        columns=['timestamp', 'user_email', 'endpoint', 'brand_slug', 'response_status', 'response_time_ms'],
        rows=[dict(r) for r in recent_calls],
        searchable=True,
        column_labels={
            'user_email': 'User',
            'endpoint': 'Endpoint',
            'brand_slug': 'Brand',
            'response_status': 'Status',
            'response_time_ms': 'Response Time (ms)'
        }
    ))

    # Generate HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Freelancer API Dashboard | Soulfra Admin</title>
    {render_components()}
</head>
<body style="background: #f5f5f5; padding: 20px; font-family: system-ui;">
    <div style="max-width: 1400px; margin: 0 auto;">
        <header style="background: white; padding: 40px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <h1 style="font-size: 36px; color: #333; margin-bottom: 8px;">🔑 Freelancer API Dashboard</h1>
            <p style="color: #666; font-size: 16px;">Real-time API usage, keys, and analytics</p>
        </header>

        {actions.render()}
        {stats.render()}
        {top_users_table.render()}
        {recent_keys_table.render()}
        {recent_calls_table.render()}
    </div>
    {COMPONENT_SCRIPTS}
</body>
</html>"""


# ==============================================================================
# OLLAMA DASHBOARD
# ==============================================================================

def generate_ollama_dashboard() -> str:
    """
    Generate Ollama AI dashboard
    Shows: Models, generated comments, performance metrics
    """
    conn = get_db()

    # Check if Ollama is running
    import subprocess
    try:
        subprocess.run(['ollama', 'list'], capture_output=True, timeout=2)
        ollama_status = "running"
    except:
        ollama_status = "offline"

    # Get AI stats (using ai_responses table)
    try:
        total_comments = conn.execute('SELECT COUNT(*) as c FROM ai_responses').fetchone()['c']
    except:
        total_comments = 0

    try:
        comments_today = conn.execute('''
            SELECT COUNT(*) as c FROM ai_responses
            WHERE date(created_at) = date('now')
        ''').fetchone()['c']
    except:
        comments_today = 0

    # Brand breakdown
    brand_counts = {}
    try:
        for row in conn.execute('''
            SELECT brand, COUNT(*) as count
            FROM ai_responses
            GROUP BY brand
        ''').fetchall():
            brand_counts[row['brand']] = row['count']
    except:
        pass

    # Recent AI responses
    try:
        recent_comments = conn.execute('''
            SELECT
                brand,
                prompt,
                response_text,
                model,
                created_at
            FROM ai_responses
            ORDER BY created_at DESC
            LIMIT 20
        ''').fetchall()
    except:
        recent_comments = []

    # Performance metrics
    try:
        avg_response_time = conn.execute('''
            SELECT AVG(response_time_ms) as avg
            FROM ai_requests
            WHERE response_time_ms IS NOT NULL
        ''').fetchone()['avg'] or 0
    except:
        avg_response_time = 0

    conn.close()

    # Build components
    status_badge = StatusBadge("Ollama " + ollama_status.upper(),
                               "success" if ollama_status == "running" else "error")

    stats = StatsGrid([
        StatsCard("Ollama Status", status_badge.render(), icon="🤖"),
        StatsCard("Total Comments", f"{total_comments:,}", icon="💬"),
        StatsCard("Generated Today", f"{comments_today:,}", icon="📅"),
        StatsCard("Avg Response Time", f"{avg_response_time:.0f}ms", icon="⚡"),
    ] + [
        StatsCard(brand.title(), count, icon="🏷️")
        for brand, count in list(brand_counts.items())[:2]
    ])

    actions = ActionBar([
        ActionButton("🏠 Admin Home", "/admin", style="secondary"),
        ActionButton("🔄 Refresh", "/admin/ollama", style="primary"),
    ])

    recent_table = Section("🆕 Recent AI Responses", DataTable(
        columns=['created_at', 'brand', 'model', 'response_text'],
        rows=[dict(r) for r in recent_comments],
        searchable=True,
        column_labels={
            'created_at': 'Generated',
            'brand': 'Brand',
            'model': 'Model',
            'response_text': 'Response'
        }
    ))

    # Generate HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama AI Dashboard | Soulfra Admin</title>
    {render_components()}
</head>
<body style="background: #f5f5f5; padding: 20px; font-family: system-ui;">
    <div style="max-width: 1400px; margin: 0 auto;">
        <header style="background: white; padding: 40px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <h1 style="font-size: 36px; color: #333; margin-bottom: 8px;">🤖 Ollama AI Dashboard</h1>
            <p style="color: #666; font-size: 16px;">AI model management and comment generation analytics</p>
        </header>

        {actions.render()}
        {stats.render()}
        {recent_table.render()}
    </div>
    {COMPONENT_SCRIPTS}
</body>
</html>"""


# ==============================================================================
# BRAND DASHBOARD
# ==============================================================================

def generate_brand_dashboard(brand_slug: Optional[str] = None) -> str:
    """
    Generate Brand analytics dashboard
    Shows: Subscribers, posts, engagement, AI persona stats
    """
    conn = get_db()

    # If no brand specified, show all brands
    if brand_slug:
        where_clause = f"WHERE brand = '{brand_slug}'"
        title = f"{brand_slug.title()} Dashboard"
    else:
        where_clause = ""
        title = "All Brands Dashboard"

    # Get brand stats
    try:
        total_subscribers = conn.execute(f'''
            SELECT COUNT(*) as c FROM newsletter_subscribers {where_clause}
        ''').fetchone()['c']
    except:
        total_subscribers = 0

    try:
        verified_subscribers = conn.execute(f'''
            SELECT COUNT(*) as c FROM newsletter_subscribers
            WHERE verified = 1 {where_clause.replace("WHERE", "AND") if where_clause else ""}
        ''').fetchone()['c']
    except:
        verified_subscribers = 0

    # Recent posts (assuming posts table exists)
    try:
        recent_posts = conn.execute(f'''
            SELECT title, brand, created_at, view_count
            FROM posts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
    except:
        recent_posts = []

    conn.close()

    # Build components
    stats = StatsGrid([
        StatsCard("Total Subscribers", f"{total_subscribers:,}", icon="👥"),
        StatsCard("Verified", f"{verified_subscribers:,}", icon="✅"),
        StatsCard("Posts", len(recent_posts), icon="📝"),
    ])

    actions = ActionBar([
        ActionButton("🏠 Admin Home", "/admin", style="secondary"),
        ActionButton("📊 View All Brands", "/admin/brands", style="primary"),
    ])

    posts_table = Section("📝 Recent Posts", DataTable(
        columns=['title', 'brand', 'created_at', 'view_count'],
        rows=[dict(r) for r in recent_posts] if recent_posts else [],
        searchable=True
    )) if recent_posts else Section("📝 Recent Posts", "<p>No posts found</p>")

    # Generate HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Soulfra Admin</title>
    {render_components()}
</head>
<body style="background: #f5f5f5; padding: 20px; font-family: system-ui;">
    <div style="max-width: 1400px; margin: 0 auto;">
        <header style="background: white; padding: 40px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <h1 style="font-size: 36px; color: #333; margin-bottom: 8px;">🏷️ {title}</h1>
            <p style="color: #666; font-size: 16px;">Brand analytics and subscriber metrics</p>
        </header>

        {actions.render()}
        {stats.render()}
        {posts_table.render()}
    </div>
    {COMPONENT_SCRIPTS}
</body>
</html>"""


# ==============================================================================
# EMAIL DASHBOARD
# ==============================================================================

def generate_email_dashboard() -> str:
    """
    Generate Email activity dashboard
    Shows: Inbound emails, conversions, newsletter stats
    """
    conn = get_db()

    # Email stats
    try:
        total_inbound = conn.execute('SELECT COUNT(*) as c FROM inbound_emails').fetchone()['c']
    except:
        total_inbound = 0

    try:
        processed = conn.execute('SELECT COUNT(*) as c FROM inbound_emails WHERE processed = 1').fetchone()['c']
    except:
        processed = 0

    try:
        converted_to_comments = conn.execute('''
            SELECT COUNT(*) as c FROM inbound_emails WHERE comment_id IS NOT NULL
        ''').fetchone()['c']
    except:
        converted_to_comments = 0

    # Recent inbound emails
    try:
        recent_emails = conn.execute('''
            SELECT from_email, subject, processed, post_id, comment_id, received_at
            FROM inbound_emails
            ORDER BY received_at DESC
            LIMIT 20
        ''').fetchall()
    except:
        recent_emails = []

    # Newsletter stats
    try:
        newsletter_sent = conn.execute('SELECT COUNT(*) as c FROM newsletter_digest_log').fetchone()['c']
    except:
        newsletter_sent = 0

    conn.close()

    # Build components
    stats = StatsGrid([
        StatsCard("Inbound Emails", f"{total_inbound:,}", icon="📧"),
        StatsCard("Processed", f"{processed:,}", icon="✅"),
        StatsCard("→ Comments", f"{converted_to_comments:,}", icon="💬"),
        StatsCard("Newsletters Sent", f"{newsletter_sent:,}", icon="📨"),
    ])

    actions = ActionBar([
        ActionButton("🏠 Admin Home", "/admin", style="secondary"),
        ActionButton("📥 View All Emails", "/admin/inbound_emails", style="primary"),
    ])

    emails_table = Section("📧 Recent Inbound Emails", DataTable(
        columns=['received_at', 'from_email', 'subject', 'processed', 'post_id', 'comment_id'],
        rows=[dict(r) for r in recent_emails],
        searchable=True,
        column_labels={
            'received_at': 'Received',
            'from_email': 'From',
            'subject': 'Subject',
            'processed': 'Processed',
            'post_id': 'Post',
            'comment_id': 'Comment'
        }
    ))

    # Generate HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Dashboard | Soulfra Admin</title>
    {render_components()}
</head>
<body style="background: #f5f5f5; padding: 20px; font-family: system-ui;">
    <div style="max-width: 1400px; margin: 0 auto;">
        <header style="background: white; padding: 40px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <h1 style="font-size: 36px; color: #333; margin-bottom: 8px;">📧 Email Dashboard</h1>
            <p style="color: #666; font-size: 16px;">Inbound email activity and newsletter analytics</p>
        </header>

        {actions.render()}
        {stats.render()}
        {emails_table.render()}
    </div>
    {COMPONENT_SCRIPTS}
</body>
</html>"""


# ==============================================================================
# SAVE & LOAD
# ==============================================================================

def save_domain_dashboards() -> List[str]:
    """
    Generate and save all domain dashboards to templates/

    Returns:
        List of generated file paths
    """
    dashboards = [
        ('admin_freelancers.html', generate_freelancer_dashboard()),
        ('admin_ollama.html', generate_ollama_dashboard()),
        ('admin_brands.html', generate_brand_dashboard()),
        ('admin_emails.html', generate_email_dashboard()),
    ]

    saved = []
    for filename, html in dashboards:
        filepath = f"templates/{filename}"
        with open(filepath, 'w') as f:
            f.write(html)
        print(f"✅ Saved {filepath}")
        saved.append(filepath)

    return saved


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Domain Dashboard Generator')
    parser.add_argument('--generate-all', action='store_true', help='Generate all domain dashboards')
    parser.add_argument('--freelancer', action='store_true', help='Generate freelancer dashboard')
    parser.add_argument('--ollama', action='store_true', help='Generate Ollama dashboard')
    parser.add_argument('--brand', metavar='SLUG', help='Generate brand dashboard')
    parser.add_argument('--email', action='store_true', help='Generate email dashboard')
    parser.add_argument('--save', action='store_true', help='Save to templates/')
    parser.add_argument('--preview', action='store_true', help='Print HTML to stdout')

    args = parser.parse_args()

    if args.generate_all:
        saved = save_domain_dashboards()
        print(f"\n✅ Generated {len(saved)} domain dashboards")

    elif args.freelancer:
        html = generate_freelancer_dashboard()
        if args.save:
            with open('templates/admin_freelancers.html', 'w') as f:
                f.write(html)
            print("✅ Saved templates/admin_freelancers.html")
        elif args.preview:
            print(html)

    elif args.ollama:
        html = generate_ollama_dashboard()
        if args.save:
            with open('templates/admin_ollama.html', 'w') as f:
                f.write(html)
            print("✅ Saved templates/admin_ollama.html")
        elif args.preview:
            print(html)

    elif args.brand:
        html = generate_brand_dashboard(args.brand)
        if args.save:
            filename = f'templates/admin_brand_{args.brand}.html'
            with open(filename, 'w') as f:
                f.write(html)
            print(f"✅ Saved {filename}")
        elif args.preview:
            print(html)

    elif args.email:
        html = generate_email_dashboard()
        if args.save:
            with open('templates/admin_emails.html', 'w') as f:
                f.write(html)
            print("✅ Saved templates/admin_emails.html")
        elif args.preview:
            print(html)

    else:
        parser.print_help()

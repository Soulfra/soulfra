#!/usr/bin/env python3
"""
Who Is On My Site - Simple Visitor Tracker

Shows you:
- WHO is visiting (IP addresses)
- WHEN they visited (timestamp)
- WHAT pages they viewed
- WHERE they came from (referrer)
- HOW they're browsing (user agent)

No external dependencies - just SQLite.

Usage:
    # Add to app.py:
    from who_is_on_my_site import track_visit, get_live_visitors

    # Track every page view:
    @app.before_request
    def log_visit():
        track_visit(request)

    # View dashboard:
    python3 who_is_on_my_site.py

    # Or visit:
    http://localhost:5001/analytics
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / 'soulfra.db'


def init_analytics_table():
    """Create analytics table if it doesn't exist"""
    db = sqlite3.connect(DB_PATH)
    db.execute('''
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            user_agent TEXT,
            path TEXT,
            referrer TEXT,
            method TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            brand_slug TEXT,
            session_id TEXT
        )
    ''')

    # Create indexes for fast queries
    db.execute('CREATE INDEX IF NOT EXISTS idx_page_views_timestamp ON page_views(timestamp)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_page_views_ip ON page_views(ip_address)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path)')

    db.commit()
    db.close()


def track_visit(request):
    """
    Track a page visit (call from Flask @app.before_request)

    Args:
        request: Flask request object
    """
    db = sqlite3.connect(DB_PATH)

    # Get visitor info
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    path = request.path
    referrer = request.referrer or ''
    method = request.method

    # Get brand if available (from Flask g object)
    brand_slug = None
    try:
        from flask import g
        if hasattr(g, 'brand') and g.brand:
            brand_slug = g.brand.get('slug')
    except:
        pass

    # Insert page view
    db.execute('''
        INSERT INTO page_views (ip_address, user_agent, path, referrer, method, brand_slug)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ip, user_agent, path, referrer, method, brand_slug))

    db.commit()
    db.close()


def get_live_visitors(minutes=5):
    """
    Get visitors from the last N minutes

    Args:
        minutes: How many minutes back to look (default 5)

    Returns:
        List of visitor dictionaries
    """
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    cutoff = datetime.now() - timedelta(minutes=minutes)

    visitors = db.execute('''
        SELECT
            ip_address,
            COUNT(*) as page_views,
            GROUP_CONCAT(DISTINCT path) as paths,
            MAX(timestamp) as last_seen,
            user_agent
        FROM page_views
        WHERE timestamp > ?
        GROUP BY ip_address
        ORDER BY last_seen DESC
    ''', (cutoff.strftime('%Y-%m-%d %H:%M:%S'),)).fetchall()

    db.close()

    return [dict(v) for v in visitors]


def get_stats(hours=24):
    """
    Get analytics stats for the last N hours

    Args:
        hours: How many hours back to analyze (default 24)

    Returns:
        Dictionary with stats
    """
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    cutoff = datetime.now() - timedelta(hours=hours)

    # Total page views
    total_views = db.execute('''
        SELECT COUNT(*) as count FROM page_views
        WHERE timestamp > ?
    ''', (cutoff.strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()['count']

    # Unique visitors
    unique_visitors = db.execute('''
        SELECT COUNT(DISTINCT ip_address) as count FROM page_views
        WHERE timestamp > ?
    ''', (cutoff.strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()['count']

    # Top pages
    top_pages = db.execute('''
        SELECT path, COUNT(*) as views
        FROM page_views
        WHERE timestamp > ?
        GROUP BY path
        ORDER BY views DESC
        LIMIT 10
    ''', (cutoff.strftime('%Y-%m-%d %H:%M:%S'),)).fetchall()

    # Top referrers
    top_referrers = db.execute('''
        SELECT referrer, COUNT(*) as count
        FROM page_views
        WHERE timestamp > ? AND referrer != ''
        GROUP BY referrer
        ORDER BY count DESC
        LIMIT 10
    ''', (cutoff.strftime('%Y-%m-%d %H:%M:%S'),)).fetchall()

    db.close()

    return {
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'top_pages': [dict(p) for p in top_pages],
        'top_referrers': [dict(r) for r in top_referrers]
    }


def show_dashboard():
    """Print analytics dashboard to terminal"""
    print()
    print("="*70)
    print(" "*20 + "WHO IS ON MY SITE" + " "*30)
    print("="*70)
    print()

    # Live visitors
    print("[Live Visitors - Last 5 Minutes]")
    print()
    visitors = get_live_visitors(5)

    if not visitors:
        print("   No visitors in the last 5 minutes")
    else:
        print(f"   {'IP Address':<15} {'Page Views':<12} {'Last Seen':<20} {'Current Page'}")
        print("   " + "-"*65)
        for v in visitors:
            ip = v['ip_address'][:15]
            views = str(v['page_views'])
            last_seen = v['last_seen'][-8:]  # Just time
            paths = v['paths'].split(',')
            current = paths[-1] if paths else '/'
            print(f"   {ip:<15} {views:<12} {last_seen:<20} {current}")

    # Stats
    print()
    print("[Last 24 Hours]")
    print()
    stats = get_stats(24)

    print(f"   Total Page Views:    {stats['total_views']}")
    print(f"   Unique Visitors:     {stats['unique_visitors']}")

    if stats['unique_visitors'] > 0:
        avg = stats['total_views'] / stats['unique_visitors']
        print(f"   Pages Per Visitor:   {avg:.1f}")

    # Top pages
    if stats['top_pages']:
        print()
        print("   Top Pages:")
        for i, page in enumerate(stats['top_pages'][:5], 1):
            print(f"      {i}. {page['path']:<40} ({page['views']} views)")

    # Top referrers
    if stats['top_referrers']:
        print()
        print("   Top Referrers:")
        for i, ref in enumerate(stats['top_referrers'][:5], 1):
            domain = ref['referrer'][:50]
            print(f"      {i}. {domain:<50} ({ref['count']} visits)")

    print()
    print("="*70)
    print()
    print("💡 To track visitors, add this to app.py:")
    print()
    print("   from who_is_on_my_site import track_visit")
    print()
    print("   @app.before_request")
    print("   def log_visit():")
    print("       track_visit(request)")
    print()
    print("   Then visit: http://localhost:5001/analytics")
    print()


if __name__ == '__main__':
    # Initialize table
    init_analytics_table()

    # Show dashboard
    show_dashboard()

#!/usr/bin/env python3
"""
PageRank Calculator - Logarithmic decay and ranking algorithm

Calculates PageRank for blog posts based on:
1. Incoming links (40%) - How many posts link to this one
2. External shares (30%) - References from outside the system
3. View count (20%) - How many people read it
4. Freshness (10%) - Logarithmic decay over time

Formula:
    PageRank = (incoming_links * 0.4) + (external_refs * 0.3) +
               (views * 0.2) + (freshness_decay * 0.1)

Freshness decay:
    freshness = 100 / (1 + log(days_old + 1))

    Day 0: 100%
    Day 1: 59%
    Day 7: 27%
    Day 30: 13%
    Day 90: 9%

Usage:
    python3 pagerank_calculator.py calculate-all
    python3 pagerank_calculator.py calculate-post 5
    python3 pagerank_calculator.py show-rankings
"""

import math
from datetime import datetime, timezone, timedelta
from database import get_db
import re


def calculate_freshness_decay(published_at):
    """
    Calculate logarithmic freshness decay

    Args:
        published_at (str): ISO timestamp of publication

    Returns:
        float: Freshness score (0.0 - 100.0)
    """
    # Parse published date
    try:
        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
    except:
        # Fallback - return max freshness if can't parse
        return 100.0

    now = datetime.now(timezone.utc)

    # Calculate days old
    days_old = (now - pub_date).days

    # Logarithmic decay: 100 / (1 + log(days + 1))
    # Prevents division by zero, starts at 100 for day 0
    if days_old == 0:
        return 100.0

    freshness = 100.0 / (1.0 + math.log(days_old + 1))

    return freshness


def count_incoming_links(post_id):
    """
    Count how many other posts link to this post

    Args:
        post_id (int): Post ID

    Returns:
        int: Number of incoming links
    """
    db = get_db()

    # Get this post's slug
    post = db.execute('SELECT slug FROM posts WHERE id = ?', (post_id,)).fetchone()
    if not post:
        return 0

    post_slug = post['slug']

    # Search for links in other posts' content
    # Matches: [text](/post/slug.html) or [text](slug.html) or just "slug"
    all_posts = db.execute('SELECT id, content FROM posts WHERE id != ?', (post_id,)).fetchall()

    incoming_count = 0
    for other_post in all_posts:
        content = other_post['content']

        # Check for markdown links
        if f'/post/{post_slug}' in content or f'/{post_slug}' in content or post_slug in content:
            incoming_count += 1

    return incoming_count


def count_external_references(post_content):
    """
    Count external references (links to outside sources)

    More external refs = Higher quality (research-backed content)

    Args:
        post_content (str): Post markdown content

    Returns:
        int: Number of external links
    """
    # Find markdown links: [text](http://...)
    external_links = re.findall(r'\[.*?\]\((https?://.*?)\)', post_content)

    # Filter out internal links (soulfra domains)
    internal_domains = ['soulfra.github.io', 'calriven.com', 'deathtodata.com', 'cringeproof.com']

    external_count = 0
    for link in external_links:
        is_internal = any(domain in link for domain in internal_domains)
        if not is_internal:
            external_count += 1

    return external_count


def get_view_count(post_id):
    """
    Get view count for post

    TODO: Implement view tracking (currently returns 0)

    Args:
        post_id (int): Post ID

    Returns:
        int: View count
    """
    # Placeholder - would need to track views in separate table
    # For now, estimate based on post age (older = more views)
    db = get_db()
    post = db.execute('SELECT published_at FROM posts WHERE id = ?', (post_id,)).fetchone()

    if not post:
        return 0

    # Rough estimate: 10 views per day old
    try:
        pub_date = datetime.fromisoformat(post['published_at'].replace('Z', '+00:00'))
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
    except:
        # Fallback if date parsing fails
        return 0

    days_old = (datetime.now(timezone.utc) - pub_date).days

    estimated_views = days_old * 10

    return max(0, estimated_views)


def calculate_pagerank(post_id):
    """
    Calculate PageRank for a single post

    Args:
        post_id (int): Post ID

    Returns:
        float: PageRank score (0.0 - 100.0+)
    """
    db = get_db()

    # Get post
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if not post:
        return 0.0

    # 1. Incoming links (40% weight)
    incoming_links = count_incoming_links(post_id)
    incoming_score = min(incoming_links * 10, 40.0)  # Max 40 points

    # 2. External references (30% weight)
    external_refs = count_external_references(post['content'])
    external_score = min(external_refs * 5, 30.0)  # Max 30 points

    # 3. View count (20% weight)
    views = get_view_count(post_id)
    view_score = min(views / 10, 20.0)  # Max 20 points (200+ views)

    # 4. Freshness decay (10% weight)
    freshness = calculate_freshness_decay(post['published_at'])
    freshness_score = (freshness / 100.0) * 10.0  # Scale to max 10 points

    # Total PageRank
    pagerank = incoming_score + external_score + view_score + freshness_score

    # Calculate freshness decay factor (for separate column)
    freshness_decay = freshness / 100.0

    return pagerank, freshness_decay


def update_post_pagerank(post_id):
    """
    Calculate and update PageRank for a post

    Args:
        post_id (int): Post ID

    Returns:
        float: New PageRank score
    """
    pagerank, freshness_decay = calculate_pagerank(post_id)

    db = get_db()
    updated_at = datetime.now(timezone.utc).isoformat()

    db.execute('''
        UPDATE posts
        SET pagerank = ?,
            freshness_decay = ?,
            pagerank_updated_at = ?
        WHERE id = ?
    ''', (pagerank, freshness_decay, updated_at, post_id))

    db.commit()

    print(f"✅ Post {post_id}: PageRank = {pagerank:.2f}, Freshness = {freshness_decay:.2f}")

    return pagerank


def calculate_all_pageranks():
    """
    Calculate PageRank for all posts

    Returns:
        int: Number of posts updated
    """
    db = get_db()

    posts = db.execute('SELECT id FROM posts').fetchall()

    print(f"\n{'='*60}")
    print(f"Calculating PageRank for {len(posts)} posts...")
    print(f"{'='*60}\n")

    for post in posts:
        update_post_pagerank(post['id'])

    print(f"\n✅ Updated PageRank for {len(posts)} posts\n")

    return len(posts)


def show_rankings(limit=20):
    """
    Show top posts by PageRank

    Args:
        limit (int): Number of posts to show

    Returns:
        None (prints to console)
    """
    db = get_db()

    posts = db.execute('''
        SELECT id, title, pagerank, freshness_decay, is_evergreen, published_at
        FROM posts
        ORDER BY pagerank DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    print(f"\n{'='*80}")
    print(f"TOP {limit} POSTS BY PAGERANK")
    print(f"{'='*80}")
    print(f"{'Rank':<6} {'ID':<6} {'PageRank':<12} {'Fresh%':<10} {'Evergreen':<12} {'Title':<30}")
    print(f"{'-'*80}")

    for rank, post in enumerate(posts, 1):
        fresh_pct = f"{post['freshness_decay']*100:.1f}%"
        evergreen = "✅ Yes" if post['is_evergreen'] else "❌ No"
        title = post['title'][:28] + '...' if len(post['title']) > 30 else post['title']

        print(f"{rank:<6} {post['id']:<6} {post['pagerank']:<12.2f} {fresh_pct:<10} {evergreen:<12} {title:<30}")

    print(f"{'='*80}\n")


def show_post_details(post_id):
    """
    Show detailed PageRank breakdown for a post

    Args:
        post_id (int): Post ID

    Returns:
        None (prints to console)
    """
    db = get_db()

    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if not post:
        print(f"❌ Post {post_id} not found")
        return

    # Calculate components
    incoming = count_incoming_links(post_id)
    external = count_external_references(post['content'])
    views = get_view_count(post_id)
    freshness = calculate_freshness_decay(post['published_at'])

    pagerank, freshness_decay = calculate_pagerank(post_id)

    print(f"\n{'='*60}")
    print(f"PAGERANK BREAKDOWN: {post['title']}")
    print(f"{'='*60}")
    print(f"Post ID:             {post_id}")
    print(f"Published:           {post['published_at'][:10]}")
    print(f"Current PageRank:    {post['pagerank']:.2f}")
    print(f"\n--- Components ---")
    print(f"Incoming Links:      {incoming} → Score: {min(incoming * 10, 40):.1f} / 40")
    print(f"External Refs:       {external} → Score: {min(external * 5, 30):.1f} / 30")
    print(f"View Count:          {views} → Score: {min(views / 10, 20):.1f} / 20")
    print(f"Freshness:           {freshness:.1f}% → Score: {(freshness/100)*10:.1f} / 10")
    print(f"\n--- Calculated ---")
    print(f"New PageRank:        {pagerank:.2f}")
    print(f"Freshness Decay:     {freshness_decay:.2f}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 pagerank_calculator.py calculate-all")
        print("  python3 pagerank_calculator.py calculate-post <post_id>")
        print("  python3 pagerank_calculator.py show-rankings [limit]")
        print("  python3 pagerank_calculator.py details <post_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "calculate-all":
        calculate_all_pageranks()
        show_rankings(10)

    elif command == "calculate-post":
        if len(sys.argv) < 3:
            print("Usage: python3 pagerank_calculator.py calculate-post <post_id>")
            sys.exit(1)

        post_id = int(sys.argv[2])
        pagerank = update_post_pagerank(post_id)
        show_post_details(post_id)

    elif command == "show-rankings":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_rankings(limit)

    elif command == "details":
        if len(sys.argv) < 3:
            print("Usage: python3 pagerank_calculator.py details <post_id>")
            sys.exit(1)

        post_id = int(sys.argv[2])
        show_post_details(post_id)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

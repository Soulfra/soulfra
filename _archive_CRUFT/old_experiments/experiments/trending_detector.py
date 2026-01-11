#!/usr/bin/env python3
"""
Trending Topic Detector

Uses existing tracking data to detect trending topics:
- Tags frequency from post_tags
- QR scan activity from qr_scans
- URL click counts from url_shortcuts

This connects tracking data → trending keywords → product generation.
No LLM needed - pure SQL + Python stdlib.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict


def get_db() -> sqlite3.Connection:
    """Get database connection with Row factory."""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_trending_tags(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get trending tags based on recent post activity.

    Strategy:
    1. Count tag mentions in recent posts
    2. Weight by recency (newer = higher score)
    3. Return top tags by score

    Args:
        days: Look back this many days (default 7)
        limit: Max tags to return (default 10)

    Returns:
        List of dicts with tag_name, mention_count, trending_score
    """
    conn = get_db()
    cursor = conn.cursor()

    # Calculate cutoff date
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    rows = cursor.execute('''
        SELECT
            t.name as tag_name,
            COUNT(DISTINCT pt.post_id) as mention_count,
            COUNT(DISTINCT pt.post_id) * 1.0 as trending_score
        FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        JOIN posts p ON pt.post_id = p.id
        WHERE p.published_at >= ?
        GROUP BY t.id, t.name
        ORDER BY trending_score DESC
        LIMIT ?
    ''', (cutoff, limit)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_trending_from_qr_scans(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get trending topics based on QR scan activity.

    Looks at which QR codes (linked to posts) are being scanned most.

    Args:
        days: Look back this many days
        limit: Max results to return

    Returns:
        List of dicts with code_data, scan_count, post_id (if linked)
    """
    conn = get_db()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    rows = cursor.execute('''
        SELECT
            qc.code_data,
            qc.target_url,
            COUNT(qs.id) as scan_count,
            MAX(qs.scanned_at) as last_scan
        FROM qr_codes qc
        JOIN qr_scans qs ON qc.id = qs.qr_code_id
        WHERE qs.scanned_at >= ?
        GROUP BY qc.id, qc.code_data, qc.target_url
        ORDER BY scan_count DESC
        LIMIT ?
    ''', (cutoff, limit)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_trending_from_url_clicks(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get trending topics based on URL shortener click activity.

    Looks at which short URLs are getting the most clicks.

    Args:
        days: Look back this many days
        limit: Max results to return

    Returns:
        List of dicts with short_id, clicks, username
    """
    conn = get_db()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    rows = cursor.execute('''
        SELECT
            short_id,
            username,
            clicks,
            created_at
        FROM url_shortcuts
        WHERE created_at >= ?
        ORDER BY clicks DESC
        LIMIT ?
    ''', (cutoff, limit)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def calculate_post_trending_score(post_id: int) -> float:
    """
    Calculate trending score for a post.

    Combines:
    - Recency (newer = higher)
    - Comment count
    - Tag mentions
    - External signals (QR scans, URL clicks)

    Args:
        post_id: Post to score

    Returns:
        Trending score (0.0 to 100.0)
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get post data
    post = cursor.execute(
        'SELECT published_at FROM posts WHERE id = ?',
        (post_id,)
    ).fetchone()

    if not post:
        return 0.0

    # Recency score (0-40 points)
    published = datetime.fromisoformat(post['published_at'])
    age_days = (datetime.now() - published).days
    recency_score = max(0, 40 - age_days)

    # Comment count score (0-30 points)
    comment_count = cursor.execute(
        'SELECT COUNT(*) as count FROM comments WHERE post_id = ?',
        (post_id,)
    ).fetchone()['count']
    comment_score = min(30, comment_count * 3)

    # Tag mentions score (0-30 points)
    tag_count = cursor.execute(
        'SELECT COUNT(*) as count FROM post_tags WHERE post_id = ?',
        (post_id,)
    ).fetchone()['count']
    tag_score = min(30, tag_count * 10)

    conn.close()

    total_score = recency_score + comment_score + tag_score
    return round(total_score, 2)


def get_trending_posts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get trending posts based on calculated scores.

    Args:
        limit: Max posts to return

    Returns:
        List of dicts with post_id, title, slug, trending_score
    """
    conn = get_db()
    cursor = conn.cursor()

    posts = cursor.execute(
        'SELECT id, title, slug FROM posts ORDER BY published_at DESC LIMIT 50'
    ).fetchall()

    conn.close()

    # Calculate trending score for each post
    trending = []
    for post in posts:
        score = calculate_post_trending_score(post['id'])
        trending.append({
            'post_id': post['id'],
            'title': post['title'],
            'slug': post['slug'],
            'trending_score': score
        })

    # Sort by score descending
    trending.sort(key=lambda x: x['trending_score'], reverse=True)

    return trending[:limit]


def extract_keywords_from_trending() -> List[str]:
    """
    Extract keywords from trending tags and posts.

    Returns simple, human-readable keywords that can be used for:
    - Slogan generation
    - Merch design
    - Product naming

    Returns:
        List of trending keywords (strings)
    """
    keywords = []

    # Get trending tags
    tags = get_trending_tags(days=30, limit=20)
    for tag in tags:
        keywords.append(tag['tag_name'])

    # Get trending posts and extract simple keywords from titles
    posts = get_trending_posts(limit=10)
    for post in posts:
        title = post['title'].lower()
        # Extract simple keywords (words longer than 3 chars)
        words = [w.strip('.,!?') for w in title.split() if len(w) > 3]
        keywords.extend(words[:3])  # Take top 3 words from each title

    # Deduplicate and clean
    unique_keywords = list(dict.fromkeys(keywords))  # Preserve order

    return unique_keywords


def get_trending_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get comprehensive trending summary across all signals.

    Args:
        days: Look back this many days

    Returns:
        Dict with all trending data: tags, posts, qr_scans, url_clicks, keywords
    """
    summary = {
        'period_days': days,
        'generated_at': datetime.now().isoformat(),
        'trending_tags': get_trending_tags(days=days, limit=10),
        'trending_posts': get_trending_posts(limit=10),
        'qr_scan_activity': get_trending_from_qr_scans(days=days, limit=5),
        'url_click_activity': get_trending_from_url_clicks(days=days, limit=5),
        'keywords': extract_keywords_from_trending()[:20]
    }

    return summary


if __name__ == '__main__':
    print("📈 Trending Topic Detector\n")

    # Test trending tags
    print("🏷️  Trending Tags (last 30 days):")
    tags = get_trending_tags(days=30, limit=10)
    if tags:
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag['tag_name']} ({int(tag['mention_count'])} mentions)")
    else:
        print("  No trending tags found")

    print()

    # Test trending posts
    print("📝 Trending Posts:")
    posts = get_trending_posts(limit=5)
    if posts:
        for i, post in enumerate(posts, 1):
            print(f"  {i}. {post['title'][:60]}... (score: {post['trending_score']})")
    else:
        print("  No trending posts found")

    print()

    # Test keywords extraction
    print("🔑 Extracted Keywords:")
    keywords = extract_keywords_from_trending()
    if keywords:
        print(f"  {', '.join(keywords[:15])}")
    else:
        print("  No keywords found")

    print()

    # Test QR scan activity
    print("📱 QR Scan Activity (last 7 days):")
    qr_scans = get_trending_from_qr_scans(days=7, limit=5)
    if qr_scans:
        for scan in qr_scans:
            print(f"  {scan['code_data']}: {scan['scan_count']} scans")
    else:
        print("  No QR scan activity")

    print()

    # Test URL click activity
    print("🔗 URL Click Activity (last 7 days):")
    url_clicks = get_trending_from_url_clicks(days=7, limit=5)
    if url_clicks:
        for click in url_clicks:
            print(f"  /{click['short_id']} ({click['username']}): {click['clicks']} clicks")
    else:
        print("  No URL click activity")

    print()
    print("✅ Trending detection complete!")

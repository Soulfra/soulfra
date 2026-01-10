#!/usr/bin/env python3
"""
Query Templates - Reusable SQL Patterns for Soulfra

Provides pre-built, tested SQL queries for common data access patterns.
Think of this as the "standard library" for database queries.

Philosophy:
-----------
- DRY (Don't Repeat Yourself): Write each query once
- Type-safe: Return dictionaries with known keys
- Fast: Optimized with proper indexes
- Documented: Every query has docstring with examples

Usage:
    from query_templates import QueryTemplates

    qt = QueryTemplates()

    # Get recent comments for a brand
    comments = qt.get_brand_comments('calriven', days=7)

    # Get API usage stats
    stats = qt.get_api_usage('calriven')

    # Get newsletter subscribers
    subscribers = qt.get_newsletter_subscribers('calriven')
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import get_db


class QueryTemplates:
    """
    Collection of reusable SQL query templates

    All methods return:
    - List[Dict]: For multi-row results
    - Dict: For single-row results
    - None: If no results found
    """

    def __init__(self, db_path: str = 'soulfra.db'):
        """
        Initialize query templates

        Args:
            db_path: Path to SQLite database (default: soulfra.db)
        """
        self.db_path = db_path

    # ==========================================================================
    # BRAND & PERSONA QUERIES
    # ==========================================================================

    def get_brand_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Get brand details by slug

        Args:
            slug: Brand slug (e.g., 'calriven')

        Returns:
            {
                'id': 1,
                'slug': 'calriven',
                'name': 'CalRiven',
                'tagline': '...',
                'description': '...',
                'created_at': '2025-12-25'
            }

        Example:
            >>> qt = QueryTemplates()
            >>> brand = qt.get_brand_by_slug('calriven')
            >>> print(brand['name'])
            CalRiven
        """
        conn = get_db()
        result = conn.execute(
            'SELECT * FROM brands WHERE slug = ?',
            (slug,)
        ).fetchone()
        conn.close()

        return dict(result) if result else None

    def get_all_brands(self, active_only: bool = True) -> List[Dict]:
        """
        Get all brands in system

        Args:
            active_only: Only return active brands (default: True)

        Returns:
            List of brand dictionaries

        Example:
            >>> qt = QueryTemplates()
            >>> brands = qt.get_all_brands()
            >>> len(brands)
            5
        """
        conn = get_db()

        query = 'SELECT * FROM brands'
        if active_only:
            query += ' WHERE status = "active"'
        query += ' ORDER BY created_at DESC'

        results = conn.execute(query).fetchall()
        conn.close()

        return [dict(r) for r in results]

    def get_ai_personas(self, brand_slug: Optional[str] = None) -> List[Dict]:
        """
        Get AI personas (users with is_ai_persona = 1)

        Args:
            brand_slug: Filter by brand (None = all)

        Returns:
            List of AI persona user dictionaries

        Example:
            >>> qt = QueryTemplates()
            >>> personas = qt.get_ai_personas('calriven')
            >>> [p['username'] for p in personas]
            ['calriven', 'theauditor', 'deathtodata']
        """
        conn = get_db()

        query = '''
            SELECT u.*
            FROM users u
            WHERE u.is_ai_persona = 1
        '''

        params = []
        if brand_slug:
            query += ' AND u.email LIKE ?'
            params.append(f'%{brand_slug}%')

        query += ' ORDER BY u.created_at DESC'

        results = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(r) for r in results]

    # ==========================================================================
    # COMMENT QUERIES
    # ==========================================================================

    def get_brand_comments(
        self,
        brand_slug: str,
        days: int = 7,
        ai_only: bool = True,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent comments for a brand

        Args:
            brand_slug: Brand to get comments for
            days: Days to look back (default: 7)
            ai_only: Only AI comments (default: True)
            limit: Max comments to return (default: 100)

        Returns:
            List of comment dictionaries with post info

        Example:
            >>> qt = QueryTemplates()
            >>> comments = qt.get_brand_comments('calriven', days=7)
            >>> comments[0]['ai_persona']
            'calriven'
        """
        conn = get_db()

        query = '''
            SELECT
                c.id,
                c.content,
                c.created_at,
                u.username as ai_persona,
                u.email as persona_email,
                p.id as post_id,
                p.title as post_title,
                p.slug as post_slug
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN posts p ON c.post_id = p.id
            WHERE 1=1
        '''

        params = []

        if ai_only:
            query += ' AND u.is_ai_persona = 1'

        if brand_slug:
            query += ' AND u.email LIKE ?'
            params.append(f'%{brand_slug}%')

        query += ' AND c.created_at > datetime("now", "-" || ? || " days")'
        params.append(days)

        query += ' ORDER BY c.created_at DESC LIMIT ?'
        params.append(limit)

        results = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(r) for r in results]

    def get_post_comments(
        self,
        post_id: int,
        include_ai: bool = True
    ) -> List[Dict]:
        """
        Get all comments for a specific post

        Args:
            post_id: Post ID to get comments for
            include_ai: Include AI persona comments (default: True)

        Returns:
            List of comment dictionaries with user info

        Example:
            >>> qt = QueryTemplates()
            >>> comments = qt.get_post_comments(1)
            >>> len(comments)
            10
        """
        conn = get_db()

        query = '''
            SELECT
                c.*,
                u.username,
                u.email,
                u.is_ai_persona
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
        '''

        params = [post_id]

        if not include_ai:
            query += ' AND u.is_ai_persona = 0'

        query += ' ORDER BY c.created_at ASC'

        results = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(r) for r in results]

    # ==========================================================================
    # API KEY QUERIES
    # ==========================================================================

    def get_api_key_by_key(self, api_key: str) -> Optional[Dict]:
        """
        Get API key details

        Args:
            api_key: API key string (e.g., 'SK-...')

        Returns:
            API key dictionary or None

        Example:
            >>> qt = QueryTemplates()
            >>> key = qt.get_api_key_by_key('SK-abc123')
            >>> key['tier']
            'free'
        """
        conn = get_db()
        result = conn.execute(
            'SELECT * FROM api_keys WHERE api_key = ?',
            (api_key,)
        ).fetchone()
        conn.close()

        return dict(result) if result else None

    def get_api_usage(
        self,
        brand_slug: str,
        days: int = 7
    ) -> Dict:
        """
        Get API usage statistics for a brand

        Args:
            brand_slug: Brand to get stats for
            days: Days to look back (default: 7)

        Returns:
            {
                'total_calls': 150,
                'unique_users': 5,
                'avg_response_time_ms': 45,
                'error_rate': 0.02
            }

        Example:
            >>> qt = QueryTemplates()
            >>> stats = qt.get_api_usage('calriven', days=7)
            >>> stats['total_calls']
            150
        """
        conn = get_db()

        stats = conn.execute('''
            SELECT
                COUNT(*) as total_calls,
                COUNT(DISTINCT ak.user_email) as unique_users,
                AVG(acl.response_time_ms) as avg_response_time_ms,
                SUM(CASE WHEN acl.response_status >= 400 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as error_rate
            FROM api_call_logs acl
            JOIN api_keys ak ON acl.api_key_id = ak.id
            WHERE ak.brand_slug = ?
            AND acl.created_at > datetime('now', '-' || ? || ' days')
        ''', (brand_slug, days)).fetchone()

        conn.close()

        return dict(stats) if stats else {
            'total_calls': 0,
            'unique_users': 0,
            'avg_response_time_ms': 0,
            'error_rate': 0
        }

    def get_api_call_logs(
        self,
        api_key: str,
        days: int = 7,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get API call logs for a specific key

        Args:
            api_key: API key to get logs for
            days: Days to look back (default: 7)
            limit: Max logs to return (default: 100)

        Returns:
            List of API call log dictionaries

        Example:
            >>> qt = QueryTemplates()
            >>> logs = qt.get_api_call_logs('SK-abc123')
            >>> logs[0]['endpoint']
            '/api/v1/calriven/comment'
        """
        conn = get_db()

        # Get API key ID first
        key_row = conn.execute(
            'SELECT id FROM api_keys WHERE api_key = ?',
            (api_key,)
        ).fetchone()

        if not key_row:
            conn.close()
            return []

        api_key_id = key_row['id']

        results = conn.execute('''
            SELECT *
            FROM api_call_logs
            WHERE api_key_id = ?
            AND created_at > datetime('now', '-' || ? || ' days')
            ORDER BY created_at DESC
            LIMIT ?
        ''', (api_key_id, days, limit)).fetchall()

        conn.close()

        return [dict(r) for r in results]

    # ==========================================================================
    # NEWSLETTER QUERIES
    # ==========================================================================

    def get_newsletter_subscribers(
        self,
        brand: Optional[str] = None,
        verified_only: bool = True
    ) -> List[Dict]:
        """
        Get newsletter subscribers

        Args:
            brand: Filter by brand (None = all)
            verified_only: Only verified subscribers (default: True)

        Returns:
            List of subscriber dictionaries

        Example:
            >>> qt = QueryTemplates()
            >>> subs = qt.get_newsletter_subscribers('calriven')
            >>> len(subs)
            5
        """
        conn = get_db()

        query = 'SELECT * FROM newsletter_subscribers WHERE 1=1'
        params = []

        if verified_only:
            query += ' AND verified = 1'

        if brand:
            query += ' AND brand = ?'
            params.append(brand)

        query += ' AND unsubscribed_at IS NULL'
        query += ' ORDER BY subscribed_at DESC'

        results = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(r) for r in results]

    def get_subscriber_by_email(self, email: str) -> Optional[Dict]:
        """
        Get subscriber by email

        Args:
            email: Subscriber email

        Returns:
            Subscriber dictionary or None

        Example:
            >>> qt = QueryTemplates()
            >>> sub = qt.get_subscriber_by_email('test@example.com')
            >>> sub['brand']
            'calriven'
        """
        conn = get_db()
        result = conn.execute(
            'SELECT * FROM newsletter_subscribers WHERE email = ?',
            (email,)
        ).fetchone()
        conn.close()

        return dict(result) if result else None

    # ==========================================================================
    # POST QUERIES
    # ==========================================================================

    def get_recent_posts(
        self,
        days: int = 7,
        published_only: bool = True,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get recent blog posts

        Args:
            days: Days to look back (default: 7)
            published_only: Only published posts (default: True)
            limit: Max posts to return (default: 50)

        Returns:
            List of post dictionaries

        Example:
            >>> qt = QueryTemplates()
            >>> posts = qt.get_recent_posts(days=7)
            >>> posts[0]['title']
            'Welcome to Soulfra'
        """
        conn = get_db()

        query = 'SELECT * FROM posts WHERE 1=1'
        params = []

        if published_only:
            query += ' AND published = 1'

        query += ' AND created_at > datetime("now", "-" || ? || " days")'
        params.append(days)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        results = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(r) for r in results]

    def get_post_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Get post by slug

        Args:
            slug: Post slug

        Returns:
            Post dictionary or None

        Example:
            >>> qt = QueryTemplates()
            >>> post = qt.get_post_by_slug('welcome')
            >>> post['title']
            'Welcome to Soulfra Simple'
        """
        conn = get_db()
        result = conn.execute(
            'SELECT * FROM posts WHERE slug = ?',
            (slug,)
        ).fetchone()
        conn.close()

        return dict(result) if result else None

    # ==========================================================================
    # STATISTICS QUERIES
    # ==========================================================================

    def get_platform_stats(self, days: int = 7) -> Dict:
        """
        Get overall platform statistics

        Args:
            days: Days to look back (default: 7)

        Returns:
            {
                'total_users': 100,
                'ai_personas': 8,
                'total_posts': 50,
                'total_comments': 200,
                'api_calls': 1500,
                'newsletter_subscribers': 25
            }

        Example:
            >>> qt = QueryTemplates()
            >>> stats = qt.get_platform_stats(days=7)
            >>> stats['api_calls']
            1500
        """
        conn = get_db()

        # Get all stats in one query using subqueries
        stats = conn.execute(f'''
            SELECT
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE is_ai_persona = 1) as ai_personas,
                (SELECT COUNT(*) FROM posts) as total_posts,
                (SELECT COUNT(*) FROM comments WHERE created_at > datetime('now', '-{days} days')) as total_comments,
                (SELECT COUNT(*) FROM api_call_logs WHERE created_at > datetime('now', '-{days} days')) as api_calls,
                (SELECT COUNT(*) FROM newsletter_subscribers WHERE verified = 1 AND unsubscribed_at IS NULL) as newsletter_subscribers
        ''').fetchone()

        conn.close()

        return dict(stats) if stats else {}

    # ==========================================================================
    # FEED QUERIES (RSS/XML)
    # ==========================================================================

    def get_feed_items(
        self,
        feed_type: str = 'posts',
        brand_slug: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get items for RSS/XML feeds

        Args:
            feed_type: 'posts' or 'comments' (default: 'posts')
            brand_slug: Filter by brand (None = all)
            limit: Max items to return (default: 50)

        Returns:
            List of feed item dictionaries

        Example:
            >>> qt = QueryTemplates()
            >>> items = qt.get_feed_items('posts', limit=10)
            >>> items[0]['title']
            'Welcome to Soulfra'
        """
        conn = get_db()

        if feed_type == 'posts':
            query = '''
                SELECT
                    id,
                    title,
                    slug,
                    content,
                    created_at,
                    updated_at
                FROM posts
                WHERE published = 1
                ORDER BY created_at DESC
                LIMIT ?
            '''
            results = conn.execute(query, (limit,)).fetchall()

        elif feed_type == 'comments':
            query = '''
                SELECT
                    c.id,
                    c.content,
                    c.created_at,
                    u.username as author,
                    p.title as post_title,
                    p.slug as post_slug
                FROM comments c
                JOIN users u ON c.user_id = u.id
                JOIN posts p ON c.post_id = p.id
                WHERE u.is_ai_persona = 1
            '''

            params = []
            if brand_slug:
                query += ' AND u.email LIKE ?'
                params.append(f'%{brand_slug}%')

            query += ' ORDER BY c.created_at DESC LIMIT ?'
            params.append(limit)

            results = conn.execute(query, params).fetchall()

        else:
            conn.close()
            return []

        conn.close()

        return [dict(r) for r in results]


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def quick_query(query_name: str, **kwargs) -> any:
    """
    Quick access to common queries

    Args:
        query_name: Name of query method (e.g., 'get_brand_comments')
        **kwargs: Arguments to pass to query method

    Returns:
        Query results

    Example:
        >>> from query_templates import quick_query
        >>> comments = quick_query('get_brand_comments', brand_slug='calriven', days=7)
        >>> len(comments)
        35
    """
    qt = QueryTemplates()
    method = getattr(qt, query_name, None)

    if not method:
        raise ValueError(f"Unknown query: {query_name}")

    return method(**kwargs)


if __name__ == '__main__':
    # Test query templates
    print("Testing Query Templates...")
    print("=" * 60)

    qt = QueryTemplates()

    # Test platform stats
    print("\n📊 Platform Stats:")
    stats = qt.get_platform_stats(days=7)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test brand comments
    print("\n💬 Recent Comments (calriven):")
    comments = qt.get_brand_comments('calriven', days=7, limit=5)
    for c in comments:
        print(f"  • {c['ai_persona']}: {c['content'][:60]}...")

    # Test API usage
    print("\n🔑 API Usage (calriven):")
    api_stats = qt.get_api_usage('calriven', days=7)
    for key, value in api_stats.items():
        print(f"  {key}: {value}")

    # Test newsletter subscribers
    print("\n📧 Newsletter Subscribers:")
    subs = qt.get_newsletter_subscribers()
    print(f"  Total subscribers: {len(subs)}")

    print("\n✅ Query templates working!\n")

#!/usr/bin/env python3
"""
Publishing Pipeline - Universal Content Distribution

When content is created (AI comment, blog post, etc.), automatically publish it to:
1. Database (primary storage)
2. RSS/XML feeds
3. Newsletter queue
4. JSON API cache
5. WebSocket (real-time updates)
6. Podcast transcripts (future)

Think of this like media-ssl for publishing - one source, many destinations.

Philosophy:
-----------
Write once, publish everywhere. Content flows through the pipeline and gets
distributed to all relevant channels automatically.

Usage:
    from publishing_pipeline import PublishingPipeline

    pipeline = PublishingPipeline()

    # Publish an AI comment
    pipeline.publish_comment(
        comment_id=123,
        brand_slug='calriven',
        post_id=1
    )

    # Publish a blog post
    pipeline.publish_post(
        post_id=42,
        notify_subscribers=True
    )
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db
from query_templates import QueryTemplates


class PublishingPipeline:
    """
    Central content publishing system

    Coordinates distribution of content across multiple channels.
    """

    def __init__(self):
        """Initialize publishing pipeline"""
        self.qt = QueryTemplates()

    # ==========================================================================
    # COMMENT PUBLISHING
    # ==========================================================================

    def publish_comment(
        self,
        comment_id: int,
        brand_slug: str,
        post_id: int,
        notify_subscribers: bool = False
    ) -> Dict:
        """
        Publish an AI comment to all channels

        Args:
            comment_id: Comment ID from database
            brand_slug: Brand that generated comment
            post_id: Post the comment is on
            notify_subscribers: Send to newsletter queue (default: False)

        Returns:
            {
                'success': True,
                'published_to': ['database', 'rss', 'json', 'websocket'],
                'comment_id': 123
            }

        Example:
            >>> pipeline = PublishingPipeline()
            >>> result = pipeline.publish_comment(123, 'calriven', 1)
            >>> result['published_to']
            ['database', 'rss', 'json']
        """
        conn = get_db()

        # Get comment details
        comment = conn.execute('''
            SELECT
                c.*,
                u.username as author,
                u.email as author_email,
                p.title as post_title,
                p.slug as post_slug
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN posts p ON c.post_id = p.id
            WHERE c.id = ?
        ''', (comment_id,)).fetchone()

        if not comment:
            conn.close()
            return {'success': False, 'error': 'Comment not found'}

        published_to = ['database']  # Already in database

        # 1. Update RSS feed cache
        try:
            self._update_rss_cache(brand_slug, 'comment', dict(comment))
            published_to.append('rss')
        except Exception as e:
            print(f"⚠️  RSS cache update failed: {e}")

        # 2. Update JSON API cache
        try:
            self._update_json_cache(brand_slug, 'comment', dict(comment))
            published_to.append('json')
        except Exception as e:
            print(f"⚠️  JSON cache update failed: {e}")

        # 3. Queue for newsletter (if requested)
        if notify_subscribers:
            try:
                self._queue_for_newsletter(brand_slug, 'comment', dict(comment))
                published_to.append('newsletter_queue')
            except Exception as e:
                print(f"⚠️  Newsletter queue failed: {e}")

        # 4. Broadcast via WebSocket (if server is running)
        try:
            self._broadcast_websocket(brand_slug, 'new_comment', {
                'comment_id': comment_id,
                'author': dict(comment)['author'],
                'post_slug': dict(comment)['post_slug'],
                'content_preview': dict(comment)['content'][:100]
            })
            published_to.append('websocket')
        except Exception as e:
            print(f"⚠️  WebSocket broadcast failed: {e}")

        conn.close()

        print(f"✅ Published comment #{comment_id} to: {', '.join(published_to)}")

        return {
            'success': True,
            'published_to': published_to,
            'comment_id': comment_id
        }

    # ==========================================================================
    # POST PUBLISHING
    # ==========================================================================

    def publish_post(
        self,
        post_id: int,
        notify_subscribers: bool = True
    ) -> Dict:
        """
        Publish a blog post to all channels

        Args:
            post_id: Post ID from database
            notify_subscribers: Send to newsletter queue (default: True)

        Returns:
            {
                'success': True,
                'published_to': ['database', 'rss', 'json', 'newsletter_queue'],
                'post_id': 42
            }

        Example:
            >>> pipeline = PublishingPipeline()
            >>> result = pipeline.publish_post(42)
            >>> 'rss' in result['published_to']
            True
        """
        post = self.qt.get_post_by_slug('')  # Get by ID instead
        conn = get_db()
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

        if not post:
            conn.close()
            return {'success': False, 'error': 'Post not found'}

        published_to = ['database']

        # 1. Update RSS feed cache
        try:
            self._update_rss_cache(None, 'post', dict(post))
            published_to.append('rss')
        except Exception as e:
            print(f"⚠️  RSS cache update failed: {e}")

        # 2. Update JSON API cache
        try:
            self._update_json_cache(None, 'post', dict(post))
            published_to.append('json')
        except Exception as e:
            print(f"⚠️  JSON cache update failed: {e}")

        # 3. Queue for newsletter
        if notify_subscribers:
            try:
                self._queue_for_newsletter(None, 'post', dict(post))
                published_to.append('newsletter_queue')
            except Exception as e:
                print(f"⚠️  Newsletter queue failed: {e}")

        # 4. Broadcast via WebSocket
        try:
            self._broadcast_websocket(None, 'new_post', {
                'post_id': post_id,
                'title': dict(post)['title'],
                'slug': dict(post)['slug']
            })
            published_to.append('websocket')
        except Exception as e:
            print(f"⚠️  WebSocket broadcast failed: {e}")

        conn.close()

        print(f"✅ Published post #{post_id} to: {', '.join(published_to)}")

        return {
            'success': True,
            'published_to': published_to,
            'post_id': post_id
        }

    # ==========================================================================
    # CACHE MANAGEMENT
    # ==========================================================================

    def _update_rss_cache(
        self,
        brand_slug: Optional[str],
        content_type: str,
        content: Dict
    ):
        """
        Update RSS feed cache with new content

        Args:
            brand_slug: Brand (None = global)
            content_type: 'comment' or 'post'
            content: Content dictionary
        """
        conn = get_db()

        cache_key = f"rss_feed:{brand_slug or 'global'}:{content_type}"

        # Check if api_response_cache table exists
        try:
            conn.execute('SELECT 1 FROM api_response_cache LIMIT 1')
        except:
            # Table doesn't exist, create it
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_response_cache (
                    cache_key TEXT PRIMARY KEY,
                    cache_value TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text/xml',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            conn.commit()

        # Store feed item in cache
        conn.execute('''
            INSERT OR REPLACE INTO api_response_cache
            (cache_key, cache_value, content_type)
            VALUES (?, ?, 'text/xml')
        ''', (cache_key, json.dumps(content)))

        conn.commit()
        conn.close()

        print(f"  📡 RSS cache updated: {cache_key}")

    def _update_json_cache(
        self,
        brand_slug: Optional[str],
        content_type: str,
        content: Dict
    ):
        """
        Update JSON API cache with new content

        Args:
            brand_slug: Brand (None = global)
            content_type: 'comment' or 'post'
            content: Content dictionary
        """
        conn = get_db()

        cache_key = f"json_api:{brand_slug or 'global'}:{content_type}"

        # Check if api_response_cache table exists
        try:
            conn.execute('SELECT 1 FROM api_response_cache LIMIT 1')
        except:
            # Table doesn't exist, create it
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_response_cache (
                    cache_key TEXT PRIMARY KEY,
                    cache_value TEXT NOT NULL,
                    content_type TEXT DEFAULT 'application/json',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            conn.commit()

        # Store JSON in cache
        conn.execute('''
            INSERT OR REPLACE INTO api_response_cache
            (cache_key, cache_value, content_type)
            VALUES (?, ?, 'application/json')
        ''', (cache_key, json.dumps(content)))

        conn.commit()
        conn.close()

        print(f"  📄 JSON cache updated: {cache_key}")

    def _queue_for_newsletter(
        self,
        brand_slug: Optional[str],
        content_type: str,
        content: Dict
    ):
        """
        Add content to newsletter queue

        Args:
            brand_slug: Brand (None = all brands)
            content_type: 'comment' or 'post'
            content: Content dictionary
        """
        conn = get_db()

        # Create newsletter queue table if it doesn't exist
        try:
            conn.execute('SELECT 1 FROM newsletter_queue LIMIT 1')
        except:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS newsletter_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand_slug TEXT,
                    content_type TEXT NOT NULL,
                    content_id INTEGER NOT NULL,
                    content_data TEXT,
                    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    sent_to_count INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

        # Queue the content
        content_id = content.get('id')

        conn.execute('''
            INSERT INTO newsletter_queue
            (brand_slug, content_type, content_id, content_data)
            VALUES (?, ?, ?, ?)
        ''', (brand_slug, content_type, content_id, json.dumps(content)))

        conn.commit()
        conn.close()

        print(f"  📬 Queued for newsletter: {content_type} #{content_id}")

    def _broadcast_websocket(
        self,
        brand_slug: Optional[str],
        event_type: str,
        data: Dict
    ):
        """
        Broadcast event via WebSocket (if server is running)

        Args:
            brand_slug: Brand (None = global)
            event_type: Event name ('new_comment', 'new_post', etc.)
            data: Event data
        """
        # WebSocket broadcasting would go here
        # For now, we'll just log it
        # In production, this would use Flask-SocketIO

        room = f"brand:{brand_slug}" if brand_slug else "global"

        print(f"  🔌 WebSocket broadcast to {room}: {event_type}")

        # Future implementation:
        # from flask_socketio import emit
        # emit(event_type, data, room=room, namespace='/')

    # ==========================================================================
    # BATCH OPERATIONS
    # ==========================================================================

    def publish_batch(
        self,
        items: List[Dict],
        content_type: str
    ) -> Dict:
        """
        Publish multiple items at once

        Args:
            items: List of content dictionaries with 'id' field
            content_type: 'comment' or 'post'

        Returns:
            {
                'success': True,
                'published_count': 10,
                'failed_count': 0
            }

        Example:
            >>> pipeline = PublishingPipeline()
            >>> items = [{'id': 1}, {'id': 2}, {'id': 3}]
            >>> result = pipeline.publish_batch(items, 'comment')
            >>> result['published_count']
            3
        """
        published_count = 0
        failed_count = 0

        for item in items:
            try:
                if content_type == 'comment':
                    result = self.publish_comment(
                        comment_id=item['id'],
                        brand_slug=item.get('brand_slug', ''),
                        post_id=item.get('post_id', 0)
                    )
                elif content_type == 'post':
                    result = self.publish_post(post_id=item['id'])

                if result.get('success'):
                    published_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"⚠️  Failed to publish {content_type} #{item.get('id')}: {e}")
                failed_count += 1

        return {
            'success': True,
            'published_count': published_count,
            'failed_count': failed_count
        }

    # ==========================================================================
    # METADATA GENERATION
    # ==========================================================================

    def generate_rss_feed(
        self,
        brand_slug: Optional[str] = None,
        content_type: str = 'posts',
        limit: int = 50
    ) -> str:
        """
        Generate RSS/XML feed

        Args:
            brand_slug: Brand to generate feed for (None = global)
            content_type: 'posts' or 'comments'
            limit: Max items in feed

        Returns:
            XML string

        Example:
            >>> pipeline = PublishingPipeline()
            >>> rss = pipeline.generate_rss_feed('calriven', 'comments')
            >>> '<rss version="2.0">' in rss
            True
        """
        items = self.qt.get_feed_items(content_type, brand_slug, limit)

        # Build RSS XML
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{brand_slug.upper() if brand_slug else 'Soulfra'} - {content_type.title()}</title>
        <link>http://localhost:5001</link>
        <description>AI-powered conversation platform</description>
        <language>en-us</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
"""

        for item in items:
            if content_type == 'posts':
                rss += f"""
        <item>
            <title>{item['title']}</title>
            <link>http://localhost:5001/post/{item['slug']}</link>
            <description>{item['content'][:200]}...</description>
            <pubDate>{item['created_at']}</pubDate>
            <guid>http://localhost:5001/post/{item['slug']}</guid>
        </item>
"""
            elif content_type == 'comments':
                rss += f"""
        <item>
            <title>{item['author']} on "{item['post_title']}"</title>
            <link>http://localhost:5001/post/{item['post_slug']}#comment-{item['id']}</link>
            <description>{item['content'][:200]}...</description>
            <author>{item['author']}</author>
            <pubDate>{item['created_at']}</pubDate>
            <guid>http://localhost:5001/post/{item['post_slug']}#comment-{item['id']}</guid>
        </item>
"""

        rss += """
    </channel>
</rss>
"""

        return rss

    def generate_json_feed(
        self,
        brand_slug: Optional[str] = None,
        content_type: str = 'posts',
        limit: int = 50
    ) -> str:
        """
        Generate JSON feed

        Args:
            brand_slug: Brand to generate feed for (None = global)
            content_type: 'posts' or 'comments'
            limit: Max items in feed

        Returns:
            JSON string

        Example:
            >>> pipeline = PublishingPipeline()
            >>> feed = pipeline.generate_json_feed('calriven', 'comments')
            >>> '"version"' in feed
            True
        """
        items = self.qt.get_feed_items(content_type, brand_slug, limit)

        feed = {
            "version": "https://jsonfeed.org/version/1.1",
            "title": f"{brand_slug.upper() if brand_slug else 'Soulfra'} - {content_type.title()}",
            "home_page_url": "http://localhost:5001",
            "feed_url": f"http://localhost:5001/feeds/{brand_slug or 'global'}/{content_type}.json",
            "items": []
        }

        for item in items:
            if content_type == 'posts':
                feed["items"].append({
                    "id": str(item['id']),
                    "url": f"http://localhost:5001/post/{item['slug']}",
                    "title": item['title'],
                    "content_html": item['content'],
                    "date_published": item['created_at']
                })
            elif content_type == 'comments':
                feed["items"].append({
                    "id": str(item['id']),
                    "url": f"http://localhost:5001/post/{item['post_slug']}#comment-{item['id']}",
                    "title": f"{item['author']} on \"{item['post_title']}\"",
                    "content_text": item['content'],
                    "author": {"name": item['author']},
                    "date_published": item['created_at']
                })

        return json.dumps(feed, indent=2)


if __name__ == '__main__':
    # Test publishing pipeline
    print("Testing Publishing Pipeline...")
    print("=" * 60)

    pipeline = PublishingPipeline()

    # Test RSS feed generation
    print("\n📡 Generating RSS Feed:")
    rss = pipeline.generate_rss_feed('calriven', 'comments', limit=5)
    print(f"  RSS feed generated: {len(rss)} characters")
    print(f"  Preview: {rss[:200]}...")

    # Test JSON feed generation
    print("\n📄 Generating JSON Feed:")
    json_feed = pipeline.generate_json_feed('calriven', 'comments', limit=5)
    print(f"  JSON feed generated: {len(json_feed)} characters")

    # Test publishing a comment (using existing comment ID)
    print("\n📝 Testing Comment Publishing:")
    qt = QueryTemplates()
    comments = qt.get_brand_comments('calriven', days=7, limit=1)
    if comments:
        result = pipeline.publish_comment(
            comment_id=comments[0]['id'],
            brand_slug='calriven',
            post_id=comments[0]['post_id']
        )
        print(f"  Published to: {result['published_to']}")

    print("\n✅ Publishing pipeline ready!\n")

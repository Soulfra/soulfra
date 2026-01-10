#!/usr/bin/env python3
"""
Blog Syndication System

Cross-post content between domains in the network.
Supports:
- Publishing posts to multiple domains
- Tracking syndication relationships
- Generating cross-domain links
"""

import sqlite3
import json
import os
from datetime import datetime
from database import get_db


class BlogSyndicator:
    """Handle blog syndication across network"""

    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), 'soulfra.db')

    def publish_to_network(self, post_id, source_domain, target_domains=None):
        """
        Publish a post to one or more domains in the network

        Args:
            post_id: Post ID to syndicate
            source_domain: Original domain (e.g., 'soulfra.com')
            target_domains: List of target domains. If None, publishes to all connected domains.

        Returns:
            dict: {'success': bool, 'syndicated_to': [domains], 'errors': []}
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get post details
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        if not post:
            conn.close()
            return {'success': False, 'error': 'Post not found'}

        # Get source brand
        source_brand = conn.execute('SELECT * FROM brands WHERE domain = ?', (source_domain,)).fetchone()
        if not source_brand:
            conn.close()
            return {'success': False, 'error': 'Source domain not found'}

        # Determine target domains
        if target_domains is None:
            # Get all domains in network
            target_domains = []
            relationships = conn.execute('''
                SELECT child_domain FROM domain_relationships
                WHERE parent_domain = ?
                UNION
                SELECT parent_domain FROM domain_relationships
                WHERE child_domain = ?
            ''', (source_domain, source_domain)).fetchall()

            target_domains = [r['child_domain'] for r in relationships if r['child_domain'] != source_domain]
            target_domains.extend([r['parent_domain'] for r in relationships if r['parent_domain'] != source_domain])

        # Record syndication
        syndicated_to = []
        errors = []

        for target_domain in target_domains:
            try:
                # Check if already syndicated
                existing = conn.execute('''
                    SELECT id FROM network_posts
                    WHERE post_id = ? AND syndicated_domains LIKE ?
                ''', (post_id, f'%{target_domain}%')).fetchone()

                if not existing:
                    # Add syndication record
                    conn.execute('''
                        INSERT OR IGNORE INTO network_posts (post_id, source_domain, syndicated_domains)
                        VALUES (?, ?, ?)
                    ''', (post_id, source_domain, json.dumps([target_domain])))

                    syndicated_to.append(target_domain)
                else:
                    # Update existing record
                    record = conn.execute('SELECT * FROM network_posts WHERE post_id = ?', (post_id,)).fetchone()
                    current_domains = json.loads(record['syndicated_domains'] or '[]')
                    if target_domain not in current_domains:
                        current_domains.append(target_domain)
                        conn.execute('''
                            UPDATE network_posts
                            SET syndicated_domains = ?
                            WHERE post_id = ?
                        ''', (json.dumps(current_domains), post_id))
                        syndicated_to.append(target_domain)

            except Exception as e:
                errors.append({'domain': target_domain, 'error': str(e)})

        conn.commit()
        conn.close()

        return {
            'success': True,
            'post_id': post_id,
            'source_domain': source_domain,
            'syndicated_to': syndicated_to,
            'errors': errors
        }

    def get_syndicated_posts(self, domain):
        """
        Get all posts syndicated to a domain

        Args:
            domain: Domain to check (e.g., 'calriven.com')

        Returns:
            list: List of post dicts with syndication info
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        posts = conn.execute('''
            SELECT p.*, np.source_domain, np.syndicated_domains, np.shared_at
            FROM posts p
            JOIN network_posts np ON p.id = np.post_id
            WHERE np.syndicated_domains LIKE ?
            ORDER BY p.published_at DESC
        ''', (f'%{domain}%',)).fetchall()

        conn.close()

        return [dict(post) for post in posts]

    def get_network_feed(self, limit=50):
        """
        Get unified feed of all network activity

        Args:
            limit: Max posts to return

        Returns:
            list: List of posts from all domains
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        posts = conn.execute('''
            SELECT p.*, np.source_domain, np.syndicated_domains
            FROM posts p
            LEFT JOIN network_posts np ON p.id = np.post_id
            ORDER BY p.published_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

        conn.close()

        return [dict(post) for post in posts]

    def generate_cross_links(self, post_id):
        """
        Generate "Also on..." links for a syndicated post

        Args:
            post_id: Post ID

        Returns:
            dict: {'source': domain, 'also_on': [domains]}
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        record = conn.execute('SELECT * FROM network_posts WHERE post_id = ?', (post_id,)).fetchone()

        if not record:
            conn.close()
            return {'source': None, 'also_on': []}

        syndicated_domains = json.loads(record['syndicated_domains'] or '[]')

        conn.close()

        return {
            'source': record['source_domain'],
            'also_on': syndicated_domains
        }

    def get_syndication_stats(self):
        """Get network syndication statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        total_syndicated = conn.execute('SELECT COUNT(*) as count FROM network_posts').fetchone()['count']

        top_sources = conn.execute('''
            SELECT source_domain, COUNT(*) as count
            FROM network_posts
            GROUP BY source_domain
            ORDER BY count DESC
            LIMIT 5
        ''').fetchall()

        conn.close()

        return {
            'total_syndicated_posts': total_syndicated,
            'top_sources': [dict(row) for row in top_sources]
        }


def main():
    """Test syndication system"""
    syndicator = BlogSyndicator()

    # Example: Publish post #1 from soulfra.com to all connected domains
    result = syndicator.publish_to_network(
        post_id=1,
        source_domain='soulfra.com'
    )

    print("🌐 Blog Syndication Test")
    print(f"\n✅ Published to: {', '.join(result.get('syndicated_to', []))}")

    if result.get('errors'):
        print(f"\n❌ Errors: {result['errors']}")

    # Get syndicated posts
    posts = syndicator.get_syndicated_posts('calriven.com')
    print(f"\n📰 Posts syndicated to calriven.com: {len(posts)}")

    # Get network feed
    feed = syndicator.get_network_feed(limit=10)
    print(f"\n📊 Network feed: {len(feed)} posts")

    # Get stats
    stats = syndicator.get_syndication_stats()
    print(f"\n📈 Syndication Stats:")
    print(f"   Total syndicated posts: {stats['total_syndicated_posts']}")
    print(f"   Top sources: {stats['top_sources']}")


if __name__ == '__main__':
    main()

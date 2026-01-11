"""
Blog Network Automation Workflows
Automates content syndication, publishing, and management across domains
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Optional dependency - don't break if not installed
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("⚠️  anthropic module not installed - AI features disabled")

from database import get_db
from blog_syndication import BlogSyndicator


class WorkflowAutomation:
    """Manages automated workflows for blog network"""

    def __init__(self, claude_api_key: Optional[str] = None):
        self.db_path = os.path.join(os.path.dirname(__file__), 'soulfra.db')
        self.syndicator = BlogSyndicator()

        # Initialize Claude API if key provided and module available
        self.claude_client = None
        if HAS_ANTHROPIC:
            if claude_api_key:
                self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
            elif os.getenv('ANTHROPIC_API_KEY'):
                self.claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def auto_syndicate_new_posts(self, hours_back: int = 24) -> Dict:
        """
        Automatically syndicate posts created in last N hours
        Returns dict with results
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        posts = conn.execute('''
            SELECT p.*, b.domain, b.slug as brand_slug
            FROM posts p
            JOIN brands b ON p.brand_id = b.id
            WHERE p.published_at >= ?
            AND p.published_at IS NOT NULL
        ''', (cutoff_time,)).fetchall()

        results = {
            'processed': 0,
            'syndicated': 0,
            'errors': []
        }

        for post in posts:
            try:
                # Check if already syndicated
                existing = conn.execute('''
                    SELECT id FROM network_posts WHERE post_id = ?
                ''', (post['id'],)).fetchone()

                if not existing:
                    result = self.syndicator.publish_to_network(
                        post_id=post['id'],
                        source_domain=post['domain']
                    )
                    results['processed'] += 1
                    results['syndicated'] += len(result.get('syndicated_to', []))
            except Exception as e:
                results['errors'].append(f"Post {post['id']}: {str(e)}")

        conn.close()
        return results

    def generate_weekly_summary(self, domain: str = 'soulfra.com') -> Dict:
        """
        Generate weekly summary of network activity using Claude
        """
        if not self.claude_client:
            return {'error': 'Claude API not configured'}

        # Get week's posts
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        week_ago = datetime.now() - timedelta(days=7)
        posts = conn.execute('''
            SELECT p.*, b.domain, b.name as brand_name
            FROM posts p
            JOIN brands b ON p.brand_id = b.id
            WHERE p.published_at >= ?
            ORDER BY p.published_at DESC
        ''', (week_ago,)).fetchall()

        # Format for Claude
        posts_text = "\n\n".join([
            f"**{post['title']}** ({post['brand_name']})\n{post['content'][:200]}..."
            for post in posts
        ])

        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this week's blog posts from our network and create a concise summary highlighting key themes, insights, and connections between posts.

Posts:
{posts_text}

Provide a 2-3 paragraph summary."""
                }]
            )

            summary = message.content[0].text

            conn.close()
            return {
                'summary': summary,
                'post_count': len(posts),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            conn.close()
            return {'error': str(e)}

    def optimize_post_with_ai(self, post_id: int, task: str = 'improve_seo') -> Dict:
        """
        Use Claude to optimize a blog post
        Tasks: improve_seo, add_tags, generate_description
        """
        if not self.claude_client:
            return {'error': 'Claude API not configured'}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        if not post:
            conn.close()
            return {'error': 'Post not found'}

        prompts = {
            'improve_seo': f"""Analyze this blog post and suggest SEO improvements:

Title: {post['title']}
Content: {post['content'][:500]}...

Provide:
1. Optimized title
2. Meta description (160 chars)
3. 5-7 relevant keywords
4. Suggested headings structure""",

            'add_tags': f"""Generate relevant tags for this blog post:

Title: {post['title']}
Content: {post['content'][:500]}...

Return 5-10 tags as comma-separated values.""",

            'generate_description': f"""Write a compelling 2-sentence description for this post:

Title: {post['title']}
Content: {post['content'][:500]}..."""
        }

        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompts.get(task, prompts['improve_seo'])
                }]
            )

            result = message.content[0].text
            conn.close()

            return {
                'post_id': post_id,
                'task': task,
                'result': result,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            conn.close()
            return {'error': str(e)}

    def schedule_publish(self, post_id: int, publish_at: datetime) -> Dict:
        """
        Schedule a post for future publication
        """
        conn = sqlite3.connect(self.db_path)

        # Update post with scheduled time
        conn.execute('''
            UPDATE posts
            SET published_at = ?
            WHERE id = ?
        ''', (publish_at, post_id))

        conn.commit()
        conn.close()

        return {
            'post_id': post_id,
            'scheduled_for': publish_at.isoformat(),
            'status': 'scheduled'
        }

    def bulk_tag_posts(self, domain: str, tags: List[str]) -> Dict:
        """
        Add tags to all posts in a domain
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get brand ID
        brand = conn.execute('SELECT id FROM brands WHERE domain = ?', (domain,)).fetchone()
        if not brand:
            conn.close()
            return {'error': f'Domain {domain} not found'}

        # Get posts
        posts = conn.execute('SELECT id FROM posts WHERE brand_id = ?', (brand['id'],)).fetchall()

        tags_json = json.dumps(tags)
        updated = 0

        for post in posts:
            conn.execute('''
                UPDATE posts
                SET tags = ?
                WHERE id = ?
            ''', (tags_json, post['id']))
            updated += 1

        conn.commit()
        conn.close()

        return {
            'domain': domain,
            'posts_updated': updated,
            'tags_added': tags
        }


class WorkflowScheduler:
    """Manages scheduled workflow tasks"""

    def __init__(self):
        self.workflows = WorkflowAutomation()

    def run_daily_tasks(self):
        """Run all daily automated tasks"""
        results = {}

        # Auto-syndicate posts from last 24 hours
        results['syndication'] = self.workflows.auto_syndicate_new_posts(hours_back=24)

        return results

    def run_weekly_tasks(self):
        """Run all weekly automated tasks"""
        results = {}

        # Generate weekly summary
        results['summary'] = self.workflows.generate_weekly_summary()

        return results


# CLI interface for running workflows
if __name__ == '__main__':
    import sys

    workflows = WorkflowAutomation()

    if len(sys.argv) < 2:
        print("""
Usage: python automation_workflows.py <command> [args]

Commands:
  auto-syndicate [hours]    - Syndicate posts from last N hours (default: 24)
  weekly-summary [domain]   - Generate weekly summary (requires ANTHROPIC_API_KEY)
  optimize-post <id> [task] - Optimize post with AI (tasks: improve_seo, add_tags, generate_description)
  bulk-tag <domain> <tags>  - Add tags to all posts in domain (comma-separated)

Examples:
  python automation_workflows.py auto-syndicate 48
  python automation_workflows.py weekly-summary soulfra.com
  python automation_workflows.py optimize-post 123 improve_seo
  python automation_workflows.py bulk-tag calriven.com "AI,Engineering,Tech"
""")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'auto-syndicate':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        result = workflows.auto_syndicate_new_posts(hours_back=hours)
        print(json.dumps(result, indent=2))

    elif command == 'weekly-summary':
        domain = sys.argv[2] if len(sys.argv) > 2 else 'soulfra.com'
        result = workflows.generate_weekly_summary(domain=domain)
        print(json.dumps(result, indent=2))

    elif command == 'optimize-post':
        if len(sys.argv) < 3:
            print("Error: post_id required")
            sys.exit(1)
        post_id = int(sys.argv[2])
        task = sys.argv[3] if len(sys.argv) > 3 else 'improve_seo'
        result = workflows.optimize_post_with_ai(post_id, task)
        print(json.dumps(result, indent=2))

    elif command == 'bulk-tag':
        if len(sys.argv) < 4:
            print("Error: domain and tags required")
            sys.exit(1)
        domain = sys.argv[2]
        tags = [t.strip() for t in sys.argv[3].split(',')]
        result = workflows.bulk_tag_posts(domain, tags)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

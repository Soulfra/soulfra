#!/usr/bin/env python3
"""
Publish Everywhere - Cross-post from one database to all platforms

Usage:
    python3 publish_everywhere.py --post-id 33
    python3 publish_everywhere.py --latest
    python3 publish_everywhere.py --brand soulfra --latest

Platforms:
    - Substack (email newsletter)
    - Medium (blog)
    - Email (SMTP/SendGrid)
    - WhatsApp Business API
    - Signal (via signal-cli)
    - RSS feed
    - GitHub Pages (already working)

Configuration:
    Create .env file with API keys:

    SUBSTACK_API_KEY=your_key
    MEDIUM_API_KEY=your_key
    SENDGRID_API_KEY=your_key
    WHATSAPP_TOKEN=your_token
    SIGNAL_NUMBER=+1234567890
"""

import os
import sys
import sqlite3
import requests
import argparse
from pathlib import Path
from datetime import datetime

# Database connection
DB_PATH = Path(__file__).parent / 'soulfra.db'

class Publisher:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.results = {}

    def get_post(self, post_id=None, latest=False, brand=None):
        """Get post from database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        if latest:
            if brand:
                query = '''
                    SELECT p.*, b.name as brand_name
                    FROM posts p
                    JOIN brands b ON p.brand_id = b.id
                    WHERE b.name = ? AND p.published_at IS NOT NULL
                    ORDER BY p.published_at DESC
                    LIMIT 1
                '''
                post = conn.execute(query, (brand,)).fetchone()
            else:
                query = '''
                    SELECT p.*, b.name as brand_name
                    FROM posts p
                    JOIN brands b ON p.brand_id = b.id
                    WHERE p.published_at IS NOT NULL
                    ORDER BY p.published_at DESC
                    LIMIT 1
                '''
                post = conn.execute(query).fetchone()
        else:
            query = '''
                SELECT p.*, b.name as brand_name
                FROM posts p
                JOIN brands b ON p.brand_id = b.id
                WHERE p.id = ?
            '''
            post = conn.execute(query, (post_id,)).fetchone()

        conn.close()

        if not post:
            raise ValueError(f"Post not found (id={post_id}, latest={latest}, brand={brand})")

        return dict(post)

    def publish_to_substack(self, post):
        """Publish to Substack via API"""
        api_key = os.getenv('SUBSTACK_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'No SUBSTACK_API_KEY in environment'}

        if self.dry_run:
            return {'success': True, 'dry_run': True, 'platform': 'Substack'}

        # Substack API endpoint (this is a placeholder - check Substack docs)
        url = 'https://api.substack.com/v1/posts'

        try:
            response = requests.post(url, json={
                'title': post['title'],
                'body': post['content'],
                'status': 'published'
            }, headers={'Authorization': f'Bearer {api_key}'}, timeout=30)

            if response.status_code in [200, 201]:
                return {'success': True, 'url': response.json().get('url')}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def publish_to_medium(self, post):
        """Publish to Medium via API"""
        api_key = os.getenv('MEDIUM_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'No MEDIUM_API_KEY in environment'}

        if self.dry_run:
            return {'success': True, 'dry_run': True, 'platform': 'Medium'}

        # Get user ID first
        try:
            user_response = requests.get(
                'https://api.medium.com/v1/me',
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=10
            )
            user_id = user_response.json()['data']['id']

            # Publish post
            url = f'https://api.medium.com/v1/users/{user_id}/posts'
            response = requests.post(url, json={
                'title': post['title'],
                'contentFormat': 'markdown',
                'content': post['content'],
                'publishStatus': 'public'
            }, headers={'Authorization': f'Bearer {api_key}'}, timeout=30)

            if response.status_code in [200, 201]:
                return {'success': True, 'url': response.json()['data']['url']}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def publish_to_email(self, post):
        """Send via email (SendGrid)"""
        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'No SENDGRID_API_KEY in environment'}

        if self.dry_run:
            return {'success': True, 'dry_run': True, 'platform': 'Email'}

        # Get subscribers from database
        conn = sqlite3.connect(DB_PATH)
        subscribers = conn.execute('''
            SELECT email FROM subscribers
            WHERE active = 1 AND brand_id = ?
        ''', (post.get('brand_id'),)).fetchall()
        conn.close()

        if not subscribers:
            return {'success': False, 'error': 'No active subscribers'}

        try:
            url = 'https://api.sendgrid.com/v3/mail/send'

            # Convert content to HTML (simple markdown → HTML)
            html_content = post['content'].replace('\n', '<br>')

            response = requests.post(url, json={
                'personalizations': [{
                    'to': [{'email': sub[0]} for sub in subscribers[:1000]],  # Max 1000 per batch
                    'subject': post['title']
                }],
                'from': {'email': 'noreply@soulfra.com', 'name': post['brand_name']},
                'content': [{
                    'type': 'text/html',
                    'value': html_content
                }]
            }, headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }, timeout=30)

            if response.status_code == 202:
                return {'success': True, 'sent_to': len(subscribers)}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def publish_to_whatsapp(self, post):
        """Send to WhatsApp subscribers via Business API"""
        token = os.getenv('WHATSAPP_TOKEN')
        if not token:
            return {'success': False, 'error': 'No WHATSAPP_TOKEN in environment'}

        if self.dry_run:
            return {'success': True, 'dry_run': True, 'platform': 'WhatsApp'}

        # WhatsApp Business API endpoint
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        url = f'https://graph.facebook.com/v17.0/{phone_number_id}/messages'

        # Get WhatsApp subscribers
        conn = sqlite3.connect(DB_PATH)
        subscribers = conn.execute('''
            SELECT phone FROM subscribers
            WHERE active = 1 AND brand_id = ? AND phone IS NOT NULL
        ''', (post.get('brand_id'),)).fetchall()
        conn.close()

        if not subscribers:
            return {'success': False, 'error': 'No WhatsApp subscribers'}

        sent_count = 0
        errors = []

        for subscriber in subscribers:
            try:
                response = requests.post(url, json={
                    'messaging_product': 'whatsapp',
                    'to': subscriber[0],
                    'type': 'text',
                    'text': {
                        'body': f"{post['title']}\n\n{post['content'][:500]}...\n\nRead more: https://soulfra.com/post/{post['slug']}"
                    }
                }, headers={'Authorization': f'Bearer {token}'}, timeout=10)

                if response.status_code == 200:
                    sent_count += 1
                else:
                    errors.append(f"{subscriber[0]}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"{subscriber[0]}: {str(e)}")

        return {
            'success': sent_count > 0,
            'sent_to': sent_count,
            'errors': errors[:10]  # Limit error reporting
        }

    def publish_to_signal(self, post):
        """Send to Signal subscribers via signal-cli"""
        signal_number = os.getenv('SIGNAL_NUMBER')
        if not signal_number:
            return {'success': False, 'error': 'No SIGNAL_NUMBER in environment'}

        if self.dry_run:
            return {'success': True, 'dry_run': True, 'platform': 'Signal'}

        # Get Signal subscribers
        conn = sqlite3.connect(DB_PATH)
        subscribers = conn.execute('''
            SELECT signal_number FROM subscribers
            WHERE active = 1 AND brand_id = ? AND signal_number IS NOT NULL
        ''', (post.get('brand_id'),)).fetchall()
        conn.close()

        if not subscribers:
            return {'success': False, 'error': 'No Signal subscribers'}

        message = f"{post['title']}\n\n{post['content'][:500]}...\n\nRead more: https://soulfra.com/post/{post['slug']}"

        sent_count = 0
        errors = []

        for subscriber in subscribers:
            try:
                import subprocess
                result = subprocess.run([
                    'signal-cli',
                    '-u', signal_number,
                    'send',
                    '-m', message,
                    subscriber[0]
                ], capture_output=True, timeout=30)

                if result.returncode == 0:
                    sent_count += 1
                else:
                    errors.append(f"{subscriber[0]}: {result.stderr.decode()}")
            except Exception as e:
                errors.append(f"{subscriber[0]}: {str(e)}")

        return {
            'success': sent_count > 0,
            'sent_to': sent_count,
            'errors': errors[:10]
        }

    def publish_all(self, post_id=None, latest=False, brand=None):
        """Publish to all platforms"""
        # Get post
        post = self.get_post(post_id=post_id, latest=latest, brand=brand)

        print(f"\n📢 Publishing: {post['title']}")
        print(f"   Brand: {post['brand_name']}")
        print(f"   Published: {post['published_at']}")
        print(f"   Dry run: {self.dry_run}\n")

        platforms = {
            'Substack': self.publish_to_substack,
            'Medium': self.publish_to_medium,
            'Email': self.publish_to_email,
            'WhatsApp': self.publish_to_whatsapp,
            'Signal': self.publish_to_signal
        }

        for platform_name, publish_func in platforms.items():
            print(f"📤 Publishing to {platform_name}...", end=' ')
            result = publish_func(post)
            self.results[platform_name] = result

            if result['success']:
                if result.get('dry_run'):
                    print("✅ (dry run)")
                elif result.get('url'):
                    print(f"✅ {result['url']}")
                elif result.get('sent_to'):
                    print(f"✅ Sent to {result['sent_to']} subscribers")
                else:
                    print("✅")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")

        return self.results


def main():
    parser = argparse.ArgumentParser(description='Publish posts to all platforms')
    parser.add_argument('--post-id', type=int, help='Specific post ID to publish')
    parser.add_argument('--latest', action='store_true', help='Publish latest post')
    parser.add_argument('--brand', help='Filter by brand (with --latest)')
    parser.add_argument('--dry-run', action='store_true', help='Test without actually publishing')

    args = parser.parse_args()

    if not args.post_id and not args.latest:
        parser.error('Must specify either --post-id or --latest')

    publisher = Publisher(dry_run=args.dry_run)

    try:
        results = publisher.publish_all(
            post_id=args.post_id,
            latest=args.latest,
            brand=args.brand
        )

        # Summary
        print("\n" + "="*50)
        print("📊 PUBLISH SUMMARY")
        print("="*50)

        success_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)

        print(f"✅ Successful: {success_count}/{total_count}")
        print(f"❌ Failed: {total_count - success_count}/{total_count}")

        if args.dry_run:
            print("\n⚠️  DRY RUN - No actual publishing occurred")

        sys.exit(0 if success_count == total_count else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

"""
Mac Shortcuts Integration
Python scripts that can be called from Mac Shortcuts app for quick actions
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict
from database import get_db, add_post


class ShortcutsAPI:
    """API for Mac Shortcuts integration"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'soulfra.db')

    def quick_post(self, title: str, content: str, domain: str, username: str) -> Dict:
        """
        Create a quick blog post from Mac Shortcuts

        Usage in Shortcuts:
        1. Add "Get Text from Input" action
        2. Add "Run Shell Script" with: python3 shortcuts_integration.py quick-post --title "$1" --content "$2" --domain "$3" --username "$4"
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get user
        user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            conn.close()
            return {'error': f'User {username} not found'}

        # Get brand
        brand = conn.execute('SELECT id FROM brands WHERE domain = ?', (domain,)).fetchone()
        if not brand:
            conn.close()
            return {'error': f'Domain {domain} not found'}

        # Create slug from title
        slug = title.lower().replace(' ', '-').replace("'", '').replace('"', '')

        # Add post
        post_id = add_post(
            user_id=user['id'],
            title=title,
            slug=slug,
            content=content,
            published_at=datetime.now(),
            brand_id=brand['id']
        )

        conn.close()

        return {
            'success': True,
            'post_id': post_id,
            'title': title,
            'domain': domain,
            'url': f'http://{domain}/blog/{slug}'
        }

    def list_domains(self) -> Dict:
        """
        List all available domains

        Returns JSON array of domains for Shortcuts selection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        domains = conn.execute('SELECT domain, name, slug FROM brands ORDER BY name').fetchall()
        conn.close()

        return {
            'domains': [{'domain': d['domain'], 'name': d['name'], 'slug': d['slug']} for d in domains]
        }

    def get_recent_posts(self, limit: int = 10, domain: str = None) -> Dict:
        """
        Get recent posts for quick access

        Useful for Shortcuts menu to open recent posts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if domain:
            posts = conn.execute('''
                SELECT p.id, p.title, p.slug, p.published_at, b.domain
                FROM posts p
                JOIN brands b ON p.brand_id = b.id
                WHERE b.domain = ? AND p.published_at IS NOT NULL
                ORDER BY p.published_at DESC
                LIMIT ?
            ''', (domain, limit)).fetchall()
        else:
            posts = conn.execute('''
                SELECT p.id, p.title, p.slug, p.published_at, b.domain
                FROM posts p
                JOIN brands b ON p.brand_id = b.id
                WHERE p.published_at IS NOT NULL
                ORDER BY p.published_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        conn.close()

        return {
            'posts': [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'slug': p['slug'],
                    'domain': p['domain'],
                    'url': f"http://{p['domain']}/blog/{p['slug']}",
                    'published_at': p['published_at']
                }
                for p in posts
            ]
        }

    def start_ollama_chat(self, prompt: str) -> Dict:
        """
        Start Ollama chat session from Shortcuts

        Returns response from Ollama
        """
        try:
            import requests
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result.get('response', ''),
                    'model': 'llama3.2'
                }
            else:
                return {'error': f'Ollama error: {response.status_code}'}

        except Exception as e:
            return {'error': f'Failed to connect to Ollama: {str(e)}'}

    def open_domain_editor(self, domain: str) -> Dict:
        """
        Open domain editor in browser

        Returns URL to open
        """
        return {
            'url': f'http://localhost:5001/domains?domain={domain}',
            'domain': domain
        }


def main():
    """CLI interface for Mac Shortcuts"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Command required',
            'usage': {
                'quick-post': 'Create quick blog post',
                'list-domains': 'List all domains',
                'recent-posts': 'Get recent posts',
                'ollama-chat': 'Chat with Ollama',
                'open-editor': 'Open domain editor'
            }
        }))
        sys.exit(1)

    api = ShortcutsAPI()
    command = sys.argv[1]

    try:
        if command == 'quick-post':
            # Parse arguments
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('--title', required=True)
            parser.add_argument('--content', required=True)
            parser.add_argument('--domain', required=True)
            parser.add_argument('--username', required=True)
            args, _ = parser.parse_known_args(sys.argv[2:])

            result = api.quick_post(
                title=args.title,
                content=args.content,
                domain=args.domain,
                username=args.username
            )

        elif command == 'list-domains':
            result = api.list_domains()

        elif command == 'recent-posts':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            domain = sys.argv[3] if len(sys.argv) > 3 else None
            result = api.get_recent_posts(limit=limit, domain=domain)

        elif command == 'ollama-chat':
            if len(sys.argv) < 3:
                result = {'error': 'Prompt required'}
            else:
                prompt = ' '.join(sys.argv[2:])
                result = api.start_ollama_chat(prompt)

        elif command == 'open-editor':
            domain = sys.argv[2] if len(sys.argv) > 2 else 'soulfra.com'
            result = api.open_domain_editor(domain)

        else:
            result = {'error': f'Unknown command: {command}'}

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()

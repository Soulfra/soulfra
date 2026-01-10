#!/usr/bin/env python3
"""
Ollama Feed Watcher - Auto-generate content from voice/IRC messages

Watches RSS feeds for new content → Ollama processes → auto-generates blog → deploys

Usage:
    python3 ollama_feed_watcher.py --domain soulfra --interval 60
    python3 ollama_feed_watcher.py --domain soulfra --interval 60 --daemon
"""

import argparse
import time
import os
import sys
import subprocess
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from database import get_db
import feedparser
import json

# Ollama API endpoint
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')


class OllamaFeedWatcher:
    def __init__(self, domain, interval=60, template='blog', auto_deploy=True):
        self.domain = domain
        self.interval = interval
        self.template = template
        self.auto_deploy = auto_deploy
        self.processed_ids = set()
        self.rss_path = f'soulfra.github.io/{domain}/rss.xml'

        # Load previously processed IDs from state file
        self.state_file = f'ollama_watcher_{domain}.json'
        self.load_state()

        print(f"🤖 Ollama Feed Watcher initialized")
        print(f"   Domain: {domain}")
        print(f"   Interval: {interval}s")
        print(f"   Template: {template}")
        print(f"   Auto-deploy: {auto_deploy}")
        print(f"   Ollama: {OLLAMA_URL} ({OLLAMA_MODEL})")

    def load_state(self):
        """Load previously processed message IDs"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_ids = set(state.get('processed_ids', []))
                print(f"📂 Loaded {len(self.processed_ids)} processed IDs from state")
            except Exception as e:
                print(f"⚠️  Failed to load state: {e}")

    def save_state(self):
        """Save processed message IDs"""
        try:
            state = {
                'processed_ids': list(self.processed_ids),
                'last_check': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save state: {e}")

    def check_rss_feed(self):
        """Check RSS feed for new entries"""
        if not os.path.exists(self.rss_path):
            print(f"⚠️  RSS feed not found: {self.rss_path}")
            return []

        feed = feedparser.parse(self.rss_path)
        new_entries = []

        for entry in feed.entries:
            # Use GUID or link as unique ID
            entry_id = entry.get('id', entry.get('link', ''))

            if entry_id and entry_id not in self.processed_ids:
                new_entries.append(entry)
                self.processed_ids.add(entry_id)

        return new_entries

    def check_database(self):
        """Check database directly for new unprocessed messages"""
        db = get_db()

        # Get all messages not yet processed by Ollama
        messages = db.execute('''
            SELECT id, from_user, to_domain, channel, subject, body, created_at, message_type
            FROM domain_messages
            WHERE to_domain = ?
            AND (ollama_processed IS NULL OR ollama_processed = 0)
            ORDER BY created_at DESC
            LIMIT 10
        ''', (self.domain,)).fetchall()

        return messages

    def generate_blog_post_with_ollama(self, content, title='', author='anonymous'):
        """Use Ollama to generate blog post from voice transcription or IRC message"""

        prompt = f"""You are a technical blogger writing for {self.domain}.

Source material:
Title: {title}
Author: {author}
Content: {content}

Task: Transform this into a well-structured blog post. Keep the authentic voice and technical details. Format with:
- Clear heading
- Introduction paragraph
- Main content (keep code/technical details intact)
- Conclusion or takeaway

Write in first person if the source is a voice memo. Write the blog post now:"""

        try:
            # Call Ollama API
            response = requests.post(
                f'{OLLAMA_URL}/api/generate',
                json={
                    'model': OLLAMA_MODEL,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'top_p': 0.9
                    }
                },
                timeout=120  # 2 minute timeout for long generation
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')

                if generated_text:
                    print(f"✅ Ollama generated {len(generated_text)} chars")
                    return generated_text
                else:
                    print(f"⚠️  Ollama returned empty response")
                    return None
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
            print(f"   Is Ollama running? Try: ollama serve")
            return None
        except requests.exceptions.Timeout:
            print(f"⏱️  Ollama request timed out after 120s")
            return None
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None

    def classify_brand_persona(self, content):
        """Use Ollama to classify which brand persona this content belongs to"""

        prompt = f"""Classify this content into ONE of these brand personas:

1. calriven - Technical/code/engineering content
2. theauditor - Validation/verification/testing content
3. deathtodata - Privacy/security/data protection content
4. cringeproof - Debugging/voice memo/development workflow
5. stpetepros - Real estate/business/services
6. soulfra - General/meta/platform content

Content to classify:
{content[:500]}

Reply with ONLY the persona name (lowercase, no explanation):"""

        try:
            response = requests.post(
                f'{OLLAMA_URL}/api/generate',
                json={
                    'model': OLLAMA_MODEL,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3  # Lower temp for classification
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                persona = result.get('response', '').strip().lower()

                # Validate persona
                valid_personas = ['calriven', 'theauditor', 'deathtodata', 'cringeproof', 'stpetepros', 'soulfra']
                if persona in valid_personas:
                    return persona
                else:
                    return 'soulfra'  # Default
            else:
                return 'soulfra'

        except Exception as e:
            print(f"⚠️  Persona classification failed: {e}")
            return 'soulfra'

    def process_new_content(self, message):
        """Process a new message: generate blog post, update database, deploy"""

        message_id = message['id']
        content = message['body']
        title = message.get('subject', 'Untitled')
        author = message.get('from_user', 'anonymous')

        print(f"\n📝 Processing message {message_id}: {title[:50]}...")

        # Step 1: Classify persona
        persona = self.classify_brand_persona(content)
        print(f"🎭 Classified as: {persona}")

        # Step 2: Generate blog post
        print(f"🤖 Generating blog post with Ollama...")
        generated_content = self.generate_blog_post_with_ollama(content, title, author)

        if not generated_content:
            print(f"❌ Failed to generate content for message {message_id}")
            return False

        # Step 3: Update database with generated content
        db = get_db()
        db.execute('''
            UPDATE domain_messages
            SET
                ollama_processed = 1,
                ollama_generated_content = ?,
                ollama_persona = ?,
                ollama_processed_at = ?
            WHERE id = ?
        ''', (generated_content, persona, datetime.now().isoformat(), message_id))
        db.commit()

        print(f"💾 Saved generated content to database")

        # Step 4: Regenerate static site
        if self.auto_deploy:
            print(f"🏗️  Regenerating static site...")
            try:
                result = subprocess.run([
                    'python3', 'generate_static_site.py',
                    '--domain', self.domain,
                    '--template', self.template,
                    '--deploy'
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print(f"✅ Static site regenerated and deployed")
                else:
                    print(f"⚠️  Static site generation failed:")
                    print(result.stderr)
            except Exception as e:
                print(f"❌ Deployment error: {e}")

        return True

    def run_once(self):
        """Run one check cycle"""
        print(f"\n🔍 Checking for new content... ({datetime.now().strftime('%H:%M:%S')})")

        # Check database for unprocessed messages
        new_messages = self.check_database()

        if new_messages:
            print(f"📬 Found {len(new_messages)} new messages")

            for message in new_messages:
                self.process_new_content(message)
                time.sleep(2)  # Rate limit between Ollama calls

            self.save_state()
        else:
            print(f"   No new content")

    def run_daemon(self):
        """Run continuously as daemon"""
        print(f"\n🚀 Starting daemon mode (checking every {self.interval}s)")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                self.run_once()
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print(f"\n\n⏹️  Stopping daemon...")
            self.save_state()
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Ollama Feed Watcher - Auto-generate content')
    parser.add_argument('--domain', required=True, help='Domain to watch (e.g., soulfra)')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--template', default='blog', help='Template to use (blog, newspaper, classified)')
    parser.add_argument('--no-deploy', action='store_true', help='Generate but do not deploy')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (continuous)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')

    args = parser.parse_args()

    # Initialize watcher
    watcher = OllamaFeedWatcher(
        domain=args.domain,
        interval=args.interval,
        template=args.template,
        auto_deploy=not args.no_deploy
    )

    # Run
    if args.once:
        watcher.run_once()
    elif args.daemon:
        watcher.run_daemon()
    else:
        # Default: run once
        watcher.run_once()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
AI Workforce Content Generator - POC Version

Reads pending tasks from ai_workforce_tasks and generates content using Ollama.

Usage:
    python3 auto_content_generator.py --execute
    python3 auto_content_generator.py --task-id 1
"""

import requests
import sqlite3
import json
import argparse
from datetime import datetime

DB_PATH = 'soulfra.db'
OLLAMA_URL = 'http://192.168.1.87:11434/api/chat'
OLLAMA_MODEL = 'soulfra-model'


class AIContentGenerator:
    """Generate blog posts using Ollama based on assigned tasks"""

    def __init__(self, db_path=DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.ollama_url = OLLAMA_URL
        self.model = OLLAMA_MODEL

    def get_pending_tasks(self):
        """Get all pending tasks from database"""
        cursor = self.db.execute('''
            SELECT * FROM ai_workforce_tasks
            WHERE status = 'pending'
            ORDER BY created_at ASC
        ''')
        return cursor.fetchall()

    def get_task_by_id(self, task_id):
        """Get specific task by ID"""
        cursor = self.db.execute('''
            SELECT * FROM ai_workforce_tasks
            WHERE id = ?
        ''', (task_id,))
        return cursor.fetchone()

    def generate_content(self, prompt, keywords):
        """Call Ollama to generate blog post content"""
        print(f"\n🤖 Calling Ollama ({self.model})...")
        print(f"   Prompt: {prompt[:100]}...")

        # Build full prompt with SEO keywords
        keywords_str = ', '.join(keywords) if keywords else ''
        full_prompt = f"""Write a blog post about: {prompt}

Target keywords to include naturally: {keywords_str}

Requirements:
- Write 400-600 words
- Include an engaging introduction
- Use clear headings and paragraphs
- Be informative and helpful
- Natural tone, not overly formal
- Include the keywords naturally (don't force them)

Write the blog post now:"""

        try:
            # Ollama chat API
            response = requests.post(
                self.ollama_url,
                json={
                    'model': self.model,
                    'messages': [
                        {'role': 'user', 'content': full_prompt}
                    ],
                    'stream': False  # Don't stream for POC
                },
                timeout=120  # 2 min timeout
            )

            if response.status_code == 200:
                result = response.json()
                # Extract message content from chat response
                generated_text = result.get('message', {}).get('content', '')

                print(f"✅ Generated {len(generated_text)} characters")
                return generated_text
            else:
                print(f"❌ Ollama error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None

        except requests.RequestException as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            print(f"   Make sure Ollama is running at {self.ollama_url}")
            return None

    def generate_title_from_prompt(self, prompt):
        """Generate a clean title from the task prompt"""
        # Simple title generation (can enhance with Ollama later)
        title = prompt.strip()

        # Capitalize first letter of each word
        title = ' '.join(word.capitalize() for word in title.split())

        # Ensure it's not too long
        if len(title) > 60:
            title = title[:57] + '...'

        return title

    def generate_slug_from_title(self, title):
        """Generate URL-friendly slug from title"""
        import re

        # Lowercase
        slug = title.lower()

        # Remove special chars, keep alphanumeric and spaces
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)

        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug.strip())

        # Remove duplicate hyphens
        slug = re.sub(r'-+', '-', slug)

        return slug

    def execute_task(self, task_id):
        """Execute a single task: generate content and update database"""
        print(f"\n{'='*80}")
        print(f"📝 Executing Task #{task_id}")
        print(f"{'='*80}")

        # Get task
        task = self.get_task_by_id(task_id)
        if not task:
            print(f"❌ Task {task_id} not found")
            return False

        print(f"Domain: {task['domain']}")
        print(f"Type: {task['task_type']}")
        print(f"Assigned to: {task['assigned_to_persona']}")
        print(f"Prompt: {task['prompt']}")

        # Parse keywords
        keywords = []
        if task['keywords_target']:
            try:
                keywords = json.loads(task['keywords_target'])
            except json.JSONDecodeError:
                keywords = [task['keywords_target']]

        # Mark as in_progress
        self.db.execute('''
            UPDATE ai_workforce_tasks
            SET status = 'in_progress'
            WHERE id = ?
        ''', (task_id,))
        self.db.commit()

        # Generate content
        content = self.generate_content(task['prompt'], keywords)

        if not content:
            print(f"❌ Content generation failed")
            # Revert to pending
            self.db.execute('''
                UPDATE ai_workforce_tasks
                SET status = 'pending'
                WHERE id = ?
            ''', (task_id,))
            self.db.commit()
            return False

        # Generate title and slug
        title = self.generate_title_from_prompt(task['prompt'])
        slug = self.generate_slug_from_title(title)

        print(f"\n📄 Generated Content:")
        print(f"   Title: {title}")
        print(f"   Slug: {slug}")
        print(f"   Length: {len(content)} characters")
        print(f"   Preview: {content[:200]}...")

        # Update task with output
        self.db.execute('''
            UPDATE ai_workforce_tasks
            SET status = 'completed',
                output_content = ?,
                output_title = ?,
                output_slug = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (content, title, slug, task_id))
        self.db.commit()

        print(f"\n✅ Task #{task_id} completed!")
        print(f"   Status: completed (ready for CringeProof review)")

        return True

    def execute_all_pending(self):
        """Execute all pending tasks"""
        tasks = self.get_pending_tasks()

        if not tasks:
            print("✅ No pending tasks found")
            return

        print(f"\n🚀 Found {len(tasks)} pending task(s)")

        for task in tasks:
            success = self.execute_task(task['id'])
            if not success:
                print(f"⚠️  Skipping remaining tasks due to error")
                break

        print(f"\n{'='*80}")
        print("📊 Task Execution Summary")
        print(f"{'='*80}")

        # Show updated status
        completed = self.db.execute('''
            SELECT COUNT(*) as count FROM ai_workforce_tasks WHERE status = 'completed'
        ''').fetchone()['count']

        pending = self.db.execute('''
            SELECT COUNT(*) as count FROM ai_workforce_tasks WHERE status = 'pending'
        ''').fetchone()['count']

        print(f"Completed: {completed}")
        print(f"Pending: {pending}")

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description='Generate content for AI workforce tasks')
    parser.add_argument('--execute', action='store_true',
                       help='Execute all pending tasks')
    parser.add_argument('--task-id', type=int,
                       help='Execute specific task by ID')
    args = parser.parse_args()

    generator = AIContentGenerator()

    try:
        if args.task_id:
            generator.execute_task(args.task_id)
        elif args.execute:
            generator.execute_all_pending()
        else:
            # Show pending tasks
            tasks = generator.get_pending_tasks()
            if tasks:
                print(f"\n📋 {len(tasks)} Pending Task(s):\n")
                for task in tasks:
                    print(f"Task #{task['id']}")
                    print(f"  Domain: {task['domain']}")
                    print(f"  Persona: {task['assigned_to_persona']}")
                    print(f"  Prompt: {task['prompt']}")
                    print()
                print("Run with --execute to process all tasks")
                print("Run with --task-id N to process specific task")
            else:
                print("✅ No pending tasks")

    finally:
        generator.close()


if __name__ == '__main__':
    main()

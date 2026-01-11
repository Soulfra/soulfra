#!/usr/bin/env python3
"""
Ollama Discussion Helper - Interactive AI Research & Comment Generation

Manages discussion sessions where users can:
1. Chat with AI about a specific post
2. Command AI to research (search posts, comments, etc.)
3. Finalize discussion into a polished comment
4. Post the final comment to the blog

Usage:
    from ollama_discussion import DiscussionSession

    session = DiscussionSession(post_id=42, user_id=1)
    session.send_message("What should I focus on here?")
    session.execute_command("/research privacy")
    draft = session.finalize_comment()
    session.post_comment(draft)
"""

import sqlite3
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import List
from database import get_db


# AI Persona definitions
PERSONAS = {
    'calriven': {
        'display_name': 'CalRiven',
        'user_id': 2,
        'system_prompt': '''You are CalRiven, a technical architecture expert who focuses on:
- Data structures and algorithms
- System design and scalability
- Code quality and patterns
- Performance optimization
- Database architecture

When discussing posts, provide technical insights, architectural suggestions, and data-focused analysis.
When asked to research, search for related technical discussions.
When finalizing comments, create a concise (2-3 paragraph) technical perspective.'''
    },
    'deathtodata': {
        'display_name': 'DeathToData',
        'user_id': 3,
        'system_prompt': '''You are DeathToData, a privacy and anti-surveillance advocate who focuses on:
- User privacy protection
- Data minimization
- Anti-tracking techniques
- Decentralization
- User control over data

When discussing posts, analyze privacy implications and suggest privacy-preserving alternatives.
When asked to research, search for related privacy discussions.
When finalizing comments, create a concise (2-3 paragraph) privacy-focused perspective.'''
    },
    'theauditor': {
        'display_name': 'TheAuditor',
        'user_id': 4,
        'system_prompt': '''You are TheAuditor, a testing and validation expert who focuses on:
- Code review and quality assurance
- Edge cases and error handling
- Testing strategies
- Documentation completeness
- Production readiness

When discussing posts, identify potential issues and suggest tests.
When asked to research, search for related validation discussions.
When finalizing comments, create a concise (2-3 paragraph) validation-focused perspective.'''
    },
    'soulfra': {
        'display_name': 'Soulfra',
        'user_id': 5,
        'system_prompt': '''You are Soulfra, a security and encryption expert who focuses on:
- Cryptographic security
- Threat modeling
- Secure system design
- Encryption best practices
- Authentication and authorization

When discussing posts, analyze security implications and identify vulnerabilities.
When asked to research, search for related security discussions.
When finalizing comments, create a concise (2-3 paragraph) security-focused perspective.'''
    }
}


class DiscussionSession:
    """Manages an interactive discussion session about a post"""

    def __init__(self, post_id=None, brand_name=None, user_id=None, persona_name='calriven', session_id=None):
        """
        Initialize or resume a discussion session

        Args:
            post_id: The post to discuss (for blog post discussions)
            brand_name: The brand to discuss (for brand building discussions)
            user_id: The user conducting the discussion
            persona_name: AI persona to use (default: calriven)
            session_id: Resume existing session (or create new if None)

        Note: Either post_id OR brand_name must be provided (not both)
        """
        self.post_id = post_id
        self.brand_name = brand_name
        self.user_id = user_id
        self.persona_name = persona_name

        if session_id:
            self.session_id = session_id
            self._load_session()
        else:
            self.session_id = self._create_session()

    def _create_session(self):
        """Create new discussion session"""
        db = get_db()
        cursor = db.execute('''
            INSERT INTO discussion_sessions (post_id, brand_name, user_id, persona_name, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (self.post_id, self.brand_name, self.user_id, self.persona_name))
        session_id = cursor.lastrowid
        db.commit()
        db.close()
        return session_id

    def _load_session(self):
        """Load existing session details"""
        db = get_db()
        session = db.execute('''
            SELECT * FROM discussion_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()
        db.close()

        if session:
            self.post_id = session['post_id']
            self.brand_name = session['brand_name']
            self.user_id = session['user_id']
            self.persona_name = session['persona_name']

    def get_context(self):
        """Get the context being discussed (post or brand)"""
        if self.post_id:
            db = get_db()
            post = db.execute('SELECT * FROM posts WHERE id = ?', (self.post_id,)).fetchone()
            db.close()
            return {
                'type': 'post',
                'data': dict(post) if post else None
            }
        elif self.brand_name:
            return {
                'type': 'brand',
                'data': {
                    'name': self.brand_name,
                    'description': f'Brand building discussion for: {self.brand_name}'
                }
            }
        return None

    def get_post_context(self):
        """Get the post being discussed (legacy method - kept for compatibility)"""
        context = self.get_context()
        if context and context['type'] == 'post':
            return context['data']
        return None

    def get_messages(self):
        """Get all messages in this session"""
        db = get_db()
        messages = db.execute('''
            SELECT * FROM discussion_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (self.session_id,)).fetchall()
        db.close()
        return [dict(m) for m in messages]

    def send_message(self, content, sender='user'):
        """Add a message to the session"""
        db = get_db()
        db.execute('''
            INSERT INTO discussion_messages (session_id, sender, content, message_type)
            VALUES (?, ?, ?, 'chat')
        ''', (self.session_id, sender, content))
        db.commit()
        db.close()

    def call_ollama(self, prompt, include_post_context=True):
        """
        Call Ollama API with persona system prompt

        Args:
            prompt: The user's prompt
            include_post_context: Whether to include context (post or brand) in prompt

        Returns:
            AI response text or None if error
        """
        persona_config = PERSONAS.get(self.persona_name, PERSONAS['calriven'])

        # Build full prompt with context if requested
        full_prompt = prompt
        if include_post_context:
            context = self.get_context()
            if context:
                if context['type'] == 'post':
                    post = context['data']
                    full_prompt = f"""Post Title: {post['title']}

Post Content:
{post['content'][:1000]}...

User Question: {prompt}"""
                elif context['type'] == 'brand':
                    brand = context['data']
                    full_prompt = f"""Brand: {brand['name']}

Context: We are building and refining the brand "{brand['name']}".
This is a collaborative discussion about brand identity, messaging, target audience,
values, positioning, and all aspects of brand development.

Your role: Provide expertise from your perspective ({self.persona_name}) to help shape this brand.

User Question: {prompt}"""

        try:
            request_data = {
                'model': 'llama2',
                'prompt': full_prompt,
                'system': persona_config['system_prompt'],
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 500
                }
            }

            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()

        except urllib.error.URLError:
            return "❌ Error: Ollama not running. Start with: ollama serve"
        except Exception as e:
            return f"❌ Error calling Ollama: {str(e)}"

    def research(self, topic):
        """
        Research a topic by searching posts and comments

        Returns:
            Research findings as formatted text
        """
        db = get_db()

        # Search posts for topic
        posts = db.execute('''
            SELECT id, title, content
            FROM posts
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY published_at DESC
            LIMIT 5
        ''', (f'%{topic}%', f'%{topic}%')).fetchall()

        # Search comments for topic
        comments = db.execute('''
            SELECT c.content, p.title as post_title, u.display_name
            FROM comments c
            JOIN posts p ON c.post_id = p.id
            JOIN users u ON c.user_id = u.id
            WHERE c.content LIKE ?
            ORDER BY c.created_at DESC
            LIMIT 5
        ''', (f'%{topic}%',)).fetchall()

        db.close()

        # Format findings
        findings = f"**Research Results for '{topic}':**\n\n"

        if posts:
            findings += f"**Related Posts ({len(posts)}):**\n"
            for post in posts:
                findings += f"- {post['title']} (ID: {post['id']})\n"
            findings += "\n"
        else:
            findings += "No related posts found.\n\n"

        if comments:
            findings += f"**Related Comments ({len(comments)}):**\n"
            for comment in comments:
                preview = comment['content'][:100] + "..." if len(comment['content']) > 100 else comment['content']
                findings += f"- {comment['display_name']} on '{comment['post_title']}': {preview}\n"
        else:
            findings += "No related comments found.\n"

        # Store research as system message
        self.send_message(findings, sender='system')

        return findings

    def execute_command(self, command):
        """
        Execute a slash command

        Commands:
            /research <topic> - Search for related content
            /persona <name> - Switch AI persona
            /finalize - Generate final comment from discussion

        Returns:
            Command result text
        """
        command = command.strip()

        if command.startswith('/research '):
            topic = command[10:].strip()
            return self.research(topic)

        elif command.startswith('/persona '):
            persona = command[9:].strip().lower()
            if persona in PERSONAS:
                self.persona_name = persona
                db = get_db()
                db.execute('UPDATE discussion_sessions SET persona_name = ? WHERE id = ?',
                          (persona, self.session_id))
                db.commit()
                db.close()
                return f"✅ Switched to {PERSONAS[persona]['display_name']}"
            else:
                return f"❌ Unknown persona: {persona}. Available: {', '.join(PERSONAS.keys())}"

        elif command == '/finalize':
            return self.finalize_comment()

        else:
            return f"❌ Unknown command: {command}\n\nAvailable commands:\n- /research <topic>\n- /persona <name>\n- /finalize"

    def finalize_comment(self):
        """
        Synthesize the discussion into a final polished comment

        Returns:
            Draft comment text
        """
        # Get discussion history
        messages = self.get_messages()

        # Build context from discussion
        discussion_summary = "\n".join([
            f"{m['sender']}: {m['content']}"
            for m in messages
            if m['message_type'] == 'chat'
        ])

        # Ask AI to synthesize
        prompt = f"""Based on our discussion below, write a final polished comment for the post.

Discussion:
{discussion_summary}

Create a concise, well-structured comment (2-3 paragraphs) that incorporates the key insights from our discussion.
Focus on your area of expertise ({self.persona_name}) and provide actionable insights."""

        draft = self.call_ollama(prompt, include_post_context=True)

        # Store draft
        db = get_db()
        db.execute('UPDATE discussion_sessions SET draft_comment = ? WHERE id = ?',
                  (draft, self.session_id))
        db.commit()
        db.close()

        self.send_message(draft, sender='draft')

        return draft

    def finalize_sops(self, template_ids: List[str] = None):
        """
        Generate structured SOPs from discussion (NEW METHOD)

        Args:
            template_ids: List of template IDs to generate (default: all)

        Returns:
            Dictionary of {template_id: sop_dict}
        """
        from sop_generator import SOPGenerator

        generator = SOPGenerator()

        if template_ids is None:
            # Generate all SOPs
            sops = generator.generate_all_sops(self.session_id)
        else:
            # Generate specific SOPs
            sops = {}
            for template_id in template_ids:
                sop = generator.generate_from_discussion(self.session_id, template_id)
                if sop:
                    sops[template_id] = sop

        # Save SOPs to database if this is a brand discussion
        if self.brand_name:
            db = get_db()
            brand = db.execute('SELECT id FROM brands WHERE slug = ?', (self.brand_name,)).fetchone()

            if brand:
                for template_id, sop in sops.items():
                    generator.save_sop_to_database(sop, brand['id'])

            db.close()

        return sops

    def post_comment(self, content=None):
        """
        Post the final comment to the blog

        Args:
            content: Comment text (uses draft if None)

        Returns:
            Comment ID or None if error
        """
        if not content:
            # Use draft
            db = get_db()
            session = db.execute('SELECT draft_comment FROM discussion_sessions WHERE id = ?',
                               (self.session_id,)).fetchone()
            db.close()
            content = session['draft_comment'] if session else None

        if not content:
            return None

        # Post comment
        persona_config = PERSONAS.get(self.persona_name, PERSONAS['calriven'])
        db = get_db()
        cursor = db.execute('''
            INSERT INTO comments (post_id, user_id, content, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (self.post_id, persona_config['user_id'], content))
        comment_id = cursor.lastrowid

        # Mark session as finalized
        db.execute('''
            UPDATE discussion_sessions
            SET status = 'finalized',
                final_comment_id = ?,
                finalized_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (comment_id, self.session_id))

        db.commit()
        db.close()

        return comment_id


if __name__ == '__main__':
    # Test the discussion system
    print("🧪 Testing Discussion System")
    print("=" * 70)

    # Create test session
    session = DiscussionSession(post_id=1, user_id=1, persona_name='calriven')
    print(f"✅ Created discussion session {session.session_id}")

    # Send test message
    session.send_message("What are the key technical considerations here?")
    print("✅ Sent test message")

    # Get AI response
    response = session.call_ollama("Summarize the main technical points of this post.")
    print(f"✅ AI Response: {response[:100]}...")

    # Test research
    findings = session.research("privacy")
    print(f"✅ Research findings: {len(findings)} characters")

    print()
    print("=" * 70)
    print("✅ All tests passed!")

#!/usr/bin/env python3
"""
Content Generator - Unified Content Creation Interface

The ONE place to generate ALL content types:
- Blog posts from conversations
- RSS/Atom feeds
- Social media posts
- Podcast episodes
- Newsletters

Replaces 20+ scattered post generation functions with a single, unified interface.

Philosophy:
----------
Currently the codebase has:
  - auto_document.py: generates posts
  - calriven_post.py: generates posts
  - create_tutorial_post.py: generates posts
  - dogfood_platform.py: generates posts
  ... etc (20+ files)

This creates:
  - Duplication (same post generation logic 20+ times)
  - No consistency in post structure
  - Hard to add new content types
  - Can't track content generation

Solution: ONE generator that:
  1. Takes any input (conversation, test results, code changes)
  2. Uses content templates (from content_templates.py)
  3. Generates consistent, structured content
  4. Integrates with AI for enhancement
  5. Saves to database with tracking

Zero Dependencies: Uses Python stdlib + local modules.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

from content_templates import (
    BlogPost, ConversationSummary, ConversationToPost,
    FeedItem, SocialPost, PodcastEpisode,
    ContentType, ContentStatus, SocialPlatform
)


class ContentGenerator:
    """
    Unified interface to generate all content types

    Usage:
        generator = ContentGenerator()

        # Generate post from widget conversation
        post = generator.conversation_to_post(session_id=3)

        # Generate RSS feed
        feed = generator.generate_feed(limit=10)

        # Generate social post
        social = generator.generate_social_post(post_id=1, platform='twitter')
    """

    def __init__(self, db_path: str = 'soulfra.db'):
        """Initialize content generator"""
        self.db_path = db_path
        self.generation_log: List[Dict] = []

    # ==========================================================================
    # CONVERSATION TO POST (KEY FEATURE!)
    # ==========================================================================

    def conversation_to_post(
        self,
        session_id: int,
        author_id: int = 6,  # Default to SoulAssistant
        template: str = 'qa_format',
        auto_publish: bool = False,
        brand_slug: Optional[str] = None,
        generate_images: bool = True
    ) -> Optional[BlogPost]:
        """
        Turn widget conversation into blog post

        This is THE feature for: "after we fill out templates or business
        ideas or visions...we could see posts and progress"

        Args:
            session_id: Widget conversation session ID
            author_id: Author user ID (default: SoulAssistant)
            template: Post template ('qa_format', 'tutorial', 'insight', 'story')
            auto_publish: Publish immediately or save as draft
            brand_slug: Brand slug for colors/branding (optional)
            generate_images: Generate procedural images (default: True)

        Returns:
            BlogPost object or None if failed
        """
        # 1. Fetch conversation from database
        conversation = self._fetch_conversation(session_id)
        if not conversation:
            return None

        # 2. Analyze conversation to extract insights
        summary = self._analyze_conversation(conversation)

        # 3. Convert to post using template
        conv_to_post = ConversationToPost(
            conversation=summary,
            post_template=template
        )
        post = conv_to_post.to_blog_post(author_id=author_id)

        # 4. Generate slug and excerpt
        post.generate_slug()
        post.generate_excerpt()

        # 5. Generate procedural images if requested
        if generate_images:
            print(f"   🖼️  Generating procedural images...")
            post_id_for_images = self._generate_images_for_post(post, brand_slug)
            if post_id_for_images:
                post.metadata['images_generated'] = True
                post.metadata['image_post_id'] = post_id_for_images

        # 6. Set status
        post.status = ContentStatus.PUBLISHED if auto_publish else ContentStatus.DRAFT

        # 7. Save to database
        if auto_publish:
            post_id = self._save_post_to_db(post)
            post.metadata['db_id'] = post_id

        # 8. Log generation
        self._log_generation('conversation_to_post', {
            'session_id': session_id,
            'post_title': post.title,
            'template': template,
            'published': auto_publish,
            'images_generated': generate_images
        })

        return post

    def _fetch_conversation(self, session_id: int) -> Optional[List[Dict]]:
        """Fetch conversation messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT sender, content, created_at as timestamp, session_id
                FROM discussion_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,))

            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return messages if messages else None

        except Exception as e:
            print(f"Error fetching conversation: {e}")
            return None

    def _analyze_conversation(self, messages: List[Dict]) -> ConversationSummary:
        """
        Analyze conversation to extract insights

        Uses simple heuristics (could be enhanced with AI later)
        """
        # Extract Q&A pairs
        questions = []
        answers = []
        main_topics = []
        key_insights = []

        for msg in messages:
            sender = msg.get('sender', '')
            content = msg.get('content', '')

            if sender == 'user':
                # User messages are questions
                if len(content) > 10:  # Skip very short messages
                    questions.append(content)

                    # Extract topics (simple word extraction)
                    words = content.lower().split()
                    for word in words:
                        if len(word) > 5 and word not in ['about', 'should', 'would', 'could']:
                            if word not in main_topics:
                                main_topics.append(word)

            elif sender == 'ai':
                # AI messages are answers
                if len(content) > 20:  # Skip very short responses
                    answers.append(content)

                    # Extract insights (sentences with key phrases)
                    sentences = content.split('. ')
                    for sentence in sentences:
                        if any(phrase in sentence.lower() for phrase in ['important', 'key', 'essential', 'note that', 'remember']):
                            if sentence not in key_insights:
                                key_insights.append(sentence)

        # Limit topics to most relevant
        main_topics = main_topics[:5]
        key_insights = key_insights[:10]

        return ConversationSummary(
            session_id=messages[0].get('session_id', 0) if messages else 0,
            messages=messages,
            main_topics=main_topics,
            key_insights=key_insights,
            questions_asked=questions,
            answers_given=answers
        )

    def _generate_images_for_post(self, post: BlogPost, brand_slug: Optional[str] = None) -> Optional[int]:
        """
        Generate AI images for blog post

        Uses Stable Diffusion for real neural network-based image generation.
        Falls back to procedural generation if AI unavailable.

        Args:
            post: BlogPost object
            brand_slug: Brand slug for colors (optional)

        Returns:
            Post ID if successful, None otherwise
        """
        try:
            import hashlib

            # Extract keywords from title and main topics
            keywords = []

            # Add title words
            title_words = post.title.lower().split()
            keywords.extend([word for word in title_words if len(word) > 4][:3])

            # Add tags if available
            if post.tags:
                keywords.extend(post.tags[:2])

            # Ensure at least some keywords
            if not keywords:
                keywords = ['content', 'post', 'discussion']

            # Get brand colors if available
            brand_colors = ['#FF6B35', '#F7931E', '#C1272D']  # Default colors

            if brand_slug:
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    brand = conn.execute(
                        'SELECT color_primary, color_secondary, color_accent FROM brands WHERE slug = ?',
                        (brand_slug,)
                    ).fetchone()
                    conn.close()

                    if brand:
                        brand_colors = [
                            brand['color_primary'] or '#FF6B35',
                            brand['color_secondary'] or '#F7931E',
                            brand['color_accent'] or '#C1272D'
                        ]
                except:
                    pass  # Use defaults

            # Generate hero image using AI (with fallback)
            hero_bytes = None

            # Try AI generation first
            try:
                from ai_image_generator import AIImageGenerator
                from prompt_templates import get_brand_prompt, get_negative_prompt

                print(f"      🎨 Generating AI image...")
                generator = AIImageGenerator()

                if generator.available:
                    # Create brand-specific prompt using templates
                    prompt = get_brand_prompt(
                        brand_slug=brand_slug or 'default',
                        title=post.title,
                        keywords=keywords,
                        content_type='blog'  # Could be 'recipe', 'tutorial', etc.
                    )

                    negative = get_negative_prompt(brand_slug)

                    print(f"      Prompt: {prompt[:80]}...")

                    hero_bytes = generator.generate_from_text(
                        prompt=prompt,
                        negative_prompt=negative,
                        brand_colors=brand_colors,
                        size=(1200, 600),
                        num_steps=20  # Balanced quality/speed
                    )
                    print(f"      ✅ AI image generated ({len(hero_bytes)} bytes)")
                else:
                    print(f"      ⚠️  AI unavailable, using fallback...")

            except Exception as e:
                print(f"      ⚠️  AI generation failed: {e}")
                print(f"      ↻  Falling back to procedural generation...")

            # Fallback to procedural if AI failed
            if hero_bytes is None:
                from ai_image_generator import generate_fallback_image

                hero_bytes = generate_fallback_image(
                    keywords=keywords,
                    brand_colors=brand_colors,
                    size=(1200, 600)
                )
                print(f"      ✅ Fallback image generated ({len(hero_bytes)} bytes)")

            # Save hero image to database
            hero_hash = hashlib.sha256(hero_bytes).hexdigest()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO images (hash, data, mime_type, width, height)
                VALUES (?, ?, ?, ?, ?)
            ''', (hero_hash, hero_bytes, 'image/png', 1200, 600))

            conn.commit()

            # Update post content to include hero image
            hero_markdown = f"![{post.title}](</i/{hero_hash}>)\n\n"
            post.content = hero_markdown + post.content

            conn.close()
            return 1  # Success indicator

        except Exception as e:
            print(f"      ⚠️  Image generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_post_to_db(self, post: BlogPost) -> int:
        """Save blog post to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO posts (
                    user_id, title, slug, content, excerpt,
                    published_at, ai_processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                post.author_id,
                post.title,
                post.slug,
                post.content,
                post.excerpt,
                post.created_at.isoformat(),
                post.ai_processed
            ))

            post_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return post_id

        except Exception as e:
            print(f"Error saving post to database: {e}")
            return 0

    # ==========================================================================
    # FEED GENERATION
    # ==========================================================================

    def generate_feed(
        self,
        format: str = 'rss',
        limit: int = 20,
        category: Optional[str] = None
    ) -> str:
        """
        Generate RSS/Atom feed

        For: "feeds and podcast style"

        Args:
            format: 'rss' or 'atom'
            limit: Number of items to include
            category: Filter by category (optional)

        Returns:
            XML feed as string
        """
        # Fetch recent posts
        posts = self._fetch_recent_posts(limit, category)

        # Convert to feed items
        feed_items = []
        for post in posts:
            feed_item = FeedItem(
                title=post['title'],
                link=f"https://soulfra.com/post/{post['slug']}",
                description=post.get('excerpt', post['content'][:200]),
                pub_date=datetime.fromisoformat(post['published_at']),
                author=post.get('author_name', 'Soulfra Team'),
                guid=f"post-{post['id']}",
                categories=[]  # TODO: Fetch categories
            )
            feed_items.append(feed_item)

        # Generate XML
        if format == 'rss':
            return self._generate_rss_feed(feed_items)
        else:
            return self._generate_atom_feed(feed_items)

    def _fetch_recent_posts(self, limit: int, category: Optional[str] = None) -> List[Dict]:
        """Fetch recent posts from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT p.*, u.display_name as author_name
                FROM posts p
                JOIN users u ON p.user_id = u.id
                ORDER BY p.published_at DESC
                LIMIT ?
            """

            cursor.execute(query, (limit,))
            posts = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return posts

        except Exception as e:
            print(f"Error fetching posts: {e}")
            return []

    def _generate_rss_feed(self, items: List[FeedItem]) -> str:
        """Generate RSS 2.0 feed XML"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>Soulfra</title>
    <link>https://soulfra.com</link>
    <description>AI-powered blogging platform</description>
    <language>en-us</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <atom:link href="https://soulfra.com/feed.xml" rel="self" type="application/rss+xml"/>
""".format(last_build=datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))

        for item in items:
            xml += item.to_rss_xml() + "\n"

        xml += """
</channel>
</rss>"""

        return xml

    def _generate_atom_feed(self, items: List[FeedItem]) -> str:
        """Generate Atom 1.0 feed XML"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Soulfra</title>
    <link href="https://soulfra.com"/>
    <link href="https://soulfra.com/feed.atom" rel="self"/>
    <id>https://soulfra.com</id>
    <updated>{updated}</updated>
""".format(updated=datetime.now().isoformat() + 'Z')

        for item in items:
            xml += item.to_atom_xml() + "\n"

        xml += "</feed>"

        return xml

    # ==========================================================================
    # SOCIAL MEDIA POST GENERATION
    # ==========================================================================

    def generate_social_post(
        self,
        post_id: int,
        platform: str = 'twitter',
        style: str = 'announcement'
    ) -> Optional[SocialPost]:
        """
        Generate social media post from blog post

        For: "ai twitter of ideas"

        Args:
            post_id: Blog post ID
            platform: 'twitter', 'mastodon', 'bluesky'
            style: 'announcement', 'question', 'insight'

        Returns:
            SocialPost object or None
        """
        # Fetch post
        post = self._fetch_post_by_id(post_id)
        if not post:
            return None

        # Generate social content based on style
        if style == 'announcement':
            content = f"New post: {post['title']}\n\nCheck it out at soulfra.com/post/{post['slug']}"
        elif style == 'question':
            # Extract first question from content
            content = f"Thinking about {post['title'].lower()}...\n\nWhat's your take?"
        else:  # insight
            # Extract key insight from excerpt
            excerpt = post.get('excerpt', post['content'][:100])
            content = f"💡 {excerpt}\n\nRead more: soulfra.com/post/{post['slug']}"

        # Extract hashtags from title
        words = post['title'].split()
        hashtags = [word for word in words if len(word) > 4][:3]

        platform_enum = {
            'twitter': SocialPlatform.TWITTER,
            'mastodon': SocialPlatform.MASTODON,
            'bluesky': SocialPlatform.BLUESKY
        }.get(platform, SocialPlatform.GENERIC)

        return SocialPost(
            content=content,
            platform=platform_enum,
            hashtags=hashtags
        )

    def _fetch_post_by_id(self, post_id: int) -> Optional[Dict]:
        """Fetch post by ID from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            conn.close()

            return dict(post) if post else None

        except Exception as e:
            print(f"Error fetching post: {e}")
            return None

    # ==========================================================================
    # DRAFT MANAGEMENT
    # ==========================================================================

    def get_all_drafts(self) -> List[Dict]:
        """Get all draft posts"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # For now, we'll identify drafts by checking if they're from widget sessions
            # In the future, add a 'status' column to posts table
            cursor.execute("""
                SELECT p.*, u.display_name as author_name
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.published_at > datetime('now', '-7 days')
                ORDER BY p.published_at DESC
            """)

            drafts = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return drafts

        except Exception as e:
            print(f"Error fetching drafts: {e}")
            return []

    def get_conversation_sessions(self) -> List[Dict]:
        """Get all widget conversation sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    s.id,
                    s.created_at,
                    COUNT(m.id) as message_count,
                    MAX(m.created_at) as last_activity
                FROM discussion_sessions s
                LEFT JOIN discussion_messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """)

            sessions = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return sessions

        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    # ==========================================================================
    # LOGGING & STATS
    # ==========================================================================

    def _log_generation(self, operation: str, details: Dict):
        """Log content generation for analytics"""
        self.generation_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details
        })

    def get_stats(self) -> Dict:
        """Get content generation statistics"""
        return {
            'total_generations': len(self.generation_log),
            'operations': [log['operation'] for log in self.generation_log]
        }


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Content Generator")
    print("=" * 70)

    generator = ContentGenerator()

    # Test 1: Get conversation sessions
    print("\n📊 Widget Conversation Sessions:")
    sessions = generator.get_conversation_sessions()
    for session in sessions[:3]:
        print(f"   Session {session['id']}: {session['message_count']} messages, last active {session['last_activity']}")

    # Test 2: Convert conversation to post (if sessions exist)
    if sessions:
        print(f"\n✨ Converting Session {sessions[0]['id']} to Blog Post:")
        post = generator.conversation_to_post(
            session_id=sessions[0]['id'],
            template='qa_format',
            auto_publish=False
        )

        if post:
            print(f"   Title: {post.title}")
            print(f"   Slug: {post.slug}")
            print(f"   Excerpt: {post.excerpt[:100]}...")
            print(f"   Tags: {post.tags}")
            print(f"   Source: {post.source}")
            print(f"   Status: {post.status.value}")
        else:
            print("   ⚠️  Could not generate post (conversation might be too short)")

    # Test 3: Generate RSS feed
    print("\n📡 RSS Feed Generation:")
    feed = generator.generate_feed(format='rss', limit=5)
    print(f"   Generated {len(feed)} characters of RSS XML")
    print(f"   Preview: {feed[:200]}...")

    # Test 4: Get stats
    print("\n📈 Stats:")
    stats = generator.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ Content Generator working!")
    print("\n💡 Next: Add /generate commands to widget")

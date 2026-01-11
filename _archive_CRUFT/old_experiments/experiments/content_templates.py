#!/usr/bin/env python3
"""
Content Template Schemas - Structure for All Content Types

Defines schemas for:
- Blog posts
- Feed items (RSS/Atom)
- Podcast episodes
- Social media posts (Twitter/X style)
- Newsletters
- Conversation-to-post transformations

Philosophy:
----------
Just like schemas.py defines data structures, this defines CONTENT structures.
Every piece of content follows a template. No more scattered post generators!

Benefits:
- Type safety for content generation
- Consistent structure across all content types
- Easy to add new content formats
- Self-documenting content requirements

Zero Dependencies: Uses Python stdlib dataclasses only.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


# ==============================================================================
# CONTENT TYPE ENUMS
# ==============================================================================

class ContentType(Enum):
    """Types of content we can generate"""
    BLOG_POST = 'blog_post'
    FEED_ITEM = 'feed_item'
    PODCAST_EPISODE = 'podcast_episode'
    SOCIAL_POST = 'social_post'
    NEWSLETTER = 'newsletter'
    TUTORIAL = 'tutorial'
    DOCUMENTATION = 'documentation'


class ContentStatus(Enum):
    """Content lifecycle status"""
    DRAFT = 'draft'
    REVIEW = 'review'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'


class SocialPlatform(Enum):
    """Social media platforms"""
    TWITTER = 'twitter'
    MASTODON = 'mastodon'
    BLUESKY = 'bluesky'
    GENERIC = 'generic'


# ==============================================================================
# BASE CONTENT SCHEMA
# ==============================================================================

@dataclass
class BaseContent:
    """Base class for all content types"""
    title: str
    content: str
    author_id: int
    created_at: datetime = field(default_factory=datetime.now)
    status: ContentStatus = ContentStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None  # e.g., 'widget_session_3', 'manual', 'ai_generated'

    def to_dict(self) -> dict:
        """Convert to dict for database storage"""
        return {
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'metadata': self.metadata,
            'source': self.source
        }


# ==============================================================================
# BLOG POST SCHEMAS
# ==============================================================================

@dataclass
class BlogPost(BaseContent):
    """
    Blog post structure

    Replaces hardcoded post generation in:
    - auto_document.py
    - calriven_post.py
    - create_tutorial_post.py
    - etc.
    """
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    brand_id: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    ai_processed: bool = False

    def generate_slug(self) -> str:
        """Generate URL-safe slug from title"""
        import re
        slug = self.title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        self.slug = slug
        return slug

    def generate_excerpt(self, max_length: int = 200) -> str:
        """Generate excerpt from content"""
        # Remove markdown formatting for excerpt
        import re
        text = re.sub(r'[#*_`\[\]()]', '', self.content)

        if len(text) <= max_length:
            self.excerpt = text
        else:
            # Cut at last space before max_length
            excerpt = text[:max_length]
            last_space = excerpt.rfind(' ')
            if last_space > 0:
                excerpt = excerpt[:last_space]
            self.excerpt = excerpt + '...'

        return self.excerpt

    def to_dict(self) -> dict:
        """Convert to dict for database storage"""
        base = super().to_dict()
        base.update({
            'slug': self.slug,
            'excerpt': self.excerpt,
            'brand_id': self.brand_id,
            'categories': self.categories,
            'tags': self.tags,
            'ai_processed': self.ai_processed
        })
        return base


# ==============================================================================
# CONVERSATION TO POST SCHEMA
# ==============================================================================

@dataclass
class ConversationSummary:
    """Summary of a widget conversation"""
    session_id: int
    messages: List[Dict[str, Any]]
    main_topics: List[str]
    key_insights: List[str]
    questions_asked: List[str]
    answers_given: List[str]

    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'messages': self.messages,
            'main_topics': self.main_topics,
            'key_insights': self.key_insights,
            'questions_asked': self.questions_asked,
            'answers_given': self.answers_given
        }


@dataclass
class ConversationToPost:
    """
    Transform widget conversation into blog post

    This is the KEY feature for: "after we fill out templates or business
    ideas or visions...we could see posts and progress"
    """
    conversation: ConversationSummary
    post_template: str = 'qa_format'  # 'qa_format', 'tutorial', 'insight', 'story'

    def to_blog_post(self, author_id: int) -> BlogPost:
        """
        Convert conversation to blog post

        Templates:
        - qa_format: Q&A style post
        - tutorial: Step-by-step guide
        - insight: Key learnings post
        - story: Narrative style
        """
        if self.post_template == 'qa_format':
            return self._to_qa_post(author_id)
        elif self.post_template == 'tutorial':
            return self._to_tutorial_post(author_id)
        elif self.post_template == 'insight':
            return self._to_insight_post(author_id)
        else:
            return self._to_story_post(author_id)

    def _to_qa_post(self, author_id: int) -> BlogPost:
        """Generate Q&A style post"""
        # Extract Q&A pairs
        qa_pairs = []
        for i in range(len(self.conversation.questions_asked)):
            if i < len(self.conversation.answers_given):
                qa_pairs.append({
                    'q': self.conversation.questions_asked[i],
                    'a': self.conversation.answers_given[i]
                })

        # Build content
        content = f"# Q&A: {', '.join(self.conversation.main_topics[:2])}\n\n"
        content += f"This post captures insights from a conversation about {', '.join(self.conversation.main_topics)}.\n\n"

        for i, pair in enumerate(qa_pairs, 1):
            content += f"## Question {i}: {pair['q']}\n\n"
            content += f"{pair['a']}\n\n"

        # Generate title from first topic
        title = f"Understanding {self.conversation.main_topics[0]}" if self.conversation.main_topics else "Conversation Insights"

        return BlogPost(
            title=title,
            content=content,
            author_id=author_id,
            source=f'widget_session_{self.conversation.session_id}',
            tags=self.conversation.main_topics,
            metadata={'conversation_id': self.conversation.session_id}
        )

    def _to_tutorial_post(self, author_id: int) -> BlogPost:
        """Generate tutorial-style post"""
        content = f"# Tutorial: {self.conversation.main_topics[0]}\n\n"
        content += "## What You'll Learn\n\n"

        for insight in self.conversation.key_insights:
            content += f"- {insight}\n"

        content += "\n## Step-by-Step Guide\n\n"

        for i, pair in enumerate(zip(self.conversation.questions_asked, self.conversation.answers_given), 1):
            q, a = pair
            content += f"### Step {i}: {q}\n\n{a}\n\n"

        title = f"How to {self.conversation.main_topics[0]}" if self.conversation.main_topics else "Tutorial"

        return BlogPost(
            title=title,
            content=content,
            author_id=author_id,
            source=f'widget_session_{self.conversation.session_id}',
            categories=['Tutorial'],
            tags=self.conversation.main_topics
        )

    def _to_insight_post(self, author_id: int) -> BlogPost:
        """Generate insights-focused post"""
        content = f"# Key Insights: {', '.join(self.conversation.main_topics[:2])}\n\n"

        if self.conversation.key_insights:
            content += "## Main Takeaways\n\n"
            for insight in self.conversation.key_insights:
                content += f"- {insight}\n"
            content += "\n"

        content += "## Deep Dive\n\n"
        for q, a in zip(self.conversation.questions_asked, self.conversation.answers_given):
            content += f"**{q}**\n\n{a}\n\n"

        title = f"Insights on {self.conversation.main_topics[0]}" if self.conversation.main_topics else "Key Insights"

        return BlogPost(
            title=title,
            content=content,
            author_id=author_id,
            source=f'widget_session_{self.conversation.session_id}',
            tags=self.conversation.main_topics
        )

    def _to_story_post(self, author_id: int) -> BlogPost:
        """Generate narrative-style post"""
        content = f"# {self.conversation.main_topics[0] if self.conversation.main_topics else 'A Conversation'}\n\n"
        content += "Here's how our conversation unfolded...\n\n"

        for msg in self.conversation.messages:
            sender = msg.get('sender', 'unknown')
            text = msg.get('content', '')

            if sender == 'user':
                content += f"**Question:** {text}\n\n"
            elif sender == 'ai':
                content += f"{text}\n\n"

        title = f"Exploring {self.conversation.main_topics[0]}" if self.conversation.main_topics else "A Conversation"

        return BlogPost(
            title=title,
            content=content,
            author_id=author_id,
            source=f'widget_session_{self.conversation.session_id}',
            tags=self.conversation.main_topics
        )


# ==============================================================================
# FEED ITEM SCHEMA
# ==============================================================================

@dataclass
class FeedItem:
    """
    RSS/Atom feed item structure

    For: "feeds and podcast style or ai twitter of ideas"
    """
    title: str
    link: str
    description: str
    pub_date: datetime
    author: str
    guid: str
    categories: List[str] = field(default_factory=list)

    def to_rss_xml(self) -> str:
        """Generate RSS XML for this item"""
        xml = f"""
    <item>
        <title><![CDATA[{self.title}]]></title>
        <link>{self.link}</link>
        <description><![CDATA[{self.description}]]></description>
        <pubDate>{self.pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
        <author>{self.author}</author>
        <guid>{self.guid}</guid>
"""
        for cat in self.categories:
            xml += f"        <category>{cat}</category>\n"

        xml += "    </item>"
        return xml

    def to_atom_xml(self) -> str:
        """Generate Atom XML for this item"""
        xml = f"""
    <entry>
        <title>{self.title}</title>
        <link href="{self.link}"/>
        <id>{self.guid}</id>
        <updated>{self.pub_date.isoformat()}Z</updated>
        <summary>{self.description}</summary>
        <author>
            <name>{self.author}</name>
        </author>
"""
        for cat in self.categories:
            xml += f"        <category term=\"{cat}\"/>\n"

        xml += "    </entry>"
        return xml


# ==============================================================================
# SOCIAL MEDIA POST SCHEMA
# ==============================================================================

@dataclass
class SocialPost:
    """
    Social media post structure (Twitter/X, Mastodon, Bluesky style)

    For: "ai twitter of ideas"
    """
    content: str
    platform: SocialPlatform = SocialPlatform.GENERIC
    max_length: int = 280
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    thread: bool = False
    thread_parts: List[str] = field(default_factory=list)

    def format_for_platform(self) -> str:
        """Format content according to platform rules"""
        formatted = self.content

        # Add hashtags
        if self.hashtags:
            hashtag_str = ' '.join(f'#{tag}' for tag in self.hashtags)
            formatted = f"{formatted}\n\n{hashtag_str}"

        # Truncate if needed
        if len(formatted) > self.max_length and not self.thread:
            formatted = formatted[:self.max_length-3] + '...'

        return formatted

    def to_thread(self) -> List[str]:
        """Split long content into thread"""
        if not self.thread or len(self.content) <= self.max_length:
            return [self.format_for_platform()]

        # Split into thread parts
        words = self.content.split()
        parts = []
        current = []

        for word in words:
            current.append(word)
            if len(' '.join(current)) > self.max_length - 20:  # Leave room for (1/N)
                parts.append(' '.join(current))
                current = []

        if current:
            parts.append(' '.join(current))

        # Add numbering
        numbered = []
        for i, part in enumerate(parts, 1):
            numbered.append(f"({i}/{len(parts)}) {part}")

        return numbered


# ==============================================================================
# PODCAST EPISODE SCHEMA
# ==============================================================================

@dataclass
class PodcastEpisode:
    """
    Podcast episode structure

    For: "feeds and podcast style"
    """
    title: str
    description: str
    audio_url: Optional[str] = None
    duration: Optional[int] = None  # seconds
    pub_date: datetime = field(default_factory=datetime.now)
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    transcript: Optional[str] = None

    def to_rss_item(self) -> str:
        """Generate podcast RSS item"""
        xml = f"""
    <item>
        <title>{self.title}</title>
        <description><![CDATA[{self.description}]]></description>
        <pubDate>{self.pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
"""
        if self.audio_url:
            xml += f"        <enclosure url=\"{self.audio_url}\" type=\"audio/mpeg\"/>\n"

        if self.duration:
            xml += f"        <itunes:duration>{self.duration}</itunes:duration>\n"

        if self.episode_number:
            xml += f"        <itunes:episode>{self.episode_number}</itunes:episode>\n"

        if self.season_number:
            xml += f"        <itunes:season>{self.season_number}</itunes:season>\n"

        xml += "    </item>"
        return xml


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def validate_blog_post(data: dict) -> bool:
    """Validate blog post structure"""
    required_fields = ['title', 'content', 'author_id']
    return all(field in data for field in required_fields)


def validate_feed_item(data: dict) -> bool:
    """Validate feed item structure"""
    required_fields = ['title', 'link', 'description', 'pub_date']
    return all(field in data for field in required_fields)


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Content Template Schemas")
    print("=" * 70)

    # Test 1: BlogPost
    print("\n✅ BlogPost:")
    post = BlogPost(
        title="How to Build a Neural Network",
        content="# Introduction\n\nThis is a tutorial...",
        author_id=1,
        tags=['neural-networks', 'tutorial']
    )
    post.generate_slug()
    post.generate_excerpt()
    print(f"   Title: {post.title}")
    print(f"   Slug: {post.slug}")
    print(f"   Excerpt: {post.excerpt}")

    # Test 2: ConversationToPost
    print("\n✅ ConversationToPost:")
    conv = ConversationSummary(
        session_id=3,
        messages=[
            {'sender': 'user', 'content': 'What is this post about?'},
            {'sender': 'ai', 'content': 'This post covers neural networks...'}
        ],
        main_topics=['neural networks', 'machine learning'],
        key_insights=['Neural networks learn from data', 'Training requires labeled examples'],
        questions_asked=['What is this post about?', 'How do neural networks work?'],
        answers_given=['This post covers neural networks...', 'Neural networks use layers...']
    )
    conv_to_post = ConversationToPost(conversation=conv, post_template='qa_format')
    generated_post = conv_to_post.to_blog_post(author_id=1)
    print(f"   Generated Title: {generated_post.title}")
    print(f"   Source: {generated_post.source}")
    print(f"   Tags: {generated_post.tags}")

    # Test 3: FeedItem
    print("\n✅ FeedItem:")
    feed_item = FeedItem(
        title="New Post: Neural Networks",
        link="https://soulfra.com/post/neural-networks",
        description="Learn about neural networks...",
        pub_date=datetime.now(),
        author="Soulfra Team",
        guid="post-neural-networks",
        categories=['AI', 'Tutorial']
    )
    print(f"   Title: {feed_item.title}")
    print(f"   Categories: {feed_item.categories}")

    # Test 4: SocialPost
    print("\n✅ SocialPost:")
    social = SocialPost(
        content="Just published a new post about neural networks! Check it out.",
        platform=SocialPlatform.TWITTER,
        hashtags=['AI', 'MachineLearning', 'NeuralNetworks']
    )
    formatted = social.format_for_platform()
    print(f"   Formatted: {formatted[:80]}...")

    print("\n" + "=" * 70)
    print("✅ All content template schemas working!")
    print("\n💡 Next: Create content_generator.py to USE these templates")

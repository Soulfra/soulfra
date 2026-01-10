#!/usr/bin/env python3
"""
Whitepaper Generator

Automatically generates a cohesive whitepaper from existing posts using AI synthesis.

Usage:
    python3 generate_whitepaper.py
    python3 generate_whitepaper.py --brand calriven
    python3 generate_whitepaper.py --output custom-whitepaper.md
"""

import sqlite3
import json
import requests
from datetime import datetime
from pathlib import Path
import argparse


class WhitepaperGenerator:
    """Generate whitepaper from posts using Ollama"""

    def __init__(self, brand_filter=None):
        """
        Initialize generator

        Args:
            brand_filter: Optional brand slug to filter posts (e.g., 'calriven')
        """
        self.brand_filter = brand_filter
        self.db_path = Path(__file__).parent / 'soulfra.db'
        self.ollama_url = 'http://localhost:11434/api/generate'

    def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_posts(self):
        """
        Fetch posts from database

        Returns:
            List of post dictionaries
        """
        db = self.get_db()

        if self.brand_filter:
            # Fetch posts for specific brand
            query = '''
                SELECT p.title, p.content, p.excerpt, p.published_at,
                       b.name as brand_name, b.personality
                FROM posts p
                LEFT JOIN post_brands pb ON p.id = pb.post_id
                LEFT JOIN brands b ON pb.brand_id = b.id
                WHERE b.slug = ?
                ORDER BY p.published_at DESC
            '''
            cursor = db.execute(query, (self.brand_filter,))
        else:
            # Fetch all posts
            query = '''
                SELECT p.title, p.content, p.excerpt, p.published_at
                FROM posts p
                ORDER BY p.published_at DESC
            '''
            cursor = db.execute(query)

        posts = [dict(row) for row in cursor.fetchall()]
        db.close()

        return posts

    def extract_key_themes(self, posts):
        """
        Extract key themes from posts using simple keyword frequency

        Args:
            posts: List of post dictionaries

        Returns:
            List of (theme, count) tuples
        """
        # Common words to ignore
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }

        word_freq = {}

        for post in posts:
            content = (post.get('title', '') + ' ' + post.get('content', '')).lower()
            words = content.split()

            for word in words:
                # Clean word (remove punctuation)
                clean_word = ''.join(c for c in word if c.isalnum())

                if len(clean_word) > 4 and clean_word not in stopwords:
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1

        # Sort by frequency
        themes = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return themes[:10]  # Top 10 themes

    def synthesize_with_ollama(self, posts, themes):
        """
        Use Ollama to synthesize posts into cohesive whitepaper

        Args:
            posts: List of post dictionaries
            themes: List of (theme, count) tuples

        Returns:
            Generated whitepaper content
        """
        # Build context from posts
        posts_summary = []
        for i, post in enumerate(posts[:10], 1):  # Limit to 10 most recent
            posts_summary.append(f"{i}. {post['title']}: {post.get('excerpt', 'No excerpt')}")

        themes_str = ', '.join([theme for theme, _ in themes])

        prompt = f"""You are writing a professional whitepaper based on a collection of blog posts.

Key themes identified: {themes_str}

Recent posts:
{chr(10).join(posts_summary)}

Write a comprehensive whitepaper that:
1. Introduces the platform's core philosophy
2. Explains the key technical concepts (conversational blogging, neural networks, brand theming)
3. Describes the architecture (widget, database, AI integration)
4. Outlines use cases and benefits
5. Concludes with future vision

The whitepaper should be professional, cohesive, and around 1000-1500 words.
Use markdown formatting with headers, bullet points, and emphasis where appropriate.

Title: Soulfra Platform Whitepaper
"""

        try:
            # Call Ollama API
            response = requests.post(
                self.ollama_url,
                json={
                    'model': 'llama2',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                print(f"⚠️  Ollama API returned status {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            print("⚠️  Ollama not running. Install with: curl https://ollama.ai/install.sh | sh")
            return None
        except Exception as e:
            print(f"⚠️  Error calling Ollama: {e}")
            return None

    def generate_manual_whitepaper(self, posts, themes):
        """
        Generate whitepaper manually (without Ollama)

        Args:
            posts: List of post dictionaries
            themes: List of (theme, count) tuples

        Returns:
            Generated whitepaper content
        """
        brand_name = posts[0].get('brand_name', 'Soulfra') if self.brand_filter and posts else 'Soulfra'

        whitepaper = f"""# {brand_name} Platform Whitepaper

**Generated:** {datetime.now().strftime('%B %d, %Y')}

---

## Abstract

{brand_name} is a self-documenting platform that transforms natural conversations into structured content. By combining conversational AI, neural network classification, and exportable brand themes, {brand_name} enables users to build and distribute content ecosystems without traditional content management overhead.

---

## 1. Introduction

### The Problem

Traditional content platforms force creators into rigid workflows:
- Write posts in markdown editors
- Manually categorize and tag content
- Export/import is complex and lossy
- Platform lock-in prevents distribution

### The Solution

{brand_name} inverts this model:
- **Conversations become content** - Talk to an AI widget, generate blog posts
- **AI organizes automatically** - Neural networks classify and tag posts
- **Brands are portable** - Export entire themes as ZIP packages
- **Self-hosted and open** - Python, SQLite, no external dependencies

---

## 2. Core Architecture

### Widget-First Design

The {brand_name} widget (💬 purple bubble) is the primary interface:

```
USER CONVERSATION → AI PROCESSING → BLOG POST
```

**Key Commands:**
- `/generate post` - Create blog post from conversation
- `/research <topic>` - Search and analyze content
- `/qr <text>` - Generate QR codes
- `/dnd quests` - Interactive D&D gameplay (bonus feature)

### Database-Centric Storage

All content lives in SQLite database:
- **posts** - Blog posts and content
- **post_brands** - Neural network classifications
- **brands** - Brand configurations (colors, personality, tone)
- **discussion_sessions** - Widget conversation history

**Pattern:** Filesystem from database
- Binary blobs as file contents
- Tags as filenames
- Metadata as inode data
- Transparent compression

---

## 3. Neural Network Classification

### How It Works

When posts are created, neural networks automatically classify them by brand:

1. **Keyword Extraction** - Scan content for brand-specific terms
2. **Confidence Scoring** - Each brand gets score (0.0 - 1.0)
3. **Assignment** - Posts linked to brands above threshold
4. **Storage** - Relationships saved in `post_brands` table

### Example Classification

**Post:** "Building privacy-focused QR tracking without surveillance"

**Results:**
- DeathToData: 0.75 (privacy, surveillance keywords)
- Calriven: 0.65 (QR, tracking, technical keywords)
- Soulfra: 0.50 (platform philosophy keywords)

**Assigned to:** DeathToData (highest confidence)

---

## 4. Brand Theme System

### Export/Import Architecture

Brands can be exported as standalone ZIP packages:

**Export:**
```bash
python3 brand_theme_manager.py export deathtodata
```

**Package Contents:**
- `brand.yaml` - Colors, personality, tone
- `metadata.json` - Brand configuration
- `images/` - Logos, banners, avatars
- `stories/` - All brand posts as markdown
- `ml_models/` - Trained wordmaps and emoji patterns
- `LICENSE.txt` - Licensing information
- `README.md` - Installation instructions

**Import:**
```bash
python3 brand_theme_manager.py import deathtodata-theme.zip
```

Result: Standalone branded site with all content and theming intact.

---

## 5. Key Themes in {brand_name}

Based on analysis of {len(posts)} posts, the platform focuses on:

"""

        # Add themes
        for theme, count in themes[:5]:
            whitepaper += f"- **{theme.capitalize()}** - Mentioned {count} times across posts\n"

        whitepaper += f"""

---

## 6. Use Cases

### 1. Conversational Blogging

**Traditional:**
1. Open text editor
2. Write markdown
3. Add frontmatter
4. Git commit
5. Deploy

**{brand_name}:**
1. Open widget
2. Have conversation
3. Type `/generate post`
4. Done!

### 2. Multi-Brand Content Ecosystems

Create multiple branded sites from one platform:
- **Soulfra** - Platform philosophy and architecture
- **DeathToData** - Privacy and anti-surveillance
- **Calriven** - Technical AI and ML content

Each brand exports as standalone site with unique theming.

### 3. Self-Documenting Development

The platform documents itself through use:
- Conversations become blog posts
- Posts auto-classify by topic
- Neural networks learn brand voices
- Documentation emerges organically

---

## 7. Technical Stack

**Backend:**
- Python 3.x (Flask web framework)
- SQLite database
- Ollama (local AI inference)

**Frontend:**
- Vanilla JavaScript
- No framework dependencies
- Server-side templates (Jinja2)

**AI/ML:**
- Ollama llama2 model
- Custom neural network classifiers
- Keyword-based brand matching

**Distribution:**
- Binary protocol for compression
- ZIP package export/import
- Self-contained deployment

---

## 8. Key Features

### ✅ Already Working

1. **Blog Generator** - Widget → conversation → post
2. **Neural Network Classifier** - Auto-categorize posts by brand
3. **Brand Theme Export** - ZIP packages for distribution
4. **QR Code Generation** - Create scannable codes for content
5. **Research Assistant** - Search and analyze posts
6. **D&D Game System** - Interactive gameplay (bonus)

### 🔄 In Development

1. **Whitepaper Auto-Generation** - Synthesize docs from posts
2. **Enhanced About Pages** - Dynamic platform documentation
3. **Multiplayer D&D** - 6-8 person party gameplay

---

## 9. Philosophy

### Self-Documenting

The platform documents itself through natural use. Every conversation, every generated post, every classification becomes part of the documentation.

### Exportable

No platform lock-in. Export any brand as standalone package. Share, distribute, fork freely.

### AI-Assisted

AI handles organization, classification, and content generation. Humans focus on ideas and decisions.

### Open Source

Everything is open, self-hosted, and modifiable. Python stdlib when possible, minimal dependencies always.

---

## 10. Future Vision

### Near Term (1-3 months)

- Enhanced neural network models
- Multi-language support
- Advanced brand theming (CSS variables, typography)
- Collaborative editing

### Long Term (6-12 months)

- Federated brand network (link multiple {brand_name} instances)
- Plugin system for custom commands
- Mobile app (widget on phone)
- Blockchain integration for content provenance

---

## 11. Getting Started

### Installation

```bash
git clone https://github.com/soulfra/soulfra-simple
cd soulfra-simple
python3 app.py
```

Visit: http://localhost:5001

### First Steps

1. Click purple 💬 bubble
2. Chat: "I want to write about privacy"
3. Widget responds with ideas
4. You: `/generate post`
5. Post created and saved!

### Next Steps

- Classify posts: `python3 classify_posts_by_brand.py`
- Export brand: `python3 brand_theme_manager.py export <brand>`
- Explore docs: `README.md`, `BLOG_GENERATOR_GUIDE.md`

---

## 12. Conclusion

{brand_name} represents a new paradigm in content creation:
- **Conversation over composition** - Talk, don't type
- **AI organization** - Classify, don't categorize manually
- **Exportable brands** - Distribute, don't lock in
- **Self-documentation** - Emerge, don't write specs

The platform is fully operational and ready for use. Your conversations become content. Your content becomes brands. Your brands become ecosystems.

**Start talking. Start building.**

---

## Appendix A: Post Topics

The following posts contributed to this whitepaper:

"""

        # Add post list
        for i, post in enumerate(posts[:15], 1):
            whitepaper += f"{i}. **{post['title']}**\n"
            if post.get('excerpt'):
                whitepaper += f"   {post['excerpt']}\n"
            whitepaper += "\n"

        if len(posts) > 15:
            whitepaper += f"*...and {len(posts) - 15} more posts*\n"

        whitepaper += f"""
---

## Appendix B: Quick Reference

**Widget Commands:**
- `/generate post [template]` - Create blog post
- `/research <topic>` - Search content
- `/qr <text>` - Generate QR code
- `/neural <text>` - Neural network prediction
- `/dnd quests` - List D&D quests

**Scripts:**
- `python3 app.py` - Start web server
- `python3 classify_posts_by_brand.py` - Classify posts
- `python3 brand_theme_manager.py export <brand>` - Export brand
- `python3 generate_whitepaper.py` - Generate this whitepaper

**Docs:**
- `HOW_IT_ALL_CONNECTS.md` - System overview
- `BLOG_GENERATOR_GUIDE.md` - Blog generator usage
- `READY_TO_USE.md` - D&D and integration guide

---

**{brand_name} Platform Whitepaper**
Version 1.0 | {datetime.now().strftime('%Y-%m-%d')}
"""

        return whitepaper

    def generate(self, output_path=None):
        """
        Generate whitepaper

        Args:
            output_path: Optional output file path (default: WHITEPAPER.md)

        Returns:
            Path to generated whitepaper
        """
        print(f"\n📄 Generating Whitepaper{' for ' + self.brand_filter if self.brand_filter else ''}\n")

        # Fetch posts
        print("1️⃣  Fetching posts from database...")
        posts = self.fetch_posts()

        if not posts:
            print("❌ No posts found!")
            return None

        print(f"   ✅ Found {len(posts)} posts")

        # Extract themes
        print("2️⃣  Extracting key themes...")
        themes = self.extract_key_themes(posts)
        print(f"   ✅ Identified {len(themes)} key themes")
        for theme, count in themes[:5]:
            print(f"      • {theme}: {count} mentions")

        # Try Ollama synthesis
        print("3️⃣  Synthesizing with AI...")
        content = self.synthesize_with_ollama(posts, themes)

        if content:
            print("   ✅ AI synthesis complete")
        else:
            print("   ⚠️  AI unavailable, using template generation")
            content = self.generate_manual_whitepaper(posts, themes)

        # Determine output path
        if output_path is None:
            if self.brand_filter:
                output_path = f"{self.brand_filter.upper()}_WHITEPAPER.md"
            else:
                output_path = "WHITEPAPER.md"

        output_file = Path(output_path)

        # Write to file
        print(f"4️⃣  Writing to {output_file}...")
        output_file.write_text(content)
        print(f"   ✅ Whitepaper written ({len(content)} chars)")

        # Also save as post to database
        print("5️⃣  Saving as blog post...")
        self.save_as_post(content)

        print(f"\n✅ Whitepaper generated successfully!")
        print(f"   File: {output_file.absolute()}")
        print(f"   View at: http://localhost:5001/admin (check drafts)")

        return str(output_file.absolute())

    def save_as_post(self, content):
        """
        Save whitepaper as blog post

        Args:
            content: Whitepaper content
        """
        db = self.get_db()

        title = f"{''.join(self.brand_filter.split('-')).capitalize() if self.brand_filter else 'Soulfra'} Platform Whitepaper"
        slug = f"{''.join(self.brand_filter.split('-')) if self.brand_filter else 'soulfra'}-whitepaper"
        excerpt = "Comprehensive whitepaper auto-generated from platform posts and documentation."

        # Check if whitepaper post already exists
        existing = db.execute('SELECT id FROM posts WHERE slug = ?', (slug,)).fetchone()

        if existing:
            # Update existing
            db.execute('''
                UPDATE posts SET content = ?, updated_at = ?
                WHERE slug = ?
            ''', (content, datetime.now(), slug))
            print(f"   ✅ Updated existing whitepaper post")
        else:
            # Create new (user_id = 1 for system-generated posts)
            db.execute('''
                INSERT INTO posts (title, slug, content, excerpt, published_at, user_id)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (title, slug, content, excerpt, datetime.now()))
            print(f"   ✅ Created new whitepaper post")

        db.commit()
        db.close()


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate whitepaper from posts')
    parser.add_argument('--brand', help='Filter posts by brand slug (e.g., calriven)')
    parser.add_argument('--output', help='Output file path (default: WHITEPAPER.md)')

    args = parser.parse_args()

    generator = WhitepaperGenerator(brand_filter=args.brand)
    generator.generate(output_path=args.output)

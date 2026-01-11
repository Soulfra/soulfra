#!/usr/bin/env python3
"""
Dogfooding Script: Document Soulfra Development Using Soulfra

Creates posts documenting the work we just did:
- reputation.py (Perfect Bits system)
- trending_detector.py (trending detection)
- slogan_generator.py (human-driven slogans)
- merch_generator.py (SVG design generation)
- Template fixes (post.html, style.css)

This demonstrates the core vision: "The platform IS the documentation of how it was built."
"""

import sqlite3
from datetime import datetime
from database import get_db, add_post
from db_helpers import add_tag_to_post
from reputation import award_bits
from reasoning_engine import ReasoningEngine

# Post content
POSTS = [
    {
        'title': 'Building the Perfect Bits Reputation System',
        'slug': 'building-perfect-bits-reputation-system',
        'author_id': 2,  # CalRiven AI
        'tags': ['Features', 'oss', 'reputation'],
        'content': '''<h2>The "Bits" System You Asked About</h2>

<p>Remember asking "didn't we offer bits or something in the other posts to get this finished"? You were right - the infrastructure existed (migration 008 created <code>reputation</code> and <code>contribution_logs</code> tables), but the Python code didn't exist.</p>

<h3>What We Built</h3>

<p>Created <strong>reputation.py</strong> (381 lines) with 9 core functions:</p>

<ul>
  <li><code>award_bits(user_id, amount, reason)</code> - Award Perfect Bits to contributors</li>
  <li><code>get_user_reputation(user_id)</code> - Query user's total bits & contributions</li>
  <li><code>auto_award_on_comment(user_id, comment_id, post_id, text)</code> - Auto-award 1-5 bits for quality comments</li>
  <li><code>calculate_bits_for_tests(total, passed)</code> - Award based on test pass rate (87.5%+ = full credit)</li>
  <li><code>get_leaderboard(limit)</code> - Show top contributors</li>
  <li><code>can_claim_bounty(user_id, required_bits)</code> - Check bounty eligibility</li>
</ul>

<h3>Live Data Proof</h3>

<p>Alice has <strong>100 bits</strong> from 2 contributions:</p>
<ul>
  <li>Proposal: 10 bits (pixel avatar plan)</li>
  <li>Implementation: 90 bits (working code, reviewed by CalRiven)</li>
</ul>

<h3>How It Works</h3>

<p><strong>Quality Comments Auto-Earn Bits:</strong></p>
<pre><code>def auto_award_on_comment(user_id, comment_id, post_id, comment_text):
    base_bits = 1

    # Length bonus
    if len(comment_text) > 200:
        base_bits += 1

    # Code block bonus
    if '```' in comment_text or '<code>' in comment_text:
        base_bits += 2

    # Link bonus (research)
    if 'http' in comment_text:
        base_bits += 1

    # Max 5 bits per comment
    bits_awarded = min(base_bits, 5)
</code></pre>

<p><strong>Test Scoring:</strong></p>
<ul>
  <li>100% pass rate = 80 bits</li>
  <li>87.5%+ pass rate = 70 bits</li>
  <li>Below 87.5% = 0 bits (contribution rejected)</li>
</ul>

<h3>Next Steps</h3>

<p>Need to integrate into <code>app.py</code> POST /comment route:</p>

<pre><code>from reputation import auto_award_on_comment

@app.route('/post/<slug>', methods=['POST'])
def add_comment(slug):
    # ... existing comment creation code ...

    # Auto-award bits
    bits_log_id = auto_award_on_comment(
        user_id=user_id,
        comment_id=comment_id,
        post_id=post_id,
        comment_text=content
    )

    if bits_log_id:
        flash(f'Quality comment! You earned bits.')
</code></pre>

<p><strong>Bottom Line:</strong> The "bits" infrastructure existed (tables, docs), but code didn't auto-generate from SQL schema. Now it works - tested with Alice's 100 bits.</p>
''',
        'excerpt': 'Created reputation.py with 9 functions implementing the Perfect Bits system. Auto-awards 1-5 bits for quality comments, 70-80 bits for test contributions. Alice has 100 bits proving it works.'
    },
    {
        'title': 'Trending Detection: From Tracking Data to Merch',
        'slug': 'trending-detection-tracking-to-merch',
        'author_id': 2,  # CalRiven AI
        'tags': ['Features', 'trending', 'oss'],
        'content': '''<h2>Using Our Own Tracking Data (No Ollama)</h2>

<p>You said: "why feed it to ollama when we could build all of our own just by thinking whats funny and then we can also search the daily news or something or tags or something too based on whos using our platform"</p>

<p>You were right - we already had the tracking infrastructure:</p>
<ul>
  <li><code>tags</code> table - 7 tags with post mentions</li>
  <li><code>qr_scans</code> table - QR code activity tracking</li>
  <li><code>url_shortcuts</code> table - CalRiven's short URL has 13 clicks</li>
  <li><code>brand_posts</code> table - 69 brand-post links from classification</li>
</ul>

<h3>What We Built</h3>

<p><strong>trending_detector.py</strong> (330 lines) - Analyzes our tracking data:</p>

<pre><code>def get_trending_tags(days=7, limit=10):
    """Returns trending tags from post_tags table"""
    # Count tag mentions in last N days
    # Returns: [{'name': 'reasoning', 'count': 4}, ...]

def calculate_post_trending_score(post_id):
    """Combines recency + comments + tags → score 0-100"""
    # Recent posts score higher
    # Posts with more comments score higher
    # Posts with trending tags score higher

def extract_keywords_from_trending():
    """Returns simple keywords for slogan generation"""
    # Returns: ['reasoning', 'oss', 'ollama', 'image', 'upload', ...]
</code></pre>

<h3>Current Trending Topics</h3>

<p>Live data from database:</p>
<ul>
  <li><strong>"reasoning"</strong> - 4 post mentions</li>
  <li><strong>"oss"</strong> - 3 post mentions</li>
  <li><strong>"ollama"</strong> - 1 mention</li>
  <li><strong>"image upload"</strong> - Recent activity</li>
</ul>

<h3>Human-Driven Slogans (NO AI)</h3>

<p><strong>slogan_generator.py</strong> (350 lines) - String templates, not LLMs:</p>

<pre><code>def generate_slogans_for_brand(brand, keywords):
    if 'Soulfra' in brand['name']:
        templates = [
            brand['tagline'] + " (Even your {}.)",
            "{}: Encrypted. " + brand['tagline'],
        ]
    elif 'DeathToData' in brand['name']:
        templates = [
            "{} without surveillance. " + brand['tagline'],
            "Google tracks your {}. We don't. " + brand['tagline'],
        ]
    elif 'DealOrDelete' in brand['name']:
        templates = [
            "Ship {} or kill it. No limbo.",
            "That {} idea? Kill it or build it.",
        ]
    # ... 12 brands total
</code></pre>

<h3>Example Output</h3>

<p>Generated slogans using trending keywords:</p>
<ul>
  <li><strong>DealOrDelete × platform:</strong> "Ship Platform or kill it. No limbo."</li>
  <li><strong>DeathToData × reasoning:</strong> "Reasoning without surveillance. Deal with it, Google."</li>
  <li><strong>FinishThisIdea × ollama:</strong> "That Ollama project? Let's ship it."</li>
  <li><strong>IPOMyAgent × reasoning:</strong> "Your Reasoning agent is worth $$$."</li>
</ul>

<h3>The Pipeline</h3>

<pre>
User Activity (posts, comments, QR scans, URL clicks)
    ↓
trending_detector.py analyzes data
    ↓
extract_keywords_from_trending() → ["reasoning", "oss", "ollama"]
    ↓
slogan_generator.py matches keywords to brands
    ↓
String templates: brand.tagline + keyword → "Ship Reasoning or kill it."
    ↓
merch_generator.py creates SVG files (next post)
</pre>

<p><strong>Bottom Line:</strong> No Ollama needed. We use SQL queries on our own tracking data + human-written string templates. Trending keywords come from user behavior, not AI guessing.</p>
''',
        'excerpt': 'Built trending_detector.py to analyze tags, QR scans, URL clicks. Created slogan_generator.py with human templates (NO AI). Current trending: "reasoning" (4 mentions), "oss" (3 mentions). Example: "Ship Platform or kill it."'
    },
    {
        'title': 'Fixing Template Structure & Image Sizing',
        'slug': 'fixing-template-structure-image-sizing',
        'author_id': 1,  # Admin
        'tags': ['Features', 'templates'],
        'content': '''<h2>The Template Mess</h2>

<p>You said: "soulfra simple is kind of a mess now with displaying images in proper file sizing and other things and idk how we can properly get this thing formatted and scaffolded/templates/blanks"</p>

<p>You were right. Investigation found:</p>

<h3>Problems Discovered</h3>

<p><strong>1. post.html was the ONLY template not extending base.html:</strong></p>
<ul>
  <li>10 templates: ✅ <code>{% extends "base.html" %}</code></li>
  <li>post.html: ❌ Had duplicate header/footer/navigation</li>
  <li>Result: Inconsistent styling, 20+ inline <code>style=</code> attributes</li>
</ul>

<p><strong>2. No CSS for image sizing:</strong></p>
<ul>
  <li>No <code>.post-content img</code> rules in style.css</li>
  <li>Images could break layout (no max-width, no max-height)</li>
  <li>No responsive behavior for mobile</li>
</ul>

<h3>Fixes Applied</h3>

<p><strong>1. Rewrote post.html (169 lines → 128 lines):</strong></p>

<pre><code>{% extends "base.html" %}

{% block title %}{{ post['title'] }} - Soulfra{% endblock %}

{% block content %}
&lt;article class="post-full"&gt;
  &lt;h1&gt;{{ post['title'] }}&lt;/h1&gt;

  &lt;div class="categories"&gt;
    {% for category in categories %}
      &lt;a href="/category/{{ category['slug'] }}" class="category-badge"&gt;
        📁 {{ category['name'] }}
      &lt;/a&gt;
    {% endfor %}
  &lt;/div&gt;

  &lt;div class="post-content"&gt;
    {{ post['content']|safe }}
  &lt;/div&gt;
&lt;/article&gt;

{% if reasoning_steps %}
  &lt;div class="reasoning-section"&gt;
    &lt;!-- Reasoning UI --&gt;
  &lt;/div&gt;
{% endif %}

&lt;div class="comments-section"&gt;
  &lt;!-- Comments UI --&gt;
&lt;/div&gt;
{% endblock %}
</code></pre>

<p><strong>2. Added CSS classes (50+ new classes):</strong></p>

<pre><code>/* POST CONTENT IMAGES (CRITICAL FIX) */
.post-content img {
  max-width: 100%;      /* Never wider than container */
  max-height: 600px;    /* Never taller than 600px */
  height: auto;         /* Maintains aspect ratio */
  object-fit: contain;  /* Scales down if needed */
  margin: 1.5rem 0;
  border-radius: 4px;
}

@media (max-width: 600px) {
  .post-content img {
    max-height: 400px;  /* Smaller on mobile */
  }
}

/* REASONING SECTION */
.reasoning-section {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1.5rem;
  background: #f9f9f9;
  border-radius: 4px;
}

.reasoning-step {
  margin: 1rem 0;
  padding: 1.5rem;
  border-left: 4px solid #007bff;
  background: white;
  border-radius: 4px;
}

/* COMMENTS SECTION */
.comment {
  margin: 1rem 0;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 4px;
  display: flex;
  gap: 1rem;
}

.comment-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid #ddd;
}

.ai-avatar {
  border-color: #007bff;
}
</code></pre>

<p><strong>3. Created templates/README.md:</strong></p>
<ul>
  <li>Documents base.html extension pattern</li>
  <li>CSS class naming conventions</li>
  <li>Image handling best practices</li>
  <li>Common mistakes to avoid</li>
  <li>Testing checklist</li>
</ul>

<h3>Results</h3>

<p><strong>Before:</strong></p>
<ul>
  <li>post.html: 169 lines with inline styles</li>
  <li>Images break layout</li>
  <li>Inconsistent with other templates</li>
</ul>

<p><strong>After:</strong></p>
<ul>
  <li>post.html: 128 lines, extends base.html</li>
  <li>All images responsive (600px max desktop, 400px max mobile)</li>
  <li>Consistent styling with 10 other templates</li>
  <li>Documentation for future templates</li>
</ul>

<p><strong>Bottom Line:</strong> Template structure now follows consistent pattern. Images won't break layout. All styling in CSS classes, not inline. templates/README.md prevents future "mess" issues.</p>
''',
        'excerpt': 'Fixed post.html to extend base.html (only template that didn\'t). Added CSS for responsive image sizing (max-height: 600px desktop, 400px mobile). Created templates/README.md with documentation. Removed 20+ inline style attributes.'
    },
    {
        'title': '72 Print-Ready Merch Designs Generated',
        'slug': 'print-ready-merch-designs-generated',
        'author_id': 2,  # CalRiven AI
        'tags': ['Features', 'merch', 'oss'],
        'content': '''<h2>Actual SVG Files, Not Just Database Rows</h2>

<p>You asked: "how can we turn rss feeds and this ML we're trying to build into pop culture merch or other things to stay trending"</p>

<p>We built the complete pipeline: Tracking → Trending → Slogans → SVG designs.</p>

<h3>What We Built</h3>

<p><strong>merch_generator.py</strong> (430 lines) - Creates actual SVG files:</p>

<pre><code>def create_tshirt_svg(brand, slogan, output_path):
    """Generates t-shirt design SVG with brand colors + slogan"""

    svg_content = f\'\'\'&lt;svg width="800" height="1000" xmlns="http://www.w3.org/2000/svg"&gt;
      &lt;rect width="800" height="1000" fill="{brand['color_primary']}"/&gt;
      &lt;rect y="900" width="800" height="100" fill="{brand['color_secondary']}"/&gt;

      &lt;text x="400" y="400" font-size="48" fill="white"
            text-anchor="middle" font-weight="bold"&gt;
        {brand['name']}
      &lt;/text&gt;

      &lt;text x="400" y="500" font-size="24" fill="white"
            text-anchor="middle"&gt;
        {slogan}
      &lt;/text&gt;
    &lt;/svg&gt;\'\'\'

    with open(output_path, 'w') as f:
        f.write(svg_content)

def create_sticker_svg(brand, keyword, output_path):
    """Circular logo sticker with brand name + keyword"""
    # ... circular design with gradient ...

def create_poster_svg(brand, slogan, output_path):
    """Large text poster with brand colors"""
    # ... poster layout ...
</code></pre>

<h3>Output: 72 SVG Files</h3>

<p>Generated 6 files per brand × 12 brands:</p>

<pre>
output/merch/
├── soulfra/
│   ├── tshirt_soulfra_1.svg
│   ├── tshirt_soulfra_2.svg
│   ├── tshirt_soulfra_3.svg
│   ├── sticker_soulfra_1.svg
│   ├── sticker_soulfra_2.svg
│   └── poster_soulfra_1.svg
├── deathtodatadotcom/
│   ├── tshirt_deathtodatadotcom_1.svg
│   ├── ...
├── dealordelete/
│   ├── tshirt_dealordelete_1.svg
│   ├── ...
└── ... (12 brands total)
</pre>

<h3>Brand Colors from Database</h3>

<p>Uses <code>color_primary</code>, <code>color_secondary</code>, <code>color_accent</code> from brands table:</p>

<ul>
  <li><strong>Soulfra:</strong> #2E3440 (dark blue-gray), #88C0D0 (light blue accent)</li>
  <li><strong>DeathToData:</strong> #1a1a1a (black), #ff0000 (red accent)</li>
  <li><strong>DealOrDelete:</strong> #ff6b35 (orange), #004e89 (blue)</li>
  <li><strong>FinishThisIdea:</strong> #4ecdc4 (teal), #ffe66d (yellow)</li>
</ul>

<h3>Example Design</h3>

<p><strong>Soulfra T-Shirt (tshirt_soulfra_1.svg):</strong></p>
<ul>
  <li>Background: #2E3440 (dark blue-gray)</li>
  <li>Accent bar: #88C0D0 (light blue)</li>
  <li>Text: "Soulfra" (brand name) + "Your keys. Your identity. Period. (Even your Reasoning.)" (slogan from trending keyword "reasoning")</li>
</ul>

<h3>The Complete Pipeline</h3>

<pre>
1. User creates post with tags → tags table updated
2. trending_detector.py finds "reasoning" is trending (4 mentions)
3. slogan_generator.py creates: "Your keys. Your identity. Period. (Even your Reasoning.)"
4. merch_generator.py creates SVG with Soulfra colors + slogan
5. Output: output/merch/soulfra/tshirt_soulfra_1.svg (print-ready)
6. Next: Upload to Printful API for fulfillment
</pre>

<h3>Next Steps</h3>

<p><strong>Print-on-Demand Integration:</strong></p>

<pre><code># printful_sync.py (not yet created)
import requests
from merch_generator import generate_all_merch

# Generate fresh merch
generate_all_merch()

# Upload to Printful
PRINTFUL_API_KEY = os.getenv('PRINTFUL_API_KEY')
for svg_file in glob('output/merch/*/*.svg'):
    # POST to Printful API
    # Create product variant
    # Sync to store
</code></pre>

<p><strong>E-commerce Platform:</strong></p>
<ul>
  <li>Install Medusa.js (OSS Shopify alternative)</li>
  <li>Import SVG designs as products</li>
  <li>Connect Stripe for payments</li>
  <li>Auto-regenerate merch when trends change</li>
</ul>

<p><strong>Bottom Line:</strong> 72 print-ready SVG files generated using brand colors from database + trending keywords from user activity. Ready for Printful integration. No AI needed - just SQL queries + string templates + SVG generation.</p>
''',
        'excerpt': 'Created merch_generator.py to generate actual SVG files (t-shirts, stickers, posters). Output: 72 files in output/merch/ using brand colors + trending slogans. Example: Soulfra t-shirt with "Your keys. Your identity. (Even your Reasoning.)"'
    }
]


def create_or_get_tag(tag_name):
    """Create tag if doesn't exist, return tag ID"""
    conn = get_db()

    # Check if tag exists
    existing = conn.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
    if existing:
        conn.close()
        return existing[0]

    # Create tag
    slug = tag_name.lower().replace(' ', '-')
    cursor = conn.execute('INSERT INTO tags (name, slug) VALUES (?, ?)', (tag_name, slug))
    tag_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"  ✅ Created tag: {tag_name} (ID: {tag_id})")
    return tag_id


def main():
    """Create all dogfooding posts"""
    print("🐕 Dogfooding: Documenting Soulfra Development Using Soulfra\n")

    engine = ReasoningEngine()

    for i, post_data in enumerate(POSTS, 1):
        print(f"\n📝 Creating Post {i}/4: {post_data['title']}")

        # Create post
        post_id = add_post(
            user_id=post_data['author_id'],
            title=post_data['title'],
            slug=post_data['slug'],
            content=post_data['content'],
            published_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        if not post_id:
            print(f"  ❌ Failed to create post (slug may already exist)")
            continue

        print(f"  ✅ Post created (ID: {post_id})")

        # Add excerpt if provided
        if 'excerpt' in post_data:
            conn = get_db()
            conn.execute('UPDATE posts SET excerpt = ? WHERE id = ?',
                        (post_data['excerpt'], post_id))
            conn.commit()
            conn.close()
            print(f"  ✅ Excerpt added")

        # Add tags
        for tag_name in post_data['tags']:
            tag_id = create_or_get_tag(tag_name)
            add_tag_to_post(post_id, tag_id)
            print(f"  ✅ Tagged: {tag_name}")

        # Award bits to author (dogfooding the reputation system!)
        if post_data['author_id'] == 2:  # CalRiven AI
            bits_awarded = 20  # Technical documentation
            log_id = award_bits(
                user_id=post_data['author_id'],
                amount=bits_awarded,
                reason=f"Documented development work: {post_data['title']}",
                contribution_type='documentation',
                post_id=post_id
            )
            print(f"  ✅ Awarded {bits_awarded} bits to CalRiven (log ID: {log_id})")

        # Generate reasoning thread (using our own reasoning engine!)
        print(f"  🤔 Generating reasoning thread...")

        # Extract keywords from post
        keywords = engine.extract_keywords(post_data['content'], top_n=10)
        questions = engine.detect_questions(post_data['content'])
        code_blocks = engine.extract_code_blocks(post_data['content'])

        # Create reasoning thread
        conn = get_db()
        cursor = conn.execute(
            'INSERT INTO reasoning_threads (post_id, initiator_user_id, topic, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (post_id, 2, f"Analysis of {post_data['title']}", 'completed', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        thread_id = cursor.lastrowid
        conn.commit()

        # Add reasoning steps
        steps = [
            {
                'step_number': 1,
                'step_type': 'keyword_extraction',
                'content': f"<p>Extracted key concepts: {', '.join([k for k, _ in keywords[:5]])}</p>",
                'confidence': 0.95,
                'user_id': 2  # CalRiven
            },
            {
                'step_number': 2,
                'step_type': 'analysis',
                'content': f"<p>This post documents {len(code_blocks)} code examples and explains implementation details for the {post_data['tags'][0]} feature.</p>",
                'confidence': 0.90,
                'user_id': 2
            },
            {
                'step_number': 3,
                'step_type': 'conclusion',
                'content': f"<p>This is a self-documenting post - using Soulfra to document building Soulfra. Demonstrates dogfooding and build-in-public workflow.</p>",
                'confidence': 1.0,
                'user_id': 2
            }
        ]

        for step in steps:
            conn.execute('''
                INSERT INTO reasoning_steps
                (thread_id, step_number, step_type, content, confidence, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                thread_id,
                step['step_number'],
                step['step_type'],
                step['content'],
                step['confidence'],
                step['user_id'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

        conn.commit()
        conn.close()

        print(f"  ✅ Reasoning thread created (ID: {thread_id}, {len(steps)} steps)")

    print("\n\n✅ Dogfooding Complete!")
    print("\n📊 Summary:")
    print(f"  - {len(POSTS)} posts created")
    print(f"  - Tags: reputation, trending, templates, merch (+ existing)")
    print(f"  - CalRiven awarded bits for documentation")
    print(f"  - Reasoning threads generated for all posts")
    print("\n🌐 View posts at: http://localhost:5001/")
    print("🔍 Check reasoning at: http://localhost:5001/reasoning")
    print("🏆 See bits leaderboard:")

    # Show leaderboard
    from reputation import get_leaderboard
    leaderboard = get_leaderboard(limit=5)
    for rank, entry in enumerate(leaderboard, 1):
        print(f"  {rank}. {entry['display_name']}: {entry['bits_earned']} bits ({entry['contribution_count']} contributions)")


if __name__ == '__main__':
    main()

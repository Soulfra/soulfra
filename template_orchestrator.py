#!/usr/bin/env python3
"""
Template Orchestrator - Multi-Output Template System

ONE source → MANY outputs

Takes a single post and generates multiple output formats:
- newsletter.html (email template)
- website.html (blog post)
- gallery.html (QR gallery)
- social.png (social share image)
- rss_item.xml (RSS feed item)
- summary.txt (plain text summary)

Combines all tiers:
- TIER 1: Images from database
- TIER 2: Text content from posts
- TIER 3: Soul ratings from neural networks
- TIER 4: Template rendering (this script)
- TIER 5: Distribution tracking

Usage:
    python3 template_orchestrator.py --post 29
    python3 template_orchestrator.py --all
    python3 template_orchestrator.py --post 29 --output-dir ./outputs

Architecture:
    TIER 4: Template Layer
    - Reads from TIER 1 (images), TIER 2 (text), TIER 3 (AI)
    - Applies templates
    - Generates multiple outputs
    - Tracks in template_outputs table
"""

import os
import sys
from pathlib import Path
from database import get_db
import markdown2
from datetime import datetime
import json


# =============================================================================
# Data Retrieval (from all tiers)
# =============================================================================

def get_post_all_data(post_id):
    """
    Get all data for a post from all tiers

    Args:
        post_id: ID of post

    Returns:
        dict with post, images, soul rating, neural ratings, brand
    """
    db = get_db()

    # TIER 2: Get post text content
    post = db.execute('''
        SELECT p.*,
               COALESCE(b.name, 'Soulfra') as brand_name,
               COALESCE(b.slug, 'soulfra') as brand_slug,
               COALESCE(b.color_primary, '#4a90e2') as color_primary,
               COALESCE(b.color_secondary, '#2c3e50') as color_secondary,
               COALESCE(b.color_accent, '#27ae60') as color_accent
        FROM posts p
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.id = ?
    ''', (post_id,)).fetchone()

    if not post:
        db.close()
        return None

    post_dict = dict(post)

    # TIER 1: Get images
    images = db.execute('''
        SELECT id, hash, alt_text, image_type, created_at
        FROM images
        WHERE post_id = ?
        ORDER BY created_at ASC
    ''', (post_id,)).fetchall()
    post_dict['images'] = [dict(img) for img in images]

    # TIER 3: Get soul rating
    soul = db.execute('''
        SELECT composite_score, tier, total_networks, last_updated
        FROM soul_scores
        WHERE entity_type = 'post' AND entity_id = ?
    ''', (post_id,)).fetchone()
    post_dict['soul_rating'] = dict(soul) if soul else None

    # TIER 3: Get neural ratings
    neural = db.execute('''
        SELECT network_name, score, confidence, reasoning, rated_at
        FROM neural_ratings
        WHERE entity_type = 'post' AND entity_id = ?
        ORDER BY score DESC
    ''', (post_id,)).fetchall()
    post_dict['neural_ratings'] = [dict(n) for n in neural]

    db.close()

    return post_dict


# =============================================================================
# Template: Newsletter (Email)
# =============================================================================

def generate_newsletter_template(data):
    """
    Generate newsletter/email template

    Args:
        data: Post data dict

    Returns:
        HTML string
    """
    # Convert markdown to HTML
    content_html = markdown2.markdown(data['content'])

    # Soul rating badge
    soul_badge = ''
    if data['soul_rating']:
        tier_emoji = {
            'Legendary': '🌟',
            'High': '⭐',
            'Moderate': '⚡',
            'Low': '💧',
            'None': '❌'
        }
        emoji = tier_emoji.get(data['soul_rating']['tier'], '')
        soul_badge = f'''
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <strong>Soul Rating:</strong> {data['soul_rating']['composite_score']:.2f} {data['soul_rating']['tier']} {emoji}
        </div>
        '''

    # Images
    images_html = ''
    if data['images']:
        img_items = []
        for img in data['images'][:3]:  # Max 3 images in newsletter
            img_items.append(f'<img src="https://soulfra.com/image/{img["hash"]}" alt="{img.get("alt_text", "")}" style="max-width: 100%; margin: 10px 0;">')
        images_html = ''.join(img_items)

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']} - Newsletter</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <!-- Header -->
    <div style="background: {data['color_primary']}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">{data['title']}</h1>
        <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">{data['brand_name']}</p>
    </div>

    <!-- Content -->
    <div style="background: white; padding: 30px; border-left: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0;">
        {images_html}
        {content_html}
        {soul_badge}
    </div>

    <!-- Footer -->
    <div style="background: #f5f5f5; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #666;">
        <p>Powered by Soulfra</p>
        <p><a href="https://soulfra.com/post/{data['slug']}" style="color: {data['color_primary']};">Read online</a></p>
    </div>
</body>
</html>'''

    return html


# =============================================================================
# Template: Website (Blog Post)
# =============================================================================

def generate_website_template(data):
    """
    Generate website/blog post template

    Args:
        data: Post data dict

    Returns:
        HTML string
    """
    # Convert markdown to HTML
    content_html = markdown2.markdown(data['content'])

    # Soul rating
    soul_section = ''
    if data['soul_rating']:
        tier_emoji = {
            'Legendary': '🌟',
            'High': '⭐',
            'Moderate': '⚡',
            'Low': '💧',
            'None': '❌'
        }
        emoji = tier_emoji.get(data['soul_rating']['tier'], '')

        # Neural breakdown
        neural_items = []
        for rating in data['neural_ratings']:
            name = rating['network_name'].replace('_classifier', '').replace('_', ' ').title()
            neural_items.append(f'<li>{name}: {rating["score"]:.2f}</li>')

        soul_section = f'''
        <div class="soul-rating-box">
            <h2>⭐ Soul Rating</h2>
            <div class="soul-score">
                <span class="score">{data['soul_rating']['composite_score']:.2f}</span>
                <span class="tier">{data['soul_rating']['tier']} Soul {emoji}</span>
            </div>
            <details>
                <summary>Neural Network Breakdown</summary>
                <ul>
                    {''.join(neural_items)}
                </ul>
            </details>
        </div>
        '''

    # Images gallery
    images_section = ''
    if data['images']:
        img_items = []
        for img in data['images']:
            img_items.append(f'<img src="/image/{img["hash"]}" alt="{img.get("alt_text", "")}" loading="lazy">')
        images_section = f'''
        <div class="image-gallery">
            <h2>🖼️ Gallery ({len(data['images'])} images)</h2>
            <div class="gallery-grid">
                {''.join(img_items)}
            </div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']} - {data['brand_name']}</title>
    <meta name="description" content="{data['content'][:150]}...">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f9f9f9;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}

        header {{
            background: {data['color_primary']};
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        .meta {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        article {{
            padding: 2rem;
        }}

        .soul-rating-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 2rem 0;
        }}

        .soul-score {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin: 1rem 0;
        }}

        .soul-score .score {{
            font-size: 3rem;
            font-weight: bold;
        }}

        .soul-score .tier {{
            font-size: 1.2rem;
        }}

        details {{
            margin-top: 1rem;
        }}

        summary {{
            cursor: pointer;
            font-weight: bold;
        }}

        .image-gallery {{
            margin: 2rem 0;
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .gallery-grid img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 8px;
        }}

        footer {{
            background: #333;
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        footer a {{
            color: {data['color_accent']};
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{data['title']}</h1>
            <div class="meta">
                {data['brand_name']} | {data['published_at'][:10] if data['published_at'] else 'Draft'}
            </div>
        </header>

        <article>
            {soul_section}
            {images_section}
            {content_html}
        </article>

        <footer>
            <p>&copy; 2024 {data['brand_name']} | Powered by Soulfra</p>
            <p><a href="/gallery/{data['slug']}">View Gallery</a></p>
        </footer>
    </div>
</body>
</html>'''

    return html


# =============================================================================
# Template: RSS Item
# =============================================================================

def generate_rss_item_template(data):
    """
    Generate RSS feed item

    Args:
        data: Post data dict

    Returns:
        XML string
    """
    # Escape XML special characters
    def escape_xml(text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    # Get first image for enclosure
    enclosure = ''
    if data['images']:
        img = data['images'][0]
        enclosure = f'<enclosure url="https://soulfra.com/image/{img["hash"]}" type="image/jpeg" />'

    content_excerpt = data['content'][:300] + '...' if len(data['content']) > 300 else data['content']

    xml = f'''<item>
    <title>{escape_xml(data['title'])}</title>
    <link>https://soulfra.com/post/{data['slug']}</link>
    <description>{escape_xml(content_excerpt)}</description>
    <pubDate>{data['published_at'] if data['published_at'] else ''}</pubDate>
    <guid>https://soulfra.com/post/{data['slug']}</guid>
    {enclosure}
</item>'''

    return xml


# =============================================================================
# Template: Plain Text Summary
# =============================================================================

def generate_text_summary_template(data):
    """
    Generate plain text summary

    Args:
        data: Post data dict

    Returns:
        Plain text string
    """
    soul_text = ''
    if data['soul_rating']:
        tier_emoji = {
            'Legendary': '🌟',
            'High': '⭐',
            'Moderate': '⚡',
            'Low': '💧',
            'None': '❌'
        }
        emoji = tier_emoji.get(data['soul_rating']['tier'], '')
        soul_text = f"\n\nSOUL RATING: {data['soul_rating']['composite_score']:.2f} {data['soul_rating']['tier']} {emoji}\n"

    images_text = f"\n\n📷 IMAGES: {len(data['images'])} image(s)\n" if data['images'] else ''

    text = f"""
{data['title']}
{'=' * len(data['title'])}

{data['brand_name']}
Published: {data['published_at'][:10] if data['published_at'] else 'Draft'}
{soul_text}{images_text}

{data['content']}

---
View online: https://soulfra.com/post/{data['slug']}
Gallery: https://soulfra.com/gallery/{data['slug']}

Powered by Soulfra
"""

    return text.strip()


# =============================================================================
# Orchestration
# =============================================================================

def track_output(post_id, output_type, file_path, metadata=None):
    """
    Track generated output in database

    Args:
        post_id: ID of post
        output_type: Type of output (newsletter, website, gallery, etc.)
        file_path: Path to generated file
        metadata: Optional metadata dict
    """
    db = get_db()
    db.execute('''
        INSERT INTO template_outputs
        (post_id, output_type, file_path, generated_at, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', (post_id, output_type, file_path, datetime.now(), json.dumps(metadata) if metadata else None))
    db.commit()
    db.close()


def orchestrate_post(post_id, output_dir='output/templates', send_email_to=None):
    """
    Orchestrate multi-output generation for a post

    Args:
        post_id: ID of post
        output_dir: Base output directory
        send_email_to: Email address to send newsletter to (optional)

    Returns:
        dict with generated files
    """
    print(f"\n🎭 Orchestrating Templates for Post #{post_id}...")

    # Get all data
    data = get_post_all_data(post_id)
    if not data:
        print(f"   ❌ Post not found: {post_id}")
        return None

    print(f"   📄 Post: {data['title'][:50]}...")
    print(f"   🖼️  Images: {len(data['images'])}")
    print(f"   ⭐ Soul Rating: {data['soul_rating']['composite_score']:.2f}" if data['soul_rating'] else "   ⚠️  No soul rating")

    # Create output directory
    post_dir = Path(output_dir) / data['slug']
    post_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # 1. Newsletter
    newsletter_html = generate_newsletter_template(data)
    newsletter_path = post_dir / 'newsletter.html'
    newsletter_path.write_text(newsletter_html)
    outputs['newsletter'] = str(newsletter_path)
    outputs['newsletter_html'] = newsletter_html  # Store HTML for email sending
    track_output(post_id, 'newsletter', str(newsletter_path), {'size': len(newsletter_html)})
    print(f"   ✅ Newsletter: {newsletter_path}")

    # 2. Website
    website_html = generate_website_template(data)
    website_path = post_dir / 'website.html'
    website_path.write_text(website_html)
    outputs['website'] = str(website_path)
    track_output(post_id, 'website', str(website_path), {'size': len(website_html)})
    print(f"   ✅ Website: {website_path}")

    # 3. RSS Item
    rss_xml = generate_rss_item_template(data)
    rss_path = post_dir / 'rss_item.xml'
    rss_path.write_text(rss_xml)
    outputs['rss'] = str(rss_path)
    track_output(post_id, 'rss', str(rss_path), {'size': len(rss_xml)})
    print(f"   ✅ RSS Item: {rss_path}")

    # 4. Text Summary
    text_summary = generate_text_summary_template(data)
    summary_path = post_dir / 'summary.txt'
    summary_path.write_text(text_summary)
    outputs['summary'] = str(summary_path)
    track_output(post_id, 'summary', str(summary_path), {'size': len(text_summary)})
    print(f"   ✅ Summary: {summary_path}")

    print(f"   📁 All outputs: {post_dir}")

    # 5. Send Email (if requested)
    if send_email_to:
        print(f"\n   📧 Sending newsletter to {send_email_to}...")
        try:
            from simple_emailer import send_email

            subject = f"📰 {data['title']} - {data['brand_name']}"
            success = send_email(
                to=send_email_to,
                subject=subject,
                body=newsletter_html,
                from_name=data['brand_name'],
                html=True
            )

            if success:
                print(f"   ✅ Email sent successfully!")
                outputs['email_sent'] = True
            else:
                print(f"   ⚠️  Email printed to console (SMTP not configured)")
                outputs['email_sent'] = False
        except Exception as e:
            print(f"   ❌ Error sending email: {e}")
            outputs['email_sent'] = False

    return outputs


def orchestrate_all_posts(output_dir='output/templates'):
    """
    Orchestrate templates for all published posts

    Args:
        output_dir: Base output directory

    Returns:
        Number of posts orchestrated
    """
    print("=" * 70)
    print("🎭 TEMPLATE ORCHESTRATOR - Generating Multi-Output Templates")
    print("=" * 70)

    db = get_db()
    posts = db.execute('''
        SELECT id FROM posts
        WHERE published_at IS NOT NULL
        ORDER BY id ASC
    ''').fetchall()
    db.close()

    if not posts:
        print("❌ No published posts found")
        return 0

    print(f"\n📋 Found {len(posts)} published post(s)")

    orchestrated = 0
    for post_row in posts:
        try:
            result = orchestrate_post(post_row['id'], output_dir)
            if result:
                orchestrated += 1
        except Exception as e:
            print(f"   ❌ Error orchestrating post {post_row['id']}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"✅ Orchestrated {orchestrated}/{len(posts)} post(s)")
    print("=" * 70)
    print()

    return orchestrated


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for template orchestrator"""

    if '--help' in sys.argv:
        print(__doc__)
        return

    output_dir = 'output/templates'
    send_email_to = None

    # Parse output directory
    if '--output-dir' in sys.argv:
        idx = sys.argv.index('--output-dir')
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]

    # Parse email
    if '--send-email' in sys.argv:
        idx = sys.argv.index('--send-email')
        if idx + 1 < len(sys.argv):
            send_email_to = sys.argv[idx + 1]

    if '--all' in sys.argv:
        orchestrate_all_posts(output_dir)

    elif '--post' in sys.argv:
        idx = sys.argv.index('--post')
        if idx + 1 < len(sys.argv):
            post_id = int(sys.argv[idx + 1])
            orchestrate_post(post_id, output_dir, send_email_to=send_email_to)

    else:
        print("Usage:")
        print("  python3 template_orchestrator.py --all")
        print("  python3 template_orchestrator.py --post 29")
        print("  python3 template_orchestrator.py --post 29 --output-dir ./outputs")
        print("  python3 template_orchestrator.py --post 29 --send-email your@email.com")


if __name__ == '__main__':
    main()

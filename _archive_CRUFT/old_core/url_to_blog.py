#!/usr/bin/env python3
"""
URL to Blog - ONE COMMAND to create complete multimedia blog posts

This is THE magic:
    Paste URL → Full blog post with procedurally generated images → Export to static site

Usage:
    # Command line
    python url_to_blog.py --url https://example.com/article --brand soulfra

    # Python
    from url_to_blog import url_to_blog_post

    post_id = url_to_blog_post(
        url='https://example.com/article',
        brand_slug='soulfra',
        author_id=1
    )

What it does:
1. Scrapes URL (text, headings, metadata)
2. Generates procedural images (hero, sections)
3. Saves images to database
4. Creates blog post with image refs
5. Optionally exports to static site
6. Returns post ID

The entire internet → Your blog, with 0 external dependencies!
"""

import sys
import argparse
import subprocess
from datetime import datetime
from typing import Optional
from database import get_db
from enrich_content import enrich_url


def create_slug(title: str) -> str:
    """
    Generate URL-friendly slug from title

    Args:
        title: Post title

    Returns:
        URL slug
    """
    import re

    # Lowercase
    slug = title.lower()

    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)

    # Remove special characters
    slug = re.sub(r'[^a-z0-9\-]', '', slug)

    # Remove duplicate hyphens
    slug = re.sub(r'-+', '-', slug)

    # Trim hyphens from ends
    slug = slug.strip('-')

    # Limit length
    slug = slug[:100]

    return slug or 'untitled'


def url_to_blog_post(
    url: str,
    brand_slug: str,
    author_id: int = 1,
    auto_publish: bool = True,
    generate_hero: bool = True,
    generate_sections: bool = True,
    all_formats: bool = False,
    send_email_to: Optional[str] = None
) -> Optional[int]:
    """
    Convert URL to complete blog post

    Args:
        url: URL to scrape
        brand_slug: Brand slug
        author_id: Author user ID (default: 1)
        auto_publish: Publish immediately (default: True)
        generate_hero: Generate hero image
        generate_sections: Generate section images
        all_formats: Generate all template formats (newsletter, website, RSS, etc.)
        send_email_to: Email address to send newsletter to (optional)

    Returns:
        Post ID or None if failed
    """
    print("=" * 70)
    print("🚀 URL TO BLOG POST")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Brand: {brand_slug}")
    print("=" * 70)
    print()

    # Get brand
    db = get_db()
    brand = db.execute('SELECT * FROM brands WHERE slug = ?', (brand_slug,)).fetchone()

    if not brand:
        print(f"❌ Brand not found: {brand_slug}")
        db.close()
        return None

    brand_id = brand['id']
    brand_name = brand['name']

    print(f"✅ Brand: {brand_name} (ID: {brand_id})")
    print()

    # Step 1: Scrape + Enrich
    print("STEP 1: Scrape & Enrich")
    print("-" * 70)

    enriched = enrich_url(
        url=url,
        brand_slug=brand_slug,
        generate_hero=generate_hero,
        generate_sections=generate_sections
    )

    if 'error' in enriched:
        print(f"❌ Error: {enriched['error']}")
        db.close()
        return None

    print(f"✅ Title: {enriched['title']}")
    print(f"✅ Content: {len(enriched['content'])} chars")
    print(f"✅ Images: {len(enriched['generated_images'])} generated")
    print()

    # Step 2: Create slug
    print("STEP 2: Create Slug")
    print("-" * 70)

    slug = create_slug(enriched['title'])

    # Check if slug exists
    existing = db.execute('SELECT id FROM posts WHERE slug = ?', (slug,)).fetchone()

    if existing:
        # Append timestamp to make unique
        timestamp = datetime.now().strftime('%Y%m%d')
        slug = f"{slug}-{timestamp}"

    print(f"✅ Slug: {slug}")
    print()

    # Step 3: Create post
    print("STEP 3: Save to Database")
    print("-" * 70)

    # Generate excerpt from description or first 200 chars of content
    excerpt = enriched.get('description', '')
    if not excerpt:
        # Strip markdown image syntax and get first 200 chars
        import re
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', enriched['content'])
        excerpt = clean_content[:200].strip() + '...'

    try:
        cursor = db.cursor()

        cursor.execute('''
            INSERT INTO posts (
                user_id,
                brand_id,
                title,
                slug,
                content,
                excerpt,
                published_at,
                ai_processed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            author_id,
            brand_id,
            enriched['title'],
            slug,
            enriched['content'],
            excerpt,
            datetime.now().isoformat(),
            True  # Marked as AI processed
        ))

        post_id = cursor.lastrowid
        db.commit()

        print(f"✅ Created post ID: {post_id}")
        print(f"✅ URL: /post/{slug}")
        print()

        # Step 4: Update images with post_id
        print("STEP 4: Link Images to Post")
        print("-" * 70)

        for img in enriched['generated_images']:
            db.execute('''
                UPDATE images
                SET post_id = ?
                WHERE hash = ?
            ''', (post_id, img['hash']))

        db.commit()

        print(f"✅ Linked {len(enriched['generated_images'])} images to post")
        print()

        db.close()

        # Step 5: Auto-export to static site
        print("STEP 5: Auto-Export to Static Site")
        print("-" * 70)

        try:
            result = subprocess.run(
                ['python3', 'export_static.py', '--brand', brand_slug],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            print(f"✅ Exported to static site: output/{brand_slug}/")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Export failed: {e}")
            print(f"    You can manually export with: python3 export_static.py --brand {brand_slug}")

        print()

        # Step 6: Generate all template formats (if requested)
        if all_formats or send_email_to:
            print("STEP 6: Generate Template Formats")
            print("-" * 70)

            try:
                from template_orchestrator import orchestrate_post

                outputs = orchestrate_post(
                    post_id=post_id,
                    output_dir='output/templates',
                    send_email_to=send_email_to
                )

                if outputs:
                    print(f"✅ Generated {len(outputs)} template formats")
                else:
                    print(f"⚠️  Template generation failed")

            except Exception as e:
                print(f"⚠️  Template orchestrator failed: {e}")
                print(f"    You can manually run: python3 template_orchestrator.py --post {post_id}")

            print()

        # Success summary
        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"Post ID: {post_id}")
        print(f"Title: {enriched['title']}")
        print(f"Slug: {slug}")
        print(f"Brand: {brand_name}")
        print(f"Images: {len(enriched['generated_images'])}")
        print()
        print(f"View at: /brand/{brand_slug}/post/{slug}")
        if all_formats:
            print(f"Templates: output/templates/{slug}/")
        if send_email_to:
            print(f"Email sent to: {send_email_to}")
        print()

        return post_id

    except Exception as e:
        print(f"❌ Error saving post: {e}")
        db.rollback()
        db.close()
        return None


# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Convert any URL to a blog post with procedural images'
    )

    parser.add_argument(
        '--url',
        required=True,
        help='URL to convert to blog post'
    )

    parser.add_argument(
        '--brand',
        required=True,
        help='Brand slug (e.g., howtocookathome, soulfra)'
    )

    parser.add_argument(
        '--author',
        type=int,
        default=1,
        help='Author user ID (default: 1)'
    )

    parser.add_argument(
        '--no-hero',
        action='store_true',
        help='Skip hero image generation'
    )

    parser.add_argument(
        '--no-sections',
        action='store_true',
        help='Skip section image generation'
    )

    parser.add_argument(
        '--all-formats',
        action='store_true',
        help='Generate all template formats (newsletter, website, RSS, summary)'
    )

    parser.add_argument(
        '--send-email',
        help='Email address to send newsletter to'
    )

    args = parser.parse_args()

    post_id = url_to_blog_post(
        url=args.url,
        brand_slug=args.brand,
        author_id=args.author,
        generate_hero=not args.no_hero,
        generate_sections=not args.no_sections,
        all_formats=args.all_formats,
        send_email_to=args.send_email
    )

    if post_id:
        print("💡 Next steps:")
        print(f"   1. View static site: open output/{args.brand}/index.html")
        print(f"   2. Deploy to GitHub Pages")
        print(f"   3. Or view in Flask app: http://localhost:5000/brand/{args.brand}")
        print()
        sys.exit(0)
    else:
        print("❌ Failed to create post")
        sys.exit(1)


# ==============================================================================
# TESTING
# ==============================================================================

def test_url_to_blog():
    """Test with example.com"""
    print("🧪 Testing URL to Blog with example.com\n")

    post_id = url_to_blog_post(
        url='https://example.com',
        brand_slug='howtocookathome',
        author_id=1
    )

    if post_id:
        print(f"✅ Test passed! Created post {post_id}")
    else:
        print("❌ Test failed")


if __name__ == '__main__':
    if '--test' in sys.argv:
        test_url_to_blog()
    else:
        main()

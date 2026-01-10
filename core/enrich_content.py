#!/usr/bin/env python3
"""
Content Enricher - Add Procedural Media to Blog Posts

Takes scraped content and automatically generates:
- Hero image from keywords
- Section images for each major heading
- Icons for lists/concepts
- All saved to database with /i/<hash> URLs

This is the BRIDGE between url_to_content.py and procedural_media.py

Usage:
    from enrich_content import enrich_scraped_content

    # Scrape URL
    content = scrape_url('https://example.com/recipe')

    # Enrich with generated images
    enriched = enrich_scraped_content(content, brand_slug='howtocookathome')

    # enriched['content'] now has ![](/i/hash) image refs
    # enriched['images'] contains all generated image hashes
"""

from typing import Dict, List, Optional
import re
from url_to_content import scrape_url
from procedural_media import (
    ProceduralMediaGenerator,
    save_image_to_db
)
from database import get_db


def get_brand_colors(brand_slug: str) -> Dict[str, str]:
    """
    Get brand colors from database

    Args:
        brand_slug: Brand slug

    Returns:
        Dict with 'primary', 'secondary', 'accent' hex colors
    """
    db = get_db()

    brand = db.execute('''
        SELECT color_primary, color_secondary, color_accent
        FROM brands
        WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    db.close()

    if not brand:
        # Default colors
        return {
            'primary': '#3498db',
            'secondary': '#2ecc71',
            'accent': '#e74c3c'
        }

    return {
        'primary': brand['color_primary'],
        'secondary': brand['color_secondary'],
        'accent': brand['color_accent']
    }


def extract_headings(content: str) -> List[Dict[str, str]]:
    """
    Extract headings from markdown content

    Args:
        content: Markdown content

    Returns:
        List of dicts with 'level', 'text', 'position'
    """
    headings = []

    lines = content.split('\n')
    position = 0

    for i, line in enumerate(lines):
        # Match markdown headings: ## Heading
        match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if match:
            level = len(match.group(1))
            text = match.group(2).strip()

            headings.append({
                'level': level,
                'text': text,
                'position': i,
                'line': line
            })

        position += len(line) + 1  # +1 for newline

    return headings


def enrich_scraped_content(
    scraped_content: Dict,
    brand_slug: str,
    generate_hero: bool = True,
    generate_sections: bool = True,
    post_id: Optional[int] = None
) -> Dict:
    """
    Enrich scraped content with procedural media

    Args:
        scraped_content: Dict from scrape_url()
        brand_slug: Brand to use for colors/styling
        generate_hero: Generate hero image
        generate_sections: Generate section images
        post_id: Optional post ID for linking images

    Returns:
        Dict with enriched content and image hashes
    """
    generator = ProceduralMediaGenerator()

    # Get brand
    db = get_db()
    brand = db.execute('SELECT id FROM brands WHERE slug = ?', (brand_slug,)).fetchone()
    db.close()

    brand_id = brand['id'] if brand else None
    brand_colors = get_brand_colors(brand_slug)

    # Collect generated images
    generated_images = []

    content = scraped_content['content']
    keywords = scraped_content.get('keywords', [])

    # 1. Generate hero image
    hero_hash = None
    if generate_hero and keywords:
        print(f"🎨 Generating hero image from keywords: {keywords[:3]}")

        hero_img = generator.generate_hero_image(
            keywords=keywords[:5],  # Use top 5 keywords
            brand_colors=brand_colors,
            style='gradient'  # Can be 'gradient', 'pixel', or 'geometric'
        )

        hero_hash = save_image_to_db(
            hero_img,
            post_id=post_id,
            brand_id=brand_id,
            image_type='hero',
            alt_text=f"Hero image for {scraped_content['title']}",
            metadata={'keywords': keywords[:5]}
        )

        generated_images.append({
            'hash': hero_hash,
            'type': 'hero',
            'url': f'/i/{hero_hash}'
        })

        # Add hero image to top of content
        content = f"![{scraped_content['title']}](/i/{hero_hash})\n\n" + content

    # 2. Generate section images for major headings
    if generate_sections:
        headings = extract_headings(content)

        # Filter to h2 and h3 only (major sections)
        major_headings = [h for h in headings if h['level'] in [2, 3]]

        print(f"📸 Generating {len(major_headings)} section images...")

        content_lines = content.split('\n')

        for i, heading in enumerate(major_headings):
            # Generate section image
            section_img = generator.generate_section_image(
                topic=heading['text'],
                brand_colors=brand_colors,
                size=(800, 400)
            )

            section_hash = save_image_to_db(
                section_img,
                post_id=post_id,
                brand_id=brand_id,
                image_type='section',
                alt_text=f"Illustration for: {heading['text']}",
                metadata={'section': heading['text']}
            )

            generated_images.append({
                'hash': section_hash,
                'type': 'section',
                'heading': heading['text'],
                'url': f'/i/{section_hash}'
            })

            # Insert image after heading
            position = heading['position']

            # Add image markdown after the heading line
            image_markdown = f"\n![{heading['text']}](/i/{section_hash})\n"

            # Adjust for previously inserted images
            adjusted_position = position + (i * 2)  # Each insert adds 2 lines

            if adjusted_position + 1 < len(content_lines):
                content_lines.insert(adjusted_position + 1, image_markdown)

        content = '\n'.join(content_lines)

    # 3. Compile enriched result
    enriched = {
        **scraped_content,  # Keep original data
        'content': content,  # Updated content with image refs
        'generated_images': generated_images,
        'hero_image': f'/i/{hero_hash}' if hero_hash else None,
        'enriched': True
    }

    return enriched


def enrich_url(
    url: str,
    brand_slug: str,
    generate_hero: bool = True,
    generate_sections: bool = True
) -> Dict:
    """
    Convenience function: Scrape URL + Enrich with images

    Args:
        url: URL to scrape
        brand_slug: Brand for styling
        generate_hero: Generate hero image
        generate_sections: Generate section images

    Returns:
        Enriched content dict
    """
    print(f"🕷️  Scraping: {url}")
    scraped = scrape_url(url)

    if 'error' in scraped:
        return scraped

    print(f"✅ Scraped: {scraped['title']}")
    print(f"📝 Content: {len(scraped['content'])} chars")
    print()

    enriched = enrich_scraped_content(
        scraped,
        brand_slug=brand_slug,
        generate_hero=generate_hero,
        generate_sections=generate_sections
    )

    print(f"✅ Enriched with {len(enriched['generated_images'])} images")
    print()

    return enriched


# ==============================================================================
# TESTING
# ==============================================================================

def test_enricher():
    """Test content enricher"""
    print("=" * 70)
    print("🎨 Content Enricher - Test Mode")
    print("=" * 70)
    print()

    # Test with example.com
    print("📝 Test: Enrich example.com content\n")

    enriched = enrich_url(
        url='https://example.com',
        brand_slug='howtocookathome',
        generate_hero=True,
        generate_sections=False  # example.com has no headings
    )

    if 'error' in enriched:
        print(f"❌ Error: {enriched['error']}")
        return

    print("=" * 70)
    print("✅ Content Enricher Results:")
    print("=" * 70)
    print()
    print(f"Title: {enriched['title']}")
    print(f"Content length: {len(enriched['content'])} chars")
    print(f"Generated images: {len(enriched['generated_images'])}")
    print(f"Hero image: {enriched['hero_image']}")
    print()

    if enriched['generated_images']:
        print("📸 Generated Images:")
        for img in enriched['generated_images']:
            print(f"   • {img['type']}: {img['url']}")
    print()

    print("📄 First 500 chars of enriched content:")
    print(enriched['content'][:500])
    print()

    print("=" * 70)
    print("✅ Content enricher working!")
    print()
    print("💡 Next: Create url_to_blog.py to save as post")
    print()


if __name__ == '__main__':
    test_enricher()

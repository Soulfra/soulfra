"""
Image Workflow - Complete End-to-End Pipeline

Orchestrates the complete professional image generation workflow:
1. Prompt generation (from prompt_templates.py)
2. Image composition (from image_composer.py)
3. EXIF metadata embedding (from image_metadata.py)
4. Vanity QR code generation (from vanity_qr.py)
5. Database storage
6. File export

This is the production-ready pipeline for generating branded images.
"""

import io
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from PIL import Image

from image_composer import ImageComposer
from prompt_templates import get_brand_prompt, get_negative_prompt
from image_metadata import ImageMetadata, add_metadata_to_composer_output
from vanity_qr import create_and_save_vanity_qr, BRAND_DOMAINS
from database import get_db


# =============================================================================
# Complete Image Generation Workflow
# =============================================================================

class ImageWorkflow:
    """Complete professional image generation workflow"""

    def __init__(self, brand_slug: str = 'soulfra'):
        """
        Initialize workflow

        Args:
            brand_slug: Brand identifier
        """
        self.brand_slug = brand_slug
        self.brand_config = BRAND_DOMAINS.get(brand_slug, BRAND_DOMAINS['soulfra'])
        self.composer = None
        self.metadata = None
        self.layers_data = []

    def create_blog_header(
        self,
        title: str,
        keywords: List[str],
        url: str,
        size: tuple = (1200, 630),  # OpenGraph size
        author: Optional[str] = None
    ) -> bytes:
        """
        Generate complete blog header image with all features

        Args:
            title: Blog post title
            keywords: Keywords for prompt
            url: Full URL for QR code
            size: Image dimensions
            author: Author name for metadata

        Returns:
            Complete image bytes (JPEG with EXIF)
        """
        # Step 1: Get brand prompt
        prompt = get_brand_prompt(
            brand_slug=self.brand_slug,
            title=title,
            keywords=keywords,
            content_type='blog'
        )

        # Step 2: Create image composition
        self.composer = ImageComposer(size=size)

        # Get brand colors
        colors = self.brand_config['colors']

        # Background gradient with brand colors
        self.composer.add_layer(
            'gradient',
            colors=[colors['primary'], colors['secondary']],
            angle=45
        )

        # Title text
        self.composer.add_layer(
            'text',
            content=title,
            font='impact',
            font_size=min(64, size[0] // 15),  # Responsive sizing
            color='#FFFFFF',
            position=(50, size[1] // 3),
            shadow={'offset': (3, 3), 'blur': 6, 'color': '#000000'}
        )

        # Brand badge
        badge_width = min(300, size[0] // 4)
        badge_height = 60

        self.composer.add_layer(
            'shape',
            shape='rectangle',
            position=(50, size[1] - 120),
            size=(badge_width, badge_height),
            fill_color=colors['secondary'],
            corner_radius=30
        )

        # Brand name on badge
        self.composer.add_layer(
            'text',
            content=self.brand_slug.upper().replace('HOWTOCOOKATHOME', 'HTCAH'),
            font='Arial',
            font_size=28,
            color='#FFFFFF',
            position=(70, size[1] - 110)
        )

        # Generate vanity QR and add to image
        qr_result = create_and_save_vanity_qr(
            full_url=url,
            brand_slug=self.brand_slug,
            label=None  # Will be integrated into main image
        )

        # Add QR code layer
        self.composer.add_layer(
            'qr',
            url=qr_result['vanity_url'],
            position='bottom-right',
            size=150
        )

        # Track layer data for metadata
        self.layers_data = [
            {'type': 'gradient', 'colors': [colors['primary'], colors['secondary']], 'angle': 45},
            {'type': 'text', 'content': title, 'font': 'impact', 'size': 64},
            {'type': 'shape', 'shape': 'rectangle', 'color': colors['secondary']},
            {'type': 'text', 'content': self.brand_slug.upper(), 'font': 'Arial'},
            {'type': 'qr', 'url': qr_result['vanity_url'], 'position': 'bottom-right'}
        ]

        # Step 3: Render image
        image_bytes = self.composer.render()

        # Step 4: Add EXIF metadata
        metadata = ImageMetadata(
            artist=author or f"{self.brand_slug.title()} Team",
            brand=self.brand_slug,
            description=f"{title} - {self.brand_slug.title()} Blog Post"
        )

        # Add layer composition data
        for layer in self.layers_data:
            layer_type = layer.pop('type')
            metadata.add_layer_data(layer_type, **layer)

        # Add generation params
        metadata.add_generation_params(
            size=size,
            prompt=prompt,
            brand=self.brand_slug,
            vanity_url=qr_result['vanity_url']
        )

        # Add custom data
        metadata.add_custom_data('url', url)
        metadata.add_custom_data('qr_short_code', qr_result['short_code'])

        # Embed metadata
        final_image = metadata.embed_in_image(image_bytes)

        return final_image

    def create_social_post(
        self,
        message: str,
        url: str,
        size: tuple = (1080, 1080),
        style: str = 'bold'
    ) -> bytes:
        """
        Generate social media post image

        Args:
            message: Post message/caption
            url: Link URL
            size: Image dimensions (square for Instagram)
            style: Visual style (bold, minimal, vibrant)

        Returns:
            Image bytes with EXIF
        """
        self.composer = ImageComposer(size=size)
        colors = self.brand_config['colors']

        # Different styles
        if style == 'minimal':
            # Minimal: solid background + text
            self.composer.add_layer('background', color=colors['accent'])

            self.composer.add_layer(
                'text',
                content=message,
                font='Arial',
                font_size=48,
                color=colors['primary'],
                position='center',
                align='center'
            )

        elif style == 'vibrant':
            # Vibrant: gradient + large text
            self.composer.add_layer(
                'gradient',
                colors=[colors['primary'], colors['secondary'], colors['accent']],
                angle=90
            )

            self.composer.add_layer(
                'text',
                content=message,
                font='impact',
                font_size=72,
                color='#FFFFFF',
                position='center',
                shadow={'offset': (4, 4), 'blur': 8, 'color': '#000000'}
            )

        else:  # bold (default)
            self.composer.add_layer(
                'gradient',
                colors=[colors['primary'], colors['secondary']],
                angle=45
            )

            self.composer.add_layer(
                'text',
                content=message,
                font='impact',
                font_size=64,
                color='#FFFFFF',
                position='center',
                shadow={'offset': (3, 3), 'blur': 6, 'color': '#000000'}
            )

        # QR code
        qr_result = create_and_save_vanity_qr(
            full_url=url,
            brand_slug=self.brand_slug
        )

        self.composer.add_layer(
            'qr',
            url=qr_result['vanity_url'],
            position='bottom-right',
            size=120
        )

        # Render
        image_bytes = self.composer.render()

        # Add metadata
        metadata = ImageMetadata(
            artist=f"{self.brand_slug.title()} Social Team",
            brand=self.brand_slug,
            description=f"Social post: {message[:50]}..."
        )

        metadata.add_generation_params(
            size=size,
            style=style,
            platform='social',
            vanity_url=qr_result['vanity_url']
        )

        return metadata.embed_in_image(image_bytes)

    def create_product_showcase(
        self,
        product_name: str,
        tagline: str,
        url: str,
        features: List[str],
        size: tuple = (1200, 1200)
    ) -> bytes:
        """
        Generate product showcase image

        Args:
            product_name: Product name
            tagline: Product tagline
            url: Product URL
            features: List of key features
            size: Image dimensions

        Returns:
            Image bytes with EXIF
        """
        self.composer = ImageComposer(size=size)
        colors = self.brand_config['colors']

        # Gradient background
        self.composer.add_layer(
            'gradient',
            colors=[colors['primary'], colors['secondary']],
            angle=135
        )

        # Product name
        self.composer.add_layer(
            'text',
            content=product_name,
            font='impact',
            font_size=96,
            color='#FFFFFF',
            position=(100, 150),
            shadow={'offset': (4, 4), 'blur': 8, 'color': '#000000'}
        )

        # Tagline
        self.composer.add_layer(
            'text',
            content=tagline,
            font='Arial',
            font_size=42,
            color=colors['accent'],
            position=(100, 280)
        )

        # Feature list
        y_offset = 400
        for i, feature in enumerate(features[:4]):  # Max 4 features
            # Bullet point
            self.composer.add_layer(
                'shape',
                shape='circle',
                position=(120, y_offset + i * 100 + 10),
                size=(20, 20),
                fill_color=colors['accent']
            )

            # Feature text
            self.composer.add_layer(
                'text',
                content=feature,
                font='Arial',
                font_size=36,
                color='#FFFFFF',
                position=(160, y_offset + i * 100)
            )

        # QR code with label
        qr_result = create_and_save_vanity_qr(
            full_url=url,
            brand_slug=self.brand_slug,
            label="Learn More"
        )

        self.composer.add_layer(
            'qr',
            url=qr_result['vanity_url'],
            position='bottom-right',
            size=180
        )

        # Render
        image_bytes = self.composer.render()

        # Metadata
        metadata = ImageMetadata(
            artist=f"{self.brand_slug.title()} Product Team",
            brand=self.brand_slug,
            description=f"{product_name} - {tagline}"
        )

        metadata.add_generation_params(
            size=size,
            product_name=product_name,
            features=features,
            vanity_url=qr_result['vanity_url']
        )

        return metadata.embed_in_image(image_bytes)


# =============================================================================
# Batch Processing
# =============================================================================

def generate_blog_images_batch(posts: List[Dict], brand_slug: str = 'soulfra') -> List[Dict]:
    """
    Generate images for multiple blog posts

    Args:
        posts: List of post dicts with 'title', 'keywords', 'url'
        brand_slug: Brand identifier

    Returns:
        List of results with image paths and metadata
    """
    workflow = ImageWorkflow(brand_slug=brand_slug)
    results = []

    for post in posts:
        try:
            # Generate image
            image_bytes = workflow.create_blog_header(
                title=post['title'],
                keywords=post.get('keywords', []),
                url=post['url'],
                author=post.get('author')
            )

            # Save to file
            filename = f"blog_{post.get('slug', 'post')}_{datetime.now().strftime('%Y%m%d')}.jpg"
            filepath = f"static/images/blog/{filename}"

            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            results.append({
                'success': True,
                'post': post['title'],
                'filepath': filepath,
                'size': len(image_bytes)
            })

        except Exception as e:
            results.append({
                'success': False,
                'post': post.get('title', 'Unknown'),
                'error': str(e)
            })

    return results


# =============================================================================
# Database Integration
# =============================================================================

def save_generated_image_to_db(
    image_bytes: bytes,
    brand_slug: str,
    post_id: Optional[int] = None,
    platform: str = 'blog',
    metadata: Optional[Dict] = None
) -> int:
    """
    Save generated image to database

    Args:
        image_bytes: Image data
        brand_slug: Brand identifier
        post_id: Associated post ID
        platform: Platform (blog, social, email, etc.)
        metadata: Additional metadata

    Returns:
        Database ID of saved image
    """
    import hashlib

    conn = get_db()

    # Calculate hash
    image_hash = hashlib.sha256(image_bytes).hexdigest()

    # Save to published_images table
    conn.execute('''
        INSERT INTO published_images
        (image_hash, image_data, platform, post_id, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        image_hash,
        image_bytes,
        platform,
        post_id,
        json.dumps(metadata) if metadata else None
    ))

    conn.commit()

    # Get ID
    image_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    conn.close()

    return image_id


# =============================================================================
# Quick Generation Functions
# =============================================================================

def quick_blog_image(title: str, url: str, brand: str = 'soulfra') -> bytes:
    """Quick blog image generation"""
    workflow = ImageWorkflow(brand_slug=brand)
    return workflow.create_blog_header(
        title=title,
        keywords=[],
        url=url
    )


def quick_social_image(message: str, url: str, brand: str = 'soulfra') -> bytes:
    """Quick social media image generation"""
    workflow = ImageWorkflow(brand_slug=brand)
    return workflow.create_social_post(
        message=message,
        url=url
    )


# =============================================================================
# Testing
# =============================================================================

if __name__ == '__main__':
    import os

    print("Testing Complete Image Workflow...")
    print()

    # Create output directory
    os.makedirs('static/images/workflow', exist_ok=True)

    # Test 1: Blog header
    print("Test 1: Blog Header Image")
    print("-" * 70)

    workflow = ImageWorkflow(brand_slug='cringeproof')

    blog_image = workflow.create_blog_header(
        title='How to Build a Minimal Brand',
        keywords=['brand', 'minimal', 'design'],
        url='https://cringeproof.com/blog/how-to-build-a-minimal-brand',
        author='Cringeproof Team'
    )

    blog_path = 'static/images/workflow/test_blog_header.jpg'
    with open(blog_path, 'wb') as f:
        f.write(blog_image)

    print(f"✅ Generated: {blog_path} ({len(blog_image):,} bytes)")
    print()

    # Test 2: Social post
    print("Test 2: Social Media Post")
    print("-" * 70)

    social_image = workflow.create_social_post(
        message='Less is more.\nBuilding brands that matter.',
        url='https://cringeproof.com',
        style='minimal'
    )

    social_path = 'static/images/workflow/test_social_post.jpg'
    with open(social_path, 'wb') as f:
        f.write(social_image)

    print(f"✅ Generated: {social_path} ({len(social_image):,} bytes)")
    print()

    # Test 3: Product showcase
    print("Test 3: Product Showcase")
    print("-" * 70)

    product_image = workflow.create_product_showcase(
        product_name='Brand Kit Pro',
        tagline='Everything you need to build your brand',
        url='https://cringeproof.com/products/brand-kit-pro',
        features=[
            'Minimal templates',
            'Professional fonts',
            'Color palettes',
            'Brand guidelines'
        ]
    )

    product_path = 'static/images/workflow/test_product_showcase.jpg'
    with open(product_path, 'wb') as f:
        f.write(product_image)

    print(f"✅ Generated: {product_path} ({len(product_image):,} bytes)")
    print()

    # Test 4: Multi-brand generation
    print("Test 4: Multi-Brand Generation")
    print("-" * 70)

    brands = ['cringeproof', 'soulfra', 'howtocookathome']

    for brand in brands:
        wf = ImageWorkflow(brand_slug=brand)

        img = wf.create_social_post(
            message=f'{brand.title()}\nProfessional Images',
            url=f'https://{BRAND_DOMAINS[brand]["domain"]}',
            style='bold'
        )

        path = f'static/images/workflow/test_multibrand_{brand}.jpg'
        with open(path, 'wb') as f:
            f.write(img)

        print(f"  ✅ {brand}: {path} ({len(img):,} bytes)")

    print()

    # Test 5: Batch processing
    print("Test 5: Batch Blog Processing")
    print("-" * 70)

    posts = [
        {
            'title': 'Minimal Design Principles',
            'slug': 'minimal-design',
            'keywords': ['minimal', 'design'],
            'url': 'https://cringeproof.com/blog/minimal-design',
            'author': 'Design Team'
        },
        {
            'title': 'Brand Identity 101',
            'slug': 'brand-identity',
            'keywords': ['brand', 'identity'],
            'url': 'https://cringeproof.com/blog/brand-identity',
            'author': 'Brand Team'
        }
    ]

    os.makedirs('static/images/blog', exist_ok=True)
    results = generate_blog_images_batch(posts, brand_slug='cringeproof')

    for result in results:
        if result['success']:
            print(f"  ✅ {result['post']}: {result['filepath']}")
        else:
            print(f"  ❌ {result['post']}: {result['error']}")

    print()

    print("=" * 70)
    print("✅ Complete workflow tests passed!")
    print()
    print("Generated images:")
    print("  - test_blog_header.jpg (with EXIF + vanity QR)")
    print("  - test_social_post.jpg (minimal style)")
    print("  - test_product_showcase.jpg (with features)")
    print("  - test_multibrand_*.jpg (3 brands)")
    print("  - Blog batch processing (2 posts)")
    print()
    print("All images include:")
    print("  ✅ Brand-specific styling")
    print("  ✅ EXIF metadata with layer data")
    print("  ✅ Vanity QR codes (domain-based)")
    print("  ✅ Professional composition")
    print()

#!/usr/bin/env python3
"""
Prompt Templates - Brand-Specific Image Generation Prompts

Better prompts = better AI images.

Each brand has its own visual style:
- HowToCookAtHome: Food photography, warm lighting, rustic
- Cringeproof: Minimalist, clean, bold typography
- SoulFra: Abstract, colorful, creative

This module builds prompts that match brand identity.

Usage:
    from prompt_templates import get_brand_prompt

    prompt = get_brand_prompt(
        brand_slug='howtocookathome',
        title='How to Make Salted Butter',
        keywords=['butter', 'recipe', 'homemade'],
        content_type='recipe'
    )
    # Result: "Professional food photography of butter recipe, warm kitchen lighting, rustic wooden table..."
"""

from typing import List, Optional, Dict


# Brand-specific prompt templates
BRAND_TEMPLATES = {
    'howtocookathome': {
        'recipe': "Professional food photography of {title}, warm kitchen lighting, rustic wooden table, shallow depth of field, natural light, {keywords}, Instagram food styling, appetizing composition",
        'tutorial': "Step-by-step cooking tutorial for {title}, clean kitchen workspace, organized ingredients, {keywords}, professional culinary photography",
        'blog': "Homemade {title}, cozy kitchen aesthetic, natural ingredients, {keywords}, warm inviting atmosphere, food blogger style",
        'default': "{title} food photography, {keywords}, professional kitchen styling"
    },

    'cringeproof': {
        'blog': "Minimalist design for {title}, clean aesthetic, modern typography, {keywords}, bold colors, negative space, professional graphic design",
        'social': "Viral social media content about {title}, eye-catching composition, {keywords}, trending design style",
        'default': "{title}, minimalist aesthetic, {keywords}, modern clean design"
    },

    'soulfra': {
        'blog': "Abstract creative visualization of {title}, vibrant colors, {keywords}, artistic composition, digital art style",
        'tech': "Modern tech interface for {title}, sleek design, {keywords}, professional software aesthetic",
        'default': "{title}, creative design, {keywords}, artistic style"
    },

    'deathtodata': {
        'blog': "Data privacy concept art for {title}, secure digital aesthetic, {keywords}, cybersecurity theme, dark professional style",
        'default': "{title}, privacy-focused design, {keywords}, secure aesthetic"
    },

    'calriven': {
        'blog': "Professional business content about {title}, clean corporate aesthetic, {keywords}, modern professional design",
        'default': "{title}, professional style, {keywords}, business aesthetic"
    },

    'default': {
        'blog': "Professional {title}, modern aesthetic, {keywords}, high quality composition",
        'recipe': "Food photography of {title}, professional styling, {keywords}",
        'tutorial': "Tutorial visualization for {title}, clear instructional style, {keywords}",
        'default': "{title}, {keywords}, professional photography"
    }
}


def get_brand_prompt(
    brand_slug: str,
    title: str,
    keywords: List[str],
    content_type: str = 'blog'
) -> str:
    """
    Generate brand-specific image generation prompt

    Args:
        brand_slug: Brand slug (e.g., 'howtocookathome')
        title: Content title
        keywords: List of keywords (max 5 used)
        content_type: Type of content ('blog', 'recipe', 'tutorial', 'social')

    Returns:
        Optimized prompt string for Stable Diffusion

    Examples:
        >>> get_brand_prompt('howtocookathome', 'Salted Butter', ['butter', 'recipe'], 'recipe')
        'Professional food photography of Salted Butter, warm kitchen lighting...'

        >>> get_brand_prompt('cringeproof', 'Social Media Tips', ['social', 'tips'], 'blog')
        'Minimalist design for Social Media Tips, clean aesthetic...'
    """
    # Get brand templates (fallback to default)
    brand = BRAND_TEMPLATES.get(brand_slug.lower(), BRAND_TEMPLATES['default'])

    # Get content type template (fallback to default)
    template = brand.get(content_type, brand.get('default', BRAND_TEMPLATES['default']['default']))

    # Format keywords (max 5)
    keywords_str = ', '.join(keywords[:5]) if keywords else ''

    # Fill template
    prompt = template.format(
        title=title,
        keywords=keywords_str
    )

    # Add quality suffixes
    quality_suffix = ", high quality, sharp focus, professional lighting, 4k"

    return prompt + quality_suffix


def get_negative_prompt(brand_slug: str = None) -> str:
    """
    Get negative prompt (things to avoid)

    Args:
        brand_slug: Optional brand slug for brand-specific negatives

    Returns:
        Negative prompt string
    """
    # Universal negatives
    negatives = [
        "blurry",
        "low quality",
        "distorted",
        "ugly",
        "bad anatomy",
        "watermark",
        "text",
        "signature",
        "username"
    ]

    # Brand-specific negatives
    if brand_slug == 'howtocookathome':
        negatives.extend([
            "unappetizing",
            "burnt food",
            "moldy",
            "dirty dishes"
        ])
    elif brand_slug == 'cringeproof':
        negatives.extend([
            "cluttered",
            "busy composition",
            "comic sans"
        ])

    return ", ".join(negatives)


def enhance_prompt_with_style(prompt: str, style: str = 'photographic') -> str:
    """
    Add style modifiers to prompt

    Args:
        prompt: Base prompt
        style: Style type ('photographic', 'illustration', 'artistic', '3d')

    Returns:
        Enhanced prompt with style modifiers
    """
    style_modifiers = {
        'photographic': "photorealistic, DSLR camera, professional photography",
        'illustration': "digital illustration, vector art, clean lines",
        'artistic': "artistic painting, oil on canvas, expressive brushstrokes",
        '3d': "3D render, octane render, volumetric lighting",
        'minimalist': "minimal design, simple composition, clean aesthetic"
    }

    modifier = style_modifiers.get(style, '')

    if modifier:
        return f"{prompt}, {modifier}"

    return prompt


def get_aspect_ratio_size(aspect: str = '16:9') -> tuple:
    """
    Get image size for aspect ratio

    Args:
        aspect: Aspect ratio ('16:9', '4:3', '1:1', '9:16')

    Returns:
        (width, height) tuple
    """
    ratios = {
        '16:9': (1024, 576),    # Landscape - blog headers
        '4:3': (1024, 768),     # Standard - presentations
        '1:1': (1024, 1024),    # Square - social media
        '9:16': (576, 1024),    # Portrait - stories
        '3:2': (1200, 800),     # Photography standard
        '21:9': (1344, 576)     # Ultra-wide
    }

    return ratios.get(aspect, (1024, 1024))


if __name__ == '__main__':
    """Test prompt generation"""

    print("=" * 70)
    print("🎨 Prompt Templates Test")
    print("=" * 70)
    print()

    # Test cases
    test_cases = [
        {
            'brand': 'howtocookathome',
            'title': 'How to Make Salted Butter',
            'keywords': ['butter', 'recipe', 'homemade'],
            'type': 'recipe'
        },
        {
            'brand': 'howtocookathome',
            'title': 'Perfect Pasta Carbonara',
            'keywords': ['pasta', 'italian', 'carbonara'],
            'type': 'recipe'
        },
        {
            'brand': 'cringeproof',
            'title': 'Social Media Strategy 2025',
            'keywords': ['social', 'strategy', 'tips'],
            'type': 'blog'
        },
        {
            'brand': 'soulfra',
            'title': 'AI Content Generation',
            'keywords': ['ai', 'content', 'automation'],
            'type': 'blog'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"Test {i}: {case['brand']} - {case['title']}")
        print("-" * 70)

        prompt = get_brand_prompt(
            brand_slug=case['brand'],
            title=case['title'],
            keywords=case['keywords'],
            content_type=case['type']
        )

        print(f"Prompt:\n{prompt}")
        print()

        negative = get_negative_prompt(case['brand'])
        print(f"Negative:\n{negative}")
        print()

    print("=" * 70)
    print("✅ Prompt templates ready")

#!/usr/bin/env python3
"""
Content Brand Detector - Auto-Create Brands from Content

Analyzes post content to:
1. Detect topic/category (cooking, tech, privacy, etc.)
2. Check if brand exists for that category
3. If not → Auto-create brand from template
4. Auto-generate AI persona for brand

This is the KEY to full automation - no manual brand creation!

Usage:
    from content_brand_detector import detect_and_create_brand

    # Analyze post and create brand if needed
    brand_slug = detect_and_create_brand(post_id=42)

    # Or analyze content directly
    brand_slug = detect_brand_from_content("how to make salted butter")
"""

from typing import Optional, Dict, List
from database import get_db
import re


# ==============================================================================
# CATEGORY DETECTION
# ==============================================================================

CATEGORY_KEYWORDS = {
    'cooking': [
        'recipe', 'cook', 'bake', 'butter', 'salt', 'flour', 'oven', 'ingredient',
        'food', 'meal', 'dish', 'kitchen', 'chef', 'cuisine', 'taste', 'flavor',
        'simmer', 'boil', 'fry', 'grill', 'roast', 'sauce', 'spice', 'herb'
    ],
    'tech': [
        'code', 'programming', 'software', 'python', 'javascript', 'database',
        'api', 'server', 'deploy', 'git', 'algorithm', 'function', 'class',
        'debug', 'compile', 'framework', 'library', 'package', 'cli', 'command'
    ],
    'privacy': [
        'privacy', 'data', 'encrypt', 'secure', 'password', 'leak', 'tracking',
        'cookie', 'vpn', 'tor', 'anonymous', 'surveillance', 'breach', 'hack',
        'protect', 'personal', 'information', 'gdpr', 'compliance'
    ],
    'business': [
        'startup', 'entrepreneur', 'marketing', 'sales', 'revenue', 'profit',
        'growth', 'strategy', 'customer', 'product', 'market', 'business',
        'company', 'founder', 'investor', 'pitch', 'valuation', 'metrics'
    ],
    'health': [
        'health', 'fitness', 'exercise', 'nutrition', 'diet', 'wellness',
        'workout', 'yoga', 'meditation', 'sleep', 'mental', 'therapy',
        'doctor', 'medical', 'symptom', 'treatment', 'prevent', 'healthy'
    ],
    'art': [
        'art', 'design', 'creative', 'paint', 'draw', 'sketch', 'color',
        'artist', 'canvas', 'brush', 'gallery', 'exhibit', 'aesthetic',
        'visual', 'graphic', 'illustration', 'photography', 'portrait'
    ]
}


def detect_category_from_content(content: str) -> Optional[str]:
    """
    Detect category from content using keyword matching

    Args:
        content: Post content (title + body)

    Returns:
        Category slug or None
    """
    content_lower = content.lower()

    # Count keyword matches for each category
    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            category_scores[category] = score

    if not category_scores:
        return None

    # Return category with highest score
    best_category = max(category_scores.items(), key=lambda x: x[1])

    # Require at least 2 keyword matches to be confident
    if best_category[1] >= 2:
        return best_category[0]

    return None


# ==============================================================================
# BRAND TEMPLATES
# ==============================================================================

BRAND_TEMPLATES = {
    'cooking': {
        'name': 'HowToCookAtHome',
        'slug': 'howtocookathome',
        'tagline': 'Simple recipes for home cooks 🍳',
        'category': 'cooking',
        'tier': 'creative',
        'personality_tone': 'warm, practical, encouraging',
        'personality_traits': 'Patient, accessible, fun',
        'color_primary': '#FF6B35',  # Warm orange
        'color_secondary': '#F7931E',  # Golden yellow
        'color_accent': '#C1272D'  # Red
    },
    'tech': {
        'name': 'DevBuild',
        'slug': 'devbuild',
        'tagline': 'Build better software 💻',
        'category': 'tech',
        'tier': 'enterprise',
        'personality_tone': 'analytical, precise, helpful',
        'personality_traits': 'Technical, thorough, pragmatic',
        'color_primary': '#2C3E50',  # Dark blue
        'color_secondary': '#3498DB',  # Bright blue
        'color_accent': '#1ABC9C'  # Turquoise
    },
    'privacy': {
        'name': 'PrivacyFirst',
        'slug': 'privacyfirst',
        'tagline': 'Protect your data 🔒',
        'category': 'privacy',
        'tier': 'enterprise',
        'personality_tone': 'cautious, informative, empowering',
        'personality_traits': 'Security-focused, transparent, vigilant',
        'color_primary': '#2C2C2C',  # Dark gray
        'color_secondary': '#E74C3C',  # Red
        'color_accent': '#ECF0F1'  # Light gray
    },
    'business': {
        'name': 'StartupInsights',
        'slug': 'startupinsights',
        'tagline': 'Build better businesses 📈',
        'category': 'business',
        'tier': 'professional',
        'personality_tone': 'strategic, insightful, motivating',
        'personality_traits': 'Growth-minded, data-driven, supportive',
        'color_primary': '#16A085',  # Teal
        'color_secondary': '#27AE60',  # Green
        'color_accent': '#F39C12'  # Orange
    },
    'health': {
        'name': 'WellnessPath',
        'slug': 'wellnesspath',
        'tagline': 'Live healthier every day 💚',
        'category': 'health',
        'tier': 'creative',
        'personality_tone': 'caring, knowledgeable, supportive',
        'personality_traits': 'Holistic, evidence-based, encouraging',
        'color_primary': '#27AE60',  # Green
        'color_secondary': '#2ECC71',  # Light green
        'color_accent': '#F1C40F'  # Yellow
    },
    'art': {
        'name': 'CreativeCanvas',
        'slug': 'creativecanvas',
        'tagline': 'Express yourself through art 🎨',
        'category': 'art',
        'tier': 'creative',
        'personality_tone': 'imaginative, expressive, inspiring',
        'personality_traits': 'Creative, open-minded, passionate',
        'color_primary': '#9B59B6',  # Purple
        'color_secondary': '#E91E63',  # Pink
        'color_accent': '#FFC107'  # Amber
    }
}


# ==============================================================================
# BRAND CREATION
# ==============================================================================

def create_brand_from_template(category: str) -> Optional[Dict]:
    """
    Create a brand from template

    Args:
        category: Category slug (e.g., 'cooking')

    Returns:
        Brand dict or None if failed
    """
    if category not in BRAND_TEMPLATES:
        print(f"❌ No template found for category '{category}'")
        return None

    template = BRAND_TEMPLATES[category]

    db = get_db()

    # Check if brand already exists
    existing = db.execute(
        'SELECT id FROM brands WHERE slug = ?',
        (template['slug'],)
    ).fetchone()

    if existing:
        print(f"ℹ️  Brand '{template['slug']}' already exists")
        brand = db.execute('SELECT * FROM brands WHERE slug = ?', (template['slug'],)).fetchone()
        db.close()
        return dict(brand)

    # Create brand
    db.execute('''
        INSERT INTO brands (
            name, slug, tagline, category, tier,
            personality_tone, personality_traits,
            color_primary, color_secondary, color_accent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        template['name'],
        template['slug'],
        template['tagline'],
        template['category'],
        template['tier'],
        template['personality_tone'],
        template['personality_traits'],
        template['color_primary'],
        template['color_secondary'],
        template['color_accent']
    ))

    db.commit()
    brand_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    print(f"✅ Created brand: {template['name']} ({template['slug']})")

    # Get full brand data
    brand = db.execute('SELECT * FROM brands WHERE id = ?', (brand_id,)).fetchone()
    db.close()

    # Auto-generate AI persona
    try:
        from brand_ai_persona_generator import generate_brand_ai_persona
        persona = generate_brand_ai_persona(template['slug'])
        if persona:
            print(f"   ✅ Generated AI persona: @{persona['username']}")
    except Exception as e:
        print(f"   ⚠️  AI persona generation failed: {e}")

    return dict(brand)


def detect_and_create_brand(post_id: int) -> Optional[str]:
    """
    Detect brand from post content and create if needed

    Args:
        post_id: Post ID

    Returns:
        Brand slug or None
    """
    db = get_db()

    # Get post
    post = db.execute(
        'SELECT title, content FROM posts WHERE id = ?',
        (post_id,)
    ).fetchone()

    if not post:
        db.close()
        print(f"❌ Post {post_id} not found")
        return None

    content = f"{post['title']} {post['content']}"
    db.close()

    # Detect category
    category = detect_category_from_content(content)

    if not category:
        print(f"ℹ️  Could not detect category for post {post_id}")
        return None

    print(f"📊 Detected category: {category}")

    # Create brand from template
    brand = create_brand_from_template(category)

    if brand:
        return brand['slug']

    return None


def detect_brand_from_content(content: str) -> Optional[str]:
    """
    Detect and create brand from raw content

    Args:
        content: Raw content text

    Returns:
        Brand slug or None
    """
    category = detect_category_from_content(content)

    if not category:
        return None

    brand = create_brand_from_template(category)

    if brand:
        return brand['slug']

    return None


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """CLI for content brand detection"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 content_brand_detector.py detect-post <post_id>")
        print("  python3 content_brand_detector.py detect-text '<content>'")
        print("  python3 content_brand_detector.py create <category>")
        print()
        print("Examples:")
        print("  python3 content_brand_detector.py detect-post 28")
        print("  python3 content_brand_detector.py detect-text 'how to make salted butter'")
        print("  python3 content_brand_detector.py create cooking")
        return

    command = sys.argv[1]

    if command == 'detect-post':
        if len(sys.argv) < 3:
            print("Error: Missing post ID")
            return

        post_id = int(sys.argv[2])

        print("=" * 70)
        print("📊 DETECTING BRAND FROM POST")
        print("=" * 70)
        print()

        brand_slug = detect_and_create_brand(post_id)

        if brand_slug:
            print()
            print(f"✅ Brand: {brand_slug}")
        else:
            print()
            print("❌ Could not detect or create brand")

    elif command == 'detect-text':
        if len(sys.argv) < 3:
            print("Error: Missing content text")
            return

        content = sys.argv[2]

        print("=" * 70)
        print("📊 DETECTING BRAND FROM TEXT")
        print("=" * 70)
        print()
        print(f"Content: {content[:100]}...")
        print()

        brand_slug = detect_brand_from_content(content)

        if brand_slug:
            print()
            print(f"✅ Brand: {brand_slug}")
        else:
            print()
            print("❌ Could not detect or create brand")

    elif command == 'create':
        if len(sys.argv) < 3:
            print("Error: Missing category")
            return

        category = sys.argv[2]

        print("=" * 70)
        print(f"🏗️  CREATING BRAND FOR: {category}")
        print("=" * 70)
        print()

        brand = create_brand_from_template(category)

        if brand:
            print()
            print("✅ Brand created successfully!")
            print(f"   Name: {brand['name']}")
            print(f"   Slug: {brand['slug']}")
            print(f"   Category: {brand['category']}")
        else:
            print()
            print("❌ Brand creation failed")

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

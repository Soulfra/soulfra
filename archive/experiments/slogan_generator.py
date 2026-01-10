#!/usr/bin/env python3
"""
Slogan Generator - Human-Driven, Not AI-Generated

Takes brand personalities + trending keywords and generates slogans using
simple string templates. NO LLM - just "thinking what's funny" as the user wanted.

Formula: brand.tagline + trending_keyword + personality_twist
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from trending_detector import extract_keywords_from_trending, get_trending_posts


def get_db() -> sqlite3.Connection:
    """Get database connection with Row factory."""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_all_brands() -> List[Dict[str, Any]]:
    """Get all brands from database."""
    conn = get_db()
    cursor = conn.cursor()

    rows = cursor.execute('''
        SELECT id, name, slug, tagline, category, tier,
               color_primary, color_secondary, color_accent,
               personality_tone, personality_traits, ai_style
        FROM brands
        ORDER BY id
    ''').fetchall()

    conn.close()

    brands = []
    for row in rows:
        brand = dict(row)
        # Parse personality_traits from JSON
        if brand['personality_traits']:
            try:
                brand['personality_traits'] = json.loads(brand['personality_traits'])
            except:
                brand['personality_traits'] = []
        brands.append(brand)

    return brands


def generate_slogans_for_brand(brand: Dict[str, Any], keywords: List[str]) -> List[str]:
    """
    Generate slogans for a brand based on trending keywords.

    Uses simple templates based on brand personality - NO LLM.

    Args:
        brand: Brand dict with tagline, name, personality_tone
        keywords: List of trending keywords

    Returns:
        List of slogan strings
    """
    slogans = []
    tagline = brand['tagline']
    brand_name = brand['name']
    tone = brand['personality_tone']

    # Template variations based on brand personality
    templates = []

    if 'Soulfra' in brand_name:
        # Security/privacy focused
        templates = [
            tagline + " (Even your {}.)",
            "{}: Encrypted. " + tagline,
            "Your {}. Your keys. No exceptions.",
            tagline + " Zero {} tracking.",
        ]

    elif 'DeathToData' in brand_name:
        # Anti-surveillance focused
        templates = [
            "{} without surveillance. " + tagline,
            "Google tracks your {}. We don't. " + tagline,
            "Big Tech wants your {}. We want freedom.",
            "Death to {} tracking.",
        ]

    elif 'Calriven' in brand_name:
        # AI/reasoning focused
        templates = [
            tagline + " Now with {} reasoning.",
            "{} intelligence. Zero hallucinations.",
            "Local {} models. " + tagline,
            "{} AI that actually works.",
        ]

    elif 'FinishThisIdea' in brand_name:
        # Motivation/completion focused
        templates = [
            "That {} project? Let's ship it.",
            tagline + " Your {} idea deserves to be done.",
            "{} projects finished. Finally.",
            "Stop planning {}, start shipping.",
        ]

    elif 'FinishThisRepo' in brand_name:
        # Code completion focused
        templates = [
            "{} code not done? We'll finish it.",
            "Your {} repo: 3 commits from done.",
            tagline + " {} edition.",
            "Merge that {} PR already.",
        ]

    elif 'IPOMyAgent' in brand_name:
        # Business/market focused
        templates = [
            "Your {} agent is worth $$$.",
            "{} market just opened. " + tagline,
            "Monetize your {} skills.",
            "{} as a service. " + tagline,
        ]

    elif 'HollowTown' in brand_name:
        # Retro/nostalgic focused
        templates = [
            "{} in glorious 8-bit.",
            "Remember {}? We do. " + tagline,
            "{} meets 1985.",
            "Pixel perfect {}.",
        ]

    elif 'ColdStartKit' in brand_name:
        # Fast/starter focused
        templates = [
            "{} starter kit. Ship in hours.",
            tagline + " {} edition.",
            "Zero to {} in 10 minutes.",
            "{} boilerplate. Just add code.",
        ]

    elif 'BrandAidKit' in brand_name:
        # Design focused
        templates = [
            "{} designs. No agency prices.",
            tagline + " {} edition.",
            "Beautiful {} without the BS.",
            "{} branding made simple.",
        ]

    elif 'DealOrDelete' in brand_name:
        # Decision focused
        templates = [
            "Ship {} or kill it. No limbo.",
            "{} decision: Binary. " + tagline,
            "Your {} project: Ship or delete?",
            "{} indecision ends here.",
        ]

    elif 'SaveOrSink' in brand_name:
        # Emergency focused
        templates = [
            "{} outage? We got you.",
            "3am {} emergency? " + tagline,
            "{} broke? We'll fix it.",
            "Emergency {} rescue.",
        ]

    elif 'CringeProof' in brand_name:
        # Review focused
        templates = [
            "Don't post that {}. Seriously.",
            "{} review before you cringe.",
            "{} saved from embarrassment.",
            "That {} post? Let's workshop it.",
        ]

    else:
        # Generic templates
        templates = [
            tagline + " {} edition.",
            "{} made better.",
            "Your {} solution.",
        ]

    # Generate slogans by filling templates with keywords
    for template in templates:
        for keyword in keywords[:5]:  # Top 5 keywords per brand
            try:
                slogan = template.format(keyword.title())
                slogans.append(slogan)
            except:
                pass  # Skip if template doesn't have {}

    return slogans[:10]  # Return top 10 slogans per brand


def generate_all_slogans() -> Dict[str, List[str]]:
    """
    Generate slogans for all brands based on current trending keywords.

    Returns:
        Dict mapping brand_name to list of slogans
    """
    brands = get_all_brands()
    keywords = extract_keywords_from_trending()

    all_slogans = {}

    for brand in brands:
        slogans = generate_slogans_for_brand(brand, keywords)
        all_slogans[brand['name']] = slogans

    return all_slogans


def generate_product_names(brand: Dict[str, Any], keyword: str) -> List[str]:
    """
    Generate product names combining brand + keyword.

    Examples:
    - "Soulfra Privacy T-Shirt"
    - "DeathToData Reasoning Poster"
    - "FinishThisIdea Ollama Sticker"

    Args:
        brand: Brand dict
        keyword: Trending keyword

    Returns:
        List of product names
    """
    brand_name = brand['name']
    keyword_title = keyword.title()

    names = [
        f"{brand_name} {keyword_title} T-Shirt",
        f"{brand_name} {keyword_title} Poster",
        f"{brand_name} {keyword_title} Sticker",
        f"{brand_name} {keyword_title} Mug",
        f"{brand_name} {keyword_title} Hoodie",
    ]

    return names


def match_brands_to_keywords() -> List[Dict[str, Any]]:
    """
    Match trending keywords to relevant brands.

    Uses existing brand_posts classification to find best matches.

    Returns:
        List of dicts with brand_name, keyword, relevance_score, slogan
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get trending posts
    trending_posts = get_trending_posts(limit=10)

    matches = []

    for post in trending_posts:
        # Get brands associated with this post
        brands = cursor.execute('''
            SELECT b.name, b.tagline, bp.relevance_score
            FROM brand_posts bp
            JOIN brands b ON bp.brand_id = b.id
            WHERE bp.post_id = ?
            ORDER BY bp.relevance_score DESC
            LIMIT 3
        ''', (post['post_id'],)).fetchall()

        # Extract simple keyword from post title
        title_words = post['title'].lower().split()
        keyword = title_words[0] if title_words else 'tech'

        for brand in brands:
            brand_dict = {
                'name': brand['name'],
                'tagline': brand['tagline'],
                'personality_tone': '',
                'personality_traits': []
            }
            slogans = generate_slogans_for_brand(brand_dict, [keyword])

            matches.append({
                'brand_name': brand['name'],
                'keyword': keyword,
                'relevance_score': brand['relevance_score'],
                'slogan': slogans[0] if slogans else f"{brand['tagline']} {keyword}",
                'post_title': post['title']
            })

    conn.close()

    return matches


if __name__ == '__main__':
    print("💡 Slogan Generator (Human-Driven, No AI)\n")

    # Test with current trending keywords
    print("🔑 Current Trending Keywords:")
    keywords = extract_keywords_from_trending()[:10]
    print(f"  {', '.join(keywords)}")
    print()

    # Generate slogans for all brands
    print("🎨 Generated Slogans by Brand:\n")
    all_slogans = generate_all_slogans()

    for brand_name, slogans in all_slogans.items():
        if slogans:  # Only show brands with slogans
            print(f"{brand_name}:")
            for i, slogan in enumerate(slogans[:3], 1):  # Show top 3
                print(f"  {i}. {slogan}")
            print()

    # Show brand-keyword matches
    print("🎯 Best Brand-Keyword Matches:\n")
    matches = match_brands_to_keywords()

    for i, match in enumerate(matches[:10], 1):
        print(f"{i}. {match['brand_name']} × {match['keyword']}")
        print(f"   Slogan: \"{match['slogan']}\"")
        print(f"   Source: {match['post_title'][:50]}...")
        print()

    print("✅ Slogan generation complete!")

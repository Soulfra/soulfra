#!/usr/bin/env python3
"""
Classify existing posts by brand based on content analysis.

Strategy:
1. Extract keywords from post title + content
2. Match keywords to brand categories/personalities
3. Populate brand_posts table with relevance scores
4. Generate summary statistics

This creates the training data foundation for brand-specific ML models.
"""

import sqlite3
import re
from collections import defaultdict


# Brand keyword mappings (extracted from brand personalities)
BRAND_KEYWORDS = {
    'Soulfra': {
        'keywords': ['privacy', 'security', 'encryption', 'identity', 'keys', 'cryptography',
                     'sovereignty', 'self-sovereign', 'trust', 'auth', 'soulfra'],
        'weight': 1.0
    },
    'DeathToData': {
        'keywords': ['surveillance', 'google', 'facebook', 'privacy', 'tracking', 'data',
                     'big tech', 'anti', 'resist', 'freedom', 'search'],
        'weight': 1.0
    },
    'Calriven': {
        'keywords': ['ai', 'llm', 'model', 'reasoning', 'intelligence', 'machine learning',
                     'neural', 'algorithm', 'optimization', 'calriven', 'ollama'],
        'weight': 1.0
    },
    'FinishThisIdea': {
        'keywords': ['unfinished', 'complete', 'finish', 'todo', 'project', 'idea',
                     'motivation', 'productivity', 'ship'],
        'weight': 0.8
    },
    'FinishThisRepo': {
        'keywords': ['code', 'repo', 'git', 'commit', 'pull request', 'refactor',
                     'bug', 'feature', 'implementation', 'development'],
        'weight': 0.8
    },
    'IPOMyAgent': {
        'keywords': ['agent', 'market', 'trade', 'business', 'value', 'asset',
                     'investment', 'monetize', 'revenue'],
        'weight': 0.7
    },
    'HollowTown': {
        'keywords': ['pixel', '8-bit', 'retro', 'game', 'nostalgia', 'vintage',
                     'arcade', 'gaming'],
        'weight': 0.6
    },
    'ColdStartKit': {
        'keywords': ['template', 'boilerplate', 'starter', 'quick', 'fast',
                     'bootstrap', 'scaffold'],
        'weight': 0.7
    },
    'BrandAidKit': {
        'keywords': ['design', 'brand', 'color', 'logo', 'visual', 'creative',
                     'aesthetic', 'style'],
        'weight': 0.6
    },
    'DealOrDelete': {
        'keywords': ['decide', 'choice', 'decision', 'binary', 'yes', 'no',
                     'kill', 'ship'],
        'weight': 0.7
    },
    'SaveOrSink': {
        'keywords': ['rescue', 'emergency', 'outage', 'debug', 'fix', 'crash',
                     'incident', '3am', 'help'],
        'weight': 0.7
    },
    'CringeProof': {
        'keywords': ['cringe', 'review', 'feedback', 'honest', 'critique',
                     'mistake', 'embarrass', 'post'],
        'weight': 0.6
    }
}


def extract_text_from_html(html):
    """Simple HTML tag remover (not perfect but good enough)."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def calculate_relevance_score(text, brand_keywords):
    """
    Calculate relevance score (0.0 to 1.0) for a text to a brand.

    Uses simple keyword matching with normalization.
    """
    text_lower = text.lower()
    matches = 0
    total_keywords = len(brand_keywords['keywords'])

    for keyword in brand_keywords['keywords']:
        if keyword.lower() in text_lower:
            matches += 1

    if total_keywords == 0:
        return 0.0

    # Base score: percentage of keywords matched
    base_score = matches / total_keywords

    # Apply brand weight
    weighted_score = base_score * brand_keywords['weight']

    # Cap at 1.0
    return min(weighted_score, 1.0)


def classify_posts():
    """Classify all posts and populate brand_posts table."""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    print("🧠 Brand Classification System\n")

    # Get all brands
    cursor.execute("SELECT id, name FROM brands ORDER BY id")
    brands = {row['name']: row['id'] for row in cursor.fetchall()}

    print(f"📊 Loaded {len(brands)} brands")

    # Get all posts
    cursor.execute("SELECT id, title, content FROM posts ORDER BY id")
    posts = cursor.fetchall()

    print(f"📝 Found {len(posts)} posts\n")

    # Clear existing brand_posts entries
    cursor.execute("DELETE FROM brand_posts")
    print("🗑️  Cleared existing brand classifications\n")

    brand_post_counts = defaultdict(int)
    total_classifications = 0

    for post in posts:
        post_id = post['id']
        title = post['title']
        content = extract_text_from_html(post['content'])
        full_text = f"{title} {content}"

        print(f"Post {post_id}: {title[:60]}...")

        # Calculate relevance scores for each brand
        brand_scores = {}

        for brand_name, brand_keywords in BRAND_KEYWORDS.items():
            if brand_name not in brands:
                continue  # Skip if brand not in database

            score = calculate_relevance_score(full_text, brand_keywords)
            brand_scores[brand_name] = score

        # Sort by score descending
        sorted_brands = sorted(brand_scores.items(), key=lambda x: x[1], reverse=True)

        # Insert top 3 brands with score > 0.0
        for brand_name, score in sorted_brands[:3]:
            if score > 0.0:
                brand_id = brands[brand_name]

                cursor.execute("""
                    INSERT INTO brand_posts (brand_id, post_id, relevance_score)
                    VALUES (?, ?, ?)
                """, (brand_id, post_id, score))

                print(f"  → {brand_name}: {score:.2f}")
                brand_post_counts[brand_name] += 1
                total_classifications += 1

        if not any(score > 0.0 for _, score in sorted_brands):
            print("  → No brand match")

        print()

    db.commit()
    db.close()

    print("📊 Classification Summary:")
    print(f"   Total posts classified: {len(posts)}")
    print(f"   Total brand-post links: {total_classifications}")
    print()
    print("   Posts per brand:")
    for brand_name in sorted(brand_post_counts.keys()):
        count = brand_post_counts[brand_name]
        print(f"     {brand_name}: {count} posts")


if __name__ == '__main__':
    classify_posts()

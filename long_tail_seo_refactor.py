#!/usr/bin/env python3
"""
Long-Tail SEO Refactor - Broad to Micro-Niche

Start with broad, expensive keywords → Refactor to specific, cheap keywords

Philosophy: Digital twin content refactoring
- Start: "AI tools" (10,000 searches/mo, $5 CPC, impossible to rank)
- Refactor: "AI tools for solopreneurs building SaaS in 2024" (100 searches/mo, $0.50 CPC, rankable)

Like ICP (Internet Computer Protocol) but for content:
- Every article has a digital twin
- Twins get progressively more specific
- Each twin targets a micro-niche
- Eventually you own entire long-tail categories

Example refactor chain:
1. "Cooking" → broad, competitive
2. "Cooking at home" → narrower
3. "Cooking at home on a budget" → more specific
4. "Cooking at home on a budget with 3 ingredients" → micro-niche (rankable!)

Then you own:
- howtocookathome.com (broad)
- howtocookathomeonabudget.com (specific)
- 3ingredientmeals.com (micro)
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from database import get_db
import json

# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_seo_refactor_tables():
    """Initialize SEO refactor tables"""
    conn = get_db()

    # Keyword research
    conn.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL,
            search_volume INTEGER DEFAULT 0,
            cpc REAL DEFAULT 0.0,
            competition REAL DEFAULT 0.0,
            difficulty INTEGER DEFAULT 0,
            parent_keyword_id INTEGER,
            specificity_level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_keyword_id) REFERENCES keywords(id)
        )
    ''')

    # Content variations (digital twins)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS content_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_content_id INTEGER,
            keyword_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            content_text TEXT NOT NULL,
            specificity_level INTEGER DEFAULT 1,
            target_audience TEXT,
            variation_type TEXT DEFAULT 'refactor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (original_content_id) REFERENCES content_variations(id),
            FOREIGN KEY (keyword_id) REFERENCES keywords(id)
        )
    ''')

    # SEO performance tracking
    conn.execute('''
        CREATE TABLE IF NOT EXISTS seo_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_variation_id INTEGER NOT NULL,
            date DATE NOT NULL,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            position REAL DEFAULT 0.0,
            ctr REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_variation_id) REFERENCES content_variations(id),
            UNIQUE(content_variation_id, date)
        )
    ''')

    # Refactor chains (track evolution from broad → specific)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS refactor_chains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_name TEXT NOT NULL,
            root_keyword_id INTEGER NOT NULL,
            depth INTEGER DEFAULT 0,
            total_variations INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (root_keyword_id) REFERENCES keywords(id)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# KEYWORD REFACTORING
# ==============================================================================

def refactor_keyword(
    broad_keyword: str,
    modifiers: List[str] = None,
    auto_generate: bool = True
) -> List[Dict]:
    """
    Refactor broad keyword into specific variants

    Args:
        broad_keyword: Broad keyword (e.g., "cooking")
        modifiers: Manual modifiers (e.g., ["at home", "on a budget"])
        auto_generate: Auto-generate variations using AI

    Returns:
        List of refactored keywords with SEO metrics
    """

    conn = get_db()

    # Get or create broad keyword
    existing = conn.execute(
        'SELECT id FROM keywords WHERE keyword = ?',
        (broad_keyword,)
    ).fetchone()

    if existing:
        broad_keyword_id = existing['id']
    else:
        cursor = conn.execute('''
            INSERT INTO keywords (keyword, specificity_level)
            VALUES (?, 1)
        ''', (broad_keyword,))
        broad_keyword_id = cursor.lastrowid

    refactored = []

    # Manual modifiers
    if modifiers:
        for i, modifier in enumerate(modifiers, start=2):
            specific_keyword = f"{broad_keyword} {modifier}"

            cursor = conn.execute('''
                INSERT OR IGNORE INTO keywords (
                    keyword, parent_keyword_id, specificity_level
                ) VALUES (?, ?, ?)
            ''', (specific_keyword, broad_keyword_id, i))

            keyword_id = cursor.lastrowid or conn.execute(
                'SELECT id FROM keywords WHERE keyword = ?',
                (specific_keyword,)
            ).fetchone()['id']

            refactored.append({
                'keyword_id': keyword_id,
                'keyword': specific_keyword,
                'specificity_level': i,
                'parent': broad_keyword
            })

    # Auto-generate variations
    if auto_generate:
        from local_ollama_client import OllamaClient

        client = OllamaClient()

        if client.is_running():
            prompt = f"""Generate 10 increasingly specific keyword variations for: "{broad_keyword}"

Start broad, end hyper-specific (long-tail).

Output JSON array only:
[
  "{broad_keyword} at home",
  "{broad_keyword} at home on a budget",
  "{broad_keyword} at home on a budget with 3 ingredients",
  ...
]"""

            result = client.generate(
                prompt=prompt,
                model='mistral:7b',
                temperature=0.7
            )

            response_text = result.get('response', '')

            # Parse JSON
            try:
                if '[' in response_text and ']' in response_text:
                    json_start = response_text.index('[')
                    json_end = response_text.rindex(']') + 1
                    json_text = response_text[json_start:json_end]

                    variations = json.loads(json_text)

                    for i, variation in enumerate(variations, start=2):
                        cursor = conn.execute('''
                            INSERT OR IGNORE INTO keywords (
                                keyword, parent_keyword_id, specificity_level
                            ) VALUES (?, ?, ?)
                        ''', (variation, broad_keyword_id, i))

                        keyword_id = cursor.lastrowid or conn.execute(
                            'SELECT id FROM keywords WHERE keyword = ?',
                            (variation,)
                        ).fetchone()['id']

                        refactored.append({
                            'keyword_id': keyword_id,
                            'keyword': variation,
                            'specificity_level': i,
                            'parent': broad_keyword,
                            'source': 'ai_generated'
                        })
            except:
                pass

    conn.commit()
    conn.close()

    return refactored


# ==============================================================================
# CONTENT VARIATION GENERATION
# ==============================================================================

def generate_content_variation(
    original_content: str,
    target_keyword: str,
    specificity_level: int,
    target_audience: str = None
) -> Dict:
    """
    Generate content variation for specific keyword

    Args:
        original_content: Original broad content
        target_keyword: Specific keyword to target
        specificity_level: How specific (1=broad, 10=hyper-specific)
        target_audience: Optional audience description

    Returns:
        {
            'variation_id': int,
            'title': str,
            'slug': str,
            'content': str,
            'keyword': str
        }
    """

    from local_ollama_client import OllamaClient

    client = OllamaClient()

    if not client.is_running():
        return {'error': 'Ollama not running'}

    # Generate variation using AI
    system_prompt = f"""You are an SEO content writer. Rewrite content to target specific keywords.

Specificity level: {specificity_level}/10
Target keyword: "{target_keyword}"
Target audience: {target_audience or 'general'}

Make content MORE specific and targeted. Keep same core ideas but tailor to the exact niche.

Output JSON:
{{
    "title": "SEO-optimized title with target keyword",
    "slug": "url-friendly-slug",
    "content": "Full rewritten content (markdown)",
    "meta_description": "150 char meta description"
}}"""

    prompt = f"""Rewrite this content for the keyword "{target_keyword}":

{original_content[:2000]}

Output JSON only:"""

    result = client.generate(
        prompt=prompt,
        model='mistral:7b',
        system=system_prompt,
        temperature=0.7
    )

    response_text = result.get('response', '')

    # Parse JSON
    try:
        if '{' in response_text and '}' in response_text:
            json_start = response_text.index('{')
            json_end = response_text.rindex('}') + 1
            json_text = response_text[json_start:json_end]

            variation_data = json.loads(json_text)

            # Save to database
            conn = get_db()

            # Get keyword ID
            keyword = conn.execute(
                'SELECT id FROM keywords WHERE keyword = ?',
                (target_keyword,)
            ).fetchone()

            if not keyword:
                # Create keyword
                cursor = conn.execute('''
                    INSERT INTO keywords (keyword, specificity_level)
                    VALUES (?, ?)
                ''', (target_keyword, specificity_level))
                keyword_id = cursor.lastrowid
            else:
                keyword_id = keyword['id']

            # Create variation
            cursor = conn.execute('''
                INSERT INTO content_variations (
                    keyword_id, title, slug, content_text,
                    specificity_level, target_audience
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                keyword_id,
                variation_data['title'],
                variation_data['slug'],
                variation_data['content'],
                specificity_level,
                target_audience
            ))

            variation_id = cursor.lastrowid

            conn.commit()
            conn.close()

            return {
                'variation_id': variation_id,
                'title': variation_data['title'],
                'slug': variation_data['slug'],
                'content': variation_data['content'],
                'keyword': target_keyword,
                'meta_description': variation_data.get('meta_description', '')
            }
    except Exception as e:
        return {'error': str(e), 'raw_response': response_text}


# ==============================================================================
# REFACTOR CHAIN BUILDER
# ==============================================================================

def build_refactor_chain(
    root_keyword: str,
    depth: int = 5,
    original_content: str = None
) -> Dict:
    """
    Build complete refactor chain from broad → micro-niche

    Args:
        root_keyword: Starting broad keyword
        depth: How many levels of specificity
        original_content: Original content to refactor

    Returns:
        {
            'chain_id': int,
            'root_keyword': str,
            'variations': List[Dict],
            'total_variations': int
        }
    """

    conn = get_db()

    # Refactor keyword
    keyword_variations = refactor_keyword(root_keyword, auto_generate=True)

    # Create chain
    root_keyword_record = conn.execute(
        'SELECT id FROM keywords WHERE keyword = ?',
        (root_keyword,)
    ).fetchone()

    cursor = conn.execute('''
        INSERT INTO refactor_chains (
            chain_name, root_keyword_id, depth, total_variations
        ) VALUES (?, ?, ?, ?)
    ''', (
        f"{root_keyword} refactor chain",
        root_keyword_record['id'],
        depth,
        len(keyword_variations)
    ))

    chain_id = cursor.lastrowid

    conn.commit()
    conn.close()

    # Generate content variations for each keyword
    content_variations = []

    if original_content:
        for kw in keyword_variations[:depth]:
            variation = generate_content_variation(
                original_content=original_content,
                target_keyword=kw['keyword'],
                specificity_level=kw['specificity_level']
            )

            if 'error' not in variation:
                content_variations.append(variation)

    return {
        'chain_id': chain_id,
        'root_keyword': root_keyword,
        'keyword_variations': keyword_variations,
        'content_variations': content_variations,
        'total_variations': len(keyword_variations)
    }


# ==============================================================================
# DOMAIN MAPPING
# ==============================================================================

def map_keyword_to_domain(keyword: str, variation_id: Optional[int] = None) -> str:
    """
    Map keyword to potential domain name

    Args:
        keyword: Keyword (e.g., "cooking at home on a budget")
        variation_id: Optional content variation ID

    Returns:
        Domain name suggestion (e.g., "cookingathomeonabudget.com")
    """

    # Clean keyword
    clean = re.sub(r'[^a-z0-9\s]', '', keyword.lower())
    words = clean.split()

    # Generate domain options
    options = []

    # Full phrase
    full_domain = ''.join(words) + '.com'
    options.append(full_domain)

    # First + last word
    if len(words) >= 2:
        short_domain = words[0] + words[-1] + '.com'
        options.append(short_domain)

    # Acronym
    if len(words) >= 3:
        acronym = ''.join([w[0] for w in words]) + '.com'
        options.append(acronym)

    # "how to" variant
    if 'how' not in words:
        howto_domain = 'howto' + ''.join(words) + '.com'
        options.append(howto_domain)

    return {
        'keyword': keyword,
        'primary_domain': options[0],
        'alternatives': options[1:],
        'variation_id': variation_id
    }


# ==============================================================================
# SEO METRICS ESTIMATION
# ==============================================================================

def estimate_seo_metrics(keyword: str) -> Dict:
    """
    Estimate SEO difficulty based on keyword characteristics

    Args:
        keyword: Keyword to analyze

    Returns:
        {
            'keyword': str,
            'estimated_difficulty': int (1-100),
            'estimated_search_volume': int,
            'specificity_score': int (1-10)
        }
    """

    words = keyword.split()
    word_count = len(words)

    # Heuristics:
    # - More words = more specific = easier to rank
    # - Generic words = harder
    # - "How to" = easier (informational)
    # - Numbers = more specific = easier

    generic_words = {'the', 'a', 'an', 'best', 'top', 'good', 'great'}
    specific_indicators = {'how', 'to', 'guide', 'tutorial', 'beginners'}

    generic_count = sum(1 for w in words if w.lower() in generic_words)
    specific_count = sum(1 for w in words if w.lower() in specific_indicators)
    has_numbers = any(char.isdigit() for char in keyword)

    # Specificity score (1-10)
    specificity = min(word_count + specific_count * 2 + (2 if has_numbers else 0), 10)

    # Difficulty (inverse of specificity)
    difficulty = max(100 - (specificity * 10), 10)

    # Search volume estimate (inverse of specificity)
    search_volume = max(10000 // (specificity ** 2), 10)

    return {
        'keyword': keyword,
        'estimated_difficulty': difficulty,
        'estimated_search_volume': search_volume,
        'specificity_score': specificity,
        'word_count': word_count
    }


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing long-tail SEO refactor tables...")
    init_seo_refactor_tables()
    print("✅ Tables initialized")
    print()

    print("Long-Tail SEO Refactor - Broad to Micro-Niche")
    print()
    print("Features:")
    print("  - Refactor keywords from broad → specific")
    print("  - Generate content variations (digital twins)")
    print("  - Build refactor chains")
    print("  - Map keywords to domain names")
    print("  - Estimate SEO difficulty")
    print()
    print("Example refactor chain:")
    print("  1. 'cooking' (100k searches, impossible to rank)")
    print("  2. 'cooking at home' (50k searches, very hard)")
    print("  3. 'cooking at home on a budget' (5k searches, hard)")
    print("  4. 'cooking at home on a budget with 3 ingredients' (500 searches, RANKABLE!)")
    print()
    print("Domain mapping:")
    print("  - cookingathomeonabudget.com")
    print("  - 3ingredientmeals.com")
    print("  - howtocookathome.com")

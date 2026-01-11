#!/usr/bin/env python3
"""
Contribution Validator - Real-Time On-Brand Scoring

Provides INSTANT feedback as users type contributions, showing:
- How "on-brand" their content is (0-100%)
- Estimated soul token rewards
- Which brand aspects they're hitting
- Suggestions to improve score

Philosophy:
----------
Make the system TRANSPARENT and GAMIFIED:
- Users see their score in real-time
- They learn what each brand values
- They can optimize before submitting
- Instant feedback creates engagement loop

The Self-Reinforcing Loop:
-------------------------
Better feedback → Better contributions
Better contributions → Better training data
Better training data → Better neural networks
Better neural networks → BETTER FEEDBACK (LOOP)

Architecture:
------------
```
User types → AJAX call → validate_contribution()
               ↓
         Neural networks classify
               ↓
         Compare to brand profile
               ↓
         Calculate score + estimate tokens
               ↓
         Return JSON with feedback
```

Usage:
    # As a module
    from contribution_validator import validate_contribution

    result = validate_contribution(
        text="This Python function uses clean architecture...",
        brand_id=1
    )

    print(f"On-brand score: {result['on_brand_score']}%")
    print(f"Estimated tokens: {result['estimated_tokens']}")

    # As API endpoint (added to app.py)
    POST /api/validate-contribution
    {
        "text": "...",
        "brand_id": 1
    }
"""

import sqlite3
import json
from typing import Dict, List, Optional

# Import our neural network classifier
from neural_proxy import classify_with_neural_network


# ==============================================================================
# BRAND PROFILE LOADING
# ==============================================================================

def get_brand_profile(brand_id: int) -> Optional[Dict]:
    """
    Load brand profile from database

    Returns:
        {
            'id': 1,
            'name': 'CalRiven',
            'slug': 'calriven',
            'description': '...',
            'neural_network': 'calriven_technical_classifier',
            'target_classification': 'technical',
            'keywords': ['code', 'function', 'api', ...]
        }
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM brands WHERE id = ?', (brand_id,))
    brand = cursor.fetchone()

    if not brand:
        conn.close()
        return None

    brand_dict = dict(brand)

    # Map brand to neural network and classification
    brand_mappings = {
        'calriven': {
            'neural_network': 'calriven_technical_classifier',
            'target_classification': 'technical',
            'keywords': [
                'code', 'function', 'class', 'api', 'database', 'python', 'javascript',
                'build', 'implement', 'develop', 'program', 'algorithm', 'system',
                'architecture', 'backend', 'frontend', 'server', 'client', 'web',
                'sql', 'query', 'schema', 'model', 'framework', 'library'
            ]
        },
        'privacy-guard': {
            'neural_network': 'deathtodata_privacy_classifier',
            'target_classification': 'privacy',
            'keywords': [
                'privacy', 'data', 'security', 'encryption', 'personal', 'tracking',
                'gdpr', 'surveillance', 'protect', 'secure', 'confidential', 'anonymous',
                'cookie', 'fingerprint', 'breach', 'leak', 'credential', 'password'
            ]
        }
    }

    slug = brand_dict['slug']
    if slug in brand_mappings:
        brand_dict.update(brand_mappings[slug])
    else:
        # Default to general
        brand_dict.update({
            'neural_network': 'general_classifier',
            'target_classification': 'general',
            'keywords': []
        })

    conn.close()
    return brand_dict


# ==============================================================================
# CONTRIBUTION VALIDATION
# ==============================================================================

def validate_contribution(text: str, brand_id: int) -> Dict:
    """
    Validate a contribution against a brand's profile

    Args:
        text: The contribution text (comment, post, etc.)
        brand_id: Brand to validate against

    Returns:
        {
            'on_brand_score': 85.5,  # 0-100
            'quality_score': 72.0,   # 0-100
            'estimated_tokens': 17,  # Soul tokens they'll earn
            'classification': 'technical',
            'confidence': 0.85,
            'feedback': {
                'strengths': ['Uses technical keywords', 'Clear structure'],
                'suggestions': ['Add more code examples'],
                'keyword_matches': ['code', 'function', 'api']
            },
            'breakdown': {
                'classification_match': 50,  # Points for matching classification
                'keyword_coverage': 30,      # Points for keyword usage
                'quality_factors': 20        # Length, structure, etc.
            }
        }
    """

    # Load brand profile
    brand = get_brand_profile(brand_id)
    if not brand:
        return {
            'error': 'Brand not found',
            'on_brand_score': 0,
            'estimated_tokens': 0
        }

    # Run neural network classification
    classification_result = classify_with_neural_network(text)

    # Calculate on-brand score
    score_breakdown = {}

    # 1. Classification Match (50 points max)
    if classification_result['classification'] == brand['target_classification']:
        classification_match = classification_result['confidence'] * 50
    else:
        # Partial credit if confidence is low (might be borderline)
        classification_match = max(0, (0.5 - classification_result['confidence']) * 20)

    score_breakdown['classification_match'] = classification_match

    # 2. Keyword Coverage (30 points max)
    text_lower = text.lower()
    keyword_matches = [kw for kw in brand['keywords'] if kw in text_lower]
    keyword_coverage = min(30, len(keyword_matches) * 3)
    score_breakdown['keyword_coverage'] = keyword_coverage

    # 3. Quality Factors (20 points max)
    quality_score = 0

    # Length bonus (5 points)
    word_count = len(text.split())
    if word_count >= 50:
        quality_score += 5
    elif word_count >= 20:
        quality_score += 3
    elif word_count >= 10:
        quality_score += 1

    # Structure bonus (5 points)
    has_paragraphs = '\n' in text
    has_punctuation = any(p in text for p in ['.', '!', '?'])
    if has_paragraphs and has_punctuation:
        quality_score += 5
    elif has_punctuation:
        quality_score += 3

    # Code/formatting bonus for technical (5 points)
    if brand['target_classification'] == 'technical':
        has_code_markers = '```' in text or '`' in text
        if has_code_markers:
            quality_score += 5

    # Specificity bonus (5 points)
    has_numbers = any(c.isdigit() for c in text)
    has_urls = 'http' in text_lower or 'www' in text_lower
    if has_numbers or has_urls:
        quality_score += 3

    score_breakdown['quality_factors'] = quality_score

    # Total on-brand score
    on_brand_score = sum(score_breakdown.values())

    # Estimate soul tokens (1 token per 5 points, rounded)
    estimated_tokens = max(1, int(on_brand_score / 5))

    # Generate feedback
    feedback = _generate_feedback(
        text,
        brand,
        classification_result,
        keyword_matches,
        word_count,
        on_brand_score
    )

    return {
        'on_brand_score': round(on_brand_score, 1),
        'quality_score': round(quality_score, 1),
        'estimated_tokens': estimated_tokens,
        'classification': classification_result['classification'],
        'confidence': round(classification_result['confidence'], 2),
        'feedback': feedback,
        'breakdown': {
            'classification_match': round(classification_match, 1),
            'keyword_coverage': round(keyword_coverage, 1),
            'quality_factors': round(quality_score, 1)
        }
    }


def _generate_feedback(
    text: str,
    brand: Dict,
    classification: Dict,
    keyword_matches: List[str],
    word_count: int,
    score: float
) -> Dict:
    """Generate human-readable feedback"""

    strengths = []
    suggestions = []

    # Classification feedback
    if classification['classification'] == brand['target_classification']:
        strengths.append(f"✅ Matches {brand['name']}'s focus on {classification['classification']} content")
    else:
        suggestions.append(f"💡 This reads as '{classification['classification']}' but {brand['name']} focuses on '{brand['target_classification']}'")

    # Keyword feedback
    if len(keyword_matches) >= 5:
        strengths.append(f"✅ Great keyword coverage ({len(keyword_matches)} brand keywords)")
    elif len(keyword_matches) >= 2:
        strengths.append(f"✅ Uses some brand keywords: {', '.join(keyword_matches[:3])}")
    else:
        suggestions.append(f"💡 Try including keywords like: {', '.join(brand['keywords'][:5])}")

    # Length feedback
    if word_count >= 50:
        strengths.append("✅ Substantial contribution (50+ words)")
    elif word_count < 10:
        suggestions.append("💡 Add more detail (currently only {word_count} words)")

    # Structure feedback
    if '\n' in text:
        strengths.append("✅ Well-structured with paragraphs")
    else:
        suggestions.append("💡 Break into paragraphs for better readability")

    # Code feedback (for technical brands)
    if brand['target_classification'] == 'technical':
        if '```' in text or '`' in text:
            strengths.append("✅ Includes code examples")
        else:
            suggestions.append("💡 Add code examples with ``` blocks")

    # Overall score feedback
    if score >= 80:
        strengths.insert(0, "🎉 Excellent on-brand contribution!")
    elif score >= 60:
        strengths.insert(0, "👍 Good alignment with brand")
    elif score >= 40:
        suggestions.insert(0, "⚠️ Could be more aligned with brand values")
    else:
        suggestions.insert(0, "❌ Low brand alignment - consider adjusting focus")

    return {
        'strengths': strengths,
        'suggestions': suggestions,
        'keyword_matches': keyword_matches
    }


# ==============================================================================
# BATCH VALIDATION (for existing content)
# ==============================================================================

def validate_existing_contributions(brand_id: int, limit: int = 100) -> List[Dict]:
    """
    Validate existing comments/posts for a brand
    Used to bootstrap contribution_scores table
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get recent comments (you can extend to posts too)
    cursor.execute('''
        SELECT c.id, c.content, c.user_id, c.created_at
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        JOIN brands b ON p.brand_id = b.id
        WHERE b.id = ?
        ORDER BY c.created_at DESC
        LIMIT ?
    ''', (brand_id, limit))

    comments = cursor.fetchall()
    results = []

    for comment in comments:
        validation = validate_contribution(comment['content'], brand_id)

        # Save to contribution_scores
        cursor.execute('''
            INSERT OR IGNORE INTO contribution_scores (
                contribution_id,
                contribution_type,
                brand_id,
                user_id,
                on_brand_score,
                quality_score,
                accepted,
                tokens_awarded,
                evaluator_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comment['id'],
            'comment',
            brand_id,
            comment['user_id'],
            validation['on_brand_score'],
            validation['quality_score'],
            1 if validation['on_brand_score'] >= 40 else 0,  # Accept if >= 40%
            validation['estimated_tokens'] if validation['on_brand_score'] >= 40 else 0,
            validation['classification']
        ))

        results.append({
            'comment_id': comment['id'],
            'score': validation['on_brand_score'],
            'tokens': validation['estimated_tokens']
        })

    conn.commit()
    conn.close()

    return results


# ==============================================================================
# CLI FOR TESTING
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Contribution Validator')
    parser.add_argument('--test', type=str, help='Test text to validate')
    parser.add_argument('--brand', type=int, default=1, help='Brand ID')
    parser.add_argument('--bootstrap', type=int, help='Bootstrap existing contributions for brand ID')

    args = parser.parse_args()

    if args.test:
        print(f"Testing contribution against brand {args.brand}...")
        print()

        result = validate_contribution(args.test, args.brand)

        print("=" * 70)
        print("📊 CONTRIBUTION VALIDATION RESULT")
        print("=" * 70)
        print()
        print(f"On-Brand Score: {result['on_brand_score']}/100")
        print(f"Quality Score: {result['quality_score']}/100")
        print(f"Estimated Tokens: {result['estimated_tokens']} soul tokens")
        print()
        print(f"Classification: {result['classification']} ({result['confidence']:.0%} confidence)")
        print()

        print("Score Breakdown:")
        for factor, points in result['breakdown'].items():
            print(f"  {factor}: {points:.1f} points")
        print()

        print("Strengths:")
        for strength in result['feedback']['strengths']:
            print(f"  {strength}")
        print()

        if result['feedback']['suggestions']:
            print("Suggestions:")
            for suggestion in result['feedback']['suggestions']:
                print(f"  {suggestion}")
            print()

        if result['feedback']['keyword_matches']:
            print(f"Matched Keywords: {', '.join(result['feedback']['keyword_matches'])}")
            print()

    elif args.bootstrap:
        print(f"Bootstrapping contribution scores for brand {args.bootstrap}...")
        print()

        results = validate_existing_contributions(args.bootstrap)

        print(f"✅ Validated {len(results)} contributions")
        print()

        total_tokens = sum(r['tokens'] for r in results)
        avg_score = sum(r['score'] for r in results) / len(results) if results else 0

        print(f"Total tokens awarded: {total_tokens}")
        print(f"Average score: {avg_score:.1f}/100")
        print()

        # Show top contributions
        top = sorted(results, key=lambda x: x['score'], reverse=True)[:5]
        print("Top 5 contributions:")
        for i, r in enumerate(top, 1):
            print(f"  {i}. Comment #{r['comment_id']}: {r['score']:.1f}/100 ({r['tokens']} tokens)")

    else:
        print("Contribution Validator - Real-Time On-Brand Scoring")
        print()
        print("Usage:")
        print('  --test "Your text here" --brand 1    Test contribution')
        print("  --bootstrap 1                        Score existing contributions")
        print()
        print("Examples:")
        print('  python3 contribution_validator.py --test "This Python function uses clean code" --brand 1')
        print("  python3 contribution_validator.py --bootstrap 1")

#!/usr/bin/env python3
"""
Brand Voice Generator - Pure Python Stdlib

Generates brand-consistent content using trained models:
- Predicts which brand wrote text
- Generates content in brand voice
- Checks brand consistency
- Suggests emoji for brand
- Analyzes newsletter tone

Combines vocabulary, emoji, and tone models to create authentic brand content.

Like: AI ghostwriter that perfectly mimics each brand's personality!
"""

import json
from collections import Counter

from brand_vocabulary_trainer import (
    load_brand_model_from_db,
    predict_brand,
    get_brand_wordmap,
    compare_brands
)
from emoji_pattern_analyzer import (
    load_emoji_patterns_from_db,
    suggest_brand_emoji as suggest_emoji_internal,
    classify_emoji_sentiment
)
from simple_ml import tokenize


def predict_brand_voice(text):
    """
    Predict which brand this text sounds like

    Args:
        text: Content to analyze

    Returns:
        dict: {
            'brand': brand_slug,
            'confidence': 0.0-1.0,
            'wordmap_match': 0.0-1.0,
            'emoji_match': 0.0-1.0
        }
    """
    # Use vocabulary model
    brand, vocab_confidence = predict_brand(text)

    if not brand:
        return {'brand': None, 'confidence': 0.0}

    # Check emoji match (if emoji in text)
    from emoji_pattern_analyzer import extract_emoji

    emoji_list = extract_emoji(text)
    emoji_match = 0.0

    if emoji_list:
        emoji_patterns = load_emoji_patterns_from_db()
        if emoji_patterns and brand in emoji_patterns['brand_emoji_usage']:
            brand_emoji = emoji_patterns['brand_emoji_usage'][brand]['emoji_freq']

            # Calculate overlap
            text_emoji_set = set(emoji_list)
            brand_emoji_set = set(brand_emoji.keys())

            if text_emoji_set and brand_emoji_set:
                emoji_match = len(text_emoji_set & brand_emoji_set) / len(text_emoji_set)

    # Combine scores
    overall_confidence = (vocab_confidence * 0.7) + (emoji_match * 0.3)

    return {
        'brand': brand,
        'confidence': overall_confidence,
        'wordmap_match': vocab_confidence,
        'emoji_match': emoji_match
    }


def check_brand_consistency(brand_slug, text):
    """
    Check if text is consistent with brand voice

    Args:
        brand_slug: Brand to check against
        text: Content to analyze

    Returns:
        dict: {
            'is_consistent': bool,
            'score': 0.0-1.0,
            'issues': [list of problems],
            'suggestions': [list of improvements]
        }
    """
    prediction = predict_brand_voice(text)

    is_consistent = (prediction['brand'] == brand_slug and prediction['confidence'] > 0.6)

    issues = []
    suggestions = []

    # Check wordmap alignment
    brand_wordmap = get_brand_wordmap(brand_slug)
    if brand_wordmap:
        words = tokenize(text)
        word_counts = Counter(words)

        # Check if text uses brand vocabulary
        brand_words_used = sum(1 for word in words if word in brand_wordmap)
        brand_word_ratio = brand_words_used / len(words) if words else 0

        if brand_word_ratio < 0.1:
            issues.append("Text doesn't use brand-specific vocabulary")
            top_brand_words = list(brand_wordmap.keys())[:5]
            suggestions.append(f"Consider using words like: {', '.join(top_brand_words)}")

    # Check emoji usage
    from emoji_pattern_analyzer import extract_emoji

    emoji_list = extract_emoji(text)
    emoji_patterns = load_emoji_patterns_from_db()

    if emoji_patterns and brand_slug in emoji_patterns['brand_emoji_usage']:
        brand_data = emoji_patterns['brand_emoji_usage'][brand_slug]
        expected_density = brand_data['emoji_density']

        word_count = len(text.split())
        actual_density = (len(emoji_list) / word_count * 100) if word_count > 0 else 0

        if abs(actual_density - expected_density) > 2.0:
            if actual_density < expected_density:
                issues.append(f"Text has fewer emoji than typical {brand_slug} content")
                top_emoji = [e for e, c in brand_data['top_emoji'][:3]]
                suggestions.append(f"Add emoji like: {' '.join(top_emoji)}")
            else:
                issues.append(f"Text has more emoji than typical {brand_slug} content")

    return {
        'is_consistent': is_consistent,
        'score': prediction['confidence'],
        'predicted_brand': prediction['brand'],
        'target_brand': brand_slug,
        'issues': issues,
        'suggestions': suggestions
    }


def generate_brand_content(brand_slug, topic, length='short', include_emoji=True):
    """
    Generate content in brand voice

    Args:
        brand_slug: Brand to generate for
        topic: Content topic/subject
        length: 'short', 'medium', 'long'
        include_emoji: Whether to add emoji

    Returns:
        str: Generated content

    Note: This is a template-based generator (not LLM).
          Uses learned wordmaps and patterns to create on-brand content.
    """
    # Load brand data
    brand_model = load_brand_model_from_db()
    emoji_patterns = load_emoji_patterns_from_db()

    if not brand_model or brand_slug not in brand_model['brand_wordmaps']:
        return f"Brand {brand_slug} not found in trained models"

    wordmap = brand_model['brand_wordmaps'][brand_slug]
    metadata = brand_model['brand_metadata'].get(brand_slug, {})

    personality = metadata.get('personality', 'neutral')
    tone = metadata.get('tone', 'professional')

    # Get top words for this brand
    top_words = list(wordmap.keys())[:20]

    # Generate opening based on tone
    if 'calm' in tone or 'peaceful' in tone:
        opening = "Let's explore"
    elif 'technical' in tone or 'analytical' in tone:
        opening = "Analysis:"
    elif 'professional' in tone:
        opening = "Overview:"
    else:
        opening = "Here's the breakdown:"

    # Build content using brand vocabulary
    content_parts = [opening, topic]

    # Add some brand-specific words
    if len(top_words) >= 3:
        content_parts.append(f"Focusing on {top_words[0]}, {top_words[1]}, and {top_words[2]}.")

    # Add emoji if requested
    if include_emoji and emoji_patterns and brand_slug in emoji_patterns['brand_emoji_usage']:
        brand_emoji_data = emoji_patterns['brand_emoji_usage'][brand_slug]
        if brand_emoji_data['top_emoji']:
            emoji_char = brand_emoji_data['top_emoji'][0][0]
            content_parts.insert(0, emoji_char)

    content = ' '.join(content_parts)

    return content


def suggest_brand_emoji(brand_slug, context=''):
    """
    Suggest emoji for brand based on context

    Args:
        brand_slug: Brand slug
        context: Text context

    Returns:
        list: [{'emoji': char, 'confidence': float, 'reason': str}, ...]
    """
    suggestions = suggest_emoji_internal(brand_slug, context)

    # Add reasons
    for suggestion in suggestions:
        sentiment = classify_emoji_sentiment(suggestion['emoji'])
        suggestion['reason'] = f"{sentiment.capitalize()} emoji (used {suggestion['usage_count']} times)"

    return suggestions


def analyze_newsletter_tone(newsletter_html):
    """
    Analyze tone of newsletter content

    Args:
        newsletter_html: Newsletter HTML

    Returns:
        dict: {
            'word_count': int,
            'emoji_count': int,
            'emoji_density': float,
            'top_words': [(word, count), ...],
            'sentiment': str,
            'formality': str
        }
    """
    # Strip HTML tags (simple)
    import re
    text = re.sub(r'<[^>]+>', '', newsletter_html)

    # Count words
    words = tokenize(text)
    word_count = len(words)

    # Count emoji
    from emoji_pattern_analyzer import extract_emoji
    emoji_list = extract_emoji(text)
    emoji_count = len(emoji_list)
    emoji_density = (emoji_count / word_count * 100) if word_count > 0 else 0

    # Top words
    word_counts = Counter(words)
    top_words = word_counts.most_common(10)

    # Determine sentiment (simple heuristic)
    positive_words = {'great', 'awesome', 'excited', 'happy', 'good', 'excellent'}
    negative_words = {'bad', 'issue', 'problem', 'error', 'failed', 'broken'}

    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)

    if positive_count > negative_count:
        sentiment = 'positive'
    elif negative_count > positive_count:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    # Determine formality
    formal_words = {'furthermore', 'however', 'therefore', 'moreover', 'consequently'}
    casual_words = {'hey', 'yeah', 'cool', 'awesome', 'super'}

    formal_count = sum(1 for word in words if word in formal_words)
    casual_count = sum(1 for word in words if word in casual_words)

    if formal_count > casual_count:
        formality = 'formal'
    elif casual_count > formal_count:
        formality = 'casual'
    else:
        formality = 'balanced'

    return {
        'word_count': word_count,
        'emoji_count': emoji_count,
        'emoji_density': emoji_density,
        'top_words': top_words,
        'sentiment': sentiment,
        'formality': formality
    }


def compare_brand_voices(brand1_slug, brand2_slug):
    """
    Compare voices of two brands

    Args:
        brand1_slug: First brand
        brand2_slug: Second brand

    Returns:
        dict: Comparison data
    """
    # Compare vocabulary
    vocab_comparison = compare_brands(brand1_slug, brand2_slug)

    # Compare emoji usage
    from emoji_pattern_analyzer import compare_brand_emoji
    emoji_comparison = compare_brand_emoji(brand1_slug, brand2_slug)

    return {
        'vocabulary': vocab_comparison,
        'emoji': emoji_comparison,
        'overall_similarity': (
            (vocab_comparison.get('similarity_score', 0) * 0.5) +
            (emoji_comparison.get('similarity', 0) * 0.5)
        ) if vocab_comparison and emoji_comparison else 0
    }


def main():
    """CLI interface"""
    print("=" * 60)
    print("Brand Voice Generator - Test Suite")
    print("=" * 60)
    print()

    # Test 1: Predict brand from text
    print("Test 1: Brand Prediction")
    print("-" * 60)

    test_texts = [
        "Technical analysis of database optimization strategies and caching layers",
        "Calm flows of data streaming peacefully through the system",
        "Privacy-first encryption ensuring secure and protected user data",
    ]

    for text in test_texts:
        result = predict_brand_voice(text)
        print(f"\nText: {text[:60]}...")
        print(f"  Brand: {result['brand']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Wordmap: {result['wordmap_match']:.1%}, Emoji: {result['emoji_match']:.1%}")

    print()

    # Test 2: Generate content
    print("\nTest 2: Content Generation")
    print("-" * 60)

    brands = ['ocean-dreams', 'calriven', 'deathtodata']
    for brand in brands:
        content = generate_brand_content(brand, "new features", include_emoji=True)
        print(f"\n{brand}:")
        print(f"  {content}")

    print()

    # Test 3: Emoji suggestions
    print("\nTest 3: Emoji Suggestions")
    print("-" * 60)

    for brand in brands:
        suggestions = suggest_brand_emoji(brand, "technical implementation")
        print(f"\n{brand} + 'technical implementation':")
        for sugg in suggestions[:3]:
            print(f"  {sugg['emoji']} - {sugg['reason']} ({sugg['confidence']:.1%})")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Emoji Pattern Analyzer - Pure Python Stdlib

Learns emoji usage patterns per brand:
- Which emoji each brand uses
- Emoji frequency and context
- Emoji positioning (start, middle, end)
- Sentiment association (positive/technical/secure emoji)

Each theme has an emoji (🌊 Ocean Dreams, 💻 CalRiven, etc.).
This analyzes how emoji are used in actual content.

Like: Teaching AI to understand brand emoji language!
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime

from database import get_db


def extract_emoji(text):
    """
    Extract all emoji from text

    Args:
        text: String to analyze

    Returns:
        list: Emoji characters found

    Uses Unicode ranges for emoji detection
    """
    if not text:
        return []

    # Emoji Unicode ranges (simplified)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F900-\U0001F9FF"  # Supplemental symbols
        "\U0001FA70-\U0001FAFF"  # Extended pictographs
        "]+",
        flags=re.UNICODE
    )

    matches = emoji_pattern.findall(text)

    # Split combined emoji (e.g., "🌊⛵" → ["🌊", "⛵"])
    emoji_list = []
    for match in matches:
        for char in match:
            if ord(char) > 0x1F000:  # Simple emoji check
                emoji_list.append(char)

    return emoji_list


def get_emoji_context(text, emoji_char, context_words=3):
    """
    Get words surrounding an emoji

    Args:
        text: Full text
        emoji_char: Emoji to find
        context_words: How many words before/after

    Returns:
        list: [{'before': [...], 'after': [...]}]
    """
    contexts = []

    # Split text into words, keeping emoji
    tokens = re.findall(r'\w+|[^\w\s]', text)

    # Find emoji positions
    for i, token in enumerate(tokens):
        if emoji_char in token:
            before = tokens[max(0, i-context_words):i]
            after = tokens[i+1:min(len(tokens), i+1+context_words)]

            contexts.append({
                'before': [t for t in before if t.strip()],
                'after': [t for t in after if t.strip()]
            })

    return contexts


def analyze_brand_emoji_usage():
    """
    Analyze emoji usage for each brand

    Returns:
        dict: {
            brand_slug: {
                'emoji_freq': {emoji: count},
                'emoji_contexts': {emoji: [contexts]},
                'emoji_density': float,  # emoji per 100 words
                'brand_emoji': emoji,  # official brand emoji
                'top_emoji': [(emoji, count), ...]
            }
        }
    """
    db = get_db()

    # Get all brands
    brands = db.execute('SELECT id, slug, config_json FROM brands').fetchall()

    brand_analysis = {}

    for brand in brands:
        brand_id = brand['id']
        brand_slug = brand['slug']

        # Extract official brand emoji from config
        brand_emoji = None
        if brand['config_json']:
            try:
                config = json.loads(brand['config_json'])
                brand_emoji = config.get('emoji')
            except:
                pass

        # Get all posts for this brand
        posts = db.execute('''
            SELECT p.title, p.content
            FROM posts p
            JOIN brand_posts bp ON p.id = bp.post_id
            WHERE bp.brand_id = ?
        ''', (brand_id,)).fetchall()

        # Combine all text
        all_text = ' '.join([
            post['title'] + ' ' + post['content']
            for post in posts
        ])

        # Count words
        word_count = len(all_text.split())

        # Extract emoji
        emoji_list = extract_emoji(all_text)

        # Calculate emoji frequency
        emoji_freq = Counter(emoji_list)

        # Calculate density (emoji per 100 words)
        emoji_density = (len(emoji_list) / word_count * 100) if word_count > 0 else 0

        # Get contexts for top emoji
        emoji_contexts = {}
        for emoji_char, count in emoji_freq.most_common(10):
            contexts = get_emoji_context(all_text, emoji_char)
            emoji_contexts[emoji_char] = contexts

        brand_analysis[brand_slug] = {
            'emoji_freq': dict(emoji_freq),
            'emoji_contexts': emoji_contexts,
            'emoji_density': emoji_density,
            'brand_emoji': brand_emoji,
            'top_emoji': emoji_freq.most_common(10),
            'total_emoji': len(emoji_list),
            'word_count': word_count
        }

    db.close()

    return brand_analysis


def classify_emoji_sentiment(emoji_char):
    """
    Classify emoji into sentiment categories

    Args:
        emoji_char: Single emoji

    Returns:
        str: Category (positive, technical, secure, creative, neutral)
    """
    # Simplified classification based on emoji ranges
    code = ord(emoji_char) if emoji_char else 0

    # Technical emoji
    technical = {'💻', '🔧', '⚙️', '🖥️', '📊', '📈', '🤖', '🧠', '⚡', '🔬'}
    if emoji_char in technical:
        return 'technical'

    # Security/privacy emoji
    secure = {'🔒', '🔐', '🛡️', '🔑', '🚨', '⚠️', '✓', '✅', '☑️'}
    if emoji_char in secure:
        return 'secure'

    # Nature/calm emoji
    calm = {'🌊', '🌱', '🌿', '🌸', '🌺', '☀️', '🌙', '⛰️', '🏔️'}
    if emoji_char in calm:
        return 'calm'

    # Positive emotion
    positive = {'😊', '😀', '🎉', '🎊', '🌟', '✨', '💫', '🎯', '🚀', '🎮'}
    if emoji_char in positive:
        return 'positive'

    return 'neutral'


def analyze_emoji_sentiment_distribution():
    """
    Analyze sentiment distribution of emoji per brand

    Returns:
        dict: {
            brand_slug: {
                'technical': 5,
                'secure': 3,
                'calm': 8,
                ...
            }
        }
    """
    brand_emoji = analyze_brand_emoji_usage()

    sentiment_distribution = {}

    for brand_slug, analysis in brand_emoji.items():
        sentiments = Counter()

        for emoji_char in analysis['emoji_freq'].keys():
            sentiment = classify_emoji_sentiment(emoji_char)
            sentiments[sentiment] += analysis['emoji_freq'][emoji_char]

        sentiment_distribution[brand_slug] = dict(sentiments)

    return sentiment_distribution


def suggest_brand_emoji(brand_slug, context=''):
    """
    Suggest emoji for a brand based on learned patterns

    Args:
        brand_slug: Brand to suggest for
        context: Optional context text

    Returns:
        list: [(emoji, confidence), ...]
    """
    analysis = analyze_brand_emoji_usage()

    if brand_slug not in analysis:
        return []

    brand_data = analysis[brand_slug]

    # Get top emoji by frequency
    suggestions = []

    for emoji_char, count in brand_data['top_emoji']:
        # Calculate confidence based on frequency
        total_emoji = brand_data['total_emoji']
        confidence = count / total_emoji if total_emoji > 0 else 0

        suggestions.append({
            'emoji': emoji_char,
            'confidence': confidence,
            'usage_count': count
        })

    # If context provided, boost relevant emoji
    if context:
        context_lower = context.lower()

        # Boost technical emoji for technical words
        if any(word in context_lower for word in ['code', 'data', 'tech', 'system', 'api']):
            for suggestion in suggestions:
                if classify_emoji_sentiment(suggestion['emoji']) == 'technical':
                    suggestion['confidence'] *= 1.5

        # Boost security emoji for security words
        if any(word in context_lower for word in ['secure', 'private', 'encrypt', 'safe', 'protect']):
            for suggestion in suggestions:
                if classify_emoji_sentiment(suggestion['emoji']) == 'secure':
                    suggestion['confidence'] *= 1.5

    # Sort by confidence
    suggestions.sort(key=lambda x: x['confidence'], reverse=True)

    return suggestions[:5]


def compare_brand_emoji(brand1_slug, brand2_slug):
    """
    Compare emoji usage between two brands

    Args:
        brand1_slug: First brand
        brand2_slug: Second brand

    Returns:
        dict: Comparison stats
    """
    analysis = analyze_brand_emoji_usage()

    if brand1_slug not in analysis or brand2_slug not in analysis:
        return None

    brand1 = analysis[brand1_slug]
    brand2 = analysis[brand2_slug]

    # Find shared emoji
    emoji1 = set(brand1['emoji_freq'].keys())
    emoji2 = set(brand2['emoji_freq'].keys())

    shared = emoji1 & emoji2
    unique1 = emoji1 - emoji2
    unique2 = emoji2 - emoji1

    return {
        'brand1_slug': brand1_slug,
        'brand2_slug': brand2_slug,
        'brand1_density': brand1['emoji_density'],
        'brand2_density': brand2['emoji_density'],
        'shared_emoji': list(shared),
        'unique_to_brand1': list(unique1),
        'unique_to_brand2': list(unique2),
        'similarity': len(shared) / len(emoji1 | emoji2) if emoji1 or emoji2 else 0
    }


def save_emoji_analysis_to_db():
    """
    Save emoji analysis to database

    Returns:
        int: Model ID
    """
    analysis = analyze_brand_emoji_usage()
    sentiment = analyze_emoji_sentiment_distribution()

    model_data = {
        'model_type': 'emoji_pattern_analyzer',
        'brand_emoji_usage': analysis,
        'sentiment_distribution': sentiment,
        'analyzed_at': datetime.now().isoformat()
    }

    db = get_db()
    model_json = json.dumps(model_data)
    model_name = 'brand_emoji_patterns'

    # Check if exists
    existing = db.execute(
        'SELECT id FROM ml_models WHERE model_type = ?',
        (model_name,)
    ).fetchone()

    if existing:
        db.execute('''
            UPDATE ml_models
            SET model_data = ?,
                created_at = ?
            WHERE model_type = ?
        ''', (model_json, datetime.now().isoformat(), model_name))

        model_id = existing['id']
        print(f"📝 Updated emoji patterns: {model_name} (ID: {model_id})")
    else:
        cursor = db.execute('''
            INSERT INTO ml_models (model_type, model_data, created_at)
            VALUES (?, ?, ?)
        ''', (model_name, model_json, datetime.now().isoformat()))

        model_id = cursor.lastrowid
        print(f"💾 Saved emoji patterns: {model_name} (ID: {model_id})")

    db.commit()
    db.close()

    return model_id


def load_emoji_patterns_from_db():
    """Load emoji patterns from database"""
    db = get_db()

    model = db.execute(
        'SELECT model_data FROM ml_models WHERE model_type = ?',
        ('brand_emoji_patterns',)
    ).fetchone()

    db.close()

    if model:
        return json.loads(model['model_data'])
    return None


def main():
    """CLI interface"""
    print("=" * 60)
    print("Emoji Pattern Analyzer")
    print("=" * 60)
    print()

    # Analyze emoji usage
    print("📊 Analyzing emoji usage per brand...")
    analysis = analyze_brand_emoji_usage()

    print()
    print("😀 Emoji Statistics:")
    for brand_slug, data in analysis.items():
        emoji_icon = data['brand_emoji'] or '📄'
        print(f"\n  {emoji_icon} {brand_slug}")
        print(f"    Emoji density: {data['emoji_density']:.2f} per 100 words")
        print(f"    Total emoji: {data['total_emoji']}")
        print(f"    Unique emoji: {len(data['emoji_freq'])}")

        if data['top_emoji']:
            top_str = ' '.join([f"{e} ({c})" for e, c in data['top_emoji'][:5]])
            print(f"    Top emoji: {top_str}")

    print()

    # Analyze sentiment
    print("🎭 Emoji Sentiment Distribution:")
    sentiment = analyze_emoji_sentiment_distribution()

    for brand_slug, sentiments in sentiment.items():
        print(f"\n  {brand_slug}")
        for sent_type, count in sorted(sentiments.items(), key=lambda x: x[1], reverse=True):
            print(f"    {sent_type}: {count}")

    print()

    # Save analysis
    model_id = save_emoji_analysis_to_db()

    print()
    print("=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
    print(f"Model ID: {model_id}")
    print(f"Brands analyzed: {len(analysis)}")
    print()

    # Test suggestions
    print("🔮 Example Suggestions:")
    for brand_slug in list(analysis.keys())[:3]:
        suggestions = suggest_brand_emoji(brand_slug, 'technical implementation')
        print(f"\n  {brand_slug} + 'technical implementation':")
        for sugg in suggestions[:3]:
            print(f"    {sugg['emoji']} ({sugg['confidence']:.1%} confidence)")


if __name__ == '__main__':
    main()

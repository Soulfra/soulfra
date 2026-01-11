#!/usr/bin/env python3
"""
Brand Vocabulary Trainer - Pure Python Stdlib

Trains neural networks to learn each brand's unique "voice":
- Vocabulary patterns (wordmaps)
- Tone/personality from actual content
- Brand-specific language usage

Each theme (CalRiven 💻, Ocean Dreams 🌊, etc.) has a personality.
This trains ML to understand what makes each brand unique.

Like: Teaching AI to recognize "this sounds like CalRiven" vs "this sounds like Ocean Dreams"
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime

from database import get_db
from simple_ml import (
    tokenize,
    extract_features,
    calculate_idf,
    calculate_tfidf,
    train_naive_bayes,
    predict_naive_bayes
)


def get_brand_posts():
    """
    Extract all posts grouped by brand

    Returns:
        dict: {brand_slug: [{'title': ..., 'content': ...}, ...]}
    """
    db = get_db()

    # Get all brand-post associations
    results = db.execute('''
        SELECT
            b.slug as brand_slug,
            b.name as brand_name,
            b.personality,
            b.tone,
            p.title,
            p.content
        FROM brands b
        LEFT JOIN brand_posts bp ON b.id = bp.brand_id
        LEFT JOIN posts p ON bp.post_id = p.id
        WHERE p.id IS NOT NULL
        ORDER BY b.slug, p.published_at DESC
    ''').fetchall()

    db.close()

    # Group by brand
    brand_posts = defaultdict(list)

    for row in results:
        brand_posts[row['brand_slug']].append({
            'title': row['title'],
            'content': row['content'],
            'brand_name': row['brand_name'],
            'personality': row['personality'],
            'tone': row['tone']
        })

    return dict(brand_posts)


def get_brand_metadata():
    """
    Get brand personality/tone from database

    Returns:
        dict: {brand_slug: {'personality': ..., 'tone': ..., 'emoji': ...}}
    """
    db = get_db()

    brands = db.execute('''
        SELECT slug, name, personality, tone, config_json
        FROM brands
    ''').fetchall()

    db.close()

    metadata = {}

    for brand in brands:
        # Try to extract emoji from config_json
        emoji = None
        if brand['config_json']:
            try:
                config = json.loads(brand['config_json'])
                emoji = config.get('emoji')
            except:
                pass

        metadata[brand['slug']] = {
            'name': brand['name'],
            'personality': brand['personality'] or '',
            'tone': brand['tone'] or '',
            'emoji': emoji
        }

    return metadata


def extract_brand_wordmap(posts, top_n=50):
    """
    Extract top N words that define a brand's vocabulary

    Args:
        posts: List of post dicts
        top_n: Number of top words to extract

    Returns:
        dict: {'word': tfidf_score, ...}
    """
    if not posts:
        return {}

    # Combine all text for this brand
    all_text = ' '.join([
        post['title'] + ' ' + post['content']
        for post in posts
    ])

    # Tokenize and count
    words = tokenize(all_text)
    word_counts = Counter(words)

    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'from', 'by', 'as', 'is', 'was', 'are', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'it', 'its', 'we', 'you', 'they', 'them', 'their', 'i', 'me', 'my'
    }

    # Filter stop words and short words
    filtered_counts = {
        word: count for word, count in word_counts.items()
        if word not in stop_words and len(word) > 3
    }

    # Get top N
    top_words = Counter(filtered_counts).most_common(top_n)

    return dict(top_words)


def build_brand_training_dataset():
    """
    Build training dataset for brand classifier

    Returns:
        dict: {
            'documents': [text1, text2, ...],
            'labels': [brand1, brand2, ...],
            'brand_wordmaps': {brand_slug: {word: score, ...}},
            'brand_metadata': {...}
        }
    """
    print("📊 Building brand training dataset...")

    # Self-healing: Auto-sync brands from manifest if database is empty
    db = get_db()
    brand_count = db.execute('SELECT COUNT(*) as count FROM brands').fetchone()['count']
    db.close()

    if brand_count == 0:
        print()
        print("⚠️  No brands found in database!")
        print("   Auto-syncing from themes/manifest.yaml...")
        print()

        try:
            from init_brands_from_manifest import sync_brands_from_manifest
            sync_result = sync_brands_from_manifest()

            if sync_result['added'] > 0:
                print()
                print(f"✅ Auto-bootstrapped {sync_result['added']} brands!")
                print()
            else:
                print()
                print("❌ Auto-bootstrap failed - no brands added")
                print("   Run manually: python3 bootstrap.py")
                return None
        except Exception as e:
            print(f"❌ Auto-bootstrap error: {e}")
            print("   Run manually: python3 bootstrap.py")
            return None

    brand_posts = get_brand_posts()
    brand_metadata = get_brand_metadata()

    if not brand_posts:
        print("⚠️  No brand-post associations found!")
        print("   Link posts to brands via the brand_posts table")
        print("   Suggestion: python3 classify_posts_by_brand.py")
        return None

    # Build training data
    documents = []
    labels = []
    brand_wordmaps = {}

    for brand_slug, posts in brand_posts.items():
        print(f"  {brand_slug}: {len(posts)} posts")

        # Extract wordmap for this brand
        wordmap = extract_brand_wordmap(posts, top_n=50)
        brand_wordmaps[brand_slug] = wordmap

        # Add each post as a training example
        for post in posts:
            text = post['title'] + ' ' + post['content']
            documents.append(text)
            labels.append(brand_slug)

    print(f"✅ Dataset: {len(documents)} documents across {len(brand_posts)} brands")

    return {
        'documents': documents,
        'labels': labels,
        'brand_wordmaps': brand_wordmaps,
        'brand_metadata': brand_metadata
    }


def train_brand_classifier(dataset):
    """
    Train classifier to predict which brand wrote text

    Args:
        dataset: Output from build_brand_training_dataset()

    Returns:
        dict: Trained model data
    """
    if not dataset:
        return None

    print("🧠 Training brand classifier...")

    documents = dataset['documents']
    labels = dataset['labels']

    # Extract features (word counts) from each document
    feature_dicts = [extract_features(text) for text in documents]

    # Calculate IDF across all documents
    idf = calculate_idf(feature_dicts)

    # Calculate TF-IDF for each document
    tfidf_vectors = [calculate_tfidf(doc, idf) for doc in feature_dicts]

    # Train Naive Bayes classifier
    model = train_naive_bayes(tfidf_vectors, labels)

    print(f"✅ Trained on {len(documents)} documents")
    print(f"   Brands: {set(labels)}")

    return {
        'model_type': 'brand_naive_bayes',
        'model_data': model,
        'idf': idf,
        'brands': list(set(labels)),
        'training_size': len(documents),
        'brand_wordmaps': dataset['brand_wordmaps'],
        'brand_metadata': dataset['brand_metadata']
    }


def save_brand_model_to_db(model_data):
    """
    Save brand model to database

    Args:
        model_data: Trained model dict

    Returns:
        int: Model ID
    """
    db = get_db()

    model_json = json.dumps(model_data)
    model_name = 'brand_voice_classifier'

    # Check if exists
    existing = db.execute(
        'SELECT id FROM ml_models WHERE model_type = ?',
        (model_name,)
    ).fetchone()

    if existing:
        db.execute('''
            UPDATE ml_models
            SET model_data = ?,
                trained_on = ?,
                created_at = ?
            WHERE model_type = ?
        ''', (model_json, model_data['training_size'], datetime.now().isoformat(), model_name))

        model_id = existing['id']
        print(f"📝 Updated model: {model_name} (ID: {model_id})")
    else:
        cursor = db.execute('''
            INSERT INTO ml_models (model_type, model_data, trained_on, created_at)
            VALUES (?, ?, ?, ?)
        ''', (model_name, model_json, model_data['training_size'], datetime.now().isoformat()))

        model_id = cursor.lastrowid
        print(f"💾 Saved model: {model_name} (ID: {model_id})")

    db.commit()
    db.close()

    return model_id


def load_brand_model_from_db():
    """
    Load brand classifier from database

    Returns:
        dict: Model data or None
    """
    db = get_db()

    model = db.execute(
        'SELECT model_data FROM ml_models WHERE model_type = ?',
        ('brand_voice_classifier',)
    ).fetchone()

    db.close()

    if model:
        return json.loads(model['model_data'])
    return None


def predict_brand(text):
    """
    Predict which brand wrote this text

    Args:
        text: Content to analyze

    Returns:
        tuple: (brand_slug, confidence)
    """
    model = load_brand_model_from_db()

    if not model:
        return (None, 0.0)

    # Extract features
    word_counts = extract_features(text)
    tfidf = calculate_tfidf(word_counts, model['idf'])

    # Predict
    prediction, confidence = predict_naive_bayes(tfidf, model['model_data'])

    return (prediction, confidence)


def get_brand_wordmap(brand_slug):
    """
    Get vocabulary wordmap for a brand

    Args:
        brand_slug: Brand slug

    Returns:
        dict: {word: score, ...} or None
    """
    model = load_brand_model_from_db()

    if not model or 'brand_wordmaps' not in model:
        return None

    return model['brand_wordmaps'].get(brand_slug)


def compare_brands(brand1_slug, brand2_slug):
    """
    Compare vocabulary between two brands

    Args:
        brand1_slug: First brand
        brand2_slug: Second brand

    Returns:
        dict: {
            'unique_to_brand1': [words],
            'unique_to_brand2': [words],
            'shared': [words],
            'similarity_score': 0.0-1.0
        }
    """
    wordmap1 = get_brand_wordmap(brand1_slug)
    wordmap2 = get_brand_wordmap(brand2_slug)

    if not wordmap1 or not wordmap2:
        return None

    words1 = set(wordmap1.keys())
    words2 = set(wordmap2.keys())

    unique1 = words1 - words2
    unique2 = words2 - words1
    shared = words1 & words2

    # Calculate Jaccard similarity
    if not words1 and not words2:
        similarity = 1.0
    else:
        similarity = len(shared) / len(words1 | words2)

    return {
        'unique_to_brand1': list(unique1)[:10],
        'unique_to_brand2': list(unique2)[:10],
        'shared': list(shared)[:20],
        'similarity_score': similarity
    }


def test_brand_predictions():
    """Test brand classifier with example texts"""
    print("=" * 60)
    print("Testing Brand Predictions")
    print("=" * 60)
    print()

    test_cases = [
        ("Technical deep dive into database optimization and caching strategies", "Expected: CalRiven"),
        ("A peaceful flow of updates, calm and serene like ocean waves", "Expected: Ocean Dreams"),
        ("Privacy-first encryption and secure data handling protocols", "Expected: DeathToData"),
        ("Thorough validation and testing of all system components", "Expected: TheAuditor"),
        ("Building a balanced platform with trustworthy foundations", "Expected: Soulfra"),
    ]

    for text, expected in test_cases:
        brand, confidence = predict_brand(text)

        print(f"Text: {text[:60]}...")
        print(f"  {expected}")
        print(f"  Predicted: {brand} ({confidence:.1%} confidence)")
        print()


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_brand_predictions()
    else:
        # Train mode
        print("=" * 60)
        print("Brand Vocabulary Trainer")
        print("=" * 60)
        print()

        # Build dataset
        dataset = build_brand_training_dataset()

        if not dataset:
            print("❌ No training data available")
            print("   Create brand-post associations in brand_posts table")
            return

        print()

        # Show wordmaps
        print("📚 Brand Wordmaps (Top 10 words per brand):")
        for brand_slug, wordmap in dataset['brand_wordmaps'].items():
            metadata = dataset['brand_metadata'].get(brand_slug, {})
            emoji = metadata.get('emoji', '')
            personality = metadata.get('personality', '')

            print(f"\n  {emoji} {brand_slug} ({personality})")
            top_words = list(wordmap.items())[:10]
            words_str = ', '.join([f"{word} ({count})" for word, count in top_words])
            print(f"    {words_str}")

        print()

        # Train classifier
        model = train_brand_classifier(dataset)

        if model:
            # Save to database
            model_id = save_brand_model_to_db(model)

            print()
            print("=" * 60)
            print("✅ Training Complete!")
            print("=" * 60)
            print(f"Model ID: {model_id}")
            print(f"Brands trained: {len(model['brands'])}")
            print(f"Training examples: {model['training_size']}")
            print()

            # Test predictions
            test_brand_predictions()


if __name__ == '__main__':
    main()

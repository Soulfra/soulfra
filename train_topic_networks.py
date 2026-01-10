#!/usr/bin/env python3
"""
Train Topic-Specific Neural Networks

Instead of brand classifiers, train networks on specific topics:
- encryption
- privacy
- neural networks
- architecture
- etc.

This allows the neural network to:
1. Classify content by topic (not just brand)
2. Recommend posts based on conversation topics
3. Suggest content clusters for future posts
4. Build topic profiles for users

Usage:
    python3 train_topic_networks.py --topic encryption
    python3 train_topic_networks.py --topic privacy --brand deathtodata
    python3 train_topic_networks.py --topics encryption,privacy,surveillance
"""

import argparse
import sqlite3
import pickle
import os
from datetime import datetime
from pathlib import Path

# Try to import ML libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def fetch_posts_with_topic(topic, brand_slug=None):
    """Fetch posts that mention a specific topic"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Build query
    if brand_slug:
        cursor.execute("""
            SELECT p.id, p.title, p.content, p.slug, b.slug as brand_slug
            FROM posts p
            JOIN brands b ON p.brand_id = b.id
            WHERE (p.title LIKE ? OR p.content LIKE ?)
            AND b.slug = ?
        """, (f"%{topic}%", f"%{topic}%", brand_slug))
    else:
        cursor.execute("""
            SELECT p.id, p.title, p.content, p.slug, b.slug as brand_slug
            FROM posts p
            JOIN brands b ON p.brand_id = b.id
            WHERE p.title LIKE ? OR p.content LIKE ?
        """, (f"%{topic}%", f"%{topic}%"))

    posts = cursor.fetchall()
    conn.close()

    return posts

def fetch_all_posts_for_classification():
    """Fetch all posts with topic labels"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.title, p.content, p.slug, b.slug as brand_slug
        FROM posts p
        JOIN brands b ON p.brand_id = b.id
    """)

    posts = cursor.fetchall()
    conn.close()

    return posts

def create_topic_dataset(topics):
    """
    Create labeled dataset for topic classification

    For each post, determine which topics it covers based on keyword matching.
    Returns X (post content) and y (topic labels)
    """

    all_posts = fetch_all_posts_for_classification()

    X = []  # Post content
    y = []  # Topic labels

    for post_id, title, content, slug, brand_slug in all_posts:
        full_text = f"{title}\n\n{content}".lower()

        # Check which topics this post covers
        matched_topics = []
        for topic in topics:
            if topic.lower() in full_text:
                matched_topics.append(topic)

        # Add to dataset if it matches at least one topic
        if matched_topics:
            X.append(full_text)
            # Use primary topic (first match)
            y.append(matched_topics[0])

    return X, y

def train_topic_classifier(topics, model_name=None):
    """Train a classifier to identify topics in posts"""

    if not ML_AVAILABLE:
        print("✗ sklearn not installed. Run: pip install scikit-learn")
        return None

    print(f"\n{'='*60}")
    print(f"TRAINING TOPIC CLASSIFIER")
    print(f"Topics: {', '.join(topics)}")
    print(f"{'='*60}\n")

    # Create dataset
    X, y = create_topic_dataset(topics)

    if len(X) < 5:
        print(f"✗ Not enough posts with these topics (found {len(X)})")
        print(f"  Need at least 5 posts mentioning: {', '.join(topics)}")
        return None

    print(f"✓ Found {len(X)} posts covering these topics")

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"✓ Train: {len(X_train)} posts, Test: {len(X_test)} posts")

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Train classifier
    classifier = MultinomialNB()
    classifier.fit(X_train_tfidf, y_train)

    # Evaluate
    y_pred = classifier.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"✓ Training complete")
    print(f"  Accuracy: {accuracy:.2%}")
    print(f"\n{classification_report(y_test, y_pred)}")

    # Save model
    model_name = model_name or f"topic_classifier_{'_'.join(topics)}"
    model_dir = Path('neural_networks')
    model_dir.mkdir(exist_ok=True)

    model_path = model_dir / f"{model_name}.pkl"

    model_data = {
        'vectorizer': vectorizer,
        'classifier': classifier,
        'topics': topics,
        'accuracy': accuracy,
        'trained_at': datetime.now().isoformat(),
        'num_samples': len(X)
    }

    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"✓ Model saved: {model_path}")

    return model_path

def analyze_topic_coverage(topic, brand_slug=None):
    """Analyze how well a topic is covered in the blog"""

    posts = fetch_posts_with_topic(topic, brand_slug)

    print(f"\n{'='*60}")
    print(f"TOPIC COVERAGE ANALYSIS: {topic}")
    if brand_slug:
        print(f"Brand: {brand_slug}")
    print(f"{'='*60}\n")

    if not posts:
        print(f"✗ No posts found about '{topic}'")
        print(f"\n💡 Suggestion: Generate content about {topic}")
        print(f"   python3 force_claude_write.py --brand {brand_slug or 'soulfra'} --topic \"{topic}\" --save")
        return

    print(f"✓ Found {len(posts)} posts about '{topic}':\n")

    for post_id, title, content, slug, post_brand in posts:
        word_count = len(content.split())
        print(f"  • [{post_brand}] {title}")
        print(f"    {word_count} words | /post/{slug}")
        print()

    # Calculate stats
    total_words = sum(len(content.split()) for _, _, content, _, _ in posts)
    avg_words = total_words // len(posts) if posts else 0

    print(f"{'='*60}")
    print(f"STATS")
    print(f"  Total posts: {len(posts)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Average words/post: {avg_words:,}")
    print(f"{'='*60}\n")

def suggest_related_topics(topic):
    """Suggest related topics based on co-occurrence in posts"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Find posts with this topic
    cursor.execute("""
        SELECT content FROM posts
        WHERE title LIKE ? OR content LIKE ?
    """, (f"%{topic}%", f"%{topic}%"))

    posts_with_topic = cursor.fetchall()
    conn.close()

    if not posts_with_topic:
        return []

    # Extract common words (simple version - could use TF-IDF)
    word_freq = {}
    for (content,) in posts_with_topic:
        words = content.lower().split()
        for word in words:
            if len(word) > 4 and word != topic.lower():
                word_freq[word] = word_freq.get(word, 0) + 1

    # Get top 10 related words
    related = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    return [word for word, freq in related]

def main():
    parser = argparse.ArgumentParser(description="Train topic-specific neural networks")
    parser.add_argument("--topic", help="Single topic to analyze (e.g., 'encryption')")
    parser.add_argument("--topics", help="Comma-separated topics to train classifier on")
    parser.add_argument("--brand", help="Filter by brand slug")
    parser.add_argument("--train", action="store_true", help="Train classifier on topics")
    parser.add_argument("--analyze", action="store_true", help="Analyze topic coverage")
    parser.add_argument("--suggest", action="store_true", help="Suggest related topics")

    args = parser.parse_args()

    # Single topic analysis
    if args.topic:
        if args.analyze or (not args.train and not args.suggest):
            analyze_topic_coverage(args.topic, args.brand)

        if args.suggest:
            related = suggest_related_topics(args.topic)
            print(f"\n💡 Related topics to '{args.topic}':")
            for word in related:
                print(f"   • {word}")
            print()

    # Multi-topic classifier training
    if args.topics and args.train:
        topic_list = [t.strip() for t in args.topics.split(',')]
        train_topic_classifier(topic_list)

    # Help message if no args
    if not any([args.topic, args.topics]):
        print("\nUsage examples:")
        print("  python3 train_topic_networks.py --topic encryption --analyze")
        print("  python3 train_topic_networks.py --topic privacy --brand deathtodata")
        print("  python3 train_topic_networks.py --topics encryption,privacy,surveillance --train")
        print("  python3 train_topic_networks.py --topic encryption --suggest")
        print()

if __name__ == "__main__":
    main()

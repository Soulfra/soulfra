#!/usr/bin/env python3
"""
Neural Soul Scorer - AI "Soul" Ratings for Content

Uses 4 neural networks to score content (0.0-1.0):
- soulfra_judge: Overall quality and authenticity
- calriven: Creativity and originality
- theauditor: Accuracy and truthfulness
- deathtodata: Simplicity and clarity

Composite soul score is the average of all 4 networks.

Soul Tiers:
- 0.9-1.0: Legendary Soul 🌟
- 0.7-0.9: High Soul ⭐
- 0.5-0.7: Moderate Soul ⚡
- 0.3-0.5: Low Soul 💧
- 0.0-0.3: No Soul ❌

Usage:
    python3 neural_soul_scorer.py --post 29
    python3 neural_soul_scorer.py --all
    python3 neural_soul_scorer.py --user 5
    python3 neural_soul_scorer.py --comment 123

Architecture:
    TIER 3: AI/Neural Network Layer
    - Reads content from database
    - Scores with 4 neural networks
    - Stores results in neural_ratings table
    - Calculates composite score in soul_scores table
"""

import os
import sys
import json
from datetime import datetime
from database import get_db
import hashlib


# =============================================================================
# Neural Network Scoring
# =============================================================================

def load_neural_network(network_name):
    """
    Load neural network from database

    Args:
        network_name: Name of network (soulfra_judge, calriven, theauditor, deathtodata)

    Returns:
        dict with network details
    """
    db = get_db()
    network = db.execute(
        'SELECT * FROM neural_networks WHERE model_name = ?',
        (network_name,)
    ).fetchone()
    db.close()

    if not network:
        raise ValueError(f"Neural network not found: {network_name}")

    return dict(network)


def score_with_network(network_name, content, content_type='post'):
    """
    Score content with a single neural network

    Args:
        network_name: Name of network
        content: Text content to score
        content_type: Type of content (post, comment, user)

    Returns:
        dict with score, confidence, reasoning
    """
    # Load network
    network = load_neural_network(network_name)

    # Network-specific scoring logic (check both short and full names)
    if 'soulfra_judge' in network_name:
        # Overall quality and authenticity
        score, confidence, reasoning = score_quality_authenticity(content, network)

    elif 'calriven' in network_name:
        # Creativity and originality
        score, confidence, reasoning = score_creativity_originality(content, network)

    elif 'theauditor' in network_name or 'auditor' in network_name:
        # Accuracy and truthfulness
        score, confidence, reasoning = score_accuracy_truthfulness(content, network)

    elif 'deathtodata' in network_name:
        # Simplicity and clarity
        score, confidence, reasoning = score_simplicity_clarity(content, network)

    else:
        raise ValueError(f"Unknown network: {network_name}")

    return {
        'score': score,
        'confidence': confidence,
        'reasoning': reasoning,
        'network_name': network_name
    }


def score_quality_authenticity(content, network):
    """
    soulfra_judge: Score overall quality and authenticity

    Factors:
    - Length (longer = more effort)
    - Depth (detailed vs surface)
    - Personal voice (authentic vs generic)
    - Useful information (actionable vs fluff)
    """
    score = 0.5  # Base score
    confidence = 0.7
    reasons = []

    # Length factor
    word_count = len(content.split())
    if word_count > 1000:
        score += 0.15
        reasons.append("substantial length")
    elif word_count > 500:
        score += 0.10
        reasons.append("good length")
    elif word_count < 100:
        score -= 0.10
        reasons.append("very brief")

    # Depth factor - look for examples, details
    if '1.' in content or '2.' in content or '-' in content:
        score += 0.10
        reasons.append("structured with lists")

    if 'example' in content.lower() or 'for instance' in content.lower():
        score += 0.08
        reasons.append("includes examples")

    # Personal voice
    first_person = content.lower().count('i ') + content.lower().count("i've") + content.lower().count("i'm")
    if first_person > 3:
        score += 0.12
        reasons.append("personal perspective")

    # Useful information - questions answered
    if '?' in content and content.count('?') <= 5:
        score += 0.05
        reasons.append("addresses questions")

    # Cap score
    score = min(1.0, max(0.0, score))

    reasoning = f"Quality/Authenticity: {', '.join(reasons) if reasons else 'standard content'}"

    return score, confidence, reasoning


def score_creativity_originality(content, network):
    """
    calriven: Score creativity and originality

    Factors:
    - Unique word choices
    - Metaphors and analogies
    - Uncommon perspective
    - Novel combinations
    """
    score = 0.5  # Base score
    confidence = 0.65
    reasons = []

    # Metaphors/analogies
    metaphor_words = ['like', 'as if', 'similar to', 'reminds me of', 'think of it as']
    metaphor_count = sum(content.lower().count(word) for word in metaphor_words)
    if metaphor_count > 2:
        score += 0.15
        reasons.append("uses metaphors")

    # Unique word diversity
    words = content.lower().split()
    unique_ratio = len(set(words)) / len(words) if words else 0
    if unique_ratio > 0.7:
        score += 0.12
        reasons.append("diverse vocabulary")
    elif unique_ratio < 0.4:
        score -= 0.08
        reasons.append("repetitive vocabulary")

    # Uncommon perspective markers
    perspective_words = ['however', 'interestingly', 'surprisingly', 'contrary to', 'unlike']
    perspective_count = sum(content.lower().count(word) for word in perspective_words)
    if perspective_count > 1:
        score += 0.10
        reasons.append("fresh perspective")

    # Creative formatting
    if '---' in content or '===' in content or '*' in content:
        score += 0.08
        reasons.append("creative formatting")

    # Cap score
    score = min(1.0, max(0.0, score))

    reasoning = f"Creativity/Originality: {', '.join(reasons) if reasons else 'standard creativity'}"

    return score, confidence, reasoning


def score_accuracy_truthfulness(content, network):
    """
    theauditor: Score accuracy and truthfulness

    Factors:
    - Citations/sources
    - Specific numbers/dates
    - Qualifiers (might, could, possibly)
    - Absolute claims without evidence
    """
    score = 0.6  # Base score (assume truthful until proven otherwise)
    confidence = 0.60
    reasons = []

    # Citations/sources
    if 'source:' in content.lower() or 'according to' in content.lower() or 'study' in content.lower():
        score += 0.15
        reasons.append("cites sources")

    # Specific numbers/dates
    import re
    numbers = re.findall(r'\d+', content)
    if len(numbers) > 5:
        score += 0.10
        reasons.append("includes specific data")

    # Qualifiers (shows epistemic humility)
    qualifiers = ['might', 'could', 'possibly', 'likely', 'probably', 'typically', 'generally']
    qualifier_count = sum(content.lower().count(word) for word in qualifiers)
    if qualifier_count > 2:
        score += 0.08
        reasons.append("appropriate qualifiers")

    # Absolute claims (red flag)
    absolute_words = ['always', 'never', 'everyone', 'nobody', 'guaranteed', 'proven fact']
    absolute_count = sum(content.lower().count(word) for word in absolute_words)
    if absolute_count > 2:
        score -= 0.12
        reasons.append("many absolute claims")

    # Cap score
    score = min(1.0, max(0.0, score))

    reasoning = f"Accuracy/Truthfulness: {', '.join(reasons) if reasons else 'standard accuracy'}"

    return score, confidence, reasoning


def score_simplicity_clarity(content, network):
    """
    deathtodata: Score simplicity and clarity

    Factors:
    - Sentence length (shorter = clearer)
    - Jargon (less = simpler)
    - Structure (headings, lists)
    - Readability
    """
    score = 0.5  # Base score
    confidence = 0.75
    reasons = []

    # Sentence length
    sentences = content.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

    if avg_sentence_length < 15:
        score += 0.15
        reasons.append("concise sentences")
    elif avg_sentence_length < 25:
        score += 0.08
        reasons.append("readable sentences")
    elif avg_sentence_length > 40:
        score -= 0.10
        reasons.append("long sentences")

    # Structure (headings, lists)
    if '#' in content or '##' in content:
        score += 0.12
        reasons.append("clear headings")

    if content.count('\n') > 5:
        score += 0.08
        reasons.append("well-structured")

    # Jargon detection (long uncommon words)
    words = content.split()
    long_words = [w for w in words if len(w) > 12]
    jargon_ratio = len(long_words) / len(words) if words else 0

    if jargon_ratio < 0.05:
        score += 0.10
        reasons.append("simple language")
    elif jargon_ratio > 0.15:
        score -= 0.08
        reasons.append("complex terminology")

    # Clear formatting
    if '1.' in content or '- ' in content:
        score += 0.05
        reasons.append("uses lists")

    # Cap score
    score = min(1.0, max(0.0, score))

    reasoning = f"Simplicity/Clarity: {', '.join(reasons) if reasons else 'standard clarity'}"

    return score, confidence, reasoning


# =============================================================================
# Database Operations
# =============================================================================

def save_neural_rating(entity_type, entity_id, network_name, score, confidence, reasoning):
    """
    Save neural rating to database

    Args:
        entity_type: 'post', 'user', 'comment'
        entity_id: ID of entity
        network_name: Name of network
        score: Score (0.0-1.0)
        confidence: Confidence (0.0-1.0)
        reasoning: Text explanation
    """
    db = get_db()

    # Insert or replace (UNIQUE constraint on entity_type, entity_id, network_name)
    db.execute('''
        INSERT OR REPLACE INTO neural_ratings
        (entity_type, entity_id, network_name, score, confidence, reasoning, rated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (entity_type, entity_id, network_name, score, confidence, reasoning, datetime.now()))

    db.commit()
    db.close()


def calculate_composite_soul_score(entity_type, entity_id):
    """
    Calculate composite soul score from all neural ratings

    Args:
        entity_type: 'post', 'user', 'comment'
        entity_id: ID of entity

    Returns:
        dict with composite_score, tier, total_networks
    """
    db = get_db()

    # Get all ratings for this entity
    ratings = db.execute('''
        SELECT score FROM neural_ratings
        WHERE entity_type = ? AND entity_id = ?
    ''', (entity_type, entity_id)).fetchall()

    if not ratings:
        db.close()
        return None

    # Calculate average
    scores = [r['score'] for r in ratings]
    composite_score = sum(scores) / len(scores)
    total_networks = len(scores)

    # Determine tier
    if composite_score >= 0.9:
        tier = 'Legendary'
    elif composite_score >= 0.7:
        tier = 'High'
    elif composite_score >= 0.5:
        tier = 'Moderate'
    elif composite_score >= 0.3:
        tier = 'Low'
    else:
        tier = 'None'

    # Save to soul_scores table
    db.execute('''
        INSERT OR REPLACE INTO soul_scores
        (entity_type, entity_id, composite_score, tier, total_networks, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (entity_type, entity_id, composite_score, tier, total_networks, datetime.now()))

    db.commit()
    db.close()

    return {
        'composite_score': composite_score,
        'tier': tier,
        'total_networks': total_networks
    }


# =============================================================================
# Entity Scoring
# =============================================================================

def score_post(post_id):
    """
    Score a post with all 4 neural networks

    Args:
        post_id: ID of post

    Returns:
        dict with composite soul score
    """
    # Get post content
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    db.close()

    if not post:
        raise ValueError(f"Post not found: {post_id}")

    post = dict(post)
    content = f"{post['title']}\n\n{post['content']}"

    print(f"\n📊 Scoring Post #{post_id}: {post['title'][:50]}...")

    # Score with all 4 networks (use full names from database)
    networks = [
        'soulfra_judge',
        'calriven_technical_classifier',
        'theauditor_validation_classifier',
        'deathtodata_privacy_classifier'
    ]

    for network in networks:
        result = score_with_network(network, content, 'post')
        save_neural_rating('post', post_id, network, result['score'], result['confidence'], result['reasoning'])
        print(f"   {network:15} → {result['score']:.2f} ({result['reasoning']})")

    # Calculate composite score
    composite = calculate_composite_soul_score('post', post_id)

    if composite:
        tier_emoji = {
            'Legendary': '🌟',
            'High': '⭐',
            'Moderate': '⚡',
            'Low': '💧',
            'None': '❌'
        }
        emoji = tier_emoji.get(composite['tier'], '')

        print(f"\n   ✅ Composite Soul Score: {composite['composite_score']:.2f} \"{composite['tier']}\" {emoji}")
        print(f"   📈 Rated by {composite['total_networks']} neural networks")

    return composite


def score_all_posts():
    """
    Score all published posts

    Returns:
        Number of posts scored
    """
    db = get_db()
    posts = db.execute('''
        SELECT id FROM posts
        WHERE published_at IS NOT NULL
        ORDER BY id ASC
    ''').fetchall()
    db.close()

    if not posts:
        print("❌ No published posts found")
        return 0

    print("=" * 70)
    print("📊 NEURAL SOUL SCORER - Scoring All Posts")
    print("=" * 70)
    print(f"\n📋 Found {len(posts)} published post(s)")

    scored = 0
    for post_row in posts:
        try:
            score_post(post_row['id'])
            scored += 1
        except Exception as e:
            print(f"   ❌ Error scoring post {post_row['id']}: {e}")

    print("\n" + "=" * 70)
    print(f"✅ Scored {scored}/{len(posts)} post(s)")
    print("=" * 70)

    return scored


def score_user(user_id):
    """
    Score a user based on their posts and comments

    Args:
        user_id: ID of user

    Returns:
        dict with composite soul score
    """
    db = get_db()

    # Get user's posts
    posts = db.execute('SELECT content FROM posts WHERE author_id = ?', (user_id,)).fetchall()

    # Get user's comments
    comments = db.execute('SELECT content FROM comments WHERE user_id = ?', (user_id,)).fetchall()

    db.close()

    # Combine all content
    all_content = '\n\n'.join([p['content'] for p in posts] + [c['content'] for c in comments])

    if not all_content.strip():
        raise ValueError(f"User {user_id} has no content to score")

    print(f"\n📊 Scoring User #{user_id}...")

    # Score with all 4 networks (use full names from database)
    networks = [
        'soulfra_judge',
        'calriven_technical_classifier',
        'theauditor_validation_classifier',
        'deathtodata_privacy_classifier'
    ]

    for network in networks:
        result = score_with_network(network, all_content, 'user')
        save_neural_rating('user', user_id, network, result['score'], result['confidence'], result['reasoning'])
        print(f"   {network:15} → {result['score']:.2f}")

    # Calculate composite score
    composite = calculate_composite_soul_score('user', user_id)

    if composite:
        print(f"\n   ✅ Composite Soul Score: {composite['composite_score']:.2f} \"{composite['tier']}\"")

    return composite


def score_comment(comment_id):
    """
    Score a comment

    Args:
        comment_id: ID of comment

    Returns:
        dict with composite soul score
    """
    db = get_db()
    comment = db.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()
    db.close()

    if not comment:
        raise ValueError(f"Comment not found: {comment_id}")

    comment = dict(comment)
    content = comment['content']

    print(f"\n📊 Scoring Comment #{comment_id}...")

    # Score with all 4 networks (use full names from database)
    networks = [
        'soulfra_judge',
        'calriven_technical_classifier',
        'theauditor_validation_classifier',
        'deathtodata_privacy_classifier'
    ]

    for network in networks:
        result = score_with_network(network, content, 'comment')
        save_neural_rating('comment', comment_id, network, result['score'], result['confidence'], result['reasoning'])
        print(f"   {network:15} → {result['score']:.2f}")

    # Calculate composite score
    composite = calculate_composite_soul_score('comment', comment_id)

    if composite:
        print(f"\n   ✅ Composite Soul Score: {composite['composite_score']:.2f} \"{composite['tier']}\"")

    return composite


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for neural soul scorer"""

    if '--help' in sys.argv:
        print(__doc__)
        return

    if '--all' in sys.argv:
        score_all_posts()

    elif '--post' in sys.argv:
        idx = sys.argv.index('--post')
        if idx + 1 < len(sys.argv):
            post_id = int(sys.argv[idx + 1])
            score_post(post_id)

    elif '--user' in sys.argv:
        idx = sys.argv.index('--user')
        if idx + 1 < len(sys.argv):
            user_id = int(sys.argv[idx + 1])
            score_user(user_id)

    elif '--comment' in sys.argv:
        idx = sys.argv.index('--comment')
        if idx + 1 < len(sys.argv):
            comment_id = int(sys.argv[idx + 1])
            score_comment(comment_id)

    else:
        print("Usage:")
        print("  python3 neural_soul_scorer.py --all")
        print("  python3 neural_soul_scorer.py --post 29")
        print("  python3 neural_soul_scorer.py --user 5")
        print("  python3 neural_soul_scorer.py --comment 123")


if __name__ == '__main__':
    main()

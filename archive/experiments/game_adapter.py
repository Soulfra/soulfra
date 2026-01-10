#!/usr/bin/env python3
"""
Game Adapter - Neural Hub Integration for Game Reviews

Connects the game sharing system to the neural hub for intelligent routing
of peer reviews to appropriate channels (email, blog, forum, IRC).

Philosophy:
-----------
When a peer review is completed, it shouldn't just sit in the database.
The neural hub analyzes it and routes it to the right channels:
- Technical feedback → Developer channels (forum, IRC)
- High-quality reviews → Featured on blog
- Privacy concerns → Secure channels only
- General feedback → All channels

Usage:
    from game_adapter import route_review_to_channels

    # After review is submitted and analyzed
    route_review_to_channels(review_id)
"""

from typing import Dict, Any, List
import json


def route_review_to_channels(review_id: int) -> Dict[str, Any]:
    """
    Route a completed review through the neural hub

    Args:
        review_id: ID of the review to route

    Returns:
        Dict with routing results:
        - hub_message_id: Message ID in hub
        - target_channels: List of channels routed to
        - classifications: Neural network results
        - reason: Why it was routed this way
    """
    from game_sharing import get_review, get_game_share
    from neural_hub import process_message
    from database import get_db

    # Get the review
    review = get_review(review_id)
    if not review:
        return {'error': 'Review not found'}

    # Get the game share
    db = get_db()
    share_row = db.execute('SELECT * FROM game_shares WHERE id = ?', (review['game_share_id'],)).fetchone()
    share = dict(share_row)
    share['game_data'] = json.loads(share['game_data'])

    # Prepare content for neural hub
    content = f"""Peer Review Completed

Game Type: {share['game_type']}
Overall Rating: {review['overall_rating']}/5
Helpfulness Score: {review.get('helpfulness_score', 0):.2f}

Review Data: {json.dumps(review['review_data'], indent=2)}

Reviewer: {review['reviewer_name'] or review['reviewer_email']}
Anonymous: {review['is_anonymous']}
"""

    # Prepare metadata
    metadata = {
        'source': 'game_review',
        'game_share_id': share['id'],
        'review_id': review_id,
        'game_type': share['game_type'],
        'overall_rating': review['overall_rating'],
        'helpfulness_score': review.get('helpfulness_score'),
        'reviewer_email': review['reviewer_email'],
        'is_anonymous': review['is_anonymous']
    }

    # Route through neural hub
    result = process_message(
        content=content,
        source='game_review',
        metadata=metadata
    )

    return result


def get_routing_stats() -> Dict[str, Any]:
    """
    Get statistics about review routing

    Returns:
        Dict with routing statistics
    """
    from database import get_db

    db = get_db()

    # Get all game review messages from hub
    messages = db.execute('''
        SELECT COUNT(*) as count
        FROM hub_messages
        WHERE source = 'game_review'
    ''').fetchone()

    total_routed = messages['count']

    # Get routing decisions
    routing_stats = db.execute('''
        SELECT
            r.target_channels,
            COUNT(*) as count
        FROM hub_routing_log r
        JOIN hub_messages m ON m.id = r.message_id
        WHERE m.source = 'game_review'
        GROUP BY r.target_channels
        ORDER BY count DESC
    ''').fetchall()

    channel_distribution = {}
    for row in routing_stats:
        channels = json.loads(row['target_channels'])
        key = ', '.join(sorted(channels))
        channel_distribution[key] = row['count']

    return {
        'total_reviews_routed': total_routed,
        'channel_distribution': channel_distribution
    }


def route_all_pending_reviews():
    """
    Route all reviews that haven't been routed yet

    Returns:
        Dict with count of reviews routed
    """
    from database import get_db

    db = get_db()

    # Get all reviews that have been analyzed but not routed
    # (reviews with neural_classification but no hub entry)
    reviews = db.execute('''
        SELECT r.id, r.neural_classification
        FROM game_reviews r
        WHERE r.neural_classification IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM hub_messages m
              WHERE m.source = 'game_review'
                AND json_extract(m.metadata, '$.review_id') = r.id
          )
    ''').fetchall()

    results = []
    for review in reviews:
        try:
            result = route_review_to_channels(review['id'])
            results.append({
                'review_id': review['id'],
                'success': True,
                'result': result
            })
        except Exception as e:
            results.append({
                'review_id': review['id'],
                'success': False,
                'error': str(e)
            })

    return {
        'total_processed': len(reviews),
        'results': results
    }


def analyze_review_routing_quality():
    """
    Analyze the quality of review routing decisions

    Returns:
        Dict with quality metrics
    """
    from database import get_db

    db = get_db()

    # Get reviews with their routing info
    data = db.execute('''
        SELECT
            r.overall_rating,
            r.helpfulness_score,
            r.neural_classification,
            rl.target_channels,
            rl.reason
        FROM game_reviews r
        JOIN hub_messages m ON json_extract(m.metadata, '$.review_id') = r.id
        JOIN hub_routing_log rl ON rl.message_id = m.id
        WHERE r.neural_classification IS NOT NULL
    ''').fetchall()

    if not data:
        return {'error': 'No routed reviews found'}

    # Analyze correlation between helpfulness and channels
    high_quality_reviews = []
    for row in data:
        if row['helpfulness_score'] and row['helpfulness_score'] > 0.7:
            channels = json.loads(row['target_channels'])
            high_quality_reviews.append({
                'rating': row['overall_rating'],
                'helpfulness': row['helpfulness_score'],
                'channels': channels,
                'reason': row['reason']
            })

    return {
        'total_reviews': len(data),
        'high_quality_count': len(high_quality_reviews),
        'high_quality_percentage': (len(high_quality_reviews) / len(data) * 100) if data else 0,
        'high_quality_samples': high_quality_reviews[:5]  # Show top 5
    }


# ==============================================================================
# CLI & TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🎮 Game Adapter - Neural Hub Integration\n")

    # Get routing stats
    print("="*70)
    print("ROUTING STATISTICS")
    print("="*70)

    stats = get_routing_stats()
    print(f"Total reviews routed: {stats['total_reviews_routed']}")
    print("\nChannel Distribution:")
    for channels, count in stats['channel_distribution'].items():
        print(f"  {channels}: {count}")

    # Check for pending reviews
    print("\n" + "="*70)
    print("ROUTING PENDING REVIEWS")
    print("="*70)

    result = route_all_pending_reviews()
    print(f"Processed {result['total_processed']} reviews")

    successful = sum(1 for r in result['results'] if r['success'])
    print(f"✅ Successfully routed: {successful}")
    print(f"❌ Failed: {result['total_processed'] - successful}")

    # Analyze quality
    print("\n" + "="*70)
    print("ROUTING QUALITY ANALYSIS")
    print("="*70)

    quality = analyze_review_routing_quality()
    if 'error' in quality:
        print(f"⚠️  {quality['error']}")
    else:
        print(f"Total reviews analyzed: {quality['total_reviews']}")
        print(f"High quality reviews: {quality['high_quality_count']} ({quality['high_quality_percentage']:.1f}%)")

        if quality['high_quality_samples']:
            print("\nTop high-quality reviews:")
            for i, sample in enumerate(quality['high_quality_samples'], 1):
                print(f"\n{i}. Rating: {sample['rating']}/5, Helpfulness: {sample['helpfulness']:.2f}")
                print(f"   Channels: {', '.join(sample['channels'])}")
                print(f"   Reason: {sample['reason']}")

    print("\n✅ Game adapter working!")

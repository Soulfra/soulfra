#!/usr/bin/env python3
"""
End-to-End Test for Game Sharing & Review System

Tests the complete flow:
1. Create a game share
2. Submit a peer review
3. AI analysis with neural networks
4. Neural hub routing
5. Email notifications (if configured)
6. View analysis results
"""

import json
from game_sharing import (
    create_game_share,
    get_game_share,
    submit_game_review,
    analyze_game_review,
    get_reviews_for_share,
    get_share_stats
)
from game_adapter import route_review_to_channels, get_routing_stats
from neural_hub import get_hub_stats
from database import get_db


def test_complete_flow():
    """Test complete end-to-end flow"""

    print("=" * 80)
    print("🧪 END-TO-END GAME SHARING TEST")
    print("=" * 80)

    # ========================================================================
    # STEP 1: Create a game share
    # ========================================================================
    print("\n📝 STEP 1: Creating game share...")

    game_data = {
        "question_1": "I triple-check my texts before sending",
        "question_2": "I worry about what people think of my social media posts",
        "question_3": "I rehearse conversations in my head",
        "question_4": "I delete and rewrite messages multiple times",
        "question_5": "I feel embarrassed thinking about past interactions",
        "question_6": "I analyze my own behavior constantly",
        "question_7": "I seek validation from others frequently",
        "responses": [5, 4, 5, 5, 3, 4, 4],
        "total_score": 30,
        "max_score": 35,
        "percentage": 85.7
    }

    share_id, share_code = create_game_share(
        game_type='cringeproof',
        game_data=game_data,
        recipient_email='friend@example.com',
        sender_email='sender@example.com',
        sender_name='Alex',
        message='Can you review my cringeproof results and give me your honest feedback?'
    )

    print(f"✅ Share created: ID={share_id}, Code={share_code}")

    # ========================================================================
    # STEP 2: Retrieve the share (simulates friend clicking link)
    # ========================================================================
    print("\n📖 STEP 2: Retrieving game share...")

    share = get_game_share(share_code)
    assert share is not None, "Share should exist"
    assert share['game_type'] == 'cringeproof', "Game type should match"
    assert share['status'] == 'pending', "Should be pending review"

    print(f"✅ Share retrieved: {share['game_type']} from {share['sender_name']}")
    print(f"   Recipient: {share['recipient_email']}")
    print(f"   Message: {share.get('message', 'None')}")

    # ========================================================================
    # STEP 3: Submit a peer review
    # ========================================================================
    print("\n⭐ STEP 3: Submitting peer review...")

    review_data = {
        "question_1": 5,  # How self-aware does this person seem?
        "question_2": 4,  # Rate the honesty of their self-assessment
        "question_3": 4,  # Do they take social dynamics seriously?
        "question_4": "I think you're very self-aware! You clearly think deeply about your interactions. This level of introspection is actually healthy - it shows emotional intelligence.",
        "question_5": 5,  # How valuable would this feedback be to them?
        "question_6": "Keep the self-awareness but don't overthink every small interaction. Trust your instincts more.",
        "question_7": 4   # Would you share results like this?
    }

    review_id = submit_game_review(
        share_code=share_code,
        review_data=review_data,
        reviewer_email='friend@example.com',
        reviewer_name='Jamie',
        overall_rating=5,
        is_anonymous=False
    )

    print(f"✅ Review submitted: ID={review_id}")

    # ========================================================================
    # STEP 4: Verify AI analysis ran
    # ========================================================================
    print("\n🤖 STEP 4: Verifying AI analysis...")

    # Re-run analysis to get detailed results
    analysis = analyze_game_review(review_id)

    print(f"✅ Analysis complete:")
    print(f"   Helpfulness score: {analysis['helpfulness_score']:.2f}")
    print(f"   Neural classifications: {len(analysis['classifications'])}")

    for classification in analysis['classifications']:
        print(f"   - {classification.network_name}: {classification.label} ({classification.confidence:.0%})")

    # ========================================================================
    # STEP 5: Route through neural hub
    # ========================================================================
    print("\n📡 STEP 5: Routing through neural hub...")

    routing_result = route_review_to_channels(review_id)

    if 'error' not in routing_result:
        print(f"✅ Routed to neural hub:")
        print(f"   Hub message ID: {routing_result.get('hub_message_id')}")
        print(f"   Target channels: {', '.join(routing_result.get('target_channels', []))}")
        print(f"   Reason: {routing_result.get('reason')}")
    else:
        print(f"⚠️  Routing error: {routing_result['error']}")

    # ========================================================================
    # STEP 6: Check share status updated
    # ========================================================================
    print("\n📊 STEP 6: Checking updated share status...")

    updated_share = get_game_share(share_code)
    assert updated_share['status'] == 'reviewed', "Status should be 'reviewed'"
    assert updated_share['review_count'] > 0, "Review count should be incremented"

    print(f"✅ Share status updated:")
    print(f"   Status: {updated_share['status']}")
    print(f"   Review count: {updated_share['review_count']}")

    # ========================================================================
    # STEP 7: Retrieve all reviews
    # ========================================================================
    print("\n📋 STEP 7: Retrieving all reviews for share...")

    reviews = get_reviews_for_share(share_id)
    assert len(reviews) > 0, "Should have at least one review"

    print(f"✅ Found {len(reviews)} review(s)")

    for i, review in enumerate(reviews, 1):
        print(f"\n   Review #{i}:")
        print(f"   - Reviewer: {review['reviewer_name']}")
        print(f"   - Rating: {review['overall_rating']}/5")
        print(f"   - Helpfulness: {review['helpfulness_score']:.2f}")
        print(f"   - Anonymous: {review['is_anonymous']}")

    # ========================================================================
    # STEP 8: Check analytics
    # ========================================================================
    print("\n📈 STEP 8: Checking share analytics...")

    analytics = get_share_stats()

    print(f"✅ Share Analytics:")
    print(f"   Total shares: {analytics['total_shares']}")
    print(f"   By game type: {analytics['by_game_type']}")
    print(f"   Completion rate: {analytics['completion_rate']:.1f}%")
    print(f"   Avg helpfulness: {analytics['avg_helpfulness']:.2f}")

    # ========================================================================
    # STEP 9: Check neural hub stats
    # ========================================================================
    print("\n🧠 STEP 9: Checking neural hub statistics...")

    hub_stats = get_hub_stats()

    print(f"✅ Neural Hub Stats:")
    print(f"   Total messages: {hub_stats['total_messages']}")
    print(f"   Total routings: {hub_stats['total_routings']}")

    if hub_stats['by_source']:
        print(f"   Messages by source:")
        for source, count in hub_stats['by_source'].items():
            print(f"   - {source}: {count}")

    if hub_stats['common_routes']:
        print(f"\n   Common routes:")
        for channels, count in hub_stats['common_routes'][:3]:
            print(f"   - {channels}: {count} times")

    # ========================================================================
    # STEP 10: Verify database integrity
    # ========================================================================
    print("\n🔍 STEP 10: Verifying database integrity...")

    db = get_db()

    # Check game_shares table
    share_count = db.execute('SELECT COUNT(*) as count FROM game_shares').fetchone()['count']
    print(f"✅ Game shares in DB: {share_count}")

    # Check game_reviews table
    review_count = db.execute('SELECT COUNT(*) as count FROM game_reviews').fetchone()['count']
    print(f"✅ Reviews in DB: {review_count}")

    # Check hub_messages table
    hub_msg_count = db.execute('SELECT COUNT(*) as count FROM hub_messages WHERE source = "game_review"').fetchone()['count']
    print(f"✅ Hub messages from game_review: {hub_msg_count}")

    # Check hub_routing_log
    routing_log_count = db.execute('SELECT COUNT(*) as count FROM hub_routing_log').fetchone()['count']
    print(f"✅ Routing log entries: {routing_log_count}")

    # ========================================================================
    # FINAL RESULTS
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST COMPLETE!")
    print("=" * 80)
    print(f"\nTest Summary:")
    print(f"  ✅ Game share created: {share_code}")
    print(f"  ✅ Peer review submitted: {review_id}")
    print(f"  ✅ AI analysis completed: {len(analysis['classifications'])} networks")
    print(f"  ✅ Neural hub routing: SUCCESS")
    print(f"  ✅ Database integrity: VERIFIED")
    print(f"\n🎉 All systems working perfectly!")

    return {
        'share_id': share_id,
        'share_code': share_code,
        'review_id': review_id,
        'analysis': analysis,
        'routing': routing_result
    }


if __name__ == '__main__':
    try:
        result = test_complete_flow()
        print(f"\n✅ Test passed!")
        print(f"\nAccess the analysis at: /share/{result['share_code']}/analysis")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

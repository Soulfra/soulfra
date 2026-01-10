#!/usr/bin/env python3
"""
Twitter/X Integration for Soulfra

Auto-posts blog updates to Twitter with:
- Short URL from url_shortener.py
- QR code generation
- Engagement tracking
- Analytics logging

Setup:
1. Create Twitter Developer Account: https://developer.twitter.com
2. Create an App → Get API keys
3. Add to .env file:
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   TWITTER_BEARER_TOKEN=your_bearer_token

Usage:
    from integrations.twitter_integration import post_to_twitter, get_tweet_stats

    # Post a blog update
    tweet_id = post_to_twitter(
        post_id=42,
        custom_message="Check out my new AI models blog!"
    )

    # Get engagement stats
    stats = get_tweet_stats(tweet_id)
    print(f"Impressions: {stats['impressions']}, Likes: {stats['likes']}")
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_logger import log_integration_event
from url_shortener import generate_short_url
from database import get_db
import requests
import json
from datetime import datetime


# Twitter API v2 endpoints
TWITTER_API_BASE = 'https://api.twitter.com/2'
TWITTER_UPLOAD_API = 'https://upload.twitter.com/1.1/media/upload.json'


def get_twitter_credentials():
    """
    Load Twitter API credentials from environment

    Returns:
        dict: API credentials or None if not configured
    """
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    if not all([api_key, api_secret, access_token, access_secret, bearer_token]):
        print("⚠️ Twitter credentials not found in environment")
        print("   Set: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, TWITTER_BEARER_TOKEN")
        return None

    return {
        'api_key': api_key,
        'api_secret': api_secret,
        'access_token': access_token,
        'access_secret': access_secret,
        'bearer_token': bearer_token
    }


def create_tweet(text, media_ids=None):
    """
    Post a tweet using Twitter API v2

    Args:
        text (str): Tweet content (max 280 chars)
        media_ids (list): List of media IDs to attach (optional)

    Returns:
        dict: Tweet response with 'id', 'text', etc. or None if failed
    """
    creds = get_twitter_credentials()
    if not creds:
        print("❌ Cannot post tweet - missing credentials")
        return None

    # API v2 endpoint
    url = f'{TWITTER_API_BASE}/tweets'

    headers = {
        'Authorization': f"Bearer {creds['bearer_token']}",
        'Content-Type': 'application/json'
    }

    payload = {'text': text}

    if media_ids:
        payload['media'] = {'media_ids': media_ids}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        tweet_data = response.json()
        return tweet_data['data']

    except requests.exceptions.RequestException as e:
        print(f"❌ Twitter API error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return None


def get_post_details(post_id):
    """
    Get post details from database

    Args:
        post_id (int): Post ID

    Returns:
        dict: Post data or None
    """
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    db.close()

    return dict(post) if post else None


def post_to_twitter(post_id, custom_message=None, include_qr=False):
    """
    Post a blog update to Twitter

    Args:
        post_id (int): Blog post ID
        custom_message (str): Custom tweet text (optional, will auto-generate if not provided)
        include_qr (bool): Attach QR code image (default False)

    Returns:
        str: Tweet ID or None if failed

    Example:
        tweet_id = post_to_twitter(
            post_id=42,
            custom_message="🚀 New blog: AI Models Explained!\n\nRead here:",
            include_qr=True
        )
    """
    # Get post details
    post = get_post_details(post_id)
    if not post:
        print(f"❌ Post {post_id} not found")
        return None

    # Generate short URL
    from config import BASE_URL
    short_url = generate_short_url(f"post-{post_id}", base_url=BASE_URL)

    # Create tweet text
    if custom_message:
        tweet_text = f"{custom_message}\n\n{short_url}"
    else:
        # Auto-generate from post title
        title = post['title'][:200]  # Truncate if too long
        tweet_text = f"📝 New post: {title}\n\n{short_url}"

    # Ensure under 280 characters
    if len(tweet_text) > 280:
        # Truncate title to fit
        max_title_len = 280 - len(short_url) - 10  # 10 for "📝 New post: \n\n"
        title = post['title'][:max_title_len] + "..."
        tweet_text = f"📝 New post: {title}\n\n{short_url}"

    print(f"📤 Posting to Twitter: {tweet_text}")

    # TODO: Handle QR code attachment (requires media upload)
    media_ids = None
    if include_qr:
        print("⚠️ QR code attachment not yet implemented")

    # Post tweet
    tweet = create_tweet(tweet_text, media_ids=media_ids)

    if tweet:
        tweet_id = tweet['id']

        # Log to unified logger
        log_integration_event(
            platform='twitter',
            event_type='post_published',
            description=f"Posted tweet for: {post['title']}",
            metadata={
                'tweet_id': tweet_id,
                'tweet_text': tweet_text,
                'short_url': short_url
            },
            post_id=post_id
        )

        print(f"✅ Tweet posted: https://twitter.com/i/web/status/{tweet_id}")
        return tweet_id
    else:
        print("❌ Failed to post tweet")
        return None


def get_tweet_stats(tweet_id):
    """
    Get engagement stats for a tweet

    Args:
        tweet_id (str): Tweet ID

    Returns:
        dict: Stats (impressions, likes, retweets, etc.) or None

    Note: Requires Twitter API v2 with elevated access for full metrics
    """
    creds = get_twitter_credentials()
    if not creds:
        return None

    url = f'{TWITTER_API_BASE}/tweets/{tweet_id}'

    headers = {
        'Authorization': f"Bearer {creds['bearer_token']}"
    }

    # Request public metrics
    params = {
        'tweet.fields': 'public_metrics,created_at'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        tweet_data = data['data']

        metrics = tweet_data.get('public_metrics', {})

        stats = {
            'tweet_id': tweet_id,
            'created_at': tweet_data.get('created_at'),
            'likes': metrics.get('like_count', 0),
            'retweets': metrics.get('retweet_count', 0),
            'replies': metrics.get('reply_count', 0),
            'quotes': metrics.get('quote_count', 0),
            'impressions': metrics.get('impression_count', 0)  # Requires elevated access
        }

        # Log engagement update
        log_integration_event(
            platform='twitter',
            event_type='engagement_update',
            description=f"Tweet stats: {stats['likes']} likes, {stats['retweets']} retweets",
            metadata=stats
        )

        return stats

    except requests.exceptions.RequestException as e:
        print(f"❌ Twitter API error: {e}")
        return None


def sync_tweet_engagement(post_id):
    """
    Sync engagement stats for all tweets related to a post

    Args:
        post_id (int): Post ID

    Returns:
        dict: Aggregated stats

    Example:
        stats = sync_tweet_engagement(post_id=42)
        print(f"Total engagement: {stats['total_likes']} likes")
    """
    # Get all tweets for this post from integration logs
    from unified_logger import get_integration_logs

    logs = get_integration_logs(
        platform='twitter',
        event_type='post_published',
        post_id=post_id
    )

    if not logs:
        print(f"No tweets found for post {post_id}")
        return {}

    total_stats = {
        'total_likes': 0,
        'total_retweets': 0,
        'total_replies': 0,
        'total_impressions': 0,
        'tweets': []
    }

    for log in logs:
        tweet_id = log['metadata'].get('tweet_id')
        if tweet_id:
            stats = get_tweet_stats(tweet_id)
            if stats:
                total_stats['total_likes'] += stats['likes']
                total_stats['total_retweets'] += stats['retweets']
                total_stats['total_replies'] += stats['replies']
                total_stats['total_impressions'] += stats.get('impressions', 0)
                total_stats['tweets'].append(stats)

    print(f"📊 Post #{post_id} Twitter stats:")
    print(f"   {len(total_stats['tweets'])} tweets")
    print(f"   {total_stats['total_likes']} total likes")
    print(f"   {total_stats['total_retweets']} total retweets")
    print(f"   {total_stats['total_impressions']} total impressions")

    return total_stats


def test_twitter_integration():
    """Test Twitter integration (dry run without posting)"""
    print("=" * 70)
    print("🧪 Testing Twitter Integration")
    print("=" * 70)
    print()

    # Test 1: Check credentials
    print("TEST 1: Twitter Credentials")
    creds = get_twitter_credentials()
    if creds:
        print("   ✅ Credentials found")
        print(f"   API Key: {creds['api_key'][:10]}...")
    else:
        print("   ❌ Credentials not configured")
        print("   Set environment variables to enable Twitter posting")
    print()

    # Test 2: Get post details
    print("TEST 2: Get Post Details")
    post = get_post_details(post_id=1)
    if post:
        print(f"   Post: {post['title']}")
        print(f"   ID: {post['id']}")
    else:
        print("   ❌ No posts found in database")
    print()

    # Test 3: Generate tweet text (dry run)
    print("TEST 3: Generate Tweet Text")
    if post:
        from config import BASE_URL
        short_url = generate_short_url(f"post-{post['id']}", base_url=BASE_URL)
        tweet_text = f"📝 New post: {post['title']}\n\n{short_url}"

        print(f"   Tweet text ({len(tweet_text)} chars):")
        print(f"   {tweet_text}")
        print()

    # Test 4: Check existing Twitter logs
    print("TEST 4: Existing Twitter Logs")
    from unified_logger import get_integration_logs

    logs = get_integration_logs(platform='twitter', limit=5)
    print(f"   Found {len(logs)} Twitter events")
    for log in logs:
        print(f"      {log['created_at']} - {log['description']}")
    print()

    print("=" * 70)
    print("✅ Twitter integration tests complete")
    print("=" * 70)
    print()

    if not creds:
        print("⚠️ To enable Twitter posting:")
        print("   1. Create Twitter Developer App: https://developer.twitter.com")
        print("   2. Get API keys and tokens")
        print("   3. Add to .env file:")
        print("      TWITTER_API_KEY=...")
        print("      TWITTER_API_SECRET=...")
        print("      TWITTER_ACCESS_TOKEN=...")
        print("      TWITTER_ACCESS_SECRET=...")
        print("      TWITTER_BEARER_TOKEN=...")
    else:
        print("💡 To post a tweet:")
        print("   from integrations.twitter_integration import post_to_twitter")
        print("   tweet_id = post_to_twitter(post_id=1)")
    print()


if __name__ == '__main__':
    test_twitter_integration()

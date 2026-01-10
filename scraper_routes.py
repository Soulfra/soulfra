#!/usr/bin/env python3
"""
Voice Scraper API Routes

Endpoints for accessing scraped news articles.

Routes:
- GET /api/news/<recording_id> - Get articles for a recording
- GET /api/news/recent - Get recently scraped articles
- POST /api/news/scrape/<recording_id> - Manually trigger scraping
- GET /api/news/stats - Get scraping statistics
"""

from flask import Blueprint, jsonify, render_template_string
from voice_scraper import (
    get_recording_articles,
    get_recent_articles,
    scrape_for_recording,
    cleanup_expired_cache
)
from database import get_db

scraper_bp = Blueprint('scraper', __name__)


@scraper_bp.route('/api/news/<int:recording_id>')
def get_news_for_recording(recording_id):
    """
    Get all scraped articles for a voice recording

    Example:
        GET /api/news/123

    Response:
        {
            "success": true,
            "recording_id": 123,
            "articles": [
                {
                    "id": 1,
                    "title": "Breaking News...",
                    "url": "https://...",
                    "description": "...",
                    "source": "CNN",
                    "published_date": "2026-01-04T12:00:00Z",
                    "keywords": "news,breaking,politics",
                    "relevance_score": 0.9
                }
            ]
        }
    """
    articles = get_recording_articles(recording_id)

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'articles': articles
    })


@scraper_bp.route('/api/news/recent')
def get_recent_news():
    """
    Get recently scraped articles (global feed)

    Example:
        GET /api/news/recent

    Response:
        {
            "success": true,
            "articles": [...]
        }
    """
    articles = get_recent_articles(limit=20)

    return jsonify({
        'success': True,
        'articles': articles
    })


@scraper_bp.route('/api/news/scrape/<int:recording_id>', methods=['POST'])
def trigger_scrape(recording_id):
    """
    Manually trigger scraping for a recording

    Example:
        POST /api/news/scrape/123

    Response:
        {
            "success": true,
            "keywords": ["news", "article"],
            "articles_found": 5,
            "articles_new": 3,
            "articles_cached": 2
        }
    """
    result = scrape_for_recording(recording_id)

    if 'error' in result:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400

    return jsonify({
        'success': True,
        **result
    })


@scraper_bp.route('/api/news/stats')
def get_scraping_stats():
    """
    Get scraping statistics

    Example:
        GET /api/news/stats

    Response:
        {
            "success": true,
            "total_articles": 150,
            "cached_articles": 120,
            "expired_articles": 30,
            "recordings_with_articles": 45
        }
    """
    db = get_db()

    total_articles = db.execute('SELECT COUNT(*) as count FROM scraped_articles').fetchone()['count']

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    cached_articles = db.execute(
        'SELECT COUNT(*) as count FROM scraped_articles WHERE cache_expires > ?',
        (now,)
    ).fetchone()['count']

    expired_articles = total_articles - cached_articles

    recordings_with_articles = db.execute(
        'SELECT COUNT(DISTINCT recording_id) as count FROM recording_articles'
    ).fetchone()['count']

    return jsonify({
        'success': True,
        'total_articles': total_articles,
        'cached_articles': cached_articles,
        'expired_articles': expired_articles,
        'recordings_with_articles': recordings_with_articles
    })


@scraper_bp.route('/news/<int:recording_id>')
def view_recording_news(recording_id):
    """
    HTML page showing scraped news for a recording

    Example:
        GET /news/123
    """
    db = get_db()

    # Get recording info
    recording = db.execute('''
        SELECT id, transcription, created_at FROM simple_voice_recordings WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return "<h3>Recording not found</h3>", 404

    articles = get_recording_articles(recording_id)

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News for Recording #{{ recording_id }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            padding: 40px 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
            color: #00C49A;
        }
        .transcription {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        .transcription h3 {
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
            opacity: 0.7;
        }
        .articles-count {
            margin-bottom: 20px;
            opacity: 0.8;
            font-size: 14px;
        }
        .article {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .article:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(5px);
        }
        .article-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .article-title a {
            color: #00C49A;
            text-decoration: none;
        }
        .article-title a:hover {
            text-decoration: underline;
        }
        .article-meta {
            display: flex;
            gap: 15px;
            font-size: 12px;
            opacity: 0.7;
            margin-bottom: 10px;
        }
        .article-description {
            font-size: 14px;
            line-height: 1.5;
            opacity: 0.9;
        }
        .keywords {
            margin-top: 10px;
            font-size: 12px;
            opacity: 0.6;
        }
        .back-link {
            margin-top: 30px;
            text-align: center;
        }
        .back-link a {
            color: #00C49A;
            text-decoration: none;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 News for Recording #{{ recording_id }}</h1>

        <div class="transcription">
            <h3>Original Transcription:</h3>
            {{ transcription }}
        </div>

        <div class="articles-count">
            Found {{ articles|length }} related articles:
        </div>

        {% for article in articles %}
        <div class="article">
            <div class="article-title">
                <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
            </div>
            <div class="article-meta">
                <span>📰 {{ article.source }}</span>
                {% if article.published_date %}
                <span>🕐 {{ article.published_date[:10] }}</span>
                {% endif %}
                <span>⭐ Relevance: {{ (article.relevance_score * 100)|int }}%</span>
            </div>
            {% if article.description %}
            <div class="article-description">
                {{ article.description }}
            </div>
            {% endif %}
            <div class="keywords">
                🏷️ Keywords: {{ article.keywords }}
            </div>
        </div>
        {% endfor %}

        {% if not articles %}
        <div class="article">
            <p>No articles found yet. Try triggering a scrape:</p>
            <p style="margin-top: 10px;"><code>POST /api/news/scrape/{{ recording_id }}</code></p>
        </div>
        {% endif %}

        <div class="back-link">
            <a href="/">← Back to Home</a>
        </div>
    </div>
</body>
</html>"""

    return render_template_string(
        template,
        recording_id=recording_id,
        transcription=recording['transcription'],
        articles=articles
    )


@scraper_bp.route('/api/news/cleanup', methods=['POST'])
def cleanup_cache():
    """
    Manually trigger cache cleanup

    Example:
        POST /api/news/cleanup

    Response:
        {
            "success": true,
            "articles_deleted": 30
        }
    """
    deleted = cleanup_expired_cache()

    return jsonify({
        'success': True,
        'articles_deleted': deleted
    })

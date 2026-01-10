#!/usr/bin/env python3
"""
Voice-to-Scraper Engine

Automatically scrapes Google News and other sources based on voice recording keywords.

Features:
- Extract keywords from voice transcriptions
- Scrape Google News for those keywords
- Store articles in database with smart caching
- Link articles to voice recordings

Usage:
    from voice_scraper import scrape_for_recording, get_recording_articles

    # After saving a voice recording:
    scrape_for_recording(recording_id)

    # Get articles for a recording:
    articles = get_recording_articles(recording_id)
"""

import re
import hashlib
from datetime import datetime, timezone, timedelta
from database import get_db
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup


def create_scraper_tables():
    """
    Create tables for storing scraped articles

    Tables:
    - scraped_articles: Stores articles with caching
    - recording_articles: Links recordings to articles
    """
    db = get_db()

    # Table 1: Scraped articles (with cache)
    db.execute('''
        CREATE TABLE IF NOT EXISTS scraped_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            url_hash TEXT UNIQUE NOT NULL,
            title TEXT,
            description TEXT,
            source TEXT,
            published_date TEXT,
            keywords TEXT,
            scraped_at TEXT NOT NULL,
            cache_expires TEXT NOT NULL,
            is_cached INTEGER DEFAULT 1
        )
    ''')

    # Table 2: Recording-Article link
    db.execute('''
        CREATE TABLE IF NOT EXISTS recording_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            relevance_score REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
            FOREIGN KEY (article_id) REFERENCES scraped_articles(id)
        )
    ''')

    # Index for performance
    db.execute('CREATE INDEX IF NOT EXISTS idx_url_hash ON scraped_articles(url_hash)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_recording_articles ON recording_articles(recording_id)')

    db.commit()
    print("✅ Scraper tables created")


def extract_keywords(transcription):
    """
    Extract meaningful keywords from transcription

    Args:
        transcription (str): Voice recording transcription

    Returns:
        list: List of keywords (lowercase, deduplicated)

    Example:
        >>> extract_keywords("Ideas about cringeproof. It's a game about news articles.")
        ['ideas', 'cringeproof', 'game', 'news', 'articles']
    """
    if not transcription:
        return []

    # Lowercase and remove punctuation
    text = transcription.lower()
    text = re.sub(r'[^\w\s]', ' ', text)

    # Split into words
    words = text.split()

    # Filter out common stopwords
    stopwords = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'about', 'this', 'they', 'them',
        'their', 'what', 'which', 'who', 'you', 'your', 'my', 'me',
        'i', 'we', 'us', 'our', 'just', 'like', 'or', 'but', 'so', 'if',
        'when', 'where', 'how', 'why', 'can', 'could', 'would', 'should',
        'hello', 'hi', 'hey'
    }

    # Keep words longer than 3 chars and not in stopwords
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]

    # Deduplicate while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return unique_keywords[:10]  # Limit to top 10 keywords


def hash_url(url):
    """Generate SHA256 hash of URL for deduplication"""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def scrape_google_news(query, max_results=5):
    """
    Scrape Google News for a query

    Args:
        query (str): Search query
        max_results (int): Max number of results to return

    Returns:
        list: List of article dicts
            [
                {
                    'title': '...',
                    'url': '...',
                    'description': '...',
                    'source': '...',
                    'published_date': '...'
                },
                ...
            ]
    """
    articles = []

    try:
        # Google News search URL
        search_url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find article elements (Google News structure)
        article_elements = soup.find_all('article', limit=max_results)

        for article_el in article_elements:
            try:
                # Extract title
                title_el = article_el.find('a', class_='gPFEn')
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = 'https://news.google.com' + title_el['href'][1:]  # Remove leading '.'

                # Extract source
                source_el = article_el.find('a', class_='wEwyrc')
                source = source_el.get_text(strip=True) if source_el else 'Unknown'

                # Extract time (published date)
                time_el = article_el.find('time')
                published_date = time_el.get('datetime') if time_el and time_el.get('datetime') else None

                # Extract description (if available)
                desc_el = article_el.find('p')
                description = desc_el.get_text(strip=True) if desc_el else ''

                articles.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'source': source,
                    'published_date': published_date
                })

            except Exception as e:
                print(f"⚠️  Error parsing article: {e}")
                continue

    except Exception as e:
        print(f"⚠️  Google News scrape failed: {e}")

    return articles


def save_article(article, keywords):
    """
    Save article to database with caching

    Args:
        article (dict): Article data from scraper
        keywords (str): Comma-separated keywords

    Returns:
        int: article_id
    """
    db = get_db()

    url_hash = hash_url(article['url'])
    now = datetime.now(timezone.utc)
    cache_expires = now + timedelta(hours=24)  # Cache for 24 hours

    # Check if article already exists (and not expired)
    existing = db.execute('''
        SELECT id FROM scraped_articles
        WHERE url_hash = ? AND cache_expires > ?
    ''', (url_hash, now.isoformat())).fetchone()

    if existing:
        return existing['id']

    # Insert new article
    cursor = db.execute('''
        INSERT OR REPLACE INTO scraped_articles
        (url, url_hash, title, description, source, published_date, keywords, scraped_at, cache_expires)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        article['url'],
        url_hash,
        article['title'],
        article['description'],
        article['source'],
        article['published_date'],
        keywords,
        now.isoformat(),
        cache_expires.isoformat()
    ))

    db.commit()
    return cursor.lastrowid


def link_article_to_recording(recording_id, article_id, relevance_score=1.0):
    """
    Link article to recording

    Args:
        recording_id (int): Recording ID
        article_id (int): Article ID
        relevance_score (float): How relevant the article is (0.0-1.0)
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    # Avoid duplicate links
    existing = db.execute('''
        SELECT id FROM recording_articles
        WHERE recording_id = ? AND article_id = ?
    ''', (recording_id, article_id)).fetchone()

    if existing:
        return existing['id']

    cursor = db.execute('''
        INSERT INTO recording_articles (recording_id, article_id, relevance_score, created_at)
        VALUES (?, ?, ?, ?)
    ''', (recording_id, article_id, relevance_score, now))

    db.commit()
    return cursor.lastrowid


def scrape_for_recording(recording_id):
    """
    Main function: Scrape articles based on a voice recording

    Args:
        recording_id (int): Recording ID from simple_voice_recordings

    Returns:
        dict: Scraping results
            {
                'keywords': ['idea', 'game', 'news'],
                'articles_found': 5,
                'articles_cached': 2,
                'articles_new': 3
            }
    """
    db = get_db()

    # Get recording transcription
    recording = db.execute('''
        SELECT id, transcription FROM simple_voice_recordings WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording or not recording['transcription']:
        return {
            'error': 'Recording not found or has no transcription',
            'keywords': [],
            'articles_found': 0
        }

    # Extract keywords
    keywords = extract_keywords(recording['transcription'])

    if not keywords:
        return {
            'error': 'No meaningful keywords extracted',
            'keywords': [],
            'articles_found': 0
        }

    print(f"🔍 Scraping for keywords: {keywords}")

    # Scrape for each keyword
    all_articles = []
    articles_new = 0
    articles_cached = 0

    for keyword in keywords[:3]:  # Limit to first 3 keywords
        articles = scrape_google_news(keyword, max_results=3)

        for article in articles:
            # Save article (respects cache)
            article_id = save_article(article, ','.join(keywords))

            # Check if it was cached or new
            if article_id:
                db_article = db.execute('SELECT id, scraped_at FROM scraped_articles WHERE id = ?', (article_id,)).fetchone()
                if db_article:
                    # If scraped_at is recent (within last minute), it's new
                    scraped_time = datetime.fromisoformat(db_article['scraped_at'])
                    if (datetime.now(timezone.utc) - scraped_time).seconds < 60:
                        articles_new += 1
                    else:
                        articles_cached += 1

                # Link to recording
                link_article_to_recording(recording_id, article_id)

                all_articles.append(article)

    print(f"✅ Found {len(all_articles)} articles ({articles_new} new, {articles_cached} cached)")

    return {
        'keywords': keywords,
        'articles_found': len(all_articles),
        'articles_new': articles_new,
        'articles_cached': articles_cached,
        'articles': all_articles
    }


def get_recording_articles(recording_id):
    """
    Get all articles linked to a recording

    Args:
        recording_id (int): Recording ID

    Returns:
        list: List of article dicts
    """
    db = get_db()

    articles = db.execute('''
        SELECT
            a.id,
            a.url,
            a.title,
            a.description,
            a.source,
            a.published_date,
            a.keywords,
            ra.relevance_score
        FROM recording_articles ra
        JOIN scraped_articles a ON ra.article_id = a.id
        WHERE ra.recording_id = ?
        ORDER BY ra.created_at DESC
    ''', (recording_id,)).fetchall()

    return [dict(a) for a in articles]


def get_recent_articles(limit=20):
    """
    Get recently scraped articles (global feed)

    Args:
        limit (int): Max articles to return

    Returns:
        list: List of article dicts
    """
    db = get_db()

    articles = db.execute('''
        SELECT * FROM scraped_articles
        WHERE cache_expires > ?
        ORDER BY scraped_at DESC
        LIMIT ?
    ''', (datetime.now(timezone.utc).isoformat(), limit)).fetchall()

    return [dict(a) for a in articles]


def cleanup_expired_cache():
    """
    Remove expired articles from cache

    Returns:
        int: Number of articles removed
    """
    db = get_db()

    result = db.execute('''
        DELETE FROM scraped_articles
        WHERE cache_expires < ?
    ''', (datetime.now(timezone.utc).isoformat(),))

    deleted_count = result.rowcount
    db.commit()

    print(f"🗑️  Cleaned up {deleted_count} expired articles")
    return deleted_count


if __name__ == '__main__':
    """
    CLI for testing voice scraper
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 voice_scraper.py init                  # Create tables")
        print("  python3 voice_scraper.py test <text>           # Test keyword extraction")
        print("  python3 voice_scraper.py scrape <recording_id> # Scrape for recording")
        print("  python3 voice_scraper.py cleanup               # Clean expired cache")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        create_scraper_tables()
        print("✅ Scraper tables initialized")

    elif command == "test":
        if len(sys.argv) < 3:
            print("Error: Provide text to extract keywords from")
            sys.exit(1)

        text = ' '.join(sys.argv[2:])
        keywords = extract_keywords(text)
        print(f"Keywords: {keywords}")

        # Test scraping
        if keywords:
            print(f"\nTesting scrape for: {keywords[0]}")
            articles = scrape_google_news(keywords[0], max_results=3)
            for i, article in enumerate(articles, 1):
                print(f"\n{i}. {article['title']}")
                print(f"   Source: {article['source']}")
                print(f"   URL: {article['url']}")

    elif command == "scrape":
        if len(sys.argv) < 3:
            print("Error: Provide recording ID")
            sys.exit(1)

        recording_id = int(sys.argv[2])
        result = scrape_for_recording(recording_id)
        print(f"\nKeywords: {result.get('keywords', [])}")
        print(f"Articles found: {result.get('articles_found', 0)}")
        print(f"New: {result.get('articles_new', 0)}, Cached: {result.get('articles_cached', 0)}")

    elif command == "cleanup":
        deleted = cleanup_expired_cache()
        print(f"✅ Removed {deleted} expired articles")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

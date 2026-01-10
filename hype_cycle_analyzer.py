#!/usr/bin/env python3
"""
Hype Cycle Analyzer - Track Topics Over Time

Analyze news articles, blog posts, and content across time periods to identify:
- What topics are heating up (early hype)
- What's at peak hype (mainstream coverage)
- What's fading (trough of disillusionment)
- What's coming back (plateau of productivity)

Like Gartner Hype Cycle, but data-driven from actual content.

How it works:
1. Hash articles by topic/keywords
2. Cluster similar articles together
3. Track cluster volume over time
4. Identify hype cycle phases

Example:
    "AI" topic:
    - 2020: 10 articles/month (early hype)
    - 2022: 500 articles/month (peak hype)
    - 2023: 100 articles/month (trough)
    - 2024: 200 articles/month (plateau - real usage)
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_db
from collections import defaultdict
import math

# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_hype_cycle_tables():
    """Initialize hype cycle analysis tables"""
    conn = get_db()

    # Content items (articles, posts, etc.)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS content_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            content_text TEXT,
            source TEXT,
            author TEXT,
            published_date DATE NOT NULL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            keywords TEXT,
            category TEXT
        )
    ''')

    # Topic clusters (groups of similar content)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS topic_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_hash TEXT UNIQUE NOT NULL,
            topic_name TEXT NOT NULL,
            keywords TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')

    # Content-to-cluster mapping
    conn.execute('''
        CREATE TABLE IF NOT EXISTS content_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            cluster_id INTEGER NOT NULL,
            similarity_score REAL DEFAULT 1.0,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content_items(id),
            FOREIGN KEY (cluster_id) REFERENCES topic_clusters(id),
            UNIQUE(content_id, cluster_id)
        )
    ''')

    # Hype cycle measurements (volume over time)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS hype_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id INTEGER NOT NULL,
            measurement_date DATE NOT NULL,
            article_count INTEGER DEFAULT 0,
            total_mentions INTEGER DEFAULT 0,
            sentiment_score REAL DEFAULT 0.0,
            hype_phase TEXT,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cluster_id) REFERENCES topic_clusters(id),
            UNIQUE(cluster_id, measurement_date)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# CONTENT INGESTION
# ==============================================================================

def ingest_article(
    title: str,
    content: str,
    url: str = None,
    source: str = 'manual',
    author: str = None,
    published_date: datetime = None,
    keywords: List[str] = None
) -> Dict:
    """
    Ingest article for hype cycle analysis

    Args:
        title: Article title
        content: Full article text
        url: Article URL
        source: Source name (e.g., 'techcrunch', 'hackernews')
        author: Author name
        published_date: When article was published
        keywords: List of keywords

    Returns:
        {
            'content_id': int,
            'content_hash': str,
            'clusters_assigned': List[int]
        }
    """

    conn = get_db()

    # Generate content hash
    content_hash = hashlib.sha256(f"{title}{content}".encode()).hexdigest()[:16]

    # Check if already exists
    existing = conn.execute(
        'SELECT id FROM content_items WHERE content_hash = ?',
        (content_hash,)
    ).fetchone()

    if existing:
        conn.close()
        return {
            'content_id': existing['id'],
            'content_hash': content_hash,
            'status': 'already_exists'
        }

    # Insert content
    published_date = published_date or datetime.utcnow()
    keywords_json = json.dumps(keywords) if keywords else None

    cursor = conn.execute('''
        INSERT INTO content_items (
            content_hash, title, url, content_text, source,
            author, published_date, keywords
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        content_hash, title, url, content, source,
        author, published_date.date(), keywords_json
    ))

    content_id = cursor.lastrowid

    # Auto-assign to clusters
    clusters_assigned = _assign_to_clusters(content_id, title, content, keywords or [])

    conn.commit()
    conn.close()

    return {
        'content_id': content_id,
        'content_hash': content_hash,
        'clusters_assigned': clusters_assigned
    }


def _assign_to_clusters(
    content_id: int,
    title: str,
    content: str,
    keywords: List[str]
) -> List[int]:
    """
    Automatically assign content to topic clusters

    Uses simple keyword matching (can be upgraded to embeddings later)

    Args:
        content_id: Content ID
        title: Article title
        content: Article content
        keywords: Extracted keywords

    Returns:
        List of cluster IDs assigned
    """

    conn = get_db()

    # Get all clusters
    clusters = conn.execute('SELECT * FROM topic_clusters').fetchall()

    assigned_clusters = []

    for cluster in clusters:
        cluster_keywords = json.loads(cluster['keywords'])

        # Simple keyword matching
        title_lower = title.lower()
        content_lower = content.lower()

        matches = 0
        for keyword in cluster_keywords:
            if keyword.lower() in title_lower:
                matches += 3  # Title match worth more
            if keyword.lower() in content_lower:
                matches += 1

        # Assign if sufficient overlap
        if matches > 0:
            similarity = min(matches / 10.0, 1.0)  # Cap at 1.0

            conn.execute('''
                INSERT OR IGNORE INTO content_clusters (
                    content_id, cluster_id, similarity_score
                ) VALUES (?, ?, ?)
            ''', (content_id, cluster['id'], similarity))

            assigned_clusters.append(cluster['id'])

    conn.commit()
    conn.close()

    return assigned_clusters


# ==============================================================================
# CLUSTER MANAGEMENT
# ==============================================================================

def create_topic_cluster(
    topic_name: str,
    keywords: List[str],
    description: str = None
) -> Dict:
    """
    Create topic cluster for tracking

    Args:
        topic_name: Topic name (e.g., "AI", "Bitcoin", "Climate Change")
        keywords: Keywords to match (e.g., ["artificial intelligence", "machine learning", "AI"])
        description: Optional description

    Returns:
        {'cluster_id': int, 'cluster_hash': str}
    """

    conn = get_db()

    # Generate cluster hash
    cluster_hash = hashlib.sha256(f"{topic_name}{''.join(keywords)}".encode()).hexdigest()[:16]

    # Check if exists
    existing = conn.execute(
        'SELECT id FROM topic_clusters WHERE cluster_hash = ?',
        (cluster_hash,)
    ).fetchone()

    if existing:
        conn.close()
        return {
            'cluster_id': existing['id'],
            'cluster_hash': cluster_hash,
            'status': 'already_exists'
        }

    # Create cluster
    cursor = conn.execute('''
        INSERT INTO topic_clusters (
            cluster_hash, topic_name, keywords, description
        ) VALUES (?, ?, ?, ?)
    ''', (cluster_hash, topic_name, json.dumps(keywords), description))

    cluster_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        'cluster_id': cluster_id,
        'cluster_hash': cluster_hash,
        'status': 'created'
    }


def get_all_clusters() -> List[Dict]:
    """Get all topic clusters"""

    conn = get_db()

    clusters = conn.execute('''
        SELECT
            tc.*,
            COUNT(cc.content_id) as total_articles
        FROM topic_clusters tc
        LEFT JOIN content_clusters cc ON tc.id = cc.cluster_id
        GROUP BY tc.id
        ORDER BY total_articles DESC
    ''').fetchall()

    conn.close()

    return [dict(c) for c in clusters]


# ==============================================================================
# HYPE CYCLE CALCULATION
# ==============================================================================

def calculate_hype_cycle(cluster_id: int, days_back: int = 365) -> Dict:
    """
    Calculate hype cycle for a topic cluster

    Analyzes article volume over time to identify hype phases:
    - Innovation Trigger: First mentions appear
    - Peak of Inflated Expectations: Maximum article volume
    - Trough of Disillusionment: Volume drops significantly
    - Slope of Enlightenment: Gradual increase
    - Plateau of Productivity: Steady state

    Args:
        cluster_id: Topic cluster ID
        days_back: How far back to analyze (default 1 year)

    Returns:
        {
            'topic_name': str,
            'current_phase': str,
            'peak_date': str,
            'peak_volume': int,
            'current_volume': int,
            'trend': 'rising' | 'falling' | 'stable',
            'timeline': List[Dict] (daily measurements)
        }
    """

    conn = get_db()

    # Get cluster info
    cluster = conn.execute(
        'SELECT * FROM topic_clusters WHERE id = ?',
        (cluster_id,)
    ).fetchone()

    if not cluster:
        conn.close()
        return {'error': 'Cluster not found'}

    # Get articles in this cluster over time
    cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).date()

    articles_by_date = conn.execute('''
        SELECT
            ci.published_date as date,
            COUNT(*) as count
        FROM content_items ci
        JOIN content_clusters cc ON ci.id = cc.content_id
        WHERE cc.cluster_id = ?
            AND ci.published_date >= ?
        GROUP BY ci.published_date
        ORDER BY ci.published_date ASC
    ''', (cluster_id, cutoff_date)).fetchall()

    conn.close()

    # Build timeline
    timeline = []
    volume_by_date = {}

    for row in articles_by_date:
        date_str = row['date']
        count = row['count']
        volume_by_date[date_str] = count
        timeline.append({'date': date_str, 'volume': count})

    if not timeline:
        return {
            'topic_name': cluster['topic_name'],
            'current_phase': 'innovation_trigger',
            'error': 'No data yet'
        }

    # Find peak
    peak_volume = max(volume_by_date.values())
    peak_date = [d for d, v in volume_by_date.items() if v == peak_volume][0]

    # Get current volume (last 30 days average)
    recent_volumes = [v for d, v in volume_by_date.items() if d >= (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')]
    current_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0

    # Determine phase
    phase = _determine_hype_phase(timeline, peak_volume, current_volume)

    # Determine trend (last 7 days vs previous 7 days)
    last_7 = [v for d, v in volume_by_date.items() if d >= (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')]
    prev_7 = [v for d, v in volume_by_date.items() if (datetime.utcnow() - timedelta(days=14)).strftime('%Y-%m-%d') <= d < (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')]

    avg_last = sum(last_7) / len(last_7) if last_7 else 0
    avg_prev = sum(prev_7) / len(prev_7) if prev_7 else 0

    if avg_last > avg_prev * 1.2:
        trend = 'rising'
    elif avg_last < avg_prev * 0.8:
        trend = 'falling'
    else:
        trend = 'stable'

    return {
        'topic_name': cluster['topic_name'],
        'current_phase': phase,
        'peak_date': peak_date,
        'peak_volume': peak_volume,
        'current_volume': round(current_volume, 2),
        'trend': trend,
        'timeline': timeline,
        'keywords': json.loads(cluster['keywords'])
    }


def _determine_hype_phase(timeline: List[Dict], peak_volume: int, current_volume: float) -> str:
    """
    Determine which hype cycle phase we're in

    Phases:
    1. Innovation Trigger: Early growth (0-20% of peak)
    2. Peak of Inflated Expectations: At or near peak (80-100% of peak)
    3. Trough of Disillusionment: Sharp drop (20-40% of peak)
    4. Slope of Enlightenment: Recovery (40-60% of peak)
    5. Plateau of Productivity: Stable (60-80% of peak, stable trend)

    Args:
        timeline: List of {date, volume}
        peak_volume: Maximum volume
        current_volume: Current average volume

    Returns:
        Phase name
    """

    if not timeline or peak_volume == 0:
        return 'innovation_trigger'

    # Calculate percentage of peak
    pct_of_peak = (current_volume / peak_volume) * 100

    # Check if we're at peak (recent)
    peak_dates = [t['date'] for t in timeline if t['volume'] == peak_volume]
    most_recent_peak = max(peak_dates) if peak_dates else None

    if most_recent_peak:
        days_since_peak = (datetime.utcnow().date() - datetime.fromisoformat(most_recent_peak).date()).days
    else:
        days_since_peak = 999

    # Determine phase
    if pct_of_peak >= 80:
        return 'peak_inflated_expectations'
    elif pct_of_peak < 20:
        return 'innovation_trigger'
    elif 20 <= pct_of_peak < 40 and days_since_peak < 90:
        return 'trough_disillusionment'
    elif 40 <= pct_of_peak < 60:
        return 'slope_enlightenment'
    elif 60 <= pct_of_peak < 80:
        return 'plateau_productivity'
    else:
        return 'unknown'


# ==============================================================================
# MULTI-PERSPECTIVE ANALYSIS
# ==============================================================================

def generate_multi_perspective_analysis(cluster_id: int) -> Dict:
    """
    Generate multiple perspectives on a topic (the "roast" and "opposite" system)

    For a given topic, generate:
    - Critical perspective (roast)
    - Supportive perspective (hype)
    - Neutral perspective (facts)
    - Opposite perspective (contrarian)

    Args:
        cluster_id: Topic cluster ID

    Returns:
        {
            'topic': str,
            'perspectives': {
                'critical': str,
                'supportive': str,
                'neutral': str,
                'opposite': str
            }
        }
    """

    conn = get_db()

    # Get cluster
    cluster = conn.execute(
        'SELECT * FROM topic_clusters WHERE id = ?',
        (cluster_id,)
    ).fetchone()

    if not cluster:
        conn.close()
        return {'error': 'Cluster not found'}

    # Get sample articles
    articles = conn.execute('''
        SELECT ci.*
        FROM content_items ci
        JOIN content_clusters cc ON ci.id = cc.content_id
        WHERE cc.cluster_id = ?
        ORDER BY ci.published_date DESC
        LIMIT 10
    ''', (cluster_id,)).fetchall()

    conn.close()

    if not articles:
        return {
            'topic': cluster['topic_name'],
            'error': 'No articles to analyze'
        }

    # Use local Ollama to generate perspectives
    from local_ollama_client import analyze_news_article

    perspectives = {}

    # Sample article for analysis
    sample_article = articles[0]

    # Generate each perspective
    for perspective_type in ['critical', 'supportive', 'neutral', 'opposite']:
        result = analyze_news_article(
            article_url=sample_article['url'] or 'N/A',
            article_text=sample_article['content_text'] or sample_article['title'],
            perspective=perspective_type,
            model='mistral:7b'
        )

        perspectives[perspective_type] = result.get('analysis', 'Error generating perspective')

    return {
        'topic': cluster['topic_name'],
        'perspectives': perspectives,
        'sample_article': {
            'title': sample_article['title'],
            'url': sample_article['url'],
            'date': sample_article['published_date']
        }
    }


# ==============================================================================
# SEED DATA (Example Topics)
# ==============================================================================

def seed_example_topics():
    """Seed database with example topics to track"""

    topics = [
        {
            'name': 'Artificial Intelligence',
            'keywords': ['AI', 'artificial intelligence', 'machine learning', 'deep learning', 'neural networks', 'LLM'],
            'description': 'AI and machine learning technologies'
        },
        {
            'name': 'Cryptocurrency',
            'keywords': ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'DeFi', 'NFT'],
            'description': 'Cryptocurrency and blockchain'
        },
        {
            'name': 'Climate Change',
            'keywords': ['climate change', 'global warming', 'carbon emissions', 'renewable energy', 'sustainability'],
            'description': 'Climate and environmental topics'
        },
        {
            'name': 'Web3',
            'keywords': ['web3', 'decentralized', 'DAO', 'smart contracts', 'IPFS'],
            'description': 'Decentralized web technologies'
        },
        {
            'name': 'Remote Work',
            'keywords': ['remote work', 'work from home', 'distributed teams', 'async', 'hybrid work'],
            'description': 'Future of work and remote collaboration'
        }
    ]

    created = []
    for topic in topics:
        result = create_topic_cluster(
            topic_name=topic['name'],
            keywords=topic['keywords'],
            description=topic['description']
        )
        created.append(result)

    return created


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing hype cycle analyzer tables...")
    init_hype_cycle_tables()
    print("✅ Tables initialized")
    print()

    print("Seeding example topics...")
    topics = seed_example_topics()
    print(f"✅ Created {len(topics)} topic clusters")
    print()

    print("Hype Cycle Analyzer - Track Topics Over Time")
    print()
    print("Features:")
    print("  - Ingest articles from any source")
    print("  - Auto-cluster by topic")
    print("  - Calculate hype cycle phase")
    print("  - Multi-perspective analysis (critical, supportive, neutral, opposite)")
    print("  - Track trends over time")
    print()
    print("Example topics tracked:")
    for topic in topics:
        print(f"  - {topic.get('status', 'created')}: Topic cluster {topic.get('cluster_id')}")

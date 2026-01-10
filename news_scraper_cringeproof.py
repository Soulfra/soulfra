#!/usr/bin/env python3
"""
CringeProof News Scraper - Pair voice memos with news articles

Scrapes Google News + custom feeds → Pairs with voice reactions → Creates shows

Flow:
1. Scrape news from Google News RSS
2. User records voice memo reacting to article
3. System pairs memo with article metadata
4. Publishes to voice archive + creates live show
5. Tracks which articles "age well" vs "age poorly" (CringeProof score)

Usage:
    # Scrape news
    python3 news_scraper_cringeproof.py scrape --topics ai,tech,politics

    # Pair voice memo with article
    python3 news_scraper_cringeproof.py pair --recording-id 5 --article-id 123

    # Calculate CringeProof scores (after time passes)
    python3 news_scraper_cringeproof.py score --article-id 123
"""

import feedparser
import requests
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from urllib.parse import quote_plus
from database import get_db


class CringeProofNewsScraper:
    """Scrape news and pair with voice memos for CringeProof game"""

    def __init__(self):
        self.db = get_db()
        self._ensure_tables()

    def _ensure_tables(self):
        """Create tables for news articles and pairings"""
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT,
                published_date TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,
                full_text TEXT,
                topics TEXT,  -- JSON array of topics
                article_hash TEXT,  -- SHA-256 of content for deduplication
                cringe_score REAL DEFAULT 0.0,  -- How badly this aged
                relevance_score REAL DEFAULT 0.0  -- How relevant it remained
            )
        ''')

        self.db.execute('''
            CREATE TABLE IF NOT EXISTS voice_article_pairings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER REFERENCES simple_voice_recordings(id),
                article_id INTEGER REFERENCES news_articles(id),
                paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_prediction TEXT,  -- What user said would happen
                time_lock_until TIMESTAMP,  -- Don't publish until this date
                published_to_archive BOOLEAN DEFAULT 0,
                live_show_id INTEGER,  -- If created as call-in show
                cringe_factor REAL DEFAULT 0.0,  -- How wrong was the prediction
                UNIQUE(recording_id, article_id)
            )
        ''')

        self.db.commit()

    def scrape_google_news(self, topics: List[str], max_per_topic: int = 10) -> List[Dict]:
        """
        Scrape Google News RSS for given topics

        Args:
            topics: List of topics (e.g. ['ai', 'tech', 'politics'])
            max_per_topic: Max articles per topic

        Returns:
            List of scraped articles
        """
        articles = []

        for topic in topics:
            # Google News RSS URL
            rss_url = f"https://news.google.com/rss/search?q={quote_plus(topic)}&hl=en-US&gl=US&ceid=US:en"

            try:
                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:max_per_topic]:
                    # Extract article data
                    article_data = {
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'source': entry.get('source', {}).get('title', 'Google News'),
                        'published_date': self._parse_date(entry.get('published')),
                        'summary': entry.get('summary', ''),
                        'topics': topic
                    }

                    # Generate content hash
                    content = f"{article_data['title']}{article_data['url']}"
                    article_data['article_hash'] = hashlib.sha256(content.encode()).hexdigest()[:16]

                    # Check if already exists
                    existing = self.db.execute(
                        'SELECT id FROM news_articles WHERE article_hash = ?',
                        (article_data['article_hash'],)
                    ).fetchone()

                    if existing:
                        continue  # Skip duplicates

                    # Insert article
                    cursor = self.db.execute('''
                        INSERT INTO news_articles
                        (title, url, source, published_date, summary, topics, article_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article_data['title'],
                        article_data['url'],
                        article_data['source'],
                        article_data['published_date'],
                        article_data['summary'],
                        topic,
                        article_data['article_hash']
                    ))

                    article_data['id'] = cursor.lastrowid
                    articles.append(article_data)

                self.db.commit()
                print(f"✅ Scraped {len(feed.entries[:max_per_topic])} articles for topic: {topic}")

            except Exception as e:
                print(f"❌ Failed to scrape topic '{topic}': {e}")

        return articles

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse RSS date to ISO format"""
        if not date_str:
            return None

        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return None

    def pair_voice_with_article(
        self,
        recording_id: int,
        article_id: int,
        user_prediction: Optional[str] = None,
        time_lock_days: Optional[int] = None
    ) -> Dict:
        """
        Pair voice memo with news article

        Args:
            recording_id: Voice recording ID
            article_id: News article ID
            user_prediction: What user predicted would happen
            time_lock_days: Don't publish until X days pass

        Returns:
            Pairing info dict
        """
        # Get article
        article = self.db.execute(
            'SELECT * FROM news_articles WHERE id = ?',
            (article_id,)
        ).fetchone()

        if not article:
            return {'success': False, 'error': 'Article not found'}

        # Get recording
        recording = self.db.execute(
            'SELECT * FROM simple_voice_recordings WHERE id = ?',
            (recording_id,)
        ).fetchone()

        if not recording:
            return {'success': False, 'error': 'Recording not found'}

        # Calculate time lock
        time_lock_until = None
        if time_lock_days:
            time_lock_until = (datetime.now() + timedelta(days=time_lock_days)).isoformat()

        # Create pairing
        try:
            cursor = self.db.execute('''
                INSERT INTO voice_article_pairings
                (recording_id, article_id, user_prediction, time_lock_until)
                VALUES (?, ?, ?, ?)
            ''', (recording_id, article_id, user_prediction, time_lock_until))

            self.db.commit()

            return {
                'success': True,
                'pairing_id': cursor.lastrowid,
                'article_title': article['title'],
                'recording_id': recording_id,
                'time_lock_until': time_lock_until
            }

        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Pairing already exists'}

    def create_cringeproof_show(self, article_id: int, auto_pair_voices: bool = True) -> Dict:
        """
        Create live call-in show from article

        Args:
            article_id: Article to discuss
            auto_pair_voices: Auto-pair existing voice memos with article

        Returns:
            Show info dict
        """
        from live_call_in_show import LiveCallInShow

        # Get article
        article = self.db.execute(
            'SELECT * FROM news_articles WHERE id = ?',
            (article_id,)
        ).fetchone()

        if not article:
            return {'success': False, 'error': 'Article not found'}

        # Create show
        show_system = LiveCallInShow()
        show = show_system.create_show(
            title=f"CringeProof: {article['title'][:60]}...",
            article_text=article['summary'] or article['title'],
            article_url=article['url'],
            article_source=article['source']
        )

        # Update pairing with show ID if voices already paired
        if auto_pair_voices:
            self.db.execute('''
                UPDATE voice_article_pairings
                SET live_show_id = ?
                WHERE article_id = ? AND live_show_id IS NULL
            ''', (show['show_id'], article_id))
            self.db.commit()

        return {
            'success': True,
            'show_id': show['show_id'],
            'article_title': article['title'],
            'call_in_url': show['call_in_url']
        }

    def calculate_cringe_score(self, article_id: int, days_passed: int = 30) -> Dict:
        """
        Calculate how badly article/predictions aged

        CringeProof Score = How wrong were predictions + How irrelevant is topic now

        Args:
            article_id: Article to score
            days_passed: Minimum days since article published

        Returns:
            Scoring results
        """
        # Get article
        article = self.db.execute(
            'SELECT * FROM news_articles WHERE id = ?',
            (article_id,)
        ).fetchone()

        if not article:
            return {'success': False, 'error': 'Article not found'}

        # Check if enough time passed
        published = datetime.fromisoformat(article['published_date'])
        age_days = (datetime.now() - published).days

        if age_days < days_passed:
            return {
                'success': False,
                'error': f'Not enough time passed (need {days_passed} days, only {age_days})'
            }

        # TODO: Use Ollama to analyze:
        # 1. Was the article's premise wrong?
        # 2. Did predictions come true?
        # 3. Is topic still relevant?

        # For now, simple scoring based on voice pairing activity
        pairings = self.db.execute(
            'SELECT COUNT(*) as count FROM voice_article_pairings WHERE article_id = ?',
            (article_id,)
        ).fetchone()

        # Low engagement after 30 days = high cringe (topic died)
        relevance_score = min(100, pairings['count'] * 10)
        cringe_score = 100 - relevance_score

        # Update article
        self.db.execute('''
            UPDATE news_articles
            SET cringe_score = ?, relevance_score = ?
            WHERE id = ?
        ''', (cringe_score, relevance_score, article_id))

        self.db.commit()

        return {
            'success': True,
            'article_id': article_id,
            'age_days': age_days,
            'cringe_score': cringe_score,
            'relevance_score': relevance_score,
            'voice_reactions': pairings['count']
        }

    def get_unlocked_pairings(self) -> List[Dict]:
        """Get voice-article pairings ready to publish (time lock expired)"""
        now = datetime.now().isoformat()

        pairings = self.db.execute('''
            SELECT
                vap.*,
                na.title as article_title,
                na.url as article_url,
                svr.transcription
            FROM voice_article_pairings vap
            JOIN news_articles na ON vap.article_id = na.id
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE vap.published_to_archive = 0
              AND (vap.time_lock_until IS NULL OR vap.time_lock_until <= ?)
        ''', (now,)).fetchall()

        return [dict(p) for p in pairings]

    def publish_pairing_to_archive(self, pairing_id: int) -> Dict:
        """
        Publish voice-article pairing to GitHub Pages archive

        Args:
            pairing_id: Pairing to publish

        Returns:
            Publication result
        """
        # Get pairing
        pairing = self.db.execute('''
            SELECT
                vap.*,
                na.title as article_title,
                na.url as article_url,
                na.published_date as article_date,
                svr.transcription,
                svr.created_at as recording_date
            FROM voice_article_pairings vap
            JOIN news_articles na ON vap.article_id = na.id
            JOIN simple_voice_recordings svr ON vap.recording_id = svr.id
            WHERE vap.id = ?
        ''', (pairing_id,)).fetchone()

        if not pairing:
            return {'success': False, 'error': 'Pairing not found'}

        # Use voice archive publisher to create markdown with article context
        from publish_voice_archive import scrub_pii, generate_voice_signature

        # Scrub transcript
        scrubbed = scrub_pii(pairing['transcription'])

        # Generate signature
        signature = generate_voice_signature(
            scrubbed,
            pairing['recording_date'],
            1  # user_id
        )

        # Create enhanced markdown with article context
        dt = datetime.fromisoformat(pairing['recording_date'].replace(' ', 'T'))
        date_str = dt.strftime('%B %d, %Y at %I:%M %p UTC')

        markdown = f"""---
title: Voice Memo - CringeProof Reaction
date: {dt.isoformat()}
signature: {signature}
recording_id: {pairing['recording_id']}
article_id: {pairing['article_id']}
---

# Voice Memo - {date_str}

**Recording ID**: `{pairing['recording_id']}`
**Signature**: `{signature}`

---

## Original Article

**Title**: {pairing['article_title']}
**Source**: {pairing['article_url']}
**Published**: {pairing['article_date']}

---

## Voice Reaction

{scrubbed}

---

## User Prediction

{pairing['user_prediction'] or '*No prediction recorded*'}

---

## CringeProof Challenge

This is a time-locked reaction. The voice memo was recorded on {date_str}, reacting to the article above.

**The Question**: Will this prediction age well or age poorly?

Check back later to see the CringeProof Score!

---

## Verification

**Signature**: `{signature}`

This transcript is cryptographically signed to prove authenticity.

---

*Published to the Soulfra Voice Archive - A permanent record of voice memos paired with news articles.*
"""

        # Write to archive repo
        repo_dir = Path.home() / 'soulfra-voice-archive'
        posts_dir = repo_dir / 'transcripts'
        posts_dir.mkdir(exist_ok=True)

        filename = f"{dt.strftime('%Y-%m-%d-%H-%M')}-cringeproof-{pairing['recording_id']}.md"
        file_path = posts_dir / filename

        with open(file_path, 'w') as f:
            f.write(markdown)

        # Mark as published
        self.db.execute('''
            UPDATE voice_article_pairings
            SET published_to_archive = 1
            WHERE id = ?
        ''', (pairing_id,))

        self.db.commit()

        return {
            'success': True,
            'filename': filename,
            'article_title': pairing['article_title']
        }


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='CringeProof News Scraper')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scrape news
    scrape_parser = subparsers.add_parser('scrape', help='Scrape news articles')
    scrape_parser.add_argument('--topics', required=True, help='Comma-separated topics')
    scrape_parser.add_argument('--max-per-topic', type=int, default=10)

    # Pair voice with article
    pair_parser = subparsers.add_parser('pair', help='Pair voice memo with article')
    pair_parser.add_argument('--recording-id', type=int, required=True)
    pair_parser.add_argument('--article-id', type=int, required=True)
    pair_parser.add_argument('--prediction', help='User prediction about article')
    pair_parser.add_argument('--time-lock-days', type=int, help='Days to time-lock')

    # Create show
    show_parser = subparsers.add_parser('create-show', help='Create CringeProof show from article')
    show_parser.add_argument('article_id', type=int, help='Article ID')

    # Calculate cringe score
    score_parser = subparsers.add_parser('score', help='Calculate CringeProof score')
    score_parser.add_argument('article_id', type=int, help='Article ID')
    score_parser.add_argument('--min-days', type=int, default=30)

    # Publish unlocked pairings
    publish_parser = subparsers.add_parser('publish-unlocked', help='Publish time-unlocked pairings')

    args = parser.parse_args()

    scraper = CringeProofNewsScraper()

    if args.command == 'scrape':
        topics = [t.strip() for t in args.topics.split(',')]
        articles = scraper.scrape_google_news(topics, args.max_per_topic)
        print(f"\n✅ Scraped {len(articles)} total articles")
        for article in articles[:5]:
            print(f"   - {article['title'][:60]}...")

    elif args.command == 'pair':
        result = scraper.pair_voice_with_article(
            args.recording_id,
            args.article_id,
            user_prediction=args.prediction,
            time_lock_days=args.time_lock_days
        )
        if result['success']:
            print(f"\n✅ Paired voice memo #{args.recording_id} with article")
            print(f"   Article: {result['article_title']}")
            if result.get('time_lock_until'):
                print(f"   Time-locked until: {result['time_lock_until']}")
        else:
            print(f"\n❌ Error: {result['error']}")

    elif args.command == 'create-show':
        result = scraper.create_cringeproof_show(args.article_id)
        if result['success']:
            print(f"\n✅ Created CringeProof show #{result['show_id']}")
            print(f"   Article: {result['article_title']}")
            print(f"   Call-in URL: {result['call_in_url']}")
        else:
            print(f"\n❌ Error: {result['error']}")

    elif args.command == 'score':
        result = scraper.calculate_cringe_score(args.article_id, args.min_days)
        if result['success']:
            print(f"\n📊 CringeProof Score for Article #{args.article_id}")
            print(f"   Age: {result['age_days']} days")
            print(f"   Cringe Score: {result['cringe_score']:.1f}/100")
            print(f"   Relevance Score: {result['relevance_score']:.1f}/100")
            print(f"   Voice Reactions: {result['voice_reactions']}")
        else:
            print(f"\n❌ Error: {result['error']}")

    elif args.command == 'publish-unlocked':
        pairings = scraper.get_unlocked_pairings()
        print(f"\n📦 Publishing {len(pairings)} unlocked pairings...")

        for pairing in pairings:
            result = scraper.publish_pairing_to_archive(pairing['id'])
            if result['success']:
                print(f"   ✅ {result['filename']}")

        print(f"\n🎉 Published {len(pairings)} voice-article pairings!")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

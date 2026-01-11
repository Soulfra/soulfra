#!/usr/bin/env python3
"""
GoDaddy Lander Keyword Scraper

Scrapes GoDaddy parked domain pages to extract:
- Keywords (from meta tags, ad placements)
- Traffic hints (what searches bring people here)
- Competitor keywords (what others are bidding on)
- Content suggestions (what GoDaddy recommends)

This intel is used to auto-generate content for your domains.

Usage:
    python3 scrape_godaddy_landers.py
    python3 scrape_godaddy_landers.py --domain howtocookathome.com
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
from datetime import datetime
import argparse
import re
from urllib.parse import urlparse
import urllib3

# Suppress SSL warnings for POC
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = 'soulfra.db'


class GoDaddyLanderScraper:
    """Scrape GoDaddy parked pages for SEO intel"""

    def __init__(self, db_path=DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def init_tables(self):
        """Create tables for SEO intelligence"""
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS domain_seo_intel (
                domain TEXT PRIMARY KEY,
                keywords TEXT,  -- JSON array of keywords
                traffic_hints TEXT,  -- Inferred search terms
                competitor_keywords TEXT,  -- JSON array
                godaddy_categories TEXT,  -- Categories from GoDaddy
                estimated_traffic TEXT,  -- Traffic estimates if available
                ad_keywords TEXT,  -- Keywords from ad placements
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS extracted_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                keyword TEXT NOT NULL,
                source TEXT,  -- 'meta', 'ad', 'link', 'godaddy'
                relevance_score REAL,  -- 0.0 to 1.0
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (domain) REFERENCES domain_seo_intel(domain)
            );

            CREATE TABLE IF NOT EXISTS content_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                idea_title TEXT NOT NULL,
                idea_description TEXT,
                keywords_used TEXT,  -- JSON array
                target_audience TEXT,
                estimated_difficulty TEXT,  -- 'easy', 'medium', 'hard'
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_to_ai BOOLEAN DEFAULT 0,
                FOREIGN KEY (domain) REFERENCES domain_seo_intel(domain)
            );

            CREATE INDEX IF NOT EXISTS idx_keywords_domain ON extracted_keywords(domain);
            CREATE INDEX IF NOT EXISTS idx_ideas_domain ON content_ideas(domain);
        ''')
        self.db.commit()
        print("✅ SEO intelligence tables initialized")

    def scrape_domain(self, domain):
        """Scrape a domain (works for both GoDaddy landers and live sites)"""
        print(f"\n{'='*80}")
        print(f"🔍 Scraping SEO Intel: {domain}")
        print(f"{'='*80}\n")

        try:
            url = f"https://{domain}"
            response = self.session.get(url, timeout=10, allow_redirects=True, verify=False)

            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")

            if response.status_code != 200:
                print(f"⚠️  HTTP {response.status_code} - Skipping")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract keywords from various sources
            keywords = self.extract_keywords(soup, domain)
            traffic_hints = self.infer_traffic_hints(soup, domain)
            competitor_keywords = self.extract_competitor_keywords(soup)
            godaddy_categories = self.extract_godaddy_categories(soup)
            ad_keywords = self.extract_ad_keywords(soup)

            # Store in database
            self.db.execute('''
                INSERT OR REPLACE INTO domain_seo_intel
                (domain, keywords, traffic_hints, competitor_keywords,
                 godaddy_categories, ad_keywords, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                domain,
                json.dumps(keywords),
                json.dumps(traffic_hints),
                json.dumps(competitor_keywords),
                json.dumps(godaddy_categories),
                json.dumps(ad_keywords)
            ))

            # Store individual keywords
            for kw in keywords:
                self.db.execute('''
                    INSERT INTO extracted_keywords
                    (domain, keyword, source, relevance_score)
                    VALUES (?, ?, ?, ?)
                ''', (domain, kw['keyword'], kw['source'], kw.get('score', 0.5)))

            self.db.commit()

            # Generate content ideas
            ideas = self.generate_content_ideas(domain, keywords, traffic_hints)
            for idea in ideas:
                self.db.execute('''
                    INSERT INTO content_ideas
                    (domain, idea_title, idea_description, keywords_used, target_audience, estimated_difficulty)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    domain,
                    idea['title'],
                    idea['description'],
                    json.dumps(idea['keywords']),
                    idea['audience'],
                    idea['difficulty']
                ))
            self.db.commit()

            print(f"\n✅ Extracted {len(keywords)} keywords")
            print(f"✅ Found {len(traffic_hints)} traffic hints")
            print(f"✅ Generated {len(ideas)} content ideas")

            return {
                'domain': domain,
                'keywords': keywords,
                'traffic_hints': traffic_hints,
                'content_ideas': ideas
            }

        except requests.RequestException as e:
            print(f"❌ Error scraping {domain}: {e}")
            return None

    def extract_keywords(self, soup, domain):
        """Extract keywords from meta tags, content, and structure"""
        keywords = []

        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            for kw in meta_keywords['content'].split(','):
                keywords.append({
                    'keyword': kw.strip(),
                    'source': 'meta',
                    'score': 0.8
                })

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            # Extract noun phrases from description
            desc_keywords = self.extract_noun_phrases(meta_desc['content'])
            for kw in desc_keywords:
                keywords.append({
                    'keyword': kw,
                    'source': 'meta_desc',
                    'score': 0.7
                })

        # Title tag
        title = soup.find('title')
        if title:
            title_keywords = self.extract_noun_phrases(title.string or '')
            for kw in title_keywords:
                keywords.append({
                    'keyword': kw,
                    'source': 'title',
                    'score': 0.9
                })

        # H1/H2 headings
        for heading in soup.find_all(['h1', 'h2']):
            heading_keywords = self.extract_noun_phrases(heading.get_text())
            for kw in heading_keywords:
                keywords.append({
                    'keyword': kw,
                    'source': 'heading',
                    'score': 0.6
                })

        # Domain name itself (powerful signal!)
        domain_keywords = self.extract_keywords_from_domain(domain)
        keywords.extend(domain_keywords)

        # Deduplicate
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw['keyword'].lower()
            if kw_lower not in seen and len(kw_lower) > 2:
                seen.add(kw_lower)
                unique_keywords.append(kw)

        return unique_keywords[:50]  # Top 50

    def extract_noun_phrases(self, text):
        """Simple noun phrase extraction (naive but effective)"""
        # Remove special chars, split on spaces
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Common stopwords
        stopwords = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'was', 'were'}

        # Filter stopwords
        phrases = [w for w in words if w not in stopwords]

        # Look for 2-word phrases
        two_word = []
        for i in range(len(phrases) - 1):
            two_word.append(f"{phrases[i]} {phrases[i+1]}")

        return list(set(phrases + two_word))[:20]

    def extract_keywords_from_domain(self, domain):
        """Extract keywords from domain name itself"""
        # Remove TLD
        name = domain.split('.')[0]

        # Split camelCase or hyphens
        parts = re.findall(r'[A-Z][a-z]+|[a-z]+', name)
        if not parts:
            parts = name.replace('-', ' ').replace('_', ' ').split()

        keywords = []
        for part in parts:
            if len(part) > 2:
                keywords.append({
                    'keyword': part.lower(),
                    'source': 'domain',
                    'score': 1.0  # Domain name = highest relevance
                })

        # Also add full domain phrase
        full_phrase = ' '.join(parts).lower()
        keywords.append({
            'keyword': full_phrase,
            'source': 'domain',
            'score': 1.0
        })

        return keywords

    def infer_traffic_hints(self, soup, domain):
        """Infer what search terms might bring traffic"""
        hints = []

        # Check for GoDaddy parking page indicators
        if 'godaddy' in soup.get_text().lower() or 'parked' in soup.get_text().lower():
            # It's a parked domain - infer from domain name
            domain_hints = self.generate_search_hints_from_domain(domain)
            hints.extend(domain_hints)
        else:
            # It's a live site - infer from content
            content_hints = self.generate_search_hints_from_content(soup)
            hints.extend(content_hints)

        return list(set(hints))[:20]

    def generate_search_hints_from_domain(self, domain):
        """Generate likely search terms from domain name"""
        name = domain.split('.')[0]
        hints = []

        # Parse domain name
        if 'howto' in name.lower():
            topic = name.lower().replace('howto', '').replace('-', ' ')
            hints.extend([
                f"how to {topic}",
                f"{topic} tutorial",
                f"{topic} guide",
                f"learn {topic}"
            ])
        elif 'cook' in name.lower():
            hints.extend([
                "cooking tips",
                "easy recipes",
                "how to cook",
                "cooking for beginners",
                "meal prep ideas"
            ])

        # Generic patterns
        parts = re.findall(r'[A-Z][a-z]+|[a-z]+', name)
        if parts:
            topic = ' '.join(parts).lower()
            hints.extend([
                f"{topic}",
                f"{topic} tips",
                f"{topic} guide",
                f"best {topic}"
            ])

        return hints

    def generate_search_hints_from_content(self, soup):
        """Generate search hints from actual page content"""
        hints = []

        # Look for "how to" phrases
        text = soup.get_text()
        how_to_phrases = re.findall(r'how to [a-z ]{5,30}', text.lower())
        hints.extend(how_to_phrases[:10])

        return hints

    def extract_competitor_keywords(self, soup):
        """Extract keywords from competitor ads (if present)"""
        keywords = []

        # Look for ad-related content
        ad_elements = soup.find_all(['a'], class_=re.compile(r'ad|sponsored|parking'))
        for ad in ad_elements:
            text = ad.get_text()
            kw = self.extract_noun_phrases(text)
            keywords.extend(kw)

        return list(set(keywords))[:20]

    def extract_godaddy_categories(self, soup):
        """Extract categories if it's a GoDaddy parking page"""
        categories = []

        # Look for category links/text
        if 'godaddy' in soup.get_text().lower():
            # Parse category structure
            for link in soup.find_all('a'):
                text = link.get_text().strip()
                if text and len(text) < 50 and '/' not in text:
                    categories.append(text)

        return list(set(categories))[:10]

    def extract_ad_keywords(self, soup):
        """Extract keywords from ad placements"""
        ad_keywords = []

        # Look for ad containers
        ad_containers = soup.find_all(['div', 'span'], class_=re.compile(r'ad|advertisement'))
        for container in ad_containers:
            kw = self.extract_noun_phrases(container.get_text())
            ad_keywords.extend(kw)

        return list(set(ad_keywords))[:15]

    def generate_content_ideas(self, domain, keywords, traffic_hints):
        """Auto-generate content ideas from keywords"""
        ideas = []

        # Get top keywords
        top_keywords = sorted(keywords, key=lambda x: x.get('score', 0), reverse=True)[:10]

        # Generate ideas
        for kw_obj in top_keywords:
            kw = kw_obj['keyword']

            # Pattern-based idea generation
            ideas.append({
                'title': f"How to {kw}",
                'description': f"A beginner's guide to {kw}",
                'keywords': [kw, f"{kw} tutorial", f"{kw} guide"],
                'audience': 'beginners',
                'difficulty': 'easy'
            })

            ideas.append({
                'title': f"5 Tips for {kw}",
                'description': f"Expert tips and tricks for {kw}",
                'keywords': [kw, f"{kw} tips", f"best {kw}"],
                'audience': 'intermediate',
                'difficulty': 'medium'
            })

        # Generate from traffic hints
        for hint in traffic_hints[:5]:
            ideas.append({
                'title': hint.title(),
                'description': f"Everything you need to know about {hint}",
                'keywords': [hint],
                'audience': 'general',
                'difficulty': 'easy'
            })

        return ideas[:15]  # Top 15 ideas

    def generate_report(self):
        """Generate summary report of SEO intelligence"""
        print("\n" + "="*80)
        print("📊 SEO INTELLIGENCE REPORT")
        print("="*80 + "\n")

        # Total domains scraped
        total = self.db.execute('SELECT COUNT(*) as count FROM domain_seo_intel').fetchone()
        print(f"Total domains analyzed: {total['count']}")

        # By domain
        domains = self.db.execute('''
            SELECT domain, keywords, traffic_hints
            FROM domain_seo_intel
            ORDER BY last_updated DESC
        ''').fetchall()

        for domain_row in domains:
            domain = domain_row['domain']
            keywords = json.loads(domain_row['keywords'])
            hints = json.loads(domain_row['traffic_hints'])

            print(f"\n🌐 {domain}")
            print(f"  Keywords ({len(keywords)}):")
            for kw in keywords[:5]:
                print(f"    • {kw['keyword']} (score: {kw['score']:.2f}, source: {kw['source']})")

            print(f"  Traffic Hints ({len(hints)}):")
            for hint in hints[:5]:
                print(f"    • {hint}")

            # Content ideas
            ideas = self.db.execute('''
                SELECT idea_title, estimated_difficulty
                FROM content_ideas
                WHERE domain = ?
                ORDER BY generated_at DESC
                LIMIT 5
            ''', (domain,)).fetchall()

            if ideas:
                print(f"  Content Ideas ({len(ideas)}):")
                for idea in ideas:
                    print(f"    📝 {idea['idea_title']} ({idea['estimated_difficulty']})")

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description='Scrape GoDaddy landers for SEO intel')
    parser.add_argument('--domain', help='Scrape specific domain only')
    args = parser.parse_args()

    scraper = GoDaddyLanderScraper()
    scraper.init_tables()

    try:
        # Read domains from domains.txt
        with open('domains.txt', 'r') as f:
            domains = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '|' in line:
                    domain = line.split('|')[0].strip()
                    domains.append(domain)

        if args.domain:
            scraper.scrape_domain(args.domain)
        else:
            for domain in domains:
                scraper.scrape_domain(domain)
                print()  # Blank line between domains

        scraper.generate_report()

        print("\n✅ SEO intelligence gathering complete!")
        print(f"📁 Data stored in: {DB_PATH}")
        print(f"   Tables: domain_seo_intel, extracted_keywords, content_ideas")

    finally:
        scraper.close()


if __name__ == '__main__':
    main()

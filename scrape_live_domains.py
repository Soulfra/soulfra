#!/usr/bin/env python3
"""
Live Domain Scraper - Audit What's Actually Published

Scrapes your live GitHub Pages sites to find:
- Duplicate content (soulfra.github.io vs soulfra.github.io/soulfra/ vs soulfra.com)
- Broken links
- Mismatched titles/meta tags
- Content that should be in database but isn't

Uses BeautifulSoup to parse HTML and store structured audit data.

Usage:
    python3 scrape_live_domains.py
    python3 scrape_live_domains.py --domain soulfra.com
    python3 scrape_live_domains.py --full-crawl
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
import argparse
import time

DB_PATH = 'soulfra.db'

# Domains to scrape (from domains.txt)
DOMAINS = [
    'soulfra.github.io',
    'soulfra.com',
    'calriven.github.io',
    'calriven.com',
    'deathtodata.github.io',
    'deathtodata.com',
    'howtocookathome.com',
]


class DomainScraper:
    """Scrape live sites and audit content"""

    def __init__(self, db_path=DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def init_audit_tables(self):
        """Create tables for storing scrape results"""
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS site_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                domain TEXT NOT NULL,
                status_code INTEGER,
                title TEXT,
                h1_heading TEXT,
                meta_description TEXT,
                content_type TEXT,
                content_length INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                http_error TEXT,
                is_duplicate BOOLEAN DEFAULT 0,
                duplicate_of_url TEXT
            );

            CREATE TABLE IF NOT EXISTS scraped_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                link_text TEXT,
                is_broken BOOLEAN DEFAULT 0,
                is_external BOOLEAN DEFAULT 0,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS scraped_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                content_hash TEXT,
                full_html TEXT,
                main_content TEXT,
                json_ld TEXT,  -- JSON-LD structured data
                images TEXT,   -- JSON array of image URLs
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_audit_domain ON site_audit(domain);
            CREATE INDEX IF NOT EXISTS idx_audit_url ON site_audit(url);
            CREATE INDEX IF NOT EXISTS idx_links_source ON scraped_links(source_url);
            CREATE INDEX IF NOT EXISTS idx_content_hash ON scraped_content(content_hash);
        ''')
        self.db.commit()
        print("✅ Audit tables initialized")

    def scrape_url(self, url, domain):
        """Scrape a single URL and extract structured data"""
        if url in self.visited_urls:
            return None

        self.visited_urls.add(url)
        print(f"🔍 Scraping: {url}")

        try:
            response = self.session.get(url, timeout=10)
            status_code = response.status_code

            if status_code != 200:
                self.db.execute('''
                    INSERT OR REPLACE INTO site_audit
                    (url, domain, status_code, http_error)
                    VALUES (?, ?, ?, ?)
                ''', (url, domain, status_code, f'HTTP {status_code}'))
                self.db.commit()
                print(f"  ⚠️  HTTP {status_code}")
                return None

            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract metadata
            title = soup.find('title')
            title_text = title.string.strip() if title else None

            h1 = soup.find('h1')
            h1_text = h1.get_text(strip=True) if h1 else None

            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_desc_text = meta_desc.get('content') if meta_desc else None

            # Extract JSON-LD structured data
            json_ld = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    json_ld.append(json.loads(script.string))
                except json.JSONDecodeError:
                    pass

            # Extract main content (try to find article or main tag)
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            main_text = main_content.get_text(strip=True)[:5000] if main_content else None

            # Extract images
            images = [img.get('src') for img in soup.find_all('img') if img.get('src')]

            # Compute content hash (for duplicate detection)
            import hashlib
            content_hash = hashlib.sha256(main_text.encode() if main_text else b'').hexdigest()

            # Store in database
            self.db.execute('''
                INSERT OR REPLACE INTO site_audit
                (url, domain, status_code, title, h1_heading, meta_description,
                 content_type, content_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (url, domain, status_code, title_text, h1_text, meta_desc_text,
                  response.headers.get('Content-Type'), len(response.content)))

            self.db.execute('''
                INSERT OR REPLACE INTO scraped_content
                (url, content_hash, full_html, main_content, json_ld, images)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, content_hash, str(soup)[:50000], main_text,
                  json.dumps(json_ld), json.dumps(images)))

            # Extract and store links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                link_text = link.get_text(strip=True)

                # Make absolute URL
                abs_url = urljoin(url, href)

                # Check if external
                is_external = urlparse(abs_url).netloc != urlparse(url).netloc

                self.db.execute('''
                    INSERT INTO scraped_links
                    (source_url, target_url, link_text, is_external)
                    VALUES (?, ?, ?, ?)
                ''', (url, abs_url, link_text, is_external))

            self.db.commit()

            print(f"  ✅ Title: {title_text}")
            print(f"  📊 {len(images)} images, {len(json_ld)} JSON-LD blocks")
            print(f"  🔗 {len(soup.find_all('a', href=True))} links")

            return {
                'url': url,
                'status': status_code,
                'title': title_text,
                'h1': h1_text,
                'content_hash': content_hash,
                'links': soup.find_all('a', href=True)
            }

        except requests.RequestException as e:
            self.db.execute('''
                INSERT OR REPLACE INTO site_audit
                (url, domain, status_code, http_error)
                VALUES (?, ?, ?, ?)
            ''', (url, domain, 0, str(e)))
            self.db.commit()
            print(f"  ❌ Error: {e}")
            return None

    def scrape_domain(self, domain, full_crawl=False):
        """Scrape a domain and optionally crawl all internal links"""
        print(f"\n{'='*80}")
        print(f"🌐 Scraping Domain: {domain}")
        print(f"{'='*80}\n")

        # Try both http and https
        urls_to_try = [
            f'https://{domain}',
            f'https://{domain}/index.html',
        ]

        # Also check for nested paths (the problem you mentioned)
        if 'soulfra' in domain:
            urls_to_try.extend([
                f'https://{domain}/soulfra/',
                f'https://{domain}/soulfra/index.html',
            ])

        scraped_data = []
        for url in urls_to_try:
            result = self.scrape_url(url, domain)
            if result:
                scraped_data.append(result)

                # If full crawl, follow internal links
                if full_crawl:
                    for link in result['links'][:20]:  # Limit to first 20 links
                        href = link.get('href')
                        abs_url = urljoin(url, href)

                        # Only crawl same domain
                        if urlparse(abs_url).netloc == urlparse(url).netloc:
                            if abs_url not in self.visited_urls:
                                time.sleep(0.5)  # Be polite
                                self.scrape_url(abs_url, domain)

        return scraped_data

    def detect_duplicates(self):
        """Find duplicate content across different URLs"""
        print("\n🔍 Detecting duplicate content...\n")

        # Find URLs with same content_hash
        duplicates = self.db.execute('''
            SELECT content_hash, GROUP_CONCAT(url, '|||') as urls, COUNT(*) as count
            FROM scraped_content
            WHERE content_hash IS NOT NULL
            GROUP BY content_hash
            HAVING COUNT(*) > 1
        ''').fetchall()

        for dup in duplicates:
            urls = dup['urls'].split('|||')
            print(f"⚠️  Duplicate content found ({dup['count']} copies):")
            for url in urls:
                print(f"   • {url}")

            # Mark as duplicates in database
            primary_url = urls[0]  # First one is canonical
            for url in urls[1:]:
                self.db.execute('''
                    UPDATE site_audit
                    SET is_duplicate = 1, duplicate_of_url = ?
                    WHERE url = ?
                ''', (primary_url, url))

        self.db.commit()
        return len(duplicates)

    def generate_report(self):
        """Generate summary report of scrape results"""
        print("\n" + "="*80)
        print("📊 AUDIT REPORT")
        print("="*80 + "\n")

        # Total URLs scraped
        total = self.db.execute('SELECT COUNT(*) as count FROM site_audit').fetchone()
        print(f"Total URLs scraped: {total['count']}")

        # By domain
        by_domain = self.db.execute('''
            SELECT domain, COUNT(*) as count
            FROM site_audit
            GROUP BY domain
        ''').fetchall()

        print("\nBy Domain:")
        for row in by_domain:
            print(f"  • {row['domain']}: {row['count']} pages")

        # HTTP errors
        errors = self.db.execute('''
            SELECT url, status_code, http_error
            FROM site_audit
            WHERE status_code != 200 OR http_error IS NOT NULL
        ''').fetchall()

        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors[:10]:
                print(f"  • {error['url']} - {error['http_error'] or f'HTTP {error['status_code']}'}")

        # Duplicates
        dups = self.db.execute('''
            SELECT COUNT(*) as count
            FROM site_audit
            WHERE is_duplicate = 1
        ''').fetchone()

        if dups['count'] > 0:
            print(f"\n⚠️  Duplicate content: {dups['count']} pages")

            dup_pairs = self.db.execute('''
                SELECT url, duplicate_of_url
                FROM site_audit
                WHERE is_duplicate = 1
            ''').fetchall()

            for pair in dup_pairs[:5]:
                print(f"  • {pair['url']}")
                print(f"    → Duplicate of: {pair['duplicate_of_url']}")

        # Broken links (TODO: implement link checking)
        print("\n🔗 Links extracted: ")
        link_count = self.db.execute('SELECT COUNT(*) as count FROM scraped_links').fetchone()
        print(f"  Total: {link_count['count']}")

        external_count = self.db.execute('''
            SELECT COUNT(*) as count FROM scraped_links WHERE is_external = 1
        ''').fetchone()
        print(f"  External: {external_count['count']}")

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description='Scrape live domains for audit')
    parser.add_argument('--domain', help='Scrape specific domain only')
    parser.add_argument('--full-crawl', action='store_true',
                       help='Follow internal links (slower)')
    args = parser.parse_args()

    scraper = DomainScraper()
    scraper.init_audit_tables()

    try:
        if args.domain:
            scraper.scrape_domain(args.domain, full_crawl=args.full_crawl)
        else:
            # Scrape all configured domains
            for domain in DOMAINS:
                scraper.scrape_domain(domain, full_crawl=args.full_crawl)
                time.sleep(1)  # Be polite between domains

        # Detect duplicates
        dup_count = scraper.detect_duplicates()

        # Generate report
        scraper.generate_report()

        print("\n✅ Scraping complete!")
        print(f"📁 Audit data stored in: {DB_PATH}")
        print(f"   Tables: site_audit, scraped_links, scraped_content")

    finally:
        scraper.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Government Data Scraper - Public Data Aggregation

Scrapes public government data sources:
- Congress.gov (bills, votes, members)
- SEC Edgar (company filings)
- USPTO (patents)
- FDA (drug approvals)
- Federal Register (regulations)

All data is public domain (17 USC §105 - US government works not copyrighted)

Usage:
    python3 gov_data_scraper.py init
    python3 gov_data_scraper.py scrape --sources congress,sec
    python3 gov_data_scraper.py search "artificial intelligence"
"""

import requests
from bs4 import BeautifulSoup
from database import get_db
from datetime import datetime, timezone, timedelta
import json
import hashlib
import time
import re


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

def init_gov_data_tables():
    """Initialize government data tables"""
    db = get_db()

    # Scraped government data
    db.execute('''
        CREATE TABLE IF NOT EXISTS gov_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            data_type TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            content_hash TEXT UNIQUE NOT NULL,
            summary TEXT,
            data_json TEXT,
            published_date TEXT,
            scraped_at TEXT NOT NULL,
            cache_expires TEXT,
            tags TEXT,
            UNIQUE(source, content_hash)
        )
    ''')

    # Index for fast lookups
    db.execute('CREATE INDEX IF NOT EXISTS idx_gov_data_source ON gov_data(source)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_gov_data_type ON gov_data(data_type)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_gov_data_published ON gov_data(published_date)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_gov_data_tags ON gov_data(tags)')

    # Link voice recordings to government data
    db.execute('''
        CREATE TABLE IF NOT EXISTS recording_gov_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            gov_data_id INTEGER NOT NULL,
            relevance_score REAL DEFAULT 0.5,
            created_at TEXT NOT NULL,
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
            FOREIGN KEY (gov_data_id) REFERENCES gov_data(id),
            UNIQUE(recording_id, gov_data_id)
        )
    ''')

    db.commit()
    print("✅ Government data tables created")


# ============================================================================
# CONGRESS.GOV SCRAPER
# ============================================================================

def scrape_congress_bills(max_results=10):
    """
    Scrape recent bills from Congress.gov

    Returns: List of bill dicts
    """
    bills = []

    try:
        # Congress.gov API (public, no auth needed)
        url = "https://api.congress.gov/v3/bill"
        params = {
            'format': 'json',
            'limit': max_results,
            'sort': 'updateDate+desc'
        }

        # Note: Congress API requires API key (get from api.data.gov)
        # For now, we'll scrape the HTML version
        url = "https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D&pageSize=20"

        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SoulfraScraper/1.0)'
        })

        if response.status_code != 200:
            print(f"⚠️  Congress.gov returned {response.status_code}")
            return bills

        soup = BeautifulSoup(response.content, 'html.parser')

        # Parse bill listings
        bill_items = soup.select('.expanded')[:max_results]

        for item in bill_items:
            try:
                title_el = item.select_one('.result-heading a')
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                bill_url = 'https://www.congress.gov' + title_el['href']

                # Extract bill number
                bill_number = title.split('.')[0] if '.' in title else title

                # Get summary
                summary_el = item.select_one('.result-item p')
                summary = summary_el.get_text(strip=True) if summary_el else ""

                # Get sponsor
                sponsor_el = item.select_one('.result-item')
                sponsor = ""
                if sponsor_el:
                    sponsor_text = sponsor_el.get_text()
                    if 'Sponsor:' in sponsor_text:
                        sponsor = sponsor_text.split('Sponsor:')[1].split('|')[0].strip()

                bills.append({
                    'source': 'congress',
                    'data_type': 'bill',
                    'title': title,
                    'url': bill_url,
                    'summary': summary[:500],
                    'data_json': json.dumps({
                        'bill_number': bill_number,
                        'sponsor': sponsor,
                        'chamber': 'House' if 'H.R.' in bill_number else 'Senate' if 'S.' in bill_number else 'Unknown'
                    }),
                    'tags': f"congress,bill,{bill_number.lower()}"
                })

            except Exception as e:
                print(f"⚠️  Error parsing bill: {e}")
                continue

        print(f"✅ Scraped {len(bills)} bills from Congress.gov")

    except Exception as e:
        print(f"❌ Congress.gov scraping failed: {e}")

    return bills


# ============================================================================
# SEC EDGAR SCRAPER
# ============================================================================

def scrape_sec_filings(company="", max_results=10):
    """
    Scrape recent SEC filings from Edgar

    Args:
        company: Company name or ticker (optional)
        max_results: Max filings to return

    Returns: List of filing dicts
    """
    filings = []

    try:
        # SEC Edgar RSS feed (public, no auth)
        if company:
            # Search for specific company
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={company}&type=&dateb=&owner=include&count={max_results}"
        else:
            # Get recent filings
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count={max_results}&output=atom"

        response = requests.get(search_url, timeout=15, headers={
            'User-Agent': 'Soulfra contact@soulfra.com'  # SEC requires user agent
        })

        if response.status_code != 200:
            print(f"⚠️  SEC Edgar returned {response.status_code}")
            return filings

        soup = BeautifulSoup(response.content, 'xml')

        # Parse RSS entries
        entries = soup.find_all('entry')[:max_results]

        for entry in entries:
            try:
                title = entry.find('title').text if entry.find('title') else 'Untitled'
                link = entry.find('link')['href'] if entry.find('link') else ''
                summary = entry.find('summary').text if entry.find('summary') else ''
                updated = entry.find('updated').text if entry.find('updated') else ''

                # Extract company name from title
                company_name = title.split('-')[0].strip() if '-' in title else ''

                # Extract filing type
                filing_type = ''
                if '/' in title:
                    filing_type = title.split('/')[0].strip()

                filings.append({
                    'source': 'sec',
                    'data_type': 'filing',
                    'title': title,
                    'url': f"https://www.sec.gov{link}" if link.startswith('/') else link,
                    'summary': summary[:500],
                    'data_json': json.dumps({
                        'company': company_name,
                        'filing_type': filing_type,
                        'updated': updated
                    }),
                    'published_date': updated,
                    'tags': f"sec,filing,{filing_type.lower()},{company_name.lower().replace(' ', '-')}"
                })

            except Exception as e:
                print(f"⚠️  Error parsing SEC filing: {e}")
                continue

        print(f"✅ Scraped {len(filings)} SEC filings")

    except Exception as e:
        print(f"❌ SEC scraping failed: {e}")

    return filings


# ============================================================================
# USPTO SCRAPER
# ============================================================================

def scrape_uspto_patents(keyword="", max_results=10):
    """
    Scrape recent patents from USPTO

    Args:
        keyword: Search keyword (optional)
        max_results: Max patents to return

    Returns: List of patent dicts
    """
    patents = []

    try:
        # USPTO Public PAIR (Patent Application Information Retrieval)
        # Note: Full USPTO API requires registration
        # Using public search for now

        if keyword:
            search_url = f"https://ppubs.uspto.gov/pubwebapp/static/pages/searchbool.html"
            # Would need to POST search query
            print("⚠️  USPTO keyword search requires form submission - skipping for now")
            return patents
        else:
            # Get recent published applications
            url = "https://ped.uspto.gov/peds/"
            print("⚠️  USPTO scraping requires API key - placeholder for now")

            # Placeholder patents (would come from real API)
            patents.append({
                'source': 'uspto',
                'data_type': 'patent',
                'title': 'USPTO API Integration Required',
                'url': 'https://www.uspto.gov/',
                'summary': 'Full USPTO integration requires API registration at developer.uspto.gov',
                'data_json': json.dumps({'status': 'placeholder'}),
                'tags': 'uspto,patent,placeholder'
            })

    except Exception as e:
        print(f"❌ USPTO scraping failed: {e}")

    return patents


# ============================================================================
# FDA SCRAPER
# ============================================================================

def scrape_fda_approvals(max_results=10):
    """
    Scrape recent drug approvals from FDA

    Returns: List of approval dicts
    """
    approvals = []

    try:
        # FDA Drugs@FDA database
        url = "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm"

        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SoulfraScraper/1.0)'
        })

        if response.status_code != 200:
            print(f"⚠️  FDA returned {response.status_code}")
            return approvals

        soup = BeautifulSoup(response.content, 'html.parser')

        # FDA page structure changes frequently
        # This is a placeholder - would need to parse actual approval tables

        approvals.append({
            'source': 'fda',
            'data_type': 'drug_approval',
            'title': 'FDA Drugs@FDA Database',
            'url': url,
            'summary': 'FDA drug approval database - integration in progress',
            'data_json': json.dumps({'status': 'placeholder'}),
            'tags': 'fda,drug,approval,placeholder'
        })

        print(f"⚠️  FDA scraping requires specialized parser - placeholder created")

    except Exception as e:
        print(f"❌ FDA scraping failed: {e}")

    return approvals


# ============================================================================
# SAVE TO DATABASE
# ============================================================================

def save_gov_data(data_items):
    """
    Save scraped government data to database

    Args:
        data_items: List of data dicts from scrapers

    Returns:
        int: Number of new items saved
    """
    db = get_db()
    saved_count = 0

    now = datetime.now(timezone.utc).isoformat()
    cache_expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    for item in data_items:
        # Create content hash
        content_str = f"{item['source']}:{item['title']}:{item['url']}"
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        try:
            db.execute('''
                INSERT OR IGNORE INTO gov_data
                (source, data_type, title, url, content_hash, summary, data_json,
                 published_date, scraped_at, cache_expires, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['source'],
                item['data_type'],
                item['title'],
                item['url'],
                content_hash,
                item.get('summary', ''),
                item.get('data_json', '{}'),
                item.get('published_date', now),
                now,
                cache_expires,
                item.get('tags', '')
            ))

            if db.total_changes > 0:
                saved_count += 1

        except Exception as e:
            print(f"⚠️  Error saving {item['title'][:50]}: {e}")

    db.commit()
    print(f"✅ Saved {saved_count} new government data items")

    return saved_count


# ============================================================================
# SEARCH & RETRIEVAL
# ============================================================================

def search_gov_data(query, sources=None, data_types=None, limit=20):
    """
    Search government data

    Args:
        query: Search query
        sources: Filter by sources (list)
        data_types: Filter by data types (list)
        limit: Max results

    Returns:
        List of matching items
    """
    db = get_db()

    sql = "SELECT * FROM gov_data WHERE 1=1"
    params = []

    if query:
        sql += " AND (title LIKE ? OR summary LIKE ? OR tags LIKE ?)"
        search_term = f"%{query}%"
        params.extend([search_term, search_term, search_term])

    if sources:
        placeholders = ','.join(['?' for _ in sources])
        sql += f" AND source IN ({placeholders})"
        params.extend(sources)

    if data_types:
        placeholders = ','.join(['?' for _ in data_types])
        sql += f" AND data_type IN ({placeholders})"
        params.extend(data_types)

    sql += " ORDER BY published_date DESC LIMIT ?"
    params.append(limit)

    results = db.execute(sql, params).fetchall()

    return [dict(row) for row in results]


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Government Data Scraper")
        print("\nUsage:")
        print("  python3 gov_data_scraper.py init")
        print("  python3 gov_data_scraper.py scrape --sources congress,sec")
        print("  python3 gov_data_scraper.py search 'artificial intelligence'")
        print("  python3 gov_data_scraper.py stats")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_gov_data_tables()

    elif command == "scrape":
        # Parse sources
        sources = ['congress', 'sec', 'uspto', 'fda']
        if '--sources' in sys.argv:
            idx = sys.argv.index('--sources')
            if len(sys.argv) > idx + 1:
                sources = sys.argv[idx + 1].split(',')

        all_data = []

        if 'congress' in sources:
            print("\n📜 Scraping Congress.gov...")
            all_data.extend(scrape_congress_bills())

        if 'sec' in sources:
            print("\n💼 Scraping SEC Edgar...")
            all_data.extend(scrape_sec_filings())

        if 'uspto' in sources:
            print("\n🔬 Scraping USPTO...")
            all_data.extend(scrape_uspto_patents())

        if 'fda' in sources:
            print("\n💊 Scraping FDA...")
            all_data.extend(scrape_fda_approvals())

        print(f"\n📊 Total items scraped: {len(all_data)}")
        saved = save_gov_data(all_data)
        print(f"✅ Saved {saved} new items to database")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python3 gov_data_scraper.py search 'query'")
            sys.exit(1)

        query = sys.argv[2]
        results = search_gov_data(query)

        print(f"\n🔍 Found {len(results)} results for '{query}':\n")
        for item in results:
            print(f"  [{item['source'].upper()}] {item['title']}")
            print(f"  {item['url']}")
            print(f"  {item['summary'][:100]}...")
            print()

    elif command == "stats":
        db = get_db()

        total = db.execute("SELECT COUNT(*) as count FROM gov_data").fetchone()['count']
        by_source = db.execute("SELECT source, COUNT(*) as count FROM gov_data GROUP BY source").fetchall()

        print("\n📊 Government Data Statistics:\n")
        print(f"  Total items: {total}")
        print("\n  By source:")
        for row in by_source:
            print(f"    {row['source']}: {row['count']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

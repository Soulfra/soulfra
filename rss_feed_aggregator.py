#!/usr/bin/env python3
"""
RSS Feed Aggregator - Cross-Site Content Stitching

Aggregates RSS feeds from:
1. Local files: output/*/feed.xml (soulfra, calriven, deathtodata, etc.)
2. Remote URLs: https://soulfra.com/feed.xml, https://cringeproof.com/feed.xml
3. GitHub Pages: https://soulfra.github.io/voice-archive/feed.xml

Features:
- Unified feed across all domains
- Infinite scroll API
- Merge by date, deduplicate by GUID
- "Scrolless/unlimited page" - continuous content from all sources

Usage:
    python3 rss_feed_aggregator.py --fetch
    python3 rss_feed_aggregator.py --stats
    python3 rss_feed_aggregator.py --export aggregated.json
"""

from flask import Blueprint, render_template, request, jsonify
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import glob
import json
import urllib.request
import urllib.error
from email.utils import parsedate_to_datetime

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
NC = '\033[0m'

rss_aggregator_bp = Blueprint('rss_aggregator', __name__)


class RSSAggregator:
    """Aggregate RSS feeds from multiple sources"""

    def __init__(self):
        self.items = []
        self.sources = {
            'local': [],
            'remote': [],
            'github': []
        }

    def fetch_local_feeds(self, search_path='output') -> List[Dict]:
        """Fetch RSS feeds from local output/ directory"""
        local_feeds = []

        # Find all feed.xml files in output/
        for feed_path in glob.glob(f'{search_path}/*/feed.xml'):
            try:
                domain = Path(feed_path).parent.name
                feed_items = self._parse_rss_file(feed_path, source=domain, source_type='local')
                local_feeds.extend(feed_items)
                self.sources['local'].append({'domain': domain, 'path': feed_path, 'items': len(feed_items)})
                print(f"{GREEN}✅ Loaded {len(feed_items)} items from {domain}{NC}")
            except Exception as e:
                print(f"{RED}❌ Failed to parse {feed_path}: {e}{NC}")

        # Also check voice-archive/feed.xml
        voice_archive_path = 'voice-archive/feed.xml'
        if Path(voice_archive_path).exists():
            try:
                feed_items = self._parse_rss_file(voice_archive_path, source='voice-archive', source_type='local')
                local_feeds.extend(feed_items)
                self.sources['local'].append({'domain': 'voice-archive', 'path': voice_archive_path, 'items': len(feed_items)})
                print(f"{GREEN}✅ Loaded {len(feed_items)} items from voice-archive{NC}")
            except Exception as e:
                print(f"{RED}❌ Failed to parse {voice_archive_path}: {e}{NC}")

        return local_feeds

    def fetch_remote_feeds(self, urls: List[str] = None) -> List[Dict]:
        """Fetch RSS feeds from remote URLs"""
        if urls is None:
            urls = [
                'https://soulfra.com/feed.xml',
                'https://cringeproof.com/feed.xml',
                'https://calriven.com/feed.xml',
                'https://deathtodata.com/feed.xml',
                'https://soulfra.github.io/voice-archive/feed.xml'
            ]

        remote_feeds = []

        for url in urls:
            try:
                print(f"{CYAN}🌐 Fetching {url}...{NC}")
                req = urllib.request.Request(url, headers={'User-Agent': 'RSSAggregator/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()

                domain = url.split('/')[2]  # Extract domain from URL
                feed_items = self._parse_rss_xml(xml_data, source=domain, source_type='remote')
                remote_feeds.extend(feed_items)
                self.sources['remote'].append({'domain': domain, 'url': url, 'items': len(feed_items)})
                print(f"{GREEN}✅ Loaded {len(feed_items)} items from {domain}{NC}")
            except urllib.error.URLError as e:
                print(f"{YELLOW}⚠️  Could not fetch {url}: {e}{NC}")
            except Exception as e:
                print(f"{RED}❌ Failed to parse {url}: {e}{NC}")

        return remote_feeds

    def _parse_rss_file(self, filepath: str, source: str, source_type: str) -> List[Dict]:
        """Parse RSS feed from local file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            xml_data = f.read()
        return self._parse_rss_xml(xml_data, source, source_type)

    def _parse_rss_xml(self, xml_data: bytes, source: str, source_type: str) -> List[Dict]:
        """Parse RSS XML data"""
        items = []

        try:
            root = ET.fromstring(xml_data)

            # Handle both RSS 2.0 and Atom feeds
            if root.tag == 'rss':
                channel = root.find('channel')
                entries = channel.findall('item') if channel is not None else []
            elif 'feed' in root.tag:
                entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            else:
                entries = []

            for entry in entries:
                item = self._extract_item_data(entry, source, source_type)
                if item:
                    items.append(item)

        except ET.ParseError as e:
            print(f"{RED}❌ XML Parse Error in {source}: {e}{NC}")

        return items

    def _extract_item_data(self, entry, source: str, source_type: str) -> Dict:
        """Extract item data from RSS entry"""
        try:
            # Try RSS 2.0 format first
            title = entry.findtext('title', '').strip()
            link = entry.findtext('link', '').strip()
            description = entry.findtext('description', '').strip()
            pub_date_str = entry.findtext('pubDate', '')
            guid = entry.findtext('guid', link)  # Fallback to link if no GUID

            # Try Atom format if RSS fields are empty
            if not title:
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text if title_elem is not None else ''

            if not link:
                link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                link = link_elem.get('href', '') if link_elem is not None else ''

            # Parse date
            pub_date = None
            if pub_date_str:
                try:
                    # Try RFC 2822 format (RSS 2.0)
                    pub_date = parsedate_to_datetime(pub_date_str)
                except:
                    try:
                        # Try ISO format
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    except:
                        pub_date = None

            # Check for enclosure (audio/video)
            enclosure = entry.find('enclosure')
            enclosure_url = None
            enclosure_type = None
            if enclosure is not None:
                enclosure_url = enclosure.get('url')
                enclosure_type = enclosure.get('type')

            return {
                'title': title,
                'link': link,
                'description': description,
                'pub_date': pub_date,
                'pub_date_str': pub_date.isoformat() if pub_date else '',
                'guid': guid,
                'source': source,
                'source_type': source_type,
                'enclosure_url': enclosure_url,
                'enclosure_type': enclosure_type
            }

        except Exception as e:
            print(f"{YELLOW}⚠️  Could not parse item from {source}: {e}{NC}")
            return None

    def aggregate_all(self, fetch_remote=True):
        """Fetch feeds from all sources"""
        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}📡 RSS Feed Aggregator{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")

        # Local feeds
        print(f"{CYAN}📁 Fetching local feeds...{NC}")
        local_items = self.fetch_local_feeds()
        print(f"   Found {len(local_items)} items from {len(self.sources['local'])} local sources\n")

        # Remote feeds (optional, can be slow)
        remote_items = []
        if fetch_remote:
            print(f"{CYAN}🌐 Fetching remote feeds...{NC}")
            remote_items = self.fetch_remote_feeds()
            print(f"   Found {len(remote_items)} items from {len(self.sources['remote'])} remote sources\n")

        # Combine all
        self.items = local_items + remote_items

        # Sort by date (newest first) - handle timezone-aware and naive datetimes
        def get_sort_key(item):
            pub_date = item.get('pub_date')
            if pub_date is None:
                # Use a very old date for items without pub_date
                return datetime(1970, 1, 1)
            # Remove timezone info to allow comparison
            if pub_date.tzinfo is not None:
                return pub_date.replace(tzinfo=None)
            return pub_date

        self.items.sort(key=get_sort_key, reverse=True)

        # Deduplicate by GUID
        seen_guids = set()
        deduplicated = []
        for item in self.items:
            if item['guid'] not in seen_guids:
                deduplicated.append(item)
                seen_guids.add(item['guid'])

        self.items = deduplicated

        print(f"{GREEN}✅ Total items aggregated: {len(self.items)}{NC}\n")

        return self.items

    def search(self, query: str, case_sensitive=False) -> List[Dict]:
        """Search aggregated items by keyword"""
        if not self.items:
            self.aggregate_all(fetch_remote=False)

        query_lower = query if case_sensitive else query.lower()

        results = []
        for item in self.items:
            title = item.get('title', '')
            description = item.get('description', '')
            combined = f"{title} {description}"

            if not case_sensitive:
                combined = combined.lower()

            if query_lower in combined:
                results.append(item)

        return results

    def get_paginated(self, offset=0, limit=10) -> Dict:
        """Get paginated items for API response"""
        if not self.items:
            self.aggregate_all(fetch_remote=False)

        total = len(self.items)
        items_slice = self.items[offset:offset + limit]
        has_more = (offset + limit) < total

        return {
            'items': items_slice,
            'has_more': has_more,
            'offset': offset,
            'limit': limit,
            'total': total
        }

    def export(self, output_file='aggregated_feed.json'):
        """Export aggregated feed to JSON"""
        if not self.items:
            self.aggregate_all(fetch_remote=False)

        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_items': len(self.items),
            'sources': {
                'local': self.sources['local'],
                'remote': self.sources['remote']
            },
            'items': self.items
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n{GREEN}✅ Exported {len(self.items)} items to {output_file}{NC}\n")

    def stats(self):
        """Print statistics about aggregated feed"""
        if not self.items:
            self.aggregate_all(fetch_remote=False)

        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}📊 RSS Aggregation Statistics{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")

        # By source
        by_source = {}
        for item in self.items:
            source = item.get('source', 'unknown')
            by_source[source] = by_source.get(source, 0) + 1

        print(f"{CYAN}By Source:{NC}")
        for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source:30} {count:>6} items")

        # By source type
        by_type = {}
        for item in self.items:
            source_type = item.get('source_type', 'unknown')
            by_type[source_type] = by_type.get(source_type, 0) + 1

        print(f"\n{CYAN}By Type:{NC}")
        for stype, count in by_type.items():
            print(f"   {stype:30} {count:>6} items")

        # With enclosures (audio/video)
        with_enclosures = len([i for i in self.items if i.get('enclosure_url')])

        print(f"\n{CYAN}Media:{NC}")
        print(f"   Total items:                   {len(self.items):>6}")
        print(f"   With audio/video:              {with_enclosures:>6}")

        print()


# Flask Blueprint for API

# Global aggregator instance (cached)
_aggregator = None

def get_aggregator():
    """Get or create aggregator instance"""
    global _aggregator
    if _aggregator is None:
        _aggregator = RSSAggregator()
        _aggregator.aggregate_all(fetch_remote=False)  # Only local by default for speed
    return _aggregator


@rss_aggregator_bp.route('/aggregated-feed')
def aggregated_feed_page():
    """
    Display aggregated feed page with infinite scroll

    All content from all domains stitched together chronologically
    """
    return render_template('aggregated_feed.html')


@rss_aggregator_bp.route('/api/aggregated-feed')
def get_aggregated_feed():
    """
    Get aggregated RSS feed items

    Query params:
      - offset: Start index (default 0)
      - limit: Number of items (default 10)
      - refresh: Force refresh from sources (default false)

    Response:
      {
        "items": [
          {
            "title": "...",
            "link": "...",
            "description": "...",
            "pub_date": "2026-01-03T...",
            "source": "soulfra",
            "source_type": "local",
            "enclosure_url": "...",
            "enclosure_type": "audio/webm"
          }
        ],
        "has_more": true,
        "offset": 0,
        "limit": 10,
        "total": 42
      }
    """
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))
    refresh = request.args.get('refresh', 'false').lower() == 'true'

    aggregator = get_aggregator()

    # Force refresh if requested
    if refresh:
        aggregator.aggregate_all(fetch_remote=False)

    result = aggregator.get_paginated(offset=offset, limit=limit)

    return jsonify(result)


@rss_aggregator_bp.route('/api/aggregated-feed/search')
def search_aggregated_feed():
    """
    Search aggregated feed

    Query params:
      - q: Search query
      - limit: Max results (default 20)

    Response:
      {
        "query": "ai",
        "results": [...],
        "count": 15
      }
    """
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))

    if not query:
        return jsonify({'error': 'Missing query parameter "q"'}), 400

    aggregator = get_aggregator()
    results = aggregator.search(query)[:limit]

    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })


def register_rss_aggregator_routes(app):
    """Register RSS aggregator routes"""
    app.register_blueprint(rss_aggregator_bp)
    print('📡 RSS Feed Aggregator routes registered')
    print('   Page: /aggregated-feed')
    print('   API: /api/aggregated-feed')
    print('   API: /api/aggregated-feed/search')


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description='RSS Feed Aggregator')
    parser.add_argument('--fetch', action='store_true', help='Fetch and display all feeds')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    parser.add_argument('--search', type=str, help='Search feeds')
    parser.add_argument('--remote', action='store_true', help='Include remote feeds (slower)')

    args = parser.parse_args()

    aggregator = RSSAggregator()

    if args.fetch:
        aggregator.aggregate_all(fetch_remote=args.remote)

    if args.search:
        print(f"\n{CYAN}🔍 Searching for: \"{args.search}\"{NC}\n")
        results = aggregator.search(args.search)

        if results:
            print(f"{GREEN}Found {len(results)} matches:{NC}\n")
            for i, result in enumerate(results[:10], 1):
                print(f"{i}. [{result['source']}] {result['title']}")
                print(f"   {result['link']}")
                print()

            if len(results) > 10:
                print(f"   ... and {len(results) - 10} more results\n")
        else:
            print(f"{YELLOW}No matches found.{NC}\n")

    elif args.export:
        aggregator.export(args.export)

    elif args.stats:
        aggregator.stats()

    else:
        # Default: show stats
        aggregator.aggregate_all(fetch_remote=args.remote)
        aggregator.stats()


if __name__ == '__main__':
    main()

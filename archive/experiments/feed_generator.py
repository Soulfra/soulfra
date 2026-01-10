#!/usr/bin/env python3
"""
Feed Generator - RSS/Atom/JSON Feeds

Generates syndication feeds for:
- Daily color challenges
- Catchphrase A/B tests
- Brand personality updates
- CalRiven neural brain snapshots

Supports:
- RSS 2.0
- Atom 1.0
- JSON Feed 1.1
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def parse_datetime(dt_input) -> datetime:
    """Parse datetime from string or datetime object"""
    if isinstance(dt_input, datetime):
        return dt_input
    elif isinstance(dt_input, str):
        # Try parsing various formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(dt_input, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        # If all formats fail, raise error
        raise ValueError(f"Unable to parse datetime: {dt_input}")
    else:
        raise TypeError(f"Expected datetime or str, got {type(dt_input)}")


def format_rfc822_date(dt) -> str:
    """Format datetime as RFC 822 (for RSS)"""
    dt = parse_datetime(dt)
    return dt.strftime('%a, %d %b %Y %H:%M:%S %z') or dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


def format_rfc3339_date(dt) -> str:
    """Format datetime as RFC 3339 (for Atom/JSON)"""
    dt = parse_datetime(dt)
    return dt.isoformat() + 'Z' if not dt.tzinfo else dt.isoformat()


def generate_rss_feed(
    items: List[Dict[str, Any]],
    title: str,
    description: str,
    link: str,
    language: str = 'en-us',
    image_url: Optional[str] = None
) -> str:
    """
    Generate RSS 2.0 feed

    Args:
        items: List of feed items with keys:
            - title: str
            - link: str
            - description: str
            - pub_date: datetime
            - guid: str
            - author: Optional[str]
        title: Feed title
        description: Feed description
        link: Feed URL
        language: Language code
        image_url: Optional feed image

    Returns:
        RSS XML string
    """
    rss = Element('rss', version='2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')

    channel = SubElement(rss, 'channel')

    # Channel metadata
    SubElement(channel, 'title').text = title
    SubElement(channel, 'link').text = link
    SubElement(channel, 'description').text = description
    SubElement(channel, 'language').text = language
    SubElement(channel, 'lastBuildDate').text = format_rfc822_date(datetime.now(timezone.utc))
    SubElement(channel, 'generator').text = 'Soulfra Feed Generator 1.0'

    # Self-reference
    atom_link = SubElement(channel, 'atom:link')
    atom_link.set('href', link)
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    # Optional image
    if image_url:
        image = SubElement(channel, 'image')
        SubElement(image, 'url').text = image_url
        SubElement(image, 'title').text = title
        SubElement(image, 'link').text = link

    # Items
    for item_data in items:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = item_data['title']
        SubElement(item, 'link').text = item_data['link']
        SubElement(item, 'description').text = item_data['description']
        SubElement(item, 'pubDate').text = format_rfc822_date(item_data['pub_date'])
        SubElement(item, 'guid', isPermaLink='true').text = item_data['guid']

        if 'author' in item_data and item_data['author']:
            SubElement(item, 'author').text = item_data['author']

        if 'category' in item_data:
            SubElement(item, 'category').text = item_data['category']

    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss)).toprettyxml(indent='  ')
    return xml_str


def generate_atom_feed(
    items: List[Dict[str, Any]],
    title: str,
    subtitle: str,
    link: str,
    feed_id: str,
    author_name: str,
    author_email: str
) -> str:
    """
    Generate Atom 1.0 feed

    Args:
        items: List of feed items with keys:
            - title: str
            - link: str
            - summary: str
            - updated: datetime
            - id: str
            - content: Optional[str]
            - author: Optional[str]
        title: Feed title
        subtitle: Feed subtitle/description
        link: Feed URL
        feed_id: Unique feed ID (URI)
        author_name: Feed author name
        author_email: Feed author email

    Returns:
        Atom XML string
    """
    feed = Element('feed', xmlns='http://www.w3.org/2005/Atom')

    # Feed metadata
    SubElement(feed, 'title').text = title
    SubElement(feed, 'subtitle').text = subtitle
    SubElement(feed, 'id').text = feed_id
    SubElement(feed, 'updated').text = format_rfc3339_date(datetime.now(timezone.utc))

    # Self link
    link_elem = SubElement(feed, 'link')
    link_elem.set('href', link)
    link_elem.set('rel', 'self')

    # Author
    author = SubElement(feed, 'author')
    SubElement(author, 'name').text = author_name
    SubElement(author, 'email').text = author_email

    # Generator
    generator = SubElement(feed, 'generator')
    generator.text = 'Soulfra Feed Generator'
    generator.set('version', '1.0')

    # Entries
    for item_data in items:
        entry = SubElement(feed, 'entry')
        SubElement(entry, 'title').text = item_data['title']
        SubElement(entry, 'id').text = item_data['id']
        SubElement(entry, 'updated').text = format_rfc3339_date(item_data['updated'])

        # Link
        entry_link = SubElement(entry, 'link')
        entry_link.set('href', item_data['link'])

        # Summary
        summary = SubElement(entry, 'summary')
        summary.set('type', 'html')
        summary.text = item_data['summary']

        # Optional full content
        if 'content' in item_data and item_data['content']:
            content = SubElement(entry, 'content')
            content.set('type', 'html')
            content.text = item_data['content']

        # Optional author
        if 'author' in item_data and item_data['author']:
            entry_author = SubElement(entry, 'author')
            SubElement(entry_author, 'name').text = item_data['author']

    # Pretty print XML
    xml_str = minidom.parseString(tostring(feed)).toprettyxml(indent='  ')
    return xml_str


def generate_json_feed(
    items: List[Dict[str, Any]],
    title: str,
    home_page_url: str,
    feed_url: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    favicon: Optional[str] = None,
    author_name: Optional[str] = None
) -> str:
    """
    Generate JSON Feed 1.1

    Args:
        items: List of feed items with keys:
            - id: str
            - url: str
            - title: str
            - content_html: str
            - date_published: datetime
            - summary: Optional[str]
            - image: Optional[str]
            - author: Optional[Dict]
        title: Feed title
        home_page_url: Website URL
        feed_url: Feed URL
        description: Feed description
        icon: Large icon URL (512x512)
        favicon: Small icon URL (64x64)
        author_name: Feed author name

    Returns:
        JSON string
    """
    feed = {
        'version': 'https://jsonfeed.org/version/1.1',
        'title': title,
        'home_page_url': home_page_url,
        'feed_url': feed_url
    }

    if description:
        feed['description'] = description

    if icon:
        feed['icon'] = icon

    if favicon:
        feed['favicon'] = favicon

    if author_name:
        feed['authors'] = [{'name': author_name}]

    # Items
    feed['items'] = []
    for item_data in items:
        item = {
            'id': item_data['id'],
            'url': item_data['url'],
            'title': item_data['title'],
            'content_html': item_data['content_html'],
            'date_published': format_rfc3339_date(item_data['date_published'])
        }

        if 'summary' in item_data:
            item['summary'] = item_data['summary']

        if 'image' in item_data:
            item['image'] = item_data['image']

        if 'author' in item_data:
            item['authors'] = [item_data['author']]

        if 'tags' in item_data:
            item['tags'] = item_data['tags']

        feed['items'].append(item)

    return json.dumps(feed, indent=2)


def generate_challenge_rss_items(challenges: List[Dict[str, Any]], base_url: str) -> List[Dict[str, Any]]:
    """
    Convert color challenges to RSS feed items

    Args:
        challenges: List of challenge dicts from database
        base_url: Base URL for links

    Returns:
        List of RSS item dicts
    """
    items = []
    for challenge in challenges:
        items.append({
            'title': f"Daily Color Challenge: {challenge['target_mood'].title()}",
            'link': f"{base_url}/challenge/{challenge['id']}",
            'description': challenge['description'],
            'pub_date': challenge.get('challenge_date') or challenge.get('created_at'),
            'guid': f"{base_url}/challenge/{challenge['id']}",
            'category': 'Color Challenge',
            'author': challenge.get('author', 'Soulfra')
        })
    return items


def generate_catchphrase_rss_items(catchphrases: List[Dict[str, Any]], base_url: str) -> List[Dict[str, Any]]:
    """
    Convert catchphrases to RSS feed items (for CalRiven brand testing)

    Args:
        catchphrases: List of catchphrase dicts from database
        base_url: Base URL for links

    Returns:
        List of RSS item dicts
    """
    items = []
    for phrase in catchphrases:
        items.append({
            'title': f"Catchphrase Test: {phrase['text'][:50]}...",
            'link': f"{base_url}/catchphrase/{phrase['id']}",
            'description': f"Vote on CalRiven's new catchphrase: \"{phrase['text']}\"",
            'pub_date': phrase.get('created_at'),
            'guid': f"{base_url}/catchphrase/{phrase['id']}",
            'category': 'Catchphrase Test',
            'author': phrase.get('creator', 'CalRiven')
        })
    return items


def generate_brand_personality_json_items(snapshots: List[Dict[str, Any]], base_url: str) -> List[Dict[str, Any]]:
    """
    Convert brand personality snapshots to JSON Feed items

    Args:
        snapshots: List of personality snapshot dicts
        base_url: Base URL for links

    Returns:
        List of JSON Feed item dicts
    """
    items = []
    for snapshot in snapshots:
        items.append({
            'id': f"{base_url}/brand/{snapshot['brand_id']}/snapshot/{snapshot['id']}",
            'url': f"{base_url}/brand/{snapshot['brand_id']}",
            'title': f"{snapshot['brand_name']} - Personality Update",
            'content_html': f"""
                <h2>{snapshot['brand_name']} Neural Brain Update</h2>
                <p><strong>Energy:</strong> {snapshot.get('energy', 'N/A')}</p>
                <p><strong>Warmth:</strong> {snapshot.get('warmth', 'N/A')}</p>
                <p><strong>Insight:</strong> {snapshot.get('personality_insight', 'No insight available')}</p>
            """,
            'date_published': snapshot.get('created_at'),
            'summary': f"Latest personality analysis for {snapshot['brand_name']}",
            'tags': ['personality', 'brand', 'neural-network'],
            'author': {'name': snapshot.get('brand_name', 'Unknown')}
        })
    return items


if __name__ == '__main__':
    # Test feed generation
    print("🧪 Testing Feed Generator\n")

    # Test data
    test_items_rss = [
        {
            'title': 'Daily Color Challenge: Energetic',
            'link': 'https://example.com/challenge/1',
            'description': 'Pick a color that feels energetic and vibrant!',
            'pub_date': datetime.now(timezone.utc),
            'guid': 'https://example.com/challenge/1',
            'category': 'Color Challenge',
            'author': 'Soulfra'
        }
    ]

    test_items_json = [
        {
            'id': 'https://example.com/challenge/1',
            'url': 'https://example.com/challenge/1',
            'title': 'Daily Color Challenge: Energetic',
            'content_html': '<p>Pick a color that feels energetic and vibrant!</p>',
            'date_published': datetime.now(timezone.utc),
            'summary': 'Daily color personality challenge',
            'tags': ['color', 'challenge', 'personality']
        }
    ]

    # Generate RSS
    print("✅ RSS 2.0 Feed:")
    rss = generate_rss_feed(
        items=test_items_rss,
        title='Soulfra Daily Challenges',
        description='Daily color challenges for neural personality testing',
        link='https://example.com/feeds/challenges.xml'
    )
    print(rss[:500] + '...\n')

    # Generate JSON Feed
    print("✅ JSON Feed:")
    json_feed = generate_json_feed(
        items=test_items_json,
        title='Soulfra Daily Challenges',
        home_page_url='https://example.com',
        feed_url='https://example.com/feeds/challenges.json',
        description='Daily color challenges for neural personality testing'
    )
    print(json_feed[:500] + '...\n')

    print("✅ Feed generator working!")

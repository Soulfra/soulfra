#!/usr/bin/env python3
"""
StPetePros Business Scraper
Scrapes local businesses from Google Places API and scores them for sales priority

Usage:
    python3 stpetepros_scraper.py --category plumbing --city "St. Petersburg, FL"
    python3 stpetepros_scraper.py --all-categories
    python3 stpetepros_scraper.py --export-airtable
"""

import os
import sqlite3
import json
import requests
import time
from datetime import datetime
from typing import List, Dict
import argparse

# Google Places API Configuration
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', 'YOUR_API_KEY_HERE')
GOOGLE_PLACES_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
GOOGLE_PLACES_DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY', 'YOUR_AIRTABLE_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'YOUR_BASE_ID')
AIRTABLE_TABLE_NAME = 'StPetePros Sales Leads'

# St. Petersburg coordinates (downtown)
ST_PETE_LAT = 27.7676
ST_PETE_LNG = -82.6403
SEARCH_RADIUS = 20000  # 20km radius

# Categories to scrape
CATEGORIES = {
    'plumbing': {'keyword': 'plumber', 'premium': True},
    'electrical': {'keyword': 'electrician', 'premium': True},
    'hvac': {'keyword': 'hvac', 'premium': True},
    'roofing': {'keyword': 'roofer', 'premium': True},
    'legal': {'keyword': 'lawyer', 'premium': True},
    'landscaping': {'keyword': 'landscaping', 'premium': False},
    'cleaning': {'keyword': 'cleaning service', 'premium': False},
    'pest-control': {'keyword': 'pest control', 'premium': True},
    'painting': {'keyword': 'painter', 'premium': False},
    'pool-service': {'keyword': 'pool service', 'premium': True},
    'real-estate': {'keyword': 'real estate agent', 'premium': True},
    'auto-repair': {'keyword': 'auto repair', 'premium': False}
}


def calculate_business_score(business: Dict) -> int:
    """
    Calculate sales priority score (0-100)

    Algorithm:
    - review_count * 2 (popular = busy = has money)
    - no_website * 30 (easy win, they need digital presence)
    - established_years * 5 (old business = trusted = has money)
    - premium_category * 20 (legal/hvac/medical pays more)
    """
    score = 0

    # Review count (max 40 points for 20+ reviews)
    review_count = business.get('review_count', 0)
    score += min(review_count * 2, 40)

    # No website = big opportunity (30 points)
    if not business.get('website') or business.get('website') == 'N/A':
        score += 30

    # Established business (estimate from reviews if available)
    # For now, we'll use review count as proxy: 50+ reviews = likely 5+ years
    if review_count >= 50:
        score += 25  # 5 years * 5 points
    elif review_count >= 20:
        score += 15  # 3 years * 5 points
    elif review_count >= 10:
        score += 10  # 2 years * 5 points

    # Premium category (legal, hvac, medical, etc.)
    if business.get('is_premium_category'):
        score += 20

    # High rating but poor digital = perfect target
    rating = business.get('rating', 0)
    if rating >= 4.5 and not business.get('website'):
        score += 10  # Bonus: good service but needs help with marketing

    return min(score, 100)


def search_google_places(category: str, keyword: str) -> List[Dict]:
    """Search Google Places API for businesses in a category"""

    if GOOGLE_PLACES_API_KEY == 'YOUR_API_KEY_HERE':
        print("⚠️  No Google Places API key set. Using mock data for development.")
        return _generate_mock_data(category, keyword)

    params = {
        'location': f"{ST_PETE_LAT},{ST_PETE_LNG}",
        'radius': SEARCH_RADIUS,
        'keyword': keyword,
        'key': GOOGLE_PLACES_API_KEY
    }

    try:
        response = requests.get(GOOGLE_PLACES_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for place in data.get('results', []):
            # Get detailed info
            details = get_place_details(place['place_id'])

            business = {
                'name': place.get('name'),
                'address': place.get('vicinity'),
                'lat': place['geometry']['location']['lat'],
                'lng': place['geometry']['location']['lng'],
                'rating': place.get('rating', 0),
                'review_count': place.get('user_ratings_total', 0),
                'category': category,
                'is_premium_category': CATEGORIES[category]['premium'],
                'place_id': place['place_id'],
                'website': details.get('website'),
                'phone': details.get('formatted_phone_number'),
                'hours': details.get('opening_hours', {}).get('weekday_text', []),
                'photos': place.get('photos', [])
            }

            results.append(business)
            time.sleep(0.2)  # Rate limiting

        return results

    except Exception as e:
        print(f"❌ Error searching Google Places: {e}")
        return []


def get_place_details(place_id: str) -> Dict:
    """Get detailed information about a place"""

    if GOOGLE_PLACES_API_KEY == 'YOUR_API_KEY_HERE':
        return {}

    params = {
        'place_id': place_id,
        'fields': 'name,website,formatted_phone_number,opening_hours',
        'key': GOOGLE_PLACES_API_KEY
    }

    try:
        response = requests.get(GOOGLE_PLACES_DETAILS_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('result', {})
    except Exception as e:
        print(f"❌ Error getting place details: {e}")
        return {}


def _generate_mock_data(category: str, keyword: str) -> List[Dict]:
    """Generate mock data for development/testing"""

    mock_businesses = [
        {
            'name': f"Joe's {keyword.title()} Service",
            'address': '123 Central Ave, St. Petersburg, FL',
            'lat': 27.7676,
            'lng': -82.6403,
            'rating': 4.8,
            'review_count': 47,
            'category': category,
            'is_premium_category': CATEGORIES[category]['premium'],
            'place_id': 'mock_001',
            'website': None,  # High-value target!
            'phone': '(727) 555-0101',
            'hours': ['Monday: 8:00 AM – 5:00 PM', 'Tuesday: 8:00 AM – 5:00 PM'],
            'photos': []
        },
        {
            'name': f"ABC {keyword.title()} Co",
            'address': '456 1st Ave N, St. Petersburg, FL',
            'lat': 27.7710,
            'lng': -82.6380,
            'rating': 4.5,
            'review_count': 23,
            'category': category,
            'is_premium_category': CATEGORIES[category]['premium'],
            'place_id': 'mock_002',
            'website': 'http://abc-example.com',
            'phone': '(727) 555-0102',
            'hours': ['Monday: 7:00 AM – 6:00 PM', 'Tuesday: 7:00 AM – 6:00 PM'],
            'photos': []
        },
        {
            'name': f"Premium {keyword.title()} Experts",
            'address': '789 Beach Dr, St. Petersburg, FL',
            'lat': 27.7642,
            'lng': -82.6289,
            'rating': 4.9,
            'review_count': 89,
            'category': category,
            'is_premium_category': CATEGORIES[category]['premium'],
            'place_id': 'mock_003',
            'website': None,  # High-value target!
            'phone': '(727) 555-0103',
            'hours': ['Monday: 9:00 AM – 5:00 PM', 'Tuesday: 9:00 AM – 5:00 PM'],
            'photos': []
        }
    ]

    return mock_businesses


def save_to_database(businesses: List[Dict]):
    """Save scraped businesses to database"""

    db = sqlite3.connect('soulfra.db')
    cursor = db.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT UNIQUE,
            business_name TEXT NOT NULL,
            category TEXT NOT NULL,
            address TEXT,
            lat REAL,
            lng REAL,
            phone TEXT,
            website TEXT,
            rating REAL,
            review_count INTEGER,
            is_premium_category INTEGER,
            score INTEGER,
            sales_status TEXT DEFAULT 'not_contacted',
            airtable_id TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            contacted_at TIMESTAMP,
            notes TEXT
        )
    ''')

    saved_count = 0
    for business in businesses:
        score = calculate_business_score(business)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO scraped_prospects (
                    place_id, business_name, category, address, lat, lng,
                    phone, website, rating, review_count, is_premium_category, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                business['place_id'],
                business['name'],
                business['category'],
                business['address'],
                business['lat'],
                business['lng'],
                business.get('phone'),
                business.get('website') or None,
                business['rating'],
                business['review_count'],
                1 if business['is_premium_category'] else 0,
                score
            ))
            saved_count += 1
        except Exception as e:
            print(f"❌ Error saving {business['name']}: {e}")

    db.commit()
    db.close()

    print(f"✅ Saved {saved_count} businesses to database")
    return saved_count


def export_to_airtable(limit: int = 50):
    """Export top-scored prospects to Airtable"""

    if AIRTABLE_API_KEY == 'YOUR_AIRTABLE_KEY':
        print("⚠️  No Airtable API key set. Skipping export.")
        print("Set AIRTABLE_API_KEY and AIRTABLE_BASE_ID environment variables to enable.")
        return

    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Get top prospects not yet in Airtable
    prospects = cursor.execute('''
        SELECT * FROM scraped_prospects
        WHERE airtable_id IS NULL
        ORDER BY score DESC, review_count DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    if not prospects:
        print("✅ No new prospects to export")
        db.close()
        return

    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}'

    exported_count = 0
    for prospect in prospects:
        record = {
            'fields': {
                'Business Name': prospect['business_name'],
                'Category': prospect['category'].title(),
                'Address': prospect['address'],
                'Phone': prospect['phone'] or 'N/A',
                'Website': prospect['website'] or 'None',
                'Rating': prospect['rating'],
                'Review Count': prospect['review_count'],
                'Score': prospect['score'],
                'Status': 'Not Contacted',
                'Notes': f"Scraped from Google Places on {datetime.now().strftime('%Y-%m-%d')}"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=record)
            response.raise_for_status()
            airtable_id = response.json()['id']

            # Update database with Airtable ID
            cursor.execute(
                'UPDATE scraped_prospects SET airtable_id = ? WHERE id = ?',
                (airtable_id, prospect['id'])
            )
            db.commit()

            exported_count += 1
            print(f"✅ Exported: {prospect['business_name']} (Score: {prospect['score']})")

            time.sleep(0.2)  # Rate limiting

        except Exception as e:
            print(f"❌ Error exporting {prospect['business_name']}: {e}")

    db.close()
    print(f"\n✅ Exported {exported_count} prospects to Airtable")


def show_top_prospects(limit: int = 20):
    """Display top-scored prospects"""

    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    prospects = cursor.execute('''
        SELECT * FROM scraped_prospects
        ORDER BY score DESC, review_count DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    db.close()

    print(f"\n{'='*80}")
    print(f"TOP {limit} SALES PROSPECTS")
    print(f"{'='*80}\n")

    for i, p in enumerate(prospects, 1):
        website_status = "❌ NO WEBSITE" if not p['website'] else "✅ Has website"
        premium = "⭐ PREMIUM" if p['is_premium_category'] else ""

        print(f"{i}. {p['business_name']} (Score: {p['score']}/100) {premium}")
        print(f"   📍 {p['address']}")
        print(f"   ⭐ {p['rating']} stars ({p['review_count']} reviews)")
        print(f"   🌐 {website_status}")
        print(f"   ☎️  {p['phone'] or 'No phone'}")
        print(f"   📊 Status: {p['sales_status'].replace('_', ' ').title()}")
        print()


def main():
    parser = argparse.ArgumentParser(description='StPetePros Business Scraper')
    parser.add_argument('--category', help='Scrape specific category (e.g., plumbing)')
    parser.add_argument('--all-categories', action='store_true', help='Scrape all categories')
    parser.add_argument('--export-airtable', action='store_true', help='Export to Airtable')
    parser.add_argument('--show-top', type=int, help='Show top N prospects')

    args = parser.parse_args()

    if args.show_top:
        show_top_prospects(args.show_top)
        return

    if args.export_airtable:
        export_to_airtable()
        return

    # Scraping mode
    categories_to_scrape = []

    if args.all_categories:
        categories_to_scrape = list(CATEGORIES.keys())
    elif args.category:
        if args.category not in CATEGORIES:
            print(f"❌ Unknown category: {args.category}")
            print(f"Available: {', '.join(CATEGORIES.keys())}")
            return
        categories_to_scrape = [args.category]
    else:
        print("Usage:")
        print("  python3 stpetepros_scraper.py --category plumbing")
        print("  python3 stpetepros_scraper.py --all-categories")
        print("  python3 stpetepros_scraper.py --show-top 20")
        print("  python3 stpetepros_scraper.py --export-airtable")
        return

    # Run scraper
    total_saved = 0
    for category in categories_to_scrape:
        keyword = CATEGORIES[category]['keyword']
        print(f"\n🔍 Scraping {category} ({keyword})...")

        businesses = search_google_places(category, keyword)
        print(f"   Found {len(businesses)} businesses")

        if businesses:
            saved = save_to_database(businesses)
            total_saved += saved

        time.sleep(1)  # Be nice to the API

    print(f"\n✅ Total businesses saved: {total_saved}")
    print("\nNext steps:")
    print("  1. python3 stpetepros_scraper.py --show-top 20")
    print("  2. python3 stpetepros_scraper.py --export-airtable")


if __name__ == '__main__':
    main()

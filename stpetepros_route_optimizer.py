#!/usr/bin/env python3
"""
StPetePros Sales Route Optimizer
Generates optimized door-to-door sales routes using Google Maps Directions API

Usage:
    python3 stpetepros_route_optimizer.py --start "123 Main St, St. Petersburg, FL"
    python3 stpetepros_route_optimizer.py --start "Downtown St Pete" --top 15
"""

import os
import sqlite3
import requests
import json
from typing import List, Dict, Tuple
import argparse
from datetime import datetime

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'YOUR_API_KEY_HERE')
DIRECTIONS_API_URL = 'https://maps.googleapis.com/maps/api/directions/json'
GEOCODE_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'


def geocode_address(address: str) -> Tuple[float, float]:
    """Convert address to lat/lng coordinates"""

    if GOOGLE_MAPS_API_KEY == 'YOUR_API_KEY_HERE':
        # Mock geocoding for development
        return (27.7676, -82.6403)  # Downtown St Pete

    params = {
        'address': address,
        'key': GOOGLE_MAPS_API_KEY
    }

    try:
        response = requests.get(GEOCODE_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            location = data['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            print(f"❌ Could not geocode address: {address}")
            return (27.7676, -82.6403)  # Default to downtown

    except Exception as e:
        print(f"❌ Error geocoding: {e}")
        return (27.7676, -82.6403)


def get_top_prospects(limit: int = 20, category: str = None) -> List[Dict]:
    """Get top-scored prospects from database"""

    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    if category:
        prospects = cursor.execute('''
            SELECT * FROM scraped_prospects
            WHERE category = ? AND sales_status = 'not_contacted'
            ORDER BY score DESC, review_count DESC
            LIMIT ?
        ''', (category, limit)).fetchall()
    else:
        prospects = cursor.execute('''
            SELECT * FROM scraped_prospects
            WHERE sales_status = 'not_contacted'
            ORDER BY score DESC, review_count DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    db.close()

    return [dict(p) for p in prospects]


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate Haversine distance between two points (in km)"""

    from math import radians, cos, sin, asin, sqrt

    lon1, lat1, lon2, lat2 = map(radians, [lng1, lat1, lng2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c

    return km


def greedy_nearest_neighbor_route(start_lat: float, start_lng: float, prospects: List[Dict]) -> List[Dict]:
    """
    Greedy nearest-neighbor algorithm to optimize route
    Not perfect but good enough for sales routes
    """

    route = []
    remaining = prospects.copy()
    current_lat, current_lng = start_lat, start_lng

    while remaining:
        # Find nearest unvisited prospect
        nearest = min(
            remaining,
            key=lambda p: calculate_distance(current_lat, current_lng, p['lat'], p['lng'])
        )

        route.append(nearest)
        remaining.remove(nearest)
        current_lat, current_lng = nearest['lat'], nearest['lng']

    return route


def score_cluster_route(prospects: List[Dict], start_lat: float, start_lng: float) -> List[Dict]:
    """
    Alternative: Score-based clustering
    Prioritizes high-score businesses even if slightly farther
    """

    route = []
    remaining = prospects.copy()
    current_lat, current_lng = start_lat, start_lng

    while remaining:
        # Calculate combined score: business score - (distance penalty)
        scored = []
        for p in remaining:
            distance = calculate_distance(current_lat, current_lng, p['lat'], p['lng'])
            # Each km of distance = -5 points
            combined_score = p['score'] - (distance * 5)
            scored.append((combined_score, p))

        # Pick highest combined score
        best = max(scored, key=lambda x: x[0])
        route.append(best[1])
        remaining.remove(best[1])
        current_lat, current_lng = best[1]['lat'], best[1]['lng']

    return route


def calculate_total_route_distance(route: List[Dict], start_lat: float, start_lng: float) -> float:
    """Calculate total distance for entire route"""

    total = 0
    current_lat, current_lng = start_lat, start_lng

    for stop in route:
        distance = calculate_distance(current_lat, current_lng, stop['lat'], stop['lng'])
        total += distance
        current_lat, current_lng = stop['lat'], stop['lng']

    return total


def print_route(route: List[Dict], start_address: str, start_lat: float, start_lng: float):
    """Display optimized route"""

    total_distance = calculate_total_route_distance(route, start_lat, start_lng)

    print(f"\n{'='*80}")
    print(f"OPTIMIZED SALES ROUTE")
    print(f"{'='*80}\n")
    print(f"📍 Starting location: {start_address}")
    print(f"🎯 Total stops: {len(route)}")
    print(f"🚗 Total distance: {total_distance:.1f} km ({total_distance * 0.621371:.1f} miles)")
    print(f"⏱️  Estimated time: {len(route) * 20 + total_distance * 3:.0f} minutes")
    print(f"   (Assumes 20 min per stop + 3 min per km driving)\n")

    current_lat, current_lng = start_lat, start_lng

    for i, stop in enumerate(route, 1):
        distance = calculate_distance(current_lat, current_lng, stop['lat'], stop['lng'])

        print(f"{i}. {stop['business_name']} (Score: {stop['score']}/100)")
        print(f"   📍 {stop['address']}")
        print(f"   ⭐ {stop['rating']} stars ({stop['review_count']} reviews)")
        print(f"   🌐 {'❌ NO WEBSITE' if not stop['website'] else '✅ Has website'}")
        print(f"   📞 {stop['phone'] or 'No phone listed'}")
        print(f"   🚗 {distance:.1f} km from previous stop")
        print()

        current_lat, current_lng = stop['lat'], stop['lng']


def export_route_to_json(route: List[Dict], start_address: str, filename: str = None):
    """Export route to JSON for use in dashboard"""

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sales_route_{timestamp}.json"

    route_data = {
        'start_address': start_address,
        'created_at': datetime.now().isoformat(),
        'total_stops': len(route),
        'route': [
            {
                'order': i + 1,
                'business_name': stop['business_name'],
                'address': stop['address'],
                'phone': stop['phone'],
                'lat': stop['lat'],
                'lng': stop['lng'],
                'score': stop['score'],
                'rating': stop['rating'],
                'review_count': stop['review_count'],
                'website': stop['website'],
                'category': stop['category']
            }
            for i, stop in enumerate(route)
        ]
    }

    with open(filename, 'w') as f:
        json.dump(route_data, f, indent=2)

    print(f"\n✅ Route exported to: {filename}")
    return filename


def generate_google_maps_url(route: List[Dict], start_lat: float, start_lng: float) -> str:
    """Generate Google Maps URL with all waypoints"""

    # Google Maps URL has a limit, so we'll do first 10 stops
    waypoints = route[:10]

    url = f"https://www.google.com/maps/dir/{start_lat},{start_lng}"

    for stop in waypoints:
        url += f"/{stop['lat']},{stop['lng']}"

    print(f"\n📱 Google Maps URL (first 10 stops):")
    print(url)

    return url


def main():
    parser = argparse.ArgumentParser(description='StPetePros Sales Route Optimizer')
    parser.add_argument('--start', required=True, help='Starting address (e.g., "123 Main St, St. Petersburg, FL")')
    parser.add_argument('--top', type=int, default=15, help='Number of prospects to visit (default: 15)')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--algorithm', choices=['nearest', 'score'], default='score',
                       help='Route algorithm: nearest=closest first, score=prioritize high scores')
    parser.add_argument('--export', action='store_true', help='Export route to JSON file')

    args = parser.parse_args()

    # Geocode starting location
    print(f"🔍 Geocoding starting address: {args.start}")
    start_lat, start_lng = geocode_address(args.start)
    print(f"   📍 {start_lat}, {start_lng}\n")

    # Get top prospects
    print(f"📊 Loading top {args.top} prospects...")
    prospects = get_top_prospects(limit=args.top, category=args.category)

    if not prospects:
        print("❌ No prospects found in database!")
        print("Run the scraper first:")
        print("   python3 stpetepros_scraper.py --all-categories")
        return

    print(f"   Found {len(prospects)} prospects\n")

    # Optimize route
    print(f"🧮 Optimizing route using '{args.algorithm}' algorithm...")

    if args.algorithm == 'nearest':
        route = greedy_nearest_neighbor_route(start_lat, start_lng, prospects)
    else:
        route = score_cluster_route(prospects, start_lat, start_lng)

    # Display route
    print_route(route, args.start, start_lat, start_lng)

    # Generate Google Maps link
    generate_google_maps_url(route, start_lat, start_lng)

    # Export if requested
    if args.export:
        export_route_to_json(route, args.start)

    print("\n💡 Tips:")
    print("  • Print this route and check off businesses as you visit them")
    print("  • Bring flyers, business cards, and a tablet to show the platform")
    print("  • Target businesses with ❌ NO WEBSITE - easiest to convert")
    print("  • Ask for the owner/manager, not just whoever answers the door")
    print("  • Follow up with contacted_at timestamp in database\n")


if __name__ == '__main__':
    main()

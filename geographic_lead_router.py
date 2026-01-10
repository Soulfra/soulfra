#!/usr/bin/env python3
"""
Geographic Lead Router - Smart Location-Based Professional Matching

Ensures customers only see professionals within their service area.

Problem: Miami customer shouldn't get St Pete plumber (200+ miles away)
Solution: ZIP code distance calculation + service radius filtering

Example:
    Customer in Miami (33101)
    → Find professionals within 25 miles
    → Returns: Miami Plumbing Pros, South Beach Electrician
    → EXCLUDES: Tampa Electric (250 miles away)

Usage:
    from geographic_lead_router import find_nearby_professionals

    # Customer's ZIP
    pros = find_nearby_professionals('33101', trade='plumber', radius_miles=25)

    # Returns: [{'business_name': 'Miami Plumbing Pros', 'distance': 3.2, ...}]
"""

import sqlite3
import math
from typing import List, Dict, Optional, Tuple


# ============================================================================
# ZIP Code Coordinate Database (Florida Major Cities)
# ============================================================================

# In production, use full ZIP code database API or file
# For demo, we have major FL city ZIPs with lat/lon

ZIP_COORDINATES = {
    # Tampa Bay Area
    '33602': (27.9506, -82.4572),   # Tampa Downtown
    '33609': (27.9506, -82.5201),   # Tampa Westshore
    '33610': (28.0236, -82.4043),   # Tampa North
    '33701': (27.7676, -82.6403),   # St. Petersburg Downtown
    '33702': (27.7831, -82.6743),   # St. Pete North
    '33755': (27.9772, -82.7965),   # Clearwater
    '33756': (27.9806, -82.8001),   # Clearwater Beach

    # Miami Area
    '33101': (25.7743, -80.1937),   # Miami Downtown
    '33109': (25.7907, -80.1300),   # Miami Beach
    '33139': (25.7907, -80.1400),   # South Beach
    '33125': (25.7823, -80.2331),   # Miami West
    '33126': (25.7762, -80.2906),   # Miami Airport
    '33134': (25.7470, -80.2683),   # Coral Gables
    '33143': (25.7059, -80.3145),   # Kendall
    '33166': (25.8223, -80.2995),   # Miami Lakes

    # Orlando Area
    '32801': (28.5383, -81.3792),   # Orlando Downtown
    '32803': (28.5554, -81.3657),   # Orlando North
    '32805': (28.5050, -81.4011),   # Orlando West
    '32819': (28.4596, -81.4395),   # Orlando International Drive
    '34741': (28.3064, -81.4065),   # Kissimmee
    '34746': (28.2920, -81.4029),   # Kissimmee South

    # Jacksonville Area
    '32202': (30.3322, -81.6557),   # Jacksonville Downtown
    '32204': (30.3158, -81.6851),   # Jacksonville Riverside
    '32207': (30.2672, -81.6451),   # Jacksonville San Marco
    '32250': (30.2394, -81.3960),   # Jacksonville Beach
}


# ============================================================================
# Distance Calculation (Haversine Formula)
# ============================================================================

def calculate_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula

    Args:
        lat1, lon1: First coordinate (latitude, longitude)
        lat2, lon2: Second coordinate

    Returns:
        Distance in miles

    Formula:
        a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
        c = 2 ⋅ atan2( √a, √(1−a) )
        d = R ⋅ c

    Where φ is latitude, λ is longitude, R is earth's radius (3,959 miles)
    """

    # Earth's radius in miles
    R = 3959

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return distance


def get_zip_coordinates(zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Get latitude/longitude for a ZIP code

    Args:
        zip_code: 5-digit ZIP code

    Returns:
        (latitude, longitude) tuple or None if not found
    """

    # Clean ZIP (remove +4 if present)
    zip_code = zip_code.split('-')[0].strip()

    return ZIP_COORDINATES.get(zip_code)


def calculate_zip_distance(zip1: str, zip2: str) -> Optional[float]:
    """
    Calculate distance between two ZIP codes

    Args:
        zip1: First ZIP code
        zip2: Second ZIP code

    Returns:
        Distance in miles, or None if coordinates not found
    """

    coords1 = get_zip_coordinates(zip1)
    coords2 = get_zip_coordinates(zip2)

    if not coords1 or not coords2:
        return None

    return calculate_distance_miles(coords1[0], coords1[1], coords2[0], coords2[1])


# ============================================================================
# Professional Matching
# ============================================================================

def find_nearby_professionals(
    customer_zip: str,
    trade: Optional[str] = None,
    radius_miles: int = 25,
    limit: int = 10
) -> List[Dict]:
    """
    Find professionals near customer's location

    Args:
        customer_zip: Customer's ZIP code
        trade: Optional trade filter ('plumber', 'electrician', etc.)
        radius_miles: Maximum distance in miles (default: 25)
        limit: Max results to return

    Returns:
        List of professionals sorted by distance, with distance included

    Example:
        >>> pros = find_nearby_professionals('33101', trade='plumber', radius_miles=25)
        >>> for pro in pros:
        ...     print(f"{pro['business_name']} - {pro['distance']:.1f} miles")
        Miami Plumbing Pros - 2.3 miles
        South Beach Plumber - 5.7 miles
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get customer coordinates
    customer_coords = get_zip_coordinates(customer_zip)

    if not customer_coords:
        print(f"⚠️  ZIP code {customer_zip} not found in database")
        conn.close()
        return []

    # Build query
    query = '''
        SELECT
            id,
            business_name,
            subdomain,
            trade_category,
            trade_specialty,
            phone,
            email,
            address_city,
            address_state,
            address_zip,
            tier,
            primary_color
        FROM professional_profile
        WHERE address_zip IS NOT NULL
    '''

    params = []

    if trade:
        query += ' AND trade_category = ?'
        params.append(trade)

    query += ' ORDER BY business_name'

    professionals = cursor.execute(query, params).fetchall()

    # Convert to dicts
    column_names = [description[0] for description in cursor.description]
    professionals = [dict(zip(column_names, prof)) for prof in professionals]

    # Calculate distances and filter
    results = []

    for prof in professionals:
        prof_zip = prof['address_zip']
        prof_coords = get_zip_coordinates(prof_zip)

        if not prof_coords:
            continue

        distance = calculate_distance_miles(
            customer_coords[0], customer_coords[1],
            prof_coords[0], prof_coords[1]
        )

        if distance <= radius_miles:
            prof['distance'] = round(distance, 1)
            results.append(prof)

    # Sort by distance
    results.sort(key=lambda x: x['distance'])

    # Limit results
    results = results[:limit]

    conn.close()

    return results


def find_professional_service_area(professional_id: int, radius_miles: int = 25) -> List[str]:
    """
    Get list of ZIPs within professional's service area

    Args:
        professional_id: Professional's database ID
        radius_miles: Service radius

    Returns:
        List of ZIP codes within service area
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get professional location
    prof = cursor.execute(
        'SELECT address_zip FROM professional_profile WHERE id = ?',
        (professional_id,)
    ).fetchone()

    conn.close()

    if not prof or not prof[0]:
        return []

    prof_zip = prof[0]
    prof_coords = get_zip_coordinates(prof_zip)

    if not prof_coords:
        return []

    # Find all ZIPs within radius
    service_zips = []

    for zip_code, coords in ZIP_COORDINATES.items():
        distance = calculate_distance_miles(
            prof_coords[0], prof_coords[1],
            coords[0], coords[1]
        )

        if distance <= radius_miles:
            service_zips.append(zip_code)

    return service_zips


# ============================================================================
# Lead Routing Integration
# ============================================================================

def route_lead_to_professional(
    customer_zip: str,
    trade: str,
    preferred_tier: Optional[str] = None
) -> Optional[Dict]:
    """
    Smart lead routing - find best professional for customer

    Logic:
    1. Find professionals within 25 miles
    2. Filter by trade
    3. Prefer higher tiers (pro > free)
    4. Return closest match

    Args:
        customer_zip: Customer's location
        trade: Service needed ('plumber', 'electrician', etc.)
        preferred_tier: Optional tier preference

    Returns:
        Professional dict or None if no match
    """

    # Find nearby professionals
    nearby_pros = find_nearby_professionals(customer_zip, trade=trade, radius_miles=25)

    if not nearby_pros:
        # Expand radius to 50 miles
        nearby_pros = find_nearby_professionals(customer_zip, trade=trade, radius_miles=50)

    if not nearby_pros:
        return None

    # Filter by tier if specified
    if preferred_tier:
        tier_pros = [p for p in nearby_pros if p['tier'] == preferred_tier]
        if tier_pros:
            return tier_pros[0]

    # Prefer pro tier
    pro_tier_pros = [p for p in nearby_pros if p['tier'] == 'pro']
    if pro_tier_pros:
        return pro_tier_pros[0]

    # Return closest
    return nearby_pros[0]


def validate_lead_routing():
    """
    Test geographic routing with examples

    Validates that Miami customers don't see Tampa pros, etc.
    """

    print("🗺️  Geographic Lead Routing Validation\n")

    test_cases = [
        ('33101', 'plumber', 'Miami Downtown'),
        ('33701', 'electrician', 'St. Petersburg'),
        ('32801', 'hvac', 'Orlando Downtown'),
        ('33602', 'plumber', 'Tampa Downtown')
    ]

    for customer_zip, trade, location_name in test_cases:
        print(f"📍 Customer Location: {location_name} ({customer_zip})")
        print(f"   Looking for: {trade}")

        pros = find_nearby_professionals(customer_zip, trade=trade, radius_miles=25)

        if pros:
            print(f"   ✅ Found {len(pros)} professionals within 25 miles:")
            for pro in pros[:3]:
                print(f"      • {pro['business_name']} - {pro['distance']} miles ({pro['address_city']})")
        else:
            print(f"   ⚠️  No professionals found within 25 miles")

        # Check that distant pros are excluded
        all_pros = find_nearby_professionals(customer_zip, trade=trade, radius_miles=300)
        excluded_pros = [p for p in all_pros if p['distance'] > 25]

        if excluded_pros:
            print(f"   🚫 Correctly excluded {len(excluded_pros)} distant professionals:")
            for pro in excluded_pros[:2]:
                print(f"      • {pro['business_name']} - {pro['distance']} miles (too far)")

        print()


# ============================================================================
# Analytics & Reporting
# ============================================================================

def analyze_service_coverage():
    """
    Analyze how well professionals cover Florida geography
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    professionals = cursor.execute('''
        SELECT business_name, trade_category, address_city, address_zip
        FROM professional_profile
        WHERE address_zip IS NOT NULL
    ''').fetchall()

    conn.close()

    print("📊 Service Coverage Analysis\n")

    # Check coverage for each major ZIP
    test_zips = [
        ('33101', 'Miami'),
        ('33701', 'St. Petersburg'),
        ('32801', 'Orlando'),
        ('33602', 'Tampa')
    ]

    for test_zip, city_name in test_zips:
        nearby_pros = find_nearby_professionals(test_zip, radius_miles=25)

        print(f"📍 {city_name} ({test_zip})")
        print(f"   Professionals within 25 miles: {len(nearby_pros)}")

        # By trade
        trades = {}
        for pro in nearby_pros:
            trade = pro['trade_category']
            trades[trade] = trades.get(trade, 0) + 1

        for trade, count in sorted(trades.items()):
            trade_emoji = {
                'plumber': '🔧',
                'electrician': '⚡',
                'hvac': '❄️',
                'podcast': '🎙️'
            }.get(trade, '💼')
            print(f"   {trade_emoji} {trade}: {count}")

        print()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import sys

    if '--validate' in sys.argv:
        validate_lead_routing()

    elif '--coverage' in sys.argv:
        analyze_service_coverage()

    elif '--find' in sys.argv:
        # Find professionals near a ZIP
        if len(sys.argv) < 3:
            print("Usage: python3 geographic_lead_router.py --find <zip_code> [trade]")
            sys.exit(1)

        customer_zip = sys.argv[2]
        trade = sys.argv[3] if len(sys.argv) > 3 else None

        print(f"🔍 Finding professionals near {customer_zip}...\n")

        pros = find_nearby_professionals(customer_zip, trade=trade, radius_miles=25)

        if pros:
            for pro in pros:
                trade_emoji = {
                    'plumber': '🔧',
                    'electrician': '⚡',
                    'hvac': '❄️',
                    'podcast': '🎙️'
                }.get(pro['trade_category'], '💼')

                print(f"{trade_emoji} {pro['business_name']}")
                print(f"   📍 {pro['address_city']} | {pro['distance']} miles away")
                print(f"   📞 {pro['phone']}")
                print(f"   🌐 https://{pro['subdomain']}.cringeproof.com")
                print()
        else:
            print("❌ No professionals found within 25 miles")

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Geographic Lead Router - Smart Location-Based Matching             ║
║                                                                      ║
║  Ensures customers only see professionals within service area.      ║
║                                                                      ║
║  Miami customer → Miami pros only (not Tampa 250 miles away)       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python3 geographic_lead_router.py --validate       # Test routing logic
    python3 geographic_lead_router.py --coverage       # Analyze coverage
    python3 geographic_lead_router.py --find <zip>     # Find pros near ZIP

Examples:
    python3 geographic_lead_router.py --find 33101 plumber
    python3 geographic_lead_router.py --validate
""")

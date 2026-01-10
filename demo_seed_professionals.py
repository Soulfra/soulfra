#!/usr/bin/env python3
"""
Demo Professional Seeder - Create Test Profiles for Proof of Concept

Generates 10 fake professional profiles across Florida:
- Different trades (plumber, electrician, hvac, podcast, restaurant)
- Different cities (Tampa, Miami, Orlando, Jacksonville, St Pete)
- Realistic business names, license numbers, contact info
- Ready for metrics redistribution

Usage:
    python3 demo_seed_professionals.py

Creates:
    - 10 professional_profile records
    - Subdomains like joesplumbing.cringeproof.com
    - Service areas with ZIP codes
    - Ready for case study generation
"""

import sqlite3
from datetime import datetime, timedelta
import random


# ============================================================================
# Demo Professional Data
# ============================================================================

DEMO_PROFESSIONALS = [
    # Tampa Bay Area - Trade Professionals
    {
        'business_name': "Joe's Plumbing & Drain Services",
        'subdomain': 'joesplumbing',
        'trade_category': 'plumber',
        'trade_specialty': 'Residential & Emergency Plumbing',
        'tagline': '24/7 Emergency Plumbing Services in Tampa Bay',
        'bio': 'Licensed master plumber with 15 years experience. We fix leaky faucets, clogged drains, water heaters, and emergency plumbing issues.',

        'phone': '(813) 555-0101',
        'email': 'joe@joesplumbing.demo',
        'address_city': 'Tampa',
        'address_state': 'FL',
        'address_zip': '33602',

        'license_number': 'CFC1234567',
        'license_state': 'FL',
        'license_type': 'Master Plumber',

        'primary_color': '#0066CC',
        'accent_color': '#FF6600',
        'tier': 'pro',

        # Account age for metric weighting
        'created_days_ago': 180
    },

    {
        'business_name': 'Tampa Electric Services',
        'subdomain': 'tampaelectric',
        'trade_category': 'electrician',
        'trade_specialty': 'Residential & Commercial Electrical',
        'tagline': 'Licensed Electricians Serving Tampa Bay Since 2019',
        'bio': 'Full-service electrical contractor. Panel upgrades, wiring, lighting, emergency repairs. Licensed, bonded, insured.',

        'phone': '(813) 555-0202',
        'email': 'contact@tampaelectric.demo',
        'address_city': 'Tampa',
        'address_state': 'FL',
        'address_zip': '33609',

        'license_number': 'EC13000123',
        'license_state': 'FL',
        'license_type': 'Licensed Electrician',

        'primary_color': '#FFB800',
        'accent_color': '#1E3A8A',
        'tier': 'pro',
        'created_days_ago': 150
    },

    {
        'business_name': 'Cool Breeze HVAC',
        'subdomain': 'coolbreezehvac',
        'trade_category': 'hvac',
        'trade_specialty': 'AC Repair & Installation',
        'tagline': 'Beat the Florida Heat - Same Day Service Available',
        'bio': 'AC repair, installation, and maintenance. We service all major brands. Emergency service available 24/7.',

        'phone': '(813) 555-0303',
        'email': 'service@coolbreezehvac.demo',
        'address_city': 'St. Petersburg',
        'address_state': 'FL',
        'address_zip': '33701',

        'license_number': 'CAC1823456',
        'license_state': 'FL',
        'license_type': 'HVAC Contractor',

        'primary_color': '#00B4D8',
        'accent_color': '#E63946',
        'tier': 'pro',
        'created_days_ago': 120
    },

    # Miami Area - Trade Professionals
    {
        'business_name': 'Miami Plumbing Pros',
        'subdomain': 'miamiplumbingpros',
        'trade_category': 'plumber',
        'trade_specialty': 'Commercial & Residential',
        'tagline': 'Miami-Dade\'s Most Trusted Plumbers',
        'bio': 'Serving Miami-Dade County for over 20 years. Specialized in commercial plumbing, emergency repairs, and water heater installation.',

        'phone': '(305) 555-0404',
        'email': 'info@miamiplumbingpros.demo',
        'address_city': 'Miami',
        'address_state': 'FL',
        'address_zip': '33101',

        'license_number': 'CFC7654321',
        'license_state': 'FL',
        'license_type': 'Master Plumber',

        'primary_color': '#E63946',
        'accent_color': '#1D3557',
        'tier': 'pro',
        'created_days_ago': 200
    },

    {
        'business_name': 'South Beach Electrician',
        'subdomain': 'southbeachelectric',
        'trade_category': 'electrician',
        'trade_specialty': 'Luxury Residential & Condo',
        'tagline': 'High-End Electrical Services for South Beach',
        'bio': 'Specialized in luxury condos and high-rises. Smart home installation, lighting design, electrical upgrades.',

        'phone': '(305) 555-0505',
        'email': 'hello@southbeachelectric.demo',
        'address_city': 'Miami Beach',
        'address_state': 'FL',
        'address_zip': '33139',

        'license_number': 'EC13000789',
        'license_state': 'FL',
        'license_type': 'Licensed Electrician',

        'primary_color': '#06FFA5',
        'accent_color': '#FF006E',
        'tier': 'pro',
        'created_days_ago': 90
    },

    # Orlando Area
    {
        'business_name': 'Orlando HVAC Experts',
        'subdomain': 'orlandohvac',
        'trade_category': 'hvac',
        'trade_specialty': 'Residential AC & Heating',
        'tagline': 'Orlando\'s Premier HVAC Service Provider',
        'bio': 'Keeping Orlando homes comfortable since 2015. AC repair, heating services, duct cleaning, and energy-efficient upgrades.',

        'phone': '(407) 555-0606',
        'email': 'service@orlandohvac.demo',
        'address_city': 'Orlando',
        'address_state': 'FL',
        'address_zip': '32801',

        'license_number': 'CAC1829876',
        'license_state': 'FL',
        'license_type': 'HVAC Contractor',

        'primary_color': '#FF6D00',
        'accent_color': '#0077B6',
        'tier': 'pro',
        'created_days_ago': 160
    },

    {
        'business_name': 'Theme Park Plumber',
        'subdomain': 'themeparkplumber',
        'trade_category': 'plumber',
        'trade_specialty': 'Fast Response Plumbing',
        'tagline': 'Because Plumbing Emergencies Don\'t Wait',
        'bio': 'Serving the Orlando tourism district. Fast response times, upfront pricing, no surprises. Available 24/7.',

        'phone': '(407) 555-0707',
        'email': 'urgent@themeparkplumber.demo',
        'address_city': 'Kissimmee',
        'address_state': 'FL',
        'address_zip': '34741',

        'license_number': 'CFC9876543',
        'license_state': 'FL',
        'license_type': 'Master Plumber',

        'primary_color': '#3A86FF',
        'accent_color': '#FB5607',
        'tier': 'free',
        'created_days_ago': 60
    },

    # Creator/Content Profiles
    {
        'business_name': 'Tampa Tech Talk Podcast',
        'subdomain': 'tampatechtalk',
        'trade_category': 'podcast',
        'trade_specialty': 'Technology & Startups',
        'tagline': 'Weekly Conversations with Tampa Bay Tech Leaders',
        'bio': 'Interviewing founders, developers, and innovators in Tampa\'s growing tech scene. New episodes every Tuesday.',

        'phone': '(813) 555-0808',
        'email': 'host@tampatechtalk.demo',
        'address_city': 'Tampa',
        'address_state': 'FL',
        'address_zip': '33602',

        'license_number': None,
        'license_state': None,
        'license_type': None,

        'primary_color': '#8338EC',
        'accent_color': '#FF006E',
        'tier': 'pro',
        'created_days_ago': 100
    },

    {
        'business_name': 'Miami Food Review',
        'subdomain': 'miamifoodreview',
        'trade_category': 'blog',
        'trade_specialty': 'Restaurant Reviews & Food Culture',
        'tagline': 'Honest Reviews of Miami\'s Best (and Worst) Restaurants',
        'bio': 'Independent restaurant critic covering Miami-Dade dining scene. No sponsorships, just honest reviews.',

        'phone': '(305) 555-0909',
        'email': 'editor@miamifoodreview.demo',
        'address_city': 'Miami',
        'address_state': 'FL',
        'address_zip': '33101',

        'license_number': None,
        'license_state': None,
        'license_type': None,

        'primary_color': '#FF5A5F',
        'accent_color': '#00D9FF',
        'tier': 'pro',
        'created_days_ago': 140
    },

    {
        'business_name': 'Florida Lifestyle Channel',
        'subdomain': 'floridalifestyle',
        'trade_category': 'youtube',
        'trade_specialty': 'Travel & Lifestyle Vlogging',
        'tagline': 'Exploring the Best of the Sunshine State',
        'bio': 'YouTube channel featuring Florida travel, hidden gems, outdoor adventures, and local culture. 50K+ subscribers.',

        'phone': '(407) 555-1010',
        'email': 'collab@floridalifestyle.demo',
        'address_city': 'Orlando',
        'address_state': 'FL',
        'address_zip': '32801',

        'license_number': None,
        'license_state': None,
        'license_type': None,

        'primary_color': '#06FFA5',
        'accent_color': '#FFBE0B',
        'tier': 'pro',
        'created_days_ago': 110
    }
]


# ============================================================================
# Seed Functions
# ============================================================================

def seed_demo_professionals():
    """
    Seed database with demo professional profiles

    Creates 10 fake profiles ready for:
    - Metrics redistribution
    - Case study generation
    - Geographic routing testing
    - Investor demos
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("🌱 Seeding demo professional profiles...\n")

    # First, create a demo user account to own all profiles
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, display_name, is_admin, created_at)
            VALUES ('demo', 'demo@cringeproof.com', 'DEMO_HASH', 'Demo Account', 0, ?)
        ''', (datetime.now().isoformat(),))
        demo_user_id = cursor.lastrowid
        print(f"✅ Created demo user account (ID: {demo_user_id})")
    except sqlite3.IntegrityError:
        # Demo user already exists, fetch ID
        demo_user_id = cursor.execute(
            "SELECT id FROM users WHERE username = 'demo'"
        ).fetchone()[0]
        print(f"✅ Using existing demo user account (ID: {demo_user_id})")

    print("\n📝 Creating professional profiles:\n")

    created_count = 0

    for prof_data in DEMO_PROFESSIONALS:
        # Calculate created_at based on days ago
        created_at = datetime.now() - timedelta(days=prof_data['created_days_ago'])

        try:
            cursor.execute('''
                INSERT INTO professional_profile (
                    user_id,
                    business_name,
                    subdomain,
                    tagline,
                    bio,
                    trade_category,
                    trade_specialty,
                    phone,
                    email,
                    address_city,
                    address_state,
                    address_zip,
                    logo_url,
                    primary_color,
                    accent_color,
                    license_number,
                    license_state,
                    license_type,
                    license_verified,
                    license_verified_at,
                    tier,
                    subscription_status,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                demo_user_id,
                prof_data['business_name'],
                prof_data['subdomain'],
                prof_data['tagline'],
                prof_data['bio'],
                prof_data['trade_category'],
                prof_data['trade_specialty'],
                prof_data['phone'],
                prof_data['email'],
                prof_data['address_city'],
                prof_data['address_state'],
                prof_data['address_zip'],
                None,  # logo_url
                prof_data['primary_color'],
                prof_data['accent_color'],
                prof_data['license_number'],
                prof_data['license_state'],
                prof_data['license_type'],
                1 if prof_data['license_number'] else 0,  # license_verified
                created_at.isoformat() if prof_data['license_number'] else None,
                prof_data['tier'],
                'active',
                created_at.isoformat(),
                datetime.now().isoformat()
            ))

            professional_id = cursor.lastrowid

            # Trade emoji
            trade_emoji = {
                'plumber': '🔧',
                'electrician': '⚡',
                'hvac': '❄️',
                'podcast': '🎙️',
                'blog': '✍️',
                'youtube': '📹',
                'restaurant': '🍽️'
            }.get(prof_data['trade_category'], '💼')

            # Tier badge
            tier_badge = '👑' if prof_data['tier'] == 'pro' else '🆓'

            print(f"{trade_emoji} {tier_badge} {prof_data['business_name']:35} | {prof_data['address_city']:15} | {prof_data['subdomain']}.cringeproof.com")

            created_count += 1

        except sqlite3.IntegrityError as e:
            print(f"⚠️  Skipped {prof_data['business_name']} (already exists)")

    conn.commit()

    print(f"\n✅ Created {created_count} demo professional profiles!")

    # Show summary
    print("\n📊 Demo Profile Summary:\n")

    # Count by trade
    trade_counts = cursor.execute('''
        SELECT trade_category, COUNT(*) as count
        FROM professional_profile
        WHERE user_id = ?
        GROUP BY trade_category
    ''', (demo_user_id,)).fetchall()

    for trade, count in trade_counts:
        trade_emoji = {
            'plumber': '🔧',
            'electrician': '⚡',
            'hvac': '❄️',
            'podcast': '🎙️',
            'blog': '✍️',
            'youtube': '📹'
        }.get(trade, '💼')
        print(f"   {trade_emoji} {trade:15} | {count} profiles")

    # Count by city
    print("\n📍 Geographic Distribution:\n")
    city_counts = cursor.execute('''
        SELECT address_city, COUNT(*) as count
        FROM professional_profile
        WHERE user_id = ?
        GROUP BY address_city
    ''', (demo_user_id,)).fetchall()

    for city, count in city_counts:
        print(f"   📍 {city:15} | {count} profiles")

    # Count by tier
    print("\n💰 Tier Distribution:\n")
    tier_counts = cursor.execute('''
        SELECT tier, COUNT(*) as count
        FROM professional_profile
        WHERE user_id = ?
        GROUP BY tier
    ''', (demo_user_id,)).fetchall()

    for tier, count in tier_counts:
        tier_badge = '👑' if tier == 'pro' else '🆓'
        print(f"   {tier_badge} {tier:10} | {count} profiles")

    conn.close()

    print("\n🚀 Next Steps:")
    print("   1. Run: python3 metrics_redistributor.py")
    print("   2. Run: python3 case_study_generator.py")
    print("   3. Visit: http://localhost:5001/professionals/joesplumbing")
    print("   4. Visit: http://localhost:5001/case-studies/joes-plumbing-tampa")

    return created_count


# ============================================================================
# Cleanup Functions
# ============================================================================

def cleanup_demo_professionals():
    """
    Remove all demo professional profiles

    Use this to start fresh or clean up after testing
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get demo user ID
    demo_user = cursor.execute(
        "SELECT id FROM users WHERE username = 'demo'"
    ).fetchone()

    if not demo_user:
        print("⚠️  No demo user found - nothing to clean up")
        conn.close()
        return

    demo_user_id = demo_user[0]

    # Delete all associated data
    cursor.execute('DELETE FROM lead WHERE professional_id IN (SELECT id FROM professional_profile WHERE user_id = ?)', (demo_user_id,))
    cursor.execute('DELETE FROM pseo_landing_page WHERE professional_id IN (SELECT id FROM professional_profile WHERE user_id = ?)', (demo_user_id,))
    cursor.execute('DELETE FROM tutorial WHERE professional_id IN (SELECT id FROM professional_profile WHERE user_id = ?)', (demo_user_id,))
    cursor.execute('DELETE FROM professional_profile WHERE user_id = ?', (demo_user_id,))

    conn.commit()
    conn.close()

    print("✅ Cleaned up all demo professional data")


def show_demo_urls():
    """Show all demo professional URLs"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    demo_user = cursor.execute(
        "SELECT id FROM users WHERE username = 'demo'"
    ).fetchone()

    if not demo_user:
        print("⚠️  No demo professionals found. Run seed script first.")
        conn.close()
        return

    demo_user_id = demo_user[0]

    profiles = cursor.execute('''
        SELECT business_name, subdomain, trade_category, address_city, tier
        FROM professional_profile
        WHERE user_id = ?
        ORDER BY trade_category, address_city
    ''', (demo_user_id,)).fetchall()

    print("\n🔗 Demo Professional URLs:\n")

    for business_name, subdomain, trade, city, tier in profiles:
        trade_emoji = {
            'plumber': '🔧',
            'electrician': '⚡',
            'hvac': '❄️',
            'podcast': '🎙️',
            'blog': '✍️',
            'youtube': '📹'
        }.get(trade, '💼')

        tier_badge = '👑' if tier == 'pro' else '🆓'

        print(f"{trade_emoji} {tier_badge} {business_name:35}")
        print(f"   🌐 https://{subdomain}.cringeproof.com")
        print(f"   📍 {city}")
        print()

    conn.close()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import sys

    if '--cleanup' in sys.argv:
        print("🧹 Cleaning up demo data...\n")
        cleanup_demo_professionals()

    elif '--urls' in sys.argv:
        show_demo_urls()

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Demo Professional Seeder - Create Test Profiles for Proof          ║
║                                                                      ║
║  Creates 10 fake professional profiles across:                      ║
║  - Tampa Bay (plumber, electrician, HVAC)                          ║
║  - Miami (plumber, electrician)                                     ║
║  - Orlando (HVAC, plumber)                                          ║
║  - Creators (podcast, blog, YouTube)                                ║
║                                                                      ║
║  Ready for metrics redistribution and case study generation         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

        seed_demo_professionals()

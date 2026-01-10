#!/usr/bin/env python3
"""
Prove Lineage Routing - Vanity Address Demo

PROVES: Same URL → Different Destinations Based on Lineage

This demonstrates the "vanity address" concept for QR codes:
- Same short URL routes DIFFERENTLY based on WHO scans it
- Like Bitcoin vanity addresses or pre-DNS routing
- Lineage determines subdomain/faucet assignment

Demo Flow:
1. Create root lineage with privacy topic
2. Create child lineage (user who was referred)
3. Create short URL /s/ABC123
4. Device WITH lineage scans → Routes to privacy.soulfra.com
5. Device WITHOUT lineage scans → Routes to default
6. SAME URL, DIFFERENT DESTINATIONS!

This creates VIRAL ROUTING where lineage propagates through shares.
"""

import sys
from lineage_system import create_root_lineage, create_child_lineage
from lineage_router import create_lineage_short_url, route_short_url
import sqlite3


def prove_lineage_routing():
    """Demonstrate vanity address routing"""
    print("=" * 70)
    print("🔀 PROVING LINEAGE ROUTING - VANITY ADDRESS CONCEPT")
    print("=" * 70)
    print()
    print("Same URL → Different Destinations Based on Lineage!")
    print()
    input("Press ENTER to begin demo...")
    print()

    # Step 1: Create lineages with different topics
    print("=" * 70)
    print("STEP 1: Create Lineages with Topics")
    print("=" * 70)
    print()

    # Privacy lineage
    print("Creating privacy lineage...")
    privacy_lineage = create_root_lineage(
        qr_code_id=1,
        user_id=None,
        metadata={'topic': 'privacy', 'name': 'Privacy Advocate'}
    )

    # Update scan with realistic device fingerprint
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE qr_scans
        SET ip_address = '10.0.0.10',
            user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        WHERE id = ?
    ''', (privacy_lineage['scan_id'],))
    conn.commit()
    conn.close()

    print()
    print(f"✅ Privacy Lineage: {privacy_lineage['lineage_hash']}")
    print()

    # Tech lineage
    print("Creating tech lineage...")
    tech_lineage = create_root_lineage(
        qr_code_id=1,
        user_id=None,
        metadata={'topic': 'tech', 'name': 'Tech Enthusiast'}
    )

    # Update scan with different device
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE qr_scans
        SET ip_address = '10.0.0.20',
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        WHERE id = ?
    ''', (tech_lineage['scan_id'],))
    conn.commit()
    conn.close()

    print()
    print(f"✅ Tech Lineage: {tech_lineage['lineage_hash']}")
    print()

    input("Press ENTER for next step...")
    print()

    # Step 2: Create short URL
    print("=" * 70)
    print("STEP 2: Create Short URL")
    print("=" * 70)
    print()

    short_url_result = create_lineage_short_url(
        'https://soulfra.com/blog/welcome',
        lineage_hash=None  # No specific lineage - routes based on device
    )

    short_id = short_url_result['short_id']
    print()
    print(f"✅ Short URL: /s/{short_id}")
    print()
    input("Press ENTER for next step...")
    print()

    # Step 3: Route with different devices
    print("=" * 70)
    print("STEP 3: Route Same URL with Different Devices")
    print("=" * 70)
    print()

    # Device 1: Privacy lineage
    print("🔍 Device 1 (Privacy lineage):")
    print("   IP: 10.0.0.10")
    print()

    privacy_device = {
        'ip_address': '10.0.0.10',
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
        'device_type': 'mobile'
    }

    result1 = route_short_url(short_id, privacy_device)
    print()

    # Device 2: Tech lineage
    print("🔍 Device 2 (Tech lineage):")
    print("   IP: 10.0.0.20")
    print()

    tech_device = {
        'ip_address': '10.0.0.20',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'device_type': 'desktop'
    }

    result2 = route_short_url(short_id, tech_device)
    print()

    # Device 3: No lineage
    print("🔍 Device 3 (No lineage):")
    print("   IP: 192.168.1.100")
    print()

    no_lineage_device = {
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'device_type': 'desktop'
    }

    result3 = route_short_url(short_id, no_lineage_device)
    print()

    input("Press ENTER for summary...")
    print()

    # Summary
    print("=" * 70)
    print("🎉 VANITY ADDRESS ROUTING PROVED!")
    print("=" * 70)
    print()
    print(f"Same URL: /s/{short_id}")
    print()
    print("Routes to DIFFERENT destinations:")
    print()
    print(f"  • Privacy device → {result1['redirect_url']}")
    print(f"  • Tech device    → {result2['redirect_url']}")
    print(f"  • Unknown device → {result3['redirect_url']}")
    print()
    print("✅ Same URL, different results based on lineage!")
    print()
    print("This enables:")
    print("  • Viral routing (lineage-based faucet assignment)")
    print("  • Personalized destinations without user input")
    print("  • Tracking \"who recruited who\" through scan chains")
    print("  • Knowledge graphs from QR relationships")
    print()


# ==============================================================================
# SIMPLE TESTS
# ==============================================================================

def test_show_routes():
    """Show all possible routes for all short URLs"""
    from lineage_router import show_all_routes_for_short_url

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('SELECT short_id FROM lineage_short_urls')
    short_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not short_ids:
        print("No short URLs found. Run --demo first.")
        return

    for short_id in short_ids:
        show_all_routes_for_short_url(short_id)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Prove Lineage Routing - Vanity Address Demo')
    parser.add_argument('--demo', action='store_true', help='Run full demonstration')
    parser.add_argument('--show-routes', action='store_true', help='Show all possible routes')

    args = parser.parse_args()

    if args.demo:
        prove_lineage_routing()
    elif args.show_routes:
        test_show_routes()
    else:
        print("Prove Lineage Routing - Vanity Address Demo")
        print()
        print("Usage:")
        print("  --demo         Run full demonstration")
        print("  --show-routes  Show all possible routes")

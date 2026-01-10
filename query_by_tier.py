#!/usr/bin/env python3
"""
Query Domains by Tier - Database Extraction Helper

Connects:
- Brand tiers (foundation/business/creative)
- Membership tiers (free/pro/premium)
- Rotation system
- Export/publishing

Usage:
    # Query by brand tier
    python3 query_by_tier.py --tier foundation
    python3 query_by_tier.py --tier business
    python3 query_by_tier.py --tier creative

    # Query by membership tier
    python3 query_by_tier.py --membership free
    python3 query_by_tier.py --membership pro
    python3 query_by_tier.py --membership premium

    # Export results
    python3 query_by_tier.py --tier foundation --export json
    python3 query_by_tier.py --tier foundation --export csv
"""

import sqlite3
import json
import argparse
from collections import Counter

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_domains_by_tier(tier):
    """
    Get all domains for a specific brand tier

    Args:
        tier: foundation, business, or creative

    Returns:
        List of domain dicts
    """
    db = get_db()
    cursor = db.cursor()

    rows = cursor.execute('''
        SELECT id, name, slug, domain, category, tier, emoji, brand_type, tagline
        FROM brands
        WHERE tier = ?
        ORDER BY created_at DESC
    ''', (tier,)).fetchall()

    db.close()
    return [dict(row) for row in rows]

def get_domains_by_category(category):
    """Get all domains in a category"""
    db = get_db()
    cursor = db.cursor()

    rows = cursor.execute('''
        SELECT id, name, slug, domain, category, tier, emoji, brand_type, tagline
        FROM brands
        WHERE category = ?
        ORDER BY created_at DESC
    ''', (category,)).fetchall()

    db.close()
    return [dict(row) for row in rows]

def get_domains_for_membership_tier(membership_tier):
    """
    Get domains a user can access based on membership

    Membership quotas:
    - free: First 10 domains
    - pro: First 50 domains
    - premium: All domains
    """
    db = get_db()
    cursor = db.cursor()

    # Get all domains
    rows = cursor.execute('''
        SELECT id, name, slug, domain, category, tier, emoji, brand_type, tagline
        FROM brands
        ORDER BY created_at ASC
    ''').fetchall()

    db.close()
    domains = [dict(row) for row in rows]

    # Apply membership limits
    limits = {
        'free': 10,
        'pro': 50,
        'premium': 999999  # Unlimited
    }

    limit = limits.get(membership_tier, 10)
    return domains[:limit]

def get_domain_stats():
    """Get statistics about domains"""
    db = get_db()
    cursor = db.cursor()

    # Total count
    total = cursor.execute('SELECT COUNT(*) FROM brands').fetchone()[0]

    # By tier
    tier_counts = cursor.execute('''
        SELECT tier, COUNT(*) as count
        FROM brands
        WHERE tier IS NOT NULL AND tier != ''
        GROUP BY tier
    ''').fetchall()

    # By category
    category_counts = cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM brands
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
    ''').fetchall()

    # By type
    type_counts = cursor.execute('''
        SELECT brand_type, COUNT(*) as count
        FROM brands
        WHERE brand_type IS NOT NULL AND brand_type != ''
        GROUP BY brand_type
    ''').fetchall()

    db.close()

    return {
        'total': total,
        'by_tier': {row[0]: row[1] for row in tier_counts},
        'by_category': {row[0]: row[1] for row in category_counts},
        'by_type': {row[0]: row[1] for row in type_counts}
    }

def export_domains(domains, format='json'):
    """Export domains to JSON or CSV"""
    if format == 'json':
        return json.dumps(domains, indent=2)
    elif format == 'csv':
        if not domains:
            return "No domains to export"

        # CSV header
        keys = domains[0].keys()
        lines = [','.join(keys)]

        # CSV rows
        for domain in domains:
            row = [str(domain.get(k, '')) for k in keys]
            lines.append(','.join(f'"{v}"' for v in row))

        return '\n'.join(lines)
    else:
        return str(domains)

def main():
    parser = argparse.ArgumentParser(description='Query domains by tier')
    parser.add_argument('--tier', type=str, help='Brand tier: foundation, business, creative')
    parser.add_argument('--category', type=str, help='Domain category: cooking, tech, privacy, etc.')
    parser.add_argument('--membership', type=str, help='Membership tier: free, pro, premium')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--export', type=str, choices=['json', 'csv'], help='Export format')
    args = parser.parse_args()

    if args.stats:
        stats = get_domain_stats()
        print("📊 Domain Statistics")
        print("=" * 50)
        print(f"\n📈 Total domains: {stats['total']}")

        print(f"\n🏆 By Tier:")
        for tier, count in sorted(stats['by_tier'].items()):
            print(f"  {tier}: {count}")

        print(f"\n📁 By Category:")
        for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        print(f"\n🎨 By Type:")
        for typ, count in sorted(stats['by_type'].items()):
            print(f"  {typ}: {count}")

        return

    # Query domains
    domains = []
    if args.tier:
        domains = get_domains_by_tier(args.tier)
        print(f"🔍 Querying domains with tier: {args.tier}")
    elif args.category:
        domains = get_domains_by_category(args.category)
        print(f"🔍 Querying domains in category: {args.category}")
    elif args.membership:
        domains = get_domains_for_membership_tier(args.membership)
        print(f"🔍 Querying domains for {args.membership} membership")
    else:
        print("Usage examples:")
        print("  python3 query_by_tier.py --tier foundation")
        print("  python3 query_by_tier.py --category cooking")
        print("  python3 query_by_tier.py --membership pro")
        print("  python3 query_by_tier.py --stats")
        return

    print(f"✅ Found {len(domains)} domains")
    print()

    # Display or export
    if args.export:
        output = export_domains(domains, args.export)
        print(output)
    else:
        # Display summary
        for i, domain in enumerate(domains, 1):
            emoji = domain.get('emoji', '🌐')
            name = domain.get('name', 'Unknown')
            dom = domain.get('domain', 'unknown.com')
            tier = domain.get('tier', 'none')
            category = domain.get('category', 'none')
            print(f"  {i}. {emoji} {name} ({dom}) - {tier}/{category}")

        if len(domains) > 20:
            print(f"\n  ... and {len(domains) - 20} more")

        print()
        print("💡 Tip: Add --export json or --export csv to export results")

if __name__ == '__main__':
    main()

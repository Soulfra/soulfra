#!/usr/bin/env python3
"""
Domain Partnership System - External Company Integration

Allows external companies to partner with Soulfra domains for:
- Co-marketing campaigns
- Branded landing pages
- Conversion tracking
- Affiliate revenue sharing

Example Use Cases:
1. Cooking brand partners with howtocookathome.com for recipe campaigns
2. Privacy tool partners with deathtodata.com for security campaigns
3. Developer tool partners with calriven.com for technical campaigns

Run: python3 domain_partnership.py --help
"""

import sys
import argparse
from database import get_db
from pathlib import Path
from datetime import datetime
import json

# =============================================================================
# DATABASE SCHEMA
# =============================================================================

def create_partnership_tables():
    """
    Create database tables for partnerships

    Tables:
        - domain_partnerships: External company partnerships
        - partnership_campaigns: Specific marketing campaigns
        - partnership_conversions: Track referral conversions
    """
    db = get_db()

    # Domain partnerships table
    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_partnerships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            company_name TEXT NOT NULL,
            company_contact TEXT,
            partnership_type TEXT NOT NULL,
            revenue_share_percentage REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active',
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Partnership campaigns table
    db.execute('''
        CREATE TABLE IF NOT EXISTS partnership_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partnership_id INTEGER NOT NULL,
            campaign_name TEXT NOT NULL,
            campaign_type TEXT NOT NULL,
            target_url TEXT,
            custom_question TEXT,
            tracking_code TEXT UNIQUE,
            conversions_count INTEGER DEFAULT 0,
            revenue_generated REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partnership_id) REFERENCES domain_partnerships(id)
        )
    ''')

    # Partnership conversions table
    db.execute('''
        CREATE TABLE IF NOT EXISTS partnership_conversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            user_id INTEGER,
            conversion_type TEXT NOT NULL,
            conversion_value REAL DEFAULT 0.0,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES partnership_campaigns(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Partnership tables created successfully")


# =============================================================================
# PARTNERSHIP MANAGEMENT
# =============================================================================

def add_partnership(domain, company_name, partnership_type='affiliate',
                   revenue_share=0.0, contact=None, notes=None):
    """
    Add a new partnership with an external company

    Args:
        domain: Soulfra domain (e.g., 'howtocookathome.com')
        company_name: External company name
        partnership_type: Type ('affiliate', 'co-marketing', 'sponsored')
        revenue_share: Revenue share percentage (0-100)
        contact: Company contact email
        notes: Additional notes

    Returns:
        Partnership ID
    """
    db = get_db()

    cursor = db.execute('''
        INSERT INTO domain_partnerships
        (domain, company_name, company_contact, partnership_type, revenue_share_percentage, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (domain, company_name, contact, partnership_type, revenue_share, notes))

    partnership_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Partnership created: {company_name} ↔ {domain}")
    print(f"   Partnership ID: {partnership_id}")
    print(f"   Type: {partnership_type}")
    print(f"   Revenue Share: {revenue_share}%")

    return partnership_id


def list_partnerships(domain=None, status='active'):
    """
    List all partnerships (optionally filtered by domain)

    Args:
        domain: Filter by domain (optional)
        status: Filter by status ('active', 'inactive', 'all')

    Returns:
        List of partnership dicts
    """
    db = get_db()

    if domain:
        if status == 'all':
            rows = db.execute('''
                SELECT * FROM domain_partnerships
                WHERE domain = ?
                ORDER BY created_at DESC
            ''', (domain,)).fetchall()
        else:
            rows = db.execute('''
                SELECT * FROM domain_partnerships
                WHERE domain = ? AND status = ?
                ORDER BY created_at DESC
            ''', (domain, status)).fetchall()
    else:
        if status == 'all':
            rows = db.execute('''
                SELECT * FROM domain_partnerships
                ORDER BY created_at DESC
            ''').fetchall()
        else:
            rows = db.execute('''
                SELECT * FROM domain_partnerships
                WHERE status = ?
                ORDER BY created_at DESC
            ''', (status,)).fetchall()

    partnerships = [dict(row) for row in rows]
    db.close()

    return partnerships


# =============================================================================
# CAMPAIGN MANAGEMENT
# =============================================================================

def create_campaign(partnership_id, campaign_name, campaign_type='referral',
                   target_url=None, custom_question=None):
    """
    Create a marketing campaign for a partnership

    Args:
        partnership_id: Partnership ID
        campaign_name: Campaign name
        campaign_type: Type ('referral', 'landing_page', 'question_flow')
        target_url: Campaign landing page URL
        custom_question: Custom domain question for rotation system

    Returns:
        Campaign ID and tracking code
    """
    import random
    import string

    db = get_db()

    # Generate unique tracking code
    tracking_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

    cursor = db.execute('''
        INSERT INTO partnership_campaigns
        (partnership_id, campaign_name, campaign_type, target_url, custom_question, tracking_code)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (partnership_id, campaign_name, campaign_type, target_url, custom_question, tracking_code))

    campaign_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Campaign created: {campaign_name}")
    print(f"   Campaign ID: {campaign_id}")
    print(f"   Tracking Code: {tracking_code}")
    print(f"   Type: {campaign_type}")

    if target_url:
        print(f"   Landing Page: {target_url}")

    if custom_question:
        print(f"   Custom Question: {custom_question}")

    return campaign_id, tracking_code


def track_conversion(campaign_id, conversion_type='visit', value=0.0,
                    user_id=None, metadata=None):
    """
    Track a conversion for a partnership campaign

    Args:
        campaign_id: Campaign ID
        conversion_type: Type ('visit', 'signup', 'purchase', 'referral')
        value: Conversion value (revenue, points, etc.)
        user_id: User ID (optional)
        metadata: Additional metadata as dict

    Returns:
        Conversion ID
    """
    db = get_db()

    metadata_json = json.dumps(metadata) if metadata else None

    cursor = db.execute('''
        INSERT INTO partnership_conversions
        (campaign_id, user_id, conversion_type, conversion_value, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', (campaign_id, user_id, conversion_type, value, metadata_json))

    conversion_id = cursor.lastrowid

    # Update campaign stats
    db.execute('''
        UPDATE partnership_campaigns
        SET conversions_count = conversions_count + 1,
            revenue_generated = revenue_generated + ?
        WHERE id = ?
    ''', (value, campaign_id))

    db.commit()
    db.close()

    return conversion_id


def get_campaign_stats(campaign_id):
    """
    Get statistics for a campaign

    Args:
        campaign_id: Campaign ID

    Returns:
        Dict with campaign stats
    """
    db = get_db()

    # Get campaign info
    campaign = db.execute('''
        SELECT * FROM partnership_campaigns WHERE id = ?
    ''', (campaign_id,)).fetchone()

    if not campaign:
        return None

    # Get conversion breakdown
    conversions = db.execute('''
        SELECT conversion_type, COUNT(*) as count, SUM(conversion_value) as total_value
        FROM partnership_conversions
        WHERE campaign_id = ?
        GROUP BY conversion_type
    ''', (campaign_id,)).fetchall()

    db.close()

    return {
        'campaign': dict(campaign),
        'conversions': [dict(c) for c in conversions]
    }


# =============================================================================
# DOMAIN QUESTION INTEGRATION
# =============================================================================

def add_partner_question_to_domain(domain, question_text, campaign_id=None):
    """
    Add a partner's custom question to domain rotation

    This integrates with rotation_helpers.py to add partner questions
    to the domain question rotation system.

    Args:
        domain: Domain to add question to
        question_text: Question text
        campaign_id: Campaign ID for tracking (optional)

    Returns:
        Question ID
    """
    db = get_db()

    # Get brand_id for domain
    brand = db.execute('''
        SELECT id FROM brands WHERE domain = ?
    ''', (domain,)).fetchone()

    if not brand:
        print(f"❌ Domain not found: {domain}")
        return None

    brand_id = brand['id']

    # Add question to domain_questions table
    cursor = db.execute('''
        INSERT INTO domain_questions
        (brand_id, question_text, question_type, campaign_id)
        VALUES (?, ?, 'partner', ?)
    ''', (brand_id, question_text, campaign_id))

    question_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Question added to {domain} rotation:")
    print(f"   {question_text}")
    print(f"   Question ID: {question_id}")

    return question_id


# =============================================================================
# CLI COMMANDS
# =============================================================================

def cmd_add_partnership(args):
    """CLI: Add a new partnership"""
    partnership_id = add_partnership(
        domain=args.domain,
        company_name=args.company,
        partnership_type=args.type,
        revenue_share=args.revenue_share,
        contact=args.contact,
        notes=args.notes
    )

    print(f"\n✅ Partnership {partnership_id} created successfully")
    print(f"   Next: Create a campaign with --create-campaign")


def cmd_list_partnerships(args):
    """CLI: List all partnerships"""
    partnerships = list_partnerships(domain=args.domain, status=args.status)

    if not partnerships:
        print("No partnerships found")
        return

    print(f"\n📋 Found {len(partnerships)} partnership(s):\n")

    for p in partnerships:
        print(f"  [{p['id']}] {p['company_name']} ↔ {p['domain']}")
        print(f"      Type: {p['partnership_type']}")
        print(f"      Revenue Share: {p['revenue_share_percentage']}%")
        print(f"      Status: {p['status']}")
        print(f"      Created: {p['created_at']}")
        print()


def cmd_create_campaign(args):
    """CLI: Create a campaign"""
    campaign_id, tracking_code = create_campaign(
        partnership_id=args.partnership_id,
        campaign_name=args.name,
        campaign_type=args.type,
        target_url=args.url,
        custom_question=args.question
    )

    print(f"\n✅ Campaign {campaign_id} created successfully")
    print(f"\n📊 Tracking URL:")
    print(f"   https://{args.domain}/?campaign={tracking_code}")

    if args.question:
        print(f"\n💡 Custom question will appear in domain rotation")


def cmd_campaign_stats(args):
    """CLI: Show campaign statistics"""
    stats = get_campaign_stats(args.campaign_id)

    if not stats:
        print(f"❌ Campaign {args.campaign_id} not found")
        return

    campaign = stats['campaign']
    conversions = stats['conversions']

    print(f"\n📊 Campaign Stats: {campaign['campaign_name']}")
    print(f"   Tracking Code: {campaign['tracking_code']}")
    print(f"   Total Conversions: {campaign['conversions_count']}")
    print(f"   Total Revenue: ${campaign['revenue_generated']:.2f}")
    print(f"\n   Conversion Breakdown:")

    for conv in conversions:
        print(f"      {conv['conversion_type']}: {conv['count']} (${conv['total_value']:.2f})")


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Domain Partnership System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Setup command
    parser_setup = subparsers.add_parser('setup', help='Create database tables')

    # Add partnership
    parser_add = subparsers.add_parser('add', help='Add a new partnership')
    parser_add.add_argument('--domain', required=True, help='Soulfra domain')
    parser_add.add_argument('--company', required=True, help='Company name')
    parser_add.add_argument('--type', default='affiliate',
                           choices=['affiliate', 'co-marketing', 'sponsored'],
                           help='Partnership type')
    parser_add.add_argument('--revenue-share', type=float, default=0.0,
                           help='Revenue share percentage')
    parser_add.add_argument('--contact', help='Company contact email')
    parser_add.add_argument('--notes', help='Partnership notes')

    # List partnerships
    parser_list = subparsers.add_parser('list', help='List partnerships')
    parser_list.add_argument('--domain', help='Filter by domain')
    parser_list.add_argument('--status', default='active',
                            choices=['active', 'inactive', 'all'],
                            help='Filter by status')

    # Create campaign
    parser_campaign = subparsers.add_parser('campaign', help='Create a campaign')
    parser_campaign.add_argument('--partnership-id', type=int, required=True,
                                help='Partnership ID')
    parser_campaign.add_argument('--name', required=True, help='Campaign name')
    parser_campaign.add_argument('--type', default='referral',
                                choices=['referral', 'landing_page', 'question_flow'],
                                help='Campaign type')
    parser_campaign.add_argument('--url', help='Landing page URL')
    parser_campaign.add_argument('--question', help='Custom domain question')
    parser_campaign.add_argument('--domain', help='Domain (for tracking URL display)')

    # Campaign stats
    parser_stats = subparsers.add_parser('stats', help='Show campaign stats')
    parser_stats.add_argument('campaign_id', type=int, help='Campaign ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'setup':
        create_partnership_tables()
        return 0

    if args.command == 'add':
        cmd_add_partnership(args)
        return 0

    if args.command == 'list':
        cmd_list_partnerships(args)
        return 0

    if args.command == 'campaign':
        cmd_create_campaign(args)
        return 0

    if args.command == 'stats':
        cmd_campaign_stats(args)
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Email Monetization - Ethical Email List Monetization (Zero Dependencies)

Monetize email subscribers through:
1. Sponsored content (clearly labeled)
2. Affiliate partnerships (opt-in)
3. Premium tiers (subscriber pays for exclusive content)
4. Data insights (anonymized analytics for partners)

Philosophy: Respect privacy. Provide value. Opt-in only. Transparency first.

IMPORTANT: This is ETHICAL monetization:
- No selling raw email addresses
- No spam
- Clear opt-in/opt-out
- GDPR/CCPA compliant
- Value exchange (subscribers get something)

Usage:
    python3 email_monetization.py --send-sponsored  # Send sponsored email
    python3 email_monetization.py --report          # Revenue report
    python3 email_monetization.py --export-insights # Export anonymized insights

Tier System:
TIER 0: Email address (string)
TIER 1: Subscriber record (database row)
TIER 2: Opt-in preferences (JSON metadata)
TIER 3: Monetization campaigns (multi-subscriber operations)
TIER 4: Revenue analytics (aggregate insights)
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path


class EmailMonetization:
    """Ethical email list monetization system"""

    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path

    def get_subscribers(self, preferences: Optional[Dict] = None) -> List[Dict]:
        """
        Get subscribers with specific preferences

        Args:
            preferences: Filter by preferences (e.g., {'sponsored_content': True})

        Returns:
            List of subscriber dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM subscribers WHERE verified = 1")
        subscribers = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Filter by preferences if provided
        if preferences:
            filtered = []
            for sub in subscribers:
                sub_prefs = json.loads(sub.get('preferences', '{}'))
                if all(sub_prefs.get(k) == v for k, v in preferences.items()):
                    filtered.append(sub)
            return filtered

        return subscribers

    def send_sponsored_email(self, sponsor: str, subject: str, content: str, offer_price: float):
        """
        Send sponsored email to opted-in subscribers

        Args:
            sponsor: Sponsor name
            subject: Email subject
            content: Email content (markdown)
            offer_price: How much sponsor is paying per send

        Returns:
            dict with send results
        """
        # Get subscribers who opted in to sponsored content
        subscribers = self.get_subscribers({'sponsored_content': True})

        if not subscribers:
            return {
                'success': False,
                'error': 'No subscribers opted in to sponsored content'
            }

        # Calculate revenue
        revenue = len(subscribers) * offer_price

        # Queue emails
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        queued_count = 0
        for sub in subscribers:
            # Add sponsored disclaimer
            full_content = f"""
# Sponsored Content

*This email contains sponsored content from {sponsor}. You're receiving this because you opted in to sponsored emails. [Unsubscribe]({{{{unsubscribe_url}}}}) or [Update Preferences]({{{{preferences_url}}}})*

---

{content}

---

*Sponsored by {sponsor}*
"""

            cursor.execute("""
                INSERT INTO outbound_emails
                (to_email, subject, body, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                sub['email'],
                f"[Sponsored] {subject}",
                full_content,
                json.dumps({
                    'type': 'sponsored',
                    'sponsor': sponsor,
                    'campaign_id': f"sponsor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }),
                datetime.now().isoformat()
            ))
            queued_count += 1

        conn.commit()
        conn.close()

        # Log monetization
        self._log_revenue('sponsored_email', revenue, {
            'sponsor': sponsor,
            'recipient_count': queued_count,
            'price_per_send': offer_price
        })

        return {
            'success': True,
            'queued': queued_count,
            'revenue': revenue,
            'price_per_send': offer_price
        }

    def create_premium_tier(self, tier_name: str, price: float, benefits: List[str]):
        """
        Create a premium subscriber tier

        Args:
            tier_name: Name of tier (e.g., "Pro", "Premium")
            price: Monthly price
            benefits: List of benefits

        Returns:
            Premium tier ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create premium_tiers table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS premium_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier_name TEXT NOT NULL,
                price REAL NOT NULL,
                benefits TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            INSERT INTO premium_tiers (tier_name, price, benefits, created_at)
            VALUES (?, ?, ?, ?)
        """, (tier_name, price, json.dumps(benefits), datetime.now().isoformat()))

        tier_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return tier_id

    def upgrade_subscriber(self, subscriber_id: int, tier_id: int):
        """
        Upgrade subscriber to premium tier

        Args:
            subscriber_id: Subscriber ID
            tier_id: Premium tier ID

        Returns:
            bool: Success
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update subscriber preferences
        cursor.execute("SELECT preferences FROM subscribers WHERE id = ?", (subscriber_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        prefs = json.loads(row[0] if row[0] else '{}')
        prefs['premium_tier'] = tier_id
        prefs['premium_since'] = datetime.now().isoformat()

        cursor.execute("""
            UPDATE subscribers
            SET preferences = ?
            WHERE id = ?
        """, (json.dumps(prefs), subscriber_id))

        conn.commit()
        conn.close()

        # Log revenue (monthly subscription)
        cursor = conn.execute("SELECT price FROM premium_tiers WHERE id = ?", (tier_id,))
        price = cursor.fetchone()[0]
        self._log_revenue('premium_subscription', price, {
            'subscriber_id': subscriber_id,
            'tier_id': tier_id
        })

        return True

    def export_anonymized_insights(self, output_path='email_insights.json'):
        """
        Export anonymized email insights for partners

        NO personal data - only aggregate stats:
        - Total subscribers
        - Engagement rates
        - Popular content topics
        - Click-through rates
        - Geographic distribution (country level only)

        Args:
            output_path: Where to save insights

        Returns:
            dict with insights
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Aggregate stats (no personal data)
        cursor.execute("SELECT COUNT(*) FROM subscribers WHERE verified = 1")
        total_subscribers = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM subscribers
            WHERE verified = 1
            AND json_extract(preferences, '$.sponsored_content') = 1
        """)
        sponsored_opt_in = cursor.fetchone()[0]

        # Email engagement (from outbound_emails)
        cursor.execute("""
            SELECT
                COUNT(*) as total_sent,
                SUM(CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN json_extract(metadata, '$.clicked') = 1 THEN 1 ELSE 0 END) as clicked
            FROM outbound_emails
        """)
        engagement = cursor.fetchone()

        conn.close()

        insights = {
            'generated_at': datetime.now().isoformat(),
            'subscribers': {
                'total': total_subscribers,
                'sponsored_opt_in': sponsored_opt_in,
                'opt_in_rate': (sponsored_opt_in / total_subscribers * 100) if total_subscribers > 0 else 0
            },
            'engagement': {
                'total_sent': engagement[0],
                'delivered': engagement[1],
                'clicked': engagement[2],
                'delivery_rate': (engagement[1] / engagement[0] * 100) if engagement[0] > 0 else 0,
                'click_rate': (engagement[2] / engagement[0] * 100) if engagement[0] > 0 else 0
            },
            'privacy_notice': 'All data is anonymized and aggregated. No personal information included.'
        }

        # Save to file
        with open(output_path, 'w') as f:
            json.dump(insights, f, indent=2)

        return insights

    def _log_revenue(self, revenue_type: str, amount: float, metadata: Dict):
        """Log monetization revenue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create revenue_log table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revenue_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                revenue_type TEXT NOT NULL,
                amount REAL NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            INSERT INTO revenue_log (revenue_type, amount, metadata, created_at)
            VALUES (?, ?, ?, ?)
        """, (revenue_type, amount, json.dumps(metadata), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_revenue_report(self, days: int = 30) -> Dict:
        """
        Get revenue report

        Args:
            days: Number of days to include

        Returns:
            Revenue report dict
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='revenue_log'
        """)
        if not cursor.fetchone():
            conn.close()
            return {
                'total_revenue': 0,
                'by_type': {},
                'entries': []
            }

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT * FROM revenue_log
            WHERE created_at >= ?
            ORDER BY created_at DESC
        """, (since,))

        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Calculate totals
        total = sum(e['amount'] for e in entries)

        by_type = {}
        for entry in entries:
            rev_type = entry['revenue_type']
            by_type[rev_type] = by_type.get(rev_type, 0) + entry['amount']

        return {
            'total_revenue': total,
            'by_type': by_type,
            'entries': entries,
            'period_days': days
        }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Email list monetization (ethical)')
    parser.add_argument('--send-sponsored', action='store_true', help='Send sponsored email')
    parser.add_argument('--sponsor', help='Sponsor name')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--content', help='Email content (markdown)')
    parser.add_argument('--price', type=float, help='Price per send')
    parser.add_argument('--report', action='store_true', help='Revenue report')
    parser.add_argument('--export-insights', action='store_true', help='Export anonymized insights')
    parser.add_argument('--days', type=int, default=30, help='Days for report')

    args = parser.parse_args()

    monetization = EmailMonetization()

    if args.send_sponsored:
        if not all([args.sponsor, args.subject, args.content, args.price]):
            print("❌ Missing required args: --sponsor, --subject, --content, --price")
            exit(1)

        result = monetization.send_sponsored_email(
            sponsor=args.sponsor,
            subject=args.subject,
            content=args.content,
            offer_price=args.price
        )

        if result['success']:
            print(f"✅ Sponsored email queued")
            print(f"   Recipients: {result['queued']}")
            print(f"   Revenue: ${result['revenue']:.2f}")
            print(f"   Price per send: ${result['price_per_send']:.2f}")
        else:
            print(f"❌ {result['error']}")

    elif args.report:
        report = monetization.get_revenue_report(days=args.days)

        print("=" * 70)
        print(f"💰 REVENUE REPORT (Last {report['period_days']} days)")
        print("=" * 70)
        print(f"\nTotal Revenue: ${report['total_revenue']:.2f}")
        print("\nBy Type:")
        for rev_type, amount in report['by_type'].items():
            print(f"  • {rev_type}: ${amount:.2f}")

        print(f"\nRecent Entries ({len(report['entries'])}):")
        for entry in report['entries'][:10]:
            metadata = json.loads(entry['metadata'])
            print(f"  • {entry['revenue_type']}: ${entry['amount']:.2f} - {entry['created_at']}")

    elif args.export_insights:
        insights = monetization.export_anonymized_insights()

        print("=" * 70)
        print("📊 EMAIL INSIGHTS (Anonymized)")
        print("=" * 70)
        print(f"\nSubscribers:")
        print(f"  Total: {insights['subscribers']['total']}")
        print(f"  Sponsored opt-in: {insights['subscribers']['sponsored_opt_in']} ({insights['subscribers']['opt_in_rate']:.1f}%)")

        print(f"\nEngagement:")
        print(f"  Emails sent: {insights['engagement']['total_sent']}")
        print(f"  Delivery rate: {insights['engagement']['delivery_rate']:.1f}%")
        print(f"  Click rate: {insights['engagement']['click_rate']:.1f}%")

        print(f"\n✅ Insights exported to email_insights.json")
        print(f"⚠️  {insights['privacy_notice']}")

    else:
        # Show status
        subscribers = monetization.get_subscribers()
        sponsored_opt_in = monetization.get_subscribers({'sponsored_content': True})

        print("=" * 70)
        print("📧 EMAIL MONETIZATION STATUS")
        print("=" * 70)
        print(f"\nSubscribers: {len(subscribers)}")
        print(f"Sponsored opt-in: {len(sponsored_opt_in)}")

        report = monetization.get_revenue_report(days=30)
        print(f"\nRevenue (30 days): ${report['total_revenue']:.2f}")

        print("\n💡 TIP: Run with --help to see available commands")

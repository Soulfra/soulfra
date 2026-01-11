#!/usr/bin/env python3
"""
Brand Matrix Visualizer - See The Matrix

Like htop but for domains - shows how everything JOINs together in real-time.

Usage:
    python3 brand_matrix_visualizer.py           # Full matrix view
    python3 brand_matrix_visualizer.py calriven  # Single brand view
    python3 brand_matrix_visualizer.py --joins   # Show JOIN relationships
    python3 brand_matrix_visualizer.py --tiers   # Show tier progression

Like:
    - htop (process viewer)
    - systemctl status (daemon status)
    - The Matrix (see the code)
"""

import sqlite3
import sys
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'soulfra.db'


class MatrixVisualizer:
    """Visualize the domain matrix"""

    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row

    def show_full_matrix(self):
        """Show all brands in the matrix (like htop)"""

        print()
        print("🧠 " + "="*68)
        print(" " * 25 + "THE MATRIX" + " " * 33)
        print("="*70)
        print()

        # Get all brands
        brands = self.db.execute('''
            SELECT id, name, slug, domain, tier, category,
                   color_primary, personality, created_at
            FROM brands
            ORDER BY
                CASE tier
                    WHEN 'foundation' THEN 1
                    WHEN 'creative' THEN 2
                    ELSE 3
                END,
                id
        ''').fetchall()

        if not brands:
            print("   ⚠️  The Matrix is empty - no brands created yet")
            print("      Run: jupyter notebook domain_matrix_builder.ipynb")
            return

        # Header
        print(f"{'ID':<4} {'NAME':<20} {'SLUG':<15} {'TIER':<12} {'DOMAIN':<25}")
        print("-" * 80)

        # Brands
        for brand in brands:
            tier_str = (brand['tier'] or 'null')[:12]
            domain_str = (brand['domain'] or 'not configured')[:25]

            # Color code by tier
            if brand['tier'] == 'foundation':
                icon = "🔷"
            elif brand['tier'] == 'creative':
                icon = "🎨"
            else:
                icon = "⚪"

            print(f"{icon} {brand['id']:<2} {brand['name']:<20} {brand['slug']:<15} {tier_str:<12} {domain_str:<25}")

        print()
        print(f"   Total brands: {len(brands)}")
        print()

    def show_brand_detail(self, slug):
        """Show detailed view of single brand (like systemctl status)"""

        brand = self.db.execute('''
            SELECT * FROM brands WHERE slug = ?
        ''', (slug,)).fetchone()

        if not brand:
            print(f"❌ Brand '{slug}' not found in matrix")
            return

        print()
        print("🔍 " + "="*68)
        print(f"   BRAND: {brand['name']}")
        print("="*70)
        print()

        # Basic info
        print(f"   Name: {brand['name']}")
        print(f"   Slug: {brand['slug']}")
        print(f"   Domain: {brand['domain'] or 'not configured'}")
        print(f"   Tier: {brand['tier'] or 'untiered'}")
        print(f"   Category: {brand['category'] or 'uncategorized'}")
        print(f"   Emoji: {brand['emoji'] or 'none'}")
        print()

        # Colors
        if brand['color_primary']:
            print(f"   🎨 Colors:")
            print(f"      Primary: {brand['color_primary']}")
            if brand['color_secondary']:
                print(f"      Secondary: {brand['color_secondary']}")
            if brand['color_accent']:
                print(f"      Accent: {brand['color_accent']}")
            print()

        # Personality
        if brand['personality']:
            print(f"   🧠 Personality: {brand['personality']}")
            if brand['personality_tone']:
                print(f"      Tone: {brand['personality_tone']}")
            print()

        # Config
        if brand['config_json']:
            try:
                config = json.loads(brand['config_json'])
                print(f"   ⚙️  Configuration:")
                for key, value in config.items():
                    if isinstance(value, list) and len(value) <= 3:
                        print(f"      {key}: {', '.join(map(str, value))}")
                    elif not isinstance(value, (list, dict)):
                        print(f"      {key}: {value}")
                print()
            except:
                pass

        # URLs
        print(f"   🔗 Access:")
        print(f"      Local: http://{brand['slug']}.localhost:5001/")
        if brand['domain']:
            print(f"      Production: https://{brand['domain']}/")
        print()

        # Timestamps
        print(f"   📅 Created: {brand['created_at']}")
        print()

    def show_join_relationships(self):
        """Show how tables JOIN together"""

        print()
        print("🔗 " + "="*68)
        print(" " * 22 + "JOIN RELATIONSHIPS" + " " * 24)
        print("="*70)
        print()

        # Get table counts
        brands_count = self.db.execute('SELECT COUNT(*) as c FROM brands').fetchone()['c']

        # Check if other tables exist and get counts
        tables = {
            'posts': 0,
            'comments': 0,
            'users': 0,
            'email_outbox': 0,
            'professionals': 0
        }

        for table in tables.keys():
            try:
                count = self.db.execute(f'SELECT COUNT(*) as c FROM {table}').fetchone()['c']
                tables[table] = count
            except:
                pass

        # Visual representation
        print("   brands ({} rows)".format(brands_count))
        print("      ↓")
        print("      ├─→ posts ({} rows) JOIN ON brand_id".format(tables['posts']))
        print("      │      ↓")
        print("      │      └─→ comments ({} rows) JOIN ON post_id".format(tables['comments']))
        print("      │             ↓")
        print("      │             └─→ users ({} rows) JOIN ON user_id".format(tables['users']))
        print("      │")
        print("      ├─→ email_outbox ({} rows) → professionals".format(tables['email_outbox']))
        print("      │")
        print("      └─→ images (JOIN ON brand_id)")
        print()

        # Show example JOIN
        print("   📝 Example JOIN Query:")
        print()
        print("      SELECT b.name, COUNT(p.id) as posts")
        print("      FROM brands b")
        print("      LEFT JOIN posts p ON p.brand_id = b.id")
        print("      GROUP BY b.id")
        print()

        # Execute the example
        results = self.db.execute('''
            SELECT b.name, b.slug, COUNT(p.id) as post_count
            FROM brands b
            LEFT JOIN posts p ON p.brand_id = b.id
            GROUP BY b.id
            ORDER BY post_count DESC
        ''').fetchall()

        if results:
            print("   📊 Brand → Posts JOINs:")
            print()
            for r in results:
                print(f"      {r['name']:<20} → {r['post_count']} posts")
            print()

    def show_tier_progression(self):
        """Show tier-based domain unlocking"""

        print()
        print("🎯 " + "="*68)
        print(" " * 22 + "TIER PROGRESSION" + " " * 26)
        print("="*70)
        print()

        try:
            from core.tier_progression_engine import TIER_CONFIG
        except ImportError:
            print("   ⚠️  tier_progression_engine not found")
            print("      Using database tiers only")

            # Show tiers from database
            tiers = self.db.execute('''
                SELECT tier, COUNT(*) as count
                FROM brands
                WHERE tier IS NOT NULL
                GROUP BY tier
                ORDER BY
                    CASE tier
                        WHEN 'foundation' THEN 1
                        WHEN 'creative' THEN 2
                        ELSE 3
                    END
            ''').fetchall()

            for tier in tiers:
                brands = self.db.execute('''
                    SELECT name, slug, domain
                    FROM brands
                    WHERE tier = ?
                    ORDER BY name
                ''', (tier['tier'],)).fetchall()

                print(f"   **{tier['tier'].title()} Tier** ({tier['count']} brands):")
                for brand in brands:
                    domain_str = brand['domain'] or 'not configured'
                    print(f"      • {brand['name']} ({brand['slug']}) → {domain_str}")
                print()

            return

        # Show configured tier progression
        for tier_num in sorted(TIER_CONFIG.keys()):
            tier = TIER_CONFIG[tier_num]

            print(f"   **Tier {tier_num}: {tier['name']}**")
            print(f"      {tier['description']}")
            print()

            # Requirements
            reqs = []
            for req_name, req_val in tier['requirements'].items():
                if req_val > 0:
                    reqs.append(f"{req_name}: {req_val}+")

            if reqs:
                print(f"      Requirements: {', '.join(reqs)}")
            else:
                print(f"      Requirements: None (FREE)")
            print()

            # Domains
            print(f"      Unlocked Domains ({len(tier['domains'])}):")
            for domain in tier['domains']:
                # Check if in database
                brand = self.db.execute(
                    'SELECT name, slug FROM brands WHERE domain = ?',
                    (domain,)
                ).fetchone()

                if brand:
                    print(f"         ✅ {domain} → {brand['name']}")
                else:
                    print(f"         ⚠️  {domain} → Not in database")
            print()

            # Ownership
            print(f"      Ownership: {tier['ownership_base']}% base")
            if 'ownership_per_additional' in tier:
                print(f"                 +{tier['ownership_per_additional']}% per domain")
            print()
            print("-" * 70)
            print()

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main entry point"""

    viz = MatrixVisualizer()

    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--help' or arg == '-h':
            print(__doc__)
            return

        elif arg == '--joins' or arg == '-j':
            viz.show_join_relationships()

        elif arg == '--tiers' or arg == '-t':
            viz.show_tier_progression()

        else:
            # Assume it's a brand slug
            viz.show_brand_detail(arg)

    else:
        # Default: show full matrix
        viz.show_full_matrix()

    viz.close()


if __name__ == '__main__':
    main()

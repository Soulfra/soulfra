#!/usr/bin/env python3
"""
Brand Evolution Migration - Self-Evolving Ecosystem Tables

This migration enables the competitive multi-agent brand system where:
- Brands compete for territory (like War/Catan/Monopoly)
- Users contribute to brands and earn soul tokens
- System self-evolves through continuous learning
- Neural networks improve from user feedback

Philosophy:
----------
Instead of manually wiring everything, we create a self-reinforcing loop:
1. Better AI → More accurate scoring
2. Better scoring → Better contributions
3. Better contributions → Better training data
4. Better training data → Better AI (LOOP)

Plus competitive dynamics:
- Strong brands attract aligned users
- More users → More contributions
- More contributions → More territory
- More territory → Higher visibility
- Higher visibility → MORE users (POSITIVE FEEDBACK)

Tables Created:
--------------
1. brand_territory - Competitive scores and rankings
2. user_brand_loyalty - User-brand relationships with soul tokens
3. brand_evolution_log - History of brand changes
4. contribution_scores - AI evaluation of contributions

Usage:
    python3 migrate_brand_evolution.py
"""

import sqlite3
from datetime import datetime

def migrate():
    """Create all brand evolution tables"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("🧬 BRAND EVOLUTION MIGRATION")
    print("=" * 70)
    print()

    # Table 1: Brand Territory Tracking
    print("Creating brand_territory table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brand_territory (
            brand_id INTEGER PRIMARY KEY,
            total_engagement INTEGER DEFAULT 0,
            territory_score REAL DEFAULT 0.0,
            rank INTEGER DEFAULT 0,
            active_contributors INTEGER DEFAULT 0,
            avg_contribution_quality REAL DEFAULT 0.0,
            total_tokens_distributed INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')
    print("  ✅ brand_territory created")

    # Table 2: User-Brand Loyalty Relationships
    print("Creating user_brand_loyalty table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_brand_loyalty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand_id INTEGER NOT NULL,
            soul_tokens INTEGER DEFAULT 0,
            contribution_count INTEGER DEFAULT 0,
            total_contribution_score REAL DEFAULT 0.0,
            steering_power REAL DEFAULT 0.0,
            last_contribution_at TIMESTAMP,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (brand_id) REFERENCES brands(id),
            UNIQUE(user_id, brand_id)
        )
    ''')
    print("  ✅ user_brand_loyalty created")

    # Table 3: Brand Evolution History
    print("Creating brand_evolution_log table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brand_evolution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_description TEXT,
            old_value TEXT,
            new_value TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')
    print("  ✅ brand_evolution_log created")

    # Table 4: Contribution Quality Scores
    print("Creating contribution_scores table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contribution_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contribution_id INTEGER NOT NULL,
            contribution_type TEXT NOT NULL,
            brand_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            on_brand_score REAL NOT NULL,
            quality_score REAL DEFAULT 0.0,
            accepted BOOLEAN DEFAULT 0,
            tokens_awarded INTEGER DEFAULT 0,
            evaluator_model TEXT,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("  ✅ contribution_scores created")

    # Index for fast queries
    print("Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_territory_rank ON brand_territory(rank)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loyalty_user ON user_brand_loyalty(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loyalty_brand ON user_brand_loyalty(brand_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contribution_scores_brand ON contribution_scores(brand_id)')
    print("  ✅ Indexes created")

    # Initialize territory for existing brands
    print()
    print("Initializing territory for existing brands...")
    cursor.execute('''
        INSERT OR IGNORE INTO brand_territory (brand_id, territory_score, rank)
        SELECT id, 0.0, 0 FROM brands
    ''')

    brands_initialized = cursor.rowcount
    print(f"  ✅ Initialized {brands_initialized} brands")

    conn.commit()
    conn.close()

    print()
    print("=" * 70)
    print("🎉 BRAND EVOLUTION MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    print("What you can now do:")
    print("  1. Users can contribute to brands and earn soul tokens")
    print("  2. Brands compete for territory based on engagement")
    print("  3. Neural networks learn from every contribution")
    print("  4. System self-evolves through the feedback loop")
    print()
    print("Next Steps:")
    print("  → Build contribution_validator.py (real-time scoring)")
    print("  → Add brand selector to comment forms")
    print("  → Create /brand-arena leaderboard")
    print("  → Award initial tokens to seed the economy")
    print("  → Build brand_evolution_engine.py (self-evolution loop)")
    print()


def show_stats():
    """Show current brand ecosystem stats"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("📊 BRAND ECOSYSTEM STATS")
    print("=" * 70)
    print()

    # Count brands
    cursor.execute('SELECT COUNT(*) FROM brands')
    brand_count = cursor.fetchone()[0]
    print(f"Total Brands: {brand_count}")

    # Count brands with territory
    cursor.execute('SELECT COUNT(*) FROM brand_territory WHERE territory_score > 0')
    active_brands = cursor.fetchone()[0]
    print(f"Active Brands: {active_brands}")

    # Count user loyalties
    cursor.execute('SELECT COUNT(*) FROM user_brand_loyalty')
    loyalty_count = cursor.fetchone()[0]
    print(f"User-Brand Loyalties: {loyalty_count}")

    # Total tokens distributed
    cursor.execute('SELECT COALESCE(SUM(soul_tokens), 0) FROM user_brand_loyalty')
    total_tokens = cursor.fetchone()[0]
    print(f"Total Soul Tokens: {total_tokens}")

    # Total contributions scored
    cursor.execute('SELECT COUNT(*) FROM contribution_scores')
    contributions = cursor.fetchone()[0]
    print(f"Contributions Scored: {contributions}")

    print()

    # Show top brands if any have territory
    if active_brands > 0:
        print("Top Brands by Territory:")
        cursor.execute('''
            SELECT b.name, bt.territory_score, bt.rank
            FROM brand_territory bt
            JOIN brands b ON bt.brand_id = b.id
            WHERE bt.territory_score > 0
            ORDER BY bt.rank ASC
            LIMIT 5
        ''')

        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row[0]}: {row[1]:.1f} points (Rank #{row[2]})")

    conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        show_stats()
    else:
        migrate()
        print("Run with --stats to see ecosystem statistics")

#!/usr/bin/env python3
"""
Blog Network Migration Script

Adds tables and columns to support:
- Domain hierarchy and relationships
- Cross-posting/syndication between domains
- Network-wide content sharing
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'soulfra.db')


def migrate():
    """Run all blog network migrations"""
    conn = sqlite3.connect(DB_PATH)

    print("🔄 Migrating database for blog network...")

    # 1. Add parent_domain column to brands table
    try:
        conn.execute('ALTER TABLE brands ADD COLUMN parent_domain TEXT')
        print("✅ Added parent_domain column to brands table")
    except sqlite3.OperationalError:
        print("ℹ️  parent_domain column already exists")

    # 2. Add network_role column to brands table
    try:
        conn.execute("ALTER TABLE brands ADD COLUMN network_role TEXT DEFAULT 'member'")
        print("✅ Added network_role column to brands table")
    except sqlite3.OperationalError:
        print("ℹ️  network_role column already exists")

    # 3. Create domain_relationships table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS domain_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_domain TEXT NOT NULL,
            child_domain TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(parent_domain, child_domain)
        )
    ''')
    print("✅ Created domain_relationships table")

    # 4. Create network_posts table for cross-posting/syndication
    conn.execute('''
        CREATE TABLE IF NOT EXISTS network_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            source_domain TEXT NOT NULL,
            syndicated_domains TEXT,
            network_tags TEXT,
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    ''')
    print("✅ Created network_posts table")

    # 5. Create domain_files table for file browser
    conn.execute('''
        CREATE TABLE IF NOT EXISTS domain_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER,
            content TEXT,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            UNIQUE(domain, file_path)
        )
    ''')
    print("✅ Created domain_files table")

    # 6. Add indexes for performance
    conn.execute('CREATE INDEX IF NOT EXISTS idx_domain_relationships_parent ON domain_relationships(parent_domain)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_domain_relationships_child ON domain_relationships(child_domain)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_network_posts_post_id ON network_posts(post_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_network_posts_source ON network_posts(source_domain)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_domain_files_domain ON domain_files(domain)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_domain_files_type ON domain_files(file_type)')
    print("✅ Created indexes")

    # 7. Set up default network hierarchy (soulfra as hub)
    try:
        conn.execute("UPDATE brands SET network_role = 'hub' WHERE slug = 'soulfra'")
        print("✅ Set soulfra as network hub")
    except:
        pass

    # 8. Create default relationships (all domains link to soulfra)
    domains = conn.execute("SELECT domain FROM brands WHERE domain IS NOT NULL AND domain != ''").fetchall()
    for (domain,) in domains:
        if domain and 'soulfra' not in domain.lower():
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO domain_relationships (parent_domain, child_domain, relationship_type)
                    VALUES ('soulfra.com', ?, 'network_member')
                ''', (domain,))
            except:
                pass
    print("✅ Created default network relationships")

    conn.commit()
    conn.close()

    print("\n🎉 Blog network migration complete!")
    print("\nNew tables:")
    print("  - domain_relationships: Tracks network hierarchy")
    print("  - network_posts: Tracks cross-posted content")
    print("  - domain_files: Tracks files for file browser")
    print("\nNew columns:")
    print("  - brands.parent_domain: Parent domain in hierarchy")
    print("  - brands.network_role: hub/member/satellite")


if __name__ == '__main__':
    migrate()

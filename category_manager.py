#!/usr/bin/env python3
"""
Category Manager - Expandable Categories & Silos

Provides functions to work with the dynamic categories system.
Supports multiple categories per professional and domain-specific category sets.

Usage:
    from category_manager import CategoryManager

    cm = CategoryManager()
    categories = cm.get_categories_for_domain('stpetepros')
    silos = cm.get_silos_for_domain('stpetepros')
"""

from database import get_db
from typing import List, Dict, Optional


class CategoryManager:
    """Manager for dynamic categories and silos"""

    def __init__(self):
        """Initialize category manager"""
        pass

    def get_categories_for_domain(self, domain_slug: str, silo_type: Optional[str] = None) -> List[Dict]:
        """
        Get all categories for a domain

        Args:
            domain_slug: Domain slug (e.g. 'stpetepros')
            silo_type: Optional filter by silo type (e.g. 'professionals')

        Returns:
            List of category dicts
        """
        db = get_db()

        if silo_type:
            categories = db.execute('''
                SELECT * FROM categories
                WHERE domain_slug = ? AND silo_type = ? AND is_active = 1
                ORDER BY sort_order, name
            ''', (domain_slug, silo_type)).fetchall()
        else:
            categories = db.execute('''
                SELECT * FROM categories
                WHERE domain_slug = ? AND is_active = 1
                ORDER BY sort_order, name
            ''', (domain_slug,)).fetchall()

        return [dict(cat) for cat in categories]

    def get_category(self, category_id: int) -> Optional[Dict]:
        """
        Get category by ID

        Args:
            category_id: Category ID

        Returns:
            Category dict or None
        """
        db = get_db()
        category = db.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
        return dict(category) if category else None

    def get_category_by_slug(self, slug: str, domain_slug: str) -> Optional[Dict]:
        """
        Get category by slug and domain

        Args:
            slug: Category slug
            domain_slug: Domain slug

        Returns:
            Category dict or None
        """
        db = get_db()
        category = db.execute('''
            SELECT * FROM categories
            WHERE slug = ? AND domain_slug = ?
        ''', (slug, domain_slug)).fetchone()
        return dict(category) if category else None

    def get_silos_for_domain(self, domain_slug: str) -> List[Dict]:
        """
        Get all silo types used in a domain

        Args:
            domain_slug: Domain slug

        Returns:
            List of silo type dicts with category counts
        """
        db = get_db()

        # Get distinct silo types for this domain
        silos = db.execute('''
            SELECT DISTINCT c.silo_type
            FROM categories c
            WHERE c.domain_slug = ? AND c.is_active = 1
        ''', (domain_slug,)).fetchall()

        result = []
        for silo in silos:
            silo_type = silo['silo_type']

            # Get silo info
            silo_info = db.execute('''
                SELECT * FROM silo_types WHERE slug = ?
            ''', (silo_type,)).fetchone()

            if silo_info:
                silo_dict = dict(silo_info)

                # Count categories in this silo
                count = db.execute('''
                    SELECT COUNT(*) as count FROM categories
                    WHERE domain_slug = ? AND silo_type = ? AND is_active = 1
                ''', (domain_slug, silo_type)).fetchone()

                silo_dict['category_count'] = count['count'] if count else 0
                result.append(silo_dict)

        return result

    def add_category(self, slug: str, name: str, domain_slug: str, silo_type: str,
                    description: Optional[str] = None, icon: Optional[str] = None,
                    requires_verification: bool = False) -> int:
        """
        Add a new category

        Args:
            slug: Category slug (unique per domain)
            name: Display name
            domain_slug: Domain this category belongs to
            silo_type: Silo type slug
            description: Optional description
            icon: Optional icon name/emoji
            requires_verification: Whether category requires verification

        Returns:
            New category ID
        """
        db = get_db()

        # Get max sort_order for this domain
        max_sort = db.execute('''
            SELECT MAX(sort_order) as max_sort FROM categories
            WHERE domain_slug = ?
        ''', (domain_slug,)).fetchone()

        sort_order = (max_sort['max_sort'] or 0) + 1

        cursor = db.execute('''
            INSERT INTO categories (slug, name, description, domain_slug, silo_type, icon, requires_verification, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (slug, name, description, domain_slug, silo_type, icon, requires_verification, sort_order))

        db.commit()
        return cursor.lastrowid

    def assign_category_to_professional(self, professional_id: int, category_id: int, is_primary: bool = False):
        """
        Assign a category to a professional

        Args:
            professional_id: Professional ID
            category_id: Category ID
            is_primary: Whether this is the primary category
        """
        db = get_db()

        # If setting as primary, unset other primary categories
        if is_primary:
            db.execute('''
                UPDATE professional_categories
                SET is_primary = 0
                WHERE professional_id = ?
            ''', (professional_id,))

        # Insert or update
        db.execute('''
            INSERT OR REPLACE INTO professional_categories (professional_id, category_id, is_primary)
            VALUES (?, ?, ?)
        ''', (professional_id, category_id, is_primary))

        db.commit()

    def get_professional_categories(self, professional_id: int) -> List[Dict]:
        """
        Get all categories for a professional

        Args:
            professional_id: Professional ID

        Returns:
            List of category dicts
        """
        db = get_db()

        categories = db.execute('''
            SELECT c.*, pc.is_primary
            FROM categories c
            INNER JOIN professional_categories pc ON pc.category_id = c.id
            WHERE pc.professional_id = ?
            ORDER BY pc.is_primary DESC, c.name
        ''', (professional_id,)).fetchall()

        return [dict(cat) for cat in categories]

    def get_professionals_by_category(self, category_id: int, limit: int = 50) -> List[Dict]:
        """
        Get all professionals in a category

        Args:
            category_id: Category ID
            limit: Maximum results

        Returns:
            List of professional dicts
        """
        db = get_db()

        professionals = db.execute('''
            SELECT p.*, pc.is_primary
            FROM professionals p
            INNER JOIN professional_categories pc ON pc.professional_id = p.id
            WHERE pc.category_id = ?
            ORDER BY p.rating_avg DESC, p.business_name
            LIMIT ?
        ''', (category_id, limit)).fetchall()

        return [dict(pro) for pro in professionals]

    def search_categories(self, query: str, domain_slug: Optional[str] = None) -> List[Dict]:
        """
        Search categories by name or description

        Args:
            query: Search query
            domain_slug: Optional domain filter

        Returns:
            List of matching category dicts
        """
        db = get_db()

        if domain_slug:
            categories = db.execute('''
                SELECT * FROM categories
                WHERE (name LIKE ? OR description LIKE ?) AND domain_slug = ? AND is_active = 1
                ORDER BY sort_order, name
                LIMIT 20
            ''', (f'%{query}%', f'%{query}%', domain_slug)).fetchall()
        else:
            categories = db.execute('''
                SELECT * FROM categories
                WHERE (name LIKE ? OR description LIKE ?) AND is_active = 1
                ORDER BY domain_slug, sort_order, name
                LIMIT 20
            ''', (f'%{query}%', f'%{query}%')).fetchall()

        return [dict(cat) for cat in categories]


# Singleton instance
_category_manager = None


def get_category_manager() -> CategoryManager:
    """Get singleton CategoryManager instance"""
    global _category_manager
    if _category_manager is None:
        _category_manager = CategoryManager()
    return _category_manager


# CLI testing
if __name__ == '__main__':
    import sys

    cm = CategoryManager()

    if len(sys.argv) > 1:
        domain_slug = sys.argv[1]
        print(f"\n📂 Categories for {domain_slug}:\n")

        categories = cm.get_categories_for_domain(domain_slug)
        for cat in categories:
            verified_icon = "✓" if cat['requires_verification'] else " "
            print(f"  [{verified_icon}] {cat['name']:30} ({cat['slug']}) - {cat['silo_type']}")

        print(f"\n📊 Total: {len(categories)} categories")

        print(f"\n🗂️  Silos:\n")
        silos = cm.get_silos_for_domain(domain_slug)
        for silo in silos:
            print(f"  {silo['name']:20} - {silo['category_count']} categories")

    else:
        print("\n📂 All Domains and Categories:\n")

        from domain_config.domain_loader import get_domain_config
        config = get_domain_config()

        for slug, domain in config.get_all_domains().items():
            categories = cm.get_categories_for_domain(slug)
            if categories:
                print(f"{domain['name']:20} → {len(categories)} categories")

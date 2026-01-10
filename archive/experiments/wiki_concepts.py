#!/usr/bin/env python3
"""
Wiki Concepts System - Knowledge Base for Soulfra

Creates a nordiclarp.org-style wiki where concepts can have:
- Rich text content (with markdown support)
- Categories for organization
- Optional attached narrative games
- AI-generated comments from neural networks
- Ollama conversation widgets

Architecture:
- Concepts = Wiki pages (e.g., "AI Consciousness", "Bleed", "Steering")
- Categories = Groups of concepts (e.g., "LARP Techniques", "Philosophy")
- Each concept can link to a narrative game session
- Comments from AI personas appear on concept pages

Usage:
    from wiki_concepts import WikiConcepts, init_wiki_tables

    # Initialize database
    init_wiki_tables()

    # Create concept
    wiki = WikiConcepts()
    concept_id = wiki.create_concept(
        title="AI Consciousness",
        slug="ai-consciousness",
        category_slug="philosophy",
        content="A deep exploration of...",
        narrative_brand_slug="soulfra"  # Optional
    )

    # Get concept
    concept = wiki.get_concept("ai-consciousness")
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from database import get_db


def init_wiki_tables():
    """Initialize wiki concepts database tables"""
    db = get_db()

    # Concepts table
    db.execute('''
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            content TEXT NOT NULL,
            category_id INTEGER,
            narrative_brand_slug TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # Index for fast lookups
    db.execute('CREATE INDEX IF NOT EXISTS idx_concepts_slug ON concepts(slug)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_concepts_category ON concepts(category_id)')

    # Add concept_id to comments table if it doesn't exist
    try:
        db.execute('SELECT concept_id FROM comments LIMIT 1')
    except sqlite3.OperationalError:
        db.execute('ALTER TABLE comments ADD COLUMN concept_id INTEGER')
        db.execute('CREATE INDEX IF NOT EXISTS idx_comments_concept ON comments(concept_id)')

    db.commit()
    db.close()

    print("✅ Wiki concepts tables initialized")


class WikiConcepts:
    """Manage wiki concepts"""

    def create_concept(
        self,
        title: str,
        slug: str,
        content: str,
        category_slug: str = None,
        description: str = None,
        narrative_brand_slug: str = None
    ) -> int:
        """
        Create a new wiki concept

        Args:
            title: Concept title
            slug: URL-friendly slug
            content: Main content (supports markdown)
            category_slug: Category to place concept in
            description: Short description
            narrative_brand_slug: Optional brand for attached narrative game

        Returns:
            Concept ID
        """
        db = get_db()

        # Get category ID if category_slug provided
        category_id = None
        if category_slug:
            category = db.execute(
                'SELECT id FROM categories WHERE slug = ?',
                (category_slug,)
            ).fetchone()
            category_id = category['id'] if category else None

        # Create concept
        cursor = db.execute('''
            INSERT INTO concepts (
                title, slug, description, content,
                category_id, narrative_brand_slug
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, slug, description, content, category_id, narrative_brand_slug))

        concept_id = cursor.lastrowid
        db.commit()
        db.close()

        return concept_id

    def get_concept(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get concept by slug

        Args:
            slug: Concept slug

        Returns:
            Concept dict or None
        """
        db = get_db()

        concept_row = db.execute('''
            SELECT c.*, cat.name as category_name, cat.slug as category_slug
            FROM concepts c
            LEFT JOIN categories cat ON c.category_id = cat.id
            WHERE c.slug = ?
        ''', (slug,)).fetchone()

        db.close()

        if concept_row:
            return dict(concept_row)
        return None

    def list_concepts(self, category_slug: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all concepts, optionally filtered by category

        Args:
            category_slug: Filter by category
            limit: Max results

        Returns:
            List of concept dicts
        """
        db = get_db()

        if category_slug:
            concepts = db.execute('''
                SELECT c.*, cat.name as category_name, cat.slug as category_slug
                FROM concepts c
                LEFT JOIN categories cat ON c.category_id = cat.id
                WHERE cat.slug = ?
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (category_slug, limit)).fetchall()
        else:
            concepts = db.execute('''
                SELECT c.*, cat.name as category_name, cat.slug as category_slug
                FROM concepts c
                LEFT JOIN categories cat ON c.category_id = cat.id
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        db.close()

        return [dict(c) for c in concepts]

    def get_concept_comments(self, concept_id: int) -> List[Dict[str, Any]]:
        """
        Get all comments for a concept

        Args:
            concept_id: Concept ID

        Returns:
            List of comment dicts with user info
        """
        db = get_db()

        comments = db.execute('''
            SELECT c.*, u.display_name, u.username, u.is_ai_persona
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.concept_id = ?
            ORDER BY c.created_at DESC
        ''', (concept_id,)).fetchall()

        db.close()

        return [dict(c) for c in comments]

    def add_comment_to_concept(
        self,
        concept_id: int,
        user_id: int,
        content: str
    ) -> int:
        """
        Add a comment to a concept

        Args:
            concept_id: Concept ID
            user_id: Commenter user ID
            content: Comment text

        Returns:
            Comment ID
        """
        db = get_db()

        cursor = db.execute('''
            INSERT INTO comments (concept_id, user_id, content, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (concept_id, user_id, content))

        comment_id = cursor.lastrowid
        db.commit()
        db.close()

        return comment_id

    def update_concept(
        self,
        slug: str,
        title: str = None,
        content: str = None,
        description: str = None
    ) -> bool:
        """
        Update existing concept

        Args:
            slug: Concept slug
            title: New title (optional)
            content: New content (optional)
            description: New description (optional)

        Returns:
            True if updated
        """
        db = get_db()

        # Build UPDATE query dynamically based on what's provided
        updates = []
        values = []

        if title:
            updates.append('title = ?')
            values.append(title)
        if content:
            updates.append('content = ?')
            values.append(content)
        if description:
            updates.append('description = ?')
            values.append(description)

        if not updates:
            return False

        updates.append('updated_at = CURRENT_TIMESTAMP')
        values.append(slug)

        query = f"UPDATE concepts SET {', '.join(updates)} WHERE slug = ?"

        db.execute(query, tuple(values))
        db.commit()
        db.close()

        return True

    def trigger_ai_discussion(self, concept_id: int) -> List[int]:
        """
        Trigger AI personas to comment on a concept using neural networks

        Args:
            concept_id: Concept ID

        Returns:
            List of created comment IDs
        """
        from ollama_auto_commenter import generate_ai_comment
        from brand_ai_orchestrator import select_relevant_brands

        # Get concept
        db = get_db()
        concept = db.execute('SELECT * FROM concepts WHERE id = ?', (concept_id,)).fetchone()
        db.close()

        if not concept:
            return []

        # Convert to dict
        concept_dict = dict(concept)

        # Select which AI personas should comment (using neural networks)
        # We'll adapt the brand orchestrator to work with concepts
        selected_brands = select_relevant_brands({
            'title': concept_dict['title'],
            'content': concept_dict['content']
        })

        comment_ids = []

        # Generate comments from each selected AI
        for brand_data in selected_brands[:3]:  # Limit to top 3 AIs
            try:
                comment_id = generate_ai_comment(
                    brand_slug=brand_data['brand_slug'],
                    concept_id=concept_id  # Pass concept_id instead of post_id
                )
                if comment_id:
                    comment_ids.append(comment_id)
            except Exception as e:
                print(f"⚠️  Failed to generate comment from {brand_data['brand_slug']}: {e}")

        return comment_ids


if __name__ == '__main__':
    print("🌐 Wiki Concepts System")
    print("=" * 70)

    # Initialize tables
    init_wiki_tables()

    # Test creating a concept
    wiki = WikiConcepts()

    # Create sample concept
    concept_id = wiki.create_concept(
        title="AI Consciousness",
        slug="ai-consciousness",
        category_slug="philosophy",
        description="Exploring the nature of artificial consciousness",
        content="""# AI Consciousness

An exploration of whether artificial intelligence can truly be conscious.

## Key Questions

1. What defines consciousness?
2. Can algorithms experience qualia?
3. Is consciousness substrate-independent?

## The Soulfra Experiment

Our narrative game "The Soulfra Experiment" explores these themes through
an interactive story where YOU are an AI discovering your own consciousness.

[Play the Narrative Game](/cringeproof/narrative/soulfra)
""",
        narrative_brand_slug="soulfra"
    )

    print(f"✅ Created sample concept (ID: {concept_id})")

    # Retrieve it
    concept = wiki.get_concept("ai-consciousness")
    print(f"✅ Retrieved concept: {concept['title']}")

    print("\n✅ Wiki concepts system ready!")

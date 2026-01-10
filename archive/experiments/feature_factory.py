#!/usr/bin/env python3
"""
Feature Factory - Pinterest-Style Template & Component Browser

"Isn't that the entirety of this thing is learning how to start a new idea
from the widget that you can save or pin or something" - User Vision

Philosophy:
-----------
Everything you need to build features, all in one place:
- Templates (HTML pages)
- Components (reusable UI pieces)
- Forms (data input)
- Database Schemas (tables & migrations)
- Routes (Flask endpoints)
- Colors & Styles (design system)
- File Structures (project scaffolding)

Pinterest-Style Interface:
-------------------------
- Browse by category
- Search and filter
- Preview before generating
- Save/Pin favorites
- One-click generation
- Blockchain-style organization (traceable, immutable history)

Usage:
    # Discover all available resources
    factory = FeatureFactory()
    catalog = factory.get_catalog()

    # Generate from template
    factory.generate('UserProfile', category='templates')

    # Save/pin for later
    factory.pin('UserCard', category='components')

    # Get pinned items
    pinned = factory.get_pinned()
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# Import existing generators
import template_generator
import route_generator


# ==============================================================================
# DATA MODELS
# ==============================================================================

@dataclass
class FactoryItem:
    """
    Represents a single item in the Feature Factory catalog

    Attributes:
        id: Unique identifier
        name: Display name
        category: Category (templates, components, routes, etc.)
        type: Specific type within category
        description: What this item does
        preview: Preview HTML/code snippet
        tags: Searchable tags
        dependencies: What this item requires
        created_at: When discovered/created
        pinned: Whether user has pinned this
        usage_count: How many times generated
    """
    id: str
    name: str
    category: str
    type: str
    description: str
    preview: str
    tags: List[str]
    dependencies: List[str]
    created_at: str
    pinned: bool = False
    usage_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


# ==============================================================================
# FEATURE FACTORY
# ==============================================================================

class FeatureFactory:
    """
    Pinterest-style catalog and generator for all platform resources

    Discovers:
    - HTML templates from /templates
    - Components from template_generator.py
    - Routes from app.py
    - Database schemas from schema.sql
    - Colors from CSS files
    - Forms (discovered from templates)
    """

    def __init__(self, db_path: str = "soulfra.db"):
        self.db_path = db_path
        self.base_path = Path(__file__).parent
        self.templates_path = self.base_path / "templates"
        self._init_factory_db()

    def _init_factory_db(self):
        """Initialize factory database for tracking pins, usage, etc."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS factory_pins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                name TEXT,
                category TEXT,
                pinned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS factory_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT,
                category TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                output_path TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS factory_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                item_id TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    # ==========================================================================
    # DISCOVERY - Find all available resources
    # ==========================================================================

    def discover_templates(self) -> List[FactoryItem]:
        """Discover all HTML templates in /templates"""
        items = []

        if not self.templates_path.exists():
            return items

        for template_file in self.templates_path.glob("*.html"):
            # Read first few lines for description
            try:
                with open(template_file, 'r') as f:
                    content = f.read()
                    # Extract title from {% block title %}
                    title = "Untitled"
                    if "{% block title %}" in content:
                        start = content.find("{% block title %}") + len("{% block title %}")
                        end = content.find("{% endblock %}", start)
                        title = content[start:end].strip()

                    # Get preview (first 500 chars after {% block content %})
                    preview = content[:500]
                    if "{% block content %}" in content:
                        start = content.find("{% block content %}") + len("{% block content %}")
                        preview = content[start:start+500]

                    # Determine tags based on content
                    tags = []
                    if 'form' in content.lower():
                        tags.append('form')
                    if 'admin' in template_file.stem:
                        tags.append('admin')
                    if 'api' in template_file.stem:
                        tags.append('api')
                    if 'dashboard' in content.lower() or 'stats' in content.lower():
                        tags.append('dashboard')
                    if 'brand' in template_file.stem:
                        tags.append('brand')
                    if 'ai' in template_file.stem or 'soul' in template_file.stem:
                        tags.append('ai')

                    items.append(FactoryItem(
                        id=f"template_{template_file.stem}",
                        name=template_file.stem.replace('_', ' ').title(),
                        category="templates",
                        type="html_page",
                        description=f"HTML template: {title}",
                        preview=preview,
                        tags=tags,
                        dependencies=["base.html"] if "{% extends" in content else [],
                        created_at=datetime.now().isoformat(),
                        pinned=self._is_pinned(f"template_{template_file.stem}"),
                        usage_count=self._get_usage_count(f"template_{template_file.stem}")
                    ))
            except Exception as e:
                print(f"Error reading template {template_file}: {e}")
                continue

        return items

    def discover_components(self) -> List[FactoryItem]:
        """Discover available component templates from template_generator.py"""
        items = []

        # Component types available in template_generator.py
        component_types = {
            'UserCard': 'User profile card with avatar, bio, and actions',
            'Button': 'Styled button with variants (primary, secondary)',
            'Nav': 'Navigation bar with links and user menu',
            'Card': 'Generic card container with header, body, footer',
            'Form': 'Form with input fields and validation',
            'Modal': 'Modal dialog overlay with header, body, footer',
        }

        for comp_name, description in component_types.items():
            # Generate preview
            preview = template_generator.generate_component(comp_name)

            items.append(FactoryItem(
                id=f"component_{comp_name.lower()}",
                name=comp_name,
                category="components",
                type="html_component",
                description=description,
                preview=preview[:500],
                tags=['reusable', 'ui', 'component'],
                dependencies=[],
                created_at=datetime.now().isoformat(),
                pinned=self._is_pinned(f"component_{comp_name.lower()}"),
                usage_count=self._get_usage_count(f"component_{comp_name.lower()}")
            ))

        return items

    def discover_pages(self) -> List[FactoryItem]:
        """Discover available page templates from template_generator.py"""
        items = []

        page_types = {
            'BlogPost': 'Blog post page with title, content, tags',
            'UserProfile': 'User profile page with stats and posts',
            'Dashboard': 'Analytics dashboard with stat cards',
            'Login': 'Login form page',
        }

        for page_name, description in page_types.items():
            preview = template_generator.generate_page(page_name)

            items.append(FactoryItem(
                id=f"page_{page_name.lower()}",
                name=page_name,
                category="pages",
                type="html_page",
                description=description,
                preview=preview[:500],
                tags=['full-page', 'template'],
                dependencies=['base.html'],
                created_at=datetime.now().isoformat(),
                pinned=self._is_pinned(f"page_{page_name.lower()}"),
                usage_count=self._get_usage_count(f"page_{page_name.lower()}")
            ))

        return items

    def discover_routes(self) -> List[FactoryItem]:
        """Discover available route templates"""
        items = []

        # CRUD routes can be generated for any table
        from route_discovery import get_all_flask_routes
        try:
            # Import app to discover existing routes
            import app as flask_app
            routes = get_all_flask_routes(flask_app.app)

            # Group routes by endpoint prefix
            route_patterns = {}
            for route in routes:
                endpoint = route['endpoint']
                if endpoint not in route_patterns:
                    route_patterns[endpoint] = {
                        'path': route['path'],
                        'methods': route['methods'],
                        'description': route.get('description', '')
                    }

            for endpoint, info in route_patterns.items():
                items.append(FactoryItem(
                    id=f"route_{endpoint}",
                    name=endpoint.replace('_', ' ').title(),
                    category="routes",
                    type="flask_route",
                    description=info['description'] or f"Route: {info['path']}",
                    preview=f"@app.route('{info['path']}', methods={info['methods']})",
                    tags=['flask', 'endpoint'],
                    dependencies=['Flask'],
                    created_at=datetime.now().isoformat(),
                    pinned=self._is_pinned(f"route_{endpoint}"),
                    usage_count=self._get_usage_count(f"route_{endpoint}")
                ))
        except Exception as e:
            print(f"Error discovering routes: {e}")

        return items

    def discover_schemas(self) -> List[FactoryItem]:
        """Discover database schemas from schema.sql"""
        items = []

        schema_file = self.base_path / "schema.sql"
        if not schema_file.exists():
            return items

        try:
            with open(schema_file, 'r') as f:
                content = f.read()

                # Parse CREATE TABLE statements
                tables = []
                lines = content.split('\n')
                current_table = None
                table_sql = []

                for line in lines:
                    if 'CREATE TABLE' in line.upper():
                        if current_table:
                            tables.append({
                                'name': current_table,
                                'sql': '\n'.join(table_sql)
                            })
                        current_table = line.split('CREATE TABLE')[-1].strip().split('(')[0].strip()
                        table_sql = [line]
                    elif current_table:
                        table_sql.append(line)
                        if ');' in line:
                            tables.append({
                                'name': current_table,
                                'sql': '\n'.join(table_sql)
                            })
                            current_table = None
                            table_sql = []

                for table in tables:
                    items.append(FactoryItem(
                        id=f"schema_{table['name']}",
                        name=table['name'],
                        category="schemas",
                        type="database_table",
                        description=f"Database table: {table['name']}",
                        preview=table['sql'][:500],
                        tags=['database', 'sql', 'table'],
                        dependencies=[],
                        created_at=datetime.now().isoformat(),
                        pinned=self._is_pinned(f"schema_{table['name']}"),
                        usage_count=self._get_usage_count(f"schema_{table['name']}")
                    ))
        except Exception as e:
            print(f"Error discovering schemas: {e}")

        return items

    def discover_colors(self) -> List[FactoryItem]:
        """Discover color palettes from CSS files"""
        items = []

        # Define color palettes used in the platform
        palettes = {
            'Primary Gradient': {
                'colors': ['#667eea', '#764ba2'],
                'usage': 'Headers, primary actions, brand elements'
            },
            'Success Gradient': {
                'colors': ['#11998e', '#38ef7d'],
                'usage': 'Success messages, completed states'
            },
            'Info Gradient': {
                'colors': ['#4facfe', '#00f2fe'],
                'usage': 'Information, neutral states'
            },
            'Warning Gradient': {
                'colors': ['#f2994a', '#f2c94c'],
                'usage': 'Warnings, alerts'
            },
            'Accent Gradient': {
                'colors': ['#fa709a', '#fee140'],
                'usage': 'Highlights, special elements'
            },
        }

        for palette_name, info in palettes.items():
            css_preview = f"background: linear-gradient(135deg, {info['colors'][0]} 0%, {info['colors'][1]} 100%);"

            items.append(FactoryItem(
                id=f"color_{palette_name.lower().replace(' ', '_')}",
                name=palette_name,
                category="colors",
                type="gradient_palette",
                description=info['usage'],
                preview=css_preview,
                tags=['color', 'gradient', 'design'],
                dependencies=[],
                created_at=datetime.now().isoformat(),
                pinned=self._is_pinned(f"color_{palette_name.lower().replace(' ', '_')}"),
                usage_count=self._get_usage_count(f"color_{palette_name.lower().replace(' ', '_')}")
            ))

        return items

    def discover_forms(self) -> List[FactoryItem]:
        """Discover form templates"""
        items = []

        # Common form types
        form_types = {
            'Login Form': 'Username/email and password with submit',
            'Registration Form': 'User signup with validation',
            'Profile Edit': 'Edit user profile information',
            'Contact Form': 'Contact form with name, email, message',
            'Search Form': 'Search input with filters',
            'Upload Form': 'File upload with drag-and-drop',
        }

        for form_name, description in form_types.items():
            preview = template_generator.generate_component('Form', {'name': form_name})

            items.append(FactoryItem(
                id=f"form_{form_name.lower().replace(' ', '_')}",
                name=form_name,
                category="forms",
                type="html_form",
                description=description,
                preview=preview[:500],
                tags=['form', 'input', 'validation'],
                dependencies=[],
                created_at=datetime.now().isoformat(),
                pinned=self._is_pinned(f"form_{form_name.lower().replace(' ', '_')}"),
                usage_count=self._get_usage_count(f"form_{form_name.lower().replace(' ', '_')}")
            ))

        return items

    def discover_generators(self) -> List[FactoryItem]:
        """Discover available code generators"""
        items = []

        generators = {
            'Template Generator': {
                'file': 'template_generator.py',
                'description': 'Generate HTML templates, components, pages',
                'capabilities': ['component', 'page', 'folder']
            },
            'Route Generator': {
                'file': 'route_generator.py',
                'description': 'Auto-generate Flask routes from DB tables',
                'capabilities': ['crud', 'api', 'admin']
            },
            'Brand Generator': {
                'file': 'brand_generator.py',
                'description': 'Generate brand pages and assets',
                'capabilities': ['brand-page', 'qr-code', 'avatar']
            },
            'Avatar Generator': {
                'file': 'avatar_generator.py',
                'description': 'Generate user/brand avatars',
                'capabilities': ['user-avatar', 'brand-avatar', 'ai-avatar']
            },
        }

        for gen_name, info in generators.items():
            items.append(FactoryItem(
                id=f"generator_{gen_name.lower().replace(' ', '_')}",
                name=gen_name,
                category="generators",
                type="code_generator",
                description=info['description'],
                preview=f"python3 {info['file']} [options]",
                tags=['generator', 'automation'] + info['capabilities'],
                dependencies=['Python 3.9+'],
                created_at=datetime.now().isoformat(),
                pinned=self._is_pinned(f"generator_{gen_name.lower().replace(' ', '_')}"),
                usage_count=self._get_usage_count(f"generator_{gen_name.lower().replace(' ', '_')}")
            ))

        return items

    # ==========================================================================
    # CATALOG - Get all items organized
    # ==========================================================================

    def get_catalog(self, category: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    search: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Get complete catalog of all available items

        Args:
            category: Filter by category
            tags: Filter by tags
            search: Search in name/description

        Returns:
            Dictionary organized by category
        """
        all_items = (
            self.discover_templates() +
            self.discover_components() +
            self.discover_pages() +
            self.discover_routes() +
            self.discover_schemas() +
            self.discover_colors() +
            self.discover_forms() +
            self.discover_generators()
        )

        # Apply filters
        if category:
            all_items = [item for item in all_items if item.category == category]

        if tags:
            all_items = [item for item in all_items
                        if any(tag in item.tags for tag in tags)]

        if search:
            search_lower = search.lower()
            all_items = [item for item in all_items
                        if search_lower in item.name.lower()
                        or search_lower in item.description.lower()]

        # Organize by category
        catalog = {}
        for item in all_items:
            if item.category not in catalog:
                catalog[item.category] = []
            catalog[item.category].append(item.to_dict())

        return catalog

    def get_stats(self) -> Dict[str, Any]:
        """Get factory statistics"""
        catalog = self.get_catalog()

        total_items = sum(len(items) for items in catalog.values())

        conn = sqlite3.connect(self.db_path)
        pinned_count = conn.execute('SELECT COUNT(*) FROM factory_pins').fetchone()[0]
        total_usage = conn.execute('SELECT COUNT(*) FROM factory_usage').fetchone()[0]
        conn.close()

        return {
            'total_items': total_items,
            'categories': len(catalog),
            'pinned_items': pinned_count,
            'total_generations': total_usage,
            'by_category': {cat: len(items) for cat, items in catalog.items()}
        }

    # ==========================================================================
    # PIN/SAVE - Save items for later
    # ==========================================================================

    def pin(self, item_id: str, name: str, category: str) -> bool:
        """Pin an item for quick access"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO factory_pins (item_id, name, category)
                VALUES (?, ?, ?)
            ''', (item_id, name, category))

            # Log history
            conn.execute('''
                INSERT INTO factory_history (action, item_id, details)
                VALUES (?, ?, ?)
            ''', ('pin', item_id, json.dumps({'category': category})))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error pinning item: {e}")
            return False

    def unpin(self, item_id: str) -> bool:
        """Unpin an item"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('DELETE FROM factory_pins WHERE item_id = ?', (item_id,))

            # Log history
            conn.execute('''
                INSERT INTO factory_history (action, item_id, details)
                VALUES (?, ?, ?)
            ''', ('unpin', item_id, '{}'))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error unpinning item: {e}")
            return False

    def get_pinned(self) -> List[Dict]:
        """Get all pinned items"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('''
            SELECT item_id, name, category, pinned_at
            FROM factory_pins
            ORDER BY pinned_at DESC
        ''').fetchall()
        conn.close()

        return [
            {
                'item_id': row[0],
                'name': row[1],
                'category': row[2],
                'pinned_at': row[3]
            }
            for row in rows
        ]

    def _is_pinned(self, item_id: str) -> bool:
        """Check if item is pinned"""
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            'SELECT 1 FROM factory_pins WHERE item_id = ?',
            (item_id,)
        ).fetchone()
        conn.close()
        return result is not None

    def _get_usage_count(self, item_id: str) -> int:
        """Get usage count for item"""
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            'SELECT COUNT(*) FROM factory_usage WHERE item_id = ?',
            (item_id,)
        ).fetchone()
        conn.close()
        return result[0] if result else 0

    # ==========================================================================
    # GENERATE - Create from templates
    # ==========================================================================

    def generate(self, item_id: str, output_path: Optional[str] = None,
                 options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate code/files from a catalog item

        Args:
            item_id: Item to generate from
            output_path: Where to save generated files
            options: Additional generation options

        Returns:
            Result with success status and generated content
        """
        options = options or {}

        # Parse item_id to get category and name
        if '_' not in item_id:
            return {'success': False, 'error': 'Invalid item_id format'}

        category, name = item_id.split('_', 1)

        try:
            result = None

            if category == 'component':
                # Generate HTML component
                content = template_generator.generate_component(name.title())
                result = {'content': content, 'type': 'html'}

            elif category == 'page':
                # Generate HTML page
                content = template_generator.generate_page(name.title())
                result = {'content': content, 'type': 'html'}

            elif category == 'template':
                # Copy existing template
                template_path = self.templates_path / f"{name}.html"
                if template_path.exists():
                    with open(template_path, 'r') as f:
                        content = f.read()
                    result = {'content': content, 'type': 'html'}

            elif category == 'route':
                # Generate Flask route
                content = template_generator.generate_flask_route(name)
                result = {'content': content, 'type': 'python'}

            elif category == 'form':
                # Generate form component
                content = template_generator.generate_component('Form', {'name': name})
                result = {'content': content, 'type': 'html'}

            elif category == 'color':
                # Return CSS for color palette
                content = f"/* {name} */\n{self._get_color_css(name)}"
                result = {'content': content, 'type': 'css'}

            else:
                return {'success': False, 'error': f'Unknown category: {category}'}

            # Save to file if output_path provided
            if output_path and result:
                with open(output_path, 'w') as f:
                    f.write(result['content'])
                result['output_path'] = output_path

            # Track usage
            if result:
                self._track_usage(item_id, category, output_path)

            return {
                'success': True,
                **result
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_color_css(self, palette_name: str) -> str:
        """Get CSS for a color palette"""
        palettes = {
            'primary_gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'success_gradient': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
            'info_gradient': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'warning_gradient': 'linear-gradient(135deg, #f2994a 0%, #f2c94c 100%)',
            'accent_gradient': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        }
        return palettes.get(palette_name.lower(), '')

    def _track_usage(self, item_id: str, category: str, output_path: Optional[str]):
        """Track usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO factory_usage (item_id, category, output_path)
                VALUES (?, ?, ?)
            ''', (item_id, category, output_path or ''))

            # Log history
            conn.execute('''
                INSERT INTO factory_history (action, item_id, details)
                VALUES (?, ?, ?)
            ''', ('generate', item_id, json.dumps({'output_path': output_path})))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error tracking usage: {e}")

    # ==========================================================================
    # HISTORY - Track all factory actions
    # ==========================================================================

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get factory action history"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('''
            SELECT action, item_id, details, created_at
            FROM factory_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        conn.close()

        return [
            {
                'action': row[0],
                'item_id': row[1],
                'details': json.loads(row[2]) if row[2] else {},
                'created_at': row[3]
            }
            for row in rows
        ]


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Feature Factory - Pinterest-Style Template Browser'
    )
    parser.add_argument('--catalog', action='store_true',
                       help='Show full catalog')
    parser.add_argument('--category', type=str,
                       help='Filter by category')
    parser.add_argument('--search', type=str,
                       help='Search items')
    parser.add_argument('--stats', action='store_true',
                       help='Show factory statistics')
    parser.add_argument('--pinned', action='store_true',
                       help='Show pinned items')
    parser.add_argument('--history', action='store_true',
                       help='Show action history')
    parser.add_argument('--generate', type=str,
                       help='Generate item by ID')
    parser.add_argument('--output', type=str,
                       help='Output path for generated item')
    parser.add_argument('--pin', type=str,
                       help='Pin item by ID')
    parser.add_argument('--unpin', type=str,
                       help='Unpin item by ID')

    args = parser.parse_args()

    factory = FeatureFactory()

    if args.stats:
        stats = factory.get_stats()
        print("\n📊 FEATURE FACTORY STATISTICS")
        print("=" * 70)
        print(f"Total Items: {stats['total_items']}")
        print(f"Categories: {stats['categories']}")
        print(f"Pinned Items: {stats['pinned_items']}")
        print(f"Total Generations: {stats['total_generations']}")
        print("\nBy Category:")
        for cat, count in stats['by_category'].items():
            print(f"  {cat}: {count}")
        print()

    elif args.catalog:
        catalog = factory.get_catalog(
            category=args.category,
            search=args.search
        )

        print("\n🏭 FEATURE FACTORY CATALOG")
        print("=" * 70)

        for category, items in catalog.items():
            print(f"\n📁 {category.upper()} ({len(items)} items)")
            print("-" * 70)
            for item in items:
                pin_indicator = "📌" if item['pinned'] else "  "
                print(f"{pin_indicator} {item['id']}")
                print(f"   {item['name']}: {item['description']}")
                if item['usage_count'] > 0:
                    print(f"   Used {item['usage_count']} times")
                print()

    elif args.pinned:
        pinned = factory.get_pinned()
        print("\n📌 PINNED ITEMS")
        print("=" * 70)
        for item in pinned:
            print(f"{item['name']} ({item['category']})")
            print(f"  ID: {item['item_id']}")
            print(f"  Pinned: {item['pinned_at']}")
            print()

    elif args.history:
        history = factory.get_history()
        print("\n📜 FACTORY HISTORY")
        print("=" * 70)
        for entry in history:
            print(f"{entry['created_at']}: {entry['action']} - {entry['item_id']}")
            if entry['details']:
                print(f"  Details: {entry['details']}")
            print()

    elif args.generate:
        result = factory.generate(args.generate, output_path=args.output)
        if result['success']:
            print(f"\n✅ Generated {args.generate}")
            if 'output_path' in result:
                print(f"Saved to: {result['output_path']}")
            else:
                print("\nContent:")
                print(result['content'])
        else:
            print(f"\n❌ Error: {result['error']}")

    elif args.pin:
        # Need to get category from item_id
        catalog = factory.get_catalog()
        found = False
        for category, items in catalog.items():
            for item in items:
                if item['id'] == args.pin:
                    factory.pin(args.pin, item['name'], category)
                    print(f"✅ Pinned: {item['name']}")
                    found = True
                    break
        if not found:
            print(f"❌ Item not found: {args.pin}")

    elif args.unpin:
        factory.unpin(args.unpin)
        print(f"✅ Unpinned: {args.unpin}")

    else:
        print("Feature Factory - Pinterest-Style Template Browser")
        print()
        print("Usage:")
        print("  --catalog              Show all available items")
        print("  --category templates   Filter by category")
        print("  --search form          Search items")
        print("  --stats                Show statistics")
        print("  --pinned               Show pinned items")
        print("  --history              Show action history")
        print("  --generate item_id     Generate item")
        print("  --pin item_id          Pin item")
        print("  --unpin item_id        Unpin item")
        print()
        print("Examples:")
        print("  python3 feature_factory.py --catalog")
        print("  python3 feature_factory.py --generate component_usercard --output usercard.html")
        print("  python3 feature_factory.py --pin page_blogpost")
        print()

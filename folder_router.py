#!/usr/bin/env python3
"""
Folder Router - @brand Routing System

Twitter-style routing for brand content:
- @soulfra/blog/security → /brands/soulfra/blog/security.md
- @deathtodata/privacy → /brands/deathtodata/privacy
- @yourname/guides/vpn → /brands/yourname/guides/vpn.html

**The Concept:**
Use @ syntax (like Twitter handles) to route content to brand folders.
Each brand has its own folder structure, and routes map to files.

**Route Format:**
```
@brand/category/subcategory/file

Examples:
@soulfra/blog/security/encryption
@deathtodata/privacy/vpn
@calriven/architecture/databases
```

**How It Works:**
1. User types: @soulfra/blog/security
2. System looks up route in database
3. Finds file path: /brands/soulfra/blog/security.md
4. Serves content

**Usage:**
```python
from folder_router import FolderRouter

router = FolderRouter()

# Parse route
parsed = router.parse_route('@soulfra/blog/security')
# Returns: {'brand': 'soulfra', 'category': 'blog', 'file': 'security'}

# Resolve route to file path
file_path = router.resolve_route('@soulfra/blog/security')
# Returns: '/path/to/brands/soulfra/blog/security.md'

# Register new route
router.register_route(
    route='@soulfra/blog/new-post',
    file_path='/brands/soulfra/blog/new-post.md',
    user_id=15
)
```
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

from database import get_db


# ==============================================================================
# CONFIG
# ==============================================================================

BRANDS_DIR = os.environ.get('BRANDS_DIR', './brands')
ROUTE_PATTERN = re.compile(r'^@([a-z0-9_-]+)(/([a-z0-9_/-]+))?$', re.IGNORECASE)


# ==============================================================================
# FOLDER ROUTER CLASS
# ==============================================================================

class FolderRouter:
    """
    Route @brand paths to physical files
    """

    def __init__(self, brands_dir: str = BRANDS_DIR):
        self.brands_dir = Path(brands_dir)
        self.brands_dir.mkdir(parents=True, exist_ok=True)


    # ==========================================================================
    # ROUTE PARSING
    # ==========================================================================

    def parse_route(self, route: str) -> Optional[Dict]:
        """
        Parse @brand route into components

        Args:
            route: Route string (e.g., '@soulfra/blog/security')

        Returns:
            Dict with route components or None if invalid

        Example:
            >>> router = FolderRouter()
            >>> parsed = router.parse_route('@soulfra/blog/security')
            >>> print(parsed)
            {
                'brand': 'soulfra',
                'category': 'blog',
                'subcategory': None,
                'file': 'security',
                'full_route': '@soulfra/blog/security'
            }
        """
        # Remove leading/trailing slashes
        route = route.strip('/')

        # Must start with @
        if not route.startswith('@'):
            return None

        # Split into parts
        parts = route.split('/')

        if len(parts) < 1:
            return None

        # Parse components
        brand = parts[0].lstrip('@')
        category = parts[1] if len(parts) > 1 else None

        # Everything after category is path
        path_parts = parts[2:] if len(parts) > 2 else []

        # Last part is filename, everything before is subcategory
        filename = path_parts[-1] if path_parts else None
        subcategory_parts = path_parts[:-1] if len(path_parts) > 1 else []
        subcategory = '/'.join(subcategory_parts) if subcategory_parts else None

        return {
            'brand': brand,
            'category': category,
            'subcategory': subcategory,
            'file': filename,
            'full_route': route,
            'parts': parts
        }


    def is_valid_route(self, route: str) -> bool:
        """
        Check if route is valid format

        Args:
            route: Route string

        Returns:
            True if valid
        """
        return self.parse_route(route) is not None


    # ==========================================================================
    # ROUTE RESOLUTION
    # ==========================================================================

    def resolve_route(self, route: str, check_db: bool = True) -> Optional[Path]:
        """
        Resolve route to physical file path

        Args:
            route: Route string (e.g., '@soulfra/blog/post')
            check_db: Check database first

        Returns:
            Path to file or None if not found

        Example:
            >>> router = FolderRouter()
            >>> path = router.resolve_route('@soulfra/blog/security')
            >>> print(path)
            /path/to/brands/soulfra/blog/security.md
        """
        # Check database first
        if check_db:
            db_path = self._resolve_from_database(route)
            if db_path:
                return db_path

        # Parse route
        parsed = self.parse_route(route)
        if not parsed:
            return None

        # Build file path
        brand = parsed['brand']
        category = parsed['category']
        subcategory = parsed['subcategory']
        filename = parsed['file']

        if not brand:
            return None

        # Try to find file
        base_path = self.brands_dir / brand

        if category:
            base_path = base_path / category

        if subcategory:
            base_path = base_path / subcategory

        # Try different file extensions
        if filename:
            extensions = ['.md', '.html', '.txt', '']
            for ext in extensions:
                file_path = base_path / f'{filename}{ext}'
                if file_path.exists():
                    return file_path

        # Try as directory with index
        if base_path.is_dir():
            for index_name in ['index.md', 'index.html', 'README.md']:
                index_path = base_path / index_name
                if index_path.exists():
                    return index_path

        return None


    def _resolve_from_database(self, route: str) -> Optional[Path]:
        """
        Look up route in database

        Args:
            route: Route string

        Returns:
            Path if found in database
        """
        conn = get_db()
        cursor = conn.execute('''
            SELECT file_path FROM file_routes
            WHERE route = ?
        ''', (route,))

        row = cursor.fetchone()
        conn.close()

        if row:
            file_path = Path(row[0])
            if file_path.exists():
                return file_path

        return None


    # ==========================================================================
    # ROUTE REGISTRATION
    # ==========================================================================

    def register_route(
        self,
        route: str,
        file_path: str,
        user_id: int,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Register a route in the database

        Args:
            route: Route string (e.g., '@soulfra/blog/post')
            file_path: Physical file path
            user_id: Owner user ID
            metadata: Optional metadata

        Returns:
            Route ID

        Example:
            >>> router = FolderRouter()
            >>> route_id = router.register_route(
            ...     route='@soulfra/blog/new-post',
            ...     file_path='/brands/soulfra/blog/new-post.md',
            ...     user_id=15
            ... )
        """
        # Parse route
        parsed = self.parse_route(route)
        if not parsed:
            raise ValueError(f"Invalid route format: {route}")

        # Save to database
        conn = get_db()

        try:
            cursor = conn.execute('''
                INSERT INTO file_routes
                (route, brand, category, subcategory, filename, file_path,
                 owner_user_id, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                route,
                parsed['brand'],
                parsed['category'],
                parsed['subcategory'],
                parsed['file'],
                file_path,
                user_id,
                str(metadata or {}),
                datetime.now()
            ))

            route_id = cursor.lastrowid
            conn.commit()

            return route_id

        except sqlite3.IntegrityError:
            # Route already exists, update it
            cursor = conn.execute('''
                UPDATE file_routes
                SET file_path = ?, updated_at = ?
                WHERE route = ?
            ''', (file_path, datetime.now(), route))

            conn.commit()

            # Get the route ID
            cursor = conn.execute('SELECT id FROM file_routes WHERE route = ?', (route,))
            route_id = cursor.fetchone()[0]

            return route_id

        finally:
            conn.close()


    def unregister_route(self, route: str) -> bool:
        """
        Remove route from database

        Args:
            route: Route to remove

        Returns:
            True if removed
        """
        conn = get_db()
        cursor = conn.execute('DELETE FROM file_routes WHERE route = ?', (route,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted


    # ==========================================================================
    # ROUTE LISTING
    # ==========================================================================

    def list_routes(
        self,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """
        List registered routes

        Args:
            brand: Filter by brand
            category: Filter by category
            user_id: Filter by owner

        Returns:
            List of route dicts

        Example:
            >>> router = FolderRouter()
            >>> routes = router.list_routes(brand='soulfra')
            >>> for route in routes:
            ...     print(route['route'])
        """
        conn = get_db()

        query = 'SELECT route, brand, category, subcategory, filename, file_path, owner_user_id, created_at FROM file_routes WHERE 1=1'
        params = []

        if brand:
            query += ' AND brand = ?'
            params.append(brand)

        if category:
            query += ' AND category = ?'
            params.append(category)

        if user_id:
            query += ' AND owner_user_id = ?'
            params.append(user_id)

        query += ' ORDER BY created_at DESC'

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        routes = []
        for row in rows:
            routes.append({
                'route': row[0],
                'brand': row[1],
                'category': row[2],
                'subcategory': row[3],
                'filename': row[4],
                'file_path': row[5],
                'owner_user_id': row[6],
                'created_at': row[7]
            })

        return routes


    def get_route_info(self, route: str) -> Optional[Dict]:
        """
        Get full information about a route

        Args:
            route: Route string

        Returns:
            Dict with route info or None
        """
        conn = get_db()
        cursor = conn.execute('''
            SELECT route, brand, category, subcategory, filename, file_path,
                   owner_user_id, file_type, file_size, metadata, created_at
            FROM file_routes
            WHERE route = ?
        ''', (route,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'route': row[0],
            'brand': row[1],
            'category': row[2],
            'subcategory': row[3],
            'filename': row[4],
            'file_path': row[5],
            'owner_user_id': row[6],
            'file_type': row[7],
            'file_size': row[8],
            'metadata': row[9],
            'created_at': row[10]
        }


    # ==========================================================================
    # BRAND MANAGEMENT
    # ==========================================================================

    def list_brands(self) -> List[str]:
        """
        List all brands

        Returns:
            List of brand names
        """
        conn = get_db()
        cursor = conn.execute('SELECT DISTINCT brand FROM file_routes ORDER BY brand')
        brands = [row[0] for row in cursor.fetchall()]
        conn.close()

        return brands


    def list_categories(self, brand: str) -> List[str]:
        """
        List categories for a brand

        Args:
            brand: Brand name

        Returns:
            List of categories
        """
        conn = get_db()
        cursor = conn.execute('''
            SELECT DISTINCT category FROM file_routes
            WHERE brand = ?
            ORDER BY category
        ''', (brand,))

        categories = [row[0] for row in cursor.fetchall()]
        conn.close()

        return categories


    def get_brand_stats(self, brand: str) -> Dict:
        """
        Get statistics for a brand

        Args:
            brand: Brand name

        Returns:
            Dict with stats
        """
        conn = get_db()

        # Count routes
        cursor = conn.execute('''
            SELECT COUNT(*), COUNT(DISTINCT category), COUNT(DISTINCT owner_user_id)
            FROM file_routes
            WHERE brand = ?
        ''', (brand,))

        row = cursor.fetchone()

        # Total file size
        cursor = conn.execute('''
            SELECT SUM(file_size)
            FROM file_routes
            WHERE brand = ?
        ''', (brand,))

        total_size = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'brand': brand,
            'total_routes': row[0],
            'total_categories': row[1],
            'total_contributors': row[2],
            'total_size_bytes': total_size
        }


    # ==========================================================================
    # URL REWRITING
    # ==========================================================================

    def rewrite_url(self, url: str) -> Optional[str]:
        """
        Rewrite @route URL to physical path

        Args:
            url: URL with @ route

        Returns:
            Rewritten URL or None

        Example:
            >>> router = FolderRouter()
            >>> rewritten = router.rewrite_url('/view/@soulfra/blog/post')
            >>> print(rewritten)
            /brands/soulfra/blog/post.md
        """
        # Extract @route from URL
        match = re.search(r'(@[a-z0-9_/-]+)', url, re.IGNORECASE)
        if not match:
            return None

        route = match.group(1)

        # Resolve route
        file_path = self.resolve_route(route)
        if not file_path:
            return None

        # Replace @route with file path
        rewritten = url.replace(route, str(file_path))

        return rewritten


# ==============================================================================
# FLASK INTEGRATION
# ==============================================================================

def create_route_blueprint():
    """
    Create Flask blueprint for route handling

    Usage in app.py:
    >>> from folder_router import create_route_blueprint
    >>> app.register_blueprint(create_route_blueprint())
    """
    try:
        from flask import Blueprint, request, send_file, jsonify, abort
    except ImportError:
        print("Flask not available, skipping blueprint creation")
        return None

    bp = Blueprint('routes', __name__)
    router = FolderRouter()

    @bp.route('/<path:route>')
    def serve_route(route):
        """Serve file by @route"""
        # Add @ prefix if missing
        if not route.startswith('@'):
            route = f'@{route}'

        # Resolve route
        file_path = router.resolve_route(route)

        if not file_path:
            abort(404, f"Route not found: {route}")

        # Serve file
        return send_file(str(file_path))

    @bp.route('/api/routes', methods=['GET'])
    def list_routes():
        """List all routes"""
        brand = request.args.get('brand')
        category = request.args.get('category')

        routes = router.list_routes(brand=brand, category=category)

        return jsonify({
            'routes': routes,
            'count': len(routes)
        })

    @bp.route('/api/routes/<path:route>', methods=['GET'])
    def get_route(route):
        """Get route info"""
        if not route.startswith('@'):
            route = f'@{route}'

        info = router.get_route_info(route)

        if not info:
            abort(404, f"Route not found: {route}")

        return jsonify(info)

    @bp.route('/api/brands', methods=['GET'])
    def list_brands():
        """List all brands"""
        brands = router.list_brands()

        return jsonify({
            'brands': brands,
            'count': len(brands)
        })

    @bp.route('/api/brands/<brand>/stats', methods=['GET'])
    def brand_stats(brand):
        """Get brand statistics"""
        stats = router.get_brand_stats(brand)

        return jsonify(stats)

    return bp


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Folder Router')
    parser.add_argument('--parse', type=str, help='Parse a route')
    parser.add_argument('--resolve', type=str, help='Resolve route to file path')
    parser.add_argument('--register', type=str, help='Register a route')
    parser.add_argument('--file', type=str, help='File path for registration')
    parser.add_argument('--user-id', type=int, default=1, help='User ID')
    parser.add_argument('--list', action='store_true', help='List all routes')
    parser.add_argument('--brand', type=str, help='Filter by brand')
    parser.add_argument('--brands', action='store_true', help='List all brands')

    args = parser.parse_args()

    router = FolderRouter()

    if args.parse:
        parsed = router.parse_route(args.parse)
        if parsed:
            print(f'\n📍 Parsed Route:\n')
            for key, value in parsed.items():
                print(f'   {key}: {value}')
            print()
        else:
            print(f'❌ Invalid route format: {args.parse}')

    elif args.resolve:
        file_path = router.resolve_route(args.resolve)
        if file_path:
            print(f'\n✅ Resolved: {args.resolve}')
            print(f'   → {file_path}\n')
        else:
            print(f'❌ Route not found: {args.resolve}')

    elif args.register:
        if not args.file:
            print('Error: --file required for registration')
            exit(1)

        route_id = router.register_route(
            route=args.register,
            file_path=args.file,
            user_id=args.user_id
        )

        print(f'\n✅ Route registered!')
        print(f'   Route: {args.register}')
        print(f'   File: {args.file}')
        print(f'   ID: {route_id}\n')

    elif args.list:
        routes = router.list_routes(brand=args.brand)

        print(f'\n📋 Routes:\n')
        for route in routes:
            print(f'   {route["route"]}')
            print(f'      → {route["file_path"]}')
            print(f'      Brand: {route["brand"]} | Category: {route["category"]}')
            print()

        print(f'Total: {len(routes)} routes\n')

    elif args.brands:
        brands = router.list_brands()

        print(f'\n🏢 Brands:\n')
        for brand in brands:
            stats = router.get_brand_stats(brand)
            print(f'   @{brand}')
            print(f'      Routes: {stats["total_routes"]}')
            print(f'      Categories: {stats["total_categories"]}')
            print(f'      Contributors: {stats["total_contributors"]}')
            print()

    else:
        print('Usage: python3 folder_router.py --parse @soulfra/blog/post')
        print('       python3 folder_router.py --resolve @soulfra/blog/post')
        print('       python3 folder_router.py --register @soulfra/blog/new --file /path/to/file.md')
        print('       python3 folder_router.py --list --brand soulfra')
        print('       python3 folder_router.py --brands')

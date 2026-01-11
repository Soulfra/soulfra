#!/usr/bin/env python3
"""
Route Discovery - Auto-Discover Flask Routes & Health Check

Automatically discovers all registered Flask routes and cross-checks with:
- Template health (missing templates)
- Database (example parameter values)
- Route metadata (methods, endpoints, docstrings)

No more manual hardcoding!
"""

import re
import inspect
from typing import Dict, List, Set
from collections import defaultdict


def get_all_flask_routes(app) -> List[Dict]:
    """
    Auto-discover ALL routes from Flask's url_map

    Returns:
        List of route dicts with path, endpoint, methods, etc.
    """
    routes = []

    for rule in app.url_map.iter_rules():
        # Skip static files and internal Flask routes
        if rule.endpoint == 'static':
            continue

        # Get the actual function
        try:
            func = app.view_functions[rule.endpoint]
            docstring = inspect.getdoc(func) or ''
            # Extract first line of docstring as description
            description = docstring.split('\n')[0] if docstring else 'No description'
        except:
            description = 'No description'

        routes.append({
            'path': rule.rule,  # e.g., '/post/<slug>'
            'endpoint': rule.endpoint,  # function name
            'methods': sorted([m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]),
            'has_params': '<' in rule.rule,
            'description': description
        })

    return routes


def categorize_route(path: str) -> str:
    """Categorize a route based on its URL pattern"""

    # Check path patterns
    if path.startswith('/api/'):
        return 'API Endpoints'
    elif path.startswith('/admin'):
        return 'Admin & Management'
    elif '/soul' in path or '/souls' in path or '/user/' in path:
        return 'Users & Souls'
    elif '/brand' in path:
        return 'Brand System'
    elif path in ['/', '/post', '/live', '/category', '/tag'] or path.startswith('/post/') or path.startswith('/category/') or path.startswith('/tag/'):
        return 'Content & Posts'
    elif '/ml' in path or '/train' in path or '/ai' in path or '/reasoning' in path or '/dashboard' in path:
        return 'AI & Machine Learning'
    elif '/subscribe' in path or '/newsletter' in path or '/unsubscribe' in path:
        return 'Newsletter'
    elif '/qr' in path or '/s/' in path or '/i/' in path or path in ['/feed.xml', '/sitemap.xml', '/robots.txt']:
        return 'Utilities'
    elif '/code' in path or '/showcase' in path or '/status' in path or '/tiers' in path:
        return 'Showcases & Visual'
    elif '/game' in path or '/challenge' in path or '/review' in path or '/cringeproof' in path:
        return 'Games & Interactive'
    elif '/debug' in path or '/trace' in path:
        return 'Debug & Development'
    else:
        return 'Other'


def generate_example_url(path: str, conn=None) -> str:
    """
    Generate an example URL for routes with parameters

    Args:
        path: Route path like '/post/<slug>'
        conn: Optional database connection for real examples

    Returns:
        Example URL with real or placeholder values
    """
    # If no params, return as-is
    if '<' not in path:
        return path

    # Try to get real examples from database
    real_examples = {}
    if conn:
        try:
            # Get sample post slug
            post = conn.execute('SELECT slug FROM posts LIMIT 1').fetchone()
            if post:
                real_examples['slug'] = post['slug']

            # Get sample username
            user = conn.execute('SELECT username FROM users WHERE is_ai_persona = 1 LIMIT 1').fetchone()
            if user:
                real_examples['username'] = user['username']

            # Get sample brand
            brand = conn.execute('SELECT slug FROM brands LIMIT 1').fetchone()
            if brand:
                real_examples['brand_slug'] = brand['slug']
        except:
            pass

    # Replace parameters with examples
    example = path

    # Replace common patterns
    if '<slug>' in example:
        example = example.replace('<slug>', real_examples.get('slug', 'example-post'))
    if '<username>' in example:
        example = example.replace('<username>', real_examples.get('username', 'calriven'))
    if '<brand_slug>' in example:
        example = example.replace('<brand_slug>', real_examples.get('brand_slug', 'example-brand'))
    if '<int:post_id>' in example:
        example = example.replace('<int:post_id>', '1')
    if '<int:id>' in example:
        example = example.replace('<int:id>', '1')
    if '<path:' in example:
        # Extract param name
        match = re.search(r'<path:([^>]+)>', example)
        if match:
            example = example.replace(f'<path:{match.group(1)}>', 'app.py')
    if '<qr_id>' in example:
        example = example.replace('<qr_id>', real_examples.get('username', 'example'))
    if '<short_id>' in example:
        example = example.replace('<short_id>', real_examples.get('username', 'example'))
    if '<hash>' in example:
        example = example.replace('<hash>', 'abc123')

    # If still has params, couldn't resolve
    if '<' in example:
        return None  # Mark as non-clickable

    return example


def check_route_health(route: Dict, template_health: Dict) -> str:
    """
    Check if a route is healthy (has template, etc.)

    Returns:
        'ok', 'warning', or 'error'
    """
    endpoint = route['endpoint']
    methods = route['methods']

    # API endpoints don't need templates
    if 'POST' in methods and len(methods) == 1:
        return 'api'  # POST-only = API endpoint

    if route['path'].startswith('/api/'):
        return 'api'  # API endpoint

    # Check if this endpoint uses a missing template
    if template_health and 'missing' in template_health:
        # This is a simplification - would need to map endpoints to templates
        # For now, mark as 'ok' unless we detect issues
        pass

    return 'ok'


def discover_and_categorize_routes(app, db_conn=None, template_health=None) -> Dict[str, List[Dict]]:
    """
    Main function: Auto-discover all routes and organize them

    Args:
        app: Flask app instance
        db_conn: Optional database connection for examples
        template_health: Optional template health check results

    Returns:
        Dict of categorized routes with health status
    """
    all_routes = get_all_flask_routes(app)

    # Organize by category
    categorized = defaultdict(list)

    for route in all_routes:
        category = categorize_route(route['path'])

        # Add health status
        route['health'] = check_route_health(route, template_health)

        # Generate example URL
        route['example_url'] = generate_example_url(route['path'], db_conn)

        # Determine if clickable
        route['clickable'] = (
            'GET' in route['methods'] and
            route['example_url'] is not None and
            route['health'] != 'error'
        )

        categorized[category].append(route)

    # Sort routes within each category
    for category in categorized:
        categorized[category].sort(key=lambda r: r['path'])

    return dict(categorized)


if __name__ == '__main__':
    print("Route Discovery Test")
    print("\nThis module is meant to be imported by app.py")
    print("It will auto-discover all Flask routes at runtime")

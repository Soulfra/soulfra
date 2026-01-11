#!/usr/bin/env python3
"""
Website Structure Parser - Pure Python Stdlib

Extracts structured training data from:
- Sitemap routes (paths, methods, parameters)
- Jinja2 templates (variables, blocks, structure)
- Flask app routes
- Database schema

This data trains an ML model to understand website patterns and predict:
- Missing routes
- Template variables needed
- Route naming inconsistencies
- API documentation structure

Like: Training an AI on the website's DNA to understand its architecture!
"""

import os
import re
import json
from collections import defaultdict, Counter


def parse_route_pattern(route_path):
    """
    Parse Flask route into structured components

    Args:
        route_path: Flask route string (e.g., '/post/<slug>')

    Returns:
        dict: {
            'segments': ['post'],
            'parameters': [{'name': 'slug', 'type': 'string', 'position': 1}],
            'depth': 2,
            'has_params': True
        }

    Examples:
        >>> parse_route_pattern('/post/<slug>')
        {'segments': ['post'], 'parameters': [{'name': 'slug', 'type': 'string', 'position': 1}], ...}

        >>> parse_route_pattern('/api/posts/<int:id>')
        {'segments': ['api', 'posts'], 'parameters': [{'name': 'id', 'type': 'int', 'position': 2}], ...}
    """
    # Remove leading/trailing slashes
    path = route_path.strip('/')

    if not path:
        return {
            'segments': [],
            'parameters': [],
            'depth': 0,
            'has_params': False
        }

    parts = path.split('/')
    segments = []
    parameters = []

    for i, part in enumerate(parts):
        # Check if it's a parameter (e.g., <slug>, <int:id>)
        param_match = re.match(r'<(?:(\w+):)?(\w+)>', part)

        if param_match:
            param_type = param_match.group(1) or 'string'
            param_name = param_match.group(2)

            parameters.append({
                'name': param_name,
                'type': param_type,
                'position': i
            })
        else:
            segments.append(part)

    return {
        'segments': segments,
        'parameters': parameters,
        'depth': len(parts),
        'has_params': len(parameters) > 0
    }


def extract_route_features(route_data):
    """
    Extract ML training features from route data

    Args:
        route_data: dict with 'path', 'method', 'desc'

    Returns:
        dict: Feature vector for ML training

    Features extracted:
    - Path segments (tokenized)
    - HTTP method
    - Parameter types and names
    - Route depth
    - Description keywords
    """
    pattern = parse_route_pattern(route_data['path'])

    features = {
        # Path features
        'segments': ' '.join(pattern['segments']),
        'segment_count': len(pattern['segments']),
        'depth': pattern['depth'],

        # Parameter features
        'has_params': pattern['has_params'],
        'param_count': len(pattern['parameters']),
        'param_names': ' '.join([p['name'] for p in pattern['parameters']]),
        'param_types': ' '.join([p['type'] for p in pattern['parameters']]),

        # HTTP method
        'method': route_data['method'],

        # Description features (tokenized)
        'desc_words': tokenize_description(route_data.get('desc', '')),

        # Route type classification
        'route_type': classify_route_type(route_data['path']),
    }

    return features


def tokenize_description(description):
    """
    Tokenize description into keywords

    Args:
        description: Route description string

    Returns:
        str: Space-separated keywords
    """
    # Convert to lowercase
    words = description.lower().split()

    # Remove common stop words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'for', 'with', 'from', 'to', 'of', 'in', 'on'}
    keywords = [w for w in words if w not in stop_words]

    return ' '.join(keywords)


def classify_route_type(route_path):
    """
    Classify route into type category

    Args:
        route_path: Flask route path

    Returns:
        str: Route type (api, admin, content, user, utility, static)
    """
    path_lower = route_path.lower()

    if path_lower.startswith('/api/'):
        return 'api'
    elif path_lower.startswith('/admin'):
        return 'admin'
    elif '/post' in path_lower or '/category' in path_lower or '/tag' in path_lower:
        return 'content'
    elif '/user' in path_lower or '/soul' in path_lower or '/login' in path_lower:
        return 'user'
    elif path_lower.startswith('/static/') or path_lower.startswith('/i/'):
        return 'static'
    else:
        return 'utility'


def parse_jinja2_template(template_path):
    """
    Parse Jinja2 template to extract variables and structure

    Args:
        template_path: Path to .html template file

    Returns:
        dict: {
            'variables': ['user', 'posts', 'title'],
            'blocks': ['title', 'content'],
            'extends': 'base.html',
            'includes': ['partials/header.html'],
            'filters_used': ['length', 'upper'],
            'has_loops': True,
            'has_conditionals': True
        }
    """
    try:
        with open(template_path, 'r') as f:
            content = f.read()
    except:
        return None

    # Extract variables {{ variable }}
    variables = set(re.findall(r'\{\{\s*(\w+)', content))

    # Extract blocks {% block name %}
    blocks = re.findall(r'\{%\s*block\s+(\w+)', content)

    # Extract extends
    extends_match = re.search(r'\{%\s*extends\s+["\']([^"\']+)["\']', content)
    extends = extends_match.group(1) if extends_match else None

    # Extract includes
    includes = re.findall(r'\{%\s*include\s+["\']([^"\']+)["\']', content)

    # Extract filters used (e.g., {{ var|filter }})
    filters = set(re.findall(r'\|(\w+)', content))

    # Check for control structures
    has_loops = bool(re.search(r'\{%\s*for\s+', content))
    has_conditionals = bool(re.search(r'\{%\s*if\s+', content))

    return {
        'variables': list(variables),
        'variable_count': len(variables),
        'blocks': blocks,
        'extends': extends,
        'includes': includes,
        'filters_used': list(filters),
        'has_loops': has_loops,
        'has_conditionals': has_conditionals,
        'complexity': len(variables) + len(blocks) + len(includes)
    }


def extract_sitemap_from_app():
    """
    Extract sitemap data from app.py route definitions

    Returns:
        list: Route data dictionaries
    """
    # This reads the hardcoded ROUTES dict from api_game.py
    # In production, could parse app.py directly or use Flask's url_map

    from api_game import ROUTES

    all_routes = []

    for category, routes in ROUTES.items():
        for route in routes:
            all_routes.append({
                'category': category,
                'path': route['path'],
                'method': route['method'],
                'desc': route['desc']
            })

    return all_routes


def build_training_dataset():
    """
    Build complete training dataset from website structure

    Returns:
        dict: {
            'routes': [...],
            'templates': {...},
            'patterns': {...},
            'statistics': {...}
        }
    """
    # Extract routes
    routes = extract_sitemap_from_app()

    # Extract features from each route
    route_features = []
    for route in routes:
        features = extract_route_features(route)
        features['full_path'] = route['path']
        features['category'] = route['category']
        route_features.append(features)

    # Parse templates
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    templates = {}

    if os.path.exists(template_dir):
        for filename in os.listdir(template_dir):
            if filename.endswith('.html'):
                template_path = os.path.join(template_dir, filename)
                template_data = parse_jinja2_template(template_path)
                if template_data:
                    templates[filename] = template_data

    # Extract patterns
    patterns = analyze_patterns(route_features, templates)

    # Calculate statistics
    statistics = {
        'total_routes': len(routes),
        'total_templates': len(templates),
        'routes_by_method': Counter([r['method'] for r in routes]),
        'routes_by_category': Counter([r['category'] for r in routes]),
        'routes_by_type': Counter([f['route_type'] for f in route_features]),
        'avg_route_depth': sum(f['depth'] for f in route_features) / len(route_features) if route_features else 0,
        'routes_with_params': sum(1 for f in route_features if f['has_params']),
        'parameter_types': Counter(
            [pt for f in route_features for pt in f['param_types'].split() if pt]
        ),
    }

    return {
        'routes': route_features,
        'templates': templates,
        'patterns': patterns,
        'statistics': statistics
    }


def analyze_patterns(route_features, templates):
    """
    Analyze patterns in routes and templates

    Args:
        route_features: List of route feature dicts
        templates: Dict of template data

    Returns:
        dict: Detected patterns
    """
    patterns = {
        'common_segments': Counter(),
        'common_parameters': Counter(),
        'method_by_depth': defaultdict(Counter),
        'template_variable_patterns': defaultdict(int)
    }

    # Analyze route patterns
    for route in route_features:
        # Count segment frequency
        for segment in route['segments'].split():
            if segment:
                patterns['common_segments'][segment] += 1

        # Count parameter name frequency
        for param in route['param_names'].split():
            if param:
                patterns['common_parameters'][param] += 1

        # Method usage by route depth
        patterns['method_by_depth'][route['depth']][route['method']] += 1

    # Analyze template patterns
    for template_name, template_data in templates.items():
        for var in template_data['variables']:
            patterns['template_variable_patterns'][var] += 1

    # Convert defaultdicts to regular dicts for JSON serialization
    patterns['method_by_depth'] = {
        depth: dict(methods) for depth, methods in patterns['method_by_depth'].items()
    }

    return patterns


def predict_missing_routes(training_data):
    """
    Predict missing routes based on learned patterns

    Args:
        training_data: Output from build_training_dataset()

    Returns:
        list: Suggested missing routes

    Logic:
    - If there's a GET /posts but no POST /posts, suggest it
    - If there's /user/<username> but no /user/<username>/edit, suggest it
    - If there's an API endpoint but no corresponding page, suggest it
    """
    suggestions = []

    routes = training_data['routes']
    route_paths = {r['full_path']: r for r in routes}

    # Check for CRUD completeness
    # For each resource, check if all CRUD operations exist
    resources = defaultdict(set)

    for route in routes:
        # Extract base resource (e.g., '/posts' from '/posts/<id>')
        path_parts = route['full_path'].strip('/').split('/')
        if path_parts and not path_parts[0].startswith('<'):
            base = '/' + path_parts[0]
            resources[base].add(route['method'])

    # Suggest missing CRUD operations
    for resource, methods in resources.items():
        if 'GET' in methods and 'POST' not in methods:
            suggestions.append({
                'path': resource,
                'method': 'POST',
                'reason': f'Has GET {resource} but missing POST for creation',
                'confidence': 0.8
            })

        if 'GET' in methods and 'DELETE' not in methods and resource.startswith('/admin'):
            suggestions.append({
                'path': resource + '/<int:id>',
                'method': 'DELETE',
                'reason': f'Admin resource {resource} missing DELETE endpoint',
                'confidence': 0.6
            })

    # Check for missing detail pages
    for route in routes:
        if route['route_type'] == 'content' and not route['has_params']:
            # List page exists, check if detail page exists
            detail_path = route['full_path'] + '/<slug>'
            if detail_path not in route_paths:
                suggestions.append({
                    'path': detail_path,
                    'method': 'GET',
                    'reason': f'Has list page {route["full_path"]}, missing detail page',
                    'confidence': 0.7
                })

    return suggestions


def save_training_data(filename='website_structure_training.json'):
    """
    Build and save training dataset to JSON file

    Args:
        filename: Output JSON filename

    Returns:
        str: Path to saved file
    """
    training_data = build_training_dataset()

    # Add predictions
    training_data['predicted_missing_routes'] = predict_missing_routes(training_data)

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), filename)

    with open(output_path, 'w') as f:
        json.dump(training_data, f, indent=2)

    return output_path


def main():
    """CLI interface"""
    print("Website Structure Parser - Extract ML Training Data")
    print("=" * 60)
    print()

    # Build dataset
    print("📊 Building training dataset...")
    training_data = build_training_dataset()

    # Print statistics
    stats = training_data['statistics']
    print(f"✅ Extracted {stats['total_routes']} routes")
    print(f"✅ Parsed {stats['total_templates']} templates")
    print()

    print("📈 Statistics:")
    print(f"  Routes by method: {dict(stats['routes_by_method'])}")
    print(f"  Routes by type: {dict(stats['routes_by_type'])}")
    print(f"  Average route depth: {stats['avg_route_depth']:.1f}")
    print(f"  Routes with parameters: {stats['routes_with_params']}")
    print()

    # Show patterns
    print("🔍 Detected Patterns:")
    patterns = training_data['patterns']
    print(f"  Most common segments: {patterns['common_segments'].most_common(5)}")
    print(f"  Most common parameters: {patterns['common_parameters'].most_common(5)}")
    print()

    # Predict missing routes
    print("🤖 Predicting missing routes...")
    predictions = predict_missing_routes(training_data)

    if predictions:
        print(f"  Found {len(predictions)} suggestions:")
        for pred in predictions[:5]:
            print(f"    {pred['method']:6} {pred['path']:40} ({pred['confidence']:.0%} confidence)")
            print(f"           → {pred['reason']}")
    else:
        print("  No missing routes detected!")
    print()

    # Save dataset
    output_path = save_training_data()
    print(f"💾 Saved training data to: {output_path}")
    print()

    # Show sample route features
    print("📋 Sample Route Features:")
    for route in training_data['routes'][:3]:
        print(f"  {route['full_path']}")
        print(f"    Method: {route['method']}, Type: {route['route_type']}, Depth: {route['depth']}")
        print(f"    Segments: {route['segments']}")
        if route['param_names']:
            print(f"    Parameters: {route['param_names']} ({route['param_types']})")
        print()


if __name__ == '__main__':
    main()

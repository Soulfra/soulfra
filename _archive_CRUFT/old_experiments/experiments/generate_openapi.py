#!/usr/bin/env python3
"""
Generate OpenAPI Specification from Migrations + App Routes

Proves "Schema is Code" by generating API documentation from:
1. Database migrations (data model)
2. Flask routes (API endpoints)
3. Existing API schema JSON

Output: openapi.yaml - standard API documentation

This enables:
- Auto-generated API clients
- API testing tools (Postman, Insomnia)
- Documentation sites (Swagger UI)
- Schema validation

Teaching the pattern: Code → Spec (not Spec → Code)
"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime


def parse_migrations_to_schema():
    """
    Parse SQL migrations into OpenAPI schema components

    Returns:
        dict: OpenAPI schema definitions for each table
    """
    migrations_dir = Path('migrations')
    schemas = {}

    for migration_file in sorted(migrations_dir.glob('*.sql')):
        with open(migration_file, 'r') as f:
            sql = f.read()

        # Extract CREATE TABLE statements
        table_pattern = r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\((.*?)\);'

        for match in re.finditer(table_pattern, sql, re.DOTALL | re.IGNORECASE):
            table_name = match.group(1)
            columns_sql = match.group(2)

            # Skip internal tables
            if table_name in ['schema_migrations', 'sqlite_sequence']:
                continue

            # Parse columns
            properties = {}
            required_fields = []

            column_lines = [line.strip() for line in columns_sql.split(',')]

            for line in column_lines:
                # Skip constraints (FOREIGN KEY, PRIMARY KEY, etc.)
                if any(keyword in line.upper() for keyword in ['FOREIGN KEY', 'PRIMARY KEY', 'INDEX', 'UNIQUE', 'CHECK']):
                    continue

                # Parse column definition
                parts = line.split()
                if len(parts) < 2:
                    continue

                col_name = parts[0]
                col_type = parts[1].upper()

                # Map SQL types to OpenAPI types
                type_mapping = {
                    'INTEGER': {'type': 'integer'},
                    'TEXT': {'type': 'string'},
                    'REAL': {'type': 'number', 'format': 'float'},
                    'BOOLEAN': {'type': 'boolean'},
                    'TIMESTAMP': {'type': 'string', 'format': 'date-time'},
                    'BLOB': {'type': 'string', 'format': 'byte'}
                }

                openapi_type = type_mapping.get(col_type, {'type': 'string'})
                properties[col_name] = openapi_type

                # Check if required
                if 'NOT NULL' in line.upper() or 'REQUIRED' in line.upper():
                    required_fields.append(col_name)

            # Create schema
            schemas[table_name] = {
                'type': 'object',
                'properties': properties,
                'required': required_fields if required_fields else None
            }

    return schemas


def extract_api_routes_from_app():
    """
    Extract API routes from app.py

    Returns:
        dict: OpenAPI paths for each route
    """
    with open('app.py', 'r') as f:
        app_code = f.read()

    paths = {}

    # Extract @app.route patterns
    route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)'

    for match in re.finditer(route_pattern, app_code):
        path = match.group(1)
        methods_str = match.group(2)
        methods = ['GET']  # default

        if methods_str:
            methods = [m.strip().strip('\'"') for m in methods_str.split(',')]

        # Only document /api/* routes
        if not path.startswith('/api/'):
            continue

        # Create OpenAPI path entry
        if path not in paths:
            paths[path] = {}

        for method in methods:
            method_lower = method.lower()

            paths[path][method_lower] = {
                'summary': f'{method} {path}',
                'responses': {
                    '200': {
                        'description': 'Successful response',
                        'content': {
                            'application/json': {
                                'schema': {'type': 'object'}
                            }
                        }
                    }
                }
            }

    return paths


def generate_openapi_spec():
    """
    Generate complete OpenAPI 3.0 specification

    Returns:
        dict: OpenAPI specification
    """
    # Parse schemas from migrations
    schemas = parse_migrations_to_schema()

    # Extract API routes
    paths = extract_api_routes_from_app()

    # Build OpenAPI spec
    spec = {
        'openapi': '3.0.0',
        'info': {
            'title': 'Soulfra API',
            'version': '1.0.0',
            'description': '''
Soulfra Platform API

Generated from:
- Database migrations (migrations/*.sql)
- Flask routes (app.py)

This spec is auto-generated from code, proving "Schema is Code".

Distribution:
- Email newsletters (SMTP)
- RSS feeds (/feed.xml)
- Git repository (fork = copy platform)
- Static HTML (GitHub Pages)

The platform is distributed via email + git, not centralized hosting.
            ''',
            'contact': {
                'name': 'Soulfra',
                'url': 'https://github.com/soulfra/soulfra-simple'
            }
        },
        'servers': [
            {
                'url': 'http://localhost:5001',
                'description': 'Local development'
            },
            {
                'url': '{BASE_URL}',
                'description': 'Configurable deployment',
                'variables': {
                    'BASE_URL': {
                        'default': 'http://localhost:5001',
                        'description': 'Set via BASE_URL environment variable'
                    }
                }
            }
        ],
        'paths': paths,
        'components': {
            'schemas': schemas
        },
        'tags': [
            {
                'name': 'posts',
                'description': 'Blog posts and content'
            },
            {
                'name': 'reasoning',
                'description': 'AI reasoning threads and steps'
            },
            {
                'name': 'feedback',
                'description': 'User feedback and bug reports'
            },
            {
                'name': 'health',
                'description': 'System health and status'
            }
        ]
    }

    return spec


def save_openapi_spec():
    """Save OpenAPI spec as YAML and JSON"""
    spec = generate_openapi_spec()

    # Save as YAML
    with open('openapi.yaml', 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    # Save as JSON
    import json
    with open('openapi.json', 'w') as f:
        json.dump(spec, f, indent=2)

    print("=" * 70)
    print("✅ OpenAPI Specification Generated")
    print("=" * 70)
    print()
    print(f"📄 openapi.yaml - {os.path.getsize('openapi.yaml')} bytes")
    print(f"📄 openapi.json - {os.path.getsize('openapi.json')} bytes")
    print()
    print("Generated from:")
    print("  • migrations/*.sql (database schema)")
    print("  • app.py (API routes)")
    print()
    print(f"Tables documented: {len(spec['components']['schemas'])}")
    print(f"API endpoints: {len(spec['paths'])}")
    print()
    print("Use with:")
    print("  • Swagger UI: https://editor.swagger.io")
    print("  • Postman: Import openapi.json")
    print("  • OpenAPI Generator: generate clients")
    print()


if __name__ == '__main__':
    save_openapi_spec()

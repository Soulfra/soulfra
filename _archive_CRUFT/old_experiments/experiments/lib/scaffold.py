#!/usr/bin/env python3
"""
Scaffold - Code Generator for Routes, Services, CRUD (Zero Dependencies)

Generates Flask routes, database operations, and service templates from scratch.
Teaches tier system by showing how complex features build from primitives.

Philosophy: Don't write boilerplate. Generate it from patterns.

Usage:
    from lib.scaffold import generate_crud_route, generate_api_endpoint

    # Generate CRUD routes for a model
    code = generate_crud_route('products', ['name', 'price', 'description'])

    # Generate API endpoint
    code = generate_api_endpoint('search', ['query', 'limit'])

Tier System Teaching:
TIER 0: Database schema (tables, columns)
TIER 1: CRUD operations (SELECT, INSERT, UPDATE, DELETE)
TIER 2: Routes (Flask endpoints)
TIER 3: Services (business logic)
TIER 4: Workflows (multi-step operations)
"""

import re
from typing import List, Dict, Optional


# ==============================================================================
# TIER 1: DATABASE CRUD GENERATORS
# ==============================================================================

def generate_crud_operations(table_name: str, columns: List[str]) -> str:
    """
    Generate CRUD operations for a database table

    Args:
        table_name: Name of the table
        columns: List of column names (excluding id)

    Returns:
        Python code string with CRUD functions

    Example:
        >>> code = generate_crud_operations('products', ['name', 'price'])
        >>> print(code)
        def create_product(name, price):
            ...
    """
    # Column placeholders
    col_list = ', '.join(columns)
    col_params = ', '.join([f':{col}' for col in columns])
    col_args = ', '.join(columns)

    code = f'''
def create_{table_name[:-1]}({col_args}):
    """Create a new {table_name[:-1]}"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO {table_name} ({col_list})
        VALUES ({col_params})
    """, {{{', '.join([f"'{col}': {col}" for col in columns])}}})

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return new_id


def get_{table_name[:-1]}(id):
    """Get a {table_name[:-1]} by ID"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM {table_name} WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_all_{table_name}(limit=100, offset=0):
    """Get all {table_name}"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM {table_name}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_{table_name[:-1]}(id, {col_args}):
    """Update a {table_name[:-1]}"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE {table_name}
        SET {', '.join([f'{col} = :{col}' for col in columns])}
        WHERE id = :id
    """, {{{', '.join([f"'{col}': {col}" for col in columns])}, 'id': id}})

    conn.commit()
    conn.close()

    return cursor.rowcount > 0


def delete_{table_name[:-1]}(id):
    """Delete a {table_name[:-1]}"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM {table_name} WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return cursor.rowcount > 0
'''

    return code.strip()


# ==============================================================================
# TIER 2: FLASK ROUTE GENERATORS
# ==============================================================================

def generate_crud_route(resource_name: str, columns: List[str]) -> str:
    """
    Generate Flask CRUD routes for a resource

    Args:
        resource_name: Name of the resource (e.g., 'products')
        columns: List of column names

    Returns:
        Python code string with Flask routes

    Example:
        >>> code = generate_crud_route('products', ['name', 'price'])
        >>> # Generates: /api/products (GET, POST), /api/products/<id> (GET, PUT, DELETE)
    """
    singular = resource_name[:-1] if resource_name.endswith('s') else resource_name

    code = f'''
@app.route('/api/{resource_name}', methods=['GET'])
def get_{resource_name}():
    """Get all {resource_name}"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    items = get_all_{resource_name}(limit=limit, offset=offset)

    return jsonify({{
        'success': True,
        'data': items,
        'count': len(items)
    }})


@app.route('/api/{resource_name}', methods=['POST'])
def create_{singular}():
    """Create a new {singular}"""
    data = request.get_json()

    # Validate required fields
    required_fields = {[repr(col) for col in columns]}
    missing_fields = [f for f in required_fields if f not in data]

    if missing_fields:
        return jsonify({{
            'success': False,
            'error': f'Missing required fields: {{", ".join(missing_fields)}}'
        }}), 400

    # Create {singular}
    new_id = create_{singular}({', '.join([f"data['{col}']" for col in columns])})

    return jsonify({{
        'success': True,
        'data': {{'id': new_id}},
        'message': '{singular.title()} created successfully'
    }}), 201


@app.route('/api/{resource_name}/<int:id>', methods=['GET'])
def get_{singular}_by_id(id):
    """Get a {singular} by ID"""
    item = get_{singular}(id)

    if not item:
        return jsonify({{
            'success': False,
            'error': '{singular.title()} not found'
        }}), 404

    return jsonify({{
        'success': True,
        'data': item
    }})


@app.route('/api/{resource_name}/<int:id>', methods=['PUT'])
def update_{singular}_by_id(id):
    """Update a {singular}"""
    data = request.get_json()

    # Check if {singular} exists
    existing = get_{singular}(id)
    if not existing:
        return jsonify({{
            'success': False,
            'error': '{singular.title()} not found'
        }}), 404

    # Update {singular}
    success = update_{singular}(id, {', '.join([f"data.get('{col}', existing['{col}'])" for col in columns])})

    if success:
        return jsonify({{
            'success': True,
            'message': '{singular.title()} updated successfully'
        }})
    else:
        return jsonify({{
            'success': False,
            'error': 'Failed to update {singular}'
        }}), 500


@app.route('/api/{resource_name}/<int:id>', methods=['DELETE'])
def delete_{singular}_by_id(id):
    """Delete a {singular}"""
    success = delete_{singular}(id)

    if success:
        return jsonify({{
            'success': True,
            'message': '{singular.title()} deleted successfully'
        }})
    else:
        return jsonify({{
            'success': False,
            'error': '{singular.title()} not found'
        }}), 404
'''

    return code.strip()


def generate_api_endpoint(endpoint_name: str, params: List[str], description: str = "") -> str:
    """
    Generate a single API endpoint

    Args:
        endpoint_name: Name of the endpoint (e.g., 'search')
        params: List of parameter names
        description: Optional description

    Returns:
        Python code string with Flask route

    Example:
        >>> code = generate_api_endpoint('search', ['query', 'limit'])
    """
    code = f'''
@app.route('/api/{endpoint_name}', methods=['POST'])
def {endpoint_name}_endpoint():
    """{description or f'{endpoint_name.title()} endpoint'}"""
    data = request.get_json()

    # Validate parameters
    required_params = {[repr(p) for p in params]}
    missing_params = [p for p in required_params if p not in data]

    if missing_params:
        return jsonify({{
            'success': False,
            'error': f'Missing required parameters: {{", ".join(missing_params)}}'
        }}), 400

    # Extract parameters
{chr(10).join([f"    {param} = data['{param}']" for param in params])}

    # TODO: Implement {endpoint_name} logic here
    result = {{}}

    return jsonify({{
        'success': True,
        'data': result
    }})
'''

    return code.strip()


# ==============================================================================
# TIER 3: SERVICE GENERATORS
# ==============================================================================

def generate_service_class(service_name: str, methods: List[Dict[str, str]]) -> str:
    """
    Generate a service class

    Args:
        service_name: Name of the service (e.g., 'EmailService')
        methods: List of method definitions
                 [{'name': 'send_email', 'params': ['to', 'subject', 'body']}]

    Returns:
        Python code string with service class

    Example:
        >>> code = generate_service_class('EmailService', [
        ...     {'name': 'send_email', 'params': ['to', 'subject', 'body']}
        ... ])
    """
    method_code = []

    for method in methods:
        method_name = method['name']
        params = method.get('params', [])
        params_str = ', '.join(params)

        method_code.append(f'''
    def {method_name}(self, {params_str}):
        """
        {method_name.replace('_', ' ').title()}

        Args:
{chr(10).join([f"            {param}: TODO" for param in params])}

        Returns:
            dict: {{'success': bool, 'data': ...}}
        """
        # TODO: Implement {method_name}
        return {{'success': True, 'data': None}}
''')

    code = f'''
class {service_name}:
    """
    {service_name} - Service layer for {service_name.replace('Service', '').lower()} operations

    Tier System:
    - Uses CRUD operations (Tier 1)
    - Provides business logic (Tier 3)
    - Called by routes (Tier 2) or workflows (Tier 4)
    """

    def __init__(self):
        """Initialize {service_name}"""
        pass

{''.join(method_code)}
'''

    return code.strip()


# ==============================================================================
# TIER 4: WORKFLOW GENERATORS
# ==============================================================================

def generate_workflow(workflow_name: str, steps: List[str]) -> str:
    """
    Generate a workflow (multi-step operation)

    Args:
        workflow_name: Name of the workflow (e.g., 'publish_post')
        steps: List of step descriptions

    Returns:
        Python code string with workflow function

    Example:
        >>> code = generate_workflow('publish_post', [
        ...     'Validate post data',
        ...     'Save to database',
        ...     'Generate slug',
        ...     'Send notification'
        ... ])
    """
    step_code = []

    for i, step in enumerate(steps, 1):
        step_var = f"step{i}_result"
        step_code.append(f'''
    # Step {i}: {step}
    {step_var} = None  # TODO: Implement {step}
    if not {step_var}:
        return {{'success': False, 'error': 'Failed at step {i}: {step}'}}
''')

    code = f'''
def {workflow_name}():
    """
    {workflow_name.replace('_', ' ').title()} Workflow

    Multi-step operation (Tier 4):
{chr(10).join([f"    {i}. {step}" for i, step in enumerate(steps, 1)])}

    Returns:
        dict: {{'success': bool, 'data': ...}}
    """
{''.join(step_code)}

    return {{
        'success': True,
        'data': {{'message': '{workflow_name} completed successfully'}}
    }}
'''

    return code.strip()


# ==============================================================================
# FULL SCAFFOLD GENERATOR
# ==============================================================================

def generate_full_scaffold(resource_name: str, columns: List[str]) -> str:
    """
    Generate complete scaffold (CRUD + routes + service)

    Args:
        resource_name: Name of the resource (e.g., 'products')
        columns: List of column names

    Returns:
        Complete Python code with imports, CRUD, routes, and service

    Example:
        >>> code = generate_full_scaffold('products', ['name', 'price', 'description'])
        >>> print(code)
    """
    crud = generate_crud_operations(resource_name, columns)
    routes = generate_crud_route(resource_name, columns)

    code = f'''
"""
{resource_name.title()} - Auto-generated scaffold
Generated using lib/scaffold.py

Provides:
- Database CRUD operations (Tier 1)
- Flask API routes (Tier 2)
- Service layer (Tier 3)
"""

import sqlite3
from flask import jsonify, request


# ==============================================================================
# TIER 1: DATABASE CRUD OPERATIONS
# ==============================================================================

{crud}


# ==============================================================================
# TIER 2: FLASK ROUTES
# ==============================================================================

{routes}


# ==============================================================================
# USAGE
# ==============================================================================

# Add these routes to your Flask app:
#
# from {resource_name}_scaffold import *
#
# Or copy/paste the functions you need into app.py
'''

    return code.strip()


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Scaffold (Code Generator)\n")

    # Test 1: CRUD operations
    print("=" * 70)
    print("Test 1: Generate CRUD Operations")
    print("=" * 70)
    code = generate_crud_operations('products', ['name', 'price', 'description'])
    print(code[:500] + "...\n")

    # Test 2: Flask routes
    print("=" * 70)
    print("Test 2: Generate Flask Routes")
    print("=" * 70)
    code = generate_crud_route('products', ['name', 'price', 'description'])
    print(code[:500] + "...\n")

    # Test 3: API endpoint
    print("=" * 70)
    print("Test 3: Generate API Endpoint")
    print("=" * 70)
    code = generate_api_endpoint('search', ['query', 'limit'], "Search products by query")
    print(code + "\n")

    # Test 4: Service class
    print("=" * 70)
    print("Test 4: Generate Service Class")
    print("=" * 70)
    code = generate_service_class('ProductService', [
        {'name': 'create_product', 'params': ['name', 'price']},
        {'name': 'get_product', 'params': ['id']},
    ])
    print(code[:500] + "...\n")

    # Test 5: Workflow
    print("=" * 70)
    print("Test 5: Generate Workflow")
    print("=" * 70)
    code = generate_workflow('publish_product', [
        'Validate product data',
        'Save to database',
        'Generate product feed',
        'Send notification'
    ])
    print(code + "\n")

    # Test 6: Full scaffold
    print("=" * 70)
    print("Test 6: Generate Full Scaffold")
    print("=" * 70)
    code = generate_full_scaffold('items', ['name', 'value'])
    print(code[:700] + "...\n")

    print("✅ Scaffold tests complete!")
    print("\n💡 Use generate_full_scaffold() to create complete CRUD APIs!")

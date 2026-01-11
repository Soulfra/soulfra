#!/usr/bin/env python3
"""
PRE-COMMIT TEST SUITE - Run this BEFORE every git commit

Catches:
- Syntax errors
- Import errors
- Missing dependencies
- Route failures
- Template errors
- Database schema issues

Philosophy:
----------
NO MORE SQLITE ERRORS!
NO MORE INDENTATION ERRORS!
NO MORE BROKEN ROUTES!

Test BEFORE we commit, NOT after users see it broken.

Usage:
    # Test everything
    python3 test_before_commit.py

    # Test specific component
    python3 test_before_commit.py --syntax
    python3 test_before_commit.py --routes
    python3 test_before_commit.py --imports

    # Auto-run before git commit
    git config core.hooksPath .githooks
"""

import sys
import importlib
import sqlite3
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

passed = 0
failed = 0
warnings = 0


def test_print(message, status='info'):
    """Print test result with color"""
    global passed, failed, warnings

    if status == 'pass':
        print(f"{GREEN}✅ {message}{RESET}")
        passed += 1
    elif status == 'fail':
        print(f"{RED}❌ {message}{RESET}")
        failed += 1
    elif status == 'warn':
        print(f"{YELLOW}⚠️  {message}{RESET}")
        warnings += 1
    else:
        print(f"{BLUE}ℹ️  {message}{RESET}")


def test_syntax():
    """Test that all Python files have valid syntax"""
    test_print("Testing Python syntax...", 'info')

    python_files = [
        'app.py',
        'database.py',
        'neural_proxy.py',
        'story_pipeline_tracer.py',
        'contribution_validator.py',
        'neural_network.py',
        'migrate_brand_evolution.py',
        'seed_brands.py'
    ]

    for filename in python_files:
        try:
            with open(filename, 'r') as f:
                compile(f.read(), filename, 'exec')
            test_print(f"{filename} - syntax valid", 'pass')
        except SyntaxError as e:
            test_print(f"{filename} - SYNTAX ERROR: {e}", 'fail')
        except FileNotFoundError:
            test_print(f"{filename} - file not found (skipping)", 'warn')


def test_imports():
    """Test that critical modules can be imported"""
    test_print("Testing imports...", 'info')

    critical_imports = [
        'database',
        'neural_proxy',
        'story_pipeline_tracer',
        'contribution_validator',
    ]

    for module_name in critical_imports:
        try:
            # Save stdout to suppress module print statements
            import io
            import contextlib

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                importlib.import_module(module_name)

            test_print(f"{module_name} - imports successfully", 'pass')
        except ImportError as e:
            test_print(f"{module_name} - IMPORT ERROR: {e}", 'fail')
        except Exception as e:
            test_print(f"{module_name} - ERROR: {e}", 'fail')


def test_database_schema():
    """Test that database schema is valid"""
    test_print("Testing database schema...", 'info')

    required_tables = [
        'brands',
        'neural_networks',
        'pipeline_traces',
        'brand_territory',
        'user_brand_loyalty',
        'contribution_scores'
    ]

    try:
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in required_tables:
            if table in existing_tables:
                test_print(f"Table '{table}' exists", 'pass')
            else:
                test_print(f"Table '{table}' MISSING", 'fail')

        conn.close()
    except Exception as e:
        test_print(f"Database check failed: {e}", 'fail')


def test_routes():
    """Test that Flask routes can be registered"""
    test_print("Testing Flask routes...", 'info')

    try:
        # Import app (will register all routes)
        import io
        import contextlib

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            import app as flask_app

        # Check critical routes exist
        critical_routes = [
            '/brand-arena',
            '/api/validate-contribution',
            '/ai-frontend',
            '/traces',
            '/trace/<trace_id>'
        ]

        # Get all registered routes
        routes = []
        for rule in flask_app.app.url_map.iter_rules():
            routes.append(str(rule))

        for route in critical_routes:
            # Check if route pattern exists (handle <variables>)
            route_pattern = route.replace('<trace_id>', '<string:trace_id>')
            found = any(route_pattern in r or route in r for r in routes)

            if found:
                test_print(f"Route {route} registered", 'pass')
            else:
                test_print(f"Route {route} NOT FOUND", 'fail')

    except Exception as e:
        test_print(f"Route testing failed: {e}", 'fail')


def test_neural_networks():
    """Test that neural networks can be loaded"""
    test_print("Testing neural networks...", 'info')

    try:
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()

        cursor.execute('SELECT model_name FROM neural_networks')
        networks = [row[0] for row in cursor.fetchall()]

        required_networks = [
            'calriven_technical_classifier',
            'deathtodata_privacy_classifier',
            'theauditor_validation_classifier'
        ]

        for network in required_networks:
            if network in networks:
                test_print(f"Network '{network}' exists", 'pass')
            else:
                test_print(f"Network '{network}' MISSING", 'warn')

        conn.close()
    except Exception as e:
        test_print(f"Neural network check failed: {e}", 'fail')


def test_contribution_validator():
    """Test contribution validation works"""
    test_print("Testing contribution validator...", 'info')

    try:
        from contribution_validator import validate_contribution

        # Test with a technical contribution
        result = validate_contribution(
            "This Python function implements a clean API with proper error handling",
            brand_id=4  # CalRiven
        )

        if 'on_brand_score' in result:
            test_print(f"Validation works (score: {result['on_brand_score']}/100)", 'pass')
        else:
            test_print("Validation returned invalid result", 'fail')

    except Exception as e:
        test_print(f"Validation test failed: {e}", 'fail')


def test_templates():
    """Test template library"""
    test_print("Testing template library...", 'info')

    try:
        from templates_lib import list_categories, list_templates, generate_template

        # Test that template registry loads
        categories = list_categories()
        if 'database' in categories:
            test_print("Template registry loaded successfully", 'pass')
        else:
            test_print("Template registry missing expected categories", 'fail')

        # Test template listing
        db_templates = list_templates('database')
        expected = ['migration', 'schema', 'seed', 'query', 'trigger', 'view']
        if all(t in db_templates.get('database', []) for t in expected):
            test_print(f"All {len(expected)} database templates registered", 'pass')
        else:
            test_print("Missing database templates", 'fail')

        # Test template generation
        migration = generate_template('database', 'migration',
                                     migration_name='test', number=1)
        if migration and 'CREATE TABLE' in migration:
            test_print("Template generation works", 'pass')
        else:
            test_print("Template generation failed", 'fail')

    except ImportError as e:
        test_print(f"Template library not found (OK if not installed): {e}", 'warn')
    except Exception as e:
        test_print(f"Template test failed: {e}", 'fail')


def print_summary():
    """Print test summary"""
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    print(f"{YELLOW}Warnings: {warnings}{RESET}")
    print()

    if failed > 0:
        print(f"{RED}❌ TESTS FAILED - DO NOT COMMIT!{RESET}")
        return False
    elif warnings > 0:
        print(f"{YELLOW}⚠️  TESTS PASSED WITH WARNINGS{RESET}")
        return True
    else:
        print(f"{GREEN}✅ ALL TESTS PASSED - SAFE TO COMMIT!{RESET}")
        return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Pre-commit test suite')
    parser.add_argument('--syntax', action='store_true', help='Test syntax only')
    parser.add_argument('--imports', action='store_true', help='Test imports only')
    parser.add_argument('--routes', action='store_true', help='Test routes only')
    parser.add_argument('--database', action='store_true', help='Test database only')
    parser.add_argument('--neural', action='store_true', help='Test neural networks only')
    parser.add_argument('--validator', action='store_true', help='Test validator only')
    parser.add_argument('--templates', action='store_true', help='Test template library only')

    args = parser.parse_args()

    # If no specific test requested, run all
    run_all = not any([args.syntax, args.imports, args.routes, args.database, args.neural, args.validator, args.templates])

    print()
    print("=" * 70)
    print("🧪 PRE-COMMIT TEST SUITE")
    print("=" * 70)
    print()

    if run_all or args.syntax:
        test_syntax()
        print()

    if run_all or args.imports:
        test_imports()
        print()

    if run_all or args.database:
        test_database_schema()
        print()

    if run_all or args.routes:
        test_routes()
        print()

    if run_all or args.neural:
        test_neural_networks()
        print()

    if run_all or args.validator:
        test_contribution_validator()
        print()

    if run_all or args.templates:
        test_templates()
        print()

    success = print_summary()
    sys.exit(0 if success else 1)

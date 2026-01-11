#!/usr/bin/env python3
"""
Test Templates Library

Tests for the modular template system (templates_lib/).

Run with: python3 test_templates_lib.py
"""

import sys
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


def test_registry_import():
    """Test that template registry can be imported"""
    test_print("Testing template registry import...", 'info')

    try:
        from templates_lib import (
            get_registry,
            list_templates,
            list_categories,
            get_template,
            generate_template,
            search_templates
        )
        test_print("Template registry imports successfully", 'pass')
        return True
    except ImportError as e:
        test_print(f"Failed to import template registry: {e}", 'fail')
        return False


def test_registry_initialization():
    """Test that registry initializes and loads modules"""
    test_print("Testing registry initialization...", 'info')

    try:
        from templates_lib import get_registry

        registry = get_registry()
        assert registry is not None, "Registry should not be None"
        assert hasattr(registry, 'templates'), "Registry should have templates attribute"

        test_print("Registry initializes successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"Registry initialization failed: {e}", 'fail')
        return False


def test_list_categories():
    """Test listing all template categories"""
    test_print("Testing list_categories()...", 'info')

    try:
        from templates_lib import list_categories

        categories = list_categories()
        assert isinstance(categories, list), "Should return a list"
        assert 'database' in categories, "Should include 'database' category"

        test_print(f"Found {len(categories)} categories: {categories}", 'pass')
        return True
    except Exception as e:
        test_print(f"list_categories() failed: {e}", 'fail')
        return False


def test_list_templates():
    """Test listing templates"""
    test_print("Testing list_templates()...", 'info')

    try:
        from templates_lib import list_templates

        # List all templates
        all_templates = list_templates()
        assert isinstance(all_templates, dict), "Should return a dict"
        assert 'database' in all_templates, "Should include database category"

        # List database templates
        db_templates = list_templates('database')
        assert 'database' in db_templates, "Should return database category"
        assert isinstance(db_templates['database'], list), "Should return list of template names"

        expected_db_templates = ['migration', 'schema', 'seed', 'query', 'trigger', 'view']
        for template_name in expected_db_templates:
            assert template_name in db_templates['database'], f"Should include '{template_name}'"

        test_print(f"Database templates: {db_templates['database']}", 'pass')
        return True
    except Exception as e:
        test_print(f"list_templates() failed: {e}", 'fail')
        return False


def test_get_template():
    """Test getting a specific template"""
    test_print("Testing get_template()...", 'info')

    try:
        from templates_lib import get_template

        # Get migration template
        template = get_template('database', 'migration')
        assert template is not None, "Should find migration template"
        assert template.category == 'database', "Should have correct category"
        assert template.name == 'migration', "Should have correct name"
        assert hasattr(template, 'generate'), "Should have generate method"
        assert hasattr(template, 'description'), "Should have description"

        # Try non-existent template
        missing = get_template('database', 'nonexistent')
        assert missing is None, "Should return None for missing template"

        test_print("get_template() works correctly", 'pass')
        return True
    except Exception as e:
        test_print(f"get_template() failed: {e}", 'fail')
        return False


def test_search_templates():
    """Test searching templates"""
    test_print("Testing search_templates()...", 'info')

    try:
        from templates_lib import search_templates

        # Search for 'migration'
        results = search_templates('migration')
        assert len(results) > 0, "Should find migration template"
        assert any(t.name == 'migration' for t in results), "Should include migration"

        # Search for 'sql'
        sql_results = search_templates('sql')
        assert len(sql_results) > 0, "Should find SQL-related templates"

        # Search for something that doesn't exist
        empty_results = search_templates('xyz123notfound')
        assert len(empty_results) == 0, "Should return empty list for no matches"

        test_print(f"Search found {len(results)} templates for 'migration'", 'pass')
        return True
    except Exception as e:
        test_print(f"search_templates() failed: {e}", 'fail')
        return False


def test_generate_migration():
    """Test generating a migration"""
    test_print("Testing migration generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate migration
        migration = generate_template('database', 'migration',
                                     migration_name='add_users',
                                     number=1)

        assert migration is not None, "Should generate migration"
        assert 'Migration 001' in migration, "Should include migration number"
        assert 'Add Users' in migration, "Should include migration name"
        assert 'CREATE TABLE' in migration, "Should include SQL example"

        test_print("Migration generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"Migration generation failed: {e}", 'fail')
        return False


def test_generate_schema():
    """Test generating a schema"""
    test_print("Testing schema generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate schema
        schema = generate_template('database', 'schema', table_name='users')

        assert schema is not None, "Should generate schema"
        assert 'CREATE TABLE IF NOT EXISTS users' in schema, "Should include table name"
        assert 'PRIMARY KEY' in schema, "Should include primary key"
        assert 'INDEX' in schema, "Should include index"

        test_print("Schema generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"Schema generation failed: {e}", 'fail')
        return False


def test_generate_seed():
    """Test generating seed data"""
    test_print("Testing seed data generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate seed
        seed = generate_template('database', 'seed', table_name='users')

        assert seed is not None, "Should generate seed"
        assert 'INSERT' in seed, "Should include INSERT"
        assert 'users' in seed, "Should include table name"
        assert 'OR IGNORE' in seed, "Should be idempotent"

        test_print("Seed data generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"Seed generation failed: {e}", 'fail')
        return False


def test_generate_query():
    """Test generating a query"""
    test_print("Testing query generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate query
        query = generate_template('database', 'query',
                                 query_name='get_active_users',
                                 description='Get all active users')

        assert query is not None, "Should generate query"
        assert 'SELECT' in query, "Should include SELECT"
        assert 'Get all active users' in query, "Should include description"

        test_print("Query generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"Query generation failed: {e}", 'fail')
        return False


def test_generate_trigger():
    """Test generating a trigger"""
    test_print("Testing trigger generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate trigger
        trigger = generate_template('database', 'trigger',
                                   table_name='users',
                                   trigger_type='AFTER INSERT')

        assert trigger is not None, "Should generate trigger"
        assert 'CREATE TRIGGER' in trigger, "Should include CREATE TRIGGER"
        assert 'AFTER INSERT' in trigger, "Should include trigger type"
        assert 'users' in trigger, "Should include table name"

        test_print("Trigger generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"Trigger generation failed: {e}", 'fail')
        return False


def test_generate_view():
    """Test generating a view"""
    test_print("Testing view generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate view
        view = generate_template('database', 'view',
                                view_name='active_users',
                                description='View of active users')

        assert view is not None, "Should generate view"
        assert 'CREATE VIEW' in view, "Should include CREATE VIEW"
        assert 'active_users' in view, "Should include view name"
        assert 'View of active users' in view, "Should include description"

        test_print("View generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"View generation failed: {e}", 'fail')
        return False


def test_syntax_validation():
    """Test that generated SQL has basic syntax validity"""
    test_print("Testing SQL syntax validation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate various templates and check for SQL keywords
        migration = generate_template('database', 'migration', migration_name='test', number=1)
        schema = generate_template('database', 'schema', table_name='test')
        seed = generate_template('database', 'seed', table_name='test')

        # Check that they don't have obvious syntax errors
        assert 'CREATE TABLE' in schema or 'CREATE' in migration, "Should have CREATE"
        assert 'INSERT' in seed, "Should have INSERT"

        # Check for SQL comments
        assert '--' in migration, "Should have SQL comments"

        test_print("Generated SQL appears syntactically valid", 'pass')
        return True
    except Exception as e:
        test_print(f"Syntax validation failed: {e}", 'fail')
        return False


def run_all_tests():
    """Run all tests"""
    print("🧪 Testing Templates Library")
    print("=" * 70)
    print()

    try:
        # Core functionality tests
        if not test_registry_import():
            return False

        test_registry_initialization()
        test_list_categories()
        test_list_templates()
        test_get_template()
        test_search_templates()

        # Database template generation tests
        test_generate_migration()
        test_generate_schema()
        test_generate_seed()
        test_generate_query()
        test_generate_trigger()
        test_generate_view()

        # Validation tests
        test_syntax_validation()

        print()
        print("=" * 70)

        if failed == 0:
            print(f"{GREEN}✅ All {passed} tests passed!{RESET}")
            return True
        else:
            print(f"{RED}❌ {failed} test(s) failed, {passed} passed{RESET}")
            if warnings > 0:
                print(f"{YELLOW}⚠️  {warnings} warning(s){RESET}")
            return False

    except Exception as e:
        print(f"\n{RED}💥 Test suite error: {e}{RESET}")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

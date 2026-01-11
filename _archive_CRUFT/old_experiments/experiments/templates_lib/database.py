#!/usr/bin/env python3
"""
Database Template Module

SQL templates for migrations, schemas, seeds, queries, triggers, and views.
"""

from datetime import datetime
from typing import Optional


# Category name for this module
CATEGORY = 'database'


# ==============================================================================
# GENERATOR FUNCTIONS
# ==============================================================================

def generate_migration(migration_name: str, number: Optional[int] = None) -> str:
    """
    Generate a SQL migration file

    Args:
        migration_name: Migration name (e.g., 'add_users', 'create_posts')
        number: Migration number (e.g., 001, 002). Auto-generated if not provided.

    Returns:
        SQL migration file content
    """
    if number is None:
        # In real usage, this would check existing migrations
        number = 1

    migration_num = f"{number:03d}"

    return f"""-- Migration {migration_num}: {migration_name.replace('_', ' ').title()}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- TODO: Write your migration here
-- Example:
-- CREATE TABLE IF NOT EXISTS my_table (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Rollback (if needed):
-- DROP TABLE IF EXISTS my_table;
"""


def generate_schema(table_name: str, columns: Optional[str] = None) -> str:
    """
    Generate CREATE TABLE schema

    Args:
        table_name: Name of the table
        columns: Column definitions (optional, provides example if not given)

    Returns:
        CREATE TABLE SQL statement
    """
    if columns is None:
        columns = f"""    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP"""

    return f"""-- Schema for {table_name}
CREATE TABLE IF NOT EXISTS {table_name} (
{columns}
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_{table_name}_created ON {table_name}(created_at);
"""


def generate_seed(table_name: str, data: Optional[str] = None) -> str:
    """
    Generate INSERT seed data

    Args:
        table_name: Name of the table
        data: INSERT data (optional, provides example if not given)

    Returns:
        INSERT SQL statements
    """
    if data is None:
        data = f"""    (1, 'Example 1', CURRENT_TIMESTAMP),
    (2, 'Example 2', CURRENT_TIMESTAMP),
    (3, 'Example 3', CURRENT_TIMESTAMP)"""

    return f"""-- Seed data for {table_name}
-- Use INSERT OR IGNORE to make this idempotent
INSERT OR IGNORE INTO {table_name} (id, name, created_at) VALUES
{data};
"""


def generate_query(query_name: str, description: Optional[str] = None) -> str:
    """
    Generate a complex SQL query template

    Args:
        query_name: Query name (e.g., 'get_active_users', 'monthly_revenue')
        description: What this query does

    Returns:
        SQL query with documentation
    """
    if description is None:
        description = f"Query: {query_name.replace('_', ' ').title()}"

    return f"""-- {description}
-- Usage: Execute this query with appropriate parameters
SELECT
    -- TODO: Add your columns here
    *
FROM
    -- TODO: Add your table here
    your_table
WHERE
    -- TODO: Add your conditions here
    1=1
ORDER BY
    created_at DESC
LIMIT 100;
"""


def generate_trigger(table_name: str, trigger_type: str = 'AFTER INSERT') -> str:
    """
    Generate a database trigger

    Args:
        table_name: Name of the table
        trigger_type: Type of trigger (e.g., 'AFTER INSERT', 'BEFORE UPDATE')

    Returns:
        CREATE TRIGGER SQL statement
    """
    trigger_name = f"{table_name}_{trigger_type.lower().replace(' ', '_')}"

    return f"""-- Trigger for {table_name}
CREATE TRIGGER IF NOT EXISTS {trigger_name}
{trigger_type} ON {table_name}
FOR EACH ROW
BEGIN
    -- TODO: Add your trigger logic here
    -- Example: Update timestamp
    -- UPDATE {table_name} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


def generate_view(view_name: str, description: Optional[str] = None) -> str:
    """
    Generate a database view

    Args:
        view_name: Name of the view
        description: What this view represents

    Returns:
        CREATE VIEW SQL statement
    """
    if description is None:
        description = f"View: {view_name.replace('_', ' ').title()}"

    return f"""-- {description}
CREATE VIEW IF NOT EXISTS {view_name} AS
SELECT
    -- TODO: Add your view query here
    *
FROM
    your_table
WHERE
    -- TODO: Add your conditions here
    1=1;
"""


# ==============================================================================
# TEMPLATE DEFINITIONS
# ==============================================================================

TEMPLATES = {
    'migration': {
        'description': 'SQL database migration file',
        'generator': generate_migration,
        'parameters': ['migration_name', 'number?'],
        'examples': [
            "generate_template('database', 'migration', migration_name='add_users')",
            "generate_template('database', 'migration', migration_name='create_posts', number=5)"
        ],
        'tags': ['sql', 'migration', 'schema', 'database']
    },

    'schema': {
        'description': 'CREATE TABLE schema definition',
        'generator': generate_schema,
        'parameters': ['table_name', 'columns?'],
        'examples': [
            "generate_template('database', 'schema', table_name='users')",
            "generate_template('database', 'schema', table_name='posts', columns='id INT, title TEXT')"
        ],
        'tags': ['sql', 'schema', 'table', 'database']
    },

    'seed': {
        'description': 'INSERT seed data for testing',
        'generator': generate_seed,
        'parameters': ['table_name', 'data?'],
        'examples': [
            "generate_template('database', 'seed', table_name='users')",
            "generate_template('database', 'seed', table_name='posts', data='(1, \"Hello\")')"
        ],
        'tags': ['sql', 'seed', 'data', 'testing']
    },

    'query': {
        'description': 'Complex SQL query template',
        'generator': generate_query,
        'parameters': ['query_name', 'description?'],
        'examples': [
            "generate_template('database', 'query', query_name='get_active_users')",
            "generate_template('database', 'query', query_name='monthly_revenue', description='Revenue by month')"
        ],
        'tags': ['sql', 'query', 'select']
    },

    'trigger': {
        'description': 'Database trigger for automated actions',
        'generator': generate_trigger,
        'parameters': ['table_name', 'trigger_type?'],
        'examples': [
            "generate_template('database', 'trigger', table_name='users')",
            "generate_template('database', 'trigger', table_name='posts', trigger_type='BEFORE UPDATE')"
        ],
        'tags': ['sql', 'trigger', 'automation']
    },

    'view': {
        'description': 'Database view for complex queries',
        'generator': generate_view,
        'parameters': ['view_name', 'description?'],
        'examples': [
            "generate_template('database', 'view', view_name='active_users')",
            "generate_template('database', 'view', view_name='post_stats', description='Post statistics')"
        ],
        'tags': ['sql', 'view', 'query']
    }
}


if __name__ == '__main__':
    # Test the templates
    print("🧪 Testing Database Templates\n")

    print("=" * 70)
    print("1. MIGRATION")
    print("=" * 70)
    print(generate_migration(migration_name='add_users', number=1))

    print("\n" + "=" * 70)
    print("2. SCHEMA")
    print("=" * 70)
    print(generate_schema(table_name='users'))

    print("\n" + "=" * 70)
    print("3. SEED")
    print("=" * 70)
    print(generate_seed(table_name='users'))

    print("\n" + "=" * 70)
    print("4. QUERY")
    print("=" * 70)
    print(generate_query(query_name='get_active_users', description='Get all active users'))

    print("\n" + "=" * 70)
    print("5. TRIGGER")
    print("=" * 70)
    print(generate_trigger(table_name='users', trigger_type='AFTER INSERT'))

    print("\n" + "=" * 70)
    print("6. VIEW")
    print("=" * 70)
    print(generate_view(view_name='active_users', description='View of active users'))

    print("\n✅ All database templates generated successfully!")

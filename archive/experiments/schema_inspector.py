#!/usr/bin/env python3
"""
Schema Inspector - Database Introspection Engine

Automatically discovers and analyzes all database tables:
- Table schemas (columns, types, constraints)
- Relationships (foreign keys, references)
- Table classification (logs, stats, content, users, etc.)
- Metadata generation for dashboard automation

Usage:
    from schema_inspector import get_all_tables, get_table_schema, classify_table

    # Get all tables
    tables = get_all_tables()

    # Get schema for specific table
    schema = get_table_schema('api_keys')

    # Classify table by purpose
    table_type = classify_table('api_call_logs')  # Returns: 'logs'
"""

import sqlite3
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from database import get_db


# ==============================================================================
# TABLE DISCOVERY
# ==============================================================================

def get_all_tables() -> List[str]:
    """
    Get list of all tables in database

    Returns:
        List of table names
    """
    conn = get_db()

    tables = conn.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    ''').fetchall()

    conn.close()

    return [t['name'] for t in tables]


def get_table_count(table_name: str) -> int:
    """Get row count for table"""
    conn = get_db()
    count = conn.execute(f'SELECT COUNT(*) as count FROM {table_name}').fetchone()['count']
    conn.close()
    return count


# ==============================================================================
# SCHEMA INTROSPECTION
# ==============================================================================

def get_table_schema(table_name: str) -> Dict:
    """
    Get complete schema information for a table

    Args:
        table_name: Name of table to inspect

    Returns:
        {
            'name': 'api_keys',
            'columns': [{name, type, nullable, default, primary_key}, ...],
            'indexes': [...],
            'foreign_keys': [{from, to, table}, ...],
            'row_count': 42,
            'size_estimate': '1.2 MB'
        }
    """
    conn = get_db()

    # Get column information
    columns_raw = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    columns = []

    for col in columns_raw:
        columns.append({
            'name': col['name'],
            'type': col['type'],
            'nullable': not col['notnull'],
            'default': col['dflt_value'],
            'primary_key': bool(col['pk'])
        })

    # Get indexes
    indexes_raw = conn.execute(f'PRAGMA index_list({table_name})').fetchall()
    indexes = [idx['name'] for idx in indexes_raw]

    # Get foreign keys
    fks_raw = conn.execute(f'PRAGMA foreign_key_list({table_name})').fetchall()
    foreign_keys = []

    for fk in fks_raw:
        foreign_keys.append({
            'from_column': fk['from'],
            'to_table': fk['table'],
            'to_column': fk['to']
        })

    # Get row count
    row_count = conn.execute(f'SELECT COUNT(*) as count FROM {table_name}').fetchone()['count']

    conn.close()

    return {
        'name': table_name,
        'columns': columns,
        'indexes': indexes,
        'foreign_keys': foreign_keys,
        'row_count': row_count,
        'classification': classify_table(table_name, columns)
    }


# ==============================================================================
# TABLE CLASSIFICATION
# ==============================================================================

def classify_table(table_name: str, columns: List[Dict] = None) -> str:
    """
    Classify table by purpose/type

    Returns one of:
    - 'logs': Activity/event logs (api_call_logs, ai_requests)
    - 'stats': Statistics/metrics tables
    - 'content': User-generated content (posts, comments, ideas)
    - 'users': User/auth tables (users, sessions)
    - 'config': Configuration/settings
    - 'relationships': Many-to-many join tables
    - 'queue': Job/task queues
    - 'cache': Temporary/cached data
    - 'unknown': Can't classify
    """
    name_lower = table_name.lower()

    # Logs
    if any(keyword in name_lower for keyword in ['log', 'history', 'activity', 'trace', 'audit']):
        return 'logs'

    # Stats
    if any(keyword in name_lower for keyword in ['stat', 'metric', 'score', 'count', 'ranking']):
        return 'stats'

    # Content
    if any(keyword in name_lower for keyword in ['post', 'comment', 'message', 'idea', 'submission', 'plot', 'catchphrase']):
        return 'content'

    # Users
    if any(keyword in name_lower for keyword in ['user', 'subscriber', 'auth', 'session', 'login']):
        return 'users'

    # Config
    if any(keyword in name_lower for keyword in ['config', 'setting', 'preference', 'option']):
        return 'config'

    # Queue
    if any(keyword in name_lower for keyword in ['queue', 'job', 'task', 'pending', 'outbound']):
        return 'queue'

    # Cache
    if any(keyword in name_lower for keyword in ['cache', 'temp', 'temporary']):
        return 'cache'

    # Relationships (usually has two _id columns and no other substantial columns)
    if columns:
        id_columns = [c for c in columns if c['name'].endswith('_id')]
        if len(id_columns) >= 2 and len(columns) <= 5:
            return 'relationships'

    return 'unknown'


# ==============================================================================
# RELATIONSHIP DISCOVERY
# ==============================================================================

def discover_relationships() -> Dict[str, List[Dict]]:
    """
    Discover relationships between tables

    Returns:
        {
            'api_keys': [
                {'table': 'api_call_logs', 'type': 'one-to-many', 'via': 'api_key_id'},
                ...
            ],
            ...
        }
    """
    tables = get_all_tables()
    relationships = {}

    for table in tables:
        schema = get_table_schema(table)
        table_relationships = []

        # Foreign keys create one-to-many relationships
        for fk in schema['foreign_keys']:
            table_relationships.append({
                'table': fk['to_table'],
                'type': 'many-to-one',
                'via': fk['from_column'],
                'references': fk['to_column']
            })

        # Also check if other tables reference this table
        for other_table in tables:
            if other_table == table:
                continue

            other_schema = get_table_schema(other_table)
            for fk in other_schema['foreign_keys']:
                if fk['to_table'] == table:
                    table_relationships.append({
                        'table': other_table,
                        'type': 'one-to-many',
                        'via': fk['from_column'],
                        'in_table': other_table
                    })

        relationships[table] = table_relationships

    return relationships


# ==============================================================================
# COLUMN ANALYSIS
# ==============================================================================

def get_timestamp_columns(table_name: str) -> List[str]:
    """Find timestamp/datetime columns in table"""
    schema = get_table_schema(table_name)
    timestamp_cols = []

    for col in schema['columns']:
        col_name = col['name'].lower()
        col_type = col['type'].upper()

        if 'TIMESTAMP' in col_type or 'DATETIME' in col_type:
            timestamp_cols.append(col['name'])
        elif any(keyword in col_name for keyword in ['_at', 'date', 'time']):
            timestamp_cols.append(col['name'])

    return timestamp_cols


def get_numeric_columns(table_name: str) -> List[str]:
    """Find numeric columns in table (for stats/charts)"""
    schema = get_table_schema(table_name)
    numeric_cols = []

    for col in schema['columns']:
        col_type = col['type'].upper()
        col_name = col['name'].lower()

        if any(t in col_type for t in ['INTEGER', 'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT']):
            # Exclude IDs and flags
            if not col_name.endswith('_id') and col_name not in ['id', 'revoked', 'deleted']:
                numeric_cols.append(col['name'])

    return numeric_cols


def get_text_columns(table_name: str) -> List[str]:
    """Find text columns in table"""
    schema = get_table_schema(table_name)
    text_cols = []

    for col in schema['columns']:
        col_type = col['type'].upper()

        if 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
            text_cols.append(col['name'])

    return text_cols


# ==============================================================================
# TABLE SUMMARIES
# ==============================================================================

def get_table_summary(table_name: str) -> Dict:
    """
    Get high-level summary of table

    Returns:
        {
            'name': 'api_keys',
            'classification': 'config',
            'row_count': 42,
            'has_timestamps': True,
            'has_numeric': True,
            'timestamp_columns': ['created_at', 'last_call_at'],
            'numeric_columns': ['calls_today', 'calls_total'],
            'text_columns': ['user_email', 'api_key'],
            'primary_key': 'id',
            'foreign_keys': [...],
            'suggested_dashboard': 'stats'  # or 'timeline', 'table', 'cards'
        }
    """
    schema = get_table_schema(table_name)

    # Find primary key
    primary_key = None
    for col in schema['columns']:
        if col['primary_key']:
            primary_key = col['name']
            break

    # Get column types
    timestamp_cols = get_timestamp_columns(table_name)
    numeric_cols = get_numeric_columns(table_name)
    text_cols = get_text_columns(table_name)

    # Suggest dashboard type
    classification = schema['classification']

    if classification == 'logs':
        suggested_dashboard = 'timeline'
    elif classification == 'stats':
        suggested_dashboard = 'stats'
    elif classification == 'content':
        suggested_dashboard = 'cards'
    else:
        suggested_dashboard = 'table'

    return {
        'name': table_name,
        'classification': classification,
        'row_count': schema['row_count'],
        'has_timestamps': len(timestamp_cols) > 0,
        'has_numeric': len(numeric_cols) > 0,
        'timestamp_columns': timestamp_cols,
        'numeric_columns': numeric_cols,
        'text_columns': text_cols,
        'primary_key': primary_key,
        'foreign_keys': schema['foreign_keys'],
        'suggested_dashboard': suggested_dashboard
    }


def get_database_overview() -> Dict:
    """
    Get complete database overview

    Returns:
        {
            'total_tables': 60,
            'total_rows': 12345,
            'by_classification': {'logs': 15, 'stats': 10, ...},
            'tables': [...table summaries...],
            'relationships': {...}
        }
    """
    tables = get_all_tables()

    total_rows = 0
    by_classification = {}
    table_summaries = []

    for table in tables:
        summary = get_table_summary(table)
        table_summaries.append(summary)

        total_rows += summary['row_count']

        classification = summary['classification']
        by_classification[classification] = by_classification.get(classification, 0) + 1

    return {
        'total_tables': len(tables),
        'total_rows': total_rows,
        'by_classification': by_classification,
        'tables': table_summaries,
        'relationships': discover_relationships()
    }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Database Schema Inspector')
    parser.add_argument('--tables', action='store_true', help='List all tables')
    parser.add_argument('--schema', metavar='TABLE', help='Show schema for table')
    parser.add_argument('--summary', metavar='TABLE', help='Show summary for table')
    parser.add_argument('--overview', action='store_true', help='Show database overview')
    parser.add_argument('--classify', metavar='TABLE', help='Classify table')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if args.tables:
        tables = get_all_tables()
        if args.json:
            print(json.dumps(tables, indent=2))
        else:
            print(f"\n📊 Database Tables ({len(tables)} total):\n")
            for table in tables:
                count = get_table_count(table)
                classification = classify_table(table)
                print(f"   {table:30s} {count:>8,} rows  [{classification}]")

    elif args.schema:
        schema = get_table_schema(args.schema)
        if args.json:
            print(json.dumps(schema, indent=2, default=str))
        else:
            print(f"\n📋 Schema for {args.schema}:\n")
            print(f"Classification: {schema['classification']}")
            print(f"Row count: {schema['row_count']:,}")
            print(f"\nColumns ({len(schema['columns'])}):")
            for col in schema['columns']:
                pk = " [PK]" if col['primary_key'] else ""
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"   {col['name']:20s} {col['type']:15s} {nullable:8s}{default}{pk}")

            if schema['foreign_keys']:
                print(f"\nForeign Keys ({len(schema['foreign_keys'])}):")
                for fk in schema['foreign_keys']:
                    print(f"   {fk['from_column']} → {fk['to_table']}.{fk['to_column']}")

    elif args.summary:
        summary = get_table_summary(args.summary)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"\n📊 Summary for {args.summary}:\n")
            print(f"Classification: {summary['classification']}")
            print(f"Row count: {summary['row_count']:,}")
            print(f"Suggested dashboard: {summary['suggested_dashboard']}")
            print(f"\nTimestamp columns: {', '.join(summary['timestamp_columns']) or 'None'}")
            print(f"Numeric columns: {', '.join(summary['numeric_columns']) or 'None'}")
            print(f"Text columns: {', '.join(summary['text_columns'][:5]) or 'None'}")

    elif args.overview:
        overview = get_database_overview()
        if args.json:
            print(json.dumps(overview, indent=2))
        else:
            print(f"\n📊 Database Overview:\n")
            print(f"Total tables: {overview['total_tables']}")
            print(f"Total rows: {overview['total_rows']:,}")
            print(f"\nBy classification:")
            for classification, count in sorted(overview['by_classification'].items()):
                print(f"   {classification:15s} {count:>3} tables")

    elif args.classify:
        classification = classify_table(args.classify)
        print(f"{args.classify}: {classification}")

    else:
        parser.print_help()

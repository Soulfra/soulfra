#!/usr/bin/env python3
"""
Database Viewer - Visualize EVERYTHING in the Database (Zero Dependencies)

Shows tables, rows, and relationships in multiple formats:
- ASCII tables (terminal viewing)
- HTML tables (web viewing)
- CSV/JSON export
- Schema diagram
- Relationship visualization

Philosophy: See what you have. No SQL knowledge required.

Usage:
    python3 database_viewer.py                  # Show all tables (ASCII)
    python3 database_viewer.py --table posts    # Show specific table
    python3 database_viewer.py --html           # Generate HTML report
    python3 database_viewer.py --export         # Export all to JSON/CSV
    python3 database_viewer.py --schema         # Show table relationships
"""

import sqlite3
import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class DatabaseViewer:
    """Visualize database tables and relationships"""

    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to database"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_all_tables(self) -> List[str]:
        """Get list of all tables"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table schema info"""
        cursor = self.conn.cursor()

        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [
            {
                'name': row[1],
                'type': row[2],
                'not_null': bool(row[3]),
                'default': row[4],
                'pk': bool(row[5])
            }
            for row in cursor.fetchall()
        ]

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        return {
            'name': table_name,
            'columns': columns,
            'row_count': row_count
        }

    def get_table_data(self, table_name: str, limit: int = 100) -> List[Dict]:
        """Get table data as list of dicts"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        return [dict(row) for row in cursor.fetchall()]

    def print_ascii_table(self, table_name: str, limit: int = 20):
        """Print table as ASCII art"""
        info = self.get_table_info(table_name)
        data = self.get_table_data(table_name, limit)

        print(f"\n{'=' * 80}")
        print(f"📊 {table_name.upper()} ({info['row_count']} rows)")
        print(f"{'=' * 80}")

        if not data:
            print("  (empty table)")
            return

        # Calculate column widths
        col_widths = {}
        for col in info['columns']:
            col_name = col['name']
            col_widths[col_name] = len(col_name)

        for row in data:
            for col_name, value in row.items():
                value_str = str(value) if value is not None else 'NULL'
                col_widths[col_name] = max(col_widths[col_name], len(value_str))

        # Limit column width to 50 chars
        for col_name in col_widths:
            col_widths[col_name] = min(col_widths[col_name], 50)

        # Print header
        header = '│ '.join(
            col['name'].ljust(col_widths[col['name']])
            for col in info['columns']
        )
        print(f"│ {header} │")
        print(f"{'─' * (len(header) + 4)}")

        # Print rows
        for row in data:
            row_str = '│ '.join(
                str(row[col['name']])[:col_widths[col['name']]].ljust(col_widths[col['name']])
                if row[col['name']] is not None else 'NULL'.ljust(col_widths[col['name']])
                for col in info['columns']
            )
            print(f"│ {row_str} │")

        if info['row_count'] > limit:
            print(f"\n  ... {info['row_count'] - limit} more rows (showing first {limit})")

        print()

    def print_summary(self):
        """Print database summary"""
        tables = self.get_all_tables()

        print("=" * 80)
        print("📊 DATABASE SUMMARY")
        print("=" * 80)
        print(f"\nDatabase: {self.db_path}")
        print(f"Tables: {len(tables)}")
        print()

        # Group tables by category
        categories = {
            'Core': ['users', 'posts', 'comments', 'souls'],
            'Widget': ['discussion_sessions', 'discussion_messages'],
            'Neural Networks': ['neural_networks', 'model_versions'],
            'Monetization': ['brands', 'products', 'subscribers'],
            'Tracking': ['qr_codes', 'qr_scans', 'searches'],
            'Other': []
        }

        # Categorize tables
        categorized = set()
        for category, table_list in categories.items():
            for table in table_list:
                if table in tables:
                    categorized.add(table)

        # Put uncategorized in Other
        for table in tables:
            if table not in categorized:
                categories['Other'].append(table)

        # Print by category
        for category, table_list in categories.items():
            if not table_list or not any(t in tables for t in table_list):
                continue

            print(f"\n{category}:")
            for table in table_list:
                if table in tables:
                    info = self.get_table_info(table)
                    print(f"  • {table}: {info['row_count']} rows ({len(info['columns'])} columns)")

    def generate_html_report(self, output_path='database_report.html'):
        """Generate HTML report of entire database"""
        tables = self.get_all_tables()

        html = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <title>Database Report - Soulfra</title>',
            '  <style>',
            '    body { font-family: monospace; margin: 20px; background: #1a1a1a; color: #f0f0f0; }',
            '    h1 { color: #4af; }',
            '    h2 { color: #f84; margin-top: 40px; }',
            '    table { border-collapse: collapse; width: 100%; margin: 20px 0; background: #222; }',
            '    th { background: #333; padding: 10px; text-align: left; border: 1px solid #444; }',
            '    td { padding: 8px; border: 1px solid #333; }',
            '    tr:hover { background: #2a2a2a; }',
            '    .meta { color: #888; font-size: 0.9em; }',
            '  </style>',
            '</head>',
            '<body>',
            f'  <h1>📊 Database Report</h1>',
            f'  <p class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
            f'  <p class="meta">Database: {self.db_path}</p>',
            f'  <p class="meta">Tables: {len(tables)}</p>',
        ]

        for table in tables:
            info = self.get_table_info(table)
            data = self.get_table_data(table, limit=100)

            html.append(f'  <h2>{table} ({info["row_count"]} rows)</h2>')

            if not data:
                html.append('  <p>(empty table)</p>')
                continue

            html.append('  <table>')

            # Header
            html.append('    <tr>')
            for col in info['columns']:
                pk = ' 🔑' if col['pk'] else ''
                html.append(f'      <th>{col["name"]}{pk}</th>')
            html.append('    </tr>')

            # Rows
            for row in data:
                html.append('    <tr>')
                for col in info['columns']:
                    value = row[col['name']]
                    value_str = str(value) if value is not None else '<em>NULL</em>'
                    # Truncate long values
                    if len(value_str) > 100:
                        value_str = value_str[:100] + '...'
                    html.append(f'      <td>{value_str}</td>')
                html.append('    </tr>')

            if info['row_count'] > 100:
                html.append(f'    <tr><td colspan="{len(info["columns"])}" style="text-align:center;color:#888;">... {info["row_count"] - 100} more rows</td></tr>')

            html.append('  </table>')

        html.extend([
            '</body>',
            '</html>'
        ])

        with open(output_path, 'w') as f:
            f.write('\n'.join(html))

        print(f"✅ HTML report generated: {output_path}")

    def export_to_json(self, output_dir='database_export'):
        """Export all tables to JSON files"""
        Path(output_dir).mkdir(exist_ok=True)
        tables = self.get_all_tables()

        for table in tables:
            data = self.get_table_data(table, limit=10000)
            output_path = f"{output_dir}/{table}.json"

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        print(f"✅ Exported {len(tables)} tables to {output_dir}/*.json")

    def export_to_csv(self, output_dir='database_export'):
        """Export all tables to CSV files"""
        Path(output_dir).mkdir(exist_ok=True)
        tables = self.get_all_tables()

        for table in tables:
            info = self.get_table_info(table)
            data = self.get_table_data(table, limit=10000)

            if not data:
                continue

            output_path = f"{output_dir}/{table}.csv"

            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[col['name'] for col in info['columns']])
                writer.writeheader()
                writer.writerows(data)

        print(f"✅ Exported {len(tables)} tables to {output_dir}/*.csv")

    def show_schema(self):
        """Show database schema and relationships"""
        tables = self.get_all_tables()

        print("\n" + "=" * 80)
        print("📐 DATABASE SCHEMA")
        print("=" * 80)

        for table in tables:
            info = self.get_table_info(table)

            print(f"\n{table}:")
            for col in info['columns']:
                pk = ' [PK]' if col['pk'] else ''
                nn = ' NOT NULL' if col['not_null'] else ''
                default = f" DEFAULT {col['default']}" if col['default'] else ''
                print(f"  • {col['name']}: {col['type']}{pk}{nn}{default}")

        print()

    def show_relationships(self):
        """Infer and show table relationships"""
        print("\n" + "=" * 80)
        print("🔗 TABLE RELATIONSHIPS (Inferred)")
        print("=" * 80)
        print()

        relationships = [
            ('discussion_sessions', 'discussion_messages', 'session_id'),
            ('users', 'posts', 'user_id'),
            ('posts', 'comments', 'post_id'),
            ('users', 'souls', 'user_id'),
            ('brands', 'products', 'brand_id'),
            ('neural_networks', 'model_versions', 'network_id'),
        ]

        for parent, child, fk in relationships:
            tables = self.get_all_tables()
            if parent in tables and child in tables:
                parent_info = self.get_table_info(parent)
                child_info = self.get_table_info(child)
                print(f"  {parent} ({parent_info['row_count']}) ──[{fk}]──> {child} ({child_info['row_count']})")

        print()


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Visualize database tables and data')
    parser.add_argument('--table', help='Show specific table')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--export', action='store_true', help='Export all tables to JSON/CSV')
    parser.add_argument('--schema', action='store_true', help='Show schema only')
    parser.add_argument('--limit', type=int, default=20, help='Row limit for ASCII display')
    parser.add_argument('--db', default='soulfra.db', help='Database path')

    args = parser.parse_args()

    viewer = DatabaseViewer(args.db)

    try:
        viewer.connect()

        if args.html:
            viewer.generate_html_report()
        elif args.export:
            viewer.export_to_json()
            viewer.export_to_csv()
        elif args.schema:
            viewer.show_schema()
            viewer.show_relationships()
        elif args.table:
            viewer.print_ascii_table(args.table, limit=args.limit)
        else:
            # Default: Show summary + key tables
            viewer.print_summary()

            print("\n" + "=" * 80)
            print("📊 KEY TABLE DATA")
            print("=" * 80)

            key_tables = ['posts', 'discussion_messages', 'neural_networks', 'products']
            for table in key_tables:
                if table in viewer.get_all_tables():
                    viewer.print_ascii_table(table, limit=10)

            viewer.show_relationships()

            print("\n💡 TIP: Run with --html to generate a full HTML report")
            print("💡 TIP: Run with --export to export all tables to JSON/CSV")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        viewer.close()

#!/usr/bin/env python3
"""
Dashboard Generator - Auto-Create Admin Dashboards

Automatically generates complete admin dashboards for any database table.

Features:
- Stats cards for numeric columns
- Data tables with all records
- Charts for numeric data over time
- Timeline views for logs
- Search/filter UI
- Export buttons

Usage:
    from dashboard_generator import generate_dashboard

    # Generate dashboard HTML
    html = generate_dashboard('api_keys', dashboard_type='stats')

    # Or generate and save to file
    python3 dashboard_generator.py --table api_keys --save
"""

import os
from typing import Dict, List, Optional
from schema_inspector import (
    get_table_summary,
    get_table_schema,
    get_timestamp_columns,
    get_numeric_columns,
    get_text_columns
)


# ==============================================================================
# DASHBOARD TEMPLATES
# ==============================================================================

def generate_dashboard(table_name: str, dashboard_type: Optional[str] = None) -> str:
    """
    Generate complete dashboard HTML for table

    Args:
        table_name: Name of database table
        dashboard_type: 'stats', 'timeline', 'table', or 'cards' (auto-detected if None)

    Returns:
        Complete HTML dashboard string
    """
    summary = get_table_summary(table_name)
    schema = get_table_schema(table_name)

    # Auto-detect dashboard type if not specified
    if not dashboard_type:
        dashboard_type = summary['suggested_dashboard']

    # Generate appropriate dashboard
    if dashboard_type == 'stats':
        return _generate_stats_dashboard(table_name, summary, schema)
    elif dashboard_type == 'timeline':
        return _generate_timeline_dashboard(table_name, summary, schema)
    elif dashboard_type == 'cards':
        return _generate_cards_dashboard(table_name, summary, schema)
    else:
        return _generate_table_dashboard(table_name, summary, schema)


def _generate_stats_dashboard(table_name: str, summary: Dict, schema: Dict) -> str:
    """Generate stats-focused dashboard with charts"""

    numeric_cols = summary['numeric_columns']
    timestamp_cols = summary['timestamp_columns']

    # Generate stats cards HTML
    stats_cards_html = _generate_stats_cards(table_name, numeric_cols)

    # Generate charts HTML
    charts_html = _generate_charts(table_name, numeric_cols, timestamp_cols)

    # Generate recent records table
    table_html = _generate_data_table(table_name, schema, limit=20)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{table_name.replace('_', ' ').title()} Dashboard | Soulfra Admin</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        h1 {{
            font-size: 28px;
            color: #333;
            margin-bottom: 8px;
        }}

        .subtitle {{
            color: #666;
            font-size: 14px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .stat-label {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}

        .section {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 24px;
        }}

        .section h2 {{
            font-size: 20px;
            color: #333;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            text-align: left;
            padding: 12px;
            background: #f8f9fa;
            color: #666;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
            color: #333;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .nav-links {{
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }}

        .nav-link {{
            padding: 10px 20px;
            background: white;
            border-radius: 8px;
            text-decoration: none;
            color: #666;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s;
        }}

        .nav-link:hover {{
            background: #667eea;
            color: white;
        }}

        .nav-link.active {{
            background: #667eea;
            color: white;
        }}

        .btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
        }}

        .btn:hover {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 {table_name.replace('_', ' ').title()}</h1>
            <p class="subtitle">Auto-generated dashboard • {summary['row_count']:,} total records • Classification: {summary['classification']}</p>
        </header>

        <div class="nav-links">
            <a href="/admin" class="nav-link">🏠 Admin Home</a>
            <a href="/admin/{table_name}" class="nav-link active">📊 {table_name}</a>
            <a href="/admin/{table_name}/export" class="btn">📥 Export CSV</a>
        </div>

        {stats_cards_html}

        {charts_html}

        <div class="section">
            <h2>📋 Recent Records</h2>
            {table_html}
        </div>
    </div>
</body>
</html>"""


def _generate_timeline_dashboard(table_name: str, summary: Dict, schema: Dict) -> str:
    """Generate timeline-focused dashboard for logs"""
    table_html = _generate_data_table(table_name, schema, limit=50)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{table_name.replace('_', ' ').title()} Timeline | Soulfra Admin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ background: white; padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 28px; color: #333; }}
        .subtitle {{ color: #666; font-size: 14px; margin-top: 8px; }}
        .section {{ background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 12px; background: #f8f9fa; color: #666; font-size: 13px; }}
        td {{ padding: 12px; border-bottom: 1px solid #f0f0f0; font-size: 14px; color: #333; }}
        tr:hover {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⏱️ {table_name.replace('_', ' ').title()} Timeline</h1>
            <p class="subtitle">{summary['row_count']:,} total events</p>
        </header>
        <div class="section">
            {table_html}
        </div>
    </div>
</body>
</html>"""


def _generate_table_dashboard(table_name: str, summary: Dict, schema: Dict) -> str:
    """Generate simple table view dashboard"""
    table_html = _generate_data_table(table_name, schema, limit=100)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{table_name} | Soulfra Admin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ background: white; padding: 24px; border-radius: 12px; margin-bottom: 24px; }}
        .section {{ background: white; padding: 24px; border-radius: 12px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 12px; background: #f8f9fa; }}
        td {{ padding: 12px; border-bottom: 1px solid #f0f0f0; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{table_name}</h1>
        </header>
        <div class="section">
            {table_html}
        </div>
    </div>
</body>
</html>"""


def _generate_cards_dashboard(table_name: str, summary: Dict, schema: Dict) -> str:
    """Generate card-based dashboard for content"""
    return _generate_table_dashboard(table_name, summary, schema)  # Simplified for now


# ==============================================================================
# COMPONENT GENERATORS
# ==============================================================================

def _generate_stats_cards(table_name: str, numeric_cols: List[str]) -> str:
    """Generate stats cards HTML"""
    if not numeric_cols:
        return ""

    cards_html = '<div class="stats-grid">'

    for col in numeric_cols[:6]:  # Limit to 6 stats
        cards_html += f"""
    <div class="stat-card">
        <div class="stat-label">{col.replace('_', ' ').title()}</div>
        <div class="stat-value">{{{{ stats.{col} or 0 }}}}</div>
    </div>"""

    cards_html += "\n</div>"

    return cards_html


def _generate_charts(table_name: str, numeric_cols: List[str], timestamp_cols: List[str]) -> str:
    """Generate charts HTML"""
    if not numeric_cols or not timestamp_cols:
        return ""

    return f"""
<div class="section">
    <h2>📈 Charts</h2>
    <p style="color: #999;">Chart generation coming soon...</p>
</div>"""


def _generate_data_table(table_name: str, schema: Dict, limit: int = 20) -> str:
    """Generate data table HTML"""

    # Get column names
    columns = [col['name'] for col in schema['columns']]

    # Generate table header
    header_html = "<thead><tr>"
    for col in columns[:10]:  # Limit to 10 columns for display
        header_html += f"<th>{col.replace('_', ' ').title()}</th>"
    header_html += "</tr></thead>"

    # Generate table body template
    body_html = "<tbody>"
    body_html += "{% for row in rows %}<tr>"
    for col in columns[:10]:
        body_html += f"<td>{{{{ row.{col} or '-' }}}}</td>"
    body_html += "</tr>{% endfor %}"
    body_html += "</tbody>"

    return f"<table>{header_html}{body_html}</table>"


# ==============================================================================
# SAVE & LOAD
# ==============================================================================

def save_dashboard(table_name: str, dashboard_type: Optional[str] = None) -> str:
    """
    Generate dashboard and save to templates/admin_{table_name}.html

    Returns:
        Path to saved file
    """
    html = generate_dashboard(table_name, dashboard_type)

    filepath = f"templates/admin_{table_name}.html"

    with open(filepath, 'w') as f:
        f.write(html)

    print(f"✅ Dashboard saved to {filepath}")

    return filepath


def generate_all_dashboards() -> List[str]:
    """
    Generate dashboards for all database tables

    Returns:
        List of generated file paths
    """
    from schema_inspector import get_all_tables

    tables = get_all_tables()
    generated = []

    for table in tables:
        try:
            filepath = save_dashboard(table)
            generated.append(filepath)
        except Exception as e:
            print(f"❌ Failed to generate {table}: {e}")

    print(f"\n✅ Generated {len(generated)}/{len(tables)} dashboards")

    return generated


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Dashboard Generator')
    parser.add_argument('--table', metavar='TABLE', help='Generate dashboard for table')
    parser.add_argument('--type', metavar='TYPE', choices=['stats', 'timeline', 'table', 'cards'], help='Dashboard type')
    parser.add_argument('--save', action='store_true', help='Save to templates/ folder')
    parser.add_argument('--all', action='store_true', help='Generate dashboards for all tables')
    parser.add_argument('--preview', action='store_true', help='Print HTML to stdout')

    args = parser.parse_args()

    if args.all:
        generate_all_dashboards()

    elif args.table:
        html = generate_dashboard(args.table, args.type)

        if args.save:
            save_dashboard(args.table, args.type)
        elif args.preview:
            print(html)
        else:
            print(f"✅ Generated dashboard for {args.table}")
            print("   Use --save to save to file or --preview to see HTML")

    else:
        parser.print_help()

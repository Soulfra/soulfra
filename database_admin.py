#!/usr/bin/env python3
"""
Database Admin Dashboard - SharePoint-like interface for soulfra.db

Features:
- View all tables
- Export to CSV (mailing lists)
- Export to Excel (.xlsx)
- Search/filter data
- User account management
"""

from flask import Blueprint, render_template, request, jsonify, send_file, abort
import sqlite3
import csv
import io
from datetime import datetime

database_admin_bp = Blueprint('database_admin', __name__)

# Whitelisted IPs for admin panel access
ADMIN_WHITELIST = [
    '127.0.0.1',        # Localhost
    '::1',              # IPv6 localhost
    '192.168.1.87',     # User's local network IP
]

def check_admin_access():
    """Check if request IP is whitelisted for admin access"""
    from dev_config import DEV_MODE

    # In DEV_MODE, allow all localhost IPs
    if DEV_MODE:
        client_ip = request.remote_addr
        if client_ip in ['127.0.0.1', '::1', 'localhost']:
            return True

    # Check whitelist
    client_ip = request.remote_addr

    # Allow any 192.168.*.* local network
    if client_ip.startswith('192.168.'):
        return True

    if client_ip in ADMIN_WHITELIST:
        return True

    # Reject unauthorized access
    abort(403)

def get_db_connection():
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

@database_admin_bp.route('/admin/database')
def database_dashboard():
    """Main admin dashboard - like SharePoint"""
    check_admin_access()
    conn = get_db_connection()

    # Get all tables
    tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    table_list = [t['name'] for t in tables]

    # Get table counts
    table_stats = {}
    for table in table_list:
        try:
            count = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()['count']
            table_stats[table] = count
        except:
            table_stats[table] = 0

    conn.close()

    return render_template('admin/database.html',
                         tables=table_list,
                         table_stats=table_stats)

@database_admin_bp.route('/api/admin/table/<table_name>')
def get_table_data(table_name):
    """Get data from a specific table"""
    try:
        conn = get_db_connection()

        # Get column names
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall()]

        # Get data with pagination
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '')

        query = f"SELECT * FROM {table_name}"

        # Add search if provided
        if search:
            search_conditions = ' OR '.join([f"{col} LIKE ?" for col in columns])
            query += f" WHERE {search_conditions}"
            params = [f"%{search}%"] * len(columns)
            rows = conn.execute(f"{query} LIMIT {limit} OFFSET {offset}", params).fetchall()
        else:
            rows = conn.execute(f"{query} LIMIT {limit} OFFSET {offset}").fetchall()

        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        if search:
            count_query += f" WHERE {search_conditions}"
            total = conn.execute(count_query, params).fetchone()['count']
        else:
            total = conn.execute(count_query).fetchone()['count']

        data = [dict(row) for row in rows]

        conn.close()

        return jsonify({
            'success': True,
            'columns': columns,
            'data': data,
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@database_admin_bp.route('/api/admin/export/<table_name>/csv')
def export_csv(table_name):
    """Export table to CSV - for mailing lists, etc."""
    try:
        conn = get_db_connection()

        # Get all data
        rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()

        if not rows:
            return "No data to export", 404

        # Create CSV in memory
        output = io.StringIO()
        columns = rows[0].keys()
        writer = csv.DictWriter(output, fieldnames=columns)

        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

        conn.close()

        # Return as downloadable file
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{table_name}_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return f"Export failed: {e}", 500

@database_admin_bp.route('/api/admin/export-emails')
def export_emails():
    """Export all user emails for mailing lists (Mailchimp, SendGrid, etc.)"""
    try:
        conn = get_db_connection()

        # Try to find email columns across all tables
        email_data = []

        # Common tables that might have emails
        tables_to_check = [
            ('users', 'email'),
            ('user_accounts', 'email'),
            ('subscribers', 'email'),
            ('contacts', 'email'),
            ('simple_voice_recordings', None),  # May have user_id that links to email
        ]

        for table, email_col in tables_to_check:
            try:
                # Check if table exists
                check = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                if not check:
                    continue

                if email_col:
                    # Table has direct email column
                    rows = conn.execute(f"SELECT DISTINCT {email_col} as email FROM {table} WHERE {email_col} IS NOT NULL").fetchall()
                    for row in rows:
                        if row['email'] and '@' in row['email']:
                            email_data.append({
                                'email': row['email'],
                                'source': table
                            })
            except Exception as e:
                print(f"Error checking {table}: {e}")
                continue

        conn.close()

        # Remove duplicates
        seen = set()
        unique_emails = []
        for item in email_data:
            if item['email'] not in seen:
                seen.add(item['email'])
                unique_emails.append(item)

        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['email', 'source'])
        writer.writeheader()
        for item in unique_emails:
            writer.writerow(item)

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'email_list_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return f"Email export failed: {e}", 500

@database_admin_bp.route('/api/admin/sql-query', methods=['POST'])
def run_sql_query():
    """Run custom SQL query (admin only - be careful!)"""
    try:
        data = request.get_json()
        query = data.get('query', '')

        if not query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400

        # Block dangerous queries
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        if any(keyword in query.upper() for keyword in dangerous_keywords):
            return jsonify({'success': False, 'error': 'Dangerous query blocked'}), 403

        conn = get_db_connection()
        cursor = conn.execute(query)

        if cursor.description:
            # SELECT query
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            result = {
                'success': True,
                'columns': columns,
                'data': rows,
                'count': len(rows)
            }
        else:
            # Non-SELECT query
            conn.commit()
            result = {
                'success': True,
                'message': 'Query executed successfully',
                'rows_affected': cursor.rowcount
            }

        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def register_database_admin_routes(app):
    """Register database admin routes"""
    app.register_blueprint(database_admin_bp)
    print("📊 Database Admin routes registered:")
    print("   Dashboard: GET /admin/database")
    print("   Table Data: GET /api/admin/table/<name>")
    print("   Export CSV: GET /api/admin/export/<table>/csv")
    print("   Export Emails: GET /api/admin/export-emails")
    print("   Custom SQL: POST /api/admin/sql-query")

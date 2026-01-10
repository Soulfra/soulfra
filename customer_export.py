#!/usr/bin/env python3
"""
Custom Customer Export & Workflow System

Clean, simple customer data aggregation without bloat.
Exports to Mailchimp, SendGrid, JSON, and plain text.
"""

from flask import Blueprint, jsonify, send_file, request, render_template
import sqlite3
import csv
import json
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any

customer_export_bp = Blueprint('customer_export', __name__)

def get_db_connection():
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def is_real_email(email: str) -> bool:
    """Filter out test/fake emails"""
    if not email or '@' not in email:
        return False

    # Filter out test domains
    test_domains = ['qr.local', 'soulfra.local', 'test.local', 'example.com']
    domain = email.split('@')[1]

    return domain not in test_domains

def get_all_customers() -> List[Dict[str, Any]]:
    """
    Aggregate customers from all sources
    Returns list of customer dicts with: email, name, source, created_at, tags
    """
    conn = get_db_connection()
    customers = []
    seen_emails = set()

    # 1. Users table
    users = conn.execute("""
        SELECT email, username as name, created_at, 'user_signup' as source
        FROM users
        WHERE email IS NOT NULL
    """).fetchall()

    for user in users:
        email = user['email']
        if is_real_email(email) and email not in seen_emails:
            customers.append({
                'email': email,
                'name': user['name'],
                'source': user['source'],
                'created_at': user['created_at'],
                'tags': ['user', 'registered']
            })
            seen_emails.add(email)

    # 2. Subscribers table
    subscribers = conn.execute("""
        SELECT email, 'newsletter' as source, subscribed_at as created_at
        FROM subscribers
        WHERE email IS NOT NULL AND unsubscribed_at IS NULL
    """).fetchall()

    for sub in subscribers:
        email = sub['email']
        if is_real_email(email) and email not in seen_emails:
            customers.append({
                'email': email,
                'name': '',
                'source': sub['source'],
                'created_at': sub['created_at'],
                'tags': ['subscriber', 'newsletter']
            })
            seen_emails.add(email)

    # 3. QR scans (when they start collecting emails)
    qr_scans = conn.execute("""
        SELECT DISTINCT scanned_by_email as email, scanned_by_name as name,
               'qr_scan' as source, scanned_at as created_at
        FROM qr_scans
        WHERE scanned_by_email IS NOT NULL
    """).fetchall()

    for scan in qr_scans:
        email = scan['email']
        if is_real_email(email) and email not in seen_emails:
            customers.append({
                'email': email,
                'name': scan['name'] or '',
                'source': scan['source'],
                'created_at': scan['created_at'],
                'tags': ['qr_scan', 'engaged']
            })
            seen_emails.add(email)

    conn.close()

    # Sort by created_at (newest first)
    customers.sort(key=lambda x: x['created_at'] or '', reverse=True)

    return customers

@customer_export_bp.route('/customers/dashboard')
def customer_dashboard():
    """Display customer export dashboard UI"""
    return render_template('customer_dashboard.html')

@customer_export_bp.route('/api/customers/list')
def list_customers():
    """Get all customers as JSON"""
    try:
        customers = get_all_customers()

        return jsonify({
            'success': True,
            'count': len(customers),
            'customers': customers
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_export_bp.route('/api/customers/export/mailchimp')
def export_mailchimp():
    """
    Export customer list in Mailchimp CSV format
    Columns: Email Address, First Name, Last Name, Tags
    """
    try:
        customers = get_all_customers()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Mailchimp header
        writer.writerow(['Email Address', 'First Name', 'Last Name', 'Tags'])

        for customer in customers:
            # Split name into first/last (simple split)
            name_parts = customer['name'].split(' ', 1) if customer['name'] else ['', '']
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            # Join tags with semicolon
            tags = '; '.join(customer['tags'])

            writer.writerow([
                customer['email'],
                first_name,
                last_name,
                tags
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'mailchimp_customers_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return f"Export failed: {e}", 500

@customer_export_bp.route('/api/customers/export/sendgrid')
def export_sendgrid():
    """
    Export customer list in SendGrid CSV format
    Columns: email, first_name, last_name, source, created_at
    """
    try:
        customers = get_all_customers()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # SendGrid header
        writer.writerow(['email', 'first_name', 'last_name', 'source', 'created_at', 'tags'])

        for customer in customers:
            # Split name
            name_parts = customer['name'].split(' ', 1) if customer['name'] else ['', '']
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            # Format date for SendGrid
            created_at = customer['created_at'] or ''

            writer.writerow([
                customer['email'],
                first_name,
                last_name,
                customer['source'],
                created_at,
                ','.join(customer['tags'])
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sendgrid_customers_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return f"Export failed: {e}", 500

@customer_export_bp.route('/api/customers/export/plain')
def export_plain():
    """
    Export just email addresses (one per line)
    Perfect for quick copy/paste
    """
    try:
        customers = get_all_customers()

        # Just emails, one per line
        output = '\n'.join([c['email'] for c in customers])

        return send_file(
            io.BytesIO(output.encode()),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'customer_emails_{datetime.now().strftime("%Y%m%d")}.txt'
        )

    except Exception as e:
        return f"Export failed: {e}", 500

@customer_export_bp.route('/api/customers/export/json')
def export_json():
    """
    Export full customer data as JSON
    For custom automation and API integrations
    """
    try:
        customers = get_all_customers()

        data = {
            'exported_at': datetime.now().isoformat(),
            'total_customers': len(customers),
            'customers': customers
        }

        return send_file(
            io.BytesIO(json.dumps(data, indent=2).encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'customers_{datetime.now().strftime("%Y%m%d")}.json'
        )

    except Exception as e:
        return f"Export failed: {e}", 500

@customer_export_bp.route('/api/customers/new-today')
def new_customers_today():
    """Get customers who signed up in last 24 hours"""
    try:
        all_customers = get_all_customers()

        # Filter by last 24 hours
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        new_customers = []
        for customer in all_customers:
            try:
                # Parse created_at (handle multiple formats)
                created = datetime.fromisoformat(customer['created_at'].replace('T', ' '))
                if created >= yesterday:
                    new_customers.append(customer)
            except:
                continue

        return jsonify({
            'success': True,
            'count': len(new_customers),
            'customers': new_customers
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_export_bp.route('/api/customers/stats')
def customer_stats():
    """Get customer statistics"""
    try:
        conn = get_db_connection()

        # Get counts from each source
        stats = {
            'total_users': conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c'],
            'real_users': len([u for u in get_all_customers() if 'user' in u['tags']]),
            'subscribers': conn.execute("SELECT COUNT(*) as c FROM subscribers WHERE unsubscribed_at IS NULL").fetchone()['c'],
            'qr_scans': conn.execute("SELECT COUNT(*) as c FROM qr_scans").fetchone()['c'],
            'unique_customers': len(get_all_customers()),
            'voice_recordings': conn.execute("SELECT COUNT(*) as c FROM simple_voice_recordings").fetchone()['c']
        }

        conn.close()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def register_customer_export_routes(app):
    """Register customer export routes"""
    app.register_blueprint(customer_export_bp)
    print("📧 Customer Export routes registered:")
    print("   Dashboard: GET /customers/dashboard")
    print("   List: GET /api/customers/list")
    print("   Mailchimp CSV: GET /api/customers/export/mailchimp")
    print("   SendGrid CSV: GET /api/customers/export/sendgrid")
    print("   Plain Emails: GET /api/customers/export/plain")
    print("   JSON Export: GET /api/customers/export/json")
    print("   New Today: GET /api/customers/new-today")
    print("   Stats: GET /api/customers/stats")

#!/usr/bin/env python3
"""
UPC/Product Tracking System

Link QR codes to products and track scan performance.
Perfect for physical product packaging with QR codes.
"""

from flask import Blueprint, jsonify, request, send_file
import sqlite3
import csv
import io
from datetime import datetime
from typing import List, Dict, Any

product_tracking_bp = Blueprint('product_tracking', __name__)

def get_db_connection():
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_product_tables():
    """Create product tracking tables if they don't exist"""
    conn = get_db_connection()

    # Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            qr_code_id INTEGER,
            scan_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (qr_code_id) REFERENCES qr_codes(id)
        )
    """)

    # Product scans table (detailed tracking)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS product_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            qr_scan_id INTEGER,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location_city TEXT,
            location_country TEXT,
            device_type TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (qr_scan_id) REFERENCES qr_scans(id)
        )
    """)

    conn.commit()
    conn.close()

@product_tracking_bp.route('/api/products/create', methods=['POST'])
def create_product():
    """
    Create new product with UPC
    POST data: {upc, name, description, qr_code_id}
    """
    try:
        data = request.get_json()

        upc = data.get('upc')
        name = data.get('name')
        description = data.get('description', '')
        qr_code_id = data.get('qr_code_id')

        if not upc or not name:
            return jsonify({'success': False, 'error': 'UPC and name required'}), 400

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO products (upc, name, description, qr_code_id)
            VALUES (?, ?, ?, ?)
        """, (upc, name, description, qr_code_id))

        conn.commit()
        product_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'message': 'Product created',
            'product_id': product_id
        })

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'UPC already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_tracking_bp.route('/api/products/list')
def list_products():
    """Get all products with scan counts"""
    try:
        conn = get_db_connection()

        products = conn.execute("""
            SELECT p.*,
                   COUNT(ps.id) as total_scans,
                   MAX(ps.scanned_at) as last_scan
            FROM products p
            LEFT JOIN product_scans ps ON p.id = ps.product_id
            GROUP BY p.id
            ORDER BY total_scans DESC
        """).fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'count': len(products),
            'products': [dict(p) for p in products]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_tracking_bp.route('/api/products/<int:product_id>')
def get_product(product_id):
    """Get product details with scan history"""
    try:
        conn = get_db_connection()

        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        # Get scan history
        scans = conn.execute("""
            SELECT ps.*, qs.scanned_by_name, qs.scanned_by_email
            FROM product_scans ps
            LEFT JOIN qr_scans qs ON ps.qr_scan_id = qs.id
            WHERE ps.product_id = ?
            ORDER BY ps.scanned_at DESC
            LIMIT 100
        """, (product_id,)).fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'product': dict(product),
            'recent_scans': [dict(s) for s in scans]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_tracking_bp.route('/api/products/<int:product_id>/track-scan', methods=['POST'])
def track_product_scan(product_id):
    """
    Record a product scan
    POST data: {qr_scan_id, location_city, location_country, device_type}
    """
    try:
        data = request.get_json()

        conn = get_db_connection()

        # Increment product scan count
        conn.execute("""
            UPDATE products
            SET scan_count = scan_count + 1
            WHERE id = ?
        """, (product_id,))

        # Record detailed scan
        conn.execute("""
            INSERT INTO product_scans (product_id, qr_scan_id, location_city, location_country, device_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            product_id,
            data.get('qr_scan_id'),
            data.get('location_city'),
            data.get('location_country'),
            data.get('device_type')
        ))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Scan tracked'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_tracking_bp.route('/api/products/top-scanned')
def top_scanned_products():
    """Get top 10 most scanned products"""
    try:
        conn = get_db_connection()

        products = conn.execute("""
            SELECT p.*, COUNT(ps.id) as scan_count
            FROM products p
            LEFT JOIN product_scans ps ON p.id = ps.product_id
            GROUP BY p.id
            ORDER BY scan_count DESC
            LIMIT 10
        """).fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'top_products': [dict(p) for p in products]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_tracking_bp.route('/api/products/export/performance')
def export_product_performance():
    """
    Export product performance report as CSV
    Shows: UPC, Name, Total Scans, Last Scan Date, QR Code ID
    """
    try:
        conn = get_db_connection()

        products = conn.execute("""
            SELECT
                p.upc,
                p.name,
                p.description,
                p.scan_count,
                COUNT(ps.id) as total_detailed_scans,
                MAX(ps.scanned_at) as last_scan,
                p.qr_code_id,
                p.created_at
            FROM products p
            LEFT JOIN product_scans ps ON p.id = ps.product_id
            GROUP BY p.id
            ORDER BY p.scan_count DESC
        """).fetchall()

        conn.close()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['UPC', 'Product Name', 'Description', 'Total Scans', 'Last Scan', 'QR Code ID', 'Created At'])

        for product in products:
            writer.writerow([
                product['upc'],
                product['name'],
                product['description'] or '',
                product['scan_count'],
                product['last_scan'] or 'Never',
                product['qr_code_id'] or 'N/A',
                product['created_at']
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'product_performance_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return f"Export failed: {e}", 500

@product_tracking_bp.route('/api/products/stats')
def product_stats():
    """Get overall product statistics"""
    try:
        conn = get_db_connection()

        stats = {
            'total_products': conn.execute("SELECT COUNT(*) as c FROM products").fetchone()['c'],
            'total_scans': conn.execute("SELECT SUM(scan_count) as c FROM products").fetchone()['c'] or 0,
            'products_with_qr': conn.execute("SELECT COUNT(*) as c FROM products WHERE qr_code_id IS NOT NULL").fetchone()['c'],
            'avg_scans_per_product': 0
        }

        if stats['total_products'] > 0:
            stats['avg_scans_per_product'] = round(stats['total_scans'] / stats['total_products'], 2)

        conn.close()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def register_product_tracking_routes(app):
    """Register product tracking routes"""
    # Initialize tables
    init_product_tables()

    app.register_blueprint(product_tracking_bp)
    print("📦 Product Tracking routes registered:")
    print("   Create Product: POST /api/products/create")
    print("   List Products: GET /api/products/list")
    print("   Product Details: GET /api/products/<id>")
    print("   Track Scan: POST /api/products/<id>/track-scan")
    print("   Top Scanned: GET /api/products/top-scanned")
    print("   Export Performance: GET /api/products/export/performance")
    print("   Stats: GET /api/products/stats")

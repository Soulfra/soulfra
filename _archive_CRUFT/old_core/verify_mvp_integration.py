#!/usr/bin/env python3
"""
Verify QR Analytics MVP Integration
Complete system check for all components
"""

import sqlite3
import os
from pathlib import Path
from flask import Flask
from gallery_routes import register_gallery_routes

def check_database_tables():
    """Verify all required database tables exist"""
    print("\n📊 Database Tables Check:")
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    required_tables = [
        'qr_codes',
        'qr_scans',
        'qr_galleries',
        'quests',
        'posts'
    ]

    for table in required_tables:
        cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,))
        exists = cursor.fetchone()[0]
        if exists:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count} rows")
        else:
            print(f"   ❌ {table}: NOT FOUND")

    # Check for lineage tracking column
    cursor.execute("PRAGMA table_info(qr_scans)")
    columns = {row[1] for row in cursor.fetchall()}
    if 'previous_scan_id' in columns:
        print(f"   ✅ qr_scans.previous_scan_id: Lineage tracking enabled")
    else:
        print(f"   ❌ qr_scans.previous_scan_id: NOT FOUND")

    conn.close()

def check_flask_routes():
    """Verify Flask routes are registered"""
    print("\n🌐 Flask Routes Check:")
    app = Flask(__name__)
    app.secret_key = 'test-key'
    register_gallery_routes(app)

    expected_routes = [
        '/gallery/<slug>',
        '/dm/scan',
        '/qr/track/<qr_id>'
    ]

    registered_routes = [rule.rule for rule in app.url_map.iter_rules()]

    for route in expected_routes:
        if route in registered_routes:
            print(f"   ✅ {route}")
        else:
            print(f"   ❌ {route}: NOT REGISTERED")

def check_generated_files():
    """Verify generated galleries and analytics"""
    print("\n📁 Generated Files Check:")

    # Check galleries
    galleries_dir = Path('output/galleries')
    if galleries_dir.exists():
        galleries = list(galleries_dir.glob('*.html'))
        print(f"   ✅ QR Galleries: {len(galleries)} generated")
        for gallery in galleries[:3]:  # Show first 3
            print(f"      - {gallery.name}")
    else:
        print(f"   ⚠️  No galleries directory found")

    # Check analytics dashboard
    analytics_dashboard = Path('output/analytics/qr_dashboard.html')
    if analytics_dashboard.exists():
        size_kb = analytics_dashboard.stat().st_size / 1024
        print(f"   ✅ Analytics Dashboard: {size_kb:.1f} KB")
    else:
        print(f"   ⚠️  Analytics dashboard not found")

    # Check QR codes
    qr_dir = Path('static/qr_codes/galleries')
    if qr_dir.exists():
        qr_codes = list(qr_dir.glob('*.png'))
        print(f"   ✅ QR Codes: {len(qr_codes)} generated")
    else:
        print(f"   ⚠️  No QR codes directory found")

def check_python_modules():
    """Verify all required Python modules exist"""
    print("\n🐍 Python Modules Check:")

    modules = [
        ('gallery_routes', 'QR Gallery Routes'),
        ('qr_analytics', 'QR Analytics Dashboard'),
        ('post_to_quiz', 'Post to Quiz Generator'),
        ('qr_gallery_system', 'QR Gallery System'),
        ('neural_soul_scorer', 'Neural Soul Scorer'),
        ('database', 'Database Module')
    ]

    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"   ✅ {description}: {module_name}.py")
        except ImportError as e:
            print(f"   ❌ {description}: NOT FOUND ({e})")

def check_deployment_kit():
    """Verify deployment kit files"""
    print("\n🚀 Deployment Kit Check:")

    deploy_files = [
        ('deploy/install.sh', 'Installation Script'),
        ('deploy/theme_config.yaml', 'Theme Configuration'),
        ('deploy/DEPLOY_README.md', 'Deployment Guide'),
        ('deploy/docker-compose.yml', 'Docker Compose')
    ]

    for filepath, description in deploy_files:
        path = Path(filepath)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"   ✅ {description}: {size_kb:.1f} KB")
        else:
            print(f"   ❌ {description}: NOT FOUND")

def show_system_summary():
    """Show complete system summary"""
    print("\n" + "="*60)
    print("🎯 QR ANALYTICS MVP - SYSTEM VERIFICATION")
    print("="*60)

    check_python_modules()
    check_database_tables()
    check_flask_routes()
    check_generated_files()
    check_deployment_kit()

    print("\n" + "="*60)
    print("✅ MVP INTEGRATION VERIFICATION COMPLETE")
    print("="*60)
    print("\n📚 Next Steps:")
    print("   1. Start server: python3 app.py")
    print("   2. Visit gallery: http://localhost:5001/gallery/i-love-that-youre-considering-sharing-a-recipe-for")
    print("   3. View analytics: open output/analytics/qr_dashboard.html")
    print("   4. Generate quiz: python3 post_to_quiz.py --post 29")
    print("   5. Deploy: See deploy/DEPLOY_README.md")
    print()

if __name__ == '__main__':
    show_system_summary()

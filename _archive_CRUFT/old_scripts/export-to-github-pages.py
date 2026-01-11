#!/usr/bin/env python3
"""
Export Database to GitHub Pages (Static HTML)

NO ngrok, NO backend, NO third-party services.

Reads professionals from soulfra.db → Generates static HTML → Deploys to GitHub Pages

Usage:
    python3 export-to-github-pages.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import subprocess

# Configuration
DB_PATH = Path(__file__).parent / 'soulfra.db'
GITHUB_PAGES_DIR = Path.home() / 'Desktop' / 'soulfra.github.io' / 'stpetepros'
TEMPLATE_DIR = Path(__file__).parent / 'templates'


def get_professionals():
    """Get all approved professionals from database"""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    professionals = db.execute('''
        SELECT
            id,
            business_name,
            category,
            email,
            phone,
            bio,
            website,
            address,
            city,
            zip_code,
            approval_status,
            created_at
        FROM professionals
        WHERE approval_status = 'approved'
        ORDER BY business_name
    ''').fetchall()

    db.close()
    return professionals


def generate_professional_page(prof, index, total_pros, professional_ids_json='[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,26]'):
    """Generate individual professional page HTML"""

    # Create safe filename
    safe_name = prof['business_name'].lower().replace(' ', '-').replace("'", "")
    filename = f"professional-{prof['id']}.html"

    # Category display name
    categories = {
        'plumbing': 'Plumbing',
        'electrical': 'Electrical',
        'hvac': 'HVAC',
        'roofing': 'Roofing',
        'landscaping': 'Landscaping',
        'cleaning': 'Cleaning',
        'handyman': 'Handyman',
        'auto': 'Auto Repair',
        'real-estate': 'Real Estate',
        'other': 'Other Services'
    }
    category_name = categories.get(prof['category'], prof['category'].title())

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>{prof['business_name']} - StPetePros Tampa Bay Directory</title>
    <meta name="description" content="{prof['bio'] or f'{prof['business_name']} - {category_name} services in Tampa Bay'}">

    <!-- Progressive Web App -->
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="StPetePros">
    <meta name="theme-color" content="#667eea">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .category-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-top: 10px;
        }}

        .content {{
            padding: 40px;
        }}

        .info-section {{
            margin-bottom: 30px;
        }}

        .info-section h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}

        .contact-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .contact-item {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .contact-item strong {{
            display: block;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .contact-item a {{
            color: #333;
            text-decoration: none;
        }}

        .contact-item a:hover {{
            color: #667eea;
            text-decoration: underline;
        }}

        .description {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            line-height: 1.8;
        }}

        .back-link {{
            display: inline-block;
            margin-top: 30px;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s;
        }}

        .back-link:hover {{
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9rem;
        }}

        .nav-hint {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(102, 126, 234, 0.9);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 0.85rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            opacity: 0;
            animation: fadeInOut 3s ease-in-out;
        }}

        @keyframes fadeInOut {{
            0%, 100% {{ opacity: 0; }}
            10%, 90% {{ opacity: 1; }}
        }}
    </style>
    <script>
        // Global variables for navigation scripts
        window.TOTAL_PROFESSIONALS = {total_pros};
        window.PROFESSIONAL_IDS = {professional_ids_json};
        window.CURRENT_PRO_ID = {prof['id']};
    </script>
    <!-- StPetePros Global Navigation + Auth Bridge -->
    <script src="js/auth-bridge.js"></script>
    <script src="js/global-nav.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{prof['business_name']}</h1>
            <div class="category-badge">{category_name}</div>
        </div>

        <div class="content">
            <div class="info-section">
                <h2>Contact Information</h2>
                <div class="contact-grid">
                    <div class="contact-item">
                        <strong>📧 Email</strong>
                        <a href="mailto:{prof['email']}">{prof['email']}</a>
                    </div>
                    <div class="contact-item">
                        <strong>📱 Phone</strong>
                        <a href="tel:{prof['phone']}">{prof['phone']}</a>
                    </div>
                    {f'''<div class="contact-item">
                        <strong>🌐 Website</strong>
                        <a href="{prof['website']}" target="_blank">{prof['website']}</a>
                    </div>''' if prof['website'] else ''}
                </div>
            </div>

            {f'''<div class="info-section">
                <h2>About</h2>
                <div class="description">
                    {prof['bio']}
                </div>
            </div>''' if prof['bio'] else ''}

            <div class="info-section">
                <h2>📱 QR Code Business Card</h2>
                <div style="text-align: center; background: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <p style="margin-bottom: 20px;">Scan to save contact info or share this profile</p>
                    <div id="qr-placeholder" style="display: inline-block; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="width: 200px; height: 200px; background: #e0e0e0; display: flex; align-items: center; justify-content: center; color: #666;">
                            <span>QR Code<br>Coming Soon</span>
                        </div>
                    </div>
                    <p style="margin-top: 15px; font-size: 0.9rem; color: #666;">
                        Profile URL: <a href="https://soulfra.github.io/stpetepros/professional-{prof['id']}.html" style="color: #667eea;">professional-{prof['id']}.html</a>
                    </p>
                </div>
            </div>

            <a href="../index.html" class="back-link">← Back to Directory</a>
        </div>

        <div class="footer">
            StPetePros - Tampa Bay Professional Directory<br>
            Simple. Local. Affordable.
        </div>
    </div>
</body>
</html>
"""

    return filename, html


def generate_index_page(professionals):
    """Generate main directory index page"""

    # Group by category
    by_category = {}
    for prof in professionals:
        category = prof['category'] or 'other'
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(prof)

    # Category display names
    categories = {
        'plumbing': 'Plumbing',
        'electrical': 'Electrical',
        'hvac': 'HVAC',
        'roofing': 'Roofing',
        'landscaping': 'Landscaping',
        'cleaning': 'Cleaning',
        'handyman': 'Handyman',
        'auto': 'Auto Repair',
        'real-estate': 'Real Estate',
        'other': 'Other Services'
    }

    # Generate category sections
    category_html = ""
    for category_key in sorted(by_category.keys()):
        category_name = categories.get(category_key, category_key.title())
        profs = by_category[category_key]

        category_html += f"""
        <div class="category-section">
            <h2>{category_name}</h2>
            <div class="professionals-grid">
"""

        for prof in profs:
            category_html += f"""
                <div class="professional-card">
                    <h3>{prof['business_name']}</h3>
                    <p class="phone">📱 {prof['phone']}</p>
                    <p class="email">📧 {prof['email']}</p>
                    <a href="professional-{prof['id']}.html" class="view-button">View Profile</a>
                </div>
"""

        category_html += """
            </div>
        </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StPetePros - Tampa Bay Professional Directory</title>
    <meta name="description" content="Tampa Bay's simplest professional directory. Find local plumbers, electricians, HVAC, and more.">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}

        .header h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        .stats {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }}

        .category-section {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .category-section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .professionals-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .professional-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
        }}

        .professional-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .professional-card h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.2rem;
        }}

        .professional-card p {{
            color: #666;
            margin-bottom: 5px;
            font-size: 0.9rem;
        }}

        .view-button {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 0.9rem;
            transition: all 0.3s;
        }}

        .view-button:hover {{
            background: #764ba2;
            transform: scale(1.05);
        }}

        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.9;
        }}

        .signup-cta {{
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin: 40px 0;
            color: white;
        }}

        .signup-cta h2 {{
            margin-bottom: 15px;
        }}

        .signup-cta a {{
            display: inline-block;
            margin-top: 15px;
            padding: 15px 40px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s;
        }}

        .signup-cta a:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌴 StPetePros</h1>
            <p>Tampa Bay Professional Directory</p>
        </div>

        <div class="stats">
            <strong>{len(professionals)} Local Professionals</strong> | Simple. Local. Affordable.
        </div>

        {category_html}

        <div class="signup-cta">
            <h2>Get Your Business Listed</h2>
            <p>One-time $10 fee • QR code business card • Lifetime listing</p>
            <a href="signup.html">Sign Up Now →</a>
        </div>

        <div class="footer">
            StPetePros - Tampa Bay Professional Directory<br>
            © {datetime.now().year} | Simple. Local. Affordable.
        </div>
    </div>
</body>
</html>
"""

    return html


def export_to_github_pages():
    """Main export function"""

    print()
    print("=" * 60)
    print("  Export Database to GitHub Pages")
    print("=" * 60)
    print()

    # Get professionals
    print("📊 Reading database...")
    professionals = get_professionals()
    print(f"   Found {len(professionals)} approved professionals")
    print()

    if not professionals:
        print("⚠️  No approved professionals found.")
        print("   Approve some professionals first!")
        print()
        return

    # Ensure output directory exists
    GITHUB_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate individual pages
    print("📝 Generating professional pages...")
    total_pros = len(professionals)
    # Extract actual professional IDs for keyboard navigation (handles gaps)
    professional_ids = [prof['id'] for prof in professionals]
    professional_ids_json = str(professional_ids)  # Convert to JSON-like string

    for i, prof in enumerate(professionals, 1):
        filename, html = generate_professional_page(prof, i, total_pros, professional_ids_json)
        output_path = GITHUB_PAGES_DIR / filename
        output_path.write_text(html)
        print(f"   {i}. {prof['business_name']} → {filename}")

    print()

    # Generate index page
    print("📝 Generating directory index...")
    index_html = generate_index_page(professionals)
    index_path = GITHUB_PAGES_DIR / 'index.html'
    index_path.write_text(index_html)
    print("   index.html generated")
    print()

    # Summary
    print("✅ Export complete!")
    print()
    print(f"📂 Files: {GITHUB_PAGES_DIR}")
    print(f"📄 Generated: {len(professionals)} professional pages + 1 index")
    print()
    print("Next steps:")
    print("  1. cd ~/Desktop/soulfra.github.io")
    print("  2. git add stpetepros/")
    print("  3. git commit -m 'Update directory'")
    print("  4. git push")
    print()
    print("🌐 Live at: https://soulfra.github.io/stpetepros/")
    print()


if __name__ == '__main__':
    export_to_github_pages()

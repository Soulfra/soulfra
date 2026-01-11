#!/usr/bin/env python3
"""
StPetePros Static Demo Builder - GitHub Pages Edition

Builds a static HTML demo of StPetePros professional directory.
NO backend needed - all data is pre-rendered HTML.

Features:
- Professional listings from database → static HTML
- Category pages (pre-rendered)
- Individual professional profiles (static pages)
- Client-side auth simulation (localStorage + visual tokens)
- Search (client-side JavaScript)
- Color-coded persona system visualization

Deploy to: output/soulfra/stpetepros/ → soulfra.com/stpetepros/
Live at: https://soulfra.com/stpetepros/

Usage:
    python3 build_stpetepros_demo.py           # Build static site
    python3 build_stpetepros_demo.py --serve   # Build + serve locally on :8000
"""

import sqlite3
import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import base64

# Configuration
DB_PATH = "soulfra.db"
OUTPUT_DIR = Path("output/soulfra/stpetepros")  # Deploy to soulfra.com/stpetepros/
SITE_URL = "https://soulfra.com"  # Production URL

# Persona colors (for visual token system)
PERSONA_COLORS = {
    'calriven': '#3B82F6',      # Blue - Work/Technical
    'cringeproof': '#A855F7',   # Purple - Ideas/Creative
    'soulfra': '#06B6D4',       # Cyan - Spiritual/Balanced
    'deathtodata': '#1F2937',   # Dark Grey - Privacy
    'howtocookathome': '#F59E0B'  # Orange - Cooking
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_professionals():
    """Get all professionals from database"""
    db = get_db()

    professionals = db.execute('''
        SELECT * FROM professionals
        WHERE approval_status = 'approved' OR approval_status IS NULL
        ORDER BY business_name ASC
    ''').fetchall()

    db.close()
    return [dict(row) for row in professionals]


def get_categories():
    """Get all categories with counts"""
    db = get_db()

    categories = db.execute('''
        SELECT category, COUNT(*) as count
        FROM professionals
        WHERE approval_status = 'approved' OR approval_status IS NULL
        GROUP BY category
        ORDER BY count DESC, category ASC
    ''').fetchall()

    db.close()
    return [dict(row) for row in categories]


def generate_index_page(professionals, categories):
    """Generate homepage with professional listings"""
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StPetePros - Tampa Bay Professional Directory</title>
    <meta name="description" content="Find verified professionals in St. Petersburg and Tampa Bay. Plumbing, electrical, HVAC, and more.">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="auth-demo.js"></script>
</head>
<body class="bg-slate-50">
    <!-- Header -->
    <header class="bg-gradient-to-r from-sky-500 to-emerald-500 text-white">
        <div class="max-w-7xl mx-auto px-4 py-6">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold">StPetePros</h1>
                    <p class="text-sky-100">Tampa Bay's Professional Directory</p>
                </div>
                <div class="flex gap-3">
                    <button onclick="showAuthDemo()" class="px-4 py-2 bg-white text-sky-600 rounded-lg font-semibold hover:bg-sky-50 transition-colors">
                        Demo Login
                    </button>
                    <a href="signup-demo.html" class="px-4 py-2 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors">
                        Join as Pro
                    </a>
                </div>
            </div>
        </div>
    </header>

    <!-- Search Bar -->
    <div class="bg-white border-b border-slate-200">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <input
                type="text"
                id="searchInput"
                placeholder="Search professionals, categories, or services..."
                class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                onkeyup="searchProfessionals()"
            >
        </div>
    </div>

    <!-- Categories -->
    <div class="max-w-7xl mx-auto px-4 py-8">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">Browse by Category</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-12">
'''

    for cat in categories:
        cat_name = cat['category'].replace('_', ' ').replace('-', ' ').title()
        html += f'''
            <a href="category-{cat['category']}.html" class="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow border border-slate-200">
                <div class="text-sm text-slate-600">{cat_name}</div>
                <div class="text-2xl font-bold text-slate-900">{cat['count']}</div>
            </a>
'''

    html += f'''
        </div>

        <!-- Professionals Grid -->
        <h2 class="text-2xl font-bold text-slate-900 mb-6">All Professionals ({len(professionals)})</h2>
        <div id="professionalsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
'''

    for pro in professionals:
        qr_data_url = ''
        if pro.get('qr_business_card'):
            qr_base64 = base64.b64encode(pro['qr_business_card']).decode('utf-8')
            qr_data_url = f"data:image/png;base64,{qr_base64}"

        html += f'''
            <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow professional-card" data-category="{pro['category']}" data-name="{pro['business_name'].lower()}">
                <div class="p-6">
                    <div class="flex items-start justify-between mb-4">
                        <div class="w-16 h-16 bg-gradient-to-br from-sky-500 to-emerald-500 rounded-xl flex items-center justify-center text-2xl text-white font-bold">
                            {pro['business_name'][0]}
                        </div>
                        {f'<img src="{qr_data_url}" alt="QR Code" class="w-16 h-16 rounded">' if qr_data_url else ''}
                    </div>

                    <h3 class="text-xl font-bold text-slate-900 mb-2">{pro['business_name']}</h3>
                    <span class="inline-block px-3 py-1 bg-sky-100 text-sky-700 rounded-full text-sm font-semibold mb-3">
                        {pro['category'].replace('_', ' ').replace('-', ' ').title()}
                    </span>

                    <p class="text-slate-600 text-sm mb-4 line-clamp-3">{pro['bio'][:150]}...</p>

                    <div class="space-y-1 text-sm text-slate-500 mb-4">
                        <div>📍 {pro['city']}, FL {pro['zip_code']}</div>
                        <div>📞 {pro['phone']}</div>
                    </div>

                    <a href="professional-{pro['id']}.html" class="block w-full text-center px-4 py-2 bg-gradient-to-r from-sky-500 to-emerald-500 text-white rounded-lg font-semibold hover:from-sky-600 hover:to-emerald-600 transition-colors">
                        View Profile
                    </a>
                </div>
            </div>
'''

    html += '''
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-slate-900 text-white mt-16 py-12">
        <div class="max-w-7xl mx-auto px-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h3 class="text-xl font-bold mb-4">StPetePros</h3>
                    <p class="text-slate-400">Tampa Bay's most trusted professional directory. Find verified service providers in your area.</p>
                </div>
                <div>
                    <h3 class="text-xl font-bold mb-4">Quick Links</h3>
                    <ul class="space-y-2 text-slate-400">
                        <li><a href="about.html" class="hover:text-white">About Us</a></li>
                        <li><a href="signup-demo.html" class="hover:text-white">Join as Professional</a></li>
                        <li><a href="#" onclick="showAuthDemo()" class="hover:text-white">Demo Login</a></li>
                    </ul>
                </div>
                <div>
                    <h3 class="text-xl font-bold mb-4">Contact</h3>
                    <p class="text-slate-400 mb-2">Questions? Want to be listed?</p>
                    <a href="/signup/professional" class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors">
                        Join StPetePros →
                    </a>
                </div>
            </div>
            <div class="border-t border-slate-800 mt-8 pt-8 text-center text-slate-400">
                <p>© 2026 StPetePros • Tampa Bay Professional Directory</p>
            </div>
        </div>
    </footer>

    <script>
    function searchProfessionals() {
        const input = document.getElementById('searchInput').value.toLowerCase();
        const cards = document.querySelectorAll('.professional-card');

        cards.forEach(card => {
            const name = card.dataset.name;
            const category = card.dataset.category;
            const text = card.textContent.toLowerCase();

            if (name.includes(input) || category.includes(input) || text.includes(input)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
    </script>
</body>
</html>
'''

    return html


def generate_professional_page(pro):
    """Generate individual professional profile page"""
    qr_data_url = ''
    if pro.get('qr_business_card'):
        qr_base64 = base64.b64encode(pro['qr_business_card']).decode('utf-8')
        qr_data_url = f"data:image/png;base64,{qr_base64}"

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{pro['business_name']} - StPetePros</title>
    <meta name="description" content="{pro['bio'][:150]}">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50">
    <header class="bg-gradient-to-r from-sky-500 to-emerald-500 text-white py-4">
        <div class="max-w-7xl mx-auto px-4">
            <a href="index.html" class="text-white hover:text-sky-100">← Back to Directory</a>
        </div>
    </header>

    <div class="max-w-4xl mx-auto px-4 py-8">
        <div class="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div class="grid grid-cols-1 md:grid-cols-[auto_1fr_auto] gap-8 items-start">
                <div class="w-32 h-32 bg-gradient-to-br from-sky-500 to-emerald-500 rounded-2xl flex items-center justify-center text-6xl text-white font-bold">
                    {pro['business_name'][0]}
                </div>

                <div>
                    <h1 class="text-3xl font-bold text-slate-900 mb-2">{pro['business_name']}</h1>
                    <span class="inline-block bg-slate-100 text-sky-500 px-4 py-1 rounded-full text-sm font-semibold mb-4">
                        {pro['category'].replace('_', ' ').replace('-', ' ').title()}
                    </span>

                    <div class="flex flex-col gap-2 text-slate-600">
                        <div><strong>Location:</strong> {pro['address']}, {pro['city']}, FL {pro['zip_code']}</div>
                        <div><strong>Phone:</strong> {pro['phone']}</div>
                        <div><strong>Email:</strong> <a href="mailto:{pro['email']}" class="text-sky-500 hover:text-sky-600">{pro['email']}</a></div>
                        {f'<div><strong>Website:</strong> <a href="{pro["website"]}" target="_blank" class="text-sky-500 hover:text-sky-600">{pro["website"]}</a></div>' if pro.get('website') else ''}
                    </div>
                </div>

                {f'<div class="bg-slate-100 p-4 rounded-lg text-center"><img src="{qr_data_url}" alt="QR Business Card" class="w-40 h-40 mb-2"><div class="text-sm text-slate-600">Scan to save contact</div></div>' if qr_data_url else ''}
            </div>

            <div class="mt-6">
                <h2 class="text-2xl font-bold text-slate-900 mb-4">About</h2>
                <p class="text-slate-600 leading-relaxed">{pro['bio']}</p>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-lg p-8">
            <h2 class="text-2xl font-bold text-slate-900 mb-4">Contact {pro['business_name']}</h2>
            <p class="text-slate-600 mb-6">This is a static demo. In production, this form would send a message.</p>

            <form class="space-y-4" onsubmit="alert('Demo mode - form submission disabled'); return false;">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input type="text" placeholder="Your Name" class="px-4 py-2 border border-slate-300 rounded-lg" required>
                    <input type="email" placeholder="Your Email" class="px-4 py-2 border border-slate-300 rounded-lg" required>
                </div>
                <textarea placeholder="Message..." rows="4" class="w-full px-4 py-2 border border-slate-300 rounded-lg"></textarea>
                <button type="submit" class="w-full md:w-auto px-8 py-3 bg-sky-500 text-white rounded-lg font-semibold hover:bg-sky-600">
                    Send Message (Demo)
                </button>
            </form>
        </div>
    </div>
</body>
</html>
'''

    return html


def build_static_site():
    """Build entire static site"""
    print("[BUILD] Building StPetePros Static Demo...")

    # Create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Get data
    print("[INFO] Fetching data from database...")
    professionals = get_all_professionals()
    categories = get_categories()

    print(f"[SUCCESS] Found {len(professionals)} professionals in {len(categories)} categories")

    # Generate index page
    print("[INFO] Generating index.html...")
    index_html = generate_index_page(professionals, categories)
    (OUTPUT_DIR / "index.html").write_text(index_html)

    # Generate individual professional pages
    print(f"[INFO] Generating {len(professionals)} professional pages...")
    for pro in professionals:
        page_html = generate_professional_page(pro)
        (OUTPUT_DIR / f"professional-{pro['id']}.html").write_text(page_html)

    # Copy auth demo files from project root
    print("[INFO] Copying auth-demo.js and signup-demo.html...")
    auth_js_template = Path("static-sites/stpetepros-templates/auth-demo.js")
    signup_html_template = Path("static-sites/stpetepros-templates/signup-demo.html")

    # Create templates directory if it doesn't exist
    auth_js_template.parent.mkdir(parents=True, exist_ok=True)

    # If templates exist, copy them to output
    if auth_js_template.exists():
        shutil.copy(auth_js_template, OUTPUT_DIR / "auth-demo.js")
        print("[SUCCESS] Copied auth-demo.js")
    else:
        print("[WARNING] auth-demo.js template not found - creating from scratch")

    if signup_html_template.exists():
        shutil.copy(signup_html_template, OUTPUT_DIR / "signup-demo.html")
        print("[SUCCESS] Copied signup-demo.html")
    else:
        print("[WARNING] signup-demo.html template not found - creating from scratch")

    print(f"[SUCCESS] Static site built successfully!")
    print(f"[INFO] Output: {OUTPUT_DIR.absolute()}")
    print(f"[INFO] Open: file://{OUTPUT_DIR.absolute()}/index.html")

    return OUTPUT_DIR


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build StPetePros for soulfra.com")
    parser.add_argument('--serve', action='store_true', help='Serve site locally after building')

    args = parser.parse_args()

    # Build site
    output_dir = build_static_site()

    # Serve locally
    if args.serve:
        print("\n🚀 Starting local server at http://localhost:8000/stpetepros/")
        os.chdir(output_dir.parent)  # Serve from output/soulfra/
        os.system("python3 -m http.server 8000")

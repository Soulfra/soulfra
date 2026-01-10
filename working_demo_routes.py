#!/usr/bin/env python3
"""
Working Demo Routes - Add Professional Profiles to Your Existing Site

Add this to your Flask app to show the 10 demo professionals:
- /pro/1 - Joe's Plumbing
- /pro/2 - Tampa Electric
- etc.

Usage in app.py:
    from working_demo_routes import professional_bp
    app.register_blueprint(professional_bp)
"""

from flask import Blueprint, render_template_string, request, redirect, url_for
import sqlite3


professional_bp = Blueprint('professional', __name__)


def get_professional(prof_id):
    """Get professional from database"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row

    prof = conn.execute('''
        SELECT * FROM professionals WHERE id = ?
    ''', (prof_id,)).fetchone()

    conn.close()

    return dict(prof) if prof else None


# ============================================================================
# Professional Profile Routes
# ============================================================================

@professional_bp.route('/pro/<int:prof_id>')
def show_professional(prof_id):
    """Show professional profile"""

    prof = get_professional(prof_id)

    if not prof:
        return "Professional not found", 404

    # Simple HTML template
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{prof['business_name']} - CringeProof</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2em;
        }}

        .header .category {{
            opacity: 0.9;
            font-size: 1.1em;
            text-transform: capitalize;
        }}

        .info-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .info-card h3 {{
            margin-top: 0;
            color: #667eea;
        }}

        .contact-btn {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            margin: 10px 10px 10px 0;
            font-weight: 600;
        }}

        .contact-btn:hover {{
            background: #5568d3;
        }}

        .verified-badge {{
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .location {{
            color: #666;
            margin-top: 10px;
        }}

        .back-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div style="margin-bottom: 20px;">
        <a href="/" class="back-link">← Back to Home</a>
    </div>

    <div class="header">
        <h1>{prof['business_name']}</h1>
        <div class="category">{prof['category'].replace('_', ' ')}</div>
        <div class="location">📍 {prof['city']}, {prof['state']} {prof['zip_code'] or ''}</div>
        {f'<div style="margin-top: 15px;"><span class="verified-badge">✓ Verified</span></div>' if prof['verified'] else ''}
    </div>

    <div class="info-card">
        <h3>About</h3>
        <p>{prof['bio']}</p>
    </div>

    <div class="info-card">
        <h3>Contact Information</h3>
        <p>
            <strong>Phone:</strong> {prof['phone']}<br>
            <strong>Email:</strong> {prof['email']}<br>
            {f"<strong>Website:</strong> <a href='{prof['website']}'>{prof['website']}</a><br>" if prof['website'] else ''}
            <strong>Address:</strong> {prof['address']}, {prof['city']}, {prof['state']} {prof['zip_code'] or ''}
        </p>

        <a href="tel:{prof['phone']}" class="contact-btn">📞 Call Now</a>
        <a href="mailto:{prof['email']}" class="contact-btn">✉️ Email</a>
    </div>

    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>Professional profile powered by <strong>CringeProof</strong></p>
        <p style="font-size: 0.9em;">🚀 Educational Authority Platform - Demo</p>
    </div>
</body>
</html>
"""

    return html


@professional_bp.route('/professionals')
def list_professionals():
    """List all professionals"""

    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row

    # Get all demo professionals
    pros = conn.execute('''
        SELECT * FROM professionals
        WHERE email LIKE '%@example.org'
        ORDER BY id
    ''').fetchall()

    conn.close()

    # Category emoji mapping
    category_emoji = {
        'plumbing': '🔧',
        'electrical': '⚡',
        'hvac': '❄️',
        'podcast': '🎙️',
        'youtube': '📹',
        'chef': '👨‍🍳',
        'meal_prep': '🍱',
        'gaming': '🎮',
        'tech': '💻',
        'privacy': '🔒'
    }

    # Build professional cards
    cards_html = ''
    for prof in pros:
        emoji = category_emoji.get(prof['category'], '💼')

        cards_html += f"""
        <a href="/pro/{prof['id']}" class="pro-card">
            <div class="pro-emoji">{emoji}</div>
            <h3>{prof['business_name']}</h3>
            <div class="pro-category">{prof['category'].replace('_', ' ').title()}</div>
            <div class="pro-location">📍 {prof['city']}, {prof['state']}</div>
            {f'<span class="verified-badge">✓ Verified</span>' if prof['verified'] else ''}
        </a>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Professional Directory - CringeProof</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}

        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }}

        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
        }}

        .pro-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .pro-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            text-decoration: none;
            color: #333;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 2px solid transparent;
        }}

        .pro-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}

        .pro-emoji {{
            font-size: 3em;
            margin-bottom: 15px;
        }}

        .pro-card h3 {{
            margin: 10px 0;
            color: #333;
        }}

        .pro-category {{
            color: #667eea;
            font-weight: 600;
            margin: 8px 0;
        }}

        .pro-location {{
            color: #666;
            font-size: 0.9em;
            margin: 8px 0;
        }}

        .verified-badge {{
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            margin-top: 10px;
        }}

        .back-link {{
            display: block;
            text-align: center;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            margin-top: 40px;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Professional Directory</h1>
    <div class="subtitle">
        Demo professionals powered by CringeProof Educational Authority Platform
    </div>

    <div class="pro-grid">
        {cards_html}
    </div>

    <a href="/" class="back-link">← Back to Home</a>
</body>
</html>
"""

    return html


# For integration testing
if __name__ == '__main__':
    print("""
Working Demo Routes - Professional Profiles

To integrate with your Flask app:

1. Add to app.py:
   from working_demo_routes import professional_bp
   app.register_blueprint(professional_bp)

2. Run your Flask app:
   python3 app.py

3. Visit:
   http://localhost:5001/professionals  (list all)
   http://localhost:5001/pro/1          (Joe's Plumbing)
   http://localhost:5001/pro/2          (Tampa Electric)
   etc.

This works on your EXISTING site (cringeproof.com).
No multi-domain complexity needed yet.
""")

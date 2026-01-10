"""
Professional Routes - Connect Templates to Database

Flask routes that make the professional/tutorial system functional:
- Serve professional sites at /professionals/<subdomain>
- Handle voice uploads with quality checking
- Generate pSEO landing pages on-the-fly
- Capture customer leads
- Professional dashboard

This connects:
- database.py (data storage)
- template_generator.py (HTML generation)
- voice_quality_checker.py (quality control)
- content_taxonomy.py (trade detection)
- pseo_generator.py (landing pages)
"""

from flask import Blueprint, render_template_string, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List

# Import our custom modules
from template_generator import generate_professional_site
from voice_quality_checker import check_voice_quality, generate_user_feedback
from content_taxonomy import detect_trade, get_trade_config, TRADE_CATEGORIES
from pseo_generator import generate_pseo_landing_pages, generate_landing_page_html

# Create Blueprint
professional_bp = Blueprint('professional', __name__)

DATABASE_PATH = 'soulfra.db'
UPLOAD_FOLDER = 'uploads/voice'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================================
# Database Helper Functions
# ============================================================================

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_professional_by_subdomain(subdomain: str) -> Optional[Dict]:
    """
    Get professional profile by subdomain

    Args:
        subdomain: Professional's subdomain (e.g., 'joesplumbing')

    Returns:
        Professional profile dict or None
    """
    conn = get_db_connection()
    professional = conn.execute(
        'SELECT * FROM professional_profile WHERE subdomain = ?',
        (subdomain,)
    ).fetchone()
    conn.close()

    return dict(professional) if professional else None


def get_professional_tutorials(professional_id: int) -> List[Dict]:
    """
    Get all published tutorials for a professional

    Args:
        professional_id: Professional's ID

    Returns:
        List of tutorial dicts
    """
    conn = get_db_connection()
    tutorials = conn.execute(
        'SELECT * FROM tutorial WHERE professional_id = ? AND status = "published" ORDER BY created_at DESC',
        (professional_id,)
    ).fetchall()
    conn.close()

    return [dict(tutorial) for tutorial in tutorials]


def get_tutorial_by_id(tutorial_id: int) -> Optional[Dict]:
    """Get tutorial by ID"""
    conn = get_db_connection()
    tutorial = conn.execute(
        'SELECT * FROM tutorial WHERE id = ?',
        (tutorial_id,)
    ).fetchone()
    conn.close()

    return dict(tutorial) if tutorial else None


def get_pseo_page(tutorial_id: int, slug: str) -> Optional[Dict]:
    """
    Get pSEO landing page by tutorial and slug

    Args:
        tutorial_id: Tutorial ID
        slug: Page slug (e.g., 'fix-leaky-faucet-miami-fl')

    Returns:
        Landing page dict or None
    """
    conn = get_db_connection()
    page = conn.execute(
        'SELECT * FROM pseo_landing_page WHERE tutorial_id = ? AND slug = ?',
        (tutorial_id, slug)
    ).fetchone()
    conn.close()

    return dict(page) if page else None


def save_lead(professional_id: int, name: str, phone: str, email: str,
              source_page: str, utm_source: str = None) -> int:
    """
    Save customer lead to database

    Args:
        professional_id: Professional receiving the lead
        name: Customer name
        phone: Customer phone
        email: Customer email
        source_page: Which page they came from
        utm_source: Attribution source

    Returns:
        Lead ID
    """
    conn = get_db_connection()
    cursor = conn.execute(
        '''INSERT INTO lead (professional_id, name, phone, email, source_page, utm_source, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'new', ?)''',
        (professional_id, name, phone, email, source_page, utm_source, datetime.now().isoformat())
    )
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return lead_id


def increment_page_stats(page_id: int, stat_type: str):
    """
    Increment page statistics (impressions/clicks/leads)

    Args:
        page_id: pSEO page ID
        stat_type: 'impressions', 'clicks', or 'leads'
    """
    conn = get_db_connection()
    conn.execute(
        f'UPDATE pseo_landing_page SET {stat_type} = {stat_type} + 1 WHERE id = ?',
        (page_id,)
    )
    conn.commit()
    conn.close()


# ============================================================================
# Professional Site Routes
# ============================================================================

@professional_bp.route('/professionals/<subdomain>')
def professional_site(subdomain):
    """
    Serve professional's main website

    URL: /professionals/joesplumbing

    Returns:
        Rendered professional site (homepage, tutorials, contact)
    """
    # Get professional profile
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return render_template_string("""
            <h1>Professional Not Found</h1>
            <p>The professional site "{{ subdomain }}" does not exist.</p>
            <a href="/">Back to Home</a>
        """, subdomain=subdomain), 404

    # Get their tutorials
    tutorials = get_professional_tutorials(professional['id'])

    # Generate complete professional site
    site_html = generate_professional_site(professional['id'])

    # Return homepage
    return render_template_string(site_html['homepage'],
                                   professional=professional,
                                   tutorials=tutorials)


@professional_bp.route('/professionals/<subdomain>/tutorials')
def professional_tutorials(subdomain):
    """
    Show all tutorials for a professional

    URL: /professionals/joesplumbing/tutorials
    """
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return "Professional not found", 404

    tutorials = get_professional_tutorials(professional['id'])

    # Generate tutorials page
    site_html = generate_professional_site(professional['id'])

    return render_template_string(site_html['tutorials_page'],
                                   professional=professional,
                                   tutorials=tutorials)


@professional_bp.route('/professionals/<subdomain>/tutorial/<int:tutorial_id>')
def view_tutorial(subdomain, tutorial_id):
    """
    View single tutorial

    URL: /professionals/joesplumbing/tutorial/5
    """
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return "Professional not found", 404

    tutorial = get_tutorial_by_id(tutorial_id)

    if not tutorial or tutorial['professional_id'] != professional['id']:
        return "Tutorial not found", 404

    # Return tutorial HTML content
    return render_template_string(tutorial['html_content'],
                                   professional=professional,
                                   tutorial=tutorial)


@professional_bp.route('/professionals/<subdomain>/license')
def professional_license(subdomain):
    """
    Show professional's license verification page

    URL: /professionals/joesplumbing/license
    """
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return "Professional not found", 404

    site_html = generate_professional_site(professional['id'])

    return render_template_string(site_html['license_page'],
                                   professional=professional)


@professional_bp.route('/professionals/<subdomain>/contact')
def professional_contact(subdomain):
    """
    Show contact page

    URL: /professionals/joesplumbing/contact
    """
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return "Professional not found", 404

    site_html = generate_professional_site(professional['id'])

    return render_template_string(site_html['contact_page'],
                                   professional=professional)


# ============================================================================
# pSEO Landing Page Routes
# ============================================================================

@professional_bp.route('/professionals/<subdomain>/l/<slug>')
def pseo_landing_page(subdomain, slug):
    """
    Serve pSEO landing page

    URL: /professionals/joesplumbing/l/fix-leaky-faucet-miami-fl

    These are auto-generated pages optimized for specific cities/keywords
    """
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return "Professional not found", 404

    # Parse slug to get tutorial_id (encoded in slug)
    # Slug format: {tutorial_slug}-{city}-{state}
    # For now, search for matching page

    conn = get_db_connection()
    page = conn.execute(
        '''SELECT p.* FROM pseo_landing_page p
           JOIN tutorial t ON p.tutorial_id = t.id
           WHERE t.professional_id = ? AND p.slug = ?''',
        (professional['id'], slug)
    ).fetchone()
    conn.close()

    if not page:
        return "Landing page not found", 404

    page = dict(page)

    # Track impression
    increment_page_stats(page['id'], 'impressions')

    # Get tutorial
    tutorial = get_tutorial_by_id(page['tutorial_id'])

    # Return landing page HTML
    return render_template_string(page['content_html'],
                                   professional=professional,
                                   tutorial=tutorial,
                                   page=page)


@professional_bp.route('/professionals/<subdomain>/l/<slug>/track-click', methods=['POST'])
def track_pseo_click(subdomain, slug):
    """
    Track when user clicks CTA on pSEO page

    Called via JavaScript when user clicks "Get Quote" or "Call Now"
    """
    professional = get_professional_by_subdomain(subdomain)

    if not professional:
        return jsonify({'error': 'Professional not found'}), 404

    # Find page
    conn = get_db_connection()
    page = conn.execute(
        '''SELECT p.* FROM pseo_landing_page p
           JOIN tutorial t ON p.tutorial_id = t.id
           WHERE t.professional_id = ? AND p.slug = ?''',
        (professional['id'], slug)
    ).fetchone()
    conn.close()

    if page:
        increment_page_stats(page['id'], 'clicks')

    return jsonify({'success': True})


# ============================================================================
# Voice Upload & Quality Check Routes
# ============================================================================

@professional_bp.route('/api/voice/upload', methods=['POST'])
def upload_voice_tutorial():
    """
    Upload voice recording and check quality

    POST /api/voice/upload

    Form data:
    - audio: Audio file (mp3/wav)
    - professional_id: Professional's ID

    Returns:
        JSON with quality check results
        If approved, saves to database as draft
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    professional_id = request.form.get('professional_id')

    if not professional_id:
        return jsonify({'error': 'professional_id required'}), 400

    # Save audio file
    filename = secure_filename(f"{datetime.now().timestamp()}_{audio_file.filename}")
    audio_path = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(audio_path)

    # TODO: Transcribe audio using Whisper/Deepgram
    # For now, simulate with request data
    transcript = request.form.get('transcript', '')

    if not transcript:
        return jsonify({'error': 'Transcript required for quality check'}), 400

    # Check voice quality
    quality_result = check_voice_quality(transcript)

    if not quality_result['approved']:
        # Return feedback to user
        feedback = generate_user_feedback(quality_result)

        return jsonify({
            'approved': False,
            'quality_score': quality_result['quality_score'],
            'issues': quality_result['issues'],
            'suggestions': quality_result['suggestions'],
            'feedback': feedback
        })

    # Quality check passed!
    # Auto-detect trade category
    detected_trade = detect_trade(transcript)

    # Save tutorial to database (as draft)
    conn = get_db_connection()
    cursor = conn.execute(
        '''INSERT INTO tutorial (professional_id, title, audio_url, transcript,
                                quality_score, status, created_at)
           VALUES (?, ?, ?, ?, ?, 'draft', ?)''',
        (
            professional_id,
            f"New Tutorial - {datetime.now().strftime('%Y-%m-%d')}",
            audio_path,
            transcript,
            quality_result['quality_score'],
            datetime.now().isoformat()
        )
    )
    tutorial_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'approved': True,
        'tutorial_id': tutorial_id,
        'quality_score': quality_result['quality_score'],
        'detected_trade': detected_trade,
        'message': 'Tutorial saved as draft! Ready to publish.'
    })


@professional_bp.route('/api/voice/check-quality', methods=['POST'])
def check_transcript_quality():
    """
    Check transcript quality without saving

    POST /api/voice/check-quality

    JSON body:
    {
        "transcript": "I'm going to show you..."
    }

    Returns:
        Quality check results
    """
    data = request.get_json()
    transcript = data.get('transcript', '')

    if not transcript:
        return jsonify({'error': 'transcript required'}), 400

    # Check quality
    quality_result = check_voice_quality(transcript)
    feedback = generate_user_feedback(quality_result)

    # Detect trade
    detected_trade = detect_trade(transcript)

    return jsonify({
        'approved': quality_result['approved'],
        'quality_score': quality_result['quality_score'],
        'issues': quality_result['issues'],
        'suggestions': quality_result['suggestions'],
        'feedback': feedback,
        'detected_trade': detected_trade,
        'metrics': quality_result['metrics']
    })


# ============================================================================
# Tutorial Publishing Routes
# ============================================================================

@professional_bp.route('/api/tutorial/<int:tutorial_id>/publish', methods=['POST'])
def publish_tutorial(tutorial_id):
    """
    Publish tutorial and generate pSEO pages

    POST /api/tutorial/123/publish

    This:
    1. Marks tutorial as published
    2. Generates HTML content from transcript
    3. Creates 50+ pSEO landing pages

    Returns:
        JSON with pSEO page count and URLs
    """
    tutorial = get_tutorial_by_id(tutorial_id)

    if not tutorial:
        return jsonify({'error': 'Tutorial not found'}), 404

    # Get professional
    professional = get_professional_by_subdomain(tutorial['professional_id'])

    # TODO: Generate HTML content from transcript using AI
    # For now, use basic formatting
    html_content = f"""
    <div class="tutorial-content">
        <h1>{tutorial['title']}</h1>
        <audio controls src="{tutorial['audio_url']}"></audio>
        <div class="transcript">
            <p>{tutorial['transcript']}</p>
        </div>
    </div>
    """

    # Update tutorial
    conn = get_db_connection()
    conn.execute(
        'UPDATE tutorial SET status = "published", html_content = ? WHERE id = ?',
        (html_content, tutorial_id)
    )
    conn.commit()
    conn.close()

    # Generate pSEO landing pages
    pseo_pages = generate_pseo_landing_pages(tutorial_id)

    return jsonify({
        'success': True,
        'tutorial_id': tutorial_id,
        'status': 'published',
        'pseo_pages_generated': len(pseo_pages),
        'sample_urls': [
            f"/professionals/{professional['subdomain']}/l/{page['slug']}"
            for page in pseo_pages[:5]  # Show first 5
        ]
    })


@professional_bp.route('/api/tutorial/<int:tutorial_id>/unpublish', methods=['POST'])
def unpublish_tutorial(tutorial_id):
    """
    Unpublish tutorial (set back to draft)

    POST /api/tutorial/123/unpublish
    """
    conn = get_db_connection()
    conn.execute(
        'UPDATE tutorial SET status = "draft" WHERE id = ?',
        (tutorial_id,)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'status': 'draft'})


# ============================================================================
# Lead Capture Routes
# ============================================================================

@professional_bp.route('/api/leads', methods=['POST'])
def capture_lead():
    """
    Capture customer lead

    POST /api/leads

    JSON body:
    {
        "professional_id": 123,
        "name": "John Doe",
        "phone": "(305) 555-1234",
        "email": "john@example.com",
        "source_page": "/professionals/joesplumbing/l/fix-faucet-miami",
        "utm_source": "google-ads"
    }

    Returns:
        JSON with lead ID
    """
    data = request.get_json()

    required_fields = ['professional_id', 'name', 'phone', 'email', 'source_page']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    # Save lead
    lead_id = save_lead(
        professional_id=data['professional_id'],
        name=data['name'],
        phone=data['phone'],
        email=data['email'],
        source_page=data['source_page'],
        utm_source=data.get('utm_source')
    )

    # If lead came from pSEO page, increment lead count
    if '/l/' in data['source_page']:
        slug = data['source_page'].split('/l/')[-1]

        # Find page and increment
        conn = get_db_connection()
        page = conn.execute(
            'SELECT id FROM pseo_landing_page WHERE slug = ?',
            (slug,)
        ).fetchone()

        if page:
            increment_page_stats(page['id'], 'leads')

        conn.close()

    return jsonify({
        'success': True,
        'lead_id': lead_id,
        'message': 'Lead captured successfully!'
    })


@professional_bp.route('/api/professionals/<int:professional_id>/leads')
def get_professional_leads(professional_id):
    """
    Get all leads for a professional

    GET /api/professionals/123/leads

    Returns:
        JSON array of leads
    """
    conn = get_db_connection()
    leads = conn.execute(
        'SELECT * FROM lead WHERE professional_id = ? ORDER BY created_at DESC',
        (professional_id,)
    ).fetchall()
    conn.close()

    return jsonify([dict(lead) for lead in leads])


# ============================================================================
# Professional Dashboard Routes
# ============================================================================

@professional_bp.route('/dashboard')
def professional_dashboard():
    """
    Professional's control panel

    Shows:
    - Tutorial stats
    - Lead summary
    - pSEO page performance
    - Upload new tutorial
    """
    # TODO: Get professional from session
    # For now, return basic dashboard HTML

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Professional Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .stat-card { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .upload-form { background: white; border: 2px dashed #ccc; padding: 40px; text-align: center; }
        </style>
    </head>
    <body>
        <h1>Professional Dashboard</h1>

        <div class="stat-card">
            <h2>Your Stats</h2>
            <p>Tutorials Published: <strong id="tutorial-count">-</strong></p>
            <p>Total Leads: <strong id="lead-count">-</strong></p>
            <p>pSEO Pages: <strong id="pseo-count">-</strong></p>
        </div>

        <div class="upload-form">
            <h2>Upload New Tutorial</h2>
            <form id="voice-upload" enctype="multipart/form-data">
                <input type="file" name="audio" accept="audio/*" required>
                <br><br>
                <textarea name="transcript" placeholder="Paste transcript here..." rows="10" cols="50"></textarea>
                <br><br>
                <button type="submit">Check Quality & Upload</button>
            </form>
            <div id="feedback"></div>
        </div>

        <script>
            document.getElementById('voice-upload').addEventListener('submit', async (e) => {
                e.preventDefault();

                const formData = new FormData(e.target);
                formData.append('professional_id', '1'); // TODO: Get from session

                const response = await fetch('/api/voice/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                const feedback = document.getElementById('feedback');

                if (result.approved) {
                    feedback.innerHTML = `
                        <div style="color: green; margin-top: 20px;">
                            ✅ Quality Check Passed! Score: ${result.quality_score}/10
                            <br>Detected Trade: ${result.detected_trade}
                            <br>Tutorial ID: ${result.tutorial_id}
                            <br><a href="/api/tutorial/${result.tutorial_id}/publish">Publish Now</a>
                        </div>
                    `;
                } else {
                    feedback.innerHTML = `
                        <div style="color: red; margin-top: 20px;">
                            ❌ Quality Issues Found (Score: ${result.quality_score}/10)
                            <br><br><strong>Issues:</strong>
                            <ul>${result.issues.map(issue => `<li>${issue}</li>`).join('')}</ul>
                            <br><strong>Suggestions:</strong>
                            <ul>${result.suggestions.map(sug => `<li>${sug}</li>`).join('')}</ul>
                        </div>
                    `;
                }
            });
        </script>
    </body>
    </html>
    """)


@professional_bp.route('/api/professionals/<int:professional_id>/stats')
def professional_stats(professional_id):
    """
    Get professional statistics

    GET /api/professionals/123/stats

    Returns:
        JSON with tutorial count, lead count, pSEO performance
    """
    conn = get_db_connection()

    # Tutorial count
    tutorial_count = conn.execute(
        'SELECT COUNT(*) as count FROM tutorial WHERE professional_id = ? AND status = "published"',
        (professional_id,)
    ).fetchone()['count']

    # Lead count
    lead_count = conn.execute(
        'SELECT COUNT(*) as count FROM lead WHERE professional_id = ?',
        (professional_id,)
    ).fetchone()['count']

    # pSEO page count and performance
    pseo_stats = conn.execute(
        '''SELECT COUNT(*) as page_count,
                  SUM(impressions) as total_impressions,
                  SUM(clicks) as total_clicks,
                  SUM(leads) as total_leads
           FROM pseo_landing_page p
           JOIN tutorial t ON p.tutorial_id = t.id
           WHERE t.professional_id = ?''',
        (professional_id,)
    ).fetchone()

    conn.close()

    return jsonify({
        'tutorial_count': tutorial_count,
        'lead_count': lead_count,
        'pseo_page_count': pseo_stats['page_count'] or 0,
        'total_impressions': pseo_stats['total_impressions'] or 0,
        'total_clicks': pseo_stats['total_clicks'] or 0,
        'pseo_leads': pseo_stats['total_leads'] or 0,
        'conversion_rate': round((pseo_stats['total_clicks'] / pseo_stats['total_impressions'] * 100), 2)
                          if pseo_stats['total_impressions'] else 0
    })


# ============================================================================
# Admin/Setup Routes
# ============================================================================

@professional_bp.route('/setup/create-professional', methods=['POST'])
def create_professional():
    """
    Create new professional profile

    POST /setup/create-professional

    JSON body:
    {
        "user_id": 123,
        "business_name": "Joe's Plumbing",
        "subdomain": "joesplumbing",
        "trade_category": "plumber",
        "license_number": "PL12345",
        "license_state": "FL",
        "tier": "free"
    }
    """
    data = request.get_json()

    required = ['user_id', 'business_name', 'subdomain', 'trade_category']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    # Validate trade category
    if data['trade_category'] not in TRADE_CATEGORIES:
        return jsonify({'error': f'Invalid trade_category. Must be one of: {list(TRADE_CATEGORIES.keys())}'}), 400

    # Create professional
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            '''INSERT INTO professional_profile
               (user_id, business_name, subdomain, trade_category, license_number,
                license_state, tier, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                data['user_id'],
                data['business_name'],
                data['subdomain'],
                data['trade_category'],
                data.get('license_number'),
                data.get('license_state'),
                data.get('tier', 'free'),
                datetime.now().isoformat()
            )
        )
        professional_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            'success': True,
            'professional_id': professional_id,
            'subdomain': data['subdomain'],
            'url': f"/professionals/{data['subdomain']}"
        })

    except sqlite3.IntegrityError as e:
        return jsonify({'error': f'Subdomain already exists or database error: {str(e)}'}), 400
    finally:
        conn.close()


# ============================================================================
# Integration with Existing Flask App
# ============================================================================

def register_professional_routes(app):
    """
    Register professional routes with main Flask app

    Usage in main app.py:
        from professional_routes import register_professional_routes
        register_professional_routes(app)
    """
    app.register_blueprint(professional_bp)
    print("✅ Professional routes registered!")
    print("   - /professionals/<subdomain>")
    print("   - /api/voice/upload")
    print("   - /api/leads")
    print("   - /dashboard")


if __name__ == '__main__':
    print("""
Professional Routes Module - Integration Points:

To use in your Flask app:

1. Import and register:
   from professional_routes import register_professional_routes
   register_professional_routes(app)

2. Key routes:
   - /professionals/<subdomain> - Professional sites
   - /professionals/<subdomain>/l/<slug> - pSEO pages
   - /api/voice/upload - Upload voice tutorials
   - /api/tutorial/<id>/publish - Publish tutorials
   - /api/leads - Capture customer leads
   - /dashboard - Professional control panel

3. Dependencies:
   - database.py (tables created)
   - template_generator.py (generates HTML)
   - voice_quality_checker.py (quality control)
   - content_taxonomy.py (trade detection)
   - pseo_generator.py (landing pages)

All systems connected! 🚀
""")

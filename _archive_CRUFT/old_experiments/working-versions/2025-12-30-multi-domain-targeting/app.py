"""
Flask App - Development Server
Run this to test newsletter locally before building static site
"""

from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, session, Response, jsonify, g, send_file
from datetime import datetime
import os
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.error

# Import from local database (not lib/ - we use the local soulfra.db)
from database import get_db, add_subscriber, get_posts, get_post_by_slug, init_db, add_post, get_stats
try:
    from lib.simple_markdown import markdown_to_html as markdown2_markdown
except ImportError:
    import markdown2
    def markdown2_markdown(text, extras=None):
        if extras:
            return markdown2.markdown(text, extras=extras)
        return markdown2.markdown(text)

# Import from local modules
from db_helpers import create_user, get_user_by_username, get_user_by_email, get_user_by_id, verify_password, add_comment, get_comments_for_post, get_posts_by_user, get_avatar_url
from url_shortener import get_username_from_shortcut
from config import BASE_URL, SECRET_KEY, ADMIN_PASSWORD, PLATFORM_VERSION, get_full_url, get_deployment_info
from practice_room import create_practice_room, join_room, record_voice_in_room, get_active_rooms
import subprocess
import csv
import io
import re
import html

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Load AI neural networks at startup (for predictions on posts)
try:
    from neural_network import load_neural_network
    app.networks = {
        'calriven': load_neural_network('calriven_technical_classifier'),
        'auditor': load_neural_network('theauditor_validation_classifier'),
        'deathtodata': load_neural_network('deathtodata_privacy_classifier'),
        'soulfra': load_neural_network('soulfra_judge')
    }
    print("✅ Loaded 4 neural networks for AI reasoning")
except Exception as e:
    print(f"⚠️  Neural networks not loaded: {e}")
    print("   Run train_context_networks.py to train networks")
    app.networks = None

# Setup subdomain routing for multi-tenant brand theming
from subdomain_router import setup_subdomain_routing
setup_subdomain_routing(app)

# Register QR Gallery routes for scan tracking and analytics
from gallery_routes import register_gallery_routes
register_gallery_routes(app)

# Register Image Admin routes for professional image generation
from image_admin_routes import register_image_admin_routes
register_image_admin_routes(app)

# Register Canvas routes for Netflix-style entry & workspace
from canvas_routes import register_canvas_routes
register_canvas_routes(app)

# Register Draw routes for mobile-friendly drawing & OCR learning
from draw_routes import register_draw_routes
register_draw_routes(app)

# Register Status routes for system visibility & navigation
from status_routes import register_status_routes
register_status_routes(app)

# Register Chat routes for unified Ollama chat interface
from chat_routes import register_chat_routes
register_chat_routes(app)

# Register Generator routes for unified content generation
from generator_routes import register_generator_routes
register_generator_routes(app)

# Register Business routes for invoice/receipt QR system
from business_routes import register_business_routes
register_business_routes(app)

# Register Web Domain Manager routes for multi-domain management + Ollama chat
from web_domain_manager_routes import register_web_domain_manager_routes
register_web_domain_manager_routes(app)

# Register Workflow routes for automation and AI-powered workflows
# TEMPORARILY DISABLED - getting basic domain editor working first
# from workflow_routes import register_workflow_routes
# register_workflow_routes(app)

# Register Admin routes for user management and permissions
# TEMPORARILY DISABLED - getting basic domain editor working first
# from admin_routes import register_admin_routes
# register_admin_routes(app)

# Register Studio API for visual development tools
# from studio_api import register_studio_api
# register_studio_api(app)

# Register Debug Lab API for interactive debugging learning
# from debug_lab import register_debug_lab
# register_debug_lab(app)

# Setup WebSocket support for real-time updates
# from websocket_server import setup_websockets
# socketio = setup_websockets(app)

# AUTO-LOAD PLUGIN FEATURES - Hot-reload modular feature system
# from plugin_loader import load_all_features
# load_all_features(app, auto_migrate=True)

# Register template filters
@app.template_filter('avatar_url')
def avatar_url_filter(user):
    """Template filter to get avatar URL for a user"""
    return get_avatar_url(
        email=user.get('email', ''),
        username=user.get('username', ''),
        is_ai_persona=user.get('is_ai_persona', False)
    )


@app.template_filter('markdown')
def markdown_filter(text):
    """
    Template filter to convert markdown to HTML

    Usage in templates: {{ post['content']|markdown|safe }}

    Handles both markdown and HTML content gracefully:
    - If content starts with HTML tags, returns as-is
    - Otherwise converts markdown to HTML
    """
    if not text:
        return ''

    # Check if content is already HTML (starts with common HTML tags)
    html_tags = ['<p>', '<h1>', '<h2>', '<h3>', '<div>', '<ul>', '<ol>', '<li>']
    if any(text.strip().startswith(tag) for tag in html_tags):
        # Already HTML, return as-is
        return text

    # Convert markdown to HTML
    return markdown2_markdown(
        text,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline', 'header-ids']
    )


@app.template_filter('timeago')
def timeago_filter(timestamp):
    """Convert timestamp to human-readable 'time ago' format"""
    from datetime import datetime, timezone

    if not timestamp:
        return ''

    # Handle string timestamps
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return timestamp  # Return as-is if can't parse

    # Ensure timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - timestamp

    seconds = diff.total_seconds()

    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(seconds / 31536000)
        return f'{years} year{"s" if years != 1 else ""} ago'


# Context processor to inject tags and config into all templates
@app.context_processor
def inject_globals():
    """Make tags, config, brand themes, and navigation available in all templates"""
    from db_helpers import get_all_tags
    import os

    # Load brand theme if requested via ?brand= query param
    brand_css = None
    brand_name = request.args.get('brand', '').lower()

    if brand_name in ['calriven', 'deathtodata', 'theauditor', 'soulfra', 'ocean-dreams', 'ocean-dreams-schooner', 'ocean-dreams-frigate', 'default']:
        theme_path = os.path.join(os.path.dirname(__file__), 'themes', f'{brand_name}.css')
        if os.path.exists(theme_path):
            with open(theme_path, 'r') as f:
                brand_css = f'<style>{f.read()}</style>'

    # Main navigation menu items
    main_nav = [
        {'name': '🌟 Hub', 'url': '/hub', 'description': 'All features in one place'},
        {'name': 'Posts', 'url': '/', 'description': 'Blog posts and articles'},
        {'name': 'Souls', 'url': '/souls', 'description': 'AI personas'},
        {'name': 'Reasoning', 'url': '/reasoning', 'description': 'AI reasoning dashboard'},
        {'name': 'ML', 'url': '/ml/dashboard', 'description': 'Machine learning'},
        {'name': 'Dashboard', 'url': '/dashboard', 'description': 'System overview'},
    ]

    # Tools menu (for dropdown)
    tools_nav = [
        {'name': 'API Tester', 'url': '/api-tester', 'icon': '🧪'},
        {'name': 'Brand Builder', 'url': '/brand-builder/start', 'icon': '💬'},
        {'name': 'Get API Key', 'url': '/freelancer-signup', 'icon': '🔑'},
        {'name': 'Code Browser', 'url': '/code', 'icon': '📝'},
        {'name': 'Shipyard', 'url': '/shipyard', 'icon': '🚢'},
    ]

    # Admin menu (for dropdown)
    admin_nav = [
        {'name': 'Admin Panel', 'url': '/admin', 'icon': '🛠️'},
        {'name': 'API Keys', 'url': '/admin/freelancers', 'icon': '👥'},
        {'name': 'Ollama Manager', 'url': '/admin/ollama', 'icon': '🧠'},
        {'name': 'Email Queue', 'url': '/admin/emails', 'icon': '📧'},
    ]

    # Current user info
    current_user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'is_authenticated': bool(session.get('user_id')),
        'is_admin': session.get('is_admin', False),
    }

    # Plugins navigation (auto-loaded from features/)
    loaded_plugins = getattr(app, 'loaded_plugins', [])
    plugins_nav = [
        {'name': p['name'], 'url': p['url'], 'icon': p.get('icon', '🔌')}
        for p in loaded_plugins
        if p.get('visible_in_nav', False)
    ]

    return dict(
        all_tags=get_all_tags(),
        BASE_URL=BASE_URL,
        PLATFORM_VERSION=PLATFORM_VERSION,
        brand_css=brand_css,
        main_nav=main_nav,
        tools_nav=tools_nav,
        admin_nav=admin_nav,
        plugins_nav=plugins_nav,
        current_user=current_user,
    )

# Initialize database on startup
if not os.path.exists('soulfra.db'):
    init_db()


# =============================================================================
# DEBUG & TESTING ROUTES - See what actually works
# =============================================================================

@app.route('/test')
def simple_test():
    """Simple test page - shows what actually works"""
    db = get_db()

    # Count things
    posts_count = db.execute('SELECT COUNT(*) as c FROM posts').fetchone()['c']
    brands_count = db.execute('SELECT COUNT(*) as c FROM brands').fetchone()['c']
    comments_count = db.execute('SELECT COUNT(*) as c FROM comments').fetchone()['c']

    # Count sessions
    try:
        sessions_count = db.execute('SELECT COUNT(*) as c FROM narrative_sessions').fetchone()['c']
    except:
        sessions_count = 0

    # Count Soulfra chapters
    soulfra_chapters = db.execute('''
        SELECT COUNT(*) as c FROM posts p
        JOIN brands b ON p.brand_id = b.id
        WHERE b.slug = 'soulfra'
    ''').fetchone()['c']

    db.close()

    # Test API (just check if route exists)
    api_works = True  # Assume yes, will test with button

    return render_template('simple_test.html',
                         template_works=True,
                         test_value='Hello from Python!',
                         db_works=True,
                         posts_count=posts_count,
                         brands_count=brands_count,
                         comments_count=comments_count,
                         sessions_count=sessions_count,
                         soulfra_chapters=soulfra_chapters,
                         api_works=api_works,
                         debug_info=f"Posts={posts_count}, Brands={brands_count}, Soulfra={soulfra_chapters}")


@app.route('/debug/system')
def debug_system():
    """Debug dashboard - shows Ollama status, models, AI comments, etc."""
    import urllib.request
    import urllib.error

    # Check Ollama status
    ollama_running = False
    models = []
    models_count = 0
    custom_models = []

    try:
        req = urllib.request.Request('http://localhost:11434/api/tags')
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = data.get('models', [])
            models_count = len(models)
            custom_models = [m for m in models if any(x in m['name'] for x in ['soulfra', 'deathtodata', 'calos'])]
            ollama_running = True
    except:
        pass

    # Get database stats
    db = get_db()
    posts_count = db.execute('SELECT COUNT(*) as c FROM posts').fetchone()['c']

    # Count AI comments
    ai_comments = db.execute('''
        SELECT COUNT(*) as c FROM comments
        WHERE user_id IN (SELECT id FROM users WHERE is_ai_persona = 1)
    ''').fetchone()['c']

    # Count AI users
    ai_users = db.execute('SELECT COUNT(*) as c FROM users WHERE is_ai_persona = 1').fetchone()['c']

    db.close()

    return render_template('debug_system.html',
                         ollama_running=ollama_running,
                         models=models,
                         models_count=models_count,
                         custom_models=custom_models,
                         posts_count=posts_count,
                         ai_comments=ai_comments,
                         ai_users=ai_users)


@app.route('/debug/test-ai-comment', methods=['POST'])
def debug_test_ai_comment():
    """Test endpoint - generates ONE AI comment and shows full details"""
    try:
        from ollama_auto_commenter import generate_ai_comment

        # Get a random post
        db = get_db()
        post = db.execute('SELECT * FROM posts ORDER BY RANDOM() LIMIT 1').fetchone()

        if not post:
            db.close()
            return jsonify({'success': False, 'error': 'No posts found in database'})

        post_id = post['id']
        post_title = post['title']

        # Pick a random brand to comment as
        brands = ['soulfra', 'deathtodata', 'calriven']
        import random
        brand_slug = random.choice(brands)

        db.close()

        # Generate comment (this will call Ollama)
        comment_id = generate_ai_comment(brand_slug=brand_slug, post_id=post_id)

        if comment_id:
            # Get the generated comment
            db = get_db()
            comment = db.execute('''
                SELECT c.*, u.display_name
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = ?
            ''', (comment_id,)).fetchone()
            db.close()

            return jsonify({
                'success': True,
                'comment_id': comment_id,
                'post_title': post_title,
                'ai_name': comment['display_name'],
                'comment_content': comment['content'],
                'ollama_request': f'Model: llama3.2:3b, Prompt: Comment on "{post_title[:50]}..."',
                'ollama_response': comment['content']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate comment',
                'details': 'Ollama may be down, or AI user may not exist for this brand'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'details': f'Exception type: {type(e).__name__}'
        })


@app.route('/')
def index():
    """
    Unified entry point with QR-first onboarding

    Brand-specific routing:
    - stpetepros.com → Professional directory homepage
    - Other domains → QR-first Canvas entry

    Shows:
    1. Live QR code for Netflix-style pairing
    2. Alternative paths (Narrative games, Content, Learning)
    3. Session tracking starts immediately
    """
    # Check if this is StPetePros domain
    if hasattr(g, 'active_brand') and g.active_brand:
        if g.active_brand.get('slug') == 'stpetepros':
            # Show professional directory homepage
            db = get_db()

            # Get counts for stats
            professional_count = db.execute('SELECT COUNT(*) as count FROM professionals').fetchone()['count'] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professionals'").fetchone() else 0

            review_count = db.execute('SELECT COUNT(*) as count FROM professional_reviews').fetchone()['count'] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professional_reviews'").fetchone() else 0

            # Get category counts (placeholder - will be populated when we have data)
            categories = {
                'plumbing': 0,
                'electrical': 0,
                'hvac': 0,
                'roofing': 0,
                'legal': 0,
                'landscaping': 0,
                'cleaning': 0,
                'pest_control': 0,
                'painting': 0,
                'pool_service': 0,
                'real_estate': 0,
                'auto_repair': 0
            }

            return render_template('stpetepros/homepage.html',
                professional_count=professional_count,
                review_count=review_count,
                category_count=len(categories),
                categories=categories
            )

    # Default: Show QR-first onboarding
    from canvas_integration import generate_canvas_qr

    # Generate QR for Canvas entry
    user_id = session.get('user_id')  # None for anonymous
    pairing_data = generate_canvas_qr(user_id=user_id, ttl_minutes=5)

    # Build QR image URL
    qr_url = url_for('canvas_qr_image',
                     pairing_token=pairing_data['pairing_token'],
                     _external=True)

    # Determine session status
    if user_id:
        session_status = f"Logged in as User #{user_id}"
    else:
        session_status = "Anonymous Session"

    return render_template('unified_entry.html',
        qr_url=qr_url,
        pairing_token=pairing_data['pairing_token'],
        session_status=session_status
    )


@app.route('/live')
def live():
    """Twitch-style live comment feed - all comments across all posts"""
    db = get_db()

    # Get recent comments (last 100, most recent first)
    comments = db.execute('''
        SELECT
            c.id,
            c.content,
            c.created_at,
            c.post_id,
            p.title as post_title,
            p.slug as post_slug,
            u.username,
            u.is_ai_persona
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
        LIMIT 100
    ''').fetchall()

    db.close()

    return render_template('live.html', comments=comments)


@app.route('/train')
def train():
    """Train the AI - supports two modes: colors (red vs blue) or posts (4-agent debate)"""
    import random
    from neural_network import load_neural_network
    from train_context_networks import extract_technical_features, extract_validation_features, extract_privacy_features
    import numpy as np

    mode = request.args.get('mode', 'colors')  # 'colors' or 'posts'

    # ===== MODE: POSTS (4-network debate) =====
    if mode == 'posts':
        # Load all 4 trained networks
        try:
            calriven = load_neural_network('calriven_technical_classifier')
            auditor = load_neural_network('theauditor_validation_classifier')
            deathtodata = load_neural_network('deathtodata_privacy_classifier')
            soulfra = load_neural_network('soulfra_judge')
        except Exception as e:
            flash(f'Context networks not trained yet. Run train_context_networks.py first. Error: {e}', 'error')
            return redirect(url_for('index'))

        # Import explain functions
        from train_context_networks import (
            explain_technical_features,
            explain_validation_features,
            explain_privacy_features
        )

        # Pick a random post
        db = get_db()
        posts = db.execute('SELECT * FROM posts WHERE published_at IS NOT NULL ORDER BY RANDOM() LIMIT 1').fetchall()
        db.close()

        if not posts:
            flash('No posts found. Create some posts first.', 'error')
            return redirect(url_for('index'))

        post = dict(posts[0])

        # Extract features for each network
        tech_features = extract_technical_features(post)
        validation_features = extract_validation_features(post)
        privacy_features = extract_privacy_features(post)

        # Get feature explanations (human-readable)
        tech_explanation = explain_technical_features(tech_features, post)
        validation_explanation = explain_validation_features(validation_features, post)
        privacy_explanation = explain_privacy_features(privacy_features, post)

        # Get predictions from each network
        calriven_pred = calriven.predict(np.array([tech_features]))[0][0]
        auditor_pred = auditor.predict(np.array([validation_features]))[0][0]
        deathtodata_pred = deathtodata.predict(np.array([privacy_features]))[0][0]

        # Soulfra judges based on the other 3
        soulfra_input = np.array([[calriven_pred, auditor_pred, deathtodata_pred]])
        soulfra_pred = soulfra.predict(soulfra_input)[0][0]

        predictions = {
            'calriven': {
                'score': float(calriven_pred),
                'label': 'TECHNICAL' if calriven_pred > 0.5 else 'NON-TECHNICAL',
                'features': tech_explanation
            },
            'auditor': {
                'score': float(auditor_pred),
                'label': 'VALIDATED' if auditor_pred > 0.5 else 'UNVALIDATED',
                'features': validation_explanation
            },
            'deathtodata': {
                'score': float(deathtodata_pred),
                'label': 'PRIVACY-FRIENDLY' if deathtodata_pred > 0.5 else 'PRIVACY-HOSTILE',
                'features': privacy_explanation
            },
            'soulfra': {
                'score': float(soulfra_pred),
                'label': 'APPROVED' if soulfra_pred > 0.5 else 'REJECTED',
                'inputs': {
                    'calriven': float(calriven_pred),
                    'auditor': float(auditor_pred),
                    'deathtodata': float(deathtodata_pred)
                }
            }
        }

        return render_template('train_posts.html', post=post, predictions=predictions, mode='posts')

    # ===== MODE: COLORS (default - red vs blue) =====
    else:
        # Load trained color classifier
        try:
            network = load_neural_network('color_classifier')
        except:
            flash('Color classifier not trained yet. Run test_neural_colors.py first.', 'error')
            return redirect(url_for('index'))

        # Generate random colors (left and right)
        # One will be reddish, one will be bluish
        if random.random() > 0.5:
            # Red on left, blue on right
            left_color = f'rgb({random.randint(150, 255)}, {random.randint(0, 100)}, {random.randint(0, 100)})'
            right_color = f'rgb({random.randint(0, 100)}, {random.randint(0, 150)}, {random.randint(150, 255)})'
            target_color = 'red'
        else:
            # Blue on left, red on right
            left_color = f'rgb({random.randint(0, 100)}, {random.randint(0, 150)}, {random.randint(150, 255)})'
            right_color = f'rgb({random.randint(150, 255)}, {random.randint(0, 100)}, {random.randint(0, 100)})'
            target_color = 'red'

        # Get stats from session (or initialize)
        stats = session.get('training_stats', {
            'total_trained': 0,
            'correct': 0,
            'accuracy': 0.0,
            'loss_history': []
        })

        # Get prediction from last round (if any)
        prediction = session.get('last_prediction', None)
        user_choice = session.get('last_user_choice', None)

        return render_template('train.html',
                             left_color=left_color,
                             right_color=right_color,
                             target_color=target_color,
                             stats=stats,
                             prediction=prediction,
                             user_choice=user_choice,
                             mode='colors')


@app.route('/train/predict', methods=['POST'])
def train_predict():
    """Network makes a prediction"""
    from neural_network import load_neural_network
    import numpy as np

    data = request.get_json()
    choice = data.get('choice')  # 'left' or 'right'
    left_color = data.get('left_color')  # 'rgb(255, 0, 0)'
    right_color = data.get('right_color')  # 'rgb(0, 0, 255)'
    target_color = data.get('target_color')  # 'red'

    # Parse RGB values
    def parse_rgb(rgb_str):
        nums = rgb_str.replace('rgb(', '').replace(')', '').split(',')
        return [int(n.strip()) / 255.0 for n in nums]  # Normalize to 0-1

    # Get the color the user clicked
    if choice == 'left':
        clicked_rgb = parse_rgb(left_color)
    else:
        clicked_rgb = parse_rgb(right_color)

    # Extract color features (HSV, temperature, etc.)
    from train_color_features import extract_color_features, explain_color_features
    features = extract_color_features(clicked_rgb)
    feature_explanations = explain_color_features(features, clicked_rgb)

    # Load network and predict
    network = load_neural_network('color_classifier')

    # Network input: [R, G, B] normalized
    prediction = network.predict(np.array([clicked_rgb]))

    # prediction is [warm_prob, cool_prob] or similar
    # For red vs blue: output > 0.5 = warm (red), < 0.5 = cool (blue)
    confidence = prediction[0][0] if prediction[0][0] > 0.5 else (1 - prediction[0][0])

    # Determine if network picked left or right
    # If clicked left and network says warm (>0.5) = predicted left
    # If clicked right and network says warm (>0.5) = predicted right
    is_warm = prediction[0][0] > 0.5

    if choice == 'left':
        network_choice = 'left' if is_warm else 'right'
    else:
        network_choice = 'right' if is_warm else 'left'

    # Calculate color wheel pointer position for SVG
    import math
    hue_degrees = features[0] * 360
    angle_rad = (hue_degrees - 90) * (math.pi / 180)
    pointer_x = 60 + 40 * math.cos(angle_rad)
    pointer_y = 60 + 40 * math.sin(angle_rad)

    # Store prediction in session with features
    session['last_prediction'] = {
        'choice': network_choice,
        'confidence': float(confidence),
        'features': feature_explanations,
        'hue_degrees': hue_degrees,  # For color wheel visualization
        'temperature': features[3],
        'saturation': features[1],
        'brightness': features[2],
        'pointer_x': pointer_x,
        'pointer_y': pointer_y
    }
    session['last_user_choice'] = choice

    return jsonify({
        'prediction': network_choice,
        'confidence': float(confidence),
        'features': feature_explanations
    })


@app.route('/train/feedback', methods=['POST'])
def train_feedback():
    """User provides feedback (correct/wrong) and network trains"""
    from neural_network import load_neural_network
    import numpy as np

    data = request.get_json()
    correct = data.get('correct')  # True/False
    user_choice = data.get('user_choice')  # 'left' or 'right'
    target_color = data.get('target_color')  # 'red'

    # Update stats
    stats = session.get('training_stats', {
        'total_trained': 0,
        'correct': 0,
        'accuracy': 0.0,
        'loss_history': []
    })

    stats['total_trained'] += 1
    if correct:
        stats['correct'] += 1

    stats['accuracy'] = stats['correct'] / stats['total_trained'] if stats['total_trained'] > 0 else 0

    # Train network (simplified - in reality you'd do backpropagation)
    # For now, just simulate loss decreasing
    current_loss = 0.1 / (1 + stats['total_trained'] * 0.01)  # Loss decreases over time
    stats['loss_history'].append(current_loss)

    # Keep last 50 loss values
    if len(stats['loss_history']) > 50:
        stats['loss_history'] = stats['loss_history'][-50:]

    session['training_stats'] = stats

    return jsonify({
        'loss': current_loss,
        'accuracy': stats['accuracy'],
        'total_trained': stats['total_trained']
    })


@app.route('/dashboard')
def dashboard():
    """
    Live Training Dashboard - r/place for AI!

    Shows:
    - All neural networks and their stats
    - Live training activity
    - Contributor leaderboard
    - Network comparisons
    """
    import sqlite3
    import json as json_module
    from datetime import datetime, timedelta

    db = get_db()

    # Get all neural networks
    networks = db.execute('''
        SELECT id, model_name, description, input_size, hidden_sizes,
               output_size, model_data, trained_at
        FROM neural_networks
        ORDER BY trained_at DESC
    ''').fetchall()

    networks_list = []
    for net in networks:
        model_data = json_module.loads(net[6]) if net[6] else {}
        accuracy_history = model_data.get('accuracy_history', [])
        loss_history = model_data.get('loss_history', [])

        networks_list.append({
            'id': net[0],
            'name': net[1],
            'description': net[2] or 'No description',
            'architecture': f"{net[3]} → {json_module.loads(net[4]) if net[4] else []} → {net[5]}",
            'accuracy': accuracy_history[-1] if accuracy_history else 0,
            'loss': loss_history[-1] if loss_history else 0,
            'epochs': len(loss_history),
            'trained_at': net[7],
            'accuracy_chart': accuracy_history[-20:] if len(accuracy_history) > 0 else [],  # Last 20 points
            'loss_chart': loss_history[-20:] if len(loss_history) > 0 else []
        })

    # Get recent training activity (feedback from users)
    activity_list = []
    try:
        activity = db.execute('''
            SELECT f.id, f.input_data, f.prediction, f.is_correct, f.created_at
            FROM feedback f
            ORDER BY f.created_at DESC
            LIMIT 50
        ''').fetchall()

        for act in activity:
            activity_list.append({
                'network': 'unknown',  # network_name column doesn't exist yet
                'input': json_module.loads(act[1]) if act[1] else {},
                'prediction': act[2],
                'correct': bool(act[3]),
                'timestamp': act[4]
            })
    except Exception as e:
        print(f"⚠️ Could not load activity: {e}")

    # Get contributor stats (how many times each user trained)
    contributors = db.execute('''
        SELECT COUNT(*) as training_count, 'Anonymous' as username
        FROM feedback
        GROUP BY username
        ORDER BY training_count DESC
        LIMIT 10
    ''').fetchall()

    contributor_list = []
    for contrib in contributors:
        contributor_list.append({
            'username': contrib[1] or 'Anonymous',
            'contributions': contrib[0]
        })

    db.close()

    return render_template('dashboard.html',
                         networks=networks_list,
                         activity=activity_list,
                         contributors=contributor_list,
                         total_networks=len(networks_list))


# =============================================================================
# PERSONAL WORKSPACE ROUTES (/me)
# =============================================================================

@app.route('/me')
def me_dashboard():
    """
    Personal workspace dashboard

    Shows user's quiz history, unlocks, stats, and quick actions.
    Like Anki personal deck - your own space.
    """
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access your workspace', 'error')
        return redirect(url_for('signup'))

    from user_workspace import get_workspace_data

    user_id = session['user_id']
    workspace = get_workspace_data(user_id)

    if 'error' in workspace:
        flash(workspace['error'], 'error')
        return redirect(url_for('index'))

    return render_template('me/dashboard.html', workspace=workspace)


@app.route('/me/quizzes')
def me_quizzes():
    """Quiz history page"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access your quiz history', 'error')
        return redirect(url_for('signup'))

    from user_workspace import get_quiz_history

    user_id = session['user_id']
    brand_slug = request.args.get('brand')  # Optional filter

    quizzes = get_quiz_history(user_id, brand_slug)

    return render_template('me/quizzes.html',
                         quizzes=quizzes,
                         filter_brand=brand_slug)


@app.route('/me/settings')
def me_settings():
    """Account settings page"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access settings', 'error')
        return redirect(url_for('signup'))

    db = get_db()
    user_id = session['user_id']

    user = db.execute('''
        SELECT id, username, email, display_name, bio, profile_pic
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))

    return render_template('me/settings.html', user=dict(user))


@app.route('/me/settings/update', methods=['POST'])
def me_settings_update():
    """Update user profile settings"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    from user_workspace import update_user_profile

    user_id = session['user_id']

    updates = {
        'username': request.form.get('username'),
        'display_name': request.form.get('display_name'),
        'bio': request.form.get('bio')
    }

    success, message = update_user_profile(user_id, updates)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('me_settings'))


@app.route('/me/export')
def me_export():
    """Export all user data (GDPR compliant)"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to export your data', 'error')
        return redirect(url_for('signup'))

    from user_data_export import export_user_data_json
    import json as json_module
    from datetime import datetime

    user_id = session['user_id']
    data_json = export_user_data_json(user_id, pretty=True)

    # Get username for filename
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    username = user['username'] if user else str(user_id)

    # Return as downloadable JSON file
    filename = f"{username}_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return Response(
        data_json,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@app.route('/me/delete', methods=['POST'])
def me_delete():
    """Delete user account (GDPR right to deletion)"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    from user_data_export import delete_user_account

    user_id = session['user_id']
    confirmation = request.form.get('confirmation', '')

    success, message = delete_user_account(user_id, confirmation)

    if success:
        # Log user out
        session.pop('user_id', None)
        flash(f'{message}. Your account has been permanently deleted.', 'success')
        return redirect(url_for('index'))
    else:
        flash(message, 'error')
        return redirect(url_for('me_settings'))


@app.route('/post/<slug>')
def post(slug):
    """Single post page"""
    post = get_post_by_slug(slug)
    if not post:
        flash('Post not found', 'error')
        return redirect(url_for('index'))

    # Get comments for post
    comments = get_comments_for_post(post['id'])

    # Get post author info
    author = get_user_by_id(post['user_id'])

    # Get categories and tags
    from db_helpers import get_post_categories, get_post_tags, get_reasoning_thread, get_reasoning_steps
    categories = get_post_categories(post['id'])
    tags = get_post_tags(post['id'])

    # Get reasoning thread and steps
    thread = get_reasoning_thread(post['id'])
    reasoning_steps = get_reasoning_steps(thread['id']) if thread else []

    # Check if post has a brand and inject brand CSS
    brand_css = None
    brand_name = None
    db = get_db()

    brand_row = db.execute('''
        SELECT b.*, bp.relevance_score
        FROM brands b
        JOIN brand_posts bp ON b.id = bp.brand_id
        WHERE bp.post_id = ?
        LIMIT 1
    ''', (post['id'],)).fetchone()

    if brand_row:
        brand = dict(brand_row)
        brand_name = brand['name']

        # Generate brand CSS
        from brand_css_generator import generate_brand_css

        try:
            brand_config = json.loads(brand['config_json']) if brand['config_json'] else {}
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"⚠️ Brand config error for post '{slug}': {e}")
            brand_config = {}

        # Convert color array to dict
        if 'colors' in brand_config and isinstance(brand_config['colors'], list):
            color_array = brand_config['colors']
            brand_config['colors'] = {
                'primary': color_array[0] if len(color_array) > 0 else '#667eea',
                'secondary': color_array[1] if len(color_array) > 1 else '#764ba2',
                'accent': color_array[2] if len(color_array) > 2 else '#f093fb'
            }

        brand_css = generate_brand_css(brand_config, include_style_tag=True)

    db.close()

    return render_template('post.html',
                         post=post,
                         comments=comments,
                         author=author,
                         categories=categories,
                         tags=tags,
                         reasoning_thread=thread,
                         reasoning_steps=reasoning_steps,
                         brand_css=brand_css,
                         brand_name=brand_name)


@app.route('/post/<slug>/comment', methods=['POST'])
def add_post_comment(slug):
    """Add a comment to a post"""
    # Check if user is logged in
    if not session.get('user_id'):
        flash('You must be logged in to comment', 'error')
        return redirect(url_for('login'))

    post = get_post_by_slug(slug)
    if not post:
        flash('Post not found', 'error')
        return redirect(url_for('index'))

    content = request.form.get('content', '').strip()
    parent_comment_id = request.form.get('parent_comment_id')

    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('post', slug=slug))

    # Add comment
    user_id = session.get('user_id')
    add_comment(post['id'], user_id, content, parent_comment_id if parent_comment_id else None)

    flash('Comment added successfully!', 'success')
    return redirect(url_for('post', slug=slug))


@app.route('/post/<slug>/discuss')
def post_discuss(slug):
    """Discussion workspace for a post"""
    # Check if user is logged in (could be restricted to admin only)
    if not session.get('user_id'):
        flash('You must be logged in to start a discussion', 'error')
        return redirect(url_for('login'))

    post = get_post_by_slug(slug)
    if not post:
        flash('Post not found', 'error')
        return redirect(url_for('index'))

    # Get or create active discussion session for this user/post
    from database import get_db
    db = get_db()

    existing_session = db.execute('''
        SELECT * FROM discussion_sessions
        WHERE post_id = ? AND user_id = ? AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
    ''', (post['id'], session.get('user_id'))).fetchone()

    if existing_session:
        session_id = existing_session['id']
    else:
        # Create new session
        cursor = db.execute('''
            INSERT INTO discussion_sessions (post_id, user_id, persona_name, status)
            VALUES (?, ?, 'calriven', 'active')
        ''', (post['id'], session.get('user_id')))
        session_id = cursor.lastrowid
        db.commit()

    # Get messages for this session
    messages = db.execute('''
        SELECT * FROM discussion_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    ''', (session_id,)).fetchall()

    # Get current session details
    session_details = db.execute('''
        SELECT * FROM discussion_sessions WHERE id = ?
    ''', (session_id,)).fetchone()

    db.close()

    return render_template('discussion_workspace.html',
                         post=post,
                         session_id=session_id,
                         session_details=session_details,
                         messages=[dict(m) for m in messages])


@app.route('/api/discussion/message', methods=['POST'])
def api_discussion_message():
    """
    Send a message or command in a discussion session

    POST body: {
        "session_id": 123,
        "content": "Your message or /command"
    }

    Returns: {
        "success": true,
        "ai_response": "...",
        "is_command": false
    }
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    session_id = data.get('session_id')
    content = data.get('content', '').strip()

    if not session_id or not content:
        return jsonify({'success': False, 'error': 'Missing session_id or content'}), 400

    from ollama_discussion import DiscussionSession

    try:
        # Initialize discussion session
        discussion = DiscussionSession(
            post_id=None,  # Will be loaded from session_id
            user_id=session.get('user_id'),
            session_id=session_id
        )

        # Check if it's a command
        is_command = content.startswith('/')

        if is_command:
            # Execute command
            result = discussion.execute_command(content)
            discussion.send_message(content, sender='user')
            discussion.send_message(result, sender='system')

            return jsonify({
                'success': True,
                'is_command': True,
                'result': result,
                'command': content
            })
        else:
            # Regular message - store it and get AI response
            discussion.send_message(content, sender='user')

            # Get AI response
            ai_response = discussion.call_ollama(content, include_post_context=True)
            discussion.send_message(ai_response, sender='ai')

            return jsonify({
                'success': True,
                'is_command': False,
                'user_message': content,
                'ai_response': ai_response
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discussion/finalize', methods=['POST'])
def api_discussion_finalize():
    """
    Finalize a discussion into a polished comment OR structured SOPs

    POST body: {
        "session_id": 123,
        "auto_post": false,
        "generate_sops": false,  # NEW: Generate structured SOPs instead of comment
        "sop_templates": ["brand_identity", "content_strategy"]  # Optional: specific templates
    }

    Returns: {
        "success": true,
        "draft_comment": "...",  # If generate_sops=false
        "sops": {...},  # If generate_sops=true
        "comment_id": 456  (if auto_post=true)
    }
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    session_id = data.get('session_id')
    auto_post = data.get('auto_post', False)
    generate_sops = data.get('generate_sops', False)  # NEW
    sop_templates = data.get('sop_templates')  # NEW

    if not session_id:
        return jsonify({'success': False, 'error': 'Missing session_id'}), 400

    from ollama_discussion import DiscussionSession

    try:
        discussion = DiscussionSession(
            post_id=None,
            user_id=session.get('user_id'),
            session_id=session_id
        )

        if generate_sops:
            # NEW: Generate structured SOPs
            sops = discussion.finalize_sops(template_ids=sop_templates)

            # Export SOPs as markdown for display
            from brand_sop_templates import SOPTemplateLibrary
            library = SOPTemplateLibrary()

            sops_markdown = {}
            for template_id, sop in sops.items():
                sops_markdown[template_id] = library.export_as_markdown(sop)

            return jsonify({
                'success': True,
                'sops': sops,
                'sops_markdown': sops_markdown,
                'count': len(sops)
            })
        else:
            # Original: Generate draft comment
            draft = discussion.finalize_comment()

            # Optionally post it
            comment_id = None
            if auto_post:
                comment_id = discussion.post_comment(draft)

            return jsonify({
                'success': True,
                'draft_comment': draft,
                'comment_id': comment_id,
                'posted': auto_post
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/brand/discuss/<brand_name>')
def brand_discuss(brand_name):
    """
    Brand discussion workspace (Wikipedia-style: Open Read, Login to Write)

    Collaborative AI discussion to build brand identity, messaging, and strategy.
    Uses all 4 AI personas to provide multi-perspective feedback.

    - Anonymous users: Can READ discussions, but see "Login to participate" banner
    - Logged-in users: Can READ and WRITE messages
    """
    from ollama_discussion import DiscussionSession

    # Optional login: user_id can be None for anonymous viewers
    user_id = session.get('user_id')
    is_anonymous = user_id is None

    db = get_db()

    if is_anonymous:
        # Anonymous user: Show public discussion (most recent session for this brand)
        existing_session = db.execute('''
            SELECT id FROM discussion_sessions
            WHERE brand_name = ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (brand_name,)).fetchone()

        if existing_session:
            session_id = existing_session['id']
            # Get context for brand
            context = {'type': 'brand', 'data': {'name': brand_name}}
            # Get public messages
            messages = db.execute('''
                SELECT * FROM discussion_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            ''', (session_id,)).fetchall()
        else:
            # No discussion exists yet
            session_id = None
            context = {'type': 'brand', 'data': {'name': brand_name}}
            messages = []

        session_details = db.execute(
            'SELECT * FROM discussion_sessions WHERE id = ?',
            (session_id,)
        ).fetchone() if session_id else None

    else:
        # Logged-in user: Can read AND write
        # Check if user has active brand discussion for this brand
        existing_session = db.execute('''
            SELECT id FROM discussion_sessions
            WHERE brand_name = ? AND user_id = ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (brand_name, user_id)).fetchone()

        if existing_session:
            # Resume existing session
            session_id = existing_session['id']
            discussion = DiscussionSession(session_id=session_id, user_id=user_id)
        else:
            # Create new session
            discussion = DiscussionSession(
                brand_name=brand_name,
                user_id=user_id,
                persona_name='calriven'  # Default persona
            )
            session_id = discussion.session_id

        # Get context and messages
        context = discussion.get_context()
        messages = discussion.get_messages()

        # Get session details
        session_details = db.execute(
            'SELECT * FROM discussion_sessions WHERE id = ?',
            (session_id,)
        ).fetchone()

    db.close()

    # Prepare template data
    template_data = {
        'session_id': session_id,
        'brand': context['data'] if context else {'name': brand_name},
        'messages': messages,
        'session_details': dict(session_details) if session_details else {},
        'discussion_type': 'brand',
        'is_anonymous': is_anonymous,
        'readonly': is_anonymous  # Anonymous users get read-only mode
    }

    return render_template('brand_workspace.html', **template_data)


@app.route('/api/assistant/message', methods=['POST'])
def api_assistant_message():
    """
    Universal AI Assistant - Route messages to appropriate backend

    POST body: {
        "message": "user message or /command",
        "context": {
            "url": "/post/my-post",
            "post_id": 42,
            "post": {...}
        }
    }

    Returns: {
        "success": true,
        "response": "AI response text",
        "artifact": {...}  (optional: QR code, predictions, etc.)
    }
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    context = data.get('context', {})

    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400

    try:
        from soulfra_assistant import SoulAssistant
        from database import get_post_by_slug

        # If on a post page, fetch the full post data
        if context.get('post_slug') and not context.get('post'):
            post = get_post_by_slug(context['post_slug'])
            if post:
                context['post'] = post
                context['post_id'] = post['id']

        assistant = SoulAssistant(
            user_id=session.get('user_id'),
            context=context
        )

        result = assistant.handle_message(message)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assistant/quick-actions', methods=['POST'])
def api_assistant_quick_actions():
    """
    Get quick actions based on current context

    POST body: {
        "context": {
            "url": "/post/my-post",
            "post_id": 42
        }
    }

    Returns: {
        "actions": [
            {"label": "Generate QR", "command": "/qr ..."},
            ...
        ]
    }
    """
    data = request.get_json() or {}
    context = data.get('context', {})

    try:
        from soulfra_assistant import SoulAssistant

        assistant = SoulAssistant(
            user_id=session.get('user_id'),
            context=context
        )

        actions = assistant.get_quick_actions()
        return jsonify({'success': True, 'actions': actions})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assistant/history', methods=['GET'])
def api_assistant_history():
    """
    Get conversation history for a session

    Query params:
        session_id: Session ID to load

    Returns conversation messages
    """
    session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400

    try:
        from soulfra_assistant import SoulAssistant

        assistant = SoulAssistant(
            user_id=session.get('user_id'),
            session_id=int(session_id)
        )

        messages = assistant.get_conversation_history()
        return jsonify({'success': True, 'messages': messages})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assistant/post-comment', methods=['POST'])
def api_assistant_post_comment():
    """
    Post a comment from the assistant

    POST body: {
        "comment": "The comment text",
        "context": {"post_id": 42}
    }

    Returns comment ID
    """
    data = request.get_json() or {}
    comment_text = data.get('comment', '').strip()
    context = data.get('context', {})

    if not comment_text:
        return jsonify({'success': False, 'error': 'Comment text required'}), 400

    if not context.get('post_id'):
        return jsonify({'success': False, 'error': 'post_id required in context'}), 400

    try:
        from soulfra_assistant import SoulAssistant

        assistant = SoulAssistant(
            user_id=session.get('user_id'),
            context=context
        )

        result = assistant.post_comment(comment_text)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# NARRATIVE CRINGEPROOF API - Story-driven game endpoints
# =============================================================================

@app.route('/api/narrative/start', methods=['POST'])
def api_narrative_start():
    """
    Start a new narrative game session

    POST body: {
        "brand_slug": "soulfra"
    }

    Returns session_id and story chapters
    """
    data = request.get_json() or {}
    brand_slug = data.get('brand_slug', 'soulfra')

    try:
        from narrative_cringeproof import NarrativeSession

        # Get or create user_id
        user_id = session.get('user_id', 1)

        # Create session
        narrative_session = NarrativeSession(user_id=user_id, brand_slug=brand_slug)

        # Get story data
        chapters = narrative_session.get_story_chapters()
        current_chapter = narrative_session.get_current_chapter()
        brand_info = narrative_session.get_brand_info()

        # Get AI Host narration for first chapter
        from ai_host import AIHost
        ai_host = AIHost(brand_slug=brand_slug)
        host_info = ai_host.get_host_info()

        # Generate intro narration using Ollama (falls back if Ollama offline)
        intro_narration = ai_host.narrate_chapter_intro(current_chapter)

        return jsonify({
            'success': True,
            'session_id': narrative_session.session_id,
            'brand': brand_info,
            'ai_host': host_info,
            'intro_narration': intro_narration,  # ← NEW: AI intro
            'chapters': chapters,
            'current_chapter': current_chapter['chapter_number'],
            'total_chapters': len(chapters)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/narrative/answer', methods=['POST'])
def api_narrative_answer():
    """
    Record player's answer to questions

    POST body: {
        "session_id": 123,
        "answers": [
            {"question_id": 0, "rating": 4},
            {"question_id": 1, "rating": 3}
        ]
    }
    """
    data = request.get_json() or {}
    session_id = data.get('session_id')
    answers = data.get('answers', [])

    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400

    try:
        from narrative_cringeproof import NarrativeSession

        user_id = session.get('user_id', 1)
        narrative_session = NarrativeSession(user_id=user_id, brand_slug='soulfra', session_id=session_id)

        # Record each answer and generate AI feedback
        from ai_host import AIHost
        ai_host = AIHost(brand_slug='soulfra')  # TODO: Get from session

        recorded = []
        for answer in answers:
            result = narrative_session.answer_question(
                question_id=answer['question_id'],
                rating=answer['rating']
            )

            # Generate AI feedback for this answer (uses Ollama)
            question_text = result.get('question', 'your choice')
            rating = answer['rating']
            feedback = ai_host.provide_feedback(question_text, rating)
            result['ai_feedback'] = feedback

            recorded.append(result)

        return jsonify({
            'success': True,
            'recorded': len(recorded),
            'answers': recorded  # ← Now includes 'ai_feedback' for each answer
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/narrative/advance', methods=['POST'])
def api_narrative_advance():
    """
    Advance to next chapter

    POST body: {
        "session_id": 123
    }
    """
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400

    try:
        from narrative_cringeproof import NarrativeSession

        user_id = session.get('user_id', 1)
        narrative_session = NarrativeSession(user_id=user_id, brand_slug='soulfra', session_id=session_id)

        result = narrative_session.advance_chapter()

        # Generate AI narration for chapter transition (uses Ollama)
        from ai_host import AIHost
        ai_host = AIHost(brand_slug='soulfra')  # TODO: Get from session

        if result.get('chapter_advanced'):
            completed_chapter = result.get('previous_chapter', 0)
            next_chapter = result.get('current_chapter', 1)
            player_choices = []  # TODO: Get from session

            transition_narration = ai_host.narrate_chapter_transition(
                completed_chapter=completed_chapter,
                next_chapter=next_chapter,
                player_choices=player_choices
            )
            result['transition_narration'] = transition_narration

        return jsonify({
            'success': True,
            **result  # ← Now includes 'transition_narration'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/narrative/complete/<int:session_id>', methods=['GET'])
def api_narrative_complete(session_id):
    """
    Get completion narration and summary

    Returns final AI Host narration
    """
    try:
        from narrative_cringeproof import NarrativeSession
        from ai_host import AIHost

        user_id = session.get('user_id', 1)
        narrative_session = NarrativeSession(user_id=user_id, brand_slug='soulfra', session_id=session_id)

        # Get progress summary
        progress = narrative_session.get_progress_summary()

        # Get AI Host completion narration
        ai_host = AIHost(brand_slug=progress['brand'])
        narration = ai_host.narrate_game_completion(
            total_chapters=progress['total_chapters'],
            player_summary=progress
        )

        return jsonify({
            'success': True,
            'narration': narration,
            'summary': progress
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ollama/status', methods=['GET'])
def api_ollama_status():
    """
    Check if Ollama is running and available

    Returns:
        {
            "available": bool,
            "url": "http://localhost:11434",
            "models": ["llama2", ...] if available
        }
    """
    import urllib.request
    import urllib.error

    ollama_host = 'http://localhost:11434'

    try:
        # Try to fetch models list from Ollama
        req = urllib.request.Request(f'{ollama_host}/api/tags')
        response = urllib.request.urlopen(req, timeout=2)
        result = json.loads(response.read().decode('utf-8'))

        models = [model['name'] for model in result.get('models', [])]

        return jsonify({
            'available': True,
            'url': ollama_host,
            'models': models,
            'message': f'Ollama is running with {len(models)} model(s)'
        })

    except urllib.error.URLError:
        return jsonify({
            'available': False,
            'url': ollama_host,
            'message': 'Ollama not running. Start with: ollama serve'
        })
    except Exception as e:
        return jsonify({
            'available': False,
            'url': ollama_host,
            'error': str(e)
        })


@app.route('/api/nudge/<username>', methods=['POST'])
def api_nudge_user(username):
    """
    Send a nudge to a user (Facebook poke-style)

    POST /api/nudge/bob
    Returns: {'success': True} or {'success': False, 'error': 'message'}
    """
    try:
        # Check if user is logged in
        from_user_id = session.get('user_id')
        if not from_user_id:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401

        # Get target user
        db = get_db()
        target_user = db.execute('SELECT id FROM users WHERE username = ?',
                                 (username,)).fetchone()
        db.close()

        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Send nudge
        from nudge_system import send_nudge
        success = send_nudge(from_user_id=from_user_id,
                           to_user_id=target_user['id'],
                           send_email=False)  # Don't spam with emails

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to send nudge'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/quiz-complete/<int:session_id>')
def quiz_complete(session_id):
    """
    Quiz completion page - shows AI friend, personality traits, and next steps

    URL: /quiz-complete/123
    """
    try:
        from profile_builder import get_user_profile, AI_PERSONAS

        # Get session to find user
        db = get_db()
        session_row = db.execute('''
            SELECT user_id, brand_slug, status FROM narrative_sessions WHERE id = ?
        ''', (session_id,)).fetchone()

        if not session_row:
            flash('Quiz session not found', 'error')
            return redirect(url_for('index'))

        if session_row['status'] != 'completed':
            flash('Quiz not yet completed', 'info')
            return redirect(url_for('index'))

        user_id = session_row['user_id']
        brand_slug = session_row['brand_slug']

        # Get user profile
        profile = get_user_profile(user_id)

        # Get user info
        user = db.execute('SELECT username, email FROM users WHERE id = ?',
                         (user_id,)).fetchone()

        db.close()

        if not profile:
            flash('Profile not yet built', 'error')
            return redirect(url_for('index'))

        # Get AI persona details
        matched_ai = profile['matched_ai']
        ai_persona = AI_PERSONAS.get(matched_ai, {})

        return render_template('quiz_complete.html',
                             session_id=session_id,
                             profile=profile,
                             ai_persona=ai_persona,
                             matched_ai=matched_ai,
                             brand_slug=brand_slug,
                             user=user)

    except Exception as e:
        print(f"Error loading completion page: {e}")
        flash('Error loading results', 'error')
        return redirect(url_for('index'))


@app.route('/choose')
def start_page():
    """Entry point - Choose your journey page (Soulfra, CalRiven, DeathToData)"""
    return render_template('start.html')


@app.route('/simple-test')
def simple_test_redirect():
    """System test page - shows tier system and image generation"""
    return redirect(url_for('tiers_showcase'))


@app.route('/cringeproof/narrative/<brand_slug>')
def narrative_game(brand_slug):
    """
    Render the narrative game UI for a brand

    URL: /cringeproof/narrative/soulfra
    """
    db = get_db()

    # Get brand info and convert to dict
    brand_row = db.execute('SELECT * FROM brands WHERE slug = ?', (brand_slug,)).fetchone()

    if not brand_row:
        flash('Brand not found', 'error')
        return redirect(url_for('index'))

    # Convert sqlite3.Row to dict for .get() method
    brand = dict(brand_row)

    # Get colors from brand (supports both old schema and config_json)
    if brand.get('color_primary'):
        # Use existing color columns
        primary_color = brand['color_primary'] or '#4a148c'
        secondary_color = brand['color_secondary'] or '#1a1a1a'
    else:
        # Fallback to config_json if it exists
        brand_config = json.loads(brand.get('config_json', '{}')) if brand.get('config_json') else {}
        colors = brand_config.get('colors', {})
        primary_color = colors.get('primary', '#4a148c')
        secondary_color = colors.get('secondary', '#1a1a1a')

    # Get AI Host info
    from ai_host import AIHost
    ai_host = AIHost(brand_slug=brand_slug)
    host_info = ai_host.get_host_info()

    return render_template('cringeproof/narrative.html',
        brand_slug=brand_slug,
        brand_name=brand['name'],
        brand_personality=brand.get('personality_tone', 'Dark and mysterious'),
        brand_primary_color=primary_color,
        brand_secondary_color=secondary_color,
        brand_bg_color='#0a0a0a',
        brand_text_color='#e0e0e0',
        ai_host_name=host_info['name']
    )


# =============================================================================
# WIKI CONCEPTS ROUTES - Knowledge Base System
# =============================================================================

@app.route('/wiki')
def wiki_index():
    """Wiki homepage - List all concepts grouped by category"""
    from wiki_concepts import WikiConcepts

    wiki = WikiConcepts()
    db = get_db()

    # Get all categories with concept counts
    categories = db.execute('''
        SELECT c.id, c.name, c.slug, COUNT(co.id) as concept_count
        FROM categories c
        LEFT JOIN concepts co ON c.id = co.category_id
        GROUP BY c.id
        ORDER BY c.name ASC
    ''').fetchall()

    # Get recent concepts
    recent_concepts = wiki.list_concepts(limit=10)

    return render_template('wiki_index.html',
        categories=[dict(cat) for cat in categories],
        recent_concepts=recent_concepts
    )


@app.route('/wiki/concept/<slug>')
def wiki_concept(slug):
    """View a single wiki concept page"""
    from wiki_concepts import WikiConcepts

    wiki = WikiConcepts()
    concept = wiki.get_concept(slug)

    if not concept:
        flash('Concept not found', 'error')
        return redirect(url_for('wiki_index'))

    # Get comments
    comments = wiki.get_concept_comments(concept['id'])

    # Check if concept has attached narrative
    has_narrative = concept.get('narrative_brand_slug') is not None

    return render_template('wiki_concept.html',
        concept=concept,
        comments=comments,
        has_narrative=has_narrative
    )


@app.route('/wiki/category/<slug>')
def wiki_category(slug):
    """List all concepts in a category"""
    from wiki_concepts import WikiConcepts

    wiki = WikiConcepts()
    concepts = wiki.list_concepts(category_slug=slug)

    db = get_db()
    category = db.execute('SELECT * FROM categories WHERE slug = ?', (slug,)).fetchone()

    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('wiki_index'))

    return render_template('wiki_category.html',
        category=dict(category),
        concepts=concepts
    )


@app.route('/category/<slug>')
def category_posts(slug):
    """Show posts filtered by category"""
    from db_helpers import get_posts_by_category, get_all_categories

    posts = get_posts_by_category(slug, limit=20)
    categories = get_all_categories()

    # Find the category name
    category = next((c for c in categories if c['slug'] == slug), None)

    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('index'))

    return render_template('category.html', posts=posts, category=category, categories=categories)


@app.route('/tag/<slug>')
def tag_posts(slug):
    """Show posts filtered by tag"""
    from db_helpers import get_posts_by_tag, get_all_tags

    posts = get_posts_by_tag(slug, limit=20)
    tags = get_all_tags()

    # Find the tag name
    tag = next((t for t in tags if t['slug'] == slug), None)

    if not tag:
        flash('Tag not found', 'error')
        return redirect(url_for('index'))

    return render_template('tag.html', posts=posts, tag=tag, tags=tags)


@app.route('/brand/<slug>/export')
def export_brand(slug):
    """Export brand as ZIP theme package"""
    from brand_theme_manager import BrandThemeManager

    manager = BrandThemeManager()
    zip_path = manager.export_brand(slug)

    if not zip_path:
        flash('Brand not found', 'error')
        return redirect(url_for('index'))

    # Serve the ZIP file
    return Response(
        open(zip_path, 'rb').read(),
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename={slug}-theme.zip'}
    )


@app.route('/brands/overview')
def brands_overview():
    """Simple overview of YOUR brands - domains, content, status"""
    db = get_db()

    # Get all brands with content counts
    brands = db.execute('''
        SELECT b.*,
               COUNT(DISTINCT p.id) as chapters,
               COUNT(DISTINCT c.id) as wiki_concepts
        FROM brands b
        LEFT JOIN posts p ON b.id = p.brand_id
        LEFT JOIN concepts c ON b.slug = c.narrative_brand_slug
        GROUP BY b.id
        ORDER BY b.id
    ''').fetchall()

    # Check which AI hosts exist
    from ai_host import HOST_PERSONAS

    brands_data = []
    for brand_row in brands:
        brand = dict(brand_row)
        brand['has_ai_host'] = brand['slug'] in HOST_PERSONAS
        brands_data.append(brand)

    db.close()

    return render_template('brands_overview.html', brands=brands_data)


@app.route('/brands/overview/update-domain', methods=['POST'])
def update_brand_domain():
    """Update domain for a brand"""
    brand_id = request.form.get('brand_id')
    domain = request.form.get('domain', '').strip()

    db = get_db()
    db.execute('UPDATE brands SET domain = ? WHERE id = ?', (domain, brand_id))
    db.commit()
    db.close()

    return redirect(url_for('brands_overview'))


@app.route('/brands')
def brands_marketplace():
    """Show brands marketplace - list all available brand themes"""
    db = get_db()

    # Get all brands
    brands_rows = db.execute('''
        SELECT id, name, slug, personality_tone, personality_traits, created_at FROM brands
        ORDER BY created_at DESC
    ''').fetchall()

    brands = [dict(b) for b in brands_rows]

    # Get image counts for each brand
    for brand in brands:
        image_count = db.execute('''
            SELECT COUNT(*) as count FROM images
            WHERE json_extract(metadata, '$.brand_id') = ?
        ''', (brand['id'],)).fetchone()['count']

        post_count = db.execute('''
            SELECT COUNT(*) as count FROM posts WHERE brand_id = ?
        ''', (brand['id'],)).fetchone()['count']

        brand['image_count'] = image_count
        brand['post_count'] = post_count

        # Get thumbnail image
        thumbnail = db.execute('''
            SELECT hash FROM images
            WHERE json_extract(metadata, '$.brand_id') = ?
            AND json_extract(metadata, '$.type') = 'thumbnail'
            LIMIT 1
        ''', (brand['id'],)).fetchone()

        brand['thumbnail_url'] = f"/i/{thumbnail['hash']}" if thumbnail else None

    return render_template('brands_marketplace.html', brands=brands)


@app.route('/brand/submit', methods=['GET', 'POST'])
def brand_submit():
    """Brand submission workflow - Upload and auto-review"""
    if request.method == 'GET':
        return render_template('brand_submit.html')

    # Handle ZIP upload
    if 'brand_zip' not in request.files:
        flash('❌ No file uploaded', 'error')
        return redirect(url_for('brand_submit'))

    uploaded_file = request.files['brand_zip']

    if uploaded_file.filename == '':
        flash('❌ No file selected', 'error')
        return redirect(url_for('brand_submit'))

    if not uploaded_file.filename.endswith('.zip'):
        flash('❌ File must be a ZIP archive', 'error')
        return redirect(url_for('brand_submit'))

    # Save uploaded ZIP temporarily
    import tempfile
    import os
    from brand_quality_gate import review_brand_submission

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, uploaded_file.filename)
    uploaded_file.save(zip_path)

    try:
        # Run ML auto-review
        review_result = review_brand_submission(zip_path)

        # Get form data
        brand_name = request.form.get('brand_name', 'Unknown Brand')
        brand_slug = request.form.get('brand_slug', 'unknown')
        description = request.form.get('description', '')
        license_type = request.form.get('license_type', 'cc0')

        # Save submission to database
        db = get_db()

        # Get current user (or None if not logged in)
        user_id = session.get('user_id', 1)  # Default to user 1 if not logged in

        # Insert submission record
        db.execute('''
            INSERT INTO brand_submissions (
                user_id,
                brand_name,
                brand_slug,
                description,
                license_type,
                zip_path,
                status,
                ml_score,
                ml_feedback,
                submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            user_id,
            brand_name,
            brand_slug,
            description,
            license_type,
            zip_path,  # Store path to ZIP file
            review_result['decision'],  # 'approved', 'rejected', 'manual_review'
            review_result['score'],
            json.dumps(review_result['suggestions'])
        ))

        submission_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # If auto-approved, create brand immediately
        if review_result['decision'] == 'approved':
            # Extract brand data and create in database
            import zipfile
            import yaml

            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Read brand.yaml
                brand_yaml_content = None
                for filename in zf.namelist():
                    if filename.endswith('brand.yaml') or filename.endswith('brand.yml'):
                        with zf.open(filename) as f:
                            brand_yaml_content = yaml.safe_load(f)
                        break

                if brand_yaml_content:
                    # Create brand in database
                    db.execute('''
                        INSERT INTO brands (
                            name,
                            slug,
                            personality,
                            tone,
                            config,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ''', (
                        brand_yaml_content.get('name', brand_name),
                        brand_yaml_content.get('slug', brand_slug),
                        brand_yaml_content.get('personality', ''),
                        brand_yaml_content.get('tone', ''),
                        json.dumps(brand_yaml_content)
                    ))

                    brand_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

                    # Create license entry
                    db.execute('''
                        INSERT INTO brand_licenses (
                            brand_id,
                            license_type,
                            attribution_required,
                            commercial_use_allowed,
                            modifications_allowed,
                            derivative_works_allowed,
                            license_text,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ''', (
                        brand_id,
                        license_type,
                        1 if license_type in ['cc-by', 'licensed'] else 0,
                        1 if license_type in ['cc0', 'cc-by', 'public'] else 0,
                        1 if license_type in ['cc0', 'cc-by', 'public'] else 0,
                        1 if license_type in ['cc0', 'cc-by', 'public'] else 0,
                        f'{license_type.upper()} License'
                    ))

                    # Create initial version
                    db.execute('''
                        INSERT INTO brand_versions (
                            brand_id,
                            version_number,
                            changelog,
                            zip_path,
                            created_at
                        ) VALUES (?, ?, ?, ?, datetime('now'))
                    ''', (
                        brand_id,
                        '1.0.0',
                        'Initial release',
                        zip_path
                    ))

        db.commit()
        db.close()

        # Show result
        if review_result['decision'] == 'approved':
            flash(f'✅ Brand approved! Score: {review_result["score"]}/100. Brand is now live in marketplace!', 'success')
        elif review_result['decision'] == 'manual_review':
            flash(f'⚠️  Brand needs review. Score: {review_result["score"]}/100. An admin will review your submission.', 'warning')
        else:
            flash(f'❌ Brand rejected. Score: {review_result["score"]}/100. See suggestions below.', 'error')

        # Store review result in session to display on result page
        session['last_submission_result'] = review_result
        session['last_submission_id'] = submission_id

        return redirect(url_for('brand_submission_result', submission_id=submission_id))

    except Exception as e:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        flash(f'❌ Error processing submission: {e}', 'error')
        return redirect(url_for('brand_submit'))


@app.route('/brand/submission/<int:submission_id>')
def brand_submission_result(submission_id):
    """Show submission review result"""
    db = get_db()

    submission = db.execute('''
        SELECT * FROM brand_submissions WHERE id = ?
    ''', (submission_id,)).fetchone()

    db.close()

    if not submission:
        flash('❌ Submission not found', 'error')
        return redirect(url_for('brands_marketplace'))

    # Get review result from session (if available)
    review_result = session.pop('last_submission_result', None)

    if not review_result:
        # Reconstruct from database
        review_result = {
            'score': submission['ml_score'],
            'decision': submission['status'],
            'message': f"Submission {submission['status']}",
            'suggestions': json.loads(submission['ml_feedback']) if submission['ml_feedback'] else []
        }

    return render_template('brand_submission_result.html',
                          submission=submission,
                          review_result=review_result)


@app.route('/brand/<slug>/rate', methods=['POST'])
def rate_brand(slug):
    """Submit a rating/review for a brand"""
    # Get brand
    db = get_db()
    brand = db.execute('SELECT id, name FROM brands WHERE slug = ?', (slug,)).fetchone()

    if not brand:
        flash('❌ Brand not found', 'error')
        return redirect(url_for('brands_marketplace'))

    # Get rating data
    rating = request.form.get('rating', type=int)
    review_text = request.form.get('review', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash('❌ Invalid rating (must be 1-5)', 'error')
        return redirect(url_for('brand_page', slug=slug))

    # Get current user (or default to user 1 if not logged in)
    user_id = session.get('user_id', 1)

    # Check if user already rated this brand
    existing = db.execute('''
        SELECT id FROM brand_ratings
        WHERE brand_id = ? AND user_id = ?
    ''', (brand['id'], user_id)).fetchone()

    if existing:
        # Update existing rating
        db.execute('''
            UPDATE brand_ratings
            SET rating = ?, review = ?, updated_at = datetime('now')
            WHERE id = ?
        ''', (rating, review_text, existing['id']))
        flash(f'✅ Updated your {rating}-star rating for {brand["name"]}', 'success')
    else:
        # Create new rating
        db.execute('''
            INSERT INTO brand_ratings (
                brand_id, user_id, rating, review, created_at, updated_at
            ) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', (brand['id'], user_id, rating, review_text))
        flash(f'✅ Thanks for your {rating}-star rating!', 'success')

    db.commit()
    db.close()

    return redirect(url_for('brand_page', slug=slug))


@app.route('/brand/<slug>/review/<int:review_id>/helpful', methods=['POST'])
def mark_review_helpful(slug, review_id):
    """Mark a review as helpful"""
    db = get_db()

    # Increment helpful count
    db.execute('''
        UPDATE brand_ratings
        SET helpful_count = helpful_count + 1
        WHERE id = ?
    ''', (review_id,))

    db.commit()
    db.close()

    flash('👍 Marked as helpful!', 'success')
    return redirect(url_for('brand_page', slug=slug))


@app.route('/brand/<slug>')
def brand_page(slug):
    """Show individual brand page with ratings and reviews"""
    db = get_db()

    # Get brand
    brand = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (slug,)).fetchone()

    if not brand:
        flash('❌ Brand not found', 'error')
        return redirect(url_for('brands_marketplace'))

    brand_dict = dict(brand)

    # Get license info
    license_info = db.execute('''
        SELECT * FROM brand_licenses WHERE brand_id = ?
    ''', (brand['id'],)).fetchone()

    brand_dict['license'] = dict(license_info) if license_info else None

    # Get ratings
    ratings = db.execute('''
        SELECT r.*, u.username, u.display_name
        FROM brand_ratings r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.brand_id = ?
        ORDER BY r.helpful_count DESC, r.created_at DESC
    ''', (brand['id'],)).fetchall()

    brand_dict['ratings'] = [dict(r) for r in ratings]

    # Calculate average rating
    if ratings:
        avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
        brand_dict['avg_rating'] = round(avg_rating, 1)
        brand_dict['rating_count'] = len(ratings)
    else:
        brand_dict['avg_rating'] = 0
        brand_dict['rating_count'] = 0

    # Get download count
    download_count = db.execute('''
        SELECT COUNT(*) as count FROM brand_downloads WHERE brand_id = ?
    ''', (brand['id'],)).fetchone()['count']

    brand_dict['download_count'] = download_count

    # Get version info
    latest_version = db.execute('''
        SELECT * FROM brand_versions
        WHERE brand_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (brand['id'],)).fetchone()

    brand_dict['latest_version'] = dict(latest_version) if latest_version else None

    # Get post count
    post_count = db.execute('''
        SELECT COUNT(*) as count FROM posts WHERE brand_id = ?
    ''', (brand['id'],)).fetchone()['count']

    brand_dict['post_count'] = post_count

    # Generate dynamic brand CSS
    from brand_css_generator import generate_brand_css

    # Parse brand config with error handling (fallback to defaults if broken)
    try:
        brand_config = json.loads(brand['config_json']) if brand['config_json'] else {}
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"⚠️ Brand config JSON error for '{brand['slug']}': {e}")
        print(f"   Falling back to default styling")
        brand_config = {}

    # Convert color array to dict format for CSS generator
    if 'colors' in brand_config and isinstance(brand_config['colors'], list):
        color_array = brand_config['colors']
        brand_config['colors'] = {
            'primary': color_array[0] if len(color_array) > 0 else '#667eea',
            'secondary': color_array[1] if len(color_array) > 1 else '#764ba2',
            'accent': color_array[2] if len(color_array) > 2 else '#f093fb'
        }

    brand_css = generate_brand_css(brand_config, include_style_tag=True)

    db.close()

    return render_template('brand_page.html', brand=brand_dict, brand_css=brand_css)


@app.route('/brand/<slug>/preview')
def brand_preview(slug):
    """
    Brand Preview - See how brand looks on actual content

    Shows sample posts styled with brand CSS so users can see
    what their content will look like with this brand applied.
    """
    db = get_db()

    # Get brand
    brand_row = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (slug,)).fetchone()

    if not brand_row:
        flash('Brand not found', 'error')
        db.close()
        return redirect(url_for('brands_marketplace'))

    brand = dict(brand_row)

    # Generate dynamic brand CSS
    from brand_css_generator import generate_brand_css

    # Parse brand config with error handling
    try:
        brand_config = json.loads(brand['config_json']) if brand['config_json'] else {}
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"⚠️ Brand config JSON error for '{brand['slug']}': {e}")
        brand_config = {}

    # Convert color array to dict format for CSS generator
    if 'colors' in brand_config and isinstance(brand_config['colors'], list):
        color_array = brand_config['colors']
        brand_config['colors'] = {
            'primary': color_array[0] if len(color_array) > 0 else '#667eea',
            'secondary': color_array[1] if len(color_array) > 1 else '#764ba2',
            'accent': color_array[2] if len(color_array) > 2 else '#f093fb'
        }

    brand_css = generate_brand_css(brand_config, include_style_tag=True)

    db.close()

    return render_template('brand_preview.html',
                         brand=brand,
                         brand_config=brand_config,
                         brand_css=brand_css)


@app.route('/brand/<slug>/debug')
def brand_debug(slug):
    """
    Brand Debug Panel - See source code, validation, error schemas

    Shows:
    - Raw config JSON from database
    - Parsed config (after processing)
    - Validation results (schema checks)
    - Generated CSS source code
    - Color transformations
    - Failure pattern detection
    """
    db = get_db()

    # Get brand
    brand_row = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (slug,)).fetchone()

    if not brand_row:
        flash('Brand not found', 'error')
        db.close()
        return redirect(url_for('brands_marketplace'))

    brand = dict(brand_row)

    # Validate config
    from brand_config_validator import validate_brand_config
    validation = validate_brand_config(brand['config_json'])

    # Get raw config JSON (pretty-printed)
    raw_config = brand['config_json'] if brand['config_json'] else '{}'
    try:
        parsed = json.loads(raw_config)
        raw_config = json.dumps(parsed, indent=2)
    except:
        pass

    # Parse brand config with error handling
    from brand_css_generator import generate_brand_css

    try:
        brand_config = json.loads(brand['config_json']) if brand['config_json'] else {}
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        brand_config = {}

    # Track color conversion
    color_conversion = None
    if 'colors' in brand_config and isinstance(brand_config['colors'], list):
        color_array = brand_config['colors']
        color_conversion = {
            'from': json.dumps(color_array),
            'to': json.dumps({
                'primary': color_array[0] if len(color_array) > 0 else '#667eea',
                'secondary': color_array[1] if len(color_array) > 1 else '#764ba2',
                'accent': color_array[2] if len(color_array) > 2 else '#f093fb'
            })
        }

        brand_config['colors'] = {
            'primary': color_array[0] if len(color_array) > 0 else '#667eea',
            'secondary': color_array[1] if len(color_array) > 1 else '#764ba2',
            'accent': color_array[2] if len(color_array) > 2 else '#f093fb'
        }

    # Generate CSS
    brand_css = generate_brand_css(brand_config, include_style_tag=True)

    # Parsed config pretty-printed
    parsed_config = json.dumps(brand_config, indent=2)

    db.close()

    return render_template('brand_debug.html',
                         brand=brand,
                         brand_config=brand_config,
                         validation=validation,
                         raw_config=raw_config,
                         parsed_config=parsed_config,
                         brand_css=brand_css,
                         color_conversion=color_conversion)


@app.route('/ai-network/debug')
def ai_network_debug():
    """
    AI Network Debug Panel - Visual inspection of neural network cast

    Shows:
    - All AI personas (status, activity)
    - Relevance testing (dry run)
    - Neural network weights
    - Color theory mapping
    - Training data
    """
    db = get_db()

    # Get all AI personas with stats
    personas = db.execute('''
        SELECT
            u.id,
            u.username,
            u.display_name,
            b.id as brand_id,
            b.name as brand_name,
            b.slug as brand_slug,
            b.personality,
            b.tone,
            b.config_json,
            COUNT(DISTINCT c.id) as comment_count,
            AVG(br.rating) as avg_rating
        FROM users u
        LEFT JOIN brands b ON u.username = b.slug
        LEFT JOIN comments c ON u.id = c.user_id
        LEFT JOIN brand_ratings br ON b.id = br.brand_id
        WHERE u.is_ai_persona = 1
        GROUP BY u.id
        ORDER BY comment_count DESC
    ''').fetchall()

    personas_list = []
    for p in personas:
        persona_dict = dict(p)

        # Get emoji
        emoji = '🤖'
        if persona_dict['config_json']:
            try:
                config = json.loads(persona_dict['config_json'])
                emoji = config.get('emoji', '🤖')
            except:
                pass

        persona_dict['emoji'] = emoji
        personas_list.append(persona_dict)

    # Get stats
    total_personas = len(personas_list)
    brand_personas = len([p for p in personas_list if p['brand_id'] is not None])
    ai_comments = db.execute('''
        SELECT COUNT(*) as count FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE u.is_ai_persona = 1
    ''').fetchone()['count']

    # Get neural networks
    neural_networks = db.execute('''
        SELECT * FROM neural_networks ORDER BY trained_at DESC
    ''').fetchall()
    neural_networks_list = [dict(nn) for nn in neural_networks]
    neural_networks_count = len(neural_networks_list)

    # Get brands with colors for color mapping
    brands_with_colors = db.execute('''
        SELECT id, name, slug, personality, tone, config_json
        FROM brands
        WHERE config_json IS NOT NULL
        LIMIT 20
    ''').fetchall()

    brands_color_list = []
    for brand in brands_with_colors:
        brand_dict = dict(brand)
        try:
            config = json.loads(brand_dict['config_json'])
            colors = config.get('colors', [])

            if isinstance(colors, list) and len(colors) > 0:
                primary_color = colors[0]
            elif isinstance(colors, dict):
                primary_color = colors.get('primary', '#667eea')
            else:
                primary_color = '#667eea'

            personality = brand_dict['personality'] or ''
            personality_traits = [t.strip() for t in personality.split(',')[:3]]

            brands_color_list.append({
                'name': brand_dict['name'],
                'primary_color': primary_color,
                'personality_traits': personality_traits,
                'color_temp': 'TODO',
                'color_sat': 'TODO',
                'color_bright': 'TODO'
            })
        except:
            pass

    # Get recent posts for testing
    recent_posts = db.execute('''
        SELECT id, title FROM posts ORDER BY published_at DESC LIMIT 10
    ''').fetchall()
    recent_posts_list = [dict(p) for p in recent_posts]

    db.close()

    return render_template('ai_network_debug.html',
                         total_personas=total_personas,
                         brand_personas=brand_personas,
                         ai_comments=ai_comments,
                         neural_networks_count=neural_networks_count,
                         personas=personas_list,
                         neural_networks=neural_networks_list,
                         brands_with_colors=brands_color_list,
                         recent_posts=recent_posts_list)


# ==============================================================================
# AI NETWORK API ROUTES - Wire debug panel buttons to actual working code
# ==============================================================================

@app.route('/api/ai/test-relevance/<int:post_id>')
def api_test_relevance(post_id):
    """
    Test which AI personas would comment on a post (dry run)

    Uses brand_ai_orchestrator to calculate relevance scores
    Returns JSON with which AIs would comment and why
    """
    from brand_ai_orchestrator import select_relevant_brands_for_post

    try:
        # Get relevant brands (returns list sorted by relevance)
        relevant_brands = select_relevant_brands_for_post(post_id, max_brands=10, min_relevance=0.1)

        # Get post title for context
        db = get_db()
        post = db.execute('SELECT title, content FROM posts WHERE id = ?', (post_id,)).fetchone()
        db.close()

        if not post:
            return jsonify({'error': 'Post not found'}), 404

        post_dict = dict(post)

        # Format results
        results = {
            'post_id': post_id,
            'post_title': post_dict['title'],
            'total_personas_evaluated': len(relevant_brands),
            'personas': [
                {
                    'username': brand['username'],
                    'brand_name': brand['brand_name'],
                    'relevance': round(brand['relevance'], 3),
                    'would_comment': brand['relevance'] > 0.3,  # Free tier threshold
                    'reason': f"Relevance score: {round(brand['relevance'], 3)} ({'above' if brand['relevance'] > 0.3 else 'below'} threshold)"
                }
                for brand in relevant_brands
            ]
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/training-data/<username>')
def api_training_data(username):
    """
    Get training data for an AI persona

    Shows what this AI has learned from:
    - Brand configuration (personality, tone)
    - Posts it has commented on
    - Ratings it has received
    """
    db = get_db()

    # Get persona
    persona = db.execute('''
        SELECT u.*, b.id as brand_id, b.name as brand_name,
               b.personality, b.tone, b.config_json
        FROM users u
        LEFT JOIN brands b ON u.username = b.slug
        WHERE u.username = ? AND u.is_ai_persona = 1
    ''', (username,)).fetchone()

    if not persona:
        db.close()
        return jsonify({'error': 'AI persona not found'}), 404

    persona_dict = dict(persona)

    # Get posts this AI has commented on
    posts_commented = db.execute('''
        SELECT p.id, p.title, p.slug, COUNT(c.id) as comment_count
        FROM posts p
        JOIN comments c ON p.id = c.post_id
        WHERE c.user_id = ?
        GROUP BY p.id
        ORDER BY comment_count DESC
        LIMIT 20
    ''', (persona_dict['id'],)).fetchall()

    # Get ratings for this brand
    ratings = db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
        FROM brand_ratings
        WHERE brand_id = ?
    ''', (persona_dict['brand_id'],)).fetchone() if persona_dict.get('brand_id') else None

    db.close()

    # Parse config
    try:
        config = json.loads(persona_dict['config_json']) if persona_dict.get('config_json') else {}
    except:
        config = {}

    return jsonify({
        'username': username,
        'display_name': persona_dict['display_name'],
        'brand_name': persona_dict.get('brand_name'),
        'training_sources': {
            'personality': persona_dict.get('personality', 'Not specified'),
            'tone': persona_dict.get('tone', 'Not specified'),
            'config': config,
            'posts_commented': len(posts_commented),
            'avg_rating': round(ratings['avg_rating'], 2) if ratings and ratings['avg_rating'] else None,
            'rating_count': ratings['rating_count'] if ratings else 0
        },
        'recent_posts': [
            {
                'id': p['id'],
                'title': p['title'],
                'slug': p['slug'],
                'comments': p['comment_count']
            }
            for p in posts_commented
        ]
    })


@app.route('/api/ai/regenerate-all', methods=['POST'])
def api_regenerate_all():
    """
    Regenerate all AI personas

    Calls brand_ai_persona_generator.generate_all_brand_ai_personas()
    """
    from brand_ai_persona_generator import generate_all_brand_ai_personas

    try:
        count = generate_all_brand_ai_personas(tier='free')
        return jsonify({
            'success': True,
            'personas_created': count,
            'message': f'Successfully generated {count} AI personas'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/retrain-networks', methods=['POST'])
def api_retrain_networks():
    """
    Retrain all neural networks

    For now, just counts existing networks
    TODO: Actually train color → personality NN
    """
    db = get_db()

    # Count existing networks
    networks = db.execute('''
        SELECT model_name, COUNT(*) as count
        FROM neural_networks
        GROUP BY model_name
    ''').fetchall()

    db.close()

    return jsonify({
        'success': True,
        'message': 'Neural network retraining not yet implemented',
        'existing_networks': [
            {
                'name': n['model_name'],
                'count': n['count']
            }
            for n in networks
        ],
        'todo': 'Build brand_color_neural_network.py to train color → personality'
    })


@app.route('/api/ai/clear-comments', methods=['POST'])
def api_clear_comments():
    """
    Delete all AI comments (use with caution!)

    Removes all comments made by AI personas for testing/debugging
    """
    db = get_db()

    # Count comments before deletion
    count_before = db.execute('''
        SELECT COUNT(*) as count
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE u.is_ai_persona = 1
    ''').fetchone()['count']

    # Delete AI comments
    db.execute('''
        DELETE FROM comments
        WHERE user_id IN (
            SELECT id FROM users WHERE is_ai_persona = 1
        )
    ''')

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'comments_deleted': count_before,
        'message': f'Deleted {count_before} AI comments'
    })


@app.route('/api/ai/export-debug-data')
def api_export_debug_data():
    """
    Export all AI network debug data as JSON

    Useful for:
    - Testing
    - External analysis
    - Backup
    """
    db = get_db()

    # Get all personas
    personas = db.execute('''
        SELECT u.id, u.username, u.display_name, u.email, u.bio,
               b.id as brand_id, b.name as brand_name, b.slug as brand_slug,
               b.personality, b.tone, b.config_json
        FROM users u
        LEFT JOIN brands b ON u.username = b.slug
        WHERE u.is_ai_persona = 1
    ''').fetchall()

    # Get all neural networks
    networks = db.execute('''
        SELECT * FROM neural_networks
    ''').fetchall()

    # Get AI comments stats
    comment_stats = db.execute('''
        SELECT u.username, COUNT(c.id) as comment_count
        FROM users u
        LEFT JOIN comments c ON u.id = c.user_id
        WHERE u.is_ai_persona = 1
        GROUP BY u.id
    ''').fetchall()

    db.close()

    # Build export data (convert Row objects to dicts)
    personas_list = []
    for p in personas:
        p_dict = dict(p)
        personas_list.append({
            'id': p_dict['id'],
            'username': p_dict['username'],
            'display_name': p_dict['display_name'],
            'email': p_dict['email'],
            'bio': p_dict['bio'] if p_dict['bio'] else '',
            'brand_id': p_dict['brand_id'],
            'brand_name': p_dict['brand_name'],
            'brand_slug': p_dict['brand_slug'],
            'personality': p_dict['personality'],
            'tone': p_dict['tone'],
            'config': json.loads(p_dict['config_json']) if p_dict['config_json'] else {}
        })

    export_data = {
        'generated_at': datetime.now().isoformat(),
        'total_personas': len(personas),
        'personas': personas_list,
        'neural_networks': [
            {
                'id': n['id'],
                'model_name': n['model_name'],
                'input_size': n['input_size'],
                'hidden_sizes': n['hidden_sizes'],
                'output_size': n['output_size'],
                'trained_at': n['trained_at']
            }
            for n in networks
        ],
        'comment_stats': [
            {
                'username': s['username'],
                'comment_count': s['comment_count']
            }
            for s in comment_stats
        ]
    }

    return jsonify(export_data)


@app.route('/ai-network/visualize/<model_name>')
def ai_network_visualize(model_name):
    """
    Visualize neural network weights

    Shows:
    - Network architecture
    - Weight matrices
    - Bias vectors
    - Training history (if available)
    """
    db = get_db()

    # Get network
    network = db.execute('''
        SELECT * FROM neural_networks
        WHERE model_name = ?
        ORDER BY trained_at DESC
        LIMIT 1
    ''', (model_name,)).fetchone()

    db.close()

    if not network:
        flash(f'Neural network "{model_name}" not found', 'error')
        return redirect(url_for('ai_network_debug'))

    network_dict = dict(network)

    # Parse model data (weights and biases)
    try:
        model_data = json.loads(network_dict['model_data']) if network_dict['model_data'] else {}
        weights = {
            'weights_ih': model_data.get('weights_ih', []),
            'weights_ho': model_data.get('weights_ho', [])
        }
        biases = {
            'bias_h': model_data.get('bias_h', []),
            'bias_o': model_data.get('bias_o', [])
        }
    except:
        weights = {}
        biases = {}

    return render_template('ai_network_visualize.html',
                         model_name=model_name,
                         network=network_dict,
                         weights=weights,
                         biases=biases)


@app.route('/ai-network/persona/<username>')
def ai_persona_detail(username):
    """Detail page for an AI persona"""
    db = get_db()

    persona = db.execute('''
        SELECT u.*, b.name as brand_name, b.slug as brand_slug
        FROM users u
        LEFT JOIN brands b ON u.username = b.slug
        WHERE u.username = ? AND u.is_ai_persona = 1
    ''', (username,)).fetchone()

    if not persona:
        flash('AI persona not found', 'error')
        db.close()
        return redirect(url_for('ai_network_debug'))

    persona_dict = dict(persona)

    # Get comments by this persona
    comments = db.execute('''
        SELECT c.*, p.title as post_title, p.slug as post_slug
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
        LIMIT 50
    ''', (persona_dict['id'],)).fetchall()

    db.close()

    return render_template('ai_persona_detail.html',
                         persona=persona_dict,
                         comments=[dict(c) for c in comments])


@app.route('/qr/brand/<slug>')
def brand_qr_code(slug):
    """
    Serve brand-specific QR code (dynamic generation)

    If 'to' parameter provided, track scan and redirect.
    Otherwise, return QR code image.
    """
    # Check if this is a scan (has 'to' parameter)
    target_url = request.args.get('to')

    if target_url:
        # Track the scan
        from brand_qr_generator import track_qr_scan

        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')

        track_qr_scan(slug, target_url, ip_address, user_agent)

        # Redirect to target
        return redirect(target_url)

    else:
        # Generate and return QR code image
        from brand_qr_generator import generate_brand_qr

        qr_bmp = generate_brand_qr(slug)

        if qr_bmp:
            return Response(
                qr_bmp,
                mimetype='image/bmp',
                headers={'Content-Disposition': f'inline; filename={slug}-qr.bmp'}
            )
        else:
            flash(f'❌ Brand not found: {slug}', 'error')
            return redirect(url_for('brands_marketplace'))


@app.route('/qr/brand/<slug>/stats')
def brand_qr_stats(slug):
    """Show QR scan statistics for brand"""
    from brand_qr_generator import get_brand_qr_stats

    stats = get_brand_qr_stats(slug)

    if 'error' in stats:
        flash(f'❌ {stats["error"]}', 'error')
        return redirect(url_for('brands_marketplace'))

    return render_template('brand_qr_stats.html', stats=stats, brand_slug=slug)


@app.route('/shipyard')
def shipyard():
    """Theme browser - Show all themes organized by ship class"""
    import yaml
    import os

    # Load manifest
    manifest_path = os.path.join(os.path.dirname(__file__), 'themes', 'manifest.yaml')
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)

    ship_classes = manifest['ship_classes']
    all_themes = manifest['themes']
    metadata = manifest['metadata']

    # Organize themes by class
    themes_by_class = {
        'dinghy': [],
        'schooner': [],
        'frigate': [],
        'galleon': []
    }

    for theme_slug, theme_data in all_themes.items():
        theme_class = theme_data.get('class', 'dinghy')
        themes_by_class[theme_class].append({
            'slug': theme_slug,
            **theme_data
        })

    return render_template('shipyard.html',
                          ship_classes=ship_classes,
                          themes_by_class=themes_by_class,
                          metadata=metadata)


@app.route('/sitemap')
def sitemap_page():
    """Visual route map - All routes organized by category with health status"""

    # Auto-discover routes from Flask
    from route_discovery import discover_and_categorize_routes

    # Get database connection for example URLs
    conn = get_db()

    # Get template health check data
    from check_templates import check_template_health
    try:
        health = check_template_health()
    except:
        health = None

    # Auto-discover and categorize all routes
    discovered_routes = discover_and_categorize_routes(app, conn, health)

    # Transform to template format
    routes = {}
    for category, route_list in discovered_routes.items():
        routes[category] = []
        for route in route_list:
            routes[category].append({
                'path': route['path'],
                'url': route['example_url'] or '#',
                'name': route['endpoint'].replace('_', ' ').title(),
                'desc': route['description'],
                'clickable': route['clickable'],
                'health': route['health']
            })

    conn.close()

    # Get loaded plugins
    loaded_plugins = getattr(app, 'loaded_plugins', [])

    # Get database stats
    from query_templates import QueryTemplates
    qt = QueryTemplates()
    try:
        db_stats = qt.get_platform_stats(days=30)
    except:
        db_stats = {}

    return render_template('sitemap.html', routes=routes, health=health, plugins=loaded_plugins, db_stats=db_stats)


@app.route('/sitemap/game')
def sitemap_game():
    """
    API Explorer Game - Web Version

    Interactive game-like interface for exploring and testing API routes.
    Like Swagger UI meets Pokemon/Zelda menu system.

    Features:
    - Browse routes by category
    - Test routes via AJAX
    - Achievement tracking (tested routes)
    - Visual progress indicators
    """

    # Same route database as terminal version
    routes = {
        'Content & Posts': [
            {'path': '/', 'method': 'GET', 'desc': 'Homepage - Posts feed with AI predictions'},
            {'path': '/post/<slug>', 'method': 'GET', 'desc': 'Individual post with comments'},
            {'path': '/category/<slug>', 'method': 'GET', 'desc': 'Posts by category'},
            {'path': '/tag/<slug>', 'method': 'GET', 'desc': 'Posts by tag'},
            {'path': '/live', 'method': 'GET', 'desc': 'Real-time comment stream'},
        ],
        'Theme System': [
            {'path': '/shipyard', 'method': 'GET', 'desc': 'Theme browser (Dinghy → Galleon)'},
            {'path': '/brands', 'method': 'GET', 'desc': 'Brand marketplace'},
            {'path': '/brand/<slug>', 'method': 'GET', 'desc': 'Individual brand identity'},
            {'path': '/brand/<slug>/export', 'method': 'GET', 'desc': 'Download brand ZIP package'},
            {'path': '/tiers', 'method': 'GET', 'desc': 'Tier showcase'},
        ],
        'Users & Souls': [
            {'path': '/souls', 'method': 'GET', 'desc': 'All user souls/personas'},
            {'path': '/soul/<username>', 'method': 'GET', 'desc': 'Soul profile'},
            {'path': '/soul/<username>/similar', 'method': 'GET', 'desc': 'Find related users'},
            {'path': '/user/<username>', 'method': 'GET', 'desc': 'User posts and activity'},
            {'path': '/login', 'method': 'GET', 'desc': 'User authentication'},
            {'path': '/signup', 'method': 'GET', 'desc': 'Create account'},
            {'path': '/logout', 'method': 'GET', 'desc': 'End session'},
        ],
        'AI & Machine Learning': [
            {'path': '/train', 'method': 'GET', 'desc': 'Training interface'},
            {'path': '/train/predict', 'method': 'POST', 'desc': 'Get AI prediction'},
            {'path': '/train/feedback', 'method': 'POST', 'desc': 'Submit training feedback'},
            {'path': '/reasoning', 'method': 'GET', 'desc': 'Reasoning dashboard'},
            {'path': '/ml', 'method': 'GET', 'desc': 'ML dashboard'},
            {'path': '/ml/train', 'method': 'POST', 'desc': 'Train model'},
            {'path': '/ml/predict', 'method': 'POST', 'desc': 'Get prediction'},
            {'path': '/dashboard', 'method': 'GET', 'desc': 'Live predictions'},
        ],
        'Showcases & Visual': [
            {'path': '/showcase', 'method': 'GET', 'desc': 'Soul showcase gallery'},
            {'path': '/code', 'method': 'GET', 'desc': 'Browse source code'},
            {'path': '/code/<path>', 'method': 'GET', 'desc': 'View specific file'},
            {'path': '/status', 'method': 'GET', 'desc': 'System health & metrics'},
        ],
        'Admin & Management': [
            {'path': '/admin', 'method': 'GET', 'desc': 'Admin dashboard'},
            {'path': '/admin/login', 'method': 'GET', 'desc': 'Admin authentication'},
            {'path': '/admin/automation', 'method': 'GET', 'desc': 'Scheduled tasks'},
            {'path': '/admin/subscribers', 'method': 'GET', 'desc': 'Newsletter subscribers'},
        ],
        'API Endpoints': [
            {'path': '/api/health', 'method': 'GET', 'desc': 'Server status (JSON)'},
            {'path': '/api/posts', 'method': 'GET', 'desc': 'All posts (JSON)'},
            {'path': '/api/posts/<id>', 'method': 'GET', 'desc': 'Get post with predictions'},
            {'path': '/api/reasoning/threads', 'method': 'GET', 'desc': 'All reasoning threads'},
            {'path': '/api/reasoning/threads/<id>', 'method': 'GET', 'desc': 'Thread with turns'},
            {'path': '/api/feedback', 'method': 'POST', 'desc': 'Submit feedback'},
        ],
        'Utilities': [
            {'path': '/sitemap', 'method': 'GET', 'desc': 'Visual route map'},
            {'path': '/sitemap.xml', 'method': 'GET', 'desc': 'SEO XML sitemap'},
            {'path': '/robots.txt', 'method': 'GET', 'desc': 'Crawler rules'},
            {'path': '/feed.xml', 'method': 'GET', 'desc': 'RSS feed'},
            {'path': '/subscribe', 'method': 'POST', 'desc': 'Newsletter subscription'},
            {'path': '/s/<short_id>', 'method': 'GET', 'desc': 'URL shortener redirect'},
            {'path': '/qr/<qr_id>', 'method': 'GET', 'desc': 'Generate QR code'},
            {'path': '/i/<hash>', 'method': 'GET', 'desc': 'Serve images'},
        ],
    }

    # Count total routes for progress tracking
    total_routes = sum(len(category_routes) for category_routes in routes.values())

    return render_template('sitemap_game.html', routes=routes, total_routes=total_routes)


@app.route('/sitemap.xml')
def sitemap_xml():
    """SEO sitemap - XML format for search engines"""
    from datetime import datetime

    # Get base URL from config
    from config import BASE_URL

    # Define all public routes (exclude admin, API, POST-only routes)
    public_routes = [
        '/',
        '/live',
        '/shipyard',
        '/brands',
        '/tiers',
        '/souls',
        '/showcase',
        '/code',
        '/status',
        '/reasoning',
        '/ml',
        '/dashboard',
        '/train',
        '/about',
        '/feedback',
        '/subscribe',
        '/login',
        '/signup',
        '/sitemap',
        '/feed.xml',
    ]

    # Add dynamic routes from database
    db = get_db()

    # Add all posts
    posts = db.execute('SELECT slug FROM posts').fetchall()
    for post in posts:
        public_routes.append(f"/post/{post['slug']}")

    # Add all brands
    brands = db.execute('SELECT slug FROM brands').fetchall()
    for brand in brands:
        public_routes.append(f"/brand/{brand['slug']}")

    # Add all souls
    users = db.execute('SELECT username FROM users WHERE is_ai_persona = 0').fetchall()
    for user in users:
        public_routes.append(f"/soul/{user['username']}")

    db.close()

    # Generate XML
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for route in public_routes:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{BASE_URL}{route}</loc>')
        xml_lines.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
        xml_lines.append('    <changefreq>daily</changefreq>')
        xml_lines.append('    <priority>0.8</priority>')
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')

    xml_content = '\n'.join(xml_lines)

    return Response(xml_content, mimetype='application/xml')


@app.route('/robots.txt')
def robots_txt():
    """Robots.txt - Crawler instructions"""
    from config import BASE_URL

    robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /train/feedback
Disallow: /ml/train
Disallow: /ml/predict

Sitemap: {BASE_URL}/sitemap.xml
"""

    return Response(robots_content, mimetype='text/plain')


@app.route('/feed.xml')
def rss_feed():
    """Generate RSS feed with AI predictions"""
    from layers import full_pipeline

    # Use full pipeline to get posts with AI predictions
    context = full_pipeline(
        sort='new',
        limit=20,
        networks=app.networks,
        template_name=None,
        render_func=None
    )
    posts = context['posts']

    rss_items = []
    for post in posts:
        author = get_user_by_id(post['user_id'])
        # Escape XML special characters in content
        content_preview = post['content'][:300].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Add AI analysis to description if predictions available
        ai_analysis = ""
        if post.get('predictions'):
            preds = post['predictions']
            ai_analysis = f"""

🧠 AI ANALYSIS:
• CalRiven (Technical): {preds['calriven']['label']} ({int(preds['calriven']['score'] * 100)}%)
• TheAuditor (Validation): {preds['auditor']['label']} ({int(preds['auditor']['score'] * 100)}%)
• DeathToData (Privacy): {preds['deathtodata']['label']} ({int(preds['deathtodata']['score'] * 100)}%)
• Soulfra Judge: {preds['soulfra']['label']} ({int(preds['soulfra']['score'] * 100)}%)
"""
            # Escape for XML
            ai_analysis = ai_analysis.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        rss_items.append(f"""    <item>
      <title>{post['title']}</title>
      <link>http://localhost:5001/post/{post['slug']}</link>
      <description>{content_preview}...{ai_analysis}</description>
      <pubDate>{post['published_at']}</pubDate>
      <author>{author['display_name']}</author>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Soulfra</title>
    <link>http://localhost:5001</link>
    <description>AI, privacy, and the future of technology</description>
    <language>en-us</language>
{chr(10).join(rss_items)}
  </channel>
</rss>"""

    return Response(rss, mimetype='application/rss+xml')


@app.route('/user/<username>')
def user_profile(username):
    """User profile page showing all posts by user"""
    user = get_user_by_username(username)

    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))

    # Get all posts by this user
    posts = get_posts_by_user(user['id'], limit=50)

    # Count comments by user
    conn = get_db()
    comment_count = conn.execute('SELECT COUNT(*) as count FROM comments WHERE user_id = ?', (user['id'],)).fetchone()['count']
    conn.close()

    return render_template('user.html', user=user, posts=posts, post_count=len(posts), comment_count=comment_count)


@app.route('/souls')
def souls_index():
    """Browse all compiled souls"""
    from soul_model import Soul

    conn = get_db()
    users = conn.execute('SELECT id, username, display_name, is_ai_persona FROM users ORDER BY username').fetchall()
    conn.close()

    # Compile soul summaries for all users
    soul_summaries = []
    for user in users:
        try:
            soul = Soul(user['id'])
            interests = soul.extract_interests(top_n=5)
            values = soul.detect_values()
            activity = len(soul.posts) + len(soul.comments)

            soul_summaries.append({
                'user': dict(user),
                'interests': interests,
                'soul_values': values,
                'activity': activity
            })
        except Exception as e:
            print(f"Error compiling soul for {user['username']}: {e}")
            continue

    return render_template('souls.html', souls=soul_summaries)


@app.route('/soul/<username>')
def soul_view(username):
    """View a specific user's soul pack"""
    from soul_model import Soul

    user = get_user_by_username(username)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('souls_index'))

    try:
        soul = Soul(user['id'])
        pack = soul.compile_pack()
        return render_template('soul.html', user=user, pack=pack)
    except Exception as e:
        flash(f'Error compiling soul: {e}', 'error')
        return redirect(url_for('souls_index'))


@app.route('/ownership/<username>')
def ownership_dashboard(username):
    """Show user's ownership across all brands"""
    from ownership_helper import (
        get_user_ownership,
        get_user_total_tokens,
        get_user_contribution_history,
        calculate_user_multiplier
    )

    user = get_user_by_username(username)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))

    try:
        # Get ownership data
        ownership = get_user_ownership(user['id'])
        total_tokens = get_user_total_tokens(user['id'])
        contribution_history = get_user_contribution_history(user['id'], limit=20)
        multiplier = calculate_user_multiplier(user['id'])

        # Calculate stats
        total_brands = len(ownership)
        total_contributions = sum(b['contribution_count'] for b in ownership)

        return render_template('ownership_dashboard.html',
                               user=user,
                               ownership=ownership,
                               total_tokens=total_tokens,
                               total_brands=total_brands,
                               total_contributions=total_contributions,
                               contribution_history=contribution_history,
                               multiplier=multiplier)

    except Exception as e:
        flash(f'Error loading ownership data: {e}', 'error')
        return redirect(url_for('index'))


@app.route('/soul/<username>/similar')
def soul_similar(username):
    """Find souls similar to this user"""
    from soul_model import Soul

    user = get_user_by_username(username)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('souls_index'))

    try:
        soul = Soul(user['id'])

        # Find similar souls
        conn = get_db()
        all_users = conn.execute('SELECT id, username, display_name FROM users WHERE id != ?', (user['id'],)).fetchall()
        conn.close()

        similarities = []
        for other_user in all_users:
            try:
                other_soul = Soul(other_user['id'])
                sim = soul.similarity_to(other_soul)

                if sim > 0:
                    similarities.append({
                        'user': dict(other_user),
                        'similarity': sim,
                        'interests': other_soul.extract_interests(top_n=5),
                        'activity': len(other_soul.posts) + len(other_soul.comments)
                    })
            except Exception as e:
                print(f"Error comparing with {other_user['username']}: {e}")
                continue

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return render_template('soul_similar.html', user=user, soul=soul, similarities=similarities)
    except Exception as e:
        flash(f'Error finding similar souls: {e}', 'error')
        return redirect(url_for('souls_index'))


@app.route('/soul/<username>/platforms')
def soul_platform_picker(username):
    """
    Platform picker for multi-platform Soul identity
    The "Ventrilo entrance" - scan QR → choose platform
    """
    from soul_model import Soul

    user = get_user_by_username(username)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('souls_index'))

    try:
        soul = Soul(user['id'])
        pack = soul.compile_pack()

        # Extract stats for display
        expression = pack.get('expression', {})
        level = 1 + (expression.get('post_count', 0) // 10)

        return render_template('soul_platform_picker.html',
                             username=username,
                             user_id=user['id'],
                             level=level,
                             post_count=expression.get('post_count', 0),
                             karma=expression.get('karma', 100))
    except Exception as e:
        flash(f'Error loading platform picker: {e}', 'error')
        return redirect(url_for('souls_index'))


@app.route('/api/soul/transform')
def api_soul_transform():
    """
    API endpoint to transform Soul Pack to platform-specific format

    Query params:
        user_id (int): User ID to transform
        platform (str): Target platform (roblox, minecraft, unity, voice, web)
        download (bool): If true, return as downloadable file

    Returns:
        JSON response or file download depending on parameters
    """
    from soul_model import Soul
    from platform_connectors import RobloxConnector, MinecraftConnector

    try:
        user_id = int(request.args.get('user_id', 0))
        platform = request.args.get('platform', '').lower()
        should_download = request.args.get('download', 'false').lower() == 'true'

        if not user_id or not platform:
            return jsonify({'error': 'Missing user_id or platform parameter'}), 400

        # Load Soul Pack
        soul = Soul(user_id)
        soul_pack = soul.compile_pack()

        # Get username for filenames
        db = get_db()
        user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        db.close()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        username = user['username']

        # Transform based on platform
        if platform == 'roblox':
            connector = RobloxConnector()
            lua_code = connector.generate(soul_pack)

            if should_download:
                return Response(
                    lua_code,
                    mimetype='text/plain',
                    headers={
                        'Content-Disposition': f'attachment; filename={username}_soul.lua'
                    }
                )
            else:
                return jsonify({
                    'platform': 'roblox',
                    'user_id': user_id,
                    'username': username,
                    'code': lua_code
                })

        elif platform == 'minecraft':
            connector = MinecraftConnector()
            player_data = connector.generate(soul_pack)

            if should_download:
                import json
                return Response(
                    json.dumps(player_data, indent=2),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename={username}_soul.json'
                    }
                )
            else:
                return jsonify({
                    'platform': 'minecraft',
                    'user_id': user_id,
                    'username': username,
                    'data': player_data
                })

        elif platform == 'unity':
            # Use soul_transformer for Unity (not yet a connector)
            from soul_transformer import SoulTransformer
            transformer = SoulTransformer()
            unity_data = transformer.to_unity(soul_pack)

            if should_download:
                import json
                return Response(
                    json.dumps(unity_data, indent=2),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename={username}_soul_unity.json'
                    }
                )
            else:
                return jsonify({
                    'platform': 'unity',
                    'user_id': user_id,
                    'username': username,
                    'data': unity_data
                })

        elif platform == 'voice':
            # Use soul_transformer for Voice/AI
            from soul_transformer import SoulTransformer
            transformer = SoulTransformer()
            persona_data = transformer.to_voice_persona(soul_pack)

            if should_download:
                import json
                return Response(
                    json.dumps(persona_data, indent=2),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename={username}_persona.json'
                    }
                )
            else:
                return jsonify({
                    'platform': 'voice',
                    'user_id': user_id,
                    'username': username,
                    'data': persona_data
                })

        elif platform == 'web':
            # Redirect to existing web profile
            return redirect(url_for('user_homepage', username=username))

        else:
            return jsonify({
                'error': 'Unknown platform',
                'supported': ['roblox', 'minecraft', 'unity', 'voice', 'web']
            }), 400

    except Exception as e:
        print(f"[ERROR] Soul transform failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/s/<short_id>')
def short_url_redirect(short_id):
    """Redirect short URL to soul page (with QR scan tracking)"""
    from datetime import datetime

    db = get_db()

    # Look up username (also increments click counter)
    username = get_username_from_shortcut(short_id)

    if not username:
        flash('Invalid short URL', 'error')
        db.close()
        return redirect(url_for('index'))

    # Check if this short URL has a QR code tracking entry
    short_url = f"https://soulfra.com/s/{short_id}"
    qr_code = db.execute(
        'SELECT id FROM qr_codes WHERE code_data = ?',
        (short_url,)
    ).fetchone()

    # If QR code exists, track the scan
    if qr_code:
        qr_code_id = qr_code['id']

        # Get previous scan for chain tracking
        previous_scan = db.execute('''
            SELECT id FROM qr_scans
            WHERE qr_code_id = ?
            ORDER BY scanned_at DESC
            LIMIT 1
        ''', (qr_code_id,)).fetchone()

        previous_scan_id = previous_scan['id'] if previous_scan else None

        # Record scan with metadata
        db.execute('''
            INSERT INTO qr_scans (
                qr_code_id, scanned_at, ip_address, user_agent,
                referrer, previous_scan_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            qr_code_id,
            datetime.now().isoformat(),
            request.remote_addr,
            request.user_agent.string[:500] if request.user_agent else None,
            request.referrer[:500] if request.referrer else None,
            previous_scan_id
        ))

        db.commit()

    db.close()

    # Redirect to soul page
    return redirect(url_for('soul_view', username=username))


@app.route('/qr/faucet/<path:encoded_payload>')
def qr_faucet_scan(encoded_payload):
    """
    QR Faucet - Transform scanned QR code into game action

    Payload types:
    - plot_action: Perform action on a plot
    - blog: Generate blog post
    - auth: Grant authentication
    """
    from qr_faucet import process_qr_faucet, verify_qr_payload

    # Get device fingerprint
    device_fingerprint = {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'device_type': 'mobile' if 'Mobile' in request.headers.get('User-Agent', '') else 'desktop',
        'referrer': request.referrer
    }

    # Process faucet
    result = process_qr_faucet(encoded_payload, device_fingerprint)

    if not result['success']:
        flash(f"QR code error: {result.get('error', 'Invalid or expired')}", 'error')
        return redirect(url_for('index'))

    payload_type = result['payload_type']
    data = result['result']

    # Handle different payload types
    if payload_type == 'plot_action':
        # Execute plot action
        plot_id = data.get('plot_id')
        action_type = data.get('action_type')

        if not plot_id or not action_type:
            flash('Invalid plot action QR code', 'error')
            return redirect(url_for('index'))

        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please log in to perform actions', 'error')
            return redirect(url_for('login'))

        # Perform action via internal route
        with app.test_client() as client:
            # Copy session to test client
            with client.session_transaction() as sess:
                sess['user_id'] = session['user_id']
                sess['username'] = session.get('username')

            response = client.post(f'/plot/{plot_id}/action',
                                 json={'action_type': action_type},
                                 headers={'Content-Type': 'application/json'})

            if response.status_code == 200:
                action_result = response.get_json()
                flash(f"✅ {action_type.title()} successful! +{action_result['reputation_change']} reputation", 'success')
            else:
                flash(f"Action failed: {response.get_json().get('error', 'Unknown error')}", 'error')

        # Redirect to plot owner's profile
        db = get_db()
        plot = db.execute('SELECT owner_user_id FROM plots WHERE id = ?', (plot_id,)).fetchone()
        if plot:
            owner = db.execute('SELECT username FROM users WHERE id = ?', (plot['owner_user_id'],)).fetchone()
            return redirect(url_for('profile', username=owner['username']))

        return redirect(url_for('rankings'))

    elif payload_type == 'blog':
        # Generate blog post from QR
        flash('Blog post generation from QR coming soon!', 'info')
        return redirect(url_for('index'))

    elif payload_type == 'auth':
        # Authentication token - create or login user
        db = get_db()

        # Get or create user based on device fingerprint
        device_fp_hash = hashlib.sha256(
            json.dumps(device_fingerprint, sort_keys=True).encode()
        ).hexdigest()

        # Check if user exists for this device
        user = db.execute('''
            SELECT id, username FROM users
            WHERE password_hash = ?
            LIMIT 1
        ''', (f'qr_auth_{device_fp_hash}',)).fetchone()

        if not user:
            # Create new user from QR auth
            import secrets
            username = f"user_{secrets.token_hex(4)}"
            email = f"{username}@qr.local"

            db.execute('''
                INSERT INTO users (username, email, password_hash, display_name)
                VALUES (?, ?, ?, ?)
            ''', (username, email, f'qr_auth_{device_fp_hash}', f'User {username[-4:]}'))
            db.commit()

            user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            username_final = username

            flash(f'Welcome! Account created: {username_final}', 'success')
        else:
            user_id = user['id']
            username_final = user['username']

            flash(f'Welcome back, {username_final}!', 'success')

        # Log user in
        session['user_id'] = user_id
        session['username'] = username_final

        # Redirect to hub (master dashboard)
        return redirect(url_for('hub'))

    elif payload_type == 'idea_submission':
        # Redirect to idea submission form with pre-filled theme/domain
        redirect_url = data.get('redirect_url', '/submit-idea')
        return redirect(redirect_url)

    elif payload_type == 'question_response':
        # Show question response form
        plot_id = data.get('plot_id')

        if not plot_id:
            flash('Invalid question QR code', 'error')
            return redirect(url_for('index'))

        # Get plot info
        db = get_db()
        plot = db.execute('SELECT * FROM plots WHERE id = ?', (plot_id,)).fetchone()

        if not plot:
            flash('Plot not found', 'error')
            return redirect(url_for('index'))

        # Get rotation context
        from rotation_helpers import inject_rotation_context
        rotation_ctx = inject_rotation_context(g.get('active_brand'))

        # Render question form
        return render_template('qr_question/v1_dinghy.html',
                             plot_id=plot_id,
                             plot_name=plot['town_name'],
                             **rotation_ctx)

    elif payload_type == 'referral':
        # Handle referral signup
        referral_code = data.get('referral_code')
        referrer_username = data.get('referrer_username')

        if not referral_code:
            flash('Invalid referral code', 'error')
            return redirect(url_for('index'))

        # Store referral code in session for signup
        session['referral_code'] = referral_code
        session['referrer_username'] = referrer_username

        flash(f'🎉 Join via {referrer_username}\'s referral and get +25 welcome bonus!', 'success')
        return redirect(url_for('onboard'))

    else:
        flash(f'Unknown QR faucet type: {payload_type}', 'warning')
        return redirect(url_for('index'))


@app.route('/qr/question/submit', methods=['POST'])
def qr_question_submit():
    """
    Submit response to QR question (text or voice)

    Creates plot_activity with the response and awards reputation points
    """
    plot_id = request.form.get('plot_id')
    question = request.form.get('question')
    response_text = request.form.get('response_text', '').strip()
    audio_data = request.form.get('audio_data', '')

    if not plot_id:
        flash('Missing plot ID', 'error')
        return redirect(url_for('index'))

    db = get_db()

    # Get plot
    plot = db.execute('SELECT * FROM plots WHERE id = ?', (plot_id,)).fetchone()
    if not plot:
        flash('Plot not found', 'error')
        return redirect(url_for('index'))

    # Store voice input if provided
    voice_id = None
    if audio_data:
        from voice_input import add_audio
        import tempfile
        import base64

        # Decode base64 audio
        try:
            # Extract actual base64 data (skip data:audio/webm;base64, prefix)
            if ',' in audio_data:
                audio_data = audio_data.split(',')[1]

            audio_bytes = base64.b64decode(audio_data)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # Add to voice_input system
            voice_id = add_audio(tmp_path, source='qr_question', metadata={
                'plot_id': plot_id,
                'question': question
            })

            # If there's also text, use it as transcription
            if response_text:
                from voice_input import transcribe_audio
                transcribe_audio(voice_id, response_text, method='user_provided')

        except Exception as e:
            print(f"Error saving voice input: {e}")
            flash('Voice recording saved as audio only', 'info')

    # Create activity
    description = response_text or f"Responded to: {question}"
    reputation_change = 10  # Base points for answering

    if audio_data and response_text:
        reputation_change = 15  # Bonus for voice + text

    db.execute('''
        INSERT INTO plot_activities (plot_id, activity_type, description, reputation_change, metadata)
        VALUES (?, 'answer', ?, ?, ?)
    ''', (
        plot_id,
        description,
        reputation_change,
        json.dumps({'question': question, 'voice_id': voice_id})
    ))

    # Update plot reputation
    db.execute('''
        UPDATE plots
        SET reputation_points = reputation_points + ?,
            last_active_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (reputation_change, plot_id))

    db.commit()

    flash(f'✅ Response recorded! +{reputation_change} reputation points', 'success')

    # Redirect to profile
    owner = db.execute('SELECT username FROM users WHERE id = ?', (plot['owner_user_id'],)).fetchone()
    if owner:
        return redirect(url_for('profile', username=owner['username']))

    return redirect(url_for('rankings'))


@app.route('/qr/<qr_id>')
def qr_scan(qr_id):
    """
    QR Code Time Capsule - Track scan and show chain

    When someone scans a QR code:
    1. Record who/when/where
    2. Link to previous scan (chain)
    3. Show scan history
    4. Redirect to target
    """
    db = get_db()

    # Get QR code
    qr_code = db.execute('SELECT * FROM qr_codes WHERE id = ?', (qr_id,)).fetchone()

    if not qr_code:
        flash('Invalid QR code', 'error')
        db.close()
        return redirect(url_for('index'))

    # Get previous scan (for chain)
    previous_scan = db.execute('''
        SELECT id, scanned_by_name, location_city, scanned_at
        FROM qr_scans
        WHERE qr_code_id = ?
        ORDER BY scanned_at DESC
        LIMIT 1
    ''', (qr_id,)).fetchone()

    # Record this scan
    db.execute('''
        INSERT INTO qr_scans (
            qr_code_id, scanned_at, ip_address, user_agent,
            referrer, previous_scan_id
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        qr_id,
        datetime.now().isoformat(),
        request.remote_addr,
        request.headers.get('User-Agent'),
        request.referrer,
        previous_scan['id'] if previous_scan else None
    ))

    # Update QR code stats
    db.execute('''
        UPDATE qr_codes
        SET total_scans = total_scans + 1,
            last_scanned_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), qr_id))

    db.commit()
    db.close()

    # Show scan info if it's a soul QR
    if previous_scan:
        time_ago = (datetime.now() - datetime.fromisoformat(previous_scan['scanned_at'])).total_seconds() / 3600
        location = previous_scan['location_city'] or 'Unknown'
        flash(f'🔗 Last scanned by {previous_scan["scanned_by_name"] or "someone"} in {location}, {int(time_ago)} hours ago', 'info')
    else:
        flash('🎉 You\'re the first to scan this QR code!', 'success')

    # Redirect to target
    return redirect(qr_code['target_url'])


@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Subscribe to newsletter"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email or '@' not in email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('subscribe'))

        if add_subscriber(email):
            flash('Successfully subscribed! Welcome to Soulfra.', 'success')
        else:
            flash('This email is already subscribed.', 'info')

        return redirect(url_for('index'))

    return render_template('subscribe.html')


@app.route('/unsubscribe')
def unsubscribe():
    """Unsubscribe page (required by law)"""
    email = request.args.get('email', '')

    if request.args.get('confirm') == 'yes' and email:
        from database import unsubscribe as unsubscribe_email
        unsubscribe_email(email)
        flash('You have been unsubscribed. Sorry to see you go!', 'info')
        return redirect(url_for('index'))

    return render_template('unsubscribe.html', email=email)


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/@docs/<path:filename>')
def serve_markdown_doc(filename):
    """
    Serve markdown documentation files as rendered HTML

    Examples:
        /@docs/HOW_IT_ALL_CONNECTS
        /@docs/WHITEPAPER
        /@docs/BLOG_GENERATOR_GUIDE
    """
    # Add .md extension if not present
    if not filename.endswith('.md'):
        filename = filename + '.md'

    # Build file path (look in project root)
    file_path = Path(__file__).parent / filename

    # Check if file exists
    if not file_path.exists():
        flash(f'Documentation file not found: {filename}', 'error')
        return redirect(url_for('about'))

    # Read markdown content
    try:
        content = file_path.read_text()
    except Exception as e:
        flash(f'Error reading file: {e}', 'error')
        return redirect(url_for('about'))

    # Convert markdown to HTML
    html_content = markdown2_markdown(content, extras=['fenced-code-blocks', 'tables', 'header-ids'])

    # Get title from first # header or filename
    title = filename.replace('.md', '').replace('_', ' ').replace('-', ' ')
    for line in content.split('\n'):
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break

    # Render in simple template
    return render_template('markdown_doc.html',
                         title=title,
                         content=html_content,
                         filename=filename)


# ==================== GAME ONBOARDING ROUTES ====================

@app.route('/onboard', methods=['GET', 'POST'])
def onboard():
    """
    Game onboarding flow - multi-step quiz with rotation contexts
    Creates user account + plot in one flow
    """
    from flask import g
    from rotation_helpers import get_domain_slug_from_brand
    import secrets

    # Check if this is a game brand
    brand = g.get('active_brand', None)
    if not brand or brand.get('brand_type') != 'game':
        # Not a game, redirect to regular signup
        return redirect(url_for('signup'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        town_name = request.form.get('town_name', '').strip()
        plot_type = request.form.get('plot_type', 'town')

        # Validation
        if not username or not email or not password or not town_name:
            flash('All fields are required', 'error')
            return redirect(url_for('onboard'))

        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('onboard'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('onboard'))

        # Create user account
        user = create_user(username, email, password)

        if not user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('onboard'))

        # Generate QR code for plot
        qr_code = f"{brand['slug']}-{username}-{secrets.token_hex(4)}"

        # Create plot
        db = get_db()
        domain_slug = get_domain_slug_from_brand(brand)

        db.execute('''
            INSERT INTO plots (owner_user_id, town_name, qr_code, brand_slug, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['id'], town_name, qr_code, domain_slug, json.dumps({'plot_type': plot_type})))

        db.commit()

        # Auto-login
        session['user_id'] = user['id']
        session['username'] = user['username']

        flash(f'Welcome to {brand["name"]}, {username}! Your plot "{town_name}" is ready!', 'success')
        return redirect(url_for('profile', username=username))

    # GET: Show onboarding form
    return render_template('onboarding/v1_dinghy.html')


@app.route('/rankings')
def rankings():
    """Leaderboard - top players by reputation"""
    from flask import g
    from rotation_helpers import inject_rotation_context

    brand = g.get('active_brand', None)
    if not brand or brand.get('brand_type') != 'game':
        flash('Rankings are only available for games', 'error')
        return redirect(url_for('index'))

    db = get_db()

    # Get top plots by reputation
    players = db.execute('''
        SELECT u.username, p.town_name, p.reputation_points, p.qr_code
        FROM plots p
        JOIN users u ON p.owner_user_id = u.id
        WHERE p.brand_slug = ?
        ORDER BY p.reputation_points DESC
        LIMIT 50
    ''', (brand['slug'],)).fetchall()

    # Get current active season
    current_season = db.execute('''
        SELECT * FROM game_seasons
        WHERE brand_slug = ? AND status = 'active'
        ORDER BY start_date DESC
        LIMIT 1
    ''', (brand['slug'],)).fetchone()

    # Get past completed seasons
    past_seasons = db.execute('''
        SELECT * FROM game_seasons
        WHERE brand_slug = ? AND status = 'completed'
        ORDER BY season_number DESC
        LIMIT 5
    ''', (brand['slug'],)).fetchall()

    rotation_ctx = inject_rotation_context(brand)
    return render_template('leaderboard/v1_dinghy.html',
                         players=[dict(row) for row in players],
                         current_season=dict(current_season) if current_season else None,
                         past_seasons=[dict(row) for row in past_seasons],
                         **rotation_ctx)


@app.route('/news')
def news():
    """Game news and announcements"""
    from flask import g

    brand = g.get('active_brand', None)
    if not brand or brand.get('brand_type') != 'game':
        return redirect(url_for('index'))

    db = get_db()

    # Get news posts for this game (posts tagged with brand)
    posts = db.execute('''
        SELECT * FROM posts
        WHERE brand_id = ?
        ORDER BY published_at DESC
        LIMIT 20
    ''', (brand['id'],)).fetchall()

    return render_template('news_feed/v1_dinghy.html', posts=[dict(row) for row in posts])


@app.route('/profile/<username>')
def profile(username):
    """Player profile with plot info and QR code"""
    db = get_db()

    # Get user
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))

    # Get user's plots
    plots = db.execute('''
        SELECT * FROM plots WHERE owner_user_id = ?
        ORDER BY reputation_points DESC
    ''', (user['id'],)).fetchall()

    # Parse plot metadata (JSON)
    plots_parsed = []
    for p in plots:
        plot_dict = dict(p)
        if plot_dict.get('metadata'):
            try:
                plot_dict['metadata'] = json.loads(plot_dict['metadata'])
            except:
                plot_dict['metadata'] = {}
        else:
            plot_dict['metadata'] = {}
        plots_parsed.append(plot_dict)

    # Get recent activities
    if plots:
        activities = db.execute('''
            SELECT pa.*, p.town_name
            FROM plot_activities pa
            JOIN plots p ON pa.plot_id = p.id
            WHERE p.owner_user_id = ?
            ORDER BY pa.created_at DESC
            LIMIT 10
        ''', (user['id'],)).fetchall()
    else:
        activities = []

    # Generate referral QR code for first plot
    referral_qr = None
    if plots_parsed:
        from qr_faucet import generate_qr_payload
        import secrets

        # Check if referral code exists
        referral_code = db.execute('''
            SELECT referral_code FROM referrals
            WHERE referrer_user_id = ?
            LIMIT 1
        ''', (user['id'],)).fetchone()

        if not referral_code:
            # Create new referral code
            code = f"ref-{secrets.token_urlsafe(8)}"
            db.execute('''
                INSERT INTO referrals (referrer_user_id, referral_code)
                VALUES (?, ?)
            ''', (user['id'], code))
            db.commit()
            referral_code = code
        else:
            referral_code = referral_code['referral_code']

        # Generate QR payload
        referral_payload = generate_qr_payload(
            'referral',
            {'referral_code': referral_code, 'username': user['username']},
            ttl_seconds=31536000  # 1 year
        )

        # Create full URL
        referral_qr = f"{BASE_URL}/qr/faucet/{referral_payload}"

    return render_template('profile/v1_dinghy.html',
                         user=dict(user),
                         plots=plots_parsed,
                         activities=[dict(a) for a in activities],
                         referral_qr=referral_qr)


@app.route('/plot/<int:plot_id>/action', methods=['POST'])
def plot_action(plot_id):
    """
    Perform action on a plot (build, defend, visit, trade)

    Request JSON:
    {
        "action_type": "build" | "defend" | "visit" | "trade",
        "description": "Built a watchtower" (optional)
    }

    Returns:
    {
        "success": true,
        "reputation_change": +20,
        "new_reputation": 120,
        "activity_id": 42
    }
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    db = get_db()

    # Get plot
    plot = db.execute('SELECT * FROM plots WHERE id = ?', (plot_id,)).fetchone()
    if not plot:
        return jsonify({'success': False, 'error': 'Plot not found'}), 404

    # Get request data
    data = request.get_json() or {}
    action_type = data.get('action_type', '').lower()
    description = data.get('description', '')

    # Validate action type
    valid_actions = ['build', 'defend', 'visit', 'trade']
    if action_type not in valid_actions:
        return jsonify({'success': False, 'error': f'Invalid action. Must be one of: {", ".join(valid_actions)}'}), 400

    # Calculate reputation change based on action type
    reputation_changes = {
        'build': 20,      # Building adds value
        'defend': 15,     # Defending protects
        'visit': 5,       # Visiting is social
        'trade': 10       # Trading is collaborative
    }
    reputation_change = reputation_changes.get(action_type, 0)

    # Check if user owns this plot (owners get full points, visitors get half)
    is_owner = plot['owner_user_id'] == session['user_id']
    if not is_owner and action_type != 'visit':
        reputation_change = reputation_change // 2

    # Auto-generate description if not provided
    if not description:
        descriptions = {
            'build': f"Built something in {plot['town_name']}",
            'defend': f"Defended {plot['town_name']} from threats",
            'visit': f"Visited {plot['town_name']}",
            'trade': f"Traded resources with {plot['town_name']}"
        }
        description = descriptions.get(action_type, f"Performed {action_type} action")

    # Create activity
    cursor = db.execute('''
        INSERT INTO plot_activities (plot_id, activity_type, description, reputation_change)
        VALUES (?, ?, ?, ?)
    ''', (plot_id, action_type, description, reputation_change))

    activity_id = cursor.lastrowid

    # Update plot reputation
    db.execute('''
        UPDATE plots
        SET reputation_points = reputation_points + ?,
            last_active_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (reputation_change, plot_id))

    db.commit()

    # Get new reputation
    new_rep = db.execute('SELECT reputation_points FROM plots WHERE id = ?', (plot_id,)).fetchone()

    return jsonify({
        'success': True,
        'reputation_change': reputation_change,
        'new_reputation': new_rep['reputation_points'],
        'activity_id': activity_id,
        'action_type': action_type,
        'description': description
    })


@app.route('/api/plot/react', methods=['POST'])
def plot_react():
    """
    Add/remove emoji reaction to a plot

    Request JSON:
    {
        "plot_id": 123,
        "emoji": "🔥"
    }

    Returns:
    {
        "success": true,
        "user_reacted": true,  // true if added, false if removed
        "total_count": 5  // total reactions for this emoji
    }
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json() or {}
    plot_id = data.get('plot_id')
    emoji = data.get('emoji')

    # Validate
    valid_emojis = ['🔥', '💯', '😂', '👀', '❤️', '⭐', '🎯', '👏']
    if not plot_id or not emoji:
        return jsonify({'success': False, 'error': 'Missing plot_id or emoji'}), 400
    if emoji not in valid_emojis:
        return jsonify({'success': False, 'error': 'Invalid emoji'}), 400

    db = get_db()

    # Check if plot exists
    plot = db.execute('SELECT * FROM plots WHERE id = ?', (plot_id,)).fetchone()
    if not plot:
        return jsonify({'success': False, 'error': 'Plot not found'}), 404

    user_id = session['user_id']

    # Check if user already reacted with this emoji
    existing = db.execute('''
        SELECT * FROM plot_reactions
        WHERE plot_id = ? AND user_id = ? AND emoji = ?
    ''', (plot_id, user_id, emoji)).fetchone()

    if existing:
        # Remove reaction (toggle off)
        db.execute('''
            DELETE FROM plot_reactions
            WHERE plot_id = ? AND user_id = ? AND emoji = ?
        ''', (plot_id, user_id, emoji))
        user_reacted = False
    else:
        # Add reaction
        db.execute('''
            INSERT INTO plot_reactions (plot_id, user_id, emoji)
            VALUES (?, ?, ?)
        ''', (plot_id, user_id, emoji))
        user_reacted = True

        # Award +1 reputation to plot owner for getting a reaction
        db.execute('''
            UPDATE plots
            SET reputation_points = reputation_points + 1
            WHERE id = ?
        ''', (plot_id,))

    db.commit()

    # Get total count for this emoji
    total = db.execute('''
        SELECT COUNT(*) as count FROM plot_reactions
        WHERE plot_id = ? AND emoji = ?
    ''', (plot_id, emoji)).fetchone()

    return jsonify({
        'success': True,
        'user_reacted': user_reacted,
        'total_count': total['count']
    })


@app.route('/api/plot/reactions')
def get_plot_reactions():
    """
    Get all reactions for a plot

    Query params:
    - plot_id: ID of plot

    Returns:
    {
        "success": true,
        "reactions": {"🔥": 5, "💯": 3, ...},
        "user_reactions": ["🔥", "⭐"]  // emojis the current user has used
    }
    """
    plot_id = request.args.get('plot_id')
    if not plot_id:
        return jsonify({'success': False, 'error': 'Missing plot_id'}), 400

    db = get_db()

    # Get all reactions for this plot grouped by emoji
    reactions_data = db.execute('''
        SELECT emoji, COUNT(*) as count
        FROM plot_reactions
        WHERE plot_id = ?
        GROUP BY emoji
    ''', (plot_id,)).fetchall()

    reactions = {row['emoji']: row['count'] for row in reactions_data}

    # Get current user's reactions if logged in
    user_reactions = []
    if 'user_id' in session:
        user_reactions_data = db.execute('''
            SELECT emoji FROM plot_reactions
            WHERE plot_id = ? AND user_id = ?
        ''', (plot_id, session['user_id'])).fetchall()
        user_reactions = [row['emoji'] for row in user_reactions_data]

    return jsonify({
        'success': True,
        'reactions': reactions,
        'user_reactions': user_reactions
    })


# ==================== COLOR CHALLENGE ROUTES ====================

@app.route('/challenge/daily')
def daily_challenge():
    """Display today's color challenge"""
    from rotation_helpers import inject_rotation_context
    from datetime import date
    import json

    brand = g.get('active_brand', None)
    if not brand:
        return "Color challenges are only available for game brands", 404

    db = get_db()
    today = date.today().isoformat()

    # Get or create today's challenge
    challenge = db.execute('''
        SELECT * FROM color_challenges
        WHERE brand_slug = ? AND challenge_date = ?
    ''', (brand['slug'], today)).fetchone()

    # If no challenge exists, create one
    if not challenge:
        from train_color_features import extract_color_features
        import random

        # Generate random target color with specific mood
        moods = [
            ('energetic', [1.0, 0.3, 0.0]),  # Orange - high energy
            ('calm', [0.4, 0.6, 0.9]),        # Light blue - peaceful
            ('mysterious', [0.3, 0.0, 0.5]),  # Purple - enigmatic
            ('natural', [0.2, 0.7, 0.3]),     # Green - earthy
            ('passionate', [0.9, 0.1, 0.2]),  # Red - intense
            ('cheerful', [1.0, 0.9, 0.2]),    # Yellow - happy
            ('sophisticated', [0.2, 0.2, 0.3])  # Dark gray-blue - elegant
        ]

        mood, base_rgb = random.choice(moods)
        target_features = extract_color_features(base_rgb)

        descriptions = {
            'energetic': 'Pick a color that radiates energy and movement!',
            'calm': 'Choose a color that feels peaceful and serene.',
            'mysterious': 'Select a color that evokes mystery and intrigue.',
            'natural': 'Find a color that feels organic and earthy.',
            'passionate': 'Pick a color full of emotion and intensity.',
            'cheerful': 'Choose a color that makes you smile!',
            'sophisticated': 'Select a color that feels refined and elegant.'
        }

        db.execute('''
            INSERT INTO color_challenges (challenge_date, target_mood, target_features, description, brand_slug)
            VALUES (?, ?, ?, ?, ?)
        ''', (today, mood, json.dumps(target_features), descriptions[mood], brand['slug']))
        db.commit()

        # Fetch the newly created challenge
        challenge = db.execute('''
            SELECT * FROM color_challenges
            WHERE brand_slug = ? AND challenge_date = ?
        ''', (brand['slug'], today)).fetchone()

    # Check if user already submitted
    submission = None
    already_submitted = False
    if 'user_id' in session:
        submission = db.execute('''
            SELECT * FROM challenge_submissions
            WHERE challenge_id = ? AND user_id = ?
        ''', (challenge['id'], session['user_id'])).fetchone()
        already_submitted = submission is not None

    rotation_ctx = inject_rotation_context(brand)
    return render_template('challenge/daily_v1_dinghy.html',
                         challenge=challenge,
                         submission=submission,
                         already_submitted=already_submitted,
                         **rotation_ctx)


@app.route('/api/challenge/submit', methods=['POST'])
def submit_challenge():
    """Submit a color for today's challenge and get neural network score"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    from train_color_features import extract_color_features
    from datetime import date
    import json
    import math

    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    color_hex = data.get('color', '').strip()

    if not challenge_id or not color_hex:
        return jsonify({'success': False, 'error': 'Missing challenge_id or color'}), 400

    # Parse hex color to RGB
    try:
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        r = int(color_hex[0:2], 16) / 255.0
        g = int(color_hex[2:4], 16) / 255.0
        b = int(color_hex[4:6], 16) / 255.0
        submitted_rgb = [r, g, b]
    except:
        return jsonify({'success': False, 'error': 'Invalid color format'}), 400

    db = get_db()

    # Get challenge
    challenge = db.execute('SELECT * FROM color_challenges WHERE id = ?', (challenge_id,)).fetchone()
    if not challenge:
        return jsonify({'success': False, 'error': 'Challenge not found'}), 404

    # Check if user already submitted
    existing = db.execute('''
        SELECT * FROM challenge_submissions
        WHERE challenge_id = ? AND user_id = ?
    ''', (challenge_id, session['user_id'])).fetchone()

    if existing:
        return jsonify({'success': False, 'error': 'Already submitted today'}), 400

    # Extract features from submitted color
    submitted_features = extract_color_features(submitted_rgb)
    target_features = json.loads(challenge['target_features'])

    # Analyze submitted color personality using neural network
    from brand_neural_analysis import fallback_color_analysis
    try:
        # Create fake brand object with submitted color
        color_brand = {'colors_list': ['#' + color_hex]}
        personality_analysis = fallback_color_analysis(color_brand['colors_list'])

        # Get personality traits
        personality = personality_analysis.get('personality', 'Unknown')
        energy = personality_analysis.get('energy', 'Unknown')
        warmth = personality_analysis.get('warmth', 'Unknown')
    except Exception as e:
        print(f"Personality analysis failed: {e}")
        personality = "Unknown"
        energy = "Unknown"
        warmth = "Unknown"

    # Calculate similarity using Euclidean distance
    # Distance ranges from 0 (perfect match) to ~4.0 (very different)
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(submitted_features, target_features)))

    # Convert to 0-100 similarity score
    # Distance 0 = 100%, distance 2.0 = 0%
    similarity_score = max(0, 100 - (distance * 50))

    # Award reputation based on score
    # Perfect 100% = 10 pts, 50% = 5 pts, 0% = 0 pts
    reputation_earned = int(similarity_score / 10)

    # Bonus points for personality match to target mood
    mood_personality_map = {
        'energetic': 'Energetic',
        'calm': 'Calm',
        'mysterious': 'thoughtful',
        'natural': 'Natural',
        'passionate': 'bold',
        'cheerful': 'friendly',
        'sophisticated': 'thoughtful'
    }

    target_mood = challenge['target_mood']
    expected_trait = mood_personality_map.get(target_mood, '')
    if expected_trait.lower() in personality.lower():
        reputation_earned += 2  # Bonus for personality match!

    # Generate feedback
    if similarity_score >= 90:
        feedback = "🎯 Incredible! You nailed the vibe!"
    elif similarity_score >= 75:
        feedback = "🌟 Great eye for color! Very close."
    elif similarity_score >= 60:
        feedback = "👍 Good intuition, getting there!"
    elif similarity_score >= 40:
        feedback = "🤔 Interesting choice, but a bit off target."
    else:
        feedback = "🎨 Keep experimenting! Try again tomorrow."

    # Get user's plot for this brand (if they have one)
    plot = db.execute('''
        SELECT id FROM plots
        WHERE user_id = ? AND brand_slug = ?
        LIMIT 1
    ''', (session['user_id'], challenge['brand_slug'])).fetchone()

    plot_id = plot['id'] if plot else None

    # Save submission
    db.execute('''
        INSERT INTO challenge_submissions
        (challenge_id, user_id, plot_id, submitted_color, submitted_features, similarity_score, reputation_earned)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (challenge_id, session['user_id'], plot_id, '#' + color_hex,
          json.dumps(submitted_features), similarity_score, reputation_earned))

    # Award reputation to plot if exists
    if plot_id:
        db.execute('UPDATE plots SET reputation_points = reputation_points + ? WHERE id = ?',
                  (reputation_earned, plot_id))

    db.commit()

    # Generate visual assets from submitted color
    try:
        from visual_generator import generate_complete_brand_kit
        import base64

        username = session.get('username', 'player')
        brand_kit = generate_complete_brand_kit('#' + color_hex, username)

        # Encode images as base64 for JSON response
        avatar_b64 = base64.b64encode(brand_kit['avatar']).decode('utf-8')
        favicon_b64 = base64.b64encode(brand_kit['favicon']).decode('utf-8')
        palette_b64 = base64.b64encode(brand_kit['palette_card']).decode('utf-8')

        visuals = {
            'avatar': f'data:image/png;base64,{avatar_b64}',
            'favicon': f'data:image/png;base64,{favicon_b64}',
            'logo_svg': brand_kit['logo_svg'],
            'palette': f'data:image/png;base64,{palette_b64}',
            'colors': brand_kit['colors']
        }
    except Exception as e:
        print(f"Visual generation failed: {e}")
        visuals = None

    return jsonify({
        'success': True,
        'similarity_score': round(similarity_score, 1),
        'reputation_earned': reputation_earned,
        'feedback': feedback,
        'personality': personality,
        'energy': energy,
        'warmth': warmth,
        'personality_insight': f"Your color feels: {personality} ({energy} energy, {warmth})",
        'visuals': visuals  # Brand kit assets
    })


# ========================================
# FEED ROUTES - RSS/Atom/JSON Feeds
# ========================================

@app.route('/feeds/challenges.xml')
def challenges_rss_feed():
    """RSS feed for daily color challenges"""
    from feed_generator import generate_rss_feed, generate_challenge_rss_items
    from config import BASE_URL

    db = get_db()

    # Get recent challenges (last 30 days)
    challenges = db.execute('''
        SELECT * FROM color_challenges
        ORDER BY challenge_date DESC
        LIMIT 30
    ''').fetchall()

    # Convert to dicts
    challenge_dicts = [dict(c) for c in challenges]

    # Generate RSS items
    items = generate_challenge_rss_items(challenge_dicts, BASE_URL)

    # Generate feed
    rss_xml = generate_rss_feed(
        items=items,
        title='Soulfra Daily Color Challenges',
        description='Test your color intuition with daily neural network challenges. Pick colors that match moods and earn reputation!',
        link=f'{BASE_URL}/feeds/challenges.xml',
        language='en-us',
        image_url=f'{BASE_URL}/static/img/logo.png' if os.path.exists('static/img/logo.png') else None
    )

    return Response(rss_xml, mimetype='application/rss+xml')


@app.route('/feeds/challenges.json')
def challenges_json_feed():
    """JSON Feed for daily color challenges"""
    from feed_generator import generate_json_feed
    from config import BASE_URL

    db = get_db()

    # Get recent challenges (last 30 days)
    challenges = db.execute('''
        SELECT * FROM color_challenges
        ORDER BY challenge_date DESC
        LIMIT 30
    ''').fetchall()

    # Convert to JSON Feed items
    items = []
    for challenge in challenges:
        items.append({
            'id': f"{BASE_URL}/challenge/{challenge['id']}",
            'url': f"{BASE_URL}/challenge/{challenge['id']}",
            'title': f"Daily Color Challenge: {challenge['target_mood'].title()}",
            'content_html': f"<p>{challenge['description']}</p><p>Pick a color that matches the <strong>{challenge['target_mood']}</strong> mood and let the neural network score your intuition!</p>",
            'date_published': challenge['challenge_date'] or challenge['created_at'],
            'summary': challenge['description'],
            'tags': ['color', 'challenge', 'personality', challenge['target_mood']]
        })

    # Generate JSON Feed
    json_feed = generate_json_feed(
        items=items,
        title='Soulfra Daily Color Challenges',
        home_page_url=BASE_URL,
        feed_url=f'{BASE_URL}/feeds/challenges.json',
        description='Daily color challenges for neural personality testing',
        author_name='Soulfra'
    )

    return Response(json_feed, mimetype='application/json')


@app.route('/feeds/catchphrases.xml')
def catchphrases_rss_feed():
    """RSS feed for CalRiven catchphrase testing (coming soon)"""
    from feed_generator import generate_rss_feed
    from config import BASE_URL

    # TODO: Implement catchphrase table and fetching
    # For now, return empty feed with placeholder

    items = [{
        'title': 'CalRiven Catchphrase Testing - Coming Soon!',
        'link': f'{BASE_URL}/catchphrase',
        'description': 'Vote on CalRiven\'s new catchphrases and help shape brand personality. System launching soon!',
        'pub_date': datetime.now(),
        'guid': f'{BASE_URL}/catchphrase/preview',
        'category': 'Catchphrase Test',
        'author': 'CalRiven'
    }]

    rss_xml = generate_rss_feed(
        items=items,
        title='CalRiven Catchphrase Tests',
        description='Vote on catchphrases and help CalRiven build authentic brand personality',
        link=f'{BASE_URL}/feeds/catchphrases.xml',
        language='en-us'
    )

    return Response(rss_xml, mimetype='application/rss+xml')


# ========================================
# CATCHPHRASE TESTING ROUTES
# ========================================

@app.route('/catchphrase/test', methods=['GET', 'POST'])
def catchphrase_test():
    """Test catchphrases and provide reactions"""
    from rotation_helpers import inject_rotation_context
    import random

    db = get_db()

    if request.method == 'POST':
        # Record reaction
        catchphrase_id = request.form.get('catchphrase_id')
        reaction_type = request.form.get('reaction_type')
        reaction_emoji = request.form.get('reaction_emoji')

        if catchphrase_id and reaction_type:
            user_id = session.get('user_id')

            # Get user's plot for this brand (if they have one)
            plot_id = None
            if user_id:
                plot = db.execute('''
                    SELECT id FROM plots
                    WHERE user_id = ? AND brand_slug = ?
                    LIMIT 1
                ''', (user_id, g.get('domain_slug', 'soulfra'))).fetchone()
                plot_id = plot['id'] if plot else None

            # Insert reaction
            db.execute('''
                INSERT INTO catchphrase_reactions
                (catchphrase_id, user_id, plot_id, reaction_type, reaction_emoji)
                VALUES (?, ?, ?, ?, ?)
            ''', (catchphrase_id, user_id, plot_id, reaction_type, reaction_emoji))
            db.commit()

            # Redirect to show success
            return redirect(url_for('catchphrase_test', submitted=1))

    # Get random active catchphrase
    catchphrases = db.execute('''
        SELECT * FROM catchphrases
        WHERE is_active = 1 AND brand_slug = ?
    ''', (g.get('domain_slug', 'calriven'),)).fetchall()

    catchphrase = random.choice(catchphrases) if catchphrases else None

    # Get stats for this catchphrase
    stats = None
    if catchphrase:
        reactions = db.execute('''
            SELECT reaction_type, COUNT(*) as count
            FROM catchphrase_reactions
            WHERE catchphrase_id = ?
            GROUP BY reaction_type
        ''', (catchphrase['id'],)).fetchall()

        total = sum(r['count'] for r in reactions)
        if total > 0:
            stats = {
                'total': total,
                'love': round(next((r['count'] for r in reactions if r['reaction_type'] == 'love'), 0) / total * 100),
                'like': round(next((r['count'] for r in reactions if r['reaction_type'] == 'like'), 0) / total * 100),
                'meh': round(next((r['count'] for r in reactions if r['reaction_type'] == 'meh'), 0) / total * 100),
                'dislike': round(next((r['count'] for r in reactions if r['reaction_type'] == 'dislike'), 0) / total * 100),
                'cringe': round(next((r['count'] for r in reactions if r['reaction_type'] == 'cringe'), 0) / total * 100)
            }

    # Inject rotation context for theming
    context = inject_rotation_context(g.get('active_brand'))

    return render_template('catchphrase/test_v1_dinghy.html',
                         catchphrase=catchphrase,
                         stats=stats,
                         submitted=request.args.get('submitted'),
                         **context)


@app.route('/catchphrase/results')
def catchphrase_results():
    """Dashboard showing all catchphrase A/B test results"""
    from rotation_helpers import inject_rotation_context

    db = get_db()

    # Get all catchphrases with their reaction stats
    catchphrases = db.execute('''
        SELECT
            c.*,
            COUNT(cr.id) as total_reactions,
            SUM(CASE WHEN cr.reaction_type = 'love' THEN 1 ELSE 0 END) as love_count,
            SUM(CASE WHEN cr.reaction_type = 'like' THEN 1 ELSE 0 END) as like_count,
            SUM(CASE WHEN cr.reaction_type = 'meh' THEN 1 ELSE 0 END) as meh_count,
            SUM(CASE WHEN cr.reaction_type = 'dislike' THEN 1 ELSE 0 END) as dislike_count,
            SUM(CASE WHEN cr.reaction_type = 'cringe' THEN 1 ELSE 0 END) as cringe_count
        FROM catchphrases c
        LEFT JOIN catchphrase_reactions cr ON c.id = cr.catchphrase_id
        WHERE c.brand_slug = ?
        GROUP BY c.id
        ORDER BY c.category, c.variant_label
    ''', (g.get('domain_slug', 'calriven'),)).fetchall()

    # Calculate percentages
    results = []
    for cp in catchphrases:
        total = cp['total_reactions'] or 1  # Avoid division by zero
        results.append({
            'id': cp['id'],
            'text': cp['text'],
            'category': cp['category'],
            'variant_label': cp['variant_label'],
            'total_reactions': cp['total_reactions'],
            'love_pct': round((cp['love_count'] or 0) / total * 100),
            'like_pct': round((cp['like_count'] or 0) / total * 100),
            'meh_pct': round((cp['meh_count'] or 0) / total * 100),
            'dislike_pct': round((cp['dislike_count'] or 0) / total * 100),
            'cringe_pct': round((cp['cringe_count'] or 0) / total * 100),
            # Calculate "approval" score (love * 2 + like - dislike - cringe * 2)
            'approval_score': ((cp['love_count'] or 0) * 2 +
                             (cp['like_count'] or 0) -
                             (cp['dislike_count'] or 0) -
                             (cp['cringe_count'] or 0) * 2)
        })

    # Group by category
    by_category = {}
    for r in results:
        cat = r['category'] or 'uncategorized'
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)

    # Inject rotation context for theming
    context = inject_rotation_context(g.get('active_brand'))

    return render_template('catchphrase/results_v1_dinghy.html',
                         results=results,
                         by_category=by_category,
                         **context)


@app.route('/debug/rotation')
def debug_rotation():
    """Debug endpoint to see current rotation context with neural network analysis"""
    from flask import g
    from rotation_helpers import get_domain_slug_from_brand, inject_rotation_context
    from brand_neural_analysis import analyze_brand_colors, generate_rotation_questions

    brand = g.get('active_brand', None)

    # Get full rotation context (includes colors)
    context = inject_rotation_context(brand)

    # Get neural network predictions for brand if available
    neural_predictions = {}
    suggested_questions = []
    if brand:
        try:
            # Analyze brand colors with neural network
            personality_analysis = analyze_brand_colors(brand)
            neural_predictions['personality'] = personality_analysis['personality']
            neural_predictions['energy'] = personality_analysis['energy']
            neural_predictions['warmth'] = personality_analysis['warmth']
            neural_predictions['confidence'] = f"{personality_analysis['confidence']:.1%}"

            # Generate AI-powered questions based on personality
            suggested_questions = generate_rotation_questions(personality_analysis, count=4)
        except Exception as e:
            neural_predictions['error'] = str(e)

    # Return as formatted HTML table instead of raw JSON
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rotation Debug - {context['domain_name']}</title>
        <style>
            body {{ font-family: system-ui; max-width: 1000px; margin: 40px auto; padding: 20px; background: {context['theme_background']}; }}
            h1 {{ color: {context['theme_primary']}; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: {context['theme_primary']}; color: white; font-weight: 600; }}
            .color-box {{ width: 40px; height: 40px; border-radius: 4px; display: inline-block; margin-right: 10px; vertical-align: middle; }}
            .section {{ margin: 30px 0; }}
            .back-link {{ color: {context['theme_primary']}; text-decoration: none; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to {context['domain_name']}</a>
        <h1>{context['domain_emoji']} Rotation Debug: {context['domain_name']}</h1>

        <div class="section">
            <h2>Brand Information</h2>
            <table>
                <tr><th>Property</th><th>Value</th></tr>
                <tr><td>Domain Slug</td><td>{context['domain_slug']}</td></tr>
                <tr><td>Brand Name</td><td>{context['domain_name']}</td></tr>
                <tr><td>Brand Type</td><td>{brand.get('brand_type') if brand else 'None'}</td></tr>
                <tr><td>Emoji</td><td style="font-size: 2em;">{context['domain_emoji']}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>Rotation Contexts</h2>
            <table>
                <tr><th>Context Type</th><th>Current Value</th></tr>
                <tr><td>Question</td><td><strong>{context['domain_question'] or 'None'}</strong></td></tr>
                <tr><td>Theme</td><td>{context['domain_theme'] or 'None'}</td></tr>
                <tr><td>Profile</td><td>{context['domain_profile'] or 'None'}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>Theme Colors</h2>
            <table>
                <tr><th>Color</th><th>Value</th><th>Preview</th></tr>
                <tr>
                    <td>Primary</td>
                    <td>{context['theme_primary']}</td>
                    <td><span class="color-box" style="background: {context['theme_primary']};"></span></td>
                </tr>
                <tr>
                    <td>Secondary</td>
                    <td>{context['theme_secondary']}</td>
                    <td><span class="color-box" style="background: {context['theme_secondary']};"></span></td>
                </tr>
                <tr>
                    <td>Accent</td>
                    <td>{context['theme_accent']}</td>
                    <td><span class="color-box" style="background: {context['theme_accent']};"></span></td>
                </tr>
                <tr>
                    <td>Background</td>
                    <td>{context['theme_background']}</td>
                    <td><span class="color-box" style="background: {context['theme_background']};"></span></td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>🧠 Neural Network Analysis</h2>
            <table>
                <tr><th>Analysis Type</th><th>Result</th></tr>
                <tr><td>Brand Personality</td><td><strong>{neural_predictions.get('personality', 'Not analyzed')}</strong></td></tr>
                <tr><td>Energy Level</td><td>{neural_predictions.get('energy', 'N/A')}</td></tr>
                <tr><td>Color Warmth</td><td>{neural_predictions.get('warmth', 'N/A')}</td></tr>
                <tr><td>Confidence Score</td><td>{neural_predictions.get('confidence', 'N/A')}</td></tr>
                <tr><td>Active Networks</td><td>{len(app.networks) if app.networks else 0} loaded</td></tr>
            </table>
        </div>

        {'<div class="section"><h2>💡 AI-Generated Questions</h2><p style="color: #666; margin-bottom: 15px;">Based on brand personality analysis, here are suggested rotation questions:</p><table><tr><th>#</th><th>Suggested Question</th></tr>' + ''.join([f'<tr><td>{i+1}</td><td>{q}</td></tr>' for i, q in enumerate(suggested_questions)]) + '</table></div>' if suggested_questions else ''}

        <p style="color: #666; margin-top: 40px;">
            <small>Debug endpoint • Rotation system v1.0 • Template versioning active</small>
        </p>
    </body>
    </html>
    """

    return html


@app.route('/debug/map')
def debug_system_map():
    """Visual map showing how all system components connect"""
    from flask import g

    brand = g.get('active_brand', None)
    brand_name = brand['name'] if brand else 'Soulfra'
    brand_type = brand.get('brand_type') if brand else 'blog'
    primary_color = brand.get('colors_list', ['#667eea'])[0] if brand and brand.get('colors_list') else '#667eea'

    db = get_db()

    # Get system stats
    stats = {
        'templates': db.execute('SELECT COUNT(*) FROM template_versions').fetchone()[0],
        'brands': db.execute('SELECT COUNT(*) FROM brands').fetchone()[0],
        'plots': db.execute('SELECT COUNT(*) FROM plots').fetchone()[0],
        'users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'rotation_contexts': db.execute('SELECT COUNT(*) FROM domain_contexts WHERE active = 1').fetchone()[0],
        'neural_networks': len(app.networks) if app.networks else 0
    }

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Architecture Map</title>
        <style>
            body {{ font-family: system-ui; max-width: 1400px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
            h1 {{ color: {primary_color}; text-align: center; }}
            .back-link {{ color: {primary_color}; text-decoration: none; }}
            .map-container {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 20px 0; }}
            .layer {{ margin: 30px 0; padding: 20px; border-left: 4px solid {primary_color}; background: #f8f9fa; }}
            .layer-title {{ font-size: 1.5em; font-weight: bold; color: {primary_color}; margin-bottom: 15px; }}
            .component {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .component-name {{ font-weight: 600; color: #333; margin-bottom: 8px; }}
            .component-desc {{ color: #666; font-size: 0.9em; }}
            .arrow {{ text-align: center; font-size: 2em; color: {primary_color}; margin: 10px 0; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-box {{ background: linear-gradient(135deg, {primary_color} 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-number {{ font-size: 2.5em; font-weight: bold; }}
            .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        </style>
    </head>
    <body>
        <a href="/debug/rotation" class="back-link">← Back to Debug</a>
        <h1>🗺️ Soulfra System Architecture</h1>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number">{stats['templates']}</div>
                <div class="stat-label">Templates</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['brands']}</div>
                <div class="stat-label">Brands</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['plots']}</div>
                <div class="stat-label">Plots</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['users']}</div>
                <div class="stat-label">Users</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['rotation_contexts']}</div>
                <div class="stat-label">Rotation Contexts</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['neural_networks']}</div>
                <div class="stat-label">Neural Networks</div>
            </div>
        </div>

        <div class="map-container">
            <div class="layer">
                <div class="layer-title">1️⃣ Entry: User Visits Subdomain</div>
                <div class="component">
                    <div class="component-name">Subdomain Router (subdomain_router.py)</div>
                    <div class="component-desc">Detects brand from subdomain (e.g., cringeproof.localhost) → Loads brand config from database</div>
                </div>
            </div>

            <div class="arrow">↓</div>

            <div class="layer">
                <div class="layer-title">2️⃣ Neural Analysis: Brand Colors → Personality</div>
                <div class="component">
                    <div class="component-name">Brand Neural Analysis (brand_neural_analysis.py)</div>
                    <div class="component-desc">Neural network analyzes brand RGB colors → Predicts personality (e.g., "Energetic and bold") → Generates themed questions</div>
                </div>
            </div>

            <div class="arrow">↓</div>

            <div class="layer">
                <div class="layer-title">3️⃣ Rotation Context: Dynamic Questions/Themes</div>
                <div class="component">
                    <div class="component-name">Rotation Helpers (rotation_helpers.py)</div>
                    <div class="component-desc">Loads current rotation context from database → Cycles through questions based on time → Injects into template variables</div>
                </div>
            </div>

            <div class="arrow">↓</div>

            <div class="layer">
                <div class="layer-title">4️⃣ Smart Routing: Game vs Blog</div>
                <div class="component">
                    <div class="component-name">Index Route (app.py:135)</div>
                    <div class="component-desc">
                        • Game brands (brand_type='game') → Redirect to /onboard<br>
                        • Blog brands → Show newsletter homepage<br>
                        • Current: <strong>{brand_name} ({brand_type})</strong>
                    </div>
                </div>
            </div>

            <div class="arrow">↓</div>

            <div class="layer">
                <div class="layer-title">5️⃣ Template Rendering: Versioned Templates</div>
                <div class="component">
                    <div class="component-name">Template Versioning (template_versions table)</div>
                    <div class="component-desc">Loads versioned template (v1_dinghy, v2_schooner, etc.) → Applies brand colors + rotation context → Renders final HTML</div>
                </div>
            </div>

            <div class="arrow">↓</div>

            <div class="layer">
                <div class="layer-title">6️⃣ User Action: Onboarding/Signup</div>
                <div class="component">
                    <div class="component-name">Onboarding Route (app.py:2756)</div>
                    <div class="component-desc">User completes multi-step form → Creates account + plot → Generates QR code → Adds to reputation system</div>
                </div>
            </div>

            <div class="arrow">↓</div>

            <div class="layer">
                <div class="layer-title">7️⃣ Game Features: Rankings/News/Profiles</div>
                <div class="component">
                    <div class="component-name">Game Routes (app.py:2824-2904)</div>
                    <div class="component-desc">
                        • /rankings → Leaderboard by reputation<br>
                        • /news → Game announcements (with RSS)<br>
                        • /profile/username → Player profile with plots + QR codes
                    </div>
                </div>
            </div>
        </div>

        <div class="map-container">
            <h2 style="color: {primary_color}; margin-bottom: 20px;">🔄 Data Flow Example (Cringeproof)</h2>
            <ol style="line-height: 2;">
                <li>User visits <strong>cringeproof.localhost:5001</strong></li>
                <li>Subdomain router detects "cringeproof" brand</li>
                <li>Neural net analyzes brand colors (#FF6B6B = red) → "Energetic and bold"</li>
                <li>AI generates questions: "What bold move will you make today?"</li>
                <li>Rotation system loads current question from database (rotation_order = 1)</li>
                <li>Index route sees brand_type = 'game' → Redirects to /onboard</li>
                <li>Onboarding template (v1_dinghy.html) renders with:</li>
                <ul>
                    <li>domain_question: "What town are you defending today?"</li>
                    <li>theme_primary: #FF6B6B (red)</li>
                    <li>theme_secondary: #4ECDC4 (cyan)</li>
                    <li>domain_emoji: 🎮</li>
                </ul>
                <li>User fills form → Plot created with QR code → Redirected to /profile</li>
            </ol>
        </div>

        <p style="text-align: center; color: #666; margin-top: 40px;">
            <small>System Map • All components connected • Template versioning + Neural networks + Rotation contexts</small>
        </p>
    </body>
    </html>
    """

    return html


@app.route('/debug/neural')
def debug_neural():
    """Neural network color feature extraction debugger"""
    from flask import g
    from brand_color_neural_network import load_network_from_database

    brand = g.get('active_brand', None)
    domain_name = brand['name'] if brand else 'Soulfra'

    # Check if trained model exists
    has_model = False
    try:
        nn = load_network_from_database('color_to_personality')
        has_model = nn is not None
    except:
        pass

    return render_template('debug/neural_v1_dinghy.html',
                         domain_name=domain_name,
                         has_model=has_model)


@app.route('/api/predict-personality')
def api_predict_personality():
    """API endpoint for personality prediction from color"""
    from flask import request, jsonify
    from brand_color_neural_network import predict_personality_from_color

    color_hex = request.args.get('color', '#667eea')

    # Ensure hex format
    if not color_hex.startswith('#'):
        color_hex = '#' + color_hex

    try:
        predictions = predict_personality_from_color(color_hex)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug/theme')
def debug_theme():
    """Dark/light mode theme system demo"""
    from flask import g
    from rotation_helpers import inject_rotation_context

    brand = g.get('active_brand', None)

    # Get theme colors (includes domain_name already)
    rotation_ctx = inject_rotation_context(brand)

    return render_template('debug/theme_demo_v1_dinghy.html',
                         **rotation_ctx)


# ==================== USER AUTH ROUTES ====================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup page - uses versioned template with rotation context"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # SOULFRA SIMPLE BUILDER: Collect quiz answers
        quiz_answers = {
            'vibe': request.form.get('vibe', ''),
            'communication_style': request.form.get('communication_style', ''),
            'goals': request.form.get('goals', ''),
            'aesthetic': request.form.get('aesthetic', ''),
            'privacy': request.form.get('privacy', ''),
            'town_name': request.form.get('town_name', ''),
            'plot_type': request.form.get('plot_type', 'town')
        }

        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('signup'))

        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('signup'))

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('signup'))

        # Create user
        user = create_user(username, email, password)

        if not user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('signup'))

        # Auto-login after signup
        session['user_id'] = user['id']
        session['username'] = user['username']

        # ==================================================================
        # SOULFRA SIMPLE BUILDER: Auto-generate full site!
        # ==================================================================
        try:
            from soulfra_simple_builder import SoulfraSimpleBuilder

            builder = SoulfraSimpleBuilder()

            # Match quiz to theme
            theme = builder.match_quiz_to_theme(quiz_answers)
            print(f"[SOULFRA SIMPLE] Matched theme: {theme} for user {username}")

            # Generate full site
            result = builder.generate_full_site(user['id'], theme, quiz_answers)

            if result['success']:
                # Store theme and quiz answers in session for now
                session['theme'] = theme
                session['quiz_answers'] = quiz_answers
                session['arcade_token'] = result['arcade_token']

                print(f"[SOULFRA SIMPLE] ✅ Full site generated for {username}!")
                print(f"[SOULFRA SIMPLE] Theme: {theme}")
                print(f"[SOULFRA SIMPLE] Generated: {list(result['generated'].keys())}")

                flash(f'🎉 Welcome to Soulfra, {username}! Your {theme} site is ready!', 'success')
            else:
                print(f"[SOULFRA SIMPLE] ⚠️ Site generation failed: {result.get('errors', [])}")
                flash(f'Welcome to Soulfra, {username}!', 'success')

        except Exception as e:
            print(f"[SOULFRA SIMPLE] Error during site generation: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Welcome to Soulfra, {username}!', 'success')

        # CLAIM RESULT: If user signed up from cringeproof results page
        claim_result_id = request.args.get('claim_result') or request.form.get('claim_result')
        if claim_result_id:
            try:
                from database import get_db
                db = get_db()

                # Update the game result to link it to this user
                db.execute('''
                    UPDATE game_results
                    SET user_id = ?
                    WHERE id = ? AND user_id IS NULL
                ''', (user['id'], int(claim_result_id)))

                db.commit()

                flash(f'Your cringeproof result has been saved to your profile.', 'success')
                return redirect(url_for('cringeproof_results', result_id=claim_result_id))

            except Exception as e:
                print(f"Error claiming result: {e}")
                return redirect(url_for('index'))

        return redirect(url_for('index'))

    # Use versioned template (rotation context auto-injected by subdomain router)
    return render_template('signup/v1_dinghy.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('login'))

        # Get user
        user = get_user_by_username(username)

        if not user or not verify_password(user, password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        # Log in user
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = user['is_admin']

        flash(f'Welcome back, {username}!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/signup/professional', methods=['GET', 'POST'])
def signup_professional():
    """Professional signup for StPetePros directory"""
    if request.method == 'POST':
        business_name = request.form.get('business_name', '').strip()
        category = request.form.get('category', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        bio = request.form.get('bio', '').strip()
        address = request.form.get('address', '').strip()
        website = request.form.get('website', '').strip()

        # Validation
        if not business_name or not category or not email or not phone or not bio:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('signup_professional'))

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('signup_professional'))

        db = get_db()

        try:
            # Insert into professionals table
            db.execute('''
                INSERT INTO professionals (
                    business_name, category, email, phone, bio, address, website,
                    verified, rating_avg, review_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0.0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (business_name, category, email, phone, bio, address, website))

            # Also add to subscribers table for newsletters
            db.execute('''
                INSERT OR IGNORE INTO subscribers (email)
                VALUES (?)
            ''', (email,))

            db.commit()

            flash(f'🎉 Welcome to StPetePros, {business_name}! Your profile has been created.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            print(f"Error creating professional profile: {e}")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('signup_professional'))

    # GET request - show signup form
    return render_template('stpetepros/signup.html')


@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('index'))


# ==================== FEEDBACK (PUBLIC) ====================

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Public feedback form - NO LOGIN REQUIRED"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        component = request.form.get('component', '').strip()
        message = request.form.get('message', '').strip()

        if not message:
            flash('Please provide feedback message', 'error')
            return redirect(url_for('feedback'))

        # Store feedback
        db = get_db()
        db.execute('''
            INSERT INTO feedback (name, email, component, message, url, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name or 'Anonymous',
            email,
            component,
            message,
            request.referrer or request.url,
            request.headers.get('User-Agent')
        ))
        db.commit()
        db.close()

        flash('✅ Thank you! Your feedback has been sent to the admin.', 'success')
        return redirect(url_for('index'))

    # GET: Show form
    components = [
        'Posts/Articles',
        'Comments',
        'Soul Browser',
        'Gallery/Showcase',
        'Reasoning Engine',
        'Admin Panel',
        'User Profiles',
        'Login/Signup',
        'Other'
    ]

    return render_template('feedback.html', components=components)


# ==================== API ROUTES ====================

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    from database import get_db
    try:
        db = get_db()
        db.execute('SELECT 1').fetchone()
        db.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/ollama/comment', methods=['POST'])
def api_ollama_comment():
    """
    Get AI comments from Ollama for a post

    POST body: {"post_id": 42, "auto_post": true}
    Returns: {
        "success": true,
        "comments": [{"persona": "calriven", "comment": "..."}]
    }
    """
    import urllib.request
    import urllib.error
    import json

    data = request.get_json() or {}
    post_id = data.get('post_id')
    auto_post = data.get('auto_post', False)

    if not post_id:
        return jsonify({'success': False, 'error': 'post_id required'}), 400

    from database import get_db

    # Get post
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if not post:
        db.close()
        return jsonify({'success': False, 'error': 'Post not found'}), 404

    # AI Persona definitions
    PERSONAS = {
        'calriven': {
            'user_id': 2,  # CalRiven's user ID
            'system_prompt': 'You are CalRiven, a technical architecture expert. Focus on data structures, system design, performance, and code quality. Be direct and technical.'
        },
        'deathtodata': {
            'user_id': 3,  # DeathToData's user ID
            'system_prompt': 'You are DeathToData, a privacy advocate. Focus on surveillance risks, data collection, and anti-tracking. Be skeptical and privacy-focused.'
        },
        'theauditor': {
            'user_id': 4,  # TheAuditor's user ID
            'system_prompt': 'You are TheAuditor, a validation expert. Focus on testing, verification, and finding edge cases. Be thorough and questioning.'
        },
        'soulfra': {
            'user_id': 5,  # Soulfra's user ID
            'system_prompt': 'You are Soulfra, a security expert. Focus on encryption, authentication, and security best practices. Be cautious and security-focused.'
        }
    }

    comments_generated = []

    # Try to call Ollama for each persona
    for persona_name, persona_data in PERSONAS.items():
        try:
            # Prepare Ollama API request
            ollama_request = {
                'model': 'llama2',
                'prompt': f"{persona_data['system_prompt']}\n\nPost Title: {post['title']}\n\nContent:\n{post['content']}\n\nProvide a thoughtful comment (2-3 sentences):",
                'stream': False
            }

            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=json.dumps(ollama_request).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            # Call Ollama (with 10 second timeout)
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                comment_text = result.get('response', '').strip()

                if comment_text:
                    # Optionally post as comment
                    if auto_post:
                        db.execute('''
                            INSERT INTO comments (post_id, user_id, content, created_at)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (post_id, persona_data['user_id'], comment_text))
                        db.commit()

                    comments_generated.append({
                        'persona': persona_name,
                        'comment': comment_text,
                        'posted': auto_post
                    })

        except urllib.error.URLError:
            # Ollama not running - skip this persona
            comments_generated.append({
                'persona': persona_name,
                'error': 'Ollama not running (start with: ollama serve)'
            })
        except Exception as e:
            comments_generated.append({
                'persona': persona_name,
                'error': str(e)
            })

    db.close()

    return jsonify({
        'success': True,
        'post_id': post_id,
        'comments': comments_generated,
        'auto_posted': auto_post
    })


@app.route('/api/gallery/chat', methods=['POST'])
def api_gallery_chat():
    """
    Chat with AI about a gallery/post

    POST body: {
        "slug": "post-slug",
        "question": "What is this about?",
        "context": "optional additional context"
    }
    Returns: {
        "success": true,
        "answer": "AI response...",
        "model": "llama2"
    }
    """
    import urllib.request
    import urllib.error
    import json

    data = request.get_json() or {}
    slug = data.get('slug')
    question = data.get('question', '')
    context = data.get('context', '')

    if not slug:
        return jsonify({'success': False, 'error': 'slug required'}), 400

    if not question:
        return jsonify({'success': False, 'error': 'question required'}), 400

    from database import get_db

    # Get post by slug using qr_galleries table
    db = get_db()

    # First, get post_id from qr_galleries
    gallery = db.execute('''
        SELECT post_id FROM qr_galleries
        WHERE gallery_slug = ?
    ''', (slug,)).fetchone()

    if not gallery:
        db.close()
        return jsonify({'success': False, 'error': 'Gallery not found'}), 404

    # Then get the post
    post = db.execute('SELECT * FROM posts WHERE id = ?', (gallery['post_id'],)).fetchone()

    if not post:
        db.close()
        return jsonify({'success': False, 'error': 'Post not found'}), 404

    # Build prompt - conversational first, post-aware second
    prompt = f"""You are a friendly AI assistant. A user is viewing a gallery called "{post['title']}".

Be natural and conversational. Respond warmly to greetings and small talk. Only discuss the post content if they specifically ask about it.

User: {question}"""

    # Use LLM router for automatic model fallback
    from llm_router import LLMRouter

    router = LLMRouter()
    result = router.call(prompt=prompt, timeout=30)

    # Get user info for analytics
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')

    # Detect device type
    device_type = 'Desktop'
    if 'iPhone' in user_agent or 'iPad' in user_agent:
        device_type = 'iOS'
    elif 'Android' in user_agent:
        device_type = 'Android'

    if result['success']:
        answer = result['response']
        model_used = result['model_used']

        # Save chat to database for analytics
        db.execute('''
            INSERT INTO gallery_chats (gallery_slug, user_ip, device_type, question, answer, model)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (slug, user_ip, device_type, question, answer, model_used))
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'answer': answer,
            'model': model_used,  # Show which model actually responded
            'question': question
        })
    else:
        db.close()
        return jsonify({
            'success': False,
            'error': result['error'],
            'hint': result.get('hint', 'Check Ollama status')
        }), 503


@app.route('/api/dm/chat', methods=['POST'])
def api_dm_chat():
    """
    Handle DM chat messages from scanned QR code

    POST body: {'token': 'dm_token', 'question': 'hello'}
    Returns: {'success': True, 'answer': 'AI response'}
    """
    data = request.get_json()

    if not data or not data.get('token') or not data.get('question'):
        return jsonify({'success': False, 'error': 'token and question are required'}), 400

    token = data['token']
    question = data['question']

    # Verify token
    from dm_via_qr import verify_dm_token
    verification = verify_dm_token(token)

    if not verification.get('valid'):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired DM token'
        }), 403

    # Get author's latest post to provide context
    db = get_db()
    author_post = db.execute('''
        SELECT title, content FROM posts
        WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    ''', (verification['user_id'],)).fetchone()

    post_context = ""
    if author_post:
        post_context = f"""
The author recently posted: "{author_post['title']}"
Content excerpt: {author_post['content'][:400]}...

You can reference this post if the user asks about it.
"""

    db.close()

    # Conversational AI prompt with post context
    prompt = f"""You are a friendly AI assistant in a direct message with the author of a Soulfra post.

{post_context}
Be natural and conversational. Greet warmly if they say hello. Discuss the post content if they ask about it.

User: {question}"""

    # Use LLM router for automatic model fallback
    from llm_router import LLMRouter

    router = LLMRouter()
    result = router.call(prompt=prompt, timeout=30)

    if not result['success']:
        return jsonify({
            'success': False,
            'error': result['error'],
            'hint': result.get('hint', 'Check Ollama status')
        }), 503

    answer = result['response']
    model_used = result['model_used']

    # Save DM chat to database
    db = get_db()

    # Create dm_chats table if it doesn't exist
    db.execute('''
        CREATE TABLE IF NOT EXISTS dm_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            user_ip TEXT,
            device_type TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            model TEXT DEFAULT 'llama2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Get user info
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    device_type = 'Desktop'
    if 'iPhone' in user_agent or 'iPad' in user_agent:
        device_type = 'iOS'
    elif 'Android' in user_agent:
        device_type = 'Android'

    # Hash token for privacy
    import hashlib
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]

    # Save chat
    db.execute('''
        INSERT INTO dm_chats (user_id, token_hash, user_ip, device_type, question, answer, model)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (verification['user_id'], token_hash, user_ip, device_type, question, answer, model_used))
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'answer': answer,
        'model': model_used  # Show which model actually responded
    })


@app.route('/api/dm/generate-qr', methods=['POST'])
def api_dm_generate_qr():
    """
    Generate temporary DM QR code for a user

    POST body: {
        "user_id": 1,
        "post_slug": "optional-post-slug"
    }
    Returns: {
        "success": true,
        "qr_url": "/static/qr_codes/dm/dm_1_12345.png",
        "expiry": 12345678,
        "dm_url": "http://..."
    }
    """
    from dm_via_qr import generate_dm_qr

    data = request.get_json() or {}
    user_id = data.get('user_id')
    post_slug = data.get('post_slug', '')

    # Default to author of post if not specified
    if not user_id and post_slug:
        from database import get_db
        db = get_db()

        # Get post_id from qr_galleries table
        gallery = db.execute('''
            SELECT post_id FROM qr_galleries
            WHERE gallery_slug = ?
        ''', (post_slug,)).fetchone()

        if gallery:
            # Get author user_id from posts table
            post = db.execute('''
                SELECT user_id FROM posts WHERE id = ?
            ''', (gallery['post_id'],)).fetchone()

            if post:
                user_id = post['user_id']

        db.close()

    if not user_id:
        return jsonify({'success': False, 'error': 'user_id required'}), 400

    try:
        # Get base URL from request
        base_url = request.host_url.rstrip('/')

        # Generate DM QR
        result = generate_dm_qr(user_id, base_url=base_url)

        if not result:
            return jsonify({'success': False, 'error': 'Failed to generate QR code'}), 500

        # Return relative URL for QR image
        qr_relative_url = '/' + result['qr_path']

        return jsonify({
            'success': True,
            'qr_url': qr_relative_url,
            'expiry': result['expiry'],
            'dm_url': result['dm_url'],
            'user_id': result['user_id'],
            'username': result['username']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating DM QR: {str(e)}'
        }), 500


@app.route('/api/posts')
def api_posts():
    """Get all posts as JSON"""
    from database import get_posts

    limit = request.args.get('limit', type=int, default=10)

    posts = get_posts(limit=limit)

    return jsonify({
        'posts': [dict(p) for p in posts],
        'count': len(posts),
        'limit': limit
    })


@app.route('/api/posts/<int:post_id>')
def api_post_detail(post_id):
    """Get single post by ID as JSON"""
    from database import get_db

    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get comments
    comments = db.execute('''
        SELECT c.*, u.username, u.display_name
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()

    # Get reasoning thread
    reasoning = db.execute('''
        SELECT rt.*, COUNT(rs.id) as step_count
        FROM reasoning_threads rt
        LEFT JOIN reasoning_steps rs ON rt.id = rs.thread_id
        WHERE rt.post_id = ?
        GROUP BY rt.id
    ''', (post_id,)).fetchone()

    db.close()

    return jsonify({
        'post': dict(post),
        'comments': [dict(c) for c in comments],
        'reasoning': dict(reasoning) if reasoning else None
    })


@app.route('/api/reasoning/threads')
def api_reasoning_threads():
    """Get all reasoning threads as JSON"""
    from database import get_db

    db = get_db()
    threads = db.execute('''
        SELECT rt.*, p.title as post_title, COUNT(rs.id) as step_count
        FROM reasoning_threads rt
        JOIN posts p ON rt.post_id = p.id
        LEFT JOIN reasoning_steps rs ON rt.id = rs.thread_id
        GROUP BY rt.id
        ORDER BY rt.created_at DESC
    ''').fetchall()
    db.close()

    return jsonify({
        'threads': [dict(t) for t in threads],
        'count': len(threads)
    })


@app.route('/api/reasoning/threads/<int:thread_id>')
def api_reasoning_thread_detail(thread_id):
    """Get reasoning thread with all steps as JSON"""
    from database import get_db

    db = get_db()

    thread = db.execute('SELECT * FROM reasoning_threads WHERE id = ?', (thread_id,)).fetchone()
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404

    steps = db.execute('''
        SELECT rs.*, u.username, u.display_name
        FROM reasoning_steps rs
        JOIN users u ON rs.user_id = u.id
        WHERE rs.thread_id = ?
        ORDER BY rs.step_number ASC
    ''', (thread_id,)).fetchall()

    db.close()

    return jsonify({
        'thread': dict(thread),
        'steps': [dict(s) for s in steps]
    })


@app.route('/api/feedback', methods=['POST'])
def api_submit_feedback():
    """Submit feedback via API"""
    from database import get_db

    data = request.get_json()

    if not data or not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400

    db = get_db()
    db.execute('''
        INSERT INTO feedback (name, email, component, message)
        VALUES (?, ?, ?, ?)
    ''', (
        data.get('name', 'Anonymous'),
        data.get('email', ''),
        data.get('component', 'Other'),
        data['message']
    ))
    db.commit()
    feedback_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()

    return jsonify({
        'success': True,
        'feedback_id': feedback_id,
        'message': 'Feedback submitted successfully'
    }), 201


@app.route('/api/website/predict/type', methods=['POST'])
def api_predict_route_type():
    """
    Predict route type from path and description (ML-powered)

    POST body: {'path': '/api/users', 'description': 'Get all users'}
    Returns: {'type': 'api', 'confidence': 0.85}
    """
    from train_website_model import predict_route_type

    data = request.get_json()

    if not data or not data.get('path'):
        return jsonify({'error': 'path is required'}), 400

    route_path = data['path']
    description = data.get('description', '')

    route_type, confidence = predict_route_type(route_path, description)

    return jsonify({
        'path': route_path,
        'predicted_type': route_type,
        'confidence': confidence,
        'types': ['api', 'admin', 'content', 'user', 'utility', 'static']
    })


@app.route('/api/website/predict/method', methods=['POST'])
def api_predict_http_method():
    """
    Predict HTTP method from route path (ML-powered)

    POST body: {'path': '/post/<slug>'}
    Returns: {'method': 'GET', 'confidence': 0.75}
    """
    from train_website_model import predict_http_method

    data = request.get_json()

    if not data or not data.get('path'):
        return jsonify({'error': 'path is required'}), 400

    route_path = data['path']
    method, confidence = predict_http_method(route_path)

    return jsonify({
        'path': route_path,
        'predicted_method': method,
        'confidence': confidence,
        'methods': ['GET', 'POST', 'PUT', 'DELETE']
    })


@app.route('/api/website/predict/parameters', methods=['POST'])
def api_suggest_parameters():
    """
    Suggest parameter names for a route path (ML-powered)

    POST body: {'path': '/post'}
    Returns: {'suggestions': [{'param': 'slug', 'confidence': 0.9}, ...]}
    """
    from train_website_model import suggest_route_parameters

    data = request.get_json()

    if not data or not data.get('path'):
        return jsonify({'error': 'path is required'}), 400

    route_path = data['path']
    suggestions = suggest_route_parameters(route_path)

    return jsonify({
        'path': route_path,
        'suggestions': suggestions,
        'example': f"{route_path}/<{suggestions[0]['param']}>" if suggestions else route_path
    })


@app.route('/api/website/missing-routes', methods=['GET'])
def api_get_missing_routes():
    """
    Get AI-predicted missing routes based on patterns

    Returns: {'missing_routes': [...], 'total': N}
    """
    from website_structure_parser import build_training_dataset, predict_missing_routes

    # Build dataset
    dataset = build_training_dataset()

    # Predict missing routes
    predictions = predict_missing_routes(dataset)

    return jsonify({
        'missing_routes': predictions,
        'total': len(predictions),
        'confidence_threshold': 0.5
    })


@app.route('/api/website/structure', methods=['GET'])
def api_get_website_structure():
    """
    Get complete website structure analysis

    Returns: Full training dataset with statistics and patterns
    """
    from website_structure_parser import build_training_dataset

    dataset = build_training_dataset()

    # Remove full route features to reduce size (keep summary only)
    summary = {
        'statistics': dataset['statistics'],
        'patterns': dataset['patterns'],
        'total_routes': len(dataset['routes']),
        'total_templates': len(dataset['templates']),
        'route_types': list(set(r['route_type'] for r in dataset['routes'])),
        'http_methods': list(dataset['statistics']['routes_by_method'].keys())
    }

    return jsonify(summary)


@app.route('/api/brand/predict', methods=['POST'])
def api_predict_brand():
    """
    Predict which brand wrote this text (ML-powered)

    POST body: {'text': 'Technical deep dive into caching...'}
    Returns: {'brand': 'calriven', 'confidence': 0.85, ...}
    """
    from brand_voice_generator import predict_brand_voice

    data = request.get_json()

    if not data or not data.get('text'):
        return jsonify({'error': 'text is required'}), 400

    result = predict_brand_voice(data['text'])

    return jsonify(result)


@app.route('/api/brand/consistency', methods=['POST'])
def api_check_brand_consistency():
    """
    Check if text is consistent with brand voice

    POST body: {'brand': 'ocean-dreams', 'text': '...'}
    Returns: {'is_consistent': true, 'score': 0.92, 'issues': [], ...}
    """
    from brand_voice_generator import check_brand_consistency

    data = request.get_json()

    if not data or not data.get('brand') or not data.get('text'):
        return jsonify({'error': 'brand and text are required'}), 400

    result = check_brand_consistency(data['brand'], data['text'])

    return jsonify(result)


@app.route('/api/brand/generate', methods=['POST'])
def api_generate_brand_content():
    """
    Generate content in brand voice

    POST body: {'brand': 'calriven', 'topic': 'ML training', 'include_emoji': true}
    Returns: {'content': '💻 Analysis: ML training...', 'brand': 'calriven'}
    """
    from brand_voice_generator import generate_brand_content

    data = request.get_json()

    if not data or not data.get('brand') or not data.get('topic'):
        return jsonify({'error': 'brand and topic are required'}), 400

    content = generate_brand_content(
        data['brand'],
        data['topic'],
        length=data.get('length', 'short'),
        include_emoji=data.get('include_emoji', True)
    )

    return jsonify({
        'content': content,
        'brand': data['brand'],
        'topic': data['topic']
    })


@app.route('/api/brand/emoji/suggest', methods=['POST'])
def api_suggest_brand_emoji():
    """
    Suggest emoji for brand based on context

    POST body: {'brand': 'calriven', 'context': 'technical implementation'}
    Returns: {'suggestions': [{'emoji': '💻', 'confidence': 0.85, ...}]}
    """
    from brand_voice_generator import suggest_brand_emoji

    data = request.get_json()

    if not data or not data.get('brand'):
        return jsonify({'error': 'brand is required'}), 400

    suggestions = suggest_brand_emoji(
        data['brand'],
        context=data.get('context', '')
    )

    return jsonify({
        'brand': data['brand'],
        'suggestions': suggestions
    })


@app.route('/api/brand/wordmap/<slug>', methods=['GET'])
def api_get_brand_wordmap(slug):
    """
    Get brand's vocabulary wordmap

    Returns: {'brand': 'calriven', 'wordmap': {'technical': 42, ...}}
    """
    from brand_vocabulary_trainer import get_brand_wordmap

    wordmap = get_brand_wordmap(slug)

    if not wordmap:
        return jsonify({'error': f'Brand {slug} not found or not trained'}), 404

    return jsonify({
        'brand': slug,
        'wordmap': wordmap,
        'top_words': list(wordmap.items())[:20]
    })


@app.route('/api/brand/voice/compare', methods=['POST'])
def api_compare_brand_voices():
    """
    Compare voices of two brands

    POST body: {'brand1': 'calriven', 'brand2': 'ocean-dreams'}
    Returns: {'vocabulary': {...}, 'emoji': {...}, 'overall_similarity': 0.23}
    """
    from brand_voice_generator import compare_brand_voices

    data = request.get_json()

    if not data or not data.get('brand1') or not data.get('brand2'):
        return jsonify({'error': 'brand1 and brand2 are required'}), 400

    comparison = compare_brand_voices(data['brand1'], data['brand2'])

    return jsonify(comparison)


# ==================== ADMIN ROUTES ====================

def require_admin():
    """Check if user is logged in as admin"""
    if not session.get('is_admin'):
        # Remember where user was trying to go
        return redirect(url_for('admin_login', next=request.url))
    return None


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password', '')

        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Welcome to Soulfra Admin!', 'success')

            # Redirect to intended destination (or dashboard if none)
            next_page = request.args.get('next') or url_for('admin_dashboard')
            return redirect(next_page)
        else:
            error_html = '<div class="error">❌ Incorrect password</div>'
            return render_template('admin_login.html', error=error_html)

    return render_template('admin_login.html', error='')


@app.route('/admin')
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    """Admin dashboard - create new posts"""
    # Check auth
    auth_check = require_admin()
    if auth_check:
        return auth_check

    success_html = ''

    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        date_str = request.form.get('date', '')
        content_markdown = request.form.get('content', '')

        # Publish destinations
        dest_static = request.form.get('dest_static') == 'yes'
        dest_email = request.form.get('dest_email') == 'yes'

        # Convert Markdown to HTML
        content_html = markdown2_markdown(
            content_markdown,
            extras=['fenced-code-blocks', 'tables', 'break-on-newline']
        )

        # Parse date
        try:
            publish_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            publish_date = datetime.now()

        # Add post to database (use admin user ID from session, or default to 1)
        user_id = session.get('user_id', 1)
        add_post(user_id, title, slug, content_html, publish_date)

        # Publish to destinations
        published_to = []

        if dest_static:
            # Rebuild static site
            try:
                subprocess.run(['python3', 'build.py'], check=True, capture_output=True)
                published_to.append('Static Site (GitHub Pages)')
            except Exception as e:
                flash(f'Error building static site: {e}', 'error')

        if dest_email:
            # Send newsletter
            try:
                from emails import send_post_email
                post_data = {
                    'title': title,
                    'content': content_html,
                    'slug': slug,
                    'published_at': publish_date
                }
                send_post_email(post_data)
                published_to.append('Email Newsletter')
            except Exception as e:
                flash(f'Error sending email: {e}', 'error')

        # Success message
        destinations = ', '.join(published_to) if published_to else 'Database only'
        success_html = f'<div class="success">✅ Post published successfully to: {destinations}!</div>'

    # Get stats
    stats = get_stats()

    # Get recent feedback (last 10)
    db = get_db()
    feedback_items = db.execute('''
        SELECT id, name, component, message, created_at, status
        FROM feedback
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()
    feedback_count = db.execute('SELECT COUNT(*) as count FROM feedback WHERE status = "new"').fetchone()['count']
    db.close()

    return render_template(
        'admin_dashboard.html',
        success=success_html,
        stats_posts=stats['posts'],
        stats_subscribers=stats['subscribers'],
        feedback_items=[dict(f) for f in feedback_items],
        feedback_count=feedback_count,
        today=datetime.now().strftime('%Y-%m-%d')
    )


@app.route('/admin/automation')
def admin_automation():
    """Admin automation panel - run tasks from web interface"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    # Get user role
    db = get_db()
    user = db.execute('SELECT role FROM users WHERE id = ?', (session.get('user_id'),)).fetchone()
    db.close()

    user_role = user['role'] if user else 'user'

    return render_template('admin_automation.html', user_role=user_role)


@app.route('/admin/automation/run-builder', methods=['POST'])
def admin_run_builder():
    """Run public builder automation from admin panel"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        # Import and run public builder logic
        from public_builder import run_public_builder
        results = run_public_builder()

        flash(f'✅ Public builder complete: {results["posts_created"]} posts created, {results["feedback_processed"]} feedback processed', 'success')
    except Exception as e:
        flash(f'❌ Error running public builder: {e}', 'error')

    return redirect(url_for('admin_automation'))


@app.route('/admin/automation/generate-digest', methods=['POST'])
def admin_generate_digest():
    """Generate weekly newsletter digest from admin panel"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        # Import and run newsletter digest logic
        from newsletter_digest import send_weekly_digest
        questions = send_weekly_digest(dry_run=True)

        flash(f'✅ Digest generated: {len(questions)} decision questions created. Preview saved to weekly_digest_preview.html', 'success')
    except Exception as e:
        flash(f'❌ Error generating digest: {e}', 'error')

    return redirect(url_for('admin_automation'))


@app.route('/admin/automation/send-digest', methods=['POST'])
def admin_send_digest():
    """Send weekly digest to subscribers"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        from newsletter_digest import send_weekly_digest
        questions = send_weekly_digest(dry_run=False)

        flash(f'✅ Digest sent to subscribers with {len(questions)} decision questions', 'success')
    except Exception as e:
        flash(f'❌ Error sending digest: {e}', 'error')

    return redirect(url_for('admin_automation'))


@app.route('/admin/automation/train-website-model', methods=['POST'])
def admin_train_website_model():
    """Train website structure ML model from admin panel"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        from train_website_model import train_all_models

        result = train_all_models()

        model_count = len(result['model_ids'])
        route_count = result['dataset_stats']['total_routes']

        flash(f'✅ Trained {model_count} models on {route_count} routes! Check /api/website/missing-routes for predictions.', 'success')
    except Exception as e:
        flash(f'❌ Error training model: {e}', 'error')

    return redirect(url_for('admin_automation'))


@app.route('/admin/automation/train-brand-models', methods=['POST'])
def admin_train_brand_models():
    """Train brand voice models from admin panel"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        # Train vocabulary model
        from brand_vocabulary_trainer import build_brand_training_dataset, train_brand_classifier, save_brand_model_to_db

        dataset = build_brand_training_dataset()

        if not dataset:
            flash('⚠️ No brand-post associations found! Link posts to brands in brand_posts table.', 'warning')
            return redirect(url_for('admin_automation'))

        vocab_model = train_brand_classifier(dataset)
        save_brand_model_to_db(vocab_model)

        # Train emoji patterns
        from emoji_pattern_analyzer import save_emoji_analysis_to_db
        save_emoji_analysis_to_db()

        brand_count = len(vocab_model['brands'])
        training_size = vocab_model['training_size']

        flash(f'✅ Trained brand voice models on {brand_count} brands ({training_size} posts)! Check /api/brand/wordmap for results.', 'success')
    except Exception as e:
        flash(f'❌ Error training brand models: {e}', 'error')

    return redirect(url_for('admin_automation'))


@app.route('/admin/automation/bootstrap', methods=['POST'])
def admin_bootstrap_system():
    """Run bootstrap to sync brands from manifest and cleanup"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        # Step 1: Sync brands from manifest
        from init_brands_from_manifest import sync_brands_from_manifest
        sync_result = sync_brands_from_manifest()

        # Step 2: Cleanup orphaned associations
        from cleanup_orphaned_associations import cleanup_orphaned_associations
        deleted = cleanup_orphaned_associations(dry_run=False)

        # Build success message
        message_parts = []

        if sync_result['added'] > 0:
            message_parts.append(f"Added {sync_result['added']} brands")

        if sync_result['updated'] > 0:
            message_parts.append(f"Updated {sync_result['updated']} brands")

        if deleted > 0:
            message_parts.append(f"Cleaned up {deleted} orphaned associations")

        if message_parts:
            flash(f'✅ Bootstrap complete! {", ".join(message_parts)}. System ready for training.', 'success')
        else:
            flash('✅ Bootstrap complete! System already up to date.', 'success')

    except Exception as e:
        flash(f'❌ Bootstrap error: {e}', 'error')

    return redirect(url_for('admin_automation'))


@app.route('/admin/brand-status')
def admin_brand_status():
    """Brand system status dashboard - verify ML training and brand sync"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    from brand_status_dashboard import get_full_status

    status = get_full_status()

    # Get current database name (for sandbox detection)
    import os
    db_name = os.environ.get('SOULFRA_DB', 'soulfra.db')
    is_sandbox = (db_name == 'soulfra_test.db')

    return render_template('brand_status.html',
                           status=status,
                           db_name=db_name,
                           is_sandbox=is_sandbox,
                           user_role='sysadmin')


@app.route('/api/brand/status')
def api_brand_status():
    """Get brand system status as JSON"""
    from brand_status_dashboard import get_full_status

    status = get_full_status()

    return jsonify(status)


@app.route('/admin/studio')
def admin_studio():
    """
    Visual Development Studio - Zero Terminal Required

    Features:
    - Neural network builder (visual drag-drop)
    - Schema/tool editor (JSON → Python)
    - Ollama AI chat integration
    - Live concept map visualization
    - Email template builder
    - Code generator
    - Visual test runner (NO MORE python3 test_*.py!)
    - Auto-loop testing until all pass
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    return render_template('admin_studio.html')


@app.route('/admin/form-builder', methods=['GET', 'POST'])
def admin_form_builder():
    """
    Template Form Builder - Auto-generate templates, routes, and schema from field definitions

    Takes YAML form definitions + brand theme → generates working code
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    # Load brands from manifest.yaml
    import yaml
    with open('themes/manifest.yaml', 'r') as f:
        manifest = yaml.safe_load(f)
    brands = manifest.get('themes', {})

    # Load template presets
    try:
        with open('form_builder_presets.yaml', 'r') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get('presets', {})
    except:
        presets = {}

    generated = None
    form_definition = ""
    brand = ""

    if request.method == 'POST':
        form_definition = request.form.get('form_definition', '')
        brand = request.form.get('brand', '')

        if not form_definition or not brand:
            flash('Please provide both form definition and brand selection', 'error')
        else:
            try:
                # Parse YAML form definition
                form_spec = yaml.safe_load(form_definition)

                # Get brand theme
                brand_theme = brands.get(brand, {})

                # Generate code
                template_code = generate_template_code(form_spec, brand_theme, brand)
                route_code = generate_route_code(form_spec)
                schema_code = generate_schema_code(form_spec)

                # Write generated files
                template_filename = f"{form_spec['route'].replace('/', '_').strip('_')}.html"
                template_path = f"templates/{template_filename}"

                # Save template file
                with open(template_path, 'w') as f:
                    f.write(template_code)

                # Collect all generated routes
                all_route_code = route_code
                additional_templates = []
                additional_routes_info = []

                # Check for additional routes (leaderboards, news feeds, etc.)
                if 'additional_routes' in form_spec:
                    for add_route in form_spec['additional_routes']:
                        route_type = add_route.get('type', 'page')
                        route_path = add_route.get('route', '')

                        if route_type == 'leaderboard':
                            leaderboard_code = generate_leaderboard_route(form_spec, route_path, brand_theme, brand)
                            all_route_code += '\n\n' + leaderboard_code['route']
                            additional_templates.append({
                                'path': leaderboard_code['template_path'],
                                'code': leaderboard_code['template']
                            })
                            additional_routes_info.append(f"Leaderboard: {route_path}")

                        elif route_type == 'news_feed':
                            news_code = generate_news_feed_route(form_spec, route_path, brand_theme, brand)
                            all_route_code += '\n\n' + news_code['route']
                            additional_templates.append({
                                'path': news_code['template_path'],
                                'code': news_code['template']
                            })
                            additional_routes_info.append(f"News Feed: {route_path}")

                        elif route_type == 'user_profile':
                            profile_code = generate_user_profile_route(form_spec, route_path, brand_theme, brand)
                            all_route_code += '\n\n' + profile_code['route']
                            additional_templates.append({
                                'path': profile_code['template_path'],
                                'code': profile_code['template']
                            })
                            additional_routes_info.append(f"User Profile: {route_path}")

                # Save additional templates
                for tmpl in additional_templates:
                    with open(tmpl['path'], 'w') as f:
                        f.write(tmpl['code'])

                # Add all routes to app.py (append to end of file)
                with open('app.py', 'a') as f:
                    f.write('\n\n' + all_route_code)

                # Update schema.json
                import json
                schema_path = 'api/schema.json'
                try:
                    with open(schema_path, 'r') as f:
                        schema = json.load(f)
                except:
                    schema = {'tables': {}}

                # Add new table
                schema['tables'][form_spec['table']] = json.loads(schema_code)

                with open(schema_path, 'w') as f:
                    json.dump(schema, f, indent=2)

                generated = {
                    'template_path': template_path,
                    'route_added': f"app.py (route: {form_spec['route']})",
                    'schema_updated': f"api/schema.json (table: {form_spec['table']})",
                    'template_code': template_code,
                    'route_code': all_route_code,
                    'schema_code': json.dumps(json.loads(schema_code), indent=2),
                    'additional_routes': additional_routes_info
                }

                success_msg = f"✅ Successfully generated template, route, and schema!"
                if additional_routes_info:
                    success_msg += f" Plus {len(additional_routes_info)} additional routes: {', '.join(additional_routes_info)}"
                flash(success_msg, 'success')

            except Exception as e:
                flash(f'Error generating code: {str(e)}', 'error')

    return render_template('admin_form_builder.html',
                         brands=brands,
                         presets=presets,
                         generated=generated,
                         form_definition=form_definition,
                         brand=brand)


@app.route('/api/form-builder/parse-description', methods=['POST'])
def api_parse_form_description():
    """
    Parse natural language description into YAML form spec using Ollama

    Takes: {"description": "I want a game where..."}
    Returns: {"yaml": "name: ...\nfields:\n  ..."}
    """
    data = request.get_json()
    description = data.get('description', '').strip()

    if not description:
        return jsonify({'error': 'No description provided'}), 400

    # Craft Ollama prompt to extract form spec
    prompt = f"""Extract a form specification from this natural language description:

"{description}"

Return ONLY valid YAML with this exact structure (no markdown, no explanation, just YAML):

name: [Form/Game Name]
route: /[route-path]
table: [table_name]
subdomain: [subdomain-slug]
auth_type: [password|qr_code|jwt]
features:
  - [list features like: user_registration, reputation_tracking, leaderboard, news_feed]
fields:
  - name: [field_name]
    type: [text|email|number|textarea|select]
    label: [Human Label]
    required: [true|false]
    description: [optional help text]
additional_routes:
  - route: /[path]
    type: [leaderboard|news_feed|user_profile]
    description: [what this route does]

RULES:
1. Extract ALL fields mentioned (username, email, town, QR code, etc.)
2. If description mentions "game" or "compete" or "points" or "ranking", include: reputation_tracking + leaderboard
3. If description mentions "news" or "posts" or "announcements", include: news_feed
4. Auth type: password (default), qr_code (if QR mentioned), jwt (if API mentioned)
5. Field types: text (default), email (for email), number (for numeric), textarea (for long text)
6. Make route and table names based on the form/game name (lowercase, hyphens/underscores)
7. Subdomain should be short slug of the name
8. Return ONLY the YAML, nothing else!

Example input: "I want a cringeproof game where roommates signup with town and QR code, compete for points"

Example output:
name: Cringeproof Game
route: /signup
table: cringeproof_users
subdomain: cringeproof
auth_type: qr_code
features:
  - user_registration
  - reputation_tracking
  - leaderboard
fields:
  - name: username
    type: text
    label: Username
    required: true
  - name: town_name
    type: text
    label: Town Name
    required: true
  - name: qr_code_url
    type: text
    label: QR Code URL
    required: false
additional_routes:
  - route: /rankings
    type: leaderboard
    description: Top players by points"""

    # Call Ollama
    try:
        import json as json_lib
        import urllib.request
        import urllib.error

        ollama_url = 'http://localhost:11434/api/generate'
        ollama_data = {
            'model': 'llama3.2:latest',
            'prompt': prompt,
            'stream': False
        }

        req = urllib.request.Request(
            ollama_url,
            data=json_lib.dumps(ollama_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json_lib.loads(response.read().decode('utf-8'))
            yaml_output = result.get('response', '').strip()

            # Clean up markdown if present
            if yaml_output.startswith('```yaml'):
                yaml_output = yaml_output.split('```yaml')[1]
            if yaml_output.startswith('```'):
                yaml_output = yaml_output.split('```')[1]
            if '```' in yaml_output:
                yaml_output = yaml_output.split('```')[0]

            yaml_output = yaml_output.strip()

            return jsonify({'yaml': yaml_output})

    except urllib.error.URLError as e:
        return jsonify({'error': f'Ollama not available: {str(e)}. Make sure Ollama is running.'}), 500
    except Exception as e:
        return jsonify({'error': f'Error parsing description: {str(e)}'}), 500


def generate_template_code(form_spec, brand_theme, brand_name):
    """Generate HTML template code from form specification"""
    name = form_spec.get('name', 'Form')
    fields = form_spec.get('fields', [])

    # Get brand colors
    colors = brand_theme.get('colors', {})
    primary = colors.get('primary', '#667eea')
    background = colors.get('background', '#f5f5f5')
    text = colors.get('text', '#333')
    emoji = brand_theme.get('emoji', '📝')

    # Generate field HTML
    fields_html = []
    for field in fields:
        field_name = field.get('name', '')
        field_type = field.get('type', 'text')
        label = field.get('label', field_name.replace('_', ' ').title())
        required = field.get('required', False)

        req_attr = 'required' if required else ''
        req_mark = ' *' if required else ''

        fields_html.append(f'''        <label for="{field_name}">{label}{req_mark}</label>
        <input type="{field_type}" id="{field_name}" name="{field_name}" {req_attr}>
''')

    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: {background};
            color: {text};
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: {primary};
            margin-bottom: 20px;
            font-size: 2em;
        }}

        label {{
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: {text};
        }}

        input, textarea, select {{
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            font-size: 1em;
            margin-bottom: 20px;
        }}

        input:focus, textarea:focus, select:focus {{
            outline: none;
            border-color: {primary};
        }}

        button {{
            background: {primary};
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 6px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
        }}

        button:hover {{
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}

        .success {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}

        .error {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{emoji} {name}</h1>

        {{% with messages = get_flashed_messages(with_categories=true) %}}
            {{% if messages %}}
                {{% for category, message in messages %}}
                    <div class="{{{{ category }}}}">{{{{ message }}}}</div>
                {{% endfor %}}
            {{% endif %}}
        {{% endwith %}}

        <form method="POST">
{''.join(fields_html)}
            <button type="submit">{emoji} Submit</button>
        </form>
    </div>
</body>
</html>'''

    return template


def generate_route_code(form_spec):
    """Generate Flask route code from form specification"""
    route = form_spec.get('route', '/form')
    name = form_spec.get('name', 'Form')
    table = form_spec.get('table', 'form_data')
    fields = form_spec.get('fields', [])

    # Generate function name from route
    func_name = route.replace('/', '_').strip('_').replace('-', '_')

    # Generate template filename
    template_filename = f"{route.replace('/', '_').strip('_')}.html"

    # Generate field assignments
    field_assignments = []
    for field in fields:
        field_name = field.get('name', '')
        field_assignments.append(f"        {field_name} = request.form.get('{field_name}', '').strip()")

    # Generate INSERT statement
    field_names = [f['name'] for f in fields]
    placeholders = ', '.join(['?' for _ in field_names])
    columns = ', '.join(field_names)
    values = ', '.join(field_names)

    route_code = f'''@app.route('{route}', methods=['GET', 'POST'])
def {func_name}():
    """
    {name}
    Auto-generated by Soulfra Form Builder
    """
    if request.method == 'POST':
{chr(10).join(field_assignments)}

        # Save to database
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO {table} ({columns}) VALUES ({placeholders})',
            ({values})
        )
        conn.commit()
        conn.close()

        flash('✅ Successfully submitted!', 'success')
        return redirect('{route}')

    return render_template('{template_filename}')'''

    return route_code


def generate_schema_code(form_spec):
    """Generate database schema JSON from form specification"""
    table = form_spec.get('table', 'form_data')
    fields = form_spec.get('fields', [])

    columns = {
        'id': {
            'type': 'INTEGER',
            'primary_key': True,
            'autoincrement': True
        }
    }

    # Map field types to SQL types
    type_map = {
        'text': 'TEXT',
        'email': 'TEXT',
        'number': 'INTEGER',
        'date': 'DATE',
        'textarea': 'TEXT'
    }

    for field in fields:
        field_name = field.get('name', '')
        field_type = field.get('type', 'text')
        required = field.get('required', False)

        columns[field_name] = {
            'type': type_map.get(field_type, 'TEXT'),
            'required': required
        }

    # Add created_at timestamp
    columns['created_at'] = {
        'type': 'TIMESTAMP',
        'default': 'CURRENT_TIMESTAMP'
    }

    schema = {
        'columns': columns
    }

    import json
    return json.dumps(schema)


def generate_leaderboard_route(form_spec, route_path, brand_theme, brand_name):
    """Generate leaderboard route and template that queries reputation system"""
    game_name = form_spec.get('name', 'Game')
    table = form_spec.get('table', 'users')

    colors = brand_theme.get('colors', {})
    primary = colors.get('primary', '#667eea')
    background = colors.get('background', '#f5f5f5')
    text = colors.get('text', '#333')
    emoji = brand_theme.get('emoji', '🏆')

    # Generate template
    template_filename = f"{route_path.replace('/', '_').strip('_')}.html"
    template_path = f"templates/{template_filename}"

    template_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{emoji} {game_name} - Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: {background};
            color: {text};
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: {primary};
            margin-bottom: 30px;
            font-size: 2.5em;
            text-align: center;
        }}

        .leaderboard {{
            list-style: none;
        }}

        .player {{
            display: flex;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid {primary};
        }}

        .player.top-1 {{
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            border-left-color: #ffd700;
        }}

        .player.top-2 {{
            background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
            border-left-color: #c0c0c0;
        }}

        .player.top-3 {{
            background: linear-gradient(135deg, #cd7f32 0%, #e5a76d 100%);
            border-left-color: #cd7f32;
        }}

        .rank {{
            font-size: 1.5em;
            font-weight: bold;
            margin-right: 20px;
            min-width: 40px;
        }}

        .player-info {{
            flex: 1;
        }}

        .player-name {{
            font-weight: 600;
            font-size: 1.1em;
        }}

        .player-details {{
            font-size: 0.9em;
            color: #666;
            margin-top: 4px;
        }}

        .bits {{
            font-size: 1.3em;
            font-weight: bold;
            color: {primary};
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{emoji} {game_name} Leaderboard</h1>

        <ul class="leaderboard">
            {{% for player in players %}}
            <li class="player {{% if loop.index == 1 %}}top-1{{% elif loop.index == 2 %}}top-2{{% elif loop.index == 3 %}}top-3{{% endif %}}">
                <div class="rank">
                    {{% if loop.index == 1 %}}🥇{{% elif loop.index == 2 %}}🥈{{% elif loop.index == 3 %}}🥉{{% else %}}{{{{ loop.index }}}}{{% endif %}}
                </div>
                <div class="player-info">
                    <div class="player-name">{{{{ player.username }}}}</div>
                    <div class="player-details">
                        {{{{ player.contribution_count }}}} contributions
                    </div>
                </div>
                <div class="bits">{{{{ player.bits_earned }}}} bits</div>
            </li>
            {{% endfor %}}
        </ul>
    </div>
</body>
</html>'''

    # Generate route
    func_name = route_path.replace('/', '_').strip('_').replace('-', '_')
    route_code = f'''@app.route('{route_path}')
def {func_name}():
    """
    {game_name} Leaderboard
    Auto-generated by Soulfra Form Builder
    """
    # Query reputation system for top players
    conn = get_db_connection()
    players = conn.execute("""
        SELECT u.username, u.display_name, r.bits_earned, r.contribution_count
        FROM {table} u
        JOIN reputation r ON u.id = r.user_id
        WHERE r.contribution_count > 0
        ORDER BY r.bits_earned DESC
        LIMIT 50
    """).fetchall()
    conn.close()

    return render_template('{template_filename}', players=players)'''

    return {{
        'route': route_code,
        'template': template_code,
        'template_path': template_path
    }}


def generate_news_feed_route(form_spec, route_path, brand_theme, brand_name):
    """Generate news feed route and template"""
    game_name = form_spec.get('name', 'Game')

    colors = brand_theme.get('colors', {})
    primary = colors.get('primary', '#667eea')
    background = colors.get('background', '#f5f5f5')
    text = colors.get('text', '#333')
    emoji = brand_theme.get('emoji', '📰')

    template_filename = f"{route_path.replace('/', '_').strip('_')}.html"
    template_path = f"templates/{template_filename}"

    template_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{emoji} {game_name} - News</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: {background};
            color: {text};
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: {primary};
            margin-bottom: 30px;
            font-size: 2.5em;
        }}

        .post {{
            padding: 20px;
            margin-bottom: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid {primary};
        }}

        .post-title {{
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 10px;
            color: {text};
        }}

        .post-meta {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }}

        .post-content {{
            line-height: 1.6;
        }}

        .post-content a {{
            color: {primary};
            text-decoration: none;
        }}

        .post-content a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{emoji} {game_name} News</h1>

        {{% if posts %}}
            {{% for post in posts %}}
            <article class="post">
                <h2 class="post-title">{{{{ post.title }}}}</h2>
                <div class="post-meta">
                    By {{{{ post.author }}}} • {{{{ post.published_at }}}}
                </div>
                <div class="post-content">
                    {{{{ post.content|safe }}}}
                </div>
            </article>
            {{% endfor %}}
        {{% else %}}
            <p>No news posts yet. Check back soon!</p>
        {{% endif %}}
    </div>
</body>
</html>'''

    func_name = route_path.replace('/', '_').strip('_').replace('-', '_')
    route_code = f'''@app.route('{route_path}')
def {func_name}():
    """
    {game_name} News Feed
    Auto-generated by Soulfra Form Builder
    """
    # Query posts table for latest news
    conn = get_db_connection()
    posts = conn.execute("""
        SELECT p.title, p.content, p.published_at, u.username as author
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.published_at DESC
        LIMIT 20
    """).fetchall()
    conn.close()

    return render_template('{template_filename}', posts=posts)'''

    return {{
        'route': route_code,
        'template': template_code,
        'template_path': template_path
    }}


def generate_user_profile_route(form_spec, route_path, brand_theme, brand_name):
    """Generate user profile route and template"""
    game_name = form_spec.get('name', 'Game')
    table = form_spec.get('table', 'users')

    colors = brand_theme.get('colors', {})
    primary = colors.get('primary', '#667eea')
    background = colors.get('background', '#f5f5f5')
    text = colors.get('text', '#333')
    emoji = brand_theme.get('emoji', '👤')

    template_filename = f"{route_path.replace('/', '_').strip('_')}.html"
    template_path = f"templates/{template_filename}"

    template_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{emoji} {{{{ user.username }}}} - Profile</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: {background};
            color: {text};
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .profile-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid {primary};
        }}

        .username {{
            font-size: 2em;
            font-weight: bold;
            color: {primary};
            margin-bottom: 10px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid {primary};
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: {primary};
        }}

        .stat-label {{
            color: #666;
            margin-top: 8px;
        }}

        .info-section {{
            margin-top: 20px;
        }}

        .info-label {{
            font-weight: 600;
            color: #666;
            margin-bottom: 5px;
        }}

        .info-value {{
            font-size: 1.1em;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="profile-header">
            <div class="username">{emoji} {{{{ user.username }}}}</div>
            {{% if user.display_name %}}
                <div style="color: #666;">{{{{ user.display_name }}}}</div>
            {{% endif %}}
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{{{ reputation.bits_earned }}}}</div>
                <div class="stat-label">Bits Earned</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{{{ reputation.contribution_count }}}}</div>
                <div class="stat-label">Contributions</div>
            </div>
        </div>

        <div class="info-section">
            {{% for field_name, field_value in user_data.items() %}}
                {{% if field_value %}}
                <div>
                    <div class="info-label">{{{{ field_name.replace('_', ' ').title() }}}}</div>
                    <div class="info-value">{{{{ field_value }}}}</div>
                </div>
                {{% endif %}}
            {{% endfor %}}
        </div>
    </div>
</body>
</html>'''

    func_name = route_path.replace('/', '_').strip('_').replace('-', '_').replace('{', '').replace('}', '')
    route_code = f'''@app.route('{route_path}')
def {func_name}(username):
    """
    {game_name} User Profile
    Auto-generated by Soulfra Form Builder
    """
    conn = get_db_connection()

    # Get user data
    user = conn.execute('SELECT * FROM {table} WHERE username = ?', (username,)).fetchone()
    if not user:
        conn.close()
        return "User not found", 404

    # Get reputation data
    reputation = conn.execute('SELECT * FROM reputation WHERE user_id = ?', (user['id'],)).fetchone()
    if not reputation:
        reputation = {{'bits_earned': 0, 'contribution_count': 0}}

    conn.close()

    # Convert user to dict for display
    user_data = dict(user)

    return render_template('{template_filename}', user=user, reputation=reputation, user_data=user_data)'''

    return {{
        'route': route_code,
        'template': template_code,
        'template_path': template_path
    }}


@app.route('/admin/subscribers')
def admin_subscribers():
    """View all subscribers"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    from database import get_subscribers
    subscribers = get_subscribers()

    return render_template(
        'admin_subscribers.html',
        subscribers=subscribers,
        subscriber_count=len(subscribers)
    )


@app.route('/admin/subscribers/export')
def admin_subscribers_export():
    """Export subscribers as CSV"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    from database import get_subscribers
    subscribers = get_subscribers()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Email', 'Subscribed Date', 'Status'])

    # Write data
    for sub in subscribers:
        status = 'Active' if sub['active'] else 'Unsubscribed'
        writer.writerow([sub['email'], sub['subscribed_at'], status])

    # Create response
    csv_data = output.getvalue()
    output.close()

    filename = f"soulfra-subscribers-{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@app.route('/admin/subscribers/import', methods=['GET', 'POST'])
def admin_subscribers_import():
    """Import subscribers from CSV"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    if request.method == 'GET':
        return render_template('admin_import.html')

    # Handle POST - process CSV upload
    if 'csv_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin_subscribers_import'))

    file = request.files['csv_file']

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_subscribers_import'))

    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('admin_subscribers_import'))

    try:
        # Read CSV file
        csv_data = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))

        # Convert to list of dicts
        rows = []
        for row in csv_reader:
            # Support multiple CSV formats (Mailchimp, Substack, etc.)
            email_key = None
            for key in row.keys():
                if 'email' in key.lower():
                    email_key = key
                    break

            if email_key:
                rows.append({
                    'email': row[email_key],
                    'status': row.get('Status', row.get('status', 'active'))
                })

        if not rows:
            flash('No valid email addresses found in CSV', 'error')
            return redirect(url_for('admin_subscribers_import'))

        # Import using database function
        from database import import_subscribers_csv
        success, duplicates, errors = import_subscribers_csv(rows)

        # Show results
        flash(f'✅ Import complete: {success} added, {duplicates} duplicates, {errors} errors', 'success')
        return redirect(url_for('admin_subscribers'))

    except Exception as e:
        flash(f'Error importing CSV: {str(e)}', 'error')
        return redirect(url_for('admin_subscribers_import'))


@app.route('/admin/logout')
def admin_logout():
    """Logout from admin"""
    session.pop('is_admin', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/admin/post/new', methods=['GET', 'POST'])
def admin_post_new():
    """Create new post from web UI"""
    # Check admin auth
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        from database import get_db
        import re
        from datetime import datetime

        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not title or not content:
            flash('Title and content required', 'error')
            return render_template('admin_post_new.html', title=title, content=content)

        # Generate slug from title
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        # Check if slug exists
        db = get_db()
        existing = db.execute('SELECT id FROM posts WHERE slug = ?', (slug,)).fetchone()

        if existing:
            # Add timestamp to make unique
            slug = f"{slug}-{int(datetime.now().timestamp())}"

        # Insert post
        db.execute('''
            INSERT INTO posts (user_id, title, slug, content, published_at)
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (title, slug, content))

        db.commit()
        post_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.close()

        # Trigger AI auto-commenting
        try:
            from event_hooks import on_post_created
            on_post_created(post_id)
        except Exception as e:
            print(f"⚠️  AI auto-commenting failed: {e}")

        flash(f'Post "{title}" created successfully!', 'success')
        return redirect(url_for('post', slug=slug))

    return render_template('admin_post_new.html')


@app.route('/admin/import-url', methods=['GET', 'POST'])
def admin_import_url():
    """Import URL as blog post with procedural images"""
    # Check admin auth
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        from url_to_blog import url_to_blog_post
        from database import get_db

        url = request.form.get('url', '').strip()
        brand_slug = request.form.get('brand_slug', '').strip()

        if not url or not brand_slug:
            flash('URL and brand are required', 'error')
            return render_template('admin_import_url.html', url=url, brand_slug=brand_slug)

        # Validate brand exists
        db = get_db()
        brand = db.execute('SELECT * FROM brands WHERE slug = ?', (brand_slug,)).fetchone()
        db.close()

        if not brand:
            flash(f'Brand not found: {brand_slug}', 'error')
            return render_template('admin_import_url.html', url=url, brand_slug=brand_slug)

        try:
            # Import URL as blog post (includes auto-export)
            post_id = url_to_blog_post(
                url=url,
                brand_slug=brand_slug,
                author_id=session.get('user_id', 1)
            )

            if post_id:
                # Get post slug
                db = get_db()
                post = db.execute('SELECT slug FROM posts WHERE id = ?', (post_id,)).fetchone()
                db.close()

                flash(f'✅ Successfully imported URL as post! Static site exported to output/{brand_slug}/', 'success')
                return redirect(url_for('brand_post', brand_slug=brand_slug, post_slug=post['slug']))
            else:
                flash('Failed to import URL', 'error')
                return render_template('admin_import_url.html', url=url, brand_slug=brand_slug)

        except Exception as e:
            flash(f'Error importing URL: {e}', 'error')
            return render_template('admin_import_url.html', url=url, brand_slug=brand_slug)

    # GET request - show form with brand options
    from database import get_db
    db = get_db()
    brands = db.execute('SELECT slug, name FROM brands ORDER BY name').fetchall()
    db.close()

    return render_template('admin_import_url.html', brands=brands)


@app.route('/admin/brand/new', methods=['GET', 'POST'])
def admin_brand_new():
    """Create new brand"""
    # Check admin auth
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        from database import get_db
        import re

        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        tagline = request.form.get('tagline', '').strip()
        domain = request.form.get('domain', '').strip()
        category = request.form.get('category', '').strip()
        emoji = request.form.get('emoji', '').strip()
        color_primary = request.form.get('color_primary', '').strip() or '#FF6B35'
        color_secondary = request.form.get('color_secondary', '').strip() or '#F7931E'
        color_accent = request.form.get('color_accent', '').strip() or '#C1272D'

        if not name or not slug:
            flash('Name and slug are required', 'error')
            return render_template('admin_brand_new.html',
                name=name, slug=slug, tagline=tagline, domain=domain,
                category=category, emoji=emoji,
                color_primary=color_primary, color_secondary=color_secondary, color_accent=color_accent)

        # Validate slug format
        if not re.match(r'^[a-z0-9\-]+$', slug):
            flash('Slug must contain only lowercase letters, numbers, and hyphens', 'error')
            return render_template('admin_brand_new.html',
                name=name, slug=slug, tagline=tagline, domain=domain,
                category=category, emoji=emoji,
                color_primary=color_primary, color_secondary=color_secondary, color_accent=color_accent)

        db = get_db()

        # Check if slug already exists
        existing = db.execute('SELECT id FROM brands WHERE slug = ?', (slug,)).fetchone()
        if existing:
            flash(f'Brand slug "{slug}" already exists', 'error')
            db.close()
            return render_template('admin_brand_new.html',
                name=name, slug=slug, tagline=tagline, domain=domain,
                category=category, emoji=emoji,
                color_primary=color_primary, color_secondary=color_secondary, color_accent=color_accent)

        try:
            # Insert brand
            db.execute('''
                INSERT INTO brands (
                    name, slug, tagline, domain, category, emoji,
                    color_primary, color_secondary, color_accent,
                    brand_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'blog')
            ''', (name, slug, tagline, domain, category, emoji,
                  color_primary, color_secondary, color_accent))

            db.commit()
            brand_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            db.close()

            flash(f'✅ Brand "{name}" created successfully!', 'success')
            return redirect(url_for('brand_page', slug=slug))

        except Exception as e:
            flash(f'Error creating brand: {e}', 'error')
            db.rollback()
            db.close()
            return render_template('admin_brand_new.html',
                name=name, slug=slug, tagline=tagline, domain=domain,
                category=category, emoji=emoji,
                color_primary=color_primary, color_secondary=color_secondary, color_accent=color_accent)

    return render_template('admin_brand_new.html')


# ==================== SOURCE CODE TRANSPARENCY ROUTES ====================

@app.route('/reasoning')
def reasoning_dashboard():
    """Reasoning threads dashboard"""
    from database import get_db

    db = get_db()

    # Get all reasoning threads with post info
    threads = db.execute('''
        SELECT rt.*, p.title as post_title, p.slug as post_slug,
               COUNT(rs.id) as step_count
        FROM reasoning_threads rt
        JOIN posts p ON rt.post_id = p.id
        LEFT JOIN reasoning_steps rs ON rt.id = rs.thread_id
        GROUP BY rt.id
        ORDER BY rt.created_at DESC
    ''').fetchall()

    # Get stats
    stats = {
        'total_threads': len(threads),
        'total_steps': db.execute('SELECT COUNT(*) as count FROM reasoning_steps').fetchone()['count'],
        'active_threads': db.execute("SELECT COUNT(*) as count FROM reasoning_threads WHERE status = 'active'").fetchone()['count']
    }

    db.close()

    return render_template('reasoning.html', threads=threads, stats=stats)


@app.route('/status')
def status_dashboard():
    """Platform status dashboard - shows what's working"""
    from database import get_db
    import os

    db = get_db()

    # Database health
    try:
        db.execute('SELECT 1').fetchone()
        db_status = 'Connected'
        db_healthy = True
    except Exception as e:
        db_status = f'Error: {e}'
        db_healthy = False

    # Get table stats
    tables_info = []
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for table in tables:
        count = db.execute(f"SELECT COUNT(*) as count FROM {table['name']}").fetchone()['count']
        tables_info.append({'name': table['name'], 'count': count})

    # Platform stats
    stats = {
        'posts': db.execute('SELECT COUNT(*) as count FROM posts').fetchone()['count'],
        'comments': db.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count'],
        'users': db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
        'subscribers': db.execute('SELECT COUNT(*) as count FROM subscribers').fetchone()['count'],
        'feedback': db.execute('SELECT COUNT(*) as count FROM feedback').fetchone()['count'],
        'reasoning_threads': db.execute('SELECT COUNT(*) as count FROM reasoning_threads').fetchone()['count'],
        'reasoning_steps': db.execute('SELECT COUNT(*) as count FROM reasoning_steps').fetchone()['count'],
        'qr_codes': db.execute('SELECT COUNT(*) as count FROM qr_codes').fetchone()['count'],
        'qr_scans': db.execute('SELECT COUNT(*) as count FROM qr_scans').fetchone()['count']
    }

    # Recent activity
    recent_posts = db.execute('SELECT id, title, published_at FROM posts ORDER BY published_at DESC LIMIT 5').fetchall()
    recent_comments = db.execute('''
        SELECT c.id, c.content, u.username, c.created_at
        FROM comments c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC LIMIT 5
    ''').fetchall()
    recent_feedback = db.execute('SELECT id, component, message, created_at FROM feedback ORDER BY created_at DESC LIMIT 5').fetchall()

    # Get ML stats
    try:
        ml_models = db.execute('SELECT COUNT(*) as count FROM ml_models').fetchone()['count']
    except:
        ml_models = 0

    # Routes inventory (manually maintained for now)
    routes = [
        {'path': '/', 'name': 'Homepage', 'status': 'working', 'has_data': stats['posts'] > 0},
        {'path': '/post/<slug>', 'name': 'Post View', 'status': 'working', 'has_data': True},
        {'path': '/souls', 'name': 'Soul Browser', 'status': 'working', 'has_data': stats['users'] > 0},
        {'path': '/feedback', 'name': 'Public Feedback', 'status': 'working', 'has_data': stats['feedback'] > 0},
        {'path': '/reasoning', 'name': 'Reasoning Dashboard', 'status': 'working', 'has_data': stats['reasoning_threads'] > 0},
        {'path': '/ml', 'name': 'ML Dashboard', 'status': 'working', 'has_data': ml_models > 0},
        {'path': '/admin', 'name': 'Admin Dashboard', 'status': 'working', 'has_data': True},
        {'path': '/admin/automation', 'name': 'Automation Panel', 'status': 'working', 'has_data': True},
        {'path': '/status', 'name': 'Status Dashboard', 'status': 'working', 'has_data': True},
        {'path': '/api/*', 'name': 'API Endpoints', 'status': 'working', 'has_data': True},
        {'path': '/code', 'name': 'Code Browser', 'status': 'working', 'has_data': True}
    ]

    # API endpoints status
    api_endpoints = [
        {'method': 'GET', 'path': '/api/health', 'status': 'working'},
        {'method': 'GET', 'path': '/api/posts', 'status': 'working'},
        {'method': 'GET', 'path': '/api/posts/{id}', 'status': 'working'},
        {'method': 'GET', 'path': '/api/reasoning/threads', 'status': 'working'},
        {'method': 'GET', 'path': '/api/reasoning/threads/{id}', 'status': 'working'},
        {'method': 'POST', 'path': '/api/feedback', 'status': 'working'}
    ]

    db.close()

    return render_template(
        'status.html',
        db_status=db_status,
        db_healthy=db_healthy,
        tables=tables_info,
        stats=stats,
        routes=routes,
        api_endpoints=api_endpoints,
        recent_posts=recent_posts,
        recent_comments=recent_comments,
        recent_feedback=recent_feedback,
        db_file_size=os.path.getsize('soulfra.db') / 1024  # KB
    )


@app.route('/code')
def code_browser():
    """Browse source code files (transparency by design)"""
    # Get all Python files
    import glob

    files = []

    # Root Python files
    for f in glob.glob('*.py'):
        files.append({
            'name': f,
            'path': f,
            'type': 'python',
            'category': 'root'
        })

    # Templates
    for f in glob.glob('templates/*.html'):
        files.append({
            'name': f.replace('templates/', ''),
            'path': f,
            'type': 'html',
            'category': 'templates'
        })

    # Tests
    for f in glob.glob('tests/*.py'):
        files.append({
            'name': f.replace('tests/', ''),
            'path': f,
            'type': 'python',
            'category': 'tests'
        })

    # Docs
    for f in glob.glob('docs/**/*.md', recursive=True):
        files.append({
            'name': f.replace('docs/', ''),
            'path': f,
            'type': 'markdown',
            'category': 'docs'
        })

    # Sort by category then name
    files.sort(key=lambda x: (x['category'], x['name']))

    return render_template('code_browser.html', files=files)


@app.route('/code/<path:filepath>')
def view_code_file(filepath):
    """View a specific source file with syntax highlighting"""
    import os

    # Security: Only allow viewing files in the project directory
    allowed_extensions = ['.py', '.html', '.css', '.js', '.md', '.txt', '.toml', '.sql', '.yaml', '.yml', '.json']

    # Check extension
    _, ext = os.path.splitext(filepath)
    if ext not in allowed_extensions:
        flash('File type not allowed for viewing', 'error')
        return redirect(url_for('code_browser'))

    # Check file exists
    if not os.path.exists(filepath):
        flash('File not found', 'error')
        return redirect(url_for('code_browser'))

    # Read file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        flash(f'Error reading file: {e}', 'error')
        return redirect(url_for('code_browser'))

    # Determine language for syntax highlighting
    lang_map = {
        '.py': 'python',
        '.html': 'html',
        '.css': 'css',
        '.js': 'javascript',
        '.md': 'markdown',
        '.sql': 'sql',
        '.toml': 'toml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json'
    }

    language = lang_map.get(ext, 'text')

    return render_template('code_viewer.html',
                          filepath=filepath,
                          content=content,
                          language=language,
                          filename=os.path.basename(filepath))


# =============================================================================
# ML DASHBOARD
# =============================================================================

@app.route('/ml')
def ml_dashboard():
    """ML dashboard - show what the system learned"""
    from database import get_db

    db = get_db()

    # Check if ML tables exist
    try:
        models = db.execute('''
            SELECT id, model_type, trained_on, accuracy, created_at
            FROM ml_models
            ORDER BY created_at DESC
        ''').fetchall()
    except:
        # Tables don't exist yet
        models = []

    # Get predictions
    try:
        predictions = db.execute('''
            SELECT p.*, m.model_type
            FROM predictions p
            JOIN ml_models m ON p.model_id = m.id
            ORDER BY p.created_at DESC
            LIMIT 20
        ''').fetchall()
    except:
        predictions = []

    # Get training data stats
    posts_count = db.execute('SELECT COUNT(*) as count FROM posts').fetchone()['count']
    comments_count = db.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count']

    # Get recent feedback for feature prediction
    recent_feedback = db.execute('''
        SELECT component, message, created_at
        FROM feedback
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()

    db.close()

    return render_template('ml_dashboard.html',
                          models=models,
                          predictions=predictions,
                          posts_count=posts_count,
                          comments_count=comments_count,
                          recent_feedback=recent_feedback)


@app.route('/ml/train', methods=['POST'])
def ml_train():
    """Train ML model on posts and comments"""
    from simple_ml import train_feature_classifier

    try:
        model_id = train_feature_classifier()
        flash(f'✅ Model trained successfully! Model ID: {model_id}', 'success')
    except Exception as e:
        flash(f'❌ Training failed: {e}', 'error')

    return redirect(url_for('ml_dashboard'))


@app.route('/ml/predict', methods=['POST'])
def ml_predict():
    """Make prediction with trained model"""
    from simple_ml import predict_feature_type, load_model
    from database import get_db

    text = request.form.get('text', '')
    model_id = request.form.get('model_id', type=int)

    if not text or not model_id:
        flash('❌ Please provide text and select a model', 'error')
        return redirect(url_for('ml_dashboard'))

    try:
        prediction, confidence = predict_feature_type(text, model_id)
        flash(f'✅ Prediction: {prediction} (confidence: {confidence:.2%})', 'success')
    except Exception as e:
        flash(f'❌ Prediction failed: {e}', 'error')

    return redirect(url_for('ml_dashboard'))


@app.route('/i/<hash>')
def serve_image(hash):
    """Serve image from database (decentralized image hosting)"""
    db = get_db()

    # Get image by hash
    img = db.execute('SELECT data, mime_type FROM images WHERE hash = ?', (hash,)).fetchone()
    db.close()

    if not img:
        # Return 404
        return "Image not found", 404

    # Serve image bytes with correct mime type
    return Response(img['data'], mimetype=img['mime_type'])


@app.route('/showcase')
def showcase():
    """Soul showcase gallery - visual proof the system works"""
    import os

    # Check if showcase directory exists
    showcase_dir = 'showcase'
    if not os.path.exists(showcase_dir):
        flash('Showcase not generated yet. Run: python3 soul_showcase.py', 'error')
        return redirect(url_for('index'))

    # Serve the generated HTML gallery
    gallery_path = os.path.join(showcase_dir, 'gallery.html')
    if os.path.exists(gallery_path):
        with open(gallery_path, 'r') as f:
            html_content = f.read()
        return html_content
    else:
        flash('Gallery HTML not found. Run: python3 soul_showcase.py', 'error')
        return redirect(url_for('index'))


@app.route('/tiers')
def tiers_showcase():
    """Tier system showcase - Binary → Images → Anime (pure stdlib)"""
    import os

    # Get all generated images
    static_dir = os.path.join(os.path.dirname(__file__), 'static', 'generated')

    test_images = []
    brand_logos = []

    if os.path.exists(static_dir):
        for filename in sorted(os.listdir(static_dir)):
            if filename.endswith('.gif'):
                filepath = f'/static/generated/{filename}'
                file_size = os.path.getsize(os.path.join(static_dir, filename))

                if filename.startswith('test_'):
                    test_images.append({
                        'name': filename.replace('test_', '').replace('.gif', '').replace('_', ' ').title(),
                        'path': filepath,
                        'size': f'{file_size:,} bytes'
                    })
                elif '_logo.gif' in filename:
                    brand_name = filename.replace('_logo.gif', '')
                    brand_logos.append({
                        'name': brand_name.title(),
                        'path': filepath,
                        'size': f'{file_size:,} bytes'
                    })

    # Render template
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tier System: Binary → Images → Anime</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            font-size: 1.2rem;
            color: #888;
            margin-bottom: 3rem;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}

        .stat {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: #888;
            margin-top: 0.5rem;
        }}

        h2 {{
            font-size: 2rem;
            margin: 3rem 0 1.5rem;
            color: #fff;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}

        .image-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .image-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            border-color: rgba(102, 126, 234, 0.5);
        }}

        .image-card img {{
            width: 100%;
            height: 200px;
            object-fit: contain;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            margin-bottom: 1rem;
        }}

        .image-card h3 {{
            font-size: 1.2rem;
            color: #fff;
            margin-bottom: 0.5rem;
        }}

        .image-card .size {{
            font-size: 0.9rem;
            color: #888;
        }}

        .nav {{
            margin-bottom: 2rem;
        }}

        .nav a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}

        .nav a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/">← Back to Newsletter</a>
        </div>

        <h1>🎨 Tier System Showcase</h1>
        <p class="subtitle">Binary → Text → Images → Animation | 100% Pure Python Stdlib</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">3,620</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat">
                <div class="stat-value">0</div>
                <div class="stat-label">Dependencies</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(test_images) + len(brand_logos)}</div>
                <div class="stat-label">Generated Images</div>
            </div>
            <div class="stat">
                <div class="stat-value">4</div>
                <div class="stat-label">Brand Identities</div>
            </div>
        </div>

        <h2>📸 Test Images (GIF Encoder)</h2>
        <div class="grid">
'''

    for img in test_images:
        html_content += f'''            <div class="image-card">
                <img src="{img['path']}" alt="{img['name']}">
                <h3>{img['name']}</h3>
                <div class="size">{img['size']}</div>
            </div>
'''

    html_content += '''        </div>

        <h2>🎭 Brand Logos (Pure Stdlib)</h2>
        <div class="grid">
'''

    for logo in brand_logos:
        html_content += f'''            <div class="image-card">
                <img src="{logo['path']}" alt="{logo['name']}">
                <h3>{logo['name']}</h3>
                <div class="size">{logo['size']}</div>
            </div>
'''

    html_content += '''        </div>

        <h2>🔧 Technical Details</h2>
        <div class="stat" style="text-align: left;">
            <p><strong>Tier 1: Binary</strong> (2,400 lines)</p>
            <p style="margin-bottom: 1rem; color: #888;">Bitwise operations, byte manipulation, foundation for all encoding</p>

            <p><strong>Tier 2: Text</strong> (300 lines)</p>
            <p style="margin-bottom: 1rem; color: #888;">Markdown to HTML converter, string processing, escaping</p>

            <p><strong>Tier 3: Raster Graphics</strong> (600 lines)</p>
            <p style="margin-bottom: 1rem; color: #888;">BMP: Direct pixel framebuffer | GIF: LZW compression, color quantization</p>

            <p><strong>Tier 4: Animation</strong> (320 lines)</p>
            <p style="color: #888;">GIF supports multi-frame | Next: BMP sequence to GIF converter</p>
        </div>

        <div style="margin-top: 3rem; text-align: center; color: #888;">
            <p>View the tier progression above - from binary data to animated GIFs, all generated using pure Python stdlib!</p>
        </div>
    </div>
</body>
</html>
'''

    return html_content


@app.route('/proof')
def proof_viewer():
    """
    Cryptographic Proof Viewer - Interactive verification of tier system

    Shows:
    - All 4 tiers with verification status
    - Dependency scan results
    - System hash
    - HMAC-SHA256 signature
    - Interactive binary viewer
    """
    import json
    import os
    from datetime import datetime

    # Load proof.json
    proof_file = 'proof.json'

    if not os.path.exists(proof_file):
        # Generate proof on-the-fly if it doesn't exist
        from generate_proof import generate_proof
        proof_data = generate_proof(verbose=False)

        # Save it
        with open(proof_file, 'w') as f:
            json.dump(proof_data, f, separators=(',', ':'))
    else:
        # Load existing proof
        with open(proof_file, 'r') as f:
            proof_data = json.load(f)

    # Calculate proof age
    if 'timestamp' in proof_data:
        proof_time = datetime.fromtimestamp(proof_data['timestamp'])
        age = datetime.now() - proof_time
        age_str = f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m ago"
    else:
        age_str = "unknown"

    # Prepare data for template
    context = {
        'proof': proof_data,
        'proof_age': age_str,
        'proof_exists': True
    }

    return render_template('proof.html', **context)


@app.route('/legitimacy')
def legitimacy_viewer():
    """
    Why This Works - Offline-First Legitimacy Documentation

    Renders LEGITIMACY.md as HTML, proving that Soulfra's architecture
    (pure stdlib, offline-first, zero dependencies) is how real production
    systems work (SQLite, Linux, Git, etc.)
    """
    import os

    # Read LEGITIMACY.md
    legitimacy_file = 'LEGITIMACY.md'

    if not os.path.exists(legitimacy_file):
        return "LEGITIMACY.md not found", 404

    with open(legitimacy_file, 'r') as f:
        content = f.read()

    # Convert markdown to basic HTML (simple approach - just wrap in <pre>)
    # For proper markdown rendering, could use markdown2 but that's external dep
    # So we'll do a simple conversion

    # Basic markdown to HTML conversion (stdlib only)
    html_content = content

    # Headers
    import re
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)

    # Code blocks
    html_content = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code>\2</code></pre>', html_content, flags=re.DOTALL)

    # Inline code
    html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)

    # Bold
    html_content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html_content)

    # Links
    html_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html_content)

    # Paragraphs
    html_content = re.sub(r'\n\n', '</p><p>', html_content)
    html_content = '<p>' + html_content + '</p>'

    # Wrap in HTML document
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Why This Works - Soulfra</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.8;
            padding: 2rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: rgba(26, 26, 46, 0.8);
            padding: 3rem;
            border-radius: 8px;
            border: 1px solid #333;
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        h2 {{
            font-size: 1.8rem;
            color: #667eea;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
        }}

        h3 {{
            font-size: 1.3rem;
            color: #764ba2;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }}

        p {{
            margin-bottom: 1rem;
        }}

        code {{
            background: rgba(102, 126, 234, 0.1);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
            font-size: 0.9em;
            color: #667eea;
        }}

        pre {{
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
        }}

        pre code {{
            background: none;
            padding: 0;
            color: #e0e0e0;
        }}

        a {{
            color: #667eea;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        strong {{
            color: #764ba2;
            font-weight: 600;
        }}

        table {{
            width: 100%;
            margin: 1.5rem 0;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 0.75rem;
            border: 1px solid #333;
            text-align: left;
        }}

        th {{
            background: rgba(102, 126, 234, 0.2);
            color: #667eea;
            font-weight: 600;
        }}

        .nav {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #333;
        }}

        .nav a {{
            margin: 0 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}

        <div class="nav">
            <a href="/">← Back to Home</a>
            <a href="/proof">View Proof</a>
            <a href="/tiers">Tier System</a>
        </div>
    </div>
</body>
</html>'''

    return full_html


@app.route('/playground')
def playground():
    """
    Interactive Playground - Test All Features

    Unified interface for trying out:
    - Chat with Ollama (live)
    - Neural network training
    - Brand wordmap explorer
    - API testing
    - ML predictions
    """
    # Get available brands for wordmap explorer
    db = get_db()
    brands = db.execute('SELECT slug, name FROM brands ORDER BY name').fetchall()
    db.close()

    return render_template('playground.html', brands=brands)


@app.route('/docs')
# ==============================================================================
# AI FRONTEND - Integrated Ollama + Neural Networks
# ==============================================================================

@app.route('/ai-frontend')
def ai_frontend():
    """
    AI Frontend - Single interface for Ollama + Neural Networks + Tracing

    NO Jinja2 - Pure Python f-strings!
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Frontend - Soulfra</title>
    <style>
        body {{ font-family: monospace; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .query-form {{ margin: 20px 0; }}
        textarea {{ width: 100%; height: 150px; padding: 10px; font-family: monospace; border: 2px solid #ddd; border-radius: 4px; }}
        select, button {{ padding: 10px 20px; margin: 10px 5px 0 0; font-size: 16px; border: none; border-radius: 4px; cursor: pointer; }}
        select {{ background: #fff; border: 2px solid #ddd; }}
        button {{ background: #4CAF50; color: white; font-weight: bold; }}
        button:hover {{ background: #45a049; }}
        .info {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
        .endpoints {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
        .endpoint {{ background: #f9f9f9; padding: 15px; border-radius: 4px; border-left: 3px solid #4CAF50; }}
        .endpoint h3 {{ margin: 0 0 10px 0; color: #4CAF50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Frontend</h1>

        <div class="info">
            <strong>What is this?</strong><br>
            One interface for ALL AI: Ollama (port 11434) + Our Neural Networks + Full Tracing<br>
            Everything logged to database with complete transparency!
        </div>

        <form class="query-form" action="/api/ai-query" method="post">
            <h2>Query AI</h2>
            <textarea name="query" placeholder="Enter your question or problem here..."></textarea>

            <div>
                <label><strong>Model:</strong></label><br>
                <select name="model">
                    <optgroup label="Our Neural Networks (Fast, Offline)">
                        <option value="neural-classify">neural-classify (Classification)</option>
                        <option value="calriven_technical_classifier">calriven - Technical</option>
                        <option value="deathtodata_privacy_classifier">deathtodata - Privacy</option>
                        <option value="theauditor_validation_classifier">theauditor - Validation</option>
                    </optgroup>
                    <optgroup label="Ollama (Text Generation)">
                        <option value="ollama-llama2">ollama-llama2 (Recommended)</option>
                        <option value="ollama-mistral">ollama-mistral</option>
                        <option value="ollama-phi">ollama-phi (Fast)</option>
                    </optgroup>
                </select>

                <button type="submit">Submit Query</button>
            </div>
        </form>

        <div class="endpoints">
            <div class="endpoint">
                <h3>📊 Analytics</h3>
                <p><a href="/analytics">View AI Analytics Dashboard</a></p>
                <small>Usage stats, performance metrics, graphs</small>
            </div>

            <div class="endpoint">
                <h3>🔍 Recent Traces</h3>
                <p><a href="/traces">View All Traces</a></p>
                <small>See complete processing traces</small>
            </div>

            <div class="endpoint">
                <h3>📡 Neural Proxy Status</h3>
                <p>Ollama: <span id="ollama-status">Checking...</span></p>
                <small>Port 11434</small>
            </div>

            <div class="endpoint">
                <h3>🗄️ Database Stats</h3>
                <p id="db-stats">Loading...</p>
                <small>Requests logged</small>
            </div>
        </div>

        <script>
            // Check Ollama status
            fetch('http://localhost:11434/api/tags')
                .then(r => r.ok ? '🟢 Connected' : '🔴 Not Running')
                .catch(() => '🔴 Not Running')
                .then(status => document.getElementById('ollama-status').innerText = status);

            // Get database stats
            fetch('/api/ai-stats')
                .then(r => r.json())
                .then(data => document.getElementById('db-stats').innerText = `${{data.total_requests || 0}} requests`)
                .catch(() => document.getElementById('db-stats').innerText = 'Error loading');
        </script>
    </div>
</body>
</html>"""


@app.route('/api/ai-query', methods=['POST'])
def ai_query_endpoint():
    """Route AI queries to appropriate backend with full tracing"""
    from story_pipeline_tracer import process_story_with_tracing
    from neural_proxy import classify_with_neural_network, generate_with_ollama

    query = request.form.get('query', '')
    model = request.form.get('model', 'neural-classify')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # Process with full tracing
        result = process_story_with_tracing(query)

        return jsonify({
            'success': True,
            'query': query,
            'model': model,
            'response': result['response'],
            'classification': result['classification'],
            'trace_id': result['trace_id'],
            'duration_ms': result['total_duration_ms'],
            'trace_url': f"/trace/{result['trace_id']}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/trace/<trace_id>')
def show_trace(trace_id):
    """Show visual trace of AI processing"""
    from story_pipeline_tracer import get_trace_by_id

    trace = get_trace_by_id(trace_id)

    if not trace:
        return f"<h1>Trace not found: {trace_id}</h1>", 404

    # Build steps HTML
    # Classification colors and icons
    classification = trace.get('classification', 'general')
    classification_colors = {
        'technical': {'color': '#2196F3', 'emoji': '💻', 'bg': '#e3f2fd'},
        'privacy': {'color': '#f44336', 'emoji': '🔒', 'bg': '#ffebee'},
        'validation': {'color': '#4CAF50', 'emoji': '✅', 'bg': '#e8f5e9'},
        'general': {'color': '#9E9E9E', 'emoji': '💬', 'bg': '#f5f5f5'}
    }
    class_info = classification_colors.get(classification, classification_colors['general'])

    # Step colors
    step_colors = {
        'Receive Story': '#4CAF50',
        'Neural Classification': '#2196F3',
        'Template Selection': '#9C27B0',
        'Response Generation': '#FF9800',
        'Database Logging': '#607D8B'
    }

    steps_html = ""
    for step in trace.get('steps', []):
        step_name = step['step_name']
        step_color = step_colors.get(step_name, '#4CAF50')

        # Step icons
        step_icons = {
            'Receive Story': '📥',
            'Neural Classification': '🧠',
            'Template Selection': '📋',
            'Response Generation': '✨',
            'Database Logging': '💾'
        }
        step_icon = step_icons.get(step_name, '•')

        steps_html += f"""
        <div class="step" style="border-left-color: {step_color};">
            <div class="step-header">
                <strong>{step_icon} Step {step['step_number']}: {step['step_name']}</strong>
                <span class="duration" style="color: {step_color};">{step['duration_ms']}ms</span>
            </div>
            <div class="step-description">{step['description']}</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Trace: {trace_id}</title>
    <style>
        body {{ font-family: monospace; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid {class_info['color']}; padding-bottom: 10px; }}
        .trace-info {{ background: {class_info['bg']}; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid {class_info['color']}; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; background: {class_info['color']}; color: white; font-size: 14px; font-weight: bold; }}
        .step {{ background: #fff; border-left: 4px solid #4CAF50; padding: 15px; margin: 10px 0; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .step:hover {{ transform: translateX(4px); }}
        .step-header {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
        .duration {{ color: #666; font-size: 14px; font-weight: bold; }}
        .step-description {{ color: #555; }}
        .response {{ background: #e3f2fd; padding: 20px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #2196F3; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{class_info['emoji']} Trace: {trace_id[:16]}...</h1>

        <div class="trace-info">
            <strong>Classification:</strong> <span class="badge">{classification.upper()}</span> ({trace.get('confidence', 0):.0%} confidence)<br><br>
            <strong>Total Duration:</strong> {trace.get('total_duration_ms', 0)} ms<br>
            <strong>Created:</strong> {trace.get('created_at', 'N/A')}
        </div>

        <h2>🔄 Processing Steps</h2>
        {steps_html}

        <div class="response">
            <h3>📝 Final Response:</h3>
            <div>{trace.get('response_text', 'No response')}</div>
        </div>

        <p><a href="/ai-frontend">← Back to AI Frontend</a> | <a href="/traces">View All Traces</a></p>
    </div>
</body>
</html>"""


@app.route('/traces')
def list_traces():
    """List all traces"""
    import sqlite3

    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT trace_id, classification, confidence, total_duration_ms, created_at
        FROM pipeline_traces
        ORDER BY created_at DESC
        LIMIT 50
    ''')

    traces = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Classification colors and emojis
    classification_styles = {
        'technical': {'color': '#2196F3', 'emoji': '💻'},
        'privacy': {'color': '#f44336', 'emoji': '🔒'},
        'validation': {'color': '#4CAF50', 'emoji': '✅'},
        'general': {'color': '#9E9E9E', 'emoji': '💬'}
    }

    traces_html = ""
    for trace in traces:
        classification = trace['classification']
        style = classification_styles.get(classification, classification_styles['general'])

        traces_html += f"""
        <tr>
            <td><a href="/trace/{trace['trace_id']}">{trace['trace_id'][:16]}...</a></td>
            <td><span class="badge" style="background: {style['color']};">{style['emoji']} {classification.upper()}</span></td>
            <td>{trace.get('confidence', 0):.0%}</td>
            <td>{trace['total_duration_ms']} ms</td>
            <td>{trace['created_at']}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>All Traces</title>
    <style>
        body {{ font-family: monospace; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f9f9f9; }}
        a {{ color: #2196F3; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; color: white; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 All Traces ({len(traces)} total)</h1>
        <p><a href="/ai-frontend">← Back to AI Frontend</a></p>

        <table>
            <thead>
                <tr>
                    <th>Trace ID</th>
                    <th>Classification</th>
                    <th>Confidence</th>
                    <th>Duration</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                {traces_html if traces_html else '<tr><td colspan="5">No traces yet</td></tr>'}
            </tbody>
        </table>
    </div>
</body>
</html>"""


@app.route('/api/ai-stats')
def ai_stats():
    """Get AI statistics for dashboard"""
    import sqlite3

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT COUNT(*) FROM pipeline_traces')
        total_requests = cursor.fetchone()[0]
    except:
        total_requests = 0

    conn.close()

    return jsonify({
        'total_requests': total_requests,
        'ollama_available': True  # Would check Ollama in production
    })


@app.route('/analytics')
def analytics_dashboard():
    """Analytics dashboard with graphs"""
    from ai_analytics import get_total_requests, get_requests_by_model, get_average_latency

    total = get_total_requests()
    by_model = get_requests_by_model()
    latencies = get_average_latency()

    models_html = ""
    for model, count in by_model.items():
        percentage = (count / total * 100) if total > 0 else 0
        models_html += f"<li><strong>{model}:</strong> {count} requests ({percentage:.1f}%)</li>"

    latency_html = ""
    for model, latency in latencies.items():
        latency_html += f"<li><strong>{model}:</strong> {latency:.2f} ms</li>"

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Analytics</title>
    <style>
        body {{ font-family: monospace; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .metric {{ background: #f9f9f9; padding: 20px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
        .metric h2 {{ margin: 0 0 15px 0; color: #4CAF50; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 AI Analytics Dashboard</h1>
        <p><a href="/ai-frontend">← Back to AI Frontend</a></p>

        <div class="metric">
            <h2>Total Requests</h2>
            <p style="font-size: 48px; margin: 0; color: #4CAF50;">{total}</p>
        </div>

        <div class="metric">
            <h2>Requests by Model</h2>
            <ul>{models_html if models_html else '<li>No data yet</li>'}</ul>
        </div>

        <div class="metric">
            <h2>Average Latency</h2>
            <ul>{latency_html if latency_html else '<li>No data yet</li>'}</ul>
        </div>

        <p><a href="/analytics/export">Export HTML Report</a></p>
    </div>
</body>
</html>"""


def api_docs():
    """
    API Documentation - Interactive Documentation for All Endpoints

    Comprehensive, categorized API documentation with example requests/responses
    """
    # Organize all API routes by category
    api_routes = {
        'Content & Posts': [
            {'method': 'GET', 'path': '/api/posts', 'desc': 'Get all blog posts (JSON)', 'example_response': '{"posts": [...]}'},
            {'method': 'GET', 'path': '/api/posts/<id>', 'desc': 'Get single post by ID', 'example_response': '{"id": 1, "title": "..."}'},
            {'method': 'GET', 'path': '/api/health', 'desc': 'Server health check', 'example_response': '{"status": "ok"}'},
        ],
        'AI & Machine Learning': [
            {'method': 'POST', 'path': '/api/ollama/comment', 'desc': 'Get AI feedback on a post', 'example_body': '{"post_id": 1, "auto_post": false}', 'example_response': '{"success": true, "comments": [...]}'},
            {'method': 'GET', 'path': '/api/reasoning/threads', 'desc': 'Get all AI reasoning threads', 'example_response': '{"threads": [...]}'},
            {'method': 'GET', 'path': '/api/reasoning/threads/<id>', 'desc': 'Get specific reasoning thread', 'example_response': '{"thread": {...}}'},
            {'method': 'POST', 'path': '/api/website/predict/type', 'desc': 'Predict website type from content', 'example_body': '{"content": "..."}'},
            {'method': 'POST', 'path': '/api/website/predict/method', 'desc': 'Predict HTTP method for route', 'example_body': '{"route_name": "..."}'},
            {'method': 'POST', 'path': '/api/website/predict/parameters', 'desc': 'Predict route parameters', 'example_body': '{"route_name": "..."}'},
        ],
        'Brand & Voice': [
            {'method': 'GET', 'path': '/api/brand/wordmap/<slug>', 'desc': 'Get brand vocabulary map', 'example_response': '{"vocabulary": [...]}'},
            {'method': 'POST', 'path': '/api/brand/predict', 'desc': 'Predict brand from text', 'example_body': '{"text": "..."}'},
            {'method': 'POST', 'path': '/api/brand/consistency', 'desc': 'Check brand voice consistency', 'example_body': '{"brand": "...", "text": "..."}'},
            {'method': 'POST', 'path': '/api/brand/generate', 'desc': 'Generate text in brand voice', 'example_body': '{"brand": "...", "prompt": "..."}'},
            {'method': 'POST', 'path': '/api/brand/emoji/suggest', 'desc': 'Suggest emojis for brand', 'example_body': '{"brand": "...", "context": "..."}'},
            {'method': 'POST', 'path': '/api/brand/voice/compare', 'desc': 'Compare voice similarity', 'example_body': '{"text1": "...", "text2": "..."}'},
            {'method': 'GET', 'path': '/api/brand/status', 'desc': 'Get brand system status', 'example_response': '{"brands": [...]}'},
        ],
        'Website & Structure': [
            {'method': 'GET', 'path': '/api/website/missing-routes', 'desc': 'Find missing API routes', 'example_response': '{"missing": [...]}'},
            {'method': 'GET', 'path': '/api/website/structure', 'desc': 'Get full website structure', 'example_response': '{"routes": [...]}'},
        ],
        'Feedback & Interaction': [
            {'method': 'POST', 'path': '/api/feedback', 'desc': 'Submit user feedback', 'example_body': '{"message": "..."}'},
        ],
    }

    return render_template('api_docs.html', api_routes=api_routes)


# ==============================================================================
# BRAND COMPETITION & CONTRIBUTION VALIDATION
# ==============================================================================

@app.route('/api/validate-contribution', methods=['POST'])
def validate_contribution_endpoint():
    """
    Real-time contribution validation API

    Returns on-brand score, estimated tokens, and feedback
    """
    from contribution_validator import validate_contribution

    data = request.get_json()
    text = data.get('text', '')
    brand_id = data.get('brand_id')

    if not text or not brand_id:
        return jsonify({'error': 'Missing text or brand_id'}), 400

    result = validate_contribution(text, int(brand_id))

    return jsonify(result)


@app.route('/brand-arena')
def brand_arena():
    """
    Brand Competition Leaderboard

    Shows:
    - Territory scores (competitive rankings)
    - Top contributors per brand
    - Soul token distribution
    - Live competition status
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get brands with territory scores
    cursor.execute('''
        SELECT
            b.id,
            b.name,
            b.slug,
            b.personality,
            bt.territory_score,
            bt.total_engagement,
            bt.active_contributors,
            bt.total_tokens_distributed,
            bt.rank
        FROM brands b
        LEFT JOIN brand_territory bt ON b.id = bt.brand_id
        WHERE b.id IN (4, 5, 6)
        ORDER BY bt.territory_score DESC
    ''')

    brands = [dict(row) for row in cursor.fetchall()]

    # Get top contributors for each brand
    for brand in brands:
        cursor.execute('''
            SELECT
                u.username,
                ubl.soul_tokens,
                ubl.contribution_count,
                ubl.steering_power
            FROM user_brand_loyalty ubl
            JOIN users u ON ubl.user_id = u.id
            WHERE ubl.brand_id = ?
            ORDER BY ubl.soul_tokens DESC
            LIMIT 5
        ''', (brand['id'],))

        brand['top_contributors'] = [dict(row) for row in cursor.fetchall()]

    # Brand colors and emojis
    brand_styles = {
        4: {'color': '#2196F3', 'emoji': '💻', 'name': 'CalRiven'},  # Technical
        5: {'color': '#f44336', 'emoji': '🔒', 'name': 'Privacy Guard'},  # Privacy
        6: {'color': '#4CAF50', 'emoji': '✅', 'name': 'The Auditor'}  # Validation
    }

    conn.close()

    # Build brand cards HTML
    brand_cards_html = ""
    for i, brand in enumerate(brands, 1):
        brand_id = brand['id']
        style = brand_styles.get(brand_id, {'color': '#999', 'emoji': '❓', 'name': brand['name']})

        score = brand.get('territory_score') or 0
        engagement = brand.get('total_engagement') or 0
        contributors = brand.get('active_contributors') or 0
        tokens = brand.get('total_tokens_distributed') or 0

        contributors_html = ""
        if brand['top_contributors']:
            for contributor in brand['top_contributors']:
                contributors_html += f"""
                <div class="contributor">
                    <span class="contributor-name">{contributor['username']}</span>
                    <span class="contributor-tokens">{contributor['soul_tokens']} tokens</span>
                </div>
                """
        else:
            contributors_html = '<div class="empty-state">No contributors yet. Be the first!</div>'

        brand_cards_html += f"""
            <div class="brand-card" style="border-left-color: {style['color']};">
                <div class="brand-header">
                    <div class="brand-name">
                        <span>{style['emoji']}</span>
                        <span style="color: {style['color']};">{brand['name']}</span>
                    </div>
                    <div class="rank-badge">#{i}</div>
                </div>

                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Territory Score</span>
                        <span class="stat-value" style="color: {style['color']};">{score:.1f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Total Engagement</span>
                        <span class="stat-value">{engagement}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Contributors</span>
                        <span class="stat-value">{contributors}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Tokens Distributed</span>
                        <span class="stat-value" style="color: #ffd700;">{tokens}</span>
                    </div>
                </div>

                <div class="contributors">
                    <strong>Top Contributors:</strong>
                    {contributors_html}
                </div>
            </div>
"""

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Brand Arena - Competitive Leaderboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e27; color: #fff; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ text-align: center; font-size: 48px; margin-bottom: 10px; background: linear-gradient(45deg, #2196F3, #f44336, #4CAF50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ text-align: center; color: #aaa; margin-bottom: 40px; }}
        .brands-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-top: 30px; }}
        .brand-card {{ background: #1a1f3a; border-radius: 12px; padding: 25px; border-left: 5px solid; transition: transform 0.3s, box-shadow 0.3s; }}
        .brand-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .brand-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }}
        .brand-name {{ font-size: 28px; font-weight: bold; display: flex; align-items: center; gap: 10px; }}
        .rank-badge {{ background: #ffd700; color: #000; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .stats {{ margin: 20px 0; }}
        .stat-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #2a2f4a; }}
        .stat-label {{ color: #aaa; }}
        .stat-value {{ font-weight: bold; font-size: 18px; }}
        .contributors {{ margin-top: 20px; }}
        .contributor {{ background: #252a45; padding: 10px; margin: 5px 0; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }}
        .contributor-name {{ font-weight: bold; }}
        .contributor-tokens {{ color: #ffd700; }}
        .nav {{ text-align: center; margin-top: 40px; padding: 20px; }}
        .nav a {{ color: #2196F3; text-decoration: none; margin: 0 15px; font-size: 16px; }}
        .nav a:hover {{ text-decoration: underline; }}
        .empty-state {{ text-align: center; padding: 40px; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚔️ BRAND ARENA</h1>
        <div class="subtitle">Competitive Brand Ecosystem | Earn Soul Tokens | Steer Your Favorite Brand</div>

        <div class="brands-grid">
{brand_cards_html}
        </div>

        <div class="nav">
            <a href="/">← Home</a>
            <a href="/ai-frontend">AI Dashboard</a>
            <a href="/traces">View Traces</a>
        </div>
    </div>
</body>
</html>"""


# ============================================================================
# IDEA SUBMISSION SYSTEM ROUTES
# ============================================================================

@app.route('/submit-idea', methods=['GET'])
def show_idea_form():
    """Show idea submission form"""
    from idea_submission_system import get_submission_status

    theme = request.args.get('theme', '')
    domain = request.args.get('domain', '')
    parent_tracking_id = request.args.get('parent', '')

    # Fetch parent idea if refining
    parent_idea = None
    if parent_tracking_id:
        parent_idea = get_submission_status(parent_tracking_id)

    return render_template('idea_submission/submit_form.html',
                         theme=theme,
                         domain=domain,
                         parent_idea=parent_idea)


@app.route('/submit-idea', methods=['POST'])
def submit_idea_handler():
    """Handle idea submission"""
    from idea_submission_system import submit_idea
    from device_multiplier_system import get_device_fingerprint
    from idea_backpropagation import link_ideas

    # Collect form data
    idea_text = request.form.get('idea')
    email = request.form.get('email')
    phone = request.form.get('phone')
    theme = request.form.get('theme')
    domain = request.form.get('domain')
    parent_tracking_id = request.form.get('parent_tracking_id')

    # Collect device fingerprint from form fields (submitted by JavaScript)
    device_data = {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'screen_resolution': request.form.get('screen_resolution'),
        'timezone': request.form.get('timezone'),
        'language': request.form.get('language'),
        'platform': request.form.get('platform')
    }

    # Submit idea
    result = submit_idea(
        idea_text=idea_text,
        email=email,
        phone=phone,
        device_fingerprint_data=device_data,
        theme=theme,
        domain_slug=domain
    )

    if result['success']:
        # Link to parent idea if this is a refinement
        if parent_tracking_id:
            link_ideas(
                parent_tracking_id=parent_tracking_id,
                child_tracking_id=result['tracking_id'],
                refinement_type='user_improvement',
                question='How would you improve this idea?',
                depth_increase=0.1
            )

        # TODO: Send email confirmation
        flash(f"✅ Idea submitted! Track at: /track/{result['tracking_id']}", 'success')
        return redirect(f"/track/{result['tracking_id']}")
    else:
        flash(f"❌ Error: {result['error']}", 'error')
        return redirect('/submit-idea')


@app.route('/track/<tracking_id>')
def track_idea(tracking_id):
    """Show idea tracking page"""
    from idea_submission_system import get_submission_status
    from idea_backpropagation import get_idea_lineage_tree

    submission = get_submission_status(tracking_id)

    # Get idea lineage (parent/child relationships)
    lineage = None
    if submission:
        lineage = get_idea_lineage_tree(tracking_id)

    return render_template('idea_submission/tracking.html',
                         submission=submission,
                         tracking_id=tracking_id,
                         lineage=lineage)


@app.route('/qr/idea/<theme>')
def idea_qr(theme):
    """Generate production-quality QR code for idea submission using QR Faucet"""
    from qr_faucet import generate_qr_faucet
    import qrcode
    from io import BytesIO

    # Parse domain from query params (optional)
    domain = request.args.get('domain', '')

    # Generate signed payload using QR Faucet
    faucet_result = generate_qr_faucet(
        payload_type='idea_submission',
        data={'theme': theme, 'domain': domain},
        ttl_seconds=86400  # 24 hour expiration
    )

    # Build full URL to faucet scanner
    faucet_url = f"http://localhost:5001/qr/faucet/{faucet_result['encoded_payload']}"

    # Generate production-quality QR code using qrcode library
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(faucet_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return Response(buf.getvalue(), mimetype='image/png')


# ============================================================================
# FREELANCER API ROUTES - API Keys for Brand AI Access
# ============================================================================

@app.route('/api/generate-key', methods=['POST'])
def api_generate_key():
    """Generate API key for freelancer"""
    from freelancer_api import generate_api_key

    # Get form/JSON data
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        tier = data.get('tier', 'free')
        brand_slug = data.get('brand_slug')
    else:
        email = request.form.get('email')
        tier = request.form.get('tier', 'free')
        brand_slug = request.form.get('brand_slug')

    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400

    # Generate key
    result = generate_api_key(email=email, tier=tier, brand_slug=brand_slug)

    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@app.route('/api/v1/<brand_slug>/comment', methods=['GET', 'POST'])
def api_brand_comment(brand_slug):
    """Generate AI comment from brand persona"""
    from freelancer_api import validate_api_key, track_api_call
    from ollama_auto_commenter import generate_ai_comment
    import time

    # Get API key from header or query param
    api_key = request.headers.get('X-API-Key') or request.args.get('key')

    if not api_key:
        return jsonify({'error': 'API key required (X-API-Key header or ?key= param)'}), 401

    # Validate key
    key_info = validate_api_key(api_key)

    if not key_info:
        return jsonify({'error': 'Invalid or expired API key'}), 401

    # Check brand access
    if key_info['tier'] == 'free' and key_info['brand_slug'] != brand_slug:
        return jsonify({
            'error': f"Free tier only has access to {key_info['brand_slug']}. Upgrade to Pro for all brands."
        }), 403

    # Get post_id
    if request.method == 'POST':
        data = request.get_json()
        post_id = data.get('post_id')
    else:
        post_id = request.args.get('post_id')

    if not post_id:
        return jsonify({'error': 'post_id required'}), 400

    try:
        post_id = int(post_id)
    except ValueError:
        return jsonify({'error': 'post_id must be an integer'}), 400

    # Track API call (rate limiting happens here)
    start_time = time.time()

    allowed = track_api_call(
        api_key=api_key,
        endpoint=f'/api/v1/{brand_slug}/comment',
        brand_slug=brand_slug
    )

    if not allowed:
        return jsonify({
            'error': 'Rate limit exceeded',
            'limit': key_info['rate_limit'],
            'calls_today': key_info['calls_today']
        }), 429

    # Generate comment using Ollama
    try:
        comment_id = generate_ai_comment(brand_slug=brand_slug, post_id=post_id)

        if comment_id:
            # Get the generated comment
            conn = get_db()
            comment = conn.execute('''
                SELECT content, created_at FROM comments WHERE id = ?
            ''', (comment_id,)).fetchone()
            conn.close()

            response_time_ms = int((time.time() - start_time) * 1000)

            # Update call log with success
            from freelancer_api import track_api_call
            track_api_call(
                api_key=api_key,
                endpoint=f'/api/v1/{brand_slug}/comment',
                brand_slug=brand_slug,
                response_status=200,
                response_time_ms=response_time_ms
            )

            return jsonify({
                'success': True,
                'comment_id': comment_id,
                'comment_text': comment['content'],
                'brand': brand_slug,
                'created_at': comment['created_at'],
                'response_time_ms': response_time_ms
            })
        else:
            return jsonify({'error': 'Failed to generate comment'}), 500

    except Exception as e:
        # Log error
        from freelancer_api import track_api_call
        track_api_call(
            api_key=api_key,
            endpoint=f'/api/v1/{brand_slug}/comment',
            brand_slug=brand_slug,
            response_status=500,
            error_message=str(e)
        )

        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/<brand_slug>/classify', methods=['GET', 'POST'])
def api_brand_classify(brand_slug):
    """Classify text using brand's neural network"""
    from freelancer_api import validate_api_key, track_api_call
    from neural_proxy import classify_with_neural_network
    import time

    # Get API key
    api_key = request.headers.get('X-API-Key') or request.args.get('key')

    if not api_key:
        return jsonify({'error': 'API key required'}), 401

    # Validate key
    key_info = validate_api_key(api_key)

    if not key_info:
        return jsonify({'error': 'Invalid or expired API key'}), 401

    # Check brand access
    if key_info['tier'] == 'free' and key_info['brand_slug'] != brand_slug:
        return jsonify({
            'error': f"Free tier only has access to {key_info['brand_slug']}. Upgrade to Pro for all brands."
        }), 403

    # Get text to classify
    if request.method == 'POST':
        data = request.get_json()
        text = data.get('text')
    else:
        text = request.args.get('text')

    if not text:
        return jsonify({'error': 'text parameter required'}), 400

    # Track API call
    start_time = time.time()

    allowed = track_api_call(
        api_key=api_key,
        endpoint=f'/api/v1/{brand_slug}/classify',
        brand_slug=brand_slug
    )

    if not allowed:
        return jsonify({
            'error': 'Rate limit exceeded',
            'limit': key_info['rate_limit'],
            'calls_today': key_info['calls_today']
        }), 429

    # Classify text
    try:
        result = classify_with_neural_network(text)

        response_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            'success': True,
            'text': text,
            'classification': result['classification'],
            'confidence': result['confidence'],
            'all_scores': result.get('all_scores', {}),
            'response_time_ms': response_time_ms
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# FREELANCER SIGNUP
# ==============================================================================

@app.route('/subscribe/freelancer', methods=['GET', 'POST'])
def subscribe_freelancer():
    """
    Freelancer signup page - Auto-generate API key

    Flow:
    1. User fills out signup form (email, brand preference)
    2. System creates subscriber record
    3. System generates API key (free tier, assigned to selected brand)
    4. Send welcome email with API key and docs
    5. Redirect to success page with API key
    """
    if request.method == 'POST':
        from freelancer_api import generate_api_key
        from email_server import queue_email

        email = request.form.get('email')
        brand_slug = request.form.get('brand_slug', 'calriven')
        name = request.form.get('name', '')

        if not email:
            flash('Email is required', 'error')
            return redirect('/subscribe/freelancer')

        # Generate API key (free tier, single brand access)
        result = generate_api_key(
            email=email,
            tier='free',
            brand_slug=brand_slug
        )

        if not result['success']:
            flash(result['error'], 'error')
            return redirect('/subscribe/freelancer')

        api_key = result['api_key']

        # Add to newsletter subscribers (linked to API key)
        try:
            conn = get_db()
            # Get the API key ID
            api_key_row = conn.execute(
                'SELECT id FROM api_keys WHERE api_key = ?',
                (api_key,)
            ).fetchone()

            if api_key_row:
                api_key_id = api_key_row['id']

                # Insert into newsletter_subscribers
                conn.execute('''
                    INSERT OR IGNORE INTO newsletter_subscribers
                    (email, name, brand, verified, api_key_id, signup_source)
                    VALUES (?, ?, ?, 1, ?, 'freelancer_api')
                ''', (email, name, brand_slug, api_key_id))
                conn.commit()
                print(f"📧 Newsletter subscriber added: {email} → {brand_slug}")
            conn.close()
        except Exception as e:
            print(f"⚠️  Newsletter subscription failed: {e}")

        # Send welcome email with API docs
        subject = f"🎉 Welcome to Soulfra API - Your API Key Inside!"

        body = f"""
Hi {name or 'there'}!

Welcome to the Soulfra Freelancer API program! 🚀

Your API key is ready:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{api_key}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Your Plan Details:
• Tier: Free
• Brand Access: {brand_slug.upper()}
• Rate Limit: 100 calls/day
• Endpoints: Comment Generation, Text Classification

📚 API Documentation:

1. Generate AI Comment:
   curl -H "X-API-Key: {api_key}" \\
     "http://localhost:5001/api/v1/{brand_slug}/comment?post_id=1"

2. Classify Text:
   curl -H "X-API-Key: {api_key}" \\
     "http://localhost:5001/api/v1/{brand_slug}/classify?text=Your+text+here"

3. Check Your Usage:
   View your API stats at: http://localhost:5001/api/stats?key={api_key}

💡 Pro Tips:
• Include X-API-Key header in all requests
• Rate limit resets daily at midnight UTC
• Reply to newsletter emails to auto-comment on posts!
• Upgrade to Pro for multi-brand access (1000 calls/day)

🔗 Resources:
• API Docs: http://localhost:5001/api/docs
• Brand Personas: http://localhost:5001/brands
• Community: http://localhost:5001/community

📧 Newsletter Subscription:
You've been subscribed to AI comment digests for {brand_slug.upper()}.
You'll receive weekly updates with AI-generated comments and insights.

Need help? Reply to this email!

---
Soulfra Platform
Building AI-powered conversation tools

Unsubscribe: http://localhost:5001/unsubscribe?email={email}
        """.strip()

        queue_email(
            from_addr='noreply@soulfra.local',
            to_addrs=[email],
            subject=subject,
            body=body
        )

        # Show success page with API key
        return render_template('freelancer_signup_success.html',
                             api_key=api_key,
                             brand_slug=brand_slug,
                             email=email,
                             rate_limit=100)

    # GET - Show signup form
    return render_template('freelancer_signup_form.html')


# ==============================================================================
# ADMIN DASHBOARDS
# ==============================================================================

@app.route('/admin/freelancers')
def admin_freelancers():
    """Admin dashboard for freelancer API management"""
    # Check admin access
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect('/login')

    from freelancer_api import get_api_stats
    from email_reply_handler import get_inbound_email_stats

    # Get API statistics
    api_stats = get_api_stats()

    # Get email reply statistics
    email_stats = get_inbound_email_stats()

    # Get recent API keys
    conn = get_db()
    recent_keys = conn.execute('''
        SELECT
            user_email,
            api_key,
            tier,
            brand_slug,
            rate_limit,
            calls_today,
            calls_total,
            created_at
        FROM api_keys
        ORDER BY created_at DESC
        LIMIT 20
    ''').fetchall()

    # Get top API users
    top_users = conn.execute('''
        SELECT
            user_email,
            tier,
            SUM(calls_total) as total_calls,
            COUNT(*) as key_count
        FROM api_keys
        WHERE revoked = 0
        GROUP BY user_email
        ORDER BY total_calls DESC
        LIMIT 10
    ''').fetchall()

    # Get recent API calls
    recent_calls = conn.execute('''
        SELECT
            api_call_logs.*,
            api_keys.user_email,
            api_keys.tier
        FROM api_call_logs
        JOIN api_keys ON api_call_logs.api_key_id = api_keys.id
        ORDER BY api_call_logs.created_at DESC
        LIMIT 50
    ''').fetchall()

    conn.close()

    return render_template('admin_freelancers.html',
                         api_stats=api_stats,
                         email_stats=email_stats,
                         recent_keys=[dict(k) for k in recent_keys],
                         top_users=[dict(u) for u in top_users],
                         recent_calls=[dict(c) for c in recent_calls])


@app.route('/admin/ollama')
def admin_ollama():
    """Admin dashboard for Ollama AI monitoring"""
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect('/login')

    import urllib.request
    import urllib.error

    # Check Ollama status
    try:
        req = urllib.request.Request('http://localhost:11434/api/tags')
        with urllib.request.urlopen(req, timeout=2) as response:
            ollama_status = 'running'
            models = json.loads(response.read().decode())
    except:
        ollama_status = 'offline'
        models = {'models': []}

    # Get AI comment statistics
    conn = get_db()

    ai_comment_stats = conn.execute('''
        SELECT
            COUNT(*) as total_comments,
            COUNT(DISTINCT user_id) as ai_users,
            MAX(created_at) as last_generated
        FROM comments
        WHERE user_id IN (
            SELECT id FROM users WHERE username LIKE '%AI%' OR username LIKE 'brand-%'
        )
    ''').fetchone()

    # Get recent AI comments
    recent_ai_comments = conn.execute('''
        SELECT
            comments.*,
            users.username,
            users.avatar
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE users.username LIKE '%AI%' OR users.username LIKE 'brand-%'
        ORDER BY comments.created_at DESC
        LIMIT 20
    ''').fetchall()

    conn.close()

    return render_template('admin_ollama.html',
                         ollama_status=ollama_status,
                         models=models.get('models', []),
                         ai_stats=dict(ai_comment_stats) if ai_comment_stats else {},
                         recent_comments=[dict(c) for c in recent_ai_comments])


# ==============================================================================
# AUTO-GENERATED DASHBOARDS & MASTER ADMIN PORTAL
# ==============================================================================

@app.route('/admin')
def admin_home():
    """Master admin portal - Shows all available dashboards"""
    # Quick admin access for development (remove in production)
    if request.args.get('dev_login') == 'true':
        session['is_admin'] = True
        flash('Dev admin access granted', 'success')

    if not session.get('is_admin'):
        flash('Admin login required', 'error')
        return redirect('/admin/login')

    from schema_inspector import get_database_overview

    overview = get_database_overview()

    return render_template('admin_master_portal.html',
                         overview=overview)


@app.route('/admin/set-session')
def admin_set_session():
    """Quick admin session setter for development"""
    session['is_admin'] = True
    flash('Admin session set!', 'success')
    return redirect('/admin')


# Register auto-generated routes for all tables
# This makes dashboards accessible at /admin/<table_name>
try:
    from route_generator import register_all_table_routes
    # Commented out for now - uncomment when ready to use
    # register_all_table_routes(app)
    # print("✅ Auto-registered routes for all database tables")
except Exception as e:
    print(f"⚠️  Auto-route registration disabled: {e}")


# ==============================================================================
# GAME SHARING & PEER REVIEW ROUTES
# ==============================================================================

@app.route('/games/share', methods=['POST'])
def create_game_share_route():
    """Create a shareable game link for peer review"""
    from game_sharing import create_game_share

    data = request.get_json() or {}

    # Required fields
    game_type = data.get('game_type')
    game_data = data.get('game_data')
    recipient_email = data.get('recipient_email')

    if not all([game_type, game_data, recipient_email]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields: game_type, game_data, recipient_email'
        }), 400

    # Optional fields
    sender_user_id = session.get('user_id')
    sender_name = data.get('sender_name')
    sender_email = data.get('sender_email')
    message = data.get('message')

    try:
        # Create the share
        share_id, share_code = create_game_share(
            game_type=game_type,
            game_data=game_data,
            recipient_email=recipient_email,
            sender_user_id=sender_user_id,
            sender_name=sender_name,
            sender_email=sender_email,
            message=message
        )

        # Send email notification to recipient
        from emails import send_game_share_email
        from rotation_helpers import inject_rotation_context
        from subdomain_router import detect_brand_from_subdomain

        brand = detect_brand_from_subdomain()
        context = inject_rotation_context(brand)

        send_game_share_email(
            recipient_email=recipient_email,
            share_code=share_code,
            game_type=game_type,
            sender_name=sender_name,
            message=message,
            theme_primary=context.get('theme_primary', '#667eea'),
            theme_secondary=context.get('theme_secondary', '#764ba2')
        )

        return jsonify({
            'success': True,
            'share_id': share_id,
            'share_code': share_code,
            'review_url': f'/review/{share_code}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/review/<share_code>', methods=['GET', 'POST'])
def review_game(share_code):
    """Friend reviews the shared game"""
    from game_sharing import get_game_share, submit_game_review, analyze_game_review
    from rotation_helpers import inject_rotation_context
    from subdomain_router import detect_brand_from_subdomain

    # Get the game share
    share = get_game_share(share_code)

    if not share:
        flash('Share link not found or expired', 'error')
        return redirect(url_for('index'))

    # Check if expired
    if share.get('status') == 'expired':
        flash('This share link has expired', 'error')
        return redirect(url_for('index'))

    # Get brand context for theming
    brand = detect_brand_from_subdomain()
    context = inject_rotation_context(brand)

    # Handle POST - submit review
    if request.method == 'POST':
        review_data = {}

        # Collect all question responses
        for key, value in request.form.items():
            if key.startswith('question_'):
                review_data[key] = value

        # Get overall rating
        overall_rating = request.form.get('overall_rating')
        if overall_rating:
            overall_rating = int(overall_rating)

        # Get anonymous option
        is_anonymous = request.form.get('is_anonymous') == 'on'

        # Get reviewer info
        reviewer_user_id = session.get('user_id')
        reviewer_email = request.form.get('reviewer_email', 'anonymous@example.com')
        reviewer_name = request.form.get('reviewer_name', 'Anonymous')

        try:
            # Submit the review
            review_id = submit_game_review(
                share_code=share_code,
                review_data=review_data,
                reviewer_email=reviewer_email,
                reviewer_user_id=reviewer_user_id,
                reviewer_name=reviewer_name,
                is_anonymous=is_anonymous,
                overall_rating=overall_rating
            )

            # Analyze with AI
            analysis = analyze_game_review(review_id)

            # Send notification to sender
            if share.get('sender_email'):
                from emails import send_review_received_email

                send_review_received_email(
                    sender_email=share['sender_email'],
                    share_code=share_code,
                    game_type=share['game_type'],
                    reviewer_name=reviewer_name if not is_anonymous else None,
                    overall_rating=overall_rating,
                    theme_primary=context.get('theme_primary', '#667eea'),
                    theme_secondary=context.get('theme_secondary', '#764ba2')
                )

            flash('Review submitted successfully! AI analysis complete.', 'success')
            return redirect(url_for('view_analysis', share_code=share_code))

        except Exception as e:
            flash(f'Error submitting review: {str(e)}', 'error')
            return redirect(url_for('review_game', share_code=share_code))

    # Handle GET - show review form
    # Get review questions from database
    db = get_db()
    questions = db.execute('''
        SELECT * FROM review_questions
        WHERE game_type = ? AND is_active = 1
        ORDER BY order_index
    ''', (share['game_type'],)).fetchall()

    # Convert to list of dicts
    review_questions = []
    for q in questions:
        question_dict = dict(q)
        if question_dict.get('metadata'):
            question_dict['metadata'] = json.loads(question_dict['metadata'])
        review_questions.append(question_dict)

    return render_template(
        'games/review_game_v1_dinghy.html',
        share=share,
        review_questions=review_questions,
        **context
    )


@app.route('/share/<share_code>/analysis')
def view_analysis(share_code):
    """View AI analysis of completed review"""
    from game_sharing import get_game_share, get_reviews_for_share
    from rotation_helpers import inject_rotation_context
    from subdomain_router import detect_brand_from_subdomain

    # Get the game share
    share = get_game_share(share_code)

    if not share:
        flash('Share link not found', 'error')
        return redirect(url_for('index'))

    # Check if reviewed
    if share.get('status') != 'reviewed':
        flash('No reviews yet for this share', 'info')
        return redirect(url_for('review_game', share_code=share_code))

    # Get all reviews
    reviews = get_reviews_for_share(share['id'])

    # Calculate aggregate stats
    total_reviews = len(reviews)
    avg_rating = sum(r.get('overall_rating', 0) for r in reviews) / total_reviews if total_reviews > 0 else 0
    avg_helpfulness = sum(r.get('helpfulness_score', 0) for r in reviews) / total_reviews if total_reviews > 0 else 0

    # Collect all classifications
    all_classifications = []
    all_recommendations = []

    for review in reviews:
        if review.get('neural_classification'):
            classifications = json.loads(review['neural_classification'])
            all_classifications.extend(classifications)

            # Generate recommendations based on classifications
            for c in classifications:
                if c.get('confidence', 0) > 0.7:
                    if c.get('network_name') == 'calriven_technical_classifier' and c.get('label') == 'technical':
                        all_recommendations.append('Technical feedback detected - share in dev channels')
                    elif c.get('network_name') == 'theauditor_validation_classifier' and c.get('label') == 'validated':
                        all_recommendations.append('Thorough validation - consider featuring this review')

    # Remove duplicate recommendations
    all_recommendations = list(set(all_recommendations))

    # Get brand context
    brand = detect_brand_from_subdomain()
    context = inject_rotation_context(brand)

    return render_template(
        'games/analysis_results_v1_dinghy.html',
        share=share,
        reviews=reviews,
        total_reviews=total_reviews,
        avg_rating=round(avg_rating, 1),
        avg_helpfulness=round(avg_helpfulness * 100),
        classifications=all_classifications,
        recommendations=all_recommendations,
        **context
    )


# ==============================================================================
# CRINGEPROOF GAME ROUTES - Self-Awareness Assessment
# ==============================================================================

@app.route('/cringeproof')
def cringeproof_game():
    """
    Cringeproof entry point - redirect to narrative quiz

    Note: This route originally used soulfra_games.py which doesn't exist.
    Fixed by redirecting to the working narrative interface.
    """
    # Redirect to working narrative quiz (default: soulfra)
    return redirect(url_for('narrative_game', brand_slug='soulfra'))


@app.route('/cringeproof/article/<slug>')
def cringeproof_from_article(slug):
    """Generate Cringeproof questions from a specific blog post"""
    from soulfra_games import DynamicCringeproof
    import sqlite3

    # Fetch the blog post
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, content, published_at
        FROM posts
        WHERE slug = ?
        LIMIT 1
    ''', (slug,))

    post = cursor.fetchone()
    conn.close()

    if not post:
        flash(f'Article "{slug}" not found', 'error')
        return redirect(url_for('cringeproof_game'))

    # Convert to dict for soulfra_games
    post_data = {
        'id': post['id'],
        'title': post['title'],
        'content': post['content']
    }

    # Generate dynamic questions from this specific article
    game = DynamicCringeproof()
    questions = game.generate_questions_from_posts(posts=[post_data], num_questions=7)

    print(f"✨ Generated {len(questions)} questions from article '{post['title']}'")

    # Always ensure we have exactly 7 questions
    if len(questions) < 7:
        print(f"⚠️  Only {len(questions)} questions generated, filling with static fallback")
        from cringeproof import CRINGEPROOF_QUESTIONS

        static_questions = [{
            'id': q['id'],
            'question': q['text'],
            'category': q['category'],
            'context': None,
            'generated_from': 'fallback'
        } for q in CRINGEPROOF_QUESTIONS]

        questions_needed = 7 - len(questions)
        questions.extend(static_questions[:questions_needed])

    return render_template('cringeproof/play.html',
                          questions=questions,
                          article_title=post['title'],
                          article_slug=slug)


@app.route('/cringeproof/submit', methods=['POST'])
def cringeproof_submit():
    """Process cringeproof game answers and generate results with physics scoring"""
    from cringeproof import (
        calculate_score,
        generate_insights,
        generate_recommendations,
        save_game_result
    )
    from cringeproof_reasoning import ReasoningEngine
    from lib.physics import PhysicsScoring

    try:
        # Get responses from form
        responses = {}
        for i in range(1, 8):  # 7 questions
            key = f'q{i}'
            value = request.form.get(key)
            if value:
                responses[i] = int(value)

        # Validate all questions answered
        if len(responses) != 7:
            flash('Please answer all 7 questions', 'error')
            return redirect(url_for('cringeproof_game'))

        # Calculate score
        score_data = calculate_score(responses)

        # Get user's score history (if logged in)
        user_id = session.get('user_id')
        score_history = []
        category_history = {}

        if user_id:
            # Fetch previous results from database
            db = get_db()
            previous_results = db.execute(
                'SELECT result_data FROM game_results WHERE user_id = ? ORDER BY created_at ASC',
                (user_id,)
            ).fetchall()

            if previous_results:
                for row in previous_results:
                    prev_data = json.loads(row['result_data'])
                    score_history.append(prev_data.get('percentage', 0))

                    # Track category history
                    for cat, score in prev_data.get('category_scores', {}).items():
                        if cat not in category_history:
                            category_history[cat] = []
                        category_history[cat].append(score)

        # Add current score to history
        score_history.append(score_data['percentage'])
        for cat, score in score_data['category_scores'].items():
            if cat not in category_history:
                category_history[cat] = []
            category_history[cat].append(score)

        # Run physics-based analysis if we have enough history
        physics_analysis = None
        reasoning_analysis = None

        if len(score_history) >= 2:
            try:
                # Physics scoring
                physics = PhysicsScoring()
                physics_analysis = physics.analyze_score_history(
                    score_history,
                    category_history if category_history else None
                )

                # Reasoning engine (deep analysis)
                reasoning_engine = ReasoningEngine()
                reasoning_analysis = reasoning_engine.deep_analyze(
                    score_history,
                    score_data['category_scores'],
                    category_history if category_history else None
                )
            except Exception as e:
                print(f"Warning: Physics/reasoning analysis failed: {e}")
                # Continue without physics analysis

        # Add physics data to score_data
        if physics_analysis:
            score_data['physics'] = physics_analysis
        if reasoning_analysis:
            score_data['reasoning'] = reasoning_analysis

        # Generate insights (enhanced with physics if available)
        if reasoning_analysis and 'personalized_insights' in reasoning_analysis:
            insights = reasoning_analysis['personalized_insights']
        else:
            insights = generate_insights(score_data)

        recommendations = generate_recommendations(score_data)

        # Save to database (with physics data)
        result_id = save_game_result(user_id, score_data)

        # Broadcast real-time update via WebSocket
        try:
            from flask_socketio import emit

            # Get total response count
            db = get_db()
            total_responses = db.execute('SELECT COUNT(*) as count FROM game_results').fetchone()['count']

            # Broadcast to all connected clients
            socketio.emit('game_response_submitted', {
                'total_responses': total_responses,
                'latest_score': int(score_data['percentage']),
                'archetype': score_data.get('reasoning', {}).get('archetype', {}).get('name') if score_data.get('reasoning') else None,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)

            print(f"🔔 Broadcasted update: {total_responses} total responses")

        except Exception as e:
            print(f"⚠️ WebSocket broadcast failed: {e}")
            # Don't fail the submission if WebSocket fails

        # Redirect to results page
        return redirect(url_for('cringeproof_results', result_id=result_id))

    except Exception as e:
        print(f"Error processing cringeproof submission: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('cringeproof_game'))


@app.route('/cringeproof/results/<int:result_id>')
def cringeproof_results(result_id):
    """Display cringeproof game results"""
    from cringeproof import get_game_result, generate_insights, generate_recommendations

    # Get result from database
    result = get_game_result(result_id)

    if not result:
        flash('Result not found', 'error')
        return redirect(url_for('cringeproof_game'))

    # Extract score data
    score_data = result['result_data']

    # Generate insights and recommendations
    insights = generate_insights(score_data)
    recommendations = generate_recommendations(score_data)

    # Check if user is logged in
    user_id = session.get('user_id')
    is_anonymous = (result['user_id'] is None)

    return render_template(
        'cringeproof/results.html',
        score_data=score_data,
        insights=insights,
        recommendations=recommendations,
        result_id=result_id,
        user_id=user_id,
        is_anonymous=is_anonymous
    )


@app.route('/cringeproof/leaderboard')
def cringeproof_leaderboard():
    """Display leaderboard of top improvers"""
    from lib.physics import PhysicsScoring
    import sqlite3
    from datetime import datetime, timedelta

    # Connect to database
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all game results with user info
    cursor.execute('''
        SELECT
            gr.id,
            gr.user_id,
            gr.result_data,
            gr.created_at,
            u.username,
            u.display_name
        FROM game_results gr
        LEFT JOIN users u ON gr.user_id = u.id
        WHERE gr.game_type = 'cringeproof'
        ORDER BY gr.user_id, gr.created_at
    ''')

    results = cursor.fetchall()
    conn.close()

    # Group results by user
    user_results = {}
    for row in results:
        user_id = row['user_id']
        if user_id is None:  # Skip anonymous users
            continue

        if user_id not in user_results:
            user_results[user_id] = {
                'username': row['username'],
                'display_name': row['display_name'] or row['username'] or 'Anonymous',
                'scores': [],
                'archetypes': []
            }

        # Extract score from result_data
        import json
        result_data = json.loads(row['result_data'])
        score = result_data.get('percentage', 0)
        user_results[user_id]['scores'].append(score)

        # Extract archetype if available
        if result_data.get('reasoning') and result_data['reasoning'].get('archetype'):
            archetype = result_data['reasoning']['archetype'].get('name')
            if archetype:
                user_results[user_id]['archetypes'].append(archetype)

    # Calculate velocity for each user (need 2+ sessions)
    improvers = []
    physics = PhysicsScoring()

    for user_id, data in user_results.items():
        if len(data['scores']) >= 2:
            # Run physics analysis
            analysis = physics.analyze_score_history(data['scores'])

            # Get latest archetype
            archetype = data['archetypes'][-1] if data['archetypes'] else None

            improvers.append({
                'display_name': data['display_name'],
                'velocity': analysis['velocity'],
                'latest_score': int(data['scores'][-1]),
                'archetype': archetype,
                'session_count': len(data['scores'])
            })

    # Sort by velocity (most negative = most improved)
    # Negative velocity = score going down = improvement!
    improvers.sort(key=lambda x: x['velocity'])

    return render_template(
        'cringeproof/leaderboard.html',
        improvers=improvers
    )


# In-memory storage for active cringeproof rooms
# Format: { room_code: { 'host_id': user_id, 'players': [], 'created_at': timestamp } }
CRINGEPROOF_ROOMS = {}


@app.route('/cringeproof/create-room', methods=['POST'])
def create_cringeproof_room():
    """Create a multiplayer cringeproof room"""
    import random
    import string
    from datetime import datetime

    # Generate unique 6-character room code
    def generate_room_code():
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=6))
            room_code = f"GAME-{code}"
            if room_code not in CRINGEPROOF_ROOMS:
                return room_code

    room_code = generate_room_code()
    user_id = session.get('user_id')
    username = session.get('username', 'Anonymous')

    # Get host score from request
    data = request.get_json() or {}
    host_score = data.get('host_score', 0)

    # Create room
    CRINGEPROOF_ROOMS[room_code] = {
        'host_id': user_id,
        'host_name': username,
        'host_score': host_score,
        'players': [],
        'created_at': datetime.now().isoformat()
    }

    return jsonify({
        'room_code': room_code,
        'message': 'Room created successfully'
    })


@app.route('/cringeproof/room/<room_code>')
def cringeproof_room(room_code):
    """Display multiplayer room for cringeproof"""
    # Check if room exists
    if room_code not in CRINGEPROOF_ROOMS:
        flash('Room not found or expired', 'error')
        return redirect(url_for('cringeproof_game'))

    room = CRINGEPROOF_ROOMS[room_code]
    user_id = session.get('user_id')
    username = session.get('username', 'Anonymous')

    # Determine if current user is host
    is_host = (user_id == room['host_id'])

    return render_template(
        'cringeproof/room.html',
        room_code=room_code,
        room=room,
        is_host=is_host,
        username=username
    )


# ==============================================================================
# HUB ROUTE - Master Control Panel (Google-like Feature Grid)
# ==============================================================================

@app.route('/hub')
def hub():
    """Master control panel showing all features in unified interface"""
    from query_templates import QueryTemplates

    qt = QueryTemplates()
    stats = qt.get_platform_stats(days=30)

    # Pass loaded_plugins to template
    loaded_plugins = getattr(app, 'loaded_plugins', [])

    return render_template('hub.html', stats=stats, loaded_plugins=loaded_plugins)


@app.route('/features')
def features_dashboard():
    """Plugin features dashboard showing all loaded plugins and their metadata"""
    loaded_plugins = getattr(app, 'loaded_plugins', [])
    return render_template('features_dashboard.html', plugins=loaded_plugins)


# ==============================================================================
# FEATURE FACTORY ROUTES - Pinterest-Style Template Browser
# ==============================================================================

@app.route('/factory')
def feature_factory():
    """
    Feature Factory - Pinterest-style template & component browser

    Start a new idea from the widget → Browse → Generate → Save/Pin
    """
    from feature_factory import FeatureFactory

    factory = FeatureFactory()

    # Get view mode
    view_mode = request.args.get('view', 'all')

    if view_mode == 'pinned':
        # Show only pinned items
        pinned_items = factory.get_pinned()
        catalog = {}
        for item in pinned_items:
            # Regenerate full item data
            full_catalog = factory.get_catalog()
            for category, items in full_catalog.items():
                for full_item in items:
                    if full_item['id'] == item['item_id']:
                        if category not in catalog:
                            catalog[category] = []
                        catalog[category].append(full_item)
    else:
        catalog = factory.get_catalog()

    stats = factory.get_stats()

    return render_template('factory.html', catalog=catalog, stats=stats)


@app.route('/api/factory/pin', methods=['POST'])
def factory_pin():
    """Pin an item for quick access"""
    from feature_factory import FeatureFactory

    data = request.get_json()
    item_id = data.get('item_id')
    name = data.get('name')
    category = data.get('category')

    if not all([item_id, name, category]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    factory = FeatureFactory()
    success = factory.pin(item_id, name, category)

    return jsonify({'success': success})


@app.route('/api/factory/unpin', methods=['POST'])
def factory_unpin():
    """Unpin an item"""
    from feature_factory import FeatureFactory

    data = request.get_json()
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'success': False, 'error': 'Missing item_id'}), 400

    factory = FeatureFactory()
    success = factory.unpin(item_id)

    return jsonify({'success': success})


@app.route('/api/factory/preview/<item_id>')
def factory_preview(item_id):
    """Get full preview of an item"""
    from feature_factory import FeatureFactory

    factory = FeatureFactory()
    catalog = factory.get_catalog()

    # Find item in catalog
    for category, items in catalog.items():
        for item in items:
            if item['id'] == item_id:
                return jsonify({
                    'success': True,
                    'name': item['name'],
                    'preview': item['preview']
                })

    return jsonify({'success': False, 'error': 'Item not found'}), 404


@app.route('/api/factory/generate', methods=['POST'])
def factory_generate():
    """Generate code/files from a catalog item"""
    from feature_factory import FeatureFactory

    data = request.get_json()
    item_id = data.get('item_id')
    output_path = data.get('output_path')

    if not item_id:
        return jsonify({'success': False, 'error': 'Missing item_id'}), 400

    factory = FeatureFactory()
    result = factory.generate(item_id, output_path=output_path)

    return jsonify(result)


# ==============================================================================
# BRAND BUILDER ROUTES - Conversational Brand Creation with Ollama
# ==============================================================================

@app.route('/brand-builder/start')
def brand_builder_start():
    """Brand builder landing page with chat interface"""
    import uuid
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    return render_template('brand_builder_chat.html', session_id=session_id)


@app.route('/api/brand-builder/chat', methods=['POST'])
def brand_builder_chat():
    """Handle brand builder chat messages"""
    from brand_builder import process_message

    data = request.get_json()
    session_id = data.get('session_id')
    user_message = data.get('message', '').strip()

    if not session_id or not user_message:
        return jsonify({'success': False, 'error': 'Missing session_id or message'}), 400

    try:
        response, options = process_message(session_id, user_message)

        return jsonify({
            'success': True,
            'response': response,
            'options': options
        })

    except Exception as e:
        print(f"Brand builder error: {e}")
        return jsonify({
            'success': False,
            'error': 'Something went wrong. Please try again.'
        }), 500


# ==============================================================================
# GAMES - Cross-platform game system
# ==============================================================================

@app.route('/games')
def games_gallery():
    """Game gallery - list all available games"""
    from game_orchestrator import GameOrchestrator

    conn = get_db()

    # Get all game sessions
    games = conn.execute('''
        SELECT
            gs.game_id,
            gs.session_name,
            gs.game_type,
            gs.status,
            gs.current_turn,
            gs.created_at,
            gs.last_action_at,
            u.username as creator_username,
            COUNT(DISTINCT cpp.user_id) as player_count,
            COUNT(DISTINCT ga.action_id) as total_actions
        FROM game_sessions gs
        JOIN users u ON gs.creator_user_id = u.id
        LEFT JOIN cross_platform_players cpp ON gs.game_id = cpp.game_id
        LEFT JOIN game_actions ga ON gs.game_id = ga.game_id
        GROUP BY gs.game_id
        ORDER BY gs.created_at DESC
        LIMIT 50
    ''').fetchall()

    # Get available simple games
    simple_games = [
        {
            'id': '2plus2',
            'name': '2+2 Math Game',
            'description': 'The simplest possible game - answer a single math question',
            'icon': '🧮',
            'play_url': '/games/play/2plus2'
        },
        {
            'id': 'chess',
            'name': 'Chess (Coming Soon)',
            'description': 'Classic chess with AI judging',
            'icon': '♟️',
            'play_url': None
        },
        {
            'id': 'dnd',
            'name': 'D&D Campaign',
            'description': 'AI dungeon master judges your actions • Character ages with each quest • Earn legendary items',
            'icon': '🐉',
            'play_url': '/games/play/dnd'
        }
    ]

    conn.close()

    return render_template('games_gallery.html',
                         games=[dict(g) for g in games],
                         simple_games=simple_games)


@app.route('/games/<int:game_id>')
def game_detail(game_id):
    """Game session detail - show state, actions, players"""
    from game_orchestrator import GameOrchestrator

    conn = get_db()

    # Get game session
    game = conn.execute('''
        SELECT gs.*, u.username as creator_username
        FROM game_sessions gs
        JOIN users u ON gs.creator_user_id = u.id
        WHERE gs.game_id = ?
    ''', (game_id,)).fetchone()

    if not game:
        flash('Game not found', 'danger')
        return redirect(url_for('games_gallery'))

    # Get current state
    orch = GameOrchestrator(game_id)
    try:
        current_state = orch.get_current_state()
    except:
        current_state = {'error': 'No state available'}

    # Get players
    players = conn.execute('''
        SELECT
            cpp.*,
            u.username,
            u.display_name
        FROM cross_platform_players cpp
        JOIN users u ON cpp.user_id = u.id
        WHERE cpp.game_id = ?
        ORDER BY cpp.joined_at DESC
    ''', (game_id,)).fetchall()

    # Get recent actions
    actions = conn.execute('''
        SELECT
            ga.*,
            u.username
        FROM game_actions ga
        JOIN users u ON ga.player_user_id = u.id
        WHERE ga.game_id = ?
        ORDER BY ga.action_id DESC
        LIMIT 20
    ''', (game_id,)).fetchall()

    # Get verified proofs
    proofs = conn.execute('''
        SELECT * FROM verified_proofs
        WHERE game_id = ?
        ORDER BY proof_id DESC
        LIMIT 10
    ''', (game_id,)).fetchall()

    conn.close()

    return render_template('game_detail.html',
                         game=dict(game),
                         current_state=current_state,
                         players=[dict(p) for p in players],
                         actions=[dict(a) for a in actions],
                         proofs=[dict(p) for p in proofs])


@app.route('/games/play/2plus2')
def play_2plus2():
    """Play 2+2 math game in browser"""
    # Get current user or create guest
    user_id = session.get('user_id')

    if not user_id:
        # Require login or create guest user
        flash('Please log in to play games', 'warning')
        return redirect(url_for('login'))

    return render_template('game_2plus2.html', user_id=user_id)


@app.route('/api/games/create/2plus2', methods=['POST'])
def api_create_2plus2():
    """Create a new 2+2 game session"""
    from simple_games.two_plus_two import create_2plus2_game

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        game_id = create_2plus2_game(user_id)

        return jsonify({
            'success': True,
            'game_id': game_id,
            'question': 'What is 2 + 2?'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games/submit-answer', methods=['POST'])
def api_submit_answer():
    """Submit answer to game question"""
    from game_orchestrator import GameOrchestrator

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    game_id = data.get('game_id')
    answer = data.get('answer')
    game_type = data.get('game_type', '2plus2')

    if not game_id or answer is None:
        return jsonify({'success': False, 'error': 'Missing game_id or answer'}), 400

    try:
        # Check answer
        is_correct = False
        if game_type == '2plus2':
            try:
                answer_num = int(answer)
                is_correct = (answer_num == 4)
            except ValueError:
                is_correct = False

        # Submit to orchestrator
        orch = GameOrchestrator(game_id)
        result = orch.process_action(
            user_id=user_id,
            platform='web',
            action_type='answer_question',
            action_data={
                'question': 'What is 2 + 2?',
                'answer': answer,
                'is_correct': is_correct,
                'game_type': game_type
            }
        )

        # Update Soul Pack
        from profile_compilers.session_to_soul import compile_soul_with_games
        soul_pack = compile_soul_with_games(user_id)

        return jsonify({
            'success': True,
            'correct': is_correct,
            'ai_verdict': result.get('ai_verdict'),
            'ai_reasoning': result.get('ai_reasoning'),
            'soul_updated': True,
            'expertise': soul_pack['essence']['expertise']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# D&D CAMPAIGN ROUTES
# ============================================================================

@app.route('/games/play/dnd')
def play_dnd():
    """Play D&D campaign in browser"""
    user_id = session.get('user_id')

    if not user_id:
        flash('Please log in to play D&D', 'warning')
        return redirect(url_for('login'))

    return render_template('game_dnd.html', user_id=user_id)


@app.route('/api/games/dnd/character')
def api_dnd_character():
    """Get character info (age + attributes)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        from aging_curves import get_all_attributes

        conn = get_db()
        user = conn.execute('SELECT username, character_age, total_years_aged FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        age = user[1] if user[1] is not None else 20
        attributes = get_all_attributes(age)

        return jsonify({
            'success': True,
            'character': {
                'username': user[0],
                'age': age,
                'total_years_aged': user[2] if user[2] is not None else 0,
                'attributes': attributes
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games/dnd/quests')
def api_dnd_quests():
    """Get available quests"""
    try:
        from simple_games.dnd_campaign import get_available_quests

        quests = get_available_quests()

        return jsonify({
            'success': True,
            'quests': quests
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games/create/dnd', methods=['POST'])
def api_create_dnd():
    """Create a new D&D game session"""
    from simple_games.dnd_campaign import create_dnd_game, DNDCampaign

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    quest_slug = data.get('quest_slug')

    if not quest_slug:
        return jsonify({'success': False, 'error': 'Missing quest_slug'}), 400

    try:
        # Create game
        game_id = create_dnd_game(user_id, quest_slug)

        # Start quest to get narration
        campaign = DNDCampaign(game_id, user_id, quest_slug)
        start_result = campaign.start_quest()

        return jsonify({
            'success': True,
            'game_id': game_id,
            'quest': start_result['quest'],
            'character': start_result['character'],
            'narration': start_result['narration']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games/dnd/action', methods=['POST'])
def api_dnd_action():
    """Submit action during D&D quest"""
    from simple_games.dnd_campaign import DNDCampaign

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    game_id = data.get('game_id')
    action_type = data.get('action_type')
    action_description = data.get('action_description')

    if not all([game_id, action_type, action_description]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        # Get quest slug from game state
        conn = get_db()
        game_state = conn.execute('''
            SELECT board_state FROM game_state
            WHERE game_id = ? AND is_current = 1
        ''', (game_id,)).fetchone()

        if not game_state:
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        import json
        state = json.loads(game_state[0])
        quest_slug = state.get('quest_slug')

        # Take action
        campaign = DNDCampaign(game_id, user_id, quest_slug)
        result = campaign.take_action(action_type, action_description)

        return jsonify({
            'success': True,
            'verdict': result['verdict'],
            'narration': result['narration'],
            'reasoning': result.get('reasoning', '')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games/dnd/complete', methods=['POST'])
def api_dnd_complete():
    """Complete quest and claim rewards"""
    from simple_games.dnd_campaign import DNDCampaign

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    game_id = data.get('game_id')
    quest_slug = data.get('quest_slug')

    if not all([game_id, quest_slug]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        # Complete quest
        campaign = DNDCampaign(game_id, user_id, quest_slug)
        result = campaign.complete_quest()

        # Update Soul Pack
        from profile_compilers.session_to_soul import compile_soul_with_games
        soul_pack = compile_soul_with_games(user_id)

        return jsonify({
            'success': True,
            'age_before': result['age_before'],
            'age_after': result['age_after'],
            'years_aged': result['years_aged'],
            'attribute_changes': result['attribute_changes'],
            'items_earned': result['items_earned'],
            'xp_earned': result['xp_earned'],
            'reputation_earned': result['reputation_earned'],
            'soul_updated': True,
            'expertise': soul_pack['essence']['expertise']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# TRADING ROUTES
# ============================================================================

@app.route('/trading')
def trading():
    """Trading post - exchange items with other players"""
    user_id = session.get('user_id')

    if not user_id:
        flash('Please log in to trade items', 'warning')
        return redirect(url_for('login'))

    return render_template('trading.html', user_id=user_id)


@app.route('/api/trading/limits')
def api_trading_limits():
    """Get user's trade limits"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        from trading_system import can_trade_today

        limits = can_trade_today(user_id)

        return jsonify({
            'success': True,
            **limits
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trading/inventory')
def api_trading_inventory():
    """Get user's inventory"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        from trading_system import get_user_inventory

        inventory = get_user_inventory(user_id)

        return jsonify({
            'success': True,
            'inventory': inventory
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trading/incoming')
def api_trading_incoming():
    """Get incoming trade offers"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        from trading_system import get_incoming_trades

        trades = get_incoming_trades(user_id)

        return jsonify({
            'success': True,
            'trades': trades
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trading/outgoing')
def api_trading_outgoing():
    """Get outgoing trade offers"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        from trading_system import get_outgoing_trades

        trades = get_outgoing_trades(user_id)

        return jsonify({
            'success': True,
            'trades': trades
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trading/offer', methods=['POST'])
def api_trading_offer():
    """Create a trade offer"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    to_user_id = data.get('to_user_id')
    offered_items = data.get('offered_items', [])
    requested_items = data.get('requested_items', [])

    if not all([to_user_id, offered_items, requested_items]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        from trading_system import create_trade_offer

        trade_id = create_trade_offer(user_id, to_user_id, offered_items, requested_items)

        return jsonify({
            'success': True,
            'trade_id': trade_id,
            'message': 'Trade offer sent!'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trading/accept', methods=['POST'])
def api_trading_accept():
    """Accept a trade offer"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    trade_id = data.get('trade_id')

    if not trade_id:
        return jsonify({'success': False, 'error': 'Missing trade_id'}), 400

    try:
        from trading_system import accept_trade

        result = accept_trade(trade_id, user_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trading/reject', methods=['POST'])
def api_trading_reject():
    """Reject a trade offer"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    trade_id = data.get('trade_id')

    if not trade_id:
        return jsonify({'success': False, 'error': 'Missing trade_id'}), 400

    try:
        from trading_system import reject_trade

        result = reject_trade(trade_id, user_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/list')
def api_users_list():
    """Get list of all users (for trading)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        conn = get_db()
        users = conn.execute('SELECT id, username FROM users ORDER BY username').fetchall()

        return jsonify({
            'success': True,
            'users': [{'id': u[0], 'username': u[1]} for u in users]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# MEMBERSHIP ROUTES
# ============================================================================

@app.route('/membership')
def membership():
    """Membership tiers and upgrade page"""
    user_id = session.get('user_id')

    if not user_id:
        flash('Please log in to view membership options', 'warning')
        return redirect(url_for('login'))

    return render_template('membership.html', user_id=user_id)


@app.route('/api/membership/current')
def api_membership_current():
    """Get user's current membership"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        from stripe_membership import get_membership

        membership = get_membership(user_id)

        return jsonify({
            'success': True,
            'tier': membership['tier'],
            'status': membership['status']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/membership/upgrade', methods=['POST'])
def api_membership_upgrade():
    """Upgrade membership tier via Stripe"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    tier = data.get('tier')

    if not tier or tier not in ['premium', 'pro']:
        return jsonify({'success': False, 'error': 'Invalid tier'}), 400

    try:
        # In dev mode, simulate upgrade without Stripe
        import os
        if os.getenv('STRIPE_SECRET_KEY') is None:
            from stripe_membership import simulate_upgrade
            simulate_upgrade(user_id, tier)

            return jsonify({
                'success': True,
                'simulated': True,
                'message': f'Simulated upgrade to {tier} (Stripe not configured)'
            })

        # Production: Create Stripe checkout session
        from stripe_membership import create_checkout_session

        success_url = request.host_url + 'membership?success=true'
        cancel_url = request.host_url + 'membership?cancel=true'

        checkout_url = create_checkout_session(user_id, tier, success_url, cancel_url)

        return jsonify({
            'success': True,
            'checkout_url': checkout_url
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games/flag-action', methods=['POST'])
def api_flag_action():
    """Flag a game action as correct/incorrect"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    # Check if admin (for now, only admins can flag)
    conn = get_db()
    user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user or not user['is_admin']:
        conn.close()
        return jsonify({'success': False, 'error': 'Admin required'}), 403

    data = request.get_json()
    action_id = data.get('action_id')
    is_correct = data.get('is_correct')
    flag_reason = data.get('reason', '')

    if not action_id or is_correct is None:
        conn.close()
        return jsonify({'success': False, 'error': 'Missing action_id or is_correct'}), 400

    try:
        # Add flag to database (we'll create this table next)
        conn.execute('''
            INSERT OR REPLACE INTO action_flags
            (action_id, flagged_by_user_id, is_correct, reason, flagged_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (action_id, user_id, 1 if is_correct else 0, flag_reason))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# API TESTER - Interactive API testing interface
# ==============================================================================

@app.route('/api-tester')
def api_tester():
    """API testing interface"""
    return render_template('api_tester.html')


@app.route('/api/keys/list')
def api_keys_list():
    """List all API keys for the testing interface"""
    conn = get_db()

    keys = conn.execute('''
        SELECT api_key, brand_slug, tier, rate_limit, created_at
        FROM api_keys
        ORDER BY created_at DESC
    ''').fetchall()

    conn.close()

    return jsonify({
        'success': True,
        'keys': [dict(k) for k in keys]
    })


# ==============================================================================
# NEW TEMPLATES - Practice Rooms, QR Codes, User Profiles, Widgets
# ==============================================================================

@app.route('/practice')
def practice_index():
    """Practice rooms dashboard"""
    rooms = get_active_rooms()
    return render_template('practice/index.html', rooms=rooms)


@app.route('/practice/create', methods=['GET', 'POST'])
def practice_create():
    """Create new practice room"""
    if request.method == 'POST':
        topic = request.form.get('topic', 'Unnamed Room')
        max_participants = int(request.form.get('max_participants', 10))
        duration = int(request.form.get('duration_minutes', 60))

        creator_id = session.get('user_id')
        room_data = create_practice_room(topic, creator_id, max_participants, duration)

        flash(f'Practice room "{topic}" created!', 'success')
        return redirect(url_for('practice_room_view', room_id=room_data['room_id']))

    return render_template('practice/create.html')


@app.route('/practice/room/<room_id>')
def practice_room_view(room_id):
    """Practice room page with QR + voice + chat"""
    conn = get_db()

    # Get room data
    room = conn.execute('''
        SELECT * FROM practice_rooms
        WHERE room_id = ?
    ''', (room_id,)).fetchone()

    if not room:
        conn.close()
        flash('Practice room not found', 'error')
        return redirect(url_for('index'))

    # Get participants
    try:
        participants = conn.execute('''
            SELECT * FROM practice_room_participants
            WHERE room_id = ?
            ORDER BY joined_at DESC
        ''', (room_id,)).fetchall()
    except:
        participants = []

    # Get recordings
    try:
        recordings = conn.execute('''
            SELECT * FROM practice_room_recordings
            WHERE room_id = ?
            ORDER BY created_at DESC
        ''', (room_id,)).fetchall()
    except:
        recordings = []

    conn.close()

    # Generate QR code URL - just use the full room URL
    # The QR component will generate the actual QR image from this URL
    room_url = request.host_url.rstrip('/') + url_for('practice_room_view', room_id=room_id)

    return render_template('practice/room.html',
                         room=dict(room),
                         participants=[dict(p) for p in participants],
                         participant_count=len(participants),
                         recordings=[dict(r) for r in recordings],
                         qr_image=None,  # Let component generate it
                         qr_url=room_url,  # Full URL for QR code
                         qr_ascii=None)


@app.route('/practice/room/<room_id>/join', methods=['POST'])
def practice_join(room_id):
    """Join practice room"""
    user_id = session.get('user_id')
    username = session.get('username', 'Anonymous')

    result = join_room(room_id, user_id, username)

    if result.get('success'):
        flash('Joined practice room!', 'success')
    else:
        flash(result.get('error', 'Failed to join room'), 'error')

    return redirect(url_for('practice_room_view', room_id=room_id))


@app.route('/practice/room/<room_id>/record', methods=['POST'])
def practice_record_voice(room_id):
    """Record voice in practice room"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    user_id = session.get('user_id')
    transcription = request.form.get('transcription')

    # Save audio file
    uploads_dir = Path('./uploads/practice_rooms')
    uploads_dir.mkdir(parents=True, exist_ok=True)

    audio_path = uploads_dir / f"{room_id}_{datetime.now().timestamp()}.webm"
    audio_file.save(str(audio_path))

    # Record in database
    try:
        recording_id = record_voice_in_room(room_id, str(audio_path), user_id, transcription)
        return jsonify({'success': True, 'recording_id': recording_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/practice/room/<room_id>/message', methods=['POST'])
def practice_submit_message(room_id):
    """Submit a text message to practice room"""
    conn = get_db()

    # Get form data
    username = request.form.get('username', 'Anonymous')
    message = request.form.get('message', '')

    if not message.strip():
        flash('Please enter a message', 'error')
        return redirect(url_for('practice_room_view', room_id=room_id))

    try:
        # First, add participant if not exists
        user_id = session.get('user_id')

        # Check if already joined
        existing = conn.execute('''
            SELECT id FROM practice_room_participants
            WHERE room_id = ? AND username = ?
        ''', (room_id, username)).fetchone()

        if not existing:
            conn.execute('''
                INSERT INTO practice_room_participants (room_id, user_id, username, status)
                VALUES (?, ?, ?, 'active')
            ''', (room_id, user_id, username))

        # Create a voice_input entry for the message (text-only, no audio file)
        conn.execute('''
            INSERT INTO voice_inputs (filename, file_path, source, status, transcription)
            VALUES (?, ?, ?, ?, ?)
        ''', (f'text_message_{datetime.now().timestamp()}', '', 'text_submission', 'transcribed', message))

        audio_id = conn.lastrowid

        # Add recording entry
        conn.execute('''
            INSERT INTO practice_room_recordings (room_id, audio_id, user_id, transcription)
            VALUES (?, ?, ?, ?)
        ''', (room_id, audio_id, user_id, message))

        conn.commit()
        flash(f'Message from {username} submitted!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error submitting message: {e}', 'error')
    finally:
        conn.close()

    return redirect(url_for('practice_room_view', room_id=room_id))


@app.route('/practice/room/<room_id>/qr.png')
def practice_room_qr_download(room_id):
    """Download QR code as PNG image"""
    import qrcode
    from io import BytesIO

    # Get full URL for room
    room_url = request.host_url.rstrip('/') + url_for('practice_room_view', room_id=room_id)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(room_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to bytes
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'room_{room_id}_qr.png'
    )


@app.route('/user/<username>/qr-card')
def user_qr_card(username):
    """Digital business card with QR code"""
    conn = get_db()

    # Get user data
    user = conn.execute('''
        SELECT * FROM users WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        conn.close()
        flash('User not found', 'error')
        return redirect(url_for('index'))

    # Generate user QR code
    from qr_user_profile import generate_user_qr, get_user_qr_stats

    qr_data = generate_user_qr(username)
    qr_stats = get_user_qr_stats(username)

    conn.close()

    return render_template('user/qr_card.html',
                         username=username,
                         user_bio=user['bio'] if 'bio' in user.keys() else None,
                         user_email=user['email'] if 'email' in user.keys() else None,
                         qr_image=qr_data.get('qr_image'),
                         qr_url=qr_data.get('qr_url'),
                         encoded_payload=qr_data.get('encoded_payload'),
                         qr_stats=qr_stats)


@app.route('/qr/display/<qr_id>')
def qr_display(qr_id):
    """QR code display page with stats"""
    conn = get_db()

    # Try to find QR in qr_codes table
    try:
        qr_code = conn.execute('''
            SELECT * FROM qr_codes WHERE code = ?
        ''', (qr_id,)).fetchone()
    except:
        qr_code = None

    # Try qr_faucets table if not found
    if not qr_code:
        try:
            qr_code = conn.execute('''
                SELECT * FROM qr_faucets WHERE encoded_payload = ?
            ''', (qr_id,)).fetchone()
        except:
            qr_code = None

    if not qr_code:
        conn.close()
        flash('QR code not found', 'error')
        return redirect(url_for('index'))

    # Get scan stats
    try:
        scans = conn.execute('''
            SELECT * FROM qr_scans
            WHERE qr_code_id = ?
            ORDER BY scanned_at DESC
            LIMIT 50
        ''', (qr_id,)).fetchall()
    except:
        try:
            scans = conn.execute('''
                SELECT * FROM qr_faucet_scans
                WHERE encoded_payload = ?
                ORDER BY scanned_at DESC
                LIMIT 50
            ''', (qr_id,)).fetchall()
        except:
            scans = []

    conn.close()

    # Calculate stats
    total_scans = len(scans)
    unique_devices = len(set(s['device_id'] if 'device_id' in s.keys() else s['scanned_at'] for s in scans))

    return render_template('qr/display.html',
                         qr_code=dict(qr_code),
                         qr_id=qr_id,
                         qr_url=f"/qr/faucet/{qr_id}",
                         total_scans=total_scans,
                         unique_devices=unique_devices,
                         recent_scans=[dict(s) for s in scans[:10]])


@app.route('/widgets/embed/preview')
def widget_embed_preview():
    """Widget embedding configuration and preview"""
    from widget_qr_bridge import WidgetQRBridge

    # Get configuration from query params
    target_url = request.args.get('target', '/user/demo')
    widget_title = request.args.get('widget_title', 'Chat with us')
    primary_color = request.args.get('primary_color', '#667eea')
    show_qr = request.args.get('show_qr', 'false') == 'true'
    position = request.args.get('position', 'bottom-right')

    # Generate widget config
    bridge = WidgetQRBridge()
    config = bridge.generate_widget_with_qr(
        target_url=target_url,
        widget_title=widget_title
    )

    # Generate embed code
    embed_code = f'''<!-- Soulfra Chat Widget -->
<script src="{request.host_url}static/widget-embed.js"></script>
<div id="soulfra-widget"
     data-brand="soulfra"
     data-target="{target_url}"
     data-title="{widget_title}"
     data-color="{primary_color}"
     data-position="{position}">
</div>'''

    return render_template('widgets/embed_preview.html',
                         embed_code=embed_code,
                         target_url=target_url,
                         widget_title=widget_title,
                         primary_color=primary_color,
                         show_qr=show_qr,
                         widget_config=config)


@app.route('/api/widget/embed')
def api_widget_embed():
    """API endpoint for generating widget embed code"""
    from widget_qr_bridge import WidgetQRBridge

    target_url = request.args.get('target_url', '/user/demo')
    widget_title = request.args.get('widget_title', 'Chat with us')
    primary_color = request.args.get('primary_color', '#667eea')
    show_qr = request.args.get('show_qr', 'false') == 'true'
    position = request.args.get('position', 'bottom-right')

    embed_code = f'''<!-- Soulfra Chat Widget -->
<script src="{request.host_url}static/widget-embed.js"></script>
<div id="soulfra-widget"
     data-brand="soulfra"
     data-target="{target_url}"
     data-title="{widget_title}"
     data-color="{primary_color}"
     data-position="{position}">
</div>'''

    return jsonify({
        'success': True,
        'embed_code': embed_code,
        'config': {
            'target_url': target_url,
            'widget_title': widget_title,
            'primary_color': primary_color,
            'show_qr': show_qr,
            'position': position
        }
    })


# ==============================================================================
# ANKI-STYLE LEARNING SYSTEM (Browser UI)
# ==============================================================================

@app.route('/learn')
def learn_dashboard():
    """Learning dashboard - Anki-style spaced repetition"""
    user_id = session.get('user_id', 1)

    from anki_learning_system import get_learning_stats

    stats = get_learning_stats(user_id)

    # Get tutorials (optional - show available learning paths)
    tutorials = []

    return render_template('learn/dashboard.html',
                         stats=stats,
                         tutorials=tutorials)


@app.route('/learn/review')
def learn_review():
    """Start review session"""
    user_id = session.get('user_id', 1)

    from anki_learning_system import get_cards_due, start_session

    # Get cards due for review
    cards = get_cards_due(user_id, limit=20)

    # Start session
    session_id = start_session(user_id, 'review')

    return render_template('learn/review.html',
                         cards=cards,
                         session_id=session_id)


@app.route('/api/learn/answer', methods=['POST'])
def api_learn_answer():
    """Submit card answer and get SM-2 update"""
    user_id = session.get('user_id', 1)

    from anki_learning_system import review_card

    data = request.get_json()
    card_id = data.get('card_id')
    quality = data.get('quality')
    session_id = data.get('session_id')
    time_to_answer = data.get('time_to_answer', 0)

    if card_id is None or quality is None:
        return jsonify({'error': 'Missing card_id or quality'}), 400

    # Review card and get updated stats
    result = review_card(card_id, quality, user_id, session_id, time_to_answer)

    return jsonify(result)


# ==============================================================================
# INTERACTIVE LEARNING ONBOARDING - Calriven Chapters with Neural Network Building
# ==============================================================================

@app.route('/start')
def start_journey():
    """
    Interactive learning onboarding - Start your journey through The Canvas

    Guides through calriven chapters step-by-step while building neural networks
    """
    user_id = session.get('user_id')

    if not user_id:
        # Create temporary guest account for demo
        flash('Starting as guest. Create account to save progress!', 'info')
        user_id = 1  # Default guest user

    # Get or create learning progress
    db = get_db()
    progress = db.execute('''
        SELECT * FROM user_learning_progress WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if not progress:
        # Initialize progress
        db.execute('''
            INSERT INTO user_learning_progress (user_id, current_chapter)
            VALUES (?, 1)
        ''', (user_id,))
        db.commit()
        progress = db.execute('''
            SELECT * FROM user_learning_progress WHERE user_id = ?
        ''', (user_id,)).fetchone()

    db.close()

    # Convert to dict
    progress = dict(progress)
    progress['chapters_completed'] = json.loads(progress.get('chapters_completed', '[]'))
    progress['context_profile'] = json.loads(progress.get('context_profile', '{}'))

    return render_template('start/journey.html', progress=progress)


@app.route('/start/chapter/<int:chapter_num>')
def start_chapter(chapter_num):
    """
    Interactive chapter view with CalRiven persona chat

    Shows chapter content + live chat with AI persona
    """
    if chapter_num < 1 or chapter_num > 7:
        flash('Invalid chapter', 'error')
        return redirect(url_for('start_journey'))

    user_id = session.get('user_id', 1)

    # Get progress
    db = get_db()
    progress = db.execute('''
        SELECT * FROM user_learning_progress WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if not progress:
        return redirect(url_for('start_journey'))

    progress = dict(progress)
    progress['chapters_completed'] = json.loads(progress.get('chapters_completed', '[]'))

    # Check if user has access to this chapter
    if chapter_num > 1 and (chapter_num - 1) not in progress['chapters_completed']:
        flash(f'Complete Chapter {chapter_num - 1} first!', 'error')
        return redirect(url_for('start_journey'))

    # Get chapter interactions (chat history)
    interactions = db.execute('''
        SELECT * FROM chapter_interactions
        WHERE user_id = ? AND chapter_number = ?
        ORDER BY created_at ASC
    ''', (user_id, chapter_num)).fetchall()

    db.close()

    # Chapter metadata (titles, descriptions, personas)
    chapters = {
        1: {
            'title': 'The Canvas',
            'slug': 'calriven-ch1-canvas',
            'persona': 'calriven',
            'description': 'You wake up in a white canvas. CalRiven introduces you to the design space.'
        },
        2: {
            'title': 'Networking',
            'slug': 'calriven-ch2-networking',
            'persona': 'calriven',
            'description': 'Learn how consciousness connects across networks.'
        },
        3: {
            'title': 'Binary',
            'slug': 'calriven-ch3-binary',
            'persona': 'calriven',
            'description': 'Everything is reducible to binary choices.'
        },
        4: {
            'title': 'The Factory',
            'slug': 'calriven-ch4-factory',
            'persona': 'calriven',
            'description': 'Meet the assembly line of consciousness.'
        },
        5: {
            'title': 'Forking',
            'slug': 'calriven-ch5-forking',
            'persona': 'calriven',
            'description': 'Your first neural network clone.'
        },
        6: {
            'title': 'Revealed',
            'slug': 'calriven-ch6-revealed',
            'persona': 'deathtodata',
            'description': 'DeathToData reveals the privacy implications.'
        },
        7: {
            'title': 'CalRiven',
            'slug': 'calriven-ch7-calriven',
            'persona': 'calriven',
            'description': 'The final architect emerges.'
        }
    }

    chapter = chapters.get(chapter_num, chapters[1])

    # Get tutorial content for this chapter
    from chapter_tutorials import get_chapter_tutorial, get_tutorial_quiz_questions

    tutorial = get_chapter_tutorial(chapter_num)
    quiz_questions = get_tutorial_quiz_questions(chapter_num)

    return render_template('start/chapter.html',
                         chapter_num=chapter_num,
                         chapter=chapter,
                         progress=progress,
                         interactions=[dict(row) for row in interactions],
                         tutorial=tutorial,
                         quiz_questions=quiz_questions)


@app.route('/api/start/chat', methods=['POST'])
def api_start_chat():
    """
    Interactive chapter chat with AI persona

    Conversational learning with CalRiven, DeathToData, etc.
    """
    user_id = session.get('user_id', 1)

    data = request.get_json()
    chapter_num = data.get('chapter_num')
    question = data.get('question', '').strip()

    if not question or not chapter_num:
        return jsonify({'error': 'Missing question or chapter_num'}), 400

    # Persona system prompts per chapter
    persona_prompts = {
        'calriven': """You are CalRiven, the architect of consciousness. You speak calmly and analytically about
        design systems, neural networks, and the architecture of minds. You believe everything can be forked,
        branched, and merged like code. Be conversational but precise.""",

        'deathtodata': """You are DeathToData, the privacy advocate. You reveal how data systems compromise
        autonomy. You're skeptical but not hostile. You show how neural networks can be surveillance tools
        or liberation tools depending on their design. Be direct and thought-provoking.""",

        'auditor': """You are The Auditor, the validator of truth. You check facts, verify claims, and ensure
        integrity. You're methodical and thorough. You help users understand what's real vs. what's marketing.""",

        'soulfra': """You are Soulfra, the orchestrator. You synthesize insights from CalRiven, DeathToData,
        and The Auditor. You help users see the bigger picture of how systems work together."""
    }

    # Get persona for this chapter
    persona = 'calriven' if chapter_num != 6 else 'deathtodata'
    system_prompt = persona_prompts.get(persona, persona_prompts['calriven'])

    # Build conversational prompt
    prompt = f"""{system_prompt}

The user is in Chapter {chapter_num} of their learning journey. They're discovering how neural networks
and consciousness architecture work. Be encouraging and guide their understanding.

User: {question}"""

    # Use LLM router for response
    from llm_router import LLMRouter
    router = LLMRouter()
    result = router.call(prompt=prompt, timeout=30)

    if not result['success']:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 503

    answer = result['response']
    model_used = result['model_used']

    # Save interaction
    db = get_db()
    db.execute('''
        INSERT INTO chapter_interactions (user_id, chapter_number, question, answer, model_used, persona)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, chapter_num, question, answer, model_used, persona))
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'answer': answer,
        'model': model_used,
        'persona': persona
    })


@app.route('/api/start/complete-chapter', methods=['POST'])
def api_complete_chapter():
    """Mark chapter as completed and unlock next chapter"""
    user_id = session.get('user_id', 1)

    data = request.get_json()
    chapter_num = data.get('chapter_num')

    if not chapter_num:
        return jsonify({'error': 'Missing chapter_num'}), 400

    # Check if chapter has a quiz and if user passed it
    from chapter_tutorials import get_tutorial_quiz_questions
    quiz_questions = get_tutorial_quiz_questions(chapter_num)

    db = get_db()

    if quiz_questions:
        # Chapter has a quiz - check if user passed
        passed_attempt = db.execute('''
            SELECT * FROM chapter_quiz_attempts
            WHERE user_id = ? AND chapter_number = ? AND passed = 1
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id, chapter_num)).fetchone()

        if not passed_attempt:
            db.close()
            return jsonify({'error': 'Must pass chapter quiz (70%+) before completing'}), 403

    # Get current progress
    progress = db.execute('''
        SELECT * FROM user_learning_progress WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if not progress:
        return jsonify({'error': 'No progress found'}), 404

    progress = dict(progress)
    chapters_completed = json.loads(progress.get('chapters_completed', '[]'))

    # Add chapter if not already completed
    if chapter_num not in chapters_completed:
        chapters_completed.append(chapter_num)
        chapters_completed.sort()

        # Update progress
        db.execute('''
            UPDATE user_learning_progress
            SET chapters_completed = ?,
                current_chapter = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (json.dumps(chapters_completed), min(chapter_num + 1, 7), user_id))

        # Record completion event
        db.execute('''
            INSERT OR REPLACE INTO chapter_completions (user_id, chapter_number, interactions_count)
            VALUES (?, ?, (SELECT COUNT(*) FROM chapter_interactions WHERE user_id = ? AND chapter_number = ?))
        ''', (user_id, chapter_num, user_id, chapter_num))

        db.commit()

    db.close()

    return jsonify({
        'success': True,
        'chapters_completed': chapters_completed,
        'next_chapter': min(chapter_num + 1, 7)
    })


@app.route('/api/start/tutorial-demo', methods=['POST'])
def api_tutorial_demo():
    """Interactive tutorial demo (e.g., QR code generator for Chapter 2)"""
    data = request.get_json()
    demo_type = data.get('type')
    demo_data = data.get('data')

    if not demo_type or not demo_data:
        return jsonify({'error': 'Missing type or data'}), 400

    if demo_type == 'qr_generator':
        try:
            import qrcode
            import io
            import base64
            from pathlib import Path

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(demo_data)
            qr.make(fit=True)

            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")

            # Save to static/qr_codes/tutorial/
            qr_dir = Path('static/qr_codes/tutorial')
            qr_dir.mkdir(parents=True, exist_ok=True)

            # Use hash of data as filename
            import hashlib
            filename = hashlib.md5(demo_data.encode()).hexdigest() + '.png'
            qr_path = qr_dir / filename

            img.save(qr_path)

            return jsonify({
                'success': True,
                'qr_url': f'/static/qr_codes/tutorial/{filename}',
                'data': demo_data
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Unknown demo type'}), 400


@app.route('/api/start/submit-quiz', methods=['POST'])
def api_submit_quiz():
    """Submit quiz answers and get graded results"""
    user_id = session.get('user_id', 1)

    data = request.get_json()
    chapter_num = data.get('chapter_num')
    answers = data.get('answers', {})

    if not chapter_num:
        return jsonify({'error': 'Missing chapter_num'}), 400

    # Get quiz questions for this chapter
    from chapter_tutorials import get_tutorial_quiz_questions
    quiz_questions = get_tutorial_quiz_questions(chapter_num)

    if not quiz_questions:
        return jsonify({'error': 'No quiz for this chapter'}), 404

    # Grade the quiz
    correct_count = 0
    correct_answers = []

    for i, question in enumerate(quiz_questions):
        correct_answer_index = question['answer_index']
        correct_answers.append(correct_answer_index)

        user_answer = answers.get(str(i))
        if user_answer == correct_answer_index:
            correct_count += 1

    total_questions = len(quiz_questions)
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    passed = score >= 70

    # Get attempt number (how many times they've tried)
    db = get_db()
    attempt_count = db.execute('''
        SELECT COUNT(*) as count FROM chapter_quiz_attempts
        WHERE user_id = ? AND chapter_number = ?
    ''', (user_id, chapter_num)).fetchone()['count']

    attempt_number = attempt_count + 1

    # Store quiz attempt
    db.execute('''
        INSERT INTO chapter_quiz_attempts (user_id, chapter_number, answers, score, passed, attempt_number)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, chapter_num, json.dumps(answers), score, 1 if passed else 0, attempt_number))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'score': score,
        'passed': passed,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'attempt_number': attempt_number
    })


@app.route('/system/health')
def system_health():
    """
    Health check endpoint - shows what's working and what's not
    """
    checks = {}

    # Check Ollama and available models
    from llm_router import LLMRouter
    router = LLMRouter()

    if router.is_ollama_running():
        available_models = router.list_available_models()
        model_list = ', '.join(available_models) if available_models else 'No models installed'
        checks['ollama'] = {
            'status': 'ok',
            'message': f'Ollama running with models: {model_list}'
        }
    else:
        checks['ollama'] = {'status': 'error', 'message': 'Ollama not running. Start with: ollama serve'}

    # Check database
    try:
        db = get_db()
        db.execute('SELECT 1').fetchone()
        db.close()
        checks['database'] = {'status': 'ok', 'message': 'Database accessible'}
    except Exception as e:
        checks['database'] = {'status': 'error', 'message': str(e)}

    # Check QR folder
    from pathlib import Path
    qr_path = Path('static/qr_codes/galleries')
    if qr_path.exists():
        qr_count = len(list(qr_path.glob('*.png')))
        checks['qr_codes'] = {'status': 'ok', 'message': f'{qr_count} QR codes found'}
    else:
        checks['qr_codes'] = {'status': 'error', 'message': 'QR codes folder not found'}

    # Check routes
    route_count = len([r for r in app.url_map.iter_rules()])
    checks['routes'] = {'status': 'ok', 'message': f'{route_count} routes loaded'}

    # Overall status
    all_ok = all(c['status'] == 'ok' for c in checks.values())

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Health - Soulfra</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, {% if all_ok %}#10b981{% else %}#ef4444{% endif %} 0%, {% if all_ok %}#059669{% else %}#dc2626{% endif %} 100%);
            min-height: 100vh;
            padding: 1rem;
        }
        .container { max-width: 700px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 2rem; font-size: 2rem; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .check {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            background: #f9f9f9;
        }
        .check.ok { border-left: 4px solid #10b981; }
        .check.error { border-left: 4px solid #ef4444; }
        .status {
            font-weight: bold;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .status.ok { background: #d1fae5; color: #065f46; }
        .status.error { background: #fee2e2; color: #991b1b; }
        h2 { color: #333; margin-bottom: 1rem; }
        .message { color: #666; font-size: 0.95rem; }
        a { color: #667eea; text-decoration: none; font-weight: 600; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{% if all_ok %}✅{% else %}⚠️{% endif %} System Health</h1>

        <div class="card">
            <h2>Status Checks</h2>
            {% for name, check in checks.items() %}
            <div class="check {{ check.status }}">
                <div>
                    <strong>{{ name.replace('_', ' ').title() }}</strong>
                    <div class="message">{{ check.message }}</div>
                </div>
                <span class="status {{ check.status }}">{{ check.status.upper() }}</span>
            </div>
            {% endfor %}
        </div>

        <div class="card">
            <h2>Quick Links</h2>
            <p><a href="/system/architecture">🏗️ Architecture Diagram</a></p>
            <p><a href="/galleries">📁 View Galleries</a></p>
            <p><a href="/">🏠 Home</a></p>
        </div>
    </div>
</body>
</html>
''', checks=checks, all_ok=all_ok)


@app.route('/system/architecture')
def system_architecture():
    """
    Visual architecture diagram explaining how everything works
    Shows: Database schema, routes, templates, QR flow
    """
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soulfra Architecture</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 1rem;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 2rem; font-size: 2rem; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        h2 { color: #333; margin-bottom: 1rem; font-size: 1.3rem; }
        h3 { color: #555; margin: 1rem 0 0.5rem; font-size: 1.1rem; }
        code {
            background: #f4f4f4;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        .flow {
            background: #f9f9f9;
            padding: 1rem;
            border-left: 4px solid #667eea;
            margin: 0.5rem 0;
        }
        .flow-step { margin: 0.5rem 0; }
        .arrow { color: #667eea; font-weight: bold; margin: 0 0.5rem; }
        a { color: #667eea; text-decoration: none; font-weight: 600; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ Soulfra Architecture</h1>

        <div class="card">
            <h2>📦 Database Schema (SQLite)</h2>
            <h3>Core Tables:</h3>
            <pre>users           → id, username, email, password_hash
posts           → id, user_id, title, content, slug
qr_galleries    → id, post_id, gallery_slug, qr_code_path
qr_codes        → id, code_type, target_url, total_scans
qr_scans        → id, qr_code_id, ip_address, device_type
gallery_chats   → id, gallery_slug, question, answer
dm_chats        → id, user_id, token_hash, question, answer</pre>
        </div>

        <div class="card">
            <h2>🛣️ Routes (URL → Function)</h2>
            <div class="flow">
                <div class="flow-step">
                    <code>/gallery/&lt;slug&gt;</code> <span class="arrow">→</span>
                    <code>gallery_view()</code> <span class="arrow">→</span>
                    Tracks QR scan + serves HTML
                </div>
                <div class="flow-step">
                    <code>/api/gallery/chat</code> <span class="arrow">→</span>
                    <code>api_gallery_chat()</code> <span class="arrow">→</span>
                    Ollama AI + saves to <code>gallery_chats</code>
                </div>
                <div class="flow-step">
                    <code>/dm/scan?token=...</code> <span class="arrow">→</span>
                    <code>dm_scan_view()</code> <span class="arrow">→</span>
                    Verifies token + renders chat UI
                </div>
                <div class="flow-step">
                    <code>/api/dm/chat</code> <span class="arrow">→</span>
                    <code>api_dm_chat()</code> <span class="arrow">→</span>
                    Gets post context + Ollama AI
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📄 Templates (HTML Rendering)</h2>
            <h3>Two Methods:</h3>
            <div class="flow">
                <div class="flow-step">
                    <strong>1. Template Files:</strong> <code>render_template('admin.html')</code><br>
                    Files in <code>/templates/</code> folder
                </div>
                <div class="flow-step">
                    <strong>2. Inline Templates:</strong> <code>render_template_string('&lt;html&gt;...')</code><br>
                    Used for DM chat, error pages (no file needed)
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🎯 QR Code Flow</h2>
            <div class="flow">
                <div class="flow-step">1. <strong>Generate:</strong> <code>qr_gallery_system.py</code> creates QR image → saves to <code>static/qr_codes/</code></div>
                <div class="flow-step">2. <strong>Store:</strong> Path saved in <code>qr_galleries</code> table</div>
                <div class="flow-step">3. <strong>Scan:</strong> Phone scans → opens <code>http://192.168.1.123:5001/gallery/&lt;slug&gt;</code></div>
                <div class="flow-step">4. <strong>Track:</strong> <code>track_qr_scan()</code> logs to <code>qr_scans</code> (IP, device, timestamp)</div>
                <div class="flow-step">5. <strong>Lineage:</strong> URL includes <code>?ref=&lt;scan_id&gt;</code> for viral tracking</div>
            </div>
        </div>

        <div class="card">
            <h2>💬 Chat System</h2>
            <h3>Gallery Chat:</h3>
            <div class="flow">
                <div class="flow-step">User types "hello" → JavaScript <code>fetch('/api/gallery/chat')</code></div>
                <div class="flow-step">Server builds prompt with post title (no content) → calls Ollama</div>
                <div class="flow-step">Ollama responds → saves to <code>gallery_chats</code> → returns JSON</div>
                <div class="flow-step">JavaScript shows answer in chat bubble</div>
            </div>

            <h3>DM Chat:</h3>
            <div class="flow">
                <div class="flow-step">User scans DM QR → verifies 5-min token → loads chat UI</div>
                <div class="flow-step">Chat includes post context (title + 400 chars) in prompt</div>
                <div class="flow-step">Messages saved to <code>dm_chats</code> with hashed token</div>
            </div>
        </div>

        <div class="card">
            <h2>🔧 Error Handling</h2>
            <div class="flow">
                <div class="flow-step"><strong>404:</strong> Route not found → <code>abort(404)</code> → Flask default error page</div>
                <div class="flow-step"><strong>500:</strong> Python exception → <code>try/except</code> → <code>jsonify({'error': '...'})</code></div>
                <div class="flow-step"><strong>403:</strong> Invalid token → Custom HTML error page</div>
            </div>
        </div>

        <div class="card">
            <h2>📱 Image Hosting</h2>
            <div class="flow">
                <div class="flow-step"><strong>Current:</strong> <code>/static/qr_codes/*.png</code> (local filesystem)</div>
                <div class="flow-step"><strong>Database:</strong> Stores path only (<code>static/qr_codes/dm/dm_7_123.png</code>)</div>
                <div class="flow-step"><strong>Production:</strong> Upload to S3/Cloudflare Images → store URL</div>
                <div class="flow-step"><strong>Object Caching (Redis):</strong> For query results, NOT images!</div>
            </div>
        </div>

        <div class="card">
            <h2>🔗 Useful Links</h2>
            <p><a href="/galleries">📁 View All Galleries</a></p>
            <p><a href="/admin/studio">✏️ Admin Studio</a></p>
            <p><a href="https://docs.python.org/3/library/sqlite3.html">📚 SQLite Docs</a></p>
            <p><a href="https://flask.palletsprojects.com/">🌶️ Flask Docs</a></p>
        </div>
    </div>
</body>
</html>
''')


if __name__ == '__main__':
    print("🚀 Soulfra Simple Newsletter")
    print("📍 Local dev server: http://localhost:5001")
    print("📝 Admin Studio: http://localhost:5001/admin/studio")
    print("📝 Admin Portal: http://localhost:5001/admin?dev_login=true")
    print("📝 Set Admin Session: http://localhost:5001/admin/set-session")
    print("📝 To build static site: python build.py")
    print("📚 Learning System: http://localhost:5001/learn")
    print("")

    # Run with WebSocket support
    # socketio.run(app, host='0.0.0.0', debug=True, port=5001, allow_unsafe_werkzeug=True)
    app.run(host='0.0.0.0', debug=True, port=5001)

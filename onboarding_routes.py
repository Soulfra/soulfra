#!/usr/bin/env python3
"""
Onboarding Routes - Flask Blueprint

Complete web interface for:
- GitHub OAuth onboarding
- Creative challenges
- File import
- @brand routing

**Routes:**

GitHub OAuth:
- GET  /github/connect - Initiate GitHub OAuth
- GET  /github/callback - OAuth callback handler
- POST /github/refresh - Refresh API key

Creative Challenges:
- POST /api/challenge/generate - Generate new challenge
- POST /api/challenge/validate - Validate answer
- GET  /api/challenge/<id> - Get challenge details

File Import:
- POST /api/import - Upload and import file
- GET  /api/import/status/<file_id> - Check import status

Route Management:
- GET  /api/routes - List all routes
- GET  /api/routes/<route> - Get route details
- GET  /@<brand>/<path> - Serve content by route

**Usage in app.py:**
```python
from onboarding_routes import create_onboarding_blueprint

app.register_blueprint(create_onboarding_blueprint())
```
"""

from flask import Blueprint, request, redirect, jsonify, session, render_template_string, send_file
from werkzeug.utils import secure_filename
import os
from pathlib import Path

# Import our modules
from github_faucet import GitHubFaucet
from creative_onboarding import CreativeOnboarding
from file_importer import FileImporter
from folder_router import FolderRouter
from content_pipeline import ContentPipeline


# ==============================================================================
# CONFIG
# ==============================================================================

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


# ==============================================================================
# BLUEPRINT CREATION
# ==============================================================================

def create_onboarding_blueprint():
    """
    Create Flask blueprint for onboarding routes
    """
    bp = Blueprint('onboarding', __name__)

    # Initialize components
    github_faucet = GitHubFaucet()
    creative = CreativeOnboarding()
    importer = FileImporter()
    router = FolderRouter()
    pipeline = ContentPipeline()


    # ==========================================================================
    # GITHUB OAUTH ROUTES
    # ==========================================================================

    @bp.route('/github/connect')
    def github_connect():
        """Initiate GitHub OAuth flow"""
        # Get or create user_id from session
        user_id = session.get('user_id')

        if not user_id:
            # Create anonymous session
            user_id = 1  # Default anonymous user
            session['user_id'] = user_id

        # Generate OAuth URL
        auth_url = github_faucet.get_auth_url(user_id)

        return redirect(auth_url)


    @bp.route('/github/callback')
    def github_callback():
        """Handle GitHub OAuth callback"""
        code = request.args.get('code')
        state = request.args.get('state')

        if not code or not state:
            return jsonify({'error': 'Missing code or state'}), 400

        try:
            # Process callback
            result = github_faucet.process_callback(code, state)

            # Store API key in session
            session['api_key'] = result['api_key']
            session['tier'] = result['tier']
            session['github_username'] = result['github_username']

            # Render success page
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>GitHub Connected!</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                            max-width: 600px;
                            margin: 50px auto;
                            padding: 20px;
                            text-align: center;
                        }
                        .success {
                            background: #10b981;
                            color: white;
                            padding: 20px;
                            border-radius: 10px;
                            margin-bottom: 20px;
                        }
                        .key {
                            background: #f3f4f6;
                            padding: 15px;
                            border-radius: 5px;
                            font-family: monospace;
                            word-break: break-all;
                        }
                        .tier {
                            font-size: 2em;
                            margin: 20px 0;
                        }
                    </style>
                </head>
                <body>
                    <div class="success">
                        <h1>✅ GitHub Connected!</h1>
                        <p>Welcome, {{ username }}!</p>
                    </div>

                    <div class="tier">
                        Tier {{ tier }} Access
                    </div>

                    <p>Your API Key:</p>
                    <div class="key">{{ api_key }}</div>

                    <p style="margin-top: 30px;">
                        <a href="/">Go to Dashboard →</a>
                    </p>
                </body>
                </html>
            ''', **result)

        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @bp.route('/api/github/refresh', methods=['POST'])
    def github_refresh():
        """Refresh GitHub API key"""
        # Implementation for key refresh
        return jsonify({'message': 'Not yet implemented'}), 501


    # ==========================================================================
    # CREATIVE CHALLENGE ROUTES
    # ==========================================================================

    @bp.route('/api/challenge/generate', methods=['POST'])
    def challenge_generate():
        """Generate new creative challenge"""
        data = request.json or {}

        challenge_type = data.get('type', 'draw')
        difficulty = data.get('difficulty', 'easy')

        try:
            challenge = creative.generate_challenge(challenge_type, difficulty)

            # Store in session
            session['challenge_id'] = challenge['id']

            return jsonify(challenge)

        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @bp.route('/api/challenge/validate', methods=['POST'])
    def challenge_validate():
        """Validate challenge answer"""
        data = request.json or {}

        challenge_id = data.get('challenge_id') or session.get('challenge_id')
        user_answer = data.get('answer')
        user_id = session.get('user_id', 1)

        if not challenge_id or not user_answer:
            return jsonify({'error': 'Missing challenge_id or answer'}), 400

        try:
            result = creative.validate_challenge(
                challenge_id=challenge_id,
                user_answer=user_answer,
                user_id=user_id
            )

            # If passed, store API key in session
            if result['passed'] and result.get('api_key'):
                session['api_key'] = result['api_key']
                session['tier'] = result['tier']

            return jsonify(result)

        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @bp.route('/api/challenge/<challenge_id>')
    def challenge_get(challenge_id):
        """Get challenge details"""
        # Implementation to fetch challenge from database
        return jsonify({'message': 'Not yet implemented'}), 501


    # ==========================================================================
    # FILE IMPORT ROUTES
    # ==========================================================================

    @bp.route('/api/import', methods=['POST'])
    def file_import():
        """Upload and import file"""
        # Check authentication
        api_key = request.headers.get('X-API-Key') or session.get('api_key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        # Get file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        # Get parameters
        brand = request.form.get('brand')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        user_id = session.get('user_id', 1)

        if not brand or not category:
            return jsonify({'error': 'brand and category required'}), 400

        try:
            # Save uploaded file
            filename = secure_filename(file.filename)
            upload_path = Path(UPLOAD_FOLDER) / filename
            file.save(str(upload_path))

            # Process through pipeline
            result = pipeline.process_file(
                file_path=str(upload_path),
                brand=brand,
                category=category,
                user_id=user_id,
                subcategory=subcategory
            )

            # Clean up uploaded file
            upload_path.unlink()

            return jsonify(result)

        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @bp.route('/api/import/status/<int:file_id>')
    def import_status(file_id):
        """Check import status"""
        # Implementation to check processing status
        return jsonify({'message': 'Not yet implemented'}), 501


    # ==========================================================================
    # ROUTE MANAGEMENT
    # ==========================================================================

    @bp.route('/api/routes')
    def routes_list():
        """List all routes"""
        brand = request.args.get('brand')
        category = request.args.get('category')
        user_id = session.get('user_id')

        routes = router.list_routes(
            brand=brand,
            category=category,
            user_id=user_id
        )

        return jsonify({
            'routes': routes,
            'count': len(routes)
        })


    @bp.route('/api/routes/<path:route>')
    def route_get(route):
        """Get route details"""
        if not route.startswith('@'):
            route = f'@{route}'

        info = router.get_route_info(route)

        if not info:
            return jsonify({'error': 'Route not found'}), 404

        return jsonify(info)


    @bp.route('/api/brands')
    def brands_list():
        """List all brands"""
        brands = router.list_brands()

        return jsonify({
            'brands': brands,
            'count': len(brands)
        })


    @bp.route('/api/brands/<brand>')
    def brand_get(brand):
        """Get brand details"""
        stats = router.get_brand_stats(brand)
        categories = router.list_categories(brand)

        return jsonify({
            **stats,
            'categories': categories
        })


    # ==========================================================================
    # CONTENT SERVING
    # ==========================================================================

    @bp.route('/@<path:route>')
    def serve_route(route):
        """Serve content by @route"""
        route = f'@{route}'

        # Resolve route to file
        file_path = router.resolve_route(route)

        if not file_path:
            return jsonify({'error': f'Route not found: {route}'}), 404

        # Serve file
        return send_file(str(file_path))


    # ==========================================================================
    # DASHBOARD / ONBOARDING PAGE
    # ==========================================================================

    @bp.route('/onboard')
    def onboard_page():
        """Onboarding page with all options"""
        return render_template_string(ONBOARDING_PAGE_TEMPLATE)


    return bp


# ==============================================================================
# ONBOARDING PAGE TEMPLATE
# ==============================================================================

ONBOARDING_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Join Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 3em;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            opacity: 0.9;
            margin-bottom: 50px;
        }
        .options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .option {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .option:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-5px);
        }
        .option-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        .option-title {
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .option-description {
            opacity: 0.9;
            font-size: 0.95em;
        }
        .button {
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            text-decoration: none;
            display: inline-block;
        }
        .button:hover {
            background: #f3f4f6;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌌 Join Soulfra</h1>
        <p class="subtitle">Choose your path to access</p>

        <div class="options">
            <!-- GitHub OAuth -->
            <div class="option" onclick="window.location='/github/connect'">
                <div class="option-icon">🔐</div>
                <div class="option-title">GitHub OAuth</div>
                <div class="option-description">
                    Connect your GitHub account. Get tier based on your repos and followers.
                </div>
                <a href="/github/connect" class="button">Connect GitHub</a>
            </div>

            <!-- Draw Challenge -->
            <div class="option" onclick="startChallenge('draw')">
                <div class="option-icon">🎨</div>
                <div class="option-title">Draw Challenge</div>
                <div class="option-description">
                    Draw a word and we'll verify it with OCR. Quick and creative!
                </div>
                <button class="button" onclick="startChallenge('draw')">Draw Now</button>
            </div>

            <!-- Write Challenge -->
            <div class="option" onclick="startChallenge('write')">
                <div class="option-icon">✍️</div>
                <div class="option-title">Write Challenge</div>
                <div class="option-description">
                    Write a haiku, poem, or creative text. AI will judge your creativity.
                </div>
                <button class="button" onclick="startChallenge('write')">Write Now</button>
            </div>

            <!-- Solve Puzzle -->
            <div class="option" onclick="startChallenge('puzzle')">
                <div class="option-icon">🧩</div>
                <div class="option-title">Solve Puzzle</div>
                <div class="option-description">
                    Answer a logic puzzle or math question. Prove you're human!
                </div>
                <button class="button" onclick="startChallenge('puzzle')">Solve Now</button>
            </div>

            <!-- Upload File -->
            <div class="option" onclick="startChallenge('upload')">
                <div class="option-icon">📁</div>
                <div class="option-title">Upload File</div>
                <div class="option-description">
                    Upload a file about privacy, security, or digital rights. Instant access!
                </div>
                <button class="button" onclick="startChallenge('upload')">Upload Now</button>
            </div>
        </div>
    </div>

    <script>
        function startChallenge(type) {
            fetch('/api/challenge/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type: type, difficulty: 'easy'})
            })
            .then(r => r.json())
            .then(data => {
                alert('Challenge: ' + data.prompt);
                // TODO: Show challenge UI
            });
        }
    </script>
</body>
</html>
'''


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def require_api_key(f):
    """Decorator to require API key"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or session.get('api_key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        # Validate key
        faucet = GitHubFaucet()
        user = faucet.validate_api_key(api_key)

        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Add user to request context
        request.user = user

        return f(*args, **kwargs)

    return decorated_function


def require_tier(minimum_tier):
    """Decorator to require minimum tier"""
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_tier = session.get('tier', 0)

            if user_tier < minimum_tier:
                return jsonify({
                    'error': f'Tier {minimum_tier} required (you have tier {user_tier})'
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator

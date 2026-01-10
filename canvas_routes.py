#!/usr/bin/env python3
"""
Canvas Routes - Netflix-Style Entry & Workspace
Web UI for the Canvas Integration system
"""

from flask import render_template, render_template_string, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import json
from typing import Dict, Optional

from canvas_integration import (
    generate_canvas_qr,
    verify_canvas_pairing,
    complete_canvas_pairing,
    get_canvas_workspace,
    process_raw_idea,
    unlock_feature_for_user,
    generate_api_key_for_user,
    fork_brand_for_user
)
from database import get_db


def register_canvas_routes(app):
    """Register Canvas routes with Flask app"""

    # =============================================================================
    # CANVAS ENTRY - Netflix-Style QR Pairing
    # =============================================================================

    @app.route('/canvas')
    def canvas_entry():
        """
        Main Canvas entry point - Shows QR code for pairing

        Flow:
        1. Computer displays QR code
        2. User scans with phone
        3. Phone hits /canvas/pair/<token>
        4. Computer polls /canvas/pair/status
        5. When paired, redirect to /canvas/workspace
        """
        # Generate pairing QR
        user_id = session.get('user_id')  # None for guest
        pairing_data = generate_canvas_qr(user_id=user_id, ttl_minutes=5)

        # Get QR code URL (using QR faucet)
        qr_url = url_for('canvas_qr_image',
                         pairing_token=pairing_data['pairing_token'],
                         _external=True)

        return render_template_string(CANVAS_ENTRY_TEMPLATE,
            pairing_token=pairing_data['pairing_token'],
            qr_url=qr_url,
            expires_at=pairing_data['expires_at']
        )

    @app.route('/canvas/qr/<pairing_token>')
    def canvas_qr_image(pairing_token):
        """Generate QR code image for Canvas pairing"""
        from qr_faucet import generate_qr_code_image

        # Build pairing URL that phone will scan
        pair_url = url_for('canvas_pair',
                          pairing_token=pairing_token,
                          _external=True)

        # Generate QR code image
        img_data = generate_qr_code_image(pair_url)

        from flask import Response
        return Response(img_data, mimetype='image/png')

    @app.route('/canvas/pair/<pairing_token>')
    def canvas_pair(pairing_token):
        """
        Phone scans QR and hits this endpoint

        Flow:
        - Verify pairing token
        - If valid, complete pairing
        - Show success page on phone
        - Computer polls /canvas/pair/status and redirects to workspace
        """
        # Verify token
        pairing = verify_canvas_pairing(pairing_token)

        if not pairing:
            return render_template_string(CANVAS_PAIR_ERROR_TEMPLATE,
                error="Invalid or expired pairing code"
            ), 403

        # Get user (from session or create guest)
        user_id = session.get('user_id')

        if not user_id:
            # Create guest user or require login
            # For now, redirect to login
            session['canvas_redirect'] = pairing_token
            return redirect(url_for('login'))

        # Complete pairing
        success = complete_canvas_pairing(pairing_token, user_id)

        if not success:
            return render_template_string(CANVAS_PAIR_ERROR_TEMPLATE,
                error="Could not complete pairing"
            ), 500

        # Show success on phone
        return render_template_string(CANVAS_PAIR_SUCCESS_TEMPLATE,
            pairing_token=pairing_token
        )

    @app.route('/api/canvas/pair/status/<pairing_token>')
    def canvas_pair_status(pairing_token):
        """
        Computer polls this to check if phone has paired

        Returns:
        - {"status": "pending"} - Still waiting
        - {"status": "paired", "redirect": "/canvas/workspace"} - Paired!
        """
        db = get_db()

        pairing = db.execute('''
            SELECT * FROM canvas_pairing
            WHERE pairing_token = ?
        ''', (pairing_token,)).fetchone()

        db.close()

        if not pairing:
            return jsonify({'status': 'invalid'}), 404

        if pairing['status'] == 'paired':
            # Store user_id in session
            session['user_id'] = pairing['user_id']

            return jsonify({
                'status': 'paired',
                'redirect': url_for('canvas_workspace')
            })

        # Check if expired
        if datetime.now() > datetime.fromisoformat(pairing['expires_at']):
            return jsonify({'status': 'expired'}), 410

        return jsonify({'status': 'pending'})

    # =============================================================================
    # CANVAS WORKSPACE - User Dashboard
    # =============================================================================

    @app.route('/canvas/workspace')
    def canvas_workspace():
        """
        Main Canvas workspace - User's dashboard

        Shows:
        - Available chapters to learn
        - Forkable brands (CalRiven, DeathToData, etc.)
        - Current progress
        - Unlocked features
        - Raw ideas awaiting processing
        """
        user_id = session.get('user_id')

        if not user_id:
            flash('Please log in to access your workspace', 'warning')
            return redirect(url_for('login'))

        # Get workspace data
        workspace = get_canvas_workspace(user_id)

        return render_template_string(CANVAS_WORKSPACE_TEMPLATE,
            workspace=workspace,
            user_id=user_id
        )

    # =============================================================================
    # IDEA PROCESSOR - Raw Input → Structured Content
    # =============================================================================

    @app.route('/api/canvas/process-idea', methods=['POST'])
    def api_process_idea():
        """
        Process raw idea into structured content

        Request body:
        {
            "idea_text": "Raw user input",
            "brand_slug": "calriven" (optional)
        }

        Returns:
        {
            "post_id": 123,
            "title": "Generated Title",
            "slug": "generated-slug",
            "content": "Structured content",
            "status": "draft"
        }
        """
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()

        if not data or 'idea_text' not in data:
            return jsonify({'error': 'Missing idea_text'}), 400

        idea_text = data['idea_text']
        brand_slug = data.get('brand_slug')

        try:
            result = process_raw_idea(idea_text, user_id, brand_slug)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # =============================================================================
    # BRAND FORK DEPLOYER
    # =============================================================================

    @app.route('/api/canvas/fork-brand', methods=['POST'])
    def api_fork_brand():
        """
        Fork a brand (clone CalRiven, DeathToData, etc.)

        Request body:
        {
            "source_brand_slug": "calriven",
            "fork_name": "My Custom CalRiven"
        }

        Returns:
        {
            "brand_id": 5,
            "slug": "my-custom-calriven-a3f9",
            "name": "My Custom CalRiven",
            "source_brand": "CalRiven",
            "subdomain_url": "https://my-custom-calriven-a3f9.soulfra.com"
        }
        """
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()

        if not data or 'source_brand_slug' not in data or 'fork_name' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        source_brand_slug = data['source_brand_slug']
        fork_name = data['fork_name']

        try:
            result = fork_brand_for_user(user_id, source_brand_slug, fork_name)

            if 'error' in result:
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # =============================================================================
    # API KEY MANAGEMENT
    # =============================================================================

    @app.route('/api/canvas/generate-api-key', methods=['POST'])
    def api_generate_api_key():
        """
        Generate API key for user (unlocked after completing chapters)

        Returns:
        {
            "api_key": "sk_soulfra_...",
            "tier": "free"
        }
        """
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        # Check if user has unlocked API access
        from canvas_integration import check_feature_unlock

        if not check_feature_unlock(user_id, 'api_access'):
            return jsonify({
                'error': 'API access not unlocked',
                'hint': 'Complete chapters to unlock API access'
            }), 403

        try:
            api_key = generate_api_key_for_user(user_id)

            if not api_key:
                return jsonify({'error': 'Could not generate API key'}), 500

            return jsonify({
                'api_key': api_key,
                'tier': 'free'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # =============================================================================
    # TRACKING DASHBOARD - See ALL Your Data
    # =============================================================================

    @app.route('/canvas/tracking')
    def canvas_tracking():
        """
        Show EVERYTHING we're tracking about the user

        Complete transparency dashboard showing:
        - IP address, device, location
        - QR scans, sessions, timestamps
        - Progression tier, unlocks, stats
        - Narrative games, learning progress
        - Ideas processed, brands forked
        - Messages sent, posts created
        """
        from flask import request
        from progression_system import get_user_progress
        import hashlib

        user_id = session.get('user_id')

        # Get current request data
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        referrer = request.headers.get('Referer', '')

        # Device fingerprint
        fingerprint_str = f"{ip_address}:{user_agent}"
        device_fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

        # Get progression data
        progress = get_user_progress(user_id)

        # Get session data
        db = get_db()

        tracking_data = {
            'session': {
                'user_id': user_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'referrer': referrer,
                'device_fingerprint': device_fingerprint,
                'session_start': session.get('_created_at', 'Unknown')
            },
            'progression': progress,
            'qr_scans': [],
            'narrative_sessions': [],
            'learning_sessions': [],
            'anonymous_sessions': []
        }

        # Get QR scans
        if user_id:
            user_data = db.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
            if user_data:
                scans = db.execute('''
                    SELECT
                        s.*,
                        q.code_type,
                        q.target_url
                    FROM qr_scans s
                    LEFT JOIN qr_codes q ON s.qr_code_id = q.id
                    WHERE s.scanned_by_email = ?
                    ORDER BY s.scanned_at DESC
                    LIMIT 50
                ''', (user_data['email'],)).fetchall()
                tracking_data['qr_scans'] = [dict(s) for s in scans]

            # Narrative sessions
            narrative = db.execute('''
                SELECT
                    ns.*,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM narrative_sessions ns
                LEFT JOIN brands b ON ns.brand_id = b.id
                WHERE ns.user_id = ?
                ORDER BY ns.created_at DESC
            ''', (user_id,)).fetchall()
            tracking_data['narrative_sessions'] = [dict(n) for n in narrative]

            # Learning sessions
            learning = db.execute('''
                SELECT * FROM learning_sessions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
            ''', (user_id,)).fetchall()
            tracking_data['learning_sessions'] = [dict(l) for l in learning]

        # Anonymous sessions (all matching fingerprint)
        anon = db.execute('''
            SELECT * FROM anonymous_sessions
            WHERE device_fingerprint = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (device_fingerprint,)).fetchall()
        tracking_data['anonymous_sessions'] = [dict(a) for a in anon]

        db.close()

        return render_template_string(TRACKING_DASHBOARD_TEMPLATE,
            tracking_data=tracking_data,
            user_id=user_id
        )

    print("✅ Registered Canvas routes")


# =============================================================================
# HTML TEMPLATES
# =============================================================================

CANVAS_ENTRY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Canvas Entry - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 500px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        .qr-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin: 30px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .qr-code {
            max-width: 100%;
            height: auto;
        }
        .instructions {
            font-size: 1.1em;
            line-height: 1.6;
            margin: 20px 0;
        }
        .timer {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 20px;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Canvas Entry</h1>
        <p class="subtitle">Netflix-style pairing for your workspace</p>

        <div class="qr-container">
            <img src="{{ qr_url }}" alt="QR Code" class="qr-code" id="qrCode">
        </div>

        <div class="instructions">
            <p><strong>1.</strong> Open your phone camera</p>
            <p><strong>2.</strong> Scan the QR code above</p>
            <p><strong>3.</strong> Your workspace will open here</p>
        </div>

        <p class="timer">
            <span class="loading"></span>
            Waiting for scan...
        </p>
    </div>

    <script>
        // Poll for pairing status
        const pairingToken = "{{ pairing_token }}";

        function checkPairingStatus() {
            fetch(`/api/canvas/pair/status/${pairingToken}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'paired') {
                        window.location.href = data.redirect;
                    } else if (data.status === 'expired') {
                        alert('QR code expired. Please refresh to generate a new one.');
                    } else {
                        // Still pending, check again in 2 seconds
                        setTimeout(checkPairingStatus, 2000);
                    }
                })
                .catch(err => {
                    console.error('Polling error:', err);
                    setTimeout(checkPairingStatus, 2000);
                });
        }

        // Start polling
        setTimeout(checkPairingStatus, 2000);
    </script>
</body>
</html>
"""

CANVAS_PAIR_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Paired! - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            text-align: center;
            max-width: 400px;
        }
        .checkmark {
            font-size: 100px;
            animation: scaleIn 0.5s ease-out;
        }
        h1 {
            font-size: 2em;
            margin: 20px 0;
        }
        p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        @keyframes scaleIn {
            from {
                transform: scale(0);
                opacity: 0;
            }
            to {
                transform: scale(1);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="checkmark">✅</div>
        <h1>Successfully Paired!</h1>
        <p>Your workspace is now opening on your computer.</p>
        <p>You can close this tab.</p>
    </div>
</body>
</html>
"""

CANVAS_PAIR_ERROR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pairing Error - Soulfra</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            text-align: center;
            max-width: 400px;
        }
        .icon {
            font-size: 100px;
        }
        h1 {
            font-size: 2em;
            margin: 20px 0;
        }
        p {
            font-size: 1.2em;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Pairing Failed</h1>
        <p>{{ error }}</p>
    </div>
</body>
</html>
"""

CANVAS_WORKSPACE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Canvas Workspace - Soulfra</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #1a1a2e;
            border-radius: 15px;
            padding: 25px;
            border: 1px solid #333;
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .chapter-list, .brand-list, .idea-list {
            list-style: none;
        }
        .chapter-list li, .brand-list li, .idea-list li {
            background: #16213e;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .chapter-list li:hover, .brand-list li:hover, .idea-list li:hover {
            background: #1f2e4d;
            transform: translateX(5px);
        }
        .completed {
            opacity: 0.6;
        }
        .completed::after {
            content: " ✓";
            color: #38ef7d;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            margin: 10px 0;
            transition: all 0.3s;
        }
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .input-area {
            width: 100%;
            padding: 15px;
            background: #16213e;
            border: 1px solid #333;
            border-radius: 10px;
            color: #e0e0e0;
            font-family: inherit;
            font-size: 1em;
            margin: 10px 0;
            min-height: 100px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Canvas Workspace</h1>
        <p class="subtitle">Your creative command center</p>
    </div>

    <div class="grid">
        <!-- Learning Progress -->
        <div class="card">
            <h2>📚 Learning Path</h2>
            <p>Current Chapter: {{ workspace.learning.current_chapter }}</p>
            <p>Neural Network: {{ "Built ✓" if workspace.learning.neural_network_built else "Not Built" }}</p>
            <ul class="chapter-list">
                {% for i in range(1, 8) %}
                <li class="{% if i in workspace.learning.chapters_completed %}completed{% endif %}">
                    Chapter {{ i }}: Build Neural Network
                </li>
                {% endfor %}
            </ul>
        </div>

        <!-- Forkable Brands -->
        <div class="card">
            <h2>🍴 Forkable Brands</h2>
            <p>Clone and customize these brands</p>
            <ul class="brand-list">
                {% for brand in workspace.forkable_brands %}
                <li onclick="forkBrand('{{ brand.slug }}', '{{ brand.name }}')">
                    {{ brand.emoji }} {{ brand.name }}
                    <br><small>{{ brand.tagline }}</small>
                </li>
                {% endfor %}
            </ul>
        </div>

        <!-- Raw Ideas -->
        <div class="card">
            <h2>💡 Raw Ideas</h2>
            <p>Transform ideas into structured content</p>

            <textarea class="input-area" id="ideaInput" placeholder="Type your raw idea here..."></textarea>
            <button class="btn" onclick="processIdea()">🤖 Process with AI</button>

            {% if workspace.raw_ideas %}
            <ul class="idea-list">
                {% for idea in workspace.raw_ideas %}
                <li>
                    <strong>{{ idea.theme or "No theme" }}</strong>
                    <br>{{ idea.idea_text[:100] }}...
                    <br><small>{{ idea.created_at }}</small>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>

    <script>
        function processIdea() {
            const ideaText = document.getElementById('ideaInput').value;

            if (!ideaText.trim()) {
                alert('Please enter an idea first');
                return;
            }

            fetch('/api/canvas/process-idea', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    idea_text: ideaText,
                    brand_slug: 'calriven'
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert(`✅ Idea processed!\n\nTitle: ${data.title}\nPost ID: ${data.post_id}\n\nView at: /post/${data.slug}`);
                    document.getElementById('ideaInput').value = '';
                }
            })
            .catch(err => {
                alert('Error processing idea: ' + err);
            });
        }

        function forkBrand(slug, name) {
            const forkName = prompt(`Fork "${name}"?\n\nEnter your custom brand name:`);

            if (!forkName) return;

            fetch('/api/canvas/fork-brand', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    source_brand_slug: slug,
                    fork_name: forkName
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert(`🍴 Brand forked!\n\nNew Brand: ${data.name}\nSlug: ${data.slug}\nURL: ${data.subdomain_url}`);
                    location.reload();
                }
            })
            .catch(err => {
                alert('Error forking brand: ' + err);
            });
        }
    </script>
</body>
</html>
"""

TRACKING_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Your Data - Soulfra Tracking</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 30px;
            background: rgba(0, 255, 0, 0.05);
        }
        .section {
            border: 1px solid #00ff00;
            padding: 20px;
            margin-bottom: 20px;
            background: rgba(0, 255, 0, 0.02);
        }
        .section h2 { color: #00ffff; margin-bottom: 15px; font-size: 1.5em; }
        .data-grid {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin: 10px 0;
        }
        .label { color: #ffff00; font-weight: bold; }
        .value { color: #00ff00; word-break: break-all; }
        .tier-badge {
            display: inline-block;
            background: rgba(0, 255, 0, 0.2);
            border: 2px solid #00ff00;
            padding: 10px 20px;
            font-size: 1.5em;
            margin: 10px 0;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #00ff00;
            margin: 10px 0;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff00 0%, #00ffff 100%);
            transition: width 0.3s;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            font-weight: bold;
        }
        .list-item {
            background: rgba(0, 255, 0, 0.05);
            border-left: 3px solid #00ff00;
            padding: 10px;
            margin: 5px 0;
        }
        .timestamp { color: #888; font-size: 0.9em; }
        ul { list-style: none; }
        ul li::before { content: "▸ "; color: #00ff00; }
        .warning {
            color: #ff0000;
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid #ff0000;
            padding: 15px;
            margin: 20px 0;
        }
        a { color: #00ffff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 YOUR DIGITAL FOOTPRINT</h1>
            <p>Complete transparency. Everything we track about you.</p>
            {% if user_id %}
            <p>User ID: <span class="value">{{ user_id }}</span></p>
            {% else %}
            <p class="warning">⚠️ ANONYMOUS SESSION - Not logged in</p>
            {% endif %}
        </div>

        <!-- Current Session -->
        <div class="section">
            <h2>🔍 CURRENT SESSION</h2>
            <div class="data-grid">
                <div class="label">IP Address:</div>
                <div class="value">{{ tracking_data.session.ip_address }}</div>
                <div class="label">User Agent:</div>
                <div class="value">{{ tracking_data.session.user_agent }}</div>
                <div class="label">Device Fingerprint:</div>
                <div class="value">{{ tracking_data.session.device_fingerprint }}</div>
                <div class="label">Referrer:</div>
                <div class="value">{{ tracking_data.session.referrer or 'Direct' }}</div>
            </div>
        </div>

        <!-- Progression -->
        <div class="section">
            <h2>🏆 PROGRESSION TIER</h2>
            <div class="tier-badge">
                {{ tracking_data.progression.tier_icon }} {{ tracking_data.progression.tier_name }} (Tier {{ tracking_data.progression.current_tier }}/5)
            </div>
            <p>{{ tracking_data.progression.tier_description }}</p>
            <h3 style="margin-top: 20px; color: #00ffff;">Progress to Next Tier:</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ tracking_data.progression.progress_to_next }}%"></div>
                <div class="progress-text">{{ tracking_data.progression.progress_to_next|round }}%</div>
            </div>
            <h3 style="margin-top: 20px; color: #00ffff;">Stats:</h3>
            <div class="data-grid">
                <div class="label">Narrative Games:</div>
                <div class="value">{{ tracking_data.progression.stats.narrative_games_completed }} completed</div>
                <div class="label">Learning Chapters:</div>
                <div class="value">{{ tracking_data.progression.stats.chapters_completed }}/7 completed</div>
                <div class="label">QR Scans:</div>
                <div class="value">{{ tracking_data.progression.stats.qr_scans }}</div>
            </div>
            <h3 style="margin-top: 20px; color: #00ffff;">Unlocked Features:</h3>
            <ul>
                {% for feature in tracking_data.progression.unlocked_features %}
                <li>{{ feature }}</li>
                {% endfor %}
            </ul>
        </div>

        <!-- QR Scans -->
        <div class="section">
            <h2>📱 QR CODE SCANS ({{ tracking_data.qr_scans|length }})</h2>
            {% if tracking_data.qr_scans %}
            {% for scan in tracking_data.qr_scans[:10] %}
            <div class="list-item">
                <div class="data-grid">
                    <div class="label">Type:</div>
                    <div class="value">{{ scan.code_type }}</div>
                    <div class="label">Scanned At:</div>
                    <div class="value timestamp">{{ scan.scanned_at }}</div>
                    <div class="label">IP:</div>
                    <div class="value">{{ scan.ip_address }}</div>
                </div>
            </div>
            {% endfor %}
            {% else %}
            <p>No QR scans recorded yet.</p>
            {% endif %}
        </div>

        <!-- Actions -->
        <div class="section">
            <h2>⚡ ACTIONS</h2>
            <ul>
                <li><a href="/">← Back to Homepage</a></li>
                <li><a href="/canvas/workspace">Open Canvas Workspace</a></li>
                <li><a href="/me/export">Export All Data (JSON)</a></li>
            </ul>
        </div>

        <div class="warning">
            <strong>Privacy Notice:</strong> This page shows exactly what we track. Radical transparency. Export or delete anytime.
        </div>
    </div>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

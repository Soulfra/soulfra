"""
Status Routes - System visibility and navigation dashboard

Provides comprehensive system status and discoverability:
- /status - Main dashboard with tests, schemas, routes
- /status/tests - Run live tests
- /status/schemas - View database tables
- /status/routes - List all endpoints
- /sitemap.xml - Dynamic sitemap
- /robots.txt - SEO configuration
"""

from flask import Blueprint, render_template_string, jsonify, current_app
from database import get_db
import subprocess
import json
import os
from datetime import datetime

status_bp = Blueprint('status', __name__)


# ===========================================
# MAIN STATUS DASHBOARD
# ===========================================

STATUS_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Status - Soulfra</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }

        .container {
            max-width: 1400px;
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
            margin-bottom: 40px;
            font-size: 1.2em;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 30px;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }

        .card h2 {
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 0.5em;
            font-weight: 600;
            margin-left: 10px;
        }

        .status-ok {
            background: #51cf66;
            color: white;
        }

        .status-warn {
            background: #ffd43b;
            color: #333;
        }

        .status-error {
            background: #ff6b6b;
            color: white;
        }

        .stat-list {
            list-style: none;
        }

        .stat-list li {
            padding: 12px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .stat-label {
            font-weight: 600;
        }

        .stat-value {
            font-family: 'Courier New', monospace;
            opacity: 0.9;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin: 5px;
            display: inline-block;
            text-decoration: none;
            color: white;
        }

        .btn-primary {
            background: #51cf66;
        }

        .btn-primary:hover {
            background: #40c057;
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: #4c6ef5;
        }

        .btn-secondary:hover {
            background: #3b5bdb;
            transform: translateY(-2px);
        }

        .route-list {
            max-height: 400px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
        }

        .route-item {
            padding: 8px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        .route-category {
            font-weight: 600;
            color: #ffd43b;
            margin-top: 15px;
            margin-bottom: 5px;
        }

        .test-results {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
        }

        .test-pass {
            color: #51cf66;
        }

        .test-fail {
            color: #ff6b6b;
        }

        .loading {
            text-align: center;
            padding: 20px;
            font-size: 1.1em;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .back-home {
            text-align: center;
            margin-top: 30px;
        }

        .back-home a {
            color: white;
            text-decoration: none;
            font-size: 1.2em;
            opacity: 0.8;
        }

        .back-home a:hover {
            opacity: 1;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 System Status</h1>
        <p class="subtitle">Complete system visibility and diagnostics</p>

        <div class="grid">
            <!-- Database Status -->
            <div class="card">
                <h2>💾 Database <span class="status-badge status-ok">OK</span></h2>
                <ul class="stat-list">
                    <li>
                        <span class="stat-label">Tables:</span>
                        <span class="stat-value">{{ db_stats.table_count }}</span>
                    </li>
                    <li>
                        <span class="stat-label">Total Rows:</span>
                        <span class="stat-value">{{ db_stats.total_rows }}</span>
                    </li>
                    <li>
                        <span class="stat-label">Database Size:</span>
                        <span class="stat-value">{{ db_stats.db_size }}</span>
                    </li>
                </ul>
                <button class="btn btn-secondary" onclick="loadSchemas()">View Schemas</button>
            </div>

            <!-- Routes Status -->
            <div class="card">
                <h2>🛣️ Routes <span class="status-badge status-ok">{{ route_count }}</span></h2>
                <ul class="stat-list">
                    <li>
                        <span class="stat-label">Total Endpoints:</span>
                        <span class="stat-value">{{ route_count }}</span>
                    </li>
                    <li>
                        <span class="stat-label">API Endpoints:</span>
                        <span class="stat-value">{{ api_count }}</span>
                    </li>
                    <li>
                        <span class="stat-label">Admin Routes:</span>
                        <span class="stat-value">{{ admin_count }}</span>
                    </li>
                </ul>
                <button class="btn btn-secondary" onclick="loadRoutes()">View All Routes</button>
            </div>

            <!-- Neural Networks -->
            <div class="card">
                <h2>🧠 Neural Networks</h2>
                <ul class="stat-list">
                    <li>
                        <span class="stat-label">Trained Models:</span>
                        <span class="stat-value">{{ nn_stats.model_count }}</span>
                    </li>
                    <li>
                        <span class="stat-label">Training Images:</span>
                        <span class="stat-value">{{ nn_stats.training_images }}</span>
                    </li>
                    <li>
                        <span class="stat-label">User Drawings:</span>
                        <span class="stat-value">{{ nn_stats.user_drawings }}</span>
                    </li>
                </ul>
            </div>

            <!-- System Info -->
            <div class="card">
                <h2>⚙️ System Info</h2>
                <ul class="stat-list">
                    <li>
                        <span class="stat-label">Platform Version:</span>
                        <span class="stat-value">{{ system_info.version }}</span>
                    </li>
                    <li>
                        <span class="stat-label">Base URL:</span>
                        <span class="stat-value">{{ system_info.base_url }}</span>
                    </li>
                    <li>
                        <span class="stat-label">Ollama Host:</span>
                        <span class="stat-value">{{ system_info.ollama_host }}</span>
                    </li>
                </ul>
            </div>
        </div>

        <!-- Test Runner -->
        <div class="card">
            <h2>🧪 Test Runner</h2>
            <button class="btn btn-primary" onclick="runTests()">Run All Tests</button>
            <div id="testResults"></div>
        </div>

        <!-- Route Explorer (Hidden by default) -->
        <div class="card" id="routeExplorer" style="display: none;">
            <h2>🗺️ Route Map</h2>
            <div class="route-list" id="routeList"></div>
        </div>

        <!-- Schema Viewer (Hidden by default) -->
        <div class="card" id="schemaViewer" style="display: none;">
            <h2>📋 Database Schemas</h2>
            <div class="route-list" id="schemaList"></div>
        </div>

        <div class="back-home">
            <a href="/">← Back to Home</a>
        </div>
    </div>

    <script>
        async function runTests() {
            const resultsDiv = document.getElementById('testResults');
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div> Running tests...</div>';

            try {
                const response = await fetch('/status/tests');
                const data = await response.json();

                let html = '<div class="test-results">';
                html += `<div><strong>Tests Passed:</strong> ${data.passed}/${data.total}</div><br>`;

                if (data.results) {
                    data.results.forEach(test => {
                        const status = test.passed ? 'test-pass' : 'test-fail';
                        const icon = test.passed ? '✓' : '✗';
                        html += `<div class="${status}">${icon} ${test.test}</div>`;
                    });
                }

                if (data.error) {
                    html += `<div class="test-fail">Error: ${data.error}</div>`;
                }

                html += '</div>';
                resultsDiv.innerHTML = html;
            } catch (error) {
                resultsDiv.innerHTML = `<div class="test-results"><div class="test-fail">Error: ${error.message}</div></div>`;
            }
        }

        async function loadRoutes() {
            const explorer = document.getElementById('routeExplorer');
            const listDiv = document.getElementById('routeList');

            explorer.style.display = 'block';
            listDiv.innerHTML = '<div class="loading"><div class="spinner"></div> Loading routes...</div>';

            try {
                const response = await fetch('/status/routes');
                const data = await response.json();

                let html = '';
                for (const [category, routes] of Object.entries(data.routes)) {
                    html += `<div class="route-category">${category}</div>`;
                    routes.forEach(route => {
                        html += `<div class="route-item">${route}</div>`;
                    });
                }

                listDiv.innerHTML = html;
            } catch (error) {
                listDiv.innerHTML = `<div class="test-fail">Error: ${error.message}</div>`;
            }
        }

        async function loadSchemas() {
            const viewer = document.getElementById('schemaViewer');
            const listDiv = document.getElementById('schemaList');

            viewer.style.display = 'block';
            listDiv.innerHTML = '<div class="loading"><div class="spinner"></div> Loading schemas...</div>';

            try {
                const response = await fetch('/status/schemas');
                const data = await response.json();

                let html = '';
                data.tables.forEach(table => {
                    html += `<div class="route-category">${table.name} (${table.row_count} rows)</div>`;
                    table.columns.forEach(col => {
                        html += `<div class="route-item">${col.name}: ${col.type}</div>`;
                    });
                    html += '<br>';
                });

                listDiv.innerHTML = html;
            } catch (error) {
                listDiv.innerHTML = `<div class="test-fail">Error: ${error.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""


@status_bp.route('/status')
def status_dashboard():
    """Main status dashboard"""
    from config import PLATFORM_VERSION, BASE_URL, OLLAMA_HOST

    db = get_db()

    # Database stats
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_count = len(tables)

    total_rows = 0
    for table in tables:
        count = db.execute(f"SELECT COUNT(*) as cnt FROM {table['name']}").fetchone()
        total_rows += count['cnt']

    # Database file size
    db_path = db.execute("PRAGMA database_list").fetchone()['file']
    db_size = os.path.getsize(db_path) if db_path else 0
    db_size_mb = f"{db_size / 1024 / 1024:.2f} MB"

    # Neural network stats
    nn_models = db.execute("SELECT COUNT(*) as cnt FROM neural_networks").fetchone()
    training_images = db.execute("SELECT COUNT(*) as cnt FROM training_images").fetchone()
    user_drawings = db.execute("SELECT COUNT(*) as cnt FROM drawings").fetchone()

    db.close()

    # Route stats
    route_count = len([rule for rule in current_app.url_map.iter_rules()])
    api_count = len([rule for rule in current_app.url_map.iter_rules() if '/api/' in rule.rule])
    admin_count = len([rule for rule in current_app.url_map.iter_rules() if '/admin/' in rule.rule])

    return render_template_string(STATUS_DASHBOARD_TEMPLATE,
        db_stats={
            'table_count': table_count,
            'total_rows': total_rows,
            'db_size': db_size_mb
        },
        route_count=route_count,
        api_count=api_count,
        admin_count=admin_count,
        nn_stats={
            'model_count': nn_models['cnt'] if nn_models else 0,
            'training_images': training_images['cnt'] if training_images else 0,
            'user_drawings': user_drawings['cnt'] if user_drawings else 0
        },
        system_info={
            'version': PLATFORM_VERSION,
            'base_url': BASE_URL,
            'ollama_host': OLLAMA_HOST
        }
    )


# ===========================================
# API ENDPOINTS
# ===========================================

@status_bp.route('/status/tests')
def run_tests():
    """Run live tests and return results"""
    try:
        # Try to run test_everything.py if it exists
        if os.path.exists('test_everything.py'):
            result = subprocess.run(
                ['python3', 'test_everything.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Try to parse test_results.json if created
            if os.path.exists('test_results.json'):
                with open('test_results.json', 'r') as f:
                    data = json.load(f)
                    return jsonify({
                        'passed': data.get('tests_passed', 0),
                        'total': len(data.get('results', [])),
                        'results': data.get('results', []),
                        'timestamp': data.get('timestamp')
                    })

            # Otherwise return basic output
            return jsonify({
                'passed': 0 if result.returncode != 0 else 1,
                'total': 1,
                'results': [{'test': 'Test Suite', 'passed': result.returncode == 0}],
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': 'test_everything.py not found',
                'passed': 0,
                'total': 0,
                'results': []
            })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Tests timed out', 'passed': 0, 'total': 0})
    except Exception as e:
        return jsonify({'error': str(e), 'passed': 0, 'total': 0})


@status_bp.route('/status/schemas')
def get_schemas():
    """Get database table schemas"""
    db = get_db()

    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()

    result = []
    for table in tables:
        table_name = table['name']

        # Get column info
        columns = db.execute(f"PRAGMA table_info({table_name})").fetchall()

        # Get row count
        count = db.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()

        result.append({
            'name': table_name,
            'row_count': count['cnt'],
            'columns': [
                {
                    'name': col['name'],
                    'type': col['type'],
                    'notnull': bool(col['notnull']),
                    'pk': bool(col['pk'])
                }
                for col in columns
            ]
        })

    db.close()

    return jsonify({'tables': result})


@status_bp.route('/status/routes')
def get_routes():
    """Get all Flask routes categorized"""
    routes = {}

    for rule in current_app.url_map.iter_rules():
        route = rule.rule

        # Categorize routes
        if route.startswith('/api/'):
            category = 'API Endpoints'
        elif route.startswith('/admin/'):
            category = 'Admin Routes'
        elif route.startswith('/canvas/'):
            category = 'Canvas Routes'
        elif route.startswith('/cringeproof/'):
            category = 'Narrative Game Routes'
        elif route.startswith('/draw'):
            category = 'Drawing Routes'
        elif route.startswith('/learn'):
            category = 'Learning Routes'
        elif route.startswith('/status'):
            category = 'Status & Diagnostics'
        elif route.startswith('/static'):
            continue  # Skip static files
        else:
            category = 'Core Routes'

        if category not in routes:
            routes[category] = []

        routes[category].append(route)

    # Sort routes within each category
    for category in routes:
        routes[category].sort()

    return jsonify({'routes': routes})


# ===========================================
# SEO ROUTES
# ===========================================

@status_bp.route('/sitemap.xml')
def sitemap():
    """Dynamic sitemap generation"""
    from config import BASE_URL

    # Get all non-API, non-admin routes
    routes = []
    for rule in current_app.url_map.iter_rules():
        if not any(x in rule.rule for x in ['/api/', '/admin/', '/static/', '<']):
            routes.append(rule.rule)

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for route in sorted(routes):
        xml += '  <url>\n'
        xml += f'    <loc>{BASE_URL}{route}</loc>\n'
        xml += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
        xml += '    <changefreq>weekly</changefreq>\n'
        xml += '    <priority>0.8</priority>\n'
        xml += '  </url>\n'

    xml += '</urlset>'

    return current_app.response_class(xml, mimetype='application/xml')


@status_bp.route('/robots.txt')
def robots():
    """Robots.txt for SEO"""
    from config import BASE_URL

    txt = "User-agent: *\n"
    txt += "Allow: /\n"
    txt += "Disallow: /api/\n"
    txt += "Disallow: /admin/\n"
    txt += f"Sitemap: {BASE_URL}/sitemap.xml\n"

    return current_app.response_class(txt, mimetype='text/plain')


def register_status_routes(app):
    """Register status blueprint with Flask app"""
    app.register_blueprint(status_bp)
    print("✅ Registered status routes:")
    print("   - /status (System dashboard)")
    print("   - /status/tests (Test runner API)")
    print("   - /status/schemas (Database schema API)")
    print("   - /status/routes (Route map API)")
    print("   - /sitemap.xml (Dynamic sitemap)")
    print("   - /robots.txt (SEO configuration)")

#!/usr/bin/env python3
"""
Debug Routes - Local-only dashboard to see everything
NO external services, just local HTML showing your data
"""

from flask import Blueprint, render_template, jsonify, send_from_directory, request
from database import get_db
import os
from pathlib import Path

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug')
def debug_dashboard():
    """Main debug dashboard - visual overview of everything"""
    return send_from_directory('voice-archive', 'debug.html')


@debug_bp.route('/api/debug/lab-status')
def lab_status():
    """
    Show soulfra-lab status - all git repos, their remotes, and deployment state

    Returns info about:
    - Current repo (soulfra-simple)
    - GitHub Pages repo (soulfra.github.io)
    - Profile repo (soulfra/.github)
    - Git status (clean/dirty, branch, remote)
    """
    import subprocess
    import os
    from pathlib import Path

    def get_git_info(repo_path):
        """Get git status for a repository"""
        if not os.path.exists(os.path.join(repo_path, '.git')):
            return {'is_repo': False, 'path': repo_path}

        try:
            # Change to repo directory
            original_dir = os.getcwd()
            os.chdir(repo_path)

            # Get branch
            branch = subprocess.check_output(['git', 'branch', '--show-current'], stderr=subprocess.DEVNULL).decode().strip()

            # Get remote URL
            try:
                remote_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], stderr=subprocess.DEVNULL).decode().strip()
            except:
                remote_url = None

            # Get status (clean/dirty)
            status_output = subprocess.check_output(['git', 'status', '--porcelain'], stderr=subprocess.DEVNULL).decode()
            is_clean = len(status_output.strip()) == 0

            # Count untracked/modified files
            lines = [l for l in status_output.split('\n') if l.strip()]
            untracked = len([l for l in lines if l.startswith('??')])
            modified = len([l for l in lines if l.startswith(' M') or l.startswith('M ')])
            staged = len([l for l in lines if l.startswith('A ') or l.startswith('M')])

            # Get last commit
            try:
                last_commit = subprocess.check_output(['git', 'log', '-1', '--pretty=format:%h - %s (%ar)'], stderr=subprocess.DEVNULL).decode()
            except:
                last_commit = 'No commits yet'

            os.chdir(original_dir)

            return {
                'is_repo': True,
                'path': repo_path,
                'branch': branch,
                'remote_url': remote_url,
                'is_clean': is_clean,
                'untracked': untracked,
                'modified': modified,
                'staged': staged,
                'last_commit': last_commit
            }
        except Exception as e:
            os.chdir(original_dir)
            return {'is_repo': True, 'path': repo_path, 'error': str(e)}

    # Check all relevant repos
    repos = {
        'soulfra-simple (current)': os.getcwd(),
        'soulfra.github.io': '/Users/matthewmauer/Desktop/soulfra.github.io',
        'soulfra-lab': '/Users/matthewmauer/Desktop/soulfra-lab',
        'soulfra-dotgithub (profile)': os.path.join(os.getcwd(), 'soulfra-dotgithub')
    }

    repo_status = {}
    for name, path in repos.items():
        if os.path.exists(path):
            repo_status[name] = get_git_info(path)
        else:
            repo_status[name] = {'is_repo': False, 'path': path, 'exists': False}

    # Check if soulfra-lab symlinks are set up
    lab_path = '/Users/matthewmauer/Desktop/soulfra-lab'
    symlinks_status = {}
    if os.path.exists(lab_path):
        expected_symlinks = {
            'backend/api': os.getcwd(),
            'frontends/soulfra.github.io': '/Users/matthewmauer/Desktop/soulfra.github.io',
            'frontends/voice-archive': os.path.join(os.getcwd(), 'voice-archive')
        }

        for link_path, expected_target in expected_symlinks.items():
            full_path = os.path.join(lab_path, link_path)
            if os.path.islink(full_path):
                actual_target = os.readlink(full_path)
                symlinks_status[link_path] = {
                    'exists': True,
                    'target': actual_target,
                    'correct': os.path.abspath(actual_target) == os.path.abspath(expected_target)
                }
            else:
                symlinks_status[link_path] = {'exists': False, 'expected': expected_target}

    return jsonify({
        'success': True,
        'repos': repo_status,
        'symlinks': symlinks_status,
        'lab_path': lab_path,
        'lab_exists': os.path.exists(lab_path)
    })


@debug_bp.route('/api/debug/database')
def debug_database():
    """Get all database table counts and recent data"""
    db = get_db()

    # Get all table names
    tables_raw = db.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    ''').fetchall()

    tables = []
    for table in tables_raw:
        table_name = table['name']

        # Get count
        count = db.execute(f'SELECT COUNT(*) as count FROM {table_name}').fetchone()['count']

        # Get recent rows (limit 5)
        recent = db.execute(f'SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 5').fetchall()

        tables.append({
            'name': table_name,
            'count': count,
            'recent': [dict(row) for row in recent]
        })

    db.close()

    return jsonify({
        'success': True,
        'tables': tables
    })


@debug_bp.route('/api/debug/qr-codes')
def debug_qr_codes():
    """Get all shared responses with QR code URLs"""
    db = get_db()

    responses = db.execute('''
        SELECT id, response_text, source_type, crazy_level,
               view_count, created_at, content_hash
        FROM shared_responses
        ORDER BY created_at DESC
        LIMIT 50
    ''').fetchall()

    db.close()

    qr_data = [
        {
            'id': row['id'],
            'text_preview': row['response_text'][:100],
            'source': row['source_type'],
            'views': row['view_count'],
            'qr_url': f"/share/{row['id']}/qr.png",
            'share_url': f"/share/{row['id']}",
            'hash': row['content_hash'][:16] + '...',
            'created': row['created_at']
        }
        for row in responses
    ]

    return jsonify({
        'success': True,
        'qr_codes': qr_data
    })


@debug_bp.route('/api/debug/components')
def debug_components():
    """List all HTML components/pages available"""
    components_dir = Path('voice-archive')

    html_files = list(components_dir.glob('*.html'))

    components = []
    for html_file in html_files:
        name = html_file.stem
        route = f"/{name}" if name != 'index' else "/"

        # Try to extract title from file
        try:
            with open(html_file, 'r') as f:
                content = f.read(500)
                title_start = content.find('<title>') + 7
                title_end = content.find('</title>')
                title = content[title_start:title_end] if title_start > 6 else name.title()
        except:
            title = name.title()

        components.append({
            'name': name,
            'title': title,
            'route': route,
            'file_path': str(html_file)
        })

    return jsonify({
        'success': True,
        'components': components
    })


@debug_bp.route('/api/debug/routes')
def debug_routes():
    """List all Flask routes currently registered"""
    from flask import current_app

    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })

    return jsonify({
        'success': True,
        'routes': sorted(routes, key=lambda x: x['path'])
    })


@debug_bp.route('/api/debug/trace-route')
def trace_route():
    """
    Trace how a URL would be routed - like a circuit diagram for HTTP

    GET /api/debug/trace-route?url=/adaptive

    Returns full traceback showing:
    - All routes that could match
    - Which route wins (priority order)
    - Brand detection
    - Slug lookup attempts
    - Database queries
    - Why requests succeed/fail
    """
    from flask import current_app, request as flask_request
    from brand_router import detect_brand_from_request, get_brand_config
    import re

    # Get URL to trace
    test_url = flask_request.args.get('url', '/').strip()

    # Parse URL into components
    from urllib.parse import urlparse
    parsed = urlparse(test_url)
    path = parsed.path or '/'
    query_string = parsed.query or ''

    trace = {
        'url': test_url,
        'path': path,
        'query_string': query_string,
        'steps': []
    }

    # Step 1: Brand detection
    trace['steps'].append({
        'step': 1,
        'name': 'Brand Detection',
        'description': 'Determine which brand this request belongs to (domain-based routing)'
    })

    # Simulate brand detection
    host = flask_request.headers.get('Host', '192.168.1.87:5002')
    brand_slug = 'stpetepros'  # Default for localhost
    if 'calriven.com' in host:
        brand_slug = 'calriven'
    elif 'deathtodata.com' in host:
        brand_slug = 'deathtodata'
    elif 'soulfra.com' in host:
        brand_slug = 'soulfra'
    elif 'cringeproof.com' in host:
        brand_slug = 'cringeproof'

    brand_config = get_brand_config(brand_slug)
    trace['brand'] = {
        'slug': brand_slug,
        'name': brand_config['name'],
        'domain': brand_config['domain']
    }

    # Step 2: Route matching
    trace['steps'].append({
        'step': 2,
        'name': 'Route Matching',
        'description': 'Find all Flask routes that could handle this path'
    })

    matching_routes = []
    all_routes = []

    for rule in current_app.url_map.iter_rules():
        route_info = {
            'path': str(rule),
            'endpoint': rule.endpoint,
            'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'})),
            'matches': False,
            'priority': 0
        }

        # Check if route matches
        regex_pattern = str(rule).replace('<', '(?P<').replace('>', '>[^/]+)')
        regex_pattern = regex_pattern.replace('int:', '').replace('path:', '.+').replace('slug', 'slug')
        regex_pattern = f"^{regex_pattern}$"

        try:
            if re.match(regex_pattern, path):
                route_info['matches'] = True
                # Calculate priority (static routes = higher priority)
                if '<' not in str(rule):
                    route_info['priority'] = 100  # Static route
                else:
                    route_info['priority'] = 50 - str(rule).count('<')  # Dynamic route (fewer vars = higher priority)
                matching_routes.append(route_info)
        except:
            pass

        all_routes.append(route_info)

    # Sort matching routes by priority
    matching_routes.sort(key=lambda x: x['priority'], reverse=True)

    trace['matching_routes'] = matching_routes
    trace['winning_route'] = matching_routes[0] if matching_routes else None

    # Step 3: Slug detection (if catchall route matched)
    if trace['winning_route'] and '<slug>' in trace['winning_route']['path']:
        trace['steps'].append({
            'step': 3,
            'name': 'Slug Lookup',
            'description': 'Catchall /<slug> route matched - checking if slug exists in database'
        })

        # Extract slug from path
        slug = path.strip('/').split('/')[0] if '/' in path.strip('/') else path.strip('/')

        db = get_db()

        user = None
        profile = None
        schema_error = None

        # Check if it's a user slug (with schema validation)
        try:
            user = db.execute('SELECT id, username, user_slug FROM users WHERE user_slug = ?', (slug,)).fetchone()
        except Exception as e:
            schema_error = f"users table missing user_slug column: {str(e)}"

        # Check if it's a profile slug
        try:
            profile = db.execute('SELECT user_slug FROM user_profiles WHERE user_slug = ?', (slug,)).fetchone()
        except Exception as e:
            if not schema_error:
                schema_error = f"user_profiles table error: {str(e)}"

        trace['slug_lookup'] = {
            'slug': slug,
            'user_found': dict(user) if user else None,
            'profile_found': dict(profile) if profile else None,
            'will_404': not (user or profile),
            'schema_error': schema_error
        }

        db.close()

    # Step 4: Static file check
    if '.' in path:
        trace['steps'].append({
            'step': 4,
            'name': 'Static File Check',
            'description': 'Path contains a dot - checking if HTML file exists in voice-archive/'
        })

        filename = path.strip('/')
        import os
        file_path = os.path.join('voice-archive', filename)

        trace['static_file'] = {
            'filename': filename,
            'path': file_path,
            'exists': os.path.exists(file_path)
        }

    # Step 5: Diagnosis
    trace['steps'].append({
        'step': 5,
        'name': 'Diagnosis',
        'description': 'Final verdict on what happens to this request'
    })

    if not matching_routes:
        trace['diagnosis'] = {
            'status': 404,
            'message': 'No routes match this path',
            'suggestion': 'Add a route in one of the blueprint files'
        }
    elif trace['winning_route']['endpoint'] == 'user_page.user_page':
        if trace.get('slug_lookup', {}).get('will_404'):
            trace['diagnosis'] = {
                'status': 404,
                'message': f"Catchall /<slug> route matched, but slug '{trace.get('slug_lookup', {}).get('slug')}' not found in database",
                'suggestion': 'Either create a user with this slug, or add a specific route for this path'
            }
        else:
            trace['diagnosis'] = {
                'status': 200,
                'message': 'User/profile page will be served',
                'suggestion': 'Request will succeed'
            }
    elif trace['winning_route']['endpoint'].startswith('static'):
        trace['diagnosis'] = {
            'status': 200 if trace.get('static_file', {}).get('exists') else 404,
            'message': 'Static file handler matched',
            'suggestion': 'File will be served from voice-archive/ if it exists'
        }
    else:
        trace['diagnosis'] = {
            'status': 200,
            'message': f"Route matched: {trace['winning_route']['endpoint']}",
            'suggestion': 'Request will be handled by this endpoint'
        }

    return jsonify({
        'success': True,
        'trace': trace
    })


@debug_bp.route('/api/debug/voice-memos')
def debug_voice_memos():
    """
    Get recent voice memos with transcripts and vibe ratings

    GET /api/debug/voice-memos?limit=20
    Returns: voice recordings + transcripts + user feedback
    """
    limit = request.args.get('limit', 20, type=int)

    db = get_db()

    # Get recent voice recordings with transcripts
    recordings = db.execute('''
        SELECT
            id,
            user_id,
            audio_data,
            transcription,
            created_at,
            filename
        FROM simple_voice_recordings
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    result = []
    for rec in recordings:
        result.append({
            'id': rec['id'],
            'transcript': rec['transcription'] or 'No transcript yet',
            'domain': 'Unknown',  # Schema doesn't track domain
            'created_at': rec['created_at'],
            'vibe_rating': None,  # No vibe ratings linked to recordings yet
            'audio_size_kb': len(rec['audio_data']) // 1024 if rec['audio_data'] else 0
        })

    db.close()

    return jsonify({
        'success': True,
        'voice_memos': result,
        'total': len(result)
    })


@debug_bp.route('/api/debug/domain-status')
def debug_domain_status():
    """
    Get status of all domains (cringeproof, soulfra, calriven, deathtodata, stpetepros)

    GET /api/debug/domain-status
    Returns: domain health + voice memos + vibe scores
    """
    from brand_router import get_brand_config

    domains = ['cringeproof', 'soulfra', 'calriven', 'deathtodata', 'stpetepros']

    db = get_db()

    result = []
    for domain_slug in domains:
        config = get_brand_config(domain_slug)

        # Count voice recordings (total, since domain tracking not in schema)
        recordings_today = db.execute('''
            SELECT COUNT(*) as count
            FROM simple_voice_recordings
            WHERE created_at > datetime('now', '-1 day')
        ''').fetchone()['count']

        # Get average vibe score for all recent ratings (no domain link available)
        avg_vibe = db.execute('''
            SELECT AVG(vibe_score) as avg_score
            FROM vibe_ratings
            WHERE created_at > datetime('now', '-7 days')
        ''').fetchone()

        avg_vibe_score = round(avg_vibe['avg_score'], 1) if avg_vibe and avg_vibe['avg_score'] else None

        # Determine emoji based on vibe score
        vibe_emoji = '❓'
        if avg_vibe_score:
            if avg_vibe_score >= 4.5:
                vibe_emoji = '🔥'
            elif avg_vibe_score >= 3.5:
                vibe_emoji = '👍'
            elif avg_vibe_score >= 2.5:
                vibe_emoji = '😐'
            else:
                vibe_emoji = '😬'

        # Check if domain is "live" (has Flask route registered)
        from flask import current_app
        has_route = any(domain_slug in str(rule) for rule in current_app.url_map.iter_rules())

        status = '✅ Live' if has_route or recordings_today > 0 else '⚠️ Dev'

        result.append({
            'domain': config['name'],
            'slug': domain_slug,
            'status': status,
            'recordings_today': recordings_today,
            'avg_vibe_score': avg_vibe_score,
            'vibe_emoji': vibe_emoji,
            'tagline': config['tagline']
        })

    db.close()

    return jsonify({
        'success': True,
        'domains': result
    })


@debug_bp.route('/api/debug/service-health')
def debug_service_health():
    """
    Get health status of all services (Ollama, Whisper, Git, Database, Flask)

    GET /api/debug/service-health
    Returns: service health checks
    """
    import subprocess
    import requests

    health = {}

    # Check Ollama
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            health['ollama'] = {
                'status': '✅ Running',
                'models': [m['name'] for m in models],
                'model_count': len(models)
            }
        else:
            health['ollama'] = {'status': '❌ Error', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        health['ollama'] = {'status': '❌ Not Running', 'error': str(e)}

    # Check Database
    db_path = 'soulfra.db'
    if os.path.exists(db_path):
        db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        db = get_db()
        table_count = db.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'").fetchone()['count']

        # Get last write time
        last_write = db.execute('''
            SELECT MAX(created_at) as last_write
            FROM (
                SELECT created_at FROM simple_voice_recordings
                UNION ALL
                SELECT created_at FROM vibe_ratings
            )
        ''').fetchone()['last_write']

        db.close()

        health['database'] = {
            'status': '✅ Connected',
            'path': db_path,
            'size_mb': db_size_mb,
            'tables': table_count,
            'last_write': last_write or 'No data'
        }
    else:
        health['database'] = {'status': '❌ Not Found', 'path': db_path}

    # Check Git
    try:
        git_status = subprocess.check_output(['git', 'status', '--porcelain'], stderr=subprocess.DEVNULL).decode()
        is_clean = len(git_status.strip()) == 0

        branch = subprocess.check_output(['git', 'branch', '--show-current'], stderr=subprocess.DEVNULL).decode().strip()

        health['git'] = {
            'status': '✅ Clean' if is_clean else '⚠️ Dirty',
            'branch': branch,
            'uncommitted_files': len([l for l in git_status.split('\n') if l.strip()])
        }
    except Exception as e:
        health['git'] = {'status': '❌ Not a git repo', 'error': str(e)}

    # Flask uptime (fake for now, would need to track start time)
    health['flask'] = {
        'status': '✅ Running',
        'port': 5002,
        'https': True
    }

    return jsonify({
        'success': True,
        'health': health
    })


@debug_bp.route('/api/debug/ask-reasoning', methods=['POST'])
def ask_reasoning():
    """
    Ask the local reasoning engine (Ollama) a question

    POST /api/debug/ask-reasoning
    {
        "question": "Should I push soulfra-simple to GitHub?",
        "include_context": true  // Optional: include lab status as context
    }

    Returns:
    {
        "success": true,
        "response": "Cal's reasoning...",
        "model": "llama3.2:latest",
        "context_provided": true
    }
    """
    from ollama_soul import ask_ollama_with_soul
    import subprocess

    data = request.get_json() or {}
    question = data.get('question', '')
    include_context = data.get('include_context', True)

    if not question:
        return jsonify({
            'success': False,
            'error': 'No question provided'
        }), 400

    # Build context from lab status if requested
    context = ""
    if include_context:
        try:
            import requests
            from brand_router import get_brand_config

            context = "DEPLOYMENT ENVIRONMENT:\n\n"

            # 1. Git Repository Status
            repos = {
                'soulfra-simple (Flask backend)': os.getcwd(),
                'soulfra.github.io (Frontend)': '/Users/matthewmauer/Desktop/soulfra.github.io',
                'soulfra-lab (Local dev setup)': '/Users/matthewmauer/Desktop/soulfra-lab'
            }

            context += "GIT REPOSITORIES:\n"
            for name, path in repos.items():
                if os.path.exists(path) and os.path.exists(os.path.join(path, '.git')):
                    original_dir = os.getcwd()
                    os.chdir(path)

                    branch = subprocess.check_output(['git', 'branch', '--show-current'], stderr=subprocess.DEVNULL).decode().strip()
                    status_output = subprocess.check_output(['git', 'status', '--porcelain'], stderr=subprocess.DEVNULL).decode()
                    uncommitted = len([l for l in status_output.split('\n') if l.strip()])

                    try:
                        remote_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], stderr=subprocess.DEVNULL).decode().strip()
                    except:
                        remote_url = "No remote"

                    context += f"  {name}:\n"
                    context += f"    Branch: {branch}\n"
                    context += f"    Uncommitted files: {uncommitted}\n"
                    context += f"    Remote: {remote_url}\n"

                    os.chdir(original_dir)

            # 2. Ollama Service Status
            context += "\nOLLAMA AI MODELS:\n"
            try:
                ollama_resp = requests.get('http://localhost:11434/api/tags', timeout=2)
                if ollama_resp.status_code == 200:
                    models = ollama_resp.json().get('models', [])
                    context += f"  Status: ✅ Running ({len(models)} models loaded)\n"
                    context += f"  Models: {', '.join([m['name'] for m in models[:5]])}\n"
            except:
                context += "  Status: ❌ Not running\n"

            # 3. Database Status
            context += "\nDATABASE:\n"
            db_path = 'soulfra.db'
            if os.path.exists(db_path):
                db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
                db = get_db()
                table_count = db.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'").fetchone()['count']
                context += f"  File: {db_path}\n"
                context += f"  Size: {db_size_mb} MB\n"
                context += f"  Tables: {table_count}\n"

            # 4. Active Domains
            context += "\nACTIVE DOMAINS:\n"
            domains = ['cringeproof', 'soulfra', 'calriven', 'deathtodata', 'stpetepros']
            for domain_slug in domains:
                config = get_brand_config(domain_slug)
                status = '✅ Live' if domain_slug == 'cringeproof' else '⚠️ Dev'
                context += f"  {config['name']}: {status}\n"

            context += "\n"

        except Exception as e:
            context = f"(Failed to gather context: {e})\n\n"

    # Use Cal's specialized reasoning function (question FIRST, not buried in soul doc)
    try:
        from ollama_soul import ask_cal_reasoning

        response = ask_cal_reasoning(
            question=question,
            context=context,
            model='calos-model:latest'
        )

        return jsonify({
            'success': True,
            'response': response,
            'model': 'calos-model:latest',
            'context_provided': include_context and len(context) > 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Reasoning engine error: {str(e)}'
        }), 500


@debug_bp.route('/api/debug/github-repos')
def debug_github_repos():
    """
    Fetch all Soulfra GitHub repos from GitHub API

    Groups repos into:
    - Active: Pushed in last 30 days
    - Experiments: Older but not archived
    - Archived: Marked as archived

    Private repos shown as codenames for security
    """
    import requests
    from datetime import datetime, timedelta

    try:
        # Fetch from GitHub API (public repos only without auth)
        response = requests.get('https://api.github.com/users/Soulfra/repos?per_page=100', timeout=10)

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'GitHub API returned {response.status_code}'
            }), 500

        repos = response.json()

        # Group by activity
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)

        active = []
        experiments = []
        archived = []

        for repo in repos:
            # Parse last push date
            pushed_at = datetime.strptime(repo['pushed_at'], '%Y-%m-%dT%H:%M:%SZ') if repo.get('pushed_at') else None

            # Generate codename for private repos
            display_name = repo['name']
            if repo.get('private', False):
                # Hash the name for consistent codename
                import hashlib
                hash_val = hashlib.md5(repo['name'].encode()).hexdigest()[:4].upper()
                display_name = f"Project-{hash_val}"

            repo_info = {
                'name': display_name,
                'real_name': repo['name'] if not repo.get('private', False) else None,
                'description': repo.get('description', 'No description'),
                'url': repo['html_url'] if not repo.get('private', False) else None,
                'stars': repo.get('stargazers_count', 0),
                'language': repo.get('language', 'Unknown'),
                'pushed_at': repo.get('pushed_at'),
                'is_private': repo.get('private', False),
                'is_fork': repo.get('fork', False)
            }

            # Categorize
            if repo.get('archived', False):
                archived.append(repo_info)
            elif pushed_at and pushed_at > thirty_days_ago:
                active.append(repo_info)
            else:
                experiments.append(repo_info)

        # Sort each group by stars
        active.sort(key=lambda r: r['stars'], reverse=True)
        experiments.sort(key=lambda r: r['stars'], reverse=True)
        archived.sort(key=lambda r: r['stars'], reverse=True)

        return jsonify({
            'success': True,
            'total_repos': len(repos),
            'active': active,
            'experiments': experiments,
            'archived': archived,
            'fetched_at': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch GitHub repos: {str(e)}'
        }), 500

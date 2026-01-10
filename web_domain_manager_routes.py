"""
Web Domain Manager Routes

Web-based interface for managing domains, chatting with Ollama,
and building brand-specific sites.

Routes:
- /domains - List all domains + Ollama chat interface
- /domains/add - Add new domain with AI analysis
- /api/domains/chat - Chat API for Ollama conversations
- /api/domains/list - Get all domains (JSON)
- /api/domains/create - Create new domain (JSON)
"""

from flask import render_template, request, jsonify, g, make_response
from database import get_db
from llm_router import LLMRouter
import qrcode
from io import BytesIO
import base64
import os
import glob


def find_relevant_templates(message, domain=None):
    """
    Detect if user is asking for code examples and find relevant templates.

    Returns: dict with 'templates_found' and 'template_code'
    """
    # Keywords that suggest user wants code examples
    code_request_keywords = [
        'how do i build', 'show me', 'example', 'template', 'code for',
        'how to create', 'starter', 'sample', 'boilerplate'
    ]

    message_lower = message.lower()
    wants_code = any(keyword in message_lower for keyword in code_request_keywords)

    if not wants_code:
        return {'templates_found': [], 'template_code': ''}

    # Template categories to search
    template_searches = {
        'signup': ['signup', 'register', 'sign up', 'registration'],
        'login': ['login', 'signin', 'sign in', 'authentication', 'auth'],
        'dashboard': ['dashboard', 'admin', 'panel', 'control'],
        'membership': ['membership', 'subscription', 'pricing', 'plans'],
        'profile': ['profile', 'user page', 'account'],
        'directory': ['directory', 'listing', 'professionals', 'service'],
        'blog': ['blog', 'post', 'article', 'content'],
        'form': ['form', 'submit', 'input', 'contact'],
        'qr': ['qr', 'qr code', 'scanner'],
        'chat': ['chat', 'messaging', 'conversation']
    }

    templates_found = []
    template_code = ""
    base_path = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_path, 'templates')

    # Find matching templates
    for template_name, keywords in template_searches.items():
        if any(kw in message_lower for kw in keywords):
            # Look for template files
            pattern = os.path.join(templates_dir, f'*{template_name}*.html')
            files = glob.glob(pattern)

            if files:
                # Read first matching template (limit to 100 lines for context)
                try:
                    with open(files[0], 'r') as f:
                        lines = f.readlines()[:100]  # First 100 lines
                        code = ''.join(lines)
                        templates_found.append(os.path.basename(files[0]))
                        template_code += f"\n\n=== Example from {os.path.basename(files[0])} ===\n{code}\n"
                except Exception:
                    pass

    return {
        'templates_found': templates_found,
        'template_code': template_code
    }


def register_web_domain_manager_routes(app):
    """Register domain manager routes with Flask app"""

    @app.route('/domains')
    def domains_manager():
        """
        Web interface for domain management + Ollama chat

        Shows:
        - List of all domains in database
        - AI chat interface to discuss domains, files, docs
        - Add new domain with AI analysis
        """
        db = get_db()
        brands = db.execute('''
            SELECT id, name, slug, domain, tagline, category, network_role, created_at
            FROM brands
            ORDER BY created_at DESC
        ''').fetchall()

        # Filter to only show domains with folders
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        domains_dir = os.path.join(base_dir, 'domains')

        filtered_brands = []
        for brand in brands:
            domain_path = os.path.join(domains_dir, brand['slug'])
            if os.path.exists(domain_path):
                filtered_brands.append(brand)

        # Choose template version - default to classic (has working preview + Ollama)
        view = request.args.get('view', 'classic')  # unified, enhanced, classic

        template_map = {
            'unified': 'domain_manager_unified.html',
            'enhanced': 'domain_manager_enhanced.html',
            'classic': 'domain_manager.html'
        }

        template = template_map.get(view, 'domain_manager.html')

        # Add cache-busting headers to prevent browser caching
        response = make_response(render_template(template, brands=filtered_brands))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/api/domains/list')
    def api_domains_list():
        """Get all domains (JSON API)"""
        db = get_db()
        brands = db.execute('''
            SELECT id, name, slug, domain, tagline, category, created_at
            FROM brands
            ORDER BY created_at DESC
        ''').fetchall()

        return jsonify({
            'success': True,
            'domains': [dict(b) for b in brands]
        })

    @app.route('/api/domains/create', methods=['POST'])
    def api_domains_create():
        """
        Create new domain with AI analysis

        POST JSON:
        {
            "domain": "example.com"
        }

        Returns:
        {
            "success": true,
            "brand_id": 5,
            "ai_analysis": {...},
            "qr_code": "data:image/png;base64,..."
        }
        """
        data = request.get_json()
        domain = data.get('domain', '').strip()

        if not domain:
            return jsonify({'success': False, 'error': 'Domain required'}), 400

        # Ask AI for suggestions
        router = LLMRouter()
        prompt = f"""Analyze this domain and suggest:
1. What industry/niche would work best?
2. What geographic regions or languages for SEO?
3. Brief content strategy (1-2 sentences)

Domain: {domain}

Respond in this exact format:
Industry: [your suggestion]
Region: [your suggestion]
Strategy: [your suggestion]"""

        result = router.call(prompt, temperature=0.7)

        if not result['success']:
            return jsonify({
                'success': False,
                'error': 'AI analysis failed',
                'details': result.get('error', 'Unknown error')
            }), 500

        response = result['response']

        # Parse AI response
        industry = "general"
        region = "global"
        strategy = "content marketing"

        for line in response.split('\n'):
            if 'Industry:' in line or 'industry:' in line.lower():
                industry = line.split(':', 1)[1].strip()[:100]
            elif 'Region:' in line or 'region:' in line.lower():
                region = line.split(':', 1)[1].strip()[:100]
            elif 'Strategy:' in line or 'strategy:' in line.lower():
                strategy = line.split(':', 1)[1].strip()[:200]

        # Generate slug from domain
        slug = domain.replace('.com', '').replace('.', '-').replace('www-', '')

        # Generate brand name (capitalize slug)
        name = slug.replace('-', ' ').title()

        # Insert into database
        db = get_db()
        try:
            cursor = db.execute('''
                INSERT INTO brands (name, slug, domain, tagline, category, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (name, slug, domain, f"{region}: {strategy[:200]}", industry))

            db.commit()
            brand_id = cursor.lastrowid

            # Generate QR code
            qr_url = f"https://{domain}/qr/faucet/login-{slug}"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')

            return jsonify({
                'success': True,
                'brand_id': brand_id,
                'name': name,
                'slug': slug,
                'domain': domain,
                'ai_analysis': {
                    'industry': industry,
                    'region': region,
                    'strategy': strategy,
                    'full_response': response,
                    'model_used': result['model_used']
                },
                'qr_code': f"data:image/png;base64,{qr_base64}",
                'qr_url': qr_url
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Database error',
                'details': str(e)
            }), 500

    @app.route('/api/domains/preview', methods=['POST'])
    def api_domains_preview():
        """
        Preview domain HTML by fetching from localhost with Host header override

        POST JSON:
        {
            "domain": "stpetepros.com"
        }

        Returns:
        {
            "success": true,
            "html": "...",
            "brand_info": {...}
        }
        """
        import requests

        data = request.get_json()
        domain = data.get('domain', '').strip()

        if not domain:
            return jsonify({'success': False, 'error': 'Domain required'}), 400

        # Get brand info from database
        db = get_db()
        brand = db.execute('SELECT * FROM brands WHERE domain = ?', (domain,)).fetchone()

        if not brand:
            return jsonify({'success': False, 'error': 'Domain not found in database'}), 404

        # Fetch HTML by making request to localhost with Host header override
        try:
            response = requests.get(
                'http://localhost:5001/',
                headers={'Host': domain},
                timeout=5
            )

            return jsonify({
                'success': True,
                'html': response.text,
                'status_code': response.status_code,
                'brand_info': {
                    'name': brand['name'],
                    'slug': brand['slug'],
                    'domain': brand['domain'],
                    'category': brand['category'],
                    'tagline': brand['tagline']
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch domain HTML',
                'details': str(e)
            }), 500

    @app.route('/api/domains/scrape-live', methods=['POST'])
    def api_domains_scrape_live():
        """
        Scrape the ACTUAL live website from the real domain

        POST JSON:
        {
            "domain": "stpetepros.com"
        }

        Returns:
        {
            "success": true,
            "html": "...",
            "sitemap": "...",
            "robots": "...",
            "dns_info": {...},
            "brand_info": {...}
        }
        """
        import requests as req
        import subprocess
        import urllib3

        # Suppress SSL warnings (we're using verify=False for scraping)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        data = request.get_json()
        domain = data.get('domain', '').strip()

        if not domain:
            return jsonify({'success': False, 'error': 'Domain required'}), 400

        # Get brand info from database
        db = get_db()
        brand = db.execute('SELECT * FROM brands WHERE domain = ?', (domain,)).fetchone()

        if not brand:
            return jsonify({'success': False, 'error': 'Domain not found in database'}), 404

        result = {
            'success': True,
            'domain': domain,
            'brand_info': {
                'name': brand['name'],
                'slug': brand['slug'],
                'category': brand['category'],
                'tagline': brand['tagline']
            }
        }

        # Fetch live HTML (try primary domain, then .github.io fallback)
        try:
            response = req.get(f'https://{domain}', timeout=10, allow_redirects=True, verify=False)
            result['html'] = response.text
            result['status_code'] = response.status_code
            result['final_url'] = response.url  # Show if redirected
            result['headers'] = dict(response.headers)
            result['ssl_warning'] = 'SSL verification disabled for scraping'
        except Exception as e:
            # Try .github.io fallback
            github_domain = f"{brand['slug']}.github.io"
            try:
                response = req.get(f'https://{github_domain}', timeout=10, allow_redirects=True, verify=False)
                result['html'] = response.text
                result['status_code'] = response.status_code
                result['final_url'] = response.url
                result['headers'] = dict(response.headers)
                result['ssl_warning'] = 'SSL verification disabled for scraping'
                result['fallback_used'] = f'Primary domain failed, fetched from {github_domain}'
            except Exception as e2:
                result['html_error'] = f"Primary: {str(e)}\nFallback ({github_domain}): {str(e2)}"
                result['html'] = f"<!-- Error fetching live site: {str(e)} -->"

        # Fetch sitemap.xml
        try:
            sitemap_response = req.get(f'https://{domain}/sitemap.xml', timeout=5, verify=False)
            if sitemap_response.status_code == 200:
                result['sitemap'] = sitemap_response.text
            else:
                result['sitemap'] = f"<!-- Not found (HTTP {sitemap_response.status_code}) -->"
        except Exception as e:
            result['sitemap'] = f"<!-- Error: {str(e)} -->"

        # Fetch robots.txt
        try:
            robots_response = req.get(f'https://{domain}/robots.txt', timeout=5, verify=False)
            if robots_response.status_code == 200:
                result['robots'] = robots_response.text
            else:
                result['robots'] = f"# Not found (HTTP {robots_response.status_code})"
        except Exception as e:
            result['robots'] = f"# Error: {str(e)}"

        # Get DNS info (dig)
        try:
            dig_output = subprocess.run(
                ['dig', domain, '+short'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if dig_output.returncode == 0:
                ips = dig_output.stdout.strip().split('\n')
                result['dns_ips'] = [ip for ip in ips if ip]

                # Identify hosting
                if any('185.199.' in ip for ip in ips):
                    result['hosting'] = 'GitHub Pages'
                elif any('amazonaws.com' in ip or ip.startswith('3.') or ip.startswith('15.') for ip in ips):
                    result['hosting'] = 'AWS'
                elif any('digitalocean' in ip or ip.startswith('138.197.') for ip in ips):
                    result['hosting'] = 'DigitalOcean'
                else:
                    result['hosting'] = 'Unknown'
            else:
                result['dns_error'] = dig_output.stderr
        except Exception as e:
            result['dns_error'] = str(e)

        return jsonify(result)

    @app.route('/api/domains/chat', methods=['POST'])
    def api_domains_chat():
        """
        Chat with Ollama about domains, files, docs, etc.

        POST JSON:
        {
            "message": "How do I build stpetepros.com?",
            "context": {
                "domain": "stpetepros.com",
                "file_content": "...",  // optional
                "history": [...]  // optional
            }
        }

        Returns:
        {
            "success": true,
            "response": "...",
            "model_used": "llama2"
        }
        """
        import requests as req

        data = request.get_json()
        message = data.get('message', '').strip()
        context = data.get('context', {})

        if not message:
            return jsonify({'success': False, 'error': 'Message required'}), 400

        # Detect if user is asking about viewing/analyzing domain HTML
        message_lower = message.lower()
        domain_analysis_keywords = [
            'what does', 'show me', 'view', 'see', 'preview', 'look like',
            'html', 'render', 'display', 'analyze', 'structure'
        ]
        wants_domain_html = any(kw in message_lower for kw in domain_analysis_keywords)

        # Auto-fetch domain HTML if user is asking about it and domain is selected
        domain_html_context = ""
        if wants_domain_html and context.get('domain'):
            try:
                # Fetch HTML from our preview endpoint
                preview_response = req.post(
                    'http://localhost:5001/api/domains/preview',
                    json={'domain': context['domain']},
                    timeout=5
                )
                if preview_response.status_code == 200:
                    preview_data = preview_response.json()
                    if preview_data.get('success'):
                        # Extract first 1000 chars of HTML for context (enough to see structure)
                        html_preview = preview_data['html'][:1000]
                        brand_info = preview_data.get('brand_info', {})
                        domain_html_context = f"""

CURRENT DOMAIN HTML STRUCTURE:
Domain: {brand_info.get('domain', 'unknown')}
Name: {brand_info.get('name', 'unknown')}
Category: {brand_info.get('category', 'unknown')}

HTML Preview (first 1000 chars):
{html_preview}
...

[HTML continues - total length: {len(preview_data['html'])} characters]
"""
            except Exception:
                # Silently fail - don't break chat if preview fails
                pass

        # Find relevant templates if user is asking for code examples
        template_data = find_relevant_templates(message, context.get('domain'))

        # Build context-aware prompt
        system_prompt = """You are a helpful assistant for the Soulfra platform.
You help users manage domains, build websites, analyze files/transcripts, and create content.

Context available:
- Database with brands/domains
- Ollama for AI analysis
- QR code generation
- Multi-domain routing system
- Flask backend on localhost:5001
- Access to 90+ HTML templates for reference

When users ask for code examples, refer to the template code provided below.
Be concise and practical. Provide actionable advice."""

        # Add domain context if provided
        domain = context.get('domain')
        if domain:
            db = get_db()
            brand = db.execute('SELECT * FROM brands WHERE domain = ?', (domain,)).fetchone()
            if brand:
                brand_dict = dict(brand)
                system_prompt += f"\n\nCurrent domain: {domain}\nBrand: {brand_dict['name']}\nCategory: {brand_dict['category']}\nTagline: {brand_dict['tagline']}"

        # Add template code if found
        if template_data['templates_found']:
            system_prompt += f"\n\nRELEVANT TEMPLATE CODE EXAMPLES:\nFound {len(template_data['templates_found'])} template(s): {', '.join(template_data['templates_found'])}"
            message += template_data['template_code']

        # Add domain HTML context if fetched
        if domain_html_context:
            message += domain_html_context

        # Add file content if provided
        file_content = context.get('file_content')
        if file_content:
            message += f"\n\nFile content:\n{file_content}"

        # Add conversation history if provided
        history = context.get('history', [])
        if history:
            history_text = "\n\n".join([
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in history[-5:]  # Last 5 messages
            ])
            message = f"{history_text}\n\nUser: {message}"

        router = LLMRouter()
        result = router.call(
            prompt=message,
            system_prompt=system_prompt,
            temperature=0.7
        )

        if not result['success']:
            return jsonify({
                'success': False,
                'error': 'AI response failed',
                'details': result.get('error', 'Unknown error')
            }), 500

        return jsonify({
            'success': True,
            'response': result['response'],
            'model_used': result['model_used'],
            'duration_ms': result.get('duration_ms', 0)
        })

    @app.route('/api/domains/files/list', methods=['POST'])
    def api_domains_files_list():
        """
        List all files in a domain's directory

        POST JSON:
        {
            "domain": "soulfra.com"
        }

        Returns:
        {
            "success": true,
            "files": [
                {"path": "index.html", "type": "html", "size": 1234},
                {"path": "css/styles.css", "type": "css", "size": 567}
            ]
        }
        """
        data = request.get_json()
        domain = data.get('domain', '').strip()

        if not domain:
            return jsonify({'success': False, 'error': 'Domain required'}), 400

        # Get brand info from database
        db = get_db()
        brand = db.execute('SELECT * FROM brands WHERE domain = ?', (domain,)).fetchone()

        if not brand:
            return jsonify({'success': False, 'error': 'Domain not found in database'}), 404

        # Find domain directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        domain_dir = os.path.join(base_dir, 'domains', brand['slug'])

        if not os.path.exists(domain_dir):
            return jsonify({'success': False, 'error': f'Domain directory not found: {domain_dir}'}), 404

        # Scan directory for files
        files = []
        for root, dirs, filenames in os.walk(domain_dir):
            # Skip build and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'build' and d != '__pycache__']

            for filename in filenames:
                if filename.startswith('.'):
                    continue

                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, domain_dir)

                # Determine file type
                ext = os.path.splitext(filename)[1].lower()
                file_type = ext[1:] if ext else 'unknown'

                # Get file size
                try:
                    file_size = os.path.getsize(full_path)
                except:
                    file_size = 0

                files.append({
                    'path': relative_path,
                    'name': filename,
                    'type': file_type,
                    'size': file_size,
                    'dir': os.path.dirname(relative_path) or '.'
                })

        return jsonify({
            'success': True,
            'domain': domain,
            'slug': brand['slug'],
            'files': sorted(files, key=lambda f: f['path'])
        })

    @app.route('/api/domains/files/read', methods=['POST'])
    def api_domains_files_read():
        """
        Read a file from a domain

        POST JSON:
        {
            "domain": "soulfra.com",
            "file_path": "index.html"
        }

        Returns:
        {
            "success": true,
            "content": "<!DOCTYPE html>..."
        }
        """
        data = request.get_json()
        domain = data.get('domain', '').strip()
        file_path = data.get('file_path', '').strip()

        if not domain or not file_path:
            return jsonify({'success': False, 'error': 'Domain and file_path required'}), 400

        # Get brand info from database
        db = get_db()
        brand = db.execute('SELECT * FROM brands WHERE domain = ?', (domain,)).fetchone()

        if not brand:
            return jsonify({'success': False, 'error': 'Domain not found in database'}), 404

        # Build full file path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        domain_dir = os.path.join(base_dir, 'domains', brand['slug'])
        full_path = os.path.join(domain_dir, file_path)

        # Security check: ensure file is within domain directory
        if not os.path.abspath(full_path).startswith(os.path.abspath(domain_dir)):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400

        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return jsonify({
                'success': True,
                'content': content,
                'file_path': file_path,
                'size': len(content)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error reading file: {str(e)}'}), 500

    @app.route('/api/domains/files/save', methods=['POST'])
    def api_domains_files_save():
        """
        Save a file to a domain

        POST JSON:
        {
            "domain": "soulfra.com",
            "file_path": "index.html",
            "content": "<!DOCTYPE html>..."
        }

        Returns:
        {
            "success": true,
            "message": "File saved"
        }
        """
        data = request.get_json()
        domain = data.get('domain', '').strip()
        file_path = data.get('file_path', '').strip()
        content = data.get('content', '')

        if not domain or not file_path:
            return jsonify({'success': False, 'error': 'Domain and file_path required'}), 400

        # Get brand info from database
        db = get_db()
        brand = db.execute('SELECT * FROM brands WHERE domain = ?', (domain,)).fetchone()

        if not brand:
            return jsonify({'success': False, 'error': 'Domain not found in database'}), 404

        # Build full file path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        domain_dir = os.path.join(base_dir, 'domains', brand['slug'])
        full_path = os.path.join(domain_dir, file_path)

        # Security check: ensure file is within domain directory
        if not os.path.abspath(full_path).startswith(os.path.abspath(domain_dir)):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400

        # Save file content
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return jsonify({
                'success': True,
                'message': 'File saved successfully',
                'file_path': file_path,
                'size': len(content)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error saving file: {str(e)}'}), 500

    @app.route('/api/domains/network/map')
    def api_domains_network_map():
        """
        Get network map data for visualization

        Returns:
        {
            "success": true,
            "nodes": [
                {"id": "soulfra.com", "name": "Soulfra", "role": "hub"},
                {"id": "calriven.com", "name": "Calriven", "role": "member"}
            ],
            "edges": [
                {"source": "soulfra.com", "target": "calriven.com", "type": "network_member"}
            ]
        }
        """
        db = get_db()

        # Get all domains
        brands = db.execute('''
            SELECT domain, name, slug, network_role, tier, category
            FROM brands
            WHERE domain IS NOT NULL AND domain != ''
        ''').fetchall()

        # Get relationships
        relationships = db.execute('''
            SELECT parent_domain, child_domain, relationship_type
            FROM domain_relationships
        ''').fetchall()

        # Build nodes
        nodes = []
        for brand in brands:
            nodes.append({
                'id': brand['domain'],
                'name': brand['name'],
                'slug': brand['slug'],
                'role': brand['network_role'] or 'member',
                'tier': brand['tier'] or 'foundation',
                'category': brand['category'] or 'general'
            })

        # Build edges
        edges = []
        for rel in relationships:
            edges.append({
                'source': rel['parent_domain'],
                'target': rel['child_domain'],
                'type': rel['relationship_type']
            })

        return jsonify({
            'success': True,
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_domains': len(nodes),
                'total_relationships': len(edges),
                'hubs': sum(1 for n in nodes if n['role'] == 'hub'),
                'members': sum(1 for n in nodes if n['role'] == 'member')
            }
        })

    @app.route('/domains/network')
    def domains_network_view():
        """Network visualization page"""
        return render_template('domain_network_map.html')

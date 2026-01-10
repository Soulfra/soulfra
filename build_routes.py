"""
Build Feature Routes
Enables "build me X" requests that return WORKING CODE instead of pseudocode

Integrates:
- Ollama knowledge base (825 indexed docs)
- Existing code patterns from database
- Template generation

Usage:
    POST /api/build
    {
        "request": "build escrow system for blog funding",
        "output_type": "code"  // or "plan", "both"
    }

Returns working Python/JavaScript files ready to use
"""

from flask import Blueprint, request, jsonify
import sqlite3
import requests
import os
from pathlib import Path

build_bp = Blueprint('build', __name__)

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'soulfra.db')
ECONOMY_DB_PATH = '/Users/matthewmauer/Desktop/roommate-chat/roommate-chat.sqlite'
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://192.168.1.87:11434')


def search_knowledge_base(query, limit=5):
    """Search indexed documentation"""
    try:
        conn = sqlite3.connect(ECONOMY_DB_PATH)
        cursor = conn.cursor()

        results = cursor.execute('''
            SELECT ok.file_name, ok.title, ok.category, ok.content
            FROM ollama_knowledge_fts fts
            JOIN ollama_knowledge ok ON fts.rowid = ok.id
            WHERE ollama_knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit)).fetchall()

        conn.close()

        return [
            {
                'file': r[0],
                'title': r[1],
                'category': r[2],
                'content': r[3]
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error searching knowledge base: {e}")
        return []


def query_ollama(prompt, model='qwen2.5-coder:1.5b', system_prompt=None):
    """Query Ollama with context"""
    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'num_predict': 2000
            }
        }

        if system_prompt:
            payload['system'] = system_prompt

        response = requests.post(
            f'{OLLAMA_HOST}/api/generate',
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            return f"Error: Ollama returned status {response.status_code}"
    except Exception as e:
        return f"Error querying Ollama: {e}"


@build_bp.route('/api/build', methods=['POST'])
def build_feature():
    """
    Build a feature from natural language request

    Request:
    {
        "request": "build escrow system for funding blog posts",
        "output_type": "code"  // "code", "plan", or "both"
    }

    Response:
    {
        "success": true,
        "files": [
            {
                "name": "escrow_routes.py",
                "language": "python",
                "content": "..."
            }
        ],
        "plan": "Step-by-step implementation plan",
        "docs_used": ["ECONOMY-INTEGRATION-STATUS.md", ...]
    }
    """
    data = request.json
    user_request = data.get('request', '')
    output_type = data.get('output_type', 'both')

    if not user_request:
        return jsonify({'success': False, 'error': 'No request provided'}), 400

    # Step 1: Search knowledge base for relevant docs
    docs = search_knowledge_base(user_request, limit=5)
    docs_context = "\n\n".join([
        f"## {doc['title']} ({doc['file']})\n{doc['content'][:1000]}"
        for doc in docs
    ])

    # Step 2: Generate plan
    plan_prompt = f"""You are a code architect analyzing existing documentation to build new features.

USER REQUEST: {user_request}

RELEVANT DOCUMENTATION:
{docs_context}

Task: Create a detailed implementation plan that:
1. Lists specific files to create/modify
2. Identifies existing patterns to reuse from docs
3. Specifies exact API endpoints, database tables, and functions
4. Provides step-by-step instructions

Be specific. Use actual code from the docs when possible.
"""

    plan = query_ollama(plan_prompt, model='qwen2.5-coder:1.5b')

    if output_type == 'plan':
        return jsonify({
            'success': True,
            'plan': plan,
            'docs_used': [doc['file'] for doc in docs]
        })

    # Step 3: Generate actual code
    code_prompt = f"""You are a code generator. Generate COMPLETE, WORKING code files.

USER REQUEST: {user_request}

IMPLEMENTATION PLAN:
{plan}

RELEVANT DOCUMENTATION:
{docs_context}

Task: Generate complete, runnable Python or JavaScript code files.
- Use existing patterns from the docs
- Include all imports, error handling, and comments
- Make it production-ready, not pseudocode
- Output each file with clear markers:

```filename: routes/escrow_routes.py
[complete file content]
```

Generate ALL necessary files now:
"""

    code_response = query_ollama(code_prompt, model='qwen2.5-coder:1.5b')

    # Step 4: Parse generated files
    files = parse_code_files(code_response)

    return jsonify({
        'success': True,
        'files': files,
        'plan': plan if output_type == 'both' else None,
        'docs_used': [doc['file'] for doc in docs]
    })


def parse_code_files(response):
    """Parse code blocks from Ollama response"""
    files = []
    lines = response.split('\n')

    current_file = None
    current_content = []

    for line in lines:
        # Detect file marker: ```filename: path/to/file.py
        if line.strip().startswith('```filename:'):
            # Save previous file
            if current_file:
                files.append({
                    'name': current_file['name'],
                    'language': current_file['language'],
                    'content': '\n'.join(current_content)
                })

            # Start new file
            file_path = line.split('```filename:')[1].strip()
            file_name = os.path.basename(file_path)
            language = detect_language(file_name)

            current_file = {
                'name': file_path,
                'language': language
            }
            current_content = []

        elif line.strip() == '```' and current_file:
            # End of code block
            files.append({
                'name': current_file['name'],
                'language': current_file['language'],
                'content': '\n'.join(current_content)
            })
            current_file = None
            current_content = []

        elif current_file:
            current_content.append(line)

    # Save last file if exists
    if current_file and current_content:
        files.append({
            'name': current_file['name'],
            'language': current_file['language'],
            'content': '\n'.join(current_content)
        })

    return files


def detect_language(filename):
    """Detect language from file extension"""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.sql': 'sql',
        '.md': 'markdown',
        '.html': 'html',
        '.css': 'css',
        '.sh': 'bash'
    }

    ext = os.path.splitext(filename)[1].lower()
    return ext_map.get(ext, 'plaintext')


@build_bp.route('/api/build/search-docs', methods=['POST'])
def search_docs():
    """
    Search indexed documentation

    Request:
    {
        "query": "economy tokens escrow"
    }

    Response:
    {
        "success": true,
        "results": [
            {
                "file": "ECONOMY-INTEGRATION-STATUS.md",
                "title": "Economy Integration Status Report",
                "category": "economy",
                "snippet": "..."
            }
        ]
    }
    """
    data = request.json
    query = data.get('query', '')

    if not query:
        return jsonify({'success': False, 'error': 'No query provided'}), 400

    results = search_knowledge_base(query, limit=10)

    return jsonify({
        'success': True,
        'results': [
            {
                'file': r['file'],
                'title': r['title'],
                'category': r['category'],
                'snippet': r['content'][:300] + '...'
            }
            for r in results
        ]
    })


@build_bp.route('/api/build/templates', methods=['GET'])
def list_templates():
    """
    List available code templates from indexed docs

    Response:
    {
        "success": true,
        "templates": [
            {
                "name": "Flask Blog Publisher",
                "category": "publishing",
                "files": ["publish_all_brands.py"],
                "description": "Multi-brand static site generator"
            }
        ]
    }
    """
    # Hardcoded for now, could be dynamic later
    templates = [
        {
            'name': 'Multi-Brand Publisher',
            'category': 'publishing',
            'files': ['publish_all_brands.py'],
            'description': 'Publish multiple brands from one database to GitHub Pages',
            'docs': ['ARCHITECTURE.md', 'ECONOMY-INTEGRATION-STATUS.md']
        },
        {
            'name': 'SOUL Token Economy',
            'category': 'economy',
            'files': ['token_routes.py', 'soul_routes.py'],
            'description': 'Award tokens for contributions, leaderboards, badges',
            'docs': ['CAPSULE-ECONOMY-COMPLETE.md', 'PLAYTEST-ECONOMY.md']
        },
        {
            'name': 'Escrow System',
            'category': 'economy',
            'files': ['escrow_routes.py', 'fundraising_routes.py'],
            'description': 'Hold tokens in escrow until work completed',
            'docs': ['ECONOMY-INTEGRATION-STATUS.md']
        },
        {
            'name': 'BeautifulSoup Scraper',
            'category': 'content',
            'files': ['url_to_content.py', 'domain_researcher.py'],
            'description': 'Scrape web content and import to database',
            'docs': ['CONTENT-SYSTEM-README.md']
        }
    ]

    return jsonify({
        'success': True,
        'templates': templates
    })

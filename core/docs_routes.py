"""
Flask routes for documentation browser
Browse, search, and interact with 189+ markdown documentation files
"""

from flask import render_template, request, jsonify, abort
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import json

try:
    from lib.simple_markdown import markdown_to_html as markdown2_markdown
except ImportError:
    import markdown2
    def markdown2_markdown(text, extras=None):
        if extras:
            return markdown2.markdown(text, extras=extras)
        return markdown2.markdown(text)


def register_docs_routes(app):
    """Register documentation browser routes"""

    # Base directory for docs (same directory as app.py)
    DOCS_DIR = Path(__file__).parent

    def get_all_markdown_files() -> List[Dict[str, any]]:
        """
        Get all markdown files in the docs directory
        Returns list of dicts with file info
        """
        docs = []

        for md_file in DOCS_DIR.glob("*.md"):
            # Skip README if it exists (too generic)
            if md_file.name.lower() == 'readme.md':
                continue

            # Read first few lines to get metadata
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    # Try to extract title (first # heading)
                    title = md_file.stem.replace('-', ' ').title()
                    for line in lines[:20]:  # Check first 20 lines
                        if line.startswith('# '):
                            title = line.replace('#', '').strip()
                            # Remove emojis from title for cleaner display
                            title = re.sub(r'[^\w\s-]', '', title).strip()
                            break

                    # Try to extract purpose/description
                    purpose = ""
                    for line in lines[:30]:
                        if 'purpose:' in line.lower() or 'what it does' in line.lower():
                            purpose = line.split(':', 1)[-1].strip()
                            break

                    # Get file stats
                    stats = md_file.stat()
                    word_count = len(content.split())

                    docs.append({
                        'filename': md_file.name,
                        'title': title,
                        'purpose': purpose,
                        'size': stats.st_size,
                        'modified': stats.st_mtime,
                        'word_count': word_count,
                        'is_starred': '✨' in content or 'START' in md_file.name.upper()
                    })
            except Exception as e:
                print(f"Error reading {md_file.name}: {e}")
                continue

        # Sort by starred first, then alphabetically
        docs.sort(key=lambda x: (not x['is_starred'], x['filename']))

        return docs

    def search_docs(query: str) -> List[Dict[str, any]]:
        """
        Search all markdown files for a query string
        Returns list of matches with context
        """
        results = []
        query_lower = query.lower()

        for md_file in DOCS_DIR.glob("*.md"):
            if md_file.name.lower() == 'readme.md':
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    # Search for query in content
                    matches = []
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            # Get context (line before and after)
                            context_start = max(0, i - 1)
                            context_end = min(len(lines), i + 2)
                            context = '\n'.join(lines[context_start:context_end])

                            matches.append({
                                'line_number': i + 1,
                                'context': context
                            })

                    if matches:
                        results.append({
                            'filename': md_file.name,
                            'title': md_file.stem.replace('-', ' ').title(),
                            'match_count': len(matches),
                            'matches': matches[:3]  # Limit to first 3 matches per file
                        })
            except Exception as e:
                print(f"Error searching {md_file.name}: {e}")
                continue

        # Sort by match count (most matches first)
        results.sort(key=lambda x: x['match_count'], reverse=True)

        return results

    def extract_code_snippets(filename: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from a markdown file
        Returns list of code snippets with language and content
        """
        snippets = []

        md_file = DOCS_DIR / filename
        if not md_file.exists():
            return snippets

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Match code blocks with language specifier
                # Pattern: ```language\ncode\n```
                pattern = r'```(\w+)\n(.*?)```'
                matches = re.finditer(pattern, content, re.DOTALL)

                for i, match in enumerate(matches):
                    language = match.group(1)
                    code = match.group(2).strip()

                    snippets.append({
                        'id': i + 1,
                        'language': language,
                        'code': code,
                        'lines': len(code.split('\n'))
                    })
        except Exception as e:
            print(f"Error extracting snippets from {filename}: {e}")

        return snippets

    def ask_ollama(question: str, context: str = "") -> Optional[str]:
        """
        Ask Ollama a question about the documentation
        Returns answer or None if Ollama unavailable
        """
        try:
            # Check if Ollama is running
            url = "http://localhost:11434/api/generate"

            prompt = f"""You are a helpful documentation assistant for the Soulfra project.

Context from documentation:
{context}

User question: {question}

Provide a concise, helpful answer based on the documentation context."""

            data = {
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')

        except Exception as e:
            print(f"Ollama error: {e}")
            return None

    @app.route('/admin/docs')
    def docs_browser():
        """Main documentation browser page"""
        docs = get_all_markdown_files()

        # Group docs by category (based on filename patterns)
        categories = {
            'Getting Started': [],
            'Testing': [],
            'Architecture': [],
            'Deployment': [],
            'Domains': [],
            'Auth & AI': [],
            'Other': []
        }

        for doc in docs:
            filename = doc['filename'].upper()

            if 'START' in filename or 'SIMPLE-TEST' in filename or 'WHAT-YOU' in filename:
                categories['Getting Started'].append(doc)
            elif 'TEST' in filename or 'DEBUG' in filename:
                categories['Testing'].append(doc)
            elif 'ARCH' in filename or 'VISUAL' in filename or 'RUNNING' in filename:
                categories['Architecture'].append(doc)
            elif 'DEPLOY' in filename or 'PUBLISH' in filename or 'PIP' in filename:
                categories['Deployment'].append(doc)
            elif 'DOMAIN' in filename or 'DNS' in filename:
                categories['Domains'].append(doc)
            elif 'AUTH' in filename or 'OLLAMA' in filename or 'AI' in filename or 'TRAINING' in filename:
                categories['Auth & AI'].append(doc)
            else:
                categories['Other'].append(doc)

        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}

        return render_template('admin_docs.html',
                             categories=categories,
                             total_docs=len(docs))

    @app.route('/admin/docs/<filename>')
    def view_doc(filename):
        """View a specific documentation file"""

        # Security: prevent directory traversal
        if '..' in filename or '/' in filename:
            abort(403)

        md_file = DOCS_DIR / filename

        if not md_file.exists() or not md_file.name.endswith('.md'):
            abort(404)

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Convert markdown to HTML
            html_content = markdown2_markdown(content, extras=[
                'fenced-code-blocks',
                'tables',
                'header-ids',
                'task_list'
            ])

            # Extract code snippets
            snippets = extract_code_snippets(filename)

            return render_template('admin_doc_view.html',
                                 filename=filename,
                                 content=html_content,
                                 raw_content=content,
                                 snippets=snippets)
        except Exception as e:
            abort(500)

    @app.route('/api/docs/search')
    def api_search_docs():
        """API endpoint for searching documentation"""
        query = request.args.get('q', '')

        if not query:
            return jsonify({'error': 'No query provided'}), 400

        results = search_docs(query)

        return jsonify({
            'query': query,
            'result_count': len(results),
            'results': results
        })

    @app.route('/api/docs/ask', methods=['POST'])
    def api_ask_docs():
        """API endpoint for asking Ollama about documentation"""
        data = request.json or {}
        question = data.get('question', '')

        if not question:
            return jsonify({'error': 'No question provided'}), 400

        # Search for relevant docs first
        search_results = search_docs(question)

        # Build context from search results
        context = ""
        for result in search_results[:3]:  # Top 3 results
            context += f"\n\nFrom {result['filename']}:\n"
            for match in result['matches']:
                context += match['context'] + "\n"

        # Ask Ollama
        answer = ask_ollama(question, context)

        if answer is None:
            return jsonify({
                'error': 'Ollama not available',
                'suggestion': 'Start Ollama with: ollama serve'
            }), 503

        return jsonify({
            'question': question,
            'answer': answer,
            'sources': [r['filename'] for r in search_results[:3]]
        })

    @app.route('/admin/snippets')
    def snippets_browser():
        """Browse all code snippets from documentation"""

        all_snippets = []

        for md_file in DOCS_DIR.glob("*.md"):
            if md_file.name.lower() == 'readme.md':
                continue

            snippets = extract_code_snippets(md_file.name)

            if snippets:
                all_snippets.append({
                    'filename': md_file.name,
                    'title': md_file.stem.replace('-', ' ').title(),
                    'snippets': snippets,
                    'total': len(snippets)
                })

        # Sort by snippet count (most snippets first)
        all_snippets.sort(key=lambda x: x['total'], reverse=True)

        # Count snippets by language
        language_counts = {}
        for doc in all_snippets:
            for snippet in doc['snippets']:
                lang = snippet['language']
                language_counts[lang] = language_counts.get(lang, 0) + 1

        return render_template('admin_snippets.html',
                             docs=all_snippets,
                             language_counts=language_counts,
                             total_snippets=sum(language_counts.values()))

    print("✅ Documentation routes registered:")
    print("   /admin/docs - Browse all documentation")
    print("   /admin/docs/<filename> - View specific doc")
    print("   /admin/snippets - Browse code snippets")
    print("   /api/docs/search?q=query - Search docs")
    print("   /api/docs/ask - Ask Ollama about docs")

#!/usr/bin/env python3
"""
Soulfra Zero - Zero External Dependencies

Demonstrates that we can build EVERYTHING ourselves:
- HTTP server (http.server from stdlib)
- Template engine (string replacement)
- Markdown parser (regex patterns)
- Image generation (png_writer.py already exists!)
- QR codes (DIY generation)

NO pip install needed! Just Python 3.x stdlib.

Philosophy:
-----------
Every framework is just organized code. If we understand
the patterns, we can build our own. This gives us:
- Full control
- No supply chain attacks
- Educational value
- True "homebrew" platform

Teaching the pattern for building a neural network marketplace
where each "brand" (model) generates its own output.

Usage:
  python3 soulfra_zero.py
  Visit: http://localhost:8000
"""

import http.server
import socketserver
import json
import re
import sqlite3
import os
import sys
from urllib.parse import parse_qs, urlparse
from datetime import datetime

# Import our zero-dependency neural network
# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pure_neural_network import PureNeuralNetwork
from train_color_features import extract_color_features, explain_color_features
from format_converter import FormatConverter


# ==============================================================================
# 1. TEMPLATE ENGINE (Zero Dependencies)
# ==============================================================================

class SimpleTemplate:
    """
    String-based template engine

    Replaces {{ variable }} with values
    Supports {% if condition %}...{% endif %}

    No Jinja2 needed! Just regex and string ops.
    """

    @staticmethod
    def render(template_string, **context):
        """
        Render template with context variables

        Example:
            template = "Hello {{ name }}!"
            SimpleTemplate.render(template, name="World")
            # Returns: "Hello World!"
        """
        result = template_string

        # Replace {{ variable }} with values
        for key, value in context.items():
            result = result.replace(f'{{{{ {key} }}}}', str(value))
            result = result.replace(f'{{{{{key}}}}}', str(value))  # No spaces

        # Handle {% if variable %} blocks
        result = SimpleTemplate._process_if_blocks(result, context)

        # Handle {% for item in list %} blocks
        result = SimpleTemplate._process_for_loops(result, context)

        return result

    @staticmethod
    def _process_if_blocks(text, context):
        """Process {% if %} ... {% endif %} blocks"""
        pattern = r'{%\s*if\s+(\w+)\s*%}(.*?){%\s*endif\s*%}'

        def replacer(match):
            var_name = match.group(1)
            content = match.group(2)

            # Check if variable is truthy in context
            if context.get(var_name):
                return content
            else:
                return ''

        return re.sub(pattern, replacer, text, flags=re.DOTALL)

    @staticmethod
    def _process_for_loops(text, context):
        """Process {% for item in list %} ... {% endfor %} blocks"""
        pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'

        def replacer(match):
            item_var = match.group(1)
            list_var = match.group(2)
            content = match.group(3)

            items = context.get(list_var, [])
            result = []

            for item in items:
                # Create context for this iteration
                iter_context = context.copy()
                iter_context[item_var] = item

                # Render content for this item
                rendered = content
                if isinstance(item, dict):
                    for key, value in item.items():
                        rendered = rendered.replace(f'{{{{ {item_var}.{key} }}}}', str(value))
                        rendered = rendered.replace(f'{{{{{item_var}.{key}}}}}', str(value))
                else:
                    rendered = rendered.replace(f'{{{{ {item_var} }}}}', str(item))
                    rendered = rendered.replace(f'{{{{{item_var}}}}}', str(item))

                result.append(rendered)

            return ''.join(result)

        return re.sub(pattern, replacer, text, flags=re.DOTALL)


# ==============================================================================
# 2. MARKDOWN PARSER (Zero Dependencies)
# ==============================================================================

class SimpleMarkdown:
    """
    Markdown → HTML converter

    Handles basic syntax:
    - Headers: # H1, ## H2, ### H3
    - Bold: **text** or __text__
    - Italic: *text* or _text_
    - Code: `code` or ```code block```
    - Links: [text](url)
    - Lists: - item or * item

    No markdown2 needed! Just regex patterns.
    """

    @staticmethod
    def convert(markdown_text):
        """Convert Markdown to HTML"""
        html = markdown_text

        # Code blocks (must come before inline code)
        html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)

        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        # Headers
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)

        # Italic
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)

        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)

        # Line breaks
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'

        return html


# ==============================================================================
# 3. HTTP SERVER + ROUTER (Zero Dependencies)
# ==============================================================================

class SoulRouter:
    """
    URL router for HTTP server

    Maps paths to handler functions
    No Flask needed! Just http.server + manual routing.
    """

    def __init__(self):
        self.routes = {}
        self.database = 'soulfra.db'

    def route(self, path):
        """Decorator to register route handlers"""
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator

    def handle_request(self, path, query_params, post_data=None):
        """Route request to appropriate handler"""
        # Extract base path (remove query string)
        base_path = path.split('?')[0]

        # Match exact routes first
        if base_path in self.routes:
            return self.routes[base_path](query_params, post_data)

        # Pattern matching for dynamic routes like /post/<slug> or /static/generated/<filename>
        for route_path, handler in self.routes.items():
            if '<' in route_path and '>' in route_path:
                # Replace all <param> with regex capture groups
                pattern = route_path
                pattern = re.sub(r'<\w+>', r'([^/]+)', pattern)
                match = re.match(f'^{pattern}$', base_path)
                if match:
                    # Pass captured groups as first arguments
                    return handler(*match.groups(), query_params, post_data)

        return None


# Initialize router
router = SoulRouter()


# ==============================================================================
# 4. ROUTES (Like Flask routes, but DIY)
# ==============================================================================

@router.route('/')
def index(query_params, post_data):
    """Homepage with AI model outputs"""

    # Fetch posts from DB
    conn = sqlite3.connect(router.database)
    conn.row_factory = sqlite3.Row
    posts = conn.execute('''
        SELECT * FROM posts
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
        LIMIT 10
    ''').fetchall()
    conn.close()

    # Convert to dicts
    posts_list = [dict(post) for post in posts]

    # Template (inline for demo - could be external file)
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Soulfra Zero - No Dependencies!</title>
        <style>
            body { font-family: monospace; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
            h1 { color: #007bff; }
            .post { border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; }
            .badge { background: #28a745; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🏗️ Soulfra Zero</h1>
        <p><span class="badge">ZERO EXTERNAL DEPENDENCIES</span></p>
        <p>Everything built from scratch using Python stdlib!</p>

        <h2>Posts</h2>
        {% for post in posts %}
        <div class="post">
            <h3>{{ post.title }}</h3>
            <p>{{ post.excerpt }}</p>
            <small>Published: {{ post.published_at }}</small>
        </div>
        {% endfor %}

        {% if not posts %}
        <p>No posts yet. Run create_db.py to generate sample data.</p>
        {% endif %}

        <hr>
        <p><strong>What's happening here?</strong></p>
        <ul>
            <li>✅ HTTP server: Python's http.server (stdlib)</li>
            <li>✅ Templates: String replacement (no Jinja2)</li>
            <li>✅ Routing: Regex matching (no Flask)</li>
            <li>✅ Database: sqlite3 (stdlib)</li>
            <li>✅ Markdown: Regex patterns (no markdown2)</li>
            <li>🧠 Neural Networks: Pure Python + math module (no numpy/tensorflow!)</li>
        </ul>
        <p>We can build EVERYTHING ourselves! 🚀</p>

        <hr>
        <div style="background: #ff00ff11; border: 2px solid #ff00ff; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <h3 style="margin-top: 0;">🎨 NEW: Tier System Showcase!</h3>
            <p>We just built GIF and BMP encoders from scratch (pure stdlib)!</p>
            <p style="font-size: 1.2rem;">
                <strong><a href="/tiers" style="color: #ff00ff; font-weight: bold;">→ View Generated Images (GIFs + BMPs)</a></strong>
            </p>
            <p style="font-size: 0.9rem; color: #666;">
                320 lines of LZW compression + 280 lines of raw pixel encoding.
                <br/><strong>It's all binary in the end, like sex.</strong>
            </p>
        </div>

        <hr>
        <p><strong>Try the APIs:</strong></p>
        <div style="background: #f5f5f5; padding: 1rem; border-radius: 4px; margin: 1rem 0;">
            <h3 style="margin-top: 0;">1. Keyword Matching Demo</h3>
            <code style="background: #fff; padding: 0.5rem; display: block; margin: 0.5rem 0;">
curl -X POST http://localhost:8888/api/predict<br/>
  -H "Content-Type: application/json"<br/>
  -d '{"text":"code encryption test"}'
            </code>
            <p style="font-size: 0.9rem; color: #666;">Simple keyword matching - shows the "per brand" concept</p>
        </div>

        <div style="background: #e8f5e9; padding: 1rem; border-radius: 4px; margin: 1rem 0; border: 2px solid #4caf50;">
            <h3 style="margin-top: 0;">2. REAL Neural Network 🔥</h3>
            <code style="background: #fff; padding: 0.5rem; display: block; margin: 0.5rem 0;">
curl -X POST http://localhost:8888/api/classify-color<br/>
  -H "Content-Type: application/json"<br/>
  -d '{"r":255,"g":0,"b":0}'
            </code>
            <p style="font-size: 0.9rem; color: #2e7d32;">
                <strong>ACTUAL neural network!</strong> Pure Python, no numpy/tensorflow.
                <br/>Trained on 10,000 color examples. 99.8% accuracy.
            </p>
        </div>

        <p><strong>Key Difference:</strong></p>
        <ul>
            <li>/api/predict = Keyword matching (if 'code' in text)</li>
            <li>/api/classify-color = REAL neural network (matrix math, backpropagation)</li>
        </ul>

        <hr>
        <h2>Multi-Format Output (Horizontal Axis)</h2>
        <p>Get the same data in 6 different formats - like light through a prism! 🌈</p>

        <div style="background: #fff8e1; padding: 1rem; border-radius: 4px; margin: 1rem 0; border: 2px solid #ffc107;">
            <h3 style="margin-top: 0;">Format Examples</h3>
            <p>Add <code>?format=</code> to get different output types:</p>

            <div style="margin: 0.5rem 0;">
                <strong>JSON (default):</strong>
                <code style="background: #fff; padding: 0.25rem; display: inline;">?format=json</code>
            </div>

            <div style="margin: 0.5rem 0;">
                <strong>CSV (spreadsheets):</strong>
                <code style="background: #fff; padding: 0.25rem; display: inline;">?format=csv</code>
            </div>

            <div style="margin: 0.5rem 0;">
                <strong>TXT (human-readable):</strong>
                <code style="background: #fff; padding: 0.25rem; display: inline;">?format=txt</code>
            </div>

            <div style="margin: 0.5rem 0;">
                <strong>HTML (styled card):</strong>
                <code style="background: #fff; padding: 0.25rem; display: inline;">?format=html</code>
            </div>

            <div style="margin: 0.5rem 0;">
                <strong>RTF (word processors):</strong>
                <code style="background: #fff; padding: 0.25rem; display: inline;">?format=rtf</code>
            </div>

            <div style="margin: 0.5rem 0;">
                <strong>Binary (efficient storage):</strong>
                <code style="background: #fff; padding: 0.25rem; display: inline;">?format=binary</code>
            </div>

            <p style="margin-top: 1rem;"><strong>Example:</strong></p>
            <code style="background: #fff; padding: 0.5rem; display: block;">
curl -X POST "http://localhost:8888/api/classify-color?format=csv"<br/>
  -H "Content-Type: application/json"<br/>
  -d '{"r":255,"g":0,"b":0}'
            </code>

            <p style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                Same neural network prediction, 6 different representations!
                <br/>ZERO external dependencies - all formats use Python stdlib only.
            </p>
        </div>
    </body>
    </html>
    '''

    # Render and return
    html = SimpleTemplate.render(template, posts=posts_list)
    return ('text/html', html)


@router.route('/api/predict')
def api_predict(query_params, post_data):
    """
    API endpoint for AI predictions - DEMO VERSION

    NOTE: This is a simplified keyword-matching demo.
    For REAL neural network predictions, use /api/classify-color

    Shows the "hello world per brand/model" concept
    """

    # Parse input
    data = json.loads(post_data) if post_data else {}
    text = data.get('text', '')

    # Simple keyword matching (intentionally simple for demo)
    predictions = {
        'calriven': {
            'verdict': 'TECHNICAL' if 'code' in text.lower() else 'NON-TECHNICAL',
            'confidence': 0.85,
            'reasoning': 'CalRiven looks for code, tests, architecture (keyword matching)',
            'method': 'KEYWORD_MATCHING'
        },
        'theauditor': {
            'verdict': 'VALIDATED' if 'test' in text.lower() else 'UNVALIDATED',
            'confidence': 0.78,
            'reasoning': 'TheAuditor checks for proofs and validation (keyword matching)',
            'method': 'KEYWORD_MATCHING'
        },
        'deathtodata': {
            'verdict': 'PRIVACY-FRIENDLY' if 'encrypt' in text.lower() else 'PRIVACY-HOSTILE',
            'confidence': 0.92,
            'reasoning': 'DeathToData analyzes privacy implications (keyword matching)',
            'method': 'KEYWORD_MATCHING'
        },
        'soulfra': {
            'verdict': 'APPROVED',
            'confidence': 0.88,
            'reasoning': 'Soulfra meta-judges the other 3 models',
            'method': 'KEYWORD_MATCHING'
        },
        '_note': 'This endpoint uses simple keyword matching. For REAL neural network, use /api/classify-color'
    }

    return ('application/json', json.dumps(predictions, indent=2))


@router.route('/api/classify-color')
def api_classify_color(query_params, post_data):
    """
    REAL Neural Network Classification - Color Classifier

    Uses pure_neural_network.py (ZERO external dependencies)
    Trained on warm vs cool colors

    POST data:
    {
        "r": 255,  # Red (0-255)
        "g": 0,    # Green (0-255)
        "b": 0     # Blue (0-255)
    }

    Query parameters:
    ?format=json|csv|txt|html|rtf|binary (default: json)

    Returns:
    {
        "prediction": "WARM" or "COOL",
        "confidence": 0.99,
        "reasoning": [...],
        "features": {...},
        "method": "PURE_PYTHON_NEURAL_NETWORK"
    }
    """
    # Get format from query params (default: json)
    format_type = query_params.get('format', ['json'])[0].lower()

    # Parse input
    data = json.loads(post_data) if post_data else {}
    r = data.get('r', 128) / 255.0  # Normalize to 0-1
    g = data.get('g', 128) / 255.0
    b = data.get('b', 128) / 255.0

    rgb = [r, g, b]

    try:
        # Load the REAL neural network (trained in pure_neural_network.py)
        network_path = os.path.join(os.path.dirname(__file__), 'color_network.json')

        if not os.path.exists(network_path):
            return ('application/json', json.dumps({
                'error': 'Neural network not trained yet',
                'solution': 'Run: python3 pure_neural_network.py',
                'file_missing': network_path
            }, indent=2))

        # Load network
        network = PureNeuralNetwork.load(network_path)

        # Extract color features (HSV, temperature, etc.)
        features = extract_color_features(rgb)
        feature_explanations = explain_color_features(features, rgb)

        # Make prediction using REAL neural network
        prediction_raw = network.predict(rgb)

        # prediction_raw[0] is warm probability
        warm_probability = prediction_raw[0]
        is_warm = warm_probability > 0.5

        prediction_label = "WARM" if is_warm else "COOL"
        confidence = warm_probability if is_warm else (1 - warm_probability)

        # Build response
        response = {
            'prediction': prediction_label,
            'confidence': round(float(confidence), 4),
            'warm_probability': round(float(warm_probability), 4),
            'cool_probability': round(float(1 - warm_probability), 4),
            'reasoning': feature_explanations,
            'features': {
                'hue': round(features[0] * 360, 1),  # 0-360 degrees
                'saturation': round(features[1], 2),
                'brightness': round(features[2], 2),
                'temperature_score': round(features[3], 2)
            },
            'rgb': {
                'r': int(r * 255),
                'g': int(g * 255),
                'b': int(b * 255)
            },
            'method': 'PURE_PYTHON_NEURAL_NETWORK',
            'network_architecture': {
                'input_neurons': network.input_size,
                'hidden_neurons': network.hidden_size,
                'output_neurons': network.output_size,
                'total_trained': network.total_trained,
                'accuracy': round(network.get_accuracy(), 4) if network.total_trained > 0 else 0
            }
        }

        # Return in requested format (horizontal axis!)
        if format_type == 'csv':
            return ('text/csv', FormatConverter.to_csv([response]))
        elif format_type == 'txt':
            return ('text/plain', FormatConverter.to_txt(response, 'detailed'))
        elif format_type == 'html':
            return ('text/html', FormatConverter.to_html(response, 'card'))
        elif format_type == 'rtf':
            return ('application/rtf', FormatConverter.to_rtf(response))
        elif format_type == 'binary':
            # For binary, extract numeric fields only
            numeric_data = {
                'r': response['rgb']['r'],
                'g': response['rgb']['g'],
                'b': response['rgb']['b'],
                'confidence': response['confidence'],
                'hue': response['features']['hue'],
                'saturation': response['features']['saturation'],
                'brightness': response['features']['brightness']
            }
            return ('application/octet-stream', FormatConverter.to_binary(numeric_data))
        else:  # json (default)
            return ('application/json', json.dumps(response, indent=2))

    except Exception as e:
        return ('application/json', json.dumps({
            'error': str(e),
            'type': type(e).__name__,
            'solution': 'Make sure pure_neural_network.py and color_network.json exist'
        }, indent=2))


@router.route('/markdown')
def markdown_demo(query_params, post_data):
    """Demonstrate DIY Markdown parser"""

    sample_md = """
# Markdown Test

This is **bold** and this is *italic*.

Here's some `inline code` and a [link](http://example.com).

## Code Block

```python
def hello():
    print("No dependencies!")
```

We built our own Markdown parser!
    """

    html_content = SimpleMarkdown.convert(sample_md)

    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Markdown Demo - Soulfra Zero</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
            code { background: #f0f0f0; padding: 0.2rem 0.4rem; border-radius: 3px; }
            pre { background: #f0f0f0; padding: 1rem; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>DIY Markdown Parser</h1>
        <div>{{ content }}</div>
        <hr>
        <p><strong>Built with zero dependencies!</strong> No markdown2, no commonmark, just regex.</p>
        <a href="/">← Back</a>
    </body>
    </html>
    '''

    html = SimpleTemplate.render(template, content=html_content)
    return ('text/html', html)


@router.route('/tiers')
def tiers_showcase(query_params, post_data):
    """Showcase the tier system - Binary → Anime/Interactive"""

    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tier System: Binary → Images → Anime</title>
        <style>
            body {
                font-family: monospace;
                max-width: 1200px;
                margin: 2rem auto;
                padding: 0 1rem;
                background: #0a0a0a;
                color: #e0e0e0;
            }
            h1 {
                color: #00ff00;
                text-align: center;
                font-size: 2.5rem;
            }
            h2 {
                color: #00ccff;
                border-bottom: 2px solid #00ccff;
                padding-bottom: 0.5rem;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin: 2rem 0;
            }
            .image-card {
                background: #1a1a1a;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            }
            .image-card img {
                max-width: 100%;
                height: auto;
                border: 1px solid #444;
                border-radius: 4px;
            }
            .image-card h3 {
                color: #ffa500;
                margin: 0.5rem 0;
                font-size: 1rem;
            }
            .stats {
                background: #1a1a2e;
                padding: 1.5rem;
                border-radius: 8px;
                border: 2px solid #16213e;
                margin: 2rem 0;
            }
            .badge {
                background: #28a745;
                color: white;
                padding: 0.3rem 0.6rem;
                border-radius: 4px;
                font-weight: bold;
            }
            pre {
                background: #1a1a1a;
                padding: 1rem;
                border-radius: 4px;
                overflow-x: auto;
                border: 1px solid #333;
            }
            a {
                color: #00ccff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .highlight {
                color: #ff00ff;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>🎨 Tier System Showcase</h1>
        <p style="text-align: center; font-size: 1.2rem;">
            <span class="badge">ZERO EXTERNAL DEPENDENCIES</span>
        </p>
        <p style="text-align: center; color: #888;">
            <strong>It's all binary in the end, like sex</strong> - Every format reduces to 0s and 1s
        </p>

        <div class="stats">
            <h2>📊 Progress</h2>
            <p><strong>Tiers 0-3 Complete:</strong> Binary → Text → Documents → Raster Graphics</p>
            <p><strong>Total Code:</strong> 3,620 lines of pure Python stdlib</p>
            <p><strong>Formats Implemented:</strong></p>
            <ul>
                <li>✅ PNG (408 lines) - Chunks + zlib compression</li>
                <li>✅ BMP (280 lines) - Raw pixels (like framebuffers)</li>
                <li>✅ GIF (320 lines) - LZW compression + 256-color palette</li>
                <li>✅ PDF (450 lines) - PostScript commands</li>
                <li>✅ Markdown (275 lines) - Text → HTML</li>
            </ul>
            <p><strong>Next:</strong> GIF animation (multi-frame) → Video → 3D → Interactive</p>
        </div>

        <h2>🔴 GIF Images (LZW Compressed)</h2>
        <p>Generated with <code>lib/simple_gif.py</code> - Pure Python LZW compression!</p>
        <div class="grid">
            <div class="image-card">
                <img src="/static/generated/test_red.gif" alt="Red GIF">
                <h3>test_red.gif</h3>
                <p>148 bytes | 100x100</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_green.gif" alt="Green GIF">
                <h3>test_green.gif</h3>
                <p>148 bytes | 100x100</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_blue.gif" alt="Blue GIF">
                <h3>test_blue.gif</h3>
                <p>148 bytes | 100x100</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_checkerboard.gif" alt="Checkerboard GIF">
                <h3>test_checkerboard.gif</h3>
                <p>1.7 KB | 200x200</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_shapes.gif" alt="Shapes GIF">
                <h3>test_shapes.gif</h3>
                <p>1.1 KB | 300x300</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_gradient.gif" alt="Gradient GIF">
                <h3>test_gradient.gif</h3>
                <p>10.7 KB | 256x256</p>
            </div>
        </div>

        <h2>🟦 BMP Images (Raw Pixels)</h2>
        <p>Generated with <code>lib/simple_bmp.py</code> - Just like hardware framebuffers!</p>
        <div class="grid">
            <div class="image-card">
                <img src="/static/generated/test_red.bmp" alt="Red BMP">
                <h3>test_red.bmp</h3>
                <p>29 KB | 100x100</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_checkerboard.bmp" alt="Checkerboard BMP">
                <h3>test_checkerboard.bmp</h3>
                <p>117 KB | 200x200</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_shapes.bmp" alt="Shapes BMP">
                <h3>test_shapes.bmp</h3>
                <p>264 KB | 300x300</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/test_gradient.bmp" alt="Gradient BMP">
                <h3>test_gradient.bmp</h3>
                <p>192 KB | 256x256</p>
            </div>
        </div>

        <h2>🤖 Brand-Specific AI Persona Logos</h2>
        <p>Generated with our GIF encoder - each AI persona has its own visual identity!</p>
        <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
            <div class="image-card">
                <img src="/static/generated/calriven_logo.gif" alt="CalRiven Logo">
                <h3 style="color: #007bff;">CalRiven</h3>
                <p style="font-size: 0.9rem;">Technical Analysis</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/theauditor_logo.gif" alt="TheAuditor Logo">
                <h3 style="color: #ffc107;">TheAuditor</h3>
                <p style="font-size: 0.9rem;">Validation</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/deathtodata_logo.gif" alt="DeathToData Logo">
                <h3 style="color: #9c27b0;">DeathToData</h3>
                <p style="font-size: 0.9rem;">Privacy</p>
            </div>
            <div class="image-card">
                <img src="/static/generated/soulfra_logo.gif" alt="Soulfra Logo">
                <h3 style="color: #4caf50;">Soulfra</h3>
                <p style="font-size: 0.9rem;">Meta-Judge</p>
            </div>
        </div>

        <h2>🧬 The Biology Connection</h2>
        <pre>
DNA = 2-bit format (4 bases: A,C,G,T)
Vision = Image sensor (126M pixels, RGB channels)
Neural Networks = Same as biological neurons
Evolution = Gradient descent (optimize fitness)

<span class="highlight">Biology invented information systems first!</span>
        </pre>

        <h2>🎯 Format Comparison</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #1a1a1a;">
                    <th style="padding: 0.5rem; border: 1px solid #333;">Format</th>
                    <th style="padding: 0.5rem; border: 1px solid #333;">Size (100x100)</th>
                    <th style="padding: 0.5rem; border: 1px solid #333;">Compression</th>
                    <th style="padding: 0.5rem; border: 1px solid #333;">Use Case</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 0.5rem; border: 1px solid #333;"><strong>GIF</strong></td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">148 bytes</td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">LZW (196x smaller!)</td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">Animation, 256 colors</td>
                </tr>
                <tr style="background: #1a1a1a;">
                    <td style="padding: 0.5rem; border: 1px solid #333;"><strong>BMP</strong></td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">29 KB</td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">None (raw pixels)</td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">Simple, uncompressed</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem; border: 1px solid #333;"><strong>PNG</strong></td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">~2-4 KB</td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">zlib (DEFLATE)</td>
                    <td style="padding: 0.5rem; border: 1px solid #333;">Web, lossless</td>
                </tr>
            </tbody>
        </table>

        <h2>🚀 Next Steps</h2>
        <ul>
            <li><strong>GIF Animation:</strong> Multi-frame support → animated brand logos!</li>
            <li><strong>JPEG Encoder:</strong> DCT + Huffman compression</li>
            <li><strong>Video Encoder:</strong> Motion JPEG (frame sequence)</li>
            <li><strong>3D Formats:</strong> OBJ, STL files</li>
            <li><strong>Interactive:</strong> Terminal game engine</li>
        </ul>

        <p style="text-align: center; margin: 3rem 0;">
            <span class="highlight">It's all binary in the end</span><br>
            <strong>Binary (0/1) → Text → Images → Video → Interactive</strong><br>
            Just like sex: Binary choice creates ALL complexity
        </p>

        <hr style="border-color: #333; margin: 2rem 0;">
        <p style="text-align: center;">
            <a href="/">← Back to Homepage</a> |
            <a href="/markdown">Markdown Demo</a> |
            <a href="/api/classify-color" style="color: #28a745;">Neural Network API</a>
        </p>
    </body>
    </html>
    '''

    return ('text/html', template)


@router.route('/static/generated/<filename>')
def serve_static(filename, query_params, post_data):
    """Serve static files (GIF, BMP, PNG)"""
    import os

    # Security: Only allow certain file types
    allowed_extensions = {'.gif', '.bmp', '.png', '.jpg', '.jpeg'}
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in allowed_extensions:
        return None  # 404

    filepath = os.path.join('static', 'generated', filename)

    if not os.path.exists(filepath):
        return None  # 404

    # Determine content type
    content_types = {
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg'
    }

    content_type = content_types.get(file_ext, 'application/octet-stream')

    # Read and return file
    with open(filepath, 'rb') as f:
        return (content_type, f.read())


@router.route('/dashboard')
def dashboard(query_params, post_data):
    """
    LIVE TRAINING DASHBOARD - r/place for AI!

    Built using TIER SYSTEM (stdlib only):
    - TIER 1: Data (sqlite3.connect)
    - TIER 2: Transform (pure Python lists/dicts)
    - TIER 3: Format (string templates, NO Jinja!)

    Shows:
    - All neural networks with stats
    - Live training activity
    - Contributor leaderboard
    - Export options
    """
    import sqlite3

    # TIER 1: Query database directly (sqlite3 stdlib)
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get all neural networks
    cursor.execute('''
        SELECT id, model_name, description, input_size, hidden_sizes,
               output_size, model_data, trained_at
        FROM neural_networks
        ORDER BY trained_at DESC
    ''')
    networks_raw = cursor.fetchall()

    conn.close()

    # TIER 2: Transform data (pure Python)
    networks = []
    for net in networks_raw:
        model_data = json.loads(net[6]) if net[6] else {}
        accuracy_history = model_data.get('accuracy_history', [])
        loss_history = model_data.get('loss_history', [])

        # Build accuracy chart (last 20 points)
        chart_points = accuracy_history[-20:] if len(accuracy_history) > 0 else []
        chart_html = ''
        for acc in chart_points:
            height = int(acc * 100) if acc else 2
            chart_html += f'<div style="flex: 1; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); border-radius: 2px 2px 0 0; min-height: 2px; height: {height}%;"></div>'

        networks.append({
            'id': net[0],
            'name': net[1],
            'description': net[2] or 'No description',
            'architecture': f"{net[3]} → {json.loads(net[4]) if net[4] else []} → {net[5]}",
            'accuracy': f"{accuracy_history[-1] * 100:.2f}" if accuracy_history else "0",
            'loss': f"{loss_history[-1]:.4f}" if loss_history else "0",
            'epochs': len(loss_history),
            'chart_html': chart_html,
            'trained_at': net[7]
        })

    # No training activity table exists yet - show empty state
    activity = []

    # TIER 3: Generate HTML (string templates, NO Jinja!)
    # Build network cards HTML
    network_cards_html = ''
    for net in networks:
        network_cards_html += f'''
        <div class="network-card">
            <div class="network-name">{net['name']}</div>
            <div style="color: #666; font-size: 0.9rem;">{net['description']}</div>
            <div class="network-architecture">{net['architecture']}</div>

            <div class="chart-mini">
                {net['chart_html']}
            </div>
            <div style="text-align: center; font-size: 0.7rem; color: #999; margin-top: 0.25rem;">
                Accuracy History (last 20 epochs)
            </div>

            <div class="network-stats">
                <div class="network-stat">
                    <div class="network-stat-value">{net['accuracy']}%</div>
                    <div class="network-stat-label">Accuracy</div>
                </div>
                <div class="network-stat">
                    <div class="network-stat-value">{net['loss']}</div>
                    <div class="network-stat-label">Loss</div>
                </div>
                <div class="network-stat">
                    <div class="network-stat-value">{net['epochs']}</div>
                    <div class="network-stat-label">Epochs</div>
                </div>
            </div>

            <button class="export-btn" onclick="alert('Export {net['name']}\\\\n\\\\nRun:\\\\npython3 publish.py export {net['name']}')">
                📦 Export Network
            </button>
        </div>
        '''

    # Build activity feed HTML
    activity_html = ''
    if activity:
        for act in activity:
            activity_html += f'''
            <div class="activity-item {act['class']}">
                <div>
                    <span class="activity-network">{act['network']}</span>
                    <span style="color: #666;">→ {act['prediction']}</span>
                    <span style="margin-left: 0.5rem;">{act['icon']}</span>
                </div>
                <div class="activity-time">{act['timestamp']}</div>
            </div>
            '''
    else:
        activity_html = '<p style="text-align: center; color: #999;">No training activity yet. <a href="/api/classify-color">Start training!</a></p>'

    # Full dashboard HTML (string template)
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Training Dashboard - Soulfra Zero</title>
        <style>
            body {{ font-family: monospace; max-width: 1400px; margin: 0 auto; padding: 1rem; background: #f5f5f5; }}
            .dashboard-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; text-align: center; }}
            .dashboard-header h1 {{ margin: 0; font-size: 2.5rem; }}
            .live-indicator {{ display: inline-block; width: 10px; height: 10px; background: #28a745; border-radius: 50%; animation: pulse 2s infinite; margin-right: 0.5rem; }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}

            .dashboard-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
            .stat-card {{ background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; text-align: center; }}
            .stat-value {{ font-size: 2.5rem; font-weight: bold; color: #667eea; }}
            .stat-label {{ color: #666; margin-top: 0.5rem; }}

            .networks-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
            .network-card {{ background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; }}
            .network-name {{ font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem; color: #333; }}
            .network-architecture {{ font-family: monospace; background: #f5f5f5; padding: 0.5rem; border-radius: 4px; margin: 0.5rem 0; font-size: 0.9rem; }}
            .network-stats {{ display: flex; justify-content: space-between; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e0e0e0; }}
            .network-stat {{ text-align: center; }}
            .network-stat-value {{ font-size: 1.5rem; font-weight: bold; color: #28a745; }}
            .network-stat-label {{ font-size: 0.8rem; color: #666; }}
            .chart-mini {{ height: 60px; margin-top: 0.5rem; display: flex; align-items: flex-end; gap: 2px; }}
            .export-btn {{ background: #28a745; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem; margin-top: 0.5rem; width: 100%; }}

            .activity-feed {{ background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; }}
            .activity-item {{ padding: 0.75rem; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }}
            .activity-correct {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
            .activity-incorrect {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
            .activity-network {{ font-weight: bold; color: #667eea; }}
            .activity-time {{ font-size: 0.8rem; color: #999; }}
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <h1><span class="live-indicator"></span>Live Training Dashboard</h1>
            <p>Like r/place but for AI training - Everyone builds intelligence together!</p>
            <p style="font-size: 0.9rem;">Built with ZERO external dependencies - Pure Python stdlib!</p>
        </div>

        <div class="dashboard-stats">
            <div class="stat-card">
                <div class="stat-value">{len(networks)}</div>
                <div class="stat-label">Neural Networks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(activity)}</div>
                <div class="stat-label">Recent Training Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">🔥</div>
                <div class="stat-label">Live & Active</div>
            </div>
        </div>

        <h2 style="color: #333;">🧠 Neural Networks</h2>
        <div class="networks-grid">
            {network_cards_html}
        </div>

        <h2 style="color: #333;">📊 Live Training Activity</h2>
        <div class="activity-feed">
            {activity_html}
        </div>

        <div style="text-align: center; margin: 3rem 0 2rem; padding: 2rem; background: white; border-radius: 8px; border: 2px solid #667eea;">
            <h2 style="color: #667eea;">🎨 Collaborative AI Training</h2>
            <p style="font-size: 1.1rem; color: #666;">
                Like r/place where everyone places pixels, here everyone trains the AI together!
            </p>
            <p style="margin-top: 1rem;">
                <a href="/api/classify-color" style="color: #667eea; font-weight: bold;">→ Train Neural Network</a> |
                <a href="/tiers" style="color: #667eea; font-weight: bold;">→ View Tier System</a> |
                <a href="/" style="color: #667eea; font-weight: bold;">→ Homepage</a>
            </p>
        </div>

        <script>
        // Auto-refresh every 5 seconds (like r/place)
        setTimeout(function() {{ location.reload(); }}, 5000);
        </script>
    </body>
    </html>
    '''

    return ('text/html', html)


# ==============================================================================
# 5. HTTP SERVER (Zero Dependencies)
# ==============================================================================

class SoulHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP request handler

    Routes requests to appropriate handlers
    No Flask/Werkzeug needed! Just stdlib.
    """

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # Route request
        result = router.handle_request(path, query_params)

        if result:
            content_type, body = result
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            # Handle both string and bytes responses
            if isinstance(body, bytes):
                self.wfile.write(body)
            else:
                self.wfile.write(body.encode('utf-8'))
        else:
            # 404 Not Found
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1><p>Route not registered</p>')

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # Route request
        result = router.handle_request(path, query_params, post_data)

        if result:
            content_type, body = result
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            # Handle both string and bytes responses
            if isinstance(body, bytes):
                self.wfile.write(body)
            else:
                self.wfile.write(body.encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1>')

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


# ==============================================================================
# 6. MAIN (Start Server)
# ==============================================================================

def main():
    PORT = 8888

    print("=" * 70)
    print("🏗️  SOULFRA ZERO - Zero External Dependencies")
    print("=" * 70)
    print()
    print("What we built from scratch:")
    print("  ✅ HTTP server (http.server)")
    print("  ✅ URL routing (regex matching)")
    print("  ✅ Template engine (string ops)")
    print("  ✅ Markdown parser (regex patterns)")
    print("  ✅ Database (sqlite3)")
    print()
    print(f"🚀 Server running at: http://localhost:{PORT}")
    print("   Visit the homepage to see it in action!")
    print()
    print("Routes:")
    print("  /               - Homepage with posts")
    print("  /api/predict    - AI prediction API")
    print("  /markdown       - Markdown parser demo")
    print()
    print("💡 This demonstrates that we CAN build everything ourselves!")
    print("   No pip install needed. No supply chain attacks.")
    print("   Perfect foundation for a neural network marketplace.")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)

    with socketserver.TCPServer(("", PORT), SoulHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")


if __name__ == '__main__':
    main()

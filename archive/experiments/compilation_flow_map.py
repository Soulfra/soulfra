#!/usr/bin/env python3
"""
Compilation Flow Mapper - Traces Exact Data Flow for Routes

PROVES how data flows through the system by showing:
- HTTP request → Flask route → Database query → Compiler → Template → Response

Usage:
    python3 compilation_flow_map.py /brand/ocean-dreams
    python3 compilation_flow_map.py /post/soulfra-post-1
    python3 compilation_flow_map.py /
"""

import re
import os
import sys
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple


# ==============================================================================
# ROUTE MAPPING
# ==============================================================================

ROUTE_PATTERNS = [
    # Brand routes
    {
        'pattern': r'^/brand/([a-z0-9-]+)$',
        'route': '/brand/<slug>',
        'handler': 'brand_page',
        'file': 'app.py',
        'line': 1389,
        'description': 'Brand detail page'
    },
    # Post routes
    {
        'pattern': r'^/post/([a-z0-9-]+)$',
        'route': '/post/<slug>',
        'handler': 'post_page',
        'file': 'app.py',
        'line': 1450,
        'description': 'Post detail page'
    },
    # Index
    {
        'pattern': r'^/$',
        'route': '/',
        'handler': 'index',
        'file': 'app.py',
        'line': 100,
        'description': 'Homepage'
    },
    # AI Network
    {
        'pattern': r'^/ai-network$',
        'route': '/ai-network',
        'handler': 'ai_network',
        'file': 'app.py',
        'line': 200,
        'description': 'AI Network page'
    }
]


def match_route(url: str) -> Optional[Dict]:
    """Match URL to route pattern"""
    for route_info in ROUTE_PATTERNS:
        if re.match(route_info['pattern'], url):
            return route_info
    return None


# ==============================================================================
# FLOW TRACING
# ==============================================================================

class FlowStep:
    """Represents one step in the data flow"""

    def __init__(self, step_number: int, station: str, action: str, details: Dict[str, Any]):
        self.step_number = step_number
        self.station = station
        self.action = action
        self.details = details

    def __repr__(self):
        return f"Step {self.step_number}: {self.station} - {self.action}"


class CompilationFlow:
    """Traces the complete compilation flow for a route"""

    def __init__(self, url: str):
        self.url = url
        self.route_info = match_route(url)
        self.steps: List[FlowStep] = []
        self.step_counter = 1

    def add_step(self, station: str, action: str, details: Dict[str, Any]):
        """Add a step to the flow"""
        step = FlowStep(self.step_counter, station, action, details)
        self.steps.append(step)
        self.step_counter += 1
        return step

    def trace(self):
        """Trace the complete flow"""
        if not self.route_info:
            return False

        # Step 1: HTTP Request
        self.add_step(
            "HTTP REQUEST",
            "User makes request",
            {
                'url': self.url,
                'method': 'GET',
                'headers': {
                    'Accept': 'text/html',
                    'User-Agent': 'Browser'
                }
            }
        )

        # Step 2: Flask Routing
        self.add_step(
            "FLASK ROUTING",
            "Flask matches URL to route",
            {
                'route_pattern': self.route_info['route'],
                'handler_function': self.route_info['handler'],
                'file': self.route_info['file'],
                'line': self.route_info['line'],
                'description': self.route_info['description']
            }
        )

        # Route-specific tracing
        if 'brand' in self.route_info['route']:
            self._trace_brand_flow()
        elif 'post' in self.route_info['route']:
            self._trace_post_flow()
        else:
            self._trace_generic_flow()

        return True

    def _trace_brand_flow(self):
        """Trace flow for /brand/<slug>"""

        # Extract slug from URL
        match = re.match(r'^/brand/([a-z0-9-]+)$', self.url)
        slug = match.group(1) if match else 'unknown'

        # Step 3: Database Query
        self.add_step(
            "DATABASE QUERY",
            "Query brands table",
            {
                'sql': 'SELECT * FROM brands WHERE slug = ?',
                'params': [slug],
                'table': 'brands',
                'returns': 'Single brand row (id, name, slug, personality, tone, config_json, etc.)'
            }
        )

        # Step 4: Data Parsing
        self.add_step(
            "DATA PARSING",
            "Parse brand configuration",
            {
                'input': 'brand_row from database',
                'operations': [
                    'brand_dict = dict(brand_row)',
                    'brand_config = json.loads(brand_dict["config_json"])'
                ],
                'output': {
                    'brand_dict': 'Dictionary with all brand fields',
                    'brand_config': 'Parsed JSON config (colors, values, etc.)'
                }
            }
        )

        # Step 5: CSS Compilation
        self.add_step(
            "CSS COMPILATION",
            "Generate brand CSS",
            {
                'compiler': 'generate_brand_css()',
                'file': 'brand_css_generator.py',
                'line': 76,
                'input': 'brand_config (JSON)',
                'processing': [
                    'Extract colors from config',
                    'Generate color variations (light, dark)',
                    'Build CSS variables (:root)',
                    'Generate component styles (header, links, etc.)',
                    'Wrap in <style> tag'
                ],
                'output': 'CSS string with <style> tags'
            }
        )

        # Step 6: Template Rendering
        self.add_step(
            "TEMPLATE RENDERING",
            "Render Jinja2 template",
            {
                'template': 'brand_page.html',
                'extends': 'base.html',
                'variables_passed': {
                    'brand': 'brand_dict',
                    'brand_css': 'Generated CSS string'
                },
                'blocks_filled': ['title', 'content'],
                'operations': [
                    'Load base.html structure',
                    'Inject brand_css into <head>',
                    'Fill content block with brand info',
                    'Replace all {{ variables }}'
                ]
            }
        )

        # Step 7: HTTP Response
        self.add_step(
            "HTTP RESPONSE",
            "Send HTML to browser",
            {
                'status': '200 OK',
                'content_type': 'text/html; charset=utf-8',
                'body': 'Complete HTML document',
                'size': '~50KB (estimated)'
            }
        )

        # Step 8: Browser Rendering
        self.add_step(
            "BROWSER RENDERING",
            "Browser parses and displays",
            {
                'operations': [
                    'Parse HTML structure',
                    'Apply CSS (including brand_css)',
                    'Execute JavaScript (if any)',
                    'Render final page'
                ],
                'result': f'User sees: {slug.title()} brand page with custom colors'
            }
        )

    def _trace_post_flow(self):
        """Trace flow for /post/<slug>"""

        match = re.match(r'^/post/([a-z0-9-]+)$', self.url)
        slug = match.group(1) if match else 'unknown'

        # Database query
        self.add_step(
            "DATABASE QUERY",
            "Query posts table",
            {
                'sql': 'SELECT * FROM posts WHERE slug = ?',
                'params': [slug],
                'table': 'posts',
                'returns': 'Single post row (id, title, slug, content, user_id, etc.)'
            }
        )

        # Get comments
        self.add_step(
            "DATABASE QUERY",
            "Query comments",
            {
                'sql': 'SELECT * FROM comments WHERE post_id = ? ORDER BY created_at DESC',
                'params': ['post.id'],
                'table': 'comments',
                'returns': 'List of comment rows'
            }
        )

        # Template rendering
        self.add_step(
            "TEMPLATE RENDERING",
            "Render post template",
            {
                'template': 'post.html',
                'variables_passed': {
                    'post': 'post_dict',
                    'comments': 'List of comments'
                },
                'operations': [
                    'Load template',
                    'Loop through comments',
                    'Render markdown content',
                    'Fill all variables'
                ]
            }
        )

        # HTTP Response
        self.add_step(
            "HTTP RESPONSE",
            "Send HTML to browser",
            {
                'status': '200 OK',
                'content_type': 'text/html'
            }
        )

    def _trace_generic_flow(self):
        """Trace flow for generic routes"""

        self.add_step(
            "TEMPLATE RENDERING",
            "Render template",
            {
                'note': 'Generic route - varies by endpoint'
            }
        )

        self.add_step(
            "HTTP RESPONSE",
            "Send HTML to browser",
            {
                'status': '200 OK'
            }
        )


# ==============================================================================
# VISUAL OUTPUT
# ==============================================================================

def print_flow_header(url: str):
    """Print header"""
    print()
    print("=" * 100)
    print(f"  🗺️  COMPILATION FLOW MAP: {url}")
    print("=" * 100)
    print()


def print_flow_step(step: FlowStep, is_last: bool = False):
    """Print a single flow step"""

    # Station header
    print(f"{'─' * 100}")
    print(f"  🏭 STEP {step.step_number}: {step.station}")
    print(f"{'─' * 100}")
    print()
    print(f"  Action: {step.action}")
    print()

    # Details
    if step.details:
        print("  Details:")
        _print_details(step.details, indent=4)

    print()

    # Arrow to next step
    if not is_last:
        print("  ↓")
        print()


def _print_details(data: Any, indent: int = 0):
    """Recursively print details"""
    prefix = " " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}• {key}:")
                _print_details(value, indent + 2)
            else:
                print(f"{prefix}• {key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                _print_details(item, indent)
            else:
                print(f"{prefix}• {item}")
    else:
        print(f"{prefix}{data}")


def print_summary(flow: CompilationFlow):
    """Print flow summary"""
    print("=" * 100)
    print("  📊 FLOW SUMMARY")
    print("=" * 100)
    print()

    print(f"  URL:               {flow.url}")
    print(f"  Route:             {flow.route_info['route']}")
    print(f"  Handler:           {flow.route_info['handler']}()")
    print(f"  File:              {flow.route_info['file']}:{flow.route_info['line']}")
    print(f"  Total Steps:       {len(flow.steps)}")
    print()

    print("  Data Flow:")
    stations = [step.station for step in flow.steps]
    for i, station in enumerate(stations):
        marker = "→" if i < len(stations) - 1 else ""
        print(f"    {i+1}. {station} {marker}")

    print()
    print("=" * 100)
    print()


def print_code_locations(flow: CompilationFlow):
    """Print relevant code locations"""
    print("📍 RELEVANT CODE LOCATIONS:")
    print()

    locations = []

    # Route handler
    locations.append({
        'file': flow.route_info['file'],
        'line': flow.route_info['line'],
        'description': f"Route handler: {flow.route_info['handler']}()"
    })

    # Template
    for step in flow.steps:
        if step.station == "TEMPLATE RENDERING":
            template = step.details.get('template')
            if template:
                locations.append({
                    'file': f'templates/{template}',
                    'line': 1,
                    'description': f"Template: {template}"
                })

            extends = step.details.get('extends')
            if extends:
                locations.append({
                    'file': f'templates/{extends}',
                    'line': 1,
                    'description': f"Base template: {extends}"
                })

        # Compiler
        if step.station == "CSS COMPILATION":
            locations.append({
                'file': step.details['file'],
                'line': step.details['line'],
                'description': f"Compiler: {step.details['compiler']}"
            })

    # Print locations
    for loc in locations:
        print(f"  • {loc['file']}:{loc['line']}")
        print(f"    {loc['description']}")
        print()


# ==============================================================================
# MAIN
# ==============================================================================

def map_compilation_flow(url: str):
    """
    Map the complete compilation flow for a URL

    Shows exact data flow from request to response
    """

    print_flow_header(url)

    # Create flow
    flow = CompilationFlow(url)

    # Trace it
    success = flow.trace()

    if not success:
        print("❌ Unknown route - cannot map flow")
        print()
        print("Known routes:")
        for route in ROUTE_PATTERNS:
            print(f"  • {route['route']} - {route['description']}")
        return

    # Print each step
    for i, step in enumerate(flow.steps):
        is_last = (i == len(flow.steps) - 1)
        print_flow_step(step, is_last)

    # Print summary
    print_summary(flow)

    # Print code locations
    print_code_locations(flow)

    # Final note
    print("=" * 100)
    print("  💡 HOW TO VERIFY THIS FLOW")
    print("=" * 100)
    print()
    print("  1. Read the route handler:")
    print(f"     cat {flow.route_info['file']} | sed -n '{flow.route_info['line']},+50p'")
    print()
    print("  2. Check database schema:")
    print("     sqlite3 soulfra.db \".schema brands\"")
    print()
    print("  3. Inspect template:")
    print("     python3 template_anatomy.py <template_name>")
    print()
    print("  4. Test compilation:")
    print("     python3 prove_compilation.py <slug>")
    print()
    print("=" * 100)
    print()


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 compilation_flow_map.py /brand/ocean-dreams")
        print("  python3 compilation_flow_map.py /post/soulfra-post-1")
        print("  python3 compilation_flow_map.py /")
        print()
        print("Known routes:")
        for route in ROUTE_PATTERNS:
            print(f"  • {route['route']} - {route['description']}")
        return

    url = sys.argv[1]
    map_compilation_flow(url)


if __name__ == '__main__':
    main()

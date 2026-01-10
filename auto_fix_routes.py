#!/usr/bin/env python3
"""
Automated Route Fixer - Uses Ollama + SQLite to fix broken Flask routes

This is what you were talking about - using our automation infrastructure
(Ollama AI + SQLite + health scanner) to systematically debug and fix issues
instead of manual debugging.
"""

import json
import requests
import subprocess
import sys

def get_ollama_fix(route, error_info, code_snippet):
    """
    Ask Ollama to analyze the broken route and suggest a fix

    This leverages your 22 Ollama models to do the debugging work
    """
    prompt = f"""You are debugging a Flask route that returns HTTP 500 error.

ROUTE: {route}
ERROR: {error_info}

CURRENT CODE:
```python
{code_snippet}
```

TASK: Identify why this route crashes and provide a fix.

Common issues:
- Missing database columns/tables
- Missing imports
- None/null values not handled
- Wrong variable names
- Missing try/except blocks

Respond with ONLY the fixed Python code, no explanation. The code should:
1. Handle missing data gracefully
2. Return proper JSON responses
3. Use try/except for error handling
"""

    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'mistral:latest',
        'prompt': prompt,
        'stream': False
    }, timeout=60)

    return response.json()['response']


def extract_route_code(route_path, app_py_path='app.py'):
    """
    Extract the function code for a specific route from app.py
    """
    with open(app_py_path, 'r') as f:
        lines = f.readlines()

    # Find the route decorator
    route_line = None
    for i, line in enumerate(lines):
        if f"@app.route('{route_path}')" in line:
            route_line = i
            break

    if route_line is None:
        return None

    # Extract function code (next decorator or blank line marks end)
    code_lines = [lines[route_line]]
    for i in range(route_line + 1, len(lines)):
        line = lines[i]

        # Stop at next route decorator or next function
        if line.strip().startswith('@app.route') or \
           (line.strip().startswith('def ') and i > route_line + 5):
            break

        code_lines.append(line)

    return ''.join(code_lines), route_line


def fix_route(route_path):
    """
    Use Ollama to fix a single broken route
    """
    print(f"\n🔧 Fixing: {route_path}")

    # Extract current code
    result = extract_route_code(route_path)
    if not result:
        print(f"   ❌ Could not find route in app.py")
        return False

    code_snippet, line_number = result
    print(f"   📍 Found at line {line_number}")

    # Get fix from Ollama
    print(f"   🤖 Asking Ollama for fix...")
    try:
        fixed_code = get_ollama_fix(route_path, "HTTP 500 error", code_snippet)
        print(f"   ✅ Ollama suggested fix ({len(fixed_code)} chars)")

        # Save suggested fix for review
        fix_file = f"/tmp/fix_{route_path.replace('/', '_')}.py"
        with open(fix_file, 'w') as f:
            f.write(fixed_code)

        print(f"   💾 Saved to {fix_file}")
        return True

    except Exception as e:
        print(f"   ❌ Ollama error: {e}")
        return False


def main():
    """
    Main automation: Fix all 10 broken routes using Ollama
    """
    print("="*80)
    print("🤖 AUTOMATED ROUTE FIXER")
    print("Using: Ollama AI + SQLite + Health Scanner")
    print("="*80)

    # Load broken routes from health scan
    with open('/tmp/broken_routes.txt', 'r') as f:
        broken_routes = [line.strip() for line in f if line.strip()]

    print(f"\n📊 Found {len(broken_routes)} broken routes")

    # Fix each route
    fixed_count = 0
    for i, route in enumerate(broken_routes[:3], 1):  # Start with first 3
        if fix_route(route):
            fixed_count += 1

    print(f"\n" + "="*80)
    print(f"✅ Generated fixes for {fixed_count}/{min(3, len(broken_routes))} routes")
    print(f"📁 Review fixes in /tmp/fix_*.py")
    print(f"\nNext steps:")
    print(f"1. Review Ollama's suggested fixes")
    print(f"2. Apply fixes to app.py")
    print(f"3. Restart Flask")
    print(f"4. Re-run health scanner")
    print("="*80)


if __name__ == '__main__':
    main()

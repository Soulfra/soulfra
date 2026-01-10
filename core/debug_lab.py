#!/usr/bin/env python3
"""
Debug Lab - Interactive Learning Environment

Teaches users how to debug, search logs, and use Linux commands
through visual interfaces and AI assistance.

Features:
- Live log streaming
- Error explanation (Ollama-powered)
- Command teaching (grep, curl, awk, tail)
- Debug challenges
- Context-aware AI help

Routes:
    GET  /api/debug/logs/recent        - Get recent log lines
    POST /api/debug/explain            - Explain error with Ollama
    POST /api/debug/command/grep       - Run safe grep command
    POST /api/debug/command/tail       - Tail log file
    GET  /api/debug/challenges         - Get debug challenges
    POST /api/debug/challenge/complete - Mark challenge as complete
"""

from flask import Blueprint, jsonify, request
import subprocess
import os
import re
import json
import requests
from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime


# ==============================================================================
# BLUEPRINT SETUP
# ==============================================================================

debug_lab = Blueprint('debug_lab', __name__, url_prefix='/api/debug')


# ==============================================================================
# LOG MANAGEMENT
# ==============================================================================

# In-memory log buffer (last 1000 lines)
log_buffer = deque(maxlen=1000)

def add_log_line(line: str):
    """Add line to log buffer"""
    log_buffer.append({
        'line': line,
        'timestamp': datetime.now().isoformat(),
        'level': detect_log_level(line)
    })

def detect_log_level(line: str) -> str:
    """Detect log level from line content"""
    line_lower = line.lower()

    if 'error' in line_lower or '500' in line or 'traceback' in line_lower:
        return 'error'
    elif 'warning' in line_lower or 'warn' in line_lower:
        return 'warning'
    elif '404' in line or '302' in line or '301' in line:
        return 'info'
    elif 'success' in line_lower or '200' in line or '✅' in line:
        return 'success'
    else:
        return 'debug'


@debug_lab.route('/logs/recent', methods=['GET'])
def get_recent_logs():
    """
    Get recent log lines

    Query params:
        limit: Max lines to return (default 100)
        level: Filter by level (error, warning, info, success, debug)
        pattern: Grep-style pattern to match

    Returns:
        JSON: {
            'logs': [...],
            'count': 100,
            'command': 'grep "pattern" | tail -100'
        }
    """
    limit = int(request.args.get('limit', 100))
    level = request.args.get('level', '')
    pattern = request.args.get('pattern', '')

    logs = list(log_buffer)

    # Filter by level
    if level:
        logs = [log for log in logs if log['level'] == level]

    # Filter by pattern (grep-style)
    if pattern:
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            logs = [log for log in logs if regex.search(log['line'])]
        except re.error:
            return jsonify({'error': f'Invalid regex pattern: {pattern}'}), 400

    # Limit results
    logs = logs[-limit:]

    # Generate equivalent Linux command
    command = 'tail -1000 flask.log'
    if pattern:
        command += f' | grep "{pattern}"'
    if limit != 100:
        command += f' | tail -{limit}'

    return jsonify({
        'logs': logs,
        'count': len(logs),
        'command': command,
        'tutorial': f'This is like running: {command}'
    })


# ==============================================================================
# ERROR EXPLANATION (OLLAMA-POWERED)
# ==============================================================================

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')


@debug_lab.route('/explain', methods=['POST'])
def explain_error():
    """
    Explain error using Ollama AI

    Request body:
        {
            'error': 'Error message or log line',
            'context': 'Optional context (file, line number, etc.)',
            'model': 'llama3.2:3b'  # optional
        }

    Returns:
        JSON: {
            'explanation': '...',
            'fix': '...',
            'debug_steps': [...],
            'linux_commands': [...]
        }
    """
    data = request.get_json()
    error = data.get('error', '')
    context = data.get('context', '')
    model = data.get('model', 'llama3.2:3b')

    if not error:
        return jsonify({'error': 'No error provided'}), 400

    # Build prompt for Ollama
    prompt = f"""You are a debugging teacher. Explain this error to a developer learning Linux and Python.

Error:
{error}

Context:
{context if context else 'None provided'}

Provide:
1. **What happened** - Simple explanation
2. **Why it happened** - Root cause
3. **How to fix** - Step-by-step solution
4. **Debug commands** - Linux commands to investigate (grep, tail, curl, etc.)
5. **Learn more** - What to study to prevent this

Be concise but thorough. Use examples. Teach, don't just fix."""

    try:
        # Call Ollama API
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        explanation = result.get('response', '')

        # Parse response (try to extract structured info)
        debug_steps = extract_debug_steps(explanation)
        linux_commands = extract_linux_commands(explanation)

        return jsonify({
            'explanation': explanation,
            'debug_steps': debug_steps,
            'linux_commands': linux_commands,
            'model_used': model
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Ollama API error: {str(e)}',
            'message': 'Is Ollama running at localhost:11434?'
        }), 500


def extract_debug_steps(text: str) -> List[str]:
    """Extract numbered steps from Ollama response"""
    steps = []
    lines = text.split('\n')

    for line in lines:
        # Match "1. " or "* " or "- "
        if re.match(r'^\s*\d+\.\s', line) or re.match(r'^\s*[\*\-]\s', line):
            steps.append(line.strip())

    return steps[:5]  # Max 5 steps


def extract_linux_commands(text: str) -> List[Dict[str, str]]:
    """Extract Linux commands from Ollama response"""
    commands = []

    # Look for common patterns: `command`, ```command```, or "command"
    code_blocks = re.findall(r'`([^`]+)`', text)

    for cmd in code_blocks:
        cmd = cmd.strip()
        # Only include if it looks like a Linux command
        if any(cmd.startswith(prefix) for prefix in ['grep', 'tail', 'curl', 'awk', 'sed', 'cat', 'ls']):
            commands.append({
                'command': cmd,
                'description': f'Run: {cmd}'
            })

    return commands[:3]  # Max 3 commands


# ==============================================================================
# SAFE COMMAND EXECUTION
# ==============================================================================

@debug_lab.route('/command/grep', methods=['POST'])
def run_grep_command():
    """
    Run safe grep command

    Request body:
        {
            'pattern': 'search pattern',
            'path': '.' or specific file,
            'flags': ['-r', '-i', '-n']  # optional
        }

    Returns:
        JSON: {
            'output': '...',
            'command': 'grep -r "pattern" .',
            'matches': 15
        }
    """
    data = request.get_json()
    pattern = data.get('pattern', '')
    path = data.get('path', '.')
    flags = data.get('flags', [])

    if not pattern:
        return jsonify({'error': 'No pattern provided'}), 400

    # Sanitize path (prevent directory traversal)
    if '..' in path or path.startswith('/'):
        return jsonify({'error': 'Invalid path'}), 400

    # Build grep command
    cmd = ['grep'] + flags + [pattern, path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )

        output = result.stdout if result.stdout else result.stderr
        matches = len(output.split('\n')) if output else 0

        return jsonify({
            'output': output[:5000],  # Limit output
            'command': ' '.join(cmd),
            'matches': matches,
            'tutorial': f'This searches for "{pattern}" in {path}'
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timeout'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@debug_lab.route('/command/tail', methods=['POST'])
def run_tail_command():
    """
    Run safe tail command

    Request body:
        {
            'file': 'logfile.log',
            'lines': 100
        }

    Returns:
        JSON: {
            'output': '...',
            'command': 'tail -100 logfile.log'
        }
    """
    data = request.get_json()
    file_path = data.get('file', '')
    lines = int(data.get('lines', 100))

    if not file_path:
        return jsonify({'error': 'No file provided'}), 400

    # Sanitize path
    if '..' in file_path or file_path.startswith('/'):
        return jsonify({'error': 'Invalid path'}), 400

    if not os.path.exists(file_path):
        return jsonify({'error': f'File not found: {file_path}'}), 404

    try:
        cmd = ['tail', f'-{lines}', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        return jsonify({
            'output': result.stdout,
            'command': ' '.join(cmd),
            'tutorial': f'Shows last {lines} lines of {file_path}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# DEBUG CHALLENGES
# ==============================================================================

@debug_lab.route('/challenges', methods=['GET'])
def get_challenges():
    """
    Get debug challenges

    Returns:
        JSON: {
            'challenges': [
                {
                    'id': 1,
                    'title': 'Find the Redirect',
                    'description': '...',
                    'level': 'beginner',
                    'tasks': [...],
                    'reward': 'grep command mastery'
                }
            ]
        }
    """
    challenges = load_challenges()

    return jsonify({
        'challenges': challenges,
        'count': len(challenges)
    })


@debug_lab.route('/challenge/complete', methods=['POST'])
def complete_challenge():
    """
    Mark challenge as complete

    Request body:
        {
            'challenge_id': 1,
            'user_id': 'optional',
            'solution': 'User's solution'
        }

    Returns:
        JSON: {
            'success': true,
            'reward': '...',
            'next_challenge': {...}
        }
    """
    data = request.get_json()
    challenge_id = data.get('challenge_id')

    if not challenge_id:
        return jsonify({'error': 'No challenge_id provided'}), 400

    # TODO: Store completion in database
    # For now, just return success

    challenges = load_challenges()
    next_challenge = None

    for i, challenge in enumerate(challenges):
        if challenge['id'] == challenge_id:
            if i + 1 < len(challenges):
                next_challenge = challenges[i + 1]
            break

    return jsonify({
        'success': True,
        'message': '🎉 Challenge complete!',
        'next_challenge': next_challenge
    })


def load_challenges() -> List[Dict[str, Any]]:
    """Load challenges from debug_challenges.json"""
    challenges_file = 'debug_challenges.json'

    if not os.path.exists(challenges_file):
        # Return default challenges
        return get_default_challenges()

    try:
        with open(challenges_file, 'r') as f:
            return json.load(f)
    except:
        return get_default_challenges()


def get_default_challenges() -> List[Dict[str, Any]]:
    """Default debug challenges"""
    return [
        {
            'id': 1,
            'title': 'Find the Redirect',
            'description': 'You visited /admin/studio but got redirected to /admin/login. Why?',
            'level': 'beginner',
            'tasks': [
                'Look at server logs for "302" status code',
                'Find which function caused the redirect',
                'Understand how session cookies work'
            ],
            'hints': [
                'Use grep to search logs: grep "302" logs',
                'Check require_admin() function',
                'Sessions need cookies to persist'
            ],
            'reward': '🏆 Redirect Debugger Badge',
            'learn': 'HTTP redirects, session management, grep basics'
        },
        {
            'id': 2,
            'title': 'Parse JSON Logs',
            'description': 'Extract error messages from JSON log files',
            'level': 'intermediate',
            'tasks': [
                'Use jq to parse JSON',
                'Filter only error-level logs',
                'Count how many errors occurred'
            ],
            'hints': [
                'jq ".level" logfile.json',
                'jq "select(.level == \\"error\\")"',
                'Pipe to wc -l to count'
            ],
            'reward': '🏆 JSON Parser Badge',
            'learn': 'jq command, JSON parsing, piping'
        },
        {
            'id': 3,
            'title': 'Debug Test Failure',
            'description': 'One test is failing. Find it and understand why.',
            'level': 'intermediate',
            'tasks': [
                'Run all tests visually',
                'Identify the failing test',
                'Read the error message',
                'Use Ollama to explain the error'
            ],
            'hints': [
                'Use the Test Runner tab',
                'Click "Explain Error" on failure',
                'Check test file for assertions'
            ],
            'reward': '🏆 Test Detective Badge',
            'learn': 'Test debugging, error analysis, AI assistance'
        }
    ]


# ==============================================================================
# REGISTRATION
# ==============================================================================

def register_debug_lab(app):
    """
    Register Debug Lab blueprint with Flask app

    Args:
        app: Flask application

    Returns:
        Blueprint instance
    """
    app.register_blueprint(debug_lab)

    print("✅ Debug Lab registered at /api/debug/*")

    return debug_lab

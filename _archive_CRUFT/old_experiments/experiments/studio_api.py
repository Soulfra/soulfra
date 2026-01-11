#!/usr/bin/env python3
"""
Studio API - Backend Routes for Visual Development Studio

Provides REST API endpoints for:
- Test runner (list, run, auto-loop)
- Ollama chat integration
- Code generation
- Neural network training
- Schema compilation

Setup:
    from studio_api import register_studio_api
    register_studio_api(app, socketio)

Routes:
    GET  /api/studio/list-tests       - List all test files
    POST /api/studio/run-test         - Run specific test
    POST /api/studio/run-all-tests    - Run all tests
    POST /api/studio/ollama-chat      - Chat with Ollama
    POST /api/studio/generate-code    - Generate Python code
    POST /api/studio/compile-schema   - Compile JSON schema
"""

from flask import Blueprint, jsonify, request
import os
import sys
import json
import requests
from typing import Dict, Any, Optional

# Import test runner
from test_runner import discover_tests, run_test, run_all_tests


# ==============================================================================
# BLUEPRINT SETUP
# ==============================================================================

studio_api = Blueprint('studio_api', __name__, url_prefix='/api/studio')


# ==============================================================================
# TEST RUNNER API
# ==============================================================================

@studio_api.route('/list-tests', methods=['GET'])
def list_tests():
    """
    Get list of all test files

    Returns:
        JSON: {
            'tests': ['test_database.py', 'test_emails.py', ...]
        }
    """
    tests = discover_tests()

    return jsonify({
        'tests': tests,
        'count': len(tests)
    })


@studio_api.route('/run-test', methods=['POST'])
def run_test_api():
    """
    Run a specific test

    Request Body:
        {
            'test_name': 'test_database.py'
        }

    Returns:
        JSON: {
            'passed': true,
            'stdout': '...',
            'stderr': '...'
        }
    """
    data = request.get_json()
    test_name = data.get('test_name')

    if not test_name:
        return jsonify({'error': 'test_name required'}), 400

    if not os.path.exists(test_name):
        return jsonify({'error': f'Test file not found: {test_name}'}), 404

    passed, stdout, stderr = run_test(test_name)

    return jsonify({
        'test_name': test_name,
        'passed': passed,
        'stdout': stdout,
        'stderr': stderr
    })


@studio_api.route('/run-all-tests', methods=['POST'])
def run_all_tests_api():
    """
    Run all tests

    Returns:
        JSON: {
            'results': {
                'test_database.py': true,
                'test_emails.py': false,
                ...
            },
            'passed_count': 15,
            'total_count': 19
        }
    """
    results = run_all_tests()

    passed_count = sum(1 for p in results.values() if p)

    return jsonify({
        'results': results,
        'passed_count': passed_count,
        'total_count': len(results)
    })


# ==============================================================================
# OLLAMA INTEGRATION - "we have ollama and can build"
# ==============================================================================

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')


@studio_api.route('/ollama-chat', methods=['POST'])
def ollama_chat():
    """
    Chat with Ollama

    Request Body:
        {
            'message': 'How do I write a neural network?',
            'model': 'llama3.2:3b'  # optional
        }

    Returns:
        JSON: {
            'response': '...',
            'model': 'llama3.2:3b'
        }
    """
    data = request.get_json()
    message = data.get('message')
    model = data.get('model', 'llama3.2:3b')

    if not message:
        return jsonify({'error': 'message required'}), 400

    try:
        # Call Ollama API
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                'model': model,
                'prompt': message,
                'stream': False
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        return jsonify({
            'response': result.get('response', ''),
            'model': model
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Ollama API error: {str(e)}',
            'message': 'Is Ollama running at localhost:11434?'
        }), 500


@studio_api.route('/ollama-models', methods=['GET'])
def ollama_models():
    """
    List available Ollama models

    Returns:
        JSON: {
            'models': ['llama3.2:3b', 'codellama', ...]
        }
    """
    try:
        response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
        response.raise_for_status()
        result = response.json()

        models = [model['name'] for model in result.get('models', [])]

        return jsonify({
            'models': models,
            'count': len(models)
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Ollama API error: {str(e)}',
            'models': []
        }), 500


# ==============================================================================
# CODE GENERATION - "compile with python"
# ==============================================================================

@studio_api.route('/generate-code', methods=['POST'])
def generate_code():
    """
    Generate Python code from visual configuration

    Request Body:
        {
            'type': 'neural_network',  # or 'schema', 'email_template'
            'config': {
                'layers': [
                    {'type': 'Dense', 'neurons': 128, 'activation': 'relu'},
                    {'type': 'Dense', 'neurons': 10, 'activation': 'softmax'}
                ]
            }
        }

    Returns:
        JSON: {
            'code': '# Generated Python code...',
            'filename': 'neural_network.py'
        }
    """
    data = request.get_json()
    code_type = data.get('type')
    config = data.get('config', {})

    if code_type == 'neural_network':
        code = generate_neural_network_code(config)
        filename = 'neural_network.py'

    elif code_type == 'schema':
        code = generate_schema_code(config)
        filename = 'schema.py'

    elif code_type == 'email_template':
        code = generate_email_template(config)
        filename = 'email_template.html'

    else:
        return jsonify({'error': f'Unknown type: {code_type}'}), 400

    return jsonify({
        'code': code,
        'filename': filename
    })


def generate_neural_network_code(config: Dict[str, Any]) -> str:
    """
    Generate PyTorch neural network code

    Args:
        config: {'layers': [...], 'optimizer': 'adam', ...}

    Returns:
        Python code as string
    """
    layers = config.get('layers', [])

    code = '# Generated by Soulfra Studio\n'
    code += 'import torch\n'
    code += 'import torch.nn as nn\n'
    code += 'import torch.optim as optim\n\n'

    code += 'class GeneratedNetwork(nn.Module):\n'
    code += '    def __init__(self, input_size):\n'
    code += '        super().__init__()\n'

    # Add layers
    for i, layer in enumerate(layers):
        layer_type = layer.get('type', 'Dense')
        neurons = layer.get('neurons', 64)

        if i == 0:
            prev_size = 'input_size'
        else:
            prev_size = layers[i-1].get('neurons', 64)

        if layer_type == 'Dense':
            code += f'        self.fc{i} = nn.Linear({prev_size}, {neurons})\n'
        elif layer_type == 'Conv2D':
            code += f'        self.conv{i} = nn.Conv2d(in_channels, {neurons}, kernel_size=3)\n'
        elif layer_type == 'Dropout':
            code += f'        self.dropout{i} = nn.Dropout(p=0.5)\n'

    code += '\n    def forward(self, x):\n'

    # Add forward pass
    for i, layer in enumerate(layers):
        layer_type = layer.get('type', 'Dense')
        activation = layer.get('activation', 'relu')

        if layer_type == 'Dense':
            code += f'        x = self.fc{i}(x)\n'
        elif layer_type == 'Conv2D':
            code += f'        x = self.conv{i}(x)\n'
        elif layer_type == 'Dropout':
            code += f'        x = self.dropout{i}(x)\n'

        # Add activation
        if activation == 'relu':
            code += f'        x = torch.relu(x)\n'
        elif activation == 'sigmoid':
            code += f'        x = torch.sigmoid(x)\n'
        elif activation == 'tanh':
            code += f'        x = torch.tanh(x)\n'
        elif activation == 'softmax':
            code += f'        x = torch.softmax(x, dim=1)\n'

    code += '        return x\n\n'

    # Add training function
    code += '# Training loop\n'
    code += 'def train(model, data_loader, epochs=10):\n'
    code += '    criterion = nn.CrossEntropyLoss()\n'
    code += '    optimizer = optim.Adam(model.parameters(), lr=0.001)\n\n'
    code += '    for epoch in range(epochs):\n'
    code += '        for batch_x, batch_y in data_loader:\n'
    code += '            optimizer.zero_grad()\n'
    code += '            outputs = model(batch_x)\n'
    code += '            loss = criterion(outputs, batch_y)\n'
    code += '            loss.backward()\n'
    code += '            optimizer.step()\n'
    code += '        print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")\n\n'

    code += '# Usage\n'
    code += 'if __name__ == "__main__":\n'
    code += '    model = GeneratedNetwork(input_size=784)\n'
    code += '    print(model)\n'

    return code


def generate_schema_code(config: Dict[str, Any]) -> str:
    """
    Generate Pydantic schema from JSON

    Args:
        config: {'name': 'User', 'fields': [...]}

    Returns:
        Python code as string
    """
    name = config.get('name', 'GeneratedModel')
    fields = config.get('fields', [])

    code = '# Generated by Soulfra Studio\n'
    code += 'from pydantic import BaseModel\n'
    code += 'from typing import Optional\n\n'

    code += f'class {name}(BaseModel):\n'

    for field in fields:
        field_name = field.get('name', 'field')
        field_type = field.get('type', 'str')
        required = field.get('required', True)

        if required:
            code += f'    {field_name}: {field_type}\n'
        else:
            code += f'    {field_name}: Optional[{field_type}] = None\n'

    code += '\n# Usage\n'
    code += f'# user = {name}(...)\n'

    return code


def generate_email_template(config: Dict[str, Any]) -> str:
    """
    Generate Jinja2 email template

    Args:
        config: {'subject': '...', 'body': '...', 'brand': '...'}

    Returns:
        HTML template as string
    """
    subject = config.get('subject', 'Newsletter')
    body = config.get('body', 'Content goes here')
    brand = config.get('brand', 'Soulfra')

    html = f'<!-- Generated by Soulfra Studio -->\n'
    html += '<!DOCTYPE html>\n'
    html += '<html>\n'
    html += '<head>\n'
    html += f'    <title>{subject}</title>\n'
    html += '</head>\n'
    html += '<body style="font-family: Arial, sans-serif; padding: 20px;">\n'
    html += f'    <h1>{subject}</h1>\n'
    html += f'    <div>{body}</div>\n'
    html += f'    <p style="color: #666; margin-top: 40px;">— {brand}</p>\n'
    html += '    <p><a href="{{{{ unsubscribe_url }}}}">Unsubscribe</a></p>\n'
    html += '</body>\n'
    html += '</html>\n'

    return html


# ==============================================================================
# SCHEMA COMPILATION - "structured enough"
# ==============================================================================

@studio_api.route('/compile-schema', methods=['POST'])
def compile_schema():
    """
    Compile JSON schema to Python dataclass/Pydantic model

    Request Body:
        {
            'schema': {...},
            'format': 'pydantic'  # or 'dataclass'
        }

    Returns:
        JSON: {
            'code': '...',
            'errors': []
        }
    """
    data = request.get_json()
    schema = data.get('schema', {})
    format_type = data.get('format', 'pydantic')

    try:
        if format_type == 'pydantic':
            code = generate_schema_code(schema)
        else:
            code = generate_dataclass_code(schema)

        return jsonify({
            'code': code,
            'errors': []
        })

    except Exception as e:
        return jsonify({
            'code': '',
            'errors': [str(e)]
        }), 500


def generate_dataclass_code(config: Dict[str, Any]) -> str:
    """Generate Python dataclass"""
    name = config.get('name', 'GeneratedModel')
    fields = config.get('fields', [])

    code = '# Generated by Soulfra Studio\n'
    code += 'from dataclasses import dataclass\n'
    code += 'from typing import Optional\n\n'

    code += '@dataclass\n'
    code += f'class {name}:\n'

    for field in fields:
        field_name = field.get('name', 'field')
        field_type = field.get('type', 'str')
        required = field.get('required', True)

        if required:
            code += f'    {field_name}: {field_type}\n'
        else:
            code += f'    {field_name}: Optional[{field_type}] = None\n'

    return code


# ==============================================================================
# REGISTRATION
# ==============================================================================

def register_studio_api(app, socketio=None):
    """
    Register Studio API blueprint with Flask app

    Args:
        app: Flask application
        socketio: SocketIO instance (optional)

    Returns:
        Blueprint instance
    """
    app.register_blueprint(studio_api)

    print("✅ Studio API registered at /api/studio/*")

    return studio_api

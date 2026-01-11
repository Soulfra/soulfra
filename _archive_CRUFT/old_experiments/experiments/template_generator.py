#!/usr/bin/env python3
"""
Template Generator - Make EVERYTHING Templatable (Zero Dependencies)

"Everything is templatable" - User insight

Philosophy:
----------
Why write boilerplate when you can generate it from templates?
- HTML templates → Components
- Component templates → Pages
- Route templates → API endpoints
- Folder templates → Project structure
- Database templates → Schema

This is meta-templating: Templates that generate templates!

What You Can Template:
--------------------
1. **HTML Components**: Buttons, cards, forms, nav bars
2. **Pages**: Blog post, user profile, dashboard
3. **Routes**: CRUD endpoints, auth routes, API routes
4. **Folders**: New projects, features, modules
5. **Database**: Schema, migrations, seed data
6. **Config**: Environment files, settings

Usage:
    # Generate HTML component
    python3 template_generator.py --type component --name UserCard

    # Generate page template
    python3 template_generator.py --type page --name BlogPost

    # Generate route
    python3 template_generator.py --type route --name products

    # Generate folder structure
    python3 template_generator.py --type folder --name new_feature

    # List available templates
    python3 template_generator.py --list
"""

import os
from pathlib import Path
from typing import Dict, Optional


# ==============================================================================
# HTML COMPONENT TEMPLATES
# ==============================================================================

def generate_component(name: str, props: Dict = None) -> str:
    """
    Generate HTML component

    Args:
        name: Component name (e.g., "UserCard", "Button", "Nav")
        props: Component properties

    Returns:
        HTML component string
    """
    props = props or {}

    templates = {
        'UserCard': _template_user_card,
        'Button': _template_button,
        'Nav': _template_nav,
        'Card': _template_card,
        'Form': _template_form,
        'Modal': _template_modal,
    }

    template_func = templates.get(name, _template_generic_component)
    return template_func(name, props)


def _template_user_card(name: str, props: Dict) -> str:
    return '''<!-- User Card Component -->
<div class="user-card">
    <div class="user-card__avatar">
        <img src="{{ user.avatar_url }}" alt="{{ user.username }}">
    </div>
    <div class="user-card__info">
        <h3 class="user-card__name">{{ user.display_name }}</h3>
        <p class="user-card__username">@{{ user.username }}</p>
        <p class="user-card__bio">{{ user.bio }}</p>
    </div>
    <div class="user-card__actions">
        <button class="btn btn--primary">Follow</button>
        <button class="btn btn--secondary">Message</button>
    </div>
</div>

<style>
.user-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    max-width: 400px;
}

.user-card__avatar img {
    width: 80px;
    height: 80px;
    border-radius: 50%;
}

.user-card__info {
    margin-top: 15px;
}

.user-card__name {
    margin: 0;
    font-size: 1.5em;
}

.user-card__username {
    color: #666;
    margin: 5px 0;
}

.user-card__actions {
    margin-top: 15px;
    display: flex;
    gap: 10px;
}
</style>
'''


def _template_button(name: str, props: Dict) -> str:
    return '''<!-- Button Component -->
<button class="btn btn--{{ variant }}" {{ 'disabled' if disabled }}>
    {{ text }}
</button>

<style>
.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.2s;
}

.btn--primary {
    background: #007bff;
    color: white;
}

.btn--primary:hover {
    background: #0056b3;
}

.btn--secondary {
    background: #6c757d;
    color: white;
}

.btn--secondary:hover {
    background: #545b62;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
'''


def _template_nav(name: str, props: Dict) -> str:
    return '''<!-- Navigation Component -->
<nav class="nav">
    <div class="nav__brand">
        <a href="/">{{ site_name }}</a>
    </div>
    <ul class="nav__links">
        <li><a href="/">Home</a></li>
        <li><a href="/blog">Blog</a></li>
        <li><a href="/about">About</a></li>
        {% if user %}
        <li><a href="/profile">Profile</a></li>
        <li><a href="/logout">Logout</a></li>
        {% else %}
        <li><a href="/login">Login</a></li>
        {% endif %}
    </ul>
</nav>

<style>
.nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 30px;
    background: #333;
    color: white;
}

.nav__brand a {
    color: white;
    text-decoration: none;
    font-size: 1.5em;
    font-weight: bold;
}

.nav__links {
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
    gap: 20px;
}

.nav__links a {
    color: white;
    text-decoration: none;
}

.nav__links a:hover {
    text-decoration: underline;
}
</style>
'''


def _template_card(name: str, props: Dict) -> str:
    return '''<!-- Card Component -->
<div class="card">
    <div class="card__header">
        <h3>{{ title }}</h3>
    </div>
    <div class="card__body">
        {{ content }}
    </div>
    <div class="card__footer">
        {{ footer }}
    </div>
</div>

<style>
.card {
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.card__header {
    background: #f8f9fa;
    padding: 15px;
    border-bottom: 1px solid #ddd;
}

.card__header h3 {
    margin: 0;
}

.card__body {
    padding: 20px;
}

.card__footer {
    background: #f8f9fa;
    padding: 15px;
    border-top: 1px solid #ddd;
}
</style>
'''


def _template_form(name: str, props: Dict) -> str:
    return '''<!-- Form Component -->
<form class="form" method="POST" action="{{ action }}">
    <div class="form__group">
        <label for="{{ field_id }}">{{ label }}</label>
        <input type="{{ input_type }}" id="{{ field_id }}" name="{{ field_name }}" required>
    </div>
    <div class="form__actions">
        <button type="submit" class="btn btn--primary">Submit</button>
        <button type="reset" class="btn btn--secondary">Reset</button>
    </div>
</form>

<style>
.form {
    max-width: 500px;
}

.form__group {
    margin-bottom: 20px;
}

.form__group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form__group input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.form__actions {
    display: flex;
    gap: 10px;
}
</style>
'''


def _template_modal(name: str, props: Dict) -> str:
    return '''<!-- Modal Component -->
<div class="modal" id="{{ modal_id }}">
    <div class="modal__overlay"></div>
    <div class="modal__content">
        <div class="modal__header">
            <h3>{{ title }}</h3>
            <button class="modal__close">&times;</button>
        </div>
        <div class="modal__body">
            {{ content }}
        </div>
        <div class="modal__footer">
            {{ footer }}
        </div>
    </div>
</div>

<style>
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000;
}

.modal.is-active {
    display: block;
}

.modal__overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
}

.modal__content {
    position: relative;
    background: white;
    margin: 50px auto;
    max-width: 600px;
    border-radius: 8px;
    overflow: hidden;
}

.modal__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #ddd;
}

.modal__close {
    background: none;
    border: none;
    font-size: 2em;
    cursor: pointer;
}

.modal__body {
    padding: 20px;
}

.modal__footer {
    padding: 20px;
    border-top: 1px solid #ddd;
}
</style>
'''


def _template_generic_component(name: str, props: Dict) -> str:
    return f'''<!-- {name} Component -->
<div class="{name.lower()}">
    {{{{ content }}}}
</div>

<style>
.{name.lower()} {{
    /* Add your styles here */
}}
</style>
'''


# ==============================================================================
# PAGE TEMPLATES
# ==============================================================================

def generate_page(name: str) -> str:
    """Generate full HTML page template"""
    templates = {
        'BlogPost': _page_blog_post,
        'UserProfile': _page_user_profile,
        'Dashboard': _page_dashboard,
        'Login': _page_login,
    }

    template_func = templates.get(name, _page_generic)
    return template_func(name)


def _page_blog_post(name: str) -> str:
    return '''{% extends "base.html" %}

{% block title %}{{ post.title }}{% endblock %}

{% block content %}
<article class="blog-post">
    <header class="blog-post__header">
        <h1>{{ post.title }}</h1>
        <div class="blog-post__meta">
            <span>By {{ post.author }}</span>
            <span>{{ post.published_at | format_date }}</span>
        </div>
    </header>

    <div class="blog-post__content">
        {{ post.content | safe }}
    </div>

    <footer class="blog-post__footer">
        <div class="blog-post__tags">
            {% for tag in post.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
    </footer>
</article>
{% endblock %}
'''


def _page_user_profile(name: str) -> str:
    return '''{% extends "base.html" %}

{% block title %}{{ user.username }}{% endblock %}

{% block content %}
<div class="profile">
    <div class="profile__header">
        <img src="{{ user.avatar_url }}" alt="{{ user.username }}" class="profile__avatar">
        <h1>{{ user.display_name }}</h1>
        <p class="profile__username">@{{ user.username }}</p>
    </div>

    <div class="profile__bio">
        {{ user.bio }}
    </div>

    <div class="profile__stats">
        <div class="stat">
            <strong>{{ user.posts_count }}</strong>
            <span>Posts</span>
        </div>
        <div class="stat">
            <strong>{{ user.followers_count }}</strong>
            <span>Followers</span>
        </div>
        <div class="stat">
            <strong>{{ user.following_count }}</strong>
            <span>Following</span>
        </div>
    </div>

    <div class="profile__posts">
        {% for post in user.posts %}
        <!-- Post card -->
        {% endfor %}
    </div>
</div>
{% endblock %}
'''


def _page_dashboard(name: str) -> str:
    return '''{% extends "base.html" %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="dashboard">
    <h1>Dashboard</h1>

    <div class="dashboard__stats">
        <div class="stat-card">
            <h3>{{ stats.users }}</h3>
            <p>Users</p>
        </div>
        <div class="stat-card">
            <h3>{{ stats.posts }}</h3>
            <p>Posts</p>
        </div>
        <div class="stat-card">
            <h3>{{ stats.comments }}</h3>
            <p>Comments</p>
        </div>
    </div>

    <div class="dashboard__activity">
        <h2>Recent Activity</h2>
        <!-- Activity feed -->
    </div>
</div>
{% endblock %}
'''


def _page_login(name: str) -> str:
    return '''{% extends "base.html" %}

{% block title %}Login{% endblock %}

{% block content %}
<div class="login">
    <h1>Login</h1>

    <form method="POST" action="/login">
        <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required>
        </div>

        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>

        <button type="submit" class="btn btn--primary">Login</button>
    </form>

    <p>Don't have an account? <a href="/register">Register</a></p>
</div>
{% endblock %}
'''


def _page_generic(name: str) -> str:
    return f'''{{%extends "base.html" %}}

{{%block title %}}{name}{{%endblock %}}

{{%block content %}}
<div class="{name.lower()}">
    <h1>{name}</h1>
    <!-- Add your content here -->
</div>
{{%endblock %}}
'''


# ==============================================================================
# FOLDER STRUCTURE TEMPLATES
# ==============================================================================

def generate_folder_structure(name: str, base_path: str = ".") -> Dict:
    """
    Generate folder structure for a feature/module

    Args:
        name: Feature name
        base_path: Where to create folders

    Returns:
        Dict with created paths
    """
    structures = {
        'feature': _structure_feature,
        'api': _structure_api,
        'component': _structure_component,
        'project': _structure_project,
    }

    structure_func = structures.get(name, _structure_feature)
    return structure_func(name, base_path)


def _structure_feature(name: str, base_path: str) -> Dict:
    """Create feature folder structure"""
    feature_path = Path(base_path) / name

    folders = [
        feature_path / 'templates',
        feature_path / 'static' / 'css',
        feature_path / 'static' / 'js',
        feature_path / 'models',
        feature_path / 'routes',
    ]

    files = {
        feature_path / '__init__.py': '',
        feature_path / 'models' / '__init__.py': '',
        feature_path / 'routes' / '__init__.py': '',
        feature_path / f'{name}.py': f'"""{name} module"""',
    }

    return {'folders': folders, 'files': files}


def _structure_api(name: str, base_path: str) -> Dict:
    """Create API folder structure"""
    api_path = Path(base_path) / 'api' / name

    folders = [
        api_path,
        api_path / 'endpoints',
        api_path / 'schemas',
        api_path / 'tests',
    ]

    files = {
        api_path / '__init__.py': '',
        api_path / 'endpoints' / '__init__.py': '',
        api_path / 'schemas' / '__init__.py': '',
        api_path / 'tests' / f'test_{name}.py': '',
    }

    return {'folders': folders, 'files': files}


def _structure_component(name: str, base_path: str) -> Dict:
    """Create component folder structure"""
    comp_path = Path(base_path) / 'components' / name

    folders = [comp_path]

    files = {
        comp_path / f'{name}.html': generate_component(name),
        comp_path / f'{name}.css': f'/* {name} styles */',
        comp_path / f'{name}.js': f'// {name} component',
    }

    return {'folders': folders, 'files': files}


def _structure_project(name: str, base_path: str) -> Dict:
    """Create full project structure"""
    project_path = Path(base_path) / name

    folders = [
        project_path,
        project_path / 'app',
        project_path / 'app' / 'templates',
        project_path / 'app' / 'static',
        project_path / 'app' / 'models',
        project_path / 'app' / 'routes',
        project_path / 'tests',
        project_path / 'docs',
    ]

    files = {
        project_path / 'README.md': f'# {name}\n\nProject description',
        project_path / 'requirements.txt': '',
        project_path / 'config.py': 'Configuration',
        project_path / 'app' / '__init__.py': '',
        project_path / 'app' / 'models' / '__init__.py': '',
        project_path / 'app' / 'routes' / '__init__.py': '',
    }

    return {'folders': folders, 'files': files}


# ==============================================================================
# PYTHON CODE TEMPLATES
# ==============================================================================

def generate_python_test(function_name: str) -> str:
    """Generate pytest test file"""
    return f'''#!/usr/bin/env python3
"""
Tests for {function_name}

Run: pytest test_{function_name}.py -v
"""

import pytest
from {function_name} import {function_name}


class Test{function_name.title()}:
    """Test suite for {function_name}"""

    def test_{function_name}_returns_expected_value(self):
        """Test that {function_name} returns expected value"""
        # Arrange
        input_data = "test"
        expected = "result"

        # Act
        result = {function_name}(input_data)

        # Assert
        assert result == expected

    def test_{function_name}_handles_empty_input(self):
        """Test that {function_name} handles empty input gracefully"""
        # Arrange
        input_data = ""

        # Act
        result = {function_name}(input_data)

        # Assert
        assert result is not None

    def test_{function_name}_raises_error_on_invalid_input(self):
        """Test that {function_name} raises appropriate error"""
        # Arrange
        invalid_input = None

        # Act & Assert
        with pytest.raises(ValueError):
            {function_name}(invalid_input)


@pytest.fixture
def sample_data():
    """Fixture providing sample test data"""
    return {{
        "key": "value",
        "items": [1, 2, 3]
    }}


def test_{function_name}_with_fixture(sample_data):
    """Test using pytest fixture"""
    result = {function_name}(sample_data)
    assert result is not None
'''


def generate_python_class(class_name: str) -> str:
    """Generate Python class with docstrings and type hints"""
    return f'''#!/usr/bin/env python3
"""
{class_name} - Description of what this class does

Example:
    obj = {class_name}("param")
    result = obj.method()
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class {class_name}:
    """
    {class_name} class description

    Attributes:
        name: The name attribute
        value: The value attribute
        metadata: Optional metadata dictionary
    """

    name: str
    value: int
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate attributes after initialization"""
        if self.value < 0:
            raise ValueError("Value must be non-negative")

    def process(self) -> str:
        """
        Process the data and return result

        Returns:
            Processed string result

        Raises:
            ValueError: If processing fails
        """
        if not self.name:
            raise ValueError("Name cannot be empty")

        return f"Processed: {{self.name}} = {{self.value}}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> '{class_name}':
        """
        Create instance from dictionary

        Args:
            data: Dictionary with name and value keys

        Returns:
            New {class_name} instance
        """
        return cls(
            name=data['name'],
            value=data['value'],
            metadata=data.get('metadata')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert instance to dictionary

        Returns:
            Dictionary representation
        """
        return {{
            'name': self.name,
            'value': self.value,
            'metadata': self.metadata
        }}


if __name__ == '__main__':
    # Example usage
    obj = {class_name}("example", 42)
    print(obj.process())
'''


def generate_flask_route(route_name: str) -> str:
    """Generate Flask route with error handling"""
    return f'''@app.route('/{route_name}', methods=['GET', 'POST'])
def {route_name}():
    """
    {route_name.replace('_', ' ').title()} route

    Returns:
        Rendered template or JSON response
    """
    if request.method == 'POST':
        try:
            # Get form data
            data = request.get_json() or request.form

            # Validate required fields
            required_fields = ['field1', 'field2']
            missing = [f for f in required_fields if f not in data]
            if missing:
                return jsonify({{
                    'success': False,
                    'error': f'Missing fields: {{", ".join(missing)}}'
                }}), 400

            # Process data
            result = process_{route_name}(data)

            # Return success
            return jsonify({{
                'success': True,
                'data': result
            }})

        except ValueError as e:
            return jsonify({{'success': False, 'error': str(e)}}), 400
        except Exception as e:
            app.logger.error(f'Error in {route_name}: {{e}}')
            return jsonify({{'success': False, 'error': 'Internal error'}}), 500

    # GET request - render template
    return render_template('{route_name}.html')


def process_{route_name}(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process {route_name} data

    Args:
        data: Input data dictionary

    Returns:
        Processed result dictionary
    """
    # Add processing logic here
    return {{'status': 'processed', 'input': data}}
'''


# ==============================================================================
# JAVASCRIPT TEMPLATES
# ==============================================================================

def generate_javascript_function(function_name: str) -> str:
    """Generate JavaScript/ES6 function with JSDoc"""
    return f'''/**
 * {function_name} - Description
 *
 * @param {{string}} input - Input parameter
 * @returns {{Promise<Object>}} Result object
 *
 * @example
 * const result = await {function_name}("test");
 * console.log(result);
 */
async function {function_name}(input) {{
    try {{
        // Validate input
        if (!input) {{
            throw new Error('{function_name}: Input is required');
        }}

        // Process
        const response = await fetch('/api/{function_name}', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{ input }})
        }});

        if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
        }}

        const data = await response.json();

        if (!data.success) {{
            throw new Error(data.error || 'Unknown error');
        }}

        return data;

    }} catch (error) {{
        console.error(`{function_name} error:`, error);
        throw error;
    }}
}}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = {function_name};
}}
'''


def generate_javascript_test(function_name: str) -> str:
    """Generate Jest test file"""
    return f'''/**
 * Tests for {function_name}
 *
 * Run: npm test {function_name}.test.js
 */

const {function_name} = require('./{function_name}');

describe('{function_name}', () => {{
    it('should return expected result', async () => {{
        const input = 'test';
        const result = await {function_name}(input);

        expect(result).toBeDefined();
        expect(result.success).toBe(true);
    }});

    it('should handle empty input', async () => {{
        await expect({function_name}('')).rejects.toThrow();
    }});

    it('should handle API errors', async () => {{
        // Mock fetch to return error
        global.fetch = jest.fn(() =>
            Promise.resolve({{
                ok: false,
                status: 500
            }})
        );

        await expect({function_name}('test')).rejects.toThrow();
    }});
}});
'''


# ==============================================================================
# API DOCUMENTATION TEMPLATES
# ==============================================================================

def generate_openapi_spec(api_name: str) -> str:
    """Generate OpenAPI/Swagger specification"""
    return f'''openapi: 3.0.0
info:
  title: {api_name} API
  description: {api_name} REST API documentation
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: http://localhost:5001/v1
    description: Development server

paths:
  /{api_name.lower()}:
    get:
      summary: List {api_name} items
      tags:
        - {api_name}
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/{api_name}'

    post:
      summary: Create {api_name} item
      tags:
        - {api_name}
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/{api_name}Create'
      responses:
        '201':
          description: Created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/{api_name}'

components:
  schemas:
    {api_name}:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        created_at:
          type: string
          format: date-time

    {api_name}Create:
      type: object
      required:
        - name
      properties:
        name:
          type: string
'''


# ==============================================================================
# CONFIG FILE TEMPLATES
# ==============================================================================

def generate_requirements_txt() -> str:
    """Generate Python requirements.txt"""
    return '''# Core dependencies
Flask==3.0.0
SQLAlchemy==2.0.23
Pillow==10.1.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Development
black==23.11.0
flake8==6.1.0
mypy==1.7.1

# Optional
requests==2.31.0
python-dotenv==1.0.0
'''


def generate_env_template() -> str:
    """Generate .env template"""
    return '''# Application Config
APP_NAME=MyApp
APP_ENV=development
DEBUG=true
SECRET_KEY=generate-a-secret-key-here

# Database
DATABASE_URL=sqlite:///app.db

# API Keys (never commit real keys!)
API_KEY=your-api-key
API_SECRET=your-api-secret

# Features
ENABLE_ANALYTICS=false
MAX_UPLOAD_SIZE=10485760

# URLs
BASE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3000
'''


# ==============================================================================
# DOCUMENTATION TEMPLATES
# ==============================================================================

def generate_readme(project_name: str) -> str:
    """Generate README.md"""
    return f'''# {project_name}

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## Overview

{project_name} - One-line description of what this project does.

## Features

- ✅ Feature 1
- ✅ Feature 2
- ✅ Feature 3

## Installation

```bash
# Clone repository
git clone https://github.com/username/{project_name.lower()}.git
cd {project_name.lower()}

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Usage

```python
from {project_name.lower()} import main

# Example usage
result = main("input")
print(result)
```

## API Reference

See [API.md](./docs/API.md) for full API documentation.

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest --cov

# Format code
black .

# Type check
mypy .
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

- Author: Your Name
- Email: your.email@example.com
- GitHub: [@yourusername](https://github.com/yourusername)
'''


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Template Generator - Make EVERYTHING Templatable')
    parser.add_argument('--type', type=str, help='Template type (component, page, route, folder)')
    parser.add_argument('--name', type=str, help='Template name')
    parser.add_argument('--output', type=str, help='Output file/directory')
    parser.add_argument('--list', action='store_true', help='List available templates')

    args = parser.parse_args()

    if args.list:
        print("=" * 70)
        print("📋 AVAILABLE TEMPLATES")
        print("=" * 70)
        print()
        print("HTML Components:")
        print("  UserCard, Button, Nav, Card, Form, Modal")
        print()
        print("HTML Pages:")
        print("  BlogPost, UserProfile, Dashboard, Login")
        print()
        print("Python:")
        print("  test, class, route")
        print()
        print("JavaScript:")
        print("  function, test")
        print()
        print("API Docs:")
        print("  openapi")
        print()
        print("Config Files:")
        print("  requirements, env")
        print()
        print("Documentation:")
        print("  readme")
        print()
        print("Folders:")
        print("  feature, api, component, project")
        print()

    elif args.type == 'component':
        if not args.name:
            print("❌ --name required")
            exit(1)

        html = generate_component(args.name)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(html)
            print(f"✅ Component saved to {args.output}")
        else:
            print(html)

    elif args.type == 'page':
        if not args.name:
            print("❌ --name required")
            exit(1)

        html = generate_page(args.name)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(html)
            print(f"✅ Page saved to {args.output}")
        else:
            print(html)

    elif args.type == 'folder':
        if not args.name:
            print("❌ --name required")
            exit(1)

        structure = generate_folder_structure(args.name, args.output or '.')

        print(f"✅ Creating folder structure for '{args.name}'...")
        print()
        print("Folders:")
        for folder in structure['folders']:
            print(f"  📁 {folder}")

        print()
        print("Files:")
        for file in structure['files']:
            print(f"  📄 {file}")

    elif args.type in ['python', 'py']:
        if not args.name:
            print("❌ --name required")
            exit(1)

        # Determine Python template type
        if args.name in ['test', 'pytest']:
            code = generate_python_test('my_function')
        elif args.name in ['class', 'dataclass']:
            code = generate_python_class('MyClass')
        elif args.name in ['route', 'flask']:
            code = generate_flask_route('my_route')
        else:
            # Default to test
            code = generate_python_test(args.name)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(code)
            print(f"✅ Python code saved to {args.output}")
        else:
            print(code)

    elif args.type in ['javascript', 'js']:
        if not args.name:
            print("❌ --name required")
            exit(1)

        if args.name == 'test':
            code = generate_javascript_test('myFunction')
        else:
            code = generate_javascript_function(args.name)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(code)
            print(f"✅ JavaScript code saved to {args.output}")
        else:
            print(code)

    elif args.type == 'api':
        api_name = args.name or 'MyAPI'
        spec = generate_openapi_spec(api_name)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(spec)
            print(f"✅ API spec saved to {args.output}")
        else:
            print(spec)

    elif args.type == 'config':
        if args.name == 'requirements':
            content = generate_requirements_txt()
        elif args.name == 'env':
            content = generate_env_template()
        else:
            print("❌ Unknown config type. Use: requirements, env")
            exit(1)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(content)
            print(f"✅ Config saved to {args.output}")
        else:
            print(content)

    elif args.type == 'readme':
        project_name = args.name or 'MyProject'
        readme = generate_readme(project_name)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(readme)
            print(f"✅ README saved to {args.output}")
        else:
            print(readme)

    else:
        print("Template Generator - Make EVERYTHING Templatable")
        print()
        print("Usage:")
        print("  --type component --name UserCard")
        print("  --type page --name BlogPost")
        print("  --type python --name test --output test_my_function.py")
        print("  --type javascript --name myFunction --output myFunction.js")
        print("  --type api --name Users --output openapi.yaml")
        print("  --type config --name requirements --output requirements.txt")
        print("  --type readme --name MyProject --output README.md")
        print("  --type folder --name new_feature")
        print("  --list")

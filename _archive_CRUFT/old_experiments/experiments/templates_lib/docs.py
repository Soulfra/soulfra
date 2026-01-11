#!/usr/bin/env python3
"""
Documentation Templates

Code generators for creating professional documentation including:
- README.md with badges and examples
- API documentation
- Architecture diagrams (markdown)
- Quick start guides
- Contributing guides
"""

CATEGORY = 'docs'

# =============================================================================
# TEMPLATE GENERATORS
# =============================================================================

def generate_readme(
    project_name='My Project',
    description='A cool project',
    features=None,
    installation_steps=None,
    usage_example='python app.py',
    author='Developer',
    license='MIT',
    **kwargs
):
    """Generate comprehensive README.md"""

    if features is None:
        features = ['Feature 1', 'Feature 2', 'Feature 3']

    if installation_steps is None:
        installation_steps = [
            'Clone the repository',
            'Install dependencies: `pip install -r requirements.txt`',
            'Run the application'
        ]

    features_md = '\n'.join(f'- {feature}' for feature in features)
    install_md = '\n'.join(f'{i+1}. {step}' for i, step in enumerate(installation_steps))

    return f'''# {project_name}

{description}

## ✨ Features

{features_md}

## 🚀 Quick Start

### Installation

{install_md}

### Usage

```bash
{usage_example}
```

## 📖 Documentation

For full documentation, see [docs/](./docs/).

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

## 📝 License

{license} © {author}

## 🙏 Acknowledgments

Built with ❤️ by {author}
'''


def generate_api_docs(
    api_name='API',
    endpoints=None,
    base_url='http://localhost:5000',
    authentication='Bearer token',
    **kwargs
):
    """Generate API documentation in markdown"""

    if endpoints is None:
        endpoints = [
            {
                'method': 'GET',
                'path': '/api/users',
                'description': 'Get all users',
                'response': '{"users": [...]}'
            },
            {
                'method': 'POST',
                'path': '/api/users',
                'description': 'Create new user',
                'body': '{"name": "John", "email": "john@example.com"}',
                'response': '{"id": 1, "name": "John"}'
            }
        ]

    endpoints_md = ''
    for endpoint in endpoints:
        method = endpoint['method']
        path = endpoint['path']
        desc = endpoint['description']
        body = endpoint.get('body', '')
        response = endpoint['response']

        body_section = f'''
**Request Body:**
```json
{body}
```
''' if body else ''

        endpoints_md += f'''
### `{method} {path}`

{desc}

{body_section}
**Response:**
```json
{response}
```

**Example:**
```bash
curl -X {method} {base_url}{path} \\
  -H "Authorization: {authentication}" \\
  -H "Content-Type: application/json"
```

---

'''

    return f'''# {api_name} Documentation

Base URL: `{base_url}`

## Authentication

All requests require authentication via {authentication}.

Example:
```bash
curl -H "Authorization: {authentication}" {base_url}/api/endpoint
```

## Endpoints

{endpoints_md}

## Error Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 400  | Bad Request |
| 401  | Unauthorized |
| 404  | Not Found |
| 500  | Internal Server Error |
'''


def generate_quickstart(
    project_name='Project',
    prerequisites=None,
    steps=None,
    **kwargs
):
    """Generate QUICK_START.md guide"""

    if prerequisites is None:
        prerequisites = ['Python 3.8+', 'pip', 'Git']

    if steps is None:
        steps = [
            ('Clone Repository', 'git clone https://github.com/user/repo.git'),
            ('Install Dependencies', 'pip install -r requirements.txt'),
            ('Run Application', 'python app.py')
        ]

    prereq_md = '\n'.join(f'- {item}' for item in prerequisites)

    steps_md = ''
    for i, (title, command) in enumerate(steps, 1):
        steps_md += f'''
## Step {i}: {title}

```bash
{command}
```

'''

    return f'''# Quick Start Guide - {project_name}

Get {project_name} running in 5 minutes!

## Prerequisites

{prereq_md}

{steps_md}
## ✅ You're Ready!

Your {project_name} instance should now be running.

## Next Steps

- Read the [full documentation](./README.md)
- Check out the [API docs](./API.md)
- Join our community
'''


def generate_architecture(
    project_name='Project',
    components=None,
    data_flow=None,
    **kwargs
):
    """Generate ARCHITECTURE.md with markdown diagrams"""

    if components is None:
        components = [
            ('Frontend', 'User interface layer'),
            ('Backend', 'API and business logic'),
            ('Database', 'Data persistence layer')
        ]

    if data_flow is None:
        data_flow = [
            'User → Frontend',
            'Frontend → Backend API',
            'Backend → Database',
            'Database → Backend',
            'Backend → Frontend',
            'Frontend → User'
        ]

    components_md = ''
    for name, desc in components:
        components_md += f'''### {name}

{desc}

'''

    data_flow_md = '\n'.join(f'{i+1}. {step}' for i, step in enumerate(data_flow))

    return f'''# Architecture - {project_name}

## System Overview

```
┌──────────┐
│  User    │
└────┬─────┘
     │
┌────▼─────────┐
│   Frontend   │
└────┬─────────┘
     │
┌────▼─────────┐
│   Backend    │
└────┬─────────┘
     │
┌────▼─────────┐
│   Database   │
└──────────────┘
```

## Components

{components_md}

## Data Flow

{data_flow_md}

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | SQLite |

## Design Principles

1. **Simplicity** - Keep it simple and maintainable
2. **Modularity** - Each component has a single responsibility
3. **Testability** - All components are unit tested
4. **Documentation** - Code is self-documenting with clear comments
'''


def generate_contributing(
    project_name='Project',
    code_style='PEP 8',
    test_command='pytest',
    **kwargs
):
    """Generate CONTRIBUTING.md guide"""

    return f'''# Contributing to {project_name}

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `{test_command}`
5. Commit your changes: `git commit -m "Add my feature"`
6. Push to your fork: `git push origin feature/my-feature`
7. Open a Pull Request

## Code Style

We follow **{code_style}** for Python code.

Run linter before committing:
```bash
pylint *.py
```

## Testing

All new features must include tests.

Run tests:
```bash
{test_command}
```

## Pull Request Process

1. Update README.md with details of changes if needed
2. Update documentation
3. Ensure all tests pass
4. Get approval from at least one maintainer

## Code of Conduct

Be respectful, collaborative, and constructive. We're all here to build something great together!

## Questions?

Open an issue or reach out to the maintainers.
'''


def generate_changelog(
    project_name='Project',
    versions=None,
    **kwargs
):
    """Generate CHANGELOG.md"""

    if versions is None:
        versions = [
            {
                'version': '1.0.0',
                'date': '2025-01-15',
                'changes': [
                    ('Added', 'Initial release'),
                    ('Added', 'Core features')
                ]
            }
        ]

    changelog_md = ''
    for v in versions:
        version = v['version']
        date = v['date']
        changes = v['changes']

        changelog_md += f'''## [{version}] - {date}

'''

        # Group by type
        types = {}
        for change_type, description in changes:
            if change_type not in types:
                types[change_type] = []
            types[change_type].append(description)

        for change_type, descriptions in types.items():
            changelog_md += f'''### {change_type}

'''
            for desc in descriptions:
                changelog_md += f'- {desc}\n'
            changelog_md += '\n'

    return f'''# Changelog - {project_name}

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{changelog_md}
'''


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

TEMPLATES = {
    'readme': {
        'description': 'Comprehensive README.md with features, installation, usage',
        'generator': generate_readme,
        'parameters': ['project_name', 'description', 'features', 'installation_steps', 'usage_example', 'author', 'license'],
        'examples': [
            "generate_readme(project_name='My App', description='Cool app')",
            "generate_readme(features=['AI', 'Fast', 'Secure'])"
        ],
        'tags': ['readme', 'documentation', 'markdown']
    },

    'api-docs': {
        'description': 'API documentation with endpoints, authentication, examples',
        'generator': generate_api_docs,
        'parameters': ['api_name', 'endpoints', 'base_url', 'authentication'],
        'examples': [
            "generate_api_docs(api_name='User API')",
            "generate_api_docs(base_url='https://api.example.com')"
        ],
        'tags': ['api', 'documentation', 'rest']
    },

    'quickstart': {
        'description': 'Quick start guide with step-by-step instructions',
        'generator': generate_quickstart,
        'parameters': ['project_name', 'prerequisites', 'steps'],
        'examples': [
            "generate_quickstart(project_name='Web App')",
            "generate_quickstart(prerequisites=['Node.js', 'npm'])"
        ],
        'tags': ['guide', 'tutorial', 'getting-started']
    },

    'architecture': {
        'description': 'Architecture documentation with diagrams and data flow',
        'generator': generate_architecture,
        'parameters': ['project_name', 'components', 'data_flow'],
        'examples': [
            "generate_architecture(project_name='System')",
            "generate_architecture(components=[('API', 'Backend'), ('DB', 'Storage')])"
        ],
        'tags': ['architecture', 'design', 'diagram']
    },

    'contributing': {
        'description': 'Contributing guide with code style and PR process',
        'generator': generate_contributing,
        'parameters': ['project_name', 'code_style', 'test_command'],
        'examples': [
            "generate_contributing(project_name='App')",
            "generate_contributing(code_style='Black', test_command='npm test')"
        ],
        'tags': ['contributing', 'guide', 'community']
    },

    'changelog': {
        'description': 'Changelog following Keep a Changelog format',
        'generator': generate_changelog,
        'parameters': ['project_name', 'versions'],
        'examples': [
            "generate_changelog(project_name='App')",
            "generate_changelog(versions=[{'version': '2.0.0', 'date': '2025-01-20', 'changes': [('Added', 'New feature')]}])"
        ],
        'tags': ['changelog', 'history', 'versions']
    }
}


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    print("📚 Documentation Template Generator\n")

    print("=" * 70)
    print("1. README")
    print("=" * 70)
    print(generate_readme(
        project_name='Soulfra Simple',
        description='A simple, powerful newsletter platform',
        features=['AI-powered', 'Zero dependencies', 'Easy deployment']
    ))

    print("\n" + "=" * 70)
    print("2. API DOCS")
    print("=" * 70)
    print(generate_api_docs(api_name='Soulfra API'))

    print("\n" + "=" * 70)
    print("3. QUICK START")
    print("=" * 70)
    print(generate_quickstart(project_name='Soulfra'))

    print("\n✅ Documentation template generators working!")

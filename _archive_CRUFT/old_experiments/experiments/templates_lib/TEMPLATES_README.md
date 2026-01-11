# Templates Library - Developer Guide

Complete guide to creating template modules in the `templates_lib/` modular template system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Module Structure](#module-structure)
3. [Creating a Template Module](#creating-a-template-module)
4. [Testing Your Module](#testing-your-module)
5. [Best Practices](#best-practices)
6. [Examples](#examples)

---

## Quick Start

To create a new template module:

1. Create `templates_lib/your_module.py`
2. Define `CATEGORY` constant
3. Define generator functions
4. Export `TEMPLATES` dict
5. Add module name to `__init__.py` import list
6. Test your module

---

## Module Structure

Every template module follows this pattern:

```python
#!/usr/bin/env python3
"""
Your Module Name - Brief Description

Longer description of what templates this module provides.
"""

from typing import Optional


# ==============================================================================
# CATEGORY CONSTANT
# ==============================================================================

CATEGORY = 'your_category'  # e.g., 'database', 'python', 'docker'


# ==============================================================================
# GENERATOR FUNCTIONS
# ==============================================================================

def generate_template_name(param1: str, param2: Optional[str] = None) -> str:
    """
    Brief description of what this generates

    Args:
        param1: Description of param1
        param2: Optional description

    Returns:
        Generated code as string
    """
    # Your generation logic here
    return f"""
    Generated code here
    """


# ==============================================================================
# TEMPLATE DEFINITIONS
# ==============================================================================

TEMPLATES = {
    'template_name': {
        'description': 'Brief description of template',
        'generator': generate_template_name,
        'parameters': ['param1', 'param2?'],  # '?' means optional
        'examples': [
            "generate_template('category', 'template_name', param1='value')",
        ],
        'tags': ['tag1', 'tag2', 'tag3']
    },
}


# ==============================================================================
# TEST CODE (optional but recommended)
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Your Templates\n")
    print(generate_template_name(param1='test'))
```

---

## Creating a Template Module

### Step 1: Create the File

Create `templates_lib/python_advanced.py` (for example):

```bash
touch templates_lib/python_advanced.py
```

### Step 2: Set the Category

```python
CATEGORY = 'python'
```

This groups all templates in this module under the `python` category.

### Step 3: Create Generator Functions

**IMPORTANT**: Avoid parameter names that conflict with the API:
- ❌ DON'T use `name` as a parameter (conflicts with template name)
- ✅ DO use specific names like `function_name`, `class_name`, `tool_name`

```python
def generate_cli_tool(tool_name: str, description: Optional[str] = None) -> str:
    """Generate a Python CLI tool with argparse"""

    if description is None:
        description = f"{tool_name} - CLI Tool"

    return f'''#!/usr/bin/env python3
"""
{description}

Usage:
    python3 {tool_name}.py [options]
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('--version', action='store_true', help='Show version')

    args = parser.parse_args()

    if args.version:
        print("{tool_name} v1.0.0")
        return

    print("Hello from {tool_name}!")


if __name__ == '__main__':
    main()
'''
```

### Step 4: Export Templates Dict

```python
TEMPLATES = {
    'cli-tool': {
        'description': 'Python CLI tool with argparse',
        'generator': generate_cli_tool,
        'parameters': ['tool_name', 'description?'],
        'examples': [
            "generate_template('python', 'cli-tool', tool_name='mytool')",
            "generate_template('python', 'cli-tool', tool_name='converter', description='File converter tool')"
        ],
        'tags': ['python', 'cli', 'argparse', 'tool']
    },
}
```

### Step 5: Register in __init__.py

Add your module name to the `module_files` list in `templates_lib/__init__.py`:

```python
module_files = [
    'database',
    'python_advanced',  # Add your module here
    'languages',
    # ... etc
]
```

### Step 6: Test Your Module

Run the module standalone:

```bash
python3 templates_lib/python_advanced.py
```

Run the template tests:

```bash
python3 test_templates_lib.py
```

Run the pre-commit tests:

```bash
python3 test_before_commit.py --templates
```

---

## Testing Your Module

### Unit Testing Pattern

Create tests in `test_templates_lib.py`:

```python
def test_generate_cli_tool():
    """Test generating a CLI tool"""
    test_print("Testing CLI tool generation...", 'info')

    try:
        from templates_lib import generate_template

        # Generate CLI tool
        cli = generate_template('python', 'cli-tool', tool_name='mytool')

        assert cli is not None, "Should generate CLI tool"
        assert '#!/usr/bin/env python3' in cli, "Should be executable"
        assert 'argparse' in cli, "Should use argparse"
        assert 'mytool' in cli, "Should include tool name"

        test_print("CLI tool generated successfully", 'pass')
        return True
    except Exception as e:
        test_print(f"CLI tool generation failed: {e}", 'fail')
        return False
```

### Syntax Validation

Test that generated code is syntactically valid:

```python
def test_python_syntax():
    """Test that generated Python has valid syntax"""
    from templates_lib import generate_template

    cli = generate_template('python', 'cli-tool', tool_name='test')

    # Try to compile the generated Python
    try:
        compile(cli, 'test.py', 'exec')
        assert True, "Generated Python is valid"
    except SyntaxError as e:
        assert False, f"Generated Python has syntax error: {e}"
```

---

## Best Practices

### 1. Parameter Naming

✅ **Good:**
```python
def generate_migration(migration_name: str, number: int):
def generate_schema(table_name: str, columns: str):
def generate_query(query_name: str, description: str):
```

❌ **Bad:**
```python
def generate_migration(name: str):  # Conflicts with template name!
def generate_schema(name: str):     # Conflicts with template name!
```

### 2. Optional Parameters

Use `Optional[type]` and provide defaults:

```python
def generate_template(
    required_param: str,
    optional_param: Optional[str] = None,
    optional_number: Optional[int] = None
) -> str:
    if optional_param is None:
        optional_param = f"Default value for {required_param}"

    if optional_number is None:
        optional_number = 1
```

### 3. Documentation

Always include:
- Docstring for the generator function
- Description in TEMPLATES dict
- At least 2 examples showing usage
- Relevant tags for searchability

### 4. Idempotency

For database/infrastructure templates, make them idempotent:

```sql
-- Good: Can run multiple times
CREATE TABLE IF NOT EXISTS users (...);
INSERT OR IGNORE INTO users VALUES (...);

-- Bad: Fails on second run
CREATE TABLE users (...);
INSERT INTO users VALUES (...);
```

### 5. Comments and TODOs

Include helpful comments and TODOs in generated code:

```python
return f'''
# TODO: Update this with your specific logic
def {function_name}():
    # Your implementation here
    pass
'''
```

---

## Examples

### Example 1: Database Module

See `templates_lib/database.py` for a complete example with 6 templates:
- Migration
- Schema
- Seed
- Query
- Trigger
- View

### Example 2: Multi-Language Template

```python
CATEGORY = 'languages'

def generate_go_http_server(service_name: str, port: int = 8080) -> str:
    """Generate a Go HTTP server"""
    return f'''package main

import (
    "fmt"
    "log"
    "net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {{
    fmt.Fprintf(w, "Hello from {service_name}!")
}}

func main() {{
    http.HandleFunc("/", handler)
    log.Printf("Starting {service_name} on :{port}")
    log.Fatal(http.ListenAndServe(":{port}", nil))
}}
'''

TEMPLATES = {{
    'go-http-server': {{
        'description': 'Go HTTP server with basic handler',
        'generator': generate_go_http_server,
        'parameters': ['service_name', 'port?'],
        'examples': [
            "generate_template('languages', 'go-http-server', service_name='api')",
            "generate_template('languages', 'go-http-server', service_name='backend', port=3000)"
        ],
        'tags': ['go', 'http', 'server', 'api']
    }}
}}
```

### Example 3: Config Template with Nested Objects

```python
import json
from typing import Dict, Any

def generate_tsconfig(
    target: str = 'ES2020',
    module: str = 'commonjs',
    strict: bool = True,
    **options: Any
) -> str:
    """Generate tsconfig.json"""

    config = {
        "compilerOptions": {
            "target": target,
            "module": module,
            "strict": strict,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            **options  # Allow additional options
        }
    }

    return json.dumps(config, indent=2)
```

---

## API Usage

Once your module is created, users can use it like this:

### Via Python API

```python
from templates_lib import generate_template, get_template, search_templates

# Direct generation
code = generate_template('python', 'cli-tool', tool_name='mytool')

# Get template first, then generate
template = get_template('python', 'cli-tool')
code = template.generate(tool_name='mytool', description='My awesome tool')

# Search for templates
results = search_templates('cli')
for template in results:
    print(f"{template.category}/{template.name}: {template.description}")
```

### Via CLI (future enhancement)

```bash
# Generate template
python3 template_generator.py --category python --name cli-tool --params tool_name=mytool

# List templates in category
python3 template_generator.py --list --category python

# Search templates
python3 template_generator.py --search cli
```

---

## Template Module Checklist

Before submitting a new template module:

- [ ] Module file created in `templates_lib/`
- [ ] `CATEGORY` constant defined
- [ ] Generator functions use clear, non-conflicting parameter names
- [ ] All generator functions have docstrings
- [ ] `TEMPLATES` dict exported with all metadata
- [ ] Examples provided for each template
- [ ] Tags added for searchability
- [ ] Module added to `__init__.py` import list
- [ ] Standalone test works (`python3 templates_lib/your_module.py`)
- [ ] Tests added to `test_templates_lib.py`
- [ ] Pre-commit tests pass (`python3 test_before_commit.py --templates`)
- [ ] Generated code is syntactically valid
- [ ] README examples updated (if needed)

---

## Getting Help

- See `templates_lib/database.py` for a complete working example
- Run `python3 -c "from templates_lib import list_templates; print(list_templates())"` to see all available templates
- Run `python3 test_templates_lib.py` to validate the system
- Check `output/generated_templates/README.md` for usage examples

---

## Contributing

When adding new template modules:

1. Follow the structure outlined in this guide
2. Include comprehensive tests
3. Document all parameters clearly
4. Provide multiple examples
5. Tag templates appropriately
6. Test generated code validity
7. Update this README if needed

The goal is to make EVERYTHING templatable - from simple functions to entire project scaffolds!

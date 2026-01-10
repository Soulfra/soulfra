#!/usr/bin/env python3
"""
Universal Formula Engine

A generalized template/formula system inspired by the theme compiler.
Works like a spreadsheet: define variables, write formulas, generate outputs.

This extends the pattern from theme_compiler.py to work with:
- ANY input format (JSON, YAML, Python dicts)
- ANY template (HTML, CSS, Markdown, etc.)
- ANY formulas (math, colors, strings, custom functions)

Usage:
    python formula_engine.py --config vars.json --template page.html.tmpl

    # Or in code:
    from formula_engine import FormulaEngine
    engine = FormulaEngine()
    output = engine.render_template('page.html.tmpl', config_file='vars.json')

Example config.json:
    {
        "primaryColor": "#4ecca3",
        "fontSize": 16,
        "brandName": "Soulfra"
    }

Example template.html.tmpl:
    <style>
        :root {
            --color: {{primaryColor}};
            --color-dark: {{darken(primaryColor, 0.3)}};
            --size: {{fontSize}}px;
            --header-size: {{fontSize * 1.5}}px;
        }
    </style>
    <h1>Welcome to {{brandName}}</h1>
"""

import json
import re
import ast
import operator
from pathlib import Path
from typing import Dict, Any, Union, Callable, List
import colorsys


class FormulaEngine:
    """Universal template engine with formula evaluation"""

    def __init__(self, default_values: Dict[str, Any] = None):
        # Built-in functions available in templates
        self.functions = {
            # Color functions (from theme compiler)
            'darken': self._darken,
            'lighten': self._lighten,
            'hex_to_rgb': self._hex_to_rgb,
            'rgba': self._rgba,

            # Math functions
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'floor': lambda x: int(x),
            'ceil': lambda x: int(x + 0.999),

            # String functions
            'upper': str.upper,
            'lower': str.lower,
            'title': str.title,
            'capitalize': str.capitalize,
            'replace': str.replace,

            # List functions
            'join': lambda items, sep='': sep.join(str(i) for i in items),
            'len': len,
        }

        # Safe operators for expression evaluation
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        # Default values for common variables (prevents template errors)
        self.default_values = {
            'generated_content': '<p><em>Content will appear here after generation with Ollama.</em></p>',
            'author': 'Soulfra Team',
            'date': 'Today',
            'year': '2025',
            'description': 'Generated with Formula Engine',
            'keywords': 'soulfra, formula engine, templates',
        }

        # Allow custom defaults
        if default_values:
            self.default_values.update(default_values)

    # ==================================================================
    # COLOR FUNCTIONS (from theme_compiler.py)
    # ==================================================================

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgba(self, r: int, g: int, b: int, a: float = 1.0) -> str:
        """Create RGBA color string"""
        return f"rgba({r}, {g}, {b}, {a})"

    def _darken(self, hex_color: str, factor: float = 0.3) -> str:
        """Darken a hex color by factor (0-1)"""
        rgb = self._hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        v = max(0, v * (1 - factor))
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def _lighten(self, hex_color: str, factor: float = 0.3) -> str:
        """Lighten a hex color by factor (0-1)"""
        rgb = self._hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        v = min(1, v + (1 - v) * factor)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    # ==================================================================
    # VARIABLE LOADING
    # ==================================================================

    def load_config(self, config_source: Union[str, Path, Dict]) -> Dict[str, Any]:
        """
        Load configuration variables from multiple sources

        Args:
            config_source: Path to JSON/YAML file, or Python dict

        Returns:
            Dictionary of variables
        """
        if isinstance(config_source, dict):
            return config_source

        path = Path(config_source)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        # Read file
        content = path.read_text()

        # Parse based on extension
        if path.suffix == '.json':
            return json.loads(content)
        elif path.suffix in ['.yaml', '.yml']:
            try:
                import yaml
                return yaml.safe_load(content)
            except ImportError:
                raise ImportError("PyYAML required for YAML files: pip install pyyaml")
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

    # ==================================================================
    # EXPRESSION EVALUATION
    # ==================================================================

    def _eval_expr(self, node, variables: Dict[str, Any]) -> Any:
        """
        Safely evaluate Python expressions in templates

        Supports:
        - Variables: x, primaryColor
        - Math: 2 + 3, x * 2, x / 2
        - Function calls: darken(color, 0.3), upper(name)
        - Literals: numbers, strings
        """
        if isinstance(node, ast.Constant):
            # Python 3.8+: literals
            return node.value

        elif isinstance(node, ast.Num):
            # Python 3.7: numbers
            return node.n

        elif isinstance(node, ast.Str):
            # Python 3.7: strings
            return node.s

        elif isinstance(node, ast.Name):
            # Variable lookup
            if node.id in variables:
                return variables[node.id]
            elif node.id in self.functions:
                return self.functions[node.id]
            elif node.id in self.default_values:
                # Use default value instead of raising error
                return self.default_values[node.id]
            else:
                raise NameError(f"Variable not defined: {node.id}")

        elif isinstance(node, ast.BinOp):
            # Binary operations: +, -, *, /, etc.
            left = self._eval_expr(node.left, variables)
            right = self._eval_expr(node.right, variables)
            op = self.operators[type(node.op)]
            return op(left, right)

        elif isinstance(node, ast.UnaryOp):
            # Unary operations: -, +
            operand = self._eval_expr(node.operand, variables)
            op = self.operators[type(node.op)]
            return op(operand)

        elif isinstance(node, ast.Call):
            # Function calls: darken(color, 0.3)
            func = self._eval_expr(node.func, variables)
            args = [self._eval_expr(arg, variables) for arg in node.args]
            return func(*args)

        elif isinstance(node, ast.List):
            # List literals: [1, 2, 3]
            return [self._eval_expr(el, variables) for el in node.elts]

        else:
            raise SyntaxError(f"Unsupported expression type: {type(node).__name__}")

    def evaluate(self, expression: str, variables: Dict[str, Any]) -> Any:
        """
        Evaluate a formula expression

        Examples:
            evaluate("2 + 3", {}) → 5
            evaluate("x * 2", {"x": 5}) → 10
            evaluate("darken(color, 0.3)", {"color": "#4ecca3"}) → "#368e72"
        """
        try:
            tree = ast.parse(expression, mode='eval')
            return self._eval_expr(tree.body, variables)
        except Exception as e:
            raise ValueError(f"Error evaluating '{expression}': {e}")

    # ==================================================================
    # TEMPLATE PROCESSING
    # ==================================================================

    def render_template(
        self,
        template_source: Union[str, Path],
        variables: Dict[str, Any] = None,
        config_file: Union[str, Path] = None
    ) -> str:
        """
        Render a template with variables and formulas

        Template syntax:
            {{variable}}                    - Simple variable substitution
            {{expression}}                  - Evaluate expression
            {{function(arg1, arg2)}}        - Call function

        Args:
            template_source: Template string or path to template file
            variables: Dictionary of variables (optional)
            config_file: Path to config file (merged with variables)

        Returns:
            Rendered template as string
        """
        # Load variables
        all_variables = {}

        if config_file:
            all_variables.update(self.load_config(config_file))

        if variables:
            all_variables.update(variables)

        # Load template
        # Check for newlines to distinguish file paths from content strings
        if isinstance(template_source, (str, Path)) and '\n' not in str(template_source) and Path(template_source).exists():
            template = Path(template_source).read_text()
        else:
            template = str(template_source)

        # Find all {{...}} blocks
        pattern = r'\{\{([^}]+)\}\}'

        def replace_expression(match):
            expression = match.group(1).strip()
            try:
                result = self.evaluate(expression, all_variables)
                return str(result)
            except Exception as e:
                # Keep original if evaluation fails (helps debugging)
                return f"{{{{ERROR: {e}}}}}"

        # Replace all expressions
        rendered = re.sub(pattern, replace_expression, template)

        return rendered

    def compile_file(
        self,
        template_file: Union[str, Path],
        config_file: Union[str, Path],
        output_file: Union[str, Path] = None
    ) -> str:
        """
        Compile a template file with config and optionally save to output

        Args:
            template_file: Path to template file
            config_file: Path to config file (JSON/YAML)
            output_file: Path to save output (optional)

        Returns:
            Rendered content as string
        """
        template_path = Path(template_file)

        # Render template
        rendered = self.render_template(
            template_source=template_path,
            config_file=config_file
        )

        # Save to file if output_file specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered)
            print(f"✅ Generated: {output_path}")
            print(f"   Size: {len(rendered)} bytes")

        return rendered

    def register_function(self, name: str, func: Callable):
        """
        Register a custom function for use in templates

        Example:
            def greet(name):
                return f"Hello, {name}!"

            engine.register_function('greet', greet)
            engine.render_template("{{greet('World')}}", {})
            # → "Hello, World!"
        """
        self.functions[name] = func


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Universal Formula Engine - Render templates with formulas'
    )
    parser.add_argument(
        '--template',
        required=True,
        help='Path to template file'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to config file (JSON or YAML)'
    )
    parser.add_argument(
        '--output',
        help='Path to output file (optional, prints to stdout if not specified)'
    )

    args = parser.parse_args()

    # Create engine
    engine = FormulaEngine()

    # Compile template
    rendered = engine.compile_file(
        template_file=args.template,
        config_file=args.config,
        output_file=args.output
    )

    # Print to stdout if no output file specified
    if not args.output:
        print(rendered)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Template Anatomy Analyzer - Visual Tool for Understanding Template Structure

PROVES how templates work by showing:
- What they extend (inheritance chain)
- What blocks they define/fill
- What variables they use
- What filters are applied
- Complete dependency graph

Usage:
    python3 template_anatomy.py brand_page.html
    python3 template_anatomy.py templates/brand_page.html
    python3 template_anatomy.py --all  # Analyze all templates
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple


# ==============================================================================
# TEMPLATE PARSING
# ==============================================================================

class TemplateAnatomy:
    """Analyzes the structure of a Jinja2 template"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.content = self._read_file()

        # Parsed components
        self.extends: Optional[str] = None
        self.blocks_defined: List[str] = []
        self.blocks_filled: List[str] = []
        self.variables: Set[str] = set()
        self.filters: Set[str] = set()
        self.includes: List[str] = []
        self.conditionals: List[str] = []
        self.loops: List[str] = []

        self._parse()

    def _read_file(self) -> str:
        """Read template file"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse(self):
        """Parse template and extract components"""

        # Find extends
        extends_match = re.search(r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}', self.content)
        if extends_match:
            self.extends = extends_match.group(1)

        # Find block definitions (parent template)
        block_defs = re.findall(r'{%\s*block\s+(\w+)\s*%}', self.content)
        self.blocks_defined = block_defs

        # Find block fills (child template overriding parent)
        if self.extends:
            self.blocks_filled = block_defs  # If extends, blocks are fills

        # Find variables {{ variable }}
        var_matches = re.findall(r'{{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)', self.content)
        self.variables = set(var_matches)

        # Find filters {{ variable|filter }}
        filter_matches = re.findall(r'\|\s*([a-zA-Z_][a-zA-Z0-9_]*)', self.content)
        self.filters = set(filter_matches)

        # Find includes
        include_matches = re.findall(r'{%\s*include\s+["\']([^"\']+)["\']\s*%}', self.content)
        self.includes = include_matches

        # Find conditionals
        if_matches = re.findall(r'{%\s*if\s+([^%]+)\s*%}', self.content)
        self.conditionals = if_matches

        # Find loops
        for_matches = re.findall(r'{%\s*for\s+([^%]+)\s*%}', self.content)
        self.loops = for_matches


# ==============================================================================
# VISUAL OUTPUT
# ==============================================================================

def print_template_header(filename: str):
    """Print visual header for template"""
    print()
    print("=" * 100)
    print(f"  📄 TEMPLATE ANATOMY: {filename}")
    print("=" * 100)
    print()


def print_inheritance_chain(anatomy: TemplateAnatomy, templates_dir: str):
    """Print template inheritance chain"""
    print("🔗 INHERITANCE CHAIN:")
    print()

    chain = [anatomy.filename]
    current = anatomy.extends

    while current:
        chain.append(current)
        parent_path = os.path.join(templates_dir, current)
        if os.path.exists(parent_path):
            parent = TemplateAnatomy(parent_path)
            current = parent.extends
        else:
            break

    # Print chain visually
    for i, template in enumerate(chain):
        indent = "  " * i
        if i == 0:
            marker = "🎯 THIS TEMPLATE"
        elif i == len(chain) - 1:
            marker = "🏁 BASE TEMPLATE"
        else:
            marker = "📄 EXTENDS"

        print(f"{indent}{marker}: {template}")
        if i < len(chain) - 1:
            print(f"{indent}  ↓ extends")

    print()


def print_blocks(anatomy: TemplateAnatomy):
    """Print block information"""

    if anatomy.extends:
        print("📦 BLOCKS FILLED (Child overrides parent):")
        if anatomy.blocks_filled:
            for block in anatomy.blocks_filled:
                print(f"   • {block}")
        else:
            print("   (none)")
    else:
        print("📦 BLOCKS DEFINED (Parent defines structure):")
        if anatomy.blocks_defined:
            for block in anatomy.blocks_defined:
                print(f"   • {block}")
        else:
            print("   (none)")

    print()


def print_variables(anatomy: TemplateAnatomy):
    """Print variables used"""
    print("🔤 VARIABLES USED:")

    if anatomy.variables:
        # Group by root variable (before first dot)
        root_vars: Dict[str, List[str]] = {}
        for var in sorted(anatomy.variables):
            root = var.split('.')[0]
            if root not in root_vars:
                root_vars[root] = []
            root_vars[root].append(var)

        for root, vars_list in sorted(root_vars.items()):
            print(f"   • {root}")
            if len(vars_list) > 1 or vars_list[0] != root:
                for var in vars_list:
                    if var != root:
                        print(f"      └─ {var}")
    else:
        print("   (none)")

    print()


def print_filters(anatomy: TemplateAnatomy):
    """Print filters used"""
    print("🔧 FILTERS APPLIED:")

    if anatomy.filters:
        for filter_name in sorted(anatomy.filters):
            # Explain common filters
            explanations = {
                'safe': 'Don\'t escape HTML (allows raw HTML)',
                'default': 'Provide fallback value if None',
                'length': 'Get length of list/string',
                'title': 'Convert to title case',
                'lower': 'Convert to lowercase',
                'upper': 'Convert to uppercase',
                'int': 'Convert to integer',
                'float': 'Convert to float',
                'json': 'Convert to JSON string'
            }
            explanation = explanations.get(filter_name, '')
            if explanation:
                print(f"   • {filter_name} - {explanation}")
            else:
                print(f"   • {filter_name}")
    else:
        print("   (none)")

    print()


def print_control_structures(anatomy: TemplateAnatomy):
    """Print conditionals and loops"""

    print("🔀 CONTROL STRUCTURES:")
    print()

    if anatomy.conditionals:
        print("   IF STATEMENTS:")
        for cond in anatomy.conditionals:
            print(f"      • if {cond.strip()}")
        print()

    if anatomy.loops:
        print("   FOR LOOPS:")
        for loop in anatomy.loops:
            print(f"      • for {loop.strip()}")
        print()

    if not anatomy.conditionals and not anatomy.loops:
        print("   (none)")
        print()


def print_includes(anatomy: TemplateAnatomy):
    """Print included templates"""
    print("📎 INCLUDES:")

    if anatomy.includes:
        for inc in anatomy.includes:
            print(f"   • {inc}")
    else:
        print("   (none)")

    print()


def print_data_requirements(anatomy: TemplateAnatomy):
    """Print what data this template needs from Flask route"""
    print("=" * 100)
    print("  💡 DATA REQUIREMENTS - What Flask Route Must Provide")
    print("=" * 100)
    print()

    # Extract root variables (these come from Flask)
    root_vars = set()
    for var in anatomy.variables:
        root = var.split('.')[0]
        root_vars.add(root)

    print("📥 This template expects these variables from render_template():")
    print()

    if root_vars:
        for var in sorted(root_vars):
            print(f"   • {var}")

        print()
        print("🔍 Example Flask route:")
        print()
        print("   @app.route('/some-route')")
        print("   def some_view():")
        print("       return render_template(")
        print(f"           '{anatomy.filename}',")
        for var in sorted(root_vars):
            print(f"           {var}=...,  # ← REQUIRED!")
        print("       )")
    else:
        print("   (no variables - this is a static template)")

    print()


def print_summary(anatomy: TemplateAnatomy):
    """Print summary statistics"""
    print("=" * 100)
    print("  📊 SUMMARY")
    print("=" * 100)
    print()

    print(f"   Template Type:   {'Child (extends parent)' if anatomy.extends else 'Parent (base template)'}")
    print(f"   Extends:         {anatomy.extends or 'None (base template)'}")
    print(f"   Blocks:          {len(anatomy.blocks_defined)}")
    print(f"   Variables:       {len(anatomy.variables)}")
    print(f"   Filters:         {len(anatomy.filters)}")
    print(f"   Conditionals:    {len(anatomy.conditionals)}")
    print(f"   Loops:           {len(anatomy.loops)}")
    print(f"   Includes:        {len(anatomy.includes)}")

    print()


# ==============================================================================
# MAIN ANALYSIS FUNCTION
# ==============================================================================

def analyze_template(template_path: str, templates_dir: str = "templates"):
    """
    Analyze a template and print its complete anatomy

    Args:
        template_path: Path to template file (can be relative or absolute)
        templates_dir: Base templates directory
    """

    # Resolve path
    if not os.path.isabs(template_path):
        if not template_path.startswith(templates_dir):
            template_path = os.path.join(templates_dir, template_path)

    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return

    # Parse template
    anatomy = TemplateAnatomy(template_path)

    # Print complete anatomy
    print_template_header(anatomy.filename)
    print_inheritance_chain(anatomy, templates_dir)
    print_blocks(anatomy)
    print_variables(anatomy)
    print_filters(anatomy)
    print_control_structures(anatomy)
    print_includes(anatomy)
    print_data_requirements(anatomy)
    print_summary(anatomy)


def analyze_all_templates(templates_dir: str = "templates"):
    """Analyze all templates in directory"""

    if not os.path.exists(templates_dir):
        print(f"❌ Templates directory not found: {templates_dir}")
        return

    # Find all .html files
    template_files = list(Path(templates_dir).glob("**/*.html"))

    if not template_files:
        print(f"❌ No templates found in {templates_dir}")
        return

    print()
    print("=" * 100)
    print(f"  📚 ANALYZING ALL TEMPLATES IN {templates_dir}/")
    print("=" * 100)
    print()
    print(f"Found {len(template_files)} templates")
    print()

    for template_file in sorted(template_files):
        analyze_template(str(template_file), templates_dir)
        print()
        print("-" * 100)


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 template_anatomy.py brand_page.html")
        print("  python3 template_anatomy.py templates/brand_page.html")
        print("  python3 template_anatomy.py --all")
        return

    arg = sys.argv[1]

    if arg == "--all":
        analyze_all_templates()
    else:
        analyze_template(arg)


if __name__ == '__main__':
    main()

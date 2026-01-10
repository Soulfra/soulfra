#!/usr/bin/env python3
"""
Template Library - Modular Template System

Central registry for all code templates. Each module registers its templates here.

Usage:
    from templates_lib import get_template, list_templates, list_categories

    # Get all templates
    templates = list_templates()

    # Get template by type and name
    template = get_template('database', 'migration')
    code = template.generate(name='add_users')

    # List categories
    categories = list_categories()  # ['database', 'python', 'go', ...]

Architecture:
    Each template module (database.py, python_advanced.py, etc.) exports:
    - TEMPLATES dict: Maps template names to generator functions
    - CATEGORY: Category name for this module

    This __init__.py:
    - Imports all modules
    - Builds unified template registry
    - Provides search/filter/generation API
"""

from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import importlib
import os


@dataclass
class Template:
    """
    Represents a single code template

    Attributes:
        category: Category (database, python, go, etc.)
        name: Template name (migration, cli-tool, etc.)
        description: What this template does
        generator: Function that generates the code
        parameters: List of required parameters
        examples: Example usage
        tags: Search tags
    """
    category: str
    name: str
    description: str
    generator: Callable
    parameters: List[str]
    examples: List[str] = None
    tags: List[str] = None

    def generate(self, **kwargs) -> str:
        """Generate code from this template"""
        return self.generator(**kwargs)


class TemplateRegistry:
    """
    Central registry for all templates

    Automatically loads all template modules and builds a searchable registry.
    """

    def __init__(self):
        self.templates: Dict[str, Dict[str, Template]] = {}
        self._load_all_modules()

    def _load_all_modules(self):
        """Load all template modules from templates_lib/"""
        module_files = [
            'database',
            'python_advanced',
            'languages',
            'devops',
            'configs',
            'projects',
            'testing',
            'docs',
            'neural_networks',
            'games',
            'reviews',
            'bash'
        ]

        for module_name in module_files:
            try:
                module = importlib.import_module(f'templates_lib.{module_name}')
                self._register_module(module)
            except ImportError as e:
                # Module doesn't exist yet - skip silently
                pass
            except Exception as e:
                print(f"⚠️  Failed to load template module {module_name}: {e}")

    def _register_module(self, module):
        """Register all templates from a module"""
        if not hasattr(module, 'TEMPLATES'):
            return

        category = getattr(module, 'CATEGORY', 'uncategorized')

        if category not in self.templates:
            self.templates[category] = {}

        # Register each template
        for name, template_def in module.TEMPLATES.items():
            template = Template(
                category=category,
                name=name,
                description=template_def.get('description', ''),
                generator=template_def['generator'],
                parameters=template_def.get('parameters', []),
                examples=template_def.get('examples', []),
                tags=template_def.get('tags', [])
            )
            self.templates[category][name] = template

    def get(self, category: str, name: str) -> Optional[Template]:
        """Get a specific template"""
        return self.templates.get(category, {}).get(name)

    def list_categories(self) -> List[str]:
        """List all template categories"""
        return sorted(self.templates.keys())

    def list_templates(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all templates, optionally filtered by category

        Returns:
            Dict mapping category -> list of template names
        """
        if category:
            return {category: list(self.templates.get(category, {}).keys())}

        return {
            cat: list(templates.keys())
            for cat, templates in self.templates.items()
        }

    def search(self, query: str) -> List[Template]:
        """
        Search templates by name, description, or tags

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching templates
        """
        query = query.lower()
        results = []

        for category, templates in self.templates.items():
            for name, template in templates.items():
                # Search in name, description, tags
                searchable = [
                    name.lower(),
                    template.description.lower(),
                    category.lower()
                ]

                if template.tags:
                    searchable.extend([tag.lower() for tag in template.tags])

                if any(query in text for text in searchable):
                    results.append(template)

        return results

    def generate(self, category: str, name: str, **kwargs) -> Optional[str]:
        """
        Generate code from a template

        Args:
            category: Template category
            name: Template name
            **kwargs: Parameters for template generation

        Returns:
            Generated code or None if template not found
        """
        template = self.get(category, name)
        if template:
            return template.generate(**kwargs)
        return None


# ============================================================================
# GLOBAL REGISTRY - Singleton instance
# ============================================================================

_registry = None

def get_registry() -> TemplateRegistry:
    """Get the global template registry (singleton)"""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry


# ============================================================================
# CONVENIENCE FUNCTIONS - Easy API for common operations
# ============================================================================

def get_template(category: str, name: str) -> Optional[Template]:
    """Get a specific template"""
    return get_registry().get(category, name)


def list_templates(category: Optional[str] = None) -> Dict[str, List[str]]:
    """List all templates"""
    return get_registry().list_templates(category)


def list_categories() -> List[str]:
    """List all template categories"""
    return get_registry().list_categories()


def search_templates(query: str) -> List[Template]:
    """Search templates"""
    return get_registry().search(query)


def generate_template(category: str, name: str, **kwargs) -> Optional[str]:
    """Generate code from a template"""
    return get_registry().generate(category, name, **kwargs)


# ============================================================================
# CLI HELPER - For template_generator.py integration
# ============================================================================

def print_template_list():
    """Print formatted list of all templates (for CLI)"""
    registry = get_registry()
    categories = registry.list_categories()

    print("="*70)
    print("📋 AVAILABLE TEMPLATES")
    print("="*70)
    print()

    for category in categories:
        templates = registry.list_templates(category)[category]
        print(f"{category.upper()}:")
        print(f"  {', '.join(templates)}")
        print()


if __name__ == '__main__':
    # Test the registry
    print("🧪 Testing Template Registry\n")

    registry = get_registry()

    print(f"Categories: {registry.list_categories()}")
    print(f"Templates: {registry.list_templates()}")

    # Test search
    results = registry.search('test')
    print(f"\nSearch 'test': {len(results)} results")

    print("\n✅ Template registry working!")

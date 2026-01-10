#!/usr/bin/env python3
"""
Plugin Loader - Hot-Reload Modular Feature System

Auto-discovers and loads feature plugins from features/ directory.
Features are self-contained Flask Blueprints that auto-register.

Usage in app.py:
    from plugin_loader import load_all_features
    load_all_features(app)

Feature Structure:
    features/
    └── quiz_game/
        ├── __init__.py      # Exports 'blueprint'
        ├── quiz_game.py     # Blueprint definition
        ├── templates/       # Feature templates
        └── migrations/      # Feature migrations
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import importlib
import sqlite3
import yaml


def discover_features(features_dir: str = 'features') -> List[str]:
    """
    Discover all feature plugins in features directory

    Args:
        features_dir: Directory containing features

    Returns:
        List of feature names
    """
    features_path = Path(features_dir)

    if not features_path.exists():
        print(f"[WARNING] Features directory not found: {features_dir}")
        return []

    features = []
    for item in features_path.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            # Check if it has __init__.py (valid Python package)
            if (item / '__init__.py').exists():
                features.append(item.name)

    return sorted(features)


def load_feature_metadata(feature_name: str, features_dir: str = 'features') -> Dict[str, Any]:
    """
    Load metadata from feature.yaml

    Args:
        feature_name: Name of feature
        features_dir: Features directory

    Returns:
        Dict with metadata, or empty dict if no feature.yaml found
    """
    yaml_path = Path(features_dir) / feature_name / 'feature.yaml'

    if not yaml_path.exists():
        return {
            'name': feature_name.replace('_', ' ').title(),
            'description': 'No description available',
            'visible_in_hub': False,
            'visible_in_nav': False
        }

    try:
        with open(yaml_path, 'r') as f:
            metadata = yaml.safe_load(f)
            return metadata or {}
    except Exception as e:
        print(f"[WARNING] {feature_name}: Failed to load feature.yaml - {e}")
        return {}


def run_feature_migrations(feature_name: str, features_dir: str = 'features', db_path: str = 'soulfra.db') -> bool:
    """
    Auto-run migrations for a feature

    Args:
        feature_name: Name of feature
        features_dir: Features directory
        db_path: Database file path

    Returns:
        True if successful
    """
    migrations_dir = Path(features_dir) / feature_name / 'migrations'

    if not migrations_dir.exists():
        return True  # No migrations needed

    # Get all .sql files
    migration_files = sorted(migrations_dir.glob('*.sql'))

    if not migration_files:
        return True  # No migrations

    try:
        conn = sqlite3.connect(db_path)

        for migration_file in migration_files:
            print(f"   Running migration: {migration_file.name}")
            sql = migration_file.read_text()
            conn.executescript(sql)

        conn.commit()
        conn.close()

        print(f"   [OK] {len(migration_files)} migration(s) applied")
        return True

    except Exception as e:
        print(f"   [ERROR] Migration failed: {e}")
        return False


def load_feature(feature_name: str, app, features_dir: str = 'features', auto_migrate: bool = True) -> Dict[str, Any]:
    """
    Load a single feature plugin

    Args:
        feature_name: Name of feature
        app: Flask application
        features_dir: Features directory
        auto_migrate: Auto-run migrations

    Returns:
        Dict with 'success': bool and 'metadata': dict
    """
    try:
        # Load metadata first
        metadata = load_feature_metadata(feature_name, features_dir)

        # Run migrations first
        if auto_migrate:
            print(f"[MIGRATION] {feature_name}: Checking migrations...")
            run_feature_migrations(feature_name, features_dir)

        # Import feature module
        module_path = f'{features_dir}.{feature_name}'
        module = importlib.import_module(module_path)

        # Get blueprint
        if not hasattr(module, 'blueprint'):
            print(f"[WARNING] {feature_name}: No 'blueprint' exported from __init__.py")
            return {'success': False, 'metadata': metadata}

        blueprint = module.blueprint

        # Register with Flask
        app.register_blueprint(blueprint)

        print(f"[OK] {feature_name}: Loaded successfully")
        return {'success': True, 'metadata': metadata, 'blueprint': blueprint}

    except ImportError as e:
        print(f"[ERROR] {feature_name}: Import failed - {e}")
        return {'success': False, 'metadata': {}}
    except Exception as e:
        print(f"[ERROR] {feature_name}: Failed to load - {e}")
        return {'success': False, 'metadata': {}}


def load_all_features(app, features_dir: str = 'features', auto_migrate: bool = True) -> Dict[str, bool]:
    """
    Auto-discover and load all feature plugins

    Args:
        app: Flask application
        features_dir: Directory containing features
        auto_migrate: Auto-run migrations

    Returns:
        Dict mapping feature names to load success status
    """
    print("\n" + "=" * 80)
    print("  PLUGIN LOADER - Auto-Loading Features")
    print("=" * 80 + "\n")

    # Initialize plugin registry on app
    if not hasattr(app, 'loaded_plugins'):
        app.loaded_plugins = []

    # Add features directory to Python path
    features_path = Path(features_dir).resolve()
    if str(features_path.parent) not in sys.path:
        sys.path.insert(0, str(features_path.parent))

    # Discover features
    features = discover_features(features_dir)

    if not features:
        print("[INFO] No features found")
        print("       Create features in: features/<feature_name>/")
        print("=" * 80 + "\n")
        return {}

    print(f"[DISCOVER] Found {len(features)} feature(s): {', '.join(features)}\n")

    # Load each feature
    results = {}
    for feature_name in features:
        result = load_feature(feature_name, app, features_dir, auto_migrate)
        results[feature_name] = result['success']

        # Add to plugin registry
        if result['success']:
            plugin_entry = {
                'id': feature_name,
                'name': result['metadata'].get('name', feature_name.replace('_', ' ').title()),
                'description': result['metadata'].get('description', 'No description available'),
                'url': result['metadata'].get('url_prefix', f'/{feature_name}'),
                'icon': result['metadata'].get('icon', 'plugin'),
                'category': result['metadata'].get('category', 'Uncategorized'),
                'visible_in_hub': result['metadata'].get('visible_in_hub', False),
                'visible_in_nav': result['metadata'].get('visible_in_nav', False),
                'author': result['metadata'].get('author', 'Unknown'),
                'version': result['metadata'].get('version', '1.0.0'),
                'metadata': result['metadata']
            }
            app.loaded_plugins.append(plugin_entry)

        print()  # Blank line between features

    # Summary
    loaded_count = sum(1 for success in results.values() if success)
    print("=" * 80)
    print(f"  [OK] Loaded {loaded_count}/{len(features)} features successfully")
    print("=" * 80 + "\n")

    return results


def reload_feature(feature_name: str, app, features_dir: str = 'features') -> bool:
    """
    Hot-reload a specific feature (for development)

    Args:
        feature_name: Name of feature to reload
        app: Flask application
        features_dir: Features directory

    Returns:
        True if reloaded successfully
    """
    print(f"[RELOAD] Hot-reloading: {feature_name}")

    try:
        # Reimport the module
        module_path = f'{features_dir}.{feature_name}'

        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])
        else:
            importlib.import_module(module_path)

        print(f"[OK] {feature_name}: Reloaded successfully")
        return True

    except Exception as e:
        print(f"[ERROR] {feature_name}: Reload failed - {e}")
        return False


if __name__ == '__main__':
    """Test plugin discovery"""
    print("Plugin Loader Test\n")

    features = discover_features()
    print(f"Found {len(features)} features:")
    for feature in features:
        print(f"  - {feature}")

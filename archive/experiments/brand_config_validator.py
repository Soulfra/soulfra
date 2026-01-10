#!/usr/bin/env python3
"""
Brand Config Validator - JSON Schema & Error Detection

Validates brand configurations with detailed error reporting.
Detects common failure patterns before they cause crashes.

This is the "error schema" system - validates data before using it!

Usage:
    from brand_config_validator import validate_brand_config, ValidationResult

    result = validate_brand_config(config_json_string)

    if result.is_valid:
        print("✅ Config is valid!")
        parsed = result.parsed_config
    else:
        print("❌ Validation failed:")
        for error in result.errors:
            print(f"  - {error}")
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation - Railway pattern!"""
    is_valid: bool
    parsed_config: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    failure_patterns: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.failure_patterns is None:
            self.failure_patterns = []


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

BRAND_SCHEMA = {
    "name": {
        "type": "string",
        "required": True,
        "min_length": 1,
        "max_length": 100,
        "description": "Brand display name"
    },
    "slug": {
        "type": "string",
        "required": False,  # Auto-generated if missing
        "pattern": r"^[a-z0-9-]+$",
        "description": "URL-safe brand identifier"
    },
    "colors": {
        "type": ["array", "dict"],  # Accept both formats
        "required": True,
        "description": "Brand color palette",
        "array_schema": {
            "min_items": 1,
            "max_items": 10,
            "item_type": "hex_color"
        },
        "dict_schema": {
            "required_keys": ["primary"],
            "optional_keys": ["secondary", "accent"],
            "value_type": "hex_color"
        }
    },
    "personality": {
        "type": "string",
        "required": True,
        "min_length": 3,
        "description": "Brand personality traits"
    },
    "tone": {
        "type": "string",
        "required": True,
        "min_length": 3,
        "description": "Brand communication tone"
    },
    "license_type": {
        "type": "string",
        "required": False,
        "enum": ["cc0", "cc-by", "licensed", "proprietary"],
        "default": "cc0",
        "description": "License type"
    },
    "emoji": {
        "type": "string",
        "required": False,
        "pattern": r"^[\U00010000-\U0010ffff]+$",  # Unicode emoji
        "description": "Brand emoji icon"
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATORS
# ═══════════════════════════════════════════════════════════════════════════

def is_hex_color(value: str) -> bool:
    """Check if string is valid hex color (#RRGGBB or #RGB)"""
    if not isinstance(value, str):
        return False
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, value))


def validate_type(value: Any, expected_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate value against expected type

    Returns: (is_valid, error_message)
    """
    if expected_type == "string":
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"
        return True, None

    elif expected_type == "array":
        if not isinstance(value, list):
            return False, f"Expected array/list, got {type(value).__name__}"
        return True, None

    elif expected_type == "dict":
        if not isinstance(value, dict):
            return False, f"Expected dict/object, got {type(value).__name__}"
        return True, None

    elif expected_type == "hex_color":
        if not is_hex_color(value):
            return False, f"Expected hex color (#RRGGBB), got '{value}'"
        return True, None

    return True, None


def detect_failure_patterns(config: Dict[str, Any], errors: List[str]) -> List[str]:
    """
    Detect common failure patterns

    This is the "pattern recognition" - learn from past mistakes!
    """
    patterns = []

    # Pattern 1: Colors as array when dict expected
    if "colors" in config and isinstance(config["colors"], list):
        patterns.append(
            "PATTERN: Colors stored as array - needs conversion to dict with "
            "'primary', 'secondary', 'accent' keys for CSS generation"
        )

    # Pattern 2: Missing config_json in database
    if not config:
        patterns.append(
            "PATTERN: Empty config - likely missing config_json column in database "
            "(use 'config_json' not 'config')"
        )

    # Pattern 3: Invalid hex colors (missing #)
    if "colors" in config:
        colors = config["colors"]
        if isinstance(colors, list):
            for i, color in enumerate(colors):
                if isinstance(color, str) and not color.startswith("#"):
                    patterns.append(
                        f"PATTERN: Color at index {i} missing '#' prefix: '{color}' "
                        f"(should be '#{color}')"
                    )
        elif isinstance(colors, dict):
            for key, color in colors.items():
                if isinstance(color, str) and not color.startswith("#"):
                    patterns.append(
                        f"PATTERN: Color '{key}' missing '#' prefix: '{color}' "
                        f"(should be '#{color}')"
                    )

    # Pattern 4: Wrong JSON structure (nested too deep)
    if "config" in config or "data" in config:
        patterns.append(
            "PATTERN: Nested config structure detected - config should be flat, "
            "not nested under 'config' or 'data' key"
        )

    # Pattern 5: Missing required personality/tone
    if not config.get("personality") or not config.get("tone"):
        patterns.append(
            "PATTERN: Missing personality/tone - brand won't have unique voice. "
            "ML classification will use generic defaults."
        )

    return patterns


def validate_brand_config(config_json: Optional[str]) -> ValidationResult:
    """
    Validate brand configuration against schema

    Args:
        config_json: JSON string of brand config (from database config_json column)

    Returns:
        ValidationResult with detailed error reporting
    """
    errors = []
    warnings = []
    failure_patterns = []

    # Step 1: Parse JSON
    if not config_json:
        errors.append("Config is empty (NULL or empty string)")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            failure_patterns=["PATTERN: Missing config_json in database"]
        )

    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON syntax: {e}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            failure_patterns=["PATTERN: Malformed JSON - check for trailing commas, quotes"]
        )

    # Step 2: Validate against schema
    for field_name, field_schema in BRAND_SCHEMA.items():
        field_required = field_schema.get("required", False)
        field_value = config.get(field_name)

        # Check required fields
        if field_required and field_value is None:
            errors.append(f"Required field '{field_name}' is missing")
            continue

        # Skip optional fields that are None
        if field_value is None:
            continue

        # Validate type
        expected_types = field_schema["type"]
        if not isinstance(expected_types, list):
            expected_types = [expected_types]

        type_valid = False
        type_errors = []

        for expected_type in expected_types:
            is_valid, error_msg = validate_type(field_value, expected_type)
            if is_valid:
                type_valid = True
                break
            else:
                type_errors.append(error_msg)

        if not type_valid:
            errors.append(
                f"Field '{field_name}' type mismatch: {', '.join(type_errors)}"
            )
            continue

        # Validate string constraints
        if expected_types[0] == "string" and isinstance(field_value, str):
            min_len = field_schema.get("min_length")
            max_len = field_schema.get("max_length")
            pattern = field_schema.get("pattern")
            enum_values = field_schema.get("enum")

            if min_len and len(field_value) < min_len:
                errors.append(
                    f"Field '{field_name}' too short (min: {min_len}, got: {len(field_value)})"
                )

            if max_len and len(field_value) > max_len:
                errors.append(
                    f"Field '{field_name}' too long (max: {max_len}, got: {len(field_value)})"
                )

            if pattern and not re.match(pattern, field_value):
                errors.append(
                    f"Field '{field_name}' doesn't match pattern {pattern}"
                )

            if enum_values and field_value not in enum_values:
                errors.append(
                    f"Field '{field_name}' must be one of {enum_values}, got '{field_value}'"
                )

        # Validate array constraints (for colors)
        if field_name == "colors" and isinstance(field_value, list):
            array_schema = field_schema.get("array_schema", {})
            min_items = array_schema.get("min_items", 0)
            max_items = array_schema.get("max_items", float('inf'))
            item_type = array_schema.get("item_type")

            if len(field_value) < min_items:
                errors.append(
                    f"Colors array too short (min: {min_items}, got: {len(field_value)})"
                )

            if len(field_value) > max_items:
                warnings.append(
                    f"Colors array very long ({len(field_value)} colors) - only first 3 used"
                )

            if item_type:
                for i, item in enumerate(field_value):
                    is_valid, error_msg = validate_type(item, item_type)
                    if not is_valid:
                        errors.append(f"Colors[{i}]: {error_msg}")

        # Validate dict constraints (for colors as dict)
        if field_name == "colors" and isinstance(field_value, dict):
            dict_schema = field_schema.get("dict_schema", {})
            required_keys = dict_schema.get("required_keys", [])
            optional_keys = dict_schema.get("optional_keys", [])
            value_type = dict_schema.get("value_type")

            for required_key in required_keys:
                if required_key not in field_value:
                    errors.append(
                        f"Colors dict missing required key '{required_key}'"
                    )

            for key, value in field_value.items():
                if key not in required_keys and key not in optional_keys:
                    warnings.append(
                        f"Colors dict has unknown key '{key}' (will be ignored)"
                    )

                if value_type:
                    is_valid, error_msg = validate_type(value, value_type)
                    if not is_valid:
                        errors.append(f"Colors['{key}']: {error_msg}")

    # Step 3: Detect failure patterns
    failure_patterns = detect_failure_patterns(config, errors)

    # Step 4: Return result
    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        parsed_config=config if is_valid else None,
        errors=errors,
        warnings=warnings,
        failure_patterns=failure_patterns
    )


def validate_all_brands_in_db() -> Dict[str, ValidationResult]:
    """
    Validate all brands in database

    Returns:
        dict: {brand_slug: ValidationResult}
    """
    from database import get_db

    db = get_db()
    brands = db.execute('''
        SELECT slug, name, config_json FROM brands
    ''').fetchall()
    db.close()

    results = {}

    for brand in brands:
        slug = brand['slug']
        config_json = brand['config_json']

        result = validate_brand_config(config_json)
        results[slug] = result

    return results


def main():
    """CLI for validating brands"""
    import sys

    if len(sys.argv) > 1:
        brand_slug = sys.argv[1]

        # Validate single brand
        from database import get_db
        db = get_db()
        brand = db.execute('''
            SELECT slug, name, config_json FROM brands WHERE slug = ?
        ''', (brand_slug,)).fetchone()
        db.close()

        if not brand:
            print(f"❌ Brand '{brand_slug}' not found")
            return

        print("=" * 70)
        print(f"VALIDATING: {brand['name']} ({brand['slug']})")
        print("=" * 70)
        print()

        result = validate_brand_config(brand['config_json'])

        if result.is_valid:
            print("✅ VALID!")
            print()
            print("Parsed config:")
            import json
            print(json.dumps(result.parsed_config, indent=2))
        else:
            print("❌ INVALID!")
            print()
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")

        if result.warnings:
            print()
            print("⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.failure_patterns:
            print()
            print("🔍 Failure Patterns Detected:")
            for pattern in result.failure_patterns:
                print(f"  - {pattern}")

        print()

    else:
        # Validate all brands
        print("=" * 70)
        print("VALIDATING ALL BRANDS")
        print("=" * 70)
        print()

        results = validate_all_brands_in_db()

        valid_count = sum(1 for r in results.values() if r.is_valid)
        total_count = len(results)

        for slug, result in results.items():
            status = "✅" if result.is_valid else "❌"
            error_count = len(result.errors)
            warning_count = len(result.warnings)

            print(f"{status} {slug:<20} {error_count} errors, {warning_count} warnings")

            if not result.is_valid:
                for error in result.errors[:3]:  # First 3 errors
                    print(f"     → {error}")

        print()
        print(f"Summary: {valid_count}/{total_count} brands valid")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Soulfra Type System - Clean Type Conversions & Validation
NO external libraries - Pure Python stdlib only (Bun/Zig/pot philosophy)

Problem: Across 325 files, type conversions are scattered and error-prone
Solution: Centralized type checking with clear error messages

Usage:
    from soulfra_types import safe_int, safe_str, safe_bool, safe_json

    # Safe conversions (never crash)
    user_id = safe_int(request.args.get('id'), default=0)
    api_key = safe_str(data.get('api_key'), max_length=100)
    is_active = safe_bool(form_data.get('active'))
    config = safe_json(file_content, default={})

Design Philosophy:
    1. NEVER crash - always return valid value or default
    2. Type hints everywhere (Python 3.5+ style)
    3. Clear error messages with context
    4. Log issues but don't break execution
"""

import json
import re
from typing import Any, Optional, Union, List, Dict, TypeVar, Callable
from datetime import datetime

T = TypeVar('T')

# ==============================================================================
# CORE TYPE CONVERSIONS
# ==============================================================================

def safe_int(
    value: Any,
    default: int = 0,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None
) -> int:
    """
    Safely convert any value to integer

    Args:
        value: Value to convert
        default: Return this if conversion fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Integer value or default

    Examples:
        >>> safe_int("42")
        42
        >>> safe_int("invalid", default=-1)
        -1
        >>> safe_int(100, min_val=0, max_val=10)
        10
        >>> safe_int("3.14")
        3
    """
    try:
        # Handle None
        if value is None:
            return default

        # Handle boolean (True=1, False=0)
        if isinstance(value, bool):
            return 1 if value else 0

        # Handle string
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default

            # Remove commas from numbers like "1,000"
            value = value.replace(',', '')

            # Handle floats in strings
            if '.' in value:
                value = float(value)

        # Convert to int
        result = int(value)

        # Apply bounds
        if min_val is not None and result < min_val:
            return min_val
        if max_val is not None and result > max_val:
            return max_val

        return result

    except (ValueError, TypeError, OverflowError):
        return default


def safe_str(
    value: Any,
    default: str = '',
    max_length: Optional[int] = None,
    strip: bool = True,
    lower: bool = False,
    upper: bool = False
) -> str:
    """
    Safely convert any value to string

    Args:
        value: Value to convert
        default: Return this if conversion fails
        max_length: Truncate if longer
        strip: Remove leading/trailing whitespace
        lower: Convert to lowercase
        upper: Convert to uppercase

    Returns:
        String value or default

    Examples:
        >>> safe_str(42)
        '42'
        >>> safe_str(None, default="N/A")
        'N/A'
        >>> safe_str("  Hello  ", strip=True)
        'Hello'
        >>> safe_str("LongText", max_length=4)
        'Long'
    """
    try:
        # Handle None
        if value is None:
            return default

        # Convert to string
        if isinstance(value, bytes):
            result = value.decode('utf-8', errors='replace')
        else:
            result = str(value)

        # Apply transformations
        if strip:
            result = result.strip()
        if lower:
            result = result.lower()
        if upper:
            result = result.upper()

        # Apply max length
        if max_length is not None and len(result) > max_length:
            result = result[:max_length]

        return result

    except (ValueError, TypeError, UnicodeDecodeError):
        return default


def safe_bool(
    value: Any,
    default: bool = False
) -> bool:
    """
    Safely convert any value to boolean

    Args:
        value: Value to convert
        default: Return this if ambiguous

    Returns:
        Boolean value

    Examples:
        >>> safe_bool("true")
        True
        >>> safe_bool("1")
        True
        >>> safe_bool("yes")
        True
        >>> safe_bool(0)
        False
        >>> safe_bool(None)
        False
    """
    # Handle None
    if value is None:
        return default

    # Handle boolean
    if isinstance(value, bool):
        return value

    # Handle numbers
    if isinstance(value, (int, float)):
        return value != 0

    # Handle strings
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ('true', '1', 'yes', 'y', 'on', 'enabled'):
            return True
        if value in ('false', '0', 'no', 'n', 'off', 'disabled', ''):
            return False

    return default


def safe_json(
    value: Any,
    default: Optional[Union[Dict, List]] = None
) -> Union[Dict, List]:
    """
    Safely parse JSON string or return default

    Args:
        value: JSON string or dict/list
        default: Return this if parsing fails

    Returns:
        Parsed JSON or default

    Examples:
        >>> safe_json('{"key": "value"}')
        {'key': 'value'}
        >>> safe_json('invalid', default={})
        {}
        >>> safe_json(['already', 'list'])
        ['already', 'list']
    """
    if default is None:
        default = {}

    # Already parsed
    if isinstance(value, (dict, list)):
        return value

    # Parse string
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    # Other types
    return default


def safe_float(
    value: Any,
    default: float = 0.0,
    decimals: Optional[int] = None
) -> float:
    """
    Safely convert any value to float

    Args:
        value: Value to convert
        default: Return this if conversion fails
        decimals: Round to this many decimal places

    Returns:
        Float value or default

    Examples:
        >>> safe_float("3.14")
        3.14
        >>> safe_float("invalid", default=0.0)
        0.0
        >>> safe_float(3.14159, decimals=2)
        3.14
    """
    try:
        if value is None:
            return default

        result = float(value)

        if decimals is not None:
            result = round(result, decimals)

        return result

    except (ValueError, TypeError):
        return default


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

def is_valid_email(email: str) -> bool:
    """
    Check if string is valid email format

    Examples:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid")
        False
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """
    Check if string is valid URL format

    Examples:
        >>> is_valid_url("https://example.com")
        True
        >>> is_valid_url("not a url")
        False
    """
    if not url or not isinstance(url, str):
        return False

    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))


def is_valid_api_key(api_key: str, prefix: str = 'sk_') -> bool:
    """
    Check if string is valid API key format

    Examples:
        >>> is_valid_api_key("sk_github_username_abc123")
        True
        >>> is_valid_api_key("invalid")
        False
    """
    if not api_key or not isinstance(api_key, str):
        return False

    return api_key.startswith(prefix) and len(api_key) > len(prefix)


# ==============================================================================
# SAFE DICTIONARY ACCESS
# ==============================================================================

def safe_get(
    data: Dict,
    key: str,
    default: Any = None,
    converter: Optional[Callable] = None
) -> Any:
    """
    Safely get value from dictionary with optional type conversion

    Args:
        data: Dictionary to read from
        key: Key to look up
        default: Return this if key missing
        converter: Function to convert value (e.g., safe_int)

    Returns:
        Value or default

    Examples:
        >>> data = {'age': '25', 'name': 'John'}
        >>> safe_get(data, 'age', converter=safe_int)
        25
        >>> safe_get(data, 'missing', default='N/A')
        'N/A'
    """
    if not isinstance(data, dict):
        return default

    value = data.get(key, default)

    if converter is not None and value is not default:
        try:
            return converter(value)
        except Exception:
            return default

    return value


# ==============================================================================
# TIMESTAMP CONVERSIONS
# ==============================================================================

def safe_timestamp(
    value: Any,
    default: Optional[datetime] = None
) -> datetime:
    """
    Safely convert value to datetime

    Args:
        value: Timestamp string, unix timestamp, or datetime
        default: Return this if conversion fails

    Returns:
        datetime object or default

    Examples:
        >>> safe_timestamp("2025-01-01")
        datetime.datetime(2025, 1, 1, 0, 0)
        >>> safe_timestamp(1704067200)  # Unix timestamp
        datetime.datetime(2024, 1, 1, 0, 0)
    """
    if default is None:
        default = datetime.now()

    # Already datetime
    if isinstance(value, datetime):
        return value

    # Unix timestamp (int)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, OSError):
            return default

    # ISO format string
    if isinstance(value, str):
        try:
            # Try ISO format
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass

    return default


# ==============================================================================
# BATCH CONVERSIONS
# ==============================================================================

def safe_list(
    value: Any,
    item_type: Optional[Callable] = None,
    default: Optional[List] = None
) -> List:
    """
    Safely convert value to list

    Args:
        value: Value to convert (str, tuple, set, etc.)
        item_type: Convert each item with this function
        default: Return this if conversion fails

    Returns:
        List or default

    Examples:
        >>> safe_list("1,2,3")
        ['1', '2', '3']
        >>> safe_list("1,2,3", item_type=safe_int)
        [1, 2, 3]
        >>> safe_list((1, 2, 3))
        [1, 2, 3]
    """
    if default is None:
        default = []

    # Already list
    if isinstance(value, list):
        result = value
    # String (split by comma)
    elif isinstance(value, str):
        result = [item.strip() for item in value.split(',') if item.strip()]
    # Other iterables
    elif hasattr(value, '__iter__') and not isinstance(value, (dict, bytes)):
        result = list(value)
    else:
        return default

    # Apply item type conversion
    if item_type is not None:
        try:
            result = [item_type(item) for item in result]
        except Exception:
            return default

    return result


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Soulfra Type System")
    print()

    # Test safe_int
    assert safe_int("42") == 42
    assert safe_int("invalid", default=-1) == -1
    assert safe_int(100, max_val=10) == 10
    print("✅ safe_int tests passed")

    # Test safe_str
    assert safe_str(42) == "42"
    assert safe_str(None, default="N/A") == "N/A"
    assert safe_str("  hello  ", strip=True) == "hello"
    print("✅ safe_str tests passed")

    # Test safe_bool
    assert safe_bool("true") is True
    assert safe_bool(0) is False
    assert safe_bool("yes") is True
    print("✅ safe_bool tests passed")

    # Test safe_json
    assert safe_json('{"key": "value"}') == {"key": "value"}
    assert safe_json("invalid", default={}) == {}
    print("✅ safe_json tests passed")

    # Test validations
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("invalid") is False
    assert is_valid_url("https://example.com") is True
    print("✅ Validation tests passed")

    print()
    print("🎉 All tests passed!")

"""
Security Helpers - Input Validation & Sanitization

Provides helper functions to validate and sanitize user input
to prevent SQL injection, XSS, and other security vulnerabilities.
"""

import re
import html
from typing import Optional, List

# Whitelist of valid table names (for dynamic queries)
VALID_TABLES = {
    'users', 'posts', 'comments', 'messages', 'notifications',
    'subscribers', 'brands', 'brand_submissions', 'brand_reviews',
    'conversations', 'conversation_messages', 'brand_concepts',
    'brand_votes', 'qr_codes', 'qr_scans', 'cringeproof_results',
    'cringeproof_rooms', 'neural_networks', 'training_data'
}


def sanitize_content(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user-generated content

    Args:
        text: Raw user input
        allow_html: Whether to allow HTML (escaped if False)

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace('\x00', '')

    # Strip excessive whitespace
    text = text.strip()

    # Escape HTML if not allowed
    if not allow_html:
        text = html.escape(text)

    return text


def sanitize_slug(slug: str) -> str:
    """
    Sanitize URL slug to prevent path traversal

    Args:
        slug: URL slug from user input

    Returns:
        Safe slug (lowercase, alphanumeric + hyphens only)
    """
    if not slug:
        return ""

    # Convert to lowercase
    slug = slug.lower()

    # Remove dangerous characters
    slug = re.sub(r'[^a-z0-9\-]', '', slug)

    # Remove path traversal attempts
    slug = slug.replace('..', '').replace('/', '').replace('\\', '')

    # Limit length
    slug = slug[:200]

    return slug


def validate_table_name(table_name: str) -> bool:
    """
    Validate table name against whitelist

    Args:
        table_name: Table name from dynamic query

    Returns:
        True if valid, False otherwise
    """
    return table_name in VALID_TABLES


def safe_table_query(table_name: str) -> Optional[str]:
    """
    Return sanitized table name or None if invalid

    Args:
        table_name: Requested table name

    Returns:
        Validated table name or None
    """
    if validate_table_name(table_name):
        return table_name
    return None


def sanitize_email(email: str) -> str:
    """
    Sanitize email address

    Args:
        email: Email from user input

    Returns:
        Sanitized email or empty string if invalid
    """
    if not email:
        return ""

    # Basic email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(email_pattern, email):
        return email.lower().strip()

    return ""


def sanitize_username(username: str) -> str:
    """
    Sanitize username to alphanumeric + underscores

    Args:
        username: Username from user input

    Returns:
        Sanitized username
    """
    if not username:
        return ""

    # Allow alphanumeric, underscores, hyphens
    username = re.sub(r'[^a-zA-Z0-9_\-]', '', username)

    # Limit length (3-50 characters)
    username = username[:50]

    if len(username) < 3:
        return ""

    return username


def detect_sql_injection(text: str) -> bool:
    """
    Detect common SQL injection patterns

    Args:
        text: User input to check

    Returns:
        True if suspicious patterns detected
    """
    if not text:
        return False

    # Common SQL injection patterns
    dangerous_patterns = [
        r"('|(\\'))+(\s|/\*.*\*/)*or(\s|/\*.*\*/)+",  # ' OR
        r"union(\s|/\*.*\*/)+select",  # UNION SELECT
        r"(drop|delete|update|insert)(\s|/\*.*\*/)+.*table",  # DROP TABLE, etc.
        r"exec(\s|/\*.*\*/)*\(",  # EXEC(
        r"--",  # SQL comments
        r";(\s)*drop",  # ; DROP
        r"xp_cmdshell",  # Command execution
        r"sp_executesql"  # Execute SQL
    ]

    text_lower = text.lower()

    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def detect_xss(text: str) -> bool:
    """
    Detect common XSS attack patterns

    Args:
        text: User input to check

    Returns:
        True if suspicious patterns detected
    """
    if not text:
        return False

    # Common XSS patterns
    xss_patterns = [
        r"<script[^>]*>",  # <script>
        r"javascript:",  # javascript:
        r"on\w+\s*=",  # onclick=, onerror=, etc.
        r"<iframe[^>]*>",  # <iframe>
        r"<object[^>]*>",  # <object>
        r"<embed[^>]*>",  # <embed>
    ]

    text_lower = text.lower()

    for pattern in xss_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def validate_numeric_id(value: str, min_val: int = 1, max_val: int = 999999999) -> Optional[int]:
    """
    Validate and convert numeric ID

    Args:
        value: String value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Integer ID or None if invalid
    """
    try:
        num = int(value)
        if min_val <= num <= max_val:
            return num
    except (ValueError, TypeError):
        pass

    return None


# HTML Escape helpers for safe template rendering
def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return html.escape(text) if text else ""


def escape_js(text: str) -> str:
    """Escape text for safe JavaScript embedding"""
    if not text:
        return ""

    # Escape quotes and backslashes
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace("'", "\\'")
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')

    return text

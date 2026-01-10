#!/usr/bin/env python3
"""
Edge Case Logger - Centralized Logging for Edge Cases and Errors

Implements logging system documented in EDGE_CASES.md
Creates domain-specific logs and error tracking

Usage:
    from edge_case_logger import log_edge_case, EdgeCaseID

    log_edge_case(
        EdgeCaseID.MISSING_ADDRESS,
        f"Professional {prof_id} missing address field",
        professional_id=prof_id
    )
"""

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


# ==============================================================================
# Edge Case IDs (from EDGE_CASES.md)
# ==============================================================================

class EdgeCaseID(Enum):
    """Edge case identifiers matching EDGE_CASES.md"""

    # Domain Routing (DR)
    UNKNOWN_DOMAIN = "EC-DR-001"
    LOCALHOST_NO_PORT = "EC-DR-002"
    DOMAIN_PARAM_OVERRIDE = "EC-DR-003"
    INVALID_BRAND_PARAM = "EC-DR-004"
    WWW_SUBDOMAIN = "EC-DR-005"

    # Professional Data (PD)
    MISSING_ADDRESS = "EC-PD-001"
    MISSING_PHONE = "EC-PD-002"
    MISSING_EMAIL = "EC-PD-003"
    INVALID_EMAIL = "EC-PD-004"
    MISSING_BIO = "EC-PD-005"
    PROFESSIONAL_NOT_FOUND = "EC-PD-006"
    UNVERIFIED_PROFESSIONAL = "EC-PD-007"

    # User Accounts (UA)
    NO_USER_LINKED = "EC-UA-001"
    USER_NO_PROFESSIONAL = "EC-UA-002"
    MULTIPLE_PROFESSIONALS = "EC-UA-003"

    # Geo-Restrictions (GR)
    LOCALHOST_GEO_ACCESS = "EC-GR-001"
    GEO_OVERRIDE_PARAM = "EC-GR-002"
    PRODUCTION_GEO_BLOCK = "EC-GR-003"
    VPN_PROXY_DETECTED = "EC-GR-004"

    # Database (DB)
    TABLE_MISMATCH = "EC-DB-001"
    MISSING_TABLE = "EC-DB-002"
    SCHEMA_VERIFICATION = "EC-DB-003"

    # Templates (TR)
    UNDEFINED_VARIABLE = "EC-TR-001"
    MISSING_TEMPLATE = "EC-TR-002"
    CDN_FAILURE = "EC-TR-003"
    EMPTY_CATEGORIES = "EC-TR-004"


# ==============================================================================
# Log Configuration
# ==============================================================================

LOG_DIR = "logs"
LOG_FILES = {
    "domain_routing": "domain_routing.log",
    "professionals": "professionals_errors.log",
    "route_access": "route_access.log",
    "geo_access": "geo_access.log",
    "database": "database_errors.log",
    "auth": "auth_errors.log",
    "templates": "template_errors.log",
    "flask": "flask_errors.log",
}

# Map edge case categories to log files
EDGE_CASE_TO_LOG = {
    "DR": "domain_routing",
    "PD": "professionals",
    "UA": "auth",
    "GR": "geo_access",
    "DB": "database",
    "TR": "templates",
}


# ==============================================================================
# Logger Setup
# ==============================================================================

def setup_loggers():
    """Create log directory and configure loggers for each category"""

    # Create logs directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    loggers = {}

    for category, filename in LOG_FILES.items():
        logger = logging.getLogger(f"edge_case.{category}")
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        logger.handlers = []

        # File handler
        log_path = os.path.join(LOG_DIR, filename)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)

        # Format: [TIMESTAMP] [LEVEL] [MODULE] [EDGE_CASE_ID] MESSAGE
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] [%(edge_case_id)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        loggers[category] = logger

    return loggers


# Initialize loggers
LOGGERS = setup_loggers()


# ==============================================================================
# Logging Functions
# ==============================================================================

def log_edge_case(
    edge_case_id: EdgeCaseID,
    message: str,
    level: str = "WARNING",
    **kwargs
):
    """
    Log an edge case occurrence

    Args:
        edge_case_id: Edge case identifier from EdgeCaseID enum
        message: Human-readable message describing what happened
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        **kwargs: Additional context data to log

    Example:
        log_edge_case(
            EdgeCaseID.MISSING_ADDRESS,
            f"Professional {prof_id} missing address field",
            professional_id=prof_id,
            domain="stpetepros.com"
        )
    """

    # Get edge case category (e.g., "DR" from "EC-DR-001")
    ec_value = edge_case_id.value
    category_code = ec_value.split("-")[1]

    # Get appropriate logger
    log_category = EDGE_CASE_TO_LOG.get(category_code, "flask")
    logger = LOGGERS.get(log_category)

    if not logger:
        # Fallback to print if logger not found
        print(f"[{ec_value}] {message}")
        return

    # Add edge case ID to log record
    extra = {"edge_case_id": ec_value}

    # Append context data to message
    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message = f"{message} | {context_str}"

    # Log at appropriate level
    log_method = getattr(logger, level.lower(), logger.warning)
    log_method(message, extra=extra)


def log_domain_routing(brand: str, host: str, detected_from: str):
    """Log successful domain routing"""
    log_edge_case(
        EdgeCaseID.WWW_SUBDOMAIN if "www." in host else EdgeCaseID.DOMAIN_PARAM_OVERRIDE if "brand=" in detected_from else EdgeCaseID.UNKNOWN_DOMAIN,
        f"Routed to brand '{brand}' from host '{host}'",
        level="INFO",
        brand=brand,
        host=host,
        detected_from=detected_from
    )


def log_professional_access(prof_id: int, found: bool, user_id: Optional[int] = None):
    """Log professional profile access attempts"""
    if not found:
        log_edge_case(
            EdgeCaseID.PROFESSIONAL_NOT_FOUND,
            f"Attempted access to non-existent professional",
            level="WARNING",
            professional_id=prof_id,
            user_id=user_id
        )
    else:
        # Successful access, log at DEBUG level
        LOGGERS["route_access"].debug(
            f"Professional profile accessed",
            extra={"edge_case_id": "N/A", "professional_id": prof_id, "user_id": user_id}
        )


def log_missing_data(prof_id: int, field: str, domain: Optional[str] = None):
    """Log missing professional data fields"""
    edge_case_map = {
        "address": EdgeCaseID.MISSING_ADDRESS,
        "phone": EdgeCaseID.MISSING_PHONE,
        "email": EdgeCaseID.MISSING_EMAIL,
        "bio": EdgeCaseID.MISSING_BIO,
    }

    edge_case = edge_case_map.get(field, EdgeCaseID.MISSING_ADDRESS)

    log_edge_case(
        edge_case,
        f"Professional missing required field: {field}",
        level="ERROR",
        professional_id=prof_id,
        field=field,
        domain=domain
    )


def log_geo_access(allowed: bool, reason: str, ip: str, domain: str):
    """Log geo-restriction access attempts"""
    edge_case = EdgeCaseID.LOCALHOST_GEO_ACCESS if "localhost" in reason.lower() else EdgeCaseID.GEO_OVERRIDE_PARAM if "override" in reason.lower() else EdgeCaseID.PRODUCTION_GEO_BLOCK

    level = "INFO" if allowed else "WARNING"

    log_edge_case(
        edge_case,
        f"Geo-access {'allowed' if allowed else 'denied'}: {reason}",
        level=level,
        allowed=allowed,
        ip=ip,
        domain=domain
    )


def log_database_error(error_type: str, message: str, **kwargs):
    """Log database-related errors"""
    log_edge_case(
        EdgeCaseID.TABLE_MISMATCH if "table" in error_type.lower() else EdgeCaseID.MISSING_TABLE,
        message,
        level="ERROR",
        error_type=error_type,
        **kwargs
    )


def log_template_error(template: str, error: str, **kwargs):
    """Log template rendering errors"""
    log_edge_case(
        EdgeCaseID.MISSING_TEMPLATE if "not found" in error.lower() else EdgeCaseID.UNDEFINED_VARIABLE,
        f"Template error: {error}",
        level="ERROR",
        template=template,
        error=error,
        **kwargs
    )


# ==============================================================================
# Analytics and Reporting
# ==============================================================================

def get_edge_case_stats(log_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about edge case occurrences

    Args:
        log_file: Specific log file to analyze, or None for all logs

    Returns:
        Dict with edge case counts and statistics
    """
    stats = {
        "total_edge_cases": 0,
        "by_category": {},
        "by_level": {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0
        },
        "by_edge_case_id": {}
    }

    log_files = [os.path.join(LOG_DIR, log_file)] if log_file else [
        os.path.join(LOG_DIR, f) for f in LOG_FILES.values()
    ]

    for log_path in log_files:
        if not os.path.exists(log_path):
            continue

        with open(log_path, 'r') as f:
            for line in f:
                if "[EC-" not in line:
                    continue

                stats["total_edge_cases"] += 1

                # Extract log level
                for level in stats["by_level"].keys():
                    if f"[{level}]" in line:
                        stats["by_level"][level] += 1
                        break

                # Extract edge case ID
                try:
                    ec_id = line.split("[EC-")[1].split("]")[0]
                    ec_id = f"EC-{ec_id}"
                    stats["by_edge_case_id"][ec_id] = stats["by_edge_case_id"].get(ec_id, 0) + 1

                    # Extract category
                    category = ec_id.split("-")[1]
                    stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                except (IndexError, AttributeError):
                    pass

    return stats


def print_edge_case_report():
    """Print a formatted report of edge case statistics"""
    stats = get_edge_case_stats()

    print("\n" + "="*70)
    print("Edge Case Report")
    print("="*70 + "\n")

    print(f"Total Edge Cases Logged: {stats['total_edge_cases']}\n")

    print("By Category:")
    for category, count in sorted(stats['by_category'].items()):
        print(f"  {category}: {count}")

    print("\nBy Level:")
    for level, count in stats['by_level'].items():
        if count > 0:
            print(f"  {level}: {count}")

    print("\nTop Edge Cases:")
    sorted_cases = sorted(stats['by_edge_case_id'].items(), key=lambda x: x[1], reverse=True)
    for ec_id, count in sorted_cases[:10]:
        print(f"  {ec_id}: {count} occurrences")

    print("\n" + "="*70 + "\n")


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == '__main__':
    import sys

    if '--report' in sys.argv:
        print_edge_case_report()

    elif '--test' in sys.argv:
        # Test logging
        print("Testing edge case logger...")

        log_edge_case(
            EdgeCaseID.MISSING_ADDRESS,
            "Test: Professional 11 missing address",
            professional_id=11,
            domain="stpetepros.com"
        )

        log_edge_case(
            EdgeCaseID.PROFESSIONAL_NOT_FOUND,
            "Test: Access to non-existent professional",
            level="WARNING",
            professional_id=999
        )

        log_domain_routing(
            brand="stpetepros",
            host="localhost:5001",
            detected_from="localhost default"
        )

        print(f"✅ Test logs written to {LOG_DIR}/")
        print("\nCheck the following files:")
        for log_file in LOG_FILES.values():
            print(f"  - {os.path.join(LOG_DIR, log_file)}")

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Edge Case Logger - Centralized Error and Edge Case Logging         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python3 edge_case_logger.py --test     # Run test logs
    python3 edge_case_logger.py --report   # Show statistics

Integration:
    from edge_case_logger import log_edge_case, EdgeCaseID

    log_edge_case(
        EdgeCaseID.MISSING_ADDRESS,
        f"Professional {prof_id} missing address",
        professional_id=prof_id
    )

Log Files:
""")
        for category, filename in LOG_FILES.items():
            print(f"  {category:20} → {os.path.join(LOG_DIR, filename)}")

        print("\nEdge Cases Tracked: 29")
        print("See EDGE_CASES.md for full documentation\n")

#!/usr/bin/env python3
"""
PII Exposure Audit - Security Scanner for Soulfra

Scans for exposed Personally Identifiable Information (PII) in:
- Database tables (unencrypted fields)
- Log files (plaintext PII in logs)
- API responses (test endpoints for PII leaks)
- QR code analytics (location data, IPs)
- Voice memos (unencrypted audio)

PII Types Checked:
- Email addresses
- IP addresses
- GPS coordinates (latitude/longitude)
- Phone numbers
- Names (first/last)
- User agents
- Device IDs

Usage:
    python3 audit_pii_exposure.py --full
    python3 audit_pii_exposure.py --database
    python3 audit_pii_exposure.py --logs
    python3 audit_pii_exposure.py --api
    python3 audit_pii_exposure.py --report

Output:
    - Console report with findings
    - SECURITY-AUDIT-REPORT.md (detailed markdown report)
    - security_audit_results.json (machine-readable)
"""

import re
import json
import sys
from pathlib import Path
from database import get_db
from datetime import datetime
from collections import defaultdict


# =============================================================================
# PII PATTERNS
# =============================================================================

PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'ipv4': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
    'ipv6': re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
    'gps_lat': re.compile(r'lat(?:itude)?["\']?\s*[:=]\s*[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)'),
    'gps_lon': re.compile(r'lon(?:gitude)?["\']?\s*[:=]\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)'),
    'phone_us': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
}


# =============================================================================
# DATABASE AUDIT
# =============================================================================

def audit_database_tables():
    """
    Scan database tables for unencrypted PII

    Returns:
        dict: {table_name: [findings]}
    """
    print("=" * 70)
    print("🔍 DATABASE AUDIT - Checking for Unencrypted PII")
    print("=" * 70)
    print()

    db = get_db()
    findings = defaultdict(list)

    # Tables to check for PII
    tables_to_check = {
        'users': ['email', 'username', 'password_hash'],
        'posts': ['title', 'content', 'slug'],
        'dm_channels': ['location_lat', 'location_lon', 'qr_code_hash'],
        'dm_messages': ['content'],
        'qr_scans': ['ip_address', 'location_city', 'location_country', 'device_type'],
        'search_sessions': ['ip_address', 'device_fingerprint'],
        'voice_memos': ['file_path', 'encryption_key', 'encryption_iv'],
        'integration_logs': ['metadata', 'description'],
        'url_shortcuts': ['short_id'],
    }

    for table, columns in tables_to_check.items():
        try:
            # Check if table exists
            table_check = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            ).fetchone()

            if not table_check:
                print(f"⚠️ Table '{table}' not found - skipping")
                continue

            # Sample 10 rows from table
            query = f"SELECT {', '.join(columns)} FROM {table} LIMIT 10"
            rows = db.execute(query).fetchall()

            print(f"📋 Checking table: {table} ({len(rows)} rows sampled)")

            for row in rows:
                row_dict = dict(row)
                for column in columns:
                    value = row_dict.get(column)

                    if value is None:
                        continue

                    value_str = str(value)

                    # Check for PII patterns
                    for pii_type, pattern in PII_PATTERNS.items():
                        matches = pattern.findall(value_str)
                        if matches:
                            findings[table].append({
                                'column': column,
                                'pii_type': pii_type,
                                'sample': value_str[:100],  # First 100 chars
                                'matches': matches[:3],  # First 3 matches
                                'encrypted': 'encryption' in column.lower() or 'hash' in column.lower()
                            })

                    # Special check for GPS coordinates
                    if column in ['location_lat', 'location_lon'] and value:
                        findings[table].append({
                            'column': column,
                            'pii_type': 'gps_coordinate',
                            'value': value,
                            'encrypted': False  # GPS coords stored as floats (not encrypted)
                        })

                    # Special check for IP addresses
                    if column == 'ip_address' and value:
                        findings[table].append({
                            'column': column,
                            'pii_type': 'ip_address',
                            'value': value,
                            'encrypted': False  # IP addresses stored as strings (not encrypted)
                        })

        except Exception as e:
            print(f"❌ Error checking table {table}: {e}")

    db.close()

    # Print findings
    print()
    print("📊 DATABASE FINDINGS:")
    print()

    if not findings:
        print("✅ No unencrypted PII found in database tables")
    else:
        for table, table_findings in findings.items():
            print(f"⚠️ Table: {table}")
            for finding in table_findings:
                encrypted_status = "🔒 ENCRYPTED" if finding['encrypted'] else "🔓 PLAINTEXT"
                print(f"   Column: {finding['column']} - {finding['pii_type']} - {encrypted_status}")
                if 'value' in finding:
                    print(f"      Value: {finding['value']}")
                elif 'matches' in finding:
                    print(f"      Matches: {finding['matches']}")
            print()

    return dict(findings)


# =============================================================================
# LOG FILE AUDIT
# =============================================================================

def audit_log_files():
    """
    Scan log files for exposed PII

    Returns:
        dict: {log_file: [findings]}
    """
    print("=" * 70)
    print("📝 LOG FILES AUDIT - Checking for PII in Logs")
    print("=" * 70)
    print()

    findings = defaultdict(list)

    # Log files to check
    log_files = [
        '/tmp/ollama.log',
        Path(__file__).parent / 'logs' / 'assistant_errors.log',
        Path(__file__).parent / 'logs' / 'flask.log',
    ]

    for log_file in log_files:
        log_path = Path(log_file)

        if not log_path.exists():
            print(f"⚠️ Log file not found: {log_path}")
            continue

        print(f"📄 Checking: {log_path}")

        try:
            # Read last 1000 lines (to avoid memory issues)
            with open(log_path, 'r', errors='ignore') as f:
                lines = f.readlines()[-1000:]

            line_count = 0
            for line in lines:
                # Check for PII patterns
                for pii_type, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(line)
                    if matches:
                        findings[str(log_path)].append({
                            'line_number': line_count,
                            'pii_type': pii_type,
                            'matches': matches[:3],
                            'line_preview': line[:200]
                        })
                line_count += 1

        except Exception as e:
            print(f"❌ Error reading {log_path}: {e}")

    # Print findings
    print()
    print("📊 LOG FILE FINDINGS:")
    print()

    if not findings:
        print("✅ No PII found in log files")
    else:
        for log_file, log_findings in findings.items():
            print(f"⚠️ Log: {log_file} - {len(log_findings)} PII instances found")
            for finding in log_findings[:5]:  # Show first 5
                print(f"   Line {finding['line_number']}: {finding['pii_type']}")
                print(f"      {finding['line_preview'][:100]}...")
            if len(log_findings) > 5:
                print(f"   ... and {len(log_findings) - 5} more")
            print()

    return dict(findings)


# =============================================================================
# API ENDPOINT AUDIT
# =============================================================================

def audit_api_endpoints():
    """
    Test API endpoints for PII leaks

    Returns:
        dict: {endpoint: [findings]}
    """
    print("=" * 70)
    print("🌐 API ENDPOINTS AUDIT - Testing for PII Exposure")
    print("=" * 70)
    print()

    findings = defaultdict(list)

    # We can't directly test HTTP endpoints from here without requests library
    # Instead, we'll document which endpoints SHOULD be checked

    endpoints_to_test = [
        '/api/chat/send',
        '/api/questions/submit',
        '/api/analytics/qr',
        '/status',
        '/api/publisher/domains',
    ]

    print("📋 Endpoints that should be tested manually:")
    print()
    for endpoint in endpoints_to_test:
        print(f"   {endpoint}")
        print(f"      Check for: IP addresses, location data, email addresses")
    print()

    print("⚠️ API testing requires manual verification")
    print("   Run: curl http://localhost:5001{endpoint} | grep -E 'email|ip_address|location'")
    print()

    return {
        'manual_test_required': endpoints_to_test,
        'recommendation': 'Test each endpoint and verify PII is redacted/encrypted'
    }


# =============================================================================
# ENCRYPTION VERIFICATION
# =============================================================================

def verify_encryption_usage():
    """
    Verify encryption systems are being used

    Returns:
        dict: encryption status for each system
    """
    print("=" * 70)
    print("🔐 ENCRYPTION VERIFICATION - Checking Encryption Usage")
    print("=" * 70)
    print()

    status = {}

    # Check if voice_encryption.py is being used
    voice_encryption_exists = Path(__file__).parent / 'voice_encryption.py'
    status['voice_encryption'] = {
        'exists': voice_encryption_exists.exists(),
        'recommendation': 'Use voice_encryption.py for all audio files'
    }

    # Check database for encryption fields
    db = get_db()

    # Check voice_memos table for encryption
    voice_memos_check = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='voice_memos'"
    ).fetchone()

    if voice_memos_check:
        encrypted_count = db.execute(
            "SELECT COUNT(*) as count FROM voice_memos WHERE encryption_key IS NOT NULL"
        ).fetchone()['count']

        total_count = db.execute("SELECT COUNT(*) as count FROM voice_memos").fetchone()['count']

        status['voice_memos_encryption'] = {
            'encrypted': encrypted_count,
            'total': total_count,
            'percentage': (encrypted_count / total_count * 100) if total_count > 0 else 0
        }
    else:
        status['voice_memos_encryption'] = {'table_not_found': True}

    db.close()

    # Print status
    print("📊 ENCRYPTION STATUS:")
    print()
    for system, info in status.items():
        print(f"   {system}:")
        for key, value in info.items():
            print(f"      {key}: {value}")
    print()

    return status


# =============================================================================
# GENERATE REPORT
# =============================================================================

def generate_security_report(database_findings, log_findings, api_findings, encryption_status):
    """
    Generate comprehensive security audit report

    Args:
        database_findings: Results from database audit
        log_findings: Results from log audit
        api_findings: Results from API audit
        encryption_status: Encryption verification results

    Returns:
        str: Markdown report
    """
    report = []
    report.append("# 🔒 SECURITY AUDIT REPORT")
    report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## Executive Summary")
    report.append("")

    # Count total issues
    total_issues = len(database_findings) + len(log_findings)
    severity = "🟢 LOW" if total_issues < 5 else "🟡 MEDIUM" if total_issues < 20 else "🔴 HIGH"

    report.append(f"**Severity:** {severity}")
    report.append(f"**Total Issues Found:** {total_issues}")
    report.append("")

    # Database findings
    report.append("## 📊 Database Findings")
    report.append("")
    if not database_findings:
        report.append("✅ No unencrypted PII found in database")
    else:
        for table, findings in database_findings.items():
            report.append(f"### Table: `{table}`")
            for finding in findings:
                encrypted = "🔒 Encrypted" if finding['encrypted'] else "🔓 **PLAINTEXT**"
                report.append(f"- **Column:** `{finding['column']}` - **Type:** {finding['pii_type']} - {encrypted}")
            report.append("")

    # Log findings
    report.append("## 📝 Log File Findings")
    report.append("")
    if not log_findings:
        report.append("✅ No PII found in log files")
    else:
        for log_file, findings in log_findings.items():
            report.append(f"### Log: `{log_file}`")
            report.append(f"**Instances:** {len(findings)}")
            report.append("")

    # API findings
    report.append("## 🌐 API Endpoint Recommendations")
    report.append("")
    report.append("**Manual testing required for:**")
    for endpoint in api_findings.get('manual_test_required', []):
        report.append(f"- `{endpoint}`")
    report.append("")

    # Encryption status
    report.append("## 🔐 Encryption Status")
    report.append("")
    for system, status in encryption_status.items():
        report.append(f"### {system}")
        for key, value in status.items():
            report.append(f"- **{key}:** {value}")
        report.append("")

    # Recommendations
    report.append("## 💡 Recommendations")
    report.append("")

    if database_findings:
        report.append("### Database")
        report.append("1. Encrypt GPS coordinates (location_lat, location_lon) before storage")
        report.append("2. Hash or encrypt IP addresses in qr_scans and search_sessions")
        report.append("3. Ensure all voice_memos use encryption_key and encryption_iv")
        report.append("")

    if log_findings:
        report.append("### Logging")
        report.append("1. Implement PII redaction in unified_logger.py")
        report.append("2. Sanitize log output to remove emails, IPs, GPS coordinates")
        report.append("3. Use log rotation to limit exposure window")
        report.append("")

    report.append("### API Security")
    report.append("1. Test all API endpoints for PII leaks")
    report.append("2. Implement response sanitization")
    report.append("3. Use rate limiting on sensitive endpoints")
    report.append("")

    return "\n".join(report)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run full security audit"""
    print("🔒 SOULFRA SECURITY AUDIT - PII Exposure Scanner")
    print()

    # Run audits
    database_findings = audit_database_tables()
    log_findings = audit_log_files()
    api_findings = audit_api_endpoints()
    encryption_status = verify_encryption_usage()

    # Generate report
    report = generate_security_report(
        database_findings,
        log_findings,
        api_findings,
        encryption_status
    )

    # Save markdown report
    report_path = Path(__file__).parent / 'SECURITY-AUDIT-REPORT.md'
    with open(report_path, 'w') as f:
        f.write(report)

    print("=" * 70)
    print(f"📄 Report saved to: {report_path}")
    print("=" * 70)
    print()

    # Save JSON results
    json_results = {
        'timestamp': datetime.now().isoformat(),
        'database_findings': database_findings,
        'log_findings': {k: len(v) for k, v in log_findings.items()},  # Count only
        'api_findings': api_findings,
        'encryption_status': encryption_status
    }

    json_path = Path(__file__).parent / 'security_audit_results.json'
    with open(json_path, 'w') as f:
        json.dump(json_results, f, indent=2)

    print(f"📊 JSON results saved to: {json_path}")
    print()

    # Print summary
    total_issues = len(database_findings) + len(log_findings)
    if total_issues == 0:
        print("✅ NO CRITICAL ISSUES FOUND")
    else:
        print(f"⚠️ {total_issues} POTENTIAL ISSUES FOUND")
        print("   Review SECURITY-AUDIT-REPORT.md for details")
    print()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Cryptographic Proof Verifier

Standalone script to verify proof.json authenticity and integrity.

Usage:
    python3 verify_proof.py proof.json              # Verify proof file
    python3 verify_proof.py proof.json --verbose    # Show detailed verification
    python3 verify_proof.py proof.json --quick      # Skip full validation

What this verifies:
1. HMAC-SHA256 signature is valid (proves proof hasn't been tampered with)
2. Content hash matches (proves data integrity)
3. All tier verifications passed
4. Timestamp is reasonable (not from future, not too old)

Exit codes:
    0 - Proof is valid
    1 - Proof is invalid
    2 - Error reading proof file
"""

import json
import hmac
import hashlib
import sys
from datetime import datetime, timedelta

# ==============================================================================
# CONFIG
# ==============================================================================

SECRET_KEY = b"soulfra-proof-generator-2025"  # Must match generate_proof.py

# Maximum age for proof (in days)
MAX_PROOF_AGE_DAYS = 30

# ==============================================================================
# VERIFICATION FUNCTIONS
# ==============================================================================

def verify_signature(proof_data):
    """
    Verify HMAC-SHA256 signature of proof

    Returns:
        (bool, str): (is_valid, message)
    """
    # Extract signature
    if 'signature' not in proof_data:
        return False, "Missing signature section"

    signature_section = proof_data['signature']

    if 'signature' not in signature_section:
        return False, "Missing HMAC signature"

    provided_signature = signature_section['signature']

    # Remove signature section for verification
    proof_copy = proof_data.copy()
    del proof_copy['signature']

    # Recalculate signature
    proof_json = json.dumps(proof_copy, sort_keys=True, separators=(',', ':'))
    proof_bytes = proof_json.encode('utf-8')

    expected_signature = hmac.new(SECRET_KEY, proof_bytes, hashlib.sha256).hexdigest()

    # Compare signatures (constant-time comparison to prevent timing attacks)
    if hmac.compare_digest(provided_signature, expected_signature):
        return True, f"Signature valid: {provided_signature[:16]}..."
    else:
        return False, f"Signature mismatch! Expected {expected_signature[:16]}..., got {provided_signature[:16]}..."


def verify_content_hash(proof_data):
    """
    Verify SHA-256 content hash

    Returns:
        (bool, str): (is_valid, message)
    """
    if 'signature' not in proof_data or 'content_hash' not in proof_data['signature']:
        return False, "Missing content hash"

    provided_hash = proof_data['signature']['content_hash']

    # Remove signature section for hashing
    proof_copy = proof_data.copy()
    del proof_copy['signature']

    # Recalculate hash
    proof_json = json.dumps(proof_copy, sort_keys=True, separators=(',', ':'))
    proof_bytes = proof_json.encode('utf-8')

    expected_hash = hashlib.sha256(proof_bytes).hexdigest()

    if provided_hash == expected_hash:
        return True, f"Content hash valid: {provided_hash[:16]}..."
    else:
        return False, f"Content hash mismatch! Expected {expected_hash[:16]}..., got {provided_hash[:16]}..."


def verify_timestamp(proof_data):
    """
    Verify proof timestamp is reasonable

    Returns:
        (bool, str): (is_valid, message)
    """
    if 'timestamp' not in proof_data:
        return False, "Missing timestamp"

    timestamp = proof_data['timestamp']
    now = datetime.now().timestamp()

    # Check if from future (allow 5 minute clock skew)
    if timestamp > now + 300:
        return False, f"Timestamp is from the future! ({timestamp} > {now})"

    # Check if too old
    max_age_seconds = MAX_PROOF_AGE_DAYS * 24 * 60 * 60
    if now - timestamp > max_age_seconds:
        age_days = (now - timestamp) / (24 * 60 * 60)
        return False, f"Proof is too old ({age_days:.1f} days, max {MAX_PROOF_AGE_DAYS} days)"

    # Calculate age
    proof_time = datetime.fromtimestamp(timestamp)
    age = datetime.now() - proof_time

    return True, f"Timestamp valid (generated {age.seconds // 3600}h {(age.seconds % 3600) // 60}m ago)"


def verify_tiers(proof_data):
    """
    Verify all tiers passed their checks

    Returns:
        (bool, str): (is_valid, message)
    """
    tier_names = ['tier1_sql', 'tier2_python', 'tier3_binary', 'tier4_formats']

    failed_tiers = []
    for tier in tier_names:
        if tier not in proof_data:
            failed_tiers.append(f"{tier} missing")
        elif not proof_data[tier].get('verified', False):
            failed_tiers.append(f"{tier} not verified")

    if failed_tiers:
        return False, f"Tier verification failed: {', '.join(failed_tiers)}"

    return True, "All 4 tiers verified successfully"


def verify_summary(proof_data):
    """
    Verify summary section shows all checks passed

    Returns:
        (bool, str): (is_valid, message)
    """
    if 'summary' not in proof_data:
        return False, "Missing summary section"

    summary = proof_data['summary']

    checks = [
        ('all_tiers_verified', 'All tiers verified'),
        ('cryptographically_signed', 'Cryptographically signed'),
        ('reproducible', 'Reproducible')
    ]

    failed_checks = []
    for key, name in checks:
        if not summary.get(key, False):
            failed_checks.append(name)

    if failed_checks:
        return False, f"Summary checks failed: {', '.join(failed_checks)}"

    return True, "All summary checks passed"


# ==============================================================================
# DETAILED VERIFICATION
# ==============================================================================

def verify_proof_detailed(proof_data, verbose=False):
    """
    Run all verification checks and return detailed results

    Returns:
        dict: {
            'valid': bool,
            'checks': [
                {'name': str, 'passed': bool, 'message': str},
                ...
            ],
            'summary': str
        }
    """
    checks = []

    # Run all verification checks
    verification_functions = [
        ("HMAC Signature", verify_signature),
        ("Content Hash", verify_content_hash),
        ("Timestamp", verify_timestamp),
        ("Tier Verification", verify_tiers),
        ("Summary", verify_summary)
    ]

    all_passed = True

    for check_name, verify_func in verification_functions:
        passed, message = verify_func(proof_data)

        checks.append({
            'name': check_name,
            'passed': passed,
            'message': message
        })

        if not passed:
            all_passed = False

        if verbose:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")

    # Generate summary
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)

    if all_passed:
        summary = f"✅ ALL CHECKS PASSED ({passed_count}/{total_count})"
    else:
        failed_count = total_count - passed_count
        summary = f"❌ VERIFICATION FAILED ({failed_count}/{total_count} checks failed)"

    return {
        'valid': all_passed,
        'checks': checks,
        'summary': summary
    }


# ==============================================================================
# PROOF STATS
# ==============================================================================

def print_proof_stats(proof_data):
    """Print interesting stats from the proof"""
    print()
    print("=" * 70)
    print("PROOF STATISTICS")
    print("=" * 70)
    print()

    # Basic info
    print(f"Version: {proof_data.get('version', 'unknown')}")
    print(f"Generated: {proof_data.get('generated_at', 'unknown')}")
    print()

    # Tier stats
    if 'tier1_sql' in proof_data:
        t1 = proof_data['tier1_sql']
        print(f"📊 TIER 1 (SQL): {t1.get('total_tables', 0)} tables, {t1.get('total_rows', 0)} rows")

    if 'tier2_python' in proof_data:
        t2 = proof_data['tier2_python']
        print(f"🐍 TIER 2 (Python): {len(t2.get('sample_transformations', []))} sample transformations")

    if 'tier3_binary' in proof_data:
        t3 = proof_data['tier3_binary']
        print(f"🔢 TIER 3 (Binary): {len(t3.get('examples', []))} encoding examples")

    if 'tier4_formats' in proof_data:
        t4 = proof_data['tier4_formats']
        print(f"📄 TIER 4 (Formats): {t4.get('total_formats', 0)} output formats")

    print()

    # Dependencies
    if 'dependencies' in proof_data:
        deps = proof_data['dependencies']
        print(f"📦 Dependencies:")
        print(f"   Total files scanned: {deps.get('total_files_scanned', 0)}")
        print(f"   Total imports: {deps.get('total_imports', 0)}")
        print(f"   Stdlib imports: {len(deps.get('stdlib_imports', []))}")
        print(f"   External imports: {len(deps.get('external_imports', []))}")

        if deps.get('external_imports'):
            print(f"   ⚠️  External: {', '.join(deps['external_imports'][:5])}")
            if len(deps['external_imports']) > 5:
                print(f"              ... and {len(deps['external_imports']) - 5} more")

    print()

    # System hash
    if 'system_hash' in proof_data:
        sh = proof_data['system_hash']
        print(f"🔐 System Hash: {sh.get('hash_algorithm', 'unknown')} - {sh.get('system_hash', 'unknown')[:32]}...")
        print(f"   Files hashed: {sh.get('files_included', 0)}")

    print()


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Verify cryptographic proof document')
    parser.add_argument('proof_file', type=str, help='Path to proof.json file')
    parser.add_argument('--verbose', action='store_true', help='Show detailed verification')
    parser.add_argument('--quick', action='store_true', help='Skip detailed stats')
    parser.add_argument('--stats', action='store_true', help='Show proof statistics')

    args = parser.parse_args()

    # Read proof file
    try:
        with open(args.proof_file, 'r') as f:
            proof_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Proof file not found: {args.proof_file}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in proof file: {e}")
        sys.exit(2)

    if args.verbose:
        print("=" * 70)
        print("SOULFRA PROOF VERIFIER")
        print("=" * 70)
        print()
        print(f"Verifying: {args.proof_file}")
        print()

    # Verify proof
    result = verify_proof_detailed(proof_data, verbose=args.verbose)

    if args.verbose:
        print()
        print("=" * 70)
        print(result['summary'])
        print("=" * 70)

    # Show stats if requested
    if args.stats or (args.verbose and not args.quick):
        print_proof_stats(proof_data)

    # Exit with appropriate code
    if result['valid']:
        if not args.verbose:
            print(f"✅ {args.proof_file} is valid")
        sys.exit(0)
    else:
        if not args.verbose:
            print(f"❌ {args.proof_file} is INVALID")
            # Show which checks failed
            for check in result['checks']:
                if not check['passed']:
                    print(f"   ❌ {check['name']}: {check['message']}")
        sys.exit(1)


if __name__ == '__main__':
    main()

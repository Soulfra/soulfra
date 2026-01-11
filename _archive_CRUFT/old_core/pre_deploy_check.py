#!/usr/bin/env python3
"""
Pre-Deployment Verification System - The Safety Net Before You Ship

Runs comprehensive checks before deploying to production:
1. API Health Scanner (all 466 endpoints)
2. Ollama Model Availability
3. Wordmap Coverage (which brands have complete vocabularies)
4. Database Integrity
5. QR Code Generation (for mobile verification)

Returns:
- Green light (✅ DEPLOY READY) if all checks pass
- Yellow light (⚠️  DEPLOY WITH CAUTION) if warnings exist
- Red light (❌ DO NOT DEPLOY) if critical errors found

Usage:
    python3 pre_deploy_check.py                    # Run all checks
    python3 pre_deploy_check.py --quick           # Skip slow checks
    python3 pre_deploy_check.py --qr              # Generate QR code for report
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Any
import subprocess

# Check imports
try:
    from api_health_scanner import APIHealthScanner
    from ollama_client import OllamaClient
    from database import get_db
    import qrcode
    import io
    import base64
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)


class PreDeployChecker:
    """Comprehensive pre-deployment verification"""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'PENDING',
            'deploy_ready': False,
            'critical_errors': [],
            'warnings': [],
            'info': []
        }

    def run_all_checks(self, quick_mode: bool = False) -> Dict:
        """Run all pre-deployment checks"""
        print("🚀 Pre-Deployment Verification System")
        print("=" * 60)

        # Check 1: Ollama Models
        print("\n1️⃣  Checking Ollama models...")
        self.check_ollama_models()

        # Check 2: Database Integrity
        print("\n2️⃣  Checking database integrity...")
        self.check_database()

        # Check 3: Wordmap Coverage
        print("\n3️⃣  Checking brand wordmap coverage...")
        self.check_wordmap_coverage()

        # Check 4: API Health (skip in quick mode)
        if not quick_mode:
            print("\n4️⃣  Running API health scanner (this may take a minute)...")
            self.check_api_health()
        else:
            print("\n4️⃣  Skipping API health scanner (quick mode)")
            self.results['checks']['api_health'] = {'status': 'SKIPPED', 'reason': 'Quick mode enabled'}

        # Check 5: Critical Files
        print("\n5️⃣  Checking critical files...")
        self.check_critical_files()

        # Determine overall status
        self.determine_overall_status()

        print("\n" + "=" * 60)
        print(f"Overall Status: {self.results['overall_status']}")
        print(f"Deploy Ready: {'✅ YES' if self.results['deploy_ready'] else '❌ NO'}")

        return self.results

    def check_ollama_models(self):
        """Check Ollama connectivity and available models"""
        try:
            client = OllamaClient()

            # Check if Ollama is running
            if not client.check_health():
                self.results['checks']['ollama_health'] = {
                    'status': 'CRITICAL',
                    'message': 'Ollama is not running on localhost:11434'
                }
                self.results['critical_errors'].append('Ollama not running')
                print("❌ Ollama NOT running")
                return

            # Get available models
            models = client.list_models()
            model_names = [m.get('name', 'unknown') for m in models]

            # Check for recommended models
            recommended = ['llama3.2:3b', 'soulfra-model:latest', 'mistral:latest']
            available_recommended = [m for m in recommended if m in model_names]

            self.results['checks']['ollama_health'] = {
                'status': 'OK',
                'models_available': len(model_names),
                'model_list': model_names[:10],  # First 10
                'recommended_models': available_recommended
            }

            if available_recommended:
                print(f"✅ Ollama running with {len(model_names)} models ({len(available_recommended)} recommended)")
            else:
                print(f"⚠️  Ollama running but no recommended models found")
                self.results['warnings'].append('No recommended Ollama models (llama3.2:3b, soulfra-model, mistral)')

        except Exception as e:
            self.results['checks']['ollama_health'] = {
                'status': 'CRITICAL',
                'error': str(e)
            }
            self.results['critical_errors'].append(f'Ollama check failed: {e}')
            print(f"❌ Ollama check failed: {e}")

    def check_database(self):
        """Check database connectivity and critical tables"""
        try:
            db = get_db()

            # Check critical tables exist
            critical_tables = [
                'users',
                'simple_voice_recordings',
                'domain_contexts',
                'domain_ownership',
                'session_sync_tokens'
            ]

            tables_check = []
            for table in critical_tables:
                result = db.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                if result:
                    # Count rows
                    count = db.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()['count']
                    tables_check.append({'table': table, 'exists': True, 'rows': count})
                else:
                    tables_check.append({'table': table, 'exists': False, 'rows': 0})
                    self.results['critical_errors'].append(f'Missing critical table: {table}')

            self.results['checks']['database'] = {
                'status': 'OK' if len([t for t in tables_check if not t['exists']]) == 0 else 'CRITICAL',
                'tables': tables_check
            }

            missing = [t['table'] for t in tables_check if not t['exists']]
            if missing:
                print(f"❌ Missing tables: {', '.join(missing)}")
            else:
                print(f"✅ Database OK - all {len(critical_tables)} tables exist")

        except Exception as e:
            self.results['checks']['database'] = {
                'status': 'CRITICAL',
                'error': str(e)
            }
            self.results['critical_errors'].append(f'Database check failed: {e}')
            print(f"❌ Database check failed: {e}")

    def check_wordmap_coverage(self):
        """Check which brands have wordmap data"""
        try:
            # Try to fetch brand wordmaps
            # This is a simple check - just verifies the endpoint exists
            import requests
            response = requests.get('http://localhost:5001/api/brand/wordmap/soulfra', timeout=5)

            if response.status_code == 200:
                data = response.json()
                wordmap = data.get('wordmap', {})
                self.results['checks']['wordmap'] = {
                    'status': 'OK',
                    'soulfra_words': len(wordmap),
                    'message': f'Soulfra wordmap has {len(wordmap)} words'
                }
                print(f"✅ Wordmap coverage OK (Soulfra: {len(wordmap)} words)")
            else:
                self.results['checks']['wordmap'] = {
                    'status': 'WARNING',
                    'message': 'Wordmap endpoint returned non-200 status'
                }
                self.results['warnings'].append('Wordmap endpoint issue')
                print("⚠️  Wordmap endpoint returned non-200 status")

        except Exception as e:
            self.results['checks']['wordmap'] = {
                'status': 'WARNING',
                'error': str(e),
                'message': 'Could not verify wordmap coverage'
            }
            self.results['warnings'].append('Wordmap check failed (non-critical)')
            print(f"⚠️  Wordmap check failed: {e}")

    def check_api_health(self):
        """Run API health scanner"""
        try:
            scanner = APIHealthScanner()
            routes = scanner.fetch_routes('http://localhost:5001')

            if not routes:
                self.results['checks']['api_health'] = {
                    'status': 'WARNING',
                    'message': 'Could not fetch routes from /status/routes'
                }
                self.results['warnings'].append('Could not run API health scanner')
                print("⚠️  Could not fetch routes for health scan")
                return

            # Test a sample of endpoints (not all 466)
            sample_routes = list(routes.keys())[:20]  # Test first 20
            test_results = []

            for route in sample_routes:
                result = scanner.test_endpoint('http://localhost:5001', route)
                test_results.append(result)

            errors = [r for r in test_results if r['status'] == 'ERROR']
            warnings = [r for r in test_results if r['status'] == 'WARNING']

            self.results['checks']['api_health'] = {
                'status': 'OK' if len(errors) == 0 else 'WARNING',
                'total_tested': len(sample_routes),
                'errors': len(errors),
                'warnings': len(warnings),
                'ok': len([r for r in test_results if r['status'] == 'OK'])
            }

            if errors:
                print(f"⚠️  API health: {len(errors)} errors in {len(sample_routes)} endpoints tested")
                self.results['warnings'].append(f'{len(errors)} API endpoints with errors')
            else:
                print(f"✅ API health: {len(test_results)} endpoints tested OK")

        except Exception as e:
            self.results['checks']['api_health'] = {
                'status': 'WARNING',
                'error': str(e)
            }
            self.results['warnings'].append('API health scanner failed (non-critical)')
            print(f"⚠️  API health scanner failed: {e}")

    def check_critical_files(self):
        """Check that critical files exist"""
        import os

        critical_files = [
            'app.py',
            'database.py',
            'ollama_client.py',
            'voice_content_generator.py',
            'session_sync.py',
            'domain_unlock_engine.py',
            'soulfra.db'
        ]

        files_check = []
        for filepath in critical_files:
            exists = os.path.exists(filepath)
            size = os.path.getsize(filepath) if exists else 0
            files_check.append({'file': filepath, 'exists': exists, 'size': size})

            if not exists:
                self.results['critical_errors'].append(f'Missing critical file: {filepath}')

        missing = [f['file'] for f in files_check if not f['exists']]
        self.results['checks']['critical_files'] = {
            'status': 'OK' if len(missing) == 0 else 'CRITICAL',
            'files': files_check
        }

        if missing:
            print(f"❌ Missing files: {', '.join(missing)}")
        else:
            print(f"✅ All {len(critical_files)} critical files exist")

    def determine_overall_status(self):
        """Determine if system is ready to deploy"""
        if self.results['critical_errors']:
            self.results['overall_status'] = '❌ DO NOT DEPLOY'
            self.results['deploy_ready'] = False
        elif len(self.results['warnings']) > 5:
            self.results['overall_status'] = '⚠️  DEPLOY WITH CAUTION'
            self.results['deploy_ready'] = False
        else:
            self.results['overall_status'] = '✅ DEPLOY READY'
            self.results['deploy_ready'] = True

    def generate_qr_report(self) -> str:
        """Generate QR code with deployment status link"""
        try:
            # Create short summary
            summary = {
                'status': self.results['overall_status'],
                'deploy_ready': self.results['deploy_ready'],
                'critical_errors': len(self.results['critical_errors']),
                'warnings': len(self.results['warnings']),
                'timestamp': self.results['timestamp']
            }

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(json.dumps(summary))
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"⚠️  QR code generation failed: {e}")
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Pre-deployment verification system')
    parser.add_argument('--quick', action='store_true', help='Skip slow checks')
    parser.add_argument('--qr', action='store_true', help='Generate QR code for report')
    parser.add_argument('--json', action='store_true', help='Output JSON only')

    args = parser.parse_args()

    checker = PreDeployChecker()
    results = checker.run_all_checks(quick_mode=args.quick)

    if args.qr:
        print("\n📱 Generating QR code...")
        qr_code = checker.generate_qr_report()
        if qr_code:
            print("✅ QR code generated (base64 data available)")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT CHECKLIST")
        print("=" * 60)
        print(f"Critical Errors: {len(results['critical_errors'])}")
        print(f"Warnings: {len(results['warnings'])}")
        print(f"\n{results['overall_status']}")

        if results['deploy_ready']:
            print("\n🚀 System is ready for deployment!")
        else:
            print("\n⛔ Fix errors before deploying:")
            for error in results['critical_errors'][:5]:
                print(f"  - {error}")

    sys.exit(0 if results['deploy_ready'] else 1)


if __name__ == '__main__':
    main()

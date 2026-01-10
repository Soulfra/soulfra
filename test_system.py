#!/usr/bin/env python3
"""
System Test Runner

Tests all the systems we just built:
1. System manifest
2. Domain context
3. Logging
4. QR search gate
5. Documentation browser

Usage:
    python3 test_system.py
    python3 test_system.py --verbose
"""

import sys
import os
from pathlib import Path
import urllib.request
import json

# Colors for terminal output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class SystemTester:
    """Test all Soulfra systems"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tests_passed = 0
        self.tests_failed = 0
        self.root_dir = Path(__file__).parent

    def print_header(self, text):
        """Print test section header"""
        print(f"\n{'='*60}")
        print(f"{BLUE}{text}{NC}")
        print(f"{'='*60}\n")

    def test(self, name, condition, details=""):
        """Run a test and print result"""
        if condition:
            print(f"{GREEN}✅ {name}{NC}")
            if details and self.verbose:
                print(f"   {details}")
            self.tests_passed += 1
            return True
        else:
            print(f"{RED}❌ {name}{NC}")
            if details:
                print(f"   {details}")
            self.tests_failed += 1
            return False

    def test_manifest(self):
        """Test system manifest generation"""
        self.print_header("1. Testing System Manifest")

        # Check if manifest files exist
        manifest_json = self.root_dir / 'manifest.json'
        manifest_plist = self.root_dir / 'soulfra.plist'

        self.test(
            "manifest.json exists",
            manifest_json.exists(),
            f"Path: {manifest_json}"
        )

        self.test(
            "soulfra.plist exists",
            manifest_plist.exists(),
            f"Path: {manifest_plist}"
        )

        # Check manifest content
        if manifest_json.exists():
            try:
                with open(manifest_json, 'r') as f:
                    manifest = json.load(f)

                self.test(
                    "Manifest has metadata",
                    'metadata' in manifest,
                    f"Generated: {manifest.get('metadata', {}).get('generated_at', 'Unknown')}"
                )

                route_count = len(manifest.get('routes', []))
                self.test(
                    "Routes catalogued (>100)",
                    route_count > 100,
                    f"Found {route_count} routes"
                )

                tool_count = len(manifest.get('tools', []))
                self.test(
                    "Tools catalogued (>50)",
                    tool_count > 50,
                    f"Found {tool_count} Python tools"
                )

                domain_count = len(manifest.get('domains', []))
                self.test(
                    "Domains catalogued",
                    domain_count >= 4,
                    f"Found {domain_count} domains"
                )

            except Exception as e:
                self.test(
                    "Manifest is valid JSON",
                    False,
                    f"Error: {e}"
                )

    def test_domain_context(self):
        """Test domain context system"""
        self.print_header("2. Testing Domain Context")

        try:
            from domain_context import DomainContextManager

            manager = DomainContextManager()

            self.test(
                "DomainContextManager loads",
                True,
                f"Loaded successfully"
            )

            domains = manager.get_all_domains()
            self.test(
                "Domains loaded (4 expected)",
                len(domains) == 4,
                f"Found: {', '.join(domains)}"
            )

            # Test context for howtocookathome.com
            context = manager.get_domain_context('howtocookathome.com')
            self.test(
                "howtocookathome.com context exists",
                context is not None,
                f"Tagline: {context.get('tagline', 'N/A')}" if context else ""
            )

            if context:
                self.test(
                    "Context has target audience",
                    context.get('target_audience') != '',
                    f"Target: {context.get('target_audience', 'N/A')}"
                )

            # Test Ollama context building
            ollama_context = manager.build_ollama_context('howtocookathome.com')
            self.test(
                "Ollama context generated",
                len(ollama_context) > 50,
                f"Length: {len(ollama_context)} chars"
            )

        except Exception as e:
            self.test(
                "Domain context system",
                False,
                f"Error: {e}"
            )

    def test_logging(self):
        """Test centralized logging system"""
        self.print_header("3. Testing Logging System")

        logs_dir = self.root_dir / 'logs'

        self.test(
            "logs/ directory exists",
            logs_dir.exists(),
            f"Path: {logs_dir}"
        )

        expected_logs = ['flask.log', 'qr-auth.log', 'search.log', 'ollama.log', 'errors.log']

        for log_file in expected_logs:
            log_path = logs_dir / log_file
            self.test(
                f"{log_file} exists",
                log_path.exists(),
                f"Size: {log_path.stat().st_size if log_path.exists() else 0} bytes"
            )

        # Test logger module
        try:
            from logger import get_logger

            test_logger = get_logger('test')
            self.test(
                "Logger module works",
                test_logger is not None,
                "get_logger() successful"
            )

        except Exception as e:
            self.test(
                "Logger module",
                False,
                f"Error: {e}"
            )

    def test_flask_endpoints(self):
        """Test Flask endpoints"""
        self.print_header("4. Testing Flask Endpoints")

        endpoints = [
            ('http://localhost:5001/', 'Homepage'),
            ('http://localhost:5001/admin/docs', 'Documentation Browser'),
            ('http://localhost:5001/admin/snippets', 'Code Snippets'),
            ('http://localhost:5001/qr-search-gate', 'QR Search Gate'),
            ('http://localhost:5001/login-qr', 'QR Login'),
        ]

        for url, name in endpoints:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as response:
                    status = response.status
                    self.test(
                        f"{name} endpoint",
                        status == 200,
                        f"Status: {status}"
                    )
            except Exception as e:
                self.test(
                    f"{name} endpoint",
                    False,
                    f"Error: {e}"
                )

    def test_documentation(self):
        """Test documentation system"""
        self.print_header("5. Testing Documentation System")

        # Check for key documentation files
        key_docs = [
            'START-HERE.md',
            'SYSTEM-SUMMARY.md',
            'SIMPLE-TEST-NOW.md',
            'WHAT-YOURE-RUNNING.md'
        ]

        for doc in key_docs:
            doc_path = self.root_dir / doc
            self.test(
                f"{doc} exists",
                doc_path.exists(),
                f"Size: {doc_path.stat().st_size if doc_path.exists() else 0} bytes"
            )

        # Count all markdown files
        md_files = list(self.root_dir.glob('*.md'))
        self.test(
            "Markdown docs (>50 expected)",
            len(md_files) > 50,
            f"Found {len(md_files)} docs"
        )

        # Check extract_snippets.py exists
        snippets_tool = self.root_dir / 'extract_snippets.py'
        self.test(
            "extract_snippets.py exists",
            snippets_tool.exists(),
            "Code snippet extractor ready"
        )

        # Check ollama_docs_qa.py exists
        qa_tool = self.root_dir / 'ollama_docs_qa.py'
        self.test(
            "ollama_docs_qa.py exists",
            qa_tool.exists(),
            "Documentation Q&A tool ready"
        )

    def test_git_repos(self):
        """Test git repositories"""
        self.print_header("6. Testing Git Repositories")

        output_dir = self.root_dir / 'output'

        if not output_dir.exists():
            self.test(
                "output/ directory exists",
                False,
                "No generated sites found"
            )
            return

        # Check main domains
        domains = ['soulfra', 'calriven', 'deathtodata', 'howtocookathome']

        for domain in domains:
            domain_dir = output_dir / domain
            git_dir = domain_dir / '.git'

            self.test(
                f"{domain} has git repo",
                git_dir.exists(),
                f"Path: {domain_dir}"
            )

    def test_database(self):
        """Test database"""
        self.print_header("7. Testing Database")

        db_file = self.root_dir / 'soulfra.db'

        self.test(
            "soulfra.db exists",
            db_file.exists(),
            f"Size: {db_file.stat().st_size if db_file.exists() else 0} bytes"
        )

        if db_file.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()

                # Get table count
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                self.test(
                    "Database has tables (>10 expected)",
                    len(tables) > 10,
                    f"Found {len(tables)} tables"
                )

                # Check for QR tables
                table_names = [t[0] for t in tables]
                self.test(
                    "QR auth tables exist",
                    'qr_auth_tokens' in table_names or 'qr_codes' in table_names,
                    "QR authentication ready"
                )

                self.test(
                    "Search tables exist",
                    'search_tokens' in table_names or 'search_sessions' in table_names,
                    "Search system ready"
                )

                conn.close()

            except Exception as e:
                self.test(
                    "Database readable",
                    False,
                    f"Error: {e}"
                )

    def run_all_tests(self):
        """Run all tests"""
        print(f"{BLUE}{'='*60}")
        print(f"🧪 SOULFRA SYSTEM TEST RUNNER")
        print(f"{'='*60}{NC}\n")

        self.test_manifest()
        self.test_domain_context()
        self.test_logging()
        self.test_flask_endpoints()
        self.test_documentation()
        self.test_git_repos()
        self.test_database()

        # Summary
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0

        print(f"\n{'='*60}")
        print(f"{BLUE}SUMMARY{NC}")
        print(f"{'='*60}\n")
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.tests_passed}{NC}")
        print(f"{RED}Failed: {self.tests_failed}{NC}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        if pass_rate >= 80:
            print(f"{GREEN}✅ System is healthy!{NC}\n")
            return 0
        elif pass_rate >= 60:
            print(f"{YELLOW}⚠️  Some issues found. Review failures above.{NC}\n")
            return 1
        else:
            print(f"{RED}❌ Critical issues found. System needs attention.{NC}\n")
            return 2


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test Soulfra systems")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    tester = SystemTester(verbose=args.verbose)
    exit_code = tester.run_all_tests()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

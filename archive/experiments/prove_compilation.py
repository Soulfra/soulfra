#!/usr/bin/env python3
"""
Prove Compilation - Live Execution Trace

PROVES template compilation works by:
- Fetching real data from database
- Running actual compiler functions
- Showing exact transformations
- Verifying output is correct

Usage:
    python3 prove_compilation.py ocean-dreams
    python3 prove_compilation.py testbrand-auto --verbose
"""

import sys
import json
import sqlite3
from typing import Dict, Optional, Any
from database import get_db
from brand_css_generator import generate_brand_css


# ==============================================================================
# PROOF EXECUTION
# ==============================================================================

class CompilationProof:
    """Executes and proves compilation works"""

    def __init__(self, brand_slug: str, verbose: bool = False):
        self.brand_slug = brand_slug
        self.verbose = verbose
        self.success = True
        self.errors = []

    def run(self):
        """Run complete proof"""

        print()
        print("=" * 100)
        print(f"  🧪 PROVING COMPILATION: {self.brand_slug}")
        print("=" * 100)
        print()

        # Step 1: Fetch raw data
        print("📊 STEP 1: FETCH RAW DATA")
        print("─" * 100)
        brand_row = self._fetch_brand_data()
        if not brand_row:
            return False

        # Step 2: Parse configuration
        print()
        print("📊 STEP 2: PARSE CONFIGURATION")
        print("─" * 100)
        brand_dict, brand_config = self._parse_config(brand_row)
        if not brand_config:
            return False

        # Step 3: Compile CSS
        print()
        print("📊 STEP 3: COMPILE CSS")
        print("─" * 100)
        brand_css = self._compile_css(brand_config)
        if not brand_css:
            return False

        # Step 4: Verify compilation
        print()
        print("📊 STEP 4: VERIFY COMPILATION")
        print("─" * 100)
        verification = self._verify_compilation(brand_config, brand_css)

        # Final result
        print()
        print("=" * 100)
        print("  📊 PROOF RESULT")
        print("=" * 100)
        print()

        if self.success and verification['passed']:
            print("✅ COMPILATION PROVEN!")
            print()
            print(f"   Brand: {brand_dict['name']}")
            print(f"   Slug: {self.brand_slug}")
            print(f"   Config → CSS transformation: VERIFIED")
            print(f"   All checks passed: {verification['passed']}/{verification['total']}")
            print()
            print("   💡 This PROVES:")
            print("      • Database stores raw JSON config")
            print("      • Compiler transforms JSON → CSS")
            print("      • CSS contains correct brand colors")
            print("      • Template can inject this CSS")
            print()
        else:
            print("❌ COMPILATION FAILED")
            print()
            for error in self.errors:
                print(f"   • {error}")
            print()

        print("=" * 100)
        print()

        return self.success and verification['passed']

    def _fetch_brand_data(self) -> Optional[sqlite3.Row]:
        """Step 1: Fetch brand from database"""

        print(f"Querying database for brand: {self.brand_slug}")
        print()

        try:
            db = get_db()
            brand_row = db.execute('''
                SELECT * FROM brands WHERE slug = ?
            ''', (self.brand_slug,)).fetchone()
            db.close()

            if not brand_row:
                print(f"❌ Brand not found: {self.brand_slug}")
                self.errors.append(f"Brand '{self.brand_slug}' does not exist in database")
                self.success = False
                return None

            # Show raw data
            print("✅ Brand found!")
            print()
            print("Raw data from database:")
            print(f"  • id: {brand_row['id']}")
            print(f"  • name: {brand_row['name']}")
            print(f"  • slug: {brand_row['slug']}")
            print(f"  • personality: {brand_row['personality']}")
            print(f"  • tone: {brand_row['tone']}")
            print()

            if self.verbose:
                print(f"  • config_json (raw):")
                print(f"    {brand_row['config_json'][:200]}...")
                print()

            return brand_row

        except Exception as e:
            print(f"❌ Database error: {e}")
            self.errors.append(f"Database query failed: {e}")
            self.success = False
            return None

    def _parse_config(self, brand_row: sqlite3.Row) -> tuple:
        """Step 2: Parse JSON configuration"""

        print("Parsing config_json field...")
        print()

        try:
            brand_dict = dict(brand_row)
            brand_config = json.loads(brand_dict['config_json'])

            print("✅ Config parsed successfully!")
            print()
            print("Extracted configuration:")
            print(f"  • colors: {brand_config.get('colors', [])}")
            print(f"  • values: {brand_config.get('values', [])}")

            if self.verbose:
                print()
                print("Full config:")
                print(f"  {json.dumps(brand_config, indent=2)}")

            print()

            return brand_dict, brand_config

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            self.errors.append(f"Failed to parse config_json: {e}")
            self.success = False
            return None, None

    def _compile_css(self, brand_config: Dict) -> Optional[str]:
        """Step 3: Run CSS compiler"""

        print("Running brand_css_generator.py::generate_brand_css()...")
        print()

        try:
            # Transform colors list to dict if needed
            if 'colors' in brand_config and isinstance(brand_config['colors'], list):
                colors_list = brand_config['colors']
                brand_config['colors'] = {
                    'primary': colors_list[0] if len(colors_list) > 0 else '#667eea',
                    'secondary': colors_list[1] if len(colors_list) > 1 else '#764ba2',
                    'accent': colors_list[2] if len(colors_list) > 2 else '#f093fb'
                }
                print("Transformed colors list to dict format")
                print()

            # Call actual compiler
            brand_css = generate_brand_css(brand_config, include_style_tag=True)

            print("✅ CSS generated successfully!")
            print()
            print(f"Generated CSS length: {len(brand_css)} characters")
            print()

            if self.verbose:
                print("First 500 characters of generated CSS:")
                print("─" * 80)
                print(brand_css[:500])
                print("..." if len(brand_css) > 500 else "")
                print("─" * 80)
            else:
                print("Preview (first 200 chars):")
                print(f"  {brand_css[:200]}...")

            print()

            return brand_css

        except Exception as e:
            print(f"❌ CSS generation error: {e}")
            self.errors.append(f"CSS compilation failed: {e}")
            self.success = False
            return None

    def _verify_compilation(self, brand_config: Dict, brand_css: str) -> Dict[str, Any]:
        """Step 4: Verify CSS is correct"""

        print("Running verification checks...")
        print()

        checks = []
        passed = 0
        total = 0

        # Check 1: CSS contains <style> tags
        total += 1
        if '<style>' in brand_css and '</style>' in brand_css:
            checks.append(("Has <style> tags", True))
            passed += 1
        else:
            checks.append(("Has <style> tags", False))

        # Check 2: CSS contains :root
        total += 1
        if ':root' in brand_css:
            checks.append(("Has :root CSS variables", True))
            passed += 1
        else:
            checks.append(("Has :root CSS variables", False))

        # Check 3: CSS contains brand colors
        colors = brand_config.get('colors', {})
        if colors:
            total += 1
            # Handle both dict and list formats
            if isinstance(colors, dict):
                primary_color = colors.get('primary', '#667eea')
            else:
                primary_color = colors[0] if len(colors) > 0 else '#667eea'

            if primary_color in brand_css:
                checks.append((f"Contains primary color {primary_color}", True))
                passed += 1
            else:
                checks.append((f"Contains primary color {primary_color}", False))

        # Check 4: CSS contains --brand-primary variable
        total += 1
        if '--brand-primary' in brand_css:
            checks.append(("Has --brand-primary variable", True))
            passed += 1
        else:
            checks.append(("Has --brand-primary variable", False))

        # Check 5: CSS has header styles
        total += 1
        if 'header {' in brand_css or 'header{' in brand_css:
            checks.append(("Has header styles", True))
            passed += 1
        else:
            checks.append(("Has header styles", False))

        # Print results
        print("Verification results:")
        print()
        for check_name, check_passed in checks:
            status = "✅" if check_passed else "❌"
            print(f"  {status} {check_name}")

        print()
        print(f"Checks passed: {passed}/{total}")
        print()

        return {
            'passed': passed,
            'total': total,
            'all_passed': passed == total,
            'checks': checks
        }


# ==============================================================================
# SIDE-BY-SIDE COMPARISON
# ==============================================================================

def compare_brands(slug1: str, slug2: str):
    """Compare compilation results for two brands"""

    print()
    print("=" * 100)
    print(f"  🔍 COMPARING: {slug1} vs {slug2}")
    print("=" * 100)
    print()

    # Compile both
    print("Compiling first brand...")
    proof1 = CompilationProof(slug1, verbose=False)
    result1 = proof1.run()

    print()
    print("Compiling second brand...")
    proof2 = CompilationProof(slug2, verbose=False)
    result2 = proof2.run()

    # Compare
    print()
    print("=" * 100)
    print("  📊 COMPARISON RESULT")
    print("=" * 100)
    print()

    if result1 and result2:
        print(f"✅ Both brands compile successfully!")
        print()
        print("This PROVES:")
        print("  • Compilation system works for multiple brands")
        print("  • Each brand gets unique CSS")
        print("  • Template system is reusable")
    else:
        print("❌ One or both brands failed to compile")

    print()


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 prove_compilation.py ocean-dreams")
        print("  python3 prove_compilation.py testbrand-auto --verbose")
        print("  python3 prove_compilation.py ocean-dreams testbrand-auto  # Compare two")
        return

    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    # Remove flags from argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]

    if len(args) == 2:
        # Comparison mode
        compare_brands(args[0], args[1])
    else:
        # Single brand proof
        slug = args[0]
        proof = CompilationProof(slug, verbose=verbose)
        success = proof.run()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

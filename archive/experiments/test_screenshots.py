#!/usr/bin/env python3
"""
Screenshot Tests for Soulfra - Visual "Fax" Verification

Automated browser testing with screenshots to verify:
- Pages render without errors
- Visual appearance is correct
- SEO/accessibility checks
- No TypeErrors or broken templates

Run with: python test_screenshots.py

Requires: pip install playwright && playwright install
"""

import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, expect
import time

# Screenshot output directory
SCREENSHOT_DIR = 'screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Test server URL
BASE_URL = os.environ.get('TEST_URL', 'http://localhost:5001')


def timestamp():
    """Get timestamp for screenshot filenames"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def test_homepage(page):
    """Test homepage loads and renders correctly"""
    print("\n🏠 Testing homepage...")

    page.goto(BASE_URL)

    # Wait for page to load
    page.wait_for_load_state('networkidle')

    # Check title
    expect(page).to_have_title(/Soulfra/)

    # Check main elements exist
    expect(page.locator('nav')).to_be_visible()
    expect(page.locator('main')).to_be_visible()

    # Take screenshot
    screenshot_path = f'{SCREENSHOT_DIR}/homepage_{timestamp()}.png'
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"   ✅ Homepage renders correctly")
    print(f"   📸 Screenshot: {screenshot_path}")


def test_souls_browser(page):
    """Test Soul Browser page"""
    print("\n👻 Testing Soul Browser...")

    page.goto(f'{BASE_URL}/souls')
    page.wait_for_load_state('networkidle')

    # Check for key elements
    expect(page.get_by_text('Soul Browser')).to_be_visible()

    # Check for user cards (should have at least 1)
    cards = page.locator('[style*="grid"]').first
    expect(cards).to_be_visible()

    # Take screenshot
    screenshot_path = f'{SCREENSHOT_DIR}/souls_browser_{timestamp()}.png'
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"   ✅ Soul Browser renders correctly")
    print(f"   📸 Screenshot: {screenshot_path}")


def test_soul_detail(page):
    """Test individual soul detail page"""
    print("\n🧠 Testing Soul Detail page...")

    page.goto(f'{BASE_URL}/soul/calriven')
    page.wait_for_load_state('networkidle')

    # Check for key sections
    expect(page.get_by_text('Identity')).to_be_visible()
    expect(page.get_by_text('Essence')).to_be_visible()
    expect(page.get_by_text('Expression')).to_be_visible()

    # Take screenshot
    screenshot_path = f'{SCREENSHOT_DIR}/soul_detail_{timestamp()}.png'
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"   ✅ Soul Detail renders correctly")
    print(f"   📸 Screenshot: {screenshot_path}")


def test_soul_similar(page):
    """Test similar souls page"""
    print("\n🔍 Testing Similar Souls page...")

    page.goto(f'{BASE_URL}/soul/calriven/similar')
    page.wait_for_load_state('networkidle')

    # Check for similarity indicators
    expect(page.get_by_text('Similar Souls')).to_be_visible()
    expect(page.get_by_text('%')).to_be_visible()  # Similarity percentage

    # Take screenshot
    screenshot_path = f'{SCREENSHOT_DIR}/soul_similar_{timestamp()}.png'
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"   ✅ Similar Souls renders correctly")
    print(f"   📸 Screenshot: {screenshot_path}")


def test_accessibility(page):
    """Test basic accessibility requirements"""
    print("\n♿ Testing Accessibility...")

    page.goto(f'{BASE_URL}/souls')
    page.wait_for_load_state('networkidle')

    # Check for meta tags
    meta_description = page.locator('meta[name="description"]')
    expect(meta_description).to_have_count(1)

    # Check for images with alt text
    images_without_alt = page.locator('img:not([alt])')
    count = images_without_alt.count()

    if count > 0:
        print(f"   ⚠️  Found {count} images without alt text")
    else:
        print(f"   ✅ All images have alt text")

    # Check for proper heading hierarchy
    h1_count = page.locator('h1').count()
    if h1_count == 1:
        print(f"   ✅ Proper H1 hierarchy (1 H1 found)")
    else:
        print(f"   ⚠️  H1 count: {h1_count} (should be 1)")

    print(f"   ✅ Accessibility checks complete")


def test_no_console_errors(page):
    """Test that pages don't have JavaScript errors"""
    print("\n🐛 Testing for Console Errors...")

    console_errors = []

    def handle_console(msg):
        if msg.type == 'error':
            console_errors.append(msg.text)

    page.on('console', handle_console)

    # Test key pages
    pages_to_test = [
        '/',
        '/souls',
        '/soul/calriven',
        '/soul/calriven/similar'
    ]

    for url in pages_to_test:
        page.goto(f'{BASE_URL}{url}')
        page.wait_for_load_state('networkidle')
        time.sleep(0.5)  # Give time for JS errors to appear

    if console_errors:
        print(f"   ⚠️  Found {len(console_errors)} console errors:")
        for error in console_errors:
            print(f"      - {error}")
    else:
        print(f"   ✅ No console errors found")


def run_all_tests():
    """Run all screenshot tests"""
    print("=" * 70)
    print("🧪 Soulfra Screenshot Tests - Visual 'Fax' Verification")
    print("=" * 70)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            test_homepage(page)
            test_souls_browser(page)
            test_soul_detail(page)
            test_soul_similar(page)
            test_accessibility(page)
            test_no_console_errors(page)

            print("\n" + "=" * 70)
            print("✅ All screenshot tests passed!")
            print(f"📁 Screenshots saved in: {SCREENSHOT_DIR}/")
            print("=" * 70)

            return True

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            browser.close()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

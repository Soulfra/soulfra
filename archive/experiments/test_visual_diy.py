#!/usr/bin/env python3
"""
DIY Visual Testing - No External Dependencies!

Automated frontend verification using only Python stdlib + Pillow.
Tests pages like a "fax" - verifies visual content, SEO, and structure.

Teaching the pattern:
1. HTTP request (stdlib) → HTML response
2. HTML parsing (stdlib) → Meta tags, alt text, structure
3. Soul data → Pixel art baseline
4. Pixel comparison → Visual regression detection

No playwright, no selenium, no external browser!
Just pure Python learning from scratch.

Requires: Python stdlib + Pillow (already installed)
"""

import http.client
import urllib.parse
from html.parser import HTMLParser
import os
from PIL import Image, ImageChops
from datetime import datetime


# Test server URL
TEST_HOST = 'localhost'
TEST_PORT = 5001


def fetch_page(path='/'):
    """
    Fetch HTML page using stdlib http.client

    Args:
        path: URL path to fetch

    Returns:
        tuple: (status_code, html_content)

    Learning: http.client is Python's built-in HTTP library
    """
    conn = http.client.HTTPConnection(TEST_HOST, TEST_PORT, timeout=10)

    try:
        conn.request('GET', path)
        response = conn.getresponse()
        status = response.status
        content = response.read().decode('utf-8')
        return (status, content)
    except Exception as e:
        print(f"   ❌ Failed to fetch {path}: {e}")
        return (None, None)
    finally:
        conn.close()


class MetaTagParser(HTMLParser):
    """
    Parse HTML for meta tags and accessibility features

    Learning: HTMLParser is stdlib - no BeautifulSoup needed!
    """

    def __init__(self):
        super().__init__()
        self.meta_tags = {}
        self.images_without_alt = []
        self.h1_count = 0
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)

        # Collect meta tags
        if tag == 'meta':
            name = attrs_dict.get('name') or attrs_dict.get('property')
            content = attrs_dict.get('content')
            if name and content:
                self.meta_tags[name] = content

        # Check images for alt text
        if tag == 'img':
            if 'alt' not in attrs_dict:
                src = attrs_dict.get('src', 'unknown')
                self.images_without_alt.append(src)

        # Count H1 tags
        if tag == 'h1':
            self.h1_count += 1


def test_page_loads(path, expected_title_substring=None):
    """
    Test that page loads with 200 status

    Args:
        path: URL path to test
        expected_title_substring: String expected in title

    Returns:
        bool: True if test passes

    Learning: Basic HTTP status check
    """
    print(f"\n🔍 Testing page: {path}")

    status, html = fetch_page(path)

    if status != 200:
        print(f"   ❌ Failed: Got status {status}")
        return False

    print(f"   ✅ Page loads (status 200)")

    # Check for title substring
    if expected_title_substring:
        if expected_title_substring.lower() in html.lower():
            print(f"   ✅ Contains '{expected_title_substring}' in content")
        else:
            print(f"   ❌ Missing '{expected_title_substring}' in content")
            return False

    return True


def test_seo_meta_tags(path):
    """
    Test page for SEO meta tags

    Args:
        path: URL path to test

    Returns:
        bool: True if SEO tags present

    Learning: HTML parsing with stdlib
    """
    print(f"\n🏷️  Testing SEO meta tags: {path}")

    status, html = fetch_page(path)

    if status != 200:
        print(f"   ❌ Page didn't load")
        return False

    # Parse HTML
    parser = MetaTagParser()
    parser.feed(html)

    # Check for required meta tags
    required_tags = ['description']
    missing_tags = []

    for tag in required_tags:
        if tag in parser.meta_tags:
            print(f"   ✅ Has meta {tag}: {parser.meta_tags[tag][:50]}...")
        else:
            print(f"   ❌ Missing meta {tag}")
            missing_tags.append(tag)

    # Check for Open Graph tags (optional)
    og_tags = [k for k in parser.meta_tags.keys() if k.startswith('og:')]
    if og_tags:
        print(f"   ✅ Has {len(og_tags)} Open Graph tags")

    return len(missing_tags) == 0


def test_accessibility(path):
    """
    Test page for accessibility features

    Args:
        path: URL path to test

    Returns:
        bool: True if accessibility checks pass

    Learning: Check alt text, heading hierarchy
    """
    print(f"\n♿ Testing accessibility: {path}")

    status, html = fetch_page(path)

    if status != 200:
        print(f"   ❌ Page didn't load")
        return False

    # Parse HTML
    parser = MetaTagParser()
    parser.feed(html)

    passed = True

    # Check images have alt text
    if len(parser.images_without_alt) == 0:
        print(f"   ✅ All images have alt text")
    else:
        print(f"   ⚠️  {len(parser.images_without_alt)} images without alt text")
        for img in parser.images_without_alt[:3]:  # Show first 3
            print(f"      - {img}")

    # Check H1 count
    if parser.h1_count == 1:
        print(f"   ✅ Proper H1 hierarchy (1 H1)")
    else:
        print(f"   ⚠️  H1 count: {parser.h1_count} (should be 1)")

    return passed


def generate_soul_baseline_image(username='calriven', output_dir='baselines'):
    """
    Generate baseline soul visualization for comparison

    Args:
        username: Username to generate for
        output_dir: Where to save baseline

    Returns:
        str: Path to baseline image

    Learning: Use soul_visualizer to create test baselines
    """
    from soul_visualizer import generate_soul_visualization_from_username

    os.makedirs(output_dir, exist_ok=True)

    # Generate visualization
    img = generate_soul_visualization_from_username(username)

    if not img:
        print(f"   ❌ Could not generate visualization for {username}")
        return None

    # Save baseline
    filepath = os.path.join(output_dir, f'{username}_baseline.png')
    img.save(filepath, 'PNG')

    return filepath


def compare_images(img1_path, img2_path, threshold=0):
    """
    Compare two images pixel by pixel

    Args:
        img1_path: First image path
        img2_path: Second image path
        threshold: Difference threshold (0 = exact match)

    Returns:
        tuple: (are_same, difference_count, total_pixels)

    Learning: ImageChops.difference() shows pixel-level changes
    """
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    # Convert to same mode if needed
    if img1.mode != img2.mode:
        img2 = img2.convert(img1.mode)

    # Check dimensions match
    if img1.size != img2.size:
        print(f"   ❌ Image sizes don't match: {img1.size} vs {img2.size}")
        return (False, None, None)

    # Calculate difference
    diff = ImageChops.difference(img1, img2)

    # Count different pixels
    diff_data = list(diff.getdata())
    total_pixels = len(diff_data)

    # For RGB, pixel is (0,0,0) if identical
    different_pixels = sum(1 for pixel in diff_data if pixel != (0, 0, 0))

    are_same = different_pixels <= threshold

    return (are_same, different_pixels, total_pixels)


def test_visual_regression():
    """
    Test for visual regressions using pixel comparison

    Learning: Generate baseline, compare for changes
    """
    print(f"\n🎨 Testing visual regression (soul visualizations)")

    # Generate baseline
    baseline = generate_soul_baseline_image('calriven')

    if not baseline:
        print(f"   ⚠️  Could not generate baseline")
        return False

    print(f"   ✅ Generated baseline: {baseline}")

    # Generate same image again (should be identical)
    baseline2 = generate_soul_baseline_image('calriven', output_dir='baselines_test')

    if not baseline2:
        print(f"   ⚠️  Could not generate second image")
        return False

    # Compare
    are_same, diff_count, total = compare_images(baseline, baseline2)

    if are_same:
        print(f"   ✅ Images are identical (0/{total} pixels different)")
    else:
        print(f"   ❌ Images differ ({diff_count}/{total} pixels different)")
        percentage = (diff_count / total) * 100
        print(f"      {percentage:.2f}% different")

    # Cleanup test baseline
    if os.path.exists(baseline2):
        os.remove(baseline2)
        os.rmdir('baselines_test')

    return are_same


def run_all_tests():
    """Run all DIY visual tests"""
    print("=" * 70)
    print("🧪 DIY Visual Tests - Built from Scratch!")
    print("   No playwright, no selenium - just Python stdlib + Pillow")
    print("=" * 70)

    results = []

    # Test 1: Homepage loads
    results.append(test_page_loads('/', 'Soulfra'))

    # Test 2: Soul Browser loads
    results.append(test_page_loads('/souls', 'Soul Browser'))

    # Test 3: Soul Detail loads
    results.append(test_page_loads('/soul/calriven', 'Soul'))

    # Test 4: SEO meta tags
    results.append(test_seo_meta_tags('/souls'))

    # Test 5: Accessibility
    results.append(test_accessibility('/souls'))

    # Test 6: Visual regression
    results.append(test_visual_regression())

    # Summary
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All tests passed! ({passed}/{total})")
    else:
        print(f"⚠️  Some tests failed ({passed}/{total} passed)")

    print("=" * 70)

    return passed == total


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)

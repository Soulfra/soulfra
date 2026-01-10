#!/usr/bin/env python3
"""
Ad Injector - Google AdSense Auto-Injection System
===================================================

Automatically injects Google AdSense code into all static exports.

Where ads go:
1. Header (top of page) - Horizontal banner
2. Sidebar (right side) - Vertical ad
3. Middle of content - In-article ad
4. Footer - Another banner

Result: Monetize all your content automatically!

Usage:
    python3 ad_injector.py --all            # Inject ads in all brands
    python3 ad_injector.py --brand howtocookathome  # One brand

Configuration:
    Set ADSENSE_CLIENT_ID in this file to your Google AdSense publisher ID
"""

import sys
import os
import re
from pathlib import Path
from database import get_db


# ============================================================================
# CONFIGURATION - Change this to your Google AdSense ID
# ============================================================================
ADSENSE_CLIENT_ID = "ca-pub-XXXXXXXXXXXXXXXXX"  # Replace with your AdSense ID


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def generate_adsense_code():
    """Generate Google AdSense script tag"""

    return f'''
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT_ID}"
     crossorigin="anonymous"></script>
'''


def generate_ad_unit(slot, format="auto", style=""):
    """
    Generate AdSense ad unit

    Types:
    - horizontal: Banner ad (top/footer)
    - vertical: Sidebar ad
    - in-article: In-content ad
    """

    return f'''
<!-- Ad Unit: {slot} -->
<ins class="adsbygoogle"
     style="display:block;{style}"
     data-ad-client="{ADSENSE_CLIENT_ID}"
     data-ad-slot="{slot}"
     data-ad-format="{format}"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
'''


def inject_ads_into_html(html_content):
    """
    Inject ads into HTML content

    Placements:
    1. Header - after <header> tag
    2. Sidebar - in sidebar div (if exists)
    3. Middle - in middle of content
    4. Footer - before </body>
    """

    modified = html_content

    # 1. Add AdSense script to <head>
    adsense_script = generate_adsense_code()

    if '</head>' in modified:
        modified = modified.replace('</head>', f'{adsense_script}</head>')
    else:
        print("      ⚠️  No </head> tag found")

    # 2. Add header ad after <header>
    header_ad = generate_ad_unit('1234567890', 'horizontal', 'margin: 20px 0;')

    if '</header>' in modified:
        modified = modified.replace('</header>', f'</header>\n{header_ad}')

    # 3. Add sidebar ad (if sidebar exists)
    sidebar_ad = generate_ad_unit('0987654321', 'vertical', 'width: 300px;')

    if '<aside' in modified or 'class="sidebar"' in modified:
        # Try to find sidebar
        sidebar_pattern = r'(<aside[^>]*>|<div[^>]*class="sidebar"[^>]*>)'
        modified = re.sub(sidebar_pattern, r'\1\n' + sidebar_ad, modified, count=1)

    # 4. Add in-content ad (middle of article)
    article_ad = generate_ad_unit('1122334455', 'fluid', 'margin: 30px 0;')

    if '<article' in modified or '<div class="content"' in modified:
        # Find content div and inject in middle
        content_pattern = r'(<article[^>]*>.*?)(</article>)'
        if re.search(content_pattern, modified, re.DOTALL):
            # Split content and insert ad in middle
            modified = re.sub(
                content_pattern,
                lambda m: m.group(1)[:len(m.group(1))//2] + article_ad + m.group(1)[len(m.group(1))//2:] + m.group(2),
                modified,
                count=1,
                flags=re.DOTALL
            )

    # 5. Add footer ad before </body>
    footer_ad = generate_ad_unit('5544332211', 'horizontal', 'margin: 20px 0;')

    if '</body>' in modified:
        modified = modified.replace('</body>', f'{footer_ad}\n</body>')

    return modified


def inject_ads_for_brand(brand_slug):
    """Inject ads into all HTML files for a brand"""

    output_dir = Path(f"output/{brand_slug}")

    if not output_dir.exists():
        print(f"   ⚠️  Output directory not found: {output_dir}")
        return 0

    # Find all HTML files
    html_files = list(output_dir.rglob('*.html'))

    print(f"   Found {len(html_files)} HTML files")

    count = 0
    for html_file in html_files:
        try:
            # Read HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                original = f.read()

            # Inject ads
            modified = inject_ads_into_html(original)

            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(modified)

            count += 1

        except Exception as e:
            print(f"      ⚠️  Error processing {html_file}: {e}")

    return count


def main():
    """Main entry point"""

    print_header("💰 Ad Injector - Google AdSense Auto-Injection")

    print(f"""
Automatically injects Google AdSense into all static pages.

Your AdSense ID: {ADSENSE_CLIENT_ID}
(Change ADSENSE_CLIENT_ID in this file to your actual ID)

Ad placements:
1. Header - Horizontal banner after <header>
2. Sidebar - Vertical ad in sidebar
3. In-content - Fluid ad in middle of article
4. Footer - Horizontal banner before </body>
    """)

    if ADSENSE_CLIENT_ID == "ca-pub-XXXXXXXXXXXXXXXXX":
        print("\n⚠️  WARNING: Using placeholder AdSense ID!")
        print("   Update ADSENSE_CLIENT_ID in ad_injector.py with your actual ID")
        print("   Get your ID from: https://www.google.com/adsense")
        print()

    # Get brands
    process_all = '--all' in sys.argv
    brand_slug = None

    if '--brand' in sys.argv:
        idx = sys.argv.index('--brand')
        if idx + 1 < len(sys.argv):
            brand_slug = sys.argv[idx + 1]

    conn = get_db()

    if brand_slug:
        brands = [conn.execute('SELECT * FROM brands WHERE slug = ?', (brand_slug,)).fetchone()]
        brands = [dict(b) for b in brands if b]
    elif process_all:
        brands = conn.execute('SELECT * FROM brands ORDER BY id').fetchall()
        brands = [dict(b) for b in brands]
    else:
        print("❌ Specify --all or --brand <slug>")
        conn.close()
        return

    conn.close()

    if not brands:
        print("❌ No brands found")
        return

    print(f"\n📊 Processing {len(brands)} brands...\n")

    # Inject ads
    total_files = 0
    for brand in brands:
        print(f"   💉 Injecting ads for {brand['name']} ({brand['slug']})...")
        count = inject_ads_for_brand(brand['slug'])
        total_files += count
        print(f"      ✅ Modified {count} files")

    # Summary
    print_header("🎉 Ad Injection Complete!")

    print(f"""
✅ Injected ads into {total_files} HTML files across {len(brands)} brands

Next steps:
1. Verify AdSense account approved:
   https://www.google.com/adsense

2. Deploy static sites to live hosting

3. Wait for ads to start showing (can take 24-48 hours)

4. Monitor revenue:
   https://www.google.com/adsense/performance

Your content is now MONETIZED! 💰
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")

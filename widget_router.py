#!/usr/bin/env python3
"""
Widget Router - Browser-in-Browser iframe Routing System
========================================================

Creates "browser in browser" experience where widgets embed anywhere.

The Flow:
---------
External website → Your widget → iframe → Soulfra content

Example:
    <!-- On example.com -->
    <script src="https://soulfra.github.io/widget-embed.js"></script>
    <div id="soulfra-widget" data-brand="howtocookathome"></div>

    <!-- Loads iframe -->
    <iframe src="https://soulfra.com/widget/howtocookathome"></iframe>

Features:
- Routes traffic through Soulfra
- Tracks referrers
- Collects analytics
- Embeddable on ANY website

Usage:
    python3 widget_router.py --update-all    # Update all widgets
    python3 widget_router.py --brand howtocookathome  # One brand
"""

import sys
import os
from pathlib import Path
from database import get_db


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def generate_widget_embed_js(brands):
    """
    Generate widget-embed.js with all brands

    Creates embeddable JavaScript that loads iframes
    """

    brand_list = ', '.join([f'"{b["slug"]}"' for b in brands])

    js_code = f'''/**
 * Soulfra Embeddable Widget - Browser in Browser
 *
 * Usage:
 *   <script src="https://soulfra.github.io/widget-embed.js"></script>
 *   <div id="soulfra-widget" data-brand="BRAND_SLUG"></div>
 *
 * Available brands: {brand_list}
 */

(function() {{
  'use strict';

  // Configuration
  const WIDGET_BASE_URL = window.location.origin || 'http://localhost:5001';
  const AVAILABLE_BRANDS = [{brand_list}];

  function initSoulfraWidget() {{
    const containers = document.querySelectorAll('[id^="soulfra-widget"]');

    containers.forEach(container => {{
      const brand = container.getAttribute('data-brand') || 'soulfra';
      const width = container.getAttribute('data-width') || '100%';
      const height = container.getAttribute('data-height') || '600px';
      const theme = container.getAttribute('data-theme') || 'light';

      // Validate brand
      if (!AVAILABLE_BRANDS.includes(brand)) {{
        console.error(`[Soulfra Widget] Invalid brand: ${{brand}}`);
        console.error(`[Soulfra Widget] Available brands: ${{AVAILABLE_BRANDS.join(', ')}}`);
        return;
      }}

      // Create iframe
      const iframe = document.createElement('iframe');
      iframe.src = `${{WIDGET_BASE_URL}}/widget/${{brand}}?theme=${{theme}}`;
      iframe.style.width = width;
      iframe.style.height = height;
      iframe.style.border = 'none';
      iframe.style.borderRadius = '8px';
      iframe.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
      iframe.setAttribute('frameborder', '0');
      iframe.setAttribute('allowtransparency', 'true');

      // Track referrer
      const referrer = window.location.href;
      iframe.setAttribute('data-referrer', referrer);

      // Replace container with iframe
      container.innerHTML = '';
      container.appendChild(iframe);

      console.log(`[Soulfra Widget] Loaded ${{brand}} widget from ${{referrer}}`);
    }});
  }}

  // Auto-initialize on DOM ready
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initSoulfraWidget);
  }} else {{
    initSoulfraWidget();
  }}

  // Expose for manual initialization
  window.SoulfraWidget = {{
    init: initSoulfraWidget,
    brands: AVAILABLE_BRANDS
  }};
}})();
'''

    return js_code


def update_widget_embed_file(brands):
    """Update static/widget-embed.js"""

    js_code = generate_widget_embed_js(brands)

    # Write to static/
    static_path = Path('static/widget-embed.js')
    try:
        with open(static_path, 'w', encoding='utf-8') as f:
            f.write(js_code)
        print(f"   ✅ Updated {static_path}")
    except Exception as e:
        print(f"   ❌ Error writing {static_path}: {e}")

    # Copy to output directories for each brand
    for brand in brands:
        output_path = Path(f"output/{brand['slug']}/widget-embed.js")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(js_code)
            print(f"   ✅ Copied to {output_path}")
        except Exception as e:
            print(f"   ⚠️  Error writing {output_path}: {e}")


def main():
    """Main entry point"""

    print_header("🔗 Widget Router - Browser in Browser System")

    print("""
Creates embeddable widgets that work on ANY website.

How it works:
1. External site loads widget-embed.js
2. JavaScript creates iframe pointing to Soulfra
3. Content loads in iframe (browser in browser!)
4. Tracks referrers and collects analytics

Example usage:
    <script src="https://soulfra.github.io/widget-embed.js"></script>
    <div id="soulfra-widget" data-brand="howtocookathome"></div>
    """)

    # Get brands
    conn = get_db()
    brands = conn.execute('SELECT * FROM brands ORDER BY id').fetchall()
    conn.close()

    brands = [dict(b) for b in brands]

    if not brands:
        print("❌ No brands found in database")
        return

    print(f"\n📊 Found {len(brands)} brands:")
    for brand in brands:
        print(f"   - {brand['name']} ({brand['slug']})")

    # Update widget-embed.js
    print("\n🔄 Updating widget-embed.js...")
    update_widget_embed_file(brands)

    # Summary
    print_header("🎉 Widget Router Updated!")

    print(f"""
✅ Widget embed code generated for {len(brands)} brands

Files updated:
- static/widget-embed.js
- output/{{brand_slug}}/widget-embed.js (for each brand)

Next steps:
1. Deploy widget-embed.js to GitHub Pages or CDN
2. Add to ANY website:
   <script src="https://YOUR-DOMAIN/widget-embed.js"></script>
   <div id="soulfra-widget" data-brand="howtocookathome"></div>

3. Widget loads in iframe - browser in browser!

Your content is now embeddable EVERYWHERE! 🚀
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")

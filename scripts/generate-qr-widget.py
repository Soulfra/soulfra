#!/usr/bin/env python3
"""
Generate QR Code Widget for GitHub Profile README

Creates a floating QR code that enables iPhone pairing with GitHub OAuth.
Similar to Discord's "Login with QR Code" feature.

Usage:
    python3 generate-qr-widget.py --url "https://cringeproof.com/pair"

Outputs:
    - qr-widget.svg (embeddable in README.md)
    - qr-widget-markdown.md (ready-to-paste markdown)
"""

import qrcode
import qrcode.image.svg
import argparse
from pathlib import Path

def generate_qr_svg(url, output_path='qr-widget.svg'):
    """Generate SVG QR code for embedding in README"""

    # Create QR code factory
    factory = qrcode.image.svg.SvgPathImage

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Create SVG image
    img = qr.make_image(image_factory=factory, fill_color="black", back_color="white")

    # Save SVG
    img.save(output_path)

    print(f"✅ QR code saved to {output_path}")
    return output_path

def generate_floating_widget_html(qr_svg_path, pairing_url):
    """Generate HTML widget with floating QR code (GitHub supports some HTML in README)"""

    html = f"""
<!-- Floating QR Code Widget for iPhone Pairing -->
<div align="right">
    <a href="{pairing_url}">
        <img src="{qr_svg_path}" alt="Scan to pair iPhone with GitHub" width="150" height="150">
    </a>
    <br>
    <sub>📱 <strong>Scan with iPhone</strong><br>Pair your device to contribute voice memos</sub>
</div>
"""

    return html

def generate_markdown_widget(qr_svg_path, pairing_url):
    """Generate markdown-friendly QR widget"""

    markdown = f"""
## 📱 Pair Your iPhone

Scan this QR code to connect your iPhone and contribute voice memos:

<div align="center">
    <a href="{pairing_url}">
        <img src="{qr_svg_path}" alt="Scan to pair iPhone" width="200">
    </a>
</div>

**What happens when you scan:**
1. Opens pairing page on your iPhone
2. Click "Connect GitHub"
3. Authorize permissions
4. Start recording voice memos
5. Your recordings appear here automatically!

---
"""

    return markdown

def generate_inline_badge(pairing_url):
    """Generate inline badge/button style QR"""

    badge = f"""
[![Pair iPhone](https://img.shields.io/badge/📱_Pair_iPhone-Scan_QR_to_Connect-blue?style=for-the-badge)]({pairing_url})
"""

    return badge

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate QR code widget for GitHub README')
    parser.add_argument('--url', default='https://cringeproof.com/pair', help='Pairing URL')
    parser.add_argument('--style', choices=['floating', 'section', 'badge', 'all'], default='all',
                        help='Widget style to generate')
    parser.add_argument('--output', default='../assets/qr-pair.svg', help='Output SVG path')

    args = parser.parse_args()

    # Generate QR code SVG
    qr_path = generate_qr_svg(args.url, args.output)

    # Make path relative for README embedding
    relative_qr_path = qr_path.replace('../', '')

    print("\n📋 Copy-paste into README.md:\n")
    print("=" * 60)

    if args.style in ['floating', 'all']:
        print("\n### Option 1: Floating Widget (Top Right)")
        print(generate_floating_widget_html(relative_qr_path, args.url))

    if args.style in ['section', 'all']:
        print("\n### Option 2: Full Section")
        print(generate_markdown_widget(relative_qr_path, args.url))

    if args.style in ['badge', 'all']:
        print("\n### Option 3: Inline Badge")
        print(generate_inline_badge(args.url))

    print("\n" + "=" * 60)

    # Save markdown template
    markdown_output = Path('../assets/qr-widget-template.md')
    with open(markdown_output, 'w') as f:
        f.write(generate_markdown_widget(relative_qr_path, args.url))

    print(f"\n✅ Markdown template saved to {markdown_output}")
    print(f"\n🔗 Pairing URL: {args.url}")
    print("\n💡 Next steps:")
    print("   1. Copy markdown from above into README.md")
    print("   2. Create mobile-pair.html pairing page")
    print("   3. Set up GitHub OAuth app")
    print("   4. Test scanning with iPhone!")

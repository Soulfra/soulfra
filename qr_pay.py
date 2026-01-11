#!/usr/bin/env python3
"""
QR Code → Payment System

The ONLY QR system you need.

Like a price gun for creating payments:
1. Generate QR code for any amount
2. Scan QR → payment page
3. Pay → done

Usage:
    python3 qr-pay.py --code ABC123 --amount 10 --label "Tampa Plumber"
    python3 qr-pay.py --rotating-password  # Today's password
    python3 qr-pay.py --list               # Show all QR codes

Generates:
    - QR code SVG
    - Payment page HTML
    - Shareable link
"""

import argparse
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path


def generate_qr_svg(url: str, filename: str):
    """Generate QR code as SVG (no dependencies!)"""

    # Simple QR code using qrencode shell command or pure Python
    import subprocess

    try:
        # Try using qrencode if available
        subprocess.run(
            ['qrencode', '-t', 'SVG', '-o', filename, url],
            check=True,
            capture_output=True
        )
        print(f"   ✅ QR code: {filename}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Fallback: create a simple data URL
        print(f"   ⚠️  Install qrencode: brew install qrencode")
        print(f"   📋 Manual QR URL: {url}")


def create_payment_page(code: str, amount: float, label: str, output_dir: Path, style: str = 'normal'):
    """Create static payment page with specified style"""

    # Try to load template
    template_path = Path(__file__).parent / 'templates' / f'payment-{style}.html'

    if template_path.exists():
        # Use Jinja2 template
        from jinja2 import Template

        with open(template_path) as f:
            template = Template(f.read())

        html = template.render(
            code=code,
            amount=amount,
            label=label
        )

        print(f"   🎨 Using {style} template")
    else:
        # Fallback to inline HTML (default gradient style)
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pay ${amount} - {label}</title>
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}
        h1 {{ color: #333; font-size: 2rem; margin-bottom: 10px; }}
        .price {{
            color: #667eea;
            font-size: 3rem;
            font-weight: bold;
            margin: 20px 0;
        }}
        .label {{ color: #666; font-size: 1.2rem; margin-bottom: 30px; }}
        input {{
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 20px;
        }}
        input:focus {{ outline: none; border-color: #667eea; }}
        button {{
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{ transform: translateY(-2px); }}
        .note {{ color: #999; font-size: 0.9rem; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💳 Payment</h1>
        <div class="label">{label}</div>
        <input type="number" id="amount" value="{amount}" step="0.01" min="0.01">
        <button onclick="pay()">Pay Now</button>
        <div class="note">QR Code: {code}</div>
    </div>

    <script>
        function pay() {{
            const amount = document.getElementById('amount').value;
            alert(`Payment of $${{amount}} initiated!\\nQR Code: {code}\\n\\nStripe integration coming next...`);
            // TODO: Integrate with Stripe Payment Element
        }}
    </script>
</body>
</html>'''

    # Save with style suffix if not normal
    if style == 'normal':
        page_path = output_dir / f'pay-{code}.html'
    else:
        page_path = output_dir / f'pay-{code}-{style}.html'

    page_path.write_text(html)
    print(f"   ✅ Payment page: {page_path}")

    return page_path


def get_rotating_password():
    """Generate today's password (like January11)"""
    today = datetime.now()
    password = today.strftime('%B%d')  # January11
    return password


def init_database():
    """Initialize QR codes database"""
    db_path = Path('qr_codes.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_codes (
            code TEXT PRIMARY KEY,
            amount REAL,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scans INTEGER DEFAULT 0,
            payments INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

    return db_path


def save_qr_code(code: str, amount: float, label: str):
    """Save QR code to database"""
    conn = sqlite3.connect('qr_codes.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO qr_codes (code, amount, label)
        VALUES (?, ?, ?)
    ''', (code, amount, label))

    conn.commit()
    conn.close()


def list_qr_codes():
    """List all QR codes"""
    conn = sqlite3.connect('qr_codes.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT code, amount, label, created_at, scans, payments
        FROM qr_codes
        ORDER BY created_at DESC
    ''')

    print("\n📋 QR Codes:\n")
    print(f"{'Code':<15} {'Amount':<10} {'Label':<30} {'Scans':<8} {'Payments':<10}")
    print("-" * 80)

    for row in cursor.fetchall():
        code, amount, label, created_at, scans, payments = row
        print(f"{code:<15} ${amount:<9.2f} {label:<30} {scans:<8} {payments:<10}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description='QR Code Payment System')
    parser.add_argument('--code', help='QR code identifier (e.g., ABC123)')
    parser.add_argument('--amount', type=float, default=1.0, help='Payment amount')
    parser.add_argument('--label', default='Payment', help='Payment label')
    parser.add_argument('--style', default='normal', choices=['normal', 'matrix', 'cyberpunk', 'upc'],
                        help='Payment page style')
    parser.add_argument('--matrix', action='store_true', help='Use Matrix style (shortcut for --style matrix)')
    parser.add_argument('--cyberpunk', action='store_true', help='Use cyberpunk style (shortcut)')
    parser.add_argument('--upc', action='store_true', help='Use UPC barcode style (shortcut)')
    parser.add_argument('--rotating-password', action='store_true', help='Show today\'s password')
    parser.add_argument('--list', action='store_true', help='List all QR codes')

    args = parser.parse_args()

    # Handle style shortcuts
    if args.matrix:
        args.style = 'matrix'
    elif args.cyberpunk:
        args.style = 'cyberpunk'
    elif args.upc:
        args.style = 'upc'

    # Initialize database
    init_database()

    # Show rotating password
    if args.rotating_password:
        password = get_rotating_password()
        print(f"\n🔑 Today's Password: {password}")
        print(f"   Tomorrow: {(datetime.now().day + 1):02d}")
        print(f"\n   Use in URLs: soulfra.com/admin.html?password={password}")
        return

    # List QR codes
    if args.list:
        list_qr_codes()
        return

    # Generate QR code
    if not args.code:
        print("Error: --code required (or use --list or --rotating-password)")
        return

    print(f"\n🎯 Generating QR Code: {args.code}")
    print(f"   Amount: ${args.amount}")
    print(f"   Label: {args.label}")
    print()

    # Create output directory
    output_dir = Path('output/soulfra/pay')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate payment page
    page_path = create_payment_page(args.code, args.amount, args.label, output_dir, args.style)

    # Generate QR code
    if args.style == 'normal':
        url = f"https://soulfra.com/pay/pay-{args.code}.html?amount={args.amount}"
        qr_path = output_dir / f'qr-{args.code}.svg'
    else:
        url = f"https://soulfra.com/pay/pay-{args.code}-{args.style}.html?amount={args.amount}"
        qr_path = output_dir / f'qr-{args.code}-{args.style}.svg'
    generate_qr_svg(url, str(qr_path))

    # Save to database
    save_qr_code(args.code, args.amount, args.label)

    print()
    print(f"🌐 Payment URL: {url}")
    print(f"📱 Scan QR: {qr_path}")
    print()
    print("Next steps:")
    print("1. Deploy: ./deploy-tools.sh")
    print("2. Test: Open QR code on phone")
    print("3. Integrate Stripe: Add your keys to payment.py")
    print()


if __name__ == '__main__':
    main()

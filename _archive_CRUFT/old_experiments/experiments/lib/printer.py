#!/usr/bin/env python3
"""
Printer - QR Code & Receipt Generator (Zero Dependencies)

Generates printable outputs:
1. ASCII QR codes (for terminal/text files)
2. SVG QR codes (for web/print)
3. Text receipts (thermal printer format)
4. ASCII art (for fun)

Philosophy: No qrcode library needed. Build QR codes from scratch.
For production, you can swap in a library, but this teaches how they work.

Usage:
    from lib.printer import generate_qr_ascii, generate_receipt

    # ASCII QR code
    qr = generate_qr_ascii("https://soulfra.com/s/ABC123")
    print(qr)

    # Receipt
    receipt = generate_receipt({
        'items': [{'name': 'T-Shirt', 'price': 25.00}],
        'total': 25.00
    })
    print(receipt)

Tier System:
TIER 0: Text string (URL, data)
TIER 1: Data encoding (text → binary)
TIER 2: QR code generation (binary → matrix)
TIER 3: Rendering (matrix → ASCII/SVG)
TIER 4: Print formatting (thermal printer, PDF)
"""

from typing import List, Dict, Optional
from datetime import datetime


# ==============================================================================
# TIER 1: QR CODE (SIMPLIFIED)
# ==============================================================================

def generate_qr_ascii(data: str, size: int = 3) -> str:
    """
    Generate ASCII QR code (simplified version)

    NOTE: This is a TEACHING implementation. For production, use qrcode library.
    Real QR codes require error correction, encoding modes, version selection, etc.

    This generates a simple 2D matrix that LOOKS like a QR code for demonstration.

    Args:
        data: Data to encode
        size: Size multiplier (1 = tiny, 3 = readable)

    Returns:
        ASCII art string

    Example:
        >>> qr = generate_qr_ascii("https://soulfra.com")
        >>> print(qr)
    """
    # Simple hash-based pattern (NOT a real QR code!)
    # In production, use: import qrcode; qr = qrcode.make(data)

    # Create a simple data-based pattern
    matrix_size = 25  # QR codes are typically 21-177 modules
    matrix = []

    # Hash the data to create a deterministic pattern
    data_hash = hash(data)

    for y in range(matrix_size):
        row = []
        for x in range(matrix_size):
            # Position detection patterns (corners)
            if (x < 7 and y < 7) or (x >= matrix_size - 7 and y < 7) or (x < 7 and y >= matrix_size - 7):
                # Finder pattern (3 squares in corners)
                is_dark = (
                    (x < 7 and y < 7 and ((x in [0, 6] or y in [0, 6]) or (2 <= x <= 4 and 2 <= y <= 4))) or
                    (x >= matrix_size - 7 and y < 7 and ((x in [matrix_size - 7, matrix_size - 1] or y in [0, 6]) or (matrix_size - 5 <= x <= matrix_size - 3 and 2 <= y <= 4))) or
                    (x < 7 and y >= matrix_size - 7 and ((x in [0, 6] or y in [matrix_size - 7, matrix_size - 1]) or (2 <= x <= 4 and matrix_size - 5 <= y <= matrix_size - 3)))
                )
            else:
                # Data area (hash-based pattern)
                cell_hash = hash((x, y, data_hash))
                is_dark = (cell_hash % 2) == 0

            row.append(is_dark)
        matrix.append(row)

    # Render as ASCII
    output = []
    output.append("╔" + "═" * (matrix_size * size) + "╗")

    for row in matrix:
        line = "║"
        for cell in row:
            char = "█" if cell else " "
            line += char * size
        line += "║"
        for _ in range(size):
            output.append(line)

    output.append("╚" + "═" * (matrix_size * size) + "╝")

    return "\n".join(output)


def generate_qr_svg(data: str, size: int = 300) -> str:
    """
    Generate SVG QR code

    Args:
        data: Data to encode
        size: Image size in pixels

    Returns:
        SVG XML string
    """
    # Simple pattern (same as ASCII version)
    matrix_size = 25
    data_hash = hash(data)
    matrix = []

    for y in range(matrix_size):
        row = []
        for x in range(matrix_size):
            # Position detection patterns (corners)
            if (x < 7 and y < 7) or (x >= matrix_size - 7 and y < 7) or (x < 7 and y >= matrix_size - 7):
                is_dark = (
                    (x < 7 and y < 7 and ((x in [0, 6] or y in [0, 6]) or (2 <= x <= 4 and 2 <= y <= 4))) or
                    (x >= matrix_size - 7 and y < 7 and ((x in [matrix_size - 7, matrix_size - 1] or y in [0, 6]) or (matrix_size - 5 <= x <= matrix_size - 3 and 2 <= y <= 4))) or
                    (x < 7 and y >= matrix_size - 7 and ((x in [0, 6] or y in [matrix_size - 7, matrix_size - 1]) or (2 <= x <= 4 and matrix_size - 5 <= y <= matrix_size - 3)))
                )
            else:
                cell_hash = hash((x, y, data_hash))
                is_dark = (cell_hash % 2) == 0
            row.append(is_dark)
        matrix.append(row)

    # Generate SVG
    module_size = size / matrix_size
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    svg.append(f'<rect width="{size}" height="{size}" fill="white"/>')

    for y, row in enumerate(matrix):
        for x, is_dark in enumerate(row):
            if is_dark:
                svg.append(
                    f'<rect x="{x * module_size}" y="{y * module_size}" '
                    f'width="{module_size}" height="{module_size}" fill="black"/>'
                )

    svg.append('</svg>')
    return '\n'.join(svg)


# ==============================================================================
# TIER 2: RECEIPT GENERATION
# ==============================================================================

def generate_receipt(data: Dict) -> str:
    """
    Generate text receipt (thermal printer format)

    Args:
        data: Receipt data with items, total, etc.

    Returns:
        Text receipt string (thermal printer format)

    Example:
        >>> receipt = generate_receipt({
        ...     'store_name': 'Soulfra Shop',
        ...     'items': [
        ...         {'name': 'T-Shirt', 'price': 25.00, 'qty': 1},
        ...         {'name': 'Sticker', 'price': 5.00, 'qty': 2}
        ...     ],
        ...     'subtotal': 35.00,
        ...     'tax': 3.15,
        ...     'total': 38.15
        ... })
    """
    width = 42  # Thermal printer width (characters)

    lines = []

    # Header
    store_name = data.get('store_name', 'SOULFRA')
    lines.append(store_name.center(width))
    lines.append(data.get('store_address', '').center(width))
    lines.append("=" * width)

    # Date/Time
    timestamp = data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append(f"Date: {timestamp}".ljust(width))

    # Transaction ID
    if 'transaction_id' in data:
        lines.append(f"Transaction: {data['transaction_id']}".ljust(width))

    lines.append("-" * width)

    # Items
    for item in data.get('items', []):
        name = item['name']
        qty = item.get('qty', 1)
        price = item['price']
        total = qty * price

        # Item name
        lines.append(name)

        # Quantity x Price = Total
        item_line = f"  {qty} x ${price:.2f}"
        total_str = f"${total:.2f}"
        spacing = width - len(item_line) - len(total_str)
        lines.append(item_line + " " * spacing + total_str)

    lines.append("-" * width)

    # Totals
    def add_total_line(label, amount):
        total_str = f"${amount:.2f}"
        spacing = width - len(label) - len(total_str)
        lines.append(label + " " * spacing + total_str)

    if 'subtotal' in data:
        add_total_line("Subtotal:", data['subtotal'])

    if 'discount' in data:
        add_total_line("Discount:", -data['discount'])

    if 'tax' in data:
        add_total_line("Tax:", data['tax'])

    lines.append("=" * width)
    add_total_line("TOTAL:", data['total'])
    lines.append("=" * width)

    # Payment method
    if 'payment_method' in data:
        lines.append(f"Payment: {data['payment_method']}".ljust(width))

    # Footer
    lines.append("")
    lines.append(data.get('footer', 'Thank you for your purchase!').center(width))

    if 'url' in data:
        lines.append(data['url'].center(width))

    return "\n".join(lines)


# ==============================================================================
# TIER 3: ASCII ART
# ==============================================================================

def generate_ascii_art(text: str, style: str = 'block') -> str:
    """
    Generate ASCII art text

    Args:
        text: Text to convert
        style: Art style ('block', 'banner', 'simple')

    Returns:
        ASCII art string
    """
    if style == 'block':
        # Block letters (simplified)
        return _block_letters(text)
    elif style == 'banner':
        return _banner_text(text)
    else:
        return text


def _block_letters(text: str) -> str:
    """Generate block letter ASCII art"""
    # Simplified block letters (only A-Z, 0-9)
    letters = {
        'A': ['  A  ', ' A A ', 'AAAAA', 'A   A', 'A   A'],
        'B': ['BBBB ', 'B   B', 'BBBB ', 'B   B', 'BBBB '],
        'C': [' CCC ', 'C   C', 'C    ', 'C   C', ' CCC '],
        'D': ['DDDD ', 'D   D', 'D   D', 'D   D', 'DDDD '],
        'E': ['EEEEE', 'E    ', 'EEEE ', 'E    ', 'EEEEE'],
        'F': ['FFFFF', 'F    ', 'FFFF ', 'F    ', 'F    '],
        'G': [' GGG ', 'G    ', 'G  GG', 'G   G', ' GGG '],
        'H': ['H   H', 'H   H', 'HHHHH', 'H   H', 'H   H'],
        'I': ['IIIII', '  I  ', '  I  ', '  I  ', 'IIIII'],
        'O': [' OOO ', 'O   O', 'O   O', 'O   O', ' OOO '],
        'S': [' SSS ', 'S    ', ' SSS ', '    S', ' SSS '],
        'U': ['U   U', 'U   U', 'U   U', 'U   U', ' UUU '],
        ' ': ['     ', '     ', '     ', '     ', '     '],
    }

    text = text.upper()
    lines = ['', '', '', '', '']

    for char in text:
        if char in letters:
            for i in range(5):
                lines[i] += letters[char][i] + ' '

    return '\n'.join(lines)


def _banner_text(text: str) -> str:
    """Generate banner text"""
    top = '╔' + '═' * (len(text) + 2) + '╗'
    mid = '║ ' + text + ' ║'
    bot = '╚' + '═' * (len(text) + 2) + '╝'
    return f"{top}\n{mid}\n{bot}"


# ==============================================================================
# TIER 4: PRINTER INTERFACE
# ==============================================================================

def print_to_thermal(receipt_text: str, printer_device: str = '/dev/usb/lp0'):
    """
    Send receipt to thermal printer

    Args:
        receipt_text: Receipt text to print
        printer_device: Printer device path

    Example:
        >>> receipt = generate_receipt(data)
        >>> print_to_thermal(receipt)
    """
    # This would send to an actual thermal printer
    # For now, just show how it would work

    try:
        with open(printer_device, 'w') as printer:
            printer.write(receipt_text)
            printer.write('\n\n\n')  # Feed paper
            printer.write('\x1b\x69')  # Cut command (ESC i)
        return True
    except Exception as e:
        print(f"⚠️  Thermal printer not available: {e}")
        print("📝 Receipt would be printed:\n")
        print(receipt_text)
        return False


def save_receipt_pdf(receipt_text: str, output_path: str = 'receipt.pdf'):
    """
    Save receipt as PDF (requires reportlab, but we'll generate HTML instead)

    Args:
        receipt_text: Receipt text
        output_path: Output file path

    Returns:
        Path to saved file
    """
    # Since we're zero-dependency, generate HTML instead
    # In production, use reportlab or weasyprint

    html_path = output_path.replace('.pdf', '.html')

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Receipt</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            width: 350px;
            margin: 20px auto;
            background: white;
        }}
        pre {{
            white-space: pre-wrap;
            margin: 0;
        }}
    </style>
</head>
<body>
    <pre>{receipt_text}</pre>
</body>
</html>'''

    with open(html_path, 'w') as f:
        f.write(html)

    print(f"✅ Receipt saved to {html_path}")
    print("💡 TIP: Open in browser and print to PDF")

    return html_path


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Printer (QR Codes & Receipts)\n")

    # Test 1: QR Code (ASCII)
    print("=" * 70)
    print("Test 1: ASCII QR Code")
    print("=" * 70)
    qr = generate_qr_ascii("https://soulfra.com/s/ABC123", size=1)
    print(qr)
    print()

    # Test 2: Receipt
    print("=" * 70)
    print("Test 2: Thermal Receipt")
    print("=" * 70)
    receipt = generate_receipt({
        'store_name': 'SOULFRA SHOP',
        'store_address': 'soulfra.com',
        'items': [
            {'name': 'Privacy T-Shirt', 'price': 25.00, 'qty': 1},
            {'name': 'Soulfra Sticker', 'price': 5.00, 'qty': 2},
        ],
        'subtotal': 35.00,
        'tax': 3.15,
        'total': 38.15,
        'payment_method': 'Credit Card',
        'transaction_id': 'TX-20231223-0042',
        'footer': 'Thank you for supporting privacy!',
        'url': 'https://soulfra.com'
    })
    print(receipt)
    print()

    # Test 3: ASCII Art
    print("=" * 70)
    print("Test 3: ASCII Art")
    print("=" * 70)
    art = generate_ascii_art("SOULFRA", style='block')
    print(art)
    print()

    banner = generate_ascii_art("HELLO WORLD", style='banner')
    print(banner)
    print()

    # Test 4: SVG QR Code
    print("=" * 70)
    print("Test 4: SVG QR Code")
    print("=" * 70)
    svg = generate_qr_svg("https://soulfra.com", size=200)
    with open('qr_test.svg', 'w') as f:
        f.write(svg)
    print("✅ SVG QR code saved to qr_test.svg")
    print()

    print("✅ Printer tests complete!")
    print("\n💡 NOTE: QR codes are simplified for teaching. Use qrcode library for production.")

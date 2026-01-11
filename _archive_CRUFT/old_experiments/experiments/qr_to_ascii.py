#!/usr/bin/env python3
"""
QR Code to ASCII Converter - Pure Python Stdlib

Converts QR code matrix to ASCII art for terminal display.
No PIL, no qrcode library - uses qr_encoder_stdlib.py for generation.

Usage:
    python3 qr_to_ascii.py "https://soulfra.com/soul/alice"

    # Or import
    from qr_to_ascii import qr_to_ascii
    print(qr_to_ascii("Hello World"))

Output:
    ██████████████  ████    ██████████████
    ██          ██  ██  ██  ██          ██
    ██  ██████  ██  ██████  ██  ██████  ██
    ...QR code as ASCII blocks!

Like:
- QR code generators but for terminal
- ASCII art but functional (scannable from screenshot!)
"""

import sys


def get_qr_matrix_from_bmp(bmp_data):
    """
    Extract QR code matrix from BMP image data

    Args:
        bmp_data: bytes from qr_encoder_stdlib.generate_qr_code()

    Returns:
        list[list[int]]: 2D matrix (0=black, 1=white)

    Parses BMP format to get pixel data
    """
    # BMP structure:
    # - File header: 14 bytes
    # - DIB header: 40 bytes
    # - Pixel data: starts at byte 54

    import struct

    # Read DIB header to get dimensions
    dib_header = bmp_data[14:54]
    width, height = struct.unpack('<ii', dib_header[4:12])

    # Calculate row size (padded to 4-byte boundary)
    row_size = (width * 3 + 3) // 4 * 4

    # Extract pixel data
    pixel_data_start = 54
    matrix = []

    for y in range(height - 1, -1, -1):  # BMP is bottom-to-top
        row = []
        row_start = pixel_data_start + (height - 1 - y) * row_size

        for x in range(width):
            pixel_offset = row_start + (x * 3)

            # Get RGB (BMP uses BGR)
            b = bmp_data[pixel_offset]
            g = bmp_data[pixel_offset + 1]
            r = bmp_data[pixel_offset + 2]

            # Black or white?
            brightness = (r + g + b) // 3
            pixel_value = 1 if brightness > 127 else 0  # 1=white, 0=black

            row.append(pixel_value)

        matrix.append(row)

    return matrix


def qr_to_ascii(data, block_char="█", empty_char=" ", scale=1):
    """
    Convert data to QR code ASCII art

    Args:
        data: String to encode
        block_char: Character for black modules (default: █)
        empty_char: Character for white modules (default: space)
        scale: How many chars per QR module (1, 2, or 3)

    Returns:
        str: ASCII art QR code

    Example:
        >>> print(qr_to_ascii("Hello"))
        ██████████████  ████    ██████████████
        ██          ██  ██  ██  ██          ██
        ...
    """
    # Generate QR code BMP using stdlib encoder
    from qr_encoder_stdlib import generate_qr_code

    bmp_data = generate_qr_code(data, scale=1)  # Generate minimal QR
    matrix = get_qr_matrix_from_bmp(bmp_data)

    # Sample matrix to reduce size (QR is scaled up)
    # Take every Nth pixel
    sample_rate = 10  # qr_encoder_stdlib uses scale=10 by default
    sampled_matrix = []

    for y in range(0, len(matrix), sample_rate):
        row = []
        for x in range(0, len(matrix[y]) if y < len(matrix) else 0, sample_rate):
            if y < len(matrix) and x < len(matrix[y]):
                row.append(matrix[y][x])
        if row:
            sampled_matrix.append(row)

    # Convert to ASCII
    ascii_lines = []

    for row in sampled_matrix:
        line = ""
        for pixel in row:
            # Each pixel → block_char or empty_char
            char = empty_char if pixel == 1 else block_char
            line += char * (2 * scale)  # 2 chars wide for square appearance
        ascii_lines.append(line)

    # Duplicate rows for vertical scaling
    if scale > 1:
        scaled_lines = []
        for line in ascii_lines:
            for _ in range(scale):
                scaled_lines.append(line)
        ascii_lines = scaled_lines

    return "\n".join(ascii_lines)


def qr_to_ascii_fancy(data):
    """
    Fancy ASCII QR with Unicode box-drawing characters

    Uses: ▀ ▄ █ for smoother appearance
    """
    return qr_to_ascii(data, block_char="█", empty_char="░", scale=1)


def qr_to_braille(data):
    """
    QR code using Braille characters (ultra-compact!)

    Each Braille char = 2x4 pixels
    Much smaller output than block chars
    """
    from qr_encoder_stdlib import generate_qr_code

    bmp_data = generate_qr_code(data, scale=1)
    matrix = get_qr_matrix_from_bmp(bmp_data)

    # Sample matrix
    sample_rate = 10
    sampled_matrix = []

    for y in range(0, len(matrix), sample_rate):
        row = []
        for x in range(0, len(matrix[y]) if y < len(matrix) else 0, sample_rate):
            if y < len(matrix) and x < len(matrix[y]):
                row.append(matrix[y][x])
        if row:
            sampled_matrix.append(row)

    # Braille pattern starts at U+2800
    # Each char encodes 2x4 pixels
    braille_lines = []

    for y in range(0, len(sampled_matrix), 4):
        line = ""
        for x in range(0, len(sampled_matrix[0]) if sampled_matrix else 0, 2):
            # Get 2x4 pixel block
            dots = 0
            for dy in range(4):
                for dx in range(2):
                    if (y + dy < len(sampled_matrix) and
                        x + dx < len(sampled_matrix[y + dy])):
                        if sampled_matrix[y + dy][x + dx] == 0:  # Black
                            # Map to Braille dot position
                            dot_map = [0, 3, 1, 4, 2, 5, 6, 7]
                            dot_index = dot_map[dy * 2 + dx]
                            dots |= (1 << dot_index)

            # Convert to Braille character
            braille_char = chr(0x2800 + dots)
            line += braille_char

        braille_lines.append(line)

    return "\n".join(braille_lines)


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 qr_to_ascii.py <data>")
        print()
        print("Examples:")
        print("  python3 qr_to_ascii.py 'Hello World'")
        print("  python3 qr_to_ascii.py 'https://soulfra.com/soul/alice'")
        print()
        sys.exit(1)

    data = sys.argv[1]

    print("=" * 60)
    print(f"QR Code for: {data}")
    print("=" * 60)
    print()

    # Standard ASCII
    print("📱 Standard (scannable from screenshot):")
    print()
    print(qr_to_ascii(data, scale=1))
    print()

    # Fancy variant
    print("=" * 60)
    print("✨ Fancy (with background):")
    print()
    print(qr_to_ascii_fancy(data))
    print()

    # Braille (ultra-compact)
    print("=" * 60)
    print("⠿ Braille (ultra-compact):")
    print()
    try:
        print(qr_to_braille(data))
    except Exception as e:
        print(f"(Braille rendering not supported: {e})")
    print()

    print("=" * 60)
    print("Scan the QR code above with your phone!")
    print("Or take a screenshot and scan that.")
    print("=" * 60)


if __name__ == '__main__':
    main()

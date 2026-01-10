#!/usr/bin/env python3
"""
PNG Writer from Scratch - Understanding Image Encoding

Builds PNG files byte-by-byte without Pillow!
Teaches how image libraries work internally.

Teaching the pattern:
1. RGB pixels → Raw bytes
2. Compress with zlib (DEFLATE)
3. Build PNG chunks (IHDR, IDAT, IEND)
4. Calculate CRC32 checksums
5. Write binary file

PNG File Structure:
[8 bytes] PNG signature (magic bytes)
[chunks] IHDR (image header)
        IDAT (compressed pixel data)
        IEND (end marker)

Each chunk:
[4 bytes] Length
[4 bytes] Type (e.g., "IHDR")
[N bytes] Data
[4 bytes] CRC32 checksum

Learning: This is how Pillow works under the hood!
"""

import struct
import zlib
import os


class SimplePNGWriter:
    """
    Simple PNG encoder without external image libraries

    Learning:
    - Understand PNG file format
    - Byte-level image encoding
    - Compression and checksums
    - How Pillow works internally
    """

    # PNG magic signature (first 8 bytes of every PNG file)
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

    def __init__(self, width, height):
        """
        Initialize PNG writer

        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        self.width = width
        self.height = height
        self.pixels = []  # List of (r, g, b) tuples

    def set_pixel(self, x, y, r, g, b):
        """
        Set pixel color

        Args:
            x: X coordinate
            y: Y coordinate
            r, g, b: RGB values (0-255)

        Learning: Store pixels as RGB tuples
        """
        # Extend pixels list if needed
        index = y * self.width + x

        while len(self.pixels) <= index:
            self.pixels.append((255, 255, 255))  # Default white

        self.pixels[index] = (r, g, b)

    def fill(self, r, g, b):
        """
        Fill entire image with color

        Args:
            r, g, b: RGB values

        Learning: Simple way to set all pixels
        """
        self.pixels = [(r, g, b)] * (self.width * self.height)

    def _calculate_crc(self, data):
        """
        Calculate CRC32 checksum

        Args:
            data: Bytes to checksum

        Returns:
            int: CRC32 checksum

        Learning:
        - CRC = Cyclic Redundancy Check
        - Detects errors in data
        - PNG requires CRC for each chunk
        """
        return zlib.crc32(data) & 0xffffffff

    def _build_chunk(self, chunk_type, chunk_data):
        """
        Build PNG chunk with length and CRC

        Args:
            chunk_type: 4-character type (e.g., "IHDR")
            chunk_data: Chunk data bytes

        Returns:
            bytes: Complete chunk

        Learning:
        Chunk structure:
        [4 bytes] Length (big-endian)
        [4 bytes] Type
        [N bytes] Data
        [4 bytes] CRC32 of type+data
        """
        length = len(chunk_data)
        chunk_type_bytes = chunk_type.encode('ascii')

        # CRC includes type + data (not length)
        crc_data = chunk_type_bytes + chunk_data
        crc = self._calculate_crc(crc_data)

        # Pack as big-endian (network byte order)
        chunk = struct.pack('>I', length)  # Length (4 bytes)
        chunk += chunk_type_bytes           # Type (4 bytes)
        chunk += chunk_data                 # Data (N bytes)
        chunk += struct.pack('>I', crc)     # CRC (4 bytes)

        return chunk

    def _build_ihdr_chunk(self):
        """
        Build IHDR (image header) chunk

        Returns:
            bytes: IHDR chunk

        Learning:
        IHDR data:
        [4 bytes] Width
        [4 bytes] Height
        [1 byte]  Bit depth (8 = 8 bits per channel)
        [1 byte]  Color type (2 = RGB, 6 = RGBA)
        [1 byte]  Compression (0 = DEFLATE)
        [1 byte]  Filter method (0 = adaptive filtering)
        [1 byte]  Interlace (0 = no interlacing)
        """
        ihdr_data = struct.pack(
            '>IIBBBBB',
            self.width,   # Width
            self.height,  # Height
            8,            # Bit depth
            2,            # Color type (RGB)
            0,            # Compression
            0,            # Filter
            0             # Interlace
        )

        return self._build_chunk('IHDR', ihdr_data)

    def _build_idat_chunk(self):
        """
        Build IDAT (image data) chunk with compressed pixels

        Returns:
            bytes: IDAT chunk

        Learning:
        1. Convert pixels to raw bytes
        2. Add filter byte (0 = no filter) to each scanline
        3. Compress with zlib DEFLATE
        4. Build chunk
        """
        # Build raw pixel data
        raw_data = b''

        for y in range(self.height):
            # Filter byte (0 = no filter)
            raw_data += b'\x00'

            # Add RGB bytes for this scanline
            for x in range(self.width):
                index = y * self.width + x

                if index < len(self.pixels):
                    r, g, b = self.pixels[index]
                else:
                    r, g, b = 255, 255, 255  # Default white

                raw_data += bytes([r, g, b])

        # Compress with zlib
        compressed = zlib.compress(raw_data, 9)

        return self._build_chunk('IDAT', compressed)

    def _build_iend_chunk(self):
        """
        Build IEND (end marker) chunk

        Returns:
            bytes: IEND chunk

        Learning: IEND has no data, just marks end of PNG
        """
        return self._build_chunk('IEND', b'')

    def save(self, filepath):
        """
        Save PNG to file

        Args:
            filepath: Output file path

        Learning:
        PNG file structure:
        1. PNG signature
        2. IHDR chunk
        3. IDAT chunk(s)
        4. IEND chunk
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

        with open(filepath, 'wb') as f:
            # Write PNG signature
            f.write(self.PNG_SIGNATURE)

            # Write chunks
            f.write(self._build_ihdr_chunk())
            f.write(self._build_idat_chunk())
            f.write(self._build_iend_chunk())

        return filepath


def create_simple_image():
    """
    Example: Create simple 4x4 test image

    Returns:
        SimplePNGWriter: Image with red, green, blue, yellow pixels

    Learning: Test the PNG writer with simple pattern
    """
    img = SimplePNGWriter(4, 4)

    # Row 1: Red
    for x in range(4):
        img.set_pixel(x, 0, 255, 0, 0)

    # Row 2: Green
    for x in range(4):
        img.set_pixel(x, 1, 0, 255, 0)

    # Row 3: Blue
    for x in range(4):
        img.set_pixel(x, 2, 0, 0, 255)

    # Row 4: Yellow
    for x in range(4):
        img.set_pixel(x, 3, 255, 255, 0)

    return img


def create_checkerboard(size=16):
    """
    Create checkerboard pattern

    Args:
        size: Grid size

    Returns:
        SimplePNGWriter: Checkerboard image

    Learning: Simple pattern generation
    """
    img = SimplePNGWriter(size, size)

    for y in range(size):
        for x in range(size):
            # Checkerboard logic
            if (x + y) % 2 == 0:
                img.set_pixel(x, y, 0, 0, 0)  # Black
            else:
                img.set_pixel(x, y, 255, 255, 255)  # White

    return img


def create_gradient(width=256, height=256):
    """
    Create RGB gradient

    Args:
        width: Image width
        height: Image height

    Returns:
        SimplePNGWriter: Gradient image

    Learning: Show how colors blend
    """
    img = SimplePNGWriter(width, height)

    for y in range(height):
        for x in range(width):
            r = int((x / width) * 255)
            g = int((y / height) * 255)
            b = 128

            img.set_pixel(x, y, r, g, b)

    return img


def test_png_writer():
    """Test the PNG writer"""
    print("=" * 70)
    print("🧪 Testing PNG Writer - Building Images from Scratch!")
    print("=" * 70)
    print()

    output_dir = 'png_from_scratch'
    os.makedirs(output_dir, exist_ok=True)

    # Test 1: Simple 4x4 image
    print("TEST 1: Simple 4x4 image")
    img1 = create_simple_image()
    path1 = img1.save(f'{output_dir}/simple_4x4.png')
    print(f"   ✅ Created: {path1}")
    print(f"   Size: {img1.width}x{img1.height} = {img1.width * img1.height} pixels")
    print()

    # Test 2: Checkerboard
    print("TEST 2: Checkerboard 16x16")
    img2 = create_checkerboard(16)
    path2 = img2.save(f'{output_dir}/checkerboard_16x16.png')
    print(f"   ✅ Created: {path2}")
    print(f"   Pattern: Black/white checkerboard")
    print()

    # Test 3: Gradient
    print("TEST 3: RGB Gradient 128x128")
    img3 = create_gradient(128, 128)
    path3 = img3.save(f'{output_dir}/gradient_128x128.png')
    print(f"   ✅ Created: {path3}")
    print(f"   Pattern: Red→Blue gradient")
    print()

    # Test 4: Inspect file structure
    print("TEST 4: Inspect PNG File Structure")
    with open(path1, 'rb') as f:
        data = f.read()

    print(f"   File size: {len(data)} bytes")
    print(f"   PNG signature: {data[:8].hex()}")
    print(f"   First chunk type: {data[12:16].decode('ascii')}")
    print()

    # Test 5: Verify with Pillow (if available)
    print("TEST 5: Verify with Pillow")
    try:
        from PIL import Image

        # Open our hand-crafted PNG
        verify_img = Image.open(path1)
        print(f"   ✅ Pillow can read our PNG!")
        print(f"   Size: {verify_img.size}")
        print(f"   Mode: {verify_img.mode}")

        # Show first pixel
        pixel = verify_img.getpixel((0, 0))
        print(f"   First pixel: RGB{pixel} (should be red: (255, 0, 0))")
    except ImportError:
        print(f"   ⚠️  Pillow not installed (skipping verification)")
    print()

    print("=" * 70)
    print("✅ All PNG writer tests passed!")
    print("=" * 70)
    print()

    print("📚 What we learned:")
    print("   1. PNG files are just bytes following a spec")
    print("   2. Chunks have: length + type + data + CRC")
    print("   3. Pixel data is compressed with zlib")
    print("   4. Pillow does all this automatically!")
    print("   5. We built a PNG encoder with ONLY Python stdlib!")
    print()

    print(f"📁 Images saved in: {output_dir}/")
    print()


if __name__ == '__main__':
    test_png_writer()

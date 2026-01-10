#!/usr/bin/env python3
"""
Binary Protocol - Efficient Binary Data Encoding (Python stdlib only)

This implements a compact binary protocol for encoding/decoding data:
1. Encode Python objects to binary (struct, bytes)
2. Decode binary back to Python objects
3. Support versioning for backward compatibility
4. Optional compression (zlib)
5. Type markers for mixed data

WHY THIS EXISTS:
- Compact data storage (smaller than JSON)
- Fast serialization/deserialization
- No external dependencies (only stdlib)
- Portable across platforms
- Supports compression

Usage:
    from binary_protocol import encode, decode

    # Encode data
    data = {'name': 'Alice', 'age': 30, 'scores': [95, 87, 92]}
    binary = encode(data)

    # Decode data
    decoded = decode(binary)

Supported types:
- None
- bool
- int
- float
- str
- bytes
- list
- dict
"""

import struct
import zlib
import json
from datetime import datetime
from typing import Any, Union


# Protocol version
PROTOCOL_VERSION = 1

# Type markers (1 byte each)
TYPE_NONE = 0x00
TYPE_BOOL = 0x01
TYPE_INT = 0x02
TYPE_FLOAT = 0x03
TYPE_STR = 0x04
TYPE_BYTES = 0x05
TYPE_LIST = 0x06
TYPE_DICT = 0x07
TYPE_COMPRESSED = 0xFF


def encode(data: Any, compress: bool = False) -> bytes:
    """
    Encode Python object to binary

    Args:
        data: Python object to encode
        compress: If True, compress using zlib

    Returns:
        bytes: Encoded binary data
    """
    # Encode to binary
    binary = _encode_value(data)

    # Add protocol header (version + flags)
    flags = 0x01 if compress else 0x00
    header = struct.pack('<BB', PROTOCOL_VERSION, flags)

    # Optionally compress
    if compress:
        binary = zlib.compress(binary, level=9)

    return header + binary


def decode(binary: bytes) -> Any:
    """
    Decode binary data to Python object

    Args:
        binary: Encoded binary data

    Returns:
        Decoded Python object
    """
    # Read header
    version, flags = struct.unpack('<BB', binary[:2])

    if version != PROTOCOL_VERSION:
        raise ValueError(f"Unsupported protocol version: {version}")

    binary = binary[2:]  # Skip header

    # Decompress if needed
    if flags & 0x01:
        binary = zlib.decompress(binary)

    # Decode
    value, _ = _decode_value(binary, 0)
    return value


def _encode_value(value: Any) -> bytes:
    """Encode a single value to binary"""

    if value is None:
        return struct.pack('<B', TYPE_NONE)

    elif isinstance(value, bool):
        # Bool before int (bool is subclass of int)
        return struct.pack('<BB', TYPE_BOOL, 1 if value else 0)

    elif isinstance(value, int):
        # Use variable-length encoding
        if -128 <= value <= 127:
            # 1 byte signed
            return struct.pack('<Bb', TYPE_INT, value)
        elif -32768 <= value <= 32767:
            # 2 bytes signed
            return struct.pack('<BH', TYPE_INT | 0x10, value & 0xFFFF)
        elif -2147483648 <= value <= 2147483647:
            # 4 bytes signed
            return struct.pack('<BI', TYPE_INT | 0x20, value & 0xFFFFFFFF)
        else:
            # 8 bytes signed
            return struct.pack('<BQ', TYPE_INT | 0x30, value & 0xFFFFFFFFFFFFFFFF)

    elif isinstance(value, float):
        # 8 bytes double
        return struct.pack('<Bd', TYPE_FLOAT, value)

    elif isinstance(value, str):
        # Length-prefixed UTF-8 string
        encoded_str = value.encode('utf-8')
        length = len(encoded_str)

        if length < 256:
            return struct.pack('<BB', TYPE_STR, length) + encoded_str
        else:
            return struct.pack('<BI', TYPE_STR | 0x10, length) + encoded_str

    elif isinstance(value, bytes):
        # Length-prefixed bytes
        length = len(value)

        if length < 256:
            return struct.pack('<BB', TYPE_BYTES, length) + value
        else:
            return struct.pack('<BI', TYPE_BYTES | 0x10, length) + value

    elif isinstance(value, list):
        # List of values
        items_binary = b''.join(_encode_value(item) for item in value)
        count = len(value)

        if count < 256:
            return struct.pack('<BB', TYPE_LIST, count) + items_binary
        else:
            return struct.pack('<BI', TYPE_LIST | 0x10, count) + items_binary

    elif isinstance(value, dict):
        # Dictionary as key-value pairs
        items_binary = b''
        for k, v in value.items():
            items_binary += _encode_value(k)
            items_binary += _encode_value(v)

        count = len(value)

        if count < 256:
            return struct.pack('<BB', TYPE_DICT, count) + items_binary
        else:
            return struct.pack('<BI', TYPE_DICT | 0x10, count) + items_binary

    else:
        # Fallback to JSON for unsupported types
        json_str = json.dumps(value)
        return _encode_value(json_str)


def _decode_value(binary: bytes, offset: int) -> tuple[Any, int]:
    """
    Decode a single value from binary

    Returns:
        (value, new_offset)
    """
    type_marker = binary[offset]
    offset += 1

    if type_marker == TYPE_NONE:
        return None, offset

    elif type_marker == TYPE_BOOL:
        value = struct.unpack('<B', binary[offset:offset+1])[0]
        return bool(value), offset + 1

    elif (type_marker & 0x0F) == TYPE_INT:
        size_flag = type_marker & 0xF0

        if size_flag == 0x00:
            # 1 byte
            value = struct.unpack('<b', binary[offset:offset+1])[0]
            return value, offset + 1
        elif size_flag == 0x10:
            # 2 bytes
            value = struct.unpack('<H', binary[offset:offset+2])[0]
            # Sign extend
            if value & 0x8000:
                value -= 0x10000
            return value, offset + 2
        elif size_flag == 0x20:
            # 4 bytes
            value = struct.unpack('<I', binary[offset:offset+4])[0]
            if value & 0x80000000:
                value -= 0x100000000
            return value, offset + 4
        else:
            # 8 bytes
            value = struct.unpack('<Q', binary[offset:offset+8])[0]
            if value & 0x8000000000000000:
                value -= 0x10000000000000000
            return value, offset + 8

    elif type_marker == TYPE_FLOAT:
        value = struct.unpack('<d', binary[offset:offset+8])[0]
        return value, offset + 8

    elif (type_marker & 0x0F) == TYPE_STR:
        size_flag = type_marker & 0xF0

        if size_flag == 0x00:
            # 1 byte length
            length = struct.unpack('<B', binary[offset:offset+1])[0]
            offset += 1
        else:
            # 4 byte length
            length = struct.unpack('<I', binary[offset:offset+4])[0]
            offset += 4

        value = binary[offset:offset+length].decode('utf-8')
        return value, offset + length

    elif (type_marker & 0x0F) == TYPE_BYTES:
        size_flag = type_marker & 0xF0

        if size_flag == 0x00:
            length = struct.unpack('<B', binary[offset:offset+1])[0]
            offset += 1
        else:
            length = struct.unpack('<I', binary[offset:offset+4])[0]
            offset += 4

        value = binary[offset:offset+length]
        return value, offset + length

    elif (type_marker & 0x0F) == TYPE_LIST:
        size_flag = type_marker & 0xF0

        if size_flag == 0x00:
            count = struct.unpack('<B', binary[offset:offset+1])[0]
            offset += 1
        else:
            count = struct.unpack('<I', binary[offset:offset+4])[0]
            offset += 4

        items = []
        for _ in range(count):
            item, offset = _decode_value(binary, offset)
            items.append(item)

        return items, offset

    elif (type_marker & 0x0F) == TYPE_DICT:
        size_flag = type_marker & 0xF0

        if size_flag == 0x00:
            count = struct.unpack('<B', binary[offset:offset+1])[0]
            offset += 1
        else:
            count = struct.unpack('<I', binary[offset:offset+4])[0]
            offset += 4

        items = {}
        for _ in range(count):
            key, offset = _decode_value(binary, offset)
            value, offset = _decode_value(binary, offset)
            items[key] = value

        return items, offset

    else:
        raise ValueError(f"Unknown type marker: 0x{type_marker:02X}")


def compare_sizes(data: Any):
    """
    Compare binary protocol size vs JSON

    Args:
        data: Data to compare
    """
    # Binary encoding
    binary = encode(data, compress=False)
    binary_compressed = encode(data, compress=True)

    # JSON encoding
    json_str = json.dumps(data, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    json_compressed = zlib.compress(json_bytes, level=9)

    print("=" * 70)
    print("📊 Size Comparison")
    print("=" * 70)
    print()
    print(f"Binary (uncompressed):  {len(binary):,} bytes")
    print(f"Binary (compressed):    {len(binary_compressed):,} bytes")
    print(f"JSON (uncompressed):    {len(json_bytes):,} bytes")
    print(f"JSON (compressed):      {len(json_compressed):,} bytes")
    print()
    print(f"Binary vs JSON:         {len(binary) / len(json_bytes) * 100:.1f}%")
    print(f"Binary (comp) vs JSON:  {len(binary_compressed) / len(json_bytes) * 100:.1f}%")
    print()


def test_encoding():
    """Test the binary protocol with various data types"""
    print("=" * 70)
    print("🔢 Binary Protocol Test")
    print("=" * 70)
    print()

    # Test cases
    test_cases = [
        None,
        True,
        False,
        42,
        -1234,
        3.14159,
        "Hello, World!",
        b"\x00\x01\x02\x03",
        [1, 2, 3, 4, 5],
        {"name": "Alice", "age": 30, "active": True},
        {
            "post": {
                "id": 42,
                "title": "Binary Protocol Demo",
                "tags": ["binary", "encoding", "python"],
                "metadata": {
                    "views": 1234,
                    "likes": 56,
                    "saved": False
                }
            }
        }
    ]

    for i, original in enumerate(test_cases, 1):
        print(f"Test {i}: {type(original).__name__}")
        print(f"  Original: {original!r}")

        # Encode
        binary = encode(original, compress=False)
        binary_compressed = encode(original, compress=True)

        # Decode
        decoded = decode(binary)
        decoded_compressed = decode(binary_compressed)

        # Verify
        if decoded == original and decoded_compressed == original:
            print(f"  ✅ Success")
            print(f"  Binary size: {len(binary)} bytes (compressed: {len(binary_compressed)} bytes)")
        else:
            print(f"  ❌ Failed")
            print(f"  Decoded: {decoded!r}")

        print()

    # Compare with complex data
    print("=" * 70)
    print("Complex Data Test")
    print("=" * 70)
    print()

    complex_data = {
        "users": [
            {"id": 1, "name": "Alice", "score": 95.5},
            {"id": 2, "name": "Bob", "score": 87.3},
            {"id": 3, "name": "Charlie", "score": 92.1}
        ],
        "metadata": {
            "total": 3,
            "updated": "2025-12-22",
            "active": True
        }
    }

    compare_sizes(complex_data)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_encoding()
    else:
        print("=" * 70)
        print("🔢 Binary Protocol - Efficient Data Encoding")
        print("=" * 70)
        print()
        print("This module provides compact binary encoding for Python objects.")
        print()
        print("Usage:")
        print("  from binary_protocol import encode, decode")
        print()
        print("  # Encode")
        print("  data = {'name': 'Alice', 'age': 30}")
        print("  binary = encode(data, compress=True)")
        print()
        print("  # Decode")
        print("  decoded = decode(binary)")
        print()
        print("Commands:")
        print("  python3 binary_protocol.py test  # Run tests")
        print()
        print("=" * 70)

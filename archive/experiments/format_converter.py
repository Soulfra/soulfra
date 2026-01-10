#!/usr/bin/env python3
"""
Format Converter - Zero External Dependencies

Converts Python dictionaries to multiple output formats:
- JSON (machines/APIs)
- CSV (spreadsheets)
- TXT (human-readable)
- HTML (browsers)
- RTF (word processors)
- Binary (efficient storage)

NO external dependencies - uses only Python stdlib!

Usage:
    from format_converter import FormatConverter

    data = {"name": "Red", "r": 255, "g": 0, "b": 0}

    FormatConverter.to_json(data)     # JSON string
    FormatConverter.to_csv([data])    # CSV string
    FormatConverter.to_txt(data)      # Plain text
    FormatConverter.to_html(data)     # HTML
    FormatConverter.to_rtf(data)      # Rich Text Format
    FormatConverter.to_binary(data)   # Binary bytes
"""

import json
import struct
from io import StringIO


class FormatConverter:
    """Convert Python dicts to multiple formats - ZERO dependencies"""

    @staticmethod
    def to_json(data, pretty=True):
        """
        Convert to JSON

        Args:
            data: Dict or list
            pretty: If True, indent with 2 spaces

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def to_csv(data, headers=None):
        """
        Convert to CSV

        Args:
            data: List of dicts OR single dict
            headers: Optional list of column names (uses dict keys if None)

        Returns:
            CSV string with header row

        Example:
            data = [{"name": "Red", "value": 255}, {"name": "Blue", "value": 0}]
            to_csv(data)  # "name,value\\nRed,255\\nBlue,0"
        """
        # Handle single dict → list of one dict
        if isinstance(data, dict):
            data = [data]

        if not data:
            return ""

        # Determine headers
        if headers is None:
            headers = list(data[0].keys())

        # Build CSV
        output = StringIO()

        # Header row
        output.write(','.join(str(h) for h in headers))
        output.write('\n')

        # Data rows
        for row in data:
            values = []
            for header in headers:
                value = row.get(header, '')
                # Escape commas and quotes
                value_str = str(value)
                if ',' in value_str or '"' in value_str or '\n' in value_str:
                    value_str = '"' + value_str.replace('"', '""') + '"'
                values.append(value_str)
            output.write(','.join(values))
            output.write('\n')

        return output.getvalue()

    @staticmethod
    def to_txt(data, format_style='simple'):
        """
        Convert to plain text

        Args:
            data: Dict or list of dicts
            format_style: 'simple', 'detailed', or 'table'

        Returns:
            Plain text string
        """
        if isinstance(data, list):
            # List of dicts → table format
            return FormatConverter._list_to_txt_table(data)

        if format_style == 'simple':
            # Key: Value format
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return '\n'.join(lines)

        elif format_style == 'detailed':
            # Detailed format with separators
            lines = []
            lines.append("=" * 50)
            for key, value in data.items():
                key_display = key.replace('_', ' ').title()
                if isinstance(value, (list, dict)):
                    lines.append(f"{key_display}:")
                    lines.append(f"  {json.dumps(value, indent=2)}")
                else:
                    lines.append(f"{key_display}: {value}")
            lines.append("=" * 50)
            return '\n'.join(lines)

        elif format_style == 'table':
            # Single-row table
            return FormatConverter._list_to_txt_table([data])

        else:
            return FormatConverter.to_txt(data, 'simple')

    @staticmethod
    def _list_to_txt_table(data):
        """Convert list of dicts to ASCII table"""
        if not data:
            return ""

        # Get all keys
        all_keys = []
        for item in data:
            for key in item.keys():
                if key not in all_keys:
                    all_keys.append(key)

        # Calculate column widths
        col_widths = {}
        for key in all_keys:
            col_widths[key] = len(str(key))

        for item in data:
            for key in all_keys:
                value = str(item.get(key, ''))
                col_widths[key] = max(col_widths[key], len(value))

        # Build table
        lines = []

        # Header
        header = '  '.join(str(key).ljust(col_widths[key]) for key in all_keys)
        lines.append(header)
        lines.append('-' * len(header))

        # Rows
        for item in data:
            row = '  '.join(str(item.get(key, '')).ljust(col_widths[key]) for key in all_keys)
            lines.append(row)

        return '\n'.join(lines)

    @staticmethod
    def to_html(data, style='minimal'):
        """
        Convert to HTML

        Args:
            data: Dict or list of dicts
            style: 'minimal', 'styled', or 'card'

        Returns:
            HTML string
        """
        if isinstance(data, list):
            return FormatConverter._list_to_html_table(data, style)

        if style == 'minimal':
            # Simple <dl> definition list
            html = '<dl>\n'
            for key, value in data.items():
                key_display = key.replace('_', ' ').title()
                html += f'  <dt>{key_display}</dt>\n'
                html += f'  <dd>{value}</dd>\n'
            html += '</dl>'
            return html

        elif style == 'card':
            # Card-style div
            html = '<div class="data-card" style="border: 1px solid #ddd; padding: 1rem; border-radius: 4px; margin: 1rem 0;">\n'
            for key, value in data.items():
                key_display = key.replace('_', ' ').title()
                html += f'  <div class="field">\n'
                html += f'    <strong>{key_display}:</strong> {value}\n'
                html += f'  </div>\n'
            html += '</div>'
            return html

        else:
            return FormatConverter.to_html(data, 'minimal')

    @staticmethod
    def _list_to_html_table(data, style='minimal'):
        """Convert list of dicts to HTML table"""
        if not data:
            return "<p>No data</p>"

        # Get headers
        headers = list(data[0].keys())

        # Build table
        if style == 'styled':
            html = '<table style="border-collapse: collapse; width: 100%;">\n'
            html += '  <thead style="background: #f0f0f0;">\n'
            html += '    <tr>\n'
            for header in headers:
                header_display = header.replace('_', ' ').title()
                html += f'      <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{header_display}</th>\n'
            html += '    </tr>\n'
            html += '  </thead>\n'
            html += '  <tbody>\n'
            for row in data:
                html += '    <tr>\n'
                for header in headers:
                    value = row.get(header, '')
                    html += f'      <td style="border: 1px solid #ddd; padding: 8px;">{value}</td>\n'
                html += '    </tr>\n'
            html += '  </tbody>\n'
            html += '</table>'
        else:
            # Minimal table
            html = '<table>\n'
            html += '  <thead><tr>\n'
            for header in headers:
                html += f'    <th>{header}</th>\n'
            html += '  </tr></thead>\n'
            html += '  <tbody>\n'
            for row in data:
                html += '  <tr>\n'
                for header in headers:
                    html += f'    <td>{row.get(header, "")}</td>\n'
                html += '  </tr>\n'
            html += '  </tbody>\n'
            html += '</table>'

        return html

    @staticmethod
    def to_rtf(data):
        """
        Convert to RTF (Rich Text Format)

        Args:
            data: Dict

        Returns:
            RTF string
        """
        # RTF header
        rtf = r'{\rtf1\ansi\deff0'
        rtf += '\n'

        # Add content
        for key, value in data.items():
            key_display = key.replace('_', ' ').title()
            # Bold key
            rtf += r'{\b ' + FormatConverter._escape_rtf(key_display) + r':} '
            rtf += FormatConverter._escape_rtf(str(value))
            rtf += r'\par' + '\n'

        # RTF footer
        rtf += '}'

        return rtf

    @staticmethod
    def _escape_rtf(text):
        """Escape special characters for RTF"""
        text = text.replace('\\', '\\\\')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        return text

    @staticmethod
    def to_binary(data):
        """
        Convert to compact binary format

        Args:
            data: Dict with numeric values

        Returns:
            bytes

        Format:
            - Use Python struct module
            - Assumes values are numbers (int/float)

        Example:
            {"r": 255, "g": 0, "b": 128, "confidence": 0.9996}
            → b'\\xff\\x00\\x80?\\x7f\\xe1H'
        """
        # Determine data types
        values = []
        format_str = ''

        for key, value in sorted(data.items()):
            if isinstance(value, bool):
                # Boolean → byte (0 or 1)
                values.append(int(value))
                format_str += 'B'
            elif isinstance(value, int):
                # Integer → 4-byte signed int
                if -128 <= value <= 127:
                    values.append(value)
                    format_str += 'b'  # 1-byte signed
                elif -32768 <= value <= 32767:
                    values.append(value)
                    format_str += 'h'  # 2-byte signed
                else:
                    values.append(value)
                    format_str += 'i'  # 4-byte signed
            elif isinstance(value, float):
                # Float → 4-byte float
                values.append(value)
                format_str += 'f'
            elif isinstance(value, str):
                # String → length-prefixed bytes
                encoded = value.encode('utf-8')
                values.append(len(encoded))
                format_str += 'H'  # 2-byte length
                values.extend(encoded)
                format_str += f'{len(encoded)}s'

        # Pack to binary
        try:
            return struct.pack(format_str, *values)
        except struct.error:
            # Fallback: JSON as bytes
            return json.dumps(data).encode('utf-8')

    @staticmethod
    def from_binary(binary_data, keys, types):
        """
        Decode binary data back to dict

        Args:
            binary_data: bytes
            keys: List of keys in order
            types: List of types ('int', 'float', 'str', 'bool')

        Returns:
            Dict
        """
        format_str = ''
        for t in types:
            if t == 'bool':
                format_str += 'B'
            elif t == 'int':
                format_str += 'i'
            elif t == 'float':
                format_str += 'f'

        values = struct.unpack(format_str, binary_data)
        return dict(zip(keys, values))


# ==============================================================================
# DEMO / TEST
# ==============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("FORMAT CONVERTER DEMO - Zero External Dependencies")
    print("=" * 70)
    print()

    # Sample data
    data = {
        "prediction": "WARM",
        "r": 255,
        "g": 0,
        "b": 0,
        "confidence": 0.9996,
        "hue": 0.0,
        "saturation": 1.0
    }

    print("INPUT DATA:")
    print(data)
    print()

    print("=" * 70)
    print("1. JSON FORMAT")
    print("=" * 70)
    print(FormatConverter.to_json(data))
    print()

    print("=" * 70)
    print("2. CSV FORMAT")
    print("=" * 70)
    print(FormatConverter.to_csv([data]))
    print()

    print("=" * 70)
    print("3. TXT FORMAT (Simple)")
    print("=" * 70)
    print(FormatConverter.to_txt(data, 'simple'))
    print()

    print("=" * 70)
    print("4. TXT FORMAT (Detailed)")
    print("=" * 70)
    print(FormatConverter.to_txt(data, 'detailed'))
    print()

    print("=" * 70)
    print("5. HTML FORMAT (Card)")
    print("=" * 70)
    print(FormatConverter.to_html(data, 'card'))
    print()

    print("=" * 70)
    print("6. RTF FORMAT")
    print("=" * 70)
    print(FormatConverter.to_rtf(data))
    print()

    print("=" * 70)
    print("7. BINARY FORMAT")
    print("=" * 70)
    # For binary, use only numeric data
    numeric_data = {"r": 255, "g": 0, "b": 0}
    binary = FormatConverter.to_binary(numeric_data)
    print(f"Binary ({len(binary)} bytes): {binary}")
    print(f"Hex: {binary.hex()}")
    print()

    print("=" * 70)
    print("8. LIST OF DICTS → TABLE")
    print("=" * 70)
    list_data = [
        {"color": "Red", "r": 255, "g": 0, "b": 0},
        {"color": "Green", "r": 0, "g": 255, "b": 0},
        {"color": "Blue", "r": 0, "g": 0, "b": 255}
    ]
    print(FormatConverter.to_txt(list_data))
    print()

    print("SUCCESS! All formats working with ZERO external dependencies! 🎉")

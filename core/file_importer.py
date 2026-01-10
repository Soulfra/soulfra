#!/usr/bin/env python3
"""
File Importer - Multi-Format Content Import System

Import files in various formats and convert to standardized markdown:
- Text: txt, rtf
- Markdown: md, mdx, markdown
- HTML: html, htm
- Documents: doc, docx (requires python-docx)
- Data: json, yaml, csv
- Code: py, js, ts, jsx, tsx

**The Flow:**
1. User uploads file
2. System detects format
3. Convert to markdown (if needed)
4. Parse frontmatter for metadata
5. Route to @brand/category
6. Save to database
7. Generate QR code
8. Return success with route info

**Usage:**
```python
from file_importer import FileImporter

importer = FileImporter()

# Import a file
result = importer.import_file(
    file_path='uploads/privacy-guide.md',
    brand='soulfra',
    category='blog',
    user_id=15
)

# Returns:
{
    'route': '@soulfra/blog/privacy-guide',
    'url': '/brands/soulfra/blog/privacy-guide',
    'qr_code': 'data:image/png;base64,...',
    'file_id': 42
}
```

**Environment Variables:**
- BRANDS_DIR: Base directory for brand folders (default: ./brands)
- QR_OUTPUT_DIR: Directory for QR codes (default: ./static/qr)
"""

import os
import re
import json
import mimetypes
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import sqlite3

# Optional dependencies
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import markdown2
    HAS_MARKDOWN2 = True
except ImportError:
    HAS_MARKDOWN2 = False

from database import get_db


# ==============================================================================
# CONFIG
# ==============================================================================

BRANDS_DIR = os.environ.get('BRANDS_DIR', './brands')
QR_OUTPUT_DIR = os.environ.get('QR_OUTPUT_DIR', './static/qr')

# Supported file formats
SUPPORTED_FORMATS = {
    'text': ['txt', 'rtf', 'text'],
    'markdown': ['md', 'mdx', 'markdown'],
    'html': ['html', 'htm'],
    'doc': ['doc', 'docx'],
    'data': ['json', 'yaml', 'yml', 'toml', 'csv'],
    'code': ['py', 'js', 'ts', 'jsx', 'tsx', 'go', 'rs', 'java', 'c', 'cpp', 'h']
}

# Max file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


# ==============================================================================
# FILE IMPORTER CLASS
# ==============================================================================

class FileImporter:
    """
    Import and process files in multiple formats
    """

    def __init__(self, brands_dir: str = BRANDS_DIR, qr_dir: str = QR_OUTPUT_DIR):
        self.brands_dir = Path(brands_dir)
        self.qr_dir = Path(qr_dir)

        # Ensure directories exist
        self.brands_dir.mkdir(parents=True, exist_ok=True)
        self.qr_dir.mkdir(parents=True, exist_ok=True)


    # ==========================================================================
    # MAIN IMPORT FUNCTION
    # ==========================================================================

    def import_file(
        self,
        file_path: str,
        brand: str,
        category: str,
        user_id: int,
        subcategory: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Import a file into the system

        Args:
            file_path: Path to uploaded file
            brand: Brand name (e.g., 'soulfra')
            category: Category (e.g., 'blog')
            user_id: User ID who uploaded
            subcategory: Optional subcategory
            metadata: Optional metadata override

        Returns:
            Dict with import results

        Example:
            >>> importer = FileImporter()
            >>> result = importer.import_file(
            ...     file_path='uploads/post.md',
            ...     brand='soulfra',
            ...     category='blog',
            ...     user_id=15
            ... )
            >>> print(result['route'])
            @soulfra/blog/post
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")

        # Detect format
        file_format = self._detect_format(file_path)

        # Convert to markdown
        markdown_content, extracted_metadata = self._convert_to_markdown(
            file_path,
            file_format
        )

        # Merge metadata
        final_metadata = metadata or {}
        final_metadata.update(extracted_metadata)

        # Generate filename (slug)
        filename = final_metadata.get('slug') or self._generate_slug(
            final_metadata.get('title', file_path.stem)
        )

        # Build route
        route_parts = [f'@{brand}', category]
        if subcategory:
            route_parts.append(subcategory)
        route_parts.append(filename)

        route = '/'.join(route_parts)

        # Save to brand folder
        brand_file_path = self._save_to_brand_folder(
            brand, category, filename, markdown_content, subcategory
        )

        # Save to database
        file_id = self._save_to_database(
            user_id=user_id,
            route=route,
            brand=brand,
            category=category,
            subcategory=subcategory,
            filename=filename,
            file_path=str(brand_file_path),
            file_type=file_format,
            file_size=file_size,
            metadata=final_metadata
        )

        # Generate QR code
        qr_code_path = self._generate_qr_code(route, filename)

        return {
            'success': True,
            'file_id': file_id,
            'route': route,
            'url': f'/brands/{brand}/{category}/{subcategory}/{filename}' if subcategory else f'/brands/{brand}/{category}/{filename}',
            'brand_file_path': str(brand_file_path),
            'qr_code': qr_code_path,
            'metadata': final_metadata
        }


    # ==========================================================================
    # FORMAT DETECTION
    # ==========================================================================

    def _detect_format(self, file_path: Path) -> str:
        """
        Detect file format from extension and MIME type

        Args:
            file_path: Path to file

        Returns:
            Format string (e.g., 'markdown', 'html')
        """
        extension = file_path.suffix.lstrip('.').lower()

        # Check against supported formats
        for format_type, extensions in SUPPORTED_FORMATS.items():
            if extension in extensions:
                return format_type

        # Fallback: try MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if 'text' in mime_type:
                return 'text'
            elif 'html' in mime_type:
                return 'html'
            elif 'json' in mime_type:
                return 'data'

        # Default to text
        return 'text'


    # ==========================================================================
    # FORMAT CONVERSION
    # ==========================================================================

    def _convert_to_markdown(self, file_path: Path, file_format: str) -> Tuple[str, Dict]:
        """
        Convert file to markdown format

        Args:
            file_path: Path to file
            file_format: Detected format

        Returns:
            (markdown_content, metadata_dict)
        """
        converters = {
            'text': self._convert_text,
            'markdown': self._convert_markdown,
            'html': self._convert_html,
            'doc': self._convert_doc,
            'data': self._convert_data,
            'code': self._convert_code,
        }

        converter = converters.get(file_format, self._convert_text)
        return converter(file_path)


    def _convert_text(self, file_path: Path) -> Tuple[str, Dict]:
        """Convert plain text to markdown"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Try to extract metadata from first lines
        metadata = {}
        lines = content.split('\n')

        # Check for title in first line
        if lines and lines[0].strip():
            metadata['title'] = lines[0].strip()

        return content, metadata


    def _convert_markdown(self, file_path: Path) -> Tuple[str, Dict]:
        """Parse markdown and extract frontmatter"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Parse frontmatter (YAML between --- markers)
        metadata = {}
        markdown_content = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                markdown_content = parts[2].strip()

                # Parse YAML frontmatter
                if HAS_YAML:
                    try:
                        metadata = yaml.safe_load(frontmatter) or {}
                    except:
                        pass
                else:
                    # Simple key: value parsing
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()

        # If no title in metadata, extract from first heading
        if 'title' not in metadata:
            heading_match = re.search(r'^#+ (.+)$', markdown_content, re.MULTILINE)
            if heading_match:
                metadata['title'] = heading_match.group(1).strip()

        return markdown_content, metadata


    def _convert_html(self, file_path: Path) -> Tuple[str, Dict]:
        """Convert HTML to markdown"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        metadata = {}

        if HAS_BS4:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title_tag = soup.find('title') or soup.find('h1')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata['description'] = meta_desc['content']

            # Convert to text (simple approach)
            # For better HTML->Markdown, use html2text library
            content = soup.get_text('\n', strip=True)
        else:
            # Fallback: strip HTML tags with regex
            content = re.sub(r'<[^>]+>', '', html)
            title_match = re.search(r'<title>(.+?)</title>', html, re.IGNORECASE)
            if title_match:
                metadata['title'] = title_match.group(1).strip()

        return content, metadata


    def _convert_doc(self, file_path: Path) -> Tuple[str, Dict]:
        """Convert Word document to markdown"""
        if not HAS_DOCX:
            raise ImportError("python-docx required for .docx files. Install: pip install python-docx")

        doc = DocxDocument(str(file_path))

        # Extract text from paragraphs
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # Convert headings to markdown
                if para.style.name.startswith('Heading'):
                    level = para.style.name.replace('Heading ', '')
                    try:
                        level_num = int(level)
                        text = '#' * level_num + ' ' + text
                    except:
                        pass

                paragraphs.append(text)

        content = '\n\n'.join(paragraphs)

        # Extract metadata
        metadata = {}
        if paragraphs:
            # First paragraph is likely the title
            metadata['title'] = paragraphs[0].lstrip('#').strip()

        return content, metadata


    def _convert_data(self, file_path: Path) -> Tuple[str, Dict]:
        """Convert data file (JSON/YAML/CSV) to markdown"""
        extension = file_path.suffix.lstrip('.').lower()

        if extension == 'json':
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Convert to formatted JSON in code block
            content = f"```json\n{json.dumps(data, indent=2)}\n```"

            metadata = {}
            if isinstance(data, dict):
                # Try to extract title from common keys
                for key in ['title', 'name', 'heading']:
                    if key in data:
                        metadata['title'] = str(data[key])
                        break

        elif extension in ['yaml', 'yml']:
            if not HAS_YAML:
                raise ImportError("PyYAML required for YAML files. Install: pip install pyyaml")

            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            content = f"```yaml\n{yaml.dump(data)}\n```"

            metadata = {}
            if isinstance(data, dict):
                for key in ['title', 'name', 'heading']:
                    if key in data:
                        metadata['title'] = str(data[key])
                        break

        elif extension == 'csv':
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Convert CSV to markdown table
            if lines:
                # Header
                header = lines[0].strip().split(',')
                content = '| ' + ' | '.join(header) + ' |\n'
                content += '| ' + ' | '.join(['---'] * len(header)) + ' |\n'

                # Rows
                for line in lines[1:]:
                    row = line.strip().split(',')
                    content += '| ' + ' | '.join(row) + ' |\n'

            metadata = {'title': file_path.stem}

        else:
            # Fallback
            with open(file_path, 'r') as f:
                content = f.read()
            metadata = {}

        return content, metadata


    def _convert_code(self, file_path: Path) -> Tuple[str, Dict]:
        """Convert code file to markdown with syntax highlighting"""
        extension = file_path.suffix.lstrip('.').lower()

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        # Wrap in code block with language
        content = f"```{extension}\n{code}\n```"

        # Try to extract metadata from comments
        metadata = {'title': file_path.name}

        # Check for common doc comment patterns
        doc_patterns = [
            r'"""(.+?)"""',  # Python docstrings
            r'/\*\*(.+?)\*/',  # JSDoc
            r'//(.+)',  # Single-line comments
        ]

        for pattern in doc_patterns:
            match = re.search(pattern, code, re.DOTALL)
            if match:
                doc = match.group(1).strip()
                # Extract title from first line of doc
                first_line = doc.split('\n')[0].strip()
                if first_line and len(first_line) < 100:
                    metadata['title'] = first_line
                break

        return content, metadata


    # ==========================================================================
    # SAVE OPERATIONS
    # ==========================================================================

    def _save_to_brand_folder(
        self,
        brand: str,
        category: str,
        filename: str,
        content: str,
        subcategory: Optional[str] = None
    ) -> Path:
        """
        Save file to brand folder structure

        Creates: brands/soulfra/blog/post.md
        """
        # Build path
        brand_path = self.brands_dir / brand / category
        if subcategory:
            brand_path = brand_path / subcategory

        brand_path.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = brand_path / f'{filename}.md'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path


    def _save_to_database(
        self,
        user_id: int,
        route: str,
        brand: str,
        category: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        subcategory: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Save file metadata to database

        Returns:
            File ID
        """
        conn = get_db()

        # Save to file_routes table
        cursor = conn.execute('''
            INSERT INTO file_routes
            (route, brand, category, subcategory, filename, file_path,
             owner_user_id, file_type, file_size, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            route,
            brand,
            category,
            subcategory,
            filename,
            file_path,
            user_id,
            file_type,
            file_size,
            json.dumps(metadata or {}),
            datetime.now()
        ))

        file_id = cursor.lastrowid

        # Also save to posts table for backward compatibility
        title = (metadata or {}).get('title', filename)

        conn.execute('''
            INSERT INTO posts
            (title, content, author_id, status, created_at, route, brand)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            title,
            f'Imported file: {route}',
            user_id,
            'published',
            datetime.now(),
            route,
            brand
        ))

        conn.commit()
        conn.close()

        return file_id


    def _generate_qr_code(self, route: str, filename: str) -> str:
        """
        Generate QR code for file route

        Args:
            route: File route (e.g., @soulfra/blog/post)
            filename: File slug

        Returns:
            Path to QR code image
        """
        try:
            import qrcode

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(route)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Save QR code
            qr_filename = f'{filename}.png'
            qr_path = self.qr_dir / qr_filename
            img.save(str(qr_path))

            return f'/static/qr/{qr_filename}'

        except ImportError:
            # QR code generation is optional
            return ''


    # ==========================================================================
    # UTILITIES
    # ==========================================================================

    def _generate_slug(self, title: str) -> str:
        """
        Generate URL-safe slug from title

        Args:
            title: Original title

        Returns:
            Slug (e.g., 'my-awesome-post')
        """
        # Convert to lowercase
        slug = title.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)

        # Trim hyphens
        slug = slug.strip('-')

        return slug or 'untitled'


    def list_supported_formats(self) -> Dict[str, List[str]]:
        """Return dict of supported formats"""
        return SUPPORTED_FORMATS


# ==============================================================================
# DATABASE MIGRATION
# ==============================================================================

def init_file_routes_table():
    """
    Initialize file_routes table

    Run this once to set up the table:
    >>> from file_importer import init_file_routes_table
    >>> init_file_routes_table()
    """
    conn = get_db()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS file_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT UNIQUE NOT NULL,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            owner_user_id INTEGER NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (owner_user_id) REFERENCES users(id)
        )
    ''')

    # Indexes for fast lookups
    conn.execute('CREATE INDEX IF NOT EXISTS idx_file_routes_route ON file_routes(route)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_file_routes_brand ON file_routes(brand)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_file_routes_owner ON file_routes(owner_user_id)')

    conn.commit()
    conn.close()

    print('✅ file_routes table created!')


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='File Importer')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--import', dest='import_file', type=str, help='Import a file')
    parser.add_argument('--brand', type=str, help='Brand name')
    parser.add_argument('--category', type=str, help='Category')
    parser.add_argument('--user-id', type=int, default=1, help='User ID')
    parser.add_argument('--formats', action='store_true', help='List supported formats')

    args = parser.parse_args()

    if args.init:
        init_file_routes_table()

    elif args.import_file:
        if not args.brand or not args.category:
            print('Error: --brand and --category required for import')
            exit(1)

        importer = FileImporter()
        result = importer.import_file(
            file_path=args.import_file,
            brand=args.brand,
            category=args.category,
            user_id=args.user_id
        )

        print(f'\n✅ File imported successfully!\n')
        print(f'   Route: {result["route"]}')
        print(f'   URL: {result["url"]}')
        print(f'   File ID: {result["file_id"]}')
        print(f'   QR Code: {result["qr_code"]}\n')

    elif args.formats:
        importer = FileImporter()
        formats = importer.list_supported_formats()

        print('\n📁 Supported File Formats:\n')
        for category, extensions in formats.items():
            print(f'   {category.capitalize()}: {", ".join(extensions)}')
        print()

    else:
        print('Usage: python3 file_importer.py --init')
        print('       python3 file_importer.py --import file.md --brand soulfra --category blog')
        print('       python3 file_importer.py --formats')

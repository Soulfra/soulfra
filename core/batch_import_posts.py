#!/usr/bin/env python3
"""
Batch Import Posts from CSV/Excel

Import blog posts in bulk from spreadsheets. Supports:
- CSV files
- Excel files (.xlsx, .xls)
- Column mapping (Excel columns → database fields)
- Data validation
- Progress tracking

Usage:
    # Preview first 5 rows
    python3 batch_import_posts.py --file posts.csv --preview

    # Import with default column mapping
    python3 batch_import_posts.py --file posts.csv --import

    # Import with custom column mapping
    python3 batch_import_posts.py --file posts.xlsx --import \
        --mapping "Title=title,Content=content,Brand=brand_slug,Tags=tags"

    # Import to specific brand
    python3 batch_import_posts.py --file posts.csv --import --brand deathtodata

Excel/CSV Format:
    title               | content              | brand_slug  | tags                | published_date
    Privacy 101         | Your guide to...     | deathtodata | privacy,encryption  | 2025-01-15
    Neural Networks     | How they work...     | calriven    | AI,ML               | 2025-01-16
"""

import argparse
import sqlite3
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Try to import pandas for Excel support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas not installed. Excel support disabled. Run: pip install pandas openpyxl")

# Default column mapping (Excel column name → database field)
DEFAULT_MAPPING = {
    'title': 'title',
    'content': 'content',
    'brand': 'brand_slug',
    'brand_slug': 'brand_slug',
    'tags': 'tags',
    'published_date': 'published_at',
    'published_at': 'published_at',
    'excerpt': 'excerpt'
}

def load_file(file_path: str) -> pd.DataFrame:
    """Load CSV or Excel file into pandas DataFrame"""

    if not PANDAS_AVAILABLE:
        raise ImportError("pandas not installed. Run: pip install pandas openpyxl")

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect file type and load
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
        print(f"✓ Loaded CSV file: {len(df)} rows")

    elif file_path.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
        print(f"✓ Loaded Excel file: {len(df)} rows")

    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}. Use .csv, .xlsx, or .xls")

    return df

def preview_data(df: pd.DataFrame, num_rows: int = 5):
    """Preview first N rows of data"""

    print(f"\n{'='*80}")
    print(f"PREVIEW (first {num_rows} rows)")
    print(f"{'='*80}\n")

    print(f"Columns found: {', '.join(df.columns.tolist())}")
    print(f"Total rows: {len(df)}\n")

    # Show first N rows
    preview = df.head(num_rows)

    for idx, row in preview.iterrows():
        print(f"Row {idx + 1}:")
        for col in df.columns:
            value = str(row[col])[:60]  # Truncate long values
            print(f"  {col}: {value}")
        print()

def map_columns(df: pd.DataFrame, custom_mapping: Optional[Dict] = None) -> pd.DataFrame:
    """Map Excel columns to database fields"""

    mapping = DEFAULT_MAPPING.copy()

    if custom_mapping:
        mapping.update(custom_mapping)

    # Normalize column names (lowercase, strip whitespace)
    df.columns = df.columns.str.strip().str.lower()

    # Create mapped dataframe
    mapped_df = pd.DataFrame()

    for excel_col, db_field in mapping.items():
        if excel_col.lower() in df.columns:
            mapped_df[db_field] = df[excel_col.lower()]

    # Check required fields
    required_fields = ['title', 'content']
    missing_fields = [f for f in required_fields if f not in mapped_df.columns]

    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    return mapped_df

def get_brand_id(brand_slug: str) -> Optional[int]:
    """Get brand ID from slug"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM brands WHERE slug = ?", (brand_slug,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def create_slug(title: str) -> str:
    """Generate URL slug from title"""

    import re

    # Lowercase, replace spaces with hyphens, remove special chars
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')

    # Add timestamp to ensure uniqueness
    slug = f"{slug}-{int(datetime.now().timestamp())}"

    return slug[:100]  # Limit length

def validate_row(row: Dict, row_num: int) -> Optional[str]:
    """Validate a row of data. Returns error message if invalid, None if valid"""

    # Check required fields
    if not row.get('title'):
        return f"Row {row_num}: Missing title"

    if not row.get('content'):
        return f"Row {row_num}: Missing content"

    # Check title length
    if len(row['title']) > 200:
        return f"Row {row_num}: Title too long (max 200 characters)"

    # Check brand exists (if specified)
    if row.get('brand_slug'):
        brand_id = get_brand_id(row['brand_slug'])
        if not brand_id:
            return f"Row {row_num}: Brand not found: {row['brand_slug']}"

    return None

def import_posts(df: pd.DataFrame, default_brand: str = None, dry_run: bool = False) -> Dict:
    """
    Import posts from DataFrame into database

    Args:
        df: Pandas DataFrame with mapped columns
        default_brand: Default brand slug if not specified in data
        dry_run: If True, validate only without inserting

    Returns:
        Dict with success/error statistics
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get default brand ID
    default_brand_id = None
    if default_brand:
        default_brand_id = get_brand_id(default_brand)
        if not default_brand_id:
            raise ValueError(f"Default brand not found: {default_brand}")

    stats = {
        'total': len(df),
        'success': 0,
        'errors': 0,
        'skipped': 0,
        'error_messages': []
    }

    print(f"\n{'='*80}")
    print(f"IMPORTING {len(df)} POSTS")
    if dry_run:
        print("(DRY RUN - No actual changes will be made)")
    print(f"{'='*80}\n")

    for idx, row in df.iterrows():
        row_num = idx + 1
        row_dict = row.to_dict()

        # Validate row
        error = validate_row(row_dict, row_num)
        if error:
            stats['errors'] += 1
            stats['error_messages'].append(error)
            print(f"✗ {error}")
            continue

        # Prepare data
        title = row_dict['title']
        content = row_dict['content']
        slug = create_slug(title)

        # Get brand ID
        brand_id = default_brand_id
        if row_dict.get('brand_slug'):
            brand_id = get_brand_id(row_dict['brand_slug'])

        # Published date
        published_at = row_dict.get('published_at')
        if not published_at:
            published_at = datetime.now().isoformat()
        elif isinstance(published_at, str):
            # Try to parse date string
            try:
                dt = datetime.fromisoformat(published_at)
                published_at = dt.isoformat()
            except:
                published_at = datetime.now().isoformat()

        # Excerpt
        excerpt = row_dict.get('excerpt')
        if not excerpt:
            # Generate from content (first 150 chars)
            excerpt = content[:150] + '...' if len(content) > 150 else content

        if dry_run:
            print(f"✓ Row {row_num}: Would import '{title}' → /post/{slug}")
            stats['success'] += 1
            continue

        # Insert into database
        try:
            cursor.execute("""
                INSERT INTO posts (user_id, title, slug, content, excerpt, published_at, brand_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # Default admin user
                title,
                slug,
                content,
                excerpt,
                published_at,
                brand_id
            ))

            post_id = cursor.lastrowid
            stats['success'] += 1

            print(f"✓ Row {row_num}: Imported '{title}' → post #{post_id}")

        except Exception as e:
            stats['errors'] += 1
            error_msg = f"Row {row_num}: Database error: {str(e)}"
            stats['error_messages'].append(error_msg)
            print(f"✗ {error_msg}")

    if not dry_run:
        conn.commit()

    conn.close()

    # Print summary
    print(f"\n{'='*80}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"Total rows: {stats['total']}")
    print(f"✓ Success: {stats['success']}")
    print(f"✗ Errors: {stats['errors']}")
    print(f"⊘ Skipped: {stats['skipped']}")

    if stats['error_messages']:
        print(f"\nErrors:")
        for err in stats['error_messages'][:10]:  # Show first 10 errors
            print(f"  • {err}")

    return stats

def parse_custom_mapping(mapping_str: str) -> Dict:
    """Parse custom mapping string like 'Title=title,Content=content'"""

    mapping = {}

    for pair in mapping_str.split(','):
        if '=' not in pair:
            continue

        excel_col, db_field = pair.split('=', 1)
        mapping[excel_col.strip().lower()] = db_field.strip()

    return mapping

def main():
    parser = argparse.ArgumentParser(description="Batch import posts from CSV/Excel")
    parser.add_argument('--file', required=True, help='CSV or Excel file to import')
    parser.add_argument('--preview', action='store_true', help='Preview first 5 rows without importing')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Import posts into database')
    parser.add_argument('--brand', help='Default brand slug for posts')
    parser.add_argument('--mapping', help='Custom column mapping (e.g., "Title=title,Content=content")')
    parser.add_argument('--dry-run', action='store_true', help='Validate without actually importing')

    args = parser.parse_args()

    try:
        # Load file
        df = load_file(args.file)

        # Preview mode
        if args.preview:
            preview_data(df)
            print("\n💡 To import, run with --import flag")
            return 0

        # Parse custom mapping
        custom_mapping = None
        if args.mapping:
            custom_mapping = parse_custom_mapping(args.mapping)
            print(f"Using custom mapping: {custom_mapping}")

        # Map columns
        mapped_df = map_columns(df, custom_mapping)
        print(f"✓ Mapped {len(mapped_df.columns)} columns: {', '.join(mapped_df.columns)}")

        # Import mode
        if args.do_import:
            stats = import_posts(mapped_df, default_brand=args.brand, dry_run=args.dry_run)

            if stats['errors'] > 0:
                return 1
            else:
                return 0
        else:
            print("\n💡 Use --preview to preview data or --import to import")
            return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

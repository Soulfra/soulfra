#!/usr/bin/env python3
"""
PDF Scraper - Extract Data from MLS Reports

Extracts property data from MLS PDF reports using:
- PyPDF2 for text extraction
- pdfplumber for tables
- Regular expressions for data parsing

Usage:
    from pdf_scraper import extract_mls_data

    data = extract_mls_data("mls_report_jan_2026.pdf")
    # Returns: {'median_price': 750000, 'listings': 1250, ...}
"""

import re
from typing import Dict, List, Optional
from pathlib import Path


class PDFScraper:
    """Extract data from PDF files"""

    def __init__(self):
        # Try to import PDF libraries
        self.pypdf2_available = False
        self.pdfplumber_available = False

        try:
            import PyPDF2
            self.pypdf2_available = True
            self.PyPDF2 = PyPDF2
        except ImportError:
            print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")

        try:
            import pdfplumber
            self.pdfplumber_available = True
            self.pdfplumber = pdfplumber
        except ImportError:
            print("⚠️  pdfplumber not installed. Install with: pip install pdfplumber")

    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text from PDF using PyPDF2

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        if not self.pypdf2_available:
            return ""

        try:
            with open(pdf_path, 'rb') as file:
                reader = self.PyPDF2.PdfReader(file)
                text = ""

                for page in reader.pages:
                    text += page.extract_text()

                return text

        except Exception as e:
            print(f"❌ PyPDF2 extraction failed: {e}")
            return ""

    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text from PDF using pdfplumber (better for tables)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        if not self.pdfplumber_available:
            return ""

        try:
            text = ""

            with self.pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()

            return text

        except Exception as e:
            print(f"❌ pdfplumber extraction failed: {e}")
            return ""

    def extract_tables(self, pdf_path: str) -> List[List]:
        """
        Extract tables from PDF using pdfplumber

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of tables (each table is a list of rows)
        """
        if not self.pdfplumber_available:
            return []

        try:
            tables = []

            with self.pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

            return tables

        except Exception as e:
            print(f"❌ Table extraction failed: {e}")
            return []

    def parse_mls_data(self, text: str) -> Dict:
        """
        Parse MLS data from extracted text

        Looks for common patterns:
        - Median Price: $750,000
        - Total Listings: 1,250
        - Days on Market: 25

        Args:
            text: Extracted PDF text

        Returns:
            Parsed data dict
        """
        data = {}

        # Extract median price
        median_price_match = re.search(r'median\s+price[:\s]+\$?([\d,]+)', text, re.IGNORECASE)
        if median_price_match:
            price_str = median_price_match.group(1).replace(',', '')
            data['median_price'] = int(price_str)

        # Extract total listings
        listings_match = re.search(r'total\s+listings[:\s]+([\d,]+)', text, re.IGNORECASE)
        if listings_match:
            listings_str = listings_match.group(1).replace(',', '')
            data['total_listings'] = int(listings_str)

        # Extract days on market
        dom_match = re.search(r'days\s+on\s+market[:\s]+([\d,]+)', text, re.IGNORECASE)
        if dom_match:
            dom_str = dom_match.group(1).replace(',', '')
            data['days_on_market'] = int(dom_str)

        # Extract inventory
        inventory_match = re.search(r'inventory[:\s]+([\d,]+)', text, re.IGNORECASE)
        if inventory_match:
            inventory_str = inventory_match.group(1).replace(',', '')
            data['inventory'] = int(inventory_str)

        # Extract sale price
        sale_price_match = re.search(r'sale\s+price[:\s]+\$?([\d,]+)', text, re.IGNORECASE)
        if sale_price_match:
            price_str = sale_price_match.group(1).replace(',', '')
            data['avg_sale_price'] = int(price_str)

        return data


def extract_mls_data(pdf_path: str) -> Optional[Dict]:
    """
    Extract MLS data from PDF report

    Args:
        pdf_path: Path to MLS PDF report

    Returns:
        Extracted data dict or None if failed
    """
    scraper = PDFScraper()

    if not scraper.pypdf2_available and not scraper.pdfplumber_available:
        print("❌ No PDF library available")
        print("   Install: pip install PyPDF2 pdfplumber")
        return None

    # Check file exists
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return None

    print(f"📄 Extracting data from: {pdf_path}")

    # Try pdfplumber first (better for tables)
    text = scraper.extract_text_pdfplumber(pdf_path)

    # Fallback to PyPDF2
    if not text:
        text = scraper.extract_text_pypdf2(pdf_path)

    if not text:
        print("❌ Could not extract text from PDF")
        return None

    # Parse MLS data
    data = scraper.parse_mls_data(text)

    if not data:
        print("⚠️  No MLS data found in PDF")
        print("   Text preview:")
        print(text[:500])
        return None

    print(f"✅ Extracted {len(data)} data points")
    return data


def format_mls_data_for_ai(data: Dict, source_file: str) -> str:
    """
    Format MLS data for AI context

    Args:
        data: Extracted MLS data
        source_file: Source PDF filename

    Returns:
        Formatted string for AI prompt
    """
    lines = ["📊 MLS MARKET DATA (PDF REPORT):", ""]

    if data.get('median_price'):
        lines.append(f"   • Median Price: ${data['median_price']:,}")

    if data.get('total_listings'):
        lines.append(f"   • Total Listings: {data['total_listings']:,}")

    if data.get('days_on_market'):
        lines.append(f"   • Days on Market: {data['days_on_market']}")

    if data.get('inventory'):
        lines.append(f"   • Inventory: {data['inventory']:,} homes")

    if data.get('avg_sale_price'):
        lines.append(f"   • Avg Sale Price: ${data['avg_sale_price']:,}")

    lines.append("")
    lines.append(f"   ✅ SOURCE: MLS Report ({source_file})")
    lines.append("   📅 Report Date: Check PDF for date")

    return "\n".join(lines)


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """CLI for PDF scraping"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 pdf_scraper.py <pdf_file>")
        print()
        print("Example:")
        print("  python3 pdf_scraper.py mls_report_jan_2026.pdf")
        return

    pdf_path = sys.argv[1]

    print("=" * 70)
    print("📄 MLS PDF SCRAPER")
    print("=" * 70)
    print()

    # Extract data
    data = extract_mls_data(pdf_path)

    if data:
        print()
        print("=" * 70)
        print("📊 EXTRACTED DATA")
        print("=" * 70)
        print()

        for key, value in data.items():
            print(f"  {key}: {value}")

        print()
        print("=" * 70)
        print("AI CONTEXT")
        print("=" * 70)
        print()
        print(format_mls_data_for_ai(data, pdf_path))
    else:
        print()
        print("❌ Failed to extract MLS data")


if __name__ == '__main__':
    main()
